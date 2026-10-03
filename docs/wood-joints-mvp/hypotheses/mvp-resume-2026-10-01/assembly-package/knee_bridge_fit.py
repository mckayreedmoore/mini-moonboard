"""Prepare a bounded saved-scene fit screen for four proposed knee bolts.

Preparation uses only the standard library. The parent calls directrun() for
exact intersections of query cylinders with matching saved STEP obstacles.
"""

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

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-fit"
TOP_RAW = HERE / "rawlocal/top-washer-fit"
TOP_PREP = TOP_RAW / "prepare-attempt02"
TOP_RUN = TOP_RAW / "run-attempt01"
TOP_SETUP = TOP_PREP / "setup.json"
TOP_RESULT = TOP_RUN / "result.json"
TOP_MANIFEST = TOP_PREP / "snapshot-manifest.json"
LENGTH_SETUP = HERE / "rawlocal/hardware-length-fit/saved-source-attempt02/setup.json"
TOP_PRODUCER = HERE / "top_washer_fit.py"
BOUNDS_HELPER = HERE / "hardware_length_fit.py"
GEOMETRY = HERE.parent / "upper-corner-screw-layout/rawlocal/knee-spine-net-sections/attempt02/checks.json"
REINFORCEMENT = HERE.parent / "upper-corner-screw-layout/knee-spine-reinforcement.py"
CATALOG = HERE.parent / "top-corner-hardware/hardware-inputs.json"
FASTENER_INPUTS = HERE.parent.parent / "hardware-material-specification-2026-09-30/fastener-inputs.json"
EXPECTED = {
    TOP_SETUP: "d5b885bf3e023ca4efdcecd219453a288294d264692beb4d4bce100702928128",
    TOP_RESULT: "bc1bbfd01d6c002ffc7a9da4b14b44e47bb98c4809ef5059c7b3e10bddd1d797",
    TOP_MANIFEST: "c046e1d5b93a3ea69105171b1ab8958915f2a2ae81450c0fdc1d5b3547de7086",
    GEOMETRY: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
}
STOCK_MM = 165.1
LONG_BOUND_MM = 203.2
SHAFT_DIAMETER_MM = 6.35
BORE_DIAMETER_MM = 7.5
WASHER_OD_ID_THICKNESS_MM = (25.4, 8.3058, 2.5)
CENTERS_GU_MM = ((100.0, 0.0), (250.0, 0.0))
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")
FLAGS = {
    "proposal_adopted": False,
    "delivered_hardware_fit_established": False,
    "tool_fit_or_turning_qualified": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "scene_rebuilt": False,
    "CAD_run_executed": False,
    "tests_or_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    value = json.loads(Path(path).read_text())
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def fresh(output):
    output = Path(output).resolve()
    RAW.mkdir(parents=True, exist_ok=True)
    require(output.parent == RAW.resolve() and not output.exists(), f"require fresh immediate child of {RAW}: {output}")
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
    return output


def unit(vector, label):
    values = [float(value) for value in vector]
    require(len(values) == 3 and all(math.isfinite(value) for value in values), f"{label}: invalid 3-vector")
    length = math.sqrt(sum(value * value for value in values))
    require(length > 1e-12, f"{label}: zero vector")
    return [value / length for value in values]


def add_scaled(point, axis, amount):
    return [point[i] + axis[i] * amount for i in range(3)]


def world_point(source, local):
    rows = source["grain_frame_rows_xyz"]
    return [source["start_xyz_mm"][j] + sum(local[i] * rows[i][j] for i in range(3)) for j in range(3)]


def cylinder_bounds(start, axis, length, radius):
    end = add_scaled(start, axis, length)
    bounds = []
    for i in range(3):
        radial = radius * math.sqrt(max(0.0, 1.0 - axis[i] * axis[i]))
        bounds.extend([min(start[i], end[i]) - radial - 1e-6, max(start[i], end[i]) + radial + 1e-6])
    return bounds


def make_query(identity, axis_id, host_id, component, operation, start, direction, length, radius, limit, host_bore=False):
    direction = unit(direction, identity + " direction")
    cylinder = {
        "start_xyz_mm": [float(v) for v in start],
        "direction_xyz": direction,
        "length_mm": float(length),
        "radius_mm": float(radius),
    }
    return {
        "id": identity,
        "axis_id": axis_id,
        "host_obstacle_id": host_id,
        "component": component,
        "operation": operation,
        "cylinder": cylinder,
        "bounds_xyz_mm": cylinder_bounds(start, direction, length, radius),
        "geometry_limit": limit,
        "analytic_host_bore_exemption": host_bore,
    }


def annular_land(source, g, face_sign, washer):
    length, (width, depth) = source["grain_length_mm"], source["width_depth_mm"]
    outer, inner = washer[0] / 2, washer[1] / 2
    bore_radius = BORE_DIAMETER_MM / 2
    face_v = face_sign * depth / 2
    edge_grain = min(g, length - g) - outer
    edge_u = width / 2 - outer
    bore_land = inner - bore_radius
    old_bores = []
    for bore in source["bores"]:
        face_gap = abs(face_v - bore["transverse_center_mm"]) - bore["radius_mm"]
        old_bores.append({
            "axis_id": bore["axis_id"],
            "face_gap_outside_cutout_mm": face_gap,
            "cutout_reaches_face": face_gap <= 0.0,
        })
    other_axes = []
    for other_g, _other_u in CENTERS_GU_MM:
        if other_g == g:
            continue
        gap = abs(g - other_g) - 2 * bore_radius
        other_axes.append({"other_grain_center_mm": other_g, "bore_axis_clearance_mm": gap})
    supported = (
        edge_grain >= 0.0
        and edge_u >= 0.0
        and bore_land > 0.0
        and all(not row["cutout_reaches_face"] for row in old_bores)
        and all(row["bore_axis_clearance_mm"] > 0.0 for row in other_axes)
    )
    return {
        "status": "SUPPORTED_ANALYTICALLY" if supported else "STOP_UNSUPPORTED_LAND",
        "host_face_v_mm": face_v,
        "washer_annulus_mm": {"inner_radius": inner, "outer_radius": outer, "area_mm2": math.pi * (outer * outer - inner * inner)},
        "proposed_bore_radius_mm": bore_radius,
        "annular_radial_land_over_bore_mm": bore_land,
        "grain_end_margin_mm": edge_grain,
        "width_edge_margin_mm": edge_u,
        "existing_bore_cutouts": old_bores,
        "other_proposed_bores": other_axes,
        "basis": "Rectangular saved spine face; original full-width u-axis bores; proposed coaxial bore fits inside washer ID. No STEP face reconstruction.",
    }


def load_hardware():
    spec = importlib.util.spec_from_file_location("knee_bridge_reinforcement_inputs", REINFORCEMENT)
    require(spec is not None and spec.loader is not None, "reinforcement hardware source unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = module.HARDWARE
    catalog = read(CATALOG)["catalog_parts"]
    fasteners = read(FASTENER_INPUTS)["dimension_inputs"]
    head = catalog["rail_bolt_grade5_lawson"]
    nut = catalog["rail_nut_grade5"]
    nut_record = fasteners["nut"]
    require(policy["matched_metal_nut_lead"].startswith("K.L. Jack 25CNFH5Z"), "matched Grade 5 nut lead changed")
    require(nut_record["part"] == "K.L. Jack 25CNFH5Z", "matched nut dimension record changed")
    require(abs(policy["nut_height_envelope_mm"][1] - nut["height"]["mm"]["maximum"]) < 1e-9, "reinforcement and current catalog nut heights differ")
    require(abs(policy["nut_height_envelope_mm"][1] - nut_record["height_in"][1] * 25.4) < 1e-9, "nut record and current catalog height differ")
    require(abs(head["diameter"]["mm"]["nominal"] - SHAFT_DIAMETER_MM) < 1e-9, "quarter-inch bolt diameter differs")
    require(head["head"]["across_flats"]["mm"]["maximum"] > 0 and head["head"]["height"]["mm"]["maximum"] > 0, "head bounds missing")
    require(nut["material_standard"] == "SAE J995 Grade 5" and nut["thread"]["tpi"] == 20, "current Grade 5 nut dimensions changed")
    washer = list(WASHER_OD_ID_THICKNESS_MM)
    require(policy["washer_OD_ID_thickness_mm"] == washer, "reinforcement washer geometry differs")
    return {
        "stock": {
            "proposal_lead": "K.L. Jack 25C650HCS5Z, 1/4-20 x 6.5 in, Grade 5",
            "nominal_underhead_length_mm": STOCK_MM,
            "conservative_legacy_length_bound_mm": LONG_BOUND_MM,
            "thread_profile": "conditional catalog lead; delivered transition and full-form coordinates unknown",
            "source_note": "165.1 mm lead supplied by parent; 203.2 mm is bound only, not selected stock length.",
        },
        "head": {
            "source_item": head["item"],
            "across_flats_max_mm": head["head"]["across_flats"]["mm"]["maximum"],
            "height_max_mm": head["head"]["height"]["mm"]["maximum"],
            "circumscribed_radius_mm": head["head"]["across_flats"]["mm"]["maximum"] / math.sqrt(3.0),
            "limit": "conditional 1/4-in B18.2.1 head envelope; no delivered head profile",
        },
        "nut": {
            "matched_lead": policy["matched_metal_nut_lead"],
            "catalog_reference": nut["item"],
            "across_flats_max_mm": nut["across_flats"]["mm"]["maximum"],
            "height_range_mm": list(policy["nut_height_envelope_mm"]),
            "circumscribed_radius_mm": nut["across_flats"]["mm"]["maximum"] / math.sqrt(3.0),
            "limit": "conditional 1/4-20 Grade 5 finished-hex dimensional envelope; no delivered nut profile",
        },
        "washer": {
            "OD_ID_thickness_mm": washer,
            "filled_cylinder_fit_radius_mm": washer[0] / 2,
            "limit": "proposal envelope only; annular support checked analytically",
        },
    }


def validate_scene():
    for path, expected in EXPECTED.items():
        require(path.is_file() and sha(path) == expected, f"frozen top-fit binding changed: {path}")
    scene = read(TOP_SETUP)
    result = read(TOP_RESULT)
    manifest = read(TOP_MANIFEST)
    base_scene = read(LENGTH_SETUP)
    require(scene["status"] == "PREPARED_ONLY" and len(scene["obstacles"]) == 1041, "accepted top-fit obstacle set differs")
    require(key(LENGTH_SETUP) in scene["source_sha256"] and sha(LENGTH_SETUP) == scene["source_sha256"][key(LENGTH_SETUP)], "1009-obstacle saved scene binding differs")
    require(sha(TOP_PRODUCER) == scene["source_sha256"][key(TOP_PRODUCER)], "saved-scene producer differs from accepted setup")
    require(sha(BOUNDS_HELPER) == scene["source_sha256"][key(BOUNDS_HELPER)], "saved-scene bounds helper differs from accepted setup")
    require(len(base_scene["obstacles"]) == 1009, "saved pre-overlay obstacle count differs")
    require(len(scene["source_sha256"]) == 589 and len(manifest) == 589, "accepted top-fit source-pin census differs")
    require(result["status"] == "BOUNDED_NOMINAL_ENCLOSURES_CLEAR" and result["setup_sha256"] == EXPECTED[TOP_SETUP], "top-fit result is not accepted saved result")
    require(result["source_unchanged_after_run"] and result["source_sha256"] == scene["source_sha256"], "top-fit source receipt differs")
    require(scene["counts"]["moved_screw_enclosures"] == 4 and scene["counts"]["unchanged_screw_enclosures"] == 62, "current screw overlay differs")
    require(sum(row.get("category") == "wood" for row in scene["obstacles"]) == 50, "saved wood obstacle census differs")
    require(sum(row.get("category") == "panel_screw_envelope" for row in scene["obstacles"]) == 66, "saved Hillman envelope census differs")
    require(sum(row.get("category") == "corrected_top_component" for row in scene["obstacles"]) == 40, "current eight top stacks differ")
    require(set(manifest) == set(scene["source_sha256"]), "top-fit snapshot manifest source set differs")
    for relative, digest in scene["source_sha256"].items():
        row = manifest[relative]
        require(row["sha256"] == digest, f"top-fit snapshot hash differs: {relative}")
        snapshot = (TOP_PREP / row["path"]).resolve()
        require(snapshot.is_relative_to((TOP_PREP / "input-snapshots").resolve()) and snapshot.is_file(), f"top-fit snapshot missing: {relative}")
    return scene, manifest


def proposed_bore_geometry(source, block, g, direction):
    rows = source["grain_frame_rows_xyz"]
    depth = source["width_depth_mm"][1]
    center = world_point(source, [g, 0.0, 0.0])
    return {
        "block": block,
        "center_local_guv_mm": [g, 0.0, 0.0],
        "center_xyz_mm": center,
        "axis_direction_to_nut_xyz": direction,
        "axis_start_xyz_mm": world_point(source, [g, 0.0, -depth / 2]),
        "axis_end_xyz_mm": world_point(source, [g, 0.0, depth / 2]),
        "through_depth_mm": depth,
        "proposed_bore_diameter_mm": BORE_DIAMETER_MM,
        "status": "proposal_only_not_drill_instruction",
        "basis_rows_xyz": rows,
    }


def build_queries(geometry, hardware):
    queries, supports, stacks = [], [], []
    od, _id, washer_t = hardware["washer"]["OD_ID_thickness_mm"]
    nominal_r = SHAFT_DIAMETER_MM / 2
    head = hardware["head"]
    nut = hardware["nut"]
    nut_h = nut["height_range_mm"][1]
    for block in BLOCKS:
        source = geometry["geometry"][block]
        rows = [unit(row, block + " basis") for row in source["grain_frame_rows_xyz"]]
        require(source["grain_length_mm"] == 276.3 and abs(source["width_depth_mm"][0] - 38.1) < 1e-6 and abs(source["width_depth_mm"][1] - 139.7) < 1e-6, f"{block}: saved stock dimensions differ")
        require(max(abs(sum(rows[a][i] * rows[b][i] for i in range(3))) for a, b in ((0, 1), (0, 2), (1, 2))) < 1e-8, f"{block}: source basis not orthogonal")
        require(max(abs(rows[2][i] - source["grain_frame_rows_xyz"][2][i]) for i in range(3)) < 1e-8, f"{block}: local v basis differs")
        require(len(source["bores"]) == 4, f"{block}: saved original bore census differs")
        for bore in source["bores"]:
            local_axis = [sum(rows[j][i] * bore["axis_unit_global_xyz"][i] for i in range(3)) for j in range(3)]
            require(abs(abs(local_axis[1]) - 1.0) < 1e-7 and abs(local_axis[0]) < 1e-7 and abs(local_axis[2]) < 1e-7, f"{block}: original bore is not local-u aligned")
        v_to_nut = rows[2]
        depth = source["width_depth_mm"][1]
        host_id = "wood/" + block
        for g, u in CENTERS_GU_MM:
            axis_id = f"{block}/bridge_g{int(g)}"
            bore = proposed_bore_geometry(source, block, g, v_to_nut)
            head_face = world_point(source, [g, u, -depth / 2])
            nut_face = world_point(source, [g, u, depth / 2])
            head_washer = make_query(
                axis_id + "/head_washer/installed", axis_id, host_id, "head_washer", "installed",
                head_face, [-v for v in v_to_nut], washer_t, od / 2,
                "Filled OD cylinder conservatively encloses annular washer; wood land checked separately.",
            )
            nut_washer = make_query(
                axis_id + "/nut_washer/installed", axis_id, host_id, "nut_washer", "installed",
                nut_face, v_to_nut, washer_t, od / 2,
                "Filled OD cylinder conservatively encloses annular washer; wood land checked separately.",
            )
            underhead = add_scaled(head_face, v_to_nut, -washer_t)
            nut_seat = add_scaled(nut_face, v_to_nut, washer_t)
            shaft = make_query(
                axis_id + "/shaft/nominal", axis_id, host_id, "shaft", "installed_165.1_mm_stock",
                underhead, v_to_nut, STOCK_MM, nominal_r,
                "Nominal 6.5-in stock cylinder; thread and delivered profile remain conditional.", True,
            )
            shaft_bound = make_query(
                axis_id + "/shaft/203.2_mm_bound", axis_id, host_id, "shaft_bound", "conservative_extra_envelope_only",
                underhead, v_to_nut, LONG_BOUND_MM, nominal_r,
                "203.2-mm longest envelope only; not selected stock.", True,
            )
            head_query = make_query(
                axis_id + "/head/installed", axis_id, host_id, "head", "installed",
                underhead, [-v for v in v_to_nut], head["height_max_mm"], head["circumscribed_radius_mm"], head["limit"],
            )
            nut_query = make_query(
                axis_id + "/nut/installed", axis_id, host_id, "nut", "installed",
                nut_seat, v_to_nut, nut_h, nut["circumscribed_radius_mm"], nut["limit"],
            )
            nominal_tip_start = add_scaled(nut_seat, v_to_nut, nut_h)
            nominal_tip_len = STOCK_MM - (depth + 2 * washer_t + nut_h)
            bound_tip_len = LONG_BOUND_MM - (depth + 2 * washer_t + nut_h)
            require(nominal_tip_len > 0 and bound_tip_len > nominal_tip_len, f"{axis_id}: proposed bolt tip length is nonpositive")
            tip = make_query(
                axis_id + "/tip/nominal_protrusion", axis_id, host_id, "tip", "165.1_mm_stock_beyond_nut",
                nominal_tip_start, v_to_nut, nominal_tip_len, nominal_r,
                "Cylindrical nominal shaft projection beyond maximum nut envelope; no thread-tip profile.", True,
            )
            bound_tip = make_query(
                axis_id + "/tip/203.2_mm_bound", axis_id, host_id, "tip_bound", "extra_bound_beyond_nut",
                nominal_tip_start, v_to_nut, bound_tip_len, nominal_r,
                "203.2-mm conservative tail envelope only; not selected stock.", True,
            )
            shaft_sweep = make_query(
                axis_id + "/shaft/straight_install_withdraw", axis_id, host_id, "shaft", "straight_installation_and_withdrawal",
                add_scaled(underhead, v_to_nut, -STOCK_MM), v_to_nut, 2 * STOCK_MM, nominal_r,
                "Union of straight axial insertion and withdrawal paths for nominal stock; no tool or turning envelope.", True,
            )
            bound_sweep = make_query(
                axis_id + "/shaft/203.2_mm_straight_bound", axis_id, host_id, "shaft_bound", "conservative_extra_straight_envelope",
                add_scaled(underhead, v_to_nut, -LONG_BOUND_MM), v_to_nut, 2 * LONG_BOUND_MM, nominal_r,
                "Conservative axial occupancy bound only; no operation or selected 8-in stock claim.", True,
            )
            head_sweep = make_query(
                axis_id + "/head/straight_install_withdraw", axis_id, host_id, "head", "straight_bolt_assembly_path",
                underhead, [-v for v in v_to_nut], head["height_max_mm"] + STOCK_MM, head["circumscribed_radius_mm"],
                "Head cylinder swept with nominal bolt along its axis; no wrench or turning envelope.",
            )
            head_washer_sweep = make_query(
                axis_id + "/head_washer/straight_slide", axis_id, host_id, "head_washer", "straight_installation_and_withdrawal",
                head_face, [-v for v in v_to_nut], 2 * washer_t, od / 2,
                "Axial washer slide only; no handling or tool envelope.",
            )
            nut_washer_sweep = make_query(
                axis_id + "/nut_washer/straight_slide", axis_id, host_id, "nut_washer", "straight_installation_and_withdrawal",
                nut_face, v_to_nut, 2 * washer_t, od / 2,
                "Axial washer slide only after nut removal; no handling or tool envelope.",
            )
            nut_sweep = make_query(
                axis_id + "/nut/straight_slide", axis_id, host_id, "nut", "straight_installation_and_withdrawal",
                nut_seat, v_to_nut, 2 * nut_h, nut["circumscribed_radius_mm"],
                "Axial nut envelope only; thread rotation and wrench access are unmodeled.",
            )
            land_minus = annular_land(source, g, -1, (od, _id, washer_t))
            land_plus = annular_land(source, g, 1, (od, _id, washer_t))
            require(land_minus["status"] == land_plus["status"] == "SUPPORTED_ANALYTICALLY", f"{axis_id}: washer land unsupported")
            supports.extend([
                {"axis_id": axis_id, "end": "negative_v_head", **land_minus},
                {"axis_id": axis_id, "end": "positive_v_nut", **land_plus},
            ])
            stacks.append({
                "axis_id": axis_id,
                "host_obstacle_id": host_id,
                "local_center_grain_u_mm": [g, u],
                "nut_direction_choice": "positive local v from frozen source basis row 2",
                "nut_direction_global_xyz": v_to_nut,
                "head_side": "negative local v",
                "nut_side": "positive local v",
                "proposed_bore": bore,
                "underhead_xyz_mm": underhead,
                "head_wood_face_xyz_mm": head_face,
                "nut_wood_face_xyz_mm": nut_face,
                "nominal_tip_xyz_mm": add_scaled(underhead, v_to_nut, STOCK_MM),
                "nominal_tip_projection_past_nut_mm": nominal_tip_len,
                "203.2_mm_bound_projection_past_nut_mm": bound_tip_len,
                "queries": [q["id"] for q in (shaft, shaft_bound, head_query, head_washer, nut_washer, nut_query, tip, bound_tip, shaft_sweep, bound_sweep, head_sweep, head_washer_sweep, nut_washer_sweep, nut_sweep)],
            })
            queries.extend((shaft, shaft_bound, head_query, head_washer, nut_washer, nut_query, tip, bound_tip, shaft_sweep, bound_sweep, head_sweep, head_washer_sweep, nut_washer_sweep, nut_sweep))
    require(len(stacks) == 4 and len(supports) == 8, "four-axis fit census differs")
    return stacks, supports, queries


def host_bore_certificate(query, obstacle, stacks_by_axis):
    stack = stacks_by_axis[query["axis_id"]]
    if not query["analytic_host_bore_exemption"] or obstacle["id"] != query["host_obstacle_id"]:
        return None
    q = query["cylinder"]
    axis = unit(q["direction_xyz"], query["id"])
    bore = stack["proposed_bore"]
    bore_axis = unit(bore["axis_direction_to_nut_xyz"], query["id"] + " bore")
    dot = sum(axis[i] * bore_axis[i] for i in range(3))
    diff = [q["start_xyz_mm"][i] - bore["center_xyz_mm"][i] for i in range(3)]
    along = sum(diff[i] * bore_axis[i] for i in range(3))
    line_distance = math.sqrt(sum((diff[i] - along * bore_axis[i]) ** 2 for i in range(3)))
    radial_margin = BORE_DIAMETER_MM / 2 - q["radius_mm"]
    require(abs(abs(dot) - 1.0) < 1e-8 and line_distance < 1e-7 and radial_margin > 0.0, f"invalid host bore exemption: {query['id']}")
    return {
        "status": "clear_by_analytic_proposed_bore",
        "method": "coaxial finite cylinder entirely within the named proposed host bore",
        "host_obstacle_id": obstacle["id"],
        "proposed_bore_diameter_mm": BORE_DIAMETER_MM,
        "query_diameter_mm": 2 * q["radius_mm"],
        "radial_clearance_mm": radial_margin,
        "centerline_offset_mm": line_distance,
    }


def make_pairs(queries, obstacles, stacks):
    stack_index = {row["axis_id"]: row for row in stacks}
    spec = importlib.util.spec_from_file_location("frozen_top_washer_fit", HERE / "top_washer_fit.py")
    require(spec is not None and spec.loader is not None, "saved-scene pair helper unavailable")
    top = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(top)
    helper_spec = importlib.util.spec_from_file_location("knee_bridge_saved_scene_bounds", top.HELPER)
    require(helper_spec is not None and helper_spec.loader is not None, "saved-scene bounds helper unavailable")
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    pairs = []
    for query in queries:
        for obstacle in obstacles:
            pair = {"query_id": query["id"], "obstacle_id": obstacle["id"]}
            gap = helper._box_gap(query["bounds_xyz_mm"], obstacle["bounds_xyz_mm"])
            bore = host_bore_certificate(query, obstacle, stack_index)
            if bore is not None:
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap, **bore})
                continue
            if gap > 0.0:
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap, "status": "clear_by_conservative_AABB_separation"})
                continue
            certificate = top.cylinder_certificate(query.get("cylinder"), obstacle.get("cylinder")) if "step_path" not in obstacle else None
            if certificate and certificate["separation_lower_bound_mm"] > 0.0:
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap, "status": "clear_by_finite_cylinder_projection", "projection_certificate": certificate})
            elif obstacle.get("step_path"):
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap, "status": "parent_saved_STEP_check_required", "step_path": obstacle["step_path"]})
            else:
                pairs.append({**pair, "AABB_distance_lower_bound_mm": gap, "status": "undecided_specific_pair"})
    return pairs


