from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj24_compositor as compositor
from scripts import wood_joint_wj24_hardware_inventory as inventory_report

ROOT = Path(__file__).resolve().parents[1]


def _source_inventory() -> dict:
    return json.loads((ROOT / inventory_report.INVENTORY_PATH).read_text())


def _geometry() -> SimpleNamespace:
    inventory = _source_inventory()
    inventory_hash = hashlib.sha256(
        (ROOT / inventory_report.INVENTORY_PATH).read_bytes()
    ).hexdigest()
    shape = cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0))
    axis_ids = sorted(compositor.EXPECTED_CANDIDATE_AXIS_IDS)
    part_ids = sorted(compositor.EXPECTED_CANDIDATE_PART_IDS)
    family_by_axis = {
        axis_id: inventory_report._family_for_axis_id(axis_id) for axis_id in axis_ids
    }
    family_trial_ids = {
        family: f"{family}_test_trial"
        for family in set(family_by_axis.values())
        if family != "wj05_center_x190"
    }
    family_trial_ids["center_x190"] = "center_x190_test_trial"
    station_ids = compositor.EXPECTED_CANDIDATE_AXIS_STATION_IDS
    bores = {}
    hardware = {}
    for index, axis_id in enumerate(axis_ids):
        family = family_by_axis[axis_id]
        trial_key = "center_x190" if family == "wj05_center_x190" else family
        if axis_id in inventory_report.top_outer.BACKER_AXIS_IDS:
            side = "left" if "left" in axis_id else "right"
            candidate_receiver = f"inner_kicker_backer_{side}"
        else:
            candidate_receiver = part_ids[index % len(part_ids)]
        bore = SimpleNamespace(
            axis_id=axis_id,
            family=family,
            trial_id=family_trial_ids[trial_key],
            station_id=station_ids.get(axis_id),
            receiver_ids=(candidate_receiver, "base_header"),
            shape=shape,
        )
        bores[axis_id] = bore
        role_ids = (
            inventory_report.BACKER_ROLES
            if axis_id in inventory_report.top_outer.BACKER_AXIS_IDS
            else inventory_report.ORDINARY_ROLES
        )
        hardware[axis_id] = {role: shape for role in role_ids}

    panel_rows = inventory["fixed_panel_kicker_screws"]
    redirected = {}
    for row in panel_rows:
        if (
            row["source_finished_receiver_member"]
            != row["candidate_finished_receiver_member"]
        ):
            redirected.setdefault(row["candidate_finished_receiver_member"], {})[
                row["axis_id"]
            ] = shape
    frame_rows = inventory["starting_frame_bolts"]
    frame_shapes = {
        f"{row['axis_id']}/installed_component_{index}": shape
        for row in frame_rows
        for index in range(1, 6)
    }
    frame_shapes.update(
        {f"{row['axis_id']}/source_occupied_axis": shape for row in frame_rows}
    )
    checks = {
        name: True
        for name in (
            "canonical_inventory_hash_and_source_binding_match",
            "all_24_legacy_duties_and_144_source_sds_axes_replaced",
            "all_104_candidate_axes_and_520_roles_preserved",
            "all_28_candidate_parts_preserved",
            "all_16_hosts_rebuilt_from_raw_union_native_purchase_cuts_and_candidate_bores",
            "four_backer_panel_cuts_preserved",
            "all_five_historical_receiver_overlays_absorbed",
            "no_source_only_overlays_remain",
            "all_66_fixed_axes_and_twelve_frame_bolts_preserved",
            "zero_retained_legacy_clips_or_sds_axes",
        )
    }
    checks.update(
        {
            name: False
            for name in (
                "complete_static_scene_diagnostic",
                "all_tool_or_access_intersections_clear",
                "complete_joint_acceptance",
                "capacity_established",
                "installation_proven",
                "fabrication_released",
                "structural_released",
            )
        }
    )
    return SimpleNamespace(
        layout_id=compositor.LAYOUT_ID,
        trial_id=compositor.TRIAL_ID,
        status="unaccepted_integrated_hypothesis",
        source=object(),
        source_binding=SimpleNamespace(
            inventory_sha256=inventory_hash, runtime_module_sha256={}
        ),
        source_inventory_sha256=inventory_hash,
        source_inventory=inventory,
        source_inputs_sha256={inventory_report.INVENTORY_PATH: inventory_hash},
        family_source_fingerprints={
            "test_source": {inventory_report.INVENTORY_PATH: inventory_hash}
        },
        family_trial_ids=family_trial_ids,
        target_station_ids=tuple(sorted(compositor.EXPECTED_TARGET_DUTY_IDS)),
        replaced_source_axis_ids=frozenset(
            axis["axis_id"]
            for duty in inventory["legacy_duties"]
            if duty["legacy_station_id"] in compositor.EXPECTED_TARGET_DUTY_IDS
            for axis in duty["legacy_sds_axes"]
            if axis.get("shop_opening_kind") == "sds_wood"
        ),
        candidate_bores=bores,
        candidate_installed_hardware=hardware,
        raw_candidate_parts={part_id: shape for part_id in part_ids},
        finished_candidate_parts={part_id: shape for part_id in part_ids},
        fixed_axes={row["axis_id"]: shape for row in panel_rows},
        purchased_panel_cutters_by_candidate_part=redirected,
        frame_bolt_records=tuple(
            {"axis_id": row["axis_id"], "installed_component_count": 5}
            for row in frame_rows
        ),
        frame_bolt_shapes=frame_shapes,
        composition_checks=checks,
    )


