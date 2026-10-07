"""Freeze cheap finite-motion known-answer metrics without assembly/CAD/native runs."""

from __future__ import annotations

import inspect
import json
import platform

import numpy as np
import scipy

from scripts import hl35_candidate as shared
from scripts import thin_bolted_corotational_methods as method
from scripts import thin_bolted_frame_mechanics as linear

PACKET = shared.ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
OUTPUT = PACKET / "corotational-method-coupons-v1.json"


def main() -> None:
    length, area, iy, iz, j, elastic, shear = 800., 3000., 2e6, 3e6, 1e6, 11000., 700.
    basis = method.so3_exp([.13, -.2, .17])
    origin = np.array([32., -81., 47.])
    positions = np.array([origin, origin + length * basis[:, 0]])
    beam = method.CorotationalBeam.from_properties(positions, basis, area, iy, iz, j, elastic, shear)

    def rotated(q, rotation, translation):
        result = np.zeros((2, 6))
        for node, row in enumerate(np.asarray(q).reshape(2, 6)):
            result[node, :3] = rotation @ (positions[node] + row[:3]) + translation - positions[node]
            result[node, 3:] = 1000. * method.so3_log(rotation @ method.so3_exp(row[3:] / 1000.))
        return result.ravel()

    rigid = []
    axis = np.array([2., -3., 5.]) / np.sqrt(38.)
    for angle in [0., .12, np.deg2rad(20.), np.deg2rad(80.)]:
        q = rotated(np.zeros(12), method.so3_exp(axis * angle), np.array([123., -41., 35.]))
        response = beam.response(q, tangent=False)
        rigid.append({"angle_rad": angle, "energy_nmm": response["energy_nmm"],
                      "residual_norm_n_equivalent": float(np.linalg.norm(response["residual_work_conjugate_q"])),
                      "local_rotation_norm_rad": float(np.linalg.norm(response["local_rotations_rad"]))})
    transform = np.zeros((12, 12))
    for node in range(2):
        start = node * 6
        transform[start:start+3, start:start+3] = basis.T
        transform[start+3:start+6, start+3:start+6] = basis.T / 1000.
    expected = transform.T @ beam.local_stiffness @ transform
    tangent = beam.tangent(np.zeros(12))
    zero_error = np.linalg.norm(tangent - expected) / np.linalg.norm(expected)
    q = np.array([.2, -.4, .1, 11., -8., 6., .7, .9, -.3, -4., 7., 15.])
    rotation = method.so3_exp(np.array([2., -1., 3.]) / np.sqrt(14.) * np.deg2rad(20.))
    changed = rotated(q, rotation, np.array([29., -43., 13.]))
    objective_error = abs(beam.energy(changed) - beam.energy(q)) / beam.energy(q)
    finite_tangent = beam.tangent(q)
    half_step = beam.tangent(q, step_mm=.0005)
    tangent_asymmetry = np.linalg.norm(finite_tangent - finite_tangent.T) / np.linalg.norm(finite_tangent)
    tangent_step_error = np.linalg.norm(finite_tangent - half_step) / np.linalg.norm(finite_tangent)
    arm = np.array([0., 0., 100.])
    port_q = np.array([0., 0., 0., 120., 0., 0.])
    exact_position, port_jacobian = method.rigid_port(arm, np.zeros(3), port_q)
    old_linear_position = arm + np.cross(port_q[3:] / 1000., arm)
    delta = exact_position - old_linear_position
    port_h = .001
    numerical = np.column_stack([(method.rigid_port(arm, np.zeros(3), port_q + port_h * e)[0]
                                  - method.rigid_port(arm, np.zeros(3), port_q - port_h * e)[0]) / (2 * port_h)
                                 for e in np.eye(6)])
    report = {
        "schema": "thin-finite-motion-method-coupons-v1", "candidate": "standalone_method_only",
        "source_sha256": {name: shared.sha(shared.ROOT / name) for name in [
            "scripts/thin_bolted_corotational_methods.py", "scripts/thin_bolted_corotational_coupons.py",
            "scripts/thin_bolted_frame_mechanics.py", "tests/test_thin_bolted_corotational_methods.py", "uv.lock"]},
        "beam_stiffness_function_source": inspect.getsource(linear.beam_stiffness),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "coordinate_contract": "node world q=(u_mm,1000*theta_rad), node1 thennode2; basisCOLUMNS[g,u,v]=oldR.T",
        "inputs": {"length_mm": length, "area_mm2": area, "Iy_mm4": iy, "Iz_mm4": iz, "J_mm4": j,
                   "E_mpa": elastic, "G_mpa": shear, "basis_columns_world": basis.tolist(),
                   "positions_world_mm": positions.tolist(), "deformed_state_q": q.tolist()},
        "rigid_motion": rigid,
        "undeformed_tangent_relative_error_to_existing_linear_beam": float(zero_error),
        "deformed_twenty_degree_energy_relative_objectivity_error": float(objective_error),
        "finite_state_tangent_relative_asymmetry": float(tangent_asymmetry),
        "finite_state_tangent_relative_step_halving_error": float(tangent_step_error),
        "port_0p12rad_100mm_arm": {"exact_xyz_mm": exact_position.tolist(),
                                   "old_linear_xyz_mm": old_linear_position.tolist(),
                                   "exact_minus_linear_mm": delta.tolist(),
                                   "error_norm_mm": float(np.linalg.norm(delta)),
                                   "analytic_jacobian_max_difference_to_central_fd": float(np.max(np.abs(port_jacobian - numerical)))},
        "known_answer_test_command": ".venv/bin/python -m pytest tests/test_thin_bolted_corotational_methods.py -q",
        "known_answer_test_result": "18 passed; SO3 independent SciPy rotations, port Jacobian and spatial wrench work, 0/.12rad/20deg/80deg common rigid motion, deformed objectivity/force covariance, oldK tangent, axial/torsion/common twist, both Timoshenko cantilever planes, energy/residual/tangent derivatives, and branch rejection",
        "sources": method.SOURCES,
        "provenance_limit": "Primary research text was read through browser; original PDF bytes/SHA are not retained or claimed authenticated.",
        "limits": ["Small local elastic deformation Timoshenko surrogate; this is not a geometrically exact continuum beam or joint resistance.",
                   "Tangent is a central derivative of analytic residual, not an analytic Hessian; default step1e-3mm in q (rotation1e-6rad). No hidden symmetrization.",
                   "SO3 rotation-vector/log charts nearpi, collapsed chords, canceled/projected directors and local rotations at/beyond90deg are explicitly rejected.",
                   "Common twist is a free rigid mode. Numerical gauge fixing does not create physical common torque resistance; actual torsion couples remain distinct.",
                   "Reference-fixed versus rotating floor/flange normals, contact support/contact-gap laws, interpolation along flexible beams, continuation/assembly validation are not selected by this method.",
                   "No whole load case, assembly, native solve, CAD rebuild or current model change."],
        "reproduce": ".venv/bin/python -m scripts.thin_bolted_corotational_coupons",
    }
    if (max(r["energy_nmm"] for r in rigid) >= 1e-19
            or max(r["residual_norm_n_equivalent"] for r in rigid) >= 1e-8
            or zero_error >= 2e-7 or objective_error >= 1e-10
            or tangent_asymmetry >= 1e-8 or tangent_step_error >= 1e-7):
        raise ValueError("finite-motion known-answer metric exceeds acceptance tolerance")
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(OUTPUT), "rigid_motion": rigid,
                      "oldK_relative_error": float(zero_error), "objectivity_relative_error": float(objective_error),
                      "tangent_asymmetry": float(tangent_asymmetry), "tangent_step_halving_error": float(tangent_step_error),
                      "port_linear_error_at0p12rad_mm": float(np.linalg.norm(delta))}, indent=2))


if __name__ == "__main__":
    main()
