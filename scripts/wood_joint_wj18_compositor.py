"""Compose the retained WJ16 geometry with the top-outer cleat pair.

The parent owns the serialized CAD slot. This module accepts already retained
WJ16 and top-outer geometry objects; it never materializes a family or runs a
native solver. It rebuilds the fourteen shared source hosts from raw members,
the union of native and purchased cuts, and all eighty candidate bores.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import (
    _source_shape_fingerprint,
    validate_source_binding,
)
from scripts import wood_joint_right_rail_integration as right_integration
from scripts import wood_joint_top_outer_integration as top_outer
from scripts import wood_joint_wj12_compositor as wj12
from scripts import wood_joint_wj16_compositor as wj16
from scripts import wood_joint_wj16_diagnostic as wj16_diagnostic

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj18_compositor/v1"
LAYOUT_ID = "wj18-eighteen-duty-integrated-static-v1"
TRIAL_ID = "wj18-wj16-plus-top-outer-v1"
SOURCE_RECONSTRUCTION_TOLERANCE_MM3 = 1e-3

TOP_AXIS_STATION_IDS = {
    f"top_outer/{duty_id}/{role}_{index}": duty_id
    for duty_id in sorted(top_outer.TARGET_DUTY_IDS)
    for role in ("rail", "side")
    for index in (1, 2)
}
TOP_CANDIDATE_AXIS_IDS = frozenset(TOP_AXIS_STATION_IDS)
TOP_CANDIDATE_PART_IDS = frozenset(top_outer.CLEAT_IDS.values())
EXPECTED_TARGET_DUTY_IDS = (
    wj16.EXPECTED_TARGET_DUTY_IDS | top_outer.TARGET_DUTY_IDS
)
EXPECTED_SOURCE_HOST_IDS = wj16.EXPECTED_SOURCE_HOST_IDS | {"base_rail_top"}
EXPECTED_CANDIDATE_AXIS_IDS = (
    wj16.EXPECTED_CANDIDATE_AXIS_IDS | TOP_CANDIDATE_AXIS_IDS
)
EXPECTED_CANDIDATE_PART_IDS = (
    wj16.EXPECTED_CANDIDATE_PART_IDS | TOP_CANDIDATE_PART_IDS
)
EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS = {
    "base_rail_bottom_left": 2,
    "base_rail_bottom_right": 2,
}
EXPECTED_REPLACED_SOURCE_AXIS_COUNT = 108
EXPECTED_RETAINED_LEGACY_CLIP_COUNT = 6
EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT = 36
EXPECTED_CANDIDATE_AXIS_COUNT = 80
EXPECTED_CANDIDATE_PART_COUNT = 22
EXPECTED_INSTALLED_COMPONENT_COUNT = 400
EXPECTED_FIXED_PANEL_AXIS_COUNT = 66
EXPECTED_FRAME_BOLT_COUNT = 12
EXPECTED_FRAME_BOLT_COMPONENT_COUNT = 60
EXPECTED_FRAME_BOLT_AXIS_PROXY_COUNT = 12
EXPECTED_FRAME_BOLT_SHAPE_COUNT = 72

PRODUCER_HASH_PATHS = {
    "wj18_compositor": "scripts/wood_joint_wj18_compositor.py",
    "wj18_diagnostic": "scripts/wood_joint_wj18_diagnostic.py",
    "wj16_compositor": "scripts/wood_joint_wj16_compositor.py",
    "wj16_diagnostic": "scripts/wood_joint_wj16_diagnostic.py",
    "top_outer_producer": "scripts/wood_joint_top_outer_integration.py",
}


@dataclass(frozen=True)
class WJ18ComposedGeometry:
    """One source-bound eighteen-duty geometry composition."""

    layout_id: str
    trial_id: str
    source: Any
    source_binding: Any
    source_inventory_sha256: str
    source_inventory: Mapping[str, Any]
    family_source_fingerprints: Mapping[str, Mapping[str, str]]
    family_trial_ids: Mapping[str, str]
    target_station_ids: tuple[str, ...]
    raw_hosts: Mapping[str, cq.Shape]
    finished_hosts: Mapping[str, cq.Shape]
    raw_candidate_parts: Mapping[str, cq.Shape]
    finished_candidate_parts: Mapping[str, cq.Shape]
    candidate_bores: Mapping[str, wj12.CandidateBore]
    candidate_installed_hardware: Mapping[str, Mapping[str, cq.Shape]]
    replaced_source_axis_ids: frozenset[str]
    replaced_source_cutter_ids: frozenset[str]
    source_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    applied_source_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    purchased_panel_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    purchased_panel_cutters_by_candidate_part: Mapping[
        str, Mapping[str, cq.Shape]
    ]
    additional_finished_source_parts: Mapping[str, cq.Shape]
    additional_purchased_panel_cutters_by_host: Mapping[
        str, Mapping[str, cq.Shape]
    ]
    additional_source_reconstruction: Mapping[str, Mapping[str, Any]]
    source_reconstruction: Mapping[str, Mapping[str, Any]]
    panel_replacements: Mapping[str, cq.Shape]
    fixed_axes: Mapping[str, cq.Shape]
    frame_bolt_records: tuple[Mapping[str, Any], ...]
    frame_bolt_shapes: Mapping[str, cq.Shape]
    protected: Mapping[str, Mapping[str, cq.Shape]]
    absorbed_source_overlay_ids: tuple[str, ...]
    composition_checks: Mapping[str, bool]
    status: str = "unaccepted_integrated_hypothesis"

    @property
    def counts(self) -> dict[str, int]:
        return {
            "target_duties": len(self.target_station_ids),
            "source_hosts": len(self.finished_hosts),
            "replaced_source_sds_axes": len(self.replaced_source_axis_ids),
            "replaced_source_cutter_operations": len(
                self.replaced_source_cutter_ids
            ),
            "candidate_bores": len(self.candidate_bores),
            "candidate_installed_hardware_axes": len(
                self.candidate_installed_hardware
            ),
            "candidate_installed_hardware_components": sum(
                len(roles) for roles in self.candidate_installed_hardware.values()
            ),
            "candidate_parts": len(self.finished_candidate_parts),
            "panel_replacements": len(self.panel_replacements),
            "fixed_panel_axes": len(self.fixed_axes),
            "redirected_panel_receiver_axes": sum(
                len(cuts)
                for cuts in self.purchased_panel_cutters_by_candidate_part.values()
            ),
            "additional_finished_source_parts": len(
                self.additional_finished_source_parts
            ),
            "additional_purchased_panel_receiver_axes": sum(
                len(cuts)
                for cuts in self.additional_purchased_panel_cutters_by_host.values()
            ),
            "retained_frame_bolts": len(self.frame_bolt_records),
            "retained_frame_bolt_installed_components": sum(
                int(row["installed_component_count"])
                for row in self.frame_bolt_records
            ),
            "retained_frame_bolt_source_occupied_axes": sum(
                name.endswith("/source_occupied_axis")
                for name in self.frame_bolt_shapes
            ),
            "retained_frame_bolt_shapes": len(self.frame_bolt_shapes),
            "retained_legacy_clips": len(
                self.protected.get("retained_legacy_clips", {})
            ),
            "retained_legacy_sds_axes": len(
                self.protected.get("retained_legacy_sds_axes", {})
            ),
        }

    @property
    def gates(self) -> dict[str, bool]:
        return {
            "integrated_static_geometry_checked": False,
            "complete_joint_acceptance": False,
            "capacity_established": False,
            "installation_proven": False,
            "fabrication_released": False,
            "structural_released": False,
        }


def _readonly_map(values: Mapping) -> Mapping:
    return MappingProxyType(dict(values))


def _nested_readonly(values: Mapping[str, Mapping]) -> Mapping:
    return MappingProxyType(
        {key: MappingProxyType(dict(rows)) for key, rows in values.items()}
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_hash_map(expected: Mapping[str, str], *, context: str) -> dict[str, str]:
    observed = {}
    for relative_path, digest in expected.items():
        path = ROOT / relative_path
        try:
            current = _sha256_file(path)
        except OSError as error:
            raise ValueError(f"{context} input is missing: {relative_path}") from error
        if current != digest:
            raise ValueError(f"{context} input changed: {relative_path}")
        observed[relative_path] = current
    if not observed:
        raise ValueError(f"{context} input hash map is empty")
    return dict(sorted(observed.items()))


def _normalize_top_inputs(inputs: Mapping[str, str]) -> dict[str, str]:
    """Convert top-producer labels to the paths consumed by shared diagnostics."""
    if set(inputs) != set(top_outer.PRODUCER_HASH_PATHS):
        raise ValueError("top-outer producer input labels differ from its hash contract")
    normalized: dict[str, str] = {}
    for label, digest in inputs.items():
        path = top_outer.PRODUCER_HASH_PATHS.get(label)
        if path is None:
            raise ValueError(f"top-outer producer input label has no path: {label}")
        previous = normalized.get(path)
        if previous is not None and previous != digest:
            raise ValueError(f"top-outer producer path has conflicting hashes: {path}")
        normalized[path] = digest
    return _validate_hash_map(normalized, context="top-outer normalized")


def _read_canonical_inventory(g16: Any, top: Any, binding: Any) -> dict[str, Any]:
    payload = (ROOT / INVENTORY_PATH).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != binding.inventory_sha256:
        raise ValueError("WJ18 inventory differs from the retained source binding")
    inventory = json.loads(payload)
    wj12._inventory_matches_source_binding(inventory, binding)
    if dict(g16.source_inventory) != inventory:
        raise ValueError("WJ16 inventory differs from the canonical source")
    if dict(top.source_inventory) != inventory:
        raise ValueError("top-outer inventory differs from the canonical source")
    if g16.source_inventory_sha256 != digest:
        raise ValueError("WJ16 inventory hash differs from the canonical source")
    return inventory


def _inventory_duties(inventory: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = inventory.get("legacy_duties", ())
    duties = {row["legacy_station_id"]: row for row in rows}
    if len(duties) != len(rows):
        raise ValueError("source inventory duty IDs must be unique")
    return duties


def _expected_source_axes(
    inventory: Mapping[str, Any], target_ids: frozenset[str]
) -> frozenset[str]:
    duties = _inventory_duties(inventory)
    if not target_ids <= duties.keys():
        raise ValueError("WJ18 target duty contract refers to a missing source duty")
    axes = {
        axis["axis_id"]
        for duty_id in target_ids
        for axis in duties[duty_id].get("legacy_sds_axes", ())
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    expected_count = 6 * len(target_ids)
    if len(axes) != expected_count:
        raise ValueError(
            f"target duties must identify exactly {expected_count} source SDS axes"
        )
    return frozenset(axes)


def _validate_geometry_shapes(values: Mapping[str, cq.Shape], *, context: str) -> None:
    wj16._validate_shapes(values, context=context)


def _same_shape_map(
    first: Mapping[str, cq.Shape], second: Mapping[str, cq.Shape], *, context: str
) -> None:
    wj16._validate_shape_map_equal(first, second, context=context)


def _merge_cutter_maps(
    native: Mapping[str, Mapping[str, cq.Shape]],
    purchased: Mapping[str, Mapping[str, cq.Shape]],
    *,
    source_hosts: frozenset[str],
    redirected_rows: Mapping[str, tuple[str, str]],
) -> dict[str, dict[str, cq.Shape]]:
    if set(native) != source_hosts or set(purchased) != source_hosts:
        raise ValueError("WJ18 native and purchase maps must cover the same 14 hosts")
    result = {host: dict(native[host]) for host in source_hosts}
    for host in source_hosts:
        purchase = dict(purchased[host])
        overlap = set(result[host]) & set(purchase)
        if overlap:
            raise ValueError(
                f"{host}: native and purchased panel cut IDs overlap: {sorted(overlap)}"
            )
        result[host].update(purchase)
    for axis_id, (source_host, candidate_host) in redirected_rows.items():
        if source_host not in source_hosts or candidate_host not in EXPECTED_CANDIDATE_PART_IDS:
            raise ValueError(f"{axis_id}: unsupported fixed-axis receiver redirect")
        source_cuts = result[source_host]
        axis_cutter = source_cuts.pop(axis_id, None)
        purchase_cutter = source_cuts.pop(f"panel_purchase/{axis_id}", None)
        if axis_cutter is None:
            raise ValueError(f"{axis_id}: redirected source axis cutter is missing")
        if purchase_cutter is not None:
            raise ValueError(f"{axis_id}: redirected purchase cutter was not filtered")
    return result


def _candidate_axis_station_contract(
    geometry_axes: Mapping[str, Any],
) -> dict[str, str]:
    result = dict(TOP_AXIS_STATION_IDS)
    result.update(dict(wj16_diagnostic.WJ16_LAYOUT.expected_candidate_axis_station_ids))
    for axis_id, station_id in TOP_AXIS_STATION_IDS.items():
        axis = geometry_axes.get(axis_id)
        if axis is None or getattr(axis, "station_id", None) != station_id:
            raise ValueError(f"{axis_id}: top candidate station binding changed")
    return result


def _top_candidate_inputs(top: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    bores = dict(top.candidate_bores)
    hardware = dict(top.candidate_installed_hardware)
    if set(bores) != TOP_CANDIDATE_AXIS_IDS:
        raise ValueError("top-outer candidate bore IDs differ from the exact 8-axis contract")
    if set(hardware) != TOP_CANDIDATE_AXIS_IDS:
        raise ValueError("top-outer installed hardware IDs differ from the exact 8-axis contract")
    for axis_id, station_id in TOP_AXIS_STATION_IDS.items():
        axis = bores[axis_id]
        if (
            getattr(axis, "axis_id", None) != axis_id
            or getattr(axis, "station_id", None) != station_id
            or getattr(axis, "trial_id", None) != top_outer.TRIAL_ID
        ):
            raise ValueError(f"{axis_id}: top candidate bore provenance changed")
        receivers = tuple(getattr(axis, "receiver_ids", ()))
        if len(receivers) != 2 or len(set(receivers)) != 2:
            raise ValueError(f"{axis_id}: top candidate bore must have two receivers")
        if not set(receivers) <= (EXPECTED_SOURCE_HOST_IDS | TOP_CANDIDATE_PART_IDS):
            raise ValueError(f"{axis_id}: top candidate bore names an unknown receiver")
        roles = hardware[axis_id]
        if set(roles) != set(top_outer.ORDINARY_COMPONENT_ROLES):
            raise ValueError(f"{axis_id}: top ordinary hardware role map changed")
        _validate_geometry_shapes(roles, context=f"top hardware/{axis_id}")
    if set(top.raw_candidate_parts) != TOP_CANDIDATE_PART_IDS:
        raise ValueError("top raw cleat IDs differ from the exact two-part contract")
    if set(top.finished_candidate_parts) != TOP_CANDIDATE_PART_IDS:
        raise ValueError("top finished cleat IDs differ from the exact two-part contract")
    _validate_geometry_shapes(top.raw_candidate_parts, context="top raw cleats")
    _validate_geometry_shapes(top.finished_candidate_parts, context="top finished cleats")
    return bores, hardware


def _validate_wj16_base(g16: Any) -> None:
    if g16.layout_id != wj16.LAYOUT_ID or g16.trial_id != wj16.TRIAL_ID:
        raise ValueError("WJ18 requires the fixed retained WJ16 composition")
    if set(g16.target_station_ids) != wj16.EXPECTED_TARGET_DUTY_IDS:
        raise ValueError("WJ16 target duty IDs differ from their exact contract")
    if set(g16.finished_hosts) != wj16.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ16 host IDs differ from their exact thirteen-host contract")
    if set(g16.raw_hosts) != wj16.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ16 raw host IDs differ from their exact contract")
    if set(g16.candidate_bores) != wj16.EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ16 candidate axis IDs differ from their exact contract")
    if set(g16.candidate_installed_hardware) != wj16.EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ16 installed hardware IDs differ from their exact contract")
    if set(g16.raw_candidate_parts) != wj16.EXPECTED_CANDIDATE_PART_IDS:
        raise ValueError("WJ16 raw candidate part IDs differ from their exact contract")
    if set(g16.finished_candidate_parts) != wj16.EXPECTED_CANDIDATE_PART_IDS:
        raise ValueError("WJ16 finished candidate part IDs differ from their exact contract")
    if len(g16.candidate_bores) != wj16.EXPECTED_CANDIDATE_AXIS_COUNT:
        raise ValueError("WJ16 must retain 72 candidate axes")
    if sum(map(len, g16.candidate_installed_hardware.values())) != wj16.EXPECTED_INSTALLED_COMPONENT_COUNT:
        raise ValueError("WJ16 must retain 360 candidate hardware CAD roles")


def compose_wj18_geometry(g16: Any, top: Any) -> WJ18ComposedGeometry:
    """Merge retained WJ16 and top-outer geometry without family rebuilds.

    This function performs the shared-host CAD cut pass. It must run only in
    the parent's serialized geometry slot after both input geometries exist.
    """
    _validate_wj16_base(g16)
    source = g16.source
    binding = validate_source_binding(source)
    if binding != g16.source_binding or binding != top.source_binding:
        raise ValueError("WJ16 and top-outer source bindings differ")
    if top.source is not source:
        raise ValueError("WJ16 and top-outer geometry must share one source object")
    inventory = _read_canonical_inventory(g16, top, binding)

    if top.trial_id != top_outer.TRIAL_ID:
        raise ValueError("top-outer trial identity differs from its fixed contract")
    if set(top.duties) != top_outer.TARGET_DUTY_IDS:
        raise ValueError("top-outer target duties differ from their exact two-duty contract")
    if set(top.retained_candidate_axis_ids) != set(g16.candidate_bores):
        raise ValueError("top-outer retained candidate axes do not match WJ16")
    if set(top.retained_target_duty_ids) != set(g16.target_station_ids):
        raise ValueError("top-outer retained target duties do not match WJ16")
    if top.context_variant != "wj16":
        raise ValueError("top-outer integration must consume the retained WJ16 context")

    top_bores, top_hardware = _top_candidate_inputs(top)
    expected_top_source_axes = _expected_source_axes(inventory, top_outer.TARGET_DUTY_IDS)
    if frozenset(top.replaced_source_axis_ids) != expected_top_source_axes:
        raise ValueError("top-outer replaced source axes differ from the inventory duties")
    replaced_source_axes = frozenset(g16.replaced_source_axis_ids) | expected_top_source_axes
    expected_all_source_axes = _expected_source_axes(inventory, EXPECTED_TARGET_DUTY_IDS)
    if replaced_source_axes != expected_all_source_axes:
        raise ValueError("WJ18 replaced source axes differ from the exact 108-axis contract")

    target_rows = _inventory_duties(inventory)
    expected_hosts = frozenset(
        host
        for duty_id in EXPECTED_TARGET_DUTY_IDS
        for host in target_rows[duty_id]["legacy_host_members"]
    )
    if expected_hosts != EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ18 target duty host union differs from the exact fourteen hosts")

    current_top_inputs = _normalize_top_inputs(top.source_inputs_sha256)
    family_fingerprints = {
        family: dict(rows)
        for family, rows in g16.family_source_fingerprints.items()
    }
    if "top_outer" in family_fingerprints:
        raise ValueError("WJ16 source fingerprint map already contains top-outer inputs")
    family_fingerprints["top_outer"] = current_top_inputs
    merged_inputs: dict[str, str] = {}
    for family, rows in family_fingerprints.items():
        current = _validate_hash_map(rows, context=f"WJ18 {family}")
        for path, digest in current.items():
            prior = merged_inputs.get(path)
            if prior is not None and prior != digest:
                raise ValueError(f"WJ18 family input hashes conflict: {path}")
            merged_inputs[path] = digest

    family_trials = dict(g16.family_trial_ids)
    if dict(top.family_trial_ids) != family_trials:
        raise ValueError("top-outer retained family trial IDs differ from WJ16")
    family_trials["top_outer"] = top_outer.TRIAL_ID

    candidate_bores = dict(g16.candidate_bores)
    if set(candidate_bores) & set(top_bores):
        raise ValueError("WJ16 and top candidate axis IDs collide")
    candidate_bores.update(top_bores)
    candidate_hardware = {
        axis_id: dict(roles)
        for axis_id, roles in g16.candidate_installed_hardware.items()
    }
    if set(candidate_hardware) & set(top_hardware):
        raise ValueError("WJ16 and top installed hardware axis IDs collide")
    candidate_hardware.update(top_hardware)
    if set(candidate_bores) != EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ18 candidate bore IDs differ from the exact 80-axis contract")
    if set(candidate_hardware) != EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ18 installed hardware IDs differ from the exact contract")
    if sum(len(roles) for roles in candidate_hardware.values()) != EXPECTED_INSTALLED_COMPONENT_COUNT:
        raise ValueError("WJ18 must contain exactly 400 installed hardware CAD roles")
    axis_station_ids = _candidate_axis_station_contract(candidate_bores)
    expected_axis_station_bindings = dict(
        wj16_diagnostic.WJ16_LAYOUT.expected_candidate_axis_station_ids
    )
    expected_axis_station_bindings.update(TOP_AXIS_STATION_IDS)
    if axis_station_ids != expected_axis_station_bindings:
        raise ValueError("WJ18 explicit candidate station bindings differ from its contract")

    raw_candidates = dict(g16.raw_candidate_parts)
    finished_candidates = dict(g16.finished_candidate_parts)
    if set(raw_candidates) & TOP_CANDIDATE_PART_IDS:
        raise ValueError("WJ16 and top candidate part IDs collide")
    raw_candidates.update(dict(top.raw_candidate_parts))
    finished_candidates.update(dict(top.finished_candidate_parts))
    if (
        set(raw_candidates) != EXPECTED_CANDIDATE_PART_IDS
        or set(finished_candidates) != EXPECTED_CANDIDATE_PART_IDS
        or len(raw_candidates) != EXPECTED_CANDIDATE_PART_COUNT
    ):
        raise ValueError("WJ18 candidate part IDs differ from the exact 22-part contract")

    # Validate the four panel-receiver redirects already present in the WJ16
    # composition and leave their backer cuts attached to the candidate parts.
    redirected_rows = {
        row["axis_id"]: (
            row["source_finished_receiver_member"],
            row["candidate_finished_receiver_member"],
        )
        for row in inventory.get("fixed_panel_kicker_screws", ())
        if row.get("candidate_finished_receiver_member")
        != row.get("source_finished_receiver_member")
    }
    candidate_panel_cuts = {
        part: dict(cuts)
        for part, cuts in g16.purchased_panel_cutters_by_candidate_part.items()
    }
    if set(redirected_rows) != {
        axis_id for cuts in candidate_panel_cuts.values() for axis_id in cuts
    }:
        raise ValueError("WJ16 redirected fixed-axis purchase cuts changed")
    if len(redirected_rows) != 4:
        raise ValueError("WJ18 must preserve exactly four redirected panel receiver cuts")
    for part, cuts in top.candidate_panel_purchase_cutters_by_part.items():
        if not cuts:
            continue
        if part not in TOP_CANDIDATE_PART_IDS or part in candidate_panel_cuts:
            raise ValueError(f"top candidate purchase-cut receiver is unexpected: {part}")
        candidate_panel_cuts[part] = dict(cuts)

    # Reuse the already retained WJ16 maps. The top rail's WJ16 overlay is
    # checked against the top producer, then absorbed as a regular source host.
    native = {host: dict(cuts) for host, cuts in g16.source_cutters_by_host.items()}
    if set(native) != wj16.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ16 native source cutter map differs from its thirteen hosts")
    top_native = {host: dict(cuts) for host, cuts in top.source_native_cutters_by_host.items()}
    if set(top_native) != set(top_outer.HOST_IDS):
        raise ValueError("top-outer native cutter map differs from its three hosts")
    for host in set(wj16.EXPECTED_SOURCE_HOST_IDS) & set(top_outer.HOST_IDS):
        _same_shape_map(native[host], top_native[host], context=f"shared native cutters/{host}")
    native["base_rail_top"] = top_native["base_rail_top"]

    purchase = {
        host: dict(cuts) for host, cuts in g16.purchased_panel_cutters_by_host.items()
    }
    if set(purchase) != wj16.EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ16 applied purchase map differs from its thirteen hosts")
    top_purchase = {
        host: dict(cuts)
        for host, cuts in top.source_panel_purchase_cutters_by_host.items()
    }
    if set(top_purchase) != set(top_outer.HOST_IDS):
        raise ValueError("top-outer purchase map differs from its three hosts")
    for host in ("base_side_left", "base_side_right"):
        _same_shape_map(purchase[host], top_purchase[host], context=f"shared panel purchases/{host}")
    previous_top_purchase = g16.additional_purchased_panel_cutters_by_host.get(
        "base_rail_top"
    )
    if previous_top_purchase is None:
        raise ValueError("WJ16 top-rail purchase overlay is missing")
    _same_shape_map(
        previous_top_purchase,
        top_purchase["base_rail_top"],
        context="absorbed top-rail purchase overlay",
    )
    if len(top_purchase["base_rail_top"]) != 4:
        raise ValueError("absorbed top-rail overlay must retain exactly four purchase cuts")
    purchase["base_rail_top"] = top_purchase["base_rail_top"]

    additional_finished = {
        host: shape
        for host, shape in g16.additional_finished_source_parts.items()
        if host in EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS
    }
    additional_purchase = {
        host: dict(cuts)
        for host, cuts in g16.additional_purchased_panel_cutters_by_host.items()
        if host in EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS
    }
    additional_reconstruction = {
        host: dict(row)
        for host, row in g16.additional_source_reconstruction.items()
        if host in EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS
    }
    if (
        set(additional_finished) != set(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
        or set(additional_purchase) != set(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
        or set(additional_reconstruction) != set(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
    ):
        raise ValueError("WJ18 must retain only the two bottom-rail receiver overlays")
    if {
        host: len(cuts) for host, cuts in additional_purchase.items()
    } != EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS:
        raise ValueError("WJ18 bottom-rail overlays must retain exactly four purchase cuts")
    source_overlay_rows = g16.additional_source_reconstruction
    top_overlay_evidence = source_overlay_rows.get("base_rail_top", {})
    if not top_overlay_evidence.get("matches_source_plus_purchase_cuts", False):
        raise ValueError("WJ16 top-rail overlay lacks source-plus-purchase reconstruction evidence")

    applied_cutters = _merge_cutter_maps(
        native,
        purchase,
        source_hosts=frozenset(EXPECTED_SOURCE_HOST_IDS),
        redirected_rows=redirected_rows,
    )
    # The retained WJ16 source maps are an independent check that redirects
    # and purchase extensions were not accidentally restored or lost.
    for host in wj16.EXPECTED_SOURCE_HOST_IDS:
        _same_shape_map(
            applied_cutters[host],
            g16.applied_source_cutters_by_host[host],
            context=f"retained WJ16 applied cutters/{host}",
        )
    replaced_cutter_ids = wj12._replaced_source_cutter_ids(
        applied_cutters, replaced_source_axes
    )

    raw_source_parts = wj12._source_parts(source, "uncut_wood_parts")
    if not EXPECTED_SOURCE_HOST_IDS <= raw_source_parts.keys():
        raise ValueError("canonical raw source is missing one or more WJ18 hosts")
    raw_hosts = dict(g16.raw_hosts)
    raw_hosts["base_rail_top"] = raw_source_parts["base_rail_top"]
    if set(raw_hosts) != EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ18 raw source hosts differ from the exact fourteen-host contract")
    _validate_geometry_shapes(raw_hosts, context="WJ18 raw hosts")

    candidate_bores_by_receiver: dict[str, dict[str, cq.Shape]] = {
        receiver: {} for receiver in EXPECTED_SOURCE_HOST_IDS | EXPECTED_CANDIDATE_PART_IDS
    }
    for axis_id, bore in candidate_bores.items():
        receivers = tuple(getattr(bore, "receiver_ids", ()))
        if len(receivers) != 2 or len(set(receivers)) != 2:
            raise ValueError(f"{axis_id}: candidate bore must declare two receivers")
        missing = set(receivers) - candidate_bores_by_receiver.keys()
        if missing:
            raise ValueError(f"{axis_id}: candidate receivers are missing: {sorted(missing)}")
        shape = getattr(bore, "shape", None)
        if not isinstance(shape, cq.Shape) or not shape.isValid():
            raise ValueError(f"{axis_id}: candidate bore geometry is invalid")
        for receiver in receivers:
            candidate_bores_by_receiver[receiver][axis_id] = shape

    finished_hosts = right_integration.machine_shared_hosts(
        raw_hosts,
        applied_cutters,
        replaced_source_axis_ids=replaced_cutter_ids,
        candidate_bores_by_host={
            host: candidate_bores_by_receiver[host] for host in EXPECTED_SOURCE_HOST_IDS
        },
    )
    if set(finished_hosts) != EXPECTED_SOURCE_HOST_IDS:
        raise ValueError("WJ18 host machining omitted one or more shared source hosts")
    _validate_geometry_shapes(finished_hosts, context="WJ18 finished hosts")

    source_reconstruction = {
        host: dict(row) for host, row in g16.source_reconstruction.items()
    }
    top_reconstruction = dict(top.source_reconstruction).get("base_rail_top")
    if top_reconstruction is None:
        raise ValueError("top-outer source reconstruction omitted the top rail")
    top_reconstruction = dict(top_reconstruction)
    if not top_reconstruction.get("matches_canonical_source_finished_member", False):
        raise ValueError("top-outer top-rail native source reconstruction failed")
    top_reconstruction["matches_source_finished_member"] = True
    source_reconstruction["base_rail_top"] = top_reconstruction
    if set(source_reconstruction) != EXPECTED_SOURCE_HOST_IDS or any(
        not row.get("matches_source_finished_member", False)
        or not isinstance(row.get("symmetric_difference_mm3"), (int, float))
        or not 0
        <= row["symmetric_difference_mm3"]
        <= SOURCE_RECONSTRUCTION_TOLERANCE_MM3
        for row in source_reconstruction.values()
    ):
        raise ValueError("WJ18 source reconstruction evidence must cover fourteen source hosts")

    target_axis_ids_by_duty = {
        duty_id: {
            axis["axis_id"]
            for axis in target_rows[duty_id].get("legacy_sds_axes", ())
            if axis.get("shop_opening_kind") == "sds_wood"
        }
        for duty_id in EXPECTED_TARGET_DUTY_IDS
    }
    retained_duty_ids = set(_inventory_duties(inventory)) - set(
        EXPECTED_TARGET_DUTY_IDS
    )
    expected_retained_axis_ids = {
        axis["axis_id"]
        for duty_id in retained_duty_ids
        for axis in target_rows[duty_id].get("legacy_sds_axes", ())
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    protected = {family: dict(rows) for family, rows in g16.protected.items()}
    retained_clips = dict(protected.get("retained_legacy_clips", {}))
    retained_axes = dict(protected.get("retained_legacy_sds_axes", {}))
    for duty_id in top_outer.TARGET_DUTY_IDS:
        if duty_id not in retained_clips:
            raise ValueError(f"retained top legacy clip is missing before absorption: {duty_id}")
        del retained_clips[duty_id]
        for axis_id in target_axis_ids_by_duty[duty_id]:
            if axis_id not in retained_axes:
                raise ValueError(f"retained top source SDS axis is missing: {axis_id}")
            del retained_axes[axis_id]
    if set(retained_clips) != retained_duty_ids:
        raise ValueError("WJ18 retained legacy clip IDs differ from the exact six-duty set")
    if set(retained_axes) != expected_retained_axis_ids:
        raise ValueError("WJ18 retained legacy SDS IDs differ from the exact 36-axis set")
    protected["retained_legacy_clips"] = retained_clips
    protected["retained_legacy_sds_axes"] = retained_axes

    panel_replacements = dict(g16.panel_replacements)
    fixed_axes = dict(g16.fixed_axes)
    frame_records = tuple(g16.frame_bolt_records)
    frame_shapes = dict(g16.frame_bolt_shapes)
    # Top geometry was built from this exact WJ16 scene; the inventory and all
    # retained physical hardware IDs must still agree before the merge.
    if set(fixed_axes) != {
        row["axis_id"] for row in inventory.get("fixed_panel_kicker_screws", ())
    } or len(fixed_axes) != EXPECTED_FIXED_PANEL_AXIS_COUNT:
        raise ValueError("WJ18 must preserve all 66 fixed panel axes")
    if len(frame_records) != EXPECTED_FRAME_BOLT_COUNT or len(frame_shapes) != EXPECTED_FRAME_BOLT_SHAPE_COUNT:
        raise ValueError("WJ18 frame-bolt record and shape census changed")
    if len(protected["retained_12_frame_bolt_components"]) != EXPECTED_FRAME_BOLT_COMPONENT_COUNT:
        raise ValueError("WJ18 must preserve all 60 installed frame-bolt components")
    if len(protected["retained_12_frame_bolt_tools_withdrawals"]) != 36:
        raise ValueError("WJ18 must preserve all 36 frame-bolt access envelopes")
    if len(retained_clips) != EXPECTED_RETAINED_LEGACY_CLIP_COUNT or len(retained_axes) != EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT:
        raise ValueError("WJ18 retained legacy obstacle census changed")
    if validate_source_binding(source) != binding:
        raise ValueError("WJ18 source binding changed during host composition")

    checks = {
        "exact_wj16_base_contract": True,
        "exact_top_outer_two_duty_contract": True,
        "source_inventory_and_family_hashes_current": True,
        "all_108_source_sds_axes_replaced": len(replaced_source_axes) == EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
        "top_rail_purchase_overlay_absorbed_into_host_map": True,
        "two_bottom_rail_overlays_and_four_cuts_preserved": True,
        "native_and_purchase_maps_remain_distinct": True,
        "four_existing_backer_receiver_redirects_preserved": len(redirected_rows) == 4,
        "all_80_candidate_axes_and_400_cad_roles_preserved": len(candidate_bores) == EXPECTED_CANDIDATE_AXIS_COUNT
        and sum(len(rows) for rows in candidate_hardware.values()) == EXPECTED_INSTALLED_COMPONENT_COUNT,
        "candidate_axis_station_bindings_match_exact_contract": set(axis_station_ids)
        == set(expected_axis_station_bindings)
        and axis_station_ids == expected_axis_station_bindings
        and len(axis_station_ids) == 24,
        "all_14_shared_hosts_rebuilt_from_union_cut_maps_and_bores": set(finished_hosts) == EXPECTED_SOURCE_HOST_IDS,
        "source_reconstruction_evidence_covers_all_14_hosts": len(source_reconstruction) == len(EXPECTED_SOURCE_HOST_IDS),
        "all_66_fixed_axes_and_12_frame_bolts_preserved": len(fixed_axes) == 66 and len(frame_records) == 12,
        "complete_static_clearance_checked": False,
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    if not all(value for key, value in checks.items() if key not in {
        "complete_static_clearance_checked",
        "complete_joint_acceptance",
        "capacity_established",
        "installation_proven",
        "fabrication_released",
        "structural_released",
    }):
        raise ValueError("WJ18 composition evidence failed a required integration check")

    return WJ18ComposedGeometry(
        layout_id=LAYOUT_ID,
        trial_id=TRIAL_ID,
        source=source,
        source_binding=binding,
        source_inventory_sha256=binding.inventory_sha256,
        source_inventory=_readonly_map(inventory),
        family_source_fingerprints=_nested_readonly(family_fingerprints),
        family_trial_ids=_readonly_map(family_trials),
        target_station_ids=tuple(sorted(EXPECTED_TARGET_DUTY_IDS)),
        raw_hosts=_readonly_map(raw_hosts),
        finished_hosts=_readonly_map(finished_hosts),
        raw_candidate_parts=_readonly_map(raw_candidates),
        finished_candidate_parts=_readonly_map(finished_candidates),
        candidate_bores=_readonly_map(candidate_bores),
        candidate_installed_hardware=_nested_readonly(candidate_hardware),
        replaced_source_axis_ids=replaced_source_axes,
        replaced_source_cutter_ids=replaced_cutter_ids,
        source_cutters_by_host=_nested_readonly(native),
        applied_source_cutters_by_host=_nested_readonly(applied_cutters),
        purchased_panel_cutters_by_host=_nested_readonly(purchase),
        purchased_panel_cutters_by_candidate_part=_nested_readonly(candidate_panel_cuts),
        additional_finished_source_parts=_readonly_map(additional_finished),
        additional_purchased_panel_cutters_by_host=_nested_readonly(additional_purchase),
        additional_source_reconstruction=_nested_readonly(additional_reconstruction),
        source_reconstruction=_nested_readonly(source_reconstruction),
        panel_replacements=_readonly_map(panel_replacements),
        fixed_axes=_readonly_map(fixed_axes),
        frame_bolt_records=frame_records,
        frame_bolt_shapes=_readonly_map(frame_shapes),
        protected=_nested_readonly(protected),
        absorbed_source_overlay_ids=tuple(
            sorted(set(g16.absorbed_source_overlay_ids) | {"base_rail_top"})
        ),
        composition_checks=_readonly_map(checks),
    )


def _shape_evidence(shape: cq.Shape) -> dict[str, Any]:
    box = shape.BoundingBox()
    return {
        "bounds_xyz_mm": [
            round(value, 6)
            for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
        ],
        "volume_mm3": round(shape.Volume(), 6),
        "shape_sha256": _source_shape_fingerprint(shape),
    }


def composition_report(geometry: WJ18ComposedGeometry) -> dict[str, Any]:
    """Return source-bound composition evidence without embedding CAD shapes."""
    if geometry.layout_id != LAYOUT_ID or geometry.trial_id != TRIAL_ID:
        raise ValueError("composition report requires the fixed WJ18 layout")
    if validate_source_binding(geometry.source) != geometry.source_binding:
        raise ValueError("WJ18 source binding changed before report creation")
    producer_hashes = {
        name: _sha256_file(ROOT / path)
        for name, path in sorted(PRODUCER_HASH_PATHS.items())
    }
    inventory = geometry.source_inventory
    duty_rows = _inventory_duties(inventory)
    axis_owner = {
        axis["axis_id"]: duty_id
        for duty_id, row in duty_rows.items()
        for axis in row.get("legacy_sds_axes", ())
    }
    return {
        "schema": SCHEMA,
        "layout_id": geometry.layout_id,
        "trial_id": geometry.trial_id,
        "status": geometry.status,
        "claim_boundary": (
            "Source-bound nominal geometry composition only. It does not establish "
            "clearance acceptance, complete joint behavior, access, capacity, installation, "
            "fabrication, inspection, or release."
        ),
        "source": {
            "candidate": inventory.get("candidate"),
            "source_commit": inventory.get("source_commit"),
            "source_inventory_sha256": geometry.source_inventory_sha256,
            "runtime_module_sha256": dict(
                sorted(geometry.source_binding.runtime_module_sha256.items())
            ),
        },
        "producer_hashes_sha256": producer_hashes,
        "family_trial_ids": dict(sorted(geometry.family_trial_ids.items())),
        "family_source_fingerprints_sha256": {
            family: dict(sorted(rows.items()))
            for family, rows in sorted(geometry.family_source_fingerprints.items())
        },
        "counts": geometry.counts,
        "target_duties": [
            {
                "station_id": station_id,
                "legacy_host_members": duty_rows[station_id]["legacy_host_members"],
                "replaced_source_sds_axis_ids": sorted(
                    axis["axis_id"]
                    for axis in duty_rows[station_id].get("legacy_sds_axes", ())
                    if axis.get("shop_opening_kind") == "sds_wood"
                ),
            }
            for station_id in geometry.target_station_ids
        ],
        "source_reconstruction": {
            host: dict(row) for host, row in sorted(geometry.source_reconstruction.items())
        },
        "shared_hosts": {
            host: {
                "raw_shape": _shape_evidence(geometry.raw_hosts[host]),
                "finished_shape": _shape_evidence(geometry.finished_hosts[host]),
                "native_source_cut_ids": sorted(geometry.source_cutters_by_host[host]),
                "applied_source_cut_ids": sorted(geometry.applied_source_cutters_by_host[host]),
                "purchased_panel_cut_ids": sorted(geometry.purchased_panel_cutters_by_host[host]),
            }
            for host in sorted(geometry.finished_hosts)
        },
        "absorbed_top_rail_overlay": {
            "host_id": "base_rail_top",
            "absorbed_into_finished_hosts": "base_rail_top" in geometry.finished_hosts,
            "purchase_cut_ids_applied": sorted(
                geometry.purchased_panel_cutters_by_host["base_rail_top"]
            ),
            "not_retained_as_additional_overlay": "base_rail_top"
            not in geometry.additional_finished_source_parts,
        },
        "remaining_bottom_rail_overlays": {
            host: {
                "finished_shape": _shape_evidence(shape),
                "purchase_cut_ids": sorted(
                    geometry.additional_purchased_panel_cutters_by_host[host]
                ),
                "source_reconstruction": dict(
                    geometry.additional_source_reconstruction[host]
                ),
            }
            for host, shape in sorted(geometry.additional_finished_source_parts.items())
        },
        "replaced_source_axes": [
            {
                "axis_id": axis_id,
                "legacy_station_id": axis_owner.get(axis_id),
                "removed_source_cutter_ids": sorted(
                    cutter_id
                    for cutter_id in geometry.replaced_source_cutter_ids
                    if cutter_id == axis_id or cutter_id == f"{axis_id}/head"
                ),
            }
            for axis_id in sorted(geometry.replaced_source_axis_ids)
        ],
        "candidate_parts": {
            part: {
                "raw_shape": _shape_evidence(geometry.raw_candidate_parts[part]),
                "finished_shape": _shape_evidence(geometry.finished_candidate_parts[part]),
            }
            for part in sorted(geometry.finished_candidate_parts)
        },
        "fixed_inventory": {
            "fixed_panel_axis_ids": sorted(geometry.fixed_axes),
            "frame_bolt_ids": sorted(row["axis_id"] for row in geometry.frame_bolt_records),
            "frame_bolt_shape_ids": sorted(geometry.frame_bolt_shapes),
            "retained_legacy_clip_ids": sorted(
                geometry.protected.get("retained_legacy_clips", {})
            ),
            "retained_legacy_sds_axis_ids": sorted(
                geometry.protected.get("retained_legacy_sds_axes", {})
            ),
        },
        "absorbed_source_overlay_ids": list(geometry.absorbed_source_overlay_ids),
        "composition_checks": dict(geometry.composition_checks),
        "release": {
            "candidate_accepted": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_accepted": False,
            "assembly_proven": False,
        },
    }
