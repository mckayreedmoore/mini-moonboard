"""PB05 upper-center detached pair: geometry evidence only."""

from dataclasses import replace

import pytest

from scripts import simple_pb05_upper_center_detached as detached


@pytest.fixture(scope="module")
def result():
    return detached.screen()


def test_full_pb05_inventory_and_retained_work(result):
    assert result["source_id"] == detached.pb05.SOURCE_ID
    assert result["inventory"] == {
        "pb05_outer_blocks": 6,
        "pb05_unchanged_center_blocks": 2,
        "candidate_blocks": 2,
        "candidate_bolt_axes": 8,
        "legacy_sds_axes_retained": 12,
        "legacy_sds_axes_total_retained": 84,
        "original_frame_bolt_axes": 12,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["hypothetical_duties"] == {"before": 14, "after": 12}
    assert result["gates"]["source_preserved"]
    assert result["gates"]["complete_candidate_bores"]
    assert result["strength_checked"] is False
    assert result["drilling_released"] is False


def test_simultaneous_geometry_and_envelopes(result):
    assert set(result["candidate_stations"]) == set(
        detached.upper_center.TARGET_STATIONS
    )
    assert result["gates"]["pair_geometry_clear"]
    assert result["geometry_decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert not any(result["collision_hits_mm3"].values())
    assert not result["retail_upright"]["collision_hits_mm3"]
    assert set(result["collision_hits_mm3"]) >= {
        "pb05_blocks",
        "pb05_bores",
        "pb05_stacks",
        "pb05_tools",
        "frame_bolt_axes",
        "panel_kicker_axes",
        "panel_solids",
        "unrelated_timber",
    }
    assert (
        result["retail_upright"]["product_basis"]
        == "listed 8-in bolt, washer and nut envelope"
    )
    assert result["retail_upright"]["rail_product_selected"] is False
    assert result["geometry_decision"] == (
        "ADVANCE_GEOMETRY_ONLY" if all(result["gates"].values()) else "REVISE_GEOMETRY"
    )


def test_injected_pb05_block_collision_fails():
    pair, module = detached.build_inputs()
    first = next(iter(pair))
    outer = next(iter(detached.pb05.OUTER_STATIONS))
    block = next(
        part.shape
        for part in module.wood_parts()
        if part.name == module.pb03_geometries()[outer].block_name
    )
    altered = {**pair, first: replace(pair[first], block=block)}
    result = detached.screen(pair=altered, module=module)
    assert result["collision_hits_mm3"]["pb05_blocks"]
    assert result["geometry_decision"] == "REVISE_GEOMETRY"
