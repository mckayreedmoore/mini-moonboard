"""Review frozen v4 data contracts using source and supplied inert tests only."""

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
SUMMARY = OWN.parents[2]
TARGET = SUMMARY / "review-fix-v4"
PREVIOUS = SUMMARY / "independent-review-v3/correctness"
TARGET_SHA256 = {
    "summarize.py": "e4ba76473e84aa7afdae3599a2c196b894a7d0311a407de9bb0daece647196d9",
    "test_summarize.py": "66eb2383a37b0f91abf7b8191cb78189ff0504ac6801b26fc352ffa168c31fe2",
    "verification.json": "69b6cb1d4f3776b2bb4830b6be69539843e913fc703f7812a2d45a3060f5b654",
}
PREVIOUS_SHA256 = {
    "review.py": "2d0fd1b4a2ffb3881a66c31c2adf64473218462b35ef04088189fe82a154fa62",
    "receipt.json": "7fccc7531c57add384c3a7523bc068ae507e75f7e288a825be06dbedb46f321e",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    for name, digest in PREVIOUS_SHA256.items():
        assert sha256(PREVIOUS / name) == digest
    previous = json.loads((PREVIOUS / "receipt.json").read_bytes())
    expected = dict(previous["reviewed_sha256"])
    expected.update({str((PREVIOUS / name).relative_to(ROOT)): value for name, value in PREVIOUS_SHA256.items()})
    expected.update({str((TARGET / name).relative_to(ROOT)): value for name, value in TARGET_SHA256.items()})
    before = {name: sha256(ROOT / name) for name in expected}
    assert before == expected

    tree = ast.parse((SUMMARY / "summarize.py").read_bytes())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ("case_records", "build")]
    assert [node.name for node in selected] == ["case_records", "build"]
    schema_seams = [node.value for function in selected for node in ast.walk(function)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and node.value.startswith("eoere_z180_component_source_snapshot_")]
    assert schema_seams == ["eoere_z180_component_source_snapshot_before/v1", "eoere_z180_component_source_snapshot_after/v1"]
    history = ast.dump(ast.parse('snapshots["source_pins_before"]["inventory_only_historical_receipts"]', mode="eval").body)
    assert sum(ast.dump(node) == history for function in selected for node in ast.walk(function)) == 1

    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    environment.pop("PYTEST_ADDOPTS", None)
    with tempfile.TemporaryDirectory(prefix="z180-summary-v4-correctness-") as temporary:
        command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "--basetemp", str(Path(temporary) / "pytest"), str(TARGET / "test_summarize.py")]
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "13 passed" in completed.stdout, completed.stdout
    assert {name: sha256(ROOT / name) for name in expected} == before
    recorded = json.loads((TARGET / "verification.json").read_bytes())["actual_saved_shape_replay"]
    return {
        "schema": "independent_z180_summary_saved_contract_correctness_review/v4",
        "reviewer_source_sha256": sha256(OWN), "reviewed_sha256": before,
        "reused_writer_review_receipt_sha256": PREVIOUS_SHA256["receipt.json"],
        "reused_original_review_receipt_sha256": previous["reused_original_review_receipt_sha256"],
        "checks": {
            "target_and_reused_source_pins_unchanged_before_after": len(before),
            "original_AST_exact_schema_and_optional_history_seams": 3,
            "provided_inert_data_contract_tests_passed": 13,
            "provided_test_result": completed.stdout.strip(),
            "source_inspected_three_guarded_AST_substitutions_only": True,
            "source_inspected_own_adapter_before_after_union_and_output_manifest_pin": True,
            "original_identity_hash_census_coverage_equation_selector_checks_retained": True,
            "exact_v3_output_writer_reused": True,
        },
        "parent_recorded_actual_replay_not_rerun": {
            "case_count": len(recorded["cases"]),
            "verified_source_union": recorded["verified_source_union"],
            "final_summary_output_produced": recorded["final_summary_output_produced"],
        },
        "findings": [],
        "limits": [
            "Executed only the provided 13 inert data-contract tests plus source/AST inspection; no added experiments or genuine candidate-data evaluation.",
            "The bound verification records the parent's six-case in-memory actual replay; its 1306-pin closure was not independently consumed or rerun here.",
            "Reused frozen original numerical/source-join/selector reviews and v3 output-writer proof; no repeated model or engineering audit.",
            "No actual summary output, producer, gate, reducer, CAD/BREP/native, operator or solve work; null complete resistance, exceeded references, unadopted status and false releases retain their original meanings.",
        ],
    }


if __name__ == "__main__":
    receipt = evaluate()
    destination = OWN.with_name("receipt.json")
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "receipt_sha256": sha256(destination),
                      "reviewer_sha256": sha256(OWN), "pins": len(receipt["reviewed_sha256"]),
                      "tests": 13, "findings": 0}))
