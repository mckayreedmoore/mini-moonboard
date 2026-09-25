"""Prepare independent C3D10 meshes from the source-bound WJ24 patch export.

This WJ24 adapter has a distinct input schema from the historical WJ04/WJ16
worker. It imports only the five WJ24 STEP bodies. It assigns no material,
contact, interface tie, load, restraint, strength result, or solver card.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import tarfile
from pathlib import Path
from typing import Any

from fea import wood_joint_patch_mesh as wood_mesh
from fea.stitch_joint_mesh import validate_ownership

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj24_patch_mesh/v1"
BUNDLE_SCHEMA = "wood_joint_wj24_patch_reconciliation/v1"
BUNDLE_STATUS = "source_bound_representative_WJ16_to_WJ24_geometry_comparison_only"
STATUS_VERIFIED = "VERIFIED_WJ24_C3D10_MESH_ONLY_NO_SOLVER"
LIMITS = (
    "Source-bound WJ24 finished-wood mesh preparation only; no material, contact, "
    "interface tie, load, restraint, native solve, strength result, or release claim."
)

BODY_IDS = (
    "base_rail_service_lower_right",
    "base_rail_service_upper_right",
    "base_principal_center_right",
    "wj04_lower_full_stock_cleat",
    "wj04_upper_g7_crosscut_full_stock_cleat",
)
HOST_BODY_IDS = frozenset(BODY_IDS[:3])
EXPECTED_BODY_ROLES = {
    BODY_IDS[0]: "finished_source_host",
    BODY_IDS[1]: "finished_source_host",
    BODY_IDS[2]: "finished_source_host",
    BODY_IDS[3]: "finished_candidate_part",
    BODY_IDS[4]: "finished_candidate_part",
}

WJ16_LAYOUT_ID = "wj16-sixteen-duty-left-service-composition-v1"
WJ16_TRIAL_ID = "wj16-wj12-plus-left-service-four-duty-v1"
WJ24_LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
WJ24_TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
SOURCE_INVENTORY_SHA256 = "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
WJ16_COMPOSITION_PATH = "docs/wood-joints-mvp/hypotheses/wj16-integrated-static/composition.json"
WJ16_COMPOSITION_SHA256 = "c0bc37fdbc364deafcbc86dc04e710d2f5b6809436e560717a97593951f8ebcb"
WJ24_COMPOSITION_PATH = "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
WJ24_HASHES_PATH = "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/sha256.json"
WJ24_PATCH_EXPORTER_PATH = "scripts/wood_joint_wj24_patch_reconciliation.py"
WJ24_PATCH_EXPORTER_SHA256 = "314bd2ebaad301f4a82eb6a6adcadaf18241ae61718b0f3e6490ba22032d280b"
OLD_PATCH_DIR = ROOT / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
OLD_MESH_ARCHIVE_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03"
OLD_MESH_ARCHIVE_PATH = (
    "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/complete-mesh-evidence.tar.gz"
)
OLD_MESH_CONTENTS_PATH = (
    "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/bundle-contents.json"
)
OLD_MESH_HASHES_PATH = "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/sha256.json"
OLD_MESH_AUDIT_PATH = "docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/parent-audit.json"
OLD_MESH_ARCHIVE_SHA256 = "b4a92cf5d0a76082bce736efe576dda1e8732924d4a19013501727ace7c63a58"
OLD_MESH_CONTENTS_SHA256 = "981b2524dce764796d4f83a72a6a44dda278300377ee04d92a9cf77d453a4456"
OLD_MESH_REPORT_SHA256 = "e8af81e6a92eb53b4ee72fcecc43efd9ed7ab901b3568be603509994c8b3c33c"
OLD_MESH_INPUT_SHA256 = "43f50fd605841821391f749ebddf226c639778945fef89b50ff78899c38afe56"
OLD_MESH_REPORT_MEMBER = "mesh.json"

RELATIVE_MESH_VOLUME_TOLERANCE = 0.001
METADATA_POSITION_TOLERANCE_MM = 1e-4
METADATA_VOLUME_RELATIVE_TOLERANCE = 1e-7
METADATA_VOLUME_ABSOLUTE_TOLERANCE_MM3 = 1e-5
SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3 = 1e-3
SYMMETRIC_DIFFERENCE_RELATIVE_TOLERANCE = 1e-9

WORKER_SOURCE_PATHS = (
    "fea/wood_joint_wj24_patch_mesh.py",
    "fea/wood_joint_patch_mesh.py",
    "fea/stitch_joint_mesh.py",
    "fea/floor_contact.py",
    WJ24_PATCH_EXPORTER_PATH,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_json(path: str | Path, record: Any) -> None:
    Path(path).write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def _read_json_bytes(data: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{context}: invalid JSON") from error
    if not isinstance(value, dict):
        raise TypeError(f"{context}: expected a JSON object")
    return value


def _read_json(path: Path, context: str) -> dict[str, Any]:
    try:
        return _read_json_bytes(path.read_bytes(), context)
    except OSError as error:
        raise ValueError(f"{context}: unavailable at {path}") from error


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context}: expected a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite number") from error
    if not math.isfinite(number):
        raise ValueError(f"{context}: expected a finite number")
    return number


def _finite_vector(value: Any, length: int, context: str) -> tuple[float, ...]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected {length} finite values") from error
    if len(result) != length or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected {length} finite values")
    return result


def _finite_positive(value: Any, context: str) -> float:
    number = _finite_number(value, context)
    if number <= 0:
        raise ValueError(f"{context}: expected a positive value")
    return number


def validate_mesh_configuration(
    global_max_size_mm: float,
    axis_local_size_mm: float,
    axis_refinement_band_mm: float,
) -> dict[str, float]:
    """Validate the explicit C3D10 mesh size and bore-refinement settings."""
    return wood_mesh.validate_mesh_configuration(
        global_max_size_mm, axis_local_size_mm, axis_refinement_band_mm
    )


def _validate_solid_metadata(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context}: solid metadata must be an object")
    if value.get("solid_count") != 1:
        raise ValueError(f"{context}: expected a single solid")
    _finite_positive(value.get("volume_mm3"), f"{context} volume")
    _finite_vector(value.get("centroid_global_xyz_mm"), 3, f"{context} centroid")
    bounds = _finite_vector(value.get("bounds_xyz_mm"), 6, f"{context} bounds")
    if any(bounds[index] > bounds[index + 1] for index in (0, 2, 4)):
        raise ValueError(f"{context}: inverted bounds")
    if not _is_sha256(value.get("cad_shape_sha256")):
        raise ValueError(f"{context}: invalid CAD shape fingerprint")
    return value


def _assert_metadata_equal(
    first: dict[str, Any],
    second: dict[str, Any],
    context: str,
    *,
    require_same_shape_sha: bool = True,
) -> None:
    _validate_solid_metadata(first, f"{context} first signature")
    _validate_solid_metadata(second, f"{context} second signature")
    if require_same_shape_sha and first["cad_shape_sha256"] != second["cad_shape_sha256"]:
        raise ValueError(f"{context}: source CAD shape fingerprints differ")
    if first["solid_count"] != second["solid_count"]:
        raise ValueError(f"{context}: source solid counts differ")
    volume_a = float(first["volume_mm3"])
    volume_b = float(second["volume_mm3"])
    allowed_volume_delta = METADATA_VOLUME_ABSOLUTE_TOLERANCE_MM3 + (
        max(volume_a, volume_b) * METADATA_VOLUME_RELATIVE_TOLERANCE
    )
    if abs(volume_a - volume_b) > allowed_volume_delta:
        raise ValueError(f"{context}: source solid volumes differ")
    for field, length in (("centroid_global_xyz_mm", 3), ("bounds_xyz_mm", 6)):
        values_a = _finite_vector(first[field], length, f"{context} first {field}")
        values_b = _finite_vector(second[field], length, f"{context} second {field}")
        if any(
            abs(a - b) > METADATA_POSITION_TOLERANCE_MM
            for a, b in zip(values_a, values_b, strict=True)
        ):
            raise ValueError(f"{context}: source solid {field} differ")


def _validate_old_mesh_lineage(old_bundle_row: Any) -> dict[str, Any]:
    if not isinstance(old_bundle_row, dict):
        raise TypeError("old WJ16 patch bundle lineage must be an object")
    expected = {
        "inventory_path": "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1/inventory.json",
        "inventory_sha256": wood_mesh.FROZEN_PATCH_INVENTORY_SHA256,
        "old_mesh_report_archive_path": OLD_MESH_ARCHIVE_PATH,
        "old_mesh_report_member": OLD_MESH_REPORT_MEMBER,
        "old_mesh_report_sha256": OLD_MESH_REPORT_SHA256,
        "old_mesh_archive_sha256": OLD_MESH_ARCHIVE_SHA256,
        "old_mesh_bundle_contents_path": OLD_MESH_CONTENTS_PATH,
        "old_mesh_bundle_contents_sha256": OLD_MESH_CONTENTS_SHA256,
        "old_mesh_input_sha256": OLD_MESH_INPUT_SHA256,
        "old_mesh_input_bundle_inventory_sha256": wood_mesh.FROZEN_PATCH_INVENTORY_SHA256,
        "old_mesh_audit_status": "parent_deck_and_ownership_audit_passed",
        "old_mesh_audit_structural_solve_run": False,
    }
    for key, value in expected.items():
        if old_bundle_row.get(key) != value:
            raise ValueError(f"WJ24 reconciliation old-mesh lineage changed: {key}")

    old_bundle = wood_mesh.load_geometry_bundle(OLD_PATCH_DIR)
    if old_bundle["inventory_sha256"] != old_bundle_row["inventory_sha256"]:
        raise ValueError("WJ24 reconciliation is not bound to the verified old WJ16 inventory")
    expected_steps = old_bundle_row.get("step_sha256")
    if not isinstance(expected_steps, dict) or expected_steps != old_bundle["step_sha256"]:
        raise ValueError("WJ24 reconciliation old WJ16 STEP lineage differs from its verified bundle")

    archive_path = ROOT / OLD_MESH_ARCHIVE_PATH
    contents_path = ROOT / OLD_MESH_CONTENTS_PATH
    hashes_path = ROOT / OLD_MESH_HASHES_PATH
    audit_path = ROOT / OLD_MESH_AUDIT_PATH
    if sha256_file(archive_path) != OLD_MESH_ARCHIVE_SHA256:
        raise ValueError("durable WJ16 mesh archive differs from its frozen source")
    if sha256_file(contents_path) != OLD_MESH_CONTENTS_SHA256:
        raise ValueError("durable WJ16 mesh contents index differs from its frozen source")
    archive_hashes = _read_json(hashes_path, "durable WJ16 mesh hash index")
    if (
        archive_hashes.get("complete-mesh-evidence.tar.gz") != OLD_MESH_ARCHIVE_SHA256
        or archive_hashes.get("bundle-contents.json") != OLD_MESH_CONTENTS_SHA256
    ):
        raise ValueError("durable WJ16 mesh outer hash index disagrees with its archive")
    contents = _read_json(contents_path, "durable WJ16 mesh bundle contents")
    member_record = contents.get(OLD_MESH_REPORT_MEMBER)
    if not isinstance(member_record, dict):
        raise TypeError("durable WJ16 mesh contents index lacks mesh.json")
    if (
        member_record.get("bytes") != old_bundle_row.get("old_mesh_report_member_bytes")
        or member_record.get("sha256") != OLD_MESH_REPORT_SHA256
    ):
        raise ValueError("WJ24 reconciliation old WJ16 mesh member signature changed")
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            matching = [
                member
                for member in archive.getmembers()
                if member.name == OLD_MESH_REPORT_MEMBER
            ]
            if len(matching) != 1 or not matching[0].isfile():
                raise ValueError("durable WJ16 mesh archive lacks one mesh.json member")
            member = matching[0]
            if member.size != member_record.get("bytes"):
                raise ValueError("durable WJ16 mesh archive member size differs from its index")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("durable WJ16 mesh report cannot be read")
            mesh_report_bytes = stream.read()
    except (OSError, tarfile.TarError) as error:
        raise ValueError("durable WJ16 mesh evidence archive is unreadable") from error
    if sha256_bytes(mesh_report_bytes) != OLD_MESH_REPORT_SHA256:
        raise ValueError("durable WJ16 mesh report member hash differs from its index")
    mesh_report = _read_json_bytes(mesh_report_bytes, "durable WJ16 mesh report")
    if (
        mesh_report.get("status") != "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER"
        or mesh_report.get("mesh_input_sha256") != OLD_MESH_INPUT_SHA256
        or mesh_report.get("input_bundle_inventory_sha256")
        != wood_mesh.FROZEN_PATCH_INVENTORY_SHA256
    ):
        raise ValueError("durable WJ16 mesh report is not the pinned historical mesh-only result")
    audit = _read_json(audit_path, "durable WJ16 parent deck audit")
    if audit.get("status") != old_bundle_row.get("old_mesh_audit_status"):
        raise ValueError("WJ24 reconciliation old WJ16 audit status differs from its source")
    if audit.get("structural_solve_run") is not False:
        raise ValueError("historical WJ16 mesh audit claims a structural solve")
    return old_bundle


def _validate_source_composition(source: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(source, dict):
        raise TypeError("WJ24 reconciliation source_composition must be an object")
    if source.get("source_inventory_sha256") != SOURCE_INVENTORY_SHA256:
        raise ValueError("WJ24 reconciliation source inventory differs from the pinned source")
    if source.get("shared_source_object") is not True:
        raise ValueError("WJ24 reconciliation lacks shared WJ16/WJ24 source-object identity")

    wj16_path = ROOT / WJ16_COMPOSITION_PATH
    wj16_hashes_path = wj16_path.with_name("sha256.json")
    wj16_hashes = _read_json(wj16_hashes_path, "WJ16 composition hash index")
    wj16_report = _read_json(wj16_path, "WJ16 composition report")
    actual_wj16_sha = sha256_file(wj16_path)
    if (
        wj16_hashes.get("composition.json") != WJ16_COMPOSITION_SHA256
        or actual_wj16_sha != WJ16_COMPOSITION_SHA256
    ):
        raise ValueError("archived WJ16 source composition hash changed")

    wj24_path = ROOT / WJ24_COMPOSITION_PATH
    wj24_hashes = _read_json(ROOT / WJ24_HASHES_PATH, "WJ24 composition hash index")
    wj24_report = _read_json(wj24_path, "WJ24 composition report")
    actual_wj24_sha = sha256_file(wj24_path)
    if wj24_hashes.get("composition.json") != actual_wj24_sha:
        raise ValueError("WJ24 composition hash index is stale")
    expected_rows = (
        (
            "WJ16",
            WJ16_LAYOUT_ID,
            WJ16_TRIAL_ID,
            WJ16_COMPOSITION_PATH,
            WJ16_COMPOSITION_SHA256,
            wj16_report,
        ),
        (
            "WJ24",
            WJ24_LAYOUT_ID,
            WJ24_TRIAL_ID,
            WJ24_COMPOSITION_PATH,
            actual_wj24_sha,
            wj24_report,
        ),
    )
    for key, layout_id, trial_id, report_path, report_sha, report in expected_rows:
        binding = source.get(key)
        if not isinstance(binding, dict):
            raise TypeError(f"WJ24 reconciliation {key} source binding must be an object")
        if any(
            binding.get(field) != expected
            for field, expected in (
                ("layout_id", layout_id),
                ("trial_id", trial_id),
                ("report_path", report_path),
                ("report_sha256", report_sha),
            )
        ):
            raise ValueError(f"WJ24 reconciliation {key} source binding changed")
        if binding.get("live_report_matches_archive") is not True:
            raise ValueError(f"WJ24 reconciliation {key} does not match its archived report")
        if report.get("layout_id") != layout_id or report.get("trial_id") != trial_id:
            raise ValueError(f"{key} composition report identity changed")
        report_source = report.get("source")
        if not isinstance(report_source, dict) or report_source.get(
            "source_inventory_sha256"
        ) != SOURCE_INVENTORY_SHA256:
            raise ValueError(f"{key} composition source inventory binding changed")
    return wj16_report, wj24_report


def _validate_step_identity(
    artifact: Any,
    expected_step_hash: Any,
    step_path: Path,
    context: str,
) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise TypeError(f"{context}: STEP artifact must be an object")
    if artifact.get("file") != f"{context}.step":
        raise ValueError(f"{context}: STEP filename binding changed")
    artifact_hash = artifact.get("file_sha256")
    if not _is_sha256(artifact_hash) or artifact_hash != expected_step_hash:
        raise ValueError(f"{context}: STEP artifact and SHA index differ")
    if not step_path.is_file() or sha256_file(step_path) != artifact_hash:
        raise ValueError(f"{context}: source-bound WJ24 STEP is missing or changed")
    source = _validate_solid_metadata(artifact.get("source_solid"), f"{context} STEP source")
    readback = _validate_solid_metadata(
        artifact.get("step_readback_solid"), f"{context} STEP readback"
    )
    checks = artifact.get("identity_checks")
    if not isinstance(checks, dict) or any(
        checks.get(key) is not True
        for key in ("solid_count", "volume", "centroid", "bounds")
    ):
        raise ValueError(f"{context}: STEP round-trip identity checks are incomplete")
    symmetric = checks.get("symmetric_difference")
    if not isinstance(symmetric, dict) or symmetric.get("passed") is not True:
        raise ValueError(f"{context}: STEP round-trip symmetric difference did not pass")
    source_only = _finite_number(
        symmetric.get("source_only_volume_mm3"), f"{context} source-only difference"
    )
    step_only = _finite_number(
        symmetric.get("step_only_volume_mm3"), f"{context} STEP-only difference"
    )
    difference = _finite_number(
        symmetric.get("symmetric_difference_volume_mm3"),
        f"{context} symmetric difference",
    )
    allowed = _finite_number(
        symmetric.get("allowed_volume_difference_mm3"),
        f"{context} allowed symmetric difference",
    )
    if min(source_only, step_only, difference, allowed) < 0:
        raise ValueError(f"{context}: STEP symmetric-difference values must be nonnegative")
    if not math.isclose(
        source_only + step_only,
        difference,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ) or difference > allowed:
        raise ValueError(f"{context}: STEP symmetric-difference values are inconsistent")
    expected_allowed = SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3 + (
        SYMMETRIC_DIFFERENCE_RELATIVE_TOLERANCE
        * max(float(source["volume_mm3"]), float(readback["volume_mm3"]))
    )
    if not math.isclose(allowed, expected_allowed, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"{context}: STEP symmetric-difference tolerance changed")
    _assert_metadata_equal(
        source,
        readback,
        f"{context} STEP round-trip",
        require_same_shape_sha=False,
    )
    return source


def _validate_body_comparisons(
    report: dict[str, Any],
    hashes: dict[str, Any],
    bundle_directory: Path,
    old_bundle: dict[str, Any],
    wj24_composition: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if report.get("body_ids") != list(BODY_IDS):
        raise ValueError("WJ24 reconciliation body IDs or order changed")
    comparisons = report.get("body_comparisons")
    if not isinstance(comparisons, list) or [row.get("body_id") for row in comparisons if isinstance(row, dict)] != list(BODY_IDS):
        raise ValueError("WJ24 reconciliation must contain its exact five ordered body comparisons")
    artifacts = report.get("step_artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(BODY_IDS):
        raise ValueError("WJ24 reconciliation STEP artifact IDs changed")

    old_rows = {
        row["part_id"]: row
        for row in old_bundle["inventory"]["wood_bodies"]
    }
    body_rows: dict[str, dict[str, Any]] = {}
    step_hashes: dict[str, dict[str, Any]] = {}
    for comparison, body_id in zip(comparisons, BODY_IDS, strict=True):
        expected_role = EXPECTED_BODY_ROLES[body_id]
        if comparison.get("geometry_role") != expected_role:
            raise ValueError(f"{body_id}: source/candidate role changed")
        old_meta = _validate_solid_metadata(comparison.get("WJ16"), f"{body_id} WJ16 source")
        new_meta = _validate_solid_metadata(comparison.get("WJ24"), f"{body_id} WJ24 source")
        shape_collection = "shared_hosts" if body_id in HOST_BODY_IDS else "candidate_parts"
        composition_rows = wj24_composition.get(shape_collection)
        composition_part = (
            composition_rows.get(body_id) if isinstance(composition_rows, dict) else None
        )
        composition_shape = (
            composition_part.get("finished_shape")
            if isinstance(composition_part, dict)
            else None
        )
        if not isinstance(composition_shape, dict):
            raise TypeError(f"{body_id}: WJ24 composition has no finished-solid signature")
        if (
            composition_shape.get("shape_sha256") != new_meta["cad_shape_sha256"]
            or abs(
                _finite_positive(composition_shape.get("volume_mm3"), f"{body_id} WJ24 composition volume")
                - float(new_meta["volume_mm3"])
            ) > 1e-3
        ):
            raise ValueError(f"{body_id}: WJ24 reconciliation differs from current composition solid")
        composition_bounds = _finite_vector(
            composition_shape.get("bounds_xyz_mm"), 6, f"{body_id} WJ24 composition bounds"
        )
        source_bounds = _finite_vector(
            new_meta["bounds_xyz_mm"], 6, f"{body_id} WJ24 comparison bounds"
        )
        if any(
            abs(a - b) > METADATA_POSITION_TOLERANCE_MM
            for a, b in zip(composition_bounds, source_bounds, strict=True)
        ):
            raise ValueError(f"{body_id}: WJ24 reconciliation bounds differ from current composition")
        old_hash = old_rows[body_id]["finished_geometry"]["cad_shape_sha256"]
        if (
            old_meta["cad_shape_sha256"] != old_hash
            or comparison.get("archived_WJ16_STEP_source_shape_sha256") != old_hash
        ):
            raise ValueError(f"{body_id}: WJ16 comparison does not match archived WJ16 source")
        _assert_metadata_equal(
            old_meta,
            old_rows[body_id]["finished_geometry"],
            f"{body_id} WJ16 comparison and archived STEP source",
        )
        removed = _finite_number(
            comparison.get("removed_from_WJ16_material_mm3"),
            f"{body_id} removed WJ16 volume",
        )
        added = _finite_number(
            comparison.get("added_in_WJ24_material_mm3"),
            f"{body_id} added WJ24 volume",
        )
        total_difference = _finite_number(
            comparison.get("symmetric_difference_mm3"),
            f"{body_id} WJ16/WJ24 symmetric difference",
        )
        if min(removed, added, total_difference) < 0 or not math.isclose(
            removed + added,
            total_difference,
            rel_tol=0,
            abs_tol=1e-6,
        ):
            raise ValueError(f"{body_id}: WJ16/WJ24 volume-difference record is inconsistent")
        same_geometry = total_difference <= SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3
        if comparison.get("same_geometry_within_tolerance") is not (
            same_geometry
        ):
            raise ValueError(f"{body_id}: WJ16/WJ24 same-geometry result is inconsistent")
        if same_geometry:
            _assert_metadata_equal(old_meta, new_meta, f"{body_id} unchanged WJ16/WJ24 geometry")

        artifact = artifacts[body_id]
        new_meta_from_step = _validate_step_identity(
            artifact,
            hashes.get(f"wood/{body_id}.step"),
            bundle_directory / "wood" / f"{body_id}.step",
            body_id,
        )
        _assert_metadata_equal(
            new_meta,
            new_meta_from_step,
            f"{body_id} WJ24 comparison and exported STEP source",
        )

        grain_frame = old_rows[body_id].get("grain_frame")
        if not isinstance(grain_frame, dict):
            raise TypeError(f"{body_id}: source-stock grain frame is missing")
        grain_name = grain_frame.get("grain_axis_local_name")
        if grain_name not in {"X", "T", "N"}:
            raise ValueError(f"{body_id}: source-stock grain axis is invalid")
        grain_vector = _finite_vector(
            grain_frame.get("grain_axis_global_xyz"), 3, f"{body_id} grain direction"
        )
        if not math.isclose(
            math.sqrt(math.fsum(value * value for value in grain_vector)),
            1.0,
            rel_tol=0,
            abs_tol=1e-8,
        ):
            raise ValueError(f"{body_id}: source-stock grain direction is not unit length")
        local_axes = grain_frame.get("local_axes_global_xyz")
        if not isinstance(local_axes, dict) or grain_name not in local_axes:
            raise ValueError(f"{body_id}: explicit source-stock local frame is incomplete")
        local_grain = _finite_vector(
            local_axes[grain_name], 3, f"{body_id} local grain frame axis"
        )
        if any(abs(a - b) > 1e-8 for a, b in zip(grain_vector, local_grain, strict=True)):
            raise ValueError(f"{body_id}: source-stock grain axis disagrees with its local frame")
        body_rows[body_id] = {
            "part_id": body_id,
            "geometry_role": expected_role,
            "WJ24_finished_geometry": new_meta,
            "WJ16_to_WJ24_geometry_comparison": {
                key: comparison[key]
                for key in (
                    "same_geometry_within_tolerance",
                    "removed_from_WJ16_material_mm3",
                    "added_in_WJ24_material_mm3",
                    "symmetric_difference_mm3",
                    "cut_provenance_delta",
                )
            },
            "grain_frame": {
                **grain_frame,
                "WJ24_material_frame_basis": (
                    "source-stock orientation carried through the same canonical source "
                    "inventory SHA; only the finished solid geometry is WJ24-specific"
                ),
            },
        }
        step_hashes[body_id] = {
            "step_sha256": artifact["file_sha256"],
            "WJ24_cad_shape_sha256": new_meta["cad_shape_sha256"],
        }

    return body_rows, step_hashes


def _expected_bundle_files() -> set[str]:
    return {"reconciliation.json", "sha256.json"} | {
        f"wood/{body_id}.step" for body_id in BODY_IDS
    }


def load_wj24_patch_bundle(directory: str | Path) -> dict[str, Any]:
    """Validate the exact WJ24 reconciliation export and all five STEP files."""
    source = Path(directory).expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"WJ24 representative input bundle is unavailable: {source}")
    actual_files = {
        str(path.relative_to(source)) for path in source.rglob("*") if path.is_file()
    }
    if actual_files != _expected_bundle_files():
        raise ValueError("WJ24 representative bundle file set differs from its exact five-STEP schema")
    report_bytes = (source / "reconciliation.json").read_bytes()
    hash_index_bytes = (source / "sha256.json").read_bytes()
    report = _read_json_bytes(report_bytes, "WJ24 reconciliation report")
    hashes = _read_json_bytes(hash_index_bytes, "WJ24 reconciliation SHA-256 index")
    if not isinstance(hashes, dict) or set(hashes) != _expected_bundle_files() - {"sha256.json"}:
        raise ValueError("WJ24 reconciliation hash index differs from the exact five-STEP file set")
    if any(not _is_sha256(value) for value in hashes.values()):
        raise ValueError("WJ24 reconciliation hash index contains an invalid SHA-256 value")
    if hashes.get("reconciliation.json") != sha256_bytes(report_bytes):
        raise ValueError("WJ24 reconciliation report digest differs from its hash index")
    if report.get("schema") != BUNDLE_SCHEMA or report.get("status") != BUNDLE_STATUS:
        raise ValueError("WJ24 reconciliation schema or comparison-only status changed")
    exporter_path = ROOT / WJ24_PATCH_EXPORTER_PATH
    if (
        not exporter_path.is_file()
        or sha256_file(exporter_path) != WJ24_PATCH_EXPORTER_SHA256
    ):
        raise ValueError("WJ24 patch exporter source differs from the frozen export")

    source_composition = report.get("source_composition")
    _wj16_composition, wj24_composition = _validate_source_composition(source_composition)
    old_bundle = _validate_old_mesh_lineage(report.get("old_WJ16_patch_bundle"))
    relief = report.get("G7_relief_dependency")
    if not isinstance(relief, dict) or any(
        relief.get(key) is not False
        for key in (
            "WJ24_LED_relief_is_in_baseline_composition",
            "WJ24_LED_relief_mutates_retained_composition",
            "mesh_variant_exported",
        )
    ):
        raise ValueError("WJ24 baseline reconciliation includes an unexported G7 relief variant")
    limits = report.get("limits")
    if not isinstance(limits, dict) or any(
        limits.get(key) is not False
        for key in (
            "native_solve_run",
            "mesh_generated",
            "contact_law_assigned",
            "capacity_established",
            "fabrication_released",
            "structural_released",
        )
    ):
        raise ValueError("WJ24 reconciliation claim boundary changed")

    body_rows, step_hashes = _validate_body_comparisons(
        report, hashes, source, old_bundle, wj24_composition
    )
    return {
        "path": source,
        "reconciliation": report,
        "reconciliation_sha256": hashes["reconciliation.json"],
        "hash_index_sha256": sha256_bytes(hash_index_bytes),
        "step_sha256": step_hashes,
        "body_rows": body_rows,
        "source_composition": source_composition,
        "input_file_sha256": {
            "reconciliation.json": hashes["reconciliation.json"],
            "sha256.json": sha256_bytes(hash_index_bytes),
            **{
                f"wood/{body_id}.step": hashes[f"wood/{body_id}.step"]
                for body_id in BODY_IDS
            },
        },
    }


def _source_paths() -> dict[str, Path]:
    return {relative: ROOT / relative for relative in WORKER_SOURCE_PATHS}


def snapshot_sources(output: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative, path in _source_paths().items():
        data = path.read_bytes()
        digest = sha256_bytes(data)
        target = output / "sources" / f"{relative}.snapshot"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[relative] = digest
    if hashes[WJ24_PATCH_EXPORTER_PATH] != WJ24_PATCH_EXPORTER_SHA256:
        raise ValueError("WJ24 patch exporter source differs from the frozen export")
    return hashes


def verify_sources(source_hashes: dict[str, str]) -> None:
    for relative, path in _source_paths().items():
        if not path.is_file() or sha256_file(path) != source_hashes[relative]:
            raise ValueError(f"WJ24 mesh preparation source changed during run: {relative}")


def verify_input_bundle(bundle: dict[str, Any]) -> None:
    current = load_wj24_patch_bundle(bundle["path"])
    if current["input_file_sha256"] != bundle["input_file_sha256"]:
        raise ValueError("WJ24 reconciliation report, hash index, or STEP changed during meshing")


def _write_input_deck(path: Path, nodes: dict[int, tuple[float, float, float]], elements: dict[int, tuple[int, ...]], bodies: dict[str, Any]) -> None:
    lines = ["*HEADING", LIMITS, "*NODE"]
    lines.extend(
        f"{node}," + ",".join(map(repr, xyz)) for node, xyz in nodes.items()
    )
    for body_id, body in bodies.items():
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={body_id.upper()}")
        lines.extend(
            f"{element}," + ",".join(map(str, elements[element]))
            for element in body["elements"]
        )
    path.write_text("\n".join(lines) + "\n")


def prepare_wj24_patch_mesh(
    bundle_directory: str | Path,
    output_directory: str | Path,
    *,
    global_max_size_mm: float,
    axis_local_size_mm: float,
    axis_refinement_band_mm: float,
) -> Path:
    """Mesh a frozen WJ24 five-body STEP bundle in independent Gmsh models."""
    settings = validate_mesh_configuration(
        global_max_size_mm, axis_local_size_mm, axis_refinement_band_mm
    )
    source_directory = Path(bundle_directory).expanduser().resolve()
    requested_output = Path(output_directory).expanduser().absolute()
    if requested_output.exists() or requested_output.is_symlink():
        raise FileExistsError(f"WJ24 mesh output directory already exists: {requested_output}")
    output = requested_output.resolve(strict=False)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"WJ24 mesh output directory already exists: {output}")
    if (
        output == source_directory
        or output.is_relative_to(source_directory)
        or source_directory.is_relative_to(output)
    ):
        raise ValueError("WJ24 mesh output and frozen input bundle directories must be separate")
    output.mkdir(parents=True, exist_ok=False)

    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    bodies: dict[str, dict[str, Any]] = {}
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PREPARING_WJ24_MESH_ONLY",
        "limits": LIMITS,
        "input_bundle_directory": str(source_directory),
        "configuration": settings,
        "accepted": False,
        "solved": False,
        "WJ16_mesh_geometry_reused": False,
        "WJ24_G7_relief_variant_included": False,
        "contact_or_interface_classification_assigned": False,
        "full_candidate_acceptance_claim": False,
    }
    write_json(output / "mesh.json", record)
    gmsh = None
    initialized = False
    active_body_id: str | None = None
    try:
        source_hashes = snapshot_sources(output)
        bundle = load_wj24_patch_bundle(source_directory)
        record.update(
            {
                "input_bundle_reconciliation_sha256": bundle["reconciliation_sha256"],
                "input_bundle_hash_index_sha256": bundle["hash_index_sha256"],
                "input_bundle_file_sha256_before": bundle["input_file_sha256"],
                "mesh_worker_source_sha256": source_hashes,
                "runtime": {"python": platform.python_version()},
                "mesh_scope": {
                    "WJ24_finished_wood_bodies": len(BODY_IDS),
                    "physical_bolts": 8,
                    "hardware_bodies_meshed": 0,
                    "independent_body_models": len(BODY_IDS),
                    "WJ24_baseline_only": True,
                },
                "WJ24_composition_binding": bundle["source_composition"],
                "WJ16_to_WJ24_reconciliation_sha256": bundle["reconciliation_sha256"],
                "source_geometry_context": {
                    "mesh_geometry": "WJ24 baseline finished solids from the five STEP artifacts",
                    "old_WJ16_mesh_is_lineage_only": True,
                    "G7_LED_relief_variant_exported": False,
                    "contact_classification": (
                        "pending; CAD face tags are transient and are not interface identities"
                    ),
                    "bodies": [bundle["body_rows"][body_id] for body_id in BODY_IDS],
                },
                "output_contains_material_contact_tie_load_or_solver_cards": False,
            }
        )
        write_json(output / "mesh.json", record)

        import gmsh as gmsh_module
        import numpy

        gmsh = gmsh_module
        if gmsh.isInitialized():
            raise ValueError("independent Gmsh session required for WJ24 patch mesh preparation")
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Verbosity", 2)
        for body_id in BODY_IDS:
            active_body_id = body_id
            body_row = bundle["body_rows"][body_id]
            mesh_source_row = {
                "part_id": body_id,
                "finished_geometry": body_row["WJ24_finished_geometry"],
                "grain_frame": body_row["grain_frame"],
            }
            body_record = wood_mesh._mesh_body(
                gmsh,
                source_directory,
                mesh_source_row,
                settings,
                nodes,
                elements,
            )
            body_record["part_id"] = body_id
            body_record["geometry_role"] = body_row["geometry_role"]
            body_record["grain_frame"] = body_row["grain_frame"]
            body_record["WJ24_finished_geometry"] = body_row[
                "WJ24_finished_geometry"
            ]
            body_record["WJ16_to_WJ24_geometry_comparison"] = body_row[
                "WJ16_to_WJ24_geometry_comparison"
            ]
            bodies[body_id] = body_record
            record["completed_body_ids"] = list(bodies)
            record["completed_node_count"] = len(nodes)
            record["completed_element_count"] = len(elements)
            record["bodies"] = bodies
            write_json(output / "mesh.json", record)
            gmsh.model.remove()
            active_body_id = None
        if len(bodies) != len(BODY_IDS):
            raise ValueError("WJ24 patch mesh did not contain exactly five independent bodies")
        record["runtime"].update(
            {"gmsh_version": str(gmsh.__version__), "numpy_version": str(numpy.__version__)}
        )
        gmsh.finalize()
        initialized = False

        validate_ownership(nodes, elements, bodies)
        verify_input_bundle(bundle)
        verify_sources(source_hashes)
        deck = output / "mesh.inp"
        _write_input_deck(deck, nodes, elements, bodies)
        record.update(
            {
                "status": STATUS_VERIFIED,
                "body_count": len(bodies),
                "node_count": len(nodes),
                "element_count": len(elements),
                "bodies": bodies,
                "mesh_input_sha256": sha256_file(deck),
                "input_bundle_file_sha256_after": bundle["input_file_sha256"],
                "mesh_worker_source_sha256_after": source_hashes,
                "output_contains_material_contact_tie_load_or_solver_cards": False,
                "contact_or_interface_classification_assigned": False,
                "WJ16_mesh_geometry_reused": False,
                "WJ24_G7_relief_variant_included": False,
                "capacity_or_release_claim": False,
            }
        )
        write_json(output / "mesh.json", record)
        return output
    except Exception as error:
        failed_model = None
        if initialized and gmsh is not None and active_body_id is not None:
            try:
                failed_model = wood_mesh.preserve_failed_gmsh_model(
                    gmsh, output, active_body_id
                )
            except Exception as capture_error:  # noqa: BLE001 - preserve original mesh failure
                failed_model = {
                    "body_id": active_body_id,
                    "status": "capture_failed",
                    "capture_error": f"{type(capture_error).__name__}: {capture_error}",
                    "file": None,
                    "sha256": None,
                }
        record.update(
            {
                "status": "FAILED_WJ24_MESH_PREPARATION_NO_SOLVER",
                "error": f"{type(error).__name__}: {error}",
                "completed_body_ids": list(bodies),
                "completed_node_count": len(nodes),
                "completed_element_count": len(elements),
                "bodies": bodies,
                "failed_gmsh_model": failed_model,
            }
        )
        try:
            write_json(output / "mesh.json", record)
        except Exception as report_error:  # noqa: BLE001 - preserve the original error
            error.add_note(
                f"Could not update WJ24 mesh failure record: {type(report_error).__name__}: {report_error}"
            )
        raise
    finally:
        if initialized and gmsh is not None:
            gmsh.finalize()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--global-max-size-mm", type=float, required=True)
    parser.add_argument("--axis-local-size-mm", type=float, required=True)
    parser.add_argument("--axis-refinement-band-mm", type=float, required=True)
    args = parser.parse_args()
    output = prepare_wj24_patch_mesh(
        args.bundle_directory,
        args.output_directory,
        global_max_size_mm=args.global_max_size_mm,
        axis_local_size_mm=args.axis_local_size_mm,
        axis_refinement_band_mm=args.axis_refinement_band_mm,
    )
    print(output, flush=True)


if __name__ == "__main__":
    main()
