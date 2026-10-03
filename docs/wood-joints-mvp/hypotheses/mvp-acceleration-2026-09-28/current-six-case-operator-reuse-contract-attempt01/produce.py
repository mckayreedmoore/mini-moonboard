"""Verify common source elastic inputs/projections across the six load cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
SINGLE = BASE / "current-springa-frame-input-adapter-attempt01"
FIVE = BASE / "current-springa-six-case-frame-input-adapter-attempt01"
GRAVITY = BASE / "current-gravity-settle-climber-ramp-scenario-attempt01"
FLOOR = BASE / "current-floor-stick-constraint-audit-attempt01"
C11_DECK = BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.inp"
OUT = BASE / "current-six-case-operator-reuse-contract-attempt01"
CASE_IDS = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
CASE_REL = {"a12-rear": SINGLE / "a12-rear"}
CASE_REL.update({case: FIVE / case for case in CASE_IDS[1:]})
EXPANSION_PRUNE = 1e-13
COORDINATE_TOL_MM = 1e-10
PROPERTY_KEYWORDS = {"MATERIAL", "ELASTIC", "DENSITY", "ORIENTATION", "SOLID SECTION", "SHELL SECTION"}


class ReuseContractError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load_json(relative: Path) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def add_pin(pins: dict[str, str], relative: str, expected: str | None = None) -> None:
    path = ROOT / relative
    if not path.is_file():
        raise ReuseContractError(f"Pinned source missing: {relative}")
    actual = digest_file(path)
    if expected is not None and actual != expected:
        raise ReuseContractError(f"Source pin mismatch for {relative}: {actual} != {expected}")
    if relative in pins and pins[relative] != actual:
        raise ReuseContractError(f"Conflicting source pin for {relative}")
    pins[relative] = actual


def parse_keyword_blocks(path: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            parts = [part.strip() for part in line[1:].split(",")]
            current = {"keyword": parts[0].upper(), "header": [part.upper() for part in parts], "data": []}
            blocks.append(current)
        elif current is not None:
            current["data"].append(line)
    return blocks


def deck_source_data(deck: Path) -> dict[str, Any]:
    blocks = parse_keyword_blocks(deck)
    nodes: dict[int, list[float]] = {}
    c3d20: dict[int, dict[str, Any]] = {}
    properties: list[dict[str, Any]] = []
    for block in blocks:
        keyword = block["keyword"]
        if keyword == "NODE":
            for line in block["data"]:
                fields = [value.strip() for value in line.split(",")]
                if len(fields) != 4:
                    raise ReuseContractError(f"Malformed *NODE row in {deck}: {line}")
                tag = int(fields[0])
                if tag in nodes:
                    raise ReuseContractError(f"Duplicate *NODE tag in {deck}: {tag}")
                nodes[tag] = [float(value) for value in fields[1:]]
        elif keyword == "ELEMENT" and any(value.startswith("TYPE=C3D20") for value in block["header"][1:]):
            elset = next((value.split("=", 1)[1].lower() for value in block["header"][1:] if value.startswith("ELSET=")), None)
            if elset is None:
                raise ReuseContractError(f"C3D20 block lacks ELSET in {deck}")
            pending: list[int] = []
            for line in block["data"]:
                pending.extend(int(value.strip()) for value in line.split(",") if value.strip())
                while len(pending) >= 21:
                    record, pending = pending[:21], pending[21:]
                    element = record[0]
                    if element in c3d20:
                        raise ReuseContractError(f"Duplicate C3D20 id in {deck}: {element}")
                    c3d20[element] = {"connectivity": record[1:], "elset": elset}
            if pending:
                raise ReuseContractError(f"Truncated C3D20 connectivity in {deck}: {pending}")
        if keyword in PROPERTY_KEYWORDS:
            properties.append({"header": block["header"], "data": block["data"]})
    return {"nodes": nodes, "c3d20": c3d20, "property_cards": properties, "blocks": blocks}


def physical_maps(model: dict[str, Any], deck_data: dict[str, Any], case_id: str) -> dict[str, Any]:
    body_of_node: dict[int, str] = {}
    for body, tags in model["physical_body_nodes"].items():
        for raw in tags:
            node = int(raw)
            if node in body_of_node:
                raise ReuseContractError(f"Physical node has multiple body owners in {case_id}: {node}")
            body_of_node[node] = body
    if len(body_of_node) != 12549 or len(model["physical_body_nodes"]) != 50:
        raise ReuseContractError(f"Physical node/body inventory changed in {case_id}")
    physical_nodes = sorted(body_of_node)
    model_coords = {node: list(map(float, model["nodes"][str(node)])) for node in physical_nodes}
    deck_nodes = deck_data["nodes"]
    if not set(physical_nodes).issubset(deck_nodes):
        raise ReuseContractError(f"Physical node missing from actual deck in {case_id}")
    max_coord_residual = max(abs(model_coords[node][axis] - deck_nodes[node][axis]) for node in physical_nodes for axis in range(3))
    if max_coord_residual > COORDINATE_TOL_MM:
        raise ReuseContractError(f"Actual deck coordinates exceed {COORDINATE_TOL_MM} mm from model in {case_id}: {max_coord_residual}")

    body_of_element: dict[int, str] = {}
    for body, ids in model["physical_body_elements"].items():
        for raw in ids:
            element = int(raw)
            if element in body_of_element:
                raise ReuseContractError(f"Physical C3D20 has multiple body owners in {case_id}: {element}")
            body_of_element[element] = body
    if len(body_of_element) != 1903 or len(deck_data["c3d20"]) != 1903:
        raise ReuseContractError(f"Physical C3D20 count changed in {case_id}")
    model_c3d20: dict[int, dict[str, Any]] = {}
    for raw_id, value in model["elements"].items():
        if value[0] == "C3D20":
            model_c3d20[int(raw_id)] = {"connectivity": list(map(int, value[1])), "elset": str(value[2])}
    if set(model_c3d20) != set(body_of_element) or set(model_c3d20) != set(deck_data["c3d20"]):
        raise ReuseContractError(f"Physical element ownership / actual C3D20 sets disagree in {case_id}")
    for eid, record in model_c3d20.items():
        actual = deck_data["c3d20"][eid]
        if record != actual:
            raise ReuseContractError(f"Actual C3D20 record differs from model for {case_id} element {eid}")
        owner = body_of_element[eid]
        if any(body_of_node.get(node) != owner for node in record["connectivity"]):
            raise ReuseContractError(f"C3D20 connectivity crosses physical body ownership in {case_id}, element {eid}")
    if set(body_of_element.values()) != set(model["physical_body_nodes"]):
        raise ReuseContractError(f"Body node and C3D20 owner sets differ in {case_id}")
    coord_payload = [[node, model_coords[node]] for node in physical_nodes]
    deck_coord_payload = [[node, deck_nodes[node]] for node in physical_nodes]
    c3d20_payload = [[eid, body_of_element[eid], model_c3d20[eid]["elset"], model_c3d20[eid]["connectivity"]] for eid in sorted(model_c3d20)]
    owners_payload = {
        "body_nodes": {body: sorted(map(int, tags)) for body, tags in sorted(model["physical_body_nodes"].items())},
        "body_elements": {body: sorted(map(int, tags)) for body, tags in sorted(model["physical_body_elements"].items())},
    }
    return {
        "physical_nodes": physical_nodes,
        "body_of_node": body_of_node,
        "body_of_element": body_of_element,
        "model_coordinate_hash": digest_value(coord_payload),
        "deck_coordinate_hash": digest_value(deck_coord_payload),
        "c3d20_hash": digest_value(c3d20_payload),
        "ownership_hash": digest_value(owners_payload),
        "actual_deck_model_coordinate_max_abs_residual_mm": max_coord_residual,
    }


def expand_projection_rows(model: dict[str, Any], maps: dict[str, Any], case_id: str) -> dict[str, Any]:
    physical_nodes = maps["physical_nodes"]
    body_of_node = maps["body_of_node"]
    physical_index = {node: idx for idx, node in enumerate(physical_nodes)}
    coordinate_index = {(node, dof): 3 * physical_index[node] + dof - 1 for node in physical_nodes for dof in (1, 2, 3)}
    fixed_dofs = {(int(node), dof) for node in model["fixed_nodes"] for dof in (1, 2, 3)}
    conditional_keys = {tuple(map(int, row["dependent_physical_pivot_dof"])) for row in model["exact_floor_mpc_equations"]}
    equations: dict[tuple[int, int], list[list[float]]] = {}
    for terms in model["equations"]:
        key = (int(terms[0][0]), int(terms[0][1]))
        if key in equations:
            raise ReuseContractError(f"Duplicate equation pivot in {case_id}: {key}")
        equations[key] = terms
    if len(conditional_keys) != 200 or not conditional_keys.issubset(equations):
        raise ReuseContractError(f"Conditional floor pivot set changed in {case_id}")
    permanent = {key: value for key, value in equations.items() if key not in conditional_keys}
    if len(permanent) != len(equations) - 200:
        raise ReuseContractError(f"Unexpected permanent equation count in {case_id}")
    cache: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    active: set[tuple[int, int]] = set()
    def expand(key: tuple[int, int]) -> dict[tuple[int, int], float]:
        if key in cache:
            return cache[key]
        if key in active:
            raise ReuseContractError(f"Circular permanent MPC in {case_id}: {key}")
        active.add(key)
        if key in fixed_dofs:
            result: dict[tuple[int, int], float] = {}
        elif key not in permanent:
            result = {key: 1.0}
        else:
            terms = permanent[key]
            pivot = float(terms[0][2])
            if pivot == 0.0:
                raise ReuseContractError(f"Zero permanent MPC pivot in {case_id}: {key}")
            result = {}
            for node, dof, coefficient in terms[1:]:
                for master, weight in expand((int(node), int(dof))).items():
                    result[master] = result.get(master, 0.0) - float(coefficient) * weight / pivot
            result = {term: value for term, value in result.items() if abs(value) > EXPANSION_PRUNE}
        active.remove(key)
        cache[key] = result
        return result
    def qrow(first: int, second: int, dof: int) -> list[list[Any]]:
        terms = expand((second, dof)).copy()
        for key, value in expand((first, dof)).items():
            terms[key] = terms.get(key, 0.0) - value
        terms = {key: value for key, value in terms.items() if abs(value) > EXPANSION_PRUNE}
        out = []
        for (node, direction), value in sorted(terms.items(), key=lambda pair: coordinate_index.get(pair[0], 10**12)):
            if node not in body_of_node or (node, direction) not in coordinate_index:
                raise ReuseContractError(f"Projection did not close on physical translation in {case_id}: {(node, direction)}")
            out.append([coordinate_index[(node, direction)], float(value)])
        if len({term[0] for term in out}) != len(out):
            raise ReuseContractError(f"Duplicate normalized physical coordinate in {case_id}")
        return out
    rows: list[dict[str, Any]] = []
    for spring in model["springs"]:
        row = qrow(int(spring["nodes"][0]), int(spring["nodes"][1]), int(spring["dof"]))
        if not row:
            raise ReuseContractError(f"Empty bilateral physical row in {case_id}: {spring['name']}")
        rows.append({
            "family": "bilateral_spring2", "row_id": spring["name"], "group": spring["group"],
            "intended_law": spring["intended_law"], "stiffness_N_per_mm": float(spring["stiffness_n_per_mm"]),
            "owner": spring["physical_owner"], "physical_projection_row": row,
        })
    inventory = model["raw_source_carrier_law_inventory_rows"]
    for binding in model["unilateral_springa_bindings"]:
        source = inventory[int(binding["source_inventory_row_index"])]
        if source["name"] != binding["name"] or list(map(int, source["nodes"])) != list(map(int, binding["source_projection_nodes"])) or int(source["dof"]) != int(binding["source_projection_dof"]):
            raise ReuseContractError(f"Unilateral projection/source inventory mismatch in {case_id}: {binding['name']}")
        row = qrow(int(binding["source_projection_nodes"][0]), int(binding["source_projection_nodes"][1]), int(binding["source_projection_dof"]))
        if not row:
            raise ReuseContractError(f"Empty unilateral physical row in {case_id}: {binding['name']}")
        rows.append({
            "family": "unilateral_springa", "row_id": binding["name"], "group": binding["group"],
            "intended_law": source["intended_law"], "force_law": binding["force_law"],
            "stiffness_N_per_mm": float(binding["stiffness_n_per_mm"]),
            "force_table_N_mm": binding["force_vs_elongation_table_N_mm"],
            "owner": binding["physical_owner"],
            "ground_endpoint": {"node": int(binding["springa_nodes"][1]), "numerical_only": bool(binding["ground_endpoint_is_numerical_only"])},
            "source_projection": {"nodes": binding["source_projection_nodes"], "dof": int(binding["source_projection_dof"]), "springa_nodes": binding["springa_nodes"], "qghost_equations": binding["qghost_equations"]},
            "physical_projection_row": row,
        })
    if len(rows) != 1640:
        raise ReuseContractError(f"Normalized connector row count changed in {case_id}: {len(rows)}")
    return {
        "rows": rows,
        "row_sha256": digest_value(rows),
        "row_count": len(rows),
        "nonzero_count": sum(len(row["physical_projection_row"]) for row in rows),
        "nonzero_max": max(len(row["physical_projection_row"]) for row in rows),
        "permanent_equation_count": len(permanent),
        "permanent_mpc_sha256": digest_value([[list(key), permanent[key]] for key in sorted(permanent)]),
        "conditional_floor_equation_sha256": digest_value(model["exact_floor_mpc_equations"]),
    }


def normalized_floor_references(model: dict[str, Any]) -> list[dict[str, Any]]:
    exclude = {"source_load_correction_N", "correction_from_full_precision_matrix_N", "correction_uses_emitted_equation_and_cload_values"}
    normalized = []
    for row in model["floor_reference_nodes"]:
        normalized.append({key: value for key, value in row.items() if key not in exclude})
    return normalized


def build_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    adapter_single_pins_rel = SINGLE / "source-pins.json"
    adapter_single_audit_rel = SINGLE / "a12-rear/audit.json"
    adapter_five_pins_rel = FIVE / "source-pins.json"
    adapter_five_audit_rel = FIVE / "audit.json"
    decomp_rel = GRAVITY / "decomposition.json"
    decomp_script_rel = GRAVITY / "verify_decomposition.py"
    decomp_pins_rel = GRAVITY / "source-pins.json"
    floor_audit_rel = FLOOR / "audit.json"
    floor_matrix_rel = FLOOR / "constraint-matrices.npz"

    single_pins = load_json(adapter_single_pins_rel)
    single_audit = load_json(adapter_single_audit_rel)
    five_pins = load_json(adapter_five_pins_rel)
    five_audit = load_json(adapter_five_audit_rel)
    decomposition = load_json(decomp_rel)
    decomp_pins = load_json(decomp_pins_rel)
    floor_audit = load_json(floor_audit_rel)
    if digest_file(ROOT / adapter_single_pins_rel) != single_audit["source_pins_json_sha256"]:
        raise ReuseContractError("A12 adapter audit no longer binds its source-pins.json")
    if digest_file(ROOT / adapter_five_pins_rel) != five_audit["source_pins_json_sha256"]:
        raise ReuseContractError("Five-case adapter audit no longer binds its source-pins.json")
    if decomposition.get("status") != "PASS_SIX_CASE_SOURCE_LOAD_DECOMPOSITION_AND_EXACT_RECOMPOSITION":
        raise ReuseContractError("Pinned six-case decomposition status changed")
    if digest_file(ROOT / decomp_script_rel) != decomposition["producer_sha256"]:
        raise ReuseContractError("Gravity decomposition producer hash changed")
    if digest_file(ROOT / decomp_pins_rel) != decomposition["source_pins_sha256"]:
        raise ReuseContractError("Gravity decomposition source pin file changed")
    if floor_audit.get("source_input_sha256") != single_pins["pinned_inputs"][str(BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json")]["sha256"]:
        raise ReuseContractError("Floor constraint audit no longer shares the pinned C11 source input")

    declared_inputs: dict[str, str] = {}
    source_pin_aliases: dict[str, str] = {}
    for pinfile in [single_pins, five_pins, decomp_pins]:
        for path, record in pinfile.get("pinned_inputs", {}).items():
            expected = record["sha256"] if isinstance(record, dict) else str(record)
            actual_path = path if path.startswith("docs/") else path.partition(":")[2]
            if not actual_path:
                raise ReuseContractError(f"Unrecognized source pin path alias: {path}")
            if actual_path in declared_inputs and declared_inputs[actual_path] != expected:
                raise ReuseContractError(f"Source pin maps disagree for {actual_path}")
            declared_inputs[actual_path] = expected
            if actual_path != path:
                source_pin_aliases[path] = actual_path
    # Every generated case has its own source pin record; authenticate its
    # source set and both its local and aggregate output hashes.
    cases: dict[str, Any] = {}
    input_pin_map = dict(declared_inputs)
    for case_id in CASE_IDS:
        directory = CASE_REL[case_id]
        model_rel, deck_rel, audit_rel = directory / "model.json", directory / "model.inp", directory / "audit.json"
        model_path, deck_path, audit_path = ROOT / model_rel, ROOT / deck_rel, ROOT / audit_rel
        model = json.loads(model_path.read_text(encoding="utf-8"))
        local_audit = json.loads(audit_path.read_text(encoding="utf-8"))
        local_source_rel = (SINGLE if case_id == "a12-rear" else directory) / "source-pins.json"
        local_source_path = ROOT / local_source_rel
        local_source = json.loads(local_source_path.read_text(encoding="utf-8"))
        if digest_file(local_source_path) != local_audit["source_pins_json_sha256"]:
            raise ReuseContractError(f"Case audit does not bind local source pin file: {case_id}")
        if model.get("case_id") != case_id or model.get("candidate") != "compact-floor-flush-wood-joints-development":
            raise ReuseContractError(f"Case identity changed: {case_id}")
        if model.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
            raise ReuseContractError(f"Geometry revision changed: {case_id}")
        if model.get("native_solve_executed") is not False or model.get("input_only") is not True:
            raise ReuseContractError(f"Input-only/no-native source guard changed: {case_id}")
        local_expected_model = local_source.get("output_model_sha256")
        local_expected_deck = local_source.get("output_deck_sha256")
        if digest_file(model_path) != local_expected_model or digest_file(deck_path) != local_expected_deck:
            raise ReuseContractError(f"Local source pin output hash mismatch: {case_id}")
        if local_audit.get("output_files_sha256", {}).get("model.json") != local_expected_model or local_audit.get("output_files_sha256", {}).get("model.inp") != local_expected_deck:
            raise ReuseContractError(f"Case output audit and local source pins disagree: {case_id}")
        if case_id == "a12-rear":
            aggregate_expected = {"model.json": single_pins["output_model_sha256"], "model.inp": single_pins["output_deck_sha256"]}
        else:
            aggregate_expected = five_pins["output_files_sha256"][case_id]
        for filename, expected in aggregate_expected.items():
            local_path = ROOT / (directory / filename)
            if digest_file(local_path) != expected:
                raise ReuseContractError(f"Aggregate adapter output pin mismatch: {case_id}/{filename}")
        for path, record in local_source.get("pinned_inputs", {}).items():
            expected = record["sha256"] if isinstance(record, dict) else str(record)
            actual_path = path if path.startswith("docs/") else path.partition(":")[2]
            if not actual_path:
                raise ReuseContractError(f"Unrecognized case source pin path alias: {path}")
            if actual_path in input_pin_map and input_pin_map[actual_path] != expected:
                raise ReuseContractError(f"Case pin disagreement for {actual_path}")
            input_pin_map[actual_path] = expected
            if actual_path != path:
                source_pin_aliases[path] = actual_path
        cases[case_id] = {"directory": str(directory), "model_rel": model_rel, "deck_rel": deck_rel, "audit_rel": audit_rel, "source_pins_rel": local_source_rel, "model": model, "deck_path": deck_path, "local_source": local_source, "local_audit": local_audit}

    # Decomposition maps each exact case model hash to the selected six-case set.
    decomposition_cases = {entry["case_id"]: entry for entry in decomposition["cases"]}
    if set(decomposition_cases) != set(CASE_IDS) or decomposition.get("source_case_ids") != CASE_IDS:
        raise ReuseContractError("Six-case decomposition case order/set changed")
    for case_id, record in cases.items():
        model_sha = digest_file(ROOT / record["model_rel"])
        decomp_case = decomposition_cases[case_id]
        if decomp_case["input_model_sha256"] != model_sha or decomp_case["input_model_path"] != str(record["model_rel"]):
            raise ReuseContractError(f"Decomposition model binding mismatch for {case_id}")
        if decomp_case.get("exact_nodal_recomposition") is not True:
            raise ReuseContractError(f"Source load map no longer has exact nodal recomposition for {case_id}")

    # Authenticate all transitive declared pins and exact source output files.
    all_pins: dict[str, str] = {}
    for path, expected in sorted(input_pin_map.items()):
        add_pin(all_pins, path, expected)
    direct_files = [
        adapter_single_pins_rel, adapter_single_audit_rel,
        adapter_five_pins_rel, adapter_five_audit_rel,
        decomp_rel, decomp_script_rel, decomp_pins_rel,
        GRAVITY / "scenario-contract.json", floor_audit_rel, floor_matrix_rel,
        BASE / "current-floor-stick-constraint-audit-attempt01/produce.py",
        SINGLE / "prepare.py", FIVE / "prepare_six_cases.py",
        SINGLE / "README.md", FIVE / "README.md",
    ]
    for case_id in CASE_IDS:
        item = cases[case_id]
        for rel in (item["model_rel"], item["deck_rel"], item["audit_rel"], item["source_pins_rel"]):
            add_pin(all_pins, str(rel))
    for rel in direct_files:
        add_pin(all_pins, str(rel))

    decomposition_sha = digest_file(ROOT / decomp_rel)
    expected_decomp_scenario = decomposition["scenario_contract_sha256"]
    if digest_file(ROOT / (ROOT / decomp_rel).parent / "scenario-contract.json") != expected_decomp_scenario:
        raise ReuseContractError("Gravity decomposition scenario contract hash changed")
    floor_npz_path = ROOT / floor_matrix_rel
    floor_npz = np.load(floor_npz_path, allow_pickle=False)
    floor_matrix = np.asarray(floor_npz["original"], dtype="<f8")
    if floor_matrix.shape != (200, 800) or len(floor_audit["row_owners"]) != 200 or len(floor_audit["physical_master_dofs"]) != 800:
        raise ReuseContractError("Pinned conditional floor source matrix shape/row ownership changed")
    floor_master_set = {tuple(map(int, dof)) for dof in floor_audit["physical_master_dofs"]}
    if len(floor_master_set) != 800 or int(floor_audit["independent_constraint_rank"]) != 200:
        raise ReuseContractError("Pinned floor source masters/rank changed")
    floor_data = {
        "audit_sha256": all_pins[str(floor_audit_rel)],
        "matrix_file_sha256": all_pins[str(floor_matrix_rel)],
        "original_matrix_shape": list(floor_matrix.shape),
        "original_matrix_float64_le_sha256": digest_bytes(floor_matrix.tobytes(order="C")),
        "row_owners_sha256": digest_value(floor_audit["row_owners"]),
        "physical_master_dofs_sha256": digest_value(floor_audit["physical_master_dofs"]),
        "conditional_rank": int(floor_audit["independent_constraint_rank"]),
        "native_solve_executed": bool(floor_audit["native_solve_executed"]),
    }

    case_summaries: dict[str, Any] = {}
    per_case_component_hashes: dict[str, dict[str, str]] = {}
    per_case_projection: dict[str, Any] = {}
    common_property_sequence: list[dict[str, Any]] | None = None
    common_maps: dict[str, Any] | None = None
    common_projection_payloads: dict[str, Any] | None = None
    deck_card_counts: dict[str, dict[str, int]] = {}
    load_hashes: dict[str, str] = {}
    max_coord_residual = 0.0
    for case_id in CASE_IDS:
        item = cases[case_id]
        model = item["model"]
        deck_data = deck_source_data(item["deck_path"])
        maps = physical_maps(model, deck_data, case_id)
        max_coord_residual = max(max_coord_residual, maps["actual_deck_model_coordinate_max_abs_residual_mm"])
        property_hash = digest_value(deck_data["property_cards"])
        if len(deck_data["property_cards"]) != 218:
            raise ReuseContractError(f"Expected 218 ordered property cards in {case_id}; got {len(deck_data['property_cards'])}")
        card_counts = Counter(card["header"][0] for card in deck_data["property_cards"])
        deck_card_counts[case_id] = dict(sorted(card_counts.items()))
        if common_property_sequence is None:
            common_property_sequence = deck_data["property_cards"]
        elif deck_data["property_cards"] != common_property_sequence:
            raise ReuseContractError(f"Actual ordered material/elastic/orientation/section cards differ in {case_id}")
        projection = expand_projection_rows(model, maps, case_id)
        source_law_hash = digest_value({
            "springs": model["springs"],
            "unilateral_springa_bindings": model["unilateral_springa_bindings"],
            "raw_source_carrier_law_inventory_rows": model["raw_source_carrier_law_inventory_rows"],
        })
        permanent_mpc_hash = projection["permanent_mpc_sha256"]
        conditional_floor_hash = projection["conditional_floor_equation_sha256"]
        floor_reference_hash = digest_value(normalized_floor_references(model))
        floor_refs = normalized_floor_references(model)
        if len(floor_refs) != 200:
            raise ReuseContractError(f"Expected 200 normalized floor reference rows in {case_id}")
        components = {
            "physical_model_node_coordinates": maps["model_coordinate_hash"],
            "physical_deck_node_coordinates": maps["deck_coordinate_hash"],
            "physical_c3d20_connectivity_and_elset": maps["c3d20_hash"],
            "body_node_and_element_ownership": maps["ownership_hash"],
            "ordered_actual_property_cards": property_hash,
            "body_geometry_and_material_binding": digest_value({"body_geometry": model["body_geometry"], "material_binding": model["material_binding"], "material_deck_audit": model["material_deck_audit"]}),
            "normalized_physical_connector_projection_rows": projection["row_sha256"],
            "permanent_mpcs_after_200_floor_pivots_removed": permanent_mpc_hash,
            "conditional_floor_mpc_rows": conditional_floor_hash,
            "normalized_floor_reference_records_200": floor_reference_hash,
            "source_carrier_laws_and_ownership": source_law_hash,
            "support_and_numerical_ground_inventory": digest_value({"fixed_nodes": model["fixed_nodes"], "floor_support_nodes": model["floor_support_nodes"], "numerical_spring_ground_nodes": model["numerical_spring_ground_nodes"]}),
        }
        per_case_component_hashes[case_id] = components
        per_case_projection[case_id] = {k: projection[k] for k in ("row_sha256", "row_count", "nonzero_count", "nonzero_max", "permanent_equation_count", "permanent_mpc_sha256", "conditional_floor_equation_sha256")}
        case_summaries[case_id] = {
            "input_files": {
                str(item["model_rel"]): all_pins[str(item["model_rel"])],
                str(item["deck_rel"]): all_pins[str(item["deck_rel"])],
                str(item["audit_rel"]): all_pins[str(item["audit_rel"])],
                str(item["source_pins_rel"]): all_pins[str(item["source_pins_rel"])],
            },
            "case_id": model["case_id"],
            "physical_node_count": len(maps["physical_nodes"]),
            "physical_body_count": len(model["physical_body_nodes"]),
            "physical_c3d20_count": len(maps["body_of_element"]),
            "deck_node_coordinate_max_abs_residual_vs_model_mm": maps["actual_deck_model_coordinate_max_abs_residual_mm"],
            "ordered_property_card_sha256": property_hash,
            "ordered_property_card_counts": dict(sorted(card_counts.items())),
            "projection_rows": per_case_projection[case_id],
            "physical_body_nodal_load_map_sha256_case_specific": digest_value(model["physical_body_loads"]),
            "case_input_is_load_specific": True,
        }
        load_hashes[case_id] = case_summaries[case_id]["physical_body_nodal_load_map_sha256_case_specific"]
        if common_maps is None:
            common_maps = maps
        elif any(maps[key] != common_maps[key] for key in ("model_coordinate_hash", "deck_coordinate_hash", "c3d20_hash", "ownership_hash")):
            raise ReuseContractError(f"Source geometry/ownership is not identical across all six cases: {case_id}")
        if common_projection_payloads is None:
            common_projection_payloads = {"source_laws": source_law_hash, "permanent_mpcs": permanent_mpc_hash, "floor_mpcs": conditional_floor_hash, "floor_refs": floor_reference_hash, "projection_rows": projection["row_sha256"]}
        elif common_projection_payloads != {"source_laws": source_law_hash, "permanent_mpcs": permanent_mpc_hash, "floor_mpcs": conditional_floor_hash, "floor_refs": floor_reference_hash, "projection_rows": projection["row_sha256"]}:
            raise ReuseContractError(f"Source carrier/projection/floor mechanics differ across cases: {case_id}")

    if len(set(load_hashes.values())) != 6:
        raise ReuseContractError("Expected six distinct source gravity nodal maps; load-case identity may have collapsed")

    # The source C11 deck is independently pinned by both adapter lineages and
    # carries the same ordered property cards as every derived case deck.
    c11_deck = deck_source_data(ROOT / C11_DECK)
    if common_property_sequence != c11_deck["property_cards"]:
        raise ReuseContractError("Actual six-case property cards do not match the pinned C11 source deck")

    equality_groups = []
    labels = {
        "physical_model_node_coordinates": "model physical-node coordinates",
        "physical_deck_node_coordinates": "actual model.inp physical-node coordinates",
        "physical_c3d20_connectivity_and_elset": "actual C3D20 connectivity and ELSET mapping",
        "body_node_and_element_ownership": "physical body node and element ownership",
        "ordered_actual_property_cards": "actual ordered material/elastic/orientation/section cards",
        "body_geometry_and_material_binding": "source body geometry and material binding metadata",
        "normalized_physical_connector_projection_rows": "physical-coordinate connector rows after permanent MPC expansion",
        "permanent_mpcs_after_200_floor_pivots_removed": "permanent MPCs after excluding 200 conditional floor pivots",
        "conditional_floor_mpc_rows": "200 conditional floor MPC rows",
        "normalized_floor_reference_records_200": "200 normalized floor reference/ownership records (load corrections excluded)",
        "source_carrier_laws_and_ownership": "all source carrier laws and physical ownership metadata",
        "support_and_numerical_ground_inventory": "SPC, fixed floor endpoint, and numerical spring-ground inventory",
    }
    for key, label in labels.items():
        hashes = {per_case_component_hashes[case][key] for case in CASE_IDS}
        if len(hashes) != 1:
            raise ReuseContractError(f"Six-case identity group failed: {label}")
        equality_groups.append({"component": key, "description": label, "cases": CASE_IDS, "sha256": next(iter(hashes)), "equal_across_all_cases": True})

    cards = common_property_sequence or []
    card_counts_common = dict(sorted(Counter(card["header"][0] for card in cards).items()))
    all_model_node_counts = {case: len(cases[case]["model"]["nodes"]) for case in CASE_IDS}
    if set(all_model_node_counts.values()) != {21407}:
        raise ReuseContractError(f"Expected equal complete node maps: {all_model_node_counts}")
    contract = {
        "schema": "current_six_case_operator_reuse_contract/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "case_order": CASE_IDS,
        "input_only": True,
        "native_solve_executed": False,
        "operator_assembled": False,
        "response_forces_read": False,
        "case_passes_adopted": False,
        "source_authentication": {
            "gravity_decomposition_path": str(decomp_rel),
            "gravity_decomposition_sha256": decomposition_sha,
            "gravity_decomposition_status": decomposition["status"],
            "gravity_decomposition_verifier_sha256": all_pins[str(decomp_script_rel)],
            "floor_constraint_audit_sha256": all_pins[str(floor_audit_rel)],
            "floor_constraint_matrix_sha256": all_pins[str(floor_matrix_rel)],
            "all_case_model_hashes_match_decomposition_records": True,
            "all_declared_transitive_pins_verified": True,
        },
        "source_files_by_case": case_summaries,
        "case_specific_load_hashes": {"physical_body_load_map_sha256_by_case": load_hashes, "six_distinct_load_maps": True, "loads_were_not_included_in_identity_comparison": True},
        "actual_deck_physical_inventory": {
            "all_six_models_have_total_nodes": all_model_node_counts,
            "physical_body_nodes": 12549,
            "physical_bodies": 50,
            "physical_c3d20_elements": 1903,
            "actual_deck_vs_model_physical_coordinate_max_abs_residual_mm": max_coord_residual,
            "actual_coordinates_checked_against_model": True,
            "actual_element_connectivity_and_elset_checked_against_model": True,
            "every_physical_node_and_c3d20_has_exactly_one_body_owner": True,
            "every_c3d20_connectivity_node_is_owned_by_its_element_body": True,
        },
        "actual_ordered_property_cards": {
            "normalization": "Original deck order retained; keyword/options normalized to uppercase, comma token whitespace trimmed, data token text preserved.",
            "card_count": len(cards),
            "counts_by_keyword": card_counts_common,
            "ordered_sequence_sha256": digest_value(cards),
            "equal_across_all_six_emitted_decks": True,
            "equal_to_actual_pinned_c11_source_deck": True,
            "cards": cards,
        },
        "conditional_floor_source": floor_data,
        "all_six_source_equality_groups": equality_groups,
        "projection_summary": {
            "permanent_mpcs_in_each_case": 21798,
            "conditional_floor_mpcs_excluded_before_connector_expansion": 200,
            "bilateral_rows_per_case": 348,
            "unilateral_source_projection_rows_per_case": 1292,
            "physical_coordinate_count_per_case": 37647,
            "all_projected_connector_masters_are_unique_physical_translation_coordinates": True,
            "per_case_projection_details": per_case_projection,
            "one_identical_normalized_projection_hash_across_six_cases": len({value["row_sha256"] for value in per_case_projection.values()}) == 1,
        },
        "reuse_decision": {
            "permitted_scope": "The same source-defined unconstrained linear elastic physical K and the same verified permanent connector/projection rows can serve the six separate case-specific load maps, subject to the later pinned solver/export method and boundary/state treatment.",
            "not_yet_available": "No numerical K/H was assembled or exported by this source identity check.",
            "forbidden_inference": "Do not reuse a response force, reaction, unilateral active/contact state, floor-bearing mask, equilibrium result, demand, utilization, or pass from one case for another.",
            "case_specific_work_remains": "Apply each case's own distinct physical load map and independently resolve/check its compatible nonlinear contact and floor state and physical balance before using any response.",
        },
        "limits": [
            "Identity of the source linear elastic inputs does not establish material accuracy, delivered material properties, a physical floor, or candidate acceptance.",
            "The 200 floor tangent rows remain conditional on their separate all-bearing/reference-branch hypothesis; no state or reaction is selected here.",
            "Unilateral SPRINGA rows are common source laws but their active set and response vary by load case.",
            "The operator is not assembled, and native MATRIXSTORAGE/export availability or output mapping is not proved here.",
            "The six distinct load maps are source inputs only; this contract reports no force response or case pass.",
        ],
    }
    source_pins = {
        "schema": "current_six_case_operator_reuse_source_pins/v1",
        "producer": {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": digest_file(Path(__file__).resolve())},
        "verified_sources_sha256": dict(sorted(all_pins.items())),
        "source_pin_aliases_normalized": dict(sorted(source_pin_aliases.items())),
        "case_input_hashes": {case: {key: value for key, value in case_summaries[case]["input_files"].items()} for case in CASE_IDS},
        "normalized_identity_groups_sha256": {row["component"]: row["sha256"] for row in equality_groups},
        "ordered_property_card_sequence_sha256": digest_value(cards),
        "gravity_decomposition_sha256": decomposition_sha,
        "floor_constraint_matrix_sha256": all_pins[str(floor_matrix_rel)],
    }
    return contract, source_pins


def emit(write: bool) -> None:
    contract, pins = build_contract()
    OUT.mkdir(parents=True, exist_ok=True)
    payloads = {"identity-contract.json": contract, "source-pins.json": pins}
    if write:
        for name, value in payloads.items():
            (OUT / name).write_bytes(canonical_bytes(value))
    else:
        for name, value in payloads.items():
            path = OUT / name
            if not path.is_file() or path.read_bytes() != canonical_bytes(value):
                raise ReuseContractError(f"Stored output differs from source rebuild: {name}")
    print(json.dumps({"mode": "write" if write else "verify", "identity_contract_sha256": digest_bytes(canonical_bytes(contract)), "case_ids": CASE_IDS, "physical_nodes": contract["actual_deck_physical_inventory"]["physical_body_nodes"], "physical_c3d20_elements": contract["actual_deck_physical_inventory"]["physical_c3d20_elements"], "property_cards": contract["actual_ordered_property_cards"]["card_count"], "projection_rows": contract["projection_summary"]["bilateral_rows_per_case"] + contract["projection_summary"]["unilateral_source_projection_rows_per_case"], "equal_groups": len(contract["all_six_source_equality_groups"]), "distinct_case_load_maps": len(set(contract["case_specific_load_hashes"]["physical_body_load_map_sha256_by_case"].values()))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write == args.verify:
        parser.error("select exactly one of --write or --verify")
    emit(args.write)
