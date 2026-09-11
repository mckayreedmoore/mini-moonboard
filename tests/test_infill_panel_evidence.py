"""Replay all infill shell evidence and verify current screw/grid identity."""
import hashlib
import json
import math
import numbers
import shutil
import tarfile
from pathlib import Path

import pytest

from fea import infill_panel_comparison as comparison
from mini_moonboard import infill_panel_frame, split_center_frame


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


def test_archived_infill_panel_evidence_replays(tmp_path):
    shell = comparison.shell
    modules = {module.KEY: module for module in (split_center_frame, infill_panel_frame)}
    cases_by_label = {case[2]: case for case in comparison.CASES}
    assert set(cases_by_label) == {'D6', 'D7', 'H6', 'H7', 'F3', 'F10', 'G3', 'G10'}
    # Stream xz once; repeated random archive reads decompress the large raw DATs.
    with tarfile.open('fea/results/infill-panel-comparison-v1.tar.xz', mode='r|xz') as archive:
        members = []
        for member in archive:
            path = Path(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            assert member.isfile() or member.isdir()
            if not member.isfile():
                continue
            members.append(member.name)
            target = tmp_path/path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                shutil.copyfileobj(archive.extractfile(member), output)
        assert len(members) == len(set(members))

        def read(name):
            return (tmp_path/name).read_bytes()

        report = json.loads(read('report.json'))
        sizes = report['mesh_sizes_mm']
        assert len(sizes) == 2
        assert all(isinstance(size, numbers.Real) and not isinstance(size, bool)
                   and math.isfinite(size) and size > 0 for size in sizes)
        assert sizes[0] > sizes[1]
        assert report['baseline'] == split_center_frame.KEY
        assert report['revised'] == infill_panel_frame.KEY
        assert report['solver_image'] == shell.IMAGE
        assert report['fresh_solver_jobs'] == 0
        reused = {row['job']: row for row in report['reused_jobs']}
        assert len(reused) == len(report['reused_jobs']) == 33
        assert all(row['fresh_solver_run'] is False for row in reused.values())
        assert len({row['source_report_sha256'] for row in reused.values()}) == 1
        for row in reused.values():
            assert len(row['source_report_sha256']) == len(row['source_result_sha256']) == 64
            int(row['source_report_sha256'], 16)
            int(row['source_result_sha256'], 16)
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert report[flag] is False
        assert {'fea/infill_panel_comparison.py', 'fea/split_center_panel_comparison.py', 'fea/vertical_panel_comparison.py',
                'mini_moonboard/split_center_frame.py', 'mini_moonboard/infill_panel_frame.py'} <= report['source_sha256'].keys()
        assert {name for name in members if name.startswith('source_snapshots/')} == {
            'source_snapshots/'+name for name in report['source_sha256']}
        for name, sha in report['source_sha256'].items():
            assert hashlib.sha256(read('source_snapshots/'+name)).hexdigest() == sha, name
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name

        cases = report['cases']
        assert len(cases) == 32
        assert {(case['candidate'], case['case_id'], case['mesh_mm']) for case in cases} == {
            (candidate, label, size) for candidate in modules
            for label in cases_by_label for size in sizes}
        jobs = [('benchmark', report['benchmark'])]+[
            (f"{case['candidate']}-{case['case_id']}-{case['mesh_mm']:g}", case) for case in cases]
        assert reused.keys() == {directory for directory, _ in jobs}
        assert {name.split('/')[0] for name in members} == {
            'report.json', 'source_snapshots', *(directory for directory, _ in jobs)}
        metadata = {'candidate', 'case_id', 'panel', 'load_family', 'mesh_mm', 'patch_mm',
                    'projected_load_cases', 'applied_normal_force_n', 'linear_250_over_300_scale',
                    'controlling_ideal_screw', 'controlling_signed_reaction_n'}
        for directory, saved in jobs:
            result = json.loads(read(directory+'/result.json'))
            assert result['qualified_for_design'] is False
            assert_metrics(result, {key: value for key, value in saved.items() if key not in metadata})
            evidence = result['evidence_sha256']
            for provenance, artifact in (('source_input_sha256', 'input.json'),
                                         ('source_deck_sha256', 'panel.inp'),
                                         ('source_dat_sha256', 'panel.dat'),
                                         ('source_log_sha256', 'panel.log')):
                assert reused[directory][provenance] == evidence[artifact]
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
                for key in metadata-{'mesh_mm', 'controlling_ideal_screw', 'controlling_signed_reaction_n'}:
                    assert_metrics(record[key], saved[key])
                assert record['applied_climber_lb_sensitivity'] == 300
                assert record['patch_area_mm2'] == pytest.approx(400.)
                x, y = comparison.previous.panel_grid_v2.main_tnut_datums()[case[2]]
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
                reactions = replay['ideal_screw_normal_reactions_n']
                controller = max(reactions, key=lambda name: abs(reactions[name]))
                assert saved['controlling_ideal_screw'] == controller
                assert saved['controlling_signed_reaction_n'] == pytest.approx(reactions[controller])
                assert max(map(abs, result['moment_residual_nmm'])) <= 2.
            assert max(map(abs, result['force_residual_n'])) <= .1
            assert_metrics(replay, {key: value for key, value in result.items() if key != 'evidence_sha256'})

        assessed = comparison.comparison_summary(cases, report['baseline'], report['revised'])
        assert_metrics(assessed, report['comparison'])
        assert assessed['mesh_sizes_mm'] == sizes
        checks = assessed['refinement_checks']
        assert len(checks) == 16
        reaction_checks = assessed['reaction_refinement_checks']
        assert {(row['candidate'], row['case_id']) for row in reaction_checks} == {
            (candidate, label) for candidate in modules for label in cases_by_label}
        assert len(reaction_checks) == 16
        indexed = {(row['candidate'], row['case_id'], row['mesh_mm']): row for row in cases}
        for row in reaction_checks:
            coarse, fine = (indexed[row['candidate'], row['case_id'], size]['ideal_screw_normal_reactions_n']
                            for size in sizes)
            individual = row['individual_reactions']
            assert {item['connection'] for item in individual} == coarse.keys() == fine.keys()
            assert len(individual) == len(fine)
            for item in individual:
                name = item['connection']
                change = abs(coarse[name]-fine[name])
                tolerance = max(.5, .05*abs(fine[name]))
                assert item['coarse_signed_normal_n'] == pytest.approx(coarse[name])
                assert item['fine_signed_normal_n'] == pytest.approx(fine[name])
                assert item['absolute_change_n'] == pytest.approx(change)
                assert item['numerical_tolerance_n'] == pytest.approx(tolerance)
                assert item['passed'] is (change <= tolerance)
            controllers = [max(values, key=lambda name: abs(values[name])) for values in (coarse, fine)]
            assert row['coarse_controlling_connection'] == controllers[0]
            assert row['fine_controlling_connection'] == controllers[1]
            assert row['controlling_identity_changed'] is (controllers[0] != controllers[1])
            assert row['all_individual_reactions_converged'] is all(item['passed'] for item in individual)
        accepted = all(r['passes_5_percent_refinement'] for r in checks) and all(
            r['all_individual_reactions_converged'] for r in reaction_checks)
        assert assessed['numerical_comparison_accepted'] is accepted
        accepted_labels = {label for label in cases_by_label
                           if all(row['passes_5_percent_refinement'] for row in checks if row['case_id'] == label)
                           and all(row['all_individual_reactions_converged']
                                   for row in reaction_checks if row['case_id'] == label)}
        assert {row['case_id'] for row in assessed['accepted_case_surrogate_ratios']} == accepted_labels
        for row in assessed['accepted_case_surrogate_ratios']:
            coarse, revised = (indexed[candidate, row['case_id'], min(sizes)]
                               for candidate in (report['baseline'], report['revised']))
            peaks = [max(map(abs, case['ideal_screw_normal_reactions_n'].values())) for case in (coarse, revised)]
            assert row['revised_over_baseline_peak_ideal_reaction'] == pytest.approx(peaks[1]/peaks[0])
        for flag in ('qualified_for_design', 'actual_panel_qualified', 'gusset_force_reduction_established'):
            assert assessed[flag] is False
