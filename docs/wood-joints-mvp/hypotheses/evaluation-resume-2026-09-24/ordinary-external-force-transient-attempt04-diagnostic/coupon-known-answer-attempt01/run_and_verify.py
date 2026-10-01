"""Run the patched 2.23 binary on one frozen coupon and verify trace/output parity."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import time


REPO = Path(__file__).resolve().parents[6]
DIAG = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
INPUT = HERE / "input/coupon.inp"
OUTPUT = HERE / "output"
REFERENCE = REPO / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/contact-output-known-answer-attempt01"
BUILD = DIAG / "build-attempt02"
BASE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
OLD_ID = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
OLD_TAG = "mini-moonboard-fea:ccx-upstream-2.21-v1"
IMAGE_TAG = "mini-moonboard-fea:ccx-attempt04-output-trace-build02-20260927-v1"
IMAGE_ID = "sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa"
BINARY_PATH = "/usr/local/bin/ccx-attempt04-diagnostic-2.23"
INPUT_SHA = "73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab"
TIMEOUT_SECONDS = 60
STDOUT_CAP_BYTES = 1_048_576
STDERR_CAP_BYTES = 1_048_576
FRD_UTIME = re.compile(
    rb"(?m)^([ \t]*1UTIME[ \t]+)[0-9]{2}:[0-9]{2}:[0-9]{2}([^\r\n]*)$")
CEL_GROUP = re.compile(
    r"^\*ELEMENT,TYPE=C3D6,ELSET=contactelements_st(\d+)_in(\d+)_at(\d+)_it(\d+)\s*$",
    re.IGNORECASE)
BOOL_FIELDS = (
    "mechanical_applicable", "iteration_ok", "mechanical_residual_ok",
    "displacement_ok", "visco_ok", "contact_change_gate_clear",
    "no_contact_now", "no_contact_at_start", "contact_present",
    "mechanical_gate_ok", "no_contact_energy_eligible",
    "contact_energy_eligible", "final_convergence_ok")
KEY_FIELDS = ("step", "increment", "attempt", "iteration")
EXACT_OUTPUTS = (
    "coupon.12d", "coupon.cel", "coupon.cvg", "coupon.dat", "coupon.sta",
    "spooles.out")
FRD_OUTPUTS = ("coupon.frd", "ResultsForLastIterations.frd")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def docker_id(reference: str) -> str:
    return subprocess.check_output(
        ["docker", "image", "inspect", reference, "--format", "{{.Id}}"],
        text=True).strip()


def verify_frozen_sources() -> tuple[dict, dict, dict]:
    execution_path = REFERENCE / "execution.json"
    result_path = REFERENCE / "result.json"
    freeze_path = REFERENCE / "input-freeze.json"
    execution = json.loads(execution_path.read_text())
    result = json.loads(result_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    require(result["status"] == "PASS_OUTPUT_PATH_AND_BASELINE_EQUIVALENCE",
            "known-answer source result is not passing")
    require(file_sha(result_path) == execution["result_sha256"],
            "known-answer result hash differs from its execution record")
    require(file_sha(freeze_path) == execution["input_freeze_sha256"],
            "known-answer input freeze hash differs from its execution record")
    require(INPUT.is_file() and file_sha(INPUT) == INPUT_SHA ==
            freeze["deck_sha256"]["instrumented"],
            "fresh coupon input differs from the frozen instrumented deck")
    reference_run = next(run for run in execution["runs"]
                         if run["case"] == "instrumented")
    for name, expected_hash in reference_run["outputs_sha256"].items():
        path = REFERENCE / "instrumented" / name
        require(path.is_file() and file_sha(path) == expected_hash,
                f"known-answer instrumented output differs: {name}")
    return execution, result, reference_run


def verify_built_image() -> tuple[dict, dict, dict]:
    build_result_path = BUILD / "build_result.json"
    manifest_path = BUILD / "build_manifest.json"
    context_path = BUILD / "build-context-inventory.json"
    build_result = json.loads(build_result_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    context_inventory = json.loads(context_path.read_text())
    require(build_result["exit_code"] == 0 and not build_result["timed_out"],
            "source-patched image build did not complete successfully")
    require(build_result["base_image_id"] == BASE_ID and
            build_result["new_image_tag"] == IMAGE_TAG and
            build_result["image_id"] == IMAGE_ID,
            "build record differs from the pinned attempt02 image")
    require(file_sha(manifest_path) == build_result["image_manifest_sha256"],
            "built image manifest hash differs from the build record")
    require(file_sha(build_result_path) ==
            context_inventory["build_result_sha256"],
            "context inventory binds a different build result")
    for relative, record in context_inventory["files"].items():
        path = BUILD / "context" / relative
        require(path.is_file() and file_sha(path) == record["sha256"],
                f"build context file differs from its inventory: {relative}")
    require(manifest["patch_sha256"] ==
            json.loads((DIAG / "diagnostic-lock.json").read_text())["patch"]["sha256"],
            "built image patch pin differs from the diagnostic lock")
    require(manifest["upstream_source_archive_sha256"] ==
            json.loads((DIAG / "diagnostic-lock.json").read_text())[
                "official_source_archive"]["sha256"],
            "built image source archive pin differs from the diagnostic lock")
    require(docker_id(BASE_TAG) == BASE_ID and docker_id(OLD_TAG) == OLD_ID,
            "a historical solver base tag changed before coupon execution")
    require(docker_id(IMAGE_TAG) == IMAGE_ID,
            "new diagnostic image tag differs from its recorded ID")
    binary_info = subprocess.check_output([
        "docker", "run", "--rm", "--network", "none", IMAGE_ID,
        "sha256sum", BINARY_PATH, "/usr/local/bin/ccx-upstream-2.23", "/usr/bin/ccx"],
        text=True)
    parsed = {line.split(maxsplit=1)[1]: line.split(maxsplit=1)[0]
              for line in binary_info.splitlines()}
    require(parsed.get(BINARY_PATH) == build_result["patched_binary_sha256"],
            "patched binary hash differs inside the built image")
    require(parsed.get("/usr/local/bin/ccx-upstream-2.23") ==
            "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "unpatched 2.23 executable changed in the diagnostic image")
    require(parsed.get("/usr/bin/ccx") ==
            "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b",
            "packaged 2.21 executable changed in the diagnostic image")
    return build_result, manifest, context_inventory


def stop_container(name: str) -> None:
    subprocess.run(["docker", "stop", "--time", "2", name],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=10, check=False)


def stream_bounded(command: list[str], name: str, stdout_path: Path,
                   stderr_path: Path) -> dict:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selector = selectors.DefaultSelector()
    streams = {
        process.stdout: (stdout_path.open("wb"), STDOUT_CAP_BYTES, "stdout"),
        process.stderr: (stderr_path.open("wb"), STDERR_CAP_BYTES, "stderr"),
    }
    counts = {"stdout": 0, "stderr": 0}
    observed = {"stdout": 0, "stderr": 0}
    exceeded = {"stdout": False, "stderr": False}
    for pipe in streams:
        os.set_blocking(pipe.fileno(), False)
        selector.register(pipe, selectors.EVENT_READ)
    started = time.monotonic()
    stopped_for_bound = False
    timed_out = False
    while selector.get_map():
        now = time.monotonic()
        if not stopped_for_bound and now - started > TIMEOUT_SECONDS:
            timed_out = True
            stopped_for_bound = True
            stop_container(name)
        for key, _ in selector.select(timeout=0.1):
            pipe = key.fileobj
            label_file, cap, label = streams[pipe]
            chunk = os.read(pipe.fileno(), 65536)
            if not chunk:
                selector.unregister(pipe)
                continue
            observed[label] += len(chunk)
            remaining = max(0, cap - counts[label])
            kept = chunk[:remaining]
            if kept:
                label_file.write(kept)
                counts[label] += len(kept)
            if len(chunk) > remaining:
                exceeded[label] = True
                if not stopped_for_bound:
                    stopped_for_bound = True
                    stop_container(name)
        if stopped_for_bound and process.poll() is None and \
                time.monotonic() - started > TIMEOUT_SECONDS + 10:
            process.kill()
    for pipe, (label_file, _, _) in streams.items():
        label_file.close()
        pipe.close()
    returncode = process.wait(timeout=10)
    return {
        "returncode": returncode,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "timed_out": timed_out,
        "stdout_cap_bytes": STDOUT_CAP_BYTES,
        "stdout_bytes_captured": counts["stdout"],
        "stdout_bytes_observed": observed["stdout"],
        "stdout_cap_exceeded": exceeded["stdout"],
        "stderr_cap_bytes": STDERR_CAP_BYTES,
        "stderr_bytes_captured": counts["stderr"],
        "stderr_bytes_observed": observed["stderr"],
        "stderr_cap_exceeded": exceeded["stderr"],
    }


def key(record: dict) -> tuple[int, int, int, int]:
    return tuple(int(record[field]) for field in KEY_FIELDS)


def parse_cvg(path: Path) -> dict[tuple[int, int, int, int], int]:
    records = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 5 and all(re.fullmatch(r"\d+", token) for token in fields[:5]):
            identity = tuple(map(int, fields[:4]))
            require(identity not in records, f"duplicate .cvg iteration {identity}")
            records[identity] = int(fields[4])
    return records


def parse_cel(path: Path) -> dict[tuple[int, int, int, int], int]:
    records = {}
    for line in path.read_text().splitlines():
        match = CEL_GROUP.fullmatch(line)
        if match:
            identity = tuple(map(int, match.groups()))
            records[identity] = records.get(identity, 0) + 1
    return records


def parse_events(path: Path) -> tuple[list[dict], list[dict]]:
    contact = []
    convergence = []
    for line in path.read_text(errors="replace").splitlines():
        if "CCX223_ATTEMPT04_CONTACT" in line or \
                "CCX223_ATTEMPT04_CONVERGENCE" in line:
            record = json.loads(line)
            if record.get("event") == "CCX223_ATTEMPT04_CONTACT":
                contact.append(record)
            elif record.get("event") == "CCX223_ATTEMPT04_CONVERGENCE":
                convergence.append(record)
            else:
                raise ValueError("structured trace marker has an unexpected event type")
    return contact, convergence


def normalize_frd(data: bytes) -> bytes:
    matches = list(FRD_UTIME.finditer(data))
    require(len(matches) == 1, "FRD must contain exactly one generated 1UTIME header")
    return FRD_UTIME.sub(rb"\1<UTIME>\2", data, count=1)


def verify_outputs(reference_run: dict) -> tuple[dict, dict, list[str]]:
    errors: list[str] = []
    expected_hashes = reference_run["outputs_sha256"]
    actual_hashes = {}
    output_sizes = {}
    for path in sorted(OUTPUT.iterdir()):
        if path.is_file():
            data = path.read_bytes()
            actual_hashes[path.name] = sha(data)
            output_sizes[path.name] = len(data)
    for name in EXACT_OUTPUTS:
        path = OUTPUT / name
        if name not in expected_hashes or not path.is_file():
            errors.append(f"missing exact output or reference hash: {name}")
        elif actual_hashes[name] != expected_hashes[name]:
            errors.append(f"byte hash differs for {name}")
    frd_checks = {}
    for name in FRD_OUTPUTS:
        path = OUTPUT / name
        expected_path = REFERENCE / "instrumented" / name
        try:
            actual_data = path.read_bytes()
            expected_data = expected_path.read_bytes()
            actual_norm = normalize_frd(actual_data)
            expected_norm = normalize_frd(expected_data)
            frd_checks[name] = {
                "actual_sha256": sha(actual_data),
                "expected_sha256": expected_hashes.get(name),
                "actual_normalized_sha256": sha(actual_norm),
                "expected_normalized_sha256": sha(expected_norm),
                "matches_after_normalizing_generated_UTIME": actual_norm == expected_norm,
            }
            if not frd_checks[name]["matches_after_normalizing_generated_UTIME"]:
                errors.append(f"FRD numerical bytes differ after UTIME normalization: {name}")
        except (OSError, RuntimeError) as error:
            errors.append(f"could not compare {name}: {error}")
    known_expected_paths = set(expected_hashes)
    if any(name not in known_expected_paths for name in FRD_OUTPUTS):
        errors.append("known-answer record does not bind every FRD output")

    alignment = []
    trace_summary = {"contact_event_count": 0, "convergence_event_count": 0}
    try:
        cvg = parse_cvg(OUTPUT / "coupon.cvg")
        cel = parse_cel(OUTPUT / "coupon.cel")
        contact_events, convergence_events = parse_events(OUTPUT / "solver.stdout")
        contact_map = {key(event): event for event in contact_events}
        convergence_map = {key(event): event for event in convergence_events}
        trace_summary = {
            "contact_event_count": len(contact_events),
            "convergence_event_count": len(convergence_events),
            "cvg_iteration_count": len(cvg),
            "cel_group_count": len(cel),
        }
        if len(contact_map) != len(contact_events):
            errors.append("duplicate contact trace identity")
        if len(convergence_map) != len(convergence_events):
            errors.append("duplicate convergence trace identity")
        if set(cvg) != set(cel):
            errors.append(".cvg iteration identities do not match .cel groups")
        if set(contact_map) != set(cvg):
            errors.append("contact trace identities do not match .cvg records")
        if set(convergence_map) != set(cvg):
            errors.append("convergence trace identities do not match .cvg records")
        for identity in sorted(set(cvg) | set(contact_map) | set(convergence_map)):
            contact = contact_map.get(identity)
            convergence = convergence_map.get(identity)
            contact_count = cvg.get(identity)
            cel_count = cel.get(identity)
            if contact is not None:
                if contact.get("contact_new") != contact_count:
                    errors.append(f"contact trace count differs from .cvg at {identity}")
                if contact.get("contact_new") != cel_count:
                    errors.append(f"contact trace count differs from .cel at {identity}")
                if contact.get("contact_change_flag") not in (0, 1):
                    errors.append(f"contact flag is not encoded as integer 0/1 at {identity}")
                if float(contact.get("delcon", 0)) <= 0:
                    errors.append(f"contact delcon is not positive at {identity}")
            if convergence is not None:
                if any(convergence.get(field) not in (0, 1) for field in BOOL_FIELDS):
                    errors.append(f"convergence boolean is not integer 0/1 at {identity}")
                if not isinstance(convergence.get("iconvergence"), int) or \
                        not isinstance(convergence.get("idivergence"), int):
                    errors.append(f"convergence flags are not integers at {identity}")
            alignment.append({
                "step": identity[0], "increment": identity[1],
                "attempt": identity[2], "iteration": identity[3],
                "cvg_contact_elements": contact_count,
                "cel_contact_elements": cel_count,
                "contact_trace": contact,
                "convergence_trace": convergence,
            })
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        errors.append(f"trace parsing/alignment failed: {error}")

    comparisons = {
        name: {
            "actual_sha256": actual_hashes.get(name),
            "expected_sha256": expected_hashes.get(name),
            "byte_identical": actual_hashes.get(name) == expected_hashes.get(name),
        }
        for name in EXACT_OUTPUTS
    }
    checks = {
        "exact_output_comparisons": comparisons,
        "frd_normalization":
            "For each FRD only, replace the clock value on the single 1UTIME line with <UTIME>.",
        "frd_comparisons": frd_checks,
        "output_sha256": actual_hashes,
        "output_bytes": output_sizes,
        "trace_summary": trace_summary,
        "iteration_alignment": alignment,
        "numerical_output_equivalence": not any(
            comparison["byte_identical"] is False for comparison in comparisons.values())
            and all(check.get("matches_after_normalizing_generated_UTIME") is True
                    for check in frd_checks.values())
            and len(frd_checks) == len(FRD_OUTPUTS),
        "trace_alignment_pass": bool(alignment) and not any(
            "trace" in error or ".cvg" in error or ".cel" in error
            for error in errors),
        "errors": errors,
    }
    return checks, {"contact": contact_events if "contact_events" in locals() else [],
                    "convergence": convergence_events if "convergence_events" in locals() else []}, errors


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    reference_execution, reference_result, reference_run = verify_frozen_sources()
    build_result, build_manifest, context_inventory = verify_built_image()
    require(INPUT.is_file(), "frozen coupon input is missing")
    require({path.name for path in INPUT.parent.iterdir() if path.is_file()} ==
            {"coupon.inp"}, "coupon input folder has unexpected files")
    require(not any(OUTPUT.iterdir()), "coupon output folder is not fresh")
    input_bytes = INPUT.read_bytes()
    input_hash = sha(input_bytes)
    working_deck = OUTPUT / "coupon.inp"
    working_deck.write_bytes(input_bytes)
    require(file_sha(working_deck) == INPUT_SHA,
            "fresh execution deck changed during copy")

    container_name = "wjj-at04-coupon-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    existing_container = subprocess.run(
        ["docker", "inspect", container_name], capture_output=True, check=False)
    require(existing_container.returncode != 0,
            f"refusing to reuse solver container {container_name}")
    command = [
        "docker", "run", "--name", container_name, "--network", "none",
        "--cpus", "2", "--memory", "4g", "--user", "1000:1000",
        "--env", "OMP_NUM_THREADS=2", "--env", "CCX_NPROC_EQUATION_SOLVER=2",
        "--mount", f"type=bind,src={OUTPUT},dst=/work", "--workdir", "/work",
        IMAGE_ID, BINARY_PATH, "-i", "coupon",
    ]
    run = stream_bounded(command, container_name,
                         OUTPUT / "solver.stdout", OUTPUT / "solver.stderr")
    state = None
    inspect = subprocess.run(
        ["docker", "inspect", "--format", "{{json .State}}", container_name],
        text=True, capture_output=True, check=False)
    if inspect.returncode == 0:
        state = json.loads(inspect.stdout)
        subprocess.run(["docker", "rm", container_name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)

    checks, events, errors = verify_outputs(reference_run)
    if run["returncode"] != 0:
        errors.append(f"patched solver container returned {run['returncode']}")
    if run["timed_out"]:
        errors.append("solver exceeded the 60 second time limit")
    if run["stdout_cap_exceeded"] or run["stderr_cap_exceeded"]:
        errors.append("solver stdout or stderr exceeded the recorded capture cap")
    if state is None:
        errors.append("solver container state could not be inspected")
    elif state.get("OOMKilled") or state.get("ExitCode") != 0:
        errors.append("solver container state reports OOM or nonzero exit")
    stdout_path = OUTPUT / "solver.stdout"
    stderr_path = OUTPUT / "solver.stderr"
    lock_path = DIAG / "diagnostic-lock.json"
    patch_path = DIAG / "diagnostic.patch"
    binding_path = DIAG / "attempt03-input-binding.json"
    execution = {
        "schema": "calculix_223_attempt04_coupon_preflight_execution/v1",
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "base_image_id": BASE_ID,
        "base_image_tag": BASE_TAG,
        "patched_image_tag": IMAGE_TAG,
        "patched_image_id": IMAGE_ID,
        "patched_binary_path": BINARY_PATH,
        "patched_binary_sha256": build_result["patched_binary_sha256"],
        "unpatched_2_23_binary_sha256":
            build_result["unpatched_2_23_binary_sha256"],
        "packaged_2_21_binary_sha256": build_result["packaged_2_21_binary_sha256"],
        "official_source_archive_sha256": build_manifest[
            "upstream_source_archive_sha256"],
        "source_members_original_sha256":
            build_manifest["original_source_member_sha256"],
        "source_members_patched_sha256":
            build_manifest["patched_source_member_sha256"],
        "diagnostic_lock_sha256": file_sha(lock_path),
        "diagnostic_patch_sha256": file_sha(patch_path),
        "attempt03_binding_sha256": file_sha(binding_path),
        "build_result_sha256": file_sha(BUILD / "build_result.json"),
        "build_manifest_sha256": file_sha(BUILD / "build_manifest.json"),
        "build_context_inventory_sha256": file_sha(
            BUILD / "build-context-inventory.json"),
        "build_context_tree_sha256": context_inventory["context_tree_sha256"],
        "known_answer_execution_sha256": file_sha(REFERENCE / "execution.json"),
        "known_answer_result_sha256": file_sha(REFERENCE / "result.json"),
        "known_answer_input_freeze_sha256": file_sha(REFERENCE / "input-freeze.json"),
        "input_path": "input/coupon.inp",
        "input_sha256": input_hash,
        "working_deck_sha256": file_sha(working_deck),
        "command": command,
        "container_name": container_name,
        "container_state": state,
        "resources": {"cpu_limit": 2, "memory_limit": "4g", "timeout_seconds": TIMEOUT_SECONDS,
                       "network": "none", "stdout_cap_bytes": STDOUT_CAP_BYTES,
                       "stderr_cap_bytes": STDERR_CAP_BYTES},
        "run": run,
        "stdout_path": "output/solver.stdout",
        "stdout_sha256": file_sha(stdout_path),
        "stderr_sha256": file_sha(stderr_path),
        "known_answer_instrumented_output_sha256":
            reference_run["outputs_sha256"],
        "numerical_output_equivalence": checks["numerical_output_equivalence"],
        "trace_alignment_pass": checks["trace_alignment_pass"],
        "verifier_script_sha256": file_sha(Path(__file__)),
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "errors": errors,
    }
    execution_path = HERE / "execution.json"
    execution_path.write_text(json.dumps(execution, indent=2) + "\n")
    verifier = {
        "schema": "calculix_223_attempt04_coupon_preflight_verifier/v1",
        "status": "PASS" if not errors else "FAIL",
        "execution_sha256": file_sha(execution_path),
        "execution_path": "execution.json",
        "verifier_script_sha256": file_sha(Path(__file__)),
        "source_binding": {
            "base_image_id": BASE_ID,
            "patched_image_id": IMAGE_ID,
            "patched_binary_sha256": build_result["patched_binary_sha256"],
            "source_archive_sha256": build_manifest[
                "upstream_source_archive_sha256"],
            "build_context_tree_sha256": context_inventory["context_tree_sha256"],
            "patch_sha256": file_sha(patch_path),
            "attempt03_binding_sha256": file_sha(binding_path),
            "coupon_input_sha256": input_hash,
            "known_answer_result_sha256": file_sha(REFERENCE / "result.json"),
        },
        "numerical_and_iteration_checks": checks,
        "event_records": events,
        "errors": errors,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
    }
    (HERE / "verifier.json").write_text(json.dumps(verifier, indent=2) + "\n")
    require(not errors, "; ".join(errors))


if __name__ == "__main__":
    main()
