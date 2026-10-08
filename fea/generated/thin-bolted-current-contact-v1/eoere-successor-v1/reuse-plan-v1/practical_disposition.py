"""Compact saved-evidence practical disposition; no geometry or field evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
PACKET = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
SOURCES = {
    "geometry": (LEAF+"occupied-geometry-v2-complete/geometry.json", "05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd"),
    "inventory": (LEAF+"reuse-plan-v1/inventory-v2.json", "14d74a158c4af7cf57d0b1282eda41e6f7e849024130be3cf869080a6ee03de3"),
    "inventory_review": (LEAF+"raw-angle-review-v1/independent-inventory-v2-review.json", "03a5adae71469d59fcd7efa4970db380b4b529bf1079f061401a1115f72b6cfd"),
    "lower_revision": (LEAF+"cleat-corners-v1/lower-bolt-z-v2.json", "a615cb247cf48426f139cc3149ff658d38a96861c3166d0fa27e5912d650c04b"),
    "product": (PACKET+"eoere-successor-v1/product-inputs-final.json", "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309"),
    "old_access": (PACKET+"access-takeoff-v4.json", "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c"),
    "old_instructions": (PACKET+"access-takeoff-v4.md", "666c5b0b4ae45940827c82e8bd7de437c991fff729d8e9e56411c64b7c6a5b18"),
    "old_free_fittings": (PACKET+"free-fitting-release-v4.json", "3ba627fb17f960d98a3a5e5da622ce850c738a196b04393ed2884a7f9a5b0790"),
}
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_pins():
    pins = {path: digest for path, digest in SOURCES.values()}
    pins[str(OWN.relative_to(ROOT))] = LOADED_SHA
    require(all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest for path, digest in pins.items()),
            "saved practical evidence bytes changed")
    return pins


def result():
    before = source_pins()
    data = {name: json.loads((ROOT/path).read_bytes()) for name, (path, _) in SOURCES.items() if path.endswith(".json")}
    geometry, inventory, lower = (data[name] for name in ("geometry", "inventory", "lower_revision"))
    require(inventory["geometry_source"]["sha256"] == SOURCES["geometry"][1]
            and data["inventory_review"]["disposition"] == "PASS_SCOPED_NOMINAL_ARITHMETIC_AND_SOURCE_JOINS",
            "reviewed nominal inventory join differs")
    require(geometry["counts"]["physical_bolt_axes"] == inventory["counts"]["physical_shafts"] == 100
            and geometry["changes"]["Hillman_axes_moved"] == [] and geometry["counts"]["bracket"] == 22,
            "final successor count or protected screw geometry differs")
    require(all(not rows for rows in geometry["collisions"].values()), "recorded nominal collision remains")
    groups = []
    for row in inventory["shaft_groups"]:
        thread = row["thread_fit"]
        groups.append({key: row[key] for key in ("source", "quantity", "diameter_mm", "nominal_length_mm", "nominal_length_in",
            "wood_grip_mm", "near_steel_mm", "far_steel_mm", "minimum_underhead_for_modeled_nut_and_two_tip_threads_mm",
            "full_smooth_body_to_farthest_modeled_bearing_end_target_mm", "axis_ids")} |
            {"maximum_smooth_shank_for_nut_to_reach_seat_mm": thread["maximum_smooth_shank_for_nut_to_reach_seat_mm"],
             "nominal_tip_threads": thread["tip_threads"], "Actual": "", "Disposition": ""})
    require(sum(row["quantity"] for row in groups) == 100 and sum(row["quantity"] for row in groups if row["source"] != "original_starting_frame_axis") == 88,
            "unique hardware count differs")
    eight = inventory["thread_and_shank_obligations"]["four_8inch_comparisons"]
    require(len(eight) == 4 and all(abs(row["source_shortest_comparison_underhead_mm"]-
        row["current_modeled_nut_two_tip_minimum_underhead_mm"]-row["shortest_comparison_margin_against_current_modeled_stack_mm"]) < 1e-12 for row in eight),
        "four delivered-length comparisons differ")
    lower_axes = [row for row in geometry["axes"] if row["source"] == "cleat_post_through_bolt"]
    require(len(lower_axes) == 4 and all(row["point_xyz_mm"][2] == lower["common_Z_mm"] == 200. for row in lower_axes),
            "actual frozen lower revision differs")
    output = {
        "schema": "eoere_successor_practical_hardware_and_assembly_disposition/v1",
        "candidate": geometry["candidate"], "geometry_revision": geometry["revision"], "source_sha256": before,
        "scope": "Saved nominal geometry, reviewed inventory and applicable predecessor planning steps only; no forces, live outputs or new paths evaluated.",
        "counts": inventory["counts"], "hardware_groups": groups, "washer_groups": inventory["washer_groups"],
        "reusable_planning_steps": [
            {"step": "Support unloaded members separately; remove holds and disconnect power before panel/frame disassembly.",
             "source": SOURCES["old_instructions"][0]+"#checked-sequence-and-scope", "limit": "Separate member support and unplugging/hands remain planning requirements, not observed access."},
            {"step": "Keep the front screw approach and upper-panel-first order; plan lower panels 0.5 mm upslope before outward removal, then kickers.",
             "reason": "Six panel outlines, kicker seams and all 66 Hillman axes remain unchanged.",
             "limit": "Reuse the local seam/order, not predecessor corridor PASS against newly added cleats and fittings."},
            {"step": "Lift the harness from front-open channels before exposing the structural fasteners.",
             "limit": "Connector release, complete harness shape, slack and bend radius remain unmeasured."},
            {"step": "Retain the owner-selected Hillman lead-hole/countersink/driver policy and the member-local L/U/V datum method.",
             "limit": "Existing owner policy is not a new bit choice or manufacturer qualification; CAD through-bore envelopes are not drill instructions."},
            {"step": "Reuse the pass-through-tool outline and continuous withdrawal/dependency methods when checking the successor.",
             "limit": "Old 140-side tool, 70-stack withdrawal, 36-fitting and 20-member routes do not establish current 200-side/100-stack/22-fitting plus 2-cleat access."}],
        "changed_frame_steps": [
            {"step": "Identify 16 main angles inside four panel boxes plus 6 base/header angles, all 176 factory holes and 88 installed far-pair attachments.",
             "limit": "Absolute heel offsets, bend and delivered hole locations remain model scenarios; avoid obsolete B103/B104 layout and doubled/opposite rails."},
            {"step": "Place two 38.1 x 139.7 x 289.7 mm exterior Z-grain cleats above runners; retain upper inside angles and remove the two lower outside angle duties.",
             "joint_path": "Four upper-angle side shafts cross side+cleat; four separate cleat/post shafts tie the cleats to outer posts; header/post bearing remains.",
             "side_cleat_axes": [row["id"] for row in geometry["axes"] if row["source"] == "eoere_far_pair" and any("cleat" in host for host in row["receivers"])]},
            {"step": "Use all four final cleat/post stations at Z200 mm, keeping the 66 screw axes fixed.",
             "axes": [{"id": row["id"], "point_xyz_mm": row["point_xyz_mm"], "receivers": row["receivers"]} for row in lower_axes],
             "limit": "Do not drill from the preserved Z189.3 failed scenario or move screws implicitly."},
            {"step": "Count 88 fitting attachments minus 4 shared duplicates, plus 4 cleat/post shafts and 12 starting shafts: 100 unique shafts.",
             "shared_angle_axes": [axis for row in groups if row["source"] == "eoere_far_pair" and abs(row["nominal_length_in"]-3.) < 1e-10 for axis in row["axis_ids"]],
             "limit": "Four shared-angle shafts carry eight fitting holes; stage both owners before capture. This is an ownership dependency, not a verified installation/withdrawal order."},
            {"step": "Expose both fastener ends before panels/harness obscure access; plan separately supported removal of shared shafts and both cleats.",
             "limit": "The predecessor B103 beam-first dependency and free-angle release routes are obsolete for this frame. No actual tool fit or current removal DAG has been demonstrated."}],
        "specific_remaining_measurements": {
            "lower_bore_screw_clearance": {**lower["all66_screw_comparisons"]["minimum_by_lower_primitive_role"]["wood_bore_cutter"],
                "source": SOURCES["lower_revision"][0], "actual_clearance_or_tolerance_budget": None,
                "needed": "Delivered bore/screw/head diameters, both axes and installation positioning/drill runout at the lower pair; the current 0.340625 mm value is a nominal bound, not a manufactured clearance."},
            "post_top_end": {**lower["conditional_end_reference"],
                "needed": "Actual post end/grain/holes and signed group action; 38.9 mm exceeds the named 4D compression reference by 0.8 mm, but is below full 7D tension at 66.675 mm. The minimum 3.5D tension reference is 33.3375 mm; complete load-direction/group/splitting behavior remains unresolved."},
            "delivered_hardware": {"requirements": inventory["thread_and_shank_obligations"]["requirements"],
                "needed": "Actual underhead lengths, thread start/root/runout, full nut engagement and tip/tool clearance for every own new grip and bearing/shear interval; actual washers/seats, hole tolerances and head/nut outlines.",
                "limit": "Smooth-body target windows are optional geometric coverage comparisons, not a blanket resistance requirement. A threaded plane needs its own appropriate resistance basis; no preload, torque, friction or actual washer couple is supplied."},
            "four_8inch_comparisons": eight,
            "four_8inch_interpretation": "Nominal 3.848 tip threads do not cover the shortest 198.628 mm comparison. Its modeled-stack shortfall is 0.961292 mm; the separate catalog-nut/frozen-washer shortfall is 0.808892 mm. Delivered fit remains NULL. Saved 8.5-inch alternatives are unselected algebraic/access comparisons and are not inserted into current geometry.",
            "stock_and_panels": "Actual usable runner offcuts and grade/grain; delivered stick lengths at old tight nesting; reconcile cut-panel thickness/width to CAT 18.25625 mm and modeled main width 1217.6125 mm (nominal 1219.2 differs by 1.5875 mm). No new plywood or screw purchase is inferred.",
            "tools_and_service": "Actual ring/socket AF/outer diameter/depth, approach and handle/index stroke, nut reach and withdrawal; connectors/harness slack and bend radius. The new 200 sides and 100 shafts have no transferred access PASS.",
            "Actual": "", "Disposition": ""},
        "stock": {key: inventory["wood_and_panels"][key] for key in ("added_cleat_dimensions_mm", "added_cleat_quantity",
            "conditional_offcut_allocations", "existing_stock_purchase_scenario", "existing_nominal_board_feet", "new_purchased_stock_required")},
        "cost": {key: inventory["cost"][key] for key in ("C4_usd", "angle_cost_formula", "conditional_hardware_formula", "conditional_priced_subset_usd", "unpriced_U", "limits")},
        "cost_interpretation": "Six four-packs supply 24 angles: 22 installed and 2 spares. The frozen October 7 partial $61.93 covers comparison offers only; 68 new bolts, 24 legacy washers, C4, receipts and shipping/tax remain unpriced. It is not a current configured quotation or purchase selection.",
        "nominal_mass_kg": inventory["mass"]["conditional_same_basis_total_kg"],
        "limits": ["Actual/Disposition cells remain blank; no parts, wood, floor, hardware or tools were inspected.",
                   "This practical disposition does not consume the live A12 run or transfer predecessor forces, path passes or joint acceptance.",
                   "A failed fit or criterion governs its affected physical operation; other bounded analysis work may continue.",
                   "No anchor, floor-friction test, external sign-off, physical capacity or fabrication/climbing release is added."],
        "release": geometry["release"]}
    require(source_pins() == before, "practical source bytes changed during readback")
    output["source_pins_before_after_unchanged"] = True
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve every existing practical disposition")
    payload = result()
    payload["execution"] = {"command": sys.orig_argv, "python": sys.version,
        "CAD_native_query_assembly_q_K_or_solve": False, "dependency": "stdlib savedJSON arithmetic only"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
