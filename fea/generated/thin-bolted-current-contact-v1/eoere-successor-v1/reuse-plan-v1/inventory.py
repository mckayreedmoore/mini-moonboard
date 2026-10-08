"""Source-bound nominal inventory arithmetic; no CAD imports or forces."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import platform
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
SOURCES = {
    "joined": ("fea/generated/thin-bolted-build-planning-v4/joined-shop-data-final.json", "7982d8612014d6d55279f7847798ea3bf87e6c2eca2fa585ef4457daf3787074"),
    "old_access": (f"{BASE}/access-takeoff-v4.json", "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c"),
    "old_layout": (f"{BASE}/mixed-offset-rows-shallow-wires-v4.json", "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"),
    "raw_stock": (f"{BASE}/native-geometry-v4.json", "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"),
    "product": (f"{BASE}/eoere-successor-v1/product-inputs-final.json", "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309"),
    "prices": ("fea/generated/thin-bolted-build-planning-v4/price-observations.json", "fa2cbf1008c2454154f5cd7bb9a2885d8f602b3320a85b951fd92902fa6209aa"),
    "access_method": ("scripts/thin_bolted_access_takeoff.py", "8f6313a4609f935c173b151843527b0911d6b89a34dacc9b2eee2642523cb897"),
    "hardware_method": ("scripts/thin_bolted_occupied.py", "ffe285122150654f97dba1682d1f96da9aab470547bba6e3173207a03a449b77"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def merge(pins, additions):
    for path, expected in additions.items():
        require(path not in pins or pins[path] == expected, f"conflicting source: {path}")
        pins[path] = expected


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, f"changed source: {path}")


def reused_functions():
    """Compile only the two unchanged pure functions, preserving source filename."""
    relative, expected = SOURCES["access_method"]
    path = ROOT / relative
    require(sha(path) == expected, "access arithmetic source differs")
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"pack_purchase", "bolt_thread_fit"}]
    require(len(nodes) == 2, "missing pure arithmetic functions")
    namespace = {"Decimal": Decimal, "math": math}
    # The exact frozen hash is checked above; retain the two original pure functions.
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return namespace["pack_purchase"], namespace["bolt_thread_fit"]


def hardware_volumes(axis, washer_overrides=None):
    """Exact scalar volumes of the pinned local_hardware envelope recipe."""
    h = axis["hardware_scenario"]
    diameter = axis["diameter_mm"]
    length = axis["nominal_under_head_length_mm"]
    shaft_area = math.pi * diameter ** 2 / 4
    hex_area = math.sqrt(3) * h["hex_across_flats_mm"] ** 2 / 2
    volumes = {"shaft": shaft_area * length, "head": hex_area * h["head_height_mm"],
               "nut": (hex_area - shaft_area) * h["nut_height_mm"]}
    for role in ("head_washer", "nut_washer"):
        override = (washer_overrides or {}).get((axis["id"], role), {})
        od, inner, thickness = (override.get("od_mm", h["washer_od_mm"]),
                                override.get("id_mm", h["washer_id_mm"]),
                                override.get("thickness_mm", h["washer_thickness_mm"]))
        volumes[role] = math.pi * (od ** 2 - inner ** 2) * thickness / 4
    require(all(math.isfinite(v) and v > 0 for v in volumes.values()), "invalid envelope volume")
    return volumes


def evaluate(geometry_path, expected_sha):
    geometry_path = geometry_path.resolve()
    require(sha(geometry_path) == expected_sha, "occupied geometry identity differs")
    geometry = json.loads(geometry_path.read_text())
    require(geometry["schema"] == "eoere_bolted_occupied_geometry/v1", "geometry schema")
    require(geometry["counts"]["bracket"] == geometry["counts"]["timber"] == 22, "22 angle/timber scenario required")
    pins = {p: s for p, s in SOURCES.values()}
    pins[str(OWN.relative_to(ROOT))] = LOADED_SHA
    pins[str(geometry_path.relative_to(ROOT))] = expected_sha
    test = OWN.parent / "test_inventory.py"
    pins[str(test.relative_to(ROOT))] = sha(test)
    verify(pins)
    data = {key: json.loads((ROOT / path).read_text()) for key, (path, _) in SOURCES.items() if key not in {"access_method", "hardware_method"}}
    for source in [geometry, *data.values()]:
        merge(pins, source.get("source_sha256", {}))
    for row in geometry["finished_solids"]:
        merge(pins, {row["path"]: row["sha256"]})
    verify(pins)
    purchase, thread_fit = reused_functions()
    axes = geometry["axes"]
    require(len(axes) == len({a["id"] for a in axes}) == 100, "one hundred unique shafts")
    require(Counter(a["source"] for a in axes) == {"eoere_far_pair": 84, "cleat_post_through_bolt": 4, "original_starting_frame_axis": 12}, "axis ownership")
    old_axes = {a["id"]: a for a in data["old_layout"]["installed_axes"]}
    legacy = [a for a in axes if a["source"] == "original_starting_frame_axis"]
    for axis in legacy:
        old = old_axes[axis["id"]]
        for key in ("receivers", "grip_mm", "diameter_mm", "bore_diameter_mm", "before_plate_mm", "after_plate_mm", "hardware_scenario", "nominal_under_head_length_mm"):
            require(axis[key] == old[key], f"changed legacy requirement: {axis['id']}/{key}")
    groups, washer_counts, volume_totals = {}, Counter(), Counter()
    for axis in axes:
        h = axis["hardware_scenario"]
        washers = {(axis["id"], role): {"thickness_mm": h["washer_thickness_mm"], "id_mm": h["washer_id_mm"]}
                   for role in ("head_washer", "nut_washer")}
        fit = thread_fit(axis, washers)
        require(abs(fit["tip_projection_beyond_nut_mm"] - axis["tip_projection_beyond_nut_mm"]) < 1e-9, "tip arithmetic source mismatch")
        key = tuple(round(axis[k], 6) for k in ("diameter_mm", "grip_mm", "before_plate_mm", "after_plate_mm", "nominal_under_head_length_mm")) + (axis["source"],)
        if key not in groups:
            groups[key] = {"diameter_mm": axis["diameter_mm"], "wood_grip_mm": round(axis["grip_mm"], 6),
                           "near_steel_mm": axis["before_plate_mm"], "far_steel_mm": axis["after_plate_mm"],
                           "nominal_length_mm": axis["nominal_under_head_length_mm"],
                           "nominal_length_in": axis["nominal_under_head_length_mm"] / 25.4,
                           "source": axis["source"], "axis_ids": [], "quantity": 0,
                           "thread_fit": {k: v for k, v in fit.items() if k != "axis_id"},
                           "full_smooth_body_to_farthest_modeled_bearing_end_target_mm": h["washer_thickness_mm"] + axis["before_plate_mm"] + axis["grip_mm"] + axis["after_plate_mm"],
                           "minimum_underhead_for_modeled_nut_and_two_tip_threads_mm": fit["nut_near_face_from_under_head_mm"] + h["nut_height_mm"] + 2 * 25.4 / h["threads_per_inch"],
                           "hardware_scenario": h, "Actual": "", "Disposition": ""}
        groups[key]["axis_ids"].append(axis["id"])
        groups[key]["quantity"] += 1
        washer_counts[(h["washer_od_mm"], h["washer_id_mm"], h["washer_thickness_mm"])] += 2
        volume_totals.update(hardware_volumes(axis))
    old_overrides = {(r["axis_id"], r["role"]): r for r in data["old_layout"]["small_washer_changes"]}
    old_volume = math.fsum(v for a in old_axes.values() for v in hardware_volumes(a, old_overrides).values())
    old_access = data["old_access"]["takeoff"]
    old_mass = old_access["mass"]
    old_mass_error = old_volume * 7850e-9 - old_mass["conditional_bolt_metal_kg_at_7850"]
    require(abs(old_mass_error) < 1e-10, "analytic recipe fails saved old metal-volume check")
    timber_volume = math.fsum(r["volume_mm3"] for r in geometry["finished_solids"])
    timber_mass = timber_volume * 500e-9
    require(abs(timber_mass - geometry["mass"]["finished_frame_kg_at_500_kg_m3"]) < 1e-10, "finished timber arithmetic")
    native_raw_volume = math.fsum(r["volume_mm3"] for r in data["raw_stock"]["raw_parts"])
    cleat_blank_volume = 38.1 * 139.7 * 289.7
    require(abs((native_raw_volume + 2 * cleat_blank_volume) * 500e-9 - geometry["mass"]["raw_frame_kg_at_500_kg_m3"]) < 1e-10, "raw stock plus cleats arithmetic")
    panels = [r for r in old_mass["finished_wood"] if r["kind"] == "panel"]
    require(len(panels) == 6 and geometry["changes"]["Hillman_axes_moved"] == [], "unchanged panel/screw inputs")
    panel_mass = math.fsum(r["mass_kg_at_500kg_m3"] for r in panels)
    angle_mass = float(Decimal(22) * Decimal("1.46") * Decimal("0.45359237"))
    bolt_mass = math.fsum(volume_totals.values()) * 7850e-9
    small_metal = old_mass["screw_and_tnut_conditional_CAD_mass_kg"]
    total_mass = timber_mass + panel_mass + angle_mass + bolt_mass + small_metal + 25
    price_lines = {int(r["url"].split("product=")[1]): r for r in data["prices"]["boltdepot_lines"]}
    quote_rows = []
    for sku, quantity, requirement in [(407, 4, "1/2 x8in Grade5 bolt comparison"), (367, 8, "3/8 x4in Grade5 bolt comparison"),
                                      (368, 20, "3/8 x4.5in Grade5 bolt comparison"), (2586, 4, "1/2 coarse Grade8 nut comparison"),
                                      (2571, 96, "3/8 coarse Grade5 nut comparison")]:
        p = price_lines[sku]
        quote_rows.append({"sku": sku, "requirement": requirement, "url": p["url"],
                           "source_snapshot": data["prices"]["observed_date_america_denver"],
                           "comparison_only_no_SKU_selection_or_delivered_fit": True,
                           **purchase(quantity, p["listed_each_usd"], p["pack_quantity"], p["listed_pack_usd"])})
    washer_product = data["product"]["nonselected_washer_comparison"]
    wp = washer_product["catalog_price_comparison_only_usd"]
    require(washer_counts[(26.162, 11.1125, 2.6416)] == 176, "new washer inventory")
    quote_rows.append({"sku": 2996, "requirement": "176 new3/8 USS washer comparisons; modeled OD/thickness are published maxima", "url": washer_product["url"],
                       "comparison_only_no_SKU_selection_or_delivered_fit": True,
                       **purchase(176, wp["each"], 100, wp["bag_100"])})
    subtotal = sum(Decimal(str(row["cost_usd"])) for row in quote_rows)
    exact_legacy_bolt_subtotal = sum(Decimal(str(price_lines[sku]["listed_each_usd"])) * 4 for sku in (407, 367, 368))
    allocations = []
    for stick in old_access["stock"]["sticks"]:
        if stick["members"] in (["base_floor_left"], ["base_floor_right"]):
            extra = 289.7 + old_access["stock"]["kerf_mm_per_output_piece"]
            require(stick["remaining_mm"] > extra, "runner offcut too short")
            allocations.append({"existing_stick_members": stick["members"], "cleat_grain_length_mm": 289.7,
                                "additional_piece_plus_kerf_mm": extra, "nominal_remaining_mm": stick["remaining_mm"] - extra,
                                "delivered_usable_offcut_or_grade_verified": False})
    require(len(allocations) == 2, "two runner offcut scenarios")
    shortest_legacy = []
    joined_axes = {a["axis_id"]: a for a in data["joined"]["axes"]}
    for axis in legacy:
        if axis["diameter_mm"] != 12.7:
            continue
        g = next(r for r in groups.values() if axis["id"] in r["axis_ids"])
        old_check = joined_axes[axis["id"]]["stack"]
        shortest_legacy.append({"axis_id": axis["id"], "source_shortest_comparison_underhead_mm": old_check["comparison_shortest_underhead_mm"],
                                "current_modeled_nut_two_tip_minimum_underhead_mm": g["minimum_underhead_for_modeled_nut_and_two_tip_threads_mm"],
                                "shortest_comparison_margin_against_current_modeled_stack_mm": old_check["comparison_shortest_underhead_mm"] - g["minimum_underhead_for_modeled_nut_and_two_tip_threads_mm"],
                                "separate_saved_product_tolerance_stack_margin_mm": old_check["comparison_two_tip_margin_mm_frozen_washers_nut_max"] if "comparison_two_tip_margin_mm_frozen_washers_nut_max" in old_check else old_check["comparison_two_tip_margin_mm"],
                                "delivered_fit": None})
    verify(pins)
    return {
        "schema": "eoere_successor_nominal_inventory_cost_mass/v1", "candidate": geometry["candidate"], "geometry_revision": geometry["revision"],
        "geometry_source": {"path": str(geometry_path.relative_to(ROOT)), "sha256": expected_sha, "status": geometry["status"],
                            "collision_counts_preserved": {k: len(v) for k, v in geometry["collisions"].items()}, "geometry_or_strength_PASS_transferred": False},
        "counts": {"physical_shafts": 100, "heads": 100, "nuts": 100, "washers": 200, "modeled_bolt_roles": 500,
                   "angles_installed": 22, "four_packs": 6, "angles_purchased": 24, "spare_angles": 2,
                   "existing_timbers": 20, "added_cleats": 2, "total_timbers": 22, "panels": 6, "Hillman_42605": 66,
                   "factory_holes": 176, "installed_factory_holes": 88, "unused_factory_holes": 88, "shared_angle_shafts": 4},
        "shaft_groups": [groups[k] for k in sorted(groups)],
        "washer_groups": [{"OD_mm": k[0], "ID_mm": k[1], "thickness_mm": k[2], "quantity": count, "Actual": "", "Disposition": ""}
                          for k, count in sorted(washer_counts.items())],
        "thread_and_shank_obligations": {"requirements": ["Bind each delivered underhead length, shank, root and runout to all own wood/steel bearing and shear intervals.",
                                                         "Nut must reach its seat with full metal-nut engagement and the declared two-tip-thread target; nominal length is insufficient.",
                                                         "Full-smooth-body targets are conditional geometric coverage targets, not a blanket resistance requirement; classify actual threaded bearing before selecting strength inputs.",
                                                         "Verify actual head/nut/washer dimensions and contact/unused-hole/heel/tool support. No preload, torque or friction is supplied."],
                                        "four_8inch_comparisons": shortest_legacy},
        "wood_and_panels": {"existing_stock_purchase_scenario": old_access["stock"]["purchase_quantities"], "existing_nominal_board_feet": 150,
                            "added_cleat_quantity": 2, "added_cleat_dimensions_mm": [38.1, 139.7, 289.7],
                            "added_cleat_total_raw_volume_mm3": 2 * cleat_blank_volume, "added_cleat_total_raw_mass_kg_at_500": 2 * cleat_blank_volume * 500e-9,
                            "conditional_offcut_allocations": allocations, "new_purchased_stock_required": None,
                            "six_panel_blank_envelopes": old_access["stock"]["panel_blanks"], "old_nominal_4x8_sheet_scenario": 3,
                            "limits": "Original13-stick nesting can nominally fit both new cleats in runner offcuts, with existing per-stick end allowance already charged. Actual stock, grain/grade and usable offcuts need inspection. Existing cut-panel size/thickness reconciliation remains open; no added plywood/screw purchase is inferred."},
        "mass": {"wood_density_kg_m3": 500, "bolt_envelope_density_kg_m3": 7850, "finished_timber_volume_mm3": timber_volume,
                 "finished_timber_kg": timber_mass, "unchanged_panels_kg": panel_mass, "installed_angles_drawing_kg": angle_mass,
                 "purchased_angles_drawing_kg_excluding_packaging": 15.8938766448, "modeled_bolt_role_volumes_mm3": dict(volume_totals),
                 "modeled_bolt_roles_kg": bolt_mass, "unchanged_screw_and_Tnut_CAD_kg": small_metal,
                 "original_accessory_allowance_kg": 25, "conditional_same_basis_total_kg": total_mass,
                 "predecessor_conditional_total_range_kg": old_mass["dead_mass_with_original_25kg_accessory_allowance_range"],
                 "same_basis_difference_from_predecessor_range_kg": [total_mass - old_mass["dead_mass_with_original_25kg_accessory_allowance_range"][1], total_mass - old_mass["dead_mass_with_original_25kg_accessory_allowance_range"][0]],
                 "analytic_old70_recipe_mass_error_kg": old_mass_error,
                 "complete_observed_mass_or_response_load_vector": None,
                 "limits": "Cylinder shafts omit threads; hex heads/nuts omit delivered chamfers/details, nut bore is ideal, washers use scenario dimensions. Densities, drawing weight and25kg allowance are not measured. Pads and accessories outside the original allowance remain excluded. This inventory total supplies no adopted gravity ownership or new mechanics field."},
        "cost": {"currency": "USD", "C4_usd": None, "angle_cost_formula": "6*C4 plus shipping/tax", "exact_unchanged12_legacy_bolt_SKU_comparison_subtotal_usd": float(exact_legacy_bolt_subtotal),
                 "exact_unchanged12_legacy_bolts_plus_legacy_nut_comparison_usd": 24.96,
                 "conditional_reused_nominal_SKU_comparison_lines": quote_rows, "conditional_priced_subset_usd": float(subtotal),
                 "conditional_hardware_formula": f"6*C4 + {subtotal} + U; shipping/tax excluded",
                 "unpriced_U": ["60 new3/8x2.5in bolts", "4 new3/8x3in bolts", "4 new3/8x6in bolts", "8 retained1/2 washers", "16 retained3/8 washers", "wood/plywood/screw receipts or actual additional stock", "holds/electrical/pads/tools/machining/shipping/tax"],
                 "limits": "Oct7 frozen price observations are comparison offers, not a current configured quote or product selection. New4in/4.5in stacks match existing nominal bolt product descriptions but have different grips; their fit is unqualified. Grade5/Grade8 nut and washer offers are nonselected scenarios. Old177USD angles and314.17USD partial hardware are not transferred. Complete installed cost remains unknown."},
        "source_binding": {"direct_source_sha256": {**{p: s for p, s in SOURCES.values()}, str(geometry_path.relative_to(ROOT)): expected_sha,
                                                    str(OWN.relative_to(ROOT)): LOADED_SHA, str(test.relative_to(ROOT)): sha(test)},
                           "expanded_referenced_pin_count": len(pins), "expanded_source_map_canonical_sha256": canonical(pins), "all_before_after_pins_unchanged": True,
                           "source_maps_reused": ["geometry.source_sha256", "joined.source_sha256", "old_access.source_sha256", "old_layout.source_sha256", "raw_stock.source_sha256", "product.source_sha256"],
                           "finished22_BREP_hashes_checked_without_import": True},
        "execution": {"sys_argv": list(sys.argv), "sys_orig_argv": list(sys.orig_argv), "python": platform.python_version(),
                      "executable": sys.executable, "PYTHONPATH": os.environ.get("PYTHONPATH"), "dependencies": "stdlib only; two pinned pure arithmetic AST functions"},
        "scope": {"CAD_import_or_query": False, "native_or_response_solve": False, "q_K_or_actions_consumed": False, "old_force_or_PASS_transfer": False},
        "release": {"fabrication": False, "climbing": False, "purchase": False, "capacity": False, "mechanics_ready": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing inventory")
    result = evaluate(options.geometry, options.expected_sha256)
    with options.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"path": str(options.out), "sha256": sha(options.out), "bytes": options.out.stat().st_size,
                      "conditional_mass_kg": result["mass"]["conditional_same_basis_total_kg"],
                      "conditional_priced_subset_usd": result["cost"]["conditional_priced_subset_usd"]}))


if __name__ == "__main__":
    main()
