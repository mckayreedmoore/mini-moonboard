"""Independent small-model diagnostics; no native solve or strength acceptance.

Run with the repository virtual environment. Only this packet's JSON is written.
"""

from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
REPORTS = {
    "a12-rear": ("current-corner-native-demand-export-attempt03/corner-demand-report.json", "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17"),
    "a1-rear": ("current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json", "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce"),
    "k12-rear": ("current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json", "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0"),
}
METHOD_SOURCES = {
    "current-bg003-piecewise-bearing-profile-feasibility-attempt01/profile-check.json": "215bfecdd74e11688a5289c85c3179b79dbb7751c67376ff4def955f8fd6bb9e",
    "current-springa-ideal-stick-branch-cycle-method-attempt01/fixture-spec.json": "db922b42f960529a8b0eb4fd0d7aacff63cce1fb338d71fab8d851b97d3033b9",
    "current-springa-selected-floor-a12-forward-attempt05/model.inp": "7b3baa0232ba9b76874607ac20019feec28ce54e5071276e54e68e9acbb9585d",
    "current-springa-selected-floor-a12-forward-attempt05/model.json": "fc24c64fba9e2a88e3d1604500798063a13f8e45bf612fa912c7618d5c40c7b0",
}
MEMBERS = ["knee_outer_left_spine", "base_side_left", "knee_outer_left_inner_frame_block"]
LENGTHS = np.array([38.1, 88.9, 88.9])
LENGTH = float(sum(LENGTHS))
EDGES = np.r_[0.0, np.cumsum(LENGTHS)] / LENGTH
CENTERS = (EDGES[:-1] + EDGES[1:]) / 2
MIDDLE_CUT = float((38.1 + 44.45) / LENGTH)
GAUSS_X, GAUSS_W = np.polynomial.legendre.leggauss(4)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def floor_probe():
    # The existing three-DOF toy's second tangent is uncoupled and zero.
    # K=[[2,1],[1,2]], f=(-4,-1), compression q>0, n=2 max(q,0).
    active = {"t": Q(0), "q": Q(-1, 2), "n": Q(0), "T": Q(-7, 2)}
    released = {"t": Q(-15, 7), "q": Q(2, 7), "n": Q(4, 7), "T": Q(0)}
    offset = {"t": Q(-2), "q": Q(1, 4), "n": Q(1, 2), "T": Q(-1, 4)}
    for row in (active, released, offset):
        assert 2 * row["t"] + row["q"] + row["T"] == -4
        assert row["t"] + 2 * row["q"] + row["n"] == -1
    assert active["q"] < 0 and released["q"] > 0
    assert offset["q"] > 0 and offset["n"] == 2 * offset["q"]
    branches = []
    for restrained in (False, True):
        for normal_closed in (False, True):
            a = Q(4 if normal_closed else 2)
            if restrained:
                t, q = Q(0), -1/a
            else:
                determinant = 2*a-1
                t, q = (-4*a+1)/determinant, 2/determinant
            tangent = -4-2*t-q if restrained else Q(0)
            normal = 2*q if normal_closed else Q(0)
            assert 2*t+q+tangent == -4
            assert t+2*q+normal == -1
            sector = (q > 0) if normal_closed else (q <= 0)
            gate = restrained == (q > 0)
            branches.append({"tangent_restrained": restrained, "normal_closed_sector": normal_closed,
                             "t_mm": str(t), "q_mm": str(q), "tangent_reaction_N": str(tangent),
                             "sector_consistent": sector, "gate_consistent": gate,
                             "admissible": sector and gate})
    no_admissible_branch = not any(row["admissible"] for row in branches)
    assert no_admissible_branch
    stiffness_rows = []
    for k in (Q(0), Q(1), Q(2), Q(10), Q(1000)):
        q = (2 - k) / (7 + 4 * k)
        t = (-15) / (7 + 4 * k)
        assert 2 * t + q + k * t == -4
        assert t + 4 * q == -1
        stiffness_rows.append({"tangent_stiffness_N_per_mm": str(k), "assumed_closed_q_mm": str(q), "strictly_compressed": q > 0})
    return {
        "fixed_zero_reference_active": {k: str(v) for k, v in active.items()},
        "released_tangent_branch": {k: str(v) for k, v in released.items()},
        "fixed_zero_reference_has_no_admissible_branch": no_admissible_branch,
        "all_mask_and_normal_sector_enumeration": branches,
        "different_reference_example": {k: str(v) for k, v in offset.items()},
        "example_reference_mm": "-2",
        "reference_is_a_changed_history_scenario_not_a_fix": True,
        "example_does_not_establish_a_reachable_load_history": True,
        "finite_closed_tangent_stiffness_probes": stiffness_rows,
        "stiffer_tangent_does_not_generally_resolve_the_gate": True,
        "full_frame_existence_decided": False,
    }


