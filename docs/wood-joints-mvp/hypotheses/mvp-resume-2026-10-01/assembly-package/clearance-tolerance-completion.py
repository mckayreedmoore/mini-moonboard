#!/usr/bin/env python3
"""Prepare N18 with stdlib; the parent evaluates finite saved-BRep queries.

Import is inert. No source producer, compositor, solver or test is imported.
Catalog envelopes apply at the saved nominal timber pose. Missing machining
and loaded relative-motion bounds are never replaced by a global scalar.
"""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import gzip
import hashlib
import importlib.metadata
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/clearance-tolerance-completion"
H = "docs/wood-joints-mvp/hypotheses"
R = f"{H}/mvp-resume-2026-10-01"
A = f"{R}/assembly-package"
U = f"{R}/upper-corner-screw-layout"
SOURCES = {
    "scene": (f"{A}/rawlocal/knee-bridge-fit/prepare-attempt02/setup.json", "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb"),
    "fit": (f"{A}/rawlocal/knee-bridge-fit/run-attempt01/result.json", "5a2a2e3c886353d4a24262748d0169ba33826cdcca76e8fa01c0a1e0d2bfde8b"),
    "fit_receipt": (f"{A}/rawlocal/knee-bridge-fit/run-attempt01/receipt.json", "4c307065da48b557a94840fd86211dd439add4b8e392f7ac6231def4e95daf00"),
    "length": (f"{A}/rawlocal/hardware-length-fit/saved-source-attempt02/result.json", "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5"),
    "engagement": (f"{A}/rawlocal/hardware-engagement/hardware-engagement.json", "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a"),
    "inventory": (f"{A}/rawlocal/ordinary-n-envelope/attempt01/envelope.json", "278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc"),
    "inventory_receipt": (f"{A}/rawlocal/ordinary-n-envelope/attempt01/receipt.json", "8cec13103d82b262cdbd9446aefb2227ecc0270ebb241999366bc1be8f690fc2"),
    "manifest": (f"{U}/rawlocal/knee-bridge-working-package/attempt02/manifest.json", "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0"),
    "order_axes": (f"{A}/rawlocal/working-order/attempt03/working-order-axes.csv", "b5eb648c0e684f110efd6ec39700e1ba954bbea6642cff88dac6b8022b5cde5f"),
    "shop_axes": (f"{U}/rawlocal/shop-axes/axes.csv", "46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca"),
    "shop": ("docs/floor-flush-construction-kerf-right/connection-axes.csv", "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58"),
    "checklist": ("docs/floor-flush-shop-checklist.md", "c88463f7b3d861014e6aecd7af8c087ed8fce155389d08faf67b1e11f0659599"),
    "features": (f"{H}/current-finished-feature-register-2026-10-01/axis-features.json", "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19"),
    "top": (f"{R}/top-corner-correction/proposal.json", "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2"),
    "catalog": (f"{R}/top-corner-hardware/hardware-inputs.json", "a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7"),
    "gravity": (f"{U}/rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json", "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95"),
    "frame": (f"{U}/rawlocal/knee-bridge-frame/attempt02/response/comparison.json", "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729"),
    "response": (f"{U}/rawlocal/knee-bridge-frame/attempt02/response/response.npz", "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90"),
    "model": (f"{U}/operators-attempt02/model-inputs.json", "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc"),
    "authority": ("current-candidate.json", "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4"),
    "reviewed": ("wood-joints-candidate.json", "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d"),
}
FLAGS = dict.fromkeys(("criterion_closed", "complete_joint_acceptance", "proposal_adopted",
                       "physical_release", "fabrication_release", "machining_margin_qualified",
                       "loaded_clearance_qualified", "delivered_hardware_verified",
                       "geometry_changed", "scene_rebuilt", "native_or_frame_run", "tests_run"), False)
# These are query tolerances, not machining allowances. Match the saved fit helper.
BOX_PAD_MM = 1e-6
QUERY_LINEAR_MM = 1e-7
QUERY_VOLUME_MM3 = 1e-6


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(name):
    return json.loads((ROOT / SOURCES[name][0]).read_text())


