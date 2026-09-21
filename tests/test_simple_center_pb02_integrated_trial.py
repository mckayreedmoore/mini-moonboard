"""Pin the viable Z328.5 pose and the rejected Z390 comparison."""

from copy import deepcopy

import pytest

from scripts import simple_center_connected_kinematics as kinematics_module
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_current_stack_tip_screen as stack
from scripts.export_v4_viewer_scene import build_scene
from scripts.simple_center_pb02_integrated_stack_screen import screen as stack_screen
from scripts.simple_center_pb02_integrated_trial import (
    ACTIVE_TRIAL,
    COMPARISON_LINK_Z,
    _integrated_nominal_clear,
    active_geometry,
    probe,
)


def test_combined_ten_bore_trial_and_rejected_link_comparison():
    result = probe()
    assert result["variant_id"] == "ligament_priority"
    assert result["coordinates_mm"]["post_cleat_2_z"] == 176
    assert result["coordinates_mm"]["cleat_link_z"] == 328.5
    assert result["side_bounds_mm"] == [89.05, 177.95, -175.7, -114.1, 277, 460]
    assert result["bore_count"] == 10
    assert set(result["bore_received_fraction"].values()) == {1.0}
    assert len(result["washer_bearing_fraction"]) == 20
    assert result["all_20_washer_seats_full"]
    assert result["all_66_fixed_axes_preserved"]
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert result["one_insertion_end_per_bolt_clear"]
    assert result["clear_insertion_ends_by_bolt"]["cleat_link"] == ["link_rear"]
    assert result["side_checks"] == {
        "side_other_wood_hits_mm3": {},
        "side_screw_hits_mm3": {},
    }
    assert not any(result["full_center_collision_checks"].values())
    assert (
        result["finite_shared_member_bore_ligaments_mm"]["post_high/post_cleat_2"]
        == 18.7
    )
    assert (
        result["finite_shared_member_bore_ligaments_mm"]["upright/cleat_link"]
        == 20.2
    )
    assert result["minimum_finite_shared_member_bore_ligament_mm"] == 7.2
    assert result["side_y_conditional_4d_plus_project_5_reserve_mm"] == 0
    assert result["side_z_conditional_7d_plus_5_reserve_mm"] == 2.05
    assert result["post_pair_conditional_4d_plus_5_reserve_mm"] == 0.6
    assert result["conditional_subset_minimum_reserve_mm"] == -12.55
    assert result["conditional_negative_rows"] == [
        {
            "bolt": "post_high",
            "member": "shifted_right_post",
            "feature": "z_high",
            "reserve_mm": -12.55,
        }
    ]
    assert result["post_high_loaded_end_distance_mm"] == 36.9
    assert result["post_high_conditional_3_5d_reserve_mm"] == 14.675
    assert result["post_high_conditional_c_delta"] == pytest.approx(0.83015)
    assert result["header_side_cleat_header_contact_area_mm2"] > 0
    assert sum(result["header_cleat_bore_reception_fraction"].values()) == 1
    assert result["integrated_nominal_cad_clear"]
    for category in ("side_other_wood_hits_mm3", "side_screw_hits_mm3"):
        collision = deepcopy(result)
        collision["side_checks"][category] = {"synthetic_collision": 1.0}
        assert not _integrated_nominal_clear(collision)
    assert not result["whole_center_classification_complete"]
    assert not result["rating_or_drilling_release"]

    rejected = probe(COMPARISON_LINK_Z)
    assert rejected["coordinates_mm"]["cleat_link_z"] == 390
    assert rejected["full_center_collision_checks"]["socket_body_wood_hits_mm3"] == {
        "link_front/base_rail_bottom_right": pytest.approx(471.14874)
    }
    assert (
        rejected["finite_shared_member_bore_ligaments_mm"]["upright/cleat_link"] == 26.7
    )
    assert not rejected["integrated_nominal_cad_clear"]


def test_active_geometry_prioritizes_the_post_bore_ligament():
    parts, bores, ends = active_geometry()
    assert ACTIVE_TRIAL.variant_id == "ligament_priority"
    assert len(bores) == 10
    assert parts["upright_side_cleat"].BoundingBox().ymax == -114.1
    assert parts["header_side_cleat"].BoundingBox().zmax == 344
    rear = parts["rear_cleat"].BoundingBox()
    assert (rear.zmin, rear.zmax, rear.zlen) == pytest.approx((5.0, 460.0, 455.0))
    assert ends["post_cleat_2_left"][0][2] == 176
    assert ends["post_rear_high"][0][2] == 202
    assert ends["cleat_header_1_bottom"][0][:2] == (208.35, -130.5)
    assert ends["cleat_header_2_bottom"][0][:2] == (236.0, -117.5)
    assert ends["link_rear"][0][2] == 328.5


def test_active_geometry_identity_agrees_across_all_consumers():
    parts, bores, ends = active_geometry()
    owners = placement._owners()
    placement_result = placement.table()
    stack_result = stack_screen()
    kinematics_result = kinematics_module.screen()
    scene = build_scene()

    assert {
        probe()["variant_id"],
        placement_result["variant_id"],
        stack_result["variant_id"],
        kinematics_result["variant_id"],
        scene["pb02_variant_id"],
    } == {ACTIVE_TRIAL.variant_id}
    assert {
        probe()["source_fingerprint"],
        placement_result["source_fingerprint"],
        stack_result["source_fingerprint"],
        kinematics_result["source_fingerprint"],
        scene["pb02_source_fingerprint"],
    } == {scene["pb02_source_fingerprint"]}
    assert scene["pb02_source_fingerprint"] == (
        "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
    )
    assert len(bores) == len(ends) // 2 == len(owners) == 10

    rows = stack_result["scenarios"]["current_lengths"]["rows"]
    viewer_axes = {
        axis["name"]: axis for axis in scene["axes"] if axis["station"] == "PB02"
    }
    expected_centers = []
    for bolt, pair in stack.PAIRS.items():
        start, finish = (ends[end][0] for end in pair)
        assert tuple(ends[end][2] for end in pair) == owners[bolt]
        assert rows[bolt]["wood_grip_mm"] == pytest.approx(
            sum(abs(a - b) for a, b in zip(start, finish, strict=True))
        )
        assert viewer_axes[bolt]["start_mm"] == list(start)
        rendered_finish = [
            start[i] + viewer_axes[bolt]["axis"][i] * viewer_axes[bolt]["length_mm"]
            for i in range(3)
        ]
        assert rendered_finish == pytest.approx(finish)
        expected_centers.append(tuple((a + b) / 2 for a, b in zip(start, finish)))

    edge_centers = [
        center
        for edge in kinematics_module.current_edges().values()
        for center in edge[3]
    ]
    assert sorted(edge_centers) == sorted(expected_centers)
    block = parts["header_post_side_cleat"].BoundingBox()
    viewer_block = next(
        box for box in scene["boxes"] if box["name"] == "PB02 post/header block"
    )
    assert viewer_block["origin_mm"] == pytest.approx(
        [block.xmin, block.ymin, block.zmin]
    )
    assert viewer_block["size_mm"] == pytest.approx(
        [block.xlen, block.ylen, block.zlen]
    )
