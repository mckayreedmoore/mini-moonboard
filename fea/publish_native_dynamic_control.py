"""Publish retained native mass controls; cache/replay arithmetic, never run FEA."""
import hashlib
import json
import math
import subprocess
import tarfile
import uuid
from pathlib import Path

from fea import native_dynamic_control as control
from fea.dynamic_momentum import momentum

DIRECTORY = Path("fea/results/native_dynamic_control")
GENERATED = Path("fea/generated/native-dynamic-controls")
RUNS = {"control-ajgbgzoh": "qualified implicit controls", "control-axqh8cyi": "failed explicit-mode attempt"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def members(path):
    with tarfile.open(path) as archive:
        entries = archive.getmembers()
        if any(not m.isfile() or m.name.startswith("/") or ".." in Path(m.name).parts for m in entries):
            raise ValueError("Unsafe archive member")
        result = {m.name: archive.extractfile(m).read() for m in entries}
        if len(result) != len(entries):
            raise ValueError("Duplicate archive member")
        return result


def cache_blocks(directory):
    """Postprocessing only in the pinned image; retained frozen helper supplies Gmsh integration."""
    frozen = (GENERATED / "control-ajgbgzoh/frozen").resolve()
    code = '''import sys,json,gmsh
sys.path.insert(0,"/frozen")
import native_dynamic_control as c
import dynamic_momentum as m
result={"gmsh_version":gmsh.__version__,"image":c.IMAGE,"geometries":{}}
for geometry,curved in (("straight",False),("curved",True)):
 n=c.nodes(curved); e={1:tuple(n)}
 result["geometries"][geometry]={"nodes":n,"four_point":m.calculix_221_mass(e,n,1),"Gauss8":m.consistent_mass(e,n,1)}
print(json.dumps(result,indent=2))
'''
    name = "native-mass-cache-" + uuid.uuid4().hex[:12]
    cmd = ["docker", "run", "--name", name, "--network=none", "--memory=2g", "--memory-swap=2g",
           "--cpus=1", "--pids-limit=128", "-v", f"{frozen}:/frozen:ro", control.IMAGE,
           "timeout", "--kill-after=2", "20", "python3", "-c", code]
    (directory / "cache-command.json").write_text(json.dumps(cmd, indent=2) + "\n")
    try:
        completed = subprocess.run(cmd, capture_output=True, timeout=30, check=False)
        (directory / "cache-stderr.log").write_bytes(completed.stderr)
        (directory / "mass-blocks.json").write_bytes(completed.stdout)
        completed.check_returncode()
        json.loads(completed.stdout)
    finally:
        cleanup = subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10, check=False)
        (directory / "cache-cleanup.log").write_bytes(cleanup.stdout + cleanup.stderr)
        cleanup.check_returncode()