def rows(name, key):
    with (ROOT / SOURCES[name][0]).open(newline="") as stream:
        records = list(csv.DictReader(stream))
    result = {row[key]: row for row in records}
    if len(result) != len(records):
        raise ValueError(f"Duplicate {key} in {name}")
    return result


def authenticate(pins):
    for relative, digest in pins.items():
        path = (ROOT / relative).resolve()
        # Frozen worksheet receipts also bind existing /tmp reference PDFs.
        # Read them in place; neither copy nor mutate the foreign references.
        if (not Path(relative).is_absolute() and not path.is_relative_to(ROOT)) or not path.is_file() or sha(path) != digest:
            raise ValueError(f"Source pin mismatch: {relative}")


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def fresh(output):
    output = Path(output).resolve()
    if output.parent != RAW.resolve() or output.exists():
        raise ValueError("Require a fresh immediate child of rawlocal/clearance-tolerance-completion")
    return output


def advance(point, direction, distance):
    return [point[i] + direction[i] * distance for i in range(3)]


def cylinder_bounds(geometry):
    p, d = geometry["start_xyz_mm"], geometry["direction_xyz"]
    end = advance(p, d, geometry["length_mm"])
    bounds = []
    for i in range(3):
        radial = geometry["radius_mm"] * math.sqrt(max(0, 1 - d[i] ** 2))
        bounds.extend((min(p[i], end[i]) - radial - BOX_PAD_MM,
                       max(p[i], end[i]) + radial + BOX_PAD_MM))
    return bounds


def geometry_at(face, direction, low, high, radius, inner=0):
    if high <= low or radius <= inner or inner < 0:
        raise ValueError("Invalid finite cylindrical query")
    return {"kind": "cylinder", "start_xyz_mm": advance(face, direction, low),
            "direction_xyz": direction, "length_mm": high - low,
            "radius_mm": radius, "inner_radius_mm": inner}


def bound(geometry):
    if geometry["kind"] == "cylinder":
        return cylinder_bounds(geometry)
    return list(geometry["bounds_xyz_mm"])


def box_gap(first, second):
    gaps = [max(first[2*i] - second[2*i+1], second[2*i] - first[2*i+1], 0)
            for i in range(3)]
    return math.sqrt(sum(g*g for g in gaps))


def component(source, catalog_geometry, missing, intervals):
    nominal = copy.deepcopy(source["geometry"])
    return {"id": source["component_id"], "axis_id": source["axis_id"],
            "role": source["role"], "nominal": nominal, "catalog": catalog_geometry,
            "bounds": {"nominal": bound(nominal), "catalog": bound(catalog_geometry)},
            "intervals": intervals, "missing_catalog_bounds": sorted(set(missing)),
            "source": source["source"], "geometry_limit": source["geometry_limit"]}


