#!/usr/bin/env python3
"""Offline result checks for the annular elastic and contact-wrench jobs.

No solver is invoked. This module only reads an expected.json and a future
CalculiX .dat file after parent-owned execution.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from contact_pair_output import parse_pairs


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def number(token: str) -> float:
    token = token.strip()
    # CalculiX/Fortran E formats can omit E for three-digit exponents.
    match = re.fullmatch(r"([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})", token)
    if match:
        token = match[1] + "E" + match[2]
    value = float(token.replace("D", "E").replace("d", "E"))
    require(math.isfinite(value), f"nonfinite numeric output: {token}")
    return value


def norm(vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(factor, vector):
    return tuple(factor * value for value in vector)


def vector_sum(vectors):
    vectors = list(vectors)
    return tuple(sum(v[i] for v in vectors) for i in range(3))


def wrench(rows: dict[int, tuple[float, float, float]], coordinates: dict[int, tuple[float, float, float]]):
    force = vector_sum(rows.values())
    moment = vector_sum(cross(coordinates[node], value) for node, value in rows.items())
    return (*force, *moment)


def vector_error(actual, reference):
    return norm(tuple(a - b for a, b in zip(actual, reference)))


def vector_gate(actual, reference, absolute: float, relative: float, label: str):
    error = vector_error(actual, reference)
    limit = absolute + relative * norm(reference)
    require(error <= limit,
            f"{label} error {error:.9g} exceeds predeclared {limit:.9g}")
    return {"actual": list(actual), "reference": list(reference),
            "error_norm": error, "limit": limit, "pass": True}


def wrench_gate(actual, reference, force_absolute: float, force_relative: float,
                moment_absolute: float, moment_relative: float, label: str):
    force = vector_gate(actual[:3], reference[:3], force_absolute,
                        force_relative, label + " force")
    moment = vector_gate(actual[3:], reference[3:], moment_absolute,
                         moment_relative, label + " moment")
    return {"force": force, "moment": moment, "pass": True}


def scalar_gate(actual: float, reference: float, absolute: float,
                relative: float, label: str):
    error = abs(actual - reference)
    limit = absolute + relative * max(abs(actual), abs(reference))
    require(error <= limit,
            f"{label} error {error:.9g} exceeds predeclared {limit:.9g}")
    return {"actual": actual, "reference": reference,
            "absolute_error": error, "limit": limit, "pass": True}


NODE_HEADER = re.compile(
    r"^(displacements \(vx,vy,vz\)|forces \(fx,fy,fz\)) for set (\S+) and time (\S+)$",
    re.IGNORECASE)
STRESS_HEADER = re.compile(
    r"^stresses \(elem, integ\.pnt\.,sxx,syy,szz,sxy,sxz,syz\) for set (\S+) and time (\S+)$",
    re.IGNORECASE)
ENERGY_HEADER = re.compile(
    r"^total internal energy for set (\S+) and time (\S+)$", re.IGNORECASE)


def _node_row(line: str):
    fields = line.split()
    if len(fields) != 4 or not fields[0].isdigit():
        return None
    try:
        return int(fields[0]), tuple(number(value) for value in fields[1:])
    except ValueError:
        return None


def parse_node_blocks(text: str, quantity: str, set_name: str):
    lines = text.splitlines()
    blocks = []
    for index, raw in enumerate(lines):
        header = NODE_HEADER.fullmatch(" ".join(raw.split()))
        if not header or header[1].lower() != quantity.lower() or header[2] != set_name:
            continue
        time = number(header[3])
        values = {}
        cursor = index + 1
        while cursor < len(lines):
            row = _node_row(lines[cursor])
            if row is None:
                if values:
                    break
                cursor += 1
                continue
            node, value = row
            require(node not in values, f"duplicate {quantity} node {node} for {set_name}")
            values[node] = value
            cursor += 1
        require(values, f"empty {quantity} block for {set_name} at {time}")
        blocks.append({"time": time, "values": values})
    return blocks


def final_node_block(text: str, quantity: str, set_name: str, final_time: float):
    matches = [block for block in parse_node_blocks(text, quantity, set_name)
               if abs(block["time"] - final_time) <= 1e-7]
    require(len(matches) == 1,
            f"expected one final {quantity} block for {set_name}; got {len(matches)}")
    return matches[0]["values"]


TRI6_CONTINUOUS_SIX_POINT = (
    (0.445948490915965, 0.445948490915965, 0.111690794839005),
    (0.445948490915965, 0.108103018168070, 0.111690794839005),
    (0.108103018168070, 0.445948490915965, 0.111690794839005),
    (0.091576213509771, 0.091576213509771, 0.054975871827661),
    (0.091576213509771, 0.816847572980459, 0.054975871827661),
    (0.816847572980459, 0.091576213509771, 0.054975871827661),
)
TRI6_CCX_223_GAUSS2D5 = (
    (0.166666666666667, 0.166666666666667, 0.166666666666666),
    (0.666666666666667, 0.166666666666667, 0.166666666666666),
    (0.166666666666667, 0.666666666666667, 0.166666666666666),
)


def _tri6_pressure_wrench(faces, coordinates, displacements, pressure: float,
                          quadrature):
    """Integrate follower pressure with the supplied TRI6 triangle rule."""
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    scalar_area = 0.0
    first_area_moment = [0.0, 0.0, 0.0]
    for face in faces:
        node_ids = face["node_ids"]
        sign = face["outward_sign"]
        points = [add(coordinates[node], displacements[node]) for node in node_ids]
        face_vector = [0.0, 0.0, 0.0]
        for xi, eta, weight in quadrature:
            l1, l2, l3 = 1.0 - xi - eta, xi, eta
            shape = (l1 * (2 * l1 - 1), l2 * (2 * l2 - 1),
                     l3 * (2 * l3 - 1), 4 * l1 * l2,
                     4 * l2 * l3, 4 * l3 * l1)
            dxi = (1 - 4 * l1, 4 * l2 - 1, 0.0,
                   4 * (l1 - l2), 4 * l3, -4 * l3)
            deta = (1 - 4 * l1, 0.0, 4 * l3 - 1,
                    -4 * l2, 4 * l2, 4 * (l1 - l3))
            point = tuple(sum(shape[i] * points[i][axis] for i in range(6))
                          for axis in range(3))
            tangent_xi = tuple(sum(dxi[i] * points[i][axis] for i in range(6))
                               for axis in range(3))
            tangent_eta = tuple(sum(deta[i] * points[i][axis] for i in range(6))
                                for axis in range(3))
            oriented_area_vector = scale(sign, cross(tangent_xi, tangent_eta))
            for axis in range(3):
                face_vector[axis] += oriented_area_vector[axis] * weight
            pressure_force = scale(-pressure * weight, oriented_area_vector)
            for axis in range(3):
                force[axis] += pressure_force[axis]
                moment[axis] += cross(point, pressure_force)[axis]
            area_element = norm(oriented_area_vector) * weight
            scalar_area += area_element
            for axis in range(3):
                first_area_moment[axis] += point[axis] * area_element
        require(face_vector[2] > 0.0,
                "deformed pressure face lost its outward top-face orientation")
    require(scalar_area > 0.0, "deformed pressure patch has zero area")
    centroid = tuple(value / scalar_area for value in first_area_moment)
    return (*force, *moment), scalar_area, centroid


def tri6_pressure_wrench(faces, coordinates, displacements, pressure: float):
    """Continuously integrate current TRI6 geometry with a six-point rule."""
    return _tri6_pressure_wrench(faces, coordinates, displacements, pressure,
                                 TRI6_CONTINUOUS_SIX_POINT)


def tri6_pressure_wrench_ccx_223(faces, coordinates, displacements,
                                 pressure: float):
    """Reproduce CalculiX 2.23 C3D10 pressure assembly's gauss2d5 rule."""
    return _tri6_pressure_wrench(faces, coordinates, displacements, pressure,
                                 TRI6_CCX_223_GAUSS2D5)


