"""Evaluate bounded PB02 floor-contact stiffness evidence without qualifying it.

The three values are numerical trials, not measured or bounded floor properties.
Only authenticated, numerically accepted six-case suites enter the comparison.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts import simple_center_pb02_diagnostic_run as diagnostic_run
from scripts import simple_center_pb02_six_case_component_envelope as component_envelope
from scripts import simple_center_pb02_six_case_evidence as retained_evidence

TRIAL_STIFFNESSES_N_PER_MM = (5000.0, 10000.0, 20000.0)
BASELINE_STIFFNESS_N_PER_MM = 10000.0
RELATIVE_MATERIALITY_THRESHOLD = 0.05
SIGNED_ACTION_ABSOLUTE_FLOOR = 1.0
FINAL_ARTIFACTS = ("input.json", "frame.dat", "frame.frd", "frame.12d")
EXPECTED_VALIDATION = {
    "geometry_inventory": True,
    "topology_inventory": True,
    "candidate_identity": True,
    "stiffness_inventory": True,
    "producer_source_inventory": True,
    "six_case_load_inventory": True,
    "all_accepted_case_equilibrium_audits": True,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stiffness_key(value: float) -> str:
    return str(int(value))


def _baseline_stiffness_inputs() -> dict:
    authentication = retained_evidence.screen()
    if authentication["summary"]["floor_contact_n_per_mm"] != 10000.0:
        raise ValueError("retained baseline stiffness changed")
    summary = json.loads(retained_evidence.SUMMARY.read_text())
    return summary["stiffness_selection"]["exact_selected_values"]


def _expected_contract(floor_stiffness: float) -> tuple[dict, dict]:
    inputs = _baseline_stiffness_inputs()
    stiffnesses = diagnostic_run._selected_stiffnesses(
        inputs["bolt_axial_n_per_mm"],
        inputs["bolt_lateral_n_per_mm"],
        inputs["face_normal_total_per_interface_n_per_mm"],
        floor_contact_n_per_mm=floor_stiffness,
        contact_grid_resolution=(8, 8),
    )
    return stiffnesses, diagnostic_run._preflight(stiffnesses)


def _safe_case_directory(root: Path, relative: str, case: str) -> Path:
    if not isinstance(relative, str):
        raise TypeError(f"{case}: accepted case path is missing")
    resolved_root = root.resolve()
    directory = (root / relative).resolve()
    if not directory.is_relative_to(resolved_root):
        raise ValueError(f"{case}: accepted case path escapes suite")
    return directory


def _authenticate_final_artifacts(directory: Path, report: dict, case: str) -> None:
    cycles = report.get("contact_cycles", [])
    if not cycles or not isinstance(cycles[-1].get("directory"), str):
        raise ValueError(f"{case}: final cycle is missing")
    cycle = cycles[-1]["directory"]
    hashes = report.get("artifact_sha256", {})
    for filename in FINAL_ARTIFACTS:
        relative = f"{cycle}/{filename}"
        path = directory / relative
        if not path.is_file() or _sha256(path) != hashes.get(relative):
            raise ValueError(f"{case}: final-cycle artifact changed")


def _authenticate_external_suite(
    root: Path, floor_stiffness: float
) -> tuple[dict, dict]:
    """Authenticate one fresh runner suite against the current producer contract."""
    root = Path(root)
    summary_path = root / "pb02-six-case-diagnostic.json"
    if not summary_path.is_file():
        raise ValueError("suite summary is missing")
    summary = json.loads(summary_path.read_text())
    stiffnesses, contract = _expected_contract(floor_stiffness)
    contract_keys = (
        "schema",
        "candidate",
        "active_geometry_fingerprint",
        "case_order",
        "loads",
        "geometry_inventory",
        "stiffness_selection",
        "producer_source_sha256",
        "deterministic_input_fingerprint",
    )
    if any(summary.get(key) != contract[key] for key in contract_keys):
        raise ValueError("suite deterministic input contract changed")
    expected_cases = list(diagnostic_run.CASE_ORDER)
    if (
        summary.get("validation") != EXPECTED_VALIDATION
        or summary.get("accepted_case_count") != len(expected_cases)
        or list(summary.get("accepted_cases", {})) != expected_cases
        or summary.get("rejected_attempt_forces_included") is not False
        or summary.get("developmental_only") is not True
        or summary.get("qualified_for_design") is not False
        or summary.get("actual_joint_demands_qualified") is not False
        or summary.get("resistance_checked") is not False
        or summary.get("acceptance") is not False
        or summary.get("drilling_released") is not False
        or summary.get("fabrication_released") is not False
    ):
        raise ValueError("suite acceptance boundary changed")

    reports = {}
    for case in expected_cases:
        accepted = summary["accepted_cases"][case]
        directory = _safe_case_directory(root, accepted.get("path"), case)
        report_path = directory / "report.json"
        if (
            not report_path.is_file()
            or _sha256(report_path) != accepted.get("report_sha256")
            or accepted.get("numerically_accepted") is not True
            or accepted.get("forces_reported_only_in_authenticated_case_report")
            is not True
        ):
            raise ValueError(f"{case}: accepted report identity changed")
        report = json.loads(report_path.read_text())
        diagnostic_run._validate_accepted_report(report, case, stiffnesses)
        scope = report.get("diagnostic_scope", {})
        if (
            scope.get("case") != case
            or scope.get("candidate") != contract["candidate"]
            or scope.get("deterministic_input_fingerprint")
            != contract["deterministic_input_fingerprint"]
            or scope.get("stiffness_selection") != stiffnesses
            or scope.get("developmental_only") is not True
            or scope.get("qualified_for_design") is not False
            or scope.get("actual_joint_demands_qualified") is not False
            or scope.get("resistance_checked") is not False
            or scope.get("acceptance") is not False
            or scope.get("drilling_released") is not False
            or scope.get("fabrication_released") is not False
            or report.get("qualified_for_design") is not False
            or report.get("actual_joint_demands_qualified") is not False
            or report.get("drilling_released") is not False
            or report.get("fabrication_released") is not False
        ):
            raise ValueError(f"{case}: accepted report scope changed")
        if report.get("pb02_model_identity") != diagnostic_run._model_identity(
            directory, case, stiffnesses
        ):
            raise ValueError(f"{case}: native model identity changed")
        _authenticate_final_artifacts(directory, report, case)
        reports[case] = report
    return summary, reports


def _component_result(reports: dict) -> dict:
    bolts, ratio_records = component_envelope._bolt_envelope(reports)
    interfaces = component_envelope._interface_envelope(reports)
    signed_bolt_forces = {
        bolt_name: {
            case: reports[case]["physical_connection_forces"][bolt_name][
                "force_on_first_xyz_n"
            ]
            for case in component_envelope.CASE_ORDER
        }
        for bolt_name in bolts
    }
    return {
        "bolts": bolts,
        "interfaces": interfaces,
        "governing": component_envelope._governing(bolts, interfaces),
        "conditional_comparisons": component_envelope._comparison_summary(
            ratio_records
        ),
        "signed_bolt_forces": signed_bolt_forces,
    }


def _governing_identities(component: dict) -> dict:
    identities = {}
    for family, row in component["governing"].items():
        if isinstance(row, dict):
            identities[family] = {
                key: row[key] for key in ("name", "case") if key in row
            }
    for family in (
        "direct_shaft",
        "washer_bearing_sensitivity",
        "individual_wood_yield",
        "block_header_end_grain",
    ):
        row = component["conditional_comparisons"][family]["governing"]
        identities[f"ratio/{family}"] = {
            key: row[key] for key in ("name", "case", "variant")
        }
    return identities


def _governing_values(component: dict) -> dict:
    value_fields = {
        "bolt_combined_demand": "combined_n",
        "bolt_axial_tension": "axial_tension_n",
        "bolt_lateral_demand": "lateral_n",
        "complete_interface_force_resultant": "force_n",
        "complete_interface_moment_resultant": "moment_nmm",
        "interface_peak_cell_average_pressure": "pressure_n_per_mm2",
    }
    return {
        family: component["governing"][family][field]
        for family, field in value_fields.items()
    }


def _signed_actions(component: dict) -> dict:
    actions = {}
    axes = "xyz"
    for bolt_name, cases in component["signed_bolt_forces"].items():
        for case, force in cases.items():
            for axis, value in zip(axes, force, strict=True):
                actions[f"bolt/{bolt_name}/{case}/force_on_first_{axis}_n"] = value
    for interface_name, interface in component["interfaces"].items():
        for case, demand in interface["demand_by_case"].items():
            for axis, value in zip(
                axes, demand["complete_interface_force_resultant_xyz_n"], strict=True
            ):
                actions[f"interface/{interface_name}/{case}/force_{axis}_n"] = value
            for axis, value in zip(
                axes,
                demand["complete_interface_moment_about_net_centroid_xyz_nmm"],
                strict=True,
            ):
                actions[f"interface/{interface_name}/{case}/moment_{axis}_nmm"] = value
    return dict(sorted(actions.items()))


def _record(component: dict, stiffness: float, evidence_status: str) -> dict:
    comparisons = component["conditional_comparisons"]
    ratios = {
        family: comparisons[family]["governing"]["ratio"]
        for family in (
            "direct_shaft",
            "washer_bearing_sensitivity",
            "individual_wood_yield",
            "block_header_end_grain",
        )
    }
    return {
        "floor_contact_n_per_mm": stiffness,
        "evidence_status": evidence_status,
        "accepted_case_count": 6,
        "governing_identities": _governing_identities(component),
        "governing_values": _governing_values(component),
        "governing_ratios": ratios,
        "signed_actions_n_or_nmm": _signed_actions(component),
        "conditional_comparators_only": True,
        "qualified_for_design": False,
        "structural_released": False,
    }


def _retained_baseline_record() -> dict:
    component = component_envelope.screen()
    authentication = retained_evidence.screen()
    reports = component_envelope._load_reports(authentication)
    # Rebuilding through the shared helpers prevents a separate sensitivity
    # implementation from silently changing the retained component result.
    rebuilt = _component_result(reports)
    if rebuilt["governing"] != component["governing"]:
        raise ValueError("retained component envelope replay changed")
    return _record(rebuilt, BASELINE_STIFFNESS_N_PER_MM, "authenticated_retained_suite")


def _external_component_record(root: Path, stiffness: float) -> dict:
    _, reports = _authenticate_external_suite(root, stiffness)
    return _record(
        _component_result(reports), stiffness, "authenticated_external_runner_suite"
    )


def _relative_change(value: float, baseline: float, floor: float = 0.0) -> float:
    return abs(value - baseline) / max(abs(baseline), floor)


def _compare_records(
    records: dict[float, dict], ordered_stiffnesses=TRIAL_STIFFNESSES_N_PER_MM
) -> dict:
    trial_order = tuple(float(value) for value in ordered_stiffnesses)
    if BASELINE_STIFFNESS_N_PER_MM not in trial_order:
        raise ValueError("stiffness comparison requires the 10,000 N/mm baseline")
    if set(records) != set(trial_order):
        return {
            "complete": False,
            "baseline_floor_contact_n_per_mm": BASELINE_STIFFNESS_N_PER_MM,
            "material_change_conclusion": "not_evaluated",
            "reason": (
                "All three authenticated six-case suites are required; missing trials "
                "cannot be inferred from the retained 10,000 N/mm suite."
            ),
        }
    baseline = records[BASELINE_STIFFNESS_N_PER_MM]
    identity_changes = []
    ratio_changes = []
    action_changes = []
    baseline_actions = baseline["signed_actions_n_or_nmm"]
    for stiffness in trial_order:
        if stiffness == BASELINE_STIFFNESS_N_PER_MM:
            continue
        trial = records[stiffness]
        if set(trial["signed_actions_n_or_nmm"]) != set(baseline_actions):
            raise ValueError("signed action inventory changed across suites")
        for family, identity in baseline["governing_identities"].items():
            if trial["governing_identities"].get(family) != identity:
                identity_changes.append(
                    {
                        "floor_contact_n_per_mm": stiffness,
                        "family": family,
                        "baseline": identity,
                        "trial": trial["governing_identities"].get(family),
                    }
                )
        for family, baseline_ratio in baseline["governing_ratios"].items():
            trial_ratio = trial["governing_ratios"][family]
            change = _relative_change(trial_ratio, baseline_ratio)
            ratio_changes.append(
                {
                    "floor_contact_n_per_mm": stiffness,
                    "family": family,
                    "baseline_ratio": baseline_ratio,
                    "trial_ratio": trial_ratio,
                    "relative_change": change,
                    "material_by_rule": change > RELATIVE_MATERIALITY_THRESHOLD,
                }
            )
        for name, baseline_value in baseline_actions.items():
            trial_value = trial["signed_actions_n_or_nmm"][name]
            absolute_change = abs(trial_value - baseline_value)
            relative_change = _relative_change(
                trial_value, baseline_value, SIGNED_ACTION_ABSOLUTE_FLOOR
            )
            action_changes.append(
                {
                    "floor_contact_n_per_mm": stiffness,
                    "action": name,
                    "baseline": baseline_value,
                    "trial": trial_value,
                    "absolute_change": absolute_change,
                    "relative_change": relative_change,
                    "sign_changed": baseline_value * trial_value < 0.0,
                    "material_by_rule": (
                        absolute_change > SIGNED_ACTION_ABSOLUTE_FLOOR
                        and relative_change > RELATIVE_MATERIALITY_THRESHOLD
                    ),
                }
            )
    ratio_material = any(row["material_by_rule"] for row in ratio_changes)
    action_material = any(row["material_by_rule"] for row in action_changes)
    identity_material = bool(identity_changes)
    return {
        "complete": True,
        "baseline_floor_contact_n_per_mm": BASELINE_STIFFNESS_N_PER_MM,
        "governing_identity_changed": identity_material,
        "governing_ratio_materially_changed": ratio_material,
        "signed_action_materially_changed": action_material,
        "material_change_conclusion": (
            "material_change_detected"
            if identity_material or ratio_material or action_material
            else "no_material_change_by_rule"
        ),
        "numerical_screening_rule": {
            "relative_change_threshold_strictly_greater_than": (
                RELATIVE_MATERIALITY_THRESHOLD
            ),
            "signed_action_absolute_change_floor_n_or_nmm": (
                SIGNED_ACTION_ABSOLUTE_FLOOR
            ),
            "physical_or_acceptance_limit": False,
        },
        "identity_changes": identity_changes,
        "maximum_governing_ratio_relative_change": max(
            ratio_changes, key=lambda row: row["relative_change"]
        ),
        "maximum_signed_action_relative_change": max(
            action_changes, key=lambda row: row["relative_change"]
        ),
        "signed_action_sign_changes": [
            row for row in action_changes if row["sign_changed"]
        ],
    }


def evaluate_compact_package(package: Path) -> dict:
    """Evaluate one self-contained compact package in its accepted trial order."""
    from scripts import simple_center_pb02_stiffness_evidence as compact_evidence

    authentication = compact_evidence.authenticate(package)
    order = tuple(authentication["trial_floor_contact_n_per_mm"])
    if (
        authentication.get("single_variable_stiffness_comparison_eligible") is not True
        or len(order) < 2
        or set(authentication.get("reports", {})) != set(order)
    ):
        raise ValueError("compact package is not eligible for stiffness comparison")
    records = {
        stiffness: _record(
            _component_result(authentication["reports"][stiffness]),
            stiffness,
            "authenticated_compact_stiffness_suite",
        )
        for stiffness in order
    }
    comparison = _compare_records(records, order)
    return {
        "status": "complete_authenticated_numerical_sensitivity",
        "trial_floor_contact_n_per_mm": list(order),
        "available_authenticated_trials": list(order),
        "missing_authenticated_trials": [],
        "trials": {_stiffness_key(value): records[value] for value in order},
        "failed_trials": authentication["failed_trials"],
        "comparison": comparison,
        "interpretation": (
            "These are numerical trial values only. They are not measured floor "
            "properties or physical bounds."
        ),
        "floor_stiffness_is_physical_property": False,
        "complete_joint_verdict": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def evaluate(external_suites: dict[float, Path] | None = None) -> dict:
    """Evaluate available authenticated suites and report missing evidence."""
    external_suites = external_suites or {}
    unsupported = set(external_suites) - set(TRIAL_STIFFNESSES_N_PER_MM)
    if unsupported:
        raise ValueError(
            f"only prescribed trial values are accepted: {sorted(unsupported)}"
        )
    if BASELINE_STIFFNESS_N_PER_MM in external_suites:
        raise ValueError("the retained 10,000 N/mm baseline cannot be overridden")

    records = {BASELINE_STIFFNESS_N_PER_MM: _retained_baseline_record()}
    failures = {}
    for stiffness, path in sorted(external_suites.items()):
        try:
            records[stiffness] = _external_component_record(path, stiffness)
        except (KeyError, OSError, TypeError, ValueError) as error:
            failures[_stiffness_key(stiffness)] = str(error)
    available = [value for value in TRIAL_STIFFNESSES_N_PER_MM if value in records]
    missing = [value for value in TRIAL_STIFFNESSES_N_PER_MM if value not in records]
    trials = {}
    for stiffness in TRIAL_STIFFNESSES_N_PER_MM:
        key = _stiffness_key(stiffness)
        trials[key] = records.get(stiffness) or {
            "floor_contact_n_per_mm": stiffness,
            "evidence_status": (
                "authentication_failed" if key in failures else "missing"
            ),
            "reason": failures.get(key, "no retained or supplied authenticated suite"),
        }
    comparison = _compare_records(records)
    return {
        "status": (
            "complete_authenticated_numerical_sensitivity"
            if comparison["complete"]
            else "insufficient_authenticated_stiffness_evidence"
        ),
        "trial_floor_contact_n_per_mm": list(TRIAL_STIFFNESSES_N_PER_MM),
        "available_authenticated_trials": available,
        "missing_authenticated_trials": missing,
        "trials": trials,
        "comparison": comparison,
        "interpretation": (
            "These are mechanically modest numerical trial values only. They are not "
            "measured floor properties or physical bounds."
        ),
        "floor_stiffness_is_physical_property": False,
        "complete_joint_verdict": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def _suite_argument(value: str) -> tuple[float, Path]:
    try:
        stiffness_text, path_text = value.split("=", 1)
        stiffness = float(stiffness_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("suite must be STIFFNESS=PATH") from error
    if not math.isfinite(stiffness):
        raise argparse.ArgumentTypeError("suite stiffness must be finite")
    return stiffness, Path(path_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        action="append",
        type=_suite_argument,
        default=[],
        metavar="STIFFNESS=PATH",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    supplied = dict(arguments.suite)
    if len(supplied) != len(arguments.suite):
        parser.error("each supplied stiffness may appear only once")
    result = evaluate(supplied)
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if arguments.output:
        arguments.output.write_text(encoded)
    else:
        print(encoded, end="")
