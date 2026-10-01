"""Export and verify exact current timber, panel, and connector STEP solids.

The export freezes geometric inputs for the reviewed development revision. It
does not create a mesh, solve, or establish a mechanical or release result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
ATTEMPT_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ATTEMPT_DIR / "bundle"
MEMBER_DIR = ARTIFACT_DIR / "members"
OUTPUT_PATH = ARTIFACT_DIR / "current-full-frame-member-solids.json"
SCENE_PATH = "site/owner-wood-joints-wj24-scene.json"
REVIEW_REPORT_PATH = "site/owner-wood-joints-review-report.json"
CONTRACT_PATH = "wood-joints-candidate.json"
SELECTED_PATH = "current-candidate.json"
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SNAPSHOT_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
BASE_MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json"
)
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_CANDIDATE = "compact-floor-flush-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_PART_COUNTS = {"timber": 20, "plywood_panel": 6, "candidate_block": 24}
EXPECTED_REPLACED_PANEL_IDS = frozenset(
    {
        "main_lower_left",
        "main_lower_right",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
    }
)
ROUNDTRIP_BOUNDS_TOLERANCE_MM = 1e-5
ROUNDTRIP_VOLUME_TOLERANCE_MM3 = 1e-3
ROUNDTRIP_SYMMETRIC_DIFFERENCE_TOLERANCE_MM3 = 1e-2


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _relative_file_hash(path: Path) -> tuple[str, str] | None:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return relative, _sha256_file(resolved)


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_plain(item) for item in value]
    if hasattr(value, "items"):
        return {str(key): _plain(item) for key, item in value.items()}
    if hasattr(value, "tolist"):
        return _plain(value.tolist())
    if hasattr(value, "item"):
        return _plain(value.item())
    return value


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


class _PathReadTracker:
    """Record in-repository Path.read_text/read_bytes inputs during replay."""

    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}
        self._read_text = Path.read_text
        self._read_bytes = Path.read_bytes

    def _record(self, path: Path, raw: bytes) -> None:
        try:
            resolved = path.resolve()
            relative = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return
        if not resolved.is_file():
            return
        read_hash = _sha256_bytes(raw)
        prior = self.hashes.get(relative)
        if prior is not None and prior != read_hash:
            raise RuntimeError(f"Input changed during geometry replay: {relative}")
        self.hashes[relative] = read_hash

    def __enter__(self) -> _PathReadTracker:
        tracker = self

        def tracked_read_bytes(path: Path) -> bytes:
            value = tracker._read_bytes(path)
            tracker._record(path, value)
            return value

        def tracked_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
            value = tracker._read_text(path, *args, **kwargs)
            tracker._record(path, tracker._read_bytes(path))
            return value

        Path.read_bytes = tracked_read_bytes  # type: ignore[method-assign]
        Path.read_text = tracked_read_text  # type: ignore[method-assign]
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        Path.read_text = self._read_text  # type: ignore[method-assign]
        Path.read_bytes = self._read_bytes  # type: ignore[method-assign]


def _loaded_project_module_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name, module in sorted(sys.modules.items()):
        if not name.startswith(("mini_moonboard.", "scripts.")):
            continue
        path_value = getattr(module, "__file__", None)
        if not path_value:
            continue
        path = Path(path_value)
        item = _relative_file_hash(path)
        if item is None or path.suffix != ".py":
            continue
        relative, digest = item
        hashes[relative] = digest
    return hashes


def _shape(value: Any) -> Any:
    shape = getattr(value, "shape", value)
    if hasattr(shape, "val"):
        shape = shape.val()
    return shape


def _rounded(value: float, places: int = 9) -> float:
    rounded = round(float(value), places)
    return 0.0 if rounded == 0.0 else rounded


def _shape_summary(shape: Any) -> dict[str, Any]:
    bounds = shape.BoundingBox()
    center = shape.Center()
    surface_area_by_type: Counter[str] = Counter()
    for face in shape.Faces():
        surface_area_by_type[str(face.geomType())] += float(face.Area())
    return {
        "valid": bool(shape.isValid()),
        "solid_count": len(shape.Solids()),
        "shell_count": len(shape.Shells()),
        "face_count": len(shape.Faces()),
        "edge_count": len(shape.Edges()),
        "vertex_count": len(shape.Vertices()),
        "volume_mm3": _rounded(shape.Volume()),
        "surface_area_mm2": _rounded(shape.Area()),
        "center_xyz_mm": [_rounded(value) for value in center.toTuple()],
        "bounds_xyz_mm": [
            _rounded(value)
            for value in (
                bounds.xmin,
                bounds.xmax,
                bounds.ymin,
                bounds.ymax,
                bounds.zmin,
                bounds.zmax,
            )
        ],
        "surface_area_by_type_mm2": {
            key: _rounded(value) for key, value in sorted(surface_area_by_type.items())
        },
    }


def _require_shape(shape: Any, member_id: str) -> dict[str, Any]:
    summary = _shape_summary(shape)
    if not summary["valid"] or summary["solid_count"] != 1:
        raise ValueError(
            f"{member_id}: expected one valid solid, got "
            f"valid={summary['valid']} solids={summary['solid_count']}"
        )
    if summary["volume_mm3"] <= 0:
        raise ValueError(f"{member_id}: shape has no positive volume")
    return summary


def _validate_identity() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _json(ROOT / CONTRACT_PATH)
    selected = _json(ROOT / SELECTED_PATH)
    scene = _json(ROOT / SCENE_PATH)
    if contract.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Wood-joints candidate authority changed")
    if selected.get("candidate") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("Selected-candidate authority changed")
    if contract.get("authority", {}).get("selected_candidate") != selected["candidate"]:
        raise ValueError("Wood-joints contract no longer preserves selected authority")
    revision = contract.get("current_development_revision")
    if not isinstance(revision, dict) or revision.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Candidate contract no longer binds the reviewed revision")
    if revision.get("release") is not False:
        raise ValueError("Reviewed development revision must remain unreleased")
    if scene.get("candidate") != EXPECTED_CANDIDATE or scene.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Owner scene candidate or revision identity changed")
    source_binding = scene.get("source_binding")
    if not isinstance(source_binding, dict):
        raise TypeError("Owner scene lacks source-binding data")
    report_path = ROOT / str(revision.get("report", ""))
    if not report_path.is_file():
        raise ValueError("Candidate contract report is missing")
    report_hash = _sha256_file(report_path)
    inventory_hash = _sha256_file(ROOT / INVENTORY_PATH)
    if source_binding.get("revision_report_sha256") != report_hash:
        raise ValueError("Owner scene revision-report hash is stale")
    if source_binding.get("source_inventory_sha256") != inventory_hash:
        raise ValueError("Owner scene source-inventory hash is stale")
    counts = scene.get("counts")
    expected_counts = {
        "candidate_parts": 24,
        "candidate_bores": 92,
        "panel_screw_axes_total": 66,
        "retained_frame_bolts": 12,
        "fixed_panel_axes": 58,
        "moved_panel_axes": 8,
    }
    if not isinstance(counts, dict) or any(counts.get(key) != count for key, count in expected_counts.items()):
        raise ValueError("Owner scene counts differ from the reviewed revision")
    if not isinstance(scene.get("release"), dict) or any(
        value is not False for value in scene["release"].values()
    ):
        raise ValueError("Every owner-scene release flag must remain false")
    return contract, selected, scene


def _collect_member_shapes(geometry: Any, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

    inventory = _json(ROOT / INVENTORY_PATH)
    source_rows = inventory.get("parts")
    if not isinstance(source_rows, list) or len(source_rows) != 26:
        raise ValueError("Source inventory must contain 26 timber/panel records")
    source_by_id = {row["part_id"]: row for row in source_rows}
    if len(source_by_id) != 26:
        raise ValueError("Source inventory member IDs are not unique")
    source_kinds = Counter(row.get("kind") for row in source_rows)
    if source_kinds != Counter({"timber": 20, "plywood_panel": 6}):
        raise ValueError(f"Unexpected source-member kinds: {dict(source_kinds)}")

    source_parts: dict[str, Any] = {}
    duplicate_source_ids: set[str] = set()
    for part in geometry.source.parts():
        part_id = _part_name(part)
        if part_id not in source_by_id:
            continue
        if part_id in source_parts:
            duplicate_source_ids.add(part_id)
        source_parts[part_id] = _shape(part)
    missing_source_ids = set(source_by_id) - set(source_parts)
    if duplicate_source_ids or missing_source_ids:
        raise ValueError(
            "Replayed inventory source geometry IDs are not unique and complete: "
            f"duplicates={sorted(duplicate_source_ids)}, missing={sorted(missing_source_ids)}"
        )
    finished_hosts = dict(geometry.finished_hosts)
    panel_replacements = dict(geometry.panel_replacements)
    candidate_parts = dict(geometry.finished_candidate_parts)
    if (
        len(finished_hosts) != 16
        or set(panel_replacements) != EXPECTED_REPLACED_PANEL_IDS
        or len(candidate_parts) != 24
    ):
        raise ValueError("Replayed current geometry has unexpected finished-body counts")

    shapes: dict[str, Any] = {}
    records: dict[str, dict[str, Any]] = {}
    physical_rows = {row["member_id"]: row for row in manifest.get("physical_members", [])}
    block_rows = {row["part_id"]: row for row in manifest.get("candidate_blocks", [])}
    if len(physical_rows) != 50 or len(block_rows) != 24:
        raise ValueError("Attempt02 manifest member rows are incomplete")

    for part_id, row in sorted(source_by_id.items()):
        if part_id in finished_hosts:
            shape = _shape(finished_hosts[part_id])
            geometry_source = "current_composed_finished_host"
        elif part_id in panel_replacements:
            shape = _shape(panel_replacements[part_id])
            geometry_source = "current_composed_panel_replacement"
        else:
            shape = source_parts[part_id]
            geometry_source = "current_source_part_unchanged_in_composition"
        if part_id not in physical_rows:
            raise ValueError(f"{part_id}: absent from full-frame manifest")
        member_row = physical_rows[part_id]
        manifest_kind = "panel" if row["kind"] == "plywood_panel" else row["kind"]
        if member_row.get("member_kind") != manifest_kind:
            raise ValueError(f"{part_id}: manifest kind differs from source inventory")
        summary = _require_shape(shape, part_id)
        _compare_summary_to_manifest(part_id, summary, member_row)
        shape_fingerprint = _source_shape_fingerprint(shape)
        shapes[part_id] = shape
        records[part_id] = {
            "member_id": part_id,
            "member_kind": row["kind"],
            "geometry_source": geometry_source,
            "source_part_record_sha256": _canonical_sha256(row),
            "source_shape_fingerprint_sha256": shape_fingerprint,
            "shape_summary": summary,
            "shape_summary_sha256": _canonical_sha256(summary),
            "bounds_and_volume_match_current_manifest": True,
        }

    for part_id, shape_value in sorted(candidate_parts.items()):
        if part_id not in block_rows or part_id in shapes:
            raise ValueError(f"{part_id}: duplicate or unknown candidate block ID")
        shape = _shape(shape_value)
        summary = _require_shape(shape, part_id)
        _compare_summary_to_manifest(part_id, summary, block_rows[part_id], block=True)
        shape_fingerprint = _source_shape_fingerprint(shape)
        shapes[part_id] = shape
        records[part_id] = {
            "member_id": part_id,
            "member_kind": "candidate_block",
            "geometry_source": "current_composed_finished_candidate_part",
            "source_part_record_sha256": None,
            "source_shape_fingerprint_sha256": shape_fingerprint,
            "shape_summary": summary,
            "shape_summary_sha256": _canonical_sha256(summary),
            "bounds_and_volume_match_current_manifest": True,
        }

    expected_ids = set(physical_rows) | set(block_rows)
    if set(shapes) != expected_ids or len(records) != 50:
        raise ValueError("Replayed geometry does not match the 50 unique full-frame member IDs")
    return shapes, records


def _part_name(value: Any) -> str:
    name = getattr(value, "name", None)
    if not isinstance(name, str):
        raise TypeError("Current source geometry part is missing a string name")
    return name


def _compare_summary_to_manifest(
    member_id: str,
    summary: dict[str, Any],
    manifest_row: dict[str, Any],
    *,
    block: bool = False,
) -> None:
    geometry = manifest_row.get("finished_geometry_summary") if block else manifest_row.get(
        "graph_finished_geometry_summary"
    )
    if block:
        geometry = geometry.get("finished") if isinstance(geometry, dict) else None
    if not isinstance(geometry, dict):
        raise ValueError(f"{member_id}: manifest lacks a finished geometry summary")
    expected_volume = float(geometry.get("volume_mm3"))
    actual_volume = float(summary["volume_mm3"])
    if not math.isclose(actual_volume, expected_volume, rel_tol=1e-9, abs_tol=1e-2):
        raise ValueError(f"{member_id}: source volume differs from current manifest")
    if block:
        expected_bounds = [
            *geometry.get("min_xyz_mm", []),
            *geometry.get("max_xyz_mm", []),
        ]
        # The snapshot stores three minima followed by three maxima.
        expected_bounds = [
            expected_bounds[0],
            expected_bounds[3],
            expected_bounds[1],
            expected_bounds[4],
            expected_bounds[2],
            expected_bounds[5],
        ]
    else:
        expected_bounds = geometry.get("bounds_xyz_mm")
    if not isinstance(expected_bounds, list) or len(expected_bounds) != 6:
        raise ValueError(f"{member_id}: manifest bounds are malformed")
    if any(
        abs(float(actual) - float(expected)) > 1e-5
        for actual, expected in zip(summary["bounds_xyz_mm"], expected_bounds, strict=True)
    ):
        raise ValueError(f"{member_id}: source bounds differ from current manifest")


def _source_closure(read_hashes: dict[str, str]) -> dict[str, str]:
    explicit = {
        CONTRACT_PATH,
        SELECTED_PATH,
        SCENE_PATH,
        REVIEW_REPORT_PATH,
        INVENTORY_PATH,
        SNAPSHOT_PATH,
        BASE_MANIFEST_PATH,
        "scripts/wood_joint_current_geometry.py",
        "scripts/wood_joint_development_candidate_check.py",
        "docs/wood-joints-mvp/current-material-scenarios.md",
    }
    for relative in explicit:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"Missing explicitly pinned source: {relative}")
        read_hashes[relative] = _sha256_file(path)
    modules = _loaded_project_module_hashes()
    read_hashes.update(modules)
    producer_relative = Path(__file__).resolve().relative_to(ROOT).as_posix()
    read_hashes[producer_relative] = _sha256_file(Path(__file__))
    return dict(sorted(read_hashes.items()))


def _build_payload() -> tuple[dict[str, Any], dict[str, Any]]:
    _validate_identity()
    manifest = _json(ROOT / BASE_MANIFEST_PATH)
    if manifest.get("geometry_revision_id") != EXPECTED_REVISION:
        raise ValueError("Attempt02 source manifest names another geometry revision")
    if manifest.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Attempt02 source manifest names another candidate")

    sys.path.insert(0, str(ROOT))
    from scripts.wood_joint_current_geometry import build_current_geometry

    print("replaying pinned current geometry", flush=True)
    with _PathReadTracker() as tracker:
        geometry, report = build_current_geometry(progress=lambda step: print(step, flush=True))
    if getattr(geometry, "layout_id", None) != EXPECTED_REVISION:
        raise ValueError("Current geometry replay returned an unexpected revision")
    if report.get("revision_id") != EXPECTED_REVISION or report.get("joint_evaluations_run") is not False:
        raise ValueError("Current geometry report identity/status is invalid")
    release = report.get("release")
    if not isinstance(release, dict) or any(value is not False for value in release.values()):
        raise ValueError("Every replayed geometry release flag must remain false")

    source_hashes = _source_closure(dict(tracker.hashes))
    shapes, records = _collect_member_shapes(geometry, manifest)
    runtime_source_inputs = _plain(getattr(geometry, "source_inputs_sha256", {}))
    family_source_fingerprints = _plain(getattr(geometry, "family_source_fingerprints", {}))
    payload = {
        "schema": "wood_joint_current_full_frame_member_solids/v1",
        "attempt_id": "current-full-frame-member-solids-attempt01",
        "status": "source_replayed_member_solids_ready_for_input_use",
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_preserved": EXPECTED_SELECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "reviewed_source_commit": "b1e8707d",
        "member_scope": {
            "timber": EXPECTED_PART_COUNTS["timber"],
            "plywood_panel": EXPECTED_PART_COUNTS["plywood_panel"],
            "candidate_block": EXPECTED_PART_COUNTS["candidate_block"],
            "total": sum(EXPECTED_PART_COUNTS.values()),
            "member_ids_unique": True,
            "geometry_source_counts": dict(
                Counter(row["geometry_source"] for row in records.values())
            ),
        },
        "source_files_sha256": source_hashes,
        "geometry_source_inputs_sha256": runtime_source_inputs,
        "geometry_family_source_fingerprints": family_source_fingerprints,
        "roundtrip_tolerances": {
            "bounds_mm": ROUNDTRIP_BOUNDS_TOLERANCE_MM,
            "volume_mm3": ROUNDTRIP_VOLUME_TOLERANCE_MM3,
            "symmetric_difference_volume_mm3": ROUNDTRIP_SYMMETRIC_DIFFERENCE_TOLERANCE_MM3,
        },
        "members": [records[member_id] for member_id in sorted(records)],
        "readiness": {
            "all_50_finished_member_solids_exported": False,
            "source_geometry_replayed": True,
            "step_roundtrip_checked": False,
            "per_member_material_mapping_ready": False,
            "selected_structural_hardware_ready": False,
            "active_contact_and_attachment_model_ready": False,
            "full_frame_demands_available": False,
            "criterion_resolved": False,
            "native_solve_executed": False,
            "candidate_accepted": False,
            "fabrication_released": False,
            "climbing_released": False,
        },
        "claim_limits": [
            "This package supplies exact current timber, panel and candidate-block STEP geometry only.",
            "It does not supply purchased hardware, full material frames, active connection transfer, or solver mappings.",
            "A STEP hash identifies the exported file; the shape-summary hash is a rounded geometric cross-check, not a kernel-canonical BRep hash.",
            "No mesh, mechanics solve, resistance check, acceptance, fabrication, or climbing release is included.",
        ],
        "release": {
            "candidate_accepted": False,
            "fabrication_released": False,
            "climbing_released": False,
        },
    }
    return payload, shapes


def _write_artifact() -> dict[str, Any]:
    if ARTIFACT_DIR.exists():
        raise FileExistsError("Refusing to overwrite an existing full-frame solid artifact")
    from cadquery import exporters, importers

    payload, shapes = _build_payload()
    member_records = {row["member_id"]: row for row in payload["members"]}
    readback_count = 0
    with TemporaryDirectory(prefix=".member-solids-", dir=ATTEMPT_DIR) as staging_name:
        staging = Path(staging_name)
        staged_bundle = staging / "bundle"
        staged_members = staged_bundle / "members"
        staged_members.mkdir(parents=True)
        for index, member_id in enumerate(sorted(shapes), start=1):
            print(f"STEP export {index}/50: {member_id}", flush=True)
            source_shape = shapes[member_id]
            destination = staged_members / f"{member_id}.step"
            exporters.export(source_shape, str(destination))
            if not destination.is_file() or destination.stat().st_size == 0:
                raise ValueError(f"{member_id}: STEP export was not created")
            imported = _shape(importers.importStep(str(destination)))
            roundtrip_summary = _require_shape(imported, member_id)
            _validate_roundtrip(member_id, source_shape, imported, roundtrip_summary)
            record = member_records[member_id]
            record["step_file"] = f"bundle/members/{member_id}.step"
            record["step_sha256"] = _sha256_file(destination)
            record["step_size_bytes"] = destination.stat().st_size
            record["step_roundtrip_summary"] = roundtrip_summary
            readback_count += 1

        payload["readiness"]["all_50_finished_member_solids_exported"] = readback_count == 50
        payload["readiness"]["step_roundtrip_checked"] = readback_count == 50
        payload["member_bundle_sha256"] = _canonical_sha256(
            [
                {"member_id": row["member_id"], "step_sha256": row["step_sha256"]}
                for row in payload["members"]
            ]
        )
        payload["artifact_sha256"] = _canonical_sha256(payload)
        staged_json = staged_bundle / "current-full-frame-member-solids.json"
        staged_json.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        staged_bundle.replace(ARTIFACT_DIR)
    return _result(payload, "written")


def _validate_roundtrip(
    member_id: str,
    source_shape: Any,
    imported_shape: Any,
    imported_summary: dict[str, Any],
) -> None:
    source_summary = _shape_summary(source_shape)
    for actual, expected in zip(
        imported_summary["bounds_xyz_mm"],
        source_summary["bounds_xyz_mm"],
        strict=True,
    ):
        if abs(actual - expected) > ROUNDTRIP_BOUNDS_TOLERANCE_MM:
            raise ValueError(f"{member_id}: STEP roundtrip bounds differ")
    if abs(imported_summary["volume_mm3"] - source_summary["volume_mm3"]) > ROUNDTRIP_VOLUME_TOLERANCE_MM3:
        raise ValueError(f"{member_id}: STEP roundtrip volume differs")
    source_only_volume = float(source_shape.cut(imported_shape).Volume())
    step_only_volume = float(imported_shape.cut(source_shape).Volume())
    symmetric_difference = source_only_volume + step_only_volume
    if symmetric_difference > ROUNDTRIP_SYMMETRIC_DIFFERENCE_TOLERANCE_MM3:
        raise ValueError(
            f"{member_id}: STEP roundtrip symmetric difference is "
            f"{symmetric_difference:.9g} mm^3"
        )


def _verify_artifact() -> dict[str, Any]:
    from cadquery import importers

    if not OUTPUT_PATH.is_file() or not MEMBER_DIR.is_dir():
        raise FileNotFoundError("Full-frame member-solid artifact is incomplete")
    recorded = _json(OUTPUT_PATH)
    actual_artifact_hash = recorded.pop("artifact_sha256", None)
    if actual_artifact_hash != _canonical_sha256(recorded):
        raise ValueError("Artifact canonical digest does not match its payload")
    recorded["artifact_sha256"] = actual_artifact_hash
    recorded_members = recorded.get("members")
    if not isinstance(recorded_members, list) or len(recorded_members) != 50:
        raise ValueError("Artifact must contain fifty member records")
    expected_member_ids = {row.get("member_id") for row in recorded_members}
    base_manifest = _json(ROOT / BASE_MANIFEST_PATH)
    manifest_member_ids = {
        row["member_id"] for row in base_manifest.get("physical_members", [])
    } | {row["part_id"] for row in base_manifest.get("candidate_blocks", [])}
    if len(expected_member_ids) != 50 or expected_member_ids != manifest_member_ids:
        raise ValueError("Artifact must contain the exact fifty unique full-frame members")
    expected_step_files = {f"{member_id}.step" for member_id in expected_member_ids}
    actual_step_files = {path.name for path in MEMBER_DIR.glob("*.step")}
    if actual_step_files != expected_step_files:
        raise ValueError("STEP directory contains missing or unregistered member files")
    actual_files = {
        path.relative_to(ARTIFACT_DIR).as_posix()
        for path in ARTIFACT_DIR.rglob("*")
        if path.is_file()
    }
    expected_files = {
        "current-full-frame-member-solids.json",
        *(f"members/{name}" for name in expected_step_files),
    }
    actual_dirs = {
        path.relative_to(ARTIFACT_DIR).as_posix()
        for path in ARTIFACT_DIR.rglob("*")
        if path.is_dir()
    }
    if actual_files != expected_files or actual_dirs != {"members"}:
        raise ValueError("Artifact bundle has unregistered files or directories")
    if recorded.get("schema") != "wood_joint_current_full_frame_member_solids/v1":
        raise ValueError("Artifact schema changed")
    if recorded.get("attempt_id") != "current-full-frame-member-solids-attempt01":
        raise ValueError("Artifact attempt identity changed")
    if recorded.get("status") != "source_replayed_member_solids_ready_for_input_use":
        raise ValueError("Artifact status does not support the member geometry claim")
    if recorded.get("roundtrip_tolerances") != {
        "bounds_mm": ROUNDTRIP_BOUNDS_TOLERANCE_MM,
        "volume_mm3": ROUNDTRIP_VOLUME_TOLERANCE_MM3,
        "symmetric_difference_volume_mm3": ROUNDTRIP_SYMMETRIC_DIFFERENCE_TOLERANCE_MM3,
    }:
        raise ValueError("Artifact round-trip tolerances changed")
    expected_readiness = {
        "all_50_finished_member_solids_exported": True,
        "source_geometry_replayed": True,
        "step_roundtrip_checked": True,
        "per_member_material_mapping_ready": False,
        "selected_structural_hardware_ready": False,
        "active_contact_and_attachment_model_ready": False,
        "full_frame_demands_available": False,
        "criterion_resolved": False,
        "native_solve_executed": False,
        "candidate_accepted": False,
        "fabrication_released": False,
        "climbing_released": False,
    }
    if recorded.get("readiness") != expected_readiness:
        raise ValueError("Artifact readiness or release claim changed")
    if recorded.get("release") != {
        "candidate_accepted": False,
        "fabrication_released": False,
        "climbing_released": False,
    }:
        raise ValueError("Artifact release flags must remain false")
    if recorded.get("claim_limits") != [
        "This package supplies exact current timber, panel and candidate-block STEP geometry only.",
        "It does not supply purchased hardware, full material frames, active connection transfer, or solver mappings.",
        "A STEP hash identifies the exported file; the shape-summary hash is a rounded geometric cross-check, not a kernel-canonical BRep hash.",
        "No mesh, mechanics solve, resistance check, acceptance, fabrication, or climbing release is included.",
    ]:
        raise ValueError("Artifact claim limits changed")
    geometry_source_counts = dict(
        Counter(row.get("geometry_source") for row in recorded_members)
    )
    if recorded.get("member_scope") != {
        "timber": 20,
        "plywood_panel": 6,
        "candidate_block": 24,
        "total": 50,
        "member_ids_unique": True,
        "geometry_source_counts": geometry_source_counts,
    }:
        raise ValueError("Artifact member scope changed")
    member_kind_counts = Counter(row.get("member_kind") for row in recorded_members)
    if member_kind_counts != Counter(
        {"timber": 20, "plywood_panel": 6, "candidate_block": 24}
    ):
        raise ValueError("Artifact member kind counts changed")
    expected_bundle_hash = _canonical_sha256(
        [
            {"member_id": row["member_id"], "step_sha256": row.get("step_sha256")}
            for row in recorded.get("members", [])
        ]
    )
    if recorded.get("member_bundle_sha256") != expected_bundle_hash:
        raise ValueError("Member bundle digest does not match its recorded STEP hashes")
    if recorded_members != sorted(recorded_members, key=lambda row: row["member_id"]):
        raise ValueError("Artifact member records are not in canonical ID order")
    rebuilt, source_shapes = _build_payload()
    for key in (
        "schema",
        "attempt_id",
        "candidate",
        "selected_candidate_preserved",
        "geometry_revision_id",
        "member_scope",
        "source_files_sha256",
        "geometry_source_inputs_sha256",
        "geometry_family_source_fingerprints",
    ):
        if rebuilt.get(key) != recorded.get(key):
            raise ValueError(f"Replayed full-frame member input differs: {key}")
    records = {row["member_id"]: row for row in recorded["members"]}
    rebuilt_records = {row["member_id"]: row for row in rebuilt["members"]}
    output_only_fields = {
        "step_file",
        "step_sha256",
        "step_size_bytes",
        "step_roundtrip_summary",
    }
    if set(records) != set(rebuilt_records):
        raise ValueError("Replayed full-frame member IDs differ from the written bundle")
    for member_id, record in records.items():
        source_record = {key: value for key, value in record.items() if key not in output_only_fields}
        if source_record != rebuilt_records[member_id]:
            raise ValueError(f"Replayed source member record differs: {member_id}")
        if record.get("step_file") != f"bundle/members/{member_id}.step":
            raise ValueError(f"{member_id}: registered STEP path changed")
        if not isinstance(record.get("step_size_bytes"), int) or record["step_size_bytes"] <= 0:
            raise ValueError(f"{member_id}: registered STEP file size is invalid")
        step_hash = record.get("step_sha256")
        if not isinstance(step_hash, str) or len(step_hash) != 64 or any(
            character not in "0123456789abcdef" for character in step_hash
        ):
            raise ValueError(f"{member_id}: registered STEP hash is invalid")
        if not isinstance(record.get("step_roundtrip_summary"), dict):
            raise ValueError(f"{member_id}: STEP readback summary is missing")
    readback_count = 0
    for index, member_id in enumerate(sorted(source_shapes), start=1):
        print(f"STEP verify {index}/50: {member_id}", flush=True)
        path = MEMBER_DIR / f"{member_id}.step"
        record = records[member_id]
        if path.stat().st_size != record.get("step_size_bytes"):
            raise ValueError(f"{member_id}: STEP file size differs")
        if _sha256_file(path) != record.get("step_sha256"):
            raise ValueError(f"{member_id}: STEP file hash differs")
        imported = _shape(importers.importStep(str(path)))
        summary = _require_shape(imported, member_id)
        _validate_roundtrip(member_id, source_shapes[member_id], imported, summary)
        if summary != record.get("step_roundtrip_summary"):
            raise ValueError(f"{member_id}: STEP readback summary changed")
        readback_count += 1
    if readback_count != 50:
        raise ValueError("Not all fifty member STEP files were read back")
    return _result(recorded, "verified")


def _result(payload: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "status": status,
        "artifact_sha256": payload.get("artifact_sha256"),
        "member_bundle_sha256": payload.get("member_bundle_sha256"),
        "candidate": payload.get("candidate"),
        "selected_candidate_preserved": payload.get("selected_candidate_preserved"),
        "geometry_revision_id": payload.get("geometry_revision_id"),
        "member_scope": payload.get("member_scope"),
        "step_roundtrip_checked": payload.get("readiness", {}).get("step_roundtrip_checked"),
        "native_solve_executed": payload.get("readiness", {}).get("native_solve_executed"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = _write_artifact() if args.write else _verify_artifact()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
