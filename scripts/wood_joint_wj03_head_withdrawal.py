"""Bounded WJ-03 head-side through-bolt withdrawal screen.

Uses source-bound compact WJ-03 geometry and the existing external-envelope
collision helpers. It screens nominal tool and axial paths only; it is not a
tool-fit, access, capture, fabrication, or structural acceptance.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import BoltStack
from mini_moonboard.wood_joint_wj05_socket import (
    KOKEN_PRODUCT_URL,
    KOKEN_SOCKET_LENGTH_MM,
    KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
    KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
)
from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj03_compact_outer_tools as compact_tools
from scripts import wood_joint_wj04_tool_access as tool_access

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj03_head_withdrawal/v1"
HIT_TOLERANCE_MM3 = 1e-6
STROKE_DEGREES = 5.0
LOOSE_NUT_EXIT_MM = 10.0
LOOSE_WASHER_EXIT_MM = 5.0
COUNTERHOLD_HEADINGS_DEGREES = (0.0, 90.0, 180.0, 270.0)
HEAD_RATCHET_START_HEADINGS_DEGREES = (0.0, 90.0, 180.0, 270.0)

RATCHET_PRODUCT_ID = "koken_3725z_3_8"
RATCHET_PRODUCT = "Ko-ken 3725Z 3/8-in square-drive reversible ratchet"
RATCHET_PRODUCT_URL = (
    "https://kokenusa.com/products/"
    "z-series-3-8-sq-dr-reversible-ratchet-l-178mm-72-tooth"
)
RATCHET_DRAWING_URL = "https://www.koken-tool.co.jp/en/panflets/KOKEN202101EN.pdf"
RATCHET_HEAD_DIAMETER_MM = 28.0  # D
RATCHET_HEAD_THICKNESS_MM = 13.7  # H
RATCHET_BODY_AND_TANG_LENGTH_MM = 24.5  # T
RATCHET_OVERALL_LENGTH_MM = 178.0  # L
RATCHET_GEAR_TEETH = 72
RATCHET_CATALOG_SWING_DEGREES = 5.0
RATCHET_TANG_PROJECTION_MM = RATCHET_BODY_AND_TANG_LENGTH_MM - RATCHET_HEAD_THICKNESS_MM
RATCHET_STANDOFF_MAX_MM = RATCHET_TANG_PROJECTION_MM
# Drawing L spans rear head edge to handle tip; drive axis sits D/2 from rear edge.
RATCHET_HANDLE_REACH_MM = RATCHET_OVERALL_LENGTH_MM - RATCHET_HEAD_DIAMETER_MM / 2
# Ko-ken does not list handle cross-section. D and H define explicit box proxies,
# not catalog handle dimensions or guaranteed bounds.
RATCHET_HANDLE_BOX_WIDTH_MM = RATCHET_HEAD_DIAMETER_MM
RATCHET_HANDLE_BOX_THICKNESS_MM = RATCHET_HEAD_THICKNESS_MM

SOURCE_PIN_PATHS = (
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/wood_joint_wj04_config.py",
    "mini_moonboard/wood_joint_wj05_socket.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj03_compact_outer_tools.py",
    "scripts/wood_joint_wj03_head_withdrawal.py",
    "scripts/wood_joint_wj04_tool_access.py",
)


def _source_pins() -> dict[str, str]:
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in SOURCE_PIN_PATHS
    }


def _target_component_keys(
    installed: Mapping[str, cq.Shape], stack_id: str
) -> dict[str, str]:
    return {
        role: compact_tools._installed_key(installed, stack_id, role)
        for role in ("shaft", "head", "head_washer", "nut_washer", "nut")
    }


def _bearing_face_point(
    axis_point: cq.Vector, target: cq.Shape, outward: cq.Vector
) -> cq.Vector:
    low, _high = compact_tools._projection_bounds(target, outward)
    return axis_point + outward * (low - axis_point.dot(outward))


def _socket_pose(
    axis_point: cq.Vector,
    target: cq.Shape,
    outward: cq.Vector,
) -> tuple[cq.Shape, cq.Vector, dict[str, Any]]:
    """Return the 55-mm outside envelope and centered drive-axis endpoint."""
    socket = compact_tools._socket_envelopes(axis_point, outward, target)
    bearing_face = _bearing_face_point(axis_point, target, outward)
    drive_axis_center = bearing_face + outward * KOKEN_SOCKET_LENGTH_MM
    return (
        socket["seated_external_envelope"],
        drive_axis_center,
        socket["seat_datum"],
    )


def _ratchet_proxy(
    drive_axis_center: cq.Vector,
    outward: cq.Vector,
    reference: cq.Vector,
    heading_degrees: float = 0.0,
) -> dict[str, cq.Shape]:
    """Build centered round-head and full-width handle-box proxies."""
    outward = compact_tools._vec(outward, "ratchet outward axis")
    handle_axis = compact_tools._handle_axis(outward, reference, heading_degrees)
    head = cq.Solid.makeCylinder(
        RATCHET_HEAD_DIAMETER_MM / 2,
        RATCHET_HEAD_THICKNESS_MM,
        drive_axis_center,
        outward,
    )
    plane = cq.Plane(
        origin=drive_axis_center,
        xDir=handle_axis,
        normal=outward,
    )
    handle = (
        cq.Workplane(plane)
        .box(
            RATCHET_HANDLE_REACH_MM,
            RATCHET_HANDLE_BOX_WIDTH_MM,
            RATCHET_HANDLE_BOX_THICKNESS_MM,
            centered=(False, True, False),
        )
        .val()
    )
    return {"ratchet_head": head, "ratchet_handle": handle}


def _ratchet_case_shapes(
    socket_drive_axis_center: cq.Vector,
    outward: cq.Vector,
    reference: cq.Vector,
    *,
    start_heading_degrees: float,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    """Build one heading's ratchet proxies over stand-off and +/-5 degree stroke."""
    cases: dict[str, cq.Shape] = {}
    stroke_sweeps = {}
    for stand_off in (0.0, RATCHET_STANDOFF_MAX_MM):
        drive_center = socket_drive_axis_center + outward * stand_off
        pose = _ratchet_proxy(drive_center, outward, reference, start_heading_degrees)
        for name, shape in pose.items():
            cases[
                f"heading_{start_heading_degrees:+g}deg/"
                f"stand_off_{stand_off:g}mm/{name}"
            ] = shape
        for angle in (-STROKE_DEGREES, STROKE_DEGREES):
            stroke_pose = _ratchet_proxy(
                drive_center,
                outward,
                reference,
                start_heading_degrees + angle,
            )
            handle = stroke_pose["ratchet_handle"]
            cases[
                f"heading_{start_heading_degrees:+g}deg/"
                f"stand_off_{stand_off:g}mm/stroke_endpoint_{angle:+g}deg/handle"
            ] = handle
            swept = tool_access.rotational_sweep(
                pose["ratchet_handle"],
                drive_center,
                outward,
                angle,
            )
            key = (
                f"heading_{start_heading_degrees:+g}deg/"
                f"stand_off_{stand_off:g}mm/stroke_sweep_{angle:+g}deg"
            )
            cases[key] = swept
            stroke_sweeps[key] = swept

    low_pose = _ratchet_proxy(
        socket_drive_axis_center, outward, reference, start_heading_degrees
    )
    continuous_stand_off = {}
    for name, shape in low_pose.items():
        key = f"heading_{start_heading_degrees:+g}deg/continuous_stand_off/{name}"
        swept = tool_access.translation_sweep(shape, outward * RATCHET_STANDOFF_MAX_MM)
        cases[key] = swept
        continuous_stand_off[key] = swept

    for angle in (-STROKE_DEGREES, STROKE_DEGREES):
        low_heading = _ratchet_proxy(
            socket_drive_axis_center,
            outward,
            reference,
            start_heading_degrees + angle,
        )["ratchet_handle"]
        angular = tool_access.rotational_sweep(
            low_pose["ratchet_handle"],
            socket_drive_axis_center,
            outward,
            angle,
        )
        combined = tool_access.translation_sweep(
            angular, outward * RATCHET_STANDOFF_MAX_MM
        )
        key = (
            f"heading_{start_heading_degrees:+g}deg/"
            f"continuous_stand_off_and_stroke_{angle:+g}deg"
        )
        cases[key] = combined
        stroke_sweeps[key] = combined
        # Keep the exact angled endpoint available as evidence of the pose.
        cases[
            f"heading_{start_heading_degrees:+g}deg/"
            f"stand_off_0mm/stroke_endpoint_{angle:+g}deg/handle"
        ] = low_heading

    return cases, {
        "starting_heading_degrees_from_face_reference": start_heading_degrees,
        "stand_off_range_mm": [0.0, RATCHET_STANDOFF_MAX_MM],
        "continuous_stand_off_sweeps": sorted(continuous_stand_off),
        "head_stroke_degrees": [-STROKE_DEGREES, STROKE_DEGREES],
        "continuous_stand_off_and_stroke_sweeps": sorted(stroke_sweeps),
        "all_strokes_are_analytic_aabb_rotation_bounds": True,
    }


