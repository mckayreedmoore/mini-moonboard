"""Independent vertical receivers, split bottom rails and explicit attachments."""
from math import hypot

import pytest

from fea.screw_insert_repair_reserve import overlaps
from mini_moonboard import vertical_principal_frame as model
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope='module')
def candidate():
    return {p.name: p for p in model.wood_parts()}, model.connections()


def test_vertical_receivers_replace_midrails_and_preserve_gussets(candidate):
    raw, _ = candidate
    assert not any(name.startswith('base_rail_mid_') for name in raw)
    assert len([name for name in raw if name.startswith('base_rail_bottom_')]) == 6
    old = {p.name: p for p in model.previous.wood_parts()}
    for side in ('left', 'right'):
        name = f'timber_base_gusset_{side}'
        assert raw[name].shape is old[name].shape
    for name in model.ADDED_CENTERS:
        principal = raw[f'base_principal_{name}']
        assert principal.blank[1:] == (139.7, 38.1)
        assert principal.laminations == 1
        assert raw[f'base_post_{name}'].blank == (model.base.HEADER_BOTTOM, 234.95, 38.1)
        for reservation in model.timber.service_envelopes():
            assert principal.shape.intersect(reservation).Volume() < 1e-5
    for name, _, _, _, _ in model.bottom_bays():
        assert raw[name].shape.isValid() and len(raw[name].shape.Solids()) == 1


def test_new_clips_have_full_receivers_and_direct_top_base_post_attachments(candidate):
    raw, connections = candidate
    selected = [c for c in connections if c.name.startswith('clip_vertical_')]
    assert len(selected) == 144  # Twelve bottom clips plus four top/base/post triplets.
    for c in selected:
        material = sum(end-start for start, end in material_intervals(
            raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert material == pytest.approx(model.hardware.SDS['gross_penetration_through_nominal_ml24z']), c.name
    for name in model.ADDED_CENTERS:
        principal, post = f'base_principal_{name}', f'base_post_{name}'
        pairs = {(beam, upright) for _, _, _, _, beam, upright in model.stations()}
        assert ('base_rail_top', principal) in pairs
        assert ('base_header', principal) in pairs
        assert ('base_header', post) in pairs


def test_added_panel_screws_engage_each_new_receiver_and_clear_service(candidate):
    raw, connections = candidate
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    assert len(screws) == 80
    added = [c for c in screws if c.name.startswith('vertical_panel_')]
    assert len(added) == 32
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized()
    service = [(x-model.b.HALF, s) for x, s in
               (*model.timber.grid.main_tnut_datums().values(), *model.timber.grid.main_led_datums().values())]
    for name in model.ADDED_CENTERS:
        assert sum(c.members[1] == f'base_principal_{name}' for c in added) == 8
    for c in added:
        s = (c.start-model.b.point(0., 0., 0.)).dot(tangent)
        assert min(hypot(c.start.x-x, s-station) for x, station in service) >= 28.
        assert model.b.LENGTH-38.1-s >= 44.45
        material = sum(end-start for start, end in material_intervals(
            raw[c.members[1]].shape, c.start, c.direction, 0., c.length))
        assert material == pytest.approx(c.length-model.wide.PANEL)
    for c in screws:
        assert all(name in raw for name in c.members)


def test_base_retention_clears_bottom_clips_and_other_fasteners(candidate):
    _, connections = candidate
    clips = {p.name: p.shape for p in model.hardware.clip_parts(model.stations())}
    components = {c.name: c.components() for c in connections}
    for name, origin, u, _, _, _ in model.stations():
        if not name.startswith('clip_vertical_base_'):
            continue
        suffix = name.removeprefix('clip_vertical_base_')
        assert origin.x == pytest.approx(model.ADDED_CENTERS[suffix]-19.05)
        assert u.x == -1.
        for other, shape in clips.items():
            if other != name:
                assert not overlaps(clips[name], shape), (name, other)
    for c in connections:
        if not c.name.startswith('clip_vertical_base_'):
            continue
        for other in connections:
            if c.name != other.name:
                assert not any(overlaps(first, second) for first in components[c.name]
                               for second in components[other.name]), (c.name, other.name)
        for name, shape in clips.items():
            if name != c.members[0]:
                assert not any(overlaps(part, shape) for part in components[c.name]), (c.name, name)
