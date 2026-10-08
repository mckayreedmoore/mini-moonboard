"""Fixed-q panel/backing markers on authenticated saved own frontfaces.

This observes the existing admitted first-order coefficients with the frozen
finite point/surface maps. Every original port and every own face survives.
Unsupported/reconstruction/projection failures remain explicit unknowns.
No contact force, integration area, response law or geometry is changed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
TEST = OWN.with_name("test_mapped_diagnostic.py")
PREFIX = str(OWN.parent.relative_to(ROOT)) + "/"
REUSE = {
    PREFIX + "mapped_coupon.py": "fcf2d116f4b325a14f6f827ded6ecde7b9351c6ad13085ae5033bd23506ca64c",
    PREFIX + "frontfaces.json": "124f6ee5420c314a1e1a556126d089df4725f99f067389ed72fc2b5ea087ff5a",
    PREFIX + "plan.json": "63393392d0cd9043538565e024bc31038de2ff25c46bf295d5f9f3153c4bce59",
    PREFIX + "independent-frontface-review.json": "a63d94c273b3c4f4ba7f7bcfd0a2dbea63875488b283172ebe8d435d1d54fb57",
    PREFIX + "mapped-coupon-result.json": "a81616674cea679d0689258418bc29dea5b64fabe5dd804b21da431015b01627",
}


def load(path, expected, name):
    import hashlib
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
        raise ValueError("exact reuse source required: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
        raise ValueError("reuse source changed while loading: " + str(path))
    return module


reuse = load(OWN.with_name("mapped_coupon.py"), REUSE[PREFIX + "mapped_coupon.py"], "backing_marker_frozen_composition")
query, surface, domains = reuse.query, reuse.surface, reuse.domains
finite, panels = reuse.finite, reuse.panels
LOADED_SHA, TEST_SHA = query.sha(OWN), query.sha(TEST)
ERRORS = (ValueError, np.linalg.LinAlgError, FloatingPointError)


def own_pins():
    query.require(query.sha(OWN) == LOADED_SHA and query.sha(TEST) == TEST_SHA, "loaded marker/test bytes changed")
    return {str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA}


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(item) for item in value]
    return value


def error_record(exc, operation):
    return {"operation": operation, "exception_type": type(exc).__name__, "message": str(exc)}


def prepare_face(face):
    """Validate saved ownership hashes; reconstruct supported trims once."""
    query.require(query.canonical(face["signature"]) == face["signature_sha256"]
        and query.canonical(face["exact_parameter_geometry"]) == face["exact_parameter_geometry_sha256"],
        "own face canonical geometry differs")
    kinds = sorted({edge["curve_type"] for wire in face["exact_parameter_geometry"]["ordered_wires"]
                    for edge in wire["ordered_edges"]})
    supported = set(kinds) <= {"LINE", "CIRCLE"}
    query.require(face["saved_LINE_CIRCLE_classifier_applicable"] == supported,
                  "own trim support flag differs from actual exported curve types")
    domain, failure = None, None
    if supported:
        try:
            domain = domains.FaceDomain(face["signature"])
        except ERRORS as exc:
            failure = error_record(exc, "saved_LINE_CIRCLE_domain_reconstruction")
    return {"face": face, "domain": domain, "domain_error": failure, "curve_types": kinds}


def trim_at(prepared, point):
    """A bounding box excludes only; its interior never supplies occupancy."""
    face, domain = prepared["face"], prepared["domain"]
    bounds = np.asarray(face["signature"]["bounds_xyz_mm"], dtype=float).reshape(3, 2)
    excess = float(np.max(np.maximum(bounds[:, 0] - point, point - bounds[:, 1])))
    classification, failure = None, None
    if domain is not None:
        try:
            classification = domain.classify(point)
        except ERRORS as exc:
            failure = error_record(exc, "saved_own_trim_classification")
    outside = bool(excess > domains.EDGE_TOL_MM)
    return {"classification": classification, "classification_error": failure,
        "saved_own_bbox_maximum_excess_mm": max(0., excess), "definitely_outside_saved_own_bbox": outside,
        "definitely_exterior": bool(outside or classification and classification["location"] == "exterior"),
        "descriptor_plane_disagrees_with_authoritative_projection": bool(classification
            and classification["location"] == "off_reference_plane"),
        "inside_bbox_is_occupancy_proof": False}


def panel_marker(mapping, q, panel, point):
    """Frozen position plus its actual rear-offset surface-coordinate chart.

    Differentiate the existing Ritz midsurface and its normal offset; these
    are geometry derivatives, never force/energy/tangent operators. Preserve
    the saved axes rather than replacing their small Gram error by a rotation.
    """
    row = mapping["panels"][panel]
    axes, origin = np.asarray(row["axes_columns_xyz"]), np.asarray(row["origin_xyz_mm"])
    local = (np.asarray(point) - origin) @ axes
    basis = panels.SheetBasis(row["basis_width_mm"], row["basis_height_mm"], row["basis_order"] - 3)
    query.require(np.array_equal(basis.knots, row["basis_knots_normalized"]), "saved marker panel basis differs")
    xy = np.clip(local[:2], [0., 0.], [basis.width, basis.height])
    query.require(np.max(abs(local[:2] - xy)) <= 1e-7, "original panel backing point outside material chart")
    coef = np.asarray(q)[np.asarray(row["global_dof_indices"])].reshape(3, basis.size)
    deriv = lambda dx, dy: coef @ basis.values(xy[None], dx, dy)[0]
    rx, ry = np.array([1., 0., 0.]) + deriv(1, 0), np.array([0., 1., 0.]) + deriv(0, 1)
    rxx, rxy, ryy = deriv(2, 0), deriv(1, 1), deriv(0, 2)
    cross = np.cross(rx, ry)
    length = float(np.linalg.norm(cross))
    query.require(np.isfinite(length) and length > 0., "singular panel midsurface marker")
    normal = cross / length
    cx, cy = np.cross(rxx, ry) + np.cross(rx, rxy), np.cross(rxy, ry) + np.cross(rx, ryy)
    nx, ny = (cx - normal * (normal @ cx)) / length, (cy - normal * (normal @ cy)) / length
    delta = local[:2] - xy
    inside = (local[:2] >= 0.) & (local[:2] <= [basis.width, basis.height])
    # Match the frozen point map's clipping/extrapolation branch. At the
    # material boundary this is the derivative from its own interior side.
    tangent = axes @ np.column_stack((
        rx + inside[0] * (delta[0] * rxx + delta[1] * rxy + local[2] * nx),
        ry + inside[1] * (delta[0] * rxy + delta[1] * ryy + local[2] * ny)))
    rear_cross = np.cross(tangent[:, 0], tangent[:, 1])
    rear_length = float(np.linalg.norm(rear_cross))
    query.require(np.isfinite(rear_length) and rear_length > 0., "singular panel rear-offset marker")
    port = finite.current_pose_from_map(mapping, panel, point, q, allow_edge_extension=False)
    director = np.asarray(port["current_vector_xyz"])
    determinant = float(np.linalg.det(np.column_stack((tangent, axes @ normal))))
    query.require(np.isfinite(determinant) and determinant > 0., "inverted panel normal-offset marker chart")
    return {"current_rear_point_xyz_mm": port["position_xyz_mm"].tolist(),
        "current_rear_outward_geometric_normal_xyz": (-rear_cross / rear_length).tolist(),
        "frozen_midsurface_front_normal_vector_xyz": director.tolist(),
        "rear_tangent_wrt_panel_local_xy": tangent.tolist(), "rear_offset_chart_determinant": determinant,
        "rear_surface_metric_minimum_eigenvalue": float(np.linalg.eigvalsh(tangent.T @ tangent)[0]),
        "reference_panel_local_xyz_mm": local.tolist(), "reference_panel_xy_clipping_mm": (local[:2] - xy).tolist(),
        "panel_xy_derivative_from_material_interior_side_at_boundary": bool(np.any(xy == [0., 0.])
            or np.any(xy == [basis.width, basis.height])),
        "panel_xy_point_uses_frozen_tolerance_edge_extrapolation": bool(np.any(delta != 0.)),
        "source_axes_Gram_maximum_error": float(np.max(abs(axes.T @ axes - np.eye(3)))),
        "rear_geometric_vs_frozen_normal_angle_rad": float(np.arctan2(np.linalg.norm(np.cross(rear_cross / rear_length, director)),
                                                                          (rear_cross / rear_length) @ director)),
        "new_panel_rotation_frame_or_response_assigned": False}


def reference_face_marker(source_point, prepared):
    """Retain source planes and initial trim even if a current marker fails."""
    face = prepared["face"]
    exact = face["exact_parameter_geometry"]
    origin, normal = np.asarray(exact["plane_origin_xyz_mm"]), np.asarray(exact["oriented_normal_xyz"])
    point = np.asarray(source_point)
    offset = float((point - origin) @ normal)
    initial_point = point - offset * normal
    return {"face_id": face["face_id"], "signature_sha256": face["signature_sha256"],
        "exact_parameter_geometry_sha256": face["exact_parameter_geometry_sha256"],
        "actual_reference_plane_origin_xyz_mm": origin.tolist(), "actual_reference_plane_normal_xyz": normal.tolist(),
        "source_port_to_actual_plane_signed_offset_mm": offset,
        "initial_reference_projected_marker_xyz_mm": initial_point.tolist(),
        "initial_reference_actual_plane_uv_mm": (surface.plane_basis(normal).T @ (initial_point - origin)).tolist(),
        "initial_reference_trim": trim_at(prepared, initial_point),
        "exported_saved_curve_types": prepared["curve_types"], "saved_domain_reconstruction_error": prepared["domain_error"],
        "saved_domain_report": prepared["domain"].report() if prepared["domain"] is not None else None,
        "source_reference_port_replaced_or_snapped": False, "projection_error": None,
        "local_closest_point": None, "current_reference_trim": None,
        "opposed_current_outward_normal_dot": None, "smooth_local_piece_projection_with_opposed_faces": None,
        "current_overlap_area_or_pressure_proven": False}


def observe_face(mapping, q, receiver, source_point, panel, prepared):
    """One exact saved plane/piece, preserving source-port offset and errors."""
    record = reference_face_marker(source_point, prepared)
    origin = np.asarray(record["actual_reference_plane_origin_xyz_mm"])
    normal = np.asarray(record["actual_reference_plane_normal_xyz"])
    initial_point = np.asarray(record["initial_reference_projected_marker_xyz_mm"])
    point = np.asarray(source_point)
    try:
        row = mapping["mechanical_bodies"][receiver]
        initial = surface.surface_state(row, q, initial_point, normal)
        original = surface.surface_state(row, q, point, normal)
        foot = surface.closest_point(row, q, origin, normal, panel["current_rear_point_xyz_mm"])
        current = surface.surface_state(row, q, foot["reference_footpoint_xyz_mm"], normal)
        trimmed = trim_at(prepared, np.asarray(foot["reference_footpoint_xyz_mm"]))
        facing = float(np.asarray(panel["current_rear_outward_geometric_normal_xyz"]) @ current["geometric_normal"])
        classification = trimmed["classification"]
        unknown = classification is None or classification["location"] == "off_reference_plane"
        smooth = None if unknown and not trimmed["definitely_exterior"] else bool(
            classification and classification["eligible_for_smooth_own_face_projection"]
            and foot["local_stationary_closest_point_certified"] and facing < 0.)
        record.update({"current_initial_projected_receiver_marker": serial(initial),
            "current_original_source_receiver_point": serial(original), "current_pullback_receiver_surface": serial(current),
            "local_closest_point": foot, "current_reference_trim": trimmed,
            "opposed_current_outward_normal_dot": facing, "smooth_local_piece_projection_with_opposed_faces": smooth})
    except ERRORS as exc:
        record["projection_error"] = error_record(exc, "current_own_material_surface_projection")
    return record


def union_summary(rows):
    """Necessary local markers only; shared seams/global uniqueness unresolved."""
    interior = [row["face_id"] for row in rows if row["current_reference_trim"]
        and row["current_reference_trim"]["classification"]
        and row["current_reference_trim"]["classification"]["location"] == "interior"]
    boundary = [row["face_id"] for row in rows if row["current_reference_trim"]
        and row["current_reference_trim"]["classification"]
        and row["current_reference_trim"]["classification"]["location"] == "boundary"]
    unresolved = [row["face_id"] for row in rows if row["projection_error"] or
        row["current_reference_trim"] is None or
        (row["current_reference_trim"]["classification"] is None
         or row["current_reference_trim"]["descriptor_plane_disagrees_with_authoritative_projection"])
        and not row["current_reference_trim"]["definitely_exterior"]]
    exterior = all(row["current_reference_trim"] and row["current_reference_trim"]["definitely_exterior"] for row in rows)
    location = ("interior_on_supported_piece" if interior else "unresolved" if unresolved else
                "piece_boundary_or_seam" if boundary else "exterior_to_all_pieces" if exterior else "unresolved")
    eligible = [row["face_id"] for row in rows if row["smooth_local_piece_projection_with_opposed_faces"] is True]
    return {"local_pullback_union_location": location, "supported_interior_piece_ids": interior,
        "supported_boundary_or_seam_piece_ids": boundary, "unresolved_piece_ids": unresolved,
        "certified_interior_opposed_piece_ids": eligible,
        "some_smooth_local_owned_piece_projection_available": True if eligible else None if unresolved else False,
        "global_closest_point_unique": False, "piece_seam_is_union_boundary_proven": False,
        "current_supported_area_or_force_admissibility_proven": False}


def observe_port(mapping, q, identity, source, action, prepared_faces):
    record = {"id": identity, "panel": source["first"], "receiver": source["second"],
        "original_reference_point_xyz_mm": source["point_xyz_mm"], "original_reference_area_weight_mm2": source["area_mm2"],
        "original_reference_panel_outward_normal_xyz": source["direction_xyz"],
        "recorded_linear_compression_n": action["compression_n"],
        "recorded_linear_force_on_first_xyz_n": action["force_on_first_xyz_n"],
        "recorded_linear_force_on_second_xyz_n": action["force_on_second_xyz_n"],
        "recorded_force_is_diagnostic_metadata_only": True, "panel_marker_error": None,
        "current_panel_marker": None, "own_face_markers": [], "all_original_owned_faces_retained": True,
        "new_force_or_area_computed": False, "current_contact_force_set_to_zero_or_port_dropped": False}
    try:
        panel = panel_marker(mapping, q, source["first"], source["point_xyz_mm"])
        record["current_panel_marker"] = panel
    except ERRORS as exc:
        record["panel_marker_error"] = error_record(exc, "current_panel_rear_marker")
        record["own_face_markers"] = [{**reference_face_marker(source["point_xyz_mm"], prepared),
            "projection_error": error_record(exc, "projection_not_attempted_due_panel_error")}
            for prepared in prepared_faces]
        record["union"] = union_summary(record["own_face_markers"])
        return record
    record["own_face_markers"] = [observe_face(mapping, q, source["second"], source["point_xyz_mm"], panel, face)
                                  for face in prepared_faces]
    record["union"] = union_summary(record["own_face_markers"])
    return record


def read_frontfaces(field):
    query.verify(REUSE)
    packet = json.loads((ROOT / (PREFIX + "frontfaces.json")).read_bytes())
    plan = json.loads((ROOT / (PREFIX + "plan.json")).read_bytes())
    review = json.loads((ROOT / (PREFIX + "independent-frontface-review.json")).read_bytes())
    query.require(packet["schema"] == "thin_bolted_cached_panel_backing_frontfaces/v1"
        and packet["counts"] == {"actual_frontfaces": 57, "backing_ports": 530, "own_frontplanes": 16,
                                "panel_receiver_groups": 22, "panels": 6, "queried_finished_BREP_bodies": 16}
        and packet["original_source_plane_groups"] == plan["panel_receiver_groups"]
        and review["independent_review_checks_pass"] and review["current_q_or_forces_consumed"] is False
        and packet["current_field_identity"] == {key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "exact reviewed current own frontface packet required")
    pins = query.join(REUSE, packet["source_sha256"], plan["source_sha256"], review["source_sha256"])
    query.verify(pins)
    owners, all_ids = {}, set()
    for own in packet["own_frontface_queries"]:
        receiver = own["receiver"]
        query.require(receiver not in owners and own["own_frontfaces"], "duplicate or empty own receiver")
        owners[receiver] = []
        for face in own["own_frontfaces"]:
            query.require(face["face_id"].startswith(receiver + "/") and face["face_id"] not in all_ids,
                          "duplicate or foreign own frontface")
            all_ids.add(face["face_id"])
            owners[receiver].append(prepare_face(face))
    query.require(len(owners) == 16 and len(all_ids) == 57, "complete own-frontface census required")
    return packet, owners, pins


def current_mapping(field, gate):
    """Pure frozen pose facade; never evaluate a shaft pose or K."""
    query.require(query.sha(surface.CONFIG) == surface.CONFIG_SHA and query.sha(surface.POSE) == surface.POSE_SHA,
                  "frozen source pose configuration required")
    config = json.loads(surface.CONFIG.read_bytes())
    cold = {row["path"] for row in config["cold_diagnostic_sources"]}
    pins = {path: sha for path, sha in config["source_sha256"].items() if path not in cold}
    query.verify(pins)
    keys = ("layout", "timber_unit_geometry", "geometry_cache", "panel_metadata", "panel_assessment", "integrated_geometry")
    layout, unit, cache, metadata, assessment, integrated = [json.loads((ROOT / config[key]).read_bytes()) for key in keys]
    geometry = gate.read_complete_geometry()
    gate.linear.verify_timber_map(field, cache, geometry["grain_geometry"])
    method = load(surface.POSE, surface.POSE_SHA, "backing_marker_original_pose_facade")
    view = {**field, "response": {"diagnostic_last_q": field["response"]["q"]}}
    mapping, q, _ = method.make_map(view, layout, method.shaft_inputs(layout, unit, cache), metadata, assessment, integrated)
    query.require(mapping["ndof"] == 8088 and len(q) == 8088 and len(field["response"]["q"]) == 8018
        and np.array_equal(q[:8018], field["response"]["q"]) and np.array_equal(q[8018:], np.zeros(70))
        and len(mapping["panels"]) == 6, "exact diagnostic pose facade required")
    pins = query.join(pins, geometry["source_sha256"],
        {str(surface.CONFIG.relative_to(ROOT)): surface.CONFIG_SHA, str(surface.POSE.relative_to(ROOT)): surface.POSE_SHA})
    return mapping, q, pins


def consume(coupon_path, coupon_sha256, *, progress=None):
    """Parent execution after readiness: actual admission precedes any q map."""
    pins = query.join(query.PINS, reuse.PINS, REUSE, own_pins())
    query.verify(pins)
    query.require(query.sha(coupon_path) == coupon_sha256, "exact reviewed mapped-method coupon required")
    coupon = json.loads(Path(coupon_path).read_bytes())
    query.require(coupon["schema"] == "thin_bolted_panel_backing_mapped_diagnostic_coupon/v1"
        and coupon["method_checks_pass"] and coupon["candidate_q_or_forces_consumed"] is False
        and all(coupon["source_sha256"].get(path) == sha for path, sha in own_pins().items()),
        "matching source-bound method checks required")
    pins = query.join(pins, coupon["source_sha256"], {str(Path(coupon_path).resolve().relative_to(ROOT)): coupon_sha256})
    payload = (ROOT / query.FIELD).read_bytes()
    receipt = json.loads((ROOT / query.RECEIPT).read_bytes())
    gate = load(ROOT / query.GATE, query.PINS[query.GATE], "backing_marker_actual_current_gate")
    field, admitted = gate.require_admitted_payload(payload, receipt, admission_sha256=query.PINS[query.GATE])
    before, receipt_before = query.canonical(field), query.canonical(receipt)
    packet, owners, face_pins = read_frontfaces(field)
    mapping, q, map_pins = current_mapping(field, gate)
    q_before = q.copy()
    sources = gate.linear.panel_contact_sources()
    actions = {row["id"]: row for row in field["contact_actions"] if row["kind"] == "panel_contact"}
    expected_ids = {identity for group in packet["original_source_plane_groups"] for identity in group["source_contact_ids"]}
    query.require(len(sources) == len(actions) == len(expected_ids) == 530 and set(sources) == set(actions) == expected_ids,
                  "exact original 530 source/action/frontplane IDs required")
    rows = []
    for identity, source in sources.items():
        action = actions[identity]
        query.require((action["first"], action["second"], action["point_xyz_mm"]) ==
            (source["first"], source["second"], source["point_xyz_mm"])
            and all(action[key] == field[key] for key in ("state_id", "case_id", "accessory_placement")),
            "original backing owner/reference point/state differs")
        rows.append(observe_port(mapping, q, identity, source, action, owners[source["second"]]))
        if progress is not None:
            progress({"completed_ports": len(rows), "id": identity, "union": rows[-1]["union"]["local_pullback_union_location"]})
    pins = query.join(pins, admitted, face_pins, map_pins, surface.mechanics.source_pins())
    query.verify(pins)
    query.require(query.canonical(field) == before and query.canonical(receipt) == receipt_before
        and np.array_equal(q, q_before), "admitted sources or diagnostic coefficients mutated")
    faces = [face for row in rows for face in row["own_face_markers"]]
    return {"schema": "thin_bolted_admitted_current_panel_backing_mapped_markers/v1",
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "field_sha256": query.PINS[query.FIELD], "actual_admission_sha256": query.PINS[query.GATE],
        "admission_receipt_sha256": query.PINS[query.RECEIPT], "field_canonical_sha256": before,
        "source_q_canonical_sha256": query.canonical(field["response"]["q"]),
        "pure_pose_map_sha256": query.canonical(mapping), "source_sha256": pins,
        "counts": {**packet["counts"], "mapped_original_ports": len(rows), "mapped_face_piece_markers": len(faces)},
        "summary": {"all_ports": dict(Counter(row["union"]["local_pullback_union_location"] for row in rows)),
            "positive_recorded_compression_ports": dict(Counter(row["union"]["local_pullback_union_location"]
                for row in rows if row["recorded_linear_compression_n"] > 0.)),
            "panel_marker_errors": sum(row["panel_marker_error"] is not None for row in rows),
            "face_projection_errors": sum(row.get("projection_error") is not None for row in faces)},
        "mapped_backing_ports": rows, "all_original_ids_owners_forces_preserved": True,
        "candidate_K_response_native_or_CAD_evaluated": False, "new_equilibrated_or_physical_response_established": False,
        "current_contact_area_pressure_or_capacity_proven": False,
        "shaft_pose_or_added_gauge_consumed": False, "source_reference_datums_snapped": False,
        "limits": ["Fixed admitted linear q supplies diagnostic geometry, not a new equilibrated finite field or physical movement.",
            "All own pieces are retained. Unsupported curves and saved-domain failures remain unknown unless the saved bounding box proves exclusion.",
            "Supported trim classification uses the frozen descriptor-precision LINE/CIRCLE method; exact BREP coordinates define the unsnapped projection plane.",
            "Local stationary projections and their one-sided/endpoint flags do not establish global closest-point uniqueness, shared-seam normals or current overlap area.",
            "Original area weights and compression are metadata only; no force is removed, reset or admitted under a changed contact law."],
        "release": {"candidate_accepted": False, "complete_joint_acceptance": False, "capacity_established": False,
            "fabrication_released": False, "structural_released": False, "climbing_released": False}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coupon", type=Path, required=True)
    parser.add_argument("--coupon-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    query.require(not args.out.exists(), "preserve existing marker output")
    result = consume(args.coupon, args.coupon_sha256,
        progress=lambda event: print(json.dumps(event), flush=True) if event["completed_ports"] % 50 == 0 else None)
    result.update({"invocation_argv": list(sys.orig_argv), "working_directory": str(Path.cwd()),
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS")},
        "toolchain": query.toolchain()})
    query.write_exclusive(args.out, result)
    print(json.dumps({"output": str(args.out), "sha256": query.sha(args.out)}))


if __name__ == "__main__":
    main()
