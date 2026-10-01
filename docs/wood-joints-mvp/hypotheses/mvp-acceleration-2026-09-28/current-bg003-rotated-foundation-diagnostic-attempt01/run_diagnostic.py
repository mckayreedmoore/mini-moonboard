#!/usr/bin/env python3
"""Small synthetic BG003 vector-foundation diagnostic; not a strength check."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
OWNER = ROOT / "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30"
INPUT_DIR = BASE / "current-bg003-compatible-elastic-method-inputs-attempt01"
INPUT_PATH = INPUT_DIR / "inputs.json"
INPUT_SHA256 = "008d9b1d790d7994e0d72d6002baa479f82bb80143e936f6d328f334fdcd37d9"
INPUT_PRODUCER_SHA256 = "f7f45c9b01ec792449f7feff077fb58720b07fb8a4ac8000bb6c573b87538a96"
INPUT_MANIFEST_SHA256 = "544e1b3fb3875e26a09a4224d1742e9e9222b26b284b68db356e9c7a2551ae7c"
OWNER_PINS = {
    "diagnose.py": "8ab5615b9e2bc80ac56f3d5002bc7053981a3ad4387a9a39e2088273f073be59",
    "diagnostics.json": "174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98",
    "README.md": "b9cfe28dfed2205da3f2375f7563e2d8839bd0588dba85bdf7e3777ab01c9250",
}
RECEIVER_ORDER = [
    "knee_outer_left_spine",
    "base_side_left",
    "knee_outer_left_inner_frame_block",
]
AXIS_ORDER = ["knee_outer_left_side_1", "knee_outer_left_side_2"]
EXPECTED_CASES = ["a12-rear", "a1-rear", "k12-rear"]
EXPECTED_REPORT_STATUSES = {
    "a12-rear": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    "a1-rear": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    "k12-rear": "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
}
LENGTHS_MM = np.array([38.1, 88.9, 88.9], dtype=float)
LENGTH_MM = float(np.sum(LENGTHS_MM))
EDGES = np.r_[0.0, np.cumsum(LENGTHS_MM)] / LENGTH_MM
CENTERS = (EDGES[:-1] + EDGES[1:]) / 2
MIDDLE_CUT = (38.1 + 44.45) / LENGTH_MM
GAUSS_X, GAUSS_W = np.polynomial.legendre.leggauss(4)
SQRT2 = math.sqrt(2.0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam_matrix(h: float) -> np.ndarray:
    return np.array(
        [
            [12, 6 * h, -12, 6 * h],
            [6 * h, 4 * h * h, -6 * h, 2 * h * h],
            [-12, -6 * h, 12, -6 * h],
            [6 * h, 2 * h * h, -6 * h, 4 * h * h],
        ],
        dtype=float,
    ) / h**3


def shapes(t: float, h: float) -> np.ndarray:
    return np.array(
        [1 - 3 * t * t + 2 * t**3, h * (t - 2 * t * t + t**3),
         3 * t * t - 2 * t**3, h * (-t * t + t**3)],
        dtype=float,
    )


def rotation_foundation_matrix(beta: float, orientation: str) -> np.ndarray:
    """Dimensionless K_line L^4/EI; beta is based on lower k_perp eigenvalue."""
    if orientation == "outer-grain-Z":
        # Plane order is (global Y, global Z); Z is parallel to grain.
        return beta * np.diag([1.0, 2.0])
    if orientation == "middle-grain-40deg-from-Z":
        angle = math.radians(40.0)
        e_parallel = np.array([math.sin(angle), math.cos(angle)])
        e_perpendicular = np.array([math.cos(angle), -math.sin(angle)])
        return beta * (
            np.outer(e_perpendicular, e_perpendicular)
            + 2.0 * np.outer(e_parallel, e_parallel)
        )
    raise ValueError(orientation)


def isotropic_foundation_matrix(beta: float) -> np.ndarray:
    return beta * np.eye(2)


def assemble_receivers(
    beta: float, divisions: int, anisotropic: bool
) -> tuple[np.ndarray, int, np.ndarray, list[tuple[float, float, np.ndarray, int]]]:
    """Assemble one continuous two-plane EB dowel and three rigid receivers.

    Beam DOFs per node are (wY, dwY/dxi, wZ, dwZ/dxi). Each receiver's four
    DOFs are (uY, duY/dxi, uZ, duZ/dxi) about its interval midpoint.
    """
    nodes = np.concatenate(
        [
            np.linspace(EDGES[j], EDGES[j + 1], divisions + 1)[:-1]
            for j in range(3)
        ]
        + [np.array([1.0])]
    )
    beam_dofs = 4 * len(nodes)
    size = beam_dofs + 12
    matrix = np.zeros((size, size), dtype=float)
    samples: list[tuple[float, float, np.ndarray, int]] = []

    for element, (left, right) in enumerate(zip(nodes[:-1], nodes[1:])):
        h = float(right - left)
        middle = (left + right) / 2.0
        owner = int(np.searchsorted(EDGES[1:], middle, side="right"))
        node_y_ids = np.array(
            [4 * element, 4 * element + 1, 4 * (element + 1), 4 * (element + 1) + 1]
        )
        node_z_ids = node_y_ids + 2
        matrix[np.ix_(node_y_ids, node_y_ids)] += beam_matrix(h)
        matrix[np.ix_(node_z_ids, node_z_ids)] += beam_matrix(h)
        body = beam_dofs + 4 * owner
        foundation = (
            rotation_foundation_matrix(
                beta,
                "middle-grain-40deg-from-Z" if owner == 1 else "outer-grain-Z",
            )
            if anisotropic
            else isotropic_foundation_matrix(beta)
        )
        for point, weight in zip(GAUSS_X, GAUSS_W):
            t = (float(point) + 1.0) / 2.0
            x = left + h * t
            w = h * float(weight) / 2.0
            shape = shapes(t, h)
            relative = np.zeros((2, size), dtype=float)
            relative[0, node_y_ids] = shape
            relative[0, [body, body + 1]] = [-1.0, -(x - CENTERS[owner])]
            relative[1, node_z_ids] = shape
            relative[1, [body + 2, body + 3]] = [-1.0, -(x - CENTERS[owner])]
            matrix += w * relative.T @ foundation @ relative
            samples.append((float(x), w, relative, owner))

    assert np.allclose(matrix, matrix.T, rtol=0, atol=1e-10)
    return nodes, beam_dofs, matrix, samples


def source_loads(bolt: dict, beam_dofs: int) -> tuple[np.ndarray, np.ndarray]:
    """Apply balancing source wood wrenches once, at receiver DOFs only."""
    force_first_moment = np.zeros((3, 2, 2), dtype=float)
    for j, name in enumerate(RECEIVER_ORDER):
        wrench = bolt["derived_member_wrenches_at_receiver_interval_midpoints"][name]
        force = np.array(wrench["force_xyz_n"], dtype=float)
        moment = np.array(wrench["moment_xyz_nmm"], dtype=float)
        # Project only the lateral Y/Z wrench. The physical X-axis tie is a
        # separately retained demand and is outside this beam-foundation solve.
        assert abs(moment[0]) < 1e-7
        # The work-conjugate slope actions are Mz/L for Y and -My/L for Z.
        force_first_moment[j, 0, :] = [force[1], force[2]]
        force_first_moment[j, 1, :] = [moment[2] / LENGTH_MM, -moment[1] / LENGTH_MM]

    assert np.max(np.abs(np.sum(force_first_moment[:, 0, :], axis=0))) < 1e-8
    assert np.max(
        np.abs(
            np.sum(
                force_first_moment[:, 1, :]
                + CENTERS[:, None] * force_first_moment[:, 0, :],
                axis=0,
            )
        )
    ) < 1e-8

    loads = np.zeros(beam_dofs + 12, dtype=float)
    for j in range(3):
        body = beam_dofs + 4 * j
        # Structural connector actions on wood are balanced by these external
        # receiver loads. No source wrench is additionally put on the beam.
        loads[[body, body + 1, body + 2, body + 3]] = [
            -force_first_moment[j, 0, 0],
            -force_first_moment[j, 1, 0],
            -force_first_moment[j, 0, 1],
            -force_first_moment[j, 1, 1],
        ]
    return loads, force_first_moment


def solve_case(bolt: dict, beta: float, divisions: int, anisotropic: bool) -> dict:
    nodes, beam_dofs, stiffness, samples = assemble_receivers(beta, divisions, anisotropic)
    loads, expected = source_loads(bolt, beam_dofs)
    result = np.zeros_like(loads)
    # Fix the first node's two translations and two slopes as a pure common
    # Y/Z rigid-motion gauge. The physical beam ends remain free.
    result[4:] = np.linalg.solve(stiffness[4:, 4:], loads[4:])
    residual = stiffness @ result - loads
    force_scale = max(1.0, float(np.max(np.abs(loads))))
    assert np.max(np.abs(residual)) < force_scale * 2e-7

    receiver_reactions = np.zeros_like(expected)
    fields: list[tuple[float, float, np.ndarray]] = []
    for x, weight, relative, owner in samples:
        foundation = (
            rotation_foundation_matrix(
                beta,
                "middle-grain-40deg-from-Z" if owner == 1 else "outer-grain-Z",
            )
            if anisotropic
            else isotropic_foundation_matrix(beta)
        )
        bolt_action_on_wood = foundation @ (relative @ result)
        receiver_reactions[owner, 0] += weight * bolt_action_on_wood
        receiver_reactions[owner, 1] += weight * (x - CENTERS[owner]) * bolt_action_on_wood
        fields.append((x, weight, bolt_action_on_wood))
    receiver_error = float(np.max(np.abs(receiver_reactions - expected)))
    assert receiver_error < force_scale * 2e-7

    def cut(x: float) -> tuple[np.ndarray, np.ndarray]:
        shear = sum(
            (weight * action for s, weight, action in fields if s < x),
            start=np.zeros(2),
        )
        moment_arms = LENGTH_MM * sum(
            (weight * (x - s) * action for s, weight, action in fields if s < x),
            start=np.zeros(2),
        )
        return shear, moment_arms

    assert np.min(np.abs(nodes - MIDDLE_CUT)) < 1e-14
    end_shear, end_moments = cut(1.0)
    end_closure_force = float(np.linalg.norm(end_shear))
    end_closure_moment = float(np.linalg.norm(end_moments))
    assert end_closure_force < force_scale * 2e-7
    assert end_closure_moment < force_scale * LENGTH_MM * 2e-7
    cut_shear, cut_m = cut(MIDDLE_CUT)
    cut_couple_on_left = np.array([cut_m[1], -cut_m[0]])
    sampled_moments = [np.linalg.norm(cut(float(x))[1]) for x in nodes]

    # Four gauge rows carry no constraint reaction for a self-equilibrated
    # source wrench set.
    gauge_reaction = float(np.max(np.abs(residual[:4])))
    assert gauge_reaction < force_scale * 2e-7
    return {
        "middle_cut_internal_force_on_left_YZ_N": cut_shear.tolist(),
        "middle_cut_internal_couple_on_left_My_Mz_Nmm": cut_couple_on_left.tolist(),
        "middle_cut_shear_magnitude_N": float(np.linalg.norm(cut_shear)),
        "middle_cut_bending_magnitude_Nmm": float(np.linalg.norm(cut_couple_on_left)),
        "sampled_peak_bending_magnitude_Nmm": float(max(sampled_moments)),
        "gauge_reaction_max_N": gauge_reaction,
        "integrated_member_wrench_error_N_or_normalized_moment_N": receiver_error,
        "free_end_force_residual_N": end_closure_force,
        "free_end_moment_residual_Nmm": end_closure_moment,
    }


def known_infinite_beam_fixture() -> dict:
    """FE point-load solve against the exact eigenmode infinite-beam result."""
    ei = 1.0
    k_line = np.array([[2.5, 1.5], [1.5, 2.5]], dtype=float)
    half_length = 20.0
    elements = 160
    nodes = np.linspace(-half_length, half_length, elements + 1)
    size = 4 * len(nodes)
    stiffness = np.zeros((size, size), dtype=float)
    for element, (left, right) in enumerate(zip(nodes[:-1], nodes[1:])):
        h = float(right - left)
        y_ids = np.array([4 * element, 4 * element + 1, 4 * (element + 1), 4 * (element + 1) + 1])
        z_ids = y_ids + 2
        stiffness[np.ix_(y_ids, y_ids)] += ei * beam_matrix(h)
        stiffness[np.ix_(z_ids, z_ids)] += ei * beam_matrix(h)
        for point, weight in zip(GAUSS_X, GAUSS_W):
            shape = shapes((float(point) + 1.0) / 2.0, h)
            b = np.zeros((2, size), dtype=float)
            b[0, y_ids] = shape
            b[1, z_ids] = shape
            stiffness += (h * float(weight) / 2.0) * (b.T @ k_line @ b)
    loads = np.zeros(size, dtype=float)
    center_node = elements // 2
    loads[4 * center_node] = 1.0
    solution = np.linalg.solve(stiffness, loads)
    numerical = np.array([solution[4 * center_node], solution[4 * center_node + 2]])

    # K eigenvalues are 4 and 1; normalized eigenvectors are (1,1) and (1,-1).
    beta_4 = (4.0 / (4.0 * ei)) ** 0.25
    beta_1 = (1.0 / (4.0 * ei)) ** 0.25
    g_4 = 1.0 / (8.0 * ei * beta_4**3)
    g_1 = 1.0 / (8.0 * ei * beta_1**3)
    exact = np.array([(g_4 + g_1) / 2.0, (g_4 - g_1) / 2.0])
    absolute_error = float(np.max(np.abs(numerical - exact)))
    relative_error = absolute_error / float(np.max(np.abs(exact)))
    assert relative_error < 2e-5, (numerical.tolist(), exact.tolist(), relative_error)
    assert numerical[1] < 0.0 and abs(numerical[1]) > 0.1
    return {
        "fixture": "EI=1 N mm^2; infinite-beam point force P=(1,0) N at s=0",
        "K_line_N_per_mm2": k_line.tolist(),
        "finite_element_truncation_mm": [-half_length, half_length],
        "elements": elements,
        "center_node_displacement_YZ_mm": numerical.tolist(),
        "infinite_beam_oracle_center_displacement_YZ_mm": exact.tolist(),
        "maximum_relative_error": relative_error,
        "off_diagonal_coupling_test_passed": bool(numerical[1] < 0.0 and abs(numerical[1]) > 0.1),
        "passed": True,
    }


def compare_fraction(coarse: dict, fine: dict, key: str) -> float:
    c = np.asarray(coarse[key], dtype=float)
    f = np.asarray(fine[key], dtype=float)
    return float(np.linalg.norm(c - f) / max(float(np.linalg.norm(f)), 1.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    input_hash = digest(INPUT_PATH)
    assert input_hash == INPUT_SHA256, f"input packet changed: {input_hash}"
    source_hashes = {str(INPUT_PATH.relative_to(ROOT)): input_hash}
    input_producer = INPUT_DIR / "prepare_inputs.py"
    assert digest(input_producer) == INPUT_PRODUCER_SHA256
    source_hashes[str(input_producer.relative_to(ROOT))] = INPUT_PRODUCER_SHA256
    input_manifest = INPUT_DIR / "SHA256SUMS"
    assert digest(input_manifest) == INPUT_MANIFEST_SHA256
    source_hashes[str(input_manifest.relative_to(ROOT))] = INPUT_MANIFEST_SHA256
    for name, expected in OWNER_PINS.items():
        path = OWNER / name
        actual = digest(path)
        assert actual == expected, f"owner source changed: {path}: {actual} != {expected}"
        source_hashes[str(path.relative_to(ROOT))] = actual
    input_packet = json.loads(INPUT_PATH.read_text())
    for group in ("case_reports",):
        for item in input_packet["source_pins"][group].values():
            path = ROOT / item["path"]
            actual = digest(path)
            assert actual == item["sha256"], f"input report changed: {path}"
            source_hashes[str(path.relative_to(ROOT))] = actual
    for name in ("three_member_geometry", "prior_continuous_dowel_method_candidate",
                 "prior_constructed_bearing_profile_result"):
        item = input_packet["source_pins"][name]
        path = ROOT / item["path"]
        actual = digest(path)
        assert actual == item["sha256"], f"input method/geometry changed: {path}"
        source_hashes[str(path.relative_to(ROOT))] = actual
    owner_output = json.loads((OWNER / "diagnostics.json").read_text())
    assert owner_output["status"] == "PASS_SMALL_MODEL_DIAGNOSTICS_ONLY"
    assert [c["case_id"] for c in input_packet["cases"]] == EXPECTED_CASES

    owner_rows = {
        (row["case"], row["axis"], int(row["beta"])): row
        for row in owner_output["bg003"]["rows"]
    }
    isotropic_rows = []
    rotated_rows = []
    for case in input_packet["cases"]:
        assert case["candidate"] == "compact-floor-flush-wood-joints-development"
        assert case["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1"
        assert case["report_status"] == EXPECTED_REPORT_STATUSES[case["case_id"]]
        assert case["increment_count"] == 7
        full_load = case["increments"][-1]
        assert full_load["load_factor"] == 1.0
        assert full_load["all_five_corner_bodies_raw_and_interval_balance_passed"] is True
        bolts = full_load["BG003_bolts"]
        assert [bolt["axis_id"] for bolt in bolts] == AXIS_ORDER
        for bolt in bolts:
            for beta in (100, 10000):
                coarse_iso = solve_case(bolt, float(beta), 16, anisotropic=False)
                fine_iso = solve_case(bolt, float(beta), 32, anisotropic=False)
                iso_signed_shear = compare_fraction(
                    coarse_iso, fine_iso, "middle_cut_internal_force_on_left_YZ_N"
                )
                iso_signed_moment = compare_fraction(
                    coarse_iso, fine_iso, "middle_cut_internal_couple_on_left_My_Mz_Nmm"
                )
                assert max(iso_signed_shear, iso_signed_moment) < 0.01
                reference = owner_rows[(case["case_id"], bolt["axis_id"], beta)]
                for key in (
                    "middle_cut_internal_force_on_left_YZ_N",
                    "middle_cut_internal_couple_on_left_My_Mz_Nmm",
                    "middle_cut_shear_magnitude_N",
                    "middle_cut_bending_magnitude_Nmm",
                    "sampled_peak_bending_magnitude_Nmm",
                ):
                    actual = np.asarray(fine_iso[key], dtype=float)
                    target = np.asarray(reference[key], dtype=float)
                    error = float(np.linalg.norm(actual - target) / max(float(np.linalg.norm(target)), 1.0))
                    assert error < 2e-7, (case["case_id"], bolt["axis_id"], beta, key, error)
                isotropic_rows.append(
                    {
                        "case": case["case_id"],
                        "axis": bolt["axis_id"],
                        "beta": beta,
                        "owner_fine_mesh_signed_shear_N": reference[
                            "middle_cut_internal_force_on_left_YZ_N"
                        ],
                        "this_vector_operator_signed_shear_N": fine_iso[
                            "middle_cut_internal_force_on_left_YZ_N"
                        ],
                        "owner_fine_mesh_signed_couple_My_Mz_Nmm": reference[
                            "middle_cut_internal_couple_on_left_My_Mz_Nmm"
                        ],
                        "this_vector_operator_signed_couple_My_Mz_Nmm": fine_iso[
                            "middle_cut_internal_couple_on_left_My_Mz_Nmm"
                        ],
                        "mesh16_to_32_signed_shear_difference_fraction": iso_signed_shear,
                        "mesh16_to_32_signed_couple_difference_fraction": iso_signed_moment,
                        "owner_match_max_relative_error": max(
                            float(
                                np.linalg.norm(
                                    np.asarray(fine_iso[key], dtype=float)
                                    - np.asarray(reference[key], dtype=float)
                                )
                                / max(float(np.linalg.norm(np.asarray(reference[key], dtype=float))), 1.0)
                            )
                            for key in (
                                "middle_cut_internal_force_on_left_YZ_N",
                                "middle_cut_internal_couple_on_left_My_Mz_Nmm",
                                "middle_cut_shear_magnitude_N",
                                "middle_cut_bending_magnitude_Nmm",
                                "sampled_peak_bending_magnitude_Nmm",
                            )
                        ),
                    }
                )

                coarse_rot = solve_case(bolt, float(beta), 16, anisotropic=True)
                fine_rot = solve_case(bolt, float(beta), 32, anisotropic=True)
                rot_signed_shear = compare_fraction(
                    coarse_rot, fine_rot, "middle_cut_internal_force_on_left_YZ_N"
                )
                rot_signed_moment = compare_fraction(
                    coarse_rot, fine_rot, "middle_cut_internal_couple_on_left_My_Mz_Nmm"
                )
                peak_error = abs(
                    coarse_rot["sampled_peak_bending_magnitude_Nmm"]
                    - fine_rot["sampled_peak_bending_magnitude_Nmm"]
                ) / max(fine_rot["sampled_peak_bending_magnitude_Nmm"], 1.0)
                assert max(rot_signed_shear, rot_signed_moment, peak_error) < 0.01
                iso_ref = owner_rows[(case["case_id"], bolt["axis_id"], beta)]
                shear_iso = np.asarray(
                    iso_ref["middle_cut_internal_force_on_left_YZ_N"], dtype=float
                )
                moment_iso = np.asarray(
                    iso_ref["middle_cut_internal_couple_on_left_My_Mz_Nmm"], dtype=float
                )
                shear_rot = np.asarray(
                    fine_rot["middle_cut_internal_force_on_left_YZ_N"], dtype=float
                )
                moment_rot = np.asarray(
                    fine_rot["middle_cut_internal_couple_on_left_My_Mz_Nmm"], dtype=float
                )
                rotated_rows.append(
                    {
                        "case": case["case_id"],
                        "axis": bolt["axis_id"],
                        "beta_from_k_perpendicular": beta,
                        "anisotropy_parallel_to_perpendicular_ratio": 2.0,
                        "middle_grain_degrees_from_global_Z": 40.0,
                        "rotated_mesh16_signed_shear_N": coarse_rot[
                            "middle_cut_internal_force_on_left_YZ_N"
                        ],
                        "rotated_mesh32_signed_shear_N": shear_rot.tolist(),
                        "isotropic_signed_shear_N": shear_iso.tolist(),
                        "rotated_minus_isotropic_signed_shear_N": (shear_rot - shear_iso).tolist(),
                        "rotated_mesh16_signed_couple_My_Mz_Nmm": coarse_rot[
                            "middle_cut_internal_couple_on_left_My_Mz_Nmm"
                        ],
                        "rotated_mesh32_signed_couple_My_Mz_Nmm": moment_rot.tolist(),
                        "isotropic_signed_couple_My_Mz_Nmm": moment_iso.tolist(),
                        "rotated_minus_isotropic_signed_couple_My_Mz_Nmm": (
                            moment_rot - moment_iso
                        ).tolist(),
                        "rotated_middle_cut_shear_magnitude_N": fine_rot[
                            "middle_cut_shear_magnitude_N"
                        ],
                        "isotropic_middle_cut_shear_magnitude_N": iso_ref[
                            "middle_cut_shear_magnitude_N"
                        ],
                        "rotated_middle_cut_bending_magnitude_Nmm": fine_rot[
                            "middle_cut_bending_magnitude_Nmm"
                        ],
                        "isotropic_middle_cut_bending_magnitude_Nmm": iso_ref[
                            "middle_cut_bending_magnitude_Nmm"
                        ],
                        "mesh16_to_32_signed_shear_difference_fraction": rot_signed_shear,
                        "mesh16_to_32_signed_couple_difference_fraction": rot_signed_moment,
                        "mesh16_to_32_peak_bending_difference_fraction": peak_error,
                        "receiver_wrench_closure_error_N_or_normalized_moment_N": fine_rot[
                            "integrated_member_wrench_error_N_or_normalized_moment_N"
                        ],
                        "free_end_force_closure_residual_N": fine_rot[
                            "free_end_force_residual_N"
                        ],
                        "free_end_couple_closure_residual_Nmm": fine_rot[
                            "free_end_moment_residual_Nmm"
                        ],
                        "gauge_reaction_max_N": fine_rot["gauge_reaction_max_N"],
                    }
                )

    # β=100 must reproduce the owner's signed isotropic result; all β=100 and
    # 10000 isotropic rows above are also retained as the direct comparison.
    assert len(isotropic_rows) == 12 and len(rotated_rows) == 12
    fixture = known_infinite_beam_fixture()
    rotated_summary = []
    for beta in (100, 10000):
        selected = [r for r in rotated_rows if r["beta_from_k_perpendicular"] == beta]
        max_shear_change = max(
            float(np.linalg.norm(r["rotated_minus_isotropic_signed_shear_N"]))
            / max(float(np.linalg.norm(r["isotropic_signed_shear_N"])), 1.0)
            for r in selected
        )
        max_moment_change = max(
            float(np.linalg.norm(r["rotated_minus_isotropic_signed_couple_My_Mz_Nmm"]))
            / max(float(np.linalg.norm(r["isotropic_signed_couple_My_Mz_Nmm"])), 1.0)
            for r in selected
        )
        rotated_summary.append(
            {
                "beta_from_k_perpendicular": beta,
                "scenarios": len(selected),
                "maximum_relative_signed_middle_cut_shear_change_vs_isotropic": max_shear_change,
                "maximum_relative_signed_middle_cut_couple_change_vs_isotropic": max_moment_change,
            }
        )

    output = {
        "status": "PASS_SYNTHETIC_ROTATED_FOUNDATION_DIAGNOSTIC_ONLY",
        "source_sha256": dict(sorted(source_hashes.items())),
        "producer_sha256": digest(Path(__file__)),
        "operator_oracle": fixture,
        "foundation_definition": {
            "parameter": "beta = k_perpendicular * L^4 / EI; dimensionless",
            "beta_values": [100, 10000],
            "anisotropy_ratio": "k_parallel/k_perpendicular = 2 (synthetic only)",
            "outer_grain_direction": "global +Z; K dimensionless in (Y,Z) axes is beta*diag(1,2)",
            "middle_grain_direction": "synthetic 40 degrees from global +Z toward global +Y",
            "middle_K_dimensionless_YZ": "beta*(e_perp e_perp^T + 2 e_parallel e_parallel^T)",
            "foundation_law": "bilateral linear continuous foundation, no initial clearance/contact transition",
            "normalization": "one continuous circular-beam proxy with EI normalized to 1 and L=215.9 mm",
        },
        "model_scope": {
            "cases": EXPECTED_CASES,
            "full_load_increment_only": True,
            "bolts_per_case": AXIS_ORDER,
            "receiver_order_head_to_nut": RECEIVER_ORDER,
            "receiver_lengths_mm": LENGTHS_MM.tolist(),
            "continuous_middle_receiver_no_seam_or_hinge": True,
            "source_lateral_YZ_forces_and_bending_couples_applied_once_to_receiver_dofs": True,
            "source_axial_X_tie_wrench_excluded_as_separate_action": True,
            "source_wrenches_also_applied_to_beam": False,
            "physical_bolt_ends_free": True,
            "common_rigid_translation_rotation_gauge_pinned": True,
            "gauge_reactions_checked_zero": True,
            "mesh_divisions_per_receiver": [16, 32],
            "actual_0_575_mm_clearance_unmodeled": True,
            "actual_material_foundation_law_unmodeled": True,
            "axial_tie_force_preload_washer_contact_unmodeled": True,
        },
        "isotropic_matches_owner": isotropic_rows,
        "rotated_anisotropic_cases": rotated_rows,
        "coupling_effect_summary": rotated_summary,
        "joint_accepted": False,
        "capacity_calculated": False,
        "native_solve_run": False,
        "gap_response_or_contact_state_resolved": False,
        "full_frame_or_group_behavior_established": False,
    }
    serialized = json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n"
    target = HERE / "diagnostics.json"
    if args.verify:
        assert target.read_text() == serialized
        print("PASS_BYTE_IDENTICAL_ROTATED_FOUNDATION_DIAGNOSTICS")
    else:
        target.write_text(serialized)
        print(output["status"], len(rotated_rows), "rotated cases")


if __name__ == "__main__":
    main()
