#!/usr/bin/env python3
"""Replay conditional square-end tension comparisons from frozen upper actions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def end_reference(diameter_mm, angle_degrees):
    """Declared softwood interpolation, supported by historical Commentary."""
    if not 0 <= angle_degrees <= 90:
        raise ValueError("Angle must be from zero through ninety degrees")
    return diameter_mm * (7 - 3 * angle_degrees / 90)


def scope_group(row):
    axis = row["axis_id"]
    if row["block"] in (
        "top_center_left_cleat",
        "top_center_right_cleat",
    ) and axis.rsplit("/", 1)[-1].startswith("principal_"):
        return row["block"] + "/principal-pair-end-branch"
    if row["block"] == "wj04_upper_g7_crosscut_full_stock_cleat":
        interface = (
            "rail" if axis.endswith(("upper_rail_1", "upper_rail_2")) else "principal"
        )
        return row["block"] + "/" + interface + "-pair-end-branch"
    return None


def produce():
    freeze = json.loads((HERE / "end-branch-freeze.json").read_text())
    for pin in freeze["sources"]:
        if sha(ROOT / pin["path"]) != pin["sha256"]:
            raise RuntimeError("Frozen source changed: " + pin["path"])
    diameter = freeze["nominal_D_mm"]
    assert diameter == 6.35
    assert freeze["current_2024_commentary_interpolation_verified"] is False
    # Known answers exercise the two endpoints and an intermediate angle;
    # these do not establish standard applicability to a complete joint.
    expected = {0: 44.45, 45: 34.925, 90: 25.4}
    for angle, answer in expected.items():
        assert math.isclose(end_reference(diameter, angle), answer, abs_tol=1e-12)
    output = {
        "schema": "upper-conditional-tension-end-branch/v1",
        "status": "DECLARED_ANGLE_INTERPOLATION_SENSITIVITY_NO_ADOPTED_GROUP_FACTOR",
        "producer_sha256": sha(Path(__file__)),
        "freeze_sha256": sha(HERE / "end-branch-freeze.json"),
        "primary_standard": freeze["primary_standard"],
        "historical_interpolation_source": freeze["historical_interpolation_source"],
        "current_2024_commentary_interpolation_verified": False,
        "nominal_D_mm": diameter,
        "known_answer_end_reference_mm": expected,
        "rows": [],
        "pair_branch_summaries": [],
        "complete_joint_accepted": False,
        "six_case_envelope_established": False,
        "reviewed_geometry_changed": False,
        "native_solve_executed": False,
        "limits": [
            "The grain-angle interpolation is a declared sensitivity supported by official 2018 Commentary. Exact 2024 Commentary applicability was not directly verified and is not inferred from the pinned normative Chapter 12 PDF.",
            "The tension end branch is conditional; signed bearing toward an end alone does not establish a complete member tension/compression classification.",
            "Outer square-end assumption only. Principal grain-negative foot cuts are explicitly excluded; internal bores, shoulders and continuous thickness extrema remain separate.",
            "Pair minima are scoped end-branch summaries, not independently resisting group capacities. Shared-member group definition and spacing factors are unresolved.",
            "No rule or geometry factor for oblique edge loading is inferred from the tension end interpolation.",
            "Axial outer-seat ties remain a separate bolt/washer/member path, not part of the lateral vector in this comparison.",
        ],
    }
    max_axial_projection = 0.0
    groups = defaultdict(list)
    source_geometry = {}
    axes = set()
    for relative in freeze["action_reports"]:
        report = json.loads((ROOT / relative).read_text())
        assert not report["complete_joint_resistance_established"]
        assert not report["six_case_envelope_established"]
        for action in report["bolt_actions"]:
            group = scope_group(action)
            if group is None:
                continue
            axes.add(action["axis_id"])
            geometry = report["geometry_by_axis"][action["axis_id"]]
            axis = geometry["head_to_nut_axis_xyz"]
            axis = [v / math.sqrt(dot(axis, axis)) for v in axis]
            axial_projection = abs(dot(action["lateral_force_on_block_n"], axis))
            max_axial_projection = max(max_axial_projection, axial_projection)
            assert axial_projection < 1e-8
            for role, direction in action["member_directions"].items():
                member = geometry["members"][role]
                source_geometry[member["finished_step"]] = member[
                    "finished_step_sha256"
                ]
                assert abs(dot(member["conditional_grain_xyz"], axis)) < 1e-8
                sign = 1 if role == "block" else -1
                force = [sign * v for v in action["lateral_force_on_block_n"]]
                grain = dot(force, member["conditional_grain_xyz"])
                cross = dot(
                    force,
                    direction["cross_grain_edge_direction"][
                        "component_axis_global_xyz"
                    ],
                )
                assert math.isclose(
                    grain, direction["force_parallel_to_grain_signed_n"], abs_tol=1e-8
                )
                assert math.isclose(
                    cross,
                    direction["force_cross_grain_signed_on_frame_axis_n"],
                    abs_tol=1e-8,
                )
                angle = math.degrees(math.atan2(abs(cross), abs(grain)))
                assert math.isclose(
                    angle, direction["unsigned_load_to_grain_degrees"], abs_tol=1e-8
                )
                end = direction["grain_end_direction"]
                distance = end["distance_to_loaded_outer_boundary_mm"]
                is_foot = (
                    member["member"].startswith("base_principal_center_")
                    and end["local_boundary_side"] == "lower_coordinate_boundary"
                )
                status = "square_outer_end_tension_branch_assumed"
                if distance is None:
                    status = "no_signed_grain_component_no_end_branch"
                elif is_foot:
                    status = "angled_foot_profile_boundary_excluded"
                full = end_reference(diameter, angle)
                eligible = status == "square_outer_end_tension_branch_assumed"
                ratio = distance / full if eligible else None
                factor = min(1.0, ratio) if eligible and ratio >= 0.5 else None
                row = {
                    "source_report": relative,
                    "case": action["case"],
                    "load_factor": action["load_factor"],
                    "block": action["block"],
                    "pair_scope": group,
                    "axis_id": action["axis_id"],
                    "role": role,
                    "member": member["member"],
                    "signed_grain_force_n": grain,
                    "signed_cross_grain_force_n": cross,
                    "unsigned_load_to_grain_degrees": angle,
                    "loaded_outer_boundary_side": end["local_boundary_side"],
                    "distance_to_loaded_outer_boundary_mm": distance,
                    "conditional_full_tension_end_reference_mm": full,
                    "conditional_half_tension_end_minimum_mm": full / 2,
                    "conditional_end_ratio": ratio,
                    "conditional_tension_end_factor_for_square_end": factor,
                    "within_interpolated_half_distance_floor": ratio >= 0.5
                    if eligible
                    else None,
                    "boundary_status": status,
                    "pure_parallel_tension_ratio_only": distance / (7 * diameter)
                    if eligible
                    else None,
                    "geometry_factor_adopted": False,
                }
                output["rows"].append(row)
                groups[(group, action["case"], action["load_factor"])].append(row)
    for path, expected_hash in source_geometry.items():
        assert sha(ROOT / path) == expected_hash, path + " finished geometry changed"
    for (group, case, factor), rows in sorted(groups.items()):
        assert len(rows) == 4
        eligible = [
            r
            for r in rows
            if r["conditional_tension_end_factor_for_square_end"] is not None
        ]
        excluded = [
            r
            for r in rows
            if r["boundary_status"] != "square_outer_end_tension_branch_assumed"
        ]
        minimum = (
            min(
                eligible,
                key=lambda r: r["conditional_tension_end_factor_for_square_end"],
            )
            if eligible
            else None
        )
        output["pair_branch_summaries"].append(
            {
                "pair_scope": group,
                "case": case,
                "load_factor": factor,
                "minimum_of_eligible_square_end_factors": minimum[
                    "conditional_tension_end_factor_for_square_end"
                ]
                if minimum
                else None,
                "controlling_square_end_axis": minimum["axis_id"] if minimum else None,
                "controlling_square_end_member": minimum["member"] if minimum else None,
                "excluded_boundary_records": len(excluded),
                "below_half_floor_records": sum(
                    r["within_interpolated_half_distance_floor"] is False for r in rows
                ),
                "complete_end_branch_established": False,
                "complete_group_geometry_factor_established": False,
            }
        )
    assert len(axes) == 8 and len(output["rows"]) == 336
    assert len(output["pair_branch_summaries"]) == 84
    output["counts"] = {
        "physical_axes": 8,
        "member_direction_records": 336,
        "two_bolt_pair_histories": 84,
        "cases": 3,
        "increments_per_case": 7,
    }
    output["max_lateral_force_projection_on_bolt_axis_n"] = max_axial_projection
    output["checked_finished_step_sources"] = source_geometry
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = produce()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, list(report["rows"][0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(report["rows"])
    for name, text in {
        "conditional-end-branches.json": json.dumps(report, indent=2, sort_keys=True)
        + "\n",
        "conditional-end-branches.csv": stream.getvalue(),
    }.items():
        if args.verify:
            assert (HERE / name).read_text() == text
        else:
            (HERE / name).write_text(text)
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "full_load_pair_branches": [
                    r for r in report["pair_branch_summaries"] if r["load_factor"] == 1
                ],
            },
            indent=2,
        )
    )
