"""Viewer-only straight-leg variants, reusing the authenticated wide-frame assets.

No STEP duplication or structural qualification: only the four changed wood
bodies and eight replacement bolt assemblies receive new meshes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import lumber_leg_frame as model
from .box_exports import exact_bounds

PARENT = Path("exports/wide-principal-development/manifest.json")
VIEWER = Path("site/hybrid/wide-principal-development/parts.json")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(size, extension):
    model.geometry(size, extension)
    return f"lumber-leg-{size}-e{int(extension)}"


def replaced(name):
    return name.startswith(("leg_", "fastener_analysis_leg_wall_bolt_", "fastener_leg_stitch_")) or name in (
        "base_side_left", "base_side_right")


def export(size, extension=0.):
    variant = key(size, extension)
    parent = json.loads(PARENT.read_text())
    sources = {**parent["sources"], str(PARENT): digest(PARENT)}
    for path in ("mini_moonboard/lumber_leg_frame.py", "mini_moonboard/lumber_leg_exports.py", "uv.lock"):
        sources[path] = digest(path)
    inherited = {str(Path("site")/path): sha for path, sha in parent["viewer_artifacts"].items()}
    if any(digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Parent geometry or viewer evidence changed")
    baseline = json.loads(VIEWER.read_text())
    items = [p for p in baseline["parts"] if not replaced(p["name"])]
    parts = model.parts(size, extension)
    connections = model.connections(size, extension)
    changed = [p for p in parts if p.name.startswith(("base_side_", "lumber_leg_"))]
    fasteners = [(c, cq.Compound.makeCompound(c.components())) for c in connections]
    for c, shape in fasteners:
        if c.name.startswith("lumber_leg_bolt_"):
            changed.append(model.b.Part("fastener_"+c.name, shape,
                (c.length, c.diameter, c.diameter), c.product_status+"; "+" + ".join(c.members), 1))
    directory = Path("site/hybrid")/variant
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
                "description": part.description+"; new-build drilling, not a retrofit",
                "kind": "bolt" if part.name.startswith("fastener_") else "part",
                "clearance_status": model.LIMITS}})
    if len(changed) != 12 or len(items) != 283 or len({p["name"] for p in items}) != 283:
        raise RuntimeError("Expected 101 bodies and 182 connection assemblies")
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]+[s for _, s in fasteners]))
    design = {**baseline["design"], "key": variant, "baseline": "wide-principal-development",
        "status": model.LIMITS,
        "description": f"Nominal {size} legs: actual 38.1 × {model.WIDTHS[size]:g} mm "
            f"(1.5 × {model.WIDTHS[size]/25.4:g} in); extra footprint {extension:g} mm "
            f"({extension/25.4:.3f} in) beyond the current foot centre. "
            "New four-bolt groups and rim holes; other wide-frame parts retained. "
            "Geometry comparison only: no member, connection or stability approval."}
    viewer = directory/"parts.json"
    viewer.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    if any(digest(path) != sha for path, sha in (sources | inherited).items()):
        raise RuntimeError("Source or parent asset changed during export")
    artifacts = {p["path"]: digest(Path("site")/p["path"]) for p in items}
    artifacts[str(viewer.relative_to("site"))] = digest(viewer)
    (directory/"manifest.json").write_text(json.dumps({"design": design, "sources": sources,
        "parent_viewer_artifacts": parent["viewer_artifacts"], "viewer_artifacts": artifacts,
        "body_count": len(parts), "connection_count": len(connections),
        "new_mesh_count": len(changed), "reused_mesh_count": len(items)-len(changed)}, indent=2)+"\n")
    return viewer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", choices=(*model.WIDTHS, "all"))
    parser.add_argument("--extension", type=float, choices=model.EXTENSIONS, default=0.)
    args = parser.parse_args()
    for size, extension in ([(s, e) for s in model.WIDTHS for e in model.EXTENSIONS]
                            if args.size == "all" else [(args.size, args.extension)]):
        print(export(size, extension), flush=True)
