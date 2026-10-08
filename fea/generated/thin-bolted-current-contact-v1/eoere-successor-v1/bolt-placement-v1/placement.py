"""Pure raw-profile eoere placement constraints; no CAD, force or acceptance.

The source corner poses are preserved. Absolute factory heel/transverse datums
are not published: every generated hole is an explicit centered-pattern scenario.
NDS row classification follows load direction, not an assumed grain-row label.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LEAF = Path(__file__).resolve().parent
LOADED_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
RELEASE = dict.fromkeys(("candidate_accepted", "geometry_accepted", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value, label):
    require(type(value) in (int, float) and math.isfinite(value), label + " must be finite")
    return float(value)


def verify_pins(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "source bytes differ: " + path)


def load_pure_methods(pins):
    """Reuse exact frozen methods without importing the CAD package initializer."""
    path = ROOT / "fea/generated/thin-bolted-build-planning-v4/prepare.py"
    require(sha(path) == pins[str(path.relative_to(ROOT))], "raw profile method differs")
    spec = importlib.util.spec_from_file_location("eoere_raw_profile_pure", path)
    shop = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shop)
    path = ROOT / "scripts/thin_bolted_timber_resistance.py"
    require(sha(path) == pins[str(path.relative_to(ROOT))], "end-factor method differs")
    tree = ast.parse(path.read_bytes(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name == "end_geometry_factor"]
    require(len(nodes) == 1, "frozen classified square-end function absent")
    namespace = {"math": math, "require": require}
    # Only the SHA-authenticated function is compiled; its module imports CAD.
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return shop, namespace["end_geometry_factor"]


def factory_holes(station, dimensions, far_offset_mm, depth_shift_mm, shop):
    """All eight hypothetical factory centres; only four far centres are occupied."""
    h, delta = finite(far_offset_mm, "far offset"), finite(depth_shift_mm, "depth shift")
    pitch, transverse = dimensions["axial_hole_row_pitch"], dimensions["transverse_hole_pitch"]
    u, v, w = shop.proper([station[k] for k in ("u_xyz", "v_xyz", "w_xyz")])
    o = shop.vector(station["origin_xyz_mm"])
    rows = []
    for flange, along, axis in (("beam", u, shop.scale(v, -1)),
                                ("post", v, shop.scale(u, -1))):
        for row, s in (("near", h - pitch), ("far", h)):
            for sign in (-1, 1):
                z = sign * transverse / 2
                point = shop.add(o, shop.add(shop.scale(along, s), shop.scale(w, z + delta)))
                rows.append({"id": f"{station['duty_id']}/{flange}/{row}/{sign:+d}",
                             "flange": flange, "receiver": station[flange], "row": row,
                             "installed": row == "far", "along_heel_scenario_mm": s,
                             "transverse_scenario_mm": z, "depth_shift_scenario_mm": delta,
                             "wood_entry_xyz_mm": point, "axis_into_raw_wood_xyz": axis})
    return rows


def sharp_angle_domain(dimensions, factory_hole_mm):
    """Strict ideal square-heel clearance only; formed bend/steel edge strength absent."""
    r = finite(factory_hole_mm, "factory bore") / 2
    require(r > 0, "positive bore required")
    low = dimensions["axial_hole_row_pitch"] + dimensions["thickness"] + r
    high = min(dimensions["arm_A"], dimensions["arm_B"]) - r
    require(low < high and dimensions["transverse_hole_pitch"] / 2 + r < dimensions["width"] / 2,
            "factory centres do not fit ideal sharp angle")
    return {"low_mm": low, "high_mm": high, "low_inclusive": False, "high_inclusive": False,
            "scope": "All eight circular holes clear ideal t-wide square heel and plate tip only; actual bend, hole tolerances, metal end/edge resistance and datums unavailable."}


def affine_interval(base, slope, facets, shifts, domain, shop):
    """Intersect scalar halfspaces; preserves an empty interval instead of a pass."""
    low, high = domain
    for shift in shifts:
        point = shop.add(base, shift)
        for face in facets:
            n, c = face["outward_normal_xyz"], face["offset_world_mm"]
            rate, reserve = shop.dot(n, slope), c - shop.dot(n, point)
            if abs(rate) < 1e-10:
                if reserve < -1e-6:
                    return None
            elif rate > 0:
                high = min(high, reserve / rate)
            else:
                low = max(low, reserve / rate)
    return None if low > high + 1e-6 else [low, high]


def active_pair_rules(diameter, pitch, ell_over_d=None, attached_spacing_mm=None):
    """NDS 12.1.2.4 rows follow the specified load direction; no selected load."""
    d, spacing = finite(diameter, "diameter"), finite(pitch, "pitch")
    require(d >= 6.35 and spacing > 0, "Table12.5.1 C-D D>=1/4 inch required")
    require(ell_over_d is None or finite(ell_over_d, "ell/D") >= 0, "negative ell/D")
    if attached_spacing_mm is not None:
        require(finite(attached_spacing_mm, "attached spacing") >= 3 * d,
                "attached full-factor spacing below row minimum")
    parallel_edge = None if ell_over_d is None else (
        1.5 * d if ell_over_d <= 6 else max(1.5 * d, spacing / 2))
    return {
        "parallel_load": {"row_locations": 2, "bolts_per_location_from_this_pair": 1,
                          "two_or_more_fastener_rows_in_isolated_pair": 0,
                          "actual_member_row_inventory_required": True,
                          "between_rows_actual_mm": spacing, "between_rows_min_mm": 1.5 * d,
                          "in_row_spacing_applicable": False,
                          "edge_min_mm_if_ell_classified": parallel_edge,
                          "edge_min_possible_range_mm": [1.5 * d, max(1.5 * d, spacing / 2)]},
        "perpendicular_load": {"rows": 1, "bolts_in_row": 2,
                               "in_row_actual_mm": spacing, "in_row_min_mm": 3 * d,
                               "in_row_full_factor_required_mm": attached_spacing_mm,
                               "in_row_spacing_factor_only": (None if attached_spacing_mm is None
                                                              or spacing < 3 * d else min(1., spacing / attached_spacing_mm)),
                               "loaded_edge_min_mm": 4 * d, "unloaded_edge_min_mm": 1.5 * d,
                               "between_rows_spacing_applicable": False},
        "attached_spacing_input_basis": "Full perpendicular-load in-row factor requires applicable attached-member spacing; missing steel-side rule is not replaced by 4D or 5D.",
        "ell_input_basis": "TableC footnote uses lesser wood-main penetration and total wood-side penetration; single-steel-side pattern is not silently assigned ell from total grip.",
        "outer_crossgrain_spread_mm": spacing, "ordinary_sawn_outer_spread_limit_mm": 127.,
        "complete_geometry_factor": None,
    }


def member_row_inventory(active, profiles, shop):
    """Actual main-member grain lines; no assumption that an isolated bolt is a row."""
    inventories = []
    for member, profile in sorted(profiles.items()):
        groups = {}
        for row in active:
            if row["receiver"] != member:
                continue
            coordinate = shop.local(row["raw_midbearing_point_xyz_mm"], profile["datum"], profile["basis"])
            # Five decimal mm grouping exceeds the source rounding error; no geometry move.
            key = tuple(round(v, 5) for v in coordinate[1:])
            groups.setdefault(key, []).append({"hole_id": row["id"], "grain_station_mm": coordinate[0]})
        records = [{"crossgrain_u_v_source_coordinates_mm": list(key),
                    "rounding_for_identity_grouping_mm": 1e-5,
                    "fastener_count": len(group), "two_or_more_fastener_row": len(group) >= 2,
                    "holes": sorted(group, key=lambda r: r["grain_station_mm"])}
                   for key, group in sorted(groups.items())]
        inventories.append({"member": member, "direction_of_load_scenario": "parallel to nominal grain",
                            "rows": records, "scope": "64 main far attachments only; other frame/remaining-duty bolts, signs, joint group introduction and fracture not qualified."})
    return inventories


def profile_geometry(record, cached, stock, shop):
    """Authenticate saved analytic profile against original vertices and cached metadata."""
    basis = shop.proper(record["basis_grain_u_v_xyz"])
    datum = shop.vector(record["datum_xyz_mm"])
    vertices = [shop.add(datum, [math.fsum(p[j] * basis[j][i] for j in range(3))
                               for i in range(3)]) for p in record["raw_profile_vertices_luv_mm"]]
    shift = record["raw_source_translation_xyz_mm"]
    expected = [shop.add(p, shift) for p in stock["vertices_world_mm"]]
    require(len(vertices) == len(expected) and max(math.dist(p, q) for p, q in zip(vertices, expected, strict=True)) < 1e-6,
            "saved physical profile vertex source mismatch")
    native = record["raw_native_body"]
    require(all(native[k] == cached[k] for k in ("path", "sha256", "volume_mm3")),
            "raw body source join mismatch")
    require(abs(shop.dot(basis[0], cached["grain_axis_xyz"])) > 1 - 1e-8, "grain mismatch")
    facets, volume = shop.hull(vertices)
    require(abs(volume - cached["volume_mm3"]) < max(.001, volume * 1e-9), "raw convex volume mismatch")
    bounds = [[min(p[i] for p in vertices), max(p[i] for p in vertices)] for i in range(3)]
    require(max(abs(a - b) for pair, prior in zip(bounds, cached["bounds_xyz_mm"], strict=True)
                for a, b in zip(pair, prior, strict=True)) < 1e-6, "raw world bounds mismatch")
    return {"member": record["member"], "basis": basis, "facets": facets,
            "datum": datum, "bounds": bounds, "convex_volume_mm3": volume,
            "source_raw_native_body": native}


def ray_record(point, direction, facets, shop):
    interval = shop.line_interval(point, direction, facets)
    out = []
    for sign, distance in ((-1, -interval[0]), (1, interval[1])):
        boundary = shop.add(point, shop.scale(direction, sign * distance))
        faces = [{"raw_facet_vertex_indices": f["vertex_indices"],
                  "outward_normal_xyz": f["outward_normal_xyz"],
                  "alignment_with_ray": sign * shop.dot(f["outward_normal_xyz"], direction)}
                 for f in facets if abs(shop.dot(f["outward_normal_xyz"], boundary)
                                        - f["offset_world_mm"]) < 1e-5]
        require(faces, "missing owning raw boundary facet")
        out.append({"direction_sign": sign, "distance_mm": max(0., distance),
                    "square_to_ray": len(faces) == 1 and abs(faces[0]["alignment_with_ray"] - 1) < 1e-7,
                    "owning_facets": faces})
    return out


def hole_screen(hole, profile, diameter, shop, end_rule):
    axis, point = hole["axis_into_raw_wood_xyz"], hole["wood_entry_xyz_mm"]
    interval = shop.line_interval(point, axis, profile["facets"])
    require(abs(interval[0]) < 1e-6, "source pose not an entry on own raw receiving plane")
    g = profile["basis"][0]
    require(abs(shop.dot(g, axis)) < 1e-7, "oblique/end-grain shaft requires other rule")
    q = shop.unit(shop.cross(g, axis))
    center = shop.add(point, shop.scale(axis, sum(interval) / 2))
    ends = ray_record(center, g, profile["facets"], shop)
    edges = ray_record(center, q, profile["facets"], shop)
    for end in ends:
        end["softwood_toward_end_factor_only"] = (end_rule(end["distance_mm"], diameter, "softwood_parallel_tension")
                                                   if end["square_to_ray"] else None)
        end["away_or_perpendicular_factor_only"] = (end_rule(end["distance_mm"], diameter, "parallel_compression")
                                                     if end["square_to_ray"] else None)
    return {**hole, "raw_shaft_interval_from_entry_mm": interval,
            "raw_midbearing_point_xyz_mm": center, "nominal_grain_xyz": g,
            "crossgrain_edge_direction_xyz": q, "end_rays": ends, "edge_rays": edges,
            "signed_force_available": False, "finished_member_distance": None,
            "oblique_end_note": "Non-square end ray is a diagnostic; actual equivalent shear-area rule remains unavailable.",
            "complete_geometry_factor": None, "strength_pass": False}


def flange_intervals(station, flange, profile, dimensions, domain, diameter, shop):
    """Raw full-thickness ray inequalities, with ideal all-eight metal domain separate."""
    along = station["u_xyz" if flange == "beam" else "v_xyz"]
    axis = shop.scale(station["v_xyz" if flange == "beam" else "u_xyz"], -1)
    w, o, g = station["w_xyz"], station["origin_xyz_mm"], profile["basis"][0]
    q = shop.unit(shop.cross(g, axis))
    middle = shop.add(o, shop.scale(along, (domain[0] + domain[1]) / 2))
    raw_span = shop.line_interval(middle, axis, profile["facets"])
    require(abs(raw_span[0]) < 1e-6, "affine interval source plane differs")
    shifts = [shop.add(shop.scale(w, z), shop.scale(axis, s))
              for z in (-dimensions["transverse_hole_pitch"] / 2, dimensions["transverse_hole_pitch"] / 2)
              for s in raw_span]
    for sign in (-1, 1):
        for dr, distance in ((g, 7 * diameter), (q, 4 * diameter)):
            shifts.extend([shop.add(shop.add(shop.scale(w, z), shop.scale(axis, s)), shop.scale(dr, sign * distance))
                           for z in (-dimensions["transverse_hole_pitch"] / 2, dimensions["transverse_hole_pitch"] / 2)
                           for s in raw_span])
    far_interval = affine_interval(o, along, profile["facets"], shifts, domain, shop)
    h = 65.0875
    base = shop.add(o, shop.add(shop.scale(along, h), shop.scale(axis, sum(raw_span) / 2)))
    edge_shifts = [shop.add(shop.scale(w, z), shop.scale(q, sign * 4 * diameter))
                   for z in (-dimensions["transverse_hole_pitch"] / 2, dimensions["transverse_hole_pitch"] / 2)
                   for sign in (-1, 1)]
    depth_interval = affine_interval(base, w, profile["facets"], edge_shifts, [-100., 100.], shop)
    return {"flange": flange, "receiver": station[flange], "raw_thickness_mm": raw_span[1] - raw_span[0],
            "far_offset_interval_mm": far_interval,
            "far_offset_interval_endpoints_inclusive": (None if far_interval is None else
                                                        [far_interval[0] > domain[0] + 1e-6,
                                                         far_interval[1] < domain[1] - 1e-6]),
            "ideal_metal_domain_endpoints_excluded": True,
            "depth_shift_interval_for_both_possible_loaded_edges_mm": depth_interval,
            "depth_interval_reference_far_offset_mm": h,
            "scope": "Convex raw full-bearing-thickness grain rays >=7D and edge rays >=4D. Square end factors apply only to square owners; oblique-end shear area, finished cuts, actual factory datum and steel resistance remain open.",
            "complete_geometry_factor": None}


def evaluate(input_path=LEAF / "input.json", *, far_offset_mm=65.0875, depth_shift_mm=0.):
    require(sha(__file__) == LOADED_SOURCE_SHA256, "loaded placement source changed")
    raw = Path(input_path).read_bytes()
    inp = json.loads(raw)
    require(inp["schema"] == "eoere_main_analytic_placement_inputs/v1", "input schema differs")
    pins = dict(inp["source_sha256"])
    pins[str(Path(input_path).resolve().relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    pins[str(Path(__file__).relative_to(ROOT))] = LOADED_SOURCE_SHA256
    pins[str((LEAF / "test_placement.py").relative_to(ROOT))] = sha(LEAF / "test_placement.py")
    verify_pins(pins)
    shop, end_rule = load_pure_methods(pins)
    station_data = json.loads((ROOT / inp["station_path"]).read_bytes())
    layout = json.loads((ROOT / inp["layout_path"]).read_bytes())
    product = json.loads((ROOT / inp["product_path"]).read_bytes())
    require(station_data["source_sha256"] == pins[inp["layout_path"]], "station source differs")
    require(station_data["main_station_count"] == 16 and station_data["active_holes_per_angle"] == 4,
            "owner main-angle/active-hole count differs")
    require(all(v is False for v in product["release"].values()), "product unexpectedly released")
    old = {r["angle_id"]: r for r in layout["raw_fittings"]}
    stations = station_data["main_stations"]
    require(len(stations) == 16 and len({s["angle_id"] for s in stations}) == 16, "duplicate/missing main stations")
    for st in stations:
        require(all(st[k] == old[st["angle_id"]][k] for k in ("duty_id", "beam", "post", "origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")),
                "source corner pose changed")
    for path, digest in product["source_sha256"].items():
        require(pins.get(path) == digest, "product source closure absent")
    dimensions = product["drawing_dimension_conversions_mm"]
    require(dimensions == inp["drawing_dimension_conversions_mm"], "drawing scenario dimensions differ")
    require(inp["nominal_bolt_diameter_mm"] == 9.525 and inp["factory_hole_scenario_mm"] == 10., "diameter scenario differs")
    d = inp["nominal_bolt_diameter_mm"]
    bore = finite(inp["wood_bore_scenario_mm"], "wood bore")
    require(d + 25.4 / 32 <= bore <= d + 25.4 / 16, "wood bore outside NDS nominal bolt-hole range")
    domain = sharp_angle_domain(dimensions, inp["factory_hole_scenario_mm"])
    require(domain["low_mm"] < far_offset_mm < domain["high_mm"], "far row outside sharp-angle scenario domain")
    native = json.loads((ROOT / inp["native_path"]).read_bytes())
    stock = json.loads((ROOT / inp["stock_profiles_path"]).read_bytes())
    joined = json.loads((ROOT / inp["joined_profiles_path"]).read_bytes())
    members = {r["member"]: r for r in joined["members"]}
    cached = {r["member"]: r for r in native["raw_parts"]}
    used = sorted({st[fl] for st in stations for fl in ("beam", "post")})
    profiles = {name: profile_geometry(members[name], cached[name], stock[name], shop) for name in used}
    rows, intervals = [], []
    for st in stations:
        for hole in factory_holes(st, dimensions, far_offset_mm, depth_shift_mm, shop):
            if hole["installed"]:
                row = hole_screen(hole, profiles[hole["receiver"]], d, shop, end_rule)
            else:
                row = {**hole, "wood_hole_drilled_or_occupied": False,
                       "scope": "Unused factory steel hole retained; no near-row timber attachment assumed."}
            rows.append(row)
        intervals.extend(flange_intervals(st, fl, profiles[st[fl]], dimensions,
                                          [domain["low_mm"], domain["high_mm"]], d, shop) for fl in ("beam", "post"))
    active = [r for r in rows if r["installed"]]
    short = [r for r in active if any(e["square_to_ray"] and e["distance_mm"] < 7 * d - 1e-6 for e in r["end_rays"])]
    shifted_nearest_edge = min(e["distance_mm"] for r in active for e in r["edge_rays"])
    # The source end-factor function is reused unchanged; no force chooses a category.
    factor = min(e["softwood_toward_end_factor_only"]["end_factor_only"] for r in short for e in r["end_rays"]
                 if e["square_to_ray"] and e["distance_mm"] < 7 * d - 1e-6) if short else 1.
    verify_pins(pins)
    require(Path(input_path).read_bytes() == raw, "input bytes changed during evaluation")
    return {
        "schema": "eoere_main_raw_profile_placement_feasibility/v1",
        "candidate_scope": "Owner-directed eoere successor main16; source poses only",
        "parameters": {"far_offset_mm": far_offset_mm, "near_offset_mm": far_offset_mm - dimensions["axial_hole_row_pitch"],
                       "depth_shift_mm": depth_shift_mm, "dimensions": dimensions,
                       "factory_hole_scenario_mm": 10., "nominal_bolt_mm": d,
                       "wood_bore_scenario_mm": inp["wood_bore_scenario_mm"]},
        "counts": {"main_angles": 16, "factory_holes_retained": len(rows), "active_flange_attachments": len(active),
                   "unused_factory_holes": len(rows) - len(active), "source_raw_members": len(used)},
        "factory_absolute_datums_verified": False,
        "sharp_angle_all_eight_hole_domain": domain,
        "nds_active_pair_classification": active_pair_rules(d, dimensions["transverse_hole_pitch"]),
        "parallel_grain_member_row_inventory": member_row_inventory(active, profiles, shop),
        "wood_hole_NDS12_1_3_2_interval_mm": [d + 25.4 / 32, d + 25.4 / 16],
        "factory_hole_not_wood_drill_instruction": True,
        "all_factory_hole_scenarios": rows, "far_and_depth_constraints": intervals,
        "summary": {"square_end_short_of_toward_end_full_factor_attachments": len(short),
                    "affected_flange_pairs": sorted({r["id"].rsplit("/", 2)[0] for r in short}),
                    "conditional_square_end_factor_only": factor,
                    "minimum_active_raw_edge_mm": shifted_nearest_edge,
                    "perpendicular_loaded_edge_min_mm": 4 * d,
                    "nearest_edge_reserve_mm": shifted_nearest_edge - 4 * d,
                    "centered_row_shortfall_from_7D_mm": 7 * d - 65.0875,
                    "depth_18mm_nearest_edge_scenario_mm": 139.7 / 2 - 50.8 / 2 - 18.,
                    "depth_18mm_loaded_edge_shortfall_scenario_mm": 4 * d - (139.7 / 2 - 50.8 / 2 - 18.),
                    "full_factor_critical_far_offset_mm": 7 * d,
                    "unknown_factory_offset_automatically_changed": False},
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "method_source_locators": inp["method_source_locators"],
        "pure_method_reuse": {"raw_hull_line_interval": "fea/generated/thin-bolted-build-planning-v4/prepare.py",
                              "classified_square_end_factor": "scripts/thin_bolted_timber_resistance.py:end_geometry_factor; exact AST function only, package/CAD initializer not imported"},
        "cadquery_imported": "cadquery" in sys.modules,
        "tools": {"python": sys.version.split()[0]},
        "reproduction_command": f"uv run python {Path(__file__).relative_to(ROOT)} --far-offset-mm {far_offset_mm} --depth-shift-mm {depth_shift_mm} --out RESULT.json",
        "limits": inp["limits"], "release": RELEASE.copy(),
    }


def compact_receipt(result):
    """Keep every hole/ray identity and value; avoid repeated rule dictionaries."""
    out = {**result, "ray_owner_representation": "Each owning facet is identified by its source raw-profile vertex-index list; normals replay from pinned hull method/profile vertices.",
           "end_factor_representation": "Scalar classified end-only factor or null. Common thresholds: softwood toward-end3.5D/7D; away/perpendicular2D/4D. No signed load selected and no complete Cdelta."}
    holes = []
    for row in result["all_factory_hole_scenarios"]:
        compact = {k: v for k, v in row.items() if k not in (
            "oblique_end_note", "scope", "signed_force_available", "finished_member_distance",
            "complete_geometry_factor", "strength_pass")}
        for name in ("end_rays", "edge_rays"):
            if name not in row:
                continue
            rays = []
            for ray in row[name]:
                saved = {k: v for k, v in ray.items() if k != "owning_facets"}
                saved["owning_raw_facet_vertex_indices"] = [f["raw_facet_vertex_indices"] for f in ray["owning_facets"]]
                for factor in ("softwood_toward_end_factor_only", "away_or_perpendicular_factor_only"):
                    if factor in saved and saved[factor] is not None:
                        saved[factor] = saved[factor]["end_factor_only"]
                rays.append(saved)
            compact[name] = rays
        holes.append(compact)
    out["all_factory_hole_scenarios"] = holes
    out["all_hole_claim_limits"] = {"signed_force_available": False, "finished_member_distance": None,
                                    "complete_geometry_factor": None, "strength_pass": False,
                                    "near_wood_holes_drilled_or_occupied": False,
                                    "oblique_end_factor": None}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=LEAF / "input.json")
    parser.add_argument("--far-offset-mm", type=float, default=65.0875)
    parser.add_argument("--depth-shift-mm", type=float, default=0.)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = compact_receipt(evaluate(args.input, far_offset_mm=args.far_offset_mm, depth_shift_mm=args.depth_shift_mm))
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"out": str(args.out), "sha256": sha(args.out), "counts": result["counts"], "summary": result["summary"]}))
