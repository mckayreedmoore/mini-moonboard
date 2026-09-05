"""Contact result gates, independent of Gmsh installation."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from fea.joint_contact_results import audit, audit_deck, job_name, number


def test_parameter_names_do_not_alias_nearby_floats():
    original = job_name('S', 8, 100000, .2375)
    assert original == 'contact_S_8_100000_0p2375'
    assert job_name('S', 8.0000001, 100000, .2375) != original
    assert job_name('S', 8, 100000.01, .2375) != original
    assert job_name('S', 8, 100000, .2375000001) != original


def test_solver_numbers_roundtrip_without_penalty_or_motion_truncation():
    for value in (100000, 100000.01, .2375000001+.03, .2375+.03, 0):
        assert float(number(value)) == value
    assert number(100000) == '100000'


def fixture():
    context = {'nodes': {str(i): [0., 0., 0.] for i in range(1, 6)}, 'driven': [1], 'min_jacobian': 1.,
               'pins': {f'PIN{i}': [i+1] for i in range(1, 5)},
               'args': {'direction': 'S', 'penalty': 100000}, 'imposed_displacement_mm': .2675}
    text = ' displacements (vx,vy,vz) for set ALLN and time  0.1000000E+01\n\n'
    text += '1 0 .2675 0\n'+''.join(f'{i} 0 0 0\n' for i in range(2, 6))
    for label, tag, force in [('DRIVE', 1, 1000), ('PIN1_N', 2, -1000),
                               ('PIN2_N', 3, 0), ('PIN3_N', 4, 0), ('PIN4_N', 5, 0)]:
        text += f'\n forces (fx,fy,fz) for set {label} and time  0.1000000E+01\n\n{tag} 0 {force} 0\n'
        text += f'\n total force (fx,fy,fz) for set {label} and time  0.1000000E+01\n\n0 {force} 0\n'
    text += '\n relative contact displacement for time 0.1000000E+01\n\n1 1 -.001 0 0\n'
    text += '\n contact stress for time 0.1000000E+01\n\n1 1 100 0 0\n'
    text += '\n total number of contact elements for time 0.1000000E+01\n\n1\n'
    return text, context, '1 1 1 10 1.0 1.0 1.0\n', 'CalculiX Version 2.21\nJob finished'


def test_contact_equilibrium_and_actual_penalty_sign():
    result = audit(*fixture())
    assert result['driven_force_axis_n'] == 1000
    assert result['pin_axis_share'] == [1, 0, 0, 0]
    assert result['max_penalty_penetration_mm'] == .001
    assert result['moment_tolerance_nmm'] == 1


@pytest.mark.parametrize('old,new', [
    ('1 0 .2675 0', '1 0 -.2675 0'),
    ('2 0 0 0', '2 .01 0 0'),
    ('5 0 0 0\n', ''),
    ('1 0 .2675 0', '1 0 nan 0'),
    ('2 0 -1000 0', '2 0 -1001 0'),
    ('1 1 100 0 0', '1 1 -100 0 0'),
    ('1 1 100 0 0', '1 1 100 1 0'),
    ('1 1 -.001 0 0', '1 1 .001 0 0'),
    ('0.1000000E+01', '0.9000000E+00'),
])
def test_bad_contact_outputs_fail_closed(old, new):
    text, context, status, log = fixture()
    with pytest.raises(ValueError):
        audit(text.replace(old, new), context, status, log)


def test_nonfinal_solver_and_unbalanced_moment_rejected():
    text, context, status, log = fixture()
    with pytest.raises(ValueError):
        audit(text, context, status.replace('1.0', '.9'), log)
    with pytest.raises(ValueError):
        audit(text, context, status, log+'\n*ERROR')
    context['nodes']['2'][0] = .002
    with pytest.raises(ValueError, match='equilibrium'):
        audit(text, context, status, log)


def deck_fixture():
    directory = Path('fea/results/joint_contact/reference_raw')
    name = 'contact_S_8_100000_0p2375'
    text = gzip.decompress((directory/(name+'.inp.gz')).read_bytes()).decode()
    context = json.loads(gzip.decompress((directory/(name+'.context.json.gz')).read_bytes()))
    return text, context


@pytest.mark.parametrize('old,new', [
    ('7000,0.3', '70,0.3'), ('*STEP,NLGEOM,INC=1000', '*STEP,INC=1000'),
    ('DRIVE,2,2,0.2675', 'DRIVE,2,2,-0.2675'), ('1,1,1e-6,1', '.05,1,1e-6,.1'),
    ('ELSET=WOOD,MATERIAL=WOOD_SCREEN', 'ELSET=WOOD,MATERIAL=FIXED_PIN'),
    ('PIN4_N,1,3,0\n', ''), ('*END STEP', '*CLOAD\n1,2,1000\n*END STEP'),
    ('7000,0.3', '7000,0.3\n*ELASTIC\n70,0.3'),
    ('*END STEP', '*EQUATION\n2\n1,1,1,2,1,-1\n*END STEP'),
    ('*END STEP', '*BOUNDARY,OP=NEW\nALLN,1,3,0\n*END STEP'),
    ('*END STEP', '*BOUNDARY,OP=MOD\nALLN,1,3,0\n*END STEP'),
])
def test_actual_deck_materials_boundary_and_step_are_audited(old, new):
    text, context = deck_fixture()
    assert old in text
    audit_deck(text, context)
    with pytest.raises(ValueError):
        audit_deck(text.replace(old, new), context)


def test_contact_surfaces_cannot_be_removed_or_given_invalid_faces():
    import re
    text, context = deck_fixture()
    missing = re.sub(r'\*SURFACE,NAME=[^\n]*\n[^*]*', '', text)
    with pytest.raises(ValueError, match='surfaces'):
        audit_deck(missing, context)
    with pytest.raises(ValueError, match='face'):
        audit_deck(text.replace(',S1\n', ',S5\n'), context)


@pytest.mark.parametrize('removal', ['one_face', 'whole_bore'])
def test_contact_surface_requires_every_exterior_bore_face(removal):
    import re
    text, context = deck_fixture()
    surface = re.search(r'(\*SURFACE,NAME=WOOD_SURF,TYPE=ELEMENT\n)([^*]+)', text)
    rows = surface[2].strip().splitlines()
    if removal == 'one_face':
        remaining = rows[1:]
    else:
        elements = {}
        for block in re.finditer(r'\*ELEMENT,[^\n]*\n([^*]+)', text):
            for row in block[1].strip().splitlines():
                values = [int(v) for v in row.split(',')]
                elements[values[0]] = values[1:]
        indices = ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0))
        remaining = []
        removed = 0
        for row in rows:
            e, face = row.split(',')
            tags = [elements[int(e)][i] for i in indices[int(face[1:])-1]]
            centre_s = sum(context['nodes'][str(t)][1] for t in tags)/3
            if abs(centre_s-60) < 6:
                removed += 1
            else:
                remaining.append(row)
        assert removed > 100
    changed = text[:surface.start(2)]+'\n'.join(remaining)+'\n'+text[surface.end(2):]
    with pytest.raises(ValueError, match='coverage'):
        audit_deck(changed, context)


def test_published_contact_evidence_reaudits_when_raw_available():
    from fea.record_joint_contact import checked
    paths = list(Path('fea/results/joint_contact').glob('contact_*.json'))
    assert paths, 'Expected at least one accepted real contact coupon'
    for path in paths:
        record = json.loads(path.read_text())
        assert record['min_jacobian'] > 0 and record['completed_time'] == 1
        assert record['moment_residual_fraction_of_limit'] <= 1
        assert max(map(abs, record['force_residual_n'])) <= .1
        assert sum(record['pin_axis_share']) == pytest.approx(1, abs=1e-5)
        for source, digest in record['audit_source_sha256'].items():
            assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest
        raw = Path('fea/generated/joint_contact')/path.stem
        if raw.with_suffix('.dat').exists():
            for filename, digest in record['evidence_sha256'].items():
                assert hashlib.sha256((raw.parent/filename).read_bytes()).hexdigest() == digest
            assert checked(raw) == record


def test_reference_reaudits_from_published_compressed_evidence(tmp_path):
    from fea.record_joint_contact import checked
    directory = Path('fea/results/joint_contact')
    name = 'contact_S_8_100000_0p2375'
    record = json.loads((directory/(name+'.json')).read_text())
    expected = {*record['evidence_sha256'], 'leg.step'}
    paths = list((directory/'reference_raw').glob('*.gz'))
    assert {p.name[:-3] for p in paths} == expected
    for path in paths:
        (tmp_path/path.name[:-3]).write_bytes(gzip.decompress(path.read_bytes()))
    for filename, digest in record['evidence_sha256'].items():
        assert hashlib.sha256((tmp_path/filename).read_bytes()).hexdigest() == digest
    assert checked(tmp_path/name) == record


def test_presolved_hashes_prevent_relabelled_inputs(tmp_path, monkeypatch):
    from fea import record_joint_contact as recorder
    prefix = tmp_path/'contact_mock'
    (tmp_path/'leg.step').write_text('geometry')
    context = {'name': prefix.name, 'geometry': {'candidate': '2x8-foot100', 'step_sha256': hashlib.sha256(b'geometry').hexdigest()}}
    for suffix in ('.inp', '.dat', '.sta', '.log', '.cvg'):
        prefix.with_suffix(suffix).write_text('original')
    prefix.with_suffix('.context.json').write_text(json.dumps(context))
    prefix.with_suffix('.run.json').write_text(json.dumps({
        'input_sha256': hashlib.sha256(b'original').hexdigest(),
        'context_sha256': hashlib.sha256(prefix.with_suffix('.context.json').read_bytes()).hexdigest()}))
    monkeypatch.setattr(recorder, 'audit_deck', lambda *args: None)
    monkeypatch.setattr(recorder, 'audit', lambda *args: {})
    recorder.checked(prefix)
    prefix.with_suffix('.inp').write_text('changed')
    with pytest.raises(ValueError, match='pre-solve'):
        recorder.checked(prefix)
    prefix.with_suffix('.inp').write_text('original')
    context['extra'] = 'changed'
    prefix.with_suffix('.context.json').write_text(json.dumps(context))
    with pytest.raises(ValueError, match='pre-solve'):
        recorder.checked(prefix)


def test_preparation_reuses_verified_snapshot_without_rewriting(tmp_path, monkeypatch):
    from fea import prepare_joint_contact as prepare
    monkeypatch.chdir(tmp_path)
    for source in prepare.SOURCES:
        path = Path(source)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('source')
    directory = Path('fea/generated/joint_contact')
    directory.mkdir(parents=True)
    step = directory/'leg.step'
    step.write_bytes(b'frozen geometry')
    info = {'candidate': '2x8-foot100', 'step_sha256': hashlib.sha256(step.read_bytes()).hexdigest(),
            'source_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in prepare.SOURCES}}
    metadata = directory/'geometry.json'
    metadata.write_text(json.dumps(info))
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (step, metadata)}
    monkeypatch.setattr(prepare.frame, 'parts', lambda *args: pytest.fail('Verified snapshot regenerated'))
    prepare.main()
    prepare.main()
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (step, metadata)} == before
    Path(prepare.SOURCES[0]).write_text('changed source')
    with pytest.raises(ValueError, match='Archive the complete'):
        prepare.main()
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (step, metadata)} == before


def test_preparation_rejects_incomplete_or_corrupt_existing_snapshot(tmp_path):
    from fea.prepare_joint_contact import reuse_snapshot
    assert not reuse_snapshot(tmp_path)
    (tmp_path/'leg.step').write_text('orphan')
    with pytest.raises(ValueError, match='nothing was overwritten'):
        reuse_snapshot(tmp_path)
    (tmp_path/'geometry.json').write_text('{')
    with pytest.raises(ValueError, match='nothing was overwritten'):
        reuse_snapshot(tmp_path)
