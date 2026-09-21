"""Small-displacement point-constraint rank of the current PB-02 center loop."""

import json

import numpy as np

from scripts.simple_center_pb02_integrated_trial import working_geometry

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


def _midpoint(first, second):
    return tuple((a + b) / 2 for a, b in zip(first, second))


def current_edges():
    """Build rank-model bolt centers from the same active PB02 geometry as CAD."""
    _, _, ends = working_geometry()

    def center(first, second):
        return _midpoint(ends[first][0], ends[second][0])

    return {
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
            (0, 1, 0),
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


EDGES = current_edges()
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


def matrix(*, closed=(), axial=True, return_path=True, anchor_post=True):
    """Closed faces supply four normal rows; open faces supply none."""
    rows = []
    for name, (first, second, normal, bolts) in EDGES.items():
        if not return_path and name in (
            "principal_upright_block",
            "upright_rear_block",
            "rear_block_post",
        ):
            continue
        n = np.asarray(normal, dtype=float)
        tangents = [axis for axis in np.eye(3) if abs(axis @ n) < 0.5]
        for point in bolts:
            rows.extend(
                _point_row(first, second, tangent, point) for tangent in tangents
            )
            if axial:
                rows.append(_point_row(first, second, n, point))
        if name in closed:
            center = np.mean(bolts, axis=0)
            for a in (-20.0, 20.0):
                for b in (-20.0, 20.0):
                    point = center + a * tangents[0] + b * tangents[1]
                    rows.append(_point_row(first, second, n, point))
    # Fixing the post removes six arbitrary whole-assembly rigid motions only.
    anchored = np.asarray(rows)[:, 6:] if anchor_post else np.asarray(rows)
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
        "nodes": NODES,
        "edges": {
            name: {"members": edge[:2], "normal": edge[2], "bolt_centers_mm": edge[3]}
            for name, edge in EDGES.items()
        },
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
