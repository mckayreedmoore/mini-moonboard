"""Cancellation-resistant synthetic and current-pose finite fitting checks.

The synthetic coupon reads no field; current probes use authenticated saved
poses only. Neither assembles a frame, changes stiffness or grants capacity.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import scipy
from scipy.spatial.transform import Rotation

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_washer_lands as intake_source
from scripts import thin_bolted_finite_mechanics as finite
from scripts.thin_bolted_corotational_methods import ROTATION_SCALE, so3_exp

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
METHOD = {
    "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/centroidal-four-port-v1/centroidal.py",
    "sha256": "7f2d94f13732446a38693b69e9151ef72e9646c4a7aa7379247c328b973e80b9",
}
INTAKE = {"path": "scripts/eoere_current_washer_lands.py",
          "sha256": "d759bcab2d92bcb709f24726c324d83426483e2fd650dff80775ec0aa17b74d9"}
PREFLIGHT = {
    "path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/finite-preflight-v4.json",
    "sha256": "c6c57f23c237c7adbb1b19d537ea63c11d2ecf21cd297a7a9d7551067972c5a3",
}
PUBLICATION_MANIFEST = {
    "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/inputs.json",
    "sha256": "ac1e055a1d852b39bc84be2bc9c93e30675a2efcc95c9d9472b7b50e7deb1919",
}
OUTPUT_BRIDGE = {
    "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-force-bridge-v1/review-fix-v2/bridge.py",
    "sha256": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded finite fitting producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def publication_sources():
    """Bind the documented CLI's actual manifest and loaded output writer."""
    current.require(current.ref(current.MANIFEST) == PUBLICATION_MANIFEST
                    and current.manifest()["references"]["bridge"] == OUTPUT_BRIDGE,
                    "exact fitting publication manifest/bridge selection required")
    bridge = current.load("bridge")
    current.require(current.ref(bridge.OWN) == OUTPUT_BRIDGE and bridge.LOADED_SHA == OUTPUT_BRIDGE["sha256"],
                    "exact loaded fitting publication bridge required")
    return [PUBLICATION_MANIFEST, OUTPUT_BRIDGE]


def execution_pins():
    current.require(current.ref(intake_source.OWN) == INTAKE and intake_source.LOADED_SHA == INTAKE["sha256"],
                    "exact loaded fitting intake execution source required")
    refs = [component.own_ref(), component.canonical_dependency(), current.ref(current.OWN), INTAKE,
            *publication_sources()]
    return {r["path"]: r["sha256"] for r in refs}


def matrix_sha(matrix):
    return hashlib.sha256(np.ascontiguousarray(matrix, dtype="<f8").tobytes()).hexdigest()


def rotation_increment(theta, arm):
    """(Exp(theta)-I) arm, without subtracting nearly equal coordinates.

    Rodrigues gives sinc(t)*theta×arm + .5*sinc(t/2)^2*theta×(theta×arm).
    numpy.sinc uses pi-normalized arguments; both scalar limits are explicit.
    """
    theta, arm = finite.vector(theta, 3), finite.vector(arm, 3)
    angle = np.linalg.norm(theta)
    cross = np.cross(theta, arm)
    return np.sinc(angle/np.pi)*cross+.5*np.sinc(angle/(2*np.pi))**2*np.cross(theta, cross)


class StableRelative(finite.ObjectiveCondensedFitting):
    """Same relative pose and analytic Jacobian, stable translation evaluation."""

    def deformation(self, q):
        deformation, jacobian = super().deformation(q)
        state = finite.vector(q, 12).reshape(2, 6)
        theta = state[0, 3:]/ROTATION_SCALE
        chord = self.reference_positions[1]-self.reference_positions[0]
        deformation[6:9] = so3_exp(theta).T @ (state[1, :3]-state[0, :3])+rotation_increment(-theta, chord)
        return deformation, jacobian


