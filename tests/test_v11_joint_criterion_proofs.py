"""Portable, exact-arithmetic replay of the published bearing certificates."""

import gzip
import hashlib
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def binary_fraction(value):
    return Fraction.from_float(float(value))


def stored_fraction(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def assessment():
    entry = json.loads((ROOT / 'docs/bolted-frame-development/development-revisions.json').read_text())['owner_authorized_shorter_bolt_trial']
    ref = entry['joint_criterion_followthrough']
    encoded = (ROOT / ref['path']).read_bytes()
    assert hashlib.sha256(encoded).hexdigest() == ref['sha256']
    decoded = gzip.decompress(encoded)
    assert len(decoded) == ref['decoded_bytes']
    assert hashlib.sha256(decoded).hexdigest() == ref['decoded_sha256']
    return json.loads(decoded)


def replay(certificate):
    """Test the equilibrium/support inequality, independently of the LP/search."""
    v = list(map(binary_fraction, certificate['dual_direction']))
    center = binary_fraction(certificate['center_station_mm'])
    station = binary_fraction(certificate['dual_station_mm'])
    force = list(map(binary_fraction, certificate['source_force']))
    first = list(map(binary_fraction, certificate['source_first_moment']))
    functional = sum(v[k] * (first[k] + (center - station) * force[k]) for k in range(2))
    support = Fraction(0)
    for region in certificate['regions']:
        matrix = [[binary_fraction(x) for x in row] for row in region['declared_ellipse_map']]
        transformed = [sum(matrix[k][j] * v[k] for k in range(2)) for j in range(2)]
        square = sum(value * value for value in transformed)
        upper = binary_fraction(region['support_norm_upper'])
        assert upper >= 0 and upper * upper >= square
        assert square == stored_fraction(region['exact_norm_squared'])
        a, b = map(binary_fraction, region['interval_mm'])
        assert b > a
        if a <= station <= b:
            integral = ((station - a) ** 2 + (b - station) ** 2) / 2
        else:
            integral = abs((b - station) ** 2 - (a - station) ** 2) / 2
        assert integral == stored_fraction(region['exact_integral_abs_s_minus_t'])
        support += upper * integral
    assert functional == stored_fraction(certificate['equilibrium_functional_exact'])
    assert support == stored_fraction(certificate['support_integral_upper_exact'])
    assert support > 0 and functional > support
    assert binary_fraction(certificate['certified_continuous_lower_bound']) <= functional / support
    assert certificate['reference_threshold_one_exactly_exceeded'] is True
    return functional / support


def test_five_published_support_certificates_hold_for_all_continuous_fields_within_declared_caps():
    data = assessment()
    rows = data['continuous_rear_bearing']['case_rows']
    certificates = data['continuous_rear_bearing']['exact_exceedance_certificates']
    assert len(rows) == 48 and len(certificates) == 5
    assert len({(r['axis_id'], r['case_id'], r['host']) for r in rows}) == 48
    for certificate in certificates:
        lower = replay(certificate)
        assert lower <= binary_fraction(certificate['finite_witness_index'])
    assert data['accepted_connection_exceedance_count'] is None
    assert data['complete_joint_capacity'] is None
    assert data['structural_acceptance'] is False


@pytest.mark.parametrize('change', ['force', 'norm', 'integral', 'bound'])
def test_exact_support_replay_rejects_changed_demands_caps_or_strength_claim(change):
    certificate = deepcopy(assessment()['continuous_rear_bearing']['exact_exceedance_certificates'][0])
    if change == 'force':
        certificate['source_force'][0] += 1
    elif change == 'norm':
        certificate['regions'][0]['support_norm_upper'] /= 2
    elif change == 'integral':
        certificate['regions'][0]['exact_integral_abs_s_minus_t']['numerator'] = '0'
    else:
        certificate['certified_continuous_lower_bound'] *= 2
    with pytest.raises(AssertionError):
        replay(certificate)
