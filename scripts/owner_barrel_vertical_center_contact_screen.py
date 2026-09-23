"""Signed contact/tension equilibrium screen for vertical principal barrels.

Two vertical bolts act in tension only on each principal.  Exact combined-cut
header/principal face cells act in compression only and without friction.  The
screen uses authenticated old-topology proxy wrenches and adapted reference
limits; it is neither a stiffness solution nor a fresh candidate load case.
"""

from __future__ import annotations

import json
import math

import numpy as np
from scipy.optimize import linprog

from scripts import owner_barrel_vertical_center_breakout as breakout
from scripts import owner_barrel_vertical_center_capacity as capacity
from scripts import owner_barrel_vertical_center_probe as probe
from scripts.owner_barrel_native_face_contacts import _contact_cells, _touching_face

SCHEMA = "owner_barrel_vertical_center_contact_screen/v1"
GROUP_Y_MM = -106.0
INTERFACE_Z_MM = 277.0
CONTACT_FC_PERP_MPA = 625 * capacity.MPA_PER_PSI
FORCE_RESIDUAL_TOL_N = 1.0e-6
MOMENT_RESIDUAL_TOL_NMM = 1.0e-4


def _round(value, digits=6):
    return round(float(value), digits)


def _cross(first, second):
    return np.cross(np.asarray(first, dtype=float), np.asarray(second, dtype=float))


def _source_geometry():
    """Return exact net horizontal contact cells and current barrel records."""
    combined, wood, joint, _barrel = breakout._combined_solids()
    result = {}
    for side in probe.SIDES:
        principal_name = f"base_principal_center_{side}"
        header = wood["base_header"]
        principal = wood[principal_name]
        cut_header = combined["base_header"]["shape"]
        cut_principal = combined[principal_name]["shape"]

        station = f"vertical_principal_{side}"
        face, gross_patch = _touching_face(principal, header, station)
        outward = face.normalAt().normalized()
        if (
            max(
                abs(a - b)
                for a, b in zip(outward.toTuple(), (0.0, 0.0, -1.0), strict=True)
            )
            > 1.0e-9
        ):
            raise ValueError(f"{station}: principal face normal changed")
        cut_patch = gross_patch.intersect(cut_principal).intersect(cut_header)
        cells = _contact_cells(
            gross_patch,
            cut_patch,
            outward,
            station,
            refine_y=True,
        )
        bolts = sorted(
            (row for row in joint["records"] if row["hosts"][1] == principal_name),
            key=lambda row: row["bolt_seat_xyz_mm"][1],
        )
        if len(cells) != 16 or len(bolts) != 2:
            raise ValueError(f"{station}: expected 16 cells and two bolts")
        result[side] = {
            "gross_area_mm2": gross_patch.Area(),
            "net_area_mm2": cut_patch.Area(),
            "net_centroid_xyz_mm": list(cut_patch.Center().toTuple()),
            "cells": cells,
            "bolts": bolts,
        }
    return result


def _proxy_cases(proxy):
    for group in ("accepted_default_v2", "a1_rear_sensitivity"):
        for case in proxy[group]:
            for side in probe.SIDES:
                interface = case["sides"][side]["interfaces"]["principal_header"]
                yield group, case, side, interface


def _shifted_wrench(side, interface):
    origin = np.asarray((-70.0 if side == "left" else 70.0, GROUP_Y_MM, INTERFACE_Z_MM))
    force = np.asarray(interface["on_center_member"]["force_xyz_n"], dtype=float)
    old_origin = np.asarray(interface["origin_xyz_mm"], dtype=float)
    old_moment = np.asarray(
        interface["on_center_member"]["moment_xyz_nmm"], dtype=float
    )
    moment = old_moment + _cross(old_origin - origin, force)
    return origin, force, moment


def _row_reference_n(row_name, resistance):
    bearing = resistance["wood_barrel_bearing"]
    factor = bearing["provisional_distance_factors"][row_name][
        "provisional_minimum_factor"
    ]
    references = {
        "nds_fabbri_distance_sensitivity": (
            bearing["nds_fabbri_nominal_reference_n"] * factor
        ),
        "fpl_form_distance_sensitivity": (
            bearing["fpl_divide_by_four_reference_n"] * factor
        ),
        "ideal_header_washer": resistance["header_washer_bearing"][
            "nominal_reference_n"
        ],
        "raw_bolt_proof": resistance["bolt_constituent_proof"]["minimum_proof_n"],
    }
    return min(references.values()), references


