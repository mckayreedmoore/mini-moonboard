import copy
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import hl35_candidate as shared
from scripts import thin_bolted_occupied as occupied


def axis(grip=38.1, before=5.55625, after=0.):
    return {
        "id": "fixture", "point": cq.Vector(0, 0, 0),
        "direction": cq.Vector(0, 0, 1), "grip_mm": grip,
        "diameter_mm": 12.7, "bore_diameter_mm": 14.2875,
        "before_plate_mm": before, "after_plate_mm": after,
        "receivers": ["wood"], "attachments": [],
        "hardware_scenario": copy.deepcopy(occupied.DEFAULT_SETTINGS["new_half_inch_hardware"]),
    }


def test_complete_stack_stays_outside_flat_wood_faces():
    record = axis()
    pieces = dict(occupied.local_hardware(record))
    wood = cq.Solid.makeBox(100, 100, 38.1, cq.Vector(-50, -50, 0))
    wood = occupied.bore_wood({"wood": wood}, [record])["wood"]
    assert set(pieces) == {"shaft", "head", "head_washer", "nut_washer", "nut"}
    assert all(shared.overlaps(shape, wood) < .001 for shape in pieces.values())
    assert record["nominal_under_head_length_mm"] == pytest.approx(76.2)
    assert record["tip_projection_beyond_nut_mm"] > 2 * 25.4 / 13
    assert record["nominal_thread_window_qualified"] is False


def test_two_plate_stack_and_long_grip_use_available_length_without_growing_wood():
    paired = axis(after=5.55625)
    occupied.local_hardware(paired)
    assert paired["grip_mm"] == pytest.approx(38.1)
    assert paired["nominal_under_head_length_mm"] == pytest.approx(76.2)
    assert paired["tip_projection_beyond_nut_mm"] > 2 * 25.4 / 13
    long = axis(grip=88.9)
    occupied.local_hardware(long)
    assert long["grip_mm"] == pytest.approx(88.9)
    assert long["nominal_under_head_length_mm"] == pytest.approx(127.)
    with pytest.raises(ValueError, match="no planning length"):
        occupied.local_hardware(axis(grip=160.))


def test_flat_annular_seats_and_material_loss_are_distinct():
    record = axis(before=0.)
    wood = cq.Solid.makeBox(100, 100, 38.1, cq.Vector(-50, -50, 0))
    wood = occupied.bore_wood({"wood": wood}, [record])["wood"]
    seats = occupied.washer_seats([record], {"wood": wood}, [])
    assert [r["annular_seat_fraction"] for r in seats] == [1., 1.]
    slot = cq.Solid.makeBox(20, 100, 38.1, cq.Vector(10, -50, 0))
    partial = occupied.washer_seats([record], {"wood": wood.cut(slot)}, [])
    assert all(.5 < r["annular_seat_fraction"] < 1. for r in partial)
    assert all(r["bearing_or_bending_capacity_checked"] is False for r in partial)


def test_washer_on_steel_is_not_mistaken_for_wood_contact():
    record = axis()
    record["attachments"] = [{"angle_id": "plate"}]
    plate = cq.Solid.makeBox(100, 100, 5.55625, cq.Vector(-50, -50, -5.55625))
    plate = plate.cut(cq.Solid.makeCylinder(14.2875 / 2, 5.55625, cq.Vector(0, 0, -5.55625)))
    wood = cq.Solid.makeBox(100, 100, 38.1, cq.Vector(-50, -50, 0))
    seats = occupied.washer_seats([record], {"wood": wood}, [SimpleNamespace(id="plate", shape=plate)])
    assert [(r["support_material"], r["annular_seat_fraction"]) for r in seats] == [("steel", 1.), ("wood", 1.)]
