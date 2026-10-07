"""Admitted contact-centre kinematics and a LOCAL INVERSE APPROXIMATION.

No CAD/BREP query, K, potential, Hessian, response or solve. Frozen material
point/director poses replay every reference cell, including zero-action cells.
The approximate pullback and its forward residual are inputs for a separate
parent-owned reference-shape query; no current footprint is established here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import re
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_frame as finite

ROOT, PACKET = finite.frame.ROOT, finite.frame.PACKET
FINITE_SOURCE = "scripts/thin_bolted_finite_frame.py"
FINITE_SHA256 = "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588"
GATE_SOURCE = "scripts/thin_bolted_timber_contact_admission.py"
GATE_SHA256 = "75011f4cfa042a46d8e45eb5716ae01df2edff3418b1439553afb04b14b14632"
GATE_MODULE = "scripts.thin_bolted_timber_contact_admission"
GATE_SCHEMA = "thin_bolted_independent_timber_contact_admission/v1"
GATE_KEY = "independent_finite_timber_contact_support_load_and_equilibrium_checks_pass"
PROOF = PACKET / "timber-face-contact-geometry-v4.json"
PROOF_SHA256 = "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a"
PROOF_SCHEMA = "thin_bolted_timber_face_contact_geometry/v1"
FIELD_SCHEMA = "thin_bolted_finite_frame_response/v1"
IDENTITY_KEYS = ("state_id", "case_id", "accessory_placement")
EXPECTED_CELL_COUNT = 272
EXPECTED_PAIR_COUNT = 6
REPLAY_POINT_TOL_MM = 1e-5
REPLAY_DIRECTOR_TOL = 1e-8
LOADED_PRODUCER_SHA256 = finite.frame.sha(Path(__file__))


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical_sha(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def vector(value, size=3):
    result = np.asarray(value, dtype=float)
    require(result.shape == (size,) and np.isfinite(result).all(), "finite vector of declared shape required")
    return result


def source_name(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def merge_verify_pins(*groups):
    pins = {}
    for group in groups:
        for name, expected in group.items():
            require(isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None
                    and (name not in pins or pins[name] == expected), "malformed or contradictory source pin")
            pins[name] = expected
    require(all(finite.frame.sha(ROOT/name) == expected for name, expected in pins.items()), "bound source bytes changed")
    return pins


def validate_timber_map(row, ndof):
    require(row.get("kind") == "timber", "contact hosts must use timber material point maps")
    centers, index = np.asarray(row["node_reference_centers_xyz_mm"], dtype=float), np.asarray(row["node_dof_indices"])
    stations = np.asarray(row["reference_stations_mm"], dtype=float)
    start, axis = vector(row["reference_start_xyz_mm"]), vector(row["reference_axis_xyz"])
    basis = np.asarray(row["storage_basis_columns_xyz"], dtype=float)
    require(centers.ndim == 2 and centers.shape[1] == 3 and len(centers) >= 2 and np.isfinite(centers).all()
            and index.shape == (len(centers), 6) and np.issubdtype(index.dtype, np.integer)
            and np.all(index >= 0) and np.all(index < ndof) and len(set(index.ravel().tolist())) == index.size,
            "complete distinct timber nodes/indices required")
    require(stations.shape == (len(centers),) and np.isfinite(stations).all() and np.all(np.diff(stations) > 0.)
            and abs(np.linalg.norm(axis)-1.) < 1e-8
            and np.max(abs(centers-start-stations[:, None]*axis)) < 1e-7,
            "ordered timber stations and exact reference centerline required")
    require(basis.shape == (3, 3) and np.isfinite(basis).all()
            and np.linalg.norm(basis.T@basis-np.eye(3)) < 1e-8 and abs(np.linalg.det(basis)-1.) < 1e-8,
            "proper timber storage basis required")


def station_info(row, point):
    """Raw station/domain flag BEFORE the frozen pose provider's clipping."""
    stations = np.asarray(row["reference_stations_mm"], dtype=float)
    station = float((vector(point)-vector(row["reference_start_xyz_mm"])) @ vector(row["reference_axis_xyz"]))
    inside = bool(stations[0] <= station <= stations[-1])
    i = int(np.clip(np.searchsorted(stations, station)-1, 0, len(stations)-2))
    fraction = float((station-stations[i])/(stations[i+1]-stations[i]))
    return {"raw_reference_axial_station_mm": station,
            "mapped_station_domain_mm": [float(stations[0]), float(stations[-1])],
            "inside_mapped_axial_station_domain": inside, "node_pair": [i, i+1],
            "raw_segment_fraction": fraction, "pose_provider_segment_fraction": float(np.clip(fraction, 0., 1.)),
            "pose_provider_station_clipping_used": not inside,
            "station_domain_is_trimmed_face_or_solid_occupancy": False}


