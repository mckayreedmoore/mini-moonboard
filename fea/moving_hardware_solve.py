"""Freeze and explicitly launch one bounded hardware control; no qualification."""

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
MOVING_LIMITS = "Coarse moving solver completion only; complete moving audit and refinement pending. No contact or physical acceptance."
QUIET_ARCHIVE_SHA = "0149053d26aa67e1c5f2d22de7e9b1e058d24f7188ef02324fe3cc6508bb86ea"
MASS_FILES = {"context.json", "prepared-freeze.json", "moving.inp", "report.json", "blocks.json.gz",
              "hardware_mass_cache.py.snapshot", "dynamic_momentum.py.snapshot"}
REQUIRED_EVALUATORS = {"moving_hardware_audit.py", "test_moving_hardware_audit.py", "moving_hardware_replay.py",
                       "test_moving_hardware_replay.py", "moving_hardware_balance.py", "test_moving_hardware_balance.py",
                       "floor_contact_results.py", "quiescent_hardware_audit.py", "quiescent_hardware_diagnostic.py",
                       "dynamic_momentum.py", "hardware_mass_cache.py", "moving_hardware_control.py"}


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
    case = record["case"]
    check_timeout(record.get("solver_timeout_seconds", 120), case=case)
    expected = {"moving_hardware_solve.py", "control.inp", "context.json", "build_manifest.json", "prepared-freeze.json"}
    if case == "moving":
        if {p.relative_to(frozen).as_posix() for p in frozen.rglob("*") if p.is_file()} != set(record["inputs_sha256"]):
            raise ValueError("Moving frozen directory inventory differs")
        approval = json.loads((frozen / "moving-preflight.json").read_text())
        extras = set(approval["inputs_sha256"]) - expected
        evaluators = set(approval["evaluator_sha256"])
        if (not {"evaluators/" + n + ".snapshot" for n in REQUIRED_EVALUATORS} <= evaluators
                or extras != evaluators | {"mass/" + n for n in MASS_FILES}
                or any(Path(n).is_absolute() or ".." in Path(n).parts for n in extras)):
            raise ValueError("Moving preflight source/mass inventory differs")
        expected |= extras | {"moving-preflight.json"}
        if approval["inputs_sha256"] != {n: h for n, h in record["inputs_sha256"].items() if n != "moving-preflight.json"}:
            raise ValueError("Moving preflight approved input hashes differ")
    if record["image"] != IMAGE or set(record["inputs_sha256"]) != expected:
        raise ValueError("Wrong frozen control inventory or image")
    if any(sha(frozen / name) != digest for name, digest in record["inputs_sha256"].items()):
        raise ValueError("Frozen input changed")
    if (sha(Path(__file__)) != LOADED_SOURCE_SHA256 or
            LOADED_SOURCE_SHA256 != record["inputs_sha256"]["moving_hardware_solve.py"]):
        raise ValueError("Executing launcher differs from frozen source")
    context = json.loads((frozen / "context.json").read_text())
    check_reference(context)
    prepared = json.loads((frozen / "prepared-freeze.json").read_text())["files_sha256"]
    if (prepared["context.json"] != sha(frozen / "context.json") or
            prepared[case + ".inp"] != sha(frozen / "control.inp") or
            context["deck_sha256"][case] != sha(frozen / "control.inp")):
        raise ValueError("Prepared context/deck identity differs")
    if case == "moving":
        check_moving_context(context)
        if (approval["case"] != "moving" or approval["context_sha256"] != sha(frozen / "context.json")
                or approval["deck_sha256"] != sha(frozen / "control.inp")
                or approval["prepared_freeze_sha256"] != sha(frozen / "prepared-freeze.json")
                or approval["passed_quiet_archive_sha256"] != QUIET_ARCHIVE_SHA
                or approval["mass_report_sha256"] != sha(frozen / "mass/report.json")
                or approval["mass_blocks_sha256"] != sha(frozen / "mass/blocks.json.gz")
                or any(record["inputs_sha256"][n] != h for n, h in approval["evaluator_sha256"].items())):
            raise ValueError("Moving preflight identity differs")


def check_timeout(seconds, *, case="quiescent"):
    if type(case) is not str or case not in ("quiescent", "moving"):
        raise ValueError("Explicit case must be quiescent or moving")
    if type(seconds) is not int or seconds not in ((1800,) if case == "moving" else (120, 180)):
        raise ValueError("Only predeclared case-specific solver caps are supported")
    return seconds


