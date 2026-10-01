#!/usr/bin/env python3
"""Independently cross-check the conditional end-grain reference arithmetic."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ORACLE_PATH = ROOT / (
    "docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01/"
    "parent_verify.py"
)
ORACLE_SHA = "848e65019ad87dfb7ad07916f845511e1fe78931df070b5242161a79af133e54"
PRODUCER_PATH = HERE / "produce.py"
PRODUCER_SHA = "8e10846bf008430b7e5e30c484c20624bbaa71a6addc74a63bd17b1445c229b8"
CENSUS_PATH = HERE / "role_census.py"
CENSUS_SHA = "a8bd7797b1f46c11f0a9603c5a2fa87742bf9d39e99e0db33942546216ec664c"
NDS_PATH = ROOT / (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-"
    "Dowel-type-fasteners.pdf"
)
NDS_SHA = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
SOURCE_REPORT_SHA = "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e"
ROLE_REPORT_SHA = "5ec2ef3f76dbc7eab0a7a83ae7a5007ff7caec77da56418641208e29846bb16c"
RESULT_SHA = "29854f8b333fd952fab92788517fad1af64a9a807be5b0c134fc1bc47756779f"
SOURCE_REPORT_DEFAULT = Path("/tmp/remaining-single-shear-reference-2026-10-01.json")
ROLE_REPORT_DEFAULT = Path("/tmp/end-grain-role-census-2026-10-01.json")
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
AXES = {
    "center_post_header_left_1", "center_post_header_left_2",
    "center_post_header_right_1", "center_post_header_right_2",
    "center_principal_header_left_1", "center_principal_header_left_2",
    "center_principal_header_right_1", "center_principal_header_right_2",
    "knee_outer_right_inner_header_1", "knee_outer_right_inner_header_2",
}
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605
D_IN = 0.25
FYB_PSI = 45000.0
MAIN_FE_PERP_PSI = 4450.0
CEG = 0.67
THETA_DEGREES = 90.0
KTHETA = 1.25
MM_PER_IN = 25.4
TOL = 1e-10
VECTOR_TOL = 1e-7


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_oracle():
    require(sha(ORACLE_PATH) == ORACLE_SHA, "pinned independent NDS oracle changed")
    spec = importlib.util.spec_from_file_location("end_grain_independent_nds_oracle", ORACLE_PATH)
    require(spec is not None and spec.loader is not None, "cannot import closed-form oracle")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def close(actual: float, expected: float, *, rel: float = TOL, absolute: float = TOL) -> bool:
    return math.isfinite(actual) and math.isfinite(expected) and math.isclose(
        actual, expected, rel_tol=rel, abs_tol=absolute
    )


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    require(math.isfinite(number), f"nonfinite {label}")
    return number


def verify_pin_tree(value: Any) -> int:
    """Recheck every declared {path, sha256} source pin in the report."""
    checked = 0
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            path = Path(value["path"])
            if not path.is_absolute():
                path = ROOT / path
            require(path.is_file() and sha(path) == value["sha256"],
                    f"source pin changed or missing: {value['path']}")
            checked += 1
        else:
            for child in value.values():
                checked += verify_pin_tree(child)
    elif isinstance(value, list):
        for child in value:
            checked += verify_pin_tree(child)
    return checked


def vector(values: Any, label: str) -> list[float]:
    require(isinstance(values, list) and len(values) == 3, f"invalid {label}")
    result = [finite_number(value, label) for value in values]
    require(math.sqrt(math.fsum(value * value for value in result)) > 0.0,
            f"zero {label}")
    return result


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def norm(a: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in a))


def validate_identity(report: dict[str, Any], source_report: Path, census_report: Path) -> tuple[dict, dict]:
    require(sha(PRODUCER_PATH) == PRODUCER_SHA, "end-grain producer changed")
    require(sha(CENSUS_PATH) == CENSUS_SHA, "pinned role census changed")
    require(sha(NDS_PATH) == NDS_SHA, "pinned NDS source changed")
    require(source_report.is_file() and sha(source_report) == SOURCE_REPORT_SHA,
            "frozen 52-axis source report changed")
    require(census_report.is_file() and sha(census_report) == ROLE_REPORT_SHA,
            "frozen ten-axis role census report changed")
    require(report.get("schema") == "end_grain_single_shear_reference/v1"
            and report.get("status") == "PASS_SOURCE_BOUND_CONDITIONAL_CEG_ONLY_ARITHMETIC"
            and report.get("candidate") == "compact-floor-flush-wood-joints-development"
            and report.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1"
            and report.get("source_report_sha256") == SOURCE_REPORT_SHA,
            "end-grain report identity or source binding changed")
    require(report.get("producer_sha256") == PRODUCER_SHA,
            "report is not from the pinned end-grain producer")
    require(report.get("counts") == {
        "axes": 10, "source_cases": 3, "increments_per_case": 7,
        "reference_state_rows": 210,
    }, "report coverage counts changed")
    basis = report.get("reference_basis", {})
    require(basis.get("diameter_in") == D_IN
            and basis.get("bolt_bending_yield_psi") == FYB_PSI
            and basis.get("wood_specific_gravity") == 0.5
            and basis.get("interface_gap_in") == 0.0
            and basis.get("Ceg") == CEG
            and basis.get("quarter_inch_Fyb_qualified") is False,
            "conditional scenario basis or Fyb limitation changed")
    limits = report.get("claim_limits", {})
    require(limits.get("joint_accepted") is False
            and limits.get("mechanical_acceptance") is False
            and limits.get("adopted_capacity") is False
            and limits.get("fully_adjusted_design_ratio") is False
            and limits.get("Ceg_applied_once") is True
            and limits.get("other_adjustments_applied") is False
            and limits.get("same_state_tie_added_to_lateral_demand") is False
            and limits.get("source_null_reference_fields_changed") is False
            and limits.get("six_case_envelope_established") is False
            and limits.get("physical_work_released") is False,
            "claim boundary changed")
    require(verify_pin_tree(report.get("source_sha256")) >= 1
            and verify_pin_tree(report.get("source_census_pins")) >= 1,
            "no source pins were authenticated")
    require(report["source_sha256"].get("remaining_single_shear_producer", {}).get("sha256")
            == "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf"
            and report["source_sha256"].get("role_census", {}).get("sha256") == CENSUS_SHA
            and report["source_sha256"].get("NDS_2024_chapter_12", {}).get("sha256") == NDS_SHA,
            "required method/source pins differ")
    source = json.loads(source_report.read_text(encoding="utf-8"))
    census = json.loads(census_report.read_text(encoding="utf-8"))
    require(source.get("schema") == "remaining_candidate_single_shear_reference/v1"
            and source.get("counts", {}).get("same_state_bolt_rows") == 1092
            and source.get("counts", {}).get("end_grain_or_axis_orientation_excluded_axes") == 10
            and source.get("counts", {}).get("end_grain_or_axis_orientation_excluded_state_rows") == 210,
            "frozen source report no longer has the expected ten-axis cohort")
    require(census.get("schema") == "end_grain_single_shear_role_census/v1"
            and census.get("producer_sha256") == CENSUS_SHA
            and census.get("source_sha256") == SOURCE_REPORT_SHA
            and len(census.get("axes", {})) == 10
            and len(census.get("states", [])) == 210,
            "frozen role census identity/coverage changed")
    return source, census


def validate_geometry_axes(report: dict[str, Any], census: dict[str, Any]) -> dict[str, Any]:
    axes = report.get("axis_geometry_and_grain", {})
    require(set(axes) == AXES and axes == census["axes"],
            "new report changed a source-bound axis/grain/seat geometry record")
    seat_counts = {"head": 0, "nut": 0}
    for axis_id in sorted(AXES):
        axis = axes[axis_id]
        require(axis.get("axis_id") == axis_id
                and axis.get("physical_head_nut_order_established") is False,
                f"axis identity/physical head-nut limitation changed: {axis_id}")
        receivers = axis["receivers"]
        receiver_ids = axis["receiver_ids_underhead_to_tip"]
        require(len(receivers) == 2 and [row["receiver_id"] for row in receivers] == receiver_ids,
                f"receiver order changed: {axis_id}")
        bolt = vector(axis["modeled_bolt_axis_unit_global_xyz"], "modeled bolt axis")
        alignments = []
        for receiver in receivers:
            grain = vector(receiver["source_descriptor_grain_axis_unit_global_xyz"], "source grain axis")
            axis_copy = vector(receiver["bolt_axis_unit_global_xyz"], "receiver bolt axis")
            require(all(close(a, b, rel=0.0, absolute=VECTOR_TOL)
                        for a, b in zip(bolt, axis_copy, strict=True)),
                    f"receiver and axis bolt vectors differ: {axis_id}")
            alignments.append(abs(dot(bolt, grain)))
            start, end = (finite_number(x, "modeled interval")
                          for x in receiver["modeled_interval_from_underhead_mm"])
            length_mm = end - start
            require(length_mm > 0.0
                    and close(length_mm, finite_number(receiver["modeled_bearing_length_mm"], "bearing length mm"))
                    and close(length_mm / MM_PER_IN,
                              finite_number(receiver["modeled_bearing_length_in"], "bearing length in")),
                    f"modeled bearing interval/length mismatch: {axis_id}/{receiver['receiver_id']}")
        main_indices = [i for i, value in enumerate(alignments) if value >= 1.0 - 1e-8]
        side_indices = [i for i, value in enumerate(alignments) if value <= 1e-8]
        require(len(main_indices) == len(side_indices) == 1,
                f"axis does not have exactly one parallel and one transverse receiver: {axis_id}")
        main_id = receivers[main_indices[0]]["receiver_id"]
        side_id = receivers[side_indices[0]]["receiver_id"]
        require(axis.get("parallel_grain_receiver_id") == main_id and side_id == "base_header",
                f"conditional role source geometry differs: {axis_id}")
        for seat_role in ("head", "nut"):
            seat = axis[f"{seat_role}_seat"]
            require(seat.get("is_model_endpoint_role") is True
                    and seat.get("member") in receiver_ids,
                    f"modeled {seat_role} seat role changed: {axis_id}")
        main_seat = next((role for role in ("head", "nut")
                          if axis[f"{role}_seat"]["member"] == main_id), None)
        require(main_seat is not None and axis["head_seat"]["member"] != axis["nut_seat"]["member"],
                f"main receiver is not tied to one model endpoint: {axis_id}")
        seat_counts[main_seat] += 1
    require(seat_counts == {"head": 5, "nut": 5},
            "conditional main role unexpectedly follows only one modeled seat side")
    return axes


def validate_mode_map(actual: Any, expected: dict[str, float], label: str) -> float:
    require(isinstance(actual, dict) and set(actual) == set(MODES), f"{label} mode keys changed")
    maximum = 0.0
    for mode in MODES:
        value = finite_number(actual[mode], f"{label}/{mode}")
        target = expected[mode]
        require(close(value, target), f"{label} closed-form mismatch in {mode}")
        maximum = max(maximum, abs(value - target) / abs(target))
    return maximum


def verify(report_path: Path, source_report_path: Path = SOURCE_REPORT_DEFAULT,
           census_report_path: Path = ROLE_REPORT_DEFAULT) -> dict[str, Any]:
    require(report_path.is_file() and sha(report_path) == RESULT_SHA,
            "end-grain raw report is missing or differs from the pinned result")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source, census = validate_identity(report, source_report_path, census_report_path)
    oracle = load_oracle()
    axes = validate_geometry_axes(report, census)

    source_rows = {
        (row["case_id"], row["increment_index"], row["axis_id"]): row
        for row in source["state_rows"] if row["axis_id"] in AXES
    }
    census_rows = {
        (row["case_id"], row["increment_index"], row["axis_id"]): row
        for row in census["states"]
    }
    expected_keys = {
        (case, index, axis_id)
        for case in CASES for index in range(len(FACTORS)) for axis_id in AXES
    }
    require(len(source_rows) == len(census_rows) == 210
            and set(source_rows) == set(census_rows) == expected_keys,
            "source and role-census rows do not cover the exact ten-axis state set")

    rows = report.get("state_rows", [])
    observed: set[tuple[str, int, str]] = set()
    max_raw_error = 0.0
    max_N_error = 0.0
    max_Ceg_error = 0.0
    max_ratio_error = 0.0
    comparison_count = 0
    adjusted_mode_count = 0
    ratios = []
    role_assignment_counts = {"head": 0, "nut": 0}
    for row in rows:
        key = (row["case_id"], row["increment_index"], row["axis_id"])
        require(key in expected_keys and key not in observed, "duplicate or foreign state row")
        observed.add(key)
        old_row = source_rows[key]
        census_row = census_rows[key]
        source_copy = {k: v for k, v in row.items()
                       if k != "conditional_end_grain_reference"}
        require(set(row) == set(old_row) | {"conditional_end_grain_reference"}
                and source_copy == old_row == census_row,
                f"source lateral vector, tie or other old state fields changed: {key}")
        require(row["load_factor"] == FACTORS[key[1]] and row["joint_accepted"] is False
                and row["single_shear_reference_exclusion"] == "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED"
                and row["single_shear_reference_assignments"] is None
                and row["demand_to_reference_ratios_unadjusted_only"] is None,
                f"source null-reference/acceptance fields changed: {key}")

        axis = axes[key[2]]
        reference = row.get("conditional_end_grain_reference")
        require(isinstance(reference, dict) and reference.get("joint_accepted") is False
                and reference.get("end_grain_role_extension_is_engineering_inference") is True
                and reference.get("role_basis") == "conditional end-grain-main interpretation independent of modeled head/nut order",
                f"conditional claim/role boundary changed: {key}")
        receivers = axis["receivers"]
        bolt = vector(axis["modeled_bolt_axis_unit_global_xyz"], "modeled bolt axis")
        parallel = [i for i, rec in enumerate(receivers)
                    if abs(dot(bolt, vector(rec["source_descriptor_grain_axis_unit_global_xyz"], "grain"))) >= 1.0 - 1e-8]
        transverse = [i for i, rec in enumerate(receivers)
                      if abs(dot(bolt, vector(rec["source_descriptor_grain_axis_unit_global_xyz"], "grain"))) <= 1e-8]
        require(len(parallel) == len(transverse) == 1, f"bad receiver role geometry: {key}")
        mi, si = parallel[0], transverse[0]
        main, side = receivers[mi], receivers[si]
        require(reference.get("main_receiver") == main["receiver_id"]
                and reference.get("side_receiver") == "base_header" == side["receiver_id"]
                and reference.get("main_receiver_underhead_to_tip_index") == mi,
                f"main/side assignment does not follow the axis/grain source: {key}")
        main_seat = next(role for role in ("head", "nut")
                         if axis[f"{role}_seat"]["member"] == main["receiver_id"])
        role_assignment_counts[main_seat] += 1

        force_by_receiver = {
            axis["receiver_ids_underhead_to_tip"][0]: vector(row["actual_lateral_force_on_receiver_0_N"], "receiver-0 force"),
            axis["receiver_ids_underhead_to_tip"][1]: vector(row["actual_lateral_force_on_receiver_1_N"], "receiver-1 force"),
        }
        force_main = force_by_receiver[main["receiver_id"]]
        force_side = force_by_receiver[side["receiver_id"]]
        require(all(close(a, -b, rel=0.0, absolute=VECTOR_TOL)
                    for a, b in zip(force_by_receiver[axis["receiver_ids_underhead_to_tip"][0]],
                                    force_by_receiver[axis["receiver_ids_underhead_to_tip"][1]], strict=True)),
                f"signed lateral action pair does not close: {key}")
        demand = norm(force_by_receiver[axis["receiver_ids_underhead_to_tip"][0]])
        require(close(demand, finite_number(row["actual_lateral_resultant_N"], "lateral resultant"), absolute=1e-8),
                f"source resultant differs from immutable lateral vector: {key}")
        calculated_main_angle = oracle.angle(force_main, main["source_descriptor_grain_axis_unit_global_xyz"])
        calculated_side_angle = oracle.angle(force_side, side["source_descriptor_grain_axis_unit_global_xyz"])
        source_angles = row["actual_lateral_angle_to_grain_deg_by_receiver"]
        require(close(calculated_main_angle, 90.0, absolute=1e-7)
                and close(calculated_side_angle, finite_number(source_angles[side["receiver_id"]], "side angle"), absolute=1e-7)
                and close(calculated_main_angle, finite_number(source_angles[main["receiver_id"]], "main angle"), absolute=1e-7),
                f"recorded actual load/grain angles changed: {key}")

        main_length = (main["modeled_interval_from_underhead_mm"][1]
                       - main["modeled_interval_from_underhead_mm"][0]) / MM_PER_IN
        side_length = (side["modeled_interval_from_underhead_mm"][1]
                       - side["modeled_interval_from_underhead_mm"][0]) / MM_PER_IN
        require(close(finite_number(reference["main_bearing_length_in"], "main interval"), main_length)
                and close(finite_number(reference["side_bearing_length_in"], "side interval"), side_length),
                f"calculation bearing lengths differ from modeled intervals: {key}")
        side_fe = oracle.bearing(calculated_side_angle)
        require(close(finite_number(reference["main_Fe_perpendicular_psi"], "main Fe"), MAIN_FE_PERP_PSI)
                and close(finite_number(reference["side_Fe_actual_angle_psi"], "side Fe"), side_fe),
                f"main perpendicular or side angle-dependent Fe differs: {key}")
        require(close(finite_number(reference["reduction_theta_degrees"], "theta"), THETA_DEGREES)
                and close(finite_number(reference["Ktheta"], "Ktheta"), KTHETA),
                f"Table 12.3.1B theta reduction differs: {key}")

        expected_modes = oracle.nds_modes(
            main_length, side_length, MAIN_FE_PERP_PSI, side_fe, THETA_DEGREES
        )
        max_raw_error = max(max_raw_error, validate_mode_map(
            reference["unadjusted_reference_modes_lbf"], expected_modes, f"raw lbf {key}"
        ))
        expected_modes_N = {mode: value * N_PER_LBF for mode, value in expected_modes.items()}
        max_N_error = max(max_N_error, validate_mode_map(
            reference["unadjusted_reference_modes_N"], expected_modes_N, f"raw N {key}"
        ))
        comparison_count += len(MODES)
        expected_governing = min(MODES, key=expected_modes.__getitem__)
        require(reference.get("governing_mode") == expected_governing
                and close(finite_number(reference["governing_unadjusted_reference_N"], "raw governing N"),
                          expected_modes_N[expected_governing])
                and close(finite_number(reference["independent_mode_IV_lbf"], "independent Mode IV"),
                          expected_modes["IV"]),
                f"raw governing mode/value or secondary Mode IV check differs: {key}")

        require(close(finite_number(reference["Ceg"], "Ceg"), CEG)
                and reference.get("Ceg_application_count") == 1,
                f"Ceg is not represented exactly once: {key}")
        expected_adjusted = {mode: value * CEG for mode, value in expected_modes.items()}
        max_Ceg_error = max(max_Ceg_error, validate_mode_map(
            reference["Ceg_only_reference_modes_lbf"], expected_adjusted, f"Ceg-only lbf {key}"
        ))
        adjusted_mode_count += len(MODES)
        expected_adjusted_N = min(expected_adjusted.values()) * N_PER_LBF
        expected_ratio = demand / expected_adjusted_N
        require(close(finite_number(reference["governing_Ceg_only_reference_N"], "Ceg governing N"),
                      expected_adjusted_N)
                and close(finite_number(reference["lateral_demand_to_Ceg_only_reference_ratio"], "Ceg ratio"),
                          expected_ratio),
                f"once-adjusted governing reference or lateral-only ratio differs: {key}")
        max_ratio_error = max(max_ratio_error,
                              abs(reference["lateral_demand_to_Ceg_only_reference_ratio"] - expected_ratio)
                              / max(abs(expected_ratio), 1e-300))
        ratios.append({"axis_id": key[2], "case_id": key[0], "load_factor": row["load_factor"],
                       "ratio": expected_ratio, "demand_N": demand,
                       "Ceg_only_reference_N": expected_adjusted_N, "mode": expected_governing})
    require(observed == expected_keys and comparison_count == 1260 and adjusted_mode_count == 1260,
            "not all 210 states × six raw and Ceg-only modes were checked")
    require(role_assignment_counts == {"head": 105, "nut": 105},
            "per-state main role did not remain independent of modeled endpoint side")
    ratios.sort(key=lambda row: row["ratio"], reverse=True)
    return {
        "status": "PASS_INDEPENDENT_END_GRAIN_CLOSED_FORM_CEG_ARITHMETIC_ONLY",
        "report_sha256": sha(report_path),
        "source_report_sha256": SOURCE_REPORT_SHA,
        "role_census_report_sha256": ROLE_REPORT_SHA,
        "producer_sha256": PRODUCER_SHA,
        "role_census_sha256": CENSUS_SHA,
        "independent_oracle_sha256": ORACLE_SHA,
        "NDS_pdf_sha256": NDS_SHA,
        "axes": len(AXES), "source_cases": len(CASES), "states_per_axis": len(CASES) * len(FACTORS),
        "states": len(observed), "raw_closed_form_mode_comparisons": comparison_count,
        "Ceg_adjusted_mode_comparisons": adjusted_mode_count,
        "maximum_relative_raw_mode_difference": max_raw_error,
        "maximum_relative_raw_mode_N_difference": max_N_error,
        "maximum_relative_Ceg_mode_difference": max_Ceg_error,
        "maximum_relative_ratio_difference": max_ratio_error,
        "main_role_axes_on_head_seat_side": role_assignment_counts["head"] // len(CASES) // len(FACTORS),
        "main_role_axes_on_nut_seat_side": role_assignment_counts["nut"] // len(CASES) // len(FACTORS),
        "state_ratios_above_one": sum(item["ratio"] > 1.0 for item in ratios),
        "largest_conditional_lateral_only_comparisons": ratios[:5],
        "joint_accepted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True,
                        help="parent's local end-grain result JSON")
    parser.add_argument("--source-report", type=Path, default=SOURCE_REPORT_DEFAULT)
    parser.add_argument("--census-report", type=Path, default=ROLE_REPORT_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(verify(args.report, args.source_report, args.census_report),
                     indent=2, allow_nan=False))
