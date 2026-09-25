"""Pure contract tests for the separate WJ24 five-body mesh adapter."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from fea import wood_joint_patch_mesh as old_mesh
from fea import wood_joint_wj24_patch_mesh as wj24_mesh


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _old_bundle_row():
    old_bundle = old_mesh.load_geometry_bundle(wj24_mesh.OLD_PATCH_DIR)
    contents = json.loads(
        (wj24_mesh.OLD_MESH_ARCHIVE_DIR / "bundle-contents.json").read_text()
    )
    member = contents[wj24_mesh.OLD_MESH_REPORT_MEMBER]
    return {
        "inventory_path": "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1/inventory.json",
        "inventory_sha256": old_bundle["inventory_sha256"],
        "step_sha256": old_bundle["step_sha256"],
        "old_mesh_report_archive_path": wj24_mesh.OLD_MESH_ARCHIVE_PATH,
        "old_mesh_report_member": wj24_mesh.OLD_MESH_REPORT_MEMBER,
        "old_mesh_report_member_bytes": member["bytes"],
        "old_mesh_report_sha256": member["sha256"],
        "old_mesh_archive_sha256": wj24_mesh.OLD_MESH_ARCHIVE_SHA256,
        "old_mesh_bundle_contents_path": wj24_mesh.OLD_MESH_CONTENTS_PATH,
        "old_mesh_bundle_contents_sha256": wj24_mesh.OLD_MESH_CONTENTS_SHA256,
        "old_mesh_input_sha256": wj24_mesh.OLD_MESH_INPUT_SHA256,
        "old_mesh_input_bundle_inventory_sha256": old_bundle["inventory_sha256"],
        "old_mesh_audit_status": "parent_deck_and_ownership_audit_passed",
        "old_mesh_audit_structural_solve_run": False,
    }


def _source_composition():
    wj24_path = wj24_mesh.ROOT / wj24_mesh.WJ24_COMPOSITION_PATH
    wj24_report = json.loads(wj24_path.read_text())
    return {
        "source_inventory_sha256": wj24_mesh.SOURCE_INVENTORY_SHA256,
        "shared_source_object": True,
        "WJ16": {
            "layout_id": wj24_mesh.WJ16_LAYOUT_ID,
            "trial_id": wj24_mesh.WJ16_TRIAL_ID,
            "report_path": wj24_mesh.WJ16_COMPOSITION_PATH,
            "report_sha256": wj24_mesh.WJ16_COMPOSITION_SHA256,
            "live_report_matches_archive": True,
        },
        "WJ24": {
            "layout_id": wj24_mesh.WJ24_LAYOUT_ID,
            "trial_id": wj24_mesh.WJ24_TRIAL_ID,
            "report_path": wj24_mesh.WJ24_COMPOSITION_PATH,
            "report_sha256": hashlib.sha256(wj24_path.read_bytes()).hexdigest(),
            "live_report_matches_archive": True,
        },
    }, wj24_report


def _make_synthetic_bundle(path: Path) -> Path:
    path.mkdir()
    (path / "wood").mkdir()
    source_composition, wj24_composition = _source_composition()
    old_inventory = json.loads(
        (wj24_mesh.OLD_PATCH_DIR / "inventory.json").read_text()
    )
    old_rows = {row["part_id"]: row for row in old_inventory["wood_bodies"]}
    comparisons = []
    artifacts = {}
    step_hashes = {}

    for body_id in wj24_mesh.BODY_IDS:
        old_shape = old_rows[body_id]["finished_geometry"]
        source_collection = (
            "shared_hosts" if body_id in wj24_mesh.HOST_BODY_IDS else "candidate_parts"
        )
        composition_shape = wj24_composition[source_collection][body_id]["finished_shape"]
        old_meta = copy.deepcopy(old_shape)
        if body_id == wj24_mesh.BODY_IDS[2]:
            new_centroid = [
                (composition_shape["bounds_xyz_mm"][0] + composition_shape["bounds_xyz_mm"][1]) / 2,
                (composition_shape["bounds_xyz_mm"][2] + composition_shape["bounds_xyz_mm"][3]) / 2,
                (composition_shape["bounds_xyz_mm"][4] + composition_shape["bounds_xyz_mm"][5]) / 2,
            ]
            new_meta = {
                "solid_count": 1,
                "volume_mm3": composition_shape["volume_mm3"],
                "centroid_global_xyz_mm": new_centroid,
                "bounds_xyz_mm": composition_shape["bounds_xyz_mm"],
                "cad_shape_sha256": composition_shape["shape_sha256"],
            }
            removed, added = 6732.825755725, 6944.063705184
        else:
            new_meta = copy.deepcopy(old_meta)
            removed, added = 0.0, 0.0
        comparisons.append(
            {
                "body_id": body_id,
                "geometry_role": wj24_mesh.EXPECTED_BODY_ROLES[body_id],
                "WJ16": old_meta,
                "WJ24": new_meta,
                "archived_WJ16_STEP_source_shape_sha256": old_meta["cad_shape_sha256"],
                "removed_from_WJ16_material_mm3": removed,
                "added_in_WJ24_material_mm3": added,
                "symmetric_difference_mm3": removed + added,
                "same_geometry_within_tolerance": removed + added <= 1e-3,
                "delta_solids": [],
                "cut_provenance_delta": {"WJ16": {}, "WJ24": {}}
                if body_id in wj24_mesh.HOST_BODY_IDS
                else None,
            }
        )
        step_bytes = f"synthetic but hash-indexed STEP body: {body_id}\n".encode()
        (path / "wood" / f"{body_id}.step").write_bytes(step_bytes)
        step_hash = hashlib.sha256(step_bytes).hexdigest()
        step_hashes[f"wood/{body_id}.step"] = step_hash
        readback = copy.deepcopy(new_meta)
        readback["cad_shape_sha256"] = hashlib.sha256(
            f"STEP round-trip signature: {body_id}".encode()
        ).hexdigest()
        allowed_difference = wj24_mesh.SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3 + (
            wj24_mesh.SYMMETRIC_DIFFERENCE_RELATIVE_TOLERANCE
            * new_meta["volume_mm3"]
        )
        artifacts[body_id] = {
            "file": f"{body_id}.step",
            "file_sha256": step_hash,
            "source_solid": new_meta,
            "step_readback_solid": readback,
            "identity_checks": {
                "solid_count": True,
                "volume": True,
                "centroid": True,
                "bounds": True,
                "symmetric_difference": {
                    "source_only_volume_mm3": 0.0,
                    "step_only_volume_mm3": 0.0,
                    "symmetric_difference_volume_mm3": 0.0,
                    "absolute_tolerance_mm3": wj24_mesh.SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3,
                    "relative_tolerance": wj24_mesh.SYMMETRIC_DIFFERENCE_RELATIVE_TOLERANCE,
                    "allowed_volume_difference_mm3": allowed_difference,
                    "passed": True,
                },
            },
        }

    report = {
        "schema": wj24_mesh.BUNDLE_SCHEMA,
        "status": wj24_mesh.BUNDLE_STATUS,
        "source_composition": source_composition,
        "old_WJ16_patch_bundle": _old_bundle_row(),
        "body_ids": list(wj24_mesh.BODY_IDS),
        "body_comparisons": comparisons,
        "step_artifacts": artifacts,
        "G7_relief_dependency": {
            "WJ24_LED_relief_is_in_baseline_composition": False,
            "WJ24_LED_relief_mutates_retained_composition": False,
            "mesh_variant_exported": False,
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
    report_bytes = _json_bytes(report)
    (path / "reconciliation.json").write_bytes(report_bytes)
    index = {
        "reconciliation.json": hashlib.sha256(report_bytes).hexdigest(),
        **step_hashes,
    }
    (path / "sha256.json").write_bytes(_json_bytes(index))
    return path


@pytest.fixture(scope="module")
def synthetic_bundle(tmp_path_factory):
    return _make_synthetic_bundle(tmp_path_factory.mktemp("wj24-input") / "bundle")


def _copy_bundle(source: Path, destination: Path) -> Path:
    return Path(shutil.copytree(source, destination))


def _refresh_report_hash(bundle: Path) -> None:
    report_bytes = (bundle / "reconciliation.json").read_bytes()
    index_path = bundle / "sha256.json"
    index = json.loads(index_path.read_text())
    index["reconciliation.json"] = hashlib.sha256(report_bytes).hexdigest()
    index_path.write_bytes(_json_bytes(index))


def test_source_bound_wj24_bundle_passes_without_importing_the_old_geometry_schema(
    synthetic_bundle,
):
    bundle = wj24_mesh.load_wj24_patch_bundle(synthetic_bundle)

    assert bundle["reconciliation_sha256"] == hashlib.sha256(
        (synthetic_bundle / "reconciliation.json").read_bytes()
    ).hexdigest()
    assert tuple(bundle["body_rows"]) == wj24_mesh.BODY_IDS
    assert bundle["body_rows"][wj24_mesh.BODY_IDS[2]][
        "WJ16_to_WJ24_geometry_comparison"
    ]["same_geometry_within_tolerance"] is False
    assert all(
        row["grain_frame"]["WJ24_material_frame_basis"]
        for row in bundle["body_rows"].values()
    )
    with pytest.raises(ValueError, match="inventory/hash files are missing or invalid"):
        old_mesh.load_geometry_bundle(synthetic_bundle)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda report: report.__setitem__("schema", "wood_joint_wj04_patch_geometry/v1"),
            "schema or comparison-only status changed",
        ),
        (
            lambda report: report["body_ids"].reverse(),
            "body IDs or order changed",
        ),
        (
            lambda report: report["body_comparisons"][2].__setitem__(
                "same_geometry_within_tolerance", True
            ),
            "same-geometry result is inconsistent",
        ),
        (
            lambda report: report["step_artifacts"][wj24_mesh.BODY_IDS[0]][
                "identity_checks"
            ].__setitem__("volume", False),
            "identity checks are incomplete",
        ),
        (
            lambda report: report["G7_relief_dependency"].__setitem__(
                "mesh_variant_exported", True
            ),
            "unexported G7 relief variant",
        ),
    ],
)
def test_reconciliation_rejects_schema_order_geometry_and_claim_mutations(
    synthetic_bundle, tmp_path, mutate, message
):
    bundle = _copy_bundle(synthetic_bundle, tmp_path / "bundle")
    report_path = bundle / "reconciliation.json"
    report = json.loads(report_path.read_text())
    mutate(report)
    report_path.write_bytes(_json_bytes(report))
    _refresh_report_hash(bundle)

    with pytest.raises(ValueError, match=message):
        wj24_mesh.load_wj24_patch_bundle(bundle)


def test_hash_index_and_exact_bundle_file_set_are_required(synthetic_bundle, tmp_path):
    bundle = _copy_bundle(synthetic_bundle, tmp_path / "bundle")
    index_path = bundle / "sha256.json"
    index = json.loads(index_path.read_text())
    index["wood/unexpected.step"] = "0" * 64
    index_path.write_bytes(_json_bytes(index))

    with pytest.raises(ValueError, match="hash index differs from the exact five-STEP"):
        wj24_mesh.load_wj24_patch_bundle(bundle)

    bundle = _copy_bundle(synthetic_bundle, tmp_path / "bundle-extra")
    (bundle / "wood" / "unindexed.step").write_bytes(b"extra")
    with pytest.raises(ValueError, match="file set differs from its exact five-STEP"):
        wj24_mesh.load_wj24_patch_bundle(bundle)


def test_exported_step_bytes_and_wj24_composition_shape_are_independently_bound(
    synthetic_bundle, tmp_path
):
    bundle = _copy_bundle(synthetic_bundle, tmp_path / "bundle")
    step_path = bundle / "wood" / f"{wj24_mesh.BODY_IDS[0]}.step"
    step_path.write_bytes(step_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="source-bound WJ24 STEP is missing or changed"):
        wj24_mesh.load_wj24_patch_bundle(bundle)

    bundle = _copy_bundle(synthetic_bundle, tmp_path / "bundle-shape")
    report_path = bundle / "reconciliation.json"
    report = json.loads(report_path.read_text())
    report["body_comparisons"][0]["WJ24"]["cad_shape_sha256"] = "0" * 64
    report_path.write_bytes(_json_bytes(report))
    _refresh_report_hash(bundle)
    with pytest.raises(ValueError, match="differs from current composition solid"):
        wj24_mesh.load_wj24_patch_bundle(bundle)


@pytest.mark.parametrize(
    ("global_size", "local_size", "band"),
    [(0, 1, 2), (10, 11, 2), (10, 1, float("inf")), (True, 1, 2)],
)
def test_mesh_size_contract_requires_explicit_finite_positive_values(
    global_size, local_size, band
):
    with pytest.raises((TypeError, ValueError)):
        wj24_mesh.validate_mesh_configuration(global_size, local_size, band)
