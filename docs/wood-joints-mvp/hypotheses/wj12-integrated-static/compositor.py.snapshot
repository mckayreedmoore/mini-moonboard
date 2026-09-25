"""Compose the twelve-duty wood-joint hypothesis from source-bound inputs.

This adapter rebuilds shared source hosts once from uncut stock. It does not
run the family collision reports and does not establish fit, strength,
installation, fabrication, or release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import (
    LEGACY_DUTY_HOSTS as WJ03_DUTY_HOSTS,
)
from mini_moonboard.wood_joint_frame import (
    SOURCE_HOST_IDS as WJ03_SOURCE_HOST_IDS,
)
from mini_moonboard.wood_joint_frame import SOURCE_INVENTORY as WJ03_SOURCE_INVENTORY
from mini_moonboard.wood_joint_frame import (
    _source_shape_fingerprint,
    validate_source_binding,
)
from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from scripts import wood_joint_right_rail_integration as right_integration
from scripts import wood_joint_wj03_compact_outer_access as compact_access
from scripts import wood_joint_wj05_center_offset_adapter as center_offset
from scripts import wood_joint_wj05_center_post_x190_probe as center_x190_probe
from scripts import wood_joint_wj05_center_tools as center_tools

SCHEMA = "wood_joint_wj12_compositor/v1"
TRIAL_ID = "wj12-compact-outer-right-rail-center-x190-v1"
HIT_TOLERANCE_MM3 = 1e-3
EXPECTED_DUTY_COUNT = 12
EXPECTED_REPLACED_SDS_COUNT = 72
EXPECTED_CANDIDATE_AXIS_COUNT = 56
EXPECTED_PANEL_AXIS_COUNT = 66
EXPECTED_FRAME_BOLT_COUNT = 12
EXPECTED_FRAME_BOLT_INSTALLED_COMPONENT_COUNT = 60
EXPECTED_FRAME_BOLT_SOURCE_AXIS_COUNT = 12
EXPECTED_FRAME_BOLT_SHAPE_COUNT = 72
EXPECTED_REDIRECTED_PANEL_AXIS_COUNT = 4
EXPECTED_RETAINED_LEGACY_CLIP_COUNT = 12
EXPECTED_RETAINED_LEGACY_SDS_COUNT = 72
EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS = {
    "base_rail_top": 4,
    "base_rail_bottom_left": 2,
    "base_rail_bottom_right": 2,
    "base_rail_service_lower_left": 2,
    "base_rail_service_upper_left": 2,
}
EXPECTED_ADDITIONAL_PANEL_RECEIVER_CUT_COUNT = 12

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/wood-joints-mvp/hypotheses/wj12-composed-geometry.json"

WJ03_STATIONS = frozenset(WJ03_DUTY_HOSTS)
RIGHT_STATIONS = right_integration.TARGET_STATIONS
CENTER_STATIONS = center_tools.REPLACED_CENTER_LEGACY_DUTIES
TARGET_STATIONS = WJ03_STATIONS | RIGHT_STATIONS | CENTER_STATIONS


@dataclass(frozen=True)
class SourceCutterPreflight:
    """One in-memory proof that a source cutter map reproduces all 11 hosts."""

    source: Any
    source_binding: Any
    inventory: Mapping[str, Any]
    host_ids: frozenset[str]
    raw_hosts: Mapping[str, cq.Shape]
    current_hosts: Mapping[str, cq.Shape]
    source_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]]
    purchased_panel_cut_ids_by_host: Mapping[str, frozenset[str]]
    reconstruction: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class CandidateBore:
    """A source-bound candidate bore and its two receiving timber bodies."""

    axis_id: str
    family: str
    trial_id: str
    receiver_ids: tuple[str, str]
    shape: cq.Shape
    station_id: str | None = None


@dataclass(frozen=True)
class WJ12ComposedGeometry:
    """One disjoint twelve-duty geometry map, still an unaccepted hypothesis."""

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
    candidate_bores: Mapping[str, CandidateBore]
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
            "cross_family_clearance_checked": False,
            "complete_joint_acceptance": False,
            "capacity_established": False,
            "installation_proven": False,
            "fabrication_released": False,
            "structural_released": False,
        }


class SourceReconstructionError(ValueError):
    """A source cutter map does not reproduce its bound source hosts."""


def _readonly_map(values: Mapping) -> Mapping:
    return MappingProxyType(dict(values))


def _inventory_matches_source_binding(
    inventory: Mapping[str, Any], source_binding: Any
) -> None:
    """Reject caller-supplied inventory data that is not the pinned source."""
    try:
        pinned = json.loads(WJ03_SOURCE_INVENTORY.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("canonical source inventory cannot be loaded") from error
    if dict(inventory) != pinned:
        raise ValueError("caller inventory differs from the canonical source inventory")
    digest = hashlib.sha256(WJ03_SOURCE_INVENTORY.read_bytes()).hexdigest()
    if digest != source_binding.inventory_sha256:
        raise ValueError("canonical source inventory hash differs from source binding")


def _validate_fingerprint_map(
    expected: Mapping[str, str], *, context: str
) -> dict[str, str]:
    """Verify that every recorded family input still has its recorded hash."""
    current = {}
    for relative_path, digest in expected.items():
        path = ROOT / relative_path
        try:
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(f"{context} source input is unavailable: {relative_path}") from error
        if observed != digest:
            raise ValueError(f"{context} source input changed: {relative_path}")
        current[relative_path] = observed
    if not current:
        raise ValueError(f"{context} source fingerprint map is empty")
    return dict(sorted(current.items()))


def _source_parts(source: Any, method_name: str) -> dict[str, cq.Shape]:
    method = getattr(source, method_name, None)
    if not callable(method):
        raise TypeError(f"source must provide {method_name}()")
    parts = tuple(method())
    result = {part.name: part.shape for part in parts}
    if len(result) != len(parts):
        raise ValueError(f"source {method_name}() must have unique part names")
    return result


def _duty_rows(inventory: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    duties = inventory.get("legacy_duties", ())
    rows = {row["legacy_station_id"]: row for row in duties}
    if len(rows) != len(duties):
        raise ValueError("legacy duty station IDs must be unique")
    return rows


def source_host_ids(inventory: Mapping[str, Any]) -> frozenset[str]:
    """Return the canonical raw-host union from the three selected duty sets."""
    rows = _duty_rows(inventory)
    missing = TARGET_STATIONS - rows.keys()
    if missing:
        raise ValueError(f"source inventory lacks target duties: {sorted(missing)}")
    hosts = {
        host
        for station_id in TARGET_STATIONS
        for host in rows[station_id].get("legacy_host_members", ())
    }
    if not set(WJ03_SOURCE_HOST_IDS) <= hosts:
        raise ValueError("target duty host union no longer includes WJ-03 source hosts")
    if len(hosts) != 11:
        raise ValueError(
            f"twelve-duty source host union must contain 11 hosts, got {len(hosts)}"
        )
    return frozenset(hosts)


def _expected_native_cutter_ids(
    source: Any,
    host_ids: frozenset[str],
    connections: tuple[Any, ...] | None = None,
) -> dict[str, set[str]]:
    """Enumerate source operations, including separate screw-head cutters."""
    connections = tuple(source.connections()) if connections is None else connections
    expected: dict[str, set[str]] = {name: set() for name in host_ids}
    for connection in connections:
        for host_id in set(connection.members) & host_ids:
            expected[host_id].add(connection.name)
            if connection.kind == "screw" and connection.members[0] == host_id:
                expected[host_id].add(f"{connection.name}/head")

    for index, (host_id, name, _cutter) in enumerate(source.service_cutters()):
        if host_id in host_ids:
            expected[host_id].add(f"service/{index}/{name}")
    for index, (host_id, name, operation, _cutter) in enumerate(
        source.additional_machining_cutters()
    ):
        if host_id in host_ids:
            expected[host_id].add(f"additional/{index}/{name}/{operation}")
    return expected


def _target_source_axes(
    inventory: Mapping[str, Any],
) -> tuple[frozenset[str], dict[str, tuple[str, ...]]]:
    rows = _duty_rows(inventory)
    target_rows: dict[str, tuple[str, ...]] = {}
    for station_id in sorted(TARGET_STATIONS):
        row = rows.get(station_id)
        if row is None:
            raise ValueError(f"source inventory lacks target duty {station_id}")
        axes = tuple(
            axis["axis_id"]
            for axis in row.get("legacy_sds_axes", ())
            if axis.get("shop_opening_kind") == "sds_wood"
        )
        if len(axes) != 6 or len(set(axes)) != 6:
            raise ValueError(f"{station_id} must own six unique source SDS axes")
        all_axes = row.get("legacy_sds_axes", ())
        if len(all_axes) != 6 or any(
            axis.get("shop_opening_kind") != "sds_wood" for axis in all_axes
        ):
            raise ValueError(f"{station_id} includes a non-SDS or missing legacy axis")
        target_rows[station_id] = axes
    flat = [axis_id for axes in target_rows.values() for axis_id in axes]
    if len(flat) != EXPECTED_REPLACED_SDS_COUNT or len(set(flat)) != len(flat):
        raise ValueError(
            "target duty set must remove exactly 72 distinct source SDS axes"
        )
    return frozenset(flat), target_rows


def preflight_source_cutter_map(
    source: Any,
    source_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]],
    inventory: Mapping[str, Any],
    *,
    tolerance_mm3: float = HIT_TOLERANCE_MM3,
) -> SourceCutterPreflight:
    """Rebuild original source hosts first; fail before candidate machining.

    The caller supplies the currently reviewed cutter inventory. This function
    deliberately has no fallback to a family-local cutter map.
    """
    binding = validate_source_binding(source)
    _inventory_matches_source_binding(inventory, binding)
    hosts = source_host_ids(inventory)
    if set(source_cutters_by_host) != set(hosts):
        raise ValueError("source cutter map must cover exactly the 11 target hosts")
    raw_all = _source_parts(source, "uncut_wood_parts")
    current_all = _source_parts(source, "parts")
    if not hosts <= raw_all.keys() or not hosts <= current_all.keys():
        raise ValueError("canonical source is missing one or more target host shapes")
    raw_hosts = {name: raw_all[name] for name in sorted(hosts)}
    current_hosts = {name: current_all[name] for name in sorted(hosts)}
    cutters = {name: dict(source_cutters_by_host[name]) for name in sorted(hosts)}

    connections = tuple(source.connections())
    by_name = {connection.name: connection for connection in connections}
    if len(by_name) != len(connections):
        raise ValueError("source connection axis IDs must be unique")
    target_axes, target_rows = _target_source_axes(inventory)
    target_duties = _duty_rows(inventory)
    target_axis_rows = {
        axis["axis_id"]: (station_id, axis)
        for station_id in target_rows
        for axis in target_duties[station_id]["legacy_sds_axes"]
    }
    if set(target_axis_rows) != set(target_axes):
        raise ValueError("target SDS inventory rows are not uniquely keyed")
    for axis_id, (station_id, row) in target_axis_rows.items():
        connection = by_name.get(axis_id)
        if connection is None:
            raise ValueError(f"target source SDS axis missing from source: {axis_id}")
        if tuple(connection.members) != tuple(row["members"]):
            raise ValueError(f"target source SDS ownership changed: {axis_id}")
        duty_hosts = set(target_duties[station_id]["legacy_host_members"])
        if (
            len(set(connection.members) & hosts) != 1
            or not (set(connection.members) & hosts) <= duty_hosts
        ):
            raise ValueError(f"target source SDS host ownership changed: {axis_id}")

    for connection in connections:
        for host_id in set(connection.members) & hosts:
            if connection.name not in cutters[host_id]:
                raise ValueError(
                    f"source cutter map omits {connection.name} from {host_id}"
                )

    fixed_rows = inventory.get("fixed_panel_kicker_screws", ())
    fixed_ids = [row["axis_id"] for row in fixed_rows]
    if len(fixed_rows) != EXPECTED_PANEL_AXIS_COUNT or len(set(fixed_ids)) != len(
        fixed_ids
    ):
        raise ValueError("source inventory must preserve all 66 fixed panel screw axes")
    for row in fixed_rows:
        axis_id = row["axis_id"]
        connection = by_name.get(axis_id)
        if connection is None:
            raise ValueError(
                f"fixed panel axis missing from source connections: {axis_id}"
            )
        if tuple(connection.members) != tuple(row["members"]):
            raise ValueError(f"fixed panel axis ownership changed: {axis_id}")

    expected_cut_ids = _expected_native_cutter_ids(source, hosts, connections)

    for host_id in sorted(hosts):
        if set(cutters[host_id]) != expected_cut_ids[host_id]:
            missing = sorted(expected_cut_ids[host_id] - set(cutters[host_id]))
            extra = sorted(set(cutters[host_id]) - expected_cut_ids[host_id])
            raise ValueError(
                f"{host_id} native cutter IDs differ from source operations; "
                f"missing={missing}, extra={extra}"
            )
        if any(
            not isinstance(shape, cq.Shape) or not shape.isValid()
            for shape in cutters[host_id].values()
        ):
            raise ValueError(f"{host_id} native cutter map has invalid geometry")

    panel_cut_ids: dict[str, frozenset[str]] = {}
    for host_id in hosts:
        panel_cut_ids[host_id] = frozenset(
            f"panel_purchase/{row['axis_id']}"
            for row in fixed_rows
            if host_id in set(row["members"])
        )

    rebuilt = right_integration.machine_shared_hosts(
        raw_hosts,
        cutters,
        replaced_source_axis_ids=frozenset(),
        candidate_bores_by_host={name: {} for name in hosts},
    )
    reconstruction = {}
    for host_id in sorted(hosts):
        delta = right_integration._shape_difference_volume(
            rebuilt[host_id], current_hosts[host_id]
        )
        reconstruction[host_id] = {
            "symmetric_difference_mm3": round(delta, 6),
            "matches_source_finished_member": delta <= tolerance_mm3,
        }
    failures = {
        name: row["symmetric_difference_mm3"]
        for name, row in reconstruction.items()
        if not row["matches_source_finished_member"]
    }
    if failures:
        details = ", ".join(
            f"{name}={delta:.6f} mm3" for name, delta in sorted(failures.items())
        )
        raise SourceReconstructionError(
            "source cutter reconstruction failed before family composition: " + details
        )

    return SourceCutterPreflight(
        source=source,
        source_binding=binding,
        inventory=_readonly_map(inventory),
        host_ids=hosts,
        raw_hosts=_readonly_map(raw_hosts),
        current_hosts=_readonly_map(current_hosts),
        source_cutters_by_host=_readonly_map(
            {name: _readonly_map(values) for name, values in cutters.items()}
        ),
        purchased_panel_cut_ids_by_host=_readonly_map(panel_cut_ids),
        reconstruction=_readonly_map(
            {name: _readonly_map(row) for name, row in reconstruction.items()}
        ),
    )


def _shape_map(value: Any, attribute: str, context: str) -> Mapping[str, cq.Shape]:
    result = getattr(value, attribute, None)
    if not isinstance(result, Mapping):
        raise TypeError(f"{context}.{attribute} must be a shape map")
    return result


def _validate_frame_bolt_shapes(
    inventory: Mapping[str, Any],
    frame_records: tuple[Mapping[str, Any], ...],
    frame_shapes: Mapping[str, cq.Shape],
) -> None:
    """Require each source bolt's five installed pieces and occupied axis."""
    source_rows = inventory.get("starting_frame_bolts")
    if not isinstance(source_rows, (list, tuple)):
        raise TypeError("starting_frame_bolts must be a list or tuple")
    expected_axis_ids = [row.get("axis_id") for row in source_rows]
    if (
        len(expected_axis_ids) != EXPECTED_FRAME_BOLT_COUNT
        or any(not isinstance(axis_id, str) or not axis_id for axis_id in expected_axis_ids)
        or len(set(expected_axis_ids)) != EXPECTED_FRAME_BOLT_COUNT
    ):
        raise ValueError("source inventory must identify exactly 12 unique frame bolts")

    record_ids = [row.get("axis_id") for row in frame_records]
    if (
        len(record_ids) != EXPECTED_FRAME_BOLT_COUNT
        or any(not isinstance(axis_id, str) or not axis_id for axis_id in record_ids)
        or len(set(record_ids)) != EXPECTED_FRAME_BOLT_COUNT
        or set(record_ids) != set(expected_axis_ids)
    ):
        raise ValueError("frame-bolt records differ from the 12 pinned source identities")
    if any(
        row.get("installed_component_count")
        != EXPECTED_FRAME_BOLT_INSTALLED_COMPONENT_COUNT // EXPECTED_FRAME_BOLT_COUNT
        for row in frame_records
    ):
        raise ValueError("each source frame bolt must retain five installed components")

    expected_shape_ids = {
        f"{axis_id}/installed_component_{index}"
        for axis_id in expected_axis_ids
        for index in range(1, 6)
    } | {f"{axis_id}/source_occupied_axis" for axis_id in expected_axis_ids}
    if set(frame_shapes) != expected_shape_ids:
        raise ValueError(
            "frame-bolt shapes must contain exactly five installed components and "
            "one source occupied axis for each pinned bolt"
        )
    if any(
        not isinstance(shape, cq.Shape) or not shape.isValid()
        for shape in frame_shapes.values()
    ):
        raise ValueError("frame-bolt shape inventory contains invalid geometry")


