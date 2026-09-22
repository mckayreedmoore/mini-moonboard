"""Export the complete owner-review corner-block layout as diagnostic CAD.

Every replacement is drawn, including known revise findings. This scene is
never a cut, drill, hardware, or structural release.
"""

import json
from functools import lru_cache
from pathlib import Path

from scripts.owner_corner_layout_assembly import build_assembly
from scripts.simple_owner_duty_ledger import legacy_visual_names, selected_duties

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"
OUTPUT = ROOT / "site/owner-corner-layout-scene.json"
MOVED_POSTS = ("base_post_center_left", "base_post_center_right")
BACKERS = ("inner_kicker_backer_left", "inner_kicker_backer_right")


def _mesh(shape):
    vertices, triangles = shape.tessellate(0.5)
    return {
        "vertices_mm": [list(vertex.toTuple()) for vertex in vertices],
        "triangles": [list(triangle) for triangle in triangles],
    }


def _solid(name, role, shape, station=None):
    bounds = shape.BoundingBox()
    return {
        "name": name,
        "role": role,
        "source_station": station,
        "bounds_xyz_mm": [
            bounds.xmin,
            bounds.xmax,
            bounds.ymin,
            bounds.ymax,
            bounds.zmin,
            bounds.zmax,
        ],
        "mesh": _mesh(shape),
    }


def _axis(name, bolt):
    direction = bolt.direction.normalized()
    return {
        "name": name,
        "start_mm": list(bolt.start.toTuple()),
        "axis": list(direction.toTuple()),
        "length_mm": bolt.length,
        "diameter_mm": bolt.diameter,
        "diagnostic_only": True,
    }


@lru_cache(maxsize=1)
def build_scene():
    """Bind a full visual inventory to one proposed kerf-right assembly."""
    assembly = build_assembly()
    duties = selected_duties()
    baseline = json.loads(BASELINE.read_text())
    baseline_parts = baseline["parts"]
    baseline_names = {part["name"] for part in baseline_parts}
    if (
        set(assembly["blocks"]) != set(duties)
        or set(assembly["removed_legacy_stations"]) != set(duties)
        or len(assembly["removed_legacy_sds"]) != 144
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or not set(MOVED_POSTS).issubset(baseline_names)
        or not (set(MOVED_POSTS) | set(BACKERS)).issubset(assembly["wood"])
    ):
        raise ValueError("Owner corner assembly is not a complete 24-duty layout")
    hidden = sorted(set(legacy_visual_names(duties, baseline_parts)) | set(MOVED_POSTS))
    solids = [
        _solid(f"owner_{station}", "corner_block", shape, station)
        for station, shape in assembly["blocks"].items()
    ]
    solids.extend(
        _solid(name, "moved_center_post", assembly["wood"][name])
        for name in MOVED_POSTS
    )
    solids.extend(
        _solid(name, "kicker_screw_backer", assembly["wood"][name]) for name in BACKERS
    )
    axes = [_axis(name, bolt) for name, bolt in assembly["bolts"].items()]
    if len(solids) != 28 or len(axes) != 92 or len(hidden) != 170:
        raise ValueError("Owner corner scene visual inventory changed")
    return {
        "schema": "owner_corner_layout_scene/v1",
        "status": "complete_layout_concept_not_qualified",
        "baseline": "compact-floor-flush-kerf-right",
        "hidden_baseline_visual_names": hidden,
        "solids": solids,
        "diagnostic_bolt_axes": axes,
        "assembly_diagnostics": assembly["diagnostics"],
        "inventory": {
            "replaced_angle_duties": len(duties),
            "removed_structural_sds": len(assembly["removed_legacy_sds"]),
            "corner_blocks": len(assembly["blocks"]),
            "moved_center_posts": len(MOVED_POSTS),
            "kicker_screw_backers": len(BACKERS),
            "new_diagnostic_bolt_axes": len(axes),
            "fixed_panel_kicker_screw_axes": len(assembly["panel_connections"]),
            "retained_frame_bolt_axes": len(assembly["frame_connections"]),
        },
        "limits": (
            "Full proposed inventory is visible even where collision screens say REVISE. "
            "Diagnostic axes are not selected bolts or drilling dimensions. "
            "Delivered hold-bolt projection, wiring bends, fastener heads, tool "
            "sweeps, backer attachment, resistance and final cases remain open."
        ),
        "layout_clearance_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), indent=2) + "\n")
