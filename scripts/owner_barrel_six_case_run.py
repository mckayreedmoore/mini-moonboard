"""Run and resume the exact six-case conditional barrel diagnostic suite.

This orchestrator authenticates numerical response only.  Every stiffness is
an explicit conditional input.  No result from this script qualifies joint
resistance or releases drilling, fabrication, or DIY construction.

Rejected attempts may contribute authenticated unilateral active-set
memberships to the prescribed retry search.  Their forces are never copied
into suite state or the final summary.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from fea import current_response_run as native
from scripts import owner_barrel_native_run as case_runner

ROOT = Path(__file__).resolve().parents[1]
CASE_ORDER = (
    "a12-forward",
    "a12-rear",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
)
EXPECTED_LOADS = {
    "a12-forward": ("A12", (0.0, -300.0)),
    "a12-rear": ("A12", (0.0, 300.0)),
    "a12-left": ("A12", (-300.0, 0.0)),
    "k12-right": ("K12", (300.0, 0.0)),
    "k12-rear": ("K12", (0.0, 300.0)),
    "a1-rear": ("A1", (0.0, 300.0)),
}
CANDIDATE_ID = "owner-barrel-integrated-native-preparation-v3"
STATE_NAME = "owner-barrel-six-case-state.json"
SUMMARY_NAME = "owner-barrel-six-case-diagnostic.json"
EXPECTED_VERTICAL_FORCE_N = -2.0 * 250.0 * 0.45359237 * 9.80665
SUITE_SOURCE_PATHS = tuple(
    dict.fromkeys(
        (
            Path(__file__),
            *case_runner.PRODUCER_PATHS,
        )
    )
)
LOADED_SUITE_SOURCE_SHA256 = native.extra_source_hashes(SUITE_SOURCE_PATHS)
PLAN_FIELDS = (
    "case",
    "policy_label",
    "contact_update_strategy",
    "initial_contact_names",
    "initial_axial_tension_names",
    "initial_radial_clearance_states",
    "search_seed_case",
    "same_case_continuation_from_attempt",
)


def _canonical_sha256(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json_atomic(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _suite_sources():
    current = native.extra_source_hashes(SUITE_SOURCE_PATHS)
    if current != LOADED_SUITE_SOURCE_SHA256:
        raise ValueError("Barrel suite producer changed after import; restart the run")
    return current


def _positive_finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _is_active_set_nonconvergence(report):
    """Extend proven retry classification to normal, axial, and radial sets."""
    return any(
        report.get(name) is not True
        for name in (
            "contact_active_set_converged",
            "axial_tension_active_set_converged",
            "radial_clearance_active_set_converged",
        )
    )


def _is_repeated_all_state(report):
    return (
        report.get("contact_update_strategy") == "all"
        and _is_active_set_nonconvergence(report)
        and "repeat" in str(report.get("termination", "")).lower()
    )


def _max_cycles_exhausted(report, max_cycles):
    """Recognize one bounded three-active-set continuation checkpoint."""
    termination = str(report.get("termination", "")).lower()
    repeated = "repeat" in termination
    explicit_exhaustion = "max" in termination and (
        "cycle" in termination or "exhaust" in termination
    )
    return (
        report.get("contact_update_strategy") == "one_at_a_time"
        and _is_active_set_nonconvergence(report)
        and len(report.get("contact_cycles", ())) == max_cycles
        and not repeated
        and (not termination or explicit_exhaustion)
    )


def _contract(
    *,
    barrel_axial_n_per_mm,
    barrel_lateral_n_per_mm,
    contact_n_per_mm3,
    max_cycles,
    max_same_case_continuations,
):
    stiffnesses = {
        "barrel_axial_n_per_mm": barrel_axial_n_per_mm,
        "barrel_lateral_n_per_mm": barrel_lateral_n_per_mm,
        "contact_n_per_mm3": contact_n_per_mm3,
    }
    if any(not _positive_finite(value) for value in stiffnesses.values()):
        raise ValueError("Conditional stiffnesses must be positive and finite")
    if type(max_cycles) is not int or max_cycles < 1:
        raise ValueError("max_cycles must be a positive integer")
    if (
        type(max_same_case_continuations) is not int
        or max_same_case_continuations < 0
    ):
        raise ValueError("max_same_case_continuations must be nonnegative")
    if (
        case_runner.CASE_LOADS != EXPECTED_LOADS
        or tuple(case_runner.CASE_LOADS) != CASE_ORDER
        or case_runner.IntegratedBarrelNative.KEY != CANDIDATE_ID
    ):
        raise ValueError("Integrated barrel candidate or six-case identity changed")
    runner_sources = case_runner._source_inventory()
    identity = {
        "schema": "owner_barrel_six_case_run/v1",
        "candidate": CANDIDATE_ID,
        "case_order": list(CASE_ORDER),
        "loads": {
            case: {
                "hold": hold,
                "horizontal_force_xy_n": list(horizontal),
                "vertical_force_n": EXPECTED_VERTICAL_FORCE_N,
            }
            for case, (hold, horizontal) in EXPECTED_LOADS.items()
        },
        "conditional_stiffnesses": stiffnesses,
        "search_controls": {
            "max_cycles_per_attempt": max_cycles,
            "max_same_case_continuations": max_same_case_continuations,
            "strategies": ["all", "one_at_a_time"],
            "rejected_attempt_data_reuse": "authenticated active-set memberships only",
        },
        "topology_expectations": {
            "barrel_tension_only_axis_count": 46,
            "barrel_radial_clearance_group_count": 46,
            "legacy_angle_station_count": 0,
        },
        "case_runner_source_sha256": runner_sources,
        "suite_source_sha256": _suite_sources(),
        "diagnostic_only": True,
        "conditional_only": True,
        "joint_resistance_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }
    return identity | {"deterministic_input_fingerprint": _canonical_sha256(identity)}


def _new_state(contract):
    return {
        "schema": "owner_barrel_six_case_state/v1",
        "contract": contract,
        "deterministic_input_fingerprint": contract[
            "deterministic_input_fingerprint"
        ],
        "attempts": [],
        "abandoned_attempts": [],
        "accepted_cases": {},
        "pending_attempt": None,
        "suite_complete": False,
        "rejected_attempt_forces_included": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }


def _expected_report_sources(contract):
    return {**native.source_hashes(), **contract["case_runner_source_sha256"]}


def _assert_source_contract_current(contract):
    if (
        _suite_sources() != contract["suite_source_sha256"]
        or case_runner._source_inventory() != contract["case_runner_source_sha256"]
    ):
        raise ValueError("Barrel suite producer changed during orchestration")


def _load_matches(report, case):
    hold, horizontal = EXPECTED_LOADS[case]
    parameters = report.get("parameters", {})
    force = parameters.get("force_xyz_n")
    return (
        parameters.get("hold") == hold
        and parameters.get("pounds") == 250.0
        and isinstance(force, list)
        and len(force) == 3
        and force[:2] == list(horizontal)
        and math.isclose(force[2], EXPECTED_VERTICAL_FORCE_N, abs_tol=1.0e-9)
    )


def _validate_artifacts(path, report):
    artifacts = report.get("artifact_sha256")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Native artifact inventory is missing")
    for relative, expected in artifacts.items():
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("Native artifact path escapes attempt directory")
        artifact = path / relative_path
        if (
            not artifact.resolve().is_relative_to(path.resolve())
            or not artifact.is_file()
            or _sha256(artifact) != expected
        ):
            raise ValueError(f"Native artifact changed: {relative}")
    model_digest = artifacts.get("model.pkl")
    if not isinstance(model_digest, str) or len(model_digest) != 64:
        raise ValueError("Authenticated native model artifact is missing")


def _validate_radial_states(report, case):
    names = report.get("radial_clearance_names")
    states = report.get("radial_clearance_states")
    if (
        not isinstance(names, list)
        or len(names) != 46
        or len(set(names)) != 46
        or not isinstance(states, dict)
        or set(states) != set(names)
    ):
        raise ValueError(f"{case}: barrel radial-clearance inventory changed")
    for name, normal in states.items():
        if normal is None:
            continue
        if (
            not isinstance(normal, list)
            or len(normal) != 2
            or any(type(value) not in (int, float) or not math.isfinite(value) for value in normal)
            or not math.isclose(math.hypot(*normal), 1.0, abs_tol=1.0e-9)
        ):
            raise ValueError(f"{case}: invalid radial-clearance state for {name}")
    return {name: states[name] for name in sorted(states)}


def _validate_report(path, report, plan, contract, *, accepted):
    case = plan["case"]
    hold, horizontal = EXPECTED_LOADS[case]
    if report.get("candidate") != CANDIDATE_ID:
        raise ValueError(f"{case}: candidate identity changed")
    if not _load_matches(report, case):
        raise ValueError(f"{case}: load identity changed")
    if report.get("source_sha256") != _expected_report_sources(contract):
        raise ValueError(f"{case}: producer source inventory is unauthenticated")
    if report.get("contact_update_strategy") != plan["contact_update_strategy"]:
        raise ValueError(f"{case}: contact search strategy changed")
    if report.get("angle_stations") != []:
        raise ValueError(f"{case}: legacy angle proxy inventory changed")
    axial_names = report.get("axial_tension_names")
    if (
        not isinstance(axial_names, list)
        or len(axial_names) != 46
        or len(set(axial_names)) != 46
    ):
        raise ValueError(f"{case}: barrel axial inventory changed")
    scope = report.get("owner_barrel_diagnostic_scope")
    expected_stiffnesses = contract["conditional_stiffnesses"]
    if (
        not isinstance(scope, dict)
        or scope.get("case") != case
        or scope.get("candidate") != CANDIDATE_ID
        or scope.get("case_load")
        != {
            "hold": hold,
            "horizontal_force_xy_n": list(horizontal),
            "applied_force_xyz_n": [*horizontal, EXPECTED_VERTICAL_FORCE_N],
            "pounds": 250.0,
        }
        or scope.get("conditional_stiffnesses") != expected_stiffnesses
        or scope.get("contact_update_strategy")
        != plan["contact_update_strategy"]
        or scope.get("initial_contact_names") != plan["initial_contact_names"]
        or scope.get("initial_axial_tension_names")
        != plan["initial_axial_tension_names"]
        or scope.get("max_cycles") != contract["search_controls"][
            "max_cycles_per_attempt"
        ]
        or scope.get("diagnostic_only") is not True
        or scope.get("conditional_only") is not True
        or scope.get("compression_only_face_contacts") is not True
        or scope.get("tension_only_barrel_axial_springs") is not True
        or scope.get("radial_clearance_active_set") is not True
        or scope.get("joint_resistance_qualified") is not False
    ):
        raise ValueError(f"{case}: conditional diagnostic scope changed")
    for flag in (
        "qualified_for_design",
        "drilling_released",
        "fabrication_released",
        "diy_released",
    ):
        if report.get(flag) is not False or scope.get(flag) is not False:
            raise ValueError(f"{case}: {flag} must remain false")
    for flag in ("acceptance", "joint_resistance_qualified", "structural_released"):
        if report.get(flag) is not False or scope.get(flag) is not False:
            raise ValueError(f"{case}: {flag} must remain false")
    scope_path = path / "diagnostic-scope.json"
    if not scope_path.is_file() or json.loads(scope_path.read_text()) != scope:
        raise ValueError(f"{case}: persisted diagnostic scope changed")
    _validate_artifacts(path, report)
    radial_states = _validate_radial_states(report, case)
    reported_initial = scope.get("initial_radial_clearance_states")
    planned_initial = plan["initial_radial_clearance_states"]
    if planned_initial is None:
        initial_matches = (
            isinstance(reported_initial, dict)
            and set(reported_initial) == set(radial_states)
            and all(value is None for value in reported_initial.values())
        )
    else:
        initial_matches = reported_initial == planned_initial
    if (
        not initial_matches
        or report.get("initial_radial_clearance_states") != reported_initial
        or scope.get("retry_checkpoint_only") is not (not accepted)
        or scope.get("rejected_for_acceptance") is not (not accepted)
    ):
        raise ValueError(f"{case}: radial checkpoint or retry scope changed")

    if accepted:
        audits = (
            "contact_active_set_converged",
            "axial_tension_active_set_converged",
            "radial_clearance_active_set_converged",
            "closed_bearing_assumption_passed",
            "global_equilibrium_passed",
            "member_equilibrium_passed",
            "mpc_check_passed",
            "numerically_accepted",
        )
        if any(report.get(name) is not True for name in audits):
            raise ValueError(f"{case}: numerical or equilibrium audit failed")
        if (
            report.get("owner_barrel_wrapper_accepted") is not True
            or report.get("retry_checkpoint_eligible") is not False
            or report.get("native_numerically_accepted") is not True
        ):
            raise ValueError(f"{case}: wrapper acceptance identity changed")
        physical = report.get("physical_connection_forces", {})
        if not set(axial_names) <= set(physical):
            raise ValueError(f"{case}: barrel force inventory is incomplete")
        for name in axial_names:
            force = physical[name].get("force_on_first_xyz_n")
            if (
                not isinstance(force, list)
                or len(force) != 3
                or any(
                    type(value) not in (int, float) or not math.isfinite(value)
                    for value in force
                )
            ):
                raise ValueError(f"{case}: invalid physical force for {name}")
    else:
        active_set_flags = (
            "contact_active_set_converged",
            "axial_tension_active_set_converged",
            "radial_clearance_active_set_converged",
        )
        assumption_flags = (
            "closed_bearing_assumption_passed",
            "axial_tension_assumption_passed",
            "radial_clearance_assumption_passed",
        )
        if (
            not _is_active_set_nonconvergence(report)
            or report.get("owner_barrel_wrapper_accepted") is not False
            or report.get("retry_checkpoint_eligible") is not True
            or report.get("numerically_accepted") is not False
            or report.get("native_numerically_accepted") is not False
            or any(
                report.get(name) is not True
                for name in (
                    "global_equilibrium_passed",
                    "member_equilibrium_passed",
                    "mpc_check_passed",
                )
            )
            or any(type(report.get(name)) is not bool for name in active_set_flags)
            or any(type(report.get(name)) is not bool for name in assumption_flags)
            or not any(report[name] is False for name in active_set_flags)
        ):
            raise ValueError(f"{case}: rejected attempt is not an eligible checkpoint")
    return report


def _checkpoint_memberships(path, report, plan, contract, *, repeated=False):
    _validate_report(path, report, plan, contract, accepted=False)
    max_cycles = contract["search_controls"]["max_cycles_per_attempt"]
    valid = (
        _is_repeated_all_state(report)
        if repeated
        else _max_cycles_exhausted(report, max_cycles)
    )
    if not valid:
        label = "repeated all-state" if repeated else "continuation"
        raise ValueError(f"{plan['case']}: report is not a {label} checkpoint")
    bearings = report.get("bearings")
    axials = report.get("axial_tension")
    if not isinstance(bearings, list) or not isinstance(axials, list):
        raise TypeError(f"{plan['case']}: checkpoint unilateral state is incomplete")
    axial_inventory = set(report["axial_tension_names"])
    normal_names = sorted(
        {
            row["name"]
            for row in bearings
            if row.get("active") is True and not row["name"].endswith("_friction")
        }
        - axial_inventory
    )
    axial_names = sorted(row["name"] for row in axials if row.get("active") is True)
    if not set(axial_names) <= axial_inventory:
        raise ValueError(f"{plan['case']}: checkpoint axial inventory changed")
    radial_states = _validate_radial_states(report, plan["case"])
    return normal_names, axial_names, radial_states


def _normal_contact_seed(path, report, plan, contract):
    _validate_report(path, report, plan, contract, accepted=True)
    axial_inventory = set(report["axial_tension_names"])
    names = sorted(
        {
            row["name"]
            for row in report.get("bearings", ())
            if row.get("active") is True and not row["name"].endswith("_friction")
        }
        - axial_inventory
    )
    if not names:
        raise ValueError("Accepted a12-rear report has no normal-contact seed")
    return names


def _read_report(path):
    return json.loads((path / "report.json").read_text())


def _validated_attempt_path(root, relative):
    relative = Path(relative)
    attempts_root = (root / "attempts").resolve()
    path = root / relative
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 2
        or relative.parts[0] != "attempts"
        or not path.resolve().is_relative_to(attempts_root)
    ):
        raise ValueError("Attempt path escapes suite attempts directory")
    return path


def _attempt_path(root, state, case, policy_label):
    serial = len(state["attempts"]) + len(state["abandoned_attempts"]) + 1
    slug = policy_label.replace("_", "-")
    return root / "attempts" / f"{case}-{serial:03d}-{slug}"


def _attempt_summary(root, plan, path, report, accepted):
    return {
        **plan,
        "path": str(path.relative_to(root)),
        "status": "accepted" if accepted else "rejected_active_set_nonconvergence",
        "contact_active_set_converged": report.get(
            "contact_active_set_converged", False
        ),
        "axial_tension_active_set_converged": report.get(
            "axial_tension_active_set_converged", False
        ),
        "radial_clearance_active_set_converged": report.get(
            "radial_clearance_active_set_converged", False
        ),
        "numerically_accepted": report.get("numerically_accepted", False),
        "termination": report.get("termination"),
        "native_report_sha256": _sha256(path / "report.json"),
        "forces_in_suite_state": False,
    }


def _plan_fields(row):
    if not isinstance(row, dict) or any(key not in row for key in PLAN_FIELDS):
        raise ValueError("Attempt plan schema changed")
    return {key: row[key] for key in PLAN_FIELDS}


def _persist(root, state):
    _write_json_atomic(root / STATE_NAME, state)


def _finish_pending(root, state, report):
    plan = state["pending_attempt"]
    if plan is None:
        raise ValueError("No pending attempt to finish")
    path = _validated_attempt_path(root, plan["path"])
    disk_report = _read_report(path)
    returned_report = json.loads(json.dumps(report, allow_nan=False))
    if disk_report != returned_report:
        raise ValueError(f"{plan['case']}: returned report differs from persisted report")
    report = disk_report
    accepted = report.get("owner_barrel_wrapper_accepted") is True
    _validate_report(path, report, plan, state["contract"], accepted=accepted)
    row = _attempt_summary(root, plan, path, report, accepted)
    if accepted and plan["case"] in state["accepted_cases"]:
        raise ValueError(f"{plan['case']}: duplicate accepted attempt")
    state["attempts"].append(row)
    if accepted:
        case = plan["case"]
        state["accepted_cases"][case] = {
            "attempt": plan["policy_label"],
            "path": plan["path"],
            "report_sha256": row["native_report_sha256"],
            "contact_update_strategy": plan["contact_update_strategy"],
            "search_seed_case": plan["search_seed_case"],
            "numerically_accepted": True,
            "conditional_only": True,
            "joint_resistance_qualified": False,
            "forces_reported_only_in_authenticated_case_report": True,
        }
    state["pending_attempt"] = None
    _persist(root, state)
    return report


def _recover_pending(root, state):
    plan = state.get("pending_attempt")
    if plan is None:
        return
    path = root / plan["path"]
    report_path = path / "report.json"
    if report_path.is_file():
        try:
            report = _read_report(path)
            _finish_pending(root, state, report)
            return
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
    state["abandoned_attempts"].append(
        {
            **plan,
            "status": "interrupted_without_authenticated_report",
            "report_present": report_path.is_file(),
            "forces_in_suite_state": False,
        }
    )
    state["pending_attempt"] = None
    _persist(root, state)


def _validate_saved_state(root, state, contract):
    if (
        state.get("schema") != "owner_barrel_six_case_state/v1"
        or state.get("contract") != contract
        or state.get("deterministic_input_fingerprint")
        != contract["deterministic_input_fingerprint"]
        or state.get("rejected_attempt_forces_included") is not False
        or any(
            state.get(flag) is not False
            for flag in (
                "qualified_for_design",
                "drilling_released",
                "fabrication_released",
                "diy_released",
            )
        )
    ):
        raise ValueError("Resume state does not match current conditional suite contract")
    accepted_from_attempts = {}
    known_paths = set()
    expected_directories = set()
    for row in state.get("attempts", ()):
        plan = _plan_fields(row)
        path = _validated_attempt_path(root, row["path"])
        if row["path"] in known_paths or not path.is_dir():
            raise ValueError("Resume attempt path inventory changed")
        known_paths.add(row["path"])
        expected_directories.add(row["path"])
        report = _read_report(path)
        if _sha256(path / "report.json") != row.get("native_report_sha256"):
            raise ValueError("Resume attempt report changed")
        accepted = row.get("status") == "accepted"
        _validate_report(path, report, row, contract, accepted=accepted)
        expected_row = _attempt_summary(root, plan, path, report, accepted)
        if row != expected_row:
            raise ValueError("Resume attempt summary changed")
        if accepted:
            if row["case"] in accepted_from_attempts:
                raise ValueError("Resume state contains duplicate accepted cases")
            accepted_from_attempts[row["case"]] = row
    for row in state.get("abandoned_attempts", ()):
        plan = _plan_fields(row)
        path = _validated_attempt_path(root, row["path"])
        expected_abandoned = {
            **plan,
            "path": row["path"],
            "status": "interrupted_without_authenticated_report",
            "report_present": row.get("report_present"),
            "forces_in_suite_state": False,
        }
        if type(row.get("report_present")) is not bool or row != expected_abandoned:
            raise ValueError("Resume abandoned-attempt summary changed")
        if row["path"] in known_paths:
            raise ValueError("Resume attempt path is reused")
        known_paths.add(row["path"])
        if path.is_dir():
            expected_directories.add(row["path"])
    pending = state.get("pending_attempt")
    if pending is not None:
        plan = _plan_fields(pending)
        path = _validated_attempt_path(root, pending["path"])
        if pending != {**plan, "path": pending["path"]}:
            raise ValueError("Resume pending-attempt schema changed")
        if pending["path"] in known_paths:
            raise ValueError("Pending attempt path is reused")
        known_paths.add(pending["path"])
        if path.is_dir():
            expected_directories.add(pending["path"])
    accepted = state.get("accepted_cases", {})
    if set(accepted) != set(accepted_from_attempts):
        raise ValueError("Resume accepted-case inventory changed")
    for case, record in accepted.items():
        row = accepted_from_attempts[case]
        expected_record = {
            "attempt": row["policy_label"],
            "path": row["path"],
            "report_sha256": row["native_report_sha256"],
            "contact_update_strategy": row["contact_update_strategy"],
            "search_seed_case": row["search_seed_case"],
            "numerically_accepted": True,
            "conditional_only": True,
            "joint_resistance_qualified": False,
            "forces_reported_only_in_authenticated_case_report": True,
        }
        if record != expected_record:
            raise ValueError(f"{case}: resume acceptance record changed")
    attempts_root = root / "attempts"
    actual_paths = {
        str(path.relative_to(root)) for path in attempts_root.iterdir() if path.is_dir()
    }
    if actual_paths != expected_directories:
        raise ValueError("Resume attempt directory inventory changed")


def _plan(
    case,
    policy_label,
    strategy,
    *,
    initial_contact_names=None,
    initial_axial_tension_names=None,
    initial_radial_clearance_states=None,
    search_seed_case=None,
    continuation_from=None,
):
    return {
        "case": case,
        "policy_label": policy_label,
        "contact_update_strategy": strategy,
        "initial_contact_names": (
            sorted(initial_contact_names)
            if initial_contact_names is not None
            else None
        ),
        "initial_axial_tension_names": (
            sorted(initial_axial_tension_names)
            if initial_axial_tension_names is not None
            else None
        ),
        "initial_radial_clearance_states": (
            {
                name: initial_radial_clearance_states[name]
                for name in sorted(initial_radial_clearance_states)
            }
            if initial_radial_clearance_states is not None
            else None
        ),
        "search_seed_case": search_seed_case,
        "same_case_continuation_from_attempt": continuation_from,
    }


def _run_attempt(root, state, plan):
    _assert_source_contract_current(state["contract"])
    path = _attempt_path(root, state, plan["case"], plan["policy_label"])
    pending = {**plan, "path": str(path.relative_to(root))}
    state["pending_attempt"] = pending
    _persist(root, state)
    stiffnesses = state["contract"]["conditional_stiffnesses"]
    report = case_runner.run_case(
        plan["case"],
        path,
        **stiffnesses,
        max_cycles=state["contract"]["search_controls"][
            "max_cycles_per_attempt"
        ],
        contact_update_strategy=plan["contact_update_strategy"],
        initial_contact_names=plan["initial_contact_names"],
        initial_axial_tension_names=plan["initial_axial_tension_names"],
        initial_radial_clearance_states=plan["initial_radial_clearance_states"],
        allow_retry_checkpoint=True,
    )
    _assert_source_contract_current(state["contract"])
    return _finish_pending(root, state, report)


def _rows_for(state, case, prefix):
    return [
        row
        for row in state["attempts"]
        if row["case"] == case and row["policy_label"].startswith(prefix)
    ]


def _report_for(root, row):
    return _read_report(root / row["path"])


def _primary_search(root, state, case):
    if case in state["accepted_cases"]:
        row = next(
            row
            for row in state["attempts"]
            if row["path"] == state["accepted_cases"][case]["path"]
        )
        return _report_for(root, row)
    all_rows = _rows_for(state, case, "01-")
    if not all_rows:
        report = _run_attempt(root, state, _plan(case, "01-all-unseeded", "all"))
        all_rows = _rows_for(state, case, "01-")
    else:
        report = _report_for(root, all_rows[-1])
    if case in state["accepted_cases"]:
        return report

    one_rows = _rows_for(state, case, "02-")
    if not one_rows:
        all_row = all_rows[-1]
        if _is_repeated_all_state(report):
            normals, axials, radial_states = _checkpoint_memberships(
                root / all_row["path"],
                report,
                all_row,
                state["contract"],
                repeated=True,
            )
            plan = _plan(
                case,
                "02-one-at-a-time-seeded-from-repeated-all",
                "one_at_a_time",
                initial_contact_names=normals,
                initial_axial_tension_names=axials,
                initial_radial_clearance_states=radial_states,
                continuation_from=all_row["policy_label"],
            )
        else:
            plan = _plan(case, "02-one-at-a-time-unseeded", "one_at_a_time")
        report = _run_attempt(root, state, plan)
        one_rows = _rows_for(state, case, "02-")
    else:
        report = _report_for(root, one_rows[-1])
    if case in state["accepted_cases"]:
        return report

    continuation_rows = _rows_for(state, case, "03-")
    limit = state["contract"]["search_controls"]["max_same_case_continuations"]
    prior_row = continuation_rows[-1] if continuation_rows else one_rows[-1]
    report = _report_for(root, prior_row)
    while len(continuation_rows) < limit and _max_cycles_exhausted(
        report, state["contract"]["search_controls"]["max_cycles_per_attempt"]
    ):
        normals, axials, radial_states = _checkpoint_memberships(
            root / prior_row["path"], report, prior_row, state["contract"]
        )
        index = len(continuation_rows) + 1
        plan = _plan(
            case,
            f"03-one-at-a-time-same-case-continuation-{index:02d}",
            "one_at_a_time",
            initial_contact_names=normals,
            initial_axial_tension_names=axials,
            initial_radial_clearance_states=radial_states,
            continuation_from=prior_row["policy_label"],
        )
        report = _run_attempt(root, state, plan)
        continuation_rows = _rows_for(state, case, "03-")
        prior_row = continuation_rows[-1]
        if case in state["accepted_cases"]:
            break
    return report


def _forward_rear_fallback(root, state, rear_report):
    case = "a12-forward"
    if case in state["accepted_cases"]:
        return
    rows = _rows_for(state, case, "90-")
    if not rows:
        rear_record = state["accepted_cases"]["a12-rear"]
        rear_row = next(
            row
            for row in state["attempts"]
            if row["path"] == rear_record["path"]
        )
        seed = _normal_contact_seed(
            root / rear_row["path"], rear_report, rear_row, state["contract"]
        )
        report = _run_attempt(
            root,
            state,
            _plan(
                case,
                "90-one-at-a-time-seeded-from-a12-rear",
                "one_at_a_time",
                initial_contact_names=seed,
                search_seed_case="a12-rear",
            ),
        )
        rows = _rows_for(state, case, "90-")
    else:
        report = _report_for(root, rows[-1])
    if case in state["accepted_cases"]:
        return
    continuations = _rows_for(state, case, "91-")
    limit = state["contract"]["search_controls"]["max_same_case_continuations"]
    prior_row = continuations[-1] if continuations else rows[-1]
    report = _report_for(root, prior_row)
    while len(continuations) < limit and _max_cycles_exhausted(
        report, state["contract"]["search_controls"]["max_cycles_per_attempt"]
    ):
        normals, axials, radial_states = _checkpoint_memberships(
            root / prior_row["path"], report, prior_row, state["contract"]
        )
        index = len(continuations) + 1
        report = _run_attempt(
            root,
            state,
            _plan(
                case,
                f"91-one-at-a-time-rear-seed-continuation-{index:02d}",
                "one_at_a_time",
                initial_contact_names=normals,
                initial_axial_tension_names=axials,
                initial_radial_clearance_states=radial_states,
                search_seed_case="a12-rear",
                continuation_from=prior_row["policy_label"],
            ),
        )
        continuations = _rows_for(state, case, "91-")
        prior_row = continuations[-1]
        if case in state["accepted_cases"]:
            break


def _final_summary(state):
    accepted = state["accepted_cases"]
    if set(accepted) != set(CASE_ORDER):
        raise ValueError("Cannot publish incomplete barrel six-case suite")
    ordered = {case: accepted[case] for case in CASE_ORDER}
    contract = state["contract"]
    return {
        **contract,
        "status": "complete_authenticated_conditional_numerical_suite",
        "validation": {
            "candidate_identity": True,
            "six_case_load_inventory": True,
            "conditional_stiffness_inventory": True,
            "producer_source_inventory": True,
            "accepted_case_equilibrium_audits": True,
        },
        "attempts": state["attempts"],
        "abandoned_attempts": state["abandoned_attempts"],
        "accepted_cases": ordered,
        "accepted_case_count": len(ordered),
        "rejected_attempt_forces_included": False,
        "diagnostic_only": True,
        "conditional_only": True,
        "joint_resistance_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
    }


def run_suite(
    output,
    *,
    barrel_axial_n_per_mm,
    barrel_lateral_n_per_mm,
    contact_n_per_mm3,
    max_cycles=120,
    max_same_case_continuations=3,
    resume=False,
):
    """Run or resume exact six-case suite under one immutable input contract."""
    contract = _contract(
        barrel_axial_n_per_mm=barrel_axial_n_per_mm,
        barrel_lateral_n_per_mm=barrel_lateral_n_per_mm,
        contact_n_per_mm3=contact_n_per_mm3,
        max_cycles=max_cycles,
        max_same_case_continuations=max_same_case_continuations,
    )
    root = Path(output)
    state_path = root / STATE_NAME
    if resume:
        if not state_path.is_file():
            raise ValueError("Resume requires existing authenticated suite state")
        state = json.loads(state_path.read_text())
        _validate_saved_state(root, state, contract)
        _recover_pending(root, state)
        _validate_saved_state(root, state, contract)
        if state["suite_complete"]:
            summary_path = root / SUMMARY_NAME
            if not summary_path.is_file():
                raise ValueError("Complete resume state is missing final summary")
            summary = json.loads(summary_path.read_text())
            if summary != _final_summary(state):
                raise ValueError("Final barrel suite summary changed")
            return summary
    else:
        root.mkdir(parents=True, exist_ok=False)
        (root / "attempts").mkdir()
        state = _new_state(contract)
        _persist(root, state)

    _primary_search(root, state, "a12-forward")
    if "a12-forward" not in state["accepted_cases"]:
        rear = _primary_search(root, state, "a12-rear")
        if "a12-rear" not in state["accepted_cases"]:
            raise RuntimeError(
                "a12-rear did not converge; unauthenticated state cannot seed forward"
            )
        _forward_rear_fallback(root, state, rear)
    if "a12-forward" not in state["accepted_cases"]:
        raise RuntimeError("a12-forward active set did not converge")

    for case in CASE_ORDER[1:]:
        if case in state["accepted_cases"]:
            continue
        _primary_search(root, state, case)
        if case not in state["accepted_cases"]:
            raise RuntimeError(f"{case} active set did not converge")

    _assert_source_contract_current(state["contract"])
    summary = _final_summary(state)
    _write_json_atomic(root / SUMMARY_NAME, summary)
    state["suite_complete"] = True
    _persist(root, state)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--barrel-axial-n-per-mm", type=float, required=True)
    parser.add_argument("--barrel-lateral-n-per-mm", type=float, required=True)
    parser.add_argument("--contact-n-per-mm3", type=float, required=True)
    parser.add_argument("--max-cycles", type=int, default=120)
    parser.add_argument("--max-same-case-continuations", type=int, default=3)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    summary = run_suite(
        args.output,
        barrel_axial_n_per_mm=args.barrel_axial_n_per_mm,
        barrel_lateral_n_per_mm=args.barrel_lateral_n_per_mm,
        contact_n_per_mm3=args.contact_n_per_mm3,
        max_cycles=args.max_cycles,
        max_same_case_continuations=args.max_same_case_continuations,
        resume=args.resume,
    )
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "deterministic_input_fingerprint",
                    "status",
                    "accepted_case_count",
                    "conditional_only",
                    "joint_resistance_qualified",
                    "diy_released",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
