"""Outer-header alternatives must retain the owner's fixed geometry and no-release gates."""

from scripts.owner_barrel_outer_header_clearance_probe import search


def test_bounded_outer_header_search_reports_both_sides_and_real_blockers():
    result = search()
    assert result["schema"] == "owner_barrel_outer_header_clearance_probe/v1"
    assert result["panel_screw_axes_preserved"] == 66
    assert result["retained_frame_bolt_axes_preserved"] == 12
    assert result["protected_inventory_counts"]["tnuts"] == 142
    assert result["sides"] == ["left", "right"]
    assert result["candidate_count"] == len(result["candidates"])
    assert {row["orientation"] for row in result["candidates"]} == {
        "vertical_top",
        "oblique_top_inboard",
        "vertical_bottom",
    }
    baseline = [row for row in result["candidates"] if row["pose"] == "baseline"]
    assert len(baseline) == 2
    for row in baseline:
        assert row["failed_gates"] == ["unrelated_wood"]
        assert row["shaft_side_rim_hits_mm3"] == [52.285878] * 2
        assert row["access_side_rim_hits_mm3"] == [12566.370614] * 2
    for row in result["candidates"]:
        if row["orientation"] == "oblique_top_inboard":
            assert row["shaft_side_rim_hits_mm3"] == [0.0] * 2
            assert row["access_side_rim_hits_mm3"] == [0.0] * 2
            assert "seam_in_post" in row["failed_gates"]
        if row["orientation"] == "vertical_bottom":
            assert "bolt_reaches_barrel" in row["failed_gates"]
            assert [item["bolt_reach_past_axis_mm"] for item in row["rows"]] == [
                -132.601
            ] * 2
    for row in result["candidates"]:
        assert len(row["rows"]) == 2
        assert row["failed_gates"] or row["geometry_gates_clear"]
    assert result["geometry_clear_poses"] == []
    assert not result["drilling_released"]
    assert not result["fabrication_released"]
    assert not result["structural_released"]
