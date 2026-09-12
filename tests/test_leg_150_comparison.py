"""Physical invariants and regression boundaries for the matched weight screen."""
import math

import pytest

from fea.leg_150_comparison import old_metrics, old_prepare, scenario
from fea.leg_attachment_check import LEG
from fea.wider_leg_limits import force_cases


@pytest.fixture(scope='module')
def old():
    return old_prepare()


def test_sharing_scales_rear_resultant_but_not_total_contact_reaction(old):
    full = force_cases(old, 150., old['foot'][1], share=1.)
    half = force_cases(old, 150., old['foot'][1], share=.5)
    assert len(full) == len(half)
    for a, b in zip(full, half, strict=True):
        assert a['compression_n'] == pytest.approx(2*b['compression_n'])
        assert a['front_vertical_reaction_n'] == pytest.approx(b['front_vertical_reaction_n'])
        assert a['front_vertical_reaction_n'] > 0


def test_pressure_shift_adds_correct_local_equilibrium_moment(old):
    compression = 3000.
    _, centered = old_metrics(old, compression, old['foot'][1])
    _, displaced = old_metrics(old, compression, old['foot'][1]+20.)
    expected = 20.*(compression*LEG[2]+old['leg']['mass_kg']*9.80665)
    assert displaced-centered == pytest.approx(expected)


def test_150_lb_reduction_does_not_remove_fixed_dead_or_horizontal_load(old):
    center = old['foot'][1]
    n150 = max(r['compression_n'] for r in force_cases(old, 150., center))
    n250 = max(r['compression_n'] for r in force_cases(old, 250., center))
    assert n150 > .6*n250
    result = scenario(old, '2x6_four_bolt', 1., 0.)
    assert .98 < result['peak_metrics']['current_thread_root_lateral'] < 1.01
    assert result['peak_metrics']['leg_member'] < .52
    assert all(math.isfinite(v) for v in result['peak_metrics'].values())