def parse_stresses(text: str, set_name: str, final_time: float):
    lines = text.splitlines()
    blocks = []
    for index, raw in enumerate(lines):
        header = STRESS_HEADER.fullmatch(" ".join(raw.split()))
        if not header or header[1] != set_name:
            continue
        time = number(header[2])
        rows = []
        cursor = index + 1
        while cursor < len(lines):
            fields = lines[cursor].split()
            if len(fields) != 8:
                if rows:
                    break
                cursor += 1
                continue
            if not fields[0].isdigit() or not fields[1].isdigit():
                if rows:
                    break
                cursor += 1
                continue
            rows.append((int(fields[0]), int(fields[1]),
                         tuple(number(value) for value in fields[2:])))
            cursor += 1
        require(rows, f"empty stress block for {set_name} at {time}")
        blocks.append({"time": time, "rows": rows})
    matches = [block for block in blocks if abs(block["time"] - final_time) <= 1e-7]
    require(len(matches) == 1, f"expected one final stress block for {set_name}")
    return matches[0]["rows"]


def parse_energy(text: str, set_name: str, final_time: float) -> float:
    lines = text.splitlines()
    found = []
    for index, raw in enumerate(lines):
        header = ENERGY_HEADER.fullmatch(" ".join(raw.split()))
        if not header or header[1] != set_name:
            continue
        time = number(header[2])
        if abs(time - final_time) > 1e-7:
            continue
        for next_line in lines[index + 1:]:
            fields = next_line.split()
            if not fields:
                continue
            if len(fields) == 1:
                found.append(number(fields[0]))
            break
    require(len(found) == 1, f"expected one final internal-energy total for {set_name}")
    return found[0]


