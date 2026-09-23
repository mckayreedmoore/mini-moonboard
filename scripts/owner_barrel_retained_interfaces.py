"""Correct inherited retained-bolt face points for the integrated kerf pose.

This only changes analysis coordinates. All twelve physical bolt axes remain
those of the maintained viewer and selected kerf-right source.
"""

import itertools
from math import isclose, isfinite

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard.floor_flush_width import KERF_RIGHT_MM


def retained_interface_point(assembly, baseline, connection):
    """Use the current shared rim/leg face for the two right upper bolts."""
    point = baseline.bolt_interface_point(connection)
    if not connection.name.startswith("lumber_leg_bolt_right_"):
        return point
    if (
        assembly.get("post_placement") != "integrated"
        or set(connection.members) != {"base_side_right", "lumber_leg_right"}
    ):
        raise ValueError("Require current integrated right rim/leg bolt pair")
    rim = assembly["wood"]["base_side_right"].BoundingBox()
    leg = assembly["wood"]["lumber_leg_right"].BoundingBox()
    if (
        not isclose(rim.xmax, leg.xmin, abs_tol=1e-6)
        or not isclose(point.x - rim.xmax, KERF_RIGHT_MM, abs_tol=1e-6)
    ):
        raise ValueError("Right kerf rim/leg interface no longer matches its source")
    return cq.Vector(rim.xmax, point.y, point.z)


class RetainedFacePose:
    """Expose baseline bolts and wood with current retained interface points."""

    def __init__(self, assembly, baseline):
        self.assembly = assembly
        self.baseline = baseline

    def __getattr__(self, name):
        return getattr(self.baseline, name)

    def bolt_interface_point(self, connection):
        return retained_interface_point(self.assembly, self.baseline, connection)


