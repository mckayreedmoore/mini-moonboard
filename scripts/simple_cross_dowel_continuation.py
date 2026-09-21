"""Continue CD-01 recessed_centered_receiver_pair; no drill/capacity release."""

import json

INCH_MM = 25.4
SECTION_MM = (38.1, 139.7)
BARREL_END_DISTANCE_MM = 70.0
ROW_N_MM = (265.0, 310.0)
# Read from CD-01's kerf-right uncut rail via its _local_bounds helper.
RAIL_N_BOUNDS_MM = (209.84096785931308, 349.54096785931307)
ROWS_MM = tuple(n - RAIL_N_BOUNDS_MM[0] for n in ROW_N_MM)
SOURCE_NOTE = "docs/bolted-candidate-prototypes/simple-pb01-cross-dowel-trial.md"
SOURCE_SCRIPT = "scripts/simple_pb01_cross_dowel_trial.py"
REOPENING_TRIGGER = (
    "Obtain SKU-linked body/axis/complete-thread limits and a traceable barrel "
    "material/thread resistance or part-specific test basis; then rerun the "
    "recessed-centered pose with actual bolt/washer stack and changed-topology "
    "joint checks. Corner-block work continues independently."
)

# Retail nominal fields. OD/length came from Hillman customer service through
# Lowe's; the axis offset remains an explicit sensitivity, not a Hillman fact.
BARREL_LENGTH_MM = 0.630 * INCH_MM
BARREL_OD_MM = 0.394 * INCH_MM
THREAD_MAJOR_MM = 0.25 * INCH_MM
AXIS_OFFSET_SENSITIVITY_MM = (6.0, BARREL_LENGTH_MM / 2, 10.0)

# Exact retail bolt lead, with an unverified washer thickness carried only to
# expose the installed-length gate.
BOLT_LENGTH_MM = 5.0 * INCH_MM
WOOD_PATH_TO_AXIS_MM = 108.1
WASHER_THICKNESS_SENSITIVITY_MM = 0.065 * INCH_MM


def _pose(axis_offset_mm: float) -> dict:
    axis_depth = SECTION_MM[0] / 2
    recess = axis_depth - axis_offset_mm
    far_wood = SECTION_MM[0] - recess - BARREL_LENGTH_MM
    end_metal = (
        min(axis_offset_mm, BARREL_LENGTH_MM - axis_offset_mm) - THREAD_MAJOR_MM / 2
    )
    cross_bore_depth = recess + BARREL_LENGTH_MM
    return {
        "axis_offset_mm_not_hillman_specification": round(axis_offset_mm, 4),
        "recess_mm": round(recess, 4),
        "cross_bore_depth_mm": round(cross_bore_depth, 4),
        "wood_beyond_barrel_mm": round(far_wood, 4),
        "minimum_end_metal_outside_thread_major_radius_mm": round(end_metal, 4),
        "nominal_body_fit": recess >= 0 and far_wood >= 0 and end_metal >= 0,
    }


