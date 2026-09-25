"""Focused checks for the current WJ24 source-to-topology map."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from scripts.wood_joint_current_mass_topology_map import (
    build_current_mass_source_topology_map,
    load_current_inputs,
)


@pytest.fixture
def frozen_inputs():
    root = Path(__file__).resolve().parents[1]
    return load_current_inputs(root)


def test_current_mass_rows_map_once_and_rebuild_the_exported_resultant(
    frozen_inputs,
):
    inputs, hashes = frozen_inputs
    result = build_current_mass_source_topology_map(**inputs, source_sha256=hashes)

    assert result["mass_inventory_row_count"] == 778
    assert result["unique_source_mass_entity_count"] == 778
    assert result["source_mass_entity_counts"] == {
        "current_candidate_hardware_component": 460,
        "current_panel_screw_axis_envelope_proxy": 66,
        "current_physical_member_solid": 50,
        "current_physical_tnut_component": 142,
        "current_retained_frame_hardware_component": 60,
    }
    assert result["status"] == (
        "GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP"
    )
    assert result["global_model_integration"]["solver_dof_mapping_implemented"] is False
    assert (
        result["global_model_integration"]["reduced_model_mass_transfer_implemented"]
        is False
    )
    assert result["global_model_integration"]["solver_dof_mapping_count"] == 0
    assert result["global_model_integration"]["implemented_mass_carrier_count"] == 0
    integration = result["global_model_integration"]
    assert (
        integration[
            "illustrative_carrier_count_if_one_carrier_is_chosen_per_nonmember_source_row"
        ]
        == 728
    )
    assert (
        "not an adopted requirement" in integration["illustrative_carrier_count_status"]
    )
    assert result["modeled_mass_kg"] == pytest.approx(224.4207766683882)
    assert result["modeled_mass_center_global_xyz_mm"] == pytest.approx(
        [-1.6445371504, 697.8575809735, 1033.6090565930]
    )
    assert result["gravity_force_global_xyz_n"] == pytest.approx(
        [0.0, 0.0, -2200.8160095150]
    )
    assert result["gravity_moment_about_global_origin_nmm"] == pytest.approx(
        [-1535856.136568, -3619.323689, 0.0]
    )
    assert result["equipment_allowance"] == {
        "mass_kg": 25.0,
        "included_in_mass_rows": False,
        "additional_allowance_rows": 0,
        "placement_scenarios": "Use the separate current-frame-dead-load-map scenarios; this artifact assigns no actual accessory centroid.",
    }
    source_ids = [
        row["source_mass_entity"]["id"] for row in result["physical_mass_rows"]
    ]
    assert len(source_ids) == len(set(source_ids)) == 778
    assert all(
        row["source_mass_entity"]["solver_dof_id"] is None
        and row["source_mass_entity"]["solver_dof_mapping_status"]
        == "not_implemented_geometry_to_topology_map_only"
        for row in result["physical_mass_rows"]
    )
    assert (
        sum(
            row["source_mass_entity"]["location_status"] != "source_station_retained"
            for row in result["physical_mass_rows"]
            if row["source_mass_entity"]["kind"]
            == "current_panel_screw_axis_envelope_proxy"
        )
        == 8
    )
    routes = result["global_model_integration"]["integration_routes"]
    assert [route["count"] for route in routes] == [50, 520, 142, 66]
    assert (
        "distributed member mass/load"
        in result["source_to_topology_semantics"]["reduced_member_limit"]
    )
    assert "do not assign to nearest timber" in routes[1]["current_status"]
    assert "documented aggregate/condensed" in routes[1]["reduced_model_route"]
    assert "one carrier per omitted T-nut" in routes[2]["reduced_model_route"]

    receiver_axes = {row["axis_id"]: row for row in inputs["receiver"]["axes"]}
    moved_axes = {
        row["axis_id"]: row
        for row in inputs["scene"]["model_inventory"]["moved_panel_axes"]
    }
    screw_rows = [
        row
        for row in result["physical_mass_rows"]
        if row["source_mass_entity"]["kind"]
        == "current_panel_screw_axis_envelope_proxy"
    ]
    assert len(screw_rows) == 66
    for row in screw_rows:
        entity = row["source_mass_entity"]
        assert entity["current_cad_axis_envelope_length_mm"] == pytest.approx(63.5)
        assert entity[
            "historical_inventory_source_occupied_length_mm"
        ] == pytest.approx(50.8)
        axis = receiver_axes[entity["axis_id"]]
        if entity["axis_id"] in moved_axes:
            start = moved_axes[entity["axis_id"]]["new_start_global_xyz_mm"]
            direction = moved_axes[entity["axis_id"]]["axis_global_xyz_unchanged"]
        else:
            start = axis["origin_global_xyz_mm"]
            direction = axis["axis_global_xyz"]
        expected_center = [start[i] + 31.75 * direction[i] for i in range(3)]
        assert row["mass_center_global_xyz_mm"] == pytest.approx(expected_center)


def test_candidate_receiver_membership_must_match_the_current_contact_graph(
    frozen_inputs,
):
    inputs, hashes = frozen_inputs
    tampered = copy.deepcopy(inputs)
    axis = next(iter(tampered["scene"]["model_inventory"]["candidate_axes"]))
    tampered["scene"]["model_inventory"]["candidate_axes"][axis]["receiver_ids"].pop()

    with pytest.raises(ValueError, match="candidate receiver membership mismatch"):
        build_current_mass_source_topology_map(**tampered, source_sha256=hashes)


def test_tnut_panel_reference_is_checked_against_current_panel_bounds(frozen_inputs):
    inputs, hashes = frozen_inputs
    tampered = copy.deepcopy(inputs)
    panel = next(
        row
        for row in tampered["graph"]["inventories"]["physical_members"]
        if row["member_id"] == "main_lower_left"
    )
    panel["finished"]["bounds_xyz_mm"][1] = -900.0

    with pytest.raises(
        ValueError, match="T-nut centroid fails its source-label panel bounds check"
    ):
        build_current_mass_source_topology_map(**tampered, source_sha256=hashes)


def test_current_screw_envelope_length_is_not_the_historical_source_length(
    frozen_inputs,
):
    inputs, hashes = frozen_inputs
    tampered = copy.deepcopy(inputs)
    tampered["receiver"]["axes"][0]["materialized_axis_envelope"]["axial_length_mm"] = (
        50.8
    )

    with pytest.raises(ValueError, match="current screw CAD axis-envelope length"):
        build_current_mass_source_topology_map(**tampered, source_sha256=hashes)
