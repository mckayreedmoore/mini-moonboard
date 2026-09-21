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


def test_one_corrective_pose_resolves_only_the_trial_alignment(result):
    assert result["pose_count"] == 2
    assert result["corrective_pose_count"] == 1
    initial, corrective = result["poses"]
    assert initial["name"] == "initial_centered_two_receiver_row"
    assert initial["trial_thread_alignment_matches"] is False
    assert initial["geometry_clear_under_unverified_trial_dimensions"] is False
    assert corrective["name"] == "corrective_diagonal_receiver_row"
    assert corrective["trial_thread_alignment_matches"] is True
    assert corrective["geometry_clear_under_unverified_trial_dimensions"] is True
    assert corrective["actual_801914_geometry_clear"] is None
    assert corrective["machine_bore_surface_gap_mm"] > 0
    assert corrective["barrel_body_surface_gap_mm"] > 0
    for fastener in corrective["fasteners"]:
        assert fastener["machine_bolt"]["wood_path"]["contained_within_1_mm3"]
        assert fastener["receiver"]["body_path"]["contained_within_1_mm3"]
        assert fastener["receiver"]["machine_bore_intersection_mm3"] > 0
        assert fastener["machine_bolt"]["protected_axis_clashes_mm3"] == {}
        assert fastener["receiver"]["protected_axis_clashes_mm3"] == {}
        assert fastener["receiver"]["loaded_barrel_length_mm"] is None
        assert fastener["receiver"]["thread_minor_diameter_mm"] is None


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


def test_screen_stops_before_strength_or_drilling_claim(result):
    limits = result["method_limits"]
    decision = result["decision"]
    assert limits["pb01_archived_corner_block_reactions_transferred"] is False
    assert limits["pb01_named_scenarios_reanalyzed_for_changed_topology"] is False
    assert limits["awc_tr12_barrel_anchorage_rating_claimed"] is False
    assert limits["usda_fpl_rp_586_load_values_scaled_to_furniture_barrel"] is False
    assert limits["complete_joint_utilization"] is None
    assert result["connection_mechanism"]["friction_credited"] is False
    assert result["connection_mechanism"]["locating_or_shear_pin_credited"] is False
    assert decision["cd01"] == "hold_before_CD-02"
    assert decision["structural_verdict"] is None
    assert decision["hardware_selected"] is False
    assert decision["fabrication_or_drilling_released"] is False
