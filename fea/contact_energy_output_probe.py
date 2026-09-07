"""Prepare a direct call to unmodified native CELS printing; not a solver test."""
import argparse
import hashlib
import io
import json
import re
import signal
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "fea/results/native_dynamic_control/control-ajgbgzoh.tar.gz"
ARCHIVE_SHA = "62eb6870736d979993b5e8c0096f8426a90f8db41e5a621fc2398e806460ce79"
BUILD_SHA = "04b8da67a5edf12c763e03c9a4c3da241375c8d7a37c07eec06e2b31a4622988"
IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
FILES = ("printoutelem.f", "gauss.f", "nonlingeo.c", "gencontelem_f2f.f", "resultsmech.f",
         "results.c", "resultsprint.f", "printout.f")
STUBS = ("beamintscheme", "linscal10", "lintemp", "lintemp_th1", "materialdata_rho", "nident2",
         "shape10tet", "shape15w", "shape20h", "shape4tet", "shape6tri", "shape6w", "shape8h",
         "shape8hr", "shape8hu", "shape8q")
LIMITS = ("Native output-reader probe only. Energy-array inputs are controlled fixtures, not calculated spring energies. "
          "No execution of resultsmech/contact generation, actual moving-row mapping, corrected native solver, "
          "contact-energy qualification or capacity claim.")
COMPILE = ["gfortran", "-O0", "-g", "-fcheck=all", "-fallow-argument-mismatch", "-I/frozen",
           "/frozen/printoutelem.f", "/frozen/driver.f90", "/frozen/stubs.f90", "-o", "/result/energy-reader"]
