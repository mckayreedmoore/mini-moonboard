"""PB01 cross-dowel offset sensitivity; never a drill or capacity schedule."""

import json

TIMBER_THICKNESS_MM = 38.1
BARREL_LENGTH_MM = 16.002
TARGET_THREAD_AXIS_DEPTH_MM = 19.05
THREAD_AXIS_OFFSETS_MM = (6.0, 8.001, 10.0)
BARREL_NOMINAL_OD_MM = 10.0076
THREAD_NOMINAL_MAJOR_DIAMETER_MM = 6.35


def screen():
    cases = []
    for offset in THREAD_AXIS_OFFSETS_MM:
        recess = TARGET_THREAD_AXIS_DEPTH_MM - offset
        far_face_wood = TIMBER_THICKNESS_MM - recess - BARREL_LENGTH_MM
        near_end_metal = offset - THREAD_NOMINAL_MAJOR_DIAMETER_MM / 2
        far_end_metal = BARREL_LENGTH_MM - offset - THREAD_NOMINAL_MAJOR_DIAMETER_MM / 2
        cases.append(
            {
                "thread_axis_from_entry_end_mm": offset,
                "required_body_recess_mm": round(recess, 3),
                "cross_bore_depth_mm": round(recess + BARREL_LENGTH_MM, 3),
                "wood_beyond_body_mm": round(far_face_wood, 3),
                "nominal_end_metal_beyond_thread_major_radius_mm": [
                    round(near_end_metal, 3),
                    round(far_end_metal, 3),
                ],
                "body_nominally_inside_wood": recess >= 0 and far_face_wood >= 0,
                "thread_major_circle_nominally_inside_body_length": (
                    near_end_metal >= 0 and far_end_metal >= 0
                ),
            }
        )

    return {
        "study": "PB01 Hillman 880543 thread-axis follow-up sensitivity",
        "fixed_geometry": {
            "timber_thickness_mm": TIMBER_THICKNESS_MM,
            "target_thread_axis_depth_mm": TARGET_THREAD_AXIS_DEPTH_MM,
            "hillman_nominal_barrel_length_mm": BARREL_LENGTH_MM,
            "hillman_nominal_barrel_od_mm": BARREL_NOMINAL_OD_MM,
            "nominal_thread_major_diameter_mm": THREAD_NOMINAL_MAJOR_DIAMETER_MM,
        },
        "analog_offset_range_mm_not_hillman_specification": [6.0, 10.0],
        "cases": cases,
        "all_cases_preserve_target_axis": all(
            abs(
                case["required_body_recess_mm"]
                + case["thread_axis_from_entry_end_mm"]
                - TARGET_THREAD_AXIS_DEPTH_MM
            )
            < 1e-9
            for case in cases
        ),
        "all_cases_nominally_fit": all(
            case["body_nominally_inside_wood"]
            and case["thread_major_circle_nominally_inside_body_length"]
            for case in cases
        ),
        "minimum_wood_beyond_body_mm": min(
            case["wood_beyond_body_mm"] for case in cases
        ),
        "qualification_route": (
            "measure each delivered barrel's entry end, overall length, outside "
            "diameter, thread-axis offset, and complete-thread span; then rerun "
            "with measured limits before setting any bore depth"
        ),
        "hillman_thread_axis_established": False,
        "effective_thread_engagement_established": False,
        "steel_grade_or_strength_established": False,
        "wood_bearing_capacity_established": False,
        "development_geometry_advance": True,
        "structural_advance": False,
        "fabrication_or_drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
