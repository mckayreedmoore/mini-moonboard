"""Isolated zero-extension long-bolt viewer; no frozen exporter or FE changes."""
import json
from pathlib import Path

import cadquery as cq

from . import leg_hardware_trial as model
from . import lumber_leg_exports as base
from .box_exports import exact_bounds
from .box_frame import Part

KEY = "lumber-leg-hardware-2x6-e0"
DIRECTORY = Path("site/hybrid")/KEY
LIMITS = "Geometry-only compact hardware trial; NOT build-ready; no matching FE or strength acceptance"


def export():
    parent = json.loads(base.PARENT.read_text())
    sources = {**parent["sources"], str(base.PARENT): base.digest(base.PARENT)}
    for path in ("mini_moonboard/lumber_leg_frame.py", "mini_moonboard/lumber_leg_exports.py",
                 "mini_moonboard/lumber_leg_spread_frame.py", "mini_moonboard/leg_hardware_trial.py",
                 "mini_moonboard/compact_hardware_exports.py", "uv.lock"):
        sources[path] = base.digest(path)
    inherited = {str(Path("site")/path): sha for path, sha in parent["viewer_artifacts"].items()}
    if any(base.digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Parent geometry or viewer evidence changed")
    if DIRECTORY.exists():
        raise FileExistsError("Refusing to overwrite compact viewer evidence")
    baseline = json.loads(base.VIEWER.read_text())
    items = [p for p in baseline["parts"] if not base.replaced(p["name"])]
    parts, connections = model.parts(extension=0.), model.connections(extension=0.)
    changed = [p for p in parts if p.name.startswith(("base_side_", "lumber_leg_"))]
    fasteners = [(c, cq.Compound.makeCompound(c.components())) for c in connections]
    for connection, shape in fasteners:
        if isinstance(connection, model.TrialBolt):
            changed.append(Part("fastener_"+connection.name, shape,
                (connection.length, connection.diameter, connection.diameter),
                connection.product_status+"; "+" + ".join(connection.members), 1))
    meshes = DIRECTORY/"models"
    meshes.mkdir(parents=True, exist_ok=False)
    for part in changed:
        path = meshes/f"{part.name}.stl"
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        items.append({"name": part.name, "path": str(path.relative_to("site")),
            "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "fabrication": {"dimensions_mm": list(part.blank),
                "dimensions_imperial": [v/25.4 for v in part.blank],
                "description": part.description+"; spread100x50/top150; zero foot extension; new-build drilling",
                "kind": "bolt" if part.name.startswith("fastener_") else "part",
                "clearance_status": LIMITS}})
    if len(changed) != 12 or len(items) != 283 or len({p["name"] for p in items}) != 283:
        raise RuntimeError("Expected 101 bodies and 182 connection assemblies")
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]+[s for _,s in fasteners]))
    design = {**baseline["design"], "key": KEY, "baseline": "wide-principal-development",
        "status": LIMITS, "stock": "2x6", "extra_foot_extension_mm": 0.,
        "along_leg_pitch_mm": 100., "along_rim_pitch_mm": 50., "top_extension_mm": 150.,
        "bolt_length_mm": model.BOLT_LENGTH, "washers_per_bolt": 4,
        "washer_thickness_mm": model.WASHER_NOMINAL,
        "qualified_for_design": False, "native_fe_match": False,
        "description": "2×6 legs, actual 38.1 × 139.7 mm (1.5 × 5.5 in); zero added foot extension "
            "(0 mm / 0 in). Spread100×50 mm (3.94 × 1.97 in), top150 mm (5.91 in). "
            "3/8-16 × 4¼ in (107.95 mm) bolts, four MCX014423 washers each, two under each end; "
            "washer thickness shown at interval midpoint, not a manufacturer nominal. "
            "Geometry only, not an FE-matched model or strength approval. "
            "Zero extension does not certify containment beneath the top projection."}
    viewer = DIRECTORY/"parts.json"
    viewer.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    if any(base.digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Source or parent asset changed during export")
    artifacts = {p["path"]: base.digest(Path("site")/p["path"]) for p in items}
    artifacts[str(viewer.relative_to("site"))] = base.digest(viewer)
    (DIRECTORY/"manifest.json").write_text(json.dumps({"design": design, "sources": sources,
        "hardware_sources": model.SOURCES, "parent_viewer_artifacts": parent["viewer_artifacts"],
        "viewer_artifacts": artifacts, "body_count": len(parts), "connection_count": len(connections),
        "new_mesh_count": len(changed), "reused_mesh_count": len(items)-len(changed)}, indent=2)+"\n")
    return viewer


if __name__ == "__main__":
    print(export())
