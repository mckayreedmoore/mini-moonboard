"""Publish single-layer thin-stock variant without rewriting frozen provenance."""
import argparse
import hashlib
import json
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import cadquery as cq

from . import box_frame as b
from .box_exports import exact_bounds, write_csv
from .connection_geometry import material_intervals
from .export import _export_step
from .raster import render

MODULES = {"bearing-lean-frame": "bearing_frame"}


def export(key):
    model = import_module("mini_moonboard."+MODULES[key])
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    sources = dict(json.loads(Path("exports/continuous-lean-frame/manifest.json").read_text())["sources"])
    for name in ("bearing_frame", "bearing_exports"):
        path = f"mini_moonboard/{name}.py"
        sources[path] = digest(path)
    if any(digest(p) != sha for p, sha in sources.items()):
        raise RuntimeError("Source differs from the preserved baseline")
    directory = Path("exports")/key
    meshes = Path("site/hybrid")/key/"models"
    directory.mkdir(parents=True, exist_ok=True)
    meshes.mkdir(parents=True, exist_ok=True)
    design = {"key": key, "baseline": "continuous-lean-frame",
        "status": "Lower-bearing lean frame — NOT build-ready; joint resistance unqualified",
        "description": "Full-width top/bottom rails retained; lower rail shifted 1.6mm for upright end bearing. "
        "Four rotated ML24Z proxies replace four lower-ledge screws; lower edge infills shortened 1.6mm. "
        "Actual connector fit and capacity remain unqualified. No transferred structural approval."}
    parts, connections = model.parts(), model.connections()
    entries = [(p.name, p.shape, p.blank, p.description, "part") for p in parts]
    entries += [("fastener_"+c.name, cq.Compound.makeCompound(c.components()),
        (c.length, c.diameter, c.diameter), " + ".join(c.members)+"; "+getattr(c, "product_status", "provisional hardware"), c.kind)
        for c in connections]
    assembly, items, raster = cq.Assembly(name=key.replace("-", "_")), [], []
    for name, shape, dims, description, kind in entries:
        assembly.add(shape, name=name)
        path = meshes/f"{name}.stl"
        cq.exporters.export(shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        a = exact_bounds(shape)
        items.append({"name": name, "path": str(path.relative_to("site")),
            "viewer_aabb_mm": [a.xlen, a.ylen, a.zlen], "fabrication": {
                "dimensions_mm": list(dims), "description": description, "kind": kind,
                "clearance_status": "Nominal inspection geometry; NOT structural approval"}})
        color = ((210, 65, 65) if kind == "bolt" else (41, 182, 214) if kind == "screw"
            else (120, 135, 145) if name.startswith("clip_") else
            (40, 46, 51) if name.startswith("main_") else (157, 90, 36))
        raster.append((shape, color))
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts]))
    viewer = meshes.parent/"parts.json"
    viewer.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    _export_step(assembly, directory/f"{key}.step")
    render(raster, directory/f"{key}_front.png")
    write_csv(directory, f"{key}_parts.csv", ("part", "layers", "dimension_1_mm", "dimension_2_mm", "dimension_3_mm",
        "dimension_1_in", "dimension_2_in", "dimension_3_in", "description"),
        [(p.name, p.laminations, *p.blank, *[v/25.4 for v in p.blank], p.description) for p in parts])
    write_csv(directory, f"{key}_connections.csv", ("connection", "kind", "members", "x_mm", "y_mm", "z_mm",
        "x_in", "y_in", "z_in", "axis_x", "axis_y", "axis_z", "length_mm", "length_in", "diameter_mm",
        "diameter_in", "grip_mm", "grip_in", "status"),
        [(c.name, c.kind, " + ".join(c.members), *c.start.toTuple(), *[v/25.4 for v in c.start.toTuple()],
          *c.direction.toTuple(), c.length, c.length/25.4, c.diameter, c.diameter/25.4, c.grip, c.grip/25.4,
          getattr(c, "product_status", "provisional hardware")) for c in connections])
    groups = defaultdict(list)
    for p in parts:
        if not p.name.startswith("clip_"):
            groups[tuple(round(v, 6) for v in p.blank)].append(p.name)
    write_csv(directory, f"{key}_blank_groups.csv", ("quantity", "dimension_1_mm", "dimension_2_mm", "dimension_3_mm",
        "dimension_1_in", "dimension_2_in", "dimension_3_in", "parts", "status"),
        [(len(names), *dims, *[v/25.4 for v in dims], " + ".join(names),
          "Blank grouping only; profiles, grain, holes and actual-stock allowances still govern")
         for dims, names in sorted(groups.items())])
    # Part-local X/S/N coordinates are useful for an inspection drilling card.
    # They are not approved pilots or templates for drilling purchased steel.
    raw = {p.name: p for p in model.parts(False)}
    origin, tangent, normal = b.point(0, 0, 0), (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized(), b.normal()
    project = lambda v: (v.x, v.dot(tangent), v.dot(normal))
    rows = []
    for c in connections:
        for name in c.members:
            if name.startswith("clip_"):
                continue
            shape = raw[name].shape
            # Inverse board transform also captures extrema between vertices
            # on curved profiles, unlike a vertex-only minimum.
            local_bounds = exact_bounds(shape.translate(-origin).rotate((0, 0, 0), (1, 0, 0), -50.))
            low = [local_bounds.xmin, local_bounds.ymin, local_bounds.zmin]
            ray_start = 0.
            for start, end in material_intervals(shape, c.start, c.direction, ray_start, c.length):
                xyz = project(c.start+c.direction*start-origin)
                offsets = [v-a for v, a in zip(xyz, low, strict=True)]
                rows.append((name, c.name, *offsets, *[v/25.4 for v in offsets], *project(c.direction), end-start,
                    "Entry relative to this part's minimum X/S/N; see STEP for shaped parts; NOT machining approval"))
    write_csv(directory, f"{key}_hole_entries.csv", ("part", "connection", "from_min_x_mm", "from_min_s_mm", "from_min_n_mm",
        "from_min_x_in", "from_min_s_in", "from_min_n_in", "axis_x", "axis_s", "axis_n", "material_run_mm", "status"), rows)
    if any(digest(p) != sha for p, sha in sources.items()):
        raise RuntimeError("Source changed during export")
    manifest = {"design": design, "sources": sources,
        "artifacts": {p.name: digest(p) for p in directory.iterdir() if p.name != "manifest.json"},
        "viewer_artifacts": {str(p.relative_to("site")): digest(p) for p in [viewer, *sorted(meshes.glob("*.stl"))]}}
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=MODULES, required=True)
    export(parser.parse_args().variant)
