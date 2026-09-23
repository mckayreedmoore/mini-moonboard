"""Compatibility fixture for the two-vertical-bolt principal/header joint.

This is a reduced rigid-body spring diagnostic on the current source-built CAD
cuts.  Positive stiffnesses are explicit numerical sensitivities, not measured
complete-joint properties.  The fixture does not replace a fresh whole-frame
demand solve or qualify any resistance mode.
"""

from __future__ import annotations

import json
import math

import numpy as np
from scipy.optimize import minimize

from scripts import owner_barrel_vertical_center_contact_screen as contact

SCHEMA = "owner_barrel_vertical_center_joint_fixture/v1"
ROTATION_SCALE_MM = 100.0
GROUP_Y_MM = contact.GROUP_Y_MM
INTERFACE_Z_MM = contact.INTERFACE_Z_MM
THREAD_Z_MM = 305.0
BORE_DIAMETER_MM = 7.5
BOLT_DIAMETER_MM = 6.35
NOMINAL_CENTERED_CLEARANCE_MM = (BORE_DIAMETER_MM - BOLT_DIAMETER_MM) / 2

# These deliberately span the old exploratory inputs.  They are numerical
# sensitivities only: the repo contains no defensible positive lower bound for
# complete axial or face-contact stiffness.
STIFFNESS_SCENARIOS = (
    {
        "name": "soft_diagnostic",
        "axial_n_per_mm": 100.0,
        "lateral_n_per_mm": 2723.847,
        "face_n_per_mm3": 10.0,
    },
    {
        "name": "reference_diagnostic",
        "axial_n_per_mm": 1000.0,
        "lateral_n_per_mm": 3940.354,
        "face_n_per_mm3": 100.0,
    },
    {
        "name": "stiff_diagnostic",
        "axial_n_per_mm": 10000.0,
        "lateral_n_per_mm": 10000.0,
        "face_n_per_mm3": 1000.0,
    },
)
CLEARANCE_SCENARIOS_MM = (0.0, NOMINAL_CENTERED_CLEARANCE_MM, 2 * NOMINAL_CENTERED_CLEARANCE_MM)
MAX_SMALL_ROTATION_RAD = 0.05
MAX_SMALL_POINT_MOTION_MM = 2.0
CONTACT_GRID_COUNTS = (8, 8)


def _round(value, digits=6):
    return round(float(value), digits)


def _point_matrix(point, origin):
    """Map scaled six-DOF motion to displacement at one point."""
    r = (np.asarray(point, dtype=float) - np.asarray(origin, dtype=float)) / ROTATION_SCALE_MM
    cross = np.asarray(
        ((0.0, r[2], -r[1]), (-r[2], 0.0, r[0]), (r[1], -r[0], 0.0))
    )
    return np.column_stack((np.eye(3), cross))


def _generalized_load(force, moment):
    return np.concatenate(
        (np.asarray(force, dtype=float), np.asarray(moment, dtype=float) / ROTATION_SCALE_MM)
    )


