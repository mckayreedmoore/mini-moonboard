"""Preparation-only PB01 hybrid: never a V4 demand or capacity test."""

import cadquery as cq
import numpy as np
import pytest

from fea.current_response_run import physical_forces
from fea.floor_flush_mesh import FlushStructure
from fea.horizontal_panel_frame import next_bearing_set, panel_kernel
from scripts import simple_pb01_hybrid_native as hybrid
from scripts.simple_pb01_hybrid_native import HybridPB01, prepare_case


def test_candidate_axial_springs_are_switchable_without_changing_lateral_or_face_paths():
    structure, metadata = prepare_case("a12-left", tension_only_axial=True)
    names = {name for group in metadata["pb01_bolt_groups"].values() for name in group}
    axial = [spring for spring in structure.springs if spring.get("tension_only_assumption")]
    assert {spring["name"] for spring in axial} == names
    assert all(spring["dof"] == 1 and spring["bearing_closed_assumption"] for spring in axial)
    assert metadata["pb01_axial_law"] == "tension_only_no_preload"
    assert all(not spring["bearing_closed_assumption"] for spring in structure.springs
               if spring["name"] in names and spring["dof"] != 1)
    active = {spring["name"] for spring in structure.springs if spring["bearing_closed_assumption"]}
    deck = structure.deck(active_bearings=active - names)
    for spring in axial:
        assert f"*SPRING,ELSET={spring['group']}" not in deck
    for spring in structure.springs:
        if spring["name"] in names and spring["dof"] != 1:
            assert f"*SPRING,ELSET={spring['group']}" in deck


def test_short_quarter_variant_rebuilds_native_member_without_reusing_archive():
    short = HybridPB01(variant="quarter_short")
    historical = HybridPB01(variant="quarter")
    assert short.KEY != historical.KEY
    assert short.pose["size_local_x_t_n_mm"] == [139.7, 57.15, 152.4]
    assert historical.pose["size_local_x_t_n_mm"] == [139.7, 57.15, 300]
    assert short.cleat.shape.Volume() / historical.cleat.shape.Volume() == pytest.approx(
        152.4 / 300
    )
    assert short.pose["bolt_groups"] == historical.pose["bolt_groups"]
    assert len(short.panel_connections()) == 66


def test_short_quarter_preparation_tags_its_fresh_pose_and_contact_area():
    structure, metadata = prepare_case(
        "a12-left", variant="quarter_short", tension_only_axial=True
    )
    assert metadata["pb01_pose_variant"] == "quarter_short"
    assert metadata["pb01_pose_source"].endswith("PB01_GROUP_TRIAL_SIZE_MM")
    assert metadata["pb01_axial_law"] == "tension_only_no_preload"
    assert metadata["pb01_contact_faces"]["upright"]["net_area_mm2"] > 0
    assert metadata["pb01_contact_faces"]["rail"]["net_area_mm2"] > 0
    member = structure.members[hybrid.CLEAT]
    assert member["length"] == pytest.approx(152.4)


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
    assert metadata["pb01_axial_law"] == "bilateral_historical"
    assert not any(spring.get("tension_only_assumption") for spring in structure.springs)
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
    structure, metadata = prepared
    raw = {part.name: part.shape for part in HybridPB01().uncut_wood_parts()}
    assert len(metadata["pb01_contact_names"]) == 8
    for family in ("upright", "rail"):
        names = [
            n for n in metadata["pb01_contact_names"] if n.startswith(f"pb01_{family}_")
        ]
        assert len(names) == 4
        face = metadata["pb01_contact_faces"][family]
        assert sum(
            metadata["connection_ownership"][n]["tributary_net_area_mm2"] for n in names
        ) == pytest.approx(face["net_area_mm2"])
        assert sum(
            s["stiffness_n_per_mm"] for s in structure.springs if s["name"] in names
        ) == pytest.approx(1000)
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


def test_off_row_contact_transfers_row_axis_couple_only_when_closed(prepared):
    _, metadata = prepared
    owners = metadata["connection_ownership"]
    for family in ("upright", "rail"):
        bolts = [
            np.asarray(owners[n]["point"]) for n in metadata["pb01_bolt_groups"][family]
        ]
        row = bolts[1] - bolts[0]
        row /= np.linalg.norm(row)
        origin = np.mean(bolts, axis=0)
        normal = np.asarray(owners[f"pb01_{family}_compression_0_0"]["scalar_normal"])
        # Collinear bolt/centroid points give identically zero row-axis moment.
        for point in (*bolts, origin):
            assert np.dot(row, np.cross(point - origin, normal)) == pytest.approx(
                0, abs=1e-8
            )
        names = [
            n for n in metadata["pb01_contact_names"] if n.startswith(f"pb01_{family}_")
        ]
        moments = [
            np.dot(row, np.cross(np.asarray(owners[n]["point"]) - origin, normal))
            for n in names
        ]
        assert max(moments) > 1
        assert min(moments) < -1
        # A compression/opening pair produces the couple; opening contributes nothing.
        closed = next_bearing_set(
            [
                {"name": n, "active": True, "opening_mm": -0.1 if m > 0 else 0.1}
                for n, m in zip(names, moments, strict=True)
            ]
        )
        assert sum(m for n, m in zip(names, moments, strict=True) if n in closed) > 0


def test_independent_trial_stiffnesses_reach_actual_springs():
    structure, metadata = prepare_case(
        "a12-left",
        bolt_axial_n_per_mm=700,
        bolt_lateral_n_per_mm=1200,
        face_normal_total_n_per_mm=2400,
    )
    assert metadata["pb01_trial_stiffness_n_per_mm"] == {
        "bolt_axial": 700,
        "bolt_lateral": 1200,
        "face_normal_total_per_interface": 2400,
    }
    for names in metadata["pb01_bolt_groups"].values():
        for name in names:
            springs = [
                s["stiffness_n_per_mm"] for s in structure.springs if s["name"] == name
            ]
            assert springs == [700, 1200, 1200]
    for family in ("upright", "rail"):
        names = [
            n for n in metadata["pb01_contact_names"] if n.startswith(f"pb01_{family}_")
        ]
        assert [
            s["stiffness_n_per_mm"] for s in structure.springs if s["name"] in names
        ] == [600] * 4


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
