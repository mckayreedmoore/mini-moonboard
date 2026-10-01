#!/usr/bin/env python3
"""Parent-operated, bounded execution of the frozen dynamic contact coupon."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FREEZE = HERE / 'input-freeze.json'
OUTPUT = HERE / 'output'
IMAGE = 'sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36'
BINARY = '/usr/local/bin/ccx-contact-point-trace-2.23'
BINARY_SHA = '3f949f639ead34b7ca62e2226480635cc0f5dbeda14afc200dcb523cf640b203'
INPUT_SHA = 'e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b'
CAP = 16 * 1024 * 1024
SECONDS = 60
FILES = (
    'run.py', 'verifier.py', 'README.md', 'parent-review.json',
    'independent-preflight.md', '../expected.json', '../fixture-design.md',
    '../input/implicit_point_trace.inp', '../trace-format.json',
    '../diagnostic.patch', '../dynamic-input-parent-audit.json',
    '../build-attempt04/build-manifest.json', '../build-attempt04/execution.json',
    '../static-regression-attempt02/verifier.json',
    '../static-regression-attempt02/input-freeze.json',
    '../static-regression-attempt02/output/execution.json',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, record, exclusive=True):
    with path.open('x' if exclusive else 'w') as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write('\n')


def inventory():
    return {name: sha(HERE / name) for name in FILES}


def inspect(name):
    return json.loads(subprocess.check_output(
        ['docker', 'inspect', name], text=True, timeout=15))[0]


def validate_inputs():
    spec = importlib.util.spec_from_file_location('dynamic_contact_auditor', HERE / 'verifier.py')
    require(spec is not None and spec.loader is not None, 'Cannot load the pinned output auditor')
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    auditor.verify_prepared_contract()
    regression = ROOT / 'static-regression-attempt02'
    regression_result = json.loads((regression / 'verifier.json').read_text())
    require(regression_result['status'] == 'PASS_MATCHED_STATIC_REGRESSION_TRACE_CAPTURE' and
            regression_result['freeze_sha256'] == sha(regression / 'input-freeze.json') and
            regression_result['execution_sha256'] == sha(regression / 'output/execution.json'),
            'Matched static output regression is not established')
    expected = json.loads((ROOT / 'expected.json').read_text())
    require(sha(ROOT / 'input/implicit_point_trace.inp') == INPUT_SHA == expected['input']['sha256'],
            'Dynamic coupon input identity mismatch')
    manifest = json.loads((ROOT / 'build-attempt04/build-manifest.json').read_text())
    require(manifest['patched_binary_sha256'] == BINARY_SHA and
            manifest['patch_sha256'] == sha(ROOT / 'diagnostic.patch'), 'Diagnostic build mismatch')
    for key in ['diagnostic_patch', 'trace_format', 'geometry_dof_audit']:
        support = expected['supporting_artifacts']
        require(sha(ROOT / support[key + '_path']) == support[key + '_sha256'],
                'Fixture supporting artifact mismatch: ' + key)
    review = json.loads((HERE / 'parent-review.json').read_text())
    require(review['ready_for_native_coupon_only'] is True, 'Parent readiness is not established')
    return expected


def freeze():
    require(not OUTPUT.exists() and not FREEZE.exists(), 'Refusing replacement or post-run freeze')
    validate_inputs()
    record = {'schema': 'ccx223_dynamic_contact_coupon_freeze/v1', 'created_utc': now(),
              'files_sha256': inventory(), 'image_id': IMAGE, 'binary_path': BINARY,
              'binary_sha256': BINARY_SHA, 'input_sha256': INPUT_SHA,
              'limits': {'cpus': 1, 'memory_bytes': 1073741824, 'timeout_seconds': SECONDS,
                         'aggregate_output_bytes': CAP, 'network': 'none'},
              'scope': 'Prescribed-motion contact-field known answer only',
              'joint_acceptance': False, 'release': False}
    save(FREEZE, record)
    return {'status': 'FROZEN_NOT_EXECUTED', 'freeze_sha256': sha(FREEZE)}


def run(freeze_sha):
    require(sha(FREEZE) == freeze_sha, 'Freeze identity mismatch')
    record = json.loads(FREEZE.read_text())
    require(record['files_sha256'] == inventory(), 'Frozen input changed')
    validate_inputs()
    require(not OUTPUT.exists(), 'Refusing rerun or overlapping output')
    require(inspect(IMAGE)['Id'] == IMAGE, 'Image identity mismatch')
    binary_check = subprocess.check_output(
        ['docker', 'run', '--rm', '--pull=never', '--network', 'none', IMAGE,
         'sha256sum', BINARY], text=True, timeout=20)
    require(binary_check.split()[0] == BINARY_SHA, 'Binary identity mismatch')
    OUTPUT.mkdir()
    shutil.copyfile(ROOT / 'input/implicit_point_trace.inp', OUTPUT / 'coupon.inp')
    name = 'ccxpt-dynamic-' + str(time.time_ns())
    command = ['docker', 'run', '--pull=never', '--name', name, '--network', 'none',
               '--cpus', '1', '--memory', '1g', '--memory-swap', '1g',
               '--user', f'{os.getuid()}:{os.getgid()}',
               '--env', 'OMP_NUM_THREADS=1', '--env', 'CCX_NPROC_EQUATION_SOLVER=1',
               '--mount', f'type=bind,src={OUTPUT},dst=/work', '--workdir', '/work',
               IMAGE, BINARY, '-i', 'coupon']
    execution = {'schema': 'ccx223_dynamic_contact_coupon_execution/v1',
                 'started_utc': now(), 'status': 'RUNNING', 'freeze_sha256': freeze_sha,
                 'image_id': IMAGE, 'binary_sha256': BINARY_SHA, 'input_sha256': INPUT_SHA,
                 'container_name': name, 'command': command, 'limits': record['limits'],
                 'joint_acceptance': False, 'release': False}
    save(OUTPUT / 'execution.json', execution)
    start = time.monotonic()
    stop = None

    def output_bytes():
        return sum(p.stat().st_size for p in OUTPUT.iterdir()
                   if p.is_file() and p.name not in {'coupon.inp', 'execution.json'})

    with (OUTPUT / 'solver.stdout').open('wb') as stdout, (OUTPUT / 'solver.stderr').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        while process.poll() is None:
            if time.monotonic() - start > SECONDS or output_bytes() > CAP:
                stop = 'timeout' if time.monotonic() - start > SECONDS else 'output_cap'
                subprocess.run(['docker', 'kill', name], capture_output=True, timeout=15, check=False)
                break
            time.sleep(0.05)
        code = process.wait(timeout=20)
    container = inspect(name)
    state = container['State']
    size = output_bytes()
    normal = code == 0 and state['ExitCode'] == 0 and not state['OOMKilled'] and not state['Running']
    execution.update({'ended_utc': now(), 'elapsed_seconds': time.monotonic() - start,
                      'docker_cli_exit_code': code, 'container_state': state,
                      'container_image': container['Image'], 'stop_reason': stop,
                      'native_output_bytes': size,
                      'status': 'PASS_NATIVE_CAPTURE' if normal and not stop and size <= CAP else 'FAIL_NATIVE_CAPTURE',
                      'outputs_sha256': {p.name: sha(p) for p in sorted(OUTPUT.iterdir())
                                         if p.is_file() and p.name != 'execution.json'}})
    save(OUTPUT / 'execution.json', execution, exclusive=False)
    return {'status': execution['status'], 'execution_sha256': sha(OUTPUT / 'execution.json'),
            'native_output_bytes': size}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze', action='store_true')
    group.add_argument('--run', action='store_true')
    parser.add_argument('--freeze-sha')
    args = parser.parse_args()
    print(json.dumps(freeze() if args.freeze else run(args.freeze_sha), sort_keys=True))
