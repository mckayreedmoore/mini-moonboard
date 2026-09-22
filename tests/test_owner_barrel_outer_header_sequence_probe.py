"""Rim-first service is a conditional sequence, never a joint qualification."""

import pytest

from scripts.owner_barrel_outer_header_sequence_probe import probe


@pytest.fixture(scope="module")
def result():
    return probe()


def test_connection_graph_requires_actual_rim_attachment_release(result):
    assert result["schema"] == "owner_barrel_outer_header_sequence_probe/v1"
    assert result["width_option"] == "kerf-right"
    assert result["fixed_axis_inventory"] == {
        "panel_kicker_screws": 66,
        "frame_bolts": 12,
    }
    assert result["fixed_axis_coordinates_changed"] is False
    assert result["temporary_fixed_fastener_removal_required"] is True
    for side in ("left", "right"):
        row = result["sides"][side]
        release = row["release_before_rim_withdrawal"]
        assert len(release["fixed_panel_screws"]) == 8
        assert len(release["fixed_frame_bolts"]) == 2
        assert len(release["candidate_barrel_stations"]) == 5
        assert all(f"_{side}_rim_" in name for name in release["fixed_panel_screws"])
        assert release["fixed_frame_bolts"] == [
            f"lumber_leg_bolt_{side}_1",
            f"lumber_leg_bolt_{side}_2",
        ]
        assert row["outer_header_station"] == f"clip_timber_header_outer_{side}"
        assert set(row["outer_header_members"]) == {
            "base_header",
            f"base_post_outer_{side}",
        }
        assert row["outer_header_station"] not in release["candidate_barrel_stations"]
        assert row["side_rim_connected_to_header_station"] is False
        assert (
            row["graph_condition_if_fixed_screws_or_bolts_stay_installed"] == "blocked"
        )
        assert row["graph_condition_if_all_direct_fasteners_released"] == "rim_detached"


def test_sampled_bare_wood_path_is_clear_but_not_a_service_release(result):
    for side in ("left", "right"):
        row = result["sides"][side]
        withdrawal = row["nominal_wood_withdrawal"]
        assert [sample["withdrawal_mm"] for sample in withdrawal["samples"]] == list(
            range(0, 161, 5)
        )
        assert withdrawal["rim_normal_depth_mm"] == pytest.approx(139.7)
        assert withdrawal["last_sample_exceeds_rim_normal_depth"] is True
        assert withdrawal["sampled_wood_clear"] is True
        assert all(
            not sample["other_uncut_wood_hits_mm3"] for sample in withdrawal["samples"]
        )
        assert withdrawal["continuous_sweep_verified"] is False
        assert withdrawal["hardware_and_service_features_verified"] is False
        assert row["operational_result"] == "conditional_unverified"
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_rejects_invalid_sampling_or_changed_connection_inventory():
    with pytest.raises(ValueError, match="Withdrawal samples"):
        probe(samples_mm=(5, 10))
    with pytest.raises(ValueError, match="Withdrawal samples"):
        probe(samples_mm=(0, 10, 10))