def build_setup():
    scene, _base_manifest = validate_scene()
    geometry = read(GEOMETRY)
    require(geometry.get("geometry", {}).keys() >= set(BLOCKS), "frozen knee-spine geometry missing")
    hardware = load_hardware()
    stacks, supports, queries = build_queries(geometry, hardware)
    obstacles = copy.deepcopy(scene["obstacles"])
    pairs = make_pairs(queries, obstacles, stacks)
    require(len(obstacles) == 1041 and len(queries) == 56 and len(pairs) == len(obstacles) * len(queries), "fit query census differs")
    hashes = dict(scene["source_sha256"])
    extras = (TOP_SETUP, TOP_RESULT, TOP_MANIFEST, GEOMETRY, REINFORCEMENT, CATALOG, FASTENER_INPUTS)
    for path in extras:
        relative = key(path)
        digest = sha(path)
        require(relative not in hashes or hashes[relative] == digest, f"conflicting source hash: {relative}")
        hashes[relative] = digest
    producer_key = key(__file__)
    hashes[producer_key] = sha(__file__)
    require(sha(GEOMETRY) == EXPECTED[GEOMETRY], "frozen knee-spine section source changed")
    return {
        "schema": "knee_bridge_saved_scene_fit_setup/v1",
        "status": "PREPARED_ONLY",
        "source_sha256": dict(sorted(hashes.items())),
        "saved_scene": {
            "setup_path": key(TOP_SETUP),
            "setup_sha256": sha(TOP_SETUP),
            "accepted_result_path": key(TOP_RESULT),
            "accepted_result_sha256": sha(TOP_RESULT),
            "snapshot_manifest_path": key(TOP_MANIFEST),
            "snapshot_manifest_sha256": sha(TOP_MANIFEST),
            "source_pin_count": len(scene["source_sha256"]),
            "saved_obstacles_before_top_fit_overlay": 1009,
            "obstacles_after_corrected_top_stacks_and_screw_overlay": len(obstacles),
            "current_top_component_count": 40,
            "translated_Hillman_enclosures": 4,
            "unchanged_Hillman_enclosures": 62,
            "obstacle_source": "Frozen accepted top-washer-fit setup; its 1009 saved obstacles plus corrected eight top stacks and four screw translations. No scene reconstruction.",
        },
        "proposal": {
            "adopted": False,
            "new_stacks": 4,
            "current_hardware_axes_unchanged": 104,
            "current_Hillman_screw_axes_unchanged": 66,
            "stock_and_component_envelopes": hardware,
            "geometry_source_path": key(GEOMETRY),
            "geometry_source_sha256": sha(GEOMETRY),
            "center_schedule_local_grain_u_mm": [list(x) for x in CENTERS_GU_MM],
            "nut_direction_choice": "positive local v for both spines; world direction comes from each frozen source basis row 2",
            "thread_fit": "conditional; actual thread transition/full-form interval and delivered part dimensions unverified",
        },
        "stacks": stacks,
        "washer_support": supports,
        "obstacles": obstacles,
        "queries": queries,
        "pairs": pairs,
        "counts": {
            "stacks": len(stacks),
            "queries": len(queries),
            "obstacles": len(obstacles),
            "pairs": len(pairs),
            "analytic_host_bore_pairs": sum(row["status"] == "clear_by_analytic_proposed_bore" for row in pairs),
            "AABB_separated_pairs": sum(row["status"] == "clear_by_conservative_AABB_separation" for row in pairs),
            "finite_cylinder_projection_pairs": sum(row["status"] == "clear_by_finite_cylinder_projection" for row in pairs),
            "saved_STEP_pairs_for_parent": sum(row["status"] == "parent_saved_STEP_check_required" for row in pairs),
            "undecided_specific_pairs": sum(row["status"] == "undecided_specific_pair" for row in pairs),
        },
        "method_limits": [
            "Host-shaft exemption applies only to the named spine and prescribed 7.5 mm bore axis; all other obstacle pairs remain evaluated.",
            "Washer annular land is checked against saved stock edges and original bore cutouts; installed washer envelopes remain in scene-pair checks.",
            "Head and nut are conservative circumscribed cylinders; washers use filled OD cylinders for obstacle fit.",
            "Straight axial component paths only; no tools, rotation, turning, hands, or operational sequence qualification.",
            "Non-STEP AABB/projection overlaps remain named undecided pairs.",
        ],
        "CAD_run_executed": False,
        **FLAGS,
    }


