"""Parent-only serialized one-shot finite proxy execution and freeze."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n')

def run():
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    assert os.environ.get('OMP_NUM_THREADS') == '1'
    assert not (HERE/'parent-run-inputs.json').exists(), 'one-shot parent run already recorded'
    assert sha(HERE/'run_adapter.py') == '53ed0d531e0f0a540cb1710baab1e70f06b14bc2f5d4f866037faab6444262c0'
    spec = importlib.util.spec_from_file_location('frozen_bg003_combined_adapter', HERE/'run_adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    batch = module.produce_batch()
    assert module.OUT_BATCH.read_text() == module.render(batch)
    assert not module.OUT_FINITE.exists()
    sources = dict(batch['source_sha256'])
    for name in ['run_adapter.py','README.md','batch-point-oracle.json','SHA256SUMS','parent_run.py']:
        sources[str((HERE/name).relative_to(ROOT))] = sha(HERE/name)
    inputs = {'source_sha256': sources, 'CPU_cap_seconds': 180,
              'wall_cap_seconds': 180, 'memory_cap_bytes': 6*1024**3,
              'single_BLAS_thread': True, 'native_launch': False,
              'scope': 'exactly eight A12 bolt1 finite proxy combinations; no force/capacity adoption'}
    write(HERE/'parent-run-inputs.json', inputs)
    resource.setrlimit(resource.RLIMIT_AS, (6*1024**3, 6*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    signal.signal(signal.SIGALRM, lambda *args: (_ for _ in ()).throw(TimeoutError('180 s suite wall cap')))
    signal.alarm(180)
    started = time.monotonic()
    report = {'status': 'RUNNING', 'input_record_sha256': sha(HERE/'parent-run-inputs.json'),
              'native_launch': False, 'joint_accepted': False}
    try:
        pins = module.verify_pins()
        setup = module.source_setup(json.loads(module.INPUT_PATH.read_text()))
        result = module.run_finite(setup, pins)
        assert result['scenario_count'] == 8
        module.OUT_FINITE.write_text(module.render(result))
        report['status'] = result['status']
        report['finite_result_sha256'] = sha(module.OUT_FINITE)
        report['scenario_count'] = result['scenario_count']
    except Exception as err:
        report['status'] = 'STOP_PARENT_FINITE_PROXY_EXCEPTION_OR_BUDGET'
        report['exception'] = repr(err)
    finally:
        signal.alarm(0)
        report['elapsed_seconds'] = time.monotonic()-started
        report['source_freeze_unchanged'] = all(sha(ROOT/p) == h for p,h in sources.items())
        if not report['source_freeze_unchanged']:
            report['status'] = 'STOP_SOURCE_CHANGED_DURING_FINITE_PROXY'
        write(HERE/'parent-run-assessment.json', report)
        write(HERE/'parent-run-output-pin.json', {'assessment_sha256':sha(HERE/'parent-run-assessment.json')})
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    lock = ROOT/'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
    with lock.open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert json.loads(lock.with_suffix('.json').read_text())['slot']['state'] == 'idle'
        run()
