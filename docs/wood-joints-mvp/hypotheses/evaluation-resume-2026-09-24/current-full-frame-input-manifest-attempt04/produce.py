#!/usr/bin/env python3
"""Bind reviewed conditional material-scenario maps to the preserved WJ24 inputs.

Attempt04 extends the source-only attempt03 manifest. It preserves all of the
older geometry, STEP, mass, and load records and adds reviewed frame-transverse
and candidate-steel role-map evidence plus a reaffirmation of the block map.
It does not create a solver model or run CAD/CalculiX.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
ATTEMPT03 = BASE / "current-full-frame-input-manifest-attempt03"
OUT_DIR = BASE / "current-full-frame-input-manifest-attempt04"
OUTPUT = OUT_DIR / "current-full-frame-input-manifest.json"
README = OUT_DIR / "README.md"
PRODUCER_PATH = OUTPUT.as_posix().replace(
    "current-full-frame-input-manifest.json", "produce.py"
)

TRANSVERSE_DIR = BASE / "current-frame-timber-transverse-scenarios-attempt01"
TRANSVERSE_JSON = TRANSVERSE_DIR / "transverse-scenarios.json"
TRANSVERSE_PRODUCER = TRANSVERSE_DIR / "produce.py"
TRANSVERSE_README = TRANSVERSE_DIR / "README.md"
TRANSVERSE_REVIEW = TRANSVERSE_DIR / "independent-review.md"

STEEL_DIR = BASE / "current-steel-elastic-role-map-attempt01"
STEEL_JSON = STEEL_DIR / "steel-elastic-role-map.json"
STEEL_PRODUCER = STEEL_DIR / "produce.py"
STEEL_README = STEEL_DIR / "README.md"
STEEL_REVIEW = STEEL_DIR / "parent-review.json"

BLOCK_DIR = BASE / "current-block-material-frame-map-attempt02"
BLOCK_JSON = BLOCK_DIR / "material-frame-map.json"
BLOCK_PRODUCER = BLOCK_DIR / "produce.py"
BLOCK_README = BLOCK_DIR / "README.md"

ATTEMPT03_JSON = ATTEMPT03 / "current-full-frame-input-manifest.json"
ATTEMPT03_PRODUCER = ATTEMPT03 / "produce.py"
ATTEMPT03_README = ATTEMPT03 / "README.md"

# Exact current input pins, including the final reviewed frame README and
# review records. A change to any of these requires a new manifest attempt.
EXPECTED_SHA256 = {
    ATTEMPT03_JSON.as_posix(): "2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896",
    ATTEMPT03_PRODUCER.as_posix(): "1d9f1417b33d6d6ef2626c6f1b3957579361c960f59f963e3b8157df5fbf35f2",
    ATTEMPT03_README.as_posix(): "98455c87f1961517a4a6747b60ff1c27d6b2e05612dc53051f6f31bad5b4961b",
    TRANSVERSE_JSON.as_posix(): "8c7646dcbce4ad94c99a422a3e93aaee87644faf56c125fc09c5176dd4a2d714",
    TRANSVERSE_PRODUCER.as_posix(): "309fb56c9a58b7b7b529aee1a3304369a7587f02649b6cbada6842e650d35498",
    TRANSVERSE_README.as_posix(): "93e869c5f9a6f232e77025e12f8c90b79965bebe968348636dd220bcb30e69ea",
    TRANSVERSE_REVIEW.as_posix(): "68b92f8ad838665d57bd7e0a364ecf0af6992bd3f97711f6c1a99a12f8e2bdca",
    STEEL_JSON.as_posix(): "13ed1afcfbc9343207b9e8eb498f8fb3762ec2cdbe0719963f26037cc77027cc",
    STEEL_PRODUCER.as_posix(): "b625579bc032e32a1100c39f31e50cfea65f74b2137394d500e8055436ca1b26",
    STEEL_README.as_posix(): "a4ca6688d6bece7c4653c421ed52f74f681de10985896d5d4454f89314662222",
    STEEL_REVIEW.as_posix(): "149f3c13368aee1a6007b2310355b4b5ab0f923b20b6657e872d0e4d7805337a",
    BLOCK_JSON.as_posix(): "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    BLOCK_PRODUCER.as_posix(): "e66e21f8fbd3672ea826fe32f67b45ac3034db385c7b59f2ddbb084cb7f25690",
    BLOCK_README.as_posix(): "dd25a3c19f88238cfff4697c34b1cc00916f5b411636366f5d0fb26951e943d2",
}

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_SELECTED = "compact-floor-flush-development"
EXPECTED_CASE_IDS = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
STEEL_REFERENCE_ID = "steel_elastic_diagnostic_baseline_2026-09-24"

VERIFIERS = (
    (ATTEMPT03_PRODUCER, "verified"),
    (TRANSVERSE_PRODUCER, "PASS_SOURCE_AND_FRAME_ALGEBRA"),
    (STEEL_PRODUCER, "verified"),
    (BLOCK_PRODUCER, "verified"),
)

PRESERVED_IDENTITY_KEYS = (
    "candidate",
    "geometry_revision_id",
    "reviewed_repository_commit",
    "selected_candidate_authority_preserved",
    "authority_and_provenance",
    "coordinate_and_unit_contract",
    "physical_members",
    "candidate_blocks",
    "candidate_bolt_axes",
    "panel_kicker_screw_axes",
    "retained_frame_bolt_axes",
    "finished_member_step_bindings",
    "existing_step_export_evidence",
    "historical_d6_step_export_evidence",
    "inventory_counts",
    "applied_load_cases",
    "contact_graph",
    "target_duties",
    "source_artifacts",
    "source_artifacts_scope",
    "source_dependency_hash_audits",
    "independent_cross_checks",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    absolute = ROOT / path
    if not absolute.is_file():
        raise FileNotFoundError(f"pinned source is missing: {path.as_posix()}")
    return sha256_bytes(absolute.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.as_posix()}: expected a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_input_pins() -> dict[str, str]:
    actual = {}
    for relative, expected in EXPECTED_SHA256.items():
        observed = sha256_file(Path(relative))
        if observed != expected:
            raise ValueError(
                f"source changed for {relative}: expected {expected}, got {observed}"
            )
        actual[relative] = observed
    return actual


def verify_sibling_producers() -> dict[str, dict[str, Any]]:
    """Run only each pinned producer's read-only --verify command."""
    results = {}
    for script, expected_status in VERIFIERS:
        absolute = ROOT / script
        completed = subprocess.run(
            [sys.executable, str(absolute), "--verify"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise ValueError(
                f"read-only source verifier failed for {script.as_posix()}: "
                f"{completed.stderr.strip()}"
            )
        try:
            report = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"source verifier returned invalid JSON: {script.as_posix()}"
            ) from error
        if report.get("status") != expected_status:
            raise ValueError(
                f"unexpected source verification status for {script.as_posix()}: "
                f"{report.get('status')}"
            )
        results[script.as_posix()] = report
    return results


def verify_content_digest(record: dict[str, Any], field: str, context: str) -> str:
    payload = dict(record)
    recorded = payload.pop(field, None)
    if not isinstance(recorded, str) or sha256_bytes(canonical_json(payload)) != recorded:
        raise ValueError(f"{context}: {field} does not match canonical record")
    return recorded


def pin(path: Path, *, digest_field: str | None = None) -> dict[str, Any]:
    absolute = ROOT / path
    if not absolute.is_file():
        raise FileNotFoundError(f"missing bound artifact: {path.as_posix()}")
    result: dict[str, Any] = {
        "path": path.as_posix(),
        "file_sha256": sha256_file(path),
        "size_bytes": absolute.stat().st_size,
    }
    if digest_field is not None:
        record = read_json(path)
        result["content_digest_field"] = digest_field
        result["content_digest"] = record[digest_field]
    return result


def _verify_attempt03_sources(previous: dict[str, Any]) -> dict[str, Any]:
    digest = verify_content_digest(previous, "manifest_sha256", "attempt03 manifest")
    require(previous["manifest_id"] == ATTEMPT03.name, "attempt03 base ID changed")
    require(previous["candidate"] == EXPECTED_CANDIDATE, "candidate identity changed")
    require(previous["geometry_revision_id"] == EXPECTED_REVISION, "revision changed")
    require(
        previous["selected_candidate_authority_preserved"] == EXPECTED_SELECTED,
        "selected authority changed",
    )
    require(previous["reviewed_repository_commit"] == "b1e8707d", "review checkpoint changed")
    require(previous["readiness"]["inputs_ready"] is False, "attempt03 readiness changed")
    require(previous["readiness"]["per_member_material_mapping_ready"] is False,
            "attempt03 material readiness changed")
    require(previous["readiness"]["native_solve_executed"] is False,
            "attempt03 records a native solve")
    require(all(value is False for value in previous["release"].values()),
            "attempt03 contains a release/acceptance flag")

    # The historical source-artifact list is preserved verbatim; current
    # attempt03 evidence bindings and all 50 STEP files must still resolve.
    for name, binding in previous["evidence_bindings"].items():
        source_path = Path(binding["path"])
        require(sha256_file(source_path) == binding["file_sha256"],
                f"attempt03 evidence source changed: {name}")
        if "content_digest_field" in binding:
            record = read_json(source_path)
            require(record.get(binding["content_digest_field"]) == binding["content_digest"],
                    f"attempt03 evidence content digest changed: {name}")

    steps = previous["finished_member_step_bindings"]
    require(len(steps) == 50 and len({row["member_id"] for row in steps}) == 50,
            "attempt03 does not bind 50 unique finished member solids")
    kind_counts: dict[str, int] = {}
    for row in steps:
        path = Path(row["path"])
        require(sha256_file(path) == row["file_sha256"],
                f"finished STEP hash changed: {path.as_posix()}")
        require((ROOT / path).stat().st_size == row["size_bytes"],
                f"finished STEP byte size changed: {path.as_posix()}")
        require(row["one_solid_valid_roundtrip"] is True,
                f"finished STEP round-trip evidence changed: {row['member_id']}")
        kind_counts[row["member_kind"]] = kind_counts.get(row["member_kind"], 0) + 1
    require(kind_counts == {"timber": 20, "plywood_panel": 6, "candidate_block": 24},
            f"attempt03 STEP member kinds changed: {kind_counts}")

    topology_binding = previous["evidence_bindings"]["source_to_mass_topology"]
    topology = read_json(Path(topology_binding["path"]))
    require(topology["mass_inventory_row_count"] == 778,
            "source mass topology no longer has 778 rows")
    require(topology["unique_source_mass_entity_count"] == 778,
            "source mass topology entity count changed")
    require(topology_binding["reconciled_facts"]["global_solver_mass_dof_mapping"] is False,
            "source mass topology unexpectedly maps solver DOFs")

    load_binding = previous["evidence_bindings"]["six_current_applied_load_cases"]
    loads = read_json(Path(load_binding["path"]))
    require(len(loads["cases"]) == 6, "current applied case count changed")
    require(loads["contract_sha256"] == load_binding["content_digest"],
            "current load-case content digest changed")
    case_ids = [row["case_id"] for row in loads["cases"]]
    require(case_ids == EXPECTED_CASE_IDS, f"current six-case identity changed: {case_ids}")
    require([row["case_id"] for row in previous["applied_load_cases"]["cases"]] == case_ids,
            "attempt03 embedded six-case inputs differ from their source")
    load_facts = load_binding["reconciled_facts"]
    require(load_facts == {
        "applied_wrenches_only": True,
        "case_ids": EXPECTED_CASE_IDS,
        "cases": 6,
        "reactions_or_joint_demands": False,
    }, "attempt03 applied-load scope facts changed")
    require(any(
        "no frame reactions or connection demands are computed" in limit
        for limit in loads["limits"]
    ), "current load-case source no longer limits its scope to applied wrenches")

    require(previous["inventory_counts"]["full_physical_member_nodes"] == 50,
            "physical member inventory changed")
    require(previous["inventory_counts"]["candidate_bolt_axes"] == 92,
            "candidate bolt axis inventory changed")
    require(previous["inventory_counts"]["candidate_modeled_hardware_component_roles"] == 460,
            "candidate hardware role inventory changed")
    require(previous["evidence_bindings"]["modeled_body_gravity_and_accessory_scenarios"]
            ["reconciled_facts"]["mass_rows"] == 778, "gravity inventory count changed")
    require(previous["evidence_bindings"]["modeled_body_gravity_and_accessory_scenarios"]
            ["reconciled_facts"]["accessory_allowance_kg"] == 25.0,
            "separate accessory allowance changed")

    return {
        "manifest_sha256": digest,
        "step_member_count": len(steps),
        "step_member_kind_counts": kind_counts,
        "mass_row_count": topology["mass_inventory_row_count"],
        "case_ids": case_ids,
    }


def _verify_transverse_map(previous: dict[str, Any]) -> dict[str, Any]:
    record = read_json(TRANSVERSE_JSON)
    digest = verify_content_digest(record, "record_sha256", "frame transverse map")
    expected_members = {
        row["member_id"] for row in previous["finished_member_step_bindings"]
        if row["member_kind"] == "timber"
    }
    member_rows = record.get("members", [])
    actual_members = {row["member_id"] for row in member_rows}
    require(record["candidate"] == previous["candidate"], "transverse map candidate changed")
    require(record["geometry_revision_id"] == previous["geometry_revision_id"],
            "transverse map revision changed")
    require(len(member_rows) == 20 and actual_members == expected_members,
            "transverse map does not cover exactly the 20 frame timber IDs")
    require(record["member_count"] == 20 and record["scenario_frame_count"] == 40,
            "transverse map counts changed")
    require(record["wood_properties_assigned"] is False
            and record["panel_layups_assigned"] is False
            and record["geometry_changed"] is False
            and record["cad_rebuilt"] is False
            and record["native_solve_run"] is False
            and record["full_frame_inputs_ready"] is False
            and record["material_acceptance"] is False
            and record["joint_acceptance"] is False
            and record["release"] is False,
            "transverse map scope or readiness flags changed")
    for row in member_rows:
        require(set(row["cases_global_xyz"]) == {"A", "B"},
                f"missing frame cases for {row['member_id']}")
        require(row["observed_ring_orientation"] is None
                and row["selected_case"] is None
                and row["solver_element_assignment"] is None,
                f"frame map makes an observation/selection/solver claim: {row['member_id']}")
    review_text = " ".join(
        (ROOT / TRANSVERSE_REVIEW).read_text(encoding="utf-8").split()
    )
    require("found no correction needed" in review_text
            and digest in review_text
            and "does not establish physical material identity" in review_text,
            "frame transverse independent review no longer matches its bounded disposition")
    return {
        "artifact": pin(TRANSVERSE_JSON, digest_field="record_sha256"),
        "producer_file": pin(TRANSVERSE_PRODUCER),
        "readme_file": pin(TRANSVERSE_README),
        "independent_review_file": pin(TRANSVERSE_REVIEW),
        "review_disposition": "reviewed conditional frame algebra and source binding only",
        "reconciled_facts": {
            "member_count": 20,
            "frame_count": 40,
            "cases_per_member": 2,
            "member_ids": sorted(actual_members),
            "case_names": ["A", "B"],
            "observed_ring_orientations": 0,
            "selected_cases": 0,
            "solver_element_assignments": 0,
            "wood_properties_assigned": False,
        },
        "upstream_source_pins": record["source_pins"],
        "status": "conditional_transverse_scenarios_only_not_received_grain_or_material_assignment",
    }


def _verify_steel_map(previous: dict[str, Any], topology: dict[str, Any]) -> dict[str, Any]:
    record = read_json(STEEL_JSON)
    digest = verify_content_digest(record, "record_sha256", "steel role map")
    review = read_json(STEEL_REVIEW)
    expected_axes = {row["axis_id"] for row in previous["candidate_bolt_axes"]}
    actual_axes = {
        row["axis_id"] for row in record["candidate_physical_bolt_identities"]
    }
    candidate_entities = {
        row["source_mass_entity"]["id"]
        for row in topology["physical_mass_rows"]
        if row["source_mass_entity"]["kind"] == "current_candidate_hardware_component"
    }
    retained_entities = {
        row["source_mass_entity"]["id"]
        for row in topology["physical_mass_rows"]
        if row["source_mass_entity"]["kind"] == "current_retained_frame_hardware_component"
    }
    assignments = record["candidate_component_role_assignments"]
    assignment_entities = {row["source_mass"]["source_mass_entity_id"] for row in assignments}
    retained_rows = record["retained_frame_component_roles_unassigned"]
    retained_row_entities = {row["source_mass"]["source_mass_entity_id"] for row in retained_rows}

    require(record["candidate"] == previous["candidate"], "steel role map candidate changed")
    require(record["geometry_revision_id"] == previous["geometry_revision_id"],
            "steel role map revision changed")
    require(len(actual_axes) == 92 and actual_axes == expected_axes,
            "steel role map does not cover exactly the 92 candidate axes")
    require(len(assignments) == 460 and assignment_entities == candidate_entities,
            "steel role map component IDs differ from the 460 topology rows")
    require(len(retained_rows) == 60 and retained_row_entities == retained_entities,
            "retained steel inventory does not cover the exact 60 source rows")
    require(all(row["material_assignment"] is None for row in retained_rows),
            "retained hardware roles must remain unassigned by default")
    require(record["scope_counts"]["scenario_family_cases"] == 9
            and len(record["material_scenario_family"]["scenarios"]) == 9,
            "steel role map sensitivity family must contain nine scenarios")
    require(record["material_scenario_family"]["reference_scenario_id"] == STEEL_REFERENCE_ID,
            "steel role map reference scenario changed")
    require(record["solver_mapping"] == {
        "solver_body_ids_assigned": False,
        "solver_dof_mapping_implemented": False,
        "solver_element_material_assignments_written": False,
        "solver_material_cards_emitted": False,
        "source_topology_solver_dof_ids_all_null": True,
    }, "steel role map unexpectedly contains solver mappings")
    require(record["source_manifest_readiness_unchanged"]["full_frame_inputs_ready_after_this_map"]
            is False, "steel map claims full-frame readiness")
    require(review["status"] == "PASS_PARENT_SOURCE_ROLE_AND_ELASTIC_SCENARIO_REVIEW"
            and review["reviewed_files_sha256"] == {
                "README.md": EXPECTED_SHA256[STEEL_README.as_posix()],
                "produce.py": EXPECTED_SHA256[STEEL_PRODUCER.as_posix()],
                "steel-elastic-role-map.json": EXPECTED_SHA256[STEEL_JSON.as_posix()],
            }
            and review["candidate_roles"] == 460
            and review["retained_roles_unassigned"] == 60
            and review["solver_mapping_implemented"] is False
            and review["full_frame_inputs_ready"] is False
            and review["joint_acceptance"] is False
            and review["release"] is False,
            "steel role-map parent review does not match current reviewed files/scope")

    return {
        "artifact": pin(STEEL_JSON, digest_field="record_sha256"),
        "producer_file": pin(STEEL_PRODUCER),
        "readme_file": pin(STEEL_README),
        "parent_review_file": pin(STEEL_REVIEW),
        "review_disposition": review["status"],
        "reconciled_facts": {
            "candidate_axis_count": 92,
            "candidate_physical_bolt_identity_count": 92,
            "candidate_component_role_count": 460,
            "roles_per_axis": 5,
            "component_role_ids": sorted(assignment_entities),
            "retained_axis_count": 12,
            "retained_component_role_count": 60,
            "retained_role_material_assignments": 0,
            "reference_scenario_id": STEEL_REFERENCE_ID,
            "elastic_sensitivity_scenario_count": 9,
            "solver_body_element_dof_or_card_assignments": 0,
        },
        "upstream_source_pins": record["source_sha256"],
        "status": "conditional_generic_elastic_role_binding_only_no_solver_material_assignment",
    }


def _verify_block_map(previous: dict[str, Any]) -> dict[str, Any]:
    record = read_json(BLOCK_JSON)
    digest = verify_content_digest(record, "record_sha256", "block frame map")
    expected_blocks = {row["part_id"] for row in previous["candidate_blocks"]}
    actual_blocks = {row["part_id"] for row in record["members"]}
    case_count = sum(len(row["transverse_assignment_cases"]) for row in record["members"])
    require(record["candidate"] == previous["candidate"], "block map candidate changed")
    require(record["geometry_revision_id"] == previous["geometry_revision_id"],
            "block map revision changed")
    require(len(actual_blocks) == 24 and actual_blocks == expected_blocks,
            "existing block map does not cover the exact 24 candidate blocks")
    require(case_count == 48, "existing block map must preserve 48 conditional transverse cases")
    require(record["readiness_effect"]["full_frame_inputs_ready"] is False
            and record["readiness_effect"]["manifest_full_frame_per_member_material_mapping_ready"]
            is False
            and record["readiness_effect"]["native_solve_executed"] is False,
            "existing block map changed readiness/scope")
    return {
        "artifact": pin(BLOCK_JSON, digest_field="record_sha256"),
        "producer_file": pin(BLOCK_PRODUCER),
        "readme_file": pin(BLOCK_README),
        "reconciled_facts": {
            "member_count": 24,
            "block_ids": sorted(actual_blocks),
            "conditional_transverse_case_count": 48,
            "cases_per_block": 2,
            "full_frame_inputs_ready": False,
            "wood_properties_assigned": False,
        },
        "status": "existing_attempt02_conditional_block_orientation_map_preserved",
    }


def _replace_material_status(
    manifest: dict[str, Any],
    transverse_binding: dict[str, Any],
    steel_binding: dict[str, Any],
    block_binding: dict[str, Any],
) -> None:
    candidate_hardware = dict(manifest["scenario_input_status"]["candidate_hardware"])
    candidate_hardware["conditional_elastic_role_binding"] = {
        "source": steel_binding["artifact"]["path"],
        "candidate_axes": 92,
        "candidate_component_roles": 460,
        "physical_product_selected_or_received": False,
        "solver_material_cards_or_body_assignments": False,
    }
    manifest["scenario_input_status"]["candidate_hardware"] = candidate_hardware

    metal = dict(manifest["scenario_input_status"]["metal_elastic"])
    metal["status"] = (
        "conditional generic E/nu scenario family is source-bound to the 460 current "
        "candidate component roles; no physical product properties or solver material "
        "cards/body/element/DOF assignments are established"
    )
    metal["candidate_role_binding"] = {
        "map_path": steel_binding["artifact"]["path"],
        "candidate_axes": 92,
        "candidate_component_roles": 460,
        "scenario_cases": 9,
        "reference_scenario_id": STEEL_REFERENCE_ID,
    }
    metal["retained_frame_role_status"] = (
        "60 retained hardware component roles are inventoried separately and remain "
        "unassigned by default pending model inclusion and candidate recheck"
    )
    manifest["scenario_input_status"]["metal_elastic"] = metal

    timber = dict(manifest["scenario_input_status"]["timber_and_grain"])
    timber["exact_current_member_material_frames"] = (
        "two conditional transverse frames are source-bound for each of 20 frame "
        "timbers; the existing 24-block map retains its 48 cases; six plywood-panel "
        "layups remain unassigned and no solver material/element map exists"
    )
    timber["status"] = (
        "conditional orientation scenarios are bound for 20 frame timbers and 24 blocks; "
        "panel layups, delivered material identity/properties, and solver assignments remain unresolved"
    )
    timber["frame_transverse_scenarios"] = {
        "map_path": transverse_binding["artifact"]["path"],
        "members": 20,
        "cases": 40,
        "cases_per_member": 2,
        "ring_orientation_observed": False,
        "case_selected": False,
    }
    timber["connector_block_scenarios"] = {
        "map_path": block_binding["artifact"]["path"],
        "members": 24,
        "cases": 48,
    }
    timber["plywood_panels"] = {
        "count": 6,
        "layup_assigned": False,
        "material_axes_or_properties_assigned": False,
    }
    manifest["scenario_input_status"]["timber_and_grain"] = timber

    retained = dict(manifest["scenario_input_status"]["retained_frame_hardware"])
    retained["component_roles"] = 60
    retained["material_assignment"] = "unassigned_by_default"
    manifest["scenario_input_status"]["retained_frame_hardware"] = retained

    readiness = manifest["readiness"]
    readiness["frame_timber_transverse_scenarios_cover_20_of_20"] = True
    readiness["candidate_steel_elastic_role_bindings_cover_92_axes_460_roles"] = True
    readiness["connector_block_transverse_scenarios_cover_24_of_24"] = True
    readiness["six_plywood_panel_layups_assigned"] = False
    readiness["retained_frame_steel_role_assignments_complete"] = False
    readiness["solver_body_element_dof_material_mapping_complete"] = False
    readiness["inputs_ready"] = False
    readiness["per_member_material_mapping_ready"] = False

    unresolved = readiness["unresolved_inputs"]
    replaced_material = False
    replaced_hardware = False
    for index, item in enumerate(unresolved):
        if item.startswith("The 20 timber and 24 connector-block maps"):
            unresolved[index] = (
                "Each of the 20 frame timbers now has two source-bound conditional transverse "
                "frames, and the 24 candidate blocks retain their existing 48 conditional cases. "
                "These are orientation alternatives, not observed board rings or delivered "
                "properties. Six plywood panels still have no assigned layup, axes, or properties."
            )
            replaced_material = True
        elif item.startswith("No physical bolt, nut, washer, or T-nut product is selected"):
            unresolved[index] = (
                "A conditional generic steel elastic scenario family is now bound to 460 candidate "
                "component roles on 92 axes, but no solver body/element/DOF material mapping or "
                "material card exists. No physical bolt, nut, washer, or T-nut product is selected "
                "and fit-qualified for the 92 candidate or 12 retained stacks; thread start/runout, "
                "matched engagement, delivery tolerances, and receiving remain unresolved. The 60 "
                "retained component roles remain unassigned by default."
            )
            replaced_hardware = True
    require(replaced_material and replaced_hardware,
            "attempt03 unresolved material/hardware status text changed unexpectedly")

    checks = manifest["source_preparation_checks"]
    checks["frame_timber_transverse_scenarios_reconciled"] = True
    checks["candidate_steel_elastic_role_bindings_reconciled"] = True
    checks["existing_connector_block_orientation_map_reaffirmed"] = True
    checks["conditional_material_scenario_inputs_reconciled"] = True
    checks["six_plywood_panel_layups_assigned"] = False
    checks["retained_frame_steel_role_assignments_complete"] = False
    checks["solver_body_element_dof_material_mapping_complete"] = False
    checks["solver_model_inputs_complete"] = False
    checks["native_solve_executed"] = False


def build_manifest() -> dict[str, Any]:
    source_pins = verify_input_pins()
    source_verifier_results = verify_sibling_producers()
    previous = read_json(ATTEMPT03_JSON)
    baseline_facts = _verify_attempt03_sources(previous)
    topology_binding = previous["evidence_bindings"]["source_to_mass_topology"]
    topology = read_json(Path(topology_binding["path"]))
    transverse_binding = _verify_transverse_map(previous)
    steel_binding = _verify_steel_map(previous, topology)
    block_binding = _verify_block_map(previous)

    refreshed = copy.deepcopy(previous)
    for key in PRESERVED_IDENTITY_KEYS:
        require(refreshed[key] == previous[key], f"preserved attempt03 identity changed: {key}")
    for key, value in previous["evidence_bindings"].items():
        require(refreshed["evidence_bindings"][key] == value,
                f"attempt03 evidence binding changed: {key}")

    refreshed["schema"] = "wood_joint_current_full_frame_input_manifest/v3"
    refreshed["manifest_id"] = OUT_DIR.name
    refreshed["status"] = (
        "source_prepared_geometry_load_and_conditional_material_scenario_inputs_not_ready"
    )
    refreshed["attempt03_base_manifest"] = {
        **pin(ATTEMPT03_JSON, digest_field="manifest_sha256"),
        "manifest_sha256": baseline_facts["manifest_sha256"],
        "role": "immutable geometry, source inventory, mass, load, and attempt03 evidence baseline",
    }
    refreshed["attempt04_input_source_pins"] = source_pins

    refreshed["evidence_bindings"]["attempt03_preserved_manifest_snapshot"] = {
        "manifest": pin(ATTEMPT03_JSON, digest_field="manifest_sha256"),
        "producer_file": pin(ATTEMPT03_PRODUCER),
        "readme_file": pin(ATTEMPT03_README),
        "manifest_sha256": baseline_facts["manifest_sha256"],
        "preserved_step_member_count": baseline_facts["step_member_count"],
        "preserved_step_member_kind_counts": baseline_facts["step_member_kind_counts"],
        "preserved_mass_inventory_rows": baseline_facts["mass_row_count"],
        "preserved_load_case_ids": baseline_facts["case_ids"],
        "historical_snapshot_identity_changes": 0,
        "status": "preserved_attempt03_snapshot_not_rewritten",
    }
    refreshed["evidence_bindings"]["attempt04_conditional_material_map_bundle"] = {
        "status": "conditional_orientation_and_elastic_role_evidence_only",
        "frame_timber_transverse_scenarios": transverse_binding,
        "candidate_steel_elastic_role_map": steel_binding,
        "existing_connector_block_orientation_map": block_binding,
        "solver_element_or_dof_material_assignments": 0,
        "six_plywood_panel_layups_assigned": False,
        "retained_frame_steel_role_assignments": 0,
        "native_solve_executed": False,
    }

    _replace_material_status(refreshed, transverse_binding, steel_binding, block_binding)
    refreshed["claim_limits"] = list(refreshed["claim_limits"])
    refreshed["claim_limits"].append(
        "Attempt04 binds source-reviewed transverse alternatives for 20 frame timbers, the existing 24-block scenarios, and a generic elastic scenario family to 460 candidate hardware roles only."
    )
    refreshed["claim_limits"].append(
        "Six plywood-panel layups and 60 retained hardware role assignments remain unresolved; no solver material/body/element/DOF mapping is supplied and all readiness, acceptance, and release flags remain false."
    )
    refreshed["producer"] = {
        "path": PRODUCER_PATH,
        "sha256": sha256_file(Path(PRODUCER_PATH)),
        "operation": "source-only attempt03 extension; read-only verification of pinned source producers",
    }

    require(refreshed["candidate"] == EXPECTED_CANDIDATE
            and refreshed["geometry_revision_id"] == EXPECTED_REVISION
            and refreshed["selected_candidate_authority_preserved"] == EXPECTED_SELECTED,
            "attempt04 authority or geometry revision changed")
    require(refreshed["readiness"]["inputs_ready"] is False
            and refreshed["readiness"]["per_member_material_mapping_ready"] is False
            and refreshed["readiness"]["native_solve_executed"] is False
            and refreshed["readiness"]["solver_body_element_dof_material_mapping_complete"] is False,
            "attempt04 readiness must remain false")
    require(all(value is False for value in refreshed["release"].values()),
            "attempt04 acceptance/release flags must remain false")
    require(all(report.get("native_solve_executed") is False
                for report in source_verifier_results.values()
                if "native_solve_executed" in report),
            "a source verifier reported a native solve")

    refreshed["manifest_sha256"] = sha256_bytes(canonical_json(refreshed))
    return refreshed


def render_readme(manifest: dict[str, Any]) -> str:
    bindings = manifest["evidence_bindings"]["attempt04_conditional_material_map_bundle"]
    frame = bindings["frame_timber_transverse_scenarios"]
    steel = bindings["candidate_steel_elastic_role_map"]
    block = bindings["existing_connector_block_orientation_map"]
    snapshot = manifest["evidence_bindings"]["attempt03_preserved_manifest_snapshot"]
    step_counts = manifest["source_preparation_checks"]["step_member_kind_counts"]
    case_ids = manifest["applied_load_cases"]["cases"]
    unresolved_lines = "\n".join(
        textwrap.fill(
            item,
            width=98,
            initial_indent="- ",
            subsequent_indent="  ",
        )
        for item in manifest["readiness"]["unresolved_inputs"]
    )
    return f"""# Current full-frame input manifest — attempt04

## Result and lineage

Attempt04 preserves the complete attempt03 geometry, source-member identity,
STEP, 778-row mass, six-case load, and solver-profile records. It adds a
source-reviewed transverse-scenario map for the 20 frame timbers and a
conditional elastic role map for the 92 candidate bolt axes. The existing
24-block orientation map remains bound. Attempt03 is pinned as the immutable
baseline; its files are not regenerated or edited here.

The geometry inventory remains {len(manifest['finished_member_step_bindings'])}
one-solid STEP files: {step_counts['timber']} timbers, {step_counts['plywood_panel']}
panels, and {step_counts['candidate_block']} candidate blocks. Its STEP bundle
digest remains
`{manifest['evidence_bindings']['finished_member_geometry']['content_digest']}`.
The current mass-source map still contains
{manifest['evidence_bindings']['source_to_mass_topology']['reconciled_facts']['mass_inventory_rows']}
mass rows, with the separate 25 kg accessory allowance. Six applied force/wrench
case inputs remain `{', '.join(row['case_id'] for row in case_ids)}`; they provide
no reactions or joint demands.

## Added and reaffirmed conditional evidence

| Inventory | Bound evidence | Still unresolved |
| --- | --- | --- |
| 20 frame timbers | 40 transverse alternatives, two per member | No received ring orientation, wood property assignment, solver orientation card, or element assignment |
| 24 connector blocks | Existing 48 conditional transverse cases | No received ring orientation or wood property assignment |
| 92 candidate bolt axes | 460 component roles and nine generic elastic scenarios | No delivered product, grade, solver body/element/DOF mapping, or material cards |
| 6 plywood panels | Source geometry is preserved | Layups, material axes, and properties remain unassigned |
| 12 retained frame-bolt axes | 60 role rows separately inventoried | Remain unassigned by default; current-candidate recheck remains required |

The steel reference scenario is `{steel['reconciled_facts']['reference_scenario_id']}`.
Its E/nu family is a conditional model input; the head and shaft roles share
candidate bolt identity while remaining separate mass/component rows. It does
not identify delivered alloy, grade, yield, plasticity, preload, or resistance.
No material card or solver-body assignment is emitted by any new map.

Attempt04 changes only the current conditional-material evidence/status fields.
It does not claim full-frame material readiness: `inputs_ready=false`,
`per_member_material_mapping_ready=false`, all acceptance/release flags remain
false, and no full-frame finite-element model, connection transfer law,
reaction, demand, or criteria result is supplied.

## Pinned evidence

The attempt03 baseline manifest SHA-256 is
`{snapshot['manifest_sha256']}`. Added and reaffirmed map content digests are:

- Frame-timber transverse cases: `{frame['artifact']['content_digest']}`
- Candidate steel role map: `{steel['artifact']['content_digest']}`
- Existing block map: `{block['artifact']['content_digest']}`

Attempt03's inherited `source_artifacts` remain the historical attempt02
snapshot. The exact attempt03 file, producer, and README pins are separately
listed as the preserved baseline. New reviewed map and review-file hashes are
recorded under `evidence_bindings.attempt04_conditional_material_map_bundle`.

## Remaining inputs

{unresolved_lines}

## Reproduction

From this attempt directory:

```sh
python3 produce.py --verify
```

Verification checks fixed input SHA-256 pins, reruns only the four pinned
source producers in read-only `--verify` mode, rechecks all 50 STEP files,
778 mass rows, and six exact load-case IDs, then reconstructs this manifest
and README. It does not rebuild CAD, create a solver deck, or launch CalculiX.
Use `--write` once in a fresh attempt directory; both outputs use exclusive
creation and existing files are never replaced.

Manifest SHA-256: `{manifest['manifest_sha256']}`.
"""


def verify() -> dict[str, Any]:
    expected = build_manifest()
    actual = read_json(OUTPUT)
    require(actual == expected, "attempt04 manifest differs from pinned reconstruction")
    readme = (ROOT / README).read_text(encoding="utf-8")
    require(readme == render_readme(actual), "attempt04 README differs from pinned manifest")
    require(actual["readiness"]["inputs_ready"] is False
            and actual["readiness"]["native_solve_executed"] is False,
            "attempt04 readiness/native status is not false")
    require(all(flag is False for flag in actual["release"].values()),
            "attempt04 release flag is not false")
    return {
        "status": "verified",
        "manifest_path": OUTPUT.as_posix(),
        "manifest_sha256": actual["manifest_sha256"],
        "step_member_count": len(actual["finished_member_step_bindings"]),
        "mass_row_count": actual["evidence_bindings"]["source_to_mass_topology"]
        ["reconciled_facts"]["mass_inventory_rows"],
        "load_case_ids": [row["case_id"] for row in actual["applied_load_cases"]["cases"]],
        "frame_transverse_members": 20,
        "candidate_steel_axes_and_roles": [92, 460],
        "block_members_and_cases": [24, 48],
        "unassigned_panel_layups": 6,
        "unassigned_retained_hardware_roles": 60,
        "inputs_ready": False,
        "per_member_material_mapping_ready": False,
        "native_solve_executed": False,
        "release": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest_path = ROOT / OUTPUT
    readme_path = ROOT / README
    if args.verify:
        result = verify()
    else:
        if manifest_path.exists() or readme_path.exists():
            raise FileExistsError("attempt04 output already exists; preserve the snapshot")
        manifest = build_manifest()
        (ROOT / OUT_DIR).mkdir(parents=True, exist_ok=True)
        payload = json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
        with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        with readme_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_readme(manifest))
        result = {
            "status": "written",
            "manifest_path": OUTPUT.as_posix(),
            "manifest_sha256": manifest["manifest_sha256"],
            "step_member_count": len(manifest["finished_member_step_bindings"]),
            "inputs_ready": False,
            "native_solve_executed": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
