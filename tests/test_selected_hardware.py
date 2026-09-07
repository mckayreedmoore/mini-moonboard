"""Lightweight selected-product inventory checks; no CAD or native solver."""
import csv
from collections import Counter
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from mini_moonboard import selected_hardware as h


def test_exact_exported_transition_inventory_and_product_counts():
    path = Path(__file__).resolve().parents[1]/"exports/lower-transition-development/lower-transition-development_connections.csv"
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(h.SPECS_BY_NAME) == 278
    assert {r["connection"] for r in rows} == set(h.SPECS_BY_NAME)
    counts = Counter()
    for row in rows:
        spec = h.spec_for(SimpleNamespace(name=row["connection"], kind=row["kind"], grip=float(row["grip_mm"])))
        counts[spec.product] += 1
        assert spec.qualified_for_design is False
        if isinstance(spec, h.BoltSpec):
            assert spec.length_mm == pytest.approx(float(row["length_mm"]))
    assert counts[h.R4_2.product] == 80
    assert counts[h.R4_2_5.product] == 8
    assert counts[h.R4_3_5.product] == 24
    assert counts[h.SD9112.product] == 32
    assert counts[h.SDS25112.product] == 20
    assert sum(isinstance(s, h.BoltSpec) for s in h.SPECS_BY_NAME.values()) == 114


@pytest.mark.parametrize("name,kind,grip", [
    ("panel_65", "screw", 0), ("leg_stitch_left_4", "bolt", 38.1),
    ("panel_1", "bolt", 0), ("panel_1", "screw", 1),
    ("leg_stitch_left_1", "bolt", 44.1), ("leg_stitch_left_1", "bolt", float("nan")),
    ("transition_top_left_bolt_1", "bolt", float("inf")),
])
def test_unknown_names_kinds_and_grips_rejected(name, kind, grip):
    with pytest.raises(ValueError):
        h.spec_for(SimpleNamespace(name=name, kind=kind, grip=grip))


def test_immutable_specs_and_mapping():
    with pytest.raises(FrozenInstanceError):
        h.R4_2.length_nominal_mm = 1
    with pytest.raises(TypeError):
        h.SPECS_BY_NAME["panel_1"] = h.R4_3_5


def test_bolt_tolerance_stacks_and_thread_bearing_are_not_smooth_shank_claims():
    expected = {38.1: 5.4102, 44.1: 5.7602, 69.5: 5.2522, 76.2: 4.9022, 82.2: 5.2522, 94.9: 4.2362}
    for spec in h.SPECS_BY_NAME.values():
        if not isinstance(spec, h.BoltSpec):
            continue
        projection = (spec.length_mm-spec.length_under_tolerance_mm-spec.grip_mm
                      -2*spec.washer_thickness_max_mm-spec.nut_height_max_mm)
        assert projection == pytest.approx(expected[spec.grip_mm])
        assert projection >= 2*spec.pitch_mm  # Tip projection, not two complete chamfer-free threads.
        assert spec.length_mm-spec.thread_length_reference_mm < spec.washer_thickness_nominal_mm+spec.grip_mm
        assert spec.washer_id_min_mm > spec.body_diameter_max_mm


def test_screw_nominal_generation_bounds_and_assumed_tools_are_separate():
    assert h.R4_2_5.length_screen_min_mm == 60.325
    assert h.R4_2_5.thread_length_screen_max_mm == 41.275
    assert h.R4_2_5.thread_length_nominal_mm == h.R4_2_5.thread_length_screen_min_mm == 39.878
    assert h.R4_2_5.length_nominal_mm == h.R4_2_5.length_screen_max_mm == 63.5
    assert h.R4_2.thread_length_screen_min_mm == 31.75
    assert h.R4_3_5.thread_length_screen_max_mm == 60.325
    for spec in (h.R4_2, h.R4_2_5, h.R4_3_5, h.SD9112, h.SDS25112):
        assert spec.head_allowance_diameter_mm > spec.head_diameter_nominal_mm
        assert spec.tool_allowance_diameter_mm > spec.head_allowance_diameter_mm
        assert spec.tool_allowance_length_mm == 50
    assert h.R4_2.length_datum == "head_top" and h.R4_2.seating == "flush"
    assert h.SDS25112.length_datum == "underhead" and h.SDS25112.seating == "flat"
    assert h.SDS25112.root_diameter_nominal_mm is None
    assert h.SD9112.head_rim_height_nominal_mm is None
