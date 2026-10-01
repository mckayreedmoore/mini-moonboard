"""Recover physical owned forces from the revised SPRINGA frame adapter.

This module reads a model record, its input deck, and native DAT text. It never
launches a solver. SPRINGA table forces are checked against actual endpoint
length change (dd-dd0), with its signed projection MPC audited separately;
they are not screened with the legacy SPRING2 K*du auditor. The 348 retained
bilateral SPRING2 components keep their own native endpoint and K*du check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

map_physical_forces = importlib.import_module("fea.current_response_run").physical_forces
_balance = importlib.import_module("fea.wood_joint_reduced_response")._balance


SCHEMA = "current_springa_frame_physical_response_audit/v1"
SOURCE_LAWS = {
    "compression_only": 1122,
    "tension_only": 170,
    "bilateral": 348,
    "floor_tangent_all_bearing_hypothesis": 200,
}
MPC_INTERVAL_TOL_MM = 1.0e-5
BALANCE_FORCE_TOL_N = 0.1
BALANCE_MOMENT_TOL_NMM = 2.0


class ResponseAuditError(ValueError):
    """Raised when the recorded source, native output, or force map is invalid."""


def _number(token: str) -> float:
    return float(token.replace("D", "E").replace("d", "e"))


def _half_last_place(token: str) -> float:
    """Half one unit in the last printed decimal place, including E/D notation."""
    normalized = token.upper().replace("D", "E")
    if "E" in normalized:
        mantissa, exponent = normalized.split("E", 1)
        exponent_value = int(exponent)
    else:
        mantissa, exponent_value = normalized, 0
    decimal_places = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    return 0.5 * 10.0 ** (exponent_value - decimal_places)


_CCX223_E13_6_TOKEN = re.compile(r"^[+-]?\d\.\d{6}E[+-]\d{2}$")
_CCX223_ZERO_E13_6_TOKEN = re.compile(r"^[+-]?0\.000000E\+00$")


def _strict_ccx223_e13_6_value(token: str) -> float:
    """Reject DAT fields outside the pinned CCX 2.23 E13.6 output grammar."""
    if not _CCX223_E13_6_TOKEN.fullmatch(token):
        raise ResponseAuditError(f"Unrecognized CCX 2.23 E13.6 numeric token: {token!r}")
    value = _number(token)
    if not math.isfinite(value):
        raise ResponseAuditError(f"Non-finite CCX 2.23 E13.6 numeric token: {token!r}")
    return value


def _u_token_radius(token: str) -> float:
    """Use exact DAT zero only for canonical all-zero U output fields."""
    value = _strict_ccx223_e13_6_value(token)
    if value == 0.0:
        if not _CCX223_ZERO_E13_6_TOKEN.fullmatch(token):
            raise ResponseAuditError(f"Unrecognized zero-valued U token: {token!r}")
        return 0.0
    return _half_last_place(token)


def parse_native_blocks(data: str) -> dict[float, dict[str, Any]]:
    """Parse every CalculiX nodal U/RF block and retain token rounding radii."""
    pattern = re.compile(
        r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n",
        re.MULTILINE,
    )
    staged: dict[float, dict[str, Any]] = defaultdict(dict)
    for match in pattern.finditer(data):
        kind = "u" if match.group(1).lower() == "displacements" else "rf"
        time = _number(match.group(2))
        if kind in staged[time]:
            raise ResponseAuditError(f"Duplicate native {kind.upper()} block at time {time}")
        values: dict[int, list[float]] = {}
        radii: dict[int, list[float]] = {}
        started = False
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                if node in values:
                    raise ResponseAuditError(f"Duplicate node {node} in {kind.upper()} block at time {time}")
                values[node] = [_strict_ccx223_e13_6_value(token) for token in fields[1:]]
                if kind == "u":
                    radii[node] = [_u_token_radius(token) for token in fields[1:]]
                else:
                    radii[node] = [_half_last_place(token) for token in fields[1:]]
                started = True
            elif started:
                break
        if not values:
            raise ResponseAuditError(f"Empty native {kind.upper()} block at time {time}")
        staged[time][kind] = values
        staged[time][kind + "_radius"] = radii
    if not staged:
        raise ResponseAuditError("Native DAT contains no nodal displacement/reaction blocks")
    result: dict[float, dict[str, Any]] = {}
    for time, blocks in sorted(staged.items()):
        if set(blocks) != {"u", "u_radius", "rf", "rf_radius"}:
            raise ResponseAuditError(f"Native DAT has an unmatched U/RF pair at time {time}")
        if set(blocks["u"]) != set(blocks["rf"]):
            raise ResponseAuditError(f"U/RF node inventories differ at time {time}")
        result[time] = blocks
    return result


def _eq_json(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(
        right, sort_keys=True, separators=(",", ":")
    )


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _parse_equation_cards(deck: str) -> list[list[list[float]]]:
    lines = deck.splitlines()
    equations: list[list[list[float]]] = []
    cursor = 0
    while cursor < len(lines):
        if lines[cursor].strip().upper() != "*EQUATION":
            cursor += 1
            continue
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            raise ResponseAuditError("Truncated emitted *EQUATION card")
        try:
            term_count = int(lines[cursor].strip())
        except ValueError as error:
            raise ResponseAuditError("Invalid emitted *EQUATION term count") from error
        cursor += 1
        fields: list[str] = []
        while len(fields) < 3 * term_count and cursor < len(lines):
            line = lines[cursor].strip()
            if line.startswith("*"):
                raise ResponseAuditError("Truncated emitted *EQUATION terms")
            if line:
                fields.extend(part.strip() for part in line.split(","))
            cursor += 1
        if len(fields) != 3 * term_count:
            raise ResponseAuditError("Emitted *EQUATION term count does not match its data")
        try:
            equations.append([
                [int(fields[i]), int(fields[i + 1]), _number(fields[i + 2])]
                for i in range(0, len(fields), 3)
            ])
        except ValueError as error:
            raise ResponseAuditError("Malformed emitted *EQUATION term") from error
    return equations


def _parse_cload_cards(deck: str) -> dict[tuple[int, int], float]:
    result: dict[tuple[int, int], float] = defaultdict(float)
    in_cload = False
    for line in deck.splitlines():
        value = line.strip()
        if value.startswith("*"):
            in_cload = value.upper() == "*CLOAD"
            continue
        if not in_cload or not value:
            continue
        fields = [part.strip() for part in value.split(",")]
        if len(fields) != 3:
            raise ResponseAuditError(f"Malformed emitted *CLOAD row: {value}")
        key = (int(fields[0]), int(fields[1]))
        result[key] += _number(fields[2])
    return dict(result)


def _parse_node_cards(deck: str) -> dict[int, np.ndarray]:
    """Read coordinates exactly as emitted to the native input deck."""
    result: dict[int, np.ndarray] = {}
    in_nodes = False
    for line in deck.splitlines():
        value = line.strip()
        if value.startswith("*"):
            in_nodes = value.upper() == "*NODE" or value.upper().startswith("*NODE,")
            continue
        if not in_nodes or not value or value.startswith("**"):
            continue
        fields = [part.strip() for part in value.split(",")]
        if len(fields) != 4:
            raise ResponseAuditError(f"Malformed emitted *NODE row: {value}")
        node = int(fields[0])
        if node in result:
            raise ResponseAuditError(f"Duplicate node {node} in emitted input deck")
        result[node] = np.asarray([_number(token) for token in fields[1:]], dtype=float)
    if not result:
        raise ResponseAuditError("Emitted input deck has no *NODE coordinates")
    return result


def _validate_input_contract(record: dict[str, Any], deck: str) -> dict[str, Any]:
    """Reject baseline/legacy records and verify exact source-row coverage."""
    if record.get("schema") != "current_springa_frame_input_model/v1":
        raise ResponseAuditError("Input is not the revised current SPRINGA frame model schema")
    if record.get("legacy_reduced_static_linear_response_schema_compatible") is not False:
        raise ResponseAuditError("Legacy reduced-static linear response schema must be explicitly incompatible")
    if record.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ResponseAuditError("Input is not the selected wood-joints development candidate")
    if record.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ResponseAuditError("Input is not bound to the reviewed current geometry revision")
    if record.get("input_adapter_status") != "ASSEMBLED_INPUT_ONLY":
        raise ResponseAuditError("Input is not the revised input-only SPRINGA adapter record")
    required = (
        "raw_source_carrier_law_inventory_rows",
        "unilateral_springa_bindings",
        "floor_reference_nodes_and_load_map",
        "floor_constraint_audit",
        "springs",
        "connection_ownership",
        "physical_body_nodes",
        "physical_body_loads",
        "physical_external_loads",
        "source_load_normalization_audit",
        "nodes",
        "elements",
        "equations",
        "source_load_emission_audit",
    )
    missing = [key for key in required if key not in record]
    if missing:
        raise ResponseAuditError("SPRINGA response schema is missing: " + ", ".join(missing))
    if record.get("native_solve_executed") is not False:
        raise ResponseAuditError("Adapter input must remain an input-only, unsolved model record")
    if record.get("input_only") is not True or record.get("frame_ready_for_native_run") is not False:
        raise ResponseAuditError("Adapter record must remain input-only and explicitly not ready for a frame launch")
    normalization = record["source_load_normalization_audit"]
    for key in ("structure_loads_normalized_to_fresh_physical_external_map",
                "expanded_map_matches_fresh_physical_external_loads",
                "raw_and_expanded_wrench_transfer_passed"):
        if normalization.get(key) is not True:
            raise ResponseAuditError(f"Fresh source-load normalization proof failed: {key}")
    if normalization.get("historical_response_forces_read") is not False or record.get("source_response_forces_read", False) is True:
        raise ResponseAuditError("Historical response forces cannot be used as source-load evidence")
    if record["source_load_emission_audit"].get("source_loads_round_trip_through_emitted_deck") is not True:
        raise ResponseAuditError("The final model loads were not certified against emitted *CLOAD cards")
    if "wood_joint_reduced_rf_force_recovery/v1" in str(record.get("response_route", {})):
        raise ResponseAuditError("Legacy linear RF auditor cannot assess a nonlinear-carrier record")

    emitted_nodes = _parse_node_cards(deck)
    declared_nodes = {int(node): np.asarray(point, dtype=float) for node, point in record["nodes"].items()}
    if set(emitted_nodes) != set(declared_nodes):
        raise ResponseAuditError("Emitted *NODE inventory differs from the source model record")
    node_position_tolerance = 1.0e-12
    if any(not np.allclose(emitted_nodes[node], declared_nodes[node], rtol=0.0,
                           atol=node_position_tolerance + np.abs(declared_nodes[node]) * 1.0e-13)
           for node in declared_nodes):
        raise ResponseAuditError("Emitted *NODE positions differ from source coordinates beyond .14g precision")

    emitted_cloads = _parse_cload_cards(deck)
    declared_loads: dict[tuple[int, int], float] = {}
    for node, vector in record["loads"].items():
        for dof, value in enumerate(vector, start=1):
            if abs(float(value)) > 1.0e-14:
                declared_loads[(int(node), dof)] = float(value)
    if set(emitted_cloads) != set(declared_loads) or any(
        abs(emitted_cloads[key] - declared_loads[key]) > max(1.0e-10, abs(declared_loads[key]) * 1.0e-13)
        for key in declared_loads
    ):
        raise ResponseAuditError("Final model loads differ from serialized deck *CLOAD values")
    body_loads_from_emission: dict[int, np.ndarray] = defaultdict(lambda: np.zeros(3))
    for (node, dof), value in emitted_cloads.items():
        body_loads_from_emission[node][dof - 1] += value
    external = {int(node): np.asarray(force, dtype=float) for node, force in record["physical_external_loads"].items()}
    if set(body_loads_from_emission) != set(external) or any(
        not np.allclose(body_loads_from_emission[node], external[node], rtol=0.0, atol=1.0e-9)
        for node in external
    ):
        raise ResponseAuditError("Emitted *CLOADs differ from the normalized physical source-load inventory")

    emitted_equations = _parse_equation_cards(deck)
    if len(emitted_equations) != len(record["equations"]):
        raise ResponseAuditError("Emitted *EQUATION count differs from the response model record")
    for index, (emitted, recorded) in enumerate(zip(emitted_equations, record["equations"], strict=True)):
        if len(emitted) != len(recorded) or any(
            int(actual[0]) != int(expected[0]) or int(actual[1]) != int(expected[1])
            or abs(float(actual[2]) - float(expected[2])) > max(1.0e-12, abs(float(expected[2])) * 1.0e-13)
            for actual, expected in zip(emitted, recorded, strict=True)
        ):
            raise ResponseAuditError(f"Emitted *EQUATION row {index} differs from its source model record")

    source_rows = record["raw_source_carrier_law_inventory_rows"]
    law_counts = Counter(str(row["intended_law"]) for row in source_rows)
    if len(source_rows) != 1840 or dict(law_counts) != SOURCE_LAWS:
        raise ResponseAuditError(f"Unexpected source carrier law inventory: {dict(law_counts)}")
    by_group: dict[str, dict[str, Any]] = {}
    source_index_by_group: dict[str, int] = {}
    for source_index, row in enumerate(source_rows):
        group = str(row["group"])
        if group in by_group:
            raise ResponseAuditError(f"Duplicate source carrier group {group}")
        by_group[group] = row
        source_index_by_group[group] = source_index

    bindings = record["unilateral_springa_bindings"]
    springs = record["springs"]
    if len(bindings) != 1292 or len(springs) != 348:
        raise ResponseAuditError(
            f"Expected 1,292 SPRINGA bindings and 348 retained SPRING2 rows; got {len(bindings)}/{len(springs)}"
        )
    bound_groups: set[str] = set()
    for binding in bindings:
        group = str(binding["group"])
        index = int(binding["source_inventory_row_index"])
        if not 0 <= index < len(source_rows) or str(source_rows[index]["group"]) != group:
            raise ResponseAuditError(f"SPRINGA source-index mapping changed at {group}")
        source = by_group.get(group)
        if source is None or source["intended_law"] not in ("compression_only", "tension_only"):
            raise ResponseAuditError(f"SPRINGA binding has no matching unilateral source row: {group}")
        if str(binding["source_row_id"]) != group:
            raise ResponseAuditError(f"SPRINGA source-row identity changed at {group}")
        if group in bound_groups:
            raise ResponseAuditError(f"Duplicate SPRINGA source binding {group}")
        bound_groups.add(group)
        for key in ("name", "source_element", "source_projection_nodes", "source_projection_dof",
                    "springa_nodes", "stiffness_n_per_mm", "physical_owner"):
            source_key = {"source_element": "element"}.get(key, key)
            if key in ("source_projection_nodes", "source_projection_dof", "springa_nodes"):
                continue
            if source_key in source and key in binding:
                if key == "stiffness_n_per_mm":
                    if not math.isclose(float(binding[key]), float(source[source_key]), rel_tol=1e-12, abs_tol=1e-12):
                        raise ResponseAuditError(f"SPRINGA stiffness changed at {group}")
                elif not _eq_json(binding[key], source[source_key]):
                    raise ResponseAuditError(f"SPRINGA source {key} changed at {group}")
        if list(map(int, binding["source_projection_nodes"])) != list(map(int, source["nodes"])):
            raise ResponseAuditError(f"SPRINGA source projection nodes changed at {group}")
        if int(binding["source_projection_dof"]) != int(source["dof"]):
            raise ResponseAuditError(f"SPRINGA source projection DOF changed at {group}")
        if not _eq_json(binding["physical_owner"], source["physical_owner"]):
            raise ResponseAuditError(f"SPRINGA physical owner differs from source at {group}")
        axis = np.asarray(binding["numerical_axis_global_xyz"], dtype=float)
        owner_axis = np.asarray(binding["physical_owner"]["scalar_normal"], dtype=float)
        if axis.shape != (3,) or owner_axis.shape != (3,) or not np.allclose(axis, owner_axis, rtol=0, atol=1e-12):
            raise ResponseAuditError(f"SPRINGA numerical axis differs from physical owner at {group}")
        if not np.isclose(np.linalg.norm(axis), 1.0, rtol=0, atol=1e-10):
            raise ResponseAuditError(f"SPRINGA axis is not unit length at {group}")
        if binding.get("force_law") != "k * max(q_mm, 0)" or binding.get("ground_endpoint_is_numerical_only") is not True:
            raise ResponseAuditError(f"SPRINGA law or ground policy changed at {group}")
        if binding.get("historical_active_state_used") is not False:
            raise ResponseAuditError(f"Historical active state was reused at {group}")
        table = np.asarray(binding["force_vs_elongation_table_N_mm"], dtype=float)
        expected_table = np.asarray([[0.0, -10.0], [0.0, 0.0],
                                     [10.0 * float(binding["stiffness_n_per_mm"]), 10.0]])
        if table.shape != (3, 2) or not np.allclose(table, expected_table, rtol=1e-12, atol=1e-12):
            raise ResponseAuditError(f"SPRINGA table is not the recorded positive-q law at {group}")
        if list(map(float, binding["table_domain_mm"])) != [-10.0, 10.0]:
            raise ResponseAuditError(f"SPRINGA table domain changed at {group}")
        owner = binding["physical_owner"]
        if int(binding["physical_action_on_first_body"]["sign"]) != 1 or int(binding["physical_action_on_second_body"]["sign"]) != -1:
            raise ResponseAuditError(f"SPRINGA body-action sign contract changed at {group}")
        if not _eq_json(binding["physical_action_on_first_body"]["unit_direction_global_xyz"], axis.tolist()):
            raise ResponseAuditError(f"SPRINGA first-body action direction changed at {group}")
        if not _eq_json(binding["physical_action_on_second_body"]["unit_direction_global_xyz"], axis.tolist()):
            raise ResponseAuditError(f"SPRINGA second-body action direction changed at {group}")
        body_names = set(record["physical_body_nodes"])
        if owner.get("first") not in body_names or owner.get("second") not in (body_names | {"floor"}):
            raise ResponseAuditError(f"SPRINGA has an unknown physical owner at {group}")
        element = record["elements"].get(str(binding["source_element"]))
        if element is None or str(element[0]).upper() != "SPRINGA" or list(map(int, element[1])) != list(map(int, binding["springa_nodes"])):
            raise ResponseAuditError(f"SPRINGA element/node map changed at {group}")

    expected_unilateral = {
        str(row["group"]) for row in source_rows
        if row["intended_law"] in ("compression_only", "tension_only")
    }
    if bound_groups != expected_unilateral:
        raise ResponseAuditError("The nonlinear SPRINGA rows do not cover the unilateral source inventory")

    equation_json = {_json_key(equation) for equation in record["equations"]}
    for binding in bindings:
        for equation in binding.get("qghost_equations", []):
            if _json_key(equation["terms"]) not in equation_json:
                raise ResponseAuditError(f"SPRINGA qghost MPC is missing from the complete equation list: {binding['group']}")

    linear_groups: set[str] = set()
    for spring in springs:
        group = str(spring["group"])
        source = by_group.get(group)
        if source is None or source["intended_law"] != "bilateral":
            raise ResponseAuditError(f"Retained SPRING2 is not a bilateral source row: {group}")
        if group in linear_groups:
            raise ResponseAuditError(f"Duplicate retained SPRING2 row {group}")
        linear_groups.add(group)
        index = int(spring["source_inventory_row_index"])
        if not 0 <= index < len(source_rows) or str(source_rows[index]["group"]) != group:
            raise ResponseAuditError(f"Retained SPRING2 source-index mapping changed at {group}")
        if str(spring.get("source_row_id")) != group:
            raise ResponseAuditError(f"Retained SPRING2 source-row identity changed at {group}")
        for key in ("name", "element", "nodes", "dof", "stiffness_n_per_mm"):
            source_key = "element" if key == "element" else key
            if key == "stiffness_n_per_mm":
                if not math.isclose(float(spring[key]), float(source[source_key]), rel_tol=1e-12, abs_tol=1e-12):
                    raise ResponseAuditError(f"Retained SPRING2 stiffness changed at {group}")
            elif not _eq_json(spring[key], source[source_key]):
                raise ResponseAuditError(f"Retained SPRING2 {key} changed at {group}")
        if str(spring.get("intended_law")) != "bilateral":
            raise ResponseAuditError(f"Retained SPRING2 law label changed at {group}")
        if spring["name"] not in record["connection_ownership"]:
            raise ResponseAuditError(f"Retained SPRING2 lacks physical ownership: {group}")
        el = record["elements"].get(str(spring["element"]))
        if el is None or str(el[0]).upper() != "SPRING2" or list(map(int, el[1])) != list(map(int, spring["nodes"])):
            raise ResponseAuditError(f"Retained SPRING2 element/node map changed at {group}")
    expected_bilateral = {str(row["group"]) for row in source_rows if row["intended_law"] == "bilateral"}
    if linear_groups != expected_bilateral:
        raise ResponseAuditError("The 348 retained SPRING2 rows do not cover the bilateral source inventory")

    floor_tangent_rows = [row for row in source_rows if row["intended_law"] == "floor_tangent_all_bearing_hypothesis"]
    floor_map = record["floor_reference_nodes_and_load_map"]
    floor_audit = record["floor_constraint_audit"]
    floor_rows = floor_audit.get("floor_reference_rows", [])
    if len(floor_tangent_rows) != 200 or len(floor_map) != 200 or len(floor_rows) != 200:
        raise ResponseAuditError("Exact floor tangent source/reference row count is not 200")
    if {str(row["group"]) for row in floor_tangent_rows} & (linear_groups | bound_groups):
        raise ResponseAuditError("Removed floor tangent SPRING2 rows remain in native spring inventories")
    floor_normal_count = sum(
        row["intended_law"] == "compression_only" and row["role"] == "floor_normal"
        for row in source_rows
    )
    if floor_normal_count != 100:
        raise ResponseAuditError(f"Expected 100 compression-only floor normals, got {floor_normal_count}")
    floor_by_original: dict[int, dict[str, Any]] = {}
    for reference in floor_map:
        index = int(reference["source_row_original_index"])
        if index in floor_by_original:
            raise ResponseAuditError(f"Duplicate exact-floor original row {index}")
        floor_by_original[index] = reference
    if set(floor_by_original) != set(range(200)):
        raise ResponseAuditError("Exact-floor reference map is not a complete original-row mapping")
    selected_rows = list(map(int, floor_audit["selected_rows_original_indices"]))
    if sorted(selected_rows) != list(range(200)):
        raise ResponseAuditError("Exact-floor selected-row mapping is not a permutation")
    floor_by_equation: dict[int, dict[str, Any]] = {}
    for row in floor_rows:
        normalized = int(row["normalized_equation_index"])
        original = int(row["source_row_original_index"])
        if normalized in floor_by_equation or normalized not in range(200):
            raise ResponseAuditError("Exact-floor normalized equation index is duplicated or out of range")
        if selected_rows[normalized] != original:
            raise ResponseAuditError("Exact-floor permutation does not map the equation back to its original row")
        reference = floor_by_original[original]
        if int(row["dependent_reference_node"]) != int(reference["node"]):
            raise ResponseAuditError("Exact-floor equation/reference-node mapping changed")
        if int(row["source_row_original_index"]) != int(reference["source_row_original_index"]):
            raise ResponseAuditError("Exact-floor source row identity changed")
        floor_by_equation[normalized] = row
    if set(floor_by_equation) != set(range(200)):
        raise ResponseAuditError("Exact-floor equation audit is incomplete")

    # Reconstruct F_ref=(S^-1)^T F_pivot from the actual equation coefficients.
    # Floor rows are identified by their unique physical pivot DOF, not assumed
    # to occupy a fixed position in the full equation list.
    pivot_to_equation: dict[tuple[int, int], list[Any]] = {}
    for equation in record["equations"]:
        if not equation:
            continue
        first = equation[0]
        if len(first) == 3 and abs(float(first[2]) - 1.0) < 1e-13:
            pivot_to_equation[(int(first[0]), int(first[1]))] = equation
    source_pivot_by_normalized = np.zeros(200, dtype=float)
    for normalized, row in floor_by_equation.items():
        pivot = tuple(map(int, row["dependent_physical_pivot_dof"]))
        equation = pivot_to_equation.get(pivot)
        if equation is None:
            raise ResponseAuditError(f"Exact-floor dependent pivot equation is missing: {pivot}")
        reference_col = normalized
        ref = floor_by_original[selected_rows[reference_col]]
        coefficient = 0.0
        for node, dof, value in equation:
            if int(node) == int(ref["node"]) and int(dof) == 1:
                coefficient += float(value)
        source_pivot_by_normalized[normalized] = emitted_cloads.get(pivot, 0.0)
    # Each output component is a column of S^-1 weighted by the full pivot load
    # vector. Accumulate all normalized rows into their reference column.
    reconstructed_ref = np.zeros(200, dtype=float)
    for normalized, row in floor_by_equation.items():
        equation = pivot_to_equation[tuple(map(int, row["dependent_physical_pivot_dof"]))]
        pivot_load = source_pivot_by_normalized[normalized]
        for reference_col, original in enumerate(selected_rows):
            ref = floor_by_original[original]
            coefficient = 0.0
            for node, dof, value in equation:
                if int(node) == int(ref["node"]) and int(dof) == 1:
                    coefficient += float(value)
            reconstructed_ref[reference_col] += (-coefficient) * pivot_load
    omitted_term_bound = 200.0 * 1.0e-13 * max(1.0, float(np.max(np.abs(source_pivot_by_normalized))))
    max_transfer_error = 0.0
    for column, original in enumerate(selected_rows):
        expected = float(floor_by_original[original]["source_load_correction_N"])
        observed = float(reconstructed_ref[column])
        max_transfer_error = max(max_transfer_error, abs(expected - observed))
        if abs(expected - observed) > max(1.0e-7, omitted_term_bound + 1.0e-10):
            raise ResponseAuditError("Exact-floor load transfer differs from equation-derived (S^-1)^T F_pivot")
        audited = floor_by_equation[column]
        if not math.isclose(float(audited["reference_load_correction_N"]), expected, rel_tol=0.0,
                            abs_tol=max(1.0e-7, omitted_term_bound + 1.0e-10)):
            raise ResponseAuditError("Exact-floor normalized audit correction differs from its original-row reference")
    source_floor_by_group = {str(row["group"]): row for row in floor_tangent_rows}
    for index, reference in floor_by_original.items():
        source = source_floor_by_group.get(str(reference["source_spring_group"]))
        if source is None:
            raise ResponseAuditError(f"Exact-floor tangent map lacks its source carrier row: {index}")
        if int(reference["source_spring_element"]) != int(source["element"]):
            raise ResponseAuditError(f"Exact-floor source element changed at row {index}")
        owner = source["physical_owner"]
        basis = np.asarray(reference["owner_tangent_basis_global_xyz"], dtype=float)
        expected_basis = np.asarray(owner["force_basis"], dtype=float)[int(reference["source_spring_local_dof"]) - 1]
        if basis.shape != (3,) or not np.allclose(basis, expected_basis, rtol=0.0, atol=1e-12):
            raise ResponseAuditError(f"Exact-floor tangent basis changed at row {index}")
        if not np.allclose(reference["owner_floorpoint_xyz_mm"], owner["point"], rtol=0.0, atol=1e-9):
            raise ResponseAuditError(f"Exact-floor physical support point changed at row {index}")

    body_nodes = record["physical_body_nodes"]
    if len(body_nodes) != 50 or any(not nodes for nodes in body_nodes.values()):
        raise ResponseAuditError(f"Expected 50 nonempty physical bodies; got {len(body_nodes)}")
    node_sets = {name: set(map(int, values)) for name, values in body_nodes.items()}
    union_nodes: set[int] = set()
    for name, values in node_sets.items():
        if union_nodes & values:
            raise ResponseAuditError(f"Physical solid nodes are owned by multiple bodies near {name}")
        union_nodes |= values
    c3d20_nodes = {
        int(node)
        for element in record["elements"].values()
        if str(element[0]).upper() == "C3D20"
        for node in element[1]
    }
    if c3d20_nodes != union_nodes:
        raise ResponseAuditError("Physical body-node ownership does not exactly cover the solid mesh")
    new_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in source_rows if row["role"] == "candidate_bolt_lateral_plane"
    }
    retained_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in source_rows if row["role"] == "retained_bolt_lateral_plane"
    }
    panel_screw_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in source_rows if row["role"] == "panel_screw_lateral_plane"
    }
    outer_seat_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in source_rows if row["role"] == "physical_bolt_outer_seat_tension"
    }
    if len(new_axes) != 92 or len(retained_axes) != 12 or new_axes & retained_axes:
        raise ResponseAuditError("The 92 new and 12 retained bolt-axis inventories are not distinct")
    if len(panel_screw_axes) != 66 or outer_seat_axes != new_axes | retained_axes:
        raise ResponseAuditError("The 66 Hillman axes or 92+12 outer-seat axes changed")
    external = {int(node): np.asarray(force, dtype=float) for node, force in record["physical_external_loads"].items()}
    body_external: dict[int, np.ndarray] = {}
    for body, loads in record["physical_body_loads"].items():
        if body not in node_sets:
            raise ResponseAuditError(f"External load refers to unknown body {body}")
        for node, force in loads.items():
            node_i = int(node)
            if node_i not in node_sets[body] or node_i in body_external:
                raise ResponseAuditError(f"External load node has invalid/multiple physical ownership: {node_i}")
            body_external[node_i] = np.asarray(force, dtype=float)
    if set(body_external) != set(external) or any(
        not np.allclose(body_external[node], external[node], rtol=0.0, atol=1e-10)
        for node in external
    ):
        raise ResponseAuditError("Physical body and global external load inventories differ")
    declared_native_loads = {int(node): np.asarray(force, dtype=float)
                             for node, force in record["loads"].items()}
    if set(declared_native_loads) != set(external) or any(
        not np.allclose(declared_native_loads[node], external[node], rtol=0.0, atol=1e-10)
        for node in external
    ):
        raise ResponseAuditError("Native load map differs from source-owned physical body loads")

    # The reviewed adapter has one geometrically linear static step. The second
    # *STATIC value is its total time, which scales both source loads and the
    # input-derived exact-floor reference-load correction.
    step_cards = [line.strip() for line in deck.splitlines() if line.strip().upper().startswith("*STEP")]
    if len(step_cards) != 1 or "NLGEOM" not in step_cards[0].upper() or "NLGEOM=NO" not in step_cards[0].upper():
        raise ResponseAuditError("Only the one-step Newton-active/geometrically-linear adapter deck is supported")
    static_lines = [line.strip() for line in deck.splitlines() if line.strip().upper().startswith("*STATIC")]
    if len(static_lines) != 1:
        raise ResponseAuditError("Expected one *STATIC step for proportional load scaling")
    lines = deck.splitlines()
    static_index = next(i for i, line in enumerate(lines) if line.strip().upper().startswith("*STATIC"))
    static_data = None
    for line in lines[static_index + 1:]:
        value = line.strip()
        if not value or value.startswith("**"):
            continue
        if value.startswith("*"):
            break
        static_data = [field.strip() for field in value.split(",") if field.strip()]
        break
    if static_data is None or len(static_data) < 2:
        raise ResponseAuditError("Cannot recover the single-step total time from *STATIC")
    total_time = _number(static_data[1])
    if total_time <= 0.0:
        raise ResponseAuditError("Static-step total time must be positive")

    return {
        "source_rows": source_rows,
        "source_by_group": by_group,
        "source_index_by_group": source_index_by_group,
        "bindings": bindings,
        "springs": springs,
        "floor_by_original": floor_by_original,
        "floor_by_equation": floor_by_equation,
        "floor_reconstructed_source_load_max_abs_error_N": max_transfer_error,
        "floor_load_transfer_omitted_term_bound_N": omitted_term_bound,
        "physical_body_nodes": node_sets,
        "external_loads": external,
        "emitted_cloads": emitted_cloads,
        "emitted_nodes": emitted_nodes,
        "source_load_emission_audit": record["source_load_emission_audit"],
        "source_load_normalization_audit": record.get("source_load_normalization_audit", {}),
        "total_time": total_time,
        "inventory_summary": {
            "raw_source_rows": len(source_rows),
            "law_counts": dict(sorted(law_counts.items())),
            "native_springa_rows": len(bindings),
            "retained_bilateral_spring2_rows": len(springs),
            "removed_exact_floor_tangent_rows": len(floor_map),
            "floor_normal_rows": sum(
                row["intended_law"] == "compression_only" and row["role"] == "floor_normal"
                for row in source_rows
            ),
            "physical_body_count": len(body_nodes),
            "new_block_bolt_axes": len(new_axes),
            "retained_leg_runner_bolt_axes": len(retained_axes),
            "hillman_panel_screw_axes": len(panel_screw_axes),
            "new_and_retained_bolt_axes_disjoint": True,
            "legacy_linear_auditor_reused": False,
        },
    }


def _audit_all_mpcs(equations: list[Any], state: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for index, terms in enumerate(equations):
        residual = sum(float(coefficient) * state["u"][int(node)][int(dof) - 1]
                       for node, dof, coefficient in terms)
        uncertainty = sum(abs(float(coefficient)) * state["u_radius"][int(node)][int(dof) - 1]
                          for node, dof, coefficient in terms)
        rows.append((abs(residual), uncertainty, max(0.0, abs(residual) - uncertainty), index))
    maximum = max(rows, default=(0.0, 0.0, 0.0, -1), key=lambda row: row[2])
    max_resid = max((row[0] for row in rows), default=0.0)
    max_radius = max((row[1] for row in rows), default=0.0)
    max_distance = max((row[2] for row in rows), default=0.0)
    return {
        "equation_count": len(equations),
        "maximum_printed_residual_mm": max_resid,
        "maximum_rounding_interval_radius_mm": max_radius,
        "maximum_interval_distance_from_zero_mm": max_distance,
        "worst_interval_equation_index": maximum[3],
        "passed": max_distance <= MPC_INTERVAL_TOL_MM,
        "criterion": f"Every original, qghost and transformed floor MPC interval intersects zero within {MPC_INTERVAL_TOL_MM:g} mm.",
    }


def _audit_linear_spring(spring: dict[str, Any], state: dict[str, Any]) -> tuple[float, float, dict[str, Any]]:
    first, second = map(int, spring["nodes"])
    component = int(spring["dof"]) - 1
    rf_first = state["rf"][first][component]
    rf_second = state["rf"][second][component]
    r_first = state["rf_radius"][first][component]
    r_second = state["rf_radius"][second][component]
    force = 0.5 * (rf_second - rf_first)
    radius = 0.5 * (r_first + r_second)
    action_residual = rf_first + rf_second
    action_radius = r_first + r_second
    delta = state["u"][second][component] - state["u"][first][component]
    delta_radius = state["u_radius"][second][component] + state["u_radius"][first][component]
    kdu = float(spring["stiffness_n_per_mm"]) * delta
    kdu_radius = abs(float(spring["stiffness_n_per_mm"])) * delta_radius
    guard = 32.0 * np.finfo(float).eps * max(1.0, abs(force), abs(kdu))
    check = {
        "source_group": str(spring["group"]),
        "source_row_id": str(spring.get("source_row_id", spring["group"])),
        "element": int(spring["element"]),
        "endpoint_rf_N": [rf_first, rf_second],
        "endpoint_rf_radius_N": [r_first, r_second],
        "rf_action_reaction_residual_N": action_residual,
        "rf_action_reaction_allowed_radius_N": action_radius,
        "rf_action_reaction_passed": abs(action_residual) <= action_radius + guard,
        "force_on_first_local_N": force,
        "force_rounding_radius_local_N": radius,
        "relative_displacement_mm": delta,
        "relative_displacement_radius_mm": delta_radius,
        "bilateral_kdu_N": kdu,
        "bilateral_kdu_radius_N": kdu_radius,
        "rf_minus_kdu_N": force - kdu,
        "rf_kdu_intervals_intersect": abs(force - kdu) <= radius + kdu_radius + guard,
    }
    if not check["rf_action_reaction_passed"]:
        raise ResponseAuditError(f"Retained SPRING2 RF pair violates action/reaction: {spring['group']}")
    if not check["rf_kdu_intervals_intersect"]:
        raise ResponseAuditError(f"Retained bilateral SPRING2 differs from its unchanged K*du law: {spring['group']}")
    return force, radius, check


def _audit_springa(binding: dict[str, Any], source: dict[str, Any], state: dict[str, Any],
                   model_nodes: dict[str, Any]) -> tuple[float, float, dict[str, Any]]:
    q_node, ground = map(int, binding["springa_nodes"])
    first_projection, second_projection = map(int, binding["source_projection_nodes"])
    dof = int(binding["source_projection_dof"]) - 1
    axis = np.asarray(binding["numerical_axis_global_xyz"], dtype=float)
    span = float(binding["initial_span_mm"])
    k = float(binding["stiffness_n_per_mm"])

    source_q = state["u"][second_projection][dof] - state["u"][first_projection][dof]
    source_q_radius = state["u_radius"][second_projection][dof] + state["u_radius"][first_projection][dof]
    q_vector = np.asarray(state["u"][q_node]) - np.asarray(state["u"][ground])
    q_vector_radius = np.asarray(state["u_radius"][q_node]) + np.asarray(state["u_radius"][ground])
    q_from_ghost = float(q_vector @ axis)
    q_ghost_radius = float(np.abs(axis) @ q_vector_radius)
    ghost_gap = q_from_ghost - source_q
    ghost_gap_radius = q_ghost_radius + source_q_radius
    displacement_guard_mm = 32.0 * np.finfo(float).eps * max(1.0, abs(q_from_ghost), abs(source_q))
    if abs(ghost_gap) > ghost_gap_radius + displacement_guard_mm:
        raise ResponseAuditError(f"SPRINGA qghost displacement does not match its source projections: {binding['group']}")

    # The spring table uses dd-dd0, where dd0 is the actual emitted initial
    # endpoint distance. It can differ from the nominal 100 mm span after the
    # deck's .14g coordinate formatting. Only two already-parsed deck points
    # are read for this connector.
    initial_vector = np.asarray(model_nodes[q_node], dtype=float) - np.asarray(model_nodes[ground], dtype=float)
    initial_length = float(np.linalg.norm(initial_vector))
    if not np.allclose(initial_vector, span * axis, rtol=0.0, atol=1e-8):
        raise ResponseAuditError(f"SPRINGA initial node span/axis changed at {binding['group']}")
    current_vector = initial_vector + q_vector
    geometric_length = float(np.linalg.norm(current_vector))
    geometric_elongation = geometric_length - initial_length
    current_axis = current_vector / geometric_length if geometric_length > 0.0 else axis
    # Subtracting two ~100 mm lengths loses precision near a zero elongation.
    # Bound norm and subtraction roundoff explicitly at the length scale; this
    # is representation arithmetic only, not a force or equilibrium tolerance.
    geometric_arithmetic_guard = 16.0 * np.finfo(float).eps * max(1.0, initial_length, geometric_length)
    geometric_radius = float(np.abs(current_axis) @ q_vector_radius) + geometric_arithmetic_guard
    if geometric_length <= 0.0:
        raise ResponseAuditError(f"SPRINGA endpoints have zero/reversed geometric length at {binding['group']}")
    if abs(geometric_elongation - q_from_ghost) > geometric_radius + q_ghost_radius + displacement_guard_mm:
        raise ResponseAuditError(f"SPRINGA geometric elongation differs from its qghost coordinate: {binding['group']}")
    q = source_q
    domain = tuple(map(float, binding["table_domain_mm"]))
    geometric_low = geometric_elongation - geometric_radius
    geometric_high = geometric_elongation + geometric_radius
    if geometric_low < domain[0] or geometric_high > domain[1]:
        raise ResponseAuditError(f"SPRINGA table domain exceeded (including output rounding): {binding['group']}")
    # CalculiX's SPRINGA table is evaluated from dd-dd0, where dd and dd0 are
    # endpoint distances. The native constitutive force therefore follows the
    # geometric elongation, not the projected MPC scalar directly. The latter
    # remains a separate source-coordinate comparison below.
    table_force_low = k * max(geometric_low, 0.0)
    table_force_high = k * max(geometric_high, 0.0)
    table_force = k * max(geometric_elongation, 0.0)
    projection_law_force = k * max(q, 0.0)
    projection_geometry_gap_mm = abs(geometric_elongation - q)
    projection_geometry_allowance_mm = (
        geometric_radius + q_ghost_radius + ghost_gap_radius + 2.0 * displacement_guard_mm
    )
    if projection_geometry_gap_mm > projection_geometry_allowance_mm:
        raise ResponseAuditError(f"SPRINGA geometric elongation differs from source projection at {binding['group']}")
    projection_vs_geometric_allowance = k * projection_geometry_allowance_mm

    rf_first = np.asarray(state["rf"][q_node], dtype=float)
    rf_ground = np.asarray(state["rf"][ground], dtype=float)
    radius_first = np.asarray(state["rf_radius"][q_node], dtype=float)
    radius_ground = np.asarray(state["rf_radius"][ground], dtype=float)
    internal = float(rf_first @ axis)
    internal_radius = float(np.abs(axis) @ radius_first)
    ground_internal = float(rf_ground @ axis)
    ground_radius = float(np.abs(axis) @ radius_ground)
    force_guard_N = 32.0 * np.finfo(float).eps * max(
        1.0, abs(internal), abs(ground_internal), abs(table_force)
    )
    table_intersection = not (internal + internal_radius + force_guard_N < table_force_low
                              or internal - internal_radius - force_guard_N > table_force_high)
    endpoint_vector_residual = rf_first + rf_ground
    endpoint_vector_radius = radius_first + radius_ground
    endpoint_allowed_radius = endpoint_vector_radius + force_guard_N
    endpoint_passed = bool(np.all(np.abs(endpoint_vector_residual) <= endpoint_allowed_radius))
    table_force_radius = max(abs(table_force - table_force_low), abs(table_force_high - table_force))
    ground_force_passed = abs(ground_internal + table_force) <= ground_radius + table_force_radius + force_guard_N
    if not table_intersection:
        raise ResponseAuditError(f"SPRINGA endpoint RF does not intersect its nonlinear table law: {binding['group']}")
    if not endpoint_passed or not ground_force_passed:
        raise ResponseAuditError(f"SPRINGA endpoint RF pair violates action/reaction: {binding['group']}")

    # The parent-reviewed carrier convention maps the table's positive internal
    # force to +scalar_normal on the source first body. The fixed second node is
    # a numerical device and contributes no external support reaction.
    action = binding["physical_action_on_first_body"]
    if int(action["sign"]) != 1 or not np.allclose(action["unit_direction_global_xyz"], axis, rtol=0.0, atol=1e-12):
        raise ResponseAuditError(f"SPRINGA physical first-body action changed at {binding['group']}")
    check = {
        "source_group": str(binding["group"]),
        "source_row_id": str(binding["source_row_id"]),
        "source_inventory_row_index": int(binding["source_inventory_row_index"]),
        "element": int(binding["source_element"]),
        "intended_source_law": str(source["intended_law"]),
        "q_relative_projection_mm": q,
        "q_relative_projection_radius_mm": source_q_radius,
        "q_from_qghost_mm": q_from_ghost,
        "geometric_spring_elongation_mm": geometric_elongation,
        "geometric_spring_length_mm": geometric_length,
        "actual_initial_spring_length_mm": initial_length,
        "nominal_minus_actual_initial_span_mm": span - initial_length,
        "geometric_length_subtraction_arithmetic_guard_mm": geometric_arithmetic_guard,
        "qghost_minus_projection_mm": ghost_gap,
        "qghost_allowed_radius_mm": ghost_gap_radius,
        "qghost_displacement_arithmetic_guard_mm": displacement_guard_mm,
        "native_table_force_N_from_actual_dd_minus_dd0": table_force,
        "native_table_force_interval_N": [table_force_low, table_force_high],
        "projected_q_force_law_N_diagnostic_only": projection_law_force,
        "projected_q_vs_actual_geometric_force_N": projection_law_force - table_force,
        "projected_q_vs_geometric_elongation_gap_mm": projection_geometry_gap_mm,
        "projected_q_vs_geometric_elongation_allowed_bound_mm": projection_geometry_allowance_mm,
        "projected_q_vs_geometric_force_allowed_bound_N": projection_vs_geometric_allowance,
        "k_times_endpoint_length_arithmetic_guard_N": k * geometric_arithmetic_guard,
        "native_endpoint_internal_force_N": internal,
        "native_endpoint_internal_radius_N": internal_radius,
        "native_ground_rf_projected_N": ground_internal,
        "native_ground_rf_radius_N": ground_radius,
        "native_endpoint_action_reaction_vector_residual_N": endpoint_vector_residual.tolist(),
        "native_endpoint_action_reaction_allowed_radius_N": endpoint_allowed_radius.tolist(),
        "native_endpoint_force_arithmetic_guard_N": force_guard_N,
        "table_domain_mm": list(domain),
        "inside_table_domain_including_rounding": True,
        "table_force_interval_intersects_native_rf": bool(table_intersection),
        "native_endpoint_action_reaction_passed": endpoint_passed and ground_force_passed,
        "physical_force_on_first_body_xyz_n": (internal * axis).tolist(),
        "numerical_ground_rf_excluded_from_physical_balance": True,
    }
    return internal, internal_radius, check


def _load_scale(time: float, total_time: float) -> float:
    scale = time / total_time
    if scale < -1e-10 or scale > 1.0 + 1e-8:
        raise ResponseAuditError(f"Native time {time} lies outside the single static step [0,{total_time}]")
    return min(1.0, max(0.0, scale))


def _audit_floor_rows(contract: dict[str, Any], state: dict[str, Any], scale: float) -> list[dict[str, Any]]:
    rows = []
    for original, reference in sorted(contract["floor_by_original"].items()):
        node = int(reference["node"])
        basis = np.asarray(reference["owner_tangent_basis_global_xyz"], dtype=float)
        if node not in state["rf"] or basis.shape != (3,):
            raise ResponseAuditError(f"Exact-floor RF channel is absent or malformed at original row {original}")
        raw = float(state["rf"][node][0])
        radius = float(state["rf_radius"][node][0])
        source_load = float(reference["source_load_correction_N"]) * scale
        corrected = raw - source_load
        owner = reference["physical_owner"]
        source = contract["source_by_group"][str(reference["source_spring_group"])]
        if owner.get("second") != "floor" or owner.get("first") not in contract["physical_body_nodes"]:
            raise ResponseAuditError(f"Exact-floor tangent row lacks its source body/floor owner at {original}")
        force = corrected * basis
        force_radius = radius * np.abs(basis)
        rows.append({
            "name": "exact-floor/" + str(reference["source_row_id"]),
            "connector_name": str(reference["source_spring_name"]),
            "source_row_id": str(reference["source_row_id"]),
            "source_spring_group": str(reference["source_spring_group"]),
            "source_inventory_row_index": contract["source_index_by_group"][str(reference["source_spring_group"])],
            "source_row_original_index": original,
            "source_connection_name": str(source["name"]),
            "first": owner["first"],
            "second": "floor",
            "point": list(map(float, reference["owner_floorpoint_xyz_mm"])),
            "force_on_first_xyz_n": force.tolist(),
            "force_on_second_xyz_n": (-force).tolist(),
            "force_rounding_radius_xyz_n": force_radius.tolist(),
            "raw_reference_rf_N": raw,
            "transferred_source_load_N": source_load,
            "recovered_physical_tangent_reaction_N": corrected,
            "owner_tangent_basis_global_xyz": basis.tolist(),
        })
    return rows


def _attach_source_ids(physical: dict[str, dict[str, Any]], owners: dict[str, dict[str, Any]],
                       source_ids: dict[str, list[str]],
                       source_inventory_refs: dict[str, list[dict[str, Any]]]) -> None:
    for source_name, owner in owners.items():
        public_name = str(owner.get("connector_name", source_name))
        if public_name not in physical:
            raise ResponseAuditError(f"Recovered physical force omitted owner {source_name}")
        physical[public_name].setdefault("source_row_ids", []).extend(source_ids.get(source_name, [source_name]))
        physical[public_name].setdefault("source_inventory_rows", []).extend(source_inventory_refs.get(source_name, []))
    for row in physical.values():
        row["source_row_ids"] = sorted(set(row.get("source_row_ids", [])))
        unique = {
            (int(item["source_inventory_row_index"]), str(item["source_row_id"])): item
            for item in row.get("source_inventory_rows", [])
        }
        row["source_inventory_rows"] = [unique[key] for key in sorted(unique)]


def _balance_physical_state(record: dict[str, Any], contract: dict[str, Any],
                            physical: dict[str, dict[str, Any]], floor_rows: list[dict[str, Any]],
                            scale: float) -> dict[str, Any]:
    nodes = {int(node): np.asarray(point, dtype=float) for node, point in record["nodes"].items()}
    body_entries: dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = {
        body: [] for body in contract["physical_body_nodes"]
    }
    global_entries: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    loaded_nodes: set[int] = set()
    for body, node_map in record["physical_body_loads"].items():
        for node, value in node_map.items():
            node_i = int(node)
            if node_i in loaded_nodes or node_i not in nodes:
                raise ResponseAuditError(f"Duplicate or missing external-load point {node_i}")
            loaded_nodes.add(node_i)
            force = scale * np.asarray(value, dtype=float)
            zero = np.zeros(3)
            body_entries[body].append((nodes[node_i], force, zero))
            global_entries.append((nodes[node_i], force, zero))

    interfaces = list(physical.values()) + floor_rows
    for row in interfaces:
        first, second = row["first"], row["second"]
        if first not in body_entries and first != "floor":
            raise ResponseAuditError(f"Unknown physical connector owner {first}")
        if second not in body_entries and second != "floor":
            raise ResponseAuditError(f"Unknown physical connector owner {second}")
        first_point = np.asarray(row.get("first_point", row["point"]), dtype=float)
        second_point = np.asarray(row.get("second_point", row["point"]), dtype=float)
        first_force = np.asarray(row["force_on_first_xyz_n"], dtype=float)
        second_force = np.asarray(row["force_on_second_xyz_n"], dtype=float)
        radius = np.asarray(row["force_rounding_radius_xyz_n"], dtype=float)
        if first in body_entries:
            body_entries[first].append((first_point, first_force, radius))
        if second in body_entries:
            body_entries[second].append((second_point, second_force, radius))
        # Sum the actions on the physical frame subsystem. Internal body-body
        # actions are both counted; floor actions are counted only on the wood.
        if first in body_entries:
            global_entries.append((first_point, first_force, radius))
        if second in body_entries:
            global_entries.append((second_point, second_force, radius))

    body_balances = {
        body: _balance(entries, np.mean([nodes[node] for node in sorted(contract["physical_body_nodes"][body])], axis=0))
        for body, entries in body_entries.items()
    }
    global_balance = _balance(global_entries, np.zeros(3))
    return {
        "body_equilibrium": body_balances,
        "global_equilibrium": global_balance,
        "body_count": len(body_balances),
        "physical_external_load_nodes": len(loaded_nodes),
        "physical_support_rows": sum(row["first"] == "floor" or row["second"] == "floor" for row in interfaces),
        "numerical_ground_rf_counted": 0,
        "global_balance_rule": "Source loads plus both actions of body-body connectors plus only the body-side action of floor supports; numerical q grounds excluded.",
    }


def audit_record(record: dict[str, Any], data: str, deck: str) -> dict[str, Any]:
    """Recover all physical forces and balance every native output increment."""
    contract = _validate_input_contract(record, deck)
    parsed = parse_native_blocks(data)
    expected_nodes = set(map(int, record["nodes"].keys()))
    for time, state in parsed.items():
        if set(state["u"]) != expected_nodes or set(state["rf"]) != expected_nodes:
            raise ResponseAuditError(f"Native U/RF node set is incomplete at time {time}")

    linear_name_set = {str(spring["name"]) for spring in contract["springs"]}
    nonlinear_name_set = {str(binding["name"]) for binding in contract["bindings"]}
    if linear_name_set & nonlinear_name_set:
        raise ResponseAuditError("Source owner name is reused by linear and nonlinear carrier laws")
    owners: dict[str, dict[str, Any]] = {}
    source_ids: dict[str, list[str]] = defaultdict(list)
    source_inventory_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    physical_node_union = set().union(*contract["physical_body_nodes"].values())
    for name in linear_name_set:
        owners[name] = record["connection_ownership"][name]
    for binding in contract["bindings"]:
        name = str(binding["name"])
        owner = binding["physical_owner"]
        if not _eq_json(record["connection_ownership"].get(name), owner):
            raise ResponseAuditError(f"SPRINGA owner differs from source metadata at {name}")
        owners[name] = owner
        source_ids[name].append(str(binding["source_row_id"]))
        source = contract["source_by_group"][str(binding["group"])]
        source_inventory_refs[name].append({
            "source_inventory_row_index": int(binding["source_inventory_row_index"]),
            "source_row_id": str(binding["source_row_id"]),
            "source_connection_name": str(source["name"]),
            "intended_law": str(source["intended_law"]),
        })
    for spring in contract["springs"]:
        source_ids[str(spring["name"])].append(str(spring.get("source_row_id", spring["group"])))
        source = contract["source_by_group"][str(spring["group"])]
        source_inventory_refs[str(spring["name"])].append({
            "source_inventory_row_index": int(spring["source_inventory_row_index"]),
            "source_row_id": str(spring["source_row_id"]),
            "source_connection_name": str(source["name"]),
            "intended_law": str(source["intended_law"]),
        })

    component_totals: Counter[str] = Counter()
    reports = []
    all_mpc_pass = all_linear_pass = all_springa_pass = all_floor_normals_positive = True
    all_raw_balance_pass = all_interval_balance_pass = True
    spring2_endpoint_nodes = {int(node) for spring in contract["springs"] for node in spring["nodes"]}
    for time, state in parsed.items():
        scale = _load_scale(time, contract["total_time"])
        mpc = _audit_all_mpcs(record["equations"], state)
        all_mpc_pass &= bool(mpc["passed"])

        local_vectors: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        local_radii: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        spring2_checks = []
        endpoints: set[tuple[int, int]] = set()
        for spring in contract["springs"]:
            first, second = map(int, spring["nodes"])
            dof = int(spring["dof"])
            for endpoint in (first, second):
                key = (endpoint, dof)
                if key in endpoints:
                    raise ResponseAuditError(f"Retained SPRING2 endpoint DOF is not isolated: {key}")
                endpoints.add(key)
            force, radius, check = _audit_linear_spring(spring, state)
            name = str(spring["name"])
            local_vectors[name][dof - 1] += force
            local_radii[name][dof - 1] += radius
            spring2_checks.append(check)
        linear_pass = all(row["rf_action_reaction_passed"] and row["rf_kdu_intervals_intersect"]
                          for row in spring2_checks)
        all_linear_pass &= linear_pass

        springa_checks = []
        q_endpoint_dofs: set[tuple[int, int]] = set()
        floor_normals_pass = True
        for binding in contract["bindings"]:
            q_node, ground = map(int, binding["springa_nodes"])
            for node in (q_node, ground):
                if node in spring2_endpoint_nodes:
                    raise ResponseAuditError(f"SPRINGA numerical endpoint overlaps a SPRING2 endpoint: {node}")
                if node in physical_node_union:
                    raise ResponseAuditError("SPRINGA numerical endpoint is a physical body name (invalid map)")
            for dof in (1, 2, 3):
                for node in (q_node, ground):
                    key = (node, dof)
                    if key in q_endpoint_dofs:
                        raise ResponseAuditError(f"SPRINGA numerical endpoint DOF is shared: {key}")
                    q_endpoint_dofs.add(key)
            source = contract["source_by_group"][str(binding["group"])]
            force, radius, check = _audit_springa(binding, source, state, contract["emitted_nodes"])
            name = str(binding["name"])
            local_vectors[name][0] += force
            local_radii[name][0] += radius
            if source["role"] == "floor_normal":
                if force - radius <= 0.0:
                    floor_normals_pass = False
                    all_floor_normals_positive = False
                    raise ResponseAuditError(
                        f"All-bearing floor-normal branch is not strictly positive at {binding['group']} time {time}"
                    )
                check["strictly_positive_floor_normal_after_rounding"] = True
            springa_checks.append(check)
        springa_pass = all(row["table_force_interval_intersects_native_rf"]
                           and row["native_endpoint_action_reaction_passed"]
                           and row["inside_table_domain_including_rounding"] for row in springa_checks)
        all_springa_pass &= springa_pass

        # Reuse the established owner/basis transform for physical forces. The
        # RF-derived half-last-place radii below follow the same abs(B.T) or
        # abs(normal) transform used by wood_joint_reduced_force_output.recover.
        mapped = map_physical_forces(
            {"springs": [], "connection_ownership": owners},
            {"connector_forces": {
                name: {"force_on_first_xyz_n": vector.tolist()}
                for name, vector in local_vectors.items()
            }},
            precision=None,
        )
        radii_by_public: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        for name, owner in owners.items():
            radius = local_radii.get(name, np.zeros(3))
            if "force_basis" in owner:
                radius = np.abs(np.asarray(owner["force_basis"], dtype=float).T) @ radius
            elif "scalar_normal" in owner:
                radius = radius[0] * np.abs(np.asarray(owner["scalar_normal"], dtype=float))
            else:
                raise ResponseAuditError(f"Physical owner lacks scalar/basis force mapping: {name}")
            radii_by_public[str(owner.get("connector_name", name))] += radius
        for name, row in mapped.items():
            row["force_rounding_radius_xyz_n"] = radii_by_public[name].tolist()
            row["force_precision_basis"] = "Native endpoint RF half-last-place intervals propagated through the recorded physical connector basis."
        _attach_source_ids(mapped, owners, source_ids, source_inventory_refs)

        floor_rows = _audit_floor_rows(contract, state, scale)
        balances = _balance_physical_state(record, contract, mapped, floor_rows, scale)
        global_balance = balances["global_equilibrium"]
        body_balances = balances["body_equilibrium"]
        raw_balance_pass = global_balance["printed_resultants_passed"] and all(
            row["printed_resultants_passed"] for row in body_balances.values()
        )
        interval_balance_pass = global_balance["interval_resultants_passed"] and all(
            row["interval_resultants_passed"] for row in body_balances.values()
        )
        all_raw_balance_pass &= raw_balance_pass
        all_interval_balance_pass &= interval_balance_pass
        component_totals["retained_bilateral_spring2"] += len(spring2_checks)
        component_totals["unilateral_springa"] += len(springa_checks)
        component_totals["exact_floor_tangent_reactions"] += len(floor_rows)
        reports.append({
            "time": time,
            "load_factor": scale,
            "all_mpc_equations": mpc,
            "all_original_projection_and_mpc_checks_passed": bool(mpc["passed"]),
            "mpc_interval_checks_passed": bool(mpc["passed"]),
            "retained_spring2_component_count": len(spring2_checks),
            "retained_bilateral_spring2_law_and_endpoint_checks_passed": linear_pass,
            "retained_bilateral_checks_passed": linear_pass,
            "retained_spring2_action_reaction_and_kdu_passed": all(
                row["rf_action_reaction_passed"] and row["rf_kdu_intervals_intersect"] for row in spring2_checks
            ),
            "retained_spring2_components": spring2_checks,
            "springa_component_count": len(springa_checks),
            "unilateral_springa_table_endpoint_checks_passed": springa_pass,
            "springa_law_checks_passed": springa_pass,
            "springa_table_endpoint_checks": springa_checks,
            "physical_connection_forces": mapped,
            "exact_floor_tangent_reactions": floor_rows,
            "all_floor_normals_strictly_positive_after_rounding": all(
                row.get("strictly_positive_floor_normal_after_rounding", False)
                for row in springa_checks if row["intended_source_law"] == "compression_only"
                and contract["source_by_group"][row["source_group"]]["role"] == "floor_normal"
            ),
            "normal_positive_all_bearing_branch_passed": floor_normals_pass,
            "physical_balance": balances,
            "raw_balance_passed": raw_balance_pass,
            "rounding_interval_balance_passed": interval_balance_pass,
            "all_body_and_global_raw_balance_checks_passed": raw_balance_pass,
            "all_body_and_global_rounding_interval_checks_passed": interval_balance_pass,
        })

    if not all_floor_normals_positive:
        raise ResponseAuditError("At least one floor normal opened; all-bearing stick branch is invalid")
    return {
        "schema": SCHEMA,
        "status": "PASS_NUMERICAL_RESPONSE_AUDIT_ONLY" if (
            all_mpc_pass and all_linear_pass and all_springa_pass and all_floor_normals_positive
            and all_raw_balance_pass and all_interval_balance_pass
        ) else "NUMERICAL_RESPONSE_AUDIT_FAILED",
        "candidate": record["candidate"],
        "geometry_revision_id": record["geometry_revision_id"],
        "case_id": record.get("case_id", "a12-rear"),
        "native_solve_launched_by_postprocessor": False,
        "native_output_consumed": True,
        "qualified_for_design": False,
        "frame_ready_for_native_run": False,
        "joint_demand_accepted": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "historical_c11_forces_or_active_states_used": False,
        "source_inventory": contract["inventory_summary"],
        "floor_source_load_transfer": {
            "formula": "F_ref=(S^-1)^T F_pivot, reconstructed from recorded transformed-equation coefficients; R_tangent=RF(ref,1)-F_ref*load_factor",
            "equation_derived_max_abs_difference_N": contract["floor_reconstructed_source_load_max_abs_error_N"],
            "serialized_coefficient_omission_bound_N": contract["floor_load_transfer_omitted_term_bound_N"],
            "row_map": "Normalized equation index -> selected original row -> exact-floor reference node -> source tangent group/local DOF/physical floor point.",
            "numerical_grounds_counted_as_support": False,
        },
        "recovery_summary": {
            "native_increment_count": len(reports),
            "retained_spring2_component_checks": component_totals["retained_bilateral_spring2"],
            "nonlinear_springa_component_checks": component_totals["unilateral_springa"],
            "exact_floor_tangent_reaction_rows": component_totals["exact_floor_tangent_reactions"],
            "all_original_projection_and_mpc_equations_checked": True,
            "all_springa_table_domains_checked": True,
            "all_unilateral_table_endpoint_pairs_checked": True,
            "all_bilateral_spring2_laws_checked": True,
            "normal_positive_all_bearing_branch_passed": all_floor_normals_positive,
            "raw_body_and_global_balance_passed": all_raw_balance_pass,
            "rounding_interval_body_and_global_balance_passed": all_interval_balance_pass,
            "mpc_interval_checks_passed": all_mpc_pass,
            "springa_law_checks_passed": all_springa_pass,
            "retained_bilateral_checks_passed": all_linear_pass,
            "force_rounding": "Actual native RF token half-last-place intervals propagated through the recorded local-to-world force basis.",
            "moment_and_equilibrium": "Existing wood_joint_reduced_response._balance calculation applied at each body centroid and global origin.",
        },
        "input_deck_sha256": hashlib.sha256(deck.encode("utf-8")).hexdigest(),
        "native_data_sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
        "source_model_record_canonical_sha256": hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest(),
        "source_input_model_json_sha256": None,
        "increments": reports,
        "limits": [
            "One source-bound a12-rear case and one proportional load ramp only; no other load case is inferred.",
            "The exact-floor tangent reactions assume every paired floor normal is strictly compression-positive; no release/recontact procedure is supplied.",
            "Floor references are scalar reaction channels at source-owned tangent points, not anchors or verified floor properties.",
            "The 100 mm SPRINGA endpoints and fixed numerical grounds are numerical devices; their RF values are excluded from physical balances.",
            "No capacity, resistance, actual material or hardware inspection, fabrication approval, floor friction, floor anchorage, or climbing release is established.",
            "The 92 new block bolt axes and 12 retained leg/runner axes remain separately identified; no prior C11 force or active-state result is reused.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_json", type=Path)
    parser.add_argument("model_dat", type=Path)
    parser.add_argument("model_inp", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.model_json.read_text())
    report = audit_record(record, args.model_dat.read_text(), args.model_inp.read_text())
    report["source_input_model_json_sha256"] = hashlib.sha256(args.model_json.read_bytes()).hexdigest()
    report["source_input_model_json_path"] = str(args.model_json.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(report["status"])


if __name__ == "__main__":
    main()
