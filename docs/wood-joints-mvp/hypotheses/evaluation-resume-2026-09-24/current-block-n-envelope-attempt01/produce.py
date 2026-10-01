#!/usr/bin/env python3
"""Source-bound canonical-N block-body projection diagnostic.

This reports exact STEP-body projections in the frozen station direction. It
does not select a station datum, classify the 139.7 mm envelope, or include
hardware or tools.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.gp import gp_Trsf

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "block-n-envelope.json"
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
FRAME_MAP_PATH = BASE + "current-block-material-frame-map-attempt02/material-frame-map.json"
SOLIDS_PATH = BASE + "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
SOLIDS_DIR = BASE + "current-full-frame-member-solids-attempt01/bundle"
INPUT_MANIFEST_PATH = BASE + "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json"
SOURCE_INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
REVIEW_SOURCE_PATHS = (
    "docs/wood-joints-mvp/decision-log.md",
    "docs/wood-joints-mvp/plan.md",
    "docs/wood-joints-mvp/criteria.json",
    "docs/wood-joints-mvp/current-criteria-coverage.md",
    "docs/wood-joints-mvp/orchestration-handoff.md",
    "docs/wood-joints-mvp/outer-node-result.md",
)

EXPECTED_FRAME_MAP_SHA256 = "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480"
EXPECTED_FRAME_MAP_RECORD_SHA256 = "4d62c18e9717dfb21b2ff00e36668db7393c3bc83016053903bb962a24c18b70"
EXPECTED_SOLIDS_SHA256 = "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420"
EXPECTED_SOLIDS_ARTIFACT_SHA256 = "d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc"
EXPECTED_MEMBER_BUNDLE_SHA256 = "590e3d8ffc6a013ad10436def028b54b3c855688398c4bf9b30c460800fc987c"
EXPECTED_INPUT_MANIFEST_SHA256 = "21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_CANDIDATE = "compact-floor-flush-development"
LIMIT_MM = 139.7
COMPARISON_TOLERANCE_MM = 1e-6
MEMBER_BOUNDS_TOLERANCE_MM = 1e-5
MEMBER_VOLUME_TOLERANCE_MM3 = 1e-3


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(payload)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


def rounded(value: float, places: int = 9) -> float:
    result = round(float(value), places)
    return 0.0 if result == 0.0 else result


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def vector_norm(value: list[float]) -> float:
    return math.sqrt(dot(value, value))


def canonical_station_frame(manifest: dict[str, Any]) -> dict[str, list[float]]:
    coordinate_contract = manifest.get("coordinate_and_unit_contract")
    if not isinstance(coordinate_contract, dict):
        raise ValueError("Input manifest lacks its coordinate contract")
    preserved = coordinate_contract.get("preserved_source_frame")
    if not isinstance(preserved, dict):
        raise ValueError("Input manifest lacks its preserved source frame")
    columns = preserved.get("basis_columns_global_xyz")
    if not isinstance(columns, list) or len(columns) != 3:
        raise ValueError("Input manifest lacks three canonical station-frame axes")
    axes = {name: [float(x) for x in columns[index]] for index, name in enumerate(("X", "T", "N"))}
    if any(len(value) != 3 or not all(math.isfinite(x) for x in value) for value in axes.values()):
        raise ValueError("Canonical station-frame axes must be finite three-vectors")
    expected_n = [0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0))]
    if max(abs(axes["N"][index] - expected_n[index]) for index in range(3)) > 1e-12:
        raise ValueError("Canonical station N differs from the frozen handoff direction")
    for name, axis in axes.items():
        if abs(vector_norm(axis) - 1.0) > 1e-12:
            raise ValueError(f"Canonical station {name} is not unit length")
    if any(abs(dot(axes[a], axes[b])) > 1e-12 for a, b in (("X", "T"), ("X", "N"), ("T", "N"))):
        raise ValueError("Canonical station axes are not mutually orthogonal")
    handed = [
        axes["X"][1] * axes["T"][2] - axes["X"][2] * axes["T"][1],
        axes["X"][2] * axes["T"][0] - axes["X"][0] * axes["T"][2],
        axes["X"][0] * axes["T"][1] - axes["X"][1] * axes["T"][0],
    ]
    if max(abs(handed[i] - axes["N"][i]) for i in range(3)) > 1e-12:
        raise ValueError("Canonical station frame is not right-handed")
    return axes


def check_record_digest(record: dict[str, Any], digest_field: str, label: str) -> str:
    copied = dict(record)
    digest = copied.pop(digest_field, None)
    if not isinstance(digest, str) or digest != canonical_sha256(copied):
        raise ValueError(f"{label} canonical digest mismatch")
    return digest


def verify_material_map(frame_map: dict[str, Any]) -> dict[str, Any]:
    actual_file_hash = sha256_file(ROOT / FRAME_MAP_PATH)
    if actual_file_hash != EXPECTED_FRAME_MAP_SHA256:
        raise ValueError("Attempt02 material-frame map file hash changed")
    record_digest = check_record_digest(frame_map, "record_sha256", "Attempt02 material-frame map")
    if record_digest != EXPECTED_FRAME_MAP_RECORD_SHA256:
        raise ValueError("Attempt02 material-frame map record digest changed")
    pins = frame_map.get("source_pins")
    if not isinstance(pins, dict) or not pins:
        raise ValueError("Attempt02 material-frame map lacks its source pins")
    for relative, pin in sorted(pins.items()):
        expected = pin.get("sha256") if isinstance(pin, dict) else None
        path = ROOT / relative
        if not isinstance(expected, str) or not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Attempt02 material-frame source pin changed: {relative}")
    if frame_map.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Material map candidate identity changed")
    if frame_map.get("selected_candidate_preserved") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("Material map no longer preserves selected-candidate authority")
    if frame_map.get("geometry_revision_id") != EXPECTED_REVISION:
        raise ValueError("Material map no longer binds the reviewed revision")
    members = frame_map.get("members")
    if not isinstance(members, list) or len(members) != 24:
        raise ValueError("Material map must bind exactly 24 connector blocks")
    by_id = {row.get("part_id"): row for row in members}
    if len(by_id) != 24 or set(by_id) != set(frame_map["scope"]["mapped_part_ids"]):
        raise ValueError("Material map member IDs are malformed or duplicated")
    for part_id, row in by_id.items():
        axes = row.get("source_frame_axes_global_xyz")
        if not isinstance(axes, dict) or set(axes) != {"X", "T", "N"}:
            raise ValueError(f"{part_id}: mapped source/material frame is incomplete")
        vectors = {name: [float(x) for x in axes[name]] for name in ("X", "T", "N")}
        if any(len(vector) != 3 or abs(vector_norm(vector) - 1.0) > 1e-8 for vector in vectors.values()):
            raise ValueError(f"{part_id}: mapped source/material axes are not unit vectors")
        if any(abs(dot(vectors[a], vectors[b])) > 1e-8 for a, b in (("X", "T"), ("X", "N"), ("T", "N"))):
            raise ValueError(f"{part_id}: mapped source/material axes are not orthogonal")
        cross_xt = [
            vectors["X"][1] * vectors["T"][2] - vectors["X"][2] * vectors["T"][1],
            vectors["X"][2] * vectors["T"][0] - vectors["X"][0] * vectors["T"][2],
            vectors["X"][0] * vectors["T"][1] - vectors["X"][1] * vectors["T"][0],
        ]
        if dot(cross_xt, vectors["N"]) < 1.0 - 1e-8:
            raise ValueError(f"{part_id}: mapped source/material frame is not right-handed")
    return {
        "file_sha256": actual_file_hash,
        "record_sha256": record_digest,
        "source_pin_count": len(pins),
        "mapped_block_count": len(by_id),
        "member_by_id": by_id,
    }


def verify_solids_manifest(solids: dict[str, Any]) -> dict[str, Any]:
    actual_file_hash = sha256_file(ROOT / SOLIDS_PATH)
    if actual_file_hash != EXPECTED_SOLIDS_SHA256:
        raise ValueError("Exact full-frame member-solid manifest file hash changed")
    artifact_digest = check_record_digest(solids, "artifact_sha256", "Exact full-frame member-solid manifest")
    if artifact_digest != EXPECTED_SOLIDS_ARTIFACT_SHA256:
        raise ValueError("Exact full-frame member-solid artifact digest changed")
    if solids.get("member_bundle_sha256") != EXPECTED_MEMBER_BUNDLE_SHA256:
        raise ValueError("Exact full-frame STEP bundle digest changed")
    bundle_hash = canonical_sha256(
        [
            {"member_id": row["member_id"], "step_sha256": row["step_sha256"]}
            for row in solids.get("members", [])
        ]
    )
    if bundle_hash != solids.get("member_bundle_sha256"):
        raise ValueError("Exact full-frame STEP bundle digest does not match its rows")
    if solids.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Exact member-solid candidate identity changed")
    if solids.get("selected_candidate_preserved") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("Exact member-solid package no longer preserves selected authority")
    if solids.get("geometry_revision_id") != EXPECTED_REVISION:
        raise ValueError("Exact member-solid package no longer binds the reviewed revision")
    source_files = solids.get("source_files_sha256")
    if not isinstance(source_files, dict) or not source_files:
        raise ValueError("Exact member-solid package lacks its source-file pins")
    for relative, expected in sorted(source_files.items()):
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Exact member-solid source file changed: {relative}")
    members = solids.get("members")
    if not isinstance(members, list) or len(members) != 50:
        raise ValueError("Exact member-solid package must contain 50 members")
    by_id = {row.get("member_id"): row for row in members}
    if len(by_id) != 50:
        raise ValueError("Exact member-solid IDs are malformed or duplicated")
    expected_step_names = {f"{member_id}.step" for member_id in by_id}
    member_dir = ROOT / SOLIDS_DIR / "members"
    if not member_dir.is_dir() or {path.name for path in member_dir.glob("*.step")} != expected_step_names:
        raise ValueError("Full-frame STEP file tree differs from its source manifest")
    for member_id, row in sorted(by_id.items()):
        path = ROOT / SOLIDS_DIR / "members" / f"{member_id}.step"
        if sha256_file(path) != row.get("step_sha256"):
            raise ValueError(f"{member_id}: STEP file hash differs from the exact-solid manifest")
    return {
        "file_sha256": actual_file_hash,
        "artifact_sha256": artifact_digest,
        "member_bundle_sha256": bundle_hash,
        "source_file_pin_count": len(source_files),
        "member_by_id": by_id,
    }


def _bbox_xyz(bounds: Any) -> list[float]:
    return [
        float(bounds.xmin),
        float(bounds.xmax),
        float(bounds.ymin),
        float(bounds.ymax),
        float(bounds.zmin),
        float(bounds.zmax),
    ]


def _compare_global_summary(actual: list[float], expected: list[float], member_id: str) -> None:
    if len(expected) != 6 or any(
        abs(a - float(e)) > MEMBER_BOUNDS_TOLERANCE_MM
        for a, e in zip(actual, expected, strict=True)
    ):
        raise ValueError(f"{member_id}: STEP global bounds differ from exact-solid manifest")


def _datum_candidates(
    block_id: str,
    axis_rows: list[dict[str, Any]],
    inventory_by_id: dict[str, dict[str, Any]],
    station_n: list[float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    receivers = sorted(
        {
            receiver_id
            for row in axis_rows
            for receiver_id in row.get("receiver_member_ids", [])
            if receiver_id != block_id
        }
    )
    candidates = []
    missing_source_members = []
    for member_id in receivers:
        source = inventory_by_id.get(member_id)
        if source is None:
            missing_source_members.append(member_id)
            continue
        transform = source.get("local_to_global_transform")
        axes = source.get("local_axes")
        if not isinstance(transform, list) or len(transform) != 4 or not isinstance(axes, dict):
            raise ValueError(f"{member_id}: source inventory frame/datum is malformed")
        origin = [float(transform[i][3]) for i in range(3)]
        host_n = [float(x) for x in axes.get("N", [])]
        if len(host_n) != 3 or abs(vector_norm(host_n) - 1.0) > 1e-8:
            raise ValueError(f"{member_id}: source inventory N axis is malformed")
        alignment = dot(host_n, station_n)
        candidates.append(
            {
                "source_host_member_id": member_id,
                "source_local_datum_name": source.get("local_datum"),
                "source_inventory_record_sha256": source.get("source_shape_record_sha256"),
                "source_inventory_shape_sha256": source.get("source_shape_sha256"),
                "source_frame_origin_global_xyz_mm": [rounded(value) for value in origin],
                "source_host_N_global_xyz": [rounded(value, 12) for value in host_n],
                "source_host_N_dot_canonical_station_N": rounded(alignment, 12),
                "source_origin_projection_on_canonical_station_N_mm": rounded(dot(station_n, origin)),
                "candidate_only_not_adopted_station_datum": True,
                "source_host_N_parallel_to_canonical_station_N": abs(abs(alignment) - 1.0) <= 1e-8,
            }
        )
    stations = [
        {
            "axis_id": row["axis_id"],
            "station_id": row.get("station_id"),
            "receiver_member_ids": list(row.get("receiver_member_ids", [])),
        }
        for row in sorted(axis_rows, key=lambda row: row["axis_id"])
    ]
    return candidates, stations, missing_source_members


def _project_step(
    member_id: str,
    step_path: Path,
    manifest_row: dict[str, Any],
    station_frame: dict[str, list[float]],
) -> dict[str, Any]:
    shape = cq.importers.importStep(str(step_path)).val()
    if not shape.isValid() or len(shape.Solids()) != 1 or float(shape.Volume()) <= 0:
        raise ValueError(f"{member_id}: expected one valid positive-volume STEP solid")
    global_bounds = _bbox_xyz(shape.BoundingBox())
    _compare_global_summary(global_bounds, manifest_row["shape_summary"]["bounds_xyz_mm"], member_id)
    expected_volume = float(manifest_row["shape_summary"]["volume_mm3"])
    if abs(float(shape.Volume()) - expected_volume) > MEMBER_VOLUME_TOLERANCE_MM3:
        raise ValueError(f"{member_id}: STEP volume differs from exact-solid manifest")

    # Build a proper rigid transform from global XYZ into the frozen station XYZ/T/N basis.
    axes = [station_frame[name] for name in ("X", "T", "N")]
    transform = gp_Trsf()
    transform.SetValues(
        axes[0][0], axes[0][1], axes[0][2], 0.0,
        axes[1][0], axes[1][1], axes[1][2], 0.0,
        axes[2][0], axes[2][1], axes[2][2], 0.0,
    )
    projected = shape.transformShape(cq.Matrix(transform))
    if not projected.isValid() or len(projected.Solids()) != 1:
        raise ValueError(f"{member_id}: canonical station transform damaged STEP topology")
    bounds = projected.BoundingBox()
    n_min = float(bounds.zmin)
    n_max = float(bounds.zmax)
    span = n_max - n_min
    relation = (
        "equal_within_numeric_tolerance_as_body_span_only"
        if abs(span - LIMIT_MM) <= COMPARISON_TOLERANCE_MM
        else "greater_than_reference_as_body_span_only"
        if span > LIMIT_MM
        else "less_than_reference_as_body_span_only"
    )
    return {
        "step_file": manifest_row["step_file"],
        "step_sha256": manifest_row["step_sha256"],
        "step_size_bytes": manifest_row["step_size_bytes"],
        "source_shape_fingerprint_sha256": manifest_row["source_shape_fingerprint_sha256"],
        "shape_summary_sha256": manifest_row["shape_summary_sha256"],
        "exact_step_valid": True,
        "exact_step_solid_count": 1,
        "exact_step_volume_mm3": rounded(float(shape.Volume())),
        "global_bounds_xyz_mm": [rounded(value) for value in global_bounds],
        "canonical_station_N_projection_from_global_origin_mm": [rounded(n_min), rounded(n_max)],
        "canonical_station_N_body_span_mm": rounded(span),
        "body_span_reference_comparison": {
            "reference_mm": LIMIT_MM,
            "numeric_tolerance_mm": COMPARISON_TOLERANCE_MM,
            "relation": relation,
            "envelope_status": "not_assessed_without_adopted_station_datum",
        },
    }


def build_record() -> dict[str, Any]:
    frame_map = read_json(ROOT / FRAME_MAP_PATH)
    solids = read_json(ROOT / SOLIDS_PATH)
    input_manifest = read_json(ROOT / INPUT_MANIFEST_PATH)
    inventory = read_json(ROOT / SOURCE_INVENTORY_PATH)

    frame_check = verify_material_map(frame_map)
    solids_check = verify_solids_manifest(solids)
    if sha256_file(ROOT / INPUT_MANIFEST_PATH) != EXPECTED_INPUT_MANIFEST_SHA256:
        raise ValueError("Attempt02 current full-frame input manifest hash changed")
    if input_manifest.get("manifest_id") != frame_map.get("input_manifest_id"):
        raise ValueError("Material map and current full-frame input manifest IDs differ")
    if input_manifest.get("manifest_sha256") != frame_map.get("input_manifest_sha256"):
        raise ValueError("Material map and current full-frame input manifest digests differ")
    if frame_map.get("reviewed_repository_commit") != "b1e8707d":
        raise ValueError("Material map no longer binds the reviewed checkpoint")
    if input_manifest.get("geometry_revision_id") != EXPECTED_REVISION:
        raise ValueError("Attempt02 full-frame input manifest revision changed")
    if input_manifest.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Attempt02 full-frame input manifest candidate changed")

    station_frame = canonical_station_frame(input_manifest)
    block_ids = set(frame_check["member_by_id"])
    block_manifest_rows = {
        row["part_id"]: row for row in input_manifest.get("candidate_blocks", [])
    }
    if len(block_manifest_rows) != 24 or set(block_manifest_rows) != block_ids:
        raise ValueError("Exact input manifest and attempt02 map block IDs differ")
    solid_rows = solids_check["member_by_id"]
    step_rows = {
        part_id: solid_rows.get(part_id)
        for part_id in block_ids
    }
    if any(row is None or row.get("member_kind") != "candidate_block" for row in step_rows.values()):
        raise ValueError("Exact STEP bundle block IDs differ from attempt02 map")

    inventory_rows = inventory.get("parts")
    if not isinstance(inventory_rows, list):
        raise ValueError("Pinned source inventory lacks part rows")
    inventory_by_id = {row["part_id"]: row for row in inventory_rows}
    if len(inventory_by_id) != len(inventory_rows):
        raise ValueError("Pinned source inventory contains duplicate part IDs")
    source_inventory_pin = frame_map["source_pins"].get(SOURCE_INVENTORY_PATH, {}).get("sha256")
    if sha256_file(ROOT / SOURCE_INVENTORY_PATH) != source_inventory_pin:
        raise ValueError("Source inventory differs from the attempt02 material-map pin")

    axes_by_block: dict[str, list[dict[str, Any]]] = {part_id: [] for part_id in block_ids}
    for axis in input_manifest.get("candidate_bolt_axes", []):
        for receiver in axis.get("receiver_member_ids", []):
            if receiver in axes_by_block:
                axes_by_block[receiver].append(axis)
    if any(len(rows) == 0 for rows in axes_by_block.values()):
        raise ValueError("At least one current candidate block has no linked bolt axes")

    members = []
    for part_id in sorted(block_ids):
        mapped = frame_check["member_by_id"][part_id]
        host_candidates, station_rows, missing_source_members = _datum_candidates(
            part_id,
            axes_by_block[part_id],
            inventory_by_id,
            station_frame["N"],
        )
        step_path = ROOT / SOLIDS_DIR / "members" / f"{part_id}.step"
        projection = _project_step(part_id, step_path, step_rows[part_id], station_frame)
        material_n = [float(x) for x in mapped["source_frame_axes_global_xyz"]["N"]]
        members.append(
            {
                "part_id": part_id,
                "pattern_id": mapped["pattern_id"],
                "candidate_axis_stations": station_rows,
                "source_material_frame": {
                    "source_N_global_xyz": [rounded(value, 12) for value in material_n],
                    "source_N_dot_canonical_station_N": rounded(dot(material_n, station_frame["N"]), 12),
                    "binding_method": mapped["frame_binding"]["method"],
                    "basis_sources": mapped["frame_binding"]["basis_sources"],
                    "saved_transform_matrix_4x4": mapped["frame_binding"].get("transform_matrix_4x4"),
                    "conditional_frame_use": "identity/geometry cross-check only; not substituted for the frozen canonical station N",
                },
                "station_datum": {
                    "status": "not_specified_or_adopted_in_reviewed_handoff_or_current_input_records",
                    "global_xyz_mm": None,
                    "canonical_station_N_coordinate_mm": None,
                    "host_source_frame_origins_checked": host_candidates,
                    "receiver_member_ids_missing_from_source_inventory": missing_source_members,
                    "why_unresolved": (
                        "The current axis inventory links this block to receiver hosts, but no source record selects "
                        "a station datum among their member-local origins. Those origins are historical source-member "
                        "frame corners, not adopted current station datums. Some linked receivers also lack a source "
                        "inventory frame record; this does not prevent an exact block-body directional-span screen."
                    ),
                },
                "geometry_projection": projection,
            }
        )

    source_inventory_hash = sha256_file(ROOT / SOURCE_INVENTORY_PATH)
    producer_path = Path(__file__).resolve()
    record: dict[str, Any] = {
        "schema": "wood_joint_current_block_canonical_station_n_projection/v1",
        "attempt_id": "current-block-n-envelope-attempt01",
        "status": "conditional_block_body_projection_datum_unresolved",
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_preserved": EXPECTED_SELECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "reviewed_source_checkpoint": "b1e8707d",
        "source_bindings": {
            "attempt02_material_frame_map_path": FRAME_MAP_PATH,
            "attempt02_material_frame_map_sha256": frame_check["file_sha256"],
            "attempt02_material_frame_record_sha256": frame_check["record_sha256"],
            "attempt02_full_frame_manifest_path": INPUT_MANIFEST_PATH,
            "attempt02_full_frame_manifest_sha256": sha256_file(ROOT / INPUT_MANIFEST_PATH),
            "attempt01_exact_member_solids_manifest_path": SOLIDS_PATH,
            "attempt01_exact_member_solids_manifest_sha256": solids_check["file_sha256"],
            "attempt01_exact_member_solids_artifact_sha256": solids_check["artifact_sha256"],
            "attempt01_exact_member_step_bundle_sha256": solids_check["member_bundle_sha256"],
            "source_inventory_sha256": source_inventory_hash,
            "review_sources_sha256": {
                relative: sha256_file(ROOT / relative) for relative in REVIEW_SOURCE_PATHS
            },
            "material_map_source_pins": frame_map["source_pins"],
            "exact_member_solids_source_file_hashes_sha256": solids["source_files_sha256"],
            "producer_sha256": sha256_file(producer_path),
        },
        "coordinate_contract": {
            "units": "mm",
            "station_frame_source": "attempt02 full-frame input manifest coordinate_and_unit_contract.preserved_source_frame",
            "station_axes_global_xyz": {name: [rounded(x, 12) for x in station_frame[name]] for name in ("X", "T", "N")},
            "station_N_definition": "N=(0,-sin(50 deg),cos(50 deg))",
            "measured_frame": "canonical station frame; independent of conditional per-block material/grain N",
            "projection_transform": "proper rigid exact-BRep transform from global XYZ into canonical station X/T/N",
            "bounding_method": "CadQuery Shape.BoundingBox default optimal OCCT AddOptimal on transformed exact STEP BRep; no viewer mesh or tessellation",
            "datum_origin_used_for_reported_global_projection": "global XYZ origin only; this is not an adopted station datum",
        },
        "criterion": {
            "id": "ordinary_n_envelope",
            "reference_limit_mm": LIMIT_MM,
            "station_relative_envelope_status": "pending_unresolved_missing_adopted_station_datum",
            "dimensioned_exception_authorized": False,
            "required_station_relative_fields": ["connector_N_min_mm", "connector_N_max_mm"],
            "required_station_relative_fields_available": False,
        },
        "scope": {
            "exact_candidate_block_count": len(members),
            "exact_block_ids_match_attempt02_material_map": True,
            "exact_step_validity_and_single_solid_checked": True,
            "block_only_permanent_geometry": True,
            "modeled_or_delivered_hardware_included": False,
            "tool_or_product_envelopes_included": False,
            "tolerance_envelopes_included": False,
            "selected_or_delivered_bolt_nut_washer_available": False,
        },
        "datum_search": {
            "sources_checked": [
                "docs/wood-joints-mvp/decision-log.md",
                "docs/wood-joints-mvp/plan.md",
                "docs/wood-joints-mvp/criteria.json",
                "docs/wood-joints-mvp/current-criteria-coverage.md",
                "docs/wood-joints-mvp/orchestration-handoff.md",
                "docs/wood-joints-mvp/outer-node-result.md",
                INPUT_MANIFEST_PATH,
                FRAME_MAP_PATH,
                SOURCE_INVENTORY_PATH,
            ],
            "result": "No adopted per-station datum rule for the reviewed 24-block revision was found. The decision-log datum is explicitly for the historical WJ-03 outer post/header station; it does not define datums for all current blocks. At least one axis-linked receiver is absent from source-inventory frame records and is retained as a named source-resolution gap.",
            "source_inventory_origin_interpretation": "actual_vertex_minimum_N_then_T_then_X is a member-local source-frame origin. It is retained per linked host as a candidate reference only; no current source record adopts it as a station datum.",
        },
        "members": members,
        "summary": {
            "body_spans_below_139_7_mm": sum(row["geometry_projection"]["body_span_reference_comparison"]["relation"] == "less_than_reference_as_body_span_only" for row in members),
            "body_spans_equal_to_139_7_mm_within_tolerance": sum(row["geometry_projection"]["body_span_reference_comparison"]["relation"] == "equal_within_numeric_tolerance_as_body_span_only" for row in members),
            "body_spans_above_139_7_mm": sum(row["geometry_projection"]["body_span_reference_comparison"]["relation"] == "greater_than_reference_as_body_span_only" for row in members),
            "body_span_max_mm": max(row["geometry_projection"]["canonical_station_N_body_span_mm"] for row in members),
            "body_span_comparison_limit": "Directional span only; these figures are not station-envelope pass/exceedance results without the adopted datum.",
            "ordinary_n_envelope_disposition": "pending; no exception is authorized.",
        },
        "claim_limits": [
            "Canonical station N projections are computed from exact imported STEP BReps, not viewer meshes.",
            "The reported N-min/N-max values are relative to global XYZ origin because the reviewed inputs do not adopt a current per-station datum.",
            "Source-inventory host origins are listed as unadopted candidates and do not establish station-relative envelope status.",
            "Directional body spans may be compared dimensionally with 139.7 mm but do not prove a station envelope pass, exceedance, or exact contact.",
            "No selected/delivered bolt, nut, washer, tool/product envelope, tolerance envelope, or installed-hardware N bound is available.",
            "No dimensioned exception, physical fabrication, native solve, candidate acceptance, or climbing release is authorized or claimed.",
        ],
        "release": {
            "exception_authorized": False,
            "candidate_accepted": False,
            "native_solve_executed": False,
            "fabrication_released": False,
            "climbing_released": False,
        },
    }
    record["record_sha256"] = canonical_sha256(record)
    return record


def verify() -> dict[str, Any]:
    if not OUTPUT.is_file():
        raise FileNotFoundError(f"Projection record is missing: {OUTPUT}")
    expected = build_record()
    actual = read_json(OUTPUT)
    digest = check_record_digest(actual, "record_sha256", "Block N projection record")
    if digest != expected["record_sha256"]:
        raise ValueError("Block N projection differs from the current source-bound reconstruction")
    if actual != expected:
        raise ValueError("Block N projection payload differs from current source-bound inputs")
    return {
        "status": "verified_conditional_geometry_screen_datum_unresolved",
        "candidate": actual["candidate"],
        "geometry_revision_id": actual["geometry_revision_id"],
        "block_count": len(actual["members"]),
        "station_datum_status": actual["criterion"]["station_relative_envelope_status"],
        "body_span_counts": {
            "below": actual["summary"]["body_spans_below_139_7_mm"],
            "equal": actual["summary"]["body_spans_equal_to_139_7_mm_within_tolerance"],
            "above": actual["summary"]["body_spans_above_139_7_mm"],
        },
        "record_sha256": digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write:
        if OUTPUT.exists():
            raise FileExistsError(f"Refusing to overwrite existing artifact: {OUTPUT}")
        record = build_record()
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "written", "record_sha256": record["record_sha256"]}, sort_keys=True))
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
