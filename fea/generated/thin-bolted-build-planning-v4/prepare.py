"""Pure frozen-data shop-coordinate join. No CAD, response or acceptance."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEAF = Path(__file__).resolve().parent
INPUT_SHA = "8b6eed3a371140233b18db0052091d543cf541735147e3b044aba0b4ef6f2075"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda x: fail(x))


def fail(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def vector(value):
    require(len(value) == 3, "three vector coordinates required")
    value = [float(x) for x in value]
    require(all(math.isfinite(x) for x in value), "nonfinite vector")
    return value


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def scale(a, factor):
    return [x * factor for x in a]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def unit(a):
    a = vector(a)
    norm = math.sqrt(dot(a, a))
    require(norm > 1e-12, "zero vector")
    return scale(a, 1 / norm)


def proper(basis):
    basis = [vector(v) for v in basis]
    require(len(basis) == 3, "three basis vectors required")
    error = max(abs(dot(a, b) - (i == j)) for i, a in enumerate(basis)
                for j, b in enumerate(basis))
    require(error < 1e-8 and dot(cross(basis[0], basis[1]), basis[2]) > 1 - 1e-8,
            "improper grain/reference basis")
    return basis


def local(point, datum, basis):
    return [dot(sub(point, datum), b) for b in basis]


def hull(vertices):
    """Supporting facets of the small convex raw stock; reject nonconvex reuse by volume."""
    vertices = [vector(p) for p in vertices]
    require(len(vertices) >= 4, "insufficient profile vertices")
    center = [math.fsum(p[i] for p in vertices) / len(vertices) for i in range(3)]
    planes = []
    for a, b, c in itertools.combinations(vertices, 3):
        normal = cross(sub(b, a), sub(c, a))
        norm = math.sqrt(dot(normal, normal))
        if norm < 1e-7:
            continue
        normal = scale(normal, 1 / norm)
        offset = dot(normal, a)
        distances = [dot(normal, p) - offset for p in vertices]
        if max(distances) > 1e-6 and min(distances) < -1e-6:
            continue
        if dot(normal, center) > offset:
            normal, offset = scale(normal, -1), -offset
        if any(dot(normal, n) > 1 - 1e-9 and abs(offset - d) < 1e-5
               for n, d in planes):
            continue
        planes.append((normal, offset))
    require(len(planes) >= 4, "degenerate profile hull")
    volume = 0.
    facets = []
    for normal, offset in planes:
        indices = [i for i, p in enumerate(vertices) if abs(dot(normal, p) - offset) < 1e-5]
        require(len(indices) >= 3, "degenerate supporting facet")
        face_center = [math.fsum(vertices[j][i] for j in indices) / len(indices)
                       for i in range(3)]
        u = unit(sub(vertices[indices[0]], face_center))
        v = cross(normal, u)
        indices.sort(key=lambda i: math.atan2(dot(sub(vertices[i], face_center), v),
                                             dot(sub(vertices[i], face_center), u)))
        for i, j in zip(indices, indices[1:] + indices[:1], strict=True):
            area = dot(cross(sub(vertices[i], face_center), sub(vertices[j], face_center)), normal) / 2
            require(area >= -1e-7, "invalid convex facet winding")
            volume += area * (offset - dot(normal, center)) / 3
        facets.append({"outward_normal_xyz": normal, "offset_world_mm": offset,
                       "vertex_indices": indices})
    require(volume > 0 and math.isfinite(volume), "nonpositive hull volume")
    return facets, volume


def line_interval(point, direction, facets):
    low, high = -math.inf, math.inf
    for face in facets:
        n, offset = face["outward_normal_xyz"], face["offset_world_mm"]
        rate, reserve = dot(n, direction), offset - dot(n, point)
        if abs(rate) < 1e-10:
            require(reserve >= -1e-6, "line misses raw stock")
        elif rate > 0:
            high = min(high, reserve / rate)
        else:
            low = max(low, reserve / rate)
    require(math.isfinite(low) and math.isfinite(high) and high >= low - 1e-6,
            "empty or unbounded raw-stock line")
    return [low, high]


def profile_record(name, source, cached, basis):
    basis = proper(basis)
    shift = [0., math.sin(math.radians(40)) * 50.8, math.cos(math.radians(40)) * 50.8]
    if not name.startswith("base_rail_bottom_"):
        shift = [0., 0., 0.]
    vertices = [add(vector(p), shift) for p in source["vertices_world_mm"]]
    bounds = [[min(p[i] for p in vertices), max(p[i] for p in vertices)] for i in range(3)]
    error = max(abs(a - b) for pair, expected in zip(bounds, cached["bounds_xyz_mm"], strict=True)
                for a, b in zip(pair, expected, strict=True))
    require(error < 1e-6, "current raw bounds mismatch: " + name)
    facets, volume = hull(vertices)
    volume_error = abs(volume - cached["volume_mm3"])
    require(volume_error < max(.001, cached["volume_mm3"] * 1e-9),
            "current raw profile volume mismatch: " + name)
    require(abs(dot(unit(cached["grain_axis_xyz"]), basis[0])) > 1 - 1e-8,
            "cached nominal grain mismatch")
    # This is a real source vertex; an axis-aligned bounding-box corner is never invented.
    index = min(range(len(vertices)), key=lambda i: tuple(dot(vertices[i], b) for b in basis))
    datum = vertices[index]
    points = [local(p, datum, basis) for p in vertices]
    cuts = []
    for face in facets:
        normal = [dot(face["outward_normal_xyz"], b) for b in basis]
        if abs(normal[0]) > 1e-8:
            cuts.append({"outward_normal_luv": normal,
                         "offset_from_datum_mm": face["offset_world_mm"] - dot(face["outward_normal_xyz"], datum),
                         "vertex_indices": face["vertex_indices"],
                         "normal_to_nominal_grain_deg": math.degrees(math.acos(min(1., abs(normal[0]))))})
    return {"member": name, "blank_mm": source["stock_blank_allowance_mm"],
            "datum_xyz_mm": datum, "datum_source_vertex_index": index,
            "basis_grain_u_v_xyz": basis, "raw_profile_vertices_luv_mm": points,
            "end_cut_planes": cuts, "raw_source_translation_xyz_mm": shift,
            "bounds_error_mm": error, "raw_volume_error_mm3": volume_error,
            "raw_native_body": {k: cached[k] for k in ("path", "sha256", "volume_mm3")}}, facets


def washers(axis, changes):
    h = axis["hardware_scenario"]
    default = [h["washer_od_mm"], h["washer_id_mm"], h["washer_thickness_mm"]]
    result = []
    for role in ("head_washer", "nut_washer"):
        change = changes.get((axis["id"], role))
        result.append([change[k] for k in ("od_mm", "id_mm", "thickness_mm")] if change else default[:])
    return result


def stack(axis, washer_pair, product, nut_max_mm):
    head, nut = washer_pair
    h = axis["hardware_scenario"]
    near = head[2] + axis["before_plate_mm"] + axis["grip_mm"] + axis["after_plate_mm"] + nut[2]
    length = axis["nominal_under_head_length_mm"]
    pitch = 25.4 / h["threads_per_inch"]
    tip = length - near - h["nut_height_mm"]
    require(abs(tip - axis["tip_projection_beyond_nut_mm"]) < 1e-6, "nominal stack replay mismatch")
    short = length + product["length_tolerance_in"][0] * 25.4
    return {"nut_near_underhead_mm": near, "tip_nominal_mm": tip,
            "pitch_mm": pitch, "minimum_two_tip_thread_length_mm": near + h["nut_height_mm"] + 2 * pitch,
            "comparison_product": product["product"],
            "comparison_shortest_underhead_mm": short,
            "comparison_shortest_tip_threads_frozen_stack": (short - near - h["nut_height_mm"]) / pitch,
            "comparison_shortest_tip_threads_frozen_washers_nut_max": (short - near - nut_max_mm) / pitch,
            "comparison_two_tip_margin_mm_frozen_washers_nut_max": short - near - nut_max_mm - 2 * pitch}


def thread_exposure(intervals, lb_min, lg_max):
    require(all(math.isfinite(x) for pair in intervals for x in pair), "nonfinite bearing interval")
    require(all(high > low for low, high in intervals), "empty bearing interval")
    length = math.fsum(high - low for low, high in intervals)
    return [length, math.fsum(max(0., high - max(low, lg_max)) for low, high in intervals),
            math.fsum(max(0., high - max(low, lb_min)) for low, high in intervals)]


def receiving_planes(axis, receiver_map, seats):
    """Each washer retains its own receiving body/flange and geometric pressure datum."""
    p, d = vector(axis["point"]), vector(axis["direction"])
    result = []
    for role, plate, wood_station, station, inward in (
        ("head_washer", axis["before_plate_mm"], 0., -axis["before_plate_mm"], d),
        ("nut_washer", axis["after_plate_mm"], axis["grip_mm"], axis["grip_mm"] + axis["after_plate_mm"], scale(d, -1)),
    ):
        owners = []
        if plate > 0:
            for attached in axis["attachments"]:
                projected = dot(sub(attached["entry_xyz_mm"], p), d)
                if abs(projected - wood_station) < 1e-5:
                    projected_point = add(p, scale(d, projected / dot(d, d)))
                    require(math.sqrt(dot(sub(attached["entry_xyz_mm"], projected_point),
                                          sub(attached["entry_xyz_mm"], projected_point))) < 1e-5,
                            "washer flange entry is not on its own shaft")
                    expected = 1 if role == "head_washer" else -1
                    require(abs(dot(attached["axis_xyz"], d) - expected) < 1e-8,
                            "own flange normal disagrees with washer side")
                    owners.append([attached["angle_id"], attached["flange"]])
        else:
            for member in axis["receivers"]:
                proof = receiver_map[(axis["id"], member)][1]
                intervals = proof["finished_full_wall_intervals_from_axis_point_mm"]
                endpoint = min(a for a, _ in intervals) if role == "head_washer" else max(b for _, b in intervals)
                if abs(endpoint - wood_station) < 1e-5:
                    owners.append([member, "finished_outer_face"])
        require(len(owners) == 1, "own washer receiving ownership is ambiguous")
        source = seats[(axis["id"], role)]
        require(source["support_material"] == ("steel" if plate > 0 else "wood"), "washer material ownership mismatch")
        result.append([axis["id"], role, source["support_material"], owners[0],
                       add(p, scale(d, station)), inward, source["planned_support_opening_mm"]])
    return result


def verify_pins(pins, root=ROOT):
    for path, digest in pins.items():
        require(sha(root / path) == digest, "source pin mismatch: " + path)


def prepare(input_path=LEAF / "input.json"):
    method_before, test_before = sha(__file__), sha(LEAF / "test_prepare.py")
    require(sha(input_path) == INPUT_SHA, "input byte binding mismatch")
    input_data = load(input_path)
    pins = input_data["source_sha256"]
    verify_pins(pins)
    paths = input_data["source_paths"]
    data = {key: load(ROOT / value) for key, value in paths.items() if value.endswith(".json")}
    layout, native, integrated = data["layout"], data["native"], data["integrated"]
    raw = {r["member"]: r for r in native["raw_parts"]}
    frames = {}
    for r in data["frames"]["member_element_actions"]:
        name, basis = r["member"], proper(r["basis_grain_u_v_xyz"])
        require(name not in frames or frames[name] == basis, "member frame differs between elements")
        frames[name] = basis
    require(len(raw) == 20 and set(raw) == set(frames), "20-member geometry census mismatch")
    axes, screws, fitting_rows = layout["installed_axes"], layout["screw_axes"], layout["raw_fittings"]
    require((len(axes), len(screws), len(fitting_rows)) == (70, 66, 36), "hardware census mismatch")
    require(len({a["id"] for a in axes}) == 70, "duplicate physical shaft")
    profiles, facets = {}, {}
    for name, cached in sorted(raw.items()):
        profiles[name], facets[name] = profile_record(name, data["profiles"][name], cached, frames[name])
    old = data["old_primary"]
    products = {key: {**value, "product": int(key)} for key, value in input_data["new_primary_observations"].items()}
    products.update({str(old[k]["product"]): old[k] for k in ("bolt_3in", "bolt_5in")})
    windows = {r["axis_id"]: r for r in data["standard_windows"]["product_standard_thread_windows"]["current70nominal_length_scenarios"]}
    receivers = data["receivers"]["finished_geometry_queries"]["receiver_boundary_geometry"]
    require(len(receivers) == 82, "82-receiver census mismatch")
    receiver_map = {(r["axis_id"], r["member"]): (i, r) for i, r in enumerate(receivers)}
    require(len(receiver_map) == 82, "duplicate receiver proof")
    changes = {(r["axis_id"], r["role"]): r for r in layout["small_washer_changes"]}
    require(len(changes) == 14, "small-washer census mismatch")
    seats = {(r["axis_id"], r["role"]): r for r in layout["washer_seats"]}
    require(len(seats) == 140, "washer seat census mismatch")
    axis_rows, bearing_rows, steel_bearing_rows, fitting_holes = [], [], [], []
    seat_rows = []
    max_interval_error = 0.
    corrected_head_offsets = []
    for axis in axes:
        name = axis["id"]
        pair = washers(axis, changes)
        d, p = vector(axis["direction"]), vector(axis["point"])
        require(abs(dot(d, d) - 1) < 1e-8, "nonunit shaft direction")
        length, diameter = axis["nominal_under_head_length_mm"], axis["diameter_mm"]
        product_key = {(12.7, 76.2): "397", (12.7, 127.): "401", (12.7, 203.2): "407",
                       (9.525, 101.6): "367", (9.525, 114.3): "368"}[(diameter, length)]
        nut_max = old["nut"]["height_in"][1] * 25.4 if diameter == 12.7 else products["2571"]["height_in"][1] * 25.4
        fitted = stack(axis, pair, products[product_key], nut_max)
        seat_rows.extend(receiving_planes(axis, receiver_map, seats))
        own_offset = pair[0][2] + axis["before_plate_mm"]
        window = windows[name]
        require(window["nominal_CAD_length_mm"] == length, "stale length window")
        delta = pair[0][2] - window["washer_thickness_scenario_mm"]
        if abs(delta) > 1e-10:
            corrected_head_offsets.append([name, delta])
        underhead = add(p, scale(d, -own_offset))
        last_bearing = 0.
        for material_row in window["all_bearing_members"]:
            if material_row["material"] != "steel":
                continue
            intervals = [[a + delta, b + delta] for a, b in material_row["underhead_bearing_intervals_mm"]]
            last_bearing = max(last_bearing, max(b for _, b in intervals))
            steel_bearing_rows.append([name, material_row["member"], intervals,
                                       thread_exposure(intervals, window["standard_Lbmin_mm"], window["standard_Lgmax_mm"])])
        for member in axis["receivers"]:
            index, proof = receiver_map[(name, member)]
            actual = proof["finished_full_wall_intervals_from_axis_point_mm"]
            raw_interval = line_interval(p, d, facets[member])
            interval_error = max(abs(a - b) for a, b in zip(raw_interval, proof["raw_member_axis_interval_from_axis_point_mm"], strict=True))
            max_interval_error = max(max_interval_error, interval_error)
            require(interval_error < 2e-5, "raw receiver line replay mismatch")
            intervals = [[a + own_offset, b + own_offset] for a, b in actual]
            require(all(a >= raw_interval[0] - 1e-5 and b <= raw_interval[1] + 1e-5 for a, b in actual),
                    "finished bearing leaves authenticated raw profile")
            datum, basis = profiles[member]["datum_xyz_mm"], frames[member]
            endpoints = [[local(add(p, scale(d, a)), datum, basis),
                          local(add(p, scale(d, b)), datum, basis)] for a, b in actual]
            exposure = thread_exposure(intervals, window["standard_Lbmin_mm"], window["standard_Lgmax_mm"])
            last_bearing = max(last_bearing, max(b for _, b in intervals))
            bearing_rows.append([name, member, index, intervals, endpoints,
                                 math.degrees(math.acos(min(1., abs(dot(unit(d), basis[0]))))),
                                 exposure, proof["sampled_minimum_distances_to_first_finished_boundary_mm"]])
        axis_rows.append({"axis_id": name, "source": axis["source"], "point_xyz_mm": p,
                          "direction_xyz": d, "nominal_D_L_bore_mm": [diameter, length, axis["bore_diameter_mm"]],
                          "own_underhead_xyz_mm": underhead, "washers_OD_ID_t_mm": pair,
                          "modeled_collision_head_H_nut_H_AF_mm": [axis["hardware_scenario"][k] for k in ("head_height_mm", "nut_height_mm", "hex_across_flats_mm")],
                          "plate_near_far_grip_mm": [axis["before_plate_mm"], axis["after_plate_mm"], axis["grip_mm"]],
                          "stack": fitted, "conditional_ASME_Lbmin_Lgmax_mm": [window["standard_Lbmin_mm"], window["standard_Lgmax_mm"]],
                          "full_smooth_body_to_cover_every_bearing_mm": last_bearing,
                          "smooth_body_and_full_thread_nut_reach_gap_mm": fitted["nut_near_underhead_mm"] - last_bearing})
        for attached in axis["attachments"]:
            fitting_holes.append([name, attached["angle_id"], attached["duty_id"], attached["flange"], attached["receiver"],
                                  attached["offset_from_assumed_outer_corner_mm"], attached["width_edge_distance_mm"]])
    require((len(bearing_rows), len(steel_bearing_rows), len(fitting_holes), len(seat_rows)) == (82, 72, 72, 140),
            "joined ownership census mismatch")
    screw_rows = []
    for row in screws:
        member, p, d = row["receiver"], vector(row["origin_xyz_mm"]), vector(row["direction_xyz"])
        screw_rows.append([row["axis_id"], row["panel"], member, p, d,
                           local(p, profiles[member]["datum_xyz_mm"], frames[member]),
                           [dot(d, b) for b in frames[member]], row["conditional_raw_wood_penetration_body_fraction"]])
    fittings = [[r["angle_id"], r["duty_id"], r["beam"], r["post"], r["origin_xyz_mm"],
                 proper([r["u_xyz"], r["v_xyz"], r["w_xyz"]]), r["used_holes"]] for r in fitting_rows]
    # Metadata from the selected sheet is unshifted; the current V4 model explicitly shifts the right cutter.
    taper = []
    for name, old_taper in data["taper"].items():
        dx = -3.175 if name.endswith("right") else 0.
        cut = [[x + dx, s] for x, s in old_taper["cut_profile_xs_mm"]]
        recess = next(r for r in layout["recess_cuts"] if r["receiver"] == name)
        require(abs(old_taper["expected_removed_volume_mm3"] - recess["removed_volume_mm3"]) < 1e-4,
                "recess recipe volume differs from current layout")
        taper.append({"member": name, "cut_profile_world_x_global_grain_s_mm": cut,
                      "right_cutter_translation_xyz_mm": [dx, 0., 0.], "grain_xyz": old_taper["grain_axis_xyz"],
                      "normal_xyz": old_taper["normal_axis_xyz"], "top_bottom_world_z_mm": [old_taper["notch_top_z_mm"], 0.],
                      "taper_run_maxdepth_mm": [old_taper["taper_run_mm"], old_taper["max_recess_depth_mm"]],
                      "recorded_current_removed_volume_mm3": recess["removed_volume_mm3"],
                      "nominal_vertical_clearance_mm": 2., "nominal_transverse_clearance_mm": 0.})
    access = data["access"]
    # Reuse existing quantities/cost/access by exact paths and JSON keys, rather than duplicate the tables.
    report = {"schema": "thin_bolted_joined_shop_geometry/v1", "candidate": layout["candidate"],
              "layout_raw_sha256": pins[paths["layout"]],
              "scope": "Current V4 nominal construction coordinates and unselected hardware comparisons only. No physical fabrication instruction, product qualification, load field, resistance or acceptance.",
              "counts": {"timbers": 20, "panels": 6, "fittings": 36, "physical_bolts": 70,
                         "timber_bolt_receivers": 82, "fitting_hole_ownerships": 72, "Hillman_42605_axes": 66,
                         "small_washer_roles": 14},
              "datum_convention": "The authenticated source vertex minimizing lexicographic global grain/U/V projections; signed proper L/U/V coordinates. Each member has its own explicit world datum. U/V are reference directions, not observed radial/tangential growth-ring axes.",
              "raw_profile_reuse": "Pinned kerf-right uncut_wood_parts() vertices through floor_flush_construction, floor_flush_width, thin_bolted_candidate.geometry(), layout_revision.row_layout(). Only the two bottom rails receive +50.8 mm*T; header-row shift changes fittings. Convex facet volume and current native raw bounds are independently replayed. No baseline shop pass is transferred.",
              "members": list(profiles.values()), "axes": axis_rows,
              "bearing_columns": ["axis_id", "member", "finished_receiver_source_index", "own_underhead_finished_fullwall_intervals_mm",
                                  "entry_exit_luv_mm", "shaft_to_nominal_grain_deg", "bearing_length_minthread_maxthread_mm",
                                  "five_probe_minimum_first_finished_boundary_distances_mm"],
              "bearing_rows": bearing_rows,
              "steel_bearing_columns": ["axis_id", "near_or_far_steel_side", "own_underhead_bearing_intervals_mm", "bearing_length_minthread_maxthread_mm"],
              "steel_bearing_rows": steel_bearing_rows,
              "washer_receiving_plane_columns": ["axis_id", "washer_role", "receiving_material", "own_body_and_flange", "pressure_datum_xyz_mm", "inward_toward_receiver_xyz", "modeled_support_opening_mm"],
              "washer_receiving_plane_rows": seat_rows,
              "fitting_columns": ["angle_id", "duty_id", "beam", "post", "origin_xyz_mm", "basis_u_v_w_xyz", "used_holes"],
              "fittings": fittings,
              "fitting_hole_columns": ["axis_id", "angle_id", "former_angle_duty_id", "flange", "receiver", "assumed_outer_corner_hole_offset_mm", "nominal_width_edge_mm"],
              "fitting_hole_rows": fitting_holes,
              "screw_columns": ["axis_id", "panel", "receiver", "origin_xyz_mm", "direction_xyz", "origin_receiver_luv_mm", "direction_receiver_luv", "nominal_raw_receiver_fraction"],
              "Hillman_axes": screw_rows,
              "Hillman_policy": {"purchased_product": "Hillman 42605 #10 x 2.5 in", "count": 66, "nominal_purchased_length_mm": 63.5,
                                  "modeled_panel_thickness_mm": integrated["panel_screw_receiver_support"][0]["panel_thickness_mm"],
                                  "nominal_length_after_panel_mm": integrated["panel_screw_receiver_support"][0]["body_penetration_length_mm"],
                                  "true_thread_length_root_head_profile_or_resistance": None,
                                  "pilot_countersink": "Owner-selected lead-hole and face countersink policy is retained in baseline shop checklist; this join specifies no drill size or receiver pilot and transfers no Hillman capacity from SDS/SPAX."},
              "recesses": taper,
              "reused_tables": {"stock_cut_nesting_panels": [paths["access"], "takeoff.stock"],
                                "hardware_quantities_washers": [paths["access"], "takeoff.hardware_counts/takeoff.washer_envelopes"],
                                "cost_mass": [paths["access"], "takeoff.cost/takeoff.mass"],
                                "finished_body_volumes": [paths["integrated"], "finished_stock"],
                                "panel_hold_LED_holes": [paths["integrated"], "panel_machining.features"],
                                "wire_cuts_and_endpoints": [paths["layout"], "wire_proposals/service_cuts"],
                                "washer_opening_backing_ownership": [paths["layout"], "washer_seats"],
                                "all_five_depth_finished_boundary_witnesses": [paths["receivers"], "finished_geometry_queries.receiver_boundary_geometry"]},
              "nominal_disassembly": {"preconditions": access["front_release"]["conditions"],
                                      "sequence": data["free_fittings"]["sequence"],
                                      "physical_bolt_dependency_rows": access["bolt_release_sequence"]["dependency_rows"],
                                      "metal_role_order": access["bolt_release_sequence"]["operation_order_per_axis"],
                                      "exact_route_sources": [[paths["access"], "front_release/compact_pass_through_tool/bolt_release_sequence/member_release"],
                                                             [paths["free_fittings"], "free_fitting_release_rows"]],
                                      "assembly": "Reverse authenticated initial-separation routes and dependency ordering on separately supported unloaded members; support stability, complete hand/tool paths and actual installation/torque remain unresolved."},
              "verification": {"raw_member_bounds_max_error_mm": max(r["bounds_error_mm"] for r in profiles.values()),
                               "raw_member_volume_max_error_mm3": max(r["raw_volume_error_mm3"] for r in profiles.values()),
                               "raw_receiver_line_max_error_mm": max_interval_error,
                               "old_generic_to_own_small_head_offsets_mm": corrected_head_offsets,
                               "nominal_tip_stack_replay_count": len(axis_rows)},
              "dimensional_issues": {"shortest_priced_8inch_comparison": [r["axis_id"] for r in axis_rows if r["stack"]["comparison_two_tip_margin_mm_frozen_washers_nut_max"] < 0],
                                     "tightest_nominal_stock_remainder_mm": min(r["remaining_mm"] for r in access["takeoff"]["stock"]["sticks"]),
                                     "panel": "Main kerf-right blanks consume nominal 4x8 sheet width/length with no trimming allowance; bought true 4x4 faces are 1.5875 mm wider each. Delivered usable sizes are unverified; no substitution/geometry change is adopted.",
                                     "starting_washers": "8 half-inch and 16 three-eighth-inch retained washers have frozen envelopes without qualified delivered SKUs; the numerical half-inch OD is 34.925 mm, although obsolete source prose says 38.1 mm.",
                                     "fittings": "Model uses 7/32 in flat plates and sharp heels. B103 current SKU says 1/4 in with conflicting dimensions; B104 SKU/catalog weight differs. Actual formed radius, minimum thickness, hole/flat tolerances and certificates are unresolved.",
                                     "selected_right_taper": "Unshifted selected-sheet right cutter metadata/retained vertices cannot be used directly. This table applies the current model's explicit -3.175 mm cutter translation; original source bytes remain unchanged."},
              "missing_mechanics": ["Current linear-field physical applicability is unqualified; large relative motions change contact branches.",
                                    "Complete joint/contact response, timber crushing/grain-angle limits/splitting/groups/net-sections, shared shafts, actual washer bending/pressure footprint, heel/holes/prying and product capacities remain unresolved.",
                                    "Nominal von-Mises/Fy markers and conditional NDS component references are different scopes; no common allowable threshold or manufacturer angle rating is established.",
                                    "Actual bolt smooth shank/root/runout, full-thread nut engagement and matched nut/washer/head face dimensions are required for the delivered stack. Published minimum thread lengths do not supply those measurements.",
                                    "No-slip floor, pads/friction and actual stock/part dimensions are unverified; no external anchor, preload, torque or friction value is inferred."],
              "claim_limits": ["CAD occupied bore/screw/head diameters are not drill-bit or countersink instructions.",
                               "Five finished-boundary probes and raw end planes are coordinates; they do not prove continuous NDS end/edge minima or signed/group duty classification.",
                               "Saved ASME windows remain a conforming-standard hypothesis; twelve small-head own offsets are explicitly corrected, and no old 70-axis thread classification is adopted. The full smooth-body length is a dimensional target conditional on choosing smooth body throughout every bearing interval, not a blanket NDS requirement.",
                               "No current/old q, force, history or resistance vector is consumed; the old 62-body packet supplies only member/reference frames and explicit dimensional-standard tables.",
                               "Washer planes describe own receiving geometry. The ideal circular head and solid nut remain collision envelopes; they supply no actual pressure footprint, nut bore, preload or friction.",
                               "No geometry, source, authority, load/material or view changed; no CAD/native/K/global solve or physical operation performed."],
              "source_sha256": pins, "input_sha256": INPUT_SHA,
              "primary_observation_source": str(Path(input_path).relative_to(ROOT)),
              "method_sha256": method_before, "test_sha256": test_before,
              "tool_versions": {"python": sys.version.split()[0], "implementation": sys.implementation.name, "dependencies": "stdlib only"},
              "reproduction_command": ".venv/bin/python fea/generated/thin-bolted-build-planning-v4/prepare.py --out /tmp/thin-v4-joined-shop-data.json",
              "source_pins_before_after_unchanged": True}
    verify_pins(pins)
    require(sha(input_path) == INPUT_SHA and sha(__file__) == method_before
            and sha(LEAF / "test_prepare.py") == test_before, "producer/test/input changed during preparation")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = prepare()
    blob = (json.dumps(report, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n").encode()
    args.out.open("xb").write(blob)
    print(json.dumps({"path": str(args.out), "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                      "counts": report["counts"], "verification": report["verification"]}))


if __name__ == "__main__":
    main()
