"""Conditional 1/4-20 bolt-length screen for WJ24's sixteen center axes.

This consumes the frozen WJ24 hardware inventory. It proposes nominal length
classes from explicit stack and ASME dimensional inputs; it does not select a
SKU, infer delivered shank, assign capacity, or release physical work.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj24-hardware-inventory/inventory.json"
)

SCHEMA = "wood_joint_wj24_bolt_length_screen/v1"
TARGET_FAMILY = "wj05_center_x190"

MM_PER_IN = 25.4
WASHER_NOMINAL_MM = 1.651
WASHER_MIN_MM = 1.2954
WASHER_MAX_MM = 2.032
WASHERS_PER_AXIS = 2
NUT_MAX_MM = 5.7404
THREAD_PROJECTION_MM = 3.175
WOOD_MEMBER_ALLOWANCE_MM = 0.5
MAX_THREAD_BEARING_FRACTION = 0.25

# WJ05 center-node modeled receivers, in head-to-nut order. The inventory
# retains these receiver identities and nominal wood-grip spans.
HEADER_THICKNESS_MM = 38.1
POST_CLEAT_THICKNESS_MM = 128.9
FULL_SECTION_CLEAT_THICKNESS_MM = 88.9

# Candidate nominal lengths use the 1/4-in length increments in the B18.2.1
# screw dimension tables. They are dimensional candidates only; no supplier
# availability or product identity is implied.
CANDIDATE_LENGTHS_IN = tuple(
    round(4.5 + 0.25 * index, 2) for index in range(15)
)  # 4-1/2 through 8 in.


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _close(a: float, b: float, *, tolerance: float = 1e-6) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance)


def _nominal_length_mm(length_in: float) -> float:
    return length_in * MM_PER_IN


def _length_tolerance_mm(length_in: float) -> float:
    """ASME B18.2.1 Table 13 lower tolerance for 1/4-in screws.

    The relevant size column is 1/4 through 3/8 in: −0.10 in for nominal
    lengths over 4 through 6 in, and −0.18 in for lengths over 6 in. These are
    standard bounds used for screening, not measurements of a delivered lot.
    """
    if length_in <= 4.0:
        raise ValueError("this screen only supports nominal lengths over 4 in")
    return (0.10 if length_in <= 6.0 else 0.18) * MM_PER_IN


def _thread_dimensions_mm(length_in: float) -> tuple[float, float]:
    """Return ASME B18.2.1 Table 12 Lg,max and Lb,min for 1/4-in HCS.

    For 1/4-in hex cap screws, the reference thread length is 0.75 in through
    6 in nominal length and 1.00 in above 6 in. The transition allowance Y is
    0.25 in. B18.2.1 defines Lg,max = L - LT and Lb,min = Lg,max - Y.
    Values remain gaging/body envelopes, not measured thread-start locations.
    """
    nominal_mm = _nominal_length_mm(length_in)
    reference_thread_length_mm = (0.75 if length_in <= 6.0 else 1.0) * MM_PER_IN
    transition_allowance_mm = 0.25 * MM_PER_IN
    grip_gage_max_mm = nominal_mm - reference_thread_length_mm
    body_min_mm = grip_gage_max_mm - transition_allowance_mm
    return grip_gage_max_mm, body_min_mm


def _member_split(axis: dict[str, Any]) -> tuple[str, float, str, float]:
    """Return ordered receiver IDs and their modeled thicknesses.

    Thicknesses are read from the WJ05 center-node probe's dimensions and
    the inventory's ordered actual receiver pair, not inferred by proximity.
    """
    axis_id = axis["axis_id"]
    receiver_ids = axis["ordered_receiver_ids_from_candidate_bore"]
    grip = float(axis["stack_class"]["nominal_wood_grip_mm"])
    if axis_id.startswith("center_principal_header_"):
        near_member, far_member = receiver_ids
        if near_member != "base_header" or not far_member.startswith(
            "center_principal_cleat_"
        ):
            raise ValueError(f"unexpected ordered receivers for {axis_id}")
        near_thickness = HEADER_THICKNESS_MM
        far_thickness = grip - near_thickness
    elif axis_id.startswith("center_post_header_"):
        near_member, far_member = receiver_ids
        if not near_member.startswith("center_post_cleat_") or far_member != "base_header":
            raise ValueError(f"unexpected ordered receivers for {axis_id}")
        near_thickness = POST_CLEAT_THICKNESS_MM
        far_thickness = HEADER_THICKNESS_MM
    elif axis_id.startswith("center_post_"):
        near_member, far_member = receiver_ids
        if not near_member.startswith("base_post_center_") or not far_member.startswith(
            "center_post_cleat_"
        ):
            raise ValueError(f"unexpected ordered receivers for {axis_id}")
        near_thickness = HEADER_THICKNESS_MM
        far_thickness = FULL_SECTION_CLEAT_THICKNESS_MM
    elif axis_id.startswith("center_principal_"):
        near_member, far_member = receiver_ids
        if not near_member.startswith("base_principal_center_") or not far_member.startswith(
            "center_principal_cleat_"
        ):
            raise ValueError(f"unexpected ordered receivers for {axis_id}")
        near_thickness = HEADER_THICKNESS_MM
        far_thickness = FULL_SECTION_CLEAT_THICKNESS_MM
    else:
        raise ValueError(f"axis is outside the WJ05 center-node groups: {axis_id}")

    if near_thickness <= 0 or far_thickness <= 0 or not _close(
        near_thickness + far_thickness, grip
    ):
        raise ValueError(f"receiver thicknesses do not reconcile to grip for {axis_id}")
    return near_member, near_thickness, far_member, far_thickness


def _evaluate_candidate(
    *,
    length_in: float,
    grip_mm: float,
    near_thickness_mm: float,
    far_thickness_mm: float,
) -> dict[str, Any]:
    nominal_length_mm = _nominal_length_mm(length_in)
    delivered_length_min_mm = nominal_length_mm - _length_tolerance_mm(length_in)
    grip_max_mm = grip_mm + 2.0 * WOOD_MEMBER_ALLOWANCE_MM
    grip_min_mm = grip_mm - 2.0 * WOOD_MEMBER_ALLOWANCE_MM
    near_max_mm = near_thickness_mm + WOOD_MEMBER_ALLOWANCE_MM
    far_max_mm = far_thickness_mm + WOOD_MEMBER_ALLOWANCE_MM

    grip_gage_max_mm, body_min_mm = _thread_dimensions_mm(length_in)
    # Conditional member-specific threaded-bearing bound: if a subsequent
    # lateral method uses nominal D, no more than one quarter of the nut-side
    # wood member may carry thread. This is a geometry condition, not capacity.
    body_end_for_thread_bearing_mm = (
        WASHER_MAX_MM
        + near_max_mm
        + (1.0 - MAX_THREAD_BEARING_FRACTION) * far_max_mm
    )
    receiving_body_end_min_mm = max(
        body_min_mm, body_end_for_thread_bearing_mm
    )

    # A full-height nut requires the first full-form thread no later than the
    # earliest possible near face of the nut (after the nut-side washer).
    earliest_nut_bearing_face_mm = (
        WASHER_MIN_MM + grip_min_mm + WASHER_MIN_MM
    )
    receiving_full_thread_start_max_mm = min(
        grip_gage_max_mm, earliest_nut_bearing_face_mm
    )
    transition_window_mm = (
        receiving_full_thread_start_max_mm - receiving_body_end_min_mm
    )

    far_nut_face_max_mm = (
        WASHER_MAX_MM + grip_max_mm + WASHER_MAX_MM + NUT_MAX_MM
    )
    receiving_full_thread_end_min_mm = (
        far_nut_face_max_mm + THREAD_PROJECTION_MM
    )
    minimum_tip_past_nut_mm = delivered_length_min_mm - far_nut_face_max_mm
    length_margin_after_projection_mm = (
        delivered_length_min_mm - receiving_full_thread_end_min_mm
    )

    nominal_stack_underhead_requirement_mm = (
        grip_mm
        + WASHERS_PER_AXIS * WASHER_NOMINAL_MM
        + NUT_MAX_MM
        + THREAD_PROJECTION_MM
    )
    passes_length_screen = length_margin_after_projection_mm >= 0.0
    has_feasible_receiving_transition = transition_window_mm > 0.0

    return {
        "nominal_length_in": length_in,
        "nominal_length_mm": round(nominal_length_mm, 6),
        "length_tolerance_minus_mm": round(
            nominal_length_mm - delivered_length_min_mm, 6
        ),
        "minimum_delivered_underhead_length_mm": round(
            delivered_length_min_mm, 6
        ),
        "b18_2_1_Lg_max_mm": round(grip_gage_max_mm, 6),
        "b18_2_1_Lb_min_mm": round(body_min_mm, 6),
        "nominal_modeled_stack_requirement_mm": round(
            nominal_stack_underhead_requirement_mm, 6
        ),
        "wood_grip_screen_mm": [round(grip_min_mm, 6), round(grip_max_mm, 6)],
        "earliest_nut_bearing_face_mm_from_underhead": round(
            earliest_nut_bearing_face_mm, 6
        ),
        "maximum_far_nut_face_mm_from_underhead": round(
            far_nut_face_max_mm, 6
        ),
        "minimum_tip_past_far_nut_face_mm": round(minimum_tip_past_nut_mm, 6),
        "required_full_thread_end_min_mm_from_underhead": round(
            receiving_full_thread_end_min_mm, 6
        ),
        "length_margin_after_required_thread_projection_mm": round(
            length_margin_after_projection_mm, 6
        ),
        "receiving_body_end_min_mm_from_underhead": round(
            receiving_body_end_min_mm, 6
        ),
        "receiving_full_thread_start_max_mm_from_underhead": round(
            receiving_full_thread_start_max_mm, 6
        ),
        "measured_transition_window_mm": round(transition_window_mm, 6),
        "passes_total_length_screen": passes_length_screen,
        "has_feasible_measured_transition_window": has_feasible_receiving_transition,
        "dimension_screen_pass": (
            passes_length_screen and has_feasible_receiving_transition
        ),
    }


def _candidate_length_screen(
    *,
    grip_mm: float,
    near_thickness_mm: float,
    far_thickness_mm: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evaluated = [
        _evaluate_candidate(
            length_in=length_in,
            grip_mm=grip_mm,
            near_thickness_mm=near_thickness_mm,
            far_thickness_mm=far_thickness_mm,
        )
        for length_in in CANDIDATE_LENGTHS_IN
    ]
    passing = [candidate for candidate in evaluated if candidate["dimension_screen_pass"]]
    if not passing:
        raise ValueError(f"no dimensional candidate passed for {grip_mm} mm grip")
    selected = passing[0]
    previous = [candidate for candidate in evaluated if candidate["nominal_length_in"] < selected[
        "nominal_length_in"
    ]]
    shorter = previous[-1] if previous else None
    return selected | {"shorter_nominal_candidate": shorter}, evaluated


def build_screen(inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the source-bound conditional screen for the 16 WJ24 center axes."""
    if inventory is None:
        inventory_bytes = INVENTORY_PATH.read_bytes()
        inventory = json.loads(inventory_bytes)
    else:
        inventory_bytes = json.dumps(
            inventory, sort_keys=True, separators=(",", ":")
        ).encode()

    source_rows = [
        row
        for row in inventory["candidate_hardware_axis_schedule"]
        if row.get("family") == TARGET_FAMILY
    ]
    if len(source_rows) != 16:
        raise ValueError(f"expected 16 WJ05 center axes; found {len(source_rows)}")
    source_rows.sort(key=lambda row: row["axis_id"])

    required_roles = {"shaft", "head", "head_washer", "nut_washer", "nut"}
    axes: list[dict[str, Any]] = []
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        if row["stack_class"]["modeled_nominal_length_mm"] is not None:
            raise ValueError(f"source inventory already assigns a length to {row['axis_id']}")
        if row["physical_bolt_count_screen"] != 1 or row["physical_nut_count_screen"] != 1:
            raise ValueError(f"unexpected bolt/nut count for {row['axis_id']}")
        if row["physical_washer_count_screen"] != WASHERS_PER_AXIS:
            raise ValueError(f"unexpected washer count for {row['axis_id']}")
        if set(row["installed_cad_role_ids"]) != required_roles:
            raise ValueError(f"unexpected installed CAD roles for {row['axis_id']}")

        grip_mm = float(row["stack_class"]["nominal_wood_grip_mm"])
        near_member, near_t, far_member, far_t = _member_split(row)
        historical_required = float(
            row["stack_class"]["historical_required_underhead_length_screen_mm"]
        )
        expected_historical = (
            grip_mm
            + WASHERS_PER_AXIS * WASHER_NOMINAL_MM
            + NUT_MAX_MM
            + THREAD_PROJECTION_MM
        )
        if not _close(historical_required, expected_historical):
            raise ValueError(f"historical WJ05 stack value changed for {row['axis_id']}")

        axis = {
            "axis_id": row["axis_id"],
            "family_trial_id": row["family_trial_id"],
            "station_id": row["station_id"],
            "wood_grip_mm": round(grip_mm, 6),
            "ordered_receiver_ids": row["ordered_receiver_ids_from_candidate_bore"],
            "head_side_member_id": near_member,
            "head_side_member_thickness_mm": round(near_t, 6),
            "nut_side_member_id": far_member,
            "nut_side_member_thickness_mm": round(far_t, 6),
            "historical_WJ05_nominal_stack_underhead_screen_mm": round(
                historical_required, 6
            ),
        }
        grouped[grip_mm].append(axis)
        axes.append(axis)

    expected_count_by_grip = {100.915644: 4, 127.0: 8, 167.0: 4}
    observed_count_by_grip = {grip: len(rows) for grip, rows in grouped.items()}
    if observed_count_by_grip != expected_count_by_grip:
        raise ValueError(f"unexpected center grip groups: {observed_count_by_grip}")

    groups: list[dict[str, Any]] = []
    for grip_mm in sorted(grouped):
        group_axes = grouped[grip_mm]
        first_axis = group_axes[0]
        selected, evaluated = _candidate_length_screen(
            grip_mm=grip_mm,
            near_thickness_mm=first_axis["head_side_member_thickness_mm"],
            far_thickness_mm=first_axis["nut_side_member_thickness_mm"],
        )
        if any(
            not _close(axis["head_side_member_thickness_mm"], first_axis["head_side_member_thickness_mm"])
            or not _close(axis["nut_side_member_thickness_mm"], first_axis["nut_side_member_thickness_mm"])
            for axis in group_axes
        ):
            raise ValueError(f"member split differs within grip group {grip_mm}")
        assignments = {axis["axis_id"]: selected["nominal_length_in"] for axis in group_axes}
        groups.append(
            {
                "axis_count": len(group_axes),
                "axis_ids": [axis["axis_id"] for axis in group_axes],
                "wood_grip_mm": grip_mm,
                "head_side_member_id": first_axis["head_side_member_id"],
                "head_side_member_thickness_mm": first_axis[
                    "head_side_member_thickness_mm"
                ],
                "nut_side_member_id": first_axis["nut_side_member_id"],
                "nut_side_member_thickness_mm": first_axis[
                    "nut_side_member_thickness_mm"
                ],
                "screened_nominal_length_in": selected["nominal_length_in"],
                "axis_nominal_length_assignments_in": assignments,
                "selected_length_candidate": selected,
                "shorter_length_candidate": selected["shorter_nominal_candidate"],
                "eight_in_candidate": next(
                    candidate
                    for candidate in evaluated
                    if candidate["nominal_length_in"] == 8.0
                ),
            }
        )

    identity = [axis["axis_id"] for axis in axes]
    return {
        "schema": SCHEMA,
        "status": "conditional_nominal_length_screen_only",
        "candidate": inventory.get("layout_id"),
        "trial_id": inventory.get("trial_id"),
        "source_inventory_path": str(INVENTORY_PATH.relative_to(ROOT)),
        "source_inventory_sha256": _sha256(inventory_bytes),
        "source_axis_identity_sha256": _sha256(
            "\n".join(identity).encode()
        ),
        "source_axis_count": len(axes),
        "fastener_assumption": {
            "thread": "1/4-20 UNC; matched finished hex nut assumed",
            "candidate_class": "partially threaded 1/4-in hex cap screw dimensional envelope to ASME B18.2.1",
            "sku": None,
            "supplier": None,
            "nominal_length_is_delivered_length": False,
            "head_side_washer_count": 1,
            "nut_side_washer_count": 1,
            "washer_nominal_thickness_mm_each": WASHER_NOMINAL_MM,
            "washer_thickness_min_mm": WASHER_MIN_MM,
            "washer_thickness_max_mm": WASHER_MAX_MM,
            "nut_count": 1,
            "finished_hex_nut_max_thickness_mm": NUT_MAX_MM,
            "minimum_full_form_thread_past_far_nut_face_mm": THREAD_PROJECTION_MM,
            "minimum_projection_basis": "WJ05 center-node model uses 3.175 mm; this screen preserves that geometric allowance and does not establish a structural engagement requirement",
        },
        "dimensional_method": {
            "standard": "ASME B18.2.1-2012, Table 12 and Table 13, 1/4-in hex cap screw envelope",
            "nominal_length_measurement": "from the under-head bearing surface to the extreme end of the point; point length is included",
            "length_tolerance_minus_mm": "0.10 in through 6 in nominal; 0.18 in above 6 in nominal",
            "thread_reference_length_mm": "0.75 in through 6 in nominal; 1.00 in above 6 in nominal",
            "transition_allowance_mm": "0.25 in; Lg,max = nominal L - LT and Lb,min = Lg,max - Y",
            "wood_member_screen_allowance_mm_each": WOOD_MEMBER_ALLOWANCE_MM,
            "wood_member_screen_allowance_status": "screen-only ±0.5 mm per modeled wood layer; not a stock, cut, or receiving tolerance",
            "thread_bearing_condition": "measured body end must leave no more than one quarter of the nut-side wood member threaded if a later lateral method relies on nominal bolt diameter; otherwise use measured root diameter in that method",
            "transition_receiving_condition": "measure actual body end and first full-form thread together; first full-form thread must begin by the earliest nut bearing face",
            "thread_end_receiving_condition": "measure full-form thread through the entire nut and at least 3.175 mm beyond the far nut face, with thread end no farther than measured bolt tip",
            "standard_bounds_are_delivered_measurements": False,
        },
        "axes": axes,
        "groups": groups,
        "release": {
            "sku_selected": False,
            "supplier_selected": False,
            "purchase_authorized": False,
            "delivered_fastener_received": False,
            "capacity_assigned": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


def main() -> None:
    print(json.dumps(build_screen(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
