"""Bounded PB-02 tolerance pose search."""

from scripts.simple_center_tolerance_pose_probe import Pose, evaluate, search


def test_search_reports_fixed_axes_and_a_reviewable_best_pose():
    result = search()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["tested_poses"]
    assert result["best_pose"] in result["tested_poses"]
    assert result["target_margin_feasible_in_tested_set"] is True
    best = result["tested_poses"][result["best_pose"]]
    assert best["minimum_margin_mm"] == 5.075
    assert best["nominal_geometry"] == "feasible"
    assert len(best["clear_insertion_ends_by_bolt"]) == 8
    assert all(best["clear_insertion_ends_by_bolt"].values())
    assert all(value == 1 for value in best["bore_received_fraction"].values())
    assert all(value == 1 for value in best["washer_bearing_fraction"].values())
    assert best["bore_pair_hits_mm3"] == {}
    assert best["socket_body_wood_hits_mm3"] == {}
    assert best["extension_wood_hits_mm3"]
    assert result["geometry_only"] is True
    assert result["joint_mechanics_verified"] is False
    assert result["rating_or_drilling_release"] is False


def test_unmoved_pose_does_not_claim_five_mm_margin():
    result = evaluate(Pose(), detailed=False)
    assert result["minimum_margin_mm"] < 5
    assert result["target_margin_met"] is False
