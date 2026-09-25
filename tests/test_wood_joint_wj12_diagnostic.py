from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from scripts.wood_joint_wj12_diagnostic import (
    WJ12_LAYOUT,
    _layout_identity_checks,
    build_diagnostic_report,
)

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_INVENTORY = json.loads(
    (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
)


def _box(x0, x1, y0=0.0, y1=10.0, z0=0.0, z1=10.0):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _cylinder(x0, length, y, z, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(x0, y, z), cq.Vector(1, 0, 0)
    )


@dataclass
class _Connection:
    name: str
    kind: str
    members: tuple[str, str]
    start: cq.Vector
    direction: cq.Vector
    diameter: float
    length: float
    grip: float


class _Source:
    def __init__(
        self,
        raw_host: cq.Shape,
        finished_host: cq.Shape,
        connection,
        *,
        extra_raw_parts=None,
        extra_finished_parts=None,
    ):
        self._raw_host = raw_host
        self._finished_host = finished_host
        self._connection = connection
        self._extra_raw_parts = dict(extra_raw_parts or {})
        self._extra_finished_parts = dict(extra_finished_parts or {})

    def uncut_wood_parts(self):
        return (
            SimpleNamespace(name="host", shape=self._raw_host),
            *(
                SimpleNamespace(name=name, shape=shape)
                for name, shape in sorted(self._extra_raw_parts.items())
            ),
        )

    def parts(self):
        # Keep a non-wood result here to verify that the diagnostic filters
        # the canonical parts() scene through uncut_wood_parts().
        return (
            SimpleNamespace(name="host", shape=self._finished_host),
            *(
                SimpleNamespace(name=name, shape=shape)
                for name, shape in sorted(self._extra_finished_parts.items())
            ),
            SimpleNamespace(name="legacy_clip", shape=_box(30, 31)),
        )

    def connections(self):
        return (self._connection,)


def _geometry(
    *,
    candidate_overlap=False,
    shifted_live_frame_axis=False,
    omit_receiver_cut=False,
    add_untouched_source_receivers=False,
    omit_source_overlays=False,
    omit_source_purchase_cutter_maps=False,
    native_source_axis_clear=False,
):
    raw_host = _box(0, 10)
    block_start = 9.5 if candidate_overlap else 10.0
    raw_block = _box(block_start, 20)
    candidate_bore = _cylinder(4, 12, 5, 5, 3.0)
    panel_axis = _cylinder(0, 6, 8, 8, 2.0)
    panel_cut = _cylinder(0, 7, 8, 8, 3.0)
    frame_cut = _cylinder(-1, 12, 2, 2, 5.0)
    finished_host = raw_host.cut(frame_cut, panel_cut, candidate_bore).clean()
    finished_block = raw_block.cut(candidate_bore).clean()

    frame_row = {
        "axis_id": "frame_bolt_1",
        "members": ["host", "other"],
        "origin_global_xyz_mm": [0.0, 2.0, 2.0],
        "axis_global_xyz": [1.0, 0.0, 0.0],
        "source_occupied_length_mm": 10.0,
        "source_occupied_diameter_mm": 3.0,
        "source_nominal_length_mm": 10.0,
        "source_grip_mm": 10.0,
        "candidate_recheck_status": "required",
    }
    live_start = (
        cq.Vector(1.0, 2.0, 2.0) if shifted_live_frame_axis else cq.Vector(0, 2, 2)
    )
    live_connection = _Connection(
        name="frame_bolt_1",
        kind="bolt",
        members=("host", "other"),
        start=live_start,
        direction=cq.Vector(1, 0, 0),
        diameter=3.0,
        length=10.0,
        grip=10.0,
    )
    extra_raw_parts = {}
    extra_finished_parts = {}
    extra_overlays = {}
    extra_purchase_cutters = {}
    extra_reconstruction = {}
    extra_fixed_rows = []
    extra_fixed_axes = {}
    if add_untouched_source_receivers:
        receiver_axis_counts = {
            "base_rail_top": 4,
            "base_rail_bottom_left": 2,
            "base_rail_bottom_right": 2,
            "base_rail_service_lower_left": 2,
            "base_rail_service_upper_left": 2,
        }
        for host_index, (host_id, axis_count) in enumerate(
            receiver_axis_counts.items()
        ):
            x0 = 100.0 + host_index * 20.0
            raw_part = _box(x0, x0 + 10.0)
            axes = {}
            cutters = {}
            native_cutters = []
            for axis_index in range(axis_count):
                axis_id = f"fixed_{host_id}_{axis_index + 1}"
                origin_x = x0 + 0.5
                center_y = 2.0 + axis_index * 2.0
                axis = _cylinder(origin_x, 6.0, center_y, 5.0, 2.0)
                cutter = _cylinder(origin_x, 8.0, center_y, 5.0, 3.0)
                native_cutter = _cylinder(origin_x, 6.0, center_y, 5.0, 3.0)
                axes[axis_id] = axis
                cutters[f"panel_purchase/{axis_id}"] = cutter
                native_cutters.append(native_cutter)
                extra_fixed_rows.append(
                    {
                        "axis_id": axis_id,
                        "panel_member": "panel",
                        "source_finished_receiver_member": host_id,
                        "candidate_finished_receiver_member": host_id,
                        "origin_global_xyz_mm": [origin_x, center_y, 5.0],
                        "axis_global_xyz": [1.0, 0.0, 0.0],
                        "source_occupied_length_mm": 6.0,
                        "source_occupied_diameter_mm": 2.0,
                        "shop_purchased_length_mm": 8.0,
                    }
                )
            source_finished = (
                raw_part.cut(*native_cutters).clean()
                if native_source_axis_clear
                else raw_part
            )
            overlay = source_finished.cut(*cutters.values()).clean()
            extra_raw_parts[host_id] = raw_part
            extra_finished_parts[host_id] = source_finished
            extra_fixed_axes.update(axes)
            extra_purchase_cutters[host_id] = cutters
            if not omit_source_overlays:
                extra_overlays[host_id] = overlay
                cutter_volumes = {
                    cutter_id: float(source_finished.intersect(cutter).Volume())
                    for cutter_id, cutter in cutters.items()
                }
                extra_reconstruction[host_id] = {
                    "source_finished_shape_sha256": _source_shape_fingerprint(
                        source_finished
                    ),
                    "overlaid_finished_shape_sha256": _source_shape_fingerprint(
                        overlay
                    ),
                    "purchase_cut_ids": sorted(cutters),
                    "purchase_cut_intersection_mm3_by_id": cutter_volumes,
                    "matches_source_plus_purchase_cuts": True,
                }
        if omit_source_purchase_cutter_maps:
            extra_purchase_cutters = {}

    source = _Source(
        raw_host,
        finished_host,
        live_connection,
        extra_raw_parts=extra_raw_parts,
        extra_finished_parts=extra_finished_parts,
    )

    frame_components = {
        f"frame_bolt_1/installed_component_{index}": _cylinder(
            30 + index, 0.2, 2, 2, 0.2
        )
        for index in range(1, 5)
    }
    frame_components["frame_bolt_1/source_occupied_axis"] = _cylinder(0, 10, 2, 2, 3.0)
    purchased_panel_cuts = (
        {}
        if omit_receiver_cut
        else {"host": {"panel_purchase/fixed_axis_1": panel_cut}}
    )

    return SimpleNamespace(
        trial_id="synthetic-wj12",
        source=source,
        source_binding=SimpleNamespace(inventory_sha256="inventory-sha"),
        source_inventory_sha256="inventory-sha",
        source_inventory={
            "candidate": "synthetic",
            "source_commit": "test",
            "legacy_duties": [
                {
                    "legacy_station_id": "station_1",
                    "legacy_sds_axes": [
                        {"axis_id": f"old_{i}", "shop_opening_kind": "sds_wood"}
                        for i in range(6)
                    ],
                }
            ],
            "fixed_panel_kicker_screws": [
                {
                    "axis_id": "fixed_axis_1",
                    "panel_member": "panel",
                    "source_finished_receiver_member": "host",
                    "candidate_finished_receiver_member": "host",
                    "origin_global_xyz_mm": [0.0, 8.0, 8.0],
                    "axis_global_xyz": [1.0, 0.0, 0.0],
                    "source_occupied_length_mm": 6.0,
                    "source_occupied_diameter_mm": 2.0,
                    "shop_purchased_length_mm": 6.0,
                },
                *extra_fixed_rows,
            ],
            "starting_frame_bolts": [frame_row],
        },
        family_trial_ids={"synthetic": "v1"},
        target_station_ids=("station_1",),
        raw_hosts={"host": raw_host},
        finished_hosts={"host": finished_host},
        raw_candidate_parts={"block": raw_block},
        finished_candidate_parts={"block": finished_block},
        candidate_bores={
            "candidate_axis_1": SimpleNamespace(
                family="synthetic",
                receiver_ids=("host", "block"),
                shape=candidate_bore,
            )
        },
        candidate_installed_hardware={
            "candidate_axis_1": {
                "shaft": candidate_bore,
                "head": _cylinder(-5, 0.5, 5, 5, 2.0),
            }
        },
        replaced_source_axis_ids=frozenset(f"old_{i}" for i in range(6)),
        source_reconstruction={
            "host": {
                "symmetric_difference_mm3": 0.0,
                "matches_source_finished_member": True,
            }
        },
        source_cutters_by_host={"host": {"frame_bolt_1": frame_cut}},
        purchased_panel_cutters_by_host=purchased_panel_cuts,
        purchased_panel_cutters_by_candidate_part={},
        additional_finished_source_parts=extra_overlays,
        additional_purchased_panel_cutters_by_host=extra_purchase_cutters,
        additional_source_reconstruction=extra_reconstruction,
        panel_replacements={},
        fixed_axes={"fixed_axis_1": panel_axis, **extra_fixed_axes},
        frame_bolt_records=[{**frame_row, "installed_component_count": 4}],
        frame_bolt_shapes=frame_components,
        protected={
            "retained_legacy_clips": {"old_clip": _box(30, 31)},
            "retained_12_frame_bolt_tools_withdrawals": {
                "access_proxy": _box(10.5, 11.5, 1, 2, 1, 2)
            },
        },
    )


def _wj12_layout_fixture():
    duty_rows = {
        row["legacy_station_id"]: row for row in CANONICAL_INVENTORY["legacy_duties"]
    }
    retained_duty_ids = set(duty_rows) - set(WJ12_LAYOUT.expected_target_duty_ids)
    replaced_axis_ids = {
        axis["axis_id"]
        for station_id in WJ12_LAYOUT.expected_target_duty_ids
        for axis in duty_rows[station_id]["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    retained_axis_ids = {
        axis["axis_id"]
        for station_id in retained_duty_ids
        for axis in duty_rows[station_id]["legacy_sds_axes"]
        if axis["shop_opening_kind"] == "sds_wood"
    }
    overlay_cutters = {
        host_id: {
            f"panel_purchase/{row['axis_id']}": object()
            for row in CANONICAL_INVENTORY["fixed_panel_kicker_screws"]
            if row["source_finished_receiver_member"] == host_id
            and row["candidate_finished_receiver_member"] == host_id
        }
        for host_id, _count in WJ12_LAYOUT.expected_additional_overlay_axis_counts
    }
    frame_ids = {row["axis_id"] for row in CANONICAL_INVENTORY["starting_frame_bolts"]}
    frame_shapes = {
        f"{axis_id}/installed_component_{index}": object()
        for axis_id in frame_ids
        for index in range(1, 6)
    }
    frame_shapes.update(
        {f"{axis_id}/source_occupied_axis": object() for axis_id in frame_ids}
    )
    return SimpleNamespace(
        layout_id=WJ12_LAYOUT.layout_id,
        trial_id=WJ12_LAYOUT.trial_id,
        source_inventory=CANONICAL_INVENTORY,
        target_station_ids=tuple(sorted(WJ12_LAYOUT.expected_target_duty_ids)),
        raw_hosts={
            host_id: object() for host_id in WJ12_LAYOUT.expected_source_host_ids
        },
        finished_hosts={
            host_id: object() for host_id in WJ12_LAYOUT.expected_source_host_ids
        },
        raw_candidate_parts={
            part_id: object() for part_id in WJ12_LAYOUT.expected_candidate_part_ids
        },
        finished_candidate_parts={
            part_id: object() for part_id in WJ12_LAYOUT.expected_candidate_part_ids
        },
        candidate_bores={
            axis_id: SimpleNamespace(station_id=None)
            for axis_id in WJ12_LAYOUT.expected_candidate_axis_ids
        },
        candidate_installed_hardware={
            axis_id: {f"role_{index}": object() for index in range(5)}
            for axis_id in WJ12_LAYOUT.expected_candidate_axis_ids
        },
        replaced_source_axis_ids=frozenset(replaced_axis_ids),
        source_reconstruction={
            host_id: {"matches_source_finished_member": True}
            for host_id in WJ12_LAYOUT.expected_source_host_ids
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
            for host_id, _ in WJ12_LAYOUT.expected_additional_overlay_axis_counts
        },
        additional_purchased_panel_cutters_by_host=overlay_cutters,
        fixed_axes={
            row["axis_id"]: object()
            for row in CANONICAL_INVENTORY["fixed_panel_kicker_screws"]
        },
        frame_bolt_records=tuple({"axis_id": axis_id} for axis_id in frame_ids),
        frame_bolt_shapes=frame_shapes,
    )


def test_default_wj12_layout_identity_contract_is_exact():
    checks = _layout_identity_checks(_wj12_layout_fixture(), WJ12_LAYOUT)

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
        ("inventory_changed", "source_inventory_matches_canonical"),
    ],
)
def test_default_wj12_layout_identity_contract_rejects_missing_or_extra_ids(
    defect, identity_key
):
    geometry = _wj12_layout_fixture()
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
    elif defect == "sds_extra":
        geometry.protected["retained_legacy_sds_axes"]["unexpected_sds"] = object()
    else:
        geometry.source_inventory = {**CANONICAL_INVENTORY, "unexpected": True}

    checks = _layout_identity_checks(geometry, WJ12_LAYOUT)

    assert checks["exact_sets_match"][identity_key] is False
    assert checks["all_exact_sets_match"] is False


