#!/usr/bin/env python3
"""Prepare/replay a batch-law adapter; finite BG003 cases are explicit opt-in."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
INPUT_DIR = BASE / "current-bg003-compatible-elastic-method-inputs-attempt01"
ROTATED_DIR = BASE / "current-bg003-rotated-foundation-diagnostic-attempt01"
RADIAL_DIR = BASE / "current-bg003-radial-clearance-diagnostic-attempt01"
POINT_DIR = BASE / "current-bg003-anisotropic-clearance-point-law-fixture-attempt01"
INPUT_PATH = INPUT_DIR / "inputs.json"
CASE_ID, AXIS_ID = "a12-rear", "knee_outer_left_side_1"
MEMBERS = ["knee_outer_left_spine", "base_side_left", "knee_outer_left_inner_frame_block"]
DENSITIES = [350.0, 550.0]
GAPS = [0.0, 0.575]
DIVISIONS = [16, 32]
OUT_BATCH = HERE / "batch-point-oracle.json"
OUT_FINITE = HERE / "finite-proxy-results.json"
EXPECTED_PYTHON, EXPECTED_NUMPY = "3.12.3", "2.5.2"
MAX_BRACKET_DOUBLINGS, MAX_BISECTIONS = 64, 120

PINNED_SOURCES = {
    INPUT_DIR / "inputs.json": "008d9b1d790d7994e0d72d6002baa479f82bb80143e936f6d328f334fdcd37d9",
    INPUT_DIR / "prepare_inputs.py": "f7f45c9b01ec792449f7feff077fb58720b07fb8a4ac8000bb6c573b87538a96",
    INPUT_DIR / "SHA256SUMS": "544e1b3fb3875e26a09a4224d1742e9e9222b26b284b68db356e9c7a2551ae7c",
    ROTATED_DIR / "run_diagnostic.py": "4a5d3a785aac34905608f4255af4f9075e7a910e32e1acc6e0058c20d8ef063b",
    ROTATED_DIR / "diagnostics.json": "4299919a3d3bfa8ef56589e8741ca62f3e88cb7b6077d46053ac3ba06af12918",
    ROTATED_DIR / "README.md": "3de0bf9642ca9f8aefacfbc41a71000088c203792666a2ff14aa10a2e1e550ab",
    RADIAL_DIR / "run_diagnostic.py": "65147beb92edda20137d2fd962594bb1d04a62f0593f0ab0beb2f12850057b2f",
    RADIAL_DIR / "diagnostics.json": "2a6ee00883ab242ddd5f6c144e07b618aa58a604a007fb24edeebeae5461fc77",
    RADIAL_DIR / "README.md": "2816523a6c718f6bedbe12fc6fe188b3140fe21284db03afb8cf954cc256bfc4",
    POINT_DIR / "verify_point_law.py": "b1a4c8d3ec50caa0f39a6c91123a0b876a7ac062f550e300deea7141f1b1765c",
    POINT_DIR / "point-law-fixture.json": "e89dd094f2f22ee187b574aa36ce8926ea5185334078dd677831a980b9d0be1e",
    POINT_DIR / "README.md": "ea3c9247d3c3ab508111e166daeed4f09df5ee20ccf6915281fa0605159ae075",
    POINT_DIR / "SHA256SUMS": "2c4b2cef1d6b05a4a72073860a6cff7ff4889b2f659e3e2b0459274d1a012023",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def runtime_pin() -> dict:
    py, nv = platform.python_version(), np.__version__
    assert py == EXPECTED_PYTHON, f"Python pin mismatch: {py}"
    assert nv == EXPECTED_NUMPY, f"NumPy pin mismatch: {nv}"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    return {"python": py, "numpy": nv, "other_runtime_dependencies": [],
            "environment": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}}


def load_module(name: str, path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins() -> dict[str, str]:
    actual = {}
    for path, expected in PINNED_SOURCES.items():
        got = sha256(path)
        assert got == expected, f"source pin mismatch: {path}"
        actual[str(path.relative_to(ROOT))] = got
    inputs = json.loads(INPUT_PATH.read_text())
    for key in ("three_member_geometry", "prior_continuous_dowel_method_candidate",
                "prior_constructed_bearing_profile_result"):
        pin = inputs["source_pins"][key]
        path = ROOT / pin["path"]
        got = sha256(path)
        assert got == pin["sha256"], f"input dependency pin mismatch: {path}"
        actual[str(path.relative_to(ROOT))] = got
    pin = inputs["source_pins"]["case_reports"][CASE_ID]
    path = ROOT / pin["path"]
    got = sha256(path)
    assert got == pin["sha256"], "A12 source report changed"
    actual[str(path.relative_to(ROOT))] = got
    return dict(sorted(actual.items()))


def source_setup(inputs: dict) -> dict:
    assert inputs["status"] == "INPUT_REGISTER_AND_METHOD_FEASIBILITY_ONLY_NO_BG003_ELASTIC_SOLUTION"
    geo = inputs["geometry_and_available_conditional_scenarios"]
    published = inputs["published_elastic_embedment_inputs_non_adopted"]
    radial = json.loads((RADIAL_DIR / "diagnostics.json").read_text())
    rotated = json.loads((ROTATED_DIR / "diagnostics.json").read_text())
    assert radial["status"] == "PASS_BOUNDED_RADIAL_GAP_DIAGNOSTIC_ONLY"
    assert rotated["status"] == "PASS_SYNTHETIC_ROTATED_FOUNDATION_DIAGNOSTIC_ONLY"
    assert radial["source_case"]["case_id"] == CASE_ID and radial["source_case"]["axis_id"] == AXIS_ID
    assert radial["model"]["receiver_order_head_to_nut"] == MEMBERS
    assert radial["model"]["receiver_lengths_mm"] == [38.1, 88.9, 88.9]
    assert radial["model"]["mesh_divisions_per_receiver"] == DIVISIONS
    assert abs(radial["physical_and_conditional_parameters"]["radial_clearance_mm"] - GAPS[1]) < 1e-12

    d = float(geo["diameter_mm"])
    line_k, frames = {}, {}
    for density in DENSITIES:
        i = DENSITIES.index(density)
        kp = 0.1374 * density - 12.9
        kt = 0.0922 * density - 18.20
        assert abs(kp - published["resulting_moduli_N_per_mm3"]["parallel"][i]) < 1e-10
        assert abs(kt - published["resulting_moduli_N_per_mm3"]["perpendicular"][i]) < 1e-10
        eig_line = np.array([d * kt, d * kp])
        mats, grain = {}, {}
        for member in MEMBERS:
            epar = np.asarray(geo["proposed_grain_vectors_global_xyz"][member], float)[1:3]
            epar /= np.linalg.norm(epar)
            if member == "base_side_left":
                eperp = np.array([epar[1], -epar[0]])
            else:
                assert np.allclose(epar, [0.0, 1.0], atol=1e-12)
                eperp = np.array([1.0, 0.0])
            basis = np.column_stack((eperp, epar))
            mats[member] = basis @ np.diag(eig_line) @ basis.T
            grain[member] = {
                "e_parallel_global_YZ": epar.tolist(),
                "e_perpendicular_global_YZ": eperp.tolist(),
                "parallel_angle_from_global_positive_Z_toward_positive_Y_deg":
                    math.degrees(math.atan2(float(epar[0]), float(epar[1]))),
            }
        line_k[str(int(density))] = {
            "kf_parallel_N_per_mm3": kp, "kf_perpendicular_N_per_mm3": kt,
            "K_line_by_member_N_per_mm2": {m: mats[m].tolist() for m in MEMBERS},
        }
        frames[str(int(density))] = grain

    pin = inputs["source_pins"]["case_reports"][CASE_ID]
    report = json.loads((ROOT / pin["path"]).read_text())
    assert report["case_id"] == CASE_ID
    assert report["actual_case_demand_usable_for_conditional_joint_checks"] is True
    assert len(report["increments"]) == 7
    full = report["increments"][-1]
    assert full["load_factor"] == 1.0
    assert full["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
    raw = next(x for x in full["primary_physical_bolt_groups"]["BG003"]["bolts"]
               if x["axis_id"] == AXIS_ID)
    packed_case = next(x for x in inputs["cases"] if x["case_id"] == CASE_ID)
    assert packed_case["report_status"] == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY"
    packed = next(x for x in packed_case["increments"][-1]["BG003_bolts"] if x["axis_id"] == AXIS_ID)
    assert packed_case["increments"][-1]["load_factor"] == 1.0
    return {
        "inputs": inputs, "geometry": geo, "source_report": report, "raw_bolt": raw,
        "packed_bolt": packed, "line_stiffness": line_k, "grain_frames": frames,
        "diameter_mm": d,
        "radial": load_module("pinned_bg003_radial_solver", RADIAL_DIR / "run_diagnostic.py"),
        "scalar": load_module("pinned_bg003_point_scalar", POINT_DIR / "verify_point_law.py"),
    }


def batch_point_law(delta: np.ndarray, eigs: np.ndarray, bases: np.ndarray, gap: float) -> dict:
    """Evaluate a batch of SPD 2x2 laws in precomputed eigenbases."""
    delta, eigs, bases = np.asarray(delta, float), np.asarray(eigs, float), np.asarray(bases, float)
    n = len(delta)
    assert delta.shape == (n, 2) and eigs.shape == (n, 2) and bases.shape == (n, 2, 2)
    assert gap >= 0.0 and np.isfinite(gap)
    assert np.all(np.isfinite(delta)) and np.all(np.isfinite(eigs)) and np.all(eigs > 0.0)
    dl = np.einsum("nji,nj->ni", bases, delta)
    rho = np.linalg.norm(delta, axis=1)
    energy = np.zeros(n)
    pl = np.zeros((n, 2))
    vl = dl.copy()
    tl = np.zeros((n, 2, 2))
    lam_all = np.zeros(n)
    doublings_all = np.zeros(n, dtype=int)
    branches = np.full(n, "inside_or_at_gap_open", dtype=object)

    if gap == 0.0:
        pl = eigs * dl
        energy = 0.5 * np.sum(dl * pl, axis=1)
        tl[:, 0, 0], tl[:, 1, 1] = eigs[:, 0], eigs[:, 1]
        branches[:] = "zero_gap_linear"
        vl[:] = 0.0
    else:
        ids = np.flatnonzero(rho > gap)
        branches[ids] = "outside_gap_engaged"
        if len(ids):
            k, d = eigs[ids], dl[ids]
            lo = np.zeros(len(ids))
            hi = np.max(k, axis=1) * (rho[ids] / gap - 1.0)
            assert np.all(np.isfinite(hi)) and np.all(hi > 0.0)

            def v_at(lam):
                return (k / (k + lam[:, None])) * d

            norm_hi = np.linalg.norm(v_at(hi), axis=1)
            assert np.all(np.isfinite(norm_hi))
            pending = norm_hi > gap
            for _ in range(MAX_BRACKET_DOUBLINGS):
                if not np.any(pending):
                    break
                hi[pending] *= 2.0
                doublings_all[ids[pending]] += 1
                assert np.all(np.isfinite(hi))
                norm_hi[pending] = np.linalg.norm(v_at(hi)[pending], axis=1)
                assert np.all(np.isfinite(norm_hi[pending]))
                pending = norm_hi > gap
            assert not np.any(pending), "lambda upper-bracket expansion budget exhausted"

            for _ in range(MAX_BISECTIONS):
                mid = 0.5 * (lo + hi)
                distinct = (mid != lo) & (mid != hi)
                if not np.any(distinct):
                    break
                norm_mid = np.linalg.norm(v_at(mid), axis=1)
                greater = norm_mid > gap
                lo = np.where(greater & distinct, mid, lo)
                hi = np.where((~greater) & distinct, mid, hi)
            lam = 0.5 * (lo + hi)
            v = v_at(lam)
            pl[ids] = lam[:, None] * v
            vl[ids] = v
            lam_all[ids] = lam
            energy[ids] = 0.5 * np.sum(k * (d - v) ** 2, axis=1)
            md = 1.0 / (k + lam[:, None])
            b = k * md * v
            den = np.sum(v * v * md, axis=1)
            assert np.all(np.isfinite(den)) and np.all(den > 0.0)
            tl[ids, 0, 0] = lam * k[:, 0] * md[:, 0] + b[:, 0] ** 2 / den
            tl[ids, 1, 1] = lam * k[:, 1] * md[:, 1] + b[:, 1] ** 2 / den
            cross = b[:, 0] * b[:, 1] / den
            tl[ids, 0, 1] = cross
            tl[ids, 1, 0] = cross

    p = np.einsum("nij,nj->ni", bases, pl)
    v = np.einsum("nij,nj->ni", bases, vl)
    tangent = np.einsum("nik,nkl,njl->nij", bases, tl, bases)
    assert np.all(np.isfinite(energy)) and np.all(np.isfinite(p)) and np.all(np.isfinite(tangent))
    assert np.max(np.abs(tangent - tangent.swapaxes(1, 2))) < 2e-9
    return {"energy_Nmm": energy, "p_N": p, "v_mm": v,
            "tangent_N_per_mm": 0.5 * (tangent + tangent.swapaxes(1, 2)),
            "lambda_N_per_mm": lam_all, "branch": branches,
            "bracket_doublings": doublings_all, "bisection_limit": MAX_BISECTIONS}


def verify_batch_law(scalar) -> dict:
    gap = 0.575
    km = np.array([[300.0, 150.0], [150.0, 100.0]])
    pm = np.array([3.0, 4.0])
    vm = gap * pm / np.linalg.norm(pm)
    dm = vm + np.linalg.solve(km, pm)
    ki, pi = 100.0 * np.eye(2), np.array([3.0, 4.0])
    di = (gap + np.linalg.norm(pi) / 100.0) * pi / np.linalg.norm(pi)
    a40 = math.radians(40.0)
    r40 = np.array([[math.cos(a40), -math.sin(a40)], [math.sin(a40), math.cos(a40)]])
    kr, dz = r40 @ np.diag([14.07, 35.19]) @ r40.T, np.array([0.4, -0.3])
    qr = np.array([[math.cos(0.731), -math.sin(0.731)],
                   [math.sin(0.731), math.cos(0.731)]])
    dn = (gap + 1e-5) * np.array([0.6, -0.8])
    cases = [
        ("isotropic_radial", di, ki, gap),
        ("anisotropic_mixed_force", dm, km, gap),
        ("zero_interior_force", np.array([0.1, -0.2]), km, gap),
        ("rotated_linear_zero_gap", dz, kr, 0.0),
        ("exact_engagement_boundary", np.array([gap, 0.0]), km, gap),
        ("near_engagement_outside", dn, km, gap),
        ("rigidly_rotated_mixed", qr @ dm, qr @ km @ qr.T, gap),
    ]
    results, maxerr = [], {k: 0.0 for k in ("energy_Nmm", "p_N", "v_mm", "tangent_N_per_mm")}
    for label, delta, K, g in cases:
        eig, basis = np.linalg.eigh(K)
        batch = batch_point_law(np.asarray([delta]), eig[None, :], basis[None, :, :], g)
        ref = scalar.evaluate(np.asarray(delta), np.asarray(K), g)
        err = {
            "energy_Nmm": abs(float(batch["energy_Nmm"][0]) - ref["energy_Nmm"]),
            "p_N": float(np.max(np.abs(batch["p_N"][0] - ref["p_N"]))),
            "v_mm": float(np.max(np.abs(batch["v_mm"][0] - ref["v_mm"]))),
            "tangent_N_per_mm": float(np.max(np.abs(batch["tangent_N_per_mm"][0] - ref["tangent_N_per_mm"]))),
        }
        for k, value in err.items():
            maxerr[k] = max(maxerr[k], value)
        assert batch["branch"][0] == ref["branch"]
        assert max(err.values()) < 2e-7
        results.append({"case": label, "branch": str(batch["branch"][0]),
                        "max_abs_error_vs_frozen_scalar": err})

    # One-point weight homogeneity is the exact guard against applying w twice.
    w = 3.7
    eig, basis = np.linalg.eigh(km)
    base = batch_point_law(dm[None, :], eig[None, :], basis[None, :, :], gap)
    weighted = batch_point_law(dm[None, :], (w * eig)[None, :], basis[None, :, :], gap)
    homogeneity = {
        "weight": w,
        "energy_ratio": float(weighted["energy_Nmm"][0] / base["energy_Nmm"][0]),
        "force_ratio": float(np.linalg.norm(weighted["p_N"][0]) / np.linalg.norm(base["p_N"][0])),
        "tangent_ratio": float(np.linalg.norm(weighted["tangent_N_per_mm"][0]) /
                               np.linalg.norm(base["tangent_N_per_mm"][0])),
        "same_minimizer_max_abs_mm": float(np.max(np.abs(weighted["v_mm"][0] - base["v_mm"][0]))),
        "lambda_ratio": float(weighted["lambda_N_per_mm"][0] / base["lambda_N_per_mm"][0]),
    }
    assert all(abs(homogeneity[k] - w) < 2e-12 for k in
               ("energy_ratio", "force_ratio", "tangent_ratio", "lambda_ratio"))
    assert homogeneity["same_minimizer_max_abs_mm"] < 2e-13

    mixed = batch_point_law(
        np.asarray([di, dm, [0.1, -0.2], [gap, 0.0], dn]),
        np.asarray([np.linalg.eigvalsh(ki), np.linalg.eigvalsh(km),
                    np.linalg.eigvalsh(km), np.linalg.eigvalsh(km), np.linalg.eigvalsh(km)]),
        np.asarray([np.linalg.eigh(ki)[1], np.linalg.eigh(km)[1],
                    np.linalg.eigh(km)[1], np.linalg.eigh(km)[1], np.linalg.eigh(km)[1]]), gap)
    assert list(mixed["branch"]) == [
        "outside_gap_engaged", "outside_gap_engaged", "inside_or_at_gap_open",
        "inside_or_at_gap_open", "outside_gap_engaged",
    ]
    return {
        "status": "PASS_BATCH_POINT_LAW_VS_FROZEN_SCALAR_ORACLE",
        "cases": results,
        "case_count": len(results),
        "maximum_absolute_errors": maxerr,
        "mixed_branch_batch": list(mixed["branch"]),
        "weight_homogeneity_no_double_weight_oracle": homogeneity,
        "tolerance": "branch exact; absolute scalar/batch differences <2e-7 in the named units",
        "scalar_oracle_sha256": sha256(POINT_DIR / "verify_point_law.py"),
    }


def verify_receiver_moment_closure_conversion() -> dict:
    """Check radial stored [Mz,-My] closure becomes reported [My,Mz]."""
    raw_radial_order = np.array([17.0, -23.0])  # [delta Mz, -delta My]
    reported_my_mz = np.array([-raw_radial_order[1], raw_radial_order[0]])
    expected_my_mz = np.array([23.0, 17.0])
    assert np.array_equal(reported_my_mz, expected_my_mz)
    return {
        "status": "PASS_SYNTHETIC_NONZERO_MOMENT_AXIS_ORDER_ORACLE",
        "raw_radial_closure_order_Mz_minus_My_Nmm": raw_radial_order.tolist(),
        "reported_global_closure_order_My_Mz_Nmm": reported_my_mz.tolist(),
        "expected_global_closure_order_My_Mz_Nmm": expected_my_mz.tolist(),
        "conversion": "[delta_Mz,-delta_My] -> [-raw[1],raw[0]] = [delta_My,delta_Mz]",
    }


def produce_batch() -> dict:
    runtime = runtime_pin()
    source_sha = verify_pins()
    setup = source_setup(json.loads(INPUT_PATH.read_text()))
    oracle = verify_batch_law(setup["scalar"])
    source_sha[str(Path(__file__).relative_to(ROOT))] = sha256(Path(__file__))
    return {
        "schema": "bg003_anisotropic_clearance_finite_adapter_batch_oracle/v1",
        "status": "PASS_BATCH_ORACLE_ADAPTER_READY_NO_FINITE_CASES_RUN",
        "source_sha256": dict(sorted(source_sha.items())),
        "runtime": runtime,
        "source_case": {
            "case_id": CASE_ID, "axis_id": AXIS_ID, "load_factor": 1.0,
            "source_report_sha256": source_sha[str(setup["inputs"]["source_pins"]["case_reports"][CASE_ID]["path"])],
            "three_source_wrenches_loaded_once_to_rigid_receivers": True,
            "source_plane_actions_reapplied_to_beam": False,
        },
        "frozen_solver_reuse": {
            "source_script_sha256": sha256(RADIAL_DIR / "run_diagnostic.py"),
            "mesh": "unchanged radial source assemble_base; 4-point Gauss EB beam, 16/32 divisions per receiver",
            "load_mapping": "unchanged radial source load_vector and receiver order",
            "continuation_and_closure": "unchanged radial source solve_gap_case budgets, gauge, free ends, residual checks, and signed 16/32 gate",
            "receiver_order_head_to_nut": MEMBERS,
            "lengths_mm": [38.1, 88.9, 88.9],
            "E_MPa_scenario": 190000.0, "I_mm4": 79.81137627308144,
            "EI_Nmm2": 15164161.491885472, "physical_ends_free": True,
        },
        "stiffness_scenarios": {
            "density_kg_per_m3_non_adopted": DENSITIES,
            "line_modulus": "kf_parallel=0.1374*rho-12.9; kf_perpendicular=0.0922*rho-18.20 N/mm^3",
            "line_K": "diameter*kf rotated to declared receiver grain frame, N/mm^2",
            "point_K": "quadrature_weight*line_K, N/mm; returned point force, energy, tangent assembled directly once",
            "gap_mm": GAPS,
            "grain_frames": setup["grain_frames"],
            "K_line_by_density": setup["line_stiffness"],
        },
        "batch_oracle": oracle,
        "receiver_moment_closure_coordinate_oracle": verify_receiver_moment_closure_conversion(),
        "exact_finite_recipe": {
            "scenario_count": 8,
            "cartesian_product": {"case": CASE_ID, "axis": AXIS_ID, "density": DENSITIES,
                                  "gap_mm": GAPS, "mesh_divisions_per_receiver": DIVISIONS},
            "independent_zero_gap_oracle": "separately assemble beam plus weighted rotated K_line matrix at each density/mesh and compare signed g=0 actions, peak, and closure",
            "refinement": "signed middle Y/Z force vector, signed middle My/Mz couple vector, and sampled peak couple magnitude 16/32 differences each <1%, with frozen radial denominator floor",
            "outputs": [
                "signed middle beam shear/couple",
                "signed peak nodal couple and associated shear with location",
                "per-receiver sampled line resultant/d pressure in MPa with location, signed Y/Z vector and grain-force angle",
                "signed receiver force and first-moment closure residual vectors",
                "frozen radial gauge/free-end/convergence results",
            ],
            "proposed_serial_run_caps": {
                "BLAS_threads": 1, "per_scenario_CPU_seconds": 120,
                "whole_suite_CPU_seconds": 900, "wall_seconds": 1200,
                "peak_RSS_bytes": 2147483648,
                "enforcement": "parent may wrap serial execution with timeout/prlimit; stop on any cap or solver budget failure",
            },
        },
        "finite_scenarios_executed": False,
        "native_solve_executed": False,
        "calibration_strength_or_joint_acceptance": False,
    }


def install_adapter(radial, density, line_k):
    original_assemble, original_evaluate = radial.assemble_base, radial.evaluate
    state = {"context": None, "last": None}

    def assemble(divisions):
        nodes, beam_dofs, beam_k, samples = original_assemble(divisions)
        weights = np.asarray([s[1] for s in samples])
        owners = np.asarray([s[4] for s in samples], dtype=int)
        values = np.asarray([np.linalg.eigvalsh(k) for k in line_k])
        bases = np.asarray([np.linalg.eigh(k)[1] for k in line_k])
        state["context"] = {
            "nodes": nodes, "beam_dofs": beam_dofs, "beam_stiffness": beam_k,
            "samples": samples, "weights": weights, "owners": owners,
            "point_eigs": weights[:, None] * values[owners], "bases": bases[owners],
            "density": density,
        }
        state["last"] = None
        return nodes, beam_dofs, beam_k, samples

    def evaluate(q, loads, beam_stiffness, samples, k_argument, gap):
        ctx = state["context"]
        assert ctx is not None and abs(float(k_argument) - density) < 1e-12
        tangent = beam_stiffness.copy()
        residual = beam_stiffness @ q - loads
        energy = 0.5 * float(q @ beam_stiffness @ q) - float(loads @ q)
        rel = np.asarray([s[3] @ q[s[2]] for s in samples])
        law = batch_point_law(rel, ctx["point_eigs"], ctx["bases"], float(gap))
        energy += float(np.sum(law["energy_Nmm"]))
        fields = []
        for i, (x, weight, cols, relative_map, owner) in enumerate(samples):
            p = law["p_N"][i]
            residual[cols] += relative_map.T @ p
            tangent[np.ix_(cols, cols)] += relative_map.T @ law["tangent_N_per_mm"][i] @ relative_map
            fields.append((x, weight, p / weight, owner, rel[i]))
        assert np.allclose(tangent, tangent.T, rtol=0, atol=1e-7)
        state["last"] = {"q": q.copy(), "gap": gap, "loads": loads.copy()}
        return energy, residual, tangent, fields

    radial.assemble_base, radial.evaluate = assemble, evaluate
    return state, original_assemble, original_evaluate


def output_metrics(radial, setup, ctx, q, loads, expected, gap, line_k):
    samples = ctx["samples"]
    weights = ctx["weights"]
    owners = ctx["owners"]
    relative = np.asarray([s[3] @ q[s[2]] for s in samples])
    vals = np.asarray([np.linalg.eigvalsh(k) for k in line_k])
    bases0 = np.asarray([np.linalg.eigh(k)[1] for k in line_k])
    law = batch_point_law(relative, weights[:, None] * vals[owners], bases0[owners], gap)

    reaction = np.zeros_like(expected)
    active = np.zeros(3)
    cuts = []
    maxima = {}
    diameter = setup["diameter_mm"]
    grains = setup["grain_frames"][str(int(ctx["density"]))]
    for i, (x, w, cols, rmap, owner) in enumerate(samples):
        force_line = law["p_N"][i] / w
        if np.linalg.norm(relative[i]) > gap:
            active[owner] += w
        reaction[owner, 0] += w * force_line
        reaction[owner, 1] += w * (x - radial.CENTERS_MM[owner]) * force_line
        cuts.append((x, w, force_line))
        pressure = force_line / diameter
        frame = grains[MEMBERS[owner]]
        epar, eperp = np.asarray(frame["e_parallel_global_YZ"]), np.asarray(frame["e_perpendicular_global_YZ"])
        action_angle = math.degrees(math.atan2(float(force_line[0]), float(force_line[1])))
        grain_angle = frame["parallel_angle_from_global_positive_Z_toward_positive_Y_deg"]
        relative_angle = (action_angle - grain_angle + 180.0) % 360.0 - 180.0
        candidate = {
            "x_mm_from_underhead": float(x),
            "line_resultant_YZ_N_per_mm": force_line.tolist(),
            "signed_p_over_d_YZ_MPa": pressure.tolist(),
            "sampled_p_over_d_resultant_MPa": float(np.linalg.norm(pressure)),
            "parallel_component_MPa": float(pressure @ epar),
            "perpendicular_component_MPa": float(pressure @ eperp),
            "grain_angle_from_global_positive_Z_toward_positive_Y_deg": grain_angle,
            "line_force_angle_from_global_positive_Z_toward_positive_Y_deg": action_angle,
            "signed_force_to_parallel_grain_angle_deg": relative_angle,
        }
        old = maxima.get(MEMBERS[owner])
        if old is None or candidate["sampled_p_over_d_resultant_MPa"] > old["sampled_p_over_d_resultant_MPa"]:
            maxima[MEMBERS[owner]] = candidate

    def cut(x):
        shear = sum((w * p for s, w, p in cuts if s < x), start=np.zeros(2))
        arms = sum((w * (x - s) * p for s, w, p in cuts if s < x), start=np.zeros(2))
        return shear, np.array([arms[1], -arms[0]])

    middle_shear, middle_couple = cut(radial.MIDDLE_CUT_MM)
    node_actions = [(float(x), *cut(float(x))) for x in ctx["nodes"]]
    peak_x, peak_shear, peak_couple = max(node_actions, key=lambda r: float(np.linalg.norm(r[2])))
    closure = reaction - expected

    full_residual = ctx["beam_stiffness"] @ q - loads
    for i, (x, w, cols, rmap, owner) in enumerate(samples):
        full_residual[cols] += rmap.T @ law["p_N"][i]
    endshear, endcouple = cut(radial.LENGTH_MM)
    force_scale = max(1.0, float(np.max(np.abs(loads[0::4]))), float(np.max(np.abs(loads[2::4]))))
    moment_scale = max(1.0, float(np.max(np.abs(loads[1::4]))), float(np.max(np.abs(loads[3::4]))))
    dof_scale = np.tile([force_scale, moment_scale, force_scale, moment_scale], len(full_residual) // 4)
    return {
        "active_lengths_by_receiver_mm": active.tolist(),
        "signed_middle_cut_internal_force_on_left_YZ_N": middle_shear.tolist(),
        "signed_middle_cut_internal_couple_on_left_My_Mz_Nmm": middle_couple.tolist(),
        "sampled_peak_couple": {
            "x_mm_from_underhead": peak_x,
            "signed_internal_force_on_left_YZ_N": peak_shear.tolist(),
            "signed_internal_couple_on_left_My_Mz_Nmm": peak_couple.tolist(),
            "magnitude_Nmm": float(np.linalg.norm(peak_couple)),
            "sampling": "beam nodes only; not a continuous extremum or physical bound",
        },
        "sampled_line_bearing_resultant_pressure_by_receiver": maxima,
        "signed_receiver_force_and_first_moment_closure_residuals": {
            MEMBERS[j]: {"force_YZ_N": closure[j, 0].tolist(),
                         "moment_My_Mz_Nmm": [-float(closure[j, 1, 1]),
                                               float(closure[j, 1, 0])]} for j in range(3)
        },
        "receiver_closure_max_abs_N_or_Nmm": float(np.max(np.abs(closure))),
        "free_end_closure": {
            "force_YZ_N": endshear.tolist(), "couple_My_Mz_Nmm": endcouple.tolist(),
            "force_norm_N": float(np.linalg.norm(endshear)),
            "couple_norm_Nmm": float(np.linalg.norm(endcouple)),
        },
        "gauge_reaction": {
            "translation_YZ_N": full_residual[[0, 2]].tolist(),
            "slope_couples_Nmm": full_residual[[1, 3]].tolist(),
            "max_abs_translation_N": float(np.max(np.abs(full_residual[[0, 2]]))),
            "max_abs_slope_couple_Nmm": float(np.max(np.abs(full_residual[[1, 3]]))),
        },
        "scaled_free_dof_residual": float(np.max(np.abs(full_residual[4:] / dof_scale[4:]))),
    }


def linear_oracle(radial, setup, density, divisions, line_k):
    nodes, bdofs, beam_k, samples = radial.assemble_base(divisions)
    loads, expected = radial.load_vector(setup["packed_bolt"], bdofs)
    A = beam_k.copy()
    for x, w, cols, rmap, owner in samples:
        A[np.ix_(cols, cols)] += rmap.T @ (w * line_k[owner]) @ rmap
    assert np.allclose(A, A.T, rtol=0, atol=1e-7)
    free = np.arange(4, len(loads))
    q = np.zeros_like(loads)
    q[free] = np.linalg.solve(A[np.ix_(free, free)], loads[free])
    ctx = {"nodes": nodes, "beam_dofs": bdofs, "beam_stiffness": beam_k,
           "samples": samples, "weights": np.asarray([s[1] for s in samples]),
           "owners": np.asarray([s[4] for s in samples]), "density": density}
    metrics = output_metrics(radial, setup, ctx, q, loads, expected, 0.0, line_k)
    metrics["independent_linear_assembly"] = {
        "free_equilibrium_max_abs": float(np.max(np.abs((A @ q - loads)[free]))),
        "matrix_symmetry_max_abs": float(np.max(np.abs(A - A.T))),
        "matrix_assembly": "beam stiffness plus each point's quadrature_weight*K_line grain-frame block",
    }
    return {"q": q, "loads": loads, "expected": expected, "ctx": ctx,
            "metrics": metrics, "matrix": A}


def run_finite(setup, source_sha):
    assert OUT_BATCH.read_text() == render(produce_batch()), "batch oracle absent/stale; replay it first"
    radial = setup["radial"]
    linear = {}
    rows = []
    for density in DENSITIES:
        mats = setup["line_stiffness"][str(int(density))]["K_line_by_member_N_per_mm2"]
        line_k = np.asarray([mats[m] for m in MEMBERS], float)
        for div in DIVISIONS:
            linear[(density, div)] = linear_oracle(radial, setup, density, div, line_k)
        state, old_assemble, old_evaluate = install_adapter(radial, density, line_k)
        for gap in GAPS:
            for div in DIVISIONS:
                row = radial.solve_gap_case(setup["packed_bolt"], density, gap, div)
                ctx, captured = state["context"], state["last"]
                row.pop("k_line_N_per_mm2", None)
                row.update({"density_kg_per_m3_non_adopted": density,
                            "gap_mm": gap, "mesh_divisions_per_receiver": div,
                            "K_line_by_receiver_N_per_mm2": {m: line_k[i].tolist() for i, m in enumerate(MEMBERS)}})
                if row["status"] == "CONVERGED":
                    assert captured is not None
                    _, expected = radial.load_vector(setup["packed_bolt"], ctx["beam_dofs"])
                    metrics = output_metrics(radial, setup, ctx, captured["q"], captured["loads"],
                                             expected, gap, line_k)
                    row.update(metrics)
                    if gap == 0.0:
                        oracle = linear[(density, div)]
                        ref = oracle["metrics"]
                        diffs = {}
                        for key in ("signed_middle_cut_internal_force_on_left_YZ_N",
                                    "signed_middle_cut_internal_couple_on_left_My_Mz_Nmm"):
                            a, b = np.asarray(row[key]), np.asarray(ref[key])
                            suffix = "shear" if "force" in key else "couple"
                            diffs[f"signed_middle_{suffix}_fraction"] = float(
                                np.linalg.norm(a - b) / max(float(np.linalg.norm(b)), 1.0)
                            )
                        peak_a = row["sampled_peak_couple"]["magnitude_Nmm"]
                        peak_b = ref["sampled_peak_couple"]["magnitude_Nmm"]
                        diffs["sampled_peak_couple_fraction"] = abs(peak_a - peak_b) / max(peak_b, 1.0)
                        closure_diff = 0.0
                        for member in MEMBERS:
                            for field in ("force_YZ_N", "moment_My_Mz_Nmm"):
                                closure_diff = max(closure_diff, float(np.max(np.abs(
                                    np.asarray(row["signed_receiver_force_and_first_moment_closure_residuals"][member][field]) -
                                    np.asarray(ref["signed_receiver_force_and_first_moment_closure_residuals"][member][field])
                                ))))
                        diffs["receiver_force_first_moment_closure_max_abs_difference"] = closure_diff
                        action_keys = ("signed_middle_shear_fraction",
                                       "signed_middle_couple_fraction",
                                       "sampled_peak_couple_fraction")
                        assert all(key in diffs and diffs[key] < 2e-7 for key in action_keys)
                        assert diffs["receiver_force_first_moment_closure_max_abs_difference"] < 2e-7
                        row["separate_linear_zero_gap_oracle"] = {
                            "status": "PASS", "relative_signed_action_differences": diffs,
                            "assembly_audit": oracle["metrics"]["independent_linear_assembly"],
                        }
                rows.append(row)
        radial.assemble_base, radial.evaluate = old_assemble, old_evaluate

    refinement = []
    for density in DENSITIES:
        for gap in GAPS:
            c = next(r for r in rows if r["density_kg_per_m3_non_adopted"] == density and r["gap_mm"] == gap and r["mesh_divisions_per_receiver"] == 16)
            f = next(r for r in rows if r["density_kg_per_m3_non_adopted"] == density and r["gap_mm"] == gap and r["mesh_divisions_per_receiver"] == 32)
            if c["status"] != "CONVERGED" or f["status"] != "CONVERGED":
                refinement.append({"density_kg_per_m3_non_adopted": density, "gap_mm": gap,
                                   "status": "NOT_ASSESSABLE_SOLVE_FAILURE"})
                continue
            shear = float(np.linalg.norm(np.asarray(c["signed_middle_cut_internal_force_on_left_YZ_N"]) -
                                         np.asarray(f["signed_middle_cut_internal_force_on_left_YZ_N"])) /
                          max(float(np.linalg.norm(f["signed_middle_cut_internal_force_on_left_YZ_N"])), 1.0))
            couple = float(np.linalg.norm(np.asarray(c["signed_middle_cut_internal_couple_on_left_My_Mz_Nmm"]) -
                                          np.asarray(f["signed_middle_cut_internal_couple_on_left_My_Mz_Nmm"])) /
                           max(float(np.linalg.norm(f["signed_middle_cut_internal_couple_on_left_My_Mz_Nmm"])), 1.0))
            peak = abs(c["sampled_peak_couple"]["magnitude_Nmm"] - f["sampled_peak_couple"]["magnitude_Nmm"]) / max(f["sampled_peak_couple"]["magnitude_Nmm"], 1.0)
            refinement.append({"density_kg_per_m3_non_adopted": density, "gap_mm": gap,
                               "signed_middle_shear_difference_fraction_16_to_32": shear,
                               "signed_middle_couple_difference_fraction_16_to_32": couple,
                               "sampled_peak_couple_difference_fraction_16_to_32": peak,
                               "under_1_percent_all": max(shear, couple, peak) < 0.01})
    all_converged = all(r["status"] == "CONVERGED" for r in rows)
    all_refined = all(r.get("under_1_percent_all", False) for r in refinement)
    return {
        "schema": "bg003_anisotropic_clearance_finite_proxy_results/v1",
        "status": "PASS_BOUNDED_PROXY_ONLY" if all_converged and all_refined else "BOUNDED_FAILURE_OR_REFINEMENT_LIMIT",
        "source_sha256": dict(sorted(source_sha.items())), "adapter_sha256": sha256(Path(__file__)),
        "batch_oracle_sha256": sha256(OUT_BATCH), "scenario_count": len(rows),
        "scenarios": rows, "signed_refinement": refinement,
        "limits": [
            "The rotated anisotropic circular-clearance law is a constitutive hypothesis, not measured or calibrated for BG003.",
            "Densities and stiffnesses are non-adopted literature sensitivities, not member-specific values or bounds.",
            "Sampled pressure and nodal peak actions are discrete samples, not continuous maxima or physical bounds.",
            "No axial tie, preload, washer, strength/resistance, friction, splitting, group interaction, shared-timber compatibility, or whole-joint acceptance is calculated.",
        ],
        "finite_joint_cases_executed": True, "native_solve_executed": False, "joint_accepted": False,
    }


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-batch", action="store_true")
    group.add_argument("--verify-batch", action="store_true")
    group.add_argument("--run-finite", action="store_true")
    group.add_argument("--verify-finite", action="store_true")
    args = parser.parse_args()
    if args.write_batch or args.verify_batch:
        text = render(produce_batch())
        if args.write_batch:
            OUT_BATCH.write_text(text)
            print("WROTE_BATCH_ORACLE_ONLY; FINITE_CASES_NOT_RUN")
        else:
            assert OUT_BATCH.read_text() == text, "batch oracle differs from pinned replay"
            print("PASS_BATCH_ORACLE_ADAPTER; FINITE_CASES_NOT_RUN")
        return
    source_sha = verify_pins()
    setup = source_setup(json.loads(INPUT_PATH.read_text()))
    result = run_finite(setup, source_sha)
    text = render(result)
    if args.run_finite:
        assert not OUT_FINITE.exists(), "finite result already exists; do not overwrite"
        OUT_FINITE.write_text(text)
        print(result["status"], "eight finite proxy scenarios; no native solve")
    else:
        assert OUT_FINITE.read_text() == text, "finite result differs from deterministic replay"
        print("PASS_FINITE_PROXY_REPLAY", len(result["scenarios"]))


if __name__ == "__main__":
    main()
