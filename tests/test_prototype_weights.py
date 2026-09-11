"""Weights follow geometry/materials, not rotated bounding-box dimensions."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import build_prototype_weights as weights


def tetrahedron(offset=0, reverse=False, opened=False):
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)+offset
    faces = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
    if opened:
        faces.pop()
    lines = ['solid test']
    for face in faces:
        for vertex in points[face[::-1] if reverse else face]:
            lines.append('vertex '+' '.join(map(str, vertex)))
    return ('\n'.join(lines)+'\nendsolid').encode()


def test_closed_mesh_volume_translation_orientation_and_open_rejection():
    for offset in (0., 5000.):
        for reverse in (False, True):
            assert weights.volume(tetrahedron(offset, reverse)) == pytest.approx(1/6)
    with pytest.raises(ValueError, match='Open STL'):
        weights.volume(tetrahedron(opened=True))
    with pytest.raises(ValueError, match='Open STL'):
        weights.volume(tetrahedron(opened=True)*2)
    lines = tetrahedron().decode().splitlines()
    lines[1:4] = reversed(lines[1:4])
    with pytest.raises(ValueError, match='orientation'):
        weights.volume('\n'.join(lines).encode())


def test_material_conventions_include_hardware_and_zinc_inserts():
    for name, kind, expected in (
        ('base_header', 'part', 'wood/plywood'), ('angle_left_top', 'part', 'steel'),
        ('transition_seam_angle_left', 'part', 'steel'), ('analysis_leg_bolt', None, 'steel'),
        ('insert_panel_1', 'insert', 'die-cast zinc assumption')):
        assert weights.material({'name': name, 'fabrication': {'kind': kind}}) == expected
    with pytest.raises(ValueError, match='Unclassified'):
        weights.material({'name': 'mystery', 'fabrication': {}})


def test_published_catalog_reconciles_and_authenticates_available_geometry():
    saved = json.loads(Path('site/prototype-weights.json').read_text())
    assert saved['generator_sha256'] == weights.sha(Path(weights.__file__).read_bytes())
    assert saved['assumed_density_kg_m3'] == weights.DENSITIES
    assert len(saved['models']) == 52
    generated = {'2x10', '2x12', '2x8-shallow', '2x8-foot100'}
    for key, row in saved['models'].items():
        assert 'T-nuts and hold bolts' in row['scope']
        assert row['mass_kg'] > 0 and row['mass_lb'] == pytest.approx(row['mass_kg']/.45359237)
        assert row['mesh_mass_kg'] == pytest.approx(sum(row['mesh_material_mass_kg'].values()))
        assert row['mesh_part_count'] == len(row['mesh_sha256'])
        excluded = row.get('excluded_mass_parts', [])
        assert row.get('excluded_mass_part_count', 0) == len(excluded)
        assert all(part['kind'] in ('light', 'wire') and part['path'] in row['mesh_sha256'] for part in excluded)
        manifest = Path('site', row['manifest_path'])
        if not manifest.exists():
            # These four historical assemblies are generated before the catalog
            # in static.yml, not committed. Other missing geometry is a defect.
            assert key in generated
            continue
        assert weights.sha(manifest.read_bytes()) == row['manifest_sha256']
        parts = json.loads(manifest.read_text())['parts']
        assert {p['path'] for p in parts} == row['mesh_sha256'].keys()
        assert {part['name'] for part in excluded} == {
            part['name'] for part in parts if part['fabrication'].get('kind') in ('light', 'wire')}
        for name, digest in row['mesh_sha256'].items():
            assert weights.sha(Path('site', name).read_bytes()) == digest
        if key in weights.AUDITED:
            mass, source, digest = weights.audited_mass(key, parts)
            assert row['basis'] == 'audited CAD'
            assert row['mass_kg'] == pytest.approx(mass)
            assert row['mass_report'] == source and row['mass_report_sha256'] == digest
        else:
            assert row['basis'] == 'mesh estimate'
            assert row['mass_kg'] == row['mesh_mass_kg']
    assert saved['models']['angle-base-development']['mass_kg'] == pytest.approx(192.6599020241248)
    current = saved['models']['horizontal-service-development']
    assert current['mass_kg'] == pytest.approx(167.46863512295866)
    assert current['excluded_mass_part_count'] == 263
    current = saved['models']['round-bore-service-development']
    assert current['basis'] == 'audited CAD'
    assert current['excluded_mass_part_count'] == 263
    current = saved['models']['round-insert-development']
    assert current['basis'] == 'audited CAD'
    assert current['excluded_mass_part_count'] == 263
    assert current['mesh_part_count'] == 607


def test_audited_total_rejects_same_name_changed_mesh(monkeypatch):
    key = 'angle-base-development'
    parts = json.loads(Path('site/hybrid', key, 'parts.json').read_text())['parts']
    changed = Path('site', parts[0]['path']).resolve()
    original = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda p: original(p)+b'changed' if p.resolve() == changed else original(p))
    with pytest.raises(ValueError, match='viewer artifact changed'):
        weights.audited_mass(key, parts)


def test_audited_total_rejects_incomplete_bolt_even_when_manifest_rehashed(tmp_path):
    directory = Path('site/hybrid/angle-base-development')
    for path in directory.iterdir():
        if path.is_dir():
            (tmp_path/path.name).symlink_to(path.resolve(), target_is_directory=True)
    record = json.loads((directory/'parts.json').read_text())
    index = next(i for i, p in enumerate(record['parts']) if p['fabrication'].get('hardware_role') == 'nut')
    record['parts'].pop(index)
    raw = json.dumps(record).encode()
    (tmp_path/'parts.json').write_bytes(raw)
    manifest = json.loads((directory/'manifest.json').read_text())
    manifest['artifact_sha256']['parts.json'] = weights.sha(raw)
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Incomplete or duplicate bolt roles'):
        weights.audited_mass('angle-base-development', record['parts'], tmp_path)


def test_purchased_electrical_mass_is_unknown_but_all_meshes_are_hashed(tmp_path):
    parts = []
    for name, kind in (('base_header', 'part'), ('fastener_light', 'light'), ('wood_wire', 'wire')):
        path = name+'.stl'
        (tmp_path/path).write_bytes(tetrahedron())
        parts.append({'name': name, 'path': path, 'fabrication': {'kind': kind}})
    (tmp_path/'parts.json').write_text(json.dumps({'parts': parts}))
    row = weights.build(tmp_path)['models']['plywood']
    assert row['mass_kg'] == pytest.approx((1/6)/1e9*weights.DENSITIES['wood/plywood'])
    assert row['mesh_material_mass_kg'] == {'wood/plywood': row['mass_kg']}
    assert row['mesh_part_count'] == len(row['mesh_sha256']) == 3
    assert row['excluded_mass_part_count'] == 2
    assert {part['name'] for part in row['excluded_mass_parts']} == {'fastener_light', 'wood_wire'}
    assert all('unknown' in part['reason'] for part in row['excluded_mass_parts'])
    assert weights.material(parts[1]) is None and weights.material(parts[2]) is None
    before = row['mesh_sha256']['fastener_light.stl']
    (tmp_path/'fastener_light.stl').write_bytes(tetrahedron(offset=20.))
    changed = weights.build(tmp_path)['models']['plywood']
    assert changed['mass_kg'] == row['mass_kg']
    assert changed['mesh_sha256']['fastener_light.stl'] != before
    assert changed['mesh_sha256']['fastener_light.stl'] == weights.sha((tmp_path/'fastener_light.stl').read_bytes())


def test_audited_mass_excludes_electrical_only_with_explicit_report_and_authenticates_meshes(tmp_path, monkeypatch):
    key = 'electrical-audit-test'
    parts = [{'name': name, 'path': name+'.stl', 'fabrication': {'kind': kind}}
             for name, kind in (('base_header', 'part'), ('lamp', 'light'), ('cable', 'wire'))]
    for part in parts:
        (tmp_path/part['path']).write_bytes(tetrahedron())
    (tmp_path/'parts.json').write_text(json.dumps({'parts': parts}))
    (tmp_path/'manifest.json').write_text(json.dumps({'source_sha256': {}, 'artifact_sha256': {
        path.name: weights.sha(path.read_bytes()) for path in tmp_path.iterdir()}}))
    report = {'candidate': key, 'source_sha256': {}, 'mass_inventory': [{'name': 'base_header', 'mass_kg': 1.}],
              'state': {'mass_kg': 1.}, 'electrical_mass_included': False}
    source = tmp_path/'mass.json.gz'
    source.write_bytes(gzip.compress(json.dumps(report).encode()))
    monkeypatch.setitem(weights.AUDITED, key, source)
    assert weights.audited_mass(key, parts, tmp_path)[0] == 1.
    report['electrical_mass_included'] = True
    source.write_bytes(gzip.compress(json.dumps(report).encode()))
    with pytest.raises(ValueError, match='explicitly exclude'):
        weights.audited_mass(key, parts, tmp_path)
    report['electrical_mass_included'] = False
    source.write_bytes(gzip.compress(json.dumps(report).encode()))
    (tmp_path/'lamp.stl').write_bytes(tetrahedron(offset=1.))
    with pytest.raises(ValueError, match='viewer artifact changed: lamp.stl'):
        weights.audited_mass(key, parts, tmp_path)
