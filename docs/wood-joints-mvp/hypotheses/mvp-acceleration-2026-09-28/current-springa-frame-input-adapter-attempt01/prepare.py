"""Assemble one source-bound a12-rear CalculiX input adapter, without solving."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.horizontal_panel_frame import record_structure
from fea.wood_joint_reduced_case import build_case, _equation_load_expander
from fea.wood_joint_reduced_model import oriented_deck

HERE = Path(__file__).resolve().parent
CASE_DIR = HERE / "a12-rear"

BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
C11_MODEL = BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
C11_DECK = C11_MODEL.parent / "model.inp"
CARRIER_INVENTORY = BASE / "current-native-carrier-law-inventory-attempt01/carrier-laws.json"
FLOOR_AUDIT = BASE / "current-floor-stick-constraint-audit-attempt01/audit.json"
FLOOR_MATRICES = BASE / "current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz"
SPRINGA_RESULT = BASE / "current-springa-relative-coordinate-fixture-attempt01/assessment.json"
FLOOR_RF_RESULT = BASE / "current-exact-floor-mpc-fixture-attempt02/assessment.json"
TRANSFORMED_FLOOR_RESULT = BASE / "current-transformed-floor-reaction-fixture-attempt01/assessment.json"
CORNER_CONTRACT = BASE / "current-corner-demand-contract-attempt01/contract.json"
GEOMETRY_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CANDIDATE = "compact-floor-flush-wood-joints-development"
PINNED_SHA256 = {
    str(C11_MODEL): "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0",
    str(C11_DECK): "42a2527eda91c1c56933c00b8429dc37e3d02dba842798fc1eb616b299027ef1",
    str(CARRIER_INVENTORY): "af95579f8c7682b0cdb5fbb29e16bdcc311bfb08f89d055856a17588145bd372",
    str(FLOOR_AUDIT): "43b5aa99468b1577cd273baddafe47955b235fa00ddd5b9d5aff91d490695c95",
    str(FLOOR_MATRICES): "4fcc630274e2f1c7166c811d2aa97a3f075d60b5724600b88be73afebe308f6e",
    str(SPRINGA_RESULT): "b23fadfe25621e43673c8d1f3d4575ddb77ac284b2a84c6969296cc25d40c854",
    str(FLOOR_RF_RESULT): "f5d36e1f9e337b5d4c99a157a087920862efa9f2c96c4cd7c7ca9f3e0ed6ea6b",
    str(TRANSFORMED_FLOOR_RESULT): "d09e314969cc0dbb99d3a6c8cda55563a5244d590f25884f925838fed7a54a51",
    str(CORNER_CONTRACT): "f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74",
}
MODEL_SCHEMA = "current_springa_frame_input_model/v1"
LAW_COUNTS = {
    "compression_only": 1122,
    "tension_only": 170,
    "bilateral": 348,
    "floor_tangent_all_bearing_hypothesis": 200,
}


class AdapterInputError(ValueError):
    """Raised when a source pin, geometry join, or deck audit is inconsistent."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, allow_nan=False))


def ccx_real(value: float) -> str:
    """Write a real with a decimal point, including integer-valued reals."""
    number = float(value)
    if not math.isfinite(number):
        raise AdapterInputError("CalculiX input contains a nonfinite real")
    token = format(number, ".14g")
    if "e" in token.lower():
        mantissa, exponent = re.split("[eE]", token, maxsplit=1)
        if "." not in mantissa:
            mantissa += ".0"
        token = mantissa + "e" + exponent
    elif "." not in token:
        token += ".0"
    if len(token) > 20:
        raise AdapterInputError(f"CalculiX F20.0 real exceeds 20 columns: {token}")
    return token


def _decimal_point_real_token(token: str) -> str:
    """Preserve a source real token while adding a decimal point when needed."""
    value = token.strip()
    if not value or not math.isfinite(float(value)):
        raise AdapterInputError(f"Invalid CalculiX real token: {token}")
    if "e" in value.lower():
        mantissa, exponent = re.split("[eE]", value, maxsplit=1)
        if "." not in mantissa:
            mantissa += ".0"
        value = mantissa + "e" + exponent
    elif "." not in value:
        value += ".0"
    if len(value) > 20:
        raise AdapterInputError(f"CalculiX real exceeds 20 columns: {value}")
    return value


def _norm(vector: list[float]) -> float:
    return float(np.linalg.norm(np.asarray(vector, dtype=float)))


def _pin_inputs() -> dict[str, Any]:
    pins: dict[str, Any] = {}
    for relative, expected in PINNED_SHA256.items():
        path = ROOT / relative
        observed = sha256(path)
        if observed != expected:
            raise AdapterInputError(
                f"Pinned input changed: {relative}; expected {expected}, got {observed}"
            )
        pins[relative] = {"sha256": observed}

    c11 = json.loads((ROOT / C11_MODEL).read_text(encoding="utf-8"))
    carriers = json.loads((ROOT / CARRIER_INVENTORY).read_text(encoding="utf-8"))
    floor_audit = json.loads((ROOT / FLOOR_AUDIT).read_text(encoding="utf-8"))
    springa_result = json.loads((ROOT / SPRINGA_RESULT).read_text(encoding="utf-8"))
    floor_rf_result = json.loads((ROOT / FLOOR_RF_RESULT).read_text(encoding="utf-8"))
    transformed_floor_result = json.loads(
        (ROOT / TRANSFORMED_FLOOR_RESULT).read_text(encoding="utf-8")
    )
    corner_contract = json.loads((ROOT / CORNER_CONTRACT).read_text(encoding="utf-8"))
    if c11.get("candidate") != CANDIDATE or c11.get("geometry_revision_id") != GEOMETRY_REVISION:
        raise AdapterInputError("C11 input model identity does not match the reviewed candidate")
    if carriers.get("source_input_sha256") != PINNED_SHA256[str(C11_MODEL)]:
        raise AdapterInputError("Carrier inventory is not bound to the pinned C11 input")
    if floor_audit.get("source_input_sha256") != PINNED_SHA256[str(C11_MODEL)]:
        raise AdapterInputError("Floor constraint audit is not bound to the pinned C11 input")
    if carriers.get("native_solve_executed") is not False:
        raise AdapterInputError("Carrier inventory source must remain input-only")
    if springa_result.get("status") != "PASS_NATIVE_TWO_BODY_RELATIVE_SPRINGA_MPC_FIXTURE":
        raise AdapterInputError("Relative-coordinate SPRINGA method result is not the pinned pass")
    if floor_rf_result.get("status") != "PASS_NATIVE_EXACT_FLOOR_MPC_REACTION_KNOWN_ANSWER":
        raise AdapterInputError("Exact-floor reference reaction result is not the pinned pass")
    if floor_rf_result.get("floor_tangential_reaction_mapping") != "RF_REFERENCE_MINUS_DEPENDENT_CLOAD":
        raise AdapterInputError("Exact-floor reference reaction mapping changed")
    if (
        transformed_floor_result.get("status") != "PASS_NATIVE_TRANSFORMED_FLOOR_REACTION_KNOWN_ANSWER"
        or transformed_floor_result.get("method_fixture_passed") is not True
        or transformed_floor_result.get("selected_source_rows_zero_based") != [1, 0]
    ):
        raise AdapterInputError("Transformed nonidentity/permuted exact-floor method result changed")
    if (
        corner_contract.get("source_input_sha256") != PINNED_SHA256[str(C11_MODEL)]
        or corner_contract.get("source_response_used") is not False
        or corner_contract.get("actual_case_demands_available") is not False
    ):
        raise AdapterInputError("Corner-demand contract no longer describes source-only demand requirements")
    return {
        "c11_model": c11,
        "carriers": carriers,
        "floor_audit": floor_audit,
        "springa_result": springa_result,
        "floor_rf_result": floor_rf_result,
        "transformed_floor_result": transformed_floor_result,
        "corner_contract": corner_contract,
        "pinned_sources": pins,
    }


def _expand_projection_rows(structure: Any) -> tuple[list[list[tuple[int, int]]], np.ndarray]:
    """Recreate the audited source floor constraint matrix on rebuilt geometry."""
    equations: dict[tuple[int, int], list[tuple[int, int, float]]] = {}
    for terms in structure.equations:
        if not terms:
            continue
        key = (int(terms[0][0]), int(terms[0][1]))
        if key in equations or float(terms[0][2]) == 0.0:
            raise AdapterInputError(f"Duplicate or zero projection pivot: {key}")
        equations[key] = [(int(n), int(d), float(c)) for n, d, c in terms]
    fixed = {(int(node), dof) for node in structure.fixed for dof in (1, 2, 3)}
    if fixed.intersection(equations):
        raise AdapterInputError("A rebuilt fixed DOF is also an equation-dependent DOF")

    cache: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    visiting: set[tuple[int, int]] = set()

    def expand(key: tuple[int, int]) -> dict[tuple[int, int], float]:
        if key in cache:
            return cache[key]
        if key in visiting:
            raise AdapterInputError(f"Circular rebuilt projection equation at {key}")
        visiting.add(key)
        if key in fixed:
            result: dict[tuple[int, int], float] = {}
        elif key not in equations:
            result = {key: 1.0}
        else:
            terms = equations[key]
            result = {}
            first_node, first_dof, first_coefficient = terms[0]
            for node, dof, coefficient in terms[1:]:
                for master, weight in expand((node, dof)).items():
                    result[master] = result.get(master, 0.0) - coefficient * weight / first_coefficient
            result = {master: weight for master, weight in result.items() if abs(weight) > 1e-14}
        visiting.remove(key)
        cache[key] = result
        return result

    row_maps: list[dict[tuple[int, int], float]] = []
    row_keys: list[list[tuple[int, int]]] = []
    for spring in structure.springs:
        if not spring["name"].endswith("_friction"):
            continue
        first, second = map(int, spring["nodes"])
        dof = int(spring["dof"])
        row = dict(expand((first, dof)))
        for key, value in expand((second, dof)).items():
            row[key] = row.get(key, 0.0) - value
        row = {key: value for key, value in row.items() if abs(value) > 1e-14}
        row_maps.append(row)
        row_keys.append(sorted(row))
    if len(row_maps) != 200:
        raise AdapterInputError(f"Expected 200 rebuilt floor-tangent rows, got {len(row_maps)}")

    master_dofs = sorted(set().union(*(set(row) for row in row_maps)))
    columns = {key: index for index, key in enumerate(master_dofs)}
    matrix = np.zeros((len(row_maps), len(master_dofs)), dtype=float)
    for row_index, row in enumerate(row_maps):
        for key, value in row.items():
            matrix[row_index, columns[key]] = value
    return [master_dofs, row_keys], matrix


