"""Bound four cleat/post hardware specifications with saved scalar methods only."""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import json
import math
import platform
import runpy
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = OWN.parents[8]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def close(a, b, message):
    require(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-8), message)


def evaluate():
    spec_path = HERE / "inputs.json"
    spec = json.loads(spec_path.read_bytes())
    pins = {ref["path"]: ref["sha256"] for ref in spec["sources"].values()}
    pins[str(spec_path.relative_to(ROOT))] = sha(spec_path)
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)

    def verify():
        require(all(sha(ROOT / path) == digest for path, digest in pins.items()),
                "changed pinned source")

    def source(name):
        return ROOT / spec["sources"][name]["path"]

    def read(name):
        return json.loads(source(name).read_bytes())

    verify()
    frozen = read("frozen_receiver_packet")
    prior_files = frozen["final_files"] + frozen["retained_development_files"]
    for record in prior_files:
        require(record["path"] not in pins or pins[record["path"]] == record["sha256"],
                "conflicting retained pin")
        pins[record["path"]] = record["sha256"]
    verify()
    # This saved module imports only the standard library. Do not call prepare().
    hardware = runpy.run_path(str(source("hardware_method")))
    bounds = hardware["pure_functions"](spec["sources"]["window_method"],
                                         {"bounds_for", "number", "require"})["bounds_for"]
    corner_check = runpy.run_path(str(source("corner_method")))["corner_check"]
    tree = ast.parse(source("access_method").read_text())
    tool_nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "TOOL" for t in n.targets)]
    require(len(tool_nodes) == 1, "conditional tool literal missing")
    tool = ast.literal_eval(tool_nodes[0].value)
    geometry, bottom, placement = read("geometry"), read("bottom"), read("placement")
    require(geometry["revision"] == spec["current_revision"]
            and placement["geometry_adopted"] is False, "wrong geometry/adoption")
    current = {a["id"]: a for a in geometry["axes"]}
    previous = {a["id"]: a for a in bottom["axes"]}
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    ids = spec["axis_ids"]
    require(len(current) == 100 and len(ids) == len(set(ids)) == 4
            and set(proposed) == set(ids), "axis census changed")
    require(canonical(geometry["axes"]) == placement["current_100_axes_canonical_sha256"],
            "current axis binding changed")
    require(canonical(geometry["screw_axes"]) == placement["current_66_screws_canonical_sha256"],
            "current screw binding changed")
    tables = {}
    for name in ("stacks", "access", "holes"):
        with source(name).open(newline="") as stream:
            tables[name] = list(csv.DictReader(stream))
        require(all(value == "" for row in tables[name] for key, value in row.items()
                    if key.startswith("Actual") or key == "Disposition"),
                "actual observation cell is populated")
    require([len(tables[k]) for k in ("stacks", "access", "holes")] == [100, 200, 120],
            "current worksheet census changed")
    by_id = {r["axis_id"]: r for r in tables["stacks"]}
    catalog = read("catalog")
    diameter = next(d for d in catalog["diameters"] if d["diameter_in"] == 0.375)
    products = {b["sku"]: b for b in catalog["bolts"]}
    rows = []
    for name in ids:
        axis, sheet = current[name], by_id[name]
        require(axis == previous[name], "prior four-station scalar reuse no longer applies")
        changed = copy.deepcopy(axis)
        changed["point_xyz_mm"][2] = spec["proposed_Z_mm"]
        require(changed == proposed[name], "proposal changes more than Z")
        require(axis["point_xyz_mm"][2] == spec["current_Z_mm"]
                and len(axis["receivers"]) == 2 and not axis["attachments"]
                and axis["before_plate_mm"] == axis["after_plate_mm"] == 0,
                "dedicated two-wood recipe differs")
        stack = float(sheet["receiver_plus_plate_mm"])
        close(stack, 76.2, "stack differs")
        close(stack, axis["grip_mm"], "geometry/table grip differs")
        close(float(sheet["nominal_underhead_length_mm"]), 101.6, "current length differs")
        own_holes = [r for r in tables["holes"] if r["axis_id"] == name]
        own_sides = [r for r in tables["access"] if r["axis_id"] == name]
        require(len(own_holes) == len(own_sides) == 2
                and {r["receiver"] for r in own_holes} == set(axis["receivers"])
                and {r["side"] for r in own_sides} == {"head", "nut"},
                "own receiver/access coverage differs")
        for hole in own_holes:
            close(float(hole["saved_full_wall_length_mm"]), 38.1, "receiver length differs")
        wh = axis["hardware_scenario"]["washer_thickness_mm"]
        target = float(sheet["model_body_to_farthest_bearing_target_mm"])
        close(target, wh + stack, "body target differs")
        comparisons = []
        for sku in spec["comparison_skus"]:
            product = products[sku]
            require(product["partially_threaded"] is True, "full-thread substitution")
            window = bounds(stack, product, diameter)
            corners = corner_check(stack, product, diameter, window)
            length = product["nominal_length_in"] * 25.4
            well_model = length - stack - 2 * wh
            well_max = length - stack - 2 * window["washer_each_bounds_mm"][0]
            comparisons.append({
                "sku": sku, "nominal_length_mm": length, "window": window,
                "independent_box_corners": corners,
                "minimum_body_minus_model_farthest_bearing_mm": window["ASME_Lb_min_mm"] - target,
                "possible_thread_or_runout_in_far_receiver_mm": max(0.0, target - window["ASME_Lb_min_mm"]),
                "possible_thread_or_runout_far_receiver_fraction": max(0.0, target - window["ASME_Lb_min_mm"]) / 38.1,
                "nominal_tip_beyond_nut_mm": well_model - axis["hardware_scenario"]["nut_height_mm"],
                "blind_socket_required_clear_depth_model_mm": well_model,
                "blind_socket_required_clear_depth_catalog_max_mm": well_max,
                "conditional_36mm_well_minus_required_catalog_max_mm": tool["three_eighth_inch"]["minimum_well_mm"] - well_max,
                "saved_method_bolt_headward_travel_mm": length + 2.0,
                "saved_method_nut_nutward_travel_model_mm": well_model + 2.0,
                "saved_method_nut_washer_nutward_travel_model_mm": well_model + 4.0,
                "incremental_nominal_tip_and_withdrawal_mm": length - 101.6,
                "four_bolt_individual_price_increment_usd": round(4 * (product["unit_price_usd"] - products[367]["unit_price_usd"]), 2),
                "actual_fit_or_access_or_thread_bearing_verified": False,
            })
        close(comparisons[0]["nominal_tip_beyond_nut_mm"],
              axis["tip_projection_beyond_nut_mm"], "saved model tip differs")
        require(comparisons[0]["window"]["catalog_min_length_max_stack_two_tip_margin_mm"] > 0
                and comparisons[0]["window"]["nut_near_minus_Lg_max_bounds_mm"][0] > 0,
                "existing-length comparison unexpectedly fails")
        require(comparisons[1]["minimum_body_minus_model_farthest_bearing_mm"] > 0
                and comparisons[1]["window"]["nut_near_minus_Lg_max_bounds_mm"][1] < 0,
                "longer-body/seating tradeoff changed")
        rows.append({"axis_id": name, "receivers": axis["receivers"],
                     "current_point_xyz_mm": axis["point_xyz_mm"],
                     "unadopted_proposed_point_xyz_mm": proposed[name]["point_xyz_mm"],
                     "drill_entry_xyz_mm": axis["point_xyz_mm"],
                     "drill_inward_xyz": axis["direction_xyz"],
                     "head_bolt_outward_xyz": [-v for v in axis["direction_xyz"]],
                     "nut_outward_xyz": axis["direction_xyz"],
                     "matched_wood_travel_mm": stack,
                     "planning_usable_bit_reach_mm": stack + spec["guide_mm"] + spec["backer_travel_mm"],
                     "comparisons": comparisons})
    washer = diameter["washer"]
    fillet_length = diameter["underhead_fillet_max_length_in"] * 25.4
    wh_min = washer["thickness_bounds_in"][0] * 25.4
    washer_limits = {
        "catalog_OD_bounds_mm": [v * 25.4 for v in washer["OD_bounds_in"]],
        "catalog_ID_bounds_mm": [v * 25.4 for v in washer["ID_bounds_in"]],
        "catalog_thickness_bounds_mm": [v * 25.4 for v in washer["thickness_bounds_in"]],
        "fillet_max_diameter_mm": diameter["underhead_fillet_max_diameter_in"] * 25.4,
        "fillet_max_length_mm": fillet_length,
        "minimum_ID_minus_maximum_fillet_diameter_mm": (washer["ID_bounds_in"][0] - diameter["underhead_fillet_max_diameter_in"]) * 25.4,
        "model_washer_thickness_minus_maximum_fillet_length_mm": wh - fillet_length,
        "minimum_catalog_washer_thickness_minus_maximum_fillet_length_mm": wh_min - fillet_length,
        "minimum_catalog_ID_minus_maximum_reference_wood_hole_mm": washer["ID_bounds_in"][0] * 25.4 - spec["maximum_wood_hole_mm"],
        "full_nominal_annular_seat_proof_covers_all_catalog_corners": False,
        "actual_washer_material_or_contact_or_fillet_seating_verified": False,
    }
    verify()
    return {
        "schema": "eoere_four_cleat_post_hardware_build_spec_arithmetic/v1",
        "question": spec["question"], "status": "UNADOPTED_SOURCE_BOUND_DIMENSION_COMPARISON",
        "current_revision": spec["current_revision"], "current_axes_stay_Z_mm": spec["current_Z_mm"],
        "proposed_Z_mm_unadopted": spec["proposed_Z_mm"],
        "source_pin_count": len(pins), "source_sha256": pins,
        "source_pins_verified_before_after": True, "prior_frozen_receiver_files_unchanged": len(prior_files),
        "current_four_axes_exactly_match_raised_rail_metadata": True,
        "current_100_axes_canonical_sha256": canonical(geometry["axes"]),
        "current_66_screw_axes_canonical_sha256": canonical(geometry["screw_axes"]),
        "actual_observation_cells_remain_blank": True, "four_stations": rows,
        "washer_and_fillet_limits": washer_limits,
        "conditional_tool_outline_from_existing_method": tool,
        "primary_product_reading": spec["primary_product_reading"],
        "missing_inputs_and_design_disposition": spec["missing_inputs_and_design_disposition"],
        "limits": spec["limits"], "release": spec["release"],
        "execution": {"python_version": platform.python_version(),
                      "imports": "Standard library only; selected authenticated scalar functions and literal TOOL data. No CAD, geometry import/query or solver."},
        "reproduction_command": f"uv run python -B {OWN.relative_to(ROOT)} --out {HERE.relative_to(ROOT)}/reproduction01.json",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    require(output.parent == HERE and output.suffix == ".json" and not output.exists(),
            "output must be a fresh JSON file in this owned subpacket")
    result = evaluate()
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(output.relative_to(ROOT)), "sha256": sha(output),
                      "bytes": output.stat().st_size, "source_pin_count": result["source_pin_count"]}))


if __name__ == "__main__":
    main()
