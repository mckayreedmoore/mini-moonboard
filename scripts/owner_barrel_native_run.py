"""Run one source-bound integrated barrel candidate diagnostic.

The stiffnesses are explicit conditional inputs.  Numerical convergence does
not qualify joint resistance or release drilling, fabrication, or DIY use.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from fea import current_response_run as native
from fea.reinforced_frame_demand import repository_source_closure
from scripts.clear_space_batch import CASES
from scripts.owner_barrel_native_preparation import (
    IntegratedBarrelNative,
    prepare_case,
)

ROOT = Path(__file__).resolve().parents[1]
CASE_LOADS = {
    "a12-forward": ("A12", (0.0, -300.0)),
    "a12-rear": ("A12", (0.0, 300.0)),
    "a12-left": ("A12", (-300.0, 0.0)),
    "k12-right": ("K12", (300.0, 0.0)),
    "k12-rear": ("K12", (0.0, 300.0)),
    "a1-rear": ("A1", (0.0, 300.0)),
}
CONTACT_UPDATE_STRATEGIES = ("all", "one_at_a_time", "one_per_floor_body")
PRODUCER_DATA_PATHS = (
    ROOT / "docs/floor-flush-construction/connection-axes.csv",
    ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json",
)
PRODUCER_PATHS = tuple(
    repository_source_closure(
        [Path(__file__), ROOT / "scripts/owner_barrel_native_preparation.py"],
        packages=("fea", "mini_moonboard", "scripts"),
    )
) + PRODUCER_DATA_PATHS
LOADED_PRODUCER_SHA256 = native.extra_source_hashes(PRODUCER_PATHS)
EXPECTED_VERTICAL_FORCE_N = -2.0 * 250.0 * 0.45359237 * 9.80665
EXPECTED_BARREL_CONTACT_CELLS = 132
EXPECTED_RETAINED_CONTACT_CELLS = 72
EXPECTED_CONTACT_CELLS = (
    EXPECTED_BARREL_CONTACT_CELLS + EXPECTED_RETAINED_CONTACT_CELLS
)
RELEASE_FLAGS = (
    "qualified_for_design",
    "acceptance",
    "joint_resistance_qualified",
    "drilling_released",
    "fabrication_released",
    "diy_released",
    "structural_released",
)
REQUIRED_NUMERICAL_AUDITS = (
    "contact_active_set_converged",
    "axial_tension_active_set_converged",
    "closed_bearing_assumption_passed",
    "global_equilibrium_passed",
    "member_equilibrium_passed",
    "mpc_check_passed",
    "radial_clearance_active_set_converged",
    "numerically_accepted",
)
REQUIRED_RETRY_SOLVER_AUDITS = (
    "global_equilibrium_passed",
    "member_equilibrium_passed",
    "mpc_check_passed",
)


def _source_inventory():
    current = native.extra_source_hashes(PRODUCER_PATHS)
    if current != LOADED_PRODUCER_SHA256:
        raise ValueError("Integrated barrel producer changed after import; restart the run")
    return current


def _validate_inputs(
    case, stiffnesses, max_cycles, contact_update_strategy, allow_retry_checkpoint
):
    if CASES != CASE_LOADS or case not in CASE_LOADS:
        raise ValueError("Integrated barrel six-case load inventory changed")
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or value <= 0
        for value in stiffnesses.values()
    ):
        raise ValueError("Conditional stiffnesses must be positive and finite")
    if type(max_cycles) is not int or max_cycles < 1:
        raise ValueError("max_cycles must be a positive integer")
    if contact_update_strategy not in CONTACT_UPDATE_STRATEGIES:
        raise ValueError("Unknown contact update strategy")
    if type(allow_retry_checkpoint) is not bool:
        raise ValueError("allow_retry_checkpoint must be boolean")


def _load_matches(parameters, case):
    hold, horizontal = CASE_LOADS[case]
    return (
        parameters.get("hold") == hold
        and parameters.get("pounds") == 250.0
        and parameters.get("force_xyz_n")
        == [*horizontal, EXPECTED_VERTICAL_FORCE_N]
    )


def _prepared_inventory(module, structure, metadata, summary, case):
    """Authenticate topology before allowing its solve to label output."""
    force_names = set(metadata.get("connection_ownership", ()))
    contact_names = {
        row.get("name") for row in metadata.get("member_contacts", ())
    }
    barrel_names = set(module.barrel_bolt_names)
    radial_names = set(metadata.get("radial_clearance_ownership", ()))
    expected_radial_names = {
        f"{name}__radial_clearance" for name in barrel_names
    }
    tension_names = {
        row["name"]
        for row in structure.springs
        if row.get("tension_only_assumption")
    }
    if (
        not _load_matches(metadata, case)
        or metadata.get("angle_stations") != []
        or len(barrel_names) != 46
        or radial_names != expected_radial_names
        or tension_names != barrel_names
        or summary.get("barrel_pairs") != 46
        or summary.get("retained_bolts") != 12
        or summary.get("panel_screws") != 66
        or summary.get("face_contact_cells") != EXPECTED_BARREL_CONTACT_CELLS
        or summary.get("retained_face_contact_cells")
        != EXPECTED_RETAINED_CONTACT_CELLS
        or len(contact_names) != EXPECTED_CONTACT_CELLS
        or None in contact_names
        or len(force_names) != len(metadata.get("connection_ownership", ()))
        or any(metadata.get(flag) is not False for flag in ("acceptance",))
        or summary.get("structural_released") is not False
    ):
        raise ValueError(f"{case}: prepared barrel model identity is unauthenticated")
    return {
        "barrel_names": barrel_names,
        "force_names": force_names,
        "contact_names": contact_names,
        "radial_names": radial_names,
    }


def _normalized_radial_states(states, names, *, allow_none):
    if states is None:
        if allow_none:
            return {name: None for name in sorted(names)}
        raise ValueError("radial-clearance state inventory is missing")
    if not isinstance(states, dict) or set(states) != names:
        raise ValueError("radial-clearance state inventory changed")
    normalized = {}
    for name in sorted(names):
        value = states[name]
        if value is None:
            normalized[name] = None
            continue
        if (
            not isinstance(value, (list, tuple))
            or len(value) != 2
            or any(type(item) not in (int, float) or not math.isfinite(item) for item in value)
            or not math.isclose(math.hypot(*value), 1.0, abs_tol=1.0e-9)
        ):
            raise ValueError(f"{name}: radial-clearance state must be null or a unit 2-vector")
        normalized[name] = [float(item) for item in value]
    return normalized


def _validate_native_identity(
    report, case, inventory, initial_radial_clearance_states
):
    """Require exact solved identity before accepting or checkpointing output."""
    if not _load_matches(report.get("parameters", {}), case):
        raise ValueError(f"{case}: native report load identity changed")
    if report.get("angle_stations") != []:
        raise ValueError(f"{case}: native report contains legacy angle stations")
    if set(report.get("axial_tension_names", ())) != inventory["barrel_names"]:
        raise ValueError(f"{case}: barrel axial spring inventory changed")
    physical = report.get("physical_connection_forces")
    if not isinstance(physical, dict) or set(physical) != inventory["force_names"]:
        raise ValueError(f"{case}: physical-force row inventory changed")
    for row in physical.values():
        force = row.get("force_on_first_xyz_n") if isinstance(row, dict) else None
        if (
            not isinstance(force, list)
            or len(force) != 3
            or any(type(value) not in (int, float) or not math.isfinite(value) for value in force)
        ):
            raise ValueError(f"{case}: physical-force row is invalid")
    contacts = report.get("member_contacts")
    if (
        not isinstance(contacts, list)
        or len(contacts) != len(inventory["contact_names"])
        or {row.get("name") for row in contacts if isinstance(row, dict)}
        != inventory["contact_names"]
    ):
        raise ValueError(f"{case}: member-contact row inventory changed")
    if any(report.get(flag, False) is not False for flag in RELEASE_FLAGS):
        raise ValueError(f"{case}: release flag changed")
    expected_initial = _normalized_radial_states(
        initial_radial_clearance_states,
        inventory["radial_names"],
        allow_none=True,
    )
    reported_initial = _normalized_radial_states(
        report.get("initial_radial_clearance_states"),
        inventory["radial_names"],
        allow_none=False,
    )
    if reported_initial != expected_initial:
        raise ValueError(f"{case}: initial radial-clearance checkpoint changed")
    _normalized_radial_states(
        report.get("radial_clearance_states"),
        inventory["radial_names"],
        allow_none=False,
    )
    if set(report.get("radial_clearance_names", ())) != inventory["radial_names"]:
        raise ValueError(f"{case}: radial-clearance name inventory changed")


def _validate_numerical_acceptance(report, case):
    if any(report.get(name) is not True for name in REQUIRED_NUMERICAL_AUDITS):
        raise ValueError(f"{case}: native response did not converge and pass all audits")


def _retry_checkpoint_eligible(report):
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
    return (
        report.get("numerically_accepted") is False
        and all(report.get(name) is True for name in REQUIRED_RETRY_SOLVER_AUDITS)
        and all(type(report.get(name)) is bool for name in active_set_flags)
        and all(type(report.get(name)) is bool for name in assumption_flags)
        and any(report[name] is False for name in active_set_flags)
    )


def _retain_rejected_report(directory, report, error):
    """Leave any failed native artifact explicitly nonaccepted and unreleased."""
    report["native_numerically_accepted"] = report.get("numerically_accepted")
    report["numerically_accepted"] = False
    report["owner_barrel_wrapper_accepted"] = False
    report["retry_checkpoint_eligible"] = False
    report["owner_barrel_validation_error"] = str(error)
    for flag in RELEASE_FLAGS:
        report[flag] = False
    path = directory / "report.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def _diagnostic_scope(
    case,
    stiffnesses,
    contact_update_strategy,
    initial_contact_names,
    initial_axial_tension_names,
    initial_radial_clearance_states,
    max_cycles,
    *,
    retry_checkpoint,
):
    return {
        "case": case,
        "candidate": IntegratedBarrelNative.KEY,
        "case_load": {
            "hold": CASE_LOADS[case][0],
            "horizontal_force_xy_n": list(CASE_LOADS[case][1]),
            "applied_force_xyz_n": [
                *CASE_LOADS[case][1],
                EXPECTED_VERTICAL_FORCE_N,
            ],
            "pounds": 250.0,
        },
        "conditional_stiffnesses": stiffnesses,
        "contact_update_strategy": contact_update_strategy,
        "initial_contact_names": (
            sorted(initial_contact_names) if initial_contact_names is not None else None
        ),
        "initial_axial_tension_names": (
            sorted(initial_axial_tension_names)
            if initial_axial_tension_names is not None
            else None
        ),
        "initial_radial_clearance_states": initial_radial_clearance_states,
        "max_cycles": max_cycles,
        "compression_only_face_contacts": True,
        "tension_only_barrel_axial_springs": True,
        "radial_clearance_active_set": True,
        "diagnostic_only": True,
        "conditional_only": True,
        "rejected_for_acceptance": retry_checkpoint,
        "retry_checkpoint_only": retry_checkpoint,
        "acceptance": False,
        "joint_resistance_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
        "structural_released": False,
    }


def _write_scoped_report(directory, report, scope, *, accepted, retry_eligible):
    scope_path = directory / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope, indent=2, allow_nan=False) + "\n")
    report["owner_barrel_diagnostic_scope"] = scope
    report["native_numerically_accepted"] = report.get("numerically_accepted")
    report["owner_barrel_wrapper_accepted"] = accepted
    report["retry_checkpoint_eligible"] = retry_eligible
    for flag in RELEASE_FLAGS:
        report[flag] = False
    report.setdefault("artifact_sha256", {})[scope_path.name] = hashlib.sha256(
        scope_path.read_bytes()
    ).hexdigest()
    (directory / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def run_case(
    case,
    output,
    *,
    barrel_axial_n_per_mm,
    barrel_lateral_n_per_mm,
    contact_n_per_mm3,
    max_cycles=30,
    contact_update_strategy="all",
    initial_contact_names=None,
    initial_axial_tension_names=None,
    initial_radial_clearance_states=None,
    allow_retry_checkpoint=False,
):
    """Run one conditional case with compression and tension active sets."""
    stiffnesses = {
        "barrel_axial_n_per_mm": barrel_axial_n_per_mm,
        "barrel_lateral_n_per_mm": barrel_lateral_n_per_mm,
        "contact_n_per_mm3": contact_n_per_mm3,
    }
    _validate_inputs(
        case,
        stiffnesses,
        max_cycles,
        contact_update_strategy,
        allow_retry_checkpoint,
    )
    sources = _source_inventory()
    module = IntegratedBarrelNative()
    directory = Path(output)
    prepared = {}

    def prepare_factory(*_args, **_kwargs):
        structure, metadata, summary = prepare_case(
            case,
            module=module,
            **stiffnesses,
        )
        prepared.update(
            _prepared_inventory(module, structure, metadata, summary, case)
        )
        return structure, metadata

    report = native.run(
        directory,
        module=module,
        expected_candidate=module.KEY,
        prepare_factory=prepare_factory,
        extra_source_paths=PRODUCER_PATHS,
        max_cycles=max_cycles,
        contact_update_strategy=contact_update_strategy,
        initial_contact_names=initial_contact_names,
        initial_axial_tension_names=initial_axial_tension_names,
        initial_radial_clearance_states=initial_radial_clearance_states,
    )
    try:
        if report.get("candidate") != module.KEY:
            raise ValueError("Native report candidate identity changed")
        reported_sources = report.get("source_sha256", {})
        if any(
            reported_sources.get(name) != digest for name, digest in sources.items()
        ):
            raise ValueError("Native report does not authenticate barrel producer sources")
        if _source_inventory() != sources:
            raise ValueError("Integrated barrel producer changed during the run")
        if not prepared:
            raise ValueError(f"{case}: native run bypassed barrel preparation")
        _validate_native_identity(
            report,
            case,
            prepared,
            initial_radial_clearance_states,
        )
    except ValueError as error:
        _retain_rejected_report(directory, report, error)
        raise

    try:
        _validate_numerical_acceptance(report, case)
    except ValueError as error:
        if allow_retry_checkpoint and _retry_checkpoint_eligible(report):
            normalized_initial = _normalized_radial_states(
                initial_radial_clearance_states,
                prepared["radial_names"],
                allow_none=True,
            )
            scope = _diagnostic_scope(
                case,
                stiffnesses,
                contact_update_strategy,
                initial_contact_names,
                initial_axial_tension_names,
                normalized_initial,
                max_cycles,
                retry_checkpoint=True,
            )
            return _write_scoped_report(
                directory,
                report,
                scope,
                accepted=False,
                retry_eligible=True,
            )
        _retain_rejected_report(directory, report, error)
        raise

    normalized_initial = _normalized_radial_states(
        initial_radial_clearance_states,
        prepared["radial_names"],
        allow_none=True,
    )
    scope = _diagnostic_scope(
        case,
        stiffnesses,
        contact_update_strategy,
        initial_contact_names,
        initial_axial_tension_names,
        normalized_initial,
        max_cycles,
        retry_checkpoint=False,
    )
    return _write_scoped_report(
        directory, report, scope, accepted=True, retry_eligible=False
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=tuple(CASE_LOADS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--barrel-axial-n-per-mm", type=float, required=True)
    parser.add_argument("--barrel-lateral-n-per-mm", type=float, required=True)
    parser.add_argument("--contact-n-per-mm3", type=float, required=True)
    parser.add_argument("--max-cycles", type=int, default=30)
    parser.add_argument(
        "--contact-update-strategy",
        choices=CONTACT_UPDATE_STRATEGIES,
        default="all",
    )
    parser.add_argument("--initial-contact-name", action="append")
    parser.add_argument("--initial-axial-tension-name", action="append")
    parser.add_argument(
        "--allow-retry-checkpoint",
        action="store_true",
        help="Retain authenticated nonconvergence for orchestration retry only",
    )
    args = parser.parse_args(argv)
    report = run_case(
        args.case,
        args.output,
        barrel_axial_n_per_mm=args.barrel_axial_n_per_mm,
        barrel_lateral_n_per_mm=args.barrel_lateral_n_per_mm,
        contact_n_per_mm3=args.contact_n_per_mm3,
        max_cycles=args.max_cycles,
        contact_update_strategy=args.contact_update_strategy,
        initial_contact_names=args.initial_contact_name,
        initial_axial_tension_names=args.initial_axial_tension_name,
        allow_retry_checkpoint=args.allow_retry_checkpoint,
    )
    print(
        json.dumps(
            {
                key: report.get(key)
                for key in (
                    "candidate",
                    "contact_active_set_converged",
                    "axial_tension_active_set_converged",
                    "numerically_accepted",
                    "termination",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