def cell_kinematics(mapping, q, action, patch, cell):
    """Replay one material centre; no force, pressure, stiffness or footprint law."""
    first, second = patch["first"], patch["second"]
    x1, x2 = vector(action["reference_first_point_xyz_mm"]), vector(action["reference_second_point_xyz_mm"])
    nref2, nref1 = vector(patch["normal_from_second_to_first_xyz"]), vector(patch["first_outward_normal_xyz"])
    require(action["first"] == first and action["second"] == second and action["director_owner"] == second
            and action["first_port_kind"] == "point" and action["interaction_enabled"] is True,
            "own enabled paired timber material point/director required")
    require(np.array_equal(x1, cell["point_xyz_mm"]) and np.array_equal(x2, cell["point_xyz_mm"])
            and abs(np.linalg.norm(nref2)-1.) < 1e-8 and np.max(abs(nref1+nref2)) < 1e-8,
            "proof paired centres/opposing own reference normals differ")
    pose1 = finite.current_pose_from_map(mapping, first, x1, q, reference_director=nref1)
    pose2 = finite.current_pose_from_map(mapping, second, x2, q, reference_director=nref2)
    p1, p2 = vector(pose1["position_xyz_mm"]), vector(pose2["position_xyz_mm"])
    n1, n2 = vector(pose1["current_vector_xyz"]), vector(pose2["current_vector_xyz"])
    require(abs(np.linalg.norm(n1)-1.) < 1e-8 and abs(np.linalg.norm(n2)-1.) < 1e-8,
            "replayed own material face directors must be unit")
    require(np.max(abs(p1-vector(action["point_on_first_xyz_mm"]))) <= REPLAY_POINT_TOL_MM
            and np.max(abs(p2-vector(action["point_on_second_xyz_mm"]))) <= REPLAY_POINT_TOL_MM
            and np.max(abs(n2-vector(action["current_director_xyz"]))) <= REPLAY_DIRECTOR_TOL,
            "admitted current points/second outward director differ from mapped replay")
    R2 = np.column_stack([finite.current_pose_from_map(mapping, second, x2, q, reference_director=e)["current_vector_xyz"]
                          for e in np.eye(3)])
    require(np.linalg.norm(R2.T@R2-np.eye(3)) < 1e-8 and abs(np.linalg.det(R2)-1.) < 1e-8
            and np.max(abs(R2@nref2-n2)) < REPLAY_DIRECTOR_TOL,
            "same-station second material rotation differs from own director")
    delta = p1-p2
    gap = float(n2@delta)
    slip = delta-gap*n2
    angle = float(np.arccos(np.clip(-n1@n2, -1., 1.)))
    y = p1-gap*n2
    Xstar = x2+R2.T@(y-p2)
    station = station_info(mapping["mechanical_bodies"][second], Xstar)
    forward = vector(finite.current_pose_from_map(mapping, second, Xstar, q)["position_xyz_mm"])
    residual = forward-y
    return {"id": action["id"], "patch_id": patch["id"], "first": first, "second": second,
            "reference_cell_area_mm2": float(cell["area_mm2"]),
            "source_descriptor": copy.deepcopy(action["source_descriptor"]),
            "reference_first_centre_xyz_mm": x1.tolist(), "reference_second_centre_xyz_mm": x2.tolist(),
            "current_first_centre_xyz_mm": p1.tolist(), "current_second_centre_xyz_mm": p2.tolist(),
            "current_first_own_outward_material_normal_xyz": n1.tolist(),
            "current_second_own_outward_material_normal_xyz": n2.tolist(),
            "gap_opening_positive_mm": gap, "tangent_slip_xyz_mm": slip.tolist(),
            "tangent_slip_norm_mm": float(np.linalg.norm(slip)), "opposed_material_normal_angle_rad": angle,
            "current_projection_on_second_centre_director_plane_xyz_mm": y.tolist(),
            "same_reference_station_second_material_rotation_columns_xyz": R2.tolist(),
            "reference_first_station": station_info(mapping["mechanical_bodies"][first], x1),
            "reference_second_station": station_info(mapping["mechanical_bodies"][second], x2),
            "local_inverse_approximation": {"status": "LOCAL_INVERSE_APPROXIMATION",
                "reference_pullback_xyz_mm": Xstar.tolist(), "pullback_station": station,
                "forward_replayed_current_xyz_mm": forward.tolist(),
                "forward_minus_projection_xyz_mm": residual.tolist(),
                "forward_residual_distance_mm": float(np.linalg.norm(residual)),
                "exact_current_footprint_established": False}}


