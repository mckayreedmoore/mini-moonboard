#!/usr/bin/env python3
"""Compare the signed corner register directly with its pinned demand exports."""

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
REGISTER = BASE / "current-corner-complete-resistance-register-attempt01"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PRODUCER_SHA256 = "756e397f7e34c05eee6dfd7b25473033c10e81d1ca3424db2ef5f9f99a1e7b10"
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
GROUP_PLANES_PER_BOLT = {"BG001": 1, "BG003": 2, "BG045": 1}
GATES = {
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
}
SOURCES = {
    "a12-rear": (
        "current-corner-native-demand-export-attempt03",
        "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    ),
    "a1-rear": (
        "current-corner-a1-rear-case-bound-export-attempt01",
        "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    ),
    "k12-rear": (
        "current-corner-k12-rear-case-bound-export-attempt01",
        "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
    ),
}
ACTION_FIELDS = {
    "source_connection_name",
    "role",
    "first",
    "second",
    "first_point_global_xyz_mm",
    "second_point_global_xyz_mm",
    "force_on_first_xyz_n",
    "force_on_second_xyz_n",
}
ROW_FIELDS = {
    "case_id",
    "load_factor",
    "source_connection_name",
    "group",
    "axis_id",
    "first_receiver",
    "second_receiver",
    "point_global_xyz_mm",
    "force_on_first_xyz_N",
    "force_on_second_xyz_N",
    "lateral_resultant_N",
    "simultaneous_outer_tie",
    "simultaneous_tie_force_magnitude_N",
    "both_same_bolt_plane_actions",
}
REGISTER_FIELDS = {
    "schema",
    "status",
    "producer_sha256",
    "source_pins",
    "plane_count",
    "plane_state_count",
    "limits",
    "rows",
    "peak_lateral_states",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_value(value, label):
    require(isinstance(value, dict), f"{label}: expected an object")
    return value


def list_value(value, label):
    require(isinstance(value, list), f"{label}: expected an array")
    return value


def text_value(value, label):
    require(isinstance(value, str) and value, f"{label}: expected nonempty text")
    return value


def finite_number(value, label):
    require(type(value) in (int, float), f"{label}: expected a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    require(finite, f"{label}: expected a finite number")
    return value


def vector(value, label):
    require(
        isinstance(value, list) and len(value) == 3, f"{label}: expected XYZ vector"
    )
    for component in value:
        finite_number(component, label)
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_json_constant(value):
    raise ValueError(f"invalid JSON number: {value}")


def parse_json(raw, label):
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON in {label}: {error}") from error


def validate_action(value, label, role):
    action = object_value(value, label)
    require(set(action) == ACTION_FIELDS, f"{label}: action schema mismatch")
    require(action["role"] == role, f"{label}: action role mismatch")
    text_value(action["source_connection_name"], f"{label} source connection")
    text_value(action["first"], f"{label} first receiver")
    text_value(action["second"], f"{label} second receiver")
    vector(action["first_point_global_xyz_mm"], f"{label} first point")
    vector(action["second_point_global_xyz_mm"], f"{label} second point")
    first = vector(action["force_on_first_xyz_n"], f"{label} first force")
    second = vector(action["force_on_second_xyz_n"], f"{label} second force")
    require(
        all(a == -b for a, b in zip(first, second, strict=True)),
        f"{label}: endpoint forces are not equal and opposite",
    )
    return action


def trusted_rows():
    """Build the expected rows only from the three hash-pinned source exports."""
    expected = {}
    pins = {}
    source_states = set()
    source_plane_names = set()

    for case, (folder, pin) in SOURCES.items():
        path = BASE / folder / "corner-demand-report.json"
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == pin, f"source pin drift: {case}")
        pins[str(path.relative_to(ROOT))] = pin
        report = object_value(parse_json(raw, str(path)), f"{case} source report")
        require(report.get("case_id") == case, f"source case mismatch: {case}")
        require(
            report.get("candidate") == CANDIDATE, f"source candidate mismatch: {case}"
        )
        require(
            report.get("geometry_revision_id") == REVISION,
            f"source revision mismatch: {case}",
        )
        require(
            report.get("actual_case_demand_usable_for_conditional_joint_checks")
            is True,
            f"source demand is not conditionally usable: {case}",
        )

        increments = list_value(report.get("increments"), f"{case} increments")
        require(
            len(increments) == len(LOAD_FACTORS),
            f"source increment count mismatch: {case}",
        )
        for expected_factor, raw_increment in zip(
            LOAD_FACTORS, increments, strict=True
        ):
            increment = object_value(raw_increment, f"{case} increment")
            factor = finite_number(increment.get("load_factor"), f"{case} load factor")
            require(factor == expected_factor, f"source load factor mismatch: {case}")
            state_key = (case, factor)
            require(
                state_key not in source_states,
                f"duplicate source state: {case} {factor}",
            )
            source_states.add(state_key)

            gates = object_value(
                increment.get("response_audit_gates"), f"{case} response gates"
            )
            require(
                set(gates) == GATES,
                f"source response gate inventory mismatch: {case} {factor}",
            )
            require(
                all(gates[name] is True for name in GATES),
                f"source response gate failed: {case} {factor}",
            )
            require(
                increment.get("all_five_corner_bodies_raw_and_interval_balance_passed")
                is True,
                f"source corner balance gate failed: {case} {factor}",
            )

            groups = object_value(
                increment.get("primary_physical_bolt_groups"),
                f"{case} physical bolt groups",
            )
            require(
                set(groups) == set(GROUP_PLANES_PER_BOLT),
                f"source group inventory mismatch: {case} {factor}",
            )
            state_axis_ids = set()
            state_action_names = set()
            group_plane_counts = {}
            for group, raw_content in groups.items():
                content = object_value(raw_content, f"{case} {group}")
                bolt_count = content.get("physical_bolt_count")
                require(
                    type(bolt_count) is int and bolt_count == 2,
                    f"source bolt count mismatch: {case} {group}",
                )
                tie_count = content.get("outer_seat_tie_count")
                require(
                    type(tie_count) is int and tie_count == 2,
                    f"source tie count mismatch: {case} {group}",
                )
                lateral_count = content.get("lateral_plane_count")
                expected_lateral_count = 2 * GROUP_PLANES_PER_BOLT[group]
                require(
                    type(lateral_count) is int
                    and lateral_count == expected_lateral_count,
                    f"source plane count mismatch: {case} {group}",
                )
                bolts = list_value(content.get("bolts"), f"{case} {group} bolts")
                require(
                    len(bolts) == 2, f"source bolt inventory mismatch: {case} {group}"
                )
                group_plane_counts[group] = 0

                for raw_bolt in bolts:
                    bolt = object_value(raw_bolt, f"{case} {group} bolt")
                    axis = text_value(bolt.get("axis_id"), f"{case} {group} axis")
                    require(
                        axis not in state_axis_ids,
                        f"duplicate source bolt axis: {case} {axis}",
                    )
                    state_axis_ids.add(axis)
                    actions = list_value(bolt.get("actions"), f"{case} {axis} actions")
                    ties = [
                        action
                        for action in actions
                        if isinstance(action, dict)
                        and action.get("role") == "physical_bolt_outer_seat_tension"
                    ]
                    planes = [
                        action
                        for action in actions
                        if isinstance(action, dict)
                        and action.get("role") == "candidate_bolt_lateral_plane"
                    ]
                    require(
                        len(ties) == 1 and len(planes) == GROUP_PLANES_PER_BOLT[group],
                        f"source bolt roles mismatch: {case} {axis}",
                    )
                    require(
                        len(actions) == 1 + len(planes),
                        f"unknown source bolt action: {case} {axis}",
                    )
                    tie = validate_action(
                        ties[0],
                        f"{case} {axis} axial tie",
                        "physical_bolt_outer_seat_tension",
                    )
                    checked_planes = [
                        validate_action(
                            plane,
                            f"{case} {axis} lateral plane",
                            "candidate_bolt_lateral_plane",
                        )
                        for plane in planes
                    ]
                    for plane in checked_planes:
                        name = plane["source_connection_name"]
                        require(
                            name not in state_action_names,
                            f"duplicate source action: {case} {name}",
                        )
                        state_action_names.add(name)
                        source_plane_names.add(name)
                        key = (case, factor, name)
                        require(
                            key not in expected,
                            f"duplicate source plane: {case} {factor} {name}",
                        )
                        expected[key] = (group, axis, plane, tie, checked_planes)
                    tie_name = tie["source_connection_name"]
                    require(
                        tie_name not in state_action_names,
                        f"duplicate source action: {case} {tie_name}",
                    )
                    state_action_names.add(tie_name)
                    group_plane_counts[group] += len(checked_planes)

            require(
                group_plane_counts
                == {group: 2 * count for group, count in GROUP_PLANES_PER_BOLT.items()},
                f"source group plane inventory mismatch: {case} {factor}",
            )
            require(
                len(state_axis_ids) == 6 and len(state_action_names) == 14,
                f"source state inventory mismatch: {case} {factor}",
            )

    require(len(source_states) == 21, "incomplete trusted source state inventory")
    require(
        len(source_plane_names) == 8,
        "trusted source must contain eight distinct planes",
    )
    require(len(expected) == 168, "incomplete trusted plane inventory")
    require(
        all(
            sum(key[2] == name for key in expected) == 21 for name in source_plane_names
        ),
        "trusted source plane missing one or more case states",
    )
    return expected, pins, source_states


def validate_register_row(value, expected):
    row = object_value(value, "register row")
    require(set(row) == ROW_FIELDS, "register row schema mismatch")
    case = text_value(row["case_id"], "register case")
    factor = finite_number(row["load_factor"], "register load factor")
    name = text_value(row["source_connection_name"], "register source connection")
    key = (case, factor, name)
    require(key in expected, "unexpected register plane")
    group, axis, action, tie, planes = expected[key]
    require(
        row["group"] == group and row["axis_id"] == axis,
        "register group or axis mismatch",
    )

    first = vector(row["force_on_first_xyz_N"], "register first force")
    second = vector(row["force_on_second_xyz_N"], "register second force")
    require(
        all(a == -b for a, b in zip(first, second, strict=True)),
        "lateral endpoint forces are not equal and opposite",
    )
    point = vector(row["point_global_xyz_mm"], "register point")
    lateral = finite_number(row["lateral_resultant_N"], "lateral resultant")
    tie_magnitude = finite_number(
        row["simultaneous_tie_force_magnitude_N"], "simultaneous tie magnitude"
    )
    require(
        lateral >= 0 and tie_magnitude >= 0,
        "register force magnitudes must be nonnegative",
    )

    row_tie = validate_action(
        row["simultaneous_outer_tie"],
        "register simultaneous axial tie",
        "physical_bolt_outer_seat_tension",
    )
    row_planes = list_value(
        row["both_same_bolt_plane_actions"], "register same-bolt planes"
    )
    require(len(row_planes) == len(planes), "register same-bolt plane count mismatch")
    row_planes = [
        validate_action(
            plane, "register same-bolt lateral plane", "candidate_bolt_lateral_plane"
        )
        for plane in row_planes
    ]

    require(
        row["first_receiver"] == action["first"], "register first receiver mismatch"
    )
    require(
        row["second_receiver"] == action["second"], "register second receiver mismatch"
    )
    require(point == action["first_point_global_xyz_mm"], "register point mismatch")
    require(
        first == action["force_on_first_xyz_n"], "register signed first force mismatch"
    )
    require(
        second == action["force_on_second_xyz_n"],
        "register signed second force mismatch",
    )
    require(row_tie == tie, "register axial tie is not from the same source state")
    require(
        row_planes == planes, "register planes are not the same bolt and source state"
    )

    magnitude = math.hypot(*first)
    source_tie_magnitude = math.hypot(
        *vector(tie["force_on_first_xyz_n"], "source tie force")
    )
    require(
        math.isfinite(magnitude) and math.isfinite(source_tie_magnitude),
        "nonfinite reconstructed magnitude",
    )
    require(
        math.isclose(lateral, magnitude, rel_tol=1e-14, abs_tol=1e-12),
        "register lateral magnitude mismatch",
    )
    require(
        math.isclose(tie_magnitude, source_tie_magnitude, rel_tol=1e-14, abs_tol=1e-12),
        "register simultaneous tie magnitude mismatch",
    )
    return key, name, magnitude, abs(lateral - magnitude)


def verify(register_value, expected, pins, source_states):
    register = object_value(register_value, "register")
    require(set(register) == REGISTER_FIELDS, "register schema mismatch")
    require(
        register["schema"] == "three_case_corner_signed_component_register/v1",
        "register schema id mismatch",
    )
    require(
        register["status"]
        == "AUTHENTICATED_CONDITIONAL_DEMANDS_COMPLETE_RESISTANCE_OPEN",
        "register status mismatch",
    )
    require(
        register["producer_sha256"] == PRODUCER_SHA256,
        "register producer SHA-256 mismatch",
    )
    require(register["source_pins"] == pins, "register source pins mismatch")
    require(
        type(register["plane_count"]) is int and register["plane_count"] == 8,
        "declared plane count mismatch",
    )
    require(
        type(register["plane_state_count"]) is int
        and register["plane_state_count"] == len(expected),
        "declared plane state count mismatch",
    )
    limits = list_value(register["limits"], "register limits")
    require(
        all(isinstance(item, str) and item for item in limits),
        "invalid register limit text",
    )

    rows = list_value(register["rows"], "register rows")
    require(len(rows) == len(expected), "register row count mismatch")
    seen = set()
    plane_rows = {}
    maximum_difference = 0.0
    for raw_row in rows:
        key, name, magnitude, difference = validate_register_row(raw_row, expected)
        require(key not in seen, "duplicate register plane state")
        seen.add(key)
        plane_rows.setdefault(name, []).append((magnitude, raw_row))
        maximum_difference = max(maximum_difference, difference)
    require(seen == expected.keys(), "missing register plane states")
    require(
        set(plane_rows) == {key[2] for key in expected},
        "register plane inventory mismatch",
    )

    computed_peaks = {}
    for name, candidates in plane_rows.items():
        maximum = max(magnitude for magnitude, _ in candidates)
        leaders = [
            (magnitude, row) for magnitude, row in candidates if magnitude == maximum
        ]
        require(len(leaders) == 1, f"ambiguous maximum source state: {name}")
        computed_peaks[name] = leaders[0]

    selected = list_value(register["peak_lateral_states"], "register peak states")
    require(len(selected) == 8, "incomplete peak inventory")
    selected_names = set()
    for raw_peak in selected:
        key, name, magnitude, _ = validate_register_row(raw_peak, expected)
        require(name not in selected_names, "duplicate peak plane")
        selected_names.add(name)
        maximum, source_row = computed_peaks[name]
        require(
            magnitude == maximum and raw_peak == source_row,
            "incorrect or mixed-state peak",
        )
    require(selected_names == set(computed_peaks), "missing or unexpected peak plane")

    return {
        "status": "PASS_SOURCE_TO_REGISTER_ONLY",
        "conditional_cases": sorted(SOURCES),
        "source_body_states": len(source_states),
        "signed_plane_states": len(seen),
        "peak_states": len(computed_peaks),
        "maximum_magnitude_difference_N": maximum_difference,
        "joint_accepted": False,
        "six_case_envelope_established": False,
    }


def expect_rejected(name, register, expected, pins, source_states, message):
    try:
        verify(register, expected, pins, source_states)
    except ValueError as error:
        require(message in str(error), f"{name} failed for the wrong reason: {error}")
        return
    raise RuntimeError(f"self-test corruption accepted: {name}")


def self_test(register, expected, pins, source_states):
    """Exercise the source, state, numeric, sign, and peak rejection paths."""
    checks = []

    bad = copy.deepcopy(register)
    bad["producer_sha256"] = "0" * 64
    checks.append(("wrong producer pin", bad, "register producer SHA-256 mismatch"))

    bad = copy.deepcopy(register)
    bad["rows"][1] = copy.deepcopy(bad["rows"][0])
    checks.append(("duplicate plane", bad, "duplicate register plane state"))

    bad = copy.deepcopy(register)
    bad["rows"] = [row for row in bad["rows"] if row["case_id"] != "k12-rear"]
    checks.append(("missing case", bad, "register row count mismatch"))

    bad = copy.deepcopy(register)
    row = bad["rows"][0]
    other_state = next(
        candidate
        for candidate in bad["rows"]
        if candidate["case_id"] == row["case_id"]
        and candidate["source_connection_name"] == row["source_connection_name"]
        and candidate["load_factor"] != row["load_factor"]
    )
    row["simultaneous_outer_tie"] = copy.deepcopy(other_state["simultaneous_outer_tie"])
    checks.append(
        ("mixed-state tie", bad, "register axial tie is not from the same source state")
    )

    bad = copy.deepcopy(register)
    row = next(item for item in bad["rows"] if item["group"] == "BG003")
    other_state = next(
        candidate
        for candidate in bad["rows"]
        if candidate["case_id"] == row["case_id"]
        and candidate["source_connection_name"] == row["source_connection_name"]
        and candidate["load_factor"] != row["load_factor"]
    )
    row["simultaneous_outer_tie"] = copy.deepcopy(other_state["simultaneous_outer_tie"])
    checks.append(
        (
            "mixed-state BG003 tie",
            bad,
            "register axial tie is not from the same source state",
        )
    )

    bad = copy.deepcopy(register)
    row = next(
        item
        for item in bad["rows"]
        if item["group"] == "BG003" and item["load_factor"] == LOAD_FACTORS[0]
    )
    other_state = next(
        candidate
        for candidate in bad["rows"]
        if candidate["case_id"] == row["case_id"]
        and candidate["source_connection_name"] == row["source_connection_name"]
        and candidate["load_factor"] != row["load_factor"]
    )
    row["both_same_bolt_plane_actions"] = copy.deepcopy(
        other_state["both_same_bolt_plane_actions"]
    )
    checks.append(
        (
            "mixed-state BG003 planes",
            bad,
            "register planes are not the same bolt and source state",
        )
    )

    bad = copy.deepcopy(register)
    peak = bad["peak_lateral_states"][0]
    lesser = min(
        (
            row
            for row in bad["rows"]
            if row["source_connection_name"] == peak["source_connection_name"]
        ),
        key=lambda row: row["load_factor"],
    )
    bad["peak_lateral_states"][0] = copy.deepcopy(lesser)
    checks.append(("wrong peak", bad, "incorrect or mixed-state peak"))

    bad = copy.deepcopy(register)
    bad["rows"][0]["force_on_first_xyz_N"][0] = math.nan
    checks.append(
        ("nonfinite vector", bad, "register first force: expected a finite number")
    )

    bad = copy.deepcopy(register)
    bad["rows"][0]["lateral_resultant_N"] = math.inf
    checks.append(
        ("nonfinite magnitude", bad, "lateral resultant: expected a finite number")
    )

    bad = copy.deepcopy(register)
    row = bad["rows"][0]
    row["force_on_second_xyz_N"] = row["force_on_first_xyz_N"].copy()
    checks.append(
        ("endpoint sign", bad, "lateral endpoint forces are not equal and opposite")
    )

    bad = copy.deepcopy(register)
    bad["rows"][0]["load_factor"] = True
    checks.append(
        ("boolean load factor", bad, "register load factor: expected a finite number")
    )

    for name, mutation, message in checks:
        expect_rejected(name, mutation, expected, pins, source_states, message)
    return len(checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    try:
        require(
            hashlib.sha256((REGISTER / "produce.py").read_bytes()).hexdigest()
            == PRODUCER_SHA256,
            "register producer source pin drift",
        )
        expected, pins, source_states = trusted_rows()
        register_path = REGISTER / "signed-demands.json"
        register = parse_json(register_path.read_bytes(), str(register_path))
        summary = verify(register, expected, pins, source_states)
        if arguments.self_test:
            summary["corruption_checks_rejected"] = self_test(
                register, expected, pins, source_states
            )
    except (OSError, TypeError, KeyError, ValueError) as error:
        print(f"FAIL_SOURCE_TO_REGISTER: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
