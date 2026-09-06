"""Bounded new-image build; never retag or replace the existing packaged image."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

BASE = 'sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646'
BASE_TAG = 'mini-moonboard-fea:base-37671083a88d'
TAG = 'mini-moonboard-fea:ccx-upstream-2.21-v1'
ROOT = Path(__file__).parent


def main():
    actual = subprocess.check_output(['docker', 'image', 'inspect', 'mini-moonboard-fea:box-v1', '--format', '{{.Id}}'], text=True).strip()
    if actual != BASE:
        raise ValueError('Packaged base image ID changed')
    # BuildKit interprets a bare local sha256 ID as a registry image name.
    # Bind a separate local tag directly to the ID, without touching box-v1.
    probe = subprocess.run(['docker', 'image', 'inspect', BASE_TAG, '--format', '{{.Id}}'], capture_output=True, text=True, check=False)
    if probe.returncode == 0 and probe.stdout.strip() != BASE:
        raise ValueError('Immutable-base alias already names another image')
    if probe.returncode != 0:
        subprocess.run(['docker', 'tag', BASE, BASE_TAG], check=True)
    if subprocess.run(['docker', 'image', 'inspect', TAG], capture_output=True, check=False).returncode == 0:
        raise ValueError('New image tag already exists; do not overwrite an evidence image')
    directory = Path(tempfile.mkdtemp(prefix='baseline-', dir=ROOT))
    print('Build evidence: '+str(directory), flush=True)
    with (directory/'build.log').open('w') as log:
        result = subprocess.run(['docker', 'build', '--progress=plain', '--build-arg', 'BASE_IMAGE='+BASE_TAG, '-t', TAG, str(ROOT)],
                                stdout=log, stderr=subprocess.STDOUT, timeout=900, check=False)
    record = {'base_image_id': BASE, 'tag': TAG, 'exit_code': result.returncode,
              'build_log_sha256': hashlib.sha256((directory/'build.log').read_bytes()).hexdigest()}
    if result.returncode == 0:
        record['image_id'] = subprocess.check_output(['docker', 'image', 'inspect', TAG, '--format', '{{.Id}}'], text=True).strip()
        base_layers = json.loads(subprocess.check_output(['docker', 'image', 'inspect', BASE]))[0]['RootFS']['Layers']
        new_layers = json.loads(subprocess.check_output(['docker', 'image', 'inspect', record['image_id']]))[0]['RootFS']['Layers']
        if new_layers[:len(base_layers)] != base_layers:
            raise ValueError('New image does not contain immutable base layers')
        manifest = subprocess.check_output(['docker', 'run', '--rm', record['image_id'], 'cat', '/opt/ccx-upstream-2.21/build_manifest.json'])
        (directory/'build_manifest.json').write_bytes(manifest)
    (directory/'build_result.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode if result.returncode > 0 else 1)


if __name__ == '__main__':
    main()
