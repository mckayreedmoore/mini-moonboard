"""Read-only post-run audit for the frozen RF-to-opening fixture."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ATTEMPT = Path(__file__).resolve().parent
NATIVE = ATTEMPT / "native"
sys.path.insert(0, str(ROOT))

from fea import wood_joint_reduced_native as native
from fea.wood_joint_reduced_force_output import _check_spring_isolation, _numeric_block, recover


THRESHOLD_MM = 1.0e-7


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float, *, atol: float = 1.0e-14) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=atol)


def audit() -> dict:
    preparation = json.loads((ATTEMPT / "preparation.json").read_text())
    freeze = native.verify(NATIVE, check_live=True)
    if digest(NATIVE / "freeze.json") != preparation["input_freeze_sha256"]:
        raise ValueError("Native freeze differs from the reviewed preparation hash")
    if digest(NATIVE / "model.inp") != preparation["deck_sha256"]:
        raise ValueError("Frozen deck differs from the prepared deck hash")
    record = json.loads((NATIVE / "model.json").read_text())
    data = (NATIVE / "model.dat").read_text()

    u, u_radius = _numeric_block(data, "displacements")
    raw_connector_forces = {}
    for spring in record["springs"]:
        name = str(spring["name"])
        first, second = map(int, spring["nodes"])
        dof = int(spring["dof"]) - 1
        delta = u[second][dof] - u[first][dof]
        value = float(spring["stiffness_n_per_mm"]) * delta if spring.get("active", True) else 0.0
        force = [0.0, 0.0, 0.0]
        force[dof] = value
        raw_connector_forces[name] = {"force_on_first_xyz_n": force}

    recovered, rf_audit = recover(record, {"connector_forces": raw_connector_forces}, data)
    if rf_audit["status"] != "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS":
        raise AssertionError("RF helper did not pass action/reaction and KΔU interval checks")
    if not rf_audit["all_active_spring_rf_matches_kdu_print_intervals"]:
        raise AssertionError("At least one active spring RF interval does not meet printed KΔU")

    endpoint_map = _check_spring_isolation(record)
    full_fixed = {(int(node), dof) for node in record["fixed_nodes"] for dof in (1, 2, 3)}
    for node, dofs in record["host_partial_fixed_dofs"].items():
        full_fixed.update((int(node), int(dof)) for dof in dofs)
    loaded = {
        (int(node), dof + 1)
        for node, vector in record["loads"].items()
        for dof, force in enumerate(vector) if float(force) != 0.0
    }

    components = {str(row["spring_name"]): row for row in rf_audit["components"]}
    branch_results = []
    for branch in record["branches"]:
        contact_name = str(branch["contact_spring_name"])
        contact = next(row for row in record["springs"] if row["name"] == contact_name)
        if not contact.get("active", True) or int(contact["dof"]) != 1:
            raise AssertionError(f"Primary contact branch is not an active scalar spring: {contact_name}")
        if not close(float(contact["stiffness_n_per_mm"]), float(record["contact_stiffness_n_per_mm"])):
            raise AssertionError(f"Unexpected contact stiffness: {contact_name}")

        endpoints = list(map(int, branch["contact_endpoint_nodes"]))
        spring_endpoints = list(map(int, contact["nodes"]))
        if endpoints != spring_endpoints:
            raise AssertionError(f"Contact endpoint inventory changed: {contact_name}")
        endpoint_dofs = {(node, 1) for node in endpoints}
        if endpoint_dofs & loaded or endpoint_dofs & full_fixed:
            raise AssertionError(f"Primary contact endpoint DOF is directly loaded or supported: {contact_name}")
        if any(endpoint_map.get(key) is not contact and endpoint_map.get(key) != contact
               for key in endpoint_dofs):
            raise AssertionError(f"Primary contact endpoint DOF is not isolated: {contact_name}")

        # Each scalar endpoint has exactly one projection MPC, with its host
        # U3 as the only other term and unit coefficients of opposite sign.
        expected_hosts = [int(branch["wood_host_node"]), int(branch["panel_host_node"])]
        equations = record["equations"]
        for endpoint, host in zip(endpoints, expected_hosts, strict=True):
            matches = [row for row in equations
                       if any(int(term[0]) == endpoint and int(term[1]) == 1 for term in row)]
            if len(matches) != 1:
                raise AssertionError(f"Contact endpoint DOF 1 must occur in exactly one MPC: {endpoint}")
            if len(matches[0]) != 2:
                raise AssertionError(f"Contact endpoint MPC must have exactly two terms: node {endpoint}")
            terms = {(int(n), int(d)): float(coefficient) for n, d, coefficient in matches[0]}
            if set(terms) != {(endpoint, 1), (host, 3)}:
                raise AssertionError(f"Contact endpoint MPC contains unexpected terms: node {endpoint}")
            if not close(terms[(endpoint, 1)], 1.0) or not close(terms[(host, 3)], -1.0):
                raise AssertionError(f"Contact endpoint MPC coefficients changed: node {endpoint}")

        support = next(row for row in record["springs"]
                       if row["name"] == branch["host_support_spring_name"])
        if list(map(int, support["nodes"])) != [int(branch["panel_host_node"]),
                                                 int(branch["host_support_anchor_node"])]:
            raise AssertionError(f"Host support does not use the separate host-side nodes: {contact_name}")
        if int(support["dof"]) != 3 or not close(
                float(support["stiffness_n_per_mm"]),
                float(record["host_support_stiffness_n_per_mm"])):
            raise AssertionError(f"Host support spring changed: {contact_name}")

        opening = float(branch["opening_mm"])
        applied = float(branch["host_load_n"])
        expected_load = -(float(record["contact_stiffness_n_per_mm"])
                          + float(record["host_support_stiffness_n_per_mm"])) * opening
        if not close(applied, expected_load):
            raise AssertionError(f"Host CLOAD no longer solves the stated parallel-stiffness answer: {contact_name}")
        load_vector = record["loads"][str(branch["host_load_node"])]
        if int(branch["host_load_dof"]) != 3 or not close(float(load_vector[2]), applied):
            raise AssertionError(f"Host CLOAD record differs from its derivation: {contact_name}")

        checked = components[contact_name]
        if not checked["rf_action_reaction_passed"]:
            raise AssertionError(f"Contact RF endpoint pair violates action/reaction: {contact_name}")
        if not checked["rf_matches_kdu_print_intervals"]:
            raise AssertionError(f"Contact RF misses active KΔU print interval: {contact_name}")

        force_z = float(recovered[contact_name]["force_on_first_xyz_n"][2])
        force_radius_z = float(recovered[contact_name]["force_rounding_radius_xyz_n"][2])
        if not close(float(record["opening_reference_offset_mm"]), 0.0):
            raise AssertionError("RF-to-opening fixture must retain a zero reference offset")
        expected_force = float(branch["expected_contact_force_on_first_n"])
        if abs(force_z - expected_force) > force_radius_z + 1.0e-14:
            raise AssertionError(f"Contact RF interval misses its known-answer force: {contact_name}")
        stiffness = float(record["contact_stiffness_n_per_mm"])
        inferred_opening = -force_z / stiffness
        opening_radius = force_radius_z / stiffness
        lower, upper = inferred_opening - opening_radius, inferred_opening + opening_radius
        if not lower <= opening <= upper:
            raise AssertionError(f"Known opening is outside the inferred RF interval: {contact_name}")
        if branch["id"] == "below" and not upper < THRESHOLD_MM:
            raise AssertionError("Below-threshold inferred opening interval crosses the active-set threshold")
        if branch["id"] == "above" and not lower > THRESHOLD_MM:
            raise AssertionError("Above-threshold inferred opening interval crosses the active-set threshold")

        host_delta = u[int(branch["panel_host_node"])][2] - u[int(branch["wood_host_node"])][2]
        host_delta_radius = (u_radius[int(branch["panel_host_node"])][2]
                             + u_radius[int(branch["wood_host_node"])][2])
        expected_delta = -opening
        if not host_delta - host_delta_radius <= expected_delta <= host_delta + host_delta_radius:
            raise AssertionError(f"Host-side known displacement is outside its DAT interval: {contact_name}")

        branch_results.append({
            "branch": branch["id"],
            "known_opening_mm": opening,
            "inferred_opening_mm": inferred_opening,
            "inferred_opening_rounding_radius_mm": opening_radius,
            "inferred_opening_interval_mm": [lower, upper],
            "threshold_mm": THRESHOLD_MM,
            "threshold_side_passed": True,
            "expected_contact_force_on_first_n": float(branch["expected_contact_force_on_first_n"]),
            "rf_contact_force_on_first_n": force_z,
            "rf_contact_force_rounding_radius_n": force_radius_z,
            "rf_endpoint_values_n": checked["rf_endpoint_values_n"],
            "rf_action_reaction_residual_n": checked["rf_action_reaction_residual_n"],
            "rf_action_reaction_radius_n": checked["rf_action_reaction_radius_n"],
            "rf_vs_kdu_residual_n": checked["rf_minus_kdu_n"],
            "rf_vs_kdu_allowed_radius_n": checked["rf_minus_kdu_allowed_radius_n"],
            "host_relative_u3_mm": host_delta,
            "host_relative_u3_rounding_radius_mm": host_delta_radius,
            "host_load_n": applied,
            "contact_endpoint_mpc_occurrences": 2,
            "contact_endpoint_direct_load_or_support": False,
        })

    return {
        "schema": "rf_opening_known_answer_postrun_check/v1",
        "status": "PASS_RF_OPENING_INTERVALS_CLASSIFY_BOTH_THRESHOLD_SIDES",
        "input_freeze_sha256": digest(NATIVE / "freeze.json"),
        "solver_profile": freeze["solver_profile"],
        "source_sha256": preparation["source_sha256"],
        "dat_sha256": digest(NATIVE / "model.dat"),
        "branches": branch_results,
        "rf_helper_audit_status": rf_audit["status"],
        "rf_spring_component_count": rf_audit["spring_component_count"],
        "all_rf_action_reaction_checks_passed": rf_audit["all_spring_rf_action_reaction_passed"],
        "all_active_rf_vs_kdu_intervals_passed": rf_audit["all_active_spring_rf_matches_kdu_print_intervals"],
        "native_solve_executed": True,
        "mechanical_acceptance": False,
    }


if __name__ == "__main__":
    result = audit()
    (ATTEMPT / "postrun-check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
