#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if len(sys.argv) != 7:
        raise SystemExit("usage: record_build_provenance.py expected-base-id resolved-base-id built-image-id locked-base-tag image-tag packet-dir")
    expected_id, resolved_id, built_id, locked_tag, image_tag, packet = sys.argv[1:]
    root = Path(packet).resolve()
    expected_manifest = json.loads((root / "build/context/base-image-pin.json").read_text())
    expected_from_manifest = expected_manifest["image_id"]
    if expected_from_manifest != expected_id or resolved_id != expected_id:
        raise SystemExit("recorded base image resolution does not match the pinned base manifest")
    actual_locked = subprocess.run(["docker", "image", "inspect", locked_tag, "--format", "{{.Id}}"],
                                   check=True, capture_output=True, text=True).stdout.strip()
    actual_built = subprocess.run(["docker", "image", "inspect", image_tag, "--format", "{{.Id}}"],
                                  check=True, capture_output=True, text=True).stdout.strip()
    if actual_locked != resolved_id or actual_built != built_id:
        raise SystemExit("post-build Docker image IDs differ from captured build IDs")
    artifact = root / "build/artifacts"
    report = {
        "schema": "ccx223_bounded_capture_host_build_provenance/v1",
        "build_ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_image_tag_preflight": expected_manifest["image_tag"],
        "pinned_base_image_id": expected_id,
        "resolved_base_image_id_before_build": resolved_id,
        "locked_base_image_tag_used_by_from": locked_tag,
        "locked_base_image_id_after_build": actual_locked,
        "built_image_tag": image_tag,
        "built_image_id": actual_built,
        "binary_sha256": sha(artifact / "ccx-bounded-contact-capture-2.23-attempt04"),
        "container_action": "docker create --entrypoint /bin/true followed only by docker cp; no container process was started",
        "solver_executed": False,
        "native_case_executed": False,
        "build_network": "none",
        "build_pull": False,
    }
    out = artifact / "build-provenance.json"
    with out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
