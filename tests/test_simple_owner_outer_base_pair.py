"""Bounded mirrored outer-base owner-layout proposal; no strength release."""

import pytest

from scripts.simple_owner_outer_base_pair import screen


def test_rearward_outer_base_pair():
    result = screen()
    assert result["source_id"] == "owner-outer-base-139p7-pair-v2"
    assert result["inventory"]["panel_screw_axes"] == 66
    assert result["inventory"]["retained_frame_bolt_axes"] == 12
    assert result["inventory"]["pb09_blocks"] == 10
    assert result["finite_protected_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert set(result["stations"]) == {"clip_angle_base_left", "clip_angle_base_right"}
    for side, row in (
        ("left", result["stations"]["clip_angle_base_left"]),
        ("right", result["stations"]["clip_angle_base_right"]),
    ):
        assert row["timber"] == ["base_header", f"base_side_{side}"]
        assert row["within_139p7_header_y_envelope"]
        assert row["block_box_mm"][3] == pytest.approx(-115.7)
        assert row["block_box_mm"][5] == pytest.approx(365.9)
        assert row["same_side_contact"]
        assert row["complete_host_bores"]
        assert row["conditional_4d_edges"]
        assert row["bottom_outer_near_tool_y_gap_mm"] > 0
        assert not any(
            "pb09_tool/clip_horizontal_bottom_" in name
            for name in row["protected_hits_mm3"]
        )
        assert len(row["nominal_stacks"]) == 2
        assert (
            row["nominal_stacks"][f"clip_angle_base_{side}_header"]["nominal_length_mm"]
            == 152.4
        )
        assert all(
            stack["length_margin_mm"] >= 0 for stack in row["nominal_stacks"].values()
        )
        assert all(stack["tip_in_far_tool"] for stack in row["nominal_stacks"].values())
    assert result["decision"] == "ADVANCE_GEOMETRY_ONLY", {
        name: {key: value for key, value in row.items() if key.endswith("hits_mm3")}
        for name, row in result["stations"].items()
    }
    assert result["protected_gates"]["delivered_hold_bolt_length"] is None
    assert result["protected_gates"]["wiring_bend_radius"] is None
    assert result["protected_gates"]["hardware_heads"] is None
    assert not result["strength_checked"]
    assert not result["drilling_released"]
