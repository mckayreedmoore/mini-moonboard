#!/usr/bin/env python3
"""Post-run checks for the one isolated free-C3D20 STI17 coupon.

This checker reads coupon output only when the parent has completed the single
reserved native run. It has not been executed.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE_DIR = HERE / "sti17-free-c3d20-coupon-freeze-attempt01"
COUPON_DIR = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01"
)
EXPECTED_FREEZE_SCOPE = "free unit C3D20 native MATRIXSTORAGE known-answer export only"
EXPECTED_IMAGE_ID_BASE = (
    "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
)
EXPECTED_BINARY_PATH = "/usr/local/bin/ccx-upstream-2.23-sti17"
EXPECTED_LEDGER_REL = "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
RESULT_NAME = "coupon-result.json"
EXPECTED_STI_PLACES = 16
EXPECTED_MAS_PLACES = 13
EXPECTED_TIMEOUT_CONTROL = {
    "path": "/usr/bin/timeout",
    "sha256": "4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08",
}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def check_format(path: Path, decimal_places: int) -> dict[str, object]:
    value_pattern = re.compile(
        rf"[+-]?\d+\.\d{{{decimal_places}}}e[+-]\d+", re.IGNORECASE
    )
    rows = 0
    for line_number, raw in enumerate(path.read_text().splitlines(), 1):
        fields = raw.split()
        require(
            len(fields) == 3,
            f"{path.name}:{line_number}: expected one row, column, value triplet",
        )
        require(
            fields[0].isdigit() and fields[1].isdigit(),
            f"{path.name}:{line_number}: invalid integer matrix index",
        )
        require(
            value_pattern.fullmatch(fields[2]) is not None,
            f"{path.name}:{line_number}: value does not have {decimal_places} decimal places",
        )
        value = float(fields[2])
        require(
            math.isfinite(value), f"{path.name}:{line_number}: non-finite matrix value"
        )
        rows += 1
    require(rows > 0, f"{path.name} contains no matrix entries")
    return {"rows": rows, "decimal_places": decimal_places, "sha256": sha_file(path)}


def validate_sti17_profile(profile: dict) -> None:
    require(
        profile.get("version") == "2.23-sti17", "freeze does not bind the STI17 profile"
    )
    image_id = profile.get("image_id", "")
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is not None,
        "freeze has no immutable STI17 image ID",
    )
    require(
        image_id != EXPECTED_IMAGE_ID_BASE, "freeze points to the original 2.23 image"
    )
    require(
        profile.get("binary_path") == EXPECTED_BINARY_PATH,
        "freeze points to another STI17 binary path",
    )
    require(
        re.fullmatch(r"[0-9a-f]{64}", profile.get("binary_sha256", "")) is not None,
        "freeze has no exact STI17 binary hash",
    )
    require(
        profile.get("candidate_export_authorized") is False,
        "coupon profile incorrectly authorizes candidate export",
    )
    require(
        profile.get("mechanical_acceptance") is False,
        "coupon profile incorrectly claims mechanical acceptance",
    )


def validate_profile_binding(
    profile: dict, profile_file: Path, frozen_sources: dict
) -> str:
    require(profile_file.is_file(), "separate STI17 profile file is absent")
    relative = str(profile_file.resolve().relative_to(ROOT.resolve()))
    require(
        frozen_sources.get(relative) == sha_file(profile_file),
        "freeze does not bind the live STI17 profile source",
    )
    expected_profile = json.loads(profile_file.read_text())
    require(
        profile == expected_profile,
        "embedded freeze profile differs from the generated STI17 profile",
    )
    validate_sti17_profile(profile)
    return sha_file(profile_file)


def safe_result_path(attempt_directory: Path, output_path: Path) -> Path:
    directory = attempt_directory.resolve()
    output = output_path.absolute()
    require(
        output.parent.resolve() == directory,
        "coupon result must be written only inside the isolated attempt directory",
    )
    require(
        output.name == RESULT_NAME,
        "coupon result filename is reserved for the provenance receipt",
    )
    require(not output.is_symlink(), "coupon result path cannot be a symlink")
    protected_names = {
        "freeze.json",
        "model.inp",
        "model.json",
        "authorization.json",
        "execution.json",
        "model.dat",
        "native.stdout",
        "native.stderr",
    }
    require(
        output.name not in protected_names,
        "coupon result path aliases a frozen or native-run record",
    )
    require(not output.exists(), "coupon result already exists; do not overwrite it")
    output_canonical = output.resolve(strict=False)
    for protected in directory.rglob("*"):
        if protected.is_file() or protected.is_symlink():
            require(
                protected.resolve(strict=False) != output_canonical,
                "coupon result path aliases a protected source or run record",
            )
    return output


def load_bound_review(
    repository_root: Path, review_relative: object, expected_sha256: str
) -> dict:
    require(
        isinstance(review_relative, str) and review_relative,
        "authorization has no exact independent review path",
    )
    relative = Path(review_relative)
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "independent review path must be repository-relative",
    )
    root = repository_root.resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), "independent review path escapes the repository")
    require(
        path.is_file() and sha_file(path) == expected_sha256,
        "independent review changed since the parent authorized this freeze",
    )
    return json.loads(path.read_text())


def validate_runner_command(
    command: object,
    *,
    attempt_directory: Path,
    run_id: str,
    profile: dict,
) -> None:
    require(
        isinstance(command, list) and all(isinstance(arg, str) for arg in command),
        "runner command is not an argument list",
    )
    expected = [
        "docker",
        "--context",
        "default",
        "run",
        "--rm",
        "--name",
        "moonboard-" + run_id.lower(),
        "--network=none",
        "--cpus=1",
        "--memory=2g",
        "--user",
        None,
        "-e",
        "OMP_NUM_THREADS=1",
        "--memory-swap=2g",
        "-v",
        f"{attempt_directory.resolve()}:/output",
        "-v",
        f"{attempt_directory.resolve() / 'model.inp'}:/output/model.inp:ro",
        "-w",
        "/output",
        profile["image_id"],
        "/usr/bin/timeout",
        "--signal=KILL",
        "60s",
        profile["binary_path"],
        "-i",
        "model",
    ]
    require(len(command) == len(expected), "runner command has unexpected arguments")
    user = command[11]
    require(
        re.fullmatch(r"\d+:\d+", user) is not None,
        "runner command has an invalid container user",
    )
    expected[11] = user
    require(
        command == expected,
        "runner command differs from the pinned STI17 one-slot invocation",
    )


def validate_ledger_row(
    ledger: dict,
    *,
    run_id: str,
    scope: str,
    attempt_relative: str,
    freeze_digest: str,
    authorization_sha256: str,
    execution_sha256: str,
) -> dict:
    runs = ledger.get("runs")
    require(isinstance(runs, list), "native ledger has no run list")
    matches = [
        row for row in runs if isinstance(row, dict) and row.get("run_id") == run_id
    ]
    require(
        len(matches) == 1,
        "native ledger must contain exactly one row for this never-reused run ID",
    )
    row = matches[0]
    require(
        row.get("scope") == scope
        and row.get("attempt_directory") == attempt_relative
        and row.get("input_freeze_sha256") == freeze_digest,
        "native ledger row does not bind this scope, attempt and exact freeze",
    )
    require(
        row.get("max_launches") == 1
        and row.get("launches_consumed") == 1
        and row.get("state") == "consumed_terminal",
        "native ledger row is not the single terminal launch",
    )
    require(
        row.get("parent_readiness") is True
        and row.get("native_execution_authorized") is True,
        "native ledger row lacks parent execution authorization",
    )
    require(
        row.get("authorization_sha256") == authorization_sha256
        and row.get("execution_record_sha256") == execution_sha256,
        "native ledger record hashes do not match authorization/execution files",
    )
    return row


def validate_runner_records(
    freeze_digest: str,
    scope: str,
    attempt_directory: Path,
    attempt_relative: str,
    authorization: dict,
    execution: dict,
    review: dict,
    profile: dict,
    ledger: dict,
    authorization_sha256: str,
    execution_sha256: str,
) -> tuple[str, dict]:
    run_id = authorization.get("run_id")
    require(
        isinstance(run_id, str)
        and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}", run_id) is not None,
        "runner authorization has an invalid run ID",
    )
    require(
        authorization.get("scope") == scope
        and authorization.get("input_freeze_sha256") == freeze_digest
        and authorization.get("parent_readiness") is True
        and authorization.get("native_execution_authorized") is True
        and authorization.get("mechanical_acceptance") is False,
        "runner authorization does not bind this scoped freeze",
    )
    require(
        execution.get("native_solve_executed") is True
        and execution.get("run_id") == run_id
        and execution.get("container_confirmed_terminal") is True
        and execution.get("returncode") == 0
        and execution.get("mechanical_acceptance") is False,
        "coupon execution did not finish once with a successful terminal record",
    )
    authorization_command = authorization.get("command")
    execution_command = execution.get("command")
    require(
        authorization_command == execution_command,
        "authorization and execution commands differ",
    )
    require(
        authorization.get("timeout_control") == EXPECTED_TIMEOUT_CONTROL
        and execution.get("timeout_control") == EXPECTED_TIMEOUT_CONTROL,
        "runner records do not bind the qualified absolute timeout utility",
    )
    validate_sti17_profile(profile)
    validate_runner_command(
        authorization_command,
        attempt_directory=attempt_directory,
        run_id=run_id,
        profile=profile,
    )
    require(
        review.get("input_freeze_sha256") == freeze_digest
        and review.get("ready_for_scoped_native_run") is True,
        "independent review does not approve this exact coupon freeze",
    )
    ledger_row = validate_ledger_row(
        ledger,
        run_id=run_id,
        scope=scope,
        attempt_relative=attempt_relative,
        freeze_digest=freeze_digest,
        authorization_sha256=authorization_sha256,
        execution_sha256=execution_sha256,
    )
    return run_id, ledger_row


def validate_recorded_outputs(execution: dict, observed_hashes: dict[str, str]) -> None:
    recorded = execution.get("outputs_sha256", {})
    for name, observed in observed_hashes.items():
        require(
            recorded.get(name) == observed,
            f"{name} raw output hash differs from the runner's execution record",
        )


def main() -> None:
    require(FREEZE_DIR.is_dir(), "prepared STI17 coupon freeze is absent")
    out_path = safe_result_path(FREEZE_DIR, FREEZE_DIR / RESULT_NAME)
    freeze_path = FREEZE_DIR / "freeze.json"
    packet = json.loads(freeze_path.read_text())
    require(
        packet.get("scope") == EXPECTED_FREEZE_SCOPE,
        "freeze scope is not the isolated free coupon",
    )
    profile = packet.get("solver_profile", {})
    profile_path = HERE / "solver-profile-sti17.json"
    profile_sha256 = validate_profile_binding(
        profile, profile_path, packet.get("source_sha256", {})
    )
    require(
        sha_file(FREEZE_DIR / "model.inp")
        == "e128a62f899c90965fd68be09a7362ed836a30ff6b1c3f1c6dc0581e118b79fe",
        "coupon deck is not the retained free C3D20 input",
    )

    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_reduced_native import verify

    freeze_digest = sha_file(freeze_path)
    verify(FREEZE_DIR)
    sys.path.insert(0, str(HERE))
    from launch_sti17_coupon import verify_launcher_bindings

    verify_launcher_bindings(FREEZE_DIR)

    authorization_path = FREEZE_DIR / "authorization.json"
    execution_path = FREEZE_DIR / "execution.json"
    require(
        authorization_path.is_file() and execution_path.is_file(),
        "the parent runner has no terminal execution record",
    )
    authorization = json.loads(authorization_path.read_text())
    execution = json.loads(execution_path.read_text())
    authorization_sha256 = sha_file(authorization_path)
    execution_sha256 = sha_file(execution_path)
    review = load_bound_review(
        ROOT,
        authorization.get("independent_review"),
        authorization.get("independent_review_sha256"),
    )
    ledger_path = ROOT / EXPECTED_LEDGER_REL
    require(ledger_path.is_file(), "native run ledger is absent")
    ledger_bytes = ledger_path.read_bytes()
    ledger = json.loads(ledger_bytes)
    attempt_relative = str(FREEZE_DIR.resolve().relative_to(ROOT.resolve()))
    run_id, ledger_row = validate_runner_records(
        freeze_digest,
        EXPECTED_FREEZE_SCOPE,
        FREEZE_DIR,
        attempt_relative,
        authorization,
        execution,
        review,
        profile,
        ledger,
        authorization_sha256,
        execution_sha256,
    )

    base = FREEZE_DIR / "model"
    sti = check_format(base.with_suffix(".sti"), EXPECTED_STI_PLACES)
    mas = check_format(base.with_suffix(".mas"), EXPECTED_MAS_PLACES)
    dof_path = base.with_suffix(".dof")
    require(dof_path.is_file(), "native coupon did not emit model.dof")
    dof_sha = sha_file(dof_path)
    validate_recorded_outputs(
        execution,
        {
            "model.sti": sti["sha256"],
            "model.mas": mas["sha256"],
            "model.dof": dof_sha,
        },
    )

    sys.path.insert(0, str(COUPON_DIR))
    import matrix_export_oracle

    oracle = matrix_export_oracle.check(base)
    require(
        oracle.get("status") == "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE",
        "independent free C3D20 matrix oracle failed",
    )
    require(
        oracle.get("dof_count") == 60
        and oracle.get("rigid_body_mode_count") == 6
        and oracle.get("negative_eigenvalue_count_below_tolerance") == 0,
        "coupon map or rigid-mode checks failed",
    )
    require(
        oracle.get("stiffness_triplet_pairs", 0) > 0
        and oracle.get("mass_triplet_pairs", 0) > 0,
        "coupon matrices have no unique triplet pairs",
    )

    result = {
        "schema": "ccx223_sti17_coupon_result/v1",
        "status": "PASS_STI17_FREE_C3D20_FORMAT_AND_ORACLE_ONLY",
        "freeze_sha256": freeze_digest,
        "solver_profile_sha256": profile_sha256,
        "launcher_source_sha256": sha_file(HERE / "launch_sti17_coupon.py"),
        "image_id": profile["image_id"],
        "binary_path": profile["binary_path"],
        "binary_sha256": profile["binary_sha256"],
        "run_id": run_id,
        "attempt_directory": attempt_relative,
        "scope": EXPECTED_FREEZE_SCOPE,
        "authorization_sha256": authorization_sha256,
        "native_execution_sha256": execution_sha256,
        "ledger_sha256": sha_bytes(ledger_bytes),
        "ledger_row": ledger_row,
        "launch_command": authorization["command"],
        "sti": sti,
        "mas": mas,
        "dof_sha256": dof_sha,
        "oracle": oracle,
        "candidate_matrix_exported": False,
        "candidate_cause_claimed": False,
        "mechanical_acceptance": False,
    }
    with out_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