def residual_refined_root(original_root, fun, seed, *, options, tolerance_n, step_mm):
    """Keep hybr, then refine its returned residual with the existing local J.

    SciPy's xtol bounds relative iterate change, not the force residual. The
    original potential and force gate remain; at most three improving Newton
    corrections share a hard callback budget with the original root call.
    """
    current.require(set(options) == {"xtol", "maxfev"} and options["xtol"] == 1e-10
                    and type(options["maxfev"]) is int and 0 < options["maxfev"] <= 500
                    and np.isfinite([tolerance_n, step_mm]).all()
                    and 0 < tolerance_n <= 1e-7 and step_mm > 0,
                    "original local root options, force gate and derivative step required")
    calls = 0

    def counted(state):
        nonlocal calls
        current.require(calls < options["maxfev"], "local heel callback budget exhausted; no fallback")
        calls += 1
        return finite.vector(fun(state), 6)

    solved = copy.deepcopy(original_root(counted, seed, options=options))
    initial_calls = calls
    state, residual = finite.vector(solved.x, 6), finite.vector(solved.fun, 6)
    trace = {"initial_scipy_reported_success": bool(solved.success),
        "initial_scipy_message": str(solved.message), "initial_callback_count": calls,
        "initial_heel_residual_inf_n": float(np.max(abs(residual))),
        "max_improving_newton_corrections": 3, "corrections": [], "hard_callback_limit": options["maxfev"]}
    for _ in range(3):
        error = float(np.max(abs(residual)))
        if error <= tolerance_n or calls+13 > options["maxfev"]:
            break
        jacobian = finite.derivative_hessian(lambda h: counted(h)[None, :], state, step_mm)[0]
        step = np.linalg.solve(jacobian, -residual)
        trial = state+step
        if np.array_equal(state, trial):
            break
        trial_residual = counted(trial)
        changed = float(np.max(abs(trial_residual)))
        if changed >= error:
            break
        trace["corrections"].append({"before_residual_inf_n": error, "after_residual_inf_n": changed,
            "step_mm_1000rad": step.tolist(), "corrected_heel_q_mm_1000rad": trial.tolist()})
        state, residual = trial, trial_residual
    trace.update(total_callback_count=calls, refinement_callback_count=calls-initial_calls,
                 final_heel_residual_inf_n=float(np.max(abs(residual))))
    solved.x, solved.fun, solved.nfev = state, residual, calls
    return solved, trace


def stable_adapter(method, element, *, step_mm=1e-3, refine_heel=False):
    """Extend the genuine frozen operator; keep its source/branch/local gates."""
    own_ref()
    current.require(type(element) is method.GuardedFourPortAssemblyElement,
                    "genuine centroidal four-port element required")

    class StableFourPort(method.objective.ObjectiveFourPort):
        def __init__(self):
            super().__init__(element, step_mm=step_mm)
            self.precision_pins = current.join(method.source_pins(), execution_pins(), {
                str(OWN.relative_to(current.ROOT)): LOADED_SHA,
                "uv.lock": current.sha(current.ROOT/"uv.lock")})
            self.strips = [(row, StableRelative(relative.reference_positions,
                            relative.condensed_stiffness, relative.tangent_step_mm))
                           for row, relative in self.strips]
            self._relative_snapshot = self._relative_fingerprint()

        def _check(self):
            super()._check()
            current.verify(self.precision_pins)

        def _beam_state(self, full, row):
            q, jacobian, root, tip = super()._beam_state(full, row)
            i = row["port_index"]
            state = full[6+6*i:12+6*i]
            q[:3] = full[:3]+rotation_increment(full[3:6]/ROTATION_SCALE, row["root"]-self.model.origin)
            q[6:9] = state[:3]+rotation_increment(state[3:]/ROTATION_SCALE, row["center"]-row["point"])
            return q, jacobian, root, tip

        def condensed_response(self, *args, **kwargs):
            if not refine_heel:
                return super().condensed_response(*args, **kwargs)
            original = method.objective.root
            traces = []

            def refined(fun, seed, *, options):
                solved, trace = residual_refined_root(original, fun, seed, options=options,
                    tolerance_n=kwargs.get("heel_tolerance_n", 1e-8), step_mm=self.step)
                traces.append(trace)
                return solved

            # Explicit serialized extension at the frozen method's root seam.
            # The frozen condensation, final residual/positive-heel gates and
            # source-byte checks still execute; restore the callback on failure.
            with patch.object(method.objective, "root", refined):
                result = super().condensed_response(*args, **kwargs)
            current.require(len(traces) == 1 and method.objective.root is original,
                            "one local root and restored source callback required")
            result["residual_refinement"] = traces[0]
            return result

    return StableFourPort()


