"""Saved panel RHS correction and first-order applicability diagnostics.

Reuses authenticated mass-only quadrature and interval-eight load vectors.
No CAD, material stiffness assembly, contact assembly or response solve occurs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finished_support_audit as support_audit
from scripts import thin_bolted_panel_coupled as coupled
from scripts import thin_bolted_panel_mechanics as method

OPERATORS = method.ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.npz"
OPERATORS_SHA = "2b97d8c1741a0fbef119eb00b3f43bdf5f76e802b4851962a62fc555f1813468"
COUPLED_SHA = "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0"
REFERENCE = np.array([0., 750., 1100.])


def mass_only_quadrature(panel: dict) -> tuple[np.ndarray, np.ndarray]:
    """Exactly the frozen unperforated-minus-bore/bevel mass integration."""
    basis = panel["basis"]
    points, weights = basis.quadrature()
    positions, areas = [points], [weights]
    for hole in panel["holes"]:
        xy, area = method.disk_quadrature(np.asarray(hole["xy_mm"]), hole["diameter_mm"] / 2)
        positions.append(xy); areas.append(-area)
    xy, area, remaining = method.bevel_quadrature(basis, panel["geometry"]["front_height"])
    if len(area):
        positions.append(xy); areas.append(-area * (1 - remaining))
    xy, area = np.concatenate(positions), np.concatenate(areas)
    panel["mass_xy"], panel["mass_weights"] = xy, area / area.sum()
    panel["mass_row"] = area @ basis.values(xy) / area.sum()
    return xy, area


def rigid_modes(panel: dict, reference=REFERENCE) -> np.ndarray:
    """Frozen six global rigid-motion fields, with unscaled angular columns."""
    basis, geometry = panel["basis"], panel["geometry"]
    greville = np.array([np.mean(basis.knots[i + 1:i + 4]) for i in range(basis.order)])
    x, y = np.meshgrid(greville * basis.width, greville * basis.height, indexing="ij")
    positions = geometry["origin"] + np.c_[x.ravel(), y.ravel()] @ geometry["axes"][:, :2].T
    fields = []
    for component in range(6):
        displacement = np.broadcast_to(np.eye(3)[component], positions.shape) if component < 3 else np.cross(
            np.eye(3)[component - 3], positions - reference)
        fields.append((displacement @ geometry["axes"]).T.ravel())
    return np.asarray(fields).T


def load_wrench(loads: list, reference=REFERENCE) -> np.ndarray:
    value = np.zeros(6)
    for row in loads:
        force = np.asarray(row["force_xyz_n"])
        value += np.r_[force, np.cross(np.asarray(row["point_xyz_mm"]) - reference, force)]
    return value


def rhs_correction(rigid: np.ndarray, uncorrected: np.ndarray,
                   desired_wrench: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    delta = desired_wrench - rigid.T @ uncorrected
    correction = rigid @ np.linalg.solve(rigid.T @ rigid, delta)
    return correction, delta


def affine_traction_interpretation(panel: dict, points: np.ndarray, area: np.ndarray,
                                  delta: np.ndarray, correction: np.ndarray) -> dict:
    """Find affine surface tractions with the same six wrench corrections.

    This traction alternative reproduces the wrench, not the exact coefficient
    load projection used by the producer. Its difference is reported explicitly.
    """
    geometry, basis = panel["geometry"], panel["basis"]
    world = geometry["origin"] + points @ geometry["axes"][:, :2].T
    displacement = []
    for component in range(6):
        displacement.append(np.broadcast_to(np.eye(3)[component], world.shape) if component < 3 else
                            np.cross(np.eye(3)[component - 3], world - REFERENCE))
    rigid_at_points = np.stack(displacement, axis=2)
    local = np.einsum("ij,qjk->qik", geometry["axes"].T, rigid_at_points)
    interpolation = basis.values(points)
    operator = np.concatenate([interpolation.T @ (area[:, None] * local[:, i, :]) for i in range(3)])
    rigid = rigid_modes(panel)
    coefficients = np.linalg.solve(rigid.T @ operator, delta)
    generalized = operator @ coefficients
    traction = np.einsum("qik,k->qi", rigid_at_points, coefficients)
    error = rigid.T @ generalized - delta
    difference = generalized - correction
    return {"traction_global_rigid_field_coefficients": coefficients.tolist(),
            "traction_constant_coefficient_unit": "N/mm2",
            "traction_angular_gradient_coefficient_unit": "N/mm3",
            "force_wrench_residual_norm_n": float(np.linalg.norm(error[:3])),
            "moment_wrench_residual_norm_nmm": float(np.linalg.norm(error[3:])),
            "maximum_sampled_affine_traction_norm_n_per_mm2": float(np.linalg.norm(traction, axis=1).max()),
            "generalized_load_difference_from_producer_projection_norm_n": float(np.linalg.norm(difference)),
            "generalized_load_difference_work_on_saved_q_nmm": float(difference @ panel["q"]),
            "is_exact_producer_generalized_load_interpretation": False,
            "limit": "Formal affine traction uses net mass-area weights, including bore/bevel subtraction; it is an alternative wrench-equivalent load and is not substituted into the saved solution."}


def warp_slope_markers(panel: dict, q: np.ndarray, samples: int = 81) -> dict:
    basis = panel["basis"]
    x, y = np.meshgrid(np.linspace(0, basis.width, samples),
                        np.linspace(0, basis.height, samples), indexing="ij")
    points = np.c_[x.ravel(), y.ravel()]
    fields = coupled.plate_fields(panel, points, q)
    affine = np.linalg.lstsq(np.c_[np.ones(len(points)), points], fields["outward_w_mm"], rcond=None)[0]
    sx, sy = fields["slope_x"] - affine[1], fields["slope_upslope"] - affine[2]
    norm = np.hypot(sx, sy)
    geometric = np.c_[.5 * sx**2, .5 * sy**2, sx * sy]
    n = basis.size
    dx, dy = basis.values(points, 1), basis.values(points, 0, 1)
    linear = np.c_[dx @ q[:n], dy @ q[n:2 * n], dy @ q[:n] + dx @ q[n:2 * n]]
    peak = int(norm.argmax())
    return {"sample_count_per_axis": samples,
            "best_affine_outward_coefficients_mm_mm_per_mm": affine.tolist(),
            "maximum_sampled_affine_removed_slope_norm": float(norm[peak]),
            "witness_xy_mm": points[peak].tolist(),
            "simultaneous_affine_removed_slopes_x_upslope": [float(sx[peak]), float(sy[peak])],
            "simultaneous_von_karman_markers_ex_ey_engineering_gamma": geometric[peak].tolist(),
            "simultaneous_first_order_membrane_strains_ex_ey_engineering_gamma": linear[peak].tolist(),
            "maximum_half_affine_removed_slope_norm_squared": float(.5 * norm[peak]**2),
            "maximum_abs_von_karman_component_markers": np.abs(geometric).max(axis=0).tolist(),
            "maximum_abs_first_order_membrane_strain_components": np.abs(linear).max(axis=0).tolist(),
            "geometrically_nonlinear_solution_or_applicability_pass": False,
            "limit": "Affine slope removal is a diagnostic proxy for assembly tilt. Squared slope terms are von Karman strain scales; they do not update in-plane motion, equilibrium, loads, material axes or contacts, and are not objective finite-rotation strains."}


def evaluate(field: Path) -> dict:
    pins = {str(OPERATORS.relative_to(method.ROOT)): OPERATORS_SHA,
            str(Path(coupled.__file__).relative_to(method.ROOT)): COUPLED_SHA,
            str(coupled.DATUMS.relative_to(method.ROOT)): coupled.DATUMS_SHA,
            str(coupled.ASSESSMENT.relative_to(method.ROOT)): coupled.ASSESSMENT_SHA,
            str(Path(method.__file__).relative_to(method.ROOT)): coupled.METHOD_SHA,
            str(Path(support_audit.__file__).relative_to(method.ROOT)): coupled.SUPPORT_AUDIT_SHA}
    coupled.verify_pins(pins)
    state = json.loads(field.read_text())
    coupled.validate_state(state)
    audit = support_audit.audit_finished_state(state)
    method.require(audit["independent_finished_support_and_equilibrium_checks_pass"], "finished support gate failed")
    method.require(state["parameters"]["panel_intervals"] == 8
                   and state["accessory_placement"] == "retained-original-top-hold",
                   "pinned interval-eight original-top load operators required")
    coupled.verify_pins(state["source_sha256"])
    integrated = json.loads(method.INTEGRATED.read_text())
    panels = coupled.prepared_datums(state, json.loads(coupled.ASSESSMENT.read_text()),
                                     json.loads(coupled.DATUMS.read_text()), integrated)
    case = next(row for row in method.load_cases(integrated)
                if row["id"] == ("permanent" if state["case_id"] == "gravity-only" else state["case_id"]))
    rows = []
    total_work = 0.
    with np.load(OPERATORS, allow_pickle=False) as operators:
        for name, panel in panels.items():
            points, area = mass_only_quadrature(panel)
            initial, _ = method.panel_case_load(panel, case, integrated, "original_top")
            retained = operators[f"{name}/load/{case['id']}"]
            method.require(np.max(abs(initial - retained)) < 1e-8,
                           f"mass-only reconstruction differs from pinned load operator: {name}")
            loads = [row for row in state["body_applied_loads"] if row["body"] == name]
            metal = [row for row in loads if row["id"].startswith("bolt-weight/")]
            for row in metal:
                initial += method.point_matrix(panel, row["point_xyz_mm"]).T @ row["force_xyz_n"]
            rigid = rigid_modes(panel)
            desired = load_wrench(loads)
            correction, delta = rhs_correction(rigid, initial, desired)
            corrected = initial + correction
            residual = rigid.T @ corrected - desired
            work = float(correction @ panel["q"])
            total_work += work
            rows.append({"panel": name, "state_id": state["state_id"],
                         "panel_owned_metal_mass_share_count": len(metal),
                         "mass_only_npz_load_max_abs_difference_n": float(abs(method.panel_case_load(panel, case, integrated, "original_top")[0] - retained).max()),
                         "uncorrected_rigid_wrench_n_nmm": (rigid.T @ initial).tolist(),
                         "desired_exact_body_wrench_n_nmm": desired.tolist(),
                         "rigid_wrench_correction_n_nmm": delta.tolist(),
                         "force_correction_norm_n": float(np.linalg.norm(delta[:3])),
                         "moment_correction_norm_nmm": float(np.linalg.norm(delta[3:])),
                         "generalized_correction_norm_n": float(np.linalg.norm(correction)),
                         "generalized_correction_inf_n": float(abs(correction).max()),
                         "generalized_correction_norm_over_corrected_load_norm": float(np.linalg.norm(correction) / np.linalg.norm(corrected)),
                         "correction_work_on_actual_q_nmm": work,
                         "uncorrected_panel_external_work_on_actual_q_nmm": float(initial @ panel["q"]),
                         "corrected_panel_external_work_on_actual_q_nmm": float(corrected @ panel["q"]),
                         "force_wrench_residual_norm_n": float(np.linalg.norm(residual[:3])),
                         "moment_wrench_residual_norm_nmm": float(np.linalg.norm(residual[3:])),
                         "wrench_equivalent_affine_traction": affine_traction_interpretation(panel, points, area, delta, correction),
                         "affine_removed_slope_and_von_karman_markers": warp_slope_markers(panel, panel["q"])})
    pins.update(state["source_sha256"])
    pins[str(field.resolve().relative_to(method.ROOT))] = method.sha(field)
    pins[str(Path(__file__).resolve().relative_to(method.ROOT))] = method.sha(Path(__file__))
    potential = state["response"]["potential_energy_nmm"]
    result = {"schema": "thin_bolted_saved_panel_load_correction_diagnostics/v1",
              "candidate": state["candidate"], "revision": state["revision"], "state_id": state["state_id"],
              "case_id": state["case_id"], "accessory_placement": state["accessory_placement"],
              "source_sha256": pins, "parameters": state["parameters"],
              "independent_finished_support_and_equilibrium_checks_pass": True,
              "common_wrench_reference_xyz_mm": REFERENCE.tolist(),
              "all_body_metal_mass_share_count": sum(row["id"].startswith("bolt-weight/") for row in state["body_applied_loads"]),
              "six_panel_diagnostics": rows,
              "sum_panel_correction_work_on_saved_q_nmm": total_work,
              "saved_full_assembly_total_potential_energy_nmm": potential,
              "absolute_sum_correction_work_over_absolute_total_potential": abs(total_work) / abs(potential),
              "potential_change_if_corrections_removed_at_fixed_q_nmm": total_work,
              "method": {"CAD_rebuilt": False, "K_assembled": False, "response_solved": False,
                         "mass_only_quadrature_reconstructed_and_npz_compared": True,
                         "actual_q_and_all_actual_panel_metal_share_ports_used": True},
              "limits": ["Correction is a least Euclidean-norm coefficient load projection satisfying the exact six rigid-wrench constraints; it is not a manufacturer or measured force distribution.",
                         "A wrench-equivalent affine traction is constructed as a formal interpretation and explicitly differs from the producer coefficient RHS. It is not substituted or solved.",
                         "Work and potential ratios describe the saved state only, without a response sensitivity bound. Squared warp slopes are applicability markers, not nonlinear demands or new acceptance limits."],
              "release": coupled.RELEASE, "complete_panel_resistance_established": False}
    coupled.verify_pins(pins)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.field)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": method.sha(args.out),
                      "correction_work_nmm": result["sum_panel_correction_work_on_saved_q_nmm"],
                      "work_over_potential": result["absolute_sum_correction_work_over_absolute_total_potential"]}))


if __name__ == "__main__":
    main()