def recover_centres(field, proof):
    """Keep the exact six-pair/272-cell source census; never filter by force."""
    snapshot = canonical_sha({"map": field["finite_kinematic_map"], "q": field["response"]["q"],
                              "actions": field["finite_interaction_actions"], "proof": proof})
    mapping, q = field["finite_kinematic_map"], np.asarray(field["response"]["q"], dtype=float)
    require(isinstance(mapping["ndof"], int) and mapping["ndof"] > 0 and q.shape == (mapping["ndof"],)
            and np.isfinite(q).all(), "unchanged full mapped q required")
    original_q = q.copy()
    require(proof.get("schema") == PROOF_SCHEMA and len(proof["pairs"]) == EXPECTED_PAIR_COUNT,
            "exact six-pair contact proof required")
    pairs = {(row["first"], row["second"]): row for row in proof["pairs"]}
    require(len(pairs) == EXPECTED_PAIR_COUNT and len({row["id"] for row in pairs.values()}) == EXPECTED_PAIR_COUNT,
            "distinct own ordered contact pairs required")
    hosts = {host for pair in pairs for host in pair}
    for host in hosts:
        validate_timber_map(mapping["mechanical_bodies"][host], mapping["ndof"])
    selected_indices = np.concatenate([np.asarray(mapping["mechanical_bodies"][host]["node_dof_indices"]).ravel() for host in sorted(hosts)])
    require(len(set(selected_indices.tolist())) == len(selected_indices), "own timber maps overlap coefficient indices")
    actions = [row for row in field["finite_interaction_actions"] if row["kind"] == "timber_face_contact"]
    indexed = {row["id"]: row for row in actions}
    require(len(actions) == len(indexed) == EXPECTED_CELL_COUNT, "all272 distinct zero/loaded timber contact cells required")
    expected = [cell["id"] for patch in proof["patches"] for cell in patch["cells"]]
    require(len(expected) == len(set(expected)) == EXPECTED_CELL_COUNT and set(indexed) == set(expected),
            "saved contact action census differs from exact proof cells")
    result = []
    for patch in proof["patches"]:
        require((patch["first"], patch["second"]) in pairs, "contact patch has a foreign own pair")
        for cell in patch["cells"]:
            row, source = indexed[cell["id"]], indexed[cell["id"]]["source_descriptor"]
            require(all(row[key] == field[key] for key in IDENTITY_KEYS), "contact cell mixes field/state/case identity")
            require(row["id"] == source["cell_id"] == cell["id"] and source["patch_id"] == patch["id"]
                    and source["geometry_proof_sha256"] == PROOF_SHA256
                    and source["cell_area_mm2"] == cell["area_mm2"] > 0.
                    and source["patch_area_mm2"] == patch["area_mm2"], "own reference cell/area/proof source aliases differ")
            result.append({**{key: field[key] for key in IDENTITY_KEYS}, **cell_kinematics(mapping, q, row, patch, cell)})
    summaries = []
    metrics = {"largest_abs_gap": lambda r: abs(r["gap_opening_positive_mm"]),
               "largest_tangent_slip": lambda r: r["tangent_slip_norm_mm"],
               "largest_opposed_material_normal_angle": lambda r: r["opposed_material_normal_angle_rad"],
               "largest_inverse_forward_residual": lambda r: r["local_inverse_approximation"]["forward_residual_distance_mm"]}
    for pair, source_pair in pairs.items():
        own = [r for r in result if (r["first"], r["second"]) == pair]
        require(own, "own pair has no retained contact cells")
        summaries.append({"id": source_pair["id"], "first": pair[0], "second": pair[1],
            "cell_count": len(own), "retained_reference_cell_area_total_mm2": sum(r["reference_cell_area_mm2"] for r in own),
            "gap_range_mm": [min(r["gap_opening_positive_mm"] for r in own), max(r["gap_opening_positive_mm"] for r in own)],
            "pullback_outside_mapped_axial_station_domain_count": sum(not r["local_inverse_approximation"]["pullback_station"]["inside_mapped_axial_station_domain"] for r in own),
            "coherent_kinematic_witnesses": {name: copy.deepcopy(max(own, key=metric)) for name, metric in metrics.items()}})
    require(np.array_equal(q, original_q) and canonical_sha({"map": field["finite_kinematic_map"], "q": field["response"]["q"],
                           "actions": field["finite_interaction_actions"], "proof": proof}) == snapshot,
            "q/map/source contact ports were mutated during diagnostics")
    return {"contact_centre_rows": result, "own_pair_summaries": summaries,
            "retained_contact_cell_count": len(result), "own_pair_count": len(summaries)}


