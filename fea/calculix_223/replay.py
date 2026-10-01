"""Replay six unchanged 2.21 method fixtures in a new 2.23 evidence directory."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
BINARY = "/usr/local/bin/ccx-upstream-2.23"
GROUPS = {
    "motion": ("port-reaction-known-answer-attempt01",
               ("static_direct", "static_mpc", "dynamic_direct", "dynamic_mpc")),
    "force": ("force-port-known-answer-attempt01", ("force_direct", "force_mpc")),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def require_idle():
    live = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}} {{.Command}}"], text=True)
    if any("wj-" in line or "ccx" in line.lower() for line in live.splitlines()):
        raise RuntimeError("Another native job may be active")
    if subprocess.run(["pgrep", "-x", "ccx"], capture_output=True, check=False).returncode == 0:
        raise RuntimeError("Another native solver is active")


def replay(build_folder, folder):
    build = json.loads((build_folder / "build_result.json").read_text())
    manifest = json.loads((build_folder / "build_manifest.json").read_text())
    image = build["image_id"]
    expected = manifest["binary_sha256"][BINARY]
    require_idle()
    actual = subprocess.check_output([
        "docker", "run", "--rm", "--network", "none", image, "sha256sum", BINARY],
        text=True).split()[0]
    if actual != expected:
        raise ValueError("Solver binary differs from build manifest")
    folder.mkdir(parents=True, exist_ok=False)
    for name in ("build_manifest.json", "build_result.json"):
        (folder / name).write_bytes((build_folder / name).read_bytes())
    (folder / "replay.py.snapshot").write_bytes(Path(__file__).read_bytes())
    # Run the exact preexisting audit implementations from an isolated package.
    audit_root = folder / "auditor_snapshot"
    package = audit_root / "fea"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    for name in ("wood_joint_port_coupon_audit.py", "wood_joint_force_coupon_audit.py"):
        (package / name).write_bytes((ROOT / "fea" / name).read_bytes())
    freeze = {"image_id": image, "binary_path": BINARY, "binary_sha256": actual,
              "scope": "Six unchanged linear method fixtures; no candidate-joint acceptance",
              "mechanical_acceptance": False, "inputs": {},
              "auditor_sha256": {p.name: sha(p) for p in package.glob("*.py")}}
    for group, (source, cases) in GROUPS.items():
        out = folder / group
        out.mkdir()
        original = SOURCE / source
        pins = json.loads((original / "input-freeze.json").read_text())["artifacts_sha256"]
        for case in cases:
            name = case + ".inp"
            if sha(original / name) != pins[name]:
                raise ValueError("Original frozen deck changed: " + name)
            (out / name).write_bytes((original / name).read_bytes())
            freeze["inputs"][group + "/" + name] = {
                "source": str((original / name).relative_to(ROOT)), "sha256": pins[name]}
    write(folder / "input-freeze.json", freeze)
    for group, (_, cases) in GROUPS.items():
        out = folder / group
        for case in cases:
            require_idle()
            name = "wj-ccx223-" + case.replace("_", "-")
            command = ["docker", "run", "--name", name, "--network", "none",
                       "--cpus", "1", "--memory", "2g", "--user", f"{os.getuid()}:{os.getgid()}",
                       "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
                       "--mount", f"type=bind,src={out},dst=/work", "--workdir", "/work",
                       image, BINARY, "-i", case]
            record = {"command": command, "started_utc": datetime.now(UTC).isoformat(),
                      "freeze_sha256": sha(folder / "input-freeze.json"), "status": "running"}
            write(out / (case + "-execution.json"), record)
            with (out / (case + ".stdout")).open("x") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                try:
                    record["returncode"] = process.wait(timeout=60)
                except BaseException:
                    subprocess.run(["docker", "kill", name], capture_output=True, check=False)
                    process.wait(timeout=15)
                    raise
            state = json.loads(subprocess.check_output(["docker", "inspect", name]))[0]["State"]
            record.update(status="finished", container_state=state,
                          ended_utc=datetime.now(UTC).isoformat(),
                          outputs_sha256={p.name: sha(p) for p in out.glob(case + ".*")})
            write(out / (case + "-execution.json"), record)
            log = (out / (case + ".stdout")).read_text()
            if (record["returncode"] != 0 or state["Running"] or state["OOMKilled"]
                    or "CalculiX Version 2.23" not in log or "Job finished" not in log
                    or "*ERROR" in log.upper()):
                raise RuntimeError("Native completion check failed: " + case)
            print(case + ": native completion verified", flush=True)
    for relative, pin in freeze["inputs"].items():
        if sha(folder / relative) != pin["sha256"] or sha(ROOT / pin["source"]) != pin["sha256"]:
            raise ValueError("Deck changed during replay")
    for group, module in (("motion", "wood_joint_port_coupon_audit"),
                          ("force", "wood_joint_force_coupon_audit")):
        with (folder / group / "auditor.stdout").open("x") as log:
            subprocess.run([sys.executable, "-m", "fea." + module, str(folder / group)],
                           cwd=audit_root, stdout=log, stderr=subprocess.STDOUT, check=True)
    force = json.loads((folder / "force/independent-force-audit.json").read_text())
    motion = json.loads((folder / "motion/independent-audit.json").read_text())
    result = {"balanced_force_method_pass": force["method_fixture_pass"],
              "dynamic_mpc_full_inertia_error_mm": motion["cases"]["dynamic_mpc"][
                  "independent_Newmark_full_inertia"]["max_displacement_difference_mm"],
              "dynamic_mpc_omitted_inertia_error_mm": motion["cases"]["dynamic_mpc"][
                  "independent_Newmark_omitted_prescribed_inertia"]["max_displacement_difference_mm"],
              "original_decks_preserved": True, "mechanical_acceptance": False}
    write(folder / "comparison.json", result)
    print(json.dumps(result, indent=2))
    if not force["method_fixture_pass"]:
        raise RuntimeError("Balanced-force method failed; do not promote this solver")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_folder", type=Path)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    replay(args.build_folder.resolve(), args.folder.resolve())
