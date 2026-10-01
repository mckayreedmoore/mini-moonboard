"""Exact input contract for the one K12-rear SPR489 direct-master variant.

This validator is input-only. It validates the unchanged selected-floor
baseline through the pinned 711 wrapper/context, proves the two-equation
variant against that baseline, and issues one sealed response-core contract.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent

BASELINE_PACKET = SERIES / "current-springa-selected-floor-k12-rear-attempt03"
BASELINE_MODEL = BASELINE_PACKET / "model.json"
BASELINE_DECK = BASELINE_PACKET / "model.inp"
BASELINE_CONTEXT = BASELINE_PACKET / "case-context.json"
VARIANT_PACKET = SERIES / "current-springa-k12-rear-spr489-direct-master-input-attempt02"
VARIANT_MODEL = VARIANT_PACKET / "model.json"
VARIANT_DECK = VARIANT_PACKET / "model.inp"
INPUT_AUDIT = VARIANT_PACKET / "input-audit.json"
SOURCE_PINS = VARIANT_PACKET / "source-pins.json"
PREPARER = VARIANT_PACKET / "prepare.py"
RESPONSE_CORE_PATH = HERE / "response_core.py"
RESPONSE_CORE_SHA256 = "87e8624661fb30fd8d0ec23fee51ad421045bafaade0736f05439a26578ea1d8"

BASELINE_MODEL_SHA256 = "9591669b74af719e72df2a681504cab4e283d693eaac5e42920558b30773168f"
BASELINE_DECK_SHA256 = "6b630749e918189583147833e3ef94a1338dc5bb28f42171cefc05cb039695e9"
BASELINE_CONTEXT_SHA256 = "1a352178c8fe2ad64681d2f456d9fdf29e67b72d0a1cbce3aa3ed5df21259a93"
VARIANT_MODEL_SHA256 = "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd"
VARIANT_DECK_SHA256 = "6c6f8dc02616d3b92dda2f15db1a196e47935233e47eee0afaa56fda694fd3aa"
INPUT_AUDIT_SHA256 = "c593c94d206c6798b190d3b42b4956aaa898a503dfe11a1303b20a126266d8cf"
SOURCE_PINS_SHA256 = "470a89b3d354790216e095e2f0a57e3348c9660c091898f4c9bf621e980a0b96"
PREPARER_SHA256 = "d99b0fb3322c3799f5390c343c1e0bba53ae01b34a265122b778b41051f1896d"
RESPONSE_711 = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
RESPONSE_711_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
RECOVERY_711 = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
RECOVERY_711_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
DIRECT_COUPON_REVIEW = SERIES / "current-k12-rear-direct-scalar-native-attempt01/parent-method-validation.json"
DIRECT_COUPON_REVIEW_SHA256 = "7c170e58b82fe16d733e6d0bb3a57edb71b3a97d2cfefe0f5c6c601f6ddcbeb8"
DIRECT_COUPON_DAT = SERIES / "current-k12-rear-direct-scalar-native-attempt01/model.dat"
DIRECT_COUPON_DAT_SHA256 = "f70cb84fcd59c1d7edbc370ace803ebd8757e7bd6166670af1e0fd4439cb8aed"
OLD_DAT = BASELINE_PACKET / "model.dat"
OLD_EXECUTION = BASELINE_PACKET / "execution.json"
OLD_FREEZE = BASELINE_PACKET / "freeze.json"
OLD_DAT_SHA256 = "29ec3cca415ee8f1ddb6cccd07a70aade816fd4c71eca98a5944d441f6d42f7a"
OLD_EXECUTION_SHA256 = "805e2b43da0f612de7801eca6fa4e05c834e90d805ceb12c23a3cf03c72dae71"
OLD_FREEZE_SHA256 = "f1d9245626d18007e68732fb79f1a0630adc292397d0ba2fd7c2ca17c48b1cfd"
OLD_PREFLIGHT = SERIES / "current-k12-rear-all-carrier-exception-preflight-attempt01/diagnosis.json"
OLD_PREFLIGHT_SHA256 = "49a421ffe939473e6982a033e2e2b64d194c0ab6c39180e25264ba9bb0d743ab"
OLD_PREFLIGHT_PRODUCER = SERIES / "current-k12-rear-all-carrier-exception-preflight-attempt01/produce.py"
OLD_PREFLIGHT_PRODUCER_SHA256 = "5c89915e934ace0033ca76f26a8b7dc4c7ea022e286ec89ead3a561df9466369"

SOURCE_INDEX = 488
SOURCE_ROW_ID = "SPR489"
EQUATION_INDICES = (19433, 19434)
DEPENDENT_DOFS = ((19800, 2), (19800, 3))
METHOD_ID = "spr489_direct_c3d20_master_interpolation/v1"
METHOD_METADATA = {
    "schema": "current_springa_direct_master_qghost_method_variant/v1",
    "variant_id": METHOD_ID,
    "source_row_id": SOURCE_ROW_ID,
    "source_inventory_row_index": SOURCE_INDEX,
    "affected_equation_indices_zero_based": [19433, 19434],
    "affected_equation_dependent_dofs": [[19800, 2], [19800, 3]],
    "all_other_equations_preserved": True,
    "source_projection_inventory_preserved": True,
    "source_projection_inventory_preserved": True,
    "carrier_geometry_axis_spring_and_table_preserved": True,
    "automatic_mask_iteration_authorized": False,
    "frame_ready_for_native_run": False,
    "force_adoption": False,
    "mechanical_acceptance": False,
    "scope": "one explicit SPR489 qghost replacement in K12-rear; no other source row or solver method changed",
}
RELATIVE_EVALUATION = (
    "direct C3D20 master interpolation; source projection nodes are retained "
    "as provenance but are not used to recover SPR489 q"
)


class DirectMasterInputError(ValueError):
    """The serialized K12-rear direct-master input is not the pinned variant."""


_CONTRACT_SEAL = object()


class ValidatedDirectMasterContract:
    """Exact-type token created only after this module validates pinned inputs."""

    __slots__ = (
        "_seal", "validator_sha256", "baseline_context_sha256", "baseline_core",
        "variant_model_path", "variant_deck_path", "variant_model_sha256",
        "variant_deck_sha256", "source_map", "source_map_sha256", "input_audit_sha256",
        "proof_summary", "_locked",
    )

    def __init__(self, *, seal: object, validator_sha256: str,
                 baseline_context_sha256: str, baseline_core: dict[str, Any],
                 variant_model_path: str, variant_deck_path: str,
                 variant_model_sha256: str, variant_deck_sha256: str,
                 source_map: dict[str, Any], source_map_sha256: str,
                 input_audit_sha256: str, proof_summary: dict[str, Any]):
        if seal is not _CONTRACT_SEAL:
            raise DirectMasterInputError("Direct-master contracts can only be issued by the pinned validator")
        object.__setattr__(self, "_seal", seal)
        object.__setattr__(self, "validator_sha256", validator_sha256)
        object.__setattr__(self, "baseline_context_sha256", baseline_context_sha256)
        object.__setattr__(self, "baseline_core", copy.deepcopy(baseline_core))
        object.__setattr__(self, "variant_model_path", variant_model_path)
        object.__setattr__(self, "variant_deck_path", variant_deck_path)
        object.__setattr__(self, "variant_model_sha256", variant_model_sha256)
        object.__setattr__(self, "variant_deck_sha256", variant_deck_sha256)
        object.__setattr__(self, "source_map", copy.deepcopy(source_map))
        object.__setattr__(self, "source_map_sha256", source_map_sha256)
        object.__setattr__(self, "input_audit_sha256", input_audit_sha256)
        object.__setattr__(self, "proof_summary", copy.deepcopy(proof_summary))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_locked", False):
            raise DirectMasterInputError("Validated direct-master contract attributes are immutable")
        object.__setattr__(self, name, value)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise DirectMasterInputError(f"Missing pinned {label}: {path}")
    actual = _sha(path)
    if actual != expected:
        raise DirectMasterInputError(f"Pinned {label} changed: {actual} != {expected}")


def _load_711():
    _require_hash(RESPONSE_711, RESPONSE_711_SHA256, "711 response wrapper")
    _require_hash(RECOVERY_711, RECOVERY_711_SHA256, "711 recovery source")
    name = "pinned_k12_spr489_original_711_response"
    loaded = sys.modules.get(name)
    if loaded is not None:
        if Path(getattr(loaded, "__file__", "")).resolve() != RESPONSE_711.resolve():
            raise DirectMasterInputError("Canonical 711 module identity is already bound to another path")
        return loaded
    spec = importlib.util.spec_from_file_location(name, RESPONSE_711)
    if spec is None or spec.loader is None:
        raise DirectMasterInputError("Cannot load the original pinned 711 response validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _expected_qghost(base_binding: dict[str, Any], audit_map: dict[str, Any]) -> list[dict[str, Any]]:
    prior = copy.deepcopy(base_binding["qghost_equations"])
    if len(prior) != 3:
        raise DirectMasterInputError("Baseline SPR489 qghost must have exactly three components")
    equations = audit_map.get("carrier_component_equations", {})
    if set(equations) != {"Qy", "Qz", "meaning"} or equations.get("meaning") != (
        "Q_y=n_y*q and Q_z=n_z*q; the SPRINGA axis and initial 100 mm span are unchanged"
    ):
        raise DirectMasterInputError("Input audit direct-master map must serialize exactly Qy and Qz")
    prior[1] = {"dependent_q_dof": [19800, 2], "terms": copy.deepcopy(equations["Qy"])}
    prior[2] = {"dependent_q_dof": [19800, 3], "terms": copy.deepcopy(equations["Qz"])}
    return prior


def _variant_binding(base: dict[str, Any], audit_map: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    out["q_endpoint_components_use_projection_ghosts_before_method_variant"] = True
    out["q_endpoint_components_use_projection_ghosts"] = False
    out["relative_coordinate_output_evaluation"] = RELATIVE_EVALUATION
    out["direct_master_source_coordinate"] = copy.deepcopy(audit_map)
    out["qghost_equations_before_direct_master_variant"] = copy.deepcopy(base["qghost_equations"])
    out["qghost_equations_method_variant"] = METHOD_ID
    out["qghost_equations"] = _expected_qghost(base, audit_map)
    return out


def _same_except_method_fields(baseline: dict[str, Any], variant: dict[str, Any], audit: dict[str, Any]) -> None:
    expected = copy.deepcopy(baseline)
    expected["input_method_variant"] = copy.deepcopy(METHOD_METADATA)
    expected["input_method_variant"]["direct_master_source_coordinate"] = copy.deepcopy(audit["source_map_provenance"])
    expected["nonlinear_native_carrier_bindings"][SOURCE_INDEX] = _variant_binding(
        baseline["nonlinear_native_carrier_bindings"][SOURCE_INDEX], audit["source_map_provenance"])
    expected["unilateral_springa_bindings"][SOURCE_INDEX] = _variant_binding(
        baseline["unilateral_springa_bindings"][SOURCE_INDEX], audit["source_map_provenance"])
    # Attempt02 preserves original high-precision equation records everywhere
    # except the two SPR489 rows. Build those two expected records from the
    # pinned map, leaving every other serialized equation exactly baseline.
    components = audit["source_map_provenance"]["carrier_component_equations"]
    expected["equations"][EQUATION_INDICES[0]] = copy.deepcopy(components["Qy"])
    expected["equations"][EQUATION_INDICES[1]] = copy.deepcopy(components["Qz"])
    if expected != variant:
        changed = sorted(key for key in set(expected) | set(variant) if expected.get(key) != variant.get(key))
        raise DirectMasterInputError("Variant model has unapproved model-field changes: " + ", ".join(changed[:20]))


def _check_deck_equations(baseline_deck: str, variant_deck: str,
                          audit: dict[str, Any], stable: Any) -> dict[str, Any]:
    before = stable._parse_equation_cards(baseline_deck)
    after = stable._parse_equation_cards(variant_deck)
    if len(before) != 21844 or len(after) != 21844:
        raise DirectMasterInputError("K12-rear baseline/variant equation count changed")
    changed = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    if changed != list(EQUATION_INDICES):
        raise DirectMasterInputError(f"Only equation rows {EQUATION_INDICES} may change; observed {changed[:20]}")
    components = audit["source_map_provenance"]["carrier_component_equations"]
    for i, key, dof in zip(EQUATION_INDICES, ("Qy", "Qz"), (2, 3), strict=True):
        expected = components[key]
        actual = after[i]
        if len(actual) != len(expected) or any(
            int(a[0]) != int(e[0]) or int(a[1]) != int(e[1])
            or abs(float(a[2]) - float(e[2])) > max(1.0e-12, abs(float(e[2])) * 1.0e-13)
            for a, e in zip(actual, expected, strict=True)
        ):
            raise DirectMasterInputError(f"Equation {i} does not match the audited SPR489 {key} direct map")
        if tuple(map(int, actual[0][:2])) != (19800, dof):
            raise DirectMasterInputError(f"Equation {i} dependent DOF is not SPR489 qnode DOF {dof}")
    return {
        "baseline_equation_count": len(before),
        "variant_equation_count": len(after),
        "changed_equation_indices": changed,
        "changed_dependent_dofs": [[19800, 2], [19800, 3]],
        "all_other_equation_rows_exactly_unchanged": True,
        "changed_rows_match_input_audit_direct_master_map": True,
    }


def _check_source_map(audit: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    provenance = audit.get("source_map_provenance")
    if not isinstance(provenance, dict):
        raise DirectMasterInputError("Pinned input audit has no serialized source map")
    if provenance.get("source_map_recovery_rule") != (
        "q_source = -sum(c_i*U_i) from scalar_coordinate_linear_functional; radius = sum(abs(c_i)*U_radius_i)"
    ):
        raise DirectMasterInputError("Source scalar/radius recovery rule changed")
    terms = provenance.get("scalar_coordinate_linear_functional")
    if not isinstance(terms, list) or len(terms) != 80:
        raise DirectMasterInputError("SPR489 direct scalar map must contain 80 serialized master DOF terms")
    keys = [(int(row["node"]), int(row["dof"])) for row in terms]
    if len(set(keys)) != 80 or any(dof not in (2, 3) for _, dof in keys):
        raise DirectMasterInputError("SPR489 source scalar map has duplicate or non-lateral master DOFs")
    side_nodes = {
        int(row["node"])
        for side in provenance["source_interpolation_sides"].values()
        for row in side["master_shape_weights"]
    }
    if set(node for node, _ in keys) != side_nodes:
        raise DirectMasterInputError("Scalar recovery terms differ from the audited 40+40 master-node inventory")
    owner_axis = list(map(float, provenance["physical_owner_axis_global_xyz"]))
    component_rows = provenance["carrier_component_equations"]
    row_maps = {}
    for label, dof in (("Qy", 2), ("Qz", 3)):
        row = component_rows[label]
        if len(row) != 81 or tuple(map(int, row[0][:2])) != (19800, dof) or float(row[0][2]) != 1.0:
            raise DirectMasterInputError(f"Audited {label} direct equation has wrong dependent DOF/term count")
        row_maps[label] = {(int(n), int(d)): float(c) for n, d, c in row[1:]}
        if len(row_maps[label]) != 80 or any(d not in (2, 3) for _, d in row_maps[label]):
            raise DirectMasterInputError(f"Audited {label} row is not an 80-master lateral scalar equation")
    scalar = {(int(row["node"]), int(row["dof"])): float(row["coefficient_in_equation"]) for row in terms}
    if set(scalar) != set(row_maps["Qy"]) or set(scalar) != set(row_maps["Qz"]):
        raise DirectMasterInputError("Direct scalar functional DOF support differs from Qy/Qz component rows")
    max_projection_error = max(
        abs(scalar[key] - (owner_axis[1] * row_maps["Qy"][key] + owner_axis[2] * row_maps["Qz"][key]))
        for key in scalar
    )
    if max_projection_error > 1.0e-12:
        raise DirectMasterInputError("Serialized scalar map is not the owner-axis projection of Qy/Qz rows")
    for field in ("unilateral_springa_bindings", "nonlinear_native_carrier_bindings"):
        binding = variant[field][SOURCE_INDEX]
        if binding.get("group") != SOURCE_ROW_ID or binding.get("direct_master_source_coordinate") != provenance:
            raise DirectMasterInputError(f"{field} SPR489 direct source map differs from pinned input audit")
    if audit.get("direct_scalar_map_matches_validated_known_answer_coupon_max_abs") != 0.0:
        raise DirectMasterInputError("Pinned direct source map no longer matches the validated scalar coupon")
    wrench = audit.get("unit_owner_wrench_from_emitted_component_rows", {})
    if wrench.get("interpretation") != "unit SPRINGA scalar force; virtual-work transfer from the two direct carrier rows":
        raise DirectMasterInputError("Direct component-row owner-action interpretation changed")
    force_wrench_error = max(
        abs(float(value))
        for vector in wrench.get("force_residual_xyz_by_owner_N_per_N", {}).values()
        for value in vector
    )
    moment_wrench_error = max(
        abs(float(value))
        for vector in wrench.get("moment_residual_xyz_by_owner_Nmm_per_N", {}).values()
        for value in vector
    )
    if force_wrench_error > 1.0e-9 or moment_wrench_error > 1.0e-8:
        raise DirectMasterInputError("Direct component rows do not preserve the original owner unit wrench")
    return {
        "scalar_term_count": len(terms),
        "component_qy_qz_term_counts": [len(component_rows["Qy"]), len(component_rows["Qz"])],
        "owner_axis_projection_max_abs_coefficient_error": max_projection_error,
        "source_q_formula": provenance["source_q_formula"],
        "source_q_radius_formula": "sum(abs(c_i) * U_radius_i) over the same 80 audit-pinned physical master DOFs",
        "direct_map_coupon_error_max_abs": 0.0,
        "emitted_component_row_owner_unit_force_wrench_error_N_per_N": force_wrench_error,
        "emitted_component_row_owner_unit_moment_wrench_error_Nmm_per_N": moment_wrench_error,
        "unit_owner_force_and_first_moment_transfer_passed": True,
        "historical_projection_ghost_U_used_for_SPR489": False,
    }


def validate_input_contract(model_path: Path = VARIANT_MODEL,
                             deck_path: Path = VARIANT_DECK) -> ValidatedDirectMasterContract:
    """Validate the exact input pair and return a sealed contract for the fork."""
    for path, expected, label in (
        (RESPONSE_CORE_PATH, RESPONSE_CORE_SHA256, "direct-master response-core fork"),
        (BASELINE_MODEL, BASELINE_MODEL_SHA256, "K12-rear selected-floor baseline model"),
        (BASELINE_DECK, BASELINE_DECK_SHA256, "K12-rear selected-floor baseline deck"),
        (BASELINE_CONTEXT, BASELINE_CONTEXT_SHA256, "K12-rear baseline case context"),
        (VARIANT_MODEL, VARIANT_MODEL_SHA256, "SPR489 direct-master model"),
        (VARIANT_DECK, VARIANT_DECK_SHA256, "SPR489 direct-master deck"),
        (INPUT_AUDIT, INPUT_AUDIT_SHA256, "SPR489 direct-master input audit"),
        (SOURCE_PINS, SOURCE_PINS_SHA256, "SPR489 direct-master source pins"),
        (PREPARER, PREPARER_SHA256, "SPR489 direct-master preparer"),
        (DIRECT_COUPON_REVIEW, DIRECT_COUPON_REVIEW_SHA256, "reviewed direct-scalar known-answer coupon"),
        (DIRECT_COUPON_DAT, DIRECT_COUPON_DAT_SHA256, "direct-scalar coupon DAT"),
        (OLD_DAT, OLD_DAT_SHA256, "pre-variant K12-rear DAT"),
        (OLD_EXECUTION, OLD_EXECUTION_SHA256, "pre-variant K12-rear execution record"),
        (OLD_FREEZE, OLD_FREEZE_SHA256, "pre-variant K12-rear freeze"),
        (OLD_PREFLIGHT, OLD_PREFLIGHT_SHA256, "pre-variant 9,044-check diagnostic"),
        (OLD_PREFLIGHT_PRODUCER, OLD_PREFLIGHT_PRODUCER_SHA256, "pre-variant diagnostic replay script"),
    ):
        _require_hash(path, expected, label)
    model_path, deck_path = model_path.resolve(), deck_path.resolve()
    if (not model_path.is_file() or not deck_path.is_file()
            or _sha(model_path) != VARIANT_MODEL_SHA256
            or _sha(deck_path) != VARIANT_DECK_SHA256):
        raise DirectMasterInputError("Only byte-identical copies of the pinned SPR489 direct-master model/deck are accepted")
    baseline = json.loads(BASELINE_MODEL.read_text())
    variant = json.loads(VARIANT_MODEL.read_text())
    baseline_deck = BASELINE_DECK.read_text()
    variant_deck = VARIANT_DECK.read_text()
    audit = json.loads(INPUT_AUDIT.read_text())
    pins = json.loads(SOURCE_PINS.read_text())
    context = json.loads(BASELINE_CONTEXT.read_text())
    if pins.get("schema") != "current_spr489_direct_master_frame_input_source_pins/v1":
        raise DirectMasterInputError("Direct-master source-pin schema changed")
    if audit.get("schema") != "current_spr489_direct_master_frame_input_audit/v1" or audit.get("status") != "PASS_EXACT_SPR489_DIRECT_MASTER_INPUT_ARITHMETIC_ONLY":
        raise DirectMasterInputError("Direct-master input arithmetic audit is not the pinned passing input-only source")
    if audit.get("readiness_flags") != {
        "force_adoption": False, "frame_ready_for_native_run": False,
        "mechanical_acceptance": False, "native_solve_executed": False,
    }:
        raise DirectMasterInputError("Direct-master source audit claims readiness, solve, or force adoption")
    source_pin = pins.get("exact_replacement", {})
    if (source_pin.get("source_model_sha256") != BASELINE_MODEL_SHA256
            or source_pin.get("source_deck_sha256") != BASELINE_DECK_SHA256
            or source_pin.get("emitted_model_sha256") != VARIANT_MODEL_SHA256
            or source_pin.get("emitted_deck_sha256") != VARIANT_DECK_SHA256
            or source_pin.get("source_row_id") != SOURCE_ROW_ID
            or source_pin.get("source_inventory_row_index") != SOURCE_INDEX
            or source_pin.get("dependent_dofs") != [[19800, 2], [19800, 3]]):
        raise DirectMasterInputError("Source pins do not bind this exact SPR489 equation replacement")

    # This is the original strict 711 validator path on the unchanged baseline,
    # with its original K12-rear case context and source-load register pins.
    response_711 = _load_711()
    baseline_contract = response_711._validate_model(baseline, baseline_deck, context)
    if baseline_contract.get("case_id") != "k12-rear" or baseline_contract.get("selected_cell_count") != 23:
        raise DirectMasterInputError("Original 711 context validation did not resolve the K12-rear 23-cell baseline")

    if audit.get("all_1292_unilateral_laws_stiffnesses_owner_records_and_100mm_carrier_geometries_preserved_except_SPR489_qghost_method_mapping") is not True:
        raise DirectMasterInputError("Pinned audit does not assert the exact SPR489-only carrier method scope")
    if audit.get("floor_selected_23_inactive_77_preserved") is not True or audit.get("floor_tangent_rows_46_active_154_inert_preserved") is not True:
        raise DirectMasterInputError("Pinned audit does not preserve the K12-rear floor branch/input map")
    audit_map = audit["source_map_provenance"]
    _same_except_method_fields(baseline, variant, audit)
    deck_equations = _check_deck_equations(baseline_deck, variant_deck, audit, response_711._stable)
    source_map_check = _check_source_map(audit, variant)

    # The variant's serialized row array must agree with its parsed emitted
    # equation cards at the same strict decimal tolerance used by 711.
    parsed_variant = response_711._stable._parse_equation_cards(variant_deck)
    if len(parsed_variant) != len(variant["equations"]):
        raise DirectMasterInputError("Variant model/deck equation count mismatch")
    for index, (parsed, declared) in enumerate(zip(parsed_variant, variant["equations"], strict=True)):
        if len(parsed) != len(declared) or any(
            int(a[0]) != int(b[0]) or int(a[1]) != int(b[1])
            or abs(float(a[2]) - float(b[2])) > max(1.0e-12, abs(float(b[2])) * 1.0e-13)
            for a, b in zip(parsed, declared, strict=True)
        ):
            raise DirectMasterInputError(f"Variant model equation row {index} differs from its emitted deck")

    proof_summary = {
        "status": "PASS_EXACT_K12_REAR_SPR489_DIRECT_MASTER_INPUT_CONTRACT",
        "baseline_711_validation": {
            "response_wrapper_sha256": RESPONSE_711_SHA256,
            "baseline_model_sha256": BASELINE_MODEL_SHA256,
            "baseline_deck_sha256": BASELINE_DECK_SHA256,
            "baseline_case_context_sha256": BASELINE_CONTEXT_SHA256,
            "case_id": baseline_contract["case_id"],
            "selected_bearing_cells": baseline_contract["selected_cell_count"],
            "inactive_bearing_cells": baseline_contract["inactive_cell_count"],
            "physical_body_count": len(baseline_contract["physical_body_nodes"]),
            "unilateral_binding_count": len(baseline_contract["bindings"]),
            "retained_spring2_count": len(baseline_contract["springs"]),
            "strict_711_model_and_context_validator_called_on_unchanged_baseline": True,
        },
        "direct_variant": {
            "model_sha256": VARIANT_MODEL_SHA256,
            "deck_sha256": VARIANT_DECK_SHA256,
            "input_audit_sha256": INPUT_AUDIT_SHA256,
            "source_row_id": SOURCE_ROW_ID,
            "model_json_diff_whitelist": {
                "changed_equation_indices_zero_based": list(EQUATION_INDICES),
                "all_other_model_json_equation_records_exactly_unchanged": True,
                "only_non_equation_changes": [
                    "/input_method_variant",
                    "/nonlinear_native_carrier_bindings/488/declared_method_metadata_and_qghost_map",
                    "/unilateral_springa_bindings/488/declared_method_metadata_and_qghost_map",
                ],
                "unapproved_json_paths_rejected": True,
            },
            "source_laws_stiffness_owners_geometry_loads_and_floor_map_preserved": True,
            "deck_equation_diff": deck_equations,
            "direct_source_map": source_map_check,
            "parent_known_answer_coupon_method_status": "PASS_PARENT_REVIEWED_DIRECT_SCALAR_KNOWN_ANSWER_METHOD",
            "no_native_solve_or_force_adoption_in_input_contract": True,
        },
    }
    return ValidatedDirectMasterContract(
        seal=_CONTRACT_SEAL,
        validator_sha256=_sha(Path(__file__)),
        baseline_context_sha256=BASELINE_CONTEXT_SHA256,
        baseline_core=baseline_contract,
        variant_model_path=str(model_path),
        variant_deck_path=str(deck_path),
        variant_model_sha256=VARIANT_MODEL_SHA256,
        variant_deck_sha256=VARIANT_DECK_SHA256,
        source_map=audit_map,
        source_map_sha256=_canonical_sha(audit_map),
        input_audit_sha256=INPUT_AUDIT_SHA256,
        proof_summary=proof_summary,
    )


def build_response_core_contract(validated: ValidatedDirectMasterContract,
                                 record: dict[str, Any], deck: str,
                                 *, model_path: Path, deck_path: Path) -> dict[str, Any]:
    """Re-authenticate the sealed variant and adapt only its force-recovery input."""
    if type(validated) is not ValidatedDirectMasterContract or validated._seal is not _CONTRACT_SEAL:
        raise DirectMasterInputError("A validator-issued exact-type direct-master contract is required")
    if _sha(Path(__file__)) != validated.validator_sha256:
        raise DirectMasterInputError("Direct-master validator source changed after contract creation")
    if model_path.resolve() != Path(validated.variant_model_path) or deck_path.resolve() != Path(validated.variant_deck_path):
        raise DirectMasterInputError("Response-core paths differ from the sealed direct-master variant")
    if _sha(model_path) != validated.variant_model_sha256 or _sha(deck_path) != validated.variant_deck_sha256:
        raise DirectMasterInputError("Response-core model/deck hashes differ from the sealed direct-master variant")
    if _canonical_sha(validated.source_map) != validated.source_map_sha256:
        raise DirectMasterInputError("Sealed direct-master source map was mutated after validation")
    if deck != deck_path.read_text() or record != json.loads(model_path.read_text()):
        raise DirectMasterInputError("Response-core in-memory data differs from the sealed variant files")
    _require_hash(BASELINE_MODEL, BASELINE_MODEL_SHA256, "K12-rear selected-floor baseline model")
    _require_hash(BASELINE_DECK, BASELINE_DECK_SHA256, "K12-rear selected-floor baseline deck")
    _require_hash(BASELINE_CONTEXT, BASELINE_CONTEXT_SHA256, "K12-rear baseline case context")
    response_711 = _load_711()
    contract = response_711._validate_model(
        json.loads(BASELINE_MODEL.read_text()), BASELINE_DECK.read_text(),
        json.loads(BASELINE_CONTEXT.read_text()),
    )
    contract["bindings"] = copy.deepcopy(record["unilateral_springa_bindings"])
    contract["springs"] = copy.deepcopy(record["springs"])
    contract["direct_master_source_coordinate"] = copy.deepcopy(validated.source_map)
    contract["direct_master_source_map_sha256"] = validated.source_map_sha256
    contract["direct_master_input_audit_sha256"] = validated.input_audit_sha256
    contract["direct_master_method_id"] = METHOD_ID
    contract["direct_master_contract_mode"] = "one_exact_k12_rear_spr489_input_variant"
    return contract


def validate_variant_run_context(validated: ValidatedDirectMasterContract,
                                 context: dict[str, Any], *, model_path: Path,
                                 deck_path: Path) -> dict[str, Any]:
    """Check a parent-created post-freeze context without synthesizing one."""
    if type(validated) is not ValidatedDirectMasterContract or validated._seal is not _CONTRACT_SEAL:
        raise DirectMasterInputError("A validator-issued direct-master contract is required")
    if context.get("schema") != "current_springa_case_bound_input_context/v1":
        raise DirectMasterInputError("Post-freeze run context schema is unsupported")
    baseline_context = json.loads(BASELINE_CONTEXT.read_text())
    mutable = {"selected_input_model_json_path", "selected_input_model_json_sha256",
               "selected_input_deck_path", "selected_input_deck_sha256"}
    if set(context) != set(baseline_context):
        raise DirectMasterInputError("Post-freeze run context fields differ from the source K12-rear context")
    if any(context.get(key) != baseline_context.get(key) for key in set(context) - mutable):
        raise DirectMasterInputError("Post-freeze run context changes baseline case, source, branch, or load authority")
    if (_resolve(str(context["selected_input_model_json_path"])) != model_path.resolve()
            or _resolve(str(context["selected_input_deck_path"])) != deck_path.resolve()
            or context["selected_input_model_json_sha256"] != validated.variant_model_sha256
            or context["selected_input_deck_sha256"] != validated.variant_deck_sha256):
        raise DirectMasterInputError("Post-freeze context does not bind the exact direct-master model/deck")
    return {
        "schema": context["schema"], "case_id": context["case_id"],
        "baseline_context_sha256": validated.baseline_context_sha256,
        "run_context_canonical_sha256": _canonical_sha(context),
        "variant_model_sha256": validated.variant_model_sha256,
        "variant_deck_sha256": validated.variant_deck_sha256,
        "all_non_input_authority_fields_equal_baseline": True,
        "parent_created_context_consumed_without_synthesis": True,
    }
