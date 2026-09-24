"""Pure geometry transforms for the WJ-05 center-post X=±190 trial."""

from __future__ import annotations

import math
from typing import Any

import cadquery as cq

TRIAL_ID = "wj05-center-node-posts-x190-outward-v1"
POST_OFFSET_MM = 10.0
SOURCE_POST_CENTERS_MM = {"left": -180.0, "right": 180.0}
TRIAL_POST_CENTERS_MM = {"left": -190.0, "right": 190.0}

MOVED_MEMBER_IDS = frozenset(
    {
        "base_post_center_left",
        "base_post_center_right",
        "center_post_cleat_left",
        "center_post_cleat_right",
    }
)
FIXED_CLEAT_IDS = frozenset(
    {"center_principal_cleat_left", "center_principal_cleat_right"}
)
MOVED_AXIS_IDS = frozenset(
    {
        *(f"center_post_{side}_{row}" for side in ("left", "right") for row in (1, 2)),
        *(
            f"center_post_header_{side}_{row}"
            for side in ("left", "right")
            for row in (1, 2)
        ),
    }
)
FIXED_AXIS_IDS = frozenset(
    {
        *(f"center_principal_{side}_{row}" for side in ("left", "right") for row in (1, 2)),
        *(
            f"center_principal_header_{side}_{row}"
            for side in ("left", "right")
            for row in (1, 2)
        ),
    }
)


def _side_offset(side: str, offset_mm: float) -> float:
    if side not in {"left", "right"}:
        raise ValueError(f"unknown center side: {side!r}")
    if not math.isfinite(offset_mm) or offset_mm <= 0:
        raise ValueError("outward offset must be finite and positive")
    return offset_mm if side == "right" else -offset_mm


def shift_lower_axes_outward(
    axes: list[dict[str, Any]], *, offset_mm: float = POST_OFFSET_MM
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Copy the 16 center axes and move only the eight lower axes outward."""
    by_id = {axis.get("axis_id"): axis for axis in axes}
    if len(by_id) != len(axes):
        raise ValueError("center fastener axes must have unique IDs")
    expected = MOVED_AXIS_IDS | FIXED_AXIS_IDS
    if set(by_id) != expected:
        raise ValueError("center fastener axis identities changed")

    moved: list[dict[str, Any]] = []
    movement_records: list[dict[str, Any]] = []
    for axis in axes:
        axis_id = axis["axis_id"]
        updated = dict(axis)
        point = axis.get("origin_global_xyz_mm")
        if not isinstance(point, (list, tuple)) or len(point) != 3:
            raise ValueError(f"{axis_id} needs a three-component origin")
        if not all(math.isfinite(float(value)) for value in point):
            raise ValueError(f"{axis_id} origin must be finite")
        if axis_id in MOVED_AXIS_IDS:
            side = axis.get("side")
            delta_x = _side_offset(side, offset_mm)
            shifted_point = list(point)
            shifted_point[0] = float(shifted_point[0]) + delta_x
            updated["origin_global_xyz_mm"] = shifted_point
            movement_records.append(
                {
                    "axis_id": axis_id,
                    "side": side,
                    "source_x_mm": float(point[0]),
                    "trial_x_mm": shifted_point[0],
                    "delta_x_mm": delta_x,
                }
            )
        moved.append(updated)
    return moved, movement_records


def shift_lower_members_outward(
    parts: dict[str, cq.Shape], *, offset_mm: float = POST_OFFSET_MM
) -> tuple[dict[str, cq.Shape], list[dict[str, Any]]]:
    """Translate only two center posts and their lower cleats in global X."""
    required = MOVED_MEMBER_IDS | FIXED_CLEAT_IDS
    if not required <= set(parts):
        missing = sorted(required - set(parts))
        raise ValueError(f"center candidate members missing: {missing}")

    result = dict(parts)
    records: list[dict[str, Any]] = []
    for name in sorted(MOVED_MEMBER_IDS):
        shape = parts[name]
        if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
            raise ValueError(f"{name} must be valid solid geometry")
        side = "left" if name.endswith("_left") else "right"
        delta_x = _side_offset(side, offset_mm)
        result[name] = shape.translate(cq.Vector(delta_x, 0, 0))
        records.append(
            {
                "member_id": name,
                "side": side,
                "delta_x_mm": delta_x,
                "source_bounds_xyz_mm": _bounds(shape),
                "trial_bounds_xyz_mm": _bounds(result[name]),
            }
        )
    for name in FIXED_CLEAT_IDS:
        shape = parts[name]
        if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
            raise ValueError(f"{name} must be valid solid geometry")
    return result, records


def _bounds(shape: cq.Shape) -> list[float]:
    box = shape.BoundingBox()
    return [
        round(value, 6)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def geometry_implications() -> dict[str, Any]:
    """Record the known spacing/contact shifts without assigning capacity."""
    return {
        "post_center_x_mm": {
            "source": [SOURCE_POST_CENTERS_MM["left"], SOURCE_POST_CENTERS_MM["right"]],
            "trial": [TRIAL_POST_CENTERS_MM["left"], TRIAL_POST_CENTERS_MM["right"]],
        },
        "center_post_support_center_spacing_mm": {
            "source": 360.0,
            "trial": 380.0,
            "change": 20.0,
        },
        "lower_header_bolt_group_center_spacing_mm": {
            "source": 488.0,
            "trial": 508.0,
            "change": 20.0,
        },
        "upper_cleat_post_projected_overlap_mm": {
            "source": 17.0,
            "trial": 7.0,
            "change": -10.0,
        },
        "mechanics_note": (
            "Spacing and projected overlap changes require fresh mechanics and "
            "complete-joint review; no capacity transfers from the source trial."
        ),
    }
