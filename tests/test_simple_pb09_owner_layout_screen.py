"""PB09 is a detached owner-layout screen, not an active native candidate."""

import os

import pytest

from scripts import simple_pb09_owner_layout_screen as pb09


def test_layout_has_positive_conditional_reserves():
    rows = pb09.layout_reserves()
    assert rows["upright_rear_rear_end_7d_mm"] == pytest.approx(3.0)
    assert rows["upper_outer_front_end_7d_mm"] == pytest.approx(0.55)
    assert rows["upper_center_rear_end_7d_mm"] > 0
    assert rows["outer_near_rail_end_7d_mm"] > 0
    assert rows["outer_far_x_loaded_edge_4d_mm"] > 0
    assert rows["outer_rail_row_spacing_4d_mm"] > 0


def test_screen_is_source_distinct_and_no_release():
    result = pb09.screen()
    if os.environ.get("PB09_DIAGNOSTIC"):
        print(
            {
                "decision": result["decision"],
                "channel": result["service_channel"],
                "targeted_hits": result["targeted_revision_hits_mm3"],
                "blocking_pairs": result["blocking_pair_hits_mm3"],
                "protected_hits": result["protected_hits_mm3"],
                "protected_tool_hits": result["protected_tool_hits_mm3"],
                "protected_tool_status": result["protected_tool_status"],
                "conditional_tool_hits": {
                    name: row["conditional_25p4_tool_hits_mm3"]
                    for name, row in result["stations"].items()
                    if row["conditional_25p4_tool_hits_mm3"]
                },
            }
        )
    assert result["source_id"] == pb09.SOURCE_ID
    assert result["layout_revision"] == pb09.LAYOUT_REVISION
    assert result["source_id"] != pb09.pb07.SOURCE_ID
    assert result["inventory"] == {
        "blocks": 10,
        "new_bolt_axes": 40,
        "panel_kicker_axes": 66,
        "original_frame_bolt_axes": 12,
        "legacy_sds_axes": 72,
        "legacy_duties": 12,
    }
    assert set(result["stations"]) == set(pb09.STATIONS)
    assert all(
        row["block_dimensions_mm"][2] == 139.7 for row in result["stations"].values()
    )
    assert all(
        row["aligned_to_rearward_2x6_n_envelope"] for row in result["stations"].values()
    )
    assert all(
        row["stock_8in_upright"]["two_thread_projection_margin_mm"] > 0
        for row in result["stations"].values()
    )
    assert result["native_solve"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert result["decision"] in (
        "LAYOUT_ONLY_CLEAR",
        "CONDITIONAL_TOOL_LAYOUT_ONLY",
        "REVISE_LAYOUT",
    )
    channel = result["service_channel"]
    assert channel["wire"] == "wire_054_E6_E7"
    assert channel["radius_mm"] == 5.0
    assert channel["channel_applied"] == (channel["pre_cut_wire_hit_mm3"] > 0)
    assert (channel["removed_wood_mm3"] > 1) == channel["channel_applied"]
    assert channel["post_cut_wire_hit_mm3"] <= 1
    if channel["actual_wire_hit_mm3"] > 0:
        assert result["decision"] == "REVISE_LAYOUT"
    assert (
        channel["owner_approval_and_strength_check_required"]
        == channel["channel_applied"]
    )
    assert channel["qualified_for_layout_selection"] == (not channel["channel_applied"])
    assert result["decision"] == "REVISE_LAYOUT"
    assert all(value > 0 for value in channel["remaining_contact_area_mm2"].values())
    for name in (*pb09.lower.TARGET_STATIONS, *pb09.lower.LOWER_OUTER_STATIONS):
        assert result["stations"][name]["block_dimensions_mm"][1] == 76.2
    for name in (
        *pb09.upper_outer.TARGET_STATIONS,
        *pb09.bottom.TARGET_STATIONS,
        *pb09.upper_center.TARGET_STATIONS,
    ):
        assert result["stations"][name]["block_dimensions_mm"][1] == 57.15
    if (
        result["targeted_revision_hits_mm3"]
        or channel["bore_or_stack_hits_mm3"]
        or any(
            row["generic_5in_rail"]["generic_5in_two_thread_margin_mm"] < 0
            for row in result["stations"].values()
        )
    ):
        assert result["decision"] == "REVISE_LAYOUT"
    assert any(
        row["tool_to_installed_or_fixed_hits_mm3"]
        for row in result["stations"].values()
    )
    if result["blocking_pair_hits_mm3"] or any(
        row["conditional_25p4_tool_hits_mm3"] for row in result["stations"].values()
    ):
        assert result["decision"] == "REVISE_LAYOUT"
    assert result["protected_tool_status"] in (
        "screened",
        "not_run_due_core_intersections",
    )
    for name in pb09.bottom.TARGET_STATIONS:
        row = result["stations"][name]
        assert row["rail_x_mm"] == (46.0, 74.0)
        assert row["rail_n_mm"] == pytest.approx(pb09.LOWER_RAIL_N_MM)
    gates = result["protected_geometry_gates"]
    assert gates["inventory_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert gates["all_66_panel_screw_axes_modeled"] is True
    assert gates["all_12_retained_frame_bolt_axes_modeled"] is True
    for name in (
        "panel_screw_installed_bodies_and_heads_clear",
        "retained_frame_bolt_installed_stacks_clear",
        "delivered_hold_bolt_length_clear",
        "actual_wiring_bends_clear",
    ):
        assert gates[name] is None
