import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path('/home/mckay-linux/repos/mini-moonboard')
PACKET = ROOT / 'docs/wood-joints-mvp/hypotheses/washer-finite-sector-contact-native-2026-10-01-attempt02'
EXPECTED = '87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa'
RUN_ID = 'wj-washer-finite-sector-contact-20261001-a02'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

assert sha(PACKET / 'freeze.json') == EXPECTED
assert not (PACKET / 'execution.json').exists()
assert not (PACKET / 'parent-readiness.json').exists()
freeze = json.loads((PACKET / 'freeze.json').read_text())
assert freeze['run_bounds'] == {'cpus':1,'max_launches':1,'memory':'1g','timeout_seconds':60}
ledger = json.loads((ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.json').read_text())
assert ledger['slot']['state'] == 'idle'
assert not any(row.get('input_freeze_sha256') == EXPECTED or row['run_id'] == RUN_ID for row in ledger['runs'])
a12 = json.loads((ROOT / 'docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01/parent-source-execution.json').read_text())
assert a12['process_terminal'] and a12['input_and_review_hashes_stable']
quota = subprocess.run(['python3','/tmp/mini-moonboard-included-usage-check.py'],capture_output=True,text=True,check=True,timeout=15)
usage = json.loads(quota.stdout)
assert usage['ordinary_usage_allowed'] is True and usage['included_weekly_used_percent'] < 100
pins = json.loads((PACKET / 'source-pins.json').read_text())
for name, digest in pins['artifacts_sha256'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == digest, name
for name, record in pins['packet_code_paths_sha256'].items():
    assert sha(ROOT / record['path']) == record['sha256'], name
for archive_path, key in (('/tmp/ccx_2.23.src.tar.bz2','source_members_sha256'),('/tmp/ccx_2.23.htm.tar.bz2','manual_section_members')):
    with tarfile.open(archive_path) as archive:
        for member, record in pins[key].items():
            source_name = member if key == 'source_members_sha256' else record['archive_member']
            digest = record if key == 'source_members_sha256' else record['sha256']
            matches = [entry for entry in archive.getmembers() if entry.name.lstrip('./') == source_name.lstrip('./')]
            assert len(matches) == 1, source_name
            assert hashlib.sha256(archive.extractfile(matches[0]).read()).hexdigest() == digest, source_name
reviews = {name:sha(PACKET / name) for name in ('correctness-readiness-review.md','testing-readiness-review.md','architecture-readiness-review.md')}
for name in reviews:
    assert EXPECTED in (PACKET / name).read_text()
spec = importlib.util.spec_from_file_location('parent_reduced_native',ROOT / 'fea/wood_joint_reduced_native.py')
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)
protocol.verify(PACKET,check_live=True)
ready = {'schema':'wood_joint_parent_scoped_native_readiness/v1','input_freeze_sha256':EXPECTED,'ready_for_scoped_native_run':True,'scope':freeze['scope'],'reviews_sha256':reviews,'run_id':RUN_ID,'explicit_launch_arguments':{'timeout_seconds':60,'memory':'1g'},'run_bounds':freeze['run_bounds'],'no_prior_launch_for_same_freeze':True,'shared_slot_observed':ledger['slot'],'a12_source_recovery_process_terminal':True,'included_usage_observed':usage,'wrapper_sha256':sha(Path(__file__)),'mechanical_acceptance':False,'solver_convergence_is_acceptance':False,'result_review_pending':True,'no_retry_authorized':True}
write_new(PACKET / 'parent-readiness.json',ready)
execution = protocol.launch(PACKET,RUN_ID,PACKET / 'parent-readiness.json',timeout_seconds=60,memory='1g')
protocol.verify(PACKET,check_live=True)
assert all(sha(PACKET / name) == digest for name,digest in reviews.items())
print(json.dumps(execution,indent=2,sort_keys=True))