def prepare_components(inventory, order, catalog):
    by_axis = {row["axis_id"]: row for row in inventory["axes"]}
    source = {(row["axis_id"], row["role"]): row for row in inventory["components"]}
    tree = ast.parse((HERE / "hardware_engagement.py").read_text())
    stacks = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "STACKS" for target in node.targets)]
    if len(stacks) != 1:
        raise ValueError("Expected the frozen worksheet's one literal STACKS definition")
    result, passages = [], []
    for axis_id, axis in by_axis.items():
        rec = axis["reconstruction"]
        shaft = source[axis_id, "shaft"]["geometry"]
        direction = shaft["direction_xyz"]
        diameter, length = 2 * shaft["radius_mm"], shaft["length_mm"]
        if axis_id in order:
            profile_key = "five16" if abs(diameter-7.9375) < 1e-6 else "qtr_bd"
            profile = rec.get("catalog_stack", stacks[0][profile_key])
            washer, nut = profile["washer"], profile["nut"]
            face = rec.get("source_head_wood_face_xyz_mm", source[axis_id, "head_washer"]["geometry"]["start_xyz_mm"])
            grip = rec["wood_grip_mm"]
            listed = order[axis_id]["listed_product_length_range_mm"]
            length_interval = json.loads(listed) if listed else None
            retained = order[axis_id]["system"] == "retained"
        else:
            # The four unadopted bridge stacks use the already-frozen working envelope.
            face = advance(shaft["start_xyz_mm"], direction, 2.5)
            grip = 139.7
            washer = {"inside_diameter_mm": [8.3058, 8.3058],
                      "outside_diameter_mm": [25.4, 25.4], "thickness_mm": [2.5, 2.5]}
            nut = {"across_flats_mm": [10.8712, 11.1252], "height_mm": [5.3848, 5.7404]}
            length_interval, retained = None, False
        if axis_id in order and "top_rail" in order[axis_id]["family_id"]:
            washer = {"inside_diameter_mm": [8.3058, 8.3058],
                      "outside_diameter_mm": [25.4, 25.4], "thickness_mm": [2.5, 2.5]}
        missing_washer = []
        if washer["outside_diameter_mm"] == [25.4, 25.4]:
            missing_washer = ["Hillman 885522 washer OD/ID/thickness dimensional intervals; saved 25.4/8.3058/2.5 is a planning hypothesis"]
        tmin, tmax = washer["thickness_mm"]
        odmin, odmax = washer["outside_diameter_mm"]
        idmin, idmax = washer["inside_diameter_mm"]
        nmin, nmax = nut["height_mm"]
        afmin, afmax = nut["across_flats_mm"]
        lmin, lmax = length_interval or (length, length)
        missing_length = [] if length_interval else ["Item-specific under-head length interval"]
        missing_diameter = ["Item-specific maximum coated body/thread outside diameter"]
        head_key = "side_bolt_grade8" if abs(diameter-7.9375) < 1e-6 else "rail_bolt_grade5_lawson"
        head = catalog[head_key]["head"] if not retained else None
        common = {"washer_thickness_mm": [tmin, tmax], "washer_OD_mm": [odmin, odmax],
                  "washer_ID_mm": [idmin, idmax], "nut_height_mm": [nmin, nmax],
                  "nut_across_flats_mm": [afmin, afmax], "listed_length_mm": length_interval,
                  "nominal_shank_mm": diameter, "timber_pose": "saved_nominal_only"}
        for role in ("shaft", "head", "head_washer", "nut_washer", "nut"):
            original = source[axis_id, role]
            if role == "shaft":
                geom = geometry_at(face, direction, -tmax, lmax-tmin, diameter/2)
                missing = missing_length + missing_diameter + missing_washer
            elif role == "head" and head:
                headmax = head["height"]["mm"]["maximum"]
                radius = head["across_flats"]["mm"]["maximum"] / math.sqrt(3)
                geom = geometry_at(face, direction, -tmax-headmax, -tmin, radius)
                missing = missing_washer
                common["head_height_mm"] = [head["height"]["mm"]["minimum"], headmax]
                common["head_across_flats_mm"] = [head["across_flats"]["mm"]["minimum"], radius*math.sqrt(3)]
            elif role == "head":
                geom = copy.deepcopy(original["geometry"])
                missing = ["Retained bolt head dimensional/profile bounds and exact bearing-face datum"]
            elif role == "head_washer":
                geom = geometry_at(face, direction, -tmax, 0, odmax/2, idmin/2)
                missing = missing_washer
            elif role == "nut_washer":
                geom = geometry_at(face, direction, grip, grip+tmax, odmax/2, idmin/2)
                missing = missing_washer
            else:
                geom = geometry_at(face, direction, grip+tmin, grip+tmax+nmax, afmax/math.sqrt(3))
                missing = missing_washer
            if retained:
                missing = missing + ["Exact retained bearing-face datum; the frozen reconstruction retains approximately 0.001 mm source-box padding"]
            result.append(component(original, geom, missing, common))
        # A separate tail query identifies tip risks without duplicating the shaft inventory.
        nominal_tip_low = grip + tmax + nmax
        if length-tmax > nominal_tip_low:
            original = {**source[axis_id, "shaft"], "component_id": axis_id+"/tip", "role": "tip",
                        "geometry": geometry_at(face, direction, nominal_tip_low, length-tmax, diameter/2)}
            geom = geometry_at(face, direction, grip+tmin+nmin, lmax-tmin, diameter/2)
            result.append(component(original, geom, missing_length+missing_diameter+missing_washer, common))
        passages.append({"axis_id": axis_id, "kind": "washer/shank", "nominal_shank_mm": diameter,
                         "washer_ID_interval_mm": [idmin, idmax],
                         "radial_clearance_given_nominal_shank_mm": [(idmin-diameter)/2, (idmax-diameter)/2],
                         "catalog_lower_bound_mm": None, "missing_bound": missing_diameter+missing_washer,
                         "tip_projection_given_recorded_intervals_mm": [lmin-grip-2*tmax-nmax, lmax-grip-2*tmin-nmin],
                         "tip_interval_supported": length_interval is not None and not missing_washer,
                         "profile_limits": ["LB and full-form transition are not delivered shank", "Nut chamfers/full-form profile are not bounded by overall nut height"]})
    for screw in inventory["screws"]:
        result.append(component(screw, copy.deepcopy(screw["geometry"]),
                                ["Hillman 42605 purchased head, coated shank/thread, length and tip dimensional intervals"],
                                {"purchased_nominal_length_mm": 63.5, "occupied_diameter_mm": 4.1402,
                                 "owner_pilot_mm": 3.175, "owner_face_countersink_mm": 9.525}))
    return result, passages


