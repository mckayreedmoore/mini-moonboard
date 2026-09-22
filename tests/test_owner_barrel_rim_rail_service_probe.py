"""Rim-on rail service findings are bounded nominal geometry, not a release."""

import cadquery as cq
import pytest

from scripts.owner_barrel_rim_rail_service_probe import FAMILIES, _wood_hits, probe


@pytest.fixture(scope="module")
def result():
    return probe()


def test_exact_six_current_viewer_stations_and_fixed_inventory(result):
    assert result["schema"] == "owner_barrel_rim_rail_service_probe/v1"
    assert result["viewer_source"].endswith("build_viewer_assembly")
    assert result["station_count"] == 6
    assert len(result["station_names"]) == 6
    assert set(result["stations"]) == set(result["station_names"])
    assert {row["family"] for row in result["stations"].values()} == FAMILIES
    assert result["fixed_panel_axes_preserved"] == 66
    assert result["fixed_frame_bolt_axes_preserved"] == 12
    assert result["fixed_inventory"]["panel_screws"] == 66
    assert result["fixed_inventory"]["frame_bolts"] == 12
    assert set(result["panel_shapes_checked_in_place"]) == {
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
    }


def test_both_nominal_rows_and_four_service_operations_per_station(result):
    for station, duty in result["stations"].items():
        side = duty["side"]
        assert f"base_side_{side}" in duty["members"]
        assert len(duty["temporarily_removed_panel_screws"]) == 8
        assert all(
            f"_{side}_rim_" in name for name in duty["temporarily_removed_panel_screws"]
        )
        assert duty["frame_bolts_left_in_place"] is True
        assert duty["panel_shapes_left_in_place"] is True
        assert set(duty["rows"]) == {
            f"{station}_barrel_1",
            f"{station}_barrel_2",
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
            assert all(
                operation["finite_status"] in ("BLOCKED_NOMINAL", "CLEAR_FINITE_ONLY")
                for operation in row["operations"].values()
            )


def test_current_nominal_corridors_have_no_modeled_blockers(result):
    assert all(
        row["rim_on_nominal_service_clear"] for row in result["stations"].values()
    )
    for station in result["stations"].values():
        for row in station["rows"].values():
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


def test_screen_never_implies_safe_service_or_drilling(result):
    assert result["rim_removal_verified"] is False
    assert result["tool_sweep_verified"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert "no continuous real tool sweep" in result["limits"].lower()
