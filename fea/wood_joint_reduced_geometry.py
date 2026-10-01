"""Build and audit source-bound reduced wood-joint geometry.

This module composes the pinned gross-member meshes, six STEP-derived panels,
and trimmed contact-area resultants.  It creates geometric attachment
equations only: it adds no connector laws, loads, supports, or solver run.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np

from fea.current_response_materials import materials
from fea.current_response_model import CurrentStructure
from fea.wood_joint_reduced_contacts import contact_samples, load_shapes
from fea.wood_joint_reduced_materials import bind_reduced_material_scenario
from fea.wood_joint_reduced_members import (
    _inverse_shape20,
    add_current_members,
    attach_member,
)
from fea.wood_joint_reduced_panels import ReducedPanelAssembly, add_current_panels

REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01"
MEMBER_GEOMETRY = SOURCE / "member-geometry.json"
MODEL_INPUTS = SOURCE / "model-inputs.json"
CONTACT_GEOMETRY = SOURCE / "contact-geometry.json"
CONTACT_CELL_SIZE_MM = 100.0
GEOMETRY_TOL_MM = 1e-5


class ReducedGeometryError(ValueError):
    """Raised when a source-bound reduced geometry attachment is invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_geometry(
    mesh_size_mm: float = 150.,
    *,
    ring_case: str = "A",
    panel_group_factor: float = 1.0,
) -> tuple[CurrentStructure, ReducedPanelAssembly, dict[str, Any]]:
    """Build 44 current members and six layered panels from the pinned inputs.

    The member and panel meshes are coarse gross-geometry representations.
    Contact resultants use the frozen 100 mm exact trimmed-face cell grid and
    are regenerated from the pinned source B-reps during :func:`audit_geometry`.
    """
    if not math.isfinite(mesh_size_mm) or mesh_size_mm <= 0:
        raise ReducedGeometryError("Mesh size must be positive and finite")
    member_doc = _read_json(MEMBER_GEOMETRY)
    model_doc = _read_json(MODEL_INPUTS)
    contact_doc = _read_json(CONTACT_GEOMETRY)

    structure = CurrentStructure(materials())
    member_records = add_current_members(structure, member_doc, mesh_size_mm)
    panels = add_current_panels(
        structure,
        MEMBER_GEOMETRY,
        MODEL_INPUTS,
        contact_geometry=CONTACT_GEOMETRY,
        mesh_size_mm=mesh_size_mm,
    )
    material_audit = bind_reduced_material_scenario(
        structure, member_doc, ring_case=ring_case,
        panel_group_factor=panel_group_factor, panel_assembly=panels,
    )
    structure.layered_panels()
    panels.bind_layered_structure()

    # Reuse the contact adapter's hash-verified B-reps for exact occupancy and
    # cell construction.  They remain adapter state, not public metadata.
    source_shapes = load_shapes(REPOSITORY, model_doc)
    expected_names = set(member_records) | set(panels.panels)
    if set(source_shapes) != expected_names:
        raise ReducedGeometryError(
            "Pinned source solid set does not match the 44 member and six panel meshes"
        )
    panels._reduced_source_shapes = source_shapes
    panels._reduced_member_records = member_records
    panels._reduced_structure = structure
    panels._reduced_attachment_methods = {}

    metadata = {
        "candidate": member_doc.get("candidate"),
        "geometry_revision_id": member_doc.get("geometry_revision_id"),
        "source_documents": {
            path.name: {"path": str(path.relative_to(REPOSITORY)), "sha256": _sha256(path)}
            for path in (MEMBER_GEOMETRY, MODEL_INPUTS, CONTACT_GEOMETRY)
        },
        "member_count": len(member_records),
        "member_element_count": sum(len(structure.groups.get(name, [])) for name in member_records),
        "panel_count": len(panels.panels),
        "panel_element_count": sum(len(panel.elements) for panel in panels.panels.values()),
        "panel_mesh_metadata": {name: panels.panel_metadata(name) for name in sorted(panels.panels)},
        "material_binding": material_audit,
        "contact_patch_count": len(contact_doc.get("contact_patches", [])),
        "floor_patch_count": len(contact_doc.get("floor_patches", [])),
        "contact_cell_size_mm": CONTACT_CELL_SIZE_MM,
        "member_and_panel_mesh_size_mm": float(mesh_size_mm),
        "gross_member_mesh_scope": "rectangular members; actual 1:12 leg foot profiles retained; source bores filled",
        "panel_mesh_scope": "STEP broad-face footprints, uniform four-layer solids; source bores and partial-depth details omitted",
        "native_solve_executed": False,
        "loads_added": 0,
        "springs_added": 0,
        "supports_added": 0,
        "qualified_for_design": False,
    }
    return structure, panels, metadata


