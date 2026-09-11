"""Horizontal rail replacement preserves supported hardware and split center stock."""
import pytest

from mini_moonboard import horizontal_service_frame as model
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope='module')
def candidate():
    return {p.name: p for p in model.wood_parts()}, model.connections()


def test_four_intermediate_principals_and_posts_are_replaced_by_horizontal_rails(candidate):
    raw, _ = candidate
    assert not set(raw)&model.REMOVED_NAMES
    assert len([name for name in raw if name.startswith('base_principal_')]) == 2
    assert len([name for name in raw if name.startswith('base_post_')]) == 4
    assert len([name for name in raw if name.startswith('base_rail_service_')]) == 4
    assert len([name for name in raw if name.startswith('base_rail_bottom_')]) == 2
    old = {p.name: p for p in model.previous.wood_parts()}
    uncut = {p.name: p for p in model.uncut_wood_parts()}
    for name in model.CENTER_SPLIT:
        assert uncut[f'base_principal_{name}'].shape is old[f'base_principal_{name}'].shape
    for name, p in raw.items():
        if name.startswith(('base_rail_service_', 'base_rail_bottom_')):
            assert p.blank[1:] == (139.7, 38.1) and p.laminations == 1
            assert p.shape.isValid() and len(p.shape.Solids()) == 1


def test_every_remaining_or_new_connection_has_a_receiver(candidate):
    raw, connections = candidate
    assert sum(c.kind == 'bolt' for c in connections) == 8
    assert all(not set(c.members)&model.REMOVED_NAMES for c in connections)
    for c in connections:
        assert all(name in raw or name.startswith('clip_') for name in c.members)
    clips = [c for c in connections if c.name.startswith('clip_horizontal_')]
    assert len(clips) == 72
    for c in clips:
        material = sum(end-start for start, end in material_intervals(
            raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert material == pytest.approx(model.hardware.SDS['gross_penetration_through_nominal_ml24z']), c.name
    prior = {c.name: c for c in model.previous.connections()}
    for c in connections:
        if c.kind == 'bolt':
            assert c is prior[c.name]


def test_service_rail_screws_belong_to_the_correct_panel_and_clear_ends(candidate):
    raw, connections = candidate
    added = [c for c in connections if c.name.startswith('horizontal_panel_')]
    assert len(added) == 16
    for c in added:
        panel, receiver = c.members
        level = 'lower' if '_lower_' in receiver else 'upper'
        side = 'left' if receiver.endswith('left') else 'right'
        assert panel == f'main_{level}_{side}'
        _, x0, x1 = next(row for row in model.BAYS if row[0] == side)
        assert min(c.start.x-x0, x1-c.start.x) >= 44.45
        material = sum(end-start for start, end in material_intervals(
            raw[receiver].shape, c.start, c.direction, 0., c.length))
        assert material == pytest.approx(c.length-model.wide.PANEL)
