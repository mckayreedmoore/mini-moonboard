"""Implicit reference-solid bedding proof on synthetic affine/geodesic maps.

No candidate state, closed-body query, K or production response is consumed.
Reference signed distance is not current Euclidean distance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from typing import ClassVar

import numpy as np
import scipy
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
TEST = OWN.with_name("test_coupon.py")
REUSE = "fea/generated/thin-bolted-current-contact-v1/moving-domain-v1/coupon.py"
EXPECTED = "317d78b28d6a30d407f9311d212f01b049e7b07149a07a9555d071c9b85178d1"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LOADED_TEST_SHA = hashlib.sha256(TEST.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


require(sha(ROOT / REUSE) == EXPECTED, "frozen inverse coupon dependency differs")
SPEC = importlib.util.spec_from_file_location("implicit_reference_reuse", ROOT / REUSE)
previous = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = previous
SPEC.loader.exec_module(previous)
closest = previous.closest


def source_pins():
    pins = {**previous.source_pins(), REUSE: EXPECTED,
            str(OWN.relative_to(ROOT)): LOADED_SHA,
            str(TEST.relative_to(ROOT)): LOADED_TEST_SHA}
    for name, expected in pins.items():
        require(sha(ROOT / name) == expected, "implicit reference-solid source changed: " + name)
    return pins


def point_arrays(field):
    return field["value_xyz"], field["J_csr"].toarray(), np.asarray([h.toarray() for h in field["H_xyz_csr"]])


class AffineMaster:
    """Homogeneous deforming body: R*((1+q12/1000)*I+q13/1000*ez⊗ex)*X+t."""

    ndof = 14
    slave_indices = np.arange(6, 12)
    reference_center = np.zeros(3)

    def jet(self, q, point, *, tangent=True):
        q, point = np.asarray(q), np.asarray(point)
        require(q.shape == (14,) and point.shape == (3,), "affine coupon chart differs")

        def value_j(state):
            rotation = closest.so3_exp(state[3:6]/1000.)
            stretch, shear = 1.+state[12]/1000., state[13]/1000.
            require(stretch > .5 and abs(shear) < 1., "positive bounded affine coupon map required")
            a = stretch*np.eye(3)+shear*np.outer([0., 0., 1.], [1., 0., 0.])
            arm = rotation @ a @ point
            j = np.zeros((3, 14))
            j[:, :3] = np.eye(3)
            j[:, 3:6] = -closest.skew(arm) @ closest.so3_left_jacobian(state[3:6]/1000.)/1000.
            j[:, 12] = rotation @ point/1000.
            j[:, 13] = rotation @ np.array([0., 0., point[0]])/1000.
            return state[:3]+arm, j, rotation, a

        value, j, rotation, a = value_j(q)
        h = closest.mechanics.derivative_hessian(lambda state: value_j(state)[1], q) if tangent else np.zeros((3, 14, 14))
        f = rotation @ a
        f_q = np.zeros((3, 3, 14))
        for k, axis in enumerate((closest.so3_left_jacobian(q[3:6]/1000.)/1000.).T):
            f_q[:, :, k+3] = closest.skew(axis) @ f
        f_q[:, :, 12] = rotation/1000.
        f_q[:, :, 13] = rotation @ np.outer([0., 0., 1.], [1., 0., 0.])/1000.
        return {"field": closest.point_field(value, j, h, np.arange(14), 14),
                "F": f, "F_q": f_q, "phi_XX": np.zeros((3, 3, 3)),
                "branch": "homogeneous-affine", "inverse_local_only": False}


class GeodesicMaster:
    """Reuse genuine frozen timber point/UV-curvature/mixed-q jets."""

    ndof = 18
    slave_indices = np.arange(12, 18)
    reference_center = np.array([50., 0., 0.])
    row: ClassVar[dict] = {"kind": "timber", "reference_stations_mm": [0., 100.],
           "node_reference_centers_xyz_mm": [[0., 0., 0.], [100., 0., 0.]],
           "node_dof_indices": np.arange(12).reshape(2, 6).tolist(),
           "storage_basis_columns_xyz": np.eye(3).tolist(),
           "reference_axis_xyz": [1., 0., 0.], "reference_start_xyz_mm": [0., 0., 0.]}

    def jet(self, q, point, *, tangent=True):
        q, point = np.asarray(q), np.asarray(point)
        require(q.shape == (18,) and 1. < point[0] < 99., "one smooth interior timber segment required")
        state = closest.geometry.surface_state(self.row, q, point, [0., 0., 1.])
        f = state["reference_coordinate_jacobian"]
        patches = [closest.FiniteTimberPlane(self.row, point, n,
                    lambda x: {"eligible_for_smooth_own_face_projection": True, "location": "synthetic interior"})
                   for n in np.eye(3)]
        first = patches[0](q, np.zeros(2), tangent=tangent)
        if not tangent:
            return {"field": first["point_field"], "F": f, "branch": "one-geodesic-timber-segment",
                    "inverse_local_only": True}
        f_q, phi_xx = np.zeros((3, 3, 18)), np.zeros((3, 3, 3))
        for i, patch in enumerate(patches):
            surface = first if i == 0 else patch(q, np.zeros(2), tangent=False)
            directions = patch.directions
            for direction, mixed in zip(directions.T, surface["tangent_J_csr"], strict=True):
                f_q += np.einsum("ai,b->abi", mixed.toarray(), direction)/2.
            phi_xx += np.einsum("bu,auv,cv->abc", directions, surface["curvature_uv_xyz"], directions)
        for i in range(3):
            phi_xx[:, i, i] /= 2.
        return {"field": first["point_field"], "F": f, "F_q": f_q, "phi_XX": phi_xx,
                "branch": "one-geodesic-timber-segment", "inverse_local_only": True}


class MaterialPlane:
    """Smooth reference top plane, mapped by the SAME master callback."""

    def __init__(self, master, origin):
        self.master, self.origin = master, np.asarray(origin)
        self.directions = closest.geometry.plane_basis(np.array([0., 0., 1.]))

    def __call__(self, q, uv, *, tangent=True):
        point = self.origin+self.directions @ np.asarray(uv)
        jet = self.master.jet(q, point, tangent=True)
        return {"point_field": jet["field"], "tangent_xyz": jet["F"] @ self.directions,
                "curvature_uv_xyz": np.einsum("abc,bu,cv->auv", jet["phi_XX"], self.directions, self.directions),
                "tangent_J_csr": [csr_matrix(np.einsum("abi,b->ai", jet["F_q"], direction)) for direction in self.directions.T],
                "orientation_sign": 1., "reference_point_xyz_mm": point,
                "smooth_branch_key": jet["branch"], "eligible_for_smooth_projection": True,
                "domain_kind": "synthetic interior top plane"}


def inverse(master, q, target, seed, *, tolerance_mm=1e-11):
    point = np.asarray(seed, dtype=float).copy()
    for iteration in range(20):
        jet = master.jet(q, point, tangent=False)
        residual = jet["field"]["value_xyz"]-target
        f = jet["F"]
        require(np.linalg.det(f) > .1 and np.linalg.cond(f) < 100., "singular/folded local inverse unsupported")
        if np.max(abs(residual)) <= tolerance_mm:
            return point, iteration, float(np.max(abs(residual)))
        point -= np.linalg.solve(f, residual)
    raise ValueError("local inverse did not converge; no fallback force")


def response(master, q, slave_reference, seed):
    slave = closest.rigid_field(q, slave_reference, np.zeros(3), master.slave_indices)
    xs, js, hs = point_arrays(slave)
    point, iterations, residual = inverse(master, q, xs, seed)
    jet = master.jet(q, point)
    xm, jm, hm = point_arrays(jet["field"])
    f = jet["F"]
    sdf = previous.plate_distance(point-master.reference_center)
    rho = sdf["distance_mm"]
    require(rho < 0., "proof fixtures require a unique negative reference-distance branch")
    normal, curvature = sdf["normal"], sdf["hessian_per_mm"]
    x_q = np.linalg.solve(f, js-jm)
    mixed = np.einsum("abi,bj->aij", jet["F_q"], x_q)
    geometric = np.einsum("abc,bi,cj->aij", jet["phi_XX"], x_q, x_q)
    rhs = hs-hm-mixed-mixed.transpose(0, 2, 1)-geometric
    x_qq = np.linalg.solve(f, rhs.reshape(3, -1)).reshape(rhs.shape)
    rho_q = normal @ x_q
    rho_qq = x_q.T @ curvature @ x_q+np.einsum("a,aij->ij", normal, x_qq)
    covector = np.linalg.solve(f.T, normal)
    force = -rho*covector
    return {"energy_nmm": .5*rho*rho, "gradient_n": rho*rho_q,
            "hessian_n_mm": np.outer(rho_q, rho_q)+rho*rho_qq,
            "reference_point_xyz_mm": point, "reference_distance_mm": rho,
            "reference_normal_xyz": normal, "spatial_distance_gradient": covector,
            "spatial_distance_gradient_norm": float(np.linalg.norm(covector)),
            "F": f, "inverse_X_q": x_q, "inverse_X_qq": x_qq,
            "inverse_iterations": iterations, "inverse_residual_inf_mm": residual,
            "force_on_slave_xyz_n": force, "force_on_master_xyz_n": -force,
            "current_slave_point_xyz_mm": xs, "current_master_penalty_point_xyz_mm": xm,
            "slave_J": js, "master_J": jm, "master_kind": type(master).__name__,
            "local_inverse_only": jet["inverse_local_only"], "extra_director_couple_nmm": np.zeros(3)}


def fixture(kind):
    reference = np.array([.4, -.2, .3])
    if kind in ("uniform-stretch", "affine-shear"):
        master, q, truth = AffineMaster(), np.zeros(14), np.array([1.3, .2, -.25])
        if kind == "uniform-stretch":
            q[12] = 400.
        else:
            q[13] = 600.
    elif kind == "geodesic-bend":
        master = GeodesicMaster()
        q = np.array([2., -3., 1., 100., -40., 70., -1., 5., -2., 140., 60., 10.,
                      0., 0., 0., -60., 80., 90.])
        truth = np.array([51.3, .2, -.25])
    else:
        raise ValueError("known synthetic inverse fixture required")
    indices = master.slave_indices
    target = master.jet(q, truth, tangent=False)["field"]["value_xyz"]
    q[indices[:3]] = target-closest.so3_exp(q[indices[3:]]/1000.) @ reference
    return master, q, reference, truth


def boundary_comparison(master, q, reference, seed):
    data = response(master, q, reference, seed)
    point = data["reference_point_xyz_mm"]
    boundary = point-data["reference_distance_mm"]*data["reference_normal_xyz"]
    require(abs(boundary[2]) < 1e-9, "top-plane comparison fixture required")
    reference_boundary = master.jet(q, boundary, tangent=False)["field"]["value_xyz"]
    slave = closest.rigid_field(q, reference, np.zeros(3), master.slave_indices)
    current = closest.response(slave, MaterialPlane(master, boundary), q, stiffness_n_mm=1.,
                               slave_body="synthetic-slave", master_body="synthetic-master")
    current_material = current["reference_master_point_xyz_mm"]
    boundary_j = master.jet(q, current_material, tangent=False)["field"]["J_csr"].toarray()
    difference_g = data["force_on_master_xyz_n"] @ (boundary_j-data["master_J"])
    return {"current_euclidean_gap_mm": current["gap_opening_positive_mm"],
            "current_euclidean_energy_nmm": current["energy_nmm"],
            "reference_energy_over_current_energy": data["energy_nmm"]/current["energy_nmm"],
            "current_boundary_material_point_xyz_mm": current_material,
            "current_boundary_point_xyz_mm": current["current_master_point_xyz_mm"],
            "mapped_reference_closest_boundary_xyz_mm": reference_boundary,
            "reference_force_if_moved_to_mapped_reference_boundary_pair_moment_nmm": np.cross(data["current_slave_point_xyz_mm"]-reference_boundary, data["force_on_slave_xyz_n"]),
            "reference_force_if_moved_to_current_closest_boundary_pair_moment_nmm": np.cross(data["current_slave_point_xyz_mm"]-current["current_master_point_xyz_mm"], data["force_on_slave_xyz_n"]),
            "moving_reaction_to_current_boundary_full_work_covector_difference_n": difference_g,
            "current_boundary_normal_vs_interior_covector_angle_rad": float(np.arctan2(
                np.linalg.norm(np.cross(current["current_master_normal_xyz"], data["spatial_distance_gradient"])),
                current["current_master_normal_xyz"] @ data["spatial_distance_gradient"]))}


def transformed(master, q, rotation, translation):
    changed = q.copy()
    offsets = (0, 6) if isinstance(master, AffineMaster) else (0, 6, 12)
    centers = (np.zeros(3), np.zeros(3)) if isinstance(master, AffineMaster) else (np.zeros(3), np.array([100., 0., 0.]), np.zeros(3))
    for offset, center in zip(offsets, centers, strict=True):
        changed[offset:offset+3] = rotation @ (center+q[offset:offset+3])+translation-center
        changed[offset+3:offset+6] = 1000.*closest.so3_log(rotation @ closest.so3_exp(q[offset+3:offset+6]/1000.))
    return changed


def work_objectivity(master, q, reference, seed):
    data = response(master, q, reference, seed)
    direction = np.sin(np.arange(len(q))+.3)
    work = data["force_on_slave_xyz_n"] @ (data["slave_J"] @ direction)
    work += data["force_on_master_xyz_n"] @ (data["master_J"] @ direction)
    rotation, translation = closest.so3_exp([.4, -.3, .2]), np.array([8., -3., 4.])
    moved = response(master, transformed(master, q, rotation, translation), reference, seed)
    return {"colocated_physical_work_error_nmm": float(abs(work+data["gradient_n"] @ direction)),
            "superposed_rigid_energy_error_nmm": abs(moved["energy_nmm"]-data["energy_nmm"]),
            "superposed_rigid_force_error_n": float(np.max(abs(moved["force_on_slave_xyz_n"]-rotation @ data["force_on_slave_xyz_n"]))),
            "colocated_pair_moment_inf_nmm": float(np.max(abs(np.cross(data["current_slave_point_xyz_mm"]-data["current_master_penalty_point_xyz_mm"], data["force_on_slave_xyz_n"]))))}


def inverse_derivative_checks(master, q, reference, seed):
    base = response(master, q, reference, seed)
    step = 1e-3
    first, second = [], []
    for h in np.eye(len(q))*step:
        plus, minus = response(master, q+h, reference, seed), response(master, q-h, reference, seed)
        first.append((plus["reference_point_xyz_mm"]-minus["reference_point_xyz_mm"])/(2*step))
        second.append((plus["inverse_X_q"]-minus["inverse_X_q"])/(2*step))
    return {"inverse_first_derivative_max_abs": float(np.max(abs(base["inverse_X_q"]-np.column_stack(first)))),
            "inverse_second_derivative_max_abs_per_chart_mm": float(np.max(abs(base["inverse_X_qq"]-np.stack(second, axis=2)))),
            "step_chart_mm": step}


def evaluate():
    pins = source_pins()
    result = {}
    for kind in ("uniform-stretch", "affine-shear", "geodesic-bend"):
        master, q, reference, truth = fixture(kind)
        seed = truth+np.array([.1, -.03, .04])
        data = response(master, q, reference, seed)
        result[kind] = {"q": q, "reference_truth": truth,
                        "response": {key: value for key, value in data.items() if key not in ("slave_J", "master_J")},
                        "derivative_checks": previous.finite_difference(
                            lambda state, master=master, reference=reference, seed=seed: response(master, state, reference, seed), q, step=1e-3),
                        "all_three_inverse_coordinate_derivative_checks": inverse_derivative_checks(master, q, reference, seed),
                        "work_and_objectivity": work_objectivity(master, q, reference, seed),
                        "boundary_comparison": boundary_comparison(master, q, reference, seed)}
    source_pins()
    return previous.jsonable({"schema": "thin_bolted_implicit_reference_solid_bedding_coupon/v1",
        "source_sha256": pins, "question": "Can implicit inverse deformation and exact closed reference SDF give objective E/g/H, and what physical law does it define?",
        "fixtures": result, "candidate_q_geometry_K_response_or_capacity_consumed": False,
        "method": {"energy": ".5*reference_area*bedding*negative_reference_SDF_squared",
                   "inverse_first": "X_q=F^-1*(J_slave-J_master_at_fixed_X)",
                   "inverse_second": "X_qq=F^-1*(H_slave-H_master-F_q*X_q-transpose-phi_XX[X_q,X_q])",
                   "current_force": "-area*bedding*rho*F^-T*reference_normal; keep covector magnitude",
                   "master_reaction_port": "Current phi(X)=slave point; interior material point under finite penetration, not automatically the physical boundary",
                   "distance_and_area_basis": "REFERENCE signed distance and REFERENCE slave area; no current-Euclidean-distance or current-area equivalence"},
        "decision": {
            "mathematical_feasibility": "The local branch supports source-bound inverse, full gradient/Hessian and colocated physical point work; common rigid motion is objective without arbitrary rotation gauges.",
            "physical_difference": "Stretch/shear change force scale and current gap relative to Euclidean-distance bedding. Moving the reaction from the implicit interior port to a true boundary generally changes the full generalized work; rigid body closure alone cannot validate this replacement.",
            "production_prerequisites": "Exact closed reference topology and oriented SDF feature/curvature; a globally injective current volume map or certified unique local inverse; station/medial/normal-cone branch handling; whole smaller slave-face reference quadrature and ownership. None is inferred from43 paired planar faces or saved584centroids.",
            "integration": "Full-area moving feature partitions still need jump terms or an explicitly frozen nonsmooth point-discretized potential; the preceding closed-edge Hessian counterexample remains applicable.",
            "recommendation": "Feasible distinct model for bounded preparation, not a substitute physical-current-contact admission. Parent must explicitly choose reference-distance/interior-port bedding or continue true current-boundary contact before full candidate preparation."},
        "primary_source": {"url": "https://arxiv.org/pdf/1808.10420", "locator": "Eqs45-51",
                           "scope": "Reference-area surface potentials and nominal/current tractions are distinct; this inverse reference-volume penalty is our declared derivation, not the paper's adopted surface model."},
        "limits": ["Synthetic homogeneous affine map and one geodesic timber segment only; no candidate topology/query or global inverse proof.",
                   "Reference SDF medial ties and exact touch retain explicit branch/rejection; no smoothing, shifted Hessian, new geometry or physical resistance.",
                   "Objective numerical force balance does not establish actual washer, contact pressure, joint stiffness or demand bounds."],
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "release": {"candidate_method_ready": False, "fabrication": False, "climbing": False, "capacity": False}})


def main():
    invocation = {"actual_sys_argv_from_start": sys.argv.copy(), "pythonpath_from_start": os.environ.get("PYTHONPATH"),
                  "cwd_from_start": str(Path.cwd()), "loaded_driver_sha256": LOADED_SHA}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing implicit-reference result")
    result = {**evaluate(), "execution": invocation}
    with options.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"path": str(options.out), "sha256": sha(options.out)}))


if __name__ == "__main__":
    main()