def coupon():
    """Same historical failed synthetic load, unchanged 1e-8-N heel gate."""
    own_ref()
    method = component.load(METHOD, "eoere_precision_centroidal_source")
    pins = current.join(method.source_pins(), execution_pins(), {
        str(OWN.relative_to(current.ROOT)): LOADED_SHA,
        "uv.lock": current.sha(current.ROOT/"uv.lock")})
    current.verify(pins)
    rotation = Rotation.from_rotvec([.31, -.27, .19]).as_matrix()
    origin = np.array([101., -203., 307.])
    u, v = rotation[:, 0], rotation[:, 2]
    model, _ = method.model_from_reference_pose(origin, u, v, np.cross(u, v))
    element = method.GuardedFourPortAssemblyElement(model, "synthetic-precision-fitting", np.arange(3, 27), 31)
    load = {"id": "synthetic-gravity-once", "body": element.body_id,
            "point_xyz_mm": (origin+rotation @ [18., 3., 21.]).tolist(),
            "force_xyz_n": (rotation @ [0., 0., -.5]).tolist()}
    adapter = stable_adapter(method, element)
    result = adapter.condensed_response(np.zeros(24), heel_seed=np.zeros(6), loads=[load],
                                       tangent=True, recover_actions=True, heel_tolerance_n=1e-8,
                                       max_local_evaluations=100)
    heel_residual = float(result["heel_residual_inf_n"])
    current.require(np.isfinite(heel_residual) and 0 <= heel_residual <= 1e-8,
                    "synthetic fitting heel residual exceeds unchanged gate")
    closure = float(np.max(abs(np.asarray(result["external_body_resultant_about_current_heel_n_nmm"]))))
    current.require(closure < 1e-5, "synthetic fitting body wrench closure failed")
    zero = adapter.condensed_response(np.zeros(24), heel_seed=np.zeros(6), loads=[], tangent=True)
    reference = element.elastic_block()[1]
    tangent_error = float(np.linalg.norm(zero["hessian_n_per_mm"]-reference)/np.linalg.norm(reference))
    current.require(tangent_error < 1e-9, "unchanged reference tangent failed")
    current.verify(pins)
    return {"schema": "eoere_finite_fitting_stable_arithmetic_coupon/v1", "producer": current.ref(OWN),
            "source_sha256": pins, "all_sources_unchanged": True,
            "arithmetic": "Stable Rodrigues increments and relative translations; same potential, analytic Jacobian, finite-difference Hessian, stiffness, local solver and gate.",
            "synthetic_load": load, "reference_origin_xyz_mm": origin.tolist(),
            "reference_basis_rotation_vector_rad": [.31, -.27, .19],
            "heel_gate_n": 1e-8, "heel_residual_inf_n": heel_residual,
            "local_function_evaluations": result["local_function_evaluations"],
            "local_solver_reported_success": result["local_solver_reported_success"],
            "heel_hessian_min_symmetric_eigenvalue_n_mm": result["heel_hessian_min_symmetric_eigenvalue_n_mm"],
            "external_body_wrench_closure_inf_n_nmm": closure,
            "reference_schur_relative_error": tangent_error,
            "environment": {"numpy": np.__version__, "scipy": scipy.__version__},
            "candidate_field_assembly_or_native_solver_run": False,
            "physical_fitting_stiffness_resistance_or_candidate_acceptance": False}


