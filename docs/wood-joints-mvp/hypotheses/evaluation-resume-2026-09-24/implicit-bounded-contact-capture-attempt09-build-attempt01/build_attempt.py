#!/usr/bin/env python3
"""Build the pinned attempt09 image and extract its dedicated binary without running CCX."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ATTEMPT = Path(__file__).resolve().parent
CONTEXT = ATTEMPT / "context"
OUTPUT = ATTEMPT / "output"
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
EXPECTED_BASE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
LOCKED_BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1-pinned-31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BUILD_IMAGE = "mini-moonboard-fea:ccx-bounded-contact-capture-attempt09-build01"
EXTRACT_CONTAINER = "ccx-attempt09-build01-extract"
BINARY_IN_IMAGE = "/usr/local/bin/ccx-bounded-contact-capture-2.23-attempt09-build01"
MANIFEST_IN_IMAGE = "/opt/ccx-bounded-contact-capture-attempt09-build01/build-manifest.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def docker_json(*args: str) -> dict:
    result = subprocess.run(["docker", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)[0]


def image_exists(ref: str) -> bool:
    return subprocess.run(["docker", "image", "inspect", ref], capture_output=True).returncode == 0


def verify_prebuild_pins() -> dict:
    pin_path = ATTEMPT / "prebuild-input-pins.json"
    pins = json.loads(pin_path.read_text())
    if pins.get("schema") != "ccx223_attempt09_build_attempt01_prebuild_pins/v2":
        raise SystemExit("unexpected prebuild pin schema")
    for relative, expected in pins["files_sha256"].items():
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise SystemExit(f"unsafe prebuild pin path: {relative}")
        path = ATTEMPT / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise SystemExit(f"prebuild input pin mismatch: {relative}")
    return pins


def main() -> None:
    if not CONTEXT.is_dir():
        raise SystemExit(f"missing build context: {CONTEXT}")
    prebuild_pins = verify_prebuild_pins()
    prior_records = [ATTEMPT / name for name in ("base-image-before.json", "base-image-locked.json", "docker-build.log", "build-image-inspect.json", "build-execution.json")]
    if any(path.exists() for path in prior_records):
        raise SystemExit("build attempt already has a run record; preserve it and use a new attempt directory")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {OUTPUT}")
    OUTPUT.mkdir(exist_ok=True)
    if image_exists(BUILD_IMAGE):
        raise SystemExit(f"refusing to overwrite existing build image tag {BUILD_IMAGE}")
    if subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"],check=True,capture_output=True,text=True).stdout.splitlines().__contains__(EXTRACT_CONTAINER):
        raise SystemExit(f"refusing to reuse existing extraction container name {EXTRACT_CONTAINER}")

    before = docker_json("image", "inspect", BASE_TAG)
    if before["Id"] != EXPECTED_BASE_ID:
        raise SystemExit(f"base image mismatch: observed {before['Id']} expected {EXPECTED_BASE_ID}")
    (ATTEMPT / "base-image-before.json").write_text(json.dumps({"Id":before["Id"],"RepoTags":before.get("RepoTags"),"RootFS":before["RootFS"]},indent=2,sort_keys=True)+"\n")
    if image_exists(LOCKED_BASE_TAG):
        locked = docker_json("image", "inspect", LOCKED_BASE_TAG)
        if locked["Id"] != EXPECTED_BASE_ID:
            raise SystemExit(f"locked base tag already points to {locked['Id']}")
    else:
        subprocess.run(["docker", "image", "tag", EXPECTED_BASE_ID, LOCKED_BASE_TAG],check=True)
    locked = docker_json("image", "inspect", LOCKED_BASE_TAG)
    if locked["Id"] != EXPECTED_BASE_ID:
        raise SystemExit("unique local base tag failed exact image-ID check")
    (ATTEMPT / "base-image-locked.json").write_text(json.dumps({"Id":locked["Id"],"RepoTags":locked.get("RepoTags"),"RootFS":locked["RootFS"]},indent=2,sort_keys=True)+"\n")

    command=["docker","build","--pull=false","--no-cache","--network=none","--progress=plain",
             "--build-arg",f"BASE_IMAGE={LOCKED_BASE_TAG}","--build-arg",f"BASE_IMAGE_ID={EXPECTED_BASE_ID}",
             "--tag",BUILD_IMAGE,"."]
    started=datetime.now(timezone.utc).isoformat()
    with (ATTEMPT/"docker-build.log").open("wb") as log:
        result=subprocess.run(command,cwd=CONTEXT,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        tail=(ATTEMPT/"docker-build.log").read_text(errors="replace").splitlines()[-50:]
        print("\n".join(tail),file=sys.stderr)
        raise SystemExit(f"docker build failed with exit {result.returncode}; launch not a solver run")
    ended=datetime.now(timezone.utc).isoformat()

    after=docker_json("image","inspect",BASE_TAG)
    locked_after=docker_json("image","inspect",LOCKED_BASE_TAG)
    built=docker_json("image","inspect",BUILD_IMAGE)
    if after["Id"]!=EXPECTED_BASE_ID or locked_after["Id"]!=EXPECTED_BASE_ID:
        raise SystemExit("base tag or locked alias changed during build")
    base_layers=locked["RootFS"]["Layers"]
    built_layers=built["RootFS"]["Layers"]
    if built_layers[:len(base_layers)]!=base_layers:
        raise SystemExit("built image layer prefix does not match locked base image")

    (ATTEMPT/"build-image-inspect.json").write_text(json.dumps({k:built.get(k) for k in ("Id","RepoTags","RepoDigests","Created","Architecture","Os","RootFS")},indent=2,sort_keys=True)+"\n")
    container_id=subprocess.run(["docker","create","--name",EXTRACT_CONTAINER,BUILD_IMAGE],check=True,capture_output=True,text=True).stdout.strip()
    try:
        subprocess.run(["docker","cp",f"{container_id}:{BINARY_IN_IMAGE}",str(OUTPUT/"ccx-bounded-contact-capture-2.23-attempt09-build01")],check=True,capture_output=True,text=True)
        subprocess.run(["docker","cp",f"{container_id}:{MANIFEST_IN_IMAGE}",str(OUTPUT/"build-manifest.json")],check=True,capture_output=True,text=True)
    finally:
        subprocess.run(["docker","rm",container_id],check=False,capture_output=True,text=True)
    binary=OUTPUT/"ccx-bounded-contact-capture-2.23-attempt09-build01"
    manifest=json.loads((OUTPUT/"build-manifest.json").read_text())
    if sha(binary.read_bytes())!=manifest["dedicated_capture_binary_sha256"]:
        raise SystemExit("extracted binary does not match in-image build manifest")
    if manifest["base_image_id"]!=EXPECTED_BASE_ID or manifest["base_image_reference"]!=LOCKED_BASE_TAG:
        raise SystemExit("in-image build manifest does not bind the locked base ID/reference")
    for relative, expected in manifest["build_context_sha256"].items():
        current=sha((CONTEXT/relative).read_bytes())
        if current!=expected or prebuild_pins["files_sha256"].get(f"context/{relative}")!=current:
            raise SystemExit(f"built context hash disagrees with prebuild pin: {relative}")
    record={
      "schema":"ccx223_attempt09_build_execution/v1",
      "started_at":started,"ended_at":ended,
      "base_image_tag":BASE_TAG,"base_image_id":EXPECTED_BASE_ID,"locked_base_reference":LOCKED_BASE_TAG,
      "build_image_tag":BUILD_IMAGE,"build_image_id":built["Id"],
      "build_command":command,"build_network":"none","pull":False,"no_cache":True,
      "solver_executed":False,"native_solver_case_run":False,"mechanical_acceptance":False,
      "extraction_container_created":True,"extraction_container_started":False,"extraction_container_id":container_id,
      "base_layer_prefix_verified":True,"prebuild_input_pins_verified":True,
      "build_context_hashes_match_prebuild_pins":True,"prebuild_pin_count":len(prebuild_pins["files_sha256"]),
      "binary_sha256":sha(binary.read_bytes()),
      "build_manifest_sha256":sha((OUTPUT/"build-manifest.json").read_bytes()),
      "docker_build_log_sha256":sha((ATTEMPT/"docker-build.log").read_bytes())
    }
    (ATTEMPT/"build-execution.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:record[k] for k in ("build_image_id","binary_sha256","build_manifest_sha256","docker_build_log_sha256","native_solver_case_run")},indent=2))

if __name__=="__main__":
    main()
