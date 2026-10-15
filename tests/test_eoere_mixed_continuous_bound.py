"""Independent known-answer controls for the continuous virtual-work bound."""
from fractions import Fraction as F
from pathlib import Path

import pytest

from scripts import eoere_mixed_continuous_bound as bound


def fixture(force, first, cap=1):
    return {'surfaces': [{'interval': [-1, 1], 'cap': cap, 'force': force,
                          'first_moment': first}], 'points': [], 'domain': [-1, 1],
            'moment_caps': [{'interval': [-1, 1], 'cap': 1}]}


def valid_inputs():
    return {'schema': 'eoere_current_mixed_continuous_bound_inputs/v1',
            'geometry_revision': 'eoere-raised-kicker-screws-v1',
            'hardware_revision': 'eoere-selected-purchase-hardware-v1',
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'actual_observations': None, 'complete_joint_resistance': None,
            'physical_failure_established': False, 'physical_demand_bounds_established': False,
            'physical_or_structural_release': False, 'structural_acceptance': False,
            'case_id': 'a12-forward', 'axis_id': 'eoere_bolt_067',
            'candidate_cells_per_member': 32, 'candidate_facets': 32,
            'uniform_reference_divisors': [3.2, 4., 5.], 'working_uniform_reference_divisor': 5.,
            'continuous_support_gap_tolerance': '1/1000000',
            'integration_cell_budget_per_piece': 100000, 'highs_version': '1.12.0',
            'runtime_versions': {'numpy': '2.5.2', 'scipy': '1.18.1'},
            'vector_helper': bound.current.ref(bound.vector.OWN),
            'spatial_helper': bound.current.ref(bound.vector.spatial.OWN),
            'reduction_helper': bound.current.ref(bound.reductions.OWN)}


@pytest.mark.parametrize('key,value', [('current_bolt_count', 102), ('extra_grid', True),
    ('actual_observations', {}), ('complete_joint_resistance', 1), ('physical_failure_established', True),
    ('physical_or_structural_release', True), ('physical_demand_bounds_established', True),
    ('axis_id', 'eoere_bolt_065'), ('case_id', 'a12-left'), ('working_uniform_reference_divisor', 4.),
    ('candidate_cells_per_member', 64), ('candidate_facets', 64),
    ('continuous_support_gap_tolerance', '1/10'), ('highs_version', '1.11.0')])
def test_scope_hypothesis_and_method_controls_are_not_silently_changed(key, value):
    inputs = valid_inputs()
    bound.validate(inputs)
    inputs[key] = value
    with pytest.raises(ValueError):
        bound.validate(inputs)


@pytest.mark.parametrize('helper', [bound.vector, bound.vector.spatial, bound.reductions])
def test_imported_helper_must_match_its_disk_and_input_binding(monkeypatch, helper):
    inputs = valid_inputs()
    monkeypatch.setattr(helper, 'LOADED_SHA', 'stale loaded helper')
    with pytest.raises(ValueError, match='loaded and on-disk'):
        bound.validate(inputs)


def test_own_source_drift_is_refused_before_candidate_selection(monkeypatch):
    real_sha = bound.current.sha
    monkeypatch.setattr(bound.current, 'sha', lambda p: 'changed' if p == bound.OWN else real_sha(p))
    monkeypatch.setattr(bound, 'candidate', lambda *args: pytest.fail('candidate must not run'))
    with pytest.raises(ValueError, match='changed after import'):
        bound.run()


def test_transient_intake_drift_is_refused_before_candidate_selection(monkeypatch):
    import hashlib
    import json
    original = json.dumps(valid_inputs(), sort_keys=True).encode()
    altered = original+b' '
    target = bound.current.ROOT/'transient-consumed-input.json'
    ref = {'path': target.name, 'sha256': hashlib.sha256(original).hexdigest()}
    real_ref, real_read = bound.current.ref, Path.read_bytes
    monkeypatch.setattr(bound.current, 'ref', lambda p: ref if p == bound.INPUT else real_ref(p))
    monkeypatch.setattr(Path, 'read_bytes', lambda p: altered if p == target else real_read(p))
    monkeypatch.setattr(bound, 'candidate', lambda *args: pytest.fail('candidate must not run'))
    with pytest.raises(ValueError, match='consumed JSON bytes changed'):
        bound.run()