def screen() -> dict:
    poses = [_pose(offset) for offset in AXIS_OFFSET_SENSITIVITY_MM]
    row_spacing = ROWS_MM[1] - ROWS_MM[0]
    row_edge = min(ROWS_MM[0], SECTION_MM[1] - ROWS_MM[1])
    tip_from_seat = BOLT_LENGTH_MM - WASHER_THICKNESS_SENSITIVITY_MM
    tip_beyond_axis = tip_from_seat - WOOD_PATH_TO_AXIS_MM
    mechanisms = {
        "barrel_transverse_section_and_bending": False,
        "barrel_internal_thread_stripping": False,
        "bolt_tension_shear_bending_and_threads": False,
        "washer_and_principal_face_bearing": False,
        "rail_barrel_bearing_and_end_tearout": False,
        "rail_splitting_and_net_section": False,
        "bolt_group_distribution_rotation_and_stiffness": False,
        "simultaneous_changed_topology_pb05_pb06_actions": False,
    }
    return {
        "schema": "simple_cross_dowel_continuation/v1",
        "alternative": "PB05/PB06 alternative continuing the exact CD-01 pose",
        "source_trial": {
            "note": SOURCE_NOTE,
            "script": SOURCE_SCRIPT,
            "pose": "recessed_centered_receiver_pair",
            "participants": [
                "base_principal_center_right",
                "base_rail_service_lower_right",
            ],
            "butt_x_mm": 89.05,
            "row_n_mm": list(ROW_N_MM),
            "entry_faces": ["minus_t", "plus_t"],
            "barrel_od_mm": 10.0,
            "barrel_length_mm": 16.0,
            "barrel_recess_mm": 11.05,
            "thread_axis_from_barrel_end_mm": 8.0,
            "thread_axis_from_entry_face_mm": 19.05,
            "blind_cross_bore_depth_mm": 27.05,
            "machine_bore_diameter_mm": 7.5,
            "bolt_length_mm": 127.0,
            "access_diameter_and_length_mm": [20.0, 40.0],
            "cad_collisions_rerun": False,
        },
        "retail": {
            "barrel": "Hillman 880543, Lowe's item 137362 / Home Depot 202242356",
            "bolt": "Everbilt 800676, Home Depot 204633308",
            "washer": "Hillman 490687, Lowe's item 58124",
            "barrel_unit_usd": 1.48,
            "bolt_unit_usd": 0.62,
            "washer_pack_usd": 1.98,
            "washer_pack_count": 16,
            "two_stack_consumed_usd": round(2 * 1.48 + 2 * 0.62 + 2 * 1.98 / 16, 4),
            "two_stack_checkout_usd": round(2 * 1.48 + 2 * 0.62 + 1.98, 2),
            "complete_installed_cost_usd": None,
            "added_wood_volume_mm3": 0,
        },
        "whole_section_geometry": {
            "timber_section_mm": list(SECTION_MM),
            "barrel_end_distance_mm": BARREL_END_DISTANCE_MM,
            "row_centers_from_rail_n_min_mm": [round(n, 4) for n in ROWS_MM],
            "rail_n_bounds_mm": list(RAIL_N_BOUNDS_MM),
            "row_spacing_mm": round(row_spacing, 4),
            "minimum_row_center_to_section_edge_mm": round(row_edge, 4),
            "nominal_barrel_od_mm": BARREL_OD_MM,
            "nominal_barrel_length_mm": BARREL_LENGTH_MM,
            "poses": poses,
            "all_sensitivity_poses_fit_nominal_body": all(
                p["nominal_body_fit"] for p in poses
            ),
        },
        "installed_stack_sensitivity": {
            "wood_seat_to_thread_axis_mm": WOOD_PATH_TO_AXIS_MM,
            "bolt_under_head_length_mm": BOLT_LENGTH_MM,
            "washer_thickness_mm_not_product_control": WASHER_THICKNESS_SENSITIVITY_MM,
            "tip_beyond_thread_axis_mm": round(tip_beyond_axis, 4),
            "tip_position_from_seat_mm_before_clearance_allowance": round(
                tip_from_seat, 4
            ),
            "complete_thread_overlap_known": False,
            "tip_clearance_proven": False,
        },
        "tool_and_assembly": {
            "bolt_drive": "7/16 in wrench per retail bolt listing",
            "barrel_orientation": "slotted end and flat-head screwdriver per retail barrel listing",
            "opposite_face_barrel_entries": True,
            "recessed_barrel_extraction_method_proven": False,
            "cross_bore_jig_and_depth_control_proven": False,
            "physical_assembly_trial_complete": False,
        },
        "protected_panel_kicker_axes_changed": False,
        "protected_panel_kicker_axis_count": 66,
        "strength_mechanisms_supported": mechanisms,
        "shaft_rating_used_as_joint_capacity": False,
        "geometry_observation": "nominal body containment only; actual SKU fit unproven",
        "decision": "PARK",
        "reopening_trigger": REOPENING_TRIGGER,
        "manufacturer_contacted": False,
        "blocks_corner_block_work": False,
        "fabrication_or_drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
