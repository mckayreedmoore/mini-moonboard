"""PB01 barrel/bolt intersection sensitivity, not a drill or resistance design."""

import json

RAIL_THICKNESS_MM = 38.1
AXIS_DEPTH_FROM_ENTRY_FACE_MM = 19.05
WOOD_PATH_TO_THREAD_AXIS_MM = 108.1
BARREL_LENGTH_MM = 16.002  # Hillman 880543 nominal customer-service answer
BARREL_OD_MM = 10.0076  # Hillman 880543 nominal customer-service answer
BOLT_LENGTH_MM = 127.0  # CD-01 trial, not a qualified purchased bolt
BOLT_MAJOR_DIAMETER_MM = 6.35  # 1/4-20 nominal


def connection_fit(
    *,
    body_length_mm: float,
    body_od_mm: float,
    axis_offset_mm: float,
    bolt_under_head_length_mm: float,
    washer_stack_mm: float,
    bolt_complete_thread_mm: tuple[float, float],
    nut_complete_thread_x_mm: tuple[float, float],
    hole_depth_mm: float,
    required_tip_clearance_mm: float,
) -> dict:
    """Screen measured inputs; bolt threads start at head underside, nut at axis."""
    recess = AXIS_DEPTH_FROM_ENTRY_FACE_MM - axis_offset_mm
    far_wood = RAIL_THICKNESS_MM - recess - body_length_mm
    end_metal = (
        min(axis_offset_mm, body_length_mm - axis_offset_mm)
        - BOLT_MAJOR_DIAMETER_MM / 2
    )
    radius = body_od_mm / 2
    bolt_start, bolt_end = bolt_complete_thread_mm
    nut_start, nut_end = nut_complete_thread_x_mm
    if not (
        recess >= 0
        and far_wood >= 0
        and end_metal >= 0
        and body_length_mm > 0
        and body_od_mm > 0
        and 0 <= washer_stack_mm < bolt_under_head_length_mm
        and 0 <= bolt_start < bolt_end <= bolt_under_head_length_mm
        and -radius <= nut_start < nut_end <= radius
        and hole_depth_mm > 0
        and required_tip_clearance_mm >= 0
    ):
        raise ValueError("inputs exceed nominal body, wood, or bolt geometry")

    tip = bolt_under_head_length_mm - washer_stack_mm
    bolt_thread_x = (
        bolt_start - washer_stack_mm - WOOD_PATH_TO_THREAD_AXIS_MM,
        bolt_end - washer_stack_mm - WOOD_PATH_TO_THREAD_AXIS_MM,
    )
    overlap = max(
        0.0, min(bolt_thread_x[1], nut_end) - max(bolt_thread_x[0], nut_start)
    )
    clearance = hole_depth_mm - tip
    return {
        "recess_mm": round(recess, 4),
        "wood_beyond_body_mm": round(far_wood, 4),
        "minimum_nominal_end_metal_mm": round(end_metal, 4),
        "tip_beyond_axis_mm": round(tip - WOOD_PATH_TO_THREAD_AXIS_MM, 4),
        "complete_thread_overlap_mm": round(overlap, 4),
        "tip_clearance_mm": round(clearance, 4),
        "geometry_fit": overlap > 0 and clearance >= required_tip_clearance_mm,
        "engagement_capacity_proven": False,
        "selected": False,
    }


def screen() -> dict:
    """State nominal retail facts and the falsifiable offset range from analogs."""
    offsets = (6.0, 10.0)  # Other manufacturers' M6 products, not Hillman limits.
    recesses = [AXIS_DEPTH_FROM_ENTRY_FACE_MM - offset for offset in offsets]
    far_woods = [RAIL_THICKNESS_MM - recess - BARREL_LENGTH_MM for recess in recesses]
    tip_beyond_axis = BOLT_LENGTH_MM - WOOD_PATH_TO_THREAD_AXIS_MM
    return {
        "part": "Hillman 880543",
        "hillman_nominal_mm": {
            "length": BARREL_LENGTH_MM,
            "outside_diameter": BARREL_OD_MM,
        },
        "offset_interval_mm_not_hillman_specification": list(offsets),
        "required_recess_interval_mm": [min(recesses), max(recesses)],
        "minimum_nominal_wood_beyond_body_mm": min(far_woods),
        "nominal_tip_beyond_axis_without_washer_mm": tip_beyond_axis,
        "nominal_tip_beyond_body_without_washer_mm": round(
            tip_beyond_axis - BARREL_OD_MM / 2, 4
        ),
        "actual_hillman_axis_offset_known": False,
        "engagement_known": False,
        "structural_capacity_known": False,
        "selected": False,
        "selection_gate": (
            "Identify delivered part and measured axis/body limits; measure complete bolt/nut "
            "thread spans, washer seat and hole depth; establish required engagement and "
            "part-specific steel, wood, group and changed-topology resistance before selection."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
