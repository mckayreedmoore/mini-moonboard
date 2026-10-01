"""Fail-closed aggregation boundary for the exact 47 wood-joint criteria.

This module does not calculate resistance. It verifies independently bound
scope, acceptance-contract and demand-source inputs before comparing producer
results. Empty or producer-authored coverage, acceptance terms, or demand
sources are never enough to close a criterion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CRITERIA_PATH = Path("docs/wood-joints-mvp/criteria.json")
COVERAGE_PATH = Path("docs/wood-joints-mvp/current-criteria-coverage.json")
METHOD_MAP_PATH = Path("docs/wood-joints-mvp/criteria-method-map.md")
CANDIDATE_PATH = Path("wood-joints-candidate.json")
SOURCE_INVENTORY_PATH = Path("docs/wood-joints-mvp/source-inventory.json")
DUTY_REGISTRY_PATH = Path("docs/wood-joints-mvp/duty-registry.json")
FRAME_MANIFEST_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/"
    "current-full-frame-input-manifest.json"
)
LOAD_CASES_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-load-cases.json"
)
TOPOLOGY_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-attachment-topology-attempt01/attachment-topology.json"
)
CRITERIA_OVERLAY_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-criteria-overlay-attempt02"
)
CRITERIA_OVERLAY_PATH = CRITERIA_OVERLAY_DIR / "source-overlay.json"
RECONCILIATION_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-criteria-method-map-reconciliation-attempt02"
)
RECONCILIATION_PATH = RECONCILIATION_DIR / "source-reconciliation.json"
RECONCILIATION_REVIEW_PATH = RECONCILIATION_DIR / "parent-review.json"
RECONCILIATION_SCRIPT_PATH = RECONCILIATION_DIR / "reconcile.py"
RECONCILIATION_README_PATH = RECONCILIATION_DIR / "README.md"

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CRITERION_COUNT = 47
HISTORICAL_METHOD_MAP_SHA256 = "1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80"
CURRENT_METHOD_MAP_SHA256 = "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7"
FROZEN_COVERAGE_SHA256 = "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c"
SOURCE_CRITERIA_SHA256 = "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784"
HISTORICAL_METHOD_MAP_COMMIT = "55ede246246842285d97946bde84f35f2362923b"
RECONCILED_METHOD_MAP_ROW_IDS = ("additional_group_reduction_sensitivity", "steel_direct")

CRITERIA_SCHEMA = "wood_joint_mvp_criteria/v1"
COVERAGE_SCHEMA = "wood_joint_current_criteria_coverage/v1"
EXPECTATIONS_SCHEMA = "wood_joint_criterion_expectations/v1"
EVIDENCE_SCHEMA = "wood_joint_criteria_evidence/v1"
AGGREGATE_SCHEMA = "wood_joint_criteria_aggregate/v1"
ACCEPTANCE_CONTRACT_SCHEMA = "wood_joint_acceptance_contract_manifest/v1"
DEMAND_MANIFEST_SCHEMA = "wood_joint_current_demand_manifest/v1"
SOURCE_OVERLAY_SCHEMA = "wood_joint_criteria_source_overlay/v2"

PRODUCER_STATUSES = {
    "unverified",
    "failed",
    "passed_under_recorded_assumptions",
    "not_applicable_with_reason",
}
COMPARISONS = {"<=", "<", ">=", ">", "=="}
REQUIRED_AUTHORITY_PATHS = {
    "criteria_register": CRITERIA_PATH.as_posix(),
    "coverage_plan": COVERAGE_PATH.as_posix(),
    "candidate_authority": CANDIDATE_PATH.as_posix(),
    "method_map": METHOD_MAP_PATH.as_posix(),
    "full_frame_manifest": FRAME_MANIFEST_PATH.as_posix(),
    "criteria_source_overlay": CRITERIA_OVERLAY_PATH.as_posix(),
    "method_map_reconciliation": RECONCILIATION_PATH.as_posix(),
    "method_map_reconciliation_review": RECONCILIATION_REVIEW_PATH.as_posix(),
    "method_map_reconciliation_script": RECONCILIATION_SCRIPT_PATH.as_posix(),
    "method_map_reconciliation_readme": RECONCILIATION_README_PATH.as_posix(),
}
ALLOWED_AUTHORITY_ROLES = {
    "criteria_register",
    "coverage_plan",
    "candidate_authority",
    "method_map",
    "source_inventory",
    "duty_registry",
    "full_frame_input_manifest",
    "load_case_contract",
    "attachment_topology",
    "independent_geometry_manifest",
    "independent_interface_manifest",
    "independent_demand_manifest",
    "independent_material_manifest",
    "independent_hardware_manifest",
    "independent_method_record",
    "independent_acceptance_manifest",
    "independent_scope_manifest",
    "source_overlay",
    "method_map_reconciliation",
    "source_reconciliation_review",
    "source_reconciliation_reproducer",
    "source_reconciliation_documentation",
}
AGGREGATE_STATUSES = {
    "pending",
    "failed",
    "conditional_pass",
    "not_applicable_with_reason",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rel_path(path: str | Path) -> str:
    return Path(path).as_posix()


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _criterion_rows(register: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if register.get("schema") != CRITERIA_SCHEMA:
        raise ValueError("Unsupported criteria register schema")
    if register.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Criteria register candidate differs from the wood-joint lane")
    rows: list[tuple[str, dict[str, Any]]] = []
    for item in register.get("legacy_criteria", []):
        rows.append((item.get("legacy_id", ""), item))
    for item in register.get("additional_candidate_obligations", []):
        rows.append((item.get("id", ""), item))
    ids = [criterion_id for criterion_id, _ in rows]
    if len(rows) != EXPECTED_CRITERION_COUNT or any(not _nonempty_text(item) for item in ids):
        raise ValueError(f"Criteria register must contain exactly {EXPECTED_CRITERION_COUNT} named rows")
    if len(set(ids)) != len(ids):
        raise ValueError("Criteria register contains duplicate IDs")
    return rows


def _pointer_values(document: Any, pointer: str) -> list[Any]:
    """Resolve a JSON pointer with `*` as an array/dict wildcard."""
    if pointer == "":
        return [document]
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"Invalid JSON pointer: {pointer!r}")
    current = [document]
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        next_values: list[Any] = []
        for node in current:
            if part == "*":
                if isinstance(node, list):
                    next_values.extend(node)
                elif isinstance(node, dict):
                    next_values.extend(node.values())
                continue
            if isinstance(node, list):
                try:
                    next_values.append(node[int(part)])
                except (ValueError, IndexError):
                    continue
            elif isinstance(node, dict) and part in node:
                next_values.append(node[part])
        current = next_values
    return current


def _source_bindings(
    expectations: dict[str, Any], source_root: Path
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    bindings: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    raw_bindings = expectations.get("source_bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        return {}, ["independent source_bindings are missing or empty"]
    for binding in raw_bindings:
        if not isinstance(binding, dict):
            issues.append("source binding is not an object")
            continue
        binding_id = binding.get("binding_id")
        rel = binding.get("path")
        expected_hash = binding.get("sha256")
        role = binding.get("role")
        if not all(_nonempty_text(value) for value in (binding_id, rel, expected_hash, role)):
            issues.append("source binding is missing binding_id, path, sha256, or role")
            continue
        if role in {"producer_evidence", "producer_coverage", "producer_output"}:
            issues.append(f"{binding_id}: producer-owned data cannot define expected coverage")
            continue
        if role not in ALLOWED_AUTHORITY_ROLES:
            issues.append(f"{binding_id}: source role is not an approved independent-input role")
            continue
        if binding_id in REQUIRED_AUTHORITY_PATHS and rel != REQUIRED_AUTHORITY_PATHS[binding_id]:
            issues.append(f"{binding_id}: required authority path cannot be redirected")
            continue
        if binding_id in bindings:
            issues.append(f"duplicate source binding ID: {binding_id}")
            continue
        path = source_root / rel
        if not path.is_file():
            issues.append(f"{binding_id}: source file is missing: {rel}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            issues.append(f"{binding_id}: stale source hash for {rel}")
            continue
        try:
            document = load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            document = None
        bindings[binding_id] = {
            **binding,
            "absolute_path": path,
            "document": document,
            "actual_sha256": actual_hash,
        }
    return bindings, issues


def _validate_criteria_source_overlay(
    coverage: dict[str, Any],
    bindings: dict[str, dict[str, Any]],
) -> tuple[bool, list[str]]:
    """Validate the reviewed working-tree source overlay for the frozen map pin."""
    issues: list[str] = []
    required = {
        "coverage_plan": "coverage_plan",
        "method_map": "method_map",
        "criteria_source_overlay": "source_overlay",
        "method_map_reconciliation": "method_map_reconciliation",
        "method_map_reconciliation_review": "source_reconciliation_review",
        "method_map_reconciliation_script": "source_reconciliation_reproducer",
        "method_map_reconciliation_readme": "source_reconciliation_documentation",
    }
    for binding_id, role in required.items():
        binding = bindings.get(binding_id)
        if binding is None:
            issues.append(f"source overlay requires independent {binding_id} binding")
        elif binding.get("role") != role:
            issues.append(f"source overlay binding {binding_id} has the wrong role")
    if issues:
        return False, issues

    coverage_binding = bindings["coverage_plan"]
    map_binding = bindings["method_map"]
    overlay_binding = bindings["criteria_source_overlay"]
    reconciliation_binding = bindings["method_map_reconciliation"]
    review_binding = bindings["method_map_reconciliation_review"]
    script_binding = bindings["method_map_reconciliation_script"]
    readme_binding = bindings["method_map_reconciliation_readme"]
    overlay = overlay_binding.get("document")
    reconciliation = reconciliation_binding.get("document")
    review = review_binding.get("document")
    if not isinstance(overlay, dict):
        issues.append("source overlay is not a JSON object")
        return False, issues
    if not isinstance(reconciliation, dict):
        issues.append("source reconciliation record is not a JSON object")
        return False, issues
    if not isinstance(review, dict):
        issues.append("source reconciliation review is not a JSON object")
        return False, issues

    if overlay.get("schema") != SOURCE_OVERLAY_SCHEMA:
        issues.append("source overlay schema is unsupported")
    if overlay.get("overlay_id") != "current-criteria-method-map-overlay-attempt02":
        issues.append("source overlay identity is unsupported")
    if coverage_binding.get("document") != coverage:
        issues.append("coverage payload differs from its hash-bound frozen source")

    source_criteria = coverage.get("source_criteria")
    if not isinstance(source_criteria, dict):
        issues.append("frozen coverage source does not contain a method-map pin")
        source_criteria = {}
    historical_hash = source_criteria.get("method_map_sha256")
    if source_criteria.get("method_map_path") != METHOD_MAP_PATH.as_posix():
        issues.append("frozen coverage method-map path is not the fixed authority path")
    coverage_sha = coverage_binding.get("actual_sha256")
    map_sha = map_binding.get("actual_sha256")
    overlay_coverage = overlay.get("frozen_coverage")
    overlay_map = overlay.get("method_map")
    overlay_reconciliation = overlay.get("reconciliation")
    overlay_review = overlay.get("coordinator_review")

    if coverage_binding.get("path") != COVERAGE_PATH.as_posix():
        issues.append("source overlay frozen coverage path is not the fixed authority path")
    if coverage_sha != FROZEN_COVERAGE_SHA256:
        issues.append("source overlay frozen coverage digest differs from the immutable reviewed pin")
    if not isinstance(overlay_coverage, dict):
        issues.append("source overlay lacks frozen coverage provenance")
    else:
        if overlay_coverage.get("path") != coverage_binding.get("path"):
            issues.append("source overlay coverage path differs from the independent binding")
        if overlay_coverage.get("sha256") != coverage_sha:
            issues.append("source overlay frozen coverage digest differs from the bound source")
        if overlay_coverage.get("historical_method_map_sha256") != historical_hash:
            issues.append("source overlay historical method-map hash differs from the frozen pin")
    if historical_hash != HISTORICAL_METHOD_MAP_SHA256:
        issues.append("frozen coverage historical method-map hash differs from the immutable reviewed pin")

    if map_binding.get("path") != METHOD_MAP_PATH.as_posix():
        issues.append("source overlay current method-map path is not the fixed authority path")
    if map_sha != CURRENT_METHOD_MAP_SHA256:
        issues.append("source overlay current method-map hash differs from the immutable reviewed working-tree pin")
    if not isinstance(overlay_map, dict):
        issues.append("source overlay lacks method-map provenance")
    else:
        if overlay_map.get("path") != map_binding.get("path"):
            issues.append("source overlay method-map path differs from the independent binding")
        if overlay_map.get("historical_sha256") != historical_hash:
            issues.append("source overlay historical method-map hash differs from the frozen pin")
        if overlay_map.get("current_sha256") != map_sha:
            issues.append("source overlay current method-map hash differs from the current bound source")
        if overlay_map.get("source_kind") != "exact_reviewed_working_tree_bytes":
            issues.append("source overlay does not identify its current map as pinned working-tree bytes")
        if overlay_map.get("changed_row_ids") != list(RECONCILED_METHOD_MAP_ROW_IDS):
            issues.append("source overlay changed method-map rows differ from the reviewed scope")

    if reconciliation.get("schema") != "wood_joint_criteria_method_map_reconciliation/v2":
        issues.append("source reconciliation record schema is unsupported")
    if reconciliation.get("artifact") != "current-criteria-method-map-reconciliation-attempt02":
        issues.append("source reconciliation record identity is unsupported")
    if reconciliation.get("historical_method_map_commit") != HISTORICAL_METHOD_MAP_COMMIT:
        issues.append("source reconciliation historical method-map commit is unsupported")
    source_files = reconciliation.get("source_files")
    map_record = source_files.get(METHOD_MAP_PATH.as_posix()) if isinstance(source_files, dict) else None
    coverage_record = source_files.get(COVERAGE_PATH.as_posix()) if isinstance(source_files, dict) else None
    if not isinstance(map_record, dict):
        issues.append("source reconciliation record lacks the method-map comparison")
        map_record = {}
    if not isinstance(coverage_record, dict):
        issues.append("source reconciliation record lacks the frozen coverage record")
        coverage_record = {}
    if map_record.get("historical_pinned_sha256") != historical_hash:
        issues.append("reconciliation historical method-map hash differs from the frozen pin")
    if map_record.get("current_working_tree_sha256") != map_sha:
        issues.append("reconciliation current method-map hash differs from the current bound source")
    if map_record.get("current_working_tree_sha256") != CURRENT_METHOD_MAP_SHA256:
        issues.append("reconciliation current method-map hash differs from the immutable reviewed working-tree pin")
    if map_record.get("source_kind") != "exact_reviewed_working_tree_bytes":
        issues.append("reconciliation does not identify exact reviewed working-tree bytes")
    if map_record.get("changed_row_ids") != list(RECONCILED_METHOD_MAP_ROW_IDS):
        issues.append("reconciliation changed method-map rows differ from the reviewed scope")
    if coverage_record.get("sha256") != coverage_sha:
        issues.append("reconciliation coverage digest differs from the frozen bound source")
    if coverage_record.get("sha256") != FROZEN_COVERAGE_SHA256:
        issues.append("reconciliation coverage digest differs from the immutable reviewed pin")
    if coverage_record.get("embedded_method_map_sha256") != historical_hash:
        issues.append("reconciliation embedded method-map hash differs from the frozen pin")
    coverage_rows = coverage.get("criteria")
    coverage_ids = [
        row.get("criterion_id") for row in coverage_rows if isinstance(row, dict)
    ] if isinstance(coverage_rows, list) else []
    if coverage_record.get("criteria_count") != EXPECTED_CRITERION_COUNT:
        issues.append("reconciliation coverage criterion count differs from exact47")
    if coverage_record.get("criterion_ids_sha256") != sha256_bytes("\n".join(coverage_ids).encode()):
        issues.append("reconciliation coverage criterion ID digest differs from the frozen source")
    criteria_record = source_files.get(CRITERIA_PATH.as_posix()) if isinstance(source_files, dict) else None
    if not isinstance(criteria_record, dict):
        issues.append("source reconciliation record lacks the source criteria record")
        criteria_record = {}
    if criteria_record.get("sha256") != SOURCE_CRITERIA_SHA256:
        issues.append("reconciliation source criteria digest differs from the immutable reviewed pin")
    if criteria_record.get("source_row_count") != EXPECTED_CRITERION_COUNT:
        issues.append("reconciliation source criteria row count differs from the exact47 register")
    checks = reconciliation.get("checks")
    required_checks = (
        "historical_map_matches_frozen_coverage_pin",
        "current_working_tree_map_matches_exact_reviewed_sha256",
        "frozen_coverage_matches_exact_reviewed_sha256",
        "source_criteria_matches_exact_reviewed_sha256",
        "changed_method_map_rows_match_reviewed_scope",
        "frozen_47_criterion_ids_match_source_criteria",
        "no_frozen_coverage_or_candidate_dispositions_changed",
    )
    if not isinstance(checks, dict) or any(checks.get(name) is not True for name in required_checks):
        issues.append("source reconciliation checks are incomplete or did not pass")

    if not isinstance(overlay_reconciliation, dict):
        issues.append("source overlay lacks a reconciliation-record binding")
    else:
        if overlay_reconciliation.get("path") != reconciliation_binding.get("path"):
            issues.append("source overlay reconciliation path differs from its independent binding")
        if overlay_reconciliation.get("sha256") != reconciliation_binding.get("actual_sha256"):
            issues.append("source overlay reconciliation hash differs from its independent binding")

    expected_review_status = "PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY"
    if review.get("schema") != "wood_joint_parent_review/v1":
        issues.append("coordinator review schema is unsupported")
    if review.get("reviewer") != "/root":
        issues.append("source overlay lacks the required coordinator reviewer identity")
    if review.get("status") != expected_review_status:
        issues.append("coordinator review status does not authorize provenance-only overlay use")
    if review.get("artifact") != "current-criteria-method-map-reconciliation-attempt02":
        issues.append("coordinator review is for a different artifact")
    reviewed_hashes = review.get("reviewed_hashes")
    if not isinstance(reviewed_hashes, dict):
        issues.append("coordinator review does not bind reviewed reconciliation inputs")
        reviewed_hashes = {}
    for filename, binding in (
        ("reconcile.py", script_binding),
        ("README.md", readme_binding),
        ("source-reconciliation.json", reconciliation_binding),
    ):
        if reviewed_hashes.get(filename) != binding.get("actual_sha256"):
            issues.append(f"coordinator review hash does not match {filename}")
    review_checks = review.get("independent_checks")
    required_review_checks = (
        "all_reproducer_checks_pass",
        "frozen_coverage_unchanged",
        "old_method_map_digest_matches_embedded_pin",
        "current_method_map_matches_reviewed_working_tree_bytes",
        "changed_rows_match_reviewed_scope",
        "all_47_criterion_ids_preserved",
        "no_criterion_dispositions_established",
    )
    if not isinstance(review_checks, dict) or any(review_checks.get(name) is not True for name in required_review_checks):
        issues.append("coordinator review does not confirm the required provenance checks")

    if not isinstance(overlay_review, dict):
        issues.append("source overlay lacks explicit coordinator-review provenance")
    else:
        if overlay_review.get("path") != review_binding.get("path"):
            issues.append("source overlay review path differs from its independent binding")
        if overlay_review.get("sha256") != review_binding.get("actual_sha256"):
            issues.append("source overlay review hash differs from its independent binding")
        if overlay_review.get("reviewer") != review.get("reviewer"):
            issues.append("source overlay reviewer identity differs from the reviewed source")
        if overlay_review.get("status") != review.get("status"):
            issues.append("source overlay reviewer status differs from the reviewed source")
        if overlay_review.get("artifact") != review.get("artifact"):
            issues.append("source overlay review artifact differs from the reviewed source")

    if historical_hash == map_sha:
        issues.append("source overlay is unnecessary because the frozen map pin already matches current source")
    return not issues, issues


def _validate_identity(
    criteria: dict[str, Any],
    coverage: dict[str, Any],
    candidate: dict[str, Any],
    frame_manifest: dict[str, Any],
    source_root: Path,
    *,
    source_overlay_valid: bool = False,
) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    criterion_rows = _criterion_rows(criteria)
    expected_ids = {criterion_id for criterion_id, _ in criterion_rows}
    coverage_ids = {
        row.get("criterion_id")
        for row in coverage.get("criteria", [])
        if isinstance(row, dict)
    }
    if coverage.get("schema") != COVERAGE_SCHEMA or coverage.get("candidate") != EXPECTED_CANDIDATE:
        issues.append("planning coverage register has the wrong schema or candidate")
    if coverage_ids != expected_ids or len(coverage.get("criteria", [])) != EXPECTED_CRITERION_COUNT:
        issues.append("planning coverage rows do not match the exact 47 criterion IDs")
    if not isinstance(coverage.get("source_criteria"), dict):
        issues.append("planning coverage does not pin its source criteria register")
    else:
        if coverage["source_criteria"].get("sha256") != criteria.get("_sha256"):
            issues.append("planning coverage is stale against criteria.json")
        map_path = coverage["source_criteria"].get("method_map_path")
        map_expected = coverage["source_criteria"].get("method_map_sha256")
        if not _nonempty_text(map_path) or not _nonempty_text(map_expected):
            issues.append("planning coverage does not contain a complete method-map source pin")
        elif map_path:
            resolved_map = Path(source_root) / map_path
            if not resolved_map.is_file() or sha256_file(resolved_map) != map_expected:
                if not source_overlay_valid:
                    issues.append("planning coverage is stale against its method map")
    pin = coverage.get("current_geometry_pin", {})
    revision = pin.get("revision_id") if isinstance(pin, dict) else None
    manifest_revision = frame_manifest.get("geometry_revision_id")
    if revision != EXPECTED_REVISION or manifest_revision != revision:
        issues.append("reviewed revision does not match the pinned full-frame input manifest")
    if candidate.get("candidate") != EXPECTED_CANDIDATE or frame_manifest.get("candidate") != EXPECTED_CANDIDATE:
        issues.append("candidate identity differs across authority inputs")
    if frame_manifest.get("schema") != "wood_joint_current_full_frame_input_manifest/v3":
        issues.append("current full-frame input manifest schema is unsupported")
    selected = frame_manifest.get("selected_candidate_authority_preserved")
    if selected != "compact-floor-flush-development":
        issues.append("selected-candidate authority is not preserved by the full-frame manifest")
    return issues, sorted(expected_ids)


def _record_lookup(
    expectations: dict[str, Any], evidence: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    expected_rows = expectations.get("criteria")
    issues: list[str] = []
    if not isinstance(expected_rows, list):
        return {}, ["expectations.criteria is missing or is not a list"]
    ids = [row.get("criterion_id") for row in expected_rows if isinstance(row, dict)]
    if len(ids) != EXPECTED_CRITERION_COUNT or len(set(ids)) != EXPECTED_CRITERION_COUNT:
        issues.append("expectations must contain exactly one row for each of the 47 criteria")
    records = evidence.get("records") if isinstance(evidence, dict) else None
    if not isinstance(records, list):
        return {}, issues + ["evidence records are missing or are not a list"]
    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict):
            issues.append("evidence record is not an object")
            continue
        forbidden_fields = {"expected_coverage", "scope_cells", "acceptance_contract", "demand_source"}
        if forbidden_fields.intersection(record):
            issues.append("producer evidence cannot supply independent coverage, acceptance, or demand bindings")
        criterion_id = record.get("criterion_id")
        if not _nonempty_text(criterion_id):
            issues.append("evidence record has no criterion_id")
            continue
        by_id.setdefault(criterion_id, []).append(record)
    return by_id, issues


def _resolve_acceptance_contract(
    cell: dict[str, Any],
    criterion_id: str,
    candidate_id: str,
    revision_id: str,
    bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    issues: list[str] = []
    reference = cell.get("acceptance_contract_source")
    if not isinstance(reference, dict):
        return None, None, ["open field: independent acceptance_contract_source is missing"]
    binding = bindings.get(reference.get("binding_id"))
    pointer = reference.get("json_pointer")
    if not binding or binding.get("role") != "independent_acceptance_manifest":
        return None, None, ["acceptance contract must resolve from an independent_acceptance_manifest binding"]
    if not _nonempty_text(pointer) or binding.get("document") is None:
        return None, binding, ["acceptance contract source pointer is missing or is not JSON"]
    if not isinstance(binding["document"], dict):
        return None, binding, ["acceptance contract manifest is not a JSON object"]
    if binding["document"].get("schema") != ACCEPTANCE_CONTRACT_SCHEMA:
        issues.append("acceptance contract manifest has an unsupported schema")
    try:
        values = _pointer_values(binding["document"], pointer)
    except ValueError as error:
        return None, binding, [str(error)]
    if len(values) != 1 or not isinstance(values[0], dict):
        return None, binding, ["acceptance contract pointer must resolve to exactly one object"]
    contract = values[0]
    for key, expected in (
        ("candidate", candidate_id),
        ("revision_id", revision_id),
        ("criterion_id", criterion_id),
        ("scope_id", cell.get("scope_id")),
    ):
        if contract.get(key) != expected:
            issues.append(f"acceptance contract {key} does not match its independently expected scope")
    for key in ("method_id", "version", "scope", "unit"):
        if not _nonempty_text(contract.get(key)):
            issues.append(f"acceptance contract is missing {key}")
    if contract.get("comparison") not in COMPARISONS:
        issues.append("acceptance contract has no supported comparison")
    if not _finite_number(contract.get("limit")):
        issues.append("acceptance contract limit must be finite")
    return contract, binding, issues


def _resolve_demand_source(
    cell: dict[str, Any],
    candidate_id: str,
    revision_id: str,
    bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    case_id = cell.get("case_id")
    reference = cell.get("demand_source")
    if case_id is None:
        if reference is not None:
            return None, None, ["static scope cannot declare a demand source"]
        return None, None, []
    if not isinstance(reference, dict):
        return None, None, ["open field: independent demand_source binding is missing"]
    binding = bindings.get(reference.get("binding_id"))
    pointer = reference.get("json_pointer")
    if not binding or binding.get("role") != "independent_demand_manifest":
        return None, None, ["case-based scope requires an independent_demand_manifest binding"]
    document = binding.get("document")
    if not isinstance(document, dict):
        return None, binding, ["independent demand source is not a JSON object"]
    issues: list[str] = []
    if document.get("schema") != DEMAND_MANIFEST_SCHEMA:
        issues.append("independent demand manifest has an unsupported schema")
    if document.get("candidate") != candidate_id or document.get("revision_id") != revision_id:
        issues.append("independent demand manifest candidate/revision is stale or mismatched")
    if document.get("fresh_current_demands") is not True:
        issues.append("independent demand manifest does not declare fresh current demands")
    if not _nonempty_text(pointer):
        return None, binding, issues + ["independent demand source JSON pointer is missing"]
    try:
        values = _pointer_values(document, pointer)
    except ValueError as error:
        return None, binding, issues + [str(error)]
    if len(values) != 1 or not isinstance(values[0], dict):
        return None, binding, issues + ["independent demand pointer must resolve to exactly one case record"]
    demand_record = values[0]
    if demand_record.get("case_id") != case_id:
        issues.append("independent demand source pointer resolves to the wrong case")
    wrench = demand_record.get("wrench")
    if not isinstance(wrench, dict):
        issues.append("independent demand case record lacks its simultaneous wrench")
    else:
        for key, length in (("force_xyz", 3), ("moment_xyz", 3), ("datum_xyz", 3)):
            vector = wrench.get(key)
            if not isinstance(vector, list) or len(vector) != length or not all(_finite_number(value) for value in vector):
                issues.append(f"independent demand {key} must contain three finite values")
        units = wrench.get("units")
        if not isinstance(units, dict) or not all(
            _nonempty_text(units.get(key)) for key in ("force", "moment", "length")
        ):
            issues.append("independent demand wrench units are incomplete")
    return demand_record, binding, issues


def _validate_expectation_row(
    row: dict[str, Any],
    criterion_id: str,
    candidate_id: str,
    revision_id: str,
    bindings: dict[str, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if row.get("criterion_id") != criterion_id:
        return [f"expectation ID mismatch (expected {criterion_id})"]
    applicability = row.get("applicability")
    if applicability not in {"applicable", "unresolved", "not_applicable"}:
        issues.append("unsupported applicability value")
        return issues
    cells = row.get("scope_cells")
    if not isinstance(cells, list):
        return issues + ["scope_cells is missing or is not a list"]
    if applicability == "unresolved":
        if not _nonempty_text(row.get("reason")):
            issues.append("unresolved applicability requires a reason")
        if cells:
            issues.append("unresolved scope cannot assert complete scope cells")
        return issues
    if applicability == "not_applicable":
        if cells:
            issues.append("not-applicable criterion cannot contain applicable scope cells")
        if not _nonempty_text(row.get("not_applicable_reason")):
            issues.append("not-applicable criterion requires a reason")
        replacements = row.get("replacement_criterion_ids")
        obligations = row.get("preserved_obligation_ids")
        if not isinstance(replacements, list) or not replacements or any(not _nonempty_text(x) for x in replacements):
            issues.append("not-applicable criterion must name replacement criterion IDs")
        if not isinstance(obligations, list) or not obligations or any(not _nonempty_text(x) for x in obligations):
            issues.append("not-applicable criterion must preserve nonempty replacement obligations")
        obligation_refs = row.get("preserved_obligation_sources")
        if not isinstance(obligation_refs, list) or not obligation_refs:
            issues.append("not-applicable criterion must source-bind its preserved obligations")
        else:
            resolved_obligations: set[str] = set()
            for reference in obligation_refs:
                if not isinstance(reference, dict):
                    issues.append("malformed preserved-obligation source reference")
                    continue
                binding = bindings.get(reference.get("binding_id"))
                obligation_id = reference.get("obligation_id")
                value = reference.get("value")
                pointer = reference.get("json_pointer")
                if not binding or not all(_nonempty_text(item) for item in (obligation_id, value, pointer)):
                    issues.append("preserved-obligation source reference is incomplete")
                    continue
                try:
                    values = _pointer_values(binding["document"], pointer)
                except ValueError as error:
                    issues.append(str(error))
                    continue
                if value not in values or obligation_id not in obligations:
                    issues.append(f"preserved obligation {obligation_id!r} is not present in its authority source")
                    continue
                resolved_obligations.add(obligation_id)
            if resolved_obligations != set(obligations):
                issues.append("every preserved obligation must have an exact source reference")
        return issues
    if not cells:
        return issues + ["applicable criterion has empty independent scope coverage"]
    scope_ids: set[str] = set()
    for cell_index, cell in enumerate(cells):
        prefix = f"scope cell {cell_index}"
        if not isinstance(cell, dict):
            issues.append(f"{prefix} is not an object")
            continue
        scope_id = cell.get("scope_id")
        if not _nonempty_text(scope_id):
            issues.append(f"{prefix} has no scope_id")
        elif scope_id in scope_ids:
            issues.append(f"duplicate scope_id: {scope_id}")
        else:
            scope_ids.add(scope_id)
        station_id = cell.get("station_id")
        interface_id = cell.get("interface_id")
        case_id = cell.get("case_id")
        if any(value is not None and not _nonempty_text(value) for value in (station_id, interface_id, case_id)):
            issues.append(f"{prefix} has an empty station/interface/case identity")
        entity_ids = cell.get("entity_ids", [])
        if not isinstance(entity_ids, list):
            issues.append(f"{prefix} entity_ids is not a list")
            entity_ids = []
        if not any(value is not None for value in (station_id, interface_id, case_id)) and not entity_ids:
            issues.append(f"{prefix} has no station, interface, case, or other entity identity")
        if case_id is None and not _nonempty_text(cell.get("static_scope_reason")):
            issues.append(f"{prefix} has no case but lacks an explicit static-scope reason")
        source_refs = cell.get("authoritative_ids")
        if not isinstance(source_refs, list) or not source_refs:
            issues.append(f"{prefix} has no independent authoritative identifier references")
            continue
        checked_refs: list[tuple[str, str]] = []
        for source_ref in source_refs:
            if not isinstance(source_ref, dict):
                issues.append(f"{prefix} contains a malformed authoritative identifier reference")
                continue
            binding = bindings.get(source_ref.get("binding_id"))
            kind = source_ref.get("kind")
            value = source_ref.get("value")
            pointer = source_ref.get("json_pointer")
            if not binding or binding.get("document") is None:
                issues.append(f"{prefix} references an unavailable JSON authority binding")
                continue
            if not all(_nonempty_text(item) for item in (kind, value, pointer)):
                issues.append(f"{prefix} has an incomplete authoritative identifier reference")
                continue
            try:
                values = _pointer_values(binding["document"], pointer)
            except ValueError as error:
                issues.append(f"{prefix}: {error}")
                continue
            if value not in values:
                issues.append(f"{prefix} identifier {value!r} is absent from {binding['path']}#{pointer}")
                continue
            checked_refs.append((kind, value))
        for kind, expected_value in (
            ("station_id", station_id),
            ("interface_id", interface_id),
            ("case_id", case_id),
        ):
            if expected_value is not None and (kind, expected_value) not in checked_refs:
                issues.append(f"{prefix} {kind} is not bound to an independent manifest identifier")
        for entity in entity_ids:
            if not isinstance(entity, dict) or not _nonempty_text(entity.get("kind")) or not _nonempty_text(entity.get("id")):
                issues.append(f"{prefix} has a malformed entity ID")
            elif (entity["kind"], entity["id"]) not in checked_refs:
                issues.append(f"{prefix} entity {entity['id']!r} is not bound to an independent manifest identifier")
        _, _, acceptance_issues = _resolve_acceptance_contract(
            cell, criterion_id, candidate_id, revision_id, bindings
        )
        issues.extend(f"{prefix}: {item}" for item in acceptance_issues)
        _, _, demand_issues = _resolve_demand_source(
            cell, candidate_id, revision_id, bindings
        )
        issues.extend(f"{prefix}: {item}" for item in demand_issues)
    return issues


def _compare(result: float, limit: float, comparison: str) -> bool:
    if comparison == "<=":
        return result <= limit
    if comparison == "<":
        return result < limit
    if comparison == ">=":
        return result >= limit
    if comparison == ">":
        return result > limit
    if comparison == "==":
        return result == limit
    raise ValueError("unsupported comparison")


def _validate_record(
    record: dict[str, Any],
    cell: dict[str, Any],
    *,
    criterion_id: str,
    candidate_id: str,
    revision_id: str,
    bindings: dict[str, dict[str, Any]],
    acceptance_contract: dict[str, Any] | None,
    acceptance_binding: dict[str, Any] | None,
    expected_demand_record: dict[str, Any] | None,
    demand_binding: dict[str, Any] | None,
    source_root: Path,
    synthetic: bool,
    current_demands_available: bool,
) -> list[str]:
    issues: list[str] = []
    if record.get("candidate") != candidate_id:
        issues.append("candidate identity is stale or mismatched")
    if record.get("revision_id") != revision_id:
        issues.append("revision identity is stale or mismatched")
    if record.get("scope_id") != cell.get("scope_id"):
        issues.append("scope_id does not match the independent expectation")
    if record.get("coverage") != {
        key: cell.get(key)
        for key in ("station_id", "interface_id", "case_id", "entity_ids", "static_scope_reason")
        if key in cell
    }:
        issues.append("producer coverage differs from the exact independently expected scope")
    status = record.get("status")
    if status not in PRODUCER_STATUSES:
        issues.append("unsupported producer status")
        return issues
    if status == "not_applicable_with_reason":
        issues.append("not-applicable evidence is allowed only for independently justified N/A expectations")
        return issues
    if status == "unverified":
        return issues + ["producer evidence remains unverified"]
    if status not in {"failed", "passed_under_recorded_assumptions"}:
        return issues + ["unsupported producer disposition"]

    method = record.get("method")
    if acceptance_contract is None or acceptance_binding is None:
        issues.append("open field: independent acceptance contract is unresolved")
    if not isinstance(method, dict) or not all(
        _nonempty_text(method.get(key)) for key in ("method_id", "version", "scope", "source_path", "source_sha256")
    ):
        issues.append("method ID, version, scope, and source binding are required")
    elif acceptance_contract is not None and acceptance_binding is not None:
        for evidence_key, contract_key in (
            ("method_id", "method_id"),
            ("version", "version"),
            ("scope", "scope"),
        ):
            if method.get(evidence_key) != acceptance_contract.get(contract_key):
                issues.append(f"producer {evidence_key} differs from the independent acceptance contract")
        if method.get("source_path") != acceptance_binding.get("path"):
            issues.append("producer method source path differs from the independent acceptance binding")
        if method.get("source_sha256") != acceptance_binding.get("actual_sha256"):
            issues.append("producer method source hash differs from the independent acceptance binding")

    result = record.get("result")
    limit = record.get("limit")
    comparison = record.get("comparison")
    result_unit = record.get("result_unit")
    limit_unit = record.get("limit_unit")
    if not _finite_number(result) or not _finite_number(limit):
        issues.append("result and limit must both be finite numeric values")
    if comparison not in COMPARISONS:
        issues.append("comparison operator is missing or unsupported")
    if not _nonempty_text(result_unit) or result_unit != limit_unit:
        issues.append("result and limit must declare the same nonempty unit")
    if acceptance_contract is not None:
        if comparison != acceptance_contract.get("comparison"):
            issues.append("producer comparison differs from the independent acceptance contract")
        if limit != acceptance_contract.get("limit"):
            issues.append("producer limit differs from the independent acceptance contract")
        if result_unit != acceptance_contract.get("unit") or limit_unit != acceptance_contract.get("unit"):
            issues.append("producer units differ from the independent acceptance contract")
    if not _nonempty_text(record.get("governing_mode")):
        issues.append("governing failure mode is missing")
    limits = record.get("known_limits")
    if not isinstance(limits, list) or not limits or any(not _nonempty_text(item) for item in limits):
        issues.append("known limits must be a nonempty list of statements")

    case_id = cell.get("case_id")
    demand = record.get("simultaneous_demand")
    if case_id is None:
        if demand is not None:
            issues.append("static scope must not invent a simultaneous demand")
        if record.get("governing_case_id") is not None:
            issues.append("static scope must not invent a governing load case")
    else:
        if not current_demands_available and not synthetic:
            issues.append("current full-frame demands are unavailable for a load-case scope")
        if expected_demand_record is None or demand_binding is None:
            issues.append("open field: independently bound current demand source is unresolved")
        if not isinstance(demand, dict):
            issues.append("load-case evidence requires an independently bound simultaneous-demand source")
        else:
            if demand.get("case_id") != case_id or record.get("governing_case_id") != case_id:
                issues.append("demand and governing case must equal the independently expected case")
            if demand_binding is not None:
                expected_demand_ref = cell.get("demand_source", {})
                if demand.get("source_binding_id") != expected_demand_ref.get("binding_id"):
                    issues.append("producer demand binding ID differs from the independent demand source")
                if demand.get("source_path") != demand_binding.get("path"):
                    issues.append("producer demand source path differs from the independent demand binding")
                if demand.get("source_sha256") != demand_binding.get("actual_sha256"):
                    issues.append("producer demand source hash differs from the independent demand binding")
                if demand.get("source_json_pointer") != expected_demand_ref.get("json_pointer"):
                    issues.append("producer demand pointer differs from the independent demand binding")
            demand_path = demand.get("source_path")
            demand_hash = demand.get("source_sha256")
            if not _nonempty_text(demand_path) or not _nonempty_text(demand_hash):
                issues.append("simultaneous-demand source path/hash is missing")
            else:
                rel = _rel_path(demand_path)
                if record.get("source_hashes", {}).get(rel) != demand_hash:
                    issues.append("simultaneous-demand source is not bound by the evidence row")
                source = source_root / rel
                if not source.is_file() or sha256_file(source) != demand_hash:
                    issues.append("simultaneous-demand source hash is stale")
                else:
                    pointer = demand.get("source_json_pointer")
                    if not _nonempty_text(pointer):
                        issues.append("simultaneous-demand source JSON pointer is missing")
                    else:
                        try:
                            source_document = load_json(source)
                            source_rows = _pointer_values(source_document, pointer)
                        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                            issues.append(f"simultaneous-demand source record cannot be read: {error}")
                        else:
                            if len(source_rows) != 1 or not isinstance(source_rows[0], dict):
                                issues.append("simultaneous-demand pointer must resolve to one case record")
                            else:
                                source_row = source_rows[0]
                                if source_row.get("case_id") != case_id:
                                    issues.append("simultaneous-demand source record has the wrong case ID")
                                if source_row.get("wrench") != demand.get("wrench"):
                                    issues.append("signed simultaneous wrench differs from its source record")
                                if expected_demand_record is not None and source_row != expected_demand_record:
                                    issues.append("producer demand record differs from the independent expected case record")
            wrench = demand.get("wrench")
            if not isinstance(wrench, dict):
                issues.append("simultaneous demand must contain one signed wrench")
            else:
                force = wrench.get("force_xyz")
                moment = wrench.get("moment_xyz")
                datum = wrench.get("datum_xyz")
                if not isinstance(force, list) or len(force) != 3 or not all(_finite_number(x) for x in force):
                    issues.append("simultaneous force vector must contain three finite signed values")
                if not isinstance(moment, list) or len(moment) != 3 or not all(_finite_number(x) for x in moment):
                    issues.append("simultaneous moment vector must contain three finite signed values")
                if not isinstance(datum, list) or len(datum) != 3 or not all(_finite_number(x) for x in datum):
                    issues.append("simultaneous demand datum must contain three finite coordinates")
                units = wrench.get("units")
                if not isinstance(units, dict) or not all(_nonempty_text(units.get(key)) for key in ("force", "moment", "length")):
                    issues.append("simultaneous demand force, moment, and length units are required")

    source_hashes = record.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        issues.append("evidence row has empty source hashes")
    else:
        mandatory_bindings = {
            "criteria_register",
            "coverage_plan",
            "candidate_authority",
            "full_frame_manifest",
            "criteria_source_overlay",
            "method_map_reconciliation",
            "method_map_reconciliation_review",
        }
        mandatory_paths = {
            bindings[binding_id]["path"]
            for binding_id in mandatory_bindings
            if binding_id in bindings
        }
        for source_ref in cell.get("authoritative_ids", []):
            binding = bindings.get(source_ref.get("binding_id")) if isinstance(source_ref, dict) else None
            if binding:
                mandatory_paths.add(binding["path"])
        if acceptance_binding is not None:
            mandatory_paths.add(acceptance_binding["path"])
        if demand_binding is not None:
            mandatory_paths.add(demand_binding["path"])
        for path in mandatory_paths:
            if path not in source_hashes:
                issues.append(f"evidence row omits expected-scope authority source: {path}")
        if not mandatory_paths.issubset(set(source_hashes)):
            issues.append("evidence row omits one or more core authority source hashes")
        for rel, expected_hash in source_hashes.items():
            if not _nonempty_text(rel) or not _nonempty_text(expected_hash):
                issues.append("evidence source hash map contains an empty path or hash")
                continue
            path = source_root / rel
            if not path.is_file() or sha256_file(path) != expected_hash:
                issues.append(f"stale or missing evidence source hash: {rel}")
    if not issues:
        try:
            passes = _compare(float(result), float(limit), comparison)
        except (TypeError, ValueError, OverflowError):
            issues.append("numeric comparison could not be evaluated")
        else:
            if status == "passed_under_recorded_assumptions" and not passes:
                issues.append("producer marked a failing comparison as passed")
            if status == "failed" and passes:
                issues.append("producer marked a passing comparison as failed")
    return issues


def _validate_na_replacement_rows(expectation_rows: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    for criterion_id, row in expectation_rows.items():
        if row.get("applicability") != "not_applicable":
            continue
        replacements = row.get("replacement_criterion_ids", [])
        obligations = set(row.get("preserved_obligation_ids", []))
        replacement_coverage: set[str] = set()
        for replacement_id in replacements:
            replacement = expectation_rows.get(replacement_id)
            if replacement is None:
                problems.setdefault(criterion_id, []).append(f"unknown replacement criterion: {replacement_id}")
            elif replacement.get("applicability") != "applicable":
                problems.setdefault(criterion_id, []).append(f"replacement criterion {replacement_id} is not applicable")
            else:
                replacement_coverage.update(replacement.get("covers_obligation_ids", []))
        if not obligations or not obligations.issubset(replacement_coverage):
            problems.setdefault(criterion_id, []).append(
                "N/A would drop one or more required replacement obligations"
            )
    return problems


def aggregate_documents(
    criteria: dict[str, Any],
    coverage: dict[str, Any],
    candidate: dict[str, Any],
    frame_manifest: dict[str, Any],
    expectations: dict[str, Any],
    evidence: dict[str, Any],
    *,
    source_root: Path = ROOT,
    expectation_sha256: str | None = None,
) -> dict[str, Any]:
    """Aggregate producer rows against an independent exact-scope manifest."""
    source_root = Path(source_root)
    criteria_sha = criteria.get("_sha256")
    if not criteria_sha:
        criteria_sha = sha256_bytes(json.dumps(criteria, sort_keys=True).encode())
    bindings, source_issues = _source_bindings(expectations, source_root)
    source_overlay_valid, overlay_issues = _validate_criteria_source_overlay(coverage, bindings)
    identity_issues, exact_ids = _validate_identity(
        criteria,
        coverage,
        candidate,
        frame_manifest,
        source_root,
        source_overlay_valid=source_overlay_valid,
    )
    identity_issues.extend(source_issues)
    identity_issues.extend(overlay_issues)
    expected_candidate = expectations.get("candidate")
    expected_revision = expectations.get("revision_id")
    if expectations.get("schema") != EXPECTATIONS_SCHEMA:
        identity_issues.append("independent expectations schema is unsupported")
    if expected_candidate != EXPECTED_CANDIDATE or candidate.get("candidate") != expected_candidate:
        identity_issues.append("expectations, candidate authority, and criteria candidate differ")
    revision_pin = coverage.get("current_geometry_pin", {}).get("revision_id")
    if expected_revision != revision_pin or expected_revision != frame_manifest.get("geometry_revision_id"):
        identity_issues.append("expectations do not match the current reviewed geometry revision")

    binding_paths = {binding.get("path") for binding in bindings.values()}
    if len(binding_paths) != len(bindings):
        identity_issues.append("independent source bindings reuse a path ambiguously")
    for binding_id in (
        "criteria_register",
        "coverage_plan",
        "candidate_authority",
        "full_frame_manifest",
        "criteria_source_overlay",
        "method_map_reconciliation",
        "method_map_reconciliation_review",
    ):
        if binding_id not in bindings:
            identity_issues.append(f"required independent source binding is absent: {binding_id}")

    expectation_rows_list = expectations.get("criteria", [])
    expectation_rows = {
        row.get("criterion_id"): row
        for row in expectation_rows_list
        if isinstance(row, dict) and _nonempty_text(row.get("criterion_id"))
    } if isinstance(expectation_rows_list, list) else {}
    if set(expectation_rows) != set(exact_ids) or len(expectation_rows_list) != EXPECTED_CRITERION_COUNT:
        identity_issues.append("independent expectations do not contain exactly the 47 criterion IDs")
    expectation_row_issues: dict[str, list[str]] = {}
    for criterion_id in exact_ids:
        row = expectation_rows.get(criterion_id)
        if row is None:
            expectation_row_issues[criterion_id] = ["independent expected-scope row is missing"]
            continue
        row_issues = _validate_expectation_row(
            row,
            criterion_id,
            expected_candidate,
            expected_revision,
            bindings,
        )
        if row_issues:
            expectation_row_issues[criterion_id] = row_issues
    expectation_row_issues.update(_validate_na_replacement_rows(expectation_rows))

    evidence_candidate_ok = evidence.get("candidate") == expected_candidate
    evidence_revision_ok = evidence.get("revision_id") == expected_revision
    synthetic = evidence.get("synthetic_fixture") is True
    if synthetic and evidence.get("synthetic_fixture_ack") != "TEST_ONLY_NOT_ENGINEERING_EVIDENCE":
        identity_issues.append("synthetic fixture marker lacks its test-only acknowledgement")
        synthetic = False
    if evidence.get("schema") != EVIDENCE_SCHEMA:
        identity_issues.append("evidence bundle schema is unsupported")
    if not evidence_candidate_ok or not evidence_revision_ok:
        identity_issues.append("evidence bundle candidate/revision identity is stale or mismatched")
    by_id, lookup_issues = _record_lookup(expectations, evidence)
    identity_issues.extend(lookup_issues)
    unknown_evidence_ids = set(by_id) - set(exact_ids)
    if unknown_evidence_ids:
        identity_issues.append(
            "evidence contains IDs outside the exact 47-row register: "
            + ", ".join(sorted(unknown_evidence_ids))
        )
    current_demands = frame_manifest.get("readiness", {}).get("current_full_frame_demands_available") is True

    results: list[dict[str, Any]] = []
    for criterion_id in exact_ids:
        expected_row = expectation_rows.get(criterion_id)
        criterion_records = by_id.get(criterion_id, [])
        reasons = list(identity_issues)
        reasons.extend(expectation_row_issues.get(criterion_id, []))
        if expected_row is None:
            results.append({"criterion_id": criterion_id, "status": "pending", "reasons": reasons})
            continue
        applicability = expected_row.get("applicability")
        if applicability == "unresolved":
            reasons.append(expected_row.get("reason", "expected applicability and coverage are unresolved"))
            results.append({"criterion_id": criterion_id, "status": "pending", "reasons": _unique(reasons)})
            continue
        if criterion_id in expectation_row_issues:
            results.append({"criterion_id": criterion_id, "status": "pending", "reasons": _unique(reasons)})
            continue
        if applicability == "not_applicable":
            if len(criterion_records) != 1:
                reasons.append("one source-bound not-applicable evidence record is required")
                results.append({"criterion_id": criterion_id, "status": "pending", "reasons": _unique(reasons)})
                continue
            record = criterion_records[0]
            if record.get("status") != "not_applicable_with_reason":
                reasons.append("producer disposition does not match the justified N/A expectation")
            if record.get("candidate") != expected_candidate or record.get("revision_id") != expected_revision:
                reasons.append("not-applicable evidence candidate/revision is stale")
            if record.get("not_applicable_reason") != expected_row.get("not_applicable_reason"):
                reasons.append("not-applicable evidence reason differs from independent justification")
            if record.get("preserved_obligation_ids") != expected_row.get("preserved_obligation_ids"):
                reasons.append("not-applicable evidence does not preserve the required replacement obligations")
            required_binding_ids = {
                "criteria_register",
                "coverage_plan",
                "candidate_authority",
                "full_frame_manifest",
                "criteria_source_overlay",
                "method_map_reconciliation",
                "method_map_reconciliation_review",
            }
            for reference in expected_row.get("preserved_obligation_sources", []):
                if isinstance(reference, dict) and reference.get("binding_id"):
                    required_binding_ids.add(reference["binding_id"])
            reasons.extend(_validate_record_source_hashes(record, bindings, source_root, required_binding_ids))
            status = "not_applicable_with_reason" if not reasons else "pending"
            results.append({"criterion_id": criterion_id, "status": status, "reasons": _unique(reasons)})
            continue

        expected_cells = expected_row.get("scope_cells", [])
        cells_by_scope = {cell.get("scope_id"): cell for cell in expected_cells if isinstance(cell, dict)}
        records_by_scope: dict[str, list[dict[str, Any]]] = {}
        for record in criterion_records:
            records_by_scope.setdefault(record.get("scope_id"), []).append(record)
        if not expected_cells:
            reasons.append("applicable criterion has no independently expected coverage cells")
        for scope_id in cells_by_scope:
            rows_for_scope = records_by_scope.get(scope_id, [])
            if not rows_for_scope:
                reasons.append(f"missing evidence for expected scope {scope_id}")
            elif len(rows_for_scope) > 1:
                reasons.append(f"duplicate evidence rows for expected scope {scope_id}")
        extra_scope_ids = set(records_by_scope) - set(cells_by_scope)
        if extra_scope_ids:
            reasons.append("evidence contains unrecognized scope IDs: " + ", ".join(sorted(str(x) for x in extra_scope_ids)))

        row_statuses: list[str] = []
        valid_failures = 0
        for scope_id, cell in cells_by_scope.items():
            rows_for_scope = records_by_scope.get(scope_id, [])
            if len(rows_for_scope) != 1:
                continue
            record = rows_for_scope[0]
            acceptance_contract, acceptance_binding, acceptance_issues = _resolve_acceptance_contract(
                cell,
                criterion_id,
                expected_candidate,
                expected_revision,
                bindings,
            )
            expected_demand_record, demand_binding, demand_issues = _resolve_demand_source(
                cell,
                expected_candidate,
                expected_revision,
                bindings,
            )
            row_issues = _validate_record(
                record,
                cell,
                criterion_id=criterion_id,
                candidate_id=expected_candidate,
                revision_id=expected_revision,
                bindings=bindings,
                acceptance_contract=acceptance_contract,
                acceptance_binding=acceptance_binding,
                expected_demand_record=expected_demand_record,
                demand_binding=demand_binding,
                source_root=source_root,
                synthetic=synthetic,
                current_demands_available=current_demands,
            )
            row_issues.extend(acceptance_issues)
            row_issues.extend(demand_issues)
            reasons.extend(f"{scope_id}: {item}" for item in row_issues)
            if not row_issues:
                row_statuses.append(record["status"])
                if record["status"] == "failed":
                    valid_failures += 1
        if valid_failures:
            status = "failed"
        elif reasons:
            status = "pending"
        elif len(row_statuses) == len(expected_cells) and all(
            value == "passed_under_recorded_assumptions" for value in row_statuses
        ):
            status = "conditional_pass"
        else:
            status = "pending"
            reasons.append("not every independently expected scope has accepted passing evidence")
        results.append({"criterion_id": criterion_id, "status": status, "reasons": _unique(reasons)})

    disposition_counts = {status: 0 for status in sorted(AGGREGATE_STATUSES)}
    for row in results:
        disposition_counts[row["status"]] += 1
    no_release_flags = {
        "engineering_mvp_complete": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }
    overlay_source = bindings.get("criteria_source_overlay", {})
    reconciliation_source = bindings.get("method_map_reconciliation", {})
    review_source = bindings.get("method_map_reconciliation_review", {})
    coverage_source = coverage.get("source_criteria")
    return {
        "schema": AGGREGATE_SCHEMA,
        "candidate": expected_candidate,
        "revision_id": expected_revision,
        "source_hashes": {
            binding["path"]: binding["actual_sha256"]
            for binding in bindings.values()
            if binding.get("actual_sha256")
        },
        "source_overlay_validation": {
            "status": "accepted_provenance_only" if source_overlay_valid else "rejected_or_unavailable",
            "accepted": source_overlay_valid,
            "overlay_sha256": overlay_source.get("actual_sha256"),
            "historical_method_map_sha256": coverage_source.get("method_map_sha256")
            if isinstance(coverage_source, dict)
            else None,
            "current_method_map_sha256": bindings.get("method_map", {}).get("actual_sha256"),
            "reconciliation_sha256": reconciliation_source.get("actual_sha256"),
            "coordinator_review_status": (review_source.get("document") or {}).get("status")
            if isinstance(review_source.get("document"), dict)
            else None,
            "scope": "source provenance only; no criterion method or disposition is accepted",
        },
        "expectations_sha256": expectation_sha256,
        "evidence_synthetic_fixture_only": synthetic,
        "status": "criteria_pending" if disposition_counts["pending"] else "criteria_dispositions_complete_pending_engineering_review",
        "criterion_count": len(results),
        "disposition_counts": disposition_counts,
        "criteria": results,
        "engineering_mvp_complete": False,
        "release_flags": no_release_flags,
        "limits": [
            "This is an evidence-shape and coverage aggregator, not a capacity method or engineering acceptance.",
            "A conditional pass is under recorded assumptions and requires independent engineering review.",
            "An independently unresolved scope, missing current demand, missing method, or missing evidence remains pending.",
            "Static scopes may omit a load case only when the independent expectation states and sources that scope.",
        ],
    }


def _validate_record_source_hashes(
    record: dict[str, Any],
    bindings: dict[str, dict[str, Any]],
    source_root: Path,
    required_binding_ids: set[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    hashes = record.get("source_hashes")
    if not isinstance(hashes, dict) or not hashes:
        return ["evidence row has empty source hashes"]
    required_ids = required_binding_ids or {
        "criteria_register",
        "coverage_plan",
        "candidate_authority",
        "full_frame_manifest",
        "criteria_source_overlay",
        "method_map_reconciliation",
        "method_map_reconciliation_review",
    }
    required_paths = {bindings[key]["path"] for key in required_ids if key in bindings}
    if not required_paths.issubset(set(hashes)):
        issues.append("evidence row omits one or more core authority source hashes")
    for rel, expected_hash in hashes.items():
        path = source_root / rel
        if not _nonempty_text(rel) or not _nonempty_text(expected_hash) or not path.is_file():
            issues.append(f"missing or malformed evidence source binding: {rel!r}")
        elif sha256_file(path) != expected_hash:
            issues.append(f"stale evidence source hash: {rel}")
    return issues


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _binding(binding_id: str, path: Path, role: str, root: Path = ROOT) -> dict[str, str]:
    resolved = root / path
    return {
        "binding_id": binding_id,
        "path": _rel_path(path),
        "sha256": sha256_file(resolved),
        "role": role,
    }


def build_current_expectations(root: Path = ROOT) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    """Build a conservative current manifest; unresolved upstream scope stays unresolved."""
    root = Path(root)
    criteria = load_json(root / CRITERIA_PATH)
    criteria["_sha256"] = sha256_file(root / CRITERIA_PATH)
    coverage = load_json(root / COVERAGE_PATH)
    candidate = load_json(root / CANDIDATE_PATH)
    frame_manifest = load_json(root / FRAME_MANIFEST_PATH)
    if frame_manifest.get("geometry_revision_id") != EXPECTED_REVISION:
        raise ValueError("Current frame manifest is not the reviewed geometry revision")
    ids = [criterion_id for criterion_id, _ in _criterion_rows(criteria)]
    source_bindings = [
        _binding("criteria_register", CRITERIA_PATH, "criteria_register", root),
        _binding("coverage_plan", COVERAGE_PATH, "coverage_plan", root),
        _binding("candidate_authority", CANDIDATE_PATH, "candidate_authority", root),
        _binding("method_map", METHOD_MAP_PATH, "method_map", root),
        _binding("source_inventory", SOURCE_INVENTORY_PATH, "source_inventory", root),
        _binding("duty_registry", DUTY_REGISTRY_PATH, "duty_registry", root),
        _binding("full_frame_manifest", FRAME_MANIFEST_PATH, "full_frame_input_manifest", root),
        _binding("load_case_contract", LOAD_CASES_PATH, "load_case_contract", root),
        _binding("attachment_topology", TOPOLOGY_PATH, "attachment_topology", root),
        _binding("criteria_source_overlay", CRITERIA_OVERLAY_PATH, "source_overlay", root),
        _binding("method_map_reconciliation", RECONCILIATION_PATH, "method_map_reconciliation", root),
        _binding("method_map_reconciliation_review", RECONCILIATION_REVIEW_PATH, "source_reconciliation_review", root),
        _binding("method_map_reconciliation_script", RECONCILIATION_SCRIPT_PATH, "source_reconciliation_reproducer", root),
        _binding("method_map_reconciliation_readme", RECONCILIATION_README_PATH, "source_reconciliation_documentation", root),
    ]
    unresolved_reason = (
        "No reviewed WJ-07/WJ-08 independent per-criterion station/interface/case manifest is available. "
        "Open fields: scope_cells; acceptance_contract_source (method ID/version/scope, comparison, limit, unit); "
        "demand_source binding for each dynamic cell; current result evidence. The current full-frame manifest "
        "authenticates identities and applied inputs only; it reports no fresh frame demands, no complete "
        "mechanical contact/attachment model, and no selected structural hardware."
    )
    expectations = {
        "schema": EXPECTATIONS_SCHEMA,
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "purpose": "Independent expected-scope contract for exact47 aggregation; current applicability coverage is intentionally unresolved.",
        "source_bindings": source_bindings,
        "criteria": [
            {
                "criterion_id": criterion_id,
                "applicability": "unresolved",
                "reason": unresolved_reason,
                "scope_cells": [],
            }
            for criterion_id in ids
        ],
        "scope_policy": {
            "expected_coverage_must_be_authored_independently_of_producer_evidence": True,
            "producer_coverage_is_never_a_source_of_expected_scope": True,
            "producer_acceptance_terms_are_never_authoritative": True,
            "producer_demand_source_is_never_authoritative": True,
            "static_case_omission_requires_explicit_source_bound_scope_reason": True,
            "current_expected_scope_complete": False,
            "current_demands_available": frame_manifest.get("readiness", {}).get("current_full_frame_demands_available") is True,
            "replacement_duties_may_not_be_dropped_by_not_applicable_dispositions": True,
            "open_fields": [
                "scope_cells",
                "acceptance_contract_source",
                "demand_source_binding_for_dynamic_scope",
                "fresh_per_scope_result_evidence",
            ],
        },
    }
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "producer": None,
        "synthetic_fixture": False,
        "records": [],
    }
    return criteria, coverage, candidate, frame_manifest, expectations, evidence


def bootstrap_current(output_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    """Write a read-only-current-inventory attempt containing 47 pending rows."""
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to replace nonempty artifact directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    criteria, coverage, candidate, frame_manifest, expectations, evidence = build_current_expectations(root)
    (output_dir / "expected-coverage.json").write_text(json.dumps(expectations, indent=2) + "\n", encoding="utf-8")
    (output_dir / "empty-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    expected_hash = sha256_file(output_dir / "expected-coverage.json")
    result = aggregate_documents(
        criteria,
        coverage,
        candidate,
        frame_manifest,
        expectations,
        evidence,
        source_root=root,
        expectation_sha256=expected_hash,
    )
    (output_dir / "current-aggregate.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-current", action="store_true", help="write the fail-closed current 47-row pending inventory")
    parser.add_argument("--output-dir", type=Path, help="attempt directory for --bootstrap-current")
    parser.add_argument("--criteria", type=Path, default=ROOT / CRITERIA_PATH)
    parser.add_argument("--coverage", type=Path, default=ROOT / COVERAGE_PATH)
    parser.add_argument("--candidate", type=Path, default=ROOT / CANDIDATE_PATH)
    parser.add_argument("--frame-manifest", type=Path, default=ROOT / FRAME_MANIFEST_PATH)
    parser.add_argument("--expectations", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.bootstrap_current:
        if not args.output_dir:
            parser.error("--bootstrap-current requires --output-dir")
        result = bootstrap_current(args.output_dir)
        print(json.dumps({"status": result["status"], "disposition_counts": result["disposition_counts"]}, indent=2))
        return 0
    if not all((args.expectations, args.evidence, args.output)):
        parser.error("normal aggregation requires --expectations, --evidence, and --output")
    criteria = load_json(args.criteria)
    criteria["_sha256"] = sha256_file(args.criteria)
    coverage = load_json(args.coverage)
    candidate = load_json(args.candidate)
    frame_manifest = load_json(args.frame_manifest)
    expectations = load_json(args.expectations)
    evidence = load_json(args.evidence)
    result = aggregate_documents(
        criteria,
        coverage,
        candidate,
        frame_manifest,
        expectations,
        evidence,
        source_root=ROOT,
        expectation_sha256=sha256_file(args.expectations),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "disposition_counts": result["disposition_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
