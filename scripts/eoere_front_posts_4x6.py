"""Widen the two outer kicker posts inward, retaining every physical axis line.

Build only two timber solids and the eight affected bolt stacks. Compose shop
overrides on the preserved packet; old force fields provide a scalar screening
load set, not a response or complete-joint pass for this revision.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

from scripts.eoere_current_shop_followup import csv_bytes, module
from scripts.eoere_selected_hardware import ROOT, canonical, encoded, require, sha

DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
SHOP = DOC / "shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1"
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/front-posts-4x6-v1")
REPORT = DOC / "occupied-front-posts-4x6-v1.json"
REVISION = "eoere-4x6-front-posts-v1"
KEYS = {"base": "eoere-4x6-front-posts-frame-development", "extra": "eoere-4x6-front-posts-grid-development"}
POSTS = {"base_post_outer_left", "base_post_outer_right"}
ADDED = 50.8
BEVEL = 9.525
CORE_WIDTH = 88.9-BEVEL
GEOMETRY = DOC / "occupied-kicker-clearance-v1.json"
HARDWARE = DOC / "occupied-selected-hardware-v1.json"
PINS = {
    str(GEOMETRY): "7ebee98cb777de63ecdbc32007c97967c445500d93053eb942ab775568a5fb5f",
    str(HARDWARE): "c16ea7dbda86e6471d6dd1edff44f59e0d0a2db1c3fd1af145ffbd6a8a62ec09",
    "site/eoere-selected-hardware-scene.json.gz": "41830cf651f8b0a321a89336f654af5d90a4f42a1d705a7411b5e088de3b2811",
    str(SHOP / "result.json"): "c316386f4e994ad97d0718404252d9f8195f10d6d547ffe3aae22f078ff44f07",
    "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-front-end-connection-shear-attempt01.json": "a42d7b5e5127f0703108315bea5fd8a0ee577e0a7690fa5988f88484e69bf2b2",
}


def axis_lines(axes):
    """Canonical infinite lines, independent of a changed head-side datum."""
    result = []
    for a in axes:
        p, d = a["point_xyz_mm"], a["direction_xyz"]
        moment = [p[1]*d[2]-p[2]*d[1], p[2]*d[0]-p[0]*d[2], p[0]*d[1]-p[1]*d[0]]
        result.append([a["id"], d, [0. if v == 0 else v for v in moment]])
    return result


def revised_axes(original):
    axes = copy.deepcopy(original)
    for a in axes:
        if POSTS.intersection(a["receivers"]):
            require(abs(a["grip_mm"]-76.2) < 1e-8, "old grip differs")
            a["grip_mm"] = 127.
            # Runner-facing heads follow the new inboard face along the same line.
            if a["id"].startswith("rail_front_bolt_"):
                a["point_xyz_mm"] = [p-ADDED*d for p, d in zip(a["point_xyz_mm"], a["direction_xyz"], strict=True)]
            length = 177.8 if a["id"].startswith("cleat_post_bolt_") else 152.4
            a["hardware_scenario"]["available_nominal_lengths_mm"] = [length]
            a["nominal_under_head_length_mm"] = length
    require(axis_lines(axes) == axis_lines(original), "physical bolt line moved")
    require(sum(a != b for a, b in zip(axes, original, strict=True)) == 8, "eight stacks required")
    return axes


def build(out):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT / BASE), "run from root into ignored revision directory")
    require(not out.exists(), "preserve attempts; select a fresh --out")
    pins = {}

    def pin(path, digest=None):
        path = str(path)
        actual = sha(path)
        require(digest is None or actual == digest, "source changed: " + path)
        require(path not in pins or pins[path] == actual, "conflicting source: " + path)
        pins[path] = actual
        return Path(path)

    def read(path):
        return json.loads(pin(path).read_bytes())

    def binding(path):
        return {"path": str(path), "sha256": sha(path)}

    for path, digest in PINS.items():
        pin(path, digest)
    pin(Path(__file__).relative_to(ROOT))
    parent, previous_hardware, shop = read(GEOMETRY), read(HARDWARE), read(SHOP / "result.json")
    # Authenticate issued companion files; unchanged files are referenced, not copied.
    for name, ref in shop["files"].items():
        pin(SHOP / name, ref["sha256"])
    for ref in shop["reused_files"].values():
        pin(ref["path"], ref["sha256"])
    profiles = read(SHOP / "current_profiles.json")
    axes = revised_axes(parent["axes"])
    changed_axes = {a["id"]: a for a, b in zip(axes, parent["axes"], strict=True) if a != b}
    previous = {a["id"]: a for a in parent["axes"]}
    selected = {r["axis_id"]: r for r in previous_hardware["selected_stacks"]}
    inputs = read(SHOP / "inputs.json")
    catalog_ref, window_ref = (inputs["sources"][k] for k in ("catalog", "window_helper"))
    pin(catalog_ref["path"], catalog_ref["sha256"])
    pin(window_ref["path"], window_ref["sha256"])
    catalog = read(catalog_ref["path"])
    windows = module(window_ref["path"], "front_post_catalog_windows")
    diameter = next(r for r in catalog["diameters"] if r["diameter_in"] == .375)
    six = next(r for r in catalog["bolts"] if r["sku"] == 371)
    # ASME B18.2.1-2012 Table 12, printed p.22, 3/8-in / 7-in column.
    seven = {**six, "sku": 372, "url": "https://boltdepot.com/Product-Details?product=372",
             "nominal_length_in": 7., "length_tolerance_minus_in": .18,
             "minimum_full_thread_length_in": 1.25, "Lg_max_in": 5.75,
             "Lb_min_in": 5.44, "unit_price_usd": 2.14, "bag_price_usd": 76.58}
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(Path(__file__).read_bytes())
    print("Authenticated parent geometry and issued shop records; building two posts", flush=True)
    import cadquery as cq

    from scripts import thin_bolted_occupied as hardware
    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    for name, loaded in tuple(sys.modules.items()):
        if name.startswith(("scripts.", "mini_moonboard.")) and getattr(loaded, "__file__", None):
            pin(Path(loaded.__file__).resolve().relative_to(ROOT))
    shapes, saved, replacements = {}, [], []

    def load(member):
        if member not in shapes:
            ref = profiles[member]["finished"]
            pin(ref["path"], ref["sha256"])
            shapes[member] = cq.Shape.importBrep(ref["path"])
        return shapes[member]

    def save(name, kind, shape, extra=None):
        require(shape.isValid() and len(shape.Solids()) == 1, "invalid solid: " + name)
        path = out / (name + ".brep")
        require(shape.exportBrep(str(path)), "BREP export failed")
        restored = cq.Shape.importBrep(str(path))
        require(restored.isValid() and abs(restored.Volume()-shape.Volume()) < 1e-6, "BREP roundtrip differs")
        mesh = _shape_mesh(restored)
        record = {"id": name, "kind": kind, **binding(path), "bytes": path.stat().st_size,
                  "volume_mm3": restored.Volume(), "bounds_xyz_mm": mesh["bounds_xyz_mm"]}
        saved.append(record)
        shapes[name] = restored
        replacements.append({"id": name, "name": name, "mesh": mesh,
                             "fabrication": {"kind": kind, "front_post_revision": REVISION, **(extra or {})}})
        return record

    profile_overrides, member_overrides = {}, []
    members = list(csv.DictReader(io.StringIO((SHOP / "members.csv").read_text())))
    old_shapes, unbeveled = {}, {}
    for name in sorted(POSTS):
        original = load(name)
        old_shapes[name] = original
        b = original.BoundingBox()
        require(max(abs(v-w) for v, w in zip((b.xlen, b.ylen, b.zlen), (38.1, 139.7, 238.9), strict=True)) < 1e-7,
                "post dimensions differ")
        x = b.xmax if name.endswith("left") else b.xmin-ADDED
        growth = cq.Solid.makeBox(ADDED, b.ylen, b.zlen, cq.Vector(x, b.ymin, b.zmin))
        revised = original.fuse(growth).clean()
        own = [a for a in changed_axes.values() if name in a["receivers"]]
        require(len(own) == 4, "four post bores required")
        for a in own:
            d, p = cq.Vector(*a["direction_xyz"]), cq.Vector(*a["point_xyz_mm"])
            cutter = cq.Solid.makeCylinder(a["bore_diameter_mm"]/2, 400., p-d*200., d)
            revised = revised.cut(cutter).clean()
            require(revised.intersect(cutter).Volume() < 1e-7, "bore does not pass through new stock")
        unbeveled[name] = revised
        corner_x = b.xmax+ADDED if name.endswith("left") else b.xmin-ADDED
        inward = -1. if name.endswith("left") else 1.
        bevel = cq.Workplane("XY").polyline([
            (corner_x, b.ymax), (corner_x+inward*BEVEL, b.ymax),
            (corner_x, b.ymax-BEVEL),
        ]).close().extrude(b.zlen+2.).val().translate((0, 0, b.zmin-1.))
        revised = revised.cut(bevel).clean()
        require(original.cut(revised).Volume() < 1e-7, "old timber was removed")
        expected = ADDED*(139.7*238.9-sum(math.pi*a["bore_diameter_mm"]**2/4 for a in own))-.5*BEVEL**2*238.9
        require(abs(revised.Volume()-original.Volume()-expected) < 1e-6, "solid-stock increment differs")
        shapes[name] = revised
        rec = save(name, "timber", revised, {"description": "Solid 4×6 outer kicker post, 238.9 mm tall; 9.525-mm full-height inner kicker-facing corner bevel clears T-nut flanges; bolt lines retained"})
        p = copy.deepcopy(profiles[name])
        p["blank_mm"][2] = 88.9
        p["inner_kicker_facing_longitudinal_bevel_mm"] = BEVEL
        if name.endswith("right"):
            p["datum_xyz_mm"][0] -= ADDED
        for vertex in p["vertices_luv_mm"]:
            if vertex[1] > 1e-6:
                vertex[1] = 88.9
        p["finished"] = {**rec, "bounds_xyz_mm": [[rec["bounds_xyz_mm"][i], rec["bounds_xyz_mm"][i+1]] for i in (0, 2, 4)]}
        profile_overrides[name] = p
        m = next(r.copy() for r in members if r["member"] == name)
        m.update(blank_thickness_mm="88.9", datum_x_mm=str(p["datum_xyz_mm"][0]))
        # Keep the exact issued column names rather than adding parallel columns.
        for key in list(m):
            if key not in members[0]:
                del m[key]
        for key in m:
            if key.endswith("thickness_mm"):
                m[key] = "88.9"
            if key in ("origin_x_mm", "datum_x_mm"):
                m[key] = str(p["datum_xyz_mm"][0])
            if key in ("current_finished_source_path", "current_finished_source_sha256"):
                m[key] = rec["path" if key.endswith("path") else "sha256"]
        m["profile_source"] = str(REPORT)+"#/profile_overrides/"+name
        member_overrides.append(m)
    profiles.update(profile_overrides)

    holes_path = shop["reused_files"]["receiver-holes.csv"]["path"]
    holes = list(csv.DictReader(io.StringIO(Path(holes_path).read_text())))
    hole_overrides = []
    for old in holes:
        if old["axis_id"] not in changed_axes:
            continue
        r, a = old.copy(), changed_axes[old["axis_id"]]
        member = r["receiver"]
        profile, shape = profiles[member], load(member)
        b, d, origin = shape.BoundingBox(), a["direction_xyz"], a["point_xyz_mm"]
        near, far = sorted(((b.xmin-origin[0])/d[0], (b.xmax-origin[0])/d[0]))
        for j, key in enumerate("xyz"):
            r[f"axis_point_{key}_mm"] = str(origin[j])
        for label, t in (("axis_point", 0.), ("entry", near), ("exit", far)):
            world = [v+t*w for v, w in zip(origin, d, strict=True)]
            delta = [v-w for v, w in zip(world, profile["datum_xyz_mm"], strict=True)]
            for key, basis in zip("luv", profile["basis_grain_u_v_xyz"], strict=True):
                r[f"{label}_in_receiver_{key}_mm"] = str(math.fsum(v*w for v, w in zip(delta, basis, strict=True)))
            if label != "axis_point":
                r[f"{label}_from_axis_point_mm"] = str(t)
        r["saved_full_wall_length_mm"] = str(far-near)
        r["modeled_underhead_length_mm"] = str(a["nominal_under_head_length_mm"])
        r["source"] = str(REPORT)+"#/axis_overrides/"+a["id"]
        hole_overrides.append(r)
    require(len(hole_overrides) == 16, "sixteen receiver rows required")
    (out / "receiver-holes.csv").write_bytes(csv_bytes(hole_overrides))

    screw_ref = shop["current_screw_datums"]
    pin(screw_ref["path"], screw_ref["sha256"])
    screw_datums = list(csv.DictReader(io.StringIO(Path(screw_ref["path"]).read_text())))
    screw_overrides, screw_support = [], []
    for row in parent["screw_axes"]:
        if row["receiver"] not in POSTS:
            continue
        profile = profiles[row["receiver"]]
        p, d = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        depth = 63.5-18.25625
        probe = cq.Solid.makeCylinder(2.5, depth, p+d*18.25625, d)
        fraction = probe.intersect(shapes[row["receiver"]]).Volume()/probe.Volume()
        require(fraction > .999999, "kicker screw backing lost")
        screw_support.append({"axis_id": row["axis_id"], "receiver": row["receiver"],
                              "modeled_wood_body_backing_fraction": fraction,
                              "modeled_penetration_mm": depth, "Hillman_product_capacity": None})
        old = next(r for r in screw_datums if r["axis_id"] == row["axis_id"])
        r = old.copy()
        delta = [v-w for v, w in zip(row["origin_xyz_mm"], profile["datum_xyz_mm"], strict=True)]
        for key, basis in zip("luv", profile["basis_grain_u_v_xyz"], strict=True):
            r[f"origin_in_receiver_{key}_mm"] = str(math.fsum(v*w for v, w in zip(delta, basis, strict=True)))
        if any(abs(float(r[k])-float(old[k])) > 1e-8 for k in r if k.startswith("origin_in_receiver_")):
            r["source"] = str(REPORT)+"#/profile_overrides/"+row["receiver"]
            screw_overrides.append(r)
    require(len(screw_support) == 4 and len(screw_overrides) == 2, "four backed screws/two rebased datum rows required")
    (out / "panel-screw-datums.csv").write_bytes(csv_bytes(screw_overrides))

    selections = []
    for name, a in changed_axes.items():
        cleat = name.startswith("cleat_post_bolt_")
        product, spacer = (seven, 25.4) if cleat else (six, 0.)
        w = windows.bounds_for(a["grip_mm"]+spacer, product, diameter)
        own = sorted((r for r in hole_overrides if r["axis_id"] == name), key=lambda r: float(r["exit_from_axis_point_mm"]))
        target = w["washer_each_bounds_mm"][1] + (a["grip_mm"] if cleat else float(own[0]["exit_from_axis_point_mm"]))
        margins = [w["catalog_min_length_max_stack_two_tip_margin_mm"],
                   w["nut_near_minus_Lg_max_bounds_mm"][0], w["ASME_Lb_min_mm"]-target]
        require(min(margins) > 0, "selected stack window fails: " + name)
        row = {**selected[name], "selected_product": str(product["sku"]), "selected_product_url": product["url"],
               "selected_underhead_length_mm": a["nominal_under_head_length_mm"], "nut_side_spacer_mm": spacer,
               "spacer_piece_count": 2 if cleat else 0, "spacer_piece_length_mm": 12.7 if cleat else 0.,
               "minimum_length_mm": w["underhead_length_bounds_mm"][0], "minimum_body_mm": w["ASME_Lb_min_mm"],
               "maximum_grip_gaging_mm": w["ASME_Lg_max_mm"], "nominated_smooth_body_target_mm": target,
               "minimum_body_to_nominated_target_margin_mm": margins[2],
               "minimum_two_pitch_margin_mm": margins[0], "minimum_nut_seating_margin_mm": margins[1],
               "selected_tip_delta_mm": a["nominal_under_head_length_mm"]-previous[name]["nominal_under_head_length_mm"],
               "receiver_member_ids": ";".join(a["receivers"]), "receiver_plus_plate_nominal_mm": a["grip_mm"],
               "selected_recipe": "head/head_washer/receivers/nut_washer/"+("spacer/spacer/" if cleat else "")+"nut",
               "Actual": "", "Disposition": ""}
        selections.append(row)
        local = dict(hardware.local_hardware(a))
        require(a["nominal_under_head_length_mm"] == row["selected_underhead_length_mm"], "hardware chose another length")
        h = a["hardware_scenario"]
        a["tip_projection_beyond_nut_mm"] -= spacer
        local["nut"] = local["nut"].translate((0, 0, spacer))
        for index in range(row["spacer_piece_count"]):
            offset = a["grip_mm"]+h["washer_thickness_mm"]+12.7*index
            part = cq.Solid.makeCylinder(19.05/2, 12.7, cq.Vector(0, 0, offset)).cut(
                cq.Solid.makeCylinder(10.31875/2, 12.7, cq.Vector(0, 0, offset)))
            local["spacer" if index == 0 else "spacer_2"] = part
        plane = cq.Plane(origin=cq.Vector(*a["point_xyz_mm"]), normal=cq.Vector(*a["direction_xyz"]))
        for role, body in local.items():
            save(name+"_"+role, "bolt", body.moved(plane.location),
                 {"connection_name": name, "hardware_role": role,
                  "description": "Revised partial-thread Grade 5 stack for solid 4×6 post; delivered fit unverified",
                  "selected_hardware_revision": REVISION,
                  "selected_underhead_length_mm": row["selected_underhead_length_mm"],
                  "minimum_body_mm": row["minimum_body_mm"], "maximum_grip_gaging_mm": row["maximum_grip_gaging_mm"],
                  "stack_roles": list(local),
                  "nut_side_spacer_mm": spacer})
    (out / "hardware-selection.csv").write_bytes(csv_bytes(selections))

    source = read(next(k for k in PINS if k.endswith("shear-attempt01.json")))
    screens = []
    for r in source["rows"]:
        if r["geometry_key"] not in {name+"/front" for name in POSTS}:
            continue
        g = source["geometries"][r["geometry_key"]]
        limits = [c["reference_n"]*(CORE_WIDTH-.001)/c["b_mm"] for c in g["reference_lower_positive_negative_V"]]
        demand = r["maximum_strong_axis_shear_n"]+1e-5
        screens.append({"member": g["member"], "case_id": r["case_id"], "demand_upper_n": demand,
                        "reference_lower_n": min(limits), "ratio_upper": demand/min(limits)})
    require(len(screens) == 12 and max(r["ratio_upper"] for r in screens) < .724, "post rectangular-core shear screen failed")
    # Move each post blank to its rear-leg stock offcut, preserving all stick purchases.
    nesting = read(shop["reused_files"]["stock-nesting.json"]["path"])
    changed_sticks = []
    for old in nesting["sticks"]:
        s = copy.deepcopy(old)
        pairs = [(n, length) for n, length in zip(s["members"], s["blank_lengths_mm"], strict=True) if n not in POSTS]
        for side in ("left", "right"):
            if "lumber_leg_"+side in s["members"]:
                pairs.append(("base_post_outer_"+side, 238.9))
        if [p[0] for p in pairs] != s["members"]:
            s["members"], s["blank_lengths_mm"] = map(list, zip(*pairs, strict=True))
            s["consumed_with_kerf_and_trim_mm"] = sum(s["blank_lengths_mm"])+len(pairs)*nesting["kerf_mm_per_output_piece"]+2*nesting["end_trim_allowance_mm_each"]
            s["remaining_mm"] = s["length_ft"]*304.8-s["consumed_with_kerf_and_trim_mm"]
            require(s["remaining_mm"] > 0, "stock offcut too short")
            changed_sticks.append(s)
    require(len(changed_sticks) == 3, "three stock allocations should change")
    # Nominal exact-body intersections with the other current timber/panel members.
    intersections = []
    for name in sorted(POSTS):
        for other in profiles:
            if other == name:
                continue
            obstacle = load(other)
            volume = shapes[name].intersect(obstacle).Volume()
            require(volume < 1e-6, "new timber overlaps " + other)
            intersections.append({"post": name, "other": other, "intersection_volume_mm3": volume})
    metal_queries = 0
    for rec in saved:
        if rec["kind"] != "bolt":
            continue
        metal = shapes[rec["id"]]
        a = metal.BoundingBox()
        for member in profiles:
            timber = load(member)
            b = timber.BoundingBox()
            if any(min(getattr(a, k+"max"), getattr(b, k+"max"))-max(getattr(a, k+"min"), getattr(b, k+"min")) < 1e-7 for k in "xyz"):
                continue
            volume = metal.intersect(timber).Volume()
            require(volume < 1e-6, "revised metal overlaps " + member + ": " + rec["id"])
            metal_queries += 1
    # Include services in the fit gate. The uncut wider stock intersects both
    # outer kicker T-nut flanges; a timber/structural-metal census misses them.
    native_ref = inputs["sources"]["native"]
    pin(native_ref["path"], native_ref["sha256"])
    native = read(native_ref["path"])
    bounds_ref = inputs["sources"]["bounds_helper"]
    pin(bounds_ref["path"], bounds_ref["sha256"])
    bounds = module(bounds_ref["path"], "front_post_service_bounds")
    layers = []
    for name in ("eoere-bottom-rail-scene.json.gz", "eoere-cleat-trim-scene.json", "eoere-aligned-wire-scene.json.gz",
                 "eoere-adjusted-base-v3-scene.json.gz", "eoere-cleat-extension-scene.json.gz"):
        pin("site/"+name)
        layers.append(bounds.asset("site/"+name))
    pin("site/eoere-uniform-channels-scene.json.gz")
    channels = bounds.asset("site/eoere-uniform-channels-scene.json.gz")
    layers.append({"replacements": channels["common_replacements"]+channels["base_replacements"]})
    for name in ("eoere-kicker-clearance-scene.json.gz", "eoere-selected-hardware-scene.json.gz"):
        pin("site/"+name)
        layers.append(bounds.asset("site/"+name))
    bank = bounds.compose_bounds(native, layers)
    require(len(bank) == 1029, "current base part census differs")
    services = {k: v for k, v in bank.items() if v["kind"] in ("tnut", "light", "wire")}
    require(len(services) == 405, "complete base service census required")
    registry = {r["id"]: r for r in native["parts"]}
    for name in ("occupied-aligned-wire-v1.json", "occupied-adjusted-base-v3.json", "occupied-uniform-channels-v1.json"):
        data = read(DOC / name)
        registry.update({r["id"]: r for r in data["changed_finished_solids"] if r.get("variant") in (None, "base", "common")})
    service_queries, service_failures = [], []
    for name in sorted(POSTS):
        bb = shapes[name].BoundingBox()
        for other, service in services.items():
            sb = service["bounds"]
            if any(min(getattr(bb, a+"max"), sb[2*j+1])-max(getattr(bb, a+"min"), sb[2*j]) <= 1e-7 for j, a in enumerate("xyz")):
                continue
            ref = registry[other]
            pin(ref["path"], ref["sha256"])
            obstacle = cq.Shape.importBrep(ref["path"])
            before = unbeveled[name].intersect(obstacle).Volume()
            volume = shapes[name].intersect(obstacle).Volume()
            gap = shapes[name].distance(obstacle)
            require(volume < 1e-7 and gap > 2., "post/service clearance fails: "+other)
            service_queries.append({"post": name, "service": other, "source": ref,
                                    "intersection_volume_mm3": volume, "minimum_distance_mm": gap})
            if before > 1e-7:
                service_failures.append({"post": name, "service": other, "unbeveled_intersection_volume_mm3": before})
    require(len(service_failures) == 2, "both original kicker T-nut clashes must be reproduced")
    for path, digest in pins.items():
        require(sha(path) == digest, "source drift: " + path)
    release = {k: False for k in ("fabrication", "climbing", "observed_parts", "complete_joint_acceptance", "response_pass_transferred", "native_analysis")}
    report = {"schema": "eoere_front_posts_4x6_geometry/v1", "candidate": parent["candidate"],
              "revision": REVISION, "status": "GEOMETRY_REVISED_RESPONSE_AND_JOINT_ACCEPTANCE_OPEN",
              "parent_geometry": binding(GEOMETRY), "parent_hardware": binding(HARDWARE),
              "parent_shop": binding(SHOP / "result.json"), "source_sha256": pins,
              "axis_overrides": changed_axes, "bolt_axis_lines_canonical_sha256": canonical(axis_lines(axes)),
              "unchanged_bolt_axis_lines": 100, "unchanged_screw_axes": 66,
              "screw_axes_canonical_sha256": canonical(parent["screw_axes"]),
              "profile_overrides": profile_overrides, "member_overrides": member_overrides,
              "inner_kicker_facing_longitudinal_bevel_mm": BEVEL,
              "minimum_full_depth_rectangular_core_width_mm": CORE_WIDTH,
              "kicker_screw_backing": screw_support, "rebased_screw_datum_rows": 2,
              "selected_stack_overrides": selections, "changed_finished_solids": saved,
              "stock_allocation_overrides": changed_sticks,
              "nominal_stock_purchase_changed": False, "nominal_stock_board_feet": 150.,
              "timber_added_mass_at_500kg_m3": sum(shapes[n].Volume()-old_shapes[n].Volume() for n in POSTS)*500e-9,
              "fixed_original_action_post_shear_screens": screens,
              "maximum_fixed_action_post_shear_ratio": max(r["ratio_upper"] for r in screens),
              "new_post_other_member_intersections": intersections,
              "metal_member_intersection_queries": metal_queries, "metal_member_intersections_clear": True,
              "service_census": {"parts": 405, "post_service_comparisons": 810, "refined_queries": service_queries,
                                 "all_clear": True, "unbeveled_stock_failures": service_failures},
              "shop_overrides": {name: binding(out / name) for name in ("receiver-holes.csv", "hardware-selection.csv", "panel-screw-datums.csv")},
              "catalog_source_notes": {"checked_date": "2026-10-19", "bolts": [six, seven],
                  "ASME_primary_url": catalog["asme_source"]["url"] if "asme_source" in catalog else "https://www.wanhong-fastener.com/wp-content/uploads/2025/04/ASME-B18.2.1-2012.pdf",
                  "ASME_locator": "Table 12, printed pp.21–22 / PDF pp.31–32, 3/8-in diameter, 6-in and 7-in columns; same saved dimensional comparison, not delivered conformance"},
              "mechanics_ready": False, "analysis_pass_transferred": False, "new_response_computed": False,
              "release": release, "cadquery_version": cq.__version__,
              "command": f"uv run python -m scripts.eoere_front_posts_4x6 --out {out}",
              "producer_snapshot": binding(out / "producer-snapshot.py"),
              "limits": ["Original scalar demands compared with a 79.375-mm full-depth rectangular-core reference; the prismatic corner bevel and complete load transfer remain subject to the revised member/joint treatment.",
                         "New mass/stiffness, contact and bolt bending require revised response/joint checks.",
                         "Two standard half-inch spacers per cleat-post nut; axial spacer/joint resistance and actual fit remain unqualified.",
                         "Old rear-foot, channel, panel/screw and other joint holds remain recorded and unresolved."]}
    report_bytes = encoded(report)
    (out / "geometry.json").write_bytes(report_bytes)
    scene = {"schema": "eoere_front_posts_4x6_patch/v1", "candidate": parent["candidate"], "revision": REVISION,
             "layout_report": {"path": str(REPORT), "sha256": sha(out / "geometry.json")},
             "parent_scene": {"url": "eoere-selected-hardware-scene.json.gz", **binding("site/eoere-selected-hardware-scene.json.gz"),
                              "decoded_sha256": hashlib.sha256(gzip.decompress(Path("site/eoere-selected-hardware-scene.json.gz").read_bytes())).hexdigest()},
             "parent_layout": binding(HARDWARE), "keys": KEYS, "replacements": replacements,
             "triangle_topologies": _deduplicate_triangle_topologies(replacements),
             "counts": {"base": 1033, "extra": 1428, "timbers": 22, "panels": 6, "bolts": 100, "screws": 66, "spacers": 12},
             "mechanics_ready": False, "analysis_pass_transferred": False, "release": release}
    scene_bytes = encoded(scene)
    (out / "scene.json.gz").write_bytes(gzip.compress(scene_bytes, compresslevel=9, mtime=0))
    print(json.dumps({"revision": REVISION, "report": str(out / "geometry.json"), "report_sha256": sha(out / "geometry.json"),
                      "scene_sha256": sha(out / "scene.json.gz"), "decoded_sha256": hashlib.sha256(scene_bytes).hexdigest(),
                      "post_shear_ratio": report["maximum_fixed_action_post_shear_ratio"]}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    build(parser.parse_args().out)
