"""Prepare eight saved-source washer replacements; only the parent calls run()."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
UPPER = HERE.parent / "upper-corner-screw-layout"
RAW = HERE / "rawlocal/top-washer-fit"
HELPER = HERE / "hardware_length_fit.py"
LENGTH = HERE / "rawlocal/hardware-length-fit/saved-source-attempt02"
OVERLAY = HERE / "rawlocal/upper-screw-travel/attempt01/result.json"
SUITE = UPPER / "rawlocal/retail-washer-suite/attempt01-fine"
PROPOSAL = HERE.parent / "top-corner-correction/proposal.json"
CATALOG = HERE.parent / "top-corner-hardware/hardware-inputs.json"
PINS = {
    HELPER: "fd54fbe3d7d59c504b4ec80519155a12802e593c98c8043867d80746977d5b8b",
    LENGTH / "setup.json": "c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529",
    LENGTH / "result.json": "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5",
    HERE / "upper-screw-travel.py": "08d879823afb9396d9af6197a9e5d82a0887485bff29a7292d6295575f881993",
    OVERLAY: "76379eb78eb73fbdcf9c6d4b5a0edf5497a0fcb67129f5d0eb956144b4dfb925",
    SUITE / "inputs-before.json": "2b29b4c1b851ce954819d81e3c3955a49606873651559e70a2de205fcb1f06ca",
    SUITE / "checks.json": "3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    CATALOG: "a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7",
    UPPER / "retail-washer.md": "c2845b8b395934a882b1636f6d5c1ae5441fd38cacf4fc5d6e11e6ed6fa65c62",
}
GATES = {"formal_acceptance": False, "complete_joint_acceptance": False,
         "physical_release": False, "delivered_hardware_fit_established": False,
         "physical_access_established": False, "full_turning_qualification": False,
         "geometry_rebuilt": False, "new_physics_performed": False,
         "software_tests_performed": False}


def require(condition, fact):
    if not condition:
        raise ValueError(fact)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def fresh(path):
    path = Path(path).resolve()
    require(path.parent == RAW.resolve() and not path.exists(), f"require a fresh immediate child of {RAW}: {path}")
    path.mkdir(parents=True, exist_ok=False)
    (path / ".gitignore").write_text("*\n")
    return path


def authenticate(pins):
    for relative, expected in pins.items():
        path = ROOT / relative
        require(path.is_file() and sha(path) == expected, f"unsupported source binding: {relative}; required SHA256 {expected}")


def cylinder_certificate(first, second):
    """Project pinned finite cylinders/sweeps onto their axis-separation normal."""
    if not first or not second:
        return None
    u = first["direction_xyz"]
    diff = [b-a for a, b in zip(first["start_xyz_mm"], second["start_xyz_mm"])]
    along = sum(a*b for a, b in zip(diff, u)) / sum(a*a for a in u)
    offset = [diff[i]-along*u[i] for i in range(3)]
    distance = math.sqrt(sum(a*a for a in offset))
    if distance == 0:
        return None
    normal, intervals = [a/distance for a in offset], []
    for primitive in (first, second):
        axis = primitive["direction_xyz"]
        require(abs(sum(a*a for a in axis)-1) < 1e-12, "primitive axis is not unit length")
        unit = [a/math.sqrt(sum(b*b for b in axis)) for a in axis]
        cosine = sum(a*b for a, b in zip(unit, normal))
        radial = primitive["radius_mm"] * math.sqrt(max(0.0, 1-cosine*cosine))
        origin = sum(a*b for a, b in zip(primitive["start_xyz_mm"], normal))
        end = origin + primitive["length_mm"] * cosine
        intervals.append([min(origin, end)-radial, max(origin, end)+radial])
    gap = max(intervals[0][0]-intervals[1][1], intervals[1][0]-intervals[0][1])
    return {"method": "finite_cylinder_interval_projection", "normal_xyz": normal,
            "line_distance_mm": distance, "query_interval_mm": intervals[0],
            "obstacle_interval_mm": intervals[1], "separation_lower_bound_mm": gap}


def build():
    """Use frozen metadata and the existing stdlib enclosure functions only."""
    pins = {p.relative_to(ROOT).as_posix(): digest for p, digest in PINS.items()}
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(__file__)
    authenticate(pins)
    saved, previous, overlay, suite, checked, proposal, catalog = map(read, (
        LENGTH / "setup.json", LENGTH / "result.json", OVERLAY,
        SUITE / "inputs-before.json", SUITE / "checks.json", PROPOSAL, CATALOG))
    for document in (saved, suite, overlay):
        for name, digest in document["source_sha256"].items():
            path = ROOT / name
            relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
            require(relative not in pins or pins[relative] == digest, f"conflicting frozen source binding: {relative}")
            pins[relative] = digest
    authenticate(pins)
    require(previous["producer_sha256"] == PINS[HELPER] and previous["setup_sha256"] == PINS[LENGTH / "setup.json"]
            and previous["source_unchanged_after_run"] and not previous["geometry_rebuilt"], "length receipt binding differs")
    require(overlay["source_unchanged_after_run"] and not overlay["geometry_rebuilt"]
            and overlay["counts"]["relocated_screws"] == 4, "upper-screw overlay binding differs")
    require(checked["source_pins_unchanged"] and checked["envelope_covers_all_48"]
            and checked["counts"]["completed_end_states"] == 48 and checked["setup_failure"] is None,
            "retail suite is not the completed frozen 48-end result")
    require(suite["nominal_support_inventory"] == checked["nominal_support_inventory"], "eight saved seat lands differ")
    require(suite["model"]["family"] == checked["model"]["family"] == {
        "inner_radius_mm": 4.1529, "outer_radius_mm": 12.7, "head_radius_mm": 5.0, "thickness_mm": 2.5}, "fixed washer geometry differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_top_washer_bounds", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    obstacles = copy.deepcopy(saved["obstacles"])
    indexed = {row["id"]: row for row in obstacles}
    for move in overlay["relocated_screws"]:
        row = indexed[move["source_obstacle_id"]]
        require(row["bounds_xyz_mm"] == move["before_bounds_xyz_mm"], f"overlay before enclosure differs: {row['id']}")
        row["bounds_xyz_mm"] = move["translated_bounds_xyz_mm"]
        row["overlay_source"] = OVERLAY.relative_to(ROOT).as_posix()
    require(len(obstacles) == len(indexed) == 1009 and saved["obstacle_counts"]["wood"] == 50,
            "saved installed obstacle census differs")
    top = saved["top_corner_axes_for_separation_certificate"]
    require(len(top) == 8, "eight corrected top stacks required")
    obstacles = [row for row in obstacles if row["category"] != "corrected_top_stack"]
    approaches = {(row["axis_id"], row["end"]): row for row in proposal["straight_tool_approach_scenarios"]}
    snapshot = read(ROOT / saved["source_files"]["geometry_snapshot"])
    access_path = helper.ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json"
    access = {row["axis_id"]: row["operations"] for row in read(access_path)["axis_operations"]}
    lands = suite["nominal_support_inventory"]
    queries, replacements = [], []
    parts = catalog["catalog_parts"]
    for axis_id, row in top.items():
        rail = "/rail_" in axis_id
        family = "rail" if rail else "side"
        bolt = parts["rail_bolt_grade5_lawson" if rail else "side_bolt_grade8"]
        nut = parts["rail_nut_grade5" if rail else "side_nut_grade8"]
        washer = parts[f"{family}_washer_uss"]
        try:
            head_radius = bolt["head"]["across_flats"]["mm"]["maximum"] / math.sqrt(3)
            head_height = bolt["head"]["height"]["mm"]["maximum"]
            nut_radius = nut["across_flats"]["mm"]["maximum"] / math.sqrt(3)
            nut_height = nut["height"]["mm"]["maximum"]
            old_min, old_max = (washer["thickness"]["mm"][k] for k in ("minimum", "maximum"))
        except KeyError as exc:
            raise ValueError(f"unsupported {family} catalog component bound: missing {exc}") from exc
        require(row["proposed_underhead_length_mm"] == 203.2 and row["proposed_wood_grip_mm"] == 177.8,
                f"{axis_id}: frozen nominal shaft/grip differs")
        head = approaches[axis_id, "head"]
        direction = helper._vec3([-v for v in head["outward_axis_xyz"]], axis_id)
        outward = [-v for v in direction]
        source_start = head["proposed_bolt_underhead_mm"]
        host_seat = helper._add_scaled(source_start, direction, old_max)
        cleat_seat = helper._add_scaled(host_seat, direction, 177.8)
        if rail:
            require([old_min, old_max] == [1.2954, 2.032], "saved catalog thickness range differs")
            for role, seat in (("host", host_seat), ("cleat", cleat_seat)):
                land = lands[f"{axis_id}/{role}"]
                require(max(abs(a - b) for a, b in zip(seat, land["seat_xyz_mm"])) < 1e-5,
                        f"{axis_id}/{role}: corrected endpoint does not bind physical wood seat")
                seat[:] = land["seat_xyz_mm"]
            records = [r for r in suite["end_records"] if r["axis_id"] == axis_id]
            require(len(records) == 12 and all(max(abs(a-b) for a,b in zip(direction, r["source_bolt_axis_head_to_nut_xyz"])) < 1e-7
                    and r["nominal_outer_wood_seat_xyz_mm"] == lands[r["support_id"]]["seat_xyz_mm"] for r in records),
                    f"{axis_id}: repeated case seat/axis binding differs")
        thickness = 2.5 if rail else old_max
        radius = 12.7 if rail else washer["outside_diameter"]["mm"]["maximum"] / 2
        start = helper._add_scaled(host_seat, outward, thickness)
        prefix = f"corrected_top_component/{axis_id}/"
        shapes = {
            "shaft": (start, direction, 203.2, row["nominal_bolt_diameter_mm"] / 2),
            "head": (start, outward, head_height, head_radius),
            "head_washer": (host_seat, outward, thickness, radius),
            "nut_washer": (cleat_seat, direction, thickness, radius),
            "nut": (helper._add_scaled(cleat_seat, direction, thickness), direction, nut_height, nut_radius),
        }
        installed = {}
        for role, (origin, axis, length, rad) in shapes.items():
            cylinder = {"start_xyz_mm": origin, "direction_xyz": list(axis), "length_mm": length, "radius_mm": rad}
            bounds = helper._inflate(helper._cylinder_bounds(origin, helper._add_scaled(origin, axis, length), axis, rad))
            item = {"id": prefix + role, "axis_id": axis_id, "category": "corrected_top_component",
                    "component": role, "bounds_xyz_mm": bounds, "cylinder": cylinder,
                    "geometry_limit": "Conditional source catalog regular-hex circumscribed cylinder or nominal shaft/outer washer disk; no exact installed STEP/profile."}
            if "washer" in role:
                item["inside_diameter_mm"] = 8.3058 if rail else washer["inside_diameter"]["mm"]["maximum"]
            obstacles.append(item)
            installed[role] = item
        if not rail:
            continue
        old_ops = access[axis_id]
        old_length = float(snapshot["axes"][axis_id]["hardware"]["shaft"]["volume_mm3"]) / (math.pi * (6.35 / 2)**2)
        require(abs(old_length - 152.4) < 1e-5, f"{axis_id}: source shaft length is not the saved 152.4 mm cylinder")
        old_head_travel = old_ops["head_side_bolt"]["derived_travel_mm"]
        require(abs(old_head_travel - (old_length - old_max)) < 1e-5, f"{axis_id}: source withdrawal datum differs")
        travel = {"head": 203.2 - thickness, "head_washer": 203.2 - thickness,
                  "nut": 203.2 - 177.8 - 2 * thickness, "nut_washer": 203.2 - 177.8 - thickness}
        shifts = [thickness - old_max, thickness - old_min]
        replacements.append({"axis_id": axis_id, "host_seat_xyz_mm": host_seat, "cleat_seat_xyz_mm": cleat_seat,
                             "underhead_xyz_mm": start, "tip_xyz_mm": helper._add_scaled(start, direction, 203.2),
                             "added_end_thickness_range_mm": shifts, "added_both_end_thickness_range_mm": [2*v for v in shifts],
                             "nut_shift_at_wood_seat_mm": shifts, "nut_shift_from_bolt_underhead_mm": [2*v for v in shifts],
                             "saved_headward_travel_mm": old_head_travel, "corrected_prior_headward_travel_mm": 203.2-old_max,
                             "replacement_travels_mm": travel, "additional_headward_stroke_mm": 0.0})
        for role in ("head_washer", "nut_washer", "head", "nut"):
            own = installed[role]
            contact_roles = {"head_washer": ["shaft", "head"], "nut_washer": ["shaft", "nut"],
                             "head": ["shaft", "head_washer"], "nut": ["shaft", "nut_washer"]}[role]
            for moving in (False, True):
                query = copy.deepcopy(own)
                query["id"] = f"{axis_id}/{role}/{'replacement_removal_enclosure' if moving else 'installed'}"
                excluded = {prefix+role: "active query component", **{prefix+r: "named coaxial engagement or adjacent seat contact" for r in contact_roles}}
                if moving and role in ("head", "head_washer"):
                    excluded.update({prefix+r: "documented prior removal of own nut and nut washer" for r in ("nut", "nut_washer")})
                if moving and role == "nut_washer":
                    excluded[prefix+"nut"] = "own nut removed before washer slide"
                query["excluded_obstacle_ids"] = excluded
                query["intended_wood_seat_id"] = "wood/" + lands[f"{axis_id}/{'host' if role.startswith('head') else 'cleat'}"]["receiver"]
                if moving:
                    query["inherited_conditional_route"] = "straight coaxial removal, after prerequisite nut disengagement/capture; no turning proof"
                    query["cylinder"]["length_mm"] += travel[role]
                    c = query["cylinder"]
                    query["bounds_xyz_mm"] = helper._inflate(helper._cylinder_bounds(c["start_xyz_mm"], helper._add_scaled(c["start_xyz_mm"], c["direction_xyz"], c["length_mm"]), c["direction_xyz"], c["radius_mm"]))
                queries.append(query)
        collar_start = helper._add_scaled(host_seat, outward, old_min)
        collar = {"start_xyz_mm": collar_start, "direction_xyz": outward, "length_mm": shifts[1], "radius_mm": 6.35/2}
        queries.append({"id": axis_id + "/shaft/added_underhead_offset", "axis_id": axis_id, "cylinder": collar,
                        "bounds_xyz_mm": helper._inflate(helper._cylinder_bounds(collar_start, start, outward, 6.35/2)),
                        "excluded_obstacle_ids": {prefix+r: "named own shaft or coaxial head/washer engagement" for r in ("shaft", "head", "head_washer")}})
    require(len(lands) == 8 and len(replacements) == 4 and len(queries) == 36 and len(obstacles) == 1041,
            "bounded replacement/obstacle census differs")
    pairs, exclusions = [], []
    for query in queries:
        for other in obstacles:
            pair = {"query_id": query["id"], "obstacle_id": other["id"]}
            if other["id"] in query["excluded_obstacle_ids"]:
                exclusions.append({**pair, "reason": query["excluded_obstacle_ids"][other["id"]]})
                continue
            gap = helper._box_gap(query["bounds_xyz_mm"], other["bounds_xyz_mm"])
            certificate = cylinder_certificate(query.get("cylinder"), other.get("cylinder")) if gap == 0 and "step_path" not in other else None
            if certificate and certificate["separation_lower_bound_mm"] > 0:
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap,
                              "status": "clear_by_finite_cylinder_projection", "projection_certificate": certificate})
                continue
            pairs.append({**pair, "AABB_distance_lower_bound_mm": gap,
                          "intended_wood_seat_contact": other["id"] == query.get("intended_wood_seat_id"),
                          "status": "clear_by_conservative_AABB_separation" if gap > 0 else
                          "parent_saved_STEP_check_required" if "step_path" in other else "undecided_specific_pair"})
    authenticate(pins)
    return {"schema": "top_washer_fit_preflight/v1", "status": "PREPARED_ONLY", "source_sha256": pins,
            "obstacles": obstacles, "queries": queries, "pairs": pairs, "explicit_exclusions": exclusions,
            "replacements": replacements, "nominal_support_inventory": lands,
            "old_corrected_stack_ids_replaced": [r["id"] for r in saved["obstacles"] if r["category"] == "corrected_top_stack"],
            "counts": {"washers": 8, "rail_axes": 4, "queries": len(queries), "obstacles": len(obstacles),
                       "pairs": len(pairs), "exclusions": len(exclusions), "moved_screw_enclosures": 4, "unchanged_screw_enclosures": 62},
            "conditional_engagement_mm": {"nominal_length": 203.2, "wood_grip": 177.8, "required_LB": 145.375,
                                          "full_form_window": [182.8, 188.5404], "Lmin": 192.3504},
            "cad_run_executed": False, **GATES}


def prepare(output_dir):
    setup = build()
    output = fresh(output_dir)
    snapshots = output / "input-snapshots"
    snapshots.mkdir()
    manifest = {}
    for relative, digest in setup["source_sha256"].items():
        target = snapshots / digest
        if not target.exists():
            shutil.copyfile(ROOT / relative, target)
        require(sha(target) == digest, f"snapshot binding differs: {relative}")
        manifest[relative] = {"path": target.relative_to(output).as_posix(), "sha256": digest}
    authenticate(setup["source_sha256"])
    dump(output / "snapshot-manifest.json", manifest)
    setup["snapshot_manifest_sha256"] = sha(output / "snapshot-manifest.json")
    dump(output / "setup.json", setup)
    print(json.dumps({"status": setup["status"], "setup_sha256": sha(output/"setup.json"), "counts": setup["counts"]}))
    return output / "setup.json"


def run(*, output_dir, setup_path=RAW / "prepare-attempt02/setup.json"):
    """Parent API: exact saved STEP intersections only for prepared overlaps."""
    setup_path = Path(setup_path).resolve()
    setup = read(setup_path)
    authenticate(setup["source_sha256"])
    require(sha(__file__) == setup["source_sha256"][Path(__file__).relative_to(ROOT).as_posix()], "producer differs from prepared snapshot")
    manifest_path = setup_path.parent / "snapshot-manifest.json"
    require(sha(manifest_path) == setup["snapshot_manifest_sha256"], "snapshot manifest differs")
    manifest = read(manifest_path)
    for relative, digest in setup["source_sha256"].items():
        require(manifest[relative]["sha256"] == digest and sha(setup_path.parent / manifest[relative]["path"]) == digest,
                f"snapshot source differs: {relative}")
    output = fresh(output_dir)
    shutil.copyfile(__file__, output / "producer.py.snapshot")
    dump(output / "inputs-before.json", {"setup_path": str(setup_path), "setup_sha256": sha(setup_path), "source_sha256": setup["source_sha256"]})
    queries = {r["id"]: r for r in setup["queries"]}
    obstacles = {r["id"]: r for r in setup["obstacles"]}
    steps, cylinders, pairs = {}, {}, copy.deepcopy(setup["pairs"])
    for pair in pairs:
        if pair["status"] != "parent_saved_STEP_check_required":
            continue
        import cadquery as cq
        query, other = queries[pair["query_id"]], obstacles[pair["obstacle_id"]]
        path = other["step_path"]
        if path not in steps:
            steps[path] = cq.importers.importStep(str(setup_path.parent / manifest[path]["path"])).val()
            require(steps[path].isValid() and len(steps[path].Solids()) == 1, f"saved STEP is not one valid solid: {path}")
        if query["id"] not in cylinders:
            c = query["cylinder"]
            cylinders[query["id"]] = cq.Solid.makeCylinder(c["radius_mm"], c["length_mm"], cq.Vector(*c["start_xyz_mm"]), cq.Vector(*c["direction_xyz"]))
        moving, fixed = cylinders[query["id"]], steps[path]
        volume, distance = float(moving.intersect(fixed).Volume()), float(moving.distance(fixed))
        pair.update({"status": "overlapping_enclosure_requires_disposition" if volume > 1e-6 else "clear_by_saved_STEP_intersection",
                     "overlap_volume_mm3": volume, "minimum_distance_mm": distance, "step_path": path,
                     "STEP_sha256": setup["source_sha256"][path]})
    authenticate(setup["source_sha256"])
    require(sha(setup_path) == read(output / "inputs-before.json")["setup_sha256"], "prepared setup changed during run")
    unresolved = [p for p in pairs if p["status"] == "undecided_specific_pair"]
    overlaps = [p for p in pairs if p["status"] == "overlapping_enclosure_requires_disposition"]
    result = {"schema": "top_washer_fit_result/v1", "status": "STOP_ENCLOSURE_OVERLAP" if overlaps else
              "BOUNDED_FIT_UNDECIDED" if unresolved else "BOUNDED_NOMINAL_ENCLOSURES_CLEAR",
              "setup_sha256": sha(setup_path), "source_sha256": setup["source_sha256"], "source_unchanged_after_run": True,
              "counts": setup["counts"], "STEP_obstacles_loaded": len(steps), "pairs": pairs,
              "undecided_pairs": unresolved, "overlap_pairs": overlaps, "explicit_exclusions": setup["explicit_exclusions"],
              "minimum_positive_AABB_margin": min((p for p in pairs if p["AABB_distance_lower_bound_mm"] > 0), key=lambda p: p["AABB_distance_lower_bound_mm"]),
              "cad_run_executed": True, **GATES}
    dump(output / "result.json", result)
    dump(output / "receipt.json", {"output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()},
                                 "source_unchanged_after_run": True, "producer_sha256": sha(__file__)})
    print(json.dumps({"status": result["status"], "result_sha256": sha(output / "result.json"), "undecided_pairs": len(unresolved), "overlap_pairs": len(overlaps)}))
    return output / "result.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--setup", default=RAW / "prepare-attempt02/setup.json", type=Path)
    args = parser.parse_args()
    prepare(args.output_dir) if args.prepare else run(output_dir=args.output_dir, setup_path=args.setup)
