#!/usr/bin/env python3
"""Reconcile the frozen criteria coverage pin with the current method map."""

from __future__ import annotations

import difflib
import hashlib
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[5]
OUT = pathlib.Path(__file__).resolve().parent
OLD_COMMIT = "55ede246246842285d97946bde84f35f2362923b"
CURRENT_COMMIT = "c7c91fd02dc0daec9619b2fa933c4f6daf2d9041"
METHOD_MAP = "docs/wood-joints-mvp/criteria-method-map.md"
COVERAGE = "docs/wood-joints-mvp/current-criteria-coverage.json"
CRITERIA = "docs/wood-joints-mvp/criteria.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def changed_row_id(line: str) -> str:
    cells = line.split("|")
    if len(cells) < 3:
        return ""
    return cells[1].strip().strip("`")


old_bytes = git_blob(OLD_COMMIT, METHOD_MAP)
current_bytes = (ROOT / METHOD_MAP).read_bytes()
head_bytes = git_blob(CURRENT_COMMIT, METHOD_MAP)
coverage_bytes = (ROOT / COVERAGE).read_bytes()
coverage = json.loads(coverage_bytes)
criteria = json.loads((ROOT / CRITERIA).read_bytes())
old_lines = old_bytes.decode("utf-8").splitlines()
current_lines = current_bytes.decode("utf-8").splitlines()
diff = list(difflib.unified_diff(old_lines, current_lines, lineterm=""))
removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]
added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
removed_ids = [changed_row_id(line) for line in removed]
added_ids = [changed_row_id(line) for line in added]
coverage_ids = [row["criterion_id"] for row in coverage["criteria"]]
legacy_ids = [row["legacy_id"] for row in criteria["legacy_criteria"]]
additional_ids = [row["id"] for row in criteria["additional_candidate_obligations"]]
expected_coverage_map_hash = coverage["source_criteria"]["method_map_sha256"]
observed_map_hash = digest(current_bytes)

checks = {
    "current_checkout_is_named_revision": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip() == CURRENT_COMMIT,
    "tracked_method_map_unchanged_in_worktree": subprocess.check_output(
        ["git", "status", "--short", "--", METHOD_MAP], cwd=ROOT, text=True
    ).strip() == "",
    "coverage_file_unchanged_in_worktree": subprocess.check_output(
        ["git", "status", "--short", "--", COVERAGE], cwd=ROOT, text=True
    ).strip() == "",
    "coverage_still_pins_historical_method_map": expected_coverage_map_hash == digest(old_bytes),
    "only_steel_direct_row_changed": removed_ids == ["steel_direct"] and added_ids == ["steel_direct"],
    "frozen_47_criterion_ids_match_source_criteria": len(coverage_ids) == 47 and coverage_ids == legacy_ids + additional_ids,
    "current_method_map_is_exact_checked_out_blob": digest(head_bytes) == observed_map_hash,
}
if not all(checks.values()):
    raise SystemExit(f"RECONCILIATION CHECK FAILED: {checks}")

record = {
    "schema": "wood_joint_criteria_method_map_reconciliation/v1",
    "purpose": "Explain the frozen coverage pin mismatch without mutating either authority input.",
    "repository_head": CURRENT_COMMIT,
    "source_files": {
        METHOD_MAP: {
            "historical_pinned_commit": OLD_COMMIT,
            "historical_pinned_sha256": digest(old_bytes),
            "current_checked_out_sha256": observed_map_hash,
            "current_checked_out_commit_sha256": digest(head_bytes),
            "changed_row_ids": ["steel_direct"],
            "diff_removed_lines": removed,
            "diff_added_lines": added,
        },
        COVERAGE: {
            "sha256": digest(coverage_bytes),
            "embedded_method_map_sha256": expected_coverage_map_hash,
            "criteria_count": len(coverage_ids),
            "criterion_ids_sha256": digest("\n".join(coverage_ids).encode()),
        },
        CRITERIA: {
            "sha256": digest((ROOT / CRITERIA).read_bytes()),
            "source_row_count": len(legacy_ids) + len(additional_ids),
        },
    },
    "checks": checks,
    "disposition": "pin mismatch is a one-row tracked-source change; no frozen coverage input is rewritten and no criterion is resolved",
    "scope_limits": [
        "This reconciles provenance only; it does not adjudicate the steel_direct method or establish resistance.",
        "All 47 current coverage rows remain pending until accepted methods and fresh per-scope evidence exist.",
        "A future aggregator must consume a versioned current-source overlay while preserving the frozen source digest and provenance.",
    ],
}
(OUT / "source-reconciliation.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"status": "PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY", "checks": checks}, indent=2))
