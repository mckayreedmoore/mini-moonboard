"""Synthetic axial material geometry; no frame or capacity integration."""
import cadquery as cq
import pytest

from mini_moonboard.connection_geometry import material_intervals


def test_signed_intervals_normalize_direction_and_clip_segment():
    box = cq.Solid.makeBox(10, 10, 10)
    assert material_intervals(box, (5, 5, 5), (4, 0, 0), -20, 20) == pytest.approx([(-5., 5.)])
    assert material_intervals(box, (5, 5, 5), (-2, 0, 0), -3, 2) == pytest.approx([(-3., 2.)])


def test_service_relief_preserves_disjoint_material_intervals():
    box = cq.Solid.makeBox(10, 10, 10)
    relief = cq.Solid.makeCylinder(1, 12, cq.Vector(5, 5, -1), cq.Vector(0, 0, 1))
    receiver = box.cut(relief)
    assert material_intervals(receiver, (0, 5, 5), (1, 0, 0), -1, 11) == pytest.approx([(0., 4.), (6., 10.)])


def test_rotated_translated_receiver_retains_axial_distances():
    box = cq.Solid.makeBox(10, 10, 10).rotate((0, 0, 0), (0, 0, 1), 90).translate((20, 30, 40))
    assert material_intervals(box, (15, 30, 45), (0, 7, 0), -2, 12) == pytest.approx([(0., 10.)])


@pytest.mark.parametrize("start", [(0, 15, 5), (0, 0, 5), (0, 0, 0)])
def test_outside_and_boundary_tangency_receive_no_material_credit(start):
    assert material_intervals(cq.Solid.makeBox(10, 10, 10), start, (1, 0, 0), -1, 11) == []


def test_compound_keeps_gap_but_merges_touching_material():
    first = cq.Solid.makeBox(10, 10, 10)
    second = cq.Solid.makeBox(10, 10, 10, cq.Vector(12, 0, 0))
    assert material_intervals(cq.Compound.makeCompound([first, second]), (0, 5, 5),
                              (1, 0, 0), -1, 23) == pytest.approx([(0., 10.), (12., 22.)])
    second = second.translate((-2, 0, 0))
    assert material_intervals(cq.Compound.makeCompound([first, second]), (0, 5, 5),
                              (1, 0, 0), -1, 23) == pytest.approx([(0., 20.)])


@pytest.mark.parametrize("start,direction,lower,upper,tolerance", [
    ((float("nan"), 0, 0), (1, 0, 0), 0, 10, 1e-7),
    ((0, 0, 0), (float("inf"), 0, 0), 0, 10, 1e-7),
    ((0, 0, 0), (0, 0, 0), 0, 10, 1e-7),
    ((0, 0, 0), (1, 0, 0), 10, 0, 1e-7),
    ((0, 0, 0), (1, 0, 0), 0, float("inf"), 1e-7),
    ((0, 0, 0), (1, 0, 0), 0, 10, 0),
])
def test_invalid_axes_and_limits_raise(start, direction, lower, upper, tolerance):
    with pytest.raises(ValueError):
        material_intervals(cq.Solid.makeBox(10, 10, 10), start, direction, lower, upper, tolerance=tolerance)


def test_non_solid_receiver_rejected():
    with pytest.raises(TypeError):
        material_intervals(None, (0, 0, 0), (1, 0, 0), -1, 2)
    with pytest.raises(ValueError):
        material_intervals(cq.Edge.makeLine((0, 0, 0), (1, 0, 0)), (0, 0, 0), (1, 0, 0), -1, 2)


def test_kernel_failure_is_not_an_empty_success(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic kernel failure")
    monkeypatch.setattr(cq.Edge, "intersect", fail)
    with pytest.raises(RuntimeError, match="geometry evaluation failed"):
        material_intervals(cq.Solid.makeBox(10, 10, 10), (0, 5, 5), (1, 0, 0), -1, 11)
