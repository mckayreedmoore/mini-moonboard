"""Source-bound provisional hardware and stock inventory for WJ24.

This module consumes an already composed WJ24 object. It does not materialize
families, change geometry, select products, price stock, or authorize buying,
cutting, drilling, assembly, or structural use.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import (
    _source_shape_fingerprint,
    validate_source_binding,
)
from scripts import wood_joint_top_outer_integration as top_outer
from scripts import wood_joint_wj24_compositor as wj24

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
ORDINARY_HARDWARE_BASIS_PATH = "docs/wood-joints-mvp/ordinary-hardware-basis.md"
HARDWARE_SCHEDULE_AUDIT_PATH = (
    "docs/wood-joints-mvp/hypotheses/current-hardware-schedule-audit.md"
)
BACKER_BASIS_PATH = "docs/wood-joints-mvp/wj05-center-backer-transfer.json"
CENTER_X190_SCREEN_PATH = (
    "docs/wood-joints-mvp/hypotheses/wj05-center-node-relieved.json"
)
SCHEMA = "wood_joint_wj24_hardware_inventory/v1"

ORDINARY_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
BACKER_ROLES = frozenset(
    {"shaft", "bottom_washer", "bottom_head", "top_washer", "top_nut"}
)

EXPECTED_FAMILY_AXIS_COUNTS = {
    "wj03_outer": 20,
    "wj05_backer": 4,
    "wj04_g7": 8,
    "wj06_outer_pair": 8,
    "wj05_center_x190": 16,
    "left_service": 16,
    "top_outer": 8,
    "top_center": 8,
    "bottom_outer": 8,
    "bottom_center": 8,
}

# Dimensions below are the provisional blanks in the producer coordinate
# systems. They are not retail dimensions, delivered-stock measurements, or
# approved cut lists. Each spec carries its own axis order and grain basis.
PART_STOCK_BASIS: dict[str, dict[str, Any]] = {
    **{
        f"knee_outer_{side}_spine": {
            "stock_group": "wj03_nominal_4x6_cutoff",
            "stock_description": "nominal 4x6 solid-sawn DF-L No. 2 cutoff model",
            "blank_dimensions_mm": [88.9, 139.7, 269.95],
            "dimension_axis_order": ["global X", "global Y", "global Z"],
            "grain_axis": "global Z",
            "fabrication_operations": [
                "crosscut to modeled blank length",
                "rear bevel at the compact WJ-03 local-N limit 137.7 mm",
            ],
            "basis_paths": [
                "scripts/wood_joint_wj03_compact_outer_probe.py",
                "mini_moonboard/wood_joint_frame.py",
            ],
        }
        for side in ("left", "right")
    },
    **{
        f"knee_outer_{side}_rear_bridge": {
            "stock_group": "wj03_nominal_2x4_cutoff",
            "stock_description": "nominal 2x4 solid-sawn DF-L No. 2 cutoff model",
            "blank_dimensions_mm": [383.2, 38.1, 88.9],
            "dimension_axis_order": ["global X", "global Y", "global Z"],
            "grain_axis": "global X",
            "fabrication_operations": [
                "crosscut to modeled blank length",
                "rear bevel at the compact WJ-03 local-N limit 137.7 mm",
            ],
            "basis_paths": [
                "scripts/wood_joint_wj03_compact_outer_probe.py",
                "mini_moonboard/wood_joint_frame.py",
            ],
        }
        for side in ("left", "right")
    },
    **{
        f"knee_outer_{side}_under_header_link": {
            "stock_group": "wj03_nominal_4x4_cutoff",
            "stock_description": "nominal 4x4 solid-sawn DF-L No. 2 cutoff model",
            "blank_dimensions_mm": [185.2, 88.9, 88.9],
            "dimension_axis_order": ["global X", "global Y", "global Z"],
            "grain_axis": "global X",
            "fabrication_operations": ["crosscut to modeled blank length"],
            "basis_paths": [
                "scripts/wood_joint_wj03_compact_outer_probe.py",
                "mini_moonboard/wood_joint_frame.py",
            ],
        }
        for side in ("left", "right")
    },
    "wj04_lower_full_stock_cleat": {
        "stock_group": "full_4x4_cleat_119p7",
        "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
        "blank_dimensions_mm": [88.9, 88.9, 119.7],
        "dimension_axis_order": ["source local X", "source local T", "source local N"],
        "grain_axis": "source local N",
        "fabrication_operations": ["crosscut to modeled blank", "through-bolt bores"],
        "basis_paths": ["scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"],
    },
    "wj04_upper_g7_crosscut_full_stock_cleat": {
        "stock_group": "full_4x4_cleat_119p7_with_86p9_crosscut",
        "stock_description": "full-section 4x4 development blank before G7 crosscut; delivered grade unverified",
        "blank_dimensions_mm": [88.9, 88.9, 119.7],
        "dimension_axis_order": ["source local X", "source local T", "source local N"],
        "grain_axis": "source local N",
        "fabrication_operations": [
            "crosscut to the archived 86.9 mm G7 grain-length geometry",
            "through-bolt bores",
        ],
        "basis_paths": ["scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"],
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_wj06_outer_pair_probe.py"],
        }
        for part_id in ("wj06_outer_lower_right_cleat", "wj06_outer_upper_right_cleat")
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_left_rail_integration.py"],
        }
        for part_id in (
            "left_service_inner_lower_cleat",
            "left_service_inner_upper_cleat",
            "left_service_outer_lower_cleat",
            "left_service_outer_upper_cleat",
        )
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_top_outer_integration.py"],
        }
        for part_id in ("top_outer_left_cleat", "top_outer_right_cleat")
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_top_center_integration.py"],
        }
        for part_id in ("top_center_left_cleat", "top_center_right_cleat")
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_bottom_outer_integration.py"],
        }
        for part_id in ("bottom_outer_left_cleat", "bottom_outer_right_cleat")
    },
    **{
        part_id: {
            "stock_group": "full_4x4_cleat_119p7",
            "stock_description": "full-section 4x4 development cleat blank; delivered grade unverified",
            "blank_dimensions_mm": [88.9, 88.9, 119.7],
            "dimension_axis_order": [
                "source local X",
                "source local T",
                "source local N",
            ],
            "grain_axis": "source local N",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_bottom_center_integration.py"],
        }
        for part_id in ("bottom_center_left_cleat", "bottom_center_right_cleat")
    },
    **{
        f"inner_kicker_backer_{side}": {
            "stock_group": "wj05_backer_full_4x4_238p9",
            "stock_description": "full-section 4x4 backer blank; actual stock unobserved",
            "blank_dimensions_mm": [88.9, 88.9, 238.9],
            "dimension_axis_order": ["global X", "global Y", "global Z"],
            "grain_axis": "global Z",
            "fabrication_operations": [
                "two modeled through-bolt paths and bottom counterbores Ø20 mm × 7 mm",
                "two redirected fixed panel-screw receiver cuts per backer",
            ],
            "basis_paths": [BACKER_BASIS_PATH],
        }
        for side in ("left", "right")
    },
    **{
        f"center_post_cleat_{side}": {
            "stock_group": "wj05_center_post_4x4_128p9",
            "stock_description": "full-section 4x4 center-post development cleat blank",
            "blank_dimensions_mm": [88.9, 88.9, 128.9],
            "dimension_axis_order": ["global X", "global Y", "global Z"],
            "grain_axis": "global Z",
            "fabrication_operations": [
                "crosscut to modeled blank",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_wj05_center_node_probe.py"],
        }
        for side in ("left", "right")
    },
    **{
        f"center_principal_cleat_{side}": {
            "stock_group": "wj05_center_principal_4x4_angled_blank",
            "stock_description": "full-section 4x4 principal-cleat development blank",
            "blank_dimensions_mm": [88.9, 88.9, 156.595957],
            "dimension_axis_order": [
                "source local X",
                "source local N",
                "source local T",
            ],
            "grain_axis": "source local T (parallel to center principal)",
            "fabrication_operations": [
                "angled end cuts to 82 mm finished grain length",
                "open wire-relief cut in the recorded source-local region",
                "through-bolt bores",
            ],
            "basis_paths": ["scripts/wood_joint_wj05_center_node_probe.py"],
        }
        for side in ("left", "right")
    },
}

if len(PART_STOCK_BASIS) != 28:
    raise RuntimeError("WJ24 stock contract must list exactly twenty-eight connectors")


def _sha256_file(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise ValueError(f"missing source-bound inventory input: {relative_path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_plain(item) for item in value]
    return value


def _verified_hash_map(values: Mapping[str, str], *, context: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative_path, digest in values.items():
        if not isinstance(relative_path, str) or not isinstance(digest, str):
            raise TypeError(f"{context} contains malformed source pins")
        current = _sha256_file(relative_path)
        if current != digest:
            raise ValueError(
                f"{context} source changed after composition: {relative_path}"
            )
        result[relative_path] = current
    if not result:
        raise ValueError(f"{context} source pin map is empty")
    return dict(sorted(result.items()))


def _family_for_axis_id(axis_id: str) -> str:
    prefixes = (
        ("left_service/", "left_service"),
        ("top_outer/", "top_outer"),
        ("top_center/", "top_center"),
        ("bottom_outer/", "bottom_outer"),
        ("bottom_center/", "bottom_center"),
        ("wj04_g7/", "wj04_g7"),
        ("wj06_outer_pair/", "wj06_outer_pair"),
        ("knee_outer_", "wj03_outer"),
        ("backer_header_", "wj05_backer"),
        ("center_", "wj05_center_x190"),
    )
    matches = [family for prefix, family in prefixes if axis_id.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"{axis_id}: no unique WJ24 family identity")
    return matches[0]


def _trial_key(family: str) -> str:
    return "center_x190" if family == "wj05_center_x190" else family


def _load_center_x190_grip_rows() -> tuple[dict[str, dict[str, Any]], str]:
    payload = json.loads((ROOT / CENTER_X190_SCREEN_PATH).read_text())
    if payload.get("trial_id") != "wj05-center-node-rear-4x4-upper-l82-wire-relief-v2":
        raise ValueError("WJ05 center-x190 historical grip-screen identity changed")
    rows = payload.get("provisional_fastener_axes", ())
    indexed = {row.get("axis_id"): row for row in rows}
    if len(indexed) != 16 or None in indexed:
        raise ValueError("WJ05 center-x190 historical grip-screen rows changed")
    return indexed, _sha256_file(CENTER_X190_SCREEN_PATH)


def _axis_length_and_grip(
    axis_id: str,
    family: str,
    center_rows: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if family == "wj03_outer":
        short = any(
            token in axis_id for token in ("_post_", "_bridge_link_", "_header_")
        )
        if not (short or "_side_" in axis_id or "_bridge_spine_" in axis_id):
            raise ValueError(
                f"{axis_id}: WJ03 stack name does not identify its model class"
            )
        return {
            "hardware_model_class": "six_in_model_127_mm_grip"
            if short
            else "eight_in_model_177p8_mm_grip",
            "modeled_nominal_length_mm": 152.4 if short else 203.2,
            "nominal_wood_grip_mm": 127.0 if short else 177.8,
            "historical_required_underhead_length_screen_mm": None,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "WJ03 compact stack contracts; generic modeled ordinary through-bolt envelope",
        }
    if family == "wj05_backer":
        return {
            "hardware_model_class": "twelve_in_backer_model_270_mm_bearing_span",
            "modeled_nominal_length_mm": 304.8,
            "nominal_wood_grip_mm": 270.0,
            "historical_required_underhead_length_screen_mm": 287.043,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "WJ05 backer/header geometry; 270 mm wood bearing span after 7 mm counterbore",
            "model_checks": {
                "counterbore_depth_mm": 7.0,
                "wood_span_before_counterbore_mm": 277.0,
                "top_washer_count_per_axis": 3,
                "bottom_washer_count_per_axis": 1,
            },
        }
    if family == "wj04_g7":
        return {
            "hardware_model_class": "six_in_model_127_mm_grip",
            "modeled_nominal_length_mm": 152.4,
            "nominal_wood_grip_mm": 127.0,
            "historical_required_underhead_length_screen_mm": None,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "WJ04 G7 provisional 6 in cap-screw model; ordinary-hardware basis remains conditional",
        }
    if family in {"wj06_outer_pair", "top_outer", "bottom_outer"}:
        is_side = "_side_" in axis_id or "/side_" in axis_id
        return {
            "hardware_model_class": "eight_in_model_177p8_mm_grip"
            if is_side
            else "six_in_model_127_mm_grip",
            "modeled_nominal_length_mm": 203.2 if is_side else 152.4,
            "nominal_wood_grip_mm": 177.8 if is_side else 127.0,
            "historical_required_underhead_length_screen_mm": None,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "WJ06-family dimensional envelope; the 8 in F086013 reference is an unselected lead only",
        }
    if family == "wj05_center_x190":
        row = center_rows.get(axis_id)
        if row is None:
            raise ValueError(f"{axis_id}: missing historical center-x190 grip row")
        grip = float(row["wood_grip_mm"])
        screen = float(row["nominal_underhead_length_screen_mm"])
        if (
            row.get("candidate_sku") is not None
            or row.get("capacity_assigned") is not False
        ):
            raise ValueError(
                f"{axis_id}: historical center-x190 row must remain unselected and non-capacity"
            )
        return {
            "hardware_model_class": "center_x190_length_unassigned",
            "modeled_nominal_length_mm": None,
            "nominal_wood_grip_mm": grip,
            "historical_required_underhead_length_screen_mm": screen,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "historical WJ05 under-head stack screen only; not a catalog bolt length",
        }
    if family == "left_service":
        is_side = "/lower_side_" in axis_id or "/upper_side_" in axis_id
        return {
            "hardware_model_class": "eight_in_model_177p8_mm_grip"
            if is_side
            else "six_in_model_127_mm_grip",
            "modeled_nominal_length_mm": 203.2 if is_side else 152.4,
            "nominal_wood_grip_mm": 177.8 if is_side else 127.0,
            "historical_required_underhead_length_screen_mm": None,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "WJ04/WJ06 mirrored left-service provisional stack contract",
        }
    if family in {"top_center", "bottom_center"}:
        return {
            "hardware_model_class": "six_in_model_127_mm_grip",
            "modeled_nominal_length_mm": 152.4,
            "nominal_wood_grip_mm": 127.0,
            "historical_required_underhead_length_screen_mm": None,
            "nominal_length_is_catalog_selection": False,
            "length_basis": "full-stock cleat plus 38.1 mm source rail/principal receiver model",
        }
    raise ValueError(f"{axis_id}: no stack length contract for family {family}")


def _shape_evidence(shape: cq.Shape) -> dict[str, Any]:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
        raise ValueError("candidate stock map contains an invalid solid")
    bounds = shape.BoundingBox()
    return {
        "global_bounds_xyz_mm": [
            round(value, 6)
            for value in (
                bounds.xmin,
                bounds.xmax,
                bounds.ymin,
                bounds.ymax,
                bounds.zmin,
                bounds.zmax,
            )
        ],
        "volume_mm3": round(float(shape.Volume()), 6),
        "shape_sha256": _source_shape_fingerprint(shape),
    }


def _validate_geometry(
    geometry: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    if (
        getattr(geometry, "layout_id", None) != wj24.LAYOUT_ID
        or getattr(geometry, "trial_id", None) != wj24.TRIAL_ID
    ):
        raise ValueError("hardware inventory requires the exact composed WJ24 object")
    if validate_source_binding(geometry.source) != geometry.source_binding:
        raise ValueError("WJ24 source binding changed before BOM report creation")
    current_inventory_bytes = (ROOT / INVENTORY_PATH).read_bytes()
    current_inventory_hash = hashlib.sha256(current_inventory_bytes).hexdigest()
    binding_inventory_hash = getattr(geometry.source_binding, "inventory_sha256", None)
    if (
        current_inventory_hash != geometry.source_inventory_sha256
        or current_inventory_hash != binding_inventory_hash
    ):
        raise ValueError("WJ24 inventory hash no longer matches its source binding")
    canonical_inventory = json.loads(current_inventory_bytes)
    if _plain(geometry.source_inventory) != canonical_inventory:
        raise ValueError(
            "WJ24 in-memory inventory differs from the canonical source inventory"
        )

    inputs = _verified_hash_map(
        geometry.source_inputs_sha256, context="WJ24 hardware inventory"
    )
    flattened: dict[str, str] = {}
    for family, rows in geometry.family_source_fingerprints.items():
        for path, digest in _verified_hash_map(
            rows, context=f"WJ24 family source {family}"
        ).items():
            previous = flattened.get(path)
            if previous is not None and previous != digest:
                raise ValueError(f"WJ24 family source fingerprints conflict at {path}")
            flattened[path] = digest
    if flattened != inputs:
        raise ValueError(
            "WJ24 merged family fingerprints differ from source input pins"
        )

    expected_checks = {
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
    }
    checks = dict(geometry.composition_checks)
    if not expected_checks <= checks.keys() or any(
        not checks[name] for name in expected_checks
    ):
        raise ValueError(
            "WJ24 composition identity or source reconstruction checks are incomplete"
        )
    for false_gate in (
        "complete_static_scene_diagnostic",
        "all_tool_or_access_intersections_clear",
        "complete_joint_acceptance",
        "capacity_established",
        "installation_proven",
        "fabrication_released",
        "structural_released",
    ):
        if checks.get(false_gate) is not False:
            raise ValueError(
                f"WJ24 must retain false diagnostic/release gate {false_gate}"
            )

    target_ids = set(geometry.target_station_ids)
    expected_target_ids = set(wj24.EXPECTED_TARGET_DUTY_IDS)
    if target_ids != expected_target_ids:
        raise ValueError("WJ24 target duty IDs differ from the exact 24-duty contract")
    duties = {
        row["legacy_station_id"]: row
        for row in canonical_inventory.get("legacy_duties", ())
    }
    expected_old_sds = {
        axis["axis_id"]
        for duty_id in target_ids
        for axis in duties[duty_id].get("legacy_sds_axes", ())
        if axis.get("shop_opening_kind") == "sds_wood"
    }
    if (
        len(expected_old_sds) != 144
        or set(geometry.replaced_source_axis_ids) != expected_old_sds
    ):
        raise ValueError(
            "WJ24 source SDS removal IDs differ from the canonical 144-axis set"
        )
    if set(geometry.candidate_bores) != set(wj24.EXPECTED_CANDIDATE_AXIS_IDS):
        raise ValueError("WJ24 candidate bore IDs differ from the exact 104-axis set")
    if set(geometry.candidate_installed_hardware) != set(
        wj24.EXPECTED_CANDIDATE_AXIS_IDS
    ):
        raise ValueError("WJ24 installed hardware axes differ from the exact bore set")
    if set(geometry.raw_candidate_parts) != set(
        wj24.EXPECTED_CANDIDATE_PART_IDS
    ) or set(geometry.finished_candidate_parts) != set(
        wj24.EXPECTED_CANDIDATE_PART_IDS
    ):
        raise ValueError("WJ24 candidate stock parts differ from the exact 28-part set")
    if set(PART_STOCK_BASIS) != set(wj24.EXPECTED_CANDIDATE_PART_IDS):
        raise ValueError("local stock blank schedule does not exactly cover WJ24 parts")
    return canonical_inventory, checks, inputs


def build_wj24_hardware_inventory_report(geometry: Any) -> dict[str, Any]:
    """Build a bounded BOM/stock report from retained WJ24 geometry only."""
    inventory, composition_checks, inputs = _validate_geometry(geometry)
    center_rows, center_screen_hash = _load_center_x190_grip_rows()
    producer_hashes = {
        label: {"path": path, "sha256": _sha256_file(path)}
        for label, path in sorted(wj24.PRODUCER_HASH_PATHS.items())
    }
    producer_hashes["hardware_inventory_producer"] = {
        "path": "scripts/wood_joint_wj24_hardware_inventory.py",
        "sha256": _sha256_file("scripts/wood_joint_wj24_hardware_inventory.py"),
    }
    basis_hashes = {
        path: _sha256_file(path)
        for path in (
            INVENTORY_PATH,
            ORDINARY_HARDWARE_BASIS_PATH,
            HARDWARE_SCHEDULE_AUDIT_PATH,
            BACKER_BASIS_PATH,
            CENTER_X190_SCREEN_PATH,
            *sorted(
                {
                    path
                    for spec in PART_STOCK_BASIS.values()
                    for path in spec["basis_paths"]
                }
            ),
        )
    }
    if basis_hashes[CENTER_X190_SCREEN_PATH] != center_screen_hash:
        raise ValueError(
            "center-x190 grip-screen hash changed during report construction"
        )

    family_trials = dict(geometry.family_trial_ids)
    expected_candidate_axes = set(wj24.EXPECTED_CANDIDATE_AXIS_IDS)
    target_station_ids = dict(wj24.EXPECTED_CANDIDATE_AXIS_STATION_IDS)
    axes: list[dict[str, Any]] = []
    role_counts: Counter[str] = Counter()
    role_schema_counts: Counter[str] = Counter()
    washer_total = 0
    center_grip_counts: Counter[float] = Counter()
    family_counts: Counter[str] = Counter()
    receiver_pair_axes: dict[tuple[str, str], list[str]] = defaultdict(list)
    candidate_axis_incidence: dict[str, list[str]] = defaultdict(list)

    if set(geometry.candidate_installed_hardware) != expected_candidate_axes:
        raise ValueError("WJ24 must carry the exact 104 installed hardware axes")
    for axis_id in sorted(expected_candidate_axes):
        bore = geometry.candidate_bores[axis_id]
        if getattr(bore, "axis_id", None) != axis_id:
            raise ValueError(f"{axis_id}: bore key and identity differ")
        family = str(getattr(bore, "family", ""))
        expected_family = _family_for_axis_id(axis_id)
        if family != expected_family:
            raise ValueError(
                f"{axis_id}: expected family {expected_family}, got {family}"
            )
        if family not in EXPECTED_FAMILY_AXIS_COUNTS:
            raise ValueError(f"{axis_id}: unknown family {family}")
        family_counts[family] += 1
        station_id = getattr(bore, "station_id", None)
        expected_station_id = target_station_ids.get(axis_id)
        if expected_station_id is not None and station_id != expected_station_id:
            raise ValueError(f"{axis_id}: duty binding differs from exact WJ24 layout")
        trial_key = _trial_key(family)
        if (
            trial_key not in family_trials
            or getattr(bore, "trial_id", None) != family_trials[trial_key]
        ):
            raise ValueError(
                f"{axis_id}: family trial ID is not bound to WJ24 composition"
            )
        pair = tuple(getattr(bore, "receiver_ids", ()))
        if len(pair) != 2 or pair[0] == pair[1]:
            raise ValueError(
                f"{axis_id}: bore must preserve its ordered pair of distinct receivers"
            )
        receiver_ids = set(pair)
        known_receivers = set(PART_STOCK_BASIS) | {
            row["part_id"] for row in inventory.get("parts", ())
        }
        if not receiver_ids <= known_receivers:
            raise ValueError(
                f"{axis_id}: candidate bore references an unknown receiver"
            )
        for receiver in pair:
            if receiver in PART_STOCK_BASIS:
                candidate_axis_incidence[receiver].append(axis_id)
        receiver_pair_axes[pair].append(axis_id)

        roles = geometry.candidate_installed_hardware[axis_id]
        expected_roles = (
            BACKER_ROLES if axis_id in top_outer.BACKER_AXIS_IDS else ORDINARY_ROLES
        )
        if set(roles) != expected_roles:
            raise ValueError(
                f"{axis_id}: hardware role map differs from its physical stack schema"
            )
        role_schema = (
            "backer_triple_top_washer"
            if axis_id in top_outer.BACKER_AXIS_IDS
            else "ordinary_two_washer"
        )
        role_schema_counts[role_schema] += 1
        role_counts.update(roles.keys())
        physical_washers = 4 if role_schema == "backer_triple_top_washer" else 2
        washer_total += physical_washers
        hardware_model = _axis_length_and_grip(axis_id, family, center_rows)
        if family == "wj05_center_x190":
            center_grip_counts[float(hardware_model["nominal_wood_grip_mm"])] += 1
        axes.append(
            {
                "axis_id": axis_id,
                "family": family,
                "family_trial_id": bore.trial_id,
                "station_id": station_id,
                "station_binding_status": (
                    "explicit_compositor_station_binding"
                    if expected_station_id is not None
                    else "retained_legacy_bore_has_no_station_id; source duty not inferred here"
                ),
                "ordered_receiver_ids_from_candidate_bore": list(pair),
                "stack_class": hardware_model,
                "installed_cad_role_ids": sorted(roles),
                "cad_role_count": len(roles),
                "physical_washer_count_screen": physical_washers,
                "physical_bolt_count_screen": 1,
                "physical_nut_count_screen": 1,
                "hardware_selection_status": "provisional geometry envelope; no SKU or delivered part selected",
            }
        )

    if dict(family_counts) != EXPECTED_FAMILY_AXIS_COUNTS:
        raise ValueError(
            f"WJ24 family axis counts differ from exact partition: {dict(family_counts)}"
        )
    if role_schema_counts != Counter(
        {"ordinary_two_washer": 100, "backer_triple_top_washer": 4}
    ):
        raise ValueError(
            "WJ24 stack schemas must reconcile as 100 ordinary and four backer stacks"
        )
    if sum(role_counts.values()) != 520:
        raise ValueError(
            "WJ24 physical stack role evidence differs from 520 CAD role shapes"
        )
    if center_grip_counts != Counter({100.915644: 4, 127.0: 8, 167.0: 4}):
        raise ValueError(
            "center-x190 historical grip groups differ from the 16-axis source report"
        )

    actual_inventory_axis_rows = {
        row["axis_id"]: row for row in inventory.get("fixed_panel_kicker_screws", ())
    }
    expected_panel_ids = set(actual_inventory_axis_rows)
    if len(expected_panel_ids) != 66 or set(geometry.fixed_axes) != expected_panel_ids:
        raise ValueError(
            "WJ24 fixed Hillman panel/kicker axis identities differ from inventory"
        )
    redirected = {
        row["axis_id"]: row
        for row in actual_inventory_axis_rows.values()
        if row.get("source_finished_receiver_member")
        != row.get("candidate_finished_receiver_member")
    }
    if set(redirected) != {
        axis_id
        for part_cuts in geometry.purchased_panel_cutters_by_candidate_part.values()
        for axis_id in part_cuts
    }:
        raise ValueError(
            "candidate panel-screw redirects differ from the exact source inventory"
        )
    if set(geometry.purchased_panel_cutters_by_candidate_part) != {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    } or any(
        len(rows) != 2
        for rows in geometry.purchased_panel_cutters_by_candidate_part.values()
    ):
        raise ValueError(
            "each backer must retain exactly two redirected fixed panel cuts"
        )

    source_frame_rows = {
        row["axis_id"]: row for row in inventory.get("starting_frame_bolts", ())
    }
    frame_record_ids = {row.get("axis_id") for row in geometry.frame_bolt_records}
    if len(source_frame_rows) != 12 or frame_record_ids != set(source_frame_rows):
        raise ValueError(
            "the twelve retained frame bolt records differ from canonical source IDs"
        )
    if len(geometry.frame_bolt_shapes) != 72:
        raise ValueError(
            "retained frame bolt geometry must expose 72 shapes including 12 occupancy proxies"
        )
    proxy_ids = {
        name
        for name in geometry.frame_bolt_shapes
        if name.endswith("/source_occupied_axis")
    }
    if len(proxy_ids) != 12:
        raise ValueError(
            "retained frame bolt shape map must classify twelve source-axis proxies"
        )

    fixed_screws = [
        {
            "axis_id": row["axis_id"],
            "panel_member": row.get("panel_member"),
            "source_finished_receiver_member": row.get(
                "source_finished_receiver_member"
            ),
            "candidate_finished_receiver_member": row.get(
                "candidate_finished_receiver_member"
            ),
            "shop_purchased_length_mm": row.get("shop_purchased_length_mm"),
            "source_occupied_length_mm": row.get("source_occupied_length_mm"),
            "source_occupied_diameter_mm": row.get("source_occupied_diameter_mm"),
            "shop_opening_kind": row.get("shop_opening_kind"),
        }
        for row in sorted(
            actual_inventory_axis_rows.values(), key=lambda value: value["axis_id"]
        )
    ]
    screw_lengths = Counter(row["shop_purchased_length_mm"] for row in fixed_screws)

    source_frame_bolts = [
        {
            "axis_id": axis_id,
            "members": list(row.get("members", ())),
            "modeled_nominal_length_mm": row.get("source_nominal_length_mm"),
            "modeled_wood_grip_mm": row.get("source_grip_mm"),
            "occupied_cad_length_mm": row.get("source_occupied_length_mm"),
            "occupied_cad_diameter_mm": row.get("source_occupied_diameter_mm"),
            "installed_role_shape_count": 5,
            "source_occupied_axis_is_proxy": True,
            "actual_fastener_inspected": False,
        }
        for axis_id, row in sorted(source_frame_rows.items())
    ]

    connector_parts: dict[str, dict[str, Any]] = {}
    stock_group_counts: Counter[str] = Counter()
    for part_id, stock in sorted(PART_STOCK_BASIS.items()):
        raw_shape = geometry.raw_candidate_parts[part_id]
        finished_shape = geometry.finished_candidate_parts[part_id]
        panel_cuts = dict(
            geometry.purchased_panel_cutters_by_candidate_part.get(part_id, {})
        )
        cut_ids = sorted(panel_cuts)
        bore_ids = sorted(candidate_axis_incidence.get(part_id, ()))
        if (
            part_id in {"inner_kicker_backer_left", "inner_kicker_backer_right"}
            and len(cut_ids) != 2
        ):
            raise ValueError(f"{part_id}: exact two fixed receiver cuts are required")
        stock_group_counts[stock["stock_group"]] += 1
        connector_parts[part_id] = {
            "stock_group": stock["stock_group"],
            "stock_description_model": stock["stock_description"],
            "stock_blank_dimensions_mm": list(stock["blank_dimensions_mm"]),
            "dimension_axis_order": list(stock["dimension_axis_order"]),
            "grain_axis": stock["grain_axis"],
            "fabrication_operations_model_only": list(stock["fabrication_operations"]),
            "basis_paths": list(stock["basis_paths"]),
            "candidate_bore_axis_ids_from_actual_receiver_records": bore_ids,
            "candidate_bore_axis_count": len(bore_ids),
            "redirected_fixed_panel_cut_ids": cut_ids,
            "raw_candidate_shape": _shape_evidence(raw_shape),
            "finished_candidate_shape": _shape_evidence(finished_shape),
            "delivered_stock_observed": False,
            "cut_or_drill_authorized": False,
        }
    if set(connector_parts) != set(wj24.EXPECTED_CANDIDATE_PART_IDS):
        raise ValueError(
            "connector stock inventory does not cover all 28 composed parts"
        )

    receiver_groups = [
        {
            "ordered_receiver_ids": list(pair),
            "candidate_axis_count": len(axis_ids),
            "candidate_axis_ids": sorted(axis_ids),
            "order_semantics": "preserved from CandidateBore.receiver_ids; no direction inference",
        }
        for pair, axis_ids in sorted(receiver_pair_axes.items())
    ]
    grouped_axis_counts = sum(
        group["candidate_axis_count"] for group in receiver_groups
    )
    if grouped_axis_counts != 104:
        raise ValueError(
            "ordered receiver-pair grouping does not cover all 104 actual bore records"
        )

    length_grip_groups: dict[tuple[Any, Any], list[str]] = defaultdict(list)
    for row in axes:
        data = row["stack_class"]
        key = (data["modeled_nominal_length_mm"], data["nominal_wood_grip_mm"])
        length_grip_groups[key].append(row["axis_id"])
    hardware_groups = [
        {
            "modeled_nominal_length_mm": length,
            "nominal_wood_grip_mm": grip,
            "axis_count": len(axis_ids),
            "axis_ids": sorted(axis_ids),
            "catalog_selection_status": "model class only; no single catalog SKU selected for the group",
        }
        for (length, grip), axis_ids in sorted(
            length_grip_groups.items(),
            key=lambda item: (
                float("inf") if item[0][0] is None else float(item[0][0]),
                float(item[0][1]),
            ),
        )
    ]
    family_histograms = {
        family: dict(
            sorted(
                Counter(
                    row["stack_class"]["nominal_wood_grip_mm"]
                    for row in axes
                    if row["family"] == family
                ).items()
            )
        )
        for family in sorted(EXPECTED_FAMILY_AXIS_COUNTS)
    }

    physical_counts = {
        "new_candidate_bolt_axes": 104,
        "new_candidate_bolts_screen": 104,
        "new_candidate_nuts_screen": 104,
        "new_candidate_washers_screen": washer_total,
        "new_candidate_physical_piece_count_screen_excludes_integral_bolt_heads": 104
        + 104
        + washer_total,
        "installed_candidate_cad_role_shapes": sum(role_counts.values()),
        "candidate_axes_with_two_washer_roles": role_schema_counts[
            "ordinary_two_washer"
        ],
        "candidate_axes_with_one_bottom_and_three_top_washer_equivalents": role_schema_counts[
            "backer_triple_top_washer"
        ],
        "candidate_backer_top_washer_roles_are_envelopes_not_three_separate_cad_roles": 4,
        "retained_starting_frame_bolt_assemblies_separate": 12,
        "retained_frame_bolt_installed_role_shapes_separate": sum(
            int(row.get("installed_component_count", 5))
            for row in geometry.frame_bolt_records
        ),
        "retained_frame_bolt_source_occupied_axis_proxies_separate": len(proxy_ids),
        "fixed_Hillman_panel_kicker_screw_axes_separate": 66,
        "removed_legacy_SDS_axes_not_candidate_BOM_items": 144,
        "candidate_connector_stock_blanks": 28,
    }
    if physical_counts["new_candidate_washers_screen"] != 216:
        raise ValueError("physical washer envelope count must reconcile to 216 pieces")
    if (
        physical_counts[
            "new_candidate_physical_piece_count_screen_excludes_integral_bolt_heads"
        ]
        != 424
    ):
        raise ValueError(
            "new candidate physical item screen must reconcile to 424 pieces"
        )

    source_frame_shape_roles = Counter(
        name.rsplit("/", 1)[-1]
        for name in geometry.frame_bolt_shapes
        if not name.endswith("/source_occupied_axis")
    )

    release = {
        "candidate_hardware_selected": False,
        "supplier_selected": False,
        "unit_prices_entered": False,
        "delivered_hardware_inspected": False,
        "dimensional_fit_established": False,
        "assembly_or_removal_sequence_proven": False,
        "complete_joint_mechanics_coverage": False,
        "cutting_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "candidate_accepted": False,
    }
    return {
        "schema": SCHEMA,
        "layout_id": geometry.layout_id,
        "trial_id": geometry.trial_id,
        "target_duty_ids": sorted(geometry.target_station_ids),
        "status": "provisional_hardware_stock_and_cost_input_inventory_only",
        "claim_boundary": {
            "scope": "Source-bound counts and modeled stock/hardware classes for the complete 24-duty WJ24 composition.",
            "does_not_establish": [
                "selected product or supplier",
                "prices or purchase quantities for received material",
                "delivered bolt length, shank/thread transition, nut engagement, or washer fit",
                "actual timber species, grade, moisture, dimensions, or inspection",
                "cutting, drilling, assembly/removal access, structural capacity, or release",
            ],
            "model_class_lengths_are_not_catalog_selection": True,
            "CAD_role_shapes_are_not_physical_piece_counts": True,
            "receiver_pair_order_is_preserved_without_inferring_bolt_direction": True,
        },
        "source_provenance": {
            "candidate": inventory.get("candidate"),
            "source_commit": inventory.get("source_commit"),
            "source_inventory_sha256": geometry.source_inventory_sha256,
            "source_binding_inventory_sha256": geometry.source_binding.inventory_sha256,
            "source_runtime_module_sha256": dict(
                sorted(geometry.source_binding.runtime_module_sha256.items())
            ),
            "wj24_producer_hashes": producer_hashes,
            "geometry_source_input_hashes_sha256": inputs,
            "family_trial_ids": dict(sorted(family_trials.items())),
            "family_source_fingerprints_sha256": {
                family: dict(sorted(rows.items()))
                for family, rows in sorted(geometry.family_source_fingerprints.items())
            },
            "inventory_basis_source_hashes_sha256": basis_hashes,
            "composition_identity_checks": composition_checks,
        },
        "counts": {
            **physical_counts,
            "candidate_bore_axes": len(geometry.candidate_bores),
            "candidate_hardware_role_shapes_by_role": dict(sorted(role_counts.items())),
            "candidate_hardware_role_schema_counts": dict(
                sorted(role_schema_counts.items())
            ),
            "retained_frame_bolt_shape_role_counts_excluding_axis_proxies": dict(
                sorted(source_frame_shape_roles.items())
            ),
            "fixed_Hillman_shop_purchased_length_counts_mm": {
                str(length): count for length, count in sorted(screw_lengths.items())
            },
            "candidate_axis_family_counts": dict(sorted(family_counts.items())),
        },
        "candidate_hardware_axis_schedule": axes,
        "candidate_hardware_groups_by_modeled_length_and_grip": hardware_groups,
        "candidate_hardware_grip_histogram_by_family_mm": family_histograms,
        "candidate_ordered_receiver_pair_groups": receiver_groups,
        "candidate_connectors": connector_parts,
        "stock_blank_groups": [
            {
                "stock_group": group,
                "connector_blank_count": count,
                "part_ids": sorted(
                    part_id
                    for part_id, spec in PART_STOCK_BASIS.items()
                    if spec["stock_group"] == group
                ),
                "stock_selection_status": "modeled blank class only; actual stock and price unverified",
                "unit_price": None,
            }
            for group, count in sorted(stock_group_counts.items())
        ],
        "separate_retained_frame_bolts": {
            "count": 12,
            "records": source_frame_bolts,
            "shape_map_count": len(geometry.frame_bolt_shapes),
            "installed_component_shape_count": sum(
                int(row.get("installed_component_count", 5))
                for row in geometry.frame_bolt_records
            ),
            "source_occupied_axis_proxies": sorted(proxy_ids),
            "new_candidate_bom_includes_these": False,
            "actual_fasteners_inspected": False,
        },
        "separate_fixed_panel_kicker_screws": {
            "count": 66,
            "owner_selected_policy": "Hillman 42605; retained panel/kicker screw policy for this development lane",
            "axes": fixed_screws,
            "fixed_axis_shapes_are_purchase_instructions": False,
            "purchase_lengths_from_inventory_shop_column_only": True,
            "new_candidate_bom_includes_these": False,
        },
        "removed_legacy_SDS_axes": {
            "count": 144,
            "axis_ids": sorted(geometry.replaced_source_axis_ids),
            "replacement_bolt_BOM_items": False,
        },
        "cost_input_projection": {
            "line_items": [
                {
                    "item_class": "candidate connector stock blanks",
                    "quantity": 28,
                    "unit_price": None,
                    "selected_sku": None,
                },
                {
                    "item_class": "candidate ordinary/backer bolts",
                    "quantity": 104,
                    "unit_price": None,
                    "selected_sku": None,
                },
                {
                    "item_class": "candidate nuts",
                    "quantity": 104,
                    "unit_price": None,
                    "selected_sku": None,
                },
                {
                    "item_class": "candidate washers",
                    "quantity": 216,
                    "unit_price": None,
                    "selected_sku": None,
                },
            ],
            "separate_existing_or_retained_counts": {
                "starting_frame_bolt_arrangements": 12,
                "fixed_Hillman_42605_panel_kicker_axes": 66,
                "removed_legacy_SDS_axes": 144,
            },
            "prices_or_vendor_quotes_used": False,
            "purchase_list": False,
        },
        "dimensional_and_assembly_gaps": {
            "all_new_fasteners": [
                "SKU, supplier, grade, received length and thread transition remain unselected or unmeasured.",
                "The 6 in 25C600HCS5Z basis is a dimensional candidate for some WJ04/WJ06 model groups, not a universal WJ24 selection.",
                "The 8 in F086013 reference is an unselected catalog lead for some WJ06-derived groups; it does not cover all modeled 8 in envelopes by selection.",
                "Nut and washer SKUs, stack thickness at receipt, first full-form thread, full nut engagement and required tip projection remain unverified.",
            ],
            "wj05_backer_four_axis_group": [
                "Four 12 in modeled bolt envelopes have one bottom and three top washer equivalents per axis.",
                "No backer bolt SKU is selected; coupled delivered length/thread transition and full nut engagement remain a receiving condition.",
                "One top_washer CAD shape role represents a washer stack envelope; it is not one physical washer.",
            ],
            "wj05_center_x190_sixteen_axis_group": [
                "Sixteen axes have grip screens of 100.915644, 127, or 167 mm.",
                "The historical 113.133044, 139.2174, and 179.2174 mm under-head screens are not catalog bolt lengths.",
                "No nominal bolt length or SKU is assigned to this group.",
            ],
            "stock_and_cutting": [
                "Twenty-eight connector blanks are modeled; actual dimensions, grade, grain, defects, moisture, yield, and prices are unobserved.",
                "Bevels, crosscuts, counterbores, bore maps, and fixed receiver cuts are model operations, not authorized shop instructions.",
            ],
            "assembly_and_mechanics": [
                "Tool approach, turning/regrip, assembly sequence, removal path, and complete-joint mechanics remain unresolved.",
                "No preload, torque, equal load sharing, capacity, resistance, or acceptance is inferred.",
            ],
        },
        "release": release,
    }