def prepare_holes(inventory, features, top, shop, order):
    feature_axes = {}
    for group in ("candidate_bolt_axes", "retained_frame_bolt_axes"):
        feature_axes.update({row["axis_id"]: row for row in features["source_axis_groups"][group]["axes"]})
    corrected = {row["axis_id"]: row for proposal in top["proposals"] for row in proposal["axes"]}
    holes = []
    for axis in inventory["axes"]:
        axis_id = axis["axis_id"]
        diameter = 2 * next(c for c in inventory["components"] if c["axis_id"] == axis_id and c["role"] == "shaft")["geometry"]["radius_mm"]
        for receiver in axis["receivers"]:
            membership = next((r for r in feature_axes.get(axis_id, {}).get("receiver_memberships", [])
                               if r["receiver_member_id"] == receiver), None)
            if axis_id in corrected:
                bore = corrected[axis_id]["proposed_CAD_bore_envelope_mm"]
                basis = "top-corner proposal corrected bore; old patch is provenance only"
            elif axis_id not in order:
                bore, basis = 7.5, "unadopted added v-bore in effective six-bore spine STEP"
            elif membership:
                radii = {r["cylinder_radius_mm"] for r in membership["cylinder_surface_candidates"] if r["association_status"] == "eligible_bore_patch"}
                bore = 2 * next(iter(radii)) if len(radii) == 1 else None
                basis = "saved axis-feature correspondence; changed hosts are rechecked against effective STEP in parent run"
            else:
                bore, basis = None, "no supported bore descriptor"
            record = shop.get(axis_id)
            opening = ([float(record["shop_finished_opening_min_mm"]), float(record["shop_finished_opening_max_mm"])]
                       if record and record["shop_finished_opening_min_mm"] and record["shop_finished_opening_max_mm"] else None)
            holes.append({"axis_id": axis_id, "receiver": receiver, "modeled_bore_mm": bore,
                          "nominal_shank_mm": diameter, "nominal_radial_gap_mm": (bore-diameter)/2 if bore else None,
                          "bore_basis": basis, "shop_finished_opening_interval_mm": opening,
                          "shop_radial_interval_given_nominal_shank_mm": [(v-diameter)/2 for v in opening] if opening else None,
                          "shop_instruction": record["shop_instruction"] if record else None,
                          "saved_membership": membership, "assembled_passage_lower_bound_mm": None,
                          "missing_bound": ["Coated body/thread diameter interval", "Through-depth relative bore registration/angular-error bound"]
                          + ([] if opening else ["Candidate-specific finished shop opening interval; modeled bore is not a drill instruction"]),
                          "front_pair_fixture": {"pitch_mm": [39, 40], "midpoint_offset_max_mm": 0.5,
                                                 "perpendicular_hole_offset_max_mm": 0.5,
                                                 "scope": "recorded front pair only; no through-depth angular or independently misregistered-host guarantee"}
                          if axis_id.startswith("rail_front_bolt") else None})
    return holes


