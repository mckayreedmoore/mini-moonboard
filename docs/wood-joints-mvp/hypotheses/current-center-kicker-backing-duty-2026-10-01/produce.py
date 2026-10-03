"""Authenticate saved inputs and audit center-kicker geometry and duties."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
H = "docs/wood-joints-mvp/hypotheses/"
E = H + "evaluation-resume-2026-09-24/"
FILES = {
    "panel": (
        H + "current-panel-receiver-transfer-2026-10-01/receiver-transfer.json",
        "0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534",
    ),
    "atlas": (
        E
        + "current-geometric-interface-face-atlas-attempt01-2026-09-28/face-pair-atlas.json",
        "d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9",
    ),
    "manifest": (
        E
        + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
        "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    ),
    "graph": (
        E + "complete-contact-graph-attempt02.json",
        "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26",
    ),
    "axis_features": (
        H + "current-finished-feature-register-2026-10-01/axis-features.json",
        "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    ),
    "surfaces": (
        H + "current-finished-feature-register-2026-10-01/surfaces.json",
        "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    ),
    "envelopes": (
        H + "current-stock-envelope-reconciliation-2026-10-01/envelopes.json",
        "0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01",
    ),
}
CLOSURES = {
    H
    + "current-panel-receiver-transfer-2026-10-01/source-pins.json": "973ffd947cb6bcaa823e4038c0b6c98fc18736423a872ef87666806878784b3e",
    H
    + "current-finished-feature-register-2026-10-01/source-pins.json": "0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd",
    H
    + "current-finished-feature-register-2026-10-01/axis-source-pins.json": "7a501047c003174c15461ae12e3cd47af4e4bf59b1d40d3c8e5b76d8e1904d34",
    H
    + "current-stock-envelope-reconciliation-2026-10-01/source-pins.json": "8ba6fb89c1f9e05fd975d742e5bd593a5b3bbdca2ed06d3815d18217d038540d",
    E
    + "current-geometric-interface-face-atlas-attempt01-2026-09-28/source-pins.json": "b92dcec2638fc335951033a0289cdc50bc0a949cb397b46bc03c1ad185e3c30d",
}
STALE_PATH = "docs/wood-joints-mvp/criteria-method-map.md"
STALE_EXPECTED = "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7"
STALE_CURRENT = "bd356fc8751e17c860fd6df8150c3076b9cfbd742fff9b0de518b970868f324a"
REVIEWED_GEOMETRY_BINDINGS = (
    (
        "site/owner-wood-joints-wj24-scene.json",
        "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf",
    ),
    (
        "site/owner-wood-joints-review-report.json",
        "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695",
    ),
    (
        E + "geometry-snapshot.json",
        "0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187",
    ),
)
AUTHORITY_PATHS = (
    "current-candidate.json",
    "docs/wood-joints-mvp/criteria.json",
    "docs/wood-joints-mvp/current-criteria-coverage.json",
    STALE_PATH,
    "docs/wood-joints-mvp/current-kicker-edge-obligation.md",
    "docs/wood-joints-mvp/current-layout-obligations.md",
    "docs/bolted-candidate-owner-inputs.json",
    "docs/bolted-candidate-plan.md",
    "docs/floor-flush-shop-checklist.md",
    "uv.lock",
    "pyproject.toml",
)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject(value):
        raise ValueError(f"nonfinite JSON value: {value}")

    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=reject)


def register_pin(root, sources, relative, expected=None, manifest=None):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("source path is not repository-relative")
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise ValueError(f"source path escapes root: {relative}")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    stale = expected is not None and actual != expected
    allowed_prose = (relative, expected, actual) == (
        STALE_PATH,
        STALE_EXPECTED,
        STALE_CURRENT,
    )
    if stale and not allowed_prose:
        raise ValueError(f"source pin changed: {relative}")
    record = sources.setdefault(
        relative,
        {
            "path": relative,
            "sha256": actual,
            "size_bytes": len(data),
            "upstream_bindings": [],
        },
    )
    if record["sha256"] != actual or record["size_bytes"] != len(data):
        raise ValueError(f"source changed during read: {relative}")
    if manifest is not None:
        binding = {
            "manifest_path": manifest,
            "expected_sha256": expected,
            "status": "STALE_PROSE_INPUT" if stale else "MATCH",
        }
        if binding not in record["upstream_bindings"]:
            record["upstream_bindings"].append(binding)
    return stale


def closure_rows(document):
    rows = document.get("sources", document.get("pins", document.get("source_hashes")))
    if isinstance(rows, dict):
        rows = [
            {"path": key, "sha256": value} if isinstance(value, str) else value
            for key, value in rows.items()
        ]
    if not isinstance(rows, list) or not rows:
        raise ValueError("source closure has no rows")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("sha256"), str):
            raise TypeError("malformed source pin")
        if row.get("path") in seen:
            raise ValueError("duplicate source pin")
        seen.add(row.get("path"))
    return rows


def load_inputs(root):
    sources, assessment, inputs = {}, [], {}
    for key, (relative, expected) in FILES.items():
        register_pin(root, sources, relative, expected)
        inputs[key] = read_json(root / relative)
    for relative, expected in CLOSURES.items():
        register_pin(root, sources, relative, expected)
        rows = closure_rows(read_json(root / relative))
        stale_rows = []
        for row in rows:
            stale = register_pin(root, sources, row["path"], row["sha256"], relative)
            if (
                "size_bytes" in row
                and row["size_bytes"] != sources[row["path"]]["size_bytes"]
            ):
                raise ValueError(f"source pin size changed: {row['path']}")
            if stale:
                stale_rows.append(
                    {
                        "path": row["path"],
                        "expected_sha256": row["sha256"],
                        "current_sha256": sources[row["path"]]["sha256"],
                        "status": "STALE_PROSE_INPUT",
                        "numeric_geometry_dependency": False,
                    }
                )
        assessment.append(
            {
                "manifest_path": relative,
                "recorded_pin_count": len(rows),
                "matching_live_pin_count": len(rows) - len(stale_rows),
                "historical_exact_closure_status": "REFUSED" if stale_rows else "MATCH",
                "stale_inputs": stale_rows,
            }
        )
    for relative, expected in REVIEWED_GEOMETRY_BINDINGS:
        register_pin(root, sources, relative, expected)
    for relative in AUTHORITY_PATHS:
        register_pin(root, sources, relative)
    if inputs["atlas"]["toolchain"] != {
        "python": "3.12.3",
        "cadquery": "2.8.0",
        "cadquery_ocp": "7.9.3.1.1",
        "ocp_module": "7.9.3.1",
    }:
        raise ValueError("saved atlas toolchain differs")
    return inputs, sources, assessment


def load_method(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"missing method: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def current_obligations(coverage, criteria, candidate, revision, sources):
    if coverage.get("candidate") != candidate or criteria.get("candidate") != candidate:
        raise ValueError("current authority candidate differs")
    geometry_pin = coverage.get("current_geometry_pin", {})
    if geometry_pin.get("revision_id") != revision:
        raise ValueError("current authority geometry revision differs")
    for kind, (expected_path, expected_hash) in zip(
        ("scene", "report", "snapshot"), REVIEWED_GEOMETRY_BINDINGS, strict=True
    ):
        relative = geometry_pin.get(kind + "_path")
        binding = sources.get(relative)
        if (
            relative != expected_path
            or geometry_pin.get(kind + "_sha256") != expected_hash
            or binding is None
            or binding["sha256"] != expected_hash
        ):
            raise ValueError(f"current authority {kind} geometry binding differs")
    ids = {
        "actual_kicker_cutouts",
        "center_kicker_receiver_paths",
        "complete_load_path_coverage",
    }
    obligations = [r for r in coverage["criteria"] if r["criterion_id"] in ids]
    if (
        len(obligations) != len(ids)
        or {r["criterion_id"] for r in obligations} != ids
        or any(r["status"] != "pending" for r in obligations)
    ):
        raise ValueError("current support/path authority differs")
    if criteria["engineering_mvp_complete"] is not False:
        raise ValueError("criterion authority complete flag differs")
    return obligations


def build_report(root=ROOT):
    root = Path(root).resolve()
    folder = root / HERE.relative_to(ROOT)
    inputs, sources, assessment = load_inputs(root)
    for path in sorted(folder.glob("*.py")):
        register_pin(root, sources, path.relative_to(root).as_posix())
    for name in ("plan.md", "source-dependency-note.md", "README.md"):
        register_pin(root, sources, (folder / name).relative_to(root).as_posix())
    backing = load_method(folder / "backing.py", "center_current_backing")
    duties = load_method(folder / "duties.py", "center_current_duties")
    coverage = read_json(root / "docs/wood-joints-mvp/current-criteria-coverage.json")
    criteria = read_json(root / "docs/wood-joints-mvp/criteria.json")
    obligations = current_obligations(
        coverage, criteria, backing.CANDIDATE, backing.REVISION, sources
    )
    pins = {
        "schema": "current_center_kicker_source_pins/v1",
        "sources": [sources[k] for k in sorted(sources)],
    }
    report = {
        "schema": "current_center_kicker_backing_duty/v1",
        "candidate": backing.CANDIDATE,
        "geometry_revision_id": backing.REVISION,
        "status": "SOURCE_BOUND_GEOMETRY_AND_DUTIES_WITH_STALE_PROSE_INPUT",
        "upstream_source_pin_assessment": assessment,
        "stale_prose_geometry_dependency_evidence": {
            "source_dependency_note": str(
                HERE.relative_to(ROOT) / "source-dependency-note.md"
            ),
            "original_overlap_method": "scripts/wood_joint_wj08_overlap_contact_geometry.py",
            "prose_use": "PINNED_INPUTS/_load_and_check_pinned_inputs hash check only",
            "atlas_method": "scripts/wood_joint_current_face_pair_atlas_attempt01.py",
            "numeric_inputs": "pinned STEP bodies, graph and descriptor/evidence JSON; no method-map prose parsing",
            "historical_full_closure_pass_claimed": False,
        },
        "current_authority_obligations": obligations,
        "geometry": backing.build_backing(
            inputs["atlas"], inputs["graph"], inputs["manifest"]
        ),
        "duties": duties.build_duties(
            inputs["panel"],
            inputs["manifest"],
            inputs["graph"],
            inputs["axis_features"],
            inputs["surfaces"],
            inputs["envelopes"],
        ),
        "replay_runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "dependency_lock_sha256": sources["uv.lock"]["sha256"],
            "new_cad_or_native_execution": False,
        },
        "source_pins_sha256": hashlib.sha256(canonical(pins)).hexdigest(),
        "claim_boundary": {
            "continuous_direct_backing_adopted": False,
            "geometry_gap_establishes_failed_criterion": False,
            "active_contact_or_regional_force_split_established": False,
            "joint_capacity_or_six_case_acceptance": False,
            "geometry_change_or_physical_work_authorized": False,
        },
    }
    return report, pins


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        report, pins = build_report()
        for name, value in (("backing-duty.json", report), ("source-pins.json", pins)):
            expected = canonical(value)
            path = HERE / name
            if args.write:
                path.write_bytes(expected)
            elif path.read_bytes() != expected:
                raise ValueError(f"saved output differs: {name}")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "source_pins": len(pins["sources"]),
                    "report_sha256": hashlib.sha256(canonical(report)).hexdigest(),
                }
            )
        )
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
