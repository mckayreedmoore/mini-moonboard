from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj16_compositor as compositor
from scripts.wood_joint_wj12_diagnostic import (
    WJ12_LAYOUT,
    _layout_identity_checks,
)
from scripts.wood_joint_wj16_compositor import _protected_map
from scripts.wood_joint_wj16_diagnostic import WJ16_LAYOUT

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads(
    (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
)


def _layout_geometry(layout):
    duty_rows = {row["legacy_station_id"]: row for row in INVENTORY["legacy_duties"]}
    retained_duty_ids = set(duty_rows) - set(layout.expected_target_duty_ids)
    replaced_axis_ids = {
        axis["axis_id"]
        for station_id in layout.expected_target_duty_ids
        for axis in duty_rows[station_id]["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    retained_axis_ids = {
        axis["axis_id"]
        for station_id in retained_duty_ids
        for axis in duty_rows[station_id]["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    axis_stations = dict(layout.expected_candidate_axis_station_ids)
    axis_ids = set(layout.expected_candidate_axis_ids)
    panel_rows = INVENTORY["fixed_panel_kicker_screws"]
    overlay_cutters = {
        host_id: {
            f"panel_purchase/{row['axis_id']}": object()
            for row in panel_rows
            if row["source_finished_receiver_member"] == host_id
            and row["candidate_finished_receiver_member"] == host_id
        }
        for host_id, _count in layout.expected_additional_overlay_axis_counts
    }
    frame_ids = {row["axis_id"] for row in INVENTORY["starting_frame_bolts"]}
    frame_shapes = {
        f"{axis_id}/installed_component_{index}": object()
        for axis_id in frame_ids
        for index in range(1, 6)
    }
    frame_shapes.update(
        {f"{axis_id}/source_occupied_axis": object() for axis_id in frame_ids}
    )
    component_count_per_axis = (
        layout.expected_candidate_installed_component_count // len(axis_ids)
    )
    return SimpleNamespace(
        layout_id=layout.layout_id,
        trial_id=layout.trial_id,
        source_inventory=INVENTORY,
        target_station_ids=tuple(sorted(layout.expected_target_duty_ids)),
        raw_hosts={host_id: object() for host_id in layout.expected_source_host_ids},
        finished_hosts={
            host_id: object() for host_id in layout.expected_source_host_ids
        },
        raw_candidate_parts={
            part_id: object() for part_id in layout.expected_candidate_part_ids
        },
        finished_candidate_parts={
            part_id: object() for part_id in layout.expected_candidate_part_ids
        },
        candidate_bores={
            axis_id: SimpleNamespace(station_id=axis_stations.get(axis_id))
            for axis_id in axis_ids
        },
        candidate_installed_hardware={
            axis_id: {
                f"role_{index}": object() for index in range(component_count_per_axis)
            }
            for axis_id in axis_ids
        },
        replaced_source_axis_ids=frozenset(replaced_axis_ids),
        source_reconstruction={
            host_id: {"matches_source_finished_member": True}
            for host_id in layout.expected_source_host_ids
        },
        protected={
            "retained_legacy_clips": {
                duty_id: object() for duty_id in retained_duty_ids
            },
            "retained_legacy_sds_axes": {
                axis_id: object() for axis_id in retained_axis_ids
            },
        },
        additional_finished_source_parts={
            host_id: object()
            for host_id, _count in layout.expected_additional_overlay_axis_counts
        },
        additional_purchased_panel_cutters_by_host=overlay_cutters,
        fixed_axes={row["axis_id"]: object() for row in panel_rows},
        frame_bolt_records=tuple({"axis_id": axis_id} for axis_id in frame_ids),
        frame_bolt_shapes=frame_shapes,
    )


def test_wj16_contract_has_exact_sixteen_duties_hosts_axes_and_parts():
    assert len(compositor.EXPECTED_TARGET_DUTY_IDS) == 16
    assert len(compositor.EXPECTED_SOURCE_HOST_IDS) == 13
    assert len(compositor.EXPECTED_CANDIDATE_AXIS_IDS) == 72
    assert len(compositor.EXPECTED_CANDIDATE_PART_IDS) == 20
    assert compositor.EXPECTED_SOURCE_HOST_IDS - set(
        WJ12_LAYOUT.expected_source_host_ids
    ) == {
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
    }


def test_left_candidate_axes_map_exactly_four_stack_ids_to_each_duty():
    assert len(compositor.LEFT_AXIS_STATION_IDS) == 16
    assert set(compositor.LEFT_AXIS_STATION_IDS.values()) == compositor.LEFT_DUTY_IDS
    assert {
        duty_id: {
            axis_id
            for axis_id, station_id in compositor.LEFT_AXIS_STATION_IDS.items()
            if station_id == duty_id
        }
        for duty_id in compositor.LEFT_DUTY_IDS
    } == {
        "clip_horizontal_lower_left_2": {
            f"left_service/{compositor.LEFT_SERVICE_TRIAL_ID}/clip_horizontal_lower_left_2/{stack}"
            for stack in (
                "lower_rail_1",
                "lower_rail_2",
                "lower_principal_1",
                "lower_principal_2",
            )
        },
        "clip_horizontal_upper_left_2": {
            f"left_service/{compositor.LEFT_SERVICE_TRIAL_ID}/clip_horizontal_upper_left_2/{stack}"
            for stack in (
                "upper_rail_1",
                "upper_rail_2",
                "upper_principal_1",
                "upper_principal_2",
            )
        },
        "clip_horizontal_lower_left_1": {
            f"left_service/{compositor.LEFT_SERVICE_TRIAL_ID}/clip_horizontal_lower_left_1/{stack}"
            for stack in (
                "lower_rail_1",
                "lower_rail_2",
                "lower_side_1",
                "lower_side_2",
            )
        },
        "clip_horizontal_upper_left_1": {
            f"left_service/{compositor.LEFT_SERVICE_TRIAL_ID}/clip_horizontal_upper_left_1/{stack}"
            for stack in (
                "upper_rail_1",
                "upper_rail_2",
                "upper_side_1",
                "upper_side_2",
            )
        },
    }


def test_source_inventory_resolves_exact_wj16_axes_and_host_union():
    replaced = compositor.expected_replaced_source_axes(
        INVENTORY, compositor.EXPECTED_TARGET_DUTY_IDS
    )
    hosts = compositor.expected_source_hosts(
        INVENTORY, compositor.EXPECTED_TARGET_DUTY_IDS
    )

    assert len(replaced) == 96
    assert hosts == compositor.EXPECTED_SOURCE_HOST_IDS


def _frame_protection_fixture():
    axis_ids = [row["axis_id"] for row in INVENTORY["starting_frame_bolts"]]
    roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    installed = {}
    aliases = {}
    for bolt_index, axis_id in enumerate(axis_ids):
        role_shapes = []
        for component_index in range(1, 6):
            shape = cq.Solid.makeBox(
                1.0 + component_index * 0.01,
                1.0,
                1.0,
                cq.Vector(bolt_index * 20.0, component_index * 2.0, 0.0),
            )
            installed[f"{axis_id}/installed_component_{component_index}"] = shape
            role_shapes.append(shape)
        aliases.update(
            {
                f"{axis_id}/{role}": shape
                for role, shape in zip(roles, role_shapes, strict=True)
            }
        )
    source_axes = {
        f"{axis_id}/source_occupied_axis": cq.Solid.makeBox(
            0.5, 0.5, 0.5, cq.Vector(index * 20.0, 0.0, 0.0)
        )
        for index, axis_id in enumerate(axis_ids)
    }
    retained_duty_ids = {
        row["legacy_station_id"] for row in INVENTORY["legacy_duties"]
    } - compositor.EXPECTED_TARGET_DUTY_IDS
    retained_sds_ids = {
        axis["axis_id"]
        for row in INVENTORY["legacy_duties"]
        if row["legacy_station_id"] in retained_duty_ids
        for axis in row["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    left = SimpleNamespace(
        inventory=INVENTORY,
        protected={
            "fixed_66_hillman_axes_63p5mm": {
                f"panel_axis_{index}": object() for index in range(66)
            },
            "retained_12_frame_bolt_components": aliases,
            "retained_12_frame_bolt_tools_withdrawals": {
                f"withdrawal_{index}": object() for index in range(36)
            },
            "retained_legacy_clips": {},
            "retained_legacy_sds_axes": {},
        },
    )
    return left, installed | source_axes, retained_duty_ids, retained_sds_ids


def test_protected_frame_bolt_aliases_match_installed_shapes_per_bolt():
    left, frame_shapes, retained_duties, retained_sds = _frame_protection_fixture()

    result = _protected_map(
        left,
        {axis_id: object() for axis_id in retained_duties},
        {axis_id: object() for axis_id in retained_sds},
        frame_shapes,
    )

    assert len(result["retained_12_frame_bolt_components"]) == 60


def test_protected_frame_bolt_alias_swap_between_bolts_is_rejected():
    left, frame_shapes, retained_duties, retained_sds = _frame_protection_fixture()
    axis_ids = sorted(row["axis_id"] for row in INVENTORY["starting_frame_bolts"])
    first, second = axis_ids[:2]
    aliases = left.protected["retained_12_frame_bolt_components"]
    aliases[f"{first}/shaft"], aliases[f"{second}/shaft"] = (
        aliases[f"{second}/shaft"],
        aliases[f"{first}/shaft"],
    )

    with pytest.raises(ValueError, match=f"{first}: protected frame-bolt aliases"):
        _protected_map(
            left,
            {axis_id: object() for axis_id in retained_duties},
            {axis_id: object() for axis_id in retained_sds},
            frame_shapes,
        )


def _left_axis_fixture():
    return {
        axis_id: SimpleNamespace(station_id=station_id)
        for axis_id, station_id in compositor.LEFT_AXIS_STATION_IDS.items()
    }


def test_candidate_axis_merge_accepts_exact_wj12_plus_left_maps():
    base = {
        axis_id: object()
        for axis_id in WJ16_LAYOUT.expected_candidate_axis_ids
        if axis_id not in compositor.EXPECTED_LEFT_CANDIDATE_AXIS_IDS
    }
    merged = compositor._merge_candidate_axis_maps(base, _left_axis_fixture())

    assert set(merged) == compositor.EXPECTED_CANDIDATE_AXIS_IDS


@pytest.mark.parametrize(
    ("defect", "message"),
    [
        ("missing", "exact sixteen-axis contract"),
        ("extra", "exact sixteen-axis contract"),
        ("wrong_station", "assigned to the wrong left duty"),
    ],
)
def test_candidate_axis_merge_rejects_missing_extra_wrong_and_duplicate_ids(
    defect, message
):
    base = {
        axis_id: object()
        for axis_id in WJ16_LAYOUT.expected_candidate_axis_ids
        if axis_id not in compositor.EXPECTED_LEFT_CANDIDATE_AXIS_IDS
    }
    left_axes = _left_axis_fixture()
    if defect == "missing":
        left_axes.pop(next(iter(left_axes)))
    elif defect == "extra":
        left_axes["left_service/extra_axis"] = SimpleNamespace(
            station_id="clip_horizontal_lower_left_1"
        )
    elif defect == "wrong_station":
        axis_id = next(iter(left_axes))
        left_axes[axis_id] = SimpleNamespace(station_id="wrong-duty")

    with pytest.raises(ValueError, match=message):
        compositor._merge_candidate_axis_maps(base, left_axes)


def test_fixed_wj16_layout_identity_contract_passes_exact_inventory_fixture():
    checks = _layout_identity_checks(_layout_geometry(WJ16_LAYOUT), WJ16_LAYOUT)

    assert checks["all_exact_sets_match"] is True


@pytest.mark.parametrize(
    ("defect", "identity_key"),
    [
        ("candidate_axis_missing", "candidate_axis_ids"),
        ("candidate_axis_extra", "candidate_axis_ids"),
        ("host_missing", "shared_source_host_ids"),
        ("host_extra", "shared_source_host_ids"),
        ("clip_missing", "retained_legacy_clip_ids"),
        ("clip_extra", "retained_legacy_clip_ids"),
        ("sds_missing", "retained_legacy_sds_axis_ids"),
        ("sds_extra", "retained_legacy_sds_axis_ids"),
    ],
)
def test_fixed_wj16_layout_identity_contract_rejects_missing_or_extra_ids(
    defect, identity_key
):
    geometry = _layout_geometry(WJ16_LAYOUT)
    if defect == "candidate_axis_missing":
        geometry.candidate_bores.pop(next(iter(geometry.candidate_bores)))
    elif defect == "candidate_axis_extra":
        geometry.candidate_bores["unexpected_axis"] = SimpleNamespace(station_id=None)
    elif defect == "host_missing":
        geometry.finished_hosts.pop(next(iter(geometry.finished_hosts)))
    elif defect == "host_extra":
        geometry.raw_hosts["unexpected_host"] = object()
        geometry.finished_hosts["unexpected_host"] = object()
    elif defect == "clip_missing":
        geometry.protected["retained_legacy_clips"].pop(
            next(iter(geometry.protected["retained_legacy_clips"]))
        )
    elif defect == "clip_extra":
        geometry.protected["retained_legacy_clips"]["unexpected_clip"] = object()
    elif defect == "sds_missing":
        geometry.protected["retained_legacy_sds_axes"].pop(
            next(iter(geometry.protected["retained_legacy_sds_axes"]))
        )
    else:
        geometry.protected["retained_legacy_sds_axes"]["unexpected_sds"] = object()

    checks = _layout_identity_checks(geometry, WJ16_LAYOUT)

    assert checks["exact_sets_match"][identity_key] is False
    assert checks["all_exact_sets_match"] is False


def test_panel_surface_reconciles_three_replacements_with_six_panel_scene():
    right_ids = sorted(compositor.RIGHT_PANEL_NAMES)
    left_ids = [name.removesuffix("_right") + "_left" for name in right_ids]
    panels = {
        name: cq.Solid.makeBox(1, 2, 3, cq.Vector(index * 4, 0, 0))
        for index, name in enumerate(right_ids + left_ids)
    }
    replacements = {name: panels[name] for name in right_ids}
    source = {name: panels[name] for name in left_ids}
    compositor._validate_panel_surface(replacements, panels, source)
    with pytest.raises(ValueError, match="exact six panels"):
        compositor._validate_panel_surface(replacements, replacements, source)
    changed = dict(panels)
    changed[left_ids[0]] = changed[left_ids[0]].translate(cq.Vector(0, 1, 0))
    with pytest.raises(ValueError):
        compositor._validate_panel_surface(replacements, changed, source)