def verify(directory=DIRECTORY):
    publication = json.loads((directory / "manifest.json").read_text())
    for name, expected in publication["publication_files_sha256"].items():
        if digest((directory / name).read_bytes()) != expected:
            raise ValueError("Publication file changed: " + name)
    cache = json.loads((directory / "mass-blocks.json").read_text())
    if cache["image"] != control.IMAGE:
        raise ValueError("Cache image differs")
    maxima = {"ELKE_relative_error": 0., "EMAS_relative_error": 0.}
    for run, description in publication["runs"].items():
        files = members(directory / description["archive"])
        if {name: digest(data) for name, data in files.items()} != description["members_sha256"]:
            raise ValueError("Archive members differ")
        freeze = json.loads(files["freeze.json"])
        if freeze["image"] != control.IMAGE:
            raise ValueError("Frozen image differs")
        for name, expected in freeze["inputs_sha256"].items():
            if digest(files[name]) != expected:
                raise ValueError("Frozen input differs")
        build = json.loads(files["frozen/build_manifest.json"])
        for name, expected in build["upstream_files_sha256"].items():
            if "/src/" in name and digest(files["frozen/native-source/" + name.split("/src/", 1)[1]]) != expected:
                raise ValueError("Upstream source differs")
        for case in description["executed_cases"]:
            exit_report = json.loads(files[f"{case}/exit.json"])
            for name, expected in exit_report["output_sha256"].items():
                if digest(files[f"{case}/{name}"]) != expected:
                    raise ValueError("Retained output differs")
            if run == "control-axqh8cyi":
                if exit_report["returncode"] == 0 or b"Explicit time integration" not in files[f"{case}/console.log"]:
                    raise ValueError("Failed attempt classification differs")
                continue
            if exit_report["returncode"] != 0 or not exit_report["container_stopped_successfully_before_cleanup"]:
                raise ValueError("Successful control did not exit cleanly")
            for stage in ("solver", "analysis"):
                result = json.loads(files[f"{case}/{stage}-exit.json"])
                if result["exception"] is not None or (stage == "solver" and result["returncode"] != 0) or (stage == "analysis" and not result["passed"]):
                    raise ValueError("Control stage failed")
            if files[f"{case}/control.inp"].decode() != control.deck(case):
                raise ValueError("Implicit control deck differs")
            if b"Explicit time integration" in files[f"{case}/solver.log"]:
                raise ValueError("Explicit mode cannot qualify")
            states = control.parse_dat(files[f"{case}/control.dat"].decode())
            accepted = control.accepted_times(files[f"{case}/control.sta"].decode())
            recorded = json.loads(files[f"{case}/comparison.json"])
            if not recorded["qualified"] or len(states) != len(accepted) or len(states) != len(recorded["states"]):
                raise ValueError("Incomplete accepted states")
            geometry = cache["geometries"][case.split("-")[0]]
            xyz = {int(n): tuple(p) for n, p in geometry["nodes"].items()}
            if xyz != control.nodes(case.startswith("curved")):
                raise ValueError("Cache reference geometry differs")
            for time, accepted_time, row in zip(sorted(states), accepted, recorded["states"], strict=True):
                if not math.isclose(time, accepted_time, rel_tol=1e-6) or time != row["time"]:
                    raise ValueError("Accepted state time differs")
                state = states[time]
                for label in ("ELKE", "EMAS", "ELSE"):
                    if state[label] != row["native_" + label]:
                        raise ValueError("Raw scalar differs")
                reconstructed = {}
                for operator in ("four_point", "Gauss8"):
                    blocks = {int(e): (tuple(ids), block) for e, (ids, block) in geometry[operator].items()}
                    actual = momentum(xyz, blocks, state["U"], state["V"])
                    reconstructed[operator] = actual
                    for key in ("mass", "kinetic_energy"):
                        if not math.isclose(actual[key], row[operator][key], rel_tol=1e-12, abs_tol=1e-15):
                            raise ValueError("Raw actual-V arithmetic differs")
                for native_label, key in (("ELKE", "kinetic_energy"), ("EMAS", "mass")):
                    error = abs(reconstructed["four_point"][key] - state[native_label])/state[native_label]
                    if error >= 5e-6 or not math.isclose(error, row[native_label + "_relative_error"], rel_tol=1e-8, abs_tol=1e-14):
                        raise ValueError("Native comparison differs")
                    maxima[native_label + "_relative_error"] = max(maxima[native_label + "_relative_error"], error)
            final = states[max(states)]
            native, physical = (reconstructed[k]["kinetic_energy"] for k in ("four_point", "Gauss8"))
            gate_values = {"positive_kinetic_energy": final["ELKE"],
                "relative_Gauss8_energy_contrast": abs(native-physical)/max(abs(native), abs(physical)),
                "relative_affine_velocity_residual": control.affine_velocity_residual(xyz, final["V"])}
            for gate, value in gate_values.items():
                recorded_gate = recorded["final_accepted_state_discriminator_gates"][gate]
                threshold = 1e-8 if gate == "positive_kinetic_energy" else 1e-3
                if not value > threshold or not math.isclose(value, recorded_gate["value"], rel_tol=1e-12):
                    raise ValueError("Final discriminator differs")
    return maxima


def publish(directory=DIRECTORY):
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "manifest.json").exists():
        raise FileExistsError("Publication already exists; refusing overwrite")
    cache_blocks(directory)
    runs = {}
    for run, outcome in RUNS.items():
        source = GENERATED / run
        files = sorted(p for p in source.rglob("*") if p.is_file())
        archive_name = run + ".tar.gz"
        with tarfile.open(directory / archive_name, "x:gz") as archive:
            for path in files:
                archive.add(path, arcname=str(path.relative_to(source)), recursive=False)
        runs[run] = {"outcome": outcome, "archive": archive_name,
                     "executed_cases": [case for case in control.CASES if (source / case / "exit.json").exists()],
                     "members_sha256": {str(p.relative_to(source)): digest(p.read_bytes()) for p in files}}
    manifest = {"scope": "Only untransformed implicit C3D10 native ELKE/EMAS output qualified. No native P/H, contact, time-integration accuracy, frame, or material validation.",
                "cache_scope": "Source-derived mass blocks cached by frozen helpers in pinned image; portable actual-V arithmetic replay, not an independent physical quadrature proof.",
                "runs": runs, "publication_files_sha256": {p.name: digest(p.read_bytes()) for p in directory.iterdir()
                                                           if p.is_file() and p.name != "manifest.json"}}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return verify(directory)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify() if args.verify else publish(), indent=2))
