"""Freeze and serially execute known-answer port-reaction method fixtures."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
BINARY = "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b"
CASES = ("static_direct", "static_mpc", "dynamic_direct", "dynamic_mpc")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deck(case: str) -> str:
    dynamic, mpc = case.startswith("dynamic"), case.endswith("mpc")
    lines = ["** Unit-cube output-method fixture; not candidate geometry.", "*NODE",
             "1,0,0,0", "2,1,0,0", "3,1,1,0", "4,0,1,0",
             "5,0,0,1", "6,1,0,1", "7,1,1,1", "8,0,1,1"]
    if mpc:
        lines.append("9,1,0.5,0.5")
    lines.extend(["*ELEMENT,TYPE=C3D8,ELSET=CUBE", "1,1,2,3,4,5,6,7,8",
                  "*NSET,NSET=PHYSICAL", "1,2,3,4,5,6,7,8",
                  "*NSET,NSET=OBSERVE", "1,2,3,4,5,6,7,8" + (",9" if mpc else ""),
                  "*NSET,NSET=LEFT", "1,4,5,8", "*NSET,NSET=RIGHT", "2,3,6,7",
                  "*MATERIAL,NAME=UNIT_ELASTIC", "*ELASTIC", "1,0", "*DENSITY", "3e-9",
                  "*SOLID SECTION,ELSET=CUBE,MATERIAL=UNIT_ELASTIC",
                  "*SURFACE,NAME=LEFT_SECTION", "1,S6",
                  "*SURFACE,NAME=RIGHT_SECTION", "1,S4"])
    if mpc:
        lines.extend(["*EQUATION", "5", "2,1,1,3,1,1,6,1,1,7,1,1", "9,1,-4"])
    lines.extend(["*BOUNDARY", "PHYSICAL,2,3,0", "LEFT,1,1,0"])
    if dynamic:
        lines.append("*AMPLITUDE,NAME=CUBIC_KNOTS")
        for i in range(101):
            lines.append(f"{i * 1e-6:.12g},{(i / 100)**3:.12g}")
    lines.append("*STEP,INC=200")
    lines.extend(["*DYNAMIC,DIRECT,ALPHA=0", "1e-6,1e-4"] if dynamic else ["*STATIC", "1,1"])
    lines.append("*BOUNDARY" + (",AMPLITUDE=CUBIC_KNOTS" if dynamic else ""))
    lines.append(("9" if mpc else "RIGHT") + ",1,1,0.01")
    motion = "U,RF,V" if dynamic else "U,RF"
    lines.extend(["*NODE PRINT,NSET=OBSERVE,FREQUENCY=1", motion,
                  "*NODE FILE,NSET=OBSERVE,FREQUENCY=1", motion,
                  "*SECTION PRINT,SURFACE=LEFT_SECTION,NAME=LEFT_PORT", "SOF",
                  "*SECTION PRINT,SURFACE=RIGHT_SECTION,NAME=RIGHT_PORT", "SOF",
                  "*EL PRINT,ELSET=CUBE,TOTALS=ONLY,FREQUENCY=1",
                  "ELSE,ELKE,EMAS,EVOL" if dynamic else "ELSE,EMAS,EVOL",
                  "*END STEP"])
    return "\n".join(lines) + "\n"


def prepare(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if any(p.name != "README.md" for p in folder.iterdir()):
        raise FileExistsError("preserve existing attempts")
    for case in CASES:
        (folder / f"{case}.inp").write_text(deck(case))
    (folder / "producer-runner.py.snapshot").write_bytes(Path(__file__).read_bytes())
    freeze = {"schema": "wood_joint_port_reaction_coupon/v1",
              "solver_image": IMAGE, "solver_binary_sha256": BINARY,
              "cases": list(CASES), "timeout_per_case_seconds": 60,
              "exact_stiffness_N_per_mm": 1.0, "consistent_generalized_mass_tonne": 1e-9,
              "displacement_target_mm": 0.01, "dynamic_duration_s": 1e-4,
              "dynamic_dt_s": 1e-6, "dynamic_hht_alpha": 0,
              "comparison_relative_tolerance": 1e-4, "comparison_absolute_tolerance": 1e-10,
              "artifacts_sha256": {p.name: sha(p) for p in folder.iterdir() if p.is_file()},
              "mechanical_acceptance": False}
    (folder / "input-freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")


def run(folder: Path) -> list[dict]:
    freeze = json.loads((folder / "input-freeze.json").read_text())
    pins = freeze["artifacts_sha256"]
    if any(sha(folder / name) != digest for name, digest in pins.items()):
        raise ValueError("frozen input mismatch")
    if list(folder.glob("*-execution.json")):
        raise FileExistsError("terminal or active run already exists")
    live = subprocess.check_output(["docker", "ps", "--format", "{{.Names}} {{.Command}}"], text=True)
    if any("wj-" in row or "ccx" in row.lower() for row in live.splitlines()):
        raise RuntimeError("another native job may be active")
    if subprocess.run(["pgrep", "-x", "ccx"], capture_output=True).returncode == 0:
        raise RuntimeError("a native solver process is already active")
    actual = subprocess.check_output(["docker", "run", "--rm", "--network", "none",
                                      IMAGE, "sha256sum", "/usr/bin/ccx"], text=True).split()[0]
    if actual != BINARY:
        raise ValueError("solver binary mismatch")
    results = []
    for case in freeze["cases"]:
        name = "wj-method-port-" + sha(folder / "input-freeze.json")[:8] + "-" + case.replace("_", "-")
        command = ["docker", "run", "--name", name, "--network", "none", "--cpus", "1",
                   "--memory", "2g", "--user", f"{os.getuid()}:{os.getgid()}",
                   "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
                   "--mount", f"type=bind,src={folder},dst=/work", "--workdir", "/work",
                   IMAGE, "/usr/bin/ccx", "-i", case]
        record = {"case": case, "status": "running", "command": command,
                  "binary_sha256": actual, "freeze_sha256": sha(folder / "input-freeze.json"),
                  "started_utc": datetime.now(timezone.utc).isoformat(),
                  "mechanical_acceptance": False}
        record_path = folder / f"{case}-execution.json"
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        started = time.monotonic()
        with (folder / f"{case}.stdout").open("x") as out:
            process = subprocess.Popen(command, stdout=out, stderr=subprocess.STDOUT)
            try:
                record["returncode"] = process.wait(timeout=60)
                record["status"] = "process_finished" if process.returncode == 0 else "process_failed"
            except subprocess.TimeoutExpired:
                subprocess.run(["docker", "kill", name], capture_output=True, check=False)
                record["returncode"] = process.wait(timeout=15)
                record["status"] = "bounded_timeout"
            except BaseException:
                subprocess.run(["docker", "kill", name], capture_output=True, check=False)
                process.wait(timeout=15)
                raise
        state = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]["State"]
        if state["Running"]:
            raise RuntimeError("container remains active; do not freeze outputs")
        record.update({"container_state": state, "elapsed_seconds": time.monotonic() - started,
                       "ended_utc": datetime.now(timezone.utc).isoformat(),
                       "frozen_inputs_unchanged": all(sha(folder / n) == h for n, h in pins.items()),
                       "outputs_sha256": {p.name: sha(p) for p in folder.glob(case + ".*")
                                          if p.suffix != ".inp"}})
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        results.append(record)
        print(json.dumps({k: record[k] for k in ("case", "status", "returncode", "elapsed_seconds")}), flush=True)
        if record["returncode"] != 0:
            break
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.folder.resolve())
    else:
        run(args.folder.resolve())
