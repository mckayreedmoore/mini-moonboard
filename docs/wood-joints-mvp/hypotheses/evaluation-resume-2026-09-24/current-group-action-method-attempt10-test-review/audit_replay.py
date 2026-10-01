"""Independently verify the immutable attempt10 chain in temporary trees."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


REPORT = Path(__file__).resolve().parent
REPO = REPORT.parents[4]
ATTEMPT = REPORT.with_name("current-group-action-method-attempt10")
ATTEMPT07 = ATTEMPT.with_name("current-group-action-method-attempt07")
FILES = (
    "mini_moonboard/nds_2024_group_action.py",
    "tests/test_nds_2024_group_action.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    checks = []

    def check(label: str, observed, expected) -> None:
        checks.append(
            {
                "label": label,
                "observed": observed,
                "expected": expected,
                "passed": observed == expected,
            }
        )
        assert observed == expected, label

    original = {
        str(path.relative_to(ATTEMPT)): sha(path)
        for path in ATTEMPT.rglob("*")
        if path.is_file()
    }
    pins = read_json(ATTEMPT / "source-pins.json")
    terminal = read_json(ATTEMPT / "terminal-hashes.json")
    validation = read_json(ATTEMPT / "validation.json")
    for name, expected in terminal["sha256_by_file"].items():
        check(f"attempt10 terminal entry {name}", sha(ATTEMPT / name), expected)
    for filename in FILES:
        base_sha = sha(ATTEMPT / "base" / filename)
        check(
            f"attempt10 base source pin {filename}",
            base_sha,
            pins["attempt07_base_sha256_by_file"][filename],
        )
        check(
            f"attempt10 base terminal pin {filename}",
            base_sha,
            terminal["attempt07_base_sha256_by_file"][filename],
        )
        check(
            f"attempt10 base validation pin {filename}",
            base_sha,
            validation["base_attempt07_sha256_by_file"][filename],
        )
        maintained_sha = sha(REPO / filename)
        for name, data in (("source", pins), ("terminal", terminal), ("validation", validation)):
            check(
                f"maintained attempt10 {name} pin {filename}",
                maintained_sha,
                data["maintained_attempt10_sha256_by_file"][filename],
            )
    check(
        "attempt10 patch source pin",
        sha(ATTEMPT / "attempt10.patch"),
        pins["attempt10_patch_sha256"],
    )
    check(
        "attempt07 patch source pin",
        sha(ATTEMPT07 / "attempt07.patch"),
        pins["attempt07_patch_sha256"],
    )
    check(
        "attempt07 terminal source pin",
        sha(ATTEMPT07 / "terminal-hashes.json"),
        pins["attempt07_terminal_hashes_sha256"],
    )
    check(
        "attempt09 terminal source pin",
        sha(REPO / pins["attempt09_terminal_hashes_path"]),
        pins["attempt09_terminal_hashes_sha256"],
    )
    check(
        "unchanged criteria method map",
        sha(REPO / pins["criteria_method_map_path"]),
        pins["criteria_method_map_sha256"],
    )
    for number in ("07", "09"):
        directory = ATTEMPT.with_name(f"current-group-action-method-attempt{number}")
        manifest = read_json(directory / "terminal-hashes.json")
        for name, expected in manifest["sha256_by_file"].items():
            check(f"attempt{number} terminal entry {name}", sha(directory / name), expected)

    pins07 = read_json(ATTEMPT07 / "source-pins.json")
    terminal07 = read_json(ATTEMPT07 / "terminal-hashes.json")
    for filename in FILES:
        check(
            f"attempt07 base source pin {filename}",
            sha(ATTEMPT07 / "base" / filename),
            pins07["attempt06_base_sha256_by_file"][filename],
        )
        check(
            f"attempt07 maintained equals attempt10 base {filename}",
            terminal07["maintained_attempt07_sha256_by_file"][filename],
            pins["attempt07_base_sha256_by_file"][filename],
        )

    temporary = Path(tempfile.mkdtemp(prefix="attempt10-independent-test-review-"))
    patch_logs = {}
    replay_hashes = {}
    for number, directory, expected_hashes in (
        ("07", ATTEMPT07, pins["attempt07_base_sha256_by_file"]),
        ("10", ATTEMPT, pins["maintained_attempt10_sha256_by_file"]),
    ):
        tree = temporary / f"replay{number}"
        shutil.copytree(directory / "base", tree)
        command = [
            "patch", "--batch", "--forward", "--fuzz=0", "-p1", "-i",
            str(directory / f"attempt{number}.patch"),
        ]
        run = subprocess.run(command, cwd=tree, text=True, capture_output=True)
        log = run.stdout + run.stderr
        patch_logs[number] = {"command": command, "exit_code": run.returncode, "output": log}
        check(f"attempt{number} replay exit", run.returncode, 0)
        check(f"attempt{number} no fuzz or offsets", "fuzz" in log.lower() or "offset" in log.lower(), False)
        check(f"attempt{number} no rejection files", list(tree.rglob("*.rej")), [])
        replay_hashes[number] = {filename: sha(tree / filename) for filename in FILES}
        for filename, expected in expected_hashes.items():
            check(f"attempt{number} replay bytes {filename}", sha(tree / filename), expected)

    final = {
        str(path.relative_to(ATTEMPT)): sha(path)
        for path in ATTEMPT.rglob("*")
        if path.is_file()
    }
    check("entire attempt10 artifact untouched", final, original)
    result = {
        "schema": "attempt10_independent_test_review_replay/v1",
        "artifact_sha256_by_file": original,
        "replay_root": str(temporary / "replay10"),
        "replay_hashes": replay_hashes,
        "patch_logs": patch_logs,
        "checks": checks,
        "check_count": len(checks),
        "all_checks_passed": all(check["passed"] for check in checks),
        "solver_invoked": False,
        "docker_invoked": False,
        "native_execution": False,
    }
    (REPORT / "replay-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"check_count": len(checks), "all_checks_passed": True, "replay_root": result["replay_root"]}))


if __name__ == "__main__":
    main()