def prepare_current_fitting(method, pose, descriptor, *, full_ndof):
    """Rebuild one genuine fitting; preserve its exact source matrix and ports."""
    current.require(full_ndof == 9450 and pose["id"] == descriptor["body"],
                    "current own fitting and complete finite chart required")
    model, _ = method.model_from_reference_pose(pose["origin_xyz_mm"], pose["u_xyz"],
                                               pose["v_xyz"], pose["w_xyz"])
    element = method.GuardedFourPortAssemblyElement(model, pose["id"],
        np.asarray(descriptor["dof_indices"]), full_ndof)
    fresh = element.descriptor()
    keys = ["ports", "all_factory_holes", "own_fitting_scenario", "dof_indices", "centroidal_correction"]
    current.require(all(fresh[k] == descriptor[k] for k in keys)
                    and matrix_sha(element.elastic_block()[1]) == descriptor["elastic_block_little_endian_float64_sha256"],
                    "current fitting reference stiffness/geometry differs from saved operator")
    return stable_adapter(method, element, refine_heel=True)


def fitting_work_check(adapter, q24, result, loads):
    """Independent spatial work and body-wrench check at the same finite pose."""
    q24 = finite.vector(q24, 24).reshape(4, 6)
    heel = finite.vector(result["internal_heel_q_mm_1000rad"], 6)
    origin = np.asarray(adapter.model.origin)
    heel_point = origin+heel[:3]
    ports = result["port_actions"]
    manifest = adapter.model.port_manifest
    current.require(len(ports) == len(manifest) == 4
                    and [p["port_id"] for p in ports] == [p["id"] for p in manifest],
                    "all four own current fitting port actions required")
    generators, wrench = np.zeros((24, 6)), np.zeros(6)
    for i, (port, source) in enumerate(zip(ports, manifest, strict=True)):
        point = finite.vector(source["point_reference_xyz_mm"], 3)+q24[i, :3]
        current.require(port["body"] == adapter.body and np.linalg.norm(point-port["point_xyz_mm"]) < 1e-10,
                        "same own finite fitting port pose required")
        generators[6*i:6*i+3, :3] = np.eye(3)
        generators[6*i:6*i+3, 3:] = -finite.skew(point-heel_point)
        generators[6*i+3:6*i+6, 3:] = 1000.*finite.so3_left_jacobian_inverse(q24[i, 3:]/1000.)
        force = finite.vector(port["external_force_required_at_port_xyz_n"], 3)
        couple = finite.vector(port["external_couple_required_at_port_xyz_nmm"], 3)
        wrench += np.r_[force, couple+np.cross(point-heel_point, force)]
    work_error = generators.T @ finite.vector(result["gradient_n"], 24)-wrench
    current_loads = result["current_load_actions"]
    current.require(len(current_loads) == len(loads) == 1 and current_loads[0]["id"] == loads[0]["id"]
                    and current_loads[0]["body"] == loads[0]["body"] == adapter.body,
                    "one own fitting gravity load, applied exactly once, required")
    rotation = Rotation.from_rotvec(heel[3:]/1000.).as_matrix()
    load = loads[0]
    load_point = heel_point+rotation @ (np.asarray(load["point_xyz_mm"])-origin)
    force = finite.vector(load["force_xyz_n"], 3)
    current.require(np.linalg.norm(load_point-current_loads[0]["point_xyz_mm"]) < 1e-10
                    and np.array_equal(force, current_loads[0]["force_xyz_n"]),
                    "own gravity point/force changed or loaded through wrong pose")
    closure = wrench+np.r_[force, np.cross(load_point-heel_point, force)]
    reported = finite.vector(result["external_body_resultant_about_current_heel_n_nmm"], 6)
    current.require(np.max(abs(work_error)) < 1e-5 and np.max(abs(closure-reported)) < 1e-5
                    and np.max(abs(closure)) < 1e-5,
                    "finite fitting physical work or body wrench failed unchanged 1e-5 gate")
    return {"external_spatial_work_error_n_nmm": work_error.tolist(),
            "independent_body_wrench_residual_n_nmm": closure.tolist(),
            "same_pose_loaded_gravity_point_xyz_mm": load_point.tolist()}


