"""Local point-constraint ranks for the maintained 24-duty barrel assembly.

This is a rigid-body geometry screen. It neither solves a signed load case nor
establishes a force path, joint stiffness, capacity, or whole-frame stability.
"""

import json

import numpy as np

from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_face_contacts import build_report as face_report

SCHEMA = "owner_barrel_integrated_kinematics/v1"
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
        "limitations": (
            "Each station is isolated as two rigid bodies. Full bolt rows assume "
            "three ideal point-displacement restraints per bolt; lateral-only "
            "rows omit uncertain axial engagement. Closed face rows assume all "
            "modeled compression cells active without friction. No unilateral "
            "equilibrium, gap, stiffness, resistance, member deformation, floor "
            "support, signed case or connected whole-frame constraint is solved."
        ),
        "native_solve": False,
        "structural_released": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