def prepare(output):
    """Stdlib source joins only. Write setup/receipt into a fresh owned child."""
    output = fresh(output)
    pins = dict(SOURCES.values())
    authenticate(pins)
    scene, inventory, manifest = read("scene"), read("inventory"), read("manifest")
    pins.update(scene["source_sha256"])
    pins.update(inventory["source_sha256"])
    for row in read("engagement")["source_pins"]:
        pins[row["path"]] = row["sha256"]
    for descriptor in manifest["geometry"]["effective_members"]:
        step = descriptor["effective_proposal_step"]
        pins[step["path"]] = step["sha256"]
    pins[Path(__file__).resolve().relative_to(ROOT).as_posix()] = sha(__file__)
    authenticate(pins)
    fit_receipt = read("fit_receipt")
    if fit_receipt["setup_sha256"] != SOURCES["scene"][1] or fit_receipt["result_sha256"] != SOURCES["fit"][1]:
        raise ValueError("Knee fit receipt does not bind the consumed setup/result")
    if read("inventory_receipt")["output_sha256"]["envelope.json"] != SOURCES["inventory"][1]:
        raise ValueError("Installed inventory receipt does not bind its output")
    if inventory["counts"]["existing_axes"] != 104 or inventory["counts"]["proposed_internal_axes"] != 4:
        raise ValueError("104 reviewed/current stacks and four proposed stacks must remain distinct")
    if len(manifest["geometry"]["effective_members"]) != 50 or len(inventory["screws"]) != 66:
        raise ValueError("50-body/66-Hillman source census changed")
    order, shop, screw_axes = rows("order_axes", "axis_id"), rows("shop", "name"), rows("shop_axes", "axis_id")
    if len(order) != 104 or len(screw_axes) != 66:
        raise ValueError("Current shop and order joins changed")
    components, passages = prepare_components(inventory, order, read("catalog")["catalog_parts"])
    axes = {row["axis_id"]: row for row in inventory["axes"]}
    axes.update({row["axis_id"]: {"receivers": [screw_axes[row["axis_id"]]["panel_member"], screw_axes[row["axis_id"]]["receiver_member"]]}
                 for row in inventory["screws"]})
    for item in components:
        item["receivers"] = axes[item["axis_id"]]["receivers"]
        item["proposal_only"] = item["axis_id"] not in order and item["role"] != "screw_occupancy"
        if item["role"] == "head" and item["nominal"]["kind"] == "saved_world_aabb":
            saved = next((o for o in scene["obstacles"]
                          if o["id"] == f"retained_frame_bolt_roles/{item['axis_id']}/head"), None)
            if saved and "step_path" in saved:
                item["saved_modeled_head_step"] = saved["step_path"]
    wood = []
    for descriptor in manifest["geometry"]["effective_members"]:
        step = descriptor["effective_proposal_step"]
        wood.append({"id": "wood/"+descriptor["body"], "body": descriptor["body"], "category": "wood",
                     "step_path": step["path"], "step_sha256": step["sha256"],
                     "bounds_xyz_mm": descriptor["source_bounds_xyz_mm"], "descriptor": descriptor,
                     "effective_bounds_authenticated": False})
    services = [copy.deepcopy(row) for row in scene["obstacles"] if row["category"] in ("tnuts", "lights", "modeled_wires")]
    holes = prepare_holes(inventory, read("features"), read("top"), shop, order)
    setup = {"schema": "clearance_tolerance_completion/v1", "status": "PREPARED_NOT_EVALUATED",
             "source_sha256": dict(sorted(pins.items())), "components": components, "wood": wood, "services": services,
             "holes": holes, "washer_and_tip_profiles": passages,
             "screw_shop_rows": [{**screw_axes[k], "shop_drilling": shop[k]} for k in sorted(screw_axes)],
             "reused_receipts": {name: {"path": SOURCES[name][0], "sha256": SOURCES[name][1]}
                                 for name in ("fit", "fit_receipt", "length", "engagement", "inventory_receipt")},
             "finite_query_scope": ["Each installed component/tip/screw against 50 effective bodies and 405 services",
                                    "Every pair of components from distinct stacks/screw axes", "Every distinct body pair for flush/taper/top/profile separation",
                                    "Each effective body against saved services at their nominal poses"],
             "excluded_operations": ["Tools, turning, counterhold, removal and installation sweeps", "Station-N datum convention"],
             "remaining_basis": {"machining": "No universal cut/position/angle tolerance exists; each hole and component identifies its exact missing interval",
                                 "loaded": "Pair-specific common knee/contact poses, body rotations and elastic point displacement at the same state are unqualified",
                                 "seating": "7.321272 mm is a representative rigid-datum outer diagnostic, not attained total elastic movement; never applied as an obstacle expansion"},
             "counts": {"bodies": 50, "existing_stacks": 104, "proposed_stacks": 4, "screws": 66,
                        "components_including_tip_diagnostics": len(components), "services": len(services), "receiver_memberships": len(holes)},
             **FLAGS}
    authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    write(output / "setup.json", setup)
    receipt = {"setup_sha256": sha(output/"setup.json"), "source_sha256": pins, "status": setup["status"], **FLAGS}
    write(output / "receipt.json", receipt)
    return receipt