def probe_current_fitting(adapter, descriptor, old_q, linear_action, loads):
    """Local stationarity at saved port poses; not a candidate equilibrium."""
    current.require(linear_action["body"] == adapter.body and len(loads) == 1
                    and loads[0]["body"] == adapter.body, "own current fitting state and gravity required")
    q24 = np.asarray(old_q)[np.asarray(descriptor["dof_indices"])]
    seed = finite.vector(linear_action["loaded_heel_q_mm_rad"], 6).copy()
    seed[3:] *= 1000.
    record = {"body": adapter.body, "source_dof_indices": descriptor["dof_indices"],
        "source_reference_K_sha256": descriptor["elastic_block_little_endian_float64_sha256"],
        "diagnostic_port_q_mm_1000rad": q24.tolist(),
        "initial_heel_seed_mm_1000rad_from_own_linear_field": seed.tolist(), "own_gravity_loads": loads,
        "heel_tolerance_n": 1e-8, "max_local_evaluations_option": 100}
    try:
        result = adapter.condensed_response(q24, heel_seed=seed, loads=loads, tangent=True,
            recover_actions=True, heel_tolerance_n=1e-8, max_local_evaluations=100)
        residual = float(result["heel_residual_inf_n"])
        minimum = float(result["heel_hessian_min_symmetric_eigenvalue_n_mm"])
        current.require(np.isfinite([residual, minimum]).all() and 0 <= residual <= 1e-8 and minimum > 1e-8,
                        "current fitting heel result violates original stationarity/positive-branch gates")
        hessian = np.asarray(result["hessian_n_per_mm"])
        current.require(hessian.shape == (24, 24) and np.isfinite(hessian).all(),
                        "finite complete current condensed tangent required")
        work = fitting_work_check(adapter, q24, result, loads)
    except ValueError as error:
        return {**record, "finite_local_fitting_probe_pass": False, "error_type": type(error).__name__,
                "error": str(error), "accepted_local_actions": None, "candidate_equilibrium_admitted": False}
    return {**record, **work, "finite_local_fitting_probe_pass": True,
        "internal_heel_q_mm_1000rad": result["internal_heel_q_mm_1000rad"],
        "heel_residual_inf_n": residual, "heel_hessian_min_symmetric_eigenvalue_n_mm": minimum,
        "local_function_evaluations": result["local_function_evaluations"],
        "local_solver_reported_success": result["local_solver_reported_success"],
        "residual_refinement": result["residual_refinement"],
        "elastic_energy_nmm": result["elastic_energy_nmm"],
        "condensed_gradient_n": result["gradient_n"].tolist(),
        "condensed_hessian_little_endian_float64_sha256": matrix_sha(result["hessian_n_per_mm"]),
        "unsymmetrized_full_hessian_asymmetry_inf_n_mm": result["unsymmetrized_full_hessian_asymmetry_inf_n_mm"],
        "port_actions": result["port_actions"], "strip_root_actions": result["strip_root_actions"],
        "candidate_equilibrium_admitted": False, "actual_product_or_complete_joint_qualified": False}


