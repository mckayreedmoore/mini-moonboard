"""Review saved successor input arithmetic without CAD, assembly or a response.

Native face intersections and material probes remain source-produced evidence.
This checker independently joins their complete planar query census, conserves
cell area and first moments, and checks simple polygon/full-circle masks.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent
INPUT = LEAF / "mechanics-inputs-v1/inputs.json"
INPUT_SHA = "7a003cb7fe6d14a8644a3030b45caf96a7a4b59618d8c1703c3e3626f267d4b4"
EXTRACT = INPUT.with_name("extract.py")
EXTRACT_SHA = "b02cb1318518dda0949ac6175b72a130d5379a8ca45d4776ee22e540bd6769a4"
PLAN = INPUT.with_name("plan.json")
PLAN_SHA = "d398c68c2942ec2848711da46b01f405b39721e0386dd4bf087acb5c2ae8abca"
DOMAIN = ROOT / "fea/generated/thin-bolted-direct-contact-a12-v1/observer-isolation-v2/current-contact-v1/saved-face-domain-v1/face_domain.py"
DOMAIN_SHA = "b3807d1deaf3a54ba00f3e38e01903b99706d2043b6c311d4601c38b9e4bd16d"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "Changed source: " + path)


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, t):
    return [x * t for x in a]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    return scale(a, 1. / norm(a))


def near(a, b, tolerance=1e-8):
    if isinstance(a, (list, tuple)):
        require(len(a) == len(b), "Different vector lengths")
        error = max((near(x, y, tolerance) for x, y in zip(a, b, strict=True)), default=0.)
    else:
        require(math.isfinite(a) and math.isfinite(b), "Nonfinite scalar")
        error = abs(a - b)
        require(error <= tolerance, f"Arithmetic mismatch: {a}, {b}, tolerance {tolerance}")
    return error


def proper(rows):
    for i, a in enumerate(rows):
        near(norm(a), 1.)
        for j, b in enumerate(rows):
            near(dot(a, b), float(i == j))
    near(cross(rows[0], rows[1]), rows[2])


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def simple_mask(signature, normal):
    """One straight outer loop with disjoint full-circle holes, or unavailable.

    This narrow scalar check does not extend the preserved general decoder.
    Arc, spline and more complicated wire patterns retain native certificates.
    """
    edges = signature["edge_signatures"]
    if any(e["curve_type"] not in {"LINE", "CIRCLE"} for e in edges):
        return None
    circles = [e for e in edges if e["curve_type"] == "CIRCLE"]
    if any(len(e["vertex_xyz_mm"]) != 1 for e in circles):
        return None
    lines = [e for e in edges if e["curve_type"] == "LINE"]
    if not lines or signature["wire_count"] != len(circles) + 1:
        return None
    origin = lines[0]["vertex_xyz_mm"][0]
    u = unit(sub(lines[0]["vertex_xyz_mm"][1], origin))
    v = unit(cross(normal, u))
    def uv(p):
        return [dot(sub(p, origin), a) for a in (u, v)]
    remaining = [tuple(tuple(p) for p in e["vertex_xyz_mm"]) for e in lines]
    require(all(len(e) == 2 for e in remaining), "Straight mask edge needs two ends")
    points = [remaining[0][0], remaining[0][1]]
    remaining.pop(0)
    while remaining:
        candidates = [(i, b if a == points[-1] else a) for i, (a, b) in enumerate(remaining) if points[-1] in (a, b)]
        if len(candidates) != 1:
            return None
        index, following = candidates[0]
        points.append(following)
        remaining.pop(index)
    if points[-1] != points[0]:
        return None
    polygon = [uv(p) for p in points]
    products = [a[0] * b[1] - b[0] * a[1] for a, b in pairwise(polygon)]
    signed = math.fsum(products) / 2.
    require(abs(signed) > 1e-8, "Degenerate straight mask")
    centroid = [math.fsum((a[k] + b[k]) * c for a, b, c in zip(polygon[:-1], polygon[1:], products, strict=True)) / (6 * signed) for k in range(2)]
    def inside(p):
        return sum((a[1] <= p[1] < b[1] or b[1] <= p[1] < a[1]) and
                   a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) > p[0]
                   for a, b in pairwise(polygon)) % 2 == 1
    def line_distance(p, a, b):
        arm = sub(b, a)
        t = min(1., max(0., dot(sub(p, a), arm) / dot(arm, arm)))
        return norm(sub(p, add(a, scale(arm, t))))
    holes = [(uv(e["center_xyz_mm"]), e["length_mm"] / (2 * math.pi)) for e in circles]
    for i, (center, radius) in enumerate(holes):
        if not inside(center) or min(line_distance(center, a, b) for a, b in pairwise(polygon)) < radius - 2e-7:
            return None
        if any(norm(sub(center, c)) < radius + r - 2e-7 for c, r in holes[:i]):
            return None
    outer = abs(signed)
    area = outer - math.fsum(math.pi * r * r for _, r in holes)
    com = [(outer * centroid[k] - math.fsum(math.pi * r * r * c[k] for c, r in holes)) / area for k in range(2)]
    world_com = add(origin, add(scale(u, com[0]), scale(v, com[1])))
    def occupied(p):
        p = uv(p)
        boundary = min(line_distance(p, a, b) for a, b in pairwise(polygon)) <= 2e-7
        return (inside(p) or boundary) and all(norm(sub(p, c)) >= r - 2e-7 for c, r in holes)
    return {"area_mm2": area, "centroid_xyz_mm": world_com, "occupied": occupied}


def review():
    require(sha(INPUT) == INPUT_SHA and sha(EXTRACT) == EXTRACT_SHA and sha(PLAN) == PLAN_SHA, "Released input or extraction source changed")
    payload = INPUT.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == INPUT_SHA, "Released input changed while reading")
    inp = json.loads(payload)
    extractor = load_module(EXTRACT, "eoere_review_source_only_extractor")
    report, data, pins, panels = extractor.read_sources(extractor.REPORT_SHA)
    require(inp["source_sha256"] == pins and len(pins) == 328, "Input source closure differs from authentic extractor")
    pins = {**pins, str(INPUT.relative_to(ROOT)): INPUT_SHA, str(PLAN.relative_to(ROOT)): PLAN_SHA,
            str(OWN.relative_to(ROOT)): LOADED_SHA, str(DOMAIN.relative_to(ROOT)): DOMAIN_SHA}
    verify(pins)
    require(inp["schema"] == "eoere_first_order_mechanics_inputs/v1" and inp["scenario"] == extractor.SCENARIO
            and inp["parameters"] == extractor.PARAMETERS, "Different declared scenario")
    require(inp["readiness"] == {"complete_reference_contact_inventory": False, "independent_actual_extraction_review": None,
                                "source_joins_independently_reviewed": False}, "Input readiness was modified")
    require(all(v is False for v in inp["release"].values()), "Input release flag changed")
    require(inp["execution"]["parent_serialized_extraction_marker"] == "1"
            and "extract" in inp["execution"]["sys_orig_argv"], "Not the serialized extraction export")
    metrics = defaultdict(float)
    timber = {r["name"]: r for r in inp["timber_rows"]}
    profiles = {r["member"]: r for r in data["joined"]["members"]}
    profiles.update({"eoere_cleat_" + side: extractor.cleat_profile(side) for side in ("left", "right")})
    require(set(profiles) == set(timber) and len(timber) == 22, "Gross timber owner join")
    for name, p in profiles.items():
        r = timber[name]
        require(r["raw_profile_source"] == p and r["finished_cut_stiffness_or_resistance_qualified"] is False, "Gross profile qualification changed")
        basis = [unit(p["basis_grain_u_v_xyz"][i]) for i in (0, 1)]
        basis.append(unit(cross(*basis)))
        proper(basis)
        vertices = [add(p["datum_xyz_mm"], [math.fsum(a[k] * v for a, v in zip(basis, point, strict=True)) for k in range(3)]) for point in p["raw_profile_vertices_luv_mm"]]
        limits = [[min(dot(v, a) for v in vertices), max(dot(v, a) for v in vertices)] for a in basis]
        center = add(scale(basis[1], sum(limits[1]) / 2), scale(basis[2], sum(limits[2]) / 2))
        low, high = limits[0]
        if 1e-8 < abs(basis[0][2]) < 1 - 1e-8:
            low = (min(v[2] for v in vertices) - center[2]) / basis[0][2]
        expected = [add(center, scale(basis[0], s)) for s in (low, high)]
        metrics["gross_centerline_error_mm"] = max(metrics["gross_centerline_error_mm"], near([r["start"], r["end"]], expected))
        near([r["axis"], r["section_u"], r["section_v"]], basis)
        near([r["width_mm"], r["depth_mm"]], [limits[1][1] - limits[1][0], limits[2][1] - limits[2][0]])
    source_bodies = {r["id"]: r for r in [*report["finished_solids"], *panels]}
    observed = {r["id"]: r for r in inp["finished_body_observations"]}
    require(set(observed) == set(source_bodies) and len(observed) == 28, "Actual cached body census")
    for name, row in observed.items():
        require(row["source"] == source_bodies[name], "Cached body source differs")
        near(row["volume_mm3"], row["source"]["volume_mm3"], max(.01, row["volume_mm3"] * 1e-9))
        near(row["bounds_xyz_mm"], row["source"]["bounds_xyz_mm"], 1e-5)
        c = row["strict_container"]
        require(c["original_wrapper_unchanged"] and not c["extra_geometry_dropped"] and not c["location_or_orientation_reset"]
                and c["canonical_solid_topology_counts"]["solids"] == 1, "Imported container has a dropped or altered body")
        require(all(a <= p <= b for p, (a, b) in zip(row["center_xyz_mm"], row["bounds_xyz_mm"], strict=True)), "COM outside source box")
    axes = {a["id"]: a for a in report["axes"]}
    shafts = {a["axis_id"]: a for a in inp["shafts"]}
    walls = {(w["axis_id"], w["receiver"]): w for w in inp["finished_receiver_wall_queries"]}
    require(len(shafts) == 100 and set(shafts) == set(axes) and len(walls) == 120, "Shaft and receiver census")
    require(set(walls) == {(a["id"], r) for a in axes.values() for r in a["receivers"]}, "Receiver query omitted or duplicated")
    roles = {}
    for aid, axis in axes.items():
        shaft = shafts[aid]
        require(shaft["source_axis"] == axis and shaft["point"] == axis["point_xyz_mm"], "Own shaft source alias differs")
        g, h = unit(axis["direction_xyz"]), axis["hardware_scenario"]
        proper(shaft["basis"])
        near(shaft["basis"][0], g)
        near(shaft["diameter_mm"], axis["diameter_mm"])
        wood = []
        for receiver in axis["receivers"]:
            wall = walls[(aid, receiver)]
            require(not wall["partial_wall_present"] and wall["qualified_directional_bearing_length_mm"] is None, "Partial or qualified directional bearing promoted")
            accepted = []
            for face in wall["matching_cylindrical_faces"]:
                lo, hi = face["interval_mm"]
                theoretical = math.pi * axis["bore_diameter_mm"] * (hi - lo)
                near(theoretical, face["full_cylinder_area_mm2"], 1e-7)
                ratio = face["wall_area_mm2"] / theoretical
                near(ratio, face["circumference_integral_fraction"], 1e-12)
                require(face["full_circumference_wall"] == (abs(ratio - 1) <= 1e-6), "Full-wall area criterion differs")
                if face["full_circumference_wall"]:
                    accepted.append([lo, hi])
            require(len(accepted) == 1, "Unexpected full-wall partition needs separate review")
            near(accepted, wall["full_wall_intervals_mm"])
            clipped = [[max(0., lo), min(axis["grip_mm"], hi)] for lo, hi in accepted]
            near(clipped, wall["finished_full_wall_intervals_from_axis_point_mm"])
            near(sum(hi - lo for lo, hi in accepted), wall["full_wall_length_mm"])
            near(wall["grain_axis_xyz"], timber[receiver]["axis"])
            wood.extend((receiver, span) for span in clipped)
        actual_wood = [(s["host"], s["interval_mm"]) for s in shaft["surfaces"] if s["kind"] == "wood"]
        require(actual_wood == wood, "Actual finished bearing surface spans differ")
        steel = [s for s in shaft["surfaces"] if s["kind"] == "steel"]
        require(len(steel) == len(axis["attachments"]), "Steel bearing surface omitted")
        for s, b in zip(steel, axis["attachments"], strict=True):
            station = dot(sub(b["point"], axis["point_xyz_mm"]), g)
            interval = [-axis["before_plate_mm"], 0.] if abs(station) < 1e-5 else [axis["grip_mm"], axis["grip_mm"] + axis["after_plate_mm"]]
            require(s["host"] == b["angle_id"] and s["flange"] == extractor.port_id(b["flange"], b["transverse"])
                    and s["entry_xyz_mm"] == b["point"] and s["receiver"] == b["receiver"] and s["bore_diameter_mm"] == 10., "Steel own port or gap differs")
            near(s["interval_mm"], interval)
        for s in shaft["surfaces"]:
            near(s["bore_diameter_mm"], 10. if s["kind"] == "steel" else axis["bore_diameter_mm"])
        for end, index, support, sign in (("head", 0, -axis["before_plate_mm"], -1), ("nut", 1, axis["grip_mm"] + axis["after_plate_mm"], 1)):
            row = next(r for r in shaft["ends"] if r["end"] == end)
            candidates = [s for s in steel if abs(s["interval_mm"][index] - support) < 1e-5]
            if not candidates:
                target = 0. if end == "head" else axis["grip_mm"]
                candidates = [s for s in shaft["surfaces"] if s["kind"] == "wood" and abs(s["interval_mm"][index] - target) < 1e-5]
            require(len(candidates) == 1 and row["host"] == candidates[0]["host"] and row["flange"] == candidates[0].get("flange"), "External own capture host is ambiguous or wrong")
            near(row["support_s_mm"], support)
            near(row["pressure_face_s_mm"], support + sign * h["washer_thickness_mm"])
            near(row["direction_on_shaft_xyz"], scale(g, sign))
        start = -axis["before_plate_mm"] - h["washer_thickness_mm"]
        near(shaft["shaft_interval_mm"], [start, start + axis["nominal_under_head_length_mm"]])
        area = math.pi * axis["diameter_mm"] ** 2 / 4
        hexarea = 3 * (h["hex_across_flats_mm"] / math.sqrt(3)) ** 2 * math.sin(math.pi / 3)
        volumes = {"shaft": area * axis["nominal_under_head_length_mm"], "head": hexarea * h["head_height_mm"], "nut": (hexarea - area) * h["nut_height_mm"]}
        volumes.update({role: math.pi * (h["washer_od_mm"] ** 2 - h["washer_id_mm"] ** 2) * h["washer_thickness_mm"] / 4 for role in ("head_washer", "nut_washer")})
        stations = {"shaft": start + axis["nominal_under_head_length_mm"] / 2, "head": start - h["head_height_mm"] / 2,
                    "head_washer": start + h["washer_thickness_mm"] / 2, "nut_washer": axis["grip_mm"] + axis["after_plate_mm"] + h["washer_thickness_mm"] / 2,
                    "nut": axis["grip_mm"] + axis["after_plate_mm"] + h["washer_thickness_mm"] + h["nut_height_mm"] / 2}
        require({r["kind"] for r in shaft["metal_roles"]} == set(volumes), "Five metal roles required")
        for row in shaft["metal_roles"]:
            require(row["id"] == aid + "/" + row["kind"] and row["id"] not in roles, "Own metal role identity duplicated")
            metrics["role_volume_error_mm3"] = max(metrics["role_volume_error_mm3"], near(row["volume_mm3"], volumes[row["kind"]], 1e-8))
            near(row["mass_kg"], volumes[row["kind"]] * 7850e-9, 1e-12)
            near(row["center_of_mass_xyz_mm"], add(axis["point_xyz_mm"], scale(g, stations[row["kind"]])))
            roles[row["id"]] = (shaft["body"], row)
    require(len(roles) == 500 and sum(s["kind"] == "steel" for sh in shafts.values() for s in sh["surfaces"]) == 88, "Role or steel bearing census")

    # Every AABB candidate must have a recorded exact planar query disposition.
    names, panel_ids = sorted(timber), sorted(r["id"] for r in panels)
    pairs = [(a, b, "timber_face_contact") for i, a in enumerate(names) for b in names[i + 1:]] + [(a, b, "panel_contact") for a in panel_ids for b in names]
    def boxes_touch(a, b):
        return all(aa[0] <= bb[1] + 1e-5 and bb[0] <= aa[1] + 1e-5 for aa, bb in zip(observed[a]["bounds_xyz_mm"], observed[b]["bounds_xyz_mm"], strict=True))
    expected_pairs = {(a, b, kind) for a, b, kind in pairs if boxes_touch(a, b)}
    census = {(r["first"], r["second"], r["kind"]): r for r in inp["shared_pair_query_census"]}
    require(len(census) == len(inp["shared_pair_query_census"]) and set(census) == expected_pairs, "Complete planar pair query census differs")
    patches = inp["timber_and_panel_shared_face_patches"]
    require(Counter((p["first"], p["second"], p["kind"]) for p in patches) == Counter({k: v["patch_count"] for k, v in census.items() if v["patch_count"]}), "Positive patch count differs from query census")
    allpatches = patches + inp["flange_shared_face_patches"]
    require(len({p["id"] for p in allpatches}) == len(allpatches), "Duplicate native patch identity")
    contacts = {r["id"]: r for r in inp["direct_contacts"]}
    require(len(contacts) == len(inp["direct_contacts"]) == 1631, "Contact row duplicated or omitted")
    domains = {d["id"]: d for d in inp["flange_domains"]}
    bindings = {(b["angle_id"], b["model_port_id"]): b for b in inp["fitting_port_bindings"]}
    require(len(domains) == len(bindings) == 88, "Owned flange domain or port omitted")
    scene = json.loads((ROOT / extractor.SCENE).read_bytes())
    require(inp["all_factory_holes"] == scene["factory_angle_holes"], "Factory-hole source differs from final scene")
    flat_holes = [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
                  for angle in scene["factory_angle_holes"] for hole in angle["holes"]]
    require(inp["factory_holes"] == flat_holes and len(flat_holes) == 176
            and sum(h["used"] for h in flat_holes) == 88, "Complete 176-hole / 88-used factory census differs")
    source_bindings = [{**a, "model_port_id": extractor.port_id(a["flange"], a["transverse"]), "physical_axis_id": axis["id"]}
                       for axis in report["axes"] for a in axis["attachments"]]
    require(inp["hole_to_axis_port_bindings"] == source_bindings, "Source hole/shaft binding changed")
    poses = {p["id"]: p for p in inp["fitting_poses"]}
    scene_brackets = {p["id"]: p for p in scene["solids"] if p["fabrication"]["kind"] == "bracket"}
    require(len(poses) == 22 and set(poses) == set(scene_brackets), "All 22 source fitting poses required")
    for name, pose in poses.items():
        transform = scene_brackets[name]["transform"]
        source = [[transform[i], transform[i + 1], transform[i + 2]] for i in (0, 4, 8)]
        u = unit(source[0])
        v = unit(sub(source[1], scale(u, dot(source[1], u))))
        w = cross(u, v)
        proper([u, v, w])
        near([pose["u_xyz"], pose["v_xyz"], pose["w_xyz"]], [u, v, w])
        near(pose["origin_xyz_mm"], transform[12:15])
        near(pose["saved_scene_basis_columns_xyz"], source)
    for row in source_bindings:
        pose = poses[row["angle_id"]]
        along = pose["u_xyz"] if row["flange"] == "beam" else pose["v_xyz"]
        entry = add(pose["origin_xyz_mm"], add(scale(along, report["scenario"]["far_offset_mm"]),
                    scale(pose["w_xyz"], row["transverse"] * report["scenario"]["transverse_pitch_mm"] / 2)))
        metrics["loaded_four_port_entry_error_mm"] = max(metrics["loaded_four_port_entry_error_mm"], near(entry, row["point"]))
        b = bindings[(row["angle_id"], row["model_port_id"])]
        require(b["axis_id"] == row["physical_axis_id"] and b["entry_xyz_mm"] == row["point"]
                and b["source_flange"] == row["flange"] and b["source_transverse"] == row["transverse"], "Exact owned four-port datum differs")
    nominal = (report["scenario"]["leg_mm"] - report["scenario"]["thickness_mm"]) * report["scenario"]["width_mm"] - 4 * math.pi * (report["scenario"]["factory_hole_mm"] / 2) ** 2
    visited, simple_counts, complex_records = set(), Counter(), []
    for patch in allpatches:
        sig = patch["trimmed_region_geometry"]
        require(canonical(sig) == patch["trimmed_region_signature_sha256"] and sig["surface_type"] == "PLANE", "Trimmed signature hash or type differs")
        near(sig["area_mm2"], patch["area_mm2"], 2e-8)
        near(sig["center_xyz_mm"], patch["centroid_xyz_mm"], 2e-8)
        normal = patch["normal_from_second_to_first_xyz"]
        near(norm(normal), 1.)
        near(dot(patch["first_outward_normal_xyz"], normal), -1.)
        require(patch["coplanar_offset_mm"] <= 1e-5, "Patch is outside coplanar tolerance")
        for key, owner in (("source_first_face", patch["first"]), ("source_second_face", patch["second"])):
            face = patch[key]
            require(canonical(face["signature"]) == face["signature_sha256"] and face["face_id"].startswith(owner + "/step-face-"), "Owned native face identity or signature differs")
        area = math.fsum(c["area_mm2"] for c in patch["cells"])
        center = [math.fsum(c["area_mm2"] * c["point_xyz_mm"][i] for c in patch["cells"]) / area for i in range(3)]
        metrics["cell_area_error_mm2"] = max(metrics["cell_area_error_mm2"], near(area, patch["area_mm2"], max(1e-5, 1e-8 * area)))
        metrics["cell_centroid_error_mm"] = max(metrics["cell_centroid_error_mm"], near(center, patch["centroid_xyz_mm"], 1e-6))
        mask = simple_mask(sig, normal)
        if mask:
            metrics["simple_mask_area_error_mm2"] = max(metrics["simple_mask_area_error_mm2"], near(mask["area_mm2"], patch["area_mm2"], 1e-4))
            metrics["simple_mask_centroid_error_mm"] = max(metrics["simple_mask_centroid_error_mm"], near(mask["centroid_xyz_mm"], patch["centroid_xyz_mm"], 2e-7))
        else:
            complex_records.append({"patch_id": patch["id"], "source_trimmed_region_signature_sha256": patch["trimmed_region_signature_sha256"],
                                    "curve_types": sorted({e["curve_type"] for e in sig["edge_signatures"]}), "independent_analytic_mask": None})
        flange = patch not in patches
        domain_id = next((k for k in domains if patch["id"].startswith(k + "/")), None) if flange else None
        kind = "flange_contact" if flange else patch["kind"]
        for index, cell in enumerate(patch["cells"]):
            require(cell["both_inward_material_probes_occupied"] and cell["reference_centroid_on_trimmed_patch"]
                    and cell["reference_centroid_patch_distance_mm"] <= 1e-7 and cell["area_mm2"] > 0, "Native occupied cell certificate failed")
            if mask:
                require(mask["occupied"](cell["point_xyz_mm"]), "Simple native cell falls outside polygon or in a hole")
                simple_counts[kind] += 1
            cid = patch["id"] + f"/cell-{index}" if flange else cell["id"]
            require(cid not in visited and cid in contacts, "Physical cell identity duplicated or missing")
            visited.add(cid)
            row = contacts[cid]
            require((row["first"], row["second"], row["kind"]) == (patch["first"], patch["second"], kind), "Cell host ownership changed")
            near(row["point_xyz_mm"], cell["point_xyz_mm"])
            near(row["reference_area_mm2"], cell["area_mm2"])
            near(row["direction_xyz"], normal)
            require(row["source_trimmed_region_signature_sha256"] == patch["trimmed_region_signature_sha256"], "Cell mask source changed")
            if flange:
                d = domains[domain_id]
                require(row["first_port_id"] == d["model_port_id"] and row["source_domain_id"] == domain_id, "Loaded own strip port differs")
                near(row["nominal_full_holed_flange_area_mm2"], nominal)
                near(row["stiffness"], 40000 * cell["area_mm2"] / nominal)
            else:
                density = 1. if kind == "timber_face_contact" else 2.
                near(row["bedding_n_mm3"], density)
                near(row["stiffness"], density * cell["area_mm2"])
    require(visited == set(contacts), "An extra contact row lacks a native mask cell")
    for did, d in domains.items():
        near(d["nominal_full_holed_flange_area_mm2"], nominal)
        near(d["nominal_half_area_mm2"], nominal / 2)
        near(d["declared_flange_area_density_n_mm3"], 40000 / nominal)
        b = bindings[(d["fitting"], d["model_port_id"])]
        require(b["source_flange"] == d["source_flange"] and b["source_transverse"] == d["source_transverse"], "Owned port sign differs")
        owned = [p for p in inp["flange_shared_face_patches"] if p["id"].startswith(did + "/")]
        near(sum(p["area_mm2"] for p in owned), d["clipped_area_mm2"])
    floor_source = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/frame-contact-geometry-v4.json"
    old_footprints = json.loads(floor_source.read_bytes())["finished_floor_footprints"]
    require(inp["floor_footprints"] == old_footprints and len(old_footprints) == 8, "Actual finished floor datums differ; raw inner leg corners must stay excluded")
    for host, points in inp["floor_footprints"].items():
        require(host in timber and len(points) == len({tuple(p) for p in points}) == 4, "Whole floor host or corner missing")
        require(max(abs(p[2]) for p in points) <= 1e-6, "Unsapped floor plane exceeds source tolerance")
    original_screws = {r["axis_id"]: r for r in data["layout"]["screw_axes"]}
    require(len(inp["hillman_rows"]) == 66, "Hillman axis omitted")
    for row in inp["hillman_rows"]:
        s = original_screws[row["id"]]
        require(row["source_screw_descriptor"] == s and row["first"] == s["panel"] and row["second"] == s["receiver"], "Protected screw source changed")
        near(row["point_xyz_mm"], add(s["origin_xyz_mm"], scale(unit(s["direction_xyz"]), 18.25625 / 2)))
        proper(row["basis"])
        near(row["basis"][0], scale(unit(s["direction_xyz"]), -1))
        require(row["ka"] == row["kl"] == 1000. and row["tension_only"] and row["clearance"] == 0., "Hillman prior changed")

    # Saved physical source loads are replayed, not a mechanical response.
    base = {r["id"]: r for r in inp["base_bodies"]}
    owners = {r["id"]: r for r in inp["physical_owner_gravity_rows"]}
    require(len(base) == 50 and len(owners) == 150 and set(owners) == set(base) | {s["body"] for s in shafts.values()}, "Physical gravity owner duplicated or missing")
    require(all(owners[name] == row for name, row in base.items()), "Own base gravity row differs")
    for name, o in observed.items():
        r = base[name]
        near(r["mass_kg"], o["volume_mm3"] * 500e-9, 1e-12)
        near(r["center_xyz_mm"], o["center_xyz_mm"])
    for name, p in poses.items():
        near(base[name]["mass_kg"], 1.46 * .45359237, 1e-12)
        near(base[name]["center_xyz_mm"], extractor.fitting_centroid(report["scenario"], p, extractor.pure_methods()))
    for shaft in shafts.values():
        weight = math.fsum(r["mass_kg"] for r in shaft["metal_roles"])
        com = [math.fsum(r["mass_kg"] * r["center_of_mass_xyz_mm"][i] for r in shaft["metal_roles"]) / weight for i in range(3)]
        near(owners[shaft["body"]]["mass_kg"], weight, 1e-12)
        near(owners[shaft["body"]]["center_xyz_mm"], com)
    expected_loads = {}
    def source_load(identifier, body, point, mass=None, force=None):
        require(identifier not in expected_loads, "Independent physical load ID duplicated")
        expected_loads[identifier] = {"body": body, "point": point, "force": [0., 0., -mass * 9.80665] if force is None else force}
    for name, b in base.items():
        source_load("self-weight/" + name, name, b["center_xyz_mm"], b["mass_kg"])
    for rid, (body, r) in roles.items():
        source_load("physical-bolt-metal/" + rid, body, r["center_of_mass_xyz_mm"], r["mass_kg"])
    other = [r for r in data["access"]["takeoff"]["conditional_metal_gravity_rows"] if r["role"] in {"screw", "tnut"}]
    for i, r in enumerate(other):
        source_load("bolt-weight/" + r["id"] + f"/unchanged-gravity-share-{i}", r["owner"], r["centroid_xyz_mm"], r["mass_kg"])
    features = {r["identity"]: r for r in data["integrated"]["panel_machining"]["features"]}
    feature = features["hold_tnut_main_A12"]
    rear = add(add(feature["start_xyz_mm"], [1019.2, 0., 0.]), scale(feature["direction_xyz"], 18.25625))
    for panel in panel_ids:
        if panel.startswith("main_upper_"):
            source_load("accessory/" + panel, panel, rear, 12.5)
    climber_point = sub(feature["start_xyz_mm"], scale(unit(feature["direction_xyz"]), 100.))
    source_load("climber/A12", feature["panel"], climber_point, force=[0., 300., -500 * .45359237 * 9.80665])
    require(inp["case"]["case_id"] == "a12-rear" and inp["case"]["accessory_placement"] == "retained-original-top-hold", "Original A12 source load identity changed")
    loads = {r["id"]: r for r in inp["case"]["loads"]}
    require(len(loads) == len(inp["case"]["loads"]) == len(expected_loads) == 827 and set(loads) == set(expected_loads), "Complete own physical load ledger differs")
    for identifier, expected in expected_loads.items():
        actual = loads[identifier]
        require(actual["body"] == expected["body"] and actual["body"] in owners, "Own physical load host differs")
        require(actual.get("moment_xyz_nmm", [0., 0., 0.]) == [0., 0., 0.], "Source load has an undeclared free couple")
        near(actual["point_xyz_mm"], expected["point"])
        metrics["load_force_error_n"] = max(metrics["load_force_error_n"], near(actual["force_xyz_n"], expected["force"], 1e-10))
    force = [math.fsum(r["force_xyz_n"][i] for r in loads.values()) for i in range(3)]
    moment = [math.fsum(cross(r["point_xyz_mm"], r["force_xyz_n"])[i] for r in loads.values()) for i in range(3)]
    metrics["source_total_force_error_n"] = near(force, inp["case"]["applied_force_xyz_n"], 1e-8)
    metrics["source_total_moment_error_nmm"] = near(moment, inp["case"]["applied_moment_about_global_origin_xyz_nmm"], 1e-5)
    known_mass = math.fsum(r["mass_kg"] for r in base.values()) + math.fsum(r["mass_kg"] for _, r in roles.values()) + math.fsum(r["mass_kg"] for r in other)
    near(known_mass, inp["gravity"]["known_modeled_mass_kg"], 1e-10)
    near(inp["gravity"]["additional_accessory_kg"], 25.)

    # Preserve a known, excluded decoder seam without weakening its guards.
    decoder = load_module(DOMAIN, "eoere_auxiliary_frozen_domain_decoder")
    decoder_failures = []
    for patch in inp["flange_shared_face_patches"]:
        if "/post/" not in patch["id"] or not any(a in patch["id"] for a in ("clip_split_", "clip_angle_base_")):
            continue
        model = decoder.FaceDomain.__new__(decoder.FaceDomain)
        try:
            model.__init__(patch["trimmed_region_geometry"], outward_normal_xyz=patch["normal_from_second_to_first_xyz"])
        except ValueError as error:
            mask = simple_mask(patch["trimmed_region_geometry"], patch["normal_from_second_to_first_xyz"])
            require(mask is not None, "Auxiliary decoder failure needs a bounded scalar witness")
            decoder_failures.append({"patch_id": patch["id"], "signature_sha256": patch["trimmed_region_signature_sha256"],
                "decoder_error": str(error), "decoder_area_error_mm2": model.area_error,
                "decoder_centroid_error_mm": model.centroid_error, "direct_polygon_minus_disjoint_circle_area_mm2": mask["area_mm2"],
                "native_area_mm2": patch["area_mm2"], "independent_area_error_mm2": mask["area_mm2"] - patch["area_mm2"]})
    require(len(decoder_failures) == 12, "Preserved auxiliary decoder witness changed")
    verify(pins)
    require(INPUT.read_bytes() == payload and sha(OWN) == LOADED_SHA, "Input bytes or review checker changed during review")
    return {"schema": "eoere_first_order_mechanics_inputs_independent_review/v1",
        "success": "independent_eoere_successor_source_input_checks_pass", "complete_reference_contact_inventory": True,
        "input": {"path": str(INPUT.relative_to(ROOT)), "sha256": INPUT_SHA}, "source_sha256": pins,
        "source_count": len(pins), "all_source_bytes_unchanged_before_after": True,
        "disposition": "PASS_SOURCE_INPUT_JOINS_AND_DECLARED_PLANAR_REFERENCE_CENSUS",
        "counts": {**inp["counts"], "physical_loads": len(loads), "wall_intervals": 120, "shaft_end_hosts": 200,
                   "timber_pairs_in_universe": 231, "panel_timber_pairs_in_universe": 132,
                   "AABB_screened_out_pairs": len(pairs) - len(census), "exact_native_queried_pairs": len(census),
                   "patches_by_kind": dict(Counter(p.get("kind", "flange_contact") for p in allpatches)),
                   "cells_by_kind": dict(Counter(r["kind"] for r in contacts.values())),
                   "simple_analytic_mask_cells": dict(simple_counts), "native_certificate_only_patch_count": len(complex_records),
                   "actual_floor_hosts": 8, "actual_floor_normal_corners": 32, "whole_host_centroid_xy_components": 16},
        "independent_metrics": dict(metrics), "source_loads": {"known_modeled_mass_kg": known_mass, "accessory_allowance_kg": 25.,
            "conditional_total_mass_kg": known_mass + 25., "force_xyz_n": force, "moment_about_origin_xyz_nmm": moment,
            "load_prefix_counts": dict(Counter(r["id"].split("/")[0] for r in loads.values()))},
        "native_certificate_only_patches": complex_records,
        "auxiliary_decoder_failure": {"source": {"path": str(DOMAIN.relative_to(ROOT)), "sha256": DOMAIN_SHA},
            "disposition": "EXCLUDED_FROM_THIS_INPUT_REVIEW", "records": decoder_failures,
            "cause": "Preserved circular ray parity can assign a second circle to a probe on another circle's seam ordinate. Direct disjoint-circle geometry agrees with native area; no source or mask is relabeled."},
        "checks": {"gross_profiles_and_finished_geometry_kept_separate": True, "fresh_120_full_wall_intervals_not_old_bounds": True,
            "all_200_external_capture_hosts_own_only": True, "all_88_loaded_ports_and_area_coefficients": True,
            "all_176_factory_holes_and_88_used_four_port_datums": True,
            "all_1631_native_mask_cells_joined_once": True, "all_363_planar_pair_candidates_disposed": True,
            "actual_finished_floor_datums_match_geometry_only_proof": True, "all_827_physical_load_ids_replayed_once": True,
            "input_readiness_flags_preserved_false_and_null": True, "input_not_modified": True},
        "execution": {"sys_orig_argv": sys.orig_argv, "python": platform.python_version(), "executable": sys.executable},
        "limits": ["Saved source-produced OCCT planar intersections, curve descriptors and inward material probes are authenticated; this is not a fresh native geometric validation.",
            "Complete reference contact inventory means the declared coplanar planar timber/timber, panel/timber and nominal flange-mask universe; curved, noncoplanar, deformed overlap and actual pressure are separate.",
            "Complex arc/spline masks retain native area, centroid and occupancy certificates; their source geometry was not rebuilt by this checker.",
            "Gross timber and fitting stiffness, own circular shafts, screw/bedding priors, drawing density and whole-host no-slip floor are conditional inputs, not measured response bounds.",
            "Source load wrench is a fresh input ledger, not an accepted mechanical demand. No q, assembly, K, candidate response or native solve was evaluated.",
            "Actual thread/root/shank, washer pressure, materials, duration and complete joint resistance remain unqualified; no predecessor force or pass transfers."],
        "release": dict.fromkeys(("candidate_admitted", "complete_joint_resistance", "physical_contact", "fabrication", "structural", "climbing"), False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "Preserve existing review")
    result = review()
    with args.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "sources": result["source_count"], "success": result["success"]}))


if __name__ == "__main__":
    main()
