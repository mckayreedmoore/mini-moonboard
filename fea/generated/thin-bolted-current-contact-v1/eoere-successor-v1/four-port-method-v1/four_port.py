"""Four independent hole ports joined by an internally condensed strip heel.

Only frozen straight-beam/point kernels are reused. This is an explicit gross
strip network, not the old two-port angle or an actual formed-plate solution.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
TEST = OWN.with_name("test_four_port.py")
INPUT = OWN.with_name("inputs.json")
FRAME_SHA = "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
INPUT_SHA = hashlib.sha256(INPUT.read_bytes()).hexdigest()
TEST_SHA = hashlib.sha256(TEST.read_bytes()).hexdigest()
SCHEMA = "eoere_four_port_gross_strip_elastic_response/v1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_pins():
    pins = {"scripts/thin_bolted_frame_mechanics.py": FRAME_SHA,
        str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA,
        str(INPUT.relative_to(ROOT)): INPUT_SHA}
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "four-port source bytes changed")
    return pins


def array(value, shape):
    result = np.asarray(value, dtype=float)
    require(result.shape == shape and np.isfinite(result).all(), "finite complete four-port value required")
    return result


def transport(point, center):
    result = np.eye(6)
    result[:3] = frame.point_matrix(point, center, 1.)
    return result


def wrench_at(force, moment, point, reference):
    return np.r_[force, moment + np.cross(point - reference, force)]


class FourPortStripModel:
    """24 physical port coordinates [world mm,world radians], no heel support."""
    def __init__(self, inputs=None):
        self.source_sha256 = source_pins()
        self.inputs = copy.deepcopy(inputs if inputs is not None else json.loads(INPUT.read_bytes()))
        data = self.inputs
        require(data["schema"] == "eoere_four_port_inch_centered_strip_scenario/v1", "declared own scenario required")
        L, W, t, s, a, E, nu, shear = (float(data[key]) for key in ("arm_length_mm", "width_mm", "thickness_mm",
            "far_station_mm", "transverse_half_pitch_mm", "elastic_modulus_mpa", "poisson_ratio", "shear_factor"))
        require(np.isfinite([L, W, t, s, a, E, nu, shear]).all() and min(L, W, t, s, a, E, shear) > 0.
            and -.9 < nu < .5 and 0. < s < L and a < W/2 and data["steel_fy_mpa"] is None,
            "finite positive geometry/elastic scenario and unknown Fy required")
        require(Decimal(str(data["far_station_mm"])) - Decimal(str(data["near_station_mm"])) ==
            Decimal(str(data["axial_pitch_mm"])), "own inch-centered pitch differs")
        require((L, W, t, s, a, data["near_station_mm"], data["factory_hole_diameter_mm"]) ==
            (88.9, 88.9, 6.35, 65.0875, 25.4, 23.8125, 10.), "different dimensions require a distinct source-bound scenario")
        require(abs(np.dot(data["flange_axes_local"]["arm-x"], data["flange_axes_local"]["arm-z"])) < 1e-12,
            "two perpendicular arms required")
        self.origin = array(data["heel_reference_xyz_mm"], (3,))
        self.basis = array(data["fitting_basis_columns_xyz"], (3, 3))
        require(np.max(abs(self.basis.T @ self.basis - np.eye(3))) < 1e-12
            and abs(np.linalg.det(self.basis) - 1.) < 1e-12, "proper fitting reference frame required")
        self.strip_width, self.length = W/2, s
        self.A, self.Iy, self.Iz = W/2*t, W/2*t**3/12, t*(W/2)**3/12
        self.J = frame.rectangular_torsion(W/2, t)
        self.E, self.G = E, E/(2*(1+nu))
        self.local_K = frame.beam_stiffness(s, self.A, self.Iy, self.Iz, self.J, self.E, self.G, shear)
        # Exact beam rigid motion removed before energy evaluation, rather than
        # subtracting large quadratic terms. The genuine tip principal block
        # supplies all constitutive coefficients; no stiffness is shifted.
        self.relative = np.column_stack([-transport(np.array([s,0.,0.]), np.zeros(3)), np.eye(6)])
        self.tip_K = self.local_K[6:, 6:]
        self.factored_local_K = self.relative.T @ self.tip_K @ self.relative
        require(np.max(abs(self.factored_local_K-self.local_K)) <=
            32*np.finfo(float).eps*np.max(abs(self.local_K)), "source beam rigid-energy factor differs")
        self.elements, self.port_manifest, self.factory_holes = [], [], []
        self.full_K = np.zeros((30, 30))
        for flange in ("arm-x", "arm-z"):
            along = array(data["flange_axes_local"][flange], (3,))
            across = np.array([0., 1., 0.])
            normal = np.cross(along, across)
            local_basis = np.column_stack([along, across, normal])
            require(np.max(abs(local_basis.T @ local_basis - np.eye(3))) < 1e-12
                and np.linalg.det(local_basis) > 0., "orthogonal perpendicular arm frame required")
            world_basis = self.basis @ local_basis
            for sign, side in ((-1, "minus"), (1, "plus")):
                identifier = flange + "/far-" + side
                port_index = len(self.elements)
                root = self.origin + self.basis @ (sign*W/4*across)
                center = root + self.basis @ (s*along)
                point = self.origin + self.basis @ (s*along + sign*a*across)
                rotate = np.zeros((6, 6))
                rotate[:3, :3] = rotate[3:, 3:] = world_basis.T
                B = np.zeros((12, 30))
                B[:6, :6] = rotate @ transport(root, self.origin)
                indices = np.arange(6+6*port_index, 12+6*port_index)
                B[6:, indices] = rotate @ transport(center, point)
                self.full_K += B.T @ self.factored_local_K @ B
                self.elements.append({"id": identifier, "flange": flange, "B": B,
                    "world_basis": world_basis, "root": root, "center": center, "point": point,
                    "indices": indices, "port_index": port_index})
                self.port_manifest.append({"id": identifier, "flange": flange, "port_index": port_index,
                    "point_reference_xyz_mm": point.tolist(), "strip_root_xyz_mm": root.tolist(),
                    "strip_tip_neutral_xyz_mm": center.tolist(), "hole_to_neutral_xyz_mm": (point-center).tolist(),
                    "six_coordinate_order": ["ux", "uy", "uz", "rx", "ry", "rz"]})
                for row, station in (("near", data["near_station_mm"]), ("far", s)):
                    self.factory_holes.append({"id": flange + "/" + row + "-" + side, "flange": flange,
                        "point_reference_xyz_mm": (self.origin+self.basis@(station*along+sign*a*across)).tolist(),
                        "diameter_mm": data["factory_hole_diameter_mm"], "used_port": row == "far",
                        "hole_removed_from_response_stiffness": False, "actual_heel_datum_qualified": False})
        require([row["id"] for row in self.port_manifest] == data["port_order"], "four own ports in explicit order required")
        self.heel_lift = -np.linalg.solve(self.full_K[:6, :6], self.full_K[:6, 6:])
        self.lift = np.vstack([self.heel_lift, np.eye(24)])
        # Positive element-energy factorization is retained; no diagonal shift.
        self.K = sum((self.relative @ element["B"] @ self.lift).T @ self.tip_K @ (self.relative @ element["B"] @ self.lift)
            for element in self.elements)
        for value in (self.origin, self.basis, self.local_K, self.relative, self.tip_K,
            self.factored_local_K, self.full_K, self.heel_lift, self.lift, self.K):
            value.setflags(write=False)
        for element in self.elements:
            for value in element.values():
                if isinstance(value, np.ndarray):
                    value.setflags(write=False)

    def condensed_matrix(self, *, rotation_scale=1.):
        require(np.isfinite(rotation_scale) and rotation_scale > 0., "positive declared rotation storage scale required")
        scale = np.tile([1., 1., 1., 1/rotation_scale, 1/rotation_scale, 1/rotation_scale], 4)
        return self.K * scale[:, None] * scale[None, :]

    def port_matrix(self, port_id, point_reference_xyz_mm, *, rotation_scale=1.):
        require(np.isfinite(rotation_scale) and rotation_scale > 0., "positive declared rotation storage scale required")
        ports = {row["id"]: row for row in self.port_manifest}
        require(port_id in ports, "exact own strip/hole port ID required; no nearest or equal-sharing route")
        row = ports[port_id]
        result = np.zeros((3, 24))
        result[:, 6*row["port_index"]:6*(row["port_index"]+1)] = frame.point_matrix(
            array(point_reference_xyz_mm, (3,)), row["point_reference_xyz_mm"], rotation_scale)
        return result

    def response(self, q):
        source_pins()
        q = array(q, (24,))
        full = self.lift @ q
        energy, generalized, roots, arms = 0., np.zeros(30), [], {}
        for element in self.elements:
            local = self.relative @ (element["B"] @ full)
            tip_force = self.tip_K @ local
            force = self.relative.T @ tip_force
            energy += .5*float(local @ tip_force)
            generalized += element["B"].T @ force
            root = np.r_[element["world_basis"] @ force[:3], element["world_basis"] @ force[3:6]]
            roots.append({"id": element["id"], "flange": element["flange"], "point_xyz_mm": element["root"].tolist(),
                "applied_to_strip_force_xyz_n": root[:3].tolist(), "applied_to_strip_moment_at_root_xyz_nmm": root[3:].tolist(),
                "on_internal_heel_force_xyz_n": (-root[:3]).tolist(), "on_internal_heel_moment_at_root_xyz_nmm": (-root[3:]).tolist()})
            arms.setdefault(element["flange"], np.zeros(6))
            arms[element["flange"]] += wrench_at(root[:3], root[3:], element["root"], self.origin)
        ports, external = [], np.zeros(6)
        for row in self.port_manifest:
            i = row["port_index"]
            force, moment = generalized[6+6*i:9+6*i], generalized[9+6*i:12+6*i]
            point = np.asarray(row["point_reference_xyz_mm"])
            ports.append({"id": row["id"], "flange": row["flange"], "point_xyz_mm": point.tolist(),
                "external_force_on_fitting_xyz_n": force.tolist(), "external_moment_on_fitting_at_port_xyz_nmm": moment.tolist(),
                "restoring_force_by_fitting_xyz_n": (-force).tolist(), "restoring_moment_by_fitting_at_port_xyz_nmm": (-moment).tolist()})
            external += wrench_at(force, moment, point, self.origin)
        return {"schema": SCHEMA, "energy_nmm": energy, "gradient_mm_rad_units": generalized[6:].tolist(),
            "condensed_heel_q_mm_rad": full[:6].tolist(), "internal_heel_gradient_n_nmm": generalized[:6].tolist(),
            "port_actions": ports, "strip_root_actions": roots,
            "per_flange_applied_strip_root_wrench_about_heel_n_nmm": {key: value.tolist() for key, value in arms.items()},
            "external_resultant_about_heel_n_nmm": external.tolist(), "twice_energy_vs_port_work_nmm": float(q @ generalized[6:]-2*energy),
            "six_physical_rigid_modes": True, "external_heel_clamp_or_load": False,
            "actual_product_plate_or_complete_joint_response_qualified": False}


def plan(model):
    return {"schema": "eoere_four_port_strip_method_plan/v1", "source_sha256": source_pins(), "inputs": model.inputs,
        "ports": model.port_manifest, "all_eight_factory_holes": model.factory_holes,
        "physical_port_dofs": 24, "internally_eliminated_heel_dofs": 6, "expected_rigid_modes": 6,
        "beam_energy_evaluation": "Exact root-relative point transport and frozen tip6x6 beam block; positive energy factor, no clamp/diagonal shift",
        "API": {"constructor": "FourPortStripModel(inputs=None)", "matrix": "condensed_matrix(rotation_scale=1 or1000)",
            "point_mapping": "port_matrix(exact_port_id,point_reference_xyz_mm,rotation_scale=...):3x24; caller embeds actual owned24 indices",
            "recovery": "response(q24world_mm_rad):energy,gradient,four full port wrenches, four strip-root wrenches, two flange heel resultants",
            "gravity": "not supplied; future exact physical mass/centroid/load routing requires own work-conjugate source mapping",
            "production_integration": "Distinct physical fitting owner with4six-coordinate nodes; internal heel is not another physical body. Existing2node fitting finite adapters cannot accept this model unchanged."},
        "accuracy_limits": ["Gross independent half-width strips; shared physical plate-edge continuity omitted",
            "Sharp internal rigid heel collector; actual formed bend/radius/flexibility unknown", "All8hole cut/local bearing effects omitted",
            "St Venant rectangular torsion proxy only; restrained warping/shear-center/plate/prying accuracy unqualified",
            "No finite objective fitting energy or global four-port adapter qualified by this linear method",
            "No product Fy/Fu, preload, friction, washer seat response or resistance inferred", "No candidate forces/cases/geometry/native/K consumed"],
        "release": {"candidate_mechanics": False, "capacity": False, "fabrication": False, "climbing": False}}


def known_answer(model):
    P, c, L = 7., model.inputs["width_mm"]/4, model.length
    q = np.zeros(24)
    for i, sign in ((0, -1), (1, 1)):
        theta = c*P*L/(model.E*model.Iz)
        delta = sign*(model.inputs["transverse_half_pitch_mm"]-c)
        q[6*i:6*i+6] = [sign*P*L/(model.E*model.A)-delta*theta,
            c*P*L**2/(2*model.E*model.Iz), 0., 0., 0., theta]
    result = model.response(q)
    expected = np.zeros(24)
    expected[0], expected[6] = -P, P
    expected[5] = expected[11] = model.inputs["transverse_half_pitch_mm"]*P
    expected_energy = P**2*L/(model.E*model.A)+(c*P)**2*L/(model.E*model.Iz)
    require(np.max(abs(np.asarray(result["gradient_mm_rad_units"])-expected)) < 1e-8
        and abs(result["energy_nmm"]-expected_energy) < 1e-12, "four-port self-equilibrated hand answer differs")
    return {"schema": "eoere_four_port_strip_method_coupon/v1", "source_sha256": source_pins(),
        "method_known_answer_pass": True, "plan": plan(model), "hand_answer": {"q_mm_rad": q.tolist(), "port_applied_wrenches_n_nmm": expected.reshape(4,6).tolist(),
            "energy_nmm": expected_energy, "recipe": "arm-x opposed axial forces +/-7N plus each own +25.4*7Nmm Mz; common heel unloaded; isolated-strip pure axial+moment closed form"},
        "observed": result, "candidate_response_or_product_acceptance": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "coupon"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve previous four-port evidence")
    model = FourPortStripModel()
    result = plan(model) if args.mode == "plan" else known_answer(model)
    result["execution"] = {"actual_sys_argv": sys.argv.copy(), "actual_sys_orig_argv": sys.orig_argv.copy(),
        "loaded_source_path": str(OWN.relative_to(ROOT)), "loaded_source_sha256": LOADED_SHA}
    source_pins()
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "candidate_assembly_or_response": False}))


if __name__ == "__main__":
    main()
