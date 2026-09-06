"""Portable publication integrity checks only; no solver or arithmetic replay."""
import hashlib
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path('fea/results/mortar_frame_observer')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(name):
    return json.loads((ROOT/name).read_text())


@pytest.fixture(scope='module')
def publication():
    report = read('report.json')
    contents = {}
    local = None
    for name, item in report['archives'].items():
        archive = ROOT/name
        assert archive.stat().st_size == item['size_bytes'] < 100_000_000
        assert sha(archive) == item['sha256']
        hashes = {}
        with tarfile.open(archive) as tar:
            for member in tar:
                assert member.isfile() and member.name not in contents
                assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                with tar.extractfile(member) as handle:
                    hashes[member.name] = hashlib.file_digest(handle, 'sha256').hexdigest()
                if member.name == 'local_replay.json':
                    local = json.load(tar.extractfile(member))
        assert hashes == item['contents_sha256']
        contents.update(hashes)
    for name, expected in report['files_sha256'].items():
        assert sha(ROOT/name) == expected
        assert name not in contents
        contents[name] = expected
    assert sha(ROOT/'publish.py') == report['publisher_sha256']
    return report, contents, local


def test_original_failure_recovery_and_source_binding(publication):
    manifest, contents, _ = publication
    original, recovered, record = map(read, ('original-report.json', 'recovered-report.json', 'recovery.json'))
    assert original['exit_code'] == 0
    assert 0 < original['elapsed_seconds'] <= original['max_seconds'] == 1500
    assert original['terminal_state_confirmed'] is False
    assert original['stop_reason'] == 'Named container termination unconfirmed'
    absent = 'error: no such object: '+manifest['original_directory_name']
    assert original['cleanup_error'].strip() == 'RuntimeError: Cannot resolve named container: '+absent
    probe = record['container_probe']
    assert probe['command'] == ['docker', 'inspect', '--format', '{{.State.Running}}',
                                manifest['original_directory_name']]
    assert probe['returncode'] == 1 and not probe['stdout'].strip()
    assert probe['stderr'].strip() == absent
    assert record['original_report_sha256'] == contents['original-report.json']
    assert record['recovery_source_sha256'] == contents['recovery-launch.py']
    assert recovered['recovery_record_sha256'] == contents['recovery.json']
    assert recovered['original_cleanup_error'] == original['cleanup_error']
    assert recovered['original_stop_reason'] == original['stop_reason']
    assert recovered['terminal_state_confirmed'] is True
    assert 'stop_reason' not in recovered and 'cleanup_error' not in recovered
    assert recovered['audit_exit_code'] == recovered['audit_child_exit_code'] == 1
    assert recovered['audit_termination_confirmed'] is True
    assert recovered['status'] == 'TERMINAL DIAGNOSTIC ONLY; AUDIT REJECTED'
    for name, expected in manifest['original_file_sha256'].items():
        assert contents['original-report.json' if name == 'report.json' else name] == expected
    for inventory in ('prelaunch_sha256', 'output_sha256', 'audit_source_sha256'):
        assert original[inventory] == recovered[inventory]
    for inventory in ('prelaunch_sha256', 'output_sha256'):
        assert all(contents[name] == expected for name, expected in original[inventory].items())
    for name, expected in original['audit_source_sha256'].items():
        archived = 'launch.py' if name == 'mortar_frame_observer.py' else 'launch_sources/'+name
        assert contents[archived] == expected
    assert all(contents[name] == expected for name, expected in recovered['audit_output_sha256'].items())
    for name, item in manifest['reference'].items():
        assert sha(ROOT/item['path']) == record['reference_sha256'][name] == item['sha256']
    assert manifest['reference']['0.0625.tar.gz']['sha256'] == original['reference_archive_sha256']


def test_published_rejected_diagnostics_remain_explicit(publication):
    manifest, _, local = publication
    audit = read('audit.json')
    summary = manifest['summary']
    assert local['calls'] == summary['observer_calls'] == 108
    assert local['accepted_calls'] == summary['accepted_calls'] == 32
    assert audit['maximum_printed_difference'] == {'forces': 0., 'displacements': 9.999999994736442e-09}
    assert audit['accepted_history_equal'] is True
    assert audit['output_and_history_equal'] is False
    assert audit['global_gates_pass'] is False
    for key in ('ground_body_gates_pass', 'arithmetic_replay_pass', 'independent_deck_inventory_pass'):
        assert audit[key] is True
    assert all(summary[key] == value for key, value in audit.items() if key != 'diagnostic_endpoints')
    endpoints = audit['diagnostic_endpoints']
    assert len(endpoints) == 32
    assert all(row['global_gate_pass'] ==
               (max(map(abs, row['force_residual_n'])) <= .1 and
                max(map(abs, row['moment_residual_nmm'])) <= 1.) for row in endpoints)
    failures = [row['time'] for row in endpoints if not row['global_gate_pass']]
    assert failures == summary['failed_global_gate_times']
    assert len(failures) == 7