def _candidate_bore(
    axis_id: str,
    family: str,
    trial_id: str,
    receiver_ids: tuple[str, ...],
    shape: cq.Shape,
    *,
    station_id: str | None = None,
) -> CandidateBore:
    owners = tuple(receiver_ids)
    if len(owners) != 2 or len(set(owners)) != 2:
        raise ValueError(f"{axis_id} must connect exactly two distinct timber bodies")
    if not axis_id or not isinstance(shape, cq.Shape) or not shape.isValid():
        raise ValueError(f"{axis_id or '<unnamed>'} needs a valid bore shape")
    return CandidateBore(axis_id, family, trial_id, owners, shape, station_id)


def _stack_through_bore(stack: Any) -> cq.Shape:
    """Build the one full-grip cutter represented by a BoltStack."""
    direction = cq.Vector(stack.direction).normalized()
    grip = float(stack.grip_mm)
    diameter = float(stack.hardware.drill_diameter_mm)
    if grip <= 0 or diameter <= 0:
        raise ValueError(f"{stack.id} needs a positive grip and drill diameter")
    return cq.Solid.makeCylinder(
        diameter / 2,
        grip,
        stack.head_seat.center,
        direction,
    )


def _installed_components(stack: Any, *, context: str) -> dict[str, cq.Shape]:
    components = dict(stack.installed_shapes())
    required = {"shaft", "head", "head_washer", "nut_washer", "nut"}
    if set(components) != required:
        raise ValueError(
            f"{context} installed component roles differ from BoltStack: "
            f"{sorted(components)}"
        )
    if any(
        not isinstance(shape, cq.Shape) or not shape.isValid()
        for shape in components.values()
    ):
        raise ValueError(f"{context} has invalid installed hardware geometry")
    return components