def beam_matrix(h):
    return np.array([[12, 6*h, -12, 6*h], [6*h, 4*h*h, -6*h, 2*h*h],
                     [-12, -6*h, 12, -6*h], [6*h, 2*h*h, -6*h, 4*h*h]]) / h**3


def shapes(t, h):
    return np.array([1-3*t*t+2*t**3, h*(t-2*t*t+t**3), 3*t*t-2*t**3, h*(-t*t+t**3)])


def beam_oracles():
    k = beam_matrix(1.0)
    assert np.max(np.abs(k @ np.array([1, 0, 1, 0]))) == 0
    assert np.max(np.abs(k @ np.array([0, 1, 1, 1]))) == 0
    u = np.linalg.solve(k[2:, 2:], np.array([1.0, 0.0]))
    assert np.allclose(u, [1/3, 1/2], rtol=0, atol=1e-14)
    couple = np.linalg.solve(k[2:, 2:], np.array([0.0, 1.0]))
    assert np.allclose(couple, [1/2, 1], rtol=0, atol=1e-14)
    assert np.allclose(np.linalg.solve(k[2:, 2:], np.array([-1.0, 0.0])), -u, rtol=0, atol=1e-14)
    assert np.allclose(k, k.T, rtol=0, atol=0)
    return {"rigid_translation_and_rotation_energy_zero": True,
            "unit_cantilever_tip_deflection": float(u[0]),
            "unit_cantilever_tip_rotation": float(u[1]),
            "unit_couple_tip_deflection": float(couple[0]),
            "unit_couple_tip_rotation": float(couple[1]),
            "force_sign_reversal_passed": True, "passed": True}


def assemble(beta, divisions, edges=EDGES):
    centers = (edges[:-1]+edges[1:])/2
    nodes = np.concatenate([np.linspace(edges[j], edges[j+1], divisions+1)[:-1] for j in range(3)] + [np.array([1.0])])
    beam_dofs = 2 * len(nodes)
    size = beam_dofs + 6
    k = np.zeros((size, size))
    samples = []
    for e, (left, right) in enumerate(zip(nodes[:-1], nodes[1:])):
        h = right-left
        owner = int(np.searchsorted(edges[1:], (left+right)/2, side="right"))
        ids = np.array([2*e, 2*e+1, 2*e+2, 2*e+3, beam_dofs+2*owner, beam_dofs+2*owner+1])
        k[np.ix_(ids[:4], ids[:4])] += beam_matrix(h)
        for point, weight in zip(GAUSS_X, GAUSS_W):
            t = (point+1)/2
            x = left+h*t
            b = np.r_[shapes(t, h), -1.0, -(x-centers[owner])]
            w = h*weight/2
            k[np.ix_(ids, ids)] += beta*w*np.outer(b, b)
            samples.append((x, w, ids, b, owner))
    assert np.allclose(k, k.T, rtol=0, atol=1e-10)
    return nodes, beam_dofs, k, samples


