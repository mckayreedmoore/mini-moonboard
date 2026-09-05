import json
import math

import pytest

from fea.hybrid_footprint import SOURCE, report, sweep, toe_threshold
from mini_moonboard.stability import LoadCase, evaluate_load


def test_frozen_report_is_reproducible():
    from pathlib import Path
    assert json.loads(Path("fea/results/hybrid/footprint_sensitivity.json").read_text()) == report()


def test_extensions_and_friction():
    source = json.loads(SOURCE.read_text())
    base, leg, both = (sweep(source, a, b) for a, b in ((0, 0), (0, 300), (600, 600)))
    for before, after in zip(base, leg, strict=True):
        if before["minimum_factor"] is not None and after["minimum_factor"] is not None:
            assert after["minimum_factor"] >= before["minimum_factor"]
        if before["friction_required_all_rows"] is not None:
            assert after["friction_required_all_rows"] == pytest.approx(before["friction_required_all_rows"])
    assert base[-1]["minimum_leg_reaction_n"] < 0
    assert leg[-1]["minimum_leg_reaction_n"] < 0  # Opposite toe cannot cure this uplift.
    assert both[-2]["minimum_kicker_reaction_n"] > 0
    assert base[0]["governing_row"] == 12
    assert base[0]["minimum_factor"] == pytest.approx(source["cases"][0]["overturning_factor"])


@pytest.mark.parametrize("value", [-1, math.inf, math.nan])
def test_invalid_extension(value):
    with pytest.raises(ValueError):
        sweep(json.loads(SOURCE.read_text()), value, 0)
    with pytest.raises(ValueError):
        sweep(json.loads(SOURCE.read_text()), 0, value)


@pytest.mark.parametrize("force", [-100, 100])
@pytest.mark.parametrize("target", [1, 1.5, 2])
def test_threshold_against_equilibrium(force, target):
    load = LoadCase("horizontal", "analytic test", force, 0)
    threshold = toe_threshold(100/9.80665, 0, 0, 2, load, target)
    assert threshold == pytest.approx(target*2*force/100)
    a, b = (threshold, 1) if force < 0 else (-1, threshold)
    result = evaluate_load(mass_kg=100/9.80665, centre_y_mm=0,
        kicker_toe_y_mm=a, leg_toe_y_mm=b, load_y_mm=0, load_z_mm=2, load=load)
    assert result.overturning_factor == pytest.approx(target)


def test_threshold_domain_and_vertical_case():
    assert toe_threshold(100/9.80665, 0, 2, 2, LoadCase("down", "test", 0, -100), 1) == 1
    with pytest.raises(ValueError):
        toe_threshold(100/9.80665, 0, 2, 2, LoadCase("up", "test", 0, 100), 1.5)
    with pytest.raises(ValueError):
        toe_threshold(100/9.80665, 0, 2, 2, LoadCase("bad", "test", math.nan, 0), 1.5)
