"""Exact unity and adjacent-threshold checks for ordinary numeric scenarios."""
import hashlib
import sys
import types
from fractions import Fraction as F

import pytest

from scripts import eoere_cleat_traction_consumer as active


def methods():
    refs = {k: {'path': p, 'sha256': hashlib.sha256((active.ROOT/p).read_bytes()).hexdigest()}
            for k, p in {'rational': 'scripts/eoere_section_patches.py',
                         'normal': 'scripts/eoere_bore_boundary_tractions.py',
                         'stress': 'scripts/eoere_cleat_virtual_work.py',
                         'pi': 'scripts/eoere_curved_bend_field.py'}.items()}
    return active._producer().methods(refs, {})


def unity_fixture(divisor):
    method = methods()
    band = {'local_force_n': [30., 0., 40.], 'radius_mm': 1., 'axial_interval_mm': [-1., 1.],
            'peak_pressure_mpa_by_half_angle': {'90': F(1)}}
    interval = F(3, 20), F(4, 25)
    trial = active.certify(band, 90, 0, interval, method, F(divisor), F(3, 2))
    band['peak_pressure_mpa_by_half_angle']['90'] = 1/F(trial['exact_necessary_index_lower'])
    return band, interval, method


@pytest.mark.parametrize('divisor,factor', [(F(2), F(3, 2)), (2., 1.5), (1.5, 1.5), (F(3, 2), 1.5)])
@pytest.mark.parametrize('offset', (-1, 0, 1))
def test_exact_unity_and_adjacent_values_with_float_scenarios(divisor, factor, offset):
    band, interval, method = unity_fixture(divisor)
    delta = F(offset, 2**96)
    band['peak_pressure_mpa_by_half_angle']['90'] *= 1+delta
    result = active.certify(band, 90, 0, interval, method, divisor, factor)
    assert F(result['exact_necessary_index_lower']) == 1+delta
    assert result['strict_positive_area_reference_failure'] is (offset > 0)
    keyword = active.certify(band, 90, 0, interval, method, divisor=divisor, load_factor=factor)
    assert keyword == result


@pytest.mark.parametrize('value,error', [(0., ValueError), (-1., ValueError), (float('nan'), ValueError),
                                       (float('inf'), ValueError), (True, TypeError), ('0', ValueError)])
def test_invalid_scenarios_are_refused(value, error):
    with pytest.raises(error, match='positive exact real'):
        active.exact_positive(value)


def test_float_scenario_preserves_its_exact_binary_value():
    assert active.exact_positive(1.5) == F(3, 2)
    assert active.exact_positive(1.1) == F.from_float(1.1)
    assert active.exact_positive('1.1') == F(11, 10)


def test_private_producer_bypasses_cached_v1_module(monkeypatch):
    fake = types.ModuleType('scripts.eoere_cleat_traction_witness')
    fake.certify = lambda *args, **kwargs: {'wrong_cached_code': True}
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    active._producer.cache_clear()
    band, interval, method = unity_fixture(F(2))
    result = active.certify(band, 90, 0, interval, method, load_factor=1.5)
    assert result['exact_necessary_index_lower'] == '1'
    assert not result['strict_positive_area_reference_failure']
    assert sys.modules[fake.__name__] is fake
