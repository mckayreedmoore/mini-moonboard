"""Detached PB04 upper-center geometry evidence; no strength or release."""

from dataclasses import replace

import pytest

from scripts import simple_pb04_upper_center_detached as detached


@pytest.fixture(scope="module")
def result():
    return detached.screen()


def test_complete_inventories_and_source_preservation(result):
    assert result["inventory"] == {
        "legacy_stations_retained": 2,
        "legacy_sds_axes_retained": 12,
        "candidate_blocks": 2,
        "candidate_bolt_axes": 8,
        "pb04_blocks": 8,
        "pb04_counterbored_blocks": 6,
        "original_frame_bolt_axes": 12,
        "fixed_panel_kicker_axes": 66,
        "main_panel_solids": 4,
    }
    assert result["gates"]["source_preserved"]
    assert result["gates"]["complete_candidate_bores"]
    assert result["gates"]["fixed_receivers_supported"]
    assert result["source_id"] == "pb04-upper-edge-plus-outer-counterbores-v1"
    assert result["shifted_upper_outer_rail_row_mm"] == pytest.approx(
        detached.pb04.SELECTED_OFFSET_MM
    )
    assert all(value > 0 for value in result["nearest_clearance_mm"].values())
    assert result["strength_checked"] is False
    assert result["installed_retail_stacks_checked"] is False
    assert result["fabrication_released"] is False


def test_uses_actual_pb04_blocks_and_reports_collision_decision(result):
    assert set(result["candidate_stations"]) == set(
        detached.upper_center.TARGET_STATIONS
    )
    assert set(result["pb04_block_names"]) == set(detached.pb04.BLOCK_NAMES.values())
    assert result["geometry_decision"] in {"ADVANCE_GEOMETRY_ONLY", "REVISE_GEOMETRY"}
    assert result["geometry_decision"] == (
        "ADVANCE_GEOMETRY_ONLY" if all(result["gates"].values()) else "REVISE_GEOMETRY"
    )
    assert result["geometry_decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert not any(result["collision_hits_mm3"].values())
    assert set(result["collision_hits_mm3"]) >= {
        "pb04_blocks",
        "pb04_bores",
        "pb04_stacks",
        "pb04_tools",
        "pb04_counterbores",
        "frame_bolt_axes",
        "panel_kicker_axes",
        "main_panel_solids",
        "unrelated_timber",
    }


def test_injected_pb04_block_collision_revises():
    pair, module = detached.build_inputs()
    first = next(iter(pair))
    pb04_block = next(
        part.shape
        for part in module.wood_parts()
        if part.name in detached.pb04.BLOCK_NAMES.values()
    )
    altered = {**pair, first: replace(pair[first], block=pb04_block)}
    result = detached.screen(pair=altered, module=module)
    assert result["collision_hits_mm3"]["pb04_blocks"]
    assert result["geometry_decision"] == "REVISE_GEOMETRY"
