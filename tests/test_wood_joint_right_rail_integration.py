"""Focused tests for unioned source and candidate machining on shared rails."""

from __future__ import annotations

import json
import math
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_right_rail_integration as integration


def _axis(x: float, y: float) -> cq.Shape:
    return cq.Solid.makeCylinder(0.4, 12.0, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))


def test_shared_host_omits_only_replaced_sds_and_applies_both_trial_bores():
    raw = cq.Solid.makeBox(12.0, 12.0, 12.0)
    source_cutters = {
        "shared_rail": {
            "retained_sds": _axis(2.0, 2.0),
            "replaced_wj04_sds": _axis(5.0, 5.0),
            "replaced_wj06_sds": _axis(6.0, 6.0),
        }
    }
    candidate_bores = {
        "shared_rail": {
            "wj04/trial/lower_rail_1": _axis(8.0, 8.0),
            "wj06/trial/lower_rail_1": _axis(10.0, 10.0),
        }
    }

    hosts = integration.machine_shared_hosts(
        {"shared_rail": raw},
        source_cutters,
        replaced_source_axis_ids={"replaced_wj04_sds", "replaced_wj06_sds"},
        candidate_bores_by_host=candidate_bores,
    )

    finished = hosts["shared_rail"]
    assert raw.Volume() == pytest.approx(12.0**3)
    assert finished.intersect(
        source_cutters["shared_rail"]["retained_sds"]
    ).Volume() == pytest.approx(0.0)
    assert finished.intersect(
        candidate_bores["shared_rail"]["wj04/trial/lower_rail_1"]
    ).Volume() == pytest.approx(0.0)
    assert finished.intersect(
        candidate_bores["shared_rail"]["wj06/trial/lower_rail_1"]
    ).Volume() == pytest.approx(0.0)

    old_wj04_hole_probe = _axis(5.0, 5.0)
    old_wj06_hole_probe = _axis(6.0, 6.0)
    expected_probe_volume = math.pi * 0.4**2 * 12.0
    assert finished.intersect(old_wj04_hole_probe).Volume() == pytest.approx(
        expected_probe_volume
    )
    assert finished.intersect(old_wj06_hole_probe).Volume() == pytest.approx(
        expected_probe_volume
    )


def test_shared_host_rejects_removing_an_axis_missing_from_source_cutters():
    raw = cq.Solid.makeBox(12.0, 12.0, 12.0)

    with pytest.raises(ValueError, match="not present in the source cutter map"):
        integration.machine_shared_hosts(
            {"shared_rail": raw},
            {"shared_rail": {"retained_sds": _axis(2.0, 2.0)}},
            replaced_source_axis_ids={"unknown_sds"},
            candidate_bores_by_host={},
        )


def test_source_and_candidate_panel_cuts_use_separate_member_datums():
    rail_id = integration.wj04_g7.LOWER_RAIL
    side_id = integration.wj06_outer.SIDE_HOST
    panel_ids = [f"panel_{index:02d}" for index in range(66)]

    def connection(name, start, members):
        return SimpleNamespace(
            name=name,
            kind="screw",
            members=members,
            diameter=0.5,
            length=50.8,
            start=cq.Vector(*start),
            direction=cq.Vector(0.0, 0.0, 1.0),
        )

    native_connections = [
        connection("shared_old_axis", (20.0, 2.0, 4.0), ("clip", rail_id, side_id)),
        connection("panel_00", (30.0, 3.0, 4.0), ("main_lower_right", side_id)),
    ]
    current_connections = [
        connection("shared_old_axis", (16.825, 2.0, 4.0), ("clip", rail_id, side_id)),
        connection("panel_00", (26.825, 3.0, 4.0), ("main_lower_right", side_id)),
    ]
    for axis_id in panel_ids[1:]:
        native_connections.append(connection(axis_id, (1.0, 1.0, 1.0), ("other",)))
        current_connections.append(connection(axis_id, (1.0, 1.0, 1.0), ("other",)))

    native_source = SimpleNamespace(
        connections=lambda: tuple(native_connections),
        service_cutters=lambda: (),
        additional_machining_cutters=lambda: (),
    )
    current_source = SimpleNamespace(
        option=integration.KERF_RIGHT,
        source=native_source,
        connections=lambda: tuple(current_connections),
    )
    inventory = {
        "fixed_panel_kicker_screws": [
            {"axis_id": axis_id, "shop_purchased_length_mm": 63.5}
            for axis_id in panel_ids
        ]
    }

    native_cutters = integration.source_native_cutters_by_host(
        current_source, frozenset({rail_id, side_id})
    )
    purchase_cutters = integration.candidate_panel_purchase_cutters_by_host(
        current_source, inventory, frozenset({rail_id, side_id})
    )
    axis_audit = integration._source_axis_datum_audit(
        current_source,
        frozenset({"shared_old_axis", "panel_00"}),
        frozenset({rail_id, side_id}),
    )

    assert native_cutters[rail_id][
        "shared_old_axis"
    ].BoundingBox().xmin == pytest.approx(19.75)
    assert native_cutters[side_id][
        "shared_old_axis"
    ].BoundingBox().xmin == pytest.approx(16.575)
    assert "panel_purchase/panel_00" not in native_cutters[side_id]
    assert purchase_cutters[side_id][
        "panel_purchase/panel_00"
    ].BoundingBox().zlen == pytest.approx(63.5)
    assert purchase_cutters[rail_id] == {}
    assert axis_audit["shared_old_axis"]["native_start_xyz_mm"][0] == pytest.approx(
        20.0
    )
    assert axis_audit["shared_old_axis"]["current_adapter_start_xyz_mm"][
        0
    ] == pytest.approx(16.825)
    assert axis_audit["shared_old_axis"]["shared_host_native_replay_starts_xyz_mm"][
        rail_id
    ][0] == pytest.approx(20.0)
    assert axis_audit["shared_old_axis"]["shared_host_current_adapter_starts_xyz_mm"][
        rail_id
    ][0] == pytest.approx(16.825)
    assert axis_audit["shared_old_axis"]["shared_host_native_replay_starts_xyz_mm"][
        side_id
    ][0] == pytest.approx(16.825)


