"""Regression for the bounded nominal seven-axis wood screen."""

import json

from scripts.hardware_first_center_tongue_wood import OUTPUT, screen_center_tongue_wood


def test_center_tongue_wood_screen():
    report = screen_center_tongue_wood()
    axes = report["axis_margins"]
    assert len(axes) == 7
    assert axes["shared_post"]["grain_negative_boundary_mm"] == 183.55
    assert axes["shared_post"]["grain_positive_boundary_mm"] == 50.8
    assert axes["shared_post"]["transverse_negative_boundary_mm"] == 31.75
    assert axes["lower_left_header"]["grain_positive_boundary_mm"] == 274.45
    assert axes["upper_right_header"]["grain_positive_boundary_mm"] == 64.75
    assert axes["upper_right_header"]["grain_boundary_kind"] == (
        "raised_profile_shoulder_not_free_end"
    )
    assert axes["shared_post"]["reversible_4d_transverse_margins_mm"] == [-19.05, 7.92]
    assert axes["upper_right_header"]["reversible_4d_transverse_margins_mm"] == [
        139.2,
        -18.55,
    ]
    assert all(
        axes[f"upper_{side}_principal"]["oblique_end_unclassified"]
        for side in ("left", "right")
    )
    assert len(report["independent_header_group_spacing"]) == 2
    assert len(report["cross_group_header_spacing"]) == 4
    assert (
        report["header_bore_to_principal_toe_solid_gap_mm"]["lower_left_header"]["left"]
        == 0
    )
    assert all(
        gap >= 0
        for sides in report["header_bore_to_principal_toe_solid_gap_mm"].values()
        for gap in sides.values()
    )
    assert json.loads(OUTPUT.read_text()) == report
