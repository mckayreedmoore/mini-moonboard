"""Bounded PB06 bottom pair relocation remains geometry-only."""

from scripts import simple_pb06_bottom_pair_revision as revision


def test_bottom_pair_revision():
    report = revision.screen()
    assert report["candidate_block_length_mm"] == 295.0
    assert report["candidate_rail_offsets_from_butt_mm"] == [70.0, 95.0]
    assert report["prior_issues_resolved"] == {
        "second_rail_bores_complete": False,
        "right_side_cleat_clear": False,
    }
    assert report["inventory"]["panel_kicker_axes"] == 66
    assert report["inventory"]["frame_axes"] == 12
    assert report["inventory"]["existing_blocks"] == 10
    assert report["inventory"]["target_sds_axes_retained"] == 12
    assert report["decision"] == "REVISE"
    assert report["geometry_gates"]["conditional_signed_4d"] is True
    assert report["geometry_gates"]["purchased_stock_length_shafts_verified"] is False
    assert any(
        "incomplete nominal bore" in row for row in report["binding_constraints"]
    )
    assert any("upright_side_cleat" in row for row in report["binding_constraints"])
    assert report["strength_checked"] is False
    assert report["drilling_released"] is False
