"""Current saved nominal stacks and axial directions; no CAD or solve imports."""

from __future__ import annotations

import argparse
import ast
import csv
import gzip
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OWN = Path(__file__).resolve()
ROLES = ("shaft", "head", "head_washer", "nut_washer", "nut")
ACTUAL_STACK = (
    "Actual_bolt_identity_and_lot", "Actual_nut_identity_and_lot", "Actual_washer_identity_and_material",
    "Actual_underhead_length_mm", "Actual_receiver_plus_plate_mm",
    "Actual_head_washer_thickness_mm", "Actual_nut_washer_thickness_mm",
    "Actual_nut_height_mm", "Actual_gaged_grip_mm", "Actual_thread_runout",
    "Actual_nut_seating", "Actual_washer_fillet_seating", "Actual_factory_hole_bolt_fit",
    "Actual_thread_bearing_disposition", "Actual", "Disposition",
)
ACTUAL_ACCESS = (
    "Actual_tool_identity", "Actual_socket_depth_mm", "Actual_tool_swing",
    "Actual_approach_clearance", "Actual_removal_clearance", "Actual", "Disposition",
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "conflicting pin: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def pure_functions(ref, names):
    """Compile only named, authenticated scalar functions, with no module imports."""
    path = ROOT / ref["path"]
    require(sha(path) == ref["sha256"], "method source changed")
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == set(names), "missing pure function")
    namespace = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return namespace


def vector_text(values):
    return ";".join(format(0.0 if v == 0 else v, ".12g") for v in values)


def position(axis, offset):
    return [p + offset * d for p, d in zip(axis["point_xyz_mm"], axis["direction_xyz"], strict=True)]


def csv_bytes(rows):
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: format(v, ".12g") if isinstance(v, float) else v
                         for k, v in row.items()})
    return text.getvalue().encode()


def prepare():
    input_path = HERE / "hardware-inputs.json"
    inputs = json.loads(input_path.read_bytes())
    refs = inputs["sources"]
    direct = {r["path"]: r["sha256"] for r in refs.values()}
    direct[str(OWN.relative_to(ROOT))] = sha(OWN)
    direct[str(input_path.relative_to(ROOT))] = sha(input_path)
    verify(direct)
    data = {key: json.loads((ROOT / ref["path"]).read_bytes())
            for key, ref in refs.items() if ref["path"].endswith(".json")}
    geometry = data["geometry"]
    raised, catalog = data["raised_inventory"], data["catalog_result"]
    windows = data["window_result"]
    expected = inputs["expected"]
    require(geometry["candidate"] == inputs["candidate"]
            and geometry["revision"] == inputs["geometry_revision"], "current geometry identity")
    require(geometry["schema"] == "eoere_bolted_occupied_geometry/v1", "geometry schema")
    require(raised["disposition"] == "PASS_SCOPED_SAVED_METADATA_MASS_BOM_AND_DIMENSION_WINDOWS",
            "raised saved inventory proof absent")
    proof = raised["hardware_reuse_proof"]
    for key in ("all100_length_diameter_hardware_recipes_exact", "all500_role_owner_labels_exact",
                "all500_scene_hardware_templates_exact", "120_prebore_receiver_bounds_full"):
        require(proof[key] is True, "unchanged own recipe proof absent: " + key)
    require(data["catalog_review"]["independent_catalog_hardware_saved_scalar_checks_pass"] is True
            and data["window_review"]["independent_24_shop_window_source_and_arithmetic_checks_pass"] is True,
            "issued dimensional reviews absent")
    # Rebuild the already-issued raised-inventory closure, without reproducing its methods.
    inherited = dict(raised["source_binding"]["direct_source_sha256"])
    merge(inherited, catalog["source_sha256"])
    merge(inherited, geometry["source_sha256"])
    merge(inherited, windows["direct_source_sha256"])
    for row in geometry["finished_solids"] + geometry["finished_panel_solids"]:
        merge(inherited, {row["path"]: row["sha256"]})
        require((ROOT / row["path"]).stat().st_size == row["bytes"], "member byte count")
    require(len(inherited) == expected["raised_inventory_source_union_count"]
            and canonical(inherited) == expected["raised_inventory_source_union_canonical_sha256"],
            "raised inventory closure differs")
    pins = dict(direct)
    merge(pins, inherited)
    verify(pins)
    decoded = gzip.decompress((ROOT / refs["current_scene"]["path"]).read_bytes())
    require(hashlib.sha256(decoded).hexdigest() == expected["current_scene_decoded_sha256"],
            "current scene decoded bytes")
    scene = json.loads(decoded)
    require(scene["candidate"] == geometry["candidate"]
            and scene["revision"] == geometry["revision"]
            and scene["counts"] == geometry["counts"], "current scene join")
    require(all(v is False for v in geometry["release"].values())
            and all(v is False for v in scene["release"].values()), "release changed")
    offset_fn = pure_functions(refs["raised_inventory_method"], {"offsets"})["offsets"]
    thread_fn = pure_functions(refs["thread_method"], {"bolt_thread_fit"})["bolt_thread_fit"]
    window_fn = pure_functions(refs["window_method"], {"number", "require", "bounds_for"})["bounds_for"]
    return inputs, refs, data, pins, scene, offset_fn, thread_fn, window_fn


