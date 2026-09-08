import cadquery as cq
import pytest

from mini_moonboard import backing_end_trial as trial
from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame
from mini_moonboard.connection_geometry import material_intervals


def test_eight_proposed_factory_axes_have_full_nominal_receiver_penetration():
    raw = {p.name: p for p in frame.wood_parts(True)}
    screws = list(trial.screws())
    assert len({c.name for c in screws}) == 8
    for c in screws:
        receiver = raw[c.members[1]].shape
        intervals = material_intervals(receiver, c.start, c.direction, 0., c.length)
        assert len(intervals) == 1
        assert intervals[0] == pytest.approx((trial.REFERENCE["thickness_mm"], 38.1), abs=1e-6)
        # Actual shaft, not only its axis, must remain in the designated wood.
        start = c.start+c.direction*trial.REFERENCE["thickness_mm"]
        shaft = cq.Solid.makeCylinder(3.175, 38.1-trial.REFERENCE["thickness_mm"], start, c.direction)
        assert shaft.cut(receiver).Volume() < .01, c.name
    assert len(frame.connections()) == 188  # Trial is not silently installed.


def test_backing_edge_layout_is_from_ml23_not_scaled_ml24():
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    values = []
    for c in trial.screws():
        if c.members[1] == "timber_bottom_backing":
            s = (c.start-b.point(0, 0, 0)).dot(tangent)
            values.append(min(s, 88.9-s))
    assert values == pytest.approx([22.225]*4)
    assert trial.REFERENCE["width_mm"] == 76.2
