"""Fast axis/hardware tests for the provisional solid-stock pivot trial."""
import pytest

from mini_moonboard import thick_leg_frame as model


def test_pivot_depth_shift_and_actual_member_interface():
    centre, _, leg, _, rim = model.axes()
    offset = model.bolt_points()[0]-centre
    for grain in (leg, rim):
        normal = model.cq.Vector(0., grain.z, -grain.y)
        assert offset.dot(normal) == pytest.approx(0., abs=1e-8)
        assert model.DEPTH/2-abs(offset.dot(normal))-4*15.875-3. >= 3.3
    bolts = [c for c in model.connections() if isinstance(c, model.ProvisionalPivotBolt)]
    assert len(bolts) == 2
    for bolt in bolts:
        assert abs(model.bolt_interface_point(bolt).x) == pytest.approx(model.b.HALF+50.8)
        assert bolt.grip == pytest.approx(177.8)
        assert len(bolt.components()) == 5


def test_other_connections_preserved_and_hardware_not_qualified():
    old = {c.name:c for c in model.previous.connections() if not c.name.startswith('lumber_leg_bolt_')}
    new = {c.name:c for c in model.connections() if not isinstance(c, model.ProvisionalPivotBolt)}
    assert old == new
    assert model.provisional_stack()['smooth_shank_across_wood_demonstrated'] is False
    assert model.provisional_stack()['nominal_tip_projection_mm'] > 0
    assert model.b.V1_KICKER_HEIGHT_MM == 277
