"""Independent backing bolts must be screened as two-member HL33 attachments."""

import json

import pytest

from scripts.hardware_first_hl33_backing_revision import OUTPUT, screen_backing_revision


@pytest.fixture(scope="module")
def result():
    return screen_backing_revision()


def test_topology_has_no_shared_backing_bolt(result):
    assert result["backing_member_count"] == 1
    assert result["backing_bracket_count"] == 2
    assert result["backing_bolt_axes"] == [
        "backing_left_core",
        "backing_left_member",
        "backing_right_core",
        "backing_right_member",
    ]
    assert result["backing_bolt_receiver_count"] == {
        name: 1 for name in result["backing_bolt_axes"]
    }
    assert result["minimum_hl33_receiver_thickness_mm"] >= 88.9
    assert result["below_minimum_receivers_mm"] == {}


def test_fixed_geometry_and_access_are_not_silently_accepted(result):
    assert result["fixed_panel_count"] == 6
    assert result["fixed_screw_axis_count"] == 66
    assert result["fixed_screw_receiver_loss_mm3"] == {}
    assert len(result["kicker_center_receiver_mm3"]) == 4
    assert all(v > 0 for v in result["kicker_center_receiver_mm3"].values())
    assert result["kicker_inner_seam_backed"]
    assert result["stack_envelope_count"] == 60
    assert result["access_failures_mm3"]
    assert result["status"] == "rejected_nominal_pose"
    assert result["rating_or_drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == result


def test_blank_comparator_and_rail_gap_stated(result):
    assert result["blank_comparator"]["ordinary_nominal"] == "4x12x12-ft"
    assert result["blank_comparator"]["one_piece_fit"]["core"]
    assert not result["blank_comparator"]["one_piece_fit"]["backing"]
    assert result["ordinary_stock_gate"].startswith("open:")
    assert result["rail_connection_established"] is False
