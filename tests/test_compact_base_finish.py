import cadquery as cq
import pytest

from mini_moonboard import compact_base_finish as model
from mini_moonboard.connection_geometry import material_intervals


def test_base_clip_relocation_preserves_other_connections_and_lumber():
    old = {c.name: c for c in model.previous.connections()}
    new = {c.name: c for c in model.connections()}
    assert old.keys() == new.keys()
    moved = [c for c in new.values() if c.members[0] in model.MOVED_CLIPS]
    assert len(moved) == 12
    for c in moved:
        assert (c.start-old[c.name].start).toTuple() == pytest.approx((0., 29.15, 0.))
        assert c.members == old[c.name].members
        assert c.direction.toTuple() == old[c.name].direction.toTuple()
    for c in new.values():
        if c not in moved:
            assert c is old[c.name]
    assert model.uncut_wood_parts is model.previous.uncut_wood_parts


def test_angle_footprints_and_complete_screw_envelopes_fit_receivers():
    raw = {p.name: p for p in model.uncut_wood_parts()}
    header = raw['base_header'].shape.BoundingBox()
    for part in model.outer_base_angles():
        bounds = part.shape.BoundingBox()
        assert bounds.ymin-header.ymin == pytest.approx(19.05)
        assert header.ymax-bounds.ymax == pytest.approx(19.05)
    thickness = model.hardware.ML['thickness']
    for c in model.connections():
        if c.members[0] not in model.MOVED_CLIPS:
            continue
        receiver = raw[c.members[1]].shape
        intervals = material_intervals(receiver, c.start, c.direction, 0., c.length)
        assert len(intervals) == 1
        assert intervals[0] == pytest.approx((thickness, c.length))
        shaft = cq.Solid.makeCylinder(c.diameter/2, c.length-thickness,
                                     c.start+c.direction*thickness, c.direction)
        assert shaft.Volume()-receiver.intersect(shaft).Volume() == pytest.approx(0., abs=1.e-7)


def test_fresh_receiver_rebuild_restores_old_clip_holes():
    changed = {p.name: p for p in model.revised_parts()}
    old = {c.name: c for c in model.previous.connections()}
    for c in model.connections():
        if c.members[0] not in model.MOVED_CLIPS:
            continue
        receiver = changed[c.members[1]].shape
        for connection, occupied in ((old[c.name], True), (c, False)):
            probe = cq.Solid.makeSphere(.5, connection.start+connection.direction*20.)
            expected = probe.Volume() if occupied else 0.
            assert receiver.intersect(probe).Volume() == pytest.approx(expected, abs=1.e-7)
