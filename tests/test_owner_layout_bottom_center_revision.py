"""One source-distinct bottom-center owner-layout revision; no release."""

import pytest

from scripts import owner_layout_bottom_center_pair as first
from scripts import owner_layout_bottom_center_revision as revision


@pytest.fixture(scope="module")
def report():
    return revision.screen()


def test_revision_is_one_bounded_pose_and_preserves_original_source():
    assert first.SOURCE_ID != revision.SOURCE_ID
    assert first.BLOCK_X_MM == 139.7
    assert first.RAIL_X_MM == (50.0, 85.0)
    assert revision.BLOCK_X_MM == 77.0
    assert revision.RAIL_X_MM == (26.0, 51.0)
    assert first.BLOCK_N_MM == 139.7


def test_revision_preserves_fixed_axes_and_reports_actual_clearance(report):
    assert report["source_id"] == revision.SOURCE_ID
    assert report["block_local_n_mm"] == 139.7
    assert report["rail_x_offsets_from_butt_mm"] == [26.0, 51.0]
    assert report["approved_post_centers_x_mm"] == [-180.0, 180.0]
    assert report["inventory"]["fixed_panel_kicker_axes"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["inventory"]["target_legacy_sds"] == 12
    assert report["revision_basis"][
        "right_G1_flange_nominal_x_gap_mm"
    ] == pytest.approx(2.05)
    assert report["revision_basis"]["nominal_far_rail_bolt_end_distance_mm"] == 26.0
    assert not report["revision_basis"]["tolerance_and_load_direction_verified"]
    assert not report["native_solve"]
    assert not report["drilling_released"]
    assert not report["structural_released"]


def test_revision_checks_both_hosts_and_protected_solids(report):
    # Clean block placement is insufficient: installed tools remain a revise gate.
    assert report["decision"] == "REVISE"
    for name in first.STATIONS:
        row = report["pairs"][name]
        assert row["block_dimensions_mm"] == [77.0, 57.15, 139.7]
        assert row["contact_area_mm2"]["rail"] > 0
        assert row["contact_area_mm2"]["principal"] > 0
        assert all(row["complete_bores_by_bolt"].values())
        assert row["block_side_cleat_hit_mm3"] == 0
        assert not row["protected_axis_hits_mm3"]
        assert not row["other_timber_hits_mm3"]
        assert not row["finite_protected_hits"].get("block")
    right_hits = report["pairs"][first.STATIONS[1]]["finite_protected_hits"]
    for feature in (
        "stack/owner_bottom_right_principal_1/nut",
        "tool/owner_bottom_right_principal_1/far",
    ):
        assert (
            right_hits[feature]["hold_hole_and_trial_projection"]["hold_tnut_main_G1"]
            > 0
        )
    assert (
        report["protected_3d_gates"]["delivered_hold_bolt_length"]["status"]
        == "UNVERIFIED"
    )


def test_right_principal_tool_has_no_one_mm_reserve_two_row_pose():
    gate = revision.principal_tool_reserve_gate()
    assert gate["source_id"] == revision.SOURCE_ID
    assert gate["assumed_tool_diameter_mm"] == 40.0
    assert gate["max_separated_t_mm"] == pytest.approx(23.35)
    assert gate["nominal_low_n_interval_width_mm"] == pytest.approx(0.212536, abs=1e-5)
    assert gate["nominal_high_n_interval_width_mm"] == pytest.approx(
        17.112536, abs=1e-5
    )
    assert gate["two_rows_with_1mm_extra_end_reserve"] is False
    assert gate["disposition"] == "REVISE_TOOL_OR_TOPOLOGY"