def _validate_source_geometry(
    fresh_record: dict[str, Any],
    fresh_metadata: dict[str, Any],
    c11_model: dict[str, Any],
) -> dict[str, Any]:
    compared = [
        "nodes",
        "elements",
        "equations",
        "fixed_nodes",
        "physical_body_nodes",
        "physical_body_elements",
        "physical_body_loads",
        "physical_external_loads",
        "physical_body_wrenches",
        "expected_physical_body_wrenches",
        "source_wrench_ledger",
        "connection_attachment_rows",
        "connection_counts",
        "contact_cell_ownership",
        "floor_support_nodes",
        "gravity_load_audits",
        "panel_load_records",
        "physical_load_sources_by_body",
        "body_wrench_audit_rows",
    ]
    for field in compared:
        if jsonable(fresh_record[field]) != c11_model[field]:
            raise AdapterInputError(f"Freshly assembled source data differs from C11 input at {field}")
    fresh_springs = [
        {key: value for key, value in row.items() if key != "active"}
        for row in fresh_record["springs"]
    ]
    c11_springs = [
        {key: value for key, value in row.items() if key != "active"}
        for row in c11_model["springs"]
    ]
    if jsonable(fresh_springs) != c11_springs:
        raise AdapterInputError("Fresh source carrier geometry/stiffness differs from pinned C11 input")
    if jsonable(fresh_metadata["connection_ownership"]) != c11_model["connection_ownership"]:
        raise AdapterInputError("Fresh owner/axis identities differ from the pinned C11 input")
    if jsonable(fresh_metadata["body_geometry"]) != c11_model["body_geometry"]:
        raise AdapterInputError("Fresh member/panel geometry records differ from the pinned C11 input")
    if jsonable(fresh_metadata["material_binding"]) != c11_model["material_binding"]:
        raise AdapterInputError("Fresh material binding/orientation differs from the pinned C11 input")
    if jsonable(fresh_metadata["physical_external_loads"]) != c11_model["physical_external_loads"]:
        raise AdapterInputError("Fresh physical external nodal loads differ from pinned C11 input")
    if jsonable(fresh_metadata["physical_external_loads"]) != c11_model["loads"]:
        raise AdapterInputError("C11 deck load representation is not its recorded physical external load map")
    if jsonable(fresh_metadata["source_sha256"]) != c11_model["source_sha256"]:
        raise AdapterInputError("Fresh geometry/material source pins differ from the pinned C11 input")
    return {
        "fields_compared_to_c11_input": compared
        + [
            "source_springs_without_historical_active_flags",
            "physical_external_loads",
            "connection_ownership",
            "body_geometry",
            "material_binding",
            "source_sha256",
        ],
        "c11_input_model_sha256": PINNED_SHA256[str(C11_MODEL)],
        "rejected_response_forces_read": False,
        "historical_active_states_reused": False,
    }


def _wrench_from_load_map(
    nodes: dict[int, Any], loads: dict[int, Any]
) -> tuple[np.ndarray, np.ndarray]:
    force = np.zeros(3, dtype=float)
    moment = np.zeros(3, dtype=float)
    for node, vector in loads.items():
        vector_array = np.asarray(vector, dtype=float)
        point = np.asarray(nodes[int(node)], dtype=float)
        force += vector_array
        moment += np.cross(point, vector_array)
    return force, moment


