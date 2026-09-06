"""Run only the two existing bottom-supported sliding-cube decks, three binaries."""
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.contact_shear_coupon import audit
from fea.floor_contact_results import blocks
from fea.mortar_build.build import BASE, ROOT, TAG


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    archive_root = Path('fea/results/contact_shear_coupon')
    published = json.loads((archive_root/'report.json').read_text())
    raw = (archive_root/published['archive']).read_bytes()
    if digest(raw) != published['archive_sha256']:
        raise ValueError('Published cube archive changed')
    directory = Path(tempfile.mkdtemp(prefix='baseline-cube-', dir=ROOT)).resolve()
    print('Cube comparison: '+str(directory), flush=True)
    runs = []
    with tarfile.open(archive_root/published['archive']) as archive:
        for case in ('mortar_0p25', 'mortar_0p125'):
            original = {suffix: archive.extractfile('bottom-supported/'+case+'.'+suffix).read() for suffix in ('inp', 'json', 'dat', 'sta')}
            context = json.loads(original['json'])
            if digest(original['inp']) != context['deck_sha256']:
                raise ValueError('Archived deck/context mismatch')
            for label, image, binary in (('packaged-original', BASE, '/usr/bin/ccx'),
                                         ('packaged-new-libraries', TAG, '/usr/bin/ccx'),
                                         ('upstream', TAG, '/usr/local/bin/ccx-upstream-2.21')):
                work = directory/(case+'-'+label)
                work.mkdir()
                (work/'cube.inp').write_bytes(original['inp'])
                (work/'original.context.json').write_bytes(original['json'])
                container = 'ccx-baseline-'+work.name+'-'+directory.name.rsplit('-', 1)[-1]
                command = ['docker', 'run', '--rm', '--name', container, '--user', f'{os.getuid()}:{os.getgid()}',
                           '-e', 'OMP_NUM_THREADS=2', '-v', str(work)+':/work', '-w', '/work', image, binary, '-i', 'cube']
                with (work/'cube.log').open('w') as log:
                    try:
                        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=False)
                    except subprocess.TimeoutExpired:
                        subprocess.run(['docker', 'kill', container], capture_output=True, check=False)
                        raise
                if result.returncode != 0 or '*ERROR' in (work/'cube.log').read_text().upper():
                    raise ValueError('Cube solver failed; preserve '+str(work))
                data = (work/'cube.dat').read_text()
                endpoints = audit(data, context)
                if not all(ep[key] for ep in endpoints for key in ('force_pass', 'moment_pass', 'aggregate_friction_pass')):
                    raise ValueError('Cube global diagnostic failed')
                original_blocks, current = blocks(original['dat'].decode()), blocks(data)
                if original_blocks.keys() != current.keys() or any(original_blocks[k].keys() != current[k].keys() for k in current):
                    raise ValueError('Cube result coverage changed')
                differences = {kind: max(abs(a-b) for k in current if k[0] == kind for n, vec in current[k].items()
                                         for a, b in zip(vec, original_blocks[k][n], strict=True)) for kind in ('forces', 'displacements')}
                old_sta = [line.split() for line in original['sta'].decode().splitlines() if len(line.split()) == 7 and line.split()[0].isdigit()]
                new_sta = [line.split() for line in (work/'cube.sta').read_text().splitlines() if len(line.split()) == 7 and line.split()[0].isdigit()]
                runs.append({'case': case, 'binary': label, 'command': command, 'deck_sha256': context['deck_sha256'],
                             'endpoints': endpoints, 'maximum_printed_difference_from_archive': differences,
                             'accepted_history_equal_to_archive': old_sta == new_sta,
                             'output_sha256': {p.name: digest(p.read_bytes()) for p in work.iterdir() if p.is_file()}})
    report = {'status': 'BASELINE BUILD COMPARISON ONLY; NO OBSERVER OR LOCAL LAW VALIDATION',
              'reference_archive_sha256': published['archive_sha256'], 'base_image_id': BASE,
              'upstream_image_id': subprocess.check_output(['docker', 'image', 'inspect', TAG, '--format', '{{.Id}}'], text=True).strip(),
              'runs': runs}
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'report': str(directory/'report.json'), 'differences': [r['maximum_printed_difference_from_archive'] for r in runs],
                      'all_histories_equal': all(r['accepted_history_equal_to_archive'] for r in runs)}), flush=True)


if __name__ == '__main__':
    main()
