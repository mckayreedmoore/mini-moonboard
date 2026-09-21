"""Regression for the bounded PB-02 header/post geometry rejection."""

import pytest

from scripts import simple_center_wide_post_probe as wide
from scripts.simple_center_header_post_probe import probe


@pytest.fixture(scope="module")
def trial():
    return probe()


def test_rear_cleat_is_continuous_across_header_post_joint(trial):
    assert trial["continuous_rear_cleat_bounds_mm"] == [
        89.05,
        177.95,
        -213.8,
        -175.7,
        0,
        460,
    ]
    assert trial["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0, 238.9]
    assert trial["header_bounds_mm"][4:] == [238.9, 277]
    assert trial["existing_post_bolt_axes_xz_mm"] == [[140, 110], [140, 190]]
    assert trial["bore_received_fraction_by_member"] == {
        "rear_cleat": 0.21428571,
        "base_header": 0.78571429,
    }
    assert trial["bore_received_fraction_total"] == 1
    assert trial["full_intended_bore_received"] is True
    assert trial["conditional_header_nearest_z_edge_mm"] == 19.05
    assert trial["conditional_4d_header_z_shortfall_mm"] == 6.35
    assert trial["conditional_reversible_required_header_z_mm"] == 50.8
    assert trial["conditional_one_direction_required_header_z_mm"] == 34.925


def test_clear_bore_still_fails_detachable_installed_access(trial):
    assert wide.BORE_RADIUS == 3.65
    assert trial["illustrative_bore_diameter_mm"] == 7.3
    assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert trial["fixed_axes_checked"] == 66
    assert trial["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert trial["removed_legacy_stations"] == [
        "clip_split_base_center_right",
        "clip_split_header_center_right",
    ]
    assert trial["bore_unintended_wood_hits_mm3"] == {}
    assert trial["bore_fixed_screw_hits_mm3"] == {}
    assert trial["bore_existing_bore_hits_mm3"] == {}
    assert trial["washer_bearing_fraction"] == {"rear": 1, "front": 1}
    assert (
        trial["trial_external_10mm_radius_5mm_hardware_wood_hits_mm3"]["front"][
            "kicker_right"
        ]
        > 0
    )
    assert trial["trial_20mm_radius_tool_wood_hits_mm3"]["front"]["kicker_right"] > 0
    assert trial["trial_20mm_radius_tool_wood_hits_mm3"]["rear"] == {}
    assert trial["front_end_blocked_by_installed_kicker"] is True
    assert trial["accepted_geometry"] is False
