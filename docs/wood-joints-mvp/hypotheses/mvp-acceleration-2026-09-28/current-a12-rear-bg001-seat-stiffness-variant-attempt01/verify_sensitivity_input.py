"""Run source-pinned, read-only input checks and negative mutation probes."""
from __future__ import annotations

import copy
from difflib import SequenceMatcher
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
BASELINE_PACKET = SERIES / "current-springa-selected-floor-a12-rear-attempt03"
VARIANT_PACKET = HERE
VALIDATOR_PATH = HERE / "validate_sensitivity_input.py"
RESPONSE_CORE_PATH = HERE / "sensitivity_response_core.py"
OUTPUT = HERE / "sensitivity_input_contract_check.json"


def import_response_core():
    spec = importlib.util.spec_from_file_location("sensitivity_response_core", RESPONSE_CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the pinned 711-derived response-core fork")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect_reject(label: str, expected_text: str, call: Callable[[], object]) -> dict:
    try:
        call()
    except Exception as error:
        if expected_text.lower() not in str(error).lower():
            raise AssertionError(
                f"{label}: rejected for unexpected reason {error!s}"
            ) from error
        return {"name": label, "rejected": True, "reason": str(error)}
    raise AssertionError(f"negative mutation was accepted: {label}")


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Unsupported report value: {type(value).__name__}")


def _synthetic_recovery_checks(validator, core_contract, record, deck):
    """Exercise the pinned SPRINGA recovery method on constructed exact states."""
    auditor = validator._load_precision_auditor()
    node_points = auditor.parse_node_cards(deck)
    bindings_by_group = {row["group"]: row for row in core_contract["bindings"]}
    reports = []
    for group in ("SPR1771", "SPR1772"):
        binding = bindings_by_group[group]
        source = core_contract["source_by_group"][group]
        q_node, ground = map(int, binding["springa_nodes"])
        first_projection, second_projection = map(int, binding["source_projection_nodes"])
        dof = int(binding["source_projection_dof"]) - 1
        axis = np.asarray(binding["numerical_axis_global_xyz"], dtype=float)
        initial_vector = np.asarray(node_points[q_node]) - np.asarray(node_points[ground])
        initial_length = float(np.linalg.norm(initial_vector))
        for q in (2.0, -0.45):
            zeros = lambda: np.zeros(3, dtype=float)
            u = {node: zeros() for node in (q_node, ground, first_projection, second_projection)}
            u_radius = {node: zeros() for node in u}
            rf = {node: zeros() for node in u}
            rf_radius = {node: zeros() for node in u}
            u[second_projection][dof] = q
            u[q_node][0] = q
            q_vector = u[q_node] - u[ground]
            elongation = float(np.linalg.norm(initial_vector + q_vector) - initial_length)
            analytic_force = float(binding["stiffness_n_per_mm"]) * max(elongation, 0.0)
            rf[q_node] = analytic_force * axis
            rf[ground] = -analytic_force * axis
            state = {"u": u, "u_radius": u_radius, "rf": rf, "rf_radius": rf_radius}
            internal, radius, check = auditor.audit_springa(binding, source, state, node_points)
            if radius != 0.0 or not check["native_endpoint_action_reaction_passed"]:
                raise AssertionError(f"Synthetic endpoint recovery failed at {group}, q={q}")
            if abs(internal - analytic_force) > 1.0e-8:
                raise AssertionError(f"Variant slope recovery differs from analytic answer at {group}, q={q}")
            if abs(check["native_table_force_N_from_actual_dd_minus_dd0"] - analytic_force) > 1.0e-8:
                raise AssertionError(f"Native geometric table answer differs at {group}, q={q}")
            base_force = 4670.054188242363 * max(elongation, 0.0)
            if q > 0 and abs(base_force - analytic_force) < 1000.0:
                raise AssertionError("Synthetic positive state does not distinguish the baseline slope")
            reports.append({
                "group": group,
                "q_projection_mm": q,
                "geometric_elongation_mm": elongation,
                "variant_analytic_force_N": analytic_force,
                "recovered_internal_force_N": internal,
                "baseline_slope_force_N_at_same_elongation": base_force,
                "endpoint_action_reaction_passed": check["native_endpoint_action_reaction_passed"],
                "physical_first_body_action_xyz_N": check["physical_force_on_first_body_xyz_n"],
                "numerical_ground_excluded": check["numerical_ground_rf_excluded_from_physical_balance"],
            })
    return reports


def _response_core_replays(validator, contract, core):
    parent_source = core.PINNED_711_RESPONSE.read_text()
    fork_source = RESPONSE_CORE_PATH.read_text()
    parse_start = "    parsed = parse_native_blocks(data)"
    parent_body_start = parent_source.index(parse_start, parent_source.index("def audit_record("))
    fork_body_start = fork_source.index(parse_start, fork_source.index("def _audit_record_with_contract("))
    parent_body = parent_source[parent_body_start:parent_source.index("\n\ndef main()", parent_body_start)].splitlines()
    fork_body = fork_source[fork_body_start:fork_source.index("\n\ndef main()", fork_body_start)].splitlines()
    changes = [entry for entry in SequenceMatcher(a=parent_body, b=fork_body, autojunk=False).get_opcodes()
               if entry[0] != "equal"]
    if len(changes) != 3:
        raise AssertionError("Response-core fork changed pinned 711 mechanics beyond the approved report assembly")
    expected_changes = (
        ("replace", ["    return {"], ["    report = {"]),
        ("replace", ['        "case_context_provenance": contract["case_context_provenance"],'],
         ['        "case_context_provenance": contract.get("case_context_provenance"),']),
        ("insert", [], [
            "    if contract.get(\"_sensitivity_contract_mode\") is not None:",
            "        report[\"case_context_provenance\"] = None",
            "        report[\"sensitivity_input_contract_provenance\"] = contract[\"sensitivity_input_contract_provenance\"]",
            "    return report",
        ]),
    )
    observed_changes = tuple((tag, parent_body[i1:i2], fork_body[j1:j2])
                             for tag, i1, i2, j1, j2 in changes)
    if observed_changes != expected_changes:
        raise AssertionError("Response-core fork changed pinned 711 mechanics outside report metadata handling")

    baseline_record = json.loads((BASELINE_PACKET / "model.json").read_text())
    baseline_deck_path = BASELINE_PACKET / "model.inp"
    baseline_deck = baseline_deck_path.read_text()
    baseline_data = (BASELINE_PACKET / "model.dat").read_text()
    prior_report = json.loads((BASELINE_PACKET / "response.json").read_text())
    baseline_model_path = BASELINE_PACKET / "model.json"
    class FakeContract:
        def build_baseline_response_core_contract(self, *args, **kwargs):
            return {}

        def build_response_core_contract(self, *args, **kwargs):
            return {}

    rejected_contracts = []
    for label, fake in (("plain dictionary", {}), ("duck-typed fake builder", FakeContract())):
        try:
            core.audit_record_with_validated_contract(
                baseline_record, "", baseline_deck,
                validated_contract=fake,
                model_path=baseline_model_path, deck_path=baseline_deck_path,
                contract_mode="baseline_replay",
            )
        except core.ResponseAuditError as error:
            if "validator-produced sealed sensitivity contract" not in str(error):
                raise AssertionError(f"{label} failed for an unexpected reason: {error}") from error
            rejected_contracts.append({"kind": label, "rejected": True})
        else:
            raise AssertionError(f"Unauthenticated {label} was accepted as a response contract")

    replay = core.audit_record_with_validated_contract(
        baseline_record, baseline_data, baseline_deck,
        validated_contract=contract,
        model_path=baseline_model_path, deck_path=baseline_deck_path,
        contract_mode="baseline_replay",
    )
    required_gates = (
        "mpc_interval_checks_passed", "springa_law_checks_passed",
        "retained_bilateral_checks_passed", "selected_floor_complementarity_passed",
        "inactive_floor_tangent_no_restraint_or_reaction_passed",
        "raw_body_and_global_balance_passed",
        "rounding_interval_body_and_global_balance_passed",
    )
    if replay.get("status") != prior_report.get("status"):
        raise AssertionError("Pinned 711 core baseline replay status differs from prior accepted A12-rear response")
    if any(replay.get(key) is not True or prior_report.get(key) is not True for key in required_gates):
        raise AssertionError("Pinned 711 core did not preserve all baseline physical response gates")
    if (replay["recovery_summary"]["native_increment_count"] != 7
            or replay["recovery_summary"]["nonlinear_springa_component_checks"] != 9044
            or replay["recovery_summary"]["active_exact_floor_tangent_reaction_rows_per_increment"] != 50
            or replay["recovery_summary"]["inactive_floor_tangent_rows_per_increment"] != 150):
        raise AssertionError("Pinned 711 baseline replay carrier, floor-row, or increment counts changed")
    if replay.get("case_context_provenance") is not None:
        raise AssertionError("Legacy A12-rear replay must not claim 711 standard case-context validation")
    provenance = replay.get("sensitivity_input_contract_provenance", {})
    if (provenance.get("contract_mode") != "baseline_replay"
            or provenance.get("standard_711_case_context_validation_passed") is not False):
        raise AssertionError("Baseline replay provenance is not explicitly marked as sealed legacy input validation")

    # Zero-U precision radii may differ; raw native-derived physical forces and
    # printed balances must remain identical to the accepted baseline report.
    precision_comparison = []
    if len(replay["increments"]) != len(prior_report["increments"]):
        raise AssertionError("Baseline response increment count changed")
    for current, previous in zip(replay["increments"], prior_report["increments"], strict=True):
        if current["time"] != previous["time"] or current["load_factor"] != previous["load_factor"]:
            raise AssertionError("Baseline response time/load-factor sequence changed")
        current_forces, previous_forces = current["physical_connection_forces"], previous["physical_connection_forces"]
        if current_forces.keys() != previous_forces.keys():
            raise AssertionError("Baseline physical connection force inventory changed")
        if len(current_forces) != 1466 or len(current["physical_balance"]["body_equilibrium"]) != 50:
            raise AssertionError("Baseline replay changed its 1,466 physical-force-owner/50-body audit scope")
        max_force_delta = 0.0
        for owner in current_forces:
            for field in ("force_on_first_xyz_n", "force_on_second_xyz_n"):
                delta = np.asarray(current_forces[owner][field], dtype=float) - np.asarray(previous_forces[owner][field], dtype=float)
                max_force_delta = max(max_force_delta, float(np.max(np.abs(delta))))
                if not np.array_equal(current_forces[owner][field], previous_forces[owner][field]):
                    raise AssertionError(f"Baseline raw recovered connector force changed at {owner}/{field}")
        for balance_kind in ("global_equilibrium", "body_equilibrium"):
            current_balance = current["physical_balance"][balance_kind]
            previous_balance = previous["physical_balance"][balance_kind]
            if current_balance.keys() != previous_balance.keys():
                raise AssertionError(f"Baseline {balance_kind} inventory changed")
            rows = ([("global", current_balance, previous_balance)]
                    if balance_kind == "global_equilibrium" else
                    [(name, current_balance[name], previous_balance[name]) for name in current_balance])
            for name, current_row, previous_row in rows:
                for field in ("force_residual_xyz_n", "moment_residual_xyz_nmm"):
                    if current_row[field] != previous_row[field]:
                        raise AssertionError(f"Baseline printed balance changed at {balance_kind}/{name}/{field}")
        precision_comparison.append({
            "time": current["time"],
            "max_raw_connector_force_delta_N": max_force_delta,
            "raw_connector_forces_identical": True,
            "printed_global_and_50_body_balance_identical": True,
            "rounding_interval_identity_required": False,
        })

    variant_record = json.loads((VARIANT_PACKET / "model.json").read_text())
    variant_deck_path = VARIANT_PACKET / "model.inp"
    variant_deck = variant_deck_path.read_text()
    variant_contract = contract.build_response_core_contract(
        variant_record, variant_deck,
        model_path=VARIANT_PACKET / "model.json", deck_path=variant_deck_path,
    )
    native_states = core.parse_native_blocks(baseline_data)
    changed_binding_rows = []
    for group in ("SPR1771", "SPR1772"):
        binding = next(row for row in variant_contract["bindings"] if row["group"] == group)
        source = variant_contract["source_by_group"][group]
        failed_times = []
        failure_messages = []
        for time, state in native_states.items():
            try:
                core.audit_springa(binding, source, state, variant_contract["emitted_nodes"])
            except Exception as error:
                if "endpoint RF does not intersect its nonlinear table law" not in str(error):
                    raise
                failed_times.append(time)
                failure_messages.append(str(error))
        if not failed_times:
            raise AssertionError(f"Old A12 data unexpectedly satisfies variant law at {group}")
        changed_binding_rows.append({
            "group": group,
            "law_mismatch_times": failed_times,
            "first_pinned_core_failure": failure_messages[0],
        })

    try:
        core.audit_record_with_validated_contract(
            variant_record, baseline_data, variant_deck,
            validated_contract=contract,
            model_path=VARIANT_PACKET / "model.json", deck_path=variant_deck_path,
            contract_mode="approved_sensitivity_variant",
        )
    except Exception as error:
        stale_rejected = str(error)
    else:
        raise AssertionError("Old baseline DAT was accepted under the changed two-tie stiffness")
    if ("SPRINGA endpoint RF does not intersect its nonlinear table law" not in stale_rejected
            or not any(group in stale_rejected for group in ("SPR1771", "SPR1772"))):
        raise AssertionError(f"Stale baseline output was rejected for an unexpected reason: {stale_rejected}")
    return {
        "pinned_711_core_baseline_replay": "PASS",
        "pinned_711_physical_core_copy": {
            "source_body_lines": len(parent_body),
            "fork_body_lines": len(fork_body),
            "mechanics_body_unchanged": True,
            "only_changes": ["report dictionary assignment", "case-context value lookup", "conditional sensitivity provenance serialization"],
        },
        "baseline_physical_gate_names": list(required_gates),
        "baseline_increment_count": len(replay["increments"]),
        "baseline_springa_checks": replay["recovery_summary"]["nonlinear_springa_component_checks"],
        "physical_force_owner_count_per_increment": 1466,
        "physical_body_balance_count_per_increment": 50,
        "baseline_force_and_printed_balance_comparison_to_pinned_prior_report": precision_comparison,
        "zero_u_token_interval_identity_required": False,
        "711_standard_case_context_validation_passed": False,
        "711_context_reason": "A12-rear legacy screen pins the prior selected-branch outputs, not the exact all-bearing controls model/deck required by the standard 711 context path.",
        "unauthenticated_contract_probes": rejected_contracts,
        "stale_baseline_dat_under_variant": {
            "rejected": True,
            "reason": stale_rejected,
            "changed_binding_law_mismatches": changed_binding_rows,
            "no_variant_force_report_emitted": True,
        },
    }


def main() -> None:
    core = import_response_core()
    validator = core.load_sensitivity_input_validator()
    contract = validator.validate_prepared_variant()
    baseline = json.loads((BASELINE_PACKET / "model.json").read_text())
    baseline_deck = (BASELINE_PACKET / "model.inp").read_text()
    variant_path, deck_path = VARIANT_PACKET / "model.json", VARIANT_PACKET / "model.inp"
    variant = json.loads(variant_path.read_text())
    variant_deck = deck_path.read_text()
    core_contract = contract.build_response_core_contract(
        variant, variant_deck, model_path=variant_path, deck_path=deck_path,
    )
    if core_contract["bindings"] != variant["unilateral_springa_bindings"]:
        raise AssertionError("Validated core contract does not contain the exact variant bindings")
    if len(core_contract["bindings"]) != 1292 or len(core_contract["springs"]) != 348:
        raise AssertionError("Validated core contract carrier counts changed")
    synthetic_recovery = _synthetic_recovery_checks(validator, core_contract, variant, variant_deck)
    response_core_replays = _response_core_replays(validator, contract, core)

    mutations = []
    wrong_table = copy.deepcopy(variant)
    row = next(row for row in wrong_table["unilateral_springa_bindings"]
               if row["group"] == "SPR1771")
    row["force_vs_elongation_table_N_mm"][2][0] += 1.0
    row2 = next(row for row in wrong_table["nonlinear_native_carrier_bindings"]
                if row["group"] == "SPR1771")
    row2["force_vs_elongation_table_N_mm"][2][0] += 1.0
    mutations.append(_expect_reject(
        "wrong approved-tie table slope", "force table does not match",
        lambda: validator._validate_pair_content(baseline, baseline_deck, wrong_table, variant_deck),
    ))

    third_spring = copy.deepcopy(variant)
    third = next(row for row in third_spring["unilateral_springa_bindings"]
                 if row["group"] not in {"SPR1771", "SPR1772"})
    third["stiffness_n_per_mm"] *= 1.01
    third["force_vs_elongation_table_N_mm"][2][0] = third["stiffness_n_per_mm"] * 10.0
    mutations.append(_expect_reject(
        "third spring stiffness override", "unapproved difference",
        lambda: validator._validate_pair_content(baseline, baseline_deck, third_spring, variant_deck),
    ))

    changed_load = copy.deepcopy(variant)
    load_node = next(iter(changed_load["loads"]))
    changed_load["loads"][load_node][0] += 0.001
    mutations.append(_expect_reject(
        "source load change", "unapproved difference",
        lambda: validator._validate_pair_content(baseline, baseline_deck, changed_load, variant_deck),
    ))

    changed_geometry = copy.deepcopy(variant)
    geometry_node = next(iter(changed_geometry["nodes"]))
    changed_geometry["nodes"][geometry_node][0] += 1.0e-6
    mutations.append(_expect_reject(
        "geometry node change", "unapproved difference",
        lambda: validator._validate_pair_content(baseline, baseline_deck, changed_geometry, variant_deck),
    ))

    wrong_deck_slope = variant_deck.replace("24017.14359617,10.0", "24018.14359617,10.0", 1)
    mutations.append(_expect_reject(
        "wrong native table ordinate", "native table differs",
        lambda: validator._validate_pair_content(baseline, baseline_deck, variant, wrong_deck_slope),
    ))

    extra_deck_mutation = variant_deck.replace("*STEP,NLGEOM,NLGEOM=NO,INC=40",
                                              "*STEP,NLGEOM,NLGEOM=NO,INC=41", 1)
    mutations.append(_expect_reject(
        "native control card change", "unapproved changed lines",
        lambda: validator._validate_pair_content(baseline, baseline_deck, variant, extra_deck_mutation),
    ))

    if len(mutations) != 6 or not all(row["rejected"] for row in mutations):
        raise AssertionError("A negative mutation probe was not rejected")
    result = {
        "schema": "conditional_joint_stiffness_sensitivity_input_validation/v1",
        "status": "PASS_EXACT_TWO_TIE_SENSITIVITY_INPUT_CONTRACT",
        "native_solve_launched": False,
        "native_response_read": True,
        "new_native_output_generated": False,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "validator_source": str(VALIDATOR_PATH.relative_to(ROOT)),
        "validator_source_sha256": hashlib.sha256(VALIDATOR_PATH.read_bytes()).hexdigest(),
        "response_audit_source_sha256": contract.audit_source_sha256,
        "stable_recovery_source_sha256": contract.stable_recovery_source_sha256,
        "pinned_711_response_source_sha256": contract.precision_response_source_sha256,
        "pinned_711_recovery_source_sha256": contract.precision_recovery_source_sha256,
        "separate_response_core_fork_sha256": contract.response_core_fork_sha256,
        "validator_normalized_source_sha256": core.VALIDATOR_NORMALIZED_SOURCE_SHA256,
        "baseline_model_sha256": contract.baseline_model_sha256,
        "baseline_deck_sha256": contract.baseline_deck_sha256,
        "variant_model_sha256": contract.variant_model_sha256,
        "variant_deck_sha256": contract.variant_deck_sha256,
        "baseline_contract_gate_summary": contract.source_contract_summary,
        "approved_overrides": [
            {
                "name": name,
                "group": group,
                "source_inventory_row_index": index,
                "baseline_stiffness_n_per_mm": old_k,
                "variant_stiffness_n_per_mm": new_k,
            }
            for name, group, index, old_k, new_k in contract.approved_overrides
        ],
        "updated_contract_binding_count": len(core_contract["bindings"]),
        "updated_contract_retained_spring2_count": len(core_contract["springs"]),
        "synthetic_pinned_recovery_method_check": {
            "status": "PASS_SYNTHETIC_ANALYTIC_SPRINGA_RECOVERY",
            "native_solver_launched": False,
            "native_output_consumed": False,
            "cases": synthetic_recovery,
        },
        "pinned_711_response_core_replays": response_core_replays,
        "negative_mutation_probes": mutations,
        "response_audit_composition": {
            "frozen_711_audit_record_signature": "audit_record(record, data, deck, case_context)",
            "frozen_audit_record_revalidates_internally": True,
            "baseline_no_contract_path_unchanged": True,
            "variant_entrypoint": "sensitivity_response_core.audit_record_with_validated_contract(record, data, deck, *, validated_contract, model_path, deck_path, contract_mode='approved_sensitivity_variant')",
            "baseline_entrypoint": "sensitivity_response_core.audit_record_with_validated_contract(record, data, deck, *, validated_contract, model_path, deck_path, contract_mode='baseline_replay')",
            "validator_contract_authentication": "exact pinned ValidatedSensitivityContract class plus module-private seal; dictionary and fake-builder probes rejected",
            "711_case_context_validation_for_legacy_rear_screen": "not used; exact control-source binding is unavailable in the old screen provenance and is not asserted",
            "physical_core_method": "byte-copied from pinned 711 wrapper, with contract acquisition factored out; original 711 audit_record and frozen sources are unchanged",
        },
        "limits": [
            "This is input-contract validation, not an independent baseline response replay or acceptance.",
            "The selected-floor branch must be rechecked independently for the variant before any future frame response is used.",
            "The local scenario is a conditional sensitivity point, not a measured or physical stiffness bound.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False, default=_json_default) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
