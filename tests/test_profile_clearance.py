"""Synthetic exact profile distances, independent of any frame capacity claim."""
import cadquery as cq
import pytest

from mini_moonboard.profile_clearance import bore_ligament


def rectangle():
    return cq.Face.makeFromWires(cq.Wire.makePolygon([
        (0, 0, 0), (20, 0, 0), (20, 10, 0), (0, 10, 0)], close=True))


def test_rectangle_retains_positive_zero_and_negative_ligament():
    face = rectangle()
    assert bore_ligament(face, (3, 4, 0), 1) == pytest.approx(2.)
    assert bore_ligament(face, (3, 4, 0), 3) == pytest.approx(0.)
    assert bore_ligament(face, (3, 4, 0), 4) == pytest.approx(-1.)
    assert bore_ligament(face, (3, 4, 0), 0) == pytest.approx(3.)


def test_exact_curved_outer_boundary_not_vertices():
    face = cq.Face.makeFromWires(cq.Wire.makeCircle(10, (0, 0, 0), (0, 0, 1)))
    assert bore_ligament(face, (0, 6, 0), 1) == pytest.approx(3., abs=1e-7)


def test_inner_wire_and_concave_profile_are_boundaries():
    outer = cq.Wire.makeCircle(10, (0, 0, 0), (0, 0, 1))
    inner = cq.Wire.makeCircle(2, (0, 0, 0), (0, 0, 1))
    annulus = cq.Face.makeFromWires(outer, [inner])
    assert bore_ligament(annulus, (0, 3, 0), .5) == pytest.approx(.5)
    with pytest.raises(ValueError, match="inside profile"):
        bore_ligament(annulus, (0, 1, 0), .5)
    concave = cq.Face.makeFromWires(cq.Wire.makePolygon([
        (0, 0, 0), (10, 0, 0), (10, 4, 0), (4, 4, 0),
        (4, 10, 0), (0, 10, 0)], close=True))
    assert bore_ligament(concave, (3, 6, 0), .5) == pytest.approx(.5)
    with pytest.raises(ValueError, match="inside profile"):
        bore_ligament(concave, (6, 6, 0), .5)


def test_rigid_transform_keeps_ligament():
    face = rectangle().rotate((0, 0, 0), (1, 0, 0), 90).translate((7, 8, 9))
    assert bore_ligament(face, (10, 8, 13), 1) == pytest.approx(2.)


@pytest.mark.parametrize("point", [(-1, 5, 0), (0, 5, 0), (5, 5, .01)])
def test_exterior_boundary_and_offplane_centers_rejected(point):
    with pytest.raises(ValueError):
        bore_ligament(rectangle(), point, 1)


@pytest.mark.parametrize("point,radius,tolerance", [
    ((float("nan"), 5, 0), 1, 1e-7),
    ((5, 5, 0), float("inf"), 1e-7),
    ((5, 5, 0), -1, 1e-7),
    ((5, 5, 0), 1, 0),
])
def test_invalid_numeric_inputs_rejected(point, radius, tolerance):
    with pytest.raises(ValueError):
        bore_ligament(rectangle(), point, radius, tolerance=tolerance)


def test_nonplanar_face_rejected():
    cylinder = cq.Solid.makeCylinder(5, 10)
    face = next(f for f in cylinder.Faces() if f.geomType() == "CYLINDER")
    with pytest.raises(ValueError, match="planar face"):
        bore_ligament(face, (5, 0, 5), 1)


def test_boundary_distance_error_is_not_a_pass(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic distance failure")
    monkeypatch.setattr(cq.Vertex, "distance", fail)
    with pytest.raises(RuntimeError, match="geometry evaluation failed"):
        bore_ligament(rectangle(), (5, 5, 0), 1)
