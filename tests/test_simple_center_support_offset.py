"""Geometry-only regression for the one-post kerf-right center trial."""

import csv

import pytest

from scripts.simple_center_support_offset import AXES, probe


@pytest.fixture(scope="module")
def result():
    before = AXES.read_bytes()
    measured = probe()
    assert AXES.read_bytes() == before
    return measured


def test_only_right_post_moves_37_8_mm_and_4x6_backer_fills_center(result):
    assert result["left_post_bounds_xyz_mm"] == [
        -89.05,
        -50.95,
        -175.7,
        -36.0,
        0.0,
        238.9,
    ]
    assert result["shifted_right_post_bounds_xyz_mm"] == [
        88.75,
        126.85,
        -175.7,
        -36.0,
        0.0,
        238.9,
    ]
    assert result["backer_bounds_xyz_mm"] == [
        -50.95,
        88.75,
        -124.9,
        -36.0,
        0.0,
        238.9,
    ]
    assert result["post_to_backer_gap_mm"] == {"left": 0, "right": 0}
    assert result["solid_overlap_mm3"] == {"backer": {}, "shifted_post": {}}


def test_all_fixed_kicker_axes_retain_starts_directions_and_full_length(result):
    assert result["fixed_axes_count"] == {"panel": 48, "kicker": 18}
    axes = list(csv.DictReader(AXES.open(newline="")))
    fixed = {
        row["name"]: row
        for row in axes
        if row["name"].startswith(("round_kicker_", "kicker_header_"))
    }
    screws = result["kicker_screws"]
    assert len(screws) == len(fixed) == 18
    for name, screw in screws.items():
        row = fixed[name]
        assert screw["start_xyz_mm"] == pytest.approx(
            [float(row[f"start_{axis}_mm"]) for axis in "xyz"]
        )
        assert screw["direction_xyz"] == pytest.approx(
            [float(row[f"direction_{axis}"]) for axis in "xyz"]
        )
        assert screw["modeled_length_mm"] == pytest.approx(50.8)
        assert screw["purchased_length_mm"] == pytest.approx(63.5)
        assert screw["purchased_tip_y_mm"] == pytest.approx(-81.24375)
        assert screw["receiving_wood_length_mm"] == pytest.approx(45.24375)
        assert screw["full_length_bore_received_fraction"] == pytest.approx(1)
        assert screw["tip_inside_receiver"]
        if name.startswith("round_kicker_right_center_"):
            assert screw["receiver"] == "backer"
            assert screw["tip_to_receiver_rear_face_mm"] == pytest.approx(43.65625)
        else:
            assert screw["receiver"] == row["second_member"]
            assert screw["tip_to_receiver_rear_face_mm"] == pytest.approx(94.45625)


def test_both_inner_edges_and_trial_bolts_fit_nominally(result):
    for edge in result["inner_kicker_edges"].values():
        assert edge["inner_x_mm"] == pytest.approx(-1.5875)
        assert edge["backer_under_edge"]
        assert edge["header_under_top_segment"]
    for trial in result["trial_bolts"].values():
        assert trial["illustrated_nominal_bolt_diameter_mm"] == pytest.approx(9.525)
        assert trial["diagnostic_bore_diameter_mm"] == pytest.approx(10.5)
        assert trial["nds_2024_nominal_hole_interval_mm"] == pytest.approx(
            [10.31875, 11.1125]
        )
        assert trial["diagnostic_bore_within_interval"]
        assert trial["backer_y_axis_to_front_edge_mm"] == pytest.approx(44)
        assert trial["backer_y_axis_to_rear_edge_mm"] == pytest.approx(44.9)
        assert trial["purchased_kicker_screw_envelope_hits_mm3"] == {}
        assert all(
            value == pytest.approx(1)
            for value in trial["received_fraction_by_member"].values()
        )
        assert trial["access_envelope_hits_mm3"] == {"left": {}, "right": {}}
        assert trial["trial_access_front_panel_clearance_mm"] == pytest.approx(24)
