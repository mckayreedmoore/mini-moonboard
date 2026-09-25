import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_top_outer_integration as top_outer
from scripts import wood_joint_wj16_compositor as wj16
from scripts import wood_joint_wj16_diagnostic as wj16_diagnostic
from scripts import wood_joint_wj18_compositor as wj18
from scripts import wood_joint_wj18_diagnostic as wj18_diagnostic

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / wj18.INVENTORY_PATH


def _sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _box():
    return cq.Solid.makeBox(2.0, 2.0, 2.0, cq.Vector(0, 0, 0))


def _synthetic_inputs():
    inventory = json.loads(INVENTORY_PATH.read_text())
    binding = SimpleNamespace(
        inventory_sha256=_sha(wj18.INVENTORY_PATH),
        runtime_module_sha256={},
    )
    shape = _box()
    host_ids = set(wj18.EXPECTED_SOURCE_HOST_IDS)
    source_shape_ids = host_ids | set(wj18.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)

    native_all = {host: {} for host in source_shape_ids}
    for duty in inventory["legacy_duties"]:
        for axis in duty["legacy_sds_axes"]:
            if axis.get("shop_opening_kind") != "sds_wood":
                continue
            host = axis["members"][1]
            if host in native_all:
                native_all[host][axis["axis_id"]] = shape
    for row in inventory["fixed_panel_kicker_screws"]:
        host = row["source_finished_receiver_member"]
        if host in native_all:
            native_all[host][row["axis_id"]] = shape

    purchase_all = {host: {} for host in source_shape_ids}
    for row in inventory["fixed_panel_kicker_screws"]:
        source_host = row["source_finished_receiver_member"]
        if (
            source_host in purchase_all
            and row["candidate_finished_receiver_member"] == source_host
        ):
            purchase_all[source_host][f"panel_purchase/{row['axis_id']}"] = shape

    redirected_rows = {
        row["axis_id"]: (
            row["source_finished_receiver_member"],
            row["candidate_finished_receiver_member"],
        )
        for row in inventory["fixed_panel_kicker_screws"]
        if row["candidate_finished_receiver_member"]
        != row["source_finished_receiver_member"]
    }
    assert len(redirected_rows) == 4
    wj16_native = {host: dict(native_all[host]) for host in wj16.EXPECTED_SOURCE_HOST_IDS}
    wj16_purchase = {
        host: dict(purchase_all[host]) for host in wj16.EXPECTED_SOURCE_HOST_IDS
    }
    wj16_applied = {
        host: {**wj16_native[host], **wj16_purchase[host]}
        for host in wj16.EXPECTED_SOURCE_HOST_IDS
    }
    for axis_id, (source_host, _) in redirected_rows.items():
        if source_host in wj16_applied:
            wj16_applied[source_host].pop(axis_id, None)
            wj16_applied[source_host].pop(f"panel_purchase/{axis_id}", None)

    all_axis_ids = {
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        for axis in duty["legacy_sds_axes"]
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    wj16_replaced = frozenset(
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] in wj16.EXPECTED_TARGET_DUTY_IDS
        for axis in duty["legacy_sds_axes"]
        if axis.get("shop_opening_kind") == "sds_wood"
    )
    duty_ids = {row["legacy_station_id"] for row in inventory["legacy_duties"]}
    retained_duties = duty_ids - wj16.EXPECTED_TARGET_DUTY_IDS
    retained_axes = {
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] in retained_duties
        for axis in duty["legacy_sds_axes"]
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    assert len(retained_duties) == 8
    assert len(all_axis_ids - wj16_replaced) == 48

    hash_inputs = {
        path: _sha(path)
        for _, path in wj16_diagnostic.WJ16_LAYOUT.family_producer_paths
    }
    for _, path in wj16_diagnostic.WJ16_LAYOUT.extra_producer_hash_paths:
        hash_inputs[path] = _sha(path)
    hash_inputs[wj18.INVENTORY_PATH] = _sha(wj18.INVENTORY_PATH)
    family_fingerprints = {"retained_wj16": hash_inputs}
    family_trials = {"retained_wj16_family": "retained-trial"}

    candidate_parts = {part: shape for part in wj16.EXPECTED_CANDIDATE_PART_IDS}
    expected_left_station_ids = dict(
        wj16_diagnostic.WJ16_LAYOUT.expected_candidate_axis_station_ids
    )
    candidate_bores = {}
    candidate_hardware = {}
    for axis_id in wj16.EXPECTED_CANDIDATE_AXIS_IDS:
        station = expected_left_station_ids.get(axis_id)
        receiver_part = next(iter(wj16.EXPECTED_CANDIDATE_PART_IDS))
        receiver_host = next(iter(wj16.EXPECTED_SOURCE_HOST_IDS))
        candidate_bores[axis_id] = SimpleNamespace(
            axis_id=axis_id,
            family="retained_wj16",
            trial_id="retained-wj16-family",
            station_id=station,
            receiver_ids=(receiver_part, receiver_host),
            shape=shape,
        )
        roles = (
            {"shaft", "bottom_washer", "bottom_head", "top_washer", "top_nut"}
            if axis_id.startswith("backer_header_")
            else {"shaft", "head", "head_washer", "nut_washer", "nut"}
        )
        candidate_hardware[axis_id] = {role: shape for role in roles}

    frame_ids = [row["axis_id"] for row in inventory["starting_frame_bolts"]]
    frame_shapes = {
        f"{axis_id}/installed_component_{index}": shape
        for axis_id in frame_ids
        for index in range(1, 6)
    }
    frame_shapes.update({f"{axis_id}/source_occupied_axis": shape for axis_id in frame_ids})
    retained_clips = {duty: shape for duty in retained_duties}
    retained_legacy_axes = {axis_id: shape for axis_id in retained_axes}
    fixed_axes = {
        row["axis_id"]: shape for row in inventory["fixed_panel_kicker_screws"]
    }
    frame_aliases = {
        f"{axis_id}/{role}": shape
        for axis_id in frame_ids
        for role in ("shaft", "head_washer", "nut_washer", "head", "nut")
    }
    protected = {
        "fixed_66_hillman_axes_63p5mm": fixed_axes,
        "retained_12_frame_bolt_components": frame_aliases,
        "retained_12_frame_bolt_tools_withdrawals": {
            f"tool_{index}": shape for index in range(36)
        },
        "retained_legacy_clips": retained_clips,
        "retained_legacy_sds_axes": retained_legacy_axes,
        "tnuts": {f"tnut_{index}": shape for index in range(142)},
        "hold_hole_and_provisional_projection": {
            f"hold_{index}": shape for index in range(142)
        },
        "lights": {f"light_{index}": shape for index in range(132)},
        "wires": {f"wire_{index}": shape for index in range(131)},
    }
    frame_records = tuple(
        {"axis_id": axis_id, "installed_component_count": 5}
        for axis_id in frame_ids
    )

    overlay_ids = tuple(wj18.EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
    overlay_purchase = {
        host: {
            cut_id: shape
            for cut_id, shape in purchase_all[host].items()
        }
        for host in (*overlay_ids, "base_rail_top")
    }
    source_reconstruction = {
        host: {
            "matches_source_finished_member": True,
            "symmetric_difference_mm3": 0.0,
        }
        for host in wj16.EXPECTED_SOURCE_HOST_IDS
    }
    source_parts = {host: shape for host in host_ids}
    source = SimpleNamespace(
        uncut_wood_parts=lambda: [
            SimpleNamespace(name=name, shape=value)
            for name, value in source_parts.items()
        ]
    )
    g16 = SimpleNamespace(
        layout_id=wj16.LAYOUT_ID,
        trial_id=wj16.TRIAL_ID,
        status="unaccepted_integrated_hypothesis",
        source=source,
        source_binding=binding,
        source_inventory_sha256=binding.inventory_sha256,
        source_inventory=inventory,
        family_source_fingerprints=family_fingerprints,
        family_trial_ids=family_trials,
        target_station_ids=tuple(sorted(wj16.EXPECTED_TARGET_DUTY_IDS)),
        raw_hosts={host: shape for host in wj16.EXPECTED_SOURCE_HOST_IDS},
        finished_hosts={host: shape for host in wj16.EXPECTED_SOURCE_HOST_IDS},
        raw_candidate_parts=candidate_parts,
        finished_candidate_parts=dict(candidate_parts),
        candidate_bores=candidate_bores,
        candidate_installed_hardware=candidate_hardware,
        replaced_source_axis_ids=wj16_replaced,
        replaced_source_cutter_ids=wj16_replaced,
        source_cutters_by_host=wj16_native,
        applied_source_cutters_by_host=wj16_applied,
        purchased_panel_cutters_by_host=wj16_purchase,
        purchased_panel_cutters_by_candidate_part={
            part: {axis_id: shape for axis_id in cuts}
            for part, cuts in _redirected_candidate_cuts(inventory, shape).items()
        },
        additional_finished_source_parts={host: shape for host in overlay_ids + ("base_rail_top",)},
        additional_purchased_panel_cutters_by_host=overlay_purchase,
        additional_source_reconstruction={
            host: {"matches_source_plus_purchase_cuts": True}
            for host in overlay_purchase
        },
        source_reconstruction=source_reconstruction,
        panel_replacements={
            name: shape for name in ("main_lower_right", "main_upper_right", "kicker_right")
        },
        fixed_axes=fixed_axes,
        frame_bolt_records=frame_records,
        frame_bolt_shapes=frame_shapes,
        protected=protected,
        absorbed_source_overlay_ids=(
            "base_rail_service_lower_left",
            "base_rail_service_upper_left",
        ),
    )

    top_bores = {}
    top_hardware = {}
    for axis_id, station_id in wj18.TOP_AXIS_STATION_IDS.items():
        receiver = "base_rail_top" if "/rail_" in axis_id else (
            "base_side_left" if station_id.endswith("left_1") else "base_side_right"
        )
        cleat = top_outer.CLEAT_IDS[station_id]
        top_bores[axis_id] = SimpleNamespace(
            axis_id=axis_id,
            family="top_outer",
            trial_id=top_outer.TRIAL_ID,
            station_id=station_id,
            receiver_ids=(cleat, receiver),
            shape=shape,
        )
        top_hardware[axis_id] = {
            role: shape for role in top_outer.ORDINARY_COMPONENT_ROLES
        }
    top_inputs = {
        label: _sha(path)
        for label, path in top_outer.PRODUCER_HASH_PATHS.items()
    }
    top_geometry = SimpleNamespace(
        source=source,
        source_binding=binding,
        source_inventory=inventory,
        source_inputs_sha256=top_inputs,
        family_source_fingerprints=family_fingerprints,
        family_trial_ids=family_trials,
        context_variant="wj16",
        retained_candidate_axis_ids=frozenset(candidate_bores),
        retained_target_duty_ids=frozenset(wj16.EXPECTED_TARGET_DUTY_IDS),
        trial_id=top_outer.TRIAL_ID,
        duties={
            duty: inventory_duty(inventory, duty)
            for duty in top_outer.TARGET_DUTY_IDS
        },
        raw_candidate_parts={part: shape for part in top_outer.CLEAT_IDS.values()},
        finished_candidate_parts={part: shape for part in top_outer.CLEAT_IDS.values()},
        candidate_bores=top_bores,
        candidate_installed_hardware=top_hardware,
        source_native_cutters_by_host={
            host: dict(native_all[host]) for host in top_outer.HOST_IDS
        },
        source_panel_purchase_cutters_by_host={
            host: dict(purchase_all[host]) for host in top_outer.HOST_IDS
        },
        candidate_panel_purchase_cutters_by_part={
            part: {} for part in top_outer.CLEAT_IDS.values()
        },
        replaced_source_axis_ids=wj18._expected_source_axes(
            inventory, top_outer.TARGET_DUTY_IDS
        ),
        source_reconstruction={
            host: {
                "matches_canonical_source_finished_member": True,
                "symmetric_difference_mm3": 0.0,
            }
            for host in top_outer.HOST_IDS
        },
    )
    return inventory, source, binding, g16, top_geometry, shape


def inventory_duty(inventory, duty_id):
    return next(
        row for row in inventory["legacy_duties"] if row["legacy_station_id"] == duty_id
    )


def _redirected_candidate_cuts(inventory, shape):
    result = {}
    for row in inventory["fixed_panel_kicker_screws"]:
        receiver = row["candidate_finished_receiver_member"]
        if receiver == row["source_finished_receiver_member"]:
            continue
        result.setdefault(receiver, {})[row["axis_id"]] = shape
    return result


def _install_composition_stubs(monkeypatch, binding, source):
    calls = {}
    monkeypatch.setattr(wj18, "validate_source_binding", lambda actual: binding)
    monkeypatch.setattr(
        wj18.wj12,
        "_inventory_matches_source_binding",
        lambda inventory, actual_binding: None,
    )
    monkeypatch.setattr(
        wj18.wj12,
        "_source_parts",
        lambda actual_source, method: {
            item.name: item.shape for item in source.uncut_wood_parts()
        },
    )

    def machine(raw_hosts, cutters, *, replaced_source_axis_ids, candidate_bores_by_host):
        calls["raw_host_ids"] = set(raw_hosts)
        calls["applied_source_cutters"] = cutters
        calls["replaced_source_cutter_ids"] = set(replaced_source_axis_ids)
        calls["candidate_bores_by_host"] = candidate_bores_by_host
        return dict(raw_hosts)

    monkeypatch.setattr(wj18.right_integration, "machine_shared_hosts", machine)
    return calls


def test_wj18_merges_top_overlay_and_eighty_axes_without_losing_wj16_sources(monkeypatch):
    inventory, source, binding, g16, top_geometry, _ = _synthetic_inputs()
    calls = _install_composition_stubs(monkeypatch, binding, source)

    geometry = wj18.compose_wj18_geometry(g16, top_geometry)

    assert geometry.counts["target_duties"] == 18
    assert geometry.counts["source_hosts"] == 14
    assert geometry.counts["candidate_parts"] == 22
    assert geometry.counts["candidate_bores"] == 80
    assert geometry.counts["candidate_installed_hardware_components"] == 400
    assert geometry.counts["replaced_source_sds_axes"] == 108
    assert geometry.counts["retained_legacy_clips"] == 6
    assert geometry.counts["retained_legacy_sds_axes"] == 36
    assert set(geometry.finished_hosts) == wj18.EXPECTED_SOURCE_HOST_IDS
    assert "base_rail_top" in geometry.finished_hosts
    assert "base_rail_top" not in geometry.additional_finished_source_parts
    assert set(geometry.additional_finished_source_parts) == {
        "base_rail_bottom_left",
        "base_rail_bottom_right",
    }
    assert sum(map(len, geometry.additional_purchased_panel_cutters_by_host.values())) == 4
    assert len(geometry.purchased_panel_cutters_by_host["base_rail_top"]) == 4
    assert set(geometry.source_cutters_by_host["base_rail_top"]) == set(
        top_geometry.source_native_cutters_by_host["base_rail_top"]
    )
    assert set(geometry.purchased_panel_cutters_by_candidate_part) == {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    }
    assert geometry.absorbed_source_overlay_ids == (
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
        "base_rail_top",
    )
    assert calls["raw_host_ids"] == set(wj18.EXPECTED_SOURCE_HOST_IDS)
    assert len(calls["replaced_source_cutter_ids"]) == 108
    assert len(calls["candidate_bores_by_host"]["base_rail_top"]) == 4
    assert len(geometry.fixed_axes) == 66
    assert len(geometry.frame_bolt_records) == 12
    assert len(geometry.frame_bolt_shapes) == 72
    assert geometry.gates["complete_joint_acceptance"] is False
    assert geometry.gates["fabrication_released"] is False
    assert geometry.source_inventory["source_commit"] == inventory["source_commit"]


def test_wj18_rejects_missing_top_axis_before_host_composition(monkeypatch):
    _, source, binding, g16, top_geometry, _ = _synthetic_inputs()
    top_geometry.candidate_bores.pop(next(iter(top_geometry.candidate_bores)))
    calls = _install_composition_stubs(monkeypatch, binding, source)

    with pytest.raises(ValueError, match="exact 8-axis contract"):
        wj18.compose_wj18_geometry(g16, top_geometry)

    assert "raw_host_ids" not in calls


def test_wj18_rejects_top_purchase_overlay_mismatch(monkeypatch):
    _, source, binding, g16, top_geometry, _ = _synthetic_inputs()
    top_geometry.source_panel_purchase_cutters_by_host["base_rail_top"].pop(
        next(iter(top_geometry.source_panel_purchase_cutters_by_host["base_rail_top"]))
    )
    calls = _install_composition_stubs(monkeypatch, binding, source)

    with pytest.raises(ValueError, match="absorbed top-rail purchase overlay IDs differ"):
        wj18.compose_wj18_geometry(g16, top_geometry)

    assert "raw_host_ids" not in calls


def test_wj18_layout_and_diagnostic_keep_release_flags_false(monkeypatch):
    geometry = SimpleNamespace(
        layout_id=wj18.LAYOUT_ID,
        trial_id=wj18.TRIAL_ID,
        composition_checks={"top_rail_purchase_overlay_absorbed_into_host_map": True},
        absorbed_source_overlay_ids=("base_rail_top",),
        finished_hosts={"base_rail_top": _box()},
        additional_finished_source_parts={"base_rail_bottom_left": _box()},
        purchased_panel_cutters_by_host={"base_rail_top": {"axis": _box()}},
    )
    seen = {}

    def shared_report(actual, *, tolerance_mm3, layout):
        seen["layout"] = layout
        return {
            "claim_boundary": {},
            "release": {"candidate_accepted": True},
            "diagnostic_gates": {},
        }

    monkeypatch.setattr(wj18_diagnostic.shared_diagnostic, "build_diagnostic_report", shared_report)
    report = wj18_diagnostic.build_wj18_diagnostic_report(geometry)

    assert seen["layout"] is wj18_diagnostic.WJ18_LAYOUT
    assert len(wj18_diagnostic.WJ18_LAYOUT.expected_target_duty_ids) == 18
    assert len(wj18_diagnostic.WJ18_LAYOUT.expected_source_host_ids) == 14
    assert len(wj18_diagnostic.WJ18_LAYOUT.expected_candidate_axis_ids) == 80
    assert len(wj18_diagnostic.WJ18_LAYOUT.expected_candidate_part_ids) == 22
    assert wj18_diagnostic.WJ18_LAYOUT.expected_candidate_installed_component_count == 400
    assert wj18_diagnostic.WJ18_LAYOUT.expected_replaced_source_axis_count == 108
    assert dict(wj18_diagnostic.WJ18_LAYOUT.expected_additional_overlay_axis_counts) == {
        "base_rail_bottom_left": 2,
        "base_rail_bottom_right": 2,
    }
    assert report["integration_contract"]["top_rail_purchase_overlay_is_a_regular_shared_host"][
        "purchase_cut_count"
    ] == 1
    assert all(value is False for value in report["release"].values())
