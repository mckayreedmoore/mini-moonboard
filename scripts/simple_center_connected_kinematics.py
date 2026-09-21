"""Small-displacement point-constraint rank of the current PB-02 center loop."""

import hashlib
import itertools
import json

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from scripts.simple_center_pb02_geometry import (
    ACTIVE_FINGERPRINT,
    ACTIVE_TRIAL,
    active_geometry,
)

# Coordinates are global millimeters. The first four edges use the current
# shorter_8in_trial and tolerance-pose bores. The return path uses the inherited
# post_low/high, cleat_link, and upright bores in the same pose.
NODES = (
    "post",
    "post_block",
    "header",
    "principal_block",
    "principal",
    "upright_block",
    "rear_block",
)
NODE_PARTS = {
    "post": "shifted_right_post",
    "post_block": "header_post_side_cleat",
    "header": "base_header",
    "principal_block": "header_side_cleat",
    "principal": "base_principal_center_right",
    "upright_block": "upright_side_cleat",
    "rear_block": "rear_cleat",
}
EDGE_BORE_NAMES = {
    "post_block": ("post_cleat_1", "post_cleat_2"),
    "block_header": ("cleat_header_1", "cleat_header_2"),
    "header_principal_block": ("header_cleat",),
    "principal_block_principal": ("cleat_principal",),
    "principal_upright_block": ("upright",),
    "upright_rear_block": ("cleat_link",),
    "rear_block_post": ("post_low", "post_high"),
}
DEFAULT_CONTACT_GRID = (2, 2)


def _midpoint(first, second):
    return tuple((a + b) / 2 for a, b in zip(first, second))


def _convex_overlap(first_points, second_points):
    """Return the exact convex intersection of two coplanar face polygons."""
    equations = []
    for points in (first_points, second_points):
        equations.extend(ConvexHull(np.asarray(points)).equations)
    coefficients = np.asarray(equations)[:, :2]
    offsets = np.asarray(equations)[:, 2]
    vertices = []
    for first, second in itertools.combinations(range(len(coefficients)), 2):
        pair = coefficients[[first, second]]
        if abs(np.linalg.det(pair)) < 1.0e-10:
            continue
        point = np.linalg.solve(pair, -offsets[[first, second]])
        if np.max(coefficients @ point + offsets) <= 1.0e-6 and not any(
            np.linalg.norm(point - existing) < 1.0e-6 for existing in vertices
        ):
            vertices.append(point)
    if len(vertices) < 3:
        raise ValueError("PB02 contact faces have no positive polygon overlap")
    polygon = np.asarray(vertices)
    return polygon[ConvexHull(polygon).vertices]


def _face_polygon(shape, normal_index, interface_coordinate):
    """Project the true planar CAD face at one interface into global tangent axes."""
    tangents = tuple(index for index in range(3) if index != normal_index)
    candidates = []
    for face in shape.Faces():
        normal = np.asarray(face.normalAt().toTuple())
        center = np.asarray(face.Center().toTuple())
        if (
            abs(abs(normal[normal_index]) - 1.0) < 1.0e-7
            and abs(center[normal_index] - interface_coordinate) < 1.0e-6
        ):
            points = np.unique(
                [
                    np.asarray(vertex.Center().toTuple())[list(tangents)]
                    for vertex in face.Vertices()
                ],
                axis=0,
            )
            if len(points) >= 3:
                candidates.append(points)
    if len(candidates) != 1:
        raise ValueError("PB02 interface must resolve to one true planar CAD face")
    return candidates[0], tangents


def _point_in_convex_polygon(point, polygon, tolerance=1.0e-6):
    hull = ConvexHull(np.asarray(polygon))
    return bool(
        np.max(hull.equations[:, :2] @ point + hull.equations[:, 2]) <= tolerance
    )