def tables(inputs, data, scene, offsets, thread_fit, bounds_for):
    g = data["geometry"]
    axes = g["axes"]
    expected = inputs["expected"]
    require(len(axes) == len({a["id"] for a in axes}) == expected["physical_stacks"], "stack census")
    require(Counter(a["source"] for a in axes) == {
        "eoere_far_pair": expected["angle_shafts"],
        "cleat_post_through_bolt": expected["cleat_post_shafts"],
        "original_starting_frame_axis": expected["starting_frame_shafts"],
    }, "stack source census")
    old = {a["id"]: a for a in data["old_geometry"]["axes"]}
    require(set(old) == {a["id"] for a in axes}, "old/current own identities")
    members = {r["id"]: r for r in g["finished_solids"]}
    solid_rows = {r["id"]: r for r in scene["solids"]}
    metal = {r["id"]: r for r in scene["solids"] if r["fabrication"]["kind"] == "bolt"}
    require(len(metal) == expected["modeled_hardware_roles"], "role census")
    holes = {h["id"]: h for fitting in scene["factory_angle_holes"] for h in fitting["holes"]
             if h["installed_bolt_axis_id"] is not None}
    require(len(holes) == expected["factory_hole_installed_references"], "factory hole census")
    require(Counter(h["installed_bolt_axis_id"] for h in holes.values()) ==
            Counter(a["id"] for a in axes for _ in a["attachments"]), "hole/shaft ownership")
    facts = data["catalog"]
    bolt_products = {(round(b["diameter_in"] * 25.4, 6), round(b["nominal_length_in"] * 25.4, 6)): b
                     for b in facts["bolts"]}
    diameters = {round(d["diameter_in"] * 25.4, 6): d for d in facts["diameters"]}
    prior_groups = {a: group for group in data["catalog_result"]["stock_stack_groups"]
                    for a in group["axis_ids"]}
    require(len(prior_groups) == 100 and set(prior_groups) == set(old), "catalog axis join")
    inv_groups = {a: group for group in data["old_inventory"]["shaft_groups"] for a in group["axis_ids"]}
    require(len(inv_groups) == 100 and set(inv_groups) == set(old), "nominal recipe group join")
    moved = set(data["raised_inventory"]["hardware_reuse_proof"]["translated_stack_ids"])
    require(len(moved) == expected["translated_stacks"], "moved stack census")
    stacks, sides, groups, washers = [], [], {}, Counter()
    maximum_error = 0.0
    fitting_ids = set()
    for index, axis in enumerate(axes):
        name, h = axis["id"], axis["hardware_scenario"]
        prior = old[name]
        for key in ("id", "receivers", "source", "diameter_mm", "before_plate_mm", "after_plate_mm",
                    "hardware_scenario", "nominal_under_head_length_mm", "direction_xyz"):
            require(axis[key] == prior[key], "scalar reuse identity: " + name + "/" + key)
        require(abs(axis["grip_mm"] - prior["grip_mm"]) < 1e-8, "changed receiver stack")
        require(all(r in members for r in axis["receivers"]), "unbound receiver")
        require(abs(math.fsum(d * d for d in axis["direction_xyz"]) - 1) < 1e-8, "axis direction")
        require(axis["delivered_part_or_thread_window_verified"] is False
                and axis["nominal_thread_window_qualified"] is False, "part acceptance changed")
        attachments = axis["attachments"]
        fitting_sides = {"head": [], "nut": []}
        own_holes = []
        for a in attachments:
            hole_id = f'{a["angle_id"]}.{a["flange"]}.{a["row"]}.{a["transverse"]}'
            require(holes[hole_id]["installed_bolt_axis_id"] == name
                    and a["installed_bolt_axis_id"] == name, "fitting hole join")
            require(a["angle_id"] in solid_rows, "missing current fitting")
            polarity = math.fsum(x * y for x, y in zip(a["direction"], axis["direction_xyz"], strict=True))
            require(abs(abs(polarity) - 1) < 1e-8, "fitting direction")
            fitting_sides["head" if polarity > 0 else "nut"].append(a["angle_id"])
            own_holes.append(hole_id)
            fitting_ids.add(a["angle_id"])
        require(abs(len(fitting_sides["head"]) * 6.35 - axis["before_plate_mm"]) < 1e-8
                and abs(len(fitting_sides["nut"]) * 6.35 - axis["after_plate_mm"]) < 1e-8,
                "fitting plate side ownership")
        local = offsets(axis)
        for role in ROLES:
            row = metal[name + "_" + role]
            require(row["fabrication"]["connection_name"] == name
                    and row["fabrication"]["hardware_role"] == role, "role owner")
            require(row["transform"][12:15] == axis["point_xyz_mm"]
                    and row["transform"][8:11] == axis["direction_xyz"], "role placement")
            z = scene["mesh_templates"][row["template_id"]]["mesh"]["bounds_xyz_mm"][4:6]
            err = max(abs(a - b) for a, b in zip(z, local[role], strict=True))
            maximum_error = max(maximum_error, err)
            require(err < 1e-8, "role axial offset")
        fit = thread_fit(axis, {(name, role): {"thickness_mm": h["washer_thickness_mm"],
                                               "id_mm": h["washer_id_mm"]}
                                for role in ("head_washer", "nut_washer")})
        require(abs(fit["tip_projection_beyond_nut_mm"] - axis["tip_projection_beyond_nut_mm"]) < 1e-8,
                "current tip metadata")
        source_group = inv_groups[name]
        require(source_group["source"] == axis["source"]
                and source_group["hardware_scenario"] == h
                and abs(source_group["wood_grip_mm"] - axis["grip_mm"]) < 1e-8,
                "prior nominal recipe applicability")
        for key in ("nut_near_face_from_under_head_mm", "minimum_thread_length_to_reach_nut_near_face_mm",
                    "tip_projection_beyond_nut_mm"):
            maximum_error = max(maximum_error, abs(fit[key] - source_group["thread_fit"][key]))
        diameter = diameters[round(axis["diameter_mm"], 6)]
        bolt = bolt_products[(round(axis["diameter_mm"], 6), round(axis["nominal_under_head_length_mm"], 6))]
        stack = axis["grip_mm"] + axis["before_plate_mm"] + axis["after_plate_mm"]
        window = bounds_for(stack, bolt, diameter)
        catalog_group = prior_groups[name]
        require(catalog_group["bolt_sku"] == bolt["sku"], "catalog nominal SKU join")
        err = abs(window["catalog_min_length_max_stack_two_tip_margin_mm"] -
                  catalog_group["shortest_vs_catalog_max_stack_margin_mm"])
        maximum_error = max(maximum_error, err)
        require(err < 1e-8, "catalog receiving window changed")
        row = {
            "axis_id": name, "geometry_axis_pointer": "/axes/" + str(index), "source": axis["source"],
            "receiver_member_ids": ";".join(axis["receivers"]),
            "head_side_fitting_ids": ";".join(fitting_sides["head"]),
            "nut_side_fitting_ids": ";".join(fitting_sides["nut"]),
            "factory_hole_ids": ";".join(own_holes),
            "duty_ids": ";".join(a["duty_id"] for a in attachments),
            "nominal_recipe": "head/head_washer/head_plate/receivers/nut_plate/nut_washer/nut",
            "nominal_diameter_mm": axis["diameter_mm"],
            "nominal_underhead_length_mm": axis["nominal_under_head_length_mm"],
            "receiver_grip_mm": axis["grip_mm"], "head_side_plate_mm": axis["before_plate_mm"],
            "nut_side_plate_mm": axis["after_plate_mm"], "receiver_plus_plate_mm": stack,
            "model_washer_OD_mm": h["washer_od_mm"], "model_washer_ID_mm": h["washer_id_mm"],
            "model_each_washer_thickness_mm": h["washer_thickness_mm"],
            "model_head_height_mm": h["head_height_mm"], "model_nut_height_mm": h["nut_height_mm"],
            "model_hex_across_flats_mm": h["hex_across_flats_mm"], "UNC_threads_per_inch": h["threads_per_inch"],
            "model_nut_near_underhead_mm": fit["nut_near_face_from_under_head_mm"],
            "model_tip_projection_mm": fit["tip_projection_beyond_nut_mm"],
            "model_two_tip_pitch_margin_mm": fit["tip_projection_beyond_nut_mm"] - window["two_tip_pitches_mm"],
            "model_body_to_farthest_bearing_target_mm": h["washer_thickness_mm"] + stack,
            "comparison_bolt_SKU": bolt["sku"], "comparison_nut_SKU": diameter["nut"]["sku"],
            "comparison_washer_SKU": diameter["washer"]["sku"],
            "catalog_underhead_min_mm": window["underhead_length_bounds_mm"][0],
            "catalog_Lg_max_mm": window["ASME_Lg_max_mm"], "catalog_Lb_min_mm": window["ASME_Lb_min_mm"],
            "catalog_min_full_thread_length_mm": bolt["minimum_full_thread_length_in"] * 25.4,
            "catalog_each_washer_min_mm": window["washer_each_bounds_mm"][0],
            "catalog_each_washer_max_mm": window["washer_each_bounds_mm"][1],
            "catalog_nut_height_min_mm": window["nut_height_bounds_mm"][0],
            "catalog_nut_height_max_mm": window["nut_height_bounds_mm"][1],
            "catalog_min_length_max_stack_two_pitch_margin_mm": window["catalog_min_length_max_stack_two_tip_margin_mm"],
            "catalog_equal_washer_ceiling_mm": window["equal_washer_ceiling_at_shortest_length_and_max_nut_mm"],
            "catalog_nut_near_minus_Lg_min_mm": window["nut_near_minus_Lg_max_bounds_mm"][0],
            "catalog_nut_near_minus_Lg_max_mm": window["nut_near_minus_Lg_max_bounds_mm"][1],
            "catalog_box_disposition": "SHORT_STACK_COMPARISON" if window["catalog_min_length_max_stack_two_tip_margin_mm"] < 0 else "NONNEGATIVE_COMPARISON",
            "part_receiving_disposition": "UNVERIFIED", "geometry_access_disposition": "NOMINAL_ONLY",
            "current_station_translated": name in moved,
            **dict.fromkeys(ACTUAL_STACK, ""),
        }
        stacks.append(row)
        key = (axis["source"], round(axis["diameter_mm"], 6), round(stack, 6), bolt["sku"])
        if key not in groups:
            groups[key] = {"source": axis["source"], "nominal_diameter_mm": axis["diameter_mm"],
                           "nominal_length_mm": axis["nominal_under_head_length_mm"],
                           "nominal_length_in": bolt["nominal_length_in"], "receiver_plus_plate_mm": round(stack, 6),
                           "axis_ids": [], "quantity": 0, "bolt_comparison": bolt,
                           "model_hardware_scenario": h, "catalog_window": bounds_for(round(stack, 6), bolt, diameter)}
        groups[key]["axis_ids"].append(name)
        groups[key]["quantity"] += 1
        washers[(h["washer_od_mm"], h["washer_id_mm"], h["washer_thickness_mm"])] += 2
        for side in ("head", "nut"):
            outward = [(-1 if side == "head" else 1) * d for d in axis["direction_xyz"]]
            bearing_offset = local[side][1 if side == "head" else 0]
            outboard_offset = local[side][0 if side == "head" else 1]
            sides.append({
                "axis_id": name, "side": side, "scene_role_id": name + "_" + side,
                "scene_template_id": metal[name + "_" + side]["template_id"],
                "model_installed_axis_side": "NEGATIVE" if side == "head" else "POSITIVE",
                "receiver_member_ids": row["receiver_member_ids"],
                "side_fitting_ids": ";".join(fitting_sides[side]),
                "axis_origin_xyz_mm": vector_text(axis["point_xyz_mm"]),
                "axis_positive_xyz": vector_text(axis["direction_xyz"]),
                "nominal_bearing_face_xyz_mm": vector_text(position(axis, bearing_offset)),
                "nominal_outboard_face_xyz_mm": vector_text(position(axis, outboard_offset)),
                "nominal_inward_approach_xyz": vector_text([-d for d in outward]),
                "nominal_outward_removal_xyz": vector_text(outward),
                "nominal_tip_xyz_mm": vector_text(position(axis, local["shaft"][1])),
                "model_tip_beyond_nut_mm": fit["tip_projection_beyond_nut_mm"] if side == "nut" else "",
                "reference_catalog_wrench_in": "9/16" if axis["diameter_mm"] == 9.525 else "3/4",
                "current_station_translated": name in moved,
                "position_and_direction_disposition": "NOMINAL_ONLY",
                "current_tool_access_disposition": "UNVERIFIED",
                "current_axial_removal_disposition": "UNVERIFIED",
                "prior_140_side_access_pass_transferred": False,
                **dict.fromkeys(ACTUAL_ACCESS, ""),
            })
    require(len(fitting_ids) == 22, "fitting coverage")
    require(len(sides) == len({(r["axis_id"], r["side"]) for r in sides}) == expected["head_nut_sides"],
            "current side coverage")
    require(sum(r["catalog_box_disposition"] == "SHORT_STACK_COMPARISON" for r in stacks) ==
            expected["catalog_box_shortfall_stacks"], "catalog shortfall census")
    require(all(r[k] == "" for r in stacks for k in ACTUAL_STACK)
            and all(r[k] == "" for r in sides for k in ACTUAL_ACCESS), "actual cells filled")
    require(maximum_error < 1e-8, "scalar reuse error")
    return stacks, sides, [groups[k] for k in sorted(groups)], washers, maximum_error, members, fitting_ids


