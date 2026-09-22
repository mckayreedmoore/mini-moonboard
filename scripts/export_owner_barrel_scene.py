"""Export a complete but unqualified owner-review barrel-nut frame scene."""

import json
from functools import lru_cache
from pathlib import Path

from scripts.owner_barrel_layout_assembly import build_assembly
from scripts.simple_owner_duty_ledger import legacy_visual_names, selected_duties

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"
OUTPUT = ROOT / "site/owner-barrel-layout-scene.json"
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


def _axis(name, bolt, station):
    direction = bolt.direction.normalized()
    return {
        "name": name,
        "source_station": station,
        "start_mm": list(bolt.start.toTuple()),
        "axis": list(direction.toTuple()),
        "length_mm": bolt.length,
        "diameter_mm": bolt.diameter,
        "diagnostic_only": True,
    }


@lru_cache(maxsize=1)
def build_scene():
    """Preserve every source duty and release flag in one detached viewer export."""
    assembly = build_assembly()
    duties = selected_duties()
    baseline = json.loads(BASELINE.read_text())
    baseline_parts = baseline["parts"]
    baseline_names = {part["name"] for part in baseline_parts}
    if (
        set(assembly["station_dispositions"]) != set(duties)
        or set(assembly["station_modes"]) != set(duties)
        or set(assembly["removed_legacy_stations"]) != set(duties)
        or len(assembly["removed_legacy_sds"]) != 144
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or not set(MOVED_POSTS).issubset(baseline_names)
        or not (set(MOVED_POSTS) | set(BACKERS)).issubset(assembly["wood"])
        or set(assembly["barrel_station"]) != set(assembly["barrels"])
        or set(assembly["bolt_station"]) != set(assembly["bolts"])
        or set(assembly["barrel_station"].values()) != set(duties)
        or any(assembly["release_flags"].values())
    ):
        raise ValueError(
            "Owner barrel assembly is incomplete or release boundary changed"
        )
    hidden = sorted(set(legacy_visual_names(duties, baseline_parts)) | set(MOVED_POSTS))
    if len(hidden) != 170:
        raise ValueError("Owner barrel legacy visual inventory changed")
    solids = [
        _solid(f"owner_barrel_{station}_block", "joint_wood", shape, station)
        for station, shape in assembly["blocks"].items()
    ]
    solids.extend(
        _solid(name, "moved_center_post", assembly["wood"][name])
        for name in MOVED_POSTS
    )
    solids.extend(
        _solid(name, "kicker_screw_backer", assembly["wood"][name]) for name in BACKERS
    )
    barrels = [
        _solid(name, "barrel_nut_envelope", shape, assembly["barrel_station"][name])
        for name, shape in assembly["barrels"].items()
    ]
    bolts = [
        _axis(name, bolt, assembly["bolt_station"][name])
        for name, bolt in assembly["bolts"].items()
    ]
    if (
        not barrels
        or not bolts
        or not all(row["mesh"]["triangles"] for row in solids + barrels)
    ):
        raise ValueError("Barrel viewer has empty geometry")
    clash_stations = set()
    for pair in assembly["diagnostics"]["cross_family_physical_hits_mm3"]:
        for part in pair.split("|"):
            kind, name, *_ = part.split("/")
            if kind == "block":
                clash_stations.add(name)
            elif kind == "barrel":
                clash_stations.add(assembly["barrel_station"][name])
            elif kind == "bolt":
                clash_stations.add(assembly["bolt_station"][name])
    if not clash_stations <= set(duties):
        raise ValueError("Cross-family clash references an unknown duty")
    return {
        "schema": "owner_barrel_layout_scene/v1",
        "status": "complete_layout_concept_not_qualified",
        "baseline": "compact-floor-flush-kerf-right",
        "hidden_baseline_visual_names": hidden,
        "station_modes": assembly["station_modes"],
        "station_dispositions": assembly["station_dispositions"],
        "cross_family_physical_clash_stations": sorted(clash_stations),
        "solids": solids,
        "barrel_nut_envelopes": barrels,
        "diagnostic_bolt_axes": bolts,
        "hardware_basis": assembly["hardware_basis"],
        "assembly_diagnostics": assembly["diagnostics"],
        "inventory": {
            "replaced_angle_duties": len(duties),
            "removed_structural_sds": len(assembly["removed_legacy_sds"]),
            "direct_joint_duties": sum(
                mode == "direct" for mode in assembly["station_modes"].values()
            ),
            "mixed_compact_block_duties": len(assembly["blocks"]),
            "moved_center_posts": len(MOVED_POSTS),
            "kicker_screw_backers": len(BACKERS),
            "barrel_nut_envelopes": len(barrels),
            "new_diagnostic_bolt_axes": len(bolts),
            "fixed_panel_kicker_screw_axes": len(assembly["panel_connections"]),
            "retained_frame_bolt_axes": len(assembly["frame_connections"]),
        },
        "limits": (
            "A complete comparison layout, including red REVISE stations, not a cut, drill, "
            "purchase, or structural release. Retail barrel identity is provisional; "
            "thread-axis location, engagement, strength, access, service conflicts, "
            "backer attachment, tolerances and whole-frame load path remain open."
        ),
        "layout_clearance_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build_scene(), separators=(",", ":")) + "\n")
