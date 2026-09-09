"""Isolated spread-joint viewers; original model/export sources stay frozen."""
import argparse
import json
from pathlib import Path

import cadquery as cq

from . import lumber_leg_exports as base
from . import lumber_leg_spread_frame as model
from .box_exports import exact_bounds

KEY = "lumber-leg-spread-2x8-e300"
SIZE, EXTENSION = "2x8", 300.
SIZES = ("2x6", "2x8")


def export(size=SIZE):
    if size not in SIZES:
        raise ValueError("Select spread 2x6 or 2x8")
    key = f"lumber-leg-spread-{size}-e300"
    parent = json.loads(base.PARENT.read_text())
    sources = {**parent["sources"], str(base.PARENT): base.digest(base.PARENT)}
    for path in ("mini_moonboard/lumber_leg_frame.py", "mini_moonboard/lumber_leg_exports.py",
                 "mini_moonboard/lumber_leg_spread_frame.py", "mini_moonboard/spread_leg_exports.py", "uv.lock"):
        sources[path] = base.digest(path)
    inherited = {str(Path("site")/path): sha for path, sha in parent["viewer_artifacts"].items()}
    if any(base.digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Parent geometry or viewer evidence changed")
    baseline = json.loads(base.VIEWER.read_text())
    items = [p for p in baseline["parts"] if not base.replaced(p["name"])]
    parts, connections = model.parts(size, EXTENSION), model.connections(size, EXTENSION)
    changed = [p for p in parts if p.name.startswith(("base_side_", "lumber_leg_"))]
    fasteners = [(c, cq.Compound.makeCompound(c.components())) for c in connections]
    for connection, shape in fasteners:
        if connection.name.startswith("lumber_leg_bolt_"):
            changed.append(model.original.b.Part("fastener_"+connection.name, shape,
                (connection.length, connection.diameter, connection.diameter),
                connection.product_status+"; "+" + ".join(connection.members), 1))
    directory = Path("site/hybrid")/key
    meshes = directory/"models"
    meshes.mkdir(parents=True, exist_ok=True)
    for part in changed:
        path = meshes/f"{part.name}.stl"
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        items.append({"name": part.name, "path": str(path.relative_to("site")),
            "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "fabrication": {"dimensions_mm": list(part.blank),
                "dimensions_imperial": [v/25.4 for v in part.blank],
                "description": part.description+"; spread100x50/top150; new drilling, not a retrofit",
                "kind": "bolt" if part.name.startswith("fastener_") else "part",
                "clearance_status": model.LIMITS}})
    if len(changed) != 12 or len(items) != 283 or len({p["name"] for p in items}) != 283:
        raise RuntimeError("Expected 101 bodies and 182 connection assemblies")
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]+[s for _, s in fasteners]))
    design = {**baseline["design"], "key": key, "baseline": "wide-principal-development",
        "status": model.LIMITS, "stock": size, "extra_foot_extension_mm": EXTENSION,
        "along_leg_pitch_mm": model.ALONG_LEG_PITCH, "along_rim_pitch_mm": model.ALONG_RIM_PITCH,
        "top_extension_mm": model.TOP_EXTENSION,
        "description": f"{size.replace('x', '×')} legs, actual 38.1 × {model.WIDTHS[size]:g} mm "
            f"(1.5 × {model.WIDTHS[size]/25.4:g} in); +300 mm (11.81 in) footprint. "
            "Spread100×50 mm (3.94 × 1.97 in) bolt group; square top150 mm (5.91 in) beyond centroid. "
            "Other wide-frame parts retained. Geometry viewer only, not a native FE result or strength approval."}
    viewer = directory/"parts.json"
    viewer.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    if any(base.digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Source or parent asset changed during export")
    artifacts = {p["path"]: base.digest(Path("site")/p["path"]) for p in items}
    artifacts[str(viewer.relative_to("site"))] = base.digest(viewer)
    (directory/"manifest.json").write_text(json.dumps({"design": design, "sources": sources,
        "parent_viewer_artifacts": parent["viewer_artifacts"], "viewer_artifacts": artifacts,
        "body_count": len(parts), "connection_count": len(connections),
        "new_mesh_count": len(changed), "reused_mesh_count": len(items)-len(changed)}, indent=2)+"\n")
    return viewer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", choices=(*SIZES, "all"), nargs="?", default=SIZE)
    args = parser.parse_args()
    for size in SIZES if args.size == "all" else (args.size,):
        print(export(size), flush=True)
