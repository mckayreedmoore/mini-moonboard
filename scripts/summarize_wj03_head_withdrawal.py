"""Summarize consistent discrete tool-heading routes in a WJ-03 report.

This is a pure JSON postprocessor. A proxy-clear route is not physical tool
access, accepted assembly procedure, or capture/torque/threading verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "wood_joint_wj03_head_withdrawal/v1"
TRIAL_ID = "compact_bridge_rear_bevel_4x6_spine_137_7"
EXPECTED_STACK_COUNT = 20
EXPECTED_HEADINGS = (0.0, 90.0, 180.0, 270.0)
EXPECTED_STROKES = (-5.0, 5.0)
EXPECTED_STANDOFFS_MM = (0.0, 10.8)
HIT_TOLERANCE_MM3 = 1e-6
FLOOR_TOLERANCE_MM = 1e-6
FLOOR_SERIALIZATION_QUANTUM_MM = 1e-6


class ReportSchemaError(ValueError):
    """Raised when the input does not match the frozen report contract."""


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReportSchemaError(f"{path} must be an object")
    return value


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReportSchemaError(f"{path} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ReportSchemaError(f"{path} must be finite")
    return number


def _at(obj: dict[str, Any], path: str) -> dict[str, Any]:
    current: Any = obj
    parts = path.split(".")
    for index, key in enumerate(parts):
        parent = _mapping(current, ".".join(parts[:index]) or "report")
        if key not in parent:
            raise ReportSchemaError(
                f"missing required field {'.'.join(parts[: index + 1])}"
            )
        current = parent[key]
    return _mapping(current, path)


def _signed(value: float) -> str:
    return f"{value:+g}"


def _plain(value: float) -> str:
    return f"{value:g}"


def _expected_head_shapes(
    profile: dict[str, Any], heading: float, stroke: float
) -> set[str]:
    heading_key = f"{_signed(heading)}deg"
    case = _mapping(
        profile.get(heading_key), f"head_ratchet.profile_cases.{heading_key}"
    )
    if (
        _number(case.get("starting_heading_degrees_from_face_reference"), heading_key)
        != heading
    ):
        raise ReportSchemaError(f"head profile heading mismatch at {heading_key}")
    if tuple(case.get("stand_off_range_mm", ())) != EXPECTED_STANDOFFS_MM:
        raise ReportSchemaError(f"head stand-off range mismatch at {heading_key}")
    if tuple(case.get("head_stroke_degrees", ())) != EXPECTED_STROKES:
        raise ReportSchemaError(f"head stroke range mismatch at {heading_key}")

    base = f"heading_{_signed(heading)}deg"
    result: set[str] = set()
    for stand_off in EXPECTED_STANDOFFS_MM:
        pose = f"{base}/stand_off_{_plain(stand_off)}mm"
        result.update(f"{pose}/{part}" for part in ("ratchet_head", "ratchet_handle"))
        result.add(f"{pose}/stroke_endpoint_{_signed(stroke)}deg/handle")
        result.add(f"{pose}/stroke_sweep_{_signed(stroke)}deg")

    continuous_standoff = set(case.get("continuous_stand_off_sweeps", ()))
    expected_continuous = {
        f"{base}/continuous_stand_off/{part}"
        for part in ("ratchet_head", "ratchet_handle")
    }
    if continuous_standoff != expected_continuous:
        raise ReportSchemaError(f"head stand-off sweep keys mismatch at {heading_key}")
    result.update(continuous_standoff)

    combined_sweeps = set(case.get("continuous_stand_off_and_stroke_sweeps", ()))
    expected_sweeps = {
        f"{base}/continuous_stand_off_and_stroke_{_signed(value)}deg"
        for value in EXPECTED_STROKES
    }
    expected_sweeps.update(
        f"{base}/stand_off_{_plain(stand_off)}mm/stroke_sweep_{_signed(value)}deg"
        for stand_off in EXPECTED_STANDOFFS_MM
        for value in EXPECTED_STROKES
    )
    if combined_sweeps != expected_sweeps:
        raise ReportSchemaError(f"head combined-sweep keys mismatch at {heading_key}")
    result.add(f"{base}/continuous_stand_off_and_stroke_{_signed(stroke)}deg")
    return result


def _nut_shapes(
    heading: float, stand_offs: tuple[float, ...] = EXPECTED_STANDOFFS_MM
) -> set[str]:
    base = f"heading_{_signed(heading)}deg"
    result = {
        f"{base}/stand_off_{_plain(stand_off)}mm/{part}"
        for stand_off in stand_offs
        for part in ("ratchet_head", "ratchet_handle")
    }
    result.update(
        f"{base}/continuous_stand_off/{part}"
        for part in ("ratchet_head", "ratchet_handle")
    )
    return result


def _validate_screen_family(
    screen_any: Any, expected_candidates: set[str], context: str
) -> None:
    screen = _mapping(screen_any, context)
    hits = _mapping(screen.get("external_envelope_hits_mm3"), f"{context}.hits")
    floor = _mapping(screen.get("floor_screen"), f"{context}.floor_screen")
    if set(floor) != expected_candidates:
        raise ReportSchemaError(
            f"{context} candidate family mismatch: "
            f"missing={sorted(expected_candidates - set(floor))}, "
            f"unexpected={sorted(set(floor) - expected_candidates)}"
        )
    if set(hits) - expected_candidates:
        raise ReportSchemaError(
            f"{context} hit map has unknown candidates: "
            f"{sorted(set(hits) - expected_candidates)}"
        )
    for candidate, obstacle_map in hits.items():
        obstacles = _mapping(obstacle_map, f"{context}.hits.{candidate}")
        if not obstacles:
            raise ReportSchemaError(
                f"{context}.hits.{candidate} must contain at least one obstacle"
            )


def _validate_report(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if report.get("schema") != SCHEMA:
        raise ReportSchemaError(f"schema must be {SCHEMA!r}")
    if report.get("trial_id") != TRIAL_ID:
        raise ReportSchemaError(f"trial_id must be {TRIAL_ID!r}")
    stacks = _mapping(report.get("stacks"), "stacks")
    if report.get("candidate_stack_count") != EXPECTED_STACK_COUNT:
        raise ReportSchemaError("candidate_stack_count must be 20")
    if len(stacks) != EXPECTED_STACK_COUNT:
        raise ReportSchemaError("stacks must contain exactly 20 records")

    tool_candidates = _mapping(report.get("tool_candidates"), "tool_candidates")
    head_tool = _mapping(
        tool_candidates.get("head_ratchet"), "tool_candidates.head_ratchet"
    )
    if tuple(head_tool.get("screened_head_strokes_degrees", ())) != EXPECTED_STROKES:
        raise ReportSchemaError("head ratchet must screen signed -5/+5 degree strokes")
    if (
        head_tool.get("selected") is not False
        or head_tool.get("handle_proxy_is_guaranteed_catalog_bound") is not False
    ):
        raise ReportSchemaError("head ratchet must remain an unselected proxy")
    counterhold_tool = _mapping(
        tool_candidates.get("counterhold_ratchet"),
        "tool_candidates.counterhold_ratchet",
    )
    nut_headings = tuple(
        counterhold_tool.get("stationary_handle_heading_samples_degrees", ())
    )
    if nut_headings != EXPECTED_HEADINGS:
        raise ReportSchemaError("nut counterhold must contain four cardinal headings")
    if (
        counterhold_tool.get("selected") is not False
        or counterhold_tool.get("heading_samples_are_continuous_coverage") is not False
    ):
        raise ReportSchemaError("nut counterhold headings must remain discrete proxies")
    socket_tool = _mapping(
        tool_candidates.get("deep_socket"), "tool_candidates.deep_socket"
    )
    if (
        socket_tool.get("selected") is not False
        or socket_tool.get("outer_proxy_internal_profile_or_fit_verified") is not False
    ):
        raise ReportSchemaError(
            "socket must remain an unselected outside-envelope proxy"
        )
    mating = _mapping(report.get("ratchet_socket_mating"), "ratchet_socket_mating")
    stand_offs = tuple(mating.get("ratchet_head_standoff_range_mm", ()))
    if stand_offs != EXPECTED_STANDOFFS_MM:
        raise ReportSchemaError("ratchet/socket stand-off range mismatch")

    claims = _mapping(report.get("release_claims"), "release_claims")
    if not claims or any(claim is not False for claim in claims.values()):
        raise ReportSchemaError("all release claims must remain false")

    for stack_id, stack_any in stacks.items():
        stack = _mapping(stack_any, f"stacks.{stack_id}")
        if stack.get("bolt_id") != stack_id:
            raise ReportSchemaError(f"stack key/id mismatch at {stack_id}")
        if _at(stack, "hardware").get("delivered_bolt_selected") is not False:
            raise ReportSchemaError(
                f"delivered bolt must remain unselected at {stack_id}"
            )
        head = _at(stack, "head_socket_and_ratchet")
        head_profile = _mapping(
            head.get("ratchet_profile_cases"), f"{stack_id}.head profile"
        )
        if set(head_profile) != {f"{_signed(h)}deg" for h in EXPECTED_HEADINGS}:
            raise ReportSchemaError(f"head heading families mismatch at {stack_id}")
        for heading in EXPECTED_HEADINGS:
            _expected_head_shapes(head_profile, heading, EXPECTED_STROKES[0])
        all_head_shapes = set().union(
            *(
                _expected_head_shapes(head_profile, heading, stroke)
                for heading in EXPECTED_HEADINGS
                for stroke in EXPECTED_STROKES
            )
        )

        nut = _at(stack, "nut_counterhold_ratchet")
        nut_profile = _mapping(nut.get("profile_cases"), f"{stack_id}.nut profile")
        if (
            tuple(
                nut_profile.get(
                    "sampled_handle_heading_degrees_from_face_reference", ()
                )
            )
            != EXPECTED_HEADINGS
        ):
            raise ReportSchemaError(
                f"nut counterhold heading families mismatch at {stack_id}"
            )
        if tuple(nut_profile.get("stand_off_range_mm", ())) != EXPECTED_STANDOFFS_MM:
            raise ReportSchemaError(
                f"nut counterhold stand-off range mismatch at {stack_id}"
            )
        if (
            _at(stack, "nut_counterhold_socket").get(
                "internal_profile_fit_and_hand_hold_verified"
            )
            is not False
        ):
            raise ReportSchemaError(
                f"nut socket fit must remain unverified at {stack_id}"
            )
        if nut.get("torque_capacity_hand_hold_and_real_tool_fit_verified") is not False:
            raise ReportSchemaError(
                f"counterhold tool fit must remain unverified at {stack_id}"
            )
        withdrawal = _at(stack, "bolt_withdrawal_after_unthreading")
        if withdrawal.get("threading_kinematics_or_thread_fit_verified") is not False:
            raise ReportSchemaError(f"threading must remain unverified at {stack_id}")
        loose_hardware = _at(stack, "post_withdrawal_loose_hardware")
        if loose_hardware.get("capture_and_retrieval_path_verified") is not False:
            raise ReportSchemaError(f"capture must remain unverified at {stack_id}")

        all_nut_shapes = set().union(
            *(_nut_shapes(heading) for heading in EXPECTED_HEADINGS)
        )
        all_head_axial = _head_withdrawal_candidates(
            all_head_shapes, with_axial_exit=True
        )
        _validate_screen_family(
            _at(stack, "nut_counterhold_socket.outside_envelope"),
            {"stationary_nut_socket"},
            f"{stack_id}.nut_counterhold_socket.outside_envelope",
        )
        _validate_screen_family(
            _at(stack, "nut_counterhold_ratchet.outside_envelope"),
            all_nut_shapes,
            f"{stack_id}.nut_counterhold_ratchet.outside_envelope",
        )
        _validate_screen_family(
            _at(stack, "nut_counterhold_ratchet.ratchet_vs_its_socket"),
            all_nut_shapes,
            f"{stack_id}.nut_counterhold_ratchet.ratchet_vs_its_socket",
        )
        _validate_screen_family(
            _at(stack, "head_socket_and_ratchet.head_socket_outside_envelope"),
            {"head_side_socket"},
            f"{stack_id}.head_socket_outside_envelope",
        )
        for path in (
            "head_socket_and_ratchet.ratchet_body_and_head_strokes",
            "head_socket_and_ratchet.ratchet_vs_mating_head_socket",
        ):
            _validate_screen_family(
                _at(stack, path), all_head_shapes, f"{stack_id}.{path}"
            )
        _validate_screen_family(
            _at(
                stack,
                "head_socket_and_ratchet.head_tools_vs_stationary_counterhold_tools",
            ),
            {"head_side_socket"}
            | {f"head_side_ratchet/{pose}" for pose in all_head_shapes},
            f"{stack_id}.head_tools_vs_stationary_counterhold_tools",
        )
        withdrawal = _at(stack, "bolt_withdrawal_after_unthreading")
        for path, expected in (
            ("shaft_path", {"shaft_axial_withdrawal"}),
            ("head_path", {"bolt_head_axial_withdrawal"}),
            ("head_socket_and_ratchet_path", all_head_axial),
            ("head_tool_against_stationary_counterhold", all_head_axial),
        ):
            _validate_screen_family(
                _at(withdrawal, path), expected, f"{stack_id}.{path}"
            )
        loose_hardware = _at(stack, "post_withdrawal_loose_hardware")
        for path, expected in (
            (
                "nut_counterhold_tool_and_nut_exit",
                {"nut_socket_and_loose_nut_short_axial_exit"}
                | {f"{pose}/short_axial_exit" for pose in all_nut_shapes},
            ),
            ("nut_washer_exit", {"nut_washer_short_axial_exit"}),
            ("head_washer_exit", {"head_washer_short_axial_exit"}),
        ):
            _validate_screen_family(
                _at(loose_hardware, path), expected, f"{stack_id}.{path}"
            )
    return stacks


def _screen_failures(
    screen_any: Any,
    candidates: set[str],
    context: str,
    *,
    known_alternatives: set[str] | None = None,
    selected_alternatives: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    screen = _mapping(screen_any, context)
    hits = _mapping(screen.get("external_envelope_hits_mm3"), f"{context}.hits")
    floor = _mapping(screen.get("floor_screen"), f"{context}.floor_screen")
    aggregate_clear = screen.get("external_envelope_clear")
    if not isinstance(aggregate_clear, bool):
        raise ReportSchemaError(f"{context}.external_envelope_clear must be boolean")
    if aggregate_clear != (not hits):
        raise ReportSchemaError(
            f"{context} aggregate collision flag disagrees with hit map"
        )
    if not candidates:
        raise ReportSchemaError(f"{context} selected no candidate poses")
    missing = candidates - set(floor)
    if missing:
        raise ReportSchemaError(
            f"{context} floor rows missing candidate poses: {sorted(missing)}"
        )
    if set(hits) - set(floor):
        raise ReportSchemaError(
            f"{context} hit map has candidate poses without floor rows"
        )
    for candidate, obstacle_any in hits.items():
        obstacle_map = _mapping(obstacle_any, f"{context}.hits.{candidate}")
        if not obstacle_map:
            raise ReportSchemaError(
                f"{context}.hits.{candidate} must contain at least one obstacle"
            )
        for obstacle, volume_any in obstacle_map.items():
            volume = _number(volume_any, f"{context}.hits.{candidate}.{obstacle}")
            if volume <= HIT_TOLERANCE_MM3:
                raise ReportSchemaError(
                    f"{context} contains a sub-tolerance collision row for {candidate}"
                )

    failures: dict[str, list[dict[str, Any]]] = {
        "envelope_intersection_proxy": [],
        "below_analytical_floor_proxy": [],
        "floor_threshold_rounding_ambiguous_proxy": [],
    }
    known_alternatives = known_alternatives or set()
    selected_alternatives = selected_alternatives or set()
    for candidate in sorted(candidates):
        floor_row = _mapping(floor[candidate], f"{context}.floor_screen.{candidate}")
        below = floor_row.get("below_analytical_floor")
        if not isinstance(below, bool):
            raise ReportSchemaError(
                f"{context}.floor_screen.{candidate}.below_analytical_floor must be boolean"
            )
        minimum_z = _number(
            floor_row.get("minimum_z_mm"),
            f"{context}.floor_screen.{candidate}.minimum_z_mm",
        )
        floor_z = _number(
            floor_row.get("floor_z_mm"),
            f"{context}.floor_screen.{candidate}.floor_z_mm",
        )
        clearance = _number(
            floor_row.get("clearance_mm"),
            f"{context}.floor_screen.{candidate}.clearance_mm",
        )
        penetration = _number(
            floor_row.get("penetration_depth_mm"),
            f"{context}.floor_screen.{candidate}.penetration_depth_mm",
        )
        half_quantum = FLOOR_SERIALIZATION_QUANTUM_MM / 2
        position_difference = minimum_z - floor_z
        position_difference_low = position_difference - FLOOR_SERIALIZATION_QUANTUM_MM
        position_difference_high = position_difference + FLOOR_SERIALIZATION_QUANTUM_MM
        clearance_low = clearance - half_quantum
        clearance_high = clearance + half_quantum
        if (
            clearance_high < position_difference_low
            or clearance_low > position_difference_high
        ):
            raise ReportSchemaError(
                f"{context}.floor_screen.{candidate} clearance disagrees with min_z-floor_z"
            )
        possible_below = clearance_low < -FLOOR_TOLERANCE_MM
        possible_not_below = clearance_high >= -FLOOR_TOLERANCE_MM
        if (below and not possible_below) or (not below and not possible_not_below):
            raise ReportSchemaError(
                f"{context}.floor_screen.{candidate} below-floor flag disagrees with tolerance"
            )
        if penetration < 0:
            raise ReportSchemaError(
                f"{context}.floor_screen.{candidate} penetration must be nonnegative"
            )
        possible_penetration_low = max(0.0, -clearance_high)
        possible_penetration_high = max(0.0, -clearance_low)
        reported_penetration_low = penetration - half_quantum
        reported_penetration_high = penetration + half_quantum
        if (
            reported_penetration_high < possible_penetration_low
            or reported_penetration_low > possible_penetration_high
        ):
            raise ReportSchemaError(
                f"{context}.floor_screen.{candidate} penetration disagrees with clearance"
            )
        threshold_ambiguous = possible_below and possible_not_below
        if below:
            failures["below_analytical_floor_proxy"].append(
                {
                    "candidate": candidate,
                    "floor_threshold_rounding_ambiguous": threshold_ambiguous,
                    **floor_row,
                }
            )
        if threshold_ambiguous:
            failures["floor_threshold_rounding_ambiguous_proxy"].append(
                {
                    "candidate": candidate,
                    "reported_below_analytical_floor": below,
                    **floor_row,
                }
            )

        obstacles = _mapping(hits.get(candidate, {}), f"{context}.hits.{candidate}")
        for obstacle, volume_any in sorted(obstacles.items()):
            volume = _number(volume_any, f"{context}.hits.{candidate}.{obstacle}")
            if volume <= HIT_TOLERANCE_MM3:
                raise ReportSchemaError(
                    f"{context} contains a sub-tolerance collision row for {candidate}"
                )
            if (
                known_alternatives
                and obstacle in known_alternatives
                and obstacle not in selected_alternatives
            ):
                continue
            if (
                selected_alternatives
                and obstacle.startswith("tool_pair/")
                and obstacle not in known_alternatives
            ):
                raise ReportSchemaError(
                    f"{context} contains unknown paired tool obstacle {obstacle}"
                )
            failures["envelope_intersection_proxy"].append(
                {
                    "candidate": candidate,
                    "obstacle": obstacle,
                    "intersection_mm3": volume,
                }
            )
    return {name: values for name, values in failures.items() if values}


def _pair_failures(
    screen_any: Any,
    candidates: set[str],
    obstacles: set[str],
    all_obstacles: set[str],
    context: str,
) -> dict[str, list[dict[str, Any]]]:
    return _screen_failures(
        screen_any,
        candidates,
        context,
        known_alternatives=all_obstacles,
        selected_alternatives=obstacles,
    )


def _head_withdrawal_candidates(
    head_shapes: set[str], *, with_axial_exit: bool = False
) -> set[str]:
    suffix = "/axial_withdrawal" if with_axial_exit else ""
    return {"head_socket_axial_withdrawal"} | {
        f"{shape}{suffix}" for shape in head_shapes
    }


def _nut_tool_ids(nut_shapes: set[str]) -> set[str]:
    return {"tool_pair/stationary_nut_socket"} | {
        f"tool_pair/stationary_nut_ratchet/{shape}" for shape in nut_shapes
    }


def _route_failures(
    stack: dict[str, Any], head_heading: float, stroke: float, nut_heading: float
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    head = _at(stack, "head_socket_and_ratchet")
    nut = _at(stack, "nut_counterhold_ratchet")
    head_cases = _mapping(head.get("ratchet_profile_cases"), "head profile")
    head_shapes = _expected_head_shapes(head_cases, head_heading, stroke)
    all_head_shapes = set().union(
        *(
            _expected_head_shapes(head_cases, heading, sign)
            for heading in EXPECTED_HEADINGS
            for sign in EXPECTED_STROKES
        )
    )
    if not head_shapes <= all_head_shapes:
        raise ReportSchemaError("selected head route not in all head families")
    nut_shapes = _nut_shapes(nut_heading)
    all_nut_shapes = set().union(
        *(_nut_shapes(heading) for heading in EXPECTED_HEADINGS)
    )
    pair_candidates = {"head_side_socket"} | {
        f"head_side_ratchet/{shape}" for shape in head_shapes
    }
    pair_alt_candidates = {"head_side_socket"} | {
        f"head_side_ratchet/{shape}" for shape in all_head_shapes
    }
    selected_nut_ids = _nut_tool_ids(nut_shapes)
    all_nut_ids = _nut_tool_ids(all_nut_shapes)
    head_withdraw_candidates_axial = _head_withdrawal_candidates(
        head_shapes, with_axial_exit=True
    )

    checks: dict[str, dict[str, list[dict[str, Any]]]] = {}

    def plain(name: str, screen: Any, poses: set[str]) -> None:
        failures = _screen_failures(screen, poses, name)
        if failures:
            checks[name] = failures

    def with_nut_heading(name: str, screen: Any, poses: set[str]) -> None:
        failures = _screen_failures(
            screen,
            poses,
            name,
            known_alternatives=all_nut_ids,
            selected_alternatives=selected_nut_ids,
        )
        if failures:
            checks[name] = failures

    plain(
        "nut_socket_seating",
        _at(stack, "nut_counterhold_socket.outside_envelope"),
        {"stationary_nut_socket"},
    )
    plain(
        "head_socket_seating",
        _at(head, "head_socket_outside_envelope"),
        {"head_side_socket"},
    )
    plain(
        "nut_counterhold_ratchet_environment",
        _at(nut, "outside_envelope"),
        nut_shapes,
    )
    plain(
        "nut_counterhold_ratchet_vs_socket",
        _at(nut, "ratchet_vs_its_socket"),
        nut_shapes,
    )
    plain(
        "head_ratchet_signed_stroke_environment",
        _at(head, "ratchet_body_and_head_strokes"),
        head_shapes,
    )
    plain(
        "head_ratchet_vs_socket",
        _at(head, "ratchet_vs_mating_head_socket"),
        head_shapes,
    )
    pair = _pair_failures(
        _at(head, "head_tools_vs_stationary_counterhold_tools"),
        pair_candidates,
        selected_nut_ids,
        all_nut_ids,
        "head_tools_vs_stationary_counterhold_tools",
    )
    if pair:
        checks["head_tools_vs_stationary_counterhold_tools"] = pair

    withdrawal = _at(stack, "bolt_withdrawal_after_unthreading")
    with_nut_heading(
        "shaft_axial_withdrawal",
        _at(withdrawal, "shaft_path"),
        {"shaft_axial_withdrawal"},
    )
    with_nut_heading(
        "head_axial_withdrawal",
        _at(withdrawal, "head_path"),
        {"bolt_head_axial_withdrawal"},
    )
    with_nut_heading(
        "head_socket_ratchet_axial_withdrawal",
        _at(withdrawal, "head_socket_and_ratchet_path"),
        head_withdraw_candidates_axial,
    )
    pair = _pair_failures(
        _at(withdrawal, "head_tool_against_stationary_counterhold"),
        head_withdraw_candidates_axial,
        selected_nut_ids,
        all_nut_ids,
        "head_tool_against_stationary_counterhold",
    )
    if pair:
        checks["head_tool_against_stationary_counterhold"] = pair

    loose = _at(stack, "post_withdrawal_loose_hardware")
    nut_exit_shapes = {"nut_socket_and_loose_nut_short_axial_exit"} | {
        f"{shape}/short_axial_exit" for shape in nut_shapes
    }
    plain(
        "nut_socket_ratchet_nut_short_exit",
        _at(loose, "nut_counterhold_tool_and_nut_exit"),
        nut_exit_shapes,
    )
    plain(
        "nut_washer_short_exit",
        _at(loose, "nut_washer_exit"),
        {"nut_washer_short_axial_exit"},
    )
    plain(
        "head_washer_short_exit",
        _at(loose, "head_washer_exit"),
        {"head_washer_short_axial_exit"},
    )

    # Pair screens contain all four discrete nut headings. We selected one
    # heading above; validate all alternatives exist so omissions cannot pass.
    for pair_path in (
        "head_socket_and_ratchet.head_tools_vs_stationary_counterhold_tools",
        "bolt_withdrawal_after_unthreading.head_tool_against_stationary_counterhold",
    ):
        screen = _at(stack, pair_path)
        floor = _mapping(screen.get("floor_screen"), pair_path + ".floor_screen")
        expected_all_candidates = (
            pair_alt_candidates
            if pair_path
            == "head_socket_and_ratchet.head_tools_vs_stationary_counterhold_tools"
            else _head_withdrawal_candidates(all_head_shapes, with_axial_exit=True)
        )
        missing = expected_all_candidates - set(floor)
        if missing:
            raise ReportSchemaError(
                f"{pair_path} missing head heading families: {sorted(missing)}"
            )
    return checks


def summarize_report(
    report: dict[str, Any], source_report_sha256: str | None = None
) -> dict[str, Any]:
    """Return per-stack proxy results without equating overlaps to blockage."""
    stacks = _validate_report(_mapping(report, "report"))
    stack_summaries = []
    total_clear = 0
    total_pending_shaft = 0
    for stack_id, stack in sorted(stacks.items()):
        feasible: list[dict[str, float]] = []
        pending_shaft: list[dict[str, float]] = []
        nonclear_check_counts: Counter[str] = Counter()
        nonclear_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
        raw_shaft_failures = _screen_failures(
            _at(stack, "bolt_withdrawal_after_unthreading.shaft_path"),
            {"shaft_axial_withdrawal"},
            f"{stack_id}.raw_shaft_path_proxy",
        )
        for head_heading in EXPECTED_HEADINGS:
            for stroke in EXPECTED_STROKES:
                for nut_heading in EXPECTED_HEADINGS:
                    failures = _route_failures(stack, head_heading, stroke, nut_heading)
                    shaft_proxy = failures.pop("shaft_axial_withdrawal", None)
                    combo = {
                        "head_heading_degrees": head_heading,
                        "head_stroke_degrees": stroke,
                        "nut_counterhold_heading_degrees": nut_heading,
                    }
                    shaft_envelope_intersections = bool(
                        shaft_proxy and shaft_proxy.get("envelope_intersection_proxy")
                    )
                    if shaft_proxy:
                        shaft_floor_diagnostics = {
                            check: rows
                            for check, rows in shaft_proxy.items()
                            if check != "envelope_intersection_proxy"
                        }
                        if shaft_floor_diagnostics:
                            failures["shaft_axial_withdrawal_floor"] = (
                                shaft_floor_diagnostics
                            )
                    if not failures and not shaft_envelope_intersections:
                        feasible.append(combo)
                        continue
                    if not failures and shaft_envelope_intersections:
                        pending_shaft.append(combo)
                        continue
                    for check_name, rows in failures.items():
                        nonclear_check_counts[check_name] += 1
                        if len(nonclear_examples[check_name]) < 3:
                            nonclear_examples[check_name].append(
                                {"combination": combo, "details": rows}
                            )
        total_clear += len(feasible)
        total_pending_shaft += len(pending_shaft)
        stack_summaries.append(
            {
                "stack_id": stack_id,
                "combination_count": len(EXPECTED_HEADINGS)
                * len(EXPECTED_STROKES)
                * len(EXPECTED_HEADINGS),
                "proxy_clear_combination_count": len(feasible),
                "proxy_clear_combinations": feasible,
                "candidate_combinations_clear_except_shaft_check_count": len(
                    pending_shaft
                ),
                "candidate_combinations_clear_except_shaft_check": pending_shaft,
                "nonclear_combination_count": 32 - len(feasible) - len(pending_shaft),
                "combinations_with_nonclear_proxy_by_check": dict(
                    sorted(nonclear_check_counts.items())
                ),
                "nonclear_proxy_examples_by_check": dict(
                    sorted(nonclear_examples.items())
                ),
                "raw_shaft_path_aabb_proxy_intersections": raw_shaft_failures,
                "raw_shaft_path_requires_exact_cylinder_supplement": bool(
                    raw_shaft_failures
                ),
            }
        )

    return {
        "schema": "wood_joint_wj03_head_withdrawal_summary/v1",
        "source_report_schema": SCHEMA,
        "source_report_sha256": source_report_sha256,
        "source_pin_coverage": _at(report, "source_pins").get("coverage"),
        "trial_id": TRIAL_ID,
        "stack_count": len(stack_summaries),
        "heading_combinations_per_stack": 32,
        "proxy_clear_combination_count": total_clear,
        "candidate_combinations_clear_except_shaft_check_count": total_pending_shaft,
        "proxy_clear_stack_count": sum(
            item["proxy_clear_combination_count"] > 0 for item in stack_summaries
        ),
        "interpretation": (
            "A listed combination clears only its matching nominal geometry/tool "
            "proxy poses and floor rows. Mutually exclusive heading alternatives "
            "are not combined into a route. Candidate combinations that pass all "
            "other checks remain pending an exact coaxial shaft-withdrawal sweep "
            "when the conservative shaft AABB overlaps. Such proxy intersections "
            "are not proof of physical blockage. No result establishes physical "
            "fit, capture/retrieval, torque, threading, or accepted procedure."
        ),
        "shaft_withdrawal_status": "exact_coaxial_cylinder_supplement_pending",
        "limitations": {
            "tool_selected": False,
            "physical_tool_fit_verified": False,
            "capture_and_retrieval_verified": False,
            "torque_verified": False,
            "threading_or_thread_fit_verified": False,
            "floor_is_analytical_plane_only": True,
            "head_heading_samples_are_discrete": True,
            "nut_counterhold_heading_samples_are_discrete": True,
        },
        "stacks": stack_summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="frozen WJ-03 head-withdrawal JSON")
    parser.add_argument(
        "--output", type=Path, help="summary JSON path (defaults to stdout)"
    )
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(raw)
    summary = summarize_report(report, hashlib.sha256(raw).hexdigest())
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
