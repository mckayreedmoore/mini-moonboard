"""Pure source-bound catalog conversions; no candidate geometry or response."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from decimal import Decimal
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT, LEAF = OWN.parents[6], OWN.parent
INPUT_SHA = "132c8838065e4d7ec7a321d807a940074b02079e611c926033e1362b48cee961"
INCH_MM = Decimal("25.4")
POUND_KG = Decimal("0.45359237")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    return Decimal(str(value))


def inches(value):
    return number(value) * INCH_MM


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        assert sha(ROOT / path) == digest, path


def worksheet():
    input_path = LEAF / "product-source-inputs.json"
    assert sha(input_path) == INPUT_SHA
    source = json.loads(input_path.read_bytes())
    pins = dict(source["context_source_pins"])
    pins[str(input_path.relative_to(ROOT))] = INPUT_SHA
    drawing = source["primary_sources"]["drawing"]
    pins[str((LEAF / drawing["local_path"]).relative_to(ROOT))] = drawing["raw_sha256"]
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    assert (LEAF / drawing["local_path"]).stat().st_size == drawing["bytes"] == 79096
    before = canonical(pins)
    claims = source["catalog_claims"]
    owner = source["owner_installation_policy"]
    drawing_values = {key: float(inches(value)) for key, value in claims["drawing_dimensions_inches"].items()}
    bolt_d = inches(claims["bolt_nominal_diameter_inches"])
    metric_hole = number(claims["description_metric_dimensions_mm"]["hole_diameter"])
    literal_hole = inches(claims["literal_hole_diameter_inches_in_description"])
    assert claims["all_hole_count"] == 8 and owner["installed_bolts_per_angle"] == 4
    assert len(set(source["complete_hole_coordinate_contract"]["hole_ids"])) == 8
    holes = [{"id": name, "installed_far_pair": "-far-" in name,
              "local_transverse_coordinate_mm": None, "local_heel_axial_coordinate_mm": None,
              "through_diameter_nominal_alternatives_mm": [float(metric_hole), float(literal_hole)],
              "retained_even_when_unused": True} for name in source["complete_hole_coordinate_contract"]["hole_ids"]]
    assert sum(row["installed_far_pair"] for row in holes) == 4
    dimensions = [
        {"scenario": "drawing inch nominal", "arms_mm": [drawing_values["arm_A"], drawing_values["arm_B"]],
         "breadth_mm": drawing_values["width"], "thickness_mm": drawing_values["thickness"], "delivered_minimum_or_maximum": False},
        {"scenario": "description metric nominal", "arms_mm": [90., 90.], "breadth_mm": 90., "thickness_mm": 6.,
         "breadth_and_both_arms_mapping_from_size_is_inferred": True, "delivered_minimum_or_maximum": False},
        {"scenario": "existing peer hybrid larger-nominal gross envelope only", "arms_mm": [90., 90.], "breadth_mm": 90.,
         "thickness_mm": 6.35, "product_dimension_tuple_or_strength_minimum": False, "fit_transfer": False},
    ]
    washer = source["primary_sources"]["washer_comparison"]
    washer_mm = {key: {bound: float(inches(value)) for bound, value in washer[key].items()}
                 for key in ("outer_diameter_inches", "inner_diameter_inches", "thickness_inches")}
    od_max = inches(washer["outer_diameter_inches"]["maximum"])
    od_nom = inches(washer["outer_diameter_inches"]["nominal"])
    id_min = inches(washer["inner_diameter_inches"]["minimum"])
    transverse_pitch = inches(claims["drawing_dimensions_inches"]["transverse_hole_pitch"])
    axial_pitch = inches(claims["drawing_dimensions_inches"]["axial_hole_row_pitch"])
    centered = []
    for breadth in (inches(3.5), Decimal(90)):
        edge = (breadth - transverse_pitch) / 2
        centered.append({"breadth_mm": float(breadth), "hypothesis": "transverse pair exactly centered; centering is not dimensioned",
            "centers_from_side_edge_mm": [float(edge), float(breadth - edge)],
            "nominal_washer_to_side_edge_mm": float(edge - od_nom / 2),
            "maximum_catalog_OD_washer_to_side_edge_mm": float(edge - od_max / 2),
            "actual_receiver_support_or_installed_seat_proof": False})
    mass_claims = []
    for claim in claims["weight_claims"]:
        mass = number(claim["kilograms"]) if "kilograms" in claim else number(claim["pounds"]) * POUND_KG
        each = mass / claim["pieces"]
        mass_claims.append({"source": claim["source"], "claim_normalized_kg_per_piece": float(each),
                            "received_net_piece_weight_verified": False})
    quantities = []
    for n, label in ((16, "Owner's main-back subset only"),
                     (24, "Sixteen main plus eight starting lower/header stations; final new blocks/poses/count unresolved")):
        packs = (n + 3) // 4
        quantities.append({"angle_count_scenario": n, "role": label, "final_candidate_quantity": False,
            "four_packs": packs, "purchased_angle_pieces": 4 * packs, "unused_pack_pieces": 4 * packs - n,
            "all_factory_holes": 8 * n, "installed_angle_hole_attachments_before_coincidences": 4 * n,
            "unused_factory_holes_retained": 4 * n, "unique_physical_bolt_count": None,
            "angle_cost_formula_usd": f"{packs}*C4 + shipping + tax", "angle_cost_usd": None,
            "catalog_mass_scenarios_kg": [{"source": claim["source"], "mass_kg": float(number(claim["claim_normalized_kg_per_piece"]) * n)} for claim in mass_claims]})
    # Simple fact/conversion witnesses; no delivered-fit or resistance test.
    assert bolt_d == Decimal("9.5250") and metric_hole - bolt_d == Decimal("0.4750")
    assert literal_hole - bolt_d == 0 and transverse_pitch == Decimal("50.80") and axial_pitch == Decimal("41.2750")
    assert sum(row["installed_far_pair"] for row in holes) + sum(not row["installed_far_pair"] for row in holes) == 8
    verify(pins)
    return {
        "schema": "eoere_successor_conditional_product_and_interface_worksheet/v1",
        "source_sha256": pins, "source_manifest_before_after_sha256": [before, canonical(pins)], "all_pinned_bytes_unchanged": True,
        "command_argv": list(sys.orig_argv), "tools": {"python": platform.python_version(), "arithmetic": "Decimal exact decimal unit conversions; ordinary float serialization only"},
        "primary_listing_url": source["primary_sources"]["listing"]["url"], "primary_drawing_url": drawing["url"],
        "unit_constants": {"mm_per_inch_exact": str(INCH_MM), "kg_per_pound_exact": str(POUND_KG)},
        "drawing_dimension_conversions_mm": drawing_values,
        "item_dimension_3_point_54_inches_mm": float(inches(claims["item_dimension_each_axis_inches"])),
        "separate_nominal_dimension_scenarios": dimensions,
        "all_eight_hole_records": holes,
        "bolt_and_factory_hole_nominal_clearance": {
            "nominal_bolt_shank_mm": float(bolt_d), "literal_inch_hole_mm": float(literal_hole), "listed_metric_hole_mm": float(metric_hole),
            "literal_inch_nominal_diametral_clearance_mm": float(literal_hole - bolt_d),
            "metric_nominal_diametral_clearance_mm": float(metric_hole - bolt_d),
            "metric_nominal_radial_clearance_mm": float((metric_hole - bolt_d) / 2),
            "delivered_shank_hole_tolerances_or_coating_clearance_verified": False,
            "factory_hole_diameter_is_wood_drill_bit_instruction": False},
        "nonselected_washer_comparison": {
            "primary_seller_SKU": washer["sku"], "url": washer["url"], "published_dimensions_mm": washer_mm,
            "minimum_catalog_ID_minus_nominal_bolt_diametral_mm": float(id_min - bolt_d),
            "transverse_pitch_minus_maximum_catalog_OD_mm": float(transverse_pitch - od_max),
            "axial_row_pitch_minus_washer_radius_and_unused_hole_radius_mm": float(axial_pitch - od_max / 2 - metric_hole / 2),
            "conditional_centered_transverse_footprint": centered,
            "actual_heel_or_longitudinal_end_washer_clearance_mm": None,
            "conditional_heel_end_requirements": ["a_far-r_washer exceeds the measured bend/heel flat-seat exclusion", "L-a_far exceeds r_washer on the actual outer datum"],
            "actual_own_steel_and_wood_annular_pressure_planes_support_and_material_resistance": None,
            "delivered_washer_bolt_tolerance_or_capacity_verified": False,
            "catalog_price_comparison_only_usd": washer["displayed_comparison_prices_usd"]},
        "catalog_mass_claim_normalizations": mass_claims,
        "angle_quantity_cost_and_mass_scenarios": quantities,
        "general_count_and_cost_contract": {
            "angle_count": "N=16+n_other; n_other follows parent-owned block/cleat geometry and final station selection",
            "pack_count": "ceil(N/4)", "angle_cost": "ceil(N/4)*C4 + shipping + tax; C4 remains unknown",
            "angle_mass": "N*m_angle, with m_angle a declared catalog-mass scenario or later measured net mass",
            "installed_hole_attachment_count": "4*N; unique physical shafts and shared holes must be resolved separately",
            "nonshared_two_washer_per_bolt_quantity_scenario": "8*N; neither SKU nor physical count adopted",
            "complete_hardware_cost": "angle packs + sum(actual bolt/nut/washer SKU quantities*quoted unit costs) + block stock + shipping + tax",
            "complete_candidate_cost_mass_physical_bolt_count_or_assembly_sequence": None},
        "required_new_bolt_stack_contract": {
            "grip_i": "measured angle thickness + actual timber path lengths + each own washer thickness + actual gaps/other plates",
            "unthreaded_shank": "Must bind every shear/bearing-plane interval to actual delivered shank/thread transition; nominal bolt length is insufficient",
            "nut_engagement_and_tip_access": "Actual head/nut product geometry, full nut thread engagement and installed/protruding tip clearance remain inputs",
            "wood_holes_and_edge_end_grain_distances": "New actual receiver geometry and adopted wood-hole policy required; no catalog/CAD diameter converted into a drill instruction"},
        "material_properties_verified_or_selected": {"Fy_MPa": None, "Fu_MPa": None, "E_MPa": None, "Poisson_ratio": None,
                                                     "density_kg_m3": None, "finished_part_minimum_thickness_mm": None},
        "seller_300_lbf_scalar_transferred_to_joint_capacity": False,
        "precise_remaining_dependencies": source["missing_product_inputs"],
        "compatible_replacement_and_complete_joint_requirements": source["replacement_requirements"],
        "CAD_geometry_source_fit_old_force_or_capacity_transfer": False,
        "release": source["release"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = (json.dumps(worksheet(), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"out": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
