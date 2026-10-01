#!/usr/bin/env python3
"""Run the frozen attempt09 exact-touch output-capture coupon once, with caps."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FREEZE_PATH = HERE / "input-freeze.json"
READINESS_PATH = HERE / "readiness.json"
OUTPUT = HERE / "output"
IMAGE = "sha256:9040d55065a2dd78790b4c2af1564915d29b968d1fc236fa490ada03e0491e1e"
CONTAINER = "wj-ccxcap-attempt09-touch-attempt02"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def root_file(relative: str) -> Path:
    return ROOT / relative


def check_hash(label: str, path: Path, expected: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing frozen input {label}: {path}")
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"frozen input hash mismatch for {label}: {actual} != {expected}"
        )


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
    authorization_path = HERE / "authorization.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    ledger_path = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    freeze_sha = sha256(FREEZE_PATH)
    authorization_sha = sha256(authorization_path)
    readiness_sha = sha256(READINESS_PATH)
    if readiness.get("status") != "READY_FOR_ONE_SERIALIZED_ATTEMPT09_METHOD_COUPON_RUN":
        raise RuntimeError("parent readiness is not affirmative")
    if freeze.get("run_id") != authorization.get("run_id"):
        raise RuntimeError("run-specific authorization has a different run ID")
    if authorization.get("input_freeze_sha256") != freeze_sha:
        raise RuntimeError("run-specific authorization does not bind the exact freeze")
    if authorization.get("owner_authority_sha256") != freeze["authority_and_review"]["agents_md_sha256"]:
        raise RuntimeError("authorization does not bind the owner-level authorization")
    if authorization.get("native_execution_authorized") is not True or authorization.get("current_joint_run") is not False:
        raise RuntimeError("authorization is not bounded to this method-only coupon")
    if authorization.get("case_count") != 1 or authorization.get("fabrication_or_physical_activity") is not False:
        raise RuntimeError("authorization scope is not exactly one method coupon")
    if readiness.get("authorization_sha256") != authorization_sha:
        raise RuntimeError("readiness does not bind the run-specific authorization")
    if readiness.get("input_freeze_sha256") != freeze_sha:
        raise RuntimeError("readiness does not bind this input freeze")
    if readiness.get("ledger_run_id") != freeze["run_id"]:
        raise RuntimeError("readiness run ID differs from this freeze")
    ledger_rows = [row for row in ledger.get("runs", []) if row.get("run_id") == freeze["run_id"]]
    if len(ledger_rows) != 1:
        raise RuntimeError("parent ledger does not contain exactly one reservation for this run ID")
    reservation = ledger_rows[0]
    if (reservation.get("state") != "reserved_consumed" or reservation.get("launches_consumed") != 1
            or reservation.get("input_freeze_sha256") != freeze_sha
            or reservation.get("authorization_sha256") != authorization_sha
            or reservation.get("readiness_sha256") != readiness_sha
            or reservation.get("parent_readiness") is not True
            or reservation.get("native_execution_authorized") is not True):
        raise RuntimeError("parent run ledger reservation does not match readiness/authorization/freeze")
    if ledger.get("slot", {}).get("state") != "reserved" or ledger.get("slot", {}).get("active_run_id") != freeze["run_id"]:
        raise RuntimeError("parent serialized native slot is not reserved for this run")
    if readiness.get("input_freeze_sha256") != freeze_sha:
        raise RuntimeError("readiness does not bind the current input freeze")
    if readiness.get("runner_sha256") != sha256(HERE / "run.py"):
        raise RuntimeError("readiness does not bind this runner")
    if readiness.get("verifier_sha256") != sha256(HERE / "verify.py"):
        raise RuntimeError("readiness does not bind this verifier")
    review_path = root_file(readiness["independent_pre_run_review_path"])
    check_hash("independent pre-run review", review_path, readiness["independent_pre_run_review_sha256"])
    if readiness.get("independent_pre_run_review_status") != "PASS_BOUNDED_METHOD_COUPON_PREFLIGHT":
        raise RuntimeError("independent pre-run review is not affirmative")
    if authorization.get("independent_pre_run_review_sha256") != readiness["independent_pre_run_review_sha256"]:
        raise RuntimeError("run-specific authorization does not bind the independent pre-run review")
    if readiness.get("parent_review_sha256") != freeze["authority_and_review"]["attempt09_parent_review_sha256"]:
        raise RuntimeError("readiness and input freeze disagree on source review")
    if readiness.get("build_review_sha256") != freeze["authority_and_review"]["build_review_sha256"]:
        raise RuntimeError("readiness and input freeze disagree on build review")
    if (
        readiness.get("current_joint_run") is not False
        or readiness.get("native_case_count") != 1
    ):
        raise RuntimeError("readiness scope is not one method coupon")
    if freeze["run_limits"]["cases"] != 1 or freeze["input"]["include_closure"] != []:
        raise RuntimeError("unexpected case count or unbound include closure")
    if freeze["candidate_revision_context"]["geometry_mutated"] is not False:
        raise RuntimeError("geometry mutation is outside this method coupon")

    source = HERE / freeze["input"]["path"]
    check_hash("coupon input", source, freeze["input"]["sha256"])
    for relative, digest in {
        "AGENTS.md": freeze["authority_and_review"]["agents_md_sha256"],
        freeze["authority_and_review"]["attempt09_parent_review_path"]: freeze[
            "authority_and_review"
        ]["attempt09_parent_review_sha256"],
        freeze["authority_and_review"]["attempt09_source_pins_path"]: freeze[
            "authority_and_review"
        ]["attempt09_source_pins_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt09-build-attempt01/context/source.tar.bz2": freeze[
            "solver"
        ]["source_archive_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt09-build-attempt01/context/capture.patch": freeze[
            "solver"
        ]["patch_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt09-build-attempt01/output/build-manifest.json": freeze[
            "solver"
        ]["build_manifest_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt09-build-attempt01/output/ccx-bounded-contact-capture-2.23-attempt09-build01": freeze[
            "solver"
        ]["binary_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt09/capture-contract.json": freeze[
            "solver"
        ]["capture_contract_sha256"],
        freeze["authority_and_review"]["build_review_path"]: freeze["authority_and_review"]["build_review_sha256"],
        freeze["solver"]["build_execution_path"]: freeze["solver"]["build_execution_sha256"],
        freeze["solver"]["docker_build_log_path"]: freeze["solver"]["docker_build_log_sha256"],
        freeze["known_answer"]["expected_path"]: freeze["known_answer"][
            "expected_sha256"
        ],
        freeze["reader_contract"]["reader_path"]: freeze["reader_contract"][
            "reader_sha256"
        ],
        freeze["solver"]["manual_path"]: freeze["solver"]["manual_sha256"],
        freeze["known_answer"]["work_fixture_result_path"]: freeze["known_answer"]["work_fixture_result_sha256"],
        freeze["known_answer"]["work_fixture_independent_review_path"]: freeze["known_answer"]["work_fixture_independent_review_sha256"],
        freeze["known_answer"]["work_fixture_verifier_path"]: freeze["known_answer"]["work_fixture_verifier_sha256"],
        freeze["known_answer"]["work_fixture_execution_path"]: freeze["known_answer"]["work_fixture_execution_sha256"],
    }.items():
        check_hash(relative, root_file(relative), digest)

    baseline_dir = root_file(freeze["known_answer"]["baseline_output_path"])
    for filename, digest in freeze["known_answer"]["baseline_output_sha256"].items():
        check_hash(f"pinned baseline {filename}", baseline_dir / filename, digest)

    for local, key in (
        (freeze["rosters"]["pair_roster_path"], "pair_roster_sha256"),
        (freeze["rosters"]["face_roster_path"], "face_roster_sha256"),
        (freeze["reader_contract"]["path"], "sha256"),
    ):
        digest = (
            freeze["rosters"][key]
            if key in freeze["rosters"]
            else freeze["reader_contract"][key]
        )
        check_hash(local, HERE / local, digest)

    reader_expectation = json.loads(
        (HERE / freeze["reader_contract"]["path"]).read_text(encoding="utf-8")
    )
    expected_bindings = reader_expectation["run_bindings"]
    frozen_bindings = {
        "input_sha256": freeze["input"]["sha256"],
        "include_closure_sha256": freeze["input"]["include_closure_sha256"],
        "source_archive_sha256": freeze["solver"]["source_archive_sha256"],
        "patch_sha256": freeze["solver"]["patch_sha256"],
        "binary_sha256": freeze["solver"]["binary_sha256"],
        "pair_roster_sha256": freeze["rosters"]["pair_roster_sha256"],
        "face_roster_sha256": freeze["rosters"]["face_roster_sha256"],
    }
    if expected_bindings != frozen_bindings:
        raise RuntimeError(
            "reader contract provenance bindings differ from the full input freeze"
        )

    if freeze["solver"]["image_id"] != IMAGE:
        raise RuntimeError("runner image ID differs from the exact input freeze")
    image_result = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    if image_result.stdout.strip() != IMAGE:
        raise RuntimeError(f"local image id mismatch: {image_result.stdout.strip()!r}")
    running = subprocess.run(
        ["docker", "ps", "--format", "{{.Image}}\t{{.Names}}\t{{.Command}}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.splitlines()
    if any(
        any(term in line.lower() for term in ("ccx", "calculix")) for line in running
    ):
        raise RuntimeError(
            "another visible CalculiX container is running; serialized slot is occupied"
        )
    processes = subprocess.run(
        ["ps", "-eo", "comm="],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.splitlines()
    if any(
        name.strip().lower() in {"ccx", "calculix", "ccx-bounded-contact-capture-2.23"}
        for name in processes
    ):
        raise RuntimeError(
            "another visible CalculiX process is running; serialized slot is occupied"
        )
    existing = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.splitlines()
    if CONTAINER in existing:
        raise RuntimeError(
            "unique container name already exists; refusing to overwrite prior run"
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    if any(OUTPUT.iterdir()):
        raise RuntimeError(
            "output directory is not empty; refusing to overwrite prior evidence"
        )
    shutil.copyfile(source, OUTPUT / "coupon.inp")
    check_hash("runtime coupon copy", OUTPUT / "coupon.inp", freeze["input"]["sha256"])

    bindings = expected_bindings
    env = {
        "OMP_NUM_THREADS": "1",
        "CCX_NPROC_EQUATION_SOLVER": "1",
        "CCX_CONTACT_CAPTURE_PATH": "/work/capture.tsv",
        "CCX_CAPTURE_INPUT_SHA256": bindings["input_sha256"],
        "CCX_CAPTURE_INCLUDE_SHA256": bindings["include_closure_sha256"],
        "CCX_CAPTURE_SOURCE_SHA256": bindings["source_archive_sha256"],
        "CCX_CAPTURE_PATCH_SHA256": bindings["patch_sha256"],
        "CCX_CAPTURE_BINARY_SHA256": bindings["binary_sha256"],
        "CCX_CAPTURE_PAIR_SHA256": bindings["pair_roster_sha256"],
        "CCX_CAPTURE_FACE_SHA256": bindings["face_roster_sha256"],
        "CCX_CAPTURE_EXPECTED_TIES": str(reader_expectation["tie_count"]),
        "CCX_CAPTURE_EXPECTED_FACES": str(
            sum(reader_expectation["face_count_by_tie"].values())
        ),
    }
    command = [
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--name",
        CONTAINER,
        "--network",
        "none",
        "--cpus",
        "1",
        "--memory",
        str(freeze["run_limits"]["memory_bytes"]),
        "--memory-swap",
        str(freeze["run_limits"]["memory_plus_swap_bytes"]),
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--mount",
        f"type=bind,src={OUTPUT.resolve()},dst=/work",
        "--workdir",
        "/work",
    ]
    for key, value in env.items():
        command.extend(["--env", f"{key}={value}"])
    command.extend([IMAGE, freeze["solver"]["binary_path_in_image"], "-i", "coupon"])

    started_at = utc_now()
    started = time.monotonic()
    timeout = freeze["run_limits"]["wall_seconds"]
    timed_out = False
    try:
        proc = subprocess.run(
            command, capture_output=True, timeout=timeout, check=False
        )
        stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        subprocess.run(
            ["docker", "kill", CONTAINER], capture_output=True, timeout=10, check=False
        )
        returncode = 124
    elapsed = time.monotonic() - started
    (OUTPUT / "solver.stdout").write_bytes(stdout)
    (OUTPUT / "solver.stderr").write_bytes(stderr)
    file_sizes = {p.name: p.stat().st_size for p in OUTPUT.iterdir() if p.is_file()}
    total_size = sum(file_sizes.values())
    max_log = freeze["run_limits"]["stdout_or_stderr_bytes"]
    max_total = freeze["run_limits"]["total_output_bytes"]
    capture_size = (
        (OUTPUT / "capture.tsv").stat().st_size
        if (OUTPUT / "capture.tsv").exists()
        else 0
    )
    max_capture = freeze["run_limits"]["capture_bytes"]
    capture_size_ok = capture_size <= max_capture
    size_ok = (
        len(stdout) <= max_log
        and len(stderr) <= max_log
        and total_size <= max_total
        and capture_size_ok
    )
    execution = {
        "schema": "ccx223_attempt09_contact_capture_coupon_execution/v1",
        "run_id": freeze["run_id"],
        "authorization_sha256": authorization_sha,
        "ledger_reservation_state_before_launch": reservation["state"],
        "status": "completed"
        if returncode == 0 and not timed_out and size_ok
        else "failed",
        "case": "exact_touch_output_capture_coupon",
        "scope": "method coupon only; current_joint_run=false",
        "started_at": started_at,
        "ended_at": utc_now(),
        "elapsed_seconds": elapsed,
        "command": command,
        "container_name": CONTAINER,
        "image_id": IMAGE,
        "input_freeze_sha256": freeze_sha,
        "readiness_sha256": readiness_sha,
        "native_solver_case_run": True,
        "current_joint_run": False,
        "timed_out": timed_out,
        "docker_cli_exit_code": returncode,
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "output_bytes_by_file": file_sizes,
        "total_output_bytes": total_size,
        "capture_bytes": capture_size,
        "capture_byte_cap": max_capture,
        "capture_cap_pass": capture_size_ok,
        "output_caps_pass": size_ok,
        "limits": freeze["run_limits"],
        "output_sha256": {p.name: sha256(p) for p in OUTPUT.iterdir() if p.is_file()},
    }
    (OUTPUT / "execution.json").write_text(
        json.dumps(execution, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": execution["status"],
                "returncode": returncode,
                "elapsed_seconds": elapsed,
                "total_output_bytes": total_size,
                "execution": str((OUTPUT / "execution.json").relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0 if execution["status"] == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - fail closed with a concise parent-run diagnostic
        print(f"parent-run preflight/error: {exc}", file=sys.stderr)
        raise SystemExit(2)
