"""Review the supplied writer tests only; no additional mutation experiments."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
SUMMARY = OWN.parents[2]
TARGET = SUMMARY / "review-fix-v3"
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "summarize.py": "787626079340ea3999f940cd7e057dd5c095720d42a54e44e30711ebc8f1a36e",
    "test_summarize.py": "e42c9dfbace8f59911cc76d54cea99409bd37adab12df2756f1e7f0ed7017dea",
    "verification.json": "dce19350e322c6c02b1a0a58e5a464b3f647c827514f2460ee837e5216ae0c06",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    verification = json.loads((TARGET / "verification.json").read_bytes())
    pins = dict(verification["preserved_sources_after"])
    assert pins == verification["preserved_sources_before"] and len(pins) == 20
    pins.update({str((TARGET / name).relative_to(ROOT)): expected for name, expected in EXPECTED.items()})

    def unchanged():
        assert all(sha(ROOT / path) == expected for path, expected in pins.items())

    unchanged()
    tree = ast.parse((TARGET / "test_summarize.py").read_bytes())
    tests = {node.name: node.lineno for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    assert len(tests) == 13
    coverage = {
        "test_positive_reserved_before_loading_and_unchanged_delegation": [1, "STARTED exists before loader; result identity/JSON and load/build order"],
        "test_missing_parents_created_only_through_held_directory_fds": [1, "every mkdir receives a held dir_fd; expected three-parent census"],
        "test_source_owned_root_replaced_before_call_rejects_import_identity": [2, "symlink/directory root replacement; no callbacks or leaf in foreign/parked subtree"],
        "test_each_directory_replaced_immediately_before_open": [8, "four levels and two replacements; no callback/output and exactly one insertion"],
        "test_runs_ancestor_retarget_after_mkdir_cannot_redirect_following_stat": [1, "post-mkdir symlink rejected before callbacks; no foreign or parked output"],
        "test_all_held_ancestors_replaced_keep_failed_in_original_subtree": [16, "two phases/four levels/two replacements; FAILED under original held subtree, exact source pin, no foreign output"],
        "test_original_parent_alias_retarget_stays_bound": [1, "accepted parent alias retarget cannot redirect leaf; successful unchanged result"],
        "test_exclusive_or_foreign_output_rejected_before_callbacks": [6, "occupied/dangling/late occupied/traversal/foreign/dangling-parent guards; ordinary occupied bytes preserved"],
        "test_failed_callback_retained_and_retry_rejected": [1, "callback failure produces FAILED; repeat rejects and exact failure bytes remain"],
        "test_reserved_leaf_replaced_after_started_never_writes_replacement": [2, "symlink/regular replacement untouched; parked inode retains STARTED"],
        "test_both_corrected_method_pins_required_before_unchanged_build": [2, "missing v3/v2-loader pin blocks build and retains FAILED"],
        "test_same_output_two_callers_only_one_delegates": [1, "one success/one occupied; loader/build invoked once"],
        "test_real_v2_loader_supplies_only_unchanged_original_build_and_selectors": [1, "real loader definitions retain original99 build filename/hash and0547 selector pin"],
    }
    assert set(coverage) == set(tests) and sum(row[0] for row in coverage.values()) == 43
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TARGET / "test_summarize.py")]
    run = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert run.returncode == 0 and "43 passed" in run.stdout, run.stderr + run.stdout
    unchanged()
    assert verification["complete_joint_resistance"] is None
    assert all(value is False for value in verification["release"].values())
    report = {
        "schema": "eoere_z180_summary_writer_independent_testing_review/v3",
        "status": "PASS_PROVIDED_INERT_WRITER_TEST_SCOPE", "confirmed_substantial_findings": [],
        "source_sha256": pins, "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "frozen_sources_unchanged_before_after": len(pins),
        "provided_inert_suite": {"passed": 43, "command": command, "stdout": run.stdout},
        "inspected_assertion_coverage": {name: {"line": tests[name], "cases": row[0], "assertions": row[1]}
                                        for name, row in coverage.items()},
        "source_review": {
            "root_identity_captured_before_callbacks_and_checked_before_walk": True,
            "every_parent_created_opened_and_checked_relative_to_held_directories": True,
            "exclusive_leaf_and_payload_writes_check_the_retained_inode": True,
            "FAILED_namespace_bypass_keeps_held_directory_and_leaf_identity_checks": True,
            "v3_calls_v2_original_loader_and_never_v2_writer": True,
            "original99_build_and0547_selectors_remain_frozen": True,
        },
        "reused_reviews": {
            "original_math_join_review_sha256": pins[str((SUMMARY / "independent-review-v1/correctness/receipt.json").relative_to(ROOT))],
            "v2_loader_join_review_sha256": pins[str((SUMMARY / "independent-review-v2/correctness/receipt.json").relative_to(ROOT))],
        },
        "limits": [
            "Assessment uses source inspection and the provided43 inert tests only; no additional filesystem mutation experiment was added.",
            "Writer integration uses temporary directories and callback stubs. Real loader definitions are checked; original build is not invoked on genuine data.",
            "This does not validate genuine candidate JSON, summary production/publication or operating-system/storage failures outside the supplied controls.",
            "Original source joins, selectors and numerical meanings reuse frozen reviews; no numerical calculation or structural acceptance is implied.",
        ],
        "release": verification["release"], "complete_joint_resistance": None, "unadopted_proposal": True,
        "execution": {"provided_inert_tests_and_source_inspection_only": True,
                      "genuine_data_model_summary_gate_reducer_native_CAD_or_network_work": False,
                      "shared_documents_inputs_staging_or_commit_changes": False},
        "retention": "Keep compact helper/receipt with frozen writer evidence. The supplied tests own temporary output controls; no genuine summary was created.",
    }
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
