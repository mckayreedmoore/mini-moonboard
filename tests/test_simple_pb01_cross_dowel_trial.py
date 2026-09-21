"""CD-01 direct cross-dowel geometry and claim-boundary checks."""

import pytest

from scripts.simple_pb01_cross_dowel_trial import screen


@pytest.fixture(scope="module")
def result():
    return screen()


def test_exact_retail_lead_keeps_public_facts_separate_from_unknowns(result):
    lead = result["retailer_lead"]
    facts = lead["controlled_public_fields"]
    assert (lead["model"], lead["internet_number"]) == ("801914", "204276112")
    assert facts["internal_thread"] == "1/4-20"
    assert facts["material_description"] == "zinc plated steel"
    assert facts["package_quantity"] == 4
    assert facts["displayed_package_price_usd"] == pytest.approx(5.98)
    assert facts["connector_bolt_included"] is False
    assert lead["manufacturer_contacted"] is False
    assert len(lead["not_publicly_controlled"]) == 7
    assert result["cost_and_assembly"]["barrel_consumed_cost_usd"] == pytest.approx(
        2.99
    )
    assert result["cost_and_assembly"]["direct_complete_cost_usd"] is None
    dimensioned = result["dimensioned_retail_lead"]
    assert (dimensioned["model"], dimensioned["internet_number"]) == (
        "817828",
        "204281673",
    )
    assert dimensioned["public_length_mm"] == 16
    assert dimensioned["trial_length_matches_public_title"]
    assert not dimensioned["outside_diameter_thread_axis_and_metal_basis_verified"]


def test_one_recessed_centered_pose_keeps_insertion_and_thread_offset_separate(result):
    assert result["pose_count"] == 1
    pose = result["poses"][0]
    assert pose["name"] == "recessed_centered_receiver_pair"
    assert pose["geometry_clear_under_unverified_trial_dimensions"] is True
    assert pose["actual_801914_geometry_clear"] is None
    assert pose["machine_bore_surface_gap_mm"] == pytest.approx(37.5)
    assert pose["barrel_body_surface_gap_mm"] == pytest.approx(35.0)
    assert pose["barrel_cross_bore_surface_gap_mm"] == pytest.approx(35.0)

    trial = result["diagnostic_hardware_sensitivity_not_801914_dimensions"]
    assert trial["barrel_insertion_depth_mm"] == pytest.approx(11.05)
    assert trial["barrel_length_mm"] == pytest.approx(16.0)
    assert trial["thread_axis_from_barrel_end_mm"] == pytest.approx(8.0)
    assert trial["bolt_depth_from_timber_face_mm"] == pytest.approx(19.05)
    assert trial["barrel_insertion_depth_mm"] + trial["barrel_length_mm"] == (
        pytest.approx(27.05)
    )
    assert trial["machine_bolt_trial_under_head_length_mm"] == pytest.approx(127.0)

    for fastener in pose["fasteners"]:
        assert fastener["machine_bolt"]["wood_path"]["contained_within_1_mm3"]
        assert fastener["receiver"]["body_path"]["contained_within_1_mm3"]
        assert fastener["receiver"]["cross_bore_path"]["contained_within_1_mm3"]
        assert fastener["receiver"]["machine_bore_intersection_mm3"] > 0
        assert fastener["machine_bolt"]["protected_axis_clashes_mm3"] == {}
        assert fastener["receiver"]["protected_axis_clashes_mm3"] == {}
        assert fastener["receiver"]["cross_bore_protected_axis_clashes_mm3"] == {}
        receiver = fastener["receiver"]
        assert receiver["barrel_insertion_depth_mm"] == pytest.approx(11.05)
        assert receiver["thread_axis_from_barrel_end_mm"] == pytest.approx(8.0)
        assert receiver["bolt_depth_from_timber_face_mm"] == pytest.approx(19.05)
        assert receiver["trial_wood_beyond_body_at_opposite_t_face_mm"] == (
            pytest.approx(11.05)
        )
        assert receiver["nominal_metal_beyond_thread_major_radius_mm"] == (
            pytest.approx([4.825, 4.825])
        )
        assert fastener["receiver"]["loaded_barrel_length_mm"] is None
        assert fastener["receiver"]["thread_engagement_length_mm"] is None
        assert fastener["receiver"]["effective_thread_engagement_mm"] is None
        assert fastener["receiver"]["thread_minor_diameter_mm"] is None
        assert fastener["receiver"]["barrel_bore_clearance_mm"] is None
        assert fastener["receiver"]["barrel_alignment_method_verified"] is False
        assert fastener["receiver"]["barrel_depth_stop_or_support_verified"] is False
        assert fastener["receiver"]["barrel_removal_method_verified"] is False
        assert fastener["receiver"]["bottoming_clearance_verified"] is False


