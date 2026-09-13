"""Small real-CAD export checks; no historical assets or full frame build needed."""
import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard import no_shoes_exports as exporter


@pytest.fixture
def small_candidate(monkeypatch):
    shape = cq.Solid.makeBox(10, 20, 30, cq.Vector(5, 6, 7))
    part = SimpleNamespace(name='hold_tnut_kicker_A0', shape=shape,
                           blank=(10, 20, 30), description='Synthetic test part')
    bolt = SimpleNamespace(name='lumber_leg_bolt_left_1', kind='bolt',
                           components=lambda: tuple(shape.translate((i*20, 0, 0)) for i in range(5)),
                           product_status='Synthetic test bolt')
    screw = SimpleNamespace(name='panel_screw', kind='screw', components=lambda: (shape,),
                            length=30, diameter=10, product_status='Synthetic test screw')
    light = SimpleNamespace(name='light_A1', shape=shape, kind='light')
    monkeypatch.setattr(exporter.model, 'parts', lambda: (part,))
    monkeypatch.setattr(exporter.model, 'connections', lambda: (bolt, screw))
    monkeypatch.setattr(exporter.model, 'panel_connections', lambda: (screw,))
    monkeypatch.setattr(exporter.model, 'electrical_parts', lambda: (light,))
    monkeypatch.setattr(exporter.model.tnuts, 'datums', lambda model: (
        {'panel': 'kicker_left', 'rear_seating_xyz_mm': [0, 0, 203]},))
    return part


def test_empty_root_rebuild_preserves_bodies_and_detects_stale_assets(tmp_path, small_candidate):
    directory = exporter.export(tmp_path)
    data = json.loads((directory/'parts.json').read_text())
    assert len(data['parts']) == 8
    assert data['design']['kicker_hold_height_mm'] == 203
    assert data['design']['hold_tnut_count'] == 1
    assert data['design']['panel_kicker_screw_count'] == 1
    assert data['bounds_mm'] == [[5., 6., 7.], [95., 26., 37.]]
    for part in data['parts']:
        assert (tmp_path/part['path']).is_file()
        assert part['path'].startswith('hybrid/'+exporter.model.KEY+'/models/')
        assert 'translation_mm' not in part
    bolt_parts = [p for p in data['parts'] if p['fabrication']['kind'] == 'bolt']
    assert {p['fabrication']['hardware_role'] for p in bolt_parts} == set(exporter.BOLT_ROLES)
    assert all(p['fabrication']['connection_name'] == 'lumber_leg_bolt_left_1' for p in bolt_parts)
    light = next(p for p in data['parts'] if p['fabrication']['kind'] == 'light')
    assert light['fabrication']['mass_included'] is False
    # STEP contains the part, five bolt components and one screw, but no light.
    assert len(cq.importers.importStep(str(directory/'assembly.step')).solids().vals()) == 7
    assert exporter.check(tmp_path) == directory
    stale = tmp_path/data['parts'][0]['path']
    stale.write_bytes(b'stale mesh')
    with pytest.raises(ValueError, match='rebuild differs'):
        exporter.check(tmp_path)


def test_source_inventory_tracks_factory_inputs_not_archived_outputs():
    sources = exporter.sources()
    assert {'mini_moonboard/no_shoes_frame.py', 'mini_moonboard/no_shoes_exports.py',
            'mini_moonboard/round_structural_frame.py', 'mini_moonboard/hold_tnut_reinforcement.py',
            'docs/round-service-wiring-reference.json', 'uv.lock'} <= sources.keys()
    assert not any(name.startswith(('site/', 'exports/', 'fea/')) for name in sources)


def test_source_change_during_export_is_rejected(tmp_path, small_candidate, monkeypatch):
    hashes = iter(({'source': 'before'}, {'source': 'after'}))
    monkeypatch.setattr(exporter, 'sources', lambda: next(hashes))
    with pytest.raises(ValueError, match='Source changed during export'):
        exporter.export(tmp_path)