def retained_contact_rows(assembly, baseline, *, stiffness_per_area):
    """Partition six retained-bolt net faces into exact tributary cells.

    Each four-sided gross overlap is fanned into four triangles.  Each fan
    triangle is then split into three equal-area vertex regions.  Intersecting
    those 12 regions with the face after its bolt bores are removed gives an
    exact area and first-moment centroid for every emitted spring.
    """
    if not isfinite(stiffness_per_area) or stiffness_per_area <= 0:
        raise ValueError("Contact stiffness per area must be positive and finite")
    raw = {part.name: part for part in baseline.uncut_wood_parts()}
    groups = {}
    for bolt in baseline.connections():
        if bolt.kind == "bolt":
            groups.setdefault(bolt.members, []).append(bolt)
    if len(groups) != 6 or sum(map(len, groups.values())) != 12:
        raise ValueError("Retained frame-bolt face inventory changed")

    rows = []
    for (first, second), bolts in groups.items():
        equations = []
        for name in (first, second):
            points = np.unique(
                [
                    [vertex.Center().y, vertex.Center().z]
                    for vertex in raw[name].shape.Vertices()
                ],
                axis=0,
            )
            equations.extend(ConvexHull(points).equations)
        coefficients = np.asarray(equations)[:, :2]
        constants = np.asarray(equations)[:, 2]
        vertices = []
        for left, right in itertools.combinations(range(len(coefficients)), 2):
            pair = coefficients[[left, right]]
            if abs(np.linalg.det(pair)) < 1.0e-10:
                continue
            point = np.linalg.solve(pair, -constants[[left, right]])
            if (
                np.max(coefficients @ point + constants) <= 1.0e-6
                and not any(np.linalg.norm(point - known) < 1.0e-5 for known in vertices)
            ):
                vertices.append(point)
        if len(vertices) != 4:
            raise ValueError("Retained frame-bolt face is not four-sided")
        polygon = np.asarray(vertices)[ConvexHull(vertices).vertices]
        gross_area = ConvexHull(polygon).volume
        centre = polygon.mean(axis=0)
        interface = retained_interface_point(assembly, baseline, bolts[0]).x

        def xyz(point, interface_x=interface):
            return cq.Vector(interface_x, *point)

        outer = cq.Wire.makePolygon([xyz(point) for point in polygon], close=True)
        hole_wires = []
        bore_area = 0.0
        for bolt in bolts:
            radius = baseline.bolt_dimensions(bolt)["hole_diameter_mm"] / 2
            bore_centre = np.asarray([bolt.start.y, bolt.start.z])
            if np.max(
                coefficients @ bore_centre + constants
            ) > -radius + 1.0e-6:
                raise ValueError("Retained frame-bolt bore left its contact face")
            hole_wires.append(
                cq.Wire.makeCircle(
                    radius,
                    xyz(bore_centre),
                    cq.Vector(1, 0, 0),
                )
            )
            bore_area += np.pi * radius**2
        net_face = cq.Face.makeFromWires(outer, hole_wires)
        if not isclose(net_face.Area(), gross_area - bore_area, abs_tol=1.0e-5):
            raise ValueError("Retained frame-bolt net face lost exact bore area")

        first_centre_x = raw[first].shape.Center().x
        normal = (1.0 if first_centre_x > interface else -1.0, 0.0, 0.0)
        face_rows = []
        for index in range(len(polygon)):
            triangle = np.asarray(
                [centre, polygon[index], polygon[(index + 1) % len(polygon)]]
            )
            triangle_centre = triangle.mean(axis=0)
            midpoints = [
                (triangle[0] + triangle[1]) / 2,
                (triangle[1] + triangle[2]) / 2,
                (triangle[2] + triangle[0]) / 2,
            ]
            # Median partition: one equal-area region around each triangle
            # vertex.  These 12 regions exactly tile the gross face.
            regions = (
                (triangle[0], midpoints[0], triangle_centre, midpoints[2]),
                (triangle[1], midpoints[1], triangle_centre, midpoints[0]),
                (triangle[2], midpoints[2], triangle_centre, midpoints[1]),
            )
            for sample, region in enumerate(regions):
                gross_cell = cq.Face.makeFromWires(
                    cq.Wire.makePolygon([xyz(point) for point in region], close=True)
                )
                components = [
                    face
                    for face in net_face.intersect(gross_cell).Faces()
                    if face.Area() > 1.0e-9
                ]
                if len(components) != 1:
                    raise ValueError("Retained contact cell became disconnected or empty")
                cut_cell = components[0]
                point = cut_cell.Center()
                if net_face.distance(cq.Vertex.makeVertex(*point.toTuple())) > 1.0e-6:
                    raise ValueError("Retained contact-cell centroid lies in a bore")
                area = cut_cell.Area()
                face_rows.append(
                    {
                        "name": f"flush_face_{first}_{second}_{index}_{sample}",
                        "first": first,
                        "second": second,
                        "point_xyz_mm": list(point.toTuple()),
                        "normal_xyz": normal,
                        "gross_tributary_area_mm2": gross_cell.Area(),
                        "tributary_area_mm2": area,
                        "stiffness_n_per_mm": stiffness_per_area * area,
                        "exact_cut_cell_area_and_centroid": True,
                    }
                )
        expected_moment = net_face.Area() * np.asarray(net_face.Center().toTuple())
        actual_moment = sum(
            (
                row["tributary_area_mm2"] * np.asarray(row["point_xyz_mm"])
                for row in face_rows
            ),
            np.zeros(3),
        )
        if (
            len(face_rows) != 12
            or not isclose(
                sum(row["tributary_area_mm2"] for row in face_rows),
                net_face.Area(),
                abs_tol=1.0e-5,
            )
            or not np.allclose(actual_moment, expected_moment, atol=1.0e-4)
        ):
            raise ValueError("Retained contact cells do not preserve face moments")
        rows.extend(face_rows)
    if len(rows) != 72:
        raise ValueError("Retained frame-bolt face-contact inventory changed")
    return tuple(rows)