def test_exact_reader_parses_its_bound_bytes_once(monkeypatch):
    import hashlib
    original = b'{"value": 3}\n'
    target = bound.current.ROOT/'exact-consumed-input.json'
    calls = []
    def read(path):
        assert path == target
        calls.append(path)
        return original if len(calls) == 1 else b'{"value": 4}\n'
    monkeypatch.setattr(Path, 'read_bytes', read)
    assert bound.read_exact({'path': target.name, 'sha256': hashlib.sha256(original).hexdigest()}) == {'value': 3}
    assert calls == [target]


@pytest.mark.parametrize('value,answer', [([0, 0], 0), ([3, 4], 5),
                                         ([F(1, 3), 0], F(1, 3)),
                                         ([F(1, 10**80), 0], F(1, 10**80))])
def test_outward_roots(value, answer):
    low, high = bound.norm_bounds(value)
    assert low <= answer <= high
    assert high-low <= F(1, 10**24)
    if answer == 0:
        assert high == 0
    else:
        assert high > 0


@pytest.mark.parametrize('value,length,expected', [([3, 4], 2, 10), ([0, 0], 1, 0)])
def test_uniform_vector_integrals(value, length, expected):
    low, high, count = bound.affine_norm_integral(value, value, length)
    assert low == high == expected and count == 1


def test_zero_crossing_integral_is_exact_after_one_split():
    low, high, count = bound.affine_norm_integral([-1, 0], [1, 0], 2)
    assert low == high == 1 and count == 2


@pytest.mark.parametrize('direction', [[1, 0], [0, 1], [-1, 0], [0, -1]])
def test_exact_uniform_force_limit(direction):
    result = bound.continuous_bound(fixture([2*x for x in direction], [0, 0]),
                                    {'surfaces': [{'force': direction, 'first_moment': [0, 0]}], 'cuts': []})
    assert result['exact_necessary_raw_index_lower'] == 1


def test_exact_first_moment_limit():
    result = bound.continuous_bound(fixture([0, 0], [1, 0]),
                                    {'surfaces': [{'force': [0, 0], 'first_moment': [1, 0]}], 'cuts': []})
    assert result['exact_necessary_raw_index_lower'] == 1


def test_two_sided_point_couple_has_half_cap_necessary_bound():
    data = fixture([0, 0], [0, 0])
    data['points'] = [{'s': 0, 'force': [0, 0], 'couple': [3, 0]}]
    result = bound.continuous_bound(data, {'surfaces': [{'force': [0, 0], 'first_moment': [0, 0]}],
        'cuts': [{'station': 0, 'include': False, 'nu': [1, 0]},
                 {'station': 0, 'include': True, 'nu': [-1, 0]}]})
    assert result['exact_bearing_support_lower_upper'] == (0, 0)
    assert result['exact_necessary_raw_index_lower'] == F(3, 2)


def test_point_force_rotation_and_couple_signs():
    points = [{'s': -2, 'force': [3, 7], 'couple': [11, 13]},
              {'s': 1, 'force': [17, 19], 'couple': [23, 29]}]
    assert bound.point_moment(points, 1, False) == [-32, -4]
    assert bound.point_moment(points, 1, True) == [-55, -33]


def test_smallest_own_root_moment_cap_at_transition():
    caps = [{'interval': [-1, 0], 'cap': 4}, {'interval': [0, 1], 'cap': 3}]
    assert bound.cap_at(caps, 0) == 3
    with pytest.raises(ValueError, match='own positive'):
        bound.cap_at(caps, 2)


def test_noncollinear_affine_norm_matches_independent_analytic_integral():
    import math
    expected = (math.sqrt(2)+math.asinh(1))/2
    low, high, _ = bound.affine_norm_integral([1, 0], [1, 1], 1, F(1, 10**7))
    assert float(low) <= expected <= float(high)
    assert high-low <= F(1, 10**7)