def test_declared_body_interfaces_still_fail_positive_volume_overlap():
    report = build_diagnostic_report(_geometry(candidate_overlap=True))

    overlap = report["candidate_bodies"]["candidate_body_vs_finished_wood_hits"][
        "block"
    ]["host"]
    assert overlap["declared_candidate_fastener_interface"] is True
    assert overlap["overlap_mm3"] > 0
    assert (
        report["diagnostic_gates"]["candidate_body_finished_wood_hits_absent"] is False
    )
    assert report["diagnostic_gates"]["integrated_clearance_accepted"] is False


def test_temporary_access_overlap_is_reported_separately_from_physical_clearance():
    report = build_diagnostic_report(_geometry())

    assert report["integrated_scene"]["finished_wood_ids"] == ["block", "host"]
    assert report["integrated_scene"]["access_envelope_shape_count"] == 1
    frame_counts = report["counts_and_ids"]["starting_frame_bolts"]
    assert frame_counts["component_count"] == 4
    assert frame_counts["occupied_axis_proxy_count"] == 1
    assert frame_counts["total_shape_count"] == 5
    assert report["candidate_bodies"]["candidate_body_vs_access_envelope_hits_mm3"][
        "block"
    ]
    assert not report["candidate_bodies"][
        "candidate_body_vs_physical_protected_hits_mm3"
    ]
    assert report["fixed_66_receiver_checks"]["per_axis"]["fixed_axis_1"][
        "raw_receiver_material_present"
    ]
    assert report["fixed_66_receiver_checks"]["per_axis"]["fixed_axis_1"][
        "finished_receiver_clear_of_axis"
    ]


