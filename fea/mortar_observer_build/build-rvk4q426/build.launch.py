"""Bounded separate observer build from the verified unmodified upstream image."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from fea.mortar_build.compare_cube import verified_image

ROOT = Path(__file__).parent
BASE_TAG = 'mini-moonboard-fea:observer-base-5adec98a0bb4'
TAG = 'mini-moonboard-fea:ccx-observer-2.21-v1'


def main():
    parent, parent_evidence = verified_image()
    if parent != 'sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0':
        raise ValueError('Observer requires the reviewed upstream baseline')
    probe = subprocess.run(['docker', 'image', 'inspect', BASE_TAG, '--format', '{{.Id}}'],
                           capture_output=True, text=True, timeout=30, check=False)
    if probe.returncode == 0 and probe.stdout.strip() != parent:
        raise ValueError('Observer base alias conflicts; do not overwrite it')
    if probe.returncode:
        subprocess.run(['docker', 'tag', parent, BASE_TAG], timeout=30, check=True)
    if subprocess.run(['docker', 'image', 'inspect', TAG], capture_output=True,
                      timeout=30, check=False).returncode == 0:
        raise ValueError('Observer tag exists; preserve the evidence image')
    directory = Path(tempfile.mkdtemp(prefix='build-', dir=ROOT))
    context = directory/'context'
    context.mkdir()
    for name, source in {
        'Dockerfile': ROOT/'Dockerfile', 'record_build.py': ROOT/'record_build.py',
        'patch.py': ROOT.parent/'mortar_observer/patch.py',
    }.items():
        shutil.copyfile(source, context/name)
    shutil.copyfile(__file__, directory/'build.launch.py')
    command = ['docker', 'build', '--progress=plain', '--build-arg', 'BASE_IMAGE='+BASE_TAG,
               '-t', TAG, str(context)]
    print('Observer build evidence: '+str(directory), flush=True)
    record = {'parent_image_id': parent, 'parent_evidence_sha256': parent_evidence,
              'tag': TAG, 'command': command}
    with (directory/'build.log').open('w') as log:
        try:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=300, check=False)
            record['exit_code'] = result.returncode
        except subprocess.TimeoutExpired:
            record['exit_code'] = 124
            record['timed_out'] = True
    if record['exit_code'] == 0:
        image = subprocess.check_output(['docker', 'image', 'inspect', TAG, '--format', '{{.Id}}'],
                                        text=True, timeout=30).strip()
        record['image_id'] = image
        inspected = json.loads(subprocess.check_output(['docker', 'image', 'inspect', parent, image], timeout=30))
        layers = inspected[0]['RootFS']['Layers']
        if inspected[1]['RootFS']['Layers'][:len(layers)] != layers:
            record['exit_code'] = 1
            record['verification_error'] = 'Immutable parent layers differ'
        else:
            manifest = subprocess.check_output(['docker', 'run', '--rm', image, 'cat',
                                                '/opt/ccx-observer-2.21/build_manifest.json'], timeout=30)
            (directory/'build_manifest.json').write_bytes(manifest)
    record['evidence_sha256'] = {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob('*')) if path.is_file()
    }
    (directory/'build_result.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)
    if record['exit_code']:
        raise SystemExit(record['exit_code'] if record['exit_code'] > 0 else 1)


if __name__ == '__main__':
    main()
