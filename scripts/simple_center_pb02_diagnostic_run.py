"""Run the source-bound PB02 six-case developmental diagnostic.

This runner authenticates numerical response only.  It does not qualify the
trial stiffnesses, establish joint resistance, or release drilling/fabrication.
Rejected active-set attempts may guide the prescribed search sequence, but
their forces are never copied into the accepted case record or suite summary.
"""

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path

from fea import current_response_run as native
from fea.reinforced_frame_demand import repository_source_closure
from scripts.clear_space_batch import CASES
from scripts.simple_center_pb02_native import (
    CANDIDATE_ID,
    PB02Native,
    native_row_inventory,
    prepare_case,
    screen,
)

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
EXPECTED_VERTICAL_FORCE_N = -2.0 * 250.0 * 0.45359237 * 9.80665
SHIFTED_POST_HEADER_CONTACTS = {
    f"pb02_shifted_post_header_compression_{i}_{j}" for i in (1, 2) for j in (1, 2)
}
PRODUCER_PATHS = tuple(
    repository_source_closure(
        [
            Path(__file__),
            ROOT / "scripts/simple_center_pb02_native.py",
            ROOT / "scripts/simple_center_published_stiffness_basis.py",
        ],
        packages=("fea", "mini_moonboard", "scripts"),
    )
)
LOADED_PRODUCER_SHA256 = native.extra_source_hashes(PRODUCER_PATHS)


def _canonical_sha256(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _selected_stiffnesses(
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
):
    values = {
        "bolt_axial_n_per_mm": bolt_axial_n_per_mm,
        "bolt_lateral_n_per_mm": bolt_lateral_n_per_mm,
        "face_normal_total_per_interface_n_per_mm": (face_normal_total_n_per_mm),
    }
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or value <= 0
        for value in values.values()
    ):
        raise ValueError("PB02 trial stiffnesses must be positive and finite")
    return {
        "exact_selected_values": values,
        "selection_status": "explicit developmental trial inputs",
        "published_basis_record": (
            "scripts/simple_center_published_stiffness_basis.py"
        ),
        "complete_joint_stiffness_qualified": False,
    }


def _source_inventory():
    current = native.extra_source_hashes(PRODUCER_PATHS)
    if current != LOADED_PRODUCER_SHA256:
        raise ValueError("PB02 producer changed after import; restart the run")
    return current


def _native_source_inventory():
    """Return the exact source inventory embedded in a fresh native model."""
    return {**native.source_hashes(), **_source_inventory()}


def _preflight(stiffnesses):
    if set(CASES) != set(EXPECTED_LOADS) or any(
        CASES[name] != expected for name, expected in EXPECTED_LOADS.items()
    ):
        raise ValueError("PB02 unchanged six-case load inventory changed")
    geometry = screen()
    expected_rows = {
        "bolt_shear": 20,
        "bolt_tension": 10,
        "contact_compression": 28,
    }
    if (
        geometry.get("candidate") != CANDIDATE_ID
        or geometry.get("panel_kicker_axis_count") != 66
        or geometry.get("legacy_proxy_station_count") != 22
        or geometry.get("native_rows") != expected_rows
        or geometry.get("qualified_for_design") is not False
        or geometry.get("drilling_released") is not False
    ):
        raise ValueError("PB02 geometry, topology, or claim inventory changed")
    sources = _source_inventory()
    identity = {
        "schema": "simple_center_pb02_diagnostic_run/v1",
        "candidate": CANDIDATE_ID,
        "active_geometry_fingerprint": geometry["active_fingerprint"],
        "case_order": list(CASE_ORDER),
        "loads": {
            name: {"hold": hold, "horizontal_force_xy_n": list(force)}
            for name, (hold, force) in EXPECTED_LOADS.items()
        },
        "geometry_inventory": geometry,
        "stiffness_selection": stiffnesses,
        "producer_source_sha256": sources,
    }
    return identity | {"deterministic_input_fingerprint": _canonical_sha256(identity)}


def _normal_contact_seed(report):
    """Extract search state only from an authenticated accepted report."""
    if report.get("numerically_accepted") is not True:
        raise ValueError("Only an authenticated accepted report may seed contacts")
    names = [
        row["name"]
        for row in report["bearings"]
        if row["active"] and not row["name"].endswith("_friction")
    ]
    axial = set(report.get("axial_tension_names", ()))
    names = sorted(set(names) - axial)
    if not names:
        raise ValueError("Accepted a12-rear result has no normal-contact seed")
    return names


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


