"""Publish the removable-panel geometry candidate without changing frozen exports."""
import hashlib
import json
from pathlib import Path

import cadquery as cq

from . import insert_frame as model
from .box_exports import exact_bounds, write_csv
from .export import _export_step
from .panel_grid_v2 import main_tnut_datums
from .raster import render


def export():
    key = model.KEY
    directory = Path("exports") / key
    meshes = Path("site/hybrid") / key / "models"
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    baseline = Path("exports/timber-base-development/manifest.json")
    sources = dict(json.loads(baseline.read_text())["sources"])
    reference = Path("docs/panel-insert-reference.json")
    for path in (baseline, reference, Path("mini_moonboard/insert_frame.py"),
                 Path("mini_moonboard/insert_exports.py")):
        sources[str(path)] = digest(path)
    if any(digest(path) != sha for path, sha in sources.items()):
        raise RuntimeError("Historical dependency changed")
    facts = json.loads(reference.read_text())
    insert, assumptions = facts["insert"], facts["project_geometry_assumptions"]
    directory.mkdir(parents=True, exist_ok=True)
    meshes.mkdir(parents=True, exist_ok=True)
    design = {"key": key, "baseline": "timber-base-development",
        "status": "Removable-panel connection development — NOT build-ready; insert resistance unqualified",
        "description": "Machine screws and flush timber inserts replace panel wood screws. "
        "Nominal bodies and provisional drilling reservations are not approved installation details. "
        "Corrected 1219.2 mm panel-edge grid; no transferred structural approval.",
        "tnut_row_stations_mm": [main_tnut_datums()[f"A{row}"][1] for row in range(1, 13)]}
    connections = tuple(model.connections())
    kinds = {"fastener_"+c.name: c.kind for c in connections}
    parts = list(model.parts())
    kinds.update({p.name: "insert" for p in parts if p.name.startswith("insert_")})
    for c in connections:
        parts.append(model.b.Part("fastener_"+c.name, cq.Compound.makeCompound(c.components()),
            (c.length, c.diameter, c.diameter), c.product_status+"; "+" + ".join(c.members), 1))
    assembly, items, raster = cq.Assembly(name=key.replace("-", "_")), [], []
    for part in parts:
        assembly.add(part.shape, name=part.name)
        path = meshes / f"{part.name}.stl"
        cq.exporters.export(part.shape, str(path), cq.exporters.ExportTypes.STL, tolerance=.5)
        bounds = exact_bounds(part.shape)
        kind = kinds.get(part.name, "part")
        items.append({"name": part.name, "path": str(path.relative_to("site")),
            "viewer_aabb_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "fabrication": {"dimensions_mm": list(part.blank), "description": part.description,
                "kind": kind, "clearance_status": "Geometry candidate only; effective engagement and joint resistance unqualified"}})
        color = ((210, 65, 65) if kind == "bolt" else (41, 182, 214) if kind == "screw" else
                 (120, 135, 145) if kind == "insert" or part.name.startswith("clip_") else
                 (40, 46, 51) if part.name.startswith("main_") else
                 (80, 88, 96) if part.name in ("kicker_left", "kicker_right") else (157, 90, 36))
        raster.append((part.shape, color))
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
    write_csv(directory, f"{key}_connections.csv",
        ("connection", "kind", "members", "length_mm", "length_in", "diameter_mm", "diameter_in",
         "grip_mm", "grip_in", "x_mm", "y_mm", "z_mm", "axis_x", "axis_y", "axis_z", "status"),
        [(c.name, c.kind, " + ".join(c.members), c.length, c.length/25.4, c.diameter,
          c.diameter/25.4, c.grip, c.grip/25.4, *c.start.toTuple(), *c.direction.toTuple(), c.product_status)
         for c in connections])
    panel_connections = model.panel_connections()
    clearance = assumptions["panel_clearance_bore_diameter"]
    pilot, depth = insert["pilot_diameter_inch_recommendation"], assumptions["pilot_tip_clearance_depth"]
    body = insert["nominal_outer_diameter"]
    body_max = body+insert["drawing_general_tolerance_plus_minus"]
    write_csv(directory, f"{key}_panel_drilling.csv",
        ("connection", "members", "face_x_mm", "face_y_mm", "face_z_mm",
         "receiver_x_mm", "receiver_y_mm", "receiver_z_mm", "axis_x", "axis_y", "axis_z",
         "panel_clearance_mm", "panel_clearance_in", "receiver_pilot_mm", "receiver_pilot_in",
         "receiver_pilot_depth_mm", "receiver_pilot_depth_in", "insert_nominal_od_mm", "insert_nominal_od_in",
         "insert_max_od_reservation_mm", "insert_max_od_reservation_in", "effective_engagement_mm", "status"),
        [(c.name, " + ".join(c.members), *c.start.toTuple(), *c.insert_start.toTuple(), *c.direction.toTuple(),
          clearance, clearance/25.4, pilot, pilot/25.4, depth, depth/25.4, body, body/25.4,
          body_max, body_max/25.4, "unknown",
          "Provisional geometry: insert OD is not pilot diameter; depth and engagement require qualification")
         for c in panel_connections])
    if any(digest(path) != sha for path, sha in sources.items()):
        raise RuntimeError("Source changed during export")
    manifest = {"design": design, "sources": sources,
        "artifacts": {p.name: digest(p) for p in directory.iterdir() if p.name != "manifest.json"},
        "viewer_artifacts": {str(p.relative_to("site")): digest(p)
                             for p in [viewer, *sorted(meshes.glob("*.stl"))]}}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    export()
