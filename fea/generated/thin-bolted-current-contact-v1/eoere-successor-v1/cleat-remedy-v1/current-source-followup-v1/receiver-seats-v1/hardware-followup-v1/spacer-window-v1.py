"""Compare one catalog nut-side spacer using the frozen hardware inequalities."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import runpy
from decimal import Decimal
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUT = HERE / "spacer-window-inputs-v1.json"
INPUT_SHA = "9326e6cfb8280760c47d00dace8967b84eecccbf813f5ea2e7dfb96841b49813"
D = Decimal
MM = D("25.4")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(pins):
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "source bytes changed")


def evaluate():
    require(sha(INPUT) == INPUT_SHA, "frozen spacer inputs changed")
    inputs = json.loads(INPUT.read_bytes())
    verify(inputs["sources"])
    prior = json.loads((HERE / "result-v3.json").read_bytes())
    pins = dict(prior["source_sha256"])
    for name, digest in inputs["sources"].items():
        require(name not in pins or pins[name] == digest, "contradictory source pin")
        pins[name] = digest
    pins[str(INPUT.relative_to(ROOT))] = INPUT_SHA
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    catalog_path = next(name for name in inputs["sources"] if name.endswith("/catalog-inputs.json"))
    helper_path = next(name for name in inputs["sources"] if name.endswith("/shop_windows.py"))
    catalog = json.loads((ROOT / catalog_path).read_bytes())
    helper = runpy.run_path(str(ROOT / helper_path))
    bolt = next(b for b in catalog["bolts"] if b["sku"] == inputs["bolt_sku"])
    old_bolt = next(b for b in catalog["bolts"] if b["sku"] == inputs["replaced_bolt_sku"])
    diameter = next(d for d in catalog["diameters"] if d["diameter_in"] == bolt["diameter_in"])
    spacer = inputs["spacer"]
    nominal = D(str(spacer["length_in"])) * MM
    spacer_id = D(str(spacer["ID_in"])) * MM
    spacer_od = D(str(spacer["OD_in"])) * MM
    length_max = D(str(bolt["nominal_length_in"])) * MM
    length_min = length_max - D(str(bolt["length_tolerance_minus_in"])) * MM
    washer = tuple(D(str(v)) * MM for v in diameter["washer"]["thickness_bounds_in"])
    nut = tuple(D(str(v)) * MM for v in diameter["nut"]["height_bounds_in"])
    pitch = MM / D(str(diameter["threads_per_inch"]))
    grip_max = D(str(bolt["Lg_max_in"])) * MM
    body_min = D(str(bolt["Lb_min_in"])) * MM
    require([row["axis_id"] for row in prior["four_stations"]] == inputs["axis_ids"], "four-axis join changed")
    rows = []
    max_error = 0.0
    for row in prior["four_stations"]:
        wood = D(str(row["matched_wood_travel_mm"]))
        old = next(c for c in row["comparisons"] if c["sku"] == bolt["sku"])
        require(helper["bounds_for"](float(wood), bolt, diameter) == old["window"], "old dimension replay changed")
        low = grip_max - wood - 2 * washer[0]
        high = length_min - wood - 2 * washer[1] - nut[1] - 2 * pitch
        require(low <= nominal <= high, "nominal spacer outside derived dimensional window")
        for length, wh, wn, nh, spacing in itertools.product(
            (length_min, length_max), washer, washer, nut, (low, high)
        ):
            expected_near = wood + wh + wn + spacing
            expected_tip = length - expected_near - nh
            expected = {
                "tip_projection_beyond_nut_mm": expected_tip,
                "two_pitch_margin_mm": expected_tip - 2 * pitch,
                "nut_near_underhead_mm": expected_near,
                "nut_near_minus_gaged_grip_mm": expected_near - grip_max,
            }
            require(expected["two_pitch_margin_mm"] >= 0
                    and expected["nut_near_minus_gaged_grip_mm"] >= 0, "Decimal endpoint outside window")
            actual = helper["measured_window"](
                underhead_length_mm=float(length), receiver_and_plate_mm=float(wood + spacing),
                head_washer_mm=float(wh), nut_washer_mm=float(wn), nut_height_mm=float(nh),
                pitch_mm=float(pitch), gaged_grip_mm=float(grip_max),
            )
            max_error = max(max_error, *(abs(actual[k] - float(v)) for k, v in expected.items()))
        require(max_error < 1e-9, "shared floating-point helper differs from independent Decimal arithmetic")
        body_margin = body_min - wood - washer[1]
        require(abs(float(body_margin) - old["minimum_body_minus_model_farthest_bearing_mm"]) < 1e-9,
                "wood bearing target changed")
        require(grip_max - wood - 2 * washer[0] - (low - D("0.001")) > 0,
                "below-window seating negative control failed")
        require(length_min - wood - 2 * washer[1] - nut[1] - 2 * pitch - (high + D("0.001")) < 0,
                "above-window projection negative control failed")
        require(body_margin > 0 and body_margin - nominal < 0, "nut/head-side distinction changed")
        window = helper["bounds_for"](float(wood + nominal), bolt, diameter)
        rows.append({
            "axis_id": row["axis_id"], "wood_stack_mm": float(wood),
            "current_point_xyz_mm": row["current_point_xyz_mm"],
            "unadopted_proposed_point_xyz_mm": row["unadopted_proposed_point_xyz_mm"],
            "derived_spacer_length_interval_mm": [float(low), float(high)],
            "exact_nominal_spacer_length_mm": float(nominal), "nominal_dimension_window": window,
            "smooth_body_reserve_beyond_far_wood_mm": float(body_margin),
            "hypothetical_head_side_spacer_smooth_body_reserve_mm": float(body_margin - nominal),
            "max_socket_well_from_nut_near_face_mm": float(length_max - wood - 2 * washer[0] - nominal),
            "conditional_36mm_socket_well_reserve_mm": float(
                D(str(inputs["conditional_clear_socket_well_mm"])) - length_max + wood + 2 * washer[0] + nominal
            ),
            "headward_bolt_withdrawal_model_mm_unchanged": old["saved_method_bolt_headward_travel_mm"],
            "nut_only_withdrawal_model_mm": old["saved_method_nut_nutward_travel_model_mm"] - float(nominal),
            "nut_washer_withdrawal_model_mm_unchanged": old["saved_method_nut_washer_nutward_travel_model_mm"],
            "spacer_removal_continuous_clearance_verified": False,
        })
    washer_id_max = D(str(diameter["washer"]["ID_bounds_in"][1])) * MM
    washer_od_min = D(str(diameter["washer"]["OD_bounds_in"][0])) * MM
    count = len(rows)
    result = {
        "schema": "eoere_four_cleat_post_under_nut_spacer_comparison/v1",
        "status": "UNADOPTED_NOMINAL_DIMENSIONAL_FEASIBILITY",
        "source_pin_count": len(pins), "source_sha256": pins,
        "current_revision": prior["current_revision"],
        "current_100_axes_canonical_sha256": prior["current_100_axes_canonical_sha256"],
        "current_66_screw_axes_canonical_sha256": prior["current_66_screw_axes_canonical_sha256"],
        "station_comparisons": rows,
        "spacer_catalog_candidate": spacer,
        "nominal_contact_geometry": {
            "spacer_ID_mm": float(spacer_id), "spacer_OD_mm": float(spacer_od),
            "nominal_diametral_bolt_clearance_mm": float(spacer_id - D(str(bolt["diameter_in"])) * MM),
            "minimum_coaxial_spacer_washer_overlap_radial_width_mm": float((spacer_od - washer_id_max) / 2),
            "minimum_coaxial_washer_outer_edge_reserve_mm": float((washer_od_min - spacer_od) / 2),
            "full_spacer_end_face_supported_by_washer": False,
            "material_compression_washer_bending_eccentricity_or_joint_resistance_verified": False,
        },
        "dated_incremental_cost_before_shipping_tax_usd": {
            "four_spacers": float(D(str(spacer["unit_price_usd"])) * count),
            "four_longer_bolts_increment": float((D(str(bolt["unit_price_usd"])) - D(str(old_bolt["unit_price_usd"]))) * count),
            "total": float((D(str(spacer["unit_price_usd"])) + D(str(bolt["unit_price_usd"]))
                            - D(str(old_bolt["unit_price_usd"]))) * count),
            "current_hardware_basket_and_mass_unchanged": True,
        },
        "verification": {
            "frozen_dimension_windows_exactly_replayed": count,
            "independent_Decimal_endpoint_checks": 32 * count,
            "maximum_shared_helper_Decimal_difference_mm": max_error,
            "per_station_negative_controls": ["spacer_0.001mm_below_seating_boundary",
                                              "spacer_0.001mm_above_projection_boundary",
                                              "same_spacer_wrongly_placed_under_head"],
            "all_source_bytes_unchanged_before_after": True,
        },
        "receiving_and_removal_limits": [
            "The derived spacer interval applies to the frozen nominal wood stack and catalog box, not unknown delivered dimensions. The listing publishes no spacer tolerance.",
            "Use actual L >= S + w_head + w_nut + s + h + 2*p; gaged grip <= S + w_head + w_nut + s; smooth body >= w_head + S. Actual rows remain blank.",
            "Positive actual bore clearance, end flatness/squareness, concentricity, free nut seating, active threads, fillet/washer/wood seating and material resistance remain needed.",
            "Assemble wood, existing nut washer, one spacer, then nut. A head-side spacer would consume the smooth body reserve and is not this scenario.",
            "The bolt tip and headward withdrawal are unchanged from the bare 4.5-inch comparison. Nut-only travel decreases; nut-washer travel does not. Spacer removal needs its own continuous path.",
            "For delivered spacer bounds, worst clear socket well is the old 34.8488-mm catalog bound minus s_min. Hex depth alone does not establish socket well or drive clearance.",
            "Only a coaxial overlapping annulus is described. No full spacer-face support, washer bending, spacer compression, preload or changed-demand acceptance follows.",
        ],
        "limits": inputs["limits"], "actual_observations": inputs["actual_observations"],
        "release": inputs["release"],
    }
    require(all(v is False for v in result["release"].values())
            and all(v == "" for v in result["actual_observations"].values()), "claim boundary changed")
    verify(pins)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "owned JSON output required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "fresh output required")
    result = evaluate()
    with destination.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination),
                      "bytes": destination.stat().st_size, "source_pin_count": result["source_pin_count"]}))


if __name__ == "__main__":
    main()
