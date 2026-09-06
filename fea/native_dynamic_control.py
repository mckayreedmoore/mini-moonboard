"""Bounded native C3D10 output control; arbitrary consistent units, no material claim.

Default invocation only freezes four decks and their provenance. Launch requires
an explicit --launch DIRECTORY invocation after review. No frame/contact solve.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
BINARY = "/usr/local/bin/ccx-upstream-2.21"
SOURCE = Path("/tmp/contact-source-2.21/CalculiX/ccx_2.21/src")
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "fea/mortar_build/baseline-njusw3dz/build_manifest.json"
CASES = ("straight-linear", "curved-linear", "straight-nlgeom", "curved-nlgeom")
KE_FLOOR = 1e-8  # Arbitrary consistent control energy units, not a physical limit.
ENERGY_CONTRAST_MIN = 1e-3
AFFINE_RESIDUAL_MIN = 1e-3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nodes(curved=False):
    corners = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    points = corners + [tuple((corners[a][i] + corners[b][i])/2 for i in range(3))
                        for a, b in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
    if curved:
        points[4] = (.5, -.06, -.025)
        points[8] = (.53, .02, .51)
    return dict(enumerate(points, 1))


def deck(case):
    if case not in CASES:
        raise ValueError("Unknown control case")
    xyz = nodes(case.startswith("curved"))
    lines = ["*HEADING", "Native mass/output qualification only; arbitrary consistent units", "*NODE,NSET=BODY"]
    lines += [f"{n}," + ",".join(map(str, p)) for n, p in xyz.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=BODY", "1,1,2,3,4,5,6,7,8,9,10",
              "*MATERIAL,NAME=CONTROL", "*ELASTIC", "1.,0.3", "*DENSITY", "1.",
              "*SOLID SECTION,ELSET=BODY,MATERIAL=CONTROL", "*INITIAL CONDITIONS,TYPE=VELOCITY"]
    lines += [f"{n},{axis},{1 if n == 1 and axis == 1 else 0}." for n in xyz for axis in (1, 2, 3)]
    lines += ["*STEP,INC=100" + (",NLGEOM" if case.endswith("nlgeom") else ""),
              # dynamics.f treats any EXPLICIT prefix, including =0, as explicit.
              "*DYNAMIC,ALPHA=0", "1.e-3,1.e-3,1.e-8,1.e-3",
              "*NODE PRINT,NSET=BODY,FREQUENCY=1", "U,V",
              "*EL PRINT,ELSET=BODY,FREQUENCY=1,TOTALS=ONLY", "ELKE,EMAS,ELSE", "*END STEP"]
    return "\n".join(lines) + "\n"


def parse_dat(text):
    """Read matched BODY states only; reject missing/duplicate/nonfinite data."""
    headers = {"displacements (": "U", "velocities (": "V",
               "total kinetic energy for set ": "ELKE", "total mass for set ": "EMAS",
               "total internal energy for set ": "ELSE"}
    states, active = {}, None
    for line in text.splitlines():
        clean = line.strip().lower()
        if "for set" in clean and "and time" in clean:
            active = None
            for prefix, field in headers.items():
                if clean.startswith(prefix) and re.search(r"for set\s+body\s+and time", clean):
                    time = float(clean.split("and time")[1].replace("d", "e"))
                    if not math.isfinite(time) or time <= 0:
                        raise ValueError("Native output times must be finite and positive")
                    state = states.setdefault(time, {})
                    if field in state:
                        raise ValueError("Duplicate native output field")
                    state[field] = {} if field in ("U", "V") else None
                    active = (state, field)
                    break
        elif active and clean:
            state, field = active
            parts = clean.replace("d", "e").split()
            if field in ("U", "V"):
                if len(parts) != 4:
                    raise ValueError("Malformed native vector row")
                tag = int(parts[0])
                if tag in state[field]:
                    raise ValueError("Duplicate native node")
                state[field][tag] = tuple(map(float, parts[1:]))
            else:
                if len(parts) != 1:
                    raise ValueError("Malformed native scalar row")
                state[field] = float(parts[0])
                active = None
    if not states:
        raise ValueError("No native states")
    for time, state in states.items():
        if set(state) != {"U", "V", "ELKE", "EMAS", "ELSE"}:
            raise ValueError("Incomplete native fields")
        if any(set(state[k]) != set(range(1, 11)) for k in ("U", "V")):
            raise ValueError("Incomplete native nodes")
        values = [time, state["ELKE"], state["EMAS"], state["ELSE"]]
        values += [x for k in ("U", "V") for v in state[k].values() for x in v]
        if any(v is None or not math.isfinite(v) for v in values):
            raise ValueError("Nonfinite native output")
        if state["EMAS"] <= 0 or state["ELKE"] < 0:
            raise ValueError("Invalid native mass or kinetic energy")
    return states


def accepted_times(text):
    times = []
    for line in text.splitlines():
        row = line.split()
        if not row or not row[0].isdigit():
            continue
        if len(row) != 7:
            raise ValueError("Malformed STA row")
        if row[2].endswith("U"):
            continue
        time = float(row[4].replace("D", "E"))
        if (int(row[0]) != 1 or int(row[1]) != len(times) + 1 or
                not math.isfinite(time) or time <= (times[-1] if times else 0)):
            raise ValueError("Invalid accepted STA sequence")
        times.append(time)
    if not times or not math.isclose(times[-1], .001, rel_tol=1e-7):
        raise ValueError("Accepted STA endpoint missing")
    return times


def affine_velocity_residual(xyz, velocities):
    """Relative L2 residual from the four unit-reference-corner affine fit."""
    residual = math.fsum((velocities[n][a] - velocities[1][a] -
                         math.fsum((velocities[j + 2][a] - velocities[1][a])*p[j]
                                   for j in range(3)))**2
                        for n, p in xyz.items() for a in range(3))
    norm = math.fsum(v*v for row in velocities.values() for v in row)
    return math.sqrt(residual/norm) if norm else 0.


def analyze(case, directory):
    if (directory / "control.inp").read_text() != deck(case):
        raise ValueError("Executed deck differs from source-qualified implicit control")
    solver_log = (directory / "solver.log").read_text()
    if "explicit time integration" in solver_log.lower():
        raise ValueError("Explicit time integration cannot qualify this implicit control")
    if "Dynamic analysis was selected" not in solver_log:
        raise ValueError("Native dynamic analysis identification missing")
    # Frozen sibling module; no test imports and no frame-code dependency.
    from dynamic_momentum import calculix_221_mass, consistent_mass, momentum
    xyz = nodes(case.startswith("curved"))
    elements = {1: tuple(xyz)}
    native = calculix_221_mass(elements, xyz, 1)
    physical = consistent_mass(elements, xyz, 1)
    states = parse_dat((directory / "control.dat").read_text())
    accepted = accepted_times((directory / "control.sta").read_text())
    # STA prints seven significant digits; DAT prints eight.
    if len(states) != len(accepted) or any(not math.isclose(a, b, rel_tol=1e-6)
                                         for a, b in zip(sorted(states), accepted)):
        raise ValueError("Native fields do not cover every accepted STA state")
    rows = []
    for time, state in sorted(states.items()):
        reconstructed = momentum(xyz, native, state["U"], state["V"])
        gauss8 = momentum(xyz, physical, state["U"], state["V"])
        rows.append({"time": time, "native_ELKE": state["ELKE"], "native_EMAS": state["EMAS"],
                     "native_ELSE": state["ELSE"], "four_point": reconstructed, "Gauss8": gauss8,
                     "ELKE_relative_error": abs(reconstructed["kinetic_energy"] - state["ELKE"])/max(abs(state["ELKE"]), 1e-30),
                     "EMAS_relative_error": abs(reconstructed["mass"] - state["EMAS"])/state["EMAS"]})
    final = rows[-1]
    native_ke, gauss8_ke = final["four_point"]["kinetic_energy"], final["Gauss8"]["kinetic_energy"]
    contrast = abs(native_ke - gauss8_ke)/max(abs(native_ke), abs(gauss8_ke), 1e-30)
    affine_residual = affine_velocity_residual(xyz, states[max(states)]["V"])
    gates = {"positive_kinetic_energy": {"value": final["native_ELKE"], "minimum_exclusive": KE_FLOOR,
                                           "passed": final["native_ELKE"] > KE_FLOOR},
             "relative_Gauss8_energy_contrast": {"value": contrast, "minimum_exclusive": ENERGY_CONTRAST_MIN,
                "normalization": "max(abs(four_point_KE), abs(Gauss8_KE))", "passed": contrast > ENERGY_CONTRAST_MIN},
             "relative_affine_velocity_residual": {"value": affine_residual, "minimum_exclusive": AFFINE_RESIDUAL_MIN,
                "normalization": "L2 nodal velocity norm", "passed": affine_residual > AFFINE_RESIDUAL_MIN}}
    passed = all(g["passed"] for g in gates.values()) and math.isclose(max(states), .001, rel_tol=1e-7) and all(
        row["ELKE_relative_error"] < 5e-6 and row["EMAS_relative_error"] < 5e-6 for row in rows)
    report = {"case": case, "qualified": passed, "tolerance": 5e-6, "accepted_STA_times": accepted,
              "integration_mode_evidence": "Source-qualified implicit deck (EXPLICIT omitted), native dynamic banner, accepted STA increments, no explicit integration banner",
              "final_accepted_state_discriminator_gates": gates,
              "scope": "Native ELKE/EMAS agreement at printed actual V; no frame or physical validation", "states": rows}
    (directory / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise ValueError("Native output qualification failed")


def prepare(parent):
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="control-", dir=parent)).resolve()
    frozen = directory / "frozen"
    frozen.mkdir()
    shutil.copy2(__file__, frozen / "native_dynamic_control.py")
    shutil.copy2(Path(__file__).with_name("dynamic_momentum.py"), frozen / "dynamic_momentum.py")
    for name in ("test_native_dynamic_control.py", "test_dynamic_momentum.py"):
        shutil.copy2(ROOT / "tests" / name, frozen / name)
    shutil.copy2(BUILD, frozen / "build_manifest.json")
    manifest = json.loads(BUILD.read_text())
    for key, expected in manifest["upstream_files_sha256"].items():
        if "/src/" not in key:
            continue
        relative = key.split("/src/", 1)[1]
        source = SOURCE / relative
        if sha(source) != expected:
            raise ValueError("Native source does not match build: " + relative)
        target = frozen / "native-source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for case in CASES:
        (frozen / (case + ".inp")).write_text(deck(case))
    hashes = {str(p.relative_to(directory)): sha(p) for p in frozen.rglob("*") if p.is_file()}
    (directory / "freeze.json").write_text(json.dumps({"image": IMAGE, "inputs_sha256": hashes}, indent=2) + "\n")
    return directory


def command(directory, case):
    return ["docker", "run", "--name", f"native-{directory.name}-{case}", "--network=none",
            "--memory=2g", "--memory-swap=2g", "--cpus=1", "--pids-limit=128",
            "-e", "OMP_NUM_THREADS=1", "-e", "OPENBLAS_NUM_THREADS=1",
            "-v", f"{directory / 'frozen'}:/frozen:ro", "-v", f"{directory / case}:/result",
            "-w", "/result", IMAGE, "timeout", "--signal=TERM", "--kill-after=2", "20",
            "python3", "/frozen/native_dynamic_control.py", "--execute-case", case]


def launch(directory):
    directory = directory.resolve()
    freeze_bytes = (directory / "freeze.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    def verify():
        if ((directory / "freeze.json").read_bytes() != freeze_bytes or freeze["image"] != IMAGE or
                any(sha(directory / p) != h for p, h in freeze["inputs_sha256"].items())):
            raise ValueError("Frozen inputs changed")
        if sha(Path(__file__)) != freeze["inputs_sha256"].get("frozen/native_dynamic_control.py"):
            raise ValueError("Executing launcher differs from frozen source")
    verify()
    # Exclusive sentinel forbids automatic or accidental reruns in this directory.
    with (directory / "launch.json").open("x") as stream:
        json.dump({"image": IMAGE, "cases": CASES}, stream)
    for case in CASES:
        result = directory / case
        result.mkdir()
        cmd = command(directory, case)
        (result / "command.json").write_text(json.dumps(cmd, indent=2) + "\n")
        code, cleanup_code, stopped = None, None, False
        errors = []
        try:
            with (result / "console.log").open("wb") as log:
                code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=35, check=False).returncode
        except BaseException as exc:  # noqa: BLE001 -- retain interrupted runs and still clean up
            errors.append(exc)
        try:
            inspect = subprocess.run(["docker", "inspect", cmd[3]], capture_output=True, timeout=10, check=False)
            (result / "container-inspect.json").write_bytes(inspect.stdout + inspect.stderr)
            inspected = json.loads(inspect.stdout)
            stopped = (inspect.returncode == 0 and len(inspected) == 1 and
                       inspected[0]["State"]["Running"] is False and
                       inspected[0]["State"]["ExitCode"] == 0 and
                       inspected[0]["State"].get("OOMKilled") is False)
        except BaseException as exc:  # noqa: BLE001 -- cleanup must follow failed inspection
            errors.append(exc)
        try:
            cleanup = subprocess.run(["docker", "rm", "-f", cmd[3]], capture_output=True, timeout=10, check=False)
            cleanup_code = cleanup.returncode
            (result / "cleanup.log").write_bytes(cleanup.stdout + cleanup.stderr)
        except BaseException as exc:  # noqa: BLE001 -- record uncertain cleanup, never assert success
            errors.append(exc)
        try:
            verify()
        except BaseException as exc:  # noqa: BLE001 -- retain provenance-check interruption too
            errors.append(exc)
        output_hashes = {str(p.relative_to(result)): sha(p) for p in result.rglob("*") if p.is_file()}
        (result / "exit.json").write_text(json.dumps({"returncode": code, "cleanup_returncode": cleanup_code,
            "container_stopped_successfully_before_cleanup": stopped,
            "exceptions": [{"type": type(e).__name__, "message": str(e)} for e in errors],
            "output_sha256": output_hashes}, indent=2) + "\n")
        if errors:
            raise errors[0]
        if code != 0 or cleanup_code != 0 or not stopped:
            raise RuntimeError("Control failed; retained all outputs: " + str(result))
    verify()


def execute_case(case):
    frozen = Path("/frozen")
    manifest = json.loads((frozen / "build_manifest.json").read_text())
    if (frozen / "build_manifest.json").read_bytes() != Path("/opt/ccx-upstream-2.21/build_manifest.json").read_bytes():
        raise ValueError("Image build manifest differs")
    if sha(Path(BINARY)) != manifest["binary_sha256"][BINARY]:
        raise ValueError("Native executable differs")
    shutil.copy2(frozen / (case + ".inp"), "control.inp")
    run_case(case, Path.cwd())


def run_case(case, directory):
    code, error = None, None
    try:
        with (directory / "solver.log").open("wb") as log:
            completed = subprocess.run([BINARY, "control"], cwd=directory, stdout=log,
                                       stderr=subprocess.STDOUT, check=False, timeout=15)
        code = completed.returncode
        completed.check_returncode()
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        (directory / "solver-exit.json").write_text(json.dumps({"returncode": code, "exception": error}) + "\n")
    error = None
    try:
        analyze(case, directory)
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        (directory / "analysis-exit.json").write_text(json.dumps({"passed": error is None, "exception": error}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "fea/native_dynamic_controls")
    parser.add_argument("--launch", type=Path)
    parser.add_argument("--execute-case", choices=CASES)
    args = parser.parse_args()
    if args.execute_case:
        execute_case(args.execute_case)
    elif args.launch:
        launch(args.launch)
    else:
        print(prepare(args.output))
