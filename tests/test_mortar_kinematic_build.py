"""Default-CI coverage of v2 build guards and actual retained solver evidence."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from fea.mortar_kinematic_build import build
from fea.mortar_kinematic_build.record_build import sha, verify_sources


@pytest.mark.parametrize('timeout', [False, True])
def test_failed_build_is_preserved_and_propagated(monkeypatch, tmp_path, timeout):
    root = tmp_path/'build_support'
    root.mkdir()
    for name in ('Dockerfile', 'record_build.py'):
        (root/name).write_text('fixture')
    (tmp_path/'mortar_observer').mkdir()
    for name in ('patch.py', 'kinematic_patch.py'):
        (tmp_path/'mortar_observer'/name).write_text('fixture')
    parent = 'sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0'
    monkeypatch.setattr(build, 'ROOT', root)
    monkeypatch.setattr(build, 'verified_image', lambda: (parent, {}))
    def run(command, **kwargs):
        if command[1] == 'build':
            assert kwargs['timeout'] == 300
            kwargs['stdout'].write('compiler failed\n')
            if timeout:
                raise subprocess.TimeoutExpired(command, 300)
            return subprocess.CompletedProcess(command, 7)
        if build.BASE_TAG in command:
            return subprocess.CompletedProcess(command, 0, parent+'\n')
        return subprocess.CompletedProcess(command, 1)
    monkeypatch.setattr(build.subprocess, 'run', run)
    with pytest.raises(SystemExit) as error:
        build.main()
    assert error.value.code == (124 if timeout else 7)
    report, = root.glob('build-*/build_result.json')
    assert json.loads(report.read_text())['exit_code'] == error.value.code
    assert (report.parent/'context/patch.py').exists()
    assert (report.parent/'context/kinematic_patch.py').exists()


def test_exact_two_changed_sources_only():
    prefix = './CalculiX/ccx_2.21/src/'
    original = {'stressmortar.c': 'a', 'nonlingeo.c': 'b'}
    changed = {'stressmortar.c': 'c', 'nonlingeo.c': 'd'}
    before = {prefix+k: v for k, v in original.items()} | {'other': 'same'}
    after = before | {prefix+k: v for k, v in changed.items()}
    patch = {'source_sha256': original, 'patched_sha256': changed}
    assert len(verify_sources(before, patch, after)) == 2
    for bad in (after | {'other': 'wrong'}, after | {'extra': 'x'}, {k: v for k, v in after.items() if k != 'other'}):
        with pytest.raises(ValueError):
            verify_sources(before, patch, bad)


@pytest.mark.parametrize('relocated', [False, True])
def test_published_v2_full_replays_and_all_four_raw_runs(relocated, tmp_path, monkeypatch):
    from fea.mortar_kinematic_replay import replay
    from fea.mortar_observer_build.publish import require_comparison_coverage
    report = json.loads(Path('fea/mortar_kinematic_build/report.json').read_text())
    if relocated:
        shutil.copytree('fea/mortar_kinematic_build', tmp_path/'fea/mortar_kinematic_build')
        for name in report['sources_sha256']:
            target = tmp_path/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(name, target)
        monkeypatch.chdir(tmp_path)
        report = json.loads(Path('fea/mortar_kinematic_build/report.json').read_text())
    for group in ('sources_sha256', 'evidence_sha256'):
        for name, expected in report[group].items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert sha(Path(name)) == expected
    assert not Path(report['build_directory']).is_absolute()
    assert not Path(report['cube_directory']).is_absolute()
    history = report['publication_history']
    assert not Path(history['initial_report']).is_absolute()
    assert sha(Path(history['initial_report'])) == history['initial_report_sha256']
    build_dir, cubes = Path(report['build_directory']), Path(report['cube_directory'])
    built = json.loads((build_dir/'build_result.json').read_text())
    assert built['exit_code'] == 0 and built['image_id'] == report['observer_image_id']
    for name, expected in built['evidence_sha256'].items():
        assert sha(build_dir/name) == expected
    comparison = json.loads((cubes/'report.json').read_text())
    require_comparison_coverage(comparison['runs'])
    for run in comparison['runs']:
        directory = cubes/(run['case']+'-'+run['binary'])
        assert run['command'][-4] in (report['observer_image_id'], report['parent_image_id'])
        assert not any(run['maximum_printed_difference_from_archive'].values())
        assert run['accepted_history_equal_to_archive']
        for name, expected in run['output_sha256'].items():
            assert sha(directory/name) == expected
    for case in report['cases']:
        directory = cubes/(case['case']+'-observer')
        output = Path(case['replay'])
        assert not output.is_absolute() and '..' not in output.parts
        assert sha(output) == case['replay_sha256']
        result = replay((directory/'cube.log').read_text(), (directory/'cube.sta').read_text())
        assert json.loads(output.read_text()) == result
        assert result['calls_checked'] == case['calls_checked']
        assert len(result['accepted_coupling']) == case['accepted_coupling_count']
