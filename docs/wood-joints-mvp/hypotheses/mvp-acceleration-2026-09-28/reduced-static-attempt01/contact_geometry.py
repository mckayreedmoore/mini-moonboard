"""Export geometry-only contact and existing z=0 floor patches from pinned STEP."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

from scripts import wood_joint_current_contact_graph as contact_graph


MANIFEST_REL = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
GRAPH_REL = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "complete-contact-graph-attempt02.json"
)
EQUILIBRIUM_REL = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "global-equilibrium.json"
)
EQUILIBRIUM_SCRIPT_REL = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "global_equilibrium_screen.py"
)
CONTACT_GRAPH_HELPER_REL = "scripts/wood_joint_current_contact_graph.py"
RECEIVER_SCREEN_HELPER_REL = "scripts/wood_joint_current_receiver_screen.py"
MANIFEST_SHA256 = "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"
GRAPH_SHA256 = "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26"
EQUILIBRIUM_SHA256 = "4fe8652f4296827ed8bf06b376cee22194027d24eb64a73a17afa87679ffb381"
GEOMETRY_TOLERANCE_MM = contact_graph.GEOMETRY_TOLERANCE_MM
AREA_TOLERANCE_MM2 = contact_graph.AREA_TOLERANCE_MM2
NORMAL_TOLERANCE = contact_graph.NORMAL_TOLERANCE


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative_path: str, expected_sha256: str | None = None) -> dict[str, Any]:
    path = ROOT / relative_path
    digest = sha256(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"source SHA-256 changed for {relative_path}: {digest}")
    return json.loads(path.read_text(encoding="utf-8"))


def vector_tuple(vector: Any) -> tuple[float, float, float]:
    return tuple(float(value) for value in vector.toTuple())


def vector_list(vector: Any) -> list[float]:
    return list(vector_tuple(vector))


def point_vertices(shape: Any) -> list[list[float]]:
    points = {
        tuple(round(float(value), 9) for value in vertex.Center().toTuple())
        for vertex in shape.Vertices()
    }
    return [list(point) for point in sorted(points)]


def boundary_edges(shape: Any) -> list[dict[str, Any]]:
    rows = []
    for index, edge in enumerate(shape.Edges(), start=1):
        curve_type = str(edge.geomType())
        row = {
            "edge_index": index,
            "curve_type": curve_type,
            "start_xyz_mm": vector_list(edge.startPoint()),
            "end_xyz_mm": vector_list(edge.endPoint()),
            "length_mm": float(edge.Length()),
        }
        if curve_type == "CIRCLE":
            adaptor = BRepAdaptor_Curve(edge.wrapped)
            circle = adaptor.Circle()
            row["circle"] = {
                "center_xyz_mm": [float(value) for value in circle.Location().Coord()],
                "axis_xyz": [float(value) for value in circle.Axis().Direction().Coord()],
                "radius_mm": float(circle.Radius()),
                "first_parameter_rad": float(adaptor.FirstParameter()),
                "last_parameter_rad": float(adaptor.LastParameter()),
            }
        rows.append(row)
    return rows


def planar_face(face: Any) -> bool:
    return face.geomType() == "PLANE" and float(face.Area()) > 1e-8


def _area_tolerance(perimeter_mm: float) -> float:
    # Propagate the existing 1e-5 mm contact-plane tolerance across the patch
    # boundary, retaining the graph collector's 1e-6 mm2 area floor.
    return AREA_TOLERANCE_MM2 + GEOMETRY_TOLERANCE_MM * perimeter_mm


def opposed_patches(first: Any, second: Any, member_ids: list[str]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    first_faces = first.Faces()
    second_faces = second.Faces()
    for first_index, face_a in enumerate(first_faces, start=1):
        if not planar_face(face_a):
            continue
        normal_a = face_a.normalAt().normalized()
        for second_index, face_b in enumerate(second_faces, start=1):
            if not planar_face(face_b):
                continue
            if not contact_graph.receiver_screen._face_bounds_overlap(
                face_a, face_b, GEOMETRY_TOLERANCE_MM
            ):
                continue
            normal_b = face_b.normalAt().normalized()
            dot = float(normal_a.dot(normal_b))
            if abs(abs(dot) - 1.0) > NORMAL_TOLERANCE:
                continue
            if abs(float((face_b.Center() - face_a.Center()).dot(normal_a))) > GEOMETRY_TOLERANCE_MM:
                continue
            if dot >= 0.0:
                continue
            common = face_a.intersect(face_b)
            for patch in common.Faces():
                area = float(patch.Area())
                if area <= AREA_TOLERANCE_MM2:
                    continue
                patches.append(
                    {
                        "member_ids": member_ids,
                        "source_face_indices": [first_index, second_index],
                        "area_mm2": area,
                        "centroid_xyz_mm": vector_list(patch.Center()),
                        "normal_on_first_xyz": vector_list(normal_a),
                        "normal_on_second_xyz": vector_list(normal_b),
                        "vertices_xyz_mm": point_vertices(patch),
                        "boundary_edges": boundary_edges(patch),
                        "boundary_edge_types": sorted(
                            {edge.geomType() for edge in patch.Edges()}
                        ),
                        "boundary_perimeter_mm": sum(
                            float(edge.Length()) for edge in patch.Edges()
                        ),
                    }
                )
    patches.sort(
        key=lambda row: (
            row["source_face_indices"],
            row["centroid_xyz_mm"],
            row["area_mm2"],
            row["vertices_xyz_mm"],
        )
    )
    for patch_index, row in enumerate(patches):
        row["patch_index"] = patch_index
    return patches


def floor_patch_rows(
    member_id: str, shape: Any, expected: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    for face_index, face in enumerate(shape.Faces(), start=1):
        if not planar_face(face):
            continue
        normal = face.normalAt().normalized()
        if abs(float(face.Center().z)) >= 1e-6 or abs(abs(float(normal.z)) - 1.0) >= 1e-8:
            continue
        vertices = point_vertices(face)
        if not vertices or any(abs(point[2]) >= 1e-6 for point in vertices):
            raise ValueError(f"{member_id}: selected z=0 floor face has a non-floor vertex")
        rows.append(
            {
                "member_id": member_id,
                "patch_index": len(rows),
                "source_face_index": face_index,
                "area_mm2": float(face.Area()),
                "centroid_xyz_mm": vector_list(face.Center()),
                "outward_normal_xyz": vector_list(normal),
                "vertices_xyz_mm": vertices,
                "boundary_edges": boundary_edges(face),
                "boundary_edge_types": sorted({edge.geomType() for edge in face.Edges()}),
                "boundary_perimeter_mm": sum(float(edge.Length()) for edge in face.Edges()),
                "geometry_only": True,
                "support_added": False,
            }
        )
    if not rows:
        raise ValueError(f"{member_id}: no actual z=0 planar floor face found")
    perimeter = sum(row["boundary_perimeter_mm"] for row in rows)
    area = sum(row["area_mm2"] for row in rows)
    discrepancy = area - float(expected["planar_area_mm2"])
    expected_vertices = {
        tuple(round(float(value), 8) for value in point)
        for point in expected["floor_face_vertices_xy_mm"]
    }
    actual_vertices = {
        (round(point[0], 8), round(point[1], 8))
        for row in rows
        for point in row["vertices_xyz_mm"]
    }
    tolerance = _area_tolerance(perimeter)
    check = {
        "member_id": member_id,
        "floor_face_count": len(rows),
        "step_area_mm2": area,
        "prior_screen_area_mm2": float(expected["planar_area_mm2"]),
        "signed_area_difference_mm2": discrepancy,
        "area_tolerance_mm2": tolerance,
        "vertex_xy_sets_match_at_1e-8_mm": actual_vertices == expected_vertices,
        "status": "PASS"
        if abs(discrepancy) <= tolerance and actual_vertices == expected_vertices
        else "DISCREPANCY",
    }
    return rows, check


def build_artifact() -> dict[str, Any]:
    manifest = read_json(MANIFEST_REL, MANIFEST_SHA256)
    graph = read_json(GRAPH_REL, GRAPH_SHA256)
    equilibrium = read_json(EQUILIBRIUM_REL, EQUILIBRIUM_SHA256)
    script_expected = equilibrium["source_sha256"][EQUILIBRIUM_SCRIPT_REL]
    if sha256(ROOT / EQUILIBRIUM_SCRIPT_REL) != script_expected:
        raise ValueError("global-equilibrium screen source changed")
    revision = manifest["geometry_revision_id"]
    if graph["revision_id"] != revision or equilibrium["geometry_revision_id"] != revision:
        raise ValueError("source artifacts disagree on current geometry revision")

    member_rows = {row["member_id"]: row for row in manifest["physical_members"]}
    graph_member_rows = {row["member_id"]: row for row in graph["inventories"]["physical_members"]}
    if len(member_rows) != 50 or set(member_rows) != set(graph_member_rows):
        raise ValueError("attempt04 STEP members do not match graph members")
    shapes: dict[str, Any] = {}
    step_hashes = {}
    for member_id, row in sorted(member_rows.items()):
        binding = row["current_finished_step_binding"]
        step_path = ROOT / binding["path"]
        actual_hash = sha256(step_path)
        if actual_hash != binding["file_sha256"]:
            raise ValueError(f"manifest-bound STEP changed for {member_id}")
        shape = cq.importers.importStep(str(step_path)).val()
        if shape.ShapeType() != "Solid" or len(shape.Solids()) != 1 or not shape.isValid():
            raise ValueError(f"manifest-bound STEP is not one valid solid: {member_id}")
        graph_summary = graph_member_rows[member_id]["finished"]
        if abs(float(shape.Volume()) - float(graph_summary["volume_mm3"])) > max(
            1e-5, 1e-9 * float(graph_summary["volume_mm3"])
        ):
            raise ValueError(f"STEP volume does not match pinned graph summary: {member_id}")
        shapes[member_id] = shape
        step_hashes[binding["path"]] = actual_hash

    exact_edges = [edge for edge in graph["edges"] if edge["broadphase_candidate"]]
    if len(exact_edges) != 147:
        raise ValueError(f"expected 147 exact BRep candidate pairs, found {len(exact_edges)}")
    contact_patches = []
    pair_area_checks = []
    discrepancies = []
    for edge in exact_edges:
        member_ids = list(edge["member_ids"])
        first, second = (shapes[member_id] for member_id in member_ids)
        rows = opposed_patches(first, second, member_ids)
        contact_patches.extend(rows)
        extracted_area = sum(row["area_mm2"] for row in rows)
        perimeter = sum(row["boundary_perimeter_mm"] for row in rows)
        expected_area = float(edge["opposed_planar_face_contact_area_mm2"])
        helper_area, _ = contact_graph._opposed_planar_contact_area(first, second)
        tolerance = _area_tolerance(perimeter)
        graph_difference = extracted_area - expected_area
        helper_difference = extracted_area - float(helper_area)
        status = (
            "PASS"
            if abs(graph_difference) <= tolerance and abs(helper_difference) <= tolerance
            else "DISCREPANCY"
        )
        check = {
            "member_ids": member_ids,
            "geometry_state": edge["geometry_state"],
            "graph_opposed_area_mm2": expected_area,
            "step_patch_area_sum_mm2": extracted_area,
            "existing_helper_opposed_area_mm2": float(helper_area),
            "signed_graph_difference_mm2": graph_difference,
            "signed_helper_difference_mm2": helper_difference,
            "boundary_perimeter_mm": perimeter,
            "area_tolerance_mm2": tolerance,
            "status": status,
        }
        pair_area_checks.append(check)
        if status != "PASS":
            discrepancies.append(check)

    prior_floor_rows = {row["member_id"]: row for row in equilibrium["footprints"]}
    floor_member_ids = sorted(prior_floor_rows)
    if len(floor_member_ids) != 8 or any(
        member_rows[member_id]["member_kind"] != "timber" for member_id in floor_member_ids
    ):
        raise ValueError("prior global-equilibrium footprint list is not eight timbers")
    floor_patches = []
    floor_checks = []
    for member_id in floor_member_ids:
        rows, check = floor_patch_rows(member_id, shapes[member_id], prior_floor_rows[member_id])
        floor_patches.extend(rows)
        floor_checks.append(check)
        if check["status"] != "PASS":
            discrepancies.append(check)

    sources = {
        MANIFEST_REL: MANIFEST_SHA256,
        GRAPH_REL: GRAPH_SHA256,
        EQUILIBRIUM_REL: EQUILIBRIUM_SHA256,
        EQUILIBRIUM_SCRIPT_REL: script_expected,
        CONTACT_GRAPH_HELPER_REL: sha256(ROOT / CONTACT_GRAPH_HELPER_REL),
        RECEIVER_SCREEN_HELPER_REL: sha256(ROOT / RECEIVER_SCREEN_HELPER_REL),
        **step_hashes,
    }
    boundary_edge_types = sorted(
        {
            edge["curve_type"]
            for patch in contact_patches
            for edge in patch["boundary_edges"]
        }
    )
    unsupported_boundary_edge_types = sorted(
        set(boundary_edge_types) - {"LINE", "CIRCLE"}
    )
    return {
        "schema": "wood_joint_reduced_static_contact_geometry/v1",
        "candidate": manifest["candidate"],
        "revision_id": revision,
        "source_sha256": sources,
        "tolerances": {
            "contact_geometry_tolerance_mm": GEOMETRY_TOLERANCE_MM,
            "contact_area_floor_mm2": AREA_TOLERANCE_MM2,
            "normal_dot_tolerance": NORMAL_TOLERANCE,
            "area_roundtrip_tolerance": "1e-6 mm2 + 1e-5 mm times summed extracted patch perimeter",
            "floor_vertex_xy_comparison_mm": 1e-8,
        },
        "contact_patches": contact_patches,
        "pair_area_checks": pair_area_checks,
        "floor_patches": floor_patches,
        "floor_area_checks": floor_checks,
        "checks": {
            "manifest_bound_steps_imported": len(shapes) == 50,
            "one_valid_solid_per_member": len(shapes) == 50,
            "exact_graph_pairs_checked": len(pair_area_checks) == 147,
            "all_opposed_patch_sums_match_graph_and_helper": not any(
                row["status"] != "PASS" for row in pair_area_checks
            ),
            "existing_floor_timbers_checked": len(floor_checks) == 8,
            "existing_floor_areas_and_vertices_match": all(
                row["status"] == "PASS" for row in floor_checks
            ),
            "discrepancy_count": len(discrepancies),
            "boundary_edge_types_observed": boundary_edge_types,
            "unsupported_boundary_edge_types": unsupported_boundary_edge_types,
            "all_contact_patch_boundary_edges_encoded": not unsupported_boundary_edge_types,
            "floor_supports_added": False,
            "native_solve_run": False,
            "active_contact_law_defined": False,
        },
        "limits": [
            "Opposed patches and z=0 floor faces are nominal CAD geometry only.",
            "Floor patches reproduce the prior eight-member screen; no floor support or contact law is added.",
            "This export supplies no active contact, connector stiffness, force transfer, capacity, or acceptance result.",
            "Patch vertices are rounded to 1e-9 mm for JSON serialization; line endpoints and circular edge center/axis/radius are retained explicitly.",
        ],
    }


def main() -> None:
    if sys.argv[1:] not in (["--write"], ["--verify"]):
        raise SystemExit("Use --write or --verify")
    artifact = build_artifact()
    output = json.dumps(artifact, indent=2, allow_nan=False) + "\n"
    path = HERE / "contact-geometry.json"
    if sys.argv[1] == "--write":
        path.write_text(output, encoding="utf-8")
    elif path.read_text(encoding="utf-8") != output:
        raise SystemExit("contact-geometry.json differs from pinned STEP extraction")
    print(json.dumps(artifact["checks"], indent=2))
    if not artifact["checks"]["all_contact_patch_boundary_edges_encoded"]:
        raise SystemExit("Unsupported contact-patch boundary curve type recorded")
    if artifact["checks"]["discrepancy_count"]:
        raise SystemExit("Geometry discrepancies recorded; do not consume as a matched export")


if __name__ == "__main__":
    main()