def prepare(output):
    setup = build_setup()
    output = fresh(output)
    local_sources = (GEOMETRY, REINFORCEMENT, CATALOG, FASTENER_INPUTS, Path(__file__).resolve())
    snapshots = output / "input-snapshots"
    snapshots.mkdir()
    entries = {}
    scene_manifest = read(TOP_MANIFEST)
    scene_sources = read(TOP_SETUP)["source_sha256"]
    for relative, digest in scene_sources.items():
        entries[relative] = {
            "sha256": digest,
            "snapshot_kind": "reused_accepted_top_fit_snapshot",
            "path_from_repository_root": (TOP_PREP / scene_manifest[relative]["path"]).relative_to(ROOT).as_posix(),
        }
    for path in local_sources:
        relative = key(path)
        digest = sha(path)
        target = snapshots / digest
        if not target.exists():
            shutil.copyfile(path, target)
        require(sha(target) == digest, f"local source snapshot differs: {relative}")
        entries[relative] = {"sha256": digest, "snapshot_kind": "local_input_snapshot", "path": target.relative_to(output).as_posix()}
    for path in (TOP_SETUP, TOP_RESULT, TOP_MANIFEST):
        relative = key(path)
        entries[relative] = {"sha256": sha(path), "snapshot_kind": "frozen_repository_record", "path_from_repository_root": relative}
    dump(output / "snapshot-manifest.json", {"schema": "knee_bridge_fit_snapshot_manifest/v1", "entries": dict(sorted(entries.items()))})
    setup["snapshot_manifest_sha256"] = sha(output / "snapshot-manifest.json")
    dump(output / "setup.json", setup)
    return output / "setup.json"


