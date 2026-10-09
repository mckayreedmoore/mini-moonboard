"""Independent source-only review of the frozen nut-side spacer comparison."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import runpy
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "spacer-window-inputs-v1.json": "9326e6cfb8280760c47d00dace8967b84eecccbf813f5ea2e7dfb96841b49813",
    "spacer-window-v1.py": "59f429916ff26f897f5ace94fee610b0e420e261094e9f10659e937b44b0b3d6",
    "spacer-window-result-v1.json": "592c237e8f98456f936deaf3b8613f60c493008851e65f43a9fbde6300929896",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok):
    if not ok:
        raise AssertionError("independent comparison failed")


def close(actual, expected):
    need(not isinstance(actual, bool) and abs(D(str(actual)) - D(str(expected))) < D("1e-9"))


def validate(result, prior, inputs, pins):
    """Check saved fields with exact Decimal formulas, without producer helpers."""
    need(result["source_sha256"] == pins and result["source_pin_count"] == 34)
    need(result["status"] == "UNADOPTED_NOMINAL_DIMENSIONAL_FEASIBILITY")
    for key in ("current_revision", "current_100_axes_canonical_sha256", "current_66_screw_axes_canonical_sha256"):
        need(result[key] == prior[key])
    need(result["actual_observations"] == inputs["actual_observations"])
    need(all(v == "" for v in result["actual_observations"].values()))
    need(result["release"] == inputs["release"] and all(v is False for v in result["release"].values()))
    need(result["spacer_catalog_candidate"] == inputs["spacer"])
    need(inputs["spacer"]["length_tolerance_mm"] is None)
    need(inputs["spacer"]["diameter_tolerances_mm"] is None)
    need(inputs["spacer"]["numeric_yield_or_compression_capacity"] is None)
    need([r["axis_id"] for r in result["station_comparisons"]] == inputs["axis_ids"])
    need(len(result["station_comparisons"]) == 4)
    count = 0
    for row, old in zip(result["station_comparisons"], prior["four_stations"], strict=True):
        need(row["axis_id"] == old["axis_id"])
        for key in ("current_point_xyz_mm", "unadopted_proposed_point_xyz_mm"):
            need(row[key] == old[key])
        need(row["current_point_xyz_mm"][2] == 200 and row["unadopted_proposed_point_xyz_mm"][2] == 180)
        close(row["wood_stack_mm"], "76.2")
        # Frozen ASME box in mm: L=4.4..4.5in, w=.064...104in,
        # h=.320...337in, Lg=3.5in, Lb=3.19in, pitch=1/16in.
        wood, spacer, lg, lb = D("76.2"), D("12.7"), D("88.9"), D("81.026")
        lengths, washers, nuts = (D("111.76"), D("114.3")), (D("1.6256"), D("2.6416")), (D("8.128"), D("8.5598"))
        two_pitches = D("3.175")
        low = lg - wood - 2 * washers[0]
        high = lengths[0] - wood - 2 * washers[1] - nuts[1] - two_pitches
        need([D(str(x)) for x in row["derived_spacer_length_interval_mm"]] == [low, high])
        close(row["exact_nominal_spacer_length_mm"], spacer)
        window = row["nominal_dimension_window"]
        expected = {
            "underhead_length_bounds_mm": lengths,
            "washer_each_bounds_mm": washers,
            "nut_height_bounds_mm": nuts,
            "two_tip_pitches_mm": two_pitches,
            "required_length_at_max_catalog_stack_mm": wood + spacer + 2 * washers[1] + nuts[1] + two_pitches,
            "combined_washers_plus_nut_budget_at_shortest_length_mm": lengths[0] - wood - spacer - two_pitches,
            "equal_washer_ceiling_at_shortest_length_and_max_nut_mm": (lengths[0] - wood - spacer - two_pitches - nuts[1]) / 2,
            "tip_projection_bounds_mm": (lengths[0] - wood - spacer - 2 * washers[1] - nuts[1], lengths[1] - wood - spacer - 2 * washers[0] - nuts[0]),
            "nut_near_underhead_bounds_mm": (wood + spacer + 2 * washers[0], wood + spacer + 2 * washers[1]),
            "ASME_Lg_max_mm": lg,
            "ASME_Lb_min_mm": lb,
            "nut_near_minus_Lg_max_bounds_mm": (wood + spacer + 2 * washers[0] - lg, wood + spacer + 2 * washers[1] - lg),
            "catalog_min_length_max_stack_two_tip_margin_mm": high - spacer,
        }
        need(window.keys() == expected.keys())
        for key, value in expected.items():
            if isinstance(value, tuple):
                need(len(window[key]) == len(value))
                for actual, target in zip(window[key], value, strict=True):
                    close(actual, target)
            else:
                close(window[key], value)
        for length, wh, wn, nut, spacing in itertools.product(lengths, washers, washers, nuts, (low, high)):
            need(wood + wh + wn + spacing >= lg)
            need(length - wood - wh - wn - spacing - nut >= two_pitches)
            count += 1
        need(wood + 2 * washers[0] + low - D(".001") < lg)
        need(lengths[0] - wood - 2 * washers[1] - high - D(".001") - nuts[1] < two_pitches)
        body_margin = lb - wood - washers[1]
        need(body_margin > 0 and body_margin - spacer < 0)
        close(row["smooth_body_reserve_beyond_far_wood_mm"], body_margin)
        close(row["hypothetical_head_side_spacer_smooth_body_reserve_mm"], body_margin - spacer)
        close(row["max_socket_well_from_nut_near_face_mm"], lengths[1] - wood - 2 * washers[0] - spacer)
        close(row["conditional_36mm_socket_well_reserve_mm"], D(36) - lengths[1] + wood + 2 * washers[0] + spacer)
        close(row["headward_bolt_withdrawal_model_mm_unchanged"], "116.3")
        close(row["nut_only_withdrawal_model_mm"], "22.1168")
        close(row["nut_washer_withdrawal_model_mm_unchanged"], "36.8168")
        need(row["spacer_removal_continuous_clearance_verified"] is False)
    need(count == result["verification"]["independent_Decimal_endpoint_checks"] == 128)
    contact = result["nominal_contact_geometry"]
    for key, expected in {
        "spacer_ID_mm": "10.31875", "spacer_OD_mm": "19.05",
        "nominal_diametral_bolt_clearance_mm": "0.79375",
        "minimum_coaxial_spacer_washer_overlap_radial_width_mm": "3.7719",
        "minimum_coaxial_washer_outer_edge_reserve_mm": "3.0861",
    }.items():
        close(contact[key], expected)
    need(contact["full_spacer_end_face_supported_by_washer"] is False)
    need(contact["material_compression_washer_bending_eccentricity_or_joint_resistance_verified"] is False)
    for key, expected in {"four_spacers": "10.12", "four_longer_bolts_increment": ".52", "total": "10.64"}.items():
        close(result["dated_incremental_cost_before_shipping_tax_usd"][key], expected)
    need(result["dated_incremental_cost_before_shipping_tax_usd"]["current_hardware_basket_and_mass_unchanged"] is True)


def evaluate():
    for name, digest in TARGETS.items():
        need(sha(PACKET / name) == digest)
    inputs = json.loads((PACKET / "spacer-window-inputs-v1.json").read_bytes())
    saved = json.loads((PACKET / "spacer-window-result-v1.json").read_bytes())
    prior = json.loads((PACKET / "result-v3.json").read_bytes())
    pins = dict(prior["source_sha256"])
    need(prior["source_pin_count"] == len(pins) == 31)
    for name, digest in inputs["sources"].items():
        need(name not in pins or pins[name] == digest)
        pins[name] = digest
    for name in ("spacer-window-inputs-v1.json", "spacer-window-v1.py"):
        pins[str((PACKET / name).relative_to(ROOT))] = TARGETS[name]
    inventory = {**pins, str((PACKET / "spacer-window-result-v1.json").relative_to(ROOT)): TARGETS["spacer-window-result-v1.json"]}
    before = {name: sha(ROOT / name) for name in inventory}
    need(before == inventory)
    validate(saved, prior, inputs, pins)
    live = runpy.run_path(str(PACKET / "spacer-window-v1.py"))["evaluate"]()
    need(live == saved)
    mutations = [
        ("source_pin_count", 33),
        ("station_comparisons", "smooth_body_reserve_beyond_far_wood_mm", -10.5156),
        ("station_comparisons", "nut_washer_withdrawal_model_mm_unchanged", 24.1168),
        ("station_comparisons", "headward_bolt_withdrawal_model_mm_unchanged", 103.6),
        ("station_comparisons", "max_socket_well_from_nut_near_face_mm", 34.8488),
        ("station_comparisons", "spacer_removal_continuous_clearance_verified", True),
        ("nominal_contact_geometry", "full_spacer_end_face_supported_by_washer", True),
        ("release", "hardware_adoption", True),
        ("actual_observations", "spacer_dimensions", "observed"),
        ("dated_incremental_cost_before_shipping_tax_usd", "total", 11.36),
    ]
    for mutation in mutations:
        changed = copy.deepcopy(saved)
        if len(mutation) == 2:
            changed[mutation[0]] = mutation[1]
        elif mutation[0] == "station_comparisons":
            changed[mutation[0]][0][mutation[1]] = mutation[2]
        else:
            changed[mutation[0]][mutation[1]] = mutation[2]
        try:
            validate(changed, prior, inputs, pins)
        except AssertionError:
            continue
        raise AssertionError(f"mutation escaped: {mutation}")
    need({name: sha(ROOT / name) for name in inventory} == before)
    return {
        "schema": "independent_spacer_source_correctness_review/v1", "findings": [],
        "reviewer_source_sha256": sha(Path(__file__)), "reviewed_sha256": inventory,
        "checks": {"all_35_source_and_result_pins_before_after": True,
                   "old_31_plus_direct_and_self_union_exactly_34": True,
                   "one_in_memory_producer_evaluation_exact_saved_result": True,
                   "independent_Decimal_endpoint_comparisons": 128,
                   "independent_per_station_boundary_and_wrong_head_controls": 12,
                   "saved_field_mutations_rejected": len(mutations),
                   "nut_only_topology_bearing_tool_removal_cost_and_claims": True},
        "reused_primary_reading": "https://boltdepot.com/Product-Details?product=13731",
        "limits": ["Frozen nominal stack/uncoated ASME box and catalog nominal spacer only; delivered tolerances and material capacity unknown.",
                   "Prior source admissions and methods are reused within their bindings, without a new old-method or force audit.",
                   "No CLI output execution, native/CAD/BREP/frame/FEA/browser/physical work, hardware/geometry adoption or strength acceptance.",
                   "Current Z200/100-bolt/66-screw authority and actions remain unchanged; Z180 remains unadopted and Actual cells blank."],
    }


if __name__ == "__main__":
    receipt = evaluate()
    with (HERE / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"findings": receipt["findings"], "review_sha256": receipt["reviewer_source_sha256"],
                      "receipt_sha256": sha(HERE / "receipt.json")}))