def foundation_oracles():
    flank_rows = []
    for gap in (0.0, 0.575):
        for delta in (-1.0, -0.575, -0.1, 0.0, 0.1, 0.575, 1.0):
            plus, minus = max(delta-gap, 0.0), max(-delta-gap, 0.0)
            resultant = -plus+minus
            assert plus*minus == 0
            if gap == 0:
                assert resultant == -delta
            else:
                assert np.isclose(resultant, -np.sign(delta)*max(abs(delta)-gap, 0.0))
            flank_rows.append({"gap_mm": gap, "relative_displacement_mm": delta,
                               "bolt_line_reaction_for_unit_k": resultant})
    edges = np.linspace(0, 1, 4)
    nodes, beam_dofs, k, samples = assemble(100, 16, edges)
    f = np.zeros(beam_dofs+6)
    # Three equal receivers, mirrored equal outer loads; opposite middle load.
    f[beam_dofs:] = [-1, -1/6, 2, 0, -1, 1/6]
    u = np.zeros_like(f)
    u[2:] = np.linalg.solve(k[2:, 2:], f[2:])
    assert np.max(np.abs(k@u-f)) < 1e-7
    fields = np.array([b@u[ids] for _, _, ids, b, _ in samples])
    assert np.max(np.abs(fields-fields[::-1])) < 1e-9
    translation = np.zeros_like(u)
    rotation = np.zeros_like(u)
    translation[:beam_dofs:2] = 1
    translation[beam_dofs::2] = 1
    rotation[:beam_dofs:2] = nodes
    rotation[1:beam_dofs:2] = 1
    rotation[beam_dofs::2] = (edges[:-1]+edges[1:])/2
    rotation[beam_dofs+1::2] = 1
    changed = u+17*translation-3*rotation
    transformed_fields = np.array([b@changed[ids] for _, _, ids, b, _ in samples])
    assert np.max(np.abs(transformed_fields-fields)) < 1e-12
    # Two transverse planes share the declared isotropic operator. Rotate a
    # non-collinear load pair by 90 degrees and solve independently.
    other = np.zeros_like(f)
    other[beam_dofs:] = [-2, -2/6, 1.5, -2.5/6, 0.5, -0.5/6]
    rhs = np.column_stack([f, other])
    turn = np.array([[0.0, -1.0], [1.0, 0.0]])
    solved = np.linalg.solve(k[2:, 2:], rhs[2:])
    rotated = np.linalg.solve(k[2:, 2:], rhs[2:]@turn.T)
    assert np.allclose(rotated, solved@turn.T, rtol=0, atol=1e-12)
    return {"paired_unilateral_flank_sign_and_gap_rows": flank_rows,
            "equal_receiver_symmetric_transfer_passed": True,
            "common_rigid_translation_rotation_invariance_passed": True,
            "ninety_degree_transverse_rotation_passed": True,
            "gauge_reactions_zero_within_1e_minus_7_N": True,
            "nonzero_gap_not_used_in_case_diagnostic": True, "passed": True}


def loads_from_bolt(bolt, beam_dofs):
    f = np.zeros((beam_dofs+6, 2))
    expected = np.zeros((3, 2, 2))  # owner / force-or-first-moment / Y,Z
    tie = next(a for a in bolt["actions"] if a["role"] == "physical_bolt_outer_seat_tension")
    origin = tie["first_point_global_xyz_mm"][0]
    for a in bolt["actions"]:
        if a["role"] != "candidate_bolt_lateral_plane":
            continue
        assert abs(a["force_on_first_xyz_n"][0]) < 1e-8
        for side in ("first", "second"):
            j = MEMBERS.index(a[side])
            x = (a[side+"_point_global_xyz_mm"][0]-origin) / LENGTH
            assert min(abs(x-EDGES[1]), abs(x-EDGES[2])) < 1e-10
            force = np.array(a["force_on_"+side+"_xyz_n"][1:])
            expected[j, 0] += force
            expected[j, 1] += (x-CENTERS[j])*force
    assert np.max(np.abs(np.sum(expected[:, 0], axis=0))) < 1e-8
    assert np.max(np.abs(np.sum(expected[:, 1]+CENTERS[:, None]*expected[:, 0], axis=0))) < 1e-8
    # Source connector actions are desired forces ON wood. External forces
    # balance those reactions; they are applied once to the rigid wood DOFs.
    for j in range(3):
        f[beam_dofs+2*j:beam_dofs+2*j+2] = -expected[j]
    return f, expected