def iter_queries(setup, profiles=("nominal", "catalog")):
    """Yield finite pair queries without loading CAD or changing source shapes."""
    for profile in profiles:
        if profile not in ("nominal", "catalog"):
            raise ValueError(f"Unknown dimension profile: {profile}")
        for component_row in setup["components"]:
            for obstacle in itertools.chain(setup["wood"], setup["services"]):
                yield {"profile": profile, "first": component_row, "second": obstacle, "scope": "installed"}
        for first, second in itertools.combinations(setup["components"], 2):
            if first["axis_id"] != second["axis_id"]:
                yield {"profile": profile, "first": first, "second": second, "scope": "distinct_installed_axes"}
        if profile == "nominal":
            for first, second in itertools.combinations(setup["wood"], 2):
                yield {"profile": profile, "first": first, "second": second, "scope": "flush_taper_top_profiles"}
            for first in setup["wood"]:
                for second in setup["services"]:
                    yield {"profile": profile, "first": first, "second": second, "scope": "flush_taper_top_services"}


def evaluate_pair(query, saved_brep_query=None):
    """AABB separation or a parent-supplied exact saved-shape query.

    Callback signature: (first, second, profile) -> mapping containing
    distance_mm, intersection_volume_mm3, method and source bindings.
    Positive enclosure intersection is an unresolved profile risk, not an
    observed physical collision. Zero distance is contact, not overlap.
    """
    first, second, profile = query["first"], query["second"], query["profile"]
    first_box = first["bounds"][profile] if "bounds" in first else first["bounds_xyz_mm"]
    second_box = second["bounds"][profile] if "bounds" in second else second["bounds_xyz_mm"]
    result = {"first": first["id"], "second": second["id"], "profile": profile, "scope": query["scope"],
              "physical_collision_claim": False, "loaded_margin_mm": None, "machining_margin_mm": None,
              "loaded_missing_bound": "Same-state relative rigid/elastic displacement at this pair's closest features, including shared knee/contact compatibility",
              "machining_missing_bound": "Relative cut/axis/angle/seat deviations for these named parts; no universal tolerance is recorded",
              "missing_catalog_bounds": sorted(set(first.get("missing_catalog_bounds", []) + second.get("missing_catalog_bounds", [])))}
    effective_bounds = all(item.get("effective_bounds_authenticated", False)
                           for item in (first, second) if item.get("category") == "wood")
    result["effective_body_bounds_authenticated"] = effective_bounds
    result["complete_catalog_dimensional_bound"] = profile == "catalog" and not result["missing_catalog_bounds"]
    own_host = second.get("body") in first.get("receivers", [])
    if own_host and first.get("role") == "screw_occupancy":
        return {**result, "status": "INTENDED_THREADED_RECEIVER_OCCUPANCY", "nominal_separation_mm": None,
                "limit": "4.1402-mm modeled bore is not the 3.175-mm lead pilot; purchased head/tip and receiver penetration remain separate"}
    gap = box_gap(first_box, second_box)
    if gap > 0:
        status = "NOMINAL_SEPARATION" if profile == "nominal" else "CATALOG_ENVELOPE_SEPARATION_AT_SAVED_POSE"
        if not effective_bounds:
            status = "SAVED_ENCLOSURES_SEPARATE_EFFECTIVE_BODY_BOUND_PENDING"
        elif profile == "catalog" and result["missing_catalog_bounds"]:
            status = "PARTIAL_CATALOG_ENCLOSURES_SEPARATE_WITH_NOMINAL_SUBSTITUTIONS"
        return {**result, "status": status,
                "separation_lower_bound_mm": gap, "method": "conservative_AABB"}
    if saved_brep_query is None:
        return {**result, "status": "PARENT_EXACT_QUERY_REQUIRED"}
    exact = saved_brep_query(first, second, profile)
    if exact is None:
        return {**result, "status": "UNSUPPORTED_SPECIFIC_PROFILE_PAIR"}
    volume, distance = float(exact["intersection_volume_mm3"]), float(exact["distance_mm"])
    if not math.isfinite(volume+distance) or min(volume, distance) < 0:
        raise ValueError("Invalid exact-query result")
    status = "EXACT_QUERY_ENCLOSURES_SEPARATE" if distance > QUERY_LINEAR_MM else "NOMINAL_CONTACT"
    if volume > QUERY_VOLUME_MM3:
        status = "ENCLOSURE_OVERLAP_PROFILE_RESOLUTION_REQUIRED"
    if own_host and first.get("role") in ("shaft", "tip") and volume <= QUERY_VOLUME_MM3:
        status = "EFFECTIVE_STEP_RECEIVER_PASSAGE"
    return {**result, "status": status, "exact_query": exact,
            "separation_lower_bound_mm": max(0, distance-QUERY_LINEAR_MM)}