def _spring_state(q, geometry, origin, scenario, clearance_mm):
    internal_gradient = np.zeros(6)
    tangent = np.zeros((6, 6))
    energy = 0.0
    contacts = []
    bolts = []

    for cell in geometry["cells"]:
        matrix = _point_matrix(cell["point_xyz_mm"], origin)
        gap = float(matrix[2] @ q)
        stiffness = scenario["face_n_per_mm3"] * cell["tributary_area_mm2"]
        compression = stiffness * max(-gap, 0.0)
        if compression > 0:
            row = matrix[2]
            internal_gradient += stiffness * gap * row
            tangent += stiffness * np.outer(row, row)
            energy += 0.5 * stiffness * gap**2
        contacts.append(
            {
                "name": cell["name"],
                "gap_mm": gap,
                "compression_n": compression,
                "pressure_mpa": compression / cell["tributary_area_mm2"],
                "area_mm2": cell["tributary_area_mm2"],
                "point_xyz_mm": cell["point_xyz_mm"],
            }
        )

    for index, bolt in enumerate(geometry["bolts"]):
        point = list(bolt["thread_axis_xyz_mm"])
        if abs(point[2] - THREAD_Z_MM) > 1e-6:
            raise ValueError("Vertical principal thread elevation changed")
        matrix = _point_matrix(point, origin)
        displacement = matrix @ q
        extension = float(displacement[2])
        axial = scenario["axial_n_per_mm"] * max(extension, 0.0)
        if axial > 0:
            row = matrix[2]
            internal_gradient += scenario["axial_n_per_mm"] * extension * row
            tangent += scenario["axial_n_per_mm"] * np.outer(row, row)
            energy += 0.5 * scenario["axial_n_per_mm"] * extension**2

        lateral = displacement[:2]
        radius = float(np.linalg.norm(lateral))
        overtravel = max(radius - clearance_mm, 0.0)
        shear = np.zeros(2)
        if overtravel > 0:
            direction = lateral / radius
            shear = scenario["lateral_n_per_mm"] * overtravel * direction
            internal_gradient += matrix[:2].T @ shear
            energy += 0.5 * scenario["lateral_n_per_mm"] * overtravel**2
            local_tangent = scenario["lateral_n_per_mm"] * (
                (1 - clearance_mm / radius) * np.eye(2)
                + clearance_mm / radius * np.outer(direction, direction)
            )
            tangent += matrix[:2].T @ local_tangent @ matrix[:2]
        bolts.append(
            {
                "row": "rear" if index == 0 else "forward",
                "point_xyz_mm": point,
                "extension_mm": extension,
                "tension_n": axial,
                "lateral_displacement_xy_mm": lateral,
                "radial_slip_mm": radius,
                "clearance_overtravel_mm": overtravel,
                "shear_xy_n": shear,
                "shear_resultant_n": float(np.linalg.norm(shear)),
            }
        )
    return energy, internal_gradient, tangent, contacts, bolts


