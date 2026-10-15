"""Independent section equilibrium and continuous-maximum method controls."""
import copy
import hashlib
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

from scripts import eoere_cleat_section_reference as section


@pytest.mark.parametrize("wrench", [
    [17., -23., 31., -47., 59., -61.],
    *[np.eye(6)[i]*(-1 if i % 2 else 1)*100 for i in range(6)],
])
def test_independent_gauss_integration_recovers_all_six_signed_resultants(wrench):
    width, height = 13., 29.
    fields = section.traction_coefficients(wrench, width, height)
    points, weights = np.polynomial.legendre.leggauss(3)
    recovered = np.zeros(6)
    for u, v in itertools.product(range(3), repeat=2):
        p, q = points[u]*height/2, points[v]*width/2
        stress = np.array([float(section.evaluate(f, points[u], points[v])) for f in fields])
        recovered += np.r_[stress, np.cross([0., p, q], stress)]*weights[u]*weights[v]*width*height/4
    assert recovered == pytest.approx(wrench, abs=1e-11)


def test_side_normal_shear_vanishes_including_combined_shear_and_torque():
    fields = section.traction_coefficients([7., -11., 13., -17., 19., -23.], 31., 59.)
    for coordinate in (F(-1), F(-1, 3), F(0), F(2, 5), F(1)):
        for edge in (-1, 1):
            assert section.evaluate(fields[1], F(edge), coordinate) == 0
            assert section.evaluate(fields[2], coordinate, F(edge)) == 0


def test_torsion_field_is_transversely_divergence_free_exactly():
    _, parallel, rolling = section.traction_coefficients([0., 0., 0., 123., 0., 0.], 7., 19.)
    derivative = {}
    for field, axis, half_span in ((parallel, 0, F(19, 2)), (rolling, 1, F(7, 2))):
        for powers, coefficient in field.items():
            exponent = powers[axis]
            if exponent:
                key = list(powers)
                key[axis] -= 1
                derivative[tuple(key)] = derivative.get(tuple(key), F(0))+coefficient*exponent/half_span
    assert all(value == 0 for value in derivative.values())


@pytest.mark.parametrize("force,expected", [(8., 2.), (-8., 1.)])
def test_pure_normal_reference_uses_tension_or_compression_strength(force, expected):
    fields = section.traction_coefficients([force, 0., 0., 0., 0., 0.], 2., 2.)
    strengths = {"tension": 1., "compression": 2., "parallel_shear": 1., "rolling_shear": 1.}
    result = section.enclosure(section.interaction_polynomials(fields, strengths))
    assert result["lower"] == result["upper"] == expected


def test_pure_torsion_square_has_known_continuous_linear_interaction_maximum():
    fields = section.traction_coefficients([0., 0., 0., 1., 0., 0.], 2., 2.)
    strengths = dict.fromkeys(("tension", "compression", "parallel_shear", "rolling_shear"), 1.)
    result = section.enclosure(section.interaction_polynomials(fields, strengths), 1e-6)
    # For |u|,|v|<=1, |u|(1-v²)+|v|(1-u²)<=1. Maximum is at an edge midpoint.
    assert result["lower"] <= 9/16 <= result["upper"]
    assert result["upper"]-result["lower"] <= 1.000001e-6


def test_continuous_bound_covers_interior_peak_missed_by_corner_and_center_sampling():
    # 1-(u-3/10)^2-(v+1/5)^2 has its exact maximum at (0.3,-0.2).
    polynomial = {(0, 0): F(87, 100), (1, 0): F(3, 5), (2, 0): F(-1),
                  (0, 1): F(-2, 5), (0, 2): F(-1)}
    result = section.enclosure([polynomial], 1e-7)
    assert F(result["exact_lower_fraction"]) <= 1 <= F(result["exact_upper_fraction"])
    assert F(result["exact_upper_fraction"])-F(result["exact_lower_fraction"]) <= F(1, 10**7)
    assert result["normalized_witness_u_v"] == pytest.approx([.3, -.2], abs=.001)


def test_subdivision_preserves_a_nonseparable_polynomial_on_both_child_domains():
    polynomial = {(2, 1): F(7), (1, 2): F(-11), (0, 2): F(13), (0, 0): F(-17)}
    matrix = section.bernstein(polynomial)
    for axis in (0, 1):
        halves = section.subdivide(matrix, axis)
        for side, child in enumerate(halves):
            for x, y in itertools.product((F(0), F(1, 3), F(1)), repeat=2):
                weights_x, weights_y = ((1-x)**2, 2*x*(1-x), x*x), ((1-y)**2, 2*y*(1-y), y*y)
                value = sum(child[i][j]*weights_x[i]*weights_y[j] for i in range(3) for j in range(3))
                coordinates = [2*x-1, 2*y-1]
                coordinates[axis] = (x if axis == 0 else y)+side-1
                assert value == section.evaluate(polynomial, *coordinates)


