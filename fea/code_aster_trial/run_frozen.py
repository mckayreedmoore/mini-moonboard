"""Freeze and run one prepared stock Code_Aster fixture; no acceptance inference."""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("export")
    parser.add_argument("attempt", type=Path)
    parser.add_argument("--image", required=True, help="Immutable repository@sha256 digest")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if "@sha256:" not in args.image:
        parser.error("An immutable image digest is required")
    source = args.source.resolve()
    attempt = args.attempt.resolve()
    if Path(args.export).name != args.export or not (source / args.export).is_file():
        parser.error("Export must be a filename within the prepared source directory")
    # Nonblocking lock serializes this trial's jobs. Parent also checks external
    # native jobs before launch; this lock cannot govern unrelated launchers.
    with open("/tmp/mini-moonboard-code-aster-trial.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempt.mkdir(parents=True, exist_ok=False)
        for item in source.iterdir():
            if item.is_file() and not item.is_symlink():
                shutil.copy2(item, attempt / item.name)
        hashes = {p.name: digest(p) for p in sorted(attempt.iterdir()) if p.is_file()}
        name = "moonboard-aster-" + str(os.getpid())
        command = ["docker", "run", "--rm", "--name", name, "--network", "none",
                   "--cpus", "1", "--memory", "4g", "--pids-limit", "256",
                   "-e", "OMP_NUM_THREADS=1", "-e", "OPENBLAS_NUM_THREADS=1",
                   "--mount", f"type=bind,source={attempt},target=/home/user/data",
                   "-w", "/home/user/data", args.image,
                   "bash", "-ic", 'run_aster "$1"', "bash", args.export]
        freeze = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "source_directory": str(source), "input_sha256": hashes,
                  "runner_sha256": digest(Path(__file__)), "image": args.image,
                  "command": command, "timeout_seconds": args.timeout,
                  "scope": "Method fixture only; process success is not mechanical acceptance."}
        (attempt / "input-freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
        start = time.monotonic()
        timed_out = False
        with (attempt / "native.stdout").open("w") as out, (attempt / "native.stderr").open("w") as err:
            try:
                run = subprocess.run(command, stdout=out, stderr=err, timeout=args.timeout, check=False)
                returncode = run.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                subprocess.run(["docker", "stop", "--time", "5", name], capture_output=True, check=False)
                returncode = None
        changed = [name for name, sha in hashes.items() if not (attempt / name).is_file()
                   or digest(attempt / name) != sha]
        record = {"returncode": returncode, "timed_out": timed_out,
                  "elapsed_seconds": time.monotonic() - start,
                  "changed_frozen_inputs": changed, "mechanical_acceptance": "NOT_INFERRED"}
        (attempt / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, indent=2))
        raise SystemExit(1 if timed_out or changed else returncode)


if __name__ == "__main__":
    main()
