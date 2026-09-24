"""Cheap adapter checks; source CAD materialization stays in parent slot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_probe

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PROBE = ROOT / "docs/wood-joints-mvp/wj04-narrow-3p5in-historical.json"
PRE_ADAPTER_PROBE_SHA256 = (
    "fab6696d6142ba9fe32bd78343c5d0f181e1d25dc8969b9e78dadaab4316b59e"
)


def test_stack_adapter_uses_configured_order_axes_and_catalog_max_envelopes():
    modeled = wood_joint_wj04_probe.build_stacks(WJ04_TRIAL)

    assert set(modeled) == {stack.stack_id for stack in WJ04_TRIAL.stacks}
    for configured in WJ04_TRIAL.stacks:
        stack = modeled[configured.stack_id]
        envelope = configured.cad_envelope
        candidate = configured.hardware_candidate

        assert [(layer.body_id, layer.thickness_mm) for layer in stack.layers] == [
            (layer.member_id, layer.thickness_mm) for layer in configured.layers
        ]
        assert stack.grip_mm == pytest.approx(configured.grip_mm)
        assert stack.hardware.candidate_sku == candidate.sku
        assert stack.hardware.under_head_length_mm == pytest.approx(
            candidate.nominal_length_mm
        )
        assert stack.hardware.steel_diameter_mm == pytest.approx(
            envelope.shaft_diameter_mm
        )
        assert stack.hardware.cad_occupied_diameter_mm == pytest.approx(
            envelope.shaft_diameter_mm
        )
        assert stack.hardware.drill_diameter_mm == pytest.approx(
            envelope.bore_occupancy_diameter_mm
        )
        assert stack.hardware.head_diameter_mm == pytest.approx(
            envelope.head_diameter_mm
        )
        assert stack.hardware.washer_od_mm == pytest.approx(
            WJ04_TRIAL.fasteners.washer.outer_diameter_range_mm[1]
        )
        assert stack.hardware.washer_id_mm == pytest.approx(
            WJ04_TRIAL.fasteners.washer.inner_diameter_range_mm[0]
        )
        assert stack.hardware.washer_thickness_mm == pytest.approx(
            WJ04_TRIAL.fasteners.washer.thickness_range_mm[1]
        )
        assert stack.hardware.nut_height_mm == pytest.approx(
            WJ04_TRIAL.fasteners.nut.thickness_range_mm[1]
        )
        assert stack.head_seat.center.toTuple() == pytest.approx(
            WJ04_TRIAL.axis_point_global(configured.stack_id)
        )
        assert stack.direction.toTuple() == pytest.approx(
            WJ04_TRIAL.axis_direction_global(configured.stack_id)
        )


def test_cheap_adapter_records_bind_trial_catalog_and_release_flags():
    metadata = wood_joint_wj04_probe.trial_adapter_metadata(WJ04_TRIAL)
    rows = metadata["stacks"]

    assert metadata["trial_id"] == WJ04_TRIAL.trial_id
    assert metadata["trial_config_sha256"] == WJ04_TRIAL.canonical_sha256
    assert metadata["source_inventory_sha256"] == WJ04_TRIAL.source_inventory_sha256
    assert metadata["stock"]["section_x_t_n_mm"] == list(WJ04_TRIAL.cleat.size_x_t_n_mm)
    assert metadata["stock"]["grain_axis"] == WJ04_TRIAL.cleat.grain_axis
    assert metadata["catalog_candidate_ids"]["bolts"] == [
        candidate.candidate_id for candidate in WJ04_TRIAL.fasteners.bolts
    ]
    assert set(rows) == {stack.stack_id for stack in WJ04_TRIAL.stacks}
    assert all(
        rows[stack.stack_id]["bolt_sku"] == stack.hardware_candidate.sku
        for stack in WJ04_TRIAL.stacks
    )
    assert json.loads(json.dumps(metadata)) == metadata
    assert not any(metadata["release_claims"].values())


def test_candidate_panel_overlay_preserves_raw_parts_and_all_fixed_axes(monkeypatch):
    axis_count = wood_joint_wj04_probe.PANEL_CONNECTION_COUNT
    panel_axes = tuple(
        SimpleNamespace(
            name=f"panel_axis_{index:02d}",
            members=("main_lower_left", "base_rail_bottom_left"),
            start=cq.Vector(index, 2.0, 3.0),
            direction=cq.Vector(0.0, 0.0, 1.0),
            length=40.0,
            diameter=6.0,
            kind="screw",
        )
        for index in range(axis_count)
    )

    class Source:
        def panel_connections(self):
            return panel_axes

    source = Source()
    panel_names = RIGHT_PANEL_NAMES | {
        "main_lower_left",
        "main_upper_left",
        "kicker_left",
    }
    source_panels = {
        name: cq.Solid.makeBox(5.0, 5.0, 5.0).translate((index * 10.0, 0.0, 0.0))
        for index, name in enumerate(sorted(panel_names))
    }
    original_shapes = source_panels.copy()
    current_parts = tuple(
        SimpleNamespace(name=name, shape=shape) for name, shape in source_panels.items()
    )
    uncut_parts = tuple(
        SimpleNamespace(name=name, shape=shape) for name, shape in source_panels.items()
    )
    replacement_parts = {
        name: SimpleNamespace(
            name=name,
            shape=cq.Solid.makeBox(2.0, 2.0, 2.0).translate((100.0, index, 0.0)),
        )
        for index, name in enumerate(sorted(RIGHT_PANEL_NAMES))
    }
    helper_calls = []

    def replacements(model, *, current_parts, uncut_parts):
        helper_calls.append((model, current_parts, uncut_parts))
        return replacement_parts

    monkeypatch.setattr(
        wood_joint_wj04_probe, "candidate_panel_replacements", replacements
    )

    obstacles, metadata = wood_joint_wj04_probe._candidate_panel_obstacles(
        source, source_panels, current_parts, uncut_parts
    )

    assert helper_calls == [(source, current_parts, uncut_parts)]
    assert obstacles is not source_panels
    assert all(
        obstacles[name] is replacement_parts[name].shape for name in RIGHT_PANEL_NAMES
    )
    assert all(
        obstacles[name] is original_shapes[name]
        for name in panel_names - RIGHT_PANEL_NAMES
    )
    assert all(source_panels[name] is original_shapes[name] for name in panel_names)
    assert metadata["replacement_names"] == sorted(RIGHT_PANEL_NAMES)
    assert metadata["fixed_panel_axis_count"] == 66
    assert len(metadata["fixed_panel_axis_identity_sha256"]) == 64
    assert metadata["fixed_panel_axes_preserved"] is True
    assert metadata["raw_source_panel_shapes_preserved_separately"] is True


def test_candidate_panel_overlay_fails_closed_on_missing_axis_or_replacement(
    monkeypatch,
):
    axis = SimpleNamespace(
        name="single-axis",
        members=("main_lower_left", "base_rail_bottom_left"),
        start=cq.Vector(0.0, 0.0, 0.0),
        direction=cq.Vector(0.0, 0.0, 1.0),
        length=40.0,
        diameter=6.0,
        kind="screw",
    )

    class Source:
        def panel_connections(self):
            return (axis,)

    monkeypatch.setattr(
        wood_joint_wj04_probe,
        "candidate_panel_replacements",
        lambda *args, **kwargs: pytest.fail(
            "invalid axes must fail before remachining"
        ),
    )
    with pytest.raises(ValueError, match="exact unique source panel axes"):
        wood_joint_wj04_probe._candidate_panel_obstacles(Source(), {}, (), ())

    axes = tuple(
        SimpleNamespace(
            name=f"panel_axis_{index:02d}",
            members=("main_lower_left", "base_rail_bottom_left"),
            start=cq.Vector(index, 0.0, 0.0),
            direction=cq.Vector(0.0, 0.0, 1.0),
            length=40.0,
            diameter=6.0,
            kind="screw",
        )
        for index in range(wood_joint_wj04_probe.PANEL_CONNECTION_COUNT)
    )

    class CompleteSource:
        def panel_connections(self):
            return axes

    monkeypatch.setattr(
        wood_joint_wj04_probe,
        "candidate_panel_replacements",
        lambda *args, **kwargs: {
            "main_lower_right": SimpleNamespace(
                name="main_lower_right",
                shape=cq.Solid.makeBox(1.0, 1.0, 1.0),
            )
        },
    )
    with pytest.raises(ValueError, match="replace exactly the three right panels"):
        wood_joint_wj04_probe._candidate_panel_obstacles(
            CompleteSource(),
            {name: cq.Solid.makeBox(1.0, 1.0, 1.0) for name in RIGHT_PANEL_NAMES},
            (),
            (),
        )


def test_pre_adapter_narrow_probe_was_archived_byte_for_byte():
    assert hashlib.sha256(HISTORICAL_PROBE.read_bytes()).hexdigest() == (
        PRE_ADAPTER_PROBE_SHA256
    )


def test_materialized_host_keeps_retained_panel_and_legacy_screw_voids():
    geometry = wood_joint_wj04_probe.materialize_trial_geometry(WJ04_TRIAL)
    inventory = json.loads((ROOT / WJ04_TRIAL.source_inventory_path).read_text())
    member = next(row for row in WJ04_TRIAL.members if row.role == "principal")
    axis = next(
        row
        for row in inventory["fixed_panel_kicker_screws"]
        if row["source_finished_receiver_member"] == member.source_part_id
    )
    connections = {row.name: row for row in geometry.source.connections()}
    source_blank = geometry.wood[member.source_part_id]
    finished_host = geometry.finished[member.member_id]

    panel_connection = connections[axis["axis_id"]]
    retained_panel_hole = cq.Solid.makeCylinder(
        panel_connection.diameter / 2,
        axis["shop_purchased_length_mm"],
        panel_connection.start,
        panel_connection.direction.normalized(),
    )
    retained_duty = next(
        duty
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] != WJ04_TRIAL.station_id
        and member.source_part_id in duty["legacy_host_members"]
    )
    retained_axis = next(
        row
        for row in retained_duty["legacy_sds_axes"]
        if member.source_part_id in row["members"]
    )
    retained_connection = connections[retained_axis["axis_id"]]
    retained_legacy_hole = cq.Solid.makeCylinder(
        retained_connection.diameter / 2,
        retained_connection.length + 2.0,
        retained_connection.start - retained_connection.direction.normalized(),
        retained_connection.direction.normalized(),
    )
    replaced_duty = next(
        duty
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] == WJ04_TRIAL.station_id
    )
    allowed_restore_domains = []
    for replaced_axis in replaced_duty["legacy_sds_axes"]:
        if member.source_part_id not in replaced_axis["members"]:
            continue
        connection = connections[replaced_axis["axis_id"]]
        direction = connection.direction.normalized()
        allowed_restore_domains.append(
            source_blank.intersect(
                cq.Solid.makeCylinder(
                    connection.diameter / 2,
                    connection.length + 2.0,
                    connection.start - direction,
                    direction,
                )
            )
        )
    allowed_restore = (
        allowed_restore_domains[0].fuse(*allowed_restore_domains[1:]).clean()
    )
    original_finished_host = next(
        row.shape
        for row in geometry.source.parts()
        if row.name == member.source_part_id
    )
    restored_material = (
        geometry.parts[member.member_id].cut(original_finished_host).clean()
    )
    restored_outside_replaced_axes = restored_material.cut(allowed_restore).clean()

    for cutter in (retained_panel_hole, retained_legacy_hole):
        assert source_blank.intersect(cutter).Volume() > 1.0
        assert finished_host.intersect(cutter).Volume() == pytest.approx(0.0, abs=1e-4)
    assert restored_outside_replaced_axes.Volume() == pytest.approx(0.0, abs=1e-4)
