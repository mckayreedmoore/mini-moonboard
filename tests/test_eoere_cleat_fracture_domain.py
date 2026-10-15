"""Independent published-equation, finite-path and provenance controls."""
import copy
import hashlib
import json
import math

import pytest

from scripts import eoere_cleat_fracture_domain as domain


def published_length(ei, eii, gi, gii, ft, fv, k):
    # Evaluate Eqs.22-23 directly, independently of the harmonic-mean shortcut.
    mixed_gi = (1/math.sqrt(gi)+math.sqrt(ei)*k/math.sqrt(eii*gii))**-2
    return 2/math.pi*ei*mixed_gi/ft**2*(1+k*k/(fv/ft)**2)


@pytest.mark.parametrize('nu', [0., .2, .45])
def test_isotropic_generalized_moduli_reduce_to_youngs_modulus(nu):
    assert domain.generalized_moduli(1234., 1234., 1234./(2*(1+nu)), nu) == pytest.approx((1234., 1234.))


@pytest.mark.parametrize('parameters', [
    (1207.3242506954066, 4629.877152348811, .1, .35, .2, 1.072),
    (7., 19., .3, .7, .4, .9), (31., 11., .2, .05, .6, .2),
])
def test_minimum_is_attained_and_bounds_the_direct_published_expression(parameters):
    result = domain.length_bound(*parameters)
    minimum = result['minimum_over_all_nonnegative_mode_ratios_mm']
    optimum = result['minimizing_absolute_shear_to_tension_ratio']
    assert published_length(*parameters, optimum) == pytest.approx(minimum, rel=2e-15)
    for k in (0., 1e-6, .01, .5, 1., 2., 10., 100., 1e6, optimum/2, optimum*2):
        assert published_length(*parameters, k) >= minimum*(1-2e-15)
    assert published_length(*parameters, 0.) == pytest.approx(result['pure_mode_I_length_mm'])
    assert published_length(*parameters, 1e12) == pytest.approx(result['pure_mode_II_length_mm'], rel=1e-10)


def test_equal_pure_mode_lengths_have_half_length_minimum_at_unit_mode_ratio():
    result = domain.length_bound(100., 100., .1, .1, 1., 1.)
    assert result['minimum_over_all_nonnegative_mode_ratios_mm'] == pytest.approx(10/math.pi)
    assert result['minimizing_absolute_shear_to_tension_ratio'] == pytest.approx(1.)


def test_strength_divisor_and_common_energy_scaling_have_the_expected_units():
    base = domain.length_bound(7., 19., .3, .7, .4, .9)
    scaled = domain.length_bound(7., 19., .6, 1.4, .4/3, .9/3)
    for key in ('pure_mode_I_length_mm', 'pure_mode_II_length_mm', 'minimum_over_all_nonnegative_mode_ratios_mm'):
        assert scaled[key] == pytest.approx(18*base[key])
    assert scaled['minimizing_absolute_shear_to_tension_ratio'] == pytest.approx(base['minimizing_absolute_shear_to_tension_ratio'])


def bores():
    return [{'axis_id': f'b{i}', 'y_mm': y, 'z_mm': z, 'radius_mm': 1.}
            for i, (y, z) in enumerate(((-2., 5.), (2., 5.), (-2., 10.), (2., 10.)))]


def test_tangent_rays_use_the_finished_sloping_top_and_both_grain_directions():
    polygon = [[-5., 0.], [5., 0.], [5., 30.], [-5., 20.]]
    paths = domain.tangent_paths('test-cleat', polygon, bores())
    assert len(paths) == len({(p['axis_id'], p['tangent_side'], p['grain_direction']) for p in paths}) == 16
    assert min(p['available_length_upper_bound_mm'] for p in paths) == 5.
    assert max(p['available_length_upper_bound_mm'] for p in paths) == 23.
    for path in paths:
        end = 0. if path['grain_direction'] == -1 else 25.+path['path_y_mm']
        assert path['end_z_mm'] == end
        assert path['available_length_upper_bound_mm'] == abs(end-path['start_z_mm'])


@pytest.mark.parametrize('change', ['duplicate', 'edge', 'top', 'radius', 'nan'])
def test_invalid_bore_or_duplicate_identity_is_rejected(change):
    rows = bores()
    if change == 'duplicate':
        rows[1]['axis_id'] = rows[0]['axis_id']
    elif change == 'edge':
        rows[0]['y_mm'] = -4.
    elif change == 'top':
        rows[0]['z_mm'] = 22.
    elif change == 'radius':
        rows[0]['radius_mm'] = True
    else:
        rows[0]['z_mm'] = math.nan
    with pytest.raises(ValueError):
        domain.tangent_paths('test-cleat', [[-5., 0.], [5., 0.], [5., 30.], [-5., 20.]], rows)


@pytest.mark.parametrize('ex,ey,g,nu', [(0., 1., 1., .2), (1., math.inf, 1., .2),
                                      (1., 1., -1., .2), (True, 1., 1., .2),
                                      (1., 1., 1., math.nan), (1., 1., 1., 1.)])
def test_invalid_elastic_plane_is_rejected(ex, ey, g, nu):
    with pytest.raises(ValueError):
        domain.generalized_moduli(ex, ey, g, nu)


@pytest.mark.parametrize('bad', [0., -1., True, math.nan, math.inf])
def test_invalid_fracture_parameter_is_rejected(bad):
    with pytest.raises(ValueError):
        domain.length_bound(100., 100., bad, .1, 1., 1.)


def test_assumptions_are_read_and_hashed_before_intake_and_drift_is_refused(tmp_path, monkeypatch):
    data = json.loads(domain.INPUT.read_bytes())
    path = tmp_path/'inputs.json'
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    monkeypatch.setattr(domain, 'INPUT', path)
    monkeypatch.setattr(domain.current, 'ROOT', tmp_path)
    captured = {}

    def intake():
        path.write_bytes(raw+b'\n')
        return [], {}

    monkeypatch.setattr(domain.prior.intake_source, 'intake', intake)
    monkeypatch.setattr(domain.current, 'read', lambda _: {'source_sha256': {}})
    monkeypatch.setattr(domain.current, 'ref', lambda p: {'path': str(p), 'sha256': 'unused'})

    def verify(pins):
        captured.update(pins)
        assert pins['inputs.json'] == hashlib.sha256(raw).hexdigest()
        raise ValueError('changed input before comparison')

    monkeypatch.setattr(domain.current, 'verify', verify)
    with pytest.raises(ValueError, match='changed input before comparison'):
        domain.run()
    assert captured['inputs.json'] != hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('key,value', [('actual_observations', {}), ('extra_grid', True),
                                     ('fracture_energies_mode_I_n_per_mm', [.133]),
                                     ('mode_II_to_I_energy_ratios', [3.5]), ('strength_divisors', [1.]),
                                     ('geometry_revision', 'old')])
def test_unbound_or_changed_hypothesis_scope_is_rejected(key, value):
    inputs = copy.deepcopy(json.loads(domain.INPUT.read_bytes()))
    inputs[key] = value
    with pytest.raises(ValueError):
        domain.validate(inputs)
