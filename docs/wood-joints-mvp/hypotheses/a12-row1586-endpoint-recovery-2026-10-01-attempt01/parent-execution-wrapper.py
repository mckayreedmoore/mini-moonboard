import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

ROOT = Path('/home/mckay-linux/repos/mini-moonboard')
PACKET = ROOT / 'docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01'
FREEZE = PACKET / 'parent-input-freeze-02.json'
EXPECTED_FREEZE = 'a4f0ba75a5a3d46b047880ea4b6feae7df40470be1ca921ef78da398261b537a'
MARKER = Path('/tmp/mini-moonboard-a12-row1586-endpoint-recovery-attempt01.consumed')
APPROVAL = Path('/tmp/mini-moonboard-a12-row1586-parent-approval-attempt01.json')
REPORT = Path('/tmp/mini-moonboard-a12-row1586-parent-source-result-attempt01.json')
LEDGER = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.json'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

def check_inputs(freeze):
    assert sha(FREEZE) == EXPECTED_FREEZE
    checks = {}
    for name, digest in freeze['files_sha256'].items():
        live = PACKET / name
        frozen = PACKET / freeze['frozen_snapshot_directory'] / name
        assert sha(live) == sha(frozen) == digest, name
        checks[str(live.relative_to(ROOT))] = digest
    for name, record in freeze['source_input_sha256'].items():
        path = Path(record['path'])
        if not path.is_absolute():
            path = ROOT / path
        assert sha(path) == record['sha256'], name
        checks[str(path)] = record['sha256']
    assert sha(ROOT / 'uv.lock') == freeze['runtime']['uv_lock_sha256']
    return checks

def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (2147483648, 2147483648))

assert sha(FREEZE) == EXPECTED_FREEZE
freeze = json.loads(FREEZE.read_text())
assert not MARKER.exists() and not APPROVAL.exists() and not REPORT.exists()
assert not (PACKET / 'parent-source-execution.json').exists()
assert not (PACKET / 'parent-source-reservation.json').exists()
env = os.environ.copy()
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    env[key] = '1'
runtime = subprocess.run([freeze['runtime']['executable'], '-c', 'import sys, platform, numpy, scipy, json; print(json.dumps({"python":platform.python_version(),"implementation":platform.python_implementation(),"numpy":numpy.__version__,"scipy":scipy.__version__,"executable":sys.executable}))'], env=env, capture_output=True, text=True, check=True, timeout=20)
observed_runtime = json.loads(runtime.stdout)
assert all(observed_runtime[k] == freeze['runtime'][k] for k in observed_runtime)
review_names = ('correctness-readiness-review.md', 'testing-readiness-review.md', 'architecture-readiness-review.md')
reviews = {name: sha(PACKET / name) for name in review_names}
for name in review_names:
    assert EXPECTED_FREEZE in (PACKET / name).read_text()
approval = {'schema':'a12_row1586_endpoint_recovery_parent_approval/v1', 'approved':True, 'preparation_readiness_sha256':'edcc2fbc8adddfab44e8419db8b297df4c8f6f6a11e905523d1bcb60102d84f7', 'runner_sha256':freeze['files_sha256']['runner.py'], 'source_pin_manifest_sha256':freeze['files_sha256']['source-pins.json'], 'scope':'two_target_bodies_row_1586_only'}
command = [freeze['runtime']['executable'], str(PACKET / 'runner.py'), '--execute', '--parent-approval', str(APPROVAL), '--report', str(REPORT)]
with LEDGER.with_suffix('.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ledger = json.loads(LEDGER.read_text())
    assert ledger['slot']['state'] == 'idle'
    before = check_inputs(freeze)
    containers = subprocess.run(['docker','ps','--format','{{.Names}}'], capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()
    assert not any('moonboard' in name or 'ccx' in name for name in containers)
    write_new(APPROVAL, approval)
    reservation = {'schema':'wood_joint_parent_source_recovery_reservation/v1', 'input_freeze_sha256':EXPECTED_FREEZE, 'parent_launch_authorized':True, 'scope':approval['scope'], 'approval_path':str(APPROVAL), 'approval_sha256':sha(APPROVAL), 'reviews_sha256':reviews, 'process_command':command, 'process_bounds':freeze['run_bounds'], 'runtime_observed':observed_runtime, 'wrapper_sha256':sha(Path(__file__)), 'ledger_slot_observed':ledger['slot'], 'ledger_run_count_observed':len(ledger['runs']), 'shared_ledger_lock_held_through_process':True, 'no_native_run_registered':True, 'source_inputs_before':before, 'mechanical_acceptance':False, 'source_force_adopted':False, 'reserved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write_new(PACKET / 'parent-source-reservation.json', reservation)
    start = time.monotonic()
    timed_out = False
    with (PACKET / 'parent-source.stdout').open('xb') as out, (PACKET / 'parent-source.stderr').open('xb') as err:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err, preexec_fn=limits, start_new_session=True)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.wait(timeout=10)
    elapsed = time.monotonic() - start
    try:
        after = check_inputs(freeze)
        stable = after == before and all(sha(PACKET / name) == digest for name, digest in reviews.items())
        post_error = None
    except Exception as exc:
        stable = False
        after = {}
        post_error = repr(exc)
    output_hashes = {name:sha(PACKET / name) for name in ('parent-source.stdout','parent-source.stderr')}
    if REPORT.exists():
        raw = REPORT.read_bytes()
        (PACKET / 'parent-source-result.json').write_bytes(raw)
        output_hashes['parent-source-result.json'] = sha(REPORT)
    record = {'schema':'wood_joint_parent_source_recovery_execution/v1', 'input_freeze_sha256':EXPECTED_FREEZE, 'reservation_sha256':sha(PACKET / 'parent-source-reservation.json'), 'approval_sha256':sha(APPROVAL), 'one_shot_marker_present':MARKER.exists(), 'one_shot_marker_sha256':sha(MARKER) if MARKER.exists() else None, 'process_terminal':proc.poll() is not None, 'return_code':proc.returncode, 'timed_out':timed_out, 'wall_seconds_including_startup':elapsed, 'process_limits_enforced_before_imports':True, 'input_and_review_hashes_stable':stable, 'postcheck_error':post_error, 'source_inputs_after':after, 'output_sha256':output_hashes, 'native_solve_executed':False, 'mechanical_acceptance':False, 'source_force_adopted':False, 'result_review_pending':True, 'no_retry_under_this_attempt':True, 'ledger_slot_after':json.loads(LEDGER.read_text())['slot'], 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write_new(PACKET / 'parent-source-execution.json', record)
    print(json.dumps({k:record[k] for k in ('return_code','timed_out','wall_seconds_including_startup','input_and_review_hashes_stable','one_shot_marker_present','output_sha256')}))
