"""Nominal AB205 center-butt fit is a prototype, not a drilling layout."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_ab205_center_fit import screen_center_fit


def test_center_fit_uses_current_cad_and_keeps_release_closed():
    actual = screen_center_fit()
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/ab205-center-fit.json").read_text()
    )
    assert actual["station"] == "clip_split_base_center_left"
    assert actual["contact_x_mm"] == pytest.approx(-89.05)
    assert actual["contact_z_mm"] == pytest.approx(277)
    assert actual["legacy_station_y_mm"] == pytest.approx(-124.9)
    product = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/superstrut-ab205-retail.json"
        ).read_text()
    )["product"]
    assert actual["bolt_diameter_mm"] == pytest.approx(
        product["manufacturer_standard_bolt_diameter_in"] * 25.4
    )
    assert actual["nominal_bore_diameter_mm"] == pytest.approx(
        product["factory_hole_diameter_in"] * 25.4
    )
    assert actual["vertical_hole_offsets_from_bend_in"][1] - actual[
        "vertical_hole_offsets_from_bend_in"
    ][0] == pytest.approx(product["manufacturer_hole_pitch_in"])
    assert actual["wood_bore_count"] == 4
    assert all(value > 0.999 for value in actual["wood_bore_full_section_fractions"])
    assert actual["legacy_y_far_principal_4d_reserve_mm"] < -29
    assert actual["reversible_4d_y_band_width_mm"] == pytest.approx(0.148, abs=0.01)
    assert actual["nearest_principal_hole_vertical_offset_mm"] == pytest.approx(36.5125)
    assert actual["principal_grain_z_component"] == pytest.approx(0.766044, abs=1e-5)
    assert actual["nearest_principal_hole_grain_ray_mm"] == pytest.approx(
        47.664, abs=0.01
    )
    assert actual["softwood_loaded_end_minimum_mm"] == pytest.approx(44.45)
    assert actual["principal_end_square_to_grain"] is False
    assert actual["end_distance_classified"] is False
    for key, value in actual.items():
        if isinstance(value, float):
            assert record[key] == pytest.approx(value)
        else:
            assert record[key] == value
    assert record["angle_placement_verified"] is False
    assert record["drilling_released"] is False
    center = json.loads(
        Path("docs/bolted-candidate-prototypes/center-header.json").read_text()
    )
    assert center["ab205_center_fit_trial"]["record"].endswith("ab205-center-fit.json")
    assert center["status"] == "incomplete_representative_prototype"