def _same_shape(first: cq.Shape, second: cq.Shape) -> bool:
    return _source_shape_fingerprint(first) == _source_shape_fingerprint(second)


def _collect_wj03_outer_bores(compact: Any) -> dict[str, CandidateBore]:
    stacks = _shape_map(compact, "stacks", "compact outer")
    if len(stacks) != 20:
        raise ValueError(f"compact outer requires 20 BoltStacks, got {len(stacks)}")
    result = {}
    for axis_id, stack in stacks.items():
        receivers = tuple(layer.body_id for layer in stack.layers)
        result[axis_id] = _candidate_bore(
            axis_id,
            "wj03_outer",
            compact.trial_id,
            receivers,
            _stack_through_bore(stack),
        )
    return result


def _collect_backer_bores(compact: Any) -> dict[str, CandidateBore]:
    bores = _shape_map(compact, "wj05_bores", "compact outer")
    backers = _shape_map(compact, "wj05_raw_backers", "compact outer")
    expected_ids = {
        f"backer_header_{side}_{index}"
        for side in ("left", "right")
        for index in (1, 2)
    }
    if set(bores) != expected_ids:
        raise ValueError("compact outer requires exactly four WJ-05 backer bores")
    if set(backers) != {f"inner_kicker_backer_{side}" for side in ("left", "right")}:
        raise ValueError("compact outer requires both raw WJ-05 backer bodies")
    result = {}
    for axis_id, shape in bores.items():
        side = axis_id.split("_")[2]
        result[axis_id] = _candidate_bore(
            axis_id,
            "wj05_backer",
            compact.trial_id,
            (f"inner_kicker_backer_{side}", "base_header"),
            shape,
            station_id=f"wj05_backer_{side}",
        )
    return result


def _collect_right_bores(right: Any) -> dict[str, CandidateBore]:
    stacks = _shape_map(right, "stacks", "right integration")
    bores = _shape_map(right, "bores", "right integration")
    trial_ids = dict(right.trial_ids)
    if set(stacks) != set(bores) or len(stacks) != 16:
        raise ValueError("right integration requires 16 matching stack and bore IDs")
    result = {}
    for axis_id, stack in stacks.items():
        receiver_ids = tuple(layer.body_id for layer in stack.layers)
        family = next(
            (
                name
                for name, trial_id in trial_ids.items()
                if axis_id.startswith(f"{name}/")
            ),
            None,
        )
        if family is None:
            raise ValueError(f"right stack has no family provenance: {axis_id}")
        result[axis_id] = _candidate_bore(
            axis_id,
            family,
            trial_ids[family],
            receiver_ids,
            bores[axis_id],
        )
    return result


def _collect_center_bores(center: Any) -> dict[str, CandidateBore]:
    axes = tuple(center.axes)
    fasteners = _shape_map(center, "fastener_shapes", "center x190")
    if len(axes) != 16:
        raise ValueError("center x190 requires 16 candidate axis records")
    ids = [row["axis_id"] for row in axes]
    if len(set(ids)) != 16 or set(ids) != set(fasteners):
        raise ValueError("center x190 axes and fastener shape IDs must match uniquely")
    result = {}
    for row in axes:
        axis_id = row["axis_id"]
        components = fasteners[axis_id]
        if "bore" not in components:
            raise ValueError(f"center x190 omitted candidate bore for {axis_id}")
        result[axis_id] = _candidate_bore(
            axis_id,
            "wj05_center_x190",
            center.trial_id,
            tuple(row["intended_receivers"]),
            components["bore"],
            station_id=row["interface_id"],
        )
    return result


