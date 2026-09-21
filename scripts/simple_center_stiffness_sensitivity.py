"""Compatibility-aware PB02 spring sensitivity on authenticated old actions.

The stiffnesses are explicit trial ratios, not measured properties or design
inputs. Reactions are historical-action sensitivity results, not PB02 demands.
"""

import json

import numpy as np
from scipy.optimize import minimize

from scripts.simple_center_connected_kinematics import (
    CONTACT_PARTITION,
    CONTACT_PARTITION_FINGERPRINT,
    EDGES,
    NODES,
    ROTATION_SCALE_MM,
    constraint_rows,
)
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT, ACTIVE_TRIAL
from scripts.simple_center_signed_duty_fixture import _fixture_load, _source_cases

REFERENCE_STIFFNESS_N_PER_MM = 10000.0
FORMULA_ANALOGY_LATERAL_N_PER_MM = 3086.746
SCENARIOS = (
    ("reference", 1.0, 1.0, 1.0),
    ("lateral_soft", 0.1, 1.0, 1.0),
    ("lateral_stiff", 10.0, 1.0, 1.0),
    ("axial_soft", 1.0, 0.1, 1.0),
    ("axial_stiff", 1.0, 10.0, 1.0),
    ("contact_soft", 1.0, 1.0, 0.1),
    ("contact_stiff", 1.0, 1.0, 10.0),
    ("bolt_dominant_contrast", 10.0, 10.0, 0.1),
    ("contact_dominant_contrast", 0.1, 0.1, 10.0),
    (
        "formula_anchored_lateral",
        FORMULA_ANALOGY_LATERAL_N_PER_MM / REFERENCE_STIFFNESS_N_PER_MM,
        1.0,
        1.0,
    ),
)


def _active_rows(rows, gaps, tolerance=1e-9, *, boundary_active=False):
    return np.asarray(
        [
            row["kind"] == "bolt_shear"
            or (
                row["kind"] == "bolt_tension"
                and (gap >= -tolerance if boundary_active else gap > tolerance)
            )
            or (
                row["kind"] == "contact_compression"
                and (gap <= tolerance if boundary_active else gap < -tolerance)
            )
            for row, gap in zip(rows, gaps, strict=True)
        ]
    )


def _validate_self_equilibrium(load, tolerance=1e-9):
    net_force = np.asarray([load[offset::6].sum() for offset in range(3)])
    net_moment = np.asarray(
        [load[offset::6].sum() * ROTATION_SCALE_MM for offset in range(3, 6)]
    )
    if np.max(np.abs(net_force)) > tolerance or np.max(np.abs(net_moment)) > tolerance:
        raise ValueError("PB02 stiffness fixture load is not self-equilibrated")


