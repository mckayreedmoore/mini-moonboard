"""Opt-in integrated rail length trial; delivered thread fit remains unverified."""

from math import pi

import cadquery as cq
import pytest

from scripts import owner_barrel_rail_layout as rail
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly


@pytest.fixture(scope="module")
def layouts():
    wood = build_integrated_viewer_assembly()["wood"]
    return rail.build_revised_layout(wood), rail.build_integrated_layout(wood)


def _bounds(shape):
    box = shape.BoundingBox()
    return box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax


def test_integrated_rail_inventory_and_source_diagnostics(layouts):
    historical, integrated = layouts
    center = set(rail.INTEGRATED_CENTER_STATIONS)
    outer = set(rail.VIEWER_OUTER_STATIONS)
    assert len(center) == 4
    assert len(outer) == 6
    assert center | outer == set(integrated["stations"]) == set(historical["stations"])
    assert sum(len(integrated["stations"][name]["bolts"]) for name in center) == 8
    assert sum(len(integrated["stations"][name]["bolts"]) for name in outer) == 12
    for name, row in integrated["stations"].items():
        expected = 114.3 if name in center else 152.4
        assert [bolt.length for bolt in row["bolts"].values()] == pytest.approx(
            [expected, expected]
        )
        screen = integrated["diagnostics"]["station_screens"][name]
        assert screen["nominal_bolt_lengths_mm"] == pytest.approx([expected, expected])
        if name in center:
            old_screen = historical["diagnostics"]["station_screens"][name]
            assert old_screen["nominal_bolt_lengths_mm"] == pytest.approx(
                [127.0, 127.0]
            )
            assert screen["nominal_tip_past_assumed_axis_mm"] == pytest.approx(
                [
                    value - 12.7
                    for value in old_screen["nominal_tip_past_assumed_axis_mm"]
                ]
            )
        assert row["disposition"] == "REVISE"
    assert integrated["diagnostics"][
        "integrated_center_rail_bolt_length_mm"
    ] == pytest.approx(114.3)
    assert "integrated_center_rail_bolt_length_mm" not in historical["diagnostics"]
    assert "unverified" in integrated["diagnostics"]["limits"]


def test_shafts_match_connections_while_all_other_geometry_stays_put(layouts):
    historical, integrated = layouts
    for station, row in integrated["stations"].items():
        old = historical["stations"][station]
        assert set(row["bolts"]) == set(old["bolts"])
        assert set(row["barrels"]) == set(old["barrels"])
        assert set(row["drilling_paths"]) == set(old["drilling_paths"])
        assert set(row["access_paths"]) == set(old["access_paths"])
        for name, bolt in row["bolts"].items():
            previous = old["bolts"][name]
            assert bolt.start.toTuple() == pytest.approx(previous.start.toTuple())
            assert bolt.direction.toTuple() == pytest.approx(
                previous.direction.toTuple()
            )
            assert bolt.diameter == pytest.approx(previous.diameter)
            assert bolt.members == previous.members
            assert bolt.kind == previous.kind
            stack, old_stack = row["stacks"][name], old["stacks"][name]
            assert set(stack) == set(old_stack) == {"shaft", "washer", "head"}
            assert stack["shaft"].Volume() == pytest.approx(
                pi * (bolt.diameter / 2) ** 2 * bolt.length
            )
            expected_shaft = cq.Solid.makeCylinder(
                bolt.diameter / 2, bolt.length, bolt.start, bolt.direction.normalized()
            )
            assert _bounds(stack["shaft"]) == pytest.approx(_bounds(expected_shaft))
            if station in rail.INTEGRATED_CENTER_STATIONS:
                assert _bounds(stack["shaft"]) != pytest.approx(
                    _bounds(old_stack["shaft"])
                )
            else:
                assert _bounds(stack["shaft"]) == pytest.approx(
                    _bounds(old_stack["shaft"])
                )
            for role in ("washer", "head"):
                assert _bounds(stack[role]) == pytest.approx(_bounds(old_stack[role]))
                assert stack[role].Volume() == pytest.approx(old_stack[role].Volume())
        for role in ("barrels", "drilling_paths", "access_paths"):
            for name, shape in row[role].items():
                original = old[role][name]
                assert _bounds(shape) == pytest.approx(_bounds(original))
                assert shape.Volume() == pytest.approx(original.Volume())
