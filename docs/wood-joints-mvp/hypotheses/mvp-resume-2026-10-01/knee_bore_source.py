"""Load frozen knee receiver intervals and finished-bore clearances."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCREEN_PATH = HERE / "three-member-screen-attempt01/all-two-receiver/screen.json"
MODEL_PATH = (
    HERE.parent
    / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
)
SCREEN_SHA256 = "306aa4a8e4c6113d4a0258d09564292d07095131ef2b4621370d7284e75e0377"
MODEL_SHA256 = "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9"
AXIS_IDS = (
    "knee_outer_left_side_1",
    "knee_outer_left_side_2",
    "knee_outer_right_side_1",
    "knee_outer_right_side_2",
)
SHAFT_DIAMETER_MM = 6.35
TOLERANCE_MM = 1e-6


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _point_at(start, distance, axis):
    return [start[i] + distance * axis[i] for i in range(3)]


def _assert_point_close(actual, expected, label):
    assert math.dist(actual, expected) <= TOLERANCE_MM, label


def load_bores() -> tuple[dict[str, Any], dict[Path, str]]:
    """Return axis records and SHA pins for the two frozen source files."""
    assert _sha256(SCREEN_PATH) == SCREEN_SHA256, "changed frozen knee screen"
    assert _sha256(MODEL_PATH) == MODEL_SHA256, "changed frozen model inputs"
    screen = json.loads(SCREEN_PATH.read_text())
    model = json.loads(MODEL_PATH.read_text())
    assert set(screen["geometry"]) == set(AXIS_IDS), "knee axis inventory changed"
    connections = {
        row["axis_id"]: row
        for row in model["connections"]
        if row.get("kind") == "candidate_bolt" and row.get("axis_id") in AXIS_IDS
    }
    assert set(connections) == set(AXIS_IDS), "knee bore axis inventory changed"

    records: dict[str, Any] = {}
    for axis_id in AXIS_IDS:
        geometry = screen["geometry"][axis_id]
        member_ids = geometry["receiver_order"]
        lengths = [float(value) for value in geometry["bearing_lengths_mm"]]
        assert len(member_ids) == len(lengths) == 3, "expected three knee receivers"
        assert len(set(member_ids)) == 3, "duplicate knee receiver"
        assert all(math.isfinite(length) and length > 0 for length in lengths)

        intervals = geometry["receiver_intervals_from_underhead_mm"]
        assert set(intervals) == set(member_ids), "receiver interval order changed"
        interval_origin = float(intervals[member_ids[0]][0])
        cumulative = 0.0
        for member_id, length in zip(member_ids, lengths, strict=True):
            start, end = map(float, intervals[member_id])
            assert math.isclose(
                start, interval_origin + cumulative, rel_tol=0, abs_tol=TOLERANCE_MM
            ), f"noncontiguous receiver interval: {axis_id}/{member_id}"
            assert math.isclose(end - start, length, rel_tol=0, abs_tol=TOLERANCE_MM), (
                f"receiver length mismatch: {axis_id}/{member_id}"
            )
            cumulative += length

        axis = [float(value) for value in geometry["bolt_axis_xyz"]]
        assert len(axis) == 3 and math.isclose(
            math.sqrt(sum(value * value for value in axis)),
            1.0,
            rel_tol=0,
            abs_tol=1e-8,
        ), f"invalid knee axis: {axis_id}"
        headseat = [float(value) for value in geometry["head_seat_point_mm"]]
        interfaces = geometry["interface_points_mm"]
        nutseat = geometry["nut_seat_point_mm"]
        assert len(interfaces) == 2, "expected two knee interfaces"

        boundaries = [headseat]
        cumulative = 0.0
        for length in lengths:
            cumulative += length
            boundaries.append(_point_at(headseat, cumulative, axis))
        for actual, expected, label in zip(
            [*interfaces, nutseat],
            boundaries[1:],
            ("interface 1", "interface 2", "nutseat"),
            strict=True,
        ):
            _assert_point_close(actual, expected, f"{axis_id} {label} differs")

        clearance_rows = connections[axis_id]["receiver_clearance_geometry"]
        clearances = {row["receiver_id"]: row for row in clearance_rows}
        assert len(clearance_rows) == len(clearances) == 3, (
            "expected three bore records"
        )
        assert set(clearances) == set(member_ids), "bore receiver order/source mismatch"

        receivers = []
        cumulative = 0.0
        for member_id, length in zip(member_ids, lengths, strict=True):
            clearance = clearances[member_id]
            assert clearance["axis_id"] == axis_id
            span_records = clearance["manifest_receiver_interval"][
                "source_intersection_solid_intervals_from_underhead_mm"
            ]
            assert len(span_records) == 1, (
                f"disconnected receiver source: {axis_id}/{member_id}"
            )
            source_start, source_end = map(float, span_records[0])
            interval_start, interval_end = map(float, intervals[member_id])
            assert math.isclose(
                source_start, interval_start, rel_tol=0, abs_tol=TOLERANCE_MM
            ) and math.isclose(
                source_end, interval_end, rel_tol=0, abs_tol=TOLERANCE_MM
            ), f"clearance interval mismatch: {axis_id}/{member_id}"
            assert clearance["result_status"] == "unique_coaxial_bore_radius"
            assert math.isclose(
                float(clearance["modeled_shaft_diameter_mm"]),
                SHAFT_DIAMETER_MM,
                rel_tol=0,
                abs_tol=1e-8,
            ), f"modeled shaft changed: {axis_id}/{member_id}"

            bore_radius = float(clearance["unique_bore_radius_mm"])
            radial_clearance = bore_radius - SHAFT_DIAMETER_MM / 2
            assert radial_clearance > 0, (
                f"nonpositive bore clearance: {axis_id}/{member_id}"
            )
            endpoints = [
                _point_at(headseat, cumulative, axis),
                _point_at(headseat, cumulative + length, axis),
            ]
            receivers.append(
                {
                    "member": member_id,
                    "start_point_mm": endpoints[0],
                    "end_point_mm": endpoints[1],
                    "bore_diameter_mm": 2 * bore_radius,
                    "radial_clearance_mm": radial_clearance,
                    "geometry_source_id": {
                        "step_path": clearance["receiver_step_path"],
                        "step_sha256": clearance["receiver_step_sha256"],
                    },
                }
            )
            cumulative += length

        records[axis_id] = {
            "axis_xyz": axis,
            "head_seat_point_mm": headseat,
            "shaft_diameter_mm": SHAFT_DIAMETER_MM,
            "receivers": receivers,
        }

    assert (
        len(records) == 4
        and sum(len(row["receivers"]) for row in records.values()) == 12
    )
    return records, {SCREEN_PATH: SCREEN_SHA256, MODEL_PATH: MODEL_SHA256}
