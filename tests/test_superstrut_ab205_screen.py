"""AB205 is a dimensioned retail lead, not a wood-joint rating."""

import json
from pathlib import Path

import pytest


def test_ab205_retail_candidate_keeps_geometry_and_rating_separate():
    record = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/superstrut-ab205-retail.json"
        ).read_text()
    )
    product = record["product"]
    screen = record["nominal_wood_geometry_screen"]
    diameter = product["manufacturer_standard_bolt_diameter_in"]
    assert product["model"] == "ZAB205EG-10 / AB205-EG"
    assert product["factory_hole_diameter_in"] == pytest.approx(diameter + 1 / 16)
    assert product["manufacturer_hole_pitch_in"] == pytest.approx(1.875)
    assert screen["wide_face_best_case_4d_edge_reserve_in"] == pytest.approx(
        5.5 / 2 - 4 * diameter
    )
    assert screen["narrow_face_best_case_4d_edge_reserve_in"] == pytest.approx(
        1.5 / 2 - 4 * diameter
    )
    assert record["manufacturer_channel_rating"]["value_lb"] == 2000
    assert "A1200" in record["manufacturer_channel_rating"]["scope"]
    assert "steel-to-wood" in record["wood_method_boundary"]
    assert "exact grade" in product["material_description"]
    assert record["abb_channel_test_rating_transferable_to_wood"] is False
    assert record["wood_to_wood_capacity_established"] is False
    assert record["factory_drill_coordinates_released"] is False
    assert record["drilling_released"] is False
