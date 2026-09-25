"""Place the bottom support just above the T-nut row below its raised position.

Geometry for owner review only. Reuse the incremental machining path while
preserving both previous review geometries and all selected-baseline inputs.
"""

from __future__ import annotations

import math
from typing import Any

from scripts import wood_joint_wj24_bottom_support_up_one_row as support

REVISION_ID = "lower-rear-blocks-below-plus-bottom-support-above-tnuts-v1"
FLANGE_CLEARANCE_MM = 5.0


def projected_t_bounds(shape: Any, t_axis: Any) -> tuple[float, float]:
    """Include circular flange extrema, rather than only topological vertices."""
    if abs(t_axis.x) > 1e-9:
        raise ValueError("expected the climbing surface T axis in the YZ plane")
    angle = math.degrees(math.atan2(t_axis.z, t_axis.y))
    bounds = shape.rotate((0, 0, 0), (1, 0, 0), -angle).BoundingBox()
    return bounds.ymin, bounds.ymax


def build_bottom_support_above_tnuts(
    lower_blocks_geometry: Any,
    lower_blocks_report: dict[str, Any],
    raised_geometry: Any,
) -> tuple[Any, dict[str, Any]]:
    if raised_geometry.layout_id != support.REVISION_ID:
        raise ValueError("reference must be the previous one-row raised support")
    t_axis = support._translation_from_inventory(lower_blocks_geometry.source_inventory, 1.0)
    current_lower = {
        name: projected_t_bounds(raised_geometry.raw_hosts[name], t_axis)[0]
        for name in support.MOVED_RAIL_IDS
    }
    if max(current_lower.values()) - min(current_lower.values()) > 1e-6:
        raise ValueError("the two bottom support rails must share one T station")
    below = {
        name: projected_t_bounds(shape, t_axis)[1]
        for name, shape in raised_geometry.protected["tnuts"].items()
        if "_main_" in name
        and projected_t_bounds(shape, t_axis)[1] < min(current_lower.values())
    }
    if not below:
        raise ValueError("no main-panel T-nut row lies below the raised support")
    flange_top = max(below.values())
    row_ids = sorted(name for name, top in below.items() if abs(top - flange_top) < 1e-6)
    target_lower = flange_top + FLANGE_CLEARANCE_MM
    original_lower = {
        name: projected_t_bounds(lower_blocks_geometry.raw_hosts[name], t_axis)[0]
        for name in support.MOVED_RAIL_IDS
    }
    if max(original_lower.values()) - min(original_lower.values()) > 1e-6:
        raise ValueError("original support rails must share one T station")
    offset = target_lower - min(original_lower.values())
    if target_lower >= min(current_lower.values()):
        raise ValueError("this owner revision must lower the raised support")
    geometry, report = support.build_wj24_bottom_support_up_one_row(
        lower_blocks_geometry,
        lower_blocks_report,
        translation_wall_t_mm=offset,
        revision_id=REVISION_ID,
    )
    for name in support.MOVED_RAIL_IDS:
        actual = projected_t_bounds(geometry.raw_hosts[name], t_axis)[0]
        if abs(actual - target_lower) > 1e-6:
            raise ValueError(f"{name}: support placement differs from the requested flange gap")
    report.update({
        "schema": "wood_joint_wj24_bottom_support_above_tnuts/v1",
        "summary": "Bottom support just above the first T-nut row; middle blocks remain below their rails",
        "supersedes_revision_id": raised_geometry.layout_id,
        "position_reference": {
            "tnut_ids": row_ids,
            "flange_top_global_T_mm": flange_top,
            "rail_lower_edge_global_T_mm": target_lower,
            "flange_clearance_mm": FLANGE_CLEARANCE_MM,
            "movement_from_previous_viewer_along_T_mm": target_lower - min(current_lower.values()),
        },
    })
    return geometry, report
