#!/usr/bin/env python3
"""Register current six-case source loads from fresh reduced-case metadata only."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "register.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.wood_joint_reduced_case import build_case
from scripts.wood_joint_current_load_cases import CASE_INPUTS


BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
MODEL_INPUTS = BASE / "reduced-static-attempt01/model-inputs.json"
CURRENT_LOAD_CONTRACT = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json")
ADAPTER_DIR = BASE / "current-springa-frame-input-adapter-attempt01"
ADAPTER_PREPARE = ADAPTER_DIR / "prepare.py"
ADAPTER_PINS = ADAPTER_DIR / "source-pins.json"
A12_MODEL = ADAPTER_DIR / "a12-rear/model.json"
A12_DECK = ADAPTER_DIR / "a12-rear/model.inp"
A12_AUDIT = ADAPTER_DIR / "a12-rear/audit.json"
CONDITIONAL_A12_RESPONSE_DIR = BASE / "current-springa-selected-floor-a12-rear-attempt03"
CONDITIONAL_A12_TERMINAL = CONDITIONAL_A12_RESPONSE_DIR / "parent-terminal-assessment.json"
CONDITIONAL_A12_RESPONSE = CONDITIONAL_A12_RESPONSE_DIR / "response.json"
CONDITIONAL_A12_FREEZE = CONDITIONAL_A12_RESPONSE_DIR / "freeze.json"
CONDITIONAL_A12_EXECUTION = CONDITIONAL_A12_RESPONSE_DIR / "execution.json"
CONDITIONAL_A12_BODY_AUDIT = CONDITIONAL_A12_RESPONSE_DIR / "parent-all-body-response-audit.json"
CONDITIONAL_A12_MODEL = CONDITIONAL_A12_RESPONSE_DIR / "model.json"
CONDITIONAL_A12_DECK = CONDITIONAL_A12_RESPONSE_DIR / "model.inp"
CURRENT_ADAPTER_DIR = BASE / "current-springa-active-floor-input-adapter-attempt03"

CASE_IDS = [case_id for case_id, _hold, _xy in CASE_INPUTS]
BUILD_KWARGS = {
    "accessory_scenario_id": None,
    "mesh_size_mm": 150.0,
    "ring_case": "A",
    "panel_group_factor": 1.0,
    "hillman_axial_ratio": 1.0,
    "bolt_gap_factor": 0.0,
    "contact_penalty_n_per_mm3": 100.0,
}

# Immutable source snapshot for this register. Adapter source-pins.json is also
# checked recursively so the SPRINGA and exact-floor method fixtures stay bound.
PINNED_SHA256 = {
    "scripts/wood_joint_current_load_cases.py": "46f67d66c9490d3a435c0f1098ed42ce0f95dee7de81d4c62bd8835ed607b534",
    "fea/wood_joint_reduced_case.py": "9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192",
    "fea/wood_joint_reduced_loads.py": "d8e2da5ad196878c8d10dc27920e0723bbc9b89b824624521a55bcee7caebbf3",
    "fea/wood_joint_reduced_gravity.py": "e41c09282d59fa41d452ec88031fc59213863fd6edf65b1335dc8de92b7d3c45",
    "fea/wood_joint_reduced_body_loads.py": "64b7b2ccec107a95f23d749abace7d89346d0a57191ad3746273c496c27ab1f0",
    "fea/wood_joint_reduced_geometry.py": "7483dd6bac169ade5c731af2b22e8d40d8132cd0881ddfda2642ef5430208200",
    "fea/wood_joint_reduced_model.py": "f94b1161b984b7599f6c8d4a131ad49a3f12a0033ec6a0b6b5892a5b9d45e2f7",
    "fea/wood_joint_reduced_panels.py": "50b94669a5f112a75357529af01ca56ff6acd8887f1245f4368b58e6ee4ec388",
    "fea/wood_joint_reduced_properties.py": "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1",
    str(MODEL_INPUTS): "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    str(CURRENT_LOAD_CONTRACT): "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    str(ADAPTER_PREPARE): "b3fd2371fe36eceb4fe7111241130e565eacf4ce94dbfef4eeb2ed7104a80c4a",
    str(ADAPTER_PINS): "3242284af13f7e7d4f5fbe3ca68d22bd76533f2428a8080053f27569278ce228",
    str(A12_MODEL): "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    str(A12_DECK): "11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c",
    str(A12_AUDIT): "1570e9680ae09e1437baa225667806c4e1c7380eac2ddddbd633f342c15a778f",
    str(CURRENT_ADAPTER_DIR / "prepare.py"): "1c634b285b6ce988eaf9eef8bc2bfe52a3d243fd89f4d3f7eb4ba1c31cde5ccb",
    str(CURRENT_ADAPTER_DIR / "source-pins.json"): "61597eb2f67fd38a0c2be601fae314a592cf3ac6c91cf85fe0067df303d175c0",
    str(CURRENT_ADAPTER_DIR / "a12-rear/model.json"): "f880d1fe44d64939d0f4755b62b6e7b007b681b44ffbadc20abe278f8296a44b",
    str(CURRENT_ADAPTER_DIR / "a12-rear/model.inp"): "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    str(CURRENT_ADAPTER_DIR / "audit.json"): "596035007d06fb1bc5e62fc7f2b13d48e8f991f792f847455ffd069a833b1111",
    str(CONDITIONAL_A12_MODEL): "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    str(CONDITIONAL_A12_DECK): "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    str(CONDITIONAL_A12_RESPONSE): "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    str(CONDITIONAL_A12_FREEZE): "a362e551a39afcaed06ecbf0a0f1f18858fbc8677bdf2a927652b543ac67eb03",
    str(CONDITIONAL_A12_EXECUTION): "6827b199681a574b744460e5b2b0e171a26fd68a51093843a897e1abb9744f00",
    str(CONDITIONAL_A12_TERMINAL): "e19dd495bf6ca910a0aa6a070e38dfc00e214974d8e62fbf72624387c80ce075",
    str(CONDITIONAL_A12_BODY_AUDIT): "3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5",
}

CONDITIONAL_A12_REFERENCE = {
    "case_id": "a12-rear",
    "terminal_status": "PASS_CONDITIONAL_NUMERICAL_RESPONSE",
    "selected_bearing_cells": 25,
    "separated_cells": 75,
    "response_sha256": PINNED_SHA256[str(CONDITIONAL_A12_RESPONSE)],
    "model_sha256": PINNED_SHA256[str(CONDITIONAL_A12_MODEL)],
    "deck_sha256": PINNED_SHA256[str(CONDITIONAL_A12_DECK)],
    "terminal_assessment_sha256": PINNED_SHA256[str(CONDITIONAL_A12_TERMINAL)],
    "parent_all_body_audit_sha256": PINNED_SHA256[str(CONDITIONAL_A12_BODY_AUDIT)],
    "path": str(CONDITIONAL_A12_RESPONSE_DIR),
    "scope": "Conditional numerical response for ring A, Hillman axial proxy ratio 1, zero bolt gap, zero accessory, reviewed geometry, and an unverified no-slip floor assumption. Not physical floor qualification, joint acceptance, or a six-case envelope.",
}

SCENARIO_EXPECTED = {
    "mesh_size_mm": 150.0,
    "ring_case": "A",
    "panel_group_factor": 1.0,
    "hillman_axial_to_lateral_ratio": 1.0,
    "hillman_ratio_status": "non-qualifying diagnostic only",
    "bolt_gap_factor": 0.0,
    "contact_penalty_n_per_mm3": 100.0,
    "accessory_scenario_id": None,
    "accessory_budget_kg": 0.0,
    "floor": "unverified no-slip assumption only while each floor cell bears",
    "zero_gap_seed_is_diagnostic_only": True,
}

STATIC_SIGNATURE_FIELDS = (
    "candidate",
    "geometry_revision_id",
    "source_model_inputs_sha256",
    "scenario",
    "material_binding",
    "source_sha256",
    "geometry_source_documents",
    "geometry_audit",
    "body_geometry",
    "physical_body_elements",
    "physical_body_nodes",
    "expected_physical_body_names",
    "connection_ownership",
    "connection_attachment_rows",
    "connection_counts",
    "connection_scenario",
    "contact_cell_ownership",
    "floor_support_nodes",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical(value))


def verify_source_pins() -> dict[str, str]:
    found = {}
    for relative, expected in PINNED_SHA256.items():
        path = ROOT / relative
        observed = sha256_file(path)
        if observed != expected:
            raise ValueError(f"pinned source changed: {relative}: {observed} != {expected}")
        found[relative] = observed

    adapter_pins = json.loads((ROOT / ADAPTER_PINS).read_text(encoding="utf-8"))
    for relative, record in adapter_pins["pinned_inputs"].items():
        expected = record["sha256"]
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise ValueError(f"SPRINGA adapter upstream pin changed: {relative}: {observed} != {expected}")
        found[relative] = observed

    terminal = json.loads((ROOT / CONDITIONAL_A12_TERMINAL).read_text(encoding="utf-8"))
    expected_terminal = {
        "status": CONDITIONAL_A12_REFERENCE["terminal_status"],
        "case_id": "a12-rear",
        "selected_bearing_cells": 25,
        "separated_cells": 75,
        "response_sha256": CONDITIONAL_A12_REFERENCE["response_sha256"],
        "independent_parent_all_body_pass": True,
        "conditional_case_forces_usable": True,
        "six_case_demands_complete": False,
        "joint_acceptance": False,
    }
    for key, expected in expected_terminal.items():
        if terminal.get(key) != expected:
            raise ValueError(f"conditional a12 response terminal field changed: {key}")
    return dict(sorted(found.items()))


def vec_close(a: Any, b: Any, *, tolerance: float = 1e-9) -> bool:
    return (
        isinstance(a, list)
        and isinstance(b, list)
        and len(a) == len(b)
        and all(abs(float(x) - float(y)) <= tolerance for x, y in zip(a, b, strict=True))
    )


def verify_contract_projection(source: dict[str, Any], contract: dict[str, Any]) -> None:
    if source["case_id"] != contract["case_id"] or source["hold_id"] != contract["hold_id"]:
        raise ValueError(f"case/hold mismatch: {source['case_id']}")
    if source["case_inputs"] != contract["case_inputs"]:
        raise ValueError(f"case force-input mismatch: {source['case_id']}")
    comparisons = (
        (source["applied_force_global_xyz_n"], contract["applied_force_global_xyz_n"], "applied force"),
        (source["force_application_point_global_xyz_mm"], contract["standoff"]["force_application_point_global_xyz_mm"], "application point"),
        (source["wrench_reference_point_global_xyz_mm"], contract["panel_midplane_applicationpoint_global_xyz_mm"], "wrench reference"),
        (source["moment_global_xyz_nmm"], contract["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"], "moment"),
        (source["patch_center_global_xyz_mm"], contract["panel_patch"]["center_global_xyz_mm"], "patch center"),
    )
    for observed, expected, label in comparisons:
        if not vec_close(observed, expected):
            raise ValueError(f"{label} differs from current load contract for {source['case_id']}")
    if float(source["patch_size_mm"]) != float(contract["panel_patch"]["size_mm"]):
        raise ValueError(f"patch size differs from current load contract for {source['case_id']}")


def _load_map_record(loads: dict[Any, Any]) -> dict[str, Any]:
    normalized = {str(int(node)): [float(value) for value in vector] for node, vector in loads.items()}
    return {
        "node_count": len(normalized),
        "sha256": canonical_hash(normalized),
        "loads": normalized,
    }


def _body_wrench_record(wrenches: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "body": body,
            "force_xyz_n": [float(value) for value in wrenches[body]["force_xyz_n"]],
            "moment_about_global_origin_xyz_nmm": [
                float(value) for value in wrenches[body]["moment_about_global_origin_xyz_nmm"]
            ],
        }
        for body in sorted(wrenches)
    ]


def _load_map_delta(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    deltas = []
    changed_components = 0
    for node in sorted(set(current) | set(baseline), key=int):
        a = baseline.get(node, [0.0, 0.0, 0.0])
        b = current.get(node, [0.0, 0.0, 0.0])
        delta = [float(b[i]) - float(a[i]) for i in range(3)]
        nonzero = sum(value != 0.0 for value in delta)
        if nonzero:
            changed_components += nonzero
            deltas.append({"node": int(node), "delta_force_xyz_n": delta})
    return {
        "changed_node_count": len(deltas),
        "changed_component_count": changed_components,
        "delta_sha256": canonical_hash(deltas),
        "changed_node_deltas": deltas,
    }


def _body_wrench_delta(current: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base_by_body = {row["body"]: row for row in baseline}
    changed = []
    for row in current:
        before = base_by_body[row["body"]]
        delta_force = [
            float(row["force_xyz_n"][i]) - float(before["force_xyz_n"][i]) for i in range(3)
        ]
        delta_moment = [
            float(row["moment_about_global_origin_xyz_nmm"][i])
            - float(before["moment_about_global_origin_xyz_nmm"][i])
            for i in range(3)
        ]
        if any(value != 0.0 for value in delta_force + delta_moment):
            changed.append({
                "body": row["body"],
                "delta_force_xyz_n": delta_force,
                "delta_moment_about_global_origin_xyz_nmm": delta_moment,
            })
    return changed


def _contract_load_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "hold_id": row["hold_id"],
        "case_inputs": copy.deepcopy(row["case_inputs"]),
        "applied_force_global_xyz_n": copy.deepcopy(row["applied_force_global_xyz_n"]),
        "applied_wrench": copy.deepcopy(row["applied_wrench"]),
        "panel_patch": copy.deepcopy(row["panel_patch"]),
        "standoff": copy.deepcopy(row["standoff"]),
        "panel_midplane_applicationpoint_global_xyz_mm": copy.deepcopy(
            row["panel_midplane_applicationpoint_global_xyz_mm"]
        ),
        "moment_about_panel_midplane_applicationpoint_global_xyz_nmm": copy.deepcopy(
            row["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"]
        ),
    }


def _fresh_case(case_id: str, contract_row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    structure, _panels, metadata = build_case(case_id, **BUILD_KWARGS)
    if metadata.get("case_id") != case_id:
        raise ValueError(f"fresh builder returned wrong case id for {case_id}")
    if metadata.get("scenario") != SCENARIO_EXPECTED:
        raise ValueError(f"fresh builder scenario changed for {case_id}: {metadata.get('scenario')}")
    if metadata.get("source_model_inputs_sha256") != PINNED_SHA256[str(MODEL_INPUTS)]:
        raise ValueError(f"fresh builder model-input source hash changed for {case_id}")
    case_input = metadata["case_input"]
    source_load = case_input["source_applied_load"]
    verify_contract_projection(source_load, contract_row)

    static_signature = {key: copy.deepcopy(metadata[key]) for key in STATIC_SIGNATURE_FIELDS}
    if metadata["connection_scenario"].get("hillman_physical_stiffness_bounds_established") is not False:
        raise ValueError("Hillman axial ratio remains a diagnostic, not a qualified stiffness bound")

    physical_loads = _load_map_record(metadata["physical_external_loads"])
    body_wrenches = _body_wrench_record(metadata["physical_body_wrenches"])
    audit = metadata["case_assembly_audit"]
    row = {
        "case_id": case_id,
        "loaded_panel": case_input["loaded_panel"],
        "current_load_contract": _contract_load_record(contract_row),
        "fresh_build_case_source_applied_load": copy.deepcopy(source_load),
        "scenario": copy.deepcopy(metadata["scenario"]),
        "connection_scenario": copy.deepcopy(metadata["connection_scenario"]),
        "source_model_inputs_sha256": metadata["source_model_inputs_sha256"],
        "fresh_case_metadata_sha256": canonical_hash(metadata),
        "source_sha256": copy.deepcopy(metadata["source_sha256"]),
        "physical_external_load_map": {
            "node_count": physical_loads["node_count"],
            "sha256": physical_loads["sha256"],
            "loads_by_node": physical_loads["loads"],
        },
        "source_wrench_ledger": {
            "row_count": len(metadata["source_wrench_ledger"]),
            "sha256": canonical_hash(metadata["source_wrench_ledger"]),
        },
        "physical_body_wrenches": body_wrenches,
        "case_assembly_audit": {
            key: copy.deepcopy(audit[key])
            for key in (
                "global_force_xyz_n",
                "global_moment_about_origin_xyz_nmm",
                "expected_global_force_xyz_n",
                "expected_global_moment_about_origin_xyz_nmm",
                "max_body_force_residual_n",
                "max_body_moment_residual_nmm",
                "physical_body_count",
                "physical_body_node_count",
                "physical_element_count",
                "native_solve_executed",
                "mechanical_acceptance",
            )
        },
        "floor_bearing_mask": {
            "required_per_case": True,
            "mask_recorded_in_this_source_load_register": False,
            "input_register_value": None,
            "state": (
                "CONDITIONAL_A12_RESPONSE_REFERENCE_EXISTS_OUTSIDE_THIS_REGISTER"
                if case_id == "a12-rear"
                else "UNRESOLVED_CASE_SPECIFIC_RESPONSE_AND_MASK"
            ),
            "current_response_reference": copy.deepcopy(CONDITIONAL_A12_REFERENCE) if case_id == "a12-rear" else None,
            "why": "A separate per-case mask is required. The a12-rear 25/75 branch is case-specific and must not transfer to the other five cases.",
        },
    }
    del structure, _panels, metadata
    gc.collect()
    return row, static_signature


def build_register() -> dict[str, Any]:
    explicit_source_pins = verify_source_pins()
    model_inputs = json.loads((ROOT / MODEL_INPUTS).read_text(encoding="utf-8"))
    contract = json.loads((ROOT / CURRENT_LOAD_CONTRACT).read_text(encoding="utf-8"))
    model_cases = model_inputs.get("cases", [])
    contract_cases = contract.get("cases", [])
    if [row.get("case_id") for row in model_cases] != CASE_IDS:
        raise ValueError("model-inputs case order/IDs differ from the current six-case source")
    if [row.get("case_id") for row in contract_cases] != CASE_IDS:
        raise ValueError("current load contract case order/IDs differ from the current six-case source")
    if model_inputs.get("revision_id") != contract.get("geometry_revision_id"):
        raise ValueError("builder and current load contract geometry revisions differ")
    contract_by_id = {row["case_id"]: row for row in contract_cases}

    case_records = []
    signatures = []
    for case_id in CASE_IDS:
        print(f"fresh build_case metadata: {case_id}", flush=True)
        row, signature = _fresh_case(case_id, contract_by_id[case_id])
        case_records.append(row)
        signatures.append(signature)

    base = case_records[0]
    base_map = base["physical_external_load_map"]["loads_by_node"]
    base_body = base["physical_body_wrenches"]
    baseline_load = base["fresh_build_case_source_applied_load"]
    baseline_audit = base["case_assembly_audit"]
    for index, record in enumerate(case_records):
        if signatures[index] != signatures[0]:
            raise ValueError(f"non-load model signature differs from a12-rear for {record['case_id']}")
        direct = record["fresh_build_case_source_applied_load"]
        record["differences_from_a12_rear"] = {
            "case_id_changed": direct["case_id"] != baseline_load["case_id"],
            "hold_id_changed": direct["hold_id"] != baseline_load["hold_id"],
            "loaded_panel_changed": record["loaded_panel"] != base["loaded_panel"],
            "horizontal_force_delta_global_xy_n": [
                float(direct["case_inputs"]["horizontal_force_global_xy_n"][i])
                - float(baseline_load["case_inputs"]["horizontal_force_global_xy_n"][i])
                for i in range(2)
            ],
            "applied_force_delta_global_xyz_n": [
                float(direct["applied_force_global_xyz_n"][i])
                - float(baseline_load["applied_force_global_xyz_n"][i])
                for i in range(3)
            ],
            "applied_moment_delta_at_panel_midplane_nmm": [
                float(direct["moment_global_xyz_nmm"][i])
                - float(baseline_load["moment_global_xyz_nmm"][i])
                for i in range(3)
            ],
            "application_point_delta_global_xyz_mm": [
                float(direct["force_application_point_global_xyz_mm"][i])
                - float(baseline_load["force_application_point_global_xyz_mm"][i])
                for i in range(3)
            ],
            "wrench_reference_point_delta_global_xyz_mm": [
                float(direct["wrench_reference_point_global_xyz_mm"][i])
                - float(baseline_load["wrench_reference_point_global_xyz_mm"][i])
                for i in range(3)
            ],
            "physical_external_load_map_delta_from_a12": _load_map_delta(
                record["physical_external_load_map"]["loads_by_node"], base_map
            ),
            "physical_body_wrench_deltas_from_a12": _body_wrench_delta(
                record["physical_body_wrenches"], base_body
            ),
            "global_equilibrium_force_delta_xyz_n": [
                float(record["case_assembly_audit"]["expected_global_force_xyz_n"][i])
                - float(baseline_audit["expected_global_force_xyz_n"][i])
                for i in range(3)
            ],
            "global_equilibrium_moment_delta_about_origin_xyz_nmm": [
                float(record["case_assembly_audit"]["expected_global_moment_about_origin_xyz_nmm"][i])
                - float(baseline_audit["expected_global_moment_about_origin_xyz_nmm"][i])
                for i in range(3)
            ],
        }
        del record["physical_external_load_map"]["loads_by_node"]

    adapter_model = json.loads((ROOT / A12_MODEL).read_text(encoding="utf-8"))
    settings = copy.deepcopy(case_records[0]["scenario"])
    if adapter_model.get("scenario") != settings:
        raise ValueError("fresh a12-rear scenario differs from the pinned SPRINGA adapter scenario")
    if adapter_model.get("case_id") != "a12-rear":
        raise ValueError("pinned SPRINGA adapter is not the a12-rear source input")

    return {
        "schema": "current_springa_six_case_source_load_register/v1",
        "status": "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER",
        "candidate": model_inputs["candidate"],
        "geometry_revision_id": model_inputs["revision_id"],
        "current_load_contract_sha256": contract["contract_sha256"],
        "case_id_order": CASE_IDS,
        "build_case_kwargs": BUILD_KWARGS,
        "common_scenario_settings": settings,
        "nonload_source_geometry_and_carrier_signature_sha256": canonical_hash(signatures[0]),
        "same_nonload_signature_across_all_six_cases": True,
        "source_pins": explicit_source_pins,
        "source_model_input_hashes_from_fresh_build_case": copy.deepcopy(case_records[0]["source_sha256"]),
        "adapter_reuse_contract": {
            "pinned_adapter_case_id": "a12-rear",
            "adapter_schema": adapter_model["schema"],
            "adapter_input_only": adapter_model["input_only"],
            "adapter_native_solve_executed": adapter_model["native_solve_executed"],
            "a12_support_response_gate": "Do not assemble or run the other five as response cases until the a12 support response assessment passes.",
            "existing_adapter_case_binding": [
                "prepare.py calls build_case('a12-rear') and checks metadata case_id == 'a12-rear'.",
                "CASE_DIR is fixed to a12-rear; per-case output paths must be parameterized before six-case assembly.",
                "_validate_source_geometry compares case-dependent physical loads and wrench fields to pinned C11 a12 data; retain strict checks for invariant geometry/carrier fields and bind each case's fresh load fields to that case's source register.",
                "_normalize_fresh_source_loads currently checks the expanded map against fresh metadata and also cross-checks the pinned C11 a12 physical load map; that C11 load equality is a12-specific and must not be treated as the other five cases' load oracle.",
                "The serialized source CLOAD and exact-floor transforms must be rebuilt/audited for each case from its fresh physical_external_loads map; no historical response forces are a valid source.",
            ],
            "floor_branch": {
                "adapter_rule": adapter_model["floor_constraint_audit"]["floor_condition"],
                "original_tangent_constraint_rows": adapter_model["floor_constraint_audit"]["original_constraint_rows"],
                "fresh_scalar_reference_nodes": adapter_model["floor_constraint_audit"]["floor_reference_node_count"],
                "separate_bearing_mask_required_for_each_case": True,
                "masks_in_this_register": "The a12-rear 25-bearing/75-separated branch is referenced separately; fresh build_case metadata supplies no mask. The other five case-specific masks and responses are unresolved.",
                "mask_transfer_from_a12": False,
            },
            "control_settings_to_preserve": {
                "step": "*STEP,NLGEOM,NLGEOM=NO,INC=40; *STATIC; 0.1,1.0,1.e-6,0.25",
                "output": "*NODE PRINT,NSET=ALLN,FREQUENCY=1 U,RF",
                "source_carrier_counts": {"SPRINGA": 1292, "bilateral_SPRING2": 348},
                "floor_tangent_rows_replaced_by_exact_constraints": 200,
                "reuse_requires": "same source-bound carrier inventory and floor constraint signature already confirmed across all six fresh builds in this register",
            },
            "claim_limit": "This register covers source applied loads and load-to-wrench assembly only; it contains no solved forces, response, support mask, capacity, or case acceptance.",
        },
        "conditional_a12_response_reference": copy.deepcopy(CONDITIONAL_A12_REFERENCE),
        "cases": case_records,
        "limits": [
            "All six records come from fresh fea.wood_joint_reduced_case.build_case metadata using the same explicit a12 scenario kwargs; no native solve or deck rewrite was performed.",
            "Global and body wrenches are applied external loads from source assembly, not reactions, contact forces, or joint demands.",
            "The a12-rear case remains the source adapter baseline. The five other load maps are registered independently and must not inherit its response or floor-bearing mask.",
            "The Hillman axial-to-lateral ratio of 1.0 is a non-qualifying diagnostic setting, not a supported physical stiffness bound.",
            "The zero bolt-gap factor remains diagnostic only; contact penalty is a model setting, not a measured connection property.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write register.json from six fresh build_case metadata records")
    mode.add_argument("--verify", action="store_true", help="rebuild six metadata records and compare register.json")
    args = parser.parse_args()
    result = build_register()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}; six source load/wrench records; no native solve")
        return
    if not OUTPUT.is_file():
        raise SystemExit("missing register.json; run with --write")
    if OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("verification failed: fresh case metadata differs from register.json")
    print("PASS: six fresh source load/wrench records reproduce; no native solve")


if __name__ == "__main__":
    main()
