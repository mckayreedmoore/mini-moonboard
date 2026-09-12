"""Independent checks on reference crossings and their support-validity domain."""
import math

import pytest

from fea.leg_attachment_check import LEG
from fea.leg_bolt_pattern_search import group_factor, lateral
from fea.wider_leg_assessment import six_group_factor
from fea.wider_leg_limits import (
    POUND_FORCE_N,
    bisect_crossing,
    force_cases,
    front_contact_crossing,
    prepare,
    source_adjusted_lateral,
)


@pytest.fixture(scope='module')
def data():
    return prepare()


def test_dead_and_fixed_horizontal_are_not_scaled_with_climber(data):
    # Use one hold and fixed coordinates so extrema identify the same load.
    data = {**data, 'holds': [data['holds'][-1]]}
    y = data['foot'][1]
    def peak(pounds, share=1.):
        return max(r['compression_n'] for r in force_cases(data, pounds, y, share))
    assert peak(0.) > 0
    assert peak(200.)-peak(100.) == pytest.approx(peak(100.)-peak(0.))
    assert peak(200.) < 2*peak(100.)
    assert peak(200., .5) == pytest.approx(.5*peak(200.))


def test_reference_engine_reproduces_existing_worst_angle_equations():
    forces = [(0., 200., 600.), (0., -300., 900.), (0., 0., 700.)]
    old = lateral(forces, .5, 84.)
    current = source_adjusted_lateral(forces)
    for before, after in zip(old['bolts'], current, strict=True):
        assert after['ratio'] == pytest.approx(before['ratio']*group_factor(.5, 84.)/six_group_factor())
        assert after['mode'] == before['mode']
    exact = source_adjusted_lateral(forces, exact_angle=True)
    assert all(a['ratio'] <= b['ratio'] for a, b in zip(exact, current, strict=True))


def test_first_contact_loss_is_actual_zero_reaction_and_share_independent(data):
    offset = -data['half']
    loss = front_contact_crossing(data, offset)
    assert 250 < loss['climber_lb'] < 400
    assert loss['reaction_intercept_n']+loss['climber_lb']*loss['reaction_slope_n_per_lb'] == pytest.approx(0., abs=1e-9)
    for share in (1., .5):
        cases = force_cases(data, loss['climber_lb'], data['foot'][1]+offset, share)
        assert min(r['front_vertical_reaction_n'] for r in cases) == pytest.approx(0., abs=1e-8)
        row = max(cases, key=lambda r:r['compression_n'])
        total_down = data['mass']*9.80665+loss['climber_lb']*2*POUND_FORCE_N
        assert row['front_vertical_reaction_n']+row['compression_n']/share*LEG[2] == pytest.approx(total_down)


def test_bidirectional_root_and_missing_bracket():
    assert bisect_crossing(lambda x: x*x, 0., 2.) == pytest.approx(1.)
    assert bisect_crossing(lambda x: 2-x, 0., 2.) == pytest.approx(1.)
    with pytest.raises(ValueError, match='not bracketed'):
        bisect_crossing(lambda x: math.exp(x), 1., 2.)


def test_full_strength_retains_nonconnection_governing_checks(data):
    from fea.wider_leg_limits import full_context, full_strength_envelope
    # A centered foot minimizes bolt-group moment; timber/plate checks must
    # still be retained rather than reporting the much higher bolt-only limit.
    result = full_strength_envelope(data, full_context(data), 250., 0.)
    assert result['evaluated_unique_load_cases'] > 20
    assert 'leg_member' in result['peak_metrics']
    assert 'plate_plastic_bending' in result['peak_metrics']
    assert result['peak_ratio'] == max(result['peak_metrics'].values())
    assert result['peak_ratio'] > result['peak_metrics']['conservative_lateral_plus_axial']
