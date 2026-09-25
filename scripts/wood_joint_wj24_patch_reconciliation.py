"""Compare and export the representative WJ04 wood bodies inside WJ24.

The caller must supply retained WJ16 and complete WJ24 geometry objects from
one serialized CAD session. This module does not materialize families, mesh,
or run a native solver. Exported files are a new WJ24 input bundle and are not
accepted by the older WJ04-pinned mesh worker.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import validate_source_binding
from scripts import wood_joint_wj04_patch_geometry as wj04_patch
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe
from scripts import wood_joint_wj16_compositor as wj16
from scripts import wood_joint_wj24_access_relief_probe as wj24_relief
from scripts import wood_joint_wj24_compositor as wj24

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj24_patch_reconciliation/v1"
OLD_PATCH_DIR = ROOT / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
OLD_PATCH_INVENTORY = OLD_PATCH_DIR / "inventory.json"
OLD_PATCH_HASHES = OLD_PATCH_DIR / "sha256.json"
WJ24_COMPOSITION = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
WJ24_HASHES = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/sha256.json"
OLD_MESH_ARCHIVE_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03"
OLD_MESH_ARCHIVE = OLD_MESH_ARCHIVE_DIR / "complete-mesh-evidence.tar.gz"
OLD_MESH_BUNDLE_CONTENTS = OLD_MESH_ARCHIVE_DIR / "bundle-contents.json"
OLD_MESH_ARCHIVE_HASHES = OLD_MESH_ARCHIVE_DIR / "sha256.json"
OLD_MESH_REPORT_MEMBER = "mesh.json"
FROZEN_OLD_MESH_ARCHIVE_SHA256 = (
    "b4a92cf5d0a76082bce736efe576dda1e8732924d4a19013501727ace7c63a58"
)
FROZEN_OLD_MESH_BUNDLE_CONTENTS_SHA256 = (
    "981b2524dce764796d4f83a72a6a44dda278300377ee04d92a9cf77d453a4456"
)
OLD_MESH_AUDIT = ROOT / "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/parent-audit.json"

BODY_IDS = tuple(wj04_patch.WOOD_BODY_IDS)
HOST_BODY_IDS = frozenset({g7_probe.LOWER_RAIL, g7_probe.UPPER_RAIL, g7_probe.PRINCIPAL})
CLEAT_BODY_IDS = frozenset({g7_probe.LOWER_CLEAT, g7_probe.UPPER_CLEAT})
VOLUME_TOLERANCE_MM3 = 1e-3


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_json(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context}: missing or invalid JSON at {path}") from error
    if not isinstance(value, dict):
        raise TypeError(f"{context}: expected a JSON object at {path}")
    return value


def _read_archived_json_member(
    archive_path: Path,
    bundle_contents_path: Path,
    archive_hashes_path: Path,
    member_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read and verify an indexed JSON member directly from a compressed tar."""
    archive_hashes = _read_json(archive_hashes_path, "archived WJ16 mesh hash index")
    for archive_name, archive_file in (
        ("complete-mesh-evidence.tar.gz", archive_path),
        ("bundle-contents.json", bundle_contents_path),
    ):
        expected_hash = archive_hashes.get(archive_name)
        if not isinstance(expected_hash, str) or _sha256_file(archive_file) != expected_hash:
            raise ValueError(f"archived WJ16 mesh input hash mismatch: {archive_name}")

    contents = _read_json(bundle_contents_path, "archived WJ16 mesh contents index")
    if member_name not in contents:
        raise ValueError(f"archived WJ16 mesh contents index lacks {member_name!r}")
    member_record = contents.get(member_name)
    if not isinstance(member_record, dict):
        raise TypeError(f"archived WJ16 mesh contents index entry must be an object: {member_name!r}")
    expected_size = member_record.get("bytes")
    expected_member_hash = member_record.get("sha256")
    if type(expected_size) is not int:
        raise TypeError(f"archived WJ16 mesh contents index size must be an integer: {member_name!r}")
    if expected_size < 0:
        raise ValueError(f"archived WJ16 mesh contents index has invalid size for {member_name!r}")
    if not isinstance(expected_member_hash, str):
        raise TypeError(f"archived WJ16 mesh contents index hash must be a string: {member_name!r}")

    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            matching = [member for member in archive.getmembers() if member.name == member_name]
            if len(matching) != 1 or not matching[0].isfile():
                raise ValueError(f"archived WJ16 mesh member is missing or ambiguous: {member_name!r}")
            member = matching[0]
            if member.size != expected_size:
                raise ValueError(f"archived WJ16 mesh member size mismatch: {member_name!r}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"archived WJ16 mesh member cannot be read: {member_name!r}")
            member_bytes = stream.read()
    except (OSError, tarfile.TarError) as error:
        raise ValueError("archived WJ16 mesh evidence is not a readable gzip tar") from error

    if len(member_bytes) != expected_size or _sha256_bytes(member_bytes) != expected_member_hash:
        raise ValueError(f"archived WJ16 mesh member hash/size mismatch: {member_name!r}")
    try:
        report = json.loads(member_bytes)
    except json.JSONDecodeError as error:
        raise ValueError(f"archived WJ16 mesh member is not valid JSON: {member_name!r}") from error
    if not isinstance(report, dict):
        raise TypeError(f"archived WJ16 mesh member must be a JSON object: {member_name!r}")
    return report, member_record


def _load_archived_old_mesh_report() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the durable WJ16 mesh report without extracting it to disk."""
    if _sha256_file(OLD_MESH_ARCHIVE) != FROZEN_OLD_MESH_ARCHIVE_SHA256:
        raise ValueError("durable WJ16 mesh evidence archive differs from its frozen source")
    if _sha256_file(OLD_MESH_BUNDLE_CONTENTS) != FROZEN_OLD_MESH_BUNDLE_CONTENTS_SHA256:
        raise ValueError("durable WJ16 mesh contents index differs from its frozen source")
    return _read_archived_json_member(
        OLD_MESH_ARCHIVE,
        OLD_MESH_BUNDLE_CONTENTS,
        OLD_MESH_ARCHIVE_HASHES,
        OLD_MESH_REPORT_MEMBER,
    )


def _shape_solid(shape: Any, context: str) -> cq.Shape:
    if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
        raise ValueError(f"{context}: expected a valid non-null CAD shape")
    solids = shape.Solids()
    if len(solids) != 1 or shape.Volume() <= 0:
        raise ValueError(f"{context}: expected one positive-volume solid")
    return shape


def _delta_solids(shape: cq.Shape, kind: str) -> list[dict[str, Any]]:
    rows = []
    for solid in shape.Solids():
        volume = float(solid.Volume())
        if volume <= 1e-5:
            continue
        box = solid.BoundingBox()
        rows.append(
            {
                "kind": kind,
                "volume_mm3": round(volume, 9),
                "bounds_xyz_mm": [
                    round(float(value), 9)
                    for value in (
                        box.xmin,
                        box.xmax,
                        box.ymin,
                        box.ymax,
                        box.zmin,
                        box.zmax,
                    )
                ],
            }
        )
    return rows


def _body_map(geometry: Any, context: str) -> dict[str, cq.Shape]:
    hosts = getattr(geometry, "finished_hosts", None)
    candidates = getattr(geometry, "finished_candidate_parts", None)
    if not hasattr(hosts, "get") or not hasattr(candidates, "get"):
        raise ValueError(f"{context}: finished host/candidate shape maps are absent")
    result: dict[str, cq.Shape] = {}
    for body_id in BODY_IDS:
        source = hosts if body_id in HOST_BODY_IDS else candidates
        result[body_id] = _shape_solid(source.get(body_id), f"{context}/{body_id}")
    return result


def _candidate_bore_ids(geometry: Any, body_id: str) -> list[str]:
    bores = getattr(geometry, "candidate_bores", None)
    if not hasattr(bores, "items"):
        raise ValueError("composed geometry has no candidate-bore map")
    return sorted(
        str(axis_id)
        for axis_id, bore in bores.items()
        if body_id in tuple(getattr(bore, "receiver_ids", ()))
    )


def _host_cut_record(geometry: Any, body_id: str) -> dict[str, Any] | None:
    if body_id not in HOST_BODY_IDS:
        return None
    native = getattr(geometry, "source_cutters_by_host", {}).get(body_id, {})
    applied = getattr(geometry, "applied_source_cutters_by_host", {}).get(body_id, {})
    purchase = getattr(geometry, "purchased_panel_cutters_by_host", {}).get(body_id, {})
    replaced = set(getattr(geometry, "replaced_source_cutter_ids", ()))
    return {
        "native_source_cutter_ids": sorted(str(key) for key in native),
        "applied_source_cutter_map_ids": sorted(str(key) for key in applied),
        "replaced_source_cutter_ids_on_host": sorted(replaced & set(native)),
        "purchased_panel_cutter_ids": sorted(str(key) for key in purchase),
        "source_reconstruction": dict(
            getattr(geometry, "source_reconstruction", {}).get(body_id, {})
        ),
        "candidate_bore_axis_ids": _candidate_bore_ids(geometry, body_id),
    }


def _validate_old_patch_archive() -> tuple[dict[str, Any], dict[str, str]]:
    index = _read_json(OLD_PATCH_HASHES, "WJ16 representative STEP hash index")
    expected = {"inventory.json"} | {
        f"wood/{body_id}.step" for body_id in BODY_IDS
    }
    if set(index) != expected:
        raise ValueError("old representative STEP bundle no longer has exactly five bodies")
    for relative, digest in index.items():
        path = OLD_PATCH_DIR / relative
        if not path.is_file() or _sha256_file(path) != digest:
            raise ValueError(f"old representative STEP input changed: {relative}")
    inventory = _read_json(OLD_PATCH_INVENTORY, "WJ16 representative STEP inventory")
    if inventory.get("schema") != wj04_patch.SCHEMA:
        raise ValueError("old representative inventory is not the pinned WJ04 patch export")
    if _sha256_file(OLD_PATCH_INVENTORY) != index["inventory.json"]:
        raise ValueError("old representative inventory hash disagrees with its index")
    rows = inventory.get("wood_bodies")
    if not isinstance(rows, list) or {row.get("part_id") for row in rows} != set(BODY_IDS):
        raise ValueError("old representative inventory body IDs differ from WJ04 contract")
    return inventory, {str(key): str(value) for key, value in index.items()}


def _validate_live_compositions(g16: Any, g24: Any) -> dict[str, Any]:
    if getattr(g16, "layout_id", None) != wj16.LAYOUT_ID or getattr(g16, "trial_id", None) != wj16.TRIAL_ID:
        raise ValueError("comparison requires the pinned WJ16 source geometry")
    if getattr(g24, "layout_id", None) != wj24.LAYOUT_ID or getattr(g24, "trial_id", None) != wj24.TRIAL_ID:
        raise ValueError("comparison requires the fixed complete WJ24 composition")
    if getattr(g16, "source", None) is not getattr(g24, "source", None):
        raise ValueError("WJ16 and WJ24 must share the exact retained source object")
    binding = validate_source_binding(g24.source)
    if binding != g16.source_binding or binding != g24.source_binding:
        raise ValueError("WJ16/WJ24 source binding changed before reconciliation")

    frozen_wj16 = wj04_patch._load_frozen_inputs()
    report16 = wj16.composition_report(g16)
    if report16 != frozen_wj16.composition_report:
        raise ValueError("live WJ16 geometry differs from the archived patch source")
    report24 = wj24.composition_report(g24)
    index24 = _read_json(WJ24_HASHES, "current WJ24 report hash index")
    if index24.get("composition.json") != _sha256_file(WJ24_COMPOSITION):
        raise ValueError("current WJ24 composition hash index is stale")
    archived24 = _read_json(WJ24_COMPOSITION, "current WJ24 composition report")
    if report24 != archived24:
        raise ValueError("live WJ24 geometry differs from the selected WJ24 composition report")
    return {
        "source_inventory_sha256": g24.source_inventory_sha256,
        "shared_source_object": True,
        "WJ16": {
            "layout_id": g16.layout_id,
            "trial_id": g16.trial_id,
            "report_path": str(wj04_patch.COMPOSITION_PATH.relative_to(ROOT)),
            "report_sha256": frozen_wj16.composition_sha256,
            "live_report_matches_archive": True,
        },
        "WJ24": {
            "layout_id": g24.layout_id,
            "trial_id": g24.trial_id,
            "report_path": str(WJ24_COMPOSITION.relative_to(ROOT)),
            "report_sha256": _sha256_file(WJ24_COMPOSITION),
            "live_report_matches_archive": True,
        },
    }


def _comparison_row(
    g16: Any,
    g24: Any,
    old_shapes: dict[str, cq.Shape],
    new_shapes: dict[str, cq.Shape],
    old_inventory_rows: dict[str, dict[str, Any]],
    body_id: str,
) -> dict[str, Any]:
    old_shape = old_shapes[body_id]
    new_shape = new_shapes[body_id]
    old_meta = wj04_patch._shape_metadata(old_shape, f"WJ16/{body_id}")
    new_meta = wj04_patch._shape_metadata(new_shape, f"WJ24/{body_id}")
    archived_meta = old_inventory_rows[body_id]["finished_geometry"]
    if archived_meta.get("cad_shape_sha256") != old_meta["cad_shape_sha256"]:
        raise ValueError(f"{body_id}: retained WJ16 solid differs from archived STEP source")
    try:
        removed = old_shape.cut(new_shape)
        added = new_shape.cut(old_shape)
    except Exception as error:
        raise ValueError(f"{body_id}: WJ16/WJ24 symmetric-difference CAD failed") from error
    removed_volume = max(0.0, float(removed.Volume()))
    added_volume = max(0.0, float(added.Volume()))
    difference = removed_volume + added_volume
    cut_delta = None
    if body_id in HOST_BODY_IDS:
        old_cuts = _host_cut_record(g16, body_id)
        new_cuts = _host_cut_record(g24, body_id)
        assert old_cuts is not None and new_cuts is not None
        cut_delta = {
            "native_source_cutter_ids_added": sorted(
                set(new_cuts["native_source_cutter_ids"])
                - set(old_cuts["native_source_cutter_ids"])
            ),
            "native_source_cutter_ids_removed": sorted(
                set(old_cuts["native_source_cutter_ids"])
                - set(new_cuts["native_source_cutter_ids"])
            ),
            "replacement_cutter_ids_added": sorted(
                set(new_cuts["replaced_source_cutter_ids_on_host"])
                - set(old_cuts["replaced_source_cutter_ids_on_host"])
            ),
            "replacement_cutter_ids_no_longer_removed": sorted(
                set(old_cuts["replaced_source_cutter_ids_on_host"])
                - set(new_cuts["replaced_source_cutter_ids_on_host"])
            ),
            "candidate_bore_axis_ids_added": sorted(
                set(new_cuts["candidate_bore_axis_ids"])
                - set(old_cuts["candidate_bore_axis_ids"])
            ),
            "candidate_bore_axis_ids_removed": sorted(
                set(old_cuts["candidate_bore_axis_ids"])
                - set(new_cuts["candidate_bore_axis_ids"])
            ),
            "WJ16": old_cuts,
            "WJ24": new_cuts,
        }
    return {
        "body_id": body_id,
        "geometry_role": (
            "finished_source_host" if body_id in HOST_BODY_IDS else "finished_candidate_part"
        ),
        "WJ16": old_meta,
        "WJ24": new_meta,
        "archived_WJ16_STEP_source_shape_sha256": archived_meta.get("cad_shape_sha256"),
        "removed_from_WJ16_material_mm3": round(removed_volume, 9),
        "added_in_WJ24_material_mm3": round(added_volume, 9),
        "symmetric_difference_mm3": round(difference, 9),
        "same_geometry_within_tolerance": difference <= VOLUME_TOLERANCE_MM3,
        "delta_solids": [
            *_delta_solids(removed, "removed_from_WJ16"),
            *_delta_solids(added, "added_in_WJ24"),
        ],
        "cut_provenance_delta": cut_delta,
    }


def build_wj24_patch_reconciliation_report(g16: Any, g24: Any) -> dict[str, Any]:
    """Compare five archived WJ16 WJ04 bodies with their complete WJ24 bodies.

    CAD booleans run here, so call only in the serialized geometry slot after
    the retained WJ16 and WJ24 objects are available in the same process.
    """
    old_inventory, old_hashes = _validate_old_patch_archive()
    composition = _validate_live_compositions(g16, g24)
    old_shapes = _body_map(g16, "WJ16")
    new_shapes = _body_map(g24, "WJ24")
    old_inventory_rows = {
        str(row["part_id"]): row for row in old_inventory["wood_bodies"]
    }
    if set(old_inventory_rows) != set(BODY_IDS):
        raise ValueError("archived WJ16 representative body inventory is incomplete")
    rows = [
        _comparison_row(
            g16,
            g24,
            old_shapes,
            new_shapes,
            old_inventory_rows,
            body_id,
        )
        for body_id in BODY_IDS
    ]
    mesh_report, mesh_report_member = _load_archived_old_mesh_report()
    mesh_audit = _read_json(OLD_MESH_AUDIT, "archived WJ16 mesh ownership audit")
    return {
        "schema": SCHEMA,
        "status": "source_bound_representative_WJ16_to_WJ24_geometry_comparison_only",
        "source_composition": composition,
        "old_WJ16_patch_bundle": {
            "inventory_path": str(OLD_PATCH_INVENTORY.relative_to(ROOT)),
            "inventory_sha256": old_hashes["inventory.json"],
            "step_sha256": {
                body_id: old_hashes[f"wood/{body_id}.step"] for body_id in BODY_IDS
            },
            "old_mesh_report_archive_path": str(OLD_MESH_ARCHIVE.relative_to(ROOT)),
            "old_mesh_report_member": OLD_MESH_REPORT_MEMBER,
            "old_mesh_report_member_bytes": mesh_report_member["bytes"],
            "old_mesh_report_sha256": mesh_report_member["sha256"],
            "old_mesh_archive_sha256": FROZEN_OLD_MESH_ARCHIVE_SHA256,
            "old_mesh_bundle_contents_path": str(OLD_MESH_BUNDLE_CONTENTS.relative_to(ROOT)),
            "old_mesh_bundle_contents_sha256": FROZEN_OLD_MESH_BUNDLE_CONTENTS_SHA256,
            "old_mesh_input_sha256": mesh_report.get("mesh_input_sha256"),
            "old_mesh_input_bundle_inventory_sha256": mesh_report.get(
                "input_bundle_inventory_sha256"
            ),
            "old_mesh_audit_status": mesh_audit.get("status"),
            "old_mesh_audit_structural_solve_run": mesh_audit.get(
                "structural_solve_run"
            ),
        },
        "body_ids": list(BODY_IDS),
        "body_comparisons": rows,
        "cut_replay_interpretation": {
            "native_source_replay_is_checked_separately_from_candidate_machining": True,
            "replacement_source_cutter_ids_are_explicit_per_body": True,
            "candidate_bores_are_reported_separately_from_native_source_cutters": True,
            "volume_comparison_uses_finished_WJ16_and_finished_WJ24_shapes": True,
        },
        "G7_relief_dependency": {
            "historical_upper_crosscut_body_id": g7_probe.UPPER_CLEAT,
            "historical_upper_crosscut_N_dimension_mm": g7_probe.UPPER_CLEAT_SIZE_MM[2],
            "historical_upper_crosscut_reserve_mm": g7_probe.G7_CLEARANCE_RESERVE_MM,
            "WJ24_LED_connector_body_id": wj24_relief.LED_CONNECTOR_ID,
            "WJ24_LED_id": wj24_relief.LED_ID,
            "WJ24_LED_radial_clearance_scenarios_mm": list(
                wj24_relief.LED_RADIAL_CLEARANCE_SCENARIOS_MM
            ),
            "WJ24_LED_relief_is_in_baseline_composition": False,
            "WJ24_LED_relief_mutates_retained_composition": False,
            "mesh_variant_exported": False,
            "if_a_relief_variant_is_selected": (
                "replace the lower cleat with its named source-bound relief shape, "
                "then repeat STEP identity and geometry reconciliation"
            ),
        },
        "limits": {
            "native_solve_run": False,
            "mesh_generated": False,
            "contact_law_assigned": False,
            "capacity_established": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


def _export_step(shape: cq.Shape, path: Path, body_id: str) -> dict[str, Any]:
    source = wj04_patch._shape_metadata(shape, f"WJ24/{body_id} STEP source")
    cq.exporters.export(shape, str(path))
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"{body_id}: STEP export is missing or empty")
    imported = cq.importers.importStep(str(path)).val()
    readback = wj04_patch._readback_signature(imported)
    wj04_patch._assert_step_identity(source, readback, body_id)
    symmetric_difference = wj04_patch._symmetric_difference_evidence(
        shape, imported, body_id
    )
    return {
        "file": path.name,
        "file_sha256": _sha256_file(path),
        "source_solid": source,
        "step_readback_solid": readback,
        "identity_checks": {
            "solid_count": True,
            "volume": True,
            "centroid": True,
            "bounds": True,
            "symmetric_difference": symmetric_difference,
        },
    }


def export_wj24_representative_patch(
    g16: Any, g24: Any, output_dir: str | Path
) -> dict[str, Any]:
    """Write a new five-body WJ24 STEP bundle without overwriting any path.

    The bundle uses its own schema. The frozen ``fea.wood_joint_patch_mesh``
    worker intentionally rejects it because that worker is pinned to the
    historical WJ16/WJ04 bundle.
    """
    target = Path(output_dir).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"WJ24 representative output already exists: {target}")
    report = build_wj24_patch_reconciliation_report(g16, g24)
    shapes = _body_map(g24, "WJ24 export")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent)))
    try:
        wood_dir = staging / "wood"
        wood_dir.mkdir()
        artifacts = {
            body_id: _export_step(shapes[body_id], wood_dir / f"{body_id}.step", body_id)
            for body_id in BODY_IDS
        }
        report["step_artifacts"] = artifacts
        report_bytes = _json_bytes(report)
        (staging / "reconciliation.json").write_bytes(report_bytes)
        hashes = {
            "reconciliation.json": _sha256_bytes(report_bytes),
            **{
                f"wood/{body_id}.step": artifacts[body_id]["file_sha256"]
                for body_id in BODY_IDS
            },
        }
        hashes_bytes = _json_bytes(hashes)
        (staging / "sha256.json").write_bytes(hashes_bytes)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"WJ24 representative output appeared during export: {target}")
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output_dir": str(target),
        "reconciliation_path": str(target / "reconciliation.json"),
        "reconciliation_sha256": _sha256_file(target / "reconciliation.json"),
        "artifact_hashes": hashes,
        "status": report["status"],
    }
