"""Compose the raised-screw shop packet and bounded change/fit reviews.

Reuse frozen coordinate/drawing/window helpers. Bounded CAD queries compare
the restored principal and selected hardware additions against two nominal
angles. There is no frame rebuild or native solve. Observation cells stay empty.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
OLD = DOC / "shop-assembly-v1/extended-cleat-followup-v1"
PACKET = OLD / "current-model-followup-v1"
REVISION = "eoere-raised-kicker-screws-v1"
TARGETS = {"round_kicker_left_rim_2", "round_kicker_right_rim_2"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def table(raw):
    return list(csv.DictReader(io.StringIO(raw.decode())))


def csv_bytes(rows):
    require(bool(rows), "nonempty worksheet required")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def segment_box_distance(start, finish, bounds):
    """Exact piecewise-quadratic segment/AABB distance, including endpoints."""
    delta = [b-a for a, b in zip(start, finish, strict=True)]
    breaks = {0., 1.}
    for i, velocity in enumerate(delta):
        if abs(velocity) > 1e-15:
            for edge in bounds[2*i:2*i+2]:
                t = (edge-start[i])/velocity
                if 0 < t < 1:
                    breaks.add(t)
    breaks = sorted(breaks)

    def square(t):
        return math.fsum(max(bounds[2*i]-(start[i]+t*delta[i]),
                             start[i]+t*delta[i]-bounds[2*i+1], 0.)**2 for i in range(3))

    best = min(square(t) for t in breaks)
    for low, high in itertools.pairwise(breaks):
        mid, quadratic, linear = (low+high)/2, 0., 0.
        for i, velocity in enumerate(delta):
            position = start[i]+mid*velocity
            if position < bounds[2*i] or position > bounds[2*i+1]:
                edge = bounds[2*i] if position < bounds[2*i] else bounds[2*i+1]
                quadratic += velocity**2
                linear += velocity*(start[i]-edge)
        if quadratic:
            best = min(best, square(max(low, min(high, -linear/quadratic))))
    return math.sqrt(best)


def known_answers():
    box = [0., 1., 0., 1., 0., 1.]
    for a, b, answer in [([-2, .5, .5], [2, .5, .5], 0),
                         ([-2, 2, .5], [2, 2, .5], 1),
                         ([-2, 2, 2], [2, 2, 2], math.sqrt(2)),
                         ([-2, -2, .5], [-1, -1, .5], math.sqrt(2)),
                         ([2, 2, 2], [2, 2, 2], math.sqrt(3))]:
        require(abs(segment_box_distance(a, b, box)-answer) < 1e-12, "segment/box known answer")
    return 5


def shifted_bounds(bounds, direction, distance):
    return [value+direction[i//2]*distance for i, value in enumerate(bounds)]


def cylinder_bounds(start, finish, radius):
    """Exact enclosing AABB of a circular cylinder with flat axial ends."""
    delta = [b-a for a, b in zip(start, finish, strict=True)]
    length = math.sqrt(math.fsum(v*v for v in delta))
    require(length > 0 and radius > 0, "nondegenerate cylinder required")
    return [value for i in range(3)
            for value in (min(start[i], finish[i])-radius*math.sqrt(max(0., 1-(delta[i]/length)**2)),
                          max(start[i], finish[i])+radius*math.sqrt(max(0., 1-(delta[i]/length)**2)))]


def selected_hardware_bounds(bank, axes, selections):
    """Enclose the selected shafts, shifted nuts and eight added spacers.

    Other metal dimensions retain the nominal viewer scenario. This is an
    obstruction screen, not a finished-product or socket engagement check.
    """
    bank = copy.deepcopy(bank)
    for name, selected in selections.items():
        axis = axes[name]
        direction = axis["direction_xyz"]
        delta = selected["selected_tip_delta_mm"]
        require(delta >= 0, "this packet permits only retained or longer shafts")
        original = bank[name+"_shaft"]["bounds"]
        translated = shifted_bounds(original, direction, delta)
        bank[name+"_shaft"]["bounds"] = [
            (min if i % 2 == 0 else max)(a, b)
            for i, (a, b) in enumerate(zip(original, translated, strict=True))]
        spacer = selected["nut_side_spacer_mm"]
        if spacer:
            bank[name+"_nut"]["bounds"] = shifted_bounds(bank[name+"_nut"]["bounds"], direction, spacer)
            offset = axis["grip_mm"]+axis["after_plate_mm"]+axis["hardware_scenario"]["washer_thickness_mm"]
            start = [p+offset*d for p, d in zip(axis["point_xyz_mm"], direction, strict=True)]
            finish = [p+spacer*d for p, d in zip(start, direction, strict=True)]
            require(name+"_spacer" not in bank, "spacer identity already exists")
            bank[name+"_spacer"] = {"kind": "selected_spacer", "bounds": cylinder_bounds(start, finish, 19.05/2)}
    return bank


def build(inputs_path, expected):
    require(sha(inputs_path) == expected, "frozen input digest differs")
    inputs = json.loads(inputs_path.read_bytes())
    require(inputs["schema"] == "eoere_current_shop_followup_inputs/v1"
            and inputs["revision"] == REVISION and inputs["optional_grid"] is False,
            "current extra-off inputs required")
    pins = {str(inputs_path.resolve().relative_to(ROOT)): expected,
            str(OWN.relative_to(ROOT)): sha(OWN)}

    def pin(path, digest=None):
        path = str(path)
        observed = sha(ROOT / path)
        require(digest is None or observed == digest, "changed source: " + path)
        require(path not in pins or pins[path] == observed, "conflicting source: " + path)
        pins[path] = observed
        return observed

    def merge(bank):
        for path, digest in bank.items():
            pin(path, digest)

    def verify():
        for path, digest in pins.items():
            require(sha(ROOT / path) == digest, "source drift: " + path)

    data = {}
    for key, ref in inputs["sources"].items():
        pin(ref["path"], ref["sha256"])
        if ref["path"].endswith(".json"):
            data[key] = json.loads((ROOT / ref["path"]).read_bytes())
    geometry, channels, extension = (data[k] for k in ("geometry", "channels", "extension"))
    require(geometry["revision"] == REVISION and geometry["axes"] == extension["axes"]
            == channels["axes"], "100 bolt records must remain fixed")
    require(len(geometry["screw_axes"]) == 66 and geometry["unchanged_screw_count"] == 64,
            "66-screw/two-move identity differs")
    merge(geometry["source_sha256"])
    print("Authenticating and replaying the preceding nominal shop packet", flush=True)
    old = module(inputs["sources"]["old_export"]["path"], "preserved_shop_export")
    saved, prior = old.build()
    require(prior == data["old_result"], "preceding shop replay differs")
    for name, raw in saved.items():
        path = OLD / name
        pin(path)
        require((ROOT / path).read_bytes() == raw, "preceding shop bytes differ: " + name)
    profiles = json.loads(saved["current_profiles.json"])
    original_profiles = copy.deepcopy(profiles)
    holes = table(saved["receiver-holes.csv"])
    screws = table((ROOT / geometry["panel_screw_datums"]["path"]).read_bytes())
    pin(geometry["panel_screw_datums"]["path"], geometry["panel_screw_datums"]["sha256"])
    require(len(screws) == 66 and {r["axis_id"] for r in screws} ==
            {r["axis_id"] for r in geometry["screw_axes"]}, "complete current screw datums required")
    axes = {a["id"]: a for a in geometry["axes"]}
    current_screws = {r["axis_id"]: r for r in geometry["screw_axes"]}
    changed = [r for r in channels["changed_finished_solids"]
               if r["kind"] == "timber" and r["variant"] == "base"]
    changed += [r for r in geometry["changed_finished_solids"] if r["kind"] == "panel"]
    require({r["id"] for r in changed} == {"base_principal_center_right", "kicker_left", "kicker_right"},
            "exact three current wood/panel owners required")
    for row in changed:
        pin(row["path"], row["sha256"])
        profiles[row["id"]]["finished"] = row
    members = table(saved["members.csv"])
    for row in members:
        finished = profiles[row["member"]]["finished"]
        row["current_finished_source_path"] = finished["path"]
        row["current_finished_source_sha256"] = finished["sha256"]
    for profile in original_profiles.values():
        pin(profile["finished"]["path"], profile["finished"]["sha256"])
    helper = module(data["old_inputs"]["sources"]["datum_helper"]["path"], "current_saved_datums")
    draw = module(data["old_inputs"]["sources"]["drawing_helper"]["path"], "current_saved_drawing")
    machining = table(saved["panel-machining.csv"])
    for row in machining:
        name = row["identity"]
        if name in TARGETS:
            source = current_screws[name]
            p = profiles[row["panel"]]
            point = source["origin_xyz_mm"]
            row.update(dict(zip(("origin_x_mm", "origin_y_mm", "origin_z_mm"), point, strict=True)))
            local = helper.local(point, p["datum_xyz_mm"], p["basis_grain_u_v_xyz"])
            row.update(dict(zip(("origin_in_panel_l_mm", "origin_in_panel_u_mm", "origin_in_panel_v_mm"), local, strict=True)))
            row["source"] = f"geometry#/screw_axes/{geometry['screw_axes'].index(source)}"
    require(len(machining) == 340, "340 machining envelopes required")
    outputs = {"current_profiles.json": encoded(profiles), "members.csv": csv_bytes(members),
               "panel-machining.csv": csv_bytes(machining)}
    plot_screws = copy.deepcopy(screws)
    for row in plot_screws:
        row["moved_by_rail_revision"] = row["moved_by_rail_revision"] in (True, "True") or row["axis_id"] in TARGETS
    plot_machining = [[r[k] if k in ("identity", "panel", "kind", "source") else float(r[k])
                       for k in r if k not in ("Actual", "Disposition")] for r in machining]
    drawings = old.drawings(draw, profiles, holes, plot_screws, plot_machining,
                            extension, json.loads(saved["rear-recesses.json"]))
    drawings["extended-cleats.svg"] = drawings["extended-cleats.svg"].replace(
        b"HOLD those four stations: nominal bore/screw gap only 0.341 mm.",
        b"Kicker screws now Z212: maximum bore/screw gap 3.944 mm.").replace(
        b"No axis move, hole diameter or woodworking tolerance adopted here.",
        b"Bolt axes stay fixed; hardware lengths use the separate selected plan.").replace(
        b"Use receiver-holes.csv for all local coordinates and directions.",
        b"Use ../receiver-holes.csv for local coordinates and directions.")
    for name in ("panel-layout-1.svg", "panel-layout-2.svg", "extended-cleats.svg"):
        if drawings[name] != saved[name]:
            outputs[name] = drawings[name]

    print("Querying inclusion of the two saved principal solids", flush=True)
    import cadquery as cq

    before = cq.Shape.importBrep(original_profiles["base_principal_center_right"]["finished"]["path"])
    after = cq.Shape.importBrep(profiles["base_principal_center_right"]["finished"]["path"])
    require(before.isValid() and after.isValid(), "invalid saved principal")
    removed, addition = before.cut(after), after.cut(before)
    added_volume = after.Volume()-before.Volume()
    require(abs(removed.Volume()) < 1e-5 and abs(addition.Volume()-added_volume) < .01,
            "principal change must only restore wood")
    require(abs(added_volume-channels["principal_arc_cuts"]["base_restored_volume_mm3"]) < .01,
            "restored volume disagrees with geometry receipt")
    centroid = list(addition.Center().toTuple())
    observations = data["mechanics_observations"]
    density = observations["parameters"]["wood_density_kg_m3"]
    g = observations["parameters"]["gravity_m_s2"]
    require(density == 500. and g == 9.80665, "preceding declared density/gravity scenario differs")
    require(observations["material_scenario"]["timber_stiffness_basis"] == "declared-gross-stock-Timoshenko",
            "preceding beam stiffness basis differs")
    mass_increment = added_volume*density*1e-9
    gravity = mass_increment*g
    before_box, after_box = before.BoundingBox(), after.BoundingBox()
    bounds_error = max(abs(getattr(before_box, axis+end)-getattr(after_box, axis+end))
                       for axis in "xyz" for end in ("min", "max"))
    require(bounds_error < 1e-5, "restoring internal cuts changed the principal envelope")
    signed_trials = []
    for case in data["numerical_summary"]["cases"]:
        ref = case["coarse"]["bindings"]["result"]
        pin(ref["path"], ref["sha256"])
        result = json.loads((ROOT / ref["path"]).read_bytes())
        merge(result["source_sha256"])
        for row in result["component_reductions"]["simultaneous_Hillman_actions_and_generic_references"]:
            if row["axis_id"] in TARGETS:
                fx, fy, fz = row["force_on_receiver_xyz_n"]
                signed_trials.append({"case_id": case["case_id"], "axis_id": row["axis_id"],
                    "preceding_force_on_post_xyz_N": [fx, fy, fz],
                    "fixed_force_20mm_translation_added_moment_xyz_Nmm": [-20*fy, 20*fx, 0.],
                    "new_layout_action": False})
    require(len(signed_trials) == 12, "six old cases/two own screw witnesses required")
    mechanics = {"revision": REVISION, "scope": "Current geometry and fixed-action change diagnostics; no new response or resistance pass.",
        "principal_inclusion_query": {"old_minus_new_volume_mm3": removed.Volume(),
            "added_volume_mm3": added_volume, "added_centroid_xyz_mm": centroid,
            "added_mass_kg_at_500kg_m3": mass_increment, "gravity_m_s2": g, "added_weight_N": gravity,
            "added_gravity_moment_about_world_origin_Nmm": [-gravity*centroid[1], gravity*centroid[0], 0.],
            "CADQuery_version": cq.__version__, "bounds_unchanged_within_1e_minus_5_mm": True,
            "maximum_envelope_coordinate_change_mm": bounds_error},
        "screw_placement": geometry["screw_support"],
        "generic_5mm_prebored_wood_side_member_recommendation_comparisons": {
            "post_top_axis_mm": 26.9, "post_side_axis_mm": 19.05,
            "compression_5D_margin_mm": 1.9, "tension_10D_margin_mm": -23.1,
            "edge_2p5D_margin_mm": 6.55, "outer_pair_spacing_mm": 152.,
            "pure_equal_pair_fixed_couple_force_ratio_new_over_old": 132/152,
            "is_Hillman_resistance_or_adopted_criterion": False,
            "below_quarter_inch_specific_NDS_placement_requirements_not_prescribed": True},
        "preceding_signed_action_trials": signed_trials,
        "source_change_disposition": {"100_bolt_axes_unchanged": True, "66_screw_count_unchanged": True,
            "kicker_interpolation_coupling_and_aperture_maps_need_new_bindings": True,
            "principal_finished_domain_and_mass_need_new_bindings": True,
            "declared_gross_stock_beam_stiffness_operator_changes_from_filled_internal_cuts": False,
            "physical_net_section_stiffness_or_capacity_qualified_by_gross_beam_model": False,
            "selected_hardware_requires_own_shaft_capture_contact_and_gravity_bindings": True,
            "new_six_case_response_generated": False, "historical_pass_transferred": False,
            "complete_joint_resistance": None, "first_order_physical_applicability": None}}
    outputs["mechanical-change-review.json"] = encoded(mechanics)

    windows = module(inputs["sources"]["window_helper"]["path"], "saved_scalar_windows")
    products = {r["sku"]: r for r in data["catalog"]["bolts"]}
    intermediate = {r["old_sku"]: r for r in data["intermediate_inputs"]["products"]}
    header_product = inputs["shared_header_product"]
    diameters = {round(r["diameter_in"]*25.4, 6): r for r in data["catalog"]["diameters"]}
    stacks = table(saved["bolt-stacks.csv"])
    selections, selected_by_axis = [], {}
    for row in stacks:
        name, axis = row["axis_id"], axes[row["axis_id"]]
        product, spacer, reason = products[int(row["comparison_bolt_SKU"])], 0., "Retain nominal recipe; positive catalog length/seating comparison."
        if row["catalog_box_disposition"] == "SHORT_STACK_COMPARISON":
            product = intermediate[int(row["comparison_bolt_SKU"])]
            reason = "Resolve the catalog two-pitch shortfall with the intermediate partially threaded length."
        if float(row["nut_side_plate_mm"]) > 0:
            product, spacer = header_product, 12.7
            reason = "Cover both shared-header steel/wood interfaces with smooth body; one nut-side spacer permits seating."
        if name.startswith("cleat_post_bolt_"):
            product, spacer = products[368], 12.7
            reason = "Cover both corner timbers with smooth body; one nut-side spacer permits seating."
        diameter = diameters[round(axis["diameter_mm"], 6)]
        stack = float(row["receiver_plus_plate_mm"])
        window = windows.bounds_for(stack+spacer, product, diameter)
        require(window["catalog_min_length_max_stack_two_tip_margin_mm"] > 0
                and window["nut_near_minus_Lg_max_bounds_mm"][0] > 0,
                "selected dimensional window fails: " + name)
        own_holes = sorted((r for r in holes if r["axis_id"] == name), key=lambda r: float(r["entry_from_axis_point_mm"]))
        head_offset = window["washer_each_bounds_mm"][1]+axis["before_plate_mm"]
        targets = [head_offset]
        targets += [head_offset+float(r["exit_from_axis_point_mm"]) for r in own_holes[:-1]]
        if axis["after_plate_mm"]:
            targets.append(window["washer_each_bounds_mm"][1]+stack)
        if name.startswith("cleat_post_bolt_"):
            targets.append(window["washer_each_bounds_mm"][1]+stack)
        required_body = max(targets)
        body_margin = window["ASME_Lb_min_mm"]-required_body
        require(body_margin > 0, "minimum smooth body misses nominated interface: " + name)
        selected = {"axis_id": name, "receiver_member_ids": row["receiver_member_ids"],
            "head_side_fitting_ids": row["head_side_fitting_ids"], "nut_side_fitting_ids": row["nut_side_fitting_ids"],
            "model_underhead_length_mm": axis["nominal_under_head_length_mm"],
            "selected_underhead_length_mm": product["nominal_length_in"]*25.4,
            "selected_diameter_mm": axis["diameter_mm"], "selected_product": product["sku"],
            "selected_product_url": product["url"], "nut_side_spacer_mm": spacer,
            "selected_bolt_grade": "SAE J429 Grade 5; zinc; partially threaded full body",
            "threads_per_inch": diameter["threads_per_inch"],
            "selected_nut_SKU": row["comparison_nut_SKU"], "selected_washer_SKU": row["comparison_washer_SKU"],
            "selected_spacer_SKU": data["spacer_result"]["spacer_catalog_candidate"]["sku"] if spacer else "",
            "selected_recipe": "head/head_washer/head_plate/receivers/nut_plate/nut_washer/"+("spacer/" if spacer else "")+"nut",
            "receiver_plus_plate_nominal_mm": stack,
            "minimum_length_mm": window["underhead_length_bounds_mm"][0],
            "maximum_grip_gaging_mm": window["ASME_Lg_max_mm"],
            "minimum_body_mm": window["ASME_Lb_min_mm"],
            "nominated_smooth_body_target_mm": required_body,
            "minimum_body_to_nominated_target_margin_mm": body_margin,
            "body_to_farthest_wood_plate_end_margin_mm": window["ASME_Lb_min_mm"]-(window["washer_each_bounds_mm"][1]+stack),
            "minimum_two_pitch_margin_mm": window["catalog_min_length_max_stack_two_tip_margin_mm"],
            "minimum_nut_seating_margin_mm": window["nut_near_minus_Lg_max_bounds_mm"][0],
            "minimum_nut_socket_cavity_depth_mm": product["nominal_length_in"]*25.4-window["nut_near_underhead_bounds_mm"][0],
            "selected_tip_delta_mm": product["nominal_length_in"]*25.4-axis["nominal_under_head_length_mm"],
            "reason": reason, "hardware_model_updated": False,
            "installed_fit_and_threaded_wood_bearing_strength": "UNVERIFIED",
            **{field: "" for field in (
                "Actual_bolt_identity_and_lot", "Actual_underhead_length_mm", "Actual_minimum_smooth_body_mm",
                "Actual_gaged_grip_mm", "Actual_receiver_plus_plate_mm", "Actual_head_washer_thickness_mm",
                "Actual_nut_washer_thickness_mm", "Actual_nut_height_mm", "Actual_spacer_length_and_fit",
                "Actual_thread_runout_and_full_form_engagement", "Actual_free_nut_seating",
                "Actual_washer_fillet_and_contact_fit", "Actual_factory_hole_bolt_fit")},
            "Actual": "", "Disposition": ""}
        selections.append(selected)
        selected_by_axis[name] = selected
    require(len(selections) == len(selected_by_axis) == 100, "100 own hardware selections required")
    require(sum(r["nut_side_spacer_mm"] > 0 for r in selections) == 8, "eight one-piece spacers required")
    outputs["hardware-selection.csv"] = csv_bytes(selections)

    bounds_method = module(inputs["sources"]["bounds_helper"]["path"], "saved_world_bounds")
    scene_names = ["eoere-bottom-rail-scene.json.gz", "eoere-cleat-trim-scene.json",
                   "eoere-aligned-wire-scene.json.gz", "eoere-adjusted-base-v3-scene.json.gz",
                   "eoere-cleat-extension-scene.json.gz"]
    scenes = []
    for name in scene_names:
        path = "site/"+name
        pin(path)
        scenes.append(bounds_method.asset(path))
    patch = bounds_method.asset("site/eoere-uniform-channels-scene.json.gz")
    pin("site/eoere-uniform-channels-scene.json.gz")
    scenes.append({"replacements": patch["common_replacements"]+patch["base_replacements"]})
    bank = bounds_method.compose_bounds(data["native"], scenes)
    bank.update({r["id"]: {"kind": r["kind"], "bounds": r["bounds_xyz_mm"]}
                 for r in geometry["changed_finished_solids"]})
    require(len(bank) == 1021, "full current extra-off obstruction census required")
    bank = selected_hardware_bounds(bank, axes, selected_by_axis)
    require(len(bank) == 1029, "selected obstruction census must include eight spacers")
    changed_envelopes = []
    for name, selected in selected_by_axis.items():
        axis, h = axes[name], axes[name]["hardware_scenario"]
        direction = axis["direction_xyz"]
        pieces = []
        if selected["selected_tip_delta_mm"]:
            offset = axis["nominal_under_head_length_mm"]-axis["before_plate_mm"]-h["washer_thickness_mm"]
            pieces.append(("shaft_extension", offset, selected["selected_tip_delta_mm"], axis["diameter_mm"]/2))
        if selected["nut_side_spacer_mm"]:
            offset = axis["grip_mm"]+axis["after_plate_mm"]+h["washer_thickness_mm"]
            pieces.extend([("spacer", offset, selected["nut_side_spacer_mm"], 19.05/2),
                           ("translated_nut_outer_cylinder", offset+selected["nut_side_spacer_mm"],
                            h["nut_height_mm"], h["hex_across_flats_mm"]/math.sqrt(3))])
        for role, offset, length, radius in pieces:
            start = [p+offset*d for p, d in zip(axis["point_xyz_mm"], direction, strict=True)]
            finish = [p+length*d for p, d in zip(start, direction, strict=True)]
            box = cylinder_bounds(start, finish, radius)
            excluded = {name+"_"+r for r in ("shaft", "head", "head_washer", "nut_washer", "nut", "spacer")}
            separations = [(max(max(row["bounds"][i]-box[i+1], box[i]-row["bounds"][i+1], 0.)
                                for i in (0, 2, 4)), part) for part, row in bank.items() if part not in excluded]
            candidates = [part for gap, part in separations if gap <= 1e-5]
            changed_envelopes.append({"axis_id": name, "role": role, "start_xyz_mm": start,
                "finish_xyz_mm": finish, "radius_mm": radius, "AABB_candidates": candidates,
                "minimum_non_candidate_separating_axis_gap_mm": min(gap for gap, part in separations if part not in candidates)})
    require(len(changed_envelopes) == 48, "32 extensions, eight spacers and eight translated nuts required")
    from scripts import eoere_bolted_candidate as nominal_angles

    pin("scripts/eoere_bolted_candidate.py")
    poses = {r["id"]: r for r in observations["fitting_poses"]}
    needed = {part for row in changed_envelopes for part in row["AABB_candidates"]}
    require(needed == {"eoere_clip_split_header_center_left", "eoere_clip_split_header_center_right"},
            "new hardware has an unexpected obstruction requiring another disposition")
    angle_template = nominal_angles.template(nominal_angles.Scenario())
    angle_bodies = {}
    for name in needed:
        angle = nominal_angles.pose({**poses[name], "beam": "source-bound-metadata-only",
                                      "post": "source-bound-metadata-only"}, angle_template)
        require(angle.id == name, "nominal angle pose identity differs")
        box = angle.shape.BoundingBox()
        error = max(abs(getattr(box, axis+end)-bank[name]["bounds"][2*i+j])
                    for i, axis in enumerate("xyz") for j, end in enumerate(("min", "max")))
        require(error < 1e-5, "nominal angle does not match current exporter bounds")
        angle_bodies[name] = angle.shape
    coupon = cq.Solid.makeCylinder(1., 2.)
    require(abs(coupon.distance(coupon.translate((3, 0, 0)))-1.) < 1e-8,
            "CAD cylinder distance known answer differs")
    refined_count = 0
    for row in changed_envelopes:
        refined = []
        for part in row["AABB_candidates"]:
            a, z = cq.Vector(*row["start_xyz_mm"]), cq.Vector(*row["finish_xyz_mm"])
            body = cq.Solid.makeCylinder(row["radius_mm"], (z-a).Length, a, z-a)
            interference = body.intersect(angle_bodies[part]).Volume()
            distance = body.distance(angle_bodies[part])
            require(interference < 1e-5 and distance > 1e-5,
                    "selected hardware addition conflicts with nominal angle: "+row["axis_id"])
            refined.append({"part": part, "intersection_mm3": interference, "distance_mm": distance})
            refined_count += 1
        row["refined_nominal_angle_queries"] = refined
        row["disposition"] = "NOMINAL_ADDED_ENVELOPE_CLEAR"
    require(refined_count == 12, "twelve header/angle refined queries required")
    outputs["hardware-envelope-review.json"] = encoded({"revision": REVISION,
        "scope": "Only added shafts/spacers and final translated nuts, against the current nominal extra-off bank; own six hardware roles excluded.",
        "obstruction_count": len(bank), "changed_envelope_count": len(changed_envelopes),
        "refined_query_count": refined_count, "CAD_distance_known_answer": True,
        "rows": changed_envelopes, "all_changed_envelopes_nominally_clear": True,
        "limits": "Ideal sharp angles and nominal metal dimensions; cylinder envelopes include nut corners and fill spacer bores conservatively. No formed heel, delivered-part tolerance, tool engagement, insertion/withdrawal sweep or joint strength qualification.",
        "hardware_model_updated": False, "physical_fit_observed": False})
    known_answers()
    access = table(saved["access-sides.csv"])
    requirements = []
    for row in access:
        name, side = row["axis_id"], row["side"]
        axis, selected = axes[name], selected_by_axis[name]
        outward = list(map(float, row["nominal_outward_removal_xyz"].split(";")))
        start = list(map(float, row["nominal_outboard_face_xyz_mm"].split(";")))
        if side == "nut":
            start = [x+selected["nut_side_spacer_mm"]*d for x, d in zip(start, outward, strict=True)]
        reach = inputs["generic_tools"]["socket_axial_envelope_mm"]
        finish = [x+reach*d for x, d in zip(start, outward, strict=True)]
        radius = float(row["reference_catalog_wrench_in"] == "3/4")
        radius = (19.05 if radius else 14.2875)/math.sqrt(3)+inputs["generic_tools"]["socket_wall_allowance_mm"]
        excluded = {name+"_"+role for role in ("shaft", "head", "head_washer", "nut_washer", "nut", "spacer")}
        nearest = min((segment_box_distance(start, finish, r["bounds"]), part)
                      for part, r in bank.items() if part not in excluded)
        requirements.append({"axis_id": name, "side": side,
            "origin_xyz_mm": ";".join(map(str, start)), "outward_xyz": row["nominal_outward_removal_xyz"],
            "reference_wrench_in": row["reference_catalog_wrench_in"],
            "reference_socket_radius_mm": radius, "reference_axial_length_mm": reach,
            "minimum_axis_segment_to_other_AABB_mm": nearest[0], "nearest_AABB_owner": nearest[1],
            "reference_capsule_separation_lower_bound_mm": nearest[0]-radius,
            "reference_screen": "POSITIVE_CONSERVATIVE_BOUND" if nearest[0] > radius else "NEEDS_FINER_TOOL_GEOMETRY",
            "screen_scope": "Outboard approach capsule only; engagement, handle sweep and continuous removal remain unverified.",
            "headward_full_bolt_withdrawal_length_mm": selected["selected_underhead_length_mm"] if side == "head" else "",
            "nutward_removal_includes_spacer_mm": selected["nut_side_spacer_mm"] if side == "nut" else "",
            "selected_tip_delta_mm": selected["selected_tip_delta_mm"],
            "actual_tool_and_continuous_removal_verified": False, "Actual": "", "Disposition": ""})
    outputs["access-requirements.csv"] = csv_bytes(requirements)

    drill_rows = []
    for name, axis in axes.items():
        wood = axis["grip_mm"]
        usable = wood+inputs["generic_tools"]["guide_depth_mm"]+inputs["generic_tools"]["backer_travel_mm"]
        drill_rows.append({"axis_id": name, "receiver_member_ids": ";".join(axis["receivers"]),
            "modeled_bore_mm": axis["bore_diameter_mm"], "nominal_shaft_mm": axis["diameter_mm"],
            "nominal_wood_path_mm": wood, "proposed_guide_mm": inputs["generic_tools"]["guide_depth_mm"],
            "proposed_backer_travel_mm": inputs["generic_tools"]["backer_travel_mm"],
            "minimum_usable_bit_projection_mm": usable,
            "extra_chip_gap_or_fixture_height_adds_one_for_one_mm": True,
            "same_setup_positive_stop_and_independent_clamping": True,
            "Actual": "", "Disposition": ""})
    outputs["drilling-requirements.csv"] = csv_bytes(drill_rows)
    from mini_moonboard import box_frame

    pin("mini_moonboard/box_frame.py")
    aligned = data["aligned_geometry"]
    proposals = {r["name"]: r for r in aligned["wire_proposals"]}
    channel_rows = []
    for cut in aligned["service_cuts"]:
        source = proposals[cut["service"]]
        profile = profiles[cut["receiver"]]
        world = [list((box_frame.point(*point)+cq.Vector(*source["placement_xyz_mm"])).toTuple())
                 for point in source["route_local_mm"]]
        local = [helper.local(point, profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]) for point in world]
        require(all(abs(point[2]-8.) < 1e-8 for point in source["route_local_mm"]),
                "common base channels must remain at N8")
        channel_rows.append({"receiver": cut["receiver"], "service": cut["service"],
            "control_route_board_X_S_N_mm": json.dumps(source["route_local_mm"], separators=(",", ":")),
            "placement_xyz_mm": ";".join(map(str, source["placement_xyz_mm"])),
            "control_route_world_xyz_mm": json.dumps(world, separators=(",", ":")),
            "control_route_receiver_L_U_V_mm": json.dumps(local, separators=(",", ":")),
            "channel_radius_mm": 6.35, "front_opening_mm": channels["smaller_profile"]["front_width_mm"],
            "rear_depth_N_mm": 14.35,
            "interpretation": "Source rounded control route; clip swept cutter to raw receiver. Vertices are not sharp finished corners or a saw path.",
            "source": inputs["sources"]["aligned_geometry"]["path"]+"#/wire_proposals/"+str(aligned["wire_proposals"].index(source)),
            "Actual": "", "Disposition": ""})
    require(len(channel_rows) == 32, "32 retained base channel/receiver occurrences required")
    require([r["service"] for r in channel_rows if r["receiver"] == "base_principal_center_right"]
            == ["wire_072_F1_G1"], "right principal must retain only its transverse base passage")
    outputs["service-channel-datums.csv"] = csv_bytes(channel_rows)
    svg = draw.SVG(1350, 1100)
    svg.text(25, 35, "Selected partial-thread stack details | axes fixed; viewer hardware retained", 23, "bold")
    svg.text(25, 75, "Maximum catalog washers/nuts and nominal timber/plates/spacers, measured from under the bolt head.", 15)
    palette = {"washer": "#d8e1eb", "plate": "#829bb2", "wood": "#edc89c", "spacer": "#bdd6b3", "nut": "#c1c6cc"}
    examples = [("eoere_bolt_065", "Four shared-header stacks: 3/8-16 x 3-1/2 in, one 1/2-in spacer"),
                ("cleat_post_bolt_left_1", "Four dedicated cleat/post stacks: 3/8-16 x 4-1/2 in, one 1/2-in spacer"),
                ("eoere_bolt_005", "Example single-receiver stack: read its own complete selected row")]
    for index, (name, caption) in enumerate(examples):
        axis, selected = axes[name], selected_by_axis[name]
        washer = diameters[round(axis["diameter_mm"], 6)]["washer"]["thickness_bounds_in"][1]*25.4
        nut = diameters[round(axis["diameter_mm"], 6)]["nut"]["height_bounds_in"][1]*25.4
        pieces = [("washer", washer), ("plate", axis["before_plate_mm"])]
        pieces += [("wood", float(r["exit_from_axis_point_mm"])-float(r["entry_from_axis_point_mm"]))
                   for r in sorted((r for r in holes if r["axis_id"] == name), key=lambda r: float(r["entry_from_axis_point_mm"]))]
        pieces += [("plate", axis["after_plate_mm"]), ("washer", washer),
                   ("spacer", selected["nut_side_spacer_mm"]), ("nut", nut)]
        y, x, scale = 160+285*index, 90., 7.
        svg.text(25, y-25, caption, 19, "bold")
        offset = 0.
        for role, thickness in pieces:
            if thickness:
                svg.rect(x+offset*scale, y, thickness*scale, 50, palette[role])
                label = {"washer": "W", "plate": "P"}.get(role, role)
                svg.text(x+(offset+thickness/2)*scale-len(label)*3.5, y+80, label, 13)
                offset += thickness
        svg.line((x, y+25), (x+selected["selected_underhead_length_mm"]*scale, y+25), "#18242e", 3)
        svg.line((x, y+105), (x+selected["minimum_body_mm"]*scale, y+105), "#25743a", 4)
        svg.text(x, y+140, f"{name}: Lb minimum {selected['minimum_body_mm']:.4f} mm; nominated target {selected['nominated_smooth_body_target_mm']:.4f} mm", 15)
        svg.text(x, y+170, "The green line is the minimum smooth-body comparison; threads/runout beyond it still need their own disposition.", 15)
    svg.text(25, 1000, "W = washer, P = steel flange. Wood bars follow each shaft's own receiver order; schematic scale 7 px/mm.", 16)
    svg.text(25, 1040, "Spacer placement: existing nut washer, then one factory spacer, then nut. Keep one washer at each end.", 17)
    svg.text(25, 1075, "No extra washer packing, bolt trimming, nut torque/preload or finished-part conformance is assumed.", 16)
    outputs["hardware-stacks.svg"] = svg.render().encode()
    svg = draw.SVG(1350, 920)
    svg.text(25, 35, "Current smaller channels and restored right principal | extra grid OFF", 23, "bold")
    svg.text(25, 70, "Channel section in common board X/N; front clipping plane N=0. Dimensions are derived CAD envelopes.", 15)
    opening_radius = math.hypot(8., 6.35)
    section = []
    for i in range(121):
        depth = 14.35*i/120
        half_width = max(math.sqrt(max(0., opening_radius**2-depth**2)),
                         math.sqrt(max(0., 6.35**2-(depth-8.)**2)))
        section.append((half_width, depth))
    section += [(-x, y) for x, y in reversed(section)]
    svg.polygon([(235+x*10, 140+y*10) for x, y in section], "#fff0d9", width=2)
    # Overall front opening includes the two retained front-open lips.
    svg.text(440, 150, "Radius 6.350 mm; center N8.000 mm; rear depth 14.350 mm", 18)
    svg.text(440, 190, "Derived front opening 20.427677 mm (0.804239 in)", 18)
    svg.text(440, 230, "These envelopes do not select a saw blade, router or drill bit.", 15)
    svg.text(440, 270, "Use the preserved passage routes; no eleven repeated F-column arc cuts.", 15)
    svg.text(80, 415, "Reference opening: 20.428 mm", 16)
    for i, text in enumerate([
        "Right principal: retain only its original transverse wire_072_F1_G1 passage and all original bolt bores.",
        "Eleven F-column links run straight beside the principal; their original LED endpoints remain fixed.",
        "Restoring 97,352.067 mm3 changes the finished domain and mass; no old response transfers.",
        "All other base timber passages keep their preceding smaller profiles and source-bound route identities.",
        "Optional-grid lifted cables, extra cuts and provisional midpoint assumptions are outside this shop packet.",
        "Panel screw policy: 1/8-in lead pilot, 3/8-in face countersink, #2 Phillips; CAD screw voids are not bits.",
        "Current outer kicker holes: Z212 mm, 65 mm below the top envelope; use the full screw datum table.",
    ]):
        svg.text(25, 490+47*i, text, 16)
    outputs["current-channels.svg"] = svg.render().encode()
    mass = copy.deepcopy(prior["nominal_mass"])
    mass["finished_timber_volume_mm3"] += added_volume
    mass["finished_timber_kg_at_500kg_m3"] += mass_increment
    mass["conditional_total_kg"] += mass_increment
    mass["limits"] += " Current principal restored; selected hardware increments below are a separate cylinder estimate."
    spacer_volume = math.pi/4*(19.05**2-10.31875**2)*12.7
    hardware_increment = (math.fsum(math.pi/4*r["selected_diameter_mm"]**2*r["selected_tip_delta_mm"]
                                   for r in selections)+8*spacer_volume)*7850e-9
    counts = Counter((r["selected_diameter_mm"], r["selected_underhead_length_mm"]) for r in selections)
    replacement_cost = math.fsum(p["quantity"]*products[p["old_sku"]]["unit_price_usd"] for p in intermediate.values())
    intermediate_cost = math.fsum(math.ceil(p["quantity"]/p["pack_quantity"])*p["observed_pack_price_usd"] for p in intermediate.values())
    spacer_catalog = data["spacer_result"]["spacer_catalog_candidate"]
    spacer_cost = min(8*spacer_catalog["unit_price_usd"], spacer_catalog["ten_pack_price_usd"])
    selected_cost = 109.93-replacement_cost+intermediate_cost+4*(products[368]["unit_price_usd"]-products[367]["unit_price_usd"])+4*(header_product["unit_price_usd"]-products[365]["unit_price_usd"])+spacer_cost
    result = {"schema": "eoere_current_shop_followup/v1", "revision": REVISION,
        "status": "CONDITIONAL_CURRENT_COORDINATE_AND_HARDWARE_PLAN_WITH_OPEN_RESISTANCE_AND_FIT",
        "inputs_sha256": expected, "producer_sha256": sha(OWN),
        "source_pin_count": len(pins), "source_map_canonical_sha256": canonical(pins),
        "preceding_shop_replayed_byte_identical": True, "source_pins_before_after_unchanged": True,
        "counts": {"timbers": 22, "panels": 6, "angles": 22, "bolts": 100, "nuts": 100,
                   "washers": 200, "Hillman_screws": 66, "selected_spacers": 8,
                   "receiver_occurrences": 120, "machining_envelopes": 340, "access_sides": 200,
                   "base_wire_channel_occurrences": len(channel_rows),
                   "changed_bolt_lengths_from_viewer": sum(r["selected_tip_delta_mm"] > 0 for r in selections)},
        "selected_bolt_counts": [{"diameter_mm": d, "length_mm": length, "quantity": count}
                                 for (d, length), count in sorted(counts.items())],
        "minimum_two_pitch_margin_mm": min(r["minimum_two_pitch_margin_mm"] for r in selections),
        "minimum_nut_seating_margin_mm": min(r["minimum_nut_seating_margin_mm"] for r in selections),
        "minimum_body_to_nominated_interface_margin_mm": min(r["minimum_body_to_nominated_target_margin_mm"] for r in selections),
        "reference_tool_screen_counts": dict(Counter(r["reference_screen"] for r in requirements)),
        "reference_tool_obstruction_count": len(bank),
        "added_hardware_nominal_clearance_envelopes": len(changed_envelopes),
        "added_hardware_nominal_angle_refinements": refined_count,
        "reference_tool_obstructions": "Current 1021 nominal parts, 32 shaft extensions, eight nut translations and eight spacers; other hardware dimensions retain the viewer scenario.",
        "tool_screen_known_answers": 5,
        "maximum_nominal_bit_projection_mm": max(r["minimum_usable_bit_projection_mm"] for r in drill_rows),
        "nominal_mass_with_retained_viewer_hardware": mass,
        "selected_hardware_added_mass_cylinder_estimate_kg": hardware_increment,
        "selected_hardware_mass_estimate_limits": "7850kg/m3 steel, solid nominal extra shaft cylinders and eight nominal annular spacers; not measured or fresh model gravity.",
        "dated_hardware_comparison_usd_before_shipping_tax": round(selected_cost, 2),
        "cost_scope": "Prior $109.93 basket less 24 superseded bolts plus $55.94 intermediate packs; +$0.52 corner bolts, +$0.48 header bolts, +$18.04 ten-spacer pack. Angles/wood/services/tools unpriced. Not a live quote.",
        "reused_files": {name: {"path": str(OLD/name), "sha256": hashlib.sha256(raw).hexdigest()}
                         for name, raw in saved.items() if name not in outputs and name != "result.json"
                         and name != "panel-screw-datums.csv"},
        "current_screw_datums": geometry["panel_screw_datums"],
        "release": {"fabrication": False, "climbing": False, "observed_parts": False,
                    "complete_joint_resistance": False, "hardware_model_changed": False,
                    "historical_response_pass_transferred": False},
        "open_inputs": ["Finished-part conformance, actual placement and continuous tool/removal access remain unobserved.",
            "Spacer/washer/contact and threaded wood bearing resistance are unqualified.",
            "Current-response rebinding, eight mixed stacks, complete joints, net sections/restraint and first-order applicability remain open.",
            "Panel/screw strength remedies remain paused; the two authorized clearance moves do not resume them."],
        "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for name, raw in outputs.items()}}
    outputs["result.json"] = encoded(result)
    require(all(value == "" for rows in (machining, selections, requirements, drill_rows)
                for row in rows for key, value in row.items() if key.startswith("Actual") or key == "Disposition"),
            "physical observation was filled")
    verify()
    return outputs, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT/PACKET/"inputs.json")
    parser.add_argument("--inputs-sha256", required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--out", type=Path)
    modes.add_argument("--check", type=Path)
    args = parser.parse_args()
    require(Path.cwd() == ROOT, "run from the repository root")
    if args.out:
        require(args.out.resolve().is_relative_to(ROOT/"fea/generated"), "ignored generated output required")
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out/"producer-snapshot.py").write_bytes(OWN.read_bytes())
        (args.out/"inputs-snapshot.json").write_bytes(args.inputs.read_bytes())
    outputs, result = build(args.inputs, args.inputs_sha256)
    for name, raw in outputs.items():
        if args.out:
            with (args.out/name).open("xb") as stream:
                stream.write(raw)
        else:
            require((args.check/name).read_bytes() == raw, "saved output differs: " + name)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "source_pins": result["source_pin_count"], "generated_bytes": sum(map(len, outputs.values())),
                      "minimum_two_pitch_margin_mm": result["minimum_two_pitch_margin_mm"],
                      "minimum_seating_margin_mm": result["minimum_nut_seating_margin_mm"],
                      "reference_tool_screens": result["reference_tool_screen_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