def _collect_candidate_installed_hardware(
    compact: Any, right: Any, center: Any
) -> dict[str, Mapping[str, cq.Shape]]:
    """Normalize installed candidate component shapes by candidate axis ID."""
    result: dict[str, Mapping[str, cq.Shape]] = {}

    outer_stacks = _shape_map(compact, "stacks", "compact outer")
    for axis_id, stack in outer_stacks.items():
        result[axis_id] = _readonly_map(_installed_components(stack, context=axis_id))

    backer_bores = _shape_map(compact, "wj05_bores", "compact outer")
    backer_shafts = _shape_map(compact, "wj05_bolts", "compact outer")
    backer_stacks = _shape_map(compact, "wj05_stacks", "compact outer")
    if set(backer_bores) != set(backer_shafts) or set(backer_bores) != set(
        backer_stacks
    ):
        raise ValueError("backer bore, shaft and hardware component IDs must agree")
    for axis_id in backer_bores:
        components = dict(backer_stacks[axis_id])
        components["shaft"] = backer_shafts[axis_id]
        if "bore" in components or any("tool" in name for name in components):
            raise ValueError(
                f"{axis_id} backer hardware map includes non-hardware shapes"
            )
        if not {
            "shaft",
            "bottom_washer",
            "bottom_head",
            "top_washer",
            "top_nut",
        } <= set(components):
            raise ValueError(f"{axis_id} backer hardware component set is incomplete")
        if any(
            not isinstance(shape, cq.Shape) or not shape.isValid()
            for shape in components.values()
        ):
            raise ValueError(f"{axis_id} backer hardware has invalid geometry")
        if axis_id in result:
            raise ValueError(f"duplicate candidate hardware axis ID: {axis_id}")
        result[axis_id] = _readonly_map(components)

    right_stacks = _shape_map(right, "stacks", "right integration")
    right_installed = _shape_map(right, "installed", "right integration")
    if set(right_stacks) != set(right_installed):
        raise ValueError("right integration stack and installed hardware IDs differ")
    for axis_id, components in right_installed.items():
        if axis_id in result:
            raise ValueError(f"duplicate candidate hardware axis ID: {axis_id}")
        rows = dict(components)
        if set(rows) != {"shaft", "head", "head_washer", "nut_washer", "nut"}:
            raise ValueError(f"{axis_id} right installed hardware roles changed")
        if any(
            not isinstance(shape, cq.Shape) or not shape.isValid()
            for shape in rows.values()
        ):
            raise ValueError(f"{axis_id} right installed hardware has invalid geometry")
        result[axis_id] = _readonly_map(rows)

    center_axes = tuple(center.axes)
    center_fasteners = _shape_map(center, "fastener_shapes", "center x190")
    expected_roles = {"shaft", "head", "head_washer", "nut_washer", "nut"}
    center_ids = {row["axis_id"] for row in center_axes}
    if center_ids != set(center_fasteners):
        raise ValueError("center axis and fastener component IDs differ")
    for axis_id, all_components in center_fasteners.items():
        if axis_id in result:
            raise ValueError(f"duplicate candidate hardware axis ID: {axis_id}")
        components = {
            role: shape
            for role, shape in all_components.items()
            if role in expected_roles
        }
        if set(components) != expected_roles:
            raise ValueError(f"{axis_id} center installed hardware roles changed")
        if any(
            not isinstance(shape, cq.Shape) or not shape.isValid()
            for shape in components.values()
        ):
            raise ValueError(
                f"{axis_id} center installed hardware has invalid geometry"
            )
        result[axis_id] = _readonly_map(components)

    if len(result) != EXPECTED_CANDIDATE_AXIS_COUNT:
        raise ValueError(
            "twelve-duty composition requires installed hardware for 56 axes, "
            f"got {len(result)}"
        )
    return result


def _candidate_parts(
    compact: Any, right: Any, center: Any
) -> tuple[dict[str, cq.Shape], dict[str, tuple[cq.Shape, ...]]]:
    raw: dict[str, cq.Shape] = {}
    design_cuts: dict[str, tuple[cq.Shape, ...]] = {}

    def add_parts(rows: Mapping[str, cq.Shape], context: str) -> None:
        duplicate = raw.keys() & rows.keys()
        if duplicate:
            raise ValueError(
                f"duplicate candidate part IDs from {context}: {sorted(duplicate)}"
            )
        raw.update(rows)

    compact_parts = _shape_map(compact, "parts", "compact outer")
    if len(compact_parts) != 6:
        raise ValueError("compact outer must provide six raw candidate timber parts")
    for name, part in compact_parts.items():
        raw[name] = part.uncut_shape
        design_cuts[name] = tuple(
            cut.removed_shape for cut in part.modifications if cut.kind != "bore"
        )

    backers = _shape_map(compact, "wj05_raw_backers", "compact outer")
    if set(backers) != {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    }:
        raise ValueError("compact outer must provide both raw WJ-05 backers")
    add_parts(backers, "WJ-05 backers")
    counterbores = _shape_map(compact, "wj05_counterbores", "compact outer")
    if set(counterbores) != set(compact.wj05_bores):
        raise ValueError("WJ-05 counterbore and backer bore IDs must agree")
    for axis_id, counterbore in counterbores.items():
        side = axis_id.split("_")[2]
        part_id = f"inner_kicker_backer_{side}"
        design_cuts[part_id] = (*design_cuts.get(part_id, ()), counterbore)

    right_hosts = set(right_integration.SHARED_HOSTS)
    right_parts = _shape_map(right, "parts", "right integration")
    right_candidates = set(right_parts) - right_hosts
    if len(right_candidates) != 4:
        raise ValueError("right integration must provide four raw cleats")
    add_parts(
        {name: right_parts[name] for name in right_candidates}, "right integration"
    )

    center_candidates = _shape_map(center, "candidates", "center x190")
    if len(center_candidates) != 4:
        raise ValueError("center x190 must provide four raw center cleats")
    add_parts(center_candidates, "center x190")

    if len(raw) != 16:
        raise ValueError(
            f"composition requires 16 raw candidate bodies, got {len(raw)}"
        )
    return raw, design_cuts


def _validate_center_raw_posts(
    source_raw_hosts: Mapping[str, cq.Shape], center: Any
) -> dict[str, cq.Shape]:
    center_parts = _shape_map(center, "parts", "center x190")
    moved = {}
    for side, expected_trial_center in center_offset.TRIAL_POST_CENTERS_MM.items():
        part_id = f"base_post_center_{side}"
        if part_id not in source_raw_hosts or part_id not in center_parts:
            raise ValueError(f"center x190 omitted raw moved host {part_id}")
        source_box = source_raw_hosts[part_id].BoundingBox()
        source_center = (source_box.xmin + source_box.xmax) / 2
        outward = expected_trial_center - source_center
        expected_sign = -1 if side == "left" else 1
        if expected_sign * outward <= center_offset.POST_OFFSET_MM:
            raise ValueError(
                f"{part_id} movement must reach x190 from source raw stock, "
                f"not only apply the final {center_offset.POST_OFFSET_MM:g} mm shift"
            )
        expected = source_raw_hosts[part_id].translate(cq.Vector(outward, 0, 0))
        trial_box = center_parts[part_id].BoundingBox()
        trial_center = (trial_box.xmin + trial_box.xmax) / 2
        if abs(trial_center - expected_trial_center) > 1e-6:
            raise ValueError(
                f"{part_id} trial raw-stock center must be {expected_trial_center:g} mm"
            )
        if not _same_shape(center_parts[part_id], expected):
            raise ValueError(
                f"{part_id} must be raw source stock translated to the x190 trial datum"
            )
        moved[part_id] = center_parts[part_id]
    return moved


def _candidate_axis_map(
    compact: Any, right: Any, center: Any
) -> dict[str, CandidateBore]:
    result: dict[str, CandidateBore] = {}
    family_rows_list = (
        _collect_wj03_outer_bores(compact),
        _collect_backer_bores(compact),
        _collect_right_bores(right),
        _collect_center_bores(center),
    )
    expected_family_counts = (20, 4, 16, 16)
    if tuple(map(len, family_rows_list)) != expected_family_counts:
        raise ValueError("WJ12 candidate bore family counts must be 20, 4, 16, and 16")
    for family_rows in family_rows_list:
        duplicate = result.keys() & family_rows.keys()
        if duplicate:
            raise ValueError(f"duplicate candidate axis IDs: {sorted(duplicate)}")
        result.update(family_rows)
    if len(result) != EXPECTED_CANDIDATE_AXIS_COUNT:
        raise ValueError(
            f"twelve-duty composition requires 56 candidate axes, got {len(result)}"
        )
    return result


