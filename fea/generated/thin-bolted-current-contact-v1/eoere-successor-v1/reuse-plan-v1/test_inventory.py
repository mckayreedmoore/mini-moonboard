"""Known scalar volume/stack answers; no candidate CAD or response."""

import importlib.util
import math
from pathlib import Path

import pytest

PATH = Path(__file__).with_name("inventory.py")
SPEC = importlib.util.spec_from_file_location("eoere_inventory_coupon", PATH)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


def axis():
    return {"id": "hand", "diameter_mm": 2., "nominal_under_head_length_mm": 20.,
            "grip_mm": 5., "before_plate_mm": 1., "after_plate_mm": 2.,
            "hardware_scenario": {"hex_across_flats_mm": 2., "head_height_mm": 2.,
                                  "nut_height_mm": 3., "washer_od_mm": 4., "washer_id_mm": 2.,
                                  "washer_thickness_mm": 1., "threads_per_inch": 25.4}}


def test_cylinder_hex_bore_annulus_hand_volume():
    result = inventory.hardware_volumes(axis())
    assert result == pytest.approx({"shaft": 20 * math.pi, "head": 4 * math.sqrt(3),
                                   "nut": 6 * math.sqrt(3) - 3 * math.pi,
                                   "head_washer": 3 * math.pi, "nut_washer": 3 * math.pi})
    assert sum(result.values()) == pytest.approx(23 * math.pi + 10 * math.sqrt(3))


def test_source_pack_and_thread_functions_hand_answers():
    purchase, fit = inventory.reused_functions()
    assert purchase(96, .11, 100, 7.53) == {"required": 96, "packs": 1, "pack_quantity": 100,
                                          "singles": 0, "purchased": 100, "spares": 4, "cost_usd": 7.53}
    row = axis()
    washers = {("hand", r): {"thickness_mm": 1., "id_mm": 2.} for r in ("head_washer", "nut_washer")}
    result = fit(row, washers)
    assert result["nut_near_face_from_under_head_mm"] == 10.
    assert result["minimum_thread_length_to_reach_nut_near_face_mm"] == 10.
    assert result["tip_projection_beyond_nut_mm"] == 7.
    assert result["tip_threads"] == 7.
    assert result["delivered_transition_and_engagement_verified"] is False


def test_own_washer_override_changes_only_that_role():
    row = axis()
    original = inventory.hardware_volumes(row)
    revised = inventory.hardware_volumes(row, {("hand", "nut_washer"): {"od_mm": 3., "id_mm": 2., "thickness_mm": .5}})
    assert revised["nut_washer"] == pytest.approx(5 * math.pi / 8)
    assert {k: v for k, v in revised.items() if k != "nut_washer"} == {k: v for k, v in original.items() if k != "nut_washer"}


def test_changed_pure_source_is_rejected(monkeypatch):
    monkeypatch.setattr(inventory, "sha", lambda _p: "0" * 64)
    with pytest.raises(ValueError, match="source differs"):
        inventory.reused_functions()
