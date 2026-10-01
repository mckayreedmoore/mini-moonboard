#!/usr/bin/env python3
"""Read-only source and boundary verifier for the ordinary-patch manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ATTEMPT = Path(__file__).resolve().parent


def find_repo_root() -> Path:
    for parent in ATTEMPT.parents:
        if (parent / "site/owner-wood-joints-wj24-scene.json").is_file() and (
            parent / "docs/wood-joints-mvp"
        ).is_dir():
            return parent
    raise RuntimeError("Could not locate mini-moonboard repository root")


ROOT = find_repo_root()


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def checked_source_path(relative: str) -> Path:
    path = Path(relative)
    require(not path.is_absolute(), f"Pinned path must be relative: {relative}")
    require(".." not in path.parts, f"Pinned path escapes repository: {relative}")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"Pinned path escapes repository: {relative}") from error
    return resolved


def verify() -> None:
    manifest_path = ATTEMPT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(
        manifest["schema"] == "wood_joint_conditional_resistance_input_manifest/v1",
        "Unexpected manifest schema",
    )

    source_pins = manifest["source_pins"]
    pinned: dict[str, str] = {}
    for record in source_pins:
        relative = record["path"]
        require(relative not in pinned, f"Duplicate source pin: {relative}")
        path = checked_source_path(relative)
        require(path.is_file(), f"Pinned source is missing: {relative}")
        actual = digest(path)
        require(actual == record["sha256"], f"Source hash changed: {relative}")
        pinned[relative] = actual

    identity = manifest["candidate_identity"]
    scene = read_json("site/owner-wood-joints-wj24-scene.json")
    report = read_json("site/owner-wood-joints-review-report.json")
    revision = read_json(
        "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json"
    )
    snapshot = read_json(identity["geometry_snapshot_path"])
    source_inventory = read_json("docs/wood-joints-mvp/source-inventory.json")
    require(scene["candidate"] == identity["candidate_id"], "Scene candidate mismatch")
    for record in (scene, report, revision, snapshot):
        require(record["revision_id"] == identity["revision_id"], "Revision record mismatch")
    require(
        scene["source_binding"]["source_commit"]
        == identity["source_inventory_baseline_commit"]
        == source_inventory["source_commit"],
        "Source baseline commit mismatch",
    )
    require(
        report["joint_evaluations_run"] is False,
        "Current owner review unexpectedly reports joint evaluations",
    )
    for key in (
        "candidate_accepted",
        "capacity_established",
        "complete_joint_acceptance",
        "climbing_released",
        "structural_released",
        "fabrication_released",
    ):
        require(scene.get(key) is False, f"Scene status is not false: {key}")
    for key in (
        "candidate_accepted",
        "drilling_released",
        "fabrication_released",
        "structural_accepted",
    ):
        require(scene["release"].get(key) is False,
                f"Nested scene release status is not false: {key}")

    scope = manifest["patch_scope"]
    patch_path = (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-patch-inputs-attempt01/inventory.json"
    )
    preflight_path = (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-patch-resistance-preflight-attempt01/resistance-preflight.json"
    )
    patch = read_json(patch_path)
    preflight = read_json(preflight_path)
    classification = read_json(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-patch-contact-classification-attempt01/classification.json"
    )
    material_map = read_json(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-patch-materials-attempt01/material-map.json"
    )
    require(
        patch["candidate"]["revision_id"] == identity["revision_id"],
        "Patch inventory revision mismatch",
    )
    require(
        patch["candidate"]["implementation_revision"]
        == identity["implementation_revision"],
        "Patch implementation revision mismatch",
    )
    require(
        sorted(scope["wood_members"])
        == sorted(row["part_id"] for row in patch["wood_bodies"]),
        "Patch timber-member set mismatch",
    )
    require(
        sorted(scope["physical_bolt_ids"])
        == sorted(row["physical_bolt_id"] for row in patch["physical_bolts"]),
        "Patch physical-bolt set mismatch",
    )
    require(
        sorted(scope["wood_interface_ids"])
        == sorted(row["interface_id"] for row in patch["wood_interfaces"]),
        "Patch wood-interface set mismatch",
    )
    require(len(scope["physical_bolt_ids"]) == 4, "Expected four physical bolts")
    require(len(scope["washer_seats"]) == 8, "Expected eight washer seats")
    require(
        sorted(row["seat_id"] for row in scope["washer_seats"])
        == sorted(row["seat_id"] for row in preflight["wood_washer_bearing"]["seats"]),
        "Washer-seat set mismatch",
    )
    require(classification["contact_laws_assigned"] is False,
            "Patch classification unexpectedly assigns contact laws")
    require(classification["native_solve_ready"] is False,
            "Patch classification unexpectedly enables a native solve")
    require(classification["thread_engagement_verified"] is False,
            "Patch classification unexpectedly verifies thread engagement")
    require(material_map["scope"]["strength_or_capacity_claim"] is False,
            "Patch material map unexpectedly claims strength or capacity")
    for path, field in (
        (patch_path, "inventory"),
        (
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "ordinary-patch-contact-classification-attempt01/classification.json",
            "contact_classification",
        ),
        (
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "ordinary-patch-materials-attempt01/material-map.json",
            "material_map",
        ),
    ):
        require(
            preflight["inputs"][field]["sha256"] == pinned[path],
            f"Preflight input pin mismatch: {field}",
        )
    require(preflight["demand_and_acceptance"]["joint_adequacy_claim"] is False,
            "Preflight unexpectedly claims joint adequacy")
    require(preflight["demand_and_acceptance"]["criteria_passed"] == [],
            "Preflight unexpectedly reports passed criteria")

    scenarios = manifest["conditional_scenario_assumptions"]
    steel = scenarios["bolt_steel"]
    expected_steel = {
        "minimum_tensile_yield_ksi": 92.0,
        "minimum_tensile_strength_ksi": 120.0,
        "proof_stress_ksi": 85.0,
        "nominal_thread_tensile_stress_area_in2": 0.0318,
    }
    require(steel["properties"] == expected_steel,
            "Hypothetical Grade 5 scenario inputs changed")
    require(
        steel["basis"]
        == "Hypothetical 1/4-20 SAE J429 Grade 5 cap screw with numeric minima "
        "imposed as project performance requirements.",
        "Bolt basis must remain the declared hypothetical SAE J429 Grade 5 scenario",
    )
    require(
        steel["area_basis"]
        == "Nominal 1/4-20 tensile stress area; not a measured root or shank section.",
        "Bolt tensile-area basis changed",
    )
    steel_source_path = (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-bolt-steel-reference-attempt01/README.md"
    )
    require(steel["scenario_source_path"] == steel_source_path,
            "Bolt scenario source path changed")
    require(steel_source_path in pinned,
            "Bolt scenario source path is not SHA-256 pinned")
    require(steel["selected_or_delivered_product"] is False,
            "Bolt product must remain unselected and unreceived")
    require(steel["project_specification_is_not_lot_conformance"] is True,
            "Scenario specification must remain distinct from lot conformance")
    require(steel["component_resistance_or_interaction_calculated_in_this_manifest"] is False,
            "This manifest must not calculate bolt resistance or interaction")

    washer = scenarios["washer_to_wood"]
    preflight_wood = preflight["wood_washer_bearing"]
    expected_washer_range = [920.570210427248, 1019.1603103826817]
    require(washer["per_seat_reference_range_N"] == expected_washer_range,
            "Conditional per-seat washer reference range changed")
    require(
        washer["conditional_washer_geometry"]
        == "1/4-in Type A Wide plain-washer dimensional envelope.",
        "Conditional washer geometry basis changed",
    )
    require(
        washer["conditional_wood_property"]
        == "Dry DF-L No. 2 Fc-perp = 625 psi, NDS Supplement Table 4A basis.",
        "Conditional wood property basis changed",
    )
    require(washer["cad_wood_bore_mm"] == 7.5,
            "Pinned CAD wood-bore input changed")
    require(
        washer["per_seat_reference_range_N"]
        == [
            preflight_wood["lower_per_seat"]["reference_N"],
            preflight_wood["upper_per_seat"]["reference_N"],
        ],
        "Manifest washer range does not match the pinned preflight",
    )
    require(
        preflight_wood["washer_dimensions_mm"]
        == {
            "inner_diameter": {"min": 7.7978, "max": 8.3058},
            "outer_diameter": {"min": 18.4658, "max": 19.0246},
        },
        "Pinned Type A Wide dimensional envelope changed",
    )
    require(
        preflight_wood["wood_property_basis"]
        == "dry DF-L No. 2 Fc-perp = 625 psi per 2024 NDS Supplement Table 4A",
        "Pinned DF-L No. 2 Fc-perp basis changed",
    )
    require(
        washer["cad_wood_bore_mm"]
        == preflight_wood["wood_bore_diameter_mm"]["value"],
        "Manifest bore input does not match the pinned preflight",
    )
    require(washer["per_seat_only"] is True,
            "Washer reference must remain per seat")
    require(washer["summed_across_seats"] is False,
            "Washer references must not be summed across seats")
    require(washer["assumptions"] == [
        "Uniform compression over a complete circular annulus.",
        "Full washer footprint on sound wood.",
        "No preload and no bearing-area increase.",
    ], "Washer-reference assumptions changed")
    require(washer["delivered_wood_grade_verified"] is False,
            "Delivered wood grade must remain unverified")
    require(washer["washer_product_selected_or_received"] is False,
            "Washer product must remain unselected and unreceived")
    require(washer["active_pressure_or_load_distribution_established"] is False,
            "Washer reference must not establish active pressure")
    require(washer["washer_steel_resistance_method_established"] is False,
            "Washer reference must not establish washer-steel resistance")

    index_path = (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "ordinary-patch-inputs-attempt01/sha256.json"
    )
    index = read_json(index_path)
    for relative, expected in index.items():
        artifact = checked_source_path(str(Path(index_path).parent / relative))
        require(artifact.is_file(), f"Patch source artifact is missing: {relative}")
        require(digest(artifact) == expected, f"Patch source artifact changed: {relative}")
    require(
        index["inventory.json"] == pinned[patch_path],
        "Patch hash index does not bind the inventory",
    )

    load_path = manifest["load_and_resolution_boundary"][
        "six_case_applied_load_contract"
    ]["path"]
    load = read_json(load_path)
    boundary = manifest["load_and_resolution_boundary"]
    require(
        load["geometry_revision_id"] == identity["revision_id"],
        "Six-case input contract revision mismatch",
    )
    require(len(load["cases"]) == 6, "Expected six applied-load cases")
    require(
        load["contract_sha256"]
        == boundary["six_case_applied_load_contract"]["contract_sha256"],
        "Six-case contract hash mismatch",
    )
    require(
        boundary["six_case_applied_load_contract"]["consumed_by_this_manifest"]
        is False,
        "Applied-load contract must remain boundary-only",
    )
    require(
        boundary["current_six_case_joint_demands_available"] is False,
        "Current six-case demands must remain absent",
    )

    fyb = manifest["method_gaps_and_unknowns"]["nds_fyb"]
    require(fyb["status"] == "UNRESOLVED_METHOD_AND_EVIDENCE_GAP",
            "NDS Fyb gap must remain unresolved")
    require(fyb["value_ksi"] is None, "This manifest must not assign Fyb")
    require(fyb["accepted_basis"] is None,
            "This manifest must not claim an accepted Fyb basis")
    require(fyb["commentary_estimate_adopted"] is False,
            "Commentary estimate must not be adopted")
    require(manifest["criterion_results"] == [], "Criterion results must remain empty")
    require(
        all(value is False for value in manifest["flags"].values()),
        "All demand, criterion, acceptance, and release flags must remain false",
    )
    for row in manifest["criterion_readiness"]:
        require(row["criterion_result_calculated"] is False,
                f"Criterion result unexpectedly calculated: {row['criterion_id']}")
        require(row["criterion_resolved"] is False,
                f"Criterion unexpectedly resolved: {row['criterion_id']}")

    expected_standard_sources = {
        "ANSI/AWC NDS-2024": "https://awc.org/resources/2024-nds/",
        "ASTM F1575/F1575M-24 (active record)": "https://store.astm.org/f1575_f1575m-24.html",
        "ASTM F606/F606M-26a (active record)": "https://store.astm.org/f0606_f0606m-26a.html",
        "AWC 2024 NDS errata and addenda, 2026-03-23 record": (
            "https://awc.org/wp-content/uploads/2026/03/"
            "2024-NDS-Errata-and-Addenda-03.23.26.pdf"
        ),
    }
    actual_standard_sources = {
        record["designation"]: record["source"]
        for record in manifest["primary_standard_sources_checked_2026_09_27"]
    }
    require(actual_standard_sources == expected_standard_sources,
            "Official primary-standard source links changed")

    print(
        "PASS: source pins, current patch identity, six-case boundary, Fyb gap, "
        f"and false status fields ({len(source_pins)} pins; {len(index) - 1} patch artifacts)."
    )


def main() -> int:
    if sys.argv[1:] not in ([], ["--verify"]):
        print("usage: verify.py [--verify]", file=sys.stderr)
        return 2
    try:
        verify()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