def current_fitting_checks():
    own_ref()
    current.require(current.ref(intake_source.OWN) == INTAKE and intake_source.LOADED_SHA == INTAKE["sha256"],
                    "exact loaded current intake helper required")
    cases, pins = intake_source.intake()
    preflight = current.read(PREFLIGHT)
    method = component.load(METHOD, "current_precision_centroidal_source")
    pins = current.join(pins, preflight["source_sha256"], method.source_pins(), execution_pins(),
        {r["path"]: r["sha256"] for r in [own_ref(), INTAKE, PREFLIGHT, current.ref(current.ROOT/"uv.lock")]})
    current.verify(pins)
    current.require(preflight["schema"] == "eoere_current_finite_ownership_and_shaft_gauge/v1"
                    and preflight["case_sequence"] == component.SEQUENCE
                    and preflight["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and preflight["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and preflight["extra_grid"] is False and preflight["all_sources_unchanged"] is True,
                    "exact current finite preflight required")
    result_cases = []
    for (binding, field, _), parent in zip(cases, preflight["cases"], strict=True):
        bundle_ref = field["operator_bundle"]["manifest"]
        current.require(binding["case_id"] == parent["case_id"] and binding["state_id"] == parent["state_id"]
                        and binding["field"] == parent["field"] and bundle_ref == parent["operator_manifest"],
                        "own current preflight/field/operator join required")
        bundle = current.read(bundle_ref)
        full_ndof = parent["coordinate_ownership"]["prospective_full_ndof"]
        descriptors = bundle["coordinate_map"]["four_port_fittings"]
        poses = {p["id"]: p for p in field["source_inputs"]["fitting_poses"]}
        actions = {a["body"]: a for a in field["four_port_fitting_actions"]}
        current.require(len(poses) == len(actions) == len(descriptors) == 22
                        and set(poses) == set(actions) == set(descriptors), "all 22 own current fittings required")
        rows = []
        for body, descriptor in descriptors.items():
            adapter = prepare_current_fitting(method, poses[body], descriptor, full_ndof=full_ndof)
            loads = [load for load in bundle["case"]["loads"] if load["body"] == body]
            rows.append(probe_current_fitting(adapter, descriptor, field["response"]["q"], actions[body], loads))
        result_cases.append({"case_id": binding["case_id"], "state_id": binding["state_id"],
            "field": binding["field"], "operator_manifest": bundle_ref, "fittings": rows})
    current.verify(pins)
    return {"schema": "eoere_current_pose_finite_loaded_fitting_probes/v1", "producer": own_ref(),
        "source_sha256": pins, "all_sources_unchanged": True, "current_preflight": PREFLIGHT,
        "case_sequence": component.SEQUENCE, "cases": result_cases,
        "all132_local_fitting_probes_pass": all(r["finite_local_fitting_probe_pass"] for c in result_cases for r in c["fittings"]),
        "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
        "extra_grid": False, "environment": {"numpy": np.__version__, "scipy": scipy.__version__},
        "execution": {"actual_sys_argv": sys.argv, "actual_sys_orig_argv": sys.orig_argv},
        "full_frame_potential_equilibrium_native_solve_or_remedy_performed": False,
        "physical_stiffness_bounds_complete_joint_resistance_or_structural_acceptance": False,
        "local_root_extension": "Original hybr/xtol and same finite potential; at most three improving Newton corrections with the frozen derivative step, unchanged residual gate and hard total callback cap.",
        "release": current.manifest()["release"],
        "limits": ["Saved first-order port poses and loaded heel values are only diagnostic poses and local initial seeds, not finite frame solutions.",
                   "Original gross four-strip/rigid-heel analogy and source matrices retained; actual formed thickness, net holes and heel stiffness remain unqualified.",
                   "Local positive heel branch and residual are checked; global heel uniqueness or a physical response bound is not established.",
                   "The current extension counts all local callbacks against maxfev; parent must also impose a whole-process wall limit. No failed probe is replaced with zero or accepted actions."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--current-fittings", action="store_true", help="probe all current fitting poses instead of the synthetic coupon")
    args = parser.parse_args()
    publication_sources()
    with current.load("bridge").reserve(args.out) as output:
        output.write(current_fitting_checks() if args.current_fittings else coupon())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
