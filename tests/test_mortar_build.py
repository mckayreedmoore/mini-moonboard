import hashlib
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from fea.contact_shear_coupon import audit
from fea.floor_contact_results import blocks
from fea.mortar_build.build import BASE, BASE_TAG, TAG
from fea.mortar_build.compare_cube import cube_command


def test_failed_docker_build_persists_evidence_and_exits_nonzero(tmp_path, monkeypatch):
    from fea.mortar_build import build

    monkeypatch.setattr(build, 'ROOT', tmp_path)
    monkeypatch.setattr(build.subprocess, 'check_output', lambda *a, **k: BASE+'\n')
    def run(command, **kwargs):
        if command[:2] == ['docker', 'build']:
            kwargs['stdout'].write('controlled build failure\n')
            return SimpleNamespace(returncode=7)
        if command[3] == BASE_TAG:
            return SimpleNamespace(returncode=0, stdout=BASE+'\n')
        assert command[3] == TAG
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(build.subprocess, 'run', run)
    with pytest.raises(SystemExit) as error:
        build.main()
    assert error.value.code == 7
    directory, = tmp_path.glob('baseline-*')
    record = json.loads((directory/'build_result.json').read_text())
    assert record['exit_code'] == 7
    assert record['build_log_sha256'] == hashlib.sha256((directory/'build.log').read_bytes()).hexdigest()


def test_cube_commands_reject_mutable_tag():
    with pytest.raises(ValueError, match='immutable'):
        cube_command(Path('/tmp/cube'), 'cube', TAG, '/usr/bin/ccx')
    command = cube_command(Path('/tmp/cube'), 'cube', BASE, '/usr/bin/ccx')
    assert command[-4:] == [BASE, '/usr/bin/ccx', '-i', 'cube']


@pytest.mark.parametrize('bad', [None, 'manifest', 'binary'])
def test_prelaunch_image_manifest_and_binary_hashes_are_verified(monkeypatch, bad):
    from fea.mortar_build import compare_cube

    publication = json.loads((compare_cube.ROOT/'report.json').read_text())
    manifest = (Path(publication['build_directory'])/'build_manifest.json').read_bytes()
    calls = []
    def check_output(command, **kwargs):
        calls.append(command)
        assert command[3] in (BASE, publication['upstream_image_id'])
        if command[4] == 'cat':
            return b'wrong manifest' if bad == 'manifest' else manifest
        return ''.join(f'{"0"*64 if bad == "binary" else publication["binary_sha256"][p]}  {p}\n' for p in command[5:])
    monkeypatch.setattr(compare_cube.subprocess, 'check_output', check_output)
    if bad:
        with pytest.raises(ValueError):
            compare_cube.verified_image()
    else:
        image, _ = compare_cube.verified_image()
        assert image == publication['upstream_image_id'] and len(calls) == 3


def test_build_is_separate_pinned_upstream_without_source_edits():
    root = Path('fea/mortar_build')
    docker = (root/'Dockerfile').read_text()
    make = (root/'Makefile.upstream').read_text()
    assert BASE == 'sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646'
    assert len({BASE_TAG, TAG, 'mini-moonboard-fea:box-v1'}) == 3
    assert '52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad' in docker
    assert '/usr/local/bin/ccx-upstream-2.21' in docker
    assert 'sha256sum -c /tmp/packaged-ccx.before.sha256' in docker
    assert 'include Makefile.inc' in make
    assert 'date.pl' not in make  # Do not rewrite upstream source/version files.
    assert 'SCCXF:.f=.o' in make and 'SCCXC:.c=.o' in make
    assert not list(root.glob('*.c')) and not list(root.glob('*.f'))


def test_published_build_and_six_cube_replays_are_bound():
    root = Path('fea/mortar_build')
    published = json.loads((root/'report.json').read_text())
    for field in ('evidence_sha256', 'support_sha256'):
        for path, sha in published[field].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha
    manifest = json.loads((Path(published['build_directory'])/'build_manifest.json').read_text())
    assert len(manifest['upstream_files_sha256']) == published['upstream_original_file_count'] == 1176
    assert manifest['upstream_source_archive_sha256'] == published['source_archive_sha256']
    assert manifest['binary_sha256'] == published['binary_sha256']
    assert [sha for path, sha in manifest['upstream_files_sha256'].items() if path.endswith('/src/stressmortar.c')] == [
        'd7cc1fa5d73aba85bbec7dd48f839e7b05514d91ab996025d089a12c45e84cd6']
    for name, sha in manifest['build_support_sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha
    cube = Path(published['cube_directory'])
    comparison = json.loads((cube/'report.json').read_text())
    assert comparison['upstream_image_id'] == published['upstream_image_id']
    assert len(comparison['runs']) == published['cube_run_count'] == 6
    assert comparison['launch_source_sha256'] == hashlib.sha256((cube/'compare_cube.launch.py').read_bytes()).hexdigest()
    assert (cube/'compare_cube.launch.py').read_bytes() == (root/'compare_cube.py').read_bytes()
    for name, sha in comparison['prelaunch_build_evidence_sha256'].items():
        assert hashlib.sha256((Path(published['build_directory'])/name).read_bytes()).hexdigest() == sha
    previous = json.loads((root/'pre-review-snapshot/report.json').read_text())
    assert previous['cube_directory'] == published['prior_cube_directory']
    for name in ('build.py', 'compare_cube.py'):
        assert hashlib.sha256((root/'pre-review-snapshot'/name).read_bytes()).hexdigest() == previous['support_sha256'][str(root/name)]
    for path, sha in previous['evidence_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha
    assert {(r['case'], r['binary']) for r in comparison['runs']} == {
        (case, binary) for case in ('mortar_0p25', 'mortar_0p125')
        for binary in ('packaged-original', 'packaged-new-libraries', 'upstream')}
    archive_path = Path('fea/results/contact_shear_coupon/solver_evidence.tar.gz')
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == comparison['reference_archive_sha256']
    with tarfile.open(archive_path) as archive:
        originals = {case: {suffix: archive.extractfile('bottom-supported/'+case+'.'+suffix).read()
                            for suffix in ('inp', 'dat', 'sta')}
                     for case in ('mortar_0p25', 'mortar_0p125')}
    for run in comparison['runs']:
        expected_image = BASE if run['binary'] == 'packaged-original' else published['upstream_image_id']
        assert run['command'][-4] == expected_image
        work = cube/(run['case']+'-'+run['binary'])
        for name, sha in run['output_sha256'].items():
            assert hashlib.sha256((work/name).read_bytes()).hexdigest() == sha
        context = json.loads((work/'original.context.json').read_text())
        assert hashlib.sha256((work/'cube.inp').read_bytes()).hexdigest() == run['deck_sha256'] == context['deck_sha256']
        assert audit((work/'cube.dat').read_text(), context) == run['endpoints']
        assert all(ep[k] for ep in run['endpoints'] for k in ('force_pass', 'moment_pass', 'aggregate_friction_pass'))
        assert run['maximum_printed_difference_from_archive'] == {'forces': 0., 'displacements': 0.}
        assert run['accepted_history_equal_to_archive']
        original = originals[run['case']]
        assert (work/'cube.inp').read_bytes() == original['inp']
        assert blocks((work/'cube.dat').read_text()) == blocks(original['dat'].decode())
        def accepted(text):
            return [line.split() for line in text.splitlines() if len(line.split()) == 7 and line.split()[0].isdigit()]
        assert accepted((work/'cube.sta').read_text()) == accepted(original['sta'].decode())