def _point3(point: Sequence[float]) -> np.ndarray:
    result = np.asarray(point, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ReducedGeometryError("Attachment must be a finite global XYZ point")
    return result


def _surface_distance(shape: cq.Shape, point: np.ndarray) -> float:
    vertex = cq.Vertex.makeVertex(*map(float, point))
    return float(shape.distance(vertex))


def _member_source_bore_at(shape: cq.Shape, point: np.ndarray) -> dict[str, Any] | None:
    """Identify a point in a declared cylindrical source bore, never a cut gap."""
    for face_index, face in enumerate(shape.Faces()):
        if face.geomType() != "CYLINDER":
            continue
        surface = face._geomAdaptor()
        axis = np.asarray(surface.Axis().Direction().Coord(), dtype=float)
        axis /= np.linalg.norm(axis)
        origin = np.asarray(surface.Location().Coord(), dtype=float)
        delta = point - origin
        station = float(delta @ axis)
        radial = delta - station * axis
        radius = float(surface.Radius())
        if radius <= 0 or float(np.linalg.norm(radial)) >= radius - 2e-4:
            continue
        vertices = face.Vertices()
        if len(vertices) < 2:
            continue
        stations = [float((np.asarray(vertex.Center().toTuple()) - origin) @ axis)
                    for vertex in vertices]
        if station < min(stations) - 2e-4 or station > max(stations) + 2e-4:
            continue
        # For a bore, points just beyond the cylindrical wall should be wood.
        # The occupancy ring avoids mistaking an unrelated external cylinder
        # whose axis happens to pass near the attachment for a source hole.
        radial_norm = float(np.linalg.norm(radial))
        if radial_norm <= 1e-12:
            seed = np.array([1., 0., 0.])
            if abs(float(seed @ axis)) > .9:
                seed = np.array([0., 1., 0.])
            radial_u = np.cross(axis, seed)
        else:
            radial_u = radial / radial_norm
        radial_u /= np.linalg.norm(radial_u)
        radial_v = np.cross(axis, radial_u)
        ring_radius = radius + min(.1, max(.02, radius * .002))
        # At a through-bore mouth the ring lies on the end face, which the
        # solid classifier may report outside. Test its nearby interior ring;
        # retain the original attachment and its checked axial-span membership.
        low, high = min(stations), max(stations)
        inset = min(.01, (high-low)/4.)
        ring_station = min(max(station, low+inset), high-inset)
        inside_count = 0
        for angle in np.linspace(0., 2. * math.pi, 12, endpoint=False):
            sample = (origin + ring_station * axis + ring_radius
                      * (math.cos(float(angle)) * radial_u + math.sin(float(angle)) * radial_v))
            if shape.isInside(sample.tolist(), 1e-6):
                inside_count += 1
        if inside_count >= 9:
            return {"face_index": face_index, "radius_mm": radius,
                    "cylindrical_wall_ring_samples_inside": inside_count}
    return None


def _append_equations(
    structure: CurrentStructure,
    point: np.ndarray,
    node_ids: Sequence[int],
    weights: Sequence[float],
) -> int:
    if len(node_ids) != len(weights) or not node_ids:
        raise ReducedGeometryError("Attachment interpolation has no source element nodes")
    tag = structure.node(point)
    for dof in (1, 2, 3):
        structure.equations.append(
            [(tag, dof, 1.0)]
            + [(int(node), dof, -float(weight))
               for node, weight in zip(node_ids, weights, strict=True)
               if abs(float(weight)) > 1e-13]
        )
    return tag


def _attach_panel_gross_volume(
    structure: CurrentStructure,
    panelAssembly: ReducedPanelAssembly,
    name: str,
    point: np.ndarray,
) -> int:
    """Interpolate an exact source-face point inside the coarse panel solid."""
    layer_groups = getattr(structure, "panel_layer_groups", {}).get(name, [])
    for group in layer_groups:
        for element_id in structure.groups.get(group, []):
            kind, node_ids, _ = structure.elements[element_id]
            if kind != "C3D20":
                continue
            coordinates = np.asarray([structure.nodes[node] for node in node_ids], dtype=float)
            if (np.any(point < coordinates.min(axis=0) - GEOMETRY_TOL_MM)
                    or np.any(point > coordinates.max(axis=0) + GEOMETRY_TOL_MM)):
                continue
            inverse = _inverse_shape20(point, coordinates)
            if inverse is None:
                continue
            natural, weights = inverse
            if (np.max(np.abs(natural)) > 1. + 1e-7
                    or np.linalg.norm(weights @ coordinates - point) > 1e-6
                    or abs(float(weights.sum()) - 1.) > 1e-10):
                continue
            tag = _append_equations(structure, point, node_ids, weights)
            panelAssembly._reduced_attachment_methods[tag] = {
                "body": name,
                "method": "C3D20_inverse_interpolation_in_coarse_panel_solid",
                "exact_pinned_source_surface": True,
                "natural_coordinates": natural.tolist(),
                "source_hole_abstraction": False,
            }
            return tag
    raise ReducedGeometryError(
        f"{name} exact STEP surface point is outside the coarse layered-panel C3D20 stiffness mesh"
    )


def attach_body(
    structure: CurrentStructure,
    panelAssembly: ReducedPanelAssembly,
    name: str,
    xyz: Sequence[float],
    *,
    allow_source_bore: bool = False,
) -> int:
    """Attach one point to a member C3D20 or a true panel surface face.

    Source-bore abstraction must be explicit and positively identified from
    the pinned solid.  A source perimeter, recess, or unrelated outside point
    is never moved to a nearby mesh node or accepted by this flag.
    """
    if structure is not panelAssembly.structure or structure is not getattr(
        panelAssembly, "_reduced_structure", None
    ):
        raise ReducedGeometryError("Panel assembly is not bound to this structure")
    point = _point3(xyz)
    if name in panelAssembly.panels:
        # Validate footprint and true surface before considering a declared
        # source hole.  A shallow bevel on the true STEP panel edge can lie
        # inside the coarse layered solid without lying on a broad/outer edge
        # face; in that case use exact inverse interpolation in the C3D20 body.
        face_error = None
        try:
            _, _, _, hole_ids, _, _ = panelAssembly._element_and_face(name, point)
        except (ValueError, RuntimeError) as exc:
            face_error = exc
            hole_ids = []
        if face_error is not None:
            if allow_source_bore:
                raise ReducedGeometryError(
                    f"{name} bore allowance cannot apply because no panel source bore was located"
                ) from face_error
            source_shape = panelAssembly._reduced_source_shapes[name]
            source_distance = _surface_distance(source_shape, point)
            if source_distance > GEOMETRY_TOL_MM:
                raise ReducedGeometryError(
                    f"{name} attachment is not on its pinned STEP surface "
                    f"(distance {source_distance:.6g} mm); panel locator: {face_error}"
                ) from face_error
            return _attach_panel_gross_volume(structure, panelAssembly, name, point)
        if bool(hole_ids) != bool(allow_source_bore):
            if hole_ids:
                raise ReducedGeometryError(
                    f"{name} attachment falls in declared source panel bore(s) {hole_ids}"
                )
            if allow_source_bore:
                raise ReducedGeometryError(
                    f"{name} bore allowance requested at a point not in a declared source bore"
                )
        tag = panelAssembly.attach(
            name, point, allow_source_hole=bool(hole_ids),
        )
        panelAssembly._reduced_attachment_methods[tag] = {
            "body": name,
            "method": "panel_C3D20_surface_face_interpolation",
            "exact_pinned_source_surface": True,
            "source_hole_abstraction": bool(hole_ids),
            "panel_source_hole_ids": list(hole_ids),
        }
        return tag

    if name not in structure.members:
        raise ReducedGeometryError(f"Unknown reduced body {name!r}")
    try:
        source_shape = panelAssembly._reduced_source_shapes[name]
    except (AttributeError, KeyError) as exc:
        raise ReducedGeometryError("Pinned source solids are unavailable on this panel assembly") from exc
    inside = bool(source_shape.isInside(point.tolist(), 1e-6))
    boundary_distance = math.inf if inside else _surface_distance(source_shape, point)
    on_boundary = boundary_distance <= GEOMETRY_TOL_MM
    bore = None if inside or on_boundary else _member_source_bore_at(source_shape, point)
    if bore is not None and not allow_source_bore:
        raise ReducedGeometryError(
            f"{name} attachment falls in declared source cylindrical bore; explicit abstraction required"
        )
    if allow_source_bore and bore is None:
        raise ReducedGeometryError(
            f"{name} bore allowance requested outside a declared cylindrical source bore"
        )
    if not inside and not on_boundary and bore is None:
        raise ReducedGeometryError(
            f"{name} attachment lies outside its pinned STEP solid by {boundary_distance:.6g} mm"
        )
    tag = attach_member(structure, name, point)
    panelAssembly._reduced_attachment_methods[tag] = {
        "body": name,
        "method": "member_C3D20_inverse_interpolation",
        "exact_pinned_source_surface_or_interior": bool(inside or on_boundary),
        "source_hole_abstraction": bool(bore),
    }
    return tag


def _audit_equations(
    structure: CurrentStructure,
    tag: int,
    point: np.ndarray,
    equation_start: int,
) -> dict[str, float]:
    equations = structure.equations[equation_start:]
    if len(equations) != 3:
        raise ReducedGeometryError(f"Attachment {tag} did not create exactly three kinematic equations")
    max_weight_error = max_position_error = max_affine_error = 0.0
    # A non-symmetric affine field simultaneously checks translation, stretch,
    # shear, and rigid-rotation reproduction through each interpolation rule.
    matrix = np.array([[.17, -.23, .31], [.29, .11, -.19], [-.07, .37, .13]])
    offset = np.array([1.3, -2.1, .7])
    expected = matrix @ point + offset
    for dof, row in enumerate(equations, start=1):
        if not row or row[0][0] != tag or row[0][1] != dof or abs(row[0][2] - 1.) > 1e-12:
            raise ReducedGeometryError("Attachment equation has an unexpected dependent node or DOF")
        weights = np.asarray([-float(term[2]) for term in row[1:]], dtype=float)
        node_ids = [int(term[0]) for term in row[1:]]
        if not node_ids or len(node_ids) != len(weights):
            raise ReducedGeometryError("Attachment equation has no source face or element nodes")
        coordinates = np.asarray([structure.nodes[node] for node in node_ids], dtype=float)
        max_weight_error = max(max_weight_error, abs(float(weights.sum()) - 1.))
        reconstructed = weights @ coordinates
        max_position_error = max(max_position_error, float(np.linalg.norm(reconstructed - point)))
        interpolated = weights @ (coordinates @ matrix.T + offset)
        max_affine_error = max(max_affine_error, float(np.linalg.norm(interpolated - expected)))
    return {"weight_sum_error": max_weight_error,
            "position_reproduction_error_mm": max_position_error,
            "affine_motion_reproduction_error": max_affine_error}


def audit_geometry(
    structure: CurrentStructure,
    panelAssembly: ReducedPanelAssembly,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach and verify every frozen contact cell to both bodies and floor cell.

    Each source cylindrical bore resultant is explicitly tagged as an abstract
    distributed-patch attachment. All other out-of-source points are retained
    as failures; no projection or nearest-point correction is attempted.
    """
    model_doc = _read_json(MODEL_INPUTS)
    contact_doc = _read_json(CONTACT_GEOMETRY)
    shapes = panelAssembly._reduced_source_shapes
    samples, floors = contact_samples(
        REPOSITORY, model_doc, contact_doc,
        size_mm=CONTACT_CELL_SIZE_MM, shapes=shapes,
    )

    by_patch: dict[int, list[Mapping[str, Any]]] = {}
    for sample in samples:
        by_patch.setdefault(int(sample["source_patch_index"]), []).append(sample)
    area_rows = []
    max_area_error = max_centroid_error = 0.0
    for patch_index, patch in enumerate(contact_doc["contact_patches"]):
        cells = by_patch.get(patch_index, [])
        area = sum(float(cell["area_mm2"]) for cell in cells)
        moment = sum((np.asarray(cell["point_xyz_mm"], dtype=float) * float(cell["area_mm2"])
                      for cell in cells), np.zeros(3))
        if area <= 0:
            area_error, centroid_error = math.inf, math.inf
        else:
            centroid = moment / area
            area_error = abs(area - float(patch["area_mm2"]))
            centroid_error = float(np.linalg.norm(
                centroid - np.asarray(patch["centroid_xyz_mm"], dtype=float)
            ))
        max_area_error = max(max_area_error, area_error)
        max_centroid_error = max(max_centroid_error, centroid_error)
        area_rows.append({"source_patch_index": patch_index, "cell_count": len(cells),
                          "cell_area_mm2": area, "source_area_mm2": float(patch["area_mm2"]),
                          "area_error_mm2": area_error,
                          "centroid_error_mm": centroid_error})

    failures: list[dict[str, Any]] = []
    bore_attachments: list[dict[str, Any]] = []
    affine_errors: list[dict[str, Any]] = []
    attempted = succeeded = 0
    contact_attachment_nodes: dict[str, dict[str, int | None]] = {}
    floor_attachment_nodes: dict[str, int | None] = {}
    attachment_methods: dict[str, dict[str, dict[str, Any] | None]] = {}

    def attempt(name: str, point_values: Sequence[float], label: str, *, owner: str,
                context: Mapping[str, Any], permit_detected_bore: bool) -> int | None:
        nonlocal attempted, succeeded
        point = _point3(point_values)
        allow_bore = False
        bore_record: dict[str, Any] | None = None
        if permit_detected_bore:
            if name in panelAssembly.panels:
                try:
                    _, _, _, hole_ids, _, _ = panelAssembly._element_and_face(name, point)
                except (ValueError, RuntimeError):
                    # The real attach below records unsupported interior or
                    # outside-footprint points; only a located source bore can
                    # opt into the explicit bore abstraction.
                    hole_ids = []
                allow_bore = bool(hole_ids)
                if allow_bore:
                    bore_record = {"name": label, "owner": name,
                                   "panel_source_hole_ids": list(hole_ids)}
            elif name in structure.members:
                source_shape = shapes[name]
                if (not source_shape.isInside(point.tolist(), 1e-6)
                        and _surface_distance(source_shape, point) > GEOMETRY_TOL_MM):
                    bore = _member_source_bore_at(source_shape, point)
                    allow_bore = bore is not None
                    if bore is not None:
                        bore_record = {"name": label, "owner": name, **bore}
        attempted += 1
        before = len(structure.equations)
        try:
            tag = attach_body(structure, panelAssembly, name, point,
                              allow_source_bore=allow_bore)
            audit = _audit_equations(structure, tag, point, before)
            succeeded += 1
            if (audit["weight_sum_error"] > 1e-9
                    or audit["position_reproduction_error_mm"] > 1e-5
                    or audit["affine_motion_reproduction_error"] > 1e-7):
                affine_errors.append({"name": label, "owner": name, **audit})
            if bore_record is not None:
                bore_attachments.append(bore_record)
            panel_method = panelAssembly._reduced_attachment_methods.get(tag)
            if owner in ("first", "second"):
                attachment_methods.setdefault(label, {})[owner] = panel_method
            else:
                attachment_methods[label] = {"wood": panel_method}
            return tag
        except (ReducedGeometryError, ValueError, RuntimeError) as exc:
            # Continue the independent per-owner audit after a geometry miss.
            del structure.equations[before:]
            failures.append({"name": label, "owner": name,
                             "point_xyz_mm": point.tolist(), "reason": str(exc),
                             **dict(context)})
            return None

    for sample in samples:
        context = {"kind": "internal_contact", "source_patch_index": sample["source_patch_index"],
                   "area_mm2": sample["area_mm2"]}
        label = str(sample["name"])
        contact_attachment_nodes[label] = {
            "first": attempt(str(sample["first"]), sample["point_xyz_mm"], label,
                             owner="first", context=context, permit_detected_bore=True),
            "second": attempt(str(sample["second"]), sample["point_xyz_mm"], label,
                              owner="second", context=context, permit_detected_bore=True),
        }
    for floor in floors:
        floor_attachment_nodes[str(floor["name"])] = attempt(
                str(floor["first"]), floor["point_xyz_mm"], str(floor["name"]),
                owner="floor_member", context={"kind": "floor_contact",
                    "source_floor_patch_index": floor["source_floor_patch_index"],
                    "area_mm2": floor["area_mm2"]}, permit_detected_bore=True)

    total_expected = 2 * len(samples) + len(floors)
    area_passed = (len(area_rows) == len(contact_doc["contact_patches"])
                   and max_area_error <= 1e-5 and max_centroid_error <= 1e-6)
    all_passed = (attempted == total_expected and succeeded == total_expected and area_passed
                  and not affine_errors)
    return {
        "candidate": metadata.get("candidate"),
        "geometry_revision_id": metadata.get("geometry_revision_id"),
        "contact_patch_count": len(contact_doc["contact_patches"]),
        "contact_area_cell_count": len(samples),
        "contact_owner_attachment_attempts": 2 * len(samples),
        "floor_cell_count": len(floors),
        "floor_attachment_attempts": len(floors),
        "attachment_attempt_count": attempted,
        "attachment_success_count": succeeded,
        "attachment_failure_count": len(failures),
        "source_bore_abstraction_count": len(bore_attachments),
        "source_bore_abstractions": bore_attachments,
        "contact_attachment_nodes": contact_attachment_nodes,
        "floor_attachment_nodes": floor_attachment_nodes,
        "attachment_methods": attachment_methods,
        "sample_geometry_records": [
            {key: sample[key] for key in (
                "name", "first", "second", "kind", "source_patch_index",
                "point_xyz_mm", "area_mm2", "normal_xyz")}
            for sample in samples
        ] + [
            {key: floor[key] for key in (
                "name", "first", "second", "kind", "source_floor_patch_index",
                "point_xyz_mm", "area_mm2", "normal_xyz")}
            for floor in floors
        ],
        "contact_area_first_moment_audit": {
            "patch_count": len(area_rows), "max_area_error_mm2": max_area_error,
            "max_centroid_error_mm": max_centroid_error, "all_passed": area_passed,
            "patches": area_rows,
        },
        "affine_motion_audit_failure_count": len(affine_errors),
        "affine_motion_audit_failures": affine_errors,
        "attachment_failures": failures,
        "native_solve_executed": False,
        "loads_added": 0,
        "springs_added": 0,
        "supports_added": 0,
        "all_passed": all_passed,
        "qualified_for_design": False,
        "scope_note": (
            "Coarse source-bound geometry and kinematic attachment audit only; "
            "panel cutouts and member bore/cut stiffness omissions remain diagnostic, "
            "and no joint mechanics or capacity is established."
        ),
    }


def build_and_audit(mesh_size_mm: float = 150.) -> tuple[CurrentStructure, ReducedPanelAssembly, dict[str, Any]]:
    structure, panels, metadata = build_geometry(mesh_size_mm)
    audit = audit_geometry(structure, panels, metadata)
    metadata["attachment_audit"] = audit
    return structure, panels, metadata


def main() -> None:
    _, _, report = build_and_audit()
    audit = report["attachment_audit"]
    summary = {key: audit[key] for key in (
        "contact_patch_count", "contact_area_cell_count", "contact_owner_attachment_attempts",
        "floor_cell_count", "floor_attachment_attempts", "attachment_attempt_count",
        "attachment_success_count", "attachment_failure_count", "source_bore_abstraction_count",
        "affine_motion_audit_failure_count", "native_solve_executed", "all_passed",
    )}
    summary["member_count"] = report["member_count"]
    summary["member_element_count"] = report["member_element_count"]
    summary["panel_count"] = report["panel_count"]
    summary["panel_element_count"] = report["panel_element_count"]
    summary["material_scenario_id"] = report["material_binding"]["scenario_id"]
    summary["material_ring_case"] = report["material_binding"]["ring_case"]
    summary["material_panel_group_factor"] = report["material_binding"]["panel_group_factor"]
    summary["material_orientation_override_count"] = sum(
        row["explicit_orientation_override_required"]
        for row in report["material_binding"]["orientation_overrides"].values()
    )
    summary["max_contact_area_error_mm2"] = audit["contact_area_first_moment_audit"]["max_area_error_mm2"]
    summary["max_contact_centroid_error_mm"] = audit["contact_area_first_moment_audit"]["max_centroid_error_mm"]
    summary["attachment_node_map_entries"] = len(audit["contact_attachment_nodes"])
    summary["floor_attachment_node_map_entries"] = len(audit["floor_attachment_nodes"])
    summary["sample_geometry_record_count"] = len(audit["sample_geometry_records"])
    summary["qualified_for_design"] = False
    print(json.dumps(summary, indent=2))
    if not audit["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
