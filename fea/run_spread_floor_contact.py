"""Bounded native execution; solver termination is NOT contact acceptance."""
import argparse
import json
import math
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid
from pathlib import Path

from fea import spread_floor_contact as preparation
from fea.lumber_leg_response import IMAGE, digest, unchanged


def run(output, max_seconds=600., **settings):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite native contact evidence")
    if not math.isfinite(max_seconds) or not 1 <= max_seconds <= 3600:
        raise ValueError("Require a bounded runtime of 1–3600 seconds")
    parent = Path("fea/generated")
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="spread-floor-", dir=parent)).resolve()
    job = directory/"native"
    preparation.write(job, **settings)
    record = json.loads((job/"input.json").read_text())
    sources = {**record["source_sha256"], "fea/run_spread_floor_contact.py": digest(Path(__file__))}
    unchanged(sources)
    snapshots = job/"launch_sources"
    snapshots.mkdir()
    for source in sources:
        target = snapshots/source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    name = "moonboard-spread-floor-"+uuid.uuid4().hex[:12]
    command = ["docker", "run", "--rm", "--name", name, "--network=none", "--cpus=2", "--memory=6g",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", "OMP_NUM_THREADS=2", "-v", f"{job}:/work", "-w", "/work", IMAGE,
        "timeout", "--signal=TERM", "--kill-after=10s", f"{max_seconds:g}s", "ccx", "-i", "contact"]
    run_record = {"image": IMAGE, "command": command, "max_seconds": max_seconds,
        "source_sha256": sources, "qualified_for_design": False,
        "status": "RUNNING; NO ACCEPTANCE", "local_contact_audited": False,
        "global_equilibrium_audited": False}
    (job/"run.json").write_text(json.dumps(run_record, indent=2)+"\n")
    print(f"Native evidence: {job}", flush=True)
    started = time.monotonic()
    with (job/"contact.log").open("w") as log:
        try:
            done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=max_seconds+60, check=False)
            exit_code = done.returncode
        except subprocess.TimeoutExpired:
            # Stop only the exact container created for this run.
            subprocess.run(["docker", "stop", "--time", "10", name], capture_output=True,
                           timeout=30, check=False)
            exit_code = -999
    run_record.update(exit_code=exit_code, elapsed_seconds=time.monotonic()-started)
    text = (job/"contact.log").read_text()
    completed = exit_code == 0 and "Job finished" in text and "*ERROR" not in text.upper()
    run_record["status"] = ("SOLVER TERMINATED; OUTPUT/EQUILIBRIUM/CONTACT AUDITS REQUIRED" if completed
        else "INCOMPLETE OR FAILED NUMERICAL TRIAL; NOT PHYSICAL INSTABILITY EVIDENCE")
    run_record["solver_terminated_normally"] = completed
    unchanged(sources)
    run_record["artifact_sha256"] = {str(p.relative_to(job)): digest(p)
        for p in job.rglob("*") if p.is_file() and p != job/"run.json"}
    (job/"run.json").write_text(json.dumps(run_record, indent=2, allow_nan=False)+"\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "x:gz") as archive:
        for path in sorted(job.rglob("*")):
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(job)), recursive=False)
    print(run_record["status"], flush=True)
    return run_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=600.)
    parser.add_argument("--mu", type=float, default=.2)
    parser.add_argument("--stiffness", type=float, default=1000.)
    args = parser.parse_args()
    run(args.output, args.max_seconds, mu=args.mu, stiffness=args.stiffness)
