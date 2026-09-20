"""Regression for the bounded lower-only outer-post HL35 trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_outer_post import screen_outer_post

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_outer_post.json"
)


def test_outer_post_lower_only_trial():
    result = screen_outer_post()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["scope"] == "lower-only; upper center joint unresolved"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_bolt_axis_count"] == 12
    assert result["hl35_catalog_minimum_receiver_thickness_mm"] == 88.9
    assert result["bolt_receiver_thickness_mm"] == {
        "post": 184.15,
        "header": 38.1,
    }
    assert result["undersize_hl35_bolt_receivers_mm"] == {"header": 38.1}
    assert result["coincident_left_right_post_bolt_rows"] == [1, 2]
    assert result["unique_post_through_bolt_axes"] == 2
    assert result["post_bores_shared_between_side_plates"] is True
    assert result["multilateral_fastener_action"].startswith("unresolved")
    assert result["upper_lower_header_bore_spacing"].startswith("not applicable")
    assert result["kicker_seam_supported"] is True
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert result["independent_header_bore_crossings_mm3"] == {}
    assert result["plate_pair_clashes_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert result["protected_screw_hardware_clashes_mm3"] == {}
    assert result["bore_panel_clashes_mm3"] == {}
    assert result["bore_adjacent_wood_clashes_mm3"] == {}
    assert result["conditional_63_5_overall_screw_hardware_clashes_mm3"] == {
        "round_kicker_left_center_2": {"shared_post_2": 4.629},
        "round_kicker_right_center_2": {"shared_post_2": 4.629},
    }
    assert result["failures"] == [
        "HL35 catalog minimum receiver thickness",
        "conditional purchased-overall screw envelope collision",
    ]
    assert json.loads(REPORT.read_text()) == result
