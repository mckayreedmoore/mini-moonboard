"""Run the frozen focused suite and independent probes against replayed bytes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


REPORT = Path(__file__).resolve().parent
REPO = REPORT.parents[4]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    receipt = json.loads((REPORT / "replay-verification.json").read_text())
    replay = Path(receipt["replay_root"])
    assert receipt["all_checks_passed"]
    for filename, expected in receipt["replay_hashes"]["10"].items():
        assert sha(replay / filename) == expected
    destination = replay / "tests/test_attempt10_independent_review.py"
    shutil.copyfile(REPORT / "test_independent_paths.py", destination)
    environment = os.environ.copy()
    environment.update(
        PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(replay),
        ATTEMPT10_REVIEW_REPLAY_ROOT=str(replay),
    )
    results = []
    for label, filename in (
        ("focused", "tests/test_nds_2024_group_action.py"),
        ("independent", "tests/test_attempt10_independent_review.py"),
    ):
        command = [str(REPO / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", filename]
        run = subprocess.run(command, cwd=replay, env=environment, text=True, capture_output=True)
        output = run.stdout + run.stderr
        (REPORT / f"{label}-test-output.txt").write_text(output)
        results.append({"suite": label, "command": command, "cwd": str(replay), "exit_code": run.returncode,
                        "output_file": f"{label}-test-output.txt", "output_sha256": sha(REPORT / f"{label}-test-output.txt")})
        print(f"{label}: {output.strip()}")
    for filename, expected in receipt["replay_hashes"]["10"].items():
        assert sha(replay / filename) == expected
    attempt = REPORT.with_name("current-group-action-method-attempt10")
    artifact_final = {
        str(path.relative_to(attempt)): sha(path)
        for path in attempt.rglob("*") if path.is_file()
    }
    assert artifact_final == receipt["artifact_sha256_by_file"]
    result = {"schema": "attempt10_independent_test_execution/v1", "runs": results,
              "artifact_unchanged_after_tests": True, "replayed_source_and_original_tests_unchanged": True,
              "all_suites_passed": all(run["exit_code"] == 0 for run in results),
              "environment": {key: environment[key] for key in ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "ATTEMPT10_REVIEW_REPLAY_ROOT")},
              "solver_invoked": False, "docker_invoked": False, "native_execution": False}
    (REPORT / "test-execution.json").write_text(json.dumps(result, indent=2) + "\n")
    raise SystemExit(0 if result["all_suites_passed"] else 1)


if __name__ == "__main__":
    main()
