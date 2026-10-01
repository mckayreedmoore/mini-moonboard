"""Strict parsing and shared validation for external coupon authorization."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re


CASE = "shared_slave_penalty"
INPUT_SHA256 = "d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7"
ORACLE_SHA256 = "8c0344c1c7f98976cd1636532eb73925c9c896917c5110729834c816e4c0c9da"
AUTHORIZATION_SCHEMA = "shared_slave_penalty_one_case_external_authorization/v1"
AUTHORIZATION_STATUS = "AUTHORIZED_FOR_ONE_CASE_COUPON_ONLY"
AUTHORIZATION_FIELDS = frozenset({
    "schema", "status", "native_execution_authorized", "parent_readiness",
    "input_freeze_sha256", "readiness_record_path", "readiness_record_sha256",
    "parent_readiness_record_path", "parent_readiness_record_sha256",
    "case_order", "source_input_sha256", "candidate_oracle_sha256",
    "reviewer", "reviewed_at_utc", "mechanical_or_joint_acceptance",
    "native_solver_launched", "release",
})
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$"
)


class AuthorizationError(ValueError):
    """A strict parse or external-authorization contract failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuthorizationError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json_bytes(data: bytes) -> object:
    """Parse one UTF-8 JSON byte snapshot, rejecting ambiguous JSON values."""
    require(isinstance(data, bytes), "JSON input must be bytes")

    def unique_object(items):
        result = {}
        for name, value in items:
            require(name not in result, f"Duplicate JSON key: {name}")
            result[name] = value
        return result

    def reject_constant(value):
        raise AuthorizationError(f"Nonfinite JSON number: {value}")

    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), f"Nonfinite JSON number: {value}")
        return result

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_float=finite_float, parse_constant=reject_constant)
    except UnicodeDecodeError as exc:
        raise AuthorizationError("JSON input is not valid UTF-8") from exc


def read_json_snapshot(path: Path) -> tuple[object, bytes, str]:
    """Hash and parse the same file bytes to avoid a read/parse race."""
    data = path.read_bytes()
    return parse_json_bytes(data), data, sha256_bytes(data)


def validate_external_authorization(
    record: object,
    *,
    input_freeze_sha256: str,
    readiness_record_sha256: str,
    parent_readiness_record_sha256: str,
    source_input_sha256: str = INPUT_SHA256,
    candidate_oracle_sha256: str = ORACLE_SHA256,
    case_order: tuple[str, ...] = (CASE,),
) -> None:
    """Validate the shared runtime and verifier authorization contract."""
    require(isinstance(record, dict), "External authorization must be a JSON object")
    require(set(record) == AUTHORIZATION_FIELDS,
            "External authorization fields differ from the frozen schema")
    require(record.get("schema") == AUTHORIZATION_SCHEMA,
            "Unexpected external authorization schema")
    require(record.get("status") == AUTHORIZATION_STATUS,
            "External authorization is not in the authorized state")
    require(record.get("native_execution_authorized") is True and
            record.get("parent_readiness") is True,
            "External authorization gates are false")
    require(record.get("input_freeze_sha256") == input_freeze_sha256 and
            record.get("readiness_record_sha256") == readiness_record_sha256 and
            record.get("parent_readiness_record_sha256") ==
            parent_readiness_record_sha256,
            "External authorization hash binding differs")
    for name in (
        "input_freeze_sha256", "readiness_record_sha256",
        "parent_readiness_record_sha256", "source_input_sha256",
        "candidate_oracle_sha256",
    ):
        require(isinstance(record.get(name), str) and
                SHA256_PATTERN.fullmatch(record[name]) is not None,
                f"External authorization {name} is not a lowercase SHA-256")
    require(record.get("readiness_record_path") == "readiness.json" and
            record.get("parent_readiness_record_path") == "parent-readiness.json",
            "External authorization readiness record path differs")
    require(record.get("case_order") == list(case_order),
            "External authorization case scope differs")
    require(record.get("source_input_sha256") == source_input_sha256 and
            record.get("candidate_oracle_sha256") == candidate_oracle_sha256,
            "External authorization source pins differ")
    require(isinstance(record.get("reviewer"), str) and
            bool(record["reviewer"].strip()),
            "External authorization has no reviewer")
    timestamp = record.get("reviewed_at_utc")
    require(isinstance(timestamp, str) and
            UTC_TIMESTAMP_PATTERN.fullmatch(timestamp) is not None,
            "External authorization timestamp must be RFC 3339 UTC")
    try:
        reviewed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError("External authorization timestamp is invalid") from exc
    require(reviewed_at.tzinfo is not None and
            reviewed_at.utcoffset() == timezone.utc.utcoffset(reviewed_at),
            "External authorization timestamp must be UTC")
    require(record.get("mechanical_or_joint_acceptance") is False and
            record.get("native_solver_launched") is False and
            record.get("release") is False,
            "External authorization must not claim execution, acceptance, or release")
