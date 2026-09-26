import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

out = Path('/work')
request = json.loads((out / 'request.json').read_text())
root = Path('/opt/ccx-upstream-2.21')
source = root / 'CalculiX/ccx_2.21/src'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for name, expected in request['input_sha256'].items():
    assert sha(out / 'inputs' / name) == expected, name
manifest = json.loads((out / 'inputs/baseline-build-manifest.json').read_text())
assert manifest['upstream_source_archive_sha256'] == request['source_archive_sha256']
for name, expected in manifest['upstream_files_sha256'].items():
    assert sha(root / name) == expected, name
baseline = Path('/usr/local/bin/ccx-upstream-2.21')
assert sha(baseline) == request['baseline_upstream_binary_sha256']
assert sha(Path('/usr/bin/ccx')) == request['packaged_binary_sha256']
shutil.copyfile(baseline, out / 'ccx-unmodified-upstream-2.21')
for name in ('results.c', 'printoutcontact.f'):
    shutil.copyfile(out / 'inputs' / name, source / name)
command = ['make', '-C', str(source), '-f', str(root / 'Makefile.upstream'), '-j2']
started = time.monotonic()
with (out / 'make.log').open('w') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
record = {
    'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'returncode': result.returncode,
    'command': command,
    'elapsed_seconds': time.monotonic() - started,
    'verified_upstream_source_file_count': len(manifest['upstream_files_sha256']),
    'request': request,
}
if result.returncode == 0:
    shutil.copyfile(source / 'ccx_2.21', out / 'ccx-wj-angular-output-2.21')
    for name in ('ccx-unmodified-upstream-2.21', 'ccx-wj-angular-output-2.21'):
        (out / name).chmod(0o755)
    record['instrumented_binary_sha256'] = sha(out / 'ccx-wj-angular-output-2.21')
    record['unmodified_upstream_binary_sha256'] = sha(out / 'ccx-unmodified-upstream-2.21')
    shutil.copyfile(root / 'Makefile.upstream', out / 'Makefile.upstream.snapshot')
    record['makefile_sha256'] = sha(out / 'Makefile.upstream.snapshot')
(out / 'build-result.json').write_text(json.dumps(record, indent=2) + '\n')
for path in out.rglob('*'):
    os.chown(path, request['output_uid'], request['output_gid'])
print(json.dumps(record, indent=2), flush=True)
raise SystemExit(result.returncode)
