"""Focused tests for the source-bound WJ-04 bolt-stack dimensional screen."""

from dataclasses import replace

import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wj04_fastener_stack_method import report, screen_stack


def _screen_by_id():
    return {screen.stack_id: screen for screen in report()}


def test_each_actual_stack_uses_candidate_standard_and_shared_hardware_bounds():
    screens = _screen_by_id()

    assert set(screens) == {"rail_1", "rail_2", "upright_1", "upright_2"}
    rail = screens["rail_1"]
    assert rail.bolt_sku == "25C375HCS5Z"
    assert rail.layer_grip_mm == (38.1, 38.1)
    assert rail.delivered_length_min_mm == pytest.approx(93.726)
    assert rail.delivered_length_max_mm == pytest.approx(95.25)
    assert rail.standard_body_min_mm == pytest.approx(69.85)
    assert rail.standard_full_thread_start_max_mm == pytest.approx(76.2)
    assert rail.nut_bearing_face_min_mm == pytest.approx(77.7908)
    assert rail.nut_far_face_max_mm == pytest.approx(87.0044)
    assert rail.tip_projection_min_mm == pytest.approx(6.7216)
    assert rail.max_thread_bearing_fractions == pytest.approx((0.0, 0.2430569948))
    assert rail.body_end_min_for_fraction_mm == pytest.approx(69.582)
    assert rail.receiving_body_end_min_mm == pytest.approx(69.85)
    assert rail.receiving_full_thread_start_max_mm == pytest.approx(77.7908)
    assert rail.receiving_full_thread_end_min_mm == pytest.approx(89.5444)
    assert rail.standards_guarantee_limited_thread_bearing
    assert rail.standards_guarantee_nut_thread_start
    assert not rail.standards_guarantee_full_form_thread_end
    assert rail.standards_guarantee_tip_projection
    assert not rail.standards_guarantee_stack

    principal = screens["upright_1"]
    assert principal.bolt_sku == "25C600HCS5Z"
    assert principal.layer_grip_mm == (95.25, 38.1)
    assert principal.delivered_length_min_mm == pytest.approx(149.86)
    assert principal.delivered_length_max_mm == pytest.approx(152.4)
    assert principal.standard_body_min_mm == pytest.approx(127.0)
    assert principal.standard_full_thread_start_max_mm == pytest.approx(133.35)
    assert principal.nut_bearing_face_min_mm == pytest.approx(134.9408)
    assert principal.nut_far_face_max_mm == pytest.approx(144.1544)
    assert principal.tip_projection_min_mm == pytest.approx(5.7056)
    assert principal.max_thread_bearing_fractions == pytest.approx((0.0, 0.2430569948))
    assert principal.body_end_min_for_fraction_mm == pytest.approx(126.732)
    assert principal.receiving_body_end_min_mm == pytest.approx(127.0)
    assert principal.receiving_full_thread_start_max_mm == pytest.approx(134.9408)
    assert principal.receiving_full_thread_end_min_mm == pytest.approx(146.6944)
    assert principal.standards_guarantee_limited_thread_bearing
    assert principal.standards_guarantee_nut_thread_start
    assert not principal.standards_guarantee_full_form_thread_end
    assert principal.standards_guarantee_tip_projection
    assert not principal.standards_guarantee_stack


def test_receiving_screen_requires_measured_body_transition_threads_and_nut_fit():
    rail = _screen_by_id()["rail_1"]

    def received(body, start, end, length, verified=True):
        return rail.receipt_transition_fits(
            body,
            start,
            end,
            length,
            functional_nut_engagement_verified=verified,
        )

    assert received(69.85, 77.0, 89.5444, 93.726)
    assert not received(69.849, 77.0, 89.5444, 93.726)
    assert not received(69.85, 77.7909, 89.5444, 93.726)
    assert not received(77.1, 77.0, 89.5444, 93.726)  # Transition intervals overlap.
    assert not received(69.85, 77.0, 89.5443, 93.726)
    assert not received(69.85, 77.0, 89.5444, 93.725)
    assert not received(69.85, 77.0, 89.5444, 95.251)
    assert not received(
        69.85, 77.0, 94.0, 93.726
    )  # Full thread cannot exceed bolt tip.
    assert not received(69.85, 77.0, 89.5444, 93.726, verified=False)
    assert not received(float("nan"), 77.0, 89.5444, 93.726)


def test_changed_member_thickness_recomputes_against_same_bolt_candidate():
    rail = WJ04_TRIAL.stack_by_id("rail_1")
    changed_layers = (
        rail.layers[0],
        replace(rail.layers[1], thickness_mm=53.34),
    )
    wider_t_stack = screen_stack(replace(rail, layers=changed_layers))

    assert wider_t_stack.bolt_sku == "25C375HCS5Z"
    assert wider_t_stack.layer_grip_mm == (38.1, 53.34)
    assert wider_t_stack.nut_bearing_face_min_mm == pytest.approx(93.0308)
    assert wider_t_stack.nut_far_face_max_mm == pytest.approx(102.2444)
    assert wider_t_stack.tip_projection_min_mm == pytest.approx(-8.5184)
    assert not wider_t_stack.standards_guarantee_limited_thread_bearing
    assert not wider_t_stack.standards_guarantee_tip_projection


def test_limits_and_stack_shape_are_validated():
    rail = WJ04_TRIAL.stack_by_id("rail_1")
    with pytest.raises(ValueError, match="thread-bearing fraction"):
        screen_stack(rail, max_thread_bearing_fraction=1.0)
    with pytest.raises(ValueError, match="cut allowance"):
        screen_stack(rail, wood_cut_allowance_mm=38.1)
    with pytest.raises(ValueError, match="actual wood layers"):
        screen_stack(replace(rail, layers=()))
