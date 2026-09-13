"""Fast physical-sole-cut checks using a small representative timber block."""
import cadquery as cq
import pytest

from mini_moonboard import leg_mvp_sole_frame as model


def test_finite_sole_is_a_real_cut_with_four_floor_corners():
    width, full_length, height = 38.1, 200., 20.
    original = cq.Solid.makeBox(width, full_length, height,
        cq.Vector(0., model.FOOT_CENTER_Y_MM-full_length/2, 0.))
    revised = model.relieve_sole(original)
    points = [v.Center() for v in revised.Vertices() if abs(v.Z) < 1e-6]
    assert len(points) == 4
    assert max(p.y for p in points)-min(p.y for p in points) == pytest.approx(75.)
    assert min(p.y for p in points)+max(p.y for p in points) == pytest.approx(2*model.FOOT_CENTER_Y_MM)
    assert original.Volume()-revised.Volume() == pytest.approx(width*(full_length-75.)*5.)
    assert revised.isValid()
    assert original.Volume() == pytest.approx(width*full_length*height)
    assert revised.BoundingBox().zmax == height


def test_candidate_preserves_full_sole_variant_and_connection_pattern():
    assert model.KEY == 'leg-mvp-sole-development'
    assert model.previous.KEY == 'leg-mvp-development'
    assert model.connections is model.previous.connections
    assert model.bolt_interface_point is model.previous.bolt_interface_point
    assert model.FOOT_RELIEF_MM-model.FOOT_RELIEF_TOLERANCE_MM == 4.
    assert model.DEPTH == 234.95


def test_sole_review_cannot_silently_evaluate_full_sole_candidate():
    with pytest.raises(NotImplementedError, match='original_foot_bounds'):
        model.geometry_review()


def test_sole_cut_rejects_elevated_stock():
    elevated = cq.Solid.makeBox(38.1, 200., 20.,
        cq.Vector(0., model.FOOT_CENTER_Y_MM-100., 10.))
    with pytest.raises(ValueError, match='floor-bearing stock'):
        model.relieve_sole(elevated)
