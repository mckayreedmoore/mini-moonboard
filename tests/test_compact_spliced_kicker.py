import cadquery as cq
import pytest

from mini_moonboard import compact_spliced_kicker as model


def test_only_four_bottom_screw_axes_move_and_datums_follow():
    old = {c.name: c for c in model.previous.connections()}
    new = {c.name: c for c in model.connections()}
    assert old.keys() == new.keys()
    moved = {name for name, c in new.items() if (c.start-old[name].start).Length > 1.e-8}
    assert moved == model.MOVED_NAMES
    assert len(model.panel_connections()) == 66
    for name in moved:
        assert old[name].start.z == pytest.approx(112.)
        assert new[name].start.z == pytest.approx(60.)
        assert new[name].start.x == pytest.approx(old[name].start.x)
        assert new[name].start.y == pytest.approx(old[name].start.y)
        assert new[name].members == old[name].members
        assert (new[name].direction-old[name].direction).Length == pytest.approx(0.)
    rows = {row['name']: row for row in model.attachment_datums()}
    for c in model.panel_connections():
        if c.members[0].startswith('kicker_'):
            assert rows[c.name]['s'] == pytest.approx(c.start.z)
            assert rows[c.name]['x'] == pytest.approx(c.start.x)
    for name in old.keys()-moved:
        assert new[name] is old[name]


def test_lower_row_retains_receiver_end_and_spacing_margins():
    raw = {p.name: p for p in model.previous.uncut_wood_parts() if p.name in model.CHANGED_NAMES}
    for c in model.panel_connections():
        if c.name not in model.MOVED_NAMES:
            continue
        box = raw[c.members[1]].shape.BoundingBox()
        assert c.start.z-box.zmin == pytest.approx(60.)
        assert c.start.z-box.zmin > 44.45
        upper = next(other for other in model.panel_connections()
                     if other.members == c.members and other.name != c.name)
        assert upper.start.z-c.start.z == pytest.approx(132.)
        assert min(c.start.x-box.xmin, box.xmax-c.start.x) >= 9.525


def test_fresh_parts_restore_old_holes_and_cut_new_screw_envelopes():
    changed = {p.name: p for p in model.revised_parts()}
    assert changed.keys() == model.CHANGED_NAMES
    old = {c.name: c for c in model.previous.connections()}
    for c in model.connections():
        if c.name not in model.MOVED_NAMES:
            continue
        for name, depth in ((c.members[0], 2.), (c.members[1], 25.)):
            # Interior spheres avoid surface-tolerance ambiguity at both axes.
            probe = cq.Solid.makeSphere(.5, old[c.name].start+old[c.name].direction*depth)
            assert changed[name].shape.intersect(probe).Volume() == pytest.approx(probe.Volume(), rel=1.e-5)
            probe = cq.Solid.makeSphere(.5, c.start+c.direction*depth)
            assert changed[name].shape.intersect(probe).Volume() == pytest.approx(0., abs=1.e-8)
        shaft, head = c.components()
        panel = changed[c.members[0]].shape
        assert panel.intersect(shaft).Volume() == pytest.approx(0., abs=1.e-6)
        assert panel.intersect(head).Volume() == pytest.approx(0., abs=1.e-6)
