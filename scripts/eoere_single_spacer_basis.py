"""Freeze catalog and dimensional inputs for the eight simpler cleat stacks."""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from scripts.eoere_paired_frame_basis import ROOT, ref

REVISION = "eoere-single-spacer-cleat-stacks-v9"
PACKET = Path("docs/bolted-frame-development/owner-frame-v9")
FACTS = PACKET / "hardware-facts.json"
PARAMETERS = PACKET / "candidate-parameters.json"
AXES = {"eoere_bolt_067", "eoere_bolt_070", "eoere_bolt_071", "eoere_bolt_074"} | {
    f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)}


def window(axis, length, spacer, minimum_body, maximum_grip, washer=None):
    h = axis["hardware_scenario"]
    washer = h["washer_thickness_mm"] if washer is None else washer
    wood_end = washer + axis["before_plate_mm"] + axis["grip_mm"]
    plate_end = wood_end + axis["after_plate_mm"]
    nut_start = plate_end + washer + spacer
    two_pitches = 2 * 25.4 / h["threads_per_inch"]
    margins = {"wood_body_margin_mm": minimum_body - wood_end,
               "wood_and_steel_body_margin_mm": minimum_body - plate_end,
               "free_nut_seating_margin_mm": nut_start - maximum_grip,
               "two_pitch_margin_mm": length - 3.048 - nut_start - h["nut_height_mm"] - two_pitches}
    return {"underhead_to_last_wood_mm": wood_end, "underhead_to_last_plate_mm": plate_end,
            "underhead_to_nut_seating_mm": nut_start, **margins,
            "all_nominal_reference_margins_positive": all(v > 0 for v in margins.values())}


