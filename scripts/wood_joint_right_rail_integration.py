"""One source-bound machining pass for four right-side rail duties.

The WJ-04 G7 and WJ-06 outer-pair producers remain independent diagnostic
hypotheses. This adapter combines their finished candidate bodies and hardware
on shared source members; it does not establish installation access, capacity,
or release.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import validate_source_binding
from mini_moonboard.wood_joint_geometry import BoltStack, washer_support_report
from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_probe as wj04_base
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as wj04_g7
from scripts import wood_joint_wj06_outer_pair_probe as wj06_outer

ROOT = Path(__file__).resolve().parents[1]
HIT_TOLERANCE_MM3 = 1e-6
SOURCE_RECONSTRUCTION_TOLERANCE_MM3 = 1e-3
LAYER_FRACTION_TOLERANCE = 1e-6
INCH_TO_MM = 25.4
WJ06_SIDE_NOMINAL_STEEL_DIAMETER_MM = 6.35
ORDINARY_BOLT_BODY_MAXIMUM_IN = 0.260
ORDINARY_BOLT_BODY_MAXIMUM_MM = ORDINARY_BOLT_BODY_MAXIMUM_IN * INCH_TO_MM
ORDINARY_BODY_MAXIMUM_SOURCE = (
    "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md"
)

SCHEMA = "wood_joint_right_rail_integration/v1"
FAMILY_WJ04 = "wj04_g7"
FAMILY_WJ06 = "wj06_outer_pair"

SHARED_HOSTS = frozenset(
    {
        wj04_g7.LOWER_RAIL,
        wj04_g7.UPPER_RAIL,
        wj04_g7.PRINCIPAL,
        wj06_outer.SIDE_HOST,
    }
)
TARGET_STATIONS = frozenset(
    {
        wj04_g7.LOWER_STATION,
        wj04_g7.UPPER_STATION,
        wj06_outer.LOWER_STATION,
        wj06_outer.UPPER_STATION,
    }
)


@dataclass(frozen=True)
class RightRailIntegrationGeometry:
    """Reusable materialized geometry and non-acceptance diagnostics."""

    source: Any
    source_binding: Any
    inventory: dict[str, Any]
    source_inputs_sha256: dict[str, str]
    trial_ids: dict[str, str]
    duties: dict[str, dict[str, Any]]
    replaced_source_axis_ids: frozenset[str]
    retained_source_axis_shapes: dict[str, cq.Shape]
    retained_legacy_clip_shapes: dict[str, cq.Shape]
    parts: dict[str, cq.Shape]
    finished: dict[str, cq.Shape]
    stacks: dict[str, BoltStack]
    bores: dict[str, cq.Shape]
    installed: dict[str, dict[str, cq.Shape]]
    panels: dict[str, cq.Shape]
    all_wood: dict[str, cq.Shape]
    protected: dict[str, dict[str, cq.Shape]]
    bore_reports: dict[str, dict[str, Any]]
    cross_bore_hits_mm3: dict[str, dict[str, float]]
    candidate_body_hits: dict[str, dict[str, Any]]
    installed_hits: dict[str, dict[str, Any]]
    washer_support: dict[str, dict[str, Any]]
    side_shaft_envelope_sensitivity: dict[str, Any]
    body_solid_checks: dict[str, dict[str, Any]]
    machining: dict[str, dict[str, Any]]
    source_reconstruction: dict[str, dict[str, Any]]
    diagnostic_gates: dict[str, Any]
    release: dict[str, bool]


def diagnostic_report(geometry: RightRailIntegrationGeometry) -> dict[str, Any]:
    """Return compact JSON-safe evidence; never serialize CadQuery objects."""
    binding = geometry.source_binding
    stack_rows = []
    for stack_key, stack in sorted(geometry.stacks.items()):
        stack_rows.append(
            {
                "stack_id": stack_key,
                "axis_point_global_xyz_mm": [
                    round(value, 6) for value in stack.head_seat.center.toTuple()
                ],
                "axis_direction_global_xyz": [
                    round(value, 9) for value in stack.direction.toTuple()
                ],
                "hardware_candidate_sku": stack.hardware.candidate_sku,
                "nominal_under_head_length_mm": round(
                    stack.hardware.under_head_length_mm, 6
                ),
                "steel_diameter_mm": round(stack.hardware.steel_diameter_mm, 6),
                "drill_diameter_mm": round(stack.hardware.drill_diameter_mm, 6),
                "wood_layers_head_to_nut": [
                    {"member_id": layer.body_id, "thickness_mm": layer.thickness_mm}
                    for layer in stack.layers
                ],
                "grip_mm": round(stack.grip_mm, 6),
            }
        )

    installed_conflicts = {
        stack_id: {
            role: {category: hits for category, hits in categories.items() if hits}
            for role, categories in stack_reports.items()
            if any(categories.values())
        }
        for stack_id, stack_reports in geometry.installed_hits.items()
        if any(any(categories.values()) for categories in stack_reports.values())
    }
    body_checks = {
        name: {
            "valid": record["valid"],
            "solid_count": record["solid_count"],
            "volume_mm3": record["volume_mm3"],
            "valid_single_positive_volume_solid": record[
                "valid_single_positive_volume_solid"
            ],
        }
        for name, record in geometry.body_solid_checks.items()
    }
    source_binding = {
        "inventory_sha256": binding.inventory_sha256,
        "runtime_module_sha256": dict(binding.runtime_module_sha256),
        "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
        "uncut_host_shape_sha256": dict(binding.uncut_host_shape_sha256),
        "duty_host_mapping": {
            name: list(hosts) for name, hosts in binding.duty_host_mapping.items()
        },
        "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
        "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
    }
    return {
        "schema": SCHEMA,
        "title": "Right rail four-duty installed geometry diagnostic",
        "status": "unaccepted integrated trial geometry",
        "source_candidate": geometry.inventory["candidate"],
        "source_commit": geometry.inventory["source_commit"],
        "source_binding": source_binding,
        "source_inputs_sha256": dict(geometry.source_inputs_sha256),
        "trial_ids": dict(geometry.trial_ids),
        "trial_sources": {
            FAMILY_WJ04: {
                "producer": "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
                "producer_sha256": geometry.source_inputs_sha256[
                    "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"
                ],
                "config_sha256": WJ04_TRIAL.canonical_sha256,
            },
            FAMILY_WJ06: {
                "producer": "scripts/wood_joint_wj06_outer_pair_probe.py",
                "producer_sha256": geometry.source_inputs_sha256[
                    "scripts/wood_joint_wj06_outer_pair_probe.py"
                ],
                "config_sha256": None,
            },
        },
        "duty_count": len(geometry.duties),
        "duties": {
            name: {
                "legacy_host_members": list(row["legacy_host_members"]),
                "replaced_old_sds_axis_ids": [
                    axis["axis_id"] for axis in row["legacy_sds_axes"]
                ],
            }
            for name, row in geometry.duties.items()
        },
        "counts": {
            "shared_source_hosts": len(SHARED_HOSTS),
            "candidate_cleats": len(set(geometry.parts) - SHARED_HOSTS),
            "candidate_stack_axes": len(geometry.stacks),
            "candidate_bore_axes": len(geometry.bores),
            "installed_hardware_components": sum(
                len(components) for components in geometry.installed.values()
            ),
            "replaced_source_sds_axes": len(geometry.replaced_source_axis_ids),
            "retained_source_sds_axes": len(geometry.retained_source_axis_shapes),
            "retained_legacy_clip_bodies": len(geometry.retained_legacy_clip_shapes),
            "fixed_panel_screw_axes": len(
                geometry.protected.get("fixed_66_hillman_axes_63p5mm", {})
            ),
            "starting_frame_bolt_components": len(
                geometry.protected.get("retained_12_frame_bolt_components", {})
            ),
            "candidate_panel_bodies": len(geometry.panels),
        },
        "source_reconstruction": geometry.source_reconstruction,
        "machining": geometry.machining,
        "candidate_bodies": body_checks,
        "candidate_body_hits": geometry.candidate_body_hits,
        "stacks": stack_rows,
        "bore_checks": geometry.bore_reports,
        "cross_bore_hits_mm3": geometry.cross_bore_hits_mm3,
        "washer_support": geometry.washer_support,
        "installed_component_conflicts": installed_conflicts,
        "side_shaft_envelope_sensitivity": geometry.side_shaft_envelope_sensitivity,
        "protected_geometry_counts": {
            family: len(shapes) for family, shapes in geometry.protected.items()
        },
        "diagnostic_gates": geometry.diagnostic_gates,
        "release": dict(geometry.release),
        "claim_boundary": {
            "installed_geometry_is_a_diagnostic_only": True,
            "integrated_clearance_accepted": False,
            "movement_or_installation_access_proven": False,
            "capacity_established": False,
            "drilling_released": False,
            "fabrication_released": False,
            "assembly_proven": False,
            "ordinary_body_maximum_is_delivered_hardware": False,
            "ordinary_body_maximum_is_selected_or_adopted": False,
        },
    }


def _wj06_side_stack_keys() -> tuple[str, ...]:
    return tuple(
        _namespace(FAMILY_WJ06, wj06_outer.TRIAL_ID, spec.stack_id)
        for spec in wj06_outer.STACK_SPECS
        if spec.interface_id == "cleat_to_side"
    )


def _ordinary_body_maximum_side_stack(stack: BoltStack) -> BoltStack:
    """Change CAD shaft occupancy only; retain steel/design diameter and stack."""
    if not math.isclose(
        stack.hardware.steel_diameter_mm,
        WJ06_SIDE_NOMINAL_STEEL_DIAMETER_MM,
        abs_tol=1e-9,
    ):
        raise ValueError("WJ-06 side stack nominal steel diameter changed")
    if not math.isclose(
        stack.hardware.cad_occupied_diameter_mm,
        WJ06_SIDE_NOMINAL_STEEL_DIAMETER_MM,
        abs_tol=1e-9,
    ):
        raise ValueError("WJ-06 side stack nominal CAD shaft diameter changed")
    if ORDINARY_BOLT_BODY_MAXIMUM_MM > stack.hardware.drill_diameter_mm:
        raise ValueError("ordinary-class maximum shaft exceeds unchanged bore")
    hardware = replace(
        stack.hardware,
        cad_occupied_diameter_mm=ORDINARY_BOLT_BODY_MAXIMUM_MM,
    )
    return replace(stack, hardware=hardware)


def _shaft_clearance_screen(
    stack_key: str,
    shaft: cq.Shape,
    installed: dict[str, dict[str, cq.Shape]],
    all_wood: dict[str, cq.Shape],
    protected: dict[str, dict[str, cq.Shape]],
) -> dict[str, Any]:
    other_components = {
        f"{peer_key}/{role}": shape
        for peer_key, components in installed.items()
        if peer_key != stack_key
        for role, shape in components.items()
    }
    return {
        "finished_wood_hits_mm3": _hits(shaft, all_wood),
        "protected_geometry_hits_mm3": {
            family: _hits(shaft, shapes) for family, shapes in protected.items()
        },
        "other_installed_components_hits_mm3": _hits(shaft, other_components),
    }


def _side_shaft_envelope_sensitivity(
    stacks: dict[str, BoltStack],
    installed: dict[str, dict[str, cq.Shape]],
    all_wood: dict[str, cq.Shape],
    protected: dict[str, dict[str, cq.Shape]],
) -> dict[str, Any]:
    """Compare nominal and class-maximum shaft envelopes on four WJ-06 side stacks."""
    keys = _wj06_side_stack_keys()
    if len(keys) != 4 or len(set(keys)) != 4:
        raise ValueError("WJ-06 side envelope sensitivity requires four unique stacks")
    missing = set(keys) - stacks.keys() | (set(keys) - installed.keys())
    if missing:
        raise ValueError(
            "WJ-06 side envelope sensitivity is missing stack geometry: "
            + ", ".join(sorted(missing))
        )
    missing_shafts = {key for key in keys if "shaft" not in installed[key]}
    if missing_shafts:
        raise ValueError(
            "WJ-06 side envelope sensitivity is missing nominal shaft geometry: "
            + ", ".join(sorted(missing_shafts))
        )

    scenarios: dict[str, dict[str, Any]] = {}
    for scenario, maximum in (("nominal", False), ("ordinary_class_maximum", True)):
        shapes: dict[str, cq.Shape] = {}
        screens: dict[str, dict[str, Any]] = {}
        for key in keys:
            stack = stacks[key]
            selected_stack = (
                _ordinary_body_maximum_side_stack(stack) if maximum else stack
            )
            shaft = selected_stack.shaft_shape() if maximum else installed[key]["shaft"]
            shapes[key] = shaft
            screens[key] = _shaft_clearance_screen(
                key, shaft, installed, all_wood, protected
            )
            screens[key].update(
                {
                    "steel_or_design_diameter_mm": round(
                        selected_stack.hardware.steel_diameter_mm, 6
                    ),
                    "cad_occupied_diameter_mm": round(
                        selected_stack.hardware.cad_occupied_diameter_mm, 6
                    ),
                    "drilled_bore_diameter_mm": round(
                        selected_stack.hardware.drill_diameter_mm, 6
                    ),
                    "under_head_length_mm": round(
                        selected_stack.hardware.under_head_length_mm, 6
                    ),
                    "same_axis_and_seats_as_nominal": True,
                    "same_head_washers_and_nut_as_nominal": True,
                    "modeled_overlap_present": any(
                        screens[key][category]
                        for category in (
                            "finished_wood_hits_mm3",
                            "other_installed_components_hits_mm3",
                        )
                    )
                    or any(
                        any(hits.values())
                        for hits in screens[key]["protected_geometry_hits_mm3"].values()
                    ),
                }
            )
        pairwise_hits: dict[str, dict[str, float]] = {key: {} for key in keys}
        for index, first_key in enumerate(keys):
            for second_key in keys[index + 1 :]:
                overlap = _intersect_volume(shapes[first_key], shapes[second_key])
                if overlap > HIT_TOLERANCE_MM3:
                    volume = round(overlap, 6)
                    pairwise_hits[first_key][second_key] = volume
                    pairwise_hits[second_key][first_key] = volume
        scenarios[scenario] = {
            "shaft_diameter_mm": (
                ORDINARY_BOLT_BODY_MAXIMUM_MM
                if maximum
                else WJ06_SIDE_NOMINAL_STEEL_DIAMETER_MM
            ),
            "modeled_overlap_present": any(
                row["modeled_overlap_present"] for row in screens.values()
            )
            or any(any(hits.values()) for hits in pairwise_hits.values()),
            "per_stack": screens,
            "peer_side_shaft_hits_mm3": pairwise_hits,
        }

    return {
        "status": "diagnostic shaft-envelope sensitivity only",
        "basis": {
            "ordinary_fastener_class": "ASME B18.2.1 ordinary 1/4-in bolt body",
            "ordinary_body_maximum_in": ORDINARY_BOLT_BODY_MAXIMUM_IN,
            "ordinary_body_maximum_mm": round(ORDINARY_BOLT_BODY_MAXIMUM_MM, 6),
            "nominal_side_steel_and_CAD_shaft_diameter_mm": (
                WJ06_SIDE_NOMINAL_STEEL_DIAMETER_MM
            ),
            "drilled_bores_changed": False,
            "seats_and_other_hardware_changed": False,
            "delivered_fastener_fit_verified": False,
            "hardware_selected_or_received": False,
            "capacity_or_joint_acceptance": False,
        },
        "screen_scope": {
            "finished_wood_member_count": len(all_wood),
            "protected_families_and_shape_counts": {
                family: len(shapes) for family, shapes in protected.items()
            },
            "other_installed_components": "all components on other stack IDs",
            "same_stack_companions": "excluded as intended bolt assembly parts",
            "peer_side_shaft_pair_checks": "reported separately for each scenario",
        },
        "scenarios": scenarios,
    }


def _intersect_volume(first: cq.Shape, second: cq.Shape) -> float:
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


def _hits(shape: cq.Shape, obstacles: dict[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, obstacle in obstacles.items()
        if (volume := _intersect_volume(shape, obstacle)) > HIT_TOLERANCE_MM3
    }


def _shape_difference_volume(first: cq.Shape, second: cq.Shape) -> float:
    """Return symmetric-difference volume without mutating either input."""
    return first.cut(second).Volume() + second.cut(first).Volume()


def _cutters_for_connection(source: Any, connection: Any) -> cq.Shape:
    direction = connection.direction.normalized()
    diameter = (
        source.bolt_dimensions(connection)["hole_diameter_mm"]
        if connection.kind == "bolt"
        else connection.diameter
    )
    return cq.Solid.makeCylinder(
        diameter / 2,
        connection.length + 2.0,
        connection.start - direction,
        direction,
    )


def _source_screw_axis_shape(connection: Any) -> cq.Shape:
    """Build occupied SDS axis proxy from source axis identity and extent."""
    if connection.kind != "screw":
        raise ValueError(f"legacy SDS axis is not a source screw: {connection.name}")
    return cq.Solid.makeCylinder(
        connection.diameter / 2,
        connection.length,
        connection.start,
        connection.direction.normalized(),
    )


def _source_cutter_map(
    source: Any,
    inventory: dict[str, Any],
    host_ids: frozenset[str],
) -> dict[str, dict[str, cq.Shape]]:
    """Collect exact source operations which finish each selected stock host."""
    result: dict[str, dict[str, cq.Shape]] = {name: {} for name in host_ids}
    connections = tuple(source.connections())
    by_name = {row.name: row for row in connections}
    if len(by_name) != len(connections):
        raise ValueError("source connections must have unique axis IDs")

    for connection in connections:
        cutter = _cutters_for_connection(source, connection)
        for host_id in host_ids.intersection(connection.members):
            result[host_id][connection.name] = cutter

    service_rows = tuple(source.service_cutters())
    for index, (member_id, name, cutter) in enumerate(service_rows):
        if member_id in host_ids:
            result[member_id][f"service/{index}/{name}"] = cutter

    additional_rows = tuple(source.additional_machining_cutters())
    for index, (member_id, name, operation, cutter) in enumerate(additional_rows):
        if member_id in host_ids:
            result[member_id][f"additional/{index}/{name}/{operation}"] = cutter

    panel_rows = inventory.get("fixed_panel_kicker_screws", ())
    if len(panel_rows) != 66:
        raise ValueError("right-rail integration requires all 66 fixed panel axes")
    panel_ids: set[str] = set()
    for row in panel_rows:
        axis_id = row["axis_id"]
        connection = by_name.get(axis_id)
        if connection is None:
            raise ValueError(f"fixed panel axis missing from source: {axis_id}")
        panel_ids.add(axis_id)
        direction = connection.direction.normalized()
        cutter = cq.Solid.makeCylinder(
            connection.diameter / 2,
            row["shop_purchased_length_mm"],
            connection.start,
            direction,
        )
        for host_id in host_ids.intersection(connection.members):
            result[host_id][f"panel_purchase/{axis_id}"] = cutter

    if len(panel_ids) != 66:
        raise ValueError("fixed panel screw axis IDs must be unique")
    return result


def machine_shared_hosts(
    raw_hosts: dict[str, cq.Shape],
    source_cutters_by_host: dict[str, dict[str, cq.Shape]],
    *,
    replaced_source_axis_ids: set[str] | frozenset[str],
    candidate_bores_by_host: dict[str, dict[str, cq.Shape]],
) -> dict[str, cq.Shape]:
    """Cut retained source work and candidate bores from raw candidate parts.

    Only named source axes in ``replaced_source_axis_ids`` are skipped. Each
    candidate bore is applied to every layer body assigned by its stack record.
    CadQuery's multi-tool cut removes the union of these cutters in one pass.
    """
    replaced = set(replaced_source_axis_ids)
    present = {
        axis_id
        for cutter_map in source_cutters_by_host.values()
        for axis_id in cutter_map
    }
    missing = replaced - present
    if missing:
        raise ValueError(
            "replaced source axis is not present in the source cutter map: "
            + ", ".join(sorted(missing))
        )

    result: dict[str, cq.Shape] = {}
    for host_id, raw_shape in raw_hosts.items():
        if not isinstance(raw_shape, cq.Shape) or not raw_shape.isValid():
            raise ValueError(f"raw candidate part is invalid: {host_id}")
        source_cutters = source_cutters_by_host.get(host_id, {})
        candidate_cutters = candidate_bores_by_host.get(host_id, {})
        tools = [
            cutter
            for axis_id, cutter in source_cutters.items()
            if axis_id not in replaced
        ] + list(candidate_cutters.values())
        finished = raw_shape.cut(*tools).clean() if tools else raw_shape
        if not finished.isValid() or not finished.Solids():
            raise ValueError(f"machining produced invalid candidate part: {host_id}")
        result[host_id] = finished
    return result


def _source_inputs_sha256() -> dict[str, str]:
    files = set(wj04_g7.SOURCE_INPUTS) | set(wj06_outer.SOURCE_INPUTS)
    files.update(
        {
            "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
            "scripts/wood_joint_wj06_outer_pair_probe.py",
            "scripts/wood_joint_right_rail_integration.py",
            ORDINARY_BODY_MAXIMUM_SOURCE,
        }
    )
    return {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in sorted(files)
    }


def _namespace(family: str, trial_id: str, stack_id: str) -> str:
    return f"{family}/{trial_id}/{stack_id}"


def _load_pinned_source_inventory(source_binding: Any) -> dict[str, Any]:
    """Reuse WJ-06's lightweight inventory loader; verify bound inventory SHA."""
    if source_binding.inventory_sha256 != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("source binding differs from canonical inventory pin")
    inventory = wj06_outer._inventory()
    if inventory["candidate"] != wj06_outer.CANDIDATE:
        raise ValueError("right-rail inventory candidate changed")
    if (
        len(inventory["legacy_duties"]) != 24
        or sum(len(row["legacy_sds_axes"]) for row in inventory["legacy_duties"]) != 144
        or len(inventory["fixed_panel_kicker_screws"]) != 66
        or len(inventory["starting_frame_bolts"]) != 12
    ):
        raise ValueError("right-rail source inventory schema or counts changed")
    return inventory


