"""Publish the base-bearing layout study; no fabricated connection schedule."""
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import base_frame as model
from .box_exports import exact_bounds, write_csv
from .export import _export_step
from .panel_grid_v2 import main_tnut_datums
from .raster import render


def export():
    key = model.KEY
    directory = Path("exports") / key
    meshes = Path("site/hybrid") / key / "models"
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    # Preserve the dependency closure of reused historical leg geometry.
    sources = dict(json.loads(Path("exports/bearing-lean-frame/manifest.json").read_text())["sources"])
    for name in ("base_frame", "base_exports", "panel_grid_v2"):
        path = f"mini_moonboard/{name}.py"
        sources[path] = digest(path)
    if any(digest(path) != sha for path, sha in sources.items()):
        raise RuntimeError("Historical dependency changed")
    directory.mkdir(parents=True, exist_ok=True)
    meshes.mkdir(parents=True, exist_ok=True)
    design = {"key": key, "baseline": "bearing-lean-frame",
        "status": "Geometry-only base concept — NOT build-ready; connections omitted",
        "description": "Panels cover side framing; horizontal base supports flat-cut sloped members. "
        "Corrected panel-edge grid adapted to 1219.2 mm sheets. No transferred FEA or connection approval.",
        "tnut_row_stations_mm": [main_tnut_datums()[f"A{row}"][1] for row in range(1, 13)]}
    parts = model.parts()
    assembly, items, raster = cq.Assembly(name=key.replace("-", "_")), [], []
    for part in parts:
        assembly.add(part.shape, name=part.name)
        path = meshes / f"{part.name}.stl"
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        items.append({"name": part.name, "path": str(path.relative_to("site")),
            "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "fabrication": {"dimensions_mm": list(part.blank), "description": part.description,
                "kind": "part", "clearance_status": "Layout only; joints and hardware not designed"}})
        raster.append((part.shape, (40, 46, 51) if part.name.startswith("main_")
                       else (80, 88, 96) if part.name in ("kicker_left", "kicker_right") else (157, 90, 36)))
    bounds = exact_bounds(cq.Compound.makeCompound([part.shape for part in parts]))
    viewer = meshes.parent / "parts.json"
    viewer.write_text(json.dumps({"design": design, "parts": items,
        "bounds_mm": [[getattr(bounds, axis+end) for axis in "xyz"] for end in ("min", "max")]}, indent=2)+"\n")
    _export_step(assembly, directory / f"{key}.step")
    render(raster, directory / f"{key}_front.png")
    write_csv(directory, f"{key}_parts.csv",
        ("part", "layers", "dimension_1_mm", "dimension_2_mm", "dimension_3_mm",
         "dimension_1_in", "dimension_2_in", "dimension_3_in", "description"),
        [(p.name, p.laminations, *p.blank, *[v/25.4 for v in p.blank], p.description) for p in parts])
    if any(digest(path) != sha for path, sha in sources.items()):
        raise RuntimeError("Source changed during export")
    manifest = {"design": design, "sources": sources,
        "artifacts": {p.name: digest(p) for p in directory.iterdir() if p.name != "manifest.json"},
        "viewer_artifacts": {str(p.relative_to("site")): digest(p)
                             for p in [viewer, *sorted(meshes.glob("*.stl"))]}}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    export()