def _normalize_fresh_source_loads(
    structure: Any, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Expand current auxiliary point loads through the source translational MPCs."""
    raw_loads = {
        int(node): np.asarray(force, dtype=float).copy()
        for node, force in structure.loads.items()
    }
    expanded: dict[int, np.ndarray] = {}
    expander = _equation_load_expander(structure)
    for node, vector in raw_loads.items():
        for dof, value in enumerate(vector, start=1):
            scalar = float(value)
            if scalar == 0.0:
                continue
            masters = expander.get(int(node), {}).get(dof)
            if masters is None:
                expanded.setdefault(int(node), np.zeros(3, dtype=float))[dof - 1] += scalar
                continue
            for master, weight in masters:
                expanded.setdefault(int(master), np.zeros(3, dtype=float))[dof - 1] += (
                    scalar * float(weight)
                )

    target = {
        int(node): np.asarray(force, dtype=float).copy()
        for node, force in metadata["physical_external_loads"].items()
    }
    def load_map_hash(load_map: dict[int, Any]) -> str:
        payload = {
            str(node): [float(value) for value in vector]
            for node, vector in sorted(load_map.items())
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    all_nodes = set(expanded) | set(target)
    nodal_differences = {
        node: expanded.get(node, np.zeros(3)) - target.get(node, np.zeros(3))
        for node in all_nodes
    }
    maximum_nodal_error = max(
        (float(np.max(np.abs(value))) for value in nodal_differences.values()),
        default=0.0,
    )
    raw_force, raw_moment = _wrench_from_load_map(structure.nodes, raw_loads)
    expanded_force, expanded_moment = _wrench_from_load_map(structure.nodes, expanded)
    target_force, target_moment = _wrench_from_load_map(structure.nodes, target)
    force_transfer_error = expanded_force - raw_force
    moment_transfer_error = expanded_moment - raw_moment
    target_force_error = expanded_force - target_force
    target_moment_error = expanded_moment - target_moment
    if maximum_nodal_error > 1e-8:
        worst_node = max(
            nodal_differences,
            key=lambda node: float(np.max(np.abs(nodal_differences[node]))),
        )
        raise AdapterInputError(
            "Original source CLOADs do not expand through their MPCs to physical_external_loads; "
            f"node={worst_node}, delta_N={nodal_differences[worst_node].tolist()}, max={maximum_nodal_error} N"
        )
    if max(
        float(np.max(np.abs(force_transfer_error))),
        float(np.max(np.abs(moment_transfer_error))),
        float(np.max(np.abs(target_force_error))),
        float(np.max(np.abs(target_moment_error))),
    ) > 1e-7:
        raise AdapterInputError("Original-to-physical CLOAD MPC transfer does not conserve force and first moment")

    # The existing response freezer deliberately solves the physical external
    # nodal map after these same MPC expansions; preserve that source behavior.
    structure.loads = {node: vector.tolist() for node, vector in target.items()}
    return {
        "method": "fea.wood_joint_reduced_case._equation_load_expander on the original source MPCs",
        "raw_source_load_node_count": len(raw_loads),
        "expanded_physical_load_node_count": len(expanded),
        "fresh_physical_external_load_node_count": len(target),
        "raw_source_load_map_sha256": load_map_hash(raw_loads),
        "expanded_physical_load_map_sha256": load_map_hash(expanded),
        "fresh_physical_external_load_map_sha256": load_map_hash(target),
        "maximum_nodal_expansion_discrepancy_N": maximum_nodal_error,
        "raw_to_expanded_force_difference_N": force_transfer_error.tolist(),
        "raw_to_expanded_first_moment_difference_Nmm": moment_transfer_error.tolist(),
        "expanded_to_physical_external_force_difference_N": target_force_error.tolist(),
        "expanded_to_physical_external_first_moment_difference_Nmm": target_moment_error.tolist(),
        "raw_and_expanded_wrench_transfer_passed": True,
        "expanded_map_matches_fresh_physical_external_loads": True,
        "physical_external_loads_match_pinned_c11_input": True,
        "load_values_taken_from": "fresh_build_case_metadata.physical_external_loads",
        "c11_physical_load_map_used_for_cross_check_only": True,
        "structure_loads_normalized_to_fresh_physical_external_map": True,
        "historical_response_forces_read": False,
    }


def _validate_corner_contract(
    contract: dict[str, Any], metadata: dict[str, Any]
) -> dict[str, Any]:
    if contract.get("candidate") != CANDIDATE or contract.get("geometry_revision_id") != GEOMETRY_REVISION:
        raise AdapterInputError("Corner-demand contract is bound to a different candidate geometry")
    inventory = contract.get("interface_inventory")
    if not isinstance(inventory, list) or len(inventory) != 338:
        raise AdapterInputError("Corner-demand contract must bind its 338 incident interface rows")
    names: set[str] = set()
    owners = metadata["connection_ownership"]
    for row in inventory:
        name = str(row["source_connection_name"])
        if name in names:
            raise AdapterInputError(f"Duplicate source owner in corner-demand contract: {name}")
        names.add(name)
        if jsonable(owners.get(name)) != row["owner"]:
            raise AdapterInputError(f"Corner-demand contract owner changed in rebuilt input: {name}")
        action_bodies = set(map(str, row["physical_action_required_on"]))
        if not action_bodies or not action_bodies.issubset(
            {str(row["owner"]["first"]), str(row["owner"]["second"])}
        ):
            raise AdapterInputError(f"Corner-demand contract has an invalid body action mapping: {name}")

    group_audit: dict[str, Any] = {}
    for group_name, group in contract.get("primary_new_corner_groups", {}).items():
        group_names = list(map(str, group["source_connection_names"]))
        if any(name not in names for name in group_names):
            raise AdapterInputError(f"Primary corner group {group_name} includes an unbound source owner")
        group_rows = [row for row in inventory if row["source_connection_name"] in set(group_names)]
        group_axes = {
            str(row["owner"].get("axis_id"))
            for row in group_rows
            if row["owner"].get("axis_id") is not None
        }
        lateral_count = sum(row["owner"].get("role") == "candidate_bolt_lateral_plane" for row in group_rows)
        seat_count = sum(row["owner"].get("role") == "physical_bolt_outer_seat_tension" for row in group_rows)
        if (
            group_axes != set(map(str, group["axis_ids"]))
            or lateral_count != int(group["lateral_plane_count"])
            or seat_count != int(group["outer_seat_tie_count"])
        ):
            raise AdapterInputError(f"Primary corner group ownership or plane/tie count changed: {group_name}")
        group_audit[group_name] = {
            "axis_ids": sorted(group_axes),
            "source_connection_names": group_names,
            "lateral_plane_count": lateral_count,
            "outer_seat_tie_count": seat_count,
        }
    return {
        "contract_sha256": PINNED_SHA256[str(CORNER_CONTRACT)],
        "contract_path": str(CORNER_CONTRACT),
        "source_input_sha256": contract["source_input_sha256"],
        "source_response_used": False,
        "actual_case_demands_available": False,
        "incident_owned_groups_checked": len(names),
        "all_contract_owners_match_rebuilt_source": True,
        "primary_corner_groups": group_audit,
        "new_block_axis_count": int(contract["new_block_axis_count"]),
        "retained_original_leg_runner_axis_count": int(
            contract["retained_original_leg_runner_axis_count"]
        ),
        "new_and_retained_axes_are_separately_audited": True,
        "source_demands_extracted": False,
    }


def _source_spring_index(structure: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for spring in structure.springs:
        group = str(spring["group"])
        if group in result:
            raise AdapterInputError(f"Duplicate scalar spring group {group}")
        result[group] = spring
    return result


def _validate_carrier_inventory(
    rows: list[dict[str, Any]],
    structure: Any,
    metadata: dict[str, Any],
    carrier_summary: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if len(rows) != 1840 or len(structure.springs) != 1840:
        raise AdapterInputError("Expected 1,840 source scalar carrier rows")
    source_by_group = _source_spring_index(structure)
    if len(source_by_group) != len(rows):
        raise AdapterInputError("Carrier law rows do not cover the rebuilt scalar springs")
    by_group: dict[str, dict[str, Any]] = {}
    observed_laws = Counter()
    for inventory_index, row in enumerate(rows):
        group = str(row["group"])
        if group in by_group:
            raise AdapterInputError(f"Duplicate carrier inventory group {group}")
        spring = source_by_group.get(group)
        if spring is None:
            raise AdapterInputError(f"Carrier group is absent from the fresh source model: {group}")
        expected = {
            "name": spring["name"],
            "element": int(spring["element"]),
            "nodes": list(map(int, spring["nodes"])),
            "dof": int(spring["dof"]),
            "stiffness_n_per_mm": float(spring["stiffness_n_per_mm"]),
        }
        for field, value in expected.items():
            actual = row[field]
            if field == "stiffness_n_per_mm":
                if not math.isclose(float(actual), value, rel_tol=1e-12, abs_tol=1e-12):
                    raise AdapterInputError(f"Carrier stiffness differs at {group}")
            elif actual != value:
                raise AdapterInputError(f"Carrier {field} differs at {group}")
        if metadata["connection_ownership"].get(str(row["name"])) != row["physical_owner"]:
            raise AdapterInputError(f"Physical owner/axis changed at carrier {group}")
        law = str(row["intended_law"])
        observed_laws[law] += 1
        by_group[group] = {
            **row,
            "_adapter_source_row_index": inventory_index,
        }
    if dict(observed_laws) != LAW_COUNTS:
        raise AdapterInputError(f"Unexpected source carrier law counts: {dict(observed_laws)}")
    if set(by_group) != set(source_by_group):
        raise AdapterInputError("The carrier law inventory is not a complete scalar-row join")

    axes_by_role: dict[str, set[str]] = {}
    for role in (
        "candidate_bolt_lateral_plane",
        "retained_bolt_lateral_plane",
        "panel_screw_lateral_plane",
        "non_qualifying_parametric_screw_withdrawal",
        "physical_bolt_outer_seat_tension",
    ):
        axes_by_role[role] = {
            str(row["physical_owner"]["axis_id"])
            for row in rows
            if row["role"] == role and row["physical_owner"].get("axis_id") is not None
        }
    candidate_axes = axes_by_role["candidate_bolt_lateral_plane"]
    retained_axes = axes_by_role["retained_bolt_lateral_plane"]
    panel_screw_axes = axes_by_role["panel_screw_lateral_plane"]
    screw_tension_axes = axes_by_role["non_qualifying_parametric_screw_withdrawal"]
    bolt_tension_axes = axes_by_role["physical_bolt_outer_seat_tension"]
    if len(candidate_axes) != 92 or len(retained_axes) != 12 or candidate_axes & retained_axes:
        raise AdapterInputError("The 92 new and 12 retained bolt-axis sets are not disjoint")
    if len(panel_screw_axes) != 66 or screw_tension_axes != panel_screw_axes:
        raise AdapterInputError("The 66 current Hillman axes do not match their axial rows")
    if bolt_tension_axes != candidate_axes | retained_axes:
        raise AdapterInputError("The 104 bolt outer-seat rows do not cover 92+12 axes")
    if carrier_summary.get("new_block_attachment_axes") is None:
        raise AdapterInputError("Carrier source lacks its reviewed new-bolt axis inventory")
    if set(carrier_summary["new_block_attachment_axes"]) != candidate_axes:
        raise AdapterInputError("Carrier summary new-bolt axes differ from scalar rows")
    if set(carrier_summary["retained_original_leg_runner_axes"]) != retained_axes:
        raise AdapterInputError("Carrier summary retained-bolt axes differ from scalar rows")

    return by_group, {
        "source_scalar_carrier_rows": len(rows),
        "source_law_counts": dict(sorted(observed_laws.items())),
        "new_candidate_bolt_axes": len(candidate_axes),
        "retained_starting_frame_bolt_axes": len(retained_axes),
        "new_and_retained_bolt_axes_disjoint": True,
        "hillman_panel_screw_axes": len(panel_screw_axes),
        "hillman_lateral_axes_preserved": True,
        "hillman_axial_rows_are_parametric_nonqualifying_rows": True,
        "old_bolt_resistance_qualification_inherited": False,
    }


def _build_floor_equations(
    structure: Any,
    carrier_rows: list[dict[str, Any]],
    floor_audit: dict[str, Any],
    matrices_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[list[tuple[int, int, float]]]]:
    masters, rebuilt_a = _expand_projection_rows(structure)
    matrix_archive = np.load(matrices_path)
    saved_a = np.asarray(matrix_archive["original"], dtype=float)
    reduced_h = np.asarray(matrix_archive["reduced"], dtype=float)
    pivots = np.asarray(matrix_archive["pivots"], dtype=int)
    selected_rows = np.asarray(matrix_archive["selected_rows"], dtype=int)
    source_masters = [tuple(map(int, item)) for item in floor_audit["physical_master_dofs"]]
    if [tuple(item) for item in masters[0]] != source_masters:
        raise AdapterInputError("Rebuilt floor master-DOF ordering differs from its pinned audit")
    if rebuilt_a.shape != saved_a.shape or not np.allclose(rebuilt_a, saved_a, rtol=0.0, atol=1e-11):
        raise AdapterInputError("Fresh floor-stick rows differ from the pinned 200x800 constraint matrix")
    if reduced_h.shape != saved_a.shape or len(pivots) != 200 or len(selected_rows) != 200:
        raise AdapterInputError("Pinned exact floor constraint matrix has an unexpected shape")
    if sorted(map(int, selected_rows)) != list(range(200)):
        raise AdapterInputError("Selected floor rows are not a permutation of all 200 source rows")
    selected_a = saved_a[np.ix_(selected_rows, np.arange(saved_a.shape[1]))]
    pivot_block = selected_a[:, pivots]
    inverse_pivot_block = np.linalg.solve(pivot_block, np.eye(200, dtype=float))
    free_column_mask = np.ones(saved_a.shape[1], dtype=bool)
    free_column_mask[pivots] = False
    omitted_h_values = np.abs(reduced_h[:, free_column_mask])
    omitted_h_values = omitted_h_values[(omitted_h_values > 0.0) & (omitted_h_values <= 1e-13)]
    omitted_inverse_values = np.abs(inverse_pivot_block)
    omitted_inverse_values = omitted_inverse_values[
        (omitted_inverse_values > 0.0) & (omitted_inverse_values <= 1e-13)
    ]
    reconstructed_h = inverse_pivot_block @ selected_a
    if not np.allclose(reconstructed_h, reduced_h, rtol=0.0, atol=1e-10):
        raise AdapterInputError("Reconstructed H does not match the pinned exact floor matrix")
    if not np.allclose(reduced_h[:, pivots], np.eye(200), rtol=0.0, atol=1e-10):
        raise AdapterInputError("Pinned floor pivot block is not the identity")

    row_owners = floor_audit["row_owners"]
    tangent_carriers = [
        row for row in carrier_rows if row["role"] == "assumed_no_slip_floor"
    ]
    if len(tangent_carriers) != 200 or len(row_owners) != 200:
        raise AdapterInputError("Expected 200 source floor tangent components")
    carrier_by_name_dof = {
        (str(row["name"]), int(row["dof"])): row for row in tangent_carriers
    }
    original_node_tags = set(map(int, structure.nodes))
    reference_by_original_row: dict[int, dict[str, Any]] = {}
    for row_index, owner in enumerate(row_owners):
        name = str(owner["normal_cell"]) + "_friction"
        dof = int(owner["local_dof"])
        source = carrier_by_name_dof.get((name, dof))
        if source is None:
            raise AdapterInputError(f"Floor audit row lacks source tangent {name}/{dof}")
        physical_owner = source["physical_owner"]
        basis = np.asarray(physical_owner["force_basis"][dof - 1], dtype=float)
        if not np.isclose(np.linalg.norm(basis), 1.0, atol=1e-12, rtol=0.0):
            raise AdapterInputError(f"Floor tangent basis is not unit length: {name}/{dof}")
        point = list(map(float, physical_owner["point"]))
        ref = structure.node(point)
        if ref in original_node_tags or any(int(item["node"]) == ref for item in reference_by_original_row.values()):
            raise AdapterInputError("Floor reference node tag was reused instead of created uniquely")
        structure.fixed.add(ref)
        reference_by_original_row[row_index] = {
            "source_row_original_index": row_index,
            "normal_cell": str(owner["normal_cell"]),
            "source_spring_name": name,
            "source_spring_group": str(source["group"]),
            "source_spring_element": int(source["element"]),
            "source_spring_local_dof": dof,
            "node": ref,
            "reference_dof": 1,
            "source_row_id": f"{name}/local-dof-{dof}",
            "coordinate_is_abstract_scalar": True,
            "owner_floorpoint_xyz_mm": point,
            "owner_tangent_basis_global_xyz": basis.tolist(),
            "physical_owner": physical_owner,
            "former_finite_tangent_element_removed": int(source["element"]),
        }

    pivot_dofs = [source_masters[int(index)] for index in pivots]
    floor_equations: list[dict[str, Any]] = []
    equation_terms: list[list[tuple[int, int, float]]] = []
    for normalized_row in range(200):
        original_row = int(selected_rows[normalized_row])
        pivot_node, pivot_dof = pivot_dofs[normalized_row]
        terms: list[tuple[int, int, float]] = [(int(pivot_node), int(pivot_dof), 1.0)]
        for column, (node, dof) in enumerate(source_masters):
            if int(column) in set(map(int, pivots)):
                continue
            coefficient = float(reduced_h[normalized_row, column])
            if abs(coefficient) > 1e-13:
                terms.append((int(node), int(dof), coefficient))
        for selected_column, selected_original_row in enumerate(selected_rows):
            coefficient = -float(inverse_pivot_block[normalized_row, selected_column])
            if abs(coefficient) > 1e-13:
                reference = reference_by_original_row[int(selected_original_row)]
                terms.append((int(reference["node"]), 1, coefficient))
        equation_terms.append(terms)
        reference = reference_by_original_row[original_row]
        floor_equations.append(
            {
                "normalized_equation_index": normalized_row,
                "source_row_original_index": original_row,
                "dependent_physical_pivot_dof": [int(pivot_node), int(pivot_dof)],
                "dependent_reference_node": int(reference["node"]),
                "equation_term_count": len(terms),
                "physical_free_master_term_count": len(terms)
                - 1
                - int(np.count_nonzero(np.abs(inverse_pivot_block[normalized_row]) > 1e-13)),
            }
        )
    structure.equations.extend(equation_terms)
    if len({(terms[0][0], terms[0][1]) for terms in equation_terms}) != 200:
        raise AdapterInputError("Floor equations do not have 200 unique physical dependent DOFs")
    return [reference_by_original_row[index] for index in range(200)], {
        "original_constraint_rows": 200,
        "independent_constraint_rank": 200,
        "physical_master_dof_count": 800,
        "physical_master_dofs": [[int(node), int(dof)] for node, dof in source_masters],
        "rebuilt_original_matrix_max_abs_residual": float(np.max(np.abs(rebuilt_a - saved_a))),
        "rebuilt_reduced_matrix_max_abs_residual": float(np.max(np.abs(reconstructed_h - reduced_h))),
        "equation_term_omission_policy": "Omit H and S^-1 coefficients with absolute magnitude <=1e-13 before serialization; serialize retained coefficients with .14g.",
        "omitted_nonzero_H_coefficient_count": int(len(omitted_h_values)),
        "maximum_abs_omitted_nonzero_H_coefficient": float(
            np.max(omitted_h_values) if len(omitted_h_values) else 0.0
        ),
        "omitted_nonzero_inverse_S_coefficient_count": int(len(omitted_inverse_values)),
        "maximum_abs_omitted_nonzero_inverse_S_coefficient": float(
            np.max(omitted_inverse_values) if len(omitted_inverse_values) else 0.0
        ),
        "reference_row_order": "original audit row order; equation permutation is explicitly mapped back",
        "selected_rows_original_indices": list(map(int, selected_rows)),
        "pivot_physical_dofs": [[int(node), int(dof)] for node, dof in pivot_dofs],
        "reference_source_load_correction": {
            "method": "F_ref = -E_emit^T F_pivot_emit, where E_emit are the serialized reference coefficients",
            "full_precision_identity": "E = -S^-1, so F_ref = (S^-1)^T F_pivot",
            "serialized_deck_values_populated_after_deck_emission": True,
            "policy": "Subtract transferred source CLOAD from raw scalar reference RF.",
            "observed_fixture_mapping": "RF_REFERENCE_MINUS_DEPENDENT_CLOAD",
            "observation_sources": [str(FLOOR_RF_RESULT), str(TRANSFORMED_FLOOR_RESULT)],
            "formula_scope": (
                "identity and nonidentity/permuted 2D known-answer MPC fixtures, "
                "plus the serialized full-frame H/S transformation audit"
            ),
        },
        "recovery_policy": (
            "For each selected source row k mapped back by selected_rows[k], "
            "R_tangent = RF(reference_node,1) - F_ref[k]; "
            "global floor force vector = R_tangent * owner_tangent_basis_global_xyz."
        ),
        "floor_reference_rows": floor_equations,
        "floor_condition": (
            "Conditional all-bearing exact-stick branch only. Every paired normal "
            "carrier must have strictly positive compression at every state used. "
            "Any open, zero-force, or nonpositive-force paired normal invalidates "
            "this branch; no release/recontact algorithm is supplied."
        ),
    }, equation_terms


def _spring_real_audit(deck: str) -> dict[str, Any]:
    lines = deck.splitlines()
    spring_headers = [index for index, line in enumerate(lines) if line.upper().startswith("*SPRING,")]
    linear_count = nonlinear_count = real_value_count = 0
    maximum_real_field_length = 0
    for index in spring_headers:
        header = lines[index].upper()
        is_nonlinear = "NONLINEAR" in header
        if is_nonlinear:
            nonlinear_count += 1
            data_rows = []
            for line in lines[index + 1 :]:
                if line.startswith("*"):
                    break
                if line.strip():
                    data_rows.append(line.strip())
            if len(data_rows) != 3:
                raise AdapterInputError("Each nonlinear SPRINGA table must have three data rows")
            for line in data_rows:
                cells = [cell.strip() for cell in line.split(",")]
                if len(cells) != 2:
                    raise AdapterInputError("Nonlinear spring table row must have force and elongation")
                for cell in cells:
                    if "." not in cell or len(cell) > 20:
                        raise AdapterInputError(f"SPRING real must include a decimal point and fit F20.0: {cell}")
                    real_value_count += 1
                    maximum_real_field_length = max(maximum_real_field_length, len(cell))
        else:
            linear_count += 1
            data_rows = []
            for line in lines[index + 1 :]:
                if line.startswith("*"):
                    break
                if line.strip():
                    data_rows.append(line.strip())
            if len(data_rows) != 2:
                raise AdapterInputError("Each linear SPRING2 group must have selector and stiffness rows")
            cells = [cell.strip() for cell in data_rows[1].split(",")]
            if len(cells) != 1 or "." not in cells[0] or len(cells[0]) > 20:
                raise AdapterInputError(f"Linear SPRING2 stiffness must be a decimal real: {data_rows[1]}")
            real_value_count += 1
            maximum_real_field_length = max(maximum_real_field_length, len(cells[0]))
    if linear_count != 348 or nonlinear_count != 1292:
        raise AdapterInputError(
            f"Unexpected deck spring counts: linear={linear_count}, nonlinear={nonlinear_count}"
        )
    return {
        "linear_spring2_property_groups": linear_count,
        "nonlinear_springa_property_groups": nonlinear_count,
        "spring_real_fields_checked": real_value_count,
        "spring_real_fields_all_have_decimal_points": True,
        "maximum_spring_real_field_length": maximum_real_field_length,
        "spring_real_field_width_limit": 20,
    }


def _normalize_linear_spring_real_tokens(deck: str) -> tuple[str, int]:
    lines = deck.splitlines()
    normalized = 0
    for index, line in enumerate(lines):
        if not line.upper().startswith("*SPRING,") or "NONLINEAR" in line.upper():
            continue
        data_indices = []
        cursor = index + 1
        while cursor < len(lines) and len(data_indices) < 2:
            if lines[cursor].strip().startswith("*"):
                break
            if lines[cursor].strip():
                data_indices.append(cursor)
            cursor += 1
        if len(data_indices) != 2:
            raise AdapterInputError("Linear spring card is missing its selector or stiffness data")
        cells = [cell.strip() for cell in lines[data_indices[1]].split(",")]
        if len(cells) != 1:
            raise AdapterInputError("Linear spring stiffness data must contain one real token")
        token = _decimal_point_real_token(cells[0])
        if token != cells[0]:
            lines[data_indices[1]] = token
            normalized += 1
    return "\n".join(lines) + "\n", normalized


def _parse_equation_cards(deck: str) -> list[list[tuple[int, int, float]]]:
    lines = deck.splitlines()
    equations: list[list[tuple[int, int, float]]] = []
    cursor = 0
    while cursor < len(lines):
        if lines[cursor].strip().upper() != "*EQUATION":
            cursor += 1
            continue
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            raise AdapterInputError("Truncated *EQUATION card before term count")
        try:
            term_count = int(lines[cursor].strip())
        except ValueError as exc:
            raise AdapterInputError("Invalid *EQUATION term count") from exc
        if term_count < 1:
            raise AdapterInputError("An emitted equation must have at least one term")
        cursor += 1
        values: list[str] = []
        while len(values) < 3 * term_count and cursor < len(lines):
            line = lines[cursor].strip()
            if line.startswith("*"):
                raise AdapterInputError("Truncated *EQUATION data before all terms")
            if line:
                values.extend(cell.strip() for cell in line.split(","))
            cursor += 1
        if len(values) != 3 * term_count:
            raise AdapterInputError("Emitted *EQUATION term count does not match data")
        try:
            equation = [
                (int(values[index]), int(values[index + 1]), float(values[index + 2]))
                for index in range(0, len(values), 3)
            ]
        except ValueError as exc:
            raise AdapterInputError("Invalid emitted *EQUATION term") from exc
        equations.append(equation)
    return equations


def _parse_emitted_cloads(deck: str) -> dict[tuple[int, int], float]:
    lines = deck.splitlines()
    loads: dict[tuple[int, int], float] = {}
    in_cload = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            in_cload = stripped.upper() == "*CLOAD"
            continue
        if not in_cload or not stripped:
            continue
        cells = [cell.strip() for cell in stripped.split(",")]
        if len(cells) != 3:
            raise AdapterInputError(f"Unexpected emitted *CLOAD row: {stripped}")
        try:
            key = (int(cells[0]), int(cells[1]))
            value = float(cells[2])
        except ValueError as exc:
            raise AdapterInputError(f"Invalid emitted *CLOAD row: {stripped}") from exc
        loads[key] = loads.get(key, 0.0) + value
    return loads


def _audit_emitted_source_loads(deck: str, structure: Any) -> dict[str, Any]:
    emitted = _parse_emitted_cloads(deck)
    expected: dict[tuple[int, int], float] = {}
    for node, vector in structure.loads.items():
        for dof, value in enumerate(vector, start=1):
            numeric = float(value)
            if abs(numeric) > 1e-14:
                expected[(int(node), dof)] = float(format(numeric, ".14g"))
    if emitted != expected:
        all_keys = set(emitted) | set(expected)
        maximum_difference = max(
            (abs(emitted.get(key, 0.0) - expected.get(key, 0.0)) for key in all_keys),
            default=0.0,
        )
        raise AdapterInputError(
            f"Serialized *CLOAD differs from freshly assembled current source loads; max={maximum_difference} N"
        )
    raw_nonzero = sum(
        abs(float(value)) > 1e-14
        for vector in structure.loads.values()
        for value in vector
    )
    return {
        "fresh_source_load_components_expected": int(raw_nonzero),
        "serialized_source_cload_components": len(emitted),
        "source_loads_round_trip_through_emitted_deck": True,
        "all_loads_are_from_fresh_case_reassembly": True,
        "historical_response_forces_read": False,
        "tolerance": "Exact equality to the emitted .14g source load token values; components <=1e-14 N are omitted by the existing deck writer.",
    }


def _coefficient_map(terms: list[tuple[int, int, float]]) -> dict[tuple[int, int], float]:
    result: dict[tuple[int, int], float] = {}
    for node, dof, coefficient in terms:
        key = (int(node), int(dof))
        result[key] = result.get(key, 0.0) + float(coefficient)
    return {key: value for key, value in result.items() if value != 0.0}


def _audit_emitted_floor_equations(
    deck: str,
    prepared_equation_terms: list[list[tuple[int, int, float]]],
    floor_references: list[dict[str, Any]],
    floor_audit: dict[str, Any],
    matrices_path: Path,
    original_equation_count: int,
) -> dict[str, Any]:
    equations = _parse_equation_cards(deck)
    start = original_equation_count
    actual_rows = equations[start : start + 200]
    if len(actual_rows) != 200:
        raise AdapterInputError("Could not locate all 200 serialized floor equations")
    if len(prepared_equation_terms) != 200:
        raise AdapterInputError("Prepared floor equation matrix does not cover 200 rows")

    matrix_archive = np.load(matrices_path)
    original_a = np.asarray(matrix_archive["original"], dtype=float)
    pivots = np.asarray(matrix_archive["pivots"], dtype=int)
    selected_rows = np.asarray(matrix_archive["selected_rows"], dtype=int)
    selected_a = original_a[selected_rows, :]
    pivot_block = selected_a[:, pivots]
    master_dofs = [tuple(map(int, item)) for item in floor_audit["physical_master_dofs"]]
    master_column = {key: index for index, key in enumerate(master_dofs)}
    reference_by_node = {int(row["node"]): row for row in floor_references}
    original_row_to_selected_position = {
        int(original_row): position for position, original_row in enumerate(selected_rows)
    }
    h_emitted = np.zeros((200, len(master_dofs)), dtype=float)
    e_emitted_selected = np.zeros((200, 200), dtype=float)
    actual_equation_term_count = 0
    expected_serialized_max_abs_difference = 0.0

    for row_index, (actual, expected_row) in enumerate(
        zip(actual_rows, prepared_equation_terms, strict=True)
    ):
        actual_equation_term_count += len(actual)
        actual_map = _coefficient_map(actual)
        expected_terms = [tuple(item) for item in expected_row]
        expected_serialized = {
            key: float(format(coefficient, ".14g"))
            for key, coefficient in _coefficient_map(expected_terms).items()
        }
        if set(actual_map) != set(expected_serialized):
            raise AdapterInputError(
                f"Serialized floor equation {row_index} has different retained terms from its prepared matrix"
            )
        expected_serialized_max_abs_difference = max(
            expected_serialized_max_abs_difference,
            max(
                abs(actual_map[key] - expected_serialized[key])
                for key in actual_map
            ),
        )
        pivot_key = tuple(map(int, floor_audit["pivot_physical_dofs"][row_index]))
        if actual[0][:2] != pivot_key or actual_map.get(pivot_key) != 1.0:
            raise AdapterInputError(f"Serialized floor equation {row_index} changed its physical pivot")
        for (node, dof), coefficient in actual_map.items():
            key = (node, dof)
            if key in master_column:
                h_emitted[row_index, master_column[key]] += coefficient
            elif node in reference_by_node and dof == 1:
                original_reference_row = int(reference_by_node[node]["source_row_original_index"])
                column = original_row_to_selected_position[original_reference_row]
                e_emitted_selected[row_index, column] += coefficient
            else:
                raise AdapterInputError(
                    f"Serialized floor equation contains an unclassified term {node}/{dof}"
                )

    reconstructed_selected = pivot_block @ h_emitted
    reconstructed_original = np.zeros_like(original_a)
    reconstructed_original[selected_rows, :] = reconstructed_selected
    h_residual = reconstructed_original - original_a
    inverse_reference_residual = pivot_block @ (-e_emitted_selected) - np.eye(200)

    emitted_cloads = _parse_emitted_cloads(deck)
    pivot_dofs = [tuple(map(int, item)) for item in floor_audit["pivot_physical_dofs"]]
    pivot_loads_emitted = np.asarray(
        [emitted_cloads.get(key, 0.0) for key in pivot_dofs], dtype=float
    )
    inverse_pivot_block = np.linalg.solve(pivot_block, np.eye(200, dtype=float))
    correction_selected_emitted = -(e_emitted_selected.T @ pivot_loads_emitted)
    correction_selected_full_precision = inverse_pivot_block.T @ pivot_loads_emitted
    correction_by_original_row = np.zeros(200, dtype=float)
    correction_full_by_original_row = np.zeros(200, dtype=float)
    for selected_position, original_row in enumerate(selected_rows):
        correction_by_original_row[int(original_row)] = correction_selected_emitted[selected_position]
        correction_full_by_original_row[int(original_row)] = correction_selected_full_precision[selected_position]
    for reference in floor_references:
        original_row = int(reference["source_row_original_index"])
        reference["source_load_correction_N"] = float(correction_by_original_row[original_row])
        reference["correction_from_full_precision_matrix_N"] = float(
            correction_full_by_original_row[original_row]
        )
        reference["correction_uses_emitted_equation_and_cload_values"] = True
    for row_index, row in enumerate(floor_audit["floor_reference_rows"]):
        row["reference_load_correction_N"] = float(correction_selected_emitted[row_index])
        row["source_pivot_CLOAD_N"] = float(pivot_loads_emitted[row_index])
        row["source_load_correction_source"] = "serialized equation coefficients and emitted source CLOAD"

    full_audit = floor_audit["reference_source_load_correction"]
    full_audit.update(
        {
            "method": "F_ref = -E_emit^T F_pivot_emit, using parsed serialized floor equations and *CLOAD",
            "full_precision_identity": "E=-S^-1, so the unrounded result is (S^-1)^T F_pivot",
            "pivot_CLOAD_N_in_selected_equation_order": pivot_loads_emitted.tolist(),
            "reference_CLOAD_N_in_selected_equation_order": correction_selected_emitted.tolist(),
            "reference_CLOAD_N_by_original_row_index": correction_by_original_row.tolist(),
            "full_precision_reference_CLOAD_N_by_original_row_index": correction_full_by_original_row.tolist(),
            "maximum_abs_serialized_vs_full_precision_reference_CLOAD_N": float(
                np.max(np.abs(correction_by_original_row - correction_full_by_original_row))
            ),
            "source_CLOADs_parsed_from_emitted_deck": True,
            "policy": "Subtract transferred source CLOAD from raw scalar reference RF.",
        }
    )
    return {
        "serialized_equation_count_total": len(equations),
        "serialized_floor_equation_count": len(actual_rows),
        "serialized_floor_equation_term_count": actual_equation_term_count,
        "serialized_equation_terms_match_prepared_matrix_after_14_digit_format": (
            expected_serialized_max_abs_difference == 0.0
        ),
        "maximum_abs_actual_vs_expected_serialized_coefficient": expected_serialized_max_abs_difference,
        "h_times_serialized_h_max_abs_reconstruction_residual": float(np.max(np.abs(h_residual))),
        "h_times_serialized_h_max_relative_reconstruction_residual": float(
            np.max(np.abs(h_residual)) / max(float(np.max(np.abs(original_a))), 1.0)
        ),
        "s_times_negative_serialized_reference_coefficients_max_abs_identity_residual": float(
            np.max(np.abs(inverse_reference_residual))
        ),
        "serialized_source_load_transfer": {
            "pivot_CLOAD_values_read_from_emitted_deck": True,
            "correction_derived_from_emitted_reference_coefficients": True,
            "maximum_abs_reference_load_difference_vs_full_precision_N": float(
                np.max(np.abs(correction_by_original_row - correction_full_by_original_row))
            ),
            "maximum_abs_transferred_reference_load_N": float(np.max(np.abs(correction_by_original_row))),
            "sum_abs_transferred_reference_load_N": float(np.sum(np.abs(correction_by_original_row))),
        },
        "reference_node_tags_unique": len(reference_by_node) == 200,
        "reference_node_tags_are_scalar_channels": all(
            int(reference["reference_dof"]) == 1 for reference in floor_references
        ),
    }


def _audit_serialized_qghost_equations(
    deck: str,
    bindings: list[dict[str, Any]],
    original_equation_count: int,
) -> dict[str, Any]:
    equations = _parse_equation_cards(deck)
    start = original_equation_count + 200
    expected_count = len(bindings) * 3
    actual = equations[start : start + expected_count]
    if len(actual) != expected_count:
        raise AdapterInputError("Could not locate all serialized SPRINGA qghost equations")
    expected_flat = [
        equation
        for binding in bindings
        for equation in binding["qghost_equations"]
    ]
    if len(expected_flat) != expected_count:
        raise AdapterInputError("SPRINGA qghost metadata does not contain three scalar rows per carrier")
    maximum_abs_coefficient_rounding = 0.0
    omitted_zero_component_count = 0
    for index, (actual_row, expected_row) in enumerate(zip(actual, expected_flat, strict=True)):
        expected_terms = [tuple(item) for item in expected_row["terms"]]
        expected_map = _coefficient_map(expected_terms)
        actual_map = _coefficient_map(actual_row)
        expected_serialized = {
            key: float(format(value, ".14g")) for key, value in expected_map.items()
        }
        if set(actual_map) != set(expected_serialized):
            raise AdapterInputError(
                f"Serialized qghost equation {index} differs in retained terms; actual={actual_map}, expected={expected_serialized}"
            )
        if actual_map != expected_serialized:
            raise AdapterInputError(f"Serialized qghost equation {index} did not preserve .14g coefficients")
        maximum_abs_coefficient_rounding = max(
            maximum_abs_coefficient_rounding,
            max((abs(actual_map[key] - expected_map[key]) for key in actual_map), default=0.0),
        )
        if len(actual_map) == 1:
            omitted_zero_component_count += 1
    return {
        "serialized_qghost_equation_count": len(actual),
        "qghost_equations_match_coefficient_maps_after_14_digit_format": True,
        "maximum_abs_qghost_coefficient_rounding": maximum_abs_coefficient_rounding,
        "axis_aligned_components_with_only_dependent_term": omitted_zero_component_count,
        "source_projection_ghosts_used": True,
    }


def _material_card_blocks(deck: str) -> list[str]:
    target = {
        "*MATERIAL",
        "*ELASTIC",
        "*DENSITY",
        "*ORIENTATION",
        "*SOLID SECTION",
        "*SHELL SECTION",
    }
    lines = deck.splitlines()
    blocks: list[str] = []
    cursor = 0
    while cursor < len(lines):
        line = lines[cursor].strip()
        if not line.startswith("*"):
            cursor += 1
            continue
        keyword = line.split(",", 1)[0].upper()
        if keyword not in target:
            cursor += 1
            continue
        block = [re.sub(r"\s+", "", line).upper()]
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip().startswith("*"):
            if lines[cursor].strip():
                block.append(re.sub(r"\s+", "", lines[cursor]).upper())
            cursor += 1
        blocks.append("\n".join(block))
    return blocks


def _audit_material_deck(source_deck_path: Path, emitted_deck: str) -> dict[str, Any]:
    source_deck = source_deck_path.read_text(encoding="utf-8")
    source_cards = _material_card_blocks(source_deck)
    emitted_cards = _material_card_blocks(emitted_deck)
    if source_cards != emitted_cards:
        raise AdapterInputError("Emitted material/orientation/solid-section cards differ from pinned C11 input")
    return {
        "source_deck_sha256": sha256(source_deck_path),
        "source_material_orientation_and_section_cards_sha256": hashlib.sha256(
            "\n\n".join(source_cards).encode("utf-8")
        ).hexdigest(),
        "emitted_material_orientation_and_section_cards_sha256": hashlib.sha256(
            "\n\n".join(emitted_cards).encode("utf-8")
        ).hexdigest(),
        "material_orientation_solid_section_cards_exactly_match_pinned_c11_input": True,
        "cards_checked": len(source_cards),
        "keywords_checked": [
            "*MATERIAL", "*ELASTIC", "*DENSITY", "*ORIENTATION", "*SOLID SECTION", "*SHELL SECTION"
        ],
    }


def _deck_text(
    structure: Any,
    material_binding: dict[str, Any],
    nonlinear_bindings: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    text = oriented_deck(structure, material_binding)
    old_step = "*STEP\n*STATIC\n"
    new_step = (
        "*STEP,NLGEOM,NLGEOM=NO,INC=40\n"
        "*STATIC\n"
        "0.1,1.0,1.e-6,0.25\n"
    )
    if text.count(old_step) != 1:
        raise AdapterInputError("Expected exactly one source static step before native adaptation")
    text = text.replace(old_step, new_step, 1)
    old_print = "*NODE PRINT,NSET=ALLN\nU,RF"
    new_print = "*NODE PRINT,NSET=ALLN,FREQUENCY=1\nU,RF"
    if text.count(old_print) != 1:
        raise AdapterInputError("Expected the source displacement/reaction print request")
    text = text.replace(old_print, new_print, 1)

    table_cards: list[str] = []
    for binding in nonlinear_bindings:
        stiffness = float(binding["stiffness_n_per_mm"])
        table_cards.extend(
            [
                f"*SPRING,ELSET={binding['group']},NONLINEAR",
                "",
                f"0.0,-10.0",
                "0.0,0.0",
                f"{ccx_real(10.0 * stiffness)},10.0",
            ]
        )
    marker = "*BOUNDARY\n"
    if text.count(marker) != 1:
        raise AdapterInputError("Expected one source boundary card")
    text = text.replace(marker, "\n".join(table_cards) + "\n" + marker, 1)

    text, normalized_linear_real_count = _normalize_linear_spring_real_tokens(text)

    spring_counts = _spring_real_audit(text)
    spring_counts["linear_spring_real_tokens_normalized_with_decimal_point"] = normalized_linear_real_count
    if text.count("*STEP,NLGEOM,NLGEOM=NO,INC=40") != 1:
        raise AdapterInputError("Newton-active, geometrically linear static step option was not preserved")
    if text.count("*NODE PRINT,NSET=ALLN,FREQUENCY=1\nU,RF") != 1:
        raise AdapterInputError("Deck does not request all-node displacement and reaction output")
    return text, spring_counts


def prepare() -> dict[str, Any]:
    source = _pin_inputs()
    structure, _panels, metadata = build_case(
        "a12-rear",
        accessory_scenario_id=None,
        mesh_size_mm=150.0,
        ring_case="A",
        panel_group_factor=1.0,
        hillman_axial_ratio=1.0,
        bolt_gap_factor=0.0,
        contact_penalty_n_per_mm3=100.0,
    )
    if (
        metadata["candidate"] != CANDIDATE
        or metadata["geometry_revision_id"] != GEOMETRY_REVISION
        or metadata["case_id"] != "a12-rear"
    ):
        raise AdapterInputError("Default reduced-case builder returned an unexpected source case")
    expected_scenario = {
        "mesh_size_mm": 150.0,
        "ring_case": "A",
        "panel_group_factor": 1.0,
        "hillman_axial_to_lateral_ratio": 1.0,
        "bolt_gap_factor": 0.0,
        "contact_penalty_n_per_mm3": 100.0,
        "accessory_scenario_id": None,
        "accessory_budget_kg": 0.0,
    }
    for key, value in expected_scenario.items():
        if metadata["scenario"].get(key) != value:
            raise AdapterInputError(f"Source scenario changed at {key}")

    base_record = record_structure(structure, metadata)
    geometry_rebinding = _validate_source_geometry(base_record, metadata, source["c11_model"])
    corner_contract_audit = _validate_corner_contract(source["corner_contract"], metadata)
    source_load_normalization_audit = _normalize_fresh_source_loads(structure, metadata)
    rows = source["carriers"]["rows"]
    carrier_by_group, carrier_audit = _validate_carrier_inventory(
        rows, structure, metadata, source["carriers"]
    )
    source_spring_rows = copy.deepcopy(structure.springs)
    source_spring_groups = {str(row["group"]): row for row in source_spring_rows}
    original_nodes = len(structure.nodes)
    original_node_tags = set(map(int, structure.nodes))
    original_equations = len(structure.equations)

    floor_references, floor_audit, prepared_floor_equation_terms = _build_floor_equations(
        structure, rows, source["floor_audit"], ROOT / FLOOR_MATRICES
    )
    if len(floor_references) != 200:
        raise AdapterInputError("Expected 200 exact floor reference nodes")
    floor_reference_tags = [int(row["node"]) for row in floor_references]
    if (
        len(set(floor_reference_tags)) != 200
        or set(floor_reference_tags) & original_node_tags
        or min(floor_reference_tags) <= max(original_node_tags)
    ):
        raise AdapterInputError("Floor references must use 200 fresh, unique scalar node tags")

    nonlinear_bindings: list[dict[str, Any]] = []
    removed_floor_groups: set[str] = set()
    numerical_ground_nodes: list[dict[str, Any]] = []
    qghost_node_tags: list[int] = []
    for group, carrier in carrier_by_group.items():
        law = str(carrier["intended_law"])
        spring = source_spring_groups[group]
        element = int(spring["element"])
        if law in ("compression_only", "tension_only"):
            owner = carrier["physical_owner"]
            axis = np.asarray(owner["scalar_normal"], dtype=float)
            if axis.shape != (3,) or not np.isclose(np.linalg.norm(axis), 1.0, atol=1e-10, rtol=0.0):
                raise AdapterInputError(f"Nonlinear source axis is not a unit vector: {group}")
            first, second = map(int, carrier["nodes"])
            point = np.asarray(owner["point"], dtype=float)
            if point.shape != (3,) or not np.isfinite(point).all():
                raise AdapterInputError(f"Nonlinear owner point is invalid: {group}")
            q_node = structure.node((point + 100.0 * axis).tolist())
            ground_node = structure.node(point.tolist())
            qghost_node_tags.append(int(q_node))
            structure.fixed.add(ground_node)
            structure.elements[element] = ("SPRINGA", [q_node, ground_node], group)
            dof = int(carrier["dof"])
            qghost_equations: list[dict[str, Any]] = []
            for global_dof, axis_component in enumerate(axis.tolist(), start=1):
                terms = [(q_node, global_dof, 1.0)]
                if abs(float(axis_component)) > 1e-14:
                    terms.extend(
                        [
                            (second, dof, -float(axis_component)),
                            (first, dof, float(axis_component)),
                        ]
                    )
                structure.equations.append(terms)
                qghost_equations.append(
                    {
                        "dependent_q_dof": [q_node, global_dof],
                        "terms": [[n, d, coefficient] for n, d, coefficient in terms],
                    }
                )
            binding = {
                "name": str(carrier["name"]),
                "group": group,
                "source_row_id": group,
                "source_inventory_row_index": int(carrier["_adapter_source_row_index"]),
                "source_element": element,
                "springa_nodes": [q_node, ground_node],
                "source_projection_nodes": [first, second],
                "source_projection_dof": dof,
                "relative_coordinate": (
                    f"u(second projection,{dof}) - u(first projection,{dof})"
                ),
                "q_elongation_mm": "u(second projection)-u(first projection)",
                "initial_span_mm": 100.0,
                "numerical_axis_global_xyz": axis.tolist(),
                "physical_action_on_first_body": {
                    "sign": 1,
                    "unit_direction_global_xyz": axis.tolist(),
                    "formula": "native_internal_force_N * preserved scalar_normal",
                },
                "physical_action_on_second_body": {
                    "sign": -1,
                    "unit_direction_global_xyz": axis.tolist(),
                    "formula": "equal and opposite to first-body action",
                },
                "physical_owner": copy.deepcopy(owner),
                "physical_force_on_first_body": (
                    "native internal force times preserved scalar_normal"
                ),
                "physical_force_on_second_body": (
                    "equal and opposite; numerical spring ground RF is excluded"
                ),
                "stiffness_n_per_mm": float(carrier["stiffness_n_per_mm"]),
                "force_law": "k * max(q_mm, 0)",
                "force_vs_elongation_table_N_mm": [
                    [0.0, -10.0],
                    [0.0, 0.0],
                    [float(10.0 * carrier["stiffness_n_per_mm"]), 10.0],
                ],
                "table_domain_mm": [-10.0, 10.0],
                "future_response_domain_gate": (
                    "Reject any solved elongation outside [-10,+10] mm; "
                    "do not rely on CalculiX table extrapolation."
                ),
                "q_endpoint_components_use_projection_ghosts": True,
                "qghost_equations": qghost_equations,
                "ground_endpoint_is_numerical_only": True,
                "historical_active_state_used": False,
            }
            nonlinear_bindings.append(binding)
            numerical_ground_nodes.append(
                {
                    "node": ground_node,
                    "spring_group": group,
                    "role": "numerical SPRINGA ground; RF excluded from physical balance",
                    "xyz_mm": point.tolist(),
                }
            )
        elif law == "floor_tangent_all_bearing_hypothesis":
            removed_floor_groups.add(group)
            structure.elements.pop(element)
            structure.groups.pop(group, None)
        elif law == "bilateral":
            pass
        else:
            raise AdapterInputError(f"Unrecognized source spring law: {law}")

    structure.springs = [
        spring for spring in source_spring_rows
        if carrier_by_group[str(spring["group"])]["intended_law"] == "bilateral"
    ]
    if len(nonlinear_bindings) != 1292 or len(removed_floor_groups) != 200:
        raise AdapterInputError("SPRINGA conversion or exact floor tangent replacement is incomplete")

    if len(structure.springs) != 348:
        raise AdapterInputError("The 348 bilateral source SPRING2 rows were not preserved")

    numerical_ground_tags = [int(row["node"]) for row in numerical_ground_nodes]
    if (
        len(qghost_node_tags) != 1292
        or len(set(qghost_node_tags)) != 1292
        or len(numerical_ground_tags) != 1292
        or len(set(numerical_ground_tags)) != 1292
        or set(qghost_node_tags) & set(numerical_ground_tags)
        or set(qghost_node_tags) & original_node_tags
        or set(numerical_ground_tags) & original_node_tags
        or set(floor_reference_tags) & (set(qghost_node_tags) | set(numerical_ground_tags))
    ):
        raise AdapterInputError("SPRINGA ghosts, numerical grounds, and floor refs need disjoint fresh tags")

    output_metadata = copy.deepcopy(metadata)
    output_metadata.update(
        {
            "schema": MODEL_SCHEMA,
            "scope": (
                "Input-only stock-CalculiX carrier adapter for one freshly rebuilt "
                "a12-rear source case; no frame response or joint acceptance."
            ),
            "input_adapter_status": "ASSEMBLED_INPUT_ONLY",
            "legacy_reduced_static_linear_response_schema_compatible": False,
            "source_response_schema": "current_springa_frame_input_model/v1",
            "native_carrier_model_schema": MODEL_SCHEMA,
            "input_only": True,
            "native_solve_executed": False,
            "mechanical_acceptance": False,
            "qualified_for_design": False,
            "complete_joint_validated": False,
            "frame_ready_for_native_run": False,
            "source_geometry_rebinding": geometry_rebinding,
            "source_inventory_audit": carrier_audit,
            "corner_demand_contract_audit": corner_contract_audit,
            "source_load_normalization_audit": source_load_normalization_audit,
            "nonlinear_native_carrier_bindings": nonlinear_bindings,
            "numerical_spring_ground_nodes": numerical_ground_nodes,
            "floor_reference_nodes": floor_references,
            "floor_constraint_audit": floor_audit,
            "source_carrier_inventory_rows": copy.deepcopy(rows),
            "response_route": {
            "native_force_output_method_fixtures_passed": True,
            "known_springa_reference": str(SPRINGA_RESULT),
            "known_floor_reference_rf": "RF_REFERENCE_MINUS_DEPENDENT_CLOAD",
            "known_floor_reference_source": str(FLOOR_RF_RESULT),
            "known_transformed_floor_reference_source": str(TRANSFORMED_FLOOR_RESULT),
                "whole_frame_source_audited_response_route_implemented": False,
                "frame_ready_for_native_run": False,
                "mechanical_acceptance": False,
            },
            "load_case_scope": {
                "case_id": "a12-rear",
                "all_six_source_load_cases_assembled": False,
                "primary_corner_demands_requested": ["BG001", "BG003", "BG045"],
                "corner_demands_extracted": False,
                "next_parent_gate": (
                    "Review this one input and implement/verify source-audited "
                    "response recovery before any frame native run."
                ),
            },
            "claim_limits": [
                "The C11 SHA binds source geometry only; its rejected forces and active states are not reused.",
                "The 92 new and 12 retained bolt axes remain distinct; no historical bolt resistance pass is transferred.",
                "All 66 current Hillman axes remain preserved; their parametric tension rows are not qualifying screw properties.",
                "The exact tangential floor constraint is conditional on strictly positive paired normal force at every relevant state.",
                "No floor anchor, verified floor, friction test, actual material inspection, member capacity, or complete-joint acceptance is established.",
            ],
        }
    )

    deck, spring_real_audit = _deck_text(
        structure, metadata["material_binding"], nonlinear_bindings
    )
    material_deck_audit = _audit_material_deck(ROOT / C11_DECK, deck)
    source_load_emission_audit = _audit_emitted_source_loads(deck, structure)
    serialized_floor_audit = _audit_emitted_floor_equations(
        deck,
        prepared_floor_equation_terms,
        floor_references,
        floor_audit,
        ROOT / FLOOR_MATRICES,
        original_equations,
    )
    serialized_qghost_audit = _audit_serialized_qghost_equations(
        deck, nonlinear_bindings, original_equations
    )
    floor_audit["serialized_deck_equation_audit"] = serialized_floor_audit
    floor_audit["floor_reference_nodes_unique_and_fresh"] = True
    floor_audit["floor_reference_node_count"] = len(floor_references)
    output_metadata["floor_constraint_audit"] = floor_audit
    output_metadata["source_load_emission_audit"] = source_load_emission_audit
    output_metadata["material_deck_audit"] = material_deck_audit
    output_metadata["serialized_qghost_equation_audit"] = serialized_qghost_audit

    record = record_structure(structure, output_metadata)
    record["schema"] = MODEL_SCHEMA
    record["springs"] = []
    for spring in structure.springs:
        source_row = carrier_by_group[str(spring["group"])]
        record["springs"].append(
            {
                **{key: value for key, value in spring.items() if key != "active"},
                "source_row_id": str(spring["group"]),
                "source_inventory_row_index": int(source_row["_adapter_source_row_index"]),
                "intended_law": str(source_row["intended_law"]),
                "role": str(source_row["role"]),
                "physical_owner": copy.deepcopy(source_row["physical_owner"]),
            }
        )
    element_kinds = Counter(element[0] for element in structure.elements.values())
    record["adapted_element_kind_counts"] = dict(sorted(element_kinds.items()))
    record["source_spring_counts"] = {
        "source_scalar_rows": len(source_spring_rows),
        "converted_to_springa": len(nonlinear_bindings),
        "retained_bilateral_spring2": len(structure.springs),
        "removed_floor_tangent_spring2": len(removed_floor_groups),
    }
    record["source_geometry_hashes"] = copy.deepcopy(metadata["source_sha256"])
    record["source_model_pin"] = geometry_rebinding
    record["corner_demand_contract_audit"] = corner_contract_audit
    record["source_load_normalization_audit"] = source_load_normalization_audit
    record["material_deck_audit"] = material_deck_audit
    record["source_load_emission_audit"] = source_load_emission_audit
    record["serialized_qghost_equation_audit"] = serialized_qghost_audit
    record["unilateral_springa_bindings"] = nonlinear_bindings
    record["floor_reference_nodes_and_load_map"] = floor_references
    record["exact_floor_mpc_equations"] = floor_audit["floor_reference_rows"]
    record["raw_source_carrier_law_inventory_rows"] = copy.deepcopy(rows)
    record["legacy_reduced_static_linear_response_schema_compatible"] = False

    if len(structure.nodes) != original_nodes + 2 * len(nonlinear_bindings) + 200:
        raise AdapterInputError("Numerical carrier/reference node accounting changed")
    if len(structure.equations) != original_equations + 3 * len(nonlinear_bindings) + 200:
        raise AdapterInputError("Projection-ghost or exact floor equation accounting changed")
    if element_kinds["SPRINGA"] != 1292 or element_kinds["SPRING2"] != 348:
        raise AdapterInputError(f"Unexpected adapted element kinds: {dict(element_kinds)}")
    if not (set(removed_floor_groups) & set(source_spring_groups)):
        raise AdapterInputError("No original floor tangent groups were removed")

    CASE_DIR.mkdir(parents=True, exist_ok=True)
    (CASE_DIR / "model.inp").write_text(deck, encoding="utf-8")
    write_json(CASE_DIR / "model.json", record)
    output_hashes = {
        "model.inp": sha256(CASE_DIR / "model.inp"),
        "model.json": sha256(CASE_DIR / "model.json"),
    }
    source_pins = {
        "schema": "current_springa_frame_input_source_pins/v1",
        "pinned_inputs": source["pinned_sources"],
        "adapter_script_sha256": sha256(HERE / "prepare.py"),
        "output_deck_sha256": output_hashes["model.inp"],
        "output_model_sha256": output_hashes["model.json"],
        "scope": "Input-only a12-rear source rebind; no native response output is pinned or reused.",
    }
    write_json(HERE / "source-pins.json", source_pins)
    audit = {
        "schema": "current_springa_frame_input_adapter_audit/v1",
        "model_schema": MODEL_SCHEMA,
        "status": "PASS_INPUT_ASSEMBLY_METHODS_BOUND_RESPONSE_READINESS_BLOCKED",
        "candidate": CANDIDATE,
        "geometry_revision_id": GEOMETRY_REVISION,
        "case_id": "a12-rear",
        "input_only": True,
        "native_solve_executed": False,
        "source_response_forces_read": False,
        "historical_active_states_reused": False,
        "source_geometry_rebinding": geometry_rebinding,
        "source_carrier_inventory": carrier_audit,
        "corner_demand_contract": corner_contract_audit,
        "source_load_normalization_audit": source_load_normalization_audit,
        "exact_floor_constraint_audit": {
            key: value for key, value in floor_audit.items()
            if key not in ("floor_reference_rows",)
        },
        "serialized_floor_equation_audit": serialized_floor_audit,
        "serialized_qghost_equation_audit": serialized_qghost_audit,
        "material_deck_audit": material_deck_audit,
        "source_load_emission_audit": source_load_emission_audit,
        "deck_real_format_audit": spring_real_audit,
        "element_counts": dict(sorted(element_kinds.items())),
        "node_count": len(structure.nodes),
        "equation_count": len(structure.equations),
        "source_equation_count": original_equations,
        "added_relative_springa_equation_count": 3 * len(nonlinear_bindings),
        "added_exact_floor_equation_count": 200,
        "source_load_count": len(structure.loads),
        "source_case_reassembly": {
            "mesh_size_mm": 150.0,
            "ring_case": "A",
            "panel_group_factor": 1.0,
            "hillman_axial_to_lateral_ratio": 1.0,
            "bolt_gap_factor": 0.0,
            "contact_penalty_n_per_mm3": 100.0,
            "accessory_scenario_id": None,
            "accessory_budget_kg": 0.0,
            "physical_body_count": len(metadata["physical_body_nodes"]),
            "case_assembly_audit": metadata["case_assembly_audit"],
        },
        "method_evidence": {
            "relative_springa": {
                "path": str(SPRINGA_RESULT),
                "sha256": PINNED_SHA256[str(SPRINGA_RESULT)],
                "status": source["springa_result"]["status"],
                "scope": "Two moving bodies with nested projection ghosts; method only.",
            },
            "exact_floor_reference_rf": {
                "path": str(FLOOR_RF_RESULT),
                "sha256": PINNED_SHA256[str(FLOOR_RF_RESULT)],
                "status": source["floor_rf_result"]["status"],
                "mapping": source["floor_rf_result"]["floor_tangential_reaction_mapping"],
                "scope": "One scalar exact-stick known answer; method only.",
            },
            "transformed_floor_reference_rf": {
                "path": str(TRANSFORMED_FLOOR_RESULT),
                "sha256": PINNED_SHA256[str(TRANSFORMED_FLOOR_RESULT)],
                "status": source["transformed_floor_result"]["status"],
                "selected_source_rows_zero_based": source["transformed_floor_result"][
                    "selected_source_rows_zero_based"
                ],
                "reaction_mapping": source["transformed_floor_result"]["reaction_mapping"],
                "scope": "Nonidentity 2x2 transformed constraint with row permutation; fixture only.",
            },
        },
        "output_files_sha256": output_hashes,
        "source_pins_json_sha256": sha256(HERE / "source-pins.json"),
        "readiness": {
            "source_input_and_geometry_bound": True,
            "native_springa_carrier_method_fixture_passed": True,
            "exact_floor_reference_reaction_method_fixture_passed": True,
            "source_audited_whole_frame_response_route": False,
            "six_case_source_demands_complete": False,
            "paired_floor_normal_states_verified": False,
            "frame_ready_for_native_run": False,
            "joint_demand_accepted": False,
        },
        "limitations": [
            "Only one a12-rear input is assembled; no six-case frame responses or BG001/BG003/BG045 demands are produced.",
            "Solver convergence is not joint acceptance. This packet has no freeze, native output, response assessor, or capacity comparison.",
            "The reference source-load correction is derived from the serialized constraint coefficients and current deck CLOAD; raw reference RF values still require source-audited recovery for each future state.",
            "Any zero, open, or nonpositive force in a paired floor normal invalidates the conditional all-bearing tangent branch.",
            "The 100 mm SPRINGA spans and fixed numerical qgrounds are numerical devices; exclude their RF values from physical force balance.",
            "Floor reference nodes are scalar reaction channels at owner floor-point/tangent bases; they are not anchors or inspected floor points.",
            "Twelve retained bolt geometries are starting arrangements only; no blanket old-bolt qualification is implied.",
        ],
    }
    write_json(CASE_DIR / "audit.json", audit)
    return audit


if __name__ == "__main__":
    result = prepare()
    print(
        json.dumps(
            {
                "status": result["status"],
                "case": result["case_id"],
                "element_counts": result["element_counts"],
                "frame_ready_for_native_run": result["readiness"]["frame_ready_for_native_run"],
                "native_solve_executed": result["native_solve_executed"],
            },
            indent=2,
        )
    )