def directrun(output, setup):
    setup_path = Path(setup).resolve()
    require(setup_path.name == "setup.json" and setup_path.parent.parent == RAW.resolve(), "setup must be a prepared child of the knee-bridge raw directory")
    data = read(setup_path)
    producer_key = key(__file__)
    require(sha(__file__) == data["source_sha256"][producer_key], "producer changed after preparation")
    manifest_path = setup_path.parent / "snapshot-manifest.json"
    require(sha(manifest_path) == data["snapshot_manifest_sha256"], "preparation snapshot manifest changed")
    manifest = read(manifest_path)["entries"]
    for relative in (key(GEOMETRY), key(REINFORCEMENT), key(CATALOG), key(FASTENER_INPUTS), producer_key):
        row = manifest[relative]
        snapshot = setup_path.parent / row["path"]
        require(sha(snapshot) == row["sha256"] == data["source_sha256"][relative], f"prepared input snapshot changed: {relative}")
    for path in (TOP_SETUP, TOP_RESULT, TOP_MANIFEST):
        relative = key(path)
        require(sha(path) == data["source_sha256"][relative], f"accepted saved-scene source changed: {relative}")
    output = fresh(output)
    shutil.copyfile(__file__, output / "producer.py.snapshot")
    pairs = copy.deepcopy(data["pairs"])
    queries = {row["id"]: row for row in data["queries"]}
    scene_manifest = read(TOP_MANIFEST)
    steps, solids = {}, {}
    for pair in pairs:
        if pair["status"] != "parent_saved_STEP_check_required":
            continue
        import cadquery as cq
        query = queries[pair["query_id"]]
        path = pair["step_path"]
        if path not in steps:
            entry = scene_manifest[path]
            source = (TOP_PREP / entry["path"]).resolve()
            require(source.is_relative_to((TOP_PREP / "input-snapshots").resolve()) and sha(source) == data["source_sha256"][path], f"saved STEP snapshot changed: {path}")
            steps[path] = cq.importers.importStep(str(source)).val()
            require(steps[path].isValid() and len(steps[path].Solids()) == 1, f"saved STEP is not one valid solid: {path}")
        if query["id"] not in solids:
            c = query["cylinder"]
            solids[query["id"]] = cq.Solid.makeCylinder(c["radius_mm"], c["length_mm"], cq.Vector(*c["start_xyz_mm"]), cq.Vector(*c["direction_xyz"]))
        moving, fixed = solids[query["id"]], steps[path]
        volume, distance = float(moving.intersect(fixed).Volume()), float(moving.distance(fixed))
        pair.update({
            "status": "overlapping_enclosure_requires_disposition" if volume > 1e-6 else "clear_by_saved_STEP_intersection",
            "overlap_volume_mm3": volume,
            "minimum_distance_mm": distance,
            "STEP_sha256": data["source_sha256"][path],
        })
    for path in (TOP_SETUP, TOP_RESULT, TOP_MANIFEST):
        require(sha(path) == data["source_sha256"][key(path)], f"saved-scene record changed during run: {path}")
    for path in (GEOMETRY, REINFORCEMENT, CATALOG, FASTENER_INPUTS, Path(__file__).resolve()):
        require(sha(setup_path.parent / manifest[key(path)]["path"]) == data["source_sha256"][key(path)], f"prepared input changed during run: {path}")
    unresolved = [row for row in pairs if row["status"] == "undecided_specific_pair"]
    overlaps = [row for row in pairs if row["status"] == "overlapping_enclosure_requires_disposition"]
    result = {
        "schema": "knee_bridge_saved_scene_fit_result/v1",
        "status": "STOP_ENCLOSURE_OVERLAP" if overlaps else "BOUNDED_FIT_UNDECIDED" if unresolved else "BOUNDED_NOMINAL_SCENE_FIT_CLEAR",
        "setup_sha256": sha(setup_path),
        "source_sha256": data["source_sha256"],
        "pairs": pairs,
        "counts": {**data["counts"], "STEP_obstacles_loaded": len(steps), "overlap_pairs": len(overlaps), "undecided_pairs": len(unresolved)},
        "overlap_pairs": overlaps,
        "undecided_pairs": unresolved,
        "CAD_run_executed": True,
        **FLAGS,
    }
    result["CAD_run_executed"] = True
    dump(output / "result.json", result)
    dump(output / "receipt.json", {"producer_sha256": sha(__file__), "result_sha256": sha(output / "result.json"), "setup_sha256": result["setup_sha256"]})
    return output / "result.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--setup", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(prepare(args.output_dir))
    else:
        require(args.setup is not None, "--setup is required with --run")
        print(directrun(args.output_dir, args.setup))
