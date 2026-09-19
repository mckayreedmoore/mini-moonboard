"""Source-bound, provisional signed actions from an accepted native AB205 diagnostic."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.bolted_center_demand_extract import _physical_row, _vector, _wrench

CANDIDATE = "bolted-kerf-right-left-center-ab205-diagnostic"
GEOMETRY = "compact-floor-flush-bolted-development-kerf-right"
CASES = {
    "a12-rear": ("A12", 0, 300),
    "a12-forward": ("A12", 0, -300),
    "a12-left": ("A12", -300, 0),
    "k12-right": ("K12", 300, 0),
    "k12-rear": ("K12", 0, 300),
    "a1-rear": ("A1", 0, 300),
}


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(report, root):
    manifest = report.get("artifact_sha256")
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("Missing artifact manifest")
    for name, expected in manifest.items():
        path = root / name
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or not path.is_file()
            or _digest(path) != expected
        ):
            raise ValueError(f"Artifact digest mismatch: {name}")
    sources = report.get("source_sha256")
    required = {
        "fea/current_response_run.py",
        "fea/current_response_model.py",
        "scripts/bolted_center_native_diagnostic.py",
        "scripts/bolted_center_joint_model.py",
        "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    }
    if not isinstance(sources, dict) or not required <= sources.keys():
        raise ValueError("Missing native producer source identity")
    for name, expected in sources.items():
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or manifest.get(f"source_snapshots/{name}") != expected
        ):
            raise ValueError(f"Source snapshot identity mismatch: {name}")
    return sources


def _wrench_checked(rows, body, origin):
    wrench, force_radius, moment_radius = _wrench(rows, body, origin)
    return wrench, force_radius, moment_radius


def _balance(rows, body, origin):
    wrench, fr, mr = _wrench_checked(rows, body, origin)
    passed = all(abs(v) <= r + 0.1 for v, r in zip(wrench["force_xyz_n"], fr)) and all(
        abs(v) <= r + 20 for v, r in zip(wrench["moment_xyz_nmm"], mr)
    )
    if not passed:
        raise ValueError(f"Joint body equilibrium failed: {body}")
    return {
        **wrench,
        "force_rounding_radius_xyz_n": fr,
        "moment_rounding_radius_xyz_nmm": mr,
        "passed": True,
    }


def _points_match(rows, points, label):
    if len(rows) != len(points) or sorted(
        tuple(_vector(row["point"], label)) for row in rows
    ) != sorted(tuple(_vector(point, label)) for point in points):
        raise ValueError(f"Joint branch point mismatch: {label}")


def extract(report, record):
    """Use only the recorded topology and simultaneous final-cycle connector rows."""
    spec = record["diagnostic_center_joint"]
    angles = spec["angles"]
    bolts = spec["shared_header_bolts"]
    if (
        len(angles) != 2
        or len(bolts) != 2
        or {a["wood_member"] for a in angles}
        != {"base_principal_center_left", "base_post_center_left"}
        or len({a["name"] for a in angles} | {b["name"] for b in bolts}) != 4
    ):
        raise ValueError("Unexpected left-center joint specification")
    principal = next(
        a for a in angles if a["wood_member"] == "base_principal_center_left"
    )
    post = next(a for a in angles if a["wood_member"] == "base_post_center_left")
    upper, lower = principal["name"], post["name"]
    body_names = {upper, lower, *(b["name"] for b in bolts)}
    owners = record["connection_ownership"]
    physical = report["physical_connection_forces"]
    if any(
        clip in {o["first"], o["second"]}
        for clip in spec["replaced_clips"]
        for o in owners.values()
    ):
        raise ValueError("Replaced baseline clip remains connected")
    selected = {
        name: owner
        for name, owner in owners.items()
        if {owner["first"], owner["second"]} & body_names
    }
    if not selected or any(
        {r["first"], r["second"]} & body_names and name not in selected
        for name, r in physical.items()
    ):
        raise ValueError("Unrecorded joint branch")
    rows = {
        name: _physical_row(name, owner, physical) for name, owner in selected.items()
    }

    angle_actions = {}
    for angle in angles:
        name, wood = angle["name"], angle["wood_member"]
        own = {
            key: row
            for key, row in rows.items()
            if name in (row["first"], row["second"])
        }
        wood_rows = {
            key: row
            for key, row in own.items()
            if wood in (row["first"], row["second"])
        }
        bolt_rows = {
            key: row
            for key, row in own.items()
            if ({row["first"], row["second"]} & {b["name"] for b in bolts})
        }
        header_rows = {
            key: row
            for key, row in own.items()
            if "base_header" in (row["first"], row["second"])
        }
        if (
            not wood_rows
            or not bolt_rows
            or set(own) != set(wood_rows) | set(bolt_rows) | set(header_rows)
        ):
            raise ValueError(f"Unexpected angle branch ownership: {name}")
        _points_match(wood_rows.values(), angle["vertical_points"], f"{name} wood")
        # Each header point belongs to a shared bolt, even when wood bore branches multiply.
        _points_match(bolt_rows.values(), angle["header_points"], f"{name} steel")
        _points_match(header_rows.values(), angle["contact_points"], f"{name} contact")
        origin = _vector(angle["vertical_points"][0], "angle origin")
        angle_actions[name] = {
            "wood_member": wood,
            "origin_xyz_mm": origin,
            "on_wood": _wrench(list(wood_rows.values()), wood, origin)[0],
            "on_angle_from_wood": _wrench(list(wood_rows.values()), name, origin)[0],
            "on_angle_from_shared_bolts": _wrench(
                list(bolt_rows.values()), name, origin
            )[0],
            "on_angle_from_header_contact": _wrench(
                list(header_rows.values()), name, origin
            )[0],
            "branch_names": {
                "wood": sorted(wood_rows),
                "shared_bolts": sorted(bolt_rows),
                "header_contact": sorted(header_rows),
            },
            "equilibrium": _balance(list(own.values()), name, origin),
        }

    bolt_actions = {}
    for bolt in bolts:
        name = bolt["name"]
        own = {
            key: row
            for key, row in rows.items()
            if name in (row["first"], row["second"])
        }
        groups = {"upper_steel": {}, "lower_steel": {}, "middle_wood": {}}
        for key, row in own.items():
            other = row["second"] if row["first"] == name else row["first"]
            group = (
                "upper_steel"
                if other == upper
                else "lower_steel"
                if other == lower
                else "middle_wood"
                if other == "base_header"
                else None
            )
            if group is None:
                raise ValueError(f"Unexpected shared bolt branch: {key}")
            groups[group][key] = row
        if any(not group for group in groups.values()):
            raise ValueError(f"Incomplete shared bolt branches: {name}")
        for label, field in (
            ("upper_steel", "top_point"),
            ("lower_steel", "bottom_point"),
        ):
            if field in bolt:
                _points_match(groups[label].values(), [bolt[field]], f"{name} {label}")
        wood_points = bolt.get("wood_points", bolt.get("wood_bore_points"))
        if wood_points is None and "wood_upper_point" in bolt and "wood_lower_point" in bolt:
            wood_points = [bolt["wood_upper_point"], bolt["wood_lower_point"]]
        if (
            wood_points is None
            and "wood_point" in bolt
            and len(groups["middle_wood"]) == 1
        ):
            wood_points = [bolt["wood_point"]]
        if wood_points is not None:
            _points_match(groups["middle_wood"].values(), wood_points, f"{name} wood")
        if len(groups["middle_wood"]) != 2:
            raise ValueError(f"Expected two distributed wood-bearing branches: {name}")
        for branch in groups["middle_wood"]:
            dofs = sorted(spring["dof"] for spring in record["springs"]
                          if spring["name"] == branch)
            if dofs != [1, 2]:
                raise ValueError(f"Header bore branch is not lateral-only: {branch}")
        wood_coordinates = [
            _vector(row["point"], "bolt wood point")
            for row in groups["middle_wood"].values()
        ]
        origin = _vector(
            bolt.get(
                "wood_point",
                [
                    sum(p[i] for p in wood_coordinates) / len(wood_coordinates)
                    for i in range(3)
                ],
            ),
            "bolt origin",
        )
        bolt_actions[name] = {
            "origin_xyz_mm": origin,
            "branches": {
                label: {
                    "connection_names": sorted(group),
                    "on_bolt": _wrench(list(group.values()), name, origin)[0],
                    "on_other_body": _wrench(
                        list(group.values()),
                        upper
                        if label == "upper_steel"
                        else lower
                        if label == "lower_steel"
                        else "base_header",
                        origin,
                    )[0],
                }
                for label, group in groups.items()
            },
            "equilibrium": _balance(list(own.values()), name, origin),
        }
    interfaces = {}
    for key, angle in (("principal_header", principal), ("post_header", post)):
        member = angle["wood_member"]
        stations = [station for station in record["angle_stations"]
                    if set(station["members"]) == {member, "base_header"}]
        if len(stations) != 1:
            raise ValueError(f"Missing unique original station for {member}")
        origin = _vector(stations[0]["origin"], "interface origin")
        direct_names = [name for name, owner in owners.items()
                        if {owner["first"], owner["second"]} == {member, "base_header"}]
        direct = [_physical_row(name, owners[name], physical) for name in direct_names]
        via = [rows[name] for name in angle_actions[angle["name"]]["branch_names"]["wood"]]
        interfaces[key] = {
            "origin_xyz_mm": origin,
            "on_center_member": _wrench(direct + via, member, origin)[0],
            "on_center_member_direct_contact": _wrench(direct, member, origin)[0],
            "on_center_member_via_angle": _wrench(via, member, origin)[0],
            "on_header_direct_contact": _wrench(direct, "base_header", origin)[0],
            "direct_connection_names": sorted(direct_names),
        }
    return {"angles": angle_actions, "shared_bolts": bolt_actions,
            "interfaces": interfaces}


def extract_files(report_path, record_path=None):
    report_path = Path(report_path)
    if report_path.name != "report.json":
        raise ValueError("Expected report.json")
    root = report_path.parent
    report = json.loads(report_path.read_bytes())
    sources = _manifest(report, root)
    cycles = report.get("contact_cycles")
    if not cycles or not cycles[-1].get("contact_passed"):
        raise ValueError("Final contact cycle did not pass")
    expected_record = root / cycles[-1]["directory"] / "input.json"
    record_path = Path(record_path) if record_path is not None else expected_record
    if record_path.resolve() != expected_record.resolve():
        raise ValueError("Input is not the final cycle record")
    record = json.loads(record_path.read_bytes())
    if (
        report.get("numerically_accepted") is not True
        or any(
            report.get(key) is not True
            for key in (
                "contact_active_set_converged",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "mpc_check_passed",
            )
        )
        or not report.get("member_equilibrium")
        or any(
            row.get("passed") is not True
            for row in report["member_equilibrium"].values()
        )
    ):
        raise ValueError("Native numerical acceptance failed")
    scope_path = root / "diagnostic-scope.json"
    scope = json.loads(scope_path.read_bytes())
    if (
        scope != report.get("diagnostic_scope")
        or scope.get("source_geometry") != GEOMETRY
        or scope.get("numerically_converged") is not True
        or any(
            scope.get(key) is not False
            for key in (
                "qualified_bolted_joint_demands",
                "resistance_checked",
                "acceptance",
                "drilling_released",
            )
        )
    ):
        raise ValueError("Diagnostic scope mismatch")
    spec = record.get("diagnostic_center_joint", {})
    spring = scope.get("spring_n_per_mm")
    if (not isinstance(spec, dict) or not isinstance(spring, (float, int))
            or not math.isfinite(spring) or spring <= 0
            or any(spec.get(name) != spring for name in
                   ("wood_bearing_lateral_n_per_mm", "flange_contact_n_per_mm"))
            or any(spec.get(name) != {"axial_n_per_mm": spring, "lateral_n_per_mm": spring}
                   for name in ("vertical_spring", "steel_bolt_spring"))):
        raise ValueError("Joint slip scope differs from native record")
    case = scope.get("case")
    expected = CASES.get(case)
    force = record.get("force_xyz_n")
    if (
        not expected
        or record.get("candidate") != CANDIDATE
        or report.get("candidate") != CANDIDATE
        or record.get("hold") != expected[0]
        or report.get("parameters", {}).get("hold") != expected[0]
        or force != report.get("parameters", {}).get("force_xyz_n")
        or not isinstance(force, list)
        or len(force) != 3
        or not all(math.isfinite(float(value)) for value in force)
        or force[:2] != list(expected[1:])
        or record.get("pounds") != 250.0
        or report.get("parameters", {}).get("pounds") != 250.0
        or record.get("diagnostic_only") is not True
        or any(
            record.get(key) is not False
            for key in (
                "acceptance",
                "actual_joint_demands_qualified",
                "bolted_joint_demands",
                "qualified_for_design",
            )
        )
    ):
        raise ValueError("Candidate or case identity mismatch")
    for part in ("main_lower", "main_upper", "kicker"):
        for side, expected_width in (
            ("left", [-1219.2, -1.5875]),
            ("right", [-1.5875, 1216.025]),
        ):
            row = record.get("kerf_panel_bounds", {}).get(f"{part}_{side}", {})
            for key in ("actual_x_mm", "mesh_x_mm"):
                width = row.get(key)
                if (
                    not isinstance(width, list)
                    or len(width) != 2
                    or any(
                        not math.isclose(float(a), b, abs_tol=1e-4)
                        for a, b in zip(width, expected_width)
                    )
                ):
                    raise ValueError("Kerf-right width mismatch")
    result = extract(report, record)
    result.update(
        source={
            "case": case,
            "report_sha256": _digest(report_path),
            "record_sha256": _digest(record_path),
            "producer_sha256": {
                name: sources[name]
                for name in (
                    "scripts/bolted_center_native_diagnostic.py",
                    "scripts/bolted_center_joint_model.py",
                )
            },
        },
        classification="provisional_native_AB205_diagnostic",
        limitations="Exploratory signed simultaneous actions only; no qualified bolt demands, rating, resistance acceptance or drilling release",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("record", type=Path, nargs="?")
    args = parser.parse_args()
    print(json.dumps(extract_files(args.report, args.record), indent=2))
