import cadquery as cq
import pytest

from mini_moonboard import compact_knee_two_frame as model


def test_two_upper_bolts_have_symmetric_loaded_edge_reserve():
    points = model.bolt_points()
    assert (points[1]-points[0]).Length == pytest.approx(64.)
    _,foot,leg,_,rim = model.axes()
    for point in points:
        for grain,datum in ((leg,foot),(rim,model.b.point(0.,0.,69.85))):
            normal = cq.Vector(0.,grain.z,-grain.y)
            assert 69.85-abs((point-datum).dot(normal))-4*12.7 >= 3.
    bolts = [c for c in model.connections() if c.name.startswith('lumber_leg_bolt_')]
    assert len(bolts) == 4
    assert len([c for c in model.connections() if c.name.startswith('knee_bolt_')]) == 8
    assert model.KEY != model.previous.KEY
