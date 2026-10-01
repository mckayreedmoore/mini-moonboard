#!/usr/bin/env python3
"""Audit one parent-run exact two-tie sensitivity packet; never launches a solver."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
VARIANT_DIR = SERIES / "current-a12-rear-bg001-seat-stiffness-variant-attempt01"
CONTRACT_PATH = HERE / "readiness-contract.json"
SNAPSHOT_MANIFEST_PATH = HERE / "source-snapshot-manifest.json"
RUN_ID = "a12rear-bg001-stiffness-sensitivity-attempt01"
IMAGE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY_SHA256 = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"


class RunAuditError(ValueError):
    """Frozen input, terminal execution, or physical response does not match."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RunAuditError(f"Expected an object in {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunAuditError(message)


def import_core(path: Path):
    spec = importlib.util.spec_from_file_location("pinned_a12_bg001_sensitivity_response_core", path)
    if spec is None or spec.loader is None:
        raise RunAuditError("Cannot import the pinned sensitivity response core")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(run_directory: Path, output_path: Path | None = None) -> dict[str, Any]:
    run_directory = run_directory.resolve()
    require(run_directory.is_relative_to(ROOT), "Run directory must remain inside the repository")
    require(CONTRACT_PATH.is_file(), "Missing readiness contract")
    contract = load_json(CONTRACT_PATH)
    source_manifest = load_json(SNAPSHOT_MANIFEST_PATH)
    require(contract.get("schema") == "a12_rear_bg001_stiffness_sensitivity_parent_readiness_inputs/v1",
            "Unsupported readiness contract")
    require(contract.get("parent_native_readiness") is False, "Input packet cannot grant native readiness")
    expected_audit_sha = contract.get("postrun", {}).get("fork_audit_script_sha256")
    require(expected_audit_sha == sha(Path(__file__)), "Post-run audit script differs from the contract pin")

    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_reduced_native import verify as verify_native_freeze

    try:
        freeze = verify_native_freeze(run_directory)
    except Exception as error:
        raise RunAuditError(f"Frozen source/input verification failed: {error}") from error
    require(freeze.get("schema") == "wood_joint_reduced_native_freeze/v1", "Unsupported native freeze schema")
    require(freeze.get("native_solve_executed") is False and freeze.get("mechanical_acceptance") is False,
            "Freeze metadata must remain input-only and non-accepting")
    require(freeze.get("candidate") == "compact-floor-flush-wood-joints-development",
            "Frozen candidate does not match the sensitivity lane")
    require(freeze.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1",
            "Frozen geometry revision changed")
    require(freeze.get("case_id") in (None, "a12-rear"), "Frozen case is not A12-rear")
    scope = str(freeze.get("scope", ""))
    require("A12-rear" in scope and "BG001" in scope and "sensitivity" in scope.lower(),
            "Freeze scope must identify the single A12-rear BG001 sensitivity")
    profile = freeze.get("solver_profile", {})
    require(profile.get("version") == "2.23" and profile.get("image_id") == IMAGE_ID,
            "Freeze does not bind the pinned CalculiX 2.23 image")
    require(profile.get("binary_sha256") == BINARY_SHA256, "Freeze solver binary pin changed")

    frozen_sources = freeze.get("source_sha256", {})
    manifest_copy = run_directory / "readiness-source-snapshot-manifest.json"
    require(manifest_copy.is_file() and sha(manifest_copy) == sha(SNAPSHOT_MANIFEST_PATH),
            "Run directory is missing the exact source-snapshot manifest")
    require(freeze.get("files_sha256", {}).get("readiness-source-snapshot-manifest.json") == sha(manifest_copy),
            "Freeze does not bind the source-snapshot manifest")
    snapshot_hashes = source_manifest.get("source_snapshots", {})
    require(snapshot_hashes == contract.get("frozen_source_snapshot_sha256"),
            "Readiness contract and source-snapshot manifest disagree")
    for relative, expected in snapshot_hashes.items():
        require(frozen_sources.get(relative) == expected,
                f"Freeze omits or changes the prepared method snapshot: {relative}")
        snapshot = run_directory / "sources" / relative
        require(snapshot.is_file() and sha(snapshot) == expected,
                f"Frozen method snapshot is missing or changed: {relative}")
    contract_hash = sha(CONTRACT_PATH)
    contract_snapshot_info = source_manifest.get("readiness_contract_snapshot", {})
    contract_relative = str(contract_snapshot_info.get("repository_relative_path", ""))
    require(contract_relative == str(CONTRACT_PATH.relative_to(ROOT)),
            "Source manifest readiness-contract path changed")
    require(contract_snapshot_info.get("sha256") == contract_hash,
            "Source manifest does not bind the readiness contract")
    require(frozen_sources.get(contract_relative) == contract_hash,
            "Freeze does not bind the readiness contract")
    contract_snapshot = run_directory / "sources" / contract_relative
    require(contract_snapshot.is_file() and sha(contract_snapshot) == contract_hash,
            "Frozen readiness-contract snapshot is missing or changed")

    model_path = run_directory / "model.json"
    deck_path = run_directory / "model.inp"
    data_path = run_directory / "model.dat"
    execution_path = run_directory / "execution.json"
    authorization_path = run_directory / "authorization.json"
    stdout_path = run_directory / "native.stdout"
    stderr_path = run_directory / "native.stderr"
    required = (model_path, deck_path, data_path, execution_path, authorization_path, stdout_path, stderr_path)
    require(all(path.is_file() for path in required), "Run is missing model, terminal output, or execution provenance")
    expected_files = {
        "model.json": contract["prepared_inputs"]["model_json_sha256"],
        "model.inp": contract["prepared_inputs"]["deck_sha256"],
    }
    for name, expected in expected_files.items():
        require(sha(run_directory / name) == expected, f"Frozen sensitivity {name} differs from prepared bytes")
        require(freeze.get("files_sha256", {}).get(name) == expected, f"Freeze does not bind exact {name}")

    execution = load_json(execution_path)
    authorization = load_json(authorization_path)
    require(execution.get("native_solve_executed") is True and execution.get("returncode") == 0,
            "Native execution is not a successful terminal run")
    require(execution.get("container_confirmed_terminal") is True, "Native container is not confirmed terminal")
    require(execution.get("mechanical_acceptance") is False, "Execution record cannot claim acceptance")
    require(execution.get("run_id") == RUN_ID, "Execution record belongs to a different run ID")
    freeze_sha = sha(run_directory / "freeze.json")
    require(authorization.get("run_id") == RUN_ID
            and authorization.get("input_freeze_sha256") == freeze_sha
            and authorization.get("parent_readiness") is True
            and authorization.get("native_execution_authorized") is True
            and authorization.get("mechanical_acceptance") is False,
            "Parent launch authorization does not bind this exact non-accepting freeze")
    review_rel = authorization.get("independent_review")
    require(isinstance(review_rel, str), "Launch authorization lacks its independent review path")
    review_path = (ROOT / review_rel).resolve()
    require(review_path == (run_directory / "parent-readiness-review.json").resolve(),
            "Independent review must be adjacent to this exact run")
    review = load_json(review_path)
    require(sha(review_path) == authorization.get("independent_review_sha256")
            and review.get("input_freeze_sha256") == freeze_sha
            and review.get("ready_for_scoped_native_run") is True
            and review.get("mechanical_acceptance") is False,
            "Independent parent review is stale or overclaims acceptance")
    require(authorization.get("owner_authority_sha256") == sha(ROOT / "AGENTS.md"),
            "Launch authorization does not bind the resumed owner-authority record")
    expected_command = [
        "docker", "--context", "default", "run", "--rm", "--name", "moonboard-" + RUN_ID.lower(),
        "--network=none", "--cpus=1", "--memory=4g", "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", "OMP_NUM_THREADS=1", "-v", f"{run_directory}:/output", "-w", "/output",
        IMAGE_ID, "timeout", "240s", profile["binary_path"], "-i", "model",
    ]
    require(execution.get("command") == expected_command and authorization.get("command") == expected_command,
            "Executed command differs from the one-run pinned 2.23/240-second/4-GiB scope")
    ledger_path = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
    ledger = load_json(ledger_path)
    ledger_rows = [row for row in ledger.get("runs", []) if row.get("run_id") == RUN_ID]
    require(len(ledger_rows) == 1, "Serialized native ledger lacks a unique sensitivity run record")
    ledger_row = ledger_rows[0]
    require(ledger_row.get("state") == "consumed_terminal"
            and ledger_row.get("max_launches") == 1
            and ledger_row.get("launches_consumed") == 1
            and ledger_row.get("input_freeze_sha256") == freeze_sha
            and ledger_row.get("execution_record_sha256") == sha(execution_path),
            "Serialized native ledger does not bind one terminal run of this freeze")
    output_hashes = execution.get("outputs_sha256", {})
    for name, path in (("model.dat", data_path), ("native.stdout", stdout_path), ("native.stderr", stderr_path)):
        require(output_hashes.get(name) == sha(path), f"Native execution output hash mismatch: {name}")
    error_pattern = re.compile(r"(?:\*ERROR|\*\*\s*ERROR|FATAL ERROR)", re.IGNORECASE)
    for path in (data_path, stdout_path, stderr_path):
        require(not error_pattern.search(path.read_text(errors="replace")), f"Native error marker found in {path.name}")

    core_path = VARIANT_DIR / "sensitivity_response_core.py"
    require(sha(core_path) == contract["source_hashes"]["response_core_fork"],
            "Pinned response-core fork changed")
    core = import_core(core_path)
    validator = core.load_sensitivity_input_validator()
    validated_contract = validator.validate_prepared_variant()
    record = load_json(model_path)
    data = data_path.read_text()
    deck = deck_path.read_text()
    report = core.audit_record_with_validated_contract(
        record, data, deck,
        validated_contract=validated_contract,
        model_path=model_path,
        deck_path=deck_path,
        contract_mode="approved_sensitivity_variant",
    )
    require(report.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY",
            "Sensitivity fork did not return its unchanged all-gates physical audit pass")
    require(report.get("sensitivity_input_contract_provenance", {}).get(
        "standard_711_case_context_validation_passed") is False,
            "Do not claim the standard 711 case-context validator")
    require(report.get("mechanical_acceptance") is False and report.get("joint_demand_accepted") is False,
            "Response audit cannot claim acceptance")
    report.update({
        "source_input_model_json_sha256": sha(model_path),
        "source_input_model_json_path": str(model_path),
        "source_input_deck_sha256": sha(deck_path),
        "source_input_deck_path": str(deck_path),
        "native_data_sha256": sha(data_path),
        "native_data_path": str(data_path),
        "case_context_path": None,
        "case_context_sha256": None,
        "standard_711_case_context_validation_passed": False,
        "terminal_execution_provenance": {
            "run_id": execution["run_id"],
            "freeze_path": str(run_directory / "freeze.json"),
            "freeze_sha256": freeze_sha,
            "execution_path": str(execution_path),
            "execution_sha256": sha(execution_path),
            "authorization_path": str(authorization_path),
            "authorization_sha256": sha(authorization_path),
            "independent_review_path": str(review_path),
            "independent_review_sha256": sha(review_path),
            "serialized_ledger_path": str(ledger_path),
            "serialized_ledger_row": ledger_row,
            "returncode": 0,
            "container_confirmed_terminal": True,
            "native_output_hashes_match": True,
            "solver_error_markers_absent": True,
        },
        "campaign_scope": contract["campaign_scope"],
        "sensitivity_mask_provenance": {
            "status": "PROVISIONAL_COPIED_MASK_NOT_ADOPTED",
            "selected_cells": 25,
            "inactive_cells": 75,
            "source_screen_path": contract["floor_mask"]["screen_path"],
            "source_screen_sha256": contract["floor_mask"]["screen_sha256"],
            "source_screen_status": contract["floor_mask"]["screen_status"],
            "strict_native_complementarity_rechecked_every_increment": report.get("selected_floor_complementarity_passed") is True,
            "standard_711_case_context_validation_passed": False,
            "floor_branch_scope": "One monotone zero-gap reference branch only; no mask iteration, physical acceptance, recontact or uniqueness claim.",
        },
        "sensitivity_interpretation": {
            "type": "single conditional response sensitivity point",
            "variant_stiffness_n_per_mm": 2401.714359616974,
            "baseline_stiffness_n_per_mm": 4670.054188242363,
            "physical_or_statistical_stiffness_bound_claimed": False,
            "baseline_response_forces_reused_as_variant_demands": False,
            "six_case_scope_satisfied_by_this_run": False,
        },
        "postprocessor_source_sha256": sha(Path(__file__)),
    })
    output_path = (output_path or (run_directory / "response.json")).resolve()
    require(output_path == (run_directory / "response.json").resolve(),
            "The audited response must be written beside its frozen native run")
    output_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.run_directory, args.output)
    print(json.dumps({"status": report["status"], "increment_count": len(report["increments"]),
                      "selected_floor_complementarity_passed": report["selected_floor_complementarity_passed"],
                      "raw_body_and_global_balance_passed": report["raw_body_and_global_balance_passed"],
                      "rounding_interval_body_and_global_balance_passed": report["rounding_interval_body_and_global_balance_passed"],
                      "mechanical_acceptance": False}, indent=2))


if __name__ == "__main__":
    main()
