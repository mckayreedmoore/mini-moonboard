#!/usr/bin/env python3
"""Reconcile the frozen exact47 coverage pin to reviewed working-tree bytes."""

from __future__ import annotations

import difflib
import hashlib
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[5]
OUT = pathlib.Path(__file__).resolve().parent
OLD_COMMIT = "55ede246246842285d97946bde84f35f2362923b"
METHOD_MAP = "docs/wood-joints-mvp/criteria-method-map.md"
COVERAGE = "docs/wood-joints-mvp/current-criteria-coverage.json"
CRITERIA = "docs/wood-joints-mvp/criteria.json"
EXPECTED_HISTORICAL_MAP_SHA256 = "1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80"
EXPECTED_CURRENT_MAP_SHA256 = "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7"
EXPECTED_COVERAGE_SHA256 = "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c"
EXPECTED_CRITERIA_SHA256 = "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784"
EXPECTED_CHANGED_ROWS = ["additional_group_reduction_sensitivity", "steel_direct"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def row_id(line: str) -> str:
    cells = line.split("|")
    if len(cells) < 3:
        return ""
    return cells[1].strip().strip("`")


old_bytes = git_blob(OLD_COMMIT, METHOD_MAP)
current_bytes = (ROOT / METHOD_MAP).read_bytes()
coverage_bytes = (ROOT / COVERAGE).read_bytes()
criteria_bytes = (ROOT / CRITERIA).read_bytes()
coverage = json.loads(coverage_bytes)
criteria = json.loads(criteria_bytes)
old_lines = old_bytes.decode("utf-8").splitlines()
current_lines = current_bytes.decode("utf-8").splitlines()
diff = list(difflib.unified_diff(old_lines, current_lines, lineterm=""))
removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]
added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
removed_ids = [row_id(line) for line in removed]
added_ids = [row_id(line) for line in added]
changed_ids = sorted(set(removed_ids) | set(added_ids))
coverage_ids = [row["criterion_id"] for row in coverage["criteria"]]
criteria_ids = [row["legacy_id"] for row in criteria["legacy_criteria"]] + [
    row["id"] for row in criteria["additional_candidate_obligations"]
]
embedded_map_hash = coverage["source_criteria"]["method_map_sha256"]

checks = {
    "historical_map_matches_frozen_coverage_pin": (
        digest(old_bytes) == EXPECTED_HISTORICAL_MAP_SHA256 == embedded_map_hash
    ),
    "current_working_tree_map_matches_exact_reviewed_sha256": (
        digest(current_bytes) == EXPECTED_CURRENT_MAP_SHA256
    ),
    "frozen_coverage_matches_exact_reviewed_sha256": (
        digest(coverage_bytes) == EXPECTED_COVERAGE_SHA256
    ),
    "source_criteria_matches_exact_reviewed_sha256": (
        digest(criteria_bytes) == EXPECTED_CRITERIA_SHA256
    ),
    "changed_method_map_rows_match_reviewed_scope": (
        removed_ids == EXPECTED_CHANGED_ROWS and added_ids == EXPECTED_CHANGED_ROWS
    ),
    "frozen_47_criterion_ids_match_source_criteria": (
        len(coverage_ids) == 47 and coverage_ids == criteria_ids
    ),
    "no_frozen_coverage_or_candidate_dispositions_changed": (
        digest(coverage_bytes) == EXPECTED_COVERAGE_SHA256
        and digest(criteria_bytes) == EXPECTED_CRITERIA_SHA256
    ),
}
if not all(checks.values()):
    raise SystemExit(f"RECONCILIATION CHECK FAILED: {checks}")

record = {
    "schema": "wood_joint_criteria_method_map_reconciliation/v2",
    "artifact": "current-criteria-method-map-reconciliation-attempt02",
    "purpose": "Bind the frozen coverage pin to exact reviewed working-tree method-map bytes without requiring a commit or clean worktree.",
    "historical_method_map_commit": OLD_COMMIT,
    "source_files": {
        METHOD_MAP: {
            "historical_pinned_sha256": digest(old_bytes),
            "current_working_tree_sha256": digest(current_bytes),
            "source_kind": "exact_reviewed_working_tree_bytes",
            "changed_row_ids": changed_ids,
            "removed_rows": removed,
            "added_rows": added,
        },
        COVERAGE: {
            "sha256": digest(coverage_bytes),
            "embedded_method_map_sha256": embedded_map_hash,
            "criteria_count": len(coverage_ids),
            "criterion_ids_sha256": digest("\n".join(coverage_ids).encode()),
        },
        CRITERIA: {
            "sha256": digest(criteria_bytes),
            "source_row_count": len(criteria_ids),
        },
    },
    "checks": checks,
    "disposition": "The exact current map bytes are source-reconciled to the historical frozen pin; this is provenance only and resolves no criterion.",
    "scope_limits": [
        "No repository HEAD or clean-worktree condition is used; the exact current method-map bytes are pinned by SHA-256 instead.",
        "Any method-map byte change invalidates this attempt until a new source reconciliation and review bind the replacement bytes.",
        "The frozen coverage and criteria source digests remain byte-identical to their reviewed pins.",
        "No method, resistance, criterion disposition, candidate selection, solver readiness, or release state is established.",
    ],
}
(OUT / "source-reconciliation.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"status": "PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY", "checks": checks}, indent=2))
