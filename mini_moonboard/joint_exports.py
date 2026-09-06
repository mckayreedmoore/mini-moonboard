"""Separate viewer/export artifacts for provisional development variants."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import joint_frame
from .box_exports import exact_bounds, write_csv
from .export import _export_step
from .raster import render

KEY = "joint-development"
DESIGN = {
    "key": KEY,
    "baseline": "2x8-foot100",
    "status": "PROVISIONAL — geometry development, not build-ready; candidate FEA not run",
    "description": "Wider seam battens, solid ribs with wire chases, relocated custom rear angles and longer bolts. Steel fabrication, materials and fastener products remain unresolved.",
}
INDEPENDENT_DESIGN = {
    "key": "independent-leg-development",
    "baseline": KEY,
    "status": "PROVISIONAL — independent-ply experiment; candidate FEA not run",
    "description": "Four separate plywood leg plies and six internal stitch bolts on the joint redesign. No adhesive, interface-friction or external-bracing credit. Products and resistance unresolved.",
}


def export(directory=None, viewer=Path("site"), *, variant=KEY):
    if variant == KEY:
        model, design = joint_frame, DESIGN
    elif variant == INDEPENDENT_DESIGN["key"]:
        from . import independent_leg_frame
        model, design = independent_leg_frame, INDEPENDENT_DESIGN
    else:
        raise ValueError("Unknown development variant")
    directory = Path(directory) if directory is not None else Path("exports")/variant
    parts, connections = model.parts(), model.connections()
    directory.mkdir(parents=True, exist_ok=True)
    models = viewer/"hybrid"/variant/"models"
    models.mkdir(parents=True, exist_ok=True)
    assembly = cq.Assembly(name=variant.replace("-", "_")+"_PROVISIONAL")
    entries = [(p.name, p.shape, p.blank, p.description, "part") for p in parts]
    entries.extend(("fastener_"+c.name, cq.Compound.makeCompound(c.components()),
                    (c.length, c.diameter, c.diameter), " + ".join(c.members)+
                    "; nominal hardware envelope, capacity unvalidated", c.kind) for c in connections)
    items, solids = [], []
    for name, shape, dims, description, kind in entries:
        assembly.add(shape, name=name)
        color = ((210, 65, 65) if kind == "bolt" else (41, 182, 214) if kind == "screw"
                 else (120, 135, 145) if name.startswith("angle_")
                 else (40, 46, 51) if name.startswith("main_") else (157, 90, 36))
        solids.append((shape, color))
        path = models/f"{name}.stl"
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(shape)
        items.append({"name": name, "path": str(path.relative_to(viewer)),
                      "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
                      "fabrication": {"dimensions_mm": list(dims), "description": description,
                                      "kind": kind, "clearance_status": "Development geometry; NOT structural approval"}})
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]))
    viewer_manifest = models.parent/"parts.json"
    viewer_manifest.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    _export_step(assembly, directory/f"{variant}.step")
    render(solids, directory/f"{variant}_front.png")
    render([(shape.rotate((0, 0, 0), (0, 0, 1), 180), color) for shape, color in solids],
           directory/f"{variant}_rear.png")
    write_csv(directory, f"{variant}_parts.csv",
              ("part", "layers", "dimension_1_mm", "dimension_2_mm", "dimension_3_mm",
               "dimension_1_in", "dimension_2_in", "dimension_3_in", "description"),
              [(p.name, p.laminations, *p.blank, *[v/25.4 for v in p.blank], p.description) for p in parts])
    write_csv(directory, f"{variant}_connections.csv",
              ("connection", "kind", "members", "x_mm", "y_mm", "z_mm", "axis_x", "axis_y", "axis_z",
               "length_mm", "length_in", "diameter_mm", "grip_mm", "status"),
              [(c.name, c.kind, " + ".join(c.members), *c.start.toTuple(), *c.direction.toTuple(),
                c.length, c.length/25.4, c.diameter, c.grip, design["status"]) for c in connections])
    sources = list(map(Path, ("mini_moonboard/joint_exports.py", "mini_moonboard/joint_frame.py", "mini_moonboard/footprint_frame.py",
               "mini_moonboard/shallow_frame.py", "mini_moonboard/hybrid_frame.py", "mini_moonboard/hybrid.py",
               "mini_moonboard/box_frame.py", "mini_moonboard/model.py", "mini_moonboard/panel_grid.py",
               "mini_moonboard/box_exports.py", "mini_moonboard/export.py", "mini_moonboard/raster.py")))
    if variant == INDEPENDENT_DESIGN["key"]:
        sources.append(Path("mini_moonboard/independent_leg_frame.py"))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"design": design, "sources": {str(p): digest(p) for p in sources},
                "artifacts": {p.name: digest(p) for p in sorted(directory.iterdir()) if p.name != "manifest.json"},
                "viewer_artifacts": {str(p.relative_to(viewer)): digest(p) for p in [viewer_manifest, *sorted(models.glob("*.stl"))]}}
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=(KEY, INDEPENDENT_DESIGN["key"]), default=KEY)
    export(variant=parser.parse_args().variant)
