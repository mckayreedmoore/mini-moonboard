"""STEP-bound panel meshing and load attachment for the reduced wood-joint model.

This adapter reuses the current response model's native ``CurrentStructure``
and four bonded panel layers.  It does not reconstruct panel CAD or start a
solver.  The STEP broad-face perimeter defines the panel mesh footprint;
through-holes and partial-depth edge details are measured and reported, while
the current equivalent-layer panel abstraction remains continuous and uniform
through its thickness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

REPOSITORY = Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from fea import horizontal_panel_frame as frame
from fea.current_response_model import cut_panel_mesh, retained_panel_weights


EXPECTED_PANEL_IDS = {
    "kicker_left", "kicker_right",
    "main_lower_left", "main_lower_right",
    "main_upper_left", "main_upper_right",
}
PANEL_SOURCE_LIMIT = (
    "Existing conditional APA equivalent-layer properties are a section fit, "
    "not an identification of the actual panel product, grade, or layup. "
    "The mesh retains the STEP broad-face footprint but omits through-hole "
    "voids and partial-depth edge details."
)


def _document(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text())


def _v3(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must be a finite global XYZ point/vector")
    return result


def _wire_points(wire: Any) -> list[np.ndarray]:
    points: list[np.ndarray] = []
    for vertex in wire.Vertices():
        point = np.asarray(vertex.Center().toTuple(), dtype=float)
        if not any(np.linalg.norm(point - known) <= 1e-7 for known in points):
            points.append(point)
    return points


def _polygon_area(points: list[tuple[float, float]]) -> float:
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1]
                   - points[(i + 1) % len(points)][0] * points[i][1]
                   for i in range(len(points))) / 2.)


def _rectangular_outline(points: list[np.ndarray], origin: np.ndarray,
                         axis_u: np.ndarray, axis_v: np.ndarray,
                         *, tolerance: float = 2e-5) -> tuple[list[tuple[float, float]], tuple[float, float, float, float]]:
    if len(points) != 4:
        raise ValueError("Reduced panel mesh requires a four-corner STEP broad-face perimeter")
    polygon = [(float((point - origin) @ axis_u), float((point - origin) @ axis_v))
               for point in points]
    xs = sorted({round(point[0], 5) for point in polygon})
    ys = sorted({round(point[1], 5) for point in polygon})
    if len(xs) != 2 or len(ys) != 2:
        raise ValueError("STEP panel outline is not a rectangle in its recovered face frame")
    corners = {(round(x, 5), round(y, 5)) for x, y in polygon}
    expected = {(x, y) for x in xs for y in ys}
    if corners != expected:
        raise ValueError("STEP panel perimeter is not a complete rectangular footprint")
    bounds = (min(x for x, _ in polygon), max(x for x, _ in polygon),
              min(y for _, y in polygon), max(y for _, y in polygon))
    if (bounds[1] - bounds[0] <= tolerance
            or bounds[3] - bounds[2] <= tolerance):
        raise ValueError("STEP panel outline has no positive area")
    return polygon, bounds


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]],
                      tolerance: float = 1e-6) -> bool:
    x, y = point
    inside = False
    for index, (x0, y0) in enumerate(polygon):
        x1, y1 = polygon[(index + 1) % len(polygon)]
        cross = (x - x0) * (y1 - y0) - (y - y0) * (x1 - x0)
        if abs(cross) <= tolerance * max(1., math.hypot(x1 - x0, y1 - y0)):
            if (min(x0, x1) - tolerance <= x <= max(x0, x1) + tolerance
                    and min(y0, y1) - tolerance <= y <= max(y0, y1) + tolerance):
                return True
        if (y0 > y) != (y1 > y):
            crossing = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < crossing:
                inside = not inside
    return inside


def _source_panel_geometry(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    """Read and bind one pinned STEP panel's two principal planar faces."""
    import cadquery as cq

    name = str(descriptor["panel_id"])
    path = (REPOSITORY / str(descriptor["step_path"])).resolve()
    if REPOSITORY not in path.parents or not path.is_file():
        raise ValueError(f"Current panel STEP source is missing or outside the repository: {name}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != descriptor.get("step_sha256"):
        raise ValueError(f"Current panel STEP hash changed: {name}")
    shape = cq.importers.importStep(str(path)).val()
    planes = sorted((face for face in shape.Faces() if face.geomType() == "PLANE"),
                    key=lambda face: face.Area(), reverse=True)
    if len(planes) < 2 or planes[1].Area() <= 0:
        raise ValueError(f"Current panel STEP needs two broad planar faces: {name}")
    face_a, face_b = planes[:2]
    centre_a = np.asarray(face_a.Center().toTuple(), dtype=float)
    centre_b = np.asarray(face_b.Center().toTuple(), dtype=float)
    delta = centre_b - centre_a
    normal = np.asarray(face_a.normalAt().toTuple(), dtype=float)
    normal /= np.linalg.norm(normal)
    if normal @ delta < 0:
        normal = -normal
    thickness = float(normal @ delta)
    normal_b = np.asarray(face_b.normalAt().toTuple(), dtype=float)
    normal_b /= np.linalg.norm(normal_b)
    if (thickness <= 0 or float(normal @ normal_b) < .99999):
        raise ValueError(f"Current panel broad faces are not opposed parallel planes: {name}")

    # Use the broad-face edge most aligned with global X as sheet width.  This
    # keeps the current panel-layer material's sheet-width direction explicit.
    outer_a = face_a.outerWire()
    edge_directions = []
    for edge in outer_a.Edges():
        vertices = edge.Vertices()
        if len(vertices) < 2:
            continue
        first = np.asarray(vertices[0].Center().toTuple(), dtype=float)
        last = np.asarray(vertices[-1].Center().toTuple(), dtype=float)
        direction = last - first
        direction -= normal * float(direction @ normal)
        length = float(np.linalg.norm(direction))
        if length > 1e-8:
            edge_directions.append((abs(float(direction[0])) / length, length, direction / length))
    if not edge_directions:
        raise ValueError(f"Cannot recover panel width direction from STEP perimeter: {name}")
    axis_u = max(edge_directions, key=lambda row: (row[0], row[1]))[2]
    if axis_u[0] < 0:
        axis_u = -axis_u
    axis_v = np.cross(normal, axis_u)
    axis_v /= np.linalg.norm(axis_v)
    origin = centre_a + normal * (thickness / 2.)

    polygon_a, bounds_a = _rectangular_outline(_wire_points(outer_a), origin, axis_u, axis_v)
    polygon_b, bounds_b = _rectangular_outline(_wire_points(face_b.outerWire()), origin, axis_u, axis_v)
    outline_mismatch = max(abs(a - b) for a, b in zip(bounds_a, bounds_b, strict=True))
    broadface_area_a, broadface_area_b = float(face_a.Area()), float(face_b.Area())

    def holes(face: Any, side: int) -> list[dict[str, Any]]:
        outer = face.outerWire()
        result = []
        for wire_index, wire in enumerate(face.Wires()):
            if wire.isSame(outer):
                continue
            edges = wire.Edges()
            circle = next((edge for edge in edges if edge.geomType() == "CIRCLE"), None)
            if circle is not None and len(edges) == 1:
                centre = np.asarray(circle.Center().toTuple(), dtype=float)
                result.append({"wire_index": wire_index, "side": side,
                    "centre_local_mm": [float((centre - origin) @ axis_u),
                                         float((centre - origin) @ axis_v)],
                    "radius_mm": float(circle.radius()), "geometry": "circular_source_bore"})
            else:
                points = _wire_points(wire)
                local = [[float((point - origin) @ axis_u), float((point - origin) @ axis_v)]
                         for point in points]
                if len(local) >= 3:
                    result.append({"wire_index": wire_index, "side": side,
                                  "outline_local_mm": local, "geometry": "noncircular_source_bore"})
        return result

    side_a_holes, side_b_holes = holes(face_a, -1), holes(face_b, 1)
    box = shape.BoundingBox()
    return {
        "name": name, "step_path": str(path.relative_to(REPOSITORY)),
        "step_sha256": digest, "shape": shape,
        "origin_xyz_mm": origin, "axis_u_xyz": axis_u,
        "axis_v_xyz": axis_v, "normal_xyz": normal,
        "thickness_mm": thickness, "bounds_local_mm": bounds_a,
        "outline_local_mm": polygon_a,
        "outline_front_local_mm": polygon_a,
        "outline_back_local_mm": polygon_b,
        "broadface_area_mm2": {"negative": broadface_area_a, "positive": broadface_area_b},
        "outline_mismatch_mm": float(outline_mismatch),
        "partial_depth_or_face_detail_present": bool(
            outline_mismatch > 1e-5 or abs(broadface_area_a - broadface_area_b)
            > max(1e-3, max(broadface_area_a, broadface_area_b) * 1e-6)),
        "source_bores": side_a_holes + side_b_holes,
        "source_bore_count_by_side": {"negative": len(side_a_holes), "positive": len(side_b_holes)},
        "source_shape_bounds_xyz_mm": [box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax],
    }


@dataclass
class _PanelMesh:
    geometry: dict[str, Any]
    local_nodes: dict[int, list[float]]
    elements: dict[int, list[int]]
    lookup: dict[tuple[float, float], int]
    element_bounds: list[tuple[float, float, float, float]]
    node_tags: dict[int, int]
    cell_face_nodes: dict[int, dict[int, list[int]]] = field(default_factory=dict)
    x_axes: list[float] = field(default_factory=list)
    y_axes: list[float] = field(default_factory=list)
    element_tags: list[int] = field(default_factory=list)
    surface_node_tags_by_side: dict[int, dict[int, int]] = field(default_factory=dict)


class ReducedPanelAssembly:
    """Six independent panels attached to one `CurrentStructure` instance."""

    def __init__(self, structure: Any, panels: dict[str, _PanelMesh],
                 screws: list[dict[str, Any]], cases: list[dict[str, Any]],
                 contact_patches: list[dict[str, Any]]):
        self.structure = structure
        self.panels = panels
        self.screw_records = screws
        self.case_records = cases
        self.contact_patches = contact_patches
        self.screw_nodes: dict[str, int] = {}
        self.contact_nodes: dict[str, int] = {}
        self.load_records: list[dict[str, Any]] = []
        self.metadata = {
            "panels": {name: self.panel_metadata(name) for name in sorted(panels)},
            "panel_property_scope": PANEL_SOURCE_LIMIT,
            "native_solve_executed": False,
        }

    def panel_metadata(self, panel_id: str) -> dict[str, Any]:
        geometry = self.panels[panel_id].geometry
        return {
            "step_path": geometry["step_path"], "step_sha256": geometry["step_sha256"],
            "outline_local_mm": geometry["outline_local_mm"],
            "outline_front_local_mm": geometry["outline_front_local_mm"],
            "outline_back_local_mm": geometry["outline_back_local_mm"],
            "bounds_local_mm": list(geometry["bounds_local_mm"]),
            "thickness_mm": geometry["thickness_mm"],
            "broadface_area_mm2": geometry["broadface_area_mm2"],
            "outline_mismatch_mm": geometry["outline_mismatch_mm"],
            "partial_depth_or_face_detail_present": geometry["partial_depth_or_face_detail_present"],
            "source_bore_count_by_side": geometry["source_bore_count_by_side"],
            "mesh_retained_area_mm2": float(geometry["mesh_retained_area_mm2"]),
            "mesh_element_count": len(self.panels[panel_id].elements),
            "mesh_node_count": len(self.panels[panel_id].local_nodes),
        }

    def bind_layered_structure(self, structure: Any | None = None) -> None:
        """Bind the four native solid layers before attachments or loads."""
        structure = structure or self.structure
        if structure is not self.structure:
            raise ValueError("Panel assembly must bind to the CurrentStructure it meshed")
        if not getattr(structure, "panel_solid_layers", False):
            raise ValueError("Call CurrentStructure.layered_panels() before panel attachments or loads")
        offsets = [-self.panels[next(iter(self.panels))].geometry["thickness_mm"] / 2.]
        for layer in structure.layer_materials:
            offsets.append(offsets[-1] + float(layer["thickness_mm"]))
        self.layer_offsets_mm = offsets
        if abs(offsets[-1] - self.panels[next(iter(self.panels))].geometry["thickness_mm"] / 2.) > 1e-7:
            raise ValueError("Native panel layer thickness differs from the frozen current STEP panels")

        for name, panel in self.panels.items():
            layer_groups = structure.panel_layer_groups[name]
            if len(layer_groups) != 4:
                raise ValueError("Reduced current panels require the existing four-layer panel adapter")
            group_eids = [structure.groups[group] for group in layer_groups]
            if any(len(eids) != len(panel.elements) for eids in group_eids):
                raise ValueError("Layered panel cell inventory differs from source panel mesh")
            surface_maps = {-1: {}, 1: {}}
            for cell_index in range(len(panel.elements)):
                face_nodes: dict[int, list[int]] = {}
                for layer_index in range(4):
                    eid = group_eids[layer_index][cell_index]
                    kind, connectivity, group = structure.elements[eid]
                    if kind != "C3D20" or group != layer_groups[layer_index]:
                        raise ValueError("Current panel layer did not produce native C3D20 elements")
                    face_nodes[layer_index] = list(connectivity)
                local_ids = list(panel.elements.values())[cell_index]
                for side, layer_index, positions in (
                    (-1, 0, (0, 1, 2, 3, 8, 9, 10, 11)),
                    (1, 3, (4, 5, 6, 7, 12, 13, 14, 15)),
                ):
                    surface_tags = [face_nodes[layer_index][position] for position in positions]
                    target = surface_maps[side]
                    for local_node, global_node in zip(local_ids, surface_tags, strict=True):
                        if local_node in target and target[local_node] != global_node:
                            raise ValueError("Layered panel surface nodes are inconsistent across adjacent cells")
                        target[local_node] = global_node
                panel.cell_face_nodes[cell_index] = face_nodes
            if any(set(mapping) != set(panel.local_nodes) for mapping in surface_maps.values()):
                raise ValueError("Layered panel surface lost one or more source panel mesh nodes")
            panel.surface_node_tags_by_side = surface_maps

    def _require_bound(self) -> None:
        if any(not panel.cell_face_nodes for panel in self.panels.values()):
            raise ValueError("Call bind_layered_structure after CurrentStructure.layered_panels()")

    def local_point(self, panel_id: str, point_xyz_mm: Any) -> tuple[float, float, float]:
        geometry = self.panels[panel_id].geometry
        delta = _v3(point_xyz_mm, "Panel point") - geometry["origin_xyz_mm"]
        return (float(delta @ geometry["axis_u_xyz"]),
                float(delta @ geometry["axis_v_xyz"]),
                float(delta @ geometry["normal_xyz"]))

    @staticmethod
    def _interval(axes: list[float], value: float, tolerance: float) -> int:
        for index, (low, high) in enumerate(zip(axes[:-1], axes[1:], strict=True)):
            if low - tolerance <= value <= high + tolerance:
                return index
        raise ValueError("Panel point is outside the meshed STEP outline")

    def _source_holes_at(self, geometry: Mapping[str, Any], x: float, y: float,
                         side: int, tolerance: float) -> list[int]:
        matches = []
        for index, hole in enumerate(geometry["source_bores"]):
            if hole["side"] != side:
                continue
            if "radius_mm" in hole:
                centre = np.asarray(hole["centre_local_mm"], dtype=float)
                if np.linalg.norm(np.array([x, y]) - centre) <= hole["radius_mm"] + tolerance:
                    matches.append(index)
            elif _point_in_polygon((x, y), [tuple(point) for point in hole["outline_local_mm"]], tolerance):
                matches.append(index)
        return matches

    def _element_and_face(self, panel_id: str, point_xyz_mm: Any,
                          tolerance: float = 1e-5) -> tuple[int, list[int], np.ndarray, list[int], int, list[int]]:
        """Return cell, C3D20 face nodes, shape weights and source-hole matches."""
        self._require_bound()
        panel = self.panels[panel_id]
        geometry = panel.geometry
        x, y, w = self.local_point(panel_id, point_xyz_mm)
        x0, x1, y0, y1 = geometry["bounds_local_mm"]
        if not _point_in_polygon((x, y), geometry["outline_local_mm"], tolerance):
            raise ValueError(f"Panel attachment is outside the STEP perimeter: {panel_id}")
        side_a = abs(w + geometry["thickness_mm"] / 2.) <= tolerance
        side_b = abs(w - geometry["thickness_mm"] / 2.) <= tolerance
        if side_a or side_b:
            face_side = -1 if side_a else 1
            hole_ids = self._source_holes_at(geometry, x, y, face_side, tolerance)
            i = self._interval(panel.x_axes, x, tolerance)
            j = self._interval(panel.y_axes, y, tolerance)
            cell_index = j * (len(panel.x_axes) - 1) + i
            layer_index = 0 if face_side < 0 else 3
            connectivity = panel.cell_face_nodes[cell_index][layer_index]
            positions = [0, 1, 2, 3, 8, 9, 10, 11] if face_side < 0 else [4, 5, 6, 7, 12, 13, 14, 15]
            node_tags = [connectivity[index] for index in positions]
            xa, xb, ya, yb = panel.element_bounds[cell_index]
            xi = 2. * (x - xa) / (xb - xa) - 1.
            eta = 2. * (y - ya) / (yb - ya) - 1.
            weights = frame.shape8(xi, eta)
            return cell_index, node_tags, weights, hole_ids, face_side, [layer_index]

        # Thickness-edge contacts use the corresponding exterior side face of
        # the actual four-layer solid.  This keeps partial-depth coordinates
        # explicit and avoids projecting edge contacts onto a broad-face mesh.
        if abs(x - x0) <= tolerance:
            edge_kind, edge_sign, along = "x", -1, y
        elif abs(x - x1) <= tolerance:
            edge_kind, edge_sign, along = "x", 1, y
        elif abs(y - y0) <= tolerance:
            edge_kind, edge_sign, along = "y", -1, x
        elif abs(y - y1) <= tolerance:
            edge_kind, edge_sign, along = "y", 1, x
        else:
            raise ValueError(f"Panel point is inside the STEP solid, not on a surface: {panel_id}")
        if w < self.layer_offsets_mm[0] - tolerance or w > self.layer_offsets_mm[-1] + tolerance:
            raise ValueError(f"Panel edge point is outside its STEP thickness: {panel_id}")
        layer_index = next((index for index, (low, high) in enumerate(
            zip(self.layer_offsets_mm[:-1], self.layer_offsets_mm[1:], strict=True))
            if low - tolerance <= w <= high + tolerance), None)
        if layer_index is None:
            raise ValueError("Panel thickness coordinate is outside native layer stations")
        if edge_kind == "x":
            i = 0 if edge_sign < 0 else len(panel.x_axes) - 2
            j = self._interval(panel.y_axes, along, tolerance)
            face_positions = ([0, 3, 7, 4, 11, 19, 15, 16] if edge_sign < 0
                              else [1, 2, 6, 5, 9, 18, 13, 17])
            q0, q1 = panel.y_axes[j], panel.y_axes[j + 1]
        else:
            j = 0 if edge_sign < 0 else len(panel.y_axes) - 2
            i = self._interval(panel.x_axes, along, tolerance)
            face_positions = ([0, 1, 5, 4, 8, 17, 12, 16] if edge_sign < 0
                              else [3, 2, 6, 7, 10, 18, 14, 19])
            q0, q1 = panel.x_axes[i], panel.x_axes[i + 1]
        cell_index = j * (len(panel.x_axes) - 1) + i
        connectivity = panel.cell_face_nodes[cell_index][layer_index]
        node_tags = [connectivity[index] for index in face_positions]
        w0, w1 = self.layer_offsets_mm[layer_index:layer_index + 2]
        xi = 2. * (along - q0) / (q1 - q0) - 1.
        eta = 2. * (w - w0) / (w1 - w0) - 1.
        weights = frame.shape8(xi, eta)
        return cell_index, node_tags, weights, [], edge_sign, [layer_index]

    def attach(self, panel_id: str, point_xyz_mm: Any, *, label: str | None = None,
               allow_source_hole: bool = False) -> int:
        """Tie a coincident point to its true STEP-derived C3D20 surface face."""
        point = _v3(point_xyz_mm, "Panel attachment point")
        cell, nodes, weights, hole_ids, side, _ = self._element_and_face(panel_id, point)
        if hole_ids and not allow_source_hole:
            raise ValueError(
                f"Panel attachment falls in source bore(s) {hole_ids}; mark the declared screw/hold bore explicitly")
        reconstructed = sum((weight * np.asarray(self.structure.nodes[node], dtype=float)
                             for node, weight in zip(nodes, weights, strict=True)), np.zeros(3))
        if (abs(float(np.sum(weights)) - 1.) > 1e-10
                or np.linalg.norm(reconstructed - point) > 2e-5):
            raise ValueError("Panel C3D20 face interpolation lost affine geometry")
        tag = self.structure.node(point)
        for dof in (1, 2, 3):
            terms = [(tag, dof, 1.)] + [
                (node, dof, -float(weight)) for node, weight in zip(nodes, weights, strict=True)
                if abs(weight) > 1e-13]
            self.structure.equations.append(terms)
        if label:
            self.metadata.setdefault("attachments", {})[label] = {
                "panel_id": panel_id, "point_xyz_mm": point.tolist(),
                "face_side": side, "source_hole_ids": hole_ids,
                "element_index": cell, "qualified_for_design": False,
            }
        return tag

    def attach_panel_screw_axes(self, point_overrides: Mapping[str, Any] | None = None) -> dict[str, int]:
        """Attach all 66 frozen panel-screw axes at caller-selected panel points.

        By default the input axis station is used.  Supply ``axis_id`` overrides
        when the parent assembly has selected the opposite panel/wood interface
        point along that physical axis.
        """
        overrides = dict(point_overrides or {})
        expected = {row["axis_id"] for row in self.screw_records}
        if set(overrides) - expected:
            raise ValueError("Panel screw point overrides contain unknown current axes")
        result = {}
        for row in self.screw_records:
            axis_id = row["axis_id"]
            panel_id = row["source_record"]["panel_member"]
            point = overrides.get(axis_id, row["source_point_xyz_mm"])
            result[axis_id] = self.attach(panel_id, point, label="panel_screw/" + axis_id,
                                           allow_source_hole=True)
        self.screw_nodes.update(result)
        return result

    def attach_contact_patch_centroids(self) -> dict[str, int]:
        """Attach all frozen panel/frame contact patch centroids as independent points."""
        result = {}
        for row in self.contact_patches:
            panel_ids = [name for name in row["member_ids"] if name in self.panels]
            if len(panel_ids) != 1:
                continue
            panel_id = panel_ids[0]
            key = f"{row['member_ids'][0]}__{row['member_ids'][1]}__{row['patch_index']}"
            result[key] = self.attach(panel_id, row["centroid_xyz_mm"], label="contact/" + key)
        self.contact_nodes.update(result)
        return result

    def _add_load_record(self, label: str, panel_id: str, reference: np.ndarray,
                         expected_force: np.ndarray, expected_moment: np.ndarray,
                         tagged_forces: list[tuple[int, np.ndarray]], **details: Any) -> dict[str, Any]:
        for tag, force in tagged_forces:
            frame.add_load(self.structure, tag, force)
        record = {
            "label": label, "panel_id": panel_id,
            "reference_xyz_mm": reference.tolist(),
            "expected_force_xyz_n": expected_force.tolist(),
            "expected_moment_xyz_nmm": expected_moment.tolist(),
            "nodal_forces": [(int(tag), np.asarray(force, dtype=float).tolist())
                             for tag, force in tagged_forces],
            **details,
        }
        self.load_records.append(record)
        return record

    def add_point_wrench(self, panel_id: str, point_xyz_mm: Any,
                         force_xyz_n: Any = (0., 0., 0.),
                         moment_xyz_nmm: Any = (0., 0., 0.), *,
                         moment_reference_xyz_mm: Any | None = None,
                         label: str = "panel-point-wrench",
                         allow_source_hole: bool = False) -> dict[str, Any]:
        point = _v3(point_xyz_mm, "Point-wrench application point")
        force = _v3(force_xyz_n, "Point-wrench force")
        moment = _v3(moment_xyz_nmm, "Point-wrench moment")
        reference = point if moment_reference_xyz_mm is None else _v3(
            moment_reference_xyz_mm, "Point-wrench reference point")
        node = self.attach(panel_id, point, label=label + "/point",
                           allow_source_hole=allow_source_hole)
        tagged_forces: list[tuple[int, np.ndarray]] = []
        if np.linalg.norm(force) > 0:
            tagged_forces.append((node, force))
        point_moment = moment + np.cross(reference - point, force)
        if np.linalg.norm(point_moment) > 0:
            _, face_nodes, _, hole_ids, _, _ = self._element_and_face(panel_id, point)
            if hole_ids and not allow_source_hole:
                raise ValueError("Point moment lies at an undeclared source panel bore")
            positions = [self.structure.nodes[tag] for tag in face_nodes]
            couple = frame.distribute_wrench(positions, np.zeros(3), point_moment, point)
            tagged_forces.extend((tag, value) for tag, value in zip(face_nodes, couple, strict=True))
        return self._add_load_record(label, panel_id, reference, force, moment,
                                     tagged_forces, load_kind="point_wrench",
                                     point_xyz_mm=point.tolist())

    def add_patch_wrench(self, panel_id: str, center_xyz_mm: Any,
                         patch_size_mm: float, force_xyz_n: Any,
                         moment_xyz_nmm: Any, *,
                         moment_reference_xyz_mm: Any | None = None,
                         label: str = "panel-patch-wrench") -> dict[str, Any]:
        """Apply a consistent uniform S8 patch resultant and preserve its wrench."""
        self._require_bound()
        if not math.isfinite(patch_size_mm) or patch_size_mm <= 0:
            raise ValueError("Patch width must be finite and positive")
        panel = self.panels[panel_id]
        centre = _v3(center_xyz_mm, "Patch center")
        force = _v3(force_xyz_n, "Patch force")
        moment = _v3(moment_xyz_nmm, "Patch moment")
        reference = centre if moment_reference_xyz_mm is None else _v3(
            moment_reference_xyz_mm, "Patch-wrench reference point")
        x, y, w = self.local_point(panel_id, centre)
        geometry = panel.geometry
        if min(abs(w + geometry["thickness_mm"] / 2.),
               abs(w - geometry["thickness_mm"] / 2.)) > 1e-5:
            raise ValueError("Applied panel patch center must lie on an actual STEP broad face")
        patch = (x - patch_size_mm / 2., x + patch_size_mm / 2.,
                 y - patch_size_mm / 2., y + patch_size_mm / 2.)
        x0, x1, y0, y1 = geometry["bounds_local_mm"]
        if patch[0] < x0 - 1e-7 or patch[1] > x1 + 1e-7 or patch[2] < y0 - 1e-7 or patch[3] > y1 + 1e-7:
            raise ValueError("Applied square patch extends outside the actual STEP panel outline")
        side = -1 if w < 0 else 1
        weights, area = frame.panel_kernel.pressure_load(panel.local_nodes, panel.elements, patch, 1.)
        if not math.isclose(area, patch_size_mm ** 2, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("Applied square patch is not fully imprinted in the panel mesh")
        tags = panel.surface_node_tags_by_side[side]
        local_nodes = list(weights)
        node_tags = [tags[node] for node in local_nodes]
        positions = [self.structure.nodes[tag] for tag in node_tags]
        moment_at_center = moment + np.cross(reference - centre, force)
        values = frame.traction_wrench(positions, [weights[node] for node in local_nodes],
                                       force, moment_at_center, centre)
        tagged = list(zip(node_tags, values, strict=True))
        record = self._add_load_record(label, panel_id, reference, force, moment,
            tagged, load_kind="uniform_square_patch_wrench", center_xyz_mm=centre.tolist(),
            patch_local_mm=list(patch), patch_area_mm2=area, patch_size_mm=patch_size_mm,
            broadface_side=side, moment_at_patch_center_xyz_nmm=moment_at_center.tolist(),
            source_bores_overlapping_patch=self._patch_hole_overlaps(geometry, patch, side))
        return record

    def add_case_patch_wrench(self, case: Mapping[str, Any]) -> dict[str, Any]:
        source = case["source_applied_load"]
        panel_id = str(case["loaded_panel"])
        return self.add_patch_wrench(panel_id, source["patch_center_global_xyz_mm"],
            float(source["patch_size_mm"]), source["applied_force_global_xyz_n"],
            source["moment_global_xyz_nmm"],
            moment_reference_xyz_mm=source["wrench_reference_point_global_xyz_mm"],
            label=str(case["case_id"]))

    @staticmethod
    def _patch_hole_overlaps(geometry: Mapping[str, Any], patch: tuple[float, float, float, float],
                             side: int) -> list[int]:
        left, right, low, high = patch
        matches = []
        for index, hole in enumerate(geometry["source_bores"]):
            if hole["side"] != side:
                continue
            if "radius_mm" in hole:
                x, y = hole["centre_local_mm"]
                nearest = np.array([min(right, max(left, x)), min(high, max(low, y))])
                if np.linalg.norm(nearest - np.array([x, y])) <= hole["radius_mm"]:
                    matches.append(index)
        return matches

    def audit_wrenches(self, *, force_tolerance_n: float = 1e-7,
                       moment_tolerance_nmm: float = 1e-5) -> dict[str, Any]:
        """Recover each adapter-added load's resultant at its declared reference."""
        rows = []
        for record in self.load_records:
            force = np.zeros(3)
            moment = np.zeros(3)
            for tag, value in record["nodal_forces"]:
                nodal_force = np.asarray(value, dtype=float)
                point = np.asarray(self.structure.nodes[tag], dtype=float)
                force += nodal_force
                moment += np.cross(point - np.asarray(record["reference_xyz_mm"]), nodal_force)
            force_error = force - np.asarray(record["expected_force_xyz_n"])
            moment_error = moment - np.asarray(record["expected_moment_xyz_nmm"])
            passed = (max(abs(force_error)) <= force_tolerance_n
                      and max(abs(moment_error)) <= moment_tolerance_nmm)
            rows.append({"label": record["label"], "panel_id": record["panel_id"],
                "force_xyz_n": force.tolist(), "moment_xyz_nmm": moment.tolist(),
                "force_residual_xyz_n": force_error.tolist(),
                "moment_residual_xyz_nmm": moment_error.tolist(), "passed": bool(passed)})
        return {"load_count": len(rows), "all_passed": all(row["passed"] for row in rows),
                "loads": rows, "force_tolerance_n": force_tolerance_n,
                "moment_tolerance_nmm": moment_tolerance_nmm}


def _patch_landmarks(cases: list[dict[str, Any]],
                     panels: dict[str, dict[str, Any]]) -> dict[str, tuple[list[float], list[float]]]:
    x_values: dict[str, list[float]] = {name: [] for name in panels}
    y_values: dict[str, list[float]] = {name: [] for name in panels}
    for case in cases:
        panel_id = str(case["loaded_panel"])
        if panel_id not in panels:
            raise ValueError("Frozen load case refers to a panel outside the six current STEP panels")
        source = case["source_applied_load"]
        centre = _v3(source["patch_center_global_xyz_mm"], "Frozen load patch center")
        geometry = panels[panel_id]
        delta = centre - geometry["origin_xyz_mm"]
        x, y, depth = float(delta @ geometry["axis_u_xyz"]), float(delta @ geometry["axis_v_xyz"]), float(delta @ geometry["normal_xyz"])
        if min(abs(depth + geometry["thickness_mm"] / 2.),
               abs(depth - geometry["thickness_mm"] / 2.)) > 1e-5:
            raise ValueError(f"Frozen case patch center is not on its STEP panel: {case['case_id']}")
        size = float(source["patch_size_mm"])
        if not math.isfinite(size) or size <= 0:
            raise ValueError("Frozen case patch width must be finite and positive")
        x_values[panel_id].extend((x - size / 2., x + size / 2.))
        y_values[panel_id].extend((y - size / 2., y + size / 2.))
    return {name: (x_values[name], y_values[name]) for name in panels}


def add_current_panels(structure: Any,
                       member_geometry: str | Path | Mapping[str, Any],
                       model_inputs: str | Path | Mapping[str, Any], *,
                       contact_geometry: str | Path | Mapping[str, Any] | None = None,
                       mesh_size_mm: float = 100.) -> ReducedPanelAssembly:
    """Mesh six frozen current STEP panels into an existing CurrentStructure.

    Only load-patch boundaries are imprinted in the Cartesian panel grids.
    Screw and contact points remain arbitrary STEP surface locations and are
    tied later by quadratic face interpolation.  Call ``layered_panels()`` on
    the structure, then ``assembly.bind_layered_structure()``, before attaching
    points or applying loads.
    """
    if not math.isfinite(mesh_size_mm) or mesh_size_mm <= 0:
        raise ValueError("Panel mesh size must be finite and positive")
    if not hasattr(structure, "materials") or "panel_layers" not in structure.materials:
        raise ValueError("Require current_response_model.CurrentStructure panel_layers properties")
    geometry_doc, inputs = _document(member_geometry), _document(model_inputs)
    geometry_revision = geometry_doc.get("geometry_revision_id")
    if (geometry_doc.get("candidate") != inputs.get("candidate")
            or geometry_revision != inputs.get("revision_id")):
        raise ValueError("Current panel geometry and response inputs belong to different revisions")
    descriptors = geometry_doc.get("panels", [])
    by_name = {str(row["panel_id"]): row for row in descriptors}
    if set(by_name) != EXPECTED_PANEL_IDS or len(descriptors) != len(EXPECTED_PANEL_IDS):
        raise ValueError("Require exactly the six frozen current panel STEP descriptors")
    screws = [row for row in inputs.get("connections", []) if row.get("kind") == "panel_screw"]
    if len(screws) != 66 or len({row["axis_id"] for row in screws}) != 66:
        raise ValueError("Require the 66 unique frozen current panel screw axes")
    if any(row.get("source_record", {}).get("panel_member") not in by_name for row in screws):
        raise ValueError("Frozen panel screw inventory refers to an unbound panel")
    cases = list(inputs.get("cases", []))
    if len(cases) != 6 or len({row["case_id"] for row in cases}) != 6:
        raise ValueError("Require all six frozen reduced-static load cases")
    contact_doc = {} if contact_geometry is None else _document(contact_geometry)
    contacts = list(contact_doc.get("contact_patches", []))
    if contact_geometry is not None:
        if (contact_doc.get("candidate") != inputs.get("candidate")
                or contact_doc.get("revision_id") != inputs.get("revision_id")):
            raise ValueError("Current contact geometry and response inputs belong to different revisions")

    geometries = {name: _source_panel_geometry(by_name[name]) for name in sorted(by_name)}
    if any(abs(g["thickness_mm"] - frame.panel_kernel.THICKNESS) > 1e-5
           for g in geometries.values()):
        raise ValueError("Current STEP panel thickness differs from the native equivalent-layer thickness")
    landmarks = _patch_landmarks(cases, geometries)
    panel_meshes = {}
    for name, geometry in geometries.items():
        x0, x1, y0, y1 = geometry["bounds_local_mm"]
        patch_x, patch_y = landmarks[name]
        x_axes = frame.panel_kernel.mesh_axes(x0, x1, mesh_size_mm, patch_x)
        y_axes = frame.panel_kernel.mesh_axes(y0, y1, mesh_size_mm, patch_y)
        local_nodes, elements, lookup = cut_panel_mesh(x_axes, y_axes, ())
        node_tags = {}
        for local_id, local in local_nodes.items():
            world = (geometry["origin_xyz_mm"]
                     + float(local[0]) * geometry["axis_u_xyz"]
                     + float(local[1]) * geometry["axis_v_xyz"])
            node_tags[local_id] = structure.node(world)
        cell_bounds = []
        for local_ids in elements.values():
            corners = np.array([local_nodes[node] for node in local_ids[:4]], dtype=float)
            cell_bounds.append((float(corners[:, 0].min()), float(corners[:, 0].max()),
                                float(corners[:, 1].min()), float(corners[:, 1].max())))
        element_tags = []
        for local_ids in elements.values():
            element_tags.append(structure.element("S8", [node_tags[node] for node in local_ids], name))
        structure.panels[name] = {"nodes": list(node_tags.values()),
                                  "normal": geometry["normal_xyz"].tolist()}
        weights, area = retained_panel_weights(local_nodes, elements)
        geometry["mesh_retained_area_mm2"] = area
        geometry["mesh_area_weights"] = weights
        panel = _PanelMesh(geometry, local_nodes, elements, lookup, cell_bounds, node_tags)
        panel.x_axes, panel.y_axes = x_axes, y_axes
        panel.element_tags = element_tags
        panel.surface_node_tags_by_side = {}
        panel_meshes[name] = panel

    assembly = ReducedPanelAssembly(structure, panel_meshes, screws, cases, contacts)
    return assembly


def build_demo(mesh_size_mm: float = 120.) -> dict[str, Any]:
    """Build, layer, attach frozen points and audit six patch wrenches; no solve."""
    from fea.current_response_materials import materials
    from fea.current_response_model import CurrentStructure

    root = REPOSITORY / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01"
    structure = CurrentStructure(materials())
    assembly = add_current_panels(structure, root / "member-geometry.json",
        root / "model-inputs.json", contact_geometry=root / "contact-geometry.json",
        mesh_size_mm=mesh_size_mm)
    structure.layered_panels()
    assembly.bind_layered_structure()
    assembly.attach_panel_screw_axes()
    assembly.attach_contact_patch_centroids()
    for case in assembly.case_records:
        assembly.add_case_patch_wrench(case)
    audit = assembly.audit_wrenches()
    if not audit["all_passed"]:
        raise ValueError("Reduced panel case loads failed force/moment conservation")
    return {"panel_count": len(assembly.panels), "screw_attachment_count": len(assembly.screw_nodes),
            "contact_attachment_count": len(assembly.contact_nodes),
            "panel_metadata": assembly.metadata["panels"], "wrench_audit": audit,
            "native_solve_executed": False}


if __name__ == "__main__":
    report = build_demo()
    summary = {"panel_count": report["panel_count"],
        "mesh_element_counts": {name: row["mesh_element_count"]
                                for name, row in report["panel_metadata"].items()},
        "screw_attachment_count": report["screw_attachment_count"],
        "contact_attachment_count": report["contact_attachment_count"],
        "source_face_detail": {name: {"front_back_area_mm2": row["broadface_area_mm2"],
            "outline_mismatch_mm": row["outline_mismatch_mm"],
            "source_bore_count_by_side": row["source_bore_count_by_side"]}
            for name, row in report["panel_metadata"].items()},
        "wrench_load_count": report["wrench_audit"]["load_count"],
        "wrench_conservation_passed": report["wrench_audit"]["all_passed"],
        "native_solve_executed": report["native_solve_executed"]}
    print(json.dumps(summary, indent=2))
