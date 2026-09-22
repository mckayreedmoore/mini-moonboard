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
    assert scene["visual_wood_replacement"]["center_trial_cuts"] == 20
    assert scene["visual_wood_replacement"]["outer_header_barrel_body_cuts"] == 4
    assert scene["visual_wood_replacement"]["center_barrel_body_cuts"] == 6
    assert scene["visual_wood_replacement"]["remaining_trial_cuts"] == 108
    assert (
        scene["visual_wood_replacement"]["candidate_barrel_pairs_with_cut_wood"] == 46
    )
    assert (
        scene["visual_wood_replacement"]["barrel_drilling_paths_without_cut_wood"] == []
    )
    assert scene["visual_wood_replacement"]["barrel_path_host_anomalies"] == []
    assert (
        scene["visual_wood_replacement"]["unrelated_remaining_pair_cut_intersections"]
        == []
    )
    assert (
        len(scene["visual_wood_replacement"]["remaining_pair_cut_intersections"]) == 36
    )
    assert (
        len(
            scene["visual_wood_replacement"]["remaining_to_protected_cut_intersections"]
        )
        == 2
    )
    assert inventory["barrel_nut_envelopes"] == 46
    assert inventory["new_diagnostic_bolt_axes"] == 46
    assert inventory["rail_head_washer_envelopes"] == 40
    assert inventory["other_head_washer_envelopes"] == 44
    assert inventory["backer_attachment_duties"] == 0
    backing = scene["integrated_kicker_backing"]
    assert backing["status"] == "geometric_receiver_and_post_header_path_only"
    assert backing["fixed_center_kicker_screw_count"] == 4
    assert backing["post_header_barrel_pair_count"] == 4
    assert backing["complete_backing_load_path_verified"] is False
    assert inventory["backer_barrel_nut_envelopes"] == 0
    assert inventory["backer_diagnostic_bolt_axes"] == 0
    all_axes = scene["diagnostic_bolt_axes"] + scene["backer_diagnostic_bolt_axes"]
    assert len(all_axes) == 46
    assert all(
        row["nominal_axial"]["thread_engagement"] == "UNKNOWN" for row in all_axes
    )
    assert all(row["nominal_axial"]["tip_past_assumed_axis_mm"] > 0 for row in all_axes)
    assert (
        sum(
            row["nominal_axial"]["partial_thread_comparator_body_overlap_mm"] == 0
            for row in all_axes
        )
        == 0
    )
    assert all(
        row["nominal_axial"]["partial_thread_comparator_end_length_mm"] == 19.05
        for row in all_axes
    )
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
        == "CANDIDATE_ONLY_UNVERIFIED"
    )
    assert (
        scene["integrated_center_joint_trial"]["candidate_service_diameter_mm"] == 25.4
    )
    assert scene["visual_wood_replacement"]["candidate_service_diameter_mm"] == 25.4
    assert scene["integrated_center_joint_trial"]["unverified"][
        "single_connector_moment_transfer_and_stiffness"
    ]
    assert scene["integrated_center_joint_trial"]["unverified"][
        "service_feed_and_strength"
    ]
    for station, row in scene["integrated_center_joint_trial"]["stations"].items():
        expected = 1 if "clip_split_base_center_" in station else 2
        assert len(row["bolts"]) == expected
        assert all(
            not bolt["candidate_service_void_hits_mm3"]
            for bolt in row["bolts"].values()
        )
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
    service = scene["integrated_service_geometry"]
    assert service["source_pair_count"] == 46
    assert service["outer_top_station_count"] == 4
    assert service["rim_sample_count_per_side"] == 33
    assert service["outer_top_nominal_straight_paths_clear"] is True
    assert service["both_rims_sampled_clear_with_retained_modeled_hardware"] is True
    assert service["both_rims_continuous_swept_aabb_clear_of_retained_hardware"] is True
    assert service["both_rims_continuous_swept_aabb_clear_of_other_wood"] is False
    assert service["both_rims_continuous_nominal_model_sweep_clear"] is True
    assert service["all_retained_trial_stacks_include_heads_and_washers"] is True
    assert service["continuous_withdrawal_verified"] is False
    assert service["delivered_hardware_or_tool_verified"] is False
    assert service["barrel_insertion_alignment_extraction_verified"] is False
    assert service["safe_supported_panel_removal_verified"] is False
    assert service["operational_result"] == "continuous_nominal_geometry_only"
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