def check_moving_context(context):
    """Small stdlib child guard; full geometry/protocol replay occurs on the host."""
    if (context.get("cases") != {"moving": {"initial_dt_s": 1e-7, "total_time_s": 2e-5,
            "maximum_increment_count": 200, "alpha": 0., "direct_moving": True,
            "initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": [-100., 100., 0.]}}}
            or context.get("passed_quiet_evidence", {}).get("archive_sha256") != QUIET_ARCHIVE_SHA
            or context.get("angular_reference_mm_local") != [1.001, .7356, 0.]
            or context.get("moving_protocol", {}).get("solver_timeout_seconds") != 1800
            or context.get("moving_protocol", {}).get("outer_timeout_seconds") != 1820):
        raise ValueError("Unsupported coarse moving context")


def moving_preflight(prepared, context, mass_directory):
    """Host-only pure replay; freeze its approval for the stdlib container entrypoint."""
    import gzip

    from fea import hardware_mass_cache as mass
    from fea import moving_hardware_event as event

    if mass_directory is None:
        raise ValueError("Moving launch preparation requires an explicit mass_directory")
    check_moving_context(context)
    sources = event.sources()
    if not REQUIRED_EVALUATORS <= set(sources):
        raise ValueError("Complete moving evaluator source/test closure is not prepared")
    if context["source_sha256"] != {n: hashlib.sha256(b).hexdigest() for n, b in sources.items()}:
        raise ValueError("Moving event evaluator/source snapshot differs from current preflight")
    for name, data in sources.items():
        if (prepared / "frozen" / name).read_bytes() != data:
            raise ValueError("Prepared moving source bytes differ")
    archive = (prepared / "frozen/posed-quiet.tar.gz").read_bytes()
    document_bytes = (prepared / "frozen/moving-hardware-control.md").read_bytes()
    document = document_bytes.decode()
    if document.count(event.SECTION) != 1:
        raise ValueError("Moving protocol section differs")
    protocol = event.SECTION + document.split(event.SECTION, 1)[1]
    expected = event.build_context(event.archived_files(archive), protocol)
    expected["input_sha256"] = {"posed-quiet.tar.gz": hashlib.sha256(archive).hexdigest(),
                                "moving-hardware-control.md": hashlib.sha256(document_bytes).hexdigest()}
    expected["source_sha256"] = {n: hashlib.sha256(b).hexdigest() for n, b in sources.items()}
    expected["audit_source_sha256"] = {Path(n).name: expected["source_sha256"][Path(n).name] for n in event.EVALUATOR_FILES}
    expected["deck_sha256"] = {"moving": hashlib.sha256(event.control.deck(expected, "moving").encode()).hexdigest()}
    if expected != context or event.control.deck(context, "moving").encode() != (prepared / "moving.inp").read_bytes():
        raise ValueError("Moving event context/deck differs from passed proof and protocol")
    if context["audit_source_sha256"] != {Path(n).name: context["source_sha256"][Path(n).name] for n in event.EVALUATOR_FILES}:
        raise ValueError("Moving audit source declaration differs")
    directory = Path(mass_directory)
    if {p.name for p in directory.iterdir() if p.is_file()} != MASS_FILES or any(p.is_dir() for p in directory.iterdir()):
        raise ValueError("Unexpected selected moving mass-cache inventory")
    cached = {n: (directory / n).read_bytes() for n in MASS_FILES}
    data = (prepared / "context.json").read_bytes()
    report = json.loads(cached["report.json"])
    if (cached["context.json"] != data or cached["moving.inp"] != (prepared / "moving.inp").read_bytes()
            or cached["prepared-freeze.json"] != (prepared / "freeze.json").read_bytes()
            or report.get("case") != "moving"
            or report["context_sha256"] != hashlib.sha256(data).hexdigest()
            or report["prepared_freeze_sha256"] != hashlib.sha256(cached["prepared-freeze.json"]).hexdigest()
            or report["deck_sha256"] != hashlib.sha256(cached["moving.inp"]).hexdigest()
            or report["blocks_sha256"] != hashlib.sha256(cached["blocks.json.gz"]).hexdigest()):
        raise ValueError("Selected moving mass-cache identity differs")
    cache = json.loads(gzip.decompress(cached["blocks.json.gz"]))
    masses = mass.validate_cache(cache, data)
    if masses != report["body_mass_tonne"] or cache["gmsh_version"] != report["gmsh_version"]:
        raise ValueError("Selected moving mass-cache totals/version differ")
    if not math.isclose(masses["native_four_point"]["WASHER"],
                        context["diagnostic_reference_scales"]["reference_mass_tonne"], rel_tol=1e-12, abs_tol=0.):
        raise ValueError("Selected native washer mass differs from declared reference")
    if report["source_sha256"] != {n: hashlib.sha256(b).hexdigest() for n, b in mass.sources().items()}:
        raise ValueError("Selected moving mass-cache source differs")
    if any(cached[n + ".snapshot"] != b for n, b in mass.sources().items()):
        raise ValueError("Selected moving mass-cache source bytes differ")
    if event.sources() != sources or any((directory / n).read_bytes() != b for n, b in cached.items()):
        raise ValueError("Moving preflight source/cache drift")
    extras = {"evaluators/" + n + ".snapshot": b for n, b in sources.items()}
    extras.update({"mass/" + n: b for n, b in cached.items()})
    approval = {"case": "moving", "context_sha256": hashlib.sha256(data).hexdigest(),
        "deck_sha256": hashlib.sha256(cached["moving.inp"]).hexdigest(),
        "prepared_freeze_sha256": hashlib.sha256(cached["prepared-freeze.json"]).hexdigest(),
        "passed_quiet_archive_sha256": QUIET_ARCHIVE_SHA,
        "mass_report_sha256": hashlib.sha256(cached["report.json"]).hexdigest(),
        "mass_blocks_sha256": hashlib.sha256(cached["blocks.json.gz"]).hexdigest(),
        "evaluator_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in extras.items() if n.startswith("evaluators/")}}
    return extras, approval


def prepare(prepared, parent=Path("fea/generated/quiescent-solves"), *, solver_timeout_seconds=120,
            case="quiescent", mass_directory=None):
    """Copy an explicitly selected verified deck into a new, unlaunched bundle."""
    check_timeout(solver_timeout_seconds, case=case)
    if case == "quiescent" and mass_directory is not None:
        raise ValueError("mass_directory is moving-only")
    prepared = Path(prepared).resolve()
    original_freeze = (prepared / "freeze.json").read_bytes()
    inventory = json.loads(original_freeze)["files_sha256"]
    if case == "moving" and {p.relative_to(prepared).as_posix() for p in prepared.rglob("*") if p.is_file()} != set(inventory) | {"freeze.json"}:
        raise ValueError("Prepared moving directory inventory differs")
    for name, expected in inventory.items():
        path = (prepared / name).resolve()
        if not path.is_relative_to(prepared) or sha(path) != expected:
            raise ValueError("Prepared provenance changed: " + name)
    context = json.loads((prepared / "context.json").read_text())
    check_reference(context)
    if case not in context["cases"]:
        raise ValueError("Explicit selected prepared case is absent")
    if case == "quiescent" and any(v != [0., 0., 0.] for v in context["cases"]["quiescent"]["initial_velocity_mm_s"].values()):
        raise ValueError("Only the prepared quiescent control may launch")
    for group in ("input_sha256", "source_sha256"):
        if any(inventory.get("frozen/" + name) != expected for name, expected in context[group].items()):
            raise ValueError("Prepared source/input manifest differs")
    if (inventory.get("context.json") != sha(prepared / "context.json") or
            inventory.get(case + ".inp") != context["deck_sha256"][case]):
        raise ValueError("Prepared selected context/deck identity differs")
    extras, approval = moving_preflight(prepared, context, mass_directory) if case == "moving" else ({}, None)
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=case + "-", dir=parent)).resolve()
    frozen = directory / "frozen"
    frozen.mkdir()
    for source, name in ((prepared / (case + ".inp"), "control.inp"), (prepared / "context.json", "context.json"),
                         (BUILD, "build_manifest.json"), (Path(__file__), "moving_hardware_solve.py")):
        shutil.copy2(source, frozen / name)
    (frozen / "prepared-freeze.json").write_bytes(original_freeze)
    for name, data in extras.items():
        target = frozen / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if approval is not None:
        approval["inputs_sha256"] = {p.relative_to(frozen).as_posix(): sha(p) for p in frozen.rglob("*") if p.is_file()}
        save(frozen / "moving-preflight.json", approval)
    if (prepared / "freeze.json").read_bytes() != original_freeze or any(sha(prepared / n) != h for n, h in inventory.items()):
        raise ValueError("Prepared inputs changed while freezing solve; no launchable freeze")
    if sha(Path(__file__)) != LOADED_SOURCE_SHA256:
        raise ValueError("Executing launcher source changed; no launchable freeze")
    for name, data in extras.items():
        if name.startswith("evaluators/"):
            basename = Path(name).name.removesuffix(".snapshot")
            path = ROOT / ("tests" if basename.startswith("test_") else "fea") / basename
            if path.read_bytes() != data:
                raise ValueError("Moving evaluator source changed; no launchable freeze")
    record = {"image": IMAGE, "case": case, "prepared_directory": str(prepared),
         "solver_timeout_seconds": solver_timeout_seconds,
         "inputs_sha256": {p.relative_to(frozen).as_posix(): sha(p) for p in frozen.rglob("*") if p.is_file()}}
    check_frozen(frozen, record)
    save(directory / "freeze.json", record)
    return directory


