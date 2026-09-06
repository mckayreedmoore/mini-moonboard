"""Post-hoc cleanup classification recovery; never rerun or alter solver evidence."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def check_recoverable(report, directory, probe):
    """Only the observed exact-name missing-container cleanup failure is eligible."""
    name = directory.name
    expected = 'error: no such object: '+name
    if (report['exit_code'] != 0 or 'monitor_error' in report or
            report['terminal_state_confirmed'] is not False or
            report.get('stop_reason') != 'Named container termination unconfirmed' or
            report.get('cleanup_error', '').strip() !=
            'RuntimeError: Cannot resolve named container: '+expected or
            probe.returncode != 1 or probe.stdout.strip() or probe.stderr.strip() != expected or
            not 0 < report['elapsed_seconds'] <= report['max_seconds'] or
            (directory/'frame.log').stat().st_size > report['stdout_limit_bytes']):
        raise ValueError('Not the narrowly recoverable completed-run cleanup error')
    command = report['command']
    if command[command.index('--name')+1] != name or '--rm' not in command:
        raise ValueError('Original named auto-removed container required')
    for key in ('prelaunch_sha256', 'output_sha256'):
        for relative, expected_sha in report[key].items():
            path = (directory/relative).resolve()
            if not path.is_relative_to(directory.resolve()) or sha(path) != expected_sha:
                raise ValueError('Original evidence changed: '+relative)


def recover(directory):
    directory = directory.resolve()
    original = directory/'report.json'
    original_sha = sha(original)
    report = json.loads(original.read_text())
    command = ['docker', 'inspect', '--format', '{{.State.Running}}', directory.name]
    probe = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    check_recoverable(report, directory, probe)
    root = Path(tempfile.mkdtemp(prefix='recovered-frame-audit-', dir=directory.parent)).resolve()
    evidence = root/'evidence'
    shutil.copy2(Path(__file__), root/'recovery-launch.py')
    shutil.copytree(directory, evidence)
    shutil.copy2(original, evidence/'original-report.json')
    sources = root/'fea'
    sources.mkdir()
    for name, expected in report['audit_source_sha256'].items():
        source = directory/('launch.py' if name == 'mortar_frame_observer.py' else 'launch_sources/'+name)
        if sha(source) != expected:
            raise ValueError('Launch source changed: '+name)
        shutil.copy2(source, sources/name)
    # Execute only the original project source closure, from its own package root.
    reference = sources/'results/full_frame_refinement'
    reference.mkdir(parents=True)
    for name in ('0.0625.tar.gz', 'report.json'):
        shutil.copy2(Path('fea/results/full_frame_refinement')/name, reference/name)
    recovery = {
        'original_directory': str(directory), 'original_report_sha256': original_sha,
        'recovery_source_sha256': sha(Path(__file__)),
        'checked_at_utc': datetime.now(UTC).isoformat(),
        'container_probe': {'command': command, 'returncode': probe.returncode,
                            'stdout': probe.stdout, 'stderr': probe.stderr},
        'meaning': 'Post-hoc terminal classification only. Original cleanup failure retained. '
                   'No solver rerun, numerical changes, physical acceptance or retroactive monitor success.',
        'reference_sha256': {p.name: sha(p) for p in reference.iterdir()},
    }
    (root/'recovery.json').write_text(json.dumps(recovery, indent=2)+'\n')
    report['terminal_state_confirmed'] = True
    report['original_cleanup_error'] = report.pop('cleanup_error')
    report['original_stop_reason'] = report.pop('stop_reason')
    report['recovery_record_sha256'] = sha(root/'recovery.json')
    report['status'] = 'POST-HOC TERMINAL CONFIRMATION; AUDIT PENDING; NO PHYSICAL ACCEPTANCE'
    (evidence/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Recovery evidence: '+str(root), flush=True)
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    # Original runner supplies its existing 300-second / 6-GiB audit bounds.
    code = ('import json; from pathlib import Path; from fea.mortar_frame_observer import run_audit; '
            'p=Path("evidence").resolve(); run_audit(p,json.loads((p/"report.json").read_text()))')
    result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env, check=False)
    if sha(original) != original_sha:
        raise ValueError('Original report changed during recovery')
    check_recoverable(json.loads(original.read_text()), directory, probe)
    terminal = json.loads((evidence/'report.json').read_text())
    return root, result.returncode or terminal.get('audit_exit_code', 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root, code = recover(args.directory)
    terminal = json.loads((root/'evidence/report.json').read_text())
    print(json.dumps({'directory': str(root), 'status': terminal['status'],
                      'audit_exit_code': terminal.get('audit_exit_code')}))
    raise SystemExit(code or terminal.get('audit_exit_code', 1))
