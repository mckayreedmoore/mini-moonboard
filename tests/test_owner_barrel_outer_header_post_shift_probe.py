"""An inward post shift must not be called a viable fixed-axis joint on clearance alone."""

from scripts.owner_barrel_outer_header_post_shift_probe import search


def test_post_shift_exposes_clearance_vs_retained_frame_bolt_tradeoff():
    result = search()
    assert result["schema"] == "owner_barrel_outer_header_post_shift_probe/v1"
    assert result["width_option"] == "kerf-right"
    assert result["fixed_axes"] == {"panel_screws": 66, "frame_bolts": 12}
    assert result["shifts_inward_mm"] == [0, 20, 40, 60, 80, 90]
    assert len(result["candidates"]) == 12
    assert result["fully_viable_fixed_axis_poses"] == []

    for side in ("left", "right"):
        assert result["thresholds_by_side_mm"][side] == {
            "minimum_shift_for_20mm_tool_rim_clearance_mm": 79.85,
            "shift_at_loss_of_front_bolt_centerline_post_overlap_mm": 40.132,
            "shift_at_loss_of_kicker_screw_receiver_centerline_mm": 19.05,
            "shift_at_loss_of_all_post_rim_x_projection_mm": 88.9,
        }
        rows = {
            row["shift_inward_mm"]: row
            for row in result["candidates"]
            if row["side"] == side
        }
        assert set(rows) == {0, 20, 40, 60, 80, 90}
        assert rows[0]["rim_projection_overlap_x_mm"] == 38.1
        assert rows[0]["front_bolt_axis_post_centerline_overlap_mm"] == [38.1, 38.1]
        assert rows[0]["kicker_screw_axis_post_x_edge_margin_mm"] == [19.05, 19.05]
        assert rows[0]["kicker_screw_axis_post_centerline_overlap_mm"] == [
            32.54375,
            32.54375,
        ]
        assert rows[0]["header_butt_area_mm2"] == 5322.57
        assert rows[0]["outer_header"]["access_side_rim_hits_mm3"] == [12566.370614] * 2

        assert rows[80]["outer_header"]["shaft_side_rim_hits_mm3"] == [0.0, 0.0]
        assert rows[80]["outer_header"]["access_side_rim_hits_mm3"] == [0.0, 0.0]
        assert rows[80]["rim_projection_overlap_x_mm"] == 8.9
        assert rows[80]["front_bolt_axis_post_centerline_overlap_mm"] == [0.0, 0.0]
        assert rows[80]["kicker_screw_axis_post_centerline_overlap_mm"] == [0.0, 0.0]
        assert rows[80]["header_butt_area_mm2"] == 5322.57
        assert "fixed_front_bolts_enter_post" in rows[80]["failed_gates"]
        assert "fixed_kicker_screws_enter_post" in rows[80]["failed_gates"]

        assert rows[90]["rim_projection_overlap_x_mm"] == 0.0
        assert "rim_projection_overlap" in rows[90]["failed_gates"]
        assert rows[40]["front_bolt_axis_post_centerline_overlap_mm"] == [0.132, 0.132]
        assert rows[20]["kicker_screw_axis_post_x_edge_margin_mm"] == [-0.95, -0.95]
        assert "fixed_kicker_screws_enter_post" in rows[20]["failed_gates"]

    assert not result["viewer_changed"]
    assert not result["drilling_released"]
    assert not result["structural_released"]
