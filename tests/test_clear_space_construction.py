"""Construction datums must reconstruct actual drilling points across grain axes."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import clear_space_construction as packet


def test_post_and_floor_corner_datums_reconstruct_same_joint(monkeypatch):
    post = SimpleNamespace(name='base_post_outer_right',
                           shape=cq.Solid.makeBox(38.1, 139.7, 238.9, cq.Vector(1143., -175.7, 0.)))
    rail = SimpleNamespace(name='base_floor_right',
                           shape=cq.Solid.makeBox(38.1, 1880., 139.7, cq.Vector(1181.1, -210., 0.)))
    candidate = SimpleNamespace(
        MEMBER_AXES={'base_floor_right': (cq.Vector(0., 1., 0.), cq.Vector(1., 0., 0.))},
        uncut_wood_parts=lambda: (post, rail),
        bolt_dimensions=lambda c: {'hole_diameter_mm': 11.1125})
    bolt = SimpleNamespace(kind='bolt', name='joint', members=(post.name, rail.name),
                           start=cq.Vector(1140.968, -134., 70.))
    monkeypatch.setattr(packet, 'model', candidate)
    rows = packet.bolt_member_datums([bolt])
    assert len(rows) == 2
    for row in rows:
        origin = cq.Vector(*(row[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., row['along_y'], row['along_z'])
        cross = cq.Vector(0., row['cross_y'], row['cross_z'])
        reconstructed = origin+along*row['along_from_corner_mm']+cross*row['signed_cross_from_corner_mm']
        assert (reconstructed.y, reconstructed.z) == pytest.approx((-134., 70.))
        source = post if row['member'] == post.name else rail
        assert any((v.Center()-origin).Length < 1.e-7 for v in source.shape.Vertices())
    assert (rows[0]['along_y'], rows[0]['along_z']) == (0., 1.)
    assert (rows[1]['along_y'], rows[1]['along_z']) == (1., 0.)


def test_mirrored_notches_preserve_outer_screw_clearance():
    candidate = SimpleNamespace(b=SimpleNamespace(HALF=1219.2), panel_edge_cutouts=lambda: {
        'kicker_left': [(-1219.2, -1179.1, 0., 141.7)],
        'kicker_right': [(1179.1, 1219.2, 0., 141.7)]})
    rows = packet.kicker_notch_records(candidate)
    assert [row['from_left_mm'] for row in rows] == pytest.approx([0., 1179.1])
    for row in rows:
        assert row['width_mm'] == pytest.approx(40.1)
        assert row['height_mm'] == pytest.approx(141.7)
    # The shifted outer screw is beyond the relieved panel edge in both halves.
    assert 1179.1-1162.05 == pytest.approx(17.05)
