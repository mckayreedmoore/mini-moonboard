"""Run the patched 2.23 binary on one frozen coupon and verify trace/output parity."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
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
REFERENCE = REPO / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "contact-output-known-answer-attempt01")
BUILD = DIAG / "build-attempt02"
BASE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
OLD_ID = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
OLD_TAG = "mini-moonboard-fea:ccx-upstream-2.21-v1"
IMAGE_TAG = "mini-moonboard-fea:ccx-attempt04-output-trace-build02-20260927-v1"
IMAGE_ID = "sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa"
BINARY_PATH = "/usr/local/bin/ccx-attempt04-diagnostic-2.23"
INPUT_SHA = "73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab"
SOURCE_ARCHIVE_SHA = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
PATCH_SHA = "aea55ec88be569a39a06482723d5da22260b071bf072c55491448b22ab273e54"
SOURCE_BASIS = {
    "source_path": "CalculiX/ccx_2.23/src/nonlingeo.c",
    "original_sha256":
        "8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f",
    "patched_sha256":
        "49ad90f47350d133c9f1994065cb7f38642b08f06b82ad47428891c8d19705b9",
    "initial_contact_generation_lines": "1738-1921",
    "contact_call_lines": "1883-1895",
    "outer_iteration_guard_line": 2228,
    "contact_count_change_branch_lines": "2352-2360",
    "contact_threshold": 0.001,
}
SOURCE_BASIS_SOURCE_HASHES = {
    "CalculiX/ccx_2.23/src/checkconvergence.c":
        "776ecbeec10de037dc1a18171b81ede973fca52d587a2c4d4342f0d14f362b11",
    "CalculiX/ccx_2.23/src/nonlingeo.c": SOURCE_BASIS["original_sha256"],
}
PATCHED_SOURCE_HASHES = {
    "CalculiX/ccx_2.23/src/nonlingeo.c": SOURCE_BASIS["patched_sha256"],
    "CalculiX/ccx_2.23/src/checkconvergence.c":
        "248d79718c6d939d8685a86f51bfa12272cc403fb6da855001be88d163f0088a",
}
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
OLD_ATTEMPT_DIR = DIAG / "coupon-known-answer-attempt01"
OLD_EXECUTION_SHA = (
    "66b9cc4404b9b58ea27f0a6bdc1566ff"
    "7d3a034eefd601a00621972eb7f6d797"
)
OLD_VERIFIER_SHA = (
    "e114ca152d9b0cb22f0366b2ecf8291d971fd7ff"
    "ccaf702fcfc89d4cb95c7c88"
)
FROZEN_KEYS = {
    (1, increment, 1, iteration)
    for increment in range(1, 9)
    for iteration in (1, 2)
}
CONTACT_EVENT_KEYS = {identity for identity in FROZEN_KEYS if identity[3] > 1}
CONTACT_FIELDS = {
    "event", *KEY_FIELDS, "contact_old", "contact_new", "delcon",
    "contact_change_flag",
}
CONVERGENCE_FIELDS = {
    "event", *KEY_FIELDS, "mechanical_applicable", "iteration_ok",
    "mechanical_residual_ok", "displacement_ok", "visco_ok",
    "contact_change_gate_clear", "no_contact_now", "no_contact_at_start",
    "contact_present", "mechanical_gate_ok", "no_contact_energy_eligible",
    "contact_energy_eligible", "iconvergence", "idivergence",
    "final_convergence_ok",
}


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


def verify_frozen_sources() -> tuple[dict, dict, dict, dict]:
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

    reference_cvg = parse_cvg(REFERENCE / "instrumented/coupon.cvg")
    reference_cel = parse_cel(REFERENCE / "instrumented/coupon.cel")
    require(set(reference_cvg) == FROZEN_KEYS,
            "frozen known-answer .cvg keys differ from 16-iteration baseline")
    require(set(reference_cel) == FROZEN_KEYS,
            "frozen known-answer .cel keys differ from 16-iteration baseline")

    old_execution_path = OLD_ATTEMPT_DIR / "execution.json"
    old_verifier_path = OLD_ATTEMPT_DIR / "verifier.json"
    old_execution = json.loads(old_execution_path.read_text())
    old_verifier = json.loads(old_verifier_path.read_text())
    old_errors = ["contact trace identities do not match .cvg records"]
    require(file_sha(old_execution_path) == OLD_EXECUTION_SHA,
            "preserved coupon01 failure execution hash changed")
    require(file_sha(old_verifier_path) == OLD_VERIFIER_SHA,
            "preserved coupon01 failure verifier hash changed")
    require(old_execution["status"] == "FAIL" and
            old_execution["numerical_output_equivalence"] is True and
            old_execution["trace_alignment_pass"] is False and
            old_execution["errors"] == old_errors,
            "coupon01 execution is not the expected trace-only failure")
    require(old_verifier["status"] == "FAIL" and
            old_verifier["errors"] == old_errors and
            old_verifier["numerical_and_iteration_checks"][
                "numerical_output_equivalence"] is True and
            old_verifier["numerical_and_iteration_checks"][
                "trace_alignment_pass"] is False,
            "coupon01 verifier is not the expected trace-only failure")
    require(old_execution["patched_image_id"] == IMAGE_ID and
            old_execution["patched_binary_sha256"] ==
            "3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f",
            "coupon01 failure does not bind the unchanged build02 binary")
    prior_failure = {
        "execution_path": "../coupon-known-answer-attempt01/execution.json",
        "execution_sha256": file_sha(old_execution_path),
        "verifier_path": "../coupon-known-answer-attempt01/verifier.json",
        "verifier_sha256": file_sha(old_verifier_path),
        "status": "FAIL",
        "numerical_output_equivalence": True,
        "trace_alignment_pass": False,
        "errors": old_errors,
    }
    return execution, result, reference_run, prior_failure


def verify_coupon_scope() -> dict:
    require(INPUT.is_file() and file_sha(INPUT) == INPUT_SHA,
            "fresh coupon input differs from its frozen deck hash")
    deck = INPUT.read_text(encoding="ascii")
    keywords = [line.strip().upper() for line in deck.splitlines()
                if line.lstrip().startswith("*") and
                not line.lstrip().startswith("**")]
    contact_cards = [line for line in keywords if line.startswith("*CONTACT PAIR")]
    require(len(contact_cards) == 1 and "TYPE=SURFACE TO SURFACE" in contact_cards[0],
            "coupon scope requires exactly one surface-to-surface contact pair")
    require("SMALL SLIDING" not in deck.upper(),
            "coupon scope unexpectedly includes SMALL SLIDING")
    require(sum(line.startswith("*STATIC") for line in keywords) == 1,
            "coupon scope requires exactly one *STATIC procedure")
    require(not any(any(token in line for token in
                        ("*DYNAMIC", "*COUPLED", "*HEAT TRANSFER", "*THERMAL"))
                    for line in keywords),
            "coupon scope includes dynamic or thermal procedure keywords")
    return {
        "coupon_input_sha256": INPUT_SHA,
        "contact_pair_keyword": contact_cards[0],
        "procedure": "one *STATIC step",
        "small_sliding_present": False,
        "mortar_mode": 1,
        "scope": "mechanical, surface-to-surface mortar1 contact coupon",
    }


def verify_built_image() -> tuple[dict, dict, dict]:
    build_result_path = BUILD / "build_result.json"
    manifest_path = BUILD / "build_manifest.json"
    context_path = BUILD / "build-context-inventory.json"
    build_result = json.loads(build_result_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    context_inventory = json.loads(context_path.read_text())
    lock_path = DIAG / "diagnostic-lock.json"
    lock = json.loads(lock_path.read_text())
    source_verification_path = BUILD / "source-manifest-verification.json"
    source_verification = json.loads(source_verification_path.read_text())
    require(build_result["exit_code"] == 0 and not build_result["timed_out"],
            "source-patched image build did not complete successfully")
    require(build_result["base_image_id"] == BASE_ID and
            build_result["new_image_tag"] == IMAGE_TAG and
            build_result["image_id"] == IMAGE_ID,
            "build record differs from the pinned attempt02 image")
    require(manifest["base_image_id"] == BASE_ID and
            manifest["base_image_tag"] == BASE_TAG and
            manifest["upstream_file_count"] == 1197,
            "build manifest differs from the pinned 2.23 source base")
    require(file_sha(manifest_path) == build_result["image_manifest_sha256"],
            "built image manifest hash differs from the build record")
    require(manifest["complete_source_manifest_match"] is True and
            source_verification == build_result["source_manifest_verification"] and
            source_verification["full_source_manifest_match"] is True,
            "built image source manifest verification is incomplete or changed")
    require(manifest["diagnostic_lock_sha256"] == file_sha(lock_path),
            "build manifest differs from the current exact diagnostic lock")
    require(manifest["original_source_member_sha256"] ==
            lock["source_members_sha256"] == SOURCE_BASIS_SOURCE_HASHES,
            "built image original source members differ from exact lock pins")
    require(manifest["patched_source_member_sha256"] ==
            PATCHED_SOURCE_HASHES,
            "built image patched source members differ from exact patch pins")
    require(file_sha(build_result_path) ==
            context_inventory["build_result_sha256"],
            "context inventory binds a different build result")
    for relative, record in context_inventory["files"].items():
        path = BUILD / "context" / relative
        require(path.is_file() and file_sha(path) == record["sha256"],
                f"build context file differs from its inventory: {relative}")
    require(manifest["patch_sha256"] == lock["patch"]["sha256"] and
            manifest["patch_sha256"] == PATCH_SHA and
            file_sha(DIAG / "diagnostic.patch") == PATCH_SHA,
            "built image patch pin differs from the diagnostic lock")
    require(manifest["upstream_source_archive_sha256"] ==
            lock["official_source_archive"]["sha256"] == SOURCE_ARCHIVE_SHA,
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
    require(build_result["patched_binary_sha256"] ==
            "3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f",
            "patched binary SHA-256 differs from the pinned attempt02 build")
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


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate JSON field: {name}")
        result[name] = value
    return result


def reject_nonfinite_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def validate_event(record: object) -> dict:
    require(type(record) is dict, "trace event must be a JSON object")
    event_type = record.get("event")
    if event_type == "CCX223_ATTEMPT04_CONTACT":
        expected_fields = CONTACT_FIELDS
    elif event_type == "CCX223_ATTEMPT04_CONVERGENCE":
        expected_fields = CONVERGENCE_FIELDS
    else:
        raise ValueError("structured trace marker has an unexpected event type")
    require(set(record) == expected_fields,
            f"{event_type} trace fields differ from the strict schema")
    for field in KEY_FIELDS:
        require(type(record[field]) is int and record[field] > 0,
                f"{event_type}.{field} must be a positive JSON integer")
    for field, value in record.items():
        if type(value) is float:
            require(math.isfinite(value),
                    f"{event_type}.{field} must be finite")
    if event_type == "CCX223_ATTEMPT04_CONTACT":
        for field in ("contact_old", "contact_new", "contact_change_flag"):
            require(type(record[field]) is int,
                    f"contact.{field} must be a JSON integer")
        require(record["contact_old"] >= 0 and record["contact_new"] >= 0,
                "contact counts must be nonnegative")
        require(record["contact_change_flag"] in (0, 1),
                "contact_change_flag must be integer 0/1")
        require(type(record["delcon"]) is float and
                math.isfinite(record["delcon"]) and
                record["delcon"] == SOURCE_BASIS["contact_threshold"],
                "contact.delcon must equal the pinned 0.001 threshold")
    else:
        for field in BOOL_FIELDS:
            require(type(record[field]) is int and record[field] in (0, 1),
                    f"convergence.{field} must be integer 0/1")
        for field in ("iconvergence", "idivergence"):
            require(type(record[field]) is int,
                    f"convergence.{field} must be a JSON integer")
    return record


def parse_events(path: Path) -> tuple[list[dict], list[dict]]:
    contact = []
    convergence = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if "CCX223_ATTEMPT04_CONTACT" in line or \
                "CCX223_ATTEMPT04_CONVERGENCE" in line:
            record = validate_event(json.loads(
                line, object_pairs_hook=reject_duplicate_json_keys,
                parse_constant=reject_nonfinite_json_constant))
            if record["event"] == "CCX223_ATTEMPT04_CONTACT":
                contact.append(record)
            elif record["event"] == "CCX223_ATTEMPT04_CONVERGENCE":
                convergence.append(record)
    return contact, convergence


def normalize_frd(data: bytes) -> bytes:
    matches = list(FRD_UTIME.finditer(data))
    require(len(matches) == 1, "FRD must contain exactly one generated 1UTIME header")
    return FRD_UTIME.sub(rb"\1<UTIME>\2", data, count=1)


def verify_outputs(reference_run: dict) -> tuple[dict, dict, list[str]]:
    numerical_errors: list[str] = []
    trace_errors: list[str] = []
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
            numerical_errors.append(f"missing exact output or reference hash: {name}")
        elif actual_hashes[name] != expected_hashes[name]:
            numerical_errors.append(f"byte hash differs for {name}")
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
                numerical_errors.append(
                    f"FRD numerical bytes differ after UTIME normalization: {name}")
        except (OSError, RuntimeError) as error:
            numerical_errors.append(f"could not compare {name}: {error}")
    known_expected_paths = set(expected_hashes)
    if any(name not in known_expected_paths for name in FRD_OUTPUTS):
        numerical_errors.append("known-answer record does not bind every FRD output")

    alignment = []
    cvg: dict[tuple[int, int, int, int], int] = {}
    cel: dict[tuple[int, int, int, int], int] = {}
    contact_map: dict[tuple[int, int, int, int], dict] = {}
    convergence_map: dict[tuple[int, int, int, int], dict] = {}
    contact_events: list[dict] = []
    convergence_events: list[dict] = []
    trace_summary = {
        "contact_event_count": 0,
        "convergence_event_count": 0,
        "cvg_iteration_count": 0,
        "cel_group_count": 0,
        "frozen_baseline_iteration_count": len(FROZEN_KEYS),
        "frozen_baseline_increment_count": 8,
    }
    try:
        cvg = parse_cvg(OUTPUT / "coupon.cvg")
        cel = parse_cel(OUTPUT / "coupon.cel")
        contact_events, convergence_events = parse_events(OUTPUT / "solver.stdout")
        contact_map.clear()
        convergence_map.clear()
        for event in contact_events:
            identity = key(event)
            if identity in contact_map:
                trace_errors.append(f"duplicate contact trace identity: {identity}")
            contact_map[identity] = event
        for event in convergence_events:
            identity = key(event)
            if identity in convergence_map:
                trace_errors.append(f"duplicate convergence trace identity: {identity}")
            convergence_map[identity] = event
        trace_summary = {
            "contact_event_count": len(contact_events),
            "convergence_event_count": len(convergence_events),
            "cvg_iteration_count": len(cvg),
            "cel_group_count": len(cel),
            "frozen_baseline_iteration_count": len(FROZEN_KEYS),
            "frozen_baseline_increment_count": 8,
        }
        increments = {identity[1] for identity in cvg}
        if len(cvg) != 16 or set(cvg) != FROZEN_KEYS:
            trace_errors.append(
                ".cvg must match the frozen 16-iteration, 8-increment baseline")
        if set(increments) != set(range(1, 9)):
            trace_errors.append(".cvg increment keys must be exactly 1 through 8")
        if set(cel) != FROZEN_KEYS:
            trace_errors.append(
                ".cel keys must match the frozen 16-iteration, 8-increment baseline")
        if set(cvg) != set(cel):
            trace_errors.append(".cvg iteration identities do not match .cel groups")
        if set(convergence_map) != set(cvg):
            trace_errors.append(
                "convergence event identities must equal all .cvg/.cel keys")
        expected_contact_keys = {
            identity for identity in cvg if identity[3] > 1
        }
        if expected_contact_keys != CONTACT_EVENT_KEYS:
            trace_errors.append(
                "frozen .cvg keys do not produce the 8 expected later-iteration keys")
        if set(contact_map) != expected_contact_keys:
            trace_errors.append(
                "contact event identities must equal .cvg/.cel keys with iteration > 1")
        for identity in sorted(FROZEN_KEYS):
            contact = contact_map.get(identity)
            convergence = convergence_map.get(identity)
            contact_count = cvg.get(identity)
            cel_count = cel.get(identity)
            if contact is not None:
                if contact.get("contact_new") != contact_count:
                    trace_errors.append(
                        f"contact_new differs from .cvg count at {identity}")
                if contact.get("contact_new") != cel_count:
                    trace_errors.append(
                        f"contact_new differs from .cel count at {identity}")
                previous = (identity[0], identity[1], identity[2], identity[3] - 1)
                if previous not in cvg:
                    trace_errors.append(
                        f"preceding .cvg iteration is absent for contact at {identity}")
                elif contact.get("contact_old") != cvg[previous]:
                    trace_errors.append(
                        f"contact_old differs from preceding .cvg count at {identity}")
            alignment.append({
                "step": identity[0], "increment": identity[1],
                "attempt": identity[2], "iteration": identity[3],
                "cvg_contact_elements": contact_count,
                "cel_contact_elements": cel_count,
                "contact_trace": contact,
                "convergence_trace": convergence,
            })
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        trace_errors.append(f"trace parsing/alignment failed: {error}")

    comparisons = {
        name: {
            "actual_sha256": actual_hashes.get(name),
            "expected_sha256": expected_hashes.get(name),
            "byte_identical": actual_hashes.get(name) == expected_hashes.get(name),
        }
        for name in EXACT_OUTPUTS
    }
    numerical_output_equivalence = not numerical_errors and all(
        comparison["byte_identical"] for comparison in comparisons.values()) and \
        all(check.get("matches_after_normalizing_generated_UTIME") is True
            for check in frd_checks.values()) and len(frd_checks) == len(FRD_OUTPUTS)
    trace_alignment_pass = not trace_errors and len(cvg) == 16 and \
        set(cvg) == set(cel) == set(convergence_map) == FROZEN_KEYS and \
        set(contact_map) == {identity for identity in cvg if identity[3] > 1}
    errors = numerical_errors + trace_errors
    checks = {
        "exact_output_comparisons": comparisons,
        "frd_normalization": (
            "For each FRD only, replace the clock value on the single 1UTIME line "
            "with <UTIME>."),
        "frd_comparisons": frd_checks,
        "output_sha256": actual_hashes,
        "output_bytes": output_sizes,
        "trace_summary": trace_summary,
        "iteration_alignment": alignment,
        "numerical_output_equivalence": numerical_output_equivalence,
        "trace_alignment_pass": trace_alignment_pass,
        "trace_expectation": {
            "convergence_keys": "exactly all 16 .cvg/.cel keys",
            "contact_keys": "exactly .cvg/.cel keys with iteration > 1",
            "contact_event_count": 8,
            "convergence_event_count": 16,
            "source_basis": SOURCE_BASIS,
        },
        "numerical_errors": numerical_errors,
        "trace_errors": trace_errors,
        "errors": errors,
    }
    return checks, {
        "contact": contact_events,
        "convergence": convergence_events,
    }, errors


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    reference_execution, reference_result, reference_run, prior_failure = \
        verify_frozen_sources()
    coupon_scope = verify_coupon_scope()
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
        "schema": "calculix_223_attempt04_coupon_known_answer_attempt02_execution/v1",
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
        "source_logic_basis": SOURCE_BASIS,
        "diagnostic_lock_sha256": file_sha(lock_path),
        "diagnostic_patch_sha256": file_sha(patch_path),
        "attempt03_binding_sha256": file_sha(binding_path),
        "build_result_sha256": file_sha(BUILD / "build_result.json"),
        "build_manifest_sha256": file_sha(BUILD / "build_manifest.json"),
        "build_context_inventory_sha256": file_sha(
            BUILD / "build-context-inventory.json"),
        "build_context_tree_sha256": context_inventory["context_tree_sha256"],
        "source_manifest_verification_sha256": file_sha(
            BUILD / "source-manifest-verification.json"),
        "known_answer_execution_sha256": file_sha(REFERENCE / "execution.json"),
        "known_answer_result_sha256": file_sha(REFERENCE / "result.json"),
        "known_answer_input_freeze_sha256": file_sha(REFERENCE / "input-freeze.json"),
        "attempt01_failure_binding": prior_failure,
        "coupon_scope": coupon_scope,
        "expected_trace_counts": {
            "iterations": 16,
            "increments": 8,
            "convergence_events": 16,
            "contact_events": 8,
        },
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
        "schema": "calculix_223_attempt04_coupon_known_answer_attempt02_verifier/v1",
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
            "original_source_members_sha256":
                build_manifest["original_source_member_sha256"],
            "patched_source_members_sha256":
                build_manifest["patched_source_member_sha256"],
            "source_logic_basis": SOURCE_BASIS,
            "build_context_tree_sha256": context_inventory["context_tree_sha256"],
            "patch_sha256": file_sha(patch_path),
            "attempt03_binding_sha256": file_sha(binding_path),
            "coupon_input_sha256": input_hash,
            "known_answer_result_sha256": file_sha(REFERENCE / "result.json"),
            "attempt01_failure_binding": prior_failure,
            "coupon_scope": coupon_scope,
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