def _selected_duties(
    inventory: dict[str, Any],
    replaced_axis_ids: frozenset[str],
) -> dict[str, dict[str, Any]]:
    rows = {
        row["legacy_station_id"]: row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in TARGET_STATIONS
    }
    if set(rows) != TARGET_STATIONS:
        raise ValueError("right-rail slice requires its exact four source duties")
    expected_hosts = {
        wj04_g7.LOWER_STATION: [wj04_g7.LOWER_RAIL, wj04_g7.PRINCIPAL],
        wj04_g7.UPPER_STATION: [wj04_g7.UPPER_RAIL, wj04_g7.PRINCIPAL],
        wj06_outer.LOWER_STATION: [wj06_outer.LOWER_RAIL, wj06_outer.SIDE_HOST],
        wj06_outer.UPPER_STATION: [wj06_outer.UPPER_RAIL, wj06_outer.SIDE_HOST],
    }
    axis_ids = {
        axis["axis_id"] for row in rows.values() for axis in row["legacy_sds_axes"]
    }
    if axis_ids != set(replaced_axis_ids) or len(axis_ids) != 24:
        raise ValueError("right-rail slice must replace exactly 24 old SDS axes")
    for station_id, row in rows.items():
        if row["legacy_host_members"] != expected_hosts[station_id]:
            raise ValueError(f"{station_id}: source host mapping changed")
        axes = row["legacy_sds_axes"]
        if len(axes) != 6 or any(
            axis.get("shop_opening_kind") != "sds_wood" for axis in axes
        ):
            raise ValueError(f"{station_id}: source openings are not six SDS axes")
    return rows


