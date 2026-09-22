"""Detached, layout-only bottom-center pair at the original same-side corners."""

import pytest

from scripts import owner_layout_bottom_center_pair as trial


@pytest.fixture(scope="module")
def report():
    return trial.screen()


def test_source_duties_and_protected_axes_are_explicit(report):
    assert report["stations"] == list(trial.STATIONS)
    assert report["target_duty_members"] == {
        trial.STATIONS[0]: ["base_rail_bottom_left", "base_principal_center_left"],
        trial.STATIONS[1]: ["base_rail_bottom_right", "base_principal_center_right"],
    }
    assert report["approved_post_centers_x_mm"] == [-180.0, 180.0]
    assert report["inventory"] == {
        "candidate_blocks": 2,
        "candidate_through_bolts": 8,
        "target_legacy_sds": 12,
        "other_legacy_sds": 132,
        "retained_frame_bolts": 12,
        "fixed_panel_kicker_axes": 66,
    }
    assert report["block_local_n_mm"] == 139.7
    assert report["finite_protected_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert not report["native_solve"]
    assert not report["drilling_released"]
    assert not report["structural_released"]


def test_left_bore_and_right_cleat_are_physically_screened_not_accepted(report):
    assert report["decision"] == "REVISE"
    for row in report["pairs"].values():
        assert row["contact_area_mm2"]["rail"] > 0
        assert row["contact_area_mm2"]["principal"] > 0
        assert len(row["complete_bores_by_bolt"]) == 4
        assert len(row["bolt_paths"]) == 4
        assert sorted(
            {path["wood_grip_mm"] for path in row["bolt_paths"].values()}
        ) == pytest.approx([95.25, 177.8])
        assert row["block_side_cleat_hit_mm3"] == 0
        assert not row["protected_axis_hits_mm3"]
        assert not row["generic_tool_host_hits_mm3"]
        assert row["finite_protected_hits"]["block"]
    left, right = (report["pairs"][name] for name in trial.STATIONS)
    assert left["complete_bores_by_bolt"]["owner_bottom_left_rail_2"] is False
    assert (
        left["bore_host_volume_fraction"]["owner_bottom_left_rail_2"][
            "base_rail_bottom_left"
        ]
        == 0
    )
    assert report["binding_constraints"][trial.STATIONS[0]]["incomplete_bores"] == [
        "owner_bottom_left_rail_2"
    ]
    assert all(right["complete_bores_by_bolt"].values())
    assert left["finite_protected_hits"]["block"]["tnuts"] == {
        "hold_tnut_main_E1": pytest.approx(736.888367)
    }
    assert right["finite_protected_hits"]["block"]["tnuts"] == {
        "hold_tnut_main_G1": pytest.approx(804.105091)
    }


def test_unmodeled_installed_protection_is_not_accepted(report):
    assert all(
        gate == {"status": "UNVERIFIED", "clearance_mm": None}
        for gate in report["protected_3d_gates"].values()
    )
    assert not report["backer_frame_attachment_qualified"]
    assert not report["whole_frame_qualified"]
