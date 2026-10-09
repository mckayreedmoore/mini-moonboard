"""Source-bound catalog/intake inequalities only; no field-vector consumption."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CATALOG = HERE.parent
BASE = CATALOG.parent
PRIOR_SHA = "6d14fbd84ed32757afde7930f559aeeaf90e98259dbb634537ffa7a201b04c71"
INPUT_SHA = "94d7c3aea8588ed2a2dafea9ef168e9596b941c1b6723f883ab4b6a655f6a008"
DIRECT = {
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf":
        "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf":
        "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/source-bounds.json":
        "91c8c0c33cb7cc35dc31ba332778a80e1c5a972a6134e5e277a473a2adf719c9",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt06-tr12-2026-independent-review-2026-09-28/source-access-check.md":
        "62de65dcb429427d8dcedd02b774a7d27d4902e724c5041e1834f672e3193138",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def number(value, label, *, positive=False):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), f"invalid {label}")
    require(value > 0 if positive else value >= 0, f"negative/nonpositive {label}")
    return float(value)


def measured_window(*, underhead_length_mm, receiver_and_plate_mm, head_washer_mm,
                    nut_washer_mm, nut_height_mm, pitch_mm, gaged_grip_mm):
    """Dimensional checks, without claiming actual conformance or strength."""
    length = number(underhead_length_mm, "length", positive=True)
    stack = number(receiver_and_plate_mm, "receiver stack", positive=True)
    wh = number(head_washer_mm, "head washer", positive=True)
    wn = number(nut_washer_mm, "nut washer", positive=True)
    nut = number(nut_height_mm, "nut", positive=True)
    pitch = number(pitch_mm, "pitch", positive=True)
    grip = number(gaged_grip_mm, "gaged grip")
    nut_near = stack + wh + wn
    tip = length - nut_near - nut
    return {
        "tip_projection_beyond_nut_mm": tip,
        "two_pitch_margin_mm": tip - 2 * pitch,
        "nut_near_underhead_mm": nut_near,
        "nut_near_minus_gaged_grip_mm": nut_near - grip,
        "two_tip_pitch_condition": tip >= 2 * pitch,
        "conservative_gaged_grip_condition": grip <= nut_near,
        "delivered_fit_or_strength_acceptance": False,
    }


def bounds_for(stack, bolt, diameter):
    """Extrema over the declared independent catalog dimension box."""
    length = number(bolt["nominal_length_in"], "catalog length", positive=True) * 25.4
    shortest = length - number(bolt["length_tolerance_minus_in"], "length tolerance") * 25.4
    wh_min, wh_max = [number(v, "washer bound", positive=True) * 25.4
                      for v in diameter["washer"]["thickness_bounds_in"]]
    n_min, n_max = [number(v, "nut bound", positive=True) * 25.4
                    for v in diameter["nut"]["height_bounds_in"]]
    require(wh_min <= wh_max and n_min <= n_max, "reversed catalog bounds")
    pitch = 25.4 / number(diameter["threads_per_inch"], "thread count", positive=True)
    lg = number(bolt["Lg_max_in"], "Lg") * 25.4
    return {
        "underhead_length_bounds_mm": [shortest, length],
        "washer_each_bounds_mm": [wh_min, wh_max],
        "nut_height_bounds_mm": [n_min, n_max],
        "two_tip_pitches_mm": 2 * pitch,
        "required_length_at_max_catalog_stack_mm": stack + 2 * wh_max + n_max + 2 * pitch,
        "combined_washers_plus_nut_budget_at_shortest_length_mm": shortest - stack - 2 * pitch,
        "equal_washer_ceiling_at_shortest_length_and_max_nut_mm":
            (shortest - stack - 2 * pitch - n_max) / 2,
        "tip_projection_bounds_mm": [shortest - stack - 2 * wh_max - n_max,
                                      length - stack - 2 * wh_min - n_min],
        "nut_near_underhead_bounds_mm": [stack + 2 * wh_min, stack + 2 * wh_max],
        "ASME_Lg_max_mm": lg,
        "ASME_Lb_min_mm": number(bolt["Lb_min_in"], "Lb") * 25.4,
        "nut_near_minus_Lg_max_bounds_mm": [stack + 2 * wh_min - lg, stack + 2 * wh_max - lg],
        "catalog_min_length_max_stack_two_tip_margin_mm":
            shortest - stack - 2 * wh_max - n_max - 2 * pitch,
    }


def merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "contradictory source pin")
        pins[path] = digest


def verify(pins):
    observed = {path: sha(ROOT / path) for path in pins}
    require(observed == pins, "source bytes changed")
    return observed


def intake():
    prior_path = CATALOG / "complete-result.json"
    require(sha(prior_path) == PRIOR_SHA and sha(HERE / "input.json") == INPUT_SHA,
            "issued catalog result or new inputs changed")
    prior = json.loads(prior_path.read_text())
    pins = dict(prior["source_sha256"])
    require(len(pins) == prior["source_pin_count"] == 400
            and prior["source_pins_before_after_unchanged"] is True,
            "prior complete-source map changed")
    prior_map_digest = canonical(pins)
    # Hash all400 pinned source bytes before using geometry/stack metadata.
    verify(pins)
    direct = dict(DIRECT)
    for path in (prior_path, CATALOG / "independent-review-v1/independent-review.json",
                 HERE / "input.json", Path(__file__), HERE / "test_shop_windows.py"):
        direct[str(path.relative_to(ROOT))] = sha(path)
    merge(pins, direct)
    before = verify(pins)
    facts = json.loads((CATALOG / "catalog-inputs.json").read_text())
    geometry = json.loads((BASE / "occupied-geometry-v2-complete/geometry.json").read_text())
    inputs = json.loads((HERE / "input.json").read_text())
    require(inputs["bending_yield_source_check"]["named_Grade5_published_minimum_Fyb_psi"] is None,
            "invented Grade5 Fyb minimum")
    return prior, facts, geometry, inputs, direct, pins, before, prior_map_digest


def report():
    prior, facts, geometry, inputs, direct, pins, before, old_digest = intake()
    bolts = {row["sku"]: row for row in facts["bolts"]}
    diameters = {row["diameter_in"]: row for row in facts["diameters"]}
    axes = {row["id"]: row for row in geometry["axes"]}
    require(len(axes) == 100, "current axis count changed")
    alternatives = {row["old_sku"]: row for row in inputs["next_listed_products"]}
    groups = [row for row in prior["stock_stack_groups"]
              if row["shortest_vs_catalog_max_stack_margin_mm"] < 0]
    require([row["quantity"] for row in groups] == [16, 4, 4], "flagged stack census changed")
    rows, all_ids, extra_cost = [], [], 0.0
    for group in groups:
        ids = group["axis_ids"]
        require(len(ids) == group["quantity"] and len(set(ids)) == len(ids), "duplicate/missing own axis")
        all_ids.extend(ids)
        own = [axes[axis] for axis in ids]
        stack_values = [row["grip_mm"] + row["before_plate_mm"] + row["after_plate_mm"] for row in own]
        require(max(stack_values) - min(stack_values) < 1e-8, "mixed receiving stack group")
        # Original metadata retains its floating roundoff; declared nominal stack is a shop scenario.
        stack = round(stack_values[0], 8)
        old = bolts[group["bolt_sku"]]
        new = alternatives[group["bolt_sku"]]
        require(old["diameter_in"] == new["diameter_in"]
                and all(abs(row["diameter_mm"] - old["diameter_in"] * 25.4) < 1e-10
                        and abs(row["nominal_under_head_length_mm"] - old["nominal_length_in"] * 25.4) < 1e-10
                        for row in own), "wrong own diameter/length join")
        diameter = diameters[old["diameter_in"]]
        existing = bounds_for(stack, old, diameter)
        next_stock = bounds_for(stack, new, diameter)
        require(abs(existing["catalog_min_length_max_stack_two_tip_margin_mm"]
                    - group["shortest_vs_catalog_max_stack_margin_mm"]) < 1e-8,
                "issued shortfall replay differs")
        delta = (new["nominal_length_in"] - old["nominal_length_in"]) * 25.4
        cost = round(group["quantity"] * (new["unit_price_usd"] - old["unit_price_usd"]), 2)
        extra_cost += cost
        proof = []
        for row in own:
            proof.append({"axis_id": row["id"], "receivers": row["receivers"],
                          "point_xyz_mm": row["point_xyz_mm"], "outward_nut_direction_xyz": row["direction_xyz"],
                          "receiver_grip_mm": row["grip_mm"], "before_plate_mm": row["before_plate_mm"],
                          "after_plate_mm": row["after_plate_mm"],
                          "same_head_washer_next_nominal_tip_shift_xyz_mm":
                              [delta * value for value in row["direction_xyz"]]})
        rows.append({
            "axis_ids": ids, "quantity": len(ids), "existing_sku": old["sku"], "next_sku": new["sku"],
            "receiver_and_plate_nominal_stack_mm": stack, "existing_length": existing,
            "next_listed_length": next_stock, "next_nominal_outward_tip_increment_mm": delta,
            "next_length_incremental_unit_purchase_cost_usd": cost,
            "next_length_worst_grip_exceeds_max_catalog_nut_near_mm":
                max(0, -next_stock["nut_near_minus_Lg_max_bounds_mm"][1]),
            "own_axis_source_metadata": proof,
            "choice": "Existing length with measured joint-stack inequality preferred as a proposal; no SKU/thinner washer/longer bolt selected or actual fit accepted.",
            "next_length_seating_guaranteed_by_catalog_bounds": False,
            "actual_tool_tip_or_withdrawal_clearance_verified": False,
        })
    require(len(all_ids) == len(set(all_ids)) == 24, "flagged axis coverage differs")
    after = verify(pins)
    require(before == after, "source changed during pure arithmetic")
    return {
        "schema": "eoere_same_catalog_shop_window_proposal/v1", "status": "SOURCE_BOUND_DIMENSIONAL_PROPOSAL",
        "state_id_for_prior_catalog_reuse_only": prior["state_id"],
        "direct_source_sha256": direct,
        "verified_referenced_source_map": {"path": str((CATALOG / "complete-result.json").relative_to(ROOT)),
                                           "raw_sha256": PRIOR_SHA, "source_map_key": "source_sha256",
                                           "pin_count": 400, "canonical_sha256": old_digest},
        "complete_union_pin_count": len(pins), "complete_union_canonical_sha256": canonical(pins),
        "all_source_pins_verified_before_after": True,
        "source_check": inputs["bending_yield_source_check"],
        "NDS_product_specific_Grade5_Fyb_psi": None,
        "documented_generic_comparison_Fyb_psi": 45000,
        "generic_Fyb_is_a_product_minimum_or_adopted_joint_strength": False,
        "shop_purchase_and_receiving_proposal": inputs["shop_proposal"],
        "flagged_own_stack_count": 24, "three_eighth_count": 20, "half_inch_count": 4,
        "stack_groups": rows,
        "price_scenario": {"prior_catalog_hardware_total_usd": prior["purchase_cost_scenario"]["total_usd"],
                           "all24_next_lengths_increment_usd": round(extra_cost, 2),
                           "all24_next_lengths_hardware_total_usd":
                               round(prior["purchase_cost_scenario"]["total_usd"] + extra_cost, 2),
                           "limit": "Current observed merchant prices and prior same-family basket only, before tax/shipping; no availability, quote, purchase, supplier sorting charge or part qualification. Next-length groups use individuals, cheaper than buying their listed bags for these counts."},
        "bounded_constraints": [
            "Actual receiver/plate thickness S belongs in each intake equation; nominal S is not an observed cut/stack.",
            "Minimum2-tip pitch is a retained project geometry scenario; nut thread class/entry chamfer and free full seating need actual part compatibility.",
            "Original100shaft/200capture field and prior washer bending/seat/couple limits remain unchanged. Thinner in-range washer selection would be a new local scenario requiring its applicable strength/seat treatment.",
            "Half-inch washer minimum opening0.547in vs cap fillet maximum0.550in leaves a0.0762mm diametral corner; actual fillet/chamfer/washer seating remains unresolved.",
            "No additional packing washers, preload, friction, force removal, bolt trimming, blanket longer selection or manufactured custom part is credited.",
            "Outward tip and tool/removal clearance beyond the old nominal envelope is not proven by pure length arithmetic. Axial protrusion bounds are recorded, with9/16 and3/4in reference wrench sizes only.",
            "Full-body/source finish definition, thread bearing/root regions and NDS member-specific diameter exception remain separate purchase/method inputs; longer body may relocate thread-bearing regions without yielding a complete resistance pass.",
        ],
        "release": {"candidate_response_force_vector_or_q_consumed": False, "CAD_native_or_K_run": False,
                    "geometry_or_issued_packet_modified": False, "part_or_capacity_or_build_acceptance": False},
        "execution": {"argv": sys.orig_argv, "python_version": platform.python_version()},
        "reproduction_command": "uv run python -m fea.generated.thin-bolted-current-contact-v1.eoere-successor-v1.catalog-hardware-strength-v1.shop-window-v1.shop_windows --out /tmp/eoere-shop-window-replay.json",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = report()
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "source_pins": result["complete_union_pin_count"]}))


if __name__ == "__main__":
    main()