def _validate_accepted_report(report, case, stiffnesses):
    """Reject a converged-looking report with mismatched identity or audits."""
    required = (
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
        raise ValueError(f"{case}: load inventory changed")
    if any(report.get(key) is not True for key in required):
        raise ValueError(f"{case}: accepted numerical/equilibrium audits failed")
    if len(report.get("angle_stations", ())) != 22:
        raise ValueError(f"{case}: retained proxy topology changed")

    rows = native_row_inventory()
    bolt_rows = _bolt_row_inventory(rows)
    bolt_names = set(bolt_rows)
    contact_names = {
        row["name"] for row in rows if row["kind"] == "contact_compression"
    }
    physical = report.get("physical_connection_forces", {})
    physical_names = set(physical)
    required_names = bolt_names | contact_names | SHIFTED_POST_HEADER_CONTACTS
    if not required_names <= physical_names:
        raise ValueError(f"{case}: PB02 physical-force topology is incomplete")
    for name in bolt_names:
        if set(physical[name].get("source_rows", ())) != bolt_rows[name]:
            raise ValueError(f"{case}: {name} does not own its three canonical rows")
    for name in required_names:
        force = physical[name].get("force_on_first_xyz_n")
        if (
            not isinstance(force, list)
            or len(force) != 3
            or any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in force
            )
        ):
            raise ValueError(f"{case}: {name} has a non-finite force vector")
    if set(report.get("axial_tension_names", ())) != bolt_names:
        raise ValueError(f"{case}: PB02 tension-only bolt inventory changed")
    if report.get("pb02_stiffness_verification") != stiffnesses:
        raise ValueError(f"{case}: solved PB02 stiffness inventory is unauthenticated")

    expected_sources = _source_inventory()
    reported_sources = report.get("source_sha256", {})
    if any(
        reported_sources.get(name) != digest
        for name, digest in expected_sources.items()
    ):
        raise ValueError(f"{case}: producer source inventory is unauthenticated")
    return report


def _bolt_row_inventory(rows):
    """Group three canonical spring rows under each physical PB02 bolt."""
    bolt_rows = {}
    for row in rows:
        if row["kind"].startswith("bolt_"):
            name = row["name"].rsplit("/", 1)[0]
            bolt_rows.setdefault(name, set()).add(row["name"])
    return bolt_rows


def _verify_model_stiffness(path, stiffnesses):
    """Tie selected trial values to the generated native model artifact."""
    model_path = path / "model.pkl"
    with model_path.open("rb") as source:
        payload = pickle.load(source)
    structure, metadata = payload["model"]
    values = stiffnesses["exact_selected_values"]
    expected_metadata = {
        "bolt_axial": values["bolt_axial_n_per_mm"],
        "bolt_lateral": values["bolt_lateral_n_per_mm"],
        "face_normal_total_per_interface": values[
            "face_normal_total_per_interface_n_per_mm"
        ],
    }
    if metadata.get("pb02_trial_stiffness_n_per_mm") != expected_metadata:
        raise ValueError("Generated model PB02 stiffness metadata changed")

    rows = native_row_inventory()
    bolt_names = {
        row["name"].removesuffix("/tension")
        for row in rows
        if row["kind"] == "bolt_tension"
    }
    canonical_contacts = {
        row["name"] for row in rows if row["kind"] == "contact_compression"
    }
    bolt_springs = [
        spring for spring in structure.springs if spring["name"] in bolt_names
    ]
    contacts = [
        spring
        for spring in structure.springs
        if spring["name"] in canonical_contacts | SHIFTED_POST_HEADER_CONTACTS
    ]
    if (
        len(bolt_springs) != 30
        or sum(spring["dof"] == 1 for spring in bolt_springs) != 10
        or sum(spring["dof"] in (2, 3) for spring in bolt_springs) != 20
        or any(
            not math.isclose(
                spring["stiffness_n_per_mm"],
                values[
                    "bolt_axial_n_per_mm"
                    if spring["dof"] == 1
                    else "bolt_lateral_n_per_mm"
                ],
                abs_tol=1.0e-12,
            )
            for spring in bolt_springs
        )
        or len(contacts) != 32
        or any(
            not math.isclose(
                spring["stiffness_n_per_mm"],
                values["face_normal_total_per_interface_n_per_mm"] / 4.0,
                abs_tol=1.0e-12,
            )
            for spring in contacts
        )
    ):
        raise ValueError("Generated model PB02 spring stiffness inventory changed")
    return stiffnesses


