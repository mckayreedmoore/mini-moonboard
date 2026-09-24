"""Synthetic tests for bounded WJ-03 through-bolt withdrawal screens."""

from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_frame import BoltStack
from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    StackLayer,
    WasherSeat,
)
from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj03_head_withdrawal as withdrawal


def _synthetic_geometry(stack_count=20):
    hardware = BoltHardware(
        candidate_sku="synthetic provisional 1/4-20 through-bolt",
        under_head_length_mm=55.0,
        steel_diameter_mm=6.35,
        cad_occupied_diameter_mm=6.35,
        drill_diameter_mm=7.5,
        head_diameter_mm=12.827,
        head_height_mm=4.1656,
        washer_od_mm=18.6436,
        washer_id_mm=8.0,
        washer_thickness_mm=1.651,
        nut_diameter_mm=12.827,
        nut_height_mm=5.7404,
        usable_thread_start_mm=0.0,
        usable_thread_end_mm=55.0,
    )
    stacks = {}
    installed = {}
    for index in range(stack_count):
        stack_id = f"synthetic_{index:02d}"
        direction = cq.Vector(0, 0, 1 if index % 2 == 0 else -1)
        origin = cq.Vector(index * 500.0, 0, 300.0)
        layers = (
            StackLayer("host_head", 20.0),
            StackLayer("host_nut", 20.0),
        )
        head_seat = origin + direction * hardware.washer_thickness_mm
        nut_seat = head_seat + direction * 40.0
        stack = BoltStack(
            id=stack_id,
            hardware=hardware,
            under_head_origin=origin,
            direction=direction,
            layers=layers,
            head_seat=WasherSeat("host_head", head_seat, direction),
            nut_seat=WasherSeat("host_nut", nut_seat, -direction),
        )
        stacks[stack_id] = stack
        installed.update(
            {
                f"wj03/{stack_id}/{role}": shape
                for role, shape in stack.installed_shapes().items()
            }
        )
    return SimpleNamespace(
        trial_id=compact_access.TRIAL_ID,
        source_binding={"synthetic": "binding"},
        source_pins={"synthetic": "pin"},
        floor_z_mm=0.0,
        stacks=stacks,
        panels={},
        staged_panels={},
        finished_wood={
            "retained_body": cq.Solid.makeBox(
                20.0, 20.0, 20.0, cq.Vector(0, 500.0, 10.0)
            )
        },
        protected={"solids": {}},
        tnut_owners={},
        installed_hardware=installed,
        wj05_bolts={},
        wj05_stacks={},
    )


def test_ratchet_proxy_uses_centered_drive_axis_and_declared_dimensions():
    pose = withdrawal._ratchet_proxy(
        cq.Vector(10, 20, 30),
        cq.Vector(0, 0, 1),
        cq.Vector(1, 0, 0),
    )
    head_bounds = pose["ratchet_head"].BoundingBox()
    handle_bounds = pose["ratchet_handle"].BoundingBox()

    assert head_bounds.xlen == pytest.approx(withdrawal.RATCHET_HEAD_DIAMETER_MM)
    assert head_bounds.ylen == pytest.approx(withdrawal.RATCHET_HEAD_DIAMETER_MM)
    assert head_bounds.zlen == pytest.approx(withdrawal.RATCHET_HEAD_THICKNESS_MM)
    assert handle_bounds.xmin == pytest.approx(10.0)
    assert handle_bounds.xmax == pytest.approx(
        10.0 + withdrawal.RATCHET_HANDLE_REACH_MM
    )
    assert withdrawal.RATCHET_HANDLE_REACH_MM == pytest.approx(164.0)
    assert handle_bounds.ylen == pytest.approx(withdrawal.RATCHET_HANDLE_BOX_WIDTH_MM)
    assert handle_bounds.zlen == pytest.approx(
        withdrawal.RATCHET_HANDLE_BOX_THICKNESS_MM
    )
    assert withdrawal.RATCHET_HANDLE_BOX_WIDTH_MM == pytest.approx(28.0)
    assert withdrawal.RATCHET_BODY_AND_TANG_LENGTH_MM == pytest.approx(24.5)
    assert withdrawal.RATCHET_TANG_PROJECTION_MM == pytest.approx(10.8)


def test_stationary_counterhold_cases_cover_four_headings_and_stand_off_range():
    cases, record = withdrawal._stationary_ratchet_case_shapes(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, 1),
        cq.Vector(1, 0, 0),
    )

    assert record["sampled_handle_heading_degrees_from_face_reference"] == [
        0.0,
        90.0,
        180.0,
        270.0,
    ]
    assert record["stand_off_range_mm"] == [0.0, 10.8]
    assert record["heading_screen_is_discrete_not_continuous"] is True
    assert len(record["continuous_stand_off_sweeps"]) == 8
    assert all(shape.isValid() for shape in cases.values())


