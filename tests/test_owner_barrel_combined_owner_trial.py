"""The two owner-approved frame-hole revisions remain nominally clash-free."""

import pytest

from scripts.owner_barrel_combined_owner_trial import build_trial, report


@pytest.fixture(scope="module")
def trial_report():
    return report()


def test_screen_is_detached_from_maintained_assembly():
    source, trial, moved, extended, tips = build_trial()
    assert len(moved) == 2
    assert len(extended) == len(tips) == 4
    assert trial["wood"] is source["wood"]
    assert trial["panel_connections"] is source["panel_connections"]
    assert trial["frame_connections"] is source["frame_connections"]
    assert trial["bolts"] is not source["bolts"]
    assert trial["drilling_paths"] is not source["drilling_paths"]
    assert all(trial["bolts"][name] == source["bolts"][name] for name in moved)
    assert all(
        trial["drilling_paths"][name] == source["drilling_paths"][name]
        for name in extended
    )
    assert not any(trial["release_flags"].values())


def test_whole_assembly_trial_keeps_all_connections(trial_report):
    assert trial_report["whole_cut_barrel_pairs"] == 46
    assert trial_report["whole_cut_missing_paths"] == []
    assert trial_report["whole_cut_path_host_anomalies"] == []
    assert trial_report["source_wood_panel_frame_release_unchanged"] is True
    assert trial_report["first_row_trial_n_mm"] == 42.0
    assert trial_report["extension_mm"] == 2.0
    assert len(trial_report["moved_first_row_drilling_paths"]) == 4
    assert len(trial_report["changed_drilling_paths_checked"]) == 8
    assert (
        sum(
            path.endswith("/barrel_bore")
            for path in trial_report["changed_drilling_paths_checked"]
        )
        == 2
    )
    assert len(trial_report["top_tip_clearance_mm"]) == 4
    assert set(trial_report["top_tip_clearance_mm"].values()) == {2.0}


def test_candidate_clearances_are_not_a_release(trial_report):
    assert all(not rows for rows in trial_report["changed_cut_intersections"].values())
    assert all(
        not hits for hits in trial_report["incremental_top_tip_protected_hits"].values()
    )
    assert all(
        not hits
        for hits in trial_report["incremental_top_tip_other_wood_hits"].values()
    )
    assert all(
        fraction == 1.0
        for fraction in trial_report["incremental_top_tip_receiver_coverage"].values()
    )
    assert trial_report["maintained_scene_changed"] is True
    assert trial_report["owner_approval_pending"] is False
    assert trial_report["structural_released"] is False
    assert trial_report["drilling_released"] is False
    assert trial_report["fabrication_released"] is False
