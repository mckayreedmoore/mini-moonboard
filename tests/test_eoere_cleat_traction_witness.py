"""Exact patch bounds, material-support controls and captured-definition checks."""
import hashlib
import math
import sys
import types
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import eoere_cleat_traction_witness as witness


def reference(path):
    return {'path': path, 'sha256': hashlib.sha256((witness.ROOT/path).read_bytes()).hexdigest()}


def methods():
    return witness.methods({k: reference(v) for k, v in {
        'rational': 'scripts/eoere_section_patches.py', 'normal': 'scripts/eoere_bore_boundary_tractions.py',
        'stress': 'scripts/eoere_cleat_virtual_work.py', 'pi': 'scripts/eoere_curved_bend_field.py'}.items()}, {})


def band(force=(30., 0., 40.)):
    size = math.sqrt(sum(f*f for f in force))
    return {'local_force_n': list(force), 'radius_mm': 1., 'axial_interval_mm': [-1., 1.],
            'peak_pressure_mpa_by_half_angle': {
                '30': size/(2*3*math.sqrt(3)/8), '60': size/(2*1.2), '90': size/math.pi}}


@pytest.mark.parametrize('value', [F(0), F(2), F(3), F(9, 4), F(1, 2**100), F(2147483647)])
def test_exact_root_enclosures(value):
    lo, hi = witness.sqrt_bounds(value)
    assert lo*lo <= value <= hi*hi and hi-lo <= F(1, 2**96)
    if lo*lo == value:
        assert hi == lo


@pytest.mark.parametrize('value,bits', [(F(-1), 96), (F(1), 15), (F(1), 257)])
def test_root_refuses_unsupported_domain(value, bits):
    with pytest.raises(ValueError):
        witness.sqrt_bounds(value, bits)


def test_full_tensor_normal_support_keeps_shear_factor_and_asymmetric_signs():
    method = methods()
    strengths = {key: F(1, 10) for key in method.BASE_STRENGTHS}
    strengths['parallel_shear'] = F(10)
    c, s = F(3, 5), F(4, 5)
    strain = (-c*c, F(0), -s*s, F(0), -2*c*s, F(0))
    support = method.support(strain, strengths)
    # A stress with only tau_gv=-10 saturates the gauge and this normal work.
    assert support == 2*10*c*s == F(48, 5)
    strengths['compression_parallel'], strengths['tension_parallel'] = F(17), F(1)
    assert method.support((F(-1), F(0), F(0), F(0), F(0), F(0)), strengths) == 17
    assert method.support((F(1), F(0), F(0), F(0), F(0), F(0)), strengths) == 1


@pytest.mark.parametrize('degrees', (30, 60, 90))
def test_continuous_pressure_patch_encloses_independent_samples_and_both_normalizations(degrees):
    method = methods()
    source = band()
    # Deliberately separate stored and exact-normalization amplitudes.
    source['peak_pressure_mpa_by_half_angle'][str(degrees)] *= 1+1e-10
    certificate = witness.certify(source, degrees, 0, (F(49, 100), F(51, 100)), method)
    lo, hi = map(F, certificate['exact_pressure_interval_mpa'])
    h = F(certificate['exact_full_tensor_support_upper_mpa'])
    beta, size = math.radians(degrees), 50.
    integral = {30: 3*math.sqrt(3)/8, 60: 1.2, 90: math.pi/2}[degrees]
    for t in np.linspace(.49, .51, 31):
        c, s = map(float, method.normal(0, F(float(t))))
        phi = math.acos(min(1., (30*c+40*s)/size))
        for peak in (source['peak_pressure_mpa_by_half_angle'][str(degrees)], size/(2*integral)):
            pressure = peak*math.cos(math.pi*phi/(2*beta))
            assert float(lo)-1e-11 <= pressure <= float(hi)+1e-11
        local_support = max(8.5*c*c, 1.1*s*s, 2*1.072*abs(c*s))
        assert local_support <= float(h)+1e-12
    assert F(certificate['exact_area_lower_mm2']) > 0
    assert certificate['strict_positive_area_reference_failure']


def test_certified_lower_scales_exactly_and_small_trial_is_inconclusive():
    method = methods()
    args = band(), 90, 0, (F(49, 100), F(51, 100)), method
    first = witness.certify(*args)
    double_divisor = witness.certify(*args, divisor=F(4))
    scaled_load = witness.certify(*args, load_factor=F(3, 2))
    lower = F(first['exact_necessary_index_lower'])
    assert F(double_divisor['exact_necessary_index_lower']) == 2*lower
    assert F(scaled_load['exact_necessary_index_lower']) == F(3, 2)*lower
    small = witness.certify(band((.003, 0., .004)), 90, 0, (F(49, 100), F(51, 100)), method)
    assert F(small['exact_necessary_index_lower']) < 1
    assert small['disposition'] == 'INCONCLUSIVE_NECESSARY_WITNESS'


@pytest.mark.parametrize('fault', ('opposite_arc', 'out_of_arc', 'axial_force', 'negative_length', 'zero_peak'))
def test_unadmitted_surface_hypotheses_are_refused(fault):
    method = methods()
    source = band()
    degrees, quarter, interval = 90, 0, (F(49, 100), F(51, 100))
    if fault == 'opposite_arc':
        quarter = 2
    elif fault == 'out_of_arc':
        degrees, interval = 30, (F(0), F(1, 100))
    elif fault == 'axial_force':
        source['local_force_n'][1] = 1.
    elif fault == 'negative_length':
        source['axial_interval_mm'] = [1., -1.]
    else:
        source['peak_pressure_mpa_by_half_angle']['90'] = 0.
    with pytest.raises(ValueError):
        witness.certify(source, degrees, quarter, interval, method)


def test_pure_definition_capture_avoids_module_side_effects_and_rejects_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(witness, 'ROOT', tmp_path)
    path = tmp_path/'source.py'
    path.write_bytes(b'raise RuntimeError("module execution forbidden")\ndef chosen():\n return 17\n')
    reference = {'path': 'source.py', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    loaded = witness.definitions(reference, ('chosen',), (), {}, {})
    path.write_bytes(b'def chosen():\n return 18\n')
    assert loaded.chosen() == 17
    with pytest.raises(ValueError, match='source changed'):
        witness.definitions(reference, ('chosen',), (), {}, {})
    path.write_bytes(b'def chosen():\n return 17\ndef chosen():\n return 18\n')
    reference['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='unique'):
        witness.definitions(reference, ('chosen',), (), {}, {})


def test_cached_repository_helpers_do_not_supply_certifying_definitions(monkeypatch):
    fake = types.ModuleType('scripts.eoere_cleat_virtual_work')
    fake.support = lambda *args: F(0)
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    method = methods()
    assert method.support((F(-1), F(0), F(0), F(0), F(0), F(0)), method.BASE_STRENGTHS) == 17
    assert sys.modules[fake.__name__] is fake
