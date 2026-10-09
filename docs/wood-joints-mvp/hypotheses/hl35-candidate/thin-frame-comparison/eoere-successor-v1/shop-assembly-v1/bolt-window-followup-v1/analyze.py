"""Reuse issued dimension windows on three intermediate, unadopted bolt lengths."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import runpy
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[8]
HERE = OWN.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "conflicting source: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def corner_check(stack, product, diameter, window):
    """Independently enumerate length, two washers, nut and gage endpoints."""
    length = product["nominal_length_in"] * 25.4
    lengths = [length - product["length_tolerance_minus_in"] * 25.4, length]
    washers = [v * 25.4 for v in diameter["washer"]["thickness_bounds_in"]]
    nuts = [v * 25.4 for v in diameter["nut"]["height_bounds_in"]]
    # A nonnegative gage up to Lg,max bounds seating; zero is an arithmetic
    # envelope endpoint, not a claimed physical minimum or thread coordinate.
    gages = [0.0, product["Lg_max_in"] * 25.4]
    pitch = 25.4 / diameter["threads_per_inch"]
    margins, seats = [], []
    for length, head, washer, nut, gage in itertools.product(lengths, washers, washers, nuts, gages):
        margins.append(length - stack - head - washer - nut - 2 * pitch)
        seats.append(stack + head + washer - gage)
    require(abs(min(margins) - window["catalog_min_length_max_stack_two_tip_margin_mm"]) < 1e-10,
            "length extremum differs from independent corners")
    require(abs(min(seats) - window["nut_near_minus_Lg_max_bounds_mm"][0]) < 1e-10,
            "gage extremum differs from independent corners")
    return {"corner_count": len(margins), "minimum_two_pitch_margin_mm": min(margins),
            "minimum_nut_near_minus_gage_mm": min(seats),
            "scope": "Endpoint enumeration of the declared comparison box; no physical thread model."}


def evaluate():
    spec_path = HERE / "inputs.json"
    spec = json.loads(spec_path.read_bytes())
    pins = {r["path"]: r["sha256"] for r in spec["sources"].values()}
    merge(pins, {str(OWN.relative_to(ROOT)): sha(OWN), str(spec_path.relative_to(ROOT)): sha(spec_path)})
    verify(pins)
    helper = runpy.run_path(str(ROOT / spec["sources"]["hardware_method"]["path"]))
    _, _, data, inherited, _, _, _, bounds = helper["prepare"]()
    merge(pins, inherited)
    geometry = json.loads((ROOT / spec["sources"]["current_geometry"]["path"]).read_bytes())
    require(geometry["candidate"] == spec["candidate"]
            and geometry["revision"] == spec["geometry_revision"], "current geometry identity")
    require(geometry["axes"] == data["geometry"]["axes"], "current complete axis records differ")
    require(len(geometry["axes"]) == len({a["id"] for a in geometry["axes"]}) == 100,
            "current physical shaft census")
    require(all(v is False for v in geometry["release"].values())
            and all(v is False for v in spec["release"].values()), "release changed")
    merge(pins, geometry["source_sha256"])
    verify(pins)
    prior = json.loads((ROOT / spec["sources"]["hardware_result"]["path"]).read_bytes())
    csv_path = ROOT / spec["sources"]["hardware_table"]["path"]
    with csv_path.open(newline="") as stream:
        worksheet = {r["axis_id"]: r for r in csv.DictReader(stream)}
    axes = {a["id"]: a for a in geometry["axes"]}
    require(set(worksheet) == set(axes), "worksheet/current census differs")
    require(all(r[k] == "" for r in worksheet.values() for k in helper["ACTUAL_STACK"]),
            "actual receiving cells were filled")
    groups = [g for g in prior["nominal_stack_groups"]
              if g["catalog_window"]["catalog_min_length_max_stack_two_tip_margin_mm"] < 0]
    require([g["quantity"] for g in groups] == [16, 4, 4], "issued short group census")
    products = {p["old_sku"]: p for p in spec["products"]}
    require(len(products) == 3, "proposal product census")
    rows, chosen, total_cost = [], [], 0.0
    for group in groups:
        old = group["bolt_comparison"]
        product = products[old["sku"]]
        diameter = next(d for d in data["catalog"]["diameters"]
                        if d["diameter_in"] == product["diameter_in"])
        stack = group["receiver_plus_plate_mm"]
        require(stack == product["receiver_plus_plate_mm"] and group["quantity"] == product["quantity"],
                "wrong proposal group join")
        require(product["partially_threaded"] is True, "full-thread substitute")
        window = bounds(stack, product, diameter)
        old_window = bounds(stack, old, diameter)
        require(old_window == group["catalog_window"], "issued window changed")
        corners = corner_check(stack, product, diameter, window)
        require(corners["minimum_two_pitch_margin_mm"] > 0
                and corners["minimum_nut_near_minus_gage_mm"] > 0, "proposed comparison fails")
        delta = (product["nominal_length_in"] - old["nominal_length_in"]) * 25.4
        proof = []
        for axis_id in group["axis_ids"]:
            axis, saved = axes[axis_id], worksheet[axis_id]
            require(float(saved["receiver_plus_plate_mm"]) == stack
                    and int(saved["comparison_bolt_SKU"]) == old["sku"], "worksheet group differs")
            require(abs(axis["grip_mm"] + axis["before_plate_mm"] + axis["after_plate_mm"] - stack) < 1e-8,
                    "current receiver stack differs")
            target = float(saved["model_body_to_farthest_bearing_target_mm"])
            proof.append({"axis_id": axis_id, "receiver_ids": axis["receivers"],
                          "nominal_tip_extension_delta_xyz_mm": [delta * d for d in axis["direction_xyz"]],
                          "saved_farthest_bearing_body_target_mm": target,
                          "target_minus_proposed_Lb_min_mm": target - window["ASME_Lb_min_mm"],
                          "target_minus_proposed_Lg_max_mm": target - window["ASME_Lg_max_mm"]})
            chosen.append(axis_id)
        packs = math.ceil(product["quantity"] / product["pack_quantity"])
        cost = round(packs * product["observed_pack_price_usd"], 2)
        total_cost += cost
        rows.append({"old_sku": old["sku"], "proposal": product,
                     "original_window": old_window, "intermediate_window": window,
                     "independent_corners": corners, "own_axes": proof,
                     "nominal_underhead_tip_and_withdrawal_increment_mm": delta,
                     "buy_packs": packs, "buy_bolts": packs * product["pack_quantity"],
                     "pack_spend_usd_before_shipping_tax": cost,
                     "adopted": False, "smooth_body_or_resistance_accepted": False,
                     "new_tip_and_tool_clearance_verified": False})
    require(len(chosen) == len(set(chosen)) == 24
            and set(chosen) == set(prior["catalog_short_stack_axis_ids"]), "flagged own axis coverage")
    verify(pins)
    return {"schema": "eoere_intermediate_bolt_dimension_result/v1",
            "status": "PASS_CONDITIONAL_LENGTH_AND_GAGE_COMPARISON_ONLY_UNADOPTED",
            "candidate": spec["candidate"], "geometry_revision": spec["geometry_revision"],
            "all100_current_axis_records_exact": True, "unchanged_nominal_recipe_count": 100,
            "all100_axis_records_sha256": canonical(geometry["axes"]),
            "proposed_axis_count": 24, "retained_other_axis_count": 76,
            "source_sha256": pins, "source_pin_count": len(pins),
            "source_pins_verified_before_after": True,
            "independent_box_corner_count": sum(r["independent_corners"]["corner_count"] for r in rows),
            "groups": rows, "proposed_24_bolt_pack_spend_usd": round(total_cost, 2),
            "source_limits": spec["limits"], "standard_transcription": spec["standard_transcription"],
            "release": spec["release"],
            "execution": {"CAD": False, "solver_or_force_field_consumption": False,
                          "physical_work": False, "dependencies": "Python standard library only"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    arguments = parser.parse_args()
    require(not arguments.out.exists(), "preserve issued output")
    result = evaluate()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"out": str(arguments.out), "sha256": sha(arguments.out),
                      "source_pin_count": result["source_pin_count"],
                      "proposal_axes": result["proposed_axis_count"], "status": result["status"]}))
