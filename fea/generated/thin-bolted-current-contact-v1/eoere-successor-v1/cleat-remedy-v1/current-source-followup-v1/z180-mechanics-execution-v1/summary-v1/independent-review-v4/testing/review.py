"""Saved-data seam test assessment; supplied inert suite and source records only."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
SUMMARY = OWN.parents[2]
TARGET = SUMMARY / "review-fix-v4"
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "summarize.py": "e4ba76473e84aa7afdae3599a2c196b894a7d0311a407de9bb0daece647196d9",
    "test_summarize.py": "66eb2383a37b0f91abf7b8191cb78189ff0504ac6801b26fc352ffa168c31fe2",
    "verification.json": "69b6cb1d4f3776b2bb4830b6be69539843e913fc703f7812a2d45a3060f5b654",
}
PRIOR = {
    "receipt.json": "3487e4099e427237de9357d08b0a243b7d4d381f275b3b6b982cd945e65fc832",
    "review.py": "713b4b50f2a76640cdbf9f46a9c5df50bb85142a47cf6abc43be28f36367f5f6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior_dir = SUMMARY / "independent-review-v3/testing"
    prior = json.loads((prior_dir / "receipt.json").read_bytes())
    pins = dict(prior["source_sha256"])
    pins.update({str((prior_dir / name).relative_to(ROOT)): digest for name, digest in PRIOR.items()})
    pins.update({str((TARGET / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()})

    def unchanged():
        assert all(sha(ROOT / path) == digest for path, digest in pins.items())

    unchanged()
    verification = json.loads((TARGET / "verification.json").read_bytes())
    tree = ast.parse((TARGET / "test_summarize.py").read_bytes())
    tests = {node.name: node.lineno for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    coverage = {
        "test_actual_schema_and_optional_history_preserve_selectors_and_caveat": [1, "six ordered cases, present history retained, later absent history empty, adapter pin, original selectors equal, exact union, false releases/null joint resistance"],
        "test_old_invented_or_foreign_schema_rejected_without_relabel": [6, "both before/after roles reject both old invented schemas and foreign schema"],
        "test_missing_history_observation_is_empty_without_erasing_coverage": [1, "absent history defaults empty while missing-before count and incomplete coverage stay intact"],
        "test_unchanged_coverage_mismatch_guard_rejects": [1, "inconsistent missing-before caveat still rejects"],
        "test_exact_raw_snapshot_hash_still_required": [1, "same-size raw snapshot change rejects on SHA rather than size"],
        "test_production_build_requires_own_adapter_manifest_pin": [1, "missing adapter manifest pin rejects; adding exact pin permits six inert cases"],
        "test_adapter_source_drift_rejected_before_ast": [1, "adapter drift rejects before AST parser callback"],
        "test_exact_v3_output_guard_reused_without_copy": [1, "v3 writer filename/hash unchanged; selector pin retained and adapted build filename identifies v4"],
    }
    assert set(tests) == set(coverage) and sum(row[0] for row in coverage.values()) == 13
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TARGET / "test_summarize.py")]
    run = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert run.returncode == 0 and "13 passed" in run.stdout, run.stderr + run.stdout
    unchanged()
    replay = verification["actual_saved_shape_replay"]
    assert len(replay["cases"]) == 6 and replay["verified_source_union"]["count"] == 1306
    assert replay["verified_source_union"]["before_after_exact"] is True
    assert replay["final_summary_output_produced"] is False
    assert replay["first_42_caveat_unchanged"] is True and replay["first_two_historical_inventory_observations_preserved"] is True
    assert replay["later_five_absences_reported_as_empty_observation_lists"] is True
    assert verification["complete_joint_resistance"] is None and not any(verification["release"].values())
    report = {
        "schema": "eoere_z180_summary_saved_data_adapter_independent_testing_review/v4",
        "status": "PASS_NARROW_PROVIDED_INERT_AND_RECORDED_REPLAY_SCOPE", "confirmed_substantial_findings": [],
        "source_sha256": pins, "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "frozen_source_pin_count_unchanged_before_after": len(pins),
        "provided_inert_suite": {"passed": 13, "command": command, "stdout": run.stdout},
        "inspected_assertion_coverage": {name: {"line": tests[name], "cases": row[0], "assertions": row[1]}
                                        for name, row in coverage.items()},
        "source_inspection": {
            "exact99_source_checked_before_selecting_only_case_records_and_build": True,
            "guarded_two_schema_literals_and_one_optional_history_access": True,
            "source_hash_state_census_coverage_and_selector_checks_untouched": True,
            "adapter_pin_joins_both_existing_source_union_verifications": True,
            "production_build_additionally_requires_adapter_manifest_pin": True,
            "private_exact_v3_writer_reused_with_only_original_loader_rebound": True,
        },
        "recorded_actual_replay": {
            "independently_rerun": False, "evidence": str((TARGET / "verification.json").relative_to(ROOT)),
            "cases": 6, "reported_source_pin_count": 1306,
            "reported_result_canonical_sha256": replay["result_canonical_sha256"],
            "first_case_missing_before": 42, "first_case_inventory_observations": 2,
            "later_five_absent_history_observations_default_empty": True, "reported_output_produced": False,
        },
        "reuse": {"clean_v3_writer_testing_receipt_sha256": PRIOR["receipt.json"],
                  "writer_controls_rerun": False, "original99_math_and_join_reviews_reused": True},
        "limits": [
            "Only source inspection, the provided13 inert tests and the frozen recorded replay were assessed.",
            "No additional filesystem mutation experiment, genuine saved-data read/replay or output production was performed by this review.",
            "The recorded1306-pin six-case replay is author evidence, not independently reproduced here; adapter tests use frozen synthetic fixtures.",
            "Unchanged writer and numerical selector proofs are reused. Reference exceedances and unknown resistance remain retained without physical release.",
        ],
        "release": verification["release"], "complete_joint_resistance": None, "unadopted_proposal": True,
        "execution": {"provided_inert_tests_source_and_recorded_evidence_only": True,
                      "additional_filesystem_experiments_genuine_candidate_output_gate_reducer_native_CAD_or_network": False,
                      "shared_docs_staging_or_commit_changes": False},
        "retention": "Keep compact helper/receipt alongside frozen old proofs. Supplied synthetic tests own their temporary fixtures; no candidate run or summary publication was performed.",
    }
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