def test_live_frame_bolt_axis_is_recomputed_against_inventory():
    report = build_diagnostic_report(_geometry(shifted_live_frame_axis=True))

    bolt = report["starting_frame_bolt_recheck"]["per_bolt"]["frame_bolt_1"]
    assert bolt["record_matches_source_inventory"] is True
    assert bolt["live_source_connection_matches_inventory"] is False
    assert bolt["live_connection_origin_delta_mm"] == 1.0
    assert (
        report["diagnostic_gates"]["frame_bolt_inventory_and_live_axes_match"] is False
    )


def test_missing_fixed_receiver_purchase_cut_is_reported():
    report = build_diagnostic_report(_geometry(omit_receiver_cut=True))

    receiver = report["fixed_66_receiver_checks"]["per_axis"]["fixed_axis_1"]
    assert receiver["raw_receiver_material_present"] is True
    assert receiver["required_support_or_embedment_evaluated"] is False
    assert receiver["purchase_cut_present_on_composed_receiver"] is False
    assert (
        report["diagnostic_gates"]["fixed_panel_receiver_material_and_cuts_present"]
        is False
    )


def test_twelve_untouched_source_receivers_fail_when_purchase_overlays_are_missing():
    report = build_diagnostic_report(
        _geometry(
            add_untouched_source_receivers=True,
            omit_source_overlays=True,
        )
    )

    overlay_checks = report["additional_source_purchase_overlays"]
    assert overlay_checks["expected_host_count"] == 5
    assert overlay_checks["expected_fixed_axis_count"] == 12
    assert overlay_checks["overlay_host_ids"] == []
    assert len(overlay_checks["cutter_map_host_ids"]) == 5
    extra_axis_rows = {
        axis_id: row
        for axis_id, row in report["fixed_66_receiver_checks"]["per_axis"].items()
        if axis_id.startswith("fixed_base_rail_")
    }
    assert len(extra_axis_rows) == 12
    assert all(row["raw_receiver_material_present"] for row in extra_axis_rows.values())
    assert all(
        row["purchase_cut_present_on_composed_receiver"]
        for row in extra_axis_rows.values()
    )
    assert all(
        row["finished_receiver_axis_overlap_mm3"] > 0
        for row in extra_axis_rows.values()
    )
    assert (
        report["diagnostic_gates"]["untouched_source_receiver_overlays_reconcile"]
        is False
    )
    assert (
        report["diagnostic_gates"]["fixed_panel_receiver_material_and_cuts_present"]
        is False
    )


