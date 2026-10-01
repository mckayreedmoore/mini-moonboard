#!/usr/bin/env python3
"""Verify the frozen inputs and null-preserving panel crosswalk evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ATTEMPT_DIR = Path(__file__).resolve().parent
STATUS_PATH = ATTEMPT_DIR / "crosswalk-status.json"
PINS_PATH = ATTEMPT_DIR / "source-pins.sha256"
TERMINAL_PATH = ATTEMPT_DIR / "terminal-hashes.sha256"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_repository_root() -> Path:
    for candidate in (ATTEMPT_DIR, *ATTEMPT_DIR.parents):
        if (candidate / "AGENTS.md").is_file() and (
            candidate / "docs/wood-joints-mvp/current-material-map-status-2026-09-27.md"
        ).is_file():
            return candidate
    raise ValueError("could not locate repository root from attempt directory")


def read_pins(root: Path) -> int:
    count = 0
    for line_number, raw_line in enumerate(PINS_PATH.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        require(len(parts) == 2, f"malformed source pin line {line_number}")
        expected, relative_path = parts
        path = root / relative_path
        require(path.is_file(), f"pinned source is missing: {relative_path}")
        actual = sha256(path)
        require(actual == expected, f"source hash mismatch: {relative_path}")
        count += 1
    require(count > 0, "no source pins were checked")
    return count


def read_terminal_hashes(root: Path) -> int:
    count = 0
    for line_number, raw_line in enumerate(TERMINAL_PATH.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        require(len(parts) == 2, f"malformed terminal hash line {line_number}")
        expected, relative_path = parts
        path = root / relative_path
        require(path.is_file(), f"terminal artifact is missing: {relative_path}")
        actual = sha256(path)
        require(actual == expected, f"terminal artifact hash mismatch: {relative_path}")
        count += 1
    require(count > 0, "no terminal artifact hashes were checked")
    return count


def main() -> int:
    root = find_repository_root()
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    pin_count = read_pins(root)
    terminal_count = read_terminal_hashes(root)

    require(
        status["attempt"] == "current-plywood-product-crosswalk-attempt03",
        "attempt identity must remain attempt03",
    )

    require(status["material_assignment_complete"] is False, "material assignment must remain incomplete")
    require(status["solver_material_cards_created"] is False, "solver material cards must remain absent")
    require(status["solver_assignment_created"] is False, "solver assignments must remain absent")
    require(status["native_run"] is False, "native_run must remain false")
    require(status["physical_receiving_performed"] is False, "physical receiving must remain false")
    require(status["physical_inspection_claimed"] is False, "physical inspection must not be claimed")
    require(status["inputs_ready_claimed"] is False, "inputs_ready must not be claimed")
    require(status["release_changed"] is False, "release state must remain unchanged")

    conditional = status["standard_context"]["conditional_table_4_constraint"]
    require(conditional["minimum_plies"] == 5, "conditional Table 4 minimum must be five plies")
    require(conditional["minimum_layers"] == 5, "conditional Table 4 minimum must be five layers")
    require(conditional["exact_veneer_sequence"] is None, "exact veneer sequence must stay null")
    require(
        conditional["assignment_to_lowe_model_or_panels"] is None,
        "Table 4 minimum must not be assigned to the retailer model or panels",
    )
    excerpt_path = root / conditional["excerpt_path"]
    require(excerpt_path.is_file(), "the bounded PS 1-09 Table 4 excerpt is missing")
    require(
        sha256(excerpt_path) == conditional["excerpt_sha256"],
        "PS 1-09 Table 4 excerpt hash differs from the status record",
    )
    excerpt_text = excerpt_path.read_text(encoding="utf-8")
    for required_text in (
        "Section 5.8, Table 4",
        "Exterior; A-A, A-B, A-C, B-B, B-C",
        "Over 1/2 through 7/8",
        "Minimum plies",
        "Minimum layers",
        "at least 5 plies and 5 layers",
    ):
        require(required_text in excerpt_text, f"Table 4 excerpt is missing: {required_text}")

    review = status["standards_correction_review"]
    for path_key, hash_key in (
        ("review_report_path", "review_report_sha256"),
        ("review_integrity_manifest_path", "review_integrity_manifest_sha256"),
        ("review_checksum_path", "review_checksum_sha256"),
    ):
        review_path = root / review[path_key]
        require(review_path.is_file(), f"pinned independent-review file is missing: {review[path_key]}")
        require(sha256(review_path) == review[hash_key], f"independent-review hash mismatch: {review[path_key]}")

    manufacturer = status["manufacturer_product_record"]
    require(
        manufacturer["direct_reference_to_lowes_item_12235_or_model_119055"] is None,
        "manufacturer-to-retailer direct reference must stay null",
    )
    require(manufacturer["exact_model_layup"] is None, "exact model layup must stay null")
    require(manufacturer["exact_model_property_record"] is None, "exact model property record must stay null")

    manifest_path = root / status["geometry_binding"]["manifest_path"]
    require(manifest_path.is_file(), "current full-frame manifest is missing")
    manifest_digest = sha256(manifest_path)
    require(
        manifest_digest == status["geometry_binding"]["manifest_sha256"],
        "manifest hash differs from the attempt pin",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_rows = {
        row["member_id"]: row
        for row in manifest["finished_member_step_bindings"]
        if row["member_kind"] == "plywood_panel"
    }
    actual_rows = {row["body_id"]: row for row in status["geometry_binding"]["panels"]}
    require(len(expected_rows) == 6, "manifest must contain six plywood panel bodies")
    require(set(actual_rows) == set(expected_rows), "panel body IDs differ from the manifest")

    for body_id, panel in actual_rows.items():
        source = expected_rows[body_id]
        require(panel["step_path"] == source["path"], f"STEP path mismatch for {body_id}")
        require(panel["step_sha256"] == source["file_sha256"], f"STEP manifest hash mismatch for {body_id}")
        step_path = root / panel["step_path"]
        require(step_path.is_file(), f"STEP file is missing for {body_id}")
        require(sha256(step_path) == panel["step_sha256"], f"STEP file hash mismatch for {body_id}")
        for field in (
            "physical_sheet_id",
            "model_119055_crosswalk",
            "layup",
            "principal_axis_global",
            "orthotropic_properties",
            "solver_assignment",
        ):
            require(panel[field] is None, f"{field} must remain null for {body_id}")

    properties = status["field_status"]["orthotropic_properties"]
    for field in ("E_L", "E_T", "G_LT", "poisson_ratios", "strengths", "density"):
        require(properties[field] is None, f"{field} must remain null")

    fields = status["field_status"]
    identity = fields["product_identity"]
    for field in ("retailer_model_to_roseburg_product_crosswalk", "delivered_sheet_identity", "lot_or_mill_identity"):
        require(identity[field] is None, f"product identity field {field} must remain null")
    for field in ("received_panel_mark_values", "span_rating", "species_group", "structural_i"):
        require(fields["thickness_grade_rating"][field] is None, f"received-mark/rating field {field} must remain null")
    construction = fields["construction_layup"]
    for field in ("directly_linked_to_model_119055", "exact_veneer_species_by_ply", "exact_veneer_thickness_by_ply", "exact_veneer_sequence"):
        require(construction[field] is None, f"construction field {field} must remain null")
    require(construction["product_layup_assigned_to_current_bodies"] is False, "no product layup may be assigned to bodies")
    axes = fields["principal_axis_orientation"]
    for field in ("actual_mark_or_orientation_for_model", "sheet_to_body_orientation", "global_principal_axis_by_body"):
        require(axes[field] is None, f"principal-axis field {field} must remain null")
    solver = fields["solver_assignment"]
    for field in ("material_card", "solver_body_map", "element_map", "dof_map"):
        require(solver[field] is None, f"solver field {field} must remain null")

    source_register = json.loads((ATTEMPT_DIR / "source-register.json").read_text(encoding="utf-8"))
    nist_record = next(source for source in source_register["sources"] if source["id"] == "nist_ps1_09")
    require(
        nist_record["table_4_excerpt_sha256"] == sha256(excerpt_path),
        "source register Table 4 excerpt hash mismatch",
    )
    require(
        "5 plies and 5 layers" in " ".join(nist_record["observed"]),
        "source register must state the corrected conditional Table 4 minimum",
    )
    require(
        nist_record["table_4_locator"].startswith("Section 5.8, Table 4, printed pp. 21-22"),
        "source register Table 4 locator is missing or stale",
    )
    for source in source_register["sources"]:
        require(source["url"].startswith("https://"), f"source URL is not direct HTTPS: {source['id']}")
        require(source["retrieved"] == status["retrieved_local_date"], f"retrieval date mismatch: {source['id']}")
        require(source["local_copy_saved"] is False, f"unexpected saved external copy declaration: {source['id']}")
        require(source["content_sha256"] is None, f"external content hash must be null when not saved: {source['id']}")

    print(
        f"PASS: {pin_count} repository source pins and {terminal_count} attempt artifact hashes verified; "
        "six panel STEP bindings match the frozen manifest; "
        "product crosswalk, layup, properties, axes, and solver assignments remain bounded/null."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
