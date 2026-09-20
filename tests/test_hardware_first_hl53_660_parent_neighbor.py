"""The zero-gap rail must be screened in its 660-mm parent context."""

import json

import pytest

from scripts.hardware_first_hl53_660_parent_neighbor import (
    OUTPUT,
    screen_parent_neighbor,
)


@pytest.fixture(scope="module")
def report():
    return screen_parent_neighbor()


def test_parent_neighbor_screen_is_bounded_and_preserves_fixed_axes(report):
    assert report["rib_spacing_mm"] == 660
    assert report["rail_to_rib_gap_mm"] == 0
    assert report["header_bracket_count"] == 8
    assert report["fixed_panel_kicker_axis_count"] == 66
    assert report["fixed_screw_receiver_loss_mm3"] == {}
    assert report["parent_wood_names"]
    assert len(report["parent_header_bracket_names"]) == 8
    assert report["status"] == "partial_parent_neighbor_geometry_clear"
    assert all(not clashes for clashes in report["checks_mm3"].values())
    assert report["old_frame_axis_hits_mm3_diagnostic_only"] == {}
    assert report["isolated_zero_gap_status"] == "isolated_joint_geometry_clear"
    assert report["other_rail_ends_open"] == 5
    assert report["connected_architecture_verdict"] is False
    assert report["catalog_applicability_verified"] is False
    assert report["actual_hardware_access_verified"] is False
    assert report["load_rating_adopted"] is False
    assert report["drilling_released"] is False


def test_report_serializes_without_overwriting_prior_prototypes(report):
    assert json.loads(OUTPUT.read_text()) == report