def test_cut_record_separates_native_and_purchased_panel_cutters():
    axis = _axis(2.0, 2.0)

    record = integration._cut_record(
        "shared_rail",
        {
            "retained_native_axis": axis,
            "replaced_sds_axis": axis,
            "service/0/fixed_service": axis,
            "panel_purchase/round_panel_1": axis,
        },
        frozenset({"replaced_sds_axis"}),
        {},
        input_part_origin="source_uncut_member",
    )

    assert record["retained_source_cutter_ids"] == [
        "retained_native_axis",
        "service/0/fixed_service",
    ]
    assert record["candidate_panel_purchase_cutter_ids"] == [
        "panel_purchase/round_panel_1"
    ]
    assert record["source_cutter_counts"] == {
        "named_connections": 1,
        "connection_head_cutters": 0,
        "service_cutters": 1,
        "additional_cutters": 0,
        "purchased_panel_screw_cutters": 1,
    }
    assert record["source_cutters_retained"] == 2
    assert record["candidate_panel_purchase_cutters_applied"] == 1
    assert record["input_part_origin"] == "source_uncut_member"
    assert record["cut_union_applied_to_raw_stock"] is True
    assert record["cut_union_applied_to_input_part"] is True

    candidate_cleat = integration._cut_record(
        "candidate_cleat",
        {},
        frozenset(),
        {"candidate/upper_bolt": axis},
        input_part_origin="producer_candidate_cleat",
    )
    assert candidate_cleat["retained_source_cutter_ids"] == []
    assert candidate_cleat["source_stock"] is None
    assert candidate_cleat["input_part_origin"] == "producer_candidate_cleat"
    assert candidate_cleat["cut_union_applied_to_raw_stock"] is False
    assert candidate_cleat["cut_union_applied_to_input_part"] is True


