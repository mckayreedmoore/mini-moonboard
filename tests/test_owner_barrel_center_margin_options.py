"""Nominal source-CAD screens for the bounded center joint margin option."""

import pytest

from scripts import owner_barrel_center_margin_options as options


@pytest.fixture(scope="module")
def trial():
    return options.build()


def test_source_bound_broad_face_pose_preserves_fixed_model_and_is_unreleased(trial):
    assert trial["protected_counts"]["panel_screws"] == 66
    assert trial["protected_counts"]["frame_bolts"] == 12
    assert trial["native_solve"] is False
    assert not any(trial["release_flags"].values())
    assert trial["baseline"]["barrel_recess_mm"] == pytest.approx(1.049)
    rows = trial["broad_face_option"]["rows"]
    assert len(rows) == 4
    assert all(
        row["entry_face"] == "principal_rear_broad_face" for row in rows.values()
    )
    assert all(row["bolt_entry_face"] == "header_rear_recess" for row in rows.values())


def test_candidate_meets_finite_envelope_targets_without_reported_clashes(trial):
    option = trial["broad_face_option"]
    assert option["minimum_barrel_recess_mm"] >= 3
    assert option["minimum_tool_path_gap_mm"] >= 2
    assert option["minimum_principal_pair_tool_gap_mm"] >= 2
    assert option["minimum_head_pocket_pair_gap_mm"] > 0
    assert option["minimum_barrel_recess_mm"] == pytest.approx(31.189399)
    assert option["minimum_tool_path_gap_mm"] == pytest.approx(4.003358)
    assert option["minimum_head_pocket_header_edge_mm"] == pytest.approx(0.090167)
    assert option["maximum_barrel_mouth_x_side_breakout_mm"] == pytest.approx(3.45)
    assert option["minimum_barrel_radial_x_ligament_mm"] == pytest.approx(2.0462)
    assert option["barrel_x_ligament_structural_sizing_required"] is True
    assert option["net_section_unqualified"] is True
    assert (
        option["nominal_geometry_disposition"]
        == "NOMINAL_TARGETS_ONLY_NET_SECTION_UNQUALIFIED"
    )
    assert not option["installed_hardware_pair_hits_mm3"]
    assert not option["tool_to_other_hardware_hits_mm3"]
    assert not option["tool_pair_hits_mm3"]
    assert not option["shape_failures"]
    for row in option["rows"].values():
        assert row["modeled_bore_depth_past_nominal_tip_mm"] == 4
        assert row["tip_extension_in_receiver_fraction"] > 0.999
        assert row["joined_wood_bore_core_fraction"] > 0.999
        assert row["barrel_body_in_host_fraction"] > 0.999
        assert row["barrel_cross_bore_in_host_fraction"] > 0.997
        assert row["barrel_cross_bore_past_entry_1mm_in_host_fraction"] > 0.999
        assert row["barrel_radial_x_edge_ligament_mm"] > 0
        assert row["unrelieved_barrel_tool_host_intrusion_mm3"] > 50
        assert row["barrel_tool_residual_host_mm3"] == 0
        assert row["bolt_barrel_intersection_mm3"] > 0
        assert not row["protected_hits_mm3"]
        assert not row["unrelated_wood_hits_mm3"]
        assert not row["retained_hardware_hits_mm3"]
        assert not row["inherited_service_cutter_hits_mm3"]
        assert row["driver_residual_header_mm3"] == 0
        assert row["head_pocket_in_principal_mm3"] == 0
        assert row["head_washer_inside_header_fraction"] == {
            "head": 1.0,
            "washer": 1.0,
        }
        assert row["head_pocket_header_bottom_margin_mm"] > 0
        assert row["head_pocket_header_top_margin_mm"] > 0
        assert not row["tip_extension_unrelated_wood_hits_mm3"]
        assert not row["tip_extension_protected_hits_mm3"]


def test_common_five_in_second_bolt_is_reported_conditionally(trial):
    option = trial["common_5_in_second_row"]
    assert len(option["rows"]) == 4
    assert all(row["bolt_length_mm"] == 127 for row in option["rows"].values())
    assert (
        option["nominal_geometry_disposition"]
        == "NOMINAL_TARGETS_ONLY_NET_SECTION_UNQUALIFIED"
    )
    assert all(
        row["modeled_bore_depth_past_nominal_tip_mm"] == 4
        for row in option["rows"].values()
    )
    assert all(
        not row["complete_thread_engagement_verified"]
        for row in option["rows"].values()
    )


def test_shallow_seat_recovers_header_edge_but_fails_full_head_washer_support(trial):
    for key in ("shallow_seat_option", "shallow_common_5_in"):
        option = trial[key]
        assert option["header_seat_depth_mm"] == 7.5
        assert option["thread_depth_from_seat_mm"] == 108.0
        assert option["minimum_barrel_recess_mm"] == pytest.approx(29.25367)
        assert option["minimum_tool_path_gap_mm"] == pytest.approx(4.003358)
        assert option["minimum_head_pocket_header_edge_mm"] == pytest.approx(3.090167)
        assert option["minimum_barrel_radial_x_ligament_mm"] == pytest.approx(2.0462)
        assert option["barrel_x_ligament_structural_sizing_required"] is True
        assert option["nominal_geometry_disposition"] == "CLASH"
        assert not option["installed_hardware_pair_hits_mm3"]
        assert not option["tool_to_other_hardware_hits_mm3"]
        assert not option["tool_pair_hits_mm3"]
        for row in option["rows"].values():
            assert row["head_washer_inside_header_fraction"] == {
                "head": pytest.approx(0.795042),
                "washer": pytest.approx(0.799113),
            }
            assert row["driver_residual_header_mm3"] == 0
            assert row["barrel_tool_residual_host_mm3"] == 0
            assert row["tip_extension_in_receiver_fraction"] == 1
            assert row["joined_wood_bore_core_fraction"] == 1
            assert not row["inherited_service_cutter_hits_mm3"]
            assert not row["protected_hits_mm3"]
            assert not row["retained_hardware_hits_mm3"]
            assert not row["unrelated_wood_hits_mm3"]
    assert trial["shallow_seat_option"]["rows"][
        "barrel_center_clip_split_base_center_right_2"
    ]["nominal_tip_beyond_barrel_far_wall_mm"] == pytest.approx(-0.3548)
    assert trial["shallow_common_5_in"]["rows"][
        "barrel_center_clip_split_base_center_right_2"
    ]["nominal_tip_beyond_barrel_far_wall_mm"] == pytest.approx(12.3452)


def test_bounded_offset_sensitivity_is_not_misreported_as_collision_screen(trial):
    offsets = trial["offset_sensitivity"]
    assert offsets["11.0"]["nominal_parallel_bolt_tool_gap_mm"] == pytest.approx(
        2.003665, abs=1e-5
    )
    assert offsets["11.0"]["barrel_radial_x_ligament_mm"] == pytest.approx(3.0462)
    assert offsets["13.0"]["barrel_radial_x_ligament_mm"] == pytest.approx(1.0462)
    assert offsets["13.0"]["nominal_parallel_bolt_tool_gap_mm"] > 6
    assert offsets["11.0"]["full_collision_rescreened"] is False
    assert offsets["12.0"]["full_collision_rescreened"] is True
    assert offsets["13.0"]["full_collision_rescreened"] is False