def test_signed_field_reversal_and_strength_swap_preserve_the_interaction():
    wrench = [3., -7., 11., -13., 17., -19.]
    strengths = {"tension": .4, "compression": 2.2, "parallel_shear": 2.144, "rolling_shear": .8}
    original = section.enclosure(section.interaction_polynomials(section.traction_coefficients(wrench, 17., 53.), strengths))
    reverse = {**strengths, "tension": strengths["compression"], "compression": strengths["tension"]}
    reflected = section.enclosure(section.interaction_polynomials(section.traction_coefficients([-v for v in wrench], 17., 53.), reverse))
    assert original["lower"] == pytest.approx(reflected["lower"], abs=1e-5)
    assert original["upper"] == pytest.approx(reflected["upper"], abs=1e-5)


@pytest.mark.parametrize("wrench,width,height", [
    ([0.]*5, 1., 1.), ([0., 0., 0., math.nan, 0., 0.], 1., 1.),
    ([0.]*6, 0., 1.), ([0.]*6, 1., -1.), ([0.]*6, 1., math.inf),
    ([True, 0., 0., 0., 0., 0.], 1., 1.),
])
def test_invalid_section_input_is_rejected(wrench, width, height):
    with pytest.raises(ValueError):
        section.traction_coefficients(wrench, width, height)


def test_invalid_strength_or_certificate_is_rejected():
    fields = section.traction_coefficients([0.]*6, 1., 1.)
    with pytest.raises(ValueError):
        section.interaction_polynomials(fields, dict.fromkeys(("tension", "compression", "parallel_shear", "rolling_shear"), 0.))
    for kwargs in ({"tolerance": 0.}, {"max_cells": 0}):
        with pytest.raises(ValueError):
            section.enclosure([{(0, 0): F(1)}], **kwargs)
    with pytest.raises(ValueError):
        section.enclosure([{(3, 0): F(1)}])
    with pytest.raises(ValueError, match="did not converge"):
        section.enclosure([{(0, 0): F(1), (2, 0): F(-1), (1, 0): F(3, 5)}], 1e-12, max_cells=1)


def assumptions():
    return {"schema": "eoere_conditional_material_assumptions/v1",
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
            "extra_grid": False, "actual_observations": None, "physical_or_structural_release": False,
            "source_characteristic_values_mpa": {"tension_perpendicular": .4, "compression_perpendicular": 2.2,
                                                  "parallel_shear": 3.2, "rolling_shear_approximation": .8},
            "parallel_shear_reference_reduction": .67,
            "intact_section_base_reference_mpa": {"tension": .4, "compression": 2.2, "parallel_shear": 2.144, "rolling_shear": .8},
            "strength_scaling_scenarios": [{"id": str(i), "strength_divisor": 2.+i,
                                            "whole_wrench_multiplier": 1., "working_reference": i == 0} for i in range(6)]}


def test_assumption_validation_preserves_the_declared_scope():
    value = assumptions()
    before = copy.deepcopy(value)
    section.validate_assumptions(value)
    assert value == before


@pytest.mark.parametrize("change", ["assigned_grade", "released", "false_source", "wrong_reduction", "strength_increase",
                                    "demand_reduction", "second_working", "duplicate_scenario", "wrong_revision"])
def test_inconsistent_or_unapproved_assumption_is_rejected(change):
    value = assumptions()
    if change == "assigned_grade":
        value["actual_observations"] = "C16 observed"
    elif change == "released":
        value["physical_or_structural_release"] = True
    elif change == "false_source":
        value["source_characteristic_values_mpa"]["tension_perpendicular"] = .5
    elif change == "wrong_reduction":
        value["intact_section_base_reference_mpa"]["parallel_shear"] = 3.2
    elif change == "strength_increase":
        value["strength_scaling_scenarios"][2]["strength_divisor"] = .5
    elif change == "demand_reduction":
        value["strength_scaling_scenarios"][2]["whole_wrench_multiplier"] = .5
    elif change == "second_working":
        value["strength_scaling_scenarios"][1]["working_reference"] = True
    elif change == "duplicate_scenario":
        value["strength_scaling_scenarios"][1]["id"] = "0"
    elif change == "wrong_revision":
        value["geometry_revision"] = "earlier-model"
    with pytest.raises(ValueError):
        section.validate_assumptions(value)


def test_input_changed_during_intake_is_rejected_before_any_comparison(tmp_path, monkeypatch):
    input_path = tmp_path/"assumptions.json"
    initial = {**assumptions(), "cached_sources": []}
    input_path.write_text(json.dumps(initial))
    monkeypatch.setattr(section, "INPUT", input_path)
    monkeypatch.setattr(section.current, "ROOT", tmp_path)

    def ref(path):
        path = Path(path)
        return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "unused"}

    def intake():
        changed = copy.deepcopy(initial)
        changed["strength_scaling_scenarios"][0]["strength_divisor"] = 4.
        input_path.write_text(json.dumps(changed))
        return [], {}

    def verify(pins):
        section.current.require(pins["assumptions.json"] == hashlib.sha256(input_path.read_bytes()).hexdigest(),
                                "source drift: assumptions.json")

    monkeypatch.setattr(section.current, "ref", ref)
    monkeypatch.setattr(section.current, "read", lambda source: {"source_sha256": {}, "cases": []})
    monkeypatch.setattr(section.current, "verify", verify)
    monkeypatch.setattr(section.prior.intake_source, "intake", intake)
    with pytest.raises(ValueError, match="source drift: assumptions.json"):
        section.run()
