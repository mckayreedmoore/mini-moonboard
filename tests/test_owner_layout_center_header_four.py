"""Four direct center-header duties in the approved ±180 mm post pose."""

import pytest

from scripts import owner_layout_center_header_four as trial


@pytest.fixture(scope="module")
def result():
    return trial.screen()


def test_exact_duties_and_owner_pose(result):
    assert set(result["stations"]) == set(trial.STATIONS)
    assert result["post_centers_x_mm"] == {"left": -180.0, "right": 180.0}
    assert result["inventory"]["candidate_blocks"] == 4
    assert result["inventory"]["candidate_bolts"] == 16
    assert result["inventory"]["removed_target_sds_axes"] == 24
    assert result["inventory"]["fixed_panel_kicker_axes"] == 66
    assert result["inventory"]["retained_frame_bolt_axes"] == 12
    assert result["source_preserved"]


def test_direct_joint_topology_without_backer_structural_credit(result):
    assert result["direct_paths"] == {
        "header_to_post_left": ["base_header", "base_post_center_left"],
        "header_to_post_right": ["base_header", "base_post_center_right"],
        "header_to_principal_left": ["base_header", "base_principal_center_left"],
        "header_to_principal_right": ["base_header", "base_principal_center_right"],
    }
    assert result["backer_frame_attachment_qualified"] is False
    assert result["backers_receive_four_fixed_kicker_screws"]
    assert not result["pb02_rear_return_chain_used"]
    assert not result["native_solve"]
    assert not result["drilling_released"]
    assert not result["structural_released"]


def test_contact_bores_and_obstruction_disposition_are_explicit(result):
    for row in result["stations"].values():
        assert row["post_or_principal_contact_mm2"] > 0
        assert row["header_contact_mm2"] > 0
        assert len(row["bore_coverage"]) == 4
    if result["decision"] == "REVISE_LAYOUT":
        assert result["exact_obstructions"]
        assert result["needed_owner_exception"] is not None
    else:
        assert result["decision"] == "LAYOUT_ONLY_CLEAR"
        assert not result["exact_obstructions"]
        assert result["needed_owner_exception"] is None


def test_same_side_principal_tool_access_clears_nominal_installed_stacks(result):
    for station in ("clip_split_base_center_left", "clip_split_base_center_right"):
        hits = result["exact_obstructions"].get(station, {})
        assert not any(key.startswith("tool_host/") for key in hits)
        assert not any(key.startswith("tool_to_other_installed/") for key in hits)
