"""First-order compression rows for the six authenticated timber interfaces.

Reuse the finished-face proof, linear point ports and existing unilateral
contact solver. This adapter supplies no solver, tangential restraint, preload,
finite-motion contact law or physical resistance.
"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_timber_face_contact as faces

OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FRAME_SHA = "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"
FACE_SHA = "9558a036f9f8b06fb6a1a1a711419aaa961f655e8f7fb02deb7808e8ade4ed8c"
METHOD_BASIS = "source-bound-linear-finished-paired-wood-compression-v1"
MAP_SCHEMA = "thin_bolted_linear_timber_coordinates/v1"


def source_pins(additional=None):
    return faces.source_pins(faces.merge_pins({OWN: LOADED_PRODUCER_SHA256,
        "scripts/thin_bolted_frame_mechanics.py": FRAME_SHA,
        "scripts/thin_bolted_timber_face_contact.py": FACE_SHA}, additional or {}))


def timber_coordinate_map(assembly):
    """Export only existing timber coordinates; no K or geometry preparation."""
    members = []
    for name, member in assembly.members.items():
        start, axis = np.asarray(member["start"]), np.asarray(member["axis"])
        stations, indices = np.asarray(member["stations"]), np.asarray(member["index"])
        faces.require(start.shape == axis.shape == (3,) and np.isfinite([start, axis]).all()
                      and abs(np.linalg.norm(axis)-1.) < 1e-8
                      and stations.ndim == 1 and len(stations) >= 2 and np.isfinite(stations).all()
                      and np.all(np.diff(stations) > 0.) and indices.shape == (len(stations), 6)
                      and np.issubdtype(indices.dtype, np.integer)
                      and np.all((indices >= 0) & (indices < assembly.ndof)), "invalid existing timber coordinates")
        members.append({"member": name, "node_dof_indices": indices.tolist(),
            "reference_start_xyz_mm": start.tolist(), "reference_axis_xyz": axis.tolist(),
            "reference_stations_mm": stations.tolist(),
            "node_reference_centers_xyz_mm": (start+stations[:, None]*axis).tolist(),
            "storage_basis_columns_xyz": np.eye(3).tolist()})
    all_indices = [i for member in members for row in member["node_dof_indices"] for i in row]
    faces.require(len(set(all_indices)) == len(all_indices), "timber coordinate indices overlap")
    return {"schema": MAP_SCHEMA, "ndof": int(assembly.ndof), "rotation_scale": frame.ROTATION_SCALE,
            "members": members, "action_datums": "reference world points; first-order rigid arms"}


def linear_contact_rows(assembly, descriptors):
    """Convert reused face descriptors into the existing positive-closing law."""
    result = []
    for row in descriptors:
        first, second = row["first"], row["second"]
        point, normal = faces.vector(row["reference_first_point_xyz_mm"]), faces.vector(row["reference_director_xyz"])
        faces.require(first in assembly.members and second in assembly.members and first != second,
                      "paired contact requires two existing timber hosts")
        faces.require(np.array_equal(point, row["reference_second_point_xyz_mm"])
                      and abs(np.linalg.norm(normal)-1.) < 1e-8 and row["axial_sign"] == -1.
                      and row["axial_tension_only"] is True and row["lateral_stiffness_n_mm"] == 0.
                      and row["radial_gap_mm"] == row["reference_axial_projection_mm"] == 0.,
                      "zero-gap friction-free compression descriptor required")
        stiffness = float(row["axial_stiffness_n_mm"])
        faces.require(np.isfinite(stiffness) and stiffness > 0., "positive finite normal stiffness required")
        closing = -(assembly.scalar_port(first, point, normal)-assembly.scalar_port(second, point, normal))
        result.append({"id": row["id"], "kind": "timber_face_contact", "first": first, "second": second,
            "point_xyz_mm": point.tolist(), "direction_xyz": normal.tolist(), "B": closing,
            "stiffness": stiffness, "source_descriptor": copy.deepcopy(row["source_descriptor"])})
    faces.require(len({row["id"] for row in result}) == len(result), "duplicate timber-face contact identity")
    return result


def prepare_linear_timber_faces(assembly, proof_path, expected_proof_sha256, *, bedding_n_mm3=1.,
                                scenario_id=faces.DEFAULT_SCENARIO_ID):
    """Prepare contacts on an existing assembly; preserve its objects and K."""
    source_pins()
    proof, pins = faces.read_proof(proof_path, expected_proof_sha256)
    descriptors = faces.describe_contacts(proof, bedding_n_mm3, scenario_id, proof_sha256=expected_proof_sha256)
    faces.require(len(descriptors) == 272 and len(proof["patches"]) == 6 and len(assembly.members) == 20,
                  "reviewed six-patch,272-cell,20-timber production census required")
    contacts = linear_contact_rows(assembly, descriptors)
    metadata = {"method": METHOD_BASIS, "contact_pair_count": 6, "contact_cell_count": 272,
        "parameters": {"linear_timber_face_contact_basis": METHOD_BASIS,
            "linear_timber_face_contact_geometry_sha256": expected_proof_sha256,
            "linear_timber_face_contact_bedding_n_mm3": float(bedding_n_mm3),
            "linear_timber_face_contact_scenario_id": scenario_id,
            "linear_timber_face_contact_cell_mm": proof["method"]["cell_size_mm"],
            "linear_timber_face_contact_producer_sha256": LOADED_PRODUCER_SHA256},
        "limits": ["Fixed source normals/reference points and linear rigid arms; current overlap and finite-motion applicability unresolved.",
            "Area-weighted declared bedding is not measured stiffness or a pressure/resistance bound.",
            "No tangential law, preload, clamp, physical work or release is authorized."]}
    return {"contacts": contacts, "coordinate_map": timber_coordinate_map(assembly), "metadata": metadata,
            "source_sha256": source_pins(pins)}


def stamp_recovered_actions(recovered, prepared, q):
    """Enrich existing recovery, retaining every zero row and both force duals."""
    source_pins(prepared["source_sha256"])
    q = np.asarray(q, dtype=float)
    faces.require(q.shape == (prepared["coordinate_map"]["ndof"],) and np.isfinite(q).all(),
                  "complete finite first-order saved vector required")
    expected = {row["id"]: row for row in prepared["contacts"]}
    existing = [row for row in recovered["contact_actions"] if row["kind"] == "timber_face_contact"]
    faces.require(len(existing) == len(expected) and {row["id"] for row in existing} == set(expected),
                  "all distinct timber-face actions, including zeros, required")
    enriched = {}
    for row in existing:
        contact = expected[row["id"]]
        closure = float((contact["B"] @ q)[0])
        force = max(closure, 0.)*contact["stiffness"]
        vector = force*np.asarray(contact["direction_xyz"])
        faces.require((row["first"], row["second"]) == (contact["first"], contact["second"])
                      and np.array_equal(row["point_xyz_mm"], contact["point_xyz_mm"])
                      and np.isfinite(row["compression_n"]) and abs(row["compression_n"]-force) < 1e-7
                      and np.allclose(row["force_on_first_xyz_n"], vector, rtol=0., atol=1e-7),
                      "recovered timber-face datum or unmodified compression law differs")
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            faces.require(np.array_equal(faces.vector(row.get(key, [0., 0., 0.])), np.zeros(3)),
                          "linear point contact cannot supply a free couple")
        if "force_on_second_xyz_n" in row:
            faces.require(np.allclose(faces.vector(row["force_on_second_xyz_n"]), -vector, rtol=0., atol=1e-7),
                          "recovered timber-face force dual differs")
        enriched[row["id"]] = {**row, "direction_xyz": contact["direction_xyz"],
            "cell_area_mm2": contact["source_descriptor"]["cell_area_mm2"],
            "penalty_stiffness_n_mm": contact["stiffness"], "relative_closure_mm": closure,
            "force_on_second_xyz_n": (-vector).tolist(),
            "moment_on_first_at_point_xyz_nmm": [0., 0., 0.], "moment_on_second_at_point_xyz_nmm": [0., 0., 0.],
            "moment_at_point_model_xyz_nmm": [0., 0., 0.],
            "source_descriptor": copy.deepcopy(contact["source_descriptor"]),
            "action_wrench_uses_reference_point_first_order": True,
            "physical_pressure_or_current_overlap_resolved": False}
    result = {**recovered, "contact_actions": [enriched.get(row["id"], row) for row in recovered["contact_actions"]],
        "timber_face_contact_actions": [enriched[row["id"]] for row in prepared["contacts"]],
        "linear_timber_coordinate_map": copy.deepcopy(prepared["coordinate_map"]),
        "linear_timber_face_method": METHOD_BASIS}
    source_pins(prepared["source_sha256"])
    return result
