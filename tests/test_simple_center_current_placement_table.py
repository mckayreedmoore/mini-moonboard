"""Regression checks for the current center placement inventory."""

from scripts import simple_center_combined_cleats_probe as historical
from scripts.simple_center_current_placement_table import table


def _find(rows, bolt, member, feature):
    return next(
        r
        for r in rows
        if (r["bolt"], r["member"], r["feature"]) == (bolt, member, feature)
    )


def test_current_inventory_includes_changed_and_inherited_bolts():
    result = table()
    assert result["variant_id"] == "ligament_priority"
    assert result["bolt_count"] == 10
    assert {r["bolt"] for r in result["rows"]} == {
        "post_cleat_1",
        "post_cleat_2",
        "cleat_header_1",
        "cleat_header_2",
        "header_cleat",
        "cleat_principal",
        "post_low",
        "post_high",
        "upright",
        "cleat_link",
    }
    assert result["whole_center_classification_complete"] is False
    assert any(r["marker_status"] == "unknown" for r in result["rows"])


def test_inherited_near_edge_cannot_be_reported_as_five_mm_whole_center_margin():
    # The review's old 0.3 mm position is real in the former single-bolt pose.
    old = historical.new_bores()["post_cleat"].BoundingBox()
    old_y = (old.ymin + old.ymax) / 2
    assert round(old_y - (-175.7) - 25.4, 5) == 0.3

    result = table()
    post_high = _find(result["rows"], "post_high", "shifted_right_post", "z_high")
    assert post_high["nominal_distance_mm"] == 48.9
    assert post_high["marker_mm"] == 44.45
    assert post_high["fabrication_allowance_mm"] == 5.0
    assert post_high["reserve_mm"] == -0.55
    assert result["conditional_subset_minimum_reserve_mm"] < 5.0
    assert result["whole_center_classification_complete"] is False


def test_single_allowance_and_neighbor_classification():
    result = table()
    row = _find(result["rows"], "post_cleat_1", "shifted_right_post", "y_low")
    assert row["nominal_distance_mm"] == 30.7
    assert row["marker_mm"] == 25.4
    assert row["fabrication_allowance_mm"] == 5.0
    assert row["reserve_mm"] == 0.3  # 30.7 - 25.4 - 5, not minus 10.

    pair = _find(result["rows"], "cleat_header_1", "base_header", "cleat_header_2")
    assert pair["nominal_distance_mm"] == 30.5536
    assert pair["reserve_mm"] == 0.1536
    unknown = _find(result["rows"], "upright", "base_principal_center_right", "y_low")
    assert unknown["marker_status"] == "unknown"
    assert unknown["reserve_mm"] is None

    for bolt, member, other, distance in (
        ("post_high", "shifted_right_post", "post_cleat_2", 14.0),
        ("upright", "upright_side_cleat", "cleat_link", 14.0),
    ):
        gap = _find(result["rows"], bolt, member, other)
        assert gap["kind"] == "orthogonal_neighbor"
        assert gap["nominal_distance_mm"] == distance
        assert gap["marker_status"] == "unknown"
