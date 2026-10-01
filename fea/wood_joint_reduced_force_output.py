"""Recover spring forces and precision bounds from native nodal RF output.

At an isolated scalar SPRING2 endpoint pair, the printed RF values carry a
more useful force precision than recomputing ``k * delta_u`` from rounded U.
This module validates that isolation, checks RF action/reaction and kinematic
consistency against the printed U/RF intervals, then delegates orientation and
clearance-reference correction to ``current_response_run.physical_forces``.
It does not run a solver or confer mechanical acceptance.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from fea import horizontal_panel_frame as frame
from fea.current_response_run import physical_forces


def _half_last_place(token: str) -> float:
    normalized = token.upper().replace("D", "E")
    if "E" in normalized:
        mantissa, exponent_text = normalized.split("E", 1)
        exponent = int(exponent_text)
    else:
        mantissa, exponent = normalized, 0
    decimals = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    return 0.5 * 10.0 ** (exponent - decimals)


def _numeric_block(data: str, kind: str) -> tuple[dict[int, list[float]], dict[int, list[float]]]:
    """Read one DAT nodal vector block and half-last-place radii."""
    matches = list(re.finditer(
        rf"^\s*{re.escape(kind)}\s*\([^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)",
        data, re.MULTILINE | re.DOTALL,
    ))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one complete {kind} output block")
    values: dict[int, list[float]] = {}
    radii: dict[int, list[float]] = {}
    for line in matches[0].group(1).splitlines():
        cells = line.split()
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        node = int(cells[0])
        if node in values:
            raise ValueError(f"Duplicate {kind} output for node {node}")
        try:
            vector = [float(token.upper().replace("D", "E")) for token in cells[1:]]
            radius = [_half_last_place(token) for token in cells[1:]]
        except (ValueError, OverflowError) as error:
            raise ValueError(f"Malformed {kind} output at node {node}") from error
        if not np.isfinite(vector).all() or not np.isfinite(radius).all():
            raise ValueError(f"Nonfinite {kind} output at node {node}")
        values[node] = vector
        radii[node] = radius
    if not values:
        raise ValueError(f"Empty {kind} output block")
    return values, radii


def _check_spring_isolation(record: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    """Require each spring endpoint DOF to be an isolated scalar spring DOF."""
    springs = record.get("springs")
    elements = record.get("elements")
    if not isinstance(springs, list) or not isinstance(elements, dict):
        raise TypeError("Native model spring and element inventories must be a list and mapping")
    rows_by_node_dof: dict[tuple[int, int], dict[str, Any]] = {}
    spring_elements: set[int] = set()
    auxiliary_nodes: set[int] = set()
    connector_name_dofs: set[tuple[str, int]] = set()
    for row in springs:
        try:
            element_id = int(row["element"])
            nodes = tuple(map(int, row["nodes"]))
            dof = int(row["dof"])
            name = str(row["name"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Malformed scalar spring inventory") from error
        if len(nodes) != 2 or nodes[0] == nodes[1] or dof not in (1, 2, 3):
            raise ValueError(f"Invalid spring endpoint/dof row: {row}")
        name_dof = (name, dof)
        if name_dof in connector_name_dofs:
            raise ValueError(f"Connector output would merge repeated component DOF: {name} DOF {dof}")
        connector_name_dofs.add(name_dof)
        if element_id in spring_elements:
            raise ValueError(f"Spring element is multiply assigned: {element_id}")
        spring_elements.add(element_id)
        element = elements.get(str(element_id), elements.get(element_id))
        if (element is None or len(element) != 3 or element[0] != "SPRING2"
                or list(map(int, element[1])) != list(nodes)
                or row.get("group") != element[2]):
            raise ValueError(f"Spring inventory disagrees with element {element_id}")
        for node in nodes:
            auxiliary_nodes.add(node)
            key = (node, dof)
            if key in rows_by_node_dof:
                other = rows_by_node_dof[key]
                raise ValueError(
                    f"Spring endpoint DOF is not isolated: node={node}, dof={dof}, "
                    f"springs={other['name']},{name}"
                )
            rows_by_node_dof[key] = row

    for element_id, element in elements.items():
        kind, node_ids, _ = element
        if kind == "SPRING2":
            continue
        overlap = auxiliary_nodes.intersection(map(int, node_ids))
        if overlap:
            raise ValueError(
                f"Spring auxiliary node is shared with {kind} element {element_id}: {sorted(overlap)}"
            )
    model_spring_elements = {int(element_id) for element_id, element in elements.items()
                             if element[0] == "SPRING2"}
    if spring_elements != model_spring_elements:
        raise ValueError("Spring rows do not cover the exact native SPRING2 element inventory")
    return rows_by_node_dof


def _owners(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {**record.get("connection_ownership", {}),
            **record.get("radial_clearance_ownership", {})}


def recover(record: dict[str, Any], raw_assessed: dict[str, Any], data: str
            ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Recover physical connector forces with RF-derived rounding intervals.

    ``raw_assessed`` is the ordinary ``horizontal_panel_frame.assess`` result
    from this same DAT output. Its connector force values provide the K*U
    independent check; its force directions/ownership are retained while scalar
    force values are replaced by the RF endpoint estimates.
    """
    spring_inventory = record.get("springs", [])
    owners = _owners(record)
    if not owners:
        raise ValueError("Native response lacks physical spring ownership")
    if not isinstance(raw_assessed.get("connector_forces"), dict):
        raise TypeError("Raw native assessment connector_forces must be a mapping")
    endpoints_by_dof = _check_spring_isolation(record)
    rf, rf_radius = _numeric_block(data, "forces")
    displacement, displacement_radius = _numeric_block(data, "displacements")
    model_nodes = {int(node) for node in record.get("nodes", {})}
    if set(rf) != model_nodes or set(displacement) != model_nodes:
        raise ValueError("Native U/RF blocks do not cover the frozen node inventory")

    assessed_rows = raw_assessed["connector_forces"]
    corrected_rows = {name: {**row, "force_on_first_xyz_n": list(row["force_on_first_xyz_n"])}
                      for name, row in assessed_rows.items()}
    local_radius_by_name: dict[str, np.ndarray] = {}
    checks = []
    seen_names: set[str] = set()
    for spring in spring_inventory:
        name = str(spring["name"])
        if name not in owners or name not in corrected_rows:
            raise ValueError(f"Spring lacks physical ownership or raw force output: {name}")
        if len(corrected_rows[name]["force_on_first_xyz_n"]) != 3:
            raise ValueError(f"Malformed raw connector force vector: {name}")
        dof = int(spring["dof"])
        first, second = map(int, spring["nodes"])
        if first not in rf or second not in rf or first not in displacement or second not in displacement:
            raise ValueError(f"Native U/RF output omits spring endpoints: {name}")
        key = (first, dof)
        if endpoints_by_dof.get(key) is not spring and endpoints_by_dof.get(key) != spring:
            raise ValueError(f"Spring endpoint isolation lookup failed: {name}")
        if name not in seen_names:
            local_radius_by_name[name] = np.zeros(3)
            seen_names.add(name)

        rf_first = rf[first][dof - 1]
        rf_second = rf[second][dof - 1]
        rf_first_radius = rf_radius[first][dof - 1]
        rf_second_radius = rf_radius[second][dof - 1]
        rf_force_on_first = 0.5 * (rf_second - rf_first)
        rf_force_radius = 0.5 * (rf_first_radius + rf_second_radius)
        action_reaction_residual = rf_first + rf_second
        action_reaction_radius = rf_first_radius + rf_second_radius

        u_first = displacement[first][dof - 1]
        u_second = displacement[second][dof - 1]
        u_radius = displacement_radius[first][dof - 1] + displacement_radius[second][dof - 1]
        delta = u_second - u_first
        active = bool(spring.get("active", True))
        stiffness = float(spring["stiffness_n_per_mm"])
        kdu = stiffness * delta if active else 0.0
        kdu_radius = abs(stiffness) * u_radius if active else 0.0
        residual = rf_force_on_first - kdu
        allowed = rf_force_radius + kdu_radius
        arithmetic_guard = 32.0 * np.finfo(float).eps * max(1.0, abs(rf_force_on_first), abs(kdu))
        action_passed = abs(action_reaction_residual) <= action_reaction_radius + arithmetic_guard
        kdu_passed = abs(residual) <= allowed + arithmetic_guard
        local = corrected_rows[name]["force_on_first_xyz_n"]
        local[dof - 1] = rf_force_on_first
        local_radius_by_name[name][dof - 1] += rf_force_radius
        checks.append({
            "spring_name": name,
            "spring_element": int(spring["element"]),
            "active": active,
            "nodes_first_second": [first, second],
            "dof": dof,
            "rf_endpoint_values_n": [rf_first, rf_second],
            "rf_endpoint_rounding_radius_n": [rf_first_radius, rf_second_radius],
            "rf_action_reaction_residual_n": action_reaction_residual,
            "rf_action_reaction_radius_n": action_reaction_radius,
            "rf_action_reaction_passed": bool(action_passed),
            "rf_force_on_first_n": rf_force_on_first,
            "rf_force_rounding_radius_n": rf_force_radius,
            "rounded_u_delta_mm": delta,
            "u_delta_rounding_radius_mm": u_radius,
            "kdu_force_on_first_n": kdu,
            "kdu_rounding_radius_n": kdu_radius,
            "rf_minus_kdu_n": residual,
            "rf_minus_kdu_allowed_radius_n": allowed,
            "rf_matches_kdu_print_intervals": bool(kdu_passed),
            "force_comparison_basis": ("active SPRING2 K*deltaU" if active
                                        else "inactive/deleted spring has zero physical force"),
        })
        if not action_passed:
            raise ValueError(f"SPRING2 RF endpoints violate action/reaction: {name} DOF {dof}")
        if not kdu_passed:
            raise ValueError(f"SPRING2 RF force disagrees with printed K*deltaU intervals: {name} DOF {dof}")

    if set(assessed_rows) != {str(row["name"]) for row in spring_inventory}:
        raise ValueError("Native connector force groups differ from the spring inventory")
    if set(owners) - set(assessed_rows):
        raise ValueError("Physical ownership contains a connector absent from the spring inventory")

    recovered = physical_forces(record, {**raw_assessed, "connector_forces": corrected_rows})
    recovered_radius: dict[str, np.ndarray] = {}
    for name, owner in owners.items():
        local_radius = local_radius_by_name.get(name, np.zeros(3))
        if "force_basis" in owner:
            radius = np.abs(np.asarray(owner["force_basis"], dtype=float).T) @ local_radius
        elif "scalar_normal" in owner:
            radius = local_radius[0] * np.abs(np.asarray(owner["scalar_normal"], dtype=float))
        else:
            radius = local_radius
        public_name = owner.get("connector_name", name)
        recovered_radius[public_name] = recovered_radius.get(public_name, np.zeros(3)) + radius
    for name, row in recovered.items():
        if name not in recovered_radius:
            raise ValueError(f"Recovered physical force lacks RF rounding interval: {name}")
        row["force_rounding_radius_xyz_n"] = recovered_radius[name].tolist()
        row["force_precision_basis"] = "Native endpoint RF half-last-place intervals propagated through local connector basis; gap offset treated as exact input"

    audit = {
        "schema": "wood_joint_reduced_rf_force_recovery/v1",
        "status": "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS",
        "spring_component_count": len(spring_inventory),
        "auxiliary_node_count": len({node for node, _ in endpoints_by_dof}),
        "isolated_node_dof_count": len(endpoints_by_dof),
        "structural_element_overlap_checked": True,
        "all_spring_rf_action_reaction_passed": True,
        "all_active_spring_rf_matches_kdu_print_intervals": True,
        "all_inactive_spring_rf_matches_zero_within_print_intervals": True,
        "components": checks,
        "rounding_rule": "Each printed U/RF scalar contributes half one unit in its last shown decimal place; endpoint force is (RF_second-RF_first)/2.",
        "force_comparison_rule": "RF endpoint force interval must intersect active k*deltaU interval; inactive/deleted spring force must intersect zero.",
        "physical_force_rule": "RF local scalar estimates replace rounded-U spring forces before physical_forces applies basis orientation and radial-clearance reference-force subtraction.",
        "native_solve_executed": False,
        "mechanical_acceptance": False,
    }
    return recovered, audit


