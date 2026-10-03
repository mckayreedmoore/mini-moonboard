#!/usr/bin/env python3
"""Independently replay the retained-bolt reference arithmetic.

This oracle uses only the Python standard library. It reads the frozen current
load-path JSON and raw source pins, reconstructs the signed force actions from
their scalar channels, derives current member grain angles and bore bearing
lengths, and evaluates conditional NDS and Grade 5 arithmetic. It does not
import the producer or a capacity helper and does not issue an acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LOAD_REPORT = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json"
)
RAW_RECEIPT = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json"
)
LOAD_SHA256 = "f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1"
RAW_RECEIPT_SHA256 = "c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9"
SOURCE_MANIFEST_SHA256 = "504728bb81018ad749544a12c967c240068d7ca2de0b6223c26a725958897d23"
SOURCE_EVIDENCE_SHA256 = "c58852dfc270f7bf1795ceb0cc8b6530b436f023bbf5a7c27ac9f4baa1e7f373"
CASE_ORDER = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
GROUPS = tuple(
    f"{kind}_bolt_{side}"
    for kind in ("lumber_leg", "rail_front", "rail_rear")
    for side in ("left", "right")
)
AXES = tuple(f"{group}_{index}" for group in GROUPS for index in (1, 2))
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605
PSI_TO_MPA = N_PER_LBF / (25.4**2)
EPSILON = 1e-10


class OracleError(ValueError):
    """Raised when an input pin or emitted result fails reconciliation."""


class Checks:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.max_abs: dict[str, float] = {}
        self.max_rel: dict[str, float] = {}

    def count(self, name: str, amount: int = 1) -> None:
        self.counts[name] = self.counts.get(name, 0) + amount

    def number(
        self,
        actual: Any,
        expected: float,
        label: str,
        category: str,
        *,
        rel_tol: float = 2e-11,
        abs_tol: float = 2e-10,
    ) -> None:
        value = finite(actual, label)
        target = float(expected)
        if not math.isfinite(target):
            raise OracleError(f"{label}: oracle produced a non-finite value")
        absolute = abs(value - target)
        relative = absolute / abs(target) if target != 0.0 else absolute
        self.max_abs[category] = max(self.max_abs.get(category, 0.0), absolute)
        self.max_rel[category] = max(self.max_rel.get(category, 0.0), relative)
        self.count(category)
        tolerance = max(abs_tol, rel_tol * abs(target))
        require(absolute <= tolerance,
                f"{label}: {value:.17g} != {target:.17g} (error {absolute:.4g}, "
                f"tolerance {tolerance:.4g})")

    def vector(
        self,
        actual: Any,
        expected: list[float],
        label: str,
        category: str,
        *,
        abs_tol: float = 1e-8,
        rel_tol: float = 2e-11,
    ) -> None:
        values = vector3(actual, label)
        require(len(expected) == 3, f"{label}: malformed oracle vector")
        for index, target in enumerate(expected):
            self.number(values[index], target, f"{label}[{index}]", category,
                        abs_tol=abs_tol, rel_tol=rel_tol)

    def null(self, actual: Any, label: str) -> None:
        require(actual is None, f"{label}: expected unresolved null, got {actual!r}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as error:
        raise OracleError(f"cannot read {path}: {error}") from error


def read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"cannot read JSON {path}: {error}") from error
    return value, raw


def finite(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{label} is not numeric")
    result = float(value)
    require(math.isfinite(result), f"{label} is not finite")
    return result


def vector3(value: Any, label: str) -> list[float]:
    require(isinstance(value, list) and len(value) == 3,
            f"{label} must be a 3-vector")
    return [finite(component, f"{label}[{index}]")
            for index, component in enumerate(value)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def scale(value: float, vector: list[float]) -> list[float]:
    return [value * component for component in vector]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(a[i] * b[i] for i in range(3))


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(component * component for component in vector))


def unit(vector: list[float], label: str) -> list[float]:
    length = norm(vector)
    require(length > 0.0, f"{label} has zero length")
    return [component / length for component in vector]


def acute_angle_degrees(vector: list[float], axis: list[float], label: str) -> float:
    magnitude = norm(vector)
    axis_magnitude = norm(axis)
    require(magnitude > 0.0 and axis_magnitude > 0.0,
            f"{label}: angle is undefined for a zero vector")
    cosine = abs(dot(vector, axis)) / (magnitude * axis_magnitude)
    return math.degrees(math.acos(min(1.0, max(0.0, cosine))))


def check_source_pin_table(
    pins: Any, checks: Checks, *, expected_count: int, label: str
) -> None:
    require(isinstance(pins, dict) and len(pins) == expected_count,
            f"{label}: expected {expected_count} path pins")
    for relative, expected in pins.items():
        require(isinstance(relative, str) and isinstance(expected, dict),
                f"{label}: malformed pin for {relative!r}")
        require(set(expected) == {"sha256", "size_bytes"},
                f"{label}: malformed pin fields for {relative}")
        path = ROOT / relative
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise OracleError(f"{label}: cannot read {path}: {error}") from error
        require(sha256_bytes(raw) == expected["sha256"],
                f"{label}: SHA-256 mismatch for {relative}")
        require(len(raw) == expected["size_bytes"],
                f"{label}: byte-size mismatch for {relative}")
        checks.count(label)


def load_frozen_load_path(checks: Checks) -> tuple[dict[str, Any], str]:
    data, raw = read_json(LOAD_REPORT)
    report_sha = sha256_bytes(raw)
    require(report_sha == LOAD_SHA256, "frozen current-load-path JSON SHA changed")
    require(isinstance(data, dict), "frozen load-path report is not an object")
    pins = data.get("input_pins")
    check_source_pin_table(pins, checks, expected_count=143,
                           label="load_input_pin")
    require(data.get("producer_sha256") == sha256_path(
        ROOT / "docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01/produce.py"
    ), "frozen load-path producer source changed")
    require(data.get("candidate") == "compact-floor-flush-wood-joints-development"
            and data.get("geometry_revision_id") ==
            "led-clearance-2x6-runner-seated-blocks-v1",
            "frozen load-path candidate or geometry revision changed")
    for field in ("qualified_for_design", "mechanical_acceptance",
                  "joint_demand_accepted", "floor_capacity_established",
                  "friction_qualified", "joint_accepted", "fabrication_release",
                  "native_solve_executed"):
        require(data.get(field) is False,
                f"frozen load-path acceptance boundary changed at {field}")
    require(set(data.get("axis_register", {})) == set(AXES),
            "frozen retained axis register changed")
    states = data.get("states")
    require(isinstance(states, list) and len(states) == 21,
            "frozen load-path state census changed")
    observed: set[tuple[str, int]] = set()
    for state in states:
        case_index = state.get("case_id"), state.get("increment_index")
        require(case_index not in observed and case_index[0] in CASE_ORDER
                and case_index[1] in range(7), "duplicate or foreign source state")
        observed.add(case_index)
        require(state.get("load_factor") == FACTORS[case_index[1]],
                "frozen source load factor changed")
        require(set(state.get("bolt_states", {})) == set(AXES),
                "frozen source state has a different retained-axis census")
    require(len(observed) == 21, "frozen source state coverage is incomplete")

    receipt, receipt_raw = read_json(RAW_RECEIPT)
    require(sha256_bytes(receipt_raw) == RAW_RECEIPT_SHA256,
            "accepted raw load-path receipt SHA changed")
    require(isinstance(receipt, dict)
            and receipt.get("schema") == "retained_frame_bolt_raw_oracle/v1"
            and receipt.get("status") == "PASS_RAW_TOKEN_FORCE_AND_WRENCH_RECONCILIATION"
            and receipt.get("report_sha256") == LOAD_SHA256,
            "accepted raw load-path receipt does not bind the frozen report")
    for field in ("qualified_for_design", "mechanical_acceptance",
                  "joint_demand_accepted", "joint_accepted", "fabrication_release",
                  "native_solve_executed"):
        require(receipt.get(field) is False,
                f"accepted raw load-path receipt changes {field}")
    checks.count("accepted_raw_receipt")
    return data, report_sha


def verify_report_pins(report: dict[str, Any], checks: Checks) -> dict[str, Any]:
    pin_path = HERE / "source-pins.json"
    evidence_path = HERE / "source-evidence.json"
    producer_path = HERE / "produce.py"
    pin_table, _ = read_json(pin_path)
    evidence, _ = read_json(evidence_path)
    require(isinstance(pin_table, dict) and len(pin_table) == 19,
            "resistance source pin manifest must contain 19 paths")
    require(report.get("source_pins") == pin_table,
            "report source pins differ from the checked-in source manifest")
    check_source_pin_table(pin_table, checks, expected_count=19,
                           label="report_source_pin")
    producer_hash = sha256_path(producer_path)
    manifest_hash = sha256_path(pin_path)
    evidence_hash = sha256_path(evidence_path)
    require(report.get("producer_sha256") == producer_hash,
            "report producer SHA does not match current producer bytes")
    require(manifest_hash == SOURCE_MANIFEST_SHA256,
            "independently pinned source-manifest SHA changed")
    require(evidence_hash == SOURCE_EVIDENCE_SHA256,
            "independently pinned source-evidence SHA changed")
    require(report.get("source_manifest_sha256") == SOURCE_MANIFEST_SHA256,
            "report source-manifest SHA changed")
    require(report.get("source_evidence_sha256") == SOURCE_EVIDENCE_SHA256,
            "report source-evidence SHA changed")
    require(isinstance(evidence, dict), "source-evidence manifest is not an object")
    grade5 = evidence.get("grade5")
    tensile_areas = evidence.get("nominal_thread_tensile_stress_area")
    catalog = evidence.get("catalog_bolts")
    require(isinstance(grade5, dict)
            and grade5.get("minimum_Fy_psi") == 92000,
            "source evidence no longer records the conditional Grade 5 Fy scenario")
    require(isinstance(tensile_areas, dict)
            and tensile_areas.get("half_inch_13_in2") == 0.1419
            and tensile_areas.get("three_eighths_16_in2") == 0.0775,
            "source evidence no longer records both nominal thread areas")
    require(isinstance(catalog, dict)
            and catalog.get("407", {}).get("nominal_diameter_in") == 0.5
            and catalog.get("407", {}).get("nominal_length_in") == 8
            and catalog.get("367", {}).get("nominal_diameter_in") == 0.375
            and catalog.get("367", {}).get("nominal_length_in") == 4
            and catalog.get("368", {}).get("nominal_diameter_in") == 0.375
            and catalog.get("368", {}).get("nominal_length_in") == 4.5,
            "source evidence no longer supports the inherited nominal policy map")
    checks.count("producer_source_file")
    checks.count("report_manifest_source_file", 2)

    expected_pins = report.get("rechecked_load_input_pins")
    require(expected_pins == json.loads(LOAD_REPORT.read_bytes()).get("input_pins"),
            "report does not preserve all frozen load input pins")
    require(len(expected_pins) == 143, "report load input pin count changed")
    require(report.get("load_report_sha256") == LOAD_SHA256,
            "report load-path source SHA changed")
    require(report.get("accepted_raw_receipt_sha256") == RAW_RECEIPT_SHA256,
            "report accepted raw receipt SHA changed")
    return {"producer_sha256": producer_hash,
            "source_manifest_sha256": manifest_hash,
            "source_evidence_sha256": evidence_hash}


def expected_catalog_policy(axis_id: str) -> tuple[str, float, float, float]:
    if axis_id.startswith("lumber_leg"):
        return "407", 0.5, 8.0, 0.132
    if axis_id.startswith("rail_front"):
        return "367", 0.375, 4.0, 0.104
    require(axis_id.startswith("rail_rear"), f"unknown axis family {axis_id}")
    return "368", 0.375, 4.5, 0.104


def verify_axis_register(
    report: dict[str, Any], load: dict[str, Any], checks: Checks
) -> dict[str, float]:
    axis_rows = report.get("axis_register")
    require(isinstance(axis_rows, dict) and set(axis_rows) == set(AXES),
            "resistance axis register changed")
    source_axes = load["axis_register"]
    for axis_id in AXES:
        source = source_axes[axis_id]
        output = axis_rows[axis_id]
        fields = source["source_axis_fields"]
        policy = output.get("hardware_policy")
        require(isinstance(policy, dict), f"{axis_id}: hardware policy missing")
        sku, diameter, nominal_length, washer_in = expected_catalog_policy(axis_id)
        checks.number(policy.get("nominal_diameter_in"), diameter,
                      f"{axis_id} policy D", "axis_policy")
        checks.number(fields.get("occupied_diameter_mm"), diameter * 25.4,
                      f"{axis_id} source occupied diameter", "axis_policy")
        checks.number(fields.get("axis_length_mm"), nominal_length * 25.4,
                      f"{axis_id} source modeled axis length", "axis_policy")
        checks.number(policy.get("nominal_length_in"), nominal_length,
                      f"{axis_id} policy nominal length", "axis_policy")
        require(policy.get("catalog_sku_reference") == sku,
                f"{axis_id}: catalog policy identity changed")
        checks.number(policy.get("catalog_max_head_washer_thickness_mm"),
                      washer_in * 25.4, f"{axis_id} head washer thickness",
                      "axis_policy")
        require(policy.get("status") == "inherited_hardware_policy_only",
                f"{axis_id}: policy is presented as a delivered part")
        for key in ("delivered_product", "delivered_full_body_to_transition_mm",
                    "delivered_thread_root_diameter_in", "delivered_thread_class",
                    "delivered_Fy_psi", "delivered_Fyb_psi",
                    "actual_effective_NDS_diameter_in", "actual_steel_shear_area_mm2",
                    "actual_minimum_tensile_area_mm2", "nut_thread_engagement",
                    "washer_resistance_n"):
            checks.null(policy.get(key), f"{axis_id}.hardware_policy.{key}")

        receivers = source["receivers_head_to_nut"]
        require(len(receivers) == 2, f"{axis_id}: source must have two receiver intervals")
        intervals = [r["interval_from_axis_datum_mm"] for r in receivers]
        lengths = [finite(pair[1], f"{axis_id} bore high")
                   - finite(pair[0], f"{axis_id} bore low") for pair in intervals]
        require(all(length > 0.0 for length in lengths),
                f"{axis_id}: nonpositive bore interval length")
        checks.number(intervals[0][1], intervals[1][0],
                      f"{axis_id} receiver interface contiguity", "axis_geometry",
                      abs_tol=1e-8)
        reported = output.get("modeled_bearing_lengths_mm")
        require(isinstance(reported, list) and len(reported) == 2,
                f"{axis_id}: reported bearing lengths malformed")
        for index, length in enumerate(lengths):
            checks.number(reported[index], length,
                          f"{axis_id} bearing length {index}", "axis_geometry")
        grip = math.fsum(lengths)
        checks.number(output.get("modeled_wood_grip_mm"), grip,
                      f"{axis_id} modeled wood grip", "axis_geometry")
        threshold = grip + washer_in * 25.4 - lengths[1] / 4.0
        checks.number(output.get("conditional_full_body_transition_threshold_mm"),
                      threshold, f"{axis_id} transition threshold", "axis_geometry")
        require(output.get("threshold_status") ==
                "conditional dimensions; measured transition and each member occupancy required",
                f"{axis_id}: delivered-thread status boundary changed")
        finished_receivers = output.get("finished_receivers")
        require(finished_receivers == receivers,
                f"{axis_id}: source receiver intervals or finished feature changed")
        checks.null(output.get("adopted_reference_lateral_resistance_n"),
                    f"{axis_id} adopted reference resistance")
        checks.null(output.get("actual_adjusted_joint_resistance_n"),
                    f"{axis_id} adjusted actual joint resistance")
    checks.count("axis_register_rows", len(AXES))
    return {axis: expected_catalog_policy(axis)[1] for axis in AXES}


def rounded_to_nearest_50_half_up(value: float) -> float:
    return 50.0 * math.floor(value / 50.0 + 0.5)


def bearing_strength_psi(angle_degrees: float, diameter_in: float) -> float:
    sg = 0.5
    fe_parallel = rounded_to_nearest_50_half_up(11200.0 * sg)
    fe_perpendicular = rounded_to_nearest_50_half_up(
        6100.0 * sg**1.45 / math.sqrt(diameter_in)
    )
    radians = math.radians(angle_degrees)
    sin_squared = math.sin(radians) ** 2
    cos_squared = math.cos(radians) ** 2
    result = (fe_parallel * fe_perpendicular) / (
        fe_parallel * sin_squared + fe_perpendicular * cos_squared
    )
    require(math.isfinite(result) and result > 0.0,
            "Hankinson bearing strength is invalid")
    return result


def positive_quadratic_root(a: float, b: float, c: float, label: str) -> float:
    """Compute the positive root of a*x^2+b*x+c=0 with low cancellation."""
    require(a > 0.0 and c < 0.0, f"{label}: expected one positive root")
    discriminant = b * b - 4.0 * a * c
    require(discriminant >= 0.0 and math.isfinite(discriminant),
            f"{label}: invalid quadratic discriminant")
    root = (-2.0 * c) / (b + math.sqrt(discriminant))
    require(math.isfinite(root) and root > 0.0,
            f"{label}: nonpositive or nonfinite positive root")
    return root


def single_shear_modes_lbf(
    main_length_in: float,
    side_length_in: float,
    main_fe_psi: float,
    side_fe_psi: float,
    diameter_in: float,
    fyb_psi: float,
    angle_max_degrees: float,
) -> tuple[dict[str, float], dict[str, float]]:
    """Evaluate all six Table 12.3.1A modes from their direct quadratics."""
    require(min(main_length_in, side_length_in, main_fe_psi, side_fe_psi,
                diameter_in, fyb_psi) > 0.0,
            "single-shear input must be positive")
    require(0.0 <= angle_max_degrees <= 90.0,
            "load-to-grain angle is outside the acute-angle domain")
    q_main = main_fe_psi * diameter_in
    q_side = side_fe_psi * diameter_in
    moment = fyb_psi * diameter_in**3 / 6.0
    k_theta = 1.0 + 0.25 * angle_max_degrees / 90.0
    reductions = {
        "Im": 4.0 * k_theta,
        "Is": 4.0 * k_theta,
        "II": 3.6 * k_theta,
        "IIIm": 3.2 * k_theta,
        "IIIs": 3.2 * k_theta,
        "IV": 3.2 * k_theta,
    }
    lm, ls = main_length_in, side_length_in
    gap = 0.0
    coefficients = {
        "II": (
            1.0 / (4.0 * q_side) + 1.0 / (4.0 * q_main),
            ls / 2.0 + gap + lm / 2.0,
            -q_side * ls**2 / 4.0 - q_main * lm**2 / 4.0,
        ),
        "IIIm": (
            1.0 / (2.0 * q_side) + 1.0 / (4.0 * q_main),
            gap + lm / 2.0,
            -moment - q_main * lm**2 / 4.0,
        ),
        "IIIs": (
            1.0 / (4.0 * q_side) + 1.0 / (2.0 * q_main),
            ls / 2.0 + gap,
            -q_side * ls**2 / 4.0 - moment,
        ),
        "IV": (
            1.0 / (2.0 * q_side) + 1.0 / (2.0 * q_main),
            gap,
            -2.0 * moment,
        ),
    }
    yields = {
        "Im": q_main * lm,
        "Is": q_side * ls,
    }
    for mode, (a, b, c) in coefficients.items():
        yields[mode] = positive_quadratic_root(a, b, c, mode)
    reference = {mode: yields[mode] / reductions[mode] for mode in MODES}
    require(all(math.isfinite(value) and value > 0.0
                for value in reference.values()),
            "single-shear reference values must be finite and positive")
    return reference, reductions


def compare_mode_dictionary(
    actual: Any,
    expected: dict[str, float],
    label: str,
    checks: Checks,
) -> str:
    require(isinstance(actual, dict) and set(actual) == set(MODES),
            f"{label}: six-mode dictionary changed")
    for mode in MODES:
        checks.number(actual[mode], expected[mode], f"{label}.{mode}",
                      "nds_mode_lbf", rel_tol=1e-10, abs_tol=1e-11)
    return min(expected, key=expected.get)


def compare_reductions(
    actual: Any, expected: dict[str, float], label: str, checks: Checks
) -> None:
    require(isinstance(actual, dict) and set(actual) == set(MODES),
            f"{label}: six NDS reduction terms missing")
    for mode in MODES:
        checks.number(actual[mode], expected[mode], f"{label}.{mode}",
                      "nds_reduction", rel_tol=1e-12, abs_tol=1e-12)


def verify_lateral_reference(
    item: Any,
    receivers: list[dict[str, Any]],
    angles: list[float],
    diameter_in: float,
    demand_n: float,
    fyb_psi: float,
    label: str,
    checks: Checks,
) -> None:
    require(isinstance(item, dict), f"{label}: reference scenario missing")
    theta_max = max(angles)
    fe = [bearing_strength_psi(angle, diameter_in) for angle in angles]
    checks.number(item.get("Fyb_scenario_psi"), fyb_psi,
                  f"{label} Fyb", "nds_basis")
    require(item.get("Fyb_test_derived_or_adopted") is False,
            f"{label}: conditional Fyb is presented as adopted")
    checks.number(item.get("specific_gravity_scenario"), 0.5,
                  f"{label} SG", "nds_basis")
    checks.number(item.get("diameter_scenario_in"), diameter_in,
                  f"{label} diameter", "nds_basis")
    require(item.get("main_receiver") == receivers[0]["member"]
            and item.get("side_receiver") == receivers[1]["member"],
            f"{label}: main/side receiver ordering changed")
    checks.number(item.get("main_Fe_psi"), fe[0], f"{label} main Fe",
                  "nds_bearing")
    checks.number(item.get("side_Fe_psi"), fe[1], f"{label} side Fe",
                  "nds_bearing")
    forward, reductions = single_shear_modes_lbf(
        finite(receivers[0]["bearing_length_in"], f"{label} main length"),
        finite(receivers[1]["bearing_length_in"], f"{label} side length"),
        fe[0], fe[1], diameter_in, fyb_psi, theta_max,
    )
    reverse, reverse_reductions = single_shear_modes_lbf(
        finite(receivers[1]["bearing_length_in"], f"{label} reverse main length"),
        finite(receivers[0]["bearing_length_in"], f"{label} reverse side length"),
        fe[1], fe[0], diameter_in, fyb_psi, theta_max,
    )
    compare_reductions(item.get("reduction_terms"), reductions,
                       f"{label} reductions", checks)
    compare_reductions(reverse_reductions, reductions,
                       f"{label} reverse reductions", checks)
    forward_governing = compare_mode_dictionary(
        item.get("mode_reference_lbf"), forward, f"{label} modes", checks)
    reverse_governing = compare_mode_dictionary(
        item.get("reverse_assignment_mode_reference_lbf"), reverse,
        f"{label} reversed modes", checks)
    require(item.get("governing_mode") == forward_governing,
            f"{label}: governing yield mode changed")
    min_reference_n = min(forward.values()) * N_PER_LBF
    checks.number(item.get("single_fastener_unadjusted_reference_n"),
                  min_reference_n, f"{label} unadjusted reference N",
                  "nds_reference_n", rel_tol=1e-10, abs_tol=1e-9)
    checks.number(item.get("same_state_demand_divided_by_unadjusted_reference"),
                  demand_n / min_reference_n, f"{label} raw ratio",
                  "nds_ratio", rel_tol=1e-10, abs_tol=1e-12)
    # With the current two-member layouts and identical smooth-shank scenario,
    # role reversal is a permutation of Im/Is and IIIm/IIIs; the minimum must
    # remain invariant while each individual mode is still compared above.
    checks.number(min(reverse.values()) * N_PER_LBF, min_reference_n,
                  f"{label} reversal minimum", "nds_reversal")
    require(reverse_governing in MODES, f"{label}: reverse mode missing")
    for key in ("adjusted_resistance_n", "adjusted_joint_utilization", "Cg",
                "Cdelta", "CD", "CM", "Ct", "actual_Ceg_verified"):
        checks.null(item.get(key), f"{label}.{key}")
    checks.number(item.get("Ceg_scenario"), 1.0,
                  f"{label} Ceg scenario", "nds_basis")
    require(item.get("reference_qualified_for_this_finished_joint") is False,
            f"{label}: reference is marked qualified")


def verify_steel(
    steel: Any,
    tie_n: float,
    lateral_vector: list[float],
    diameter_in: float,
    axis_id: str,
    checks: Checks,
) -> None:
    label = f"{axis_id} steel"
    require(isinstance(steel, dict), f"{label}: material reference missing")
    lateral = norm(lateral_vector)
    area_t_in2 = 0.1419 if diameter_in == 0.5 else 0.0775
    area_t = area_t_in2 * 25.4**2
    area_v = math.pi * (diameter_in * 25.4)**2 / 4.0
    fy_mpa = 92000.0 * PSI_TO_MPA
    checks.number(steel.get("nominal_thread_tensile_stress_area_mm2"), area_t,
                  f"{label} nominal At", "steel_area")
    checks.number(steel.get("hypothetical_full_D_interface_area_mm2"), area_v,
                  f"{label} full D Av", "steel_area")
    require(steel.get("actual_bolt_bending_demand_nmm") is None
            and steel.get("actual_bolt_bending_resistance_nmm") is None
            and steel.get("axial_complete_joint_resistance_n") is None,
            f"{label}: actual bolt/joint resistance became non-null")

    conditional = steel.get("conditional_nominal_material_reference")
    require(isinstance(conditional, dict),
            f"{label}: conditional nominal material reference missing")
    require(conditional.get("status") == "material_first_yield_reference_only",
            f"{label}: nominal steel result status changed")
    checks.number(conditional.get("axial_tension_demand_n"), tie_n,
                  f"{label} pure tension demand", "steel_demand")
    checks.number(conditional.get("lateral_shear_demand_n"), lateral,
                  f"{label} pure shear demand", "steel_demand")
    tension_reference = area_t * fy_mpa
    shear_reference = area_v * fy_mpa / math.sqrt(3.0)
    checks.number(conditional.get("tension_first_yield_reference_n"),
                  tension_reference, f"{label} pure tension reference", "steel_ref")
    checks.number(conditional.get("shear_first_yield_reference_n"),
                  shear_reference, f"{label} pure shear reference", "steel_ref")
    checks.number(conditional.get("tension_first_yield_utilization"),
                  tie_n / tension_reference, f"{label} pure tension ratio", "steel_ratio")
    checks.number(conditional.get("shear_first_yield_utilization"),
                  lateral / shear_reference, f"{label} pure shear ratio", "steel_ratio")
    require(conditional.get("interaction_rule") ==
            "nominal_von_mises_same_section_average_shear",
            f"{label}: co-located interaction rule changed")
    equivalent_stress = math.sqrt(tie_n**2 + 3.0 * lateral**2) / area_v
    vm_ratio = math.sqrt(tie_n**2 + 3.0 * lateral**2) / (fy_mpa * area_v)
    checks.number(conditional.get("interaction_equivalent_stress_mpa"),
                  equivalent_stress, f"{label} same-section von Mises stress",
                  "steel_vm")
    checks.number(conditional.get("interaction_utilization"), vm_ratio,
                  f"{label} same-section von Mises ratio", "steel_vm")
    section = conditional.get("interaction_section")
    require(isinstance(section, dict), f"{label}: co-located section missing")
    checks.number(section.get("area_mm2"), area_v,
                  f"{label} co-located area", "steel_area")
    checks.number(section.get("normal_stress_mpa"), abs(tie_n) / area_v,
                  f"{label} axial stress", "steel_vm")
    checks.number(section.get("average_shear_stress_mpa"), lateral / area_v,
                  f"{label} average shear stress", "steel_vm")
    scenario = conditional.get("specified_material_scenario")
    require(isinstance(scenario, dict), f"{label}: steel scenario missing")
    checks.number(scenario.get("minimum_yield_strength_mpa"), fy_mpa,
                  f"{label} Fy scenario", "steel_basis")

    actual = steel.get("actual_bolt_material_reference")
    require(isinstance(actual, dict) and actual.get("status") == "unresolved",
            f"{label}: actual steel reference was resolved")
    checks.number(actual.get("axial_tension_demand_n"), tie_n,
                  f"{label} actual-record tension demand", "steel_demand")
    checks.number(actual.get("lateral_shear_demand_n"), lateral,
                  f"{label} actual-record lateral demand", "steel_demand")
    for key in ("tension_first_yield_reference_n", "shear_first_yield_reference_n",
                "tension_first_yield_utilization", "shear_first_yield_utilization",
                "interaction_utilization", "interaction_equivalent_stress_mpa"):
        checks.null(actual.get(key), f"{label}.actual.{key}")


def derive_source_actions(
    source_axis: dict[str, Any], bolt_state: dict[str, Any],
    axis_id: str, checks: Checks,
) -> tuple[list[float], float, list[str]]:
    channels = bolt_state.get("scalar_channels")
    require(isinstance(channels, list), f"{axis_id}: source scalar channels missing")
    lateral_channels = [c for c in channels if c.get("family") == "bilateral_spring2"]
    axial_channels = [c for c in channels if c.get("family") == "unilateral_springa"]
    require(len(lateral_channels) == 2 and len(axial_channels) == 1,
            f"{axis_id}: expected two lateral channels and one tension tie")
    lateral = [0.0, 0.0, 0.0]
    source_ids: list[str] = []
    for channel in lateral_channels:
        scalar = finite(channel.get("scalar_force_on_first_N"),
                        f"{axis_id} lateral source scalar")
        direction = vector3(channel.get("direction_global_xyz"),
                            f"{axis_id} lateral source direction")
        owner = channel.get("physical_owner")
        require(isinstance(owner, dict)
                and owner.get("axis_id") == axis_id
                and owner.get("role") == "retained_bolt_lateral_plane",
                f"{axis_id}: lateral source owner changed")
        lateral = add(lateral, scale(scalar, direction))
        source_ids.append(channel.get("source_row_id"))
    expected_axis = vector3(source_axis["source_axis_fields"]["direction_global_xyz"],
                            f"{axis_id} installation axis")
    checks.number(norm(expected_axis), 1.0, f"{axis_id} installation unit norm",
                  "source_action", abs_tol=1e-12, rel_tol=1e-12)
    checks.number(dot(lateral, expected_axis), 0.0,
                  f"{axis_id} lateral axial component", "source_action",
                  abs_tol=1e-8, rel_tol=1e-12)

    axial_channel = axial_channels[0]
    axial_scalar = finite(axial_channel.get("scalar_force_on_first_N"),
                          f"{axis_id} axial source scalar")
    axial_direction = vector3(axial_channel.get("direction_global_xyz"),
                              f"{axis_id} axial source direction")
    axial_owner = axial_channel.get("physical_owner")
    require(isinstance(axial_owner, dict)
            and axial_owner.get("axis_id") == axis_id
            and axial_owner.get("role") == "physical_bolt_outer_seat_tension",
            f"{axis_id}: axial tie source owner changed")
    require(axial_scalar >= 0.0, f"{axis_id}: unilateral tie is compression-signed")
    derived_tie = max(0.0, axial_scalar)
    action = bolt_state.get("lateral_interface_action")
    tie_action = bolt_state.get("axial_interface_action")
    require(isinstance(action, dict) and isinstance(tie_action, dict),
            f"{axis_id}: source interface action missing")
    checks.vector(action.get("force_on_first_xyz_n"), lateral,
                  f"{axis_id} source lateral action first", "source_action")
    checks.vector(action.get("force_on_second_xyz_n"), scale(-1.0, lateral),
                  f"{axis_id} source lateral action second", "source_action")
    checks.number(action.get("transverse_shear_n"), norm(lateral),
                  f"{axis_id} source lateral norm", "source_action")
    checks.number(tie_action.get("axial_along_installation_direction_n"),
                  derived_tie, f"{axis_id} source scalar tie", "source_tie")
    checks.number(dot(scale(axial_scalar, axial_direction), expected_axis),
                  derived_tie, f"{axis_id} tie direction sign", "source_tie")
    return lateral, derived_tie, source_ids + [axial_channel.get("source_row_id")]


def verify_state_rows(
    report: dict[str, Any], load: dict[str, Any], diameters: dict[str, float],
    checks: Checks,
) -> None:
    rows = report.get("state_rows")
    require(isinstance(rows, list) and len(rows) == 252,
            "state-row count must be 252")
    source_states = {
        (state["case_id"], state["increment_index"]): state
        for state in load["states"]
    }
    expected: set[tuple[str, int, str]] = {
        (case, index, axis)
        for case in CASE_ORDER for index in range(len(FACTORS)) for axis in AXES
    }
    observed: set[tuple[str, int, str]] = set()
    source_axis_rows = load["axis_register"]
    for row in rows:
        require(isinstance(row, dict), "state row is not an object")
        identity = (row.get("case_id"), row.get("increment_index"), row.get("axis_id"))
        require(identity in expected and identity not in observed,
                f"foreign or duplicate state-axis row {identity!r}")
        observed.add(identity)
        case_id, index, axis_id = identity
        source_state = source_states[(case_id, index)]
        checks.number(row.get("load_factor"), FACTORS[index],
                      f"{identity} load factor", "state_identity",
                      abs_tol=0.0, rel_tol=0.0)
        lateral, tie, source_ids = derive_source_actions(
            source_axis_rows[axis_id], source_state["bolt_states"][axis_id],
            axis_id, checks,
        )
        demand = norm(lateral)
        checks.vector(row.get("lateral_force_on_first_xyz_n"), lateral,
                      f"{identity} lateral first", "signed_demand")
        checks.number(row.get("lateral_resultant_n"), demand,
                      f"{identity} lateral resultant", "signed_demand")
        checks.number(row.get("same_state_axial_tie_n"), tie,
                      f"{identity} same-state tie", "same_state_tie")
        require(row.get("source_row_ids") == source_ids,
                f"{identity}: source scalar channel IDs changed")
        require(row.get("joint_accepted") is False,
                f"{identity}: state row claims joint acceptance")

        source_axis = source_axis_rows[axis_id]
        output_receivers = row.get("receivers")
        source_receivers = source_axis.get("receivers_head_to_nut")
        require(isinstance(output_receivers, list) and len(output_receivers) == 2
                and len(source_receivers) == 2,
                f"{identity}: receiver pair changed")
        receiver_angles: list[float] = []
        receiver_forces = (lateral, scale(-1.0, lateral))
        for receiver_index, (output, source, force) in enumerate(
            zip(output_receivers, source_receivers, receiver_forces, strict=True)
        ):
            label = f"{identity} receiver {receiver_index}"
            interval = source["interval_from_axis_datum_mm"]
            bearing_length = (finite(interval[1], label + " bore end")
                              - finite(interval[0], label + " bore start")) / 25.4
            stock = source.get("stock_frame")
            require(isinstance(stock, dict), f"{label}: current stock frame missing")
            columns = stock.get("basis_columns_global_xyz")
            require(isinstance(columns, list) and len(columns) == 3,
                    f"{label}: stock frame basis changed")
            grain = vector3(columns[0], label + " grain direction")
            checks.number(norm(grain), 1.0, label + " grain unit norm",
                          "grain_bearing", abs_tol=1e-10, rel_tol=1e-10)
            bolt_direction = vector3(source_axis["source_axis_fields"]["direction_global_xyz"],
                                     label + " bolt direction")
            checks.number(dot(grain, bolt_direction), 0.0,
                          label + " bolt/grain orthogonality", "grain_bearing",
                          abs_tol=1e-8, rel_tol=1e-12)
            theta = acute_angle_degrees(force, grain, label + " load-to-grain angle")
            receiver_angles.append(theta)
            require(isinstance(output, dict), f"{label}: report receiver is malformed")
            require(output.get("member") == source.get("member")
                    and output.get("finished_feature_id") == source.get("feature_id")
                    and output.get("finished_step_sha256") ==
                    source.get("finished_step", {}).get("file_sha256"),
                    f"{label}: receiver or finished feature identity changed")
            for field, expected_value in zip(("bore_interval_mm",), (interval,), strict=True):
                require(output.get(field) == expected_value,
                        f"{label}: source bore interval changed")
            checks.number(output.get("bearing_length_in"), bearing_length,
                          label + " bore-derived bearing length", "grain_bearing")
            checks.vector(output.get("modeled_grain_axis_global_xyz"), grain,
                          label + " member grain axis", "grain_bearing",
                          abs_tol=1e-12)
            checks.vector(output.get("force_on_receiver_xyz_n"), force,
                          label + " signed receiver force", "signed_demand")
            checks.number(output.get("load_to_grain_degrees"), theta,
                          label + " grain angle", "grain_bearing",
                          rel_tol=2e-11, abs_tol=1e-9)
            for field in ("finished_loaded_end_distance_mm",
                          "finished_loaded_edge_distance_mm",
                          "minimum_spacing_end_edge_verified"):
                checks.null(output.get(field), label + "." + field)
        checks.count("receiver_grain_bearing_records", 2)

        references = row.get("lateral_references")
        require(isinstance(references, list) and len(references) == 2,
                f"{identity}: expected two Fyb scenario references")
        for reference, fyb in zip(references, (45000.0, 106000.0), strict=True):
            verify_lateral_reference(reference, output_receivers,
                                     receiver_angles, diameters[axis_id], demand,
                                     fyb, f"{identity} Fyb {fyb:g}", checks)
        verify_steel(row.get("steel"), tie, lateral, diameters[axis_id],
                     axis_id, checks)
        checks.count("state_axis_rows")
    require(observed == expected, "state-axis rows do not cover all 252 combinations")


def verify_group_rows(
    report: dict[str, Any], load: dict[str, Any], checks: Checks
) -> None:
    rows = report.get("group_state_rows")
    require(isinstance(rows, list) and len(rows) == 126,
            "group/state row count must be 126")
    source_states = {
        (state["case_id"], state["increment_index"]): state
        for state in load["states"]
    }
    expected: set[tuple[str, int, str]] = {
        (case, index, group)
        for case in CASE_ORDER for index in range(len(FACTORS)) for group in GROUPS
    }
    observed: set[tuple[str, int, str]] = set()
    for row in rows:
        identity = (row.get("case_id"), row.get("increment_index"), row.get("group_id"))
        require(identity in expected and identity not in observed,
                f"foreign or duplicate group-state row {identity!r}")
        observed.add(identity)
        case_id, index, group = identity
        checks.number(row.get("load_factor"), FACTORS[index],
                      f"{identity} factor", "group_identity",
                      abs_tol=0.0, rel_tol=0.0)
        state = source_states[(case_id, index)]
        axis_ids = [f"{group}_1", f"{group}_2"]
        require(row.get("axis_ids") == axis_ids,
                f"{identity}: group axis membership changed")
        actions = [state["bolt_states"][axis]["lateral_interface_action"]
                   for axis in axis_ids]
        points = [vector3(action["point"], f"{identity} point")
                  for action in actions]
        delta = sub(points[1], points[0])
        spacing = norm(delta)
        require(spacing > 0.0, f"{identity}: zero bolt row spacing")
        row_axis = scale(1.0 / spacing, delta)
        force_vectors = [
            vector3(action["force_on_first_xyz_n"], f"{identity} force {i}")
            for i, action in enumerate(actions)
        ]
        resultant = add(force_vectors[0], force_vectors[1])
        theta = acute_angle_degrees(resultant, row_axis, f"{identity} group angle")
        checks.number(row.get("bolt_row_spacing_mm"), spacing,
                      f"{identity} bolt spacing", "group_geometry")
        checks.vector(row.get("bolt_row_unit_global_xyz"), row_axis,
                      f"{identity} row unit vector", "group_geometry",
                      abs_tol=1e-12)
        checks.vector(row.get("same_state_force_on_first_xyz_n"), resultant,
                      f"{identity} same-state group resultant", "group_action")
        checks.number(row.get("resultant_to_bolt_row_degrees"), theta,
                      f"{identity} resultant-to-row angle", "group_angle",
                      rel_tol=2e-11, abs_tol=1e-9)
        expected_receivers = [actions[0]["first"], actions[0]["second"]]
        require(row.get("receiver_pair") == expected_receivers
                and all(action["first"] == expected_receivers[0]
                        and action["second"] == expected_receivers[1]
                        for action in actions),
                f"{identity}: receiver pair changed within bolt group")
        checks.null(row.get("Cg"), f"{identity}.Cg")
        checks.null(row.get("group_adjusted_resistance_n"),
                    f"{identity}.group_adjusted_resistance_n")
        checks.null(row.get("finished_group_edge_end_applicability"),
                    f"{identity}.finished_group_edge_end_applicability")
        checks.count("group_state_rows")
        checks.count("group_row_resultant_angles")
    require(observed == expected, "group/state rows do not cover all 126 combinations")


def verify_acceptance_boundary(report: dict[str, Any], checks: Checks) -> None:
    require(report.get("schema") == "retained_current_resistance_basis/v1"
            and report.get("status") == "conditional_reference_only",
            "resistance report schema/status changed")
    for field in ("qualified_for_design", "mechanical_acceptance",
                  "joint_demand_accepted", "floor_capacity_established",
                  "friction_qualified", "joint_accepted", "fabrication_release",
                  "native_solve_executed", "engineering_mvp_complete"):
        require(report.get(field) is False,
                f"resistance report acceptance boundary changed at {field}")
    counts = report.get("counts")
    require(isinstance(counts, dict)
            and counts.get("axes") == 12
            and counts.get("finished_receiver_memberships") == 24
            and counts.get("states") == 21
            and counts.get("bolt_states") == 252
            and counts.get("conditional_lateral_scenarios") == 504
            and counts.get("two_bolt_group_states") == 126
            and counts.get("pending_criteria") == 47
            and counts.get("closed_criteria") == 0,
            "resistance report counts or criterion boundary changed")
    require(report.get("criteria_status") == "all_47_pending_unchanged",
            "formal criterion status changed")
    criteria_path = ROOT / "docs/wood-joints-mvp/criteria.json"
    criteria, _ = read_json(criteria_path)
    obligations = criteria.get("legacy_criteria", []) + criteria.get(
        "additional_candidate_obligations", [])
    require(len(obligations) == 47
            and all(item.get("status") == "pending" for item in obligations),
            "current criteria authority no longer has 47 pending obligations")
    checks.count("pending_formal_criteria", 47)
    checks.count("closed_formal_criteria", 0)


def verify(report_path: Path) -> dict[str, Any]:
    checks = Checks()
    load, load_sha = load_frozen_load_path(checks)
    report_value, report_bytes = read_json(report_path)
    require(isinstance(report_value, dict), "resistance report is not an object")
    report = report_value
    source_hashes = verify_report_pins(report, checks)
    verify_acceptance_boundary(report, checks)
    require(report.get("candidate") == load.get("candidate")
            and report.get("geometry_revision_id") == load.get("geometry_revision_id"),
            "resistance report candidate/revision differs from frozen load path")
    diameters = verify_axis_register(report, load, checks)
    verify_state_rows(report, load, diameters, checks)
    verify_group_rows(report, load, checks)
    return {
        "schema": "retained_current_resistance_basis_raw_oracle/v1",
        "status": "PASS_INDEPENDENT_REFERENCE_ARITHMETIC_RECONCILIATION_ONLY",
        "report_sha256": sha256_bytes(report_bytes),
        "oracle_source_sha256": sha256_path(Path(__file__).resolve()),
        "producer_sha256": source_hashes["producer_sha256"],
        "source_manifest_sha256": source_hashes["source_manifest_sha256"],
        "source_evidence_sha256": source_hashes["source_evidence_sha256"],
        "load_report_sha256": load_sha,
        "accepted_raw_receipt_sha256": RAW_RECEIPT_SHA256,
        "tested_counts": dict(sorted(checks.counts.items())),
        "maximum_absolute_errors": dict(sorted(checks.max_abs.items())),
        "maximum_relative_errors": dict(sorted(checks.max_rel.items())),
        "scope": "Source pins and conditional arithmetic only; this receipt issues no design, joint, fabrication, or climbing acceptance.",
        "acceptance_issued": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True,
                        help="new retained-bolt resistance JSON report")
    parser.add_argument("--output", type=Path, required=True,
                        help="deterministic JSON oracle receipt path")
    args = parser.parse_args()
    receipt = verify(args.report)
    encoded = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    args.output.write_bytes(encoded)
    print(json.dumps({"status": receipt["status"],
                      "report_sha256": receipt["report_sha256"],
                      "receipt_sha256": sha256_bytes(encoded),
                      "tested_counts": receipt["tested_counts"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
