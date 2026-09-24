"""Synthetic checks for WJ-03 outer-trial tool and removal screens."""

import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    BoltStack,
    StackLayer,
    WasherSeat,
)
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_wj03_compact_outer_tools import (
    TOOL,
    _face_datum,
    _geometry_maps,
    _projection_bounds,
    _seated_tool_center,
    _socket_envelopes,
    build_tool_report,
)
from scripts.wood_joint_wj04_tool_access import build_catalog_wrench_envelope


@pytest.mark.parametrize("outward_sign", (1, -1))
def test_wrench_and_socket_seat_within_target_for_either_axis_sign(outward_sign):
    outward = cq.Vector(0, 0, outward_sign)
    target = cq.Solid.makeCylinder(
        6.4,
        4.0,
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, -outward_sign),
    )
    center = _seated_tool_center((0, 0, 0), outward, target, TOOL.head_thickness_mm)
    wrench = build_catalog_wrench_envelope(
        center,
        outward.toTuple(),
        (1, 0, 0),
        TOOL,
        offset_degrees=0,
    )
    wrench_datum = _face_datum((0, 0, 0), outward, target, wrench)
    socket = _socket_envelopes((0, 0, 0), outward, target, travel_mm=7.0)

    target_inner, target_outer = _projection_bounds(target, outward)
    wrench_inner, wrench_outer = _projection_bounds(wrench, outward)
    assert wrench_datum["wrench_axial_overlap_mm"] == pytest.approx(
        TOOL.head_thickness_mm
    )
    assert wrench_datum["wrench_is_contained_within_modeled_fastener_height"] is True
    assert wrench_inner >= target_inner
    assert wrench_outer <= target_outer
    assert wrench_datum["actual_jaw_contact_or_hex_engagement_verified"] is False
    assert socket["seat_datum"]["seat_plane_error_mm"] == pytest.approx(0, abs=1e-9)
    assert socket["seat_datum"]["socket_seating_face_projection_mm"] == pytest.approx(
        target_inner
    )
    assert socket["seat_datum"]["approach_start_axis_projection_mm"] == pytest.approx(
        target_outer
    )
    assert _projection_bounds(socket["seated_external_envelope"], outward)[
        0
    ] == pytest.approx(target_inner)
    assert _projection_bounds(socket["seated_external_envelope"], outward)[
        1
    ] == pytest.approx(target_inner + 55.0)
    assert _projection_bounds(
        socket["approach_sweep_envelope"], outward
    ) == pytest.approx((target_inner, target_inner + 55.0 + 4.0))
    assert socket["approach_start_envelope"].isValid()
    assert socket["seated_external_envelope"].isValid()
    assert socket["approach_sweep_envelope"].isValid()
    assert socket["removal_terminal_envelope"].isValid()
    assert socket["removal_sweep_envelope"].isValid()


@pytest.mark.parametrize("outward_sign", (1, -1))
def test_wrench_proxy_rejects_target_thinner_than_nominal_tool_head(outward_sign):
    outward = cq.Vector(0, 0, outward_sign)
    thin_target = cq.Solid.makeCylinder(
        6.4,
        TOOL.head_thickness_mm - 0.5,
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, -outward_sign),
    )

    with pytest.raises(ValueError, match="tool thickness exceeds target axial height"):
        _seated_tool_center((0, 0, 0), outward, thin_target, TOOL.head_thickness_mm)


