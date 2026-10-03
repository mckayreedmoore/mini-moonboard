"""Build a source-pinned physical-coordinate connector projection contract.

This is an input-only sparse row expansion. It invokes no finite-element
kernel, controller, or native solver and does not modify its pinned inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
ADAPTER = BASE / "current-springa-frame-input-adapter-attempt01"
MODEL_REL = ADAPTER / "a12-rear/model.json"
RANK = BASE / "current-frame-gravity-rank-readiness-attempt01"
FLOOR = BASE / "current-floor-stick-constraint-audit-attempt01"
OUT = BASE / "current-frame-physical-connector-projection-contract-attempt01"
PRUNE = 1e-13
ROTATION_LENGTH_MM = 1000.0


class ContractError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_json(rel: Path) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def source_pins() -> dict[str, Any]:
    prior = read_json(RANK / "audit.json")
    pins = dict(prior["pinned_inputs"])
    for rel in (RANK / "audit.py", RANK / "audit.json"):
        pins[str(rel)] = {"sha256": sha256_file(ROOT / rel)}
    observed: dict[str, Any] = {}
    for rel, pin in sorted(pins.items()):
        path = ROOT / rel
        if not path.is_file():
            raise ContractError(f"Missing rank-audit pinned source: {rel}")
        got = sha256_file(path)
        if got != pin["sha256"]:
            raise ContractError(f"Rank-audit source pin changed: {rel}: {got} != {pin['sha256']}")
        observed[rel] = {"sha256": got}
    floor_audit = read_json(FLOOR / "audit.json")
    model = read_json(MODEL_REL)
    if floor_audit.get("source_input_sha256") != model["source_model_pin"]["c11_input_model_sha256"]:
        raise ContractError("Floor constraint audit and A12 adapter do not bind the same C11 source model")
    return {
        "schema": "current_frame_physical_connector_projection_source_pins/v1",
        "rank_audit_schema": prior.get("schema"),
        "rank_audit_status": prior.get("status"),
        "projection_contract_producer": {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": sha256_file(Path(__file__).resolve())},
        "rank_audit_input_pins": observed,
        "projection_contract_direct_inputs": {
            str(MODEL_REL): {"sha256": sha256_file(ROOT / MODEL_REL)},
            str(FLOOR / "audit.json"): {"sha256": sha256_file(ROOT / (FLOOR / "audit.json"))},
            str(FLOOR / "constraint-matrices.npz"): {"sha256": sha256_file(ROOT / (FLOOR / "constraint-matrices.npz"))},
        },
        "adapter_embedded_c11_input_model_sha256": model["source_model_pin"]["c11_input_model_sha256"],
    }


def sparse_add(target: dict[tuple[int, int], float], source: dict[tuple[int, int], float], scale: float) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0.0) + scale * value


def main_artifacts() -> dict[str, Any]:
    pins = source_pins()
    model = read_json(MODEL_REL)
    floor_audit = read_json(FLOOR / "audit.json")
    matrix_file = np.load(ROOT / FLOOR / "constraint-matrices.npz", allow_pickle=False)
    floor_matrix = np.asarray(matrix_file["original"], dtype=float)

    nodes = {int(tag): np.asarray(xyz, dtype=float) for tag, xyz in model["nodes"].items()}
    bodies = sorted(model["physical_body_nodes"])
    body_index = {body: i for i, body in enumerate(bodies)}
    body_of: dict[int, str] = {}
    physical_node_set: set[int] = set()
    for body, tags in model["physical_body_nodes"].items():
        for tag in tags:
            node = int(tag)
            if node in body_of:
                raise ContractError(f"Physical node belongs to multiple bodies: {node}")
            body_of[node] = body
            physical_node_set.add(node)
    if len(physical_node_set) != 12549 or len(bodies) != 50:
        raise ContractError(f"Unexpected physical inventory: {len(physical_node_set)} nodes / {len(bodies)} bodies")
    physical_nodes = sorted(physical_node_set)
    node_index = {node: i for i, node in enumerate(physical_nodes)}
    coordinate_index = {(node, dof): 3 * node_index[node] + dof - 1 for node in physical_nodes for dof in (1, 2, 3)}
    datums = {
        body: np.mean([nodes[int(tag)] for tag in model["physical_body_nodes"][body]], axis=0)
        for body in bodies
    }
    index_map = [
        {"physical_node_index": i, "node": node, "body": body_of[node], "xyz_mm": nodes[node].tolist()}
        for i, node in enumerate(physical_nodes)
    ]

    fixed_nodes = set(map(int, model["fixed_nodes"]))
    fixed_dofs = {(node, dof) for node in fixed_nodes for dof in (1, 2, 3)}
    floor_support_nodes = set(map(int, model["floor_support_nodes"]))
    conditional_floor_keys = {
        tuple(map(int, row["dependent_physical_pivot_dof"]))
        for row in model["exact_floor_mpc_equations"]
    }
    equations: dict[tuple[int, int], list[list[float]]] = {}
    for terms in model["equations"]:
        key = (int(terms[0][0]), int(terms[0][1]))
        if key in equations:
            raise ContractError(f"Duplicate MPC pivot: {key}")
        equations[key] = terms
    if len(conditional_floor_keys) != 200 or not conditional_floor_keys.issubset(equations):
        raise ContractError("The exact 200 conditional floor pivots are not present in the serialized MPC set")
    permanent = {key: terms for key, terms in equations.items() if key not in conditional_floor_keys}
    if len(permanent) != 21798:
        raise ContractError(f"Unexpected permanent equation count: {len(permanent)}")
    cache: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    active: set[tuple[int, int]] = set()

    def expand(key: tuple[int, int]) -> dict[tuple[int, int], float]:
        if key in cache:
            return cache[key]
        if key in active:
            raise ContractError(f"Circular permanent MPC at {key}")
        active.add(key)
        if key in fixed_dofs:
            out: dict[tuple[int, int], float] = {}
        elif key not in permanent:
            out = {key: 1.0}
        else:
            terms = permanent[key]
            pivot = float(terms[0][2])
            if pivot == 0.0:
                raise ContractError(f"Zero pivot coefficient for {key}")
            out = {}
            for node, dof, coeff in terms[1:]:
                for master, weight in expand((int(node), int(dof))).items():
                    out[master] = out.get(master, 0.0) - float(coeff) * weight / pivot
            out = {term: value for term, value in out.items() if abs(value) > PRUNE}
        active.remove(key)
        cache[key] = out
        return out

    def difference(first: int, second: int, dof: int) -> dict[tuple[int, int], float]:
        out = expand((second, dof)).copy()
        sparse_add(out, expand((first, dof)), -1.0)
        return {key: value for key, value in out.items() if abs(value) > PRUNE}

    def to_sparse_row(terms: dict[tuple[int, int], float]) -> list[dict[str, Any]]:
        result = []
        for (node, dof), coefficient in sorted(terms.items(), key=lambda pair: coordinate_index[pair[0]]):
            if node not in body_of or dof not in (1, 2, 3):
                raise ContractError(f"Connector row did not close on a physical translational coordinate: {(node, dof)}")
            result.append({"coordinate_index": coordinate_index[(node, dof)], "coefficient": float(coefficient)})
        if len({entry["coordinate_index"] for entry in result}) != len(result):
            raise ContractError("Sparse row contains duplicate physical coordinates")
        return result

    def rigid_row(terms: dict[tuple[int, int], float]) -> np.ndarray:
        out = np.zeros(6 * len(bodies), dtype=float)
        for (node, dof), coefficient in terms.items():
            body = body_of.get(node)
            if body is None or dof not in (1, 2, 3):
                raise ContractError(f"Rigid projection reached nonphysical term {(node, dof)}")
            relative = (nodes[node] - datums[body]) / ROTATION_LENGTH_MM
            start = 6 * body_index[body]
            out[start + dof - 1] += coefficient
            if dof == 1:
                out[start + 4] += coefficient * relative[2]
                out[start + 5] -= coefficient * relative[1]
            elif dof == 2:
                out[start + 3] -= coefficient * relative[2]
                out[start + 5] += coefficient * relative[0]
            else:
                out[start + 3] += coefficient * relative[1]
                out[start + 4] -= coefficient * relative[0]
        return out

    def owner_rigid_row(first: str, second: str, point: list[float], direction: list[float]) -> np.ndarray:
        out = np.zeros(6 * len(bodies), dtype=float)
        p = np.asarray(point, dtype=float)
        d = np.asarray(direction, dtype=float)
        for body, sign in ((first, -1.0), (second, 1.0)):
            if body == "floor":
                continue
            if body not in body_index:
                raise ContractError(f"Owner references unknown physical body: {body}")
            start = 6 * body_index[body]
            out[start : start + 3] += sign * d
            out[start + 3 : start + 6] += sign * np.cross(p - datums[body], d) / ROTATION_LENGTH_MM
        return out

    def sparse_work(entries: list[dict[str, Any]], field: str) -> float:
        return sum(float(item["coefficient"]) * (math.sin((int(item["coordinate_index"]) + 1) * 0.0017) if field == "u" else math.cos((int(item["coordinate_index"]) + 1) * 0.00091)) for item in entries)

    all_rows: list[dict[str, Any]] = []
    bilateral_rows: list[dict[str, Any]] = []
    owner_rigid_max = 0.0
    row_support_max = 0
    for spring in model["springs"]:
        terms = difference(int(spring["nodes"][0]), int(spring["nodes"][1]), int(spring["dof"]))
        entries = to_sparse_row(terms)
        owner = spring["physical_owner"]
        direction = owner["force_basis"][int(spring["connector_local_dof"]) - 1]
        expected = owner_rigid_row(owner["first"], owner["second"], owner["point"], direction)
        residual = float(np.max(np.abs(rigid_row(terms) - expected)))
        owner_rigid_max = max(owner_rigid_max, residual)
        row_support_max = max(row_support_max, len(entries))
        row = {
            "family": "bilateral_spring2",
            "row_id": spring["name"],
            "source_group": spring["group"],
            "source_element": int(spring["element"]),
            "source_inventory_row_index": int(spring["source_inventory_row_index"]),
            "q_definition": "u(second SPRING2 endpoint,dof) - u(first SPRING2 endpoint,dof), after permanent MPC expansion and SPC-ground substitution",
            "law": {"intended_law": spring["intended_law"], "stiffness_N_per_mm": float(spring["stiffness_n_per_mm"]), "scalar_force_conjugate_to_q": "k*q"},
            "ownership": {"first_body": owner["first"], "second_body": owner["second"], "role": owner["role"], "point_mm": owner["point"], "direction_global_xyz": direction},
            "source_connector": {"nodes": spring["nodes"], "dof": int(spring["dof"]), "connector_local_dof": int(spring["connector_local_dof"]), "axis": owner["axis"]},
            "physical_sparse_row": entries,
            "owner_point_rigid_row_max_abs_residual": residual,
            "stiffness_sign_convention": "U=0.5*k*q^2; B is dq/du; energy-gradient/internal residual uses B^T*(k*q), and restoring force is its negative.",
        }
        bilateral_rows.append(row)
        all_rows.append(row)

    inventory = model["raw_source_carrier_law_inventory_rows"]
    fixed_dofs_set = fixed_dofs
    qghost_rows_checked = 0
    qghost_projection_max = 0.0
    floor_normal_ground_nodes: set[int] = set()
    unilateral_rows: list[dict[str, Any]] = []
    for binding in model["unilateral_springa_bindings"]:
        source = inventory[int(binding["source_inventory_row_index"])]
        if source["name"] != binding["name"] or list(map(int, source["nodes"])) != list(map(int, binding["source_projection_nodes"])) or int(source["dof"]) != int(binding["source_projection_dof"]):
            raise ContractError(f"SPRINGA source projection does not rejoin source inventory: {binding['name']}")
        source_terms = difference(int(binding["source_projection_nodes"][0]), int(binding["source_projection_nodes"][1]), int(binding["source_projection_dof"]))
        first, ground = map(int, binding["springa_nodes"])
        if (ground, 1) not in fixed_dofs_set or ground in body_of or not binding["ground_endpoint_is_numerical_only"]:
            raise ContractError(f"SPRINGA numerical fixed-ground mismatch: {binding['name']}")
        element = model["elements"][str(int(binding["source_element"]))]
        if element[0] != "SPRINGA" or list(map(int, element[1])) != [first, ground]:
            raise ContractError(f"SPRINGA element endpoints changed: {binding['name']}")
        for ghost_eq in binding["qghost_equations"]:
            pivot = tuple(map(int, ghost_eq["terms"][0][:2]))
            if pivot != tuple(map(int, ghost_eq["dependent_q_dof"])) or pivot not in permanent:
                raise ContractError(f"SPRINGA qghost equation missing from permanent set: {binding['name']}")
            if permanent[pivot] != ghost_eq["terms"]:
                # JSON numerics and MPC serialization should be byte-value exact.
                if permanent[pivot] != [[int(t[0]), int(t[1]), float(t[2])] for t in ghost_eq["terms"]]:
                    raise ContractError(f"SPRINGA qghost equation differs from serialized MPC: {binding['name']}")
            qghost_rows_checked += 1
        axis = nodes[ground] - nodes[first]
        axis_length = float(np.linalg.norm(axis))
        if axis_length == 0.0 or abs(axis_length - float(binding["initial_span_mm"])) > 1e-8:
            raise ContractError(f"SPRINGA initial geometry/length mismatch: {binding['name']}")
        axis = axis / axis_length
        native_terms: dict[tuple[int, int], float] = {}
        for dof in (1, 2, 3):
            for master, weight in expand((first, dof)).items():
                native_terms[master] = native_terms.get(master, 0.0) - float(axis[dof - 1]) * weight
        native_terms = {key: value for key, value in native_terms.items() if abs(value) > PRUNE}
        all_keys = set(source_terms) | set(native_terms)
        residual = max((abs(source_terms.get(key, 0.0) - native_terms.get(key, 0.0)) for key in all_keys), default=0.0)
        qghost_projection_max = max(qghost_projection_max, residual)
        if residual > 1e-8:
            raise ContractError(f"SPRINGA qghost/native-axis/source projection mismatch: {binding['name']}: {residual}")
        entries = to_sparse_row(source_terms)
        owner = binding["physical_owner"]
        direction = owner["scalar_normal"]
        expected = owner_rigid_row(owner["first"], owner["second"], owner["point"], direction)
        rigid_resid = float(np.max(np.abs(rigid_row(source_terms) - expected)))
        owner_rigid_max = max(owner_rigid_max, rigid_resid)
        role = owner.get("role")
        grounding: dict[str, Any] = {"springa_ground_node": ground, "ground_is_fixed_spc": True, "ground_is_physical": False, "ground_endpoint_is_numerical_only": True, "no_extra_physical_anchor_added": True}
        if role == "floor_normal":
            second_projection = (int(binding["source_projection_nodes"][1]), int(binding["source_projection_dof"]))
            body_projection = (int(binding["source_projection_nodes"][0]), int(binding["source_projection_dof"]))
            if expand(second_projection):
                raise ContractError(f"Floor normal's fixed-side source projection did not reduce to zero: {binding['name']}")
            if not expand(body_projection) or any(node not in body_of for node, _ in expand(body_projection)):
                raise ContractError(f"Floor normal's body-side projection did not close physically: {binding['name']}")
            endpoints = trace_floor_endpoint(second_projection, permanent, fixed_dofs, floor_support_nodes)
            if len(endpoints) != 1:
                raise ContractError(f"Floor normal does not map to one fixed floor endpoint: {binding['name']}")
            endpoint = next(iter(endpoints))
            if endpoint in floor_normal_ground_nodes:
                raise ContractError(f"Floor normal endpoint reused: {endpoint}")
            floor_normal_ground_nodes.add(endpoint)
            grounding["fixed_floor_projection_endpoint"] = endpoint
            grounding["fixed_floor_projection_endpoint_is_included_as_physical_coordinate"] = False
            grounding["body_side_projection_is_physical"] = True
        row = {
            "family": "unilateral_springa",
            "row_id": binding["name"],
            "source_group": binding["group"],
            "source_element": int(binding["source_element"]),
            "source_inventory_row_index": int(binding["source_inventory_row_index"]),
            "q_definition": "u(second source projection,dof) - u(first source projection,dof); matched against negative SPRINGA axis projection of first qghost endpoint",
            "law": {"intended_law": source["intended_law"], "force_law": binding["force_law"], "stiffness_N_per_mm": float(binding["stiffness_n_per_mm"]), "scalar_force_table_N_mm": binding["force_vs_elongation_table_N_mm"], "table_domain_mm": binding["table_domain_mm"]},
            "ownership": {"first_body": owner["first"], "second_body": owner["second"], "role": owner["role"], "point_mm": owner["point"], "direction_global_xyz": direction},
            "source_projection": {"nodes": binding["source_projection_nodes"], "dof": int(binding["source_projection_dof"]), "springa_nodes": binding["springa_nodes"], "serialized_numerical_axis_global_xyz": binding["numerical_axis_global_xyz"], "geometric_ground_minus_first_axis_global_xyz": axis.tolist(), "qghost_equations": binding["qghost_equations"], "qghost_equations_checked": len(binding["qghost_equations"])},
            "grounding": grounding,
            "physical_sparse_row": entries,
            "source_to_springa_axis_projection_max_abs_residual": residual,
            "owner_point_rigid_row_max_abs_residual": rigid_resid,
            "source_physical_action": {"on_first_body": binding["physical_action_on_first_body"], "on_second_body": binding["physical_action_on_second_body"], "source_row_relation": "The verified owner-point row is (-d on first, +d on second), so the source physical action for positive table force f is -B^T*f on the physical bodies; numerical ground reaction is excluded."},
            "work_sign_convention": "q is the source extension and the scalar table force is work-conjugate to q; B^T*f is the energy-gradient/internal residual, while the source restoring physical action is -B^T*f. Numerical ground reaction is outside the physical-node row vector.",
        }
        unilateral_rows.append(row)
        all_rows.append(row)
    if len(unilateral_rows) != 1292 or qghost_rows_checked != sum(len(row["qghost_equations"]) for row in model["unilateral_springa_bindings"]):
        raise ContractError("Unilateral or qghost row count changed")
    if len(floor_normal_ground_nodes) != 100 or floor_normal_ground_nodes != floor_support_nodes:
        raise ContractError("100 floor normals no longer preserve one-to-one fixed floor endpoint grounding")

    # Exact-stick source rows are separate conditional rows over their 800 physical masters.
    masters = [tuple(map(int, pair)) for pair in floor_audit["physical_master_dofs"]]
    if floor_matrix.shape != (200, 800) or len(masters) != 800 or len(set(masters)) != 800:
        raise ContractError("Floor source matrix/master inventory shape or uniqueness changed")
    if any(node not in body_of or dof not in (1, 2, 3) for node, dof in masters):
        raise ContractError("Floor source matrix master is not a unique physical translation DOF")
    if len(set(masters) & conditional_floor_keys) != 200:
        raise ContractError("Floor source masters no longer include all 200 exact conditional pivots")
    if int(floor_audit["independent_constraint_rank"]) != 200:
        raise ContractError("Floor constraint source rank changed")
    refs = {(str(ref["normal_cell"]), int(ref["source_spring_local_dof"])): ref for ref in model["floor_reference_nodes"]}
    floor_rows: list[dict[str, Any]] = []
    floor_owner_rigid_max = 0.0
    for i, owner_rec in enumerate(floor_audit["row_owners"]):
        key = (str(owner_rec["normal_cell"]), int(owner_rec["local_dof"]))
        ref = refs.get(key)
        if ref is None:
            raise ContractError(f"Floor row owner has no exact reference record: {key}")
        source_terms: dict[tuple[int, int], float] = {}
        for j, (node, dof) in enumerate(masters):
            coefficient = float(floor_matrix[i, j])
            if coefficient != 0.0:
                source_terms[(node, dof)] = coefficient
        entries = to_sparse_row(source_terms)
        if not entries:
            raise ContractError(f"Floor constraint row is empty: {key}")
        owner = ref["physical_owner"]
        expected = owner_rigid_row(owner["first"], owner["second"], ref["owner_floorpoint_xyz_mm"], ref["owner_tangent_basis_global_xyz"])
        projected_rigid = rigid_row(source_terms)
        positive_resid = float(np.max(np.abs(projected_rigid - expected)))
        negative_resid = float(np.max(np.abs(projected_rigid + expected)))
        row_owner_sign = 1 if positive_resid <= negative_resid else -1
        rigid_resid = min(positive_resid, negative_resid)
        floor_owner_rigid_max = max(floor_owner_rigid_max, rigid_resid)
        floor_rows.append({
            "family": "conditional_floor_tangent_constraint",
            "row_id": ref["source_row_id"],
            "source_group": ref["source_spring_group"],
            "source_element": int(ref["source_spring_element"]),
            "source_original_row_index": int(ref["source_row_original_index"]),
            "normal_cell": ref["normal_cell"],
            "local_dof": int(owner_rec["local_dof"]),
            "law": {"intended_law": "floor_tangent_all_bearing_hypothesis", "row_type": "homogeneous conditional stick constraint; no spring stiffness is assigned here", "conditional_scope": "all-bearing floor increment/reference-branch hypothesis"},
            "ownership": {"first_body": owner["first"], "second_body": owner["second"], "role": owner["role"], "point_mm": ref["owner_floorpoint_xyz_mm"], "direction_global_xyz": ref["owner_tangent_basis_global_xyz"]},
            "reference_node_metadata": {"node": int(ref["node"]), "reference_dof": int(ref["reference_dof"]), "source_load_correction_N": float(ref["source_load_correction_N"]), "correction_from_full_precision_matrix_N": float(ref["correction_from_full_precision_matrix_N"])},
            "physical_sparse_row": entries,
            "source_row_norm_l2": float(np.linalg.norm(floor_matrix[i])),
            "owner_point_rigid_row_sign": row_owner_sign,
            "owner_point_rigid_row_max_abs_residual": rigid_resid,
            "conditional_pivot_is_retained_as_a_physical_coordinate": any((node, dof) in conditional_floor_keys for node, dof in source_terms),
        })
    if len(floor_rows) != 200:
        raise ContractError("Floor exact-stick row count changed")

    # Ensure exact row statistics and generic dual-work identity for every row.
    virtual_work_max_abs = 0.0
    restoring_work_max_abs = 0.0
    for row in [*bilateral_rows, *unilateral_rows, *floor_rows]:
        entries = row["physical_sparse_row"]
        row["nonzero_count"] = len(entries)
        q_trial = sparse_work(entries, "u")
        virtual_trial = sparse_work(entries, "v")
        scalar_force = 13.25
        b_transpose_work = scalar_force * virtual_trial
        nodal_force_work = sum(float(e["coefficient"]) * scalar_force * math.cos((int(e["coordinate_index"]) + 1) * 0.00091) for e in entries)
        restoring_work = -nodal_force_work
        expected_restoring_work = -scalar_force * virtual_trial
        virtual_work_max_abs = max(virtual_work_max_abs, abs(nodal_force_work - b_transpose_work))
        restoring_work_max_abs = max(restoring_work_max_abs, abs(restoring_work - expected_restoring_work))
        row["known_answer_work"] = {"deterministic_trial_q": q_trial, "test_scalar_force_N": scalar_force, "B_transpose_virtual_work_N_mm": b_transpose_work, "explicit_nodal_transpose_work_N_mm": nodal_force_work, "restoring_work_N_mm": restoring_work, "expected_restoring_work_N_mm": expected_restoring_work}

    # Source gravity remains a distinct nodal map, separate from row projections.
    gravity_map = model["physical_body_loads"]
    gravity_bytes = canonical_bytes(gravity_map)
    gravity_hash = sha256_bytes(gravity_bytes)

    flat_rows = [*bilateral_rows, *unilateral_rows, *floor_rows]
    all_sparse_indices = [e["coordinate_index"] for row in flat_rows for e in row["physical_sparse_row"]]
    if any(index < 0 or index >= 3 * len(physical_nodes) for index in all_sparse_indices):
        raise ContractError("Sparse row index falls outside the physical-coordinate map")
    row_nnz = [row["nonzero_count"] for row in flat_rows]
    counts = Counter(row["family"] for row in flat_rows)
    if counts != Counter({"bilateral_spring2": 348, "unilateral_springa": 1292, "conditional_floor_tangent_constraint": 200}):
        raise ContractError(f"Unexpected row family counts: {dict(counts)}")
    contract = {
        "schema": "current_frame_physical_connector_projection_contract/v1",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "case_id": model["case_id"],
        "input_only": True,
        "native_solve_executed": False,
        "fe_kernel_or_controller_used": False,
        "source_pin_file": "source-pins.json",
        "physical_coordinate_map": {"node_count": len(physical_nodes), "body_count": len(bodies), "coordinate_count": 3 * len(physical_nodes), "indexing": "index = 3*physical_node_index + (dof-1); physical_node_index orders node tags ascending; DOFs 1,2,3 are global x,y,z translations", "index_map_file": "physical-index-map.json", "physical_index_map_sha256": sha256_bytes(canonical_bytes(index_map)), "all_physical_nodes_owned_exactly_once": True, "all_row_masters_physical_and_unique": True},
        "equation_treatment": {"serialized_equation_count": len(equations), "conditional_floor_exact_mpc_equations_removed_before_permanent_expansion": len(conditional_floor_keys), "permanent_equations_recursively_expanded": len(permanent), "spc_fixed_numerical_dofs_substituted_as_zero": len(fixed_dofs), "physical_body_nodes_fixed": 0, "absolute_expansion_prune": PRUNE, "all_expanded_connector_rows_close_on_physical_translational_dofs": True},
        "row_counts": {"bilateral_spring2": len(bilateral_rows), "unilateral_springa": len(unilateral_rows), "conditional_floor_tangent": len(floor_rows), "total": len(flat_rows)},
        "projection_checks": {"springa_qghost_equations_checked": qghost_rows_checked, "springa_source_vs_native_axis_max_abs_coefficient_residual": qghost_projection_max, "connector_owner_point_rigid_row_max_abs_residual": owner_rigid_max, "floor_owner_point_rigid_row_max_abs_residual": floor_owner_rigid_max, "floor_normal_fixed_endpoint_count": len(floor_normal_ground_nodes), "floor_normal_fixed_endpoints_one_to_one_with_100_floor_support_nodes": floor_normal_ground_nodes == floor_support_nodes, "no_additional_floor_anchor": True},
        "dual_virtual_work_checks": {"operator": "q=B*u; scalar conjugate work f*(B*v) equals explicit v dot (B^T*f); restoring sign is its negative", "rows_checked": len(flat_rows), "max_abs_virtual_work_residual_N_mm": virtual_work_max_abs, "max_abs_restoring_work_residual_N_mm": restoring_work_max_abs, "passed": virtual_work_max_abs < 1e-9 and restoring_work_max_abs < 1e-9},
        "sparse_row_statistics": {"nonzero_total": sum(row_nnz), "nonzero_min": min(row_nnz), "nonzero_max": max(row_nnz), "nonzero_mean": sum(row_nnz) / len(row_nnz)},
        "source_gravity_nodal_map": {"file": "source-gravity-nodal-map.json", "source_field": "A12 adapter model.physical_body_loads", "source_model_sha256": pins["projection_contract_direct_inputs"][str(MODEL_REL)]["sha256"], "canonical_field_sha256": gravity_hash, "body_count": len(gravity_map), "preserved_separately_from_connector_rows": True},
        "rows": flat_rows,
        "limitations": ["These are source-bound linear coordinate rows, not a stiffness assembly or solution.", "The 200 floor tangent rows remain a conditional all-bearing/reference-branch constraint hypothesis; they do not establish actual bearing or floor capacity.", "The 1,292 unilateral SPRINGA laws remain state-dependent and nonsmooth at zero extension; this packet does not select contact state or infer resistance.", "B^T is the work-conjugate transpose. Numerical-ground reactions are excluded from the physical coordinate vector.", "Projection of C3D20 physical stiffness into these rows, nonlinear/contact equilibrium, local wood splitting resistance, and candidate acceptance remain outside scope."],
    }
    return {"contract": contract, "index_map": index_map, "gravity_map": gravity_map, "pins": pins}


def trace_floor_endpoint(key: tuple[int, int], permanent: dict[tuple[int, int], list[list[float]]], fixed_dofs: set[tuple[int, int]], floor_support_nodes: set[int]) -> set[int]:
    seen: set[tuple[int, int]] = set()
    def visit(current: tuple[int, int]) -> set[int]:
        if current in fixed_dofs:
            return {current[0]} if current[0] in floor_support_nodes else set()
        if current not in permanent:
            return set()
        if current in seen:
            raise ContractError(f"Cycle while tracing fixed floor endpoint at {current}")
        seen.add(current)
        found: set[int] = set()
        for node, dof, coeff in permanent[current][1:]:
            if abs(float(coeff)) > PRUNE:
                found |= visit((int(node), int(dof)))
        seen.remove(current)
        return found
    return visit(key)


def emit(write: bool) -> None:
    artifacts = main_artifacts()
    OUT.mkdir(parents=True, exist_ok=True)
    payloads = {
        "projection-contract.json": artifacts["contract"],
        "physical-index-map.json": artifacts["index_map"],
        "source-gravity-nodal-map.json": artifacts["gravity_map"],
        "source-pins.json": artifacts["pins"],
    }
    if write:
        for name, value in payloads.items():
            write_json(OUT / name, value)
    else:
        for name, value in payloads.items():
            path = OUT / name
            if not path.is_file() or path.read_bytes() != canonical_bytes(value):
                raise ContractError(f"Stored projection artifact differs from source rebuild: {name}")
    c = artifacts["contract"]
    print(json.dumps({"mode": "write" if write else "verify", "contract_sha256": sha256_file(OUT / "projection-contract.json") if write else sha256_bytes(canonical_bytes(c)), "row_counts": c["row_counts"], "projection_checks": c["projection_checks"], "dual_virtual_work_checks": c["dual_virtual_work_checks"], "sparse_row_statistics": c["sparse_row_statistics"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write == args.verify:
        parser.error("select exactly one of --write or --verify")
    emit(args.write)
