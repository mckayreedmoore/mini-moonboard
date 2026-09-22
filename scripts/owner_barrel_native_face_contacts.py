"""Source-built contact faces for the integrated barrel frame.

This is a native-model input, not a contact law, solve, or release.
"""

import json
from math import isclose

import cadquery as cq

from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_native_face_contacts/v4"
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


def _contact_cells(patch, cut_patch, normal, station, *, refine_y=False):
    """Resolve the center rear strip exactly; retain gross cells elsewhere."""
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
    if refine_y and abs(normal.z) < 1 - 1e-6:
        raise ValueError(f"{station}: refined center face is no longer horizontal")
    u_count = 8 if refine_y and abs(tangent_u.y) > abs(tangent_v.y) else 2
    v_count = 8 if refine_y and u_count == 2 else 2
    plane = patch.Center().dot(normal)

    def point_at(u, v):
        return normal * plane + tangent_u * u + tangent_v * v

    cells = []
    total_area = 0.0
    for row in range(1, u_count + 1):
        u_min = u0 + (row - 1) * (u1 - u0) / u_count
        u_max = u0 + row * (u1 - u0) / u_count
        for column in range(1, v_count + 1):
            v_min = v0 + (column - 1) * (v1 - v0) / v_count
            v_max = v0 + column * (v1 - v0) / v_count
            gross_point = point_at((u_min + u_max) / 2, (v_min + v_max) / 2)
            corners = [
                point_at(u_min, v_min),
                point_at(u_max, v_min),
                point_at(u_max, v_max),
                point_at(u_min, v_max),
            ]
            if patch.distance(cq.Vertex.makeVertex(*gross_point.toTuple())) > TOL_MM:
                raise ValueError(f"{station}: gross cell left timber face")
            cell_area = area / (u_count * v_count)
            cell_point = gross_point
            if refine_y:
                # The two horizontal principal/header faces preserve cutouts
                # in exact coplanar intersections. Other faces remain gross
                # until one cut-cell method closes on every orientation.
                cell_face = cq.Face.makeFromWires(
                    cq.Wire.makePolygon(corners, close=True)
                )
                cut_cell = cut_patch.intersect(cell_face)
                cell_area = cut_cell.Area()
                cell_point = cut_cell.Center()
                if (
                    cell_area <= 0
                    or cell_area > area / (u_count * v_count) + TOL_AREA_MM2
                    or cut_patch.distance(cq.Vertex.makeVertex(*cell_point.toTuple()))
                    > TOL_MM
                ):
                    raise ValueError(f"{station}: invalid cut center cell")
            total_area += cell_area
            cells.append(
                {
                    "name": f"{station}_contact_{row}_{column}",
                    "point_xyz_mm": _xyz(cell_point),
                    "gross_cell_center_xyz_mm": _xyz(gross_point),
                    "gross_tributary_area_mm2": round(area / (u_count * v_count), 6),
                    "tributary_area_mm2": round(cell_area, 6),
                }
            )
    target_area = cut_patch.Area() if refine_y else patch.Area()
    if not isclose(total_area, target_area, abs_tol=TOL_AREA_MM2):
        raise ValueError(f"{station}: contact-cell areas do not close")
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
    # Reuse the same complete, unreleased cutter replay as the public viewer.
    from scripts.owner_barrel_visual_wood import build_visual_wood

    trial = build_visual_wood(
        assembly=assembly,
        candidate_service=True,
        candidate_center_cuts=True,
        candidate_all_cuts=True,
    )
    if (
        trial["report"]["candidate_barrel_pairs_with_cut_wood"] != 46
        or trial["report"]["barrel_drilling_paths_without_cut_wood"]
        or trial["report"]["barrel_path_host_anomalies"]
        or trial["report"]["release"]
    ):
        raise ValueError("Current viewer trial-cut inventory changed")
    stations = {}
    for station, duty in duties.items():
        first_name, second_name = duty["timber"]
        first, second = assembly["wood"][first_name], assembly["wood"][second_name]
        face, patch = _touching_face(first, second, station)
        cut_patch = patch.intersect(trial["wood"][first_name]).intersect(
            trial["wood"][second_name]
        )
        if (
            cut_patch.Area() <= 0
            or cut_patch.Area() > patch.Area() + TOL_AREA_MM2
            or len(cut_patch.Faces()) != 1
        ):
            raise ValueError(f"{station}: trial-cut contact face is invalid")
        opposite, reverse_patch = _touching_face(second, first, station)
        normal = face.normalAt().normalized()
        if (
            not isclose(patch.Area(), reverse_patch.Area(), abs_tol=TOL_AREA_MM2)
            or (patch.Center() - reverse_patch.Center()).Length > TOL_MM
            or normal.dot(opposite.normalAt().normalized()) > -1 + 1e-6
        ):
            raise ValueError(f"{station}: timber faces do not oppose each other")
        crossings = _bolt_crossings(assembly, station, patch, normal)
        center_margin = None
        if duty["family"] == "base_center":
            if len(crossings) != 1:
                raise ValueError(f"{station}: center principal bolt count changed")
            bolt_y = crossings[0]["point_xyz_mm"][1]
            bounds = patch.BoundingBox()
            rear, front = bolt_y - bounds.ymin, bounds.ymax - bolt_y
            if rear <= 0 or front <= 0:
                raise ValueError(f"{station}: center bolt left its gross face")
            z = patch.Center().z
            rear_face = cq.Face.makeFromWires(
                cq.Wire.makePolygon(
                    [
                        cq.Vector(bounds.xmin, bounds.ymin, z),
                        cq.Vector(bounds.xmax, bounds.ymin, z),
                        cq.Vector(bounds.xmax, bolt_y, z),
                        cq.Vector(bounds.xmin, bolt_y, z),
                    ],
                    close=True,
                )
            )
            cut_rear = cut_patch.intersect(rear_face).Area()
            if not 0 < cut_rear < cut_patch.Area():
                raise ValueError(f"{station}: rear cut-contact strip disappeared")
            center_margin = {
                "rear": round(rear, 6),
                "front": round(front, 6),
                "trial_cut_rear_strip_area_mm2": round(cut_rear, 6),
                "trial_cut_front_area_mm2": round(cut_patch.Area() - cut_rear, 6),
            }
        cells = _contact_cells(
            patch,
            cut_patch,
            normal,
            station,
            refine_y=duty["family"] == "base_center",
        )
        if center_margin is not None:
            cell_y = [cell["point_xyz_mm"][1] for cell in cells]
            if not min(cell_y) < crossings[0]["point_xyz_mm"][1] < max(cell_y):
                raise ValueError(f"{station}: rear compression strip is unresolved")
        stations[station] = {
            "family": duty["family"],
            "first_part": first_name,
            "second_part": second_name,
            "gross_contact_area_mm2": round(patch.Area(), 6),
            "trial_cut_contact_area_mm2": round(cut_patch.Area(), 6),
            "trial_cut_face_continuous": True,
            "trial_cut_face_capacity_qualified": False,
            "gross_contact_centroid_xyz_mm": _xyz(patch.Center()),
            "normal_outward_from_first_xyz": _xyz(normal),
            "contact_cells": cells,
            "contact_cell_area_basis": (
                "exact_trial_cut_face"
                if duty["family"] == "base_center"
                else "gross_uncut_face"
            ),
            "bolt_face_crossings": crossings,
            "gross_face_y_edge_margins_from_bolt_mm": center_margin,
        }
    return {
        "schema": SCHEMA,
        "source": "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()",
        "post_placement": "integrated",
        "station_count": len(stations),
        "contact_cell_count": sum(
            len(row["contact_cells"]) for row in stations.values()
        ),
        "trial_cut_face_count": len(stations),
        "trial_cut_cell_face_count": sum(
            row["contact_cell_area_basis"] == "exact_trial_cut_face"
            for row in stations.values()
        ),
        "bolt_interface_count": sum(
            len(row["bolt_face_crossings"]) for row in stations.values()
        ),
        "fixed_panel_kicker_screw_count": len(assembly["panel_connections"]),
        "retained_frame_bolt_count": len(assembly["frame_connections"]),
        "stations": stations,
        "limits": (
            "Only the two horizontal principal/header faces have exact "
            "trial-cut cell areas; other cells retain gross weights because "
            "the general cutout-clipping method did not close on an inclined "
            "face. This is "
            "not a certified contact law. Current visual cutters include "
            "unresolved bore/service "
            "collisions; neither gross nor cut face establishes delivered "
            "contact, gaps, preload, tolerances, moisture, partial opening, "
            "slip, stiffness, or resistance. The two single-"
            "bolt principal/header faces use 2x8 cells to resolve their narrow "
            "rear strips; all other gross faces use 2x2 cells."
        ),
        "contact_law_qualified": False,
        "native_solve": False,
        "structural_released": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
