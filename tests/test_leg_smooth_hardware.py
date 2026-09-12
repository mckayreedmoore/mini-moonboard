"""Leg candidate stack acceptance and preservation checks."""
from itertools import product

import pytest

from mini_moonboard import leg_smooth_hardware as model


@pytest.mark.parametrize("rim,leg", list(product((37.5, 38.5), repeat=2)))
def test_entire_wood_stack_has_smooth_body_and_nut_engages(rim, leg):
    result = model.dimensional_window(rim, leg)
    assert result["smooth_body_margin_mm"] >= 7.7725 - 1e-8
    assert result["nut_seating_margin_mm"] >= 5.15 - 1e-8
    assert result["two_thread_margin_mm"] >= 3.9752 - 1e-8
    assert result["dimensional_acceptance_pass"]
    assert not result["qualified_for_design"]


def test_unaccepted_stock_rejected():
    for stock in (37.49, 38.51, float("nan")):
        with pytest.raises(ValueError, match="Stock must measure"):
            model.dimensional_window(stock, 38.1)


def test_only_eight_leg_stacks_replaced():
    originals = {c.name: c for c in model.base.connections()}
    changed = [c for c in model.connections() if isinstance(c, model.SmoothBolt)]
    assert len(changed) == 8
    for bolt in model.connections():
        original = originals[bolt.name]
        if isinstance(bolt, model.SmoothBolt):
            assert bolt.members == original.members
            assert bolt.grip == original.grip
            assert (bolt.start + bolt.direction * model.PLATE_THICKNESS -
                    original.start - original.direction * model.WASHER).Length < 1e-8
        else:
            assert bolt is original


def test_mass_allowance_bounds_even_entire_new_stack():
    mass = model.mass_summary()
    assert mass["even_total_new_hardware_below_allowance"]
    assert 0 < mass["net_added_envelope_kg"] < 2
