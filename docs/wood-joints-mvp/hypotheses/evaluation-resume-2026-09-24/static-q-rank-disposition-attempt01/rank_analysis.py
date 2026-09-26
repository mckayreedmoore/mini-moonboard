#!/usr/bin/env python3
"""Reproduce the current ordinary-patch rigid-kinematic rank disposition.

This is a small NumPy analysis of frozen matrices and a frozen displacement
equation. It does not run CalculiX, regenerate geometry, or infer material
stiffness.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
OUT = Path(__file__).resolve().parent
L = 100.0
RTOL = 1e-10

PATHS = {
    "rigid_mode_matrix": BASE / "ordinary-rigid-preflight-attempt01/rigid-mode-matrix.json",
    "rigid_mode_summary": BASE / "ordinary-rigid-preflight-attempt01/summary.json",
    "actuator": BASE / "ordinary-seating-actuator-attempt03/actuator.json",
    "mesh_report": BASE / "ordinary-patch-mesh-attempt02/mesh/mesh.json",
    "mesh_bundle": BASE / "ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz",
    "classification": BASE / "ordinary-patch-contact-classification-attempt01/classification.json",
    "inventory": BASE / "ordinary-patch-inputs-attempt01/inventory.json",
    "rigid_mode_helper": ROOT / "fea/wood_joint_patch_rigid_modes.py",
    "native_preflight_readme": BASE / "ordinary-native-preflight-attempt04/README.md",
    "native_preflight_execution": BASE / "ordinary-native-preflight-attempt04/execution.json",
    "native_matrix_witness": BASE / "ordinary-matrix-witness-attempt01/audit.json",
    "ordinary_response_method": ROOT / "docs/wood-joints-mvp/ordinary-joint-response-method.md",
    "unit_response_contract": ROOT / "docs/wood-joints-mvp/representative-unit-response-contract.md",
    "current_criteria_coverage": ROOT / "docs/wood-joints-mvp/current-criteria-coverage.md",
    "engagement_applicability": ROOT / "docs/wood-joints-mvp/current-engagement-model-applicability.md",
    "material_scenarios": ROOT / "docs/wood-joints-mvp/current-material-scenarios.md",
    "upstream_attempt_execution": BASE / "dependent-native-upstream-attempt01/execution.json",
    "instrumented_attempt_execution": BASE / "dependent-native-instrumented-attempt01/execution.json",
    "upstream_attempt_outcome": BASE / "dependent-native-upstream-parent-review-attempt01/terminal-outcome.md",
    "accepted_inc1_comparison": BASE / "dependent-residual-native-check-attempt01/comparison-adapter-attempt01/accepted-inc1-comparison.json",
    "tiny_static_q_outcome": BASE / "prescribed-q-native-static-attempt02/terminal-outcome.md",
}

EXPECTED_SHA256 = {
    "rigid_mode_matrix": "de205bd0b94cde0687f2ae8e666866a1cd2b0323050a89b3de4b373d2588f282",
    "rigid_mode_summary": "c500031cd50b07b5f232e27db8c521ab8cc76d2d72883b7605bd80e680c03db1",
    "actuator": "cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7",
    "mesh_report": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "mesh_bundle": "3bd1b28bdbc9c109c6c96183a01e132cbd4c15f86867dca54e0c6ec3a309f4ac",
    "classification": "18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13",
    "inventory": "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3",
    "rigid_mode_helper": "d59d6ae6fb86f981b78e2c4b2e8578c938e1cfafc646d7c011c0187ef3b53647",
    "native_preflight_readme": "0f4a02e23b3b10e2b1e15ade285b4954b8ce18685e3a1f83c56444cfab2640c8",
    "native_preflight_execution": "0ba6907c82486040c09ad60e8f600017c000f0a11ba82239f42f497ccdf0dfab",
    "native_matrix_witness": "ff4b701f4df42b45e8e69c914a7208c822f1673148125755df4a697a34d74413",
    "ordinary_response_method": "57175468e43da005078d0b9e807da3e92c20a7a433fcb1c4a2693493c57c0c0b",
    "unit_response_contract": "edba2e6678edba206e920292770d6bd8f20fc7bb2bfc861cc8d4c0e340a7cb9a",
    "current_criteria_coverage": "ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a",
    "engagement_applicability": "5e5e530b45812519e6c8dc6811bee740cd717b3b8ffe2cba5070f83691645305",
    "material_scenarios": "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    "upstream_attempt_execution": "6cd07953d6756a2e8d1a5ae7b080523ec499bdb759f8504fd7277bec66f77234",
    "instrumented_attempt_execution": "bb103133a63954751e926cde03c2f92299280cbe8d3ae89600da11343eba98a9",
    "upstream_attempt_outcome": "88d76715a01dd4c33efeef6b5e33c1babc6996981cfb88385bde81d339ce28d5",
    "accepted_inc1_comparison": "b1d9750339de6042b3943158d9af981b46ac86ec2aec51b7110267ebf03a93bd",
    "tiny_static_q_outcome": "966555b992e875692bb3a6a7acd67853549309dcfb17cc96126db35316536d6c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def svd_rank_null(
    matrix: np.ndarray, relative_tolerance: float = RTOL
) -> tuple[int, np.ndarray, list[float]]:
    _, singular, right = np.linalg.svd(matrix, full_matrices=True)
    threshold = relative_tolerance * float(singular[0]) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > threshold))
    return rank, right[rank:, :], singular.tolist()


def relative_translation_row(
    ids: list[str],
    index: dict[str, int],
    origins: dict[str, np.ndarray],
    moving: str,
    reference: str,
    point: np.ndarray,
    direction: np.ndarray,
) -> np.ndarray:
    row = np.zeros(len(ids) * 6, dtype=np.float64)
    for body_id, sign in ((moving, 1.0), (reference, -1.0)):
        start = index[body_id] * 6
        row[start : start + 3] = sign * direction
        # The matrix coordinates store rotations as L * omega.
        row[start + 3 : start + 6] = sign * np.cross(
            point - origins[body_id], direction
        ) / L
    return row


def relative_rotation_row(
    ids: list[str], index: dict[str, int], moving: str, reference: str, axis: np.ndarray
) -> np.ndarray:
    row = np.zeros(len(ids) * 6, dtype=np.float64)
    row[index[moving] * 6 + 3 : index[moving] * 6 + 6] = axis / L
    row[index[reference] * 6 + 3 : index[reference] * 6 + 6] = -axis / L
    return row


def read_mesh_nodes(bundle_path: Path) -> dict[int, np.ndarray]:
    with tarfile.open(bundle_path, "r:gz") as bundle:
        raw = bundle.extractfile("mesh/mesh.inp")
        if raw is None:
            raise RuntimeError("mesh/mesh.inp missing from frozen bundle")
        lines = raw.read().decode("ascii").splitlines()
    nodes: dict[int, np.ndarray] = {}
    in_nodes = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("*NODE"):
            in_nodes = True
            continue
        if in_nodes and stripped.startswith("*"):
            in_nodes = False
        if in_nodes and stripped:
            fields = [field.strip() for field in stripped.split(",")]
            if len(fields) >= 4:
                nodes[int(fields[0])] = np.asarray(
                    [float(fields[1]), float(fields[2]), float(fields[3])],
                    dtype=np.float64,
                )
    return nodes


def actuator_rigid_row(
    actuator: dict,
    mesh_report: dict,
    nodes: dict[int, np.ndarray],
    ids: list[str],
    index: dict[str, int],
    origins: dict[str, np.ndarray],
) -> np.ndarray:
    owner = {
        int(node): body_id
        for body_id, body in mesh_report["bodies"].items()
        for node in body["nodes"]
    }
    row = np.zeros(len(ids) * 6, dtype=np.float64)
    terms = actuator["equation"]["physical_terms_before_normalization"]
    if len(terms) != 662:
        raise AssertionError(f"expected 662 physical equation terms, got {len(terms)}")
    for node_id_raw, dof_raw, coefficient_raw in terms:
        node_id = int(node_id_raw)
        dof = int(dof_raw)
        if node_id not in owner or node_id not in nodes:
            raise AssertionError(f"actuator term node {node_id} has no frozen mesh owner/xyz")
        body_id = owner[node_id]
        start = index[body_id] * 6
        basis = np.eye(3, dtype=np.float64)[dof - 1]
        coefficient = float(coefficient_raw)
        row[start : start + 3] += coefficient * basis
        row[start + 3 : start + 6] += (
            coefficient * np.cross(nodes[node_id] - origins[body_id], basis) / L
        )
    return row


def analyze() -> dict:
    actual_sha = {name: sha256(path) for name, path in PATHS.items()}
    if actual_sha != EXPECTED_SHA256:
        differing = {
            name: {"expected": EXPECTED_SHA256[name], "actual": actual_sha[name]}
            for name in EXPECTED_SHA256
            if actual_sha.get(name) != EXPECTED_SHA256[name]
        }
        raise RuntimeError(f"frozen input hash mismatch: {json.dumps(differing, sort_keys=True)}")

    matrix_doc = load_json(PATHS["rigid_mode_matrix"])
    summary = load_json(PATHS["rigid_mode_summary"])
    actuator = load_json(PATHS["actuator"])
    mesh_report = load_json(PATHS["mesh_report"])
    classification = load_json(PATHS["classification"])
    native_matrix_witness = load_json(PATHS["native_matrix_witness"])

    ids = matrix_doc["body_ids_in_coordinate_order"]
    index = {body_id: i for i, body_id in enumerate(ids)}
    origins = {
        body_id: np.asarray(matrix_doc["body_origins_xyz_mm"][body_id], dtype=np.float64)
        for body_id in ids
    }
    base = np.asarray(
        matrix_doc["with_global_gauge"]["dimensionless_constraint_matrix"],
        dtype=np.float64,
    )
    if base.shape != (67, 114):
        raise AssertionError(f"unexpected base matrix shape: {base.shape}")
    if matrix_doc["with_global_gauge"]["rank"] != 62:
        raise AssertionError("frozen parent rank changed")
    if summary["after_six_global_gauges_nullity"] != 52:
        raise AssertionError("frozen parent nullity changed")
    if len(classification["wood_interfaces"]) != 3 or len(classification["hardware_seats"]) != 16:
        raise AssertionError("current representative patch inventory changed")
    if len(mesh_report["bodies"]) != 19:
        raise AssertionError("current rigid-body inventory changed")

    nodes = read_mesh_nodes(PATHS["mesh_bundle"])
    q = actuator_rigid_row(actuator, mesh_report, nodes, ids, index, origins)

    q_interface = actuator["interface_id"]
    q_record = next(row for row in classification["wood_interfaces"] if row["interface_id"] == q_interface)
    q_moving = q_record["first_face"]["mesh_body_id"]
    q_reference = q_record["second_face"]["mesh_body_id"]
    q_datum = np.asarray(actuator["datum_global_xyz_mm"], dtype=np.float64)
    q_direction = np.asarray(actuator["direction_global_xyz"], dtype=np.float64)
    q_analytic = relative_translation_row(
        ids, index, origins, q_moving, q_reference, q_datum, q_direction
    )
    q_scale = float(np.dot(q, q_analytic) / np.dot(q_analytic, q_analytic))
    q_relative_error = float(np.linalg.norm(q - q_scale * q_analytic) / np.linalg.norm(q))
    if abs(q_scale - 1.0) > 1e-10 or q_relative_error > 1e-10:
        raise AssertionError("exact actuator row does not match its analytic rigid-body q")

    rail_interface_id = "base_rail_bottom_right_to_base_principal_center_right"
    rail_interface = next(
        row for row in classification["wood_interfaces"] if row["interface_id"] == rail_interface_id
    )
    rail_body = rail_interface["first_face"]["mesh_body_id"]
    principal_body = rail_interface["second_face"]["mesh_body_id"]
    rail_datum = np.asarray(
        rail_interface["mesh_overlay"]["centroid_global_xyz_mm"], dtype=np.float64
    )
    relative_six: list[np.ndarray] = []
    relative_six_labels: list[str] = []
    global_axes = np.eye(3, dtype=np.float64)
    for axis, label in zip(global_axes, ("X", "Y", "Z"), strict=True):
        relative_six.append(
            relative_translation_row(
                ids,
                index,
                origins,
                rail_body,
                principal_body,
                rail_datum,
                axis,
            )
        )
        relative_six_labels.append(f"relative_translation_{label}")
    for axis, label in zip(global_axes, ("X", "Y", "Z"), strict=True):
        relative_six.append(relative_rotation_row(ids, index, rail_body, principal_body, axis))
        relative_six_labels.append(f"relative_rotation_{label}")
    relative_six_matrix = np.asarray(relative_six)

    cases = {
        "six_global_gauges_only": base,
        "six_global_gauges_plus_single_q": np.vstack((base, q)),
        "six_global_gauges_plus_relative_rail_principal_six": np.vstack(
            (base, relative_six_matrix)
        ),
        "six_global_gauges_plus_relative_six_plus_q": np.vstack(
            (base, relative_six_matrix, q)
        ),
    }
    case_results = {}
    nullspaces = {}
    singular_values_by_case = {}
    for case_id, matrix in cases.items():
        rank, nullspace, singular = svd_rank_null(matrix)
        nullspaces[case_id] = nullspace
        singular_values_by_case[case_id] = singular
        case_results[case_id] = {
            "rows": int(matrix.shape[0]),
            "columns": int(matrix.shape[1]),
            "rank": rank,
            "nullity": int(nullspace.shape[0]),
            "largest_singular_value": float(singular[0]) if singular else 0.0,
            "rank_tolerance_relative": RTOL,
        }

    rank_tolerance_sensitivity = {}
    for relative_tolerance in (1e-9, 1e-10, 1e-11, 1e-12):
        rank_tolerance_sensitivity[f"{relative_tolerance:.0e}"] = {}
        for case_id, singular in singular_values_by_case.items():
            threshold = relative_tolerance * singular[0]
            rank = int(np.count_nonzero(np.asarray(singular) > threshold))
            rank_tolerance_sensitivity[f"{relative_tolerance:.0e}"][case_id] = {
                "rank": rank,
                "nullity": int(114 - rank),
                "smallest_retained_singular_ratio": float(singular[rank - 1] / singular[0]),
                "next_two_singular_ratios": [
                    float(value / singular[0]) for value in singular[rank : rank + 2]
                ],
            }

    q_six_null = nullspaces["six_global_gauges_plus_relative_six_plus_q"]

    spin_vectors = []
    spin_body_ids = []
    for spin in summary["verified_component_axis_spins"]:
        vector = np.zeros(114, dtype=np.float64)
        start = index[spin["body_id"]] * 6
        axis = np.asarray(spin["axis"], dtype=np.float64)
        vector[start + 3 : start + 6] = axis / np.linalg.norm(axis)
        spin_vectors.append(vector)
        spin_body_ids.append(spin["body_id"])
    spin_matrix = np.asarray(spin_vectors)
    augmented = cases["six_global_gauges_plus_relative_six_plus_q"]
    spin_residual_max = float(np.max(np.abs(augmented @ spin_matrix.T)))
    spin_coords = q_six_null @ spin_matrix.T
    spin_projection_error_max = float(
        np.max(np.linalg.norm(spin_matrix.T - q_six_null.T @ spin_coords, axis=0))
    )
    spin_projection_rank = int(np.linalg.matrix_rank(spin_coords, tol=1e-9))
    if spin_residual_max > 1e-8 or spin_projection_error_max > 1e-8 or spin_projection_rank != 16:
        raise AssertionError("verified component spin subspace is not contained in the expanded nullspace")
    spin_orth, _ = np.linalg.qr(spin_coords)
    nonspin = q_six_null - spin_orth @ (spin_orth.T @ q_six_null)
    nonspin_singular = np.linalg.svd(nonspin, compute_uv=False)
    nonspin_rank = int(np.count_nonzero(nonspin_singular > 1e-9))

    wood_bodies = [body_id for body_id in ids if body_id.startswith("W")]
    metal_bodies = [body_id for body_id in ids if body_id.startswith("M")]
    body_participation = {}
    for body_id in ids:
        start = index[body_id] * 6
        body_participation[body_id] = float(
            np.linalg.norm(q_six_null[:, start : start + 6]) ** 2 / q_six_null.shape[0]
        )
    wood_null_participation = float(sum(body_participation[b] for b in wood_bodies))
    metal_null_participation = float(sum(body_participation[b] for b in metal_bodies))

    local_axes = {
        "X": np.asarray([1.0, 0.0, 0.0]),
        "T": np.asarray([0.0, 0.6427876096865394, 0.766044443118978]),
        "N": np.asarray([0.0, -0.766044443118978, 0.6427876096865394]),
    }

    def wood_observables_for(nullspace: np.ndarray) -> dict:
        result = {}
        for interface in classification["wood_interfaces"]:
            moving = interface["first_face"]["mesh_body_id"]
            reference = interface["second_face"]["mesh_body_id"]
            datum = np.asarray(
                interface["mesh_overlay"]["centroid_global_xyz_mm"], dtype=np.float64
            )
            values = {}
            for label, axis in local_axes.items():
                row = relative_translation_row(
                    ids, index, origins, moving, reference, datum, axis
                )
                values[f"translation_{label}"] = float(np.linalg.norm(nullspace @ row))
            for axis, label in zip(global_axes, ("X", "Y", "Z"), strict=True):
                row = relative_rotation_row(ids, index, moving, reference, axis)
                values[f"rotation_{label}"] = float(np.linalg.norm(nullspace @ row))
            result[interface["interface_id"]] = values
        return result

    wood_observables_by_case = {
        case_id: wood_observables_for(nullspace)
        for case_id, nullspace in nullspaces.items()
    }
    max_wood_observable_by_case = {
        case_id: max(abs(value) for values in interfaces.values() for value in values.values())
        for case_id, interfaces in wood_observables_by_case.items()
    }
    wood_observables = wood_observables_by_case[
        "six_global_gauges_plus_relative_six_plus_q"
    ]
    max_wood_observable = max_wood_observable_by_case[
        "six_global_gauges_plus_relative_six_plus_q"
    ]

    # The q-only case demonstrates why a complete interface six-component
    # control cannot be replaced by one scalar, and the six-only case shows
    # why q can appear to close one internal wood mode only while prescribed.
    q_only_null = nullspaces["six_global_gauges_plus_single_q"]
    six_only_null = nullspaces["six_global_gauges_plus_relative_rail_principal_six"]
    q_only_principal_n = relative_translation_row(
        ids,
        index,
        origins,
        q_moving,
        q_reference,
        q_datum,
        q_direction,
    )
    q_projection_q_only = float(np.linalg.norm(q_only_null @ q_only_principal_n))
    q_projection_six_only = float(np.linalg.norm(six_only_null @ q_only_principal_n))

    paired_run = load_json(PATHS["upstream_attempt_execution"])
    if paired_run["returncode"] != 201 or paired_run["timed_out"]:
        raise AssertionError("pinned paired upstream attempt terminal status changed")
    instrumented_run = load_json(PATHS["instrumented_attempt_execution"])
    if instrumented_run["returncode"] != 201 or instrumented_run["timed_out"]:
        raise AssertionError("pinned paired instrumented attempt terminal status changed")
    prefix_comparison = load_json(PATHS["accepted_inc1_comparison"])
    if (
        prefix_comparison["status"]
        != "ACCEPTED_INC1_PREFIX_OUTPUT_DIAGNOSTIC_ONLY_RUNTIME_NOT_ACCEPTED"
        or prefix_comparison["runtime_pass"]
        or prefix_comparison["full_step_pass"]
        or prefix_comparison["mechanical_acceptance"]
        or prefix_comparison["full_trajectory_neutrality"]
        or prefix_comparison["frd"]["datasets_compared"] != 6
        or prefix_comparison["frd"]["accepted_states_compared"] != 1
        or not prefix_comparison["sta"]["path_identical"]
        or not prefix_comparison["sta"]["attempt_path_through_first_accepted_identical"]
        or prefix_comparison["dat_contact"]["max_abs_difference"] != "0"
    ):
        raise AssertionError("accepted-increment prefix comparison status changed")
    if (
        prefix_comparison["executions"]["unmodified-upstream"]["record_sha256"]
        != actual_sha["upstream_attempt_execution"]
        or prefix_comparison["executions"]["instrumented"]["record_sha256"]
        != actual_sha["instrumented_attempt_execution"]
    ):
        raise AssertionError("accepted-prefix report is not bound to the frozen attempt records")
    if actuator["native_solve_run"] is not False:
        raise AssertionError("actuator artifact must remain input-only")
    native_probe = native_matrix_witness["candidate_null_vector"]
    if native_probe["specific_candidate_witness_passed"] is not True:
        raise AssertionError("frozen native reference-tangent witness did not pass")

    return {
        "schema": "wood_joint_static_q_rank_disposition/v1",
        "status": "KINEMATIC_RANK_ONLY_NO_STATIC_JOINT_STIFFNESS_ACCEPTANCE",
        "producer_path": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": sha256(Path(__file__).resolve()),
        "frozen_input_sha256": actual_sha,
        "rank_method": {
            "description": "SVD row-space rank of the frozen maximal-closure rigid-body matrix, exact actuator row, and explicitly constructed rail/principal relative six-DOF control rows.",
            "relative_tolerance": RTOL,
            "characteristic_length_mm": L,
            "base_matrix_has_six_global_gauges": True,
            "base_row_kind_counts": {
                kind: matrix_doc["with_global_gauge"]["row_kinds"].count(kind)
                for kind in sorted(set(matrix_doc["with_global_gauge"]["row_kinds"]))
            },
            "patch_inventory": {
                "full_timber_bodies": len([body_id for body_id in ids if body_id.startswith("W")]),
                "physical_hardware_component_bodies": len([body_id for body_id in ids if body_id.startswith("M")]),
                "wood_interfaces": [row["interface_id"] for row in classification["wood_interfaces"]],
                "hardware_seats": len(classification["hardware_seats"]),
                "assumed_axial_mpc_rows": summary["assumed_axial_mpc_rows"],
                "direct_rail_principal_butt_seat_area_mm2": float(rail_interface["mesh_overlay"]["area_mm2"]),
            },
            "active_set_limit": "All three finite wood patches and sixteen hardware seats are treated as closed bilateral normal equalities, with four assumed axial bolt/nut MPC rows. This is a maximal-closure kinematic screen, not the current unilateral zero-load active set or a continuum tangent.",
        },
        "q_coordinate": {
            "source_actuator_status": actuator["status"],
            "source_interface_id": q_interface,
            "moving_body": q_moving,
            "reference_body": q_reference,
            "datum_global_xyz_mm": q_datum.tolist(),
            "direction_global_xyz": q_direction.tolist(),
            "physical_nodal_equation_terms": len(actuator["equation"]["physical_terms_before_normalization"]),
            "analytic_relative_displacement_row_scale": q_scale,
            "relative_row_error": q_relative_error,
            "unit_wrench_force_residual_n": actuator["global_unit_force_residual_n"],
            "unit_wrench_moment_residual_nmm": actuator["global_unit_moment_residual_nmm"],
            "actuator_artifact_is_input_only": actuator["native_solve_run"] is False,
            "role_limit": "q is an exact work-conjugate finite-patch coordinate and a possible separately labeled clearance-seating input. It is not a physical service restraint or an accepted static joint load case.",
        },
        "relative_interface_control": {
            "interface_id": rail_interface_id,
            "moving_body": rail_body,
            "reference_body": principal_body,
            "datum_global_xyz_mm": rail_datum.tolist(),
            "component_rows": relative_six_labels,
            "interpretation": "Six relative translation/rotation components at the direct rail/principal butt-seat datum; these are prescribed interface kinematics, not arbitrary internal stabilizers or global gauges.",
        },
        "rank_cases": case_results,
        "rank_tolerance_sensitivity": {
            "description": "Exact reported nullities use relative SVD threshold 1e-10. The same integer ranks persist at 1e-9 and 1e-11; at 1e-12 two additional near-singular directions are retained in every case.",
            "by_relative_tolerance": rank_tolerance_sensitivity,
        },
        "q_does_not_resolve_wood_modes_alone": {
            "null_projection_of_q_after_q_control": q_projection_q_only,
            "null_projection_of_q_after_six_relative_controls_without_q": q_projection_six_only,
            "maximum_wood_relative_observable_null_projection_by_case": max_wood_observable_by_case,
            "wood_relative_observables_by_case": wood_observables_by_case,
            "note": "The exact q row removes one null direction. Six rail/principal controls without q leave one cleat-related wood mode in this screen. Combining q with all six controls removes the tested rigid relative wood observables only while both sets of kinematics are enforced.",
        },
        "expanded_nullspace": {
            "nullity": int(q_six_null.shape[0]),
            "verified_component_axis_spin_count": len(spin_body_ids),
            "verified_component_axis_spin_rank": spin_projection_rank,
            "verified_component_axis_spin_body_ids": spin_body_ids,
            "maximum_augmented_row_residual_for_spin_vectors": spin_residual_max,
            "maximum_spin_projection_error_from_nullspace": spin_projection_error_max,
            "additional_nonspin_hardware_nullity": nonspin_rank,
            "wood_body_null_participation_fraction": wood_null_participation,
            "metal_body_null_participation_fraction": metal_null_participation,
            "per_body_null_participation_fraction": body_participation,
            "maximum_relative_wood_interface_observable_null_projection": max_wood_observable,
            "relative_wood_interface_observables": wood_observables,
            "classification_limit": "The sixteen pure component-axis spins are null under the modeled normal-only seat and axial-MPC equations. They are gauge-like for non-torsional response only under an axisymmetric/no-torque connection idealization; thread torque, nut seating, or friction can make them response-affecting. The other thirty-two are not global gauges or these pure spins; they remain unclassified internal hardware mechanisms and cannot be presumed energetically irrelevant or stabilized away.",
        },
        "native_evidence": {
            "reference_tangent_preflight_completed": True,
            "native_matrix_probe": {
                "displacement": "1 mm translation of all 9,369 cleat nodes along local N with other bodies/control zero",
                "maximum_nodal_residual_n": native_probe["kv_inf_norm"],
                "scaled_residual": native_probe["scaled_residual_inf"],
                "scaled_residual_limit": native_probe["scaled_residual_acceptance_limit"],
                "contact_active_set_proven": native_matrix_witness["matrix_scope"]["deck_audit"]["contact_active_set_or_zero_pressure_state_proven"],
            },
            "interpretation": "The candidate cleat-slip vector has a near-zero residual in the emitted zero-load reference tangent. The native record does not prove the contact active set or zero-pressure state, so this is not proof of a physically equilibrated free mechanism. It does not establish total nullity or make q control a service restraint.",
            "paired_output_instrumentation_comparison": {
                "attempt": "dependent-native-upstream-attempt01",
                "accepted_inc1_prefix_output_comparison_passed": True,
                "comparison_report_status": prefix_comparison["status"],
                "comparison_report_sha256": actual_sha["accepted_inc1_comparison"],
                "accepted_states_compared": prefix_comparison["frd"]["accepted_states_compared"],
                "frd_datasets_compared": prefix_comparison["frd"]["datasets_compared"],
                "dat_contact_max_abs_difference": prefix_comparison["dat_contact"]["max_abs_difference"],
                "full_run_solver_exit_codes": {
                    "unmodified_upstream": paired_run["returncode"],
                    "instrumented": instrumented_run["returncode"],
                },
                "timed_out": False,
                "runtime_pass": prefix_comparison["runtime_pass"],
                "full_step_pass": prefix_comparison["full_step_pass"],
                "full_trajectory_neutrality": prefix_comparison["full_trajectory_neutrality"],
                "mechanical_acceptance": prefix_comparison["mechanical_acceptance"],
                "interpretation": "The accepted first-increment (0.0005 s) output comparison passed as a bounded diagnostic: six accepted-state FRD datasets and 35-pair contact triplets agree within frozen print bounds. Both full runs later exited 201 at the endpoint; runtime, full-step, full-trajectory, and mechanical acceptance remain false.",
            },
        },
        "reduced_bound_disposition": {
            "currently_qualified_source_bound": False,
            "why_not": [
                "The ordinary-joint method describes an older EN 1995-1-1:2004+A1:2008 K_ser expression as a comparison and explicitly says the 2025 edition must be checked before calling that rule current; the described 460/500/520 kg/m^3 points are not material bounds.",
                "The four current WJ24 bottom-center stack products are not selected, and source applicability for physical 1/4-20 thread engagement, bolt/nut stiffness/slack, and seat transfer remains unresolved.",
                "The current six-case applied-load contract does not provide a joint load split or accepted current interface stiffness; a whole-frame sensitivity can only be diagnostic until a defensible law and bounded parameters exist.",
            ],
            "clearance_basis": "Use a frozen modeled dimensional clearance scenario, explicitly distinguished from clearance measured on a received physical part. A supported provisional dimensional scenario may be analyzed conditionally; it does not imply a received-part measurement.",
            "next_supported_route": "Obtain a current, applicable fastener/wood slip law or a justified evidence-backed lower/upper connection model; include the frozen modeled dimensional clearance scenario explicitly and keep bolt bending, wood bearing, axial engagement, and seat compliance in series without double counting. Then propagate the bounded laws through fresh whole-frame sensitivity cases. Until those source inputs exist, retain the dynamic seating case as a clearance/contact diagnostic only; do not infer static stiffness from its endpoint or substitute an arbitrary positive K.",
        },
        "disposition": {
            "single_q_plus_six_global_gauges_for_static_joint_stiffness": "NO",
            "six_relative_rail_principal_controls_as_component_test_kinematics": "YES_AS_PHYSICALLY_INTERPRETABLE_BOUNDARY_CONDITION_BUT_NOT_SUFFICIENT_FOR_THIS_CURRENT_PATCH",
            "combined_q_plus_relative_six_as_a_service_case": "NO; q is an internal cleat seat coordinate, not a physical service restraint. It may only be a separate, labeled clearance-seating diagnostic unless a physical fixture/load case justifies it.",
            "current_static_q_response_or_stiffness_accepted": False,
            "current_direct_patch_or_reduced_bound_route_ready": False,
        },
        "limits": [
            "The rigid matrix is a sensitivity under assumed closed bilateral face-normal constraints and assumed axial MPCs; unilateral contacts and finite clearances can add mechanisms.",
            "The six relative controls are kinematic inputs; they do not prove internal cleat/hardware equilibrium after controls are released.",
            "No stiffness, resistance, capacity, service demand, material property, product choice, or release conclusion is produced.",
            "Six-axis torque response cannot dismiss bolt/nut axis spins as harmless without a torsional applicability basis.",
        ],
    }


if __name__ == "__main__":
    result = analyze()
    result_path = OUT / "rank-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "result": str(result_path),
                "status": result["status"],
                "rank_cases": {
                    case_id: {
                        "rank": case["rank"],
                        "nullity": case["nullity"],
                    }
                    for case_id, case in result["rank_cases"].items()
                },
                "expanded_nullity": result["expanded_nullspace"]["nullity"],
                "axis_spin_rank": result["expanded_nullspace"][
                    "verified_component_axis_spin_rank"
                ],
                "additional_hardware_modes": result["expanded_nullspace"][
                    "additional_nonspin_hardware_nullity"
                ],
                "max_wood_interface_projection": result["expanded_nullspace"][
                    "maximum_relative_wood_interface_observable_null_projection"
                ],
            },
            indent=2,
        )
    )