def _model_identity(path, case, stiffnesses):
    """Authenticate the generated model used by a continuation checkpoint."""
    model_path = path / "model.pkl"
    with model_path.open("rb") as source:
        payload = pickle.load(source)
    structure, metadata = payload["model"]
    del structure
    hold, horizontal = EXPECTED_LOADS[case]
    expected_force = [*horizontal, EXPECTED_VERTICAL_FORCE_N]
    values = stiffnesses["exact_selected_values"]
    expected_pb02 = {
        "bolt_axial": values["bolt_axial_n_per_mm"],
        "bolt_lateral": values["bolt_lateral_n_per_mm"],
        "face_normal_total_per_interface": values[
            "face_normal_total_per_interface_n_per_mm"
        ],
    }
    if (
        payload.get("source_sha256") != _native_source_inventory()
        or metadata.get("candidate") != CANDIDATE_ID
        or metadata.get("hold") != hold
        or metadata.get("pounds") != 250.0
        or metadata.get("force_xyz_n") != expected_force
        or metadata.get("pb02_trial_stiffness_n_per_mm") != expected_pb02
    ):
        raise ValueError(f"{case}: generated model identity is unauthenticated")
    return hashlib.sha256(model_path.read_bytes()).hexdigest()


def _max_cycles_exhausted(report, max_cycles):
    """Recognize only a bounded one-at-a-time chunk that used every cycle."""
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


def _same_case_checkpoint(path, report, case, stiffnesses, max_cycles):
    """Return unilateral memberships, never forces, from one rejected chunk."""
    if not _max_cycles_exhausted(report, max_cycles):
        raise ValueError(f"{case}: report is not a max-cycle continuation checkpoint")
    if report.get("candidate") != CANDIDATE_ID:
        raise ValueError(f"{case}: checkpoint candidate identity changed")
    if not _load_matches(report, case):
        raise ValueError(f"{case}: checkpoint load identity changed")
    if report.get("source_sha256") != _native_source_inventory():
        raise ValueError(f"{case}: checkpoint source identity changed")
    if report.get("pb02_stiffness_verification") != stiffnesses:
        raise ValueError(f"{case}: checkpoint stiffness identity changed")
    if report.get("pb02_model_identity") != _model_identity(path, case, stiffnesses):
        raise ValueError(f"{case}: checkpoint model identity changed")

    bearings = report.get("bearings")
    axial_rows = report.get("axial_tension")
    if not isinstance(bearings, list) or not isinstance(axial_rows, list):
        raise TypeError(f"{case}: checkpoint unilateral state is incomplete")
    normal_names = {
        row["name"]
        for row in bearings
        if row.get("active") is True and not row["name"].endswith("_friction")
    }
    axial_names = {row["name"] for row in axial_rows if row.get("active") is True}
    axial_inventory = set(report.get("axial_tension_names", ()))
    if not axial_names <= axial_inventory or normal_names & axial_inventory:
        raise ValueError(f"{case}: checkpoint unilateral state is invalid")
    return sorted(normal_names), sorted(axial_names)


def _attempt_summary(case, label, strategy, seed_case, continuation_from, path, report):
    """Record search status without copying forces from a rejected result."""
    report_path = path / "report.json"
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
        "native_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "forces_in_suite_summary": False,
    }


def _run_attempt(
    case,
    path,
    *,
    strategy,
    stiffnesses,
    max_cycles,
    initial_contact_names=None,
    initial_axial_tension_names=None,
):
    values = stiffnesses["exact_selected_values"]
    module = PB02Native()
    report = native.run(
        path,
        module=module,
        expected_candidate=module.KEY,
        prepare_factory=lambda *args, **kwargs: prepare_case(
            case,
            bolt_axial_n_per_mm=values["bolt_axial_n_per_mm"],
            bolt_lateral_n_per_mm=values["bolt_lateral_n_per_mm"],
            face_normal_total_n_per_mm=(
                values["face_normal_total_per_interface_n_per_mm"]
            ),
        ),
        extra_source_paths=PRODUCER_PATHS,
        contact_update_strategy=strategy,
        initial_contact_names=initial_contact_names,
        initial_axial_tension_names=initial_axial_tension_names,
        max_cycles=max_cycles,
    )
    report["pb02_stiffness_verification"] = _verify_model_stiffness(path, stiffnesses)
    report["pb02_model_identity"] = _model_identity(path, case, stiffnesses)
    return report


def _is_active_set_nonconvergence(report):
    return (
        report.get("contact_active_set_converged") is not True
        or report.get("axial_tension_active_set_converged") is not True
    )


def _write_accepted_scope(path, report, case, strategy, seed_case, contract):
    scope = {
        "case": case,
        "candidate": CANDIDATE_ID,
        "deterministic_input_fingerprint": contract["deterministic_input_fingerprint"],
        "stiffness_selection": contract["stiffness_selection"],
        "contact_update_strategy": strategy,
        "search_seed_case": seed_case,
        "developmental_only": True,
        "qualified_for_design": False,
        "actual_joint_demands_qualified": False,
        "resistance_checked": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    scope_path = path / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope, indent=2, allow_nan=False) + "\n")
    report["diagnostic_scope"] = scope
    report["qualified_for_design"] = False
    report["drilling_released"] = False
    report["fabrication_released"] = False
    report["artifact_sha256"][scope_path.name] = hashlib.sha256(
        scope_path.read_bytes()
    ).hexdigest()
    (path / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )


