"""Owner-directed two-vertical-bolt center probe stays bounded and fail-closed."""

import pytest

from scripts import owner_barrel_vertical_center_probe as probe


@pytest.fixture(scope="module")
def report():
    return probe.build_report()


def test_full_posts_clear_kick_tnuts_under_explicit_provisional_stack(report):
    layout = report["post_layout"]
    assert layout["kick_tnut_centers_x_mm"] == {
        "left": pytest.approx(-124.96),
        "right": pytest.approx(123.6),
    }
    assert layout["moved_post_bounds_xyz_mm"] == {
        "base_post_center_left": pytest.approx(
            [-239.26, -150.36, -175.7, -36.0, 0.0, 238.9]
        ),
        "base_post_center_right": pytest.approx(
            [149.0, 237.9, -175.7, -36.0, 0.0, 238.9]
        ),
    }
    stack = layout["provisional_tolerance_stack_mm"]
    assert layout["nominal_post_to_tnut_flange_clearance_mm"] == pytest.approx(12.7)
    assert stack["total_consumed"] == pytest.approx(5.0)
    assert stack["remaining_clearance"] == pytest.approx(7.7)
    assert stack["status"] == "PROVISIONAL_NOT_CONTROLLED"
    assert not report["checks"]["moved_post_protected_hits_mm3"]
    literal = layout["literal_tnut_centered_full_post"]
    assert literal["status"] == "REJECTED_NOMINAL_WITHOUT_RELIEF"
    assert literal["right_driver_overlap_mm"] == pytest.approx(0.85)
    assert literal["right_selected_max_washer_overlap_mm"] == pytest.approx(0.3623)


def test_only_four_center_kicker_screws_move_and_enter_new_posts(report):
    screws = report["panel_screws"]
    assert screws["source_count"] == 66
    assert screws["unchanged_count"] == 62
    assert screws["relocated_count"] == 4
    assert set(screws["relocated_names"]) == probe.CENTER_SCREWS
    assert all(row["embedded_shaft_outside_post_mm3"] == 0 for row in screws["rows"])
    assert all(row["nominal_nearest_post_edge_mm"] == 19.05 for row in screws["rows"])
    assert all(
        row["adverse_provisional_post_edge_mm"] == pytest.approx(14.55)
        for row in screws["rows"]
    )
    assert sorted({row["new_start_xyz_mm"][0] for row in screws["rows"]}) == (
        pytest.approx([-169.41, 168.05])
    )


def test_shallow_backers_keep_both_kicker_seam_edges_continuously_supported(report):
    layout = report["post_layout"]
    assert layout["seam_backer_bounds_xyz_mm"] == {
        "kicker_seam_backer_left": pytest.approx(
            [-39.6875, -1.5875, -124.9, -36.0, 0.0, 238.9]
        ),
        "kicker_seam_backer_right": pytest.approx(
            [-1.5875, 36.5125, -124.9, -36.0, 0.0, 238.9]
        ),
    }
    assert not report["checks"]["seam_backer_protected_hits_mm3"]
    for side in ("left", "right"):
        row = report["checks"]["seam_backing"][side]
        assert row["backer_full_height_samples"]
        assert row["header_continuation_samples"]
        assert row["nominal_panel_contact_area_mm2"] == pytest.approx(9102.09)


def test_each_principal_gets_two_selected_vertical_barrel_rows(report):
    joint = report["principal_header_joint"]
    assert joint["hardware"] == {
        "barrel_product": "JCD14201606NL ZN",
        "barrel_od_mm": pytest.approx(10.0076),
        "barrel_length_mm": pytest.approx(16.002),
        "barrel_axis_from_slotted_end_mm": pytest.approx(5.9944),
        "bolt_product": "1456BHT5",
        "bolt_nominal_length_mm": pytest.approx(88.9),
        "bolt_adverse_length_range_mm": pytest.approx([87.376, 89.916]),
        "washer_product": "33857",
        "washer_max_od_mm": pytest.approx(19.0246),
        "washer_max_thickness_mm": pytest.approx(2.032),
    }
    assert len(joint["records"]) == 4
    assert joint["barrel_pair_axis_pitch_mm"] > 23
    assert joint["barrel_pair_clear_wood_between_bores_mm"] > 13
    assert joint["header_clear_wood_between_bolt_bores_mm"] > 15
    assert joint["balanced_max_washer_reserve_mm"] > 4
    assert joint["driver_edge_reserve_mm"] > 3
    for row in joint["records"]:
        assert row["bolt_axis_xyz"] == [0.0, 0.0, 1.0]
        assert row["bolt_seat_xyz_mm"][2] == pytest.approx(238.9)
        assert row["thread_axis_xyz_mm"][2] == pytest.approx(305.0)
        assert row["barrel_axis_xyz"] in ([-1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert row["selected_barrel_recess_mm"] == pytest.approx(13.0556)
        assert row["selected_barrel_bore_depth_mm"] == pytest.approx(29.0576)
        assert row["wood_beyond_barrel_bore_mm"] == pytest.approx(9.0424)
        assert row["minimum_bolt_tip_past_thread_axis_mm"] == pytest.approx(19.244)
        assert row["minimum_complete_thread_endpoint_past_axis_mm"] == pytest.approx(
            16.704
        )
        assert row["barrel_x_edge_ligament_mm"] == pytest.approx(14.0462)
        assert row["barrel_local_tn_edge_ligament_mm"] > 0
    assert report["candidate_inventory_delta"] == {
        "barrel_pairs": {"current": 46, "proposed": 48},
        "JCD14201606NL ZN": {"current": 46, "proposed": 48},
        "Fastenal 33857": {"current": 46, "proposed": 48},
        "CDE 1456BHT5": {"current": 4, "proposed": 8},
        "CDE 1472BHT5": {"current": 26, "proposed": 24},
        "basis": (
            "Replace two current 4.5-in single angled principal/header bolts "
            "with four selected 3.5-in vertical bolts."
        ),
    }


def test_all_nominal_interactions_and_combined_cuts_are_clear(report):
    checks = report["checks"]
    assert checks["geometry_clear"]
    for key in (
        "protected_hardware_hits_mm3",
        "unrelated_wood_hits_mm3",
        "candidate_service_void_hits_mm3",
        "peer_role_hits_mm3",
        "intended_path_outside_hosts_mm3",
    ):
        assert not checks[key]
    combined = checks["combined_cut_members"]
    assert set(combined) == {
        "base_header",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    assert combined["base_header"]["candidate_cut_count"] == 4
    assert combined["base_principal_center_left"]["candidate_cut_count"] == 4
    assert combined["base_principal_center_right"]["candidate_cut_count"] == 4
    assert all(row["valid"] and row["solid_count"] == 1 for row in combined.values())
    assert all(row["removed_volume_mm3"] > 0 for row in combined.values())


def test_result_stays_fail_closed_without_physical_evidence(report):
    assert report["native_solve_run"] is False
    decision = report["decision"]
    assert decision["nominal_and_provisional_tolerance_geometry"] == "CANDIDATE"
    assert decision["complete_joint"] == "EVIDENCE_BLOCKED"
    assert decision["diy_ready"] is False
    assert decision["drilling_released"] is False
    assert decision["fabrication_released"] is False
    assert decision["structural_released"] is False
    assert len(decision["blocking_gates"]) == 6
