"""Separate lightweight publication of the no-custom-steel concept candidates."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

from .box_exports import exact_bounds, write_csv
from .export import _export_step
from .raster import render

VARIANTS = ("wood-first-mvp", "commercial-bracket-mvp")


def export(variant):
    if variant == VARIANTS[0]:
        from . import wood_mvp as model
    elif variant == VARIANTS[1]:
        from . import bracket_mvp as model
    else:
        raise ValueError("Unknown MVP variant")
    design = {"key": variant, "baseline": "top-joint-development",
              "status": "MVP — no custom steel; NOT build-ready; structural qualification pending",
              "description": ("Wood-bearing housed/lapped joints with mechanical retention. " if variant == VARIANTS[0]
                              else "Commercial connector alternative with provisional factory-fit envelopes. ")
              + "Independent design concept, not copied manufacturer plans. Purchased face stock and independent leg plies retained. Dimensions, hardware fit, assembly and strength require review; no new FEA or IP clearance claimed."}
    directory = Path("exports")/variant
    viewer = Path("site")
    meshes = viewer/"hybrid"/variant/"models"
    directory.mkdir(parents=True, exist_ok=True)
    meshes.mkdir(parents=True, exist_ok=True)
    sources = dict(json.loads(Path("exports/top-joint-development/manifest.json").read_text())["sources"])
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    for module in ("wood_mvp", "bracket_mvp", "mvp_exports"):
        source = f"mini_moonboard/{module}.py"
        sources[source] = digest(source)
    if any(digest(path) != value for path, value in sources.items()):
        raise RuntimeError("Baseline source differs from preserved export")
    parts, connections = model.parts(), model.connections()
    entries = [(p.name, p.shape, p.blank, p.description, "part") for p in parts]
    entries += [("fastener_"+c.name, cq.Compound.makeCompound(c.components()),
                 (c.length, c.diameter, c.diameter), " + ".join(c.members)+"; "+getattr(c, "product_status", "provisional hardware"), c.kind)
                for c in connections]
    assembly = cq.Assembly(name=variant.replace("-", "_"))
    items, render_items = [], []
    for name, shape, dimensions, description, kind in entries:
        assembly.add(shape, name=name)
        path = meshes/f"{name}.stl"
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(shape)
        color = ((210, 65, 65) if kind == "bolt" else (41, 182, 214) if kind == "screw"
                 else (120, 135, 145) if name.startswith("clip_")
                 else (40, 46, 51) if name.startswith("main_") else (157, 90, 36))
        render_items.append((shape, color))
        items.append({"name": name, "path": str(path.relative_to(viewer)),
                      "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
                      "fabrication": {"dimensions_mm": list(dimensions), "description": description,
                                      "kind": kind, "clearance_status": "MVP; NOT structural approval"}})
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]))
    viewer_manifest = meshes.parent/"parts.json"
    viewer_manifest.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    _export_step(assembly, directory/f"{variant}.step")
    render(render_items, directory/f"{variant}_front.png")
    write_csv(directory, f"{variant}_parts.csv",
              ("part", "layers", "dimension_1_mm", "dimension_2_mm", "dimension_3_mm",
               "dimension_1_in", "dimension_2_in", "dimension_3_in", "description"),
              [(p.name, p.laminations, *p.blank, *[v/25.4 for v in p.blank], p.description) for p in parts])
    write_csv(directory, f"{variant}_connections.csv",
              ("connection", "kind", "members", "x_mm", "y_mm", "z_mm", "x_in", "y_in", "z_in",
               "axis_x", "axis_y", "axis_z", "length_mm", "length_in", "diameter_mm", "diameter_in",
               "grip_mm", "grip_in", "status"),
              [(c.name, c.kind, " + ".join(c.members), *c.start.toTuple(),
                *[v/25.4 for v in c.start.toTuple()], *c.direction.toTuple(),
                c.length, c.length/25.4, c.diameter, c.diameter/25.4, c.grip, c.grip/25.4,
                getattr(c, "product_status", "MVP")) for c in connections])
    if any(digest(path) != value for path, value in sources.items()):
        raise RuntimeError("Source changed while exporting")
    manifest = {"design": design, "sources": sources,
                "artifacts": {p.name: digest(p) for p in directory.iterdir() if p.name != "manifest.json"},
                "viewer_artifacts": {str(p.relative_to(viewer)): digest(p) for p in [viewer_manifest, *sorted(meshes.glob("*.stl"))]}}
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    export(parser.parse_args().variant)