def _purchased_panel_extension_map(
    preflight: SourceCutterPreflight,
    panel_extension_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]],
) -> dict[str, dict[str, cq.Shape]]:
    hosts = preflight.host_ids
    if set(panel_extension_cutters_by_host) != set(hosts):
        raise ValueError(
            "purchased panel extension map must cover exactly the 11 target hosts"
        )
    result: dict[str, dict[str, cq.Shape]] = {}
    for host_id in sorted(hosts):
        cuts = dict(panel_extension_cutters_by_host[host_id])
        expected = set(preflight.purchased_panel_cut_ids_by_host[host_id])
        if set(cuts) != expected:
            missing = sorted(expected - set(cuts))
            extra = sorted(set(cuts) - expected)
            raise ValueError(
                f"{host_id} purchased panel cuts differ from fixed axes; "
                f"missing={missing}, extra={extra}"
            )
        if any(
            not isinstance(shape, cq.Shape) or not shape.isValid()
            for shape in cuts.values()
        ):
            raise ValueError(
                f"{host_id} has invalid purchased panel extension geometry"
            )
        result[host_id] = cuts
    return result


def _candidate_panel_extension_map(
    preflight: SourceCutterPreflight,
    candidate_part_ids: set[str],
) -> dict[str, dict[str, cq.Shape]]:
    """Build the four fixed purchase-length screw cuts redirected to backers."""
    inventory = preflight.inventory
    source = preflight.source
    connections = {row.name: row for row in source.panel_connections()}
    if len(connections) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError("source must preserve all 66 fixed panel screw axes")

    result: dict[str, dict[str, cq.Shape]] = {}
    redirected = 0
    for row in inventory.get("fixed_panel_kicker_screws", ()):
        receiver = row.get("candidate_finished_receiver_member")
        source_receiver = row.get("source_finished_receiver_member")
        if receiver == source_receiver or receiver not in candidate_part_ids:
            continue
        if not receiver.startswith("inner_kicker_backer_"):
            raise ValueError(
                f"fixed panel axis {row['axis_id']} moved to unsupported candidate "
                f"receiver {receiver!r}"
            )
        axis_id = row["axis_id"]
        connection = connections.get(axis_id)
        if connection is None:
            raise ValueError(f"redirected panel axis missing from source: {axis_id}")
        if tuple(connection.members) != tuple(row["members"]):
            raise ValueError(f"redirected panel axis ownership changed: {axis_id}")
        origin = cq.Vector(*row["origin_global_xyz_mm"])
        direction = cq.Vector(*row["axis_global_xyz"]).normalized()
        if (connection.start - origin).Length > 1e-6:
            raise ValueError(f"redirected panel axis origin changed: {axis_id}")
        if (connection.direction.normalized() - direction).Length > 1e-8:
            raise ValueError(f"redirected panel axis direction changed: {axis_id}")
        if abs(connection.diameter - row["source_occupied_diameter_mm"]) > 1e-6:
            raise ValueError(f"redirected panel axis diameter changed: {axis_id}")
        purchase_length = float(row["shop_purchased_length_mm"])
        if purchase_length <= 0:
            raise ValueError(f"redirected panel axis has no purchase length: {axis_id}")
        cutter = cq.Solid.makeCylinder(
            connection.diameter / 2,
            purchase_length,
            connection.start,
            direction,
        )
        result.setdefault(receiver, {})[axis_id] = cutter
        redirected += 1

    expected_parts = {"inner_kicker_backer_left", "inner_kicker_backer_right"}
    if set(result) != expected_parts or redirected != EXPECTED_REDIRECTED_PANEL_AXIS_COUNT:
        raise ValueError(
            "WJ12 requires exactly four redirected center-kicker screw cuts in "
            "the two diagnostic backers"
        )
    for receiver, cuts in result.items():
        if len(cuts) != 2:
            raise ValueError(f"{receiver} must receive exactly two fixed panel axes")
    return result


def _additional_panel_receiver_overlays(
    preflight: SourceCutterPreflight,
) -> tuple[
    dict[str, cq.Shape],
    dict[str, dict[str, cq.Shape]],
    dict[str, dict[str, Any]],
]:
    """Cut the fixed purchased screw lengths into five other source members.

    These receivers are outside the eleven source-host union rebuilt for the
    twelve candidate duties. Their native machining is retained by starting
    from the canonical source's finished ``parts()`` shapes and overlaying only
    the purchased-length panel-axis cutters.
    """
    inventory = preflight.inventory
    source = preflight.source
    fixed_rows = tuple(inventory.get("fixed_panel_kicker_screws", ()))
    if len(fixed_rows) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError("additional receiver overlays require all 66 fixed axes")
    connections = {row.name: row for row in source.panel_connections()}
    if len(connections) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError("source must preserve all 66 fixed panel screw axes")

    cutters: dict[str, dict[str, cq.Shape]] = {}
    axis_ids: set[str] = set()
    for row in fixed_rows:
        axis_id = row.get("axis_id")
        source_receiver = row.get("source_finished_receiver_member")
        candidate_receiver = row.get("candidate_finished_receiver_member")
        if source_receiver != candidate_receiver or source_receiver in preflight.host_ids:
            continue
        if not isinstance(axis_id, str) or not axis_id:
            raise ValueError("additional fixed panel rows need named axis IDs")
        if axis_id in axis_ids:
            raise ValueError(f"duplicate additional fixed panel axis: {axis_id}")
        axis_ids.add(axis_id)
        connection = connections.get(axis_id)
        if connection is None:
            raise ValueError(f"additional fixed panel axis missing from source: {axis_id}")
        if connection.kind != "screw" or tuple(connection.members) != tuple(row["members"]):
            raise ValueError(f"additional fixed panel ownership changed: {axis_id}")
        origin = cq.Vector(*row["origin_global_xyz_mm"])
        direction = cq.Vector(*row["axis_global_xyz"]).normalized()
        if (connection.start - origin).Length > 1e-6:
            raise ValueError(f"additional fixed panel origin changed: {axis_id}")
        if (connection.direction.normalized() - direction).Length > 1e-8:
            raise ValueError(f"additional fixed panel direction changed: {axis_id}")
        if abs(connection.diameter - row["source_occupied_diameter_mm"]) > 1e-6:
            raise ValueError(f"additional fixed panel diameter changed: {axis_id}")
        purchase_length = float(row["shop_purchased_length_mm"])
        if purchase_length <= 0:
            raise ValueError(f"additional fixed panel axis has no purchase length: {axis_id}")
        cutter = cq.Solid.makeCylinder(
            connection.diameter / 2,
            purchase_length,
            connection.start,
            direction,
        )
        cut_id = f"panel_purchase/{axis_id}"
        host_cuts = cutters.setdefault(source_receiver, {})
        if cut_id in host_cuts:
            raise ValueError(f"duplicate purchased panel cutter ID: {cut_id}")
        host_cuts[cut_id] = cutter

    observed_counts = {
        host_id: len(cuts) for host_id, cuts in sorted(cutters.items())
    }
    if observed_counts != EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS:
        raise ValueError(
            "additional fixed panel receivers differ from the pinned five-host, "
            f"12-axis map: {observed_counts}"
        )
    if len(axis_ids) != EXPECTED_ADDITIONAL_PANEL_RECEIVER_CUT_COUNT:
        raise ValueError("additional fixed panel map must contain exactly 12 axes")

    source_finished_parts = _source_parts(source, "parts")
    missing_parts = set(observed_counts) - source_finished_parts.keys()
    if missing_parts:
        raise ValueError(
            f"canonical source parts omit additional receivers: {sorted(missing_parts)}"
        )

    finished: dict[str, cq.Shape] = {}
    evidence: dict[str, dict[str, Any]] = {}
    for host_id in sorted(observed_counts):
        base_shape = source_finished_parts[host_id]
        host_cuts = cutters[host_id]
        if not isinstance(base_shape, cq.Shape) or not base_shape.isValid():
            raise ValueError(f"canonical finished source receiver is invalid: {host_id}")
        intersections = {
            cut_id: round(base_shape.intersect(cutter).Volume(), 6)
            for cut_id, cutter in sorted(host_cuts.items())
        }
        if any(volume <= HIT_TOLERANCE_MM3 for volume in intersections.values()):
            raise ValueError(f"purchased panel cut misses its source receiver: {host_id}")
        overlaid = base_shape.cut(*host_cuts.values()).clean()
        if not overlaid.isValid() or not overlaid.Solids():
            raise ValueError(f"purchased panel machining invalidated source receiver: {host_id}")
        finished[host_id] = overlaid
        evidence[host_id] = {
            "source_finished_shape_sha256": _source_shape_fingerprint(base_shape),
            "overlaid_finished_shape_sha256": _source_shape_fingerprint(overlaid),
            "purchase_cut_ids": sorted(host_cuts),
            "purchase_cut_intersection_mm3_by_id": intersections,
            "matches_source_plus_purchase_cuts": True,
        }
    return finished, cutters, evidence


