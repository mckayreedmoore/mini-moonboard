"""Arithmetic and claim boundary for the conditional wood/bolt comparison."""

import json
import math
from pathlib import Path

import pytest


def test_a66_wood_vs_bolt_screen_is_conditional_and_reproducible():
    path = Path("docs/bolted-candidate-prototypes/a66-wood-vs-bolt-screen.json")
    screen = json.loads(path.read_text())
    inputs = screen["inputs"]
    derived = screen["derived"]
    diameter = inputs["diameter_in"]
    length = inputs["wood_bearing_length_in"]

    assert derived["wood_mode_im_reference_lbf_parallel"] == pytest.approx(
        diameter * length * inputs["wood_fe_parallel_psi"] / inputs["nds_mode_im_rd_parallel"]
    )
    assert derived["wood_mode_im_reference_lbf_perpendicular"] == pytest.approx(
        diameter * length * inputs["wood_fe_perpendicular_psi"] /
        inputs["nds_mode_im_rd_perpendicular"]
    )
    assert derived["one_hole_net_parallel_tension_lbf_at_5p5_in_face"] == pytest.approx(
        inputs["dfl_no2_ft_parallel_psi"] * length * (5.5 - 7 / 16)
    )
    assert derived["one_in_washer_axial_wood_bearing_lbf"] == pytest.approx(
        inputs["dfl_no2_fc_perpendicular_psi"] * math.pi / 4 * (1 - (7 / 16) ** 2),
        abs=0.001,
    )
    assert derived["hypothetical_two_bolt_row_tear_out_lbf_at_3d_pitch"] == pytest.approx(
        2 * inputs["dfl_no2_fv_parallel_psi"] * length * 3 * diameter
    )
    nominal = (math.pi * diameter**2 / 4 *
               inputs["aisc_a307_nominal_shear_stress_ksi"] * 1000)
    assert derived["a307_nominal_shaft_shear_lbf"] == pytest.approx(nominal, abs=0.001)
    assert derived["a307_asd_shaft_shear_lbf"] == pytest.approx(
        nominal / inputs["aisc_bolt_shear_asd_omega"], abs=0.001
    )
    assert derived["wood_mode_im_reference_lbf_parallel"] < derived["a307_asd_shaft_shear_lbf"]
    assert derived["wood_mode_im_reference_lbf_perpendicular"] < derived["a307_asd_shaft_shear_lbf"]
    assert screen["a66_joint_capacity_established"] is False
    assert screen["factory_hole_layout_established"] is False
    assert screen["drilling_released"] is False