def solve_wrench(geometry, force, moment, scenario, clearance_mm):
    """Solve one monotonic centered-start wrench on a fixed-header fixture."""
    origin = np.asarray(
        (geometry["bolts"][0]["thread_axis_xyz_mm"][0], GROUP_Y_MM, INTERFACE_Z_MM)
    )
    load = _generalized_load(force, moment)

    def objective(q):
        energy, gradient, *_ = _spring_state(
            q, geometry, origin, scenario, clearance_mm
        )
        return energy - load @ q, gradient - load

    starts = (np.zeros(6), np.sign(load) * 1e-4)
    candidates = [
        minimize(
            objective,
            start,
            jac=True,
            method="L-BFGS-B",
            options={"ftol": 1e-14, "gtol": 1e-9, "maxiter": 5000, "maxls": 100},
        )
        for start in starts
    ]
    solved = min(candidates, key=lambda row: row.fun)
    q = solved.x.copy()
    # Polish the compatibility solution with its current exact tangent.  This
    # removes L-BFGS termination noise without changing the spring law.
    for _ in range(30):
        energy, gradient, tangent, _contacts, _bolts = _spring_state(
            q, geometry, origin, scenario, clearance_mm
        )
        residual = load - gradient
        if (
            max(abs(residual[:3])) <= 1e-6
            and max(abs(residual[3:])) * ROTATION_SCALE_MM <= 1e-4
        ):
            break
        if np.linalg.matrix_rank(tangent, tol=1e-7) < 6:
            break
        step = np.linalg.solve(tangent, residual)
        old_objective = energy - load @ q
        for exponent in range(20):
            trial = q + step / 2**exponent
            trial_energy = _spring_state(
                trial, geometry, origin, scenario, clearance_mm
            )[0] - load @ trial
            if trial_energy <= old_objective + 1e-12:
                q = trial
                break
        else:
            break
    energy, gradient, tangent, contacts, bolts = _spring_state(
        q, geometry, origin, scenario, clearance_mm
    )
    residual = load - gradient
    rank = int(np.linalg.matrix_rank(tangent, tol=1e-7))
    converged = bool(
        solved.success
        and max(abs(residual[:3])) <= 1e-4
        and max(abs(residual[3:])) * ROTATION_SCALE_MM <= 1e-3
    )
    active_contact = [row for row in contacts if row["compression_n"] > 1e-8]
    total_contact = sum(row["compression_n"] for row in active_contact)
    contact_centroid = None
    if total_contact:
        contact_centroid = sum(
            row["compression_n"] * np.asarray(row["point_xyz_mm"])
            for row in active_contact
        ) / total_contact
    max_opening = max(row["gap_mm"] for row in contacts)
    min_gap = min(row["gap_mm"] for row in contacts)
    point_motions = [
        _point_matrix(row["point_xyz_mm"], origin) @ q for row in contacts
    ] + [_point_matrix(row["point_xyz_mm"], origin) @ q for row in bolts]
    rotation_norm_rad = float(np.linalg.norm(q[3:]) / ROTATION_SCALE_MM)
    maximum_point_motion_mm = max(float(np.linalg.norm(row)) for row in point_motions)
    small_kinematics_valid = bool(
        rotation_norm_rad <= MAX_SMALL_ROTATION_RAD
        and maximum_point_motion_mm <= MAX_SMALL_POINT_MOTION_MM
    )
    return {
        "converged": converged,
        "solver_success": bool(solved.success),
        "solver_message": solved.message,
        "force_xyz_n": [_round(value) for value in force],
        "moment_xyz_nmm": [_round(value) for value in moment],
        "translation_xyz_mm": [_round(value, 9) for value in q[:3]],
        "rotation_xyz_mrad": [
            _round(1000 * value / ROTATION_SCALE_MM, 9) for value in q[3:]
        ],
        "rotation_norm_rad": _round(rotation_norm_rad, 9),
        "maximum_rigid_point_motion_mm": _round(maximum_point_motion_mm, 9),
        "small_kinematics_valid": small_kinematics_valid,
        "interpretation_status": (
            "WITHIN_DECLARED_LINEARIZED_KINEMATIC_SCREEN"
            if small_kinematics_valid
            else "NUMERICAL_ONLY_OUTSIDE_LINEARIZED_KINEMATIC_SCREEN"
        ),
        "maximum_face_opening_mm": _round(max(0.0, max_opening), 9),
        "maximum_face_approach_mm": _round(max(0.0, -min_gap), 9),
        "active_contact_cell_count": len(active_contact),
        "active_contact_area_mm2": _round(sum(row["area_mm2"] for row in active_contact)),
        "contact_total_n": _round(total_contact),
        "contact_resultant_xyz_mm": (
            [_round(value) for value in contact_centroid] if contact_centroid is not None else None
        ),
        "maximum_cell_average_pressure_mpa": _round(
            max((row["pressure_mpa"] for row in contacts), default=0.0)
        ),
        "bolts": [
            {
                **{key: row[key] for key in ("row", "point_xyz_mm")},
                "extension_mm": _round(row["extension_mm"], 9),
                "tension_n": _round(row["tension_n"]),
                "radial_slip_mm": _round(row["radial_slip_mm"], 9),
                "clearance_overtravel_mm": _round(row["clearance_overtravel_mm"], 9),
                "shear_xy_n": [_round(value) for value in row["shear_xy_n"]],
                "shear_resultant_n": _round(row["shear_resultant_n"]),
                "combined_vector_resultant_n": _round(
                    math.hypot(row["tension_n"], row["shear_resultant_n"])
                ),
            }
            for row in bolts
        ],
        "axial_row_share": (
            [
                _round(row["tension_n"] / sum(bolt["tension_n"] for bolt in bolts))
                for row in bolts
            ]
            if sum(row["tension_n"] for row in bolts) > 1e-8
            else [0.0, 0.0]
        ),
        "active_tangent_rank": rank,
        "active_tangent_condition_number": (
            _round(np.linalg.cond(tangent)) if rank == 6 else None
        ),
        "equilibrium_residual_force_xyz_n": [_round(value, 9) for value in residual[:3]],
        "equilibrium_residual_moment_xyz_nmm": [
            _round(value * ROTATION_SCALE_MM, 9) for value in residual[3:]
        ],
        "spring_energy_nmm": _round(energy),
    }