def document(groups):
    lines = [
        "# Raised-rail nominal hardware and access", "",
        ("This is the hardware and receiving companion for the Eoere raised-rail conditional numerical MVP. "
        "The current saved model has 100 physical bolts, 100 heads, 100 nuts and 200 washers: 84 angle shafts, "
        "four cleat/post shafts and twelve starting frame bolts. Twenty-two installed angles use 88 factory holes; "
        "four shafts pass through two angles. The purchase scenario is six four-packs for 24 angles, including two spares."), "",
        ("[Bolt stacks](bolt-stacks.csv) covers every physical stack, its current receiver and fitting identities, "
        "model recipe, nominal length and dimensional receiving comparisons. [Access sides](access-sides.csv) "
        "covers all 200 head/nut sides. [Inputs](hardware-inputs.json) and [result](hardware-result.json) bind the "
        "saved sources. Actual and Disposition cells are blank; no delivered part or tool has been observed."), "",
        "## Nominal length allocation", "",
        ("The listed Bolt Depot SKUs and matching Grade5 nuts/USS washers are the frozen comparison basket. "
        "They do not replace the saved model's washer, nut or hex envelopes or establish a delivered hardware selection."), "",
        ("The Eoere four-pack reference is [B0C7V7VS89](https://www.amazon.com/dp/B0C7V7VS89). "
        "Its drawing-inch and description-metric dimensions remain separate nominal scenarios: 88.9 mm arms/breadth "
        "with 6.35 mm thickness, and 90 mm arms/breadth with 6 mm thickness. Delivered dimensions, factory-hole "
        "datums/tolerances, formed heel and material remain unverified. Reconcile the listed 10 mm hole with literal "
        "3/8 in (9.525 mm); the latter has zero nominal diametral clearance to a 3/8 in bolt. Keep all eight product "
        "holes, including the unused pairs. The saved current fitting placement does not qualify a delivered part."), "",
        "| Source | Diameter | Nominal length | Quantity | Receiver + plate S | Bolt comparison SKU | Shortest L / maximum catalog stack margin for two tip pitches |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for group in groups:
        diameter = "3/8 in" if group["nominal_diameter_mm"] == 9.525 else "1/2 in"
        label = {"eoere_far_pair": "Angle", "cleat_post_through_bolt": "Cleat/post",
                 "original_starting_frame_axis": "Starting frame"}[group["source"]]
        margin = group["catalog_window"]["catalog_min_length_max_stack_two_tip_margin_mm"]
        lines.append(f'| {label} | {diameter} | {group["nominal_length_in"]:g} in | {group["quantity"]} '
                     f'| {group["receiver_plus_plate_mm"]:g} mm | {group["bolt_comparison"]["sku"]} | {margin:.6f} mm |')
    lines += [
        "", ("Twenty-four stacks have a negative worst-case catalog-box comparison: sixteen 3/8 × 4.5 in "
        "angle stacks at S = 95.25 mm (−0.508 mm), four 3/8 × 6 in angle stacks at S = 133.35 mm "
        "(−0.508 mm), and four 1/2 × 8 in starting stacks at S = 177.8 mm (−1.164492 mm). "
        "These flags compare the shortest listed bolt against the maximum matching catalog washer/nut stack; "
        "they do not prove that every delivered bolt fails. Nonnegative comparisons do not establish delivered fit. "
        "The modeled nut and washer comparison for the four 8 in bolts is a different basis and remains separate."), "",
        ("Model washer allocation is 176 at OD/ID/thickness 26.162/11.1125/2.6416 mm, sixteen at "
        "25.4/11.1125/2.032 mm, and eight at 34.925/14.2875/3.175 mm. Keep one own washer at each end. "
        "The model uses 14.2875 mm hex flats for 3/8 in hardware and 22.225 mm for 1/2 in hardware; "
        "the catalog reference wrench sizes are 9/16 and 3/4 in. Catalog flats do not silently alter those model envelopes."), "",
        "## Receiving and assignment", "",
        ("Retain the existing nominal lengths as the proposal. For each identified stack, record delivered underhead "
        "length L, seated receiver-plus-plate thickness S, head and nut washer thicknesses w_head/w_nut, nut height h_nut, "
        "matching UNC pitch p, and the actual gaged grip/thread/runout. The recorded project target is:"), "",
        "`L >= S + w_head + w_nut + h_nut + 2*p`", "",
        ("The matching nut must run freely to the required washer seat, with full nut seating and the actual threaded "
        "end through the nut. The two tip pitches come from this project's frozen geometry scenario. "
        "The conservative gaged-grip comparison is `G_actual <= S + w_head + w_nut`; catalog Lg is grip-gaging "
        "length, not an observed thread start. Lb and the saved body-to-farthest-bearing target identify separate "
        "body/thread-bearing questions; nominal length does not establish delivered shank or resistance."), "",
        ("Apply the cited ASME dimensions only to the applicable full-body hex-cap-screw definition. A generic "
        "hex-bolt listing is insufficient for that dimensional guarantee; the standard's dimensions are uncoated, "
        "and finished zinc dimensions need the applicable declared agreement. Record matching UNC nut identity, "
        "bolt/nut standards and lot information in the receiving record. Keep washer OD seating, ID/fillet/chamfer "
        "fit, thickness and material evidence separate. The 1/2 in catalog washer minimum opening is 0.547 in "
        "against a 0.550 in maximum bolt fillet, a 0.0762 mm diametral corner requiring actual seating information."), "",
        ("Allocate the 24 flagged stacks individually using measured dimensions. If the tip inequality or free "
        "nut/washer seating cannot be met, leave that stack unassigned. Longer stock or thinner washers remain "
        "unselected: each change needs its own seat, thread-bearing and applicable strength/geometry disposition, "
        "plus current tip/tool/removal clearance. No extra washer packing, cut bolt or full-thread substitute is specified. "
        "No torque, preload or friction capacity is supplied."), "",
        "## Current access disposition", "",
        ("In the current saved model, the head sits on the negative axis side and the nut on the positive side. "
        "The CSV names each role, bearing/outboard face and nominal inward approach/outward removal vector "
        "in the saved global millimetre coordinates. Head/bolt withdrawal points opposite the positive axis; "
        "nut withdrawal follows it. These are axial directions, not a swept clearance or an assembly sequence."), "",
        ("All 200 positions/directions are **NOMINAL_ONLY** and all current tool and removal checks are "
        "**UNVERIFIED**. Sixteen absolute stack stations moved. None of the historical 140-side access passes "
        "or old tool allowances transfers, including at unchanged stations. Actual socket wall/depth, wrench swing, "
        "hand room and withdrawal paths are not supplied. At a nut, the saved tip protrusion is only the nominal "
        "free depth beyond the nut required inside a closed socket, before an unquantified tool allowance. "
        "Fill the tool and clearance cells only from an observed tool/part disposition; leave incompatible affected "
        "installations unassigned."), "",
        "## Scope and reproduction", "",
        ("This table supplies planning and blank receiving records. It supplies no drilling diameter, machining "
        "tolerance, tightening instruction, complete joint resistance or fabrication/climbing release. The six-case "
        "numerical exceedances, unknown capacities and unverified rear-leg no-slip floor assumption stay in the "
        "[numerical packet](../fixed-floor-numerical-mvp-v1.json). The 66 Hillman panel/kicker screws retain their "
        "separate purchased policy; this table specifies no panel remedy."), "",
        "Run from the repository root:", "",
        "```sh", ".venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/hardware.py --check",
        "```", "",
        ("The helper reads and hashes saved records and uses only named pinned scalar functions. `--write` "
        "reproduces these four generated companions; it performs no CAD query, tool sweep, candidate preparation or solve."), "",
    ]
    return "\n".join(lines).encode()


def build():
    inputs, refs, data, pins, scene, offsets, thread_fit, bounds_for = prepare()
    stacks, sides, groups, washers, error, members, fitting_ids = tables(inputs, data, scene, offsets, thread_fit, bounds_for)
    outputs = {"bolt-stacks.csv": csv_bytes(stacks), "access-sides.csv": csv_bytes(sides),
               "hardware.md": document(groups)}
    verify(pins)
    result = {
        "schema": "eoere_raised_rail_nominal_hardware_shop_result/v1",
        "candidate": inputs["candidate"], "geometry_revision": inputs["geometry_revision"],
        "disposition": "COMPLETE_NOMINAL_TABLES_WITH_UNVERIFIED_RECEIVING_AND_ACCESS",
        "counts": {"physical_stacks": len(stacks), "heads": 100, "nuts": 100, "washers": 200,
                   "modeled_roles": 500, "angle_shafts": 84, "cleat_post_shafts": 4, "starting_frame_shafts": 12,
                   "installed_angles": 22, "purchased_angles": 24, "spares": 2, "four_packs": 6,
                   "installed_factory_holes": 88, "shared_angle_shafts": 4, "head_nut_sides": len(sides),
                   "translated_stacks": 16, "translated_sides": 32, "catalog_short_stack_comparisons": 24,
                   "NOMINAL_ONLY_sides": 200, "UNVERIFIED_tool_sides": 200, "UNVERIFIED_removal_sides": 200,
                   "current_swept_tool_clearance_passes": 0, "prior_140_side_passes_transferred": 0,
                   "observed_stack_or_tool_rows": 0},
        "nominal_stack_groups": groups,
        "modeled_washer_groups": [{"OD_mm": k[0], "ID_mm": k[1], "thickness_mm": k[2], "quantity": q}
                                  for k, q in sorted(washers.items())],
        "catalog_dimension_comparison_basis": data["catalog"]["diameters"],
        "angle_product_receiving_limits": {k: data["product_inputs"][k] for k in (
            "primary_listing_url", "primary_drawing_url", "separate_nominal_dimension_scenarios",
            "bolt_and_factory_hole_nominal_clearance", "precise_remaining_dependencies")},
        "member_source_bindings": [{"id": r["id"], "path": r["path"], "sha256": r["sha256"]}
                                   for r in members.values()],
        "fitting_source_bindings": {"scene": refs["current_scene"], "solid_ids": sorted(fitting_ids),
                                    "factory_holes_key": "/factory_angle_holes"},
        "receiving_requirements": data["window_inputs"]["shop_proposal"],
        "catalog_purchase_requirements": data["catalog"]["purchase_requirements"],
        "actual_and_disposition_cells_blank": True,
        "catalog_short_stack_axis_ids": [r["axis_id"] for r in stacks
                                          if r["catalog_box_disposition"] == "SHORT_STACK_COMPARISON"],
        "maximum_saved_scalar_or_scene_offset_difference_mm": error,
        "source_binding": {"direct_source_sha256": {r["path"]: r["sha256"] for r in refs.values()},
                           "hardware_source_sha256": sha(OWN), "inputs_sha256": sha(HERE / "hardware-inputs.json"),
                           "expanded_source_pin_count": len(pins), "expanded_source_map_canonical_sha256": canonical(pins),
                           "raised_inventory_closure": data["raised_inventory"]["source_binding"],
                           "source_pins_verified_before_after": True,
                           "pure_function_reuse": {"raised_inventory_method": ["offsets"],
                                                   "thread_method": ["bolt_thread_fit"],
                                                   "window_method": ["bounds_for", "number", "require"]}},
        "generated_companion_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in outputs.items()},
        "execution": {"saved_metadata_and_scalar_arithmetic_only": True, "candidate_CAD_or_solve": False,
                      "tool_or_removal_sweep": False, "measured_part_or_tool_intake": False},
        "limits": [inputs["reuse_scope"], inputs["receiving_basis"], inputs["access_basis"],
                   "Catalog box flags are comparisons, not actual fit failures; nonnegative margins are not delivered acceptance.",
                   "All complete joint resistance, thread-bearing, washer material/seat, access and physical observation gaps remain separate.",
                   "No new panels, screws, substitute connectors, torque, tool dimensions or physical release are specified."],
        "release": inputs["release"],
    }
    outputs["hardware-result.json"] = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return outputs, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Compare saved companions without writing")
    mode.add_argument("--write", action="store_true", help="Write only this helper's four companions")
    args = parser.parse_args()
    outputs, result = build()
    for name, content in outputs.items():
        path = HERE / name
        if args.write:
            path.write_bytes(content)
        else:
            require(path.read_bytes() == content, "saved output differs: " + name)
    print(json.dumps({"disposition": result["disposition"], "counts": result["counts"],
                      "source_pin_count": result["source_binding"]["expanded_source_pin_count"],
                      "result_sha256": sha(HERE / "hardware-result.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
