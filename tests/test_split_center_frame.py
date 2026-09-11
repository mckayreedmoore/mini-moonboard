"""Separate center receivers, service access and full-depth base support."""
import pytest

from mini_moonboard import split_center_frame as model
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope='module')
def candidate():
    return {p.name: p for p in model.wood_parts()}, model.connections()


def test_center_principals_are_separate_unpocketed_2x6_stock(candidate):
    raw, _ = candidate
    assert 'base_principal_center' not in raw and 'base_post_center' not in raw
    old = {p.name: p for p in model.previous.wood_parts()}
    for side in ('left', 'right'):
        assert raw[f'timber_base_gusset_{side}'].shape is old[f'timber_base_gusset_{side}'].shape
    service = model.timber.service_envelopes()
    for name, x in model.CENTER_SPLIT.items():
        p = raw[f'base_principal_{name}']
        expected, _ = model.base._sloped_bearing_member(x-19.05, x+19.05, 139.7, model.b.LENGTH-38.1)
        assert p.blank[1:] == (139.7, 38.1) and p.laminations == 1
        assert p.shape.Volume() == pytest.approx(expected.Volume())
        assert min(p.shape.distance(tool) for tool in service) >= 11.75-1e-5
    left = raw['base_principal_center_left'].shape.BoundingBox()
    right = raw['base_principal_center_right'].shape.BoundingBox()
    assert right.xmin-left.xmax == pytest.approx(model.CENTER_CLEAR_GAP)
    assert model.CENTER_PANEL_OVERHANG == pytest.approx(50.95)


def test_center_clips_and_panel_screws_have_full_receivers(candidate):
    raw, connections = candidate
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    assert len(screws) == 80
    center = [c for c in screws if c.members[1].startswith(('base_principal_center_', 'base_post_center_'))]
    assert len(center) == 20
    for c in center:
        side = 'left' if c.members[0].endswith('left') else 'right'
        assert c.members[1].endswith(side)
        assert c.start.x == model.CENTER_SPLIT['center_'+side]
        length = sum(z-a for a, z in material_intervals(raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert length == pytest.approx(c.length-model.wide.PANEL)
    clips = [c for c in connections if c.name.startswith('clip_split_')]
    assert len(clips) == 48
    for c in clips:
        length = sum(z-a for a, z in material_intervals(raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert length == pytest.approx(model.hardware.SDS['gross_penetration_through_nominal_ml24z']), c.name
    assert all(name in raw or name.startswith('clip_') for c in connections for name in c.members)


def test_every_post_supports_full_header_depth_and_outer_bolts_keep_grips(candidate):
    raw, connections = candidate
    posts = [p for name, p in raw.items() if name.startswith('base_post_')]
    assert len(posts) == 8
    for p in posts:
        bounds = p.shape.BoundingBox()
        assert bounds.ymin == pytest.approx(model.base.HEADER_FRONT_Y-model.HEADER_DEPTH)
        assert bounds.ymax == pytest.approx(model.base.HEADER_FRONT_Y)
        assert p.blank == (model.base.HEADER_BOTTOM, 234.95, 38.1)
    old = {c.name: c for c in model.previous.connections()}
    for c in connections:
        if not c.name.startswith(('timber_base_left_', 'timber_base_right_')):
            continue
        before = old[c.name]
        assert c.start.toTuple() == before.start.toTuple()
        assert c.direction.toTuple() == before.direction.toTuple()
        assert c.length == before.length and c.grip == before.grip
