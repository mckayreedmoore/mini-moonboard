"""Four-duty left service-rail geometry hypothesis, bound to the source.

This local diagnostic mirrors the existing right inner/outer rail geometry
while retaining the left members' own source machining.  It is a nominal
geometry study only; it does not establish access, capacity, release, or
acceptance, and it does not build any family geometry at import time.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT_MM
from mini_moonboard.wood_joint_frame import validate_source_binding
from mini_moonboard.wood_joint_geometry import (
    BoltStack,
    StackLayer,
    WasherSeat,
    washer_support_report,
)
from mini_moonboard.wood_joint_panel_machining import PANEL_NAMES
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_right_rail_integration as right_integration
from scripts import wood_joint_wj04_probe as wj04_base
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as wj04_inner
from scripts import wood_joint_wj06_outer_pair_probe as wj06_outer

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_left_rail_integration/v1"
TRIAL_ID = "left_service_mirrored_inner_outer_hypothesis"
HIT_TOLERANCE_MM3 = 1e-6
SOURCE_RECONSTRUCTION_TOLERANCE_MM3 = 1e-3
LAYER_FRACTION_TOLERANCE = 1e-6
CONTACT_PROBE_MM = 0.1

INNER_SOURCE_TO_LEFT = {
    wj04_inner.LOWER_STATION: "clip_horizontal_lower_left_2",
    wj04_inner.UPPER_STATION: "clip_horizontal_upper_left_2",
}
OUTER_SOURCE_TO_LEFT = {
    wj06_outer.LOWER_STATION: "clip_horizontal_lower_left_1",
    wj06_outer.UPPER_STATION: "clip_horizontal_upper_left_1",
}
SOURCE_TO_LEFT_DUTY = {**INNER_SOURCE_TO_LEFT, **OUTER_SOURCE_TO_LEFT}

LOWER_RAIL_LEFT = "base_rail_service_lower_left"
UPPER_RAIL_LEFT = "base_rail_service_upper_left"
PRINCIPAL_LEFT = "base_principal_center_left"
SIDE_LEFT = "base_side_left"
SHARED_HOSTS = frozenset(
    {LOWER_RAIL_LEFT, UPPER_RAIL_LEFT, PRINCIPAL_LEFT, SIDE_LEFT}
)
SOURCE_HOSTS = frozenset(
    {LOWER_RAIL_LEFT, UPPER_RAIL_LEFT, PRINCIPAL_LEFT, SIDE_LEFT}
)
TARGET_STATIONS = frozenset(SOURCE_TO_LEFT_DUTY.values())

INNER_LOWER_CLEAT = "left_service_inner_lower_cleat"
INNER_UPPER_CLEAT = "left_service_inner_upper_cleat"
OUTER_LOWER_CLEAT = "left_service_outer_lower_cleat"
OUTER_UPPER_CLEAT = "left_service_outer_upper_cleat"
CLEAT_BY_LEFT_STATION = {
    "clip_horizontal_lower_left_2": INNER_LOWER_CLEAT,
    "clip_horizontal_upper_left_2": INNER_UPPER_CLEAT,
    "clip_horizontal_lower_left_1": OUTER_LOWER_CLEAT,
    "clip_horizontal_upper_left_1": OUTER_UPPER_CLEAT,
}

INNER_FULL_SIZE_MM = (88.9, 88.9, 119.7)
INNER_LOWER_ORIGIN_MM = (89.05, 1353.874134, 229.840968)
INNER_UPPER_FULL_ORIGIN_MM = (89.05, 1497.924134, 229.840968)
INNER_UPPER_FULL_DEPTH_MM = 119.7
OUTER_KERF_UNDO_MM = KERF_RIGHT_MM
OUTER_EXPECTED_X_BOUNDS_MM = (-1130.3, -1041.4)
OUTER_EXPECTED_RAIL_AXIS_X_MM = -1084.85
OUTER_EXPECTED_SIDE_START_X_MM = -1041.4

_RIGHT_TO_LEFT_MEMBER = {
    wj04_inner.LOWER_RAIL: LOWER_RAIL_LEFT,
    wj04_inner.UPPER_RAIL: UPPER_RAIL_LEFT,
    wj04_inner.PRINCIPAL: PRINCIPAL_LEFT,
    wj06_outer.LOWER_RAIL: LOWER_RAIL_LEFT,
    wj06_outer.UPPER_RAIL: UPPER_RAIL_LEFT,
    wj06_outer.SIDE_HOST: SIDE_LEFT,
    wj04_inner.LOWER_CLEAT: INNER_LOWER_CLEAT,
    wj04_inner.UPPER_CLEAT: INNER_UPPER_CLEAT,
    wj06_outer.LOWER_CLEAT: OUTER_LOWER_CLEAT,
    wj06_outer.UPPER_CLEAT: OUTER_UPPER_CLEAT,
}

_INPUT_PATHS = tuple(
    sorted(
        set(wj04_inner.SOURCE_INPUTS)
        | set(wj06_outer.SOURCE_INPUTS)
        | {
            INVENTORY_PATH,
            "docs/wood-joints-mvp/hypotheses/remaining-duty-sequence.md",
            "docs/wood-joints-mvp/hypotheses/right-rail-integration.md",
            "docs/wood-joints-mvp/ordinary-hardware-basis.md",
            "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md",
            "scripts/wood_joint_right_rail_integration.py",
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
            "scripts/wood_joint_wj06_outer_pair_probe.py",
            "scripts/wood_joint_left_rail_integration.py",
        }
    )
)


@dataclass(frozen=True)
class LeftServiceGeometry:
    """Four-duty candidate overlay plus source-bound geometric evidence."""

    source: Any
    source_binding: Any
    inventory: dict[str, Any]
    source_inputs_sha256: dict[str, str]
    producer_bindings: dict[str, str]
    trial_ids: dict[str, str]
    duties: dict[str, dict[str, Any]]
    stack_provenance: dict[str, dict[str, Any]]
    replaced_axis_ids: frozenset[str]
    combined_replaced_axis_ids: frozenset[str]
    retained_source_axis_shapes: dict[str, cq.Shape]
    retained_legacy_clip_shapes: dict[str, cq.Shape]
    parts: dict[str, cq.Shape]
    finished: dict[str, cq.Shape]
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    installed: dict[str, dict[str, cq.Shape]]
    bore_members: dict[str, tuple[str, ...]]
    candidate_bores_by_host: dict[str, dict[str, cq.Shape]]
    native_source_cutters_by_host: dict[str, dict[str, cq.Shape]]
    purchased_panel_cutters_by_host: dict[str, dict[str, cq.Shape]]
    source_cutters_by_host: dict[str, dict[str, cq.Shape]]
    source_reconstruction: dict[str, dict[str, Any]]
    source_axis_datum_audit: dict[str, dict[str, Any]]
    panels: dict[str, cq.Shape]
    all_wood: dict[str, cq.Shape]
    protected: dict[str, dict[str, cq.Shape]]
    bore_reports: dict[str, dict[str, Any]]
    cross_bore_hits_mm3: dict[str, dict[str, float]]
    candidate_body_hits: dict[str, dict[str, Any]]
    installed_hits: dict[str, dict[str, Any]]
    washer_support: dict[str, dict[str, Any]]
    body_solid_checks: dict[str, dict[str, Any]]
    machining: dict[str, dict[str, Any]]
    diagnostic_gates: dict[str, Any]
    release: dict[str, bool]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_inputs_sha256() -> dict[str, str]:
    return {path: _sha256(ROOT / path) for path in _INPUT_PATHS}


def _selected_duties(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_hosts = {
        "clip_horizontal_lower_left_1": [LOWER_RAIL_LEFT, SIDE_LEFT],
        "clip_horizontal_upper_left_1": [UPPER_RAIL_LEFT, SIDE_LEFT],
        "clip_horizontal_lower_left_2": [LOWER_RAIL_LEFT, PRINCIPAL_LEFT],
        "clip_horizontal_upper_left_2": [UPPER_RAIL_LEFT, PRINCIPAL_LEFT],
    }
    rows = {
        row["legacy_station_id"]: row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in TARGET_STATIONS
    }
    if set(rows) != TARGET_STATIONS:
        raise ValueError("left-service hypothesis requires its exact four duties")

    axis_ids: list[str] = []
    for station_id, expected_members in expected_hosts.items():
        row = rows[station_id]
        if row["legacy_host_members"] != expected_members:
            raise ValueError(f"{station_id}: left source host mapping changed")
        axes = row["legacy_sds_axes"]
        if len(axes) != 6 or any(
            axis.get("shop_opening_kind") != "sds_wood" for axis in axes
        ):
            raise ValueError(f"{station_id}: expected six source SDS axes")
        if {axis.get("axis_role") for axis in axes} != {"beam", "upright"}:
            raise ValueError(f"{station_id}: beam/upright axis roles changed")
        for axis in axes:
            if axis.get("members", [None])[0] != station_id:
                raise ValueError(f"{station_id}: legacy axis ownership changed")
            host_members = set(axis.get("members", ())) - {station_id}
            if len(host_members) != 1 or not host_members <= set(expected_members):
                raise ValueError(f"{station_id}: legacy axis host changed")
            axis_ids.append(axis["axis_id"])
    if len(axis_ids) != 24 or len(set(axis_ids)) != 24:
        raise ValueError("left-service slice must replace exactly 24 unique SDS axes")
    return rows


def _canonical_inventory(inventory: dict[str, Any] | None) -> dict[str, Any]:
    payload = (ROOT / INVENTORY_PATH).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("live source inventory differs from canonical source pin")
    canonical = json.loads(payload)
    if inventory is not None and inventory != canonical:
        raise ValueError("caller inventory content differs from canonical source file")
    if canonical.get("candidate") != wj06_outer.CANDIDATE:
        raise ValueError("canonical inventory candidate changed")
    if (
        len(canonical.get("legacy_duties", ())) != 24
        or sum(len(row.get("legacy_sds_axes", ())) for row in canonical["legacy_duties"])
        != 144
        or len(canonical.get("fixed_panel_kicker_screws", ())) != 66
        or len(canonical.get("starting_frame_bolts", ())) != 12
    ):
        raise ValueError("canonical inventory schema or pinned counts changed")
    return canonical


def _left_station_metadata() -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for spec in wj04_inner.STACK_SPECS:
        result.append({
            "family": "inner",
            "source_stack_id": spec.stack_id,
            "source_station_id": spec.station_id,
            "target_station_id": INNER_SOURCE_TO_LEFT[spec.station_id],
            "source_cleat_id": spec.cleat_id,
            "interface_id": spec.interface_id,
        })
    for spec in wj06_outer.STACK_SPECS:
        result.append({
            "family": "outer",
            "source_stack_id": spec.stack_id,
            "source_station_id": spec.station_id,
            "target_station_id": OUTER_SOURCE_TO_LEFT[spec.station_id],
            "source_cleat_id": spec.cleat_id,
            "interface_id": spec.interface_id,
        })
    if len(result) != 16:
        raise ValueError("left-service proposal requires exactly 16 stack mappings")
    return tuple(result)


def _source_stack_key(family: str, stack_id: str) -> str:
    if family == "inner":
        return right_integration._namespace(
            right_integration.FAMILY_WJ04, wj04_inner.TRIAL_ID, stack_id
        )
    if family == "outer":
        return right_integration._namespace(
            right_integration.FAMILY_WJ06, wj06_outer.TRIAL_ID, stack_id
        )
    raise ValueError(f"unknown left-service source family: {family}")


def mirror_point_x(point: cq.Vector, *, undo_outer_kerf: bool = False) -> cq.Vector:
    """Reflect a right-side point; outer points first return to source X datum."""
    x = point.x + (OUTER_KERF_UNDO_MM if undo_outer_kerf else 0.0)
    return cq.Vector(-x, point.y, point.z)


def mirror_direction_x(direction: cq.Vector) -> cq.Vector:
    """Reflect a vector without translating it."""
    return cq.Vector(-direction.x, direction.y, direction.z)


def mirror_shape_x(shape: cq.Shape, *, undo_outer_kerf: bool = False) -> cq.Shape:
    """Mirror candidate geometry; only the outer family undoes kerf first."""
    shifted = (
        shape.translate((OUTER_KERF_UNDO_MM, 0.0, 0.0))
        if undo_outer_kerf
        else shape
    )
    mirrored = shifted.mirror("YZ")
    if not mirrored.isValid() or not mirrored.Solids():
        raise ValueError("mirrored left-service candidate shape is invalid")
    return mirrored


def _left_cleat_shapes(right_geometry: Any) -> dict[str, cq.Shape]:
    parts = right_geometry.parts
    required = {
        wj04_inner.LOWER_CLEAT,
        wj06_outer.LOWER_CLEAT,
        wj06_outer.UPPER_CLEAT,
    }
    if not required <= parts.keys():
        raise ValueError("corrected right geometry is missing source cleat shapes")
    lower_inner = mirror_shape_x(parts[wj04_inner.LOWER_CLEAT])
    upper_full_right = wj04_base._box_in_trial_frame(
        WJ04_TRIAL, INNER_UPPER_FULL_ORIGIN_MM, INNER_FULL_SIZE_MM
    )
    upper_inner = mirror_shape_x(upper_full_right)
    lower_outer = mirror_shape_x(
        parts[wj06_outer.LOWER_CLEAT], undo_outer_kerf=True
    )
    upper_outer = mirror_shape_x(
        parts[wj06_outer.UPPER_CLEAT], undo_outer_kerf=True
    )
    expected = {
        INNER_LOWER_CLEAT: lower_inner,
        INNER_UPPER_CLEAT: upper_inner,
        OUTER_LOWER_CLEAT: lower_outer,
        OUTER_UPPER_CLEAT: upper_outer,
    }
    if set(expected) != set(CLEAT_BY_LEFT_STATION.values()):
        raise ValueError("candidate cleat IDs do not map one-to-one to duties")
    upper_n = [vertex.Center().dot(cq.Vector(*WJ04_TRIAL.frame.n_global)) for vertex in upper_inner.Vertices()]
    if not math.isclose(
        max(upper_n) - min(upper_n), INNER_UPPER_FULL_DEPTH_MM, abs_tol=1e-6
    ):
        raise ValueError("left inner upper cleat must retain full 119.7 mm N depth")
    outer_x = [vertex.Center().x for vertex in lower_outer.Vertices()]
    actual_bounds = (min(outer_x), max(outer_x))
    if any(
        abs(actual - expected_value) > 1e-6
        for actual, expected_value in zip(
            actual_bounds, OUTER_EXPECTED_X_BOUNDS_MM, strict=True
        )
    ):
        raise ValueError(
            "outer cleat did not undo right kerf translation before mirroring"
        )
    return expected


def _mirror_stack(
    source_stack: BoltStack,
    *,
    stack_key: str,
    member_map: dict[str, str],
    undo_outer_kerf: bool,
) -> BoltStack:
    missing = {layer.body_id for layer in source_stack.layers} - member_map.keys()
    if missing:
        raise ValueError("stack layer is outside the left-service source mapping")
    direction = mirror_direction_x(source_stack.direction)
    layers = tuple(
        StackLayer(member_map[layer.body_id], layer.thickness_mm)
        for layer in source_stack.layers
    )
    head = WasherSeat(
        member_map[source_stack.head_seat.body_id],
        mirror_point_x(source_stack.head_seat.center, undo_outer_kerf=undo_outer_kerf),
        mirror_direction_x(source_stack.head_seat.inward_normal),
    )
    nut = WasherSeat(
        member_map[source_stack.nut_seat.body_id],
        mirror_point_x(source_stack.nut_seat.center, undo_outer_kerf=undo_outer_kerf),
        mirror_direction_x(source_stack.nut_seat.inward_normal),
    )
    return BoltStack(
        id=stack_key,
        hardware=source_stack.hardware,
        under_head_origin=mirror_point_x(
            source_stack.under_head_origin, undo_outer_kerf=undo_outer_kerf
        ),
        direction=direction,
        layers=layers,
        head_seat=head,
        nut_seat=nut,
        required_tip_projection_mm=source_stack.required_tip_projection_mm,
    )


def _vector_tuple(vector: cq.Vector, digits: int = 9) -> list[float]:
    return [round(value, digits) for value in vector.toTuple()]


def _intersection_volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _hits(shape: cq.Shape, others: dict[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := _intersection_volume(shape, other)) > HIT_TOLERANCE_MM3
    }


def _symmetric_difference_volume(first: cq.Shape, second: cq.Shape) -> float:
    return first.cut(second).Volume() + second.cut(first).Volume()


def _combined_protected(
    right_geometry: Any,
    source: Any,
    inventory: dict[str, Any],
    replaced_axis_ids: frozenset[str],
    target_duties: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, cq.Shape]], dict[str, cq.Shape], dict[str, cq.Shape]]:
    protected = {
        family: dict(shapes) for family, shapes in right_geometry.protected.items()
    }
    connection_by_id = {row.name: row for row in source.connections()}
    all_replaced = frozenset(right_geometry.replaced_source_axis_ids) | replaced_axis_ids
    expected_legacy_axis_count = 144 - len(all_replaced)
    retained_axis_shapes: dict[str, cq.Shape] = {}
    for duty in inventory["legacy_duties"]:
        for axis in duty["legacy_sds_axes"]:
            axis_id = axis["axis_id"]
            if axis_id in all_replaced:
                continue
            connection = connection_by_id.get(axis_id)
            if connection is None:
                raise ValueError(f"retained legacy SDS axis missing: {axis_id}")
            retained_axis_shapes[axis_id] = (
                right_integration._source_screw_axis_shape(connection)
            )
    if len(retained_axis_shapes) != expected_legacy_axis_count or len(
        retained_axis_shapes
    ) != 96:
        raise ValueError("combined right/left slice must retain exactly 96 source SDS axes")

    replaced_duty_ids = set(right_geometry.duties) | set(target_duties)
    current_parts = {part.name: part.shape for part in source.parts()}
    retained_duty_ids = {
        row["legacy_station_id"] for row in inventory["legacy_duties"]
    } - replaced_duty_ids
    retained_clips = {
        name: current_parts[name]
        for name in retained_duty_ids
        if name in current_parts
    }
    if set(retained_clips) != retained_duty_ids or len(retained_clips) != 16:
        raise ValueError("combined right/left slice must retain exactly 16 legacy clips")

    protected["retained_legacy_sds_axes"] = retained_axis_shapes
    protected["retained_legacy_clips"] = retained_clips
    expected_protected_counts = {
        "fixed_66_hillman_axes_63p5mm": 66,
        "retained_12_frame_bolt_components": 60,
        "retained_12_frame_bolt_tools_withdrawals": 36,
        "tnuts": 142,
        "hold_hole_and_provisional_projection": 142,
        "lights": 132,
        "wires": 131,
        "retained_legacy_sds_axes": 96,
        "retained_legacy_clips": 16,
    }
    for family, count in expected_protected_counts.items():
        if len(protected.get(family, {})) != count:
            raise ValueError(
                f"combined protected source inventory changed for {family}: "
                f"{len(protected.get(family, {}))} != {count}"
            )
    return protected, retained_axis_shapes, retained_clips


def _native_left_datum_check(
    datum_audit: dict[str, dict[str, Any]],
    duties: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    expected_hosts = {
        host for duty in duties.values() for host in duty["legacy_host_members"]
    }
    checked = 0
    for axis_id, record in datum_audit.items():
        for host_id in expected_hosts.intersection(record["members"]):
            replay = record["shared_host_native_replay_starts_xyz_mm"][host_id]
            current = record["shared_host_current_adapter_starts_xyz_mm"][host_id]
            if any(abs(a - b) > 1e-9 for a, b in zip(replay, current, strict=True)):
                raise ValueError(
                    f"{axis_id}/{host_id}: left source machining is not at its own datum"
                )
            transform = record["shared_host_transforms"][host_id][
                "native_replay_member_transform"
            ]
            if transform != "identity":
                raise ValueError(
                    f"{axis_id}/{host_id}: left host unexpectedly inherited a right transform"
                )
            checked += 1
    expected_count = sum(len(row["legacy_sds_axes"]) for row in duties.values())
    if checked != expected_count:
        raise ValueError("source axis datum audit omitted one or more left SDS axes")
    return {
        "checked_left_host_axis_datums": checked,
        "source_member_transform": "identity",
        "right_outer_kerf_translation_reused_for_left_cuts": False,
    }


def _hardware_length_record(stack: BoltStack, family: str, stack_id: str) -> dict[str, Any]:
    if family == "inner":
        candidate = WJ04_TRIAL.fasteners.bolt_by_id("kl_jack_25c600hcs5z")
        minimum = candidate.nominal_length_mm - candidate.length_minus_tolerance_mm
        source_basis = "WJ-04 configured KL Jack 25C600HCS5Z 6-in ordinary-bolt model"
    elif stack_id.endswith(("rail_1", "rail_2")):
        minimum = wj06_outer.RAIL_BOLT_MIN_LENGTH_MM
        source_basis = "WJ-06 shared 6-in catalog minus-tolerance bound"
    else:
        minimum = wj06_outer.SIDE_BOLT_MIN_LENGTH_MM
        source_basis = "WJ-06 provisional 8-in ordinary-bolt catalog lead bound"
    if not math.isclose(stack.hardware.under_head_length_mm, 152.4 if (family == "inner" or stack_id.endswith(("rail_1", "rail_2"))) else 203.2, abs_tol=1e-9):
        raise ValueError(f"{stack_id}: nominal ordinary-bolt model length changed")
    if minimum > stack.hardware.under_head_length_mm:
        raise ValueError(f"{stack_id}: minimum length exceeds nominal length")
    return {
        "hardware_model": stack.hardware.candidate_sku,
        "modeled_nominal_under_head_length_mm": round(
            stack.hardware.under_head_length_mm, 6
        ),
        "source_bound_minimum_catalog_length_mm": round(minimum, 6),
        "source_basis": source_basis,
        "cad_shaft_is_a_full_length_collision_envelope": True,
        "smooth_shank_length_inferred_from_nominal_length": False,
        "hardware_selected_or_received": False,
    }


def _source_scene_geometry(
    right_geometry: Any,
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape]]:
    panels = dict(right_geometry.panels)
    if len(panels) != 6 or set(panels) != PANEL_NAMES:
        raise ValueError("corrected right geometry must retain all six panel bodies")
    return dict(right_geometry.all_wood), panels


def materialize_left_service_geometry(
    right_geometry: Any,
    inventory: dict[str, Any] | None = None,
) -> LeftServiceGeometry:
    """Build the bounded left four-duty overlay from retained right geometry.

    This performs CAD booleans. It must be called only in the repository's
    serialized geometry slot, with the corrected right geometry retained in
    memory. It never rebuilds WJ-04 or WJ-06 family geometry.
    """
    inputs_before = _source_inputs_sha256()
    source = right_geometry.source
    binding_before = validate_source_binding(source)
    if binding_before != right_geometry.source_binding:
        raise ValueError("left service received stale right source binding")
    if binding_before.inventory_sha256 != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("left source inventory differs from canonical source pin")
    source_inputs_existing = getattr(right_geometry, "source_inputs_sha256", {})
    for path, digest in source_inputs_existing.items():
        if inputs_before.get(path) != digest:
            raise ValueError(f"right geometry input changed since materialization: {path}")
    expected_trial_ids = {
        right_integration.FAMILY_WJ04: wj04_inner.TRIAL_ID,
        right_integration.FAMILY_WJ06: wj06_outer.TRIAL_ID,
    }
    if right_geometry.trial_ids != expected_trial_ids:
        raise ValueError("left service requires the corrected right trial IDs")

    source_inventory = _canonical_inventory(inventory)
    duties = _selected_duties(source_inventory)
    replaced_axis_ids = frozenset(
        axis["axis_id"]
        for row in duties.values()
        for axis in row["legacy_sds_axes"]
    )
    if len(replaced_axis_ids) != 24:
        raise ValueError("left service must replace exactly 24 old SDS axes")
    right_duties = right_integration._selected_duties(
        source_inventory, frozenset(right_geometry.replaced_source_axis_ids)
    )
    if right_duties != right_geometry.duties:
        raise ValueError("retained right geometry no longer matches source duties")
    if replaced_axis_ids & right_geometry.replaced_source_axis_ids:
        raise ValueError("left and right source duties unexpectedly overlap")

    raw_wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    current_wood = {part.name: part.shape for part in source.parts() if part.name in raw_wood}
    if not SOURCE_HOSTS <= raw_wood.keys() or not SOURCE_HOSTS <= current_wood.keys():
        raise ValueError("canonical source is missing a left service host")

    native_cutters = right_integration.source_native_cutters_by_host(
        source, SOURCE_HOSTS
    )
    for host_id in SOURCE_HOSTS:
        host_replaced = replaced_axis_ids.intersection(native_cutters[host_id])
        if len(host_replaced) != 6:
            raise ValueError(
                f"{host_id}: expected six left legacy SDS host cutters, "
                f"found {len(host_replaced)}"
            )
    source_reconstruction: dict[str, dict[str, Any]] = {}
    for host_id in sorted(SOURCE_HOSTS):
        rebuilt = raw_wood[host_id].cut(*native_cutters[host_id].values()).clean()
        added = rebuilt.cut(current_wood[host_id]).Volume()
        missing = current_wood[host_id].cut(rebuilt).Volume()
        delta = added + missing
        source_reconstruction[host_id] = {
            "added_material_mm3": round(added, 9),
            "missing_material_mm3": round(missing, 9),
            "symmetric_difference_mm3": round(delta, 6),
            "native_source_cutters_applied": len(native_cutters[host_id]),
            "candidate_purchase_cutters_excluded": True,
            "matches_source_finished_member": (
                delta <= SOURCE_RECONSTRUCTION_TOLERANCE_MM3
            ),
        }
        if delta > SOURCE_RECONSTRUCTION_TOLERANCE_MM3:
            raise ValueError(
                f"{host_id}: left raw-stock retained-cut pass differs from source "
                f"by {delta:.6f} mm3"
            )

    source_axis_datum_audit = right_integration._source_axis_datum_audit(
        source, replaced_axis_ids, SOURCE_HOSTS
    )
    datum_policy = _native_left_datum_check(source_axis_datum_audit, duties)
    purchased = right_integration.candidate_panel_purchase_cutters_by_host(
        source, source_inventory, SOURCE_HOSTS
    )
    source_cutters = right_integration._merge_cutter_maps(native_cutters, purchased)

    cleats = _left_cleat_shapes(right_geometry)
    parts = {host_id: raw_wood[host_id] for host_id in SOURCE_HOSTS}
    parts.update(cleats)

    source_stack_metadata = _left_station_metadata()
    stacks: dict[str, BoltStack] = {}
    stack_provenance: dict[str, dict[str, Any]] = {}
    for metadata in source_stack_metadata:
        source_stack_id = metadata["source_stack_id"]
        source_key = _source_stack_key(metadata["family"], source_stack_id)
        source_stack = right_geometry.stacks.get(source_key)
        if source_stack is None:
            raise ValueError(f"corrected right geometry omitted stack {source_key}")
        target_station = metadata["target_station_id"]
        cleat_id = CLEAT_BY_LEFT_STATION[target_station]
        undo_kerf = metadata["family"] == "outer"
        member_map = dict(_RIGHT_TO_LEFT_MEMBER)
        member_map[metadata["source_cleat_id"]] = cleat_id
        stack_key = f"left_service/{TRIAL_ID}/{target_station}/{source_stack_id}"
        stack = _mirror_stack(
            source_stack,
            stack_key=stack_key,
            member_map=member_map,
            undo_outer_kerf=undo_kerf,
        )
        if any(layer.body_id not in parts for layer in stack.layers):
            raise ValueError(f"{stack_key}: reflected stack layer is not in slice")
        if stack_key in stacks:
            raise ValueError(f"duplicate left-service stack key: {stack_key}")
        stacks[stack_key] = stack
        stack_provenance[stack_key] = {
            **metadata,
            "source_stack_key": source_key,
            "target_cleat_id": cleat_id,
            "candidate_geometry_transform": (
                "undo kerf-right x translation +3.175 mm, then reflect X"
                if undo_kerf
                else "reflect X about source datum"
            ),
            **_hardware_length_record(stack, metadata["family"], source_stack_id),
        }
    if len(stacks) != 16:
        raise ValueError("left service hypothesis requires exactly 16 through-bolt stacks")

    bores: dict[str, cq.Shape] = {}
    installed: dict[str, dict[str, cq.Shape]] = {}
    candidate_bores_by_host: dict[str, dict[str, cq.Shape]] = {
        name: {} for name in parts
    }
    bore_members: dict[str, tuple[str, ...]] = {}
    for stack_key, stack in stacks.items():
        direction = stack.direction.normalized()
        bore = cq.Solid.makeCylinder(
            stack.hardware.drill_diameter_mm / 2,
            stack.grip_mm + 2 * CONTACT_PROBE_MM,
            stack.head_seat.center - direction * CONTACT_PROBE_MM,
            direction,
        )
        bores[stack_key] = bore
        installed[stack_key] = dict(stack.installed_shapes())
        layer_ids = tuple(layer.body_id for layer in stack.layers)
        if len(layer_ids) != 2 or len(set(layer_ids)) != 2:
            raise ValueError(f"{stack_key}: expected two wood layers")
        bore_members[stack_key] = layer_ids
        for member_id in layer_ids:
            candidate_bores_by_host[member_id][stack_key] = bore
    if len(bores) != 16 or len(installed) != 16:
        raise ValueError("left service bore and installed stack counts changed")

    finished = right_integration.machine_shared_hosts(
        parts,
        source_cutters,
        replaced_source_axis_ids=replaced_axis_ids,
        candidate_bores_by_host=candidate_bores_by_host,
    )
    if len(finished) != 8:
        raise ValueError("left service requires four source hosts and four cleats")

    bore_reports: dict[str, dict[str, Any]] = {}
    for stack_key, stack in stacks.items():
        direction = stack.direction.normalized()
        progress = 0.0
        fractions: dict[str, float] = {}
        for layer in stack.layers:
            segment = cq.Solid.makeCylinder(
                stack.hardware.drill_diameter_mm / 2,
                layer.thickness_mm,
                stack.head_seat.center + direction * progress,
                direction,
            )
            fraction = _intersection_volume(segment, parts[layer.body_id]) / segment.Volume()
            fractions[layer.body_id] = round(fraction, 6)
            progress += layer.thickness_mm
        bore_reports[stack_key] = {
            "source_duty_id": stack_provenance[stack_key]["target_station_id"],
            "wood_layers_head_to_nut": [
                {"member_id": layer.body_id, "thickness_mm": layer.thickness_mm}
                for layer in stack.layers
            ],
            "layer_material_fractions_before_candidate_bore": fractions,
            "all_declared_layers_present": all(
                fraction >= 1.0 - LAYER_FRACTION_TOLERANCE
                for fraction in fractions.values()
            ),
        }

    cross_bore_hits: dict[str, dict[str, float]] = {key: {} for key in bores}
    keys = sorted(bores)
    for index, first_key in enumerate(keys):
        for second_key in keys[index + 1 :]:
            overlap = _intersection_volume(bores[first_key], bores[second_key])
            if overlap > HIT_TOLERANCE_MM3:
                value = round(overlap, 6)
                cross_bore_hits[first_key][second_key] = value
                cross_bore_hits[second_key][first_key] = value

    protected, retained_axes, retained_clips = _combined_protected(
        right_geometry,
        source,
        source_inventory,
        replaced_axis_ids,
        duties,
    )
    source_scene, panels = _source_scene_geometry(right_geometry)
    all_wood = dict(source_scene)
    all_wood.update(finished)
    physical_protected = {
        family: shapes
        for family, shapes in protected.items()
        if family
        not in {
            "retained_12_frame_bolt_tools_withdrawals",
            "hold_hole_and_provisional_projection",
        }
    }
    access_protected = {
        family: protected[family]
        for family in (
            "retained_12_frame_bolt_tools_withdrawals",
            "hold_hole_and_provisional_projection",
        )
    }

    candidate_body_hits: dict[str, dict[str, Any]] = {}
    cleat_ids = set(cleats)
    for station_id, duty in duties.items():
        cleat_id = CLEAT_BY_LEFT_STATION[station_id]
        intended_hosts = set(duty["legacy_host_members"])
        other_wood = {
            name: shape
            for name, shape in source_scene.items()
            if name not in intended_hosts and name not in cleat_ids
        }
        candidate_body_hits[cleat_id] = {
            "source_duty_id": station_id,
            "intended_source_host_overlap_mm3": _hits(
                parts[cleat_id],
                {name: parts[name] for name in intended_hosts},
            ),
            "other_wood_hits_mm3": _hits(
                parts[cleat_id],
                {
                    name: shape
                    for name, shape in other_wood.items()
                    if name not in panels
                },
            ),
            "candidate_panel_hits_mm3": _hits(parts[cleat_id], panels),
            "fixed_geometry_hits_mm3": {
                family: hits
                for family, obstacles in physical_protected.items()
                if (hits := _hits(parts[cleat_id], obstacles))
            },
            "access_envelope_hits_mm3": {
                family: hits
                for family, obstacles in access_protected.items()
                if (hits := _hits(parts[cleat_id], obstacles))
            },
            "peer_candidate_cleat_hits_mm3": _hits(
                parts[cleat_id],
                {peer: shape for peer, shape in cleats.items() if peer != cleat_id},
            ),
        }

    # Include already materialized right candidate bodies and hardware in the
    # same local scene; the left family remains independently non-accepted.
    scene_wood = dict(source_scene)
    scene_wood.update(finished)
    finished_timber = dict(scene_wood)
    for station_id, duty in duties.items():
        cleat_id = CLEAT_BY_LEFT_STATION[station_id]
        intended_hosts = set(duty["legacy_host_members"])
        report = candidate_body_hits[cleat_id]
        report["intended_source_host_overlap_before_bores_mm3"] = report.pop(
            "intended_source_host_overlap_mm3"
        )
        finished_hits = _hits(
            finished[cleat_id],
            {name: shape for name, shape in finished_timber.items() if name != cleat_id},
        )
        report["finished_solid_wood_intersections_mm3"] = finished_hits
        report["intended_host_finished_solid_intersections_mm3"] = {
            name: volume
            for name, volume in finished_hits.items()
            if name in intended_hosts
        }
        report["other_finished_solid_wood_intersections_mm3"] = {
            name: volume
            for name, volume in finished_hits.items()
            if name not in intended_hosts
        }
    right_installed = dict(right_geometry.installed)
    installed_scene = {**right_installed, **installed}
    right_bores = dict(right_geometry.bores)
    all_installed_shapes = {
        f"{stack_id}/{role}": shape
        for stack_id, components in installed_scene.items()
        for role, shape in components.items()
    }
    for cleat_id, report in candidate_body_hits.items():
        report["installed_hardware_hits_mm3"] = _hits(
            finished[cleat_id], all_installed_shapes
        )
    for stack_key, bore in bores.items():
        for peer_key, peer_bore in right_bores.items():
            overlap = _intersection_volume(bore, peer_bore)
            if overlap > HIT_TOLERANCE_MM3:
                cross_bore_hits[stack_key][peer_key] = round(overlap, 6)
    bore_members_by_key = bore_members
    for stack_key, report in bore_reports.items():
        own_ids = set(bore_members_by_key[stack_key])
        report.update(
            {
                "other_wood_hits_mm3": _hits(
                    bores[stack_key],
                    {
                        name: shape
                        for name, shape in scene_wood.items()
                        if name not in own_ids and name not in panels
                    },
                ),
                "candidate_panel_hits_mm3": _hits(bores[stack_key], panels),
                "fixed_geometry_hits_mm3": {
                    family: hits
                    for family, obstacles in physical_protected.items()
                    if (hits := _hits(bores[stack_key], obstacles))
                },
                "access_envelope_hits_mm3": {
                    family: hits
                    for family, obstacles in access_protected.items()
                    if (hits := _hits(bores[stack_key], obstacles))
                },
                "other_installed_component_hits_mm3": _hits(
                    bores[stack_key],
                    {
                        f"{other_key}/{role}": shape
                        for other_key, components in installed_scene.items()
                        if other_key != stack_key
                        for role, shape in components.items()
                    },
                ),
                "right_candidate_bore_hits_mm3": _hits(
                    bores[stack_key], right_bores
                ),
            }
        )

    installed_hits: dict[str, dict[str, Any]] = {}
    washer_support: dict[str, dict[str, Any]] = {}
    for stack_key, components in installed.items():
        other_hardware = {
            f"{other_key}/{role}": shape
            for other_key, peer_components in installed_scene.items()
            if other_key != stack_key
            for role, shape in peer_components.items()
        }
        installed_hits[stack_key] = {
            role: {
                "finished_timber_mm3": _hits(shape, finished_timber),
                "fixed_geometry_mm3": {
                    family: hits
                    for family, obstacles in physical_protected.items()
                    if (hits := _hits(shape, obstacles))
                },
                "access_envelope_mm3": {
                    family: hits
                    for family, obstacles in access_protected.items()
                    if (hits := _hits(shape, obstacles))
                },
                "other_installed_hardware_mm3": _hits(shape, other_hardware),
            }
            for role, shape in components.items()
        }
        stack = stacks[stack_key]
        washer_support[stack_key] = {}
        for seat_name, seat in (("head", stack.head_seat), ("nut", stack.nut_seat)):
            support = washer_support_report(seat, finished[seat.body_id], stack.hardware)
            washer_support[stack_key][seat_name] = {
                "body_id": support.body_id,
                "support_fraction": round(support.support_fraction, 6),
                "unsupported_area_mm2": round(support.unsupported_area_mm2, 6),
                "full_seat": support.full_seat,
            }

    body_solid_checks = {
        name: {
            "valid": shape.isValid(),
            "solid_count": len(shape.Solids()),
            "volume_mm3": round(shape.Volume(), 6),
            "valid_single_positive_volume_solid": (
                shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0
            ),
        }
        for name, shape in {**cleats, **finished}.items()
    }
    machining: dict[str, dict[str, Any]] = {}
    for host_id in SOURCE_HOSTS:
        cutters = source_cutters[host_id]
        removed = replaced_axis_ids.intersection(cutters)
        purchase_ids = {name for name in cutters if name.startswith("panel_purchase/")}
        machining[host_id] = {
            "source_retained_cut_ids": sorted(set(cutters) - removed - purchase_ids),
            "candidate_removed_old_sds_ids": sorted(removed),
            "candidate_purchased_panel_cut_ids": sorted(purchase_ids),
            "candidate_left_stack_bore_ids": sorted(candidate_bores_by_host[host_id]),
            "source_cuts_use_left_native_member_datums": True,
            "candidate_only_old_sds_removal": True,
            "purchased_66_axis_policy_preserved": True,
        }
    for cleat_id in cleats:
        machining[cleat_id] = {
            "input_part_origin": "candidate mirrored or full-stock cleat",
            "candidate_left_stack_bore_ids": sorted(candidate_bores_by_host[cleat_id]),
            "source_native_cut_ids": [],
            "candidate_only_old_sds_removal": False,
        }

    inputs_after = _source_inputs_sha256()
    if inputs_before != inputs_after:
        raise RuntimeError("left service producer inputs changed during materialization")
    binding_after = validate_source_binding(source)
    if binding_after != binding_before:
        raise RuntimeError("left service source binding changed during materialization")

    combined_replaced = frozenset(right_geometry.replaced_source_axis_ids) | replaced_axis_ids
    producer_bindings = {
        "left_service_producer_sha256": inputs_before[
            "scripts/wood_joint_left_rail_integration.py"
        ],
        "right_rail_integration_sha256": inputs_before[
            "scripts/wood_joint_right_rail_integration.py"
        ],
        "wj04_inner_producer_sha256": inputs_before[
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"
        ],
        "wj06_outer_producer_sha256": inputs_before[
            "scripts/wood_joint_wj06_outer_pair_probe.py"
        ],
        "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        "source_inventory_sha256": binding_before.inventory_sha256,
    }
    trial_ids = {
        right_integration.FAMILY_WJ04: wj04_inner.TRIAL_ID,
        right_integration.FAMILY_WJ06: wj06_outer.TRIAL_ID,
        "left_service": TRIAL_ID,
    }
    diagnostic_gates = {
        "source_binding_matches_canonical_inventory": True,
        "left_source_native_reconstruction_matches": all(
            row["matches_source_finished_member"]
            for row in source_reconstruction.values()
        ),
        "left_native_axis_datums_are_identity": datum_policy[
            "right_outer_kerf_translation_reused_for_left_cuts"
        ]
        is False,
        "four_exact_target_duties": len(duties) == 4,
        "four_candidate_cleats": len(cleats) == 4,
        "sixteen_full_through_bolt_stack_envelopes": len(stacks) == 16,
        "all_16_bore_layers_present": all(
            row["all_declared_layers_present"] for row in bore_reports.values()
        ),
        "outer_kerf_undo_applied_before_x_mirror": True,
        "upper_inner_uses_full_119p7mm_n_depth": True,
        "fixed_66_panel_screw_axes_retained": len(
            protected["fixed_66_hillman_axes_63p5mm"]
        )
        == 66,
        "twelve_frame_bolt_components_retained_for_screen": len(
            protected["retained_12_frame_bolt_components"]
        )
        == 60,
        "twelve_frame_bolt_tool_and_withdrawal_envelopes_retained": len(
            protected["retained_12_frame_bolt_tools_withdrawals"]
        )
        == 36,
        "left_service_intersections_reported_not_waived": True,
    }
    release = {
        "accepted_replacement": False,
        "structural_capacity_established": False,
        "installation_access_proven": False,
        "full_layout_clearance_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "hardware_selected_or_received": False,
        "assembly_or_transport_proven": False,
    }
    return LeftServiceGeometry(
        source=source,
        source_binding=binding_before,
        inventory=source_inventory,
        source_inputs_sha256=inputs_before,
        producer_bindings=producer_bindings,
        trial_ids=trial_ids,
        duties=duties,
        stack_provenance=stack_provenance,
        replaced_axis_ids=replaced_axis_ids,
        combined_replaced_axis_ids=combined_replaced,
        retained_source_axis_shapes=retained_axes,
        retained_legacy_clip_shapes=retained_clips,
        parts=parts,
        finished=finished,
        stacks=stacks,
        bores=bores,
        installed=installed,
        bore_members=bore_members,
        candidate_bores_by_host=candidate_bores_by_host,
        native_source_cutters_by_host=native_cutters,
        purchased_panel_cutters_by_host=purchased,
        source_cutters_by_host=source_cutters,
        source_reconstruction=source_reconstruction,
        source_axis_datum_audit=source_axis_datum_audit,
        panels=panels,
        all_wood=all_wood,
        protected=protected,
        bore_reports=bore_reports,
        cross_bore_hits_mm3=cross_bore_hits,
        candidate_body_hits=candidate_body_hits,
        installed_hits=installed_hits,
        washer_support=washer_support,
        body_solid_checks=body_solid_checks,
        machining=machining,
        diagnostic_gates=diagnostic_gates,
        release=release,
    )


def diagnostic_report(geometry: LeftServiceGeometry) -> dict[str, Any]:
    """Return JSON-safe nominal geometry evidence without CAD objects."""
    binding = geometry.source_binding
    stacks = []
    for stack_key, stack in sorted(geometry.stacks.items()):
        source_stack_id = stack_key.rsplit("/", 1)[-1]
        stacks.append(
            {
                "stack_id": stack_key,
                "axis_point_global_xyz_mm": _vector_tuple(stack.head_seat.center, 6),
                "axis_direction_global_xyz": _vector_tuple(stack.direction),
                "hardware_candidate_sku": stack.hardware.candidate_sku,
                "modeled_nominal_under_head_length_mm": round(
                    stack.hardware.under_head_length_mm, 6
                ),
                "cad_occupied_diameter_mm": round(
                    stack.hardware.cad_occupied_diameter_mm, 6
                ),
                "steel_diameter_mm": round(stack.hardware.steel_diameter_mm, 6),
                "drill_diameter_mm": round(stack.hardware.drill_diameter_mm, 6),
                "wood_layers_head_to_nut": [
                    {"member_id": row.body_id, "thickness_mm": row.thickness_mm}
                    for row in stack.layers
                ],
                "grip_mm": round(stack.grip_mm, 6),
                "source_stack_id": source_stack_id,
                "source_family_geometry": geometry.stack_provenance[stack_key][
                    "family"
                ],
                "source_bound_hardware_length": {
                    key: value
                    for key, value in geometry.stack_provenance[stack_key].items()
                    if key
                    in {
                        "modeled_nominal_under_head_length_mm",
                        "source_bound_minimum_catalog_length_mm",
                        "source_basis",
                        "cad_shaft_is_a_full_length_collision_envelope",
                        "smooth_shank_length_inferred_from_nominal_length",
                        "hardware_selected_or_received",
                    }
                },
            }
        )
    return {
        "schema": SCHEMA,
        "title": "Left service four-duty installed geometry diagnostic",
        "status": "unaccepted nominal geometry hypothesis",
        "source_candidate": geometry.inventory["candidate"],
        "source_commit": geometry.inventory["source_commit"],
        "source_binding": {
            "inventory_sha256": binding.inventory_sha256,
            "runtime_module_sha256": dict(binding.runtime_module_sha256),
            "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": dict(binding.uncut_host_shape_sha256),
            "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
        },
        "source_inputs_sha256": dict(geometry.source_inputs_sha256),
        "producer_bindings": dict(geometry.producer_bindings),
        "trial_ids": dict(geometry.trial_ids),
        "duty_count": len(geometry.duties),
        "duties": {
            station_id: {
                "legacy_host_members": list(row["legacy_host_members"]),
                "replaced_old_sds_axis_ids": [
                    axis["axis_id"] for axis in row["legacy_sds_axes"]
                ],
                "candidate_cleat_id": CLEAT_BY_LEFT_STATION[station_id],
            }
            for station_id, row in geometry.duties.items()
        },
        "candidate_stack_mapping": [
            {
                "source_family": row["family"],
                "source_stack_id": row["source_stack_id"],
                "source_station_id": row["source_station_id"],
                "target_station_id": row["target_station_id"],
                "interface_id": row["interface_id"],
            }
            for row in sorted(
                _left_station_metadata(),
                key=lambda item: (
                    item["target_station_id"],
                    item["source_stack_id"],
                ),
            )
        ],
        "counts": {
            "left_source_hosts": len(SHARED_HOSTS),
            "candidate_cleats": len(set(geometry.parts) - SHARED_HOSTS),
            "candidate_through_bolt_stacks": len(geometry.stacks),
            "candidate_bore_axes": len(geometry.bores),
            "installed_hardware_components": sum(
                len(rows) for rows in geometry.installed.values()
            ),
            "newly_replaced_source_sds_axes": len(geometry.replaced_axis_ids),
            "combined_right_left_replaced_source_sds_axes": len(
                geometry.combined_replaced_axis_ids
            ),
            "remaining_source_sds_axes": len(geometry.retained_source_axis_shapes),
            "remaining_legacy_clip_bodies": len(geometry.retained_legacy_clip_shapes),
            "fixed_panel_screw_axes": len(
                geometry.protected["fixed_66_hillman_axes_63p5mm"]
            ),
            "starting_frame_bolt_components": len(
                geometry.protected["retained_12_frame_bolt_components"]
            ),
            "candidate_panel_bodies": len(geometry.panels),
        },
        "geometry_policy": {
            "inner_geometry_transform": "mirror X about source datum",
            "outer_geometry_transform": "undo +3.175 mm kerf shift, then mirror X",
            "source_left_cutter_datum": "left source-native identity member transform",
            "inner_upper_cleat_n_depth_mm": INNER_UPPER_FULL_DEPTH_MM,
            "right_g7_crosscut_copied_to_left_upper": False,
            "nominal_source_hardware_model_reused": True,
            "nominal_length_interpreted_as_smooth_shank": False,
        },
        "source_reconstruction": geometry.source_reconstruction,
        "source_axis_datum_audit": geometry.source_axis_datum_audit,
        "machining": geometry.machining,
        "candidate_bodies": geometry.body_solid_checks,
        "candidate_body_intersections": geometry.candidate_body_hits,
        "stacks": stacks,
        "bore_checks": geometry.bore_reports,
        "cross_bore_hits_mm3": geometry.cross_bore_hits_mm3,
        "washer_support": geometry.washer_support,
        "installed_component_intersections": geometry.installed_hits,
        "protected_geometry_counts": {
            family: len(shapes) for family, shapes in geometry.protected.items()
        },
        "diagnostic_gates": dict(geometry.diagnostic_gates),
        "release": dict(geometry.release),
        "claim_boundary": {
            "accepted_replacement_count": 0,
            "full_layout_acceptance": False,
            "installation_access_proven": False,
            "capacity_established": False,
            "tool_fit_or_assembly_sequence_proven": False,
            "transport_feasibility_proven": False,
            "hardware_selected_or_received": False,
            "drilling_released": False,
            "fabrication_released": False,
        },
    }


def trial_plan(inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return exact source duty ownership and transforms without CAD booleans."""
    source_inventory = _canonical_inventory(inventory)
    duties = _selected_duties(source_inventory)
    return {
        "schema": SCHEMA,
        "trial_id": TRIAL_ID,
        "status": "bounded unaccepted geometry hypothesis",
        "candidate": source_inventory["candidate"],
        "source_commit": source_inventory["source_commit"],
        "duty_count": len(duties),
        "duties": {
            station_id: {
                "legacy_host_members": list(row["legacy_host_members"]),
                "replaced_old_sds_axis_ids": [
                    axis["axis_id"] for axis in row["legacy_sds_axes"]
                ],
                "source_family": (
                    "inner" if station_id.endswith("_left_2") else "outer"
                ),
                "candidate_cleat_id": CLEAT_BY_LEFT_STATION[station_id],
            }
            for station_id, row in duties.items()
        },
        "candidate_stack_mapping": [
            {
                "source_family": row["family"],
                "source_stack_id": row["source_stack_id"],
                "source_station_id": row["source_station_id"],
                "target_station_id": row["target_station_id"],
                "interface_id": row["interface_id"],
            }
            for row in sorted(
                _left_station_metadata(),
                key=lambda item: (
                    item["target_station_id"],
                    item["source_stack_id"],
                ),
            )
        ],
        "counts": {
            "source_hosts": len(SHARED_HOSTS),
            "candidate_cleats": 4,
            "candidate_through_bolt_stacks": 16,
            "removed_old_sds_axes_candidate_only": 24,
            "fixed_panel_screw_axes_retained": 66,
            "starting_frame_bolt_arrangements_retained": 12,
        },
        "layout": {
            "inner_cleat_x_bounds_mm": [-177.95, -89.05],
            "inner_rail_bolt_axis_x_mm": -134.5,
            "inner_principal_bolt_start_x_mm": -177.95,
            "inner_principal_bolt_direction_x": 1.0,
            "outer_cleat_x_bounds_mm": list(OUTER_EXPECTED_X_BOUNDS_MM),
            "outer_rail_bolt_axis_x_mm": OUTER_EXPECTED_RAIL_AXIS_X_MM,
            "outer_side_bolt_start_x_mm": OUTER_EXPECTED_SIDE_START_X_MM,
            "outer_side_bolt_direction_x": -1.0,
            "outer_right_kerf_shift_undone_before_mirror_mm": OUTER_KERF_UNDO_MM,
            "upper_inner_cleat_n_origin_mm": INNER_UPPER_FULL_ORIGIN_MM[2],
            "upper_inner_cleat_n_depth_mm": INNER_UPPER_FULL_DEPTH_MM,
            "right_g7_crosscut_inherited": False,
        },
        "claim_boundary": {
            "structural_reuse_accepted": False,
            "installation_access_proven": False,
            "capacity_established": False,
            "fabrication_released": False,
        },
    }
