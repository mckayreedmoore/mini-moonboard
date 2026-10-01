#!/usr/bin/env python3
"""Build a pinned, geometry-only inventory of the current bolt axes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any


SOURCE_PINS = {
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
}

NEAR_PARALLEL_DEGREES = 1.0  # Descriptive flag only; not a design criterion.
PARALLEL_AXES_TOLERANCE_DEGREES = 1e-6
AXIAL_ZERO_TOLERANCE_MM = 1e-6
OUTPUT_NAMES = (
    "bolt-groups.json",
    "bolt-groups.csv",
    "bolt-group-axis-receivers.csv",
    "bolt-group-axis-spacings.csv",
    "retained-frame-bolt-axes.csv",
)


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "current-candidate.json").is_file() and (parent / "docs/wood-joints-mvp").is_dir():
            return parent
    raise RuntimeError("Could not locate repository root from this script.")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_pinned_json(root: Path, relative: str) -> tuple[dict[str, Any], str]:
    path = root / relative
    actual = sha256(path)
    expected = SOURCE_PINS[relative]
    if actual != expected:
        raise RuntimeError(f"Pinned source changed: {relative}\nexpected {expected}\nactual   {actual}")
    return json.loads(path.read_text(encoding="utf-8")), actual


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def unit(vector: list[float]) -> list[float]:
    length = norm(vector)
    if length == 0:
        raise ValueError("Zero vector cannot define an axis.")
    return [value / length for value in vector]


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def vector_sub(left: list[float], right: list[float]) -> list[float]:
    return [a - b for a, b in zip(left, right)]


def axis_normal_spacing(delta: list[float], axis_a: list[float], axis_b: list[float]) -> dict[str, Any]:
    unit_a = unit(axis_a)
    unit_b = unit(axis_b)
    alignment_abs_dot = min(1.0, abs(dot(unit_a, unit_b)))
    misalignment_deg = math.degrees(math.acos(alignment_abs_dot))
    parallel = misalignment_deg <= PARALLEL_AXES_TOLERANCE_DEGREES
    if not parallel:
        return {
            "axis_a_unit_global_xyz": unit_a,
            "axis_b_unit_global_xyz": unit_b,
            "axis_pair_alignment_abs_dot": alignment_abs_dot,
            "axis_pair_misalignment_deg": misalignment_deg,
            "axes_parallel_for_normal_projection": False,
            "normal_projection_status": "not_reported_axes_not_parallel_within_tolerance",
            "axis_a_reference_signed_component_mm": None,
            "axis_a_reference_absolute_component_mm": None,
            "axis_a_reference_component_exceeds_zero_tolerance_mm": None,
            "perpendicular_inter_axis_pitch_mm": None,
            "perpendicular_axis_center_delta_global_xyz_mm": None,
        }
    axial_signed = dot(delta, unit_a)
    axial_vector = [axial_signed * value for value in unit_a]
    perpendicular_delta = [delta[index] - axial_vector[index] for index in range(3)]
    return {
        "axis_a_unit_global_xyz": unit_a,
        "axis_b_unit_global_xyz": unit_b,
        "axis_pair_alignment_abs_dot": alignment_abs_dot,
        "axis_pair_misalignment_deg": misalignment_deg,
        "axes_parallel_for_normal_projection": True,
        "normal_projection_status": "reported_axis_a_reference_parallel_or_antiparallel_axes",
        "axis_a_reference_signed_component_mm": axial_signed,
        "axis_a_reference_absolute_component_mm": abs(axial_signed),
        "axis_a_reference_component_exceeds_zero_tolerance_mm": abs(axial_signed) > AXIAL_ZERO_TOLERANCE_MM,
        "perpendicular_inter_axis_pitch_mm": norm(perpendicular_delta),
        "perpendicular_axis_center_delta_global_xyz_mm": perpendicular_delta,
    }


def angle_to_grain_deg(axis: list[float], grain: list[float]) -> float:
    cosine = min(1.0, max(0.0, abs(dot(unit(axis), unit(grain)))))
    return math.degrees(math.acos(cosine))


def json_cell(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def wood_grain_directions(block_map: dict[str, Any], frame_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in block_map["members"]:
        member_id = record["part_id"]
        assignment = record["conditional_grain_assignment"]
        vector = assignment["grain_direction_global_xyz"]
        result[member_id] = {
            "grain_axis_global_xyz": unit(vector),
            "source_map": "current-block-material-frame-map-attempt02",
            "grain_assignment_basis": assignment.get("grain_basis"),
            "delivered_stock_observed": assignment.get("delivered_stock_observed", False),
        }
    for record in frame_map["members"]:
        member_id = record["member_id"]
        assignment = record["conditional_grain_assignment"]
        vector = assignment["proposed_global_xyz"]
        if member_id in result:
            raise AssertionError(f"Duplicate timber/block grain map member: {member_id}")
        result[member_id] = {
            "grain_axis_global_xyz": unit(vector),
            "source_map": "current-frame-timber-material-frame-map-attempt01",
            "grain_assignment_basis": assignment.get("source_inventory_grain_rule"),
            "delivered_stock_observed": assignment.get("delivered_stock_observed", False),
        }
    return result


def receiver_interval_bounds(axis: dict[str, Any], receiver_id: str) -> list[float] | None:
    matches = [item for item in axis["geometry"]["wood_receiver_intervals"] if item["receiver_id"] == receiver_id]
    if len(matches) != 1:
        return None
    item = matches[0]
    intervals = item.get("current_shaft_intersection_solid_intervals_from_underhead_mm")
    if intervals is None:
        intervals = item.get("intersection_solid_intervals_from_underhead_mm")
    if not intervals:
        return None
    return [min(interval[0] for interval in intervals), max(interval[1] for interval in intervals)]


def interval_order_proposal(axis: dict[str, Any], receiver_ids: list[str]) -> dict[str, Any]:
    bounds = {member_id: receiver_interval_bounds(axis, member_id) for member_id in receiver_ids}
    if len(receiver_ids) != 2:
        return {
            "status": "not_emitted_for_three_member_stack",
            "receiver_intervals_from_underhead_mm": bounds,
            "delivered_head_to_nut_order_verified": False,
        }
    if any(value is None for value in bounds.values()):
        return {
            "status": "unresolved_missing_interval",
            "receiver_intervals_from_underhead_mm": bounds,
            "delivered_head_to_nut_order_verified": False,
        }
    first, second = receiver_ids
    first_bounds = bounds[first]
    second_bounds = bounds[second]
    assert first_bounds is not None and second_bounds is not None
    tolerance = 1e-6
    if first_bounds[1] <= second_bounds[0] + tolerance:
        order = [first, second]
        status = "geometric_interval_order_proposal_head_to_nut"
    elif second_bounds[1] <= first_bounds[0] + tolerance:
        order = [second, first]
        status = "geometric_interval_order_proposal_head_to_nut"
    else:
        order = None
        status = "overlapping_intervals_order_unresolved"
    return {
        "status": status,
        "receiver_order_head_to_nut_proposal": order,
        "receiver_intervals_from_underhead_mm": bounds,
        "delivered_head_to_nut_order_verified": False,
    }


def grouping_key(axis: dict[str, Any]) -> tuple[Any, ...]:
    station = axis.get("station_id")
    receivers = tuple(sorted(axis["receiver_member_ids"]))
    if station is None:
        # The input lacks a station identifier for these rows. Scope fallback
        # by its source family/trial while keeping that limitation explicit.
        return (None, axis.get("family"), axis.get("trial_id"), receivers)
    return (station, None, None, receivers)


def axis_record(axis: dict[str, Any], group_id: str, grains: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    geometry = axis["geometry"]
    center = list(geometry["shaft_center_global_xyz_mm"])
    raw_axis = list(geometry["axis_head_to_nut_global"])
    axis_unit = unit(raw_axis)
    if abs(norm(raw_axis) - 1.0) > 1e-7:
        raise AssertionError(f"Source bolt axis is not unit length: {axis['axis_id']}")
    receivers = sorted(axis["receiver_member_ids"])
    intervals = interval_order_proposal(axis, receivers)
    record = {
        "axis_id": axis["axis_id"],
        "group_id": group_id,
        "station_id": axis.get("station_id"),
        "family": axis.get("family"),
        "trial_id": axis.get("trial_id"),
        "receiver_member_ids": receivers,
        "receiver_member_count": len(receivers),
        "geometric_member_pair_associations": axis["geometric_member_pair_associations"],
        "shaft_center_global_xyz_mm": center,
        "modeled_shaft_diameter_mm": geometry["modeled_shaft_diameter_mm"],
        "axis_head_to_nut_unit_global_xyz": axis_unit,
        "source_axis_norm": norm(raw_axis),
        "modeled_underhead_to_tip_mm": geometry.get("modeled_underhead_to_tip_mm"),
        "modeled_shaft_occupied_length_mm": geometry.get("modeled_shaft_occupied_length_mm"),
        "geometric_receiver_order_proposal": intervals,
        "nds_load_aligned_row_assessment": "not_assessed_geometry_groups_are_not_nds_rows",
    }
    receiver_rows = []
    for member_id in receivers:
        grain = grains[member_id]
        grain_axis = grain["grain_axis_global_xyz"]
        angle = angle_to_grain_deg(axis_unit, grain_axis)
        receiver_rows.append({
            "group_id": group_id,
            "axis_id": axis["axis_id"],
            "station_id": axis.get("station_id"),
            "family": axis.get("family"),
            "trial_id": axis.get("trial_id"),
            "geometry_group_type": "three_member_stack_preserved" if len(receivers) == 3 else "two_member_receiver_pair",
            "receiver_member_count": len(receivers),
            "receiver_member_id": member_id,
            "shaft_center_global_xyz_mm": center,
            "modeled_shaft_diameter_mm": geometry["modeled_shaft_diameter_mm"],
            "axis_head_to_nut_unit_global_xyz": axis_unit,
            "source_proposed_grain_unit_global_xyz": grain_axis,
            "axis_to_grain_angle_deg_unsigned": angle,
            "parallel_to_grain_within_1deg_descriptive_flag": angle <= NEAR_PARALLEL_DEGREES,
            "grain_map_source": grain["source_map"],
            "grain_proposal_basis": grain["grain_assignment_basis"],
            "delivered_stock_observed": grain["delivered_stock_observed"],
        })
    return record, receiver_rows


def build(root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    rel_manifest, rel_block, rel_frame = SOURCE_PINS
    manifest, manifest_sha = read_pinned_json(root, rel_manifest)
    block_map, block_sha = read_pinned_json(root, rel_block)
    frame_map, frame_sha = read_pinned_json(root, rel_frame)
    grains = wood_grain_directions(block_map, frame_map)

    candidate_axes = manifest["candidate_bolt_axes"]
    retained_axes = manifest["retained_frame_bolt_axes"]
    if len(candidate_axes) != 92:
        raise AssertionError(f"Expected 92 candidate axes from the pinned manifest; got {len(candidate_axes)}")
    if len(retained_axes) != 12:
        raise AssertionError(f"Expected 12 separately retained axes; got {len(retained_axes)}")

    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for axis in candidate_axes:
        receivers = axis["receiver_member_ids"]
        if len(receivers) not in (2, 3):
            raise AssertionError(f"Unexpected receiver count for {axis['axis_id']}: {receivers}")
        if len(set(receivers)) != len(receivers):
            raise AssertionError(f"Duplicate receiver member in {axis['axis_id']}")
        unknown = set(receivers) - grains.keys()
        if unknown:
            raise AssertionError(f"Receiver member(s) lack a pinned grain map: {sorted(unknown)}")
        expected_pairs = {tuple(pair) for pair in itertools.combinations(sorted(receivers), 2)}
        actual_pairs = {tuple(sorted(item["member_pair"])) for item in axis["geometric_member_pair_associations"]}
        if actual_pairs != expected_pairs or len(axis["geometric_member_pair_associations"]) != len(expected_pairs):
            raise AssertionError(f"Receiver-pair associations do not reconcile for {axis['axis_id']}")
        grouped.setdefault(grouping_key(axis), []).append(axis)

    group_rows: list[dict[str, Any]] = []
    axis_records: list[dict[str, Any]] = []
    receiver_rows: list[dict[str, Any]] = []
    spacing_rows: list[dict[str, Any]] = []
    json_groups: list[dict[str, Any]] = []
    for ordinal, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple("" if v is None else str(v) for v in item[0])), 1):
        group_id = f"BG{ordinal:03d}"
        members = sorted(members, key=lambda item: item["axis_id"])
        representative = members[0]
        receiver_ids = sorted(representative["receiver_member_ids"])
        if any(sorted(item["receiver_member_ids"]) != receiver_ids for item in members):
            raise AssertionError(f"Inconsistent receivers in {group_id}")
        if any(item.get("station_id") != representative.get("station_id") for item in members):
            raise AssertionError(f"Inconsistent station id in {group_id}")
        group_type = "three_member_stack_preserved" if len(receiver_ids) == 3 else "two_member_receiver_pair"
        has_station = representative.get("station_id") is not None
        group_basis = "exact_manifest_station_id_plus_full_receiver_member_set" if has_station else "station_id_missing_scoped_by_family_trial_and_full_receiver_member_set"
        family_values = sorted({item.get("family") for item in members if item.get("family") is not None})
        trial_values = sorted({item.get("trial_id") for item in members if item.get("trial_id") is not None})
        group_axis_records = []
        group_receiver_rows = []
        for axis in members:
            record, rows = axis_record(axis, group_id, grains)
            axis_records.append(record)
            group_axis_records.append(record)
            receiver_rows.extend(rows)
            group_receiver_rows.extend(rows)

        group_spacing_rows = []
        for left, right in itertools.combinations(members, 2):
            left_center = left["geometry"]["shaft_center_global_xyz_mm"]
            right_center = right["geometry"]["shaft_center_global_xyz_mm"]
            delta = vector_sub(right_center, left_center)
            distance = norm(delta)
            projections = {}
            for receiver_id in receiver_ids:
                grain_axis = grains[receiver_id]["grain_axis_global_xyz"]
                signed = dot(delta, grain_axis)
                projections[receiver_id] = {
                    "projection_signed_mm": signed,
                    "projection_absolute_mm": abs(signed),
                    "grain_normal_center_spacing_component_mm": math.sqrt(max(0.0, distance * distance - signed * signed)),
                }
            axis_components = axis_normal_spacing(
                delta,
                left["geometry"]["axis_head_to_nut_global"],
                right["geometry"]["axis_head_to_nut_global"],
            )
            row = {
                "group_id": group_id,
                "axis_id_a": left["axis_id"],
                "axis_id_b": right["axis_id"],
                "station_id": representative.get("station_id"),
                "receiver_member_ids": receiver_ids,
                "center_a_global_xyz_mm": left_center,
                "center_b_global_xyz_mm": right_center,
                "center_delta_b_minus_a_global_xyz_mm": delta,
                "center_spacing_euclidean_mm": distance,
                "axis_normal_center_spacing_components": axis_components,
                "center_spacing_projected_by_source_proposed_grain": projections,
                "meaning": "Euclidean shaft-center distance is not perpendicular inter-axis pitch; the perpendicular inter-axis pitch is reported only when the two modeled bolt axes are parallel within tolerance.",
            }
            spacing_rows.append(row)
            group_spacing_rows.append(row)

        pair_associations = sorted({
            tuple(sorted(association["member_pair"]))
            for axis in members
            for association in axis["geometric_member_pair_associations"]
        })
        json_group = {
            "group_id": group_id,
            "geometry_group_type": group_type,
            "grouping_basis": group_basis,
            "station_id": representative.get("station_id"),
            "station_id_present_in_source": has_station,
            "family": family_values,
            "trial_id": trial_values,
            "receiver_member_ids": receiver_ids,
            "geometric_pair_associations_within_receiver_set": [list(pair) for pair in pair_associations],
            "axis_ids": [item["axis_id"] for item in members],
            "axes": group_axis_records,
            "center_spacing_records": group_spacing_rows,
            "nds_load_aligned_row_assessment": "not_assessed_geometry_group_does_not_establish_load_aligned_nds_row",
            "group_factor_Cg_or_force": None,
        }
        json_groups.append(json_group)
        group_row = {
            "group_id": group_id,
            "geometry_group_type": group_type,
            "grouping_basis": group_basis,
            "station_id": representative.get("station_id"),
            "station_id_present_in_source": has_station,
            "family": json_cell(family_values),
            "trial_id": json_cell(trial_values),
            "receiver_member_ids": json_cell(receiver_ids),
            "geometric_pair_associations": json_cell([list(pair) for pair in pair_associations]),
            "axis_ids": json_cell([item["axis_id"] for item in members]),
            "axis_count": len(members),
            "center_spacing_records": len(group_spacing_rows),
            "geometric_interval_order_proposals_by_axis": json_cell({item["axis_id"]: item["geometric_receiver_order_proposal"] for item in group_axis_records}),
            "nds_load_aligned_row_assessment": "not_assessed",
        }
        group_rows.append(group_row)

    retained_rows: list[dict[str, Any]] = []
    retained_json = []
    for axis in sorted(retained_axes, key=lambda item: item["axis_id"]):
        axis_unit = unit(axis["axis_global_xyz"])
        receiver_angles = {}
        members = sorted(axis["members_as_recorded"])
        if set(members) - grains.keys():
            raise AssertionError(f"Retained axis receiver lacks source grain mapping: {axis['axis_id']}")
        for member_id in members:
            angle = angle_to_grain_deg(axis_unit, grains[member_id]["grain_axis_global_xyz"])
            receiver_angles[member_id] = {
                "axis_to_grain_angle_deg_unsigned": angle,
                "parallel_to_grain_within_1deg_descriptive_flag": angle <= NEAR_PARALLEL_DEGREES,
                "source_proposed_grain_unit_global_xyz": grains[member_id]["grain_axis_global_xyz"],
            }
        record = {
            "axis_id": axis["axis_id"],
            "members_as_recorded": members,
            "geometric_member_pair_associations": axis["geometric_member_pair_associations"],
            "source_origin_global_xyz_mm": axis["origin_global_xyz_mm"],
            "source_occupied_diameter_mm": axis["source_occupied_diameter_mm"],
            "axis_unit_global_xyz": axis_unit,
            "receiver_axis_to_grain": receiver_angles,
            "candidate_grouping_included": False,
            "candidate_recheck_status": axis["candidate_recheck_status"],
        }
        retained_json.append(record)
        retained_rows.append({
            "axis_id": record["axis_id"],
            "members_as_recorded": json_cell(members),
            "geometric_member_pair_associations": json_cell(axis["geometric_member_pair_associations"]),
            "source_origin_global_xyz_mm": json_cell(axis["origin_global_xyz_mm"]),
            "source_occupied_diameter_mm": axis["source_occupied_diameter_mm"],
            "axis_unit_global_xyz": json_cell(axis_unit),
            "receiver_axis_to_grain": json_cell(receiver_angles),
            "candidate_grouping_included": False,
            "candidate_recheck_status": axis["candidate_recheck_status"],
        })

    source_by_id = {item["axis_id"]: item for item in candidate_axes}
    def independent_spacing_check(side: str) -> dict[str, Any]:
        axis_ids = [f"knee_outer_{side}_inner_header_1", f"knee_outer_{side}_inner_header_2"]
        example_group = next(group for group in json_groups if set(group["axis_ids"]) == set(axis_ids))
        example_a, example_b = [source_by_id[axis_id] for axis_id in axis_ids]
        ca = example_a["geometry"]["shaft_center_global_xyz_mm"]
        cb = example_b["geometry"]["shaft_center_global_xyz_mm"]
        raw_delta = [cb[index] - ca[index] for index in range(3)]
        direct_distance = math.sqrt(raw_delta[0] ** 2 + raw_delta[1] ** 2 + raw_delta[2] ** 2)
        raw_axis_a = example_a["geometry"]["axis_head_to_nut_global"]
        raw_axis_b = example_b["geometry"]["axis_head_to_nut_global"]
        axis_a = [value / math.sqrt(sum(component * component for component in raw_axis_a)) for value in raw_axis_a]
        axis_b = [value / math.sqrt(sum(component * component for component in raw_axis_b)) for value in raw_axis_b]
        axis_alignment_abs_dot = abs(sum(axis_a[index] * axis_b[index] for index in range(3)))
        direct_misalignment = math.degrees(math.acos(min(1.0, axis_alignment_abs_dot)))
        if direct_misalignment > PARALLEL_AXES_TOLERANCE_DEGREES:
            raise AssertionError(f"Independent example axes are not parallel: {axis_ids}")
        direct_axial_signed = sum(raw_delta[index] * axis_a[index] for index in range(3))
        perpendicular_delta = [raw_delta[index] - direct_axial_signed * axis_a[index] for index in range(3)]
        direct_pitch = math.sqrt(sum(value * value for value in perpendicular_delta))
        direct_projection_values = {}
        for member_id in example_group["receiver_member_ids"]:
            grain_vector = unit(grains[member_id]["grain_axis_global_xyz"])
            direct_projection_values[member_id] = sum(raw_delta[index] * grain_vector[index] for index in range(3))
        stored_example = next(row for row in spacing_rows if row["group_id"] == example_group["group_id"])
        stored_axis_components = stored_example["axis_normal_center_spacing_components"]
        comparisons = {
            "center_spacing_euclidean_mm": (direct_distance, stored_example["center_spacing_euclidean_mm"]),
            "axis_a_reference_signed_component_mm": (direct_axial_signed, stored_axis_components["axis_a_reference_signed_component_mm"]),
            "perpendicular_inter_axis_pitch_mm": (direct_pitch, stored_axis_components["perpendicular_inter_axis_pitch_mm"]),
        }
        for quantity, (direct, stored) in comparisons.items():
            if stored is None or abs(direct - stored) > 1e-10:
                raise AssertionError(f"Independent {quantity} recomputation failed for {side} knee header.")
        for member_id, direct_projection in direct_projection_values.items():
            stored_projection = stored_example["center_spacing_projected_by_source_proposed_grain"][member_id]["projection_signed_mm"]
            if abs(direct_projection - stored_projection) > 1e-10:
                raise AssertionError(f"Independent grain projection recomputation failed for {member_id}")
        if abs(abs(direct_axial_signed) - 22.098) > 1e-9 or abs(direct_pitch - 93.35) > 1e-9:
            raise AssertionError(f"Expected nonzero axial-offset control did not reproduce for {side} knee header.")
        return {
            "status": "passed",
            "example": f"knee_outer_{side}_inner_header",
            "group_id": example_group["group_id"],
            "axis_ids": axis_ids,
            "center_spacing_euclidean_direct_mm": direct_distance,
            "axis_a_reference_signed_component_direct_mm": direct_axial_signed,
            "perpendicular_inter_axis_pitch_direct_mm": direct_pitch,
            "axis_misalignment_direct_deg": direct_misalignment,
            "signed_grain_projections_direct_mm": direct_projection_values,
            "nonzero_axial_offset_control": True,
            "compared_to_emitted_spacing_row": True,
            "tolerance_mm": 1e-10,
        }

    left_recomputation = independent_spacing_check("left")
    right_recomputation = independent_spacing_check("right")
    recomputation = left_recomputation

    expected_axis_ids = [axis["axis_id"] for axis in candidate_axes]
    emitted_axis_ids = [axis["axis_id"] for axis in axis_records]
    if len(expected_axis_ids) != len(set(expected_axis_ids)):
        raise AssertionError("Candidate source axis IDs are not unique.")
    if sorted(expected_axis_ids) != sorted(emitted_axis_ids) or len(emitted_axis_ids) != 92:
        raise AssertionError("The group inventory does not conserve the 92 unique candidate axes.")
    if sum(len(group["axes"]) for group in json_groups if group["geometry_group_type"] == "three_member_stack_preserved") != 4:
        raise AssertionError("Three-member stack membership was not preserved.")
    if any(group["geometry_group_type"] != "three_member_stack_preserved" and len(group["receiver_member_ids"]) != 2 for group in json_groups):
        raise AssertionError("A non-pair group was misclassified.")
    if len(retained_json) != 12 or set(item["axis_id"] for item in retained_json) & set(emitted_axis_ids):
        raise AssertionError("Retained axes were merged into candidate grouping or count changed.")
    if not all(
        row["axis_normal_center_spacing_components"]["axes_parallel_for_normal_projection"]
        == (row["axis_normal_center_spacing_components"]["perpendicular_inter_axis_pitch_mm"] is not None)
        for row in spacing_rows
    ):
        raise AssertionError("Perpendicular inter-axis pitch must only be emitted for parallel axes.")

    angle_values = [row["axis_to_grain_angle_deg_unsigned"] for row in receiver_rows]
    parallel_rows = [row for row in receiver_rows if row["parallel_to_grain_within_1deg_descriptive_flag"]]
    axis_normal_rows = [row["axis_normal_center_spacing_components"] for row in spacing_rows if row["axis_normal_center_spacing_components"]["perpendicular_inter_axis_pitch_mm"] is not None]
    nonzero_axial_rows = [row for row in axis_normal_rows if row["axis_a_reference_component_exceeds_zero_tolerance_mm"]]
    group_counts = {
        "candidate_axes": len(candidate_axes),
        "candidate_axes_unique_and_accounted_once": len(emitted_axis_ids),
        "geometry_groups": len(json_groups),
        "two_member_receiver_pair_groups": sum(group["geometry_group_type"] == "two_member_receiver_pair" for group in json_groups),
        "three_member_stack_groups": sum(group["geometry_group_type"] == "three_member_stack_preserved" for group in json_groups),
        "axes_in_three_member_stacks": sum(len(group["axes"]) for group in json_groups if group["geometry_group_type"] == "three_member_stack_preserved"),
        "candidate_receiver_memberships": len(receiver_rows),
        "groups_missing_manifest_station_id": sum(not group["station_id_present_in_source"] for group in json_groups),
        "candidate_axes_missing_manifest_station_id": sum(axis.get("station_id") is None for axis in candidate_axes),
        "geometric_pair_association_rows": sum(len(axis["geometric_member_pair_associations"]) for axis in candidate_axes),
        "center_spacing_records": len(spacing_rows),
        "parallel_axes_tolerance_deg": PARALLEL_AXES_TOLERANCE_DEGREES,
        "axial_component_zero_tolerance_mm": AXIAL_ZERO_TOLERANCE_MM,
        "parallel_axis_pairs_with_perpendicular_spacing_reported": len(axis_normal_rows),
        "axis_pairs_with_axial_center_offset_over_1e-6_mm": len(nonzero_axial_rows),
        "maximum_absolute_axial_center_offset_mm": max(row["axis_a_reference_absolute_component_mm"] for row in axis_normal_rows),
        "perpendicular_inter_axis_pitch_min_mm": min(row["perpendicular_inter_axis_pitch_mm"] for row in axis_normal_rows),
        "perpendicular_inter_axis_pitch_max_mm": max(row["perpendicular_inter_axis_pitch_mm"] for row in axis_normal_rows),
        "retained_frame_axes_reported_separately": len(retained_json),
        "receiver_axes_parallel_to_proposed_grain_within_1deg_descriptive": len(parallel_rows),
        "receiver_axis_to_grain_angle_min_deg": min(angle_values),
        "receiver_axis_to_grain_angle_max_deg": max(angle_values),
    }
    payload = {
        "schema": "wood_joint_bolt_geometry_group_inventory/v1",
        "status": "geometry_inventory_only_not_design_or_acceptance",
        "candidate": manifest.get("candidate"),
        "geometry_revision_id": manifest.get("geometry_revision_id"),
        "source_pins": {path: {"sha256": digest} for path, digest in SOURCE_PINS.items()},
        "source_sha256_observed": {path: digest for path, digest in ((rel_manifest, manifest_sha), (rel_block, block_sha), (rel_frame, frame_sha))},
        "definitions": {
            "geometry_group": "Exact source station_id plus exact full receiver-member set. Two-member sets are receiver-pair groups; three-member sets remain single three-member stacks with their three pair associations listed separately.",
            "missing_station_id": "Where station_id is null in the source, rows are grouped by family, trial_id, and exact receiver-member set; this fallback does not recover a missing station identifier.",
            "center_spacing_and_pitch": "Euclidean distance between modeled shaft center points is center_spacing_euclidean_mm. The center delta is decomposed into a signed component along axis A and perpendicular_inter_axis_pitch_mm only if the two modeled bolt axes are parallel or antiparallel within the stated angular tolerance. This perpendicular inter-axis center spacing is not a verified per-receiver hole-station spacing. Projections along proposed grain directions are separate center-delta components.",
            "angle": "Unsigned acute angle between the unit bolt axis and each receiver's source-proposed longitudinal grain direction. The within-1-degree flag is descriptive only.",
            "interval_order": "For two-member axes only, a nonoverlapping underhead receiver interval ordering is an axis-direction geometric proposal. It does not establish a delivered head-to-nut hardware stack.",
            "nds_rows": "No NDS load-aligned bolt rows, group factor Cg, force, capacity, or pass/fail result is derived from these geometry groups.",
        },
        "conservation_checks": {
            "all_92_candidate_axis_ids_unique_and_accounted_once": True,
            "all_candidate_receiver_member_ids_found_in_pinned_block_or_frame_grain_maps": True,
            "geometric_pair_associations_reconciled_to_full_receiver_membership": True,
            "four_axes_in_two_three_member_stacks_preserved_without_pair_expansion": True,
            "retained_12_excluded_from_candidate_groups_and_reported_separately": True,
            "perpendicular_inter_axis_pitch_only_reported_when_axis_pair_is_parallel_within_tolerance": True,
            "independent_geometry_recomputation": recomputation,
            "independent_mirrored_nonzero_axial_geometry_recomputation": right_recomputation,
        },
        "counts_and_angle_summary": group_counts,
        "candidate_groups": json_groups,
        "candidate_axes": axis_records,
        "candidate_axis_receiver_grain_angles": receiver_rows,
        "candidate_group_center_spacing": spacing_rows,
        "retained_frame_axes_separate": retained_json,
        "limits": [
            "The two material-frame maps provide conditional source-proposed grain directions, not observed delivered stock or ring orientation.",
            "Geometry group membership is not an NDS load-aligned bolt row, and no arbitrary spacing scalar is an NDS pass.",
            "No NDS group factor Cg, force, load share, connection capacity, or acceptance is calculated.",
            "Perpendicular inter-axis pitch is a centerline decomposition only; the inventory does not establish the actual hole station on each receiver or NDS spacing compliance.",
            "Underhead receiver intervals do not verify physical head-to-nut order, delivered hardware, fit, washers, nuts, thread engagement, or installation.",
            "Candidate groups with a null source station_id retain that null and expose the family/trial grouping fallback.",
        ],
    }

    group_fields = list(group_rows[0])
    receiver_fields = list(receiver_rows[0])
    spacing_csv_rows = []
    for row in spacing_rows:
        flattened = dict(row)
        flattened["receiver_member_ids"] = json_cell(row["receiver_member_ids"])
        flattened["center_a_global_xyz_mm"] = json_cell(row["center_a_global_xyz_mm"])
        flattened["center_b_global_xyz_mm"] = json_cell(row["center_b_global_xyz_mm"])
        flattened["center_delta_b_minus_a_global_xyz_mm"] = json_cell(row["center_delta_b_minus_a_global_xyz_mm"])
        flattened["axis_normal_center_spacing_components"] = json_cell(row["axis_normal_center_spacing_components"])
        flattened["center_spacing_projected_by_source_proposed_grain"] = json_cell(row["center_spacing_projected_by_source_proposed_grain"])
        spacing_csv_rows.append(flattened)
    spacing_fields = list(spacing_csv_rows[0])
    retained_fields = list(retained_rows[0])
    outputs = {
        "bolt-groups.json": (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
        "bolt-groups.csv": csv_bytes(group_rows, group_fields),
        "bolt-group-axis-receivers.csv": csv_bytes(receiver_rows, receiver_fields),
        "bolt-group-axis-spacings.csv": csv_bytes(spacing_csv_rows, spacing_fields),
        "retained-frame-bolt-axes.csv": csv_bytes(retained_rows, retained_fields),
    }
    return payload, outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="Write deterministic JSON and CSV outputs beside this script.")
    action.add_argument("--verify", action="store_true", help="Rebuild in memory and compare all outputs byte-for-byte.")
    args = parser.parse_args()
    output_dir = Path(__file__).resolve().parent
    _, outputs = build(repo_root())
    if args.write:
        for name, content in outputs.items():
            (output_dir / name).write_bytes(content)
        print(f"wrote {len(outputs)} outputs to {output_dir}")
        return 0
    mismatches = []
    for name, expected in outputs.items():
        path = output_dir / name
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(name)
    if mismatches:
        print("verification mismatch: " + ", ".join(mismatches), file=sys.stderr)
        return 1
    print(f"verified {len(outputs)} outputs; conservation and independent geometry checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