def parse_coordinate_map(expected: dict):
    path = expected.get("model_coordinates_json")
    require(path is not None, "expected.json lacks model coordinate path")
    coordinates = json.loads(Path(path).read_text())
    return {int(node): tuple(value) for node, value in coordinates.items()}


def audit_affine(expected: dict, dat_text: str, coordinates: dict[int, tuple[float, float, float]]):
    oracle = expected["oracle"]
    tolerance = expected["predeclared_tolerances"]
    final_time = expected["final_time"]
    displacements = final_node_block(dat_text, "displacements (vx,vy,vz)",
                                     "ALLNODES", final_time)
    reactions = final_node_block(dat_text, "forces (fx,fy,fz)", "ALLNODES", final_time)
    boundary = set(expected["boundary_node_ids"])
    node_inventory = set(coordinates)
    require(node_inventory == set(expected["mesh"]["node_ids"]),
            "coordinate map differs from declared affine mesh-node inventory")
    require(set(displacements) == node_inventory,
            "ALLNODES displacement output differs from declared mesh-node inventory")
    require(set(reactions) == node_inventory,
            "ALLNODES RF output differs from declared mesh-node inventory")
    require(boundary <= node_inventory, "affine boundary nodes are absent from mesh inventory")

    eps = expected["kinematics"]["epsilon_zz"]
    displacement_errors = {}
    for node in node_inventory:
        _x, _y, z = coordinates[node]
        actual = displacements[node]
        reference = (0.0, 0.0, eps * z)
        displacement_errors[node] = vector_error(actual, reference)
    max_boundary_u_error = max((displacement_errors[node] for node in boundary), default=0.0)
    interior_ids = set(oracle["interior_nodes_free"])
    require(interior_ids == node_inventory - boundary,
            "declared free interior-node inventory differs from mesh topology")
    max_interior_u_error = max((displacement_errors[node] for node in interior_ids), default=0.0)
    displacement_limit = tolerance["displacement_absolute_mm"]
    require(max_boundary_u_error <= displacement_limit,
            "prescribed affine boundary field mismatch")
    require(max_interior_u_error <= displacement_limit,
            "free interior nodes do not reproduce the affine known-answer field")

    top_ids = set(expected["top_node_ids"])
    bottom_ids = set(expected["bottom_node_ids"])
    top_rows = {node: reactions[node] for node in top_ids}
    bottom_rows = {node: reactions[node] for node in bottom_ids}
    top_wrench = wrench(top_rows, coordinates)
    bottom_wrench = wrench(bottom_rows, coordinates)
    top_gate = wrench_gate(top_wrench, oracle["top_RF_wrench_N_Nmm"],
                           tolerance["force_absolute_N"], tolerance["force_relative"],
                           tolerance["moment_absolute_N_mm"], tolerance["moment_relative"],
                           "affine top reaction wrench")
    bottom_gate = wrench_gate(bottom_wrench, oracle["bottom_RF_wrench_N_Nmm"],
                              tolerance["force_absolute_N"], tolerance["force_relative"],
                              tolerance["moment_absolute_N_mm"], tolerance["moment_relative"],
                              "affine bottom reaction wrench")
    total_wrench = wrench({node: reactions[node] for node in boundary}, coordinates)
    total_gate = wrench_gate(total_wrench, oracle["all_boundary_wrench_sum_N_Nmm"],
                             tolerance["global_force_absolute_N"], 0.0,
                             tolerance["global_moment_absolute_N_mm"], 0.0,
                             "affine all-boundary reaction closure")

    stress_rows = parse_stresses(dat_text, "ANNULUS", final_time)
    by_element = {}
    for element, point, components in stress_rows:
        by_element.setdefault(element, []).append((point, components))
    element_inventory = set(expected["mesh"]["element_ids"])
    require(element_inventory == set(range(1, expected["mesh"]["elements"] + 1)),
            "declared C3D10 element-ID inventory is not contiguous from 1")
    require(set(by_element) == element_inventory,
            "stress output element IDs differ from declared C3D10 inventory")
    expected_points = set(range(1, expected["mesh"]["integration_points_per_c3d10"] + 1))
    require(all(len(points) == len(expected_points)
                and {point for point, _components in points} == expected_points
                for points in by_element.values()),
            "C3D10 integration-point inventory differs from pinned manual expectation")
    stress_reference = (oracle["sigma_xx_MPa"], oracle["sigma_yy_MPa"],
                        oracle["sigma_zz_MPa"], oracle["shear_MPa"],
                        oracle["shear_MPa"], oracle["shear_MPa"])
    max_component_error = max(abs(value - stress_reference[i])
                              for _element, _point, components in stress_rows
                              for i, value in enumerate(components))
    stress_limit = tolerance["stress_absolute_MPa"] + tolerance["stress_relative"] * abs(oracle["sigma_zz_MPa"])
    require(max_component_error <= stress_limit,
            f"affine stress error {max_component_error:.9g} exceeds {stress_limit:.9g} MPa")

    energy = parse_energy(dat_text, "ANNULUS", final_time)
    energy_gate = scalar_gate(energy, oracle["total_elastic_energy_N_mm"],
                              tolerance["energy_absolute_N_mm"],
                              tolerance["energy_relative"], "affine total internal energy")
    return {
        "status": "PASS_AFFINE_ELASTIC_METHOD_FIXTURE",
        "native_mechanical_acceptance": False,
        "max_boundary_displacement_error_mm": max_boundary_u_error,
        "max_free_interior_displacement_error_mm": max_interior_u_error,
        "top_reaction_wrench": top_gate,
        "bottom_reaction_wrench": bottom_gate,
        "all_boundary_reaction_closure": total_gate,
        "stress_rows": len(stress_rows),
        "stress_max_component_error_MPa": max_component_error,
        "stress_limit_MPa": stress_limit,
        "internal_energy": energy_gate,
    }


