"""Published narrow-panel reference and the formerly missed kicker comparison."""

import hashlib
import json
import math

import pytest

from scripts.eoere_panel_size_reference import ROOT, adjusted_reference, size_factor


@pytest.mark.parametrize('inches,expected', [(4, .5), (8, .5004), (16, .7508), (24, 1), (48, 1)])
def test_published_panel_size_reference_cases(inches, expected):
    assert size_factor(inches * 25.4) == pytest.approx(expected)


def test_recorded_right_kicker_changes_from_below_to_above_reference():
    # Actual saved a12-forward kicker_right bending-x peak and base reference.
    corrected = adjusted_reference(186.5179764884001, 287.28097931890727,
                                   [276.906732627469, 277.])
    assert corrected['base_ratio_CD1'] == pytest.approx(.6492527870470278)
    assert corrected['Cs_bounds'][1] == pytest.approx(.5913425196850394)
    assert corrected['adjusted_reference_bounds_per_mm_width_CD1'][1] == pytest.approx(169.8814581680283)
    assert corrected['adjusted_ratio_bounds_CD1'][0] == pytest.approx(1.0979301596523663)
    assert corrected['definite_adjusted_reference_exceedance'] is True


def test_full_width_reference_and_strict_equality_are_retained():
    corrected = adjusted_reference(500., 500., [609.6, 1219.2])
    assert corrected['Cs_bounds'] == [1., 1.]
    assert corrected['adjusted_ratio_bounds_CD1'] == [1., 1.]
    assert corrected['definite_adjusted_reference_exceedance'] is False


def test_rule_boundary_interval_encloses_rounded_coefficient_jumps():
    corrected = adjusted_reference(1., 1., [7.9*25.4, 24.1*25.4])
    assert corrected['Cs_bounds'][0] == .5
    assert corrected['Cs_bounds'][1] == pytest.approx(1.0012)


@pytest.mark.parametrize('width', [0., -1., math.nan, math.inf])
def test_invalid_width_is_rejected(width):
    with pytest.raises(ValueError):
        size_factor(width)


@pytest.mark.parametrize('peak,reference,bounds', [(1., 0., [100., 200.]),
    (-1., 1., [100., 200.]), (1., 1., [200., 100.]), (math.inf, 1., [100., 200.])])
def test_invalid_comparison_is_rejected(peak, reference, bounds):
    with pytest.raises(ValueError):
        adjusted_reference(peak, reference, bounds)


def test_issued_correction_binds_current_sources_and_retains_holds():
    index = json.loads((ROOT/'docs/bolted-frame-development/development-revisions.json').read_text())
    while 'reference_corrections' not in index:
        index = index['preceding_revision']
    ref = index['reference_corrections']['panel_size']
    raw = (ROOT/ref['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ref['sha256']
    report = json.loads(raw)
    assert report['components'] == index['current_response']['components']
    producer = report['producer']
    assert hashlib.sha256((ROOT/producer['path']).read_bytes()).hexdigest() == producer['sha256']
    assert report['sampled_panel_comparisons'] == 144
    assert len(report['affected_bending_rows']) == 12
    assert report['original_base_reference_exceedance_count'] == 26
    assert report['size_adjusted_definite_exceedance_count'] == report['size_adjusted_possible_exceedance_count'] == 27
    assert [(r['case_id'], r['panel'], r['component']) for r in report['newly_exceeded_rows']] == [
        ('a12-forward', 'kicker_right', 'bending_x')]
    for row in report['affected_bending_rows']:
        expected = adjusted_reference(row['peak_abs_resultant'], row['base_reference_per_mm_width_CD1'], row['width_bounds_mm'])
        assert all(row[key] == value for key, value in expected.items())
    assert report['structural_acceptance'] is False and report['complete_panel_resistance'] is None
    assert report['field_or_operator_changed'] is False and report['frozen_report_rewritten'] is False
