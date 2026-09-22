"""Local point-constraint ranks for the maintained 24-duty barrel assembly.

This is a rigid-body geometry screen. It neither solves a signed load case nor
establishes a force path, joint stiffness, capacity, or whole-frame stability.
"""

import json

import numpy as np

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_face_contacts import build_report as face_report
from scripts.owner_barrel_retained_interfaces import (
    retained_contact_rows,
    retained_interface_point,
)

SCHEMA = "owner_barrel_integrated_kinematics/v2"
ROTATION_SCALE_MM = 100.0
RANK_TOL = 1e-8


def _point_row(point, direction, origin, *, scale_mm=ROTATION_SCALE_MM):
    """Relative point displacement projected along one unit direction."""
    if not np.isfinite(scale_mm) or scale_mm <= 0:
        raise ValueError("Rotation scale must be positive and finite")
    direction = np.asarray(direction, dtype=float)
    lever = (np.asarray(point, dtype=float) - origin) / scale_mm
    return np.r_[direction, np.cross(lever, direction)]


def _lateral_directions(axis):
    """Choose two stable orthonormal directions transverse to a bolt axis."""
    axis = np.asarray(axis, dtype=float)
    length = np.linalg.norm(axis)
    if not np.isclose(length, 1.0, atol=1e-6):
        raise ValueError("Current bolt direction is not unit length")
    seed = np.eye(3)[np.argmin(np.abs(axis))]
    first = np.cross(axis, seed)
    first /= np.linalg.norm(first)
    return first, np.cross(axis, first)


def _rank(rows, *, tolerance=RANK_TOL):
    matrix = np.asarray(rows, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != 6 or not np.isfinite(matrix).all():
        raise ValueError("Require six relative rigid-body columns")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Require positive finite rank tolerance")
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.sum(singular > tolerance))


def _closed_twist_alignment(rows, normal, rank):
    if rank != 5:
        return None
    _, _, right_vectors = np.linalg.svd(np.asarray(rows, dtype=float))
    rotation = right_vectors[-1, 3:]
    length = np.linalg.norm(rotation)
    if length < RANK_TOL:
        raise ValueError("Rank-five free mode has no rotation")
    return round(abs(rotation @ normal) / length, 9)


