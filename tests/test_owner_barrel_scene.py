"""The published barrel scene is a complete, explicitly unqualified snapshot."""

import json
from pathlib import Path

from scripts import owner_barrel_outer_header_recess_probe as independent
from scripts import owner_barrel_outer_top_layout as outer
from scripts.simple_owner_duty_ledger import selected_duties


def test_published_barrel_scene_inventory_and_release_boundary():
    path = Path(__file__).resolve().parents[1] / "site/owner-barrel-layout-scene.json"
    scene = json.loads(path.read_text())
    duties = set(selected_duties())
    inventory = scene["inventory"]
    assert scene["schema"] == "owner_barrel_layout_scene/v1"
    assert scene["status"] == "complete_layout_concept_not_qualified"
    assert scene["baseline"] == "compact-floor-flush-kerf-right"
    assert set(scene["station_modes"]) == set(scene["station_dispositions"]) == duties
    assert inventory["replaced_angle_duties"] == 24
    assert inventory["removed_structural_sds"] == 144
    assert inventory["direct_joint_duties"] == 24
    assert inventory["integrated_center_posts"] == 2
    assert inventory["kicker_screw_backers"] == 0
    assert inventory["barrel_replacement_timbers"] == 16
    assert "mixed_compact_block_duties" not in inventory
    assert {row["role"] for row in scene["solids"]} == {
        "integrated_center_post",
        "barrel_replacement_timber",
        "derived_cut_header",
    }
    assert len(scene["solids"]) == 16
    assert scene["visual_wood_replacement"]["excluded_legacy_sds_axes"] == 144
    assert (
        scene["visual_wood_replacement"]["fixed_panel_receiver_cuts_in_replacements"]
        == 66
    )
    assert (
        scene["visual_wood_replacement"]["fixed_panel_axes_landing_on_separate_backers"]
        == 0
    )
    assert scene["visual_wood_replacement"]["release"] is False
    assert inventory["barrel_nut_envelopes"] == 48
    assert inventory["new_diagnostic_bolt_axes"] == 48
    assert inventory["rail_head_washer_envelopes"] == 40
    assert inventory["other_head_washer_envelopes"] == 48
    assert inventory["backer_attachment_duties"] == 0
    assert inventory["backer_barrel_nut_envelopes"] == 0
    assert inventory["backer_diagnostic_bolt_axes"] == 0
    all_axes = scene["diagnostic_bolt_axes"] + scene["backer_diagnostic_bolt_axes"]
    assert len(all_axes) == 48
    assert all(
        row["nominal_axial"]["thread_engagement"] == "UNKNOWN" for row in all_axes
    )
    assert all(row["nominal_axial"]["tip_past_assumed_axis_mm"] > 0 for row in all_axes)
    assert (
        sum(
            "BEYOND_MODELED_MACHINE_BORE" in row["nominal_axial"]["flags"]
            for row in all_axes
        )
        == 0
    )
    assert scene["backer_diagnostic_bolt_axes"] == []
    assert inventory["backer_head_washer_envelopes"] == 0
    assert {row["role"] for row in scene["rail_head_washer_envelopes"]} == {
        "rail_head",
        "rail_washer",
    }
    assert {row["role"] for row in scene["other_head_washer_envelopes"]} == {
        "joint_head",
        "joint_washer",
    }
    assert scene["backer_head_washer_envelopes"] == []
    assert (
        scene["backer_attachment"]["status"] == "not_applicable_integrated_center_posts"
    )
    assert len(scene["integrated_center_joint_trial"]["stations"]) == 4
    assert (
        scene["integrated_center_joint_trial"]["nominal_geometry_disposition"]
        == "CLASH"
    )
    assert scene["integrated_center_joint_trial"][
        "candidate_to_inherited_service_void_hits_mm3"
    ]
    assert scene["integrated_center_joint_trial"][
        "driver_to_header_after_pocket_hits_mm3"
    ]
    assert (
        scene["integrated_center_joint_trial"]["structural_capacity_verified"] is False
    )
    assert inventory["conditional_outer_header_recess_envelopes"] == 12
    assert inventory["fixed_panel_kicker_screw_axes"] == 66
    assert inventory["retained_frame_bolt_axes"] == 12
    assert len(scene["hidden_baseline_visual_names"]) == 184
    assert "base_header" in scene["hidden_baseline_visual_names"]
    header = next(row for row in scene["solids"] if row["role"] == "derived_cut_header")
    assert header["name"] == "base_header/derived_outer_header_cut"
    assert header["mesh"]["triangles"]
    cut = scene["outer_header_cut_diagnostics"]
    assert cut["source_member"] == "base_header"
    assert cut["counterbore_count"] == 4
    assert cut["machine_bore_count"] == 4
    assert cut["connected_solid_count"] == 1
    assert cut["cut_is_valid"] is True
    assert 0 < cut["cut_volume_mm3"] < cut["uncut_volume_mm3"]
    assert cut["minimum_modeled_radial_edge_residual_mm"] > 0
    assert cut["counterbore_floor_residual_mm"] > 0
    assert cut["net_section_capacity_verified"] is False
    assert cut["disposition"] == "REVISE"
    assert cut["clearance_approved"] is False
    assert scene["rim_first_sequence"]["operational_result"] == "conditional_unverified"
    assert (
        scene["rim_first_sequence"]["temporary_fixed_fastener_removal_required"] is True
    )
    assert {row["source_station"] for row in scene["barrel_nut_envelopes"]} == duties
    assert {row["source_station"] for row in scene["diagnostic_bolt_axes"]} == duties
    assert all(row["mesh"]["triangles"] for row in scene["barrel_nut_envelopes"])
    assert scene["cross_family_physical_clash_stations"] == []
    trial = scene["outer_header_recess_trial"]
    assert trial["forward_row_y_mm"] == outer.VIEWER_HEADER_FORWARD_Y_MM == -85.0
    assert trial["counterbore_depth_mm"] == (
        independent.hardware.WASHER_THICKNESS_SENSITIVITY_MM
        + independent.HEAD_HEIGHT_MM
        + independent.HEAD_BELOW_TOP_MM
    )
    assert trial["counterbore_depth_mm"] == outer.VIEWER_HEADER_RECESS_MM
    assert trial["washer_od_mm"] == independent.WASHER_OD_MM
    assert trial["head_od_mm"] == independent.HEAD_OD_MM
    assert trial["head_height_mm"] == independent.HEAD_HEIGHT_MM
    assert trial["nominal_head_below_header_top_mm"] == independent.HEAD_BELOW_TOP_MM
    assert trial["side_rim_removal_required_for_driver"] is True
    assert trial["actual_rim_removal_verified"] is False
    assert trial["delivered_hardware_verified"] is False
    assert trial["structural_capacity_verified"] is False
    recesses = scene["conditional_outer_header_recess_envelopes"]
    for role in ("recess_head", "recess_washer", "recess_counterbore"):
        assert sum(row["role"] == role for row in recesses) == 4
    counterbores = [row for row in recesses if row["role"] == "recess_counterbore"]
    assert {row["source_station"] for row in counterbores} == {
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    }
    assert all(
        sum(row["source_station"] == station for row in counterbores) == 2
        for station in (
            "clip_timber_header_outer_left",
            "clip_timber_header_outer_right",
        )
    )
    assert all(row["mesh"]["triangles"] for row in recesses)
    assert all(
        scene[key] is False
        for key in (
            "layout_clearance_approved",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )
