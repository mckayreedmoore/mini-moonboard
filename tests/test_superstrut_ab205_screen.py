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
    assert "wood-to-steel single-shear helper" in record["wood_method_boundary"]
    assert "requires supplied steel bearing" in record["wood_method_boundary"]
    assert "does not supply AB205 steel properties" in record["wood_method_boundary"]
    assert "exact grade" in product["material_description"]
    assert record["abb_channel_test_rating_transferable_to_wood"] is False
    assert record["wood_to_wood_capacity_established"] is False
    assert record["factory_drill_coordinates_released"] is False
    assert record["drilling_released"] is False


@pytest.mark.parametrize(
    "leg,expected_nearest,expected_minimum_shift,expected_full_shift",
    [
        ("short_3p5", 0.8125, 0.9375, 2.6875),
        ("long_4p125", 1.4375, 0.3125, 2.0625),
    ],
)
def test_flush_bend_softwood_end_distance_is_only_a_conditional_failure(
    leg, expected_nearest, expected_minimum_shift, expected_full_shift
):
    record = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/superstrut-ab205-retail.json"
        ).read_text()
    )
    screen = record["flush_bend_wood_end_screen"]
    diameter = record["product"]["manufacturer_standard_bolt_diameter_in"]
    flange = screen["flanges"][leg]
    assert flange["nearest_hole_from_bend_in"] == pytest.approx(expected_nearest)
    assert flange["nearest_hole_from_bend_in"] == pytest.approx(
        flange["flange_length_in"]
        - record["product"]["manufacturer_generic_hole_center_from_end_in"]
        - record["product"]["manufacturer_hole_pitch_in"]
    )
    assert screen["minimum_loaded_end_distance_in"] == pytest.approx(3.5 * diameter)
    assert screen["full_geometry_factor_loaded_end_distance_in"] == pytest.approx(
        7 * diameter
    )
    assert flange["shift_to_minimum_in"] == pytest.approx(expected_minimum_shift)
    assert flange["shift_to_full_factor_in"] == pytest.approx(expected_full_shift)
    assert flange["passes_minimum_when_bend_flush"] is False
    assert screen["rejects_every_possible_ab205_arrangement"] is False


def test_flush_bend_screen_is_tied_to_three_actual_representative_butts():
    prototype = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/superstrut-ab205-retail.json"
        ).read_text()
    )
    butt_screen = json.loads(
        Path("docs/bolted-candidate-direct-butt-screen.json").read_text()
    )
    by_station = {row["representative_station"]: row for row in butt_screen["pairs"]}
    applications = prototype["flush_bend_wood_end_screen"][
        "representative_butt_applications"
    ]
    assert set(applications) == set(by_station)
    for station, application in applications.items():
        datum = by_station[station]
        assert application["butt_axis"] == datum["nominal_contact_axis"]
        assert application["member_with_end_at_butt"] in datum["members"]
        assert application["butt_datum_mm"] == pytest.approx(
            datum["nominal_contact_datum_mm"]
        )
        assert application["angle_placement_verified"] is False
        assert application["end_directed_joint_action_verified"] is False
