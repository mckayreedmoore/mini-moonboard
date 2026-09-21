"""Net-section elastic arithmetic and retained-demand provenance."""

import pytest

from scripts.simple_pb01_short_net_elastic_screen import elastic_corners, screen


def test_centroid_shift_changes_bending_moment_and_corner_stress():
    net = {
        "net_area_mm2": 50.0,
        "centroid_x_t_mm": [4.0, 3.0],
        "second_moments_about_x_t_mm4": [100.0, 200.0],
        "product_second_moment_mm4": 0.0,
    }
    row = {
        "axial_n_tension_positive": 100.0,
        "moment_u_nmm": 20.0,
        "moment_v_nmm": 30.0,
    }
    result = elastic_corners(row, net, width=10.0, depth=6.0)
    assert result["net_centroid_moment_u_nmm"] == pytest.approx(20.0)
    assert result["net_centroid_moment_v_nmm"] == pytest.approx(-70.0)
    assert result["corner_normal_mpa"]["x0_t0"] == pytest.approx(2 - 0.6 - 1.4)
    assert result["corner_normal_mpa"]["x10_t6"] == pytest.approx(2 + 0.6 + 2.1)


def test_bore_center_cut_sides_remain_diagnostic_only():
    result = screen()
    assert set(result["cases"]) == {"a12-left", "k12-right"}
    for case in result["cases"].values():
        assert len(case["bore_center_cut_sides"]) == 6
        assert {row["bores"][0] for row in case["bore_center_cut_sides"]} == {
            "u1",
            "r1",
            "u2",
        }
        assert case["max_normal_tension_mpa"] >= 0
        assert case["max_normal_compression_mpa"] >= 0
    assert result["local_hole_stress_or_splitting_checked"] is False
    assert result["complete_joint_utilization"] is None
    assert result["rating_or_drilling_release"] is False