def _contact_cells(
    name,
    parts,
    bores,
    first,
    second,
    normal,
    interface_coordinate,
    resolution,
):
    """Partition exact net face overlap into finite rectangular-grid cells."""
    normal_index = next(index for index, value in enumerate(normal) if value)
    first_polygon, tangents = _face_polygon(
        parts[NODE_PARTS[first]], normal_index, interface_coordinate
    )
    second_polygon, second_tangents = _face_polygon(
        parts[NODE_PARTS[second]], normal_index, interface_coordinate
    )
    if tangents != second_tangents:
        raise ValueError("PB02 interface tangent axes changed")
    overlap = _convex_overlap(first_polygon, second_polygon)

    def xyz(point):
        result = np.zeros(3)
        result[normal_index] = interface_coordinate
        result[list(tangents)] = point
        return cq.Vector(*result)

    outer = cq.Wire.makePolygon([xyz(point) for point in overlap], close=True)
    bore_data = []
    hole_wires = []
    normal_vector = np.zeros(3)
    normal_vector[normal_index] = 1.0
    for bore_name in EDGE_BORE_NAMES[name]:
        bounds = bores[bore_name].BoundingBox()
        radius = min(bounds.xlen, bounds.ylen, bounds.zlen) / 2.0
        center = np.asarray(bores[bore_name].Center().toTuple())
        projected = center[list(tangents)]
        if not _point_in_convex_polygon(projected, overlap):
            raise ValueError(
                f"PB02 bore center is outside contact overlap: {bore_name}"
            )
        bore_data.append((projected, radius))
        hole_wires.append(
            cq.Wire.makeCircle(
                radius,
                xyz(projected),
                cq.Vector(*normal_vector),
            )
        )
    net_face = cq.Face.makeFromWires(outer, hole_wires)
    expected_net_area = ConvexHull(overlap).volume - sum(
        np.pi * radius**2 for _, radius in bore_data
    )
    if abs(net_face.Area() - expected_net_area) > 1.0e-5:
        raise ValueError("PB02 net contact face area does not match bore deduction")

    low = overlap.min(axis=0)
    high = overlap.max(axis=0)
    cells = []
    for row, column in itertools.product(range(resolution[0]), range(resolution[1])):
        cell_low = low + (high - low) * np.array(
            (row / resolution[0], column / resolution[1])
        )
        cell_high = low + (high - low) * np.array(
            ((row + 1) / resolution[0], (column + 1) / resolution[1])
        )
        rectangle = cq.Face.makeFromWires(
            cq.Wire.makePolygon(
                [
                    xyz((cell_low[0], cell_low[1])),
                    xyz((cell_high[0], cell_low[1])),
                    xyz((cell_high[0], cell_high[1])),
                    xyz((cell_low[0], cell_high[1])),
                ],
                close=True,
            )
        )
        clipped = net_face.intersect(rectangle)
        faces = sorted(
            (face for face in clipped.Faces() if face.Area() > 1.0e-9),
            key=lambda face: face.Center().toTuple(),
        )
        # Empty grid cells and multiple disconnected positive components are
        # both valid outcomes for clipped or perforated overlap polygons.
        for component, face in enumerate(faces):
            point = np.asarray(face.Center().toTuple())
            projected = point[list(tangents)]
            inside_faces = _point_in_convex_polygon(
                projected, first_polygon
            ) and _point_in_convex_polygon(projected, second_polygon)
            outside_bores = all(
                np.linalg.norm(projected - center) > radius + 1.0e-7
                for center, radius in bore_data
            )
            if not inside_faces or not outside_bores:
                raise ValueError(
                    "PB02 contact component centroid is not on the net true face"
                )
            cells.append(
                {
                    "cell_id": f"r{row + 1}c{column + 1}p{component + 1}",
                    "grid_row": row + 1,
                    "grid_column": column + 1,
                    "component": component + 1,
                    "point_mm": tuple(point),
                    "tributary_area_mm2": face.Area(),
                    "net_overlap_area_mm2": net_face.Area(),
                    "gross_overlap_area_mm2": ConvexHull(overlap).volume,
                    "bore_area_mm2": ConvexHull(overlap).volume - net_face.Area(),
                    "inside_both_true_faces": inside_faces,
                    "outside_all_bore_footprints": outside_bores,
                }
            )
    if (
        abs(sum(cell["tributary_area_mm2"] for cell in cells) - net_face.Area())
        > 1.0e-5
    ):
        raise ValueError("PB02 tributary contact cells do not cover net face overlap")
    expected_first_moment = net_face.Area() * np.asarray(net_face.Center().toTuple())
    actual_first_moment = sum(
        (cell["tributary_area_mm2"] * np.asarray(cell["point_mm"]) for cell in cells),
        np.zeros(3),
    )
    if not np.allclose(actual_first_moment, expected_first_moment, atol=1.0e-4):
        raise ValueError("PB02 tributary contact cells do not preserve first moments")
    return tuple(cells), {
        "grid_resolution": list(resolution),
        "gross_overlap_area_mm2": ConvexHull(overlap).volume,
        "bore_area_mm2": ConvexHull(overlap).volume - net_face.Area(),
        "net_overlap_area_mm2": net_face.Area(),
        "net_centroid_mm": list(net_face.Center().toTuple()),
        "net_first_moment_mm3": expected_first_moment.tolist(),
        "positive_component_count": len(cells),
    }


