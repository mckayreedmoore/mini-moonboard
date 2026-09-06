"""The observer source delta must be exactly the declared two-file patch."""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from fea.mortar_observer_build.publish import require_comparison_coverage
from fea.mortar_observer_build.record_build import verify_sources


def evidence():
    original = {'stressmortar.c': 'original-stress', 'nonlingeo.c': 'original-nonlinear'}
    patched = {'stressmortar.c': 'patched-stress', 'nonlingeo.c': 'patched-nonlinear'}
    prefix = './CalculiX/ccx_2.21/src/'
    upstream = {prefix+k: v for k, v in original.items()} | {prefix+'unchanged.f': 'unchanged'}
    measured = upstream | {prefix+k: v for k, v in patched.items()}
    return upstream, {'source_sha256': original, 'patched_sha256': patched}, measured


def test_exact_two_file_delta():
    upstream, patch, measured = evidence()
    assert len(verify_sources(upstream, patch, measured)) == 2


def comparison_runs():
    return [{'case': case, 'binary': binary, 'exit_code': 0}
            for case in ('mortar_0p25', 'mortar_0p125') for binary in ('upstream', 'observer')]


def test_complete_successful_comparison_inventory():
    require_comparison_coverage(comparison_runs())


@pytest.mark.parametrize('corruption', ['empty', 'missing', 'duplicate', 'extra', 'failed', 'boolean_exit'])
def test_publication_rejects_incomplete_or_failed_comparisons(corruption):
    runs = comparison_runs()
    if corruption == 'empty':
        runs = []
    elif corruption == 'missing':
        runs.pop()
    elif corruption == 'duplicate':
        runs[-1] = runs[0]
    elif corruption == 'extra':
        runs.append(runs[0])
    else:
        runs[-1]['exit_code'] = False if corruption == 'boolean_exit' else 7
    with pytest.raises(ValueError, match='four unique successful'):
        require_comparison_coverage(runs)


@pytest.mark.parametrize('corruption', ['extra', 'missing', 'changed_other', 'wrong_parent', 'third_patch'])
def test_unexplained_source_changes_rejected(corruption):
    upstream, patch, measured = evidence()
    key = './CalculiX/ccx_2.21/src/unchanged.f'
    if corruption == 'extra':
        measured['extra.c'] = 'extra'
    elif corruption == 'missing':
        del measured[key]
    elif corruption == 'changed_other':
        measured[key] = 'modified'
    elif corruption == 'wrong_parent':
        patch['source_sha256']['stressmortar.c'] = 'wrong'
    else:
        patch['source_sha256']['unchanged.f'] = 'unchanged'
        patch['patched_sha256']['unchanged.f'] = 'new'
        measured[key] = 'new'
    with pytest.raises(ValueError):
        verify_sources(upstream, patch, measured)


@pytest.mark.parametrize('timeout', [False, True])
def test_launcher_preserves_failed_build_and_exits_nonzero(monkeypatch, tmp_path, timeout):
    from fea.mortar_observer_build import build
    root = tmp_path/'observer_build'
    root.mkdir()
    for name in ('Dockerfile', 'record_build.py'):
        (root/name).write_text('test-only fixture')
    (tmp_path/'mortar_observer').mkdir()
    (tmp_path/'mortar_observer/patch.py').write_text('test-only fixture')
    parent = 'sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0'
    monkeypatch.setattr(build, 'ROOT', root)
    monkeypatch.setattr(build, 'verified_image', lambda: (parent, {}))

    def run(command, **kwargs):
        if command[1] == 'build':
            assert kwargs['timeout'] == 300
            kwargs['stdout'].write('failed compiler evidence\n')
            if timeout:
                raise subprocess.TimeoutExpired(command, 300)
            return subprocess.CompletedProcess(command, 7)
        if build.BASE_TAG in command:
            return subprocess.CompletedProcess(command, 0, parent+'\n')
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(build.subprocess, 'run', run)
    with pytest.raises(SystemExit) as failure:
        build.main()
    assert failure.value.code == (124 if timeout else 7)
    records = list(root.glob('build-*/build_result.json'))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record['exit_code'] == failure.value.code
    assert (records[0].parent/'build.log').read_text() == 'failed compiler evidence\n'


def test_published_observer_evidence_and_replay_are_bound():
    from fea.mortar_observer_replay import replay
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root/'fea/mortar_observer_build/report.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for group in ('sources_sha256', 'evidence_sha256'):
        for name, expected in report[group].items():
            assert sha(root/name) == expected
    build = json.loads((root/report['build_directory']/'build_result.json').read_text())
    assert build['exit_code'] == 0 and build['image_id'] == report['observer_image_id']
    for name, expected in build['evidence_sha256'].items():
        assert sha(root/report['build_directory']/name) == expected
    comparison = json.loads((root/report['cube_directory']/'report.json').read_text())
    assert len(comparison['runs']) == 4
    for run in comparison['runs']:
        directory = root/report['cube_directory']/(run['case']+'-'+run['binary'])
        for name, expected in run['output_sha256'].items():
            assert sha(directory/name) == expected
        assert run['accepted_history_equal_to_archive']
        assert not any(run['maximum_printed_difference_from_archive'].values())
    assert [(c['calls'], c['accepted_increments']) for c in report['cases']] == [(28, 8), (45, 16)]
    for case in report['cases']:
        directory = root/report['cube_directory']/(case['case']+'-observer')
        result = replay((directory/'cube.log').read_text(), (directory/'cube.sta').read_text())
        assert sha(root/case['replay']) == case['replay_sha256']
        assert json.loads((root/case['replay']).read_text()) == result
        assert len(result['calls']) == case['calls']
        assert len(result['accepted_call_ids']) == case['accepted_increments']
        assert result['accepted_override_call_ids'] == case['accepted_override_call_ids'] == []
