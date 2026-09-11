"""Weights follow geometry/materials, not rotated bounding-box dimensions."""
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
    assert len(saved['models']) == 49
    generated = {'2x10', '2x12', '2x8-shallow', '2x8-foot100'}
    for key, row in saved['models'].items():
        assert row['mass_kg'] > 0 and row['mass_lb'] == pytest.approx(row['mass_kg']/.45359237)
        assert row['mesh_mass_kg'] == pytest.approx(sum(row['mesh_material_mass_kg'].values()))
        assert row['mesh_part_count'] == len(row['mesh_sha256'])
        manifest = Path('site', row['manifest_path'])
        if not manifest.exists():
            # These four historical assemblies are generated before the catalog
            # in static.yml, not committed. Other missing geometry is a defect.
            assert key in generated
            continue
        assert weights.sha(manifest.read_bytes()) == row['manifest_sha256']
        parts = json.loads(manifest.read_text())['parts']
        assert {p['path'] for p in parts} == row['mesh_sha256'].keys()
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
    current = saved['models']['angle-base-development']
    assert current['mass_kg'] == pytest.approx(192.6599020241248)


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