def test_twelve_untouched_source_receivers_replay_candidate_purchase_overlays():
    report = build_diagnostic_report(_geometry(add_untouched_source_receivers=True))

    overlays = report["additional_source_purchase_overlays"]
    assert overlays["expected_host_count"] == 5
    assert overlays["expected_fixed_axis_count"] == 12
    assert overlays["host_ids_match_expected"] is True
    assert overlays["all_overlay_cutter_ids_match_fixed_axes"] is True
    assert overlays["all_purchase_cutters_intersect_source_finished_members"] is True
    assert overlays["all_overlays_replay_from_source_finished_members_and_cuts"] is True
    assert overlays["all_compositor_reconstruction_evidence_matches"] is True
    assert (
        report["diagnostic_gates"]["untouched_source_receiver_overlays_reconcile"]
        is True
    )


def test_missing_source_overlays_cannot_pass_on_preexisting_axis_clearance():
    report = build_diagnostic_report(
        _geometry(
            add_untouched_source_receivers=True,
            omit_source_overlays=True,
            native_source_axis_clear=True,
        )
    )

    extra_axis_rows = {
        axis_id: row
        for axis_id, row in report["fixed_66_receiver_checks"]["per_axis"].items()
        if axis_id.startswith("fixed_base_rail_")
    }
    assert len(extra_axis_rows) == 12
    assert all(
        row["purchase_cut_present_on_composed_receiver"]
        for row in extra_axis_rows.values()
    )
    assert all(
        row["finished_receiver_clear_of_axis"] for row in extra_axis_rows.values()
    )
    # The fixed-axis subcheck alone would be green, but the required source-scene
    # overlay and its replay evidence are absent, so the integration gate stays false.
    assert (
        report["diagnostic_gates"]["fixed_panel_receiver_material_and_cuts_present"]
        is True
    )
    assert (
        report["diagnostic_gates"]["untouched_source_receiver_overlays_reconcile"]
        is False
    )


def test_source_provenance_includes_family_and_report_producer_hashes():
    report = build_diagnostic_report(_geometry())
    provenance = report["source_provenance"]

    assert len(provenance["compositor_sha256"]) == 64
    assert len(provenance["diagnostic_sha256"]) == 64
    assert provenance["family_source_fingerprints_sha256"] == {}
    assert provenance["family_input_hashes_current"] is False