def _stationary_ratchet_case_shapes(
    socket_drive_axis_center: cq.Vector,
    outward: cq.Vector,
    reference: cq.Vector,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    """Build four sampled stationary-handle headings and full stand-off sweeps."""
    cases: dict[str, cq.Shape] = {}
    stand_off_sweeps: list[str] = []
    for heading in COUNTERHOLD_HEADINGS_DEGREES:
        low_pose = _ratchet_proxy(socket_drive_axis_center, outward, reference, heading)
        for stand_off in (0.0, RATCHET_STANDOFF_MAX_MM):
            drive_center = socket_drive_axis_center + outward * stand_off
            pose = _ratchet_proxy(drive_center, outward, reference, heading)
            for component, shape in pose.items():
                cases[
                    f"heading_{heading:+g}deg/stand_off_{stand_off:g}mm/{component}"
                ] = shape
        for component, shape in low_pose.items():
            key = f"heading_{heading:+g}deg/continuous_stand_off/{component}"
            cases[key] = tool_access.translation_sweep(
                shape, outward * RATCHET_STANDOFF_MAX_MM
            )
            stand_off_sweeps.append(key)
    return cases, {
        "sampled_handle_heading_degrees_from_face_reference": list(
            COUNTERHOLD_HEADINGS_DEGREES
        ),
        "heading_screen_is_discrete_not_continuous": True,
        "stand_off_range_mm": [0.0, RATCHET_STANDOFF_MAX_MM],
        "continuous_stand_off_sweeps": sorted(stand_off_sweeps),
    }


def _screen(
    candidate_shapes: Mapping[str, cq.Shape],
    obstacles: Mapping[str, cq.Shape],
    floor_z_mm: float,
    *,
    excluded: tuple[str, ...] = (),
    exclusion_scope: str,
) -> dict[str, Any]:
    result = tool_access.collision_report(
        candidate_shapes,
        obstacles,
        excluded_target_ids=excluded,
        exclusion_scope=exclusion_scope,
    )
    return {
        **result,
        "floor_screen": {
            name: compact_tools._floor_bounds(shape, floor_z_mm)
            for name, shape in candidate_shapes.items()
        },
    }


def _path(shape: cq.Shape, direction: cq.Vector, distance_mm: float) -> cq.Shape:
    return tool_access.translation_sweep(shape, direction * distance_mm)


def _withdrawal_obstacles(
    obstacles: Mapping[str, cq.Shape], target_keys: Mapping[str, str]
) -> dict[str, cq.Shape]:
    """Keep washers and unrelated stacks; remove moving bolt and modeled nut."""
    excluded = {target_keys[role] for role in ("shaft", "head", "nut")}
    return {name: shape for name, shape in obstacles.items() if name not in excluded}


def _loose_hardware_obstacles(
    obstacles: Mapping[str, cq.Shape],
    target_keys: Mapping[str, str],
    moving_role: str,
    already_removed: set[str],
) -> dict[str, cq.Shape]:
    removed_roles = already_removed | {moving_role, "shaft", "head"}
    excluded = {target_keys[role] for role in removed_roles}
    return {name: shape for name, shape in obstacles.items() if name not in excluded}


def _stack_report(
    stack_id: str,
    stack: BoltStack,
    physical_obstacles: Mapping[str, cq.Shape],
    installed: Mapping[str, cq.Shape],
    floor_z_mm: float,
) -> dict[str, Any]:
    hardware = stack.hardware
    direction = cq.Vector(stack.direction).normalized()
    head_outward = -direction
    nut_outward = direction
    target_keys = _target_component_keys(installed, stack_id)
    target_shapes = {role: installed[key] for role, key in target_keys.items()}

    nut_socket, nut_drive_center, nut_socket_datum = _socket_pose(
        cq.Vector(stack.nut_seat.center), target_shapes["nut"], nut_outward
    )
    head_socket, head_drive_center, head_socket_datum = _socket_pose(
        cq.Vector(stack.head_seat.center), target_shapes["head"], head_outward
    )
    nut_reference = compact_tools._face_reference(nut_outward)
    head_reference = compact_tools._face_reference(head_outward)
    nut_ratchet_cases, nut_ratchet_case_record = _stationary_ratchet_case_shapes(
        nut_drive_center, nut_outward, nut_reference
    )

    nut_socket_screen = _screen(
        {"stationary_nut_socket": nut_socket},
        physical_obstacles,
        floor_z_mm,
        excluded=(target_keys["nut"], target_keys["shaft"]),
        exclusion_scope=(
            "The 3305A external cylinder starts at the nut bearing face and spans "
            "its 55 mm overall length. Only intended nut/shaft occupancy is "
            "excluded; the internal 12-point opening and fit are not modeled."
        ),
    )
    nut_ratchet_screen = _screen(
        nut_ratchet_cases,
        physical_obstacles,
        floor_z_mm,
        exclusion_scope=(
            "The stationary counterhold ratchet is outside the 3305A envelope. "
            "No fastener or retained geometry is excluded; four discrete handle "
            "headings and the full 0..10.8 mm stand-off range are screened."
        ),
    )
    head_socket_screen = _screen(
        {"head_side_socket": head_socket},
        physical_obstacles,
        floor_z_mm,
        excluded=(target_keys["head"], target_keys["shaft"]),
        exclusion_scope=(
            "Only the engaged target bolt head and its shaft are excluded for "
            "intended socket occupancy; washers, wood, services and other stacks "
            "remain obstacles."
        ),
    )

    ratchet_cases: dict[str, cq.Shape] = {}
    ratchet_case_record: dict[str, Any] = {}
    for heading in HEAD_RATCHET_START_HEADINGS_DEGREES:
        heading_cases, heading_record = _ratchet_case_shapes(
            head_drive_center,
            head_outward,
            head_reference,
            start_heading_degrees=heading,
        )
        ratchet_cases.update(heading_cases)
        ratchet_case_record[f"{heading:+g}deg"] = heading_record
    ratchet_screen = _screen(
        ratchet_cases,
        physical_obstacles,
        floor_z_mm,
        excluded=(target_keys["head"], target_keys["shaft"]),
        exclusion_scope=(
            "The candidate ratchet body acts through the head-side socket. Only "
            "the target head and shaft are excluded as intended drive occupancy; "
            "all washers, wood, protected services, staged panels and other "
            "hardware remain obstacles."
        ),
    )

    nut_counterhold_tool = {
        "tool_pair/stationary_nut_socket": nut_socket,
        **{
            f"tool_pair/stationary_nut_ratchet/{name}": shape
            for name, shape in nut_ratchet_cases.items()
        },
    }
    head_tool_cases = {
        "head_side_socket": head_socket,
        **{f"head_side_ratchet/{name}": shape for name, shape in ratchet_cases.items()},
    }
    nut_ratchet_vs_its_socket = _screen(
        nut_ratchet_cases,
        {"tool_pair/nut_side_socket": nut_socket},
        floor_z_mm,
        exclusion_scope=(
            "No tool is excluded. Counterhold ratchet body proxies are screened "
            "against the 3305A external envelope; drive engagement and interface "
            "contact are not represented."
        ),
    )
    ratchet_vs_head_socket = _screen(
        ratchet_cases,
        {"tool_pair/head_side_socket": head_socket},
        floor_z_mm,
        exclusion_scope=(
            "No tool is excluded. Head-side ratchet bodies are screened against "
            "their mating socket outside envelope; drive engagement and tang/recess "
            "contact are not represented."
        ),
    )
    head_tools_vs_stationary_counterhold = _screen(
        head_tool_cases,
        nut_counterhold_tool,
        floor_z_mm,
        exclusion_scope=(
            "No tool is excluded. Both 3305A sockets and both ratchet proxies are "
            "screened against each other during the head-side stroke; intended "
            "drive engagement, internal profiles and contact are not modeled."
        ),
    )

    withdrawal_mm = float(hardware.under_head_length_mm)
    shaft_sweep = _path(target_shapes["shaft"], head_outward, withdrawal_mm)
    head_sweep = _path(target_shapes["head"], head_outward, withdrawal_mm)
    shaft_obstacles = dict(_withdrawal_obstacles(physical_obstacles, target_keys))
    shaft_obstacles["tool_pair/stationary_nut_socket"] = nut_socket
    shaft_obstacles.update(
        {
            f"tool_pair/stationary_nut_ratchet/{name}": shape
            for name, shape in nut_ratchet_cases.items()
        }
    )
    shaft_screen = _screen(
        {"shaft_axial_withdrawal": shaft_sweep},
        shaft_obstacles,
        floor_z_mm,
        excluded=("tool_pair/stationary_nut_socket",),
        exclusion_scope=(
            "The loose bolt shaft passes through the stationary socket's and "
            "nut's unmodeled internal openings while it exits head-side. Those "
            "intended shaft/socket overlaps are excluded; fit and thread behavior "
            "remain unknown. Target shaft/head/nut are removed from the obstacle "
            "map; both washers, counterhold ratchet, wood, services and other "
            "stacks remain obstacles."
        ),
    )
    head_withdrawal_obstacles = dict(physical_obstacles)
    head_withdrawal_obstacles.update(nut_counterhold_tool)
    head_screen = _screen(
        {"bolt_head_axial_withdrawal": head_sweep},
        head_withdrawal_obstacles,
        floor_z_mm,
        excluded=(target_keys["head"], target_keys["shaft"]),
        exclusion_scope=(
            "The moving head and shaft are excluded from their own obstacle map. "
            "All wood, washers, services and unrelated stacks remain. The axial "
            "path begins after the nut has unthreaded; thread engagement is not modeled."
        ),
    )

    head_tool_displacement = head_outward * withdrawal_mm
    head_socket_sweep = _path(head_socket, head_outward, withdrawal_mm)
    moving_head_tool: dict[str, cq.Shape] = {
        "head_socket_axial_withdrawal": head_socket_sweep,
    }
    for name, shape in ratchet_cases.items():
        moving_head_tool[f"{name}/axial_withdrawal"] = _path(
            shape, head_outward, withdrawal_mm
        )
    moving_tool_obstacles = dict(physical_obstacles)
    moving_tool_obstacles.update(nut_counterhold_tool)
    moving_tool_screen = _screen(
        moving_head_tool,
        moving_tool_obstacles,
        floor_z_mm,
        excluded=(target_keys["head"], target_keys["shaft"]),
        exclusion_scope=(
            "Head-side socket, ratchet and bolt leave together. Only the target "
            "head/shaft are excluded as intended coupling; stationary nut socket, "
            "counterhold ratchet and all other retained geometry remain obstacles."
        ),
    )
    moving_tool_vs_counterhold = _screen(
        moving_head_tool,
        nut_counterhold_tool,
        floor_z_mm,
        exclusion_scope=(
            "No tool is excluded. Complete head-side socket/ratchet/bolt axial "
            "sweeps are screened against the retained nut-side socket and "
            "counterhold ratchet outside proxies."
        ),
    )

    nut_counterhold_exit: dict[str, cq.Shape] = {
        "nut_socket_and_loose_nut_short_axial_exit": _path(
            nut_socket, nut_outward, LOOSE_NUT_EXIT_MM
        )
    }
    for name, shape in nut_ratchet_cases.items():
        nut_counterhold_exit[f"{name}/short_axial_exit"] = _path(
            shape, nut_outward, LOOSE_NUT_EXIT_MM
        )
    nut_counterhold_exit_screen = _screen(
        nut_counterhold_exit,
        physical_obstacles,
        floor_z_mm,
        excluded=(target_keys["nut"], target_keys["shaft"], target_keys["head"]),
        exclusion_scope=(
            "After bolt withdrawal, the nut, its 3305A socket and the stationary "
            "counterhold ratchet move together only 10 mm outward. Target nut and "
            "removed bolt components are excluded; washers, wood, services and "
            "other stacks remain. Internal nut/socket fit and later capture are "
            "unverified; this is not a complete retrieval path."
        ),
    )
    nut_washer_obstacles = _loose_hardware_obstacles(
        physical_obstacles,
        target_keys,
        "nut_washer",
        {"nut"},
    )
    nut_washer_exit = _path(
        target_shapes["nut_washer"], nut_outward, LOOSE_WASHER_EXIT_MM
    )
    nut_washer_screen = _screen(
        {"nut_washer_short_axial_exit": nut_washer_exit},
        nut_washer_obstacles,
        floor_z_mm,
        exclusion_scope=(
            "This state follows 10 mm counterhold-tool/nut exit and assumes that "
            "assembly is then captured and moved clear. The nut washer moves only "
            "5 mm outward; capture and any longer retrieval are unverified."
        ),
    )
    head_washer_obstacles = _loose_hardware_obstacles(
        physical_obstacles,
        target_keys,
        "head_washer",
        {"nut", "nut_washer"},
    )
    head_washer_exit = _path(
        target_shapes["head_washer"], head_outward, LOOSE_WASHER_EXIT_MM
    )
    head_washer_screen = _screen(
        {"head_washer_short_axial_exit": head_washer_exit},
        head_washer_obstacles,
        floor_z_mm,
        exclusion_scope=(
            "After bolt/head-side tool withdrawal and nut-side counterhold/nut "
            "removal, the head washer moves only 5 mm outward from its seat. "
            "Manual capture and retrieval are unverified."
        ),
    )

    compatibility = compact_tools._stack_compatibility(stack)
    return {
        "bolt_id": stack_id,
        "hardware": {
            "candidate_sku": hardware.candidate_sku,
            "under_head_length_mm": hardware.under_head_length_mm,
            "grip_mm": round(stack.grip_mm, 6),
            "axis_direction_xyz": [round(value, 9) for value in direction.toTuple()],
            "head_outward_axis_xyz": [
                round(value, 9) for value in head_outward.toTuple()
            ],
            "nut_outward_axis_xyz": [
                round(value, 9) for value in nut_outward.toTuple()
            ],
            "delivered_bolt_selected": False,
            "wood_threads_or_spacers_modeled": False,
        },
        "nominal_stack_compatibility": compatibility,
        "nut_counterhold_socket": {
            "product": "Ko-ken 3305A-7/16",
            "outside_envelope": nut_socket_screen,
            "seat_datum": nut_socket_datum,
            "stationary_during_bolt_unthreading_and_withdrawal": True,
            "internal_profile_fit_and_hand_hold_verified": False,
        },
        "nut_counterhold_ratchet": {
            "candidate_product_id": RATCHET_PRODUCT_ID,
            "outside_envelope": nut_ratchet_screen,
            "profile_cases": nut_ratchet_case_record,
            "ratchet_vs_its_socket": nut_ratchet_vs_its_socket,
            "stationary_during_head_side_stroke_and_bolt_withdrawal": True,
            "torque_capacity_hand_hold_and_real_tool_fit_verified": False,
        },
        "head_socket_and_ratchet": {
            "head_socket_outside_envelope": head_socket_screen,
            "head_socket_seat_datum": head_socket_datum,
            "ratchet_drive_axis_center_xyz_mm_at_flush_standoff": [
                round(value, 9) for value in head_drive_center.toTuple()
            ],
            "ratchet_profile_cases": ratchet_case_record,
            "ratchet_body_and_head_strokes": ratchet_screen,
            "ratchet_vs_mating_head_socket": ratchet_vs_head_socket,
            "head_tools_vs_stationary_counterhold_tools": (
                head_tools_vs_stationary_counterhold
            ),
        },
        "bolt_withdrawal_after_unthreading": {
            "travel_mm": round(withdrawal_mm, 6),
            "axis_xyz": [round(value, 9) for value in head_outward.toTuple()],
            "shaft_path": shaft_screen,
            "head_path": head_screen,
            "head_socket_and_ratchet_path": moving_tool_screen,
            "head_tool_against_stationary_counterhold": moving_tool_vs_counterhold,
            "threads_fully_disengaged_before_axial_translation_assumed": True,
            "threading_kinematics_or_thread_fit_verified": False,
            "head_tool_displacement_xyz_mm": [
                round(value, 9) for value in head_tool_displacement.toTuple()
            ],
        },
        "post_withdrawal_loose_hardware": {
            "nut_counterhold_tool_and_nut_short_exit_mm": LOOSE_NUT_EXIT_MM,
            "nut_counterhold_tool_and_nut_exit": nut_counterhold_exit_screen,
            "nut_washer_exit_precondition": (
                "Counterhold socket, ratchet and nut are captured and moved clear "
                "after the screened 10 mm exit; this completion is unverified."
            ),
            "counterhold_tool_removal_complete_before_nut_washer_exit_assumed": True,
            "counterhold_tool_removal_complete_before_nut_washer_exit_verified": False,
            "counterhold_tool_full_capture_after_short_exit_verified": False,
            "nut_washer_short_exit_mm": LOOSE_WASHER_EXIT_MM,
            "nut_washer_exit": nut_washer_screen,
            "head_washer_short_exit_mm": LOOSE_WASHER_EXIT_MM,
            "head_washer_exit": head_washer_screen,
            "capture_and_retrieval_path_verified": False,
        },
    }


def build_head_withdrawal_report(geometry: Any) -> dict[str, Any]:
    """Screen head-side tool/bolt withdrawal on one materialized WJ-03 trial."""
    if getattr(geometry, "trial_id", None) != compact_access.TRIAL_ID:
        raise ValueError("geometry must use the frozen compact WJ-03 trial")
    stacks = getattr(geometry, "stacks", None)
    if not isinstance(stacks, Mapping) or len(stacks) != compact_tools.STACK_COUNT:
        raise ValueError(
            f"geometry must provide {compact_tools.STACK_COUNT} candidate stacks"
        )
    if any(stack_id != stack.id for stack_id, stack in stacks.items()):
        raise ValueError("stack keys must match each BoltStack.id")
    floor_z = float(geometry.floor_z_mm)
    if not math.isfinite(floor_z):
        raise ValueError("geometry.floor_z_mm must be finite")

    obstacles, _obstacle_classes, _panel_ids = compact_tools._geometry_maps(geometry)
    installed = compact_tools._flatten_shapes(
        geometry.installed_hardware, "installed_hardware"
    )
    if len(stacks) != compact_tools.STACK_COUNT:
        raise ValueError("candidate stack count changed during geometry mapping")
    records = {
        stack_id: _stack_report(
            stack_id,
            stack,
            obstacles,
            installed,
            floor_z,
        )
        for stack_id, stack in sorted(stacks.items())
    }
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": "diagnostic_only_not_acceptance",
        "source_binding": compact_tools._json_safe(geometry.source_binding),
        "source_pins": {
            "geometry_materializer_inputs": compact_tools._json_safe(
                geometry.source_pins
            ),
            "head_withdrawal_direct_inputs": _source_pins(),
            "coverage": "direct file pins only; not a recursive dependency closure",
        },
        "candidate_stack_count": len(records),
        "tool_candidates": {
            "deep_socket": {
                "product": "Ko-ken 3305A-7/16",
                "product_url": KOKEN_PRODUCT_URL,
                "overall_length_mm": KOKEN_SOCKET_LENGTH_MM,
                "maximum_outside_diameter_mm": KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
                "stud_clearance_depth_mm": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
                "drive_square": "3/8 in",
                "selected": False,
                "outer_proxy_internal_profile_or_fit_verified": False,
            },
            "head_ratchet": {
                "product": RATCHET_PRODUCT,
                "product_url": RATCHET_PRODUCT_URL,
                "primary_manufacturer_drawing_url": RATCHET_DRAWING_URL,
                "drive_square": "3/8 in",
                "drive_axis_centered_on_bolt_axis": True,
                "head_diameter_D_mm": RATCHET_HEAD_DIAMETER_MM,
                "body_plus_tang_length_T_mm": RATCHET_BODY_AND_TANG_LENGTH_MM,
                "body_thickness_H_mm": RATCHET_HEAD_THICKNESS_MM,
                "overall_length_L_mm": RATCHET_OVERALL_LENGTH_MM,
                "modeled_handle_reach_from_drive_axis_mm": RATCHET_HANDLE_REACH_MM,
                "handle_reach_basis": "L - D/2 = 164 mm from centered drive axis to handle tip; derived from drawing dimensions",
                "handle_box_width_assumption_mm": RATCHET_HANDLE_BOX_WIDTH_MM,
                "handle_box_width_basis": "D=28 mm round-head diameter reused as assumed box width; maker publishes no handle width",
                "handle_box_thickness_assumption_mm": RATCHET_HANDLE_BOX_THICKNESS_MM,
                "handle_box_thickness_basis": "H=13.7 mm body thickness reused as assumed box thickness; maker publishes no handle thickness",
                "handle_cross_section_is_published": False,
                "handle_proxy_is_guaranteed_catalog_bound": False,
                "handle_proxy": "box from drive-axis center to derived L - D/2 reach; D and H used only as labeled cross-section assumptions, not guaranteed tool bounds",
                "gear_teeth": RATCHET_GEAR_TEETH,
                "manufacturer_catalog_swing_degrees": RATCHET_CATALOG_SWING_DEGREES,
                "screened_head_strokes_degrees": [-STROKE_DEGREES, STROKE_DEGREES],
                "selected": False,
                "selector_direction_profile_and_real_tool_fit_verified": False,
            },
            "counterhold_ratchet": {
                "product": RATCHET_PRODUCT,
                "product_url": RATCHET_PRODUCT_URL,
                "primary_manufacturer_drawing_url": RATCHET_DRAWING_URL,
                "quantity_needed_for_two_socket_operation": 2,
                "drive_square": "3/8 in",
                "drive_axis_centered_on_bolt_axis": True,
                "head_diameter_D_mm": RATCHET_HEAD_DIAMETER_MM,
                "body_plus_tang_length_T_mm": RATCHET_BODY_AND_TANG_LENGTH_MM,
                "body_thickness_H_mm": RATCHET_HEAD_THICKNESS_MM,
                "overall_length_L_mm": RATCHET_OVERALL_LENGTH_MM,
                "modeled_handle_reach_from_drive_axis_mm": RATCHET_HANDLE_REACH_MM,
                "handle_reach_basis": "L - D/2 = 164 mm from centered drive axis to handle tip; derived from drawing dimensions",
                "handle_box_width_assumption_mm": RATCHET_HANDLE_BOX_WIDTH_MM,
                "handle_box_width_basis": "D=28 mm round-head diameter reused as assumed box width; maker publishes no handle width",
                "handle_box_thickness_assumption_mm": RATCHET_HANDLE_BOX_THICKNESS_MM,
                "handle_box_thickness_basis": "H=13.7 mm body thickness reused as assumed box thickness; maker publishes no handle thickness",
                "handle_cross_section_is_published": False,
                "handle_proxy_is_guaranteed_catalog_bound": False,
                "handle_proxy": "box from drive-axis center to derived L - D/2 reach; D and H used only as labeled cross-section assumptions, not guaranteed tool bounds",
                "stationary_handle_heading_samples_degrees": list(
                    COUNTERHOLD_HEADINGS_DEGREES
                ),
                "heading_samples_are_continuous_coverage": False,
                "selected": False,
                "selector_direction_profile_and_real_tool_fit_verified": False,
            },
        },
        "ratchet_socket_mating": {
            "ratchet_head_standoff_range_mm": [0.0, RATCHET_STANDOFF_MAX_MM],
            "nominal_tang_projection_from_drawing_mm": RATCHET_TANG_PROJECTION_MM,
            "nominal_tang_projection_basis": "T=24.5 mm body-plus-tang length minus H=13.7 mm body thickness",
            "range_basis": "0..T-H nominal tang projection screened because socket recess is unknown; stand-off is envelope range only, not assumed drive engagement.",
            "square_drive_nominal_sizes_match": True,
            "ratchets_required_for_two_socket_operation": 2,
            "tang_depth_recess_depth_backlash_and_clearance_verified": False,
        },
        "operation_sequence": [
            "Seat one 3305A-7/16 socket on the nut and retain it with one stationary 3725Z ratchet; seat second socket on bolt head with second 3725Z ratchet. Drive engagement and torque holding are unverified.",
            "Keep nut-side socket and counterhold ratchet stationary while head-side ratchet turns through either signed 5-degree stroke; four cardinal starting headings are sampled on both sides.",
            "Assume the nut has fully unthreaded from the ordinary through-bolt, then withdraw the bolt, head socket and ratchet axially from the head side by the modeled under-head length.",
            "After shaft withdrawal, move the counterhold socket, ratchet and loose nut together through a short 10 mm axial exit; complete capture/retrieval remains unverified.",
            "Screen 5 mm nut-washer exit only after counterhold tool/nut assembly is captured and moved clear; screen head washer after head-side tool and bolt have exited.",
        ],
        "assumptions_and_limits": [
            "Collision maps come from the compact access materializer and include finished candidate bodies, retained hardware/services and staged panels.",
            "Two candidate ratchets are modeled: stationary nut-side counterhold and head-side turning/removal tool. Each screen removes only active components that move, were already removed, or occupy intended socket/shank envelopes. Other stacks and retained geometry stay as obstacles.",
            "Socket and ratchet envelopes are external proxies. Internal 12-point/3/8-square profiles, contact, drive engagement, selector position and tolerance are not modeled.",
            "The ±5 degree handle envelopes use the shared analytic axis-aligned rotational bound. They are nominal proxies, not a continuous physical hand/tool model.",
            "Bolt turning/threading is not geometrically simulated. The straight withdrawal begins only after threads are assumed disengaged; there are no wood threads or spacers in the model.",
            "The nut stays counterheld stationary during head stroke and bolt withdrawal. Counterhold and head-side tool proxies are checked against retained geometry and each other; actual internal socket/ratchet fit, hand hold and torque are unknown.",
            "Counterhold socket/ratchet plus nut receive only 10 mm axial exit screen. Nut washer exit assumes later capture and removal of that assembly; full capture, carrying out, storage, support and operator access are not screened.",
            "Floor comparisons use the analytical global z datum from the geometry materializer; no actual floor, support or friction is represented.",
        ],
        "stacks": records,
        "release_claims": {
            "tool_selected": False,
            "physical_tool_access_established": False,
            "threading_and_bolt_withdrawal_procedure_accepted": False,
            "hardware_capture_path_verified": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }
