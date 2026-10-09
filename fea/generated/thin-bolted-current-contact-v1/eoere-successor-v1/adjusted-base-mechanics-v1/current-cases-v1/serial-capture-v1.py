"""Capture authorized serial fresh runs; this helper changes no mechanics."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/mckay-linux/repos/mini-moonboard')
MECH = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1')
CASES = MECH / 'current-cases-v1'
SEQUENCE = ['a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear']
WRAPPER = MECH / 'current-force-bridge-v1/review-fix-v2/bridge.py'
INPUT = MECH / 'current-inputs-v1/attempt01/inputs.json'
REVIEW = MECH / 'current-inputs-v1/independent-review-v1/receipt.json'
METHOD = MECH / 'current-readiness-v1/method-input.json'
SLOT = Path('/tmp/moonboard-extended-cleat-force-parent-slot-v1.json')
PINS = {
    str(WRAPPER): '4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643',
    str(INPUT): 'f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa',
    str(REVIEW): 'f7936b055d3a0ee9a475b09bff73d46fbbf25303c23c17c14e2d3e6c4c97eb2c',
    str(METHOD): '941ca92e8230de9d480d17f6e2a082d05a3fae267329ef0b33c81d06d0ad46f5',
    str(SLOT): '6d40efb578db5f46f4bf5deffa762c0d3c0b7dc9f1ef36bdd4ac0e9d14895e88',
    str(CASES / 'a12-forward/attempt01/field.json'): 'a6061668878537da052571075c3ede10ab4236f9734eea5be0176c647688f4bb',
    str(CASES / 'a12-forward/attempt01/admission.json'): 'f15357cfc083a50446eec61550900fd44fdab0198a13e2c06a252bd25bfbd2b7',
}
RELEASE = dict.fromkeys(['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
                        'fabrication_released', 'structural_released', 'climbing_released'], False)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify_pins():
    actual = {path: ref(path)['sha256'] for path in PINS}
    if actual != PINS:
        raise ValueError('Authorized pin or original parent pair changed')
    return actual


def load(path):
    return json.loads(Path(path).read_bytes())


def capture(case, mode, command, directory):
    prefix = '' if mode == 'run' else 'admission.'
    record_name = 'process.json' if mode == 'run' else 'admission-process.json'
    environment = {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    if mode == 'run':
        environment['EOERE_PARENT_SERIALIZED_FORCE_RUN'] = '1'
    before = verify_pins()
    record = {'schema': 'eoere_serial_current_' + mode + '_process_capture/v1', 'case_id': case,
              'command': command, 'cwd': str(ROOT), 'controlled_environment': environment,
              'started_at_utc': utc(), 'status': 'STARTED', 'pins_before': before,
              'historical_state_or_actions_used': False, 'release': RELEASE}
    with (directory / record_name).open('x+') as stream:
        def write():
            stream.seek(0)
            json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        write()
        start = time.monotonic()
        print(json.dumps({'case_id': case, 'phase': mode, 'status': 'STARTED', 'started_at_utc': record['started_at_utc']}), flush=True)
        with (directory / (prefix + 'stdout.log')).open('xb') as stdout, (directory / (prefix + 'stderr.log')).open('xb') as stderr:
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, **environment}, stdout=stdout, stderr=stderr, check=False)
        record.update(finished_at_utc=utc(), elapsed_seconds=time.monotonic()-start, exit_code=result.returncode,
                      status='FINISHED', logs={name: ref(directory / name) for name in [prefix + 'stdout.log', prefix + 'stderr.log']})
        record['pins_after'] = {path: ref(path)['sha256'] for path in PINS}
        record['pins_unchanged'] = record['pins_after'] == before == PINS
        write()
    print(json.dumps({'case_id': case, 'phase': mode, 'status': 'FINISHED', 'exit_code': result.returncode,
                      'elapsed_seconds': record['elapsed_seconds'], 'pins_unchanged': record['pins_unchanged']}), flush=True)
    if result.returncode != 0 or not record['pins_unchanged']:
        raise ValueError('Genuine process or pin failure; preserve raw outputs and stop without retry')


def admitted(case):
    directory = CASES / case / 'attempt01'
    field_path, admission_path = directory / 'field.json', directory / 'admission.json'
    field, admission = load(field_path), load(admission_path)
    if not (field['case_id'] == admission['case_id'] == case
            and admission['current_extended_cleat_equilibrium_and_recovery_pass'] is True
            and admission['input_raw_sha256'] == ref(field_path)['sha256']
            and admission['admission_source_sha256'] == PINS[str(WRAPPER)]
            and all(value is False for value in field['release'].values())
            and all(value is False for value in admission['release'].values())):
        raise ValueError('Actual pair did not pass the unchanged current admission')
    return field, admission


def run(case):
    if case not in SEQUENCE[1:]:
        raise ValueError('Helper only owns remaining authorized cases')
    verify_pins()
    for previous in SEQUENCE[:SEQUENCE.index(case)]:
        admitted(previous)
    directory = CASES / case / 'attempt01'
    directory.mkdir(parents=True, exist_ok=False)
    field_path = directory / 'field.json'
    command = [sys.executable, '-B', str(WRAPPER), '--mode', 'run', '--run', '--case-id', case, '--wall-seconds', '900']
    for option, path in [('inputs', INPUT), ('input-review', REVIEW), ('method-input', METHOD), ('slot', SLOT)]:
        command += ['--' + option, str(path), '--' + option + '-sha256', PINS[str(path)]]
    command += ['--out', str(field_path)]
    capture(case, 'run', command, directory)
    capture(case, 'admit', [sys.executable, '-B', str(WRAPPER), '--mode', 'admit', '--field', str(field_path), '--out', str(directory / 'admission.json')], directory)
    field, admission = admitted(case)
    print(json.dumps({'case_id': case, 'status': 'ADMITTED', 'field': ref(field_path),
                      'admission': ref(directory / 'admission.json'), 'declared_law_checks': admission['declared_law_checks']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-id', choices=SEQUENCE[1:], required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    run(args.case_id)
