"""Freeze and explicitly launch one quiescent hardware control; no qualification."""

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
BINARY = "/usr/local/bin/ccx-upstream-2.21"
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "fea/mortar_build/baseline-njusw3dz/build_manifest.json"
LIMITS = "Solver completion only; quiescent audit pending. No moving run, contact qualification or physical acceptance."


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    with Path(path).open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


LOADED_SOURCE_SHA256 = sha(Path(__file__))


def check_reference(context):
    """Quiescent launch requires predeclared numeric native-reference scales."""
    reference = context.get("diagnostic_reference_scales", {})
    keys = ("reference_mass_tonne", "P_star_tonne_mm_s", "E_star_N_mm", "H_star_tonne_mm2_s")
    values = [reference.get(key) for key in keys]
    if (reference.get("status") != "SOURCE-RECONSTRUCTED REFERENCE SCALES; no contact output qualification" or
            any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)):
        raise ValueError("Native reference mass/scales are pending or invalid")
    mass, linear, energy, angular = values
    if not all(math.isclose(a, b, rel_tol=1e-12, abs_tol=0.) for a, b in (
            (linear, mass * math.sqrt(20000)), (energy, mass * 10000), (angular, 57.15 * linear))):
        raise ValueError("Native reference scale formula differs")


def check_frozen(frozen, record):
    expected = {"moving_hardware_solve.py", "control.inp", "context.json", "build_manifest.json", "prepared-freeze.json"}
    if record["image"] != IMAGE or record["case"] != "quiescent" or set(record["inputs_sha256"]) != expected:
        raise ValueError("Wrong frozen quiescent inventory or image")
    if any(sha(frozen / name) != digest for name, digest in record["inputs_sha256"].items()):
        raise ValueError("Frozen input changed")
    if (sha(Path(__file__)) != LOADED_SOURCE_SHA256 or
            LOADED_SOURCE_SHA256 != record["inputs_sha256"]["moving_hardware_solve.py"]):
        raise ValueError("Executing launcher differs from frozen source")
    context = json.loads((frozen / "context.json").read_text())
    check_reference(context)
    prepared = json.loads((frozen / "prepared-freeze.json").read_text())["files_sha256"]
    if (prepared["context.json"] != sha(frozen / "context.json") or
            prepared["quiescent.inp"] != sha(frozen / "control.inp") or
            context["deck_sha256"]["quiescent"] != sha(frozen / "control.inp")):
        raise ValueError("Prepared context/deck identity differs")


def prepare(prepared, parent=Path("fea/generated/quiescent-solves")):
    """Copy a verified prepared quiescent deck into a new, unlaunched bundle."""
    prepared = Path(prepared).resolve()
    original_freeze = (prepared / "freeze.json").read_bytes()
    inventory = json.loads(original_freeze)["files_sha256"]
    for name, expected in inventory.items():
        path = (prepared / name).resolve()
        if not path.is_relative_to(prepared) or sha(path) != expected:
            raise ValueError("Prepared provenance changed: " + name)
    context = json.loads((prepared / "context.json").read_text())
    check_reference(context)
    if any(v != [0., 0., 0.] for v in context["cases"]["quiescent"]["initial_velocity_mm_s"].values()):
        raise ValueError("Only the prepared quiescent control may launch")
    for group in ("input_sha256", "source_sha256"):
        if any(inventory.get("frozen/" + name) != expected for name, expected in context[group].items()):
            raise ValueError("Prepared source/input manifest differs")
    if (inventory.get("context.json") != sha(prepared / "context.json") or
            inventory.get("quiescent.inp") != context["deck_sha256"]["quiescent"]):
        raise ValueError("Prepared quiescent context/deck identity differs")
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="quiescent-", dir=parent)).resolve()
    frozen = directory / "frozen"
    frozen.mkdir()
    for source, name in ((prepared / "quiescent.inp", "control.inp"), (prepared / "context.json", "context.json"),
                         (BUILD, "build_manifest.json"), (Path(__file__), "moving_hardware_solve.py")):
        shutil.copy2(source, frozen / name)
    (frozen / "prepared-freeze.json").write_bytes(original_freeze)
    save(directory / "freeze.json", {"image": IMAGE, "case": "quiescent", "prepared_directory": str(prepared),
         "inputs_sha256": {p.name: sha(p) for p in frozen.iterdir()}})
    verify(directory)
    if (prepared / "freeze.json").read_bytes() != original_freeze:
        raise ValueError("Prepared manifest changed while freezing solve")
    return directory


def verify(directory):
    frozen = directory / "frozen"
    record = json.loads((directory / "freeze.json").read_text())
    check_frozen(frozen, record)
    return record


def command(directory):
    return ["docker", "run", "--name", "quiescent-" + directory.name,
            "--cidfile", str(directory / "result/container.id"),
            "--network=none", "--read-only", "--memory=4g", "--memory-swap=4g", "--cpus=2",
            "--pids-limit=256", "--tmpfs", "/tmp:size=128m", "-e", "OMP_NUM_THREADS=2",
            "-e", "OPENBLAS_NUM_THREADS=2", "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", f"{directory / 'freeze.json'}:/freeze.json:ro",
            "-v", f"{directory / 'frozen'}:/frozen:ro", "-v", f"{directory / 'result'}:/result",
            "-w", "/result", IMAGE, "timeout", "--signal=TERM", "--kill-after=5", "120",
            "python3", "/frozen/moving_hardware_solve.py", "--execute"]