def _solve_vertical(wrench, geometry, resistance):
    """Minimize maximum adapted-reference use for Fz, Mx and My."""
    origin, force, moment = wrench
    bolts = geometry["bolts"]
    cells = geometry["cells"]
    variable_count = len(bolts) + len(cells) + 1
    utilization_index = variable_count - 1
    equilibrium = np.zeros((3, variable_count))
    labels = []
    references = []

    for index, bolt in enumerate(bolts):
        point = np.asarray(
            (
                bolt["bolt_seat_xyz_mm"][0],
                bolt["bolt_seat_xyz_mm"][1],
                INTERFACE_Z_MM,
            )
        )
        lever = point - origin
        bolt_force = np.asarray((0.0, 0.0, -1.0))
        bolt_moment = _cross(lever, bolt_force)
        equilibrium[:, index] = (bolt_force[2], bolt_moment[0], bolt_moment[1])
        row_name = "rear" if index == 0 else "forward"
        reference_n, components = _row_reference_n(row_name, resistance)
        labels.append(f"bolt_tension_{row_name}")
        references.append((reference_n, components))

    for offset, cell in enumerate(cells, len(bolts)):
        point = np.asarray(cell["point_xyz_mm"], dtype=float)
        lever = point - origin
        contact_force = np.asarray((0.0, 0.0, 1.0))
        contact_moment = _cross(lever, contact_force)
        equilibrium[:, offset] = (
            contact_force[2],
            contact_moment[0],
            contact_moment[1],
        )
        labels.append(cell["name"])
        references.append(
            (
                CONTACT_FC_PERP_MPA * cell["tributary_area_mm2"],
                {
                    "ideal_fc_perp_cell_bearing": CONTACT_FC_PERP_MPA
                    * cell["tributary_area_mm2"]
                },
            )
        )

    inequalities = []
    right_hand = []
    for index, (reference_n, _components) in enumerate(references):
        row = np.zeros(variable_count)
        row[index] = 1.0
        row[utilization_index] = -reference_n
        inequalities.append(row)
        right_hand.append(0.0)
    objective = np.zeros(variable_count)
    objective[utilization_index] = 1.0
    target = np.asarray((force[2], moment[0], moment[1]))
    solved = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.asarray(right_hand),
        A_eq=equilibrium,
        b_eq=target,
        bounds=[(0.0, None)] * variable_count,
        method="highs",
    )
    result = {
        "feasible": bool(solved.success),
        "solver_status": int(solved.status),
        "solver_message": solved.message,
    }
    if not solved.success:
        return result

    values = solved.x[:-1]
    bolt_values = values[: len(bolts)]
    contact_values = values[len(bolts) :]
    residual = equilibrium @ solved.x - target
    contact_total = float(contact_values.sum())
    contact_point = None
    if contact_total > 0:
        contact_point = (
            sum(
                force_n * np.asarray(cell["point_xyz_mm"], dtype=float)
                for force_n, cell in zip(contact_values, cells, strict=True)
            )
            / contact_total
        ).tolist()
    row_records = []
    for index, (label, value, (reference_n, components)) in enumerate(
        zip(labels, values, references, strict=True)
    ):
        row_records.append(
            {
                "name": label,
                "force_n": _round(value),
                "adapted_reference_n": _round(reference_n),
                "reference_ratio": _round(value / reference_n),
                "reference_components_n": {
                    name: _round(component) for name, component in components.items()
                },
                "kind": "bolt_tension" if index < len(bolts) else "face_compression",
            }
        )
    return {
        **result,
        "adapted_reference_utilization": _round(solved.x[utilization_index]),
        "target_fz_mx_my": [_round(value) for value in target],
        "bolt_tension_n": [_round(value) for value in bolt_values],
        "contact_total_n": _round(contact_total),
        "contact_resultant_xyz_mm": (
            [_round(value) for value in contact_point] if contact_point else None
        ),
        "maximum_piecewise_uniform_cell_pressure_mpa": _round(
            max(
                force_n / cell["tributary_area_mm2"]
                for force_n, cell in zip(contact_values, cells, strict=True)
            )
        ),
        "equilibrium_residual_fz_mx_my": [_round(value, 9) for value in residual],
        "rows": row_records,
    }


