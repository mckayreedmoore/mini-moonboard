"""The PB01 oblique decomposition reconstructs retained signed bolt actions."""

import math

import pytest

from scripts.simple_pb01_short_oblique_distribution import decompose, screen


def test_pair_algebra_retains_couple_and_signed_reconstruction():
    result = decompose((31.662, 16.534), (31.169, -10.708), 40.0)
    assert result["resultant_along_across_n"] == pytest.approx([62.831, 5.826])
    assert result["half_difference_along_across_n"] == pytest.approx([-0.2465, -13.621])
    assert result["bolt_couple_nmm"] == pytest.approx(-544.84)
    for actual, expected in zip(
        result["reconstructed_bolts_along_across_n"],
        ([31.662, 16.534], [31.169, -10.708]),
        strict=True,
    ):
        assert actual == pytest.approx(expected)
    assert result["sum_lateral_magnitudes_n"] == pytest.approx(
        math.hypot(31.662, 16.534) + math.hypot(31.169, -10.708)
    )


def test_verified_archives_reconstruct_all_four_oblique_pairs():
    result = screen()
    assert result["block_length_mm"] == 152.4
    assert result["legacy_proxy_stations_per_case"] == 23
    assert result["joint_utilization"] is None
    assert result["design_pass"] is None
    assert result["drilling_released"] is False
    assert set(result["cases"]) == {"a12-left", "k12-right"}
    expected_couples = {
        "a12-left": {"upright": -565.4475, "rail": -417.24},
        "k12-right": {"upright": -634.95, "rail": -544.84},
    }
    for case, faces in result["cases"].items():
        for family, row in faces.items():
            assert row["pitch_mm"] == pytest.approx(
                45.0 if family == "upright" else 40.0, abs=0.001
            )
            assert row["bolt_couple_nmm"] == pytest.approx(
                expected_couples[case][family], abs=0.01
            )
            assert row["max_reconstruction_error_n"] < 1e-10
            assert row["max_out_of_plane_lateral_n"] < 1e-10
            assert row["group_utilization"] is None
            assert row["adjusted_resistance_n"] is None
    rail = result["cases"]["k12-right"]["rail"]
    assert rail["sum_lateral_magnitudes_n"] == pytest.approx(68.676, abs=0.001)
    assert rail["bolts"][0]["axial_on_host_n"] == pytest.approx(19.6676)


def test_zero_pitch_is_rejected():
    with pytest.raises(ValueError, match="pitch"):
        decompose((1.0, 2.0), (3.0, 4.0), 0.0)