def launch(directory):
    """A consumed launch sentinel forbids rerunning this frozen bundle."""
    directory = Path(directory).resolve()
    verify(directory)
    freeze_bytes = (directory / "freeze.json").read_bytes()
    cmd = command(directory)
    save(directory / "launch.json", {"command": cmd, "freeze_sha256": sha(directory / "freeze.json"),
                                    "limits": LIMITS, "outer_timeout_seconds": 140})
    result = directory / "result"
    result.mkdir()
    errors, code, cleanup_code, stopped, owned_cid = [], None, None, False, None
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    cleanup_mask = None

    def protect_cleanup():
        nonlocal cleanup_mask
        if cleanup_mask is None:
            cleanup_mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)

    def interrupted(signum, frame):
        protect_cleanup()
        raise KeyboardInterrupt("Received signal " + str(signum))

    try:
        for signum in previous:
            signal.signal(signum, interrupted)
        try:
            with (result / "solver.log").open("xb") as log:
                code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                      timeout=140, check=False).returncode
        except BaseException as error:  # noqa: BLE001 -- interruption must still clean the named container
            errors.append(error)
        finally:
            protect_cleanup()
        try:
            captured = (result / "container.id").read_text().strip()
            if not re.fullmatch(r"[0-9a-f]{64}", captured):
                raise ValueError("Invalid Docker-created container ID; no cleanup authorized")
            owned_cid = captured
        except (OSError, ValueError) as error:
            errors.append(error)
        try:
            if owned_cid is None:
                raise ValueError("No captured owned container ID; inspect and cleanup skipped")
            probe = subprocess.run(["docker", "inspect", owned_cid], capture_output=True, timeout=10, check=False)
            save(result / "container-probe.json", {"returncode": probe.returncode,
                 "stdout": probe.stdout.decode(errors="replace"), "stderr": probe.stderr.decode(errors="replace")})
            inspected = json.loads(probe.stdout)
            if probe.returncode == 0 and len(inspected) == 1:
                container = inspected[0]
                state = container["State"]
                stopped = (container["Id"] == owned_cid and container["Name"] == "/" + cmd[3]
                           and container["Config"]["Image"] == IMAGE
                           and state["Running"] is False and state["ExitCode"] == 0
                           and state.get("OOMKilled") is False)
        except BaseException as error:  # noqa: BLE001 -- inspection failure must not skip cleanup
            errors.append(error)
        try:
            if owned_cid is not None:
                cleanup = subprocess.run(["docker", "rm", "-f", owned_cid], capture_output=True, timeout=10, check=False)
                cleanup_code = cleanup.returncode
                save(result / "cleanup.json", {"returncode": cleanup_code, "container_id": owned_cid,
                     "stdout": cleanup.stdout.decode(errors="replace"), "stderr": cleanup.stderr.decode(errors="replace")})
        except BaseException as error:  # noqa: BLE001 -- retain cleanup failures and partial evidence
            errors.append(error)
        try:
            if (directory / "freeze.json").read_bytes() != freeze_bytes:
                raise ValueError("Freeze manifest changed during launch")
            verify(directory)
        except BaseException as error:  # noqa: BLE001 -- record source drift alongside solver failures
            errors.append(error)
        completed = code == 0 and cleanup_code == 0 and stopped and not errors
        save(result / "exit.json", {"status": "SOLVER COMPLETED; AUDIT PENDING" if completed else "SOLVER OR CLEANUP FAILED",
             "limits": LIMITS, "returncode": code, "cleanup_returncode": cleanup_code,
             "owned_container_id": owned_cid,
             "container_stopped_successfully_before_cleanup": stopped,
             "exceptions": [{"type": type(e).__name__, "message": str(e)} for e in errors],
             "output_sha256": {str(p.relative_to(result)): sha(p) for p in result.rglob("*") if p.is_file()}})
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        if cleanup_mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, cleanup_mask)
    if errors:
        raise errors[0]
    if not completed:
        raise RuntimeError("Quiescent solver/cleanup failed; outputs retained: " + str(result))
    return result


def execute():
    """Container entrypoint: bind build and binary before executing any solver."""
    frozen = Path("/frozen")
    check_frozen(frozen, json.loads(Path("/freeze.json").read_text()))
    build = frozen / "build_manifest.json"
    if build.read_bytes() != Path("/opt/ccx-upstream-2.21/build_manifest.json").read_bytes():
        raise ValueError("Image build manifest differs")
    manifest = json.loads(build.read_text())
    if sha(Path(BINARY)) != manifest["binary_sha256"][BINARY]:
        raise ValueError("Native executable differs")
    shutil.copy2(frozen / "control.inp", "/result/control.inp")
    os.execv(BINARY, [BINARY, "control"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", type=Path, help="freeze a prepared quiescent control without launching")
    action.add_argument("--launch", type=Path)
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("fea/generated/quiescent-solves"))
    args = parser.parse_args()
    if args.execute:
        execute()
    elif args.launch:
        print(launch(args.launch))
    else:
        print(prepare(args.prepare, args.output))