def _connected_frame(assembly, faces):
    """Rank the bolted 20-timber graph without panel or floor brace credit."""
    members = sorted(
        name
        for name in assembly["wood"]
        if not name.startswith(("main_", "kicker_"))
    )
    if len(members) != 20 or set(members) != set(assembly["wood"]) - {
        "main_lower_left", "main_lower_right", "main_upper_left",
        "main_upper_right", "kicker_left", "kicker_right",
    }:
        raise ValueError("Current integrated framing timber inventory changed")
    index = {name: number for number, name in enumerate(members)}
    centers = {
        name: np.asarray(assembly["wood"][name].Center().toTuple())
        for name in members
    }
    gauge = "base_header"
    if gauge not in index:
        raise ValueError("Connected frame lost its coordinate reference")
    graph = {name: set() for name in members}
    width = 6 * len(members)

    def point_row(first, second, point, direction):
        if first not in index or second not in index or first == second:
            raise ValueError("Frame link has unknown or identical timber members")
        row = np.zeros(width)
        for name, sign in ((first, -1), (second, 1)):
            local = _point_row(point, direction, centers[name])
            start = 6 * index[name]
            row[start : start + 6] += sign * local
        return np.delete(row, slice(6 * index[gauge], 6 * index[gauge] + 6))

    barrel_full = []
    barrel_lateral = []
    for face in faces["stations"].values():
        first, second = face["first_part"], face["second_part"]
        graph[first].add(second)
        graph[second].add(first)
        for crossing in face["bolt_face_crossings"]:
            lateral = _lateral_directions(crossing["direction_xyz"])
            point = crossing["point_xyz_mm"]
            barrel_lateral.extend(
                point_row(first, second, point, direction) for direction in lateral
            )
            barrel_full.extend(
                point_row(first, second, point, direction)
                for direction in (*lateral, crossing["direction_xyz"])
            )
    baseline = variant(KERF_RIGHT)
    retained = []
    for bolt in assembly["frame_connections"]:
        if bolt.kind != "bolt" or len(bolt.members) != 2:
            raise ValueError("Retained frame-bolt identity changed")
        first, second = bolt.members
        graph[first].add(second)
        graph[second].add(first)
        point = retained_interface_point(assembly, baseline, bolt).toTuple()
        lateral = _lateral_directions(bolt.direction.normalized().toTuple())
        retained.extend(
            point_row(first, second, point, direction)
            for direction in (*lateral, bolt.direction.normalized().toTuple())
        )
    if len(barrel_full) != 46 * 3 or len(retained) != 12 * 3:
        raise ValueError("Connected frame bolt inventory changed")
    unseen = set(members)
    components = []
    while unseen:
        reached = {min(unseen)}
        frontier = list(reached)
        while frontier:
            new = graph[frontier.pop()] - reached
            reached.update(new)
            frontier.extend(new)
        unseen -= reached
        components.append(reached)
    face_rows = []
    center_face_rows = []
    for station, face in faces["stations"].items():
        first, second = face["first_part"], face["second_part"]
        normal = face["normal_outward_from_first_xyz"]
        rows = [
            point_row(first, second, cell["point_xyz_mm"], normal)
            for cell in face["contact_cells"]
        ]
        face_rows.extend(rows)
        if station in {"clip_split_base_center_left", "clip_split_base_center_right"}:
            center_face_rows.extend(rows)
    if len(face_rows) != 120 or len(center_face_rows) != 32:
        raise ValueError("Connected frame contact point inventory changed")
    retained_contacts = retained_contact_rows(
        assembly, baseline, stiffness_per_area=1.0
    )
    retained_face_rows = [
        point_row(
            row["first"], row["second"],
            row["point_xyz_mm"], row["normal_xyz"],
        )
        for row in retained_contacts
    ]
    if len(retained_face_rows) != 72:
        raise ValueError("Connected retained-face inventory changed")
    non_center_faces = [
        point_row(face["first_part"], face["second_part"],
                  cell["point_xyz_mm"], face["normal_outward_from_first_xyz"])
        for station, face in faces["stations"].items()
        if station not in {"clip_split_base_center_left", "clip_split_base_center_right"}
        for cell in face["contact_cells"]
    ]
    states = {
        "all_bolts_full_all_faces_open": [*barrel_full, *retained],
        "all_bolts_full_all_faces_closed": [
            *barrel_full, *retained, *face_rows, *retained_face_rows
        ],
        "barrel_axial_off_all_faces_closed": [
            *barrel_lateral, *retained, *face_rows, *retained_face_rows
        ],
        "both_center_faces_open": [
            *barrel_full, *retained, *non_center_faces, *retained_face_rows
        ],
    }
    dof = width - 6

    def rank(rows, tolerance=RANK_TOL):
        matrix = np.asarray(rows)
        if matrix.shape[1] != dof or not np.isfinite(matrix).all():
            raise ValueError("Connected frame point rows changed")
        return int(np.sum(np.linalg.svd(matrix, compute_uv=False) > tolerance))

    ranks = {name: rank(rows) for name, rows in states.items()}
    stable = all(
        rank(rows, 1e-9) == ranks[name] == rank(rows, 1e-7)
        for name, rows in states.items()
    )
    if not stable or any(value > dof for value in ranks.values()):
        raise ValueError("Connected frame rank is unstable or impossible")
    return {
        "timber_count": len(members),
        "barrel_bolt_count": len(barrel_full) // 3,
        "retained_bolt_count": len(retained) // 3,
        "barrel_contact_cell_count": len(face_rows),
        "retained_contact_cell_count": len(retained_face_rows),
        "contact_cell_count": len(face_rows) + len(retained_face_rows),
        "graph_component_count": len(components),
        "relative_dof_count": dof,
        "coordinate_reference_only": gauge,
        "ranks": ranks,
        "free_relative_modes": {name: dof - value for name, value in ranks.items()},
        "rank_stable_at_tolerance_1e_9_to_1e_7": stable,
        "panel_screw_structural_credit": False,
        "floor_support_credit": False,
        "conditional_only": True,
    }


