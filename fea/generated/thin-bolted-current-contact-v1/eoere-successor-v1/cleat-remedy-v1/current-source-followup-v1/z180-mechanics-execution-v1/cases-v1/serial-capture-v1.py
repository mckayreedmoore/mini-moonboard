"""Fresh Z180 execution using the immutable existing process-capture helper."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path('/home/mckay-linux/repos/mini-moonboard')
E = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1')
CAPTURE = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/serial-capture-v1.py')
CAPTURE_SHA = '5dc4f8fd42c772aaaea7dfde8545804e70e7b28cbbcc561c6fc9ca7f041453f6'
WRAPPER = E / 'review-fix-v2/bridge.py'
WRAPPER_SHA = 'dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55'
CASES = E / 'cases-v1'
SEQUENCE = ['a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear']
FIRST = CASES / 'a12-forward/attempt01'
PINS = {
    str(CAPTURE): CAPTURE_SHA,
    str(WRAPPER): WRAPPER_SHA,
    str(E / 'inputs-v1/attempt01/inputs.json'): '80b5c013b5c69e895c4286d8673f91143f57ac0b0b5243c7370450ec87a2565a',
    str(E / 'inputs-review-v1/runs-v1/attempt01/receipt.json'): '3b8b6e2dff8cc8d047cf53b7865137aea11d5085d86359041f6541c78e9dcedf',
    str(E / 'readiness-v1/method-input.json'): '2549e962a5feac6617e27e8f324b6b7b576beb0683289c5dcfd1ee4b5d588654',
    str(E / 'readiness-v1/serialized-slot.json'): '74b562805b1aad0b7461554c791b5526391f7f751ee6f7f555987da4c46f035c',
    str(FIRST / 'field.json'): '43ccb97ab8e95bb2a37092a47fafe1b2b40ef8275145dad5ae736e80a6065a09',
    str(FIRST / 'admission.json'): 'b5a75796f2d39c49e04ef9b37d5fbfa9dc84f4cb0c03ff1c80925ac40a1b3baf',
}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def configured_capture():
    if hashlib.sha256(CAPTURE.read_bytes()).hexdigest() != CAPTURE_SHA:
        raise ValueError('Immutable capture helper changed')
    h = module(CAPTURE, 'eoere_z180_reused_process_capture')
    h.PINS = PINS
    h.verify_pins()
    return h


def admitted(case, h):
    d = CASES / case / 'attempt01'
    f, a = h.load(d / 'field.json'), h.load(d / 'admission.json')
    proof_name = 'parent-pair-validation.json' if case == 'a12-forward' else 'pair-validation.json'
    proof = h.load(d / proof_name)
    if not (a['unadopted_z180_equilibrium_and_recovery_pass'] is True
            and a['input_raw_sha256'] == h.ref(d / 'field.json')['sha256']
            and a['admission_source_sha256'] == WRAPPER_SHA
            and f['case_id'] == a['case_id'] == proof['case_id'] == case
            and proof['success'] is True and proof['source_pin_count'] == 1174
            and proof['field']['sha256'] == h.ref(d / 'field.json')['sha256']
            and proof['admission']['sha256'] == h.ref(d / 'admission.json')['sha256']
            and f['unadopted_proposal'] is a['unadopted_proposal'] is True
            and f['nut_spacer_proposal_included'] is a['nut_spacer_proposal_included'] is False
            and f['complete_joint_resistance'] is a['complete_joint_resistance'] is None
            and f['release'] == a['release'] == h.RELEASE):
        raise ValueError('Actual Z180 pair or raw gate validation failed')
    return f, a


def validate_pair(case, h):
    d = CASES / case / 'attempt01'
    started = datetime.now(timezone.utc).isoformat()
    before = h.verify_pins()
    start = time.monotonic()
    gate = module(WRAPPER, 'eoere_z180_own_raw_pair_gate')
    f, pins = gate.require_admitted_payload((d / 'field.json').read_bytes(), h.load(d / 'admission.json'), admission_sha256=WRAPPER_SHA)
    for path, expected in pins.items():
        if h.ref(path)['sha256'] != expected:
            raise ValueError('Raw pair source pin drift: ' + path)
    after = h.verify_pins()
    proof = {'schema': 'eoere_serial_z180_raw_pair_validation/v1', 'case_id': case,
             'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
             'elapsed_seconds': time.monotonic() - start, 'field': h.ref(d / 'field.json'),
             'admission': h.ref(d / 'admission.json'), 'gate': h.ref(WRAPPER),
             'state_id': f['state_id'], 'source_pin_count': len(pins), 'success': True,
             'pins_before': before, 'pins_after': after, 'release': h.RELEASE,
             'unadopted_proposal': True, 'nut_spacer_proposal_included': False,
             'complete_joint_resistance': None}
    with (d / 'pair-validation.json').open('x') as stream:
        json.dump(proof, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    return admitted(case, h)


def run(case):
    h = configured_capture()
    for previous in SEQUENCE[:SEQUENCE.index(case)]:
        admitted(previous, h)
    d = CASES / case / 'attempt01'
    d.mkdir(parents=True, exist_ok=False)
    for mode, process_name in [('run', 'process.json'), ('admit', 'admission-process.json')]:
        command = h.load(FIRST / process_name)['command'][:]
        changes = {'--case-id': case, '--out': str(d / 'field.json')} if mode == 'run' else {'--field': str(d / 'field.json'), '--out': str(d / 'admission.json')}
        for flag, value in changes.items():
            command[command.index(flag) + 1] = value
        h.capture(case, mode, command, d)
    f, a = validate_pair(case, h)
    print(json.dumps({'schema': 'eoere_serial_z180_admitted_pair_notice/v1', 'case_id': case,
                      'field': h.ref(d / 'field.json'), 'admission': h.ref(d / 'admission.json'),
                      'pair_validation': h.ref(d / 'pair-validation.json'),
                      'declared_law_checks': a['declared_law_checks']}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-id', choices=SEQUENCE[1:], required=True)
    args = p.parse_args()
    os.chdir(ROOT)
    os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    run(args.case_id)