def solve_case(
    extracted,
    *,
    scenario,
    lateral_factor,
    axial_factor,
    contact_factor,
):
    """Minimize one-sided spring energy and recover an exact active-set solve."""
    if min(lateral_factor, axial_factor, contact_factor) <= 0:
        raise ValueError("Sensitivity factors must be positive")
    rows = constraint_rows(closed=EDGES, axial=True)
    inventory = {
        kind: sum(row["kind"] == kind for row in rows)
        for kind in ("bolt_shear", "bolt_tension", "contact_compression")
    }
    if inventory != {
        "bolt_shear": 20,
        "bolt_tension": 10,
        "contact_compression": CONTACT_PARTITION["contact_row_count"],
    } or len({row["name"] for row in rows}) != len(rows):
        raise ValueError("PB02 labeled spring inventory changed")
    compatibility = np.asarray([row["row"] for row in rows])
    free = compatibility[:, 6:]
    load, _ = _fixture_load(extracted)
    _validate_self_equilibrium(load)
    free_load = load[6:]
    mean_contact_area = sum(
        interface["net_overlap_area_mm2"]
        for interface in CONTACT_PARTITION["interfaces"].values()
    ) / len(CONTACT_PARTITION["interfaces"])
    contact_stiffness_per_area = (
        REFERENCE_STIFFNESS_N_PER_MM * contact_factor / mean_contact_area
    )
    stiffness = np.asarray(
        [
            REFERENCE_STIFFNESS_N_PER_MM
            * (
                lateral_factor
                if row["kind"] == "bolt_shear"
                else axial_factor
                if row["kind"] == "bolt_tension"
                else contact_stiffness_per_area
                * row["tributary_area_mm2"]
                / REFERENCE_STIFFNESS_N_PER_MM
            )
            for row in rows
        ]
    )

    def energy_gradient(displacement):
        gaps = free @ displacement
        active = _active_rows(rows, gaps, tolerance=0)
        spring = stiffness * gaps * active
        energy = 0.5 * gaps @ spring - free_load @ displacement
        return energy, free.T @ spring - free_load

    optimized = minimize(
        energy_gradient,
        np.zeros(free.shape[1]),
        jac=True,
        method="L-BFGS-B",
        options={"ftol": 1e-15, "gtol": 1e-10, "maxiter": 10000, "maxls": 100},
    )
    displacement = optimized.x
    seen = set()
    singular_refinement_advances = 0
    for refinement in range(20):
        gaps = free @ displacement
        active = _active_rows(rows, gaps, boundary_active=True)
        signature = tuple(active)
        if signature in seen:
            raise ValueError("PB02 spring active set repeated during exact refinement")
        seen.add(signature)
        stiffness_matrix = free.T @ (stiffness[:, None] * active[:, None] * free)
        rank = int(np.linalg.matrix_rank(stiffness_matrix, tol=1e-9))
        if rank != free.shape[1]:
            _, singular_values, right = np.linalg.svd(stiffness_matrix)
            nullspace = right[singular_values <= 1e-9].T
            drive = nullspace @ (nullspace.T @ free_load)
            if np.linalg.norm(drive) <= 1e-8:
                raise ValueError("PB02 spring active tangent has a neutral mechanism")
            direction = drive / np.linalg.norm(drive)
            rates = free @ direction
            crossings = []
            for index, (row, is_active, gap, rate) in enumerate(
                zip(rows, active, gaps, rates, strict=True)
            ):
                if is_active:
                    continue
                if (
                    row["kind"] == "bolt_tension"
                    and rate > 1e-12
                    or row["kind"] == "contact_compression"
                    and rate < -1e-12
                ):
                    distance = -gap / rate
                else:
                    continue
                if distance >= -1e-9:
                    crossings.append((max(0.0, distance), row["name"], index))
            if not crossings:
                raise ValueError(
                    "PB02 spring active tangent cannot reach another unilateral row"
                )
            distance, _, _ = min(crossings)
            displacement += (distance + 1e-8) * direction
            singular_refinement_advances += 1
            continue
        exact = np.linalg.solve(stiffness_matrix, free_load)
        exact_active = _active_rows(rows, free @ exact, boundary_active=True)
        displacement = exact
        if np.array_equal(exact_active, active):
            break
    else:
        raise ValueError("PB02 spring active set did not converge")

    gaps = free @ displacement
    active = _active_rows(rows, gaps, boundary_active=True)
    reactions = -stiffness * gaps * active
    residual = load + compatibility.T @ reactions
    force_residual = np.concatenate(
        [residual[6 * index : 6 * index + 3] for index in range(len(NODES))]
    )
    moment_residual = np.concatenate(
        [
            residual[6 * index + 3 : 6 * index + 6] * ROTATION_SCALE_MM
            for index in range(len(NODES))
        ]
    )
    maximum_force_residual = float(np.max(np.abs(force_residual)))
    maximum_moment_residual = float(np.max(np.abs(moment_residual)))
    if maximum_force_residual > 1e-5 or maximum_moment_residual > 1e-3:
        raise ValueError("PB02 spring solution failed whole-system equilibrium")

    edges = {}
    for edge in EDGES:
        selected = [
            (row, float(reaction), bool(is_active))
            for row, reaction, is_active in zip(rows, reactions, active, strict=True)
            if row["edge"] == edge
        ]
        edges[edge] = {
            "maximum_bolt_shear_n": max(
                abs(reaction)
                for row, reaction, _ in selected
                if row["kind"] == "bolt_shear"
            ),
            "total_bolt_tension_n": sum(
                -reaction
                for row, reaction, is_active in selected
                if row["kind"] == "bolt_tension" and is_active
            ),
            "total_contact_compression_n": sum(
                reaction
                for row, reaction, is_active in selected
                if row["kind"] == "contact_compression" and is_active
            ),
            "active_tension_rows": sum(
                row["kind"] == "bolt_tension" and is_active
                for row, _, is_active in selected
            ),
            "active_contact_rows": sum(
                row["kind"] == "contact_compression" and is_active
                for row, _, is_active in selected
            ),
        }
        contacts = [
            (row, reaction)
            for row, reaction, is_active in selected
            if row["kind"] == "contact_compression" and is_active
        ]
        centroid = np.asarray(CONTACT_PARTITION["interfaces"][edge]["net_centroid_mm"])
        # Compatibility reactions act on the second body along the canonical
        # first-to-second direction. Report force on the first body, matching
        # the native PB02 ownership convention.
        contact_forces = [
            -reaction * np.asarray(row["direction"]) for row, reaction in contacts
        ]
        edges[edge]["contact_aggregation"] = {
            "force_resultant_n": sum(contact_forces, np.zeros(3)).tolist(),
            "moment_resultant_about_net_centroid_nmm": sum(
                (
                    np.cross(np.asarray(row["point_mm"]) - centroid, force)
                    for (row, _), force in zip(contacts, contact_forces, strict=True)
                ),
                np.zeros(3),
            ).tolist(),
            "active_tributary_area_mm2": sum(
                row["tributary_area_mm2"] for row, _ in contacts
            ),
            "peak_average_cell_pressure_n_per_mm2": max(
                (reaction / row["tributary_area_mm2"] for row, reaction in contacts),
                default=0.0,
            ),
        }
    row_results = [
        {
            "name": row["name"],
            "edge": row["edge"],
            "kind": row["kind"],
            "first": row["first"],
            "second": row["second"],
            "point_mm": row["point_mm"],
            "direction": row["direction"],
            "active": bool(is_active),
            "relative_displacement_mm": float(gap),
            "signed_reaction_n": float(reaction),
            "stiffness_n_per_mm": float(value),
            **(
                {
                    "tributary_area_mm2": row["tributary_area_mm2"],
                    "average_cell_pressure_n_per_mm2": (
                        float(reaction) / row["tributary_area_mm2"]
                        if is_active
                        else 0.0
                    ),
                }
                if row["kind"] == "contact_compression"
                else {}
            ),
            "spring_energy_nmm": float(0.5 * value * gap**2 if is_active else 0),
        }
        for row, reaction, gap, is_active, value in zip(
            rows, reactions, gaps, active, stiffness, strict=True
        )
    ]
    constitutive_law_passed = all(
        (
            abs(
                row["signed_reaction_n"]
                + row["stiffness_n_per_mm"] * row["relative_displacement_mm"]
            )
            <= 1e-5
            if row["active"]
            else abs(row["signed_reaction_n"]) <= 1e-8
        )
        for row in row_results
    ) and all(
        row["kind"] == "bolt_shear"
        or (
            row["kind"] == "bolt_tension"
            and (
                row["relative_displacement_mm"] >= -1e-9
                if row["active"]
                else row["relative_displacement_mm"] <= 1e-9
            )
            and row["signed_reaction_n"] <= 1e-5
        )
        or (
            row["kind"] == "contact_compression"
            and (
                row["relative_displacement_mm"] <= 1e-9
                if row["active"]
                else row["relative_displacement_mm"] >= -1e-9
            )
            and row["signed_reaction_n"] >= -1e-5
        )
        for row in row_results
    )
    if not constitutive_law_passed:
        raise ValueError("PB02 spring solution failed one-sided constitutive laws")
    return {
        "case": extracted["source"]["case"],
        "scenario": scenario,
        "lateral_to_reference_stiffness_factor": lateral_factor,
        "axial_to_reference_stiffness_factor": axial_factor,
        "contact_mean_total_to_reference_stiffness_factor": contact_factor,
        "contact_partition_fingerprint": CONTACT_PARTITION_FINGERPRINT,
        "contact_grid_resolution": CONTACT_PARTITION["grid_resolution"],
        "trial_stiffness_n_per_mm": {
            "bolt_shear_per_direction": (REFERENCE_STIFFNESS_N_PER_MM * lateral_factor),
            "bolt_axial_tension": REFERENCE_STIFFNESS_N_PER_MM * axial_factor,
            "face_contact_law": (
                "mean-interface-total-calibrated common areal density"
            ),
            "face_contact_mean_total": (REFERENCE_STIFFNESS_N_PER_MM * contact_factor),
            "face_contact_per_area_n_per_mm3": contact_stiffness_per_area,
        },
        "seed_optimizer": {
            "success": bool(optimized.success),
            "iterations": int(optimized.nit),
            "message": optimized.message,
            "exact_refinement_cycles": refinement + 1,
            "singular_refinement_advances": singular_refinement_advances,
            "active_tangent_rank": rank,
            "active_tangent_condition_number": float(np.linalg.cond(stiffness_matrix)),
        },
        "equilibrium": {
            "maximum_force_residual_n": maximum_force_residual,
            "maximum_moment_residual_nmm": maximum_moment_residual,
            "constitutive_law_passed": constitutive_law_passed,
        },
        "edges": edges,
        "rows": row_results,
    }


