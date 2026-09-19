"""Nominal AB205 center-butt fit is a prototype, not a drilling layout."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_ab205_center_fit import (
    screen_center_fit,
    screen_opposed_center_fit,
    screen_retained_axis_conflicts,
)


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
    assert center["ab205_center_fit_trial"]["shared_header_method_gate"][
        "record"
    ].endswith("center-shared-bolt-method.md")
    assert center["status"] == "incomplete_representative_prototype"


def test_swapping_ab205_legs_widens_edge_band_but_does_not_release_joint():
    actual = screen_center_fit(vertical_leg="short")
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/ab205-center-fit.json").read_text()
    )["alternate_short_vertical"]
    assert actual["vertical_hole_offsets_from_bend_in"] == [0.8125, 2.6875]
    assert actual["horizontal_hole_offsets_from_bend_in"] == [1.4375, 3.3125]
    assert actual["reversible_4d_y_band_width_mm"] == pytest.approx(9.774, abs=0.01)
    assert actual["nearest_principal_hole_grain_ray_mm"] == pytest.approx(
        26.94, abs=0.01
    )
    assert actual["end_distance_classified"] is False
    assert actual["drilling_released"] is False
    for key, value in actual.items():
        if isinstance(value, float):
            assert record[key] == pytest.approx(value)
        else:
            assert record[key] == value


def test_short_vertical_midband_bores_do_not_hit_frozen_kerf_axes():
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/ab205-center-fit.json").read_text()
    )["short_vertical_midband_trial"]
    initial = screen_center_fit("short")
    row_y = (
        initial["reversible_4d_y_lower_mm"] + initial["reversible_4d_y_upper_mm"]
    ) / 2
    actual = screen_center_fit("short", row_y)
    axis_screen = screen_retained_axis_conflicts(row_y)
    assert row_y == pytest.approx(record["row_y_mm"])
    assert actual["legacy_y_far_principal_4d_reserve_mm"] == pytest.approx(
        record["principal_far_hole_4d_edge_reserve_mm"]
    )
    assert all(value > 0.999 for value in actual["wood_bore_full_section_fractions"])
    assert axis_screen == record["retained_axis_conflict_screen"]
    assert axis_screen["retained_axes_inspected"] == {
        "hillman_panel": 66,
        "bolt_clearance": 12,
    }
    assert axis_screen["trial_bore_count"] == 4
    assert not axis_screen["nominal_axis_conflicts_found"]
    assert actual["end_distance_classified"] is False
    assert actual["drilling_released"] is False


def test_opposed_center_post_can_nominally_share_header_axes_only():
    record = json.loads(
        Path("docs/bolted-candidate-prototypes/ab205-center-fit.json").read_text()
    )["opposed_center_post_trial"]
    actual = screen_opposed_center_fit(record["trial_row_y_mm"])
    assert actual == record
    assert actual["top_header_hole_x_mm"] == actual["underside_header_hole_x_mm"]
    assert all(value > 0.999 for value in actual["post_bore_full_section_fractions"])
    assert actual["unique_wood_bore_axes"] == 6
    assert (
        actual[
            "two_member_single_shear_method_directly_applicable_to_shared_header_bolts"
        ]
        is False
    )
    assert actual["purchased_panel_length_axis_conflicts_for_six_unique_bores"] == []
    assert actual["post_conditional_reversible_4d_edge_reserve_mm"] > 8
    assert actual["shared_fastener_stack_defined"] is False
    assert actual["drilling_released"] is False