def test_source_reconstruction_preflight_runs_before_joint_family_builders(monkeypatch):
    stations = (
        (
            integration.wj04_g7.LOWER_STATION,
            [integration.wj04_g7.LOWER_RAIL, integration.wj04_g7.PRINCIPAL],
        ),
        (
            integration.wj04_g7.UPPER_STATION,
            [integration.wj04_g7.UPPER_RAIL, integration.wj04_g7.PRINCIPAL],
        ),
        (
            integration.wj06_outer.LOWER_STATION,
            [integration.wj06_outer.LOWER_RAIL, integration.wj06_outer.SIDE_HOST],
        ),
        (
            integration.wj06_outer.UPPER_STATION,
            [integration.wj06_outer.UPPER_RAIL, integration.wj06_outer.SIDE_HOST],
        ),
    )
    inventory_duties = []
    axes = []
    connection_index = 0
    for station_id, hosts in stations:
        duty_axes = []
        for index in range(6):
            axis_id = f"{station_id}_synthetic_sds_{index + 1}"
            host_id = hosts[0] if index < 3 else hosts[1]
            duty_axes.append({"axis_id": axis_id, "shop_opening_kind": "sds_wood"})
            axes.append(
                SimpleNamespace(
                    name=axis_id,
                    kind="screw",
                    members=("legacy_clip", host_id),
                    diameter=0.5,
                    length=8.0,
                    start=cq.Vector(10.0 + connection_index, 10.0, 10.0),
                    direction=cq.Vector(0.0, 0.0, 1.0),
                )
            )
            connection_index += 1
        inventory_duties.append(
            {
                "legacy_station_id": station_id,
                "legacy_host_members": hosts,
                "legacy_sds_axes": duty_axes,
            }
        )

    inventory = {"legacy_duties": inventory_duties}
    binding = SimpleNamespace(
        inventory_sha256=integration.WJ04_TRIAL.source_inventory_sha256
    )
    raw_shapes = {
        host_id: cq.Solid.makeBox(100.0, 100.0, 100.0)
        for host_id in integration.SHARED_HOSTS
    }
    source = SimpleNamespace(
        uncut_wood_parts=lambda: tuple(
            SimpleNamespace(name=name, shape=shape)
            for name, shape in raw_shapes.items()
        ),
        parts=lambda: tuple(
            SimpleNamespace(name=name, shape=shape)
            for name, shape in raw_shapes.items()
        ),
        connections=lambda: tuple(axes),
        service_cutters=lambda: (),
        additional_machining_cutters=lambda: (),
    )
    base_geometry = SimpleNamespace(
        config=SimpleNamespace(
            canonical_sha256=integration.WJ04_TRIAL.canonical_sha256
        ),
        source=source,
        source_binding=binding,
    )
    monkeypatch.setattr(integration, "validate_source_binding", lambda _: binding)
    monkeypatch.setattr(
        integration, "_load_pinned_source_inventory", lambda _: inventory
    )

    def family_builder_must_not_run(*args, **kwargs):
        pytest.fail("family geometry ran before source reconstruction passed")

    monkeypatch.setattr(
        integration.wj04_g7, "materialize_geometry", family_builder_must_not_run
    )
    monkeypatch.setattr(
        integration.wj06_outer, "materialize_geometry", family_builder_must_not_run
    )

    with pytest.raises(ValueError, match="raw-stock retained-cut pass differs"):
        integration.materialize_right_rail_geometry(base_geometry)


def test_retained_sds_protection_uses_occupied_source_axis_extent():
    source_axis = SimpleNamespace(
        name="retained_sds",
        kind="screw",
        diameter=0.5,
        length=10.0,
        start=cq.Vector(2.0, 3.0, 4.0),
        direction=cq.Vector(0.0, 0.0, 2.0),
    )

    occupied = integration._source_screw_axis_shape(source_axis)
    bounds = occupied.BoundingBox()

    assert bounds.zmin == pytest.approx(4.0)
    assert bounds.zmax == pytest.approx(14.0)
    assert occupied.Volume() == pytest.approx(math.pi * 0.25**2 * 10.0)


def test_ordinary_class_maximum_changes_only_wj06_side_shaft_envelope():
    nominal = integration.wj06_outer.build_stacks()["lower_side_1"]
    maximum = integration._ordinary_body_maximum_side_stack(nominal)
    maximum_shaft = maximum.shaft_shape()

    assert integration.ORDINARY_BOLT_BODY_MAXIMUM_IN == 0.260
    assert integration.INCH_TO_MM == 25.4
    assert integration.ORDINARY_BOLT_BODY_MAXIMUM_MM == pytest.approx(6.604)
    assert nominal.hardware.steel_diameter_mm == pytest.approx(6.35)
    assert maximum.hardware.steel_diameter_mm == pytest.approx(6.35)
    assert nominal.hardware.cad_occupied_diameter_mm == pytest.approx(6.35)
    assert maximum.hardware.cad_occupied_diameter_mm == pytest.approx(6.604)
    assert maximum.hardware.drill_diameter_mm == nominal.hardware.drill_diameter_mm
    assert (
        maximum.hardware.under_head_length_mm == nominal.hardware.under_head_length_mm
    )
    assert maximum.head_seat == nominal.head_seat
    assert maximum.nut_seat == nominal.nut_seat
    assert maximum.direction == nominal.direction
    assert maximum_shaft.BoundingBox().ylen == pytest.approx(6.604)


def test_ordinary_body_maximum_document_is_pinned_as_an_input():
    inputs = integration._source_inputs_sha256()

    assert (
        integration.ORDINARY_BODY_MAXIMUM_SOURCE
        == "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md"
    )
    assert len(inputs[integration.ORDINARY_BODY_MAXIMUM_SOURCE]) == 64


def test_pinned_inventory_adapter_uses_lightweight_validated_loader():
    binding = SimpleNamespace(
        inventory_sha256=integration.WJ04_TRIAL.source_inventory_sha256
    )

    inventory = integration._load_pinned_source_inventory(binding)

    assert inventory["candidate"] == integration.wj06_outer.CANDIDATE
    assert len(inventory["legacy_duties"]) == 24
    assert sum(len(row["legacy_sds_axes"]) for row in inventory["legacy_duties"]) == 144
    assert len(inventory["fixed_panel_kicker_screws"]) == 66
    assert len(inventory["starting_frame_bolts"]) == 12


