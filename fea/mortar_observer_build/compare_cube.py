"""Bounded unchanged cube runs comparing observer and unmodified upstream solver."""
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.contact_shear_coupon import audit
from fea.floor_contact_results import blocks
from fea.mortar_build.compare_cube import cube_command, verified_image

ROOT = Path(__file__).parent
BUILD = ROOT/'build-rvk4q426'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    upstream, _ = verified_image()
    built = json.loads((BUILD/'build_result.json').read_text())
    if built['exit_code'] or built['parent_image_id'] != upstream:
        raise ValueError('Successful observer build from verified upstream required')
    for path, expected in built['evidence_sha256'].items():
        if sha(BUILD/path) != expected:
            raise ValueError('Observer build evidence changed')
    image = built['image_id']
    manifest_bytes = subprocess.check_output(['docker', 'run', '--rm', image, 'cat',
                                             '/opt/ccx-observer-2.21/build_manifest.json'], timeout=30)
    if manifest_bytes != (BUILD/'build_manifest.json').read_bytes():
        raise ValueError('Observer image manifest differs')
    manifest = json.loads(manifest_bytes)
    measured = subprocess.check_output(['docker', 'run', '--rm', image, 'sha256sum',
                                        *sorted(manifest['binary_sha256'])], text=True, timeout=30)
    if {p: h for h, p in (line.split() for line in measured.splitlines())} != manifest['binary_sha256']:
        raise ValueError('Observer image binary differs')
    archive_root = Path('fea/results/contact_shear_coupon')
    published = json.loads((archive_root/'report.json').read_text())
    archive_path = archive_root/published['archive']
    if sha(archive_path) != published['archive_sha256']:
        raise ValueError('Reference archive changed')
    directory = Path(tempfile.mkdtemp(prefix='cube-', dir=ROOT)).resolve()
    (directory/'compare_cube.launch.py').write_bytes(Path(__file__).read_bytes())
    print('Observer cube evidence: '+str(directory), flush=True)
    runs = []
    with tarfile.open(archive_path) as archive:
        for case in ('mortar_0p25', 'mortar_0p125'):
            original = {suffix: archive.extractfile('bottom-supported/'+case+'.'+suffix).read()
                        for suffix in ('inp', 'json', 'dat', 'sta')}
            context = json.loads(original['json'])
            if hashlib.sha256(original['inp']).hexdigest() != context['deck_sha256']:
                raise ValueError('Reference deck/context mismatch')
            for label, target, binary in (
                ('upstream', upstream, '/usr/local/bin/ccx-upstream-2.21'),
                ('observer', image, '/usr/local/bin/ccx-observer-2.21'),
            ):
                work = directory/(case+'-'+label)
                work.mkdir()
                (work/'cube.inp').write_bytes(original['inp'])
                (work/'original.context.json').write_bytes(original['json'])
                container = 'observer-'+directory.name+'-'+case+'-'+label
                command = cube_command(work, container, target, binary)
                with (work/'cube.log').open('w') as log:
                    try:
                        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                                timeout=60, check=False)
                    except subprocess.TimeoutExpired:
                        subprocess.run(['docker', 'kill', container], capture_output=True, check=False)
                        raise
                data = (work/'cube.dat').read_text()
                if result.returncode or '*ERROR' in (work/'cube.log').read_text().upper():
                    raise ValueError('Cube execution failed; raw evidence retained')
                reference, current = blocks(original['dat'].decode()), blocks(data)
                if reference.keys() != current.keys() or any(reference[k].keys() != current[k].keys() for k in current):
                    raise ValueError('Cube output coverage differs')
                differences = {kind: max(abs(a-b) for k in current if k[0] == kind
                                        for n, vector in current[k].items()
                                        for a, b in zip(vector, reference[k][n], strict=True))
                               for kind in ('forces', 'displacements')}
                history = lambda text: [line.split() for line in text.splitlines()
                                        if len(line.split()) == 7 and line.split()[0].isdigit()]
                equal = history(original['sta'].decode()) == history((work/'cube.sta').read_text())
                endpoints = audit(data, context)
                runs.append({'case': case, 'binary': label, 'command': command,
                             'deck_sha256': context['deck_sha256'], 'exit_code': result.returncode,
                             'maximum_printed_difference_from_archive': differences,
                             'accepted_history_equal_to_archive': equal, 'endpoints': endpoints,
                             'output_sha256': {p.name: sha(p) for p in sorted(work.iterdir()) if p.is_file()}})
    report = {'status': 'OBSERVER OUTPUT COMPARISON ONLY; INTERNAL REPLAY AND LOCAL LAW QUALIFICATION SEPARATE',
              'build_result_sha256': sha(BUILD/'build_result.json'),
              'build_manifest_sha256': sha(BUILD/'build_manifest.json'), 'build_directory': str(BUILD),
              'reference_archive_sha256': published['archive_sha256'],
              'launch_source_sha256': sha(directory/'compare_cube.launch.py'), 'runs': runs}
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    okay = all(not any(r['maximum_printed_difference_from_archive'].values()) and
               r['accepted_history_equal_to_archive'] and
               all(ep[k] for ep in r['endpoints'] for k in ('force_pass', 'moment_pass', 'aggregate_friction_pass'))
               for r in runs)
    print(json.dumps({'report': str(directory/'report.json'), 'comparison_equal': okay}), flush=True)
    if not okay:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