def self_check() -> dict[str, Any]:
    """Replay the retained three-case known-answer DAT without solver execution."""
    root = Path(__file__).resolve().parents[1]
    directory = root / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-methods-attempt02"
    record = json.loads((directory / "model.json").read_text())
    data = (directory / "model.dat").read_text()
    raw = frame.assess(record, data)
    recovered, audit = recover(record, raw, data)
    observed = {}
    for check in record["checks"]:
        actual = np.asarray(recovered[check["name"]]["force_on_first_xyz_n"])
        expected = np.asarray(check["expected_force_on_first_n"])
        error = float(np.max(np.abs(actual - expected)))
        observed[check["name"]] = {"expected_force_on_first_n": expected.tolist(),
                                   "recovered_force_on_first_n": actual.tolist(),
                                   "maximum_error_n": error}
        if error > record["tolerances"]["physical_force_abs_n"]:
            raise AssertionError(f"Recovered RF force misses known answer: {check['name']}")
    if audit["status"] != "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS":
        raise AssertionError("RF precision self-check did not pass")
    return {"status": audit["status"], "observed_known_answers": observed,
            "spring_component_count": audit["spring_component_count"],
            "auxiliary_node_count": audit["auxiliary_node_count"],
            "native_solve_executed": False, "mechanical_acceptance": False}


if __name__ == "__main__":
    print(json.dumps(self_check(), indent=2, sort_keys=True))
