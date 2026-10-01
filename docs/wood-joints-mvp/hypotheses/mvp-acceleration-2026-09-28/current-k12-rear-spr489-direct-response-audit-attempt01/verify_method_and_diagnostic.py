"""Read-only exact-input, scalar-map and rejected-DAT diagnostic checks."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
VALIDATOR_PATH = HERE / "validate_direct_master_input.py"
CORE_PATH = HERE / "response_core.py"
PREFLIGHT_MODULE_PATH = SERIES / "current-k12-rear-all-carrier-exception-preflight-attempt01/produce.py"
PREFLIGHT_DIAG_PATH = SERIES / "current-k12-rear-all-carrier-exception-preflight-attempt01/diagnosis.json"
PARENT_COUPON = SERIES / "current-k12-rear-direct-scalar-native-attempt01/parent-method-validation.json"
COUPON_DAT = SERIES / "current-k12-rear-direct-scalar-native-attempt01/model.dat"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(name: str, path: Path):
    loaded = sys.modules.get(name)
    if loaded is not None:
        if Path(getattr(loaded, "__file__", "")).resolve() != path.resolve():
            raise RuntimeError(f"Canonical module {name} is bound to another source path")
        return loaded
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _expect_reject(name: str, action: Callable[[], Any], error_types: tuple[type[BaseException], ...]) -> dict[str, Any]:
    try:
        action()
    except error_types as error:
        return {"name": name, "rejected": True, "reason": str(error)}
    raise AssertionError(f"Negative test was not rejected: {name}")


def _scalar_functional_fixture(core: Any, source_map: dict[str, Any]) -> dict[str, Any]:
    """Exercise only the linear map with synthetic algebra inputs, not native U/RF."""
    terms = source_map["scalar_coordinate_linear_functional"]
    axis = list(map(float, source_map["physical_owner_axis_global_xyz"]))
    first = source_map["source_interpolation_sides"]["first"]["master_shape_weights"]
    second = source_map["source_interpolation_sides"]["second"]["master_shape_weights"]
    synthetic: dict[str, dict[int, list[float]]] = {"u": {}, "u_radius": {}}
    for term in terms:
        node = int(term["node"])
        if node not in synthetic["u"]:
            synthetic["u"][node] = [0.0, 0.0, 0.0]
            synthetic["u_radius"][node] = [0.0, 0.0, 0.0]
        synthetic["u_radius"][node][int(term["dof"]) - 1] = 1.0e-9
    amplitude = 1.0e-3
    second_tags = {int(row["node"]) for row in second}
    first_tags = {int(row["node"]) for row in first}
    if len(second_tags) != 20 or len(first_tags) != 20 or second_tags & first_tags:
        raise AssertionError("Pinned map sides do not have the expected disjoint 20-node support")
    for node in second_tags:
        synthetic["u"][node][1] = amplitude * axis[1]
        synthetic["u"][node][2] = amplitude * axis[2]
    q_value, q_radius = core.recover_direct_source_coordinate(synthetic, terms)
    second_weight_sum = math.fsum(float(row["weight"]) for row in second)
    expected = amplitude * second_weight_sum * (axis[1] ** 2 + axis[2] ** 2)
    expected_radius = 1.0e-9 * math.fsum(abs(float(row["coefficient_in_equation"])) for row in terms)
    if not math.isclose(q_value, expected, rel_tol=0.0, abs_tol=1.0e-12):
        raise AssertionError(f"Direct scalar functional sign/value failed: {q_value} != {expected}")
    if not math.isclose(q_radius, expected_radius, rel_tol=1.0e-14, abs_tol=1.0e-25):
        raise AssertionError(f"Direct scalar rounding-radius propagation failed: {q_radius} != {expected_radius}")
    # Uniform translation on both interpolation sides must cancel in q.
    for node in synthetic["u"]:
        synthetic["u"][node][1] = 0.25
        synthetic["u"][node][2] = -0.125
    translation_q, translation_radius = core.recover_direct_source_coordinate(synthetic, terms)
    if abs(translation_q) > 1.0e-12 or translation_radius <= 0.0:
        raise AssertionError("Direct scalar functional did not cancel common translation / retain interval radius")
    return {
        "scope": "pure coefficient-map algebra; no native state, RF, physical force, or response is constructed",
        "mapped_master_dof_count": len(terms),
        "source_interpolation_node_counts": [len(first), len(second)],
        "known_affine_projection_q_mm": q_value,
        "expected_affine_projection_q_mm": expected,
        "propagated_token_radius_mm": q_radius,
        "expected_propagated_token_radius_mm": expected_radius,
        "common_translation_q_mm": translation_q,
        "common_translation_radius_mm": translation_radius,
        "positive_scalar_sign_and_radius_passed": True,
        "common_translation_cancellation_passed": True,
    }


def _old_dat_coordinate_diagnostic(validator: Any, core: Any,
                                   baseline_contract: dict[str, Any],
                                   source_map: dict[str, Any]) -> dict[str, Any]:
    baseline = validator.BASELINE_PACKET
    record = json.loads((baseline / "model.json").read_text())
    deck = (baseline / "model.inp").read_text()
    data = (baseline / "model.dat").read_text()
    context = json.loads((baseline / "case-context.json").read_text())
    m711 = validator._load_711()
    contract = baseline_contract
    parsed = core.parse_native_blocks(data)
    if len(parsed) != 7:
        raise AssertionError(f"Pinned original K12 DAT expected seven increments; got {len(parsed)}")
    binding = record["unilateral_springa_bindings"][validator.SOURCE_INDEX]
    axis = [float(x) for x in binding["numerical_axis_global_xyz"]]
    q_node, ground = map(int, binding["springa_nodes"])
    p_first, p_second = map(int, binding["source_projection_nodes"])
    legacy_fails: list[float] = []
    direct_passes: list[bool] = []
    rows = []
    for time, state in parsed.items():
        direct_q, direct_radius = core.recover_direct_source_coordinate(
            state, source_map["scalar_coordinate_linear_functional"],
        )
        ghost_q = math.fsum(
            (float(state["u"][q_node][i]) - float(state["u"][ground][i])) * axis[i]
            for i in range(3)
        )
        ghost_radius = math.fsum(
            abs(axis[i]) * (float(state["u_radius"][q_node][i]) + float(state["u_radius"][ground][i]))
            for i in range(3)
        )
        legacy_q = float(state["u"][p_second][0]) - float(state["u"][p_first][0])
        legacy_radius = float(state["u_radius"][p_second][0]) + float(state["u_radius"][p_first][0])
        guard = 32.0 * float.fromhex("0x1.0000000000000p-52") * max(1.0, abs(ghost_q), abs(legacy_q), abs(direct_q))
        legacy_pass = abs(ghost_q - legacy_q) <= ghost_radius + legacy_radius + guard
        direct_pass = abs(ghost_q - direct_q) <= ghost_radius + direct_radius + guard
        if not legacy_pass:
            legacy_fails.append(float(time))
        direct_passes.append(direct_pass)
        rows.append({
            "time": float(time),
            "old_projection_mean_q_mm": legacy_q,
            "old_projection_radius_mm": legacy_radius,
            "direct_master_mean_q_mm": direct_q,
            "direct_master_radius_mm": direct_radius,
            "qghost_projected_mean_q_mm": ghost_q,
            "qghost_projection_radius_mm": ghost_radius,
            "old_projection_interval_matches_qghost": legacy_pass,
            "direct_master_interval_contains_qghost": direct_pass,
            "direct_q_matches_qghost_guarded_intervals": direct_pass,
        })
    if legacy_fails != [0.2] or not all(direct_passes):
        raise AssertionError(f"Expected direct map to contain qghost at all states and legacy miss only at .2; got {legacy_fails}/{direct_passes}")
    exception_preflight = json.loads(validator.OLD_PREFLIGHT.read_text())
    producer = _load_module("pinned_k12_old_preflight_producer", validator.OLD_PREFLIGHT_PRODUCER)
    reproduced_preflight = producer.build()
    if reproduced_preflight != exception_preflight:
        raise AssertionError("Pinned 9,044-check original-DAT exception diagnosis did not reproduce")
    if (exception_preflight.get("carrier_checks") != 9044
            or exception_preflight.get("exception_count") != 1
            or exception_preflight.get("exceptions") != [{
                "time": 0.2, "source_row_id": "SPR489", "group": "SPR489",
                "error": "SPRINGA qghost displacement does not match its source projections: SPR489",
            }]):
        raise AssertionError("Original-DAT diagnostic no longer identifies the pinned sole SPR489@0.2 exception")
    audit_error = exception_preflight["exceptions"][0]["error"]
    coupon = json.loads(PARENT_COUPON.read_text())
    if (coupon.get("status") != "PASS_PARENT_REVIEWED_DIRECT_SCALAR_KNOWN_ANSWER_METHOD"
            or coupon.get("production_input_change_authorized_by_this_record") is not False
            or coupon.get("frame_forces_or_joint_accepted") is not False):
        raise AssertionError("Pinned prior coupon review does not support only the bounded method use")
    return {
        "scope": "diagnostic only on old selected-floor K12-rear output; not direct-master variant forces or a response audit",
        "original_model_sha256": validator.BASELINE_MODEL_SHA256,
        "original_deck_sha256": validator.BASELINE_DECK_SHA256,
        "original_dat_sha256": validator.OLD_DAT_SHA256,
        "original_case_context_sha256": validator.BASELINE_CONTEXT_SHA256,
        "replayed_existing_preflight_sha256": _sha(validator.OLD_PREFLIGHT),
        "original_all_carrier_preflight": {
            "checked_increments": exception_preflight["checked_increment_count"],
            "carrier_checks": exception_preflight["carrier_checks"],
            "exception_count": exception_preflight["exception_count"],
            "sole_exception": exception_preflight["exceptions"][0],
            "source_script_replayed_against_pinned_output": True,
        },
        "strict_711_original_DAT_diagnostic_rejection": audit_error,
        "direct_master_coordinate_gate_diagnostic": {
            "pre_variant_DAT_U_tokens_reused_only_to_compare_source_coordinate_intervals": True,
            "legacy_projection_fail_times": legacy_fails,
            "direct_master_map_contains_qghost_at_every_reported_increment": all(direct_passes),
            "increments": rows,
            "no_native_endpoint_RF_or_physical_force_reported": True,
            "no_variant_response_or_equilibrium_claim": True,
        },
        "known_answer_coupon": {
            "review_sha256": _sha(PARENT_COUPON),
            "native_coupon_dat_sha256": _sha(COUPON_DAT),
            "status": coupon["status"],
            "all_18_coupon_states_and_owner_wrenches_parent_reviewed": True,
            "coupon_not_used_as_frame_force_or_acceptance_evidence": True,
        },
    }


def run() -> dict[str, Any]:
    core = _load_module("current_k12_rear_spr489_direct_response_core", CORE_PATH)
    validator = core.load_direct_master_input_validator()
    validated = validator.validate_input_contract()
    record = json.loads(validator.VARIANT_MODEL.read_text())
    deck = validator.VARIANT_DECK.read_text()
    core_contract = validator.build_response_core_contract(
        validated, record, deck, model_path=validator.VARIANT_MODEL,
        deck_path=validator.VARIANT_DECK,
    )
    with tempfile.TemporaryDirectory(prefix="k12-spr489-pinned-copy-") as temp_name:
        copied_model = Path(temp_name) / "model.json"
        copied_deck = Path(temp_name) / "model.inp"
        os.link(validator.VARIANT_MODEL, copied_model)
        os.link(validator.VARIANT_DECK, copied_deck)
        copied_contract = validator.validate_input_contract(copied_model, copied_deck)
        copied_core_contract = validator.build_response_core_contract(
            copied_contract, record, deck, model_path=copied_model, deck_path=copied_deck,
        )
        byte_identical_copy_accepted = (
            copied_contract.variant_model_path == str(copied_model.resolve())
            and copied_contract.variant_deck_path == str(copied_deck.resolve())
            and copied_core_contract.get("direct_master_method_id") == validator.METHOD_ID
        )
        if not byte_identical_copy_accepted:
            raise AssertionError("Validator refused or misbound a byte-identical frozen-run input copy")
    if core_contract.get("direct_master_method_id") != validator.METHOD_ID:
        raise AssertionError("Sealed response core did not carry the SPR489-only method identity")
    if (len(core_contract["bindings"]) != 1292 or len(core_contract["springs"]) != 348
            or len(core_contract["physical_body_nodes"]) != 50
            or len(core_contract["floor_by_original"]) != 46
            or len(core_contract["inactive_output_nodes"]) != 154):
        raise AssertionError("Sealed core changed the existing carrier/body/floor contract")

    affine = _scalar_functional_fixture(core, validated.source_map)

    base_deck = validator.BASELINE_DECK.read_text()
    audit = json.loads(validator.INPUT_AUDIT.read_text())
    negative: list[dict[str, Any]] = []
    negative.append(_expect_reject(
        "non_target_equation_card_change",
        lambda: validator._check_deck_equations(
            base_deck, deck.replace("12550,1,1,", "12550,1,0.9,", 1), audit, core._stable,
        ),
        (validator.DirectMasterInputError,),
    ))
    tampered_audit = copy.deepcopy(audit)
    tampered_audit["source_map_provenance"]["scalar_coordinate_linear_functional"][0]["coefficient_in_equation"] += 1.0e-5
    negative.append(_expect_reject(
        "source_map_not_projected_from_direct_Qy_Qz_rows",
        lambda: validator._check_source_map(tampered_audit, record),
        (validator.DirectMasterInputError,),
    ))
    tampered_record = copy.deepcopy(record)
    tampered_record["springs"][0]["stiffness_n_per_mm"] *= 1.01
    negative.append(_expect_reject(
        "unapproved_retained_spring_change",
        lambda: validator._same_except_method_fields(
            json.loads(validator.BASELINE_MODEL.read_text()), tampered_record, audit,
        ),
        (validator.DirectMasterInputError,),
    ))
    negative.append(_expect_reject(
        "wrong_variant_input_bytes",
        lambda: validator.validate_input_contract(validator.BASELINE_MODEL, validator.BASELINE_DECK),
        (validator.DirectMasterInputError,),
    ))
    baseline_context = json.loads(validator.BASELINE_CONTEXT.read_text())
    negative.append(_expect_reject(
        "baseline_context_cannot_be_reused_for_variant_run",
        lambda: validator.validate_variant_run_context(
            validated, baseline_context, model_path=validator.VARIANT_MODEL,
            deck_path=validator.VARIANT_DECK,
        ),
        (validator.DirectMasterInputError,),
    ))

    class FakeBuilder:
        _seal = validator._CONTRACT_SEAL
        def build_response_core_contract(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            return {"bindings": [], "direct_master_method_id": validator.METHOD_ID}

    for label, fake in (("dictionary_contract", {}), ("duck_typed_same_builder", FakeBuilder())):
        negative.append(_expect_reject(
            label,
            lambda fake=fake: core.audit_record_with_direct_master_contract(
                record, "", deck, validated_contract=fake,
                model_path=validator.VARIANT_MODEL, deck_path=validator.VARIANT_DECK,
                case_context={},
            ),
            (core.ResponseAuditError,),
        ))
    negative.append(_expect_reject(
        "contract_attribute_mutation",
        lambda: setattr(validated, "variant_model_sha256", "0" * 64),
        (validator.DirectMasterInputError,),
    ))

    original_dat = _old_dat_coordinate_diagnostic(
        validator, core, validated.baseline_core, validated.source_map,
    )

    # A nested source-map mutation is detected before it reaches the physical core.
    validated.source_map["scalar_coordinate_linear_functional"][0]["coefficient_in_equation"] += 1.0e-7
    negative.append(_expect_reject(
        "post_validation_nested_source_map_mutation",
        lambda: validator.build_response_core_contract(
            validated, record, deck, model_path=validator.VARIANT_MODEL,
            deck_path=validator.VARIANT_DECK,
        ),
        (validator.DirectMasterInputError,),
    ))
    return {
        "schema": "current_k12_rear_spr489_direct_master_method_preflight/v1",
        "status": "PASS_INPUT_CONTRACT_AND_READ_ONLY_METHOD_DIAGNOSTICS_ONLY",
        "native_solve_executed_by_this_packet": False,
        "freeze_created_by_this_packet": False,
        "frame_ready_for_native_run": False,
        "force_adoption": False,
        "mechanical_acceptance": False,
        "input_contract": validated.proof_summary,
        "response_core_contract": {
            "status": "PASS_SEALED_EXACT_TYPE_CONTRACT",
            "direct_master_source_row_id": "SPR489",
            "only_changed_q_mpc_dependent_dofs": [[19800, 2], [19800, 3]],
            "unilateral_springa_bindings": len(core_contract["bindings"]),
            "retained_spring2_components": len(core_contract["springs"]),
            "physical_body_count": len(core_contract["physical_body_nodes"]),
            "selected_floor_references": len(core_contract["floor_by_original"]),
            "inactive_floor_output_only_rows": len(core_contract["inactive_output_nodes"]),
            "source_map_sha256": validated.source_map_sha256,
            "all_other_recovery_methods": "pinned 711 zero-U-token response core",
            "legacy_linear_auditor_accepted": False,
            "arbitrary_dict_or_duck_typed_contract_accepted": False,
            "contract_revalidates_baseline_711_context_and_source_map_hash_on_use": True,
            "byte_identical_parent_frozen_run_copy_accepted": byte_identical_copy_accepted,
        },
        "direct_scalar_map_fixture": affine,
        "old_dat_diagnostic": original_dat,
        "negative_contract_and_input_probes": negative,
        "negative_probe_count": len(negative),
        "all_negative_probes_rejected": all(row["rejected"] for row in negative),
        "limits": [
            "The pre-variant DAT coordinate overlay is diagnostic only and does not contain direct-master variant forces.",
            "A parent-created post-freeze context and exact variant execution record are required before the response-core CLI can audit any variant output.",
            "This contract is specific to the pinned K12-rear SPR489 method and is not reusable for another source row or case.",
        ],
    }


if __name__ == "__main__":
    result = run()
    out = HERE / "method-and-diagnostic-check.json"
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(result["status"])