def _proxy_wrenches(proxy, geometry):
    original = []
    for group, case, side, interface in contact._proxy_cases(proxy):
        _origin, force, moment = contact._shifted_wrench(side, interface)
        original.append(
            {
                "name": f"proxy:{group}:{case['series']}:{case['case']}:{side}",
                "kind": "old_topology_combined_proxy",
                "side": side,
                "force": force,
                "moment": moment,
            }
        )
    rows = []
    for row in original:
        rows.append(row)
        rows.append(
            {
                **row,
                "name": row["name"].replace("proxy:", "proxy_reversed:", 1),
                "kind": "old_topology_combined_proxy_full_reversal",
                "force": -row["force"],
                "moment": -row["moment"],
            }
        )
    maxima = np.max(
        np.abs(
            np.asarray(
                [np.concatenate((row["force"], row["moment"])) for row in rows]
            )
        ),
        axis=0,
    )
    components = ("fx", "fy", "fz", "mx", "my", "mz")
    for index, (name, magnitude) in enumerate(zip(components, maxima, strict=True)):
        if magnitude <= 0:
            continue
        for sign in (-1.0, 1.0):
            vector = np.zeros(6)
            vector[index] = sign * magnitude
            rows.append(
                {
                    "name": f"synthetic:{name}:{'positive' if sign > 0 else 'negative'}",
                    "kind": "artificial_signed_component_reversal",
                    "side": "left",
                    "force": vector[:3],
                    "moment": vector[3:],
                }
            )
    return rows, maxima


