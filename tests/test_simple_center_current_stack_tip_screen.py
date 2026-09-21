"""Current short-block grip and permanent occupancy regression."""

from scripts.simple_center_current_stack_tip_screen import screen


def test_current_pose_all_ten_bores_and_limiting_stacks():
    result = screen()
    rows = result["rows"]
    assert len(rows) == 10
    assert result["block_bounds_mm"] == [177.65, 266.55, -175.7, -86.8, 95, 238.9]
    assert rows["cleat_header_1"]["wood_grip_mm"] == 182
    assert rows["cleat_header_2"]["minimum_projection_margin_in"] == 0.134646
    assert rows["header_cleat"]["wood_grip_mm"] == 109.1
    assert rows["cleat_principal"]["wood_grip_mm"] == 109.05
    assert rows["header_cleat"]["minimum_projection_margin_in"] < 0.005
    assert rows["cleat_principal"]["minimum_projection_margin_in"] < 0.007
    assert len(result["per_end_permanent_occupancy"]) == 60
    assert result["modeled_wood_and_fixed_screws_clear_both_orientations"]
    assert result["potential_other_bolt_permanent_hits_mm3"] == {}
    assert not result["procurement_or_drilling_released"]
    assert all(not row["actual_thread_nut_washer_verified"] for row in rows.values())
