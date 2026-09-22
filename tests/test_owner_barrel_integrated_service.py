"""Keep current integrated service evidence separate from historical screens."""

import pytest

from scripts import owner_barrel_rim_outer_top_service_probe as outer_top
from scripts import owner_barrel_rim_withdrawal_hardware_probe as withdrawal
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly


@pytest.fixture(scope="module")
def assembly():
    return build_integrated_viewer_assembly()


def test_integrated_outer_top_has_modeled_stacks_and_nominal_service_paths(assembly):
    report = outer_top.probe(assembly=assembly)
    assert report["viewer_source"].endswith("build_integrated_viewer_assembly")
    assert report["station_count"] == 4
    assert len(assembly["bolts"]) == 46
    assert all(
        set(stack) == {"shaft", "washer", "head"}
        for stack in assembly["stacks"].values()
    )
    assert all(
        operation["finite_status"] == "CLEAR_FINITE_ONLY"
        for station in report["stations"].values()
        for row in station["rows"].values()
        for operation in row["operations"].values()
    )
    assert report["rim_removal_verified"] is False
    assert report["tool_sweep_verified"] is False
    assert report["drilling_released"] is False


def test_integrated_rim_withdrawal_is_sampled_only(assembly):
    report = withdrawal.probe(assembly=assembly)
    assert report["source_assembly"].endswith("build_integrated_viewer_assembly")
    assert report["fixed_axis_inventory"] == {
        "panel_kicker_screws": 66,
        "frame_bolts": 12,
    }
    for side in ("left", "right"):
        row = report["sides"][side]
        assert row["viewer_supplemental_heads_washers_absent_for"] == []
        assert row["retained_inventory"]["bolt_stack_solids"] == 108
        assert len(row["withdrawal"]["samples"]) == 33
        assert row["withdrawal"]["sampled_clear"] is True
        assert row["withdrawal"]["continuous_sweep_verified"] is False
        assert row["withdrawal"]["real_hardware_and_service_verified"] is False
    assert report["drilling_released"] is False
    assert report["fabrication_released"] is False
    assert report["structural_released"] is False
