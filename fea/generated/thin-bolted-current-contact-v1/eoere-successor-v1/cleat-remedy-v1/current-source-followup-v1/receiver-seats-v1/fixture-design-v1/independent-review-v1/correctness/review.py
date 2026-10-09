"""Bounded independent stdlib review; never invoke the producer's CLI/native work."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
import runpy
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "b17a8f72f41ab2b8ce75ffaac15af075432a0ffe7111daead6597cb34eff86be",
    "design.py": "4c84897e42d4d32b1692bec8801a3c002b1c5684f984a907bde8e2cc73e4a3db",
    "result.json": "ec1c101da8f16f29cf0949c75086418e01e3b89268f55e27379fdb6a83a212f5",
    "result.svg": "60b5b105d42d35350bfe5a263f1c997974f7b3f9b1a27eea0317f88a84bd37c7",
    "verify.py": "b91887fa829c4bda60332dd1541ef26f3648d4613c5725e7f6a25d74e4cd3513",
    "verification-v1.json": "28fe869385596b6b09b562ee009654da491c7fc4e10013de99ba6edc5977aab4",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def close(a, b, label):
    require(math.isclose(a, b, rel_tol=0, abs_tol=2e-9), label)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def verify(pins):
    require(all(sha(ROOT / p) == digest for p, digest in pins.items()), "frozen byte pin")


def sub(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def segment_distance(a, b, c, d):
    """Minimize a general 3D quadratic on the unit parameter square.

    Independently consider its four boundary minima and interior stationary
    point; this does not reuse the producer's separated X/YZ projection.
    """
    u, v, w = sub(b, a), sub(d, c), sub(a, c)
    uu, vv, uv, uw, vw = dot(u, u), dot(v, v), dot(u, v), dot(u, w), dot(v, w)
    clamp = lambda t: max(0., min(1., t))
    if not uu:
        candidates = [(0., clamp(vw/vv) if vv else 0.)]
    elif not vv:
        candidates = [(clamp(-uw/uu), 0.)]
    else:
        candidates = [(0., clamp(vw/vv)), (1., clamp((vw+uv)/vv)),
                      (clamp(-uw/uu), 0.), (clamp((uv-uw)/uu), 1.)]
        det = uu*vv-uv*uv
        if det > 1e-12*uu*vv:
            s, t = (uv*vw-vv*uw)/det, (uu*vw-uv*uw)/det
            if 0 <= s <= 1 and 0 <= t <= 1:
                candidates.append((s, t))
    return min(math.sqrt(sum((w[i]+s*u[i]-t*v[i])**2 for i in range(3)))
               for s, t in candidates)


def primitive(origin, direction, near, far, radius):
    length = math.sqrt(dot(direction, direction))
    require(abs(length-1) < 1e-8 and radius > 0 and far > near, "finite primitive")
    d = [x/length for x in direction]
    return ([p+near*x for p, x in zip(origin, d, strict=True)],
            [p+far*x for p, x in zip(origin, d, strict=True)], radius)


def scalar_controls():
    fixtures = [(([0, 0, 0], [2, 0, 0], [1, -1, 0], [1, 1, 0]), 0),
                (([0, 0, 0], [2, 0, 0], [3, 4, 0], [4, 4, 0]), math.sqrt(17)),
                (([0, 0, 0], [2, 0, 0], [1, 0, 3], [1, 2, 3]), 3),
                (([0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 2, 1]), math.sqrt(2/3)),
                (([0, 0, 0], [0, 0, 0], [1, 0, 0], [2, 0, 0]), 1)]
    for args, answer in fixtures:
        close(segment_distance(*args), answer, "general segment known answer")
        close(segment_distance(*args[2:], *args[:2]), answer, "segment symmetry")
    return len(fixtures)


def vertices(row):
    return [[row["datum_xyz_mm"][i]+sum(q[j]*row["basis_grain_u_v_xyz"][j][i]
                                         for j in range(3)) for i in range(3)]
            for q in row["vertices_luv_mm"]]


def coordinate_audit(inp, data, saved):
    g, place, profiles = data["geometry"], data["placement"], data["profiles"]
    axes = {a["id"]: a for a in g["axes"]}
    require(len(axes) == len(g["axes"]) == 100, "100 distinct source axes")
    require(len({s["axis_id"] for s in g["screw_axes"]}) == len(g["screw_axes"]) == 66,
            "66 distinct source screws")
    target = {f"cleat_post_bolt_{s}_{n}" for s in ("left", "right") for n in (1, 2)}
    require(len(place["proposed_axes"]) == 4 and {a["id"] for a in place["proposed_axes"]} == target,
            "exact four proposed identities")
    joins = {r["axis_id"]: r for r in saved["four_station_coordinate_joins"]}
    for a in place["proposed_axes"]:
        expected = copy.deepcopy(axes[a["id"]])
        require(expected["point_xyz_mm"][2] == 200, "current Z200")
        expected["point_xyz_mm"][2] = 180
        require(a == expected, "Z180-only proposal patch")
        side = "left" if "_left_" in a["id"] else "right"
        outward = -1 if side == "left" else 1
        post = vertices(profiles["base_post_outer_"+side])
        cleat = vertices(profiles["eoere_cleat_"+side])
        inner_x = (max if side == "left" else min)(p[0] for p in post)
        x0 = inner_x-outward*12.7
        row = joins[a["id"]]
        close(row["world_X_at_fixture_w0_mm"], x0, "handed bench origin")
        require(a["direction_xyz"] == [-outward, 0, 0], "inward drilling")
        local = [a["point_xyz_mm"][1]+175.7, 180., outward*(a["point_xyz_mm"][0]-x0)]
        for actual, answer in zip(row["fixture_entry_uvw_mm"], local, strict=True):
            close(actual, answer, "handed axis coordinate")
        for world, answer in ((post, [12.7, 50.8]), (cleat, [50.8, 88.9])):
            bounds = [min(outward*(p[0]-x0) for p in world), max(outward*(p[0]-x0) for p in world)]
            for actual, expected_w in zip(bounds, answer, strict=True):
                close(actual, expected_w, "two flush nominal timber layers")
        close(a["grip_mm"], 76.2, "two thicknesses")
        close(row["fixture_exit_w_mm"], 12.7, "backer entry")
        close(row["cleat_bottom_to_axis_mm"], 40.3, "cleat bottom tie")
        close(row["post_top_to_axis_mm"], 58.9, "post top tie")
    return {"source_axes": 100, "source_screws": 66, "unchanged_axes": 96,
            "Z200_to_Z180_only_moves": 4, "handed_axis_joins": 4}


def finite_pair_audit(inp, data, saved, capsule):
    bores = [primitive(a["point_xyz_mm"], a["direction_xyz"], -1, a["grip_mm"]+1, 11.1125/2)
             for a in data["placement"]["proposed_axes"]]
    specs = {"current_body": inp["primitive_scope"]["current_body"],
             "current_modeled_head": inp["primitive_scope"]["current_modeled_head"]}
    specs.update({s["name"]: s for s in inp["primitive_scope"]["extra_sensitivities"]})
    minima = {}
    for name, spec in specs.items():
        pairs = []
        for bore in bores:
            for s in data["geometry"]["screw_axes"]:
                p = primitive(s["origin_xyz_mm"], s["direction_xyz"],
                              spec["near_mm"], spec["far_mm"], spec["radius_mm"])
                distance = segment_distance(*bore[:2], *p[:2])
                close(distance, capsule.axis_distance(
                    {"start_xyz_mm": bore[0], "end_xyz_mm": bore[1]},
                    {"start_xyz_mm": p[0], "end_xyz_mm": p[1]}), "each reused axis distance")
                pairs.append(distance-bore[2]-p[2])
        actual = saved["nominal_primitive_clearance"]["cases"][name]
        require(len(pairs) == actual["comparisons"] == 264 and min(pairs) > 0,
                "all finite source capsules separate")
        close(actual["minimum"]["capsule_separation_lower_bound_mm"], min(pairs), "global finite minimum")
        minima[name] = min(pairs)
    return {"independent_general_3D_segment_pairs": 1056, "minima_mm": minima}


def rectangle_distance(p, rect):
    return math.dist(p, [min(max(x, lo), hi) for x, (lo, hi) in zip(p, rect, strict=True)])


def support_audit(inp, data, saved):
    rear = inp["fixture_coordinates"]["rear_Y_mm"]
    support = saved["support_and_clamp_requirements"]
    require(len({(r["receiver"], r["contact"]) for r in support["source_profile_and_recorded_cut_checks"]})
            == len(support["source_profile_and_recorded_cut_checks"]) == 14, "14 distinct contacts")
    for row in support["source_profile_and_recorded_cut_checks"]:
        points = sorted({(p[1]-rear, p[2]) for p in vertices(data["profiles"][row["receiver"]])})
        center = [sum(p[i] for p in points)/len(points) for i in (0, 1)]
        polygon = sorted(points, key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))
        rect = row["uv_rectangle_mm"]
        margins = []
        for q in itertools.product(*rect):
            for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
                edge = sub(b, a)
                margins.append((edge[0]*(q[1]-a[1])-edge[1]*(q[0]-a[0]))/math.hypot(*edge))
        close(row["minimum_profile_margin_mm"], max(0, min(margins)), "convex contact containment")
        require(min(margins) > -2e-8, "contact outside source profile")
        gaps = []
        for a in data["geometry"]["axes"]:
            if row["receiver"] not in a["receivers"]:
                continue
            require(abs(a["direction_xyz"][0]) == 1 and a["direction_xyz"][1:] == [0, 0],
                    "circle projection applies to each own transverse bore")
            v = 180 if a["id"].startswith("cleat_post_bolt_") else a["point_xyz_mm"][2]
            gaps.append(rectangle_distance([a["point_xyz_mm"][1]-rear, v], rect)-a["bore_diameter_mm"]/2)
        close(row["minimum_recorded_bore_margin_mm"], min(gaps), "recorded cuts avoid contact")
        require(len(gaps) == 4 and min(gaps) > 0.396875, "maximum target bore also avoids contact")
    d = inp["dimensions_mm"]
    openings = {"guide_clamps": d["guide_w"][1]-d["baseboard_w"][0],
                "cleat_clamp": d["cleat_support_w"][1]+d["member_thickness"]-d["baseboard_w"][0],
                "post_clamp": d["backer_w"][1]+d["member_thickness"]-d["baseboard_w"][0]}
    for key, value in openings.items():
        close(support["bare_opening_mm"][key], value, "contact-plane opening")
    gaps = [rectangle_distance([u, 180], lane)-31.75
            for u in (44.45, 95.25) for lane in support["clamp_arm_plan_lanes_uv_mm"].values()]
    close(support["minimum_chuck_nose_to_clamp_lane_margin_mm"], min(gaps), "finite plan lane gap")
    close(d["cleat_support_w"][1], d["backer_w"][1]+d["member_thickness"], "riser plane")
    require(d["cleat_support_v"][0] > d["post_height"], "separate riser")
    return {"contact_rectangles": 14, "own_cut_projection_checks": 56,
            "nose_lane_comparisons": 8, "nominal_openings_mm": openings,
            "minimum_nominal_nose_lane_gap_mm": min(gaps)}


def error_audit(inp, saved, finite):
    d, e = inp["dimensions_mm"], inp["error_budget"]
    b = saved["pointwise_error_and_reach_budget"]
    nominal = d["retainer_w"][1]-d["backer_w"][1]+d["breakout_travel"]
    worst = nominal+d["matched_stack_deviation_max"]+d["guide_cap_stack_deviation_max"]
    downstream = 2*d["member_thickness"]+d["matched_stack_deviation_max"]+d["breakout_travel"]
    close(nominal, 111.125, "independent nominal reach")
    close(worst, 111.825, "independent maximum reach")
    tilt = worst*math.tan(math.radians(e["guide_normal_angle_max_deg"]))
    close(b["guide_tilt_max_mm"], tilt, "full-path tilt")
    radius, length = e["bushing_diametral_play_max_mm"]/2, d["bushing_effective_length_min"]
    maximum = 0.
    # General planar sleeve-end vectors; antipodal pairs attain the triangle bound.
    vectors = [[radius*math.cos(a*math.pi/8), radius*math.sin(a*math.pi/8)] for a in range(16)]
    for entry, exit_ in itertools.product(vectors, repeat=2):
        for lever in (0., downstream/2, downstream):
            far = [x+(x-y)*lever/length for x, y in zip(exit_, entry, strict=True)]
            maximum = max(maximum, math.hypot(*far))
    analytic = radius+(2*radius)*downstream/length
    close(maximum, analytic, "2D sleeve-end worst case")
    close(b["insert_slop_max_mm"], analytic, "reported insert slop")
    total, bound = sum(e["terms_mm"].values()), e["total_relative_bore_screw_bound_mm"]
    close(total, 1.46, "triangle bound allocation")
    require(total <= bound == 1.5 and tilt <= .16 and analytic <= .5, "allocated requirements")
    close(b["minimum_declared_body_clearance_after_budget_mm"], finite["minima_mm"]["current_body"]-bound,
          "full pointwise body clearance")
    close(b["conditional_whole_screw9p525_clearance_after_budget_mm"],
          finite["minima_mm"]["whole_screw_9p525_containing_capsule_reference"]-bound,
          "conditional whole-screw bound")
    close(b["reach_requirements_mm"]["worst_free_projection_from_chuck"], worst+2, "maximum free projection")
    close(b["reach_requirements_mm"]["worst_wood_exposed_flute_lower_bound"], downstream, "wood flute lower bound")
    for key, value in {"cleat_bottom": 38.7, "post_top": 57.3, "nearest_crossgrain_raw_edge": 42.85}.items():
        close(b["geometric_tie_lower_bounds_mm"][key], value, "distance-only lower bound")
    return {"sleeve_end_vector_cases": 256, "sleeve_path_samples": 768,
            "worst_slop_mm": analytic, "full_path_tilt_mm": tilt,
            "worst_free_projection_mm": worst+2, "allocated_relative_bound_mm": total,
            "declared_relative_bound_mm": bound}


def negative_controls(method, inp, data, profile, datum, proposed, shapes, cuts, gaps):
    results = []

    def reject(label, fn):
        try:
            fn()
        except ValueError:
            results.append(label)
        else:
            raise ValueError("control accepted: "+label)

    for label, mutate in [
        ("wrong_current_revision", lambda x: x["geometry"].update(revision="wrong")),
        ("current_axis_change", lambda x: x["geometry"]["axes"][0]["point_xyz_mm"].__setitem__(2, -999)),
        ("current_screw_change", lambda x: x["geometry"]["screw_axes"][0]["origin_xyz_mm"].__setitem__(2, -999)),
        ("wrong_proposed_Z", lambda x: x["placement"]["proposed_axes"][0]["point_xyz_mm"].__setitem__(2, 181)),
        ("adopted_proposal", lambda x: x["placement"].__setitem__("geometry_adopted", True)),
        ("partial_saved_wall", lambda x: x["native_result"]["scenarios"][0]["wall_queries"][0].__setitem__("partial_wall_present", True)),
    ]:
        changed = copy.deepcopy(data)
        mutate(changed)
        reject(label, lambda c=changed: method["source_inventory"](inp, c, profile, datum))
    changed_axes = copy.deepcopy(proposed)
    changed_axes[0]["direction_xyz"][0] *= -1
    reject("wrong_hand_direction", lambda: method["transforms"](inp, changed_axes, shapes))
    changed_shapes = copy.deepcopy(shapes)
    changed_shapes["base_post_outer_left"]["thickness_mm"] += 1
    reject("wrong_receiver_thickness", lambda: method["transforms"](inp, proposed, changed_shapes))
    mutations = [
        ("wrong_rear_datum", "fixture_coordinates", "rear_Y_mm", -174.7, "transforms"),
        ("wrong_riser_height", "dimensions_mm", "cleat_support_w", [0, 51.8], "footprints"),
        ("riser_overlaps_post", "dimensions_mm", "cleat_support_v", [230, 314.325], "footprints"),
        ("contact_outside_profile", "dimensions_mm", "post_clamp_center_uv", [69.85, 250], "footprints"),
        ("nose_lane_collision", "dimensions_mm", "chuck_nose_keepout_radius", 100, "footprints"),
        ("excess_guide_tilt", "error_budget", "guide_normal_angle_max_deg", 1, "budget"),
        ("excess_insert_play", "error_budget", "bushing_diametral_play_max_mm", .2, "budget"),
        ("insufficient_total_error", "error_budget", "total_relative_bore_screw_bound_mm", 1.4, "budget"),
        ("cap_cutter_collision", "dimensions_mm", "retainer_clearance_hole_D", 11.2, "retainer"),
        ("cap_cannot_capture_flange", "dimensions_mm", "retainer_clearance_hole_D", 23, "retainer"),
    ]
    for label, group, key, value, function in mutations:
        changed = copy.deepcopy(inp)
        changed[group][key] = value
        args = {"transforms": (proposed, shapes), "footprints": (shapes, cuts, profile),
                "budget": (gaps,), "retainer": ()}[function]
        reject(label, lambda c=changed, f=function, a=args: method[f](c, *a))
    reject("existing_output", lambda: method["output_paths"](PACKET / "result.json"))
    reject("non_json_output", lambda: method["output_paths"](PACKET / "wrong.txt"))
    reject("nested_output", lambda: method["output_paths"](OWN.parent / "unused.json"))
    return results


def main():
    destination = OWN.with_name("receipt.json")
    require(not destination.exists(), "preserve existing review receipt")
    saved, inp = read(PACKET / "result.json"), read(PACKET / "inputs.json")
    pins = dict(saved["source_sha256"])
    pins.update({str((PACKET / n).relative_to(ROOT)): d for n, d in EXPECTED.items()})
    verify(pins)
    method = runpy.run_path(str(PACKET / "design.py"))
    _, replay, shapes = method["evaluate"]()
    require(replay == {k: v for k, v in saved.items() if k != "drawing"}, "exact source arithmetic replay")
    require(method["drawing"](inp, replay, shapes) == (PACKET / "result.svg").read_bytes(), "exact SVG replay")
    _, data, _, profile, datum, capsule = method["prepare"]()
    proposed, shapes, cuts, _ = method["source_inventory"](inp, data, profile, datum)
    finite = finite_pair_audit(inp, data, saved, capsule)
    audit = {"segment_known_answers": scalar_controls(), "coordinate_joins": coordinate_audit(inp, data, saved),
             "finite_primitive_clearance": finite, "nominal_support": support_audit(inp, data, saved),
             "pointwise_error_and_reach": error_audit(inp, saved, finite)}
    controls = negative_controls(method, inp, data, profile, datum, proposed, shapes, cuts,
                                 saved["nominal_primitive_clearance"])
    require(all(v is False for v in saved["release"].values()), "all release flags false")
    require(all(r["Actual"] == r["Disposition"] == "" for r in saved["actual_observations"]), "blank actuals")
    require(data["native_saved_review"]["findings"] == []
            and data["native_saved_review"]["audit"]["pass"], "reused own saved-native review")
    require(not ({"cadquery", "OCP", "numpy", "scipy"} & set(sys.modules)), "no native/numerical imports")
    verify(pins)
    receipt = {"schema": "fixture_design_v1_independent_correctness_review/v1", "findings": [],
               "target_sha256": EXPECTED, "direct_target_and_source_pin_count": len(pins),
               "direct_target_and_source_sha256": dict(sorted(pins.items())), "bytes_unchanged_before_after": True,
               "exact_result_and_svg_source_replay": True, "audit": audit, "rejected_controls": controls,
               "review_helper_sha256": sha(OWN),
               "limits": [
                   "Stdlib source, saved JSON, scalar geometry and in-memory controls only; no CAD/BREP import/query/rebuild, native/frame solve, tessellation, browser or physical work.",
                   "Seventeen direct source pins are authenticated; inherited closures and native observations are reused within the frozen saved-result review, not independently regenerated.",
                   "Generic inserts are dimensional requirements, not an actual selected product. Clamp/support contacts and finite source capsules remain nominal; actual tools/parts, chip exit, retaining hardware, workholding and achieved tolerances are unobserved.",
                   "Z180 remains unadopted. Current Z200 fields stay separate; no fresh proposal forces, complete Cdelta/joint resistance, fabrication or physical release."],
               "release": saved["release"]}
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(destination), "helper_sha256": sha(OWN),
                      "findings": [], "direct_pins": len(pins), "negative_controls": len(controls)}))


if __name__ == "__main__":
    main()
