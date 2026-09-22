"""Gross, source-built contact faces for the integrated barrel frame.

This is a native-model input, not a contact law, cut-wood face, solve, or release.
"""

import json
from math import isclose

import cadquery as cq

from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_native_face_contacts/v1"
TOL_MM = 1e-3
TOL_AREA_MM2 = 1e-2


def _xyz(vector):
    return [round(value, 6) for value in vector.toTuple()]


def _touching_face(first, second, station):
    """Find the one actual planar, gross timber interface in the uncut pose."""
    hits = []
    for face in first.Faces():
        if face.geomType() != "PLANE":
            continue
        patch = face.intersect(second)
        if patch.Area() > TOL_AREA_MM2:
            hits.append((face, patch))
    if len(hits) != 1 or len(hits[0][1].Faces()) != 1:
        raise ValueError(f"{station}: expected one planar gross timber interface")
    return hits[0]


def _contact_cells(patch, normal, station):
    """Four equal-area centroid cells on a verified rectangular gross patch."""
    edges = [edge for edge in patch.Edges() if len(edge.Vertices()) == 2]
    if len(edges) != 4 or len(patch.Vertices()) != 4:
        raise ValueError(f"{station}: contact patch is not four-sided")
    first_vertices = edges[0].Vertices()
    tangent_u = (first_vertices[1].Center() - first_vertices[0].Center()).normalized()
    tangent_v = normal.cross(tangent_u).normalized()
    vertices = [vertex.Center() for vertex in patch.Vertices()]
    u0, u1 = (
        min(point.dot(tangent_u) for point in vertices),
        max(point.dot(tangent_u) for point in vertices),
    )
    v0, v1 = (
        min(point.dot(tangent_v) for point in vertices),
        max(point.dot(tangent_v) for point in vertices),
    )
    area = patch.Area()
    if not isclose((u1 - u0) * (v1 - v0), area, abs_tol=TOL_AREA_MM2):
        raise ValueError(f"{station}: gross contact patch is not rectangular")
    plane = patch.Center().dot(normal)
    cells = []
    for row, u_fraction in enumerate((0.25, 0.75), 1):
        for column, v_fraction in enumerate((0.25, 0.75), 1):
            point = (
                normal * plane
                + tangent_u * (u0 + u_fraction * (u1 - u0))
                + tangent_v * (v0 + v_fraction * (v1 - v0))
            )
            if patch.distance(cq.Vertex.makeVertex(*point.toTuple())) > TOL_MM:
                raise ValueError(f"{station}: contact cell is outside timber face")
            cells.append(
                {
                    "name": f"{station}_contact_{row}_{column}",
                    "point_xyz_mm": _xyz(point),
                    "tributary_area_mm2": round(area / 4, 6),
                }
            )
    return cells


def _bolt_crossings(assembly, station, patch, normal):
    rows = []
    for name, owner in sorted(assembly["bolt_station"].items()):
        if owner != station:
            continue
        bolt = assembly["bolts"][name]
        direction = bolt.direction.normalized()
        denominator = direction.dot(normal)
        if abs(denominator) < TOL_MM:
            raise ValueError(f"{name}: bolt is parallel to timber contact face")
        distance = (patch.Center() - bolt.start).dot(normal) / denominator
        point = bolt.start + direction * distance
        gap = patch.distance(cq.Vertex.makeVertex(*point.toTuple()))
        if not 0 < distance < bolt.length or gap > TOL_MM:
            raise ValueError(f"{name}: bolt does not cross the gross contact face")
        rows.append(
            {
                "name": name,
                "point_xyz_mm": _xyz(point),
                "direction_xyz": _xyz(direction),
                "distance_from_modeled_shaft_start_mm": round(distance, 6),
                "point_on_gross_contact_face": True,
            }
        )
    if len(rows) not in (1, 2):
        raise ValueError(f"{station}: expected one or two integrated barrel bolts")
    return rows


def build_report(assembly=None):
    """Bind gross compression patches and bolt interface points to one scene."""
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    duties = selected_duties()
    if (
        assembly.get("post_placement") != "integrated"
        or len(duties) != 24
        or set(assembly["station_modes"]) != set(duties)
        or len(assembly["bolts"]) != 46
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or any(name.startswith("inner_kicker_backer_") for name in assembly["wood"])
    ):
        raise ValueError("Require the current integrated 46-pair barrel frame")
    stations = {}
    for station, duty in duties.items():
        first_name, second_name = duty["timber"]
        first, second = assembly["wood"][first_name], assembly["wood"][second_name]
        face, patch = _touching_face(first, second, station)
        opposite, reverse_patch = _touching_face(second, first, station)
        normal = face.normalAt().normalized()
        if (
            not isclose(patch.Area(), reverse_patch.Area(), abs_tol=TOL_AREA_MM2)
            or (patch.Center() - reverse_patch.Center()).Length > TOL_MM
            or normal.dot(opposite.normalAt().normalized()) > -1 + 1e-6
        ):
            raise ValueError(f"{station}: timber faces do not oppose each other")
        stations[station] = {
            "family": duty["family"],
            "first_part": first_name,
            "second_part": second_name,
            "gross_contact_area_mm2": round(patch.Area(), 6),
            "gross_contact_centroid_xyz_mm": _xyz(patch.Center()),
            "normal_outward_from_first_xyz": _xyz(normal),
            "contact_cells": _contact_cells(patch, normal, station),
            "bolt_face_crossings": _bolt_crossings(assembly, station, patch, normal),
        }
    return {
        "schema": SCHEMA,
        "source": "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()",
        "post_placement": "integrated",
        "station_count": len(stations),
        "contact_cell_count": sum(
            len(row["contact_cells"]) for row in stations.values()
        ),
        "bolt_interface_count": sum(
            len(row["bolt_face_crossings"]) for row in stations.values()
        ),
        "fixed_panel_kicker_screw_count": len(assembly["panel_connections"]),
        "retained_frame_bolt_count": len(assembly["frame_connections"]),
        "stations": stations,
        "limits": (
            "Gross uncut wood-to-wood faces only. Bolt paths and cells do not "
            "include actual drilled cutout, gaps, preload, tolerances, moisture, "
            "partial opening, slip, stiffness, or resistance."
        ),
        "contact_law_qualified": False,
        "native_solve": False,
        "structural_released": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