@pytest.fixture
def fake_geometry(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    geometry = _geometry()
    monkeypatch.setattr(
        inventory_report,
        "validate_source_binding",
        lambda source: geometry.source_binding,
    )
    return geometry


def test_physical_bom_counts_are_distinct_from_520_cad_roles(
    fake_geometry: SimpleNamespace,
) -> None:
    report = inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
    counts = report["counts"]
    assert counts["candidate_bore_axes"] == 104
    assert counts["installed_candidate_cad_role_shapes"] == 520
    assert counts["new_candidate_bolts_screen"] == 104
    assert counts["new_candidate_nuts_screen"] == 104
    assert counts["new_candidate_washers_screen"] == 216
    assert (
        counts["new_candidate_physical_piece_count_screen_excludes_integral_bolt_heads"]
        == 424
    )
    assert counts["candidate_axes_with_two_washer_roles"] == 100
    assert (
        counts["candidate_axes_with_one_bottom_and_three_top_washer_equivalents"] == 4
    )
    assert (
        counts[
            "candidate_backer_top_washer_roles_are_envelopes_not_three_separate_cad_roles"
        ]
        == 4
    )
    assert counts["retained_starting_frame_bolt_assemblies_separate"] == 12
    assert counts["fixed_Hillman_panel_kicker_screw_axes_separate"] == 66
    assert counts["removed_legacy_SDS_axes_not_candidate_BOM_items"] == 144
    assert report["release"] and not any(report["release"].values())


def test_actual_bore_receiver_pairs_and_hardware_length_classes_reconcile(
    fake_geometry: SimpleNamespace,
) -> None:
    report = inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
    groups = report["candidate_ordered_receiver_pair_groups"]
    assert sum(row["candidate_axis_count"] for row in groups) == 104
    assert all(
        row["order_semantics"].startswith("preserved from CandidateBore")
        for row in groups
    )
    axis_rows = report["candidate_hardware_axis_schedule"]
    assert {row["axis_id"] for row in axis_rows} == set(fake_geometry.candidate_bores)
    unstationed_legacy = [row for row in axis_rows if row["station_id"] is None]
    assert len(unstationed_legacy) == 56
    assert all(
        row["station_binding_status"].startswith(
            "retained_legacy_bore_has_no_station_id"
        )
        for row in unstationed_legacy
    )
    classes = Counter(
        (
            row["stack_class"]["modeled_nominal_length_mm"],
            row["stack_class"]["nominal_wood_grip_mm"],
        )
        for row in axis_rows
    )
    assert classes[(152.4, 127.0)] == 60
    assert classes[(203.2, 177.8)] == 24
    assert classes[(304.8, 270.0)] == 4
    assert classes[(None, 100.915644)] == 4
    assert classes[(None, 127.0)] == 8
    assert classes[(None, 167.0)] == 4
    center = [row for row in axis_rows if row["family"] == "wj05_center_x190"]
    assert all(
        row["stack_class"]["modeled_nominal_length_mm"] is None for row in center
    )
    assert all(
        row["stack_class"]["length_basis"].endswith("not a catalog bolt length")
        for row in center
    )


def test_receiver_pair_order_is_copied_from_each_bore_without_sorting(
    fake_geometry: SimpleNamespace,
) -> None:
    axis_id = next(
        axis_id
        for axis_id in sorted(fake_geometry.candidate_bores)
        if axis_id.startswith("top_center/")
    )
    original = fake_geometry.candidate_bores[axis_id].receiver_ids
    reversed_pair = tuple(reversed(original))
    fake_geometry.candidate_bores[axis_id].receiver_ids = reversed_pair
    report = inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
    axis = next(
        row
        for row in report["candidate_hardware_axis_schedule"]
        if row["axis_id"] == axis_id
    )
    assert axis["ordered_receiver_ids_from_candidate_bore"] == list(reversed_pair)
    assert any(
        row["ordered_receiver_ids"] == list(reversed_pair)
        and axis_id in row["candidate_axis_ids"]
        for row in report["candidate_ordered_receiver_pair_groups"]
    )


def test_all_28_stock_blanks_and_backer_receiver_cuts_are_listed(
    fake_geometry: SimpleNamespace,
) -> None:
    report = inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
    parts = report["candidate_connectors"]
    assert set(parts) == set(compositor.EXPECTED_CANDIDATE_PART_IDS)
    assert len(report["stock_blank_groups"]) == 8
    for row in parts.values():
        assert row["stock_blank_dimensions_mm"]
        assert row["grain_axis"]
        assert row["raw_candidate_shape"]["shape_sha256"]
        assert row["finished_candidate_shape"]["shape_sha256"]
        assert row["cut_or_drill_authorized"] is False
    assert len(parts["inner_kicker_backer_left"]["redirected_fixed_panel_cut_ids"]) == 2
    assert (
        len(parts["inner_kicker_backer_right"]["redirected_fixed_panel_cut_ids"]) == 2
    )


def test_source_screw_and_frame_bolt_schedules_remain_separate(
    fake_geometry: SimpleNamespace,
) -> None:
    report = inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
    frame = report["separate_retained_frame_bolts"]
    panel = report["separate_fixed_panel_kicker_screws"]
    removed = report["removed_legacy_SDS_axes"]
    assert frame["count"] == 12
    assert frame["shape_map_count"] == 72
    assert frame["installed_component_shape_count"] == 60
    assert len(frame["source_occupied_axis_proxies"]) == 12
    assert panel["count"] == 66
    assert len(panel["axes"]) == 66
    assert removed["count"] == 144
    assert len(removed["axis_ids"]) == 144
    assert not frame["new_candidate_bom_includes_these"]
    assert not panel["new_candidate_bom_includes_these"]
    assert not removed["replacement_bolt_BOM_items"]


def test_unresolved_geometry_role_is_fail_closed(
    fake_geometry: SimpleNamespace,
) -> None:
    axis_id = next(
        axis_id
        for axis_id in sorted(fake_geometry.candidate_installed_hardware)
        if axis_id not in inventory_report.top_outer.BACKER_AXIS_IDS
    )
    fake_geometry.candidate_installed_hardware[axis_id].pop("nut")
    with pytest.raises(ValueError, match="role map"):
        inventory_report.build_wj24_hardware_inventory_report(fake_geometry)


def test_changed_geometry_source_pin_is_rejected(
    fake_geometry: SimpleNamespace,
) -> None:
    fake_geometry.source_inputs_sha256[inventory_report.INVENTORY_PATH] = "0" * 64
    with pytest.raises(ValueError, match="source changed after composition"):
        inventory_report.build_wj24_hardware_inventory_report(fake_geometry)
