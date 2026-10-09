"""Bounded v3 output review: fixed source pins and supplied inert tests only."""

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
TARGET = SUMMARY / "review-fix-v3"
PREVIOUS = SUMMARY / "independent-review-v2/correctness"
TARGET_SHA256 = {
    "summarize.py": "787626079340ea3999f940cd7e057dd5c095720d42a54e44e30711ebc8f1a36e",
    "test_summarize.py": "e42c9dfbace8f59911cc76d54cea99409bd37adab12df2756f1e7f0ed7017dea",
    "verification.json": "dce19350e322c6c02b1a0a58e5a464b3f647c827514f2460ee837e5216ae0c06",
}
PREVIOUS_SHA256 = {
    "review.py": "8472daa7975b70e112e69d86ed013e8895802003e68232857da58feeb9a94838",
    "receipt.json": "04fb39f4f3f6f079cab563bde72194801e25978b84305291fa0c6c7e0acc4ab3",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    """Read source evidence and run only the packet's provided inert fixtures."""
    for name, expected in PREVIOUS_SHA256.items():
        assert sha256(PREVIOUS / name) == expected, name
    previous = json.loads((PREVIOUS / "receipt.json").read_bytes())
    expected = dict(previous["reviewed_sha256"])
    expected.update({str((PREVIOUS / name).relative_to(ROOT)): value
                     for name, value in PREVIOUS_SHA256.items()})
    expected.update({str((TARGET / name).relative_to(ROOT)): value
                     for name, value in TARGET_SHA256.items()})
    before = {name: sha256(ROOT / name) for name in expected}
    assert before == expected

    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    environment.pop("PYTEST_ADDOPTS", None)
    with tempfile.TemporaryDirectory(prefix="z180-summary-v3-correctness-") as temporary:
        command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "--basetemp", str(Path(temporary) / "pytest"), str(TARGET / "test_summarize.py")]
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "43 passed" in completed.stdout, completed.stdout
    after = {name: sha256(ROOT / name) for name in expected}
    assert after == before
    return {
        "schema": "independent_z180_summary_output_correctness_review/v3",
        "reviewer_source_sha256": sha256(OWN),
        "reviewed_sha256": before,
        "reused_v2_review_receipt_sha256": PREVIOUS_SHA256["receipt.json"],
        "reused_original_review_receipt_sha256": previous["reused_original_review_receipt_sha256"],
        "checks": {
            "source_and_target_pins_before_after": len(before),
            "provided_inert_output_tests_passed": 43,
            "provided_test_result": completed.stdout.strip(),
            "source_inspected_whole_ancestry_dir_fd_creation_and_leaf_reservation": True,
            "source_inspected_started_failed_and_normal_output_paths": True,
            "source_inspected_exact_v2_loader_delegation_and_v3_v2_manifest_pins": True,
            "unchanged_original_build_and_selectors_reused": True,
        },
        "findings": [],
        "limits": [
            "Only v3 source inspection and its provided inert fixtures executed; no additional filesystem mutation experiments were added.",
            "The actual-source loader control executes definitions only. No genuine candidate manifest, roster, config, field, result or summary was evaluated.",
            "Prior frozen original build/source joins/selectors reviews are reused; the numerical and engineering audit was not repeated.",
            "No producer, gate, reducer, CAD/BREP/native, operator, solve or actual field consumption occurred; no adoption, resistance, physical acceptance or release follows.",
            "FAILED retention requires the reserved leaf to remain at its anchored name. Supplied replacement-leaf tests preserve the unrelated replacement and the prior STARTED inode.",
        ],
    }


if __name__ == "__main__":
    receipt = evaluate()
    destination = OWN.with_name("receipt.json")
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)),
                      "receipt_sha256": sha256(destination), "reviewer_sha256": sha256(OWN),
                      "pins": len(receipt["reviewed_sha256"]), "tests": 43, "findings": 0}))
