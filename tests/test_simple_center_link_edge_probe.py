"""PB-02 solid-stock link-edge nominal regression."""

import pytest

from scripts.simple_center_link_edge_probe import probe


@pytest.fixture(scope="module")
def trial():
    return probe()


def test_ripped_solid_side_cleat_gives_both_link_members_x_edge_reserve(trial):
    assert trial["cleat_bounds_mm"] == {
        "rear": [89.05, 177.95, -213.8, -175.7, 0, 460],
        "side": [89.05, 177.95, -175.7, -118.9, 277, 460],
    }
    assert trial["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0, 238.9]
    assert trial["post_bolt_x_mm"] == 140
    assert trial["link_bolt_x_mm"] == 133.5
    assert trial["upright_bolt_x_span_mm"] == [50.95, 177.95]
    assert trial["actual_edge_end_mm"]["cleat_link_x_edges"] == [44.45, 44.45]
    assert trial["actual_edge_end_mm"]["cleat_link_side_x_edges"] == [44.45, 44.45]
    assert trial["minimum_link_4d_x_reserve_mm"] == 19.05
    assert trial["minimum_post_bolt_x_reserve_mm"] == 12.25
    assert trial["side_stock"] == {
        "blank_nominal_mm": [88.9, 88.9, 183],
        "finished_nominal_mm": [88.9, 56.8, 183],
        "nominal_y_removed_including_kerf_mm": 32.1,
        "kerf_mm": None,
        "single_solid_no_pocket": True,
    }


def test_fixed_layout_contacts_and_nominal_access_remain_clear(trial):
    assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert trial["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert set(trial["center_kicker_screw_receiver_fraction"].values()) == {1.0}
    assert trial["post_to_backer_x_gap_mm"] == 0
    assert trial["post_to_backer_x_face_contact_mm2"] == 9102.09
    assert trial["post_to_rear_cleat_contact_mm2"] > 15000
    assert trial["solid_overlaps_mm3"] == {}
    assert trial["fixed_screw_hits_mm3"] == {}
    assert trial["bore_unintended_wood_hits_mm3"] == {}
    assert trial["bore_pair_hits_mm3"] == {}
    assert set(trial["bore_received_fraction"].values()) == {1.0}
    assert set(trial["washer_bearing_fraction"].values()) == {1.0}
    assert trial["trial_20mm_radius_tool_wood_hits_mm3"] == {}
    assert trial["no_pocket_front_short_tool_clear"] is True
    assert trial["removed_legacy_stations"] == [
        "clip_split_base_center_right",
        "clip_split_header_center_right",
    ]