def audit_contact(expected: dict, dat_text: str,
                  coordinates: dict[int, tuple[float, float, float]]):
    patch = expected["loaded_patch"]
    tolerance = expected["predeclared_tolerances"]
    final_time = expected["final_time"]
    pressure_nodes = set(patch["pressure_node_ids"])
    loaded_displacements = final_node_block(dat_text, "displacements (vx,vy,vz)",
                                             "LOAD_PATCH_NODES", final_time)
    require(pressure_nodes == set(loaded_displacements),
            "pressure-face displacement node inventory changed")
    continuous_wrench, deformed_area, deformed_centroid = tri6_pressure_wrench(
        patch["tri6_face_kinematics"], coordinates, loaded_displacements,
        patch["pressure_MPa"])
    applied_wrench, solver_area, solver_centroid = tri6_pressure_wrench_ccx_223(
        patch["tri6_face_kinematics"], coordinates, loaded_displacements,
        patch["pressure_MPa"])
    quadrature_difference = tuple(discrete - continuous
                                 for discrete, continuous
                                 in zip(applied_wrench, continuous_wrench))
    quadrature_difference_gate = wrench_gate(
        quadrature_difference, [0.0] * 6,
        tolerance["quadrature_difference_force_absolute_N"], 0.0,
        tolerance["quadrature_difference_moment_absolute_N_mm"], 0.0,
        "continuous-six-point minus CalculiX-2.23-three-point pressure wrench")
    initial_wrench = (*patch["initial_applied_force_N"],
                      *patch["initial_applied_moment_about_origin_N_mm"])
    applied_change = tuple(actual - initial for actual, initial
                           in zip(applied_wrench, initial_wrench))

    gauge_u = final_node_block(dat_text, "displacements (vx,vy,vz)",
                               "UPPER_GAUGES", final_time)
    gauges = final_node_block(dat_text, "forces (fx,fy,fz)",
                              "UPPER_GAUGES", final_time)
    gauge_ids = set(expected["restraints"]["upper_in_plane_gauge_nodes"])
    require(gauge_ids == set(gauges) == set(gauge_u),
            "upper gauge-node inventory changed")
    require(not (gauge_ids & pressure_nodes),
            "gauge node directly receives distributed pressure load")
    gauge_dofs = expected["restraints"]["gauge_dofs"]
    in_plane_gauge_rows = {}
    gauge_l1 = 0.0
    for node, dofs in gauge_dofs.items():
        node_id = int(node)
        require(set(dofs) <= {1, 2} and len(dofs) > 0,
                "in-plane gauge DOF contract changed")
        force = gauges[node_id]
        in_plane_gauge_rows[node_id] = (force[0], force[1], 0.0)
        gauge_l1 += sum(abs(force[dof - 1]) for dof in dofs)
    current_coordinates = {
        node: add(xyz, gauge_u.get(node, (0.0, 0.0, 0.0)))
        for node, xyz in coordinates.items()
    }
    gauge_wrench = wrench(in_plane_gauge_rows, current_coordinates)
    gauge_limit = (tolerance["gauge_force_absolute_N"]
                   + tolerance["gauge_force_relative_to_load"]
                   * norm(applied_wrench[:3]))
    require(gauge_l1 <= gauge_limit,
            f"in-plane gauge reactions {gauge_l1:.9g} exceed {gauge_limit:.9g} N")
    free_z_rf = {str(node): gauges[node][2] for node in sorted(gauges)}

    expected_contact = tuple(-applied_wrench[i] - gauge_wrench[i]
                             for i in range(6))
    pair = parse_pairs(dat_text)
    final_pair = [row for row in pair
                  if row["slave"] == "SLAVE" and row["master"] == "MASTER"
                  and abs(row["time"] - final_time) <= 1e-7]
    quantities = {row["quantity"]: row for row in final_pair}
    require(set(quantities) == {"CF", "CFN", "CFS"},
            "final contact state must have one CF, CFN, and CFS record")
    cf = (*quantities["CF"]["force_N"], *quantities["CF"]["moment_N_mm"])
    cfn = (*quantities["CFN"]["force_N"], *quantities["CFN"]["moment_N_mm"])
    cfs = (*quantities["CFS"]["force_N"], *quantities["CFS"]["moment_N_mm"])
    contact_gate = wrench_gate(cfn, expected_contact,
                               tolerance["resultant_absolute_N"],
                               tolerance["resultant_relative"],
                               tolerance["moment_absolute_N_mm"],
                               tolerance["moment_relative"], "slave CFN wrench")
    cf_gate = wrench_gate(cf, expected_contact,
                          tolerance["resultant_absolute_N"],
                          tolerance["resultant_relative"],
                          tolerance["moment_absolute_N_mm"],
                          tolerance["moment_relative"], "slave CF wrench")
    normal_total_gate = wrench_gate(cf, cfn,
                                    tolerance["frictionless_CFS_absolute_N"], 0.0,
                                    tolerance["frictionless_CFS_absolute_N"], 0.0,
                                    "CF equals frictionless CFN")
    cfs_reference = (*patch["expected_CFS_force_N"],
                     *patch["expected_CFS_moment_N_mm"])
    cfs_gate = wrench_gate(cfs, cfs_reference,
                           tolerance["frictionless_CFS_absolute_N"], 0.0,
                           tolerance["frictionless_CFS_absolute_N"], 0.0,
                           "frictionless CFS")
    require(cfn[2] > 0.0 and applied_wrench[2] < 0.0,
            "pressure/contact vertical signs are reversed")

    base = final_node_block(dat_text, "forces (fx,fy,fz)", "GROUND", final_time)
    base_u = final_node_block(dat_text, "displacements (vx,vy,vz)", "GROUND", final_time)
    ground_ids = set(expected["restraints"]["ground_node_set"])
    require(ground_ids == set(base) == set(base_u), "ground reaction node inventory changed")
    require(not (ground_ids & pressure_nodes),
            "support node directly receives distributed pressure load")
    base_coordinates = {node: add(coordinates[node], base_u[node]) for node in ground_ids}
    base_wrench = wrench(base, base_coordinates)
    expected_ground = tuple(-applied_wrench[i] - gauge_wrench[i]
                            for i in range(6))
    support_gate = wrench_gate(base_wrench, expected_ground,
                               tolerance["resultant_absolute_N"],
                               tolerance["resultant_relative"],
                               tolerance["moment_absolute_N_mm"],
                               tolerance["moment_relative"],
                               "ground support reaction wrench")

    upper_balance = tuple(applied_wrench[i] + gauge_wrench[i] + cfn[i]
                          for i in range(6))
    upper_balance_gate = wrench_gate(
        upper_balance, [0.0] * 6,
        tolerance["equilibrium_wrench_absolute_N_or_Nmm"], 0.0,
        tolerance["equilibrium_wrench_absolute_N_or_Nmm"], 0.0,
        "upper-body applied/gauge/contact closure")
    whole_balance = tuple(applied_wrench[i] + gauge_wrench[i] + base_wrench[i]
                          for i in range(6))
    whole_balance_gate = wrench_gate(
        whole_balance, [0.0] * 6,
        tolerance["equilibrium_wrench_absolute_N_or_Nmm"], 0.0,
        tolerance["equilibrium_wrench_absolute_N_or_Nmm"], 0.0,
        "whole-model applied/gauge/support closure")

    return {
        "status": "PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE",
        "native_mechanical_acceptance": False,
        "loaded_patch_FE_area_mm2": patch["tri6_straight_sided_FE_area_mm2"],
        "loaded_patch_centroid_mm": patch["FE_area_centroid_mm"],
        "deformed_loaded_patch_FE_area_mm2": deformed_area,
        "deformed_loaded_patch_centroid_mm": list(deformed_centroid),
        "deformed_pressure_wrench_N_Nmm": list(applied_wrench),
        "ccx_2_23_discrete_three_point_pressure_wrench_N_Nmm": list(applied_wrench),
        "ccx_2_23_discrete_loaded_patch_area_mm2": solver_area,
        "ccx_2_23_discrete_loaded_patch_centroid_mm": list(solver_centroid),
        "continuous_six_point_pressure_wrench_N_Nmm": list(continuous_wrench),
        "pressure_quadrature_difference_solver_minus_continuous_N_Nmm":
            list(quadrature_difference),
        "pressure_quadrature_difference_gate": quadrature_difference_gate,
        "change_from_initial_pressure_wrench_N_Nmm": list(applied_change),
        "slave_contact_CF": cf_gate,
        "slave_contact_CFN": contact_gate,
        "CF_matches_CFN": normal_total_gate,
        "frictionless_CFS": cfs_gate,
        "upper_body_force_balance": upper_balance_gate,
        "ground_support_reaction": support_gate,
        "whole_model_force_balance": whole_balance_gate,
        "upper_gauge_in_plane_reaction_l1_N": gauge_l1,
        "upper_gauge_force_limit_N": gauge_limit,
        "upper_gauge_in_plane_reaction_wrench_N_Nmm": list(gauge_wrench),
        "upper_gauge_free_z_RF_N_by_node_not_treated_as_reaction": free_z_rf,
        "gauge_reactions_checked_separately": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", choices=("affine", "contact"))
    parser.add_argument("expected", type=Path)
    parser.add_argument("dat", type=Path)
    parser.add_argument("coordinates", type=Path,
                        help="generated model_coordinates.json used for moment integration")
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text())
    expected["model_coordinates_json"] = str(args.coordinates)
    coordinates_raw = json.loads(args.coordinates.read_text())
    coordinates = {int(node): tuple(value) for node, value in coordinates_raw.items()}
    dat_text = args.dat.read_text(errors="strict")
    if args.job == "affine":
        result = audit_affine(expected, dat_text, coordinates)
    else:
        result = audit_contact(expected, dat_text, coordinates)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
