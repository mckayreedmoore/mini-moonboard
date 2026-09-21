"""Regression checks for the bounded PB-02 post/header two-bolt co-design."""

from scripts.simple_center_post_header_two_bolt_probe import probe


def test_named_variants_recheck_complete_assembly():
    result = probe()
    assert set(result["variants"]) == {"reference", "lowered_block", "relocated_pairs"}
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
