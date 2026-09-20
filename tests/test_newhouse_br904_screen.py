"""A named steel grade does not by itself qualify a retail wood joint."""

import json
from pathlib import Path


def test_br904_grade_and_hole_pattern_remain_a_prototype_lead():
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/newhouse-br904-retail.json").read_text()
    )
    assert record["product"]["model"] == "BR904"
    assert record["product"]["manufacturer_stated_steel"] == "4 gauge Q235 steel"
    assert record["product"]["factory_hole_diameter_in"] == 9 / 16
    assert record["product"]["nominal_hole_pitch_in"] == 1 + 7 / 8
    assert record["product_specific_minimum_yield_strength_verified"] is False
    assert record["complete_factory_hole_coordinates_verified"] is False
    assert record["wood_to_wood_capacity_established"] is False
    assert record["drilling_released"] is False


def test_no_contact_material_route_separates_standard_input_from_product_acceptance():
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/newhouse-br904-retail.json").read_text()
    )
    route = record["no_contact_evidence_route"]
    conditional = route["conditional_base_metal_properties"]
    assert route["manufacturer_contact_required"] is False
    assert conditional["standard"] == "GB/T 700-2006"
    assert conditional["thickness_range_mm"] == [0, 16]
    assert conditional["minimum_yield_mpa"] == 235
    assert conditional["minimum_tensile_mpa"] == 370
    assert conditional["adopted_for_br904"] is False
    assert route["sample_measured"] is False
    assert route["formed_angle_or_joint_capacity_established"] is False
