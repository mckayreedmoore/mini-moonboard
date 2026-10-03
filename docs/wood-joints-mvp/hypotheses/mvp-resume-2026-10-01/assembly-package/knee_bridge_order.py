"""Reconcile an unadopted four-stack bridge with the frozen current order."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
UPPER = HERE.parent / "upper-corner-screw-layout"
RAW = HERE / "rawlocal/knee-bridge-order"
ORDER = HERE / "rawlocal/working-order/attempt03/working-order.json"
SETUP = HERE / "rawlocal/knee-bridge-fit/prepare-attempt02/setup.json"
PROPOSAL = UPPER / "rawlocal/knee-spine-reinforcement/attempt01/checks.json"
FRAME = UPPER / "frame-250-attempt02/comparison.json"
PINS = {
    ORDER: "6becf19a9b06f625b4292cc8cd60f908fd3bff8d865430e60abcec155af4e9be",
    SETUP: "794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb",
    PROPOSAL: "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778",
    FRAME: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, record):
    Path(path).write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")


def build(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate output child required")
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    for path, digest in pins.items():
        require(sha(path) == digest, f"frozen input differs: {path}")
    order, setup, proposal, frame = [json.loads(p.read_text()) for p in (ORDER, SETUP, PROPOSAL, FRAME)]
    require(not proposal["proposal_adopted"] and setup["counts"]["stacks"] == 4,
            "require the unadopted four-stack proposal")
    bolts, nuts, washers = [copy.deepcopy(order[name]) for name in (
        "bolt_order_lines", "nut_order_lines", "washer_order_lines")]
    require([sum(row["quantity_required"] for row in rows) for rows in (bolts, nuts, washers)] == [104, 104, 208],
            "current order census differs")
    family = {"family_id": "proposed_knee_v_bridge_4", "quantity": 4}
    bolts.append({"line_id": "proposed_kljack_25C650HCS5Z", "item": "25C650HCS5Z",
                  "supplier": "K.L. Jack", "category": "structural_bolts", "quantity_required": 4,
                  "working_nominal_lengths_in": ["6.5"], "family_allocations": [family],
                  "minimum_order_pack_quantity": None, "minimum_packs_to_cover": None,
                  "spare_if_minimum_packs_ordered": None, "delivery_conformity": None,
                  "planning_status": "proposal only; partial-thread Grade 5 and stated full-form profile required",
                  "price": {"unit_price_usd": None, "package_price_usd": None}})
    matched = next(row for row in nuts if row["item"] == "25CNFH5Z")
    require(matched["quantity_required"] == 84, "matched nut pool differs")
    matched["quantity_required"] += 4
    matched["family_allocations"].append(family)
    thick = next(row for row in washers if row["item"] == "885522")
    require(thick["quantity_required"] == 8 and thick["listed_pack_quantity"] == 4,
            "thick washer pool differs")
    thick["quantity_required"] += 8
    thick["family_allocations"].append({**family, "quantity": 8})
    thick["nominal_packs_to_cover"] = math.ceil(thick["quantity_required"] / thick["listed_pack_quantity"])
    counts = [sum(row["quantity_required"] for row in rows) for rows in (bolts, nuts, washers)]
    require(counts == [108, 108, 216], "proposal order census differs")
    lawson = next(row for row in bolts if row["item"] == "FA21103")
    require(lawson["quantity_required"] == 24 and lawson["minimum_packs_to_cover"] == 1,
            "four shorter bridge bolts must not add a Lawson pack")
    hardware = setup["proposal"]["stock_and_component_envelopes"]
    diameter = 6.35
    disk = math.pi * diameter**2 / 4
    hex_area = lambda af: math.sqrt(3) * af**2 / 2
    od, inside, thickness = hardware["washer"]["OD_ID_thickness_mm"]
    volumes = {
        "one_nominal_shaft_mm3": disk * hardware["stock"]["nominal_underhead_length_mm"],
        "one_full_hex_head_mm3": hex_area(hardware["head"]["across_flats_max_mm"]) * hardware["head"]["height_max_mm"],
        "one_nominal_bored_hex_nut_mm3": (hex_area(hardware["nut"]["across_flats_max_mm"]) - disk)
                                      * hardware["nut"]["height_range_mm"][1],
        "one_annular_washer_mm3": math.pi * (od**2 - inside**2) / 4 * thickness,
    }
    per_stack = sum(volumes.values()) + volumes["one_annular_washer_mm3"]
    steel_mass = 4 * per_stack * 7850 / 1e9
    removed_wood = sum(g["removed_wood_mass_at_original600_kg_m3_kg"] for g in proposal["geometry_proposals"].values())
    delta = steel_mass - removed_wood
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    report = {"status": "UNADOPTED_BRIDGE_ORDER_RECONCILED", "source_sha256": {
        str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "current_counts": {"bolts": 104, "nuts": 104, "washers": 208, "Hillman_screws": 66},
        "proposed_counts": {"bolts": 108, "nuts": 108, "washers": 216, "Hillman_screws": 66},
        "timber_and_plywood_body_count_unchanged": 50, "timber_blank_count_unchanged": 44,
        "bolt_order_lines": bolts, "nut_order_lines": nuts, "washer_order_lines": washers,
        "new_stock_family_count": 1, "new_bolt_axis_ids": [s["axis_id"] for s in setup["stacks"]],
        "mass_planning_convention": {"steel_density_kg_m3": 7850, "wood_density_kg_m3": 600,
            "component_volumes_mm3": volumes, "added_hardware_mass_kg": steel_mass,
            "removed_wood_mass_kg": removed_wood, "net_mass_delta_kg": delta,
            "frozen_modeled_frame_mass_kg": frame["modeled_mass_kg"],
            "arithmetic_frame_plus_delta_kg": frame["modeled_mass_kg"] + delta,
            "equipment_mass_separate_kg": 25,
            "scope": "Geometric planning convention, not measured mass or a strict upper bound: full nominal shaft, full regular-hex head, nominal-diameter bored hex nut, annular washers. Threads, chamfers and fillets omitted. Frozen frame conventions retained; no new force solve."},
        "price_or_current_order_total_established": False, "actual_hardware_mass_kg": None,
        "source_order_changed": False, "global_gravity_adopted": False,
        "proposal_adopted": False, "physical_release": False}
    for path, digest in pins.items():
        require(sha(path) == digest, f"input changed during reconciliation: {path}")
    dump(output / "proposal-order.json", report)
    dump(output / "receipt.json", {"source_sha256": report["source_sha256"], "sources_unchanged": True,
                                   "output_sha256": {n: sha(output / n) for n in (
                                       ".gitignore", "producer.py.snapshot", "proposal-order.json")},
                                   "proposal_adopted": False, "physical_release": False})
    return {"status": report["status"], "proposed_counts": report["proposed_counts"],
            "mass_delta_kg": delta, "order_sha256": sha(output / "proposal-order.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), allow_nan=False))
