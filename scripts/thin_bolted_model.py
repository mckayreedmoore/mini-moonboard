"""Export the nominal thinner bolted layout as a separate review model.

Reconstruct the frozen v4 inputs, check the CAT 23/32 screw penetration, and
rebuild panel openings at the retained world datums. Existing authorities,
failed experiments and viewer meshes remain unchanged. This is CAD review
evidence; it supplies no joint resistance, drilling instruction or release.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cadquery as cq

from mini_moonboard import hold_tnut_reinforcement as tnuts
from mini_moonboard import no_shoes_frame, panel_grid_v2, product_frame
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import hl35_candidate as shared
from scripts import hl35_nominal_service_candidate as service_tools
from scripts import thin_bolted_fitting_screen as screen
from scripts import thin_bolted_layout_revision as revision
from scripts import thin_bolted_occupied as occupied

ROOT = shared.ROOT
LAYOUT = occupied.RAW_REPORT.parent / "mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
SCENE = ROOT / "site/thin-bolted-scene.json"
EVIDENCE = LAYOUT.parent / "integrated-model-v4.json"
CONTRACT = ROOT / "thin-bolted-candidate.json"
BASELINE = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"
CANDIDATE = "compact-floor-flush-thin-bolted-development"
REVISION = "thin-offset-header-rows-shallow-wires-v4-review-model"
ROLES = ["shaft", "head", "head_washer", "nut_washer", "nut"]
PLY = product_frame.FACE_THICKNESS_MM


def source_layout() -> dict:
    if shared.sha(LAYOUT) != LAYOUT_SHA:
        raise ValueError("preserve the frozen occupied comparison")
    report = json.loads(LAYOUT.read_text())
    for name, expected in report["source_sha256"].items():
        if shared.sha(ROOT / name) != expected:
            raise ValueError(f"layout source differs: {name}")
    if report["candidate"] != CANDIDATE or report["counts"]["physical_bolt_axes"] != 70:
        raise ValueError("unexpected layout identity or bolt census")
    return report


def unperforated_main(shape: cq.Shape, inward: cq.Vector) -> cq.Shape:
    """Fill internal openings by extruding the unchanged planar outer wire.

    This applies only to a constant-thickness panel. The caller checks bounds
    and containment; beveled kicker outlines use their complete seam profile.
    """
    low, high = shared.projected_extent(shape, inward)
    candidates = [face for face in shape.Faces() if face.geomType() == "PLANE"
                  and abs(face.normalAt().dot(inward)) > .999999
                  and abs(face.Center().dot(inward) - low) < 1e-5]
    if not candidates:
        raise ValueError("no front planar panel face")
    face = max(candidates, key=lambda f: f.Area())
    return cq.Solid.extrudeLinear(face.outerWire(), [], inward.multiply(high - low))


def panel_outlines(raw: dict) -> tuple[dict, list]:
    outlines, records = {}, []
    for name, shape in raw.items():
        if name.startswith("main_"):
            outlines[name] = unperforated_main(shape, screen.N)
    for name in ("kicker_left", "kicker_right"):
        b = raw[name].BoundingBox()
        slab = cq.Solid.makeBox(b.xlen, b.ylen, b.zlen, cq.Vector(b.xmin, b.ymin, b.zmin))
        outlines[name] = slab.cut(outlines["main_lower_" + name.rsplit("_", 1)[1]]).clean()
    if len(outlines) != 6:
        raise ValueError("retain six owned panel outlines")
    for name, shape in outlines.items():
        before, after = raw[name].BoundingBox(), shape.BoundingBox()
        error = max(abs(getattr(before, a) - getattr(after, a))
                    for a in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"))
        outside = raw[name].cut(shape).Volume()
        if error > 1e-5 or outside > .01:
            raise ValueError(f"panel outline differs: {name}")
        records.append({"panel": name, "maximum_bounds_change_mm": error,
                        "source_material_outside_recovered_outline_mm3": outside,
                        "filled_source_openings_mm3": shape.Volume() - raw[name].Volume(),
                        "panel_thickness_mm": PLY,
                        "actual_panel_thickness_or_holes_inspected": False})
    return outlines, records


def machined_panels(raw: dict, screws: list, parent: dict) -> tuple[dict, dict]:
    outlines, outline_records = panel_outlines(raw)
    panels, features = dict(outlines), []

    def cut(name: str, identity: str, diameter: float, point: cq.Vector,
            direction: cq.Vector, kind: str) -> None:
        cutter = cq.Solid.makeCylinder(diameter / 2, PLY + 2., point - direction, direction)
        before = panels[name].Volume()
        panels[name] = panels[name].cut(cutter).clean()
        removed = before - panels[name].Volume()
        if removed <= .01:
            raise ValueError(f"panel feature misses its owner: {identity}")
        features.append({"panel": name, "identity": identity, "kind": kind,
                         "diameter_mm": diameter, "start_xyz_mm": shared.xyz(point),
                         "direction_xyz": shared.xyz(direction), "removed_volume_mm3": removed,
                         "drill_size_or_physical_hole_qualified": False})

    for row in tnuts.datums(no_shoes_frame):
        rear = cq.Vector(*row["rear_seating_xyz_mm"])
        inward = -cq.Vector(*row["barrel_into_panel_direction"])
        cut(row["panel"], row["name"], 11.1125, rear - inward.multiply(PLY), inward, "tnut")
    for label, (x, s) in panel_grid_v2.main_led_datums().items():
        name = f'main_{"lower" if s < no_shoes_frame.b.HALF else "upper"}_{"left" if x < no_shoes_frame.b.HALF else "right"}'
        point = no_shoes_frame.b.point(x - no_shoes_frame.b.HALF, s, -PLY)
        if label == "G2":
            point += cq.Vector(*parent["revision_report"]["led_move"]["translation_xyz_mm"])
        cut(name, "light_" + label, 13., point, screen.N, "light")
    for row in screws:
        point, direction = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        cut(row["panel"], row["axis_id"], 5., point, direction, "conditional_screw_clearance")
        panels[row["panel"]] = panels[row["panel"]].cut(
            cq.Solid.makeCone(4.5, 2.5, 3., point, direction)).clean()
    counts = Counter(row["kind"] for row in features)
    if counts != {"tnut": 142, "light": 132, "conditional_screw_clearance": 66}:
        raise ValueError("panel feature census differs")
    return panels, {"outlines": outline_records, "feature_counts": dict(counts), "features": features,
                    "limits": "World datums retained; analysis clearances and 3 mm head scenario are not drilling/countersink instructions. Only panels were reported cut; no holes were inspected."}


def recreate() -> tuple[dict, dict, list, list, list, list, dict]:
    frozen = source_layout()
    inputs = frozen["inputs"]
    raw, fitted, context, axes_source, _ = revision.row_layout(
        inputs["header_row_shift_mm"], inputs["bottom_extra_shift_mm"])
    axes = occupied.prepare_axes(raw, axes_source, context["inventory"], occupied.DEFAULT_SETTINGS)
    metal, washer_changes = revision.metal_with_washers(axes)
    expected = {r["id"]: r for r in frozen["installed_axes"]}
    for axis in axes:
        old = expected[axis["id"]]
        for key in ("grip_mm", "diameter_mm", "bore_diameter_mm", "before_plate_mm", "after_plate_mm",
                    "nominal_under_head_length_mm", "tip_projection_beyond_nut_mm"):
            if abs(axis[key] - old[key]) > 1e-6:
                raise ValueError(f"reconstructed stack differs: {axis['id']}/{key}")
        for key in ("point", "direction"):
            if (axis[key] - cq.Vector(*old[key])).Length > 1e-6:
                raise ValueError(f"reconstructed axis differs: {axis['id']}/{key}")
    services, authentication, wires, cutters = revision.routed_services(inputs["wire_depth_mm"])
    if wires != frozen["wire_proposals"] or washer_changes != frozen["small_washer_changes"]:
        raise ValueError("wire routing or restricted washer changes differ")
    before_bores = dict(raw)
    for name, _, _, cutter in variant(KERF_RIGHT).additional_machining_cutters():
        if name.endswith("_right"):
            cutter = cutter.translate((-3.175, 0, 0))
        before_bores[name] = before_bores[name].cut(cutter).clean()
    receivers = {name for name in raw if name.startswith(("base_", "lumber_leg_"))}
    before_bores, _ = service_tools.cut_services(before_bores, receivers, cutters)
    finished = occupied.bore_wood(before_bores, axes)
    screws = copy.deepcopy(frozen["screw_axes"])
    support = []
    for thickness, description in ((PLY, "preserved CAT 23/32 CAD"), (19.05, "owner nominal 3/4 comparison")):
        rows = []
        for row in screws:
            point, direction = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
            body = cq.Solid.makeCylinder(2.5, 63.5 - thickness, point + direction.multiply(thickness), direction)
            fraction = min(1., shared.overlaps(body, finished[row["receiver"]]) / body.Volume())
            rows.append({"axis_id": row["axis_id"], "receiver": row["receiver"], "fraction": fraction})
        support.append({"panel_thickness_mm": thickness, "basis": description,
                        "body_penetration_length_mm": 63.5 - thickness, "scenario_body_diameter_mm": 5.,
                        "full_receiver_bodies": sum(r["fraction"] >= .99999 for r in rows), "axes": rows})
    _, _, parent = shared.load_sources()
    panels, panel_record = machined_panels(raw, screws, parent)
    finished.update(panels)
    panel_services = revision.pair_hits(services, [(name, "panel", shape) for name, shape in panels.items()])
    if panel_services or any(r["full_receiver_bodies"] != 66 for r in support):
        raise ValueError("resolve full-penetration backing or panel/service collisions before exporting")
    evidence = {"layout_report_sha256": LAYOUT_SHA, "source_layout_reconstructed": True,
                "panel_screw_receiver_support": support, "panel_machining": panel_record,
                "panel_service_intersections": panel_services, "service_authentication": authentication,
                "machined_pilot_holes_in_receivers_displayed": False,
                "finished_stock": [{"name": name, "volume_mm3": shape.Volume(),
                                    "center_of_mass_xyz_mm": shared.xyz(shape.Center()),
                                    "cad_valid": shape.isValid(), "solid_count": len(shape.Solids())}
                                   for name, shape in sorted(finished.items())]}
    if len(receivers) != 20 or len(panels) != 6:
        raise ValueError("preserve twenty frame members and six panels")
    return frozen, finished, fitted, axes, metal, services, evidence


def scene_for(frozen: dict, wood: dict, fitted: list, axes: list, services: list) -> dict:
    solids, templates, template_keys = [], {}, {}

    def transform(plane: cq.Plane) -> list:
        return [*shared.xyz(plane.xDir), 0, *shared.xyz(plane.yDir), 0,
                *shared.xyz(plane.zDir), 0, *shared.xyz(plane.origin), 1]

    def add(name: str, shape: cq.Shape, kind: str, description: str,
            plane: cq.Plane | None = None, **metadata) -> None:
        mesh = shared._shape_mesh(shape)
        if plane:
            key = hashlib.sha256((mesh["vertices_base64"] + mesh["triangle_indices_base64"]).encode()).hexdigest()
            template = template_keys.setdefault(key, f"template_{len(template_keys) + 1:03d}")
            templates.setdefault(template, {"id": template, "mesh": mesh})
            geometry = {"template_id": template, "transform": transform(plane)}
        else:
            geometry = {"mesh": mesh}
        solids.append({"id": name, "name": name, **geometry,
                       "fabrication": {"kind": kind, "description": description,
                                       "clearance_status": "Conditional CAD review; resistance and access pending",
                                       **metadata}})

    for name, shape in sorted(wood.items()):
        panel = name.startswith(("main_", "kicker_"))
        add(name, shape, "panel" if panel else "timber",
            "Preserved panel outline and CAT 23/32 thickness; proposed openings" if panel else
            "Original section; proposed shallow front-open service channels and through-bolt bores; screw pilots omitted")
    for angle, fitting in fitted:
        plane = cq.Plane(origin=angle.origin, xDir=angle.u, normal=angle.w)
        add(angle.id, screen.template(fitting), "bracket",
            f"{fitting.model} conditional catalog geometry; unused factory holes remain; {angle.duty}",
            plane=plane, duty_id=angle.duty, catalog_model=fitting.model)
    for axis in axes:
        local_axis = dict(axis, point=cq.Vector(), direction=cq.Vector(0, 0, 1))
        local, _ = revision.metal_with_washers([local_axis])
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        for _, role, shape in local:
            add(f'{axis["id"]}_{role}', shape, "bolt", "Conditional hardware stack; actual grade, thread window and tool access unqualified",
                plane=plane, connection_name=axis["id"], hardware_role=role, stack_roles=ROLES)
    for row in frozen["screw_axes"]:
        local_row = {**row, "origin_xyz_mm": [0., 0., 0.], "direction_xyz": [0., 0., 1.]}
        shapes = [shape for _, shape in occupied.screw_shapes(local_row)]
        shape = shapes[0].fuse(shapes[1]).clean()
        add("fastener_" + row["axis_id"], shape, "screw",
            "66 purchased Hillman policy; owner 9 mm head; conditional 5 mm body / 3 mm head height; nominal 63.5 mm length",
            plane=cq.Plane(origin=row["origin_xyz_mm"], normal=row["direction_xyz"]),
            connection_name=row["axis_id"], panel_member=row["panel"], receiver_member=row["receiver"])
    for name, kind, shape in services:
        if kind == "wire":
            add(name, shape, "wire", "Proposed shallow route at retained endpoints; real slack, bend radii and harness removal unverified")
    topologies = shared._deduplicate_triangle_topologies(
        [row for row in solids if "mesh" in row] + list(templates.values()))
    counts = Counter(row["fabrication"]["kind"] for row in solids)
    if counts != {"timber": 20, "panel": 6, "bracket": 36, "bolt": 350, "screw": 66, "wire": 131}:
        raise ValueError("exported geometry census differs")
    retained = sorted(name for name, kind, _ in services if kind in {"light", "tnut"})
    return {"schema": "thin_bolted_review_scene/v1", "candidate": CANDIDATE, "revision": REVISION,
            "status": "REVISE_UNQUALIFIED_PROPOSAL",
            "parent_scene": {"url": "owner-wood-joints-wj24-scene.json",
                             "sha256": shared.SOURCE_PINS["site/owner-wood-joints-wj24-scene.json"]},
            "baseline_manifest_sha256": shared.sha(BASELINE),
            "layout_report": {"path": str(LAYOUT.relative_to(ROOT)), "sha256": LAYOUT_SHA},
            "retained_parent_service_names": retained,
            "counts": {**dict(counts), "physical_bolt_axes": 70, "new_bolt_axes": 58,
                       "retained_starting_bolt_axes": 12, "lights": 132, "tnuts": 142,
                       "total_visible_parts": 883},
            "solids": solids, "mesh_templates": templates, "triangle_topologies": topologies,
            "release": shared.RELEASE, "mechanics_ready": False,
            "design": {"key": "thin-bolted-development", "status": "REVISE_UNQUALIFIED_PROPOSAL",
                       "qualified_for_design": False,
                       "documents": [{"label": "Thin bolted goal, fit evidence and remaining work",
                                      "path": "docs/wood-joints-mvp/completion-ledger.md#hl35-replacement-candidate"},
                                     {"label": "Current development", "path": "docs/wood-joints-mvp/README.md"}]}}


def local_source_pins() -> dict:
    paths = {Path(__file__), ROOT / "uv.lock", BASELINE, LAYOUT}
    for module in list(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT / "mini_moonboard") or path.is_relative_to(ROOT / "scripts"):
                paths.add(path)
    return {str(path.relative_to(ROOT)): shared.sha(path) for path in sorted(paths)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, default=SCENE)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    args = parser.parse_args()
    if any(path.exists() for path in (args.scene, args.evidence, args.contract)):
        raise FileExistsError("preserve existing model outputs; use separate paths for a replay")
    print("Reconstructing frozen v4 and checking complete CAT 23/32 penetration", flush=True)
    frozen, wood, fitted, axes, metal, services, evidence = recreate()
    print("Encoding changed bodies; retained lights/T-nuts use shared source assets", flush=True)
    scene = scene_for(frozen, wood, fitted, axes, services)
    args.scene.parent.mkdir(parents=True, exist_ok=True)
    args.scene.write_text(json.dumps(scene, indent=2, allow_nan=False) + "\n")
    evidence.update({"schema": "thin_bolted_review_model_evidence/v1", "candidate": CANDIDATE,
                     "revision": REVISION, "source_sha256": {**frozen["source_sha256"], **local_source_pins()},
                     "environment": {"python": sys.version.split()[0], "cadquery": cq.__version__},
                     "command": ".venv/bin/python -m scripts.thin_bolted_model",
                     "outputs": {str(args.scene.relative_to(ROOT)): {"sha256": shared.sha(args.scene),
                                                                    "bytes": args.scene.stat().st_size}},
                     "counts": scene["counts"], "release": shared.RELEASE, "mechanics_ready": False,
                     "mass_components": {
                         "frame_timber_kg_at_500_kg_m3": sum(s.Volume() for n, s in wood.items()
                                                            if n.startswith(("base_", "lumber_leg_"))) * 500e-9,
                         "panels_kg_at_500_kg_m3": sum(s.Volume() for n, s in wood.items()
                                                      if n.startswith(("main_", "kicker_"))) * 500e-9,
                         "conditional_bolt_metal_kg_at_7850_kg_m3": sum(s.Volume() for _, _, s in metal) * 7850e-9,
                         "catalog_fittings_lb": 25.44,
                         "excluded": "Hillman screws, holds/hold bolts, T-nuts, LEDs, wires, pads and accessories; densities and hardware envelopes are planning assumptions."},
                     "limits": ["Nominal geometry review only; catalog discrepancies and tolerances remain unresolved.",
                                "Tool corridors, disassembly, lower panel-edge transfer, complete joint behavior and resistance remain open.",
                                "No native solve, inherited capacity, actual inspection or physical release."]})
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    contract = {"schema": "thin_bolted_development_candidate/v1", "candidate": CANDIDATE, "revision": REVISION,
                "status": scene["status"], "selected": False, "release": shared.RELEASE,
                "load_basis": {"climber_weight_lb": 250, "downward_multiplier": 2,
                               "horizontal_force_N": 300, "hold_lever_mm": 100,
                               "floor_no_slip_assumed": True, "floor_no_slip_verified": False},
                "viewer": {"query": "thin-bolted-development", "scene": str(args.scene.relative_to(ROOT)),
                           "sha256": shared.sha(args.scene), "counts": scene["counts"]},
                "evidence": {"path": str(args.evidence.relative_to(ROOT)), "sha256": shared.sha(args.evidence)},
                "preserved_authorities_sha256": {p: shared.SOURCE_PINS[p]
                                                  for p in ("current-candidate.json", "wood-joints-candidate.json")},
                "remaining": evidence["limits"]}
    args.contract.write_text(json.dumps(contract, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"scene": str(args.scene), "scene_bytes": args.scene.stat().st_size,
                      "scene_sha256": shared.sha(args.scene), "counts": scene["counts"],
                      "full_receiver_bodies": [r["full_receiver_bodies"] for r in evidence["panel_screw_receiver_support"]],
                      "mass_components": evidence["mass_components"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
