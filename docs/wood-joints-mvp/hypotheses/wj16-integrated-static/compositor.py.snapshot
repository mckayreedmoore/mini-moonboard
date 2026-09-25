"""Compose WJ-16 from the corrected WJ-12 and left-service geometry objects.

This source-bound diagnostic adapter rebuilds the thirteen shared wood hosts
from raw member shapes, source-native cuts, candidate-only purchase cuts, and
the union of the two layouts' candidate bores. It does not materialize either
family, establish fit or capacity, or authorize fabrication.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
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
from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from scripts import wood_joint_left_rail_integration as left_service
from scripts import wood_joint_right_rail_integration as right_integration
from scripts import wood_joint_wj12_compositor as wj12
from scripts.wood_joint_wj12_diagnostic import WJ12_LAYOUT

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj16_compositor/v1"
TRIAL_ID = "wj16-wj12-plus-left-service-four-duty-v1"
LAYOUT_ID = "wj16-sixteen-duty-left-service-composition-v1"
HIT_TOLERANCE_MM3 = 1e-3

LEFT_DUTY_IDS = frozenset(
    {
        "clip_horizontal_lower_left_1",
        "clip_horizontal_upper_left_1",
        "clip_horizontal_lower_left_2",
        "clip_horizontal_upper_left_2",
    }
)
EXPECTED_TARGET_DUTY_IDS = WJ12_LAYOUT.expected_target_duty_ids | LEFT_DUTY_IDS
EXPECTED_SOURCE_HOST_IDS = WJ12_LAYOUT.expected_source_host_ids | frozenset(
    {"base_rail_service_lower_left", "base_rail_service_upper_left"}
)

LEFT_SERVICE_TRIAL_ID = "left_service_mirrored_inner_outer_hypothesis"
LEFT_AXIS_STATION_IDS: dict[str, str] = {}
for _station_id, _stack_ids in {
    "clip_horizontal_lower_left_2": (
        "lower_rail_1",
        "lower_rail_2",
        "lower_principal_1",
        "lower_principal_2",
    ),
    "clip_horizontal_upper_left_2": (
        "upper_rail_1",
        "upper_rail_2",
        "upper_principal_1",
        "upper_principal_2",
    ),
    "clip_horizontal_lower_left_1": (
        "lower_rail_1",
        "lower_rail_2",
        "lower_side_1",
        "lower_side_2",
    ),
    "clip_horizontal_upper_left_1": (
        "upper_rail_1",
        "upper_rail_2",
        "upper_side_1",
        "upper_side_2",
    ),
}.items():
    for _stack_id in _stack_ids:
        LEFT_AXIS_STATION_IDS[
            f"left_service/{LEFT_SERVICE_TRIAL_ID}/{_station_id}/{_stack_id}"
        ] = _station_id
EXPECTED_LEFT_CANDIDATE_AXIS_IDS = frozenset(LEFT_AXIS_STATION_IDS)
EXPECTED_CANDIDATE_AXIS_IDS = (
    WJ12_LAYOUT.expected_candidate_axis_ids | EXPECTED_LEFT_CANDIDATE_AXIS_IDS
)
EXPECTED_LEFT_CANDIDATE_PART_IDS = frozenset(
    {
        "left_service_inner_lower_cleat",
        "left_service_inner_upper_cleat",
        "left_service_outer_lower_cleat",
        "left_service_outer_upper_cleat",
    }
)
EXPECTED_CANDIDATE_PART_IDS = (
    WJ12_LAYOUT.expected_candidate_part_ids | EXPECTED_LEFT_CANDIDATE_PART_IDS
)
EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS = {
    "base_rail_top": 4,
    "base_rail_bottom_left": 2,
    "base_rail_bottom_right": 2,
}
EXPECTED_REPLACED_SOURCE_AXIS_COUNT = 96
EXPECTED_RETAINED_LEGACY_CLIP_COUNT = 8
EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT = 48
EXPECTED_CANDIDATE_AXIS_COUNT = 72
EXPECTED_CANDIDATE_PART_COUNT = 20
EXPECTED_INSTALLED_COMPONENT_COUNT = 360
EXPECTED_PANEL_AXIS_COUNT = 66
EXPECTED_FRAME_BOLT_COUNT = 12
EXPECTED_FRAME_BOLT_INSTALLED_COMPONENT_COUNT = 60
EXPECTED_FRAME_BOLT_SOURCE_AXIS_COUNT = 12
EXPECTED_FRAME_BOLT_SHAPE_COUNT = 72
SOURCE_RECONSTRUCTION_TOLERANCE_MM3 = 1e-3

PRODUCER_HASH_PATHS = {
    "wj16_compositor": "scripts/wood_joint_wj16_compositor.py",
    "wj16_diagnostic": "scripts/wood_joint_wj16_diagnostic.py",
    "wj12_compositor": "scripts/wood_joint_wj12_compositor.py",
    "wj12_diagnostic": "scripts/wood_joint_wj12_diagnostic.py",
    "left_service": "scripts/wood_joint_left_rail_integration.py",
}


@dataclass(frozen=True)
class WJ16ComposedGeometry:
    """One source-bound sixteen-duty diagnostic composition."""

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
    purchased_panel_cutters_by_candidate_part: Mapping[str, Mapping[str, cq.Shape]]
    additional_finished_source_parts: Mapping[str, cq.Shape]
    additional_purchased_panel_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    additional_source_reconstruction: Mapping[str, Mapping[str, Any]]
    source_reconstruction: Mapping[str, Mapping[str, Any]]
    panel_replacements: Mapping[str, cq.Shape]
    fixed_axes: Mapping[str, cq.Shape]
    frame_bolt_records: tuple[Mapping[str, Any], ...]
    frame_bolt_shapes: Mapping[str, cq.Shape]
    protected: Mapping[str, Mapping[str, cq.Shape]]
    absorbed_source_overlay_ids: tuple[str, ...]
    status: str = "unaccepted_integrated_hypothesis"

    @property
    def counts(self) -> dict[str, int]:
        return {
            "target_duties": len(self.target_station_ids),
            "source_hosts": len(self.finished_hosts),
            "replaced_source_sds_axes": len(self.replaced_source_axis_ids),
            "replaced_source_cutter_operations": len(self.replaced_source_cutter_ids),
            "candidate_bores": len(self.candidate_bores),
            "candidate_installed_hardware_axes": len(self.candidate_installed_hardware),
            "candidate_installed_hardware_components": sum(
                len(components)
                for components in self.candidate_installed_hardware.values()
            ),
            "candidate_parts": len(self.finished_candidate_parts),
            "panel_replacements": len(self.panel_replacements),
            "fixed_panel_axes": len(self.fixed_axes),
            "redirected_panel_receiver_axes": sum(
                len(cutters)
                for cutters in self.purchased_panel_cutters_by_candidate_part.values()
            ),
            "additional_finished_source_parts": len(
                self.additional_finished_source_parts
            ),
            "additional_purchased_panel_receiver_axes": sum(
                len(cutters)
                for cutters in self.additional_purchased_panel_cutters_by_host.values()
            ),
            "retained_frame_bolts": len(self.frame_bolt_records),
            "retained_frame_bolt_installed_components": sum(
                int(row["installed_component_count"]) for row in self.frame_bolt_records
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
            "cross_family_clearance_checked": False,
            "complete_joint_acceptance": False,
            "capacity_established": False,
            "installation_proven": False,
            "fabrication_released": False,
            "structural_released": False,
        }


def _readonly_map(values: Mapping) -> Mapping:
    return MappingProxyType(dict(values))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_hash_map(expected: Mapping[str, str], *, context: str) -> dict[str, str]:
    observed = {}
    for relative_path, digest in expected.items():
        path = ROOT / relative_path
        try:
            current = _sha256_file(path)
        except OSError as error:
            raise ValueError(
                f"{context} source input missing: {relative_path}"
            ) from error
        if current != digest:
            raise ValueError(f"{context} source input changed: {relative_path}")
        observed[relative_path] = current
    if not observed:
        raise ValueError(f"{context} source input hash map is empty")
    return dict(sorted(observed.items()))


def _canonical_inventory(
    right_geometry: Any, left_geometry: Any, binding: Any
) -> dict[str, Any]:
    payload = (ROOT / INVENTORY_PATH).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != binding.inventory_sha256:
        raise ValueError("WJ16 source inventory differs from the pinned source binding")
    inventory = json.loads(payload)
    wj12._inventory_matches_source_binding(inventory, binding)
    if dict(right_geometry.source_inventory) != inventory:
        raise ValueError(
            "WJ12 source inventory content differs from the canonical file"
        )
    if dict(left_geometry.inventory) != inventory:
        raise ValueError(
            "left-service source inventory content differs from the canonical file"
        )
    if (
        len(inventory.get("legacy_duties", ())) != 24
        or sum(
            len(row.get("legacy_sds_axes", ())) for row in inventory["legacy_duties"]
        )
        != 144
        or len(inventory.get("fixed_panel_kicker_screws", ()))
        != EXPECTED_PANEL_AXIS_COUNT
        or len(inventory.get("starting_frame_bolts", ())) != EXPECTED_FRAME_BOLT_COUNT
    ):
        raise ValueError("WJ16 pinned inventory duty or fixed-axis counts changed")
    return inventory


def _duty_rows(inventory: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    duties = inventory.get("legacy_duties", ())
    rows = {row["legacy_station_id"]: row for row in duties}
    if len(rows) != len(duties):
        raise ValueError("legacy duty station IDs must be unique")
    return rows


def expected_replaced_source_axes(
    inventory: Mapping[str, Any], target_station_ids: frozenset[str]
) -> frozenset[str]:
    rows = _duty_rows(inventory)
    if not target_station_ids <= rows.keys():
        raise ValueError("WJ16 target duty contract refers to a missing inventory duty")
    axes = [
        axis["axis_id"]
        for station_id in target_station_ids
        for axis in rows[station_id].get("legacy_sds_axes", ())
        if axis.get("shop_opening_kind") == "sds_wood"
    ]
    if len(axes) != EXPECTED_REPLACED_SOURCE_AXIS_COUNT or len(set(axes)) != len(axes):
        raise ValueError("WJ16 source duty contract must identify 96 unique SDS axes")
    return frozenset(axes)


def expected_source_hosts(
    inventory: Mapping[str, Any], target_station_ids: frozenset[str]
) -> frozenset[str]:
    rows = _duty_rows(inventory)
    if not target_station_ids <= rows.keys():
        raise ValueError("WJ16 target duty contract refers to a missing inventory duty")
    hosts = frozenset(
        host_id
        for station_id in target_station_ids
        for host_id in rows[station_id].get("legacy_host_members", ())
    )
    if hosts != EXPECTED_SOURCE_HOST_IDS:
        raise ValueError(
            "WJ16 target duties no longer map to the exact thirteen source hosts"
        )
    return hosts


def _shape_map(value: Any, attribute: str, context: str) -> Mapping[str, cq.Shape]:
    result = getattr(value, attribute, None)
    if not isinstance(result, Mapping):
        raise TypeError(f"{context}.{attribute} must be a shape map")
    return result


def _validate_shapes(rows: Mapping[str, cq.Shape], *, context: str) -> None:
    invalid = [
        name
        for name, shape in rows.items()
        if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids()
    ]
    if invalid:
        raise ValueError(f"{context} has invalid solids: {sorted(invalid)}")


def _validate_shape_map_equal(
    first: Mapping[str, cq.Shape],
    second: Mapping[str, cq.Shape],
    *,
    context: str,
) -> None:
    if set(first) != set(second):
        raise ValueError(f"{context} IDs differ")
    different = [
        name
        for name in first
        if _source_shape_fingerprint(first[name])
        != _source_shape_fingerprint(second[name])
    ]
    if different:
        raise ValueError(f"{context} geometry differs: {sorted(different)}")


def _verify_wj12_base(geometry: Any) -> None:
    if geometry.trial_id != wj12.TRIAL_ID:
        raise ValueError("WJ16 requires the corrected WJ12 base trial")
    if geometry.status != "unaccepted_integrated_hypothesis":
        raise ValueError("WJ16 requires the unaccepted WJ12 hypothesis status")
    if set(geometry.target_station_ids) != set(WJ12_LAYOUT.expected_target_duty_ids):
        raise ValueError(
            "WJ12 base duty IDs differ from the fixed twelve-duty contract"
        )
    if set(geometry.finished_hosts) != set(WJ12_LAYOUT.expected_source_host_ids):
        raise ValueError(
            "WJ12 base host IDs differ from its fixed eleven-host contract"
        )
    if set(geometry.candidate_bores) != set(WJ12_LAYOUT.expected_candidate_axis_ids):
        raise ValueError("WJ12 base candidate-axis IDs differ from its fixed contract")
    if set(geometry.candidate_installed_hardware) != set(
        WJ12_LAYOUT.expected_candidate_axis_ids
    ):
        raise ValueError(
            "WJ12 base installed-hardware axes differ from its fixed contract"
        )
    if set(geometry.finished_candidate_parts) != set(
        WJ12_LAYOUT.expected_candidate_part_ids
    ):
        raise ValueError("WJ12 base candidate-part IDs differ from its fixed contract")
    if set(geometry.raw_candidate_parts) != set(
        WJ12_LAYOUT.expected_candidate_part_ids
    ):
        raise ValueError("WJ12 raw candidate-part IDs differ from its fixed contract")


def _merge_candidate_axis_maps(
    base_axes: Mapping[str, Any], left_axes: Mapping[str, Any]
) -> dict[str, Any]:
    """Merge exact WJ12 and left axis identities before any CAD operation."""
    if set(base_axes) != set(WJ12_LAYOUT.expected_candidate_axis_ids):
        raise ValueError("WJ12 candidate axes differ from the fixed base contract")
    if set(left_axes) != EXPECTED_LEFT_CANDIDATE_AXIS_IDS:
        raise ValueError(
            "left candidate axes differ from the exact sixteen-axis contract"
        )
    duplicate = set(base_axes) & set(left_axes)
    if duplicate:
        raise ValueError(
            f"WJ12 and left candidate axis IDs collide: {sorted(duplicate)}"
        )
    for axis_id, expected_station in LEFT_AXIS_STATION_IDS.items():
        axis = left_axes[axis_id]
        station = getattr(axis, "station_id", None)
        if station != expected_station:
            raise ValueError(f"{axis_id} is assigned to the wrong left duty")
    result = {**base_axes, **left_axes}
    if set(result) != EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError("WJ16 candidate axes differ from its exact 72-axis contract")
    return result


def _left_candidate_bores(geometry: Any) -> dict[str, wj12.CandidateBore]:
    stacks = _shape_map(geometry, "stacks", "left service")
    bores = _shape_map(geometry, "bores", "left service")
    installed = _shape_map(geometry, "installed", "left service")
    members = _shape_map(geometry, "bore_members", "left service")
    provenance = _shape_map(geometry, "stack_provenance", "left service")
    expected_ids = EXPECTED_LEFT_CANDIDATE_AXIS_IDS
    if set(stacks) != expected_ids or set(bores) != expected_ids:
        raise ValueError("left source stacks and bores differ from exact WJ16 axes")
    if set(installed) != expected_ids or set(members) != expected_ids:
        raise ValueError(
            "left installed hardware and receiver maps differ from WJ16 axes"
        )
    if set(provenance) != expected_ids:
        raise ValueError("left stack provenance differs from exact WJ16 axes")
    result = {}
    for axis_id in sorted(expected_ids):
        stack = stacks[axis_id]
        station_id = provenance[axis_id].get("target_station_id")
        if station_id != LEFT_AXIS_STATION_IDS[axis_id]:
            raise ValueError(f"{axis_id} left duty provenance changed")
        receiver_ids = tuple(members[axis_id])
        expected_receivers = tuple(layer.body_id for layer in stack.layers)
        if receiver_ids != expected_receivers or len(set(receiver_ids)) != 2:
            raise ValueError(
                f"{axis_id} left bore receivers differ from its bolt stack"
            )
        result[axis_id] = wj12.CandidateBore(
            axis_id=axis_id,
            family="left_service",
            trial_id=geometry.trial_ids["left_service"],
            receiver_ids=receiver_ids,
            shape=bores[axis_id],
            station_id=station_id,
        )
    return result


def _panel_cutters_by_host(
    source: Any,
    inventory: Mapping[str, Any],
    host_ids: frozenset[str],
) -> dict[str, dict[str, cq.Shape]]:
    return right_integration.candidate_panel_purchase_cutters_by_host(
        source, dict(inventory), host_ids
    )


def _source_reconstruction_rows(
    right_geometry: Any,
    left_geometry: Any,
    new_host_ids: frozenset[str],
) -> dict[str, dict[str, Any]]:
    rows = {
        name: dict(value)
        for name, value in right_geometry.source_reconstruction.items()
    }
    left_rows = left_geometry.source_reconstruction
    for host_id in new_host_ids:
        row = left_rows.get(host_id)
        if row is None:
            raise ValueError(f"left-service reconstruction omitted new host {host_id}")
        if not isinstance(row, Mapping):
            raise TypeError(f"left-service reconstruction row is invalid: {host_id}")
        rows[host_id] = dict(row)
    if set(rows) != EXPECTED_SOURCE_HOST_IDS:
        raise ValueError(
            "WJ16 source reconstruction evidence must cover exactly 13 hosts"
        )
    if any(
        not row.get("matches_source_finished_member", False)
        or not isinstance(row.get("symmetric_difference_mm3"), (int, float))
        or not 0
        <= row["symmetric_difference_mm3"]
        <= SOURCE_RECONSTRUCTION_TOLERANCE_MM3
        for row in rows.values()
    ):
        raise ValueError(
            "WJ16 source-bound native reconstruction evidence is incomplete"
        )
    return rows


def _retained_legacy_parts(
    source: Any,
    inventory: Mapping[str, Any],
    replaced_axis_ids: frozenset[str],
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape]]:
    duty_rows = _duty_rows(inventory)
    retained_duty_ids = set(duty_rows) - EXPECTED_TARGET_DUTY_IDS
    if len(retained_duty_ids) != EXPECTED_RETAINED_LEGACY_CLIP_COUNT:
        raise ValueError("WJ16 must retain exactly eight legacy connector clips")
    current_parts = wj12._source_parts(source, "parts")
    clips = {
        name: current_parts[name]
        for name in sorted(retained_duty_ids)
        if name in current_parts
    }
    if set(clips) != retained_duty_ids:
        raise ValueError("source model omitted one or more retained legacy clips")

    all_axis_rows = {
        axis["axis_id"]
        for row in inventory.get("legacy_duties", ())
        for axis in row.get("legacy_sds_axes", ())
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    retained_ids = all_axis_rows - set(replaced_axis_ids)
    connection_by_id = {row.name: row for row in source.connections()}
    if len(connection_by_id) != len(tuple(source.connections())):
        raise ValueError("source connection axis IDs must be unique")
    axes = {}
    for axis_id in sorted(retained_ids):
        connection = connection_by_id.get(axis_id)
        if connection is None:
            raise ValueError(f"retained source SDS axis is missing: {axis_id}")
        axes[axis_id] = right_integration._source_screw_axis_shape(connection)
    if len(axes) != EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT:
        raise ValueError("WJ16 must retain exactly 48 legacy SDS axes")
    return clips, axes


def _protected_map(
    left_geometry: Any,
    retained_clips: Mapping[str, cq.Shape],
    retained_axes: Mapping[str, cq.Shape],
    frame_bolt_shapes: Mapping[str, cq.Shape],
) -> dict[str, dict[str, cq.Shape]]:
    protected = {
        family: dict(shapes) for family, shapes in left_geometry.protected.items()
    }
    for family, values in (
        ("retained_legacy_clips", retained_clips),
        ("retained_legacy_sds_axes", retained_axes),
    ):
        protected[family] = dict(values)
    if len(protected["fixed_66_hillman_axes_63p5mm"]) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError("WJ16 must preserve all 66 fixed Hillman axis envelopes")
    if (
        len(protected["retained_12_frame_bolt_components"])
        != EXPECTED_FRAME_BOLT_INSTALLED_COMPONENT_COUNT
    ):
        raise ValueError("WJ16 must preserve all 60 installed frame-bolt components")
    if len(protected["retained_12_frame_bolt_tools_withdrawals"]) != 36:
        raise ValueError("WJ16 frame-bolt access envelope count changed")
    if len(protected["retained_legacy_clips"]) != EXPECTED_RETAINED_LEGACY_CLIP_COUNT:
        raise ValueError("WJ16 retained clip map must contain exactly eight duties")
    if (
        len(protected["retained_legacy_sds_axes"])
        != EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT
    ):
        raise ValueError("WJ16 retained SDS map must contain exactly 48 axes")
    frame_aliases = protected["retained_12_frame_bolt_components"]
    roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    axis_ids = {
        row["axis_id"] for row in left_geometry.inventory["starting_frame_bolts"]
    }
    expected_alias_ids = {f"{axis_id}/{role}" for axis_id in axis_ids for role in roles}
    expected_installed_ids = {
        f"{axis_id}/installed_component_{index}"
        for axis_id in axis_ids
        for index in range(1, 6)
    }
    installed_frame_components = {
        name: shape
        for name, shape in frame_bolt_shapes.items()
        if name in expected_installed_ids
    }
    if (
        set(frame_aliases) != expected_alias_ids
        or set(installed_frame_components) != expected_installed_ids
    ):
        raise ValueError(
            "WJ16 protected frame-bolt component aliases differ from the fixed IDs"
        )
    _validate_shapes(frame_aliases, context="WJ16 protected frame-bolt aliases")
    _validate_shapes(
        installed_frame_components,
        context="WJ16 installed frame-bolt components",
    )
    for axis_id in sorted(axis_ids):
        alias_fingerprints = Counter(
            _source_shape_fingerprint(frame_aliases[f"{axis_id}/{role}"])
            for role in roles
        )
        installed_fingerprints = Counter(
            _source_shape_fingerprint(
                installed_frame_components[f"{axis_id}/installed_component_{index}"]
            )
            for index in range(1, 6)
        )
        if alias_fingerprints != installed_fingerprints:
            raise ValueError(
                f"{axis_id}: protected frame-bolt aliases differ from installed shapes"
            )
    return protected


def _validate_panel_surface(
    replacements: Mapping[str, cq.Shape],
    family_panels: Mapping[str, cq.Shape],
    source_parts: Mapping[str, cq.Shape],
) -> None:
    """Reconcile three replacement panels with a complete six-panel scene."""
    left_ids = {name.removesuffix("_right") + "_left" for name in RIGHT_PANEL_NAMES}
    if set(replacements) != RIGHT_PANEL_NAMES:
        raise ValueError("WJ16 must preserve the three right-panel replacements")
    if set(family_panels) != RIGHT_PANEL_NAMES | left_ids:
        raise ValueError("left service panel map must contain the exact six panels")
    if not left_ids <= source_parts.keys():
        raise ValueError("source is missing a canonical left panel")
    expected = {name: source_parts[name] for name in left_ids}
    expected.update(replacements)
    _validate_shape_map_equal(expected, family_panels, context="WJ16 panel surface")


def compose_wj16_geometry(
    right_geometry: Any,
    left_geometry: Any,
) -> WJ16ComposedGeometry:
    """Compose retained WJ12 and left-service objects without rematerializing.

    This method performs host CAD booleans, so call it only in the serialized
    geometry slot. It does not build family geometry or write report files.
    """
    _verify_wj12_base(right_geometry)
    source = right_geometry.source
    if left_geometry.source is not source:
        raise ValueError(
            "WJ12 and left-service geometries must share one source object"
        )
    binding = validate_source_binding(source)
    if (
        binding != right_geometry.source_binding
        or binding != left_geometry.source_binding
    ):
        raise ValueError("WJ16 family source bindings differ")
    if right_geometry.source_inventory_sha256 != binding.inventory_sha256:
        raise ValueError("WJ12 source inventory hash differs from the live binding")
    inventory = _canonical_inventory(right_geometry, left_geometry, binding)
    rows = _duty_rows(inventory)
    if set(left_geometry.duties) != LEFT_DUTY_IDS:
        raise ValueError(
            "left-service geometry does not cover the exact four WJ16 duties"
        )
    if set(left_geometry.trial_ids) != {
        "wj04_g7",
        "wj06_outer_pair",
        "left_service",
    }:
        raise ValueError("left-service family trial IDs changed")
    for family in ("wj04_g7", "wj06_outer_pair"):
        if left_geometry.trial_ids[family] != right_geometry.family_trial_ids.get(
            family
        ):
            raise ValueError(f"left-service {family} trial differs from WJ12 base")
    if left_geometry.trial_ids["left_service"] != LEFT_SERVICE_TRIAL_ID:
        raise ValueError(
            "left-service trial identity differs from the fixed WJ16 contract"
        )
    if set(right_geometry.target_station_ids) & LEFT_DUTY_IDS:
        raise ValueError("left-service duties overlap WJ12's twelve-duty base")
    if (
        set(right_geometry.target_station_ids) | LEFT_DUTY_IDS
        != EXPECTED_TARGET_DUTY_IDS
    ):
        raise ValueError(
            "WJ16 target duties differ from the exact sixteen-duty contract"
        )

    source_inputs = {
        family: dict(fingerprints)
        for family, fingerprints in right_geometry.family_source_fingerprints.items()
    }
    if "left_service" in source_inputs:
        raise ValueError(
            "WJ12 source fingerprints already contain a left-service overlay"
        )
    left_inputs = dict(left_geometry.source_inputs_sha256)
    _validate_hash_map(left_inputs, context="left service")
    source_inputs["left_service"] = left_inputs
    merged_input_hashes: dict[str, str] = {}
    for family, fingerprints in source_inputs.items():
        current = _validate_hash_map(fingerprints, context=family)
        for path, digest in current.items():
            prior = merged_input_hashes.get(path)
            if prior is not None and prior != digest:
                raise ValueError(f"WJ16 family input fingerprints conflict: {path}")
            merged_input_hashes[path] = digest

    target_duty_ids = frozenset(EXPECTED_TARGET_DUTY_IDS)
    replaced_axis_ids = expected_replaced_source_axes(inventory, target_duty_ids)
    if replaced_axis_ids != (
        frozenset(right_geometry.replaced_source_axis_ids)
        | frozenset(left_geometry.replaced_axis_ids)
    ):
        raise ValueError(
            "WJ16 replaced source SDS axes differ from pinned duty ownership"
        )
    if set(rows) & set(target_duty_ids) != set(target_duty_ids):
        raise ValueError("WJ16 source inventory omitted one or more exact duty IDs")
    host_ids = expected_source_hosts(inventory, target_duty_ids)
    new_host_ids = host_ids - set(right_geometry.finished_hosts)
    if new_host_ids != {
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
    }:
        raise ValueError("left service must add exactly its two source receiver rails")

    left_bores = _left_candidate_bores(left_geometry)
    bores = _merge_candidate_axis_maps(right_geometry.candidate_bores, left_bores)
    hardware = {
        axis_id: dict(components)
        for axis_id, components in right_geometry.candidate_installed_hardware.items()
    }
    left_hardware = _shape_map(left_geometry, "installed", "left service")
    if set(left_hardware) != EXPECTED_LEFT_CANDIDATE_AXIS_IDS:
        raise ValueError(
            "left installed hardware differs from exact WJ16 candidate axes"
        )
    for axis_id, components in left_hardware.items():
        if axis_id in hardware:
            raise ValueError(f"duplicate candidate installed-hardware axis: {axis_id}")
        rows_for_axis = dict(components)
        if set(rows_for_axis) != {"shaft", "head", "head_washer", "nut_washer", "nut"}:
            raise ValueError(f"{axis_id} left installed component roles changed")
        _validate_shapes(rows_for_axis, context=f"left installed hardware/{axis_id}")
        hardware[axis_id] = rows_for_axis
    if set(hardware) != EXPECTED_CANDIDATE_AXIS_IDS:
        raise ValueError(
            "WJ16 installed hardware IDs differ from its exact 72-axis map"
        )
    if (
        sum(len(components) for components in hardware.values())
        != EXPECTED_INSTALLED_COMPONENT_COUNT
    ):
        raise ValueError("WJ16 must carry exactly 360 installed hardware shapes")

    raw_candidates = dict(right_geometry.raw_candidate_parts)
    finished_candidates = dict(right_geometry.finished_candidate_parts)
    left_parts = _shape_map(left_geometry, "parts", "left service")
    left_finished = _shape_map(left_geometry, "finished", "left service")
    left_candidate_parts = set(left_parts) - set(left_service.SOURCE_HOSTS)
    expected_left_parts = EXPECTED_LEFT_CANDIDATE_PART_IDS
    if left_candidate_parts != expected_left_parts:
        raise ValueError(
            "left candidate body IDs differ from the exact four-cleat contract"
        )
    if not expected_left_parts <= set(left_parts) or not expected_left_parts <= set(
        left_finished
    ):
        raise ValueError("left geometry omitted a raw or finished service cleat")
    if set(raw_candidates) != set(WJ12_LAYOUT.expected_candidate_part_ids):
        raise ValueError("WJ12 raw candidate parts differ from the fixed base contract")
    for part_id in expected_left_parts:
        if part_id in raw_candidates or part_id in finished_candidates:
            raise ValueError(f"duplicate WJ16 candidate part ID: {part_id}")
        raw_candidates[part_id] = left_parts[part_id]
        finished_candidates[part_id] = left_finished[part_id]
    if (
        set(raw_candidates) != EXPECTED_CANDIDATE_PART_IDS
        or set(finished_candidates) != EXPECTED_CANDIDATE_PART_IDS
    ):
        raise ValueError(
            "WJ16 candidate part IDs differ from the exact twenty-part map"
        )

    raw_source_parts = wj12._source_parts(source, "uncut_wood_parts")
    source_parts = wj12._source_parts(source, "parts")
    if not host_ids <= raw_source_parts.keys() or not host_ids <= source_parts.keys():
        raise ValueError("canonical source is missing one or more WJ16 shared hosts")
    raw_hosts = dict(right_geometry.raw_hosts)
    for host_id in new_host_ids:
        raw_hosts[host_id] = raw_source_parts[host_id]
    if set(raw_hosts) != host_ids:
        raise ValueError("WJ16 raw host IDs differ from exact source-host contract")

    native_cutters = right_integration.source_native_cutters_by_host(source, host_ids)
    if set(native_cutters) != set(host_ids):
        raise ValueError("WJ16 native source cutter map must cover all thirteen hosts")
    for host_id in right_geometry.finished_hosts:
        prior = right_geometry.source_cutters_by_host.get(host_id)
        if prior is None or set(prior) != set(native_cutters[host_id]):
            raise ValueError(f"WJ12 native source cutter IDs changed for {host_id}")
        _validate_shape_map_equal(
            prior,
            native_cutters[host_id],
            context=f"WJ12 source native cutters/{host_id}",
        )
    for host_id in left_service.SOURCE_HOSTS:
        prior = left_geometry.native_source_cutters_by_host.get(host_id)
        if prior is None or set(prior) != set(native_cutters[host_id]):
            raise ValueError(f"left native source cutter IDs changed for {host_id}")
        _validate_shape_map_equal(
            prior,
            native_cutters[host_id],
            context=f"left source native cutters/{host_id}",
        )

    overlay_hosts = frozenset(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS)
    all_purchase_hosts = frozenset(set(host_ids) | set(overlay_hosts))
    purchase_all = _panel_cutters_by_host(source, inventory, all_purchase_hosts)
    expected_purchase_map = {
        host_id: dict(purchase_all[host_id]) for host_id in host_ids
    }
    left_purchase = left_geometry.purchased_panel_cutters_by_host
    generated_left_purchase = {
        host_id: purchase_all[host_id] for host_id in left_service.SOURCE_HOSTS
    }
    for host_id in left_service.SOURCE_HOSTS:
        _validate_shape_map_equal(
            left_purchase[host_id],
            generated_left_purchase[host_id],
            context=f"left purchased panel cutters/{host_id}",
        )

    redirected_rows = {
        row["axis_id"]: (
            row["source_finished_receiver_member"],
            row["candidate_finished_receiver_member"],
        )
        for row in inventory.get("fixed_panel_kicker_screws", ())
        if row.get("candidate_finished_receiver_member")
        != row.get("source_finished_receiver_member")
    }
    redirected_ids = {
        axis_id
        for cutters in right_geometry.purchased_panel_cutters_by_candidate_part.values()
        for axis_id in cutters
    }
    if set(redirected_rows) != redirected_ids or len(redirected_ids) != 4:
        raise ValueError("WJ12 must preserve the exact four backer receiver redirects")
    redirected_by_part = right_geometry.purchased_panel_cutters_by_candidate_part
    if set(redirected_by_part) != {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    } or any(len(cutters) != 2 for cutters in redirected_by_part.values()):
        raise ValueError("WJ12 backer purchase cuts must remain two axes per backer")
    for axis_id, (source_receiver, candidate_receiver) in redirected_rows.items():
        if (
            candidate_receiver
            not in right_geometry.purchased_panel_cutters_by_candidate_part
        ):
            raise ValueError(
                f"redirected panel receiver is missing: {candidate_receiver}"
            )
        if source_receiver not in host_ids:
            raise ValueError(
                f"redirected panel source receiver is not a WJ16 host: {source_receiver}"
            )
        if axis_id not in native_cutters[source_receiver]:
            raise ValueError(
                f"redirected fixed axis lacks its native source cutter: {axis_id}"
            )
        extension_id = f"panel_purchase/{axis_id}"
        if extension_id not in expected_purchase_map[source_receiver]:
            raise ValueError(
                f"redirected fixed axis lacks its purchased-length cutter: {axis_id}"
            )

    final_cutters = {host_id: dict(native_cutters[host_id]) for host_id in host_ids}
    applied_purchase = {
        host_id: dict(expected_purchase_map[host_id]) for host_id in host_ids
    }
    for host_id in host_ids:
        overlap = set(final_cutters[host_id]) & set(applied_purchase[host_id])
        if overlap:
            raise ValueError(f"source native/purchase cutter IDs overlap for {host_id}")
        final_cutters[host_id].update(applied_purchase[host_id])
    for axis_id, (source_receiver, _candidate_receiver) in redirected_rows.items():
        del final_cutters[source_receiver][axis_id]
        extension_id = f"panel_purchase/{axis_id}"
        del final_cutters[source_receiver][extension_id]
        del applied_purchase[source_receiver][extension_id]

    replaced_cutter_ids = wj12._replaced_source_cutter_ids(
        final_cutters, replaced_axis_ids
    )
    receiver_ids = set(host_ids) | set(raw_candidates)
    candidate_bores_by_receiver: dict[str, dict[str, cq.Shape]] = {
        receiver_id: {} for receiver_id in receiver_ids
    }
    for axis_id, axis in bores.items():
        receiver_ids_for_axis = set(axis.receiver_ids)
        if len(axis.receiver_ids) != 2 or len(receiver_ids_for_axis) != 2:
            raise ValueError(f"{axis_id} must declare two distinct WJ16 receivers")
        missing = receiver_ids_for_axis - receiver_ids
        if missing:
            raise ValueError(f"{axis_id} receiver IDs are missing: {sorted(missing)}")
        if not isinstance(axis.shape, cq.Shape) or not axis.shape.isValid():
            raise ValueError(f"{axis_id} candidate bore is invalid")
        for receiver_id in receiver_ids_for_axis:
            candidate_bores_by_receiver[receiver_id][axis_id] = axis.shape

    finished_hosts = right_integration.machine_shared_hosts(
        raw_hosts,
        final_cutters,
        replaced_source_axis_ids=replaced_cutter_ids,
        candidate_bores_by_host={
            host_id: candidate_bores_by_receiver[host_id] for host_id in host_ids
        },
    )

    additional_finished = {
        host_id: shape
        for host_id, shape in right_geometry.additional_finished_source_parts.items()
        if host_id in overlay_hosts
    }
    additional_purchase = {
        host_id: dict(cutters)
        for host_id, cutters in right_geometry.additional_purchased_panel_cutters_by_host.items()
        if host_id in overlay_hosts
    }
    additional_reconstruction = {
        host_id: dict(row)
        for host_id, row in right_geometry.additional_source_reconstruction.items()
        if host_id in overlay_hosts
    }
    if (
        set(additional_finished) != overlay_hosts
        or set(additional_purchase) != overlay_hosts
        or set(additional_reconstruction) != overlay_hosts
    ):
        raise ValueError("WJ16 must retain exactly the three remaining source overlays")
    observed_overlay_counts = {
        host_id: len(cutters)
        for host_id, cutters in sorted(additional_purchase.items())
    }
    if observed_overlay_counts != EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS:
        raise ValueError(
            "WJ16 remaining source overlay cutters differ from the exact 8-axis map"
        )
    for host_id in overlay_hosts:
        _validate_shape_map_equal(
            additional_purchase[host_id],
            purchase_all[host_id],
            context=f"remaining source overlay purchase cutters/{host_id}",
        )
    absorbed_overlay_ids = tuple(
        sorted(set(right_geometry.additional_finished_source_parts) - overlay_hosts)
    )
    if set(absorbed_overlay_ids) != {
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
    }:
        raise ValueError(
            "WJ16 must absorb both left-service receiver overlays into hosts"
        )
    for host_id in absorbed_overlay_ids:
        prior_cuts = right_geometry.additional_purchased_panel_cutters_by_host.get(
            host_id
        )
        if prior_cuts is None or len(prior_cuts) != 2:
            raise ValueError(
                f"absorbed left receiver overlay must contain two cuts: {host_id}"
            )
        _validate_shape_map_equal(
            prior_cuts,
            purchase_all[host_id],
            context=f"absorbed source overlay purchase cutters/{host_id}",
        )
        if len(applied_purchase[host_id]) != 2:
            raise ValueError(
                f"absorbed left source host lost purchased panel cuts: {host_id}"
            )

    panel_replacements = dict(right_geometry.panel_replacements)
    left_panels = dict(left_geometry.panels)
    _validate_panel_surface(panel_replacements, left_panels, source_parts)
    fixed_axes = dict(right_geometry.fixed_axes)
    if len(fixed_axes) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError("WJ16 must retain the exact 66 fixed panel axes")
    left_fixed_axes = left_geometry.protected["fixed_66_hillman_axes_63p5mm"]
    _validate_shape_map_equal(
        fixed_axes, left_fixed_axes, context="WJ16 fixed panel axis envelopes"
    )
    frame_records = tuple(right_geometry.frame_bolt_records)
    frame_shapes = dict(right_geometry.frame_bolt_shapes)
    wj12._validate_frame_bolt_shapes(inventory, frame_records, frame_shapes)
    retained_clips, retained_sds = _retained_legacy_parts(
        source, inventory, replaced_axis_ids
    )
    protected = _protected_map(
        left_geometry, retained_clips, retained_sds, frame_shapes
    )

    source_reconstruction = _source_reconstruction_rows(
        right_geometry, left_geometry, frozenset(new_host_ids)
    )
    if set(source_reconstruction) != host_ids:
        raise ValueError("WJ16 source reconstruction map differs from 13 hosts")
    family_trial_ids = dict(right_geometry.family_trial_ids)
    family_trial_ids["left_service"] = left_geometry.trial_ids["left_service"]
    expected_trial_ids = {
        "left_service": LEFT_SERVICE_TRIAL_ID,
    }
    if any(
        family_trial_ids.get(name) != trial
        for name, trial in expected_trial_ids.items()
    ):
        raise ValueError("WJ16 left-service trial ID changed")

    # Keep inputs pinned across the CAD cut pass and verify the bound source again.
    _validate_hash_map(merged_input_hashes, context="WJ16 merged family inputs")
    if validate_source_binding(source) != binding:
        raise ValueError("WJ16 source binding changed during composition")

    return WJ16ComposedGeometry(
        layout_id=LAYOUT_ID,
        trial_id=TRIAL_ID,
        source=source,
        source_binding=binding,
        source_inventory_sha256=binding.inventory_sha256,
        source_inventory=_readonly_map(inventory),
        family_source_fingerprints=_readonly_map(
            {family: _readonly_map(rows) for family, rows in source_inputs.items()}
        ),
        family_trial_ids=_readonly_map(family_trial_ids),
        target_station_ids=tuple(sorted(target_duty_ids)),
        raw_hosts=_readonly_map(raw_hosts),
        finished_hosts=_readonly_map(finished_hosts),
        raw_candidate_parts=_readonly_map(raw_candidates),
        finished_candidate_parts=_readonly_map(finished_candidates),
        candidate_bores=_readonly_map(bores),
        candidate_installed_hardware=_readonly_map(
            {axis_id: _readonly_map(rows) for axis_id, rows in hardware.items()}
        ),
        replaced_source_axis_ids=replaced_axis_ids,
        replaced_source_cutter_ids=replaced_cutter_ids,
        source_cutters_by_host=_readonly_map(
            {host_id: _readonly_map(rows) for host_id, rows in native_cutters.items()}
        ),
        applied_source_cutters_by_host=_readonly_map(
            {host_id: _readonly_map(rows) for host_id, rows in final_cutters.items()}
        ),
        purchased_panel_cutters_by_host=_readonly_map(
            {host_id: _readonly_map(rows) for host_id, rows in applied_purchase.items()}
        ),
        purchased_panel_cutters_by_candidate_part=_readonly_map(
            {
                part_id: _readonly_map(cuts)
                for part_id, cuts in right_geometry.purchased_panel_cutters_by_candidate_part.items()
            }
        ),
        additional_finished_source_parts=_readonly_map(additional_finished),
        additional_purchased_panel_cutters_by_host=_readonly_map(
            {
                host_id: _readonly_map(rows)
                for host_id, rows in additional_purchase.items()
            }
        ),
        additional_source_reconstruction=_readonly_map(
            {
                host_id: _readonly_map(row)
                for host_id, row in additional_reconstruction.items()
            }
        ),
        source_reconstruction=_readonly_map(
            {
                host_id: _readonly_map(row)
                for host_id, row in source_reconstruction.items()
            }
        ),
        panel_replacements=_readonly_map(panel_replacements),
        fixed_axes=_readonly_map(fixed_axes),
        frame_bolt_records=frame_records,
        frame_bolt_shapes=_readonly_map(frame_shapes),
        protected=_readonly_map(
            {family: _readonly_map(rows) for family, rows in protected.items()}
        ),
        absorbed_source_overlay_ids=absorbed_overlay_ids,
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


def composition_report(geometry: WJ16ComposedGeometry) -> dict[str, Any]:
    """Return a source-bound, shape-free composition report."""
    if geometry.layout_id != LAYOUT_ID or geometry.trial_id != TRIAL_ID:
        raise ValueError("report requires the fixed WJ16 composition layout")
    if validate_source_binding(geometry.source) != geometry.source_binding:
        raise ValueError("WJ16 source binding changed before report creation")
    inventory = geometry.source_inventory
    duty_rows = _duty_rows(inventory)
    axis_owner = {
        axis["axis_id"]: row["legacy_station_id"]
        for row in inventory.get("legacy_duties", ())
        for axis in row.get("legacy_sds_axes", ())
    }
    fixed_rows = {
        row["axis_id"]: row for row in inventory.get("fixed_panel_kicker_screws", ())
    }
    producer_hashes = {
        name: _sha256_file(ROOT / path)
        for name, path in sorted(PRODUCER_HASH_PATHS.items())
    }
    family_fingerprints = {
        family: dict(sorted(rows.items()))
        for family, rows in sorted(geometry.family_source_fingerprints.items())
    }
    return {
        "schema": SCHEMA,
        "layout_id": geometry.layout_id,
        "trial_id": geometry.trial_id,
        "status": geometry.status,
        "claim_boundary": (
            "Source-bound nominal diagnostic composition only. It does not establish "
            "cross-family clearance, access, joint capacity, installation, fabrication, "
            "inspection, or acceptance."
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
        "family_source_fingerprints_sha256": family_fingerprints,
        "counts": geometry.counts,
        "target_duties": [
            {
                "station_id": station_id,
                "legacy_host_members": duty_rows[station_id]["legacy_host_members"],
                "replaced_source_sds_axis_ids": [
                    axis["axis_id"] for axis in duty_rows[station_id]["legacy_sds_axes"]
                ],
            }
            for station_id in geometry.target_station_ids
        ],
        "source_reconstruction": {
            host_id: dict(row)
            for host_id, row in sorted(geometry.source_reconstruction.items())
        },
        "source_cut_operations": {
            host_id: {
                "native_source_cut_ids": sorted(cutters),
                "applied_candidate_cut_ids": sorted(
                    geometry.applied_source_cutters_by_host[host_id]
                ),
                "purchased_panel_cut_ids_applied": sorted(
                    geometry.purchased_panel_cutters_by_host[host_id]
                ),
            }
            for host_id, cutters in sorted(geometry.source_cutters_by_host.items())
        },
        "replaced_source_axes": [
            {
                "axis_id": axis_id,
                "legacy_station_id": axis_owner.get(axis_id),
                "source_cut_ids_removed": sorted(
                    cutter_id
                    for cutter_id in geometry.replaced_source_cutter_ids
                    if cutter_id == axis_id or cutter_id == f"{axis_id}/head"
                ),
            }
            for axis_id in sorted(geometry.replaced_source_axis_ids)
        ],
        "candidate_axes": {
            axis_id: {
                "family": axis.family,
                "family_trial_id": axis.trial_id,
                "receiver_ids": list(axis.receiver_ids),
                "station_id": axis.station_id,
                "bore": _shape_evidence(axis.shape),
                "installed_component_roles": sorted(
                    geometry.candidate_installed_hardware[axis_id]
                ),
            }
            for axis_id, axis in sorted(geometry.candidate_bores.items())
        },
        "candidate_panel_receiver_cuts": {
            part_id: {
                axis_id: {
                    "candidate_finished_receiver_member": fixed_rows[axis_id][
                        "candidate_finished_receiver_member"
                    ],
                    "shop_purchased_length_mm": fixed_rows[axis_id][
                        "shop_purchased_length_mm"
                    ],
                    "cutter": _shape_evidence(cutter),
                }
                for axis_id, cutter in sorted(cuts.items())
            }
            for part_id, cuts in sorted(
                geometry.purchased_panel_cutters_by_candidate_part.items()
            )
        },
        "additional_source_panel_cut_operations": {
            host_id: {
                cut_id: _shape_evidence(cutter)
                for cut_id, cutter in sorted(cuts.items())
            }
            for host_id, cuts in sorted(
                geometry.additional_purchased_panel_cutters_by_host.items()
            )
        },
        "absorbed_source_overlay_ids": list(geometry.absorbed_source_overlay_ids),
        "parts": {
            "raw_hosts": {
                name: _shape_evidence(shape)
                for name, shape in sorted(geometry.raw_hosts.items())
            },
            "finished_hosts": {
                name: _shape_evidence(shape)
                for name, shape in sorted(geometry.finished_hosts.items())
            },
            "additional_finished_source_parts": {
                name: _shape_evidence(shape)
                for name, shape in sorted(
                    geometry.additional_finished_source_parts.items()
                )
            },
            "raw_candidate_parts": {
                name: _shape_evidence(shape)
                for name, shape in sorted(geometry.raw_candidate_parts.items())
            },
            "finished_candidate_parts": {
                name: _shape_evidence(shape)
                for name, shape in sorted(geometry.finished_candidate_parts.items())
            },
            "panel_replacements": {
                name: _shape_evidence(shape)
                for name, shape in sorted(geometry.panel_replacements.items())
            },
        },
        "fixed_panel_axes": sorted(geometry.fixed_axes),
        "frame_bolts": [dict(row) for row in geometry.frame_bolt_records],
        "protected_inventory_counts": {
            family: len(shapes) for family, shapes in sorted(geometry.protected.items())
        },
        "gates": geometry.gates,
    }