def _synthetic_geometry(stack_count=20):
    hardware = BoltHardware(
        candidate_sku="provisional ordinary 1/4-20 through-bolt; grade and supplier unselected",
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
        origin = cq.Vector(index * 250.0, 0, 40)
        grip = (StackLayer("host_head", 20.0), StackLayer("host_nut", 20.0))
        head_seat = origin + direction * hardware.washer_thickness_mm
        nut_seat = head_seat + direction * 40.0
        stack = BoltStack(
            id=stack_id,
            hardware=hardware,
            under_head_origin=origin,
            direction=direction,
            layers=grip,
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

    first_head_tool_center_z = 40 - hardware.head_height_mm / 2
    blocker = cq.Solid.makeBox(
        2.0,
        2.0,
        2.0,
        cq.Vector(30.0, -1.0, first_head_tool_center_z - 1.0),
    )
    lower_panel = cq.Solid.makeBox(10.0, 10.0, 10.0, cq.Vector(5000, 0, 10))
    upper_panel = cq.Solid.makeBox(10.0, 10.0, 10.0, cq.Vector(7000, 0, 10))
    staged_lower_panel = lower_panel.translate(cq.Vector(100, 0, 0))
    protected_solids = {
        "tnuts": {"moving_lower_tnut": blocker, "retained_upper_tnut": blocker},
        "lights": {},
        "wires": {},
        "panel_screws": {
            "round_panel_lower_left_rim_1": blocker,
            "round_panel_upper_left_rim_1": blocker,
            "round_kicker_left_rim_1": blocker,
            "round_header_upper_left_1": blocker,
        },
        "frame_bolts": {"retained_frame_bolt_axis": blocker},
        "frame_bolt_components": {"retained_frame_bolt/head": blocker},
        "frame_bolt_tools": {"not_installed_tool": blocker},
        "frame_bolt_withdrawal": {"old_withdrawal_proxy": blocker},
        "hold_hole_and_trial_projection": {"removal_precondition_proxy": blocker},
        "retained_legacy_sds": {},
        "retained_legacy_connectors": {},
    }
    return SimpleNamespace(
        trial_id="synthetic_compact_outer",
        floor_z_mm=0.0,
        floor_datum="synthetic global z=0",
        source_binding={"synthetic": True},
        source_pins={"test": "synthetic"},
        stacks=stacks,
        finished_wood={
            "synthetic_body": blocker,
            "main_lower_left": lower_panel,
            "main_upper_left": upper_panel,
        },
        panels={"main_lower_left": lower_panel, "main_upper_left": upper_panel},
        protected={
            "counts": {},
            "solids": protected_solids,
        },
        tnut_owners={
            "moving_lower_tnut": "main_lower_left",
            "retained_upper_tnut": "main_upper_left",
        },
        staged_panels={
            "staged/main_lower_left/panel": staged_lower_panel,
            "staged/main_lower_left/tnut/moving_lower_tnut": blocker,
        },
        installed_hardware=installed,
        wj05_bolts={},
        wj05_stacks={},
    )


def test_build_report_keeps_all_twenty_stacks_and_bounds_claims():
    result = build_tool_report(_synthetic_geometry())
    encoded = json.dumps(result, sort_keys=True)

    assert '"stack_count": 20' in encoded
    assert result["stack_count"] == 20
    assert len(result["stacks"]) == 20
    assert result["release_claims"]["physical_access_established"] is False
    assert result["release_claims"]["tool_selected"] is False
    assert result["tool_candidates"]["facom_open_end_wrench"]["selected"] is False
    assert result["tool_candidates"]["koken_socket"]["selected"] is False
    tool_pins = result["source_pins"]["tool_report_producer_and_direct_dependencies"]
    assert {
        "scripts/wood_joint_wj03_compact_outer_tools.py",
        "scripts/wood_joint_wj03_compact_outer_access.py",
        "scripts/wood_joint_wj04_tool_access.py",
        "mini_moonboard/wood_joint_frame.py",
        "mini_moonboard/wood_joint_wj04_config.py",
        "mini_moonboard/wood_joint_wj05_socket.py",
    } == set(tool_pins)
    assert all(len(digest) == 64 for digest in tool_pins.values())
    assert result["unmodeled_preconditions"]
    assert result["analytical_floor"]["below_floor_envelopes"]

    first = result["stacks"]["synthetic_00"]
    assert first["facom_open_end_tool"]["nut_detachment"][
        "excluded_target_obstacle_ids"
    ] == [
        "installed_hardware/wj03/synthetic_00/nut",
        "installed_hardware/wj03/synthetic_00/shaft",
    ]
    assert first["facom_open_end_tool"]["bolt_withdrawal"][
        "excluded_target_obstacle_ids"
    ] == sorted(
        [
            f"installed_hardware/wj03/synthetic_00/{role}"
            for role in ("shaft", "head", "head_washer", "nut_washer", "nut")
        ]
    )
    assert (
        "finished_wood/synthetic_body"
        in result["overlap_summary_by_class"]["finished_body"]
    )

    seat = first["facom_open_end_tool"]["heading_cases"][0]["nut_seat_datum"]
    assert seat["wrench_axial_overlap_mm"] == pytest.approx(TOOL.head_thickness_mm)
    assert seat["wrench_is_contained_within_modeled_fastener_height"] is True
    assert (
        first["facom_open_end_tool"]["nut_washer_detachment"][
            "axial_sliding_clearance"
        ]["source_bounds_allow_modeled_axial_slide"]
        is True
    )
    bolt_withdrawal = first["facom_open_end_tool"]["bolt_withdrawal"]
    assert {
        "shaft_start_pose",
        "head_start_pose",
        "shaft_terminal_pose",
        "head_terminal_pose",
        "shaft_insertion_and_withdrawal",
        "head_insertion_and_withdrawal",
    } <= set(bolt_withdrawal["floor_screen"])
    assert bolt_withdrawal["physical_access_established"] is False
    wrench_case = first["facom_open_end_tool"]["heading_cases"][0]
    pair = wrench_case["counterhold_vs_nut_motion"]["nut_stroke"]
    assert pair["excluded_target_obstacle_ids"] == []
    assert pair["envelope_clash_proves_physical_blockage"] is False


def test_report_rejects_wrong_outer_stack_count():
    with pytest.raises(ValueError, match="exactly 20"):
        build_tool_report(_synthetic_geometry(stack_count=19))


def test_obstacles_keep_only_physical_protected_shapes_in_current_sequence():
    geometry = _synthetic_geometry()

    obstacles, classes, _panels = _geometry_maps(geometry)

    assert "protected/tnuts/retained_upper_tnut" in obstacles
    assert "protected/tnuts/moving_lower_tnut" not in obstacles
    assert "staged_panels/staged/main_lower_left/tnut/moving_lower_tnut" in obstacles
    assert "protected/panel_screws/round_panel_upper_left_rim_1" in obstacles
    assert "protected/panel_screws/round_header_upper_left_1" in obstacles
    assert "protected/panel_screws/round_panel_lower_left_rim_1" not in obstacles
    assert "protected/panel_screws/round_kicker_left_rim_1" not in obstacles
    assert "finished_wood/main_lower_left" not in obstacles
    assert "finished_wood/main_upper_left" in obstacles
    assert "staged_panels/staged/main_lower_left/panel" in obstacles
    assert "protected/frame_bolts/retained_frame_bolt_axis" in obstacles
    assert not any("frame_bolt_tools" in name for name in obstacles)
    assert not any("frame_bolt_withdrawal" in name for name in obstacles)
    assert not any("hold_hole_and_trial_projection" in name for name in obstacles)
    assert classes["protected/frame_bolt_components/retained_frame_bolt/head"] == (
        "protected_geometry"
    )


def test_washer_slide_uses_shared_minimum_id_and_maximum_body_diameter():
    result = build_tool_report(_synthetic_geometry())
    clearance = result["stacks"]["synthetic_00"]["facom_open_end_tool"][
        "nut_washer_detachment"
    ]["axial_sliding_clearance"]

    assert clearance["washer_min_inner_diameter_mm"] == pytest.approx(
        WJ04_TRIAL.fasteners.washer.inner_diameter_range_mm[0]
    )
    assert clearance["shaft_max_diameter_mm"] == pytest.approx(
        WJ04_TRIAL.fasteners.bolts[0].body_diameter_range_mm[1]
    )
    assert clearance["minimum_radial_clearance_mm"] > 0
