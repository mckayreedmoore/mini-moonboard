"""Group actual finished block solids by rigid-rotation congruence, never mirrors."""

from __future__ import annotations

from itertools import permutations, product
from typing import Any

import cadquery as cq
import numpy as np
from OCP.gp import gp_Trsf


def _properties(shape: cq.Shape) -> tuple:
    volume = shape.Volume()
    center = np.asarray(shape.Center().toTuple())
    inertia, basis = np.linalg.eigh(np.asarray(cq.Shape.matrixOfInertia(shape)))
    return volume, center, inertia, basis


def equivalent_by_rotation(a: cq.Shape, b: cq.Shape) -> dict[str, Any] | None:
    va, ca, ia, ea = _properties(a)
    vb, cb, ib, eb = _properties(b)
    if not np.isclose(va, vb, rtol=1e-8, atol=0.01) or not np.allclose(
        ia, ib, rtol=1e-7, atol=0.01
    ):
        return None
    for perm in permutations(range(3)):
        if not np.allclose(ia, ib[list(perm)], rtol=1e-7, atol=0.01):
            continue
        for signs in product((-1, 1), repeat=3):
            rotation = eb[:, perm] @ np.diag(signs) @ ea.T
            if np.linalg.det(rotation) < 0:
                continue
            translation = cb - rotation @ ca
            matrix = np.eye(4)
            matrix[:3, :3] = rotation
            matrix[:3, 3] = translation
            transform = gp_Trsf()
            transform.SetValues(*matrix[:3, :].ravel().tolist())
            moved = a.moved(cq.Location(transform))
            common = moved.intersect(b).Volume()
            difference = max(0.0, va + vb - 2 * common)
            if difference <= max(0.02, (va + vb) * 1e-8):
                return {
                    "symmetric_difference_mm3": difference,
                    "rigid_transform": matrix.tolist(),
                }
    return None


def count_block_designs(geometry: Any) -> dict[str, Any]:
    groups = []
    for name, shape in sorted(geometry.finished_candidate_parts.items()):
        for group in groups:
            match = equivalent_by_rotation(
                geometry.finished_candidate_parts[group["representative"]], shape
            )
            if match is not None:
                group["members"].append(name)
                group["equivalence_checks"][name] = match
                break
        else:
            groups.append(
                {
                    "representative": name,
                    "members": [name],
                    "equivalence_checks": {},
                    "finished_volume_mm3": shape.Volume(),
                    "bolt_axes": [
                        axis
                        for axis, bore in geometry.candidate_bores.items()
                        if name in bore.receiver_ids
                    ],
                }
            )
    return {
        "schema": "wood_joint_corner_block_design_count/v1",
        "revision_id": geometry.layout_id,
        "placed_blocks": len(geometry.finished_candidate_parts),
        "unique_geometric_designs": len(groups),
        "method": "Finished CAD solids including holes, cuts and reliefs; translation and proper rotation allowed, reflection not allowed. Inertia candidates checked by exact solid intersection.",
        "limits": [
            "Geometry and drilling pattern only. This does not approve grain orientation, stock, manufacture or joint capacity.",
            "Congruence uses a maximum symmetric-difference tolerance of 0.02 mm3 or 1e-8 of summed volume.",
        ],
        "groups": groups,
    }
