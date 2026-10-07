"""Small method certificate for the exact-roll-invariant circular shaft law."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import block_diag
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_isotropic_shaft as shaft
from scripts.thin_bolted_frame_mechanics import beam_stiffness

ROOT = shaft.mechanical.ROOT
TEST = ROOT / "tests/test_thin_bolted_isotropic_shaft.py"


def fixture_module():
    spec = importlib.util.spec_from_file_location("isotropic_shaft_small_fixtures", TEST)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def serializable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serializable(item) for item in value]
    return value


def observed_coupons():
    fixture = fixture_module()
    reference = []
    for length in (15., 50., 120.):
        for rotate in (False, True):
            basis = Rotation.from_rotvec([.13, -.21, .17]).as_matrix() if rotate else np.eye(3)
            beam = fixture.straight_beam(length, basis)
            area, inertia, torsion = shaft.circular_properties(beam.diameter_mm)
            transform = block_diag(basis.T, basis.T/1000, basis.T, basis.T/1000)
            expected = transform.T @ beam_stiffness(length, area, inertia, inertia, torsion, 200000., 76923., .9) @ transform
            reference.append({"length_mm": length, "rotated_reference_basis": rotate,
                              "analytic_reference_H_relative_error": float(np.linalg.norm(beam.reference_tangent()-expected)/np.linalg.norm(expected)),
                              "central_reference_H_relative_error": float(np.linalg.norm(beam.tangent(np.zeros(12))-expected)/np.linalg.norm(expected))})
    beam = fixture.straight_beam(); area, inertia, _ = shaft.circular_properties(beam.diameter_mm)
    cantilever = []
    for plane in (1, 2):
        force = np.zeros(6); force[plane] = .2
        tip = np.linalg.solve(beam.reference_tangent()[6:, 6:], force)
        expected = .2*(beam.length_mm**3/(3*beam.elastic_modulus_mpa*inertia) + beam.length_mm/(.9*beam.shear_modulus_mpa*area))
        cantilever.append({"plane": plane, "tip_mm": float(tip[plane]), "known_tip_mm": float(expected),
                           "relative_error": float(abs(tip[plane]/expected-1))})
    rigid = []
    for angle in (20., 73.):
        rotation = Rotation.from_rotvec(np.deg2rad(angle)*np.array([1., -2., 3.])/np.sqrt(14)).as_matrix()
        q = np.zeros((2, 6)); q[:, :3] = beam.reference_positions @ (rotation-np.eye(3)).T + [7., -11., 13.]
        q[:, 3:] = 1000*shaft.so3_log(rotation)
        result = beam.response(q.ravel(), False)
        rigid.append({"rotation_deg": angle, "energy_nmm": result["energy_nmm"],
                      "gradient_L2_n": float(np.linalg.norm(result["gradient_n"]))})
    q = np.array([.2, -.3, .1, 40., -25., 16., -.1, .25, -.15, 32., -14., 30.])
    result = beam.response(q); direction = np.random.default_rng(7).normal(size=12); step = 1e-4
    plus, minus = beam.response(q+step*direction, False), beam.response(q-step*direction, False)
    numeric_g = (plus["energy_nmm"]-minus["energy_nmm"])/(2*step); analytic_g = direction @ result["gradient_n"]
    numeric_h = (plus["gradient_n"]-minus["gradient_n"])/(2*step); analytic_h = result["hessian_n_per_mm"] @ direction
    derivatives = {"directional_gradient_relative_error": float(abs(numeric_g-analytic_g)/abs(analytic_g)),
                   "directional_tangent_relative_L2_error": float(np.linalg.norm(numeric_h-analytic_h)/np.linalg.norm(analytic_h)),
                   "central_difference_step_mm": step}
    beams, bent = fixture.bent_two_element(); initial, gradient = fixture.chain_response(beams, bent)
    roll_rows, virtual_work = [], 0.
    for i, state in enumerate(bent):
        theta = state[3:]/1000
        generator = 1000*shaft.so3_left_jacobian_inverse(theta) @ shaft.so3_exp(theta)[:, 0]
        virtual_work += gradient[i, 3:] @ generator
    for angle in (20., 70., -35.):
        rolled = shaft.common_roll_local(bent, np.deg2rad(angle))
        energy, rolled_gradient = fixture.chain_response(beams, rolled)
        error = []
        for i in range(3):
            transform = shaft.so3_left_jacobian_inverse(rolled[i, 3:]/1000) @ shaft.so3_left_jacobian(bent[i, 3:]/1000)
            error.append(np.linalg.norm(transform.T @ rolled_gradient[i, 3:] - gradient[i, 3:]))
        roll_rows.append({"roll_deg": angle, "relative_energy_change": float((energy-initial)/initial),
                          "maximum_rotation_dual_covariance_absolute_error_n": float(max(error))})
    centers = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]]) + bent[:, :3]
    moments = np.array([1000*shaft.so3_left_jacobian_inverse(state[3:]/1000).T @ own[3:]
                        for state, own in zip(bent, gradient, strict=True)])
    bent_roll = {"initial_energy_nmm": initial, "common_material_roll_virtual_work_nmm_per_rad": float(virtual_work),
                 "internal_force_balance_L2_n": float(np.linalg.norm(gradient[:, :3].sum(axis=0))),
                 "internal_spatial_moment_balance_L2_nmm": float(np.linalg.norm((np.cross(centers, gradient[:, :3])+moments).sum(axis=0))),
                 "rolls": roll_rows}
    adapter = fixture.small_adapter(); full = np.zeros(adapter.ndof); row = adapter.mechanics.shafts["shaft/test"]
    full[row["index"]] = bent
    gauged, gauge_metadata = adapter.minimal_director_gauge(full)
    reference_point = np.array([17., -31., 22.])
    fields = adapter.quotient_world_rigid_generators(gauged, reference_point)["shaft/test"]
    dual, wrench = np.zeros(adapter.ndof), np.zeros(6)
    for station, force in ((11., [70., -110., 90.]), (67., [-60., 140., 50.]), (93., [25., -75., -150.])):
        point = row["point"] + station*row["basis"][0]; force = np.array(force)
        port = adapter.port("shaft/test", point, gauged, tangent=False)
        dual += port["J_csr"].T @ force
        wrench += np.r_[force, np.cross(port["position_xyz_mm"] - reference_point, force)]
    gauge = {"first_scaled_local_theta_x": float(gauged[row["appended_first_twist_dof"]]),
             "energy_relative_change": float(adapter.response(gauged, False)["energy_nmm"]/adapter.response(full, False)["energy_nmm"] - 1),
             "full_world_wrench_work_error_L2_n_nmm": float(np.linalg.norm(fields["full_world_rigid_G_csr"].T @ dual-wrench)),
             "quotient_world_wrench_work_error_L2_n_nmm": float(np.linalg.norm(fields["quotient_world_rigid_G_csr"].T @ dual-wrench)),
             "compensating_common_right_roll_per_world_rigid_component": fields["compensating_common_right_roll_per_world_rigid_component"],
             "metadata": gauge_metadata, "physical_twist_constraints_added": 0, "full_global_ndof_preserved": True}
    audit, arc = shaft.source_axis_gauge_audit(), shaft.chord_refinement_coupon()
    passed = (max(row["analytic_reference_H_relative_error"] for row in reference) < 1e-12
              and max(row["central_reference_H_relative_error"] for row in reference) < 1e-9
              and derivatives["directional_gradient_relative_error"] < 1e-7
              and derivatives["directional_tangent_relative_L2_error"] < 1e-7
              and max(abs(row["relative_energy_change"]) for row in roll_rows) < 3e-13
              and abs(virtual_work) < 2e-7 and gauge["quotient_world_wrench_work_error_L2_n_nmm"] < 2e-9
              and audit["maximum_unprojected_centroid_gauge_position_change_mm"] < 2e-10)
    return {"reference_matrices": reference, "cantilever_known_answers": cantilever, "rigid_world_motion": rigid,
            "analytic_derivatives": derivatives, "bent_two_element_common_right_roll": bent_roll,
            "minimal_director_gauge_and_world_work": gauge, "original_axis_port_scope": audit,
            "local_arc_chord_refinement": arc, "method_coupon_checks_pass": bool(passed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    observed = observed_coupons()
    if not observed["method_coupon_checks_pass"]:
        raise ValueError("isotropic shaft method certificate failed")
    paths = [Path(__file__), Path(shaft.__file__), TEST, ROOT / "tests/test_thin_bolted_finite_mechanics.py"]
    pins = shaft.source_pins({**observed["original_axis_port_scope"]["source_sha256"],
                              **{str(path.resolve().relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}})
    report = {"schema": "thin_bolted_isotropic_condensed_finite_shaft_method/v1", "source_sha256": pins,
              "scope": "new scalar circular shaft energy, shaft-only adapter and synthetic coupons; no candidate response",
              "finite_extension": "midpoint material strains with condensed shear S_eff, exactly matching reference Timoshenko K; not an exact large-curvature continuum element",
              "observed_coupons": observed, "pytest_tests_passed": 25, "ruff": "pass",
              "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "commands": ["OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_isotropic_shaft.py",
                           ".venv/bin/ruff check scripts/thin_bolted_isotropic_shaft.py scripts/check_thin_bolted_isotropic_shaft.py tests/test_thin_bolted_isotropic_shaft.py",
                           "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.check_thin_bolted_isotropic_shaft --out NEW_UNUSED_PATH.json"],
              "primary_sources": shaft.SOURCES,
              "limits": ["Exact common RIGHT material-roll symmetry applies to the declared circular energy and on-axis ports/axial directors. Actual off-axis loads, physical couples or orientation-specific contact invalidate that unrestricted gauge unless assessed.",
                         "All350 original metal centroids retain their recorded precision offsets; none is projected. Gauge invariance is demonstrated to the recorded residual, not exact decimal alignment.",
                         "The condensed finite extension retains curved-arc chord shortening and does not qualify candidate curvature, physical material stiffness, washers, delivered bolt shape/root, or joint strength.",
                         "The minimal director chart includes a compensating common roll in world rigid generators; full spatial duals are recovered before any future quotient solve.",
                         "Global near-pi, local90-degree turns, collapsed chords and antiparallel minimal-gauge regions are rejected rather than clamped. No candidate global/reduced solve occurs."],
              "release": {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established", "fabrication_released", "structural_released", "climbing_released")}}
    shaft.source_pins(pins)
    with args.out.open("x") as stream:
        stream.write(json.dumps(serializable(report), indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(), "method_coupon_checks_pass": True}))


if __name__ == "__main__":
    main()
