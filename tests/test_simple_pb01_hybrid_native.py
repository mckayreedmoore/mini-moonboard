"""Preparation-only PB01 hybrid: never a V4 demand or capacity test."""

import cadquery as cq
import numpy as np
import pytest

from fea.current_response_run import physical_forces
from fea.floor_flush_mesh import FlushStructure
from fea.horizontal_panel_frame import next_bearing_set, panel_kernel
from scripts import simple_pb01_hybrid_native as hybrid
from scripts.simple_pb01_hybrid_native import HybridPB01, prepare_case


@pytest.fixture(scope="module")
def prepared():
    before = (panel_kernel.grid, panel_kernel.pressure_load, FlushStructure.member)
    result = prepare_case("a12-forward")
    assert (
        panel_kernel.grid,
        panel_kernel.pressure_load,
        FlushStructure.member,
    ) == before
    return result


def test_hybrid_inventory_has_one_replaced_station_and_all_panel_axes():
    module = HybridPB01()
    clips = {c.members[0] for c in module.connections() if c.name.startswith("clip_")}
    assert len(clips) == 23
    assert "clip_horizontal_lower_right_1" not in clips
    assert len(module.panel_connections()) == 66
    baseline = {c.name: c for c in module.raw.panel_connections()}
    for connection in module.panel_connections():
        original = baseline[connection.name]
        assert connection.start.toTuple() == original.start.toTuple()
        assert connection.direction.toTuple() == original.direction.toTuple()
    assert "base_cleat_pb01" in {p.name for p in module.uncut_wood_parts()}


def test_prepared_hybrid_has_two_serial_groups_and_traceable_force_ownership(prepared):
    structure, metadata = prepared
    assert "base_cleat_pb01" in structure.members
    assert len(metadata["pb01_bolt_groups"]["upright"]) == 2
    assert len(metadata["pb01_bolt_groups"]["rail"]) == 2
    assert len(metadata["legacy_proxy_stations"]) == 23
    assert metadata["pb01_same_case_demand"] is False
    assert metadata["qualified_for_design"] is False
    assert metadata["acceptance"] is False
    owners = metadata["connection_ownership"]
    assert not any(name.startswith("clip_horizontal_lower_right_1_") for name in owners)
    assert (
        len([name for name in owners if name.startswith(("round_", "kicker_header_"))])
        == 66
    )
    for group in metadata["pb01_bolt_groups"].values():
        for name in group:
            assert name in owners
            assert owners[name]["first"] != owners[name]["second"]
            assert "base_cleat_pb01" in (owners[name]["first"], owners[name]["second"])
    for name in metadata["pb01_contact_names"]:
        assert name in owners
        assert "scalar_normal" in owners[name]
        assert any(
            spring["name"] == name and spring["bearing_closed_assumption"]
            for spring in structure.springs
        )
    fake = {
        "connector_forces": {
            name: {"force_on_first_xyz_n": [1.0, 2.0, 3.0]}
            for name in metadata["pb01_bolt_groups"]["upright"]
        }
    }
    record = {
        "connection_ownership": {
            name: owners[name] for name in fake["connector_forces"]
        },
        "springs": [],
    }
    physical = physical_forces(record, fake)
    for row in physical.values():
        assert np.allclose(
            np.add(row["force_on_first_xyz_n"], row["force_on_second_xyz_n"]), 0
        )
        point = np.asarray(row["point"])
        origin = np.array([89.05, 616.914452, 1199.968456])
        first_moment = np.cross(point - origin, row["force_on_first_xyz_n"])
        second_moment = np.cross(point - origin, row["force_on_second_xyz_n"])
        assert np.allclose(first_moment + second_moment, 0)


def test_pb01_contact_normals_point_into_hosts_and_opening_releases(prepared):
    _, metadata = prepared
    raw = {part.name: part.shape for part in HybridPB01().uncut_wood_parts()}
    for name in metadata["pb01_contact_names"]:
        owner = metadata["connection_ownership"][name]
        point = cq.Vector(*owner["point"])
        normal = cq.Vector(*owner["scalar_normal"])
        assert raw[owner["first"]].isInside(point + normal * 0.1, 0.001)
        assert raw[owner["second"]].isInside(point - normal * 0.1, 0.001)
        assert name not in next_bearing_set(
            [{"name": name, "active": True, "opening_mm": 0.1}]
        )
        assert name in next_bearing_set(
            [{"name": name, "active": True, "opening_mm": -0.1}]
        )


def test_four_trial_bolt_gravity_loads_are_explicit_and_balance(prepared):
    structure, metadata = prepared
    rows = metadata["pb01_trial_bolt_gravity"]
    assert len(rows) == 4
    assert {row["family"] for row in rows} == {"upright", "rail"}
    total_mass = sum(row["mass_kg"] for row in rows)
    assert total_mass > 0
    assert metadata["pb01_trial_bolt_total_mass_kg"] == pytest.approx(total_mass)
    assert len(metadata["additional_member_loads"]) == 8
    for row in rows:
        assert structure.loads[row["host_node"]][2] == pytest.approx(
            -row["mass_kg"] * 9.80665 / 2
        )
        assert structure.loads[row["cleat_node"]][2] == pytest.approx(
            -row["mass_kg"] * 9.80665 / 2
        )
        assert row["mass_basis"] == "diagnostic steel envelope only"
    assert sum(
        load["force"][2] for load in metadata["additional_member_loads"]
    ) == pytest.approx(-total_mass * 9.80665)


def test_failed_preparation_restores_shared_builders(monkeypatch):
    before = (panel_kernel.grid, panel_kernel.pressure_load, FlushStructure.member)

    def fail(*args, **kwargs):
        raise RuntimeError("injected prepare failure")

    monkeypatch.setattr(hybrid, "prepare_flush", fail)
    with pytest.raises(RuntimeError, match="injected prepare failure"):
        prepare_case("a12-left")
    assert (
        panel_kernel.grid,
        panel_kernel.pressure_load,
        FlushStructure.member,
    ) == before


def test_quarter_in_variant_has_distinct_identity_and_four_explicit_stack_weights(
    prepared,
):
    quarter = HybridPB01(variant="quarter")
    old = HybridPB01()
    assert quarter.KEY != old.KEY
    assert quarter.pose["nominal_trial_bolt_diameter_mm_not_selected"] == 6.35
    assert quarter.pose["diagnostic_wood_bore_diameter_mm_not_drill_instruction"] == 7.5
    structure, metadata = prepare_case("a12-left", variant="quarter")
    assert metadata["candidate"] == quarter.KEY
    assert metadata["pb01_pose_variant"] == "quarter"
    assert metadata["pb01_trial_bolt_diameter_mm"] == 6.35
    assert len(metadata["pb01_trial_bolt_gravity"]) == 4
    assert all(
        row["assumed_shaft_diameter_mm"] == 6.35
        for row in metadata["pb01_trial_bolt_gravity"]
    )
    assert (
        metadata["pb01_trial_bolt_total_mass_kg"]
        < prepared[1]["pb01_trial_bolt_total_mass_kg"]
    )
    assert len(structure.springs) > 0
