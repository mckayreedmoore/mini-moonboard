"""Finite shaft ownership must distinguish disconnected collinear stock."""

import cadquery as cq
import pytest

from scripts.eoere_bolted_model import connected_receivers, interval_components


def test_disconnected_collinear_receivers_are_separate_physical_stacks():
    rows = [{"member": "left", "interval_mm": [-90, -50]},
            {"member": "right", "interval_mm": [50, 90]},
            {"member": "left_other_flange", "interval_mm": [-90, -50]}]
    groups = interval_components(rows)
    assert [len(group) for group in groups] == [2, 1]


def test_touching_receivers_and_overlapping_opposite_ports_merge():
    rows = [{"member": "a", "interval_mm": [0, 38.1]},
            {"member": "b", "interval_mm": [38.1, 76.2]},
            {"member": "c", "interval_mm": [0, 38.1]}]
    assert len(interval_components(rows)) == 1


def test_connected_wood_ray_extends_through_cleat_but_stops_before_other_frame_side():
    wood = {"side": cq.Solid.makeBox(88.9, 139.7, 100, cq.Vector(0, 0, 0)),
            "cleat": cq.Solid.makeBox(38.1, 139.7, 100, cq.Vector(88.9, 0, 0)),
            "far_side": cq.Solid.makeBox(38.1, 139.7, 100, cq.Vector(1000, 0, 0))}
    names, near, far = connected_receivers(wood, cq.Vector(0, 60, 50), cq.Vector(1, 0, 0), "side")
    assert set(names) == {"side", "cleat"}
    assert near == pytest.approx(0) and far == pytest.approx(127)


def test_invalid_finite_interval_is_rejected():
    with pytest.raises(ValueError):
        interval_components([{"interval_mm": [10, 10]}])
    with pytest.raises(ValueError):
        interval_components([], tolerance=-1)
