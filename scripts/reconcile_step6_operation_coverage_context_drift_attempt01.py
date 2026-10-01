"""Replay the frozen Step 6 register and isolate current plan-context drift."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "step6-operation-coverage-attempt01-current-plan-drift-audit-2026-09-28/"
    / "reconciliation.json"
)
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/"
PREDECESSOR_PRODUCER = BASE + "produce.py"
PREDECESSOR_README = BASE + "README.md"
PREDECESSOR_JSON = BASE + "operation-coverage.json"
CURRENT_PLAN = "docs/wood-joints-mvp/next-mvp-plan.md"
EXPECTED_SOURCE_SHA256 = {
    PREDECESSOR_PRODUCER: "cd084af5b407582a0779db67570ee92c4dc12e4b2ccbcc48e042228ee92145ac",
    PREDECESSOR_README: "d11c14291554ad3870755e6fc3d2b7fbc320432eaf421f03331b52fc3e4455cd",
    PREDECESSOR_JSON: "1722ff0f0a438934df15e6285947bdbf3b34f8d99a1e94e30403d756ab33d7ae",
    CURRENT_PLAN: "7163d64645955e577b9fd8315f207b2a8511ef5773ec669145a65ad0d6f3e4ac",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(raw)


def verify_source_pins() -> dict[str, dict[str, Any]]:
    pins = {}
    for relative, expected in EXPECTED_SOURCE_SHA256.items():
        raw = (ROOT / relative).read_bytes()
        actual = sha256(raw)
        if actual != expected:
            raise ValueError(
                f"Pinned source drift: {relative}: expected {expected}, got {actual}"
            )
        pins[relative] = {"sha256": actual, "size_bytes": len(raw)}
    return pins


def import_predecessor():
    path = ROOT / PREDECESSOR_PRODUCER
    spec = importlib.util.spec_from_file_location("step6_operation_coverage_attempt01", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pinned predecessor producer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_diff_paths(left: Any, right: Any, path: str = "") -> list[str]:
    if type(left) is not type(right):
        return [path or "/"]
    if isinstance(left, dict):
        changes = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}/{key}"
            if key not in left or key not in right:
                changes.append(child)
            else:
                changes.extend(json_diff_paths(left[key], right[key], child))
        return changes
    if isinstance(left, list):
        if len(left) != len(right):
            return [path or "/"]
        changes = []
        for index, (old, new) in enumerate(zip(left, right, strict=True)):
            changes.extend(json_diff_paths(old, new, f"{path}/{index}"))
        return changes
    return [] if left == right else [path or "/"]


def readme_diff_lines(old: bytes, new: bytes) -> list[dict[str, Any]]:
    changes = []
    for index, pair in enumerate(
        zip_longest(old.decode("utf-8").splitlines(), new.decode("utf-8").splitlines()),
        start=1,
    ):
        old_line, new_line = pair
        if old_line != new_line:
            changes.append({"line": index, "frozen": old_line, "replayed": new_line})
    return changes


def build() -> dict[str, Any]:
    source_pins = verify_source_pins()
    frozen = json.loads((ROOT / PREDECESSOR_JSON).read_text(encoding="utf-8"))
    frozen_readme = (ROOT / PREDECESSOR_README).read_bytes()
    producer = import_predecessor()
    replayed = producer.build_artifact()
    replayed_json = producer.json_bytes(replayed)
    replayed_json_sha256 = sha256(replayed_json)
    replayed_readme = producer.make_readme(replayed, replayed_json_sha256).encode()

    changes = json_diff_paths(frozen, replayed)
    readme_changes = readme_diff_lines(frozen_readme, replayed_readme)
    plan_rows = {
        row["path"]: row
        for row in frozen["source_bindings"]
        if row["path"] == CURRENT_PLAN
    }
    current_plan_rows = {
        row["path"]: row
        for row in replayed["source_bindings"]
        if row["path"] == CURRENT_PLAN
    }
    if set(plan_rows) != {CURRENT_PLAN} or set(current_plan_rows) != {CURRENT_PLAN}:
        raise ValueError("The predecessor register must bind the current plan exactly once")
    if changes != [f"/source_bindings/{next(i for i, row in enumerate(frozen['source_bindings']) if row['path'] == CURRENT_PLAN)}/sha256"]:
        raise ValueError(f"Unexpected predecessor JSON drift: {changes}")
    if len(readme_changes) != 1 or not str(readme_changes[0]["frozen"]).startswith(
        "Machine JSON SHA-256:"
    ):
        raise ValueError(f"Unexpected predecessor README drift: {readme_changes}")
    if frozen["counts"] != replayed["counts"]:
        raise ValueError("Operation coverage counts changed during replay")
    for key in (
        "axis_records",
        "candidate_block_coverage",
        "service_records",
        "operation_order_context",
        "ordinary_local_n_disposition",
        "release_flags",
    ):
        if frozen[key] != replayed[key]:
            raise ValueError(f"Operation evidence changed during replay: {key}")

    record: dict[str, Any] = {
        "schema": "step6_operation_coverage_context_drift_reconciliation/v1",
        "attempt_id": "step6-operation-coverage-attempt01-current-plan-drift-audit-2026-09-28",
        "status": "replay_matches_except_for_current_plan_context_pin",
        "source_pins": source_pins,
        "predecessor": {
            "operation_record_sha256": source_pins[PREDECESSOR_JSON]["sha256"],
            "frozen_readme_sha256": source_pins[PREDECESSOR_README]["sha256"],
            "producer_path": PREDECESSOR_PRODUCER,
            "plan_context_path": CURRENT_PLAN,
            "frozen_plan_context_sha256": plan_rows[CURRENT_PLAN]["sha256"],
            "current_plan_context_sha256": current_plan_rows[CURRENT_PLAN]["sha256"],
        },
        "replay": {
            "json_sha256": replayed_json_sha256,
            "readme_sha256": sha256(replayed_readme),
            "json_diff_paths": changes,
            "readme_diff_lines": readme_changes,
            "current_source_bindings": replayed["source_bindings"],
            "operation_counts_unchanged": frozen["counts"],
            "axis_records_unchanged": True,
            "candidate_block_coverage_unchanged": True,
            "service_records_unchanged": True,
            "operation_order_context_unchanged": True,
            "ordinary_local_n_disposition_unchanged": True,
            "release_flags_unchanged": True,
        },
        "interpretation": [
            "Attempt01 remains an immutable historical packet; its own current-input verifier still fails because the plan file changed.",
            "A full replay changes only the plan digest in source_bindings and the derived machine-JSON digest in the README.",
            "All 575 operation/service rows and their 92/12/66 axis counts reproduce byte-for-byte as structured data.",
            "This is provenance reconciliation only. It establishes no selected tool, physical operation, tolerance, capacity, installation, candidate acceptance, or release.",
        ],
        "criterion_effect": {
            "fit_and_transport_criteria_closed": False,
            "engineering_mvp_complete": False,
            "release": False,
        },
    }
    record["record_sha256"] = canonical_sha256(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.write:
        if OUT.exists():
            raise SystemExit(f"Refusing to overwrite existing reconciliation: {OUT}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        if not OUT.exists():
            raise SystemExit(f"Reconciliation is missing: {OUT}")
        actual = json.loads(OUT.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("Reconciliation is stale or differs from pinned inputs")
    print(
        f"{'WROTE' if args.write else 'PASS'} {OUT.relative_to(ROOT)} "
        f"json_diffs={len(expected['replay']['json_diff_paths'])} "
        f"operation_rows={expected['replay']['operation_counts_unchanged']['operation_records']}"
    )


if __name__ == "__main__":
    main()