def run_suite(
    output,
    *,
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
    max_cycles=120,
    max_same_case_continuations=3,
):
    """Run the prescribed six cases and return only authenticated case records."""
    if type(max_cycles) is not int or max_cycles < 1:
        raise ValueError("max_cycles must be a positive integer")
    if type(max_same_case_continuations) is not int or max_same_case_continuations < 0:
        raise ValueError("max_same_case_continuations must be a nonnegative integer")
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    attempts_root = root / "attempts"
    attempts_root.mkdir()
    stiffnesses = _selected_stiffnesses(
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
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
            stiffnesses=stiffnesses,
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
        validated = _validate_accepted_report(report, case, stiffnesses)
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
        """Run at most the configured number of same-case continuation chunks."""
        for index in range(1, max_same_case_continuations + 1):
            if case in accepted or not _max_cycles_exhausted(report, max_cycles):
                break
            prior_path = attempts_root / f"{case}-{prior_label}"
            normals, axials = _same_case_checkpoint(
                prior_path, report, case, stiffnesses, max_cycles
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

    forward = attempt("a12-forward", "01-all-unseeded", "all")
    if "a12-forward" not in accepted:
        forward = attempt("a12-forward", "02-one-at-a-time-unseeded", "one_at_a_time")
        forward = continue_same_case(
            "a12-forward", forward, "02-one-at-a-time-unseeded"
        )
    if "a12-forward" not in accepted:
        rear = attempt("a12-rear", "01-all-unseeded", "all")
        if "a12-rear" not in accepted:
            rear = attempt("a12-rear", "02-one-at-a-time-unseeded", "one_at_a_time")
            rear = continue_same_case("a12-rear", rear, "02-one-at-a-time-unseeded")
        if "a12-rear" not in accepted:
            raise RuntimeError(
                "a12-rear did not converge; unauthenticated state cannot seed forward"
            )
        seed = _normal_contact_seed(rear)
        forward = attempt(
            "a12-forward",
            "90-one-at-a-time-seeded-from-a12-rear",
            "one_at_a_time",
            seed_names=seed,
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

    for case in CASE_ORDER[1:]:
        if case in accepted:
            continue
        report = attempt(case, "01-all-unseeded", "all")
        if case not in accepted:
            report = attempt(case, "02-one-at-a-time-unseeded", "one_at_a_time")
            report = continue_same_case(case, report, "02-one-at-a-time-unseeded")
        if case not in accepted:
            raise RuntimeError(f"{case} active set did not converge")

    if set(accepted) != set(CASE_ORDER):
        raise ValueError("Accepted PB02 case inventory changed")
    ordered_accepted = {case: accepted[case] for case in CASE_ORDER}
    summary = {
        **contract,
        "validation": {
            "geometry_inventory": True,
            "topology_inventory": True,
            "candidate_identity": True,
            "stiffness_inventory": True,
            "producer_source_inventory": True,
            "six_case_load_inventory": True,
            "all_accepted_case_equilibrium_audits": True,
        },
        "attempts": attempts,
        "accepted_cases": ordered_accepted,
        "accepted_case_count": len(ordered_accepted),
        "rejected_attempt_forces_included": False,
        "max_cycles_per_attempt": max_cycles,
        "max_same_case_continuations": max_same_case_continuations,
        "developmental_only": True,
        "qualified_for_design": False,
        "actual_joint_demands_qualified": False,
        "resistance_checked": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    (root / "pb02-six-case-diagnostic.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bolt-axial-n-per-mm", type=float, required=True)
    parser.add_argument("--bolt-lateral-n-per-mm", type=float, required=True)
    parser.add_argument("--face-normal-total-n-per-mm", type=float, required=True)
    parser.add_argument("--max-cycles", type=int, default=120)
    parser.add_argument("--max-same-case-continuations", type=int, default=3)
    args = parser.parse_args()
    result = run_suite(
        args.output,
        bolt_axial_n_per_mm=args.bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm=args.bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm=args.face_normal_total_n_per_mm,
        max_cycles=args.max_cycles,
        max_same_case_continuations=args.max_same_case_continuations,
    )
    print(
        json.dumps(
            {
                "deterministic_input_fingerprint": result[
                    "deterministic_input_fingerprint"
                ],
                "accepted_case_count": result["accepted_case_count"],
                "developmental_only": result["developmental_only"],
                "qualified_for_design": result["qualified_for_design"],
                "drilling_released": result["drilling_released"],
            },
            indent=2,
        )
    )
