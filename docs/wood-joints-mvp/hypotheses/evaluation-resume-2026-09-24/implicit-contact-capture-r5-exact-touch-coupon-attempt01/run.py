#!/usr/bin/env python3
"""Run the frozen r5 exact-touch output-capture coupon once, with caps."""

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
IMAGE = "sha256:4a9845150bd24a5b2a1a1fbd6035247602d29611d13e3f8091e4ca5ba09c15bb"
CONTAINER = "wj-ccxcap-touch-r5-attempt01"


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
    freeze_sha = sha256(FREEZE_PATH)
    if readiness.get("status") != "READY_FOR_ONE_SERIALIZED_R5_METHOD_COUPON_RUN":
        raise RuntimeError("parent readiness is not affirmative")
    if readiness.get("input_freeze_sha256") != freeze_sha:
        raise RuntimeError("readiness does not bind the current input freeze")
    if readiness.get("runner_sha256") != sha256(HERE / "run.py"):
        raise RuntimeError("readiness does not bind this runner")
    if readiness.get("verifier_sha256") != sha256(HERE / "verify.py"):
        raise RuntimeError("readiness does not bind this verifier")
    if (
        readiness.get("parent_review_sha256")
        != freeze["authority_and_review"]["attempt02_parent_review_sha256"]
    ):
        raise RuntimeError(
            "readiness and input freeze disagree on the source/build review"
        )
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
        freeze["authority_and_review"]["attempt02_parent_review_path"]: freeze[
            "authority_and_review"
        ]["attempt02_parent_review_sha256"],
        freeze["authority_and_review"]["attempt02_source_pins_path"]: freeze[
            "authority_and_review"
        ]["attempt02_source_pins_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/context/source.tar.bz2": freeze[
            "solver"
        ]["source_archive_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/context/capture.patch": freeze[
            "solver"
        ]["patch_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/artifacts-r5/build-manifest.json": freeze[
            "solver"
        ]["build_manifest_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/artifacts-r5/ccx-bounded-contact-capture-2.23": freeze[
            "solver"
        ]["binary_sha256"],
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/capture-contract.json": freeze[
            "solver"
        ]["capture_contract_sha256"],
        freeze["known_answer"]["expected_path"]: freeze["known_answer"][
            "expected_sha256"
        ],
        freeze["reader_contract"]["reader_path"]: freeze["reader_contract"][
            "reader_sha256"
        ],
        freeze["solver"]["manual_path"]: freeze["solver"]["manual_sha256"],
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
        "schema": "ccx223_r5_contact_capture_coupon_execution/v1",
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
        "readiness_sha256": sha256(READINESS_PATH),
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
