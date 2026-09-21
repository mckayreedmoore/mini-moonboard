"""Regression checks for the bounded PB-02 post/header two-bolt co-design."""

from scripts.simple_center_post_header_two_bolt_probe import probe


def test_named_variants_recheck_complete_assembly():
    result = probe()
    assert set(result["variants"]) == {
        "reference",
        "lowered_block",
        "relocated_pairs",
        "post_axis_forward_5",
        "balanced_pair_5",
        "shorter_8in_trial",
    }
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["baseline_nominal_geometry"] == "feasible"
    assert result["rating_or_drilling_release"] is False

    candidate = result["variants"]["relocated_pairs"]
    assert candidate["block_bounds_mm"] == [177.65, 266.55, -175.7, -86.8, 75, 238.9]
    assert set(candidate["new_bores"]) == {
        "post_cleat_1",
        "post_cleat_2",
        "cleat_header_1",
        "cleat_header_2",
    }
    assert len(candidate["all_bores_checked"]) == 10
    assert candidate["conditional_markers_pass"] is True
    assert candidate["nominal_geometry"] == "feasible"
    assert all(value == 1 for value in candidate["bore_received_fraction"].values())
    assert all(value == 1 for value in candidate["washer_bearing_fraction"].values())
    assert all(candidate["clear_insertion_ends_by_bolt"].values())
    assert all(not value for value in candidate["collision_checks"].values())


def test_failed_variants_retain_exact_limiter():
    result = probe()
    assert result["variants"]["reference"]["conditional_markers_pass"] is False
    assert result["variants"]["lowered_block"]["conditional_markers_pass"] is False


def test_forward_post_axis_variant_reports_reserve_and_full_assembly():
    result = probe()
    candidate = result["variants"]["post_axis_forward_5"]
    assert candidate["post_axis_y_mm"] == -145
    assert candidate["minimum_conditional_edge_end_margin_mm"] > 0.3
    assert len(candidate["all_bores_checked"]) == 10
    assert result["fixed_screw_axes_checked"] == 66
    assert result["rating_or_drilling_release"] is False


def test_balanced_pair_has_five_mm_conditional_edge_reserve():
    from scripts.simple_center_post_header_two_bolt_probe import VARIANTS, _candidate

    candidate = _candidate(VARIANTS["balanced_pair_5"])
    assert candidate["post_axis_y_mm"] == -145
    assert candidate["minimum_conditional_edge_end_margin_mm"] >= 5
    assert candidate["nominal_geometry"] == "feasible"


def test_shorter_block_retains_group_fit_with_182_mm_vertical_grip():
    from scripts.simple_center_post_header_two_bolt_probe import VARIANTS, _candidate

    candidate = _candidate(VARIANTS["shorter_8in_trial"])
    assert candidate["block_bounds_mm"][-2] == 95
    assert candidate["vertical_wood_grip_mm"] == 182
    assert candidate["minimum_conditional_edge_end_margin_mm"] >= 5
    assert candidate["nominal_geometry"] == "feasible"
