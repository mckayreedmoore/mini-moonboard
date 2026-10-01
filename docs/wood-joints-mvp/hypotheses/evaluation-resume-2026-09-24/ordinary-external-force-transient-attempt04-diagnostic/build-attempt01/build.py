"""Verify and build the pinned attempt04 CalculiX 2.23 trace executable."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile


REPO = Path(__file__).resolve().parents[6]
DIAG = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).resolve().parent
CONTEXT = BUILD / "context"
BASE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
OLD_BASE_ID = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
OLD_TAG = "mini-moonboard-fea:ccx-upstream-2.21-v1"
IMAGE_TAG = "mini-moonboard-fea:ccx-attempt04-output-trace-20260927-v1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def inspect_id(reference: str) -> str:
    return subprocess.check_output(
        ["docker", "image", "inspect", reference, "--format", "{{.Id}}"],
        text=True).strip()


def verify_source_manifest() -> dict:
    archive = BUILD / "source.tar.bz2"
    lock = json.loads((DIAG / "diagnostic-lock.json").read_text())
    base_manifest = json.loads((BUILD / "base-build-manifest.json").read_text())
    archive_sha = file_sha(archive)
    require(archive_sha == lock["official_source_archive"]["sha256"],
            "archive hash differs from diagnostic lock")
    require(base_manifest["upstream_source_archive_sha256"] == archive_sha,
            "base manifest archive hash differs")
    actual = {}
    with tarfile.open(archive, mode="r:bz2") as tar:
        for item in tar.getmembers():
            if item.isfile():
                name = item.name.removeprefix("./")
                actual[name] = sha(tar.extractfile(item).read())
    expected = {
        name.removeprefix("./"): digest
        for name, digest in base_manifest["upstream_files_sha256"].items()
    }
    require(actual == expected,
            "archive file hashes differ from the complete 2.23 base manifest")
    require(all(actual.get(name) == digest for name, digest in
                lock["source_members_sha256"].items()),
            "a diagnostic-lock source-member hash differs")
    require(base_manifest["binary_sha256"]["/usr/local/bin/ccx-upstream-2.23"] ==
            "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "unpatched upstream executable differs from its pin")
    result = {
        "schema": "calculix_223_attempt04_source_manifest_verification/v1",
        "base_image_id": BASE_ID,
        "base_manifest_sha256": file_sha(BUILD / "base-build-manifest.json"),
        "archive_sha256": archive_sha,
        "archive_file_count": len(actual),
        "source_manifest_file_count": len(expected),
        "full_source_manifest_match": True,
        "locked_source_members_sha256": lock["source_members_sha256"],
        "unpatched_upstream_binary_sha256":
            base_manifest["binary_sha256"]["/usr/local/bin/ccx-upstream-2.23"],
        "path_normalization": "Removed leading ./ before comparing archive and manifest paths.",
    }
    json_write(BUILD / "source-manifest-verification.json", result)
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    actual_base = inspect_id(BASE_TAG)
    require(actual_base == BASE_ID, "existing 2.23 image tag no longer identifies the pin")
    require(inspect_id(OLD_TAG) == OLD_BASE_ID,
            "existing 2.21 image tag no longer identifies its pin")
    try:
        inspect_id(IMAGE_TAG)
    except subprocess.CalledProcessError:
        pass
    else:
        raise RuntimeError(f"refusing to reuse image tag {IMAGE_TAG}")

    source_check = verify_source_manifest()
    static_command = [
        sys.executable,
        str(DIAG / "verify_apply.py"),
        "--source-archive", str(BUILD / "source.tar.bz2"),
        "--repo-root", str(REPO),
    ]
    static_log = BUILD / "diagnostic-static-verification.log"
    with static_log.open("wb") as output:
        result = subprocess.run(static_command, stdout=output, stderr=subprocess.STDOUT,
                                check=False)
    require(result.returncode == 0,
            "diagnostic static verification failed; see diagnostic-static-verification.log")

    context_hashes = {
        path.name: file_sha(path)
        for path in sorted(CONTEXT.iterdir()) if path.is_file()
    }
    require(set(context_hashes) == {
        "Dockerfile", "Makefile.upstream", "record_build.py", "source.tar.bz2",
        "diagnostic.patch", "diagnostic-lock.json", "base-build-manifest.json"},
        "build context has missing or unexpected files")
    command = [
        "docker", "build", "--no-cache", "--network=none", "--progress=plain",
        "--build-arg", f"BASE_IMAGE={BASE_ID}", "-t", IMAGE_TAG, str(CONTEXT),
    ]
    (BUILD / "build-command.txt").write_text(shlex.join(command) + "\n")
    log_path = BUILD / "build.log"
    try:
        with log_path.open("wb") as output:
            build_result = subprocess.run(
                command, stdout=output, stderr=subprocess.STDOUT,
                timeout=900, check=False)
        exit_code = build_result.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        exit_code = None
        timed_out = True
    result_record = {
        "schema": "calculix_223_attempt04_diagnostic_build_execution/v1",
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "base_image_tag": BASE_TAG,
        "base_image_id": BASE_ID,
        "build_runner_sha256": file_sha(Path(__file__)),
        "preserved_2_21_image_tag": OLD_TAG,
        "preserved_2_21_image_id": OLD_BASE_ID,
        "new_image_tag": IMAGE_TAG,
        "build_context_sha256": context_hashes,
        "source_manifest_verification": source_check,
        "static_verifier_sha256": file_sha(DIAG / "verify_apply.py"),
        "static_verification_log_sha256": file_sha(static_log),
        "build_command": command,
        "build_log": "build.log",
        "build_log_sha256": file_sha(log_path),
        "timeout_seconds": 900,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "mechanical_acceptance": False,
    }
    if exit_code == 0:
        image_id = inspect_id(IMAGE_TAG)
        manifest_text = subprocess.check_output([
            "docker", "run", "--rm", "--network", "none", image_id,
            "cat", "/opt/ccx-attempt04/build_manifest.json"], text=True)
        manifest = json.loads(manifest_text)
        (BUILD / "build_manifest.json").write_text(manifest_text)
        require(image_id != BASE_ID, "new build resolved to the unmodified base image")
        require(manifest["base_image_id"] == BASE_ID,
                "image manifest does not bind the pinned base image")
        require(manifest["upstream_source_archive_sha256"] ==
                source_check["archive_sha256"], "built image source archive pin differs")
        require(manifest["patch_sha256"] == context_hashes["diagnostic.patch"],
                "built image patch pin differs")
        require(manifest["historical_binary_sha256_before_and_after"] == {
            "/usr/bin/ccx":
                "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b",
            "/usr/local/bin/ccx-upstream-2.23":
                "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
        }, "building the diagnostic executable changed a historical binary")
        result_record.update(
            image_id=image_id,
            patched_binary_path=manifest["patched_binary_path"],
            patched_binary_sha256=manifest["patched_binary_sha256"],
            unpatched_2_23_binary_sha256=manifest[
                "historical_binary_sha256_before_and_after"][
                    "/usr/local/bin/ccx-upstream-2.23"],
            packaged_2_21_binary_sha256=manifest[
                "historical_binary_sha256_before_and_after"]["/usr/bin/ccx"],
            patched_source_member_sha256=manifest["patched_source_member_sha256"],
            image_manifest_sha256=file_sha(BUILD / "build_manifest.json"),
            historical_images_preserved={
                BASE_TAG: inspect_id(BASE_TAG), OLD_TAG: inspect_id(OLD_TAG)},
        )
        require(result_record["historical_images_preserved"] == {
            BASE_TAG: BASE_ID, OLD_TAG: OLD_BASE_ID},
            "historical 2.21 or 2.23 image tag changed")
    json_write(BUILD / "build_result.json", result_record)
    require(exit_code == 0 and not timed_out,
            "diagnostic solver image build failed or timed out; see build.log")


if __name__ == "__main__":
    main()
