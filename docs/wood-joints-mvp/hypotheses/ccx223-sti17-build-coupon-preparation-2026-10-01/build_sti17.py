#!/usr/bin/env python3
"""Parent-only builder for a one-format-token CalculiX 2.23 copy.

Prepared for later execution inside the pinned 2.23 image with this repository
mounted read-only at /repo and no network. This file has not been executed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

REPO = Path("/repo")
HERE = (
    REPO
    / "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01"
)
PREFLIGHT = (
    REPO
    / "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01"
)
PARENT_VALIDATION = (
    REPO
    / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json"
)
BUILD_INPUT_FREEZE = HERE / "build-input-freeze.json"
BASE = Path("/opt/ccx-upstream-2.23")
TARGET = Path("/opt/ccx-sti17")
SOURCE_REL = Path("CalculiX/ccx_2.23/src")
OLD_BINARY = Path("/usr/local/bin/ccx-upstream-2.23")
PACKAGED_BINARY = Path("/usr/bin/ccx")
NEW_BINARY = Path("/usr/local/bin/ccx-upstream-2.23-sti17")
BASE_IMAGE_ID = (
    "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
)
BASE_IMAGE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
NEW_IMAGE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-sti17-v1"
BASE_MANIFEST_SHA256 = (
    "496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66"
)
BASE_PROFILE_SHA256 = "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c"
BASE_BUILD_RESULT_SHA256 = (
    "1802c28e5f2f0b0cb1cd86ff7d2a3e2a7b9cd6c8f1daf89313be2fd587542200"
)
SOURCE_PINS_SHA256 = "1cc174760cb658614431a75532fcd0603342b6e1559ebc0df935be6310e65981"
PARENT_VALIDATION_SHA256 = (
    "5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2"
)
SOURCE_ARCHIVE_SHA256 = (
    "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
)
MATRIXSTORAGE_SHA256 = (
    "2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4"
)
PATCH_SHA256 = "71e56dc8854d7a89044cd36e961c79d809a12b21882524231bd2a26b6f4f7cd7"
MAKEFILE_SHA256 = "57a25e08a51bba3897cecb3c03e45f7cf602d9c28a15c12e45d9b1ddebcad0bf"
SOURCE_OLD = (
    b'    fprintf(f2,"%" ITGFORMAT " %" ITGFORMAT " %20.13e\\n",ai[i],aj[i],aa[i]);'
)
SOURCE_NEW = (
    b'    fprintf(f2,"%" ITGFORMAT " %" ITGFORMAT " %20.16e\\n",ai[i],aj[i],aa[i]);'
)
MASS_WRITER = (
    b'      fprintf(f3,"%" ITGFORMAT " %" ITGFORMAT " %20.13e\\n",ai[i],aj[i],aa[i]);'
)
READINESS_REL = "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/parent-build-readiness.json"
REQUIRED_BUILD_FILE_PINS = {
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/build_sti17.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/pin-receipt.json",
    READINESS_REL,
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/source-pins.json",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/precision-only.patch",
    "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json",
    "fea/calculix_223/solver-profile.json",
    "fea/generated/calculix-2.23-build-attempt02/build_manifest.json",
    "fea/generated/calculix-2.23-build-attempt02/build_result.json",
}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def run(
    argv: list[str], *, cwd: Path | None = None, timeout: float = 20
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, check=True, timeout=timeout
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_review_binding(root: Path, binding: dict, frozen_files: dict) -> None:
    """Bind the build inputs to the exact target and three parent-read reviews."""
    require(isinstance(binding, dict), "build has no final source-review binding")
    target = binding.get("target", {})
    reviews = binding.get("reviews", {})
    require(
        isinstance(target, dict)
        and isinstance(reviews, dict)
        and set(reviews) == {"correctness", "testing", "architecture"},
        "build needs the exact target and three independent source reviews",
    )
    records = [target, *reviews.values()]
    require(
        all(isinstance(record, dict) for record in reviews.values())
        and len({record.get("path") for record in reviews.values()}) == 3
        and len({record.get("sha256") for record in reviews.values()}) == 3
        and all(
            isinstance(record.get("agent_id"), str) and record["agent_id"]
            for record in reviews.values()
        )
        and len({record["agent_id"] for record in reviews.values()}) == 3,
        "build needs three distinct review reports and reviewer identities",
    )
    for record in records:
        require(isinstance(record, dict), "source-review binding is not an object")
        name = record.get("path")
        require(isinstance(name, str) and bool(name), "source-review path absent")
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "source-review path must be repository-relative",
        )
        path = (root / relative).resolve()
        require(
            path.is_relative_to(root.resolve()), "source-review path escapes repository"
        )
        require(
            frozen_files.get(name) == record.get("sha256")
            and path.is_file()
            and sha_file(path) == record.get("sha256"),
            "final source-review record is not bound to the build freeze",
        )
    packet = json.loads((root / target["path"]).read_text())
    rows = packet.get("files")
    require(
        isinstance(rows, list) and bool(rows), "source-review target has no file pins"
    )
    for row in rows:
        name = row["path"]
        require(
            frozen_files.get(name) == row["sha256"],
            f"build input differs from reviewed source: {name}",
        )
        path = (root / name).resolve()
        require(
            path.is_relative_to(root.resolve())
            and path.is_file()
            and sha_file(path) == row["sha256"],
            f"reviewed source changed: {name}",
        )


def validate_parent_readiness(packet: dict, *, now: float | None = None) -> dict:
    require(
        packet.get("schema") == "ccx223_sti17_parent_build_readiness/v1",
        "wrong parent build-readiness schema",
    )
    require(
        packet.get("status") == "READY_STI17_BUILD",
        "parent has not marked this exact build ready",
    )
    require(
        packet.get("parent_validation_sha256") == PARENT_VALIDATION_SHA256,
        "readiness does not bind the cited parent validation",
    )
    require(
        packet.get("source_pins_sha256") == SOURCE_PINS_SHA256,
        "readiness does not bind the preflight source pins",
    )
    require(
        packet.get("base_image_id") == BASE_IMAGE_ID,
        "readiness names a different base image",
    )
    require(
        packet.get("new_image_tag") == NEW_IMAGE_TAG,
        "readiness names a different new image tag",
    )
    require(
        packet.get("base_tag_resolves_to_id") is True
        and packet.get("new_image_tag_unused") is True,
        "parent has not confirmed immutable base mapping and unused new tag",
    )
    require(
        packet.get("candidate_export_authorized") is False,
        "this build path cannot authorize a candidate export",
    )
    require(
        packet.get("native_run_authorized") is False,
        "a build-readiness record cannot authorize native execution",
    )
    require(
        packet.get("max_cpu") == 1
        and packet.get("memory_bytes") == 2 * 1024**3
        and packet.get("wall_seconds") == 60,
        "readiness limits do not match the bounded build",
    )
    issued = packet.get("created_unix")
    reference_time = time.time() if now is None else now
    require(
        isinstance(issued, (int, float)) and 0 <= reference_time - issued <= 1800,
        "parent build readiness is absent, future-dated, or older than 30 minutes",
    )
    return packet


def validate_build_input_freeze(
    packet: dict,
    *,
    readiness_sha256: str,
    live_hashes: dict[str, str],
    now: float | None = None,
) -> dict:
    require(
        packet.get("schema") == "ccx223_sti17_build_input_freeze/v1"
        and packet.get("status") == "FROZEN_FOR_ONE_ISOLATED_BUILD",
        "build-input freeze has the wrong status",
    )
    require(
        packet.get("scope")
        == "copy pinned CalculiX 2.23 image source/object tree; rebuild matrixstorage.o only",
        "build-input freeze has another scope",
    )
    require(
        packet.get("base_image_id") == BASE_IMAGE_ID
        and packet.get("new_image_tag") == NEW_IMAGE_TAG,
        "build-input freeze names another image identity",
    )
    require(
        packet.get("parent_readiness_sha256") == readiness_sha256
        and packet.get("parent_validation_sha256") == PARENT_VALIDATION_SHA256
        and packet.get("source_pins_sha256") == SOURCE_PINS_SHA256
        and packet.get("patch_sha256") == PATCH_SHA256,
        "build-input freeze does not bind its readiness and source pins",
    )
    require(
        packet.get("resource_limits")
        == {
            "cpu_count": 1,
            "memory_bytes": 2 * 1024**3,
            "wall_seconds": 60,
        },
        "build-input freeze changed the execution limits",
    )
    require(
        packet.get("native_solver_run") is False
        and packet.get("candidate_matrix_exported") is False
        and packet.get("mechanical_acceptance") is False,
        "build-input freeze widened the scope",
    )
    frozen = packet.get("files_sha256")
    require(isinstance(frozen, dict) and frozen, "build-input freeze has no file pins")
    require(
        REQUIRED_BUILD_FILE_PINS.issubset(frozen),
        "build-input freeze omits a required source pin",
    )
    for relative, expected in frozen.items():
        require(
            live_hashes.get(relative) == expected,
            f"frozen build input changed: {relative}",
        )
    require(
        frozen[READINESS_REL] == readiness_sha256,
        "readiness changed after build-input freeze",
    )
    issued = packet.get("created_unix")
    reference_time = time.time() if now is None else now
    require(
        isinstance(issued, (int, float)) and 0 <= reference_time - issued <= 1800,
        "build-input freeze is absent, future-dated, or older than 30 minutes",
    )
    return packet


def patch_stiffness_writer(original: bytes) -> bytes:
    require(original.count(SOURCE_OLD) == 1, "expected one original stiffness writer")
    require(original.count(MASS_WRITER) == 1, "expected one unchanged mass writer")
    patched = original.replace(SOURCE_OLD, SOURCE_NEW, 1)
    require(
        patched.replace(SOURCE_NEW, SOURCE_OLD, 1) == original,
        "in-memory patch dry-run cannot reproduce the original source",
    )
    require(patched.count(MASS_WRITER) == 1, "mass writer changed")
    require(
        patched == original.replace(SOURCE_OLD, SOURCE_NEW, 1),
        "byte-level source diff is broader than the reviewed format token",
    )
    return patched


def validate_make_plan(stdout: str, archive_members: list[str]) -> list[str]:
    make_lines = [line for line in stdout.splitlines() if line.strip()]
    require(
        len(make_lines) == 3,
        f"make plan is broader than one compile/archive/link: {make_lines}",
    )
    parsed = [shlex.split(line) for line in make_lines]
    compile_lines = [tokens for tokens in parsed if "-c" in tokens]
    require(len(compile_lines) == 1, "make plan must compile exactly one source")
    expected_compile = [
        "gcc",
        "-Wall",
        "-O2",
        "-I/usr/include/spooles",
        "-DARCH=Linux",
        "-DSPOOLES",
        "-DARPACK",
        "-DMATRIXSTORAGE",
        "-DNETWORKOUT",
        "-c",
        "matrixstorage.c",
        "-o",
        "matrixstorage.o",
    ]
    require(
        compile_lines[0] == expected_compile,
        f"make plan changed compile flags or target: {compile_lines[0]}",
    )
    ar_lines = [tokens for tokens in parsed if tokens[:2] == ["ar", "rcs"]]
    require(
        len(ar_lines) == 1 and ar_lines[0][2] == "ccx_2.23.a",
        "make plan did not rebuild the existing archive",
    )
    require(
        ar_lines[0][3:] == archive_members,
        "make plan changed the existing archive member order or membership",
    )
    link_lines = [
        tokens for tokens in parsed if tokens[:3] == ["gfortran", "-O2", "-o"]
    ]
    require(len(link_lines) == 1, "make plan must link exactly once")
    require(
        link_lines[0][3:6] == ["ccx_2.23", "ccx_2.23.o", "ccx_2.23.a"]
        and link_lines[0][6:]
        == [
            "-lspooles",
            "-larpack",
            "-llapack",
            "-lblas",
            "-lpthread",
            "-lm",
            "-fopenmp",
        ],
        "make plan changed the checked-in link recipe",
    )
    return expected_compile


def source_path(root: Path, archive_path: str) -> Path:
    require(archive_path.startswith("./"), f"unexpected source path: {archive_path}")
    return root / archive_path[2:]


def source_hashes(root: Path, inventory: dict[str, str]) -> dict[str, str]:
    result = {}
    for name in sorted(inventory):
        path = source_path(root, name)
        require(path.is_file(), f"pinned upstream source is absent: {path}")
        result[name] = sha_file(path)
    return result


def object_hashes(source: Path) -> dict[str, str]:
    return {
        str(path.relative_to(source)): sha_file(path)
        for path in sorted(source.rglob("*.o"))
        if path.is_file()
    }


def library_hashes(binaries: list[Path]) -> tuple[dict[str, str], dict[str, str]]:
    linked = {}
    paths: set[Path] = set()
    for binary in binaries:
        result = run(["ldd", str(binary)], timeout=15)
        linked[str(binary)] = result.stdout
        for raw in re.findall(r"(/\S+)\s+\(", result.stdout):
            paths.add(Path(raw).resolve())
    hashes = {str(path): sha_file(path) for path in sorted(paths)}
    return hashes, linked


def cgroup_limits() -> tuple[str, str]:
    cpu = Path("/sys/fs/cgroup/cpu.max").read_text().strip()
    memory = Path("/sys/fs/cgroup/memory.max").read_text().strip()
    require(cpu == "100000 100000", f"expected one CPU quota, got {cpu!r}")
    require(memory == str(2 * 1024**3), f"expected 2 GiB memory cap, got {memory!r}")
    return cpu, memory


def check_parent_readiness() -> dict:
    path = HERE / "parent-build-readiness.json"
    require(path.is_file(), "fresh parent-build-readiness.json is required")
    return validate_parent_readiness(json.loads(path.read_text()))


def check_build_input_freeze() -> dict:
    require(
        BUILD_INPUT_FREEZE.is_file(),
        "parent-frozen build-input-freeze.json is required",
    )
    packet = json.loads(BUILD_INPUT_FREEZE.read_text())
    frozen = packet.get("files_sha256")
    require(isinstance(frozen, dict) and frozen, "build-input freeze has no file pins")
    live_hashes = {}
    for relative in frozen:
        path = REPO / relative
        require(path.is_file(), f"frozen build input is absent: {relative}")
        live_hashes[relative] = sha_file(path)
    validated = validate_build_input_freeze(
        packet,
        readiness_sha256=sha_file(HERE / "parent-build-readiness.json"),
        live_hashes=live_hashes,
    )
    readiness = json.loads((HERE / "parent-build-readiness.json").read_text())
    require(
        packet.get("review_binding") == readiness.get("review_binding"),
        "build freeze and readiness name different final reviews",
    )
    validate_review_binding(REPO, packet.get("review_binding"), frozen)
    return validated


def main() -> None:
    started = time.monotonic()
    cpu_quota, memory_limit = cgroup_limits()
    check_parent_readiness()
    build_input_freeze = check_build_input_freeze()

    require(BASE.is_dir(), "immutable base source tree is absent")
    require(not TARGET.exists(), "isolated target tree already exists; do not reuse it")
    require(
        not NEW_BINARY.exists(), "new binary path already exists; do not overwrite it"
    )

    source_pins_path = PREFLIGHT / "source-pins.json"
    patch_path = PREFLIGHT / "precision-only.patch"
    patch_check_path = PREFLIGHT / "patch-source-check-result.json"
    profile_path = REPO / "fea/calculix_223/solver-profile.json"
    recorded_manifest_path = (
        REPO / "fea/generated/calculix-2.23-build-attempt02/build_manifest.json"
    )
    recorded_result_path = (
        REPO / "fea/generated/calculix-2.23-build-attempt02/build_result.json"
    )
    require(
        sha_file(source_pins_path) == SOURCE_PINS_SHA256,
        "preflight source pins changed",
    )
    require(
        sha_file(patch_path) == PATCH_SHA256, "reviewed precision-only patch changed"
    )
    source_pin_record = json.loads(source_pins_path.read_text())
    patch_check_pin = source_pin_record["inputs"]["this_preflight"][
        "patch-source-check-result.json"
    ]
    require(
        patch_check_pin["path"] == str(patch_check_path.relative_to(REPO))
        and sha_file(patch_check_path) == patch_check_pin["sha256"],
        "reviewed patch dry-run receipt changed",
    )
    patch_check = json.loads(patch_check_path.read_text())
    require(
        patch_check.get("patch_dry_run_returncode") == 0
        and patch_check.get("proposed_patch_sha256") == PATCH_SHA256
        and patch_check.get("exact_sti_old_line_count") == 1
        and patch_check.get("exact_mass_old_line_count") == 1
        and patch_check.get("mass_writer_unchanged_by_in_memory_patch") is True
        and patch_check.get("in_memory_reverse_reproduces_original") is True,
        "source-only patch dry-run did not prove the stiffness-only edit",
    )
    require(
        sha_file(PARENT_VALIDATION) == PARENT_VALIDATION_SHA256,
        "cited parent validation changed; obtain fresh parent review",
    )
    require(sha_file(profile_path) == BASE_PROFILE_SHA256, "old solver profile changed")
    require(
        sha_file(recorded_manifest_path) == BASE_MANIFEST_SHA256,
        "recorded base build manifest changed",
    )
    require(
        sha_file(recorded_result_path) == BASE_BUILD_RESULT_SHA256,
        "recorded base build result changed",
    )

    pins = json.loads(source_pins_path.read_text())
    expected_inputs = pins["inputs"]
    require(
        expected_inputs["official_source_archive"]["sha256"] == SOURCE_ARCHIVE_SHA256,
        "source-pins archive identity disagrees",
    )
    require(
        expected_inputs["official_matrixstorage_source_member"]["sha256"]
        == MATRIXSTORAGE_SHA256,
        "source-pins matrixstorage identity disagrees",
    )
    require(
        expected_inputs["existing_toolchain_and_history"]["image_id"] == BASE_IMAGE_ID,
        "source-pins image identity disagrees",
    )
    require(
        expected_inputs["existing_toolchain_and_history"]["binary_sha256"]
        == sha_file(OLD_BINARY),
        "source-pins binary identity disagrees",
    )
    for group_name in ("local_build_recipe", "existing_toolchain_and_history"):
        for label, item in expected_inputs[group_name].items():
            if not isinstance(item, dict) or "path" not in item or "sha256" not in item:
                continue
            pinned_path = REPO / item["path"]
            require(
                pinned_path.is_file() and sha_file(pinned_path) == item["sha256"],
                f"source-pins file changed: {label} ({item['path']})",
            )

    source_archive = BASE / "source.tar.bz2"
    manifest_path = BASE / "build_manifest.json"
    require(
        sha_file(source_archive) == SOURCE_ARCHIVE_SHA256, "base source archive changed"
    )
    require(
        sha_file(manifest_path) == BASE_MANIFEST_SHA256, "base image manifest changed"
    )
    manifest = json.loads(manifest_path.read_text())
    require(
        manifest["upstream_source_archive_sha256"] == SOURCE_ARCHIVE_SHA256,
        "base manifest names another source archive",
    )
    require(
        manifest["binary_sha256"][str(OLD_BINARY)] == sha_file(OLD_BINARY),
        "old 2.23 binary does not match its manifest",
    )
    require(
        manifest["binary_sha256"][str(PACKAGED_BINARY)] == sha_file(PACKAGED_BINARY),
        "packaged solver binary does not match its manifest",
    )

    writer_member = "./CalculiX/ccx_2.23/src/matrixstorage.c"
    with tarfile.open(source_archive, "r:bz2") as archive:
        source_member = archive.extractfile(writer_member)
        require(
            source_member is not None
            and sha_bytes(source_member.read()) == MATRIXSTORAGE_SHA256,
            "pinned archive writer member changed",
        )
    original_sources = source_hashes(BASE, manifest["upstream_files_sha256"])
    require(
        original_sources == manifest["upstream_files_sha256"],
        "base source tree does not match its recorded upstream inventory",
    )
    require(
        manifest["build_support_sha256"]["Makefile.upstream"] == MAKEFILE_SHA256,
        "base manifest has another Makefile",
    )
    base_makefile = BASE / "Makefile.upstream"
    require(sha_file(base_makefile) == MAKEFILE_SHA256, "base Makefile changed")

    for program, recorded in manifest["compiler_versions"].items():
        actual = run([program, "--version"], timeout=10).stdout
        require(actual == recorded, f"compiler/tool version changed: {program}")
    baseline_libraries, _ = library_hashes([PACKAGED_BINARY, OLD_BINARY])
    require(
        baseline_libraries == manifest["linked_library_sha256"],
        "base linked-library set or hash changed",
    )

    base_source = BASE / SOURCE_REL
    base_objects = object_hashes(base_source)
    require("matrixstorage.o" in base_objects, "base matrixstorage.o is missing")
    base_archive = base_source / "ccx_2.23.a"
    base_archive_sha256 = sha_file(base_archive)
    archive_members = run(
        ["ar", "t", str(base_archive)], cwd=base_source
    ).stdout.splitlines()

    shutil.copytree(BASE, TARGET, copy_function=shutil.copy2, symlinks=True)
    target_source = TARGET / SOURCE_REL
    require(
        source_hashes(TARGET, manifest["upstream_files_sha256"]) == original_sources,
        "copy did not preserve the pinned source tree byte-for-byte",
    )
    before_objects = object_hashes(target_source)
    require(
        before_objects == base_objects,
        "copy did not preserve the object tree byte-for-byte",
    )
    target_archive = target_source / "ccx_2.23.a"
    require(
        sha_file(target_archive) == base_archive_sha256, "copy changed the link archive"
    )

    base_writer = (BASE / SOURCE_REL / "matrixstorage.c").read_bytes()
    patched_writer = (target_source / "matrixstorage.c").read_bytes()
    require(
        patched_writer == base_writer, "copied writer changed before patch application"
    )
    patched_writer = patch_stiffness_writer(base_writer)
    (target_source / "matrixstorage.c").write_bytes(patched_writer)
    copied_sources_after_patch = source_hashes(
        TARGET, manifest["upstream_files_sha256"]
    )
    source_differences = [
        name
        for name in original_sources
        if original_sources[name] != copied_sources_after_patch[name]
    ]
    require(
        source_differences == [writer_member],
        f"unexpected changed source files: {source_differences}",
    )
    diff_result = subprocess.run(
        [
            "diff",
            "-u",
            str(BASE / SOURCE_REL / "matrixstorage.c"),
            str(target_source / "matrixstorage.c"),
        ],
        cwd=TARGET,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    require(diff_result.returncode == 1, "expected one source diff after the patch")
    patch_diff = diff_result
    changed_lines = [
        line
        for line in patch_diff.stdout.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    require(
        len(changed_lines) == 2
        and "%20.13e" in changed_lines[0]
        and "%20.16e" in changed_lines[1],
        "byte-level diff does not show the one-token edit",
    )

    target_object = target_source / "matrixstorage.o"
    target_writer = target_source / "matrixstorage.c"
    object_stamp = target_object.stat()
    source_stamp = target_writer.stat()
    if source_stamp.st_mtime_ns <= object_stamp.st_mtime_ns:
        os.utime(
            target_writer, ns=(source_stamp.st_atime_ns, object_stamp.st_mtime_ns + 1)
        )
    require(
        target_writer.stat().st_mtime_ns > target_object.stat().st_mtime_ns,
        "could not make only the patched source newer than its object",
    )

    makefile = TARGET / "Makefile.upstream"
    require(sha_file(makefile) == MAKEFILE_SHA256, "copied Makefile changed")
    dry_make = run(
        ["make", "-n", "-j1", "-f", str(makefile), "ccx_2.23"], cwd=target_source
    )
    expected_compile = validate_make_plan(dry_make.stdout, archive_members)

    build_started = time.monotonic()
    build = subprocess.run(
        ["make", "-j1", "-f", str(makefile), "ccx_2.23"],
        cwd=target_source,
        text=True,
        capture_output=True,
        check=False,
        timeout=55,
    )
    build_elapsed = time.monotonic() - build_started
    (TARGET / "sti17-make.stdout").write_text(build.stdout)
    (TARGET / "sti17-make.stderr").write_text(build.stderr)
    (TARGET / "sti17-make-plan.txt").write_text(dry_make.stdout)
    require(build.returncode == 0, f"narrow make failed: {build.stderr[-1200:]}")
    require(
        build_elapsed <= 55,
        f"narrow make exceeded its 55 second inner bound: {build_elapsed:.3f}",
    )

    after_objects = object_hashes(target_source)
    require(after_objects.keys() == before_objects.keys(), "object inventory changed")
    changed_objects = [
        name for name in before_objects if before_objects[name] != after_objects[name]
    ]
    require(
        changed_objects == ["matrixstorage.o"],
        f"objects besides matrixstorage.o changed: {changed_objects}",
    )
    after_sources = source_hashes(TARGET, manifest["upstream_files_sha256"])
    require(
        [
            name
            for name in original_sources
            if original_sources[name] != after_sources[name]
        ]
        == [writer_member],
        "build modified another upstream source",
    )
    require(
        after_sources[writer_member] == copied_sources_after_patch[writer_member],
        "make modified the patched source",
    )
    archive_members_after = run(
        ["ar", "t", str(target_archive)], cwd=target_source
    ).stdout.splitlines()
    require(
        archive_members_after == archive_members,
        "rebuilt archive changed object membership or order",
    )

    built_binary = target_source / "ccx_2.23"
    require(built_binary.is_file(), "make did not produce the new copied-tree binary")
    run(["install", "-m755", str(built_binary), str(NEW_BINARY)], timeout=10)
    require(
        sha_file(OLD_BINARY) == manifest["binary_sha256"][str(OLD_BINARY)],
        "original 2.23 executable changed",
    )
    require(
        sha_file(PACKAGED_BINARY) == manifest["binary_sha256"][str(PACKAGED_BINARY)],
        "packaged executable changed",
    )
    require(
        sha_file(manifest_path) == BASE_MANIFEST_SHA256,
        "original build manifest changed",
    )
    require(
        sha_file(BASE / "source.tar.bz2") == SOURCE_ARCHIVE_SHA256,
        "original source archive changed",
    )
    base_support_after = {
        name: sha_file(BASE / name) for name in manifest["build_support_sha256"]
    }
    require(
        base_support_after == manifest["build_support_sha256"],
        "original build-support files changed",
    )
    require(
        source_hashes(BASE, manifest["upstream_files_sha256"]) == original_sources,
        "original source tree changed",
    )
    require(object_hashes(base_source) == base_objects, "original object tree changed")
    require(sha_file(base_archive) == base_archive_sha256, "original archive changed")
    require(
        sha_file(profile_path) == BASE_PROFILE_SHA256, "original solver profile changed"
    )

    new_libraries, new_ldd = library_hashes([PACKAGED_BINARY, OLD_BINARY, NEW_BINARY])
    require(
        new_libraries == baseline_libraries,
        "new executable resolved a different shared-library set or hash",
    )
    require(
        sha_file(NEW_BINARY) != sha_file(OLD_BINARY),
        "new binary unexpectedly matches the unpatched executable",
    )

    receipt = {
        "schema": "ccx223_sti17_build_receipt/v1",
        "status": "PASS_BUILD_ONLY",
        "base_image_tag": BASE_IMAGE_TAG,
        "base_image_id": BASE_IMAGE_ID,
        "new_image_tag": NEW_IMAGE_TAG,
        "new_image_id": None,
        "source_pins_sha256": SOURCE_PINS_SHA256,
        "parent_validation_sha256": PARENT_VALIDATION_SHA256,
        "source_archive_sha256": sha_file(source_archive),
        "base_build_manifest_sha256": sha_file(manifest_path),
        "build_input_freeze_sha256": sha_file(BUILD_INPUT_FREEZE),
        "build_input_freeze_files_sha256": build_input_freeze["files_sha256"],
        "base_old_profile_sha256": BASE_PROFILE_SHA256,
        "patch_sha256": sha_file(patch_path),
        "patch_dry_run_receipt": patch_check,
        "patch_application": "one exact in-memory byte replacement after reversible dry-run check",
        "source_diff": patch_diff.stdout,
        "source_sha256_before": original_sources,
        "source_sha256_after": after_sources,
        "object_sha256_before": before_objects,
        "object_sha256_after": after_objects,
        "changed_objects": changed_objects,
        "archive_sha256_before": base_archive_sha256,
        "archive_sha256_after": sha_file(target_archive),
        "archive_member_order_before": archive_members,
        "archive_member_order_after": archive_members_after,
        "compiler_versions": manifest["compiler_versions"],
        "compile_flags": expected_compile[1:-4],
        "make_dry_run": dry_make.stdout,
        "make_stdout_sha256": sha_file(TARGET / "sti17-make.stdout"),
        "make_stderr_sha256": sha_file(TARGET / "sti17-make.stderr"),
        "build_elapsed_seconds": build_elapsed,
        "resource_limits": {
            "cpu.max": cpu_quota,
            "memory.max_bytes": int(memory_limit),
            "outer_wall_seconds": 60,
        },
        "linked_library_sha256": new_libraries,
        "linked_libraries_ldd": new_ldd,
        "old_binary_path": str(OLD_BINARY),
        "old_binary_sha256": sha_file(OLD_BINARY),
        "new_binary_path": str(NEW_BINARY),
        "new_binary_sha256": sha_file(NEW_BINARY),
        "parent_readiness_sha256": sha_file(HERE / "parent-build-readiness.json"),
        "candidate_matrix_exported": False,
        "native_solver_run": False,
        "mechanical_acceptance": False,
    }
    (TARGET / "sti17-build-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    total_elapsed = time.monotonic() - started
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "binary_sha256": receipt["new_binary_sha256"],
                "make_elapsed_seconds": build_elapsed,
                "script_elapsed_seconds": total_elapsed,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