def test_head_stroke_sweeps_cover_signed_five_degrees_and_stand_off():
    cases, record = withdrawal._ratchet_case_shapes(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, 1),
        cq.Vector(1, 0, 0),
        start_heading_degrees=90.0,
    )

    assert record["starting_heading_degrees_from_face_reference"] == 90.0
    assert record["stand_off_range_mm"] == [0.0, 10.8]
    assert record["head_stroke_degrees"] == [-5.0, 5.0]
    assert record["all_strokes_are_analytic_aabb_rotation_bounds"] is True
    assert any("stroke_sweep_-5deg" in key for key in cases)
    assert any("stroke_sweep_+5deg" in key for key in cases)
    assert any("continuous_stand_off_and_stroke_-5deg" in key for key in cases)
    assert any("continuous_stand_off_and_stroke_+5deg" in key for key in cases)
    assert all(shape.isValid() for shape in cases.values())


def test_report_keeps_all_twenty_stacks_and_counterhold_in_each_removal_state(
    monkeypatch,
):
    collision_calls = []

    def record_collision(
        candidate_shapes,
        obstacles,
        *,
        excluded_target_ids=(),
        exclusion_scope="",
    ):
        excluded = set(excluded_target_ids)
        assert excluded <= set(obstacles)
        collision_calls.append(
            {
                "candidate_names": set(candidate_shapes),
                "obstacle_names": set(obstacles),
                "excluded": excluded,
                "exclusion_scope": exclusion_scope,
            }
        )
        return {
            "external_envelope_hits_mm3": {},
            "external_envelope_clear": True,
            "excluded_target_obstacle_ids": sorted(excluded),
            "exclusion_scope": exclusion_scope,
            "physical_access_established": False,
        }

    monkeypatch.setattr(withdrawal.tool_access, "collision_report", record_collision)
    result = withdrawal.build_head_withdrawal_report(_synthetic_geometry())

    assert result["candidate_stack_count"] == compact_tools.STACK_COUNT == 20
    assert len(result["stacks"]) == 20
    assert result["release_claims"]["tool_selected"] is False
    assert result["release_claims"]["hardware_capture_path_verified"] is False
    assert result["tool_candidates"]["counterhold_ratchet"][
        "stationary_handle_heading_samples_degrees"
    ] == [0.0, 90.0, 180.0, 270.0]
    assert result["ratchet_socket_mating"]["ratchet_head_standoff_range_mm"] == [
        0.0,
        10.8,
    ]
    assert result["ratchet_socket_mating"][
        "nominal_tang_projection_from_drawing_mm"
    ] == pytest.approx(10.8)
    ratchet = result["tool_candidates"]["head_ratchet"]
    assert ratchet["modeled_handle_reach_from_drive_axis_mm"] == pytest.approx(164.0)
    assert ratchet["handle_box_width_assumption_mm"] == pytest.approx(28.0)
    assert ratchet["handle_cross_section_is_published"] is False
    assert ratchet["handle_proxy_is_guaranteed_catalog_bound"] is False

    first = result["stacks"]["synthetic_00"]
    assert (
        first["nut_counterhold_ratchet"][
            "stationary_during_head_side_stroke_and_bolt_withdrawal"
        ]
        is True
    )
    assert (
        first["bolt_withdrawal_after_unthreading"][
            "head_tool_against_stationary_counterhold"
        ]["excluded_target_obstacle_ids"]
        == []
    )
    assert (
        first["post_withdrawal_loose_hardware"][
            "counterhold_tool_removal_complete_before_nut_washer_exit_assumed"
        ]
        is True
    )
    assert (
        first["post_withdrawal_loose_hardware"][
            "counterhold_tool_removal_complete_before_nut_washer_exit_verified"
        ]
        is False
    )
    assert (
        first["post_withdrawal_loose_hardware"][
            "counterhold_tool_full_capture_after_short_exit_verified"
        ]
        is False
    )

    target_head = "installed_hardware/wj03/synthetic_00/head"
    target_nut = "installed_hardware/wj03/synthetic_00/nut"
    nut_socket_call = next(
        call
        for call in collision_calls
        if call["candidate_names"] == {"stationary_nut_socket"}
    )
    assert nut_socket_call["excluded"] == {
        target_nut,
        "installed_hardware/wj03/synthetic_00/shaft",
    }
    counterhold_pair = next(
        call
        for call in collision_calls
        if "head_side_socket" in call["candidate_names"]
        and "tool_pair/stationary_nut_socket" in call["obstacle_names"]
        and "head_side_ratchet/heading_+0deg/stand_off_0mm/ratchet_handle"
        in call["candidate_names"]
    )
    assert counterhold_pair["excluded"] == set()
    assert any(
        name.startswith("tool_pair/stationary_nut_ratchet/")
        for name in counterhold_pair["obstacle_names"]
    )

    shaft_call = next(
        call
        for call in collision_calls
        if call["candidate_names"] == {"shaft_axial_withdrawal"}
    )
    assert shaft_call["excluded"] == {"tool_pair/stationary_nut_socket"}
    assert any(
        name.startswith("tool_pair/stationary_nut_ratchet/")
        for name in shaft_call["obstacle_names"]
    )
    washer_exit = next(
        call
        for call in collision_calls
        if call["candidate_names"] == {"nut_washer_short_axial_exit"}
    )
    assert not any(
        name.startswith("tool_pair/stationary_nut_")
        for name in washer_exit["obstacle_names"]
    )
    assert target_head not in washer_exit["obstacle_names"]
