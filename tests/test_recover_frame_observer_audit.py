"""No Docker or solver: recovery accepts only the exact recorded cleanup failure."""
import json
import subprocess

import pytest

from fea.recover_frame_observer_audit import check_recoverable, recover, sha


def evidence(tmp_path):
    (tmp_path/'frame.log').write_text('completed output\n')
    (tmp_path/'frame.inp').write_text('original input\n')
    absent = 'error: no such object: '+tmp_path.name
    report = {
        'exit_code': 0, 'terminal_state_confirmed': False,
        'stop_reason': 'Named container termination unconfirmed',
        'cleanup_error': 'RuntimeError: Cannot resolve named container: '+absent,
        'elapsed_seconds': 1252, 'max_seconds': 1500,
        'stdout_limit_bytes': 512*1024**2,
        'command': ['docker', 'run', '--rm', '--name', tmp_path.name],
        'prelaunch_sha256': {'frame.inp': sha(tmp_path/'frame.inp')},
        'output_sha256': {'frame.log': sha(tmp_path/'frame.log')},
    }
    return report, subprocess.CompletedProcess([], 1, '', absent+'\n')


def test_exact_absence_and_intact_completed_evidence(tmp_path):
    report, probe = evidence(tmp_path)
    check_recoverable(report, tmp_path, probe)


@pytest.mark.parametrize('code,out,err', [
    (0, 'false\n', ''),
    (0, 'true\n', ''),
    (1, '', 'permission denied'),
    (1, '', 'Cannot connect to the Docker daemon'),
    (1, '', 'error: no such object: a-different-container'),
    (1, 'unexpected output', None),
    (2, '', None),
])
def test_probe_must_prove_exact_named_absence(tmp_path, code, out, err):
    report, probe = evidence(tmp_path)
    probe.returncode, probe.stdout = code, out
    if err is not None:
        probe.stderr = err
    with pytest.raises(ValueError):
        check_recoverable(report, tmp_path, probe)


@pytest.mark.parametrize('key,value', [
    ('exit_code', 1), ('terminal_state_confirmed', True),
    ('monitor_error', 'KeyboardInterrupt: Received signal 2'),
    ('stop_reason', 'Timeout'), ('cleanup_error', 'Other cleanup failure'),
    ('elapsed_seconds', 1501), ('elapsed_seconds', 0),
    ('stdout_limit_bytes', 1),
    ('command', ['docker', 'run', '--rm', '--name', 'other']),
    ('command', ['docker', 'run', '--name', 'other']),
])
def test_ineligible_original_report_is_rejected(tmp_path, key, value):
    report, probe = evidence(tmp_path)
    report[key] = value
    with pytest.raises(ValueError):
        check_recoverable(report, tmp_path, probe)


@pytest.mark.parametrize('name', ['frame.log', 'frame.inp'])
def test_modified_original_evidence_is_rejected(tmp_path, name):
    report, probe = evidence(tmp_path)
    (tmp_path/name).write_text('changed\n')
    with pytest.raises(ValueError, match='Original evidence changed'):
        check_recoverable(report, tmp_path, probe)


@pytest.mark.parametrize('audit_code', [0, 1])
def test_recovery_preserves_original_and_propagates_audit_status(tmp_path, monkeypatch, audit_code):
    directory = tmp_path/'original'
    directory.mkdir()
    report, probe = evidence(directory)
    (directory/'launch.py').write_text('# archived source\n')
    report['audit_source_sha256'] = {'mortar_frame_observer.py': sha(directory/'launch.py')}
    report['prelaunch_sha256']['launch.py'] = sha(directory/'launch.py')
    (directory/'report.json').write_text(json.dumps(report))
    original_hashes = {p.name: sha(p) for p in directory.iterdir()}
    reference = tmp_path/'fea/results/full_frame_refinement'
    reference.mkdir(parents=True)
    for name in ('0.0625.tar.gz', 'report.json'):
        (reference/name).write_text('reference fixture')
    monkeypatch.chdir(tmp_path)
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if command[0] == 'docker':
            assert command == ['docker', 'inspect', '--format', '{{.State.Running}}', directory.name]
            return probe
        assert command[1] == '-c' and 'run_audit(' in command[2]
        derived = kwargs['cwd']/'evidence/report.json'
        terminal = json.loads(derived.read_text())
        assert terminal['terminal_state_confirmed'] is True
        assert terminal['original_cleanup_error'] == report['cleanup_error']
        assert 'stop_reason' not in terminal
        terminal['audit_exit_code'] = audit_code
        derived.write_text(json.dumps(terminal))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr('fea.recover_frame_observer_audit.subprocess.run', run)
    root, code = recover(directory)
    assert code == audit_code
    assert len(commands) == 2
    assert {p.name: sha(p) for p in directory.iterdir()} == original_hashes
    assert sha(root/'evidence/original-report.json') == original_hashes['report.json']
    assert sha(root/'evidence/frame.log') == original_hashes['frame.log']
    assert sha(root/'fea/mortar_frame_observer.py') == original_hashes['launch.py']
