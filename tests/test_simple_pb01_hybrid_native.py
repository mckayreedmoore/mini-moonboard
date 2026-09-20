"""Preparation-only PB01 hybrid: never a V4 demand or capacity test."""

import numpy as np

from fea.current_response_run import physical_forces
from scripts.simple_pb01_hybrid_native import HybridPB01, prepare_case


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


def test_prepared_hybrid_has_two_serial_groups_and_traceable_force_ownership():
    structure, metadata = prepare_case("a12-forward")
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
