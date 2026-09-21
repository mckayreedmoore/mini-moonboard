"""Finite protected-service envelopes for both owner-review concepts."""

import cadquery as cq

from scripts import owner_layout_protected as protected


def test_shared_protected_inventory_is_complete_and_provisional():
    model = protected.inventory()
    assert model["counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert model["hold_rear_projection_mm"] == 50.8
    assert model["delivered_hold_bolt_lengths_verified"] is False
    assert model["receiving_clearance_verified"] is False


def test_real_service_solids_are_not_zero_length_points():
    model = protected.inventory()
    for family in model["solids"].values():
        assert family
        assert all(shape.Volume() > 0 for shape in family.values())
    tnut_name, tnut = next(iter(model["solids"]["tnuts"].items()))
    hits = protected.hits({"known_collision": tnut}, model)
    assert hits["known_collision"]["tnuts"][tnut_name] > 0


def test_cached_bounds_preserve_intersection_results():
    fixed = cq.Solid.makeBox(10, 10, 10)
    crossing = cq.Solid.makeBox(10, 10, 10, cq.Vector(5, 0, 0))
    separate = cq.Solid.makeBox(10, 10, 10, cq.Vector(20, 0, 0))
    inventory = {"solids": {"test": {"fixed": fixed}}}
    cached = {
        **inventory,
        "bounds": {"test": {"fixed": fixed.BoundingBox()}},
    }
    candidates = {"crossing": crossing, "separate": separate}
    expected = {
        "crossing": {"test": {"fixed": 500.0}},
        "separate": {},
    }
    assert protected.hits(candidates, inventory) == expected
    assert protected.hits(candidates, cached) == expected
