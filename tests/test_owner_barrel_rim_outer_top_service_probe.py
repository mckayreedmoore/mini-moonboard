"""Bounded rim-on service geometry; no fabrication or safe-service claim."""

import cadquery as cq
import pytest

from scripts import owner_barrel_coordinates as coordinates
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_rim_outer_top_service_probe import (
    FAMILIES,
    STATIONS,
    _service_paths,
    _wood_hits,
    probe,
)
from scripts.simple_owner_duty_ledger import selected_duties


@pytest.fixture(scope="module")
def assembly():
    return build_viewer_assembly()


@pytest.fixture(scope="module")
def result(assembly):
    return probe(assembly=assembly)


def test_exact_four_current_viewer_stations_and_fixed_inventory(result):
    assert result["schema"] == "owner_barrel_rim_outer_top_service_probe/v1"
    assert result["viewer_source"].endswith("build_viewer_assembly")
    assert result["station_count"] == 4
    assert set(result["stations"]) == set(result["station_names"])
    assert {row["family"] for row in result["stations"].values()} == FAMILIES
    assert result["fixed_panel_axes_preserved"] == 66
    assert result["fixed_frame_bolt_axes_preserved"] == 12
    assert result["fixed_inventory"]["panel_screws"] == 66
    assert result["fixed_inventory"]["frame_bolts"] == 12
    assert len(result["panel_shapes_checked_in_place"]) == 6


def test_rows_preserve_rim_panels_and_all_but_eight_rim_screws(result):
    for station, duty in result["stations"].items():
        assert f"base_side_{duty['side']}" in duty["members"]
        assert len(duty["temporarily_removed_panel_screws"]) == 8
        assert all(
            f"_{duty['side']}_rim_" in name
            for name in duty["temporarily_removed_panel_screws"]
        )
        assert duty["frame_bolts_left_in_place"] is True
        assert duty["panel_shapes_left_in_place"] is True
        assert len(duty["rows"]) == 2
        assert set(duty["rows"]) == {
            f"barrel_trial_{station}_{index}" for index in (1, 2)
        }
        for name, row in duty["rows"].items():
            assert row["bolt"] == f"{name}_bolt"
            assert row["bolt_straight_withdrawal_mm"] > row["bolt_nominal_length_mm"]
            assert row["barrel_straight_withdrawal_mm"] > 16
            assert set(row["operations"]) == {
                "bolt_driver",
                "bolt_withdrawal",
                "barrel_access",
                "barrel_withdrawal",
            }


def test_derived_recess_and_axis_differ_by_outer_top_family(result):
    for duty in result["stations"].values():
        sign = 1 if duty["side"] == "left" else -1
        for row in duty["rows"].values():
            if duty["family"] == "top_outer":
                assert row["barrel_recess_mm"] == pytest.approx(11.049, abs=1e-3)
                assert row["bolt_direction_xyz"] == pytest.approx([sign, 0, 0])
                assert row["barrel_direction_xyz"] == pytest.approx(
                    [0, *coordinates.T], abs=1e-5
                )
            else:
                assert duty["family"] == "base_outer_side"
                assert row["barrel_recess_mm"] == pytest.approx(46.449, abs=1e-3)
                assert row["bolt_direction_xyz"] == pytest.approx([0, 0, 1])
                assert row["barrel_direction_xyz"] == pytest.approx([sign, 0, 0])


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_access_length_convention_drift_fails_loudly(assembly, family):
    station = next(
        name for name in STATIONS if selected_duties()[name]["family"] == family
    )
    barrel_name = next(
        name for name, owner in assembly["barrel_station"].items() if owner == station
    )
    key = f"{barrel_name}/barrel_access"
    old = assembly["access_paths"][key]
    inward = (assembly["barrels"][barrel_name].Center() - old.Center()).normalized()
    entry = old.Center() + inward * 20.0
    modified = dict(assembly)
    modified["access_paths"] = dict(assembly["access_paths"])
    modified["access_paths"][key] = cq.Solid.makeCylinder(10, 30, entry, -inward)
    with pytest.raises(ValueError, match="service path changed"):
        _service_paths(modified, station, barrel_name)


def test_current_nominal_corridors_have_no_modeled_blockers(result):
    assert all(
        duty["rim_on_nominal_service_clear"] for duty in result["stations"].values()
    )
    for duty in result["stations"].values():
        for row in duty["rows"].values():
            for operation in row["operations"].values():
                assert operation["finite_status"] == "CLEAR_FINITE_ONLY"
                assert operation["other_wood_hits_mm3"] == {}
                assert operation["fixed_protected_hits_mm3"] == {}
                assert operation["neighbor_hardware_hits_mm3"] == {}


def test_virtual_pilot_relief_applies_only_to_receiving_wood():
    box = cq.Solid.makeBox(10, 10, 10)
    assert _wood_hits(box, {"receiver": box, "other": box}, ("receiver",), box) == {
        "other": 1000.0
    }


def test_no_service_or_build_release(result):
    assert result["rim_removal_verified"] is False
    assert result["tool_sweep_verified"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert "no wood is drilled" in result["limits"].lower()
