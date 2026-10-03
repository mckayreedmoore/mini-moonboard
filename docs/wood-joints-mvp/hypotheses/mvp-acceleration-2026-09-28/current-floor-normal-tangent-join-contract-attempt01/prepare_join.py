"""Verify and serialize the source-bound floor normal/tangent row joins.

This is an input/projection audit only. It does not assemble a frame operator,
select contact states, search contact events, or run a solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = BASE / "current-floor-normal-tangent-join-contract-attempt01"
CONTRACT_DIR = BASE / "current-frame-physical-connector-projection-contract-attempt01"
ADAPTER_DIR = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear"
FLOOR_DIR = BASE / "current-floor-stick-constraint-audit-attempt01"
SELECTOR_DIR = BASE / "current-coupled-indicator-selector-fixture-attempt01"
OUTPUT = HERE / "join-contract.json"
TOL = 1e-14


class JoinError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_json(rel: Path) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def verify_pins() -> dict[str, str]:
    pin_rel = HERE / "source-pins.json"
    pin_file = read_json(pin_rel)
    observed: dict[str, str] = {}
    for entry in pin_file["files"]:
        rel = Path(entry["path"])
        path = ROOT / rel
        if not path.is_file():
            raise JoinError(f"Missing pinned input: {rel}")
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            raise JoinError(f"Pinned input changed: {rel}: {actual} != {entry['sha256']}")
        observed[str(rel)] = actual
    return observed


def row_vector(row: dict[str, Any], size: int) -> dict[int, float]:
    terms: dict[int, float] = {}
    for item in row["physical_sparse_row"]:
        coordinate = int(item["coordinate_index"])
        if coordinate < 0 or coordinate >= size or coordinate in terms:
            raise JoinError(f"Bad/duplicate projected coordinate in {row['row_id']}: {coordinate}")
        terms[coordinate] = float(item["coefficient"])
    return terms


def main_artifacts() -> dict[str, Any]:
    pins = verify_pins()
    contract = read_json(CONTRACT_DIR / "projection-contract.json")
    index_map = read_json(CONTRACT_DIR / "physical-index-map.json")
    model = read_json(ADAPTER_DIR / "model.json")
    floor_audit = read_json(FLOOR_DIR / "audit.json")
    selector_answer = read_json(SELECTOR_DIR / "known-answer.json")
    matrix_path = ROOT / FLOOR_DIR / "constraint-matrices.npz"
    with np.load(matrix_path, allow_pickle=False) as archive:
        original = np.asarray(archive["original"], dtype=np.float64)

    physical_nodes = {int(node) for values in model["physical_body_nodes"].values() for node in values}
    if sum(len(values) for values in model["physical_body_nodes"].values()) != len(physical_nodes):
        raise JoinError("A physical node is assigned to more than one body")
    bodies = sorted(model["physical_body_nodes"])
    if len(bodies) != 50 or len(physical_nodes) != 12549 or len(index_map) != 12549:
        raise JoinError("The bound adapter/index map does not contain the expected 50 bodies and 12,549 physical nodes")
    physical_index = {int(item["node"]): int(item["physical_node_index"]) for item in index_map}
    if set(physical_index) != physical_nodes or sorted(physical_index.values()) != list(range(12549)):
        raise JoinError("Physical node/index bijection is incomplete or inconsistent")
    coordinate_count = 3 * len(physical_nodes)

    row_positions = {id(row): index for index, row in enumerate(contract["rows"])}
    normal_rows = [
        row for row in contract["rows"]
        if row["family"] == "unilateral_springa" and row.get("ownership", {}).get("role") == "floor_normal"
    ]
    tangent_rows = [row for row in contract["rows"] if row["family"] == "conditional_floor_tangent_constraint"]
    if len(contract["rows"]) != 1840 or len({row["row_id"] for row in contract["rows"]}) != 1666:
        raise JoinError("Projection-contract row inventory differs from the pinned 1,840/1,666 record")
    if len(normal_rows) != 100 or len(tangent_rows) != 200:
        raise JoinError(f"Expected 100 normal and 200 tangent rows; got {len(normal_rows)} and {len(tangent_rows)}")
    if [row_positions[id(row)] for row in normal_rows] != list(range(1370, 1470)):
        raise JoinError("Floor-normal B row positions changed")
    if [row_positions[id(row)] for row in tangent_rows] != list(range(1640, 1840)):
        raise JoinError("Conditional tangent B row positions changed")

    normal_by_cell = {row["row_id"]: row for row in normal_rows}
    if len(normal_by_cell) != 100:
        raise JoinError("Normal floor-cell identifiers are not unique")
    normal_bindings = {
        row["name"]: row for row in model["unilateral_springa_bindings"]
        if row.get("physical_owner", {}).get("role") == "floor_normal"
    }
    contact_owners = {
        row["name"]: row for row in model["contact_cell_ownership"] if row.get("kind") == "floor_normal"
    }
    ref_map = {row["source_row_id"]: row for row in model["floor_reference_nodes_and_load_map"]}
    if len(normal_bindings) != 100 or len(contact_owners) != 100 or len(ref_map) != 200:
        raise JoinError("Adapter floor-normal or reference inventory has changed")

    if original.shape != (200, 800):
        raise JoinError(f"Expected original floor matrix shape (200, 800), got {original.shape}")
    if int(floor_audit["independent_constraint_rank"]) != 200 or int(floor_audit["physical_master_dof_count"]) != 800:
        raise JoinError("Pinned floor audit rank/master inventory differs from the source contract")
    if len(floor_audit["row_owners"]) != 200 or len(floor_audit["physical_master_dofs"]) != 800:
        raise JoinError("Pinned floor audit row-owner/master map has unexpected dimensions")
    selector_results = selector_answer.get("results", [])
    if selector_answer.get("status") != "ALL_TINY_FIXTURES_REPLAYED" or len(selector_results) != 8:
        raise JoinError("Pinned coupled-selector known answer does not contain its eight completed cases")
    if not all(item.get("all_binary_masks_proven_exhausted") for item in selector_results):
        raise JoinError("A pinned tiny-selector case lacks exhaustive mask completion")
    selector_by_id = {item["id"]: item for item in selector_results}
    expected_selector_classes = {
        "one_cell_zero_force_event_boundary": "AMBIGUOUS_ZERO_BOUNDARY_MASKS",
        "one_cell_nonzero_episode_reference_held": "ONE_ADMISSIBLE_MASK",
        "one_cell_fixed_reference_no_admissible_state": "NO_ADMISSIBLE_STATE",
        "one_cell_fixed_reference_two_admissible_masks": "MULTIPLE_ADMISSIBLE_MASKS",
    }
    for case_id, classification in expected_selector_classes.items():
        if selector_by_id.get(case_id, {}).get("classification") != classification:
            raise JoinError(f"Pinned coupled-selector result changed for {case_id}")
    two_cell_selector_cases = [item for item in selector_results if item["id"].startswith("two_cell_")]
    if len(two_cell_selector_cases) != 4 or any(item["classification"] != "ONE_ADMISSIBLE_MASK" for item in two_cell_selector_cases):
        raise JoinError("Pinned coupled-selector two-cell stage oracles changed")

    source_matrix_row: dict[tuple[str, int], int] = {}
    for index, owner in enumerate(floor_audit["row_owners"]):
        key = (owner["normal_cell"], int(owner["local_dof"]))
        if key in source_matrix_row:
            raise JoinError(f"Duplicate exact source row owner: {key}")
        source_matrix_row[key] = index

    # The original floor matrix columns are physical (node,dof) masters. Build
    # their coordinate indices once, then compare all 200 projected rows.
    master_coordinate_indices: list[int] = []
    for node, dof in floor_audit["physical_master_dofs"]:
        node, dof = int(node), int(dof)
        if node not in physical_index or dof not in (1, 2, 3):
            raise JoinError(f"Floor matrix master is not a physical translational coordinate: {(node, dof)}")
        master_coordinate_indices.append(3 * physical_index[node] + dof - 1)

    tangents_by_cell: dict[str, list[dict[str, Any]]] = {cell: [] for cell in normal_by_cell}
    source_rows_seen: set[int] = set()
    reference_nodes_seen: set[tuple[int, int]] = set()
    max_matrix_residual = 0.0
    max_owner_rigid_residual = 0.0
    sign_counts: Counter[int] = Counter()
    local_dof_counts: Counter[int] = Counter()
    floor_tangent_groups: set[str] = set()

    for row in tangent_rows:
        cell = row["normal_cell"]
        local_dof = int(row["local_dof"])
        key = (cell, local_dof)
        if cell not in tangents_by_cell or local_dof not in (2, 3):
            raise JoinError(f"Unknown floor cell/local tangent dof: {key}")
        expected_matrix_index = source_matrix_row.get(key)
        actual_matrix_index = int(row["source_original_row_index"])
        if expected_matrix_index is None or actual_matrix_index != expected_matrix_index:
            raise JoinError(f"Tangent row does not join its exact source matrix owner: {key}")
        if actual_matrix_index in source_rows_seen:
            raise JoinError(f"Source tangent matrix row used twice: {actual_matrix_index}")
        source_rows_seen.add(actual_matrix_index)

        source_owner = floor_audit["row_owners"][actual_matrix_index]
        if source_owner != {"normal_cell": cell, "local_dof": local_dof}:
            raise JoinError(f"Source owner mismatch for matrix row {actual_matrix_index}")
        ref = ref_map.get(row["row_id"])
        if ref is None:
            raise JoinError(f"Missing adapter reference row for {row['row_id']}")
        if (
            ref["normal_cell"] != cell
            or int(ref["source_row_original_index"]) != actual_matrix_index
            or int(ref["source_spring_local_dof"]) != local_dof
            or int(ref["source_spring_element"]) != int(row["source_element"])
            or ref["source_spring_group"] != row["source_group"]
            or ref["source_row_id"] != row["row_id"]
        ):
            raise JoinError(f"Reference-node metadata does not match source tangent row {row['row_id']}")
        ref_key = (int(row["reference_node_metadata"]["node"]), int(row["reference_node_metadata"]["reference_dof"]))
        if ref_key != (int(ref["node"]), int(ref["reference_dof"])) or ref_key in reference_nodes_seen:
            raise JoinError(f"Reference coordinate is missing, duplicated, or misjoined: {ref_key}")
        reference_nodes_seen.add(ref_key)
        if (
            not ref.get("coordinate_is_abstract_scalar")
            or ref_key[0] in physical_nodes
            or ref_key[0] not in set(map(int, model["fixed_nodes"]))
            or ref["owner_tangent_basis_global_xyz"] != row["ownership"]["direction_global_xyz"]
        ):
            raise JoinError(f"Reference node is not declared as an abstract scalar coordinate: {row['row_id']}")

        projected = row_vector(row, coordinate_count)
        matrix_row = original[actual_matrix_index]
        source: dict[int, float] = {}
        for column, value in enumerate(matrix_row):
            value = float(value)
            if value != 0.0:
                coordinate = master_coordinate_indices[column]
                source[coordinate] = value
        residual = max(
            (abs(projected.get(index, 0.0) - source.get(index, 0.0)) for index in set(projected) | set(source)),
            default=0.0,
        )
        max_matrix_residual = max(max_matrix_residual, residual)
        if residual > TOL:
            raise JoinError(f"Projected tangent row differs from exact original matrix row {actual_matrix_index}: {residual}")

        sign = int(row["owner_point_rigid_row_sign"])
        if sign not in (-1, 1):
            raise JoinError(f"Unexpected arbitrary tangent-row orientation sign {sign}")
        sign_counts[sign] += 1
        local_dof_counts[local_dof] += 1
        floor_tangent_groups.add(row["source_group"])
        max_owner_rigid_residual = max(max_owner_rigid_residual, float(row["owner_point_rigid_row_max_abs_residual"]))
        tangent_direction = np.asarray(row["ownership"]["direction_global_xyz"], dtype=float)
        normal_direction = np.asarray(normal_by_cell[cell]["ownership"]["direction_global_xyz"], dtype=float)
        if abs(float(np.linalg.norm(tangent_direction)) - 1.0) > 1e-12 or abs(float(np.dot(tangent_direction, normal_direction))) > 1e-12:
            raise JoinError(f"Tangent basis is not a unit direction perpendicular to its normal: {row['row_id']}")
        tangents_by_cell[cell].append(row)

    if source_rows_seen != set(range(200)) or len(reference_nodes_seen) != 200:
        raise JoinError("The 200 source tangent rows/reference coordinates do not form a complete bijection")

    fixed_nodes = set(map(int, model["fixed_nodes"]))
    cells: list[dict[str, Any]] = []
    numerical_ground_nodes: set[int] = set()
    floor_projection_nodes: set[int] = set()
    normal_groups: set[str] = set()
    for cell in sorted(normal_by_cell):
        normal = normal_by_cell[cell]
        binding = normal_bindings.get(cell)
        owner = contact_owners.get(cell)
        if binding is None or owner is None:
            raise JoinError(f"Missing adapter normal binding/owner for {cell}")
        if (
            binding["group"] != normal["source_group"]
            or int(binding["source_element"]) != int(normal["source_element"])
            or int(binding["source_inventory_row_index"]) != int(normal["source_inventory_row_index"])
            or int(binding["source_inventory_row_index"]) < 0
            or binding["physical_owner"]["first"] != normal["ownership"]["first_body"]
            or binding["physical_owner"]["second"] != normal["ownership"]["second_body"]
            or binding["physical_owner"]["role"] != "floor_normal"
            or binding["physical_owner"]["scalar_normal"] != normal["ownership"]["direction_global_xyz"]
            or binding["physical_owner"]["point"] != normal["ownership"]["point_mm"]
        ):
            raise JoinError(f"Normal SPRINGA source identity/owner mismatch for {cell}")
        if (
            owner["point_xyz_mm"] != normal["ownership"]["point_mm"]
            or owner["normal_xyz"] != normal["ownership"]["direction_global_xyz"]
            or owner["first"] != normal["ownership"]["first_body"]
            or owner["second"] != normal["ownership"]["second_body"]
        ):
            raise JoinError(f"Adapter floor cell geometry/owner mismatch for {cell}")
        if normal["law"]["force_law"] != "k * max(q_mm, 0)" or normal["law"]["intended_law"] != "compression_only":
            raise JoinError(f"Unexpected floor normal unilateral law for {cell}")
        if normal["ownership"]["direction_global_xyz"] != [0.0, 0.0, 1.0]:
            raise JoinError(f"Source floor normal is not the reviewed +Z direction for {cell}")
        if normal["q_definition"].find("u(second source projection") != 0:
            raise JoinError(f"Unexpected normal extension definition for {cell}")
        source_action = normal["source_physical_action"]["on_first_body"]
        if source_action["sign"] != 1 or source_action["unit_direction_global_xyz"] != normal["ownership"]["direction_global_xyz"]:
            raise JoinError(f"Normal-force conjugate sign changed for {cell}")
        ground = normal["grounding"]
        ground_node = int(ground["springa_ground_node"])
        projection_ground = int(ground["fixed_floor_projection_endpoint"])
        projection_nodes = set(map(int, normal["source_projection"]["nodes"]))
        springa_nodes = set(map(int, normal["source_projection"]["springa_nodes"]))
        if (
            ground.get("ground_is_physical") is not False
            or ground.get("ground_endpoint_is_numerical_only") is not True
            or ground.get("ground_is_fixed_spc") is not True
            or ground_node not in fixed_nodes
            or ground_node in physical_nodes
            or ground.get("fixed_floor_projection_endpoint_is_included_as_physical_coordinate") is not False
            or projection_ground not in fixed_nodes
            or projection_ground in physical_nodes
            or not projection_nodes.isdisjoint(physical_nodes)
            or not springa_nodes.isdisjoint(physical_nodes)
        ):
            raise JoinError(f"Numerical ground classification/SPC changed for {cell}")
        numerical_ground_nodes.add(ground_node)
        floor_projection_nodes.add(projection_ground)
        normal_groups.add(normal["source_group"])

        tangent_cell = sorted(tangents_by_cell[cell], key=lambda item: int(item["local_dof"]))
        if [int(row["local_dof"]) for row in tangent_cell] != [2, 3]:
            raise JoinError(f"Cell lacks exactly its two local tangent rows: {cell}")
        if any(
            row["ownership"]["first_body"] != normal["ownership"]["first_body"]
            or row["ownership"]["second_body"] != normal["ownership"]["second_body"]
            or row["ownership"]["point_mm"] != normal["ownership"]["point_mm"]
            or row["ownership"]["role"] != "assumed_no_slip_floor"
            for row in tangent_cell
        ):
            raise JoinError(f"Tangent rows do not share the normal cell's physical owner/support point: {cell}")
        tangent_dirs = [np.asarray(row["ownership"]["direction_global_xyz"], dtype=float) for row in tangent_cell]
        if abs(float(np.dot(tangent_dirs[0], tangent_dirs[1]))) > 1e-12:
            raise JoinError(f"Two tangent rows are not independent orthogonal directions: {cell}")

        cells.append({
            "cell_id": cell,
            "normal_B_row_position": row_positions[id(normal)],
            "normal": {
                "source_group": normal["source_group"],
                "source_element": int(normal["source_element"]),
                "source_inventory_row_index": int(normal["source_inventory_row_index"]),
                "owner_body": normal["ownership"]["first_body"],
                "source_second_body_label": normal["ownership"]["second_body"],
                "physical_floor_support_verified": False,
                "support_point_mm": normal["ownership"]["point_mm"],
                "unit_normal_global_xyz": normal["ownership"]["direction_global_xyz"],
                "q_definition": normal["q_definition"],
                "law": normal["law"],
                "positive_compression_normal_force_conjugate": {
                    "scalar_force": "N = k * max(q, 0), N >= 0",
                    "physical_action_on_owner": "+normal * N",
                    "physical_row_relation": "source physical action = -B_normal^T * N; numerical ground reaction excluded",
                    "verified_source_action_sign": int(source_action["sign"]),
                },
                "source_projection_nodes": normal["source_projection"]["nodes"],
                "springa_nodes": normal["source_projection"]["springa_nodes"],
                "fixed_numerical_spring_ground_node": ground_node,
                "fixed_floor_projection_endpoint": projection_ground,
                "both_endpoints_nonphysical_numerical_coordinates": True,
            },
            "tangent_rows": [
                {
                    "B_row_position": row_positions[id(row)],
                    "source_original_matrix_row_index": int(row["source_original_row_index"]),
                    "local_dof": int(row["local_dof"]),
                    "source_group": row["source_group"],
                    "source_element": int(row["source_element"]),
                    "source_row_id": row["row_id"],
                    "reference_node": int(row["reference_node_metadata"]["node"]),
                    "reference_dof": int(row["reference_node_metadata"]["reference_dof"]),
                    "reference_coordinate_is_abstract_scalar": True,
                    "unit_tangent_global_xyz": row["ownership"]["direction_global_xyz"],
                    "owner_point_row_orientation_sign": int(row["owner_point_rigid_row_sign"]),
                    "exact_source_matrix_row_max_coefficient_residual": max(
                        abs(row_vector(row, coordinate_count).get(index, 0.0) - float(original[int(row["source_original_row_index"])][column]))
                        for column, index in enumerate(master_coordinate_indices)
                    ),
                    "constraint": "B_tangent * u_physical = r_episode; B_tangent has dimensionless coefficients; r and u are mm",
                    "signed_multiplier_units": "N; physical action on first body = orientation_sign * tangent_direction * multiplier",
                }
                for row in tangent_cell
            ],
        })

    current_replay_path = HERE / "current-controls-two-cell-replay.json"
    current_replay = read_json(current_replay_path) if (ROOT / current_replay_path).is_file() else None
    if current_replay is None or current_replay.get("status") != "PASS_CURRENT_CONTROLS_MATHEMATICAL_REPLAY":
        raise JoinError("Current-controls replay is missing or failed; the historical fixture pin must remain untouched")

    return {
        "schema": "current_floor_normal_tangent_join_contract/v1",
        "status": "PASS_SOURCE_BOUND_100_NORMALS_200_TANGENT_ROWS",
        "candidate": contract["candidate"],
        "case_id": contract["case_id"],
        "geometry_revision_id": contract["geometry_revision_id"],
        "native_solve_executed": False,
        "full_frame_operator_assembled": False,
        "contact_state_or_event_solved": False,
        "source_pins_sha256": sha256_file(ROOT / HERE / "source-pins.json"),
        "current_controls_replay_sha256": sha256_file(ROOT / current_replay_path),
        "source_inventory": {
            "physical_bodies": len(bodies),
            "physical_nodes": len(physical_nodes),
            "physical_translation_coordinates": coordinate_count,
            "projection_contract_rows": len(contract["rows"]),
            "projection_contract_distinct_text_row_ids": len({row["row_id"] for row in contract["rows"]}),
            "normal_B_row_positions_zero_based": [1370, 1469],
            "normal_row_count": len(normal_rows),
            "tangent_B_row_positions_zero_based": [1640, 1839],
            "tangent_row_count": len(tangent_rows),
            "tangent_local_dof_counts": {str(key): value for key, value in sorted(local_dof_counts.items())},
            "tangent_owner_orientation_sign_counts": {str(key): value for key, value in sorted(sign_counts.items())},
            "unique_normal_numerical_spring_ground_nodes": len(numerical_ground_nodes),
            "unique_fixed_floor_projection_endpoints": len(floor_projection_nodes),
            "unique_normal_source_groups": len(normal_groups),
            "all_ground_endpoints_fixed_nonphysical_and_excluded": True,
        },
        "source_floor_matrix": {
            "audit_status": floor_audit["status"],
            "original_matrix_shape": list(original.shape),
            "physical_master_dofs": len(floor_audit["physical_master_dofs"]),
            "source_row_count": len(floor_audit["row_owners"]),
            "independent_constraint_rank_from_pinned_audit": int(floor_audit["independent_constraint_rank"]),
            "all_source_rows_used_once": True,
            "all_reference_coordinates_used_once": True,
            "max_exact_projected_vs_original_coefficient_residual": max_matrix_residual,
            "max_owner_rigid_row_residual_from_projection_contract": max_owner_rigid_residual,
            "unique_tangent_source_groups": len(floor_tangent_groups),
        },
        "normal_contact_law": {
            "q_positive_means": "compression / bearing",
            "force_law": "N = k * max(q, 0), N >= 0",
            "physical_action_on_owner_body": "+normal * N",
            "source_row_physical_action": "-B_normal^T * N",
            "ground_reaction_in_physical_coordinate_vector": False,
        },
        "tangent_reference_interface": {
            "per_cell_rows": 2,
            "reference_row_relation": "B_tangent,j * u_physical = r_episode,j",
            "capture_rule": "At a bracketed normal contact event, capture r_episode,j = B_tangent,j * u_physical(event) for each of the two exact signed rows at that cell's support point.",
            "reference_coordinate": "Adapter reference node DOF 1 is an abstract scalar displacement in mm; it is not a global x translation.",
            "source_load_correction_use": "Do not substitute source CLOAD correction metadata for an event reference.",
            "closed_branch": "For positive normal force, retain both tangent equations and solve their signed multipliers with simultaneous equilibrium.",
            "open_branch": "For normal-open motion, remove both tangent equations and enforce zero tangent multipliers.",
            "reengagement": "After an open episode, capture both new references at the next bracketed closing event; replace the prior episode references.",
            "boundary_and_unknown_state": "q = 0 is ambiguous without event direction/history; unknown initial q = 0 remains AMBIGUOUS, with no guessed mask.",
            "required_event_input": {
                "physical_displacement_vector_length": coordinate_count,
                "event_cell_id": "one of the 100 source cell_id values",
                "event_condition": "bracketed transition with q_event = 0, event direction supplied by the path solver",
                "reference_values": "two row-specific B_tangent * u_event scalar values in mm, with source row and B position IDs",
                "history_state": "open/closed transition and prior episode identifier; not inferred from the adapter's initial SPC set",
            },
            "orientation_sign_counts": {str(key): value for key, value in sorted(sign_counts.items())},
        },
        "independent_fixture_evidence": {
            "two_cell_coupled_normal_tangent_reset": {
                "status": current_replay["fixture_replay"]["status"],
                "stage_count": current_replay["fixture_replay"]["stage_count"],
                "maximum_normal_equilibrium_residual": current_replay["fixture_replay"]["max_normal_equilibrium_residual"],
                "native_solve_executed": False,
                "source_record": "current-controls-two-cell-replay.json; original fixture and observed.json remain byte-preserved",
            },
            "synthetic_bracketed_event_reference_fixture": {
                "status": "PASS_EXACT_SYNTHETIC_EVENT_CAPTURE_RELEASE_RESET_AND_REFINEMENT",
                "scope": "separate synthetic SPD event/reference oracle; not actual-frame event state",
            },
            "coupled_contact_state_selector": {
                "status": selector_answer["status"],
                "solver_method": "borrowed PySCIPOpt indicator constraints with signed unbounded continuous variables; no caller big-M bounds",
                "known_answer_sha256": sha256_file(ROOT / SELECTOR_DIR / "known-answer.json"),
                "selector_script_sha256": sha256_file(ROOT / SELECTOR_DIR / "select_states.py"),
                "all_eight_tiny_cases_proved_mask_exhaustion": True,
                "cases": {
                    case_id: {
                        "classification": item["classification"],
                        "possible_binary_masks": int(item["possible_binary_masks"]),
                        "candidate_mask_count": len(item["candidate_masks"]),
                        "all_binary_masks_proven_exhausted": bool(item["all_binary_masks_proven_exhausted"]),
                        "candidate_masks": item["candidate_masks"],
                    }
                    for case_id, item in sorted(selector_by_id.items())
                },
                "zero_budget_stop": "Separate pinned producer exercise returns BUDGET_OR_SOLVER_STOP without a completeness claim; see selector README.",
                "scope_limit": "Tiny supplied operators/references only; does not establish frame-operator readiness, actual event/reference history, or 100-cell scalability.",
            },
            "native_staged_capture_and_release_coupons": {
                "staged_ten_step_coupon": "parent staged all-increment assessment is pinned in source-pins.json",
                "nonzero_reference_release_coupon": "parent two-step all-increment assessment is pinned in source-pins.json",
                "scope": "native output mapping only; not a 100-cell or frame contact solution",
            },
        },
        "cells": cells,
        "limits": [
            "This is a source row/reference join and sign contract only; it does not assemble or solve the physical frame stiffness operator.",
            "No actual initial gravity state, admissible 100-cell mask, contact event, event reference, or frame reaction is established.",
            "The q=0 normal boundary remains ambiguous absent a path/event direction; no contact mask is guessed.",
            "The fixed SPRINGA grounds and fixed floor projection endpoints are numerical coordinates, not physical floor anchors.",
            "The source no-slip assumption remains unverified; the rows provide no floor friction, capacity, or acceptance claim.",
            "The staged and release native coupons validate bounded output/reference mechanics only and do not authorize or imply a frame solve.",
        ],
        "verified_inputs": {path: {"sha256": digest} for path, digest in sorted(pins.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="recompute and compare with join-contract.json")
    mode.add_argument("--write", action="store_true", help="write join-contract.json after all source checks pass")
    args = parser.parse_args()
    result = main_artifacts()
    rendered = canonical_bytes(result)
    output_path = ROOT / OUTPUT
    if args.write:
        output_path.write_bytes(rendered)
        print(f"wrote {OUTPUT}")
        return
    if not output_path.is_file():
        raise SystemExit("missing join-contract.json; inspect inputs, then run with --write")
    if output_path.read_bytes() != rendered:
        raise SystemExit("verification failed: recomputed join contract differs from join-contract.json")
    print(
        "PASS_SOURCE_BOUND_100_NORMALS_200_TANGENT_ROWS: exact source-row bijection, "
        "reference-node joins, coefficient identity, and physical owner/sign metadata verified; no state/operator solve"
    )


if __name__ == "__main__":
    main()