def _saved_brep_callback():
    # Parent calls this only inside its serialized saved-geometry slot.
    import cadquery as cq

    cache = {}

    def shape(item, profile):
        step_path = item.get("step_path", item.get("saved_modeled_head_step"))
        key = (item["id"], "saved" if step_path else profile)
        if key in cache:
            return cache[key]
        if step_path:
            path = ROOT / step_path
            expected = item.get("step_sha256")
            if expected and sha(path) != expected:
                raise ValueError(f"Saved BRep changed: {path}")
            solid = cq.importers.importStep(str(path)).val()
            if not solid.isValid():
                raise ValueError(f"Invalid saved BRep: {path}")
        elif "nominal" in item and item[profile]["kind"] == "cylinder":
            g = item[profile]
            solid = cq.Solid.makeCylinder(g["radius_mm"], g["length_mm"], cq.Vector(*g["start_xyz_mm"]), cq.Vector(*g["direction_xyz"]))
            # These are query enclosures, never replacements for source geometry.
            if g.get("inner_radius_mm", 0) > 0:
                inner = cq.Solid.makeCylinder(g["inner_radius_mm"], g["length_mm"], cq.Vector(*g["start_xyz_mm"]), cq.Vector(*g["direction_xyz"]))
                solid = solid.cut(inner)
        else:
            return None
        cache[key] = solid
        return solid

    def query(first, second, profile):
        left, right = shape(first, profile), shape(second, profile)
        if left is None or right is None:
            return None
        return {"distance_mm": left.distance(right), "intersection_volume_mm3": left.intersect(right).Volume(),
                "method": "saved_STEP_or_declared_finite_hardware_enclosure",
                "first_step": first.get("step_path", first.get("saved_modeled_head_step")),
                "second_step": second.get("step_path", second.get("saved_modeled_head_step")),
                "linear_query_tolerance_mm": QUERY_LINEAR_MM, "volume_query_tolerance_mm3": QUERY_VOLUME_MM3}

    def saved_bounds(item):
        solid = shape(item, "nominal")
        if solid is None:
            raise ValueError(f"No saved BRep for {item['id']}")
        box = solid.BoundingBox()
        return [box.xmin-BOX_PAD_MM, box.xmax+BOX_PAD_MM,
                box.ymin-BOX_PAD_MM, box.ymax+BOX_PAD_MM,
                box.zmin-BOX_PAD_MM, box.zmax+BOX_PAD_MM]

    query.saved_bounds = saved_bounds
    query.runtime = {name: importlib.metadata.version(name) for name in ("cadquery", "cadquery-ocp")}
    return query


