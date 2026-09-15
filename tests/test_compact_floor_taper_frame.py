"""Taper coordinates preserve runner clearance and actual variable leg width."""
import cadquery as cq
import pytest

from mini_moonboard import compact_floor_taper_frame as model


def test_grain_runout_starts_after_full_runner_clearance():
    grain = cq.Vector(0., -.23915183196324324, .9709821838059775)
    normal = cq.Vector(0., grain.z, -grain.y)
    profile = [(1047.708429168, 1820.402525498), (1158.935231128, 1952.957466327),
               (1496.071546581, 0.), (1639.946483042, 0.)]
    start, end = model.taper_stations(profile, grain)
    qs = [cq.Vector(0., y, z).dot(normal) for y, z in profile]
    for q in (min(qs), max(qs)):
        runner_top_station = (141.7-normal.z*q)/grain.z
        assert runner_top_station <= start+1.e-7
    assert end-start == pytest.approx(457.2)
    assert (end-start)/38.1 == pytest.approx(12.)


@pytest.mark.parametrize('side', ['left', 'right'])
def test_cut_has_exact_taper_volume_and_returns_to_full_stock(monkeypatch, side):
    sign = -1 if side == 'left' else 1
    inner = sign*1219.2
    data = {'inner_face_x_mm':inner, 'outward_sign':sign,
            'taper_start_station_mm':141.7, 'taper_end_station_mm':598.9,
            'taper_run_mm':457.2, 'max_recess_depth_mm':38.1,
            'grain_bounds_mm':(0., 900.), 'normal_axis_xyz':(0., 1., 0.),
            'cross_grain_bounds_mm':(0., 139.7)}
    monkeypatch.setattr(model, 'taper_profile_data', lambda: {'lumber_leg_'+side:data})
    cutter = model.recess_cutter.__wrapped__(side)
    x0 = -1308.1 if side == 'left' else 1219.2
    stock = cq.Solid.makeBox(88.9, 139.7, 900., cq.Vector(x0, 0., 0.))
    removed = stock.intersect(cutter)
    assert removed.Volume() == pytest.approx(38.1*139.7*(141.7+457.2/2))
    for station, expected_depth in ((100., 38.1), (370.3, 19.05), (700., 0.)):
        assert model.cut_depth_at_station(station, data) == pytest.approx(expected_depth)
        # Probe either side of the actual sloping boundary, away from surfaces.
        if expected_depth:
            assert cutter.isInside(cq.Vector(inner+sign*(expected_depth-.1), 60., station))
        assert not cutter.isInside(cq.Vector(inner+sign*(expected_depth+.1), 60., station))
    assert len(stock.cut(cutter).Solids()) == 1


def test_taper_preserves_hardware_and_unnotched_kicker_definition():
    assert model.connections is model.previous.connections
    assert model.panel_connections is model.previous.panel_connections
    assert model.panel_edge_cutouts() == {}
    assert model.TAPER_NATIVE_GEOMETRY_REQUIRED is True
    assert model.RECESS_NATIVE_GEOMETRY_REQUIRED is False
    assert model.LEG_RECESS_DEPTH_MM == 38.1
    assert model.RAIL_DEPTH_MM == 139.7
