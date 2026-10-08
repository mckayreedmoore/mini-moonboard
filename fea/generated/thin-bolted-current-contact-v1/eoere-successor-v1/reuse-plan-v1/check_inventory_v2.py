"""Separate same-author source and Decimal arithmetic reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PACKET = OWN.parent
PREFIX = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
GEOMETRY = f"{PREFIX}/occupied-geometry-v2-complete/geometry.json"
MIRROR = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-geometry-v2.json"
GEOMETRY_SHA = "05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd"
INVENTORY_SHA = "14d74a158c4af7cf57d0b1282eda41e6f7e849024130be3cf869080a6ee03de3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def evaluate():
    inventory_path = PACKET / "inventory-v2.json"
    require(sha(inventory_path) == INVENTORY_SHA, "inventory bytes changed")
    inventory = json.loads(inventory_path.read_text())
    pins = dict(inventory["source_binding"]["direct_source_sha256"])
    objects = {}
    for path, expected in list(pins.items()):
        require(sha(ROOT / path) == expected, f"changed direct source: {path}")
        if path.endswith(".json"):
            obj = json.loads((ROOT / path).read_text())
            objects[path] = obj
            for source, digest in obj.get("source_sha256", {}).items():
                require(source not in pins or pins[source] == digest, "conflicting source")
                pins[source] = digest
    geometry = objects[GEOMETRY]
    for row in geometry["finished_solids"]:
        pins[row["path"]] = row["sha256"]
    require(len(pins) == inventory["source_binding"]["expanded_referenced_pin_count"] == 325, "source census")
    require(canonical(pins) == inventory["source_binding"]["expanded_source_map_canonical_sha256"], "source digest")
    pins.update({str(inventory_path.relative_to(ROOT)): INVENTORY_SHA, MIRROR: GEOMETRY_SHA, str(OWN.relative_to(ROOT)): LOADED_SHA})
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, f"changed source: {path}")
    before = canonical(pins)
    first = json.loads((ROOT / PREFIX / "occupied-geometry-v1/geometry.json").read_text())
    old_axes = {a["id"]: a for a in first["axes"]}
    changed = []
    for axis in geometry["axes"]:
        old = old_axes[axis["id"]]
        differences = [k for k in set(axis) | set(old) if axis.get(k) != old.get(k)]
        if differences:
            require(differences == ["point_xyz_mm"] and axis["source"] == "cleat_post_through_bolt", "non-position stack change")
            require(old["point_xyz_mm"][:2] == axis["point_xyz_mm"][:2], "XY change")
            require(old["point_xyz_mm"][2] == 189.3 and axis["point_xyz_mm"][2] == 200., "Z revision")
            changed.append(axis["id"])
    require(len(changed) == 4, "four changed axes")
    require(len(geometry["bore_support"]) == 120 and all(r["pre_bore_full_body_fraction"] == 1 for r in geometry["bore_support"]), "bore records")
    require(len(geometry["screw_support"]) == 132 and all(r["body_fraction"] == 1 for r in geometry["screw_support"]), "screw records")
    require(len(geometry["collisions"]) == 5 and all(not rows for rows in geometry["collisions"].values()), "preserved collision lists")
    D = lambda value: Decimal(str(value))
    with localcontext() as context:
        context.prec = 60
        pi = D("3.14159265358979323846264338327950288419716939937510582097494")
        root3 = D(3).sqrt()
        volumes = Counter()
        requirements = Counter()
        for axis in geometry["axes"]:
            h = axis["hardware_scenario"]
            circle = pi * D(axis["diameter_mm"]) ** 2 / 4
            hexagon = root3 * D(h["hex_across_flats_mm"]) ** 2 / 2
            washer = pi * (D(h["washer_od_mm"]) ** 2 - D(h["washer_id_mm"]) ** 2) * D(h["washer_thickness_mm"]) / 4
            volumes.update({"shaft": circle * D(axis["nominal_under_head_length_mm"]), "head": hexagon * D(h["head_height_mm"]),
                            "nut": (hexagon - circle) * D(h["nut_height_mm"]), "head_washer": washer, "nut_washer": washer})
            requirements[(axis["diameter_mm"], axis["nominal_under_head_length_mm"])] += 1
        role_error = max(abs(float(v) - inventory["mass"]["modeled_bolt_role_volumes_mm3"][k]) for k, v in volumes.items())
        require(role_error < 1e-8, "Decimal role volumes")
        timber = sum(D(r["volume_mm3"]) for r in geometry["finished_solids"]) * D("0.0000005")
        base = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
        access = objects[f"{base}/access-takeoff-v4.json"]
        old_mass = access["takeoff"]["mass"]
        panels = sum(D(r["finished_volume_mm3"]) for r in old_mass["finished_wood"] if r["kind"] == "panel") * D("0.0000005")
        total = timber + panels + D(22) * D("1.46") * D("0.45359237") + sum(volumes.values()) * D("0.00000785") + D(old_mass["screw_and_tnut_conditional_CAD_mass_kg"]) + D(25)
        mass_error = abs(float(total) - inventory["mass"]["conditional_same_basis_total_kg"])
        require(mass_error < 1e-10, "Decimal total mass")
        price_source = objects["fea/generated/thin-bolted-build-planning-v4/price-observations.json"]
        prices = {int(r["url"].split("product=")[1]): r for r in price_source["boltdepot_lines"]}
        product = objects[f"{base}/eoere-successor-v1/product-inputs-final.json"]
        washer_prices = product["nonselected_washer_comparison"]["catalog_price_comparison_only_usd"]
        demanded = {407: requirements[(12.7, 203.2)], 367: requirements[(9.525, 101.6)], 368: requirements[(9.525, 114.3)],
                    2586: sum(a["diameter_mm"] == 12.7 for a in geometry["axes"]), 2571: sum(a["diameter_mm"] == 9.525 for a in geometry["axes"]),
                    2996: 2 * sum(a["hardware_scenario"]["washer_od_mm"] == 26.162 for a in geometry["axes"])}
        priced_total = D(0)
        for row in inventory["cost"]["conditional_reused_nominal_SKU_comparison_lines"]:
            sku, quantity = row["sku"], demanded[row["sku"]]
            if sku == 2996:
                unit, pack, size = D(washer_prices["each"]), D(washer_prices["bag_100"]), 100
            else:
                p = prices[sku]
                unit, pack, size = D(p["listed_each_usd"]), D(p["listed_pack_usd"]), p["pack_quantity"]
            choices = [(D(n) * pack + D(max(0, quantity - n * size)) * unit, n, max(0, quantity - n * size))
                       for n in range((quantity + size - 1) // size + 1)]
            cost, packs, singles = min(choices)
            require((quantity, packs, singles, cost) == (row["required"], row["packs"], row["singles"], D(row["cost_usd"])), f"price line {sku}")
            priced_total += cost
        require(priced_total == D("61.93") and inventory["cost"]["C4_usd"] is None, "price subset or C4")
        primary = json.loads((ROOT / "fea/generated/thin-bolted-b104-local-hardware-inputs/primary-dimensions.json").read_text())
        nut_catalog_max = D(primary["nut"]["height_in"][1]) * D("25.4")
        short_checks = []
        for row in inventory["thread_and_shank_obligations"]["four_8inch_comparisons"]:
            axis = next(a for a in geometry["axes"] if a["id"] == row["axis_id"])
            h = axis["hardware_scenario"]
            seat = D(axis["grip_mm"]) + D(axis["before_plate_mm"]) + D(axis["after_plate_mm"]) + 2 * D(h["washer_thickness_mm"])
            target = seat + D(h["nut_height_mm"]) + D("50.8") / D(h["threads_per_inch"])
            modeled_margin = D(row["source_shortest_comparison_underhead_mm"]) - target
            catalog_margin = D(row["source_shortest_comparison_underhead_mm"]) - seat - nut_catalog_max - D("50.8") / D(h["threads_per_inch"])
            require(abs(float(modeled_margin) - row["shortest_comparison_margin_against_current_modeled_stack_mm"]) < 1e-12, "modeled length margin")
            require(abs(float(catalog_margin) - row["separate_saved_product_tolerance_stack_margin_mm"]) < 1e-12, "catalog nut length margin")
            short_checks.append({"axis_id": axis["id"], "modeled_nut_height_mm": h["nut_height_mm"], "comparison_SKU2586_catalog_max_height_mm": str(nut_catalog_max),
                                 "minimum_modeled_underhead_mm": str(target), "shortest_modeled_margin_mm": str(modeled_margin), "separate_catalog_nut_margin_mm": str(catalog_margin)})
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, f"source changed after checks: {path}")
    return {"schema": "eoere_inventory_same_author_arithmetic_reconciliation/v1", "check_pass": True, "independent_author_review_or_admission": False,
            "reviewer_relation": "Same author as inventory.py; separately computed source/Decimal reconciliation only.",
            "inventory": {"path": str(inventory_path.relative_to(ROOT)), "sha256": INVENTORY_SHA}, "geometry": {"path": GEOMETRY, "sha256": GEOMETRY_SHA, "exact_tracked_mirror": MIRROR},
            "unchanged_source_pin_count": len(pins), "before_after_pin_map_sha256": [before, canonical(pins)],
            "four_changed_axis_ids": changed, "other96_axis_fields_and_all_grip_length_hardware_fields_unchanged": True,
            "saved_geometry_census": {"empty_collision_lists": 5, "fully_backed_bore_records": 120, "fully_backed_screw_records": 132},
            "separate_60_digit_arithmetic": {"max_role_volume_error_mm3": role_error, "total_mass_kg": str(total), "total_mass_error_kg": mass_error,
                                            "priced_comparison_subset_usd": str(priced_total), "four_8inch_length_checks": short_checks},
            "limits": "No actual CAD query, tolerance/grade/stock inspection, current load vector or force field. Same-author arithmetic is not independent source admission, geometry acceptance, purchase or capacity. Modeled nut11.5316mm and unselected catalog maximum11.3792mm remain separate bases; neither resolves delivered shank/root/runout/engagement.",
            "execution": {"sys_argv": list(sys.argv), "sys_orig_argv": list(sys.orig_argv), "PYTHONPATH": os.environ.get("PYTHONPATH"), "dependencies": "stdlib only; no inventory helper import"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve review receipt")
    result = evaluate()
    with options.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"path": str(options.out), "sha256": sha(options.out), "bytes": options.out.stat().st_size}))


if __name__ == "__main__":
    main()
