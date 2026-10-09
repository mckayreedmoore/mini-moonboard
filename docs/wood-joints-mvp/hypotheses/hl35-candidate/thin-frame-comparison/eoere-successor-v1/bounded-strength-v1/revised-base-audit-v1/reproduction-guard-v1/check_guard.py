"""Cheap guard controls; real rejected CLIs and isolated stdlib stub runs only."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import run_fresh as guard


def expect_failure(operation, expected):
    try:
        operation()
    except expected:
        return
    raise ValueError("negative control did not reject")


def controls(inputs):
    passed = []
    with tempfile.TemporaryDirectory(prefix="eoere-output-guard-") as directory:
        temporary = Path(directory)
        source = temporary / "source.txt"
        source.write_text("unchanged fixture source\n")
        pins = {str(source): guard.sha(source)}
        calls = {"before": 0, "calculate": 0, "after": 0}

        def before():
            calls["before"] += 1
            guard.verify(pins)
            return {
                "pins": pins,
                "issued_pin_count": 1,
                "issued_closure_canonical_sha256": guard.canonical(pins),
                "guarded_pin_count": 1,
                "guarded_closure_canonical_sha256": guard.canonical(pins),
            }

        def calculate():
            calls["calculate"] += 1
            return {"status": "STDLIB_STUB_ONLY"}, {"fixture_rows": [1, 2]}

        def after(snapshot):
            calls["after"] += 1
            guard.verify(snapshot["pins"])

        def run(path, producer=calculate, compare=None):
            return guard.guarded_calculation(
                path, before, producer, after, {"fixture_only": True}, compare
            )

        successful = temporary / "successful"
        record = run(successful)
        guard.require(
            calls == {"before": 1, "calculate": 1, "after": 2}, "fresh run order"
        )
        guard.require(
            record["status"] == "VERIFIED_FRESH_OUTPUT", "positive fixture status"
        )
        passed.append(
            "fresh_stdlib_stub_authenticates_before_and_after_and_writes_exclusively"
        )
        original = {p.name: p.read_bytes() for p in successful.iterdir()}
        previous_calls = dict(calls)
        expect_failure(lambda: run(successful), FileExistsError)
        guard.require(
            calls == previous_calls, "existing output reached authentication/run"
        )
        guard.require(
            original == {p.name: p.read_bytes() for p in successful.iterdir()},
            "existing artifacts changed",
        )
        passed.append("existing_populated_directory_rejected_before_callbacks")

        empty = temporary / "empty"
        empty.mkdir()
        expect_failure(lambda: run(empty), FileExistsError)
        passed.append("existing_empty_directory_rejected")
        file = temporary / "existing-file"
        file.write_bytes(b"preserve")
        expect_failure(lambda: run(file), FileExistsError)
        guard.require(file.read_bytes() == b"preserve", "existing file changed")
        passed.append("existing_file_rejected_unchanged")
        link = temporary / "populated-link"
        link.symlink_to(successful, target_is_directory=True)
        expect_failure(lambda: run(link), FileExistsError)
        passed.append("existing_directory_symlink_rejected")
        dangling = temporary / "dangling-link"
        dangling.symlink_to(temporary / "absent-target", target_is_directory=True)
        expect_failure(lambda: run(dangling), FileExistsError)
        guard.require(
            not (temporary / "absent-target").exists(), "dangling output followed"
        )
        passed.append("dangling_output_symlink_rejected_without_following")
        expect_failure(
            lambda: guard.write_new(file, {"replacement": True}), FileExistsError
        )
        guard.require(
            file.read_bytes() == b"preserve", "exclusive write changed existing file"
        )
        passed.append("exclusive_file_creation_rejects_collision")

        source.write_text("changed before run\n")
        output = temporary / "bad-source"
        count = calls["calculate"]
        expect_failure(lambda: run(output), ValueError)
        guard.require(
            calls["calculate"] == count and not list(output.iterdir()),
            "changed source reached calculation",
        )
        passed.append("changed_source_rejected_before_calculation")
        source.write_text("unchanged fixture source\n")

        def altered():
            source.write_text("changed during calculation\n")
            return calculate()

        output = temporary / "changed-during"
        expect_failure(lambda: run(output, altered), ValueError)
        guard.require(not list(output.iterdir()), "changed sources published outputs")
        passed.append("source_change_during_calculation_rejected_before_outputs")
        source.write_text("unchanged fixture source\n")

        def failed():
            raise RuntimeError("controlled producer failure")

        output = temporary / "producer-failed"
        after_count = calls["after"]
        expect_failure(lambda: run(output, failed), RuntimeError)
        guard.require(
            calls["after"] == after_count + 1 and not list(output.iterdir()),
            "failed producer bypassed after-authentication",
        )
        expect_failure(lambda: run(output), FileExistsError)
        passed.append("failed_attempt_kept_reserved_and_after_authentication_ran")
        output = temporary / "compare-good"
        run(output, compare=successful)
        passed.append("fresh_exact_compare_fixture_passes")
        wrong = temporary / "compare-wrong-source"
        wrong.mkdir()
        (wrong / "result.json").write_text("wrong\n")
        output = temporary / "compare-rejected"
        expect_failure(lambda: run(output, compare=wrong), ValueError)
        guard.require(not list(output.iterdir()), "failed comparison wrote results")
        passed.append("mismatched_compare_rejected_before_writing")

        for key, packet in inputs["packets"].items():
            existing = guard.ROOT / packet["details"]["path"]
            existing = existing.parent
            observed = {p.name: guard.sha(p) for p in existing.iterdir() if p.is_file()}
            completed = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(guard.HERE / "run_fresh.py"),
                    "--packet",
                    key,
                    "--out",
                    str(existing),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            guard.require(
                completed.returncode == 2 and "File exists" in completed.stderr,
                "real CLI did not reject existing issued directory",
            )
            guard.require(
                observed
                == {p.name: guard.sha(p) for p in existing.iterdir() if p.is_file()},
                "real CLI altered issued attempt",
            )
            passed.append(
                "real_"
                + key
                + "_CLI_existing_attempt_rejected_with_site_packages_disabled"
            )
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        guard.reserve_output(args.out)
        inputs, digest = guard.load_inputs()
        snapshots = [
            guard.authenticate(inputs, digest, key) for key in inputs["packets"]
        ]
        passed = controls(inputs)
        for snapshot in snapshots:
            guard.verify(snapshot["pins"])
        record = {
            "schema": "frozen_analysis_output_guard_controls/v1",
            "status": "PASS",
            "passed_controls": passed,
            "control_count": len(passed),
            "real_full_analysis_executed": False,
            "native_solve_CAD_rebuild_or_new_response": False,
            "issued_packet_files_and_attempts_unchanged": True,
            "both_issued_source_closures_verified_before_after": [
                s["issued_pin_count"] for s in snapshots
            ],
            "inputs_sha256": digest,
            "checker": {
                "path": str(Path(__file__).relative_to(guard.ROOT)),
                "sha256": guard.sha(__file__),
            },
            "fixture_scope": "Successful calculation fixtures use the common guarded runner with stdlib stubs. Real CLIs are exercised only on existing output paths, with -S, and must reject before importing an analysis.",
        }
        guard.write_new(args.out / "guard-controls.json", record)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps({"status": record["status"], "controls": len(passed)}))


if __name__ == "__main__":
    main()