def build(output, setup, *, saved_brep_query=None):
    """Parent-only finite evaluation; supply a callback or use run() for BReps.

    Without a callback, overlapping pairs stay individually pending. The
    report cannot label a source census or a pending exact query qualified.
    """
    output = fresh(output)
    setup_path = Path(setup).resolve()
    if setup_path.parent.parent != RAW.resolve() or setup_path.name != "setup.json":
        raise ValueError("Use a prepared setup in the owned raw folder")
    data = json.loads(setup_path.read_text())
    receipt = json.loads((setup_path.parent/"receipt.json").read_text())
    if sha(setup_path) != receipt["setup_sha256"] or data["source_sha256"] != receipt["source_sha256"]:
        raise ValueError("Prepared setup receipt mismatch")
    authenticate(data["source_sha256"])
    effective_bounds = []
    if saved_brep_query is not None:
        if not callable(getattr(saved_brep_query, "saved_bounds", None)):
            raise ValueError("Exact callback must expose saved_bounds(item) for all 50 effective body BReps")
        for item in data["wood"]:
            exact_bounds = saved_brep_query.saved_bounds(item)
            if len(exact_bounds) != 6 or not all(math.isfinite(v) for v in exact_bounds):
                raise ValueError(f"Invalid cached BRep bounds: {item['id']}")
            if any(exact_bounds[2*i] > exact_bounds[2*i+1] for i in range(3)):
                raise ValueError(f"Inverted cached BRep bounds: {item['id']}")
            effective_bounds.append({"body": item["body"], "step_path": item["step_path"],
                                     "step_sha256": item["step_sha256"], "saved_enclosure": item["bounds_xyz_mm"],
                                     "effective_bounds_xyz_mm": exact_bounds})
            item["bounds_xyz_mm"] = exact_bounds
            item["effective_bounds_authenticated"] = True
    output.mkdir(parents=True)
    (output/".gitignore").write_text("*\n")
    counts, witnesses = Counter(), {}
    with gzip.open(output/"pairs.jsonl.gz", "wt", encoding="utf-8") as stream:
        for query in iter_queries(data):
            row = evaluate_pair(query, saved_brep_query)
            key = row["profile"]+"/"+row["status"]
            counts[key] += 1
            stream.write(json.dumps(row, separators=(",", ":"), allow_nan=False)+"\n")
            gap = row.get("separation_lower_bound_mm")
            if gap is not None and gap > 0 and (key not in witnesses or gap < witnesses[key]["separation_lower_bound_mm"]):
                witnesses[key] = row
    authenticate(data["source_sha256"])
    report = {"schema": "clearance_tolerance_completion_result/v1", "status": "FINITE_COMPARISONS_RECORDED_WITH_EXPLICIT_LIMITS",
              "setup_sha256": sha(setup_path), "source_sha256": data["source_sha256"], "counts": dict(counts),
              "minimum_positive_witness_by_status": witnesses, "receiver_passages": data["holes"],
              "washer_and_tip_profiles": data["washer_and_tip_profiles"], "remaining_basis": data["remaining_basis"],
              "saved_BRep_callback_supplied": saved_brep_query is not None,
              "saved_BRep_runtime": getattr(saved_brep_query, "runtime", None),
              "effective_saved_BRep_bounds": effective_bounds,
              "effective_body_bounds_authenticated": len(effective_bounds) == 50,
              "catalog_rule": "Positive separation encloses only declared dimensional intervals at saved nominal poses; missing diameter/length/profile intervals prevent a complete purchased-part claim",
              "exact_flags": "Positive filled-envelope intersection is not physical collision; source solid contact is not interpenetration",
              **FLAGS}
    write(output/"result.json", report)
    result = {"setup_sha256": sha(setup_path), "output_sha256": {name: sha(output/name) for name in ("pairs.jsonl.gz", "result.json")},
              "source_sha256": data["source_sha256"], "source_unchanged_after_run": True, **FLAGS}
    write(output/"receipt.json", result)
    return result


def run(output, setup):
    """Parent-only saved-BRep imports and finite pair queries; no CAD rebuild."""
    return build(output, setup, saved_brep_query=_saved_brep_callback())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "build", "run"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--setup", type=Path)
    args = parser.parse_args()
    if args.mode != "prepare" and args.setup is None:
        parser.error("build/run require --setup")
    result = prepare(args.output) if args.mode == "prepare" else globals()[args.mode](args.output, args.setup)
    print(json.dumps({"status": result.get("status", "FINITE_QUERY_RECEIPT_WRITTEN"), "output": str(args.output)}))


if __name__ == "__main__":
    main()