def screen():
    """Run ten explicit stiffness sensitivities for five old-action examples."""
    cases = _source_cases()
    results = [
        solve_case(
            case,
            scenario=name,
            lateral_factor=lateral,
            axial_factor=axial,
            contact_factor=contact,
        )
        for case in cases
        for name, lateral, axial, contact in SCENARIOS
    ]
    edge_envelopes = {}
    for edge in EDGES:
        edge_envelopes[edge] = {
            field: {
                "minimum_n": min(result["edges"][edge][field] for result in results),
                "maximum_n": max(result["edges"][edge][field] for result in results),
            }
            for field in (
                "maximum_bolt_shear_n",
                "total_bolt_tension_n",
                "total_contact_compression_n",
            )
        }
    case_sensitivity = {}
    for case in cases:
        case_name = case["source"]["case"]
        selected = [row for row in results if row["case"] == case_name]
        case_sensitivity[case_name] = {}
        for edge in EDGES:
            case_sensitivity[case_name][edge] = {}
            for field in (
                "maximum_bolt_shear_n",
                "total_bolt_tension_n",
                "total_contact_compression_n",
            ):
                values = [row["edges"][edge][field] for row in selected]
                low, high = min(values), max(values)
                case_sensitivity[case_name][edge][field] = {
                    "minimum_n": low,
                    "maximum_n": high,
                    "maximum_to_minimum": high / low if low > 1e-9 else None,
                    "absolute_spread_n": high - low,
                }
    return {
        "scope": "PB02 compatibility-aware historical-action stiffness sensitivity",
        "variant_id": ACTIVE_TRIAL.variant_id,
        "source_fingerprint": ACTIVE_FINGERPRINT,
        "case_count": len(cases),
        "attempted_scenario_count": len(cases) * len(SCENARIOS),
        "converged_scenario_count": len(results),
        "reference_stiffness_n_per_mm": REFERENCE_STIFFNESS_N_PER_MM,
        "contact_partition": CONTACT_PARTITION,
        "scenarios": [
            {
                "name": name,
                "lateral_factor": lateral,
                "axial_factor": axial,
                "contact_total_factor": contact,
            }
            for name, lateral, axial, contact in SCENARIOS
        ],
        "formula_anchored_lateral_analogy": {
            "value_n_per_mm": FORMULA_ANALOGY_LATERAL_N_PER_MM,
            "formula": "rho_mean^1.5 * d / 23",
            "assumed_rho_mean_kg_per_m3": 500,
            "active_trial_diameter_mm": 6.35,
            "qualified_input": False,
        },
        "common_stiffness_scale_is_not_qualified": True,
        "results": results,
        "cross_case_and_scenario_reaction_envelopes": edge_envelopes,
        "fixed_case_stiffness_sensitivity": case_sensitivity,
        "limitations": [
            "Stiffness factors are sensitivity ratios, not measured or qualified properties.",
            "Old complete interface actions are authenticated examples, not PB02 design demands.",
            "Five cases omit a12-forward and do not form the required candidate envelope.",
            "Point springs do not resolve bearing pressure, bolt bending, clearance, preload, splitting, or strength.",
        ],
        "strength_or_fabrication_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
