"""Replay archived shell output without rerunning the solver or claiming capacity."""
import hashlib
import json
import numbers
import tarfile
from pathlib import Path

import pytest

from fea import vertical_panel_comparison as model


def assert_metrics(actual, expected):
    """Compare nested numerical output while keeping identities and flags exact."""
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key, value in expected.items():
            assert_metrics(actual[key], value)
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected, strict=True):
            assert_metrics(a, e)
    elif isinstance(expected, bool) or expected is None:
        assert actual is expected
    elif isinstance(expected, numbers.Real):
        assert actual == pytest.approx(expected, rel=1e-10, abs=1e-10)
    else:
        assert actual == expected


def test_archived_vertical_panel_evidence_replays():
    with tarfile.open('fea/results/vertical-panel-comparison-v1.tar.gz') as archive:
        members = [member.name for member in archive.getmembers() if member.isfile()]
        assert len(members) == len(set(members))

        def read(name):
            return archive.extractfile(name).read()

        report = json.loads(read('report.json'))
        assert report['solver_image'] == model.IMAGE
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert report[flag] is False
        assert 'fea/vertical_panel_comparison.py' in report['source_sha256']
        assert {name for name in members if name.startswith('source_snapshots/')} == {
            'source_snapshots/'+name for name in report['source_sha256']}
        for name, sha in report['source_sha256'].items():
            assert hashlib.sha256(read('source_snapshots/'+name)).hexdigest() == sha, name
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name

        cases = report['cases']
        assert len(cases) == 8
        assert {(case['candidate'], case['band'], case['mesh_mm']) for case in cases} == {
            (candidate, band, size) for candidate in (
                'paired-rail-base-development', 'vertical-principal-development')
            for band in ('lower', 'upper') for size in model.SIZES}
        jobs = [('benchmark', report['benchmark'])]+[
            (f"{case['candidate']}-{case['band']}-{case['mesh_mm']:g}", case) for case in cases]
        assert {name.split('/')[0] for name in members} == {
            'report.json', 'source_snapshots', *(directory for directory, _ in jobs)}
        for directory, saved in jobs:
            result = json.loads(read(directory+'/result.json'))
            assert result['qualified_for_design'] is False
            assert_metrics(result, {key: value for key, value in saved.items()
                                    if key not in ('candidate', 'band', 'mesh_mm')})
            evidence = result['evidence_sha256']
            assert {'input.json', 'panel.inp', 'panel.dat', 'panel.log'} <= evidence.keys()
            assert {name for name in members if name.startswith(directory+'/')} == {
                directory+'/'+name for name in evidence} | {directory+'/result.json'}
            for name, sha in evidence.items():
                assert hashlib.sha256(read(directory+'/'+name)).hexdigest() == sha, (directory, name)
            record = json.loads(read(directory+'/input.json'))
            for field in ('nodes', 'elements', 'loads'):
                record[field] = {int(key): value for key, value in record[field].items()}
            if directory == 'benchmark':
                assert record['candidate'] == 'cantilever-benchmark'
                assert result['benchmark_relative_error'] <= .03
            else:
                assert record['candidate'] == saved['candidate']
                assert record['panel'] == f"main_{saved['band']}_left"
                assert record['mesh_max_mm'] == saved['mesh_mm']
            assert model.deck(record).encode() == read(directory+'/panel.inp')
            replay = model.assess(record, read(directory+'/panel.dat').decode())
            assert_metrics(replay, {key: value for key, value in result.items() if key != 'evidence_sha256'})
        comparison = model.comparison_summary(cases)
        assert_metrics(comparison, report['comparison'])
        accepted = all(row['passes_5_percent_refinement'] for row in comparison['refinement_checks'])
        assert comparison['numerical_comparison_accepted'] is accepted
        assert len(comparison['fine_mesh_surrogate_ratios']) == (2 if accepted else 0)
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert comparison[flag] is False
