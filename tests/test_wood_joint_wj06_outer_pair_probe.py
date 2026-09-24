"""Focused pure-plan tests for the right outer paired-rail geometry."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj06_outer_pair_probe as probe

ROOT = Path(__file__).resolve().parents[1]


def test_plan_binds_only_two_outer_duties_and_preserves_fixed_axes():
    plan = probe.trial_plan()

    assert plan["trial_id"] == probe.TRIAL_ID
    assert set(plan["stations"]) == {probe.LOWER_STATION, probe.UPPER_STATION}
    assert plan["fixed_obligations"] == {
        "fixed_panel_kicker_axes": 66,
        "starting_frame_bolt_axes": 12,
        "preserved": True,
        "former_outer_sds_axes_removed": 12,
        "all_other_source_openings_reapplied": True,
    }
    assert plan["claim_boundary"] == {
        "target_duty_count": 2,
        "target_old_sds_axis_count": 12,
        "accepted_replacement_count": 0,
        "capacity_established": False,
        "drilling_released": False,
        "fabrication_released": False,
        "purchase_approved": False,
        "structural_accepted": False,
        "assembly_proven": False,
    }
    assert (
        sum(
            station["removed_old_sds_axis_count"]
            for station in plan["stations"].values()
        )
        == 12
    )
    assert all(
        len(station["replaced_source_sds_axes"]) == 6
        for station in plan["stations"].values()
    )


def test_source_pins_cover_directly_reused_geometry_producers():
    assert {
        "mini_moonboard/wood_joint_frame.py",
        "mini_moonboard/compact_floor_flush_frame.py",
        "mini_moonboard/hold_tnut_reinforcement.py",
        "mini_moonboard/wood_joint_panel_machining.py",
        "scripts/wood_joint_wj04_probe.py",
        "scripts/wood_joint_wj04_full_stock_probe.py",
        "scripts/wood_joint_wj06_residual_probe.py",
        "scripts/wood_joint_clearance.py",
    } <= set(probe.SOURCE_INPUTS)


def test_only_the_two_target_clips_are_removed_from_retained_source_hardware():
    station_ids = [f"source_station_{index}" for index in range(22)] + [
        probe.LOWER_STATION,
        probe.UPPER_STATION,
    ]
    inventory = {
        "legacy_duties": [
            {"legacy_station_id": station_id} for station_id in station_ids
        ]
    }
    current_parts = tuple(
        SimpleNamespace(name=station_id, shape=station_id) for station_id in station_ids
    )

    retained = probe._retained_source_clips(current_parts, inventory)

    assert len(retained) == 22
    assert probe.LOWER_STATION not in retained
    assert probe.UPPER_STATION not in retained
    assert set(retained) == set(station_ids[:-2])


def test_source_bounds_and_full_depth_cleat_poses_match_inventory():
    plan = probe.trial_plan()
    bounds = plan["source_datums"]["basis_bounds_mm"]

    assert bounds[probe.LOWER_RAIL]["X"] == pytest.approx([89.05, 1127.125])
    assert bounds[probe.LOWER_RAIL]["T"] == pytest.approx([1315.774134, 1353.874134])
    assert bounds[probe.UPPER_RAIL]["T"] == pytest.approx([1459.824134, 1497.924134])
    assert bounds[probe.SIDE_HOST]["X"] == pytest.approx([1127.125, 1216.025])
    assert plan["source_datums"]["source_section_mm"][probe.SIDE_HOST] == pytest.approx(
        [88.9, 139.7]
    )
    assert plan["source_datums"]["grain_axis_global_xyz"][
        probe.SIDE_HOST
    ] == pytest.approx(list(probe.WJ04_TRIAL.frame.t_global))
    assert plan["stations"][probe.LOWER_STATION]["cleat"]["origin_x_t_n_mm"] == (
        pytest.approx([1038.225, 1353.874134, 229.840968])
    )
    assert plan["stations"][probe.UPPER_STATION]["cleat"]["origin_x_t_n_mm"] == (
        pytest.approx([1038.225, 1497.924134, 229.840968])
    )
    assert all(
        row["cleat"]["size_x_t_n_mm"] == [88.9, 88.9, 119.7]
        for row in plan["stations"].values()
    )
    assert plan["pair_geometry"]["clear_t_gap_mm"] == pytest.approx(55.15)
    assert all(
        row["cleat"]["delivered_stock_observed"] is False
        for row in plan["stations"].values()
    )


def test_stack_layers_grips_and_side_lengths_are_explicitly_provisional():
    plan = probe.trial_plan()
    rows = {row["stack_id"]: row for row in plan["stacks"]}

    assert set(rows) == {
        "lower_rail_1",
        "lower_rail_2",
        "lower_side_1",
        "lower_side_2",
        "upper_rail_1",
        "upper_rail_2",
        "upper_side_1",
        "upper_side_2",
    }
    assert all(
        rows[name]["wood_grip_mm"] == pytest.approx(127.0)
        for name in ("lower_rail_1", "lower_rail_2", "upper_rail_1", "upper_rail_2")
    )
    assert all(
        rows[name]["wood_grip_mm"] == pytest.approx(177.8)
        for name in ("lower_side_1", "lower_side_2", "upper_side_1", "upper_side_2")
    )
    assert rows["lower_rail_1"]["layers_head_to_nut"] == [
        {"member_id": probe.LOWER_CLEAT, "thickness_mm": 88.9},
        {"member_id": probe.LOWER_RAIL, "thickness_mm": 38.1},
    ]
    assert rows["upper_rail_1"]["axis_direction_basis"] == [0.0, 1.0, 0.0]
    assert rows["upper_rail_1"]["axis_point_basis_mm"][1] == pytest.approx(1459.824134)
    assert rows["upper_rail_1"]["axis_point_basis_mm"][1] + rows["upper_rail_1"][
        "wood_grip_mm"
    ] == pytest.approx(1586.824134)
    assert rows["lower_rail_1"]["axis_point_basis_mm"][1] == pytest.approx(1442.774134)
    assert rows["lower_rail_1"]["axis_point_basis_mm"][1] - rows["lower_rail_1"][
        "wood_grip_mm"
    ] == pytest.approx(1315.774134)
    assert rows["lower_side_1"]["axis_direction_basis"] == [1.0, 0.0, 0.0]
    assert rows["lower_side_1"]["axis_point_basis_mm"] == pytest.approx(
        [1038.225, 1381.874134, 289.690968]
    )
    assert all(
        rows[name]["nominal_bolt_length_mm"] == 203.2
        and "unselected" in rows[name]["hardware_model"]
        for name in ("lower_side_1", "lower_side_2", "upper_side_1", "upper_side_2")
    )
    assert all(
        rows[name]["hardware_source_url"] == probe.SIDE_BOLT_CATALOG_URL
        for name in ("lower_side_1", "lower_side_2", "upper_side_1", "upper_side_2")
    )
    assert plan["provisional_length_arithmetic"][
        "side_min_length_margin_with_layer_allowance_mm"
    ] == pytest.approx(7.4836)
    assert plan["provisional_length_arithmetic"][
        "side_earliest_nut_bearing_face_mm"
    ] == pytest.approx(179.3908)
    assert plan["provisional_length_arithmetic"][
        "side_required_length_with_reserve_mm"
    ] == pytest.approx(191.1444)
    assert "unresolved" in plan["provisional_length_arithmetic"]["thread_engagement"]


def test_full_depth_rows_avoid_the_shifted_upper_g7_cross_bore():
    plan = probe.trial_plan()
    rows = {row["stack_id"]: row for row in plan["stacks"]}
    side_n = rows["upper_side_1"]["axis_point_basis_mm"][2]
    rail_ns = [
        rows[f"upper_rail_{index}"]["axis_point_basis_mm"][2] for index in (1, 2)
    ]

    assert rail_ns == pytest.approx([273.190968, 306.190968])
    assert min(abs(side_n - n) for n in rail_ns) == pytest.approx(16.5)
    assert plan["pair_geometry"][
        "cross_bore_surface_gap_at_7p5_envelopes_mm"
    ] == pytest.approx(9.0)
    assert abs(side_n - 289.590968) == pytest.approx(0.1)
    assert "nearly coincide" in plan["pair_geometry"]["upper_g7_shifted_row_warning"]

    shifted = replace(
        probe.STACK_SPECS[4],
        axis_point_basis_mm=(
            probe.STACK_SPECS[4].axis_point_basis_mm[0],
            probe.STACK_SPECS[4].axis_point_basis_mm[1],
            289.590968,
        ),
    )
    with pytest.raises(ValueError, match="differs from named proposal"):
        probe.build_stacks((*probe.STACK_SPECS[:4], shifted, *probe.STACK_SPECS[5:]))


def test_plan_fails_closed_if_a_target_source_duty_changes():
    raw = json.loads((ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text())
    inventory = deepcopy(raw)
    duty = next(
        row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] == probe.LOWER_STATION
    )
    duty["legacy_host_members"] = [probe.LOWER_RAIL, "base_principal_center_right"]

    with pytest.raises(ValueError, match="source host mapping changed"):
        probe.trial_plan(inventory)


def test_plan_fails_closed_if_source_axis_inventory_count_changes():
    raw = json.loads((ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text())
    inventory = deepcopy(raw)
    duty = next(
        row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] == probe.UPPER_STATION
    )
    duty["legacy_sds_axes"].pop()

    with pytest.raises(ValueError, match="expected 144 source SDS axes"):
        probe.trial_plan(inventory)


def test_installed_shaft_in_bore_is_clear_but_intrusion_into_same_host_is_reported():
    host = cq.Solid.makeBox(20, 20, 20, cq.Vector(0, 0, 0))
    clearance_bore = cq.Solid.makeCylinder(
        3.75, 22, cq.Vector(-1, 10, 10), cq.Vector(1, 0, 0)
    )
    finished_host = host.cut(clearance_bore)
    shaft_in_bore = cq.Solid.makeCylinder(
        3.175, 20, cq.Vector(0, 10, 10), cq.Vector(1, 0, 0)
    )
    shaft_intruding_wood = cq.Solid.makeCylinder(
        3.175, 20, cq.Vector(0, 14, 10), cq.Vector(1, 0, 0)
    )

    assert (
        probe._installed_component_timber_hits(
            {"shaft": shaft_in_bore}, {"host": finished_host}
        )
        == {}
    )
    hits = probe._installed_component_timber_hits(
        {"shaft": shaft_intruding_wood}, {"host": finished_host}
    )
    assert hits["shaft"]["host"] > 0


def test_two_separated_bores_both_cut_their_shared_finished_member():
    host = cq.Solid.makeBox(60, 20, 20, cq.Vector(0, 0, 0))
    bores = {
        "left": cq.Solid.makeCylinder(
            3.75, 22, cq.Vector(15, 10, -1), cq.Vector(0, 0, 1)
        ),
        "right": cq.Solid.makeCylinder(
            3.75, 22, cq.Vector(45, 10, -1), cq.Vector(0, 0, 1)
        ),
    }
    stacks = {
        stack_id: SimpleNamespace(layers=(probe.StackLayer("shared_host", 20.0),))
        for stack_id in bores
    }

    finished = probe._finished_members_with_bores({"shared_host": host}, stacks, bores)[
        "shared_host"
    ]
    for x in (15, 45):
        shaft = cq.Solid.makeCylinder(3.0, 20, cq.Vector(x, 10, 0), cq.Vector(0, 0, 1))
        assert probe._volume(finished, shaft) < 1e-6