DRIVER = """program contact_energy_output_probe
  implicit none
  integer :: mi(3)=(/4,3,1/), ipkon(8)=0, kon(32)=0, ielmat(1,8)=1
  integer :: ielprop(8)=0, nelemload(2,1)=0, ithermal(2)=0, nrhcon(1)=0
  integer :: ipobody(2,8)=0, ibody(3,1)=0
  integer :: ii=1, nelem=2, ne=2, nodes=0, ielem=101, iface=2, mortar=1
  integer :: nload=0, ntmat=1, nbody=0, case_id, igauss, j
  integer, parameter :: original_extent=1
  character(len=6) :: prlab(1)='CELS  '
  character(len=8) :: lakon(8)='C3D10   '
  character(len=20) :: sideload(1)=' '
  real(8) :: ener(2,4,8)=0, co(3,12)=0, stx(6,4,8)=0, thicke(1,32)=0
  real(8) :: prop(1)=0, xload(2,1)=0, rhcon(0:1,1,1)=0, t1(12)=0
  real(8) :: vold(0:3,12)=0, xbody(7,1)=0
  real(8) :: energytot=0, volumetot=0, enerkintot=0, bhetot=0, xmasstot=0
  real(8) :: xinertot(6)=0, cg(3)=0
  ! ESPRNGC6 matches an ordinary TRI6-to-TRI6 S2S contact element.
  lakon(nelem)='ESPRNGC6'
  ipkon(nelem)=1
  kon(1)=12
  do j=1,12
    kon(j+1)=j
  enddo
  close(5)
  open(5,file='probe.dat',status='new',action='write')
  do case_id=1,3
    igauss=7
    if(case_id==1) igauss=1
    kon(14)=igauss
    kon(15)=1
    kon(16)=igauss
    ener=0
    ! Controlled setup mirrors the documented writer layout, not its execution.
    ener(1,1,original_extent+igauss)=7.5d0
    if(case_id==3) ener(1,1,nelem)=2.25d0
    energytot=0
    call printoutelem(prlab,ipkon,lakon,kon,co,ener,mi,ii,nelem, &
      energytot,volumetot,enerkintot,ne,stx,nodes,thicke,ielmat, &
      ielem,iface,mortar,ielprop,prop,sideload,nload,nelemload,xload, &
      bhetot,xmasstot,xinertot,cg,ithermal,rhcon,nrhcon,ntmat,t1, &
      vold,ipobody,ibody,xbody,nbody)
    write(6,'(4(i0,1x),3(es24.16,1x))') case_id,nelem,igauss, &
      original_extent+igauss,ener(1,1,original_extent+igauss), &
      ener(1,1,nelem),energytot
  enddo
  close(5)
end program
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stub_source():
    return "\n".join(f"subroutine {name}()\n  implicit none\n  error stop 'UNREACHABLE {name}'\nend subroutine\n" for name in STUBS)


LOADED_SOURCE_SHA = digest(Path(__file__).read_bytes())
DECLARED_CONFIG = (IMAGE, FILES, STUBS, LIMITS, DRIVER, tuple(COMPILE), ARCHIVE_SHA, BUILD_SHA)


def upstream_inputs(data):
    if digest(data) != ARCHIVE_SHA:
        raise ValueError("Pinned upstream evidence archive differs")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if any(not member.isfile() for member in members) or len({m.name for m in members}) != len(members):
            raise ValueError("Unexpected upstream archive inventory")
        return {**{name: archive.extractfile("frozen/native-source/" + name).read() for name in FILES},
                "build_manifest.json": archive.extractfile("frozen/build_manifest.json").read()}


def prepare(parent=ROOT / "fea/generated/contact-energy-output-probes"):
    own = Path(__file__).resolve()
    if digest(own.read_bytes()) != LOADED_SOURCE_SHA or (IMAGE, FILES, STUBS, LIMITS, DRIVER, tuple(COMPILE), ARCHIVE_SHA, BUILD_SHA) != DECLARED_CONFIG:
        raise ValueError("Loaded probe source/configuration changed")
    archive_bytes = ARCHIVE.read_bytes()
    captured = upstream_inputs(archive_bytes)
    build_bytes = captured.pop("build_manifest.json")
    if digest(build_bytes) != BUILD_SHA:
        raise ValueError("Pinned native build manifest differs")
    build = json.loads(build_bytes)
    for name, data in captured.items():
        if digest(data) != build["upstream_files_sha256"]["./CalculiX/ccx_2.21/src/" + name]:
            raise ValueError("Original upstream source differs: " + name)
    calls = set(re.findall(r"\bcall\s+(\w+)", captured["printoutelem.f"].decode(), re.IGNORECASE))
    if calls != set(STUBS):
        raise ValueError("Unreachable dependency inventory changed")
    sources = {"contact_energy_output_probe.py": own.read_bytes(),
               "test_contact_energy_output_probe.py": (ROOT / "tests/test_contact_energy_output_probe.py").read_bytes()}
    inputs = {**captured, **sources, "build_manifest.json": build_bytes,
              "driver.f90": DRIVER.encode(), "stubs.f90": stub_source().encode(),
              "COPYING": (ROOT / "fea/results/native_dynamic_control/COPYING").read_bytes()}
    Path(parent).mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="energy-reader-", dir=parent))
    for name, data in inputs.items():
        (directory / name).write_bytes(data)
    if (ARCHIVE.read_bytes() != archive_bytes or own.read_bytes() != sources[own.name]
            or (ROOT / "tests/test_contact_energy_output_probe.py").read_bytes() != sources["test_contact_energy_output_probe.py"]):
        raise ValueError("Probe source drift; no execution-ready manifest")
    manifest = {"status": "PREPARED ONLY; NOT BUILT OR EXECUTED", "limits": LIMITS,
                "image": IMAGE, "memory_bytes": 2 * 1024**3, "cpus": 1,
                "source_build_manifest_sha256": BUILD_SHA,
                "upstream_evidence_archive_sha256": ARCHIVE_SHA,
                "compiler_timeout_seconds": 30, "driver_timeout_seconds": 5,
                "inner_timeout_seconds": 45, "outer_timeout_seconds": 65,
                "compile_command": COMPILE,
                "run_command": ["/result/energy-reader"],
                "files_sha256": {name: digest(data) for name, data in inputs.items()},
                "cases": [{"name": "dense", "igauss": 1, "writer_slot": 2, "compact_slot": 2, "expected_CELS": 7.5},
                          {"name": "sparse_zero", "igauss": 7, "writer_slot": 8, "compact_slot": 2, "expected_CELS": 0.},
                          {"name": "sparse_other_slot", "igauss": 7, "writer_slot": 8, "compact_slot": 2, "expected_CELS": 2.25}]}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return directory


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify(directory):
    if (IMAGE, FILES, STUBS, LIMITS, DRIVER, tuple(COMPILE), ARCHIVE_SHA, BUILD_SHA) != DECLARED_CONFIG:
        raise ValueError("Loaded probe configuration changed")
    manifest = json.loads((directory / "manifest.json").read_bytes())
    expected = set(FILES) | {"contact_energy_output_probe.py", "test_contact_energy_output_probe.py",
                            "build_manifest.json", "driver.f90", "stubs.f90", "COPYING"}
    if set(manifest["files_sha256"]) != expected or any(digest((directory / n).read_bytes()) != h for n, h in manifest["files_sha256"].items()):
        raise ValueError("Frozen probe input changed")
    if (manifest["files_sha256"]["contact_energy_output_probe.py"] != LOADED_SOURCE_SHA
            or digest(Path(__file__).read_bytes()) != LOADED_SOURCE_SHA):
        raise ValueError("Executing probe differs from frozen source")
    if (manifest["image"] != IMAGE or manifest["memory_bytes"] != 2*1024**3 or manifest["cpus"] != 1
            or [manifest[k] for k in ("compiler_timeout_seconds", "driver_timeout_seconds", "inner_timeout_seconds", "outer_timeout_seconds")] != [30, 5, 45, 65]
            or digest((directory / "build_manifest.json").read_bytes()) != BUILD_SHA):
        raise ValueError("Pinned probe build or bounds differ")
    if manifest["compile_command"] != COMPILE or manifest["run_command"] != ["/result/energy-reader"]:
        raise ValueError("Only the declared printer compilation and probe executable may run")
    build = json.loads((directory / "build_manifest.json").read_bytes())
    if (any(manifest["files_sha256"][n] != build["upstream_files_sha256"]["./CalculiX/ccx_2.21/src/" + n] for n in FILES)
            or (directory / "driver.f90").read_bytes() != DRIVER.encode()
            or (directory / "stubs.f90").read_bytes() != stub_source().encode()):
        raise ValueError("Pinned original source or controlled driver/stubs differ")
    return manifest


def execute(frozen=Path("/frozen"), result=Path("/result")):
    """Worker entrypoint: compile only the native printer, never invoke CCX."""
    manifest = verify(frozen)
    original = (frozen / "manifest.json").read_bytes()
    commands, error = [], None
    try:
        build = (frozen / "build_manifest.json").read_bytes()
        if build != Path("/opt/ccx-upstream-2.21/build_manifest.json").read_bytes():
            raise ValueError("Pinned image build manifest differs")
        for label, cmd, seconds in (("compiler-version", ["gfortran", "--version"], 5),
                ("compiler", manifest["compile_command"], 30), ("driver", manifest["run_command"], 5)):
            commands.append({"label": label, "command": cmd, "timeout_seconds": seconds})
            with (result / (label + ".log")).open("xb") as log:
                code = subprocess.run(cmd, cwd=result, stdout=log, stderr=subprocess.STDOUT, timeout=seconds, check=False).returncode
            commands[-1]["returncode"] = code
            if code != 0:
                raise RuntimeError(label + " failed; no retry")
            if label == "compiler-version" and (result / "compiler-version.log").read_text() != json.loads(build)["compiler_versions"]["gfortran"]:
                raise ValueError("Compiler version differs from pinned build")
        rows = [(int(e), int(f), float(v)) for e, f, v in (line.split() for line in (result / "probe.dat").read_text().splitlines())]
        if rows != [(101, 2, v) for v in (7.5, 0., 2.25)]:
            raise ValueError("Native printer observations differ from declared cases")
        metadata = [line.split() for line in (result / "driver.log").read_text().splitlines()]
        expected = [[str(i), "2", str(g), str(1+g), "7.5", str(v), str(v)]
                    for i, g, v in ((1, 1, 7.5), (2, 7, 0.), (3, 7, 2.25))]
        if len(metadata) != 3 or any([float(x) for x in a] != [float(x) for x in b] for a, b in zip(metadata, expected, strict=True)):
            raise ValueError("Driver slot metadata or native total differs")
    except BaseException as caught:  # noqa: BLE001 -- preserve failed compile/runtime evidence
        error = caught
    try:
        verify(frozen)
        if (frozen / "manifest.json").read_bytes() != original:
            raise ValueError("Probe manifest changed during execution")
    except BaseException as caught:  # noqa: BLE001 -- retain provenance failure
        error = caught
    save(result / "worker-exit.json", {"status": "NATIVE READER CASES OBSERVED" if error is None else "PROBE FAILED",
        "limits": LIMITS, "commands": commands,
        "exception": None if error is None else {"type": type(error).__name__, "message": str(error)},
        "output_sha256": {p.name: digest(p.read_bytes()) for p in result.iterdir()
                          if p.name in ("compiler-version.log", "compiler.log", "driver.log", "probe.dat", "energy-reader")}})
    if error is not None:
        raise error


def command(directory):
    return ["docker", "run", "--name", "energy-reader-" + directory.name,
        "--cidfile", str(directory / "run/container.id"), "--network=none", "--read-only",
        "--memory=2g", "--memory-swap=2g", "--cpus=1", "--pids-limit=128", "--tmpfs", "/tmp:size=128m",
        "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{directory}:/frozen:ro",
        "-v", f"{directory / 'run'}:/result", "-w", "/result", IMAGE,
        "timeout", "--signal=TERM", "--kill-after=5", "45", "python3", "/frozen/contact_energy_output_probe.py", "--execute"]


def launch(directory):
    """Single-use bounded diagnostic; captured-CID cleanup on every exit path."""
    directory = Path(directory).resolve()
    verify(directory)
    frozen_manifest = (directory / "manifest.json").read_bytes()
    result = directory / "run"
    result.mkdir()  # Exclusive single-use sentinel; no automatic retry.
    cmd = command(directory)
    save(result / "launch.json", {"command": cmd, "manifest_sha256": digest(frozen_manifest), "outer_timeout_seconds": 65})
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    mask, errors, code, cid, stopped, cleaned = None, [], None, None, False, False
    def protect():
        nonlocal mask
        if mask is None:
            mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
    def interrupted(signum, frame):
        protect()
        raise KeyboardInterrupt("Probe interrupted by signal " + str(signum))
    try:
        for signum in previous:
            signal.signal(signum, interrupted)
        try:
            with (result / "container.log").open("xb") as log:
                code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=65, check=False).returncode
        except BaseException as error:  # noqa: BLE001 -- cleanup must survive interruption
            errors.append(error)
        finally:
            protect()
        try:
            cid = (result / "container.id").read_text().strip()
            if not re.fullmatch(r"[0-9a-f]{64}", cid):
                cid = None
                raise ValueError("Invalid owned CID; no cleanup authorized")
            probe = subprocess.run(["docker", "inspect", cid], capture_output=True, timeout=10, check=False)
            save(result / "container-inspect.json", {"returncode": probe.returncode,
                "stdout": probe.stdout.decode(), "stderr": probe.stderr.decode()})
            records = json.loads(probe.stdout)
            if probe.returncode == 0 and len(records) == 1:
                item = records[0]
                stopped = (item["Id"] == cid and item["Name"] == "/" + cmd[3] and item["Config"]["Image"] == IMAGE
                           and item["State"]["Running"] is False and item["State"]["ExitCode"] == 0 and item["State"]["OOMKilled"] is False)
        except BaseException as error:  # noqa: BLE001 -- inspect failure must not skip owned cleanup
            errors.append(error)
        try:
            if cid is not None:
                cleanup = subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=10, check=False)
                save(result / "cleanup.json", {"returncode": cleanup.returncode, "container_id": cid,
                    "stdout": cleanup.stdout.decode(), "stderr": cleanup.stderr.decode()})
                cleaned = cleanup.returncode == 0
        except BaseException as error:  # noqa: BLE001 -- record cleanup failures
            errors.append(error)
        try:
            verify(directory)
            if (directory / "manifest.json").read_bytes() != frozen_manifest:
                raise ValueError("Frozen manifest changed during launch")
            if json.loads((result / "worker-exit.json").read_bytes())["status"] != "NATIVE READER CASES OBSERVED":
                raise ValueError("Native reader worker did not complete")
        except BaseException as error:  # noqa: BLE001 -- preserve all failure evidence
            errors.append(error)
        complete = code == 0 and stopped and cleaned and not errors
        save(result / "exit.json", {"status": "NATIVE READER PROBE COMPLETED" if complete else "PROBE OR CLEANUP FAILED",
            "limits": LIMITS, "returncode": code, "owned_container_id": cid, "stopped_successfully": stopped,
            "cleanup_success": cleaned, "exceptions": [{"type": type(e).__name__, "message": str(e)} for e in errors],
            "output_sha256": {p.name: digest(p.read_bytes()) for p in result.iterdir() if p.is_file()}})
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        if mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    if errors:
        raise errors[0]
    if not complete:
        raise RuntimeError("Probe or cleanup failed; no automatic retry")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--execute", action="store_true")
    action.add_argument("--launch", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "fea/generated/contact-energy-output-probes")
    args = parser.parse_args()
    if args.execute:
        execute()
    elif args.launch:
        print(launch(args.launch))
    else:
        print(prepare(args.output))
