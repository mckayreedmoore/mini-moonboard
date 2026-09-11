"""Replay all split-center shell evidence and verify current screw/grid identity."""
import hashlib
import json
import numbers
import tarfile
from pathlib import Path

import pytest

from fea import split_center_panel_comparison as comparison
from mini_moonboard import split_center_frame, vertical_principal_frame


def assert_metrics(actual, expected):
    """Keep identities/flags exact while tolerating serialized numerical roundoff."""
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key, value in expected.items():
            assert_metrics(actual[key], value)
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected, strict=True):
            assert_metrics(a, e)
    elif isinstance(expected, bool) or expected is None:
        assert actual is expected
    elif isinstance(expected, numbers.Real):
        assert actual == pytest.approx(expected, rel=1e-10, abs=1e-10)
    else:
        assert actual == expected


def test_archived_split_center_panel_evidence_replays():
    shell = comparison.shell
    modules = {module.KEY: module for module in (vertical_principal_frame, split_center_frame)}
    cases_by_label = {case[2]: case for case in comparison.CASES}
    assert set(cases_by_label) == {'D6', 'D7', 'H6', 'H7', 'F3', 'F10', 'G3', 'G10'}
    with tarfile.open('fea/results/split-center-panel-comparison-v1.tar.gz') as archive:
        members = [member.name for member in archive.getmembers() if member.isfile()]
        assert len(members) == len(set(members))

        def read(name):
            return archive.extractfile(name).read()

        report = json.loads(read('report.json'))
        assert report['baseline'] == vertical_principal_frame.KEY
        assert report['revised'] == split_center_frame.KEY
        assert report['solver_image'] == shell.IMAGE
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert report[flag] is False
        assert {'fea/split_center_panel_comparison.py', 'fea/vertical_panel_comparison.py',
                'mini_moonboard/split_center_frame.py'} <= report['source_sha256'].keys()
        assert {name for name in members if name.startswith('source_snapshots/')} == {
            'source_snapshots/'+name for name in report['source_sha256']}
        for name, sha in report['source_sha256'].items():
            assert hashlib.sha256(read('source_snapshots/'+name)).hexdigest() == sha, name
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name

        cases = report['cases']
        assert len(cases) == 32
        assert {(case['candidate'], case['case_id'], case['mesh_mm']) for case in cases} == {
            (candidate, label, size) for candidate in modules
            for label in cases_by_label for size in shell.SIZES}
        jobs = [('benchmark', report['benchmark'])]+[
            (f"{case['candidate']}-{case['case_id']}-{case['mesh_mm']:g}", case) for case in cases]
        assert {name.split('/')[0] for name in members} == {
            'report.json', 'source_snapshots', *(directory for directory, _ in jobs)}
        metadata = {'candidate', 'case_id', 'panel', 'load_family', 'mesh_mm', 'patch_mm',
                    'projected_load_cases', 'applied_normal_force_n', 'linear_250_over_300_scale'}
        for directory, saved in jobs:
            result = json.loads(read(directory+'/result.json'))
            assert result['qualified_for_design'] is False
            assert_metrics(result, {key: value for key, value in saved.items() if key not in metadata})
            evidence = result['evidence_sha256']
            assert {'input.json', 'panel.inp', 'panel.dat', 'panel.log'} <= evidence.keys()
            assert {name for name in members if name.startswith(directory+'/')} == {
                directory+'/'+name for name in evidence} | {directory+'/result.json'}
            for name, sha in evidence.items():
                assert hashlib.sha256(read(directory+'/'+name)).hexdigest() == sha, (directory, name)
            record = json.loads(read(directory+'/input.json'))
            for field in ('nodes', 'elements', 'loads'):
                record[field] = {int(key): value for key, value in record[field].items()}
            assert shell.deck(record).encode() == read(directory+'/panel.inp')
            data = read(directory+'/panel.dat').decode()
            if directory == 'benchmark':
                assert record['candidate'] == 'cantilever-benchmark'
                assert result['benchmark_relative_error'] <= .03
                replay = shell.assess(record, data)
            else:
                module = modules[saved['candidate']]
                case = cases_by_label[saved['case_id']]
                assert record['candidate'] == module.KEY
                assert record['case_id'] == case[2]
                assert record['panel'] == saved['panel'] == f'main_{case[0]}_{case[1]}'
                assert record['load_family'] == saved['load_family'] == case[3]
                assert record['mesh_max_mm'] == saved['mesh_mm']
                for key in metadata-{'mesh_mm'}:
                    assert_metrics(record[key], saved[key])
                assert record['applied_climber_lb_sensitivity'] == 300
                assert record['patch_area_mm2'] == pytest.approx(400.)
                x, y = comparison.panel_grid_v2.main_tnut_datums()[case[2]]
                x -= module.b.HALF
                assert record['patch_mm'] == pytest.approx([x-10., x+10., y-10., y+10.])
                assert sum(record['loads'].values()) == pytest.approx(record['applied_normal_force_n'])
                assert sum(record['nodes'][t][0]*v for t, v in record['loads'].items()) == pytest.approx(
                    x*record['applied_normal_force_n'])
                assert sum(record['nodes'][t][1]*v for t, v in record['loads'].items()) == pytest.approx(
                    y*record['applied_normal_force_n'])
                projected = record['projected_load_cases']
                for pounds in (250, 300):
                    world = [0., 300., -2*pounds*.45359237*9.80665]
                    assert projected[str(pounds)]['world_force_n'] == pytest.approx(world)
                    assert projected[str(pounds)]['outward_normal_projection_n'] == pytest.approx(
                        sum(v*n for v, n in zip(world, (-module.b.normal()).toTuple(), strict=True)))
                assert record['linear_250_over_300_scale'] == pytest.approx(
                    projected['250']['outward_normal_projection_n']/projected['300']['outward_normal_projection_n'])
                screws = {c.name: c for c in module.connections()
                          if isinstance(c, module.timber.PanelScrew) and c.members[0] == record['panel']}
                assert set(record['screw_nodes']) == screws.keys()
                along = (module.b.point(0, 1, 0)-module.b.point(0, 0, 0)).normalized()
                for name, tag in record['screw_nodes'].items():
                    c = screws[name]
                    assert record['nodes'][tag] == pytest.approx([
                        c.start.x, (c.start-module.b.point(0, 0, 0)).dot(along), 0.])
                assert {t for t, dof in record['constraints'] if dof == 3} == set(record['screw_nodes'].values())
                assert len(record['constraints']) == len(screws)+3
                replay = comparison.assess(record, data)
                assert max(map(abs, result['moment_residual_nmm'])) <= 2.
            assert max(map(abs, result['force_residual_n'])) <= .1
            assert_metrics(replay, {key: value for key, value in result.items() if key != 'evidence_sha256'})

        assessed = comparison.comparison_summary(cases, report['baseline'], report['revised'])
        assert_metrics(assessed, report['comparison'])
        checks = assessed['refinement_checks']
        assert len(checks) == 16
        assert assessed['numerical_comparison_accepted'] is all(r['passes_5_percent_refinement'] for r in checks)
        accepted_labels = {label for label in cases_by_label
                           if all(row['passes_5_percent_refinement'] for row in checks if row['case_id'] == label)}
        assert {row['case_id'] for row in assessed['accepted_case_surrogate_ratios']} == accepted_labels
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert assessed[flag] is False