def test_side_shaft_sensitivity_screens_wood_protected_and_installed_geometry():
    source_stacks = integration.wj06_outer.build_stacks()
    by_id = {spec.stack_id: spec for spec in integration.wj06_outer.STACK_SPECS}
    stacks = {
        integration._namespace(
            integration.FAMILY_WJ06,
            integration.wj06_outer.TRIAL_ID,
            stack_id,
        ): stack
        for stack_id, stack in source_stacks.items()
        if by_id[stack_id].interface_id == "cleat_to_side"
    }
    installed = {key: stack.installed_shapes() for key, stack in stacks.items()}
    first_key = min(stacks)
    first_stack = stacks[first_key]
    axis = first_stack.under_head_origin
    direction = first_stack.direction
    offset = cq.Vector(0.0, 0.0, 3.2)
    obstacle_start = axis + offset
    thin_obstacle = cq.Solid.makeCylinder(
        0.01,
        first_stack.hardware.under_head_length_mm,
        obstacle_start,
        direction,
    )
    protected_obstacle = cq.Solid.makeCylinder(
        0.01,
        first_stack.hardware.under_head_length_mm,
        axis + cq.Vector(0.0, 3.2, 0.0),
        direction,
    )
    installed["synthetic_peer_stack"] = {"component_probe": thin_obstacle}

    report = integration._side_shaft_envelope_sensitivity(
        stacks,
        installed,
        {"wood_probe": thin_obstacle},
        {"protected_probe": {"protected_shape": protected_obstacle}},
    )

    nominal = report["scenarios"]["nominal"]["per_stack"][first_key]
    maximum = report["scenarios"]["ordinary_class_maximum"]["per_stack"][first_key]
    assert nominal["finished_wood_hits_mm3"] == {}
    assert maximum["finished_wood_hits_mm3"]["wood_probe"] > 0
    assert maximum["protected_geometry_hits_mm3"]["protected_probe"]
    assert (
        maximum["protected_geometry_hits_mm3"]["protected_probe"]["protected_shape"] > 0
    )
    assert (
        maximum["other_installed_components_hits_mm3"][
            "synthetic_peer_stack/component_probe"
        ]
        > 0
    )
    assert maximum["steel_or_design_diameter_mm"] == pytest.approx(6.35)
    assert maximum["cad_occupied_diameter_mm"] == pytest.approx(6.604)
    assert maximum["drilled_bore_diameter_mm"] == pytest.approx(
        first_stack.hardware.drill_diameter_mm
    )
    assert report["basis"]["delivered_fastener_fit_verified"] is False
    assert report["basis"]["capacity_or_joint_acceptance"] is False
    assert (
        report["scenarios"]["ordinary_class_maximum"]["modeled_overlap_present"] is True
    )


def test_diagnostic_report_is_json_safe_and_keeps_release_gates_closed():
    geometry = SimpleNamespace(
        source_binding=SimpleNamespace(
            inventory_sha256="inventory-hash",
            runtime_module_sha256={},
            uncut_part_shapes_sha256="parts-hash",
            uncut_host_shape_sha256={},
            duty_host_mapping={},
            fixed_screw_axes_sha256="panel-hash",
            frame_bolt_axes_sha256="frame-hash",
        ),
        inventory={"candidate": "trial", "source_commit": "historical-commit"},
        source_inputs_sha256={
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py": "g7-hash",
            "scripts/wood_joint_wj06_outer_pair_probe.py": "wj06-hash",
        },
        trial_ids={},
        duties={},
        parts={"candidate_cleat": cq.Solid.makeBox(1.0, 1.0, 1.0)},
        replaced_source_axis_ids=frozenset(),
        retained_source_axis_shapes={},
        retained_legacy_clip_shapes={},
        protected={},
        source_reconstruction={},
        machining={},
        candidate_body_hits={},
        source_axis_datum_audit={},
        body_solid_checks={
            "candidate_cleat": {
                "valid": True,
                "solid_count": 1,
                "volume_mm3": 1.0,
                "valid_single_positive_volume_solid": True,
            }
        },
        stacks={},
        bores={},
        installed={},
        bore_reports={},
        cross_bore_hits_mm3={},
        washer_support={},
        side_shaft_envelope_sensitivity={"status": "assumption-only"},
        installed_hits={},
        panels={},
        diagnostic_gates={"integrated_clearance_review": "not_run"},
        release={"fabrication_released": False},
    )

    report = integration.diagnostic_report(geometry)
    encoded = json.dumps(report)

    assert '"status": "unaccepted integrated trial geometry"' in encoded
    assert report["candidate_bodies"]["candidate_cleat"][
        "valid_single_positive_volume_solid"
    ]
    assert report["claim_boundary"]["integrated_clearance_accepted"] is False
    assert report["release"]["fabrication_released"] is False
    assert report["side_shaft_envelope_sensitivity"]["status"] == "assumption-only"
