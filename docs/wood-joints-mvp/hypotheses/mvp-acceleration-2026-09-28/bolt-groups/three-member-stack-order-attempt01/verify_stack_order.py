#!/usr/bin/env python3
"""Reconstruct and verify modeled receiver ordering for the four triad axes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
HERE = Path(__file__).resolve().parent
MANIFEST_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
GROUPS_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "bolt-groups/bolt-groups.json"
)
EXPECTED_PINS = {
    str(MANIFEST_REL): "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    str(GROUPS_REL): "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
}
EXPECTED_STACKS = {
    "BG003": [
        "knee_outer_left_side_1",
        "knee_outer_left_side_2",
    ],
    "BG004": [
        "knee_outer_right_side_1",
        "knee_outer_right_side_2",
    ],
}
EXPECTED_ORDER = {
    "BG003": [
        "knee_outer_left_spine",
        "base_side_left",
        "knee_outer_left_inner_frame_block",
    ],
    "BG004": [
        "knee_outer_right_spine",
        "base_side_right",
        "knee_outer_right_inner_frame_block",
    ],
}
GAP_TOLERANCE_MM = 1e-6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, tolerance: float = GAP_TOLERANCE_MM) -> bool:
    return abs(a - b) <= tolerance


def verify_source_pins() -> dict[str, str]:
    observed = {}
    for rel, expected in EXPECTED_PINS.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            raise ValueError(f"source hash changed for {rel}: {actual} != {expected}")
        observed[rel] = actual
    return observed


def receiver_intervals(axis: dict[str, Any]) -> list[dict[str, Any]]:
    geometry = axis["geometry"]
    entries = geometry["wood_receiver_intervals"]
    result = []
    for entry in entries:
        intervals = entry.get("current_shaft_intersection_solid_intervals_from_underhead_mm")
        if intervals is None:
            intervals = entry.get("intersection_solid_intervals_from_underhead_mm")
        if not intervals or len(intervals) != 1:
            raise ValueError(
                f"{axis['axis_id']} / {entry['receiver_id']}: expected one solid interval, found {intervals}"
            )
        start, end = map(float, intervals[0])
        if not (math.isfinite(start) and math.isfinite(end) and end > start):
            raise ValueError(f"invalid receiver interval {axis['axis_id']} / {entry['receiver_id']}")
        if not entry.get("current_shaft_covers_long_axis_raw_receiver_projection", False):
            raise ValueError(f"modeled shaft does not cover receiver interval: {axis['axis_id']}")
        if not entry.get("current_shaft_volume_covers_long_probe_intersection", False):
            raise ValueError(f"modeled shaft does not cover probe intersection: {axis['axis_id']}")
        result.append({"receiver_id": entry["receiver_id"], "start_mm": start, "end_mm": end})
    return sorted(result, key=lambda item: (item["start_mm"], item["end_mm"], item["receiver_id"]))


def build_record(manifest: dict[str, Any], groups: dict[str, Any], pins: dict[str, str]) -> dict[str, Any]:
    axis_rows = {row["axis_id"]: row for row in manifest["candidate_bolt_axes"]}
    manifest_triads = {
        axis_id: row
        for axis_id, row in axis_rows.items()
        if len(row.get("geometry", {}).get("wood_receiver_intervals", [])) == 3
    }
    expected_axis_ids = {axis_id for values in EXPECTED_STACKS.values() for axis_id in values}
    if set(manifest_triads) != expected_axis_ids:
        raise ValueError(f"unexpected three-receiver axes: {sorted(manifest_triads)}")

    group_rows = {
        group["group_id"]: group
        for group in groups["candidate_groups"]
        if group["geometry_group_type"] == "three_member_stack_preserved"
    }
    if set(group_rows) != set(EXPECTED_STACKS):
        raise ValueError(f"unexpected triad group IDs: {sorted(group_rows)}")

    stacks = []
    for group_id in sorted(EXPECTED_STACKS):
        group = group_rows[group_id]
        expected_ids = EXPECTED_STACKS[group_id]
        if group["axis_ids"] != expected_ids:
            raise ValueError(f"{group_id}: axis IDs differ from frozen expected grouping")
        expected_members = EXPECTED_ORDER[group_id]
        if sorted(group["receiver_member_ids"]) != sorted(expected_members):
            raise ValueError(f"{group_id}: receiver membership differs from expected source group")
        axis_results = []
        axis_vectors = []
        for axis_id in expected_ids:
            axis = manifest_triads[axis_id]
            manifest_members = sorted(
                interval["receiver_id"]
                for interval in axis["geometry"]["wood_receiver_intervals"]
            )
            group_axis = next(row for row in group["axes"] if row["axis_id"] == axis_id)
            if manifest_members != sorted(expected_members):
                raise ValueError(f"{axis_id}: manifest receiver membership differs from expected group")
            if sorted(group_axis["receiver_member_ids"]) != sorted(expected_members):
                raise ValueError(f"{axis_id}: bolt-group receiver membership differs from expected group")
            intervals = receiver_intervals(axis)
            order = [row["receiver_id"] for row in intervals]
            if order != expected_members:
                raise ValueError(f"{axis_id}: derived order {order} != expected {expected_members}")
            axial_gaps = []
            for previous, current in zip(intervals, intervals[1:]):
                gap = current["start_mm"] - previous["end_mm"]
                if gap < -GAP_TOLERANCE_MM or gap > GAP_TOLERANCE_MM:
                    raise ValueError(
                        f"{axis_id}: receiver intervals overlap or separate by {gap} mm"
                    )
                axial_gaps.append(gap)
            vector = axis["geometry"]["axis_head_to_nut_global"]
            norm = math.sqrt(sum(float(value) ** 2 for value in vector))
            if abs(norm - 1.0) > 1e-8:
                raise ValueError(f"{axis_id}: head-to-nut direction is not unit length")
            for a, b in zip(vector, group_axis["axis_head_to_nut_unit_global_xyz"], strict=True):
                if abs(float(a) - float(b)) > 1e-8:
                    raise ValueError(f"{axis_id}: direction differs between pinned sources")
            axis_vectors.append([float(value) for value in vector])
            axis_results.append({
                "axis_id": axis_id,
                "head_to_nut_unit_global_xyz": [float(value) for value in vector],
                "head_to_nut_geometric_receiver_order": intervals,
                "receiver_boundary_gaps_mm": axial_gaps,
                "underhead_to_first_receiver_start_mm": intervals[0]["start_mm"],
                "last_receiver_end_from_underhead_mm": intervals[-1]["end_mm"],
                "modeled_shaft_length_mm": axis["geometry"]["modeled_underhead_to_tip_mm"],
                "modeled_wood_grip_length_mm": axis["geometry"]["wood_grip_material_length_mm"],
            })
        first_intervals = axis_results[0]["head_to_nut_geometric_receiver_order"]
        second_intervals = axis_results[1]["head_to_nut_geometric_receiver_order"]
        if [row["receiver_id"] for row in first_intervals] != [row["receiver_id"] for row in second_intervals]:
            raise ValueError(f"{group_id}: two axes do not agree on receiver order")
        for first, second in zip(first_intervals, second_intervals, strict=True):
            if not close(first["start_mm"], second["start_mm"]) or not close(first["end_mm"], second["end_mm"]):
                raise ValueError(f"{group_id}: two axes do not agree on receiver interval geometry")
        if any(abs(a - b) > 1e-8 for a, b in zip(axis_vectors[0], axis_vectors[1], strict=True)):
            raise ValueError(f"{group_id}: two axes do not share the same oriented head-to-nut direction")
        stacks.append({
            "group_id": group_id,
            "station_id": group["station_id"],
            "station_id_present_in_source": group["station_id_present_in_source"],
            "grouping_basis": group["grouping_basis"],
            "axis_ids": expected_ids,
            "axes_agree_on_geometric_receiver_order": True,
            "head_to_nut_geometric_receiver_order": expected_members,
            "axes": axis_results,
        })

    return {
        "schema": "wood_joint_three_member_receiver_order/v1",
        "candidate": manifest["candidate"],
        "geometry_revision_id": manifest["geometry_revision_id"],
        "status": "PASS_MODELED_RECEIVER_INTERVAL_ORDER_ONLY",
        "source_sha256": pins,
        "tolerance_mm": GAP_TOLERANCE_MM,
        "counts": {
            "three_member_stacks": len(stacks),
            "axes": sum(len(stack["axes"]) for stack in stacks),
            "receivers_per_axis": 3,
            "axes_with_unique_order": sum(
                len(stack["head_to_nut_geometric_receiver_order"]) == 3 for stack in stacks for _ in stack["axes"]
            ),
        },
        "stacks": stacks,
        "limits": [
            "This is an ordering of modeled STEP receiver intervals from the modeled underhead datum, not a delivered hardware installation check.",
            "The 1.651 mm modeled underhead-to-first-receiver offset is reported but is not interpreted as washer seating, clearance, bearing, or allowance.",
            "No installed clamping, force transfer, load sharing, NDS row, group factor, resistance, or design acceptance is established.",
            "The omitted source station IDs remain null; the existing family/trial/full-receiver grouping fallback is preserved.",
            "No geometry, CAD, mesh, native solver input, or physical build instruction is changed."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="reconstruct and compare without writing")
    mode.add_argument("--write", action="store_true", help="write the reconstructed record after source-pin checks")
    args = parser.parse_args()

    pins = verify_source_pins()
    manifest = json.loads((ROOT / MANIFEST_REL).read_text())
    groups = json.loads((ROOT / GROUPS_REL).read_text())
    record = build_record(manifest, groups, pins)
    path = HERE / "receiver-stack-order.json"
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.write:
        path.write_text(rendered)
        print(f"wrote {path.relative_to(ROOT)}")
        return
    if not path.exists():
        raise SystemExit(f"missing {path}; rerun with --write after inspecting source pins")
    if path.read_text() != rendered:
        raise SystemExit("verification failed: reconstructed record differs from saved output")
    print("PASS: four axes in two three-member stacks have unique modeled interval order")


if __name__ == "__main__":
    main()
