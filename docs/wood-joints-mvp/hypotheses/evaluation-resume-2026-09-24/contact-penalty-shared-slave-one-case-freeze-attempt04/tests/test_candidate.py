"""Offline checks for the immutable freeze and authorization evidence chain."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker


PACKET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKET))
import authorization_contract  # noqa: E402
import run  # noqa: E402
import verifier  # noqa: E402


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def external_authorization(freeze_sha256: str) -> dict:
    return {
        "schema": authorization_contract.AUTHORIZATION_SCHEMA,
        "status": authorization_contract.AUTHORIZATION_STATUS,
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
        "reviewed_at_utc": "2026-09-28T06:00:00Z",
        "mechanical_or_joint_acceptance": False,
        "native_solver_launched": False,
        "release": False,
    }


def authorization_bytes(record: dict) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(authorization_bytes(value))


def make_root_audit_fixture(root: Path, *, receipt: bytes | None,
                            recorded_receipt_sha256: str | None = None,
                            receipt_record: dict | None = None) -> str:
    """Build a temporary synthetic execution record for auth-gate regression."""
    freeze_path = PACKET / "input-freeze.json"
    freeze = json.loads(freeze_path.read_text())
    freeze_sha256 = file_sha(freeze_path)
    for relative in freeze["files_sha256"]:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PACKET / relative, destination)
    shutil.copyfile(freeze_path, root / "input-freeze.json")

    auth = receipt_record or external_authorization(freeze_sha256)
    receipt_bytes = receipt if receipt is not None else authorization_bytes(auth)
    receipt_digest = hashlib.sha256(receipt_bytes).hexdigest()
    if receipt is not None:
        auth = authorization_contract.parse_json_bytes(receipt)
    receipt_path = root / "output" / run.CASE / "parent-authorization.json"
    if receipt is not None or receipt_record is not None:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_bytes(receipt_bytes)
    recorded_digest = recorded_receipt_sha256 or receipt_digest
    readiness_sha256 = freeze["files_sha256"]["readiness.json"]
    parent_readiness_sha256 = freeze["files_sha256"]["parent-readiness.json"]
    case_record = {
        "case": run.CASE,
        "status": "completed",
        "container": "wj-shared-slave-penalty-shared_slave_penalty-12345",
        "input_freeze_sha256": freeze_sha256,
        "case_order": [run.CASE],
        "readiness_record_sha256": readiness_sha256,
        "parent_readiness_record_sha256": parent_readiness_sha256,
        "external_authorization_sha256": recorded_digest,
        "authorization_receipt_path": f"output/{run.CASE}/parent-authorization.json",
        "native_execution_authorized": auth["native_execution_authorized"],
        "parent_readiness": auth["parent_readiness"],
        "source_input_sha256": run.INPUT_SHA256,
        "candidate_oracle_sha256": run.ORACLE_SHA256,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }
    execution = {
        "schema": "shared_slave_penalty_one_case_execution/v1",
        "status": "completed_pending_audit",
        "cases": [run.CASE],
        "runs": [case_record],
        "input_freeze_sha256": freeze_sha256,
        "case_order": [run.CASE],
        "readiness_record_sha256": readiness_sha256,
        "parent_readiness_record_sha256": parent_readiness_sha256,
        "external_authorization_sha256": recorded_digest,
        "authorization_receipt_path": f"output/{run.CASE}/parent-authorization.json",
        "native_execution_authorized": auth["native_execution_authorized"],
        "parent_readiness": auth["parent_readiness"],
        "source_input_sha256": run.INPUT_SHA256,
        "candidate_oracle_sha256": run.ORACLE_SHA256,
        "image_id": run.IMAGE,
        "binary_sha256": run.BINARY_SHA256,
        "frozen_inputs_unchanged": True,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }
    write_json(root / "execution.json", execution)
    return freeze_sha256


class CandidateTests(unittest.TestCase):
    def test_static_pins_and_false_candidate_gates(self) -> None:
        expected, readiness = run.verify_static_pins()
        source = authorization_contract.parse_json_bytes(
            (PACKET / "source-snapshot.json").read_bytes())
        parent = authorization_contract.parse_json_bytes(
            (PACKET / "parent-readiness.json").read_bytes())
        freeze = authorization_contract.parse_json_bytes(
            (PACKET / "input-freeze.json").read_bytes())
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

    def test_false_readiness_stops_before_any_process_or_docker_call(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        with patch.object(run.subprocess, "run",
                          side_effect=AssertionError("process/Docker invoked")), \
                patch.object(run.subprocess, "Popen",
                             side_effect=AssertionError("process/Docker invoked")):
            with self.assertRaisesRegex(RuntimeError, "Readiness is false"):
                run.run(freeze_sha256)
        self.assertFalse((PACKET / "execution.json").exists())
        self.assertFalse((PACKET / "output").exists())

    def test_external_authorization_uses_one_byte_snapshot_and_strict_json(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        record = external_authorization(freeze_sha256)
        raw = authorization_bytes(record)
        with tempfile.TemporaryDirectory() as temp:
            external_path = Path(temp) / "parent-authorization.json"
            external_path.write_bytes(raw)
            parsed, digest, returned_raw = run.load_external_authorization(external_path)
        self.assertEqual(returned_raw, raw)
        self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
        self.assertEqual(parsed, record)
        with self.assertRaisesRegex(authorization_contract.AuthorizationError,
                                    "Duplicate JSON key"):
            authorization_contract.parse_json_bytes(
                b'{"schema":"first","schema":"second"}')

    def test_execution_gate_accepts_frozen_snapshots_without_process_calls(self) -> None:
        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        authorization = external_authorization(freeze_sha256)
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate"
            shutil.copytree(PACKET, candidate,
                            ignore=shutil.ignore_patterns("__pycache__"))
            with patch.object(run, "HERE", candidate):
                frozen = run.verify_freeze(freeze_sha256)
                with patch.object(run.subprocess, "run",
                                  side_effect=AssertionError("process/Docker invoked")) as process_run, \
                        patch.object(run.subprocess, "Popen",
                                     side_effect=AssertionError("process/Docker invoked")) as process_popen:
                    run.assert_execution_ready(freeze_sha256, frozen, authorization)
                    process_run.assert_not_called()
                    process_popen.assert_not_called()

                self.assertFalse((candidate / "execution.json").exists())
                self.assertFalse((candidate / "output").exists())
                self.assertFalse((candidate / "output" / run.CASE /
                                  "parent-authorization.json").exists())

                for filename, message in (
                    ("readiness.json", "Readiness snapshot differs from the verified freeze"),
                    ("parent-readiness.json",
                     "Parent-readiness snapshot differs from the verified freeze"),
                ):
                    with self.subTest(snapshot=filename):
                        snapshot_path = candidate / filename
                        original = snapshot_path.read_bytes()
                        snapshot_path.write_bytes(b"\n" + original)
                        with self.assertRaisesRegex(RuntimeError, message):
                            run.assert_execution_ready(freeze_sha256, frozen,
                                                       authorization)
                        snapshot_path.write_bytes(original)

    def test_authorization_receipt_persists_exact_bytes_exclusively(self) -> None:
        record = external_authorization(file_sha(PACKET / "input-freeze.json"))
        raw = authorization_bytes(record)
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            output.mkdir()
            with self.assertRaisesRegex(RuntimeError, "bytes differ"):
                run.write_authorization_receipt(output, raw, "0" * 64)
            receipt = run.write_authorization_receipt(output, raw, digest)
            self.assertEqual(receipt.read_bytes(), raw)
            self.assertEqual(file_sha(receipt), digest)
            with self.assertRaises(FileExistsError):
                run.write_authorization_receipt(output, raw, digest)

    def test_schema_and_runtime_accept_and_reject_same_authorization_fixtures(self) -> None:
        self.assertEqual(importlib.metadata.version("jsonschema"), "4.10.3")
        schema = authorization_contract.parse_json_bytes(
            (PACKET / "external-authorization.schema.json").read_bytes())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        properties = schema["properties"]
        self.assertEqual(set(schema["required"]),
                         authorization_contract.AUTHORIZATION_FIELDS)
        self.assertEqual(set(properties), authorization_contract.AUTHORIZATION_FIELDS)
        self.assertIs(properties["native_execution_authorized"]["const"], True)
        self.assertIs(properties["parent_readiness"]["const"], True)
        for name in ("mechanical_or_joint_acceptance", "native_solver_launched", "release"):
            self.assertIs(properties[name]["const"], False)
        self.assertEqual(properties["reviewed_at_utc"]["format"], "date-time")

        freeze_sha256 = file_sha(PACKET / "input-freeze.json")
        valid = external_authorization(freeze_sha256)
        self.assertTrue(validator.is_valid(valid))
        run.check_external_authorization(
            freeze_sha256,
            valid["readiness_record_sha256"],
            valid["parent_readiness_record_sha256"],
            valid,
        )
        context_mismatch_fixtures = (
            {**valid, "input_freeze_sha256": "0" * 64},
            {**valid, "readiness_record_sha256": "0" * 64},
            {**valid, "parent_readiness_record_sha256": "0" * 64},
        )
        for fixture in context_mismatch_fixtures:
            with self.subTest(context_binding=fixture):
                # JSON Schema constrains dynamic hashes to SHA-256 form; the
                # runtime must bind them to this exact frozen candidate.
                self.assertTrue(validator.is_valid(fixture))
                with self.assertRaises(authorization_contract.AuthorizationError):
                    run.check_external_authorization(
                        freeze_sha256,
                        valid["readiness_record_sha256"],
                        valid["parent_readiness_record_sha256"],
                        fixture,
                    )

        invalid_fixtures = (
            {**valid, "source_input_sha256": "0" * 64},
            {**valid, "candidate_oracle_sha256": "0" * 64},
            {**valid, "case_order": []},
            {**valid, "unexpected": "field"},
            {**valid, "native_execution_authorized": False},
            {**valid, "parent_readiness": False},
            {**valid, "mechanical_or_joint_acceptance": True},
            {**valid, "native_solver_launched": True},
            {**valid, "release": True},
            {**valid, "reviewed_at_utc": "2026-09-28T00:00:00-06:00"},
            {**valid, "reviewed_at_utc": "not-a-date"},
        )
        for fixture in invalid_fixtures:
            with self.subTest(fixture=fixture):
                self.assertFalse(validator.is_valid(fixture))
                with self.assertRaises(authorization_contract.AuthorizationError):
                    run.check_external_authorization(
                        freeze_sha256,
                        valid["readiness_record_sha256"],
                        valid["parent_readiness_record_sha256"],
                        fixture,
                    )

    def test_verifier_requires_receipt_and_matching_bindings_before_coupon_pass(self) -> None:
        valid = external_authorization(file_sha(PACKET / "input-freeze.json"))
        raw = authorization_bytes(valid)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            freeze_sha256 = make_root_audit_fixture(root, receipt=None,
                                                    receipt_record=valid)
            receipt_path = root / "output" / run.CASE / "parent-authorization.json"
            self.assertEqual(receipt_path.read_bytes(), raw)
            with patch.object(verifier, "HERE", root), \
                    patch.object(verifier, "audit_case", return_value={"status": "PASS"}):
                result = verifier.audit_root()
            self.assertEqual(result["status"], "PASS_SHARED_SLAVE_PENALTY_COUPON")
            self.assertEqual(result["external_authorization_sha256"],
                             hashlib.sha256(raw).hexdigest())

        cases = (
            ("missing", None, None, "receipt is missing"),
            ("digest mismatch", raw, "0" * 64, "digest differs"),
            ("freeze binding mismatch",
             authorization_bytes({**valid, "input_freeze_sha256": "0" * 64}),
             None, "hash binding differs"),
            ("readiness binding mismatch",
             authorization_bytes({**valid, "readiness_record_sha256": "0" * 64}),
             None, "hash binding differs"),
            ("parent-readiness binding mismatch",
             authorization_bytes({**valid,
                                  "parent_readiness_record_sha256": "0" * 64}),
             None, "hash binding differs"),
            ("source binding mismatch",
             authorization_bytes({**valid, "source_input_sha256": "0" * 64}),
             None, "source pins differ"),
            ("oracle binding mismatch",
             authorization_bytes({**valid, "candidate_oracle_sha256": "0" * 64}),
             None, "source pins differ"),
            ("case binding mismatch",
             authorization_bytes({**valid, "case_order": []}),
             None, "case scope differs"),
            ("false gate",
             authorization_bytes({**valid, "native_execution_authorized": False}),
             None, "gates are false"),
        )
        for label, receipt_bytes, digest_override, message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_root_audit_fixture(
                    root,
                    receipt=receipt_bytes,
                    recorded_receipt_sha256=digest_override,
                )
                with patch.object(verifier, "HERE", root), \
                        patch.object(verifier, "audit_case",
                                     return_value={"status": "PASS"}):
                    with self.assertRaisesRegex((ValueError, RuntimeError), message):
                        verifier.audit_root()


if __name__ == "__main__":
    unittest.main()
