"""Keep current integrated service evidence separate from historical screens."""

import cadquery as cq
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
        swept = row["withdrawal"]["continuous_swept_aabb"]
        assert swept["path_end_mm"] == 160
        assert swept["retained_hardware_and_protected_clear"] is True
        assert swept["other_wood_clear"] is False
        assert swept["uncertified_targets"]["retained_barrels"] == []
        assert swept["uncertified_targets"]["retained_bolt_stacks"] == []
        assert swept["uncertified_targets"]["protected_envelopes"] == []
        assert all(
            swept["minimum_certified_axis_gap_mm"][family] > 0
            for family in (
                "retained_barrels",
                "retained_bolt_stacks",
                "protected_envelopes",
            )
        )
        wood_sweep = row["withdrawal"]["continuous_wood_sweep"]
        assert wood_sweep["convex_polyhedral_rim_verified"] is True
        assert wood_sweep["continuous_nominal_wood_clear"] is True
        assert wood_sweep["positive_volume_hits_mm3"] == {}
        assert row["withdrawal"]["continuous_nominal_model_sweep_clear"] is True
        assert row["withdrawal"]["continuous_sweep_verified"] is False
        assert row["withdrawal"]["real_hardware_and_service_verified"] is False
    assert report["drilling_released"] is False
    assert report["fabrication_released"] is False
    assert report["structural_released"] is False


def test_swept_box_flags_an_obstacle_between_sampled_positions():
    rim = cq.Workplane("XY").box(1, 1, 1).val()
    hidden_obstacle = cq.Workplane("XY").box(1, 0.1, 1).translate((0, 5, 0)).val()
    clear_obstacle = cq.Workplane("XY").box(1, 0.1, 1).translate((4, 5, 0)).val()
    targets = {
        "other_uncut_wood": {},
        "retained_barrels": {"between_samples": hidden_obstacle},
        "retained_bolt_stacks": {"outside_sweep": clear_obstacle},
        "protected_envelopes": {},
    }
    report = withdrawal._swept_aabb_certificate(rim, cq.Vector(0, 1, 0), 10, targets)
    assert report["retained_hardware_and_protected_clear"] is False
    assert report["uncertified_targets"]["retained_barrels"] == ["between_samples"]
    assert report["uncertified_targets"]["retained_bolt_stacks"] == []


def test_convex_wood_sweep_finds_obstacle_between_sampled_poses():
    rim = cq.Workplane("XY").box(1, 1, 1).val()
    hidden_obstacle = cq.Workplane("XY").box(1, 0.1, 1).translate((0, 5, 0)).val()
    report = withdrawal._continuous_wood_sweep(
        rim, cq.Vector(0, 1, 0), 10, {"between_samples": hidden_obstacle}
    )
    assert report["convex_polyhedral_rim_verified"] is True
    assert report["continuous_nominal_wood_clear"] is False
    assert report["positive_volume_hits_mm3"]["between_samples"] > 0


def test_wood_sweep_refuses_to_treat_a_concave_rim_as_its_convex_hull():
    arm_x = cq.Workplane("XY").box(2, 1, 1, centered=False)
    arm_y = cq.Workplane("XY").box(1, 2, 1, centered=False)
    concave_rim = arm_x.union(arm_y).val()
    with pytest.raises(ValueError, match="not a convex polyhedral solid"):
        withdrawal._continuous_wood_sweep(concave_rim, cq.Vector(0, 1, 0), 10, {})
