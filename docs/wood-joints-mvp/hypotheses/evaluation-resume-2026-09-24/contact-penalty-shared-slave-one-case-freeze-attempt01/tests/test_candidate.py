"""Offline checks for candidate pins, scope, and fail-closed readiness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


PACKET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKET))
import run  # noqa: E402


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CandidateTests(unittest.TestCase):
    def test_exact_source_input_and_oracle_pins(self) -> None:
        expected, readiness = run.verify_static_pins()
        source = json.loads((PACKET / "source-snapshot.json").read_text())
        self.assertEqual(run.INPUT_SHA256,
                         "d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7")
        self.assertEqual(run.SOURCE_ORACLE_SHA256,
                         "29ce26d69e94579fb49af86b8608e0b001310f670a294eb596997a3ce2b538b0")
        self.assertEqual(file_sha(PACKET / "input/shared_slave_penalty.inp"),
                         run.INPUT_SHA256)
        self.assertEqual(file_sha(PACKET / "expected.json"), run.ORACLE_SHA256)
        self.assertEqual(source["upstream_expected_contract"]["sha256"],
                         run.SOURCE_ORACLE_SHA256)
        self.assertEqual(source["candidate_oracle"]["sha256"], run.ORACLE_SHA256)
        self.assertIs(readiness["native_execution_authorized"], False)

    def test_freeze_and_oracle_are_strictly_one_case(self) -> None:
        expected = json.loads((PACKET / "expected.json").read_text())
        freeze = json.loads((PACKET / "input-freeze.json").read_text())
        self.assertEqual(expected["case_order"], ["shared_slave_penalty"])
        self.assertEqual(list(expected["cases"]), ["shared_slave_penalty"])
        self.assertEqual(freeze["cases"], ["shared_slave_penalty"])
        self.assertEqual(list((PACKET / "input").glob("*.inp")),
                         [PACKET / "input/shared_slave_penalty.inp"])
        self.assertEqual(freeze["limits"]["cases_per_freeze"], 1)
        self.assertEqual(freeze["limits"]["runs_total"], 1)
        self.assertEqual(freeze["limits"]["runs_per_case"], 1)
        self.assertEqual(freeze["limits"]["max_active_native_processes"], 1)

    def test_runner_fails_closed_before_process_or_docker_invocation(self) -> None:
        freeze_path = PACKET / "input-freeze.json"
        freeze_sha = file_sha(freeze_path)
        with patch.object(run.subprocess, "run",
                          side_effect=AssertionError("Docker command was invoked")), \
                patch.object(run.subprocess, "Popen",
                             side_effect=AssertionError("Native process was invoked")):
            with self.assertRaisesRegex(RuntimeError, "not authorized"):
                run.run(freeze_sha)
        self.assertFalse((PACKET / "execution.json").exists())
        self.assertFalse((PACKET / "output").exists())


if __name__ == "__main__":
    unittest.main()