def build_report(assembly=None):
    """Compare locally open/closed faces and engaged/lateral-only bolt rows."""
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    faces = face_report(assembly)
    if (
        assembly["post_placement"] != "integrated"
        or len(assembly["bolts"]) != 46
        or faces["station_count"] != 24
        or faces["bolt_interface_count"] != 46
        or faces["contact_cell_count"] != 120
        or any(assembly["release_flags"].values())
    ):
        raise ValueError("Require the current unreleased integrated barrel assembly")
    stations = {}
    for station, face in faces["stations"].items():
        crossings = face["bolt_face_crossings"]
        cells = face["contact_cells"]
        if len(crossings) not in (1, 2) or any(
            cell["tributary_area_mm2"] <= 0 for cell in cells
        ):
            raise ValueError(f"{station}: current point-constraint source changed")
        origin = np.mean([row["point_xyz_mm"] for row in crossings], axis=0)
        normal = np.asarray(face["normal_outward_from_first_xyz"], dtype=float)
        if not np.isclose(np.linalg.norm(normal), 1.0, atol=1e-6):
            raise ValueError(f"{station}: face normal changed")
        full_bolts = []
        lateral_bolts = []
        for crossing in crossings:
            point = crossing["point_xyz_mm"]
            axis = crossing["direction_xyz"]
            lateral = _lateral_directions(axis)
            full_bolts.extend(
                _point_row(point, direction, origin) for direction in (*lateral, axis)
            )
            lateral_bolts.extend(
                _point_row(point, direction, origin) for direction in lateral
            )
        closed_face = [
            _point_row(cell["point_xyz_mm"], normal, origin) for cell in cells
        ]
        states = {
            "bolts_full_face_open": full_bolts,
            "bolts_full_face_closed": [*full_bolts, *closed_face],
            "bolts_lateral_only_face_open": lateral_bolts,
            "bolts_lateral_only_face_closed": [*lateral_bolts, *closed_face],
        }
        ranks = {name: _rank(rows) for name, rows in states.items()}
        rank_stable = all(
            _rank(rows, tolerance=1e-9) == ranks[name] == _rank(rows, tolerance=1e-7)
            for name, rows in states.items()
        )
        if not rank_stable:
            raise ValueError(f"{station}: local rank is tolerance-sensitive")
        if any(value > 6 for value in ranks.values()):
            raise ValueError(f"{station}: impossible relative-motion rank")
        stations[station] = {
            "family": face["family"],
            "first_part": face["first_part"],
            "second_part": face["second_part"],
            "bolt_count": len(crossings),
            "contact_cell_count": len(cells),
            "contact_cell_area_basis": face["contact_cell_area_basis"],
            "ranks": ranks,
            "rank_stable_at_tolerance_1e_9_to_1e_7": rank_stable,
            "closed_full_singular_values": [
                round(value, 9)
                for value in np.linalg.svd(
                    np.asarray(states["bolts_full_face_closed"]), compute_uv=False
                )
            ],
            "closed_full_free_rotation_axis_alignment_with_face_normal_abs": (
                _closed_twist_alignment(
                    [*full_bolts, *closed_face],
                    normal,
                    ranks["bolts_full_face_closed"],
                )
            ),
            "complete_joint_capacity_or_stiffness_claimed": False,
        }
    return {
        "schema": SCHEMA,
        "source": "current integrated viewer and trial-cut contact faces",
        "station_count": len(stations),
        "bolt_interface_count": sum(row["bolt_count"] for row in stations.values()),
        "contact_cell_count": sum(
            row["contact_cell_count"] for row in stations.values()
        ),
        "rotation_scale_mm": ROTATION_SCALE_MM,
        "rank_tolerance": RANK_TOL,
        "stations": stations,
        "connected_frame": _connected_frame(assembly, faces),
        "limitations": (
            "Each station is isolated as two rigid bodies. Full bolt rows assume "
            "three ideal point-displacement restraints per bolt; lateral-only "
            "rows omit uncertain axial engagement. Closed face rows assume all "
            "modeled compression cells active without friction. No unilateral "
            "equilibrium, gap, stiffness, resistance, member deformation, floor "
            "support or signed case is solved. The connected-frame result is "
            "only an idealized point-constraint rank, not a structural solve."
        ),
        "native_solve": False,
        "structural_released": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
