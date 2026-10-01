"""Offline checks for the immutable one-case freeze and authorization seam."""

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


def external_authorization(freeze_sha256: str) -> dict:
    return {
        "schema": "shared_slave_penalty_one_case_external_authorization/v1",
        "status": "AUTHORIZED_FOR_ONE_CASE_COUPON_ONLY",
        "native_execution_authorized": True,
        "parent_readiness": True,
        "input_freeze_sha256": freeze_sha256,
        "readiness_record_path": "readiness.json",
        "readiness_record_sha256": file_sha(PACKET / "readiness.json"),
        "parent_readiness_record_path": "parent-readiness.json",
        "parent_readiness_record_sha256": file_sha(PACKET / "parent-readiness.json"),
        "case_order": [run.CASE],
        "source_input_sha256": run.INPUT_SHA256,
        "candidate_oracle_sha256": run.ORACLE_SHA256,
        "reviewer": "offline test fixture only",
        "reviewed_at_utc": "2026-09-28T00:00:00Z",
        "mechanical_or_joint_acceptance": False,
        "native_solver_launched": False,
        "release": False,
    }


class CandidateTests(unittest.TestCase):
    def test_exact_source_input_oracle_and_false_candidate_gates(self) -> None:
        expected, readiness = run.verify_static_pins()
        source = json.loads((PACKET / "source-snapshot.json").read_text())
        parent = json.loads((PACKET / "parent-readiness.json").read_text())
        freeze = json.loads((PACKET / "input-freeze.json").read_text())
        self.assertEqual(file_sha(PACKET / "input/shared_slave_penalty.inp"),
                         run.INPUT_SHA256)
        self.assertEqual(file_sha(PACKET / "expected.json"), run.ORACLE_SHA256)
        self.assertEqual(source["upstream_expected_contract"]["sha256"],
                         run.SOURCE_ORACLE_SHA256)
        self.assertEqual(source["candidate_oracle"]["sha256"], run.ORACLE_SHA256)
        self.assertEqual(expected["case_order"], [run.CASE])
        self.assertIs(readiness["native_execution_authorized"], False)
        self.assertIs(readiness["parent_readiness"], False)
        self.assertIs(parent["native_execution_authorized"], False)
        self.assertIs(parent["parent_readiness"], False)
        self.assertIs(freeze["native_execution_authorized_at_freeze"], False)
        self.assertIs(freeze["parent_readiness_at_freeze"], False)

    def test_candidate_readiness_blocks_before_any_process_or_docker_call(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        with patch.object(run.subprocess, "run",
                          side_effect=AssertionError("process/Docker invoked")), \
                patch.object(run.subprocess, "Popen",
                             side_effect=AssertionError("process/Docker invoked")):
            with self.assertRaisesRegex(RuntimeError, "Readiness is false"):
                run.run(freeze_sha256)
        self.assertFalse((PACKET / "execution.json").exists())
        self.assertFalse((PACKET / "output").exists())

    def test_external_authorization_binds_exact_freeze_and_readiness_purely(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        run.verify_freeze(freeze_sha256)
        authorization = external_authorization(freeze_sha256)
        with patch.object(run.subprocess, "run",
                          side_effect=AssertionError("process/Docker invoked")), \
                patch.object(run.subprocess, "Popen",
                             side_effect=AssertionError("process/Docker invoked")):
            run.check_external_authorization(
                freeze_sha256,
                file_sha(PACKET / "readiness.json"),
                file_sha(PACKET / "parent-readiness.json"),
                authorization,
            )
            run.assert_execution_ready(freeze_sha256, authorization)
        # The reviewed transition is represented only in memory by this test;
        # the candidate readiness and parent-readiness files remain false.
        self.assertIs(json.loads((PACKET / "readiness.json").read_text())[
            "native_execution_authorized"], False)
        self.assertIs(json.loads((PACKET / "parent-readiness.json").read_text())[
            "parent_readiness"], False)

    def test_hash_mismatch_and_false_external_gates_fail_closed(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        run.verify_freeze(freeze_sha256)
        valid = external_authorization(freeze_sha256)
        cases = (
            ("freeze", {**valid, "input_freeze_sha256": "0" * 64},
             "exact input freeze"),
            ("readiness", {**valid, "readiness_record_sha256": "0" * 64},
             "exact readiness record"),
            ("parent readiness", {**valid,
                                   "parent_readiness_record_sha256": "0" * 64},
             "exact parent-readiness record"),
            ("native authorization", {**valid,
                                      "native_execution_authorized": False},
             "gates are false"),
            ("parent readiness gate", {**valid, "parent_readiness": False},
             "gates are false"),
        )
        for label, authorization, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(RuntimeError, message):
                    run.assert_execution_ready(freeze_sha256, authorization)


if __name__ == "__main__":
    unittest.main()
