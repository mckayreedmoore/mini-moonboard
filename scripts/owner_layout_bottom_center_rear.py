"""One source-distinct 77-mm rear-face bottom-center owner-layout trial."""

import json

from scripts import owner_layout_bottom_center_pair as first

SOURCE_ID = "owner-bottom-center-pair-x180-rear-77x139p7-layout-v3"
BLOCK_X_MM = 77.0
BLOCK_N_MIN_MM = 260.0
RAIL_X_MM = (26.0, 51.0)
RAIL_N_OFFSET_MM = 85.0
WIRE_072_STL_N_MIN_MM = 216.246317951324
WIRE_072_STL_N_MAX_MM = 281.690589594209
PRINCIPAL_N_HIGH_MM = 349.540967859313
TRIAL_BOLT_DIAMETER_MM = 6.35


def screen():
    """Screen the unified topology; PB02's historical cleat is absent."""
    report = first.screen_variant(
        SOURCE_ID,
        BLOCK_X_MM,
        RAIL_X_MM,
        block_side="rear",
        block_n_min_mm=BLOCK_N_MIN_MM,
        rail_n_offset_mm=RAIL_N_OFFSET_MM,
        include_pb02_side_cleat=False,
    )
    if report["source_id"] != SOURCE_ID:
        raise ValueError("Rear bottom-center source binding changed")
    return {
        **report,
        "rear_basis": {
            "assembly_topology": "unified-24-duty-without-PB02-side-cleat-or-rear-return",
            "owner_rear_envelope_compliant": False,
            "owner_exception_required": True,
            "rear_block_n_overhang_beyond_rail_mm": (
                BLOCK_N_MIN_MM + first.BLOCK_N_MM - PRINCIPAL_N_HIGH_MM
            ),
            "F1_G1_wire_name": "wire_072_F1_G1",
            "F1_G1_wire_stl_local_n_bounds_mm": [
                WIRE_072_STL_N_MIN_MM,
                WIRE_072_STL_N_MAX_MM,
            ],
            "F1_G1_wire_n_overlap_with_block_mm": (
                WIRE_072_STL_N_MAX_MM - BLOCK_N_MIN_MM
            ),
            "rail_face_overlap_n_mm": 349.540967859313 - BLOCK_N_MIN_MM,
            "rail_bolt_n_from_block_low_mm": (
                209.840967859313 + RAIL_N_OFFSET_MM - BLOCK_N_MIN_MM
            ),
            "principal_2_row_n_mm": BLOCK_N_MIN_MM + first.UPRIGHT_N_MM[1],
            "principal_n_high_mm": PRINCIPAL_N_HIGH_MM,
            "max_block_n_low_for_two_4D_edges_and_4D_pitch_mm": (
                PRINCIPAL_N_HIGH_MM - 12 * TRIAL_BOLT_DIAMETER_MM
            ),
            "protected_services_moved": False,
            "frame_cuts_changed": False,
            "tolerance_and_installed_access_verified": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
