"""Viewer-only removal of the outer rear bridges and under-header links.

Consumes the already revised sandwich-block WJ24 model. The outer spines,
inner sandwich blocks, shared rim bolts, inner-block header bolts, and all
unrelated current geometry remain; affected raw timber and retained candidate
parts are recut without the removed axes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

SCHEMA = "wood_joint_wj24_remove_outer_links/v1"
REVISION_ID = "outer-rear-bridges-under-header-links-removed-v1"
INPUT_REVISION_ID = "outer-rim-inner-frame-blocks-v1"
SIDES = ("left", "right")
REMOVED_PART_IDS = frozenset(
    f"knee_outer_{side}_{kind}"
    for side in SIDES
    for kind in ("rear_bridge", "under_header_link")
)
REMOVED_AXIS_IDS = frozenset(
    axis_id
    for side in SIDES
    for stem in ("bridge_spine", "bridge_link", "header")
    for index in (1, 2)
    for axis_id in (f"knee_outer_{side}_{stem}_{index}",)
)
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
OUTER_SPINE_IDS = frozenset(f"knee_outer_{side}_spine" for side in SIDES)
PRESERVED_SIDE_AXIS_IDS = frozenset(
    f"knee_outer_{side}_side_{index}" for side in SIDES for index in (1, 2)
)
PRESERVED_INNER_HEADER_AXIS_IDS = frozenset(
    f"knee_outer_{side}_inner_header_1" for side in SIDES
)


def _proxy(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _nested_proxy(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType({key: _proxy(value) for key, value in values.items()})


def _shape(value: Any, label: str) -> cq.Shape:
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{label}: expected a valid positive solid")
    return value


def _merge_ids(*sequences: Any) -> list[str]:
    values: set[str] = set()
    for sequence in sequences:
        if sequence is None:
            continue
        if not isinstance(sequence, (tuple, list, set, frozenset)):
            raise TypeError("cumulative ID fields must be sequences")
        values.update(map(str, sequence))
    return sorted(values)


def _merge_display_ids(
    prior: Mapping[str, Any], current: Mapping[str, list[str]], removed: set[str]
) -> dict[str, list[str]]:
    merged: dict[str, set[str]] = {}
    for source in (prior, current):
        for category, values in source.items():
            if not isinstance(values, (tuple, list, set, frozenset)):
                raise TypeError(f"changed_display_solid_ids/{category} must be a sequence")
            merged.setdefault(str(category), set()).update(map(str, values))
    return {
        category: sorted(values - removed)
        for category, values in sorted(merged.items())
    }


def _rebuild_host(
    geometry: Any, host_id: str, bores: Mapping[str, Any]
) -> tuple[cq.Shape, dict[str, Any]]:
    raw = _shape(geometry.raw_hosts[host_id], f"raw host {host_id}")
    source_cuts = geometry.applied_source_cutters_by_host[host_id]
    replaced = set(geometry.replaced_source_cutter_ids)
    retained = [cutter for key, cutter in source_cuts.items() if key not in replaced]
    host_bores = {
        axis_id: bore.shape
        for axis_id, bore in bores.items()
        if host_id in tuple(getattr(bore, "receiver_ids", ()))
    }
    cutters = retained + list(host_bores.values())
    rebuilt = raw.cut(*cutters).clean() if cutters else raw
    finished = _shape(rebuilt, f"rebuilt host {host_id}")
    return finished, {
        "retained_source_and_purchase_cutter_count": len(retained),
        "excluded_replaced_source_cutter_count": len(source_cuts) - len(retained),
        "candidate_bore_axis_ids": sorted(host_bores),
        "finished_shape_sha256": _source_shape_fingerprint(finished),
    }


def _rebuild_candidate_part(
    geometry: Any, part_id: str, bores: Mapping[str, Any]
) -> tuple[cq.Shape, dict[str, Any]]:
    raw = _shape(geometry.raw_candidate_parts[part_id], f"raw candidate part {part_id}")
    receiver_bores = {
        axis_id: bore.shape
        for axis_id, bore in bores.items()
        if part_id in tuple(getattr(bore, "receiver_ids", ()))
    }
    purchase_map = getattr(geometry, "purchased_panel_cutters_by_candidate_part", {})
    purchase_cuts = dict(purchase_map.get(part_id, {}))
    cutters = list(purchase_cuts.values()) + list(receiver_bores.values())
    rebuilt = raw.cut(*cutters).clean() if cutters else raw
    finished = _shape(rebuilt, f"rebuilt candidate part {part_id}")
    return finished, {
        "retained_purchased_panel_cutter_ids": sorted(purchase_cuts),
        "candidate_bore_axis_ids": sorted(receiver_bores),
        "finished_shape_sha256": _source_shape_fingerprint(finished),
    }


def build_wj24_remove_outer_links(
    geometry: Any,
    prior_report: Mapping[str, Any],
    *,
    progress: Callable[[str], None] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Remove four outer link members and every candidate stack attached to them."""
    if not isinstance(prior_report, Mapping):
        raise TypeError("prior_report must be a mapping")
    input_revision = getattr(geometry, "layout_id", None)
    if input_revision != INPUT_REVISION_ID or getattr(geometry, "trial_id", None) != INPUT_REVISION_ID:
        raise ValueError("input must be the outer-rim-inner-frame-blocks WJ24 revision")
    if prior_report.get("revision_id") != input_revision:
        raise ValueError("prior report must describe the supplied WJ24 geometry")
    if getattr(geometry, "status", None) != "unaccepted_viewer_geometry_revision":
        raise ValueError("input WJ24 geometry status changed")
    for name in (
        "raw_hosts", "finished_hosts", "applied_source_cutters_by_host",
        "replaced_source_cutter_ids", "raw_candidate_parts", "finished_candidate_parts",
        "candidate_bores", "candidate_installed_hardware", "fixed_axes",
        "frame_bolt_records", "frame_bolt_shapes", "purchased_panel_cutters_by_candidate_part",
    ):
        if not hasattr(geometry, name):
            raise ValueError(f"current WJ24 geometry lacks {name}")
    if not REMOVED_PART_IDS <= set(geometry.raw_candidate_parts) or not REMOVED_PART_IDS <= set(
        geometry.finished_candidate_parts
    ):
        raise ValueError("current WJ24 candidate maps omit a requested outer link")
    if not REMOVED_AXIS_IDS <= set(geometry.candidate_bores) or not REMOVED_AXIS_IDS <= set(
        geometry.candidate_installed_hardware
    ):
        raise ValueError("current WJ24 candidate maps omit one or more attached outer-link axes")

    # Explicit source-defined ownership keeps the new rim sandwich stacks out
    # of the removal set and catches any accidental change to the old six-axis
    # support/corner topology.
    expected_receivers: dict[str, tuple[str, str]] = {}
    for side in SIDES:
        bridge = f"knee_outer_{side}_rear_bridge"
        under = f"knee_outer_{side}_under_header_link"
        spine = f"knee_outer_{side}_spine"
        for index in (1, 2):
            expected_receivers[f"knee_outer_{side}_bridge_spine_{index}"] = (bridge, spine)
            expected_receivers[f"knee_outer_{side}_bridge_link_{index}"] = (bridge, under)
            expected_receivers[f"knee_outer_{side}_header_{index}"] = ("base_header", under)
    for axis_id, expected in expected_receivers.items():
        bore = geometry.candidate_bores[axis_id]
        if tuple(getattr(bore, "receiver_ids", ())) != expected:
            raise ValueError(f"{axis_id}: receiver order differs from the outer-link contract")
        roles = geometry.candidate_installed_hardware[axis_id]
        if set(roles) != HARDWARE_ROLES:
            raise ValueError(f"{axis_id}: expected the exact five CAD hardware roles")
    for axis_id in PRESERVED_SIDE_AXIS_IDS:
        bore = geometry.candidate_bores.get(axis_id)
        expected = (
            f"knee_outer_{axis_id.split('_')[2]}_spine",
            f"base_side_{axis_id.split('_')[2]}",
            f"knee_outer_{axis_id.split('_')[2]}_inner_frame_block",
        )
        if bore is None or tuple(bore.receiver_ids) != expected:
            raise ValueError(f"{axis_id}: shared spine/rim/block sandwich bolt must be preserved")
    for axis_id in PRESERVED_INNER_HEADER_AXIS_IDS:
        bore = geometry.candidate_bores.get(axis_id)
        side = "left" if "_left_" in axis_id else "right"
        if bore is None or tuple(bore.receiver_ids) != (
            f"knee_outer_{side}_inner_frame_block", "base_header"
        ):
            raise ValueError(f"{axis_id}: new inner-block/header bolt must be preserved")

    all_owned_target_axes = {
        axis_id
        for axis_id, bore in geometry.candidate_bores.items()
        if set(getattr(bore, "receiver_ids", ())) & REMOVED_PART_IDS
    }
    if all_owned_target_axes != set(REMOVED_AXIS_IDS):
        raise ValueError(
            "outer links own an unexpected candidate axis set: "
            f"missing={sorted(set(REMOVED_AXIS_IDS) - all_owned_target_axes)}, "
            f"extra={sorted(all_owned_target_axes - set(REMOVED_AXIS_IDS))}"
        )

    bores = {axis_id: bore for axis_id, bore in geometry.candidate_bores.items() if axis_id not in REMOVED_AXIS_IDS}
    hardware = {
        axis_id: dict(roles)
        for axis_id, roles in geometry.candidate_installed_hardware.items()
        if axis_id not in REMOVED_AXIS_IDS
    }
    raw_parts = {part_id: shape for part_id, shape in geometry.raw_candidate_parts.items() if part_id not in REMOVED_PART_IDS}
    finished_parts = {part_id: shape for part_id, shape in geometry.finished_candidate_parts.items() if part_id not in REMOVED_PART_IDS}
    purchase_by_part = {
        part_id: dict(cutters)
        for part_id, cutters in geometry.purchased_panel_cutters_by_candidate_part.items()
        if part_id not in REMOVED_PART_IDS
    }

    affected_hosts = {
        receiver
        for axis_id in REMOVED_AXIS_IDS
        for receiver in geometry.candidate_bores[axis_id].receiver_ids
        if receiver in geometry.raw_hosts
    }
    affected_parts = {
        receiver
        for axis_id in REMOVED_AXIS_IDS
        for receiver in geometry.candidate_bores[axis_id].receiver_ids
        if receiver in raw_parts
    }
    if not affected_hosts or not OUTER_SPINE_IDS <= affected_parts:
        raise ValueError("outer-link removal failed to identify all retained affected receivers")

    finished_hosts = dict(geometry.finished_hosts)
    host_replay: dict[str, Any] = {}
    for host_id in sorted(affected_hosts):
        if progress is not None:
            progress(f"rebuilding raw source host {host_id} without removed outer-link bores")
        finished_hosts[host_id], host_replay[host_id] = _rebuild_host(geometry, host_id, bores)
    part_replay: dict[str, Any] = {}
    for part_id in sorted(affected_parts):
        if progress is not None:
            progress(f"rebuilding retained candidate part {part_id} without removed outer-link bores")
        finished_parts[part_id], part_replay[part_id] = _rebuild_candidate_part(
            geometry, part_id, bores
        )

    if len(geometry.fixed_axes) != 66:
        raise ValueError("fixed panel/kicker axis count changed before outer-link revision")
    if len(geometry.frame_bolt_records) != 12 or len(geometry.frame_bolt_shapes) != 72:
        raise ValueError("starting frame-bolt map changed before outer-link revision")
    if not PRESERVED_SIDE_AXIS_IDS | PRESERVED_INNER_HEADER_AXIS_IDS <= set(bores):
        raise ValueError("the new outer sandwich-bolt axes were not preserved")

    checks = {
        "both_outer_rear_bridges_and_under_header_links_removed": len(REMOVED_PART_IDS) == 4,
        "all_twelve_attached_candidate_axes_and_sixty_hardware_roles_removed": len(REMOVED_AXIS_IDS) == 12,
        "affected_raw_hosts_rebuilt_without_removed_source_or_candidate_holes": True,
        "retained_outer_spines_and_all_candidate_receiver_holes_replayed": True,
        "exterior_spine_rim_inner_block_side_bolts_preserved": True,
        "inner_block_to_header_vertical_bolts_preserved": True,
        "all_66_fixed_panel_axes_and_12_starting_frame_bolts_preserved": True,
        "viewer_geometry_only_no_mechanics_or_joint_acceptance": True,
        "complete_joint_acceptance": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    revised = replace(
        geometry,
        layout_id=REVISION_ID,
        trial_id=REVISION_ID,
        status="unaccepted_viewer_geometry_revision",
        raw_candidate_parts=_proxy(raw_parts),
        finished_candidate_parts=_proxy(finished_parts),
        candidate_bores=_proxy(bores),
        candidate_installed_hardware=_nested_proxy(hardware),
        finished_hosts=_proxy(finished_hosts),
        purchased_panel_cutters_by_candidate_part=_nested_proxy(purchase_by_part),
        composition_checks=_proxy(checks),
    )

    newly_removed_display = set(REMOVED_PART_IDS) | {
        f"{axis_id}/{role}" for axis_id in REMOVED_AXIS_IDS for role in HARDWARE_ROLES
    }
    cumulative_removed_display = set(
        _merge_ids(prior_report.get("removed_display_solid_ids", ()), sorted(newly_removed_display))
    )
    prior_changed = prior_report.get("changed_display_solid_ids", {})
    if not isinstance(prior_changed, Mapping):
        raise TypeError("prior report changed_display_solid_ids must be a mapping")
    current_changed = {
        "finished_hosts": sorted(affected_hosts),
        "finished_candidate_parts": sorted(affected_parts),
        "candidate_installed_hardware": [],
        "panel_replacements": [],
        "fixed_panel_axes": [],
    }
    changed_display = _merge_display_ids(prior_changed, current_changed, cumulative_removed_display)
    moved_panel_axes = list(prior_report.get("moved_panel_axes", ()))
    moved_panel_ids = [
        row["axis_id"] for row in moved_panel_axes if isinstance(row, Mapping) and row.get("axis_id")
    ]
    if len(moved_panel_ids) != len(set(moved_panel_ids)):
        raise ValueError("prior report contains duplicate moved panel-axis rows")

    report = {
        "schema": SCHEMA,
        "status": "unaccepted_viewer_geometry_revision",
        "revision_id": REVISION_ID,
        "input_revision_id": INPUT_REVISION_ID,
        "prior_revision_report": dict(prior_report),
        "summary": "The two exterior rear bridges and two under-header links are removed. Obsolete bridge holes are cleared from retained outer spines while their post and shared side-bolt holes remain; current source cuts and candidate bores are replayed.",
        "scope": "viewer geometry only; no mechanics, force calculation, joint acceptance, fabrication, or drilling release",
        "removed_candidate_part_ids": _merge_ids(
            prior_report.get("removed_candidate_part_ids", ()), sorted(REMOVED_PART_IDS)
        ),
        "removed_candidate_axis_ids": _merge_ids(
            prior_report.get("removed_candidate_axis_ids", ()), sorted(REMOVED_AXIS_IDS)
        ),
        "removed_display_solid_ids": sorted(cumulative_removed_display),
        "moved_candidate_axis_ids": _merge_ids(prior_report.get("moved_candidate_axis_ids", ())),
        "moved_panel_axes": moved_panel_axes,
        "baseline_display_translations_mm": dict(
            prior_report.get("baseline_display_translations_mm", {})
        ),
        "changed_display_solid_ids": changed_display,
        "preserved_ids": {
            "outer_spines": sorted(OUTER_SPINE_IDS),
            "shared_spine_rim_inner_block_axes": sorted(PRESERVED_SIDE_AXIS_IDS),
            "inner_block_header_axes": sorted(PRESERVED_INNER_HEADER_AXIS_IDS),
        },
        "affected_receiver_ids": {
            "raw_hosts": sorted(affected_hosts),
            "retained_candidate_parts": sorted(affected_parts),
        },
        "host_replay": host_replay,
        "candidate_part_replay": part_replay,
        "preserved_counts": {
            "candidate_parts_before_after": [
                len(geometry.finished_candidate_parts), len(finished_parts)
            ],
            "candidate_axes_before_after": [len(geometry.candidate_bores), len(bores)],
            "candidate_hardware_roles_before_after": [
                sum(map(len, geometry.candidate_installed_hardware.values())),
                sum(map(len, hardware.values())),
            ],
            "fixed_panel_axes": len(geometry.fixed_axes),
            "starting_frame_bolts": len(geometry.frame_bolt_records),
        },
        "checks": checks,
    }
    return revised, report
