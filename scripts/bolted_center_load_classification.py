"""Provisional same-case load directions at the accepted center AB205 bores.

No bolt capacity, NDS check, or fabrication acceptance is implied.
"""

import argparse
import json
import math
from pathlib import Path

from scripts.bolted_center_candidate_extract import extract_files
from scripts.bolted_center_demand_extract import _physical_row, _vector


def _unit(values, label):
    vector = _vector(values, label)
    length = math.hypot(*vector)
    if not math.isclose(length, 1.0, abs_tol=1e-5):
        raise ValueError(f"{label} must be a unit vector")
    return [value / length for value in vector]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def classify_force(force_xyz_n, bolt_axis, grain_axis):
    """Resolve signed wood force; class is only lateral direction dominance."""
    force = _vector(force_xyz_n, "force")
    bolt = _unit(bolt_axis, "bolt axis")
    grain = _unit(grain_axis, "grain axis")
    if abs(_dot(bolt, grain)) > 1e-5:
        raise ValueError("Grain axis must be perpendicular to bolt axis")
    axial = _dot(force, bolt)
    lateral = [f - axial * a for f, a in zip(force, bolt)]
    lateral_mag = math.hypot(*lateral)
    parallel = _dot(lateral, grain)
    perpendicular_vector = [f - parallel * g for f, g in zip(lateral, grain)]
    perpendicular = math.hypot(*perpendicular_vector)
    tolerance = 1e-7 * max(1.0, math.hypot(*force))
    if lateral_mag <= tolerance:
        direction = "zero_lateral"
    elif abs(abs(parallel) - perpendicular) <= tolerance:
        direction = "equal_components"
    elif abs(parallel) > perpendicular:
        direction = "parallel_dominant"
    else:
        direction = "perpendicular_dominant"
    return {
        "force_on_wood_xyz_n": force,
        "bolt_axis_xyz": bolt,
        "grain_axis_xyz": grain,
        "axial_force_along_bolt_n": axial,
        "lateral_force_xyz_n": lateral,
        "lateral_magnitude_n": lateral_mag,
        "parallel_to_grain_n": parallel,
        "perpendicular_to_grain_xyz_n": perpendicular_vector,
        "perpendicular_to_grain_n": perpendicular,
        "direction_class": direction,
    }


def _member_axis(record, name):
    members = [row for row in record["members"] if row["name"] == name]
    if len(members) != 1:
        raise ValueError(f"Expected one CAD member: {name}")
    member = members[0]
    start = _vector(member["start"], "member start")
    end = _vector(member["end"], "member end")
    delta = [b - a for a, b in zip(start, end)]
    span = math.hypot(*delta)
    if span <= 0:
        raise ValueError(f"Degenerate CAD member: {name}")
    grain = _unit(member["axis"], "member axis")
    if _dot(grain, [value / span for value in delta]) < 1 - 1e-5:
        raise ValueError(f"CAD member axis/endpoints disagree: {name}")
    return grain


def _member_section_axis(record, name):
    members = [row for row in record["members"] if row["name"] == name]
    if len(members) != 1:
        raise ValueError(f"Expected one CAD member: {name}")
    axis = _unit(members[0]["section_u"], "member section axis")
    if abs(_dot(axis, _member_axis(record, name))) > 1e-5:
        raise ValueError(f"Member section/grain axes disagree: {name}")
    return axis