def _resolution(value):
    if type(value) is int:
        value = (value, value)
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(type(item) is not int or item < 2 for item in value)
    ):
        raise ValueError("PB02 contact grid must be an integer pair of at least 2x2")
    return value


def _partition_fingerprint(resolution, contacts, interfaces):
    payload = {
        "schema": "pb02-canonical-contact-partition/v1",
        "active_geometry_fingerprint": ACTIVE_FINGERPRINT,
        "grid_resolution": list(resolution),
        "interfaces": {
            name: {
                **interfaces[name],
                "cells": [
                    {
                        "cell_id": cell["cell_id"],
                        "point_mm": [round(value, 12) for value in cell["point_mm"]],
                        "tributary_area_mm2": round(cell["tributary_area_mm2"], 12),
                    }
                    for cell in contacts[name]
                ],
            }
            for name in contacts
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _current_edges_and_contacts(resolution=DEFAULT_CONTACT_GRID):
    """Build bolt centers and exact contact cells from active PB02 CAD."""
    resolution = _resolution(resolution)
    parts, bores, ends = active_geometry()

    def center(first, second):
        return _midpoint(ends[first][0], ends[second][0])

    edges = {
        "post_block": (
            "post",
            "post_block",
            (1, 0, 0),
            [center(f"post_cleat_{i}_left", f"post_cleat_{i}_right") for i in (1, 2)],
        ),
        "block_header": (
            "post_block",
            "header",
            (0, 0, 1),
            [
                center(f"cleat_header_{i}_bottom", f"cleat_header_{i}_top")
                for i in (1, 2)
            ],
        ),
        "header_principal_block": (
            "header",
            "principal_block",
            (0, 0, 1),
            [center("principal_header_bottom", "principal_cleat_top")],
        ),
        "principal_block_principal": (
            "principal_block",
            "principal",
            (1, 0, 0),
            [center("principal_cleat_left", "principal_right")],
        ),
        "principal_upright_block": (
            "principal",
            "upright_block",
            (1, 0, 0),
            [center("upright_left", "upright_right")],
        ),
        "upright_rear_block": (
            "upright_block",
            "rear_block",
            (0, -1, 0),
            [center("link_rear", "link_front")],
        ),
        "rear_block_post": (
            "rear_block",
            "post",
            (0, 1, 0),
            [
                center(f"post_rear_{name}", f"post_front_{name}")
                for name in ("low", "high")
            ],
        ),
    }
    bounds = {node: parts[part].BoundingBox() for node, part in NODE_PARTS.items()}
    axes = ("x", "y", "z")
    result = {}
    contacts = {}
    interfaces = {}
    for name, (first, second, normal, bolts) in edges.items():
        normal_index = next(index for index, value in enumerate(normal) if value)
        first_box, second_box = bounds[first], bounds[second]
        normal_axis = axes[normal_index]
        first_face = getattr(
            first_box, f"{normal_axis}{'max' if normal[normal_index] > 0 else 'min'}"
        )
        second_face = getattr(
            second_box, f"{normal_axis}{'min' if normal[normal_index] > 0 else 'max'}"
        )
        if abs(first_face - second_face) > 1e-6:
            raise ValueError(f"PB02 contact faces do not coincide: {name}")
        center = []
        for index, axis in enumerate(axes):
            if index == normal_index:
                center.append(first_face)
                continue
            low = max(
                getattr(first_box, f"{axis}min"), getattr(second_box, f"{axis}min")
            )
            high = min(
                getattr(first_box, f"{axis}max"), getattr(second_box, f"{axis}max")
            )
            if high - low < 40:
                raise ValueError(f"PB02 contact patch cannot hold rank samples: {name}")
            center.append((low + high) / 2)
        result[name] = (first, second, normal, bolts, tuple(center))
        contacts[name], interfaces[name] = _contact_cells(
            name,
            parts,
            bores,
            first,
            second,
            normal,
            first_face,
            resolution,
        )
        interfaces[name].update(
            {
                "first": first,
                "second": second,
                "first_part": NODE_PARTS[first],
                "second_part": NODE_PARTS[second],
                "canonical_first_to_second_normal": list(normal),
            }
        )
    partition = {
        "schema": "pb02-canonical-contact-partition/v1",
        "grid_resolution": list(resolution),
        "interfaces": interfaces,
        "contact_row_count": sum(len(cells) for cells in contacts.values()),
    }
    partition["fingerprint"] = _partition_fingerprint(resolution, contacts, interfaces)
    return result, contacts, partition


def current_edges():
    """Return current rank-model edges from the same active PB02 geometry as CAD."""
    return _current_edges_and_contacts()[0]


def contact_partition(resolution=DEFAULT_CONTACT_GRID):
    """Return a deterministic exact-face partition at the requested resolution."""
    _, contacts, partition = _current_edges_and_contacts(resolution)
    return contacts, partition


EDGES, CONTACT_CELLS, CONTACT_PARTITION = _current_edges_and_contacts()
CONTACT_PARTITION_FINGERPRINT = CONTACT_PARTITION["fingerprint"]
ORIGIN = np.array((140.0, -140.0, 270.0))
ROTATION_SCALE_MM = 100.0


def _point_row(first, second, direction, point):
    """Relative point velocity in one direction; rotations use 100-mm scaling."""
    direction = np.asarray(direction, dtype=float)
    lever = (np.asarray(point, dtype=float) - ORIGIN) / ROTATION_SCALE_MM
    local = np.r_[direction, np.cross(lever, direction)]
    row = np.zeros(6 * len(NODES))
    for node, sign in ((first, -1), (second, 1)):
        start = 6 * NODES.index(node)
        row[start : start + 6] += sign * local
    return row


def constraint_rows(
    *,
    closed=(),
    axial=True,
    return_path=True,
    contact_grid_resolution=DEFAULT_CONTACT_GRID,
    contact_partition_bundle=None,
):
    """Return labeled point constraints before an optional coordinate anchor."""
    if contact_partition_bundle is None:
        resolution = _resolution(contact_grid_resolution)
        if resolution == DEFAULT_CONTACT_GRID:
            contact_cells, partition = CONTACT_CELLS, CONTACT_PARTITION
        else:
            contact_cells, partition = contact_partition(resolution)
    else:
        contact_cells, partition = contact_partition_bundle
        if tuple(partition["grid_resolution"]) != _resolution(contact_grid_resolution):
            raise ValueError("PB02 contact partition bundle resolution changed")
    rows = []
    for name, (first, second, normal, bolts, contact_center) in EDGES.items():
        if not return_path and name in (
            "principal_upright_block",
            "upright_rear_block",
            "rear_block_post",
        ):
            continue
        n = np.asarray(normal, dtype=float)
        tangents = [axis for axis in np.eye(3) if abs(axis @ n) < 0.5]
        for bolt_index, point in enumerate(bolts, 1):
            rows.extend(
                {
                    "name": f"{name}/bolt_{bolt_index}/shear_{index}",
                    "edge": name,
                    "kind": "bolt_shear",
                    "first": first,
                    "second": second,
                    "direction": tuple(tangent),
                    "point_mm": tuple(point),
                    "row": _point_row(first, second, tangent, point),
                }
                for index, tangent in enumerate(tangents, 1)
            )
            if axial:
                rows.append(
                    {
                        "name": f"{name}/bolt_{bolt_index}/tension",
                        "edge": name,
                        "kind": "bolt_tension",
                        "first": first,
                        "second": second,
                        "direction": tuple(n),
                        "point_mm": tuple(point),
                        "row": _point_row(first, second, n, point),
                    }
                )
        if name in closed:
            for cell in contact_cells[name]:
                point = cell["point_mm"]
                rows.append(
                    {
                        "name": f"{name}/contact_{cell['cell_id']}",
                        "edge": name,
                        "kind": "contact_compression",
                        "first": first,
                        "second": second,
                        "direction": tuple(n),
                        "point_mm": tuple(point),
                        "tributary_area_mm2": cell["tributary_area_mm2"],
                        "net_overlap_area_mm2": cell["net_overlap_area_mm2"],
                        "contact_partition_fingerprint": (partition["fingerprint"]),
                        "contact_grid_resolution": tuple(partition["grid_resolution"]),
                        "row": _point_row(first, second, n, point),
                    }
                )
    return rows


def matrix(*, closed=(), axial=True, return_path=True, anchor_post=True):
    """Closed faces supply four normal rows; open faces supply none."""
    rows = constraint_rows(closed=closed, axial=axial, return_path=return_path)
    values = np.asarray([item["row"] for item in rows])
    # Fixing the post removes six arbitrary whole-assembly rigid motions only.
    anchored = values[:, 6:] if anchor_post else values
    if not return_path:
        anchored = anchored[:, : 6 * (4 if anchor_post else 5)]
    return anchored


def nullity(*, closed=(), axial=True, return_path=True, anchor_post=True):
    mat = matrix(
        closed=closed, axial=axial, return_path=return_path, anchor_post=anchor_post
    )
    rank = int(np.linalg.matrix_rank(mat, tol=1e-9))
    return {"rank": rank, "relative_dof": mat.shape[1] - rank}


def screen():
    names = tuple(EDGES)
    return {
        "variant_id": ACTIVE_TRIAL.variant_id,
        "source_fingerprint": ACTIVE_FINGERPRINT,
        "nodes": NODES,
        "edges": {
            name: {
                "members": edge[:2],
                "normal": edge[2],
                "bolt_centers_mm": edge[3],
                "contact_patch_center_mm": edge[4],
            }
            for name, edge in EDGES.items()
        },
        "contact_partition": CONTACT_PARTITION,
        "post_anchored": {
            "all_faces_closed_axial_on": nullity(closed=names),
            "all_faces_closed_axial_off": nullity(closed=names, axial=False),
            "all_faces_open_axial_on": nullity(),
            "all_faces_open_axial_off": nullity(axial=False),
            "principal_faces_open_axial_on": nullity(closed=names[:2] + names[4:]),
            "main_faces_closed_return_faces_open_axial_on": nullity(closed=names[:4]),
            "main_faces_closed_return_faces_open_axial_off": nullity(
                closed=names[:4], axial=False
            ),
            "one_face_open_axial_on": {
                name: nullity(closed=tuple(other for other in names if other != name))
                for name in names
            },
            "one_face_open_axial_off": {
                name: nullity(
                    closed=tuple(other for other in names if other != name), axial=False
                )
                for name in names
            },
            "serial_only_closed_axial_on": nullity(closed=names, return_path=False),
        },
        "free_assembly_all_faces_closed_axial_on": nullity(
            closed=names, anchor_post=False
        ),
        "contact_and_axial_rows_are_conditional": True,
        "strength_or_frame_verdict": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
