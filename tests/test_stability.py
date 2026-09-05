import math

import pytest

from mini_moonboard.stability import (
    LoadCase,
    evaluate_load,
    load_cases,
    row_point,
    v1_stability_screen,
)


def evaluate(fy=0, fz=-100, **overrides):
    args = {"mass_kg": 100/9.80665, "centre_y_mm": 1, "kicker_toe_y_mm": 0,
                "leg_toe_y_mm": 2, "load_y_mm": 1, "load_z_mm": 2, "load": LoadCase("test", "test", fy, fz)}
    return evaluate_load(**(args | overrides))


def test_hand_calculated_equilibrium_margin_and_friction():
    c = evaluate(25)
    assert c.kicker_reaction_n == pytest.approx(75)
    assert c.leg_reaction_n == pytest.approx(125)
    assert c.friction_required == pytest.approx(.125)
    assert math.isinf(c.overturning_factor)
    c = evaluate(75, 0)
    assert c.kicker_reaction_n == pytest.approx(-25)
    assert c.overturning_factor == pytest.approx(2/3)
    assert c.friction_required is None
    assert c.status == "UPLIFT"


def test_margins_translation_and_force_balance():
    c = evaluate(40, 0)
    assert c.overturning_factor == pytest.approx(1.25)
    assert c.status == "MARGIN BELOW 1.5"
    assert evaluate(100/3, 0).overturning_factor == pytest.approx(1.5)
    moved = evaluate(40, 0, centre_y_mm=101, kicker_toe_y_mm=100, leg_toe_y_mm=102, load_y_mm=101)
    assert moved == c
    for load in load_cases():
        c = evaluate(load=load)
        assert c.kicker_reaction_n+c.leg_reaction_n == pytest.approx(100-load.force_z_n)
        assert 2*c.leg_reaction_n+load.force_z_n-2*load.force_y_n-100 == pytest.approx(0)
    assert evaluate(0, 200).friction_required is None


@pytest.mark.parametrize("key,value", [("mass_kg", 0), ("mass_kg", math.nan),
    ("centre_y_mm", math.inf), ("centre_y_mm", 3), ("leg_toe_y_mm", 0),
    ("load_z_mm", -1), ("load_y_mm", math.nan)])
def test_invalid_inputs(key, value):
    with pytest.raises(ValueError):
        evaluate(**{key: value})
    with pytest.raises(ValueError):
        evaluate(math.nan)


@pytest.mark.parametrize("density", [0, -1, math.nan, math.inf])
def test_invalid_density(density):
    with pytest.raises(ValueError):
        v1_stability_screen(density)


def test_actual_row_and_separated_current_results():
    s = v1_stability_screen()
    assert (s.load_y_mm, s.load_z_mm) == row_point(12)
    assert s.load_z_mm == pytest.approx(1971.58, abs=.02)
    assert s.cases[0].status == "MEETS 2D MARGIN ONLY"
    assert s.cases[0].friction_required == 0
    assert all(c.status == "UPLIFT" for c in s.cases[-2:])
    assert s.cases[-2].kicker_reaction_n == pytest.approx(-350, abs=2)
    assert s.cases[-1].leg_reaction_n == pytest.approx(-793, abs=2)
    for c in s.cases:
        assert c == s.at(c.load, *row_point(12))
