"""Refine selected-stack access with cached solids and explicit generic tools.

No frame rebuild, native solve or physical observation. Keep every failed
nominal query. Source bounds reject remote objects before exact solid queries.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
from collections import Counter
from pathlib import Path

from scripts.eoere_current_shop_followup import module
from scripts.eoere_selected_hardware import DOC, ROOT, canonical, encoded, require, sha

BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
SHOP = DOC / "shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1"


def removal_interval(seat, part_length, bolt_tip):
    """Enclose a rigid part until its near face reaches the bolt tip."""
    require(all(math.isfinite(value) for value in (seat, part_length, bolt_tip)) and
            part_length > 0 and bolt_tip > seat, "positive hardware removal travel required")
    return seat, bolt_tip + part_length


def removal_envelopes(axis, selection, side):
    """Production cylinders as (operation, axial start, length, radius)."""
    h, travel = axis["hardware_scenario"], selection["selected_underhead_length_mm"]
    underhead = -axis["before_plate_mm"] - h["washer_thickness_mm"]
    hex_radius = h["hex_across_flats_mm"] / math.sqrt(3)
    if side == "head":
        return [("full_shaft_withdrawal", underhead - travel, travel * 2, axis["diameter_mm"] / 2),
                ("head_withdrawal", underhead - travel - h["head_height_mm"], travel + h["head_height_mm"], hex_radius)]
    require(side == "nut", "head or nut side required")
    spacer = selection["nut_side_spacer_mm"]
    near = axis["grip_mm"] + axis["after_plate_mm"] + h["washer_thickness_mm"] + spacer
    start, end = removal_interval(near, h["nut_height_mm"], travel + underhead)
    result = [("nut_removal", start, end - start, hex_radius)]
    if spacer:
        start, end = removal_interval(near - spacer, spacer, travel + underhead)
        result.append(("spacer_removal", start, end - start, 19.05 / 2))
    return result


def selected_setup_requirements(checks):
    minimum_z = min(row["bounds_xyz_mm"][4] for row in checks)
    return {"minimum_selected_operation_z_mm": minimum_z,
            "off_floor_setup_required": minimum_z < 0,
            "minimum_additional_reference_floor_clearance_mm": max(0, -minimum_z),
            "actual_temporary_support_verified": False}


def envelope_intrusions(body, bank, resolve_shape, axis_name, stage=False, excluded=()):
    """Use the production bounds filter and exact intersections for one envelope."""
    bb = body.BoundingBox()
    box = [getattr(bb, axis + end) for axis in "xyz" for end in ("min", "max")]
    ignored = {axis_name + "_" + role for role in ["shaft", "head", "head_washer", "nut_washer", "nut", "spacer"]}
    ignored.update(excluded)
    candidates = [name for name, row in bank.items() if name not in ignored and
                  (not stage or row["kind"] in ("timber", "bracket", "bolt", "selected_spacer")) and
                  all(box[i] <= row["bounds"][i + 1] + 1e-5 and row["bounds"][i] <= box[i + 1] + 1e-5
                      for i in (0, 2, 4))]
    collisions, refined = [], []
    for name in candidates:
        volume = body.intersect(resolve_shape(name)).Volume()
        refined.append({"part": name, "intersection_mm3": volume})
        if volume > 1e-4:
            collisions.append(name)
    return {"bounds_xyz_mm": box, "fine_queries": refined, "nominal_intrusions": collisions,
            "reference_envelope_clear": not collisions, "off_floor_setup_required": box[4] < 0}


def swept_handle_polygon(degrees=60):
    """Convex outer bound for a rectangular handle's continuous planar turn.

    Sample each corner every two degrees. Circumscribed octagons cover the
    maximum intervening circular-arc sagitta, so the hull encloses the sweep.
    """
    steps = math.ceil(degrees / 2)
    step = math.radians(degrees / steps)
    corners = [(x, y) for x in (9.525, 161.925) for y in (-9.525, 9.525)]
    sagitta = max(math.hypot(*p) for p in corners) * (1 - math.cos(step / 2)) + 1e-6
    padding = sagitta / math.cos(math.pi / 8)
    points = []
    for i in range(steps + 1):
        a = math.radians(-degrees / 2) + i * step
        for x, y in corners:
            u, v = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            for j in range(8):
                b = j * math.pi / 4
                points.append((u + padding * math.cos(b), v + padding * math.sin(b)))
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    lower, upper = [], []
    for chain, sequence in ((lower, points), (upper, reversed(points))):
        for p in sequence:
            while len(chain) > 1 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
    return lower[:-1] + upper[:-1]


def wrench_envelopes(point, outward, thickness, entry, radius):
    """Production static handle, continuous turn and full axial entry solids."""
    import cadquery as cq

    p, direction = cq.Vector(*point), cq.Vector(*outward)
    center = p + direction * thickness / 2
    plane = cq.Plane(origin=center, normal=outward)
    handle = cq.Workplane(plane).center(85.725, 0).rect(152.4, 19.05).extrude(thickness / 2, both=True).val()
    sweep = cq.Workplane(plane).polyline(swept_handle_polygon()).close().extrude(thickness / 2, both=True).val()
    sweep = sweep.fuse(cq.Solid.makeCylinder(radius, thickness, p, direction)).clean()
    insertion_plane = cq.Plane(origin=p, normal=outward)
    insertion = cq.Workplane(insertion_plane).center(85.725, 0).rect(152.4, 19.05).extrude(entry + thickness).val()
    insertion = insertion.fuse(cq.Solid.makeCylinder(radius, entry + thickness, p, direction)).clean()
    result = {"static_counterhold": handle, "working_handle_60deg": sweep,
              "complete_wrench_axial_insertion": insertion}
    require(all(body.isValid() and len(body.Solids()) == 1 for body in result.values()),
            "wrench envelopes must each be one valid solid")
    return result


def build(out):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT / BASE / "selected-hardware-v1"),
            "run at root with ignored selected-hardware output")
    require(not out.exists(), "preserve earlier attempts")
    layout_path = DOC / "occupied-selected-hardware-v1.json"
    layout = json.loads(layout_path.read_bytes())
    pins = json.loads(Path(layout["source_map"]["path"]).read_bytes())
    require(sha(layout["source_map"]["path"]) == layout["source_map"]["sha256"],
            "authenticated hardware source map required")
    pins[str(layout_path)] = sha(layout_path)
    pins[str(Path(__file__).relative_to(ROOT))] = sha(__file__)

    def pin(path, expected=None):
        path = str(path)
        observed = sha(path)
        require(expected is None or expected == observed, "source changed: " + path)
        require(path not in pins or pins[path] == observed, "conflicting source: " + path)
        pins[path] = observed
        return Path(path)

    def read(path):
        return json.loads(pin(path).read_bytes())

    def asset(name):
        raw = pin("site/" + name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)

    def verify():
        for name, digest in pins.items():
            require(sha(name) == digest, "source drift: " + name)

    verify()
    source = read(layout["retained_axis_geometry"]["path"])
    axes = {row["id"]: row for row in source["axes"]}
    selected = {row["axis_id"]: row for row in layout["selected_stacks"]}
    native = read(DOC.parent / "native-geometry-v4.json")
    shop_inputs = read(SHOP / "inputs.json")
    method_path = shop_inputs["sources"]["bounds_helper"]["path"]
    pin(method_path, shop_inputs["sources"]["bounds_helper"]["sha256"])
    bounds_method = module(method_path, "selected_access_bounds")
    common = [asset(n) for n in ["eoere-bottom-rail-scene.json.gz",
              "eoere-cleat-trim-scene.json", "eoere-aligned-wire-scene.json.gz",
              "eoere-adjusted-base-v3-scene.json.gz", "eoere-cleat-extension-scene.json.gz"]]
    channels = asset("eoere-uniform-channels-scene.json.gz")
    right_patch = asset("eoere-right-column-scene.json.gz")
    off = bounds_method.compose_bounds(native, [*common,
        {"replacements": channels["common_replacements"] + channels["base_replacements"]}])
    on = bounds_method.compose_bounds(native, [*common, asset("eoere-2026-adjustments-v3-scene.json.gz"),
        {"replacements": channels["common_replacements"] + channels["extra_replacements"]}, right_patch])
    for bank in (off, on):
        for row in source["changed_finished_solids"] + layout["changed_finished_solids"]:
            bank[row["id"]] = {"kind": row["kind"], "bounds": row["bounds_xyz_mm"]}
    require(len(off) == 1029 and len(on) == 1424, "complete two-variant bounds banks required")
    record_layers = [read(DOC / n) for n in ["occupied-bottom-rail-v1.json", "occupied-cleat-trim-v1.json",
        "occupied-aligned-wire-v1.json", "occupied-adjusted-base-v3.json", "occupied-extended-cleats-v1.json",
        "occupied-uniform-channels-v1.json", "occupied-kicker-clearance-v1.json"]]
    records = {row["id"]: row for row in native["parts"]}
    for layer in record_layers:
        for key in ["finished_solids", "finished_panel_solids", "unchanged_finished_solids", "changed_finished_solids"]:
            for row in layer.get(key, []):
                if row.get("variant", "base") in ("common", "base"):
                    records[row["id"]] = row
    manifest_path = ROOT.parent / "mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json"
    for row in read(manifest_path)["files"]:
        if "/aligned-wire-cutouts-v1/cad-v1/wire_" in row["path"] and row["path"].endswith(".brep"):
            records[Path(row["path"]).stem] = row
    for row in layout["changed_finished_solids"]:
        records[row["id"]] = row
    extra_records = dict(records)
    extra = read(DOC / "occupied-2026-adjustments-v3.json")
    for layer in [extra, record_layers[5], read(DOC / "occupied-right-column-v1.json")]:
        for row in layer["changed_finished_solids"]:
            if row.get("variant", "extra") in ("common", "extra"):
                extra_records[row["id"]] = row
    for row in source["changed_finished_solids"] + layout["changed_finished_solids"]:
        extra_records[row["id"]] = row
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(Path(__file__).read_bytes())
    print("Authenticated both variants; refining finite tool and removal corridors", flush=True)

    import cadquery as cq

    from scripts import eoere_bolted_candidate as fitting
    from scripts import thin_bolted_occupied as hardware

    cache, metal_cache = {}, {}
    bracket_rows = {r["name"]: r for r in common[0]["solids"] if r["fabrication"]["kind"] == "bracket"}
    bracket_template = fitting.template(fitting.Scenario())
    initial_brackets = {row["id"]: row for row in record_layers[3]["changed_finished_solids"]
                        if row["kind"] == "bracket"}
    for name, row in initial_brackets.items():
        records[name] = extra_records[name] = row
    for method in ["scripts/eoere_bolted_candidate.py", "scripts/thin_bolted_occupied.py",
                   "scripts/eoere_current_shop_followup.py", "scripts/eoere_selected_hardware.py"]:
        pin(method)

    def shape(name, variant="base"):
        key = (variant, name)
        if key in cache:
            return cache[key]
        rows = records if variant == "base" else extra_records
        if name in rows:
            row = rows[name]
            body = cq.Shape.importBrep(str(pin(row["path"], row["sha256"])))
        elif name in bracket_rows:
            m = bracket_rows[name]["transform"]
            body = bracket_template.moved(cq.Plane(origin=m[12:15], xDir=m[:3], normal=m[8:11]).location)
        else:
            axis_name, role = next(((axis, name[len(axis) + 1:]) for axis in axes if name.startswith(axis + "_")),
                                   (None, None))
            require(axis_name is not None, "unresolved source solid: " + name)
            if axis_name not in metal_cache:
                axis = axes[axis_name]
                a = {**axis, "point": cq.Vector(*axis["point_xyz_mm"]), "direction": cq.Vector(*axis["direction_xyz"])}
                metal_cache[axis_name] = {part_role: body for _, part_role, body in hardware.hardware([a])}
            body = metal_cache[axis_name][role]
        require(body.isValid() and len(body.Solids()) == 1, "invalid source solid: " + name)
        bank = off if variant == "base" else on
        bb = body.BoundingBox()
        observed = [getattr(bb, axis + end) for axis in "xyz" for end in ("min", "max")]
        require(max(abs(a - b) for a, b in zip(observed, bank[name]["bounds"], strict=True)) < 0.0002,
                "source solid differs from viewer bounds: " + name)
        cache[key] = body
        return body

    # Known flat-ended cylinder controls: a remote body, volume overlap, and
    # a tangent end plane. Tangency is not positive intrusion.
    coupon = cq.Solid.makeCylinder(1, 2)
    require(coupon.intersect(coupon.translate((3, 0, 0))).Volume() < 1e-8, "separation fixture")
    require(abs(coupon.intersect(coupon.translate((1, 0, 0))).Volume() -
                2 * (2 * math.pi / 3 - math.sqrt(3) / 2)) < 1e-8, "overlap fixture")
    require(coupon.intersect(coupon.translate((0, 0, 2))).Volume() < 1e-8, "end-plane fixture")
    fixture = cq.Workplane("XY").box(2, 2, 2).val()
    fixture_parts = {"fixture_shaft": fixture, "neighbor_shaft": fixture.translate((1, 0, 0)),
                     "fixture_panel": fixture, "remote_timber": fixture.translate((10, 0, 0))}
    fixture_bank = {}
    for name, body in fixture_parts.items():
        bb = body.BoundingBox()
        fixture_bank[name] = {"kind": "panel" if name.endswith("panel") else "timber" if name.endswith("timber") else "bolt",
                              "bounds": [getattr(bb, a + e) for a in "xyz" for e in ("min", "max")]}
    assembled = envelope_intrusions(fixture, fixture_bank, fixture_parts.__getitem__, "fixture")
    frame = envelope_intrusions(fixture, fixture_bank, fixture_parts.__getitem__, "fixture", stage=True)
    empty = envelope_intrusions(fixture, fixture_bank, fixture_parts.__getitem__, "fixture", stage=True, excluded=["neighbor_shaft"])
    require(assembled["nominal_intrusions"] == ["neighbor_shaft", "fixture_panel"] and
            frame["nominal_intrusions"] == ["neighbor_shaft"] and empty["reference_envelope_clear"] and
            abs(frame["fine_queries"][0]["intersection_mm3"] - 4) < 1e-8, "production obstacle-query fixtures")
    queries = []

    def query(label, axis_name, body, variant="base", stage=False, excluded=()):
        bank = off if variant == "base" else on
        row = {"axis_id": axis_name, "operation": label, "variant": variant,
               "stage": "frame_before_panels_services" if stage else "assembled",
               **envelope_intrusions(body, bank, lambda name: shape(name, variant), axis_name, stage, excluded),
               "Actual": "", "Disposition": ""}
        queries.append(row)
        return row

    def cylinder(point, direction, offset, length, radius):
        start = cq.Vector(*point) + cq.Vector(*direction) * offset
        return cq.Solid.makeCylinder(radius, length, start, cq.Vector(*direction))

    access = []
    hardware_table = {r["axis_id"]: r for r in csv.DictReader((SHOP / "hardware-selection.csv").open())}
    pin(SHOP / "hardware-selection.csv")
    old_requirements = list(csv.DictReader(io.StringIO((SHOP / "access-requirements.csv").read_text())))
    pin(SHOP / "access-requirements.csv")
    for row in old_requirements:
        name, side = row["axis_id"], row["side"]
        axis, selected_row = axes[name], selected[name]
        h = axis["hardware_scenario"]
        d, point = axis["direction_xyz"], axis["point_xyz_mm"]
        outward = [v * (-1 if side == "head" else 1) for v in d]
        underhead = -axis["before_plate_mm"] - h["washer_thickness_mm"]
        near = underhead if side == "head" else (axis["grip_mm"] + axis["after_plate_mm"] +
                                               h["washer_thickness_mm"] + selected_row["nut_side_spacer_mm"])
        p = [v + near * u for v, u in zip(point, d, strict=True)]
        socket = cylinder(p, outward, 0, float(row["reference_axial_length_mm"]),
                          float(row["reference_socket_radius_mm"]))
        socket_checks = [query("seated_socket", name, socket, stage=stage) for stage in (False, True)]
        short_socket = cylinder(p, outward, 0, 25.4, float(row["reference_socket_radius_mm"]))
        short_check = query("short_socket", name, short_socket, stage=True)
        removal = [query(label, name, cylinder(point, d, start, length, radius), stage=True)
                   for label, start, length, radius in removal_envelopes(axis, selected_row, side)]
        # Twelve static handle orientations provide a counterhold option only.
        # Socket operation and a continuous handle sweep are separate questions.
        thickness = min(6.35, h["head_height_mm"] if side == "head" else h["nut_height_mm"])
        entry = h["head_height_mm"] if side == "head" else float(hardware_table[name]["minimum_nut_socket_cavity_depth_mm"])
        box_entry = cylinder(p, outward, 0, entry + thickness, float(row["reference_socket_radius_mm"]))
        box_entry_check = query("box_end_axial_insertion", name, box_entry, stage=True)
        center = cq.Vector(*p) + cq.Vector(*outward) * thickness / 2
        wrenches = wrench_envelopes(p, outward, thickness, entry, float(row["reference_socket_radius_mm"]))
        handles = []
        for angle in range(0, 360, 30):
            handle = wrenches["static_counterhold"].rotate(center, center + cq.Vector(*outward), angle)
            handles.append(query("static_counterhold_" + str(angle), name, handle, stage=True))
            if handles[-1]["reference_envelope_clear"]:
                break
        sweep_checks = []
        for angle in range(0, 360, 30):
            pose = wrenches["working_handle_60deg"].rotate(center, center + cq.Vector(*outward), angle)
            sweep_checks.append(query("working_handle_60deg_" + str(angle), name, pose, stage=True))
            # The complete handle also travels axially while a box end is
            # slipped over the bolt tip/head. Keep one common orientation.
            insertion = wrenches["complete_wrench_axial_insertion"].rotate(
                cq.Vector(*p), cq.Vector(*p) + cq.Vector(*outward), angle)
            insertion_check = query("complete_wrench_axial_insertion_" + str(angle), name, insertion, stage=True)
            if sweep_checks[-1]["reference_envelope_clear"] and insertion_check["reference_envelope_clear"]:
                break
        access.append({"axis_id": name, "side": side,
            **selected_setup_requirements([*removal, handles[-1], sweep_checks[-1], insertion_check]),
            "assembled_socket_clear": socket_checks[0]["reference_envelope_clear"],
            "frame_stage_socket_clear": socket_checks[1]["reference_envelope_clear"],
            "frame_stage_removal_clear": all(r["reference_envelope_clear"] for r in removal),
            "static_counterhold_clear": handles[-1]["reference_envelope_clear"],
            "static_counterhold_angle_deg": int(handles[-1]["operation"].rsplit("_", 1)[1]) if handles[-1]["reference_envelope_clear"] else "",
            "short_socket_clear": short_check["reference_envelope_clear"],
            "box_end_insertion_clear": box_entry_check["reference_envelope_clear"],
            "box_end_entry_envelope_length_mm": entry + thickness,
            "working_handle_60deg_clear": sweep_checks[-1]["reference_envelope_clear"],
            "complete_wrench_axial_insertion_clear": insertion_check["reference_envelope_clear"],
            "working_handle_angle_deg": int(sweep_checks[-1]["operation"].rsplit("_", 1)[1]) if sweep_checks[-1]["reference_envelope_clear"] else "",
            "continuous_reference_handle_sweep_checked": True,
            "actual_tool_verified": False, "Actual": "", "Disposition": ""})
        if len(access) % 40 == 0:
            print("Refined access sides: " + str(len(access)), flush=True)
    envelopes = read(SHOP / "hardware-envelope-review.json")["rows"]
    extra_checks = []
    for row in envelopes:
        body = cylinder(row["start_xyz_mm"],
                        [(b - a) / math.dist(row["start_xyz_mm"], row["finish_xyz_mm"])
                         for a, b in zip(row["start_xyz_mm"], row["finish_xyz_mm"], strict=True)],
                        0, math.dist(row["start_xyz_mm"], row["finish_xyz_mm"]), row["radius_mm"])
        extra_checks.append(query("selected_" + row["role"], row["axis_id"], body, variant="extra"))
    verify()
    for row in cache:
        require(row[1] in (off if row[0] == "base" else on), "orphan solid")
    (out / "source-pins.json").write_bytes(encoded(pins))
    (out / "queries.json").write_bytes(encoded(queries))
    (out / "access.json").write_bytes(encoded(access))
    result = {"schema": "eoere_selected_hardware_nominal_access/v1", "revision": layout["revision"],
        "source_layout": {"path": str(layout_path), "sha256": sha(layout_path)},
        "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
        "source_map": {"path": str(out / "source-pins.json"), "sha256": sha(out / "source-pins.json")},
        "source_bytes_unchanged": True, "finite_cylinder_known_answers": 3,
        "production_obstacle_query_known_answers": 3,
        "removal_interval_policy": "Each part's near face reaches the selected bolt tip; the sweep includes that part's full axial thickness.",
        "counts": {key: sum(bool(row[key]) for row in access) for key in
                   ["assembled_socket_clear", "frame_stage_socket_clear", "frame_stage_removal_clear", "static_counterhold_clear",
                    "short_socket_clear", "box_end_insertion_clear", "working_handle_60deg_clear",
                    "complete_wrench_axial_insertion_clear"]},
        "access_sides": len(access), "fine_query_count": sum(len(r["fine_queries"]) for r in queries),
        "off_floor_setup_required_sides": sum(row["off_floor_setup_required"] for row in access),
        "minimum_selected_operation_z_mm": min(row["minimum_selected_operation_z_mm"] for row in access),
        "maximum_additional_reference_floor_clearance_mm": max(row["minimum_additional_reference_floor_clearance_mm"] for row in access),
        "temporary_support_or_reorientation_qualified": False,
        "nominal_intrusion_queries": sum(bool(r["nominal_intrusions"]) for r in queries),
        "extra_grid_added_hardware_checks": len(extra_checks),
        "extra_grid_added_hardware_clear": all(r["reference_envelope_clear"] for r in extra_checks),
        "query_operations": dict(Counter(r["operation"].split("_")[0] for r in queries)),
        "nominal_socket_wall_allowance_mm": 1.5, "socket_axial_envelope_mm": 50.8,
        "static_handle_length_width_thickness_max_mm": [152.4, 19.05, 6.35],
        "continuous_reference_handle_sweep_deg": 60,
        "limits": ["Exact nominal solid intrusions against conservative finite envelopes; not delivered-tool qualification.",
                   "Frame stage removes all panels, panel screws, T-nuts, LEDs and wiring before structural bolt operations.",
                   "Rows with tool or removal envelopes below Z=0 require a raised or reoriented, independently supported setup; its actual clearance and stability remain unqualified.",
                   "Counterhold and 60-degree operating sweeps use conservative generic wrench envelopes; clamp/guide sweeps remain unverified.",
                   "Tangency within 0.0001 mm3 is not positive intrusion; no positive manufacturing tolerance is established.",
                   "No native mechanics, timber rebuild, actual observations or fabrication/climbing release."],
        "Actual": "", "Disposition": "", "mechanics_or_physical_release": False,
        "outputs": {n: {"path": str(out / n), "sha256": sha(out / n)} for n in ["queries.json", "access.json"]}}
    (out / "result.json").write_bytes(encoded(result))
    print(json.dumps({k: result[k] for k in ["counts", "nominal_intrusion_queries", "extra_grid_added_hardware_clear", "source_pin_count"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