def consume(field_path, expected_field_sha256, *, admission_sha256):
    """Fixed corrected gate, explicit raw SHA, immutable bytes and source guards."""
    require(isinstance(expected_field_sha256, str) and re.fullmatch("[0-9a-f]{64}", expected_field_sha256) is not None,
            "explicit raw field SHA256 required")
    require(admission_sha256 == GATE_SHA256, "explicit fixed corrected gate SHA256 required")
    path = Path(field_path).resolve()
    payload = path.read_bytes()
    require(digest(payload) == expected_field_sha256, "raw field bytes differ from explicit SHA256")
    field = json.loads(payload)
    require(field.get("schema") == FIELD_SCHEMA and field.get("candidate") == "compact-floor-flush-thin-bolted-development"
            and field.get("response", {}).get("converged") is True and field.get("usable_conditional_actions") is True,
            "current converged corrected field required; no legacy/failed fallback")
    require(field.get("release") and not any(field["release"].values()), "analysis cannot authorize release")
    require(field["parameters"].get("timber_face_contact_geometry_sha256") == PROOF_SHA256,
            "fixed corrected contact geometry identity required")
    fixed = {FINITE_SOURCE: FINITE_SHA256, GATE_SOURCE: GATE_SHA256,
             source_name(PROOF): PROOF_SHA256, source_name(__file__): LOADED_PRODUCER_SHA256}
    pins = merge_verify_pins(finite.source_pins(), fixed)
    proof_payload = PROOF.read_bytes()
    require(digest(proof_payload) == PROOF_SHA256, "fixed proof bytes changed")
    proof = json.loads(proof_payload)
    gate = importlib.import_module(GATE_MODULE)
    require(Path(gate.__file__).resolve() == (ROOT/GATE_SOURCE).resolve()
            and gate.LOADED_PRODUCER_SHA256 == GATE_SHA256, "loaded corrected gate source/path differs")
    admission = gate.audit_timber_contact_state(payload)
    require(admission.get("schema") == GATE_SCHEMA and admission.get(GATE_KEY) is True
            and admission.get("field_sha256") == expected_field_sha256
            and admission.get("field_canonical_sha256") == canonical_sha(field)
            and all(admission.get(key) == field[key] for key in IDENTITY_KEYS)
            and admission.get("source_sha256", {}).get(GATE_SOURCE) == GATE_SHA256,
            "corrected admission does not bind exact raw/canonical/state/source identities")
    pins = merge_verify_pins(pins, admission["source_sha256"], field["source_sha256"], {source_name(path): expected_field_sha256})
    result = recover_centres(field, proof)
    merge_verify_pins(pins)
    require(path.read_bytes() == payload and PROOF.read_bytes() == proof_payload, "input/proof bytes changed during diagnostics")
    return {**result, "schema": "thin_bolted_admitted_timber_contact_centre_kinematics/v1",
            **{key: field[key] for key in ("candidate", "revision", *IDENTITY_KEYS, "parameters")},
            "field_sha256": expected_field_sha256, "source_sha256": pins, "corrected_admission": admission,
            "method": {"frozen_material_pose_replayed": True, "q_or_ports_mutated": False,
                "all_zero_and_loaded_cells_retained": True, "pullback": "LOCAL_INVERSE_APPROXIMATION",
                "CAD_BREP_query": False, "K_assembled": False, "potential_H_or_response_evaluated": False, "solve_run": False},
            "limits": ["Own outward directors are transported material normals, not reconstructed continuous deformed-surface geometric normals.",
                "Projection uses the second centre director plane; local inverse ignores station-dependent stretch/rotation. Forward residual and raw preclip domain flags accompany every pullback.",
                "No exact current footprint, trimmed-face/solid classification, overlap-loss, pressure, stiffness, strength, bound or adopted tolerance decision is issued."],
            "release": dict(finite.frame.RELEASE)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.field, args.field_sha256, admission_sha256=args.admission_sha256)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"path": str(args.out), "sha256": finite.frame.sha(args.out), "state_id": result["state_id"]}))


if __name__ == "__main__":
    main()
