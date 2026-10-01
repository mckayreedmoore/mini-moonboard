"""Build an additional pinned solver without replacing historical toolchains."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

BASE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.21-v1"
TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(folder):
    actual = subprocess.check_output(
        ["docker", "image", "inspect", BASE_TAG, "--format", "{{.Id}}"], text=True
    ).strip()
    if actual != BASE:
        raise ValueError("Historical base image changed")
    if subprocess.run(["docker", "image", "inspect", TAG], capture_output=True, check=False).returncode == 0:
        raise FileExistsError("Preserve the existing 2.23 image; choose a new build identity")
    folder.mkdir(parents=True, exist_ok=False)
    context = folder / "context"
    context.mkdir()
    for name in ("Dockerfile", "Makefile.upstream", "record_build.py", ".dockerignore"):
        (context / name).write_bytes((ROOT / name).read_bytes())
    (folder / "build.py.snapshot").write_bytes(Path(__file__).read_bytes())
    record = {"base_image_id": BASE, "tag": TAG,
              "inputs_sha256": {p.name: sha(p) for p in context.iterdir()},
              "mechanical_acceptance": False}
    with (folder / "build.log").open("x") as log:
        result = subprocess.run(
            ["docker", "build", "--progress=plain", "--build-arg", "BASE_IMAGE=" + BASE_TAG,
             "-t", TAG, str(context)], stdout=log, stderr=subprocess.STDOUT,
            timeout=900, check=False)
    record.update(exit_code=result.returncode, build_log_sha256=sha(folder / "build.log"))
    if result.returncode == 0:
        record["image_id"] = subprocess.check_output(
            ["docker", "image", "inspect", TAG, "--format", "{{.Id}}"], text=True).strip()
        manifest = subprocess.check_output([
            "docker", "run", "--rm", "--network", "none", record["image_id"],
            "cat", "/opt/ccx-upstream-2.23/build_manifest.json"])
        (folder / "build_manifest.json").write_bytes(manifest)
        old = json.loads(subprocess.check_output([
            "docker", "run", "--rm", "--network", "none", BASE,
            "cat", "/opt/ccx-upstream-2.21/build_manifest.json"]))
        new = json.loads(manifest)
        if new["binary_sha256"]["/usr/bin/ccx"] != old["binary_sha256"]["/usr/bin/ccx"]:
            raise ValueError("Historical packaged binary changed")
        record["historical_packaged_binary_unchanged"] = True
    (folder / "build_result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    if result.returncode:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    build(parser.parse_args().folder.resolve())