def verify(directory):
    frozen = directory / "frozen"
    record = json.loads((directory / "freeze.json").read_text())
    check_frozen(frozen, record)
    return record


def command(directory, *, solver_timeout_seconds=120, case="quiescent"):
    check_timeout(solver_timeout_seconds, case=case)
    return ["docker", "run", "--name", case + "-" + directory.name,
            "--cidfile", str(directory / "result/container.id"),
            "--network=none", "--read-only", "--memory=4g", "--memory-swap=4g", "--cpus=2",
            "--pids-limit=256", "--tmpfs", "/tmp:size=128m", "-e", "OMP_NUM_THREADS=2",
            "-e", "OPENBLAS_NUM_THREADS=2", "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", f"{directory / 'freeze.json'}:/freeze.json:ro",
            "-v", f"{directory / 'frozen'}:/frozen:ro", "-v", f"{directory / 'result'}:/result",
            "-w", "/result", IMAGE, "timeout", "--signal=TERM", "--kill-after=5", str(solver_timeout_seconds),
            "python3", "/frozen/moving_hardware_solve.py", "--execute"]


def launch(directory):
    """A consumed launch sentinel forbids rerunning this frozen bundle."""
    directory = Path(directory).resolve()
    record = verify(directory)
    freeze_bytes = (directory / "freeze.json").read_bytes()
    case = record["case"]
    seconds = check_timeout(record.get("solver_timeout_seconds", 120), case=case)
    cmd = command(directory, solver_timeout_seconds=seconds, case=case)
    limits = MOVING_LIMITS if case == "moving" else LIMITS
    save(directory / "launch.json", {"command": cmd, "freeze_sha256": sha(directory / "freeze.json"),
                                    "limits": limits, "outer_timeout_seconds": seconds + 20})
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
                                      timeout=seconds + 20, check=False).returncode
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
             "limits": limits, "returncode": code, "cleanup_returncode": cleanup_code,
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
        raise RuntimeError(case + " solver/cleanup failed; outputs retained: " + str(result))
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
    action.add_argument("--prepare", type=Path, help="freeze an explicitly selected prepared control without launching")
    action.add_argument("--launch", type=Path)
    action.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("fea/generated/quiescent-solves"))
    parser.add_argument("--case", choices=("quiescent", "moving"), default="quiescent", help="preparation-only explicit case selection")
    parser.add_argument("--mass-directory", type=Path, help="preparation-only moving context-bound mass cache")
    parser.add_argument("--solver-timeout-seconds", type=int, choices=(120, 180, 1800), default=120,
                        help="preparation-only immutable solver cap; existing bundles retain their frozen cap")
    args = parser.parse_args()
    if args.prepare is None and (args.solver_timeout_seconds != 120 or args.case != "quiescent" or args.mass_directory is not None):
        parser.error("case, mass directory and solver-timeout-seconds are preparation-only; launch uses the frozen selection")
    if args.execute:
        execute()
    elif args.launch:
        print(launch(args.launch))
    else:
        print(prepare(args.prepare, args.output, solver_timeout_seconds=args.solver_timeout_seconds,
                      case=args.case, mass_directory=args.mass_directory))
