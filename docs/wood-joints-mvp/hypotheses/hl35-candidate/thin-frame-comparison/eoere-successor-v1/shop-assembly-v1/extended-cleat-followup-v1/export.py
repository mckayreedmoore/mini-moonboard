"""Compose current shop coordinates from saved geometry; no CAD or mechanics."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import json
import math
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def table(data):
    reader = csv.DictReader(io.StringIO(data.decode()))
    return list(reader.fieldnames), list(reader)


def vector(row, prefix, axes="xyz", suffix="mm"):
    return [float(row[f"{prefix}_{a}_{suffix}"]) for a in axes]


def put(row, prefix, values, axes="xyz", suffix="mm"):
    row.update({f"{prefix}_{a}_{suffix}": v for a, v in zip(axes, values, strict=True)})


def build():
    input_bytes = (OWN / "inputs.json").read_bytes()
    spec = json.loads(input_bytes)
    pins = {r["path"]: r["sha256"] for r in spec["sources"].values()}
    data, encoded = {}, {}
    for key, ref in spec["sources"].items():
        raw = (ROOT / ref["path"]).read_bytes()
        require((sha(raw), len(raw)) == (ref["sha256"], ref["bytes"]), f"source changed: {key}")
        encoded[key] = raw
        if ref["path"].endswith(".json"):
            data[key] = json.loads(raw)
    helper = module(spec["sources"]["datum_helper"]["path"], "saved_datum_helper")
    draw = module(spec["sources"]["drawing_helper"]["path"], "saved_drawing_helper")
    for key, filename in [("members", "members.csv"), ("ends", "member-end-datums.csv"),
                          ("holes", "receiver-holes.csv"), ("screws", "panel-screw-datums.csv")]:
        require(sha(encoded[key]) == data["old_result"]["files"][filename]["sha256"],
                f"old datum result/table join differs: {filename}")
    for key, filename in [("stacks", "bolt-stacks.csv"), ("access", "access-sides.csv")]:
        require(sha(encoded[key]) == data["hardware_result"]["generated_companion_sha256"][filename],
                f"old hardware result/table join differs: {filename}")
    base, aligned, extension, bottom = (data[k] for k in ("base", "aligned", "extension", "bottom"))
    require(extension["revision"] == spec["revision"] and extension["only_two_cleat_bodies_changed"],
            "extension revision or scope differs")
    require(extension["axes"] == base["axes"] and extension["screw_axes"] == base["screw_axes"],
            "extension axes differ from reviewed base")
    require(canonical(base["axes"]) == extension["base_100_axis_records_canonical_sha256"]
            and canonical(base["screw_axes"]) == extension["base_66_screw_records_canonical_sha256"],
            "current axis canonical join differs")
    for parent in (aligned, base, extension):
        for path, expected in parent["source_sha256"].items():
            require(path not in pins or pins[path] == expected, f"conflicting source: {path}")
            pins[path] = expected
    for ref in data["old_result"]["sources"].values():
        require(ref["path"] not in pins or pins[ref["path"]] == ref["sha256"], "old datum pin conflict")
        pins[ref["path"]] = ref["sha256"]

    finished = {r["id"]: r for r in [*aligned["changed_finished_solids"],
                *aligned["unchanged_finished_solids"], *bottom["finished_panel_solids"]]}
    for r in base["changed_finished_solids"]:
        if r["kind"] in {"timber", "panel"}:
            finished[r["id"]] = r
    finished.update({r["id"]: r for r in extension["changed_finished_solids"]})
    require(len(finished) == 28, "finished timber/panel census differs")
    for r in finished.values():
        pins[r["path"]] = r["sha256"]
    for path, expected in pins.items():
        require(sha((ROOT / path).read_bytes()) == expected, f"inherited source changed: {path}")

    columns, members = table(encoded["members"])
    end_columns, old_ends = table(encoded["ends"])
    profiles = {}
    shifted = {"base_principal_center_right", "base_post_center_right"}
    for row in members:
        name = row["member"]
        datum = vector(row, "datum")
        basis = [vector(row, f"basis_{a}", suffix="unitless") for a in "luv"]
        vertices = [vector(r, "point", "luv") for r in old_ends
                    if r["member"] == name and r["record_kind"] != "raw_end_plane"]
        planes = [copy.deepcopy(r) for r in old_ends
                  if r["member"] == name and r["record_kind"] == "raw_end_plane"]
        if name in shifted or name in base["extended_rails"]:
            datum = helper.add(datum, base["principal_shift_xyz_mm"])
        if name in base["extended_rails"]:
            old_length = float(row["nominal_blank_length_mm"])
            new_length = old_length - base["principal_shift_xyz_mm"][0]
            for p in vertices:
                if abs(p[0] - old_length) < 1e-6:
                    p[0] = new_length
            row["nominal_blank_length_mm"] = new_length
            for plane in planes:
                if float(plane["outward_normal_l_unitless"]) > 0:
                    plane["plane_offset_from_datum_mm"] = new_length
        if name.startswith("eoere_cleat_"):
            xs = finished[name]["bounds_xyz_mm"][0]
            vertices = [helper.local([x, y, z], datum, basis) for x in xs
                        for y, z in extension["new_cleat_YZ_polygon_mm"]]
            row["nominal_blank_length_mm"] = extension["maximum_blank_length_mm"]
            row["profile_source"] = "extension#/new_cleat_YZ_polygon_mm"
            # The top is a plane across the thickness, not a square end cut.
            slope = ((vertices[2][0] - vertices[3][0]) /
                     (vertices[2][2] - vertices[3][2]))
            normal = helper.scale([1., 0., -slope], 1 / math.sqrt(1 + slope * slope))
            planes = []
            for index, (n, offset, indices) in enumerate([
                ([-1., 0., 0.], 0., [0, 1, 4, 5]),
                (normal, helper.dot(normal, vertices[2]), [2, 3, 6, 7]),
            ]):
                p = {k: "" for k in end_columns}
                p.update(member=name, record_kind="raw_end_plane", source_index=index,
                         plane_offset_from_datum_mm=offset,
                         normal_to_L_deg=math.degrees(math.acos(abs(n[0]))),
                         plane_source_vertex_indices=";".join(map(str, indices)))
                put(p, "outward_normal", n, "luv", "unitless")
                planes.append(p)
        row["profile_source"] = f"current_profiles.json#/{name}"
        put(row, "datum", datum)
        row["current_finished_source_path"] = finished[name]["path"]
        row["current_finished_source_sha256"] = finished[name]["sha256"]
        profiles[name] = {"datum_xyz_mm": datum, "basis_grain_u_v_xyz": basis,
                          "vertices_luv_mm": vertices, "kind": row["kind"],
                          "blank_mm": [float(row[f"nominal_blank_{d}_mm"])
                                       for d in ("length", "depth", "thickness")],
                          "finished": finished[name], "end_planes": planes}

    maximum = {"coordinate_roundtrip_mm": 0., "end_plane_vertex_residual_mm": 0.,
               "axis_grip_sum_mm": 0., "panel_axis_depth_mm": 0.}
    ends = []
    for name, profile in profiles.items():
        datum, basis = profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]
        for index, p in enumerate(profile["vertices_luv_mm"]):
            w = helper.world(p, datum, basis)
            error = max(abs(a - b) for a, b in zip(helper.local(w, datum, basis), p, strict=True))
            maximum["coordinate_roundtrip_mm"] = max(maximum["coordinate_roundtrip_mm"], error)
            row = {k: "" for k in end_columns}
            row.update(member=name, source_index=index, source=f"current_profiles.json#/{name}",
                       record_kind="raw_profile_vertex" if profile["kind"] == "timber" else "panel_section_vertex")
            put(row, "point", p, "luv")
            put(row, "point", w)
            ends.append(row)
        for plane in profile["end_planes"]:
            indices = [int(i) for i in str(plane["plane_source_vertex_indices"]).split(";")]
            n = vector(plane, "outward_normal", "luv", "unitless")
            offset = float(plane["plane_offset_from_datum_mm"])
            residual = max(abs(helper.dot(profile["vertices_luv_mm"][i], n) - offset) for i in indices)
            maximum["end_plane_vertex_residual_mm"] = max(maximum["end_plane_vertex_residual_mm"], residual)
            plane["source"] = f"current_profiles.json#/{name}"
            ends.append(plane)

    axes = {a["id"]: a for a in extension["axes"]}
    axis_indices = {a["id"]: i for i, a in enumerate(extension["axes"])}
    old_axes = {a["id"]: a for a in bottom["axes"]}
    require(set(axes) == set(old_axes) and len(axes) == 100, "shaft identities changed")
    for name, p in data["corner_data"]["parts"].items():
        require(finished[name]["sha256"] == p["finished_source"]["sha256"],
                f"left corner member no longer matches preserved drawings: {name}")
    for bolt in data["corner_data"]["bolts"]:
        require(axes[bolt["id"]]["point_xyz_mm"] == bolt["point_xyz_mm"] and
                axes[bolt["id"]]["direction_xyz"] == bolt["direction_xyz"],
                "left corner shaft no longer matches preserved drawing")
    scalar_keys = ("receivers", "diameter_mm", "bore_diameter_mm", "before_plate_mm", "after_plate_mm",
                   "nominal_under_head_length_mm", "hardware_scenario", "source")
    for name, axis in axes.items():
        require(all(axis[k] == old_axes[name][k] for k in scalar_keys), f"stack recipe changed: {name}")
        require(abs(axis["grip_mm"] - old_axes[name]["grip_mm"]) < 1e-6, f"grip changed: {name}")
        require(max(abs(x-y) for x, y in zip(axis["direction_xyz"], old_axes[name]["direction_xyz"], strict=True))
                < 1e-8, f"shaft direction changed: {name}")
    hole_columns, holes = table(encoded["holes"])
    grips = Counter()
    for index, row in enumerate(holes):
        name, receiver = row["axis_id"], row["receiver"]
        axis, profile = axes[name], profiles[receiver]
        point, direction = axis["point_xyz_mm"], vector(row, "axis_direction", suffix="unitless")
        a, b = (float(row[f"{side}_from_axis_point_mm"]) for side in ("entry", "exit"))
        datum, basis = profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]
        put(row, "axis_point", point)
        for label, p in [("axis_point", point), ("entry", helper.add(point, helper.scale(direction, a))),
                         ("exit", helper.add(point, helper.scale(direction, b)))]:
            put(row, f"{label}_in_receiver", helper.local(p, datum, basis), "luv")
        row["source"] = f"source holes CSV row {index+2}; preserved wall interval translated to extension#/axes/{axis_indices[name]}"
        grips[name] += b - a
    require({(r["axis_id"], r["receiver"]) for r in holes} ==
            {(a["id"], r) for a in axes.values() for r in a["receivers"]}, "receiver identities differ")
    maximum["axis_grip_sum_mm"] = max(abs(grips[k] - axes[k]["grip_mm"]) for k in axes)

    screw_columns, screws = table(encoded["screws"])
    screw_by_id = {r["axis_id"]: r for r in extension["screw_axes"]}
    screw_indices = {r["axis_id"]: i for i, r in enumerate(extension["screw_axes"])}
    moved_screws = []
    for row in screws:
        screw = screw_by_id[row["axis_id"]]
        require((row["panel"], row["receiver"]) == (screw["panel"], screw["receiver"]), "screw ownership changed")
        origin = screw["origin_xyz_mm"]
        moved = max(abs(x-y) for x, y in zip(origin, vector(row, "front_axis_origin"), strict=True)) > 1e-6
        if moved:
            moved_screws.append(row["axis_id"])
        row["moved_by_rail_revision"] = moved
        put(row, "front_axis_origin", origin)
        for label, member in (("panel", screw["panel"]), ("receiver", screw["receiver"])):
            p = profiles[member]
            coord = helper.local(origin, p["datum_xyz_mm"], p["basis_grain_u_v_xyz"])
            put(row, f"origin_in_{label}", coord, "luv")
            if label == "panel":
                maximum["panel_axis_depth_mm"] = max(maximum["panel_axis_depth_mm"],
                    abs(coord[2] + float(row["modeled_panel_thickness_mm"])))
        row["source"] = f"extension#/screw_axes/{screw_indices[row['axis_id']]}"
    require(len(screws) == 66 and len(moved_screws) == 10, "current ten-screw translation differs")

    stack_columns, stacks = table(encoded["stacks"])
    access_columns, access = table(encoded["access"])
    translated = []
    for row in stacks:
        name = row["axis_id"]
        moved = max(abs(x-y) for x, y in zip(axes[name]["point_xyz_mm"], old_axes[name]["point_xyz_mm"], strict=True)) > 1e-6
        row["current_station_translated"] = moved
        if moved:
            translated.append(name)
        row["geometry_axis_pointer"] = f"extension#/axes/{axis_indices[name]}"
    for row in access:
        name = row["axis_id"]
        delta = helper.subtract(axes[name]["point_xyz_mm"], old_axes[name]["point_xyz_mm"])
        for key in ("axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm"):
            p = helper.add(list(map(float, row[key].split(";"))), delta)
            if key == "axis_origin_xyz_mm":
                p = axes[name]["point_xyz_mm"]
            row[key] = ";".join(format(v, ".12g") for v in p)
        row["current_station_translated"] = name in translated
    require(len(translated) == 22 and len(stacks) == 100 and len(access) == 200, "current hardware census differs")

    machining_columns = ["identity", "panel", "kind", "modeled_diameter_mm", "origin_x_mm", "origin_y_mm",
                         "origin_z_mm", "direction_x_unitless", "direction_y_unitless", "direction_z_unitless",
                         "origin_in_panel_l_mm", "origin_in_panel_u_mm", "origin_in_panel_v_mm", "source"]
    machining = []
    for index, feature in enumerate(bottom["panel_machining"]["features"]):
        point = feature["start_xyz_mm"]
        source = f"bottom#/panel_machining/features/{index}"
        if feature["identity"] in screw_by_id:
            point = screw_by_id[feature["identity"]]["origin_xyz_mm"]
            source = f"extension#/screw_axes/{screw_indices[feature['identity']]}"
        p = profiles[feature["panel"]]
        machining.append([feature["identity"], feature["panel"], feature["kind"], feature["diameter_mm"],
                          *point, *feature["direction_xyz"],
                          *helper.local(point, p["datum_xyz_mm"], p["basis_grain_u_v_xyz"]), source])
    require(len(machining) == 340, "panel machining feature census differs")

    recesses = copy.deepcopy(data["old_result"]["recess_definitions"]["definitions"])
    for recess in recesses:
        boundary = recess["cut_profile_world_x_global_grain_s_mm"]
        start = boundary[2][1] - boundary[0][1]
        finish = boundary[3][1] - boundary[0][1]
        p = profiles[recess["member"]]
        front_foot = min(v[0] for v in p["vertices_luv_mm"] if abs(v[2]+139.7) < 1e-6)
        # Exact prismatic subtraction: constant-depth length minus sloping foot,
        # plus triangular taper. Z141.7 sets taper start; it does not clip it.
        volume = 38.1 * 139.7 * (start - front_foot/2 + (finish-start)/2)
        require(abs(volume-recess["recorded_current_removed_volume_mm3"]) < 1e-4,
                "analytic recess volume differs from saved removed volume")
        recess.update(start_from_rear_heel_L_mm=start, finish_from_rear_heel_L_mm=finish,
                      analytic_removed_volume_mm3=volume,
                      depth_law="d(L)=38.1 for L<=start; (finish-L)/12 for start<L<finish; 0 thereafter",
                      height_reference_is_not_a_cutter_clip=True)

    old_stock = data["old_access"]["takeoff"]["stock"]
    stock = copy.deepcopy(old_stock)
    # Move four posts off the nearly full principal sticks; same 13 purchased sticks.
    for stick in stock["sticks"]:
        names = stick["members"]
        if names[0].startswith("base_principal_center_"):
            names[:] = names[:1]
        if names == ["base_header"]:
            names += ["base_post_outer_left", "base_post_outer_right"]
        if names[0] == "base_rail_bottom_left":
            names.append("base_post_center_left")
        if names[0] == "base_rail_service_lower_left":
            names.append("base_post_center_right")
        if names == ["base_floor_left"]:
            names.append("eoere_cleat_left")
        if names == ["base_floor_right"]:
            names.append("eoere_cleat_right")
        lengths = [profiles[n]["blank_mm"][0] for n in names]
        consumed = math.fsum(lengths) + len(names) * stock["kerf_mm_per_output_piece"] + 2 * stock["end_trim_allowance_mm_each"]
        stick.update(blank_lengths_mm=lengths, consumed_with_kerf_and_trim_mm=consumed,
                     remaining_mm=stick["length_ft"] * 304.8 - consumed)
        require(stick["remaining_mm"] >= 0, "updated stock nesting exceeds stick")
    used = [n for s in stock["sticks"] for n in s["members"]]
    require(len(used) == len(set(used)) == 22 and set(used) ==
            {n for n, p in profiles.items() if p["kind"] == "timber"}, "22 stock pieces not uniquely nested")
    stock.pop("all_20_timbers_placed")
    stock.update(all_22_timbers_placed=True, minimum_nominal_remaining_mm=min(s["remaining_mm"] for s in stock["sticks"]),
                 limits="Nominal blank envelopes, 3.175-mm kerf per piece and 12.7-mm trim at each stick end. Actual usable stock/kerf/grade not observed. No machining tolerance is established by the spare length.")

    mass = data["inventory"]["nominal_mass"]
    timber_volume = math.fsum(p["finished"]["volume_mm3"] for p in profiles.values() if p["kind"] == "timber")
    panel_volume = math.fsum(p["finished"]["volume_mm3"] for p in profiles.values() if p["kind"] == "panel")
    nonwood = (mass["22_angles_at_drawing1_46lb_each_kg"] + mass["500_nominal_bolt_roles_kg"] +
               mass["66_screws_and142_Tnuts_saved_CAD_kg"] + mass["service_accessory_allowance_kg"])
    current_mass = {"finished_timber_volume_mm3": timber_volume, "finished_timber_kg_at_500kg_m3": timber_volume * 500e-9,
                    "finished_panel_volume_mm3": panel_volume, "finished_panel_kg_at_500kg_m3": panel_volume * 500e-9,
                    "preserved_nominal_nonwood_and_25kg_allowance_kg": nonwood,
                    "conditional_total_kg": (timber_volume + panel_volume) * 500e-9 + nonwood,
                    "actual_total_kg": None, "optional_extra_grid_included": False,
                    "limits": "Saved BREP volumes, 500kg/m3 wood, unchanged nominal metal and service allowance; pads excluded. Not measured weight or a fresh gravity/load vector."}
    require(max(maximum.values()) < 1e-5, "coordinate/plane/grip check failed")
    outputs = {}
    for filename, cols, rows in [("members.csv", columns, members), ("member-end-datums.csv", end_columns, ends),
                                 ("receiver-holes.csv", hole_columns, holes), ("panel-screw-datums.csv", screw_columns, screws),
                                 ("bolt-stacks.csv", stack_columns, stacks), ("access-sides.csv", access_columns, access)]:
        require(all(r[k] == "" for r in rows for k in cols if k.startswith("Actual") or k == "Disposition"), "observation cell filled")
        outputs[filename] = helper.csv_bytes(cols[:-2], [[r[k] for k in cols[:-2]] for r in rows])
    outputs["current_profiles.json"] = helper.json_bytes(profiles)
    outputs["panel-machining.csv"] = helper.csv_bytes(machining_columns, machining)
    outputs["rear-recesses.json"] = helper.json_bytes(recesses)
    outputs["stock-nesting.json"] = helper.json_bytes(stock)
    outputs.update(drawings(draw, profiles, holes, screws, machining, extension, recesses))
    result = {"schema": "eoere_extended_cleat_shop_followup/v1", "revision": spec["revision"],
              "status": "PASS_SAVED_COORDINATE_NESTING_AND_INVENTORY_COMPOSITION_WITH_OPEN_FIT_GATES",
              "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
              "inputs_sha256": sha(input_bytes), "helper_sha256": sha(Path(__file__).read_bytes()),
              "counts": {"timbers": 22, "panels": 6, "physical_bolts": 100, "receiver_occurrences": 120,
                         "Hillman_screws": 66, "panel_machining_features": len(machining),
                         "translated_bolts_from_raised_packet": len(translated),
                         "translated_screws_from_raised_packet": len(moved_screws), "head_nut_sides": 200,
                         "stock_sticks": 13, "nominal_board_feet": stock["nominal_board_feet"]},
              "verification": maximum, "nominal_mass": current_mass, "frozen_cost_reference": data["inventory"]["cost"],
              "receiving_requirements": data["hardware_result"]["receiving_requirements"],
              "translated_bolt_ids": translated, "translated_screw_ids": moved_screws,
              "receiver_interval_basis": "Preserved saved full-wall scalar intervals + authenticated unchanged receiver/grip/direction recipes; translated onto current axes and current raw-profile datums. No fresh BREP wall query or swept tool check.",
              "open_gates": ["Four cleat/post stations: 0.340625-mm nominal bolt-bore/screw gap; no practical tolerance acceptance.",
                             "Actual drilling/cutting tools, bits, guide bushings, clamps and fixture travel/retention.",
                             "24 worst-case catalog length flags; delivered shank/thread/washer/nut fit for all stacks.",
                             "200 current head/nut tool and removal sides remain unverified.",
                             "Supplier minimum angle heel dimensions/material and complete joint mechanics.",
                             "Current-revision load response; historical response passes do not transfer."],
              "files": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in outputs.items()},
              "release": {"fabrication": False, "climbing": False, "geometry_changed": False,
                          "physical_observations": False, "panel_screw_remedy_adopted": False},
              "execution": {"dependencies": "Python stdlib; two pinned existing drawing/datum helpers",
                            "CAD_or_native_execution": False, "mechanics": False}}
    outputs["result.json"] = helper.json_bytes(result)
    for path, expected in pins.items():
        require(sha((ROOT / path).read_bytes()) == expected, f"source changed during export: {path}")
    return outputs, result


def drawings(draw, profiles, holes, screws, machining, extension, recesses):
    result = {}
    names = sorted(profiles)
    for page in range(4):
        svg = draw.SVG(1200, 1250)
        svg.text(25, 35, f"Extended-cleat frame: nominal member projections {page+1}/4", 23, "bold")
        svg.text(25, 61, "L along grain / V across section; U is out of plane. Exact datums, U and drill direction are in CSV.", 14)
        svg.text(25, 84, "NOT marking templates. Raw outlines omit recesses, bores and service cuts; targets show entry projections.", 14, color="#9a3140")
        for slot, name in enumerate(names[page*7:(page+1)*7]):
            profile = profiles[name]
            y0 = 125 + slot * 155
            points = [(p[0], p[2]) for p in profile["vertices_luv_mm"]]
            xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
            ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
            scale = min(1050 / max(xmax-xmin, 1), 78 / max(ymax-ymin, 1))
            project = lambda l, v, x0=xmin, z0=ymin, yy=y0, sc=scale: (40+(l-x0)*sc, yy+30+(v-z0)*sc)
            svg.text(25, y0, name, 16, "bold")
            svg.text(650, y0, "Blank L × depth × thickness: " + " × ".join(f"{x:.3f}" for x in profile["blank_mm"]) + " mm", 13)
            svg.polygon([project(*p) for p in draw.hull(points)], "#edf2f7", width=1)
            for row in (r for r in holes if r["receiver"] == name):
                p = vector(row, "entry_in_receiver", "luv")
                svg.cross(*project(p[0], p[2]), "")
            # Panel front-face layout is in L/U, unlike a timber broad face L/V.
            if profile["kind"] == "panel":
                svg.text(25, y0+113, "Panel side section only; front-face L/U machining is in panel-machining.csv.", 12)
            svg.text(25, y0+130, "Datum XYZ: " + ", ".join(f"{x:.3f}" for x in profile["datum_xyz_mm"]) + " mm", 12)
        result[f"member-projections-{page+1}.svg"] = svg.render().encode()
    svg = draw.SVG(1400, 760)
    svg.text(25, 35, "Both exterior cleats: sloped top / runner seat", 24, "bold")
    svg.text(25, 63, "Nominal source coordinates. Each cleat is 38.1 mm thick across X; this is a dimensioned overview.", 14)
    project = lambda y, z: (80+(y+175.7)*1.2, 535-(z-139.7)*1.2)
    svg.polygon([project(y, z) for y, z in extension["new_cleat_YZ_polygon_mm"]], "#e1f1e5", width=2)
    for i, (y, z) in enumerate(extension["new_cleat_YZ_polygon_mm"]):
        x, yy = project(y, z)
        svg.text(x+8, yy-8, f"P{i+1}", 13)
        svg.text(620, 500+i*28, f"P{i+1}: Y {y:.3f}, Z {z:.3f} mm", 14)
    left_axes = [a for a in extension["axes"] if "eoere_cleat_left" in a["receivers"]]
    for axis, label_y in zip(left_axes, [270, 315, 465, 510], strict=True):
        _, y, z = axis["point_xyz_mm"]
        point = project(y, z)
        svg.cross(*point, "", False)
        svg.line(point, (350, label_y-5), "#9a3140", .8)
        svg.text(360, label_y, axis["id"], 13, color="#9a3140")
    for i, text in enumerate([
        "Blank: 361.186 × 139.700 × 38.100 mm (14.220 × 5.5 × 1.5 in)",
        "Rear edge height: 194.698 mm; front edge height: 361.186 mm",
        "Bottom seat: Z 139.700; top joins P4 to P3, matching the side edge",
        "Left X: -1257.300 to -1219.200 mm",
        "Right X: 1216.025 to 1254.125 mm",
        "Dedicated post shafts stay at Z 200.000 in the reviewed model.",
        "HOLD those four stations: nominal bore/screw gap only 0.341 mm.",
        "No axis move, hole diameter or woodworking tolerance adopted here.",
        "Use receiver-holes.csv for all local coordinates and directions.",
    ]):
        svg.text(620, 145+i*36, text, 14, color="#9a3140" if i == 6 else "#223044")
    svg.text(25, 710, "The two sides use their own X datums and opposite installed bolt directions. Do not mirror head/nut roles.", 14)
    svg.text(25, 735, "No cutting/drilling release; tool access, practical fit and complete joint behavior remain open.", 14)
    result["extended-cleats.svg"] = svg.render().encode()
    svg = draw.SVG(1300, 760)
    svg.text(25, 35, "Rear leg inner-face recess: full depth plus 1:12 return", 24, "bold")
    svg.text(25, 64, "Section in L / removal depth d. L is measured along grain from the rear foot heel B.", 15)
    a, b = recesses[0]["start_from_rear_heel_L_mm"], recesses[0]["finish_from_rear_heel_L_mm"]
    project = lambda l, d: (90+l*1.55, 150+d*4)
    svg.polygon([project(0, 0), project(0, 38.1), project(a, 38.1), project(b, 0)], "#fff0d9", width=2)
    for l, label in [(0, "Heel B: L0"), (a, f"Full depth ends L{a:.3f}"), (b, f"Return ends L{b:.3f}")]:
        x, y = project(l, 0)
        svg.line((x, 125), (x, 330), dashed=True)
        svg.text(x-40, 360, label, 14)
    svg.text(400, 103, "d = 38.100 mm; remaining thickness = 50.800 mm", 16)
    svg.text(600, 330, "457.200 mm run / 38.100 mm depth = 12:1", 16)
    svg.text(25, 410, "Relief-cut depth stations (nominal; leave positive finishing stock, amount unresolved):", 17, "bold")
    for i, (l, d) in enumerate([(a, 38.1), (a+114.3, 28.575), (a+228.6, 19.05), (a+342.9, 9.525), (b, 0)]):
        svg.text(55+i*240, 445, f"L {l:.3f}: d {d:.3f}", 15)
    for i, text in enumerate([
        "Left inner face X=-1219.200: remove toward -X. Right inner face X=1216.025: remove toward +X.",
        "The right cutter already carries its -3.175-mm world-X offset. Do not apply that shift a second time.",
        "Z=141.700 sets runner clearance/taper start; do not stop this taper at that height or cut a square shoulder.",
        "Proposed method: supported, depth-controlled relief kerfs, then controlled hand-tool finishing to the plane.",
        "Saw model/depth controls, blade, shoe support, finishing tool and allowed cut error remain required inputs.",
        "This section is a depth definition, not a released jig or permission to cut. Raw foot bevel is a separate cut.",
    ]):
        svg.text(25, 500+i*38, text, 15)
    result["rear-recess.svg"] = svg.render().encode()
    panel_names = sorted(n for n, p in profiles.items() if p["kind"] == "panel")
    moved = {r["axis_id"] for r in screws if r["moved_by_rail_revision"]}
    for page in range(2):
        svg = draw.SVG(1300, 1500)
        svg.text(25, 35, f"Panel front-face machining datums {page+1}/2 | extra grid OFF", 24, "bold")
        svg.text(25, 64, "Nominal L/U coordinates; V is through thickness. Model circles are occupancy, not selected bits.", 15)
        for slot, name in enumerate(panel_names[page*3:(page+1)*3]):
            p = profiles[name]
            width = p["blank_mm"][0]
            front_v = -p["blank_mm"][2]
            front = [v for v in p["vertices_luv_mm"] if abs(v[2]-front_v) < 1e-5]
            require(len(front) >= 2, "panel front-section endpoints missing")
            low, high = min(v[1] for v in front), max(v[1] for v in front)
            y0 = 125+slot*455
            project = lambda l, u, yy=y0, lo=low, hi=high: (55+l*.30, yy+30+(hi-u)*.30)
            svg.text(25, y0, name, 19, "bold")
            svg.polygon([project(0, low), project(width, low), project(width, high), project(0, high)], "#f5f7fa")
            current = [r for r in machining if r[1] == name]
            colors = {"tnut": "#66788a", "light": "#bd8b0c", "conditional_screw_clearance": "#9a3140"}
            for row in current:
                identity, _, kind, diameter = row[:4]
                x, y = project(row[10], row[11])
                color = "#146dc1" if identity in moved else colors[kind]
                svg.items.append(f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{max(.8, diameter*.15):.4f}" fill="white" stroke="{color}" stroke-width=".8"/>')
            svg.text(500, y0+35, f"Front rectangle: L0 to {width:.3f}; U{low:.3f} to {high:.3f} mm", 15)
            svg.text(500, y0+65, "Datum XYZ: " + ", ".join(f"{v:.3f}" for v in p["datum_xyz_mm"]) + " mm", 14)
            svg.text(500, y0+95, "Gray = hold/T-nut; gold = light; red = Hillman; blue = revised Hillman", 14)
            svg.text(500, y0+125, "Coordinates and exact identities: panel-machining.csv. No print-to-size scale.", 14)
            for i, identity in enumerate(r[0] for r in current if r[0] in moved):
                svg.text(500, y0+160+i*24, "Moved: " + identity, 13, color="#146dc1")
            svg.text(500, y0+365, "Conditional 5-mm screw voids are model envelopes. Use owner lead-pilot policy.", 13)
        svg.text(25, 1480, "142 T-nuts, 132 original lights and 66 Hillman axes overall. Actual panel dimensions remain unobserved.", 14)
        result[f"panel-layout-{page+1}.svg"] = svg.render().encode()
    svg = draw.SVG(1300, 850)
    svg.text(25, 35, "Matched leg/runner and leg/side drilling: fixture requirements", 24, "bold")
    svg.text(25, 64, "Concept sections along the drill axis; nominal guide/backer sizes are planning choices, not verified tooling.", 15)
    for yy, title, segments, wood, entry in [
        (170, "Lower pair R1/R2", [("Guide", 19.05), ("Runner", 38.1), ("Recessed leg", 50.8), ("Backer", 6.35)], 88.9, "left entry X=-1219.200, drill toward -X"),
        (360, "Upper pair U1/U2", [("Guide", 19.05), ("Side", 88.9), ("Leg", 88.9), ("Backer", 6.35)], 177.8, "left entry X=-1130.300, drill toward -X"),
    ]:
        svg.text(25, yy-35, f"{title}: {entry}", 18, "bold")
        x = 50
        for label, thickness in segments:
            svg.rect(x, yy, thickness*3.5, 65)
            svg.text(x+3, yy-10 if thickness < 10 else yy+26, label, 13)
            svg.text(x+3, yy+49, f"{thickness:.2f}", 10 if thickness < 10 else 13)
            x += thickness*3.5
        svg.line((35, yy+32.5), (x+25, yy+32.5), "#9a3140", 2)
        svg.text(50, yy+99, f"Wood {wood:.3f} mm; guide + wood + 6.35-mm breakout/backer travel = {wood+25.4:.3f} mm.", 16)
    for i, text in enumerate([
        "Locate both members at their finished contact faces and end datums; use positive stops plus separate clamps.",
        "Provide coplanar support to each relevant face. Projected Y/Z overlap does not mean members lie flat together.",
        "Hold one registered two-hole setup between holes. Fit metal bushings to the chosen bit; no steel-angle drilling.",
        "Bit cutting length, free projection below chuck, guide retention and complete chuck/clamp travel must all fit.",
        "An 8-inch overall bit does not establish 203.200-mm upper-stack usable reach. Controlled transfer is a separate route.",
        "Head/nut orientation stays per access-sides.csv. Drilling entry does not reverse the installed bolt.",
        "Upper/lower target coordinates remain in the preserved left-corner sheets, authenticated by current member hashes.",
        "Right member/axis datums are in current CSVs. Left paper sheets are not right-side mirroring instructions.",
    ]):
        svg.text(25, 535+i*36, text, 15)
    result["paired-drilling-fixture.svg"] = svg.render().encode()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--out", type=Path, help="Write to a new empty output directory")
    action.add_argument("--check", action="store_true", help="Replay and compare issued companion bytes")
    args = parser.parse_args()
    if args.out is not None:
        require(not args.out.exists() or not any(args.out.iterdir()), "output directory must be fresh/empty")
    outputs, result = build()
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        for name, raw in outputs.items():
            (args.out / name).write_bytes(raw)
    else:
        for name, raw in outputs.items():
            require((OWN / name).read_bytes() == raw, f"issued bytes differ: {name}")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "verification": result["verification"], "bytes": sum(map(len, outputs.values())),
                      "mass_kg": result["nominal_mass"]["conditional_total_kg"]}, sort_keys=True))


if __name__ == "__main__":
    main()
