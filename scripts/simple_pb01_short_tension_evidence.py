"""Package verified PB01 short-block tension-only diagnostic evidence."""

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

FINAL_FILES = (
    "input.json",
    "report.json",
    "frame.inp",
    "frame.dat",
    "frame.log",
    "frame.sta",
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _safe(name):
    path = Path(name)
    if (
        path.is_absolute()
        or not name
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValueError(f"Unsafe member path: {name}")
    return name


def _selection(report):
    scope = report.get("diagnostic_scope", {})
    if scope.get("case") not in ("a12-left", "k12-right"):
        raise ValueError("Expected A12-left or K12-right")
    if any(
        scope.get(key) != value
        for key, value in {
            "diagnostic_only": True,
            "pb01_pose_variant": "quarter_short",
            "pb01_axial_law": "tension_only_no_preload",
            "pb01_face_contact_law": "compression_only",
            "qualified_for_design": False,
            "drilling_released": False,
        }.items()
    ):
        raise ValueError("Unexpected diagnostic scope")
    if report.get("pb01_axial_law") != scope["pb01_axial_law"]:
        raise ValueError("Axial law disagrees with scope")
    for gate in (
        "numerically_accepted",
        "contact_active_set_converged",
        "axial_tension_active_set_converged",
        "axial_tension_assumption_passed",
        "closed_bearing_assumption_passed",
    ):
        if report.get(gate) is not True:
            raise ValueError(f"Run not accepted/converged: {gate}")
    cycles = report.get("contact_cycles") or []
    if (
        not cycles
        or cycles[-1].get("contact_passed") is not True
        or cycles[-1].get("axial_tension_passed") is not True
    ):
        raise ValueError("Final active set not converged")
    cycle = _safe(cycles[-1]["directory"])
    if Path(cycle).name != cycle or not cycle.startswith("cycle-"):
        raise ValueError("Unsafe final cycle")
    sources = tuple(
        f"source_snapshots/{_safe(name)}" for name in report["source_sha256"]
    )
    selected = (
        ("diagnostic-scope.json",)
        + tuple(f"{cycle}/{name}" for name in FINAL_FILES)
        + sources
    )
    if len(set(selected)) != len(selected):
        raise ValueError("Duplicate selected artifact")
    if any(name not in report["artifact_sha256"] for name in selected):
        raise ValueError("Missing artifact digest")
    return cycle, selected


def _summary(report):
    cycle, _ = _selection(report)
    axial = sorted(report["axial_tension"], key=lambda row: row["name"])
    face = sorted(
        (row for row in report["bearings"] if row["name"].startswith("pb01_")),
        key=lambda row: row["name"],
    )
    if (
        len(axial) != 4
        or len(face) != 8
        or any(
            row.get("tension_only_assumption_satisfied") is not True for row in axial
        )
        or any(
            row.get("compression_only_assumption_satisfied") is not True for row in face
        )
    ):
        raise ValueError("Incomplete PB01 bolt/contact results")
    active = sorted(row["name"] for row in axial if row["active"])
    if active != sorted(report["contact_cycles"][-1]["axial_tension_active_names"]):
        raise ValueError("Axial state disagrees with final cycle")
    return {
        "case": report["diagnostic_scope"]["case"],
        "final_cycle": cycle,
        "numerically_accepted": True,
        "qualified_for_design": False,
        "units": {
            "extension_mm": "positive tension/opening; negative shortening",
            "opening_mm": "positive gap; negative compression",
            "forces_n": "nonnegative unilateral spring magnitudes",
        },
        "axial_tension": [
            {
                key: row[key]
                for key in ("name", "active", "extension_mm", "tension_force_n")
            }
            for row in axial
        ],
        "face_contact": [
            {
                key: row[key]
                for key in ("name", "active", "opening_mm", "compression_force_n")
            }
            for row in face
        ],
    }


def _check_report_files(report, read):
    cycle, selected = _selection(report)
    scope = json.loads(read("diagnostic-scope.json"))
    if scope != report["diagnostic_scope"]:
        raise ValueError("Scope differs from top report")
    final = json.loads(read(f"{cycle}/report.json"))
    for key in (
        "axial_tension",
        "bearings",
        "axial_tension_assumption_passed",
        "closed_bearing_assumption_passed",
    ):
        if final.get(key) != report.get(key):
            raise ValueError(f"Final cycle differs from top report: {key}")
    case_hold = {"a12-left": "A12", "k12-right": "K12"}[scope["case"]]
    if json.loads(read(f"{cycle}/input.json")).get("hold") != case_hold:
        raise ValueError("Final input has wrong load case")
    for name in selected:
        digest = _sha(read(name))
        if digest != report["artifact_sha256"][name]:
            raise ValueError(f"Artifact digest mismatch: {name}")
        if name.startswith("source_snapshots/"):
            source_name = name.removeprefix("source_snapshots/")
            if digest != report["source_sha256"][source_name]:
                raise ValueError(f"Source digest mismatch: {name}")
    return selected


def build(source, output):
    """Validate and atomically publish one compact, self-verifying archive."""
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    original = (source / "report.json").read_bytes()
    report = json.loads(original)
    selected = _check_report_files(report, lambda name: (source / name).read_bytes())
    summary = _summary(report)
    replay = {
        "case": summary["case"],
        "source_directory": str(source.resolve()),
        "source_report_sha256": _sha(original),
        "solver_image": report.get("solver_image"),
        "final_cycle": summary["final_cycle"],
        "invocation": [
            "uv",
            "run",
            "python",
            "-m",
            "scripts.simple_pb01_hybrid_diagnostic_run",
            summary["case"],
            "--variant",
            "quarter_short",
            "--tension-only-axial",
            "--output",
            "<fresh-output-directory>",
        ],
        "trial_stiffness_n_per_mm": report["diagnostic_scope"].get(
            "trial_stiffness_n_per_mm"
        ),
    }
    members = {
        "report.json": original,
        "summary.json": _json(summary),
        "replay.json": _json(replay),
    }
    members.update({name: (source / name).read_bytes() for name in selected})
    manifest = {
        "format": "pb01-short-tension-evidence-v1",
        "case": summary["case"],
        "members_sha256": {name: _sha(data) for name, data in sorted(members.items())},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".pb01-evidence-", suffix=".zip", delete=False
        ) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as bundle:
            for name, data in sorted(members.items()):
                bundle.writestr(name, data)
            bundle.writestr("manifest.json", _json(manifest))
        verify(temporary)
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def verify(archive):
    """Verify member, producer, and final-cycle hashes without the source tree."""
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or "manifest.json" not in names:
            raise ValueError("Invalid bundle member list")
        manifest = json.loads(bundle.read("manifest.json"))
        expected = manifest["members_sha256"]
        if manifest.get("format") != "pb01-short-tension-evidence-v1" or set(
            names
        ) != set(expected) | {"manifest.json"}:
            raise ValueError("Unexpected bundle members")
        for name, digest in expected.items():
            _safe(name)
            if _sha(bundle.read(name)) != digest:
                raise ValueError(f"Bundle digest mismatch: {name}")
        report = json.loads(bundle.read("report.json"))
        selected = _check_report_files(report, bundle.read)
        if set(expected) != set(selected) | {
            "report.json",
            "summary.json",
            "replay.json",
        }:
            raise ValueError("Bundle selection differs from report")
        summary = _summary(report)
        if (
            json.loads(bundle.read("summary.json")) != summary
            or manifest["case"] != summary["case"]
        ):
            raise ValueError("Summary differs from report")
        replay = json.loads(bundle.read("replay.json"))
        if (
            replay.get("source_report_sha256") != _sha(bundle.read("report.json"))
            or replay.get("case") != summary["case"]
            or replay.get("final_cycle") != summary["final_cycle"]
            or replay.get("solver_image") != report.get("solver_image")
        ):
            raise ValueError("Replay metadata differs from report")
        return summary


def compare(left, right, output):
    """Write signed K12 minus A12 differences from verified packages."""
    a, k = verify(left), verify(right)
    if (a["case"], k["case"]) != ("a12-left", "k12-right"):
        raise ValueError("Expected A12-left then K12-right")
    with zipfile.ZipFile(left) as left_bundle, zipfile.ZipFile(right) as right_bundle:
        left_report = json.loads(left_bundle.read("report.json"))
        right_report = json.loads(right_bundle.read("report.json"))
    if (
        left_report["source_sha256"] != right_report["source_sha256"]
        or left_report.get("solver_image") != right_report.get("solver_image")
        or left_report["diagnostic_scope"].get("trial_stiffness_n_per_mm")
        != right_report["diagnostic_scope"].get("trial_stiffness_n_per_mm")
    ):
        raise ValueError("Cases have different source, solver, or trial stiffness")
    result = {
        "format": "pb01-short-tension-comparison-v1",
        "classification": "diagnostic_only_not_structural_qualification",
        "left_archive_sha256": _sha(Path(left).read_bytes()),
        "right_archive_sha256": _sha(Path(right).read_bytes()),
        "delta_definition": "k12-right minus a12-left",
    }
    for label, field, force in (
        ("axial_tension", "extension_mm", "tension_force_n"),
        ("face_contact", "opening_mm", "compression_force_n"),
    ):
        aa = {row["name"]: row for row in a[label]}
        kk = {row["name"]: row for row in k[label]}
        if aa.keys() != kk.keys():
            raise ValueError(f"Unmatched {label} names")
        result[label] = [
            {
                "name": name,
                "a12": {key: aa[name][key] for key in ("active", field, force)},
                "k12": {key: kk[name][key] for key in ("active", field, force)},
                f"delta_{field}": kk[name][field] - aa[name][field],
                f"delta_{force}": kk[name][force] - aa[name][force],
            }
            for name in sorted(aa)
        ]
    with Path(output).open("xb") as handle:
        handle.write(_json(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("source", type=Path)
    build_parser.add_argument("output", type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("archive", type=Path)
    compare_parser = sub.add_parser("compare")
    compare_parser.add_argument("a12_archive", type=Path)
    compare_parser.add_argument("k12_archive", type=Path)
    compare_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        build(args.source, args.output)
        print(json.dumps(verify(args.output), indent=2))
    elif args.command == "verify":
        print(json.dumps(verify(args.archive), indent=2))
    else:
        print(
            json.dumps(
                compare(args.a12_archive, args.k12_archive, args.output), indent=2
            )
        )


if __name__ == "__main__":
    main()