def _cut_record(
    host_id: str,
    cutters: dict[str, cq.Shape],
    replaced_axis_ids: frozenset[str],
    candidate_bores: dict[str, cq.Shape],
) -> dict[str, Any]:
    removed = sorted(replaced_axis_ids.intersection(cutters))
    retained_source = sorted(set(cutters) - set(removed))
    return {
        "source_stock": "kerf-right uncut_wood_parts() member shape",
        "removed_source_sds_axis_ids": removed,
        "retained_source_cutter_ids": retained_source,
        "source_cutter_counts": {
            "named_connections": sum(
                not name.startswith(("service/", "additional/", "panel_purchase/"))
                for name in retained_source
            ),
            "service_cutters": sum(
                name.startswith("service/") for name in retained_source
            ),
            "additional_cutters": sum(
                name.startswith("additional/") for name in retained_source
            ),
            "purchased_panel_screw_cutters": sum(
                name.startswith("panel_purchase/") for name in retained_source
            ),
        },
        "candidate_bore_ids": sorted(candidate_bores),
        "source_cutters_retained": len(retained_source),
        "candidate_bores_applied": len(candidate_bores),
        "old_sds_restored": False,
        "cut_union_applied_to_raw_stock": True,
    }


def materialize_right_rail_geometry(
    base_geometry: Any | None = None,
) -> RightRailIntegrationGeometry:
    """Build one source-bound, statically installed four-duty geometry slice.

    This call performs CAD booleans and should run only under the repository's
    serialized geometry slot. Supplying a base WJ-04 materialization reuses its
    validated source object; both producer adapters receive that same object.
    """
    source_inputs_before = _source_inputs_sha256()
    if base_geometry is None:
        base_geometry = wj04_base.materialize_trial_geometry(WJ04_TRIAL)
    if base_geometry.config.canonical_sha256 != WJ04_TRIAL.canonical_sha256:
        raise ValueError("right-rail integration requires canonical WJ-04 base config")
    source = base_geometry.source
    binding_before = validate_source_binding(source)
    if binding_before != base_geometry.source_binding:
        raise ValueError("WJ-04 base materializer source binding changed")
    if binding_before.inventory_sha256 != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("right-rail source inventory differs from canonical pin")

    g7 = wj04_g7.materialize_geometry(base_geometry)
    outer = wj06_outer.materialize_geometry(source=source)
    if g7.base.source is not source or outer.source is not source:
        raise ValueError("right-rail producers must share the same source object")
    if (
        g7.base.source_binding != binding_before
        or outer.source_binding != binding_before
    ):
        raise ValueError("right-rail producer source bindings differ")

    inventory = _load_pinned_source_inventory(binding_before)
    replaced_axis_ids = frozenset(g7.removed_axis_ids | outer.removed_axis_ids)
    duties = _selected_duties(inventory, replaced_axis_ids)
    raw_wood_parts = {part.name: part.shape for part in source.uncut_wood_parts()}
    current_wood_parts = {
        part.name: part.shape for part in source.parts() if part.name in raw_wood_parts
    }
    if not SHARED_HOSTS <= raw_wood_parts.keys():
        raise ValueError("source raw stock is missing one or more shared rail hosts")
    if not SHARED_HOSTS <= current_wood_parts.keys():
        raise ValueError("source finished stock is missing one or more shared hosts")

    # Baseline source reconstruction proves cutter inventory is complete before
    # the selected old SDS axes are omitted.
    source_cutters = _source_cutter_map(source, inventory, SHARED_HOSTS)
    for host_id in SHARED_HOSTS:
        replaced_for_host = replaced_axis_ids.intersection(source_cutters[host_id])
        if len(replaced_for_host) != 6:
            raise ValueError(
                f"{host_id}: expected six replaced source SDS cutters, "
                f"found {len(replaced_for_host)}"
            )
    source_reconstruction: dict[str, dict[str, Any]] = {}
    for host_id in sorted(SHARED_HOSTS):
        rebuilt = raw_wood_parts[host_id].cut(*source_cutters[host_id].values()).clean()
        delta = _shape_difference_volume(rebuilt, current_wood_parts[host_id])
        source_reconstruction[host_id] = {
            "symmetric_difference_mm3": round(delta, 6),
            "matches_source_finished_member": (
                delta <= SOURCE_RECONSTRUCTION_TOLERANCE_MM3
            ),
        }
        if delta > SOURCE_RECONSTRUCTION_TOLERANCE_MM3:
            raise ValueError(
                f"{host_id}: raw-stock retained-cut pass differs from source by "
                f"{delta:.6f} mm3"
            )

    panel_parts = {
        name: shape for name, shape in g7.panels.items() if name in RIGHT_PANEL_NAMES
    }
    if set(panel_parts) != RIGHT_PANEL_NAMES:
        raise ValueError(
            "integrated right-rail context requires all three right panels"
        )
    for name in RIGHT_PANEL_NAMES:
        if _shape_difference_volume(panel_parts[name], outer.panels[name]) > 1e-3:
            raise ValueError(f"WJ-04 and WJ-06 panel overlays differ: {name}")

    parts: dict[str, cq.Shape] = {name: raw_wood_parts[name] for name in SHARED_HOSTS}
    for cleat_id in (wj04_g7.LOWER_CLEAT, wj04_g7.UPPER_CLEAT):
        parts[cleat_id] = g7.parts[cleat_id]
    for cleat_id in (wj06_outer.LOWER_CLEAT, wj06_outer.UPPER_CLEAT):
        parts[cleat_id] = outer.cleats[cleat_id]
    candidate_cleat_ids = set(parts) - SHARED_HOSTS
    if len(candidate_cleat_ids) != 4:
        raise ValueError("right-rail slice must contain exactly four candidate cleats")
    source_finished_wood = dict(current_wood_parts)
    source_finished_wood.update(panel_parts)
    panels = {
        name: shape
        for name, shape in source_finished_wood.items()
        if name.startswith(("main_", "kicker_"))
    }
    precut_wood = {**source_finished_wood, **parts}

    stacks: dict[str, BoltStack] = {}
    bores: dict[str, cq.Shape] = {}
    installed: dict[str, dict[str, cq.Shape]] = {}
    for family, trial_id, geometry in (
        (FAMILY_WJ04, wj04_g7.TRIAL_ID, g7),
        (FAMILY_WJ06, wj06_outer.TRIAL_ID, outer),
    ):
        for stack_id, stack in geometry.stacks.items():
            key = _namespace(family, trial_id, stack_id)
            if key in stacks:
                raise ValueError(f"duplicate namespaced stack: {key}")
            if stack_id not in geometry.bores or stack_id not in geometry.installed:
                raise ValueError(f"producer omitted bore or installed hardware: {key}")
            stacks[key] = stack
            bores[key] = geometry.bores[stack_id]
            installed[key] = geometry.installed[stack_id]
    if len(stacks) != 16 or len(bores) != 16 or len(installed) != 16:
        raise ValueError("right-rail integration requires 16 unique candidate stacks")

    candidate_bores_by_host: dict[str, dict[str, cq.Shape]] = {
        name: {} for name in parts
    }
    bore_members: dict[str, tuple[str, ...]] = {}
    for stack_key, stack in stacks.items():
        layer_ids = tuple(layer.body_id for layer in stack.layers)
        if len(layer_ids) != 2 or len(set(layer_ids)) != 2:
            raise ValueError(f"{stack_key}: expected two distinct wood layers")
        if not set(layer_ids) <= parts.keys():
            raise ValueError(f"{stack_key}: stack layer is outside four-duty slice")
        bore_members[stack_key] = layer_ids
        for part_id in layer_ids:
            candidate_bores_by_host[part_id][stack_key] = bores[stack_key]

    finished = machine_shared_hosts(
        parts,
        source_cutters,
        replaced_source_axis_ids=replaced_axis_ids,
        candidate_bores_by_host=candidate_bores_by_host,
    )
    if len(finished) != 8:
        raise ValueError("four shared hosts and four cleats must be machined")

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
            fractions[layer.body_id] = round(
                _intersect_volume(segment, parts[layer.body_id]) / segment.Volume(),
                6,
            )
            progress += layer.thickness_mm
        own_ids = set(bore_members[stack_key])
        bore_reports[stack_key] = {
            "wood_layers_head_to_nut": [
                {"member_id": layer.body_id, "thickness_mm": layer.thickness_mm}
                for layer in stack.layers
            ],
            "layer_material_fractions_before_cut": fractions,
            "all_declared_layers_present": all(
                fraction >= 1 - LAYER_FRACTION_TOLERANCE
                for fraction in fractions.values()
            ),
        }

    cross_bore_hits: dict[str, dict[str, float]] = {key: {} for key in bores}
    stack_keys = sorted(bores)
    for index, first_id in enumerate(stack_keys):
        for second_id in stack_keys[index + 1 :]:
            overlap = _intersect_volume(bores[first_id], bores[second_id])
            if overlap > HIT_TOLERANCE_MM3:
                cross_bore_hits[first_id][second_id] = round(overlap, 6)
                cross_bore_hits[second_id][first_id] = round(overlap, 6)

    retained_source_axis_shapes: dict[str, cq.Shape] = {}
    connection_by_id = {row.name: row for row in source.connections()}
    for duty in inventory["legacy_duties"]:
        for axis in duty["legacy_sds_axes"]:
            axis_id = axis["axis_id"]
            if axis_id in replaced_axis_ids:
                continue
            connection = connection_by_id.get(axis_id)
            if connection is None:
                raise ValueError(f"retained legacy SDS axis missing: {axis_id}")
            retained_source_axis_shapes[axis_id] = _source_screw_axis_shape(connection)
    if len(retained_source_axis_shapes) != 120:
        raise ValueError("integrated slice must retain exactly 120 legacy SDS axes")

    all_legacy_ids = {row["legacy_station_id"] for row in inventory["legacy_duties"]}
    current_parts_by_id = {part.name: part.shape for part in source.parts()}
    retained_legacy_ids = all_legacy_ids - TARGET_STATIONS
    retained_legacy_clip_shapes = {
        name: current_parts_by_id[name]
        for name in retained_legacy_ids
        if name in current_parts_by_id
    }
    if (
        set(retained_legacy_clip_shapes) != retained_legacy_ids
        or len(retained_legacy_clip_shapes) != 20
    ):
        raise ValueError("integrated slice must retain exactly 20 source angle bodies")

    protected = {name: dict(shapes) for name, shapes in outer.protected.items()}
    protected["retained_legacy_sds_axes"] = retained_source_axis_shapes
    protected["retained_legacy_clips"] = retained_legacy_clip_shapes
    expected_protected_counts = {
        "fixed_66_hillman_axes_63p5mm": 66,
        "retained_12_frame_bolt_components": 60,
        "retained_12_frame_bolt_tools_withdrawals": 36,
        "tnuts": 142,
        "hold_hole_and_provisional_projection": 142,
        "lights": 132,
        "wires": 131,
    }
    for family, count in expected_protected_counts.items():
        if len(protected.get(family, {})) != count:
            raise ValueError(
                f"protected source inventory changed for {family}: "
                f"{len(protected.get(family, {}))} != {count}"
            )

    all_wood = {
        **source_finished_wood,
        **finished,
    }
    # Candidate panels are independent full timber bodies and keep their fixed
    # 66 source axes; they are not drilled by this four-duty slice.

    finished_timber = {**source_finished_wood, **finished}
    installed_hits: dict[str, dict[str, Any]] = {}
    washer_support: dict[str, dict[str, Any]] = {}
    side_shaft_envelope_sensitivity = _side_shaft_envelope_sensitivity(
        stacks,
        installed,
        all_wood,
        protected,
    )
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

    for stack_key, report in bore_reports.items():
        own_ids = set(bore_members[stack_key])
        report.update(
            {
                "other_source_wood_hits_mm3": _hits(
                    bores[stack_key],
                    {
                        name: shape
                        for name, shape in precut_wood.items()
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
            }
        )

    cleat_by_station = {
        spec.station_id: spec.cleat_id
        for spec in (*wj04_g7.STACK_SPECS, *wj06_outer.STACK_SPECS)
    }
    if set(cleat_by_station) != TARGET_STATIONS:
        raise ValueError("producer stacks must bind four target stations to cleats")
    candidate_body_hits: dict[str, dict[str, Any]] = {}
    for station_id, duty in duties.items():
        cleat_id = cleat_by_station[station_id]
        intended_hosts = set(duty["legacy_host_members"])
        other_source_wood = {
            name: shape
            for name, shape in precut_wood.items()
            if name not in intended_hosts
            and name not in candidate_cleat_ids
            and name not in panels
        }
        peer_cleats = {
            name: shape
            for name, shape in parts.items()
            if name in candidate_cleat_ids and name != cleat_id
        }
        body = parts[cleat_id]
        candidate_body_hits[cleat_id] = {
            "station_id": station_id,
            "intended_host_overlap_mm3": _hits(
                body,
                {name: precut_wood[name] for name in intended_hosts},
            ),
            "other_source_wood_hits_mm3": _hits(body, other_source_wood),
            "candidate_panel_hits_mm3": _hits(body, panels),
            "other_candidate_cleat_hits_mm3": _hits(body, peer_cleats),
            "fixed_geometry_hits_mm3": {
                family: hits
                for family, obstacles in physical_protected.items()
                if (hits := _hits(body, obstacles))
            },
            "access_envelope_hits_mm3": {
                family: hits
                for family, obstacles in access_protected.items()
                if (hits := _hits(body, obstacles))
            },
        }

    for stack_key, components in installed.items():
        other_hardware = {
            f"{other_key}/{role}": shape
            for other_key, peer_components in installed.items()
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
        for seat_name, seat in (
            ("head", stack.head_seat),
            ("nut", stack.nut_seat),
        ):
            support = washer_support_report(
                seat, finished[seat.body_id], stack.hardware
            )
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
            "valid_single_positive_volume_solid": shape.isValid()
            and len(shape.Solids()) == 1
            and shape.Volume() > HIT_TOLERANCE_MM3,
        }
        for name, shape in finished.items()
    }

    source_inputs = _source_inputs_sha256()
    if source_inputs != source_inputs_before:
        raise ValueError("right-rail source inputs changed during materialization")
    side_shaft_envelope_sensitivity["basis"]["source_pins_sha256"] = {
        path: source_inputs[path]
        for path in (
            "scripts/wood_joint_wj06_outer_pair_probe.py",
            ORDINARY_BODY_MAXIMUM_SOURCE,
            "scripts/wood_joint_right_rail_integration.py",
        )
    }
    binding_after = validate_source_binding(source)
    if binding_after != binding_before:
        raise ValueError("right-rail materialization mutated source binding")

    bore_layers_clear = all(
        report["all_declared_layers_present"] for report in bore_reports.values()
    )
    bores_disjoint = not any(cross_bore_hits.values())
    bores_clear = not any(
        report[category]
        for report in bore_reports.values()
        for category in (
            "other_source_wood_hits_mm3",
            "candidate_panel_hits_mm3",
            "fixed_geometry_hits_mm3",
        )
    )
    cleats_clear = not any(
        report[category]
        for report in candidate_body_hits.values()
        for category in (
            "other_source_wood_hits_mm3",
            "candidate_panel_hits_mm3",
            "other_candidate_cleat_hits_mm3",
            "fixed_geometry_hits_mm3",
        )
    )
    cleat_access_clear = not any(
        report["access_envelope_hits_mm3"] for report in candidate_body_hits.values()
    )
    installed_clear = not any(
        any(
            component_report[family]
            for family in (
                "finished_timber_mm3",
                "fixed_geometry_mm3",
                "other_installed_hardware_mm3",
            )
        )
        for stack_report in installed_hits.values()
        for component_report in stack_report.values()
    )
    machining = {
        host_id: _cut_record(
            host_id,
            source_cutters[host_id],
            replaced_axis_ids,
            candidate_bores_by_host[host_id],
        )
        for host_id in sorted(parts)
    }
    diagnostic_gates = {
        "source_raw_stock_reconstruction": all(
            row["matches_source_finished_member"]
            for row in source_reconstruction.values()
        ),
        "source_binding_and_input_hashes_stable": True,
        "declared_bore_layers_present": bore_layers_clear,
        "candidate_bores_disjoint": bores_disjoint,
        "candidate_bores_clear_of_integrated_fixed_geometry": bores_clear,
        "candidate_cleats_clear_of_unintended_integrated_geometry": cleats_clear,
        "candidate_cleats_clear_of_recorded_access_envelopes": cleat_access_clear,
        "all_candidate_bodies_are_valid_single_positive_volume_solids": all(
            row["valid_single_positive_volume_solid"]
            for row in body_solid_checks.values()
        ),
        "all_head_and_nut_washers_have_full_seat_support": all(
            support["full_seat"]
            for stack_support in washer_support.values()
            for support in stack_support.values()
        ),
        "right_panel_overlays_match_across_producers": True,
        "installed_state_geometry_conflicts_absent": installed_clear,
        "integrated_clearance_review": "not_run",
        "movement_or_installation_access": {
            "status": "not_run",
            "fixed_service_geometry_included": True,
            "provisional_wire_shape_count": len(protected["wires"]),
            "pre_wiring_or_harness_removal_proven": False,
            "plus_n_trial": (
                "future screen moves each rail with both family cleats; "
                "principal and side remain; X-axis candidate bolts absent"
            ),
            "physical_harness_staging_or_withdrawal_proven": False,
        },
        "load_capacity": "not_evaluated",
        "inventory_counts": {
            "duties": len(duties),
            "shared_source_hosts": len(SHARED_HOSTS),
            "candidate_cleats": 4,
            "candidate_stacks": len(stacks),
            "candidate_bore_axes": len(bores),
            "replaced_source_sds_axes": len(replaced_axis_ids),
            "retained_source_sds_axes": len(retained_source_axis_shapes),
            "retained_legacy_clip_bodies": len(retained_legacy_clip_shapes),
            "fixed_panel_screw_axes": len(protected["fixed_66_hillman_axes_63p5mm"]),
            "starting_frame_bolts": len(inventory["starting_frame_bolts"]),
            "service_cutters_on_shared_hosts": sum(
                len([name for name in cutter_map if name.startswith("service/")])
                for cutter_map in source_cutters.values()
            ),
            "additional_cutters_on_shared_hosts": sum(
                len([name for name in cutter_map if name.startswith("additional/")])
                for cutter_map in source_cutters.values()
            ),
        },
    }
    release = {
        "candidate_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_accepted": False,
        "assembly_proven": False,
        "purchase_approved": False,
    }

    return RightRailIntegrationGeometry(
        source=source,
        source_binding=binding_before,
        inventory=inventory,
        source_inputs_sha256=source_inputs,
        trial_ids={
            FAMILY_WJ04: wj04_g7.TRIAL_ID,
            FAMILY_WJ06: wj06_outer.TRIAL_ID,
        },
        duties=duties,
        replaced_source_axis_ids=replaced_axis_ids,
        retained_source_axis_shapes=retained_source_axis_shapes,
        retained_legacy_clip_shapes=retained_legacy_clip_shapes,
        parts=parts,
        finished=finished,
        stacks=stacks,
        bores=bores,
        installed=installed,
        panels=panels,
        all_wood=all_wood,
        protected=protected,
        bore_reports=bore_reports,
        cross_bore_hits_mm3={
            name: hits for name, hits in cross_bore_hits.items() if hits
        },
        candidate_body_hits=candidate_body_hits,
        installed_hits=installed_hits,
        washer_support=washer_support,
        side_shaft_envelope_sensitivity=side_shaft_envelope_sensitivity,
        body_solid_checks=body_solid_checks,
        machining=machining,
        source_reconstruction=source_reconstruction,
        diagnostic_gates=diagnostic_gates,
        release=release,
    )
