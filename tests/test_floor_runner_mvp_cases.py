"""Authenticate partial fresh cases without treating them as a six-case release."""
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.clear_space_case_contract import validate_case_identity
from scripts.floor_flush_checks import FROZEN_ADOPTED_CRITERIA

ROOT = Path(__file__).resolve().parents[1]
CASES = {'a12-left': ('A12', (-300., 0.)), 'a12-rear': ('A12', (0., 300.)),
         'a12-forward': ('A12', (0., -300.)), 'k12-right': ('K12', (300., 0.)),
         'k12-rear': ('K12', (0., 300.)), 'a1-rear': ('A1', (0., 300.))}


@pytest.mark.parametrize('case', CASES)
def test_saved_fresh_no_slip_case_is_source_authenticated_and_partial(case):
    root = ROOT/'fea/results/floor-runner-mvp'/case
    manifest = json.loads((root/'manifest.json').read_text())
    assert manifest['candidate'] == 'compact-floor-flush-development'
    assert set(manifest['files']) == {
        'report.json.gz', 'geometry.json', 'sources.zip', 'checks.json',
        'flush-checks.json'}
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected
    native = gzip.decompress((root/'report.json.gz').read_bytes())
    assert hashlib.sha256(native).hexdigest() == manifest['native_report_sha256']
    report = json.loads(native)
    hold, force = CASES[case]
    validate_case_identity(report, expected_candidate=manifest['candidate'],
                           expected_hold=hold, expected_pounds=250.,
                           expected_horizontal_force=force)
    with ZipFile(root/'sources.zip') as sources:
        assert set(sources.namelist()) == set(report['source_sha256'])
        for name, expected in report['source_sha256'].items():
            assert hashlib.sha256(sources.read(name)).hexdigest() == expected
    assessment = json.loads((root/'flush-checks.json').read_text())
    assert assessment['qualified_for_design'] is False
    assert set(assessment['criteria']) == FROZEN_ADOPTED_CRITERIA
    assert all(assessment['criteria'].values())
    relative = root.relative_to(ROOT)
    assert assessment['assessment_input_sha256'][str(relative/'report.json.gz')] == manifest[
        'files']['report.json.gz']
    assert assessment['assessment_input_sha256'][str(relative/'geometry.json')] == manifest[
        'files']['geometry.json']