def classify_files(report_path, record_path=None):
    """Reuse extractor authentication, then classify its exact owned branches."""
    extracted = extract_files(report_path, record_path)
    report_path = Path(report_path)
    report = json.loads(report_path.read_bytes())
    final_record = report_path.parent / report["contact_cycles"][-1]["directory"] / "input.json"
    record = json.loads(final_record.read_bytes())
    spec = record["diagnostic_center_joint"]
    owners = record["connection_ownership"]
    physical = report["physical_connection_forces"]
    if len(spec["angles"]) != 2 or len(spec["shared_header_bolts"]) != 2:
        raise ValueError("Expected two angles and two shared bolts")
    vertical = {}
    bores = {}

    def classify_branch(name, wood, point, expected_axis):
        owner = owners[name]
        row = _physical_row(name, owner, physical)
        if ({owner["first"], owner["second"]} != {wood, other}
                or _vector(owner["point"], "branch point") != _vector(point, "specified point")):
            raise ValueError(f"Branch ownership or point mismatch: {name}")
        if abs(_dot(_unit(owner["axis"], "owned bolt axis"), expected_axis)) < 1 - 1e-5:
            raise ValueError(f"Branch bolt axis mismatch: {name}")
        force = row["force_on_first_xyz_n"] if row["first"] == wood else row["force_on_second_xyz_n"]
        result = classify_force(force, owner["axis"], _member_axis(record, wood))
        result["connection_name"] = name
        result["point_xyz_mm"] = _vector(point, "branch point")
        return result

    for angle in spec["angles"]:
        name, wood = angle["name"], angle["wood_member"]
        names = extracted["angles"][name]["branch_names"]["wood"]
        points = angle["vertical_points"]
        if len(names) != 2 or len(points) != 2:
            raise ValueError(f"Expected two vertical bolt branches: {name}")
        other = name
        by_point = {tuple(owners[branch]["point"]): branch for branch in names}
        if set(by_point) != {tuple(point) for point in points}:
            raise ValueError(f"Vertical branch inventory mismatch: {name}")
        if len(by_point) != 2:
            raise ValueError(f"Duplicate vertical branch point: {name}")
        expected_axis = _unit(_member_section_axis(record, wood), "member section axis")
        branches = [classify_branch(by_point[tuple(point)], wood, point, expected_axis)
                    for point in points]
        for branch in branches:
            dofs = sorted(spring["dof"] for spring in record["springs"]
                          if spring["name"] == branch["connection_name"])
            if dofs != [1, 2, 3]:
                raise ValueError("Vertical bolt branch DOFs mismatch")
        vertical[name] = {"wood_member": wood, "branches": branches}

    for bolt in spec["shared_header_bolts"]:
        name = bolt["name"]
        names = extracted["shared_bolts"][name]["branches"]["middle_wood"]["connection_names"]
        points = [bolt["wood_upper_point"], bolt["wood_lower_point"]]
        if len(names) != 2:
            raise ValueError(f"Expected two header bore branches: {name}")
        other = name
        by_point = {tuple(owners[branch]["point"]): branch for branch in names}
        if set(by_point) != {tuple(point) for point in points}:
            raise ValueError(f"Header bore inventory mismatch: {name}")
        if len(by_point) != 2:
            raise ValueError(f"Duplicate header bore point: {name}")
        top = _vector(bolt["top_point"], "bolt top")
        bottom = _vector(bolt["bottom_point"], "bolt bottom")
        direction = [a - b for a, b in zip(top, bottom)]
        span = math.hypot(*direction)
        if span <= 0:
            raise ValueError(f"Degenerate shared bolt: {name}")
        axis = [value / span for value in direction]
        bores[name] = {"wood_member": "base_header", "branches": [
            classify_branch(by_point[tuple(point)], "base_header", point, axis)
            for point in points
        ]}

    return {
        "source": extracted["source"],
        "joint_spring_n_per_mm": record["diagnostic_center_joint"]["wood_bearing_lateral_n_per_mm"],
        "vertical_ab205": vertical,
        "shared_header_bores": bores,
        "classification": "provisional_load_direction_only",
        "limitations": "Same-case exploratory forces; no qualified bolt demand, capacity, NDS pass, or drilling release",
    }


def compare_stiffness_runs(report_paths):
    """Report observed dominance reversals only among the three supplied solves."""
    if len(report_paths) != 3:
        raise ValueError("Expected three distinct stiffness runs")
    runs = [classify_files(path) for path in report_paths]
    stiffnesses = [run["joint_spring_n_per_mm"] for run in runs]
    if set(stiffnesses) != {1000.0, 10000.0, 100000.0}:
        raise ValueError("Expected three distinct 1k/10k/100k stiffness runs")
    sources = [run["source"] for run in runs]
    if (len({source["case"] for source in sources}) != 1
            or len({tuple(sorted(source["producer_sha256"].items())) for source in sources}) != 1):
        raise ValueError("Stiffness runs do not share case and producer")
    by_run = {}
    for run in runs:
        classes = {}
        for group in ("vertical_ab205", "shared_header_bores"):
            for body in run[group].values():
                for branch in body["branches"]:
                    classes[branch["connection_name"]] = branch["direction_class"]
        by_run[str(int(run["joint_spring_n_per_mm"]))] = classes
    inventories = [set(classes) for classes in by_run.values()]
    if any(names != inventories[0] for names in inventories[1:]):
        raise ValueError("Stiffness run branch inventory differs")
    geometry = []
    for run in runs:
        geometry.append({
            branch["connection_name"]: (
                body["wood_member"], branch["point_xyz_mm"],
                branch["bolt_axis_xyz"], branch["grain_axis_xyz"]
            )
            for group in ("vertical_ab205", "shared_header_bores")
            for body in run[group].values() for branch in body["branches"]
        })
    if any(current != geometry[0] for current in geometry[1:]):
        raise ValueError("Stiffness run branch geometry differs")
    reversal = {name: {classes[name] for classes in by_run.values()} >= {
        "parallel_dominant", "perpendicular_dominant"} for name in inventories[0]}
    return {
        "source": {"case": sources[0]["case"], "runs": sources},
        "runs_n_per_mm": sorted(stiffnesses),
        "branch_classes_by_run": by_run,
        "reversal_by_branch": reversal,
        "any_observed_reversal": any(reversal.values()),
        "limitations": "Observed direction dominance at three provisional stiffnesses only; no capacity or NDS pass",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+")
    args = parser.parse_args()
    result = (classify_files(args.reports[0]) if len(args.reports) == 1
              else compare_stiffness_runs(args.reports))
    print(json.dumps(result, indent=2))