def _final_source_cutters(
    preflight: SourceCutterPreflight,
    purchased_panel_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]],
    redirected_panel_cutters_by_candidate_part: Mapping[
        str, Mapping[str, cq.Shape]
    ],
) -> tuple[dict[str, dict[str, cq.Shape]], dict[str, dict[str, cq.Shape]]]:
    """Apply host extensions while moving four old center-post receivers.

    Source-native machining is first proven against the canonical source. These
    four fixed panel axes then leave their old source post receivers and enter
    the WJ-05 backers at their unchanged global poses.
    """
    extensions = _purchased_panel_extension_map(
        preflight, purchased_panel_cutters_by_host
    )
    final = {
        host_id: dict(preflight.source_cutters_by_host[host_id])
        for host_id in sorted(preflight.host_ids)
    }
    for host_id, cuts in extensions.items():
        overlap = final[host_id].keys() & cuts.keys()
        if overlap:
            raise ValueError(
                f"purchased extension IDs overlap native source cuts for {host_id}: "
                f"{sorted(overlap)}"
        )
        final[host_id].update(cuts)

    redirected_rows = {
        row["axis_id"]: (
            row["source_finished_receiver_member"],
            row["candidate_finished_receiver_member"],
        )
        for row in preflight.inventory.get("fixed_panel_kicker_screws", ())
        if row.get("candidate_finished_receiver_member")
        != row.get("source_finished_receiver_member")
    }
    redirected_ids = {
        axis_id
        for receiver_cuts in redirected_panel_cutters_by_candidate_part.values()
        for axis_id in receiver_cuts
    }
    if set(redirected_rows) != redirected_ids:
        raise ValueError("redirected receiver rows and candidate cuts differ")

    applied_extensions = {host_id: dict(cuts) for host_id, cuts in extensions.items()}
    for axis_id, (source_receiver, candidate_receiver) in redirected_rows.items():
        if candidate_receiver not in redirected_panel_cutters_by_candidate_part:
            raise ValueError(f"{axis_id} candidate receiver is missing: {candidate_receiver}")
        if source_receiver not in preflight.host_ids:
            raise ValueError(f"{axis_id} source receiver is outside composed hosts")
        source_cuts = final[source_receiver]
        extension_id = f"panel_purchase/{axis_id}"
        if axis_id not in source_cuts or extension_id not in source_cuts:
            raise ValueError(
                f"{axis_id} old receiver must have both native and purchase cuts "
                "before receiver redirection"
            )
        del source_cuts[axis_id]
        del source_cuts[extension_id]
        del applied_extensions[source_receiver][extension_id]

    return final, applied_extensions


def _replaced_source_cutter_ids(
    source_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]],
    replaced_source_axis_ids: frozenset[str],
) -> frozenset[str]:
    """Expand replaced screw IDs to their separate source head-recess cuts."""
    keys = {
        cutter_id
        for cutter_map in source_cutters_by_host.values()
        for cutter_id in cutter_map
    }
    replaced = set(replaced_source_axis_ids)
    result = {
        cutter_id
        for cutter_id in keys
        if cutter_id in replaced
        or (
            cutter_id.endswith("/head")
            and cutter_id.removesuffix("/head") in replaced
        )
    }
    missing = replaced - result
    if missing:
        raise ValueError(
            "replaced source axes are missing from candidate host cuts: "
            + ", ".join(sorted(missing))
        )
    return frozenset(result)


def _machine_candidate_parts(
    raw_parts: Mapping[str, cq.Shape],
    design_cuts: Mapping[str, tuple[cq.Shape, ...]],
    candidate_bores_by_part: Mapping[str, Mapping[str, cq.Shape]],
    purchased_panel_cutters_by_part: Mapping[str, Mapping[str, cq.Shape]],
) -> dict[str, cq.Shape]:
    """Apply each body's non-bore design cuts and all assigned receivers."""
    if set(candidate_bores_by_part) != set(raw_parts):
        raise ValueError("candidate bore host IDs must match all raw candidate parts")
    if not set(purchased_panel_cutters_by_part) <= set(raw_parts):
        raise ValueError("candidate panel purchase cuts reference an unknown part")
    result = {}
    for part_id, raw_shape in raw_parts.items():
        if not isinstance(raw_shape, cq.Shape) or not raw_shape.isValid():
            raise ValueError(f"raw candidate part is invalid: {part_id}")
        cutters = [
            *design_cuts.get(part_id, ()),
            *candidate_bores_by_part[part_id].values(),
            *purchased_panel_cutters_by_part.get(part_id, {}).values(),
        ]
        if any(
            not isinstance(cutter, cq.Shape) or not cutter.isValid()
            for cutter in cutters
        ):
            raise ValueError(f"candidate part has an invalid cutter: {part_id}")
        finished = raw_shape.cut(*cutters).clean() if cutters else raw_shape
        if not finished.isValid() or not finished.Solids():
            raise ValueError(f"candidate part machining produced invalid solid: {part_id}")
        result[part_id] = finished
    return result


def _retained_legacy_parts(
    inventory: Mapping[str, Any], right_rail: Any, replaced_source_axis_ids: frozenset[str]
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape]]:
    duty_rows = _duty_rows(inventory)
    all_duty_ids = set(duty_rows)
    retained_duty_ids = all_duty_ids - TARGET_STATIONS
    if len(retained_duty_ids) != EXPECTED_RETAINED_LEGACY_CLIP_COUNT:
        raise ValueError("WJ12 must leave exactly 12 legacy connector duties retained")
    right_clips = _shape_map(right_rail, "retained_legacy_clip_shapes", "right integration")
    if not retained_duty_ids <= set(right_clips):
        raise ValueError("right integration omitted one or more retained legacy clips")
    clips = {name: right_clips[name] for name in sorted(retained_duty_ids)}

    all_axis_ids = {
        axis["axis_id"]
        for row in inventory.get("legacy_duties", ())
        for axis in row.get("legacy_sds_axes", ())
    }
    retained_axis_ids = all_axis_ids - set(replaced_source_axis_ids)
    source_axes = _shape_map(
        right_rail, "retained_source_axis_shapes", "right integration"
    )
    if not retained_axis_ids <= set(source_axes):
        raise ValueError("right integration omitted one or more retained legacy SDS axes")
    axes = {axis_id: source_axes[axis_id] for axis_id in sorted(retained_axis_ids)}
    if len(axes) != EXPECTED_RETAINED_LEGACY_SDS_COUNT:
        raise ValueError("WJ12 must leave exactly 72 legacy SDS axes retained")
    return clips, axes