def test_complete_bolt_reach_and_purchased_screw_envelopes_are_conditional(result):
    pose = result["poses"][0]
    basis = result["purchased_hillman_envelope_basis"]
    assert basis["axis_count"] == 66
    assert basis["length_mm"] == pytest.approx(63.5)
    assert basis["physical_clearance_accepted"] is False
    for fastener in pose["fasteners"]:
        bolt = fastener["machine_bolt"]
        assert bolt["trial_under_head_axis_to_tip_mm_excluding_head_washer"] == (
            pytest.approx(127.0)
        )
        assert bolt["trial_tip_beyond_thread_axis_mm"] == pytest.approx(18.9)
        assert bolt["trial_tip_beyond_barrel_far_surface_mm"] == pytest.approx(13.9)
        purchased = fastener["purchased_hillman_screen"]
        assert purchased["axis_count"] == 66
        assert purchased["clashes_mm3"] == {
            "nominal_head_diameter_full_length": {},
            "nominal_plus_1mm_radial_sensitivity": {},
        }


def test_direct_pose_preserves_pb01_reference_and_complete_axis_inventory(result):
    assert result["fixed_panel_and_kicker_axes_checked"] == 66
    assert result["meeting_surface"]["butt_plane_x_mm"] == pytest.approx(89.05)
    assert result["meeting_surface"]["rail_section_t_by_n_mm"] == pytest.approx(
        [38.1, 139.7]
    )
    reference = result["reference_six_inch_corner_block"]
    assert reference["size_x_t_n_mm"] == [139.7, 57.15, 152.4]
    assert reference["gross_volume_mm3"] == pytest.approx(1_216_739.502)
    assert reference["bolt_count"] == 4
    assert result["comparison_duties"] == {
        "retained_scenario_names": ["a12-left", "k12-right"],
        "changed_topology_demands": None,
        "corner_block_local_actions_reused": False,
        "status": "names retained for a later CD-02 analysis only",
    }
    assert result["direct_joint_inventory"]["added_wood_volume_mm3"] == 0
    assert result["direct_joint_inventory"]["cross_dowels"] == 2
    assert result["direct_joint_inventory"]["machine_bolts"] == 2
    assert result["direct_joint_inventory"]["longest_aligned_wood_path_mm"] == (
        pytest.approx(108.1)
    )
    comparison = result["inventory_comparison"]
    assert comparison["recessed_cross_dowel"]["main_bolts"] == 2
    assert comparison["six_inch_corner_block"]["main_bolts"] == 4
    assert comparison["six_inch_corner_block"]["added_wood_volume_mm3"] == (
        pytest.approx(1_216_739.502)
    )
    assert comparison["mechanically_preferable_option"] is None


def test_screen_stops_before_strength_or_drilling_claim(result):
    limits = result["method_limits"]
    decision = result["decision"]
    assert limits["pb01_archived_corner_block_reactions_transferred"] is False
    assert limits["pb01_named_scenarios_reanalyzed_for_changed_topology"] is False
    assert limits["awc_tr12_barrel_anchorage_rating_claimed"] is False
    assert limits["usda_fpl_rp_586_load_values_scaled_to_furniture_barrel"] is False
    assert limits["complete_joint_utilization"] is None
    assert limits["purchased_hillman_physical_clearance_accepted"] is False
    assert result["connection_mechanism"]["friction_credited"] is False
    assert result["connection_mechanism"]["locating_or_shear_pin_credited"] is False
    assert decision["cd01"] == "hold_before_CD-02"
    assert decision["structural_verdict"] is None
    assert decision["hardware_selected"] is False
    assert decision["fabrication_or_drilling_released"] is False