def prepare():
    assert not (ROOT / PARAMETERS).exists(), "fresh parameter receipt required"
    facts = json.loads((ROOT / FACTS).read_bytes())
    index = json.loads((ROOT / "docs/bolted-frame-development/development-revisions.json").read_bytes())
    assert index["geometry"]["revision"] == "eoere-inward-bolts-and-angles-v8"
    receipt = json.loads((ROOT / index["geometry"]["receipt"]["path"]).read_bytes())
    assert ref(index["geometry"]["receipt"]["path"]) == index["geometry"]["receipt"]
    g = json.loads((ROOT / receipt["checked_geometry"]["path"]).read_bytes())
    assert ref(receipt["checked_geometry"]["path"]) == receipt["checked_geometry"]
    selected = {r["axis_id"]: r for r in g["selected_stack_overrides"]}
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    b, s = facts["bolt"], facts["spacer"]
    length, spacing = b["underhead_length_mm"], s["length_mm"]
    updates, transforms, removed, checks = [], [], [], []
    for before in g["axes"]:
        if before["id"] not in AXES:
            continue
        identity = before["id"]
        assert before["nominal_under_head_length_mm"] == 203.2 and before["nut_side_spacer_mm"] == 38.1
        assert before["before_plate_mm"] == 0 and before["after_plate_mm"] == 6.35
        assert before["head_faces"] == "exterior" and before["nut_faces"] == "interior"
        assert abs(abs(before["direction_xyz"][0])-1) < 1e-10
        nominal = window(before, length, spacing, b["conservative_analysis_minimum_body_mm"], b["conservative_maximum_grip_gaging_mm"])
        thin = window(before, length, spacing, b["conservative_analysis_minimum_body_mm"], b["conservative_maximum_grip_gaging_mm"],
                      facts["washer"]["catalog_minimum_thickness_mm"])
        assert nominal["all_nominal_reference_margins_positive"] and thin["all_nominal_reference_margins_positive"]
        options = [{"product": r["product"], "length_mm": r["underhead_length_mm"],
                    **window(before, r["underhead_length_mm"], 0 if r["product"] == "8093" else 12.7,
                             r["catalog_minimum_body_mm"], r["underhead_length_mm"]-31.75)}
                   for r in facts["rejected_shorter_bolts"]]
        checks.append({"axis_id": identity, "nominal": nominal, "USS_minimum_thickness": thin,
                       "rejected_shorter_options": options,
                       "minimum_actual_clamped_wood_and_plate_mm_for_free_seating": b["conservative_maximum_grip_gaging_mm"]-spacing-2*facts["washer"]["catalog_minimum_thickness_mm"],
                       "maximum_actual_clamped_wood_and_plate_mm_for_two_pitch_projection": length-3.048-spacing-2*facts["washer"]["nominal_thickness_mm"]-facts["retained_nut"]["height_envelope_mm"]-3.175,
                       "delivered_dimensions_observed": False, "complete_joint_qualified": False})
        after = copy.deepcopy(before)
        after.update(nominal_under_head_length_mm=length, nut_side_spacer_mm=spacing,
                     tip_projection_beyond_nut_mm=length-nominal["underhead_to_nut_seating_mm"]-facts["retained_nut"]["height_envelope_mm"],
                     catalog_nominal_thread_window_checked=True, nominal_thread_window_qualified=False,
                     hardware_stack_revision=REVISION)
        after["hardware_scenario"]["available_nominal_lengths_mm"] = [length]
        choice = copy.deepcopy(selected[identity])
        choice.update(selected_product=b["product"], selected_product_url=b["url"],
                      selected_underhead_length_mm=length, model_underhead_length_mm=length,
                      minimum_body_mm=b["conservative_analysis_minimum_body_mm"], minimum_full_body_mm=b["conservative_analysis_minimum_body_mm"],
                      maximum_grip_gaging_mm=b["conservative_maximum_grip_gaging_mm"],
                      receiver_plus_plate_nominal_mm=133.35, nut_side_spacer_mm=spacing, spacer_piece_count=1,
                      spacer_piece_length_mm=spacing, selected_spacer_SKU=s["product"],
                      selected_recipe="head/head_washer/receivers/nut_washer/spacer/nut",
                      minimum_nut_seating_margin_mm=thin["free_nut_seating_margin_mm"],
                      minimum_two_pitch_margin_mm=nominal["two_pitch_margin_mm"],
                      body_to_farthest_wood_plate_end_margin_mm=nominal["wood_and_steel_body_margin_mm"],
                      minimum_body_to_nominated_target_margin_mm=nominal["wood_and_steel_body_margin_mm"],
                      nominated_smooth_body_target_mm=nominal["underhead_to_last_plate_mm"],
                      minimum_length_mm=length-nominal["two_pitch_margin_mm"],
                      selected_tip_delta_mm=length-before["nominal_under_head_length_mm"],
                      minimum_nut_socket_cavity_depth_mm=after["tip_projection_beyond_nut_mm"]+facts["retained_nut"]["height_envelope_mm"],
                      hardware_stack_revision=REVISION, catalog_nominal_thread_window_checked=True,
                      delivered_part_or_thread_window_verified=False, old_thread_window_margins_apply=False,
                      reason="One catalog one-inch spacer and shorter A574 bolt retain full nominal smooth-body wood/steel support; complete strength and delivered fit remain unqualified.",
                      Actual="", Disposition="")
        updates.append({"axis_id": identity, "before_axis": before, "after_axis": after,
                        "before_selection": selected[identity], "after_selection": choice})
        point, direction = before["point_xyz_mm"], before["direction_xyz"]
        for role, scale, station, travel in (
            ("shaft", length/before["nominal_under_head_length_mm"], -before["hardware_scenario"]["washer_thickness_mm"], 0),
            ("spacer", 2., before["grip_mm"]+before["after_plate_mm"]+before["hardware_scenario"]["washer_thickness_mm"], 0),
            ("nut", 1., 0, spacing-before["nut_side_spacer_mm"])):
            anchor = [p+d*station for p, d in zip(point, direction, strict=True)]
            diagonal = [scale, 1., 1.]
            translation = [(1-diagonal[i])*anchor[i]+direction[i]*travel for i in range(3)]
            name = identity+"_"+role
            old = registry[name]
            bounds = old["bounds_xyz_mm"]
            new_bounds = []
            for i in range(3):
                new_bounds.extend(sorted(bounds[2*i+j]*diagonal[i]+translation[i] for j in (0, 1)))
            transforms.append({"name": name, "axis_id": identity, "role": role,
                               "scale_xyz": diagonal, "translation_xyz_mm": translation,
                               "before": old,
                               "predicted_after": {"bounds_xyz_mm": new_bounds, "volume_mm3": old["volume_mm3"]*math.prod(diagonal),
                                                   "center_of_mass_xyz_mm": [v*diagonal[i]+translation[i] for i, v in enumerate(old["center_of_mass_xyz_mm"])]}})
        removed.extend(identity+"_"+role for role in ("spacer_2", "spacer_3"))
    assert len(updates) == 8 and len(transforms) == 24 and len(removed) == 16
    result = {"schema": "eoere_single_spacer_parameters/v1", "revision": REVISION,
              "producer": ref(Path(__file__)), "facts": ref(FACTS), "parent_geometry": index["geometry"],
              "parent_checked_geometry": receipt["checked_geometry"], "parent_clearance": receipt["checked_clearance"],
              "axis_updates": updates, "part_transforms": transforms,
              "removed_parts": [registry[n] for n in sorted(removed)], "stack_checks": checks,
              "all_nominal_catalog_windows_pass": True, "actual_parts_verified": False,
              "mechanical_force_or_strength_results_transferred": False}
    (ROOT / PARAMETERS).write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({"parameters": ref(PARAMETERS), "facts": ref(FACTS), "stacks": 8, "removed_parts": 16}))


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare()