def test_integration_budget_is_not_an_acceptance_relaxation():
    with pytest.raises(ValueError, match='budget exhausted'):
        bound.affine_norm_integral([1, 0], [1, 1], 1, F(1, 10**7), 1)


def test_candidate_failure_restores_both_original_callbacks(monkeypatch):
    def fail(**kwargs):
        raise ValueError('synthetic candidate stop')
    monkeypatch.setattr(bound.vector, 'solve', fail)
    original = bound.vector.linprog, bound.vector.point_moment
    with pytest.raises(ValueError, match='candidate stop'):
        bound.candidate(fixture([0, 0], [0, 0]))
    assert (bound.vector.linprog, bound.vector.point_moment) == original


def test_full_noncollinear_virtual_work_by_independent_exact_simpson_integrals():
    # Affine densities and affine support coefficients have quadratic products,
    # so three-point Simpson integration is exact on every coefficient piece.
    specs = [([-2, -1], [1, 2], [F(1, 2), F(-1, 3)]),
             ([F(-1, 2), 1], [-2, 1], [F(2, 3), F(1, 4)]),
             ([2, 3], [2, -3], [F(-1, 4), F(1, 2)])]
    specs = [(tuple(map(F, interval)), tuple(map(F, q0)), tuple(map(F, slope)))
             for interval, q0, slope in specs]
    surfaces = []
    for (a, b), q0, slope in specs:
        span = b-a
        surfaces.append({'interval': [a, b], 'cap': 7,
                         'force': [span*x for x in q0],
                         'first_moment': [span**3*x/12 for x in slope]})
    points = [{'s': F(-5, 2), 'force': [2, -1], 'couple': [3, 4]},
              {'s': 0, 'force': [-1, 3], 'couple': [-2, 1]}]
    data = {'domain': [-3, 4], 'surfaces': surfaces, 'points': points,
            'moment_caps': [{'interval': [-3, 4], 'cap': 11}]}
    multiplier = {'surfaces': [{'force': [1, 2], 'first_moment': [3, -1]},
                              {'force': [-2, 1], 'first_moment': [1, 4]},
                              {'force': [2, -3], 'first_moment': [-1, 2]}],
                  'cuts': [{'station': F(-3, 2), 'include': True, 'nu': [2, -1]},
                           {'station': 0, 'include': False, 'nu': [-1, 3]},
                           {'station': 0, 'include': True, 'nu': [4, 2]},
                           {'station': F(5, 2), 'include': True, 'nu': [-2, 1]}]}
    result = bound.continuous_bound(data, multiplier, tolerance=F(1, 10**5))

    def density(s, spec):
        (a, b), q0, slope = spec
        return [x+(s-(a+b)/2)*y for x, y in zip(q0, slope, strict=True)]

    def simpson(fn, a, b):
        return (b-a)*(fn(a)+4*fn((a+b)/2)+fn(b))/6

    product = F(0)
    for a, b, _, first, last in result['exact_affine_support_pieces']:
        spec = next(row for row in specs if row[0][0] <= a < b <= row[0][1])
        def value(s, spec=spec, a=a, b=b, first=first, last=last):
            coefficient = [x+(s-a)*(y-x)/(b-a) for x, y in zip(first, last, strict=True)]
            return sum(x*y for x, y in zip(coefficient, density(s, spec), strict=True))
        product += simpson(value, a, b)
    moments = F(0)
    for cut in multiplier['cuts']:
        t, nu = F(cut['station']), cut['nu']
        actual = [F(0), F(0)]
        for point in points:
            if point['s'] < t or (cut['include'] and point['s'] == t):
                actual[0] -= point['force'][1]*(t-point['s'])+point['couple'][0]
                actual[1] += point['force'][0]*(t-point['s'])-point['couple'][1]
        for spec in specs:
            a, end = spec[0]
            b = min(end, t)
            if b > a:
                actual[0] -= simpson(lambda s, spec=spec, t=t: (t-s)*density(s, spec)[1], a, b)
                actual[1] += simpson(lambda s, spec=spec, t=t: (t-s)*density(s, spec)[0], a, b)
        moments += sum(n*m for n, m in zip(nu, actual, strict=True))
    assert product-moments == result['exact_virtual_work']
