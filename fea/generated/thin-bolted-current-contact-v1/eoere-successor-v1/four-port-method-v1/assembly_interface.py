"""Small first-order four-port seam; no candidate reader or global assembler.

A declared centroid point wrench is applied to the internal rigid collector
before static condensation. This is a localized body-load scenario, not a
physical uniform weight distribution, and adds no external heel restraint.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

OWN = Path(__file__).resolve()
METHOD = OWN.with_name("four_port.py")
METHOD_SHA = "8482d5f3f1d01eee9141db2bbeef5237f87cb7d78f00619749604c0a23f57567"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
ROUTE = "source-point-wrench-through-internal-rigid-heel-v1"
SPEC = importlib.util.spec_from_file_location("eoere_frozen_four_port_for_assembly", METHOD)
four = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(four)


def source_pins():
    four.require(four.sha(METHOD) == METHOD_SHA, "frozen four-port method changed")
    four.require(four.sha(OWN) == LOADED_SHA, "loaded assembly interface changed")
    return {**four.source_pins(), str(OWN.relative_to(four.ROOT)): LOADED_SHA}


def model_from_reference_pose(origin_xyz_mm, u_xyz, v_xyz, w_xyz):
    """Reuse frozen nodes at source entry planes; keep a proper reference basis.

    Source arms follow u/v and source transverse follows w=u cross v. Frozen
    axes x/y/z therefore map to u/-w/v: transverse signs reverse explicitly.
    This never normalizes, orthogonalizes or changes supplied source datums.
    """
    u, v, w = (four.array(value, (3,)) for value in (u_xyz, v_xyz, w_xyz))
    four.require(np.max(abs(np.cross(u, v)-w)) < 1e-12, "proper source fitting axes required")
    data = json.loads(four.INPUT.read_bytes())
    data["heel_reference_xyz_mm"] = four.array(origin_xyz_mm, (3,)).tolist()
    data["fitting_basis_columns_xyz"] = np.column_stack([u, -w, v]).tolist()
    model = four.FourPortStripModel(data)
    bindings = [{"source_flange": flange, "source_row": "far", "source_transverse": sign,
                 "model_port_id": arm + ("/far-minus" if sign == 1 else "/far-plus")}
                for flange, arm in (("beam", "arm-x"), ("post", "arm-z")) for sign in (-1, 1)]
    return model, bindings


class FourPortAssemblyElement:
    """Exact owned 24 indices; source fitting remains one physical body."""

    def __init__(self, model, body_id, dof_indices, ndof, *, rotation_scale=1000.):
        self.source_sha256 = source_pins()
        four.require(isinstance(model, four.FourPortStripModel), "genuine frozen four-port model required")
        indices = np.asarray(dof_indices)
        four.require(isinstance(body_id, str) and body_id and indices.shape == (24,)
                     and np.issubdtype(indices.dtype, np.integer) and len(set(indices.tolist())) == 24
                     and isinstance(ndof, int) and np.all((indices >= 0) & (indices < ndof)),
                     "one named fitting and 24 distinct actual global indices required")
        four.require(np.isfinite(rotation_scale) and rotation_scale > 0., "positive rotation storage scale required")
        self.model, self.body_id, self.ndof = model, body_id, ndof
        self.indices, self.rotation_scale = indices.copy(), float(rotation_scale)
        self.scale = np.tile([1., 1., 1., 1./rotation_scale, 1./rotation_scale, 1./rotation_scale], 4)
        self.indices.setflags(write=False)

    def elastic_block(self):
        return self.indices.copy(), self.model.condensed_matrix(rotation_scale=self.rotation_scale)

    def descriptor(self):
        """Pure owned map/operator record; no predecessor census or field ID."""
        matrix = self.elastic_block()[1].astype("<f8", copy=False)
        return {"schema": "eoere_first_order_four_port_assembly_descriptor/v1", "body": self.body_id,
                "dof_indices": self.indices.tolist(), "ndof": self.ndof, "rotation_scale": self.rotation_scale,
                "ports": copy.deepcopy(self.model.port_manifest), "all_factory_holes": copy.deepcopy(self.model.factory_holes),
                "own_fitting_scenario": copy.deepcopy(self.model.inputs),
                "scenario_canonical_sha256": hashlib.sha256(json.dumps(self.model.inputs, sort_keys=True,
                    separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                "elastic_block_little_endian_float64_sha256": hashlib.sha256(matrix.tobytes()).hexdigest(),
                "source_sha256": source_pins(), "gravity_route": ROUTE, "internal_heel_is_physical_owner": False,
                "centroid_load_port_is_not_a_contact_or_surface_kinematic_port": True,
                "field_admission_or_product_accuracy": False}

    def point_port(self, exact_port_id, point_reference_xyz_mm):
        local = self.model.port_matrix(exact_port_id, point_reference_xyz_mm,
                                       rotation_scale=self.rotation_scale)
        rows, cols = np.nonzero(local)
        return csr_matrix((local[rows, cols], (rows, self.indices[cols])), shape=(3, self.ndof))

    def centroid_load_port(self, point_reference_xyz_mm, *, declared_route):
        """Work-conjugate source body-load port only; not a contact point map."""
        four.require(declared_route == ROUTE, "explicit localized collector body-load scenario required")
        local = (four.frame.point_matrix(four.array(point_reference_xyz_mm, (3,)), self.model.origin, 1.)
                 @ self.model.heel_lift)*self.scale[None, :]
        rows, cols = np.nonzero(local)
        return csr_matrix((local[rows, cols], (rows, self.indices[cols])), shape=(3, self.ndof))

    def rigid_modes(self, reference_xyz_mm):
        reference = four.array(reference_xyz_mm, (3,))
        result = np.zeros((24, 6))
        for row in self.model.port_manifest:
            i = row["port_index"]
            result[6*i:6*i+3] = four.frame.point_matrix(row["point_reference_xyz_mm"], reference, 1.)
            result[6*i+3:6*i+6, 3:] = np.eye(3)*self.rotation_scale
        return result

    def project_loads(self, loads, *, declared_route):
        """Return the affine condensed RHS, preserving every physical load row."""
        four.require(declared_route == ROUTE, "explicit localized collector body-load scenario required")
        rows, wrench = [], np.zeros(6)
        for row in loads:
            four.require(row["body"] == self.body_id and isinstance(row["id"], str), "load must own this physical fitting")
            point = four.array(row["point_xyz_mm"], (3,))
            force = four.array(row["force_xyz_n"], (3,))
            moment = four.array(row.get("moment_xyz_nmm", [0., 0., 0.]), (3,))
            wrench += four.wrench_at(force, moment, point, self.model.origin)
            rows.append(copy.deepcopy(row))
        four.require(len({row["id"] for row in rows}) == len(rows), "physical fitting load repeated")
        shift = np.linalg.solve(self.model.full_K[:6, :6], wrench)
        rhs = self.model.heel_lift.T @ wrench
        return {"schema": "eoere_four_port_loaded_collector_projection/v1", "route": ROUTE,
                "body": self.body_id, "physical_load_rows": rows, "heel_wrench_n_nmm": wrench.tolist(),
                "heel_load_shift_mm_rad": shift.tolist(), "rhs_port_mm_rad_units": rhs.tolist(),
                "rhs_stored_units": (self.scale*rhs).tolist(),
                "potential_constant_nmm": -.5*float(wrench @ shift),
                "uniform_physical_weight_distribution_inferred": False, "external_heel_support": False}

    def response(self, q_stored, *, loads=(), declared_route):
        """Small local recovery from genuine beam factors and loaded heel solve."""
        projection = self.project_loads(loads, declared_route=declared_route)
        q = four.array(q_stored, (24,))*self.scale
        heel = self.model.heel_lift @ q + np.asarray(projection["heel_load_shift_mm_rad"])
        full = np.r_[heel, q]
        elastic, generalized = 0., np.zeros(30)
        for element in self.model.elements:
            relative = self.model.relative @ element["B"]
            strain = relative @ full
            elastic += .5*float(strain @ self.model.tip_K @ strain)
            generalized += relative.T @ self.model.tip_K @ strain
        wrench = np.asarray(projection["heel_wrench_n_nmm"])
        port_rows, total = [], wrench.copy()
        for row in self.model.port_manifest:
            i = row["port_index"]
            action = generalized[6+6*i:12+6*i]
            total += four.wrench_at(action[:3], action[3:], row["point_reference_xyz_mm"], self.model.origin)
            port_rows.append({"body": self.body_id, "port_id": row["id"],
                              "point_xyz_mm": row["point_reference_xyz_mm"],
                              "external_force_required_at_port_xyz_n": action[:3].tolist(),
                              "external_couple_required_at_port_xyz_nmm": action[3:].tolist()})
        return {"schema": "eoere_four_port_assembly_seam_response/v1", "body": self.body_id,
                "elastic_energy_nmm": elastic, "potential_nmm": elastic-float(wrench @ heel),
                "gradient_stored_units": (generalized[6:]*self.scale).tolist(),
                "loaded_heel_q_mm_rad": heel.tolist(), "heel_net_residual_n_nmm": (generalized[:6]-wrench).tolist(),
                "port_actions": port_rows, "external_body_resultant_about_heel_n_nmm": total.tolist(),
                "load_projection": projection, "candidate_field_or_capacity_admitted": False}


def coupon():
    """One genuine loaded-condensation/work witness, not a candidate response."""
    model = four.FourPortStripModel()
    element = FourPortAssemblyElement(model, "synthetic-fitting", np.arange(3, 27), 31)
    loads = [{"id": "synthetic-own-centroid-gravity", "body": element.body_id,
              "point_xyz_mm": [18., 3., 21.], "force_xyz_n": [0., 0., -12.]}]
    q = np.random.default_rng(5).normal(size=24)*1e-4
    result = element.response(q, loads=loads, declared_route=ROUTE)
    projection = result["load_projection"]
    full = np.r_[result["loaded_heel_q_mm_rad"], q*element.scale]
    residual = model.full_K @ full-np.r_[projection["heel_wrench_n_nmm"], np.zeros(24)]
    _, matrix = element.elastic_block()
    exact_gradient = matrix @ q-np.asarray(projection["rhs_stored_units"])
    observed_gradient = np.asarray(result["gradient_stored_units"])
    rigid_work = element.rigid_modes([0., 0., 0.]).T @ np.asarray(projection["rhs_stored_units"])
    metrics = {"loaded_heel_stationarity_inf_n_nmm": float(np.max(abs(residual[:6]))),
               "condensed_affine_gradient_difference_inf": float(np.max(abs(exact_gradient-observed_gradient))),
               "full_gradient_difference_inf": float(np.max(abs(residual[6:]*element.scale-observed_gradient))),
               "source_wrench_vs_rigid_work_difference_inf": float(np.max(abs(rigid_work-projection["heel_wrench_n_nmm"]))),
               "body_force_moment_closure_inf_n_nmm": float(np.max(abs(np.asarray(result["external_body_resultant_about_heel_n_nmm"]))))}
    four.require(max(metrics.values()) < 1e-7, "synthetic loaded-condensation/work witness failed")
    return {"schema": "eoere_four_port_assembly_method_witness/v1", "source_sha256": source_pins(),
            "operator_descriptor": element.descriptor(), "toy_stored_q": q.tolist(),
            "expected_physical_gravity_wrench_about_heel_n_nmm": [0., 0., -12., -36., 216., 0.],
            "response": result, "metrics": metrics, "small_method_witness_pass": True,
            "candidate_prepared_or_evaluated": False, "old_field_or_pass_transferred": False}


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coupon-out", type=Path, required=True)
    args = parser.parse_args()
    four.require(not args.coupon_out.exists(), "preserve existing method witness output")
    result = coupon()
    for path in (OWN.with_name("test_assembly_interface.py"), OWN.with_name("assembly-plan.json")):
        result["source_sha256"][str(path.relative_to(four.ROOT))] = four.sha(path)
    result["execution"] = {"sys_argv": sys.argv, "sys_orig_argv": sys.orig_argv,
                           "python": sys.version, "numpy": np.__version__}
    args.coupon_out.parent.mkdir(parents=True, exist_ok=True)
    with args.coupon_out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