def solve_bolt(bolt, beta, divisions):
    nodes, beam_dofs, k, samples = assemble(beta, divisions)
    f, expected = loads_from_bolt(bolt, beam_dofs)
    u = np.zeros_like(f)
    # These two DOFs per plane fix coordinate gauge, not an end support.
    u[2:] = np.linalg.solve(k[2:, 2:], f[2:])
    residual = k @ u-f
    scale = max(1.0, float(np.max(np.abs(f))))
    assert np.max(np.abs(residual)) < scale*1e-7
    reactions = np.zeros_like(expected)
    fields = []
    for x, weight, ids, b, owner in samples:
        wood_line_force = beta*(b @ u[ids])
        reactions[owner, 0] += weight*wood_line_force
        reactions[owner, 1] += weight*(x-CENTERS[owner])*wood_line_force
        fields.append((x, weight, wood_line_force))
    assert np.allclose(reactions, expected, rtol=1e-7, atol=scale*1e-7)
    # At a node-cut, integration over preceding elements is exact for the
    # cubic foundation field. Internal moments below are magnitudes/signs
    # under this diagnostic convention, not stresses or strength bounds.
    def cut(x):
        v = sum((w*q for s, w, q in fields if s < x), start=np.zeros(2))
        m = LENGTH*sum((w*(x-s)*q for s, w, q in fields if s < x), start=np.zeros(2))
        return v, m
    tip_v, tip_m = cut(1.0)
    assert np.linalg.norm(tip_v) < scale*1e-7
    assert np.linalg.norm(tip_m) < scale*LENGTH*1e-7
    v, m = cut(MIDDLE_CUT)
    # The cut is a mesh node because divisions is even within the continuous
    # middle foundation. There is no change of owner/law at that station.
    assert min(abs(nodes-MIDDLE_CUT)) < 1e-14
    moments = [np.linalg.norm(cut(float(x))[1]) for x in nodes]
    # q above is the bolt force ON wood; bolt receives -q. The following
    # vectors are the internal force/couple exerted on the left cut face.
    return {"middle_cut_internal_force_on_left_YZ_N": v.tolist(),
            "middle_cut_internal_couple_on_left_My_Mz_Nmm": [float(m[1]), float(-m[0])],
            "middle_cut_shear_magnitude_N": float(np.linalg.norm(v)),
            "middle_cut_bending_magnitude_Nmm": float(np.linalg.norm(m)),
            "sampled_peak_bending_magnitude_Nmm": float(max(moments)),
            "gauge_reaction_max_N": float(np.max(np.abs(residual[:2]))),
            "integrated_member_wrench_error_N": float(np.max(np.abs(reactions-expected))),
            "free_end_force_residual_N": float(np.linalg.norm(tip_v)),
            "free_end_moment_residual_Nmm": float(np.linalg.norm(tip_m))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = {}
    cases = {}
    for relative, expected_hash in METHOD_SOURCES.items():
        path = BASE / relative
        observed = digest(path)
        assert observed == expected_hash, f"method source changed: {path}"
        sources[str(path.relative_to(ROOT))] = observed
    fixture = json.loads((BASE / "current-springa-ideal-stick-branch-cycle-method-attempt01/fixture-spec.json").read_text())
    assert fixture["structure"]["stiffness_matrix_N_per_mm"] == [[2, 0, 1], [0, 1, 0], [1, 0, 2]]
    assert fixture["load_N"] == [-4, 0, -1]
    assert fixture["normal_support"]["stiffness_N_per_mm"] == 2
    for case, (relative, expected_hash) in REPORTS.items():
        path = BASE / relative
        observed = digest(path)
        assert observed == expected_hash, f"source changed: {path}"
        report = json.loads(path.read_text())
        assert report["case_id"] == case
        assert report["candidate"] == "compact-floor-flush-wood-joints-development"
        assert report["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1"
        assert report["actual_case_demand_usable_for_conditional_joint_checks"] is True
        increment = report["increments"][-1]
        assert increment["load_factor"] == 1
        assert increment["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
        sources[str(path.relative_to(ROOT))] = observed
        cases[case] = increment["primary_physical_bolt_groups"]["BG003"]["bolts"]
    rows = []
    for case, bolts in cases.items():
        for bolt in bolts:
            for beta in (1.0, 100.0, 10000.0):
                coarse = solve_bolt(bolt, beta, 16)
                fine = solve_bolt(bolt, beta, 32)
                error = abs(coarse["sampled_peak_bending_magnitude_Nmm"]-fine["sampled_peak_bending_magnitude_Nmm"])/max(fine["sampled_peak_bending_magnitude_Nmm"], 1.0)
                assert error < 0.01, (case, beta, error)
                cut_error = max(abs(coarse[key]-fine[key])/max(fine[key], 1.0) for key in ("middle_cut_shear_magnitude_N", "middle_cut_bending_magnitude_Nmm"))
                assert cut_error < 0.01, (case, beta, cut_error)
                signed_cut_error = max(float(np.linalg.norm(np.array(coarse[key])-fine[key]))/max(float(np.linalg.norm(fine[key])), 1.0)
                                       for key in ("middle_cut_internal_force_on_left_YZ_N", "middle_cut_internal_couple_on_left_My_Mz_Nmm"))
                assert signed_cut_error < 0.01, (case, beta, signed_cut_error)
                rows.append({"case": case, "axis": bolt["axis_id"], "beta": beta,
                             "coarse_fine_peak_difference_fraction": error,
                             "coarse_fine_middle_cut_difference_fraction": cut_error,
                             "coarse_fine_signed_middle_cut_difference_fraction": signed_cut_error, **fine})
    out = {"status": "PASS_SMALL_MODEL_DIAGNOSTICS_ONLY", "source_sha256": sources,
           "producer_sha256": digest(Path(__file__)), "floor": floor_probe(),
           "beam_oracles": beam_oracles(), "foundation_oracles": foundation_oracles(),
           "bg003": {"bearing_lengths_mm": LENGTHS.tolist(), "L_mm": LENGTH,
                     "middle_cut_from_spine_outboard_face_mm": MIDDLE_CUT*LENGTH,
                     "middle_cut_from_spine_middle_interface_mm": 44.45,
                     "beta_definition": "k_line * L**4 / EI; no physical material calibration",
                     "foundation": "uniform equal isotropic linear opposing-flank law, zero radial gap",
                     "three_rigid_receivers_and_one_continuous_bolt": True,
                     "middle_receiver_has_no_artificial_seam_or_hinge": True,
                     "displacements_are_normalized_not_physical": True,
                     "mesh_divisions_per_receiver": [16, 32], "rows": rows},
           "joint_accepted": False, "capacity_calculated": False, "native_solve_run": False,
           "geometry_changed": False, "full_frame_floor_solution_established": False}
    output = json.dumps(out, indent=2, sort_keys=True, allow_nan=False)+"\n"
    target = HERE / "diagnostics.json"
    if args.verify:
        assert target.read_text() == output
        print("PASS_BYTE_IDENTICAL_SMALL_MODEL_DIAGNOSTICS")
    else:
        target.write_text(output)
        print(out["status"], len(rows), "conditional bolt scenarios")


if __name__ == "__main__":
    main()
