#!/usr/bin/env python3
"""Verify catalog-screen source pins, candidate identity, and axis coverage."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SCREEN_PATH = HERE / "catalog-screen.json"
REPORT_PATH = HERE / "verification.json"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    screen = json.loads(SCREEN_PATH.read_text())
    checks: dict[str, bool] = {}
    checks["schema_and_artifact_id"] = (
        screen.get("schema") == "wood_joint_current_bolt_catalog_screen/v1"
        and screen.get("artifact_id") == "current-bolt-catalog-screen-attempt01"
    )
    rows = screen["axis_rows"]
    axis_ids = [axis_id for row in rows for axis_id in row["axis_ids"]]
    checks["nine_rows_cover_92_unique_axes"] = (
        len(rows) == 9
        and sum(row["axis_count"] for row in rows) == 92
        and len(axis_ids) == 92
        and len(set(axis_ids)) == 92
    )
    products = {product["id"] for product in screen["products"]}
    checks["all_product_references_resolve"] = all(
        product_id in products for row in rows for product_id in row["product_ids"]
    )
    sources_match = True
    for pin in screen["source_pins"]:
        source_path = ROOT / pin["path"]
        if not source_path.is_file() or sha256(source_path) != pin["sha256"]:
            sources_match = False
    checks["all_local_source_hashes_match"] = sources_match

    grip_path = ROOT / screen["grip_screen_pin"]["path"]
    manifest_path = ROOT / screen["attempt02_manifest_pin"]["path"]
    grip = json.loads(grip_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    candidate_path = ROOT / screen["candidate_pin"]["lane_contract"]
    candidate = json.loads(candidate_path.read_text())
    source_axes = {axis["axis_id"]: axis for axis in grip["axes"]}
    checks["axis_ids_and_row_dimensions_match_grip_screen"] = (
        set(axis_ids) == set(source_axes)
        and all(
            abs(source_axes[axis_id]["modeled_underhead_to_tip_mm"] - row["modeled_underhead_to_tip_mm"]) < 0.01
            and abs(source_axes[axis_id]["wood_grip_material_length_mm"] - row["modeled_wood_grip_mm"]) < 0.01
            for row in rows for axis_id in row["axis_ids"]
        )
    )
    checks["candidate_revision_and_manifest_match"] = (
        grip["revision_id"] == screen["candidate_pin"]["geometry_revision_id"]
        == manifest["geometry_revision_id"]
        == candidate["current_development_revision"]["revision_id"]
        and manifest["candidate"] == screen["candidate_pin"]["lane_candidate"]
        == candidate["candidate"]
        and manifest["manifest_id"] == screen["attempt02_manifest_pin"]["manifest_id"]
        and manifest["manifest_sha256"] == screen["attempt02_manifest_pin"]["embedded_manifest_sha256"]
        and len(grip["axes"]) == manifest["inventory_counts"]["candidate_bolt_axes"] == 92
    )
    checks["disposition_remains_unselected_and_unreleased"] = (
        screen["disposition"]["product_selected"] is False
        and screen["disposition"]["sku_selected"] is None
        and screen["disposition"]["fit_qualified_candidate_axes"] == 0
        and screen["disposition"]["purchases_authorized"] is False
        and screen["disposition"]["hardware_acceptance"] is False
        and screen["disposition"]["candidate_accepted"] is False
        and screen["disposition"]["fabrication_released"] is False
        and screen["disposition"]["structural_released"] is False
        and screen["disposition"]["climbing_released"] is False
    )
    report = {
        "schema": "wood_joint_current_bolt_catalog_screen_verification/v1",
        "artifact_id": "current-bolt-catalog-screen-attempt01",
        "verified_on": "2026-09-27",
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "row_count": len(rows),
        "unique_axis_count": len(set(axis_ids)),
        "catalog_product_record_count": len(products),
        "catalog_screen_sha256": sha256(SCREEN_PATH),
        "verifier_sha256": sha256(Path(__file__)),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"Verification report: {REPORT_PATH.relative_to(ROOT)}")
    if not all(checks.values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
