"""Source-only Z180 receiver and nominal washer-seat applicability.

Uses saved convex X-extruded stock profiles and the complete recorded own-bore
inventory. No BREP import/query/rebuild, mechanics, model edit or tool pass.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUTS = OWN.with_name("inputs.json")
INPUT_SHA = "e3fda210640db0bc395d808c90625d65e8049da315c0872da12077731e6f0e41"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "frozen source changed: " + path)


def pure(ref, name):
    require(sha(ROOT / ref["path"]) == ref["sha256"], "exact pure helper required")
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def polygon_margin(point, polygon):
    """Signed circle-to-convex-profile margin before subtracting its radius."""
    distances = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
        dy, dz = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dy, dz)
        require(length > 0, "nondegenerate polygon edge required")
        distances.append((dy*(point[1]-a[1])-dz*(point[0]-a[0]))/length)
    return min(distances)


def profile(row, helper):
    world = [helper.world(v, row["datum_xyz_mm"], row["basis_grain_u_v_xyz"]) for v in row["vertices_luv_mm"]]
    xs = sorted({p[0] for p in world})
    yz = sorted({tuple(p[1:]) for p in world})
    require(len(xs) == 2 and len(yz) == 4 and len(world) == 8 and xs[1] > xs[0], "four-vertex straight X extrusion required")
    require({tuple(p) for p in world} == {(x, *v) for x in xs for v in yz}, "source extrusion corners differ")
    center = [sum(p[i] for p in yz)/len(yz) for i in (0, 1)]
    polygon = sorted(yz, key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))
    require(all(polygon_margin(p, polygon) >= -2e-8 for p in polygon), "convex source profile required")
    area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True))/2
    require(area > 0, "positive CCW polygon required")
    return {"X_interval_mm": xs, "YZ_polygon_mm": polygon, "raw_volume_mm3": area*(xs[1]-xs[0]), "thickness_mm": xs[1]-xs[0]}


def existing_inventory(inp, data, helper):
    geometry, cache, profiles = data["geometry"], data["cache"], data["profiles"]
    axes = {r["id"]: r for r in geometry["axes"]}
    ids = set(inp["axis_ids"])
    require(len(axes) == 100 and len(geometry["screw_axes"]) == 66 and len(ids) == 4, "current100/66 and four targets required")
    require(geometry["revision"] == inp["current_revision"] == data["placement"]["base_revision"] and data["placement"]["geometry_adopted"] is False, "current unadopted revision required")
    require(geometry["axes"] == data["base"]["axes"] and geometry["screw_axes"] == data["base"]["screw_axes"], "unchanged current v3 axes required")
    require({s["axis_id"]: s["source_axis"] for s in cache["shafts"]} == axes, "current cache source-axis identity differs")
    require({s["id"]: s["source_screw_descriptor"] for s in cache["hillman_rows"]} == {s["axis_id"]: s for s in geometry["screw_axes"]}, "current screw identity differs")
    require(canonical(geometry["axes"]) == data["placement"]["current_100_axes_canonical_sha256"] and canonical(geometry["screw_axes"]) == data["placement"]["current_66_screws_canonical_sha256"], "current placement bindings differ")
    proposed = {r["id"]: r for r in data["placement"]["proposed_axes"]}
    require(set(proposed) == ids, "exact four proposed records required")
    for key in ids:
        current = axes[key]
        require(current["point_xyz_mm"][2] == inp["current_Z_mm"] == 200, "existing Z200 source required")
        expected = copy.deepcopy(current)
        expected["point_xyz_mm"][2] = inp["proposed_Z_mm"]
        require(proposed[key] == expected and inp["proposed_Z_mm"] == 180, "only explicit Z180 source translation allowed")
    members, cuts = {}, {}
    observations = {r["id"]: r for r in cache["finished_body_observations"]}
    tolerances = inp["numerical_tolerances"]
    for name in inp["receivers"]:
        r = profiles[name]
        shape = profile(r, helper)
        require(abs(shape["thickness_mm"]-38.1) < tolerances["source_coordinate_mm"], "current38.1mm receiver required")
        bound = observations[name]
        require(bound["source"]["path"] == r["finished"]["path"] and bound["source"]["sha256"] == r["finished"]["sha256"] and abs(bound["volume_mm3"]-r["finished"]["volume_mm3"]) < tolerances["saved_volume_mm3"], "current finished metadata binding differs")
        own = [a for a in geometry["axes"] if name in a["receivers"]]
        require(len(own) == 4 and all(abs(a["direction_xyz"][0]) == 1 and a["direction_xyz"][1:] == [0, 0] and a["diameter_mm"] == 9.525 for a in own), "four own transverse3/8in bore records required")
        require(all(polygon_margin(a["point_xyz_mm"][1:], shape["YZ_polygon_mm"])-a["bore_diameter_mm"]/2 > 0 for a in own), "each current bore cross-section must lie inside its raw profile")
        require(all(math.dist(a["point_xyz_mm"][1:], b["point_xyz_mm"][1:]) > (a["bore_diameter_mm"]+b["bore_diameter_mm"])/2 for i, a in enumerate(own) for b in own[i+1:]), "disjoint own current bore cylinders required for volume identity")
        for source in ("bottom", "aligned", "base"):
            require(not any(row["receiver"] == name for row in data[source]["service_cuts"]), "affected recorded service cut requires a new method")
        walls = [w for w in cache["finished_receiver_wall_queries"] if w["receiver"] == name]
        require({w["axis_id"] for w in walls} == {a["id"] for a in own} and len(walls) == 4, "all four existing own wall observations required")
        require(all(abs(w["full_wall_length_mm"]-shape["thickness_mm"]) < tolerances["source_coordinate_mm"] and w["partial_wall_present"] is False for w in walls), "existing source full walls differ")
        void = sum(math.pi*(a["bore_diameter_mm"]/2)**2*shape["thickness_mm"] for a in own)
        error = shape["raw_volume_mm3"]-void-r["finished"]["volume_mm3"]
        require(abs(error) < tolerances["saved_volume_mm3"], "raw-minus-recorded-bores volume consistency failed")
        members[name] = {**shape, "finished_source": r["finished"], "cached_topology_counts": bound["strict_container"]["canonical_solid_topology_counts"], "current_own_bore_axis_ids": [a["id"] for a in own],
                         "current_bore_void_volume_mm3": void, "raw_minus_bores_minus_finished_volume_error_mm3": error,
                         "current_services_recorded_on_receiver": 0, "modeled_timber_screw_pilots": False}
        cuts[name] = own
    require({n for a in proposed.values() for n in a["receivers"]} == set(members), "proposed receiver census differs")
    return axes, proposed, members, cuts


def scenarios(inp, proposed, members, current_cuts, capsule):
    records = []
    for mode in ("current_modeled_bores", "all_affected_wood_bores_max11p1125"):
        for inventory in ("retain_existing_Z200_voids_for_read_only_comparison", "replace_eight_Z200_receiver_voids_from_raw_profiles"):
            walls, seats = [], []
            for key, a in proposed.items():
                radius = (a["bore_diameter_mm"] if mode == "current_modeled_bores" else inp["maximum_affected_wood_bore_diameter_mm"])/2
                h = a["hardware_scenario"]
                outer, inner = h["washer_od_mm"]/2, h["washer_id_mm"]/2
                require(a["before_plate_mm"] == a["after_plate_mm"] == 0 and radius <= inner, "nominal wood-seat inner opening must contain own bore")
                intervals = []
                for name in a["receivers"]:
                    stock = members[name]
                    xlo, xhi = stock["X_interval_mm"]
                    point, direction = a["point_xyz_mm"], a["direction_xyz"]
                    intervals.append(sorted((direction[0]*(xlo-point[0]), direction[0]*(xhi-point[0]))))
                    own = []
                    for cut in current_cuts[name]:
                        if cut["id"] in proposed and inventory.startswith("replace_"):
                            continue
                        own.append(cut)
                    own.extend(p for p in proposed.values() if name in p["receivers"])
                    primitives = []
                    for cut in own:
                        if cut is a:
                            continue
                        r = (cut["bore_diameter_mm"] if mode == "current_modeled_bores" else inp["maximum_affected_wood_bore_diameter_mm"])/2
                        primitive = capsule.primitive(cut["id"], "other_recorded_wood_bore", cut["point_xyz_mm"], cut["direction_xyz"], -1, cut["grip_mm"]+1, r)
                        primitive["cut_geometry_provenance"] = "proposed_Z180" if cut is proposed.get(cut["id"]) else "current_recorded_cut"
                        primitive["source_point_xyz_mm"] = cut["point_xyz_mm"]
                        primitives.append(primitive)

                    def compare(first, other):
                        return {**capsule.pair(first, other), "second_cut_geometry_provenance": other["cut_geometry_provenance"], "second_source_point_xyz_mm": other["source_point_xyz_mm"]}
                    center_margin = polygon_margin(point[1:], stock["YZ_polygon_mm"])
                    wall = capsule.primitive(key, "proposed_receiver_bore", [xlo, point[1], point[2]], [1, 0, 0], 0, xhi-xlo, radius)
                    comparisons = [compare(wall, c) for c in primitives]
                    minimum = min(comparisons, key=lambda c: c["capsule_separation_lower_bound_mm"])
                    supported = center_margin-radius > 0 and minimum["capsule_separation_lower_bound_mm"] > 0
                    walls.append({"axis_id": key, "receiver": name, "center_xyz_mm": point, "X_material_interval_mm": [xlo, xhi], "source_full_thickness_mm": stock["thickness_mm"],
                                  "candidate_bore_diameter_mm": 2*radius, "stock_edge_center_margin_mm": center_margin, "bore_to_raw_profile_edge_lower_bound_mm": center_margin-radius,
                                  "other_cut_comparisons": len(comparisons), "minimum_other_cut_separation": minimum, "source_recipe_analytic_full_circumference_supported": supported,
                                  "new_finished_BREP_wall_queried": False})
                    for end, station, inward in (("head", 0., direction[0]), ("nut", a["grip_mm"], -direction[0])):
                        x = point[0]+station*direction[0]
                        if abs(x-(xlo if inward > 0 else xhi)) > inp["numerical_tolerances"]["source_coordinate_mm"]:
                            continue
                        skin = capsule.primitive(key, "nominal_own_annular_skin_containing_disk", [x, point[1], point[2]], [inward, 0, 0], 0, inp["annular_inward_skin_mm"], outer)
                        comparisons = [compare(skin, c) for c in primitives]
                        minimum = min(comparisons, key=lambda c: c["capsule_separation_lower_bound_mm"])
                        supported = radius <= inner and center_margin-outer > 0 and minimum["capsule_separation_lower_bound_mm"] > 0
                        seats.append({"axis_id": key, "end": end, "receiver": name, "support_point_xyz_mm": [x, point[1], point[2]], "inward_X_sign": inward,
                                      "nominal_washer_ID_mm": 2*inner, "nominal_washer_OD_mm": 2*outer, "inward_skin_mm": inp["annular_inward_skin_mm"],
                                      "own_bore_to_annular_inner_radius_margin_mm": inner-radius, "annular_outer_edge_to_raw_profile_lower_bound_mm": center_margin-outer,
                                      "other_cut_comparisons": len(comparisons), "minimum_other_cut_separation": minimum,
                                      "source_recipe_analytic_full_nominal_annulus_supported": supported, "new_finished_BREP_annular_skin_queried": False, "physical_contact_or_strength_qualified": False})
                ordered = sorted(intervals)
                require(len(ordered) == 2 and abs(ordered[0][0]) < 2e-8 and abs(ordered[0][1]-ordered[1][0]) < 2e-8 and abs(ordered[1][1]-a["grip_mm"]) < 2e-8, "two contiguous own38.1mm receivers/grip required")
            require(len(walls) == 8 and len(seats) == 8 and len({(s["axis_id"], s["end"]) for s in seats}) == 8, "eight unique bore occurrences and external annuli required")
            require(all(w["source_recipe_analytic_full_circumference_supported"] for w in walls) and all(s["source_recipe_analytic_full_nominal_annulus_supported"] for s in seats), "source-only bore/seat separation not established")
            records.append({"bore_scenario": mode, "void_inventory": inventory, "bore_occurrences": walls, "nominal_annular_seats": seats,
                            "minimum_raw_profile_bore_margin_mm": min(w["bore_to_raw_profile_edge_lower_bound_mm"] for w in walls),
                            "minimum_bore_to_other_cut_lower_bound_mm": min(w["minimum_other_cut_separation"]["capsule_separation_lower_bound_mm"] for w in walls),
                            "minimum_raw_profile_annular_outer_margin_mm": min(s["annular_outer_edge_to_raw_profile_lower_bound_mm"] for s in seats),
                            "minimum_annular_disk_to_other_cut_lower_bound_mm": min(s["minimum_other_cut_separation"]["capsule_separation_lower_bound_mm"] for s in seats)})
    return records


def fixtures(capsule):
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    diamond = [(0, -5), (5, 0), (0, 5), (-5, 0)]
    require(polygon_margin([3, 4], square) == 3 and polygon_margin([-1, 4], square) == -1, "signed polygon fixture failed")
    require(abs(polygon_margin([0, 0], diamond)-5/math.sqrt(2)) < 1e-14, "inclined polygon fixture failed")
    first = capsule.primitive("annulus", "disk", [0, 0, 0], [1, 0, 0], 0, .05, 13.081)
    other = capsule.primitive("old_hole", "cut", [0, 0, 20], [1, 0, 0], -1, 39.1, 5.55625)
    require(abs(capsule.pair(first, other)["capsule_separation_lower_bound_mm"]-1.36275) < 1e-13, "old-hole/annulus fixture failed")
    other = capsule.primitive("cut", "overlap", [0, 0, 10], [1, 0, 0], -1, 39.1, 5.55625)
    require(capsule.pair(first, other)["capsule_separation_lower_bound_mm"] < 0, "intersecting-cut control failed")
    require(polygon_margin([1, 1], square)-2 < 0 and other["containing_capsule_radius_mm"] > 5.159375, "edge/own-inner-opening controls failed")
    return {"reused_capsule_known_answers": capsule.known_answers(), "new_hand_arithmetic_fixtures": 4,
            "negative_proof_controls": ["circle_crosses_stock_edge", "other_cut_crosses_seat_disk", "own_bore_exceeds_annular_inner_opening"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.resolve().parent == OWN.parent and not args.out.exists(), "fresh direct output in owned packet required")
    require(sha(INPUTS) == INPUT_SHA, "exact receiver/seat input required")
    inp = read(INPUTS)
    pins = {**inp["source_sha256"], str(OWN.relative_to(ROOT)): sha(OWN), str(INPUTS.relative_to(ROOT)): INPUT_SHA}
    verify(pins)
    data = {key: read(ROOT / ref["path"]) for key, ref in inp["sources"].items() if ref["path"].endswith(".json")}
    datum = pure(inp["sources"]["datum_helper"], "reused_current_shop_datum_math")
    capsule = pure(inp["sources"]["capsule_helper"], "reused_current_cleat_capsule_math")
    control = fixtures(capsule)
    axes, proposed, members, own_cuts = existing_inventory(inp, data, datum)
    results = scenarios(inp, proposed, members, own_cuts, capsule)
    require(not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy")), "source-only standard-library execution required")
    verify(pins)
    result = {"schema": "eoere_current_Z180_source_profile_receiver_and_nominal_seat_applicability/v1", "status": "UNADOPTED_SOURCE_RECIPE_ANALYTIC_BORE_AND_SEAT_CONTAINMENT_SUPPORTED",
              "source_sha256": dict(sorted(pins.items())), "sources_unchanged_before_after": True, "current_revision": inp["current_revision"],
              "current_geometry_adopted_or_changed": False, "optional_2026_extra": False, "proposed_axes": list(proposed.values()),
              "current100_axes_canonical_sha256": canonical(data["geometry"]["axes"]), "current66_screws_canonical_sha256": canonical(data["geometry"]["screw_axes"]),
              "retained_other_current_axes": len(axes)-len(proposed), "retained_current_screws": 66, "affected_members": members, "scenarios": results, "method_controls": control,
              "proof": ["Four-vertex convex stock profiles are authenticated straight38.1mm X extrusions. The minimum signed edge-line distance bounds the complete bore/annular outer circle inside the source profile.",
                        "Each affected receiver has four own current X bore records, four cached full-wall observations and no recorded service cuts. Raw profile minus these disjoint cylinders matches saved finished volume; this checks consistency, not independently reconstructed topology or cut positions.",
                        "Existing finite-axis capsule helper bounds separation of each new bore cylinder or containing washer disk from every other own cut cylinder. A positive disk separation is sufficient for annular separation; own bore radius is separately required not to exceed washer ID radius.",
                        "Keeping existing Z200 voids is a read-only source-material comparison. Intended adoption must replace eight old void occurrences from raw profiles, preserving96other axes and66screws, rather than retain extra abandoned holes."],
              "required_next_inputs_or_queries": [
                  "Parent readiness for four source-bound receiver reconstructions and eight new finished full-circumference bore-wall observations; replace old Z200 cutters before applying Z180 cutters.",
                  "Eight own finished annular seat queries with declared washer/bore scenarios; recheck affected backing and all current panel/service/angle intersections without an optional-grid transfer.",
                  "Actual delivered washer ID/OD/thickness, bolt/body/root/runout, hole placement/diameters and bounded fit uncertainty. This packet uses only nominal current washers and a declared maximum-hole sensitivity.",
                  "Actual sockets/wrenches, drill/chuck/guide/clamps and bolt/nut/washer removal envelopes for eight target access sides and continuous removal corridors; no tool pass is inferred.",
                  "After any adoption, fresh descriptors, gravity and own actions plus signed end/edge/group/net/splitting/restraint and complete-joint disposition. Existing Z200 forces and reference ratios do not transfer."],
              "limits": inp["limits"]+["Screw pilots and owner installation countersinks are absent from modeled timber and are not added or qualified by this geometry arithmetic. Recorded screw-body clearance remains in the separate current placement screen.",
                                        "No new finished BREP was imported, queried, rebuilt or compared. Analytic source-recipe support remains distinct from native observed finished-face support, delivered machining, actual pressure and strength."],
              "execution": {"stdlib_JSON_and_source_byte_reads_only": True, "reused_pure_helpers": [inp["sources"][k] for k in ("datum_helper", "capsule_helper")],
                            "finished_BREP_bytes_authenticated_not_queried": True, "CAD_cache_query_rebuild_native_global_or_force_execution": False,
                            "model_shared_document_staging_or_commit_action": False, "command": list(sys.orig_argv), "python": sys.version},
              "complete_joint_resistance": None, "release": dict.fromkeys(("geometry_adopted", "mechanics_ready", "complete_joint_resistance", "fabrication", "structural", "climbing"), False)}
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    verify(pins)
    with args.out.open("xb") as stream:
        stream.write(raw)
    verify(pins)
    print(json.dumps({"result": str(args.out.resolve().relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "source_files": len(pins),
                      "scenarios": [{k: s[k] for k in ("bore_scenario", "void_inventory", "minimum_raw_profile_bore_margin_mm", "minimum_bore_to_other_cut_lower_bound_mm", "minimum_raw_profile_annular_outer_margin_mm", "minimum_annular_disk_to_other_cut_lower_bound_mm")} for s in results]}, sort_keys=True))


if __name__ == "__main__":
    main()
