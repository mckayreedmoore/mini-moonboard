"""Export a distinct eoere/cleat review model from the preserved thin-frame inputs.

Only cached raw stock is reused for changed timbers. Reapply the authenticated
recess/service recipe and bore the new finite stacks; preserve all 66 screws.
Unchanged panel and service meshes are shared through the frozen predecessor.
This is nominal geometry, not a mechanics response or fabrication release.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import eoere_bolted_candidate as raw_method
from scripts import hl35_candidate as shared
from scripts import hl35_full_fit_candidate as geometry_tools
from scripts import hl35_nominal_service_candidate as service_tools
from scripts import thin_bolted_layout_revision as services_method
from scripts import thin_bolted_model as predecessor
from scripts import thin_bolted_occupied as hardware_method

ROOT = shared.ROOT
PACKET = raw_method.PACKET / "eoere-successor-v1"
CACHE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/occupied-geometry-v1"
REVISION = "eoere-far-pairs-cleat-corners-v1"
CANDIDATE = "compact-floor-flush-eoere-bolted-development"
ROLES = ["shaft", "head", "head_washer", "nut_washer", "nut"]
REMOVED = {"clip_timber_header_outer_left", "clip_timber_header_outer_right"}
SOURCE_SCENE = ROOT / "site/thin-bolted-scene.json.gz"
SOURCE_SCENE_SHA = "2ec1dd37dcd867e1748abe4eeb7567e1f62347802964d14bfcb09dd1329e17dc"
DECODED_SHA = "ec9bac9be2091aa76c24f4df305c020c69f890a11aa3de93e920e18b209c6c70"
HARDWARE = {"washer_od_mm": 26.162, "washer_id_mm": 11.1125,
            "washer_thickness_mm": 2.6416, "head_height_mm": 6.,
            "nut_height_mm": 8.5598, "hex_across_flats_mm": 14.2875,
            "available_nominal_lengths_mm": [63.5, 76.2, 101.6, 114.3, 127., 152.4, 165.1],
            "minimum_tip_threads": 2, "threads_per_inch": 16}


def bounds(shape: cq.Shape) -> list:
    box = shape.BoundingBox()
    return [[getattr(box, a + "min"), getattr(box, a + "max")] for a in "xyz"]


def interval_components(rows: list[dict], tolerance: float = 1e-5) -> list[list[dict]]:
    """Collinear finite intervals merge only when they overlap or touch."""
    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("finite nonnegative interval tolerance required")
    groups, endpoint = [], -math.inf
    for row in sorted(rows, key=lambda r: (r["interval_mm"][0], r["interval_mm"][1])):
        lo, hi = row["interval_mm"]
        if not all(math.isfinite(v) for v in (lo, hi)) or lo >= hi:
            raise ValueError("finite ordered positive-length intervals required")
        if lo > endpoint + tolerance:
            groups.append([])
        groups[-1].append(row)
        endpoint = max(endpoint, hi)
    return groups


def connected_receivers(wood: dict, point: cq.Vector, direction: cq.Vector,
                        primary: str) -> tuple[list[str], float, float]:
    """Extend a starting raw receiver only through contiguous occupied stock."""
    intervals = []
    for name, body in wood.items():
        try:
            near, far = geometry_tools.line_span(body, point, direction)
        except ValueError:
            continue
        intervals.append({"member": name, "interval_mm": [near, far]})
    for group in interval_components(intervals):
        if any(row["member"] == primary for row in group):
            return ([row["member"] for row in group],
                    min(row["interval_mm"][0] for row in group),
                    max(row["interval_mm"][1] for row in group))
    raise ValueError(f"axis misses its primary raw receiver: {primary}")


def prepare_axes(wood: dict, angles: list, scenario: raw_method.Scenario,
                 old_axes: list[dict]) -> tuple[list, list]:
    ports, lines = [], {}
    for angle in angles:
        for hole in scenario.holes(active_only=True):
            flange = hole["flange"]
            along, inward, receiver = ((angle.u, -angle.v, angle.beam) if flange == "beam"
                                       else (angle.v, -angle.u, angle.post))
            point = angle.origin + along * hole["along_mm"] + angle.w * hole["transverse_mm"]
            names, near, far = connected_receivers(wood, point, inward, receiver)
            canonical = inward.normalized()
            if next(v for v in canonical.toTuple() if abs(v) > 1e-8) < 0:
                canonical *= -1
            endpoints = sorted([(point + inward * near).dot(canonical),
                                (point + inward * far).dot(canonical)])
            port = {**hole, "angle_id": angle.id, "duty_id": angle.duty,
                    "receiver": receiver, "point": point, "direction": inward,
                    "receivers": names, "interval_mm": endpoints}
            ports.append(port)
            lines.setdefault(raw_method.line_key(point, inward), []).append(port)
    axes = []
    for rows in lines.values():
        for group in interval_components(rows):
            first = group[0]
            point, direction = first["point"], first["direction"]
            names, near, far = connected_receivers(wood, point, direction, first["receiver"])
            point += direction * near
            before, after = 0., 0.
            for port in group:
                distance = (port["point"] - point).dot(direction)
                if abs(distance) < 1e-5:
                    before = scenario.thickness_mm
                elif abs(distance - (far - near)) < 1e-5:
                    after = scenario.thickness_mm
                else:
                    raise ValueError("fitting is not at an external raw stack face")
            identity = f"eoere_bolt_{len(axes) + 1:03d}"
            for port in group:
                port["installed_bolt_axis_id"] = identity
            axes.append({"id": identity, "point": point, "direction": direction,
                         "receivers": names, "grip_mm": far - near,
                         "diameter_mm": scenario.bolt_mm, "bore_diameter_mm": scenario.wood_bore_mm,
                         "before_plate_mm": before, "after_plate_mm": after,
                         "attachments": group, "source": "eoere_far_pair",
                         "hardware_scenario": copy.deepcopy(HARDWARE)})
    if len(axes) != 84 or len(ports) != 88:
        raise ValueError(f"expected 84 angle stacks/88 ports, observed {len(axes)}/{len(ports)}")
    for side in ("left", "right"):
        for number, y in enumerate((-131.25, -80.45), 1):
            point = cq.Vector(-1257.3 if side == "left" else 1254.125, y, 189.3)
            direction = cq.Vector(1 if side == "left" else -1, 0, 0)
            names, near, far = connected_receivers(wood, point, direction, f"eoere_cleat_{side}")
            if set(names) != {f"eoere_cleat_{side}", f"base_post_outer_{side}"}:
                raise ValueError("cleat/post attachment has unexpected receiver ownership")
            axes.append({"id": f"cleat_post_bolt_{side}_{number}", "point": point + direction * near,
                         "direction": direction, "receivers": names, "grip_mm": far - near,
                         "diameter_mm": scenario.bolt_mm, "bore_diameter_mm": scenario.wood_bore_mm,
                         "before_plate_mm": 0., "after_plate_mm": 0., "attachments": [],
                         "source": "cleat_post_through_bolt", "hardware_scenario": copy.deepcopy(HARDWARE)})
    for old in old_axes:
        if old["source"] == "new_factory_fitting_axis":
            continue
        axis = copy.deepcopy(old)
        axis["point"], axis["direction"] = cq.Vector(*axis["point"]), cq.Vector(*axis["direction"])
        axes.append(axis)
    if len(axes) != 100 or len({a["id"] for a in axes}) != 100:
        raise ValueError("one hundred finite physical stacks required")
    return axes, ports


def serial_axis(axis: dict) -> dict:
    result = {key: value for key, value in axis.items() if key not in ("point", "direction", "attachments")}
    result.update({"point_xyz_mm": shared.xyz(axis["point"]), "direction_xyz": shared.xyz(axis["direction"]),
                   "attachments": [{key: shared.xyz(value) if isinstance(value, cq.Vector) else value
                                    for key, value in port.items()} for port in axis.get("attachments", [])],
                   "delivered_part_or_thread_window_verified": False})
    return result


def build(cache: Path, main_depth_shift_mm: float = 0.) -> tuple[dict, dict]:
    if not math.isfinite(main_depth_shift_mm):
        raise ValueError("finite main-angle depth offset required")
    if shared.sha(raw_method.MANIFEST) != raw_method.MANIFEST_SHA:
        raise ValueError("cached geometry manifest differs")
    manifest = json.loads(raw_method.MANIFEST.read_bytes())
    frozen = predecessor.source_layout()
    stations = json.loads(raw_method.STATIONS.read_bytes())
    product = PACKET / "product-inputs-final.json"
    if shared.sha(product) != "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309":
        raise ValueError("reviewed eoere product input bytes differ")
    pins = {**manifest["source_sha256"], **predecessor.local_source_pins(),
            str(raw_method.STATIONS.relative_to(ROOT)): shared.sha(raw_method.STATIONS),
            str(raw_method.MANIFEST.relative_to(ROOT)): raw_method.MANIFEST_SHA,
            str(product.relative_to(ROOT)): shared.sha(product),
            str(Path(__file__).relative_to(ROOT)): shared.sha(Path(__file__))}

    def load(row):
        path = ROOT / row["path"]
        if shared.sha(path) != row["sha256"]:
            raise ValueError(f"changed source BREP: {path}")
        pins[row["path"]] = row["sha256"]
        shape = cq.Shape.importBrep(str(path))
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"invalid cached single solid: {path}")
        return shape

    print("Importing twenty source-bound raw timbers; adding two individual cleats", flush=True)
    wood = {row["member"]: load(row) for row in manifest["raw_parts"]}
    for side, x in (("left", -1257.3), ("right", 1216.025)):
        wood[f"eoere_cleat_{side}"] = cq.Solid.makeBox(38.1, 139.7, 289.7, cq.Vector(x, -175.7, 139.7))
    raw_volumes = {name: shape.Volume() for name, shape in wood.items()}
    for name, _, _, cutter in variant(KERF_RIGHT).additional_machining_cutters():
        if name.endswith("_right"):
            cutter = cutter.translate((-3.175, 0, 0))
        wood[name] = wood[name].cut(cutter).clean()
    scenario = raw_method.Scenario()
    local_angle = raw_method.template(scenario)
    poses = [*stations["main_stations"], *stations["remaining_base_header_starting_stations"]]
    poses = [copy.deepcopy(row) for row in poses if row["duty_id"] not in REMOVED]
    changes = []
    for row in poses:
        if row in stations["main_stations"] and main_depth_shift_mm:
            delta = cq.Vector(0, -math.cos(math.radians(40)), math.sin(math.radians(40))) * main_depth_shift_mm
            before = list(row["origin_xyz_mm"])
            row["origin_xyz_mm"] = shared.xyz(cq.Vector(*before) + delta)
            changes.append({"duty_id": row["duty_id"], "origin_before_xyz_mm": before,
                            "origin_after_xyz_mm": row["origin_xyz_mm"],
                            "reason": "explicit main-angle depth-offset study at preserved planes"})
        if row["duty_id"].startswith("clip_angle_base_"):
            before = row["origin_xyz_mm"][1]
            row["origin_xyz_mm"][1] = -105.85
            changes.append({"duty_id": row["duty_id"], "origin_y_before_mm": before,
                            "origin_y_after_mm": -105.85, "reason": "center the transverse far pair on receiving stock"})
    angles = [raw_method.pose(row, local_angle) for row in poses]
    axes, ports = prepare_axes(wood, angles, scenario, frozen["installed_axes"])
    print("Reusing the authenticated shallow service/recess recipe before new bores", flush=True)
    services, _auth, routes, cutters = services_method.routed_services(frozen["inputs"]["wire_depth_mm"])
    if routes != frozen["wire_proposals"]:
        raise ValueError("reused wire endpoint/route recipe differs")
    wood, service_cuts = service_tools.cut_services(wood, set(wood), cutters)
    metal = hardware_method.hardware(axes)
    bore_support = []
    for axis in axes:
        for name in axis["receivers"]:
            near, far = geometry_tools.line_span(wood[name], axis["point"], axis["direction"])
            cylinder = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2, far - near,
                                             axis["point"] + axis["direction"] * near, axis["direction"])
            bore_support.append({"axis_id": axis["id"], "receiver": name,
                                 "pre_bore_full_body_fraction": min(1., shared.overlaps(cylinder, wood[name]) / cylinder.Volume())})
    finished = hardware_method.bore_wood(wood, axes)
    panels = {row["id"]: load(row) for row in manifest["parts"] if row["kind"] == "panel"}
    screws = [(row["axis_id"], hardware_method.screw_shapes(row)) for row in frozen["screw_axes"]]
    screw_support = []
    for thickness in (predecessor.PLY, 19.05):
        for row in frozen["screw_axes"]:
            p, d = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
            body = cq.Solid.makeCylinder(2.5, 63.5 - thickness, p + d * thickness, d)
            screw_support.append({"axis_id": row["axis_id"], "receiver": row["receiver"],
                                  "panel_thickness_mm": thickness,
                                  "body_fraction": min(1., shared.overlaps(body, finished[row["receiver"]]) / body.Volume())})
    print("Checking complete hardware, panel screws, retained services and changed receivers", flush=True)
    bodies = [(name, "timber", shape) for name, shape in finished.items()]
    bodies.extend((name, "panel", shape) for name, shape in panels.items())
    metals = [(axis, role, shape) for axis, role, shape in metal]
    metals.extend((angle.id, "bracket", angle.shape) for angle in angles)
    metal_pairs = geometry_tools.collision_pairs(metals)
    metal_wood = services_method.pair_hits(metals, bodies)
    screw_parts = [(identity, "screw_" + role, shape) for identity, roles in screws for role, shape in roles]
    metal_screws = services_method.pair_hits(metals, screw_parts)
    service_metal = services_method.pair_hits(services, metals)
    timber_pairs = geometry_tools.collision_pairs(bodies)
    shared_bytes = SOURCE_SCENE.read_bytes()
    if shared.sha(SOURCE_SCENE) != SOURCE_SCENE_SHA:
        raise ValueError("frozen source scene differs")
    source = json.loads(gzip.decompress(shared_bytes))
    if hashlib.sha256(gzip.decompress(shared_bytes)).hexdigest() != DECODED_SHA:
        raise ValueError("decoded frozen source scene differs")
    inherited = sorted(row["name"] for row in source["solids"]
                       if row["fabrication"]["kind"] in {"panel", "screw", "wire"})
    inherited += source["retained_parent_service_names"]
    if len(inherited) != 477 or len(set(inherited)) != 477:
        raise ValueError("477 unchanged panel/screw/service meshes required")
    sourcepins = {**pins, str(SOURCE_SCENE.relative_to(ROOT)): SOURCE_SCENE_SHA}
    for path, digest in sourcepins.items():
        if shared.sha(ROOT / path) != digest:
            raise ValueError(f"input changed during geometry run: {path}")
    saved_bodies = []
    for name, shape in sorted(finished.items()):
        path = cache / (name + ".brep")
        if not shape.isValid() or len(shape.Solids()) != 1 or not shape.exportBrep(str(path)):
            raise ValueError(f"cannot retain finished one-solid geometry: {name}")
        saved_bodies.append({"id": name, "path": str(path.relative_to(ROOT)), "sha256": shared.sha(path),
                             "bytes": path.stat().st_size, "volume_mm3": shape.Volume(),
                             "bounds_xyz_mm": bounds(shape)})
    report = {"schema": "eoere_bolted_occupied_geometry/v1", "candidate": CANDIDATE,
              "revision": REVISION, "status": "REVISE_UNQUALIFIED_PROPOSAL",
              "source_sha256": sourcepins, "scenario": {**vars(scenario), "hardware": HARDWARE},
              "inputs": {"main_depth_shift_mm": main_depth_shift_mm}, "finished_solids": saved_bodies,
              "changes": {"added_cleats": ["eoere_cleat_left", "eoere_cleat_right"],
                          "removed_lower_angles": sorted(REMOVED), "centered_inside_angles": changes,
                          "existing_stock_sections_changed": False, "Hillman_axes_moved": [],
                          "inside_alignment_blocks": 0, "original_frame_bolts_rechecked": 12},
              "axes": [serial_axis(axis) for axis in axes], "bore_support": bore_support,
              "screw_support": screw_support, "service_cuts": service_cuts,
              "collisions": {"metal_metal": metal_pairs, "metal_wood": metal_wood,
                             "metal_screws": metal_screws, "service_metal": service_metal,
                             "timber_panel": timber_pairs},
              "mass": {"raw_frame_kg_at_500_kg_m3": sum(raw_volumes.values()) * 500e-9,
                       "finished_frame_kg_at_500_kg_m3": sum(s.Volume() for s in finished.values()) * 500e-9,
                       "angle_drawing_mass_kg": 22 * 1.46 * .45359237},
              "counts": {"timber": 22, "panel": 6, "bracket": 22, "bolt": 500, "screw": 66,
                         "wire": 131, "physical_bolt_axes": 100, "new_bolt_axes": 88,
                         "retained_starting_bolt_axes": 12, "lights": 132, "tnuts": 142,
                         "total_visible_parts": 1021, "owned_scene_solids": 544,
                         "angle_stacks": 84, "cleat_post_stacks": 4, "factory_holes": 176,
                         "installed_factory_holes": 88, "starting_duties_accounted": 24},
              "release": shared.RELEASE, "mechanics_ready": False,
              "limits": ["Unmeasured nominal product heel offsets, sharp bend and representative head/nut shapes remain scenarios.",
                         "All 66 screw axes and panel geometry are inherited unchanged; their physical dimensions were not inspected.",
                         "Partial backing/collisions are reported; tools, delivered thread/shank, strength and floor remain unqualified.",
                         "Removed lower angle duties use a new upper-angle/side/cleat/post tie path and header/post bearing.",
                         "This geometry does not consume forces or qualify a complete joint; no fabrication or climbing release."]}
    scene = scene_for(report, finished, angles, axes, ports, inherited, source, local_angle)
    return report, scene


def scene_for(report, wood, angles, axes, ports, inherited, source, local_angle):
    solids, templates, keys = [], {}, {}

    def add(name, body, kind, description, plane=None, **metadata):
        mesh = shared._shape_mesh(body)
        if plane is None:
            geometry = {"mesh": mesh}
        else:
            digest = hashlib.sha256((mesh["vertices_base64"] + mesh["triangle_indices_base64"]).encode()).hexdigest()
            identity = keys.setdefault(digest, f"template_{len(keys) + 1:03d}")
            templates.setdefault(identity, {"id": identity, "mesh": mesh})
            transform = [*shared.xyz(plane.xDir), 0, *shared.xyz(plane.yDir), 0,
                         *shared.xyz(plane.zDir), 0, *shared.xyz(plane.origin), 1]
            geometry = {"template_id": identity, "transform": transform}
        solids.append({"id": name, "name": name, **geometry,
                       "fabrication": {"kind": kind, "description": description, **metadata}})

    for name, body in sorted(wood.items()):
        add(name, body, "timber", "Nominal raw section, retained service cuts and new through-bolt openings; screw pilots omitted")
    for angle in angles:
        add(angle.id, local_angle, "bracket", "eoere inch-drawing scenario; all eight holes retained, four far holes occupied",
            cq.Plane(origin=angle.origin, xDir=angle.u, normal=angle.w), duty_id=angle.duty,
            catalog_model="B0C7V7VS89")
    for axis in axes:
        local_axis = dict(axis, point=cq.Vector(), direction=cq.Vector(0, 0, 1))
        for role, shape in hardware_method.local_hardware(local_axis):
            add(axis["id"] + "_" + role, shape, "bolt", "Nominal complete stack; delivered shank/thread/grade unverified",
                cq.Plane(origin=axis["point"], normal=axis["direction"]), connection_name=axis["id"],
                hardware_role=role, stack_roles=ROLES)
    topologies = shared._deduplicate_triangle_topologies(
        [row for row in solids if "mesh" in row] + list(templates.values()))
    factory = []
    scenario = raw_method.Scenario()
    bindings = {(p["angle_id"], p["flange"], p["row"], p["transverse"]): p["installed_bolt_axis_id"] for p in ports}
    for angle in angles:
        holes = []
        for hole in scenario.holes():
            u, v = ((hole["along_mm"], scenario.thickness_mm / 2) if hole["flange"] == "beam"
                    else (scenario.thickness_mm / 2, hole["along_mm"]))
            direction = -angle.v if hole["flange"] == "beam" else -angle.u
            key = (angle.id, hole["flange"], hole["row"], hole["transverse"])
            holes.append({"id": ".".join(map(str, key)), "flange": hole["flange"], "row": hole["row"],
                          "transverse": hole["transverse"],
                          "point_xyz_mm": shared.xyz(angle.point(u, v, hole["transverse_mm"])),
                          "direction_xyz": shared.xyz(direction), "installed_bolt_axis_id": bindings.get(key)})
        factory.append({"angle_id": angle.id, "holes": holes})
    if len(solids) != 544 or Counter(r["fabrication"]["kind"] for r in solids) != {"timber": 22, "bracket": 22, "bolt": 500}:
        raise ValueError("owned scene geometry census differs")
    return {"schema": "eoere_bolted_review_scene/v1", "candidate": CANDIDATE, "revision": REVISION,
            "status": report["status"], "counts": report["counts"],
            "shared_scene": {"url": SOURCE_SCENE.name, "sha256": SOURCE_SCENE_SHA, "decoded_sha256": DECODED_SHA},
            "retained_shared_part_names": sorted(inherited),
            "retained_parent_service_names": source["retained_parent_service_names"],
            "baseline_manifest_sha256": source["baseline_manifest_sha256"],
            "layout_report": {"path": str((PACKET / "occupied-geometry-v1.json").relative_to(ROOT)), "sha256": None},
            "solids": solids, "mesh_templates": templates, "triangle_topologies": topologies,
            "factory_angle_holes": factory, "release": shared.RELEASE, "mechanics_ready": False,
            "design": {"key": "eoere-bolted-development", "status": report["status"], "qualified_for_design": False,
                       "documents": [{"label": "Eoere geometry and numerical MVP", "path": "docs/wood-joints-mvp/README.md"},
                                     {"label": "Current joint evidence", "path": "docs/wood-joints-mvp/completion-ledger.md#build-package-completion"}]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CACHE)
    parser.add_argument("--main-depth-shift", type=float, default=0.)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior geometry attempt; choose a distinct output")
    args.output.mkdir(parents=True)
    report, scene = build(args.output, args.main_depth_shift)
    report_path = args.output / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    scene["layout_report"]["sha256"] = shared.sha(report_path)
    scene_path = args.output / "scene.json"
    scene_path.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    (args.output / "scene.json.gz").write_bytes(gzip.compress(scene_path.read_bytes(), compresslevel=9, mtime=0))
    print(json.dumps({"output": str(args.output), "counts": report["counts"],
                      "collision_counts": {k: len(v) for k, v in report["collisions"].items()},
                      "layout_sha256": shared.sha(report_path), "scene_sha256": shared.sha(scene_path)}, indent=2))


if __name__ == "__main__":
    main()