def _lateral_resolution(force, moment):
    """Chosen equal-Fy two-row witness for Fx, Fy and Mz; no capacity claim."""
    pitch = probe.PRINCIPAL_ROWS_Y_MM[1] - probe.PRINCIPAL_ROWS_Y_MM[0]
    rear_x = force[0] / 2 + moment[2] / pitch
    forward_x = force[0] / 2 - moment[2] / pitch
    shared_y = force[1] / 2
    return {
        "rear_force_xy_n": [_round(rear_x), _round(shared_y)],
        "forward_force_xy_n": [_round(forward_x), _round(shared_y)],
        "maximum_resultant_n": _round(
            max(math.hypot(rear_x, shared_y), math.hypot(forward_x, shared_y))
        ),
        "capacity_qualified": False,
    }


def _wrench_matrix_rank(geometry, *, collapse_contact_x=False, collapse_rows=False):
    """Return six-DOF reaction-matrix rank for one principal joint."""
    center_x = geometry["bolts"][0]["bolt_seat_xyz_mm"][0]
    columns = []
    for bolt in geometry["bolts"]:
        point = np.asarray(
            (
                center_x,
                GROUP_Y_MM if collapse_rows else bolt["bolt_seat_xyz_mm"][1],
                INTERFACE_Z_MM,
            ),
            dtype=float,
        )
        lever = point - np.asarray((center_x, GROUP_Y_MM, INTERFACE_Z_MM))
        for force in (
            np.asarray((1.0, 0.0, 0.0)),
            np.asarray((0.0, 1.0, 0.0)),
            np.asarray((0.0, 0.0, -1.0)),
        ):
            columns.append(np.concatenate((force, _cross(lever, force))))
    for cell in geometry["cells"]:
        point = np.asarray(cell["point_xyz_mm"], dtype=float)
        if collapse_contact_x:
            point[0] = center_x
        lever = point - np.asarray((center_x, GROUP_Y_MM, INTERFACE_Z_MM))
        force = np.asarray((0.0, 0.0, 1.0))
        columns.append(np.concatenate((force, _cross(lever, force))))
    return int(np.linalg.matrix_rank(np.column_stack(columns), tol=1.0e-9))


