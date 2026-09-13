"""Focused checks of sensitivity scope, bearing geometry and candidate identity."""
from types import SimpleNamespace

import numpy as np
import pytest

from fea.current_response_model import (
    foot_samples,
    header_bearing_points,
    leg_bolt_properties,
)
from fea.current_response_run import assess

CORNERS = np.array([[0., 0., 0.], [0., 120., 0.], [40., 0., 0.], [40., 120., 0.]])


def test_midpoint_pressure_preserves_total_stiffness_and_centroid():
    reference = foot_samples(CORNERS)
    samples = foot_samples(CORNERS, 3)
    assert len(reference) == 4 and len(samples) == 9
    assert sum(w for _, w in samples) == pytest.approx(1.)
    np.testing.assert_allclose(sum(p*w for p, w in samples), CORNERS.mean(axis=0))
    assert all(0 < p[0] < 40 and 0 < p[1] < 120 for p, _ in samples)
    # Uniform-area rotational compliance differs intentionally from end springs.
    variance = sum(w*(p[1]-60.)**2 for p, w in samples)
    assert variance == pytest.approx(120.**2/12.*(1.-1./9.))
    for (actual, weight), expected in zip(reference, CORNERS, strict=True):
        np.testing.assert_array_equal(actual, expected)
        assert weight == .25


@pytest.mark.parametrize('grid', [0, 1, 2.5, True])
def test_invalid_sampling_fails(grid):
    with pytest.raises(ValueError, match='integer at least two'):
        foot_samples(CORNERS, grid)


def test_leg_stiffness_changes_only_leg_bolt_elastic_terms():
    original = {'axial_n_per_mm': 100., 'lateral_n_per_mm': 40., 'basis': 'test'}
    modified = leg_bolt_properties(original, 'lumber_leg_left', 'base_side_left', .5)
    assert modified == {'axial_n_per_mm': 50., 'lateral_n_per_mm': 20., 'basis': 'test'}
    assert leg_bolt_properties(original, 'base_header', 'base_side_left', .5) is original
    assert original['axial_n_per_mm'] == 100.
    for bad in (0., -1., float('nan'), float('inf')):
        with pytest.raises(ValueError, match='positive and finite'):
            leg_bolt_properties(original, 'lumber_leg_left', 'base_side_left', bad)


def test_header_bearing_clips_overhang_without_moving_reference_corners():
    class Header:
        def __init__(self, ymax):
            self.ymax = ymax

        def BoundingBox(self):
            return SimpleNamespace(xmin=-10., xmax=50., ymin=0., ymax=self.ymax, zmax=0.)

    unchanged = header_bearing_points(CORNERS, Header(150.))
    np.testing.assert_array_equal(unchanged, CORNERS)
    clipped = header_bearing_points(CORNERS, Header(90.))
    np.testing.assert_array_equal(clipped, [[0., 0., 0.], [0., 90., 0.], [40., 0., 0.], [40., 90., 0.]])
    with pytest.raises(ValueError, match='positive-area'):
        header_bearing_points(CORNERS, Header(-1.))


def test_default_assessment_rejects_alternative_candidate_without_opt_in():
    with pytest.raises(ValueError, match='Require the current candidate'):
        assess({'candidate': 'leg-mvp-development', 'elements': {}}, '', '', '')
    with pytest.raises(ValueError, match='Require the current candidate'):
        assess({'candidate': 'no-shoes-development', 'elements': {}}, '', '', '',
               expected_candidate='leg-mvp-development')


def test_header_corner_matching_tolerates_reversed_float_sort_order():
    header = SimpleNamespace(BoundingBox=lambda: SimpleNamespace(
        xmin=-10., xmax=50., ymin=-10., ymax=150., zmax=0.))
    noisy = CORNERS.copy()
    noisy[0, 0] += 1.e-10
    noisy[3, 0] -= 1.e-10
    actual = header_bearing_points(noisy, header)
    # A fully supported old member must retain exact points and input order.
    np.testing.assert_array_equal(actual, noisy)
    malformed = noisy.copy()
    malformed[0, 0] += 1.
    with pytest.raises(ValueError, match='axis-aligned rectangular'):
        header_bearing_points(malformed, header)
