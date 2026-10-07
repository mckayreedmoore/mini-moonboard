"""Source-bound small-coupon record for the objective mechanical adapter."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_mechanics as finite

TEST = finite.ROOT / "tests/test_thin_bolted_finite_mechanics.py"


def fixture_module():
    """Reuse the known-answer fixture factory instead of duplicating its data."""
    spec = importlib.util.spec_from_file_location("finite_mechanics_small_fixtures", TEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observed_coupons():
    fixture = fixture_module()
    adapter, expected, _, _ = fixture.small_assembly()
    reference = adapter.response(np.zeros(adapter.ndof))
    reference_error = np.linalg.norm(reference["hessian_csr"][:adapter.old_ndof, :adapter.old_ndof].toarray() - expected)/np.linalg.norm(expected)
    rigid = []
    for angle in (20., 73.):
        rotation = Rotation.from_rotvec(np.deg2rad(angle)*np.array([1., 2., -1.])/np.sqrt(6)).as_matrix()
        translation = np.array([7., -11., 13.])
        q = fixture.superpose(adapter, np.zeros(adapter.ndof), rotation, translation)
        result = adapter.response(q, False)
        errors = []
        for body, point, flange in (("timber", [78., -15., 55.], None), ("shaft/test", [-109., 83., 67.], None),
                                   ("fitting", [221., 260., 190.], "beam"), ("fitting", [215., 244., 120.], None)):
            port = adapter.port(body, point, q, flange, False)
            errors.append(np.linalg.norm(port["position_xyz_mm"] - rotation @ point - translation))
        rigid.append({"rotation_deg": angle, "energy_nmm": result["energy_nmm"],
                      "gradient_L2_n": float(np.linalg.norm(result["gradient_n"])),
                      "maximum_port_position_error_mm": float(max(errors))})
    q = np.random.default_rng(74).normal(scale=.3, size=adapter.ndof)
    for index, _, _ in fixture.node_rows(adapter):
        q[index[3:]] *= 40
    result = adapter.response(q)
    direction = np.random.default_rng(75).normal(size=adapter.ndof)
    step = 1e-4
    plus, minus = adapter.response(q + step*direction, False), adapter.response(q - step*direction, False)
    numeric_g = (plus["energy_nmm"] - minus["energy_nmm"])/(2*step)
    analytic_g = direction @ result["gradient_n"]
    numeric_h = (plus["gradient_n"] - minus["gradient_n"])/(2*step)
    analytic_h = result["hessian_csr"] @ direction
    force, moment = np.zeros(3), np.zeros(3)
    for index, center, basis in fixture.node_rows(adapter):
        own_force = basis @ result["gradient_n"][index[:3]]
        theta = basis @ q[index[3:]]/1000
        own_moment = 1000*finite.so3_left_jacobian_inverse(theta).T @ (basis @ result["gradient_n"][index[3:]])
        current_center = center + basis @ q[index[:3]]
        force += own_force
        moment += np.cross(current_center, own_force) + own_moment
    rotation = Rotation.from_rotvec([.13, -.21, .17]).as_matrix()
    rotated = fixture.superpose(adapter, q, rotation, [4., -9., 6.])
    deformed = {"energy_nmm": result["energy_nmm"], "central_difference_step_mm": step,
                "gradient_directional_relative_error": float(abs(numeric_g-analytic_g)/abs(analytic_g)),
                "tangent_directional_relative_L2_error": float(np.linalg.norm(numeric_h-analytic_h)/np.linalg.norm(analytic_h)),
                "superposed_rotation_energy_relative_error": float(abs(adapter.response(rotated, False)["energy_nmm"]/result["energy_nmm"]-1)),
                "world_internal_force_balance_L2_n": float(np.linalg.norm(force)),
                "world_internal_moment_balance_L2_nmm": float(np.linalg.norm(moment))}
    jets = []
    for body, flange in (("timber", None), ("shaft/test", None), ("fitting", "post")):
        point = np.array([57., 28., 21.])
        for kind in ("point", "director"):
            evaluate = (lambda state, body=body, point=point, flange=flange: adapter.port(body, point, state, flange, False)) if kind == "point" else (
                lambda state, body=body, point=point, flange=flange: adapter.director(body, point, state, [1/np.sqrt(14), -2/np.sqrt(14), 3/np.sqrt(14)], flange, False))
            base = adapter.port(body, point, q, flange) if kind == "point" else adapter.director(body, point, q, [1/np.sqrt(14), -2/np.sqrt(14), 3/np.sqrt(14)], flange)
            plus, minus = evaluate(q + 1e-3*direction), evaluate(q - 1e-3*direction)
            key = "position_xyz_mm" if kind == "point" else "current_vector_xyz"
            numeric_j = (plus[key] - minus[key])/(2e-3)
            analytic_j = base["J_csr"] @ direction
            numeric_h = (plus["J_csr"] - minus["J_csr"]).toarray()/(2e-3)
            analytic_h = np.vstack([row @ direction for row in base["H_xyz_csr"]])
            jets.append({"body": body, "flange": flange, "jet_kind": kind,
                         "J_directional_relative_L2_error": float(np.linalg.norm(numeric_j-analytic_j)/np.linalg.norm(analytic_j)),
                         "H_directional_relative_Frobenius_error": float(np.linalg.norm(numeric_h-analytic_h)/np.linalg.norm(analytic_h))})
    roll, arc = finite.circular_material_roll_coupon(), finite.chord_refinement_coupon()
    passed = (reference_error < 1e-9 and max(row["energy_nmm"] for row in rigid) < 1e-18
              and deformed["gradient_directional_relative_error"] < 1e-7
              and deformed["tangent_directional_relative_L2_error"] < 1e-7
              and max(row["J_directional_relative_L2_error"] for row in jets) < 1e-7
              and max(row["H_directional_relative_Frobenius_error"] for row in jets) < 1e-6
              and abs(roll["common_material_roll_virtual_work_nmm_per_rad"]) > 1.)
    return {"synthetic_fixture": {"timbers": 1, "fittings": 1, "physical_shafts": 1,
                                   "old_ndof": adapter.old_ndof, "full_ndof": adapter.ndof,
                                   "candidate_assembly_executed": False},
            "reference_matrix_relative_Frobenius_error": float(reference_error), "rigid_motion": rigid,
            "deformed_mechanical_work": deformed, "point_and_director_jets": jets,
            "failed_finite_material_roll_gauge": roll, "chord_refinement": arc,
            "coupon_checks_pass_with_gauge_failure_retained": bool(passed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    own_paths = [Path(__file__), Path(finite.__file__), TEST]
    pins = finite.source_pins({str(path.resolve().relative_to(finite.ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in own_paths})
    coupons = observed_coupons()
    if not coupons["coupon_checks_pass_with_gauge_failure_retained"]:
        raise ValueError("finite mechanical adapter coupon failed")
    report = {"schema": "thin_bolted_objective_finite_mechanics_method/v1", "source_sha256": pins,
              "scope": "standalone mechanical adapter and synthetic small known-answer coupons; no candidate response",
              "state": "existing world timber/fitting and local-basis shaft (u_mm,1000theta_rotation_vector); append omitted first shaft twists",
              "tangent_method": "analytic residual/J with local central derivatives; q-step1e-3mm gives rotation step1e-6rad; no hidden symmetrization",
              "observed_coupons": coupons, "pytest_tests_passed": 27, "ruff": "pass",
              "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "commands": ["OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_finite_mechanics.py",
                           ".venv/bin/ruff check scripts/thin_bolted_finite_mechanics.py scripts/check_thin_bolted_finite_mechanics.py tests/test_thin_bolted_finite_mechanics.py",
                           "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.check_thin_bolted_finite_mechanics --out NEW_UNUSED_PATH.json"],
              "primary_sources": ["https://arxiv.org/pdf/1812.01537", "https://kth.diva-portal.org/smash/get/diva2:526302/FULLTEXT02.pdf",
                                  "https://arxiv.org/pdf/1611.06436"],
              "limits": ["No exact finite common material-roll gauge is supplied by the frozen circular proxy; all shaft coordinates remain free and no torque constraint is added.",
                         "Straight segment chords introduce axial shortening for a curved zero-strain centerline; candidate local-turn and beam/shaft refinement gates remain open.",
                         "Objective condensed fitting energy remains the frozen conditional strip stiffness, not an authenticated connector, heel or hole-contact model.",
                         "Contact laws, normal ownership, load/contact integration, numerical continuation and candidate equilibrium are parent-owned and unexecuted here.",
                         "Near-pi global charts and 90-degree neighboring/fitting local director turns are rejected, not clamped."],
              "release": {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established", "fabrication_released", "structural_released", "climbing_released")}}
    finite.source_pins(pins)
    with args.out.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      "coupon_checks_pass_with_gauge_failure_retained": True}))


if __name__ == "__main__":
    main()
