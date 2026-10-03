#!/usr/bin/env python3
"""Conditional frame sensitivity using the existing frozen compliance operator.

No native solver or authority mutation. Only the four target bolt lateral
laws change. Other source laws and each source floor tangent mask are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
from scipy import linalg, optimize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
COMP = BASE / "current-frame-connector-compliance-attempt04"
FREEZE = ROOT / "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/freeze.json"
TARGET = np.arange(112, 120)
BLOCK = "left_service_outer_upper_cleat"
RAIL = "base_rail_service_upper_left"
SIDE = "base_side_left"
DATUM = np.array([-1085.85, 769.502826578, 1367.736899429])
FORCE_TOL_N = 1e-6
GAP_TOL_MM = 1e-8
FIXED_PINS = {
    COMP / "operators.npz": "88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79",
    COMP / "row-identities.json": "768d2afe58b48fa482f118f73bb01b8c911d1f937a5891d5c420a0d821b45037",
    COMP / "assessment.json": "ae30902f9340875a771d60dab83621ab5e0d6dcadb58c06a35bdb1bc8ac9da6c",
    COMP / "inputs.json": "3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208",
    BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json": "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    FREEZE: "c7669530756bcdb24662c879b86545e23934fa9ea810c00b66fa08d91d051f4f",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def maxabs(value):
    return float(np.max(np.abs(value), initial=0.0))


def project_disks(value, radius):
    pairs = np.asarray(value).reshape(4, 2)
    norms = np.linalg.norm(pairs, axis=1)
    return (pairs * np.minimum(1.0, radius / np.maximum(norms, 1e-300))[:, None]).ravel()


def clearance_offsets(f0, response, clearance):
    """Solve eight-dimensional raw compatibility with four circular gaps.

    f_target = f0 - response @ h. The gap offset h lies in four disks;
    h is on the outward force direction when the corresponding force is
    nonzero. h=projection(h+step*f) is its exact complementarity condition.
    This permits zero force inside the gap without adding a physical spring.
    """
    if clearance == 0:
        return np.zeros(8), {"evaluations": 0, "projection_residual_mm": 0.0}
    spectral = float(np.linalg.norm(response, ord=2))
    if spectral <= 0:
        raise ValueError("zero target force response")
    step = 1.0 / spectral
    eye = np.eye(8)

    def residual(h):
        force = f0 - response @ h
        return h - project_disks(h + step * force, clearance)

    def jacobian(h):
        z = (h + step * (f0 - response @ h)).reshape(4, 2)
        derivative = np.zeros((8, 8))
        for i, pair in enumerate(z):
            r = np.linalg.norm(pair)
            if r <= clearance:
                block = np.eye(2)
            else:
                unit = pair / r
                block = clearance / r * (np.eye(2) - np.outer(unit, unit))
            derivative[2*i:2*i+2, 2*i:2*i+2] = block
        return eye - derivative @ (eye - step * response)

    # The response has a neutral force direction associated with cleat
    # sliding. A constrained quadratic seed avoids a poor local minimum
    # of the squared projection residual. The seed uses the symmetric part;
    # the final solve and every audit use the original raw response.
    symmetric = 0.5 * (response + response.T)

    def seed_objective(z):
        h = clearance * z
        return 0.5 * h @ symmetric @ h - f0 @ h

    def seed_gradient(z):
        return clearance * (symmetric @ (clearance * z) - f0)

    def constraints(z):
        return 1.0 - np.sum(z.reshape(4, 2)**2, axis=1)

    def constraint_jacobian(z):
        answer = np.zeros((4, 8))
        for i in range(4):
            answer[i, 2*i:2*i+2] = -2.0 * z[2*i:2*i+2]
        return answer

    seed = optimize.minimize(seed_objective, np.zeros(8), jac=seed_gradient,
                             method="SLSQP", constraints=[{"type": "ineq", "fun": constraints,
                                                          "jac": constraint_jacobian}],
                             options={"ftol": 1e-12, "maxiter": 500})
    if not np.all(np.isfinite(seed.x)):
        raise ValueError("nonfinite clearance seed")
    result = optimize.least_squares(residual, project_disks(clearance * seed.x, clearance), jac=jacobian,
                                    ftol=1e-13, xtol=1e-13, gtol=1e-13,
                                    max_nfev=200)
    error = maxabs(residual(result.x))
    if error > GAP_TOL_MM:
        raise ValueError(f"clearance complementarity did not converge: {error}")
    return result.x, {"evaluations": int(result.nfev), "seed_iterations": int(seed.nit),
                      "seed_success": bool(seed.success), "seed_message": str(seed.message),
                      "raw_response_asymmetry_n_per_mm": maxabs(response - response.T),
                      "projection_residual_mm": error}


class Frame:
    def __init__(self):
        self.pins = {}
        for path, expected in FIXED_PINS.items():
            if sha(path) != expected:
                raise ValueError(f"source pin changed: {path}")
            self.pins[str(path.relative_to(ROOT))] = expected
        with np.load(COMP / "operators.npz", allow_pickle=False) as data:
            self.H, self.D, self.e, self.W = (data[k] for k in ("H", "D", "e", "W"))
        self.rows = read(COMP / "row-identities.json")
        self.record = read(COMP / "assessment.json")
        self.freeze = read(FREEZE)
        adapter = read(BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json")
        self.models, self.sources = {}, {}
        for case, files in self.freeze["cases"].items():
            for kind in ("model", "response"):
                path = ROOT / files[kind]["path"]
                if sha(path) != files[kind]["sha256"]:
                    raise ValueError(f"case pin changed: {case}/{kind}")
                self.pins[files[kind]["path"]] = files[kind]["sha256"]
            self.models[case] = read(ROOT / files["model"]["path"])
            self.sources[case] = read(ROOT / files["response"]["path"])
        self.identity = {}
        physical_ids = sorted({str(n) for nodes in adapter["physical_body_nodes"].values() for n in nodes})
        expected_coordinates = {n: adapter["nodes"][n] for n in physical_ids}
        expected_elements = {n: value for n, value in adapter["elements"].items() if value[0] == "C3D20"}
        fields = ("physical_body_nodes", "physical_body_elements", "body_geometry", "material_binding")
        for case, model in self.models.items():
            matches = {field: model[field] == adapter[field] for field in fields}
            matches["physical_node_coordinates"] = {n: model["nodes"][n] for n in physical_ids} == expected_coordinates
            matches["solid_element_connectivity_and_owners"] = {n: value for n, value in model["elements"].items() if value[0] == "C3D20"} == expected_elements
            if not all(matches.values()):
                raise ValueError(f"operator physical identity differs for {case}: {matches}")
            self.identity[case] = matches
        self.k = np.array([r["law"].get("stiffness_N_per_mm", 0.0) for r in self.rows])
        self.unilateral = np.array([i for i, r in enumerate(self.rows) if r["family"] == "unilateral_springa"])
        self.bilateral = np.array([i for i, r in enumerate(self.rows) if r["family"] == "bilateral_spring2"])
        self.floor_normal = np.array([i for i, r in enumerate(self.rows) if r["ownership"]["role"] == "floor_normal"])
        self.nonfloor = np.setdiff1d(self.unilateral, self.floor_normal)
        self.body_names = self.record["body_names_in_rigid_column_order"]
        self.centers = {}
        model = self.models["a12-rear"]
        for body in self.body_names:
            self.centers[body] = np.mean([model["nodes"][str(n)] for n in model["physical_body_nodes"][body]], axis=0)
        assert self.H.shape == (1840, 1840) and self.D.shape == (1840, 300)
        assert len(self.floor_normal) == 100
        assert all(BLOCK in (self.rows[int(i)]["ownership"]["first_body"],
                             self.rows[int(i)]["ownership"]["second_body"]) for i in TARGET)

    def source_state(self, case, increment):
        inc = self.sources[case]["increments"][increment]
        springs = {r["source_group"]: r for r in inc["springa_components"]}
        bilaterals = {r["source_group"]: r for r in inc["retained_bilateral_spring2_components"]}
        floor = {r["source_row_id"]: r for r in inc["exact_floor_tangent_reactions"]}
        f, q, held = np.zeros(1840), np.zeros(1840), []
        for i, row in enumerate(self.rows):
            if row["family"] == "unilateral_springa":
                item = springs[row["source_group"]]
                f[i], q[i] = item["native_endpoint_internal_force_N"], item["q_relative_projection_mm"]
            elif row["family"] == "bilateral_spring2":
                item = bilaterals[row["source_group"]]
                f[i], q[i] = item["force_on_first_local_N"], item["relative_displacement_mm"]
            elif row["row_id"] in floor:
                f[i] = -floor[row["row_id"]]["recovered_physical_tangent_reaction_N"]
                held.append(i)
        return inc, f, q, np.array(held, dtype=int)

    def branch(self, active, held, e, W, lateral_k, clearance):
        positions = np.sort(np.concatenate((self.bilateral, active, held)))
        k = self.k[positions].copy()
        target_local = np.searchsorted(positions, TARGET)
        assert np.array_equal(positions[target_local], TARGET)
        if lateral_k is not None:
            k[target_local] = lateral_k
        inverse_k = np.divide(1.0, k, out=np.zeros_like(k), where=k > 0)
        n = len(positions)
        matrix = np.zeros((n + 300, n + 300))
        matrix[:n, :n] = self.H[np.ix_(positions, positions)] + np.diag(inverse_k)
        matrix[:n, n:] = -self.D[positions]
        matrix[n:, :n] = self.D[positions].T
        rhs = np.zeros((n + 300, 9))
        rhs[:n, 0] = e[positions]
        rhs[n:, 0] = W
        rhs[target_local, np.arange(1, 9)] = 1.0
        with warnings.catch_warnings():
            warnings.simplefilter("error", linalg.LinAlgWarning)
            lu, pivot = linalg.lu_factor(matrix, check_finite=False)
            solved = linalg.lu_solve((lu, pivot), rhs, check_finite=False)
        rcond, info = linalg.lapack.get_lapack_funcs("gecon", (lu,))(lu, np.linalg.norm(matrix, 1))
        if info or rcond < 1e-14:
            raise ValueError(f"singular/ill-conditioned branch: {rcond}")
        h, gap_audit = clearance_offsets(solved[target_local, 0], solved[target_local, 1:], clearance)
        value = solved[:, 0] - solved[:, 1:] @ h
        f = np.zeros(1840)
        f[positions] = value[:n]
        a = value[n:]
        q = self.D @ a + e - self.H @ f
        law_q = f[positions] * inverse_k
        law_q[target_local] += h
        audit = {
            "reciprocal_condition": float(rcond),
            "linear_system_residual_max": maxabs(matrix @ value - (rhs[:, 0] - rhs[:, 1:] @ h)),
            "active_compatibility_residual_mm": maxabs(q[positions] - law_q),
            "body_wrench_scaled_residual_N": maxabs(self.D.T @ f - W),
            **gap_audit,
        }
        if audit["active_compatibility_residual_mm"] > GAP_TOL_MM or audit["body_wrench_scaled_residual_N"] > FORCE_TOL_N:
            raise ValueError(f"branch equation residual failed: {audit}")
        return f, q, a, h, audit

    def evaluate(self, case, increment, scale, clearance, lateral_k=None):
        if scale <= 0 or clearance < 0 or (lateral_k is not None and lateral_k <= 0):
            raise ValueError("invalid sensitivity input")
        inc, native_f, native_q, held = self.source_state(case, increment)
        columns = [c["column"] for c in self.record["load_columns"] if c["case_id"] == case]
        factor = scale * inc["load_factor"]
        e, W = factor * self.e[:, columns].sum(axis=1), factor * self.W[:, columns].sum(axis=1)
        active = self.unilateral[native_q[self.unilateral] > 0]
        closed = np.intersect1d(active, self.floor_normal)
        opened = np.setdiff1d(self.floor_normal, closed)
        seen = set()
        history = []
        for iteration in range(30):
            key = tuple(active)
            if key in seen:
                raise ValueError("normal active-set cycle")
            seen.add(key)
            f, q, a, h, audit = self.branch(active, held, e, W, lateral_k, clearance)
            free_nonfloor = np.intersect1d(active, self.nonfloor)
            bound_nonfloor = np.setdiff1d(self.nonfloor, active)
            release = free_nonfloor[f[free_nonfloor] < -FORCE_TOL_N]
            engage = bound_nonfloor[q[bound_nonfloor] > GAP_TOL_MM]
            history.append({"iteration": iteration, "released_rows": release.tolist(), "engaged_rows": engage.tolist()})
            if not len(release) and not len(engage):
                break
            active = np.union1d(np.setdiff1d(active, release), engage)
        else:
            raise ValueError("normal active-set iteration limit")
        floor_ok = bool(np.all(f[closed] > FORCE_TOL_N) and np.all(q[closed] > GAP_TOL_MM)
                        and np.all(q[opened] < -GAP_TOL_MM))
        target_pairs, gap_force_error = [], 0.0
        for i in range(4):
            pair = TARGET[2*i:2*i+2]
            displacement, force = q[pair], f[pair]
            radius = np.linalg.norm(displacement)
            stiffness = self.k[pair[0]] if lateral_k is None else lateral_k
            expected_force = stiffness * max(radius - clearance, 0.0) * displacement / max(radius, 1e-300)
            gap_force_error = max(gap_force_error, maxabs(force - expected_force))
            target_pairs.append({"axis": self.rows[int(pair[0])]["row_id"].split("/")[-2],
                                 "q_components_mm": displacement.tolist(), "force_components_n": force.tolist(),
                                 "slip_mm": float(radius), "shear_n": float(np.linalg.norm(force)),
                                 "gap_offset_mm": h[2*i:2*i+2].tolist()})
        audit["circular_gap_force_law_residual_n"] = gap_force_error
        audit["unilateral_force_min_n"] = float(f[self.unilateral].min())
        audit["open_nonfloor_gap_max_mm"] = float(q[np.setdiff1d(self.nonfloor, active)].max())
        audit["floor_branch_consistent"] = floor_ok
        audit["closed_floor_min_force_n"] = float(f[closed].min())
        audit["open_floor_max_gap_mm"] = float(q[opened].max())
        audit["held_floor_tangent_gap_max_mm"] = maxabs(q[held])
        released_floor = np.setdiff1d(np.arange(1640, 1840), held)
        audit["released_floor_tangent_force_max_n"] = maxabs(f[released_floor])
        normal_expected = self.k[self.unilateral] * np.maximum(q[self.unilateral], 0.0)
        audit["unilateral_force_law_residual_n"] = maxabs(f[self.unilateral] - normal_expected)
        audit["unilateral_max_abs_q_mm"] = maxabs(q[self.unilateral])
        audit["unilateral_max_positive_q_mm"] = float(np.max(q[self.unilateral]))
        audit["open_rows_beyond_source_negative_table_endpoint"] = int(np.count_nonzero(q[self.unilateral] < -10))
        # Explicit study assumption: an already open normal spring carries
        # zero force at any separation. Positive branches retain the source
        # table range; no positive-branch extrapolation is allowed.
        if audit["unilateral_force_law_residual_n"] > 1e-4 or audit["unilateral_max_positive_q_mm"] > 10:
            raise ValueError(f"source normal law/domain failed: {audit}")
        if gap_force_error > FORCE_TOL_N:
            raise ValueError(f"gap force law failed: {gap_force_error}")
        motions = {}
        for body in (BLOCK, RAIL, SIDE):
            i = self.body_names.index(body)
            translation, rotation = a[6*i:6*i+3], a[6*i+3:6*i+6] / 1000.0
            motions[body] = {"translation_at_common_datum_mm": (translation + np.cross(rotation, DATUM - self.centers[body])).tolist(),
                            "rotation_rad": rotation.tolist()}
        relative = np.array(motions[RAIL]["translation_at_common_datum_mm"]) - np.array(motions[SIDE]["translation_at_common_datum_mm"])
        rotation = np.array(motions[RAIL]["rotation_rad"]) - np.array(motions[SIDE]["rotation_rad"])
        interface_wrenches = {}
        local_fits = {}
        block_index = self.body_names.index(BLOCK)
        for host in (RAIL, SIDE):
            ports = [i for i, row in enumerate(self.rows)
                     if {row["ownership"]["first_body"], row["ownership"]["second_body"]} == {BLOCK, host}]
            generalized = -self.D[ports, 6*block_index:6*block_index+6].T @ f[ports]
            force = generalized[:3]
            moment = 1000 * generalized[3:] + np.cross(self.centers[BLOCK] - DATUM, force)
            interface_wrenches[host] = {"row_positions": ports, "force_on_cleat_global_n": force.tolist(),
                                       "moment_on_cleat_at_common_datum_nmm": moment.tolist()}
            # Use every returned interface projection, including the elastic
            # e-Hf correction. Fit a local six-coordinate relative pose at
            # the common datum; retain its nonrigid residual explicitly.
            local_map = self.D[ports, 6*block_index:6*block_index+6].copy()
            local_map[:, 3:] = 1000 * local_map[:, 3:] + np.cross(
                self.centers[BLOCK] - DATUM, local_map[:, :3])
            pose, _, rank, _ = np.linalg.lstsq(local_map, q[ports], rcond=None)
            if rank != 6:
                raise ValueError(f"local interface motion fit lacks six coordinates: {host}")
            local_fits[host] = {"cleat_relative_to_host_translation_at_common_datum_mm": pose[:3].tolist(),
                                "cleat_relative_to_host_rotation_rad": pose[3:].tolist(),
                                "maximum_nonrigid_projection_residual_mm": maxabs(local_map @ pose - q[ports]),
                                "row_positions": ports, "rank": int(rank)}
        local_relative = np.array(local_fits[SIDE]["cleat_relative_to_host_translation_at_common_datum_mm"]) - np.array(local_fits[RAIL]["cleat_relative_to_host_translation_at_common_datum_mm"])
        local_rotation = np.array(local_fits[SIDE]["cleat_relative_to_host_rotation_rad"]) - np.array(local_fits[RAIL]["cleat_relative_to_host_rotation_rad"])
        report = {
            "case": case, "increment": increment, "source_load_factor": inc["load_factor"],
            "load_scale": scale, "effective_load_factor": factor, "clearance_mm": clearance,
            "lateral_stiffness_n_per_mm": lateral_k if lateral_k is not None else "frozen source",
            "status": "CONDITIONAL_FIXED_FLOOR_BRANCH" if floor_ok else "STOP_FLOOR_BRANCH_CHANGED",
            "target_bolts": target_pairs, "body_rigid_component_motions": motions,
            "rail_relative_to_side_at_common_datum_mm": relative.tolist(),
            "rail_relative_to_side_rotation_rad": rotation.tolist(),
            "rail_relative_to_side_movement_mm": float(np.linalg.norm(relative)),
            "rail_relative_to_side_rotation_deg": float(np.linalg.norm(rotation) * 180 / np.pi),
            "normal_branch_iterations": history, "audit": audit,
            "zero_clearance_native_force_max_difference_n": maxabs(f - scale*native_f) if clearance == 0 and lateral_k is None else None,
            "zero_clearance_native_q_max_difference_mm": maxabs(q[:1640] - scale*native_q[:1640]) if clearance == 0 and lateral_k is None else None,
            "target_axial_tension_n": f[1588:1592].tolist(),
            "simultaneous_interface_wrenches": interface_wrenches,
            "local_interface_projection_fits": local_fits,
            "local_fit_rail_relative_to_side_translation_mm": local_relative.tolist(),
            "local_fit_rail_relative_to_side_rotation_rad": local_rotation.tolist(),
            "local_fit_rail_side_movement_mm": float(np.linalg.norm(local_relative)),
            "local_fit_rail_side_rotation_deg": float(np.linalg.norm(local_rotation) * 180 / np.pi),
        }
        return report, {"f": f, "q": q, "a": a, "active_normal_rows": active, "held_floor_rows": held}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("a1-rear", "a12-rear", "k12-rear"), default="a12-rear")
    parser.add_argument("--increment", type=int, default=6)
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--clearance", type=float, default=1.15)
    parser.add_argument("--lateral-k", type=float)
    args = parser.parse_args()
    frame = Frame()
    report, _ = frame.evaluate(args.case, args.increment, args.scale, args.clearance, args.lateral_k)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
