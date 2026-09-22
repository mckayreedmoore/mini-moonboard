"""Fast contract tests for the forthcoming three-family barrel viewer adapter."""

from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import simple_owner_duty_ledger as ledger
from scripts.owner_barrel_layout_assembly import FAMILY_STATIONS, build_assembly


def _box(x):
    return cq.Solid.makeBox(2, 2, 2, cq.Vector(x, 0, 0))


def _fixtures():
    duties = ledger.selected_duties()
    panel = [SimpleNamespace(name=f"panel_{n}", kind="screw") for n in range(66)]
    frame = [SimpleNamespace(name=f"frame_{n}", kind="bolt") for n in range(12)]
    sds = [
        SimpleNamespace(name=name, kind="screw")
        for duty in duties.values()
        for name in duty["sds_axes"]
    ]
    parts = [
        SimpleNamespace(
            name="base_post_center_left",
            shape=cq.Solid.makeBox(38.1, 1, 1, cq.Vector(-89.05, 0, 0)),
        ),
        SimpleNamespace(
            name="base_post_center_right",
            shape=cq.Solid.makeBox(38.1, 1, 1, cq.Vector(50.95, 0, 0)),
        ),
    ]
    source = SimpleNamespace(
        connections=lambda: tuple(panel + frame + sds),
        panel_connections=lambda: tuple(panel),
        uncut_wood_parts=lambda: tuple(parts),
    )
    placement = {
        "post_shift_x_mm": {"left": -110.0, "right": 110.0},
        "backer_bounds_x_mm": {
            "left": (-90.4875, -1.5875),
            "right": (-1.5875, 87.3125),
        },
    }
    builders = {}
    for family, stations in FAMILY_STATIONS.items():
        rows = {}
        for index, station in enumerate(stations):
            x = 1000.0 * (list(duties).index(station) + 1)
            bolt = SimpleNamespace(
                name=f"{family}_bolt_{index}",
                start=cq.Vector(x + 5, 0, 0),
                direction=cq.Vector(1, 0, 0),
                length=2.0,
                diameter=1.0,
            )
            rows[station] = {
                "mode": "direct",
                "disposition": "REVISE",
                "bolts": {bolt.name: bolt},
                "barrels": {f"{family}_barrel_{index}": _box(x)},
                "stacks": {bolt.name: {"shaft": _box(x + 5)}},
                "drilling_paths": {f"{family}_drill_{index}": _box(x + 10)},
                "access_paths": {f"{family}_access_{index}": _box(x + 15)},
                "axis_offset_mm": 8.001,
            }
        builders[family] = lambda wood, rows=rows: {
            "stations": {station: dict(row) for station, row in rows.items()},
            "diagnostics": {},
        }
    return source, placement, builders


def test_whole_frame_contract_without_heavy_producers():
    source, placement, builders = _fixtures()
    result = build_assembly(builders, source=source, placement=placement)
    assert len(result["station_modes"]) == 24
    assert set(result["station_modes"].values()) == {"direct"}
    assert not result["blocks"]
    assert len(result["barrels"]) == 24
    assert len(result["bolts"]) == 24
    assert len(result["replacement_solids"]) == 24
    assert all(len(shapes) == 2 for shapes in result["replacement_solids"].values())
    assert result["diagnostic_bolt_axes"] == result["bolts"]
    assert result["barrel_solids"] == result["barrels"]
    assert set(result["bolt_station"]) == set(result["bolts"])
    assert set(result["barrel_station"]) == set(result["barrels"])
    assert set(result["bolt_station"].values()) == set(result["station_modes"])
    assert set(result["barrel_station"].values()) == set(result["station_modes"])
    assert set(result["station_dispositions"].values()) == {"REVISE"}
    assert len(result["removed_legacy_stations"]) == 24
    assert len(result["removed_legacy_sds"]) == 144
    assert len(result["panel_connections"]) == 66
    assert len(result["frame_connections"]) == 12
    assert result["wood"]["base_post_center_left"].BoundingBox().xmin == pytest.approx(
        -199.05
    )
    assert result["wood"]["base_post_center_right"].BoundingBox().xmax == pytest.approx(
        199.05
    )
    assert "inner_kicker_backer_left" in result["wood"]
    assert result["hardware_basis"]["axis_offset_mm_provisional"] == 8.001
    assert result["diagnostics"]["status"] == "REVISE"
    assert not result["release_flags"]["fabrication_released"]


def test_rejects_unmarked_compact_block_and_divergent_offset():
    source, placement, builders = _fixtures()
    first = next(iter(FAMILY_STATIONS))
    original = builders[first]

    def marked(wood):
        result = original(wood)
        station = next(iter(result["stations"]))
        result["stations"][station]["compact_alternate_block"] = _box(0)
        return result

    builders[first] = marked
    with pytest.raises(ValueError, match="direct station contains a block"):
        build_assembly(builders, source=source, placement=placement)

    def divergent(wood):
        result = original(wood)
        station = next(iter(result["stations"]))
        result["stations"][station]["axis_offset_mm"] = 9.0
        return result

    builders[first] = divergent
    with pytest.raises(ValueError, match="8.001"):
        build_assembly(builders, source=source, placement=placement)


def test_explicit_mixed_block_and_cross_family_clash_are_visible():
    source, placement, builders = _fixtures()
    first, second = tuple(FAMILY_STATIONS)[:2]
    original_first, original_second = builders[first], builders[second]
    stations = {}

    def mixed(wood):
        result = original_first(wood)
        station = next(iter(result["stations"]))
        row = result["stations"][station]
        row["mode"] = "mixed"
        row["compact_alternate_block"] = _box(0)
        stations["mixed"] = station
        return result

    def clash(wood):
        result = original_second(wood)
        station = next(iter(result["stations"]))
        row = result["stations"][station]
        barrel_name = next(iter(row["barrels"]))
        row["barrels"] = {barrel_name: _box(0)}
        stations["clash"] = station
        return result

    builders[first], builders[second] = mixed, clash
    result = build_assembly(builders, source=source, placement=placement)
    assert result["station_modes"][stations["mixed"]] == "mixed"
    assert len(result["replacement_solids"][stations["mixed"]]) == 3
    assert result["diagnostics"]["cross_family_physical_hits_mm3"]


def test_rejects_non_axis_bolt_object():
    source, placement, builders = _fixtures()
    first = next(iter(FAMILY_STATIONS))
    original = builders[first]

    def missing_axis(wood):
        report = original(wood)
        row = next(iter(report["stations"].values()))
        name = next(iter(row["bolts"]))
        row["bolts"] = {name: SimpleNamespace(name=name)}
        return report

    builders[first] = missing_axis
    with pytest.raises(ValueError, match="start/direction/length/diameter"):
        build_assembly(builders, source=source, placement=placement)
