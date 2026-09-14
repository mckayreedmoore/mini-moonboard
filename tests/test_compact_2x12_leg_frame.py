import pytest

from mini_moonboard import compact_2x12_leg_frame as model


def test_unbraced_trial_has_separate_geometry_and_outward_eight_bolt_inventory():
    assert model.KEY != model.previous.KEY
    assert model.KNEE_NAMES == () and not model.NATIVE_RECTANGULAR_KNEES
    connections = model.connections()
    bolts = [c for c in connections if c.kind == 'bolt']
    assert len(bolts) == 8
    assert not any('knee' in name for c in connections for name in c.members)
    assert all(c.start.x*c.direction.x > 0 and c.grip == 127. for c in bolts)
    centre,foot,grain,_,rim = model.axes()
    assert foot.z == pytest.approx(0.)
    assert (centre-foot).cross(grain).Length < 1e-8
    assert (model.bolt_points()[-1]-model.bolt_points()[0]).Length == pytest.approx(195.)
    assert all((p-centre).cross(rim).Length < 1e-8 for p in model.bolt_points())