def build_report():
    material, _hardware, proxy, barrel, washer, bolt = capacity._load_inputs()
    geometry_report = probe.build_report()
    if (
        geometry_report["decision"]["nominal_and_provisional_tolerance_geometry"]
        != "CANDIDATE"
    ):
        raise ValueError("Vertical principal geometry is not a candidate")
    demand_report = capacity._proxy_demands(proxy)
    resistance = capacity._resistance_screen(
        barrel,
        washer,
        bolt,
        geometry_report,
        demand_report["maximum_bolt_tension_row_n"],
        material,
    )
    geometry = _source_geometry()
    cases = []
    for group, case, side, interface in _proxy_cases(proxy):
        origin, force, moment = _shifted_wrench(side, interface)
        vertical = _solve_vertical((origin, force, moment), geometry[side], resistance)
        cases.append(
            {
                "source_group": group,
                "series": case["series"],
                "case": case["case"],
                "side": side,
                "shifted_force_xyz_n": [_round(value) for value in force],
                "shifted_moment_xyz_nmm": [_round(value) for value in moment],
                "vertical_contact_tension": vertical,
                "lateral_two_row_resolution": _lateral_resolution(force, moment),
            }
        )
    feasible = all(row["vertical_contact_tension"]["feasible"] for row in cases)
    residuals_pass = feasible and all(
        abs(row["vertical_contact_tension"]["equilibrium_residual_fz_mx_my"][0])
        <= FORCE_RESIDUAL_TOL_N
        and max(
            abs(value)
            for value in row["vertical_contact_tension"][
                "equilibrium_residual_fz_mx_my"
            ][1:]
        )
        <= MOMENT_RESIDUAL_TOL_NMM
        for row in cases
    )
    feasible_cases = [
        row for row in cases if row["vertical_contact_tension"]["feasible"]
    ]
    maximum = max(
        feasible_cases,
        key=lambda row: row["vertical_contact_tension"][
            "adapted_reference_utilization"
        ],
        default=None,
    )
    maximum_lateral = max(
        row["lateral_two_row_resolution"]["maximum_resultant_n"] for row in cases
    )
    proxy_ranges = {
        component: [
            min(row["shifted_" + kind][index] for row in cases),
            max(row["shifted_" + kind][index] for row in cases),
        ]
        for component, kind, index in (
            ("fz_n", "force_xyz_n", 2),
            ("mx_nmm", "moment_xyz_nmm", 0),
            ("my_nmm", "moment_xyz_nmm", 1),
        )
    }
    topology = {
        side: {
            "nominal_six_dof_wrench_matrix_rank": _wrench_matrix_rank(row),
            "rank_with_contact_x_collapsed_to_bolt_axis": _wrench_matrix_rank(
                row, collapse_contact_x=True
            ),
            "rank_with_bolt_rows_collapsed_to_group_y": _wrench_matrix_rank(
                row, collapse_rows=True
            ),
        }
        for side, row in geometry.items()
    }
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "two-vertical-bolt principal/header signed proxy equilibrium",
        "contact_geometry": {
            side: {
                "gross_area_mm2": _round(row["gross_area_mm2"]),
                "net_area_mm2": _round(row["net_area_mm2"]),
                "net_centroid_xyz_mm": [
                    _round(value) for value in row["net_centroid_xyz_mm"]
                ],
                "cell_count": len(row["cells"]),
                "cell_area_sum_mm2": _round(
                    sum(cell["tributary_area_mm2"] for cell in row["cells"])
                ),
                "x_centroid_range_mm": [
                    min(cell["point_xyz_mm"][0] for cell in row["cells"]),
                    max(cell["point_xyz_mm"][0] for cell in row["cells"]),
                ],
                "y_centroid_range_mm": [
                    min(cell["point_xyz_mm"][1] for cell in row["cells"]),
                    max(cell["point_xyz_mm"][1] for cell in row["cells"]),
                ],
            }
            for side, row in geometry.items()
        },
        "model": {
            "bolt_axial": "tension only; force on principal is -Z",
            "face_contact": "compression only; force on principal is +Z",
            "friction": "none",
            "contact_cell_pressure_reference": "unadjusted DF-L No.2 Fc-perp 625 psi",
            "bolt_tension_reference": "minimum of adapted barrel-bearing sensitivities, ideal washer bearing, and raw bolt proof",
            "objective": "minimize maximum adapted-reference ratio",
            "compatibility_or_stiffness_solved": False,
            "reported_cell_pressure": "piecewise-uniform cell average, not elastic peak",
        },
        "topology": topology,
        "case_count": len(cases),
        "cases": cases,
        "summary": {
            "all_vertical_equilibria_feasible": feasible,
            "all_equilibrium_residuals_pass": residuals_pass,
            "maximum_adapted_reference_utilization": (
                maximum["vertical_contact_tension"]["adapted_reference_utilization"]
                if maximum is not None
                else None
            ),
            "maximum_case": (
                {
                    key: maximum[key]
                    for key in ("source_group", "series", "case", "side")
                }
                if maximum is not None
                else None
            ),
            "maximum_lateral_row_resultant_n": maximum_lateral,
            "available_proxy_action_ranges": proxy_ranges,
            "my_path": (
                "EXISTS_IN_SIGNED_PROXY_EQUILIBRIUM"
                if feasible and residuals_pass
                else "NO_PATH_IN_SCREEN"
            ),
            "fresh_barrel_case_count": 0,
            "missing_case": "a12-forward",
        },
        "decision": {
            "finite_decision": "EVIDENCE_BLOCKED",
            "my_topology_screen": (
                "PATH_EXISTS_REFERENCE_ONLY"
                if feasible and residuals_pass
                else "NO_PATH_IN_SCREEN"
            ),
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
        "limits": [
            "Old-topology proxy wrenches are not fresh barrel-candidate demands; A12-forward is absent.",
            "LP proves one statically admissible witness, not unique force sharing, compatibility, gap state, or stiffness.",
            "Bearing and contact limits are adapted/raw references, not adopted complete-joint capacities.",
            "Lateral bolt resolution has no wood, barrel, bolt, or combined-action capacity attached.",
            "Signed combined-cut splitting, row tear-out, group tear-out, and two-plane shear remain separate.",
            "STAFAST material, thread class, proof, wall, and dimensional tolerances remain uncontrolled.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
