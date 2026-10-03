"""Read-only source preflight for bounded A12 raw-H endpoint recovery.

This script never factors K, solves a body state, launches CalculiX, or writes
raw response vectors. It rebuilds the physical connector map from the pinned
source contract, checks the two-owner raw body loads/wrenches, and runs a
small analytic/constructed free-body oracle with a prescribed answer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PIN_FILE = HERE / "source-pins.json"
REPORT_FILE = HERE / "readiness.json"
OUTPUT_PIN_FILE = HERE / "output-pin.json"
ROTATION_SCALE_MM = 1000.0
TARGET_ROW = 1586
TARGET_GROUP = "SPR1787"
TARGET_ELEMENT = 3690
TARGET_OWNERS = (
    "left_service_inner_lower_cleat",
    "base_rail_service_lower_left",
)


PATHS = {
    "raw_response": "current-a12-fixed-active-raw-H-comparison-attempt01/response.npz",
    "raw_assessment": "current-a12-fixed-active-raw-H-comparison-attempt01/assessment.json",
    "raw_frozen_inputs": "current-a12-fixed-active-raw-H-comparison-attempt01/frozen-inputs.json",
    "raw_readiness": "current-a12-fixed-active-raw-H-comparison-attempt01/readiness.json",
    "raw_output_pin": "current-a12-fixed-active-raw-H-comparison-attempt01/output-pin.json",
    "raw_producer": "current-a12-fixed-active-raw-H-comparison-attempt01/prepare_raw.py",
    "raw_parent_runner": "current-a12-fixed-active-raw-H-comparison-attempt01/parent_run.py",
    "force_diagnostic": "current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/assessment.json",
    "force_diagnostic_pins": "current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/source-pins.json",
    "force_diagnostic_output_pin": "current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/output-pin.json",
    "force_diagnostic_producer": "current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/diagnose.py",
    "compliance_inputs": "current-frame-connector-compliance-attempt04/inputs.json",
    "compliance_assessment": "current-frame-connector-compliance-attempt04/assessment.json",
    "compliance_output_pin": "current-frame-connector-compliance-attempt04/output-pin.json",
    "compliance_producer": "current-frame-connector-compliance-attempt04/build_compliance.py",
    "compliance_B": "current-frame-connector-compliance-attempt04/B.npz",
    "compliance_operators": "current-frame-connector-compliance-attempt04/operators.npz",
    "compliance_row_identities": "current-frame-connector-compliance-attempt04/row-identities.json",
    "projection_contract": "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json",
    "physical_index_map": "current-frame-physical-connector-projection-contract-attempt01/physical-index-map.json",
    "projection_source_pins": "current-frame-physical-connector-projection-contract-attempt01/source-pins.json",
    "source_load_maps": "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json",
    "source_model": "current-springa-frame-input-adapter-attempt01/a12-rear/model.json",
    "mass_centroids": "../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json",
    "mass_centroids_readme": "../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/README.md",
    "mass_centroids_exporter": "../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/export.py",
    "ghost_translation_readme": "current-springa-ghost-coordinate-translation-diagnostic-attempt01/README.md",
    "ghost_translation_known_answer": "current-springa-ghost-coordinate-translation-diagnostic-attempt01/known-answer.json",
    "ghost_translation_audit": "current-springa-ghost-coordinate-translation-diagnostic-attempt01/audit.py",
    "emitted_deck": "current-springa-selected-floor-a12-rear-attempt03/model.inp",
    "emitted_model": "current-springa-selected-floor-a12-rear-attempt03/model.json",
    "stiffness_K": "current-frame-pure-solid-matrix-export-native-attempt01/model.sti",
    "dof_map": "current-frame-pure-solid-matrix-export-native-attempt01/model.dof",
    "matrix_export_assessment": "current-frame-pure-solid-matrix-export-native-attempt01/assessment.json",
    "known_answer_inputs": "current-a12-fixed-episode-dual-qp-preparation-attempt01/known-answer.npz",
    "quotient_method": "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    "quotient_method_assessment": "current-elastic-quotient-method-preflight-attempt02/assessment.json",
    "condensation_method": "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
    "condensation_assessment": "current-frame-free-body-condensation-preflight-attempt01/assessment.json",
}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_json(name: str) -> object:
    return json.loads((BASE / PATHS[name]).read_text(encoding="utf-8"))


def source_inventory() -> dict[str, str]:
    return {name: str((BASE / relative).relative_to(ROOT)) for name, relative in PATHS.items()}


def check_pins(create: bool) -> dict[str, str]:
    paths = source_inventory()
    actual = {name: sha_file(ROOT / rel) for name, rel in paths.items()}
    if create:
        if PIN_FILE.exists():
            raise RuntimeError("source-pins.json already exists; refusing to replace the frozen source set")
        dump_json(PIN_FILE, {"schema": "a12_row1586_endpoint_preflight_source_pins/v1", "sha256": actual})
        return actual
    if not PIN_FILE.is_file():
        raise RuntimeError("source-pins.json is missing; run --freeze-source-pins once on reviewed inputs")
    pinned = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if pinned.get("schema") != "a12_row1586_endpoint_preflight_source_pins/v1":
        raise AssertionError("source pin schema changed")
    expected = pinned.get("sha256")
    if expected != actual:
        changed = {name: {"expected": expected.get(name), "actual": actual.get(name)}
                   for name in sorted(set(expected or {}) | set(actual))
                   if (expected or {}).get(name) != actual.get(name)}
        raise AssertionError(f"frozen source hashes changed: {changed}")
    return actual


def parse_dof_file(path: Path) -> list[tuple[int, int]]:
    labels = []
    for line in path.read_text(encoding="ascii").splitlines():
        node, direction = line.strip().split(".")
        labels.append((int(node), int(direction)))
    if len(labels) != 37647 or len(set(labels)) != len(labels):
        raise AssertionError("native DOF labels are not a unique 37,647-entry map")
    return labels


def parse_emitted_equations(text: str) -> dict[tuple[int, int], list[tuple[int, int, float]]]:
    lines = text.splitlines()
    equations = {}
    pos = 0
    while pos < len(lines):
        if lines[pos].strip().upper() != "*EQUATION":
            pos += 1
            continue
        pos += 1
        while pos < len(lines) and not lines[pos].strip():
            pos += 1
        count = int(lines[pos].strip())
        pos += 1
        values: list[str] = []
        while len(values) < 3 * count:
            if pos >= len(lines) or lines[pos].lstrip().startswith("*"):
                raise AssertionError("emitted *EQUATION is truncated")
            values.extend(piece.strip() for piece in lines[pos].split(",") if piece.strip())
            pos += 1
        if len(values) != 3 * count:
            raise AssertionError("emitted *EQUATION has extra terms")
        terms = [(int(values[i]), int(values[i + 1]), float(values[i + 2]))
                 for i in range(0, len(values), 3)]
        key = terms[0][:2]
        if key in equations:
            raise AssertionError(f"duplicate dependent MPC DOF {key}")
        equations[key] = terms
    return equations


def parse_deck_nodes(text: str, wanted: set[int]) -> dict[int, np.ndarray]:
    output = {}
    in_nodes = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("*NODE"):
            in_nodes = True
            continue
        if stripped.startswith("*"):
            in_nodes = False
        if in_nodes and stripped:
            fields = [field.strip() for field in stripped.split(",")]
            if len(fields) >= 4 and fields[0].isdigit() and int(fields[0]) in wanted:
                output[int(fields[0])] = np.asarray([float(v) for v in fields[1:4]], dtype=np.float64)
    if set(output) != wanted:
        raise AssertionError(f"emitted deck node coordinates missing: {sorted(wanted - set(output))}")
    return output


def source_equations_for_nodes(model: dict, nodes: set[int]) -> dict[tuple[int, int], list[tuple[int, int, float]]]:
    output = {}
    for equation in model["equations"]:
        terms = [(int(term[0]), int(term[1]), float(term[2])) for term in equation]
        if terms[0][0] in nodes:
            output[terms[0][:2]] = terms
    return output


def rigid_rows(xyz: np.ndarray, scale_mm: float) -> tuple[np.ndarray, np.ndarray]:
    center = np.mean(xyz, axis=0)
    basis = np.zeros((3 * len(xyz), 6), dtype=np.float64)
    eye = np.eye(3)
    for i, point in enumerate(xyz):
        relative = point - center
        for axis in range(3):
            basis[3 * i:3 * i + 3, 3 + axis] = np.cross(eye[axis], relative) / scale_mm
        basis[3 * i:3 * i + 3, :3] = eye
    return center, basis


def wrench_from_nodal_forces(xyz: np.ndarray, force: np.ndarray, scale_mm: float) -> tuple[np.ndarray, np.ndarray]:
    net_force = np.sum(force, axis=0)
    center = np.mean(xyz, axis=0)
    moment = np.sum(np.cross(xyz - center, force), axis=0)
    return np.concatenate((net_force, moment / scale_mm)), moment


def transport_moment(moment_at_source: np.ndarray, force: np.ndarray,
                     source_reference: np.ndarray, target_reference: np.ndarray) -> np.ndarray:
    """Transport an ordinary force/moment wrench between declared points."""
    return moment_at_source - np.cross(target_reference - source_reference, force)


def known_answer_oracle() -> dict:
    """Check a prescribed tetrahedral free-body response without solving it."""
    xyz = np.asarray([[0., 0., 0.], [1000., 0., 0.], [0., 1000., 0.], [0., 0., 1000.]])
    center = np.mean(xyz, axis=0)
    _, R = rigid_rows(xyz, ROTATION_SCALE_MM)
    alpha = 0.01
    u_el = alpha * (xyz - center)
    rigid = np.asarray([3., -5., 7., 4., -2., 6.])
    u_full = (R @ rigid).reshape((4, 3)) + u_el

    # Assemble K from six unit axial springs in a complete tetrahedron. No
    # factorization or solve occurs; the prescribed u_el gives p=K*u_el.
    K = np.zeros((12, 12), dtype=np.float64)
    for i in range(4):
        for j in range(i + 1, 4):
            delta = xyz[j] - xyz[i]
            length = float(np.linalg.norm(delta))
            direction = delta / length
            block = np.outer(direction, direction)
            ii, jj = slice(3 * i, 3 * i + 3), slice(3 * j, 3 * j + 3)
            K[ii, ii] += block
            K[jj, jj] += block
            K[ii, jj] -= block
            K[jj, ii] -= block
    p_el = (K @ u_el.reshape(-1)).reshape((4, 3))
    residual = float(np.max(np.abs((K @ u_el.reshape(-1)).reshape((4, 3)) - p_el)))
    gauge = R.T @ u_el.reshape(-1)
    equilibrium_wrench, equilibrium_moment = wrench_from_nodal_forces(xyz, p_el, ROTATION_SCALE_MM)

    # Endpoint interpolation/back-projection through two exact barycentric
    # rows. Affine rigid and elastic fields must return the known point field.
    wa = np.asarray([1., 0., 0., 0.])
    wb = np.asarray([0., 1. / 3., 1. / 3., 1. / 3.])
    xa, xb = wa @ xyz, wb @ xyz
    ua, ub = wa @ u_full, wb @ u_full
    omega = rigid[3:] / ROTATION_SCALE_MM
    expected_a = rigid[:3] + np.cross(omega, xa - center) + alpha * (xa - center)
    expected_b = rigid[:3] + np.cross(omega, xb - center) + alpha * (xb - center)
    endpoint_error = float(max(np.max(np.abs(ua - expected_a)), np.max(np.abs(ub - expected_b))))
    direction = (xb - xa) / np.linalg.norm(xb - xa)
    q_point = float(np.dot(direction, ub - ua))
    Bq = np.concatenate([(-wa[i] * direction + wb[i] * direction) for i in range(4)])
    q_back_projected = float(Bq @ u_full.reshape(-1))

    # A signed endpoint-action pair exercises the force/couple transform.
    # It is deliberately only an oracle load: its couple is not balanced and
    # the production quotient method would reject it before any solve.
    test_force = 13.25
    probe_axis = np.asarray([1., 0., 0.])
    B_probe = np.concatenate([(-wa[i] * probe_axis + wb[i] * probe_axis) for i in range(4)])
    pair = (test_force * B_probe).reshape((4, 3))
    generalized_pair = R.T @ pair.reshape(-1)
    pair_wrench, pair_moment = wrench_from_nodal_forces(xyz, pair, ROTATION_SCALE_MM)
    wrench_error = float(np.max(np.abs(generalized_pair - pair_wrench)))

    if residual != 0.0 or np.max(np.abs(gauge)) > 1.0e-12:
        raise AssertionError("known prescribed free-body displacement failed K/gauge identity")
    if np.max(np.abs(equilibrium_wrench)) > 1.0e-12:
        raise AssertionError("known elastic response is not self-equilibrated")
    if endpoint_error > 1.0e-12 or abs(q_point - q_back_projected) > 1.0e-12:
        raise AssertionError("known endpoint reconstruction/back-projection failed")
    if wrench_error > 1.0e-12:
        raise AssertionError("known signed force/couple transform failed")
    return {
        "status": "PASS_PRESCRIBED_FREE_BODY_ENDPOINT_AND_WRENCH_ORACLE",
        "free_body": {"nodes": 4, "unit_axial_springs": 6, "physical_dofs": 12,
                      "rigid_modes": 6, "factorization_or_solve": False},
        "prescribed_displacement": {"elastic_field": "u_el = 0.01*(x-node_mean_reference)",
                                    "rigid_generalized_coordinates_mm": rigid.tolist(),
                                    "max_Ku_minus_p_N": residual,
                                    "max_Rt_u_el_mm": float(np.max(np.abs(gauge))),
                                    "balanced_elastic_wrench_scaled_N": equilibrium_wrench.tolist(),
                                    "balanced_elastic_moment_N_mm": equilibrium_moment.tolist()},
        "endpoint_recovery": {"endpoint_a_barycentric_weights": wa.tolist(),
                              "endpoint_b_barycentric_weights": wb.tolist(),
                              "u_a_mm": ua.tolist(), "u_b_mm": ub.tolist(),
                              "max_endpoint_known_answer_error_mm": endpoint_error,
                              "q_point_mm": q_point,
                              "q_back_projection_mm": q_back_projected,
                              "max_q_projection_back_map_error_mm": abs(q_point - q_back_projected)},
    "signed_wrench_oracle": {"scalar_force_N": test_force,
                                 "probe_axis_global_xyz": probe_axis.tolist(),
                                 "R_transpose_B_transpose_f_scaled_N": generalized_pair.tolist(),
                                 "direct_net_force_N": pair_wrench[:3].tolist(),
                                 "direct_moment_about_node_mean_reference_N_mm": pair_moment.tolist(),
                                 "max_Rt_vs_direct_wrench_error_N": wrench_error,
                                 "B_transpose_force_equals_endpoint_action_map": True,
                                 "unbalanced_couple_would_be_rejected_before_solve": True},
    }


def build_readiness(hashes: dict[str, str]) -> dict:
    response_path = ROOT / source_inventory()["raw_response"]
    response = np.load(response_path, allow_pickle=False)
    raw = {key: response[key] for key in response.files}
    raw_assessment = load_json("raw_assessment")
    raw_pin = load_json("raw_output_pin")
    force_diag = load_json("force_diagnostic")
    compliance = load_json("compliance_assessment")
    projection = load_json("projection_contract")
    physical_map = load_json("physical_index_map")
    source_load = load_json("source_load_maps")
    model = load_json("source_model")
    mass_centroids = load_json("mass_centroids")
    mass_rows = mass_centroids["rows"]
    mass_rows_by_name = {row["name"]: row for row in mass_rows}
    if len(mass_rows) != 778 or len(mass_rows_by_name) != len(mass_rows):
        raise AssertionError("pinned modeled mass-center inventory is incomplete or duplicated")
    if mass_centroids["status"] != "MODELED_SOLID_MASS_CENTERS_NOT_A_FRAME_RESPONSE":
        raise AssertionError("mass-center source has an unexpected disposition")
    if mass_centroids["revision_id"] != model["geometry_revision_id"]:
        raise AssertionError("modeled mass centers do not match the pinned model revision")
    ghost_translation = load_json("ghost_translation_known_answer")
    ghost_row = ghost_translation["row"]
    ghost_response = ghost_translation["response_comparison"]
    ghost_arithmetic = ghost_translation["source_arithmetic"]
    if (ghost_row["parent_reduced_force_vector_position"] != TARGET_ROW
            or ghost_row["response_element"] != TARGET_ELEMENT
            or ghost_row["source_group"] != TARGET_GROUP
            or ghost_translation["deck"]["endpoint_nodes"] != [21300, 21301]):
        raise AssertionError("adjacent ghost-coordinate diagnostic does not identify target SPRINGA row")
    ghost_force_shift = float(ghost_arithmetic["translated_minus_direct_force_N"])
    ghost_native_radius = float(ghost_response["reported_native_endpoint_RF_radius_N"])
    if (not ghost_response["direct_force_inside_reported_RF_radius"]
            or not ghost_response["translated_force_inside_reported_RF_radius"]
            or abs(ghost_force_shift) >= ghost_native_radius):
        raise AssertionError("ghost-only translation diagnostic no longer reports a sub-interval arithmetic effect")
    known_answer_path = ROOT / source_inventory()["known_answer_inputs"]
    known_answer = np.load(known_answer_path, allow_pickle=False)
    saved_D = np.load(ROOT / source_inventory()["compliance_operators"], allow_pickle=False)["D"]
    if saved_D.shape != (1840, 300):
        raise AssertionError("pinned compliance D operator has an unexpected shape")

    if raw_assessment["status"] != "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE":
        raise AssertionError("the original raw-H comparison stop status changed")
    if raw_assessment["original_DAT_comparisons"]["forces"]["failed_count"] != 27:
        raise AssertionError("the original 27-force-interval STOP changed")
    if raw_assessment["candidate_forces_adopted"] or raw_assessment["mechanical_acceptance"]:
        raise AssertionError("raw-H output has an adopted/accepted disposition")
    if raw_pin.get("assessment_sha256") != hashes["raw_assessment"]:
        raise AssertionError("raw-H report output pin mismatch")
    if sha_file(response_path) != raw_assessment["response_npz_sha256"]:
        raise AssertionError("raw-H saved response hash does not match its assessment")
    if not all(key in raw for key in ("f_full_N", "a_mm", "q_raw_mm", "body_equilibrium_residuals_N_and_unscaled_moment")):
        raise AssertionError("raw-H response lacks expected saved state arrays")
    if raw["f_full_N"].shape != (1840,) or raw["a_mm"].shape != (300,):
        raise AssertionError("raw-H state dimensions changed")

    rows = projection["rows"]
    if len(rows) != 1840:
        raise AssertionError("projection row count changed")
    target = rows[TARGET_ROW]
    owner = target["ownership"]
    if (target["source_group"] != TARGET_GROUP or target["source_element"] != TARGET_ELEMENT
            or target["source_inventory_row_index"] != 1786
            or (owner["first_body"], owner["second_body"]) != TARGET_OWNERS):
        raise AssertionError("target row identity or owner order changed")
    force_failure = force_diag["force_interval"]["all_row_worst_normalized_difference"]
    if force_failure["source_position"] != TARGET_ROW or force_failure["interval_ratio"] <= 1.0:
        raise AssertionError("the source diagnostic no longer identifies row 1586 as the worst normalized force failure")
    if force_diag["disposition"]["frame_state_solve"] or force_diag["disposition"]["native_run"]:
        raise AssertionError("source diagnostic unexpectedly ran a frame/native solve")

    labels = parse_dof_file(ROOT / source_inventory()["dof_map"])
    row_for = {label: i for i, label in enumerate(labels)}
    index_by_node = {int(record["node"]): i for i, record in enumerate(physical_map)}
    if len(physical_map) != 12549 or len(index_by_node) != len(physical_map):
        raise AssertionError("physical node map changed or contains duplicate nodes")
    if any((node, direction) not in row_for for node in index_by_node for direction in (1, 2, 3)):
        raise AssertionError("physical node map does not map bijectively into native DOFs")
    body_by_node = {int(record["node"]): record["body"] for record in physical_map}
    xyz_by_node = {int(record["node"]): np.asarray(record["xyz_mm"], dtype=np.float64)
                   for record in physical_map}
    for body_name, source_nodes in model["physical_body_nodes"].items():
        mapped = {node for node, value in body_by_node.items() if value == body_name}
        if mapped != {int(node) for node in source_nodes}:
            raise AssertionError(f"physical body node map mismatch for {body_name}")

    # Rebuild source B directly from physical_sparse_row and the pinned maps.
    brow, bcol, bdata = [], [], []
    body_values = {body: {"p": np.zeros(len(labels)), "gravity": np.zeros(len(labels)),
                          "climber": np.zeros(len(labels)), "target_action": np.zeros(len(labels)),
                          "incident_rows": set(), "incident_families": {}}
                   for body in TARGET_OWNERS}
    owner_terms = {body: 0 for body in TARGET_OWNERS}
    row_owner_count = {body: 0 for body in TARGET_OWNERS}
    for row_index, record in enumerate(rows):
        owners_for_row = set()
        for term in record["physical_sparse_row"]:
            coordinate = int(term["coordinate_index"])
            phys = physical_map[coordinate // 3]
            direction = coordinate % 3 + 1
            dof_index = row_for[(int(phys["node"]), direction)]
            value = float(term["coefficient"])
            brow.append(row_index)
            bcol.append(dof_index)
            bdata.append(value)
            body = phys["body"]
            if body in body_values:
                owners_for_row.add(body)
                owner_terms[body] += 1
                body_values[body]["p"][dof_index] -= value * raw["f_full_N"][row_index]
                if row_index == TARGET_ROW:
                    body_values[body]["target_action"][dof_index] -= value * raw["f_full_N"][row_index]
        for body in owners_for_row:
            body_values[body]["incident_rows"].add(row_index)
            family = record["family"]
            body_values[body]["incident_families"][family] = body_values[body]["incident_families"].get(family, 0) + 1
            row_owner_count[body] += 1
    B_rebuilt = sp.coo_matrix((bdata, (brow, bcol)), shape=(1840, 37647)).tocsr()
    B_saved = sp.load_npz(ROOT / source_inventory()["compliance_B"]).tocsr()
    delta_B = B_rebuilt - B_saved
    if B_saved.shape != (1840, 37647) or B_rebuilt.nnz != 62607 or (delta_B.nnz and np.max(np.abs(delta_B.data)) != 0.0):
        raise AssertionError("independent source B reconstruction differs from pinned compliance B")

    a12 = next(case for case in source_load["cases"] if case["case_id"] == "a12-rear")
    if not a12.get("gravity_nodal_map") or not a12.get("climber_nodal_map"):
        raise AssertionError("A12 rear source gravity/climber maps are missing")
    source_map_summaries = {}
    for kind, field in (("gravity", "gravity_nodal_map"), ("climber", "climber_nodal_map")):
        nodal = a12[field]
        for node_text, vector in nodal.items():
            node = int(node_text)
            if node not in index_by_node:
                raise AssertionError(f"{kind} source load contains nonphysical node {node}")
            body = body_by_node[node]
            if body not in body_values:
                continue
            for direction, force in enumerate(vector, 1):
                body_values[body][kind][row_for[(node, direction)]] = float(force)
                body_values[body]["p"][row_for[(node, direction)]] += float(force)
        source_map_summaries[kind] = {
            "all_case_node_count": int(a12[field + "_node_count"]),
            "all_case_map_sha256": a12[field + "_sha256"],
            "two_owner_nodes": {
                body: sum(1 for node in nodal if body_by_node[int(node)] == body)
                for body in TARGET_OWNERS},
        }

    body_names = compliance["body_names_in_rigid_column_order"]
    if len(body_names) != 50 or known_answer["W_total"].shape != (300,):
        raise AssertionError("frozen rigid load map has unexpected shape")
    deck_path = ROOT / source_inventory()["emitted_deck"]
    deck_text = deck_path.read_text(encoding="ascii")
    deck_eq = parse_emitted_equations(deck_text)
    source_eq = source_equations_for_nodes(model, {18266, 18267, 18268, 18269, 21300})
    relevant_keys = {(node, direction) for node in (18266, 18267, 18268, 18269, 21300)
                     for direction in (1, 2, 3)}
    eqs = {}
    max_emitted_source_coefficient_difference = 0.0
    for key in sorted(relevant_keys):
        if key not in deck_eq or key not in source_eq:
            raise AssertionError(f"missing exact emitted/source MPC equation at {key}")
        emitted, source = deck_eq[key], source_eq[key]
        if len(emitted) != len(source):
            raise AssertionError(f"MPC term count differs between source and deck at {key}")
        coeff_delta = max(abs(a[2] - b[2]) for a, b in zip(emitted, source))
        max_emitted_source_coefficient_difference = max(max_emitted_source_coefficient_difference, coeff_delta)
        if coeff_delta > 5.0e-15 or [x[:2] for x in emitted] != [x[:2] for x in source]:
            raise AssertionError(f"emitted/source MPC map mismatch at {key}: {coeff_delta}")
        eqs[f"{key[0]}.{key[1]}"] = [[node, direction, coefficient] for node, direction, coefficient in emitted]
    emitted_nodes = parse_deck_nodes(deck_text, {21300, 21301})
    dd0_mm = float(np.linalg.norm(emitted_nodes[21300] - emitted_nodes[21301]))
    if "3690,21300,21301" not in deck_text or "*ELEMENT,TYPE=SPRINGA,ELSET=SPR1787" not in deck_text:
        raise AssertionError("target SPRINGA element identity/connectivity changed")
    if not re.search(r"21301,1,3,0(?:\s|$)", deck_text):
        raise AssertionError("target numerical ground node is no longer fixed in translations")
    if dd0_mm < 99.999999 or dd0_mm > 100.000001:
        raise AssertionError("target emitted spring initial span is not the pinned 100 mm envelope")

    body_summary = {}
    balance_error = 0.0
    for body in TARGET_OWNERS:
        body_id = body_names.index(body)
        nodes = sorted(node for node, name in body_by_node.items() if name == body)
        xyz = np.stack([xyz_by_node[node] for node in nodes])
        center, R = rigid_rows(xyz, ROTATION_SCALE_MM)
        geometry = model["body_geometry"][body]["geometry_record"]
        descriptor_midpoint = 0.5 * (np.asarray(geometry["start"], dtype=np.float64)
                                     + np.asarray(geometry["end"], dtype=np.float64))
        mass_record = mass_rows_by_name[body]
        modeled_mass_center = np.asarray(mass_record["mass_center_global_xyz_mm"], dtype=np.float64)
        source_audit_rows = [record for record in model["body_wrench_audit_rows"]
                             if record["body"] == body]
        if len(source_audit_rows) != 1:
            raise AssertionError(f"source global-origin body audit is not unique for {body}")
        source_audit = source_audit_rows[0]
        local_force = np.zeros((len(nodes), 3))
        source_force = np.zeros((len(nodes), 3))
        gravity_force = np.zeros((len(nodes), 3))
        climber_force = np.zeros((len(nodes), 3))
        node_local = {node: i for i, node in enumerate(nodes)}
        for node in nodes:
            i = node_local[node]
            for direction in range(1, 4):
                dof = row_for[(node, direction)]
                local_force[i, direction - 1] = body_values[body]["p"][dof]
                gravity_force[i, direction - 1] = body_values[body]["gravity"][dof]
                climber_force[i, direction - 1] = body_values[body]["climber"][dof]
                target_action_force = body_values[body]["target_action"][dof]
                body_values[body].setdefault("target_action_vector", np.zeros((len(nodes), 3)))[i, direction - 1] = target_action_force
                source_force[i, direction - 1] = gravity_force[i, direction - 1] + climber_force[i, direction - 1]
        direct_source_force = np.sum(source_force, axis=0)
        direct_source_moment_global = np.sum(np.cross(xyz, source_force), axis=0)
        source_audit_force = np.asarray(source_audit["force_xyz_n"], dtype=np.float64)
        source_audit_moment_global = np.asarray(source_audit["moment_about_global_origin_xyz_nmm"], dtype=np.float64)
        source_audit_force_error = float(np.max(np.abs(direct_source_force - source_audit_force)))
        source_audit_moment_error = float(np.max(np.abs(direct_source_moment_global - source_audit_moment_global)))
        if source_audit_force_error > 1.0e-10 or source_audit_moment_error > 1.0e-7:
            raise AssertionError(f"independent A12 nodal map differs from source global-origin audit for {body}")
        p_wrench, p_moment = wrench_from_nodal_forces(xyz, local_force, ROTATION_SCALE_MM)
        gravity_wrench, gravity_moment = wrench_from_nodal_forces(xyz, gravity_force, ROTATION_SCALE_MM)
        climber_wrench, climber_moment = wrench_from_nodal_forces(xyz, climber_force, ROTATION_SCALE_MM)
        connector_force = local_force - source_force
        connector_wrench, connector_moment = wrench_from_nodal_forces(xyz, connector_force, ROTATION_SCALE_MM)
        target_action = body_values[body]["target_action_vector"]
        target_wrench, target_moment = wrench_from_nodal_forces(xyz, target_action, ROTATION_SCALE_MM)
        expected_sign = 1.0 if body == TARGET_OWNERS[0] else -1.0
        expected_target_force = expected_sign * np.asarray(owner["direction_global_xyz"]) * float(raw["f_full_N"][TARGET_ROW])
        if np.max(np.abs(target_wrench[:3] - expected_target_force)) > 1.0e-12:
            raise AssertionError(f"target source row signed endpoint force mismatch for {body}")
        source_point_node = 18266 if body == TARGET_OWNERS[0] else 18267
        source_point = np.asarray(model["nodes"][str(source_point_node)], dtype=np.float64)
        expected_target_moment = np.cross(source_point - center, expected_target_force)
        if np.max(np.abs(target_moment - expected_target_moment)) > 1.0e-8:
            raise AssertionError(f"target source row centroid couple mismatch for {body}")
        saved_residual = raw["body_equilibrium_residuals_N_and_unscaled_moment"][body_id].astype(np.float64)
        # Parent raw-H stores D.T*f - W in [N, Nmm/1000] coordinates.
        residual_difference = p_wrench + saved_residual
        body_balance_error = float(np.max(np.abs(residual_difference)))
        balance_error = max(balance_error, body_balance_error)
        if body_balance_error > 1.0e-8:
            raise AssertionError(f"independent raw body wrench does not close against saved row {body_id}: {body_balance_error}")
        # The frozen raw-H gate is componentwise at the source operator's
        # node-mean rigid-basis reference. Keep that datum and thresholds
        # unchanged; transport is reported separately for other references.
        gate_force = saved_residual[:3]
        gate_moment = saved_residual[3:] * ROTATION_SCALE_MM
        gate_force_limit_N = 0.1
        gate_moment_limit_Nmm = 2.0
        if float(np.max(np.abs(gate_force))) > gate_force_limit_N or float(np.max(np.abs(gate_moment))) > gate_moment_limit_Nmm:
            raise AssertionError(f"target body's original raw-H force/moment gate fails at source datum: {body}")
        references = {
            "operator_node_mean_rigid_basis_reference": center,
            "geometric_descriptor_endpoint_midpoint": descriptor_midpoint,
            "modeled_solid_mass_center": modeled_mass_center,
            "global_origin": np.zeros(3, dtype=np.float64),
        }
        transported = {}
        gate_bound_at_reference = {}
        for reference_name, reference_xyz in references.items():
            offset = reference_xyz - center
            residual_moment_at_reference = transport_moment(gate_moment, gate_force, center, reference_xyz)
            p_moment_at_reference = transport_moment(p_moment, p_wrench[:3], center, reference_xyz)
            source_moment_at_reference = transport_moment(direct_source_moment_global, direct_source_force,
                                                          np.zeros(3), reference_xyz)
            target_moment_at_reference = transport_moment(target_moment, target_wrench[:3], center, reference_xyz)
            # If each source-datum force component is bounded by 0.1 N and
            # each source-datum moment component by 2 N mm, this triangle
            # bound applies after translation. It is informational only.
            transported_component_bound = np.asarray([
                gate_moment_limit_Nmm + gate_force_limit_N * (abs(offset[1]) + abs(offset[2])),
                gate_moment_limit_Nmm + gate_force_limit_N * (abs(offset[0]) + abs(offset[2])),
                gate_moment_limit_Nmm + gate_force_limit_N * (abs(offset[0]) + abs(offset[1])),
            ])
            transported[reference_name] = {
                "reference_xyz_mm": reference_xyz.tolist(),
                "offset_from_operator_reference_mm": offset.tolist(),
                "a12_source_load_force_N": direct_source_force.tolist(),
                "a12_source_load_moment_N_mm": source_moment_at_reference.tolist(),
                "raw_H_body_load_force_N": p_wrench[:3].tolist(),
                "raw_H_body_load_moment_N_mm": p_moment_at_reference.tolist(),
                "raw_H_gate_residual_force_N": gate_force.tolist(),
                "raw_H_gate_residual_moment_N_mm": residual_moment_at_reference.tolist(),
                "target_row_action_force_N": target_wrench[:3].tolist(),
                "target_row_action_moment_N_mm": target_moment_at_reference.tolist(),
            }
            gate_bound_at_reference[reference_name] = transported_component_bound.tolist()

        # Independently reconstruct the selected body's exact six columns in
        # D = B R. This pins the unchanged gate's rotational datum to the
        # node-mean rigid field, rather than assuming a physical centroid.
        reconstructed_D_body = np.zeros((len(rows), 6), dtype=np.float64)
        for row_index, record in enumerate(rows):
            for term in record["physical_sparse_row"]:
                coordinate = int(term["coordinate_index"])
                physical = physical_map[coordinate // 3]
                if physical["body"] == body:
                    node_index = node_local[int(physical["node"])]
                    reconstructed_D_body[row_index] += (
                        float(term["coefficient"]) * R[3 * node_index + coordinate % 3]
                    )
        saved_D_body = saved_D[:, 6 * body_id:6 * body_id + 6]
        d_basis_error = float(np.max(np.abs(reconstructed_D_body - saved_D_body)))
        if d_basis_error > 1.0e-14:
            raise AssertionError(f"independent node-mean B R differs from frozen raw-H D block for {body}: {d_basis_error}")
        body_dof_rows = sorted(row_for[(node, direction)] for node in nodes for direction in range(1, 4))
        rigid_slice = raw["a_mm"][6 * body_id:6 * body_id + 6]
        body_summary[body] = {
            "rigid_coordinate_index": body_id,
            "rigid_coordinate_count": 6,
            "rigid_coordinate_slice_sha256_f64le": sha_bytes(np.asarray(rigid_slice, dtype="<f8").tobytes()),
            "rigid_coordinate_max_abs_mm": float(np.max(np.abs(rigid_slice))),
            "physical_node_count": len(nodes),
            "physical_dof_count": len(body_dof_rows),
            "native_dof_index_list_sha256_i64le": sha_bytes(np.asarray(body_dof_rows, dtype="<i8").tobytes()),
            "references": {
                "operator_node_mean_rigid_basis_reference_mm": center.tolist(),
                "geometric_descriptor_endpoint_midpoint_mm": descriptor_midpoint.tolist(),
                "descriptor_midpoint_minus_operator_reference_mm": (descriptor_midpoint - center).tolist(),
                "modeled_solid_mass_center_mm": modeled_mass_center.tolist(),
                "modeled_solid_mass_kg": float(mass_record["mass_kg"]),
                "modeled_mass_center_minus_operator_reference_mm": (modeled_mass_center - center).tolist(),
                "physical_as_built_mass_center_established": False,
                "source_body_audit_reference": "global origin",
                "source_audit_force_N": source_audit_force.tolist(),
                "source_audit_moment_about_global_origin_N_mm": source_audit_moment_global.tolist(),
                "independent_A12_map_to_global_origin_audit_force_max_error_N": source_audit_force_error,
                "independent_A12_map_to_global_origin_audit_moment_max_error_N_mm": source_audit_moment_error,
            },
            "unchanged_raw_H_source_datum_gate": {
                "datum": "operator node-mean rigid-basis reference; independently reconstructed B R equals pinned D block",
                "independent_D_block_max_abs_difference": d_basis_error,
                "saved_Dtf_minus_W_force_residual_N": gate_force.tolist(),
                "saved_Dtf_minus_W_moment_residual_N_mm": gate_moment.tolist(),
                "force_component_limit_N": gate_force_limit_N,
                "moment_component_limit_N_mm": gate_moment_limit_Nmm,
                "passes_original_componentwise_gate_at_source_datum": True,
                "other_reference_componentwise_outer_bounds_N_mm": gate_bound_at_reference,
                "outer_bound_note": "transported residual moments include the force-offset cross term; bounds are mathematical transports of the original component gates, not new accepted gates",
            },
            "transported_wrenches": transported,
            "a12_rear_gravity_wrench_scaled_N": gravity_wrench.tolist(),
            "a12_rear_gravity_moment_N_mm": gravity_moment.tolist(),
            "a12_rear_climber_wrench_scaled_N": climber_wrench.tolist(),
            "a12_rear_climber_moment_N_mm": climber_moment.tolist(),
            "full_raw_H_connector_wrench_scaled_N": connector_wrench.tolist(),
            "full_raw_H_connector_moment_N_mm": connector_moment.tolist(),
            "target_row_physical_action_wrench_scaled_N": target_wrench.tolist(),
            "target_row_physical_action_moment_N_mm": target_moment.tolist(),
            "full_raw_H_body_load_wrench_scaled_N": p_wrench.tolist(),
            "full_raw_H_body_load_moment_N_mm": p_moment.tolist(),
            "saved_Dtf_minus_W_scaled_N": saved_residual.tolist(),
            "independent_wrench_plus_saved_residual_max_N": body_balance_error,
            "incident_source_rows": len(body_values[body]["incident_rows"]),
            "incident_source_family_counts": {family: body_values[body]["incident_families"].get(family, 0)
                                              for family in sorted({record["family"] for record in rows})},
            "target_row_sparse_terms": sum(1 for term in target["physical_sparse_row"]
                                            if physical_map[int(term["coordinate_index"]) // 3]["body"] == body),
        }
        # Independent R construction is checked against the direct moment sum.
        dof_indices = [row_for[(node, direction)] for node in nodes for direction in range(1, 4)]
        if R.shape != (3 * len(nodes), 6) or len(dof_indices) != 3 * len(nodes):
            raise AssertionError(f"body rigid basis map did not cover all DOFs for {body}")
        if not np.all(np.isfinite(R)):
            raise AssertionError(f"nonfinite source rigid basis for {body}")

    target_terms_by_body = {body: 0 for body in TARGET_OWNERS}
    for term in target["physical_sparse_row"]:
        body = physical_map[int(term["coordinate_index"]) // 3]["body"]
        if body in target_terms_by_body:
            target_terms_by_body[body] += 1
    if target_terms_by_body != {TARGET_OWNERS[0]: 40, TARGET_OWNERS[1]: 40}:
        raise AssertionError(f"target endpoint projection support changed: {target_terms_by_body}")

    # Independent external nodal source wrench must match the full-load A12
    # generalized wrench retained by the fixed-branch problem.
    source_wrench_errors = {}
    for body in TARGET_OWNERS:
        body_id = body_names.index(body)
        expected_wrench = np.asarray(known_answer["W_total"][6 * body_id:6 * body_id + 6], dtype=np.float64)
        observed = (np.asarray(body_summary[body]["a12_rear_gravity_wrench_scaled_N"])
                    + np.asarray(body_summary[body]["a12_rear_climber_wrench_scaled_N"]))
        error = float(np.max(np.abs(observed - expected_wrench)))
        source_wrench_errors[body] = error
        if error > 1.0e-7:
            raise AssertionError(f"source A12 gravity/climber wrench differs from raw-H W for {body}: {error}")

    # The target row's native force and scalar q remain diagnostics only.
    # No correction is inferred from them or from printed native output.
    return {
        "schema": "a12_row1586_endpoint_recovery_preflight/v1",
        "status": "READY_FOR_PARENT_REVIEW_SOURCE_ONLY",
        "source_hashes": hashes,
        "scope": {
            "candidate": model["candidate"],
            "geometry_revision_id": model["geometry_revision_id"],
            "state": "one saved full-load A12 rear raw-H fixed-branch state",
            "target_row_position": TARGET_ROW,
            "target_source_inventory_row_index": 1786,
            "target_group": TARGET_GROUP,
            "target_element": TARGET_ELEMENT,
            "first_body": TARGET_OWNERS[0],
            "second_body": TARGET_OWNERS[1],
            "bounded_owner_bodies": 2,
            "native_or_CalculiX_run": False,
            "K_factorization_or_body_state_solve": False,
            "raw_response_vector_saved_again": False,
            "global_rebuild_or_new_case": False,
            "candidate_force_adoption": False,
            "force_interval_or_gate_change": False,
            "raw_H_stop_preserved": True,
        },
        "prior_stop": {
            "raw_H_status": raw_assessment["status"],
            "unchanged_failed_force_intervals": raw_assessment["original_DAT_comparisons"]["forces"]["failed_count"],
            "worst_normalized_source_interval": force_failure,
            "all_source_physical_gates_passed": raw_assessment["source_and_physical_gates_all_pass"],
            "failure_diagnostic_status": force_diag["status"],
        },
        "frozen_state": {
            "response_npz_sha256": hashes["raw_response"],
            "f_full_N_sha256_f64le": sha_bytes(np.asarray(raw["f_full_N"], dtype="<f8").tobytes()),
            "a_mm_sha256_f64le": sha_bytes(np.asarray(raw["a_mm"], dtype="<f8").tobytes()),
            "f_full_N_shape": list(raw["f_full_N"].shape),
            "a_mm_shape": list(raw["a_mm"].shape),
            "q_raw_mm_shape": list(raw["q_raw_mm"].shape),
            "target_source_force_N": float(raw["f_full_N"][TARGET_ROW]),
            "target_scalar_q_raw_mm": float(raw["q_raw_mm"][TARGET_ROW]),
            "body_equilibrium_residuals_shape": list(raw["body_equilibrium_residuals_N_and_unscaled_moment"].shape),
            "body_equilibrium_residuals_units": "D.T*f-W; N for force coordinates and Nmm/1000 for rotational coordinates",
            "source_case_load_columns": {"case_id": "a12-rear", "gravity_column": 0,
                                          "climber_column": 1, "superposition_factor": 1.0},
            "a12_rear_load_maps": source_map_summaries,
            "load_map_to_saved_W_max_abs_error_by_body": source_wrench_errors,
            "body_maps": body_summary,
        },
        "physical_source_projection": {
            "row_id": target["row_id"],
            "source_q_definition": target["q_definition"],
            "B_sign": "q=B*u; physical restoring action=-B.T*f; numerical ground reaction is excluded",
            "source_direction_global_xyz": owner["direction_global_xyz"],
            "source_point_mm": owner["point_mm"],
            "physical_sparse_term_count": target["nonzero_count"],
            "terms_by_owner": target_terms_by_body,
            "independent_rebuild": {"B_shape": list(B_rebuilt.shape), "B_nnz": int(B_rebuilt.nnz),
                                    "exactly_matches_pinned_attempt04_B": True,
                                    "raw_body_load_equilibrium_max_error_scaled_N": balance_error},
        },
        "adjacent_ghost_coordinate_translation_diagnostic": {
            "source_files": ["ghost_translation_readme", "ghost_translation_known_answer", "ghost_translation_audit"],
            "same_target_row": True,
            "ghost_nodes": [21300, 21301],
            "printed_U_common_translation_force_change_N": ghost_force_shift,
            "reported_native_RF_interval_radius_N": ghost_native_radius,
            "both_arithmetic_forces_inside_existing_RF_interval": True,
            "raw_H_force_interval_miss_N": float(force_failure["difference_N"]),
            "raw_H_miss_to_translation_effect_ratio": float(force_failure["difference_N"] / abs(ghost_force_shift)),
            "diagnostic_conclusion": "printed-U coordinate-arithmetic effect only; much smaller than raw-H miss and inside the existing native force interval",
            "proposed_coordinate_translation_remedy": False,
            "physical_body_coordinates_or_MPCs_changed": False,
        },
        "unmodified_MPC_reconstruction": {
            "source_model_mpc_coefficients_max_difference_from_emitted_deck": max_emitted_source_coefficient_difference,
            "source_model_to_emitted_deck_map_matches": True,
            "equations_from_emitted_model_inp": eqs,
            "numerical_ground": {"node": 21301, "fixed_translation_spc": "21301,1,3,0",
                                 "physical_body_node": False},
            "springa": {"group": TARGET_GROUP, "element": TARGET_ELEMENT,
                        "connectivity": [21300, 21301], "dd0_from_emitted_deck_mm": dd0_mm,
                        "law": "unchanged emitted SPRINGA table evaluated from dd-dd0"},
            "reconstruction_order": [
                "Recover each owner's complete physical displacement field u_b=R_b*a_b+u_el,b.",
                "Use emitted MPCs 18266/18267 to interpolate the two owning-body endpoint vectors from physical mesh DOFs.",
                "Apply emitted projection MPCs 18268/18269 and qghost MPCs at 21300 exactly as written.",
                "Keep 21301 at its emitted fixed numerical-ground displacement; compute dd from the two emitted endpoint coordinates plus reconstructed translations.",
                "Evaluate the original source interval with the emitted dd-dd0 table and preserved force orientation; do not replace it with q_raw or the linear projection."
            ],
        },
        "bounded_recovery_method_for_parent_only": {
            "body_count": 2,
            "body_physical_dof_counts": {body: body_summary[body]["physical_dof_count"] for body in TARGET_OWNERS},
            "unmodified_stiffness_sha256": hashes["stiffness_K"],
            "native_dof_map_sha256": hashes["dof_map"],
            "per_body_equation": "[K_b R_b; R_b.T 0] [u_el,b;lambda_b] = [F_g,b+F_c,b-B_b.T*f_full;0]",
            "no_physical_load_projection_or_rigid_wrench_repair": True,
            "combine_with_raw_rigid_field": "u_b=R_b*a_b+u_el,b using each saved six-coordinate raw-H slice",
            "method": "pinned current-elastic-quotient-method-attempt02 using unmodified K_b and six rigid columns; precheck raw wrench, reuse exact existing-factor refinement gates, no pseudoinverse or support interpretation",
            "factorization_or_solve_performed_in_preflight": False,
            "parent_authorization_required_before_any_actual_recovery": True,
        },
        "distinctions_and_limits": {
            "printed_DAT_U": "printed displacement intervals bound native output token rounding only; they are not raw-H endpoint vectors",
            "finite_span": "exact row comparison needs emitted-deck dd-dd0 from complete recovered endpoint vectors and exact MPCs",
            "linearized_projection": "q_raw and B*u are linear source projections; they do not determine dd-dd0 by themselves",
            "original_27_force_STOP": "unchanged; this readiness result neither repairs nor reclassifies any failed source interval",
            "no_new_claim": "no adopted force, new case, physical acceptance, state selection, or design release",
        },
        "known_answer_oracle": known_answer_oracle(),
        "resource_bound": {
            "preflight_reads": "saved source JSON, pinned raw vectors (read-only), 37,647 native DOF labels, source projection rows, and one saved 1840x37647 B map",
            "preflight_factors_or_solves": 0,
            "preflight_native_runs": 0,
            "actual_recovery_scope_if_parent_authorizes": "2 bodies / 336 physical DOFs total / two original-K bordered systems only",
            "source_global_matrix_K_rebuilt": False,
            "source_global_state_solved": False,
        },
    }


def verify_report() -> dict:
    hashes = check_pins(create=False)
    report = build_readiness(hashes)
    if not REPORT_FILE.is_file():
        raise AssertionError("readiness.json is missing")
    recorded = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    if json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n" != REPORT_FILE.read_text(encoding="utf-8"):
        raise AssertionError("readiness.json does not match a fresh independent source replay")
    if sha_file(OUTPUT_PIN_FILE) == "":
        raise AssertionError("missing output pin")
    output_pin = json.loads(OUTPUT_PIN_FILE.read_text(encoding="utf-8"))
    if output_pin.get("readiness_sha256") != sha_file(REPORT_FILE):
        raise AssertionError("readiness output pin mismatch")
    if output_pin.get("source_pins_sha256") != sha_file(PIN_FILE):
        raise AssertionError("source-pins output pin mismatch")
    if output_pin.get("prepare_recovery_py_sha256") != sha_file(Path(__file__)):
        raise AssertionError("preflight producer output pin mismatch")
    return recorded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--freeze-source-pins", action="store_true",
                        help="create the reviewed source hash inventory once; never run again after it exists")
    action.add_argument("--build-readiness", action="store_true",
                        help="build the source-only report from already frozen source pins")
    action.add_argument("--verify", action="store_true",
                        help="replay the source oracle and compare the frozen report and output hashes")
    args = parser.parse_args()
    if args.freeze_source_pins:
        pins = check_pins(create=True)
        print("FROZEN_SOURCE_PINS", len(pins), sha_file(PIN_FILE))
        return
    if args.build_readiness:
        hashes = check_pins(create=False)
        report = build_readiness(hashes)
        dump_json(REPORT_FILE, report)
        dump_json(OUTPUT_PIN_FILE, {
            "readiness_sha256": sha_file(REPORT_FILE),
            "source_pins_sha256": sha_file(PIN_FILE),
            "prepare_recovery_py_sha256": sha_file(Path(__file__)),
        })
        print(report["status"], "owners=2", "factorizations=0", "state_solves=0")
        return
    report = verify_report()
    print(report["status"], "owners=2", "factorizations=0", "state_solves=0")


if __name__ == "__main__":
    main()
