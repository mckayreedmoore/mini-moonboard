"""Export the source-bound five-body WJ16 ordinary-joint patch inputs.

This adapter consumes an already composed WJ16 object and the frozen right
full-stock mechanics manifest. It exports the five finished timber solids as
separate STEP files and records, but does not export/fuse fastener roles,
rebuild family geometry, mesh, assign a contact law, or run a native solver.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_full_stock_mechanics_contract as mechanics
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj16_compositor as wj16_compositor
from scripts.wood_joint_wj16_compositor import LAYOUT_ID, TRIAL_ID

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj04_patch_geometry/v1"
MANIFEST_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj16-full-stock-mechanics-inputs"
MANIFEST_PATH = MANIFEST_DIR / "mechanics-inputs.json"
MANIFEST_HASHES_PATH = MANIFEST_DIR / "sha256.json"
MANIFEST_EXECUTION_PATH = MANIFEST_DIR / "execution.json"
COMPOSITION_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj16-integrated-static/composition.json"
)
COMPOSITION_HASHES_PATH = COMPOSITION_PATH.with_name("sha256.json")
CONTRACT_SCRIPT_PATH = ROOT / "scripts/wood_joint_wj04_full_stock_mechanics_contract.py"
ADAPTER_SCRIPT_PATH = Path(__file__)
FROZEN_MANIFEST_SHA256 = (
    "f21e99f55da92ea60c950eecc6707fe98ca5df47f4d019f344c16fa06b52caf9"
)
FROZEN_EXECUTION_SHA256 = (
    "64090ead266cb6d793a005629c8f4c55e8a0c661efe3686981e4196cf2b05d8d"
)
FROZEN_COMPOSITION_SHA256 = (
    "c0bc37fdbc364deafcbc86dc04e710d2f5b6809436e560717a97593951f8ebcb"
)
FROZEN_MECHANICS_PRODUCER_SHA256 = (
    "fd8bc1c92efa43f57cb51eff07ece9aa044ca3593892f812706a5e01adff020c"
)
FROZEN_MECHANICS_TEST_SHA256 = (
    "08809397feda0ce7fb1f5f0704bc2e8d0a64f042f560b64f86e9ff51b36ef9ab"
)

WOOD_BODY_IDS = (
    g7_probe.LOWER_RAIL,
    g7_probe.UPPER_RAIL,
    g7_probe.PRINCIPAL,
    g7_probe.LOWER_CLEAT,
    g7_probe.UPPER_CLEAT,
)
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
SOLID_VOLUME_REL_TOLERANCE = 1e-8
SOLID_VOLUME_ABS_TOLERANCE_MM3 = 1e-5
SOLID_POSITION_TOLERANCE_MM = 1e-4
SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 = 1e-3
SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE = 1e-9


@dataclass(frozen=True)
class FrozenInputs:
    mechanics_manifest: dict[str, Any]
    mechanics_manifest_sha256: str
    composition_report: dict[str, Any]
    composition_sha256: str
    execution: dict[str, Any]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_pinned_file(path: Path, expected_sha256: str, context: str) -> bytes:
    if len(expected_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in expected_sha256
    ):
        raise ValueError(f"{context}: invalid pinned SHA-256")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ValueError(f"{context}: pinned file is unavailable: {path}") from error
    if _sha256_bytes(data) != expected_sha256:
        raise ValueError(f"{context}: pinned file hash changed: {path}")
    return data


def _load_frozen_inputs() -> FrozenInputs:
    """Read and cross-check the archived mechanics manifest and WJ16 report."""
    try:
        manifest_hashes = json.loads(MANIFEST_HASHES_PATH.read_text())
        expected_archive_hashes = {
            "execution.json": FROZEN_EXECUTION_SHA256,
            "mechanics-inputs.json": FROZEN_MANIFEST_SHA256,
            "producer.py.snapshot": FROZEN_MECHANICS_PRODUCER_SHA256,
            "tests.py.snapshot": FROZEN_MECHANICS_TEST_SHA256,
        }
        if any(
            manifest_hashes.get(filename) != digest
            for filename, digest in expected_archive_hashes.items()
        ):
            raise ValueError(
                "frozen mechanics archive hash index differs from its pinned values"
            )
        execution_bytes = _read_pinned_file(
            MANIFEST_EXECUTION_PATH,
            manifest_hashes["execution.json"],
            "mechanics execution record",
        )
        manifest_bytes = _read_pinned_file(
            MANIFEST_PATH,
            manifest_hashes["mechanics-inputs.json"],
            "full-stock mechanics manifest",
        )
        _read_pinned_file(
            MANIFEST_DIR / "producer.py.snapshot",
            manifest_hashes["producer.py.snapshot"],
            "frozen mechanics producer snapshot",
        )
        _read_pinned_file(
            MANIFEST_DIR / "tests.py.snapshot",
            manifest_hashes["tests.py.snapshot"],
            "frozen mechanics test snapshot",
        )
        _read_pinned_file(
            CONTRACT_SCRIPT_PATH,
            manifest_hashes["producer.py.snapshot"],
            "live mechanics producer",
        )
        execution = json.loads(execution_bytes)
        mechanics_manifest = json.loads(manifest_bytes)
        composition_pin = execution["input_archives"]["wj16_composition"]
        if composition_pin["path"] != str(COMPOSITION_PATH.relative_to(ROOT)):
            raise ValueError(
                "mechanics manifest references an unexpected WJ16 composition"
            )
        if composition_pin["sha256"] != FROZEN_COMPOSITION_SHA256:
            raise ValueError(
                "mechanics manifest WJ16 composition hash differs from its frozen pin"
            )
        composition_hashes = json.loads(COMPOSITION_HASHES_PATH.read_text())
        composition_bytes = _read_pinned_file(
            COMPOSITION_PATH,
            composition_pin["sha256"],
            "archived WJ16 composition",
        )
        if composition_hashes.get("composition.json") != composition_pin["sha256"]:
            raise ValueError(
                "WJ16 composition archive hash record disagrees with mechanics execution"
            )
        composition_report = json.loads(composition_bytes)
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("frozen WJ16 mechanics input archive is incomplete") from error

    if mechanics_manifest.get("schema") != mechanics.SCHEMA:
        raise ValueError("frozen mechanics manifest schema changed")
    if mechanics_manifest.get("status") != "bounded_mechanics_inputs_only":
        raise ValueError("frozen mechanics manifest is not the bounded input report")
    if execution.get("execution") != (
        "build_mechanics_contract(g16) on the retained WJ16 composed object; "
        "no family rebuild or native solve"
    ):
        raise ValueError(
            "mechanics execution provenance differs from the retained WJ16 contract"
        )
    return FrozenInputs(
        mechanics_manifest=mechanics_manifest,
        mechanics_manifest_sha256=_sha256_bytes(manifest_bytes),
        composition_report=composition_report,
        composition_sha256=_sha256_bytes(composition_bytes),
        execution=execution,
    )


def _vec3(value: Any, context: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: expected a three-component vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected a finite three-component vector")
    return result  # type: ignore[return-value]


def _shape_metadata(shape: Any, context: str) -> dict[str, Any]:
    if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
        raise ValueError(f"{context}: missing or invalid composed CAD shape")
    solids = shape.Solids()
    volume = float(shape.Volume())
    if len(solids) != 1 or not math.isfinite(volume) or volume <= 0:
        raise ValueError(f"{context}: expected one valid positive-volume solid")
    box = shape.BoundingBox()
    centroid = _vec3(shape.Center().toTuple(), f"{context} centroid")
    bounds = [
        float(box.xmin),
        float(box.xmax),
        float(box.ymin),
        float(box.ymax),
        float(box.zmin),
        float(box.zmax),
    ]
    if not all(math.isfinite(value) for value in bounds):
        raise ValueError(f"{context}: non-finite solid bounds")
    return {
        "solid_count": 1,
        "volume_mm3": round(volume, 9),
        "centroid_global_xyz_mm": [round(value, 9) for value in centroid],
        "bounds_xyz_mm": [round(value, 9) for value in bounds],
        "cad_shape_sha256": _source_shape_fingerprint(shape),
    }


def _source_rows(inventory: Any) -> dict[str, dict[str, Any]]:
    rows = mechanics._inventory_rows(inventory)
    return rows


def _grain_frame(
    part_id: str, source_rows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if part_id in mechanics.CLEAT_DATUMS:
        origin, axes = mechanics._cleat_member_frame(part_id)
        grain_name = "N"
        basis_source = "pinned WJ04 full-stock G7 cleat datum and X/T/N frame"
    else:
        row = source_rows.get(part_id)
        if row is None:
            raise ValueError(
                f"{part_id}: no canonical source inventory row for grain frame"
            )
        origin, axes = mechanics._source_frame(row)
        grain = mechanics._unit(row.get("grain_axis_global_xyz", ()))
        grain_name = max(axes, key=lambda name: abs(mechanics._dot(axes[name], grain)))
        if abs(mechanics._dot(axes[grain_name], grain)) < 1 - 1e-7:
            raise ValueError(
                f"{part_id}: explicit source grain is not aligned to its local frame"
            )
        basis_source = (
            "canonical source-inventory local transform, axes, and grain vector"
        )
    grain_global = axes[grain_name]
    return {
        "frame_origin_global_xyz_mm": [round(value, 12) for value in origin],
        "local_axes_global_xyz": {
            name: [round(value, 12) for value in axes[name]] for name in ("X", "T", "N")
        },
        "grain_axis_local_name": grain_name,
        "grain_axis_global_xyz": [round(value, 12) for value in grain_global],
        "basis_source": basis_source,
    }


def _axis_id(stack_id: str) -> str:
    return f"{mechanics.FAMILY}/{g7_probe.TRIAL_ID}/{stack_id}"


def _expected_body_shapes(geometry: Any) -> dict[str, tuple[str, cq.Shape]]:
    finished_hosts = getattr(geometry, "finished_hosts", None)
    finished_candidates = getattr(geometry, "finished_candidate_parts", None)
    if not hasattr(finished_hosts, "get") or not hasattr(finished_candidates, "get"):
        raise ValueError("WJ16 composed source/candidate solid maps are unavailable")
    rows: dict[str, tuple[str, cq.Shape]] = {}
    for part_id in WOOD_BODY_IDS:
        if part_id in mechanics.CLEAT_DATUMS:
            shape = finished_candidates.get(part_id)
            role = "finished_candidate_part"
        else:
            shape = finished_hosts.get(part_id)
            role = "finished_source_host"
        _shape_metadata(shape, f"finished WJ16 wood body {part_id}")
        rows[part_id] = (role, shape)
    if len(rows) != 5 or set(rows) != set(WOOD_BODY_IDS):
        raise ValueError(
            "WJ04 patch must bind exactly five unique finished wood bodies"
        )
    return rows


def _validate_manifest_and_geometry(
    geometry: Any, manifest: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if getattr(geometry, "layout_id", None) != LAYOUT_ID:
        raise ValueError("patch export requires the fixed WJ16 layout")
    if getattr(geometry, "trial_id", None) != TRIAL_ID:
        raise ValueError("patch export requires the retained WJ16 trial")
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("patch export requires the unaccepted WJ16 hypothesis status")
    composition = manifest.get("composition", {})
    if composition.get("trial_id") != geometry.trial_id:
        raise ValueError(
            "mechanics manifest is bound to a different WJ16 composition trial"
        )
    if composition.get("source_inventory_sha256") != getattr(
        geometry, "source_inventory_sha256", None
    ):
        raise ValueError(
            "mechanics manifest inventory hash differs from composed geometry"
        )
    family_trials = getattr(geometry, "family_trial_ids", {})
    if family_trials.get(mechanics.FAMILY) != composition.get(
        "right_rail_family_trial_id"
    ):
        raise ValueError(
            "mechanics manifest right G7 trial differs from composed geometry"
        )
    if composition.get("right_rail_family_trial_id") != g7_probe.TRIAL_ID:
        raise ValueError("mechanics manifest does not bind the pinned G7 family trial")

    specs = tuple(g7_probe.STACK_SPECS)
    if len(specs) != 8 or len({spec.stack_id for spec in specs}) != 8:
        raise ValueError(
            "pinned G7 producer must define exactly eight physical stack specs"
        )
    expected_axes = {_axis_id(spec.stack_id) for spec in specs}
    bores = getattr(geometry, "candidate_bores", {})
    hardware = getattr(geometry, "candidate_installed_hardware", {})
    if not hasattr(bores, "keys") or not hasattr(hardware, "keys"):
        raise ValueError("WJ16 composed bolt-axis/role maps are unavailable")
    if {
        axis_id
        for axis_id, bore in bores.items()
        if getattr(bore, "family", None) == mechanics.FAMILY
    } != expected_axes:
        raise ValueError(
            "composed right G7 bore IDs differ from the exact eight physical bolts"
        )
    if {
        axis_id for axis_id in hardware if axis_id.startswith(f"{mechanics.FAMILY}/")
    } != expected_axes:
        raise ValueError(
            "composed right G7 hardware IDs differ from the exact eight physical bolts"
        )
    if len(manifest.get("physical_bolts", ())) != 8:
        raise ValueError(
            "frozen mechanics manifest must contain exactly eight physical bolts"
        )
    if len(manifest.get("physical_interfaces", ())) != 4:
        raise ValueError(
            "frozen mechanics manifest must contain exactly four interfaces"
        )
    physical_inventory = manifest.get("physical_inventory", {})
    if physical_inventory != {
        "ordinary_physical_bolts": 8,
        "modeled_component_shapes_for_these_bolts": 40,
        "physical_interfaces": 4,
        "scope_does_not_cover": physical_inventory.get("scope_does_not_cover"),
    } or not physical_inventory.get("scope_does_not_cover"):
        raise ValueError("frozen physical inventory counts/limits changed")

    bolt_rows = {row.get("physical_bolt_id"): row for row in manifest["physical_bolts"]}
    if len(bolt_rows) != 8 or set(bolt_rows) != expected_axes:
        raise ValueError(
            "manifest physical bolt IDs differ from the exact eight-stack family"
        )
    spec_by_axis = {_axis_id(spec.stack_id): spec for spec in specs}
    for axis_id in sorted(expected_axes):
        spec = spec_by_axis[axis_id]
        bore = bores[axis_id]
        if (
            getattr(bore, "axis_id", None) != axis_id
            or getattr(bore, "family", None) != mechanics.FAMILY
            or getattr(bore, "trial_id", None) != g7_probe.TRIAL_ID
            or tuple(getattr(bore, "receiver_ids", ()))
            != tuple(member_id for member_id, _thickness in spec.layers)
            or (
                getattr(bore, "station_id", None) is not None
                and bore.station_id != spec.station_id
            )
        ):
            raise ValueError(
                f"{axis_id}: composed bore identity or ordered receivers changed"
            )
        row = bolt_rows[axis_id]
        expected_receivers = [
            {"member_id": member_id, "wood_thickness_mm": float(thickness)}
            for member_id, thickness in spec.layers
        ]
        if (
            row.get("stack_spec_id") != spec.stack_id
            or row.get("station_id") != spec.station_id
            or row.get("interface_id") != spec.interface_id
            or row.get("receivers_head_to_nut") != expected_receivers
        ):
            raise ValueError(
                f"{axis_id}: manifest stack spec or ordered receiver pair changed"
            )
        roles = hardware[axis_id]
        if not hasattr(roles, "keys") or set(roles) != HARDWARE_ROLES:
            raise ValueError(
                f"{axis_id}: expected exactly five distinct CAD component roles"
            )
        for role, shape in roles.items():
            _shape_metadata(shape, f"{axis_id}/{role}")
    if sum(len(hardware[axis_id]) for axis_id in expected_axes) != 40:
        raise ValueError(
            "WJ04 patch must retain forty CAD component roles across eight bolts"
        )

    interface_by_id = {
        row.get("interface_id"): row for row in manifest["physical_interfaces"]
    }
    expected_interface_rows: dict[str, list[str]] = {}
    for spec in specs:
        interface_id = f"{spec.station_id}__{spec.interface_id}"
        expected_interface_rows.setdefault(interface_id, []).append(
            _axis_id(spec.stack_id)
        )
    if set(interface_by_id) != set(expected_interface_rows):
        raise ValueError(
            "manifest interface IDs differ from the four pinned wood interfaces"
        )
    for interface_id, axis_ids in expected_interface_rows.items():
        row = interface_by_id[interface_id]
        expected_stack_ids = [spec_by_axis[axis_id].stack_id for axis_id in axis_ids]
        expected_members = [
            member_id for member_id, _thickness in spec_by_axis[axis_ids[0]].layers
        ]
        if (
            row.get("family_stack_ids") != expected_stack_ids
            or row.get("members_head_to_nut") != expected_members
            or len(axis_ids) != 2
        ):
            raise ValueError(
                f"{interface_id}: manifest interface bolt/member binding changed"
            )
    return spec_by_axis, interface_by_id


def _cut_feature_record(geometry: Any, part_id: str) -> dict[str, Any]:
    if part_id not in mechanics.CLEAT_DATUMS:
        reconstruction = getattr(geometry, "source_reconstruction", {}).get(part_id)
        if reconstruction is None:
            raise ValueError(f"{part_id}: source reconstruction evidence is absent")
        return {
            "native_source_cut_ids": sorted(
                getattr(geometry, "source_cutters_by_host", {}).get(part_id, {})
            ),
            "applied_candidate_cut_ids": sorted(
                getattr(geometry, "applied_source_cutters_by_host", {}).get(part_id, {})
            ),
            "purchased_panel_receiver_axis_ids": sorted(
                getattr(geometry, "purchased_panel_cutters_by_host", {}).get(
                    part_id, {}
                )
            ),
            "source_reconstruction": dict(reconstruction),
        }
    receiver_axes = sorted(
        axis_id
        for axis_id, bore in geometry.candidate_bores.items()
        if part_id in tuple(getattr(bore, "receiver_ids", ()))
        and getattr(bore, "family", None) == mechanics.FAMILY
    )
    panel_cuts = getattr(geometry, "purchased_panel_cutters_by_candidate_part", {}).get(
        part_id, {}
    )
    record: dict[str, Any] = {
        "right_g7_candidate_bore_axis_ids": receiver_axes,
        "purchased_panel_receiver_axis_ids": sorted(panel_cuts),
        "producer_trial_id": g7_probe.TRIAL_ID,
    }
    if part_id == g7_probe.UPPER_CLEAT:
        record["declared_crosscut"] = {
            "nominal_N_dimension_mm": g7_probe.UPPER_CLEAT_SIZE_MM[2],
            "source": "pinned upper G7 full-stock producer; dimension/keepout input only",
        }
    return record


def _vector_close(left: list[float], right: tuple[float, float, float]) -> bool:
    return len(left) == 3 and all(
        math.isclose(
            float(a), float(b), rel_tol=0.0, abs_tol=SOLID_POSITION_TOLERANCE_MM
        )
        for a, b in zip(left, right, strict=True)
    )


def _readback_signature(shape: cq.Shape) -> dict[str, Any]:
    return _shape_metadata(shape, "STEP round-trip solid")


def _assert_step_identity(
    source: dict[str, Any], readback: dict[str, Any], context: str
) -> None:
    if readback["solid_count"] != 1:
        raise ValueError(f"{context}: STEP round-trip changed solid count")
    if not math.isclose(
        source["volume_mm3"],
        readback["volume_mm3"],
        rel_tol=SOLID_VOLUME_REL_TOLERANCE,
        abs_tol=SOLID_VOLUME_ABS_TOLERANCE_MM3,
    ):
        raise ValueError(f"{context}: STEP round-trip volume differs")
    if not _vector_close(
        source["centroid_global_xyz_mm"], tuple(readback["centroid_global_xyz_mm"])
    ):
        raise ValueError(f"{context}: STEP round-trip centroid differs")
    if len(source["bounds_xyz_mm"]) != 6 or any(
        not math.isclose(
            float(a), float(b), rel_tol=0.0, abs_tol=SOLID_POSITION_TOLERANCE_MM
        )
        for a, b in zip(source["bounds_xyz_mm"], readback["bounds_xyz_mm"], strict=True)
    ):
        raise ValueError(f"{context}: STEP round-trip bounds differ")


def _symmetric_difference_evidence(
    source: cq.Shape, readback: cq.Shape, context: str
) -> dict[str, Any]:
    """Compare occupied CAD volumes in both directions, independent of face order."""
    try:
        source_only = max(0.0, float(source.cut(readback).Volume()))
        step_only = max(0.0, float(readback.cut(source).Volume()))
    except Exception as error:
        raise ValueError(
            f"{context}: STEP/source solid symmetric difference failed"
        ) from error
    symmetric_difference = source_only + step_only
    source_volume = float(source.Volume())
    step_volume = float(readback.Volume())
    allowed = SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 + (
        SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE * max(source_volume, step_volume)
    )
    if not all(
        math.isfinite(value)
        for value in (source_only, step_only, symmetric_difference, allowed)
    ):
        raise ValueError(f"{context}: non-finite STEP/source symmetric difference")
    evidence = {
        "source_only_volume_mm3": round(source_only, 12),
        "step_only_volume_mm3": round(step_only, 12),
        "symmetric_difference_volume_mm3": round(symmetric_difference, 12),
        "absolute_tolerance_mm3": SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3,
        "relative_tolerance": SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE,
        "allowed_volume_difference_mm3": round(allowed, 12),
        "passed": symmetric_difference <= allowed,
    }
    if not evidence["passed"]:
        raise ValueError(
            f"{context}: STEP/source solid symmetric difference "
            f"{symmetric_difference:.12g} mm3 exceeds {allowed:.12g} mm3"
        )
    return evidence


def _build_inventory(
    geometry: Any,
    manifest: dict[str, Any],
    *,
    manifest_sha256: str,
    composition_sha256: str,
    composition_report: dict[str, Any],
    expected_composition_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, cq.Shape]]:
    if composition_report != expected_composition_report:
        raise ValueError("live WJ16 composition report differs from its frozen archive")
    spec_by_axis, interface_by_id = _validate_manifest_and_geometry(geometry, manifest)
    shapes = _expected_body_shapes(geometry)
    source_rows = _source_rows(getattr(geometry, "source_inventory", None))
    body_records = []
    for part_id in WOOD_BODY_IDS:
        role, shape = shapes[part_id]
        source_metadata = _shape_metadata(shape, f"{part_id} finished wood")
        body_records.append(
            {
                "part_id": part_id,
                "geometry_role": role,
                "finished_geometry": source_metadata,
                "grain_frame": _grain_frame(part_id, source_rows),
                "cut_feature_metadata": _cut_feature_record(geometry, part_id),
                "bound_interface_ids": sorted(
                    interface_id
                    for interface_id, row in interface_by_id.items()
                    if part_id in row.get("members_head_to_nut", ())
                ),
            }
        )

    bolt_records = []
    hardware = geometry.candidate_installed_hardware
    bores = geometry.candidate_bores
    for manifest_row in manifest["physical_bolts"]:
        axis_id = manifest_row["physical_bolt_id"]
        roles = hardware[axis_id]
        role_records = [
            {
                "role": role,
                "cad_shape": _shape_metadata(roles[role], f"{axis_id}/{role}"),
            }
            for role in sorted(HARDWARE_ROLES)
        ]
        bore_record = _shape_metadata(bores[axis_id].shape, f"{axis_id} occupancy bore")
        spec = spec_by_axis[axis_id]
        bolt_records.append(
            {
                "physical_bolt_id": axis_id,
                "stack_spec_id": spec.stack_id,
                "station_id": spec.station_id,
                "interface_id": f"{spec.station_id}__{spec.interface_id}",
                "world_axis_origin_xyz_mm": manifest_row["world_axis_origin_xyz_mm"],
                "world_axis_origin_datum": manifest_row["world_axis_origin_datum"],
                "world_axis_direction_head_to_nut": manifest_row[
                    "world_axis_direction_head_to_nut"
                ],
                "receivers_head_to_nut": manifest_row["receivers_head_to_nut"],
                "wood_grip_mm": manifest_row["wood_grip_mm"],
                "single_wood_shear_plane_global_xyz_mm": manifest_row[
                    "single_wood_shear_plane_global_xyz_mm"
                ],
                "hardware_status": manifest_row["hardware"]["selection_status"],
                "provisional_hardware": manifest_row["hardware"],
                "composed_occupancy_bore": bore_record,
                "physical_hardware_roles": role_records,
                "role_count": len(role_records),
                "role_shapes_are_fused": False,
            }
        )

    interface_records = []
    for interface_id, manifest_row in sorted(interface_by_id.items()):
        interface_records.append(
            {
                "interface_id": interface_id,
                "physical_bolt_ids": [
                    _axis_id(stack_id) for stack_id in manifest_row["family_stack_ids"]
                ],
                "members_head_to_nut": manifest_row["members_head_to_nut"],
                "source_host_face": manifest_row["source_host_face"],
                "candidate_cleat_face": manifest_row["candidate_cleat_face"],
                "shear_plane_datum": manifest_row["shear_plane_datum"],
                "finite_paired_overlap_surface": {
                    "status": "unresolved_not_extracted",
                    "reason": (
                        "The frozen manifest authenticates opposed planar datums and cleat face area, "
                        "but this export step does not compute a finite OCC face intersection, gap, "
                        "or active pressure patch."
                    ),
                },
                "contact_law_assigned": False,
            }
        )

    inventory = {
        "schema": SCHEMA,
        "status": "source_bound_finished_geometry_export_inputs_only",
        "composition": {
            "layout_id": geometry.layout_id,
            "trial_id": geometry.trial_id,
            "status": geometry.status,
            "source_inventory_sha256": geometry.source_inventory_sha256,
            "mechanics_manifest_sha256": manifest_sha256,
            "wj16_composition_report_sha256": composition_sha256,
            "right_g7_family_trial_id": g7_probe.TRIAL_ID,
            "right_g7_source_fingerprints_sha256": manifest["composition"][
                "right_rail_source_fingerprints_sha256"
            ],
            "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
            "adapter_source_sha256": _sha256_file(ADAPTER_SCRIPT_PATH),
            "live_composition_report_matches_archive": True,
        },
        "scope": {
            "finished_wood_bodies": 5,
            "physical_bolts": 8,
            "modeled_hardware_roles": 40,
            "wood_interfaces": 4,
            "step_files_exported": "five independent wood solids only",
            "native_solve_run": False,
            "mesh_generated": False,
            "contact_law_assigned": False,
            "capacity_or_release_claim": False,
        },
        "step_solid_identity_method": {
            "comparison": "source-only plus STEP-only CAD solid symmetric-difference volume",
            "absolute_tolerance_mm3": SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3,
            "relative_tolerance": SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE,
            "allowed_difference_formula": (
                "absolute_tolerance + relative_tolerance * max(source, STEP solid volumes)"
            ),
            "supplementary_checks": (
                "solid count, volume, centroid, and bounds; no face ordinal matching"
            ),
        },
        "wood_bodies": body_records,
        "physical_bolts": bolt_records,
        "wood_interfaces": interface_records,
        "limitations": [
            "The STEP files are exports of already composed nominal CAD solids, not inspected or received lumber.",
            "Hardware-role metadata are separate CAD shapes; they are not fused into one bolt and are not STEP-exported here.",
            "Finite paired contact overlap, surface gap, active patch, contact law, mesh, response, and resistance remain unresolved.",
            "Bore occupancy cylinders are analysis geometry and are not drill instructions or delivered hardware measurements.",
        ],
    }
    return inventory, {part_id: shape for part_id, (_role, shape) in shapes.items()}


def _export_one_body(shape: cq.Shape, path: Path, part_id: str) -> dict[str, Any]:
    source = _shape_metadata(shape, f"{part_id} source solid")
    cq.exporters.export(shape, str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{part_id}: STEP exporter did not create a nonempty file")
    imported = cq.importers.importStep(str(path)).val()
    readback = _readback_signature(imported)
    _assert_step_identity(source, readback, part_id)
    symmetric_difference = _symmetric_difference_evidence(shape, imported, part_id)
    return {
        "file": str(path.name),
        "file_sha256": _sha256_file(path),
        "source_solid": source,
        "step_readback_solid": readback,
        "identity_checks": {
            "solid_count": True,
            "volume": True,
            "centroid": True,
            "bounds": True,
            "face_ordinal_used": False,
            "symmetric_difference": symmetric_difference,
        },
    }


def export_wj04_patch(geometry: Any, output_dir: str | Path) -> dict[str, Any]:
    """Write a non-overwriting five-body STEP bundle from retained WJ16 geometry.

    ``output_dir`` must not already exist. The function only reads the supplied
    composed object, validates it against archived source reports, and exports
    its five finished wood solids; it never invokes a family materializer.
    """
    target = Path(output_dir).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"patch export destination already exists: {target}")
    frozen = _load_frozen_inputs()
    live_mechanics = mechanics.build_mechanics_contract(geometry)
    if live_mechanics != frozen.mechanics_manifest:
        raise ValueError(
            "retained WJ16 geometry differs from the frozen mechanics manifest"
        )
    live_composition = wj16_compositor.composition_report(geometry)
    if live_composition != frozen.composition_report:
        raise ValueError(
            "retained WJ16 geometry differs from the archived composition report"
        )
    inventory, body_shapes = _build_inventory(
        geometry,
        frozen.mechanics_manifest,
        manifest_sha256=frozen.mechanics_manifest_sha256,
        composition_sha256=frozen.composition_sha256,
        composition_report=live_composition,
        expected_composition_report=frozen.composition_report,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent))
    )
    try:
        wood_dir = staging / "wood"
        wood_dir.mkdir()
        step_artifacts: dict[str, dict[str, Any]] = {}
        for part_id in WOOD_BODY_IDS:
            step_artifacts[part_id] = _export_one_body(
                body_shapes[part_id], wood_dir / f"{part_id}.step", part_id
            )
        inventory["step_artifacts"] = step_artifacts
        inventory_bytes = _json_bytes(inventory)
        (staging / "inventory.json").write_bytes(inventory_bytes)
        artifact_hashes = {
            "inventory.json": _sha256_bytes(inventory_bytes),
            **{
                f"wood/{part_id}.step": step_artifacts[part_id]["file_sha256"]
                for part_id in WOOD_BODY_IDS
            },
        }
        hash_bytes = _json_bytes(artifact_hashes)
        (staging / "sha256.json").write_bytes(hash_bytes)
        if target.exists() or target.is_symlink():
            raise FileExistsError(
                f"patch export destination appeared during export: {target}"
            )
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output_dir": str(target),
        "inventory_path": str(target / "inventory.json"),
        "inventory_sha256": _sha256_file(target / "inventory.json"),
        "artifact_hashes": artifact_hashes,
        "status": inventory["status"],
    }
