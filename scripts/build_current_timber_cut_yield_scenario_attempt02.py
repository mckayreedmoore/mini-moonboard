#!/usr/bin/env python3
"""Harden and re-authenticate the current 24-block cut-length scenarios."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-timber-cut-yield-scenario-attempt02"
)
ATTEMPT01_PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-timber-cut-yield-scenario-attempt01"
)
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_AUTHORITY = "compact-floor-flush-development"
REPORT_NAME = "current-timber-cut-yield-scenarios.json"
VERIFICATION_NAME = "verification.json"
ATTEMPT01_REPORT_NAME = "current-timber-cut-yield-scenarios.json"
ATTEMPT01_VERIFICATION_NAME = "verification.json"
REVIEW_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-timber-cut-yield-scenario-attempt01-independent-review-2026-09-28/REVIEW.md"
)
SOURCE_ROLES = {
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json": "block_schedule",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "manifest",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/grade-disposition.json": "grade",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt02/material-stock-and-panel-status.json": "cost_status",
    "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json": "revision",
    "current-candidate.json": "selected_authority",
    "scripts/build_current_timber_cut_yield_scenario_attempt01.py": "attempt01_builder",
    "tests/test_current_timber_cut_yield_scenario_attempt01.py": "attempt01_tests",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01/README.md": "attempt01_readme",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01/source-pins.json": "attempt01_source_pins",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01/scenario-inputs.json": "attempt01_scenario_inputs",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01/current-timber-cut-yield-scenarios.json": "attempt01_report",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01/verification.json": "attempt01_verification",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt01-independent-review-2026-09-28/REVIEW.md": "attempt01_review",
}
REVIEWED_ATTEMPT01_ROLES = {
    "attempt01_builder",
    "attempt01_tests",
    "attempt01_source_pins",
    "attempt01_scenario_inputs",
    "attempt01_report",
    "attempt01_verification",
}
RIPPED_4X6_IDS = {
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
}


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot read strict JSON {path}: {exc}") from exc


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value}")


def require_finite_number(
    name: str, value: Any, *, positive: bool = False, nonnegative: bool = False
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{name} must be greater than zero")
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def validate_revision_identity(
    schedule: dict[str, Any], revision: dict[str, Any]
) -> None:
    if schedule.get("geometry_revision_id") != REVISION_ID:
        raise ValueError(
            "source-yield schedule geometry_revision_id differs from the reviewed revision"
        )
    if revision.get("revision_id") != REVISION_ID:
        raise ValueError(
            "revision source revision_id differs from the reviewed revision"
        )


def validate_manifest_block_ids(
    schedule_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]
) -> None:
    schedule_ids = [row.get("part_id") for row in schedule_rows]
    manifest_ids = [row.get("part_id") for row in manifest_rows]
    if any(
        not isinstance(part_id, str) or not part_id
        for part_id in schedule_ids + manifest_ids
    ):
        raise ValueError("schedule and manifest block IDs must be nonempty strings")
    if len(schedule_ids) != 24 or len(set(schedule_ids)) != 24:
        raise ValueError(
            "source-yield schedule must contain exactly 24 unique block IDs"
        )
    if len(manifest_ids) != 24 or len(set(manifest_ids)) != 24:
        raise ValueError("attempt04 manifest must contain exactly 24 unique block IDs")
    if set(schedule_ids) != set(manifest_ids):
        raise ValueError("source-yield and attempt04 manifest block IDs differ")


def validate_numeric_inputs(
    schedule: dict[str, Any], scenario_inputs: dict[str, Any]
) -> None:
    rows = schedule.get("candidate_block_records")
    if not isinstance(rows, list):
        raise TypeError("source-yield candidate_block_records must be a list")
    for row in rows:
        part_id = row.get("part_id", "unknown")
        require_finite_number(
            f"{part_id}.proposed_blank_stock_length_mm",
            row.get("proposed_blank_stock_length_mm"),
            positive=True,
        )
        section = row.get("proposed_blank_cross_section_mm")
        if not isinstance(section, list) or len(section) != 2:
            raise ValueError(
                f"{part_id}.proposed_blank_cross_section_mm must have two values"
            )
        for index, value in enumerate(section):
            require_finite_number(f"{part_id}.section[{index}]", value, positive=True)

    options = scenario_inputs.get("stock_length_options")
    if not isinstance(options, list) or not options:
        raise ValueError("stock_length_options must be a nonempty list")
    for index, option in enumerate(options):
        lengths = option.get("published_lengths_ft")
        if not isinstance(lengths, list) or not lengths:
            raise ValueError(
                f"stock_length_options[{index}] must include published lengths"
            )
        for value in lengths:
            require_finite_number(
                f"stock_length_options[{index}].published_lengths_ft",
                value,
                positive=True,
            )

    cut_losses = scenario_inputs.get("cut_loss_scenarios")
    if not isinstance(cut_losses, list) or not cut_losses:
        raise ValueError("cut_loss_scenarios must be a nonempty list")
    scenario_ids = []
    for index, row in enumerate(cut_losses):
        scenario_ids.append(row.get("scenario_id"))
        require_finite_number(
            f"cut_loss_scenarios[{index}].kerf_mm", row.get("kerf_mm"), nonnegative=True
        )
        require_finite_number(
            f"cut_loss_scenarios[{index}].end_trim_per_arithmetic_bin_mm",
            row.get("end_trim_per_arithmetic_bin_mm"),
            nonnegative=True,
        )
    if any(not isinstance(value, str) or not value for value in scenario_ids) or len(
        set(scenario_ids)
    ) != len(scenario_ids):
        raise ValueError("cut-loss scenarios must have unique nonempty IDs")


def checked_pack_arithmetic_group(
    blanks: list[dict[str, Any]],
    stock_length_mm: Any,
    kerf_mm: Any,
    end_trim_mm: Any,
) -> dict[str, Any]:
    stock_length = require_finite_number(
        "stock_length_mm", stock_length_mm, positive=True
    )
    kerf = require_finite_number("kerf_mm", kerf_mm, nonnegative=True)
    end_trim = require_finite_number("end_trim_mm", end_trim_mm, nonnegative=True)
    for row in blanks:
        require_finite_number(
            f"{row.get('part_id', 'blank')}.proposed_blank_length_mm",
            row.get("proposed_blank_length_mm"),
            positive=True,
        )
        section = row.get("proposed_blank_cross_section_mm")
        if not isinstance(section, list) or len(section) != 2:
            raise ValueError("blank section must contain two values")
        for index, value in enumerate(section):
            require_finite_number(f"blank section[{index}]", value, positive=True)
    if not blanks:
        raise ValueError("packing requires at least one blank")
    arithmetic = importlib.import_module(
        "scripts.build_current_timber_cut_yield_scenario_attempt01"
    )
    return arithmetic.pack_arithmetic_group(blanks, stock_length, kerf, end_trim)


def expected_attempt01_verification(
    report: dict[str, Any], report_bytes: bytes
) -> dict[str, Any]:
    return {
        "schema": "wood_joint_current_timber_cut_yield_verification/v1",
        "source_pins_status": "PASS",
        "source_count": len(report["source_pins"]),
        "source_pins": report["source_pins"],
        "scenario_inputs_sha256": report["scenario_inputs_sha256"],
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "scenario_count": report["scenario_result_count"],
        "blank_count": report["inventory_reconciliation"]["count"],
        "physical_or_purchase_claims": False,
    }


def validate_attempt01_verification(
    report: dict[str, Any], report_bytes: bytes, verification: dict[str, Any]
) -> None:
    expected = expected_attempt01_verification(report, report_bytes)
    if verification != expected:
        raise ValueError(
            "attempt01 verification.json differs from its complete expected record"
        )


def _load_pinned_sources(
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    packet = root / PACKET_REL
    pins = _read_json(packet / "source-pins.json")
    rows = pins.get("sources")
    if pins.get(
        "schema"
    ) != "wood_joint_timber_cut_yield_attempt02_source_pins/v1" or not isinstance(
        rows, list
    ):
        raise ValueError("attempt02 source-pins.json has an unsupported schema")
    pin_by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        path, digest = row.get("path"), row.get("sha256")
        if (
            not isinstance(path, str)
            or not isinstance(digest, str)
            or path in pin_by_path
        ):
            raise ValueError("attempt02 pins require unique path and SHA-256 entries")
        pin_by_path[path] = row
    if set(pin_by_path) != set(SOURCE_ROLES):
        raise ValueError(
            "attempt02 source paths differ from its bounded source contract"
        )

    values: dict[str, Any] = {}
    checked: list[dict[str, str]] = []
    for rel_path, role in SOURCE_ROLES.items():
        content = (root / rel_path).read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        expected = pin_by_path[rel_path]["sha256"]
        if actual != expected:
            raise ValueError(
                f"source hash drift for {rel_path}: expected {expected}, got {actual}"
            )
        checked.append({"path": rel_path, "sha256": actual})
        if role in {
            "block_schedule",
            "manifest",
            "grade",
            "cost_status",
            "revision",
            "selected_authority",
            "attempt01_source_pins",
            "attempt01_scenario_inputs",
            "attempt01_report",
            "attempt01_verification",
        }:
            try:
                values[role] = json.loads(content, parse_constant=_reject_json_constant)
            except json.JSONDecodeError as exc:
                raise ValueError(f"pinned JSON source is invalid: {rel_path}") from exc
        else:
            values[role] = content.decode("utf-8")
    return values, checked


def authenticate_attempt01(
    sources: dict[str, Any], checked: list[dict[str, str]], root: Path = ROOT
) -> dict[str, Any]:
    arithmetic = importlib.import_module(
        "scripts.build_current_timber_cut_yield_scenario_attempt01"
    )
    schedule = sources["block_schedule"]
    revision = sources["revision"]
    manifest = sources["manifest"]
    attempt01_report = sources["attempt01_report"]
    attempt01_verification = sources["attempt01_verification"]

    validate_revision_identity(schedule, revision)
    validate_numeric_inputs(schedule, sources["attempt01_scenario_inputs"])
    validate_manifest_block_ids(
        schedule.get("candidate_block_records", []),
        manifest.get("candidate_blocks", []),
    )

    v1_source_pins = sources["attempt01_source_pins"].get("sources", [])
    v1_pin_by_path = {row.get("path"): row.get("sha256") for row in v1_source_pins}
    v2_pin_by_path = {row["path"]: row["sha256"] for row in checked}
    for path, role in arithmetic.SOURCE_ROLES.items():
        if v1_pin_by_path.get(path) != v2_pin_by_path.get(path):
            raise ValueError(
                f"attempt01 source pin does not match the authenticated attempt02 input: {path}"
            )

    review_text = sources["attempt01_review"]
    for role in REVIEWED_ATTEMPT01_ROLES:
        path = next(
            path
            for path, candidate_role in SOURCE_ROLES.items()
            if candidate_role == role
        )
        digest = v2_pin_by_path[path]
        if digest not in review_text:
            raise ValueError(
                f"independent review does not authenticate attempt01 artifact: {path}"
            )

    report_path = root / ATTEMPT01_PACKET_REL / ATTEMPT01_REPORT_NAME
    report_bytes = report_path.read_bytes()
    validate_attempt01_verification(
        attempt01_report, report_bytes, attempt01_verification
    )
    reproduced_report = arithmetic.build_report(root)
    if reproduced_report != attempt01_report:
        raise ValueError(
            "attempt01 report does not reproduce from its authenticated source packet"
        )
    if attempt01_report.get("scenario_result_count") != 30:
        raise ValueError(
            "attempt01 arithmetic report no longer contains the reviewed 30 scenarios"
        )
    return {
        "review_path": next(
            path for path, role in SOURCE_ROLES.items() if role == "attempt01_review"
        ),
        "review_sha256": v2_pin_by_path[
            next(
                path
                for path, role in SOURCE_ROLES.items()
                if role == "attempt01_review"
            )
        ],
        "reviewed_artifact_count": len(REVIEWED_ATTEMPT01_ROLES),
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "verification_rechecked_in_full": True,
        "arithmetic_rerun_scenario_count": reproduced_report["scenario_result_count"],
        "arithmetic_matches_attempt01_report": reproduced_report["scenarios"]
        == attempt01_report["scenarios"],
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    sources, checked = _load_pinned_sources(root)
    auth = authenticate_attempt01(sources, checked, root)
    attempt01_report = sources["attempt01_report"]
    return {
        "schema": "wood_joint_current_timber_cut_yield_scenarios_attempt02/v1",
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_authority_preserved": EXPECTED_SELECTED_AUTHORITY,
        "geometry_revision_id": REVISION_ID,
        "source_pins": checked,
        "attempt01_authentication": auth,
        "validation_closure": {
            "source_yield_and_revision_source_ids_checked": True,
            "complete_attempt01_verification_compared": True,
            "finite_numeric_inputs_required": True,
            "attempt04_manifest_exactly_24_unique_ids_required": True,
        },
        "scenario_result_count": attempt01_report["scenario_result_count"],
        "inventory_reconciliation": attempt01_report["inventory_reconciliation"],
        "packing_policy": attempt01_report["packing_policy"],
        "scenarios": attempt01_report["scenarios"],
        "claim_boundary": attempt01_report["claim_boundary"],
    }


def expected_verification(
    report: dict[str, Any], report_bytes: bytes
) -> dict[str, Any]:
    return {
        "schema": "wood_joint_current_timber_cut_yield_attempt02_verification/v1",
        "source_pins_status": "PASS",
        "source_count": len(report["source_pins"]),
        "source_pins": report["source_pins"],
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "scenario_count": report["scenario_result_count"],
        "blank_count": report["inventory_reconciliation"]["count"],
        "attempt01_review_sha256": report["attempt01_authentication"]["review_sha256"],
        "attempt01_arithmetic_reproduced": report["attempt01_authentication"][
            "arithmetic_matches_attempt01_report"
        ],
        "physical_or_purchase_claims": False,
    }


def validate_verification(
    report: dict[str, Any], report_bytes: bytes, verification: dict[str, Any]
) -> None:
    if verification != expected_verification(report, report_bytes):
        raise ValueError(
            "attempt02 verification.json differs from its complete expected record"
        )


def write_packet(root: Path = ROOT) -> dict[str, Any]:
    packet = root / PACKET_REL
    report = build_report(root)
    report_bytes = _json_bytes(report)
    (packet / REPORT_NAME).write_bytes(report_bytes)
    verification = expected_verification(report, report_bytes)
    (packet / VERIFICATION_NAME).write_bytes(_json_bytes(verification))
    return verification


def verify_packet(root: Path = ROOT) -> dict[str, Any]:
    packet = root / PACKET_REL
    report_path = packet / REPORT_NAME
    verification_path = packet / VERIFICATION_NAME
    expected_report = build_report(root)
    actual_report = _read_json(report_path)
    if actual_report != expected_report:
        raise ValueError(
            f"{REPORT_NAME} differs from authenticated attempt01 arithmetic and attempt02 validation"
        )
    report_bytes = report_path.read_bytes()
    verification = _read_json(verification_path)
    validate_verification(actual_report, report_bytes, verification)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--write",
        action="store_true",
        help="write attempt02 report and full verification",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="verify pins, attempt01 authentication, and attempt02 outputs",
    )
    args = parser.parse_args()
    try:
        result = write_packet() if args.write else verify_packet()
        action_name = "WROTE" if args.write else "PASS"
        print(
            f"{action_name}: {result['source_count']} source pins; "
            f"{result['scenario_count']} scenarios; {result['blank_count']} blanks; "
            "attempt01 review and arithmetic authenticated"
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