def compose_trial_geometry(
    preflight: SourceCutterPreflight,
    compact_outer: Any,
    right_rail: Any,
    center_x190: Any,
    *,
    purchased_panel_cutters_by_host: Mapping[str, Mapping[str, cq.Shape]],
) -> WJ12ComposedGeometry:
    """Build one host map after source cutter reconstruction has passed."""
    source = preflight.source
    binding = preflight.source_binding
    if validate_source_binding(source) != binding:
        raise ValueError("source binding changed after cutter preflight")
    inventory = preflight.inventory
    _inventory_matches_source_binding(inventory, binding)
    if right_rail.source_binding != binding or compact_outer.source_binding != binding:
        raise ValueError("family source bindings differ from successful preflight")
    if right_rail.source is not source:
        raise ValueError(
            "right geometry and source preflight must share one source object"
        )
    center_fingerprints = center_x190.source_fingerprints_sha256
    if (
        center_fingerprints.get("docs/wood-joints-mvp/source-inventory.json")
        != binding.inventory_sha256
    ):
        raise ValueError(
            "center x190 inventory fingerprint differs from source preflight"
        )

    family_source_fingerprints = {
        "wj03_compact_outer": _validate_fingerprint_map(
            compact_outer.source_pins, context="WJ-03 compact outer"
        ),
        "right_rail": _validate_fingerprint_map(
            right_rail.source_inputs_sha256, context="right rail"
        ),
        "center_x190": _validate_fingerprint_map(
            center_x190_probe._source_fingerprints(), context="center x190"
        ),
        "center_x190_tools": _validate_fingerprint_map(
            center_x190.tool_source_fingerprints_sha256,
            context="center x190 tools",
        ),
    }
    if dict(center_fingerprints) != family_source_fingerprints["center_x190"]:
        raise ValueError("center x190 source fingerprints changed after materialization")
    if dict(center_x190.tool_source_fingerprints_sha256) != family_source_fingerprints[
        "center_x190_tools"
    ]:
        raise ValueError("center x190 tool fingerprints changed after materialization")
    if right_rail.inventory.get("source_commit") != inventory.get("source_commit"):
        raise ValueError("right geometry and source preflight commits differ")
    if set(compact_outer.source_binding.duty_host_mapping) != WJ03_STATIONS:
        raise ValueError("compact outer family does not cover its four source duties")
    if set(right_rail.duties) != RIGHT_STATIONS:
        raise ValueError("right family does not cover the four G7/WJ06 source duties")
    if set(right_rail.trial_ids) != {
        right_integration.FAMILY_WJ04,
        right_integration.FAMILY_WJ06,
    }:
        raise ValueError("right family trial ID mapping is incomplete")
    if center_x190.trial_id != center_offset.TRIAL_ID:
        raise ValueError("center-post geometry is not the current x190 trial")

    hosts = source_host_ids(inventory)
    if hosts != preflight.host_ids:
        raise ValueError("source host union changed after successful preflight")
    source_raw = dict(preflight.raw_hosts)
    moved_posts = _validate_center_raw_posts(source_raw, center_x190)
    raw_hosts = {name: source_raw[name] for name in hosts}
    raw_hosts.update(moved_posts)

    removed_axis_ids, _target_axes = _target_source_axes(inventory)
    right_removed = frozenset(right_rail.replaced_source_axis_ids)
    expected_right_removed = frozenset(
        axis_id for station_id in RIGHT_STATIONS for axis_id in _target_axes[station_id]
    )
    if right_removed != expected_right_removed or len(right_removed) != 24:
        raise ValueError(
            "right G7/WJ06 geometry must replace exactly its 24 source SDS axes"
        )
    if len(TARGET_STATIONS) != EXPECTED_DUTY_COUNT:
        raise ValueError("target duty composition must contain exactly 12 stations")

    bores = _candidate_axis_map(compact_outer, right_rail, center_x190)
    expected_center_stations = {row["interface_id"] for row in center_x190.axes}
    if not CENTER_STATIONS <= expected_center_stations:
        raise ValueError(
            "center x190 candidate axes do not cover its four target duties"
        )
    if expected_center_stations != CENTER_STATIONS:
        raise ValueError("center x190 axes must cover exactly its four target duties")
    hardware = _collect_candidate_installed_hardware(
        compact_outer, right_rail, center_x190
    )
    if set(hardware) != set(bores):
        raise ValueError("candidate bore and installed hardware axis IDs differ")
    raw_candidates, design_cuts = _candidate_parts(
        compact_outer, right_rail, center_x190
    )
    if set(raw_candidates) & set(hosts):
        raise ValueError("candidate body IDs overlap canonical source host IDs")
    receiver_ids = set(hosts) | set(raw_candidates)
    candidate_bores_by_host: dict[str, dict[str, cq.Shape]] = {
        name: {} for name in receiver_ids
    }
    for axis_id, axis in bores.items():
        unknown = set(axis.receiver_ids) - candidate_bores_by_host.keys()
        if unknown:
            raise ValueError(
                f"{axis_id} refers to missing candidate receivers: {sorted(unknown)}"
            )
        for receiver_id in axis.receiver_ids:
            candidate_bores_by_host[receiver_id][axis_id] = axis.shape

    candidate_panel_cuts = _candidate_panel_extension_map(
        preflight, set(raw_candidates)
    )
    (
        additional_finished_source_parts,
        additional_purchased_panel_cutters_by_host,
        additional_source_reconstruction,
    ) = _additional_panel_receiver_overlays(preflight)
    final_source_cutters, applied_panel_cuts = _final_source_cutters(
        preflight,
        purchased_panel_cutters_by_host,
        candidate_panel_cuts,
    )
    replaced_source_cut_ids = _replaced_source_cutter_ids(
        final_source_cutters, removed_axis_ids
    )

    finished_hosts = right_integration.machine_shared_hosts(
        raw_hosts,
        final_source_cutters,
        replaced_source_axis_ids=replaced_source_cut_ids,
        candidate_bores_by_host={
            host_id: candidate_bores_by_host[host_id] for host_id in hosts
        },
    )

    finished_candidates = _machine_candidate_parts(
        raw_candidates,
        design_cuts,
        {
            name: candidate_bores_by_host[name]
            for name in raw_candidates
        },
        candidate_panel_cuts,
    )

    panel_replacements = {
        name: right_rail.panels[name] for name in sorted(RIGHT_PANEL_NAMES)
    }
    compact_panels = {
        name: part.shape for name, part in compact_outer.panel_replacements.items()
    }
    if (
        set(panel_replacements) != RIGHT_PANEL_NAMES
        or set(compact_panels) != RIGHT_PANEL_NAMES
    ):
        raise ValueError(
            "composition requires exactly the three right panel replacements"
        )
    for name in RIGHT_PANEL_NAMES:
        if not _same_shape(panel_replacements[name], compact_panels[name]):
            raise ValueError(f"family panel replacement mismatch: {name}")
        if name not in center_x190.parts or not _same_shape(
            panel_replacements[name], center_x190.parts[name]
        ):
            raise ValueError(f"center x190 panel replacement mismatch: {name}")

    fixed_axes = _shape_map(center_x190, "fixed_axes", "center x190")
    frame_records = tuple(center_x190.frame_records)
    frame_shapes = _shape_map(center_x190, "frame_shapes", "center x190")
    if len(fixed_axes) != EXPECTED_PANEL_AXIS_COUNT:
        raise ValueError(
            "composition must preserve the exact 66 fixed panel screw axes"
        )
    _validate_frame_bolt_shapes(inventory, frame_records, frame_shapes)
    retained_clips, retained_sds = _retained_legacy_parts(
        inventory, right_rail, removed_axis_ids
    )
    protected = {
        family: dict(shapes) for family, shapes in right_rail.protected.items()
    }
    protected["retained_legacy_clips"] = retained_clips
    protected["retained_legacy_sds_axes"] = retained_sds

    family_trial_ids = {
        "wj03_outer": compact_outer.trial_id,
        "wj05_backer": compact_outer.trial_id,
        right_integration.FAMILY_WJ04: right_rail.trial_ids[
            right_integration.FAMILY_WJ04
        ],
        right_integration.FAMILY_WJ06: right_rail.trial_ids[
            right_integration.FAMILY_WJ06
        ],
        "center_x190": center_x190.trial_id,
    }
    return WJ12ComposedGeometry(
        trial_id=TRIAL_ID,
        source=source,
        source_binding=binding,
        source_inventory_sha256=binding.inventory_sha256,
        source_inventory=_readonly_map(inventory),
        family_source_fingerprints=_readonly_map(
            {
                name: _readonly_map(rows)
                for name, rows in family_source_fingerprints.items()
            }
        ),
        family_trial_ids=_readonly_map(family_trial_ids),
        target_station_ids=tuple(sorted(TARGET_STATIONS)),
        raw_hosts=_readonly_map(raw_hosts),
        finished_hosts=_readonly_map(finished_hosts),
        raw_candidate_parts=_readonly_map(raw_candidates),
        finished_candidate_parts=_readonly_map(finished_candidates),
        candidate_bores=_readonly_map(bores),
        candidate_installed_hardware=_readonly_map(hardware),
        replaced_source_axis_ids=removed_axis_ids,
        replaced_source_cutter_ids=replaced_source_cut_ids,
        source_cutters_by_host=preflight.source_cutters_by_host,
        applied_source_cutters_by_host=_readonly_map(
            {name: _readonly_map(rows) for name, rows in final_source_cutters.items()}
        ),
        purchased_panel_cutters_by_host=_readonly_map(
            {name: _readonly_map(rows) for name, rows in applied_panel_cuts.items()}
        ),
        purchased_panel_cutters_by_candidate_part=_readonly_map(
            {name: _readonly_map(rows) for name, rows in candidate_panel_cuts.items()}
        ),
        additional_finished_source_parts=_readonly_map(
            additional_finished_source_parts
        ),
        additional_purchased_panel_cutters_by_host=_readonly_map(
            {
                name: _readonly_map(rows)
                for name, rows in additional_purchased_panel_cutters_by_host.items()
            }
        ),
        additional_source_reconstruction=_readonly_map(
            {
                name: _readonly_map(row)
                for name, row in additional_source_reconstruction.items()
            }
        ),
        source_reconstruction=preflight.reconstruction,
        panel_replacements=_readonly_map(panel_replacements),
        fixed_axes=_readonly_map(fixed_axes),
        frame_bolt_records=frame_records,
        frame_bolt_shapes=_readonly_map(frame_shapes),
        protected=_readonly_map(
            {family: _readonly_map(shapes) for family, shapes in protected.items()}
        ),
    )


