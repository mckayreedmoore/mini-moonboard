"""The WJ24 center-axis length screen stays source-bound and conditional."""

from copy import deepcopy

import pytest

from scripts.wood_joint_wj24_bolt_length_screen import (
    INVENTORY_PATH,
    build_screen,
)


@pytest.fixture(scope="module")
def screen():
    return build_screen()


def test_screen_assigns_all_sixteen_axes_to_explicit_length_classes(screen):
    assert screen["source_axis_count"] == 16
    assert len(screen["source_axis_identity_sha256"]) == 64
    assert screen["source_inventory_path"] == str(
        INVENTORY_PATH.relative_to(INVENTORY_PATH.parents[4])
    )

    by_grip = {group["wood_grip_mm"]: group for group in screen["groups"]}
    assert set(by_grip) == {100.915644, 127.0, 167.0}
    assert (by_grip[100.915644]["axis_count"], by_grip[100.915644]["screened_nominal_length_in"]) == (
        4,
        4.75,
    )
    assert (by_grip[127.0]["axis_count"], by_grip[127.0]["screened_nominal_length_in"]) == (
        8,
        5.75,
    )
    assert (by_grip[167.0]["axis_count"], by_grip[167.0]["screened_nominal_length_in"]) == (
        4,
        7.5,
    )

    assigned = {
        axis_id: length_in
        for group in screen["groups"]
        for axis_id, length_in in group["axis_nominal_length_assignments_in"].items()
    }
    assert len(assigned) == 16
    assert assigned["center_principal_header_left_1"] == 4.75
    assert assigned["center_principal_right_2"] == 5.75
    assert assigned["center_post_header_right_2"] == 7.5


def test_length_classes_have_stack_and_receiving_reserve(screen):
    by_grip = {group["wood_grip_mm"]: group for group in screen["groups"]}
    expected = {
        100.915644: (118.11, 114.895044, 3.214956),
        127.0: (143.51, 140.9794, 2.5306),
        167.0: (185.928, 180.9794, 4.9486),
    }
    for grip, (min_delivery, thread_end, reserve) in expected.items():
        candidate = by_grip[grip]["selected_length_candidate"]
        assert candidate["minimum_delivered_underhead_length_mm"] == pytest.approx(
            min_delivery
        )
        assert candidate["required_full_thread_end_min_mm_from_underhead"] == pytest.approx(
            thread_end
        )
        assert candidate["length_margin_after_required_thread_projection_mm"] == pytest.approx(
            reserve
        )
        assert candidate["measured_transition_window_mm"] > 0
        assert candidate["dimension_screen_pass"] is True


def test_nominal_length_is_not_used_as_delivered_shank_or_thread_engagement(screen):
    assert screen["fastener_assumption"]["nominal_length_is_delivered_length"] is False
    assert screen["fastener_assumption"]["sku"] is None
    assert screen["release"]["sku_selected"] is False

    long_grip = next(group for group in screen["groups"] if group["wood_grip_mm"] == 167.0)
    eight_in = long_grip["eight_in_candidate"]
    assert eight_in["passes_total_length_screen"] is True
    assert eight_in["minimum_delivered_underhead_length_mm"] > eight_in[
        "required_full_thread_end_min_mm_from_underhead"
    ]
    assert eight_in["has_feasible_measured_transition_window"] is False
    assert eight_in["b18_2_1_Lb_min_mm"] > eight_in[
        "earliest_nut_bearing_face_mm_from_underhead"
    ]


def test_inventory_historical_stack_is_checked_before_assignment():
    import json

    inventory = json.loads(INVENTORY_PATH.read_text())
    changed = deepcopy(inventory)
    center_axis = next(
        row
        for row in changed["candidate_hardware_axis_schedule"]
        if row.get("family") == "wj05_center_x190"
    )
    center_axis["stack_class"]["historical_required_underhead_length_screen_mm"] += 1.0
    with pytest.raises(ValueError, match="historical WJ05 stack value changed"):
        build_screen(changed)
