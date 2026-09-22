"""A rearward-only header bolt cannot clear both the joint and receiver edges."""

from scripts.simple_owner_outer_base_rearward_gate import screen


def test_rearward_only_outer_base_header_bolt_is_rejected():
    result = screen()
    assert result["header_rear_y_mm"] == -175.7
    assert result["outer_header_block_rear_y_mm"] == -150.3
    assert result["conditional_4d_min_center_y_mm"] == -150.3
    assert result["shaft_clear_max_center_y_mm"] == -153.475
    assert result["washer_clear_max_center_y_mm"] == -163.0
    assert result["full_washer_seat_min_center_y_mm"] == -163.0
    assert result["tool_clear_max_center_y_mm"] == -170.3
    assert result["trial_70mm_block"]["front_y_mm"] == -115.7
    assert result["trial_70mm_block"]["block_loaded_edge_mm"] == 25.4
    assert result["trial_70mm_block"]["header_receiver_rear_edge_mm"] == 15.4
    assert result["trial_70mm_block"]["washer_y_overlap_mm"] == 2.7
    assert result["decision"] == "REVISE_NO_REARWARD_ONLY_POSE"
    assert result["cad_run_needed"] is False
    assert result["strength_checked"] is False
    assert result["drilling_released"] is False