def materialize_wj12_geometry() -> WJ12ComposedGeometry:
    """Materialize and compose the three source-bound family trials serially.

    This performs CAD booleans. Call only from the serialized geometry slot.
    It writes no files and performs no collision, strength, or release checks.
    """
    compact_before = compact_access._source_pins()
    right_before = right_integration._source_inputs_sha256()
    center_before = center_x190_probe._source_fingerprints()
    center_tools_before = center_x190_probe._tool_source_fingerprints()
    inventory = json.loads(WJ03_SOURCE_INVENTORY.read_text())
    hosts = source_host_ids(inventory)

    right = right_integration.materialize_right_rail_geometry()
    if right_integration._source_inputs_sha256() != right_before:
        raise ValueError("right-rail source inputs changed during WJ12 materialization")
    if right.source_inputs_sha256 != right_before:
        raise ValueError("right-rail source fingerprints differ from WJ12 start")
    preflight = preflight_source_cutter_map(
        right.source,
        right_integration.source_native_cutters_by_host(right.source, hosts),
        inventory,
    )

    compact = compact_access.materialize_geometry()
    if compact_access._source_pins() != compact_before:
        raise ValueError("WJ-03 source pins changed during WJ12 materialization")
    if dict(compact.source_pins) != compact_before:
        raise ValueError("WJ-03 materialization returned stale source pins")

    center = center_x190_probe.materialize_geometry()
    if center_x190_probe._source_fingerprints() != center_before:
        raise ValueError("center x190 source files changed during WJ12 materialization")
    if center_x190_probe._tool_source_fingerprints() != center_tools_before:
        raise ValueError("center x190 tool files changed during WJ12 materialization")
    if center.source_fingerprints_sha256 != center_before:
        raise ValueError("center x190 materialization returned stale source fingerprints")
    if center.tool_source_fingerprints_sha256 != center_tools_before:
        raise ValueError("center x190 materialization returned stale tool fingerprints")

    geometry = compose_trial_geometry(
        preflight,
        compact,
        right,
        center,
        purchased_panel_cutters_by_host=(
            right_integration.candidate_panel_purchase_cutters_by_host(
                right.source, inventory, hosts
            )
        ),
    )

    # Recheck every declared family input after all materialization and host
    # composition, so the resulting report cannot mix source revisions.
    for family, fingerprints in geometry.family_source_fingerprints.items():
        _validate_fingerprint_map(fingerprints, context=family)
    if validate_source_binding(right.source) != geometry.source_binding:
        raise ValueError("WJ12 source binding changed during final composition")
    return geometry


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


def composition_report(geometry: WJ12ComposedGeometry) -> dict[str, Any]:
    """Return a shape-free JSON report bound to one composed WJ12 object."""
    if geometry.trial_id != TRIAL_ID or geometry.status != "unaccepted_integrated_hypothesis":
        raise ValueError("report requires the current unaccepted WJ12 trial")
    if validate_source_binding(geometry.source) != geometry.source_binding:
        raise ValueError("composed geometry source binding changed before reporting")
    inventory = geometry.source_inventory
    duty_rows = _duty_rows(inventory)
    axes_by_id = {
        axis["axis_id"]: (row["legacy_station_id"], axis)
        for row in inventory.get("legacy_duties", ())
        for axis in row.get("legacy_sds_axes", ())
    }
    fixed_rows = {
        row["axis_id"]: row
        for row in inventory.get("fixed_panel_kicker_screws", ())
    }
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": geometry.status,
        "claim_boundary": (
            "Source-bound diagnostic composition only. It does not establish "
            "cross-family clearance, joint capacity, installation, fabrication, "
            "inspection, or structural release."
        ),
        "source": {
            "candidate": inventory.get("candidate"),
            "source_commit": inventory.get("source_commit"),
            "source_inventory_sha256": geometry.source_inventory_sha256,
            "runtime_module_sha256": dict(
                sorted(geometry.source_binding.runtime_module_sha256.items())
            ),
        },
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
                "replaced_source_sds_axis_ids": list(
                    _target_source_axes(inventory)[1][station_id]
                ),
            }
            for station_id in geometry.target_station_ids
        ],
        "source_reconstruction": {
            host_id: dict(row)
            for host_id, row in sorted(geometry.source_reconstruction.items())
        },
        "source_cut_operations": {
            host_id: {
                "reconstructed_native_cut_ids": sorted(cutters),
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
                "legacy_station_id": axes_by_id[axis_id][0],
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
        "additional_source_reconstruction": {
            host_id: dict(row)
            for host_id, row in sorted(geometry.additional_source_reconstruction.items())
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
        "fixed_panel_axes": sorted(fixed_rows),
        "frame_bolts": [dict(row) for row in geometry.frame_bolt_records],
        "protected_inventory_counts": {
            family: len(shapes) for family, shapes in sorted(geometry.protected.items())
        },
        "gates": geometry.gates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the JSON report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = composition_report(materialize_wj12_geometry())
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
