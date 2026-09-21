"""Run the source-bound PB03 eight-station developmental diagnostic.

The runner preserves the proven PB02 six-case active-set search while adding
the exact PB03 block, bolt, and four-cell contact inventory. Rejected attempts
may seed memberships only; their forces never enter accepted records.
"""

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path

from fea import current_response_run as native
from fea.floor_flush_run import face_contacts
from fea.reinforced_frame_demand import repository_source_closure
from scripts import simple_center_pb02_diagnostic_run as pb02_runner
from scripts.clear_space_batch import CASES
from scripts.simple_center_pb02_native import (
    PB02Native,
    prepare_case,
)
from scripts.simple_center_pb02_native import (
    native_row_inventory as pb02_row_inventory,
)
from scripts.simple_pb03_native import BLOCK_NAMES, SOURCE_ID, PB03Native
from scripts.simple_pb03_native_mechanics import (
    PB03MechanicsNative,
    activate_existing_paths,
    native_member_contacts,
    native_row_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = SOURCE_ID
CASE_ORDER = pb02_runner.CASE_ORDER
EXPECTED_LOADS = pb02_runner.EXPECTED_LOADS
EXPECTED_VERTICAL_FORCE_N = pb02_runner.EXPECTED_VERTICAL_FORCE_N
SHIFTED_POST_HEADER_CONTACTS = pb02_runner.SHIFTED_POST_HEADER_CONTACTS
DEFAULT_OUTPUT = Path("/tmp/pb03-eight-station-working-v1")
PRODUCER_PATHS = tuple(
    repository_source_closure(
        [
            Path(__file__),
            ROOT / "scripts/simple_pb03_native.py",
            ROOT / "scripts/simple_pb03_native_mechanics.py",
            ROOT / "scripts/simple_center_pb02_native.py",
            ROOT / "scripts/simple_center_pb02_diagnostic_run.py",
            ROOT / "scripts/simple_center_published_stiffness_basis.py",
        ],
        packages=("fea", "mini_moonboard", "scripts"),
    )
)
LOADED_PRODUCER_SHA256 = native.extra_source_hashes(PRODUCER_PATHS)


class PB03DiagnosticNative(PB03MechanicsNative):
    """Retain exact PB03 points and the verified parent fallback for all others."""

    def bolt_interface_point(self, connection):
        point = self._pb03_interface_points.get(connection.name)
        if point is not None:
            return point
        return PB03Native.bolt_interface_point(self, connection)


def _canonical_sha256(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _source_inventory():
    current = native.extra_source_hashes(PRODUCER_PATHS)
    if current != LOADED_PRODUCER_SHA256:
        raise ValueError("PB03 producer changed after import; restart the run")
    return current


def _native_source_inventory():
    return {**native.source_hashes(), **_source_inventory()}


def _selected_stiffnesses(
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
    floor_contact_n_per_mm=1.0e5,
    contact_grid_resolution=2,
):
    """Reuse the PB02 inputs and bind the PB03 common-area contact law."""
    selected = pb02_runner._selected_stiffnesses(
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
        floor_contact_n_per_mm=floor_contact_n_per_mm,
        contact_grid_resolution=contact_grid_resolution,
    )
    module = PB03DiagnosticNative()
    rows = native_row_inventory(module)
    _, contact_model = native_member_contacts(face_normal_total_n_per_mm, module, rows)
    return {
        **selected,
        "pb03_contact_model": contact_model,
        "pb03_mechanics_identity": rows[1],
    }


def _topology_inventory(module, pb03_rows):
    rows, mechanics_identity = pb03_rows
    pb03_bolts = {row["name"] for row in rows if row["kind"] == "bolt"}
    pb03_contacts = {
        row["name"] for row in rows if row["kind"] == "contact_compression"
    }
    pb02_rows = pb02_row_inventory()
    pb02_bolts = set(pb02_runner._bolt_row_inventory(pb02_rows))
    pb02_contacts = {
        row["name"] for row in pb02_rows if row["kind"] == "contact_compression"
    }
    required_physical = (
        pb03_bolts
        | pb03_contacts
        | pb02_bolts
        | pb02_contacts
        | SHIFTED_POST_HEADER_CONTACTS
    )
    inventory = {
        "legacy_station_count": len(module.legacy_proxy_stations()),
        "fixed_panel_kicker_axis_count": len(module.panel_connections()),
        "pb03_tension_only_bolt_count": len(pb03_bolts),
        "pb02_tension_only_bolt_count": len(pb02_bolts),
        "pb03_contact_cell_count": len(pb03_contacts),
        "block_member_count": len(BLOCK_NAMES),
        "tension_only_bolt_names": sorted(pb03_bolts | pb02_bolts),
        "pb03_bolt_names": sorted(pb03_bolts),
        "pb03_contact_names": sorted(pb03_contacts),
        "block_member_names": sorted(BLOCK_NAMES.values()),
        "required_physical_names": sorted(required_physical),
    }
    expected = (14, 66, 32, 10, 64, 8, 42)
    actual = (
        inventory["legacy_station_count"],
        inventory["fixed_panel_kicker_axis_count"],
        inventory["pb03_tension_only_bolt_count"],
        inventory["pb02_tension_only_bolt_count"],
        inventory["pb03_contact_cell_count"],
        inventory["block_member_count"],
        len(inventory["tension_only_bolt_names"]),
    )
    if actual != expected or mechanics_identity["legacy_proxy_stations"] != 14:
        raise ValueError("PB03 eight-station topology inventory changed")
    return inventory, mechanics_identity


def _preflight(stiffnesses):
    if tuple(EXPECTED_LOADS) != CASE_ORDER or any(
        CASES.get(name) != expected for name, expected in EXPECTED_LOADS.items()
    ):
        raise ValueError("PB03 unchanged six-case load inventory changed")
    module = PB03DiagnosticNative()
    inventory, mechanics_identity = _topology_inventory(
        module, native_row_inventory(module)
    )
    if mechanics_identity != stiffnesses["pb03_mechanics_identity"]:
        raise ValueError("PB03 mechanics fingerprint changed during preflight")
    sources = _source_inventory()
    identity = {
        "schema": "simple_pb03_eight_station_diagnostic_run/v1",
        "candidate": CANDIDATE_ID,
        "case_order": list(CASE_ORDER),
        "loads": {
            name: {"hold": hold, "horizontal_force_xy_n": list(force)}
            for name, (hold, force) in EXPECTED_LOADS.items()
        },
        "mechanics_identity": mechanics_identity,
        "topology_inventory": inventory,
        "stiffness_selection": stiffnesses,
        "producer_source_sha256": sources,
        "developmental_only": True,
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    return identity | {"deterministic_input_fingerprint": _canonical_sha256(identity)}


def prepare_unsolved_case(case, stiffnesses):
    """Prepare the exact combined PB02/PB03 model without invoking a solver."""
    values = stiffnesses["exact_selected_values"]
    module = PB03DiagnosticNative()
    rows = native_row_inventory(module)
    pb03_contacts, contact_model = native_member_contacts(
        values["face_normal_total_per_interface_n_per_mm"], module, rows
    )
    if (
        rows[1] != stiffnesses["pb03_mechanics_identity"]
        or contact_model != stiffnesses["pb03_contact_model"]
    ):
        raise ValueError("PB03 preparation mechanics identity changed")

    def post_prepare(structure, metadata):
        module.validate_prepared_case(structure, metadata)
        activate_existing_paths(structure, metadata, module, rows)

    return prepare_case(
        case,
        bolt_axial_n_per_mm=values["bolt_axial_n_per_mm"],
        bolt_lateral_n_per_mm=values["bolt_lateral_n_per_mm"],
        face_normal_total_n_per_mm=values["face_normal_total_per_interface_n_per_mm"],
        floor_contact_n_per_mm=values["floor_contact_n_per_mm"],
        contact_grid_resolution=tuple(stiffnesses["contact_model"]["grid_resolution"]),
        module=module,
        expected_candidate=CANDIDATE_ID,
        member_contacts=(*face_contacts(PB02Native()), *pb03_contacts),
        expected_legacy_station_count=14,
        post_prepare=post_prepare,
    )


def _model_identity(path, case, contract):
    model_path = path / "model.pkl"
    with model_path.open("rb") as source:
        payload = pickle.load(source)
    structure, metadata = payload["model"]
    inventory = contract["topology_inventory"]
    values = contract["stiffness_selection"]["exact_selected_values"]
    hold, horizontal = EXPECTED_LOADS[case]
    tension_names = {
        spring["name"]
        for spring in structure.springs
        if spring.get("tension_only_assumption")
    }
    contact_names = {
        spring["name"]
        for spring in structure.springs
        if spring["name"] in inventory["pb03_contact_names"]
    }
    if (
        payload.get("source_sha256") != _native_source_inventory()
        or metadata.get("candidate") != CANDIDATE_ID
        or metadata.get("hold") != hold
        or metadata.get("pounds") != 250.0
        or metadata.get("force_xyz_n") != [*horizontal, EXPECTED_VERTICAL_FORCE_N]
        or metadata.get("pb03_mechanics_identity") != contract["mechanics_identity"]
        or metadata.get("pb03_native_row_counts", {}).get("bolt_tension_only") != 32
        or tension_names != set(inventory["tension_only_bolt_names"])
        or contact_names != set(inventory["pb03_contact_names"])
        or metadata.get("stiffnesses", {}).get("floor")
        != values["floor_contact_n_per_mm"]
        or any(
            metadata.get(flag) is not False
            for flag in (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
            )
        )
    ):
        raise ValueError(f"{case}: generated PB03 model identity is unauthenticated")
    return hashlib.sha256(model_path.read_bytes()).hexdigest()


def _load_matches(report, case):
    hold, horizontal = EXPECTED_LOADS[case]
    force = report.get("parameters", {}).get("force_xyz_n")
    return (
        report.get("parameters", {}).get("hold") == hold
        and report.get("parameters", {}).get("pounds") == 250.0
        and isinstance(force, list)
        and len(force) == 3
        and force[:2] == list(horizontal)
        and math.isclose(force[2], EXPECTED_VERTICAL_FORCE_N, abs_tol=1.0e-9)
    )


def _validate_accepted_report(report, case, contract):
    required_audits = (
        "contact_active_set_converged",
        "axial_tension_active_set_converged",
        "closed_bearing_assumption_passed",
        "global_equilibrium_passed",
        "member_equilibrium_passed",
        "mpc_check_passed",
        "numerically_accepted",
    )
    if report.get("candidate") != CANDIDATE_ID:
        raise ValueError(f"{case}: candidate identity changed")
    if not _load_matches(report, case):
        raise ValueError(f"{case}: load identity changed")
    if any(report.get(name) is not True for name in required_audits):
        raise ValueError(f"{case}: numerical or equilibrium audit failed")
    if len(report.get("angle_stations", ())) != 14:
        raise ValueError(f"{case}: legacy station inventory changed")
    inventory = contract["topology_inventory"]
    if set(report.get("axial_tension_names", ())) != set(
        inventory["tension_only_bolt_names"]
    ):
        raise ValueError(f"{case}: tension-only bolt inventory changed")
    physical = report.get("physical_connection_forces", {})
    required_physical = set(inventory["required_physical_names"])
    if not required_physical <= set(physical):
        raise ValueError(f"{case}: physical-force inventory is incomplete")
    for record in physical.values():
        force = record.get("force_on_first_xyz_n")
        if (
            not isinstance(force, list)
            or len(force) != 3
            or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in force
            )
        ):
            raise ValueError(f"{case}: physical-force record is invalid")
    demands = report.get("member_section_demands", {})
    if not set(inventory["block_member_names"]) <= set(demands):
        raise ValueError(f"{case}: block member records are incomplete")
    if (
        report.get("pb03_diagnostic_identity")
        != contract["deterministic_input_fingerprint"]
        or report.get("pb03_mechanics_identity") != contract["mechanics_identity"]
    ):
        raise ValueError(f"{case}: mechanics fingerprint is unauthenticated")
    model_identity = report.get("pb03_model_identity")
    if (
        not isinstance(model_identity, str)
        or len(model_identity) != 64
        or report.get("artifact_sha256", {}).get("model.pkl") != model_identity
    ):
        raise ValueError(f"{case}: model artifact hash is unauthenticated")
    reported_sources = report.get("source_sha256", {})
    if any(
        reported_sources.get(name) != digest
        for name, digest in contract["producer_source_sha256"].items()
    ):
        raise ValueError(f"{case}: producer source inventory is unauthenticated")
    if any(
        report.get(flag) is not False
        for flag in (
            "qualified_for_design",
            "acceptance",
            "drilling_released",
            "fabrication_released",
        )
    ):
        raise ValueError(f"{case}: release flags must remain false")
    return report


def _run_attempt(
    case,
    path,
    *,
    strategy,
    contract,
    max_cycles,
    initial_contact_names=None,
    initial_axial_tension_names=None,
):
    report = native.run(
        path,
        module=PB03DiagnosticNative(),
        expected_candidate=CANDIDATE_ID,
        prepare_factory=lambda *_args, **_kwargs: prepare_unsolved_case(
            case, contract["stiffness_selection"]
        ),
        extra_source_paths=PRODUCER_PATHS,
        contact_update_strategy=strategy,
        initial_contact_names=initial_contact_names,
        initial_axial_tension_names=initial_axial_tension_names,
        max_cycles=max_cycles,
    )
    report.update(
        pb03_diagnostic_identity=contract["deterministic_input_fingerprint"],
        pb03_mechanics_identity=contract["mechanics_identity"],
        pb03_model_identity=_model_identity(path, case, contract),
        acceptance=False,
        drilling_released=False,
        fabrication_released=False,
    )
    return report


def _is_active_set_nonconvergence(report):
    return pb02_runner._is_active_set_nonconvergence(report)


def _normal_contact_seed(report):
    return pb02_runner._normal_contact_seed(report)


def _max_cycles_exhausted(report, max_cycles):
    return pb02_runner._max_cycles_exhausted(report, max_cycles)


def _is_repeated_all_state(report):
    return pb02_runner._is_repeated_all_state(report)


def _checkpoint_memberships(path, report, case, contract):
    if (
        report.get("candidate") != CANDIDATE_ID
        or not _load_matches(report, case)
        or report.get("source_sha256") != _native_source_inventory()
        or report.get("pb03_diagnostic_identity")
        != contract["deterministic_input_fingerprint"]
        or report.get("pb03_model_identity") != _model_identity(path, case, contract)
    ):
        raise ValueError(f"{case}: checkpoint identity changed")
    bearings = report.get("bearings")
    axials = report.get("axial_tension")
    if not isinstance(bearings, list) or not isinstance(axials, list):
        raise TypeError(f"{case}: checkpoint unilateral state is incomplete")
    normal_names = sorted(
        {
            row["name"]
            for row in bearings
            if row.get("active") is True and not row["name"].endswith("_friction")
        }
        - set(report.get("axial_tension_names", ()))
    )
    axial_names = sorted(row["name"] for row in axials if row.get("active") is True)
    if not set(axial_names) <= set(report.get("axial_tension_names", ())):
        raise ValueError(f"{case}: checkpoint axial inventory changed")
    return normal_names, axial_names


def _same_case_checkpoint(path, report, case, contract, max_cycles):
    if not _max_cycles_exhausted(report, max_cycles):
        raise ValueError(f"{case}: report is not a continuation checkpoint")
    return _checkpoint_memberships(path, report, case, contract)


def _same_case_repeated_seed(path, report, case, contract):
    if not _is_repeated_all_state(report):
        raise ValueError(f"{case}: report is not a repeated all-state checkpoint")
    return _checkpoint_memberships(path, report, case, contract)


def _attempt_summary(case, label, strategy, seed_case, continuation_from, path, report):
    return {
        "case": case,
        "attempt": label,
        "contact_update_strategy": strategy,
        "seeded_from_authenticated_a12_rear": seed_case == "a12-rear",
        "same_case_continuation_from_attempt": continuation_from,
        "contact_active_set_converged": report.get(
            "contact_active_set_converged", False
        ),
        "numerically_accepted": report.get("numerically_accepted", False),
        "termination": report.get("termination"),
        "native_report_sha256": hashlib.sha256(
            (path / "report.json").read_bytes()
        ).hexdigest(),
        "forces_in_suite_summary": False,
    }


def _write_accepted_scope(path, report, case, strategy, seed_case, contract):
    scope = {
        "case": case,
        "candidate": CANDIDATE_ID,
        "deterministic_input_fingerprint": contract["deterministic_input_fingerprint"],
        "contact_update_strategy": strategy,
        "search_seed_case": seed_case,
        "developmental_only": True,
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    scope_path = path / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope, indent=2, allow_nan=False) + "\n")
    report["diagnostic_scope"] = scope
    report.update(
        qualified_for_design=False,
        acceptance=False,
        drilling_released=False,
        fabrication_released=False,
    )
    report["artifact_sha256"][scope_path.name] = hashlib.sha256(
        scope_path.read_bytes()
    ).hexdigest()
    (path / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )


def run_suite(
    output=DEFAULT_OUTPUT,
    *,
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
    floor_contact_n_per_mm=1.0e5,
    contact_grid_resolution=2,
    max_cycles=120,
    max_same_case_continuations=3,
    cases=CASE_ORDER,
):
    """Run the first decisive case or the exact six-case authenticated suite."""
    cases = tuple(cases)
    if cases not in (CASE_ORDER, ("a12-forward",)):
        raise ValueError("cases must be the exact suite or only a12-forward")
    if type(max_cycles) is not int or max_cycles < 1:
        raise ValueError("max_cycles must be a positive integer")
    if type(max_same_case_continuations) is not int or max_same_case_continuations < 0:
        raise ValueError("max_same_case_continuations must be nonnegative")
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    attempts_root = root / "attempts"
    attempts_root.mkdir()
    stiffnesses = _selected_stiffnesses(
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
        floor_contact_n_per_mm,
        contact_grid_resolution,
    )
    contract = _preflight(stiffnesses)
    attempts = []
    accepted = {}

    def attempt(
        case,
        label,
        strategy,
        seed_names=None,
        seed_axial_names=None,
        seed_case=None,
        continuation_from=None,
    ):
        path = attempts_root / f"{case}-{label}"
        report = _run_attempt(
            case,
            path,
            strategy=strategy,
            contract=contract,
            max_cycles=max_cycles,
            initial_contact_names=seed_names,
            initial_axial_tension_names=seed_axial_names,
        )
        if _is_active_set_nonconvergence(report):
            attempts.append(
                _attempt_summary(
                    case,
                    label,
                    strategy,
                    seed_case,
                    continuation_from,
                    path,
                    report,
                )
            )
            return report
        validated = _validate_accepted_report(report, case, contract)
        _write_accepted_scope(path, validated, case, strategy, seed_case, contract)
        attempts.append(
            _attempt_summary(
                case,
                label,
                strategy,
                seed_case,
                continuation_from,
                path,
                validated,
            )
        )
        accepted[case] = {
            "attempt": label,
            "path": str(path.relative_to(root)),
            "report_sha256": hashlib.sha256(
                (path / "report.json").read_bytes()
            ).hexdigest(),
            "contact_update_strategy": strategy,
            "search_seed_case": seed_case,
            "numerically_accepted": True,
            "forces_reported_only_in_authenticated_case_report": True,
        }
        return validated

    def continue_same_case(case, report, prior_label, label_prefix="03"):
        for index in range(1, max_same_case_continuations + 1):
            if case in accepted or not _max_cycles_exhausted(report, max_cycles):
                break
            prior_path = attempts_root / f"{case}-{prior_label}"
            normals, axials = _same_case_checkpoint(
                prior_path, report, case, contract, max_cycles
            )
            label = f"{label_prefix}-one-at-a-time-same-case-continuation-{index:02d}"
            report = attempt(
                case,
                label,
                "one_at_a_time",
                seed_names=normals,
                seed_axial_names=axials,
                continuation_from=prior_label,
            )
            prior_label = label
        return report

    def start_one_at_a_time(case, report):
        prior_label = "01-all-unseeded"
        if _is_repeated_all_state(report):
            prior_path = attempts_root / f"{case}-{prior_label}"
            normals, axials = _same_case_repeated_seed(
                prior_path, report, case, contract
            )
            label = "02-one-at-a-time-seeded-from-repeated-all"
            return (
                attempt(
                    case,
                    label,
                    "one_at_a_time",
                    seed_names=normals,
                    seed_axial_names=axials,
                    continuation_from=prior_label,
                ),
                label,
            )
        label = "02-one-at-a-time-unseeded"
        return attempt(case, label, "one_at_a_time"), label

    forward = attempt("a12-forward", "01-all-unseeded", "all")
    if "a12-forward" not in accepted:
        forward, forward_label = start_one_at_a_time("a12-forward", forward)
        forward = continue_same_case("a12-forward", forward, forward_label)
    if "a12-forward" not in accepted and cases == CASE_ORDER:
        rear = attempt("a12-rear", "01-all-unseeded", "all")
        if "a12-rear" not in accepted:
            rear, rear_label = start_one_at_a_time("a12-rear", rear)
            rear = continue_same_case("a12-rear", rear, rear_label)
        if "a12-rear" not in accepted:
            raise RuntimeError("a12-rear cannot authenticate the forward seed")
        forward = attempt(
            "a12-forward",
            "90-one-at-a-time-seeded-from-a12-rear",
            "one_at_a_time",
            seed_names=_normal_contact_seed(rear),
            seed_case="a12-rear",
        )
        forward = continue_same_case(
            "a12-forward",
            forward,
            "90-one-at-a-time-seeded-from-a12-rear",
            label_prefix="91",
        )
    if "a12-forward" not in accepted:
        raise RuntimeError("a12-forward active set did not converge")

    for case in cases[1:]:
        if case in accepted:
            continue
        report = attempt(case, "01-all-unseeded", "all")
        if case not in accepted:
            report, label = start_one_at_a_time(case, report)
            continue_same_case(case, report, label)
        if case not in accepted:
            raise RuntimeError(f"{case} active set did not converge")
    if set(accepted) != set(cases):
        raise ValueError("Accepted PB03 case inventory changed")

    ordered = {case: accepted[case] for case in cases}
    summary = {
        **contract,
        "validation": {
            "candidate_and_mechanics_identity": True,
            "topology_and_stiffness_inventory": True,
            "producer_source_inventory": True,
            "accepted_case_equilibrium_audits": True,
        },
        "attempts": attempts,
        "accepted_cases": ordered,
        "accepted_case_count": len(ordered),
        "rejected_attempt_forces_included": False,
        "max_cycles_per_attempt": max_cycles,
        "max_same_case_continuations": max_same_case_continuations,
        "developmental_only": True,
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    (root / "pb03-eight-station-diagnostic.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bolt-axial-n-per-mm", type=float, required=True)
    parser.add_argument("--bolt-lateral-n-per-mm", type=float, required=True)
    parser.add_argument("--face-normal-total-n-per-mm", type=float, required=True)
    parser.add_argument("--floor-contact-n-per-mm", type=float, default=1.0e5)
    parser.add_argument("--contact-grid-resolution", type=int, default=2)
    parser.add_argument("--max-cycles", type=int, default=120)
    parser.add_argument("--max-same-case-continuations", type=int, default=3)
    parser.add_argument("--first-case-only", action="store_true")
    args = parser.parse_args()
    result = run_suite(
        args.output,
        bolt_axial_n_per_mm=args.bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm=args.bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm=args.face_normal_total_n_per_mm,
        floor_contact_n_per_mm=args.floor_contact_n_per_mm,
        contact_grid_resolution=args.contact_grid_resolution,
        max_cycles=args.max_cycles,
        max_same_case_continuations=args.max_same_case_continuations,
        cases=("a12-forward",) if args.first_case_only else CASE_ORDER,
    )
    print(
        json.dumps(
            {
                "deterministic_input_fingerprint": result[
                    "deterministic_input_fingerprint"
                ],
                "accepted_case_count": result["accepted_case_count"],
                "qualified_for_design": result["qualified_for_design"],
                "drilling_released": result["drilling_released"],
            },
            indent=2,
        )
    )
