"""Verify the new whole-frame geometry scope, floor extensions and publication."""
import hashlib
import json
from pathlib import Path

import pytest

from mini_moonboard import no_shoes_frame as model


@pytest.fixture(scope='module')
def parts():
    return {p.name: p for p in model.parts()}


def test_no_shoes_restores_catalog_base_and_retains_hardware(parts):
    assert not any('steel_shoe' in name or 'clip_plate_' in name for name in parts)
    assert {'clip_angle_base_left', 'clip_angle_base_right'} <= parts.keys()
    connections = model.connections()
    assert sum(c.name.startswith('clip_angle_base_') for c in connections) == 12
    assert sum(c.name.startswith('lumber_leg_bolt_') for c in connections) == 8
    assert len(model.panel_connections()) == 66
    assert sum(name.startswith('hold_tnut_') for name in parts) == 142
    assert not any('steel_shoe' in c.name for c in connections)
    # Untrimmed, shoe-hole-free predecessor rims survive exactly, shifted up.
    old = {p.name: p for p in model.previous.parts()}
    for side in ('left', 'right'):
        name = 'base_side_'+side
        assert parts[name].shape.Volume() == pytest.approx(old[name].shape.Volume(), abs=.001)
        assert parts[name].shape.BoundingBox().zmin == pytest.approx(model.base.HEADER_TOP)


def test_277mm_height_and_floor_contact_preserve_stock(parts):
    assert model.KICKER_HEIGHT_MM == 277.
    assert model.KICKER_HEIGHT_MM-model.PAD_HEIGHT_MM == 150.
    assert model.b.point(0., 0., 0.).z == pytest.approx(model.previous.b.point(0., 0., 0.).z+52.)
    old = {p.name: p for p in model.previous.parts()}
    _, _, along, _ = model.leg_source.geometry('2x6', 0.)
    for name, part in parts.items():
        if name.startswith(('base_post_', 'kicker_', 'lumber_leg_')):
            assert part.shape.BoundingBox().zmin == pytest.approx(0., abs=1.e-6)
            assert part.shape.isValid()
            assert len(part.shape.Solids()) == 1
        if name.startswith('lumber_leg_'):
            assert part.blank[1:] == (139.7, 38.1)
            assert part.blank[0]-old[name].blank[0] == pytest.approx(52./along.z)
            assert part.shape.Volume()-old[name].shape.Volume() == pytest.approx(139.7*38.1*52./along.z)
        if name.startswith('base_post_'):
            assert part.blank[0]-old[name].blank[0] == pytest.approx(52.)
    for row in model.tnuts.datums(model):
        if row['panel'].startswith('kicker_'):
            assert row['rear_seating_xyz_mm'][2] == pytest.approx(202.)


def test_new_kicker_screws_clear_restored_angles(parts):
    for connection in model.panel_connections():
        if not connection.name.startswith('kicker_header_'):
            continue
        for component in connection.components():
            for side in ('left', 'right'):
                assert component.intersect(parts['clip_angle_base_'+side].shape).Volume() < .01


def test_published_asset_provenance_and_translations():
    root = Path(__file__).resolve().parents[1]
    directory = root/'site/hybrid'/model.KEY
    manifest = json.loads((directory/'manifest.json').read_text())
    for key, base in [('source_sha256', root), ('artifact_sha256', directory),
                      ('inherited_mesh_sha256', root/'site')]:
        for name, expected in manifest[key].items():
            assert hashlib.sha256((base/name).read_bytes()).hexdigest() == expected, name
    data = json.loads((directory/'parts.json').read_text())
    assert data['design']['main_face_height_mm'] == 277.
    assert data['design']['qualified_for_design'] is False
    assert data['bounds_mm'][0][2] == pytest.approx(0., abs=1.e-6)
    for part in data['parts']:
        inherited = part['path'] in manifest['inherited_mesh_sha256']
        assert part.get('translation_mm', [0., 0., 0.]) == ([0., 0., 52.] if inherited else [0., 0., 0.])
