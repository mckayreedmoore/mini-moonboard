"""Discrete upper-right service-rail subassembly motion screen.

The diagnostic consumes an already composed ``WJ12ComposedGeometry``. It
translates the upper service rail, both of its cleats, and their four rail-bolt
stacks as one rigid subassembly. The samples are nominal positions only; they
do not prove a continuous route, tool access, assembly, or release.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from mini_moonboard.wood_joint_panel_machining import PANEL_NAMES, RIGHT_PANEL_NAMES
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj06_outer_pair_probe as outer_probe
from scripts import wood_joint_wj12_compositor as compositor

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj12_right_assembly/v1"
HIT_TOLERANCE_MM3 = 1e-6
DISTANCE_TOLERANCE_MM = 1e-8
SAMPLE_DISTANCES_MM = (0.0, 5.0, 10.0, 25.0, 50.0, 100.0, 200.0)

UPPER_RAIL = "base_rail_service_upper_right"
G7_UPPER_CLEAT = "wj04_upper_g7_crosscut_full_stock_cleat"
OUTER_UPPER_CLEAT = "wj06_outer_upper_right_cleat"
G7_FAMILY = "wj04_g7"
OUTER_FAMILY = "wj06_outer_pair"
G7_UPPER_STATION = "clip_horizontal_upper_right_1"
OUTER_UPPER_STATION = "clip_horizontal_upper_right_2"

EXPECTED_STACK_AXIS_BASES = {
    (G7_FAMILY, "upper_rail_1"): (0.0, 1.0, 0.0),
    (G7_FAMILY, "upper_rail_2"): (0.0, 1.0, 0.0),
    (G7_FAMILY, "upper_principal_1"): (-1.0, 0.0, 0.0),
    (G7_FAMILY, "upper_principal_2"): (-1.0, 0.0, 0.0),
    (OUTER_FAMILY, "upper_rail_1"): (0.0, 1.0, 0.0),
    (OUTER_FAMILY, "upper_rail_2"): (0.0, 1.0, 0.0),
    (OUTER_FAMILY, "upper_side_1"): (1.0, 0.0, 0.0),
    (OUTER_FAMILY, "upper_side_2"): (1.0, 0.0, 0.0),
}

MOVING_MEMBER_IDS = (UPPER_RAIL, G7_UPPER_CLEAT, OUTER_UPPER_CLEAT)
RAIL_STACK_SUFFIXES = ("upper_rail_1", "upper_rail_2")
OMITTED_UPRIGHT_STACK_SUFFIXES = {
    G7_FAMILY: ("upper_principal_1", "upper_principal_2"),
    OUTER_FAMILY: ("upper_side_1", "upper_side_2"),
}
TEMPORARILY_ABSENT_PANEL_AXIS_IDS = frozenset(
    {
        "round_panel_upper_right_service_1",
        "round_panel_upper_right_service_2",
    }
)

EXPECTED_GEOMETRY_FIELDS = frozenset(
    {
        "trial_id",
        "source",
        "source_binding",
        "source_inventory_sha256",
        "source_inventory",
        "family_source_fingerprints",
        "family_trial_ids",
        "target_station_ids",
        "raw_hosts",
        "finished_hosts",
        "raw_candidate_parts",
        "finished_candidate_parts",
        "candidate_bores",
        "candidate_installed_hardware",
        "replaced_source_axis_ids",
        "replaced_source_cutter_ids",
        "source_cutters_by_host",
        "applied_source_cutters_by_host",
        "purchased_panel_cutters_by_host",
        "purchased_panel_cutters_by_candidate_part",
        "additional_finished_source_parts",
        "additional_purchased_panel_cutters_by_host",
        "additional_source_reconstruction",
        "source_reconstruction",
        "panel_replacements",
        "fixed_axes",
        "frame_bolt_records",
        "frame_bolt_shapes",
        "protected",
        "status",
    }
)

EXPECTED_COUNTS = {
    "target_duties": 12,
    "source_hosts": 11,
    "replaced_source_sds_axes": 72,
    "candidate_bores": 56,
    "candidate_installed_hardware_axes": 56,
    "candidate_installed_hardware_components": 280,
    "candidate_parts": 16,
    "panel_replacements": 3,
    "fixed_panel_axes": 66,
    "additional_finished_source_parts": 5,
    "retained_frame_bolts": 12,
    "retained_frame_bolt_installed_components": 60,
    "retained_frame_bolt_source_occupied_axes": 12,
    "retained_frame_bolt_shapes": 72,
    "retained_legacy_clips": 12,
    "retained_legacy_sds_axes": 72,
}

EXPECTED_SOURCE_WOOD_IDS = frozenset(
    {
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
        "base_side_left",
        "base_side_right",
        "base_rail_top",
        "base_header",
        "base_post_outer_left",
        "base_post_outer_right",
        "lumber_leg_left",
        "lumber_leg_right",
        "base_principal_center_left",
        "base_post_center_left",
        "base_principal_center_right",
        "base_post_center_right",
        "base_rail_bottom_left",
        "base_rail_service_lower_left",
        "base_rail_service_upper_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "base_floor_left",
        "base_floor_right",
    }
)

EXPECTED_PROTECTED_COUNTS = {
    "fixed_66_hillman_axes_63p5mm": 66,
    "retained_12_frame_bolt_components": 60,
    "retained_12_frame_bolt_tools_withdrawals": 36,
    "tnuts": 142,
    "hold_hole_and_provisional_projection": 142,
    "lights": 132,
    "wires": 131,
    "retained_legacy_clips": 12,
    "retained_legacy_sds_axes": 72,
}

PROTECTED_DUPLICATE_FAMILIES = frozenset(
    {
        "fixed_66_hillman_axes_63p5mm",
        "retained_12_frame_bolt_components",
    }
)
NONPHYSICAL_ACCESS_FAMILIES = frozenset({"retained_12_frame_bolt_tools_withdrawals"})


@dataclass(frozen=True)
class MotionScene:
    moving_shapes: Any
    obstacle_shapes: Any
    moving_categories: Any
    obstacle_categories: Any
    source_wood_member_ids: tuple[str, ...]
    finished_wood_member_ids: tuple[str, ...]
    panel_member_ids: tuple[str, ...]
    panel_replacement_ids: tuple[str, ...]
    moving_member_ids: tuple[str, ...]
    moving_stack_ids: tuple[str, ...]
    omitted_candidate_stack_ids: tuple[str, ...]
    omitted_candidate_stack_component_ids: tuple[str, ...]
    temporarily_absent_panel_axis_ids: tuple[str, ...]
    replaced_source_axis_ids: tuple[str, ...]
    replaced_upper_duty_axis_ids: tuple[str, ...]
    replaced_target_duty_ids: tuple[str, ...]
    suppressed_duplicate_protected_families: tuple[str, ...]
    omitted_access_envelopes: tuple[str, ...]
    fixed_axis_inventory_sha256: str
    source_metadata: Any


def _sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _require_shape_map(value: Any, *, context: str) -> dict[str, cq.Shape]:
    if not hasattr(value, "items"):
        raise TypeError(f"{context} must be a shape mapping")
    result = dict(value)
    if any(
        not isinstance(name, str)
        or not name
        or not isinstance(shape, cq.Shape)
        or not shape.isValid()
        for name, shape in result.items()
    ):
        raise ValueError(f"{context} has an invalid shape ID or CAD solid")
    return result


def _source_part_shapes(source: Any, method_name: str) -> dict[str, cq.Shape]:
    method = getattr(source, method_name, None)
    if not callable(method):
        raise TypeError(f"composed source must provide {method_name}()")
    parts = tuple(method())
    result = {part.name: part.shape for part in parts}
    if len(result) != len(parts):
        raise ValueError(f"source {method_name}() has duplicate member names")
    return _require_shape_map(result, context=f"source/{method_name}")


def _flat_fingerprints(shapes: dict[str, cq.Shape]) -> Counter[str]:
    return Counter(_source_shape_fingerprint(shape) for shape in shapes.values())


def _validate_protected_duplicates(geometry: Any) -> None:
    protected = geometry.protected
    fixed_axes = _require_shape_map(geometry.fixed_axes, context="fixed_axes")
    panel_alias = _require_shape_map(
        protected["fixed_66_hillman_axes_63p5mm"],
        context="protected fixed panel axes",
    )
    if set(panel_alias) != set(fixed_axes) or any(
        _source_shape_fingerprint(panel_alias[axis_id])
        != _source_shape_fingerprint(fixed_axes[axis_id])
        for axis_id in fixed_axes
    ):
        raise ValueError(
            "protected 66-axis alias differs from the composed fixed-axis map"
        )

    frame_components = _require_shape_map(
        protected["retained_12_frame_bolt_components"],
        context="protected frame-bolt components",
    )
    installed_frame_components = {
        shape_id: shape
        for shape_id, shape in _require_shape_map(
            geometry.frame_bolt_shapes, context="frame_bolt_shapes"
        ).items()
        if shape_id.endswith(
            tuple(f"/installed_component_{index}" for index in range(1, 6))
        )
    }
    axis_ids = {
        row["axis_id"] for row in geometry.source_inventory["starting_frame_bolts"]
    }
    roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    expected_alias_ids = {f"{axis_id}/{role}" for axis_id in axis_ids for role in roles}
    expected_installed_ids = {
        f"{axis_id}/installed_component_{index}"
        for axis_id in axis_ids
        for index in range(1, 6)
    }
    if (
        set(frame_components) != expected_alias_ids
        or set(installed_frame_components) != expected_installed_ids
    ):
        raise ValueError(
            "protected frame-bolt component alias inventory differs from composed hardware"
        )
    # Source protection uses named roles; the composed map uses indexed roles.
    # Match shapes within each physical bolt so a global multiset cannot hide
    # components assigned to the wrong bolt identity.
    for axis_id in sorted(axis_ids):
        aliases = {role: frame_components[f"{axis_id}/{role}"] for role in roles}
        installed = {
            str(index): installed_frame_components[
                f"{axis_id}/installed_component_{index}"
            ]
            for index in range(1, 6)
        }
        if _flat_fingerprints(aliases) != _flat_fingerprints(installed):
            raise ValueError(
                f"{axis_id}: protected frame-bolt component aliases differ from composed hardware"
            )


def _source_metadata(geometry: Any) -> dict[str, Any]:
    family_fingerprints = {
        family: dict(sorted(rows.items()))
        for family, rows in sorted(geometry.family_source_fingerprints.items())
    }
    family_trials = dict(sorted(geometry.family_trial_ids.items()))
    if family_trials.get(G7_FAMILY) != g7_probe.TRIAL_ID:
        raise ValueError("composed WJ04 family is not the declared upper G7 trial")
    if family_trials.get(OUTER_FAMILY) != outer_probe.TRIAL_ID:
        raise ValueError("composed WJ06 family is not the declared outer-pair trial")

    right_sources = family_fingerprints.get("right_rail")
    if not isinstance(right_sources, dict):
        raise TypeError("composed right-rail source fingerprints are missing")
    for source_path in (
        "docs/wood-joints-mvp/source-inventory.json",
        "scripts/wood_joint_right_rail_integration.py",
        "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
        "scripts/wood_joint_wj06_outer_pair_probe.py",
    ):
        expected_hash = right_sources.get(source_path)
        if (
            not isinstance(expected_hash, str)
            or _sha256_file(source_path) != expected_hash
        ):
            raise ValueError(f"composed right-rail source hash changed: {source_path}")

    if (
        UPPER_RAIL != g7_probe.UPPER_RAIL
        or UPPER_RAIL != outer_probe.UPPER_RAIL
        or G7_UPPER_CLEAT != g7_probe.UPPER_CLEAT
        or OUTER_UPPER_CLEAT != outer_probe.UPPER_CLEAT
        or G7_UPPER_STATION != g7_probe.UPPER_STATION
        or OUTER_UPPER_STATION != outer_probe.UPPER_STATION
    ):
        raise ValueError(
            "moving member IDs or station IDs differ from family producers"
        )

    inventory_bytes = (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_bytes()
    if hashlib.sha256(inventory_bytes).hexdigest() != geometry.source_inventory_sha256:
        raise ValueError("composed source inventory hash differs from the live pin")
    binding = geometry.source_binding
    if getattr(binding, "inventory_sha256", None) != geometry.source_inventory_sha256:
        raise ValueError(
            "composed source binding differs from the source inventory hash"
        )
    inventory_module_hashes = geometry.source_inventory.get(
        "source_runtime_module_hashes_sha256"
    )
    binding_module_hashes = getattr(binding, "runtime_module_sha256", None)
    if (
        not isinstance(inventory_module_hashes, dict)
        or dict(binding_module_hashes or {}) != inventory_module_hashes
    ):
        raise ValueError(
            "composed source binding runtime modules differ from inventory"
        )
    for source_path, expected_hash in inventory_module_hashes.items():
        if _sha256_file(source_path) != expected_hash:
            raise ValueError(f"canonical source runtime module changed: {source_path}")
    if getattr(
        binding, "uncut_part_shapes_sha256", None
    ) != geometry.source_inventory.get("source_part_shapes_sha256"):
        raise ValueError("composed source binding shape hash differs from inventory")

    n_axis = tuple(float(value) for value in WJ04_TRIAL.frame.n_global)
    t_axis = tuple(float(value) for value in WJ04_TRIAL.frame.t_global)
    x_axis = tuple(float(value) for value in WJ04_TRIAL.frame.x_global)
    expected_n = (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0)))
    if any(
        abs(actual - expected) > 1e-9
        for actual, expected in zip(n_axis, expected_n, strict=True)
    ):
        raise ValueError("WJ04 source N direction changed")
    assembly_axis_records = []
    for family, producer, expected_specs in (
        (G7_FAMILY, g7_probe, g7_probe.STACK_SPECS),
        (OUTER_FAMILY, outer_probe, outer_probe.STACK_SPECS),
    ):
        wanted_suffixes = (
            *RAIL_STACK_SUFFIXES,
            *OMITTED_UPRIGHT_STACK_SUFFIXES[family],
        )
        for suffix in wanted_suffixes:
            spec = next((row for row in expected_specs if row.stack_id == suffix), None)
            if spec is None:
                raise ValueError(f"{producer.__name__}:{suffix} is absent from source")
            direction_basis = tuple(spec.axis_direction_basis)
            expected_basis = EXPECTED_STACK_AXIS_BASES[(family, suffix)]
            if direction_basis != expected_basis:
                raise ValueError(
                    f"{producer.__name__}:{suffix} bolt direction differs from source"
                )
            expected_station = (
                G7_UPPER_STATION if family == G7_FAMILY else OUTER_UPPER_STATION
            )
            if spec.station_id != expected_station:
                raise ValueError(
                    f"{producer.__name__}:{suffix} is not on the declared upper duty"
                )
            axis_id = f"{family}/{family_trials[family]}/{suffix}"
            candidate_bore = geometry.candidate_bores.get(axis_id)
            station_tag = None if candidate_bore is None else candidate_bore.station_id
            if station_tag is not None and station_tag != spec.station_id:
                raise ValueError(
                    f"{axis_id} optional bore station tag contradicts source producer"
                )
            direction_global = WJ04_TRIAL.frame.vector_to_global(direction_basis)
            assembly_axis_records.append(
                {
                    "axis_id": axis_id,
                    "family": family,
                    "stack_id": suffix,
                    "interface_id": spec.interface_id,
                    "candidate_bore_station_tag": station_tag,
                    "resolved_producer_station_id": spec.station_id,
                    "axis_direction_basis": list(direction_basis),
                    "axis_direction_global_xyz": list(direction_global),
                }
            )

    return {
        "source_inventory_sha256": geometry.source_inventory_sha256,
        "source_commit": geometry.source_inventory.get("source_commit"),
        "family_trial_ids": family_trials,
        "family_source_fingerprints_sha256": family_fingerprints,
        "motion_basis": {
            "N_global_xyz_per_mm": list(n_axis),
            "T_global_xyz": list(t_axis),
            "X_global_xyz": list(x_axis),
            "source": "mini_moonboard/wood_joint_wj04_config.py FrameBasis",
        },
        "upper_station_bolt_stack_axes": assembly_axis_records,
        "adapter_sha256": _sha256_file("scripts/wood_joint_wj12_right_assembly.py"),
        "compositor_sha256_current": _sha256_file(
            "scripts/wood_joint_wj12_compositor.py"
        ),
    }


def _legacy_inventory_sets(geometry: Any) -> tuple[set[str], set[str], set[str]]:
    inventory = geometry.source_inventory
    duties = inventory.get("legacy_duties")
    if not isinstance(duties, (tuple, list)):
        raise TypeError("source inventory legacy duties are missing")
    all_duties = {row["legacy_station_id"] for row in duties}
    all_axes = {
        axis["axis_id"] for row in duties for axis in row.get("legacy_sds_axes", ())
    }
    target_duties = set(geometry.target_station_ids)
    replaced_axes = set(geometry.replaced_source_axis_ids)
    if len(duties) != 24 or len(all_duties) != 24 or len(all_axes) != 144:
        raise ValueError("source inventory must retain its 24 duties and 144 SDS IDs")
    if target_duties != set(compositor.TARGET_STATIONS):
        raise ValueError("composed WJ12 target duties differ from the pinned layout")
    if len(target_duties) != 12 or len(replaced_axes) != 72:
        raise ValueError("WJ12 replacement inventory counts changed")
    expected_replaced_axes = {
        axis["axis_id"]
        for row in duties
        if row["legacy_station_id"] in target_duties
        for axis in row.get("legacy_sds_axes", ())
    }
    if replaced_axes != expected_replaced_axes or not replaced_axes <= all_axes:
        raise ValueError(
            "replaced source SDS IDs differ from all 12 pinned target duties"
        )
    expected_retained_axes = all_axes - replaced_axes
    expected_retained_duties = all_duties - target_duties
    return expected_retained_axes, expected_retained_duties, all_axes


def _upper_duty_axis_ids(geometry: Any) -> set[str]:
    wanted = {G7_UPPER_STATION, OUTER_UPPER_STATION}
    records = {
        row["legacy_station_id"]: row
        for row in geometry.source_inventory["legacy_duties"]
        if row["legacy_station_id"] in wanted
    }
    if set(records) != wanted:
        raise ValueError("source inventory is missing an upper-right rail duty")
    result = {
        axis["axis_id"]
        for row in records.values()
        for axis in row.get("legacy_sds_axes", ())
    }
    if len(result) != 12 or not result <= set(geometry.replaced_source_axis_ids):
        raise ValueError("upper G7/WJ06 source SDS axes are not all replaced")
    return result


def _expected_stack_ids(geometry: Any) -> tuple[set[str], set[str]]:
    trials = geometry.family_trial_ids
    moving: set[str] = set()
    omitted: set[str] = set()
    for family in (G7_FAMILY, OUTER_FAMILY):
        if family not in trials:
            raise ValueError(f"composed geometry has no {family} trial identity")
        prefix = f"{family}/{trials[family]}/"
        moving.update(prefix + suffix for suffix in RAIL_STACK_SUFFIXES)
        omitted.update(
            prefix + suffix for suffix in OMITTED_UPRIGHT_STACK_SUFFIXES[family]
        )
    return moving, omitted


def _validate_stack_receivers(
    geometry: Any, moving_ids: set[str], omitted_ids: set[str]
) -> None:
    bores = geometry.candidate_bores
    hardware = geometry.candidate_installed_hardware
    if set(bores) != set(hardware) or len(bores) != 56:
        raise ValueError("candidate bore and hardware axes must match all 56 duties")
    expected_receivers = {
        f"{G7_FAMILY}/{geometry.family_trial_ids[G7_FAMILY]}/upper_rail_1": {
            UPPER_RAIL,
            G7_UPPER_CLEAT,
        },
        f"{G7_FAMILY}/{geometry.family_trial_ids[G7_FAMILY]}/upper_rail_2": {
            UPPER_RAIL,
            G7_UPPER_CLEAT,
        },
        f"{OUTER_FAMILY}/{geometry.family_trial_ids[OUTER_FAMILY]}/upper_rail_1": {
            UPPER_RAIL,
            OUTER_UPPER_CLEAT,
        },
        f"{OUTER_FAMILY}/{geometry.family_trial_ids[OUTER_FAMILY]}/upper_rail_2": {
            UPPER_RAIL,
            OUTER_UPPER_CLEAT,
        },
        f"{G7_FAMILY}/{geometry.family_trial_ids[G7_FAMILY]}/upper_principal_1": {
            G7_UPPER_CLEAT,
            "base_principal_center_right",
        },
        f"{G7_FAMILY}/{geometry.family_trial_ids[G7_FAMILY]}/upper_principal_2": {
            G7_UPPER_CLEAT,
            "base_principal_center_right",
        },
        f"{OUTER_FAMILY}/{geometry.family_trial_ids[OUTER_FAMILY]}/upper_side_1": {
            OUTER_UPPER_CLEAT,
            "base_side_right",
        },
        f"{OUTER_FAMILY}/{geometry.family_trial_ids[OUTER_FAMILY]}/upper_side_2": {
            OUTER_UPPER_CLEAT,
            "base_side_right",
        },
    }
    if set(expected_receivers) != moving_ids | omitted_ids:
        raise ValueError("declared upper rail stack IDs do not reconcile")
    for axis_id, receivers in expected_receivers.items():
        bore = bores.get(axis_id)
        if bore is None or set(bore.receiver_ids) != receivers:
            raise ValueError(f"{axis_id} receiver IDs differ from producer mapping")
        expected_station = (
            G7_UPPER_STATION
            if axis_id.startswith(f"{G7_FAMILY}/")
            else OUTER_UPPER_STATION
        )
        if bore.station_id is not None and bore.station_id != expected_station:
            raise ValueError(
                f"{axis_id} optional bore station tag contradicts producer mapping"
            )
        components = _require_shape_map(
            hardware[axis_id], context=f"candidate hardware {axis_id}"
        )
        if set(components) != {"shaft", "head", "head_washer", "nut_washer", "nut"}:
            raise ValueError(f"{axis_id} installed hardware roles changed")
    if not moving_ids <= set(bores) or not omitted_ids <= set(bores):
        raise ValueError("declared upper rail stacks are absent from composed bores")


def _shape_registry(geometry: Any) -> MotionScene:
    if not isinstance(geometry, compositor.WJ12ComposedGeometry):
        raise TypeError("diagnostic requires an already composed WJ12ComposedGeometry")
    geometry_fields = {item.name for item in fields(type(geometry))}
    if geometry_fields != EXPECTED_GEOMETRY_FIELDS:
        raise ValueError(
            "WJ12 geometry fields changed; review every included/excluded shape map"
        )
    if (
        geometry.trial_id != compositor.TRIAL_ID
        or geometry.status != "unaccepted_integrated_hypothesis"
    ):
        raise ValueError("diagnostic requires the current unaccepted WJ12 composition")
    counts = geometry.counts
    if any(counts.get(name) != expected for name, expected in EXPECTED_COUNTS.items()):
        raise ValueError(
            "WJ12 composed shape and duty counts differ from the declared map"
        )

    source_metadata = _source_metadata(geometry)
    retained_axis_ids, retained_duty_ids, all_source_axis_ids = _legacy_inventory_sets(
        geometry
    )
    replaced_axis_ids = set(geometry.replaced_source_axis_ids)
    replaced_upper_axis_ids = _upper_duty_axis_ids(geometry)
    if replaced_axis_ids & retained_axis_ids:
        raise ValueError("replaced source SDS axes appear in retained inventory")
    protected = geometry.protected
    if set(protected) != set(EXPECTED_PROTECTED_COUNTS):
        raise ValueError("protected geometry families changed; declare every family")
    protected_maps = {
        name: _require_shape_map(protected[name], context=f"protected/{name}")
        for name in sorted(protected)
    }
    if any(
        len(protected_maps[name]) != expected
        for name, expected in EXPECTED_PROTECTED_COUNTS.items()
    ):
        raise ValueError("protected obstacle counts differ from the composed contract")
    if set(protected_maps["retained_legacy_sds_axes"]) != retained_axis_ids:
        raise ValueError("retained SDS obstacle IDs differ from WJ12 source inventory")
    if set(protected_maps["retained_legacy_clips"]) != retained_duty_ids:
        raise ValueError("retained angle obstacle IDs differ from WJ12 source duties")
    if (
        all_source_axis_ids & set(protected_maps["retained_legacy_sds_axes"])
        != retained_axis_ids
    ):
        raise ValueError("retained source SDS axis map is incomplete")

    frame_axis_ids = {
        row["axis_id"]
        for row in geometry.source_inventory.get("starting_frame_bolts", ())
    }
    frame_record_ids = {row["axis_id"] for row in geometry.frame_bolt_records}
    expected_frame_shape_ids = {
        f"{axis_id}/installed_component_{component}"
        for axis_id in frame_axis_ids
        for component in range(1, 6)
    } | {f"{axis_id}/source_occupied_axis" for axis_id in frame_axis_ids}
    frame_shapes_checked = _require_shape_map(
        geometry.frame_bolt_shapes, context="frame_bolt_shapes"
    )
    if (
        len(frame_axis_ids) != 12
        or frame_record_ids != frame_axis_ids
        or set(frame_shapes_checked) != expected_frame_shape_ids
        or any(
            row.get("installed_component_count") != 5
            for row in geometry.frame_bolt_records
        )
    ):
        raise ValueError(
            "retained frame-bolt geometry IDs differ from source inventory"
        )

    moving_stack_ids, omitted_stack_ids = _expected_stack_ids(geometry)
    _validate_stack_receivers(geometry, moving_stack_ids, omitted_stack_ids)
    moving_stack_ids = set(moving_stack_ids)
    omitted_stack_ids = set(omitted_stack_ids)

    moving_members: dict[str, cq.Shape] = {}
    finished_hosts = _require_shape_map(
        geometry.finished_hosts, context="finished_hosts"
    )
    finished_parts = _require_shape_map(
        geometry.finished_candidate_parts, context="finished_candidate_parts"
    )
    raw_hosts = _require_shape_map(geometry.raw_hosts, context="raw_hosts")
    raw_candidates = _require_shape_map(
        geometry.raw_candidate_parts, context="raw_candidate_parts"
    )
    if set(raw_hosts) != set(finished_hosts) or set(raw_candidates) != set(
        finished_parts
    ):
        raise ValueError("composed raw and finished member IDs differ")
    expected_host_ids = set(compositor.source_host_ids(geometry.source_inventory))
    if set(finished_hosts) != expected_host_ids:
        raise ValueError("finished source-host IDs differ from all 12 target duties")

    raw_source = _source_part_shapes(geometry.source, "uncut_wood_parts")
    source_finished_all = _source_part_shapes(geometry.source, "parts")
    source_part_rows = geometry.source_inventory.get("parts", ())
    inventory_source_ids = {row["part_id"] for row in source_part_rows}
    if (
        inventory_source_ids != EXPECTED_SOURCE_WOOD_IDS
        or set(raw_source) != EXPECTED_SOURCE_WOOD_IDS
    ):
        raise ValueError(
            "canonical raw source wood IDs differ from the fixed 26-member map"
        )
    source_finished = {
        name: shape for name, shape in source_finished_all.items() if name in raw_source
    }
    if set(source_finished) != EXPECTED_SOURCE_WOOD_IDS:
        raise ValueError("canonical finished source omits a pinned wood member")
    source_duty_ids = {
        row["legacy_station_id"]
        for row in geometry.source_inventory.get("legacy_duties", ())
    }
    observed_source_nonwood_ids = set(source_finished_all) - set(raw_source)
    expected_source_nonwood_ids = source_duty_ids | set(protected_maps["tnuts"])
    if observed_source_nonwood_ids != expected_source_nonwood_ids:
        raise ValueError(
            "canonical source non-wood parts differ from the 24 clips and 142 T-nuts"
        )
    if set(finished_parts) & EXPECTED_SOURCE_WOOD_IDS:
        raise ValueError("candidate timber IDs overlap canonical source wood IDs")

    overlays = _require_shape_map(
        geometry.additional_finished_source_parts,
        context="additional_finished_source_parts",
    )
    expected_overlay_ids = set(
        compositor.EXPECTED_ADDITIONAL_PANEL_RECEIVER_AXIS_COUNTS
    )
    if set(overlays) != expected_overlay_ids or set(overlays) & set(finished_hosts):
        raise ValueError(
            "finished source overlays differ from the pinned five-member map"
        )
    if not set(overlays) <= EXPECTED_SOURCE_WOOD_IDS:
        raise ValueError("finished source overlays contain an unknown source member")

    panel_replacements = _require_shape_map(
        geometry.panel_replacements, context="panel_replacements"
    )
    if set(panel_replacements) != RIGHT_PANEL_NAMES:
        raise ValueError(
            "panel replacement IDs differ from the three pinned right panels"
        )
    if not RIGHT_PANEL_NAMES <= EXPECTED_SOURCE_WOOD_IDS or PANEL_NAMES != {
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
    }:
        raise ValueError("canonical six-panel identity set changed")

    finished_wood = dict(source_finished)
    finished_wood.update(overlays)
    finished_wood.update(finished_hosts)
    finished_wood.update(panel_replacements)
    finished_wood.update(finished_parts)
    expected_finished_wood_ids = EXPECTED_SOURCE_WOOD_IDS | set(finished_parts)
    if set(finished_wood) != expected_finished_wood_ids or not PANEL_NAMES <= set(
        finished_wood
    ):
        raise ValueError("complete WJ12 finished wood map omits or adds member IDs")
    for member_id in MOVING_MEMBER_IDS:
        if member_id not in finished_wood:
            raise ValueError(
                f"moving member is absent from composed geometry: {member_id}"
            )
        moving_members[f"finished_wood/{member_id}"] = finished_wood[member_id]

    moving_shapes = dict(moving_members)
    moving_categories = {
        shape_id: "finished_timber_geometry" for shape_id in moving_members
    }
    omitted_stack_component_ids = set()
    for axis_id in sorted(moving_stack_ids):
        for role, shape in _require_shape_map(
            geometry.candidate_installed_hardware[axis_id],
            context=f"candidate hardware {axis_id}",
        ).items():
            moving_shapes[f"candidate_installed_hardware/{axis_id}/{role}"] = shape
            moving_categories[f"candidate_installed_hardware/{axis_id}/{role}"] = (
                "candidate_installed_hardware_shape"
            )
    for axis_id in sorted(omitted_stack_ids):
        for role in geometry.candidate_installed_hardware[axis_id]:
            omitted_stack_component_ids.add(
                f"candidate_installed_hardware/{axis_id}/{role}"
            )

    inventory_rows = geometry.source_inventory.get("fixed_panel_kicker_screws", ())
    if len(inventory_rows) != 66:
        raise ValueError("canonical fixed panel/kicker inventory must contain 66 axes")
    screw_rows = {row["axis_id"]: row for row in inventory_rows}
    if len(screw_rows) != 66 or set(screw_rows) != set(geometry.fixed_axes):
        raise ValueError("fixed-axis geometry differs from canonical 66-axis inventory")
    rail_screw_ids = {
        axis_id
        for axis_id, row in screw_rows.items()
        if row.get("candidate_finished_receiver_member") == UPPER_RAIL
    }
    if rail_screw_ids != set(TEMPORARILY_ABSENT_PANEL_AXIS_IDS):
        raise ValueError(
            "upper-rail receiver screws changed; review panel removal/support state"
        )
    for axis_id in rail_screw_ids:
        row = screw_rows[axis_id]
        if (
            row.get("source_finished_receiver_member") != UPPER_RAIL
            or row.get("shop_opening_kind") != "hillman_panel"
            or row.get("shop_purchased_length_mm") != 63.5
        ):
            raise ValueError(f"{axis_id} no longer matches the upper-rail screw duty")
    fixed_axis_shapes = _require_shape_map(geometry.fixed_axes, context="fixed_axes")

    # Each physical/composed shape field is assigned one disposition below.
    # Raw inputs and cutters are explicitly not obstacles; their finished result
    # is present. Unknown future fields or protected families fail above.
    obstacles: dict[str, cq.Shape] = {}
    obstacle_categories: dict[str, str] = {}

    def add_shapes(
        namespace: str,
        rows: dict[str, cq.Shape],
        *,
        category: str,
        omit: set[str] | None = None,
    ) -> None:
        omitted = omit or set()
        for name, shape in sorted(rows.items()):
            if name in omitted:
                continue
            obstacle_id = f"{namespace}/{name}"
            if obstacle_id in obstacles:
                raise ValueError(f"duplicate obstacle ID: {obstacle_id}")
            obstacles[obstacle_id] = shape
            obstacle_categories[obstacle_id] = category

    add_shapes(
        "finished_wood",
        finished_wood,
        category="finished_timber_geometry",
        omit=set(MOVING_MEMBER_IDS),
    )

    hardware_axes = geometry.candidate_installed_hardware
    for axis_id in sorted(hardware_axes):
        if axis_id in moving_stack_ids or axis_id in omitted_stack_ids:
            continue
        add_shapes(
            f"candidate_installed_hardware/{axis_id}",
            _require_shape_map(hardware_axes[axis_id], context=f"hardware/{axis_id}"),
            category="candidate_installed_hardware_shape",
        )

    add_shapes(
        "fixed_axes",
        fixed_axis_shapes,
        category="fixed_panel_screw_axis_envelope",
        omit=set(TEMPORARILY_ABSENT_PANEL_AXIS_IDS),
    )
    frame_shapes = _require_shape_map(
        geometry.frame_bolt_shapes, context="frame_bolt_shapes"
    )
    for name, shape in sorted(frame_shapes.items()):
        obstacle_id = f"frame_bolt_shapes/{name}"
        if obstacle_id in obstacles:
            raise ValueError(f"duplicate obstacle ID: {obstacle_id}")
        obstacles[obstacle_id] = shape
        obstacle_categories[obstacle_id] = (
            "frame_bolt_source_occupied_axis_envelope"
            if name.endswith("/source_occupied_axis")
            else "frame_bolt_installed_component_shape"
        )
    _validate_protected_duplicates(geometry)
    for family in sorted(protected_maps):
        if family in PROTECTED_DUPLICATE_FAMILIES | NONPHYSICAL_ACCESS_FAMILIES:
            continue
        protected_category = {
            "tnuts": "retained_tnut_geometry",
            "hold_hole_and_provisional_projection": "provisional_clearance_envelope",
            "lights": "retained_light_geometry",
            "wires": "retained_wire_geometry",
            "retained_legacy_clips": "retained_angle_geometry",
            "retained_legacy_sds_axes": "retained_source_sds_axis_envelope",
        }[family]
        add_shapes(
            f"protected/{family}",
            protected_maps[family],
            category=protected_category,
        )

    if not moving_shapes or not obstacles:
        raise ValueError("moving subassembly or obstacle inventory is empty")
    axis_hash_payload = json.dumps(
        sorted(screw_rows.values(), key=lambda row: row["axis_id"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return MotionScene(
        moving_shapes=MappingProxyType(dict(sorted(moving_shapes.items()))),
        obstacle_shapes=MappingProxyType(dict(sorted(obstacles.items()))),
        moving_categories=MappingProxyType(dict(sorted(moving_categories.items()))),
        obstacle_categories=MappingProxyType(dict(sorted(obstacle_categories.items()))),
        source_wood_member_ids=tuple(sorted(EXPECTED_SOURCE_WOOD_IDS)),
        finished_wood_member_ids=tuple(sorted(finished_wood)),
        panel_member_ids=tuple(sorted(PANEL_NAMES)),
        panel_replacement_ids=tuple(sorted(panel_replacements)),
        moving_member_ids=tuple(sorted(moving_shapes)),
        moving_stack_ids=tuple(sorted(moving_stack_ids)),
        omitted_candidate_stack_ids=tuple(sorted(omitted_stack_ids)),
        omitted_candidate_stack_component_ids=tuple(
            sorted(omitted_stack_component_ids)
        ),
        temporarily_absent_panel_axis_ids=tuple(sorted(rail_screw_ids)),
        replaced_source_axis_ids=tuple(sorted(replaced_axis_ids)),
        replaced_upper_duty_axis_ids=tuple(sorted(replaced_upper_axis_ids)),
        replaced_target_duty_ids=tuple(sorted(geometry.target_station_ids)),
        suppressed_duplicate_protected_families=tuple(
            sorted(PROTECTED_DUPLICATE_FAMILIES)
        ),
        omitted_access_envelopes=tuple(
            f"protected/{family}/{name}"
            for family in sorted(NONPHYSICAL_ACCESS_FAMILIES)
            for name in sorted(protected_maps[family])
        ),
        fixed_axis_inventory_sha256=hashlib.sha256(axis_hash_payload).hexdigest(),
        source_metadata=MappingProxyType(source_metadata),
    )


def _bounds(shape: cq.Shape) -> tuple[float, float, float, float, float, float]:
    box = shape.BoundingBox()
    return box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax


def _aabb_gap(first: cq.Shape, second: cq.Shape) -> float:
    a = _bounds(first)
    b = _bounds(second)
    gaps = (
        max(0.0, a[0] - b[1], b[0] - a[1]),
        max(0.0, a[2] - b[3], b[2] - a[3]),
        max(0.0, a[4] - b[5], b[4] - a[5]),
    )
    return math.sqrt(sum(value * value for value in gaps))


def _evaluate_pose(
    moving_shapes: Any,
    obstacles: Any,
    translation_mm: tuple[float, float, float],
    *,
    moving_categories: Any | None = None,
    obstacle_categories: Any | None = None,
) -> dict[str, Any]:
    translation = cq.Vector(*translation_mm)
    hits: list[dict[str, Any]] = []
    no_hit_pairs: list[tuple[float, str, str, cq.Shape, cq.Shape]] = []
    pair_count = 0
    for moving_id, source_shape in moving_shapes.items():
        moved_shape = source_shape.translate(translation)
        for obstacle_id, obstacle in obstacles.items():
            pair_count += 1
            lower_bound = _aabb_gap(moved_shape, obstacle)
            if lower_bound <= DISTANCE_TOLERANCE_MM:
                volume = max(0.0, float(moved_shape.intersect(obstacle).Volume()))
                if volume > HIT_TOLERANCE_MM3:
                    hits.append(
                        {
                            "moving_id": moving_id,
                            "moving_category": (
                                moving_categories.get(moving_id, "unspecified")
                                if moving_categories is not None
                                else "unspecified"
                            ),
                            "obstacle_id": obstacle_id,
                            "obstacle_category": (
                                obstacle_categories.get(obstacle_id, "unspecified")
                                if obstacle_categories is not None
                                else "unspecified"
                            ),
                            "intersection_volume_mm3": round(volume, 9),
                        }
                    )
                    continue
                distance = max(0.0, float(moved_shape.distance(obstacle)))
                no_hit_pairs.append(
                    (distance, moving_id, obstacle_id, moved_shape, obstacle)
                )
            else:
                no_hit_pairs.append(
                    (lower_bound, moving_id, obstacle_id, moved_shape, obstacle)
                )

    no_hit_pairs.sort(key=lambda row: (row[0], row[1], row[2]))
    nearest: tuple[float, str, str] | None = None
    for lower_bound, moving_id, obstacle_id, moved_shape, obstacle in no_hit_pairs:
        if nearest is not None and lower_bound > nearest[0] + DISTANCE_TOLERANCE_MM:
            break
        exact_gap = max(0.0, float(moved_shape.distance(obstacle)))
        candidate = (exact_gap, moving_id, obstacle_id)
        if nearest is None or candidate < nearest:
            nearest = candidate

    hits.sort(key=lambda row: (row["moving_id"], row["obstacle_id"]))
    category_totals: dict[str, dict[str, float | int]] = {}
    for hit in hits:
        category = hit["obstacle_category"]
        totals = category_totals.setdefault(
            category, {"positive_volume_hit_count": 0, "intersection_volume_mm3": 0.0}
        )
        totals["positive_volume_hit_count"] += 1
        totals["intersection_volume_mm3"] += hit["intersection_volume_mm3"]
    for totals in category_totals.values():
        totals["intersection_volume_mm3"] = round(
            float(totals["intersection_volume_mm3"]), 9
        )
    return {
        "positive_volume_hit_count": len(hits),
        "positive_volume_hit_total_mm3": round(
            sum(row["intersection_volume_mm3"] for row in hits), 9
        ),
        "positive_volume_hits": hits,
        "positive_volume_hits_by_obstacle_category": dict(
            sorted(category_totals.items())
        ),
        "nearest_nonpenetrating_gap": (
            None
            if nearest is None
            else {
                "gap_mm": round(nearest[0], 9),
                "moving_id": nearest[1],
                "obstacle_id": nearest[2],
                "exact_shape_distance": True,
            }
        ),
        "moving_obstacle_pair_count": pair_count,
    }


def _pose_key(offset_mm: float) -> str:
    if offset_mm == 0:
        return "seated_0mm"
    direction = "plus_n" if offset_mm > 0 else "minus_n"
    return f"{direction}_{abs(offset_mm):g}mm"


def _path_offsets(sign: int, *, insertion: bool) -> list[float]:
    magnitudes = sorted(SAMPLE_DISTANCES_MM, reverse=insertion)
    return [float(sign * value) for value in magnitudes]


def diagnostic_report(geometry: Any) -> dict[str, Any]:
    """Screen sampled ±N positions using one already-composed WJ12 object."""
    scene = _shape_registry(geometry)
    n_axis = tuple(scene.source_metadata["motion_basis"]["N_global_xyz_per_mm"])
    pose_offsets = sorted(
        {float(sign * distance) for sign in (-1, 1) for distance in SAMPLE_DISTANCES_MM}
    )
    poses = {}
    evaluated_translation_keys: set[tuple[float, float, float]] = set()
    for offset in pose_offsets:
        translation = tuple(component * offset for component in n_axis)
        translation_key = tuple(round(value, 12) for value in translation)
        if translation_key in evaluated_translation_keys:
            raise ValueError("sampled N offsets unexpectedly duplicate a CAD pose")
        evaluated_translation_keys.add(translation_key)
        poses[_pose_key(offset)] = {
            "signed_N_offset_mm": offset,
            "translation_global_xyz_mm": [round(value, 9) for value in translation],
            **_evaluate_pose(
                scene.moving_shapes,
                scene.obstacle_shapes,
                translation,
                moving_categories=scene.moving_categories,
                obstacle_categories=scene.obstacle_categories,
            ),
        }

    def path_step(offset: float) -> dict[str, Any]:
        pose_id = _pose_key(offset)
        pose = poses[pose_id]
        return {
            "signed_N_offset_mm": offset,
            "pose_id": pose_id,
            "positive_volume_hit_count": pose["positive_volume_hit_count"],
            "positive_volume_hit_total_mm3": pose["positive_volume_hit_total_mm3"],
            "positive_volume_hits_by_obstacle_category": pose[
                "positive_volume_hits_by_obstacle_category"
            ],
            "positive_volume_hits_record_ref": f"sampled_poses/{pose_id}/positive_volume_hits",
            "nearest_nonpenetrating_gap": pose["nearest_nonpenetrating_gap"],
        }

    paths = {}
    for sign, direction_name in ((1, "+N"), (-1, "−N")):
        approach = _path_offsets(sign, insertion=True)
        reverse = _path_offsets(sign, insertion=False)
        paths[direction_name] = {
            "approach_steps_from_offset_to_seated": [
                path_step(offset) for offset in approach
            ],
            "reverse_steps_from_seated_to_offset": [
                path_step(offset) for offset in reverse
            ],
        }

    moving_hardware_ids = sorted(
        shape_id
        for shape_id in scene.moving_shapes
        if shape_id.startswith("candidate_installed_hardware/")
    )
    omitted_hardware_ids = [
        shape_id for shape_id in scene.omitted_candidate_stack_component_ids
    ]
    obstacle_ids = sorted(scene.obstacle_shapes)
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": "sampled_nominal_motion_diagnostic_only",
        "source": dict(scene.source_metadata),
        "assembly_state": {
            "moving_member_ids": list(MOVING_MEMBER_IDS),
            "moving_shape_ids": list(scene.moving_member_ids),
            "moving_rail_stack_ids": list(scene.moving_stack_ids),
            "moving_rail_stack_component_ids": moving_hardware_ids,
            "omitted_not_yet_installed_upright_stack_ids": list(
                scene.omitted_candidate_stack_ids
            ),
            "omitted_not_yet_installed_upright_stack_component_ids": omitted_hardware_ids,
            "temporarily_absent_panel_receiver_screw_axis_ids": list(
                scene.temporarily_absent_panel_axis_ids
            ),
            "panel_geometry_retained_as_stationary_obstacles": True,
            "panel_support_or_removal_step_proven": False,
            "canonical_source_wood_member_ids": list(scene.source_wood_member_ids),
            "canonical_source_wood_member_count": len(scene.source_wood_member_ids),
            "complete_finished_wood_member_ids": list(scene.finished_wood_member_ids),
            "complete_finished_wood_member_count": len(scene.finished_wood_member_ids),
            "panel_member_ids": list(scene.panel_member_ids),
            "panel_member_count": len(scene.panel_member_ids),
            "panel_replacement_ids": list(scene.panel_replacement_ids),
            "panel_replacement_count": len(scene.panel_replacement_ids),
            "canonical_fixed_panel_axis_count_preserved": len(
                geometry.source_inventory["fixed_panel_kicker_screws"]
            ),
            "canonical_fixed_panel_axis_inventory_sha256": scene.fixed_axis_inventory_sha256,
            "replaced_source_sds_axis_ids_excluded": list(
                scene.replaced_source_axis_ids
            ),
            "replaced_upper_right_source_duty_sds_axis_ids": list(
                scene.replaced_upper_duty_axis_ids
            ),
            "replaced_source_angle_duty_ids_not_modeled": list(
                scene.replaced_target_duty_ids
            ),
            "retained_legacy_sds_and_angle_obstacles_included": True,
            "suppressed_protected_alias_families": list(
                scene.suppressed_duplicate_protected_families
            ),
            "omitted_nonphysical_access_envelope_ids": list(
                scene.omitted_access_envelopes
            ),
            "obstacle_shape_ids": obstacle_ids,
            "obstacle_shape_count": len(obstacle_ids),
            "obstacle_shape_categories": dict(
                sorted(Counter(scene.obstacle_categories.values()).items())
            ),
            "hit_category_contract": {
                "finished_timber_geometry": "complete source plus WJ12 finished wood map, including all six panels exactly once",
                "candidate_installed_hardware_shape": "modeled candidate bolt component role; purchased/delivered fit is not verified",
                "frame_bolt_installed_component_shape": "modeled installed source-bolt component",
                "fixed_panel_screw_axis_envelope": "occupied axis geometry for canonical Hillman screw; the two upper-right receiver screws are temporarily absent",
                "retained_source_sds_axis_envelope": "occupied axis geometry for retained legacy SDS screws",
                "frame_bolt_source_occupied_axis_envelope": "occupied source axis envelope, separate from installed bolt components",
                "provisional_clearance_envelope": "conservative hole/projection keepout, not a physical installed part",
                "retained_angle_geometry": "retained source clip/angle CAD geometry",
                "retained_tnut_geometry": "retained service hardware geometry",
                "retained_light_geometry": "retained light geometry",
                "retained_wire_geometry": "retained wire geometry",
            },
            "other_composition_categories_not_used_as_obstacles": {
                "raw_source_hosts_and_candidate_parts": "complete finished wood map supersedes these pre-machining inputs",
                "source legacy clips and T-nuts from parts()": "non-wood source outputs are checked by exact ID and represented through retained clip and T-nut obstacle maps",
                "candidate_bores": "removed-material occupancy envelopes, not solids",
                "source_and_candidate_cutters": "machining tools, not installed obstacles",
                "source inventory and cut-reconstruction records": "metadata; finished results are included",
            },
        },
        "sampling": {
            "basis": "source WJ04 FrameBasis N axis",
            "N_global_xyz_per_mm": list(n_axis),
            "sample_distances_mm_each_sign": list(SAMPLE_DISTANCES_MM),
            "unique_cad_pose_evaluations": len(evaluated_translation_keys),
            "path_step_results_reuse_sampled_pose_records": True,
            "sampling_kind": "discrete nominal positions; no continuous swept-volume proof",
            "intersection_volume_report_threshold_mm3": HIT_TOLERANCE_MM3,
            "gap_method": "exact nearest nonpenetrating shape distance; AABB separation is used as a lower bound to prune distant pairs",
        },
        "paths": paths,
        "sampled_poses": poses,
        "release": {
            "movement_path_proven": False,
            "assembly_proven": False,
            "tool_or_hand_access_claimed": False,
            "physical_transport_route_proven": False,
            "capacity_established": False,
            "purchase_approved": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_accepted": False,
        },
        "limitations": [
            "A sampled positive-volume hit identifies only that nominal pose; it does not prove a physical route is impossible.",
            "Hardware-role shapes, occupied-axis envelopes, service geometry, and provisional keepouts are reported as distinct hit categories; an overlap with any modeled proxy still requires interpretation and is not a physical impossibility finding.",
            "A sampled clear pose does not establish clearance between samples or a complete assembly path.",
            "Panels remain fixed as conservative geometry after their two upper-rail receiver screw axes are declared absent; the necessary panel removal/support operation is unmodeled.",
            "Temporary support, human handling, tool fit, torque, delivered dimensions, tolerance, and forward/reverse assembly are not established.",
            "Four principal/side bolt stacks are absent from this insertion stage and must be installed in a later operation screen.",
        ],
    }


__all__ = ["diagnostic_report"]