def build_report():
    _material, _hardware, proxy, _barrel, _washer, _bolt = contact.capacity._load_inputs()
    geometry = contact._source_geometry(grid_counts=CONTACT_GRID_COUNTS)
    wrench_rows, proxy_maxima = _proxy_wrenches(proxy, geometry)
    results = []
    for scenario in STIFFNESS_SCENARIOS:
        for clearance_mm in CLEARANCE_SCENARIOS_MM:
            for row in wrench_rows:
                solved = solve_wrench(
                    geometry[row["side"]],
                    row["force"],
                    row["moment"],
                    scenario,
                    clearance_mm,
                )
                results.append(
                    {
                        "name": row["name"],
                        "kind": row["kind"],
                        "side": row["side"],
                        "stiffness_scenario": scenario["name"],
                        "clearance_mm": clearance_mm,
                        **solved,
                    }
                )
    converged = [row for row in results if row["converged"]]
    interpretable = [row for row in converged if row["small_kinematics_valid"]]
    all_converged = len(converged) == len(results)
    def governing(field, rows=converged):
        row = max(rows, key=lambda item: item[field])
        return {"value": row[field], "case": row["name"], "stiffness": row["stiffness_scenario"], "clearance_mm": row["clearance_mm"]}

    bolt_rows = [
        (case, bolt)
        for case in interpretable
        for bolt in case["bolts"]
    ]
    interpretable_bolt_rows = [
        (case, bolt)
        for case in interpretable
        for bolt in case["bolts"]
    ]
    max_tension_case, max_tension = max(bolt_rows, key=lambda pair: pair[1]["tension_n"])
    valid_max_tension_case, valid_max_tension = max(
        interpretable_bolt_rows, key=lambda pair: pair[1]["tension_n"]
    )
    valid_max_shear_case, valid_max_shear = max(
        interpretable_bolt_rows, key=lambda pair: pair[1]["shear_resultant_n"]
    )
    valid_max_combined_case, valid_max_combined = max(
        interpretable_bolt_rows,
        key=lambda pair: pair[1]["combined_vector_resultant_n"],
    )
    max_slip_case, max_slip = max(
        interpretable_bolt_rows, key=lambda pair: pair[1]["radial_slip_mm"]
    )
    max_overtravel_case, max_overtravel = max(
        interpretable_bolt_rows,
        key=lambda pair: pair[1]["clearance_overtravel_mm"],
    )
    rear_shares = [
        case["axial_row_share"][0]
        for case in interpretable
        if sum(case["axial_row_share"]) > 0
    ]
    shear_rear_shares = []
    for case in interpretable:
        shear_total = sum(row["shear_resultant_n"] for row in case["bolts"])
        if shear_total > 1e-8:
            shear_rear_shares.append(case["bolts"][0]["shear_resultant_n"] / shear_total)
    maximum_valid_total_tension = max(
        sum(row["tension_n"] for row in case["bolts"]) for case in interpretable
    )
    maximum_valid_total_contact = max(case["contact_total_n"] for case in interpretable)
    mechanism_lower_model = {
        "zero_lateral_stiffness_rank_maximum": 3,
        "pure_fx_fy_mz_behavior": "UNBOUNDED_MECHANISM",
        "meaning": "No supported positive complete-joint lateral stiffness lower bound exists; the captive-barrel sensitivity cannot be promoted to a bound.",
    }
    finite_decision = "BLOCKED"
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "revised two-vertical-bolt principal/header reduced CAD fixture",
        "native_solve_run": False,
        "geometry": {
            side: {
                "bolt_thread_points_xyz_mm": [row["thread_axis_xyz_mm"] for row in data["bolts"]],
                "contact_cell_count": len(data["cells"]),
                "net_contact_area_mm2": _round(data["net_area_mm2"]),
            }
            for side, data in geometry.items()
        },
        "modeled_nominal_stack_points": {
            "bolt_seat_z_mm": 238.9,
            "interface_z_mm": INTERFACE_Z_MM,
            "thread_axis_z_mm": THREAD_Z_MM,
            "seat_to_thread_mm": _round(THREAD_Z_MM - 238.9),
            "modeled_bore_diameter_mm": BORE_DIAMETER_MM,
            "nominal_bolt_diameter_mm": BOLT_DIAMETER_MM,
        },
        "model": {
            "principal": "rigid six-DOF body; header fixed",
            "face": "refined exact-area tributary cells from the nominal combined-cut face; compression only; zero initial gap",
            "contact_grid_counts": CONTACT_GRID_COUNTS,
            "contact_discretization_status": "REFINED_TRIBUTARY_SCREEN_WITHOUT_MESH_CONVERGENCE",
            "adverse_cut_geometry_run": False,
            "adverse_cut_geometry_status": "BLOCKED_BY_UNCONTROLLED_BORE_SEAT_SECTION_AND_MACHINING_TOLERANCES",
            "bolt_axial": "two tension-only point springs at actual thread centers; zero preload",
            "bolt_lateral": "two radially coupled shear springs after circular clearance",
            "friction": "none",
            "reversal": "independent monotonic centered-start signed cases; not cyclic history",
            "stiffness_scenarios": STIFFNESS_SCENARIOS,
            "clearance_scenarios_mm": CLEARANCE_SCENARIOS_MM,
            "linearized_kinematic_screen": {
                "maximum_rotation_norm_rad": MAX_SMALL_ROTATION_RAD,
                "maximum_rigid_point_motion_mm": MAX_SMALL_POINT_MOTION_MM,
                "purpose": "Separate small-motion diagnostic results from numerical solutions outside the point-spring geometry domain; these are declared screen limits, not material limits.",
            },
            "stiffness_status": "UNQUALIFIED_NUMERICAL_SENSITIVITY_NOT_BOUNDS",
            "supported_complete_joint_stiffness_bounds": {
                "lower_n_per_mm": None,
                "upper_n_per_mm": None,
                "status": "NO_SUPPORTED_LOWER_OR_UPPER_BOUND",
            },
        },
        "load_set": {
            "old_combined_proxy_count": sum(row["kind"].startswith("old_") for row in wrench_rows),
            "artificial_signed_component_count": sum(row["kind"].startswith("artificial_") for row in wrench_rows),
            "old_proxy_absolute_component_maxima_fx_fy_fz_mx_my_mz": [_round(value) for value in proxy_maxima],
            "fresh_48_pair_case_count": 0,
        },
        "results": results,
        "summary": {
            "case_scenario_count": len(results),
            "all_positive_stiffness_cases_converged": all_converged,
            "small_kinematics_valid_case_count": len(interpretable),
            "outside_small_kinematics_case_count": len(converged) - len(interpretable),
            "raw_numerical_maximum_face_opening_mm": governing("maximum_face_opening_mm"),
            "valid_screen_maximum_face_opening_mm": governing("maximum_face_opening_mm", interpretable),
            "valid_screen_maximum_face_approach_mm": governing("maximum_face_approach_mm", interpretable),
            "valid_screen_maximum_cell_average_pressure_mpa": governing("maximum_cell_average_pressure_mpa", interpretable),
            "raw_numerical_maximum_bolt_tension": {"value_n": max_tension["tension_n"], "row": max_tension["row"], "case": max_tension_case["name"], "stiffness": max_tension_case["stiffness_scenario"], "clearance_mm": max_tension_case["clearance_mm"]},
            "valid_screen_maximum_bolt_tension": {"value_n": valid_max_tension["tension_n"], "row": valid_max_tension["row"], "case": valid_max_tension_case["name"], "stiffness": valid_max_tension_case["stiffness_scenario"], "clearance_mm": valid_max_tension_case["clearance_mm"]},
            "valid_screen_maximum_bolt_shear": {"value_n": valid_max_shear["shear_resultant_n"], "row": valid_max_shear["row"], "case": valid_max_shear_case["name"], "stiffness": valid_max_shear_case["stiffness_scenario"], "clearance_mm": valid_max_shear_case["clearance_mm"]},
            "valid_screen_maximum_bolt_vector_resultant": {"value_n": valid_max_combined["combined_vector_resultant_n"], "row": valid_max_combined["row"], "case": valid_max_combined_case["name"], "stiffness": valid_max_combined_case["stiffness_scenario"], "clearance_mm": valid_max_combined_case["clearance_mm"]},
            "valid_screen_maximum_radial_slip": {"value_mm": max_slip["radial_slip_mm"], "row": max_slip["row"], "case": max_slip_case["name"], "stiffness": max_slip_case["stiffness_scenario"], "clearance_mm": max_slip_case["clearance_mm"]},
            "valid_screen_maximum_clearance_overtravel": {"value_mm": max_overtravel["clearance_overtravel_mm"], "row": max_overtravel["row"], "case": max_overtravel_case["name"], "stiffness": max_overtravel_case["stiffness_scenario"], "clearance_mm": max_overtravel_case["clearance_mm"]},
            "rear_axial_row_share_range_for_tension_cases": [_round(min(rear_shares)), _round(max(rear_shares))],
            "rear_shear_row_share_range_for_shear_cases": [_round(min(shear_rear_shares)), _round(max(shear_rear_shares))],
            "minimum_active_tangent_rank": min(row["active_tangent_rank"] for row in converged),
            "rank_below_six_case_count": sum(row["active_tangent_rank"] < 6 for row in converged),
            "rank_note": "Rank below six occurs in isolated modes with unloaded neutral directions; it is not promoted to a global stability claim.",
            "unsupported_lower_model": mechanism_lower_model,
        },
        "mode_specific_required_resistance": {
            "bolt_barrel_thread_axial": {
                "valid_screen_per_row_n_before_preload": valid_max_tension["tension_n"],
                "valid_screen_two_row_total_n_before_preload": _round(maximum_valid_total_tension),
                "required_design_resistance_n": None,
                "status": "VALID_SUBSET_SCREEN_ONLY_NOT_A_DEMAND_ENVELOPE",
            },
            "washer_bearing_and_flexure": {
                "valid_screen_per_washer_n_before_preload": valid_max_tension["tension_n"],
                "required_design_resistance_n": None,
                "flexural_demand": "NOT_COMPUTABLE_FROM_POINT_SPRING_FIXTURE",
                "status": "CAPACITY_UNRESOLVED",
            },
            "shank_shear_and_wood_embedment": {
                "valid_screen_per_row_shear_n": valid_max_shear["shear_resultant_n"],
                "required_design_resistance_n": None,
                "bolt_bending_moment_nmm": None,
                "status": "SHEAR_FORCE_ONLY_BENDING_AND_CAPACITY_UNRESOLVED",
            },
            "combined_bolt_tension_shear": {
                "valid_screen_maximum_simultaneous_vector_resultant_n": valid_max_combined["combined_vector_resultant_n"],
                "required_design_resistance_n": None,
                "interaction_equation": None,
                "status": "NUMERIC_VECTOR_DEMAND_INTERACTION_UNRESOLVED",
            },
            "barrel_wood_bearing_wall_and_lobes": {
                "valid_screen_per_barrel_radial_load_n_before_preload": valid_max_tension["tension_n"],
                "required_design_resistance_n": None,
                "barrel_wall_or_lobe_moment_nmm": None,
                "status": "RADIAL_FORCE_ONLY_DISTRIBUTION_AND_CAPACITY_UNRESOLVED",
            },
            "principal_split_net_two_plane_and_group_tearout": {
                "required_scalar_resistance_n": None,
                "reason": "No adopted mapping converts the six-DOF row actions into these interacting brittle wood modes.",
                "status": "NOT_COMPUTABLE_WITHOUT_ADOPTED_RESISTANCE_MODEL",
            },
            "face_compression": {
                "valid_screen_maximum_cell_average_pressure_mpa": governing("maximum_cell_average_pressure_mpa", interpretable)["value"],
                "valid_screen_total_contact_resultant_n": _round(maximum_valid_total_contact),
                "required_design_resistance_mpa": None,
                "local_elastic_peak_mpa": None,
                "status": "AVERAGE_SCREEN_DEMAND_LOCAL_PEAK_AND_CAPACITY_UNRESOLVED",
            },
        },
        "fresh_demand_blocker": {
            "status": "BLOCKED",
            "reason": "The moved center posts miss four inherited header/post barrel axes; the new seam backers occupy those axes, while moved-post/header and backer/frame load paths are undefined. The repository also forbids native solves.",
        },
        "decision": {
            "finite_decision": finite_decision,
            "reason": "Positive-stiffness captive-barrel diagnostics equilibrate, but no supported positive complete-joint stiffness lower bound, controlled clearance, complete resistance set, or fresh 48-pair demand suite exists.",
            "cad_go": False,
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
        "limits": [
            "The reduced nominal point-spring stack is not an actual hardware-stack model: it omits the bolt head and washer footprint, thread engagement, barrel body/contact, bolt beam, and cylindrical bore-contact distribution.",
            "Only nominal source-built CAD cuts were used; no adverse bore-axis, diameter, seat, timber-section, or combined machining-tolerance solids were available.",
            "The refined tributary contact grid has no mesh-convergence proof and samples cell centroids rather than integrating partial-cell contact.",
            "Zero initial face gap and rigid members omit flatness, seating, local wood deformation, and preload.",
            "Old ML24Z/topology wrenches and artificial reversals are screens, not fresh candidate demands.",
            "Cell pressure is piecewise-uniform average, not local elastic peak.",
            "No physical resistance is inferred from solver convergence or tangent rank.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
