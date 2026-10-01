"""Build a pinned diagnostic CalculiX 2.23 executable without replacing history."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parent
BASE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
ARCHIVE_SHA = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
PATCH_SHA = "aea55ec88be569a39a06482723d5da22260b071bf072c55491448b22ab273e54"
ORIGINAL_BINARIES = {
    "/usr/bin/ccx": "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b",
    "/usr/local/bin/ccx-upstream-2.23":
        "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
}
PATCHED_BINARY = "/usr/local/bin/ccx-attempt04-diagnostic-2.23"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalize_archive_path(path: str) -> str:
    return path.removeprefix("./")


def insertion_only(before: bytes, after: bytes, path: str) -> None:
    left = before.decode("utf-8").splitlines(keepends=True)
    right = after.decode("utf-8").splitlines(keepends=True)
    edits = [tag for tag, *_ in difflib.SequenceMatcher(
        a=left, b=right, autojunk=False).get_opcodes() if tag != "equal"]
    require(all(tag == "insert" for tag in edits),
            f"patch changed or removed upstream text in {path}")


def apply_exact_patch(original: bytes, patch_lines: list[str], path: str) -> bytes:
    current = original.decode("utf-8").splitlines(keepends=True)
    index = 0
    offset = 0
    while index < len(patch_lines):
        header = re.match(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", patch_lines[index])
        require(header is not None, f"invalid unified-diff hunk in {path}")
        old_start = int(header.group(1))
        old_count = int(header.group(2) or "1")
        new_start = int(header.group(3))
        new_count = int(header.group(4) or "1")
        index += 1
        old_lines: list[str] = []
        new_lines: list[str] = []
        while index < len(patch_lines) and not patch_lines[index].startswith("@@ "):
            line = patch_lines[index]
            if line.startswith(" "):
                old_lines.append(line[1:])
                new_lines.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith("-"):
                old_lines.append(line[1:])
            elif line.startswith("\\ No newline"):
                raise RuntimeError("patch unexpectedly changes a no-newline marker")
            else:
                raise RuntimeError(f"invalid unified-diff line in {path}")
            index += 1
        require(len(old_lines) == old_count and len(new_lines) == new_count,
                f"unified-diff hunk length differs in {path}")
        position = old_start - 1 if old_count else old_start
        actual = position + offset
        require(new_start - 1 == actual,
                f"unified-diff line offset differs in {path}")
        require(current[actual:actual + old_count] == old_lines,
                f"unified-diff context differs in {path}")
        current[actual:actual + old_count] = new_lines
        offset += new_count - old_count
    return "".join(current).encode("utf-8")


def main() -> None:
    base_image = os.environ.get("CCX_BASE_IMAGE", "")
    require(base_image == BASE_ID, "build base image ID is not pinned")
    lock = json.loads((ROOT / "diagnostic-lock.json").read_text())
    manifest = json.loads((ROOT / "base-build-manifest.json").read_text())
    archive = ROOT / "source.tar.bz2"
    patch_file = ROOT / "diagnostic.patch"
    require(file_sha(archive) == ARCHIVE_SHA ==
            lock["official_source_archive"]["sha256"],
            "official 2.23 archive hash differs from the diagnostic lock")
    require(file_sha(patch_file) == PATCH_SHA == lock["patch"]["sha256"],
            "diagnostic patch hash differs from the diagnostic lock")
    require(manifest["upstream_source_archive_sha256"] == ARCHIVE_SHA,
            "base image source manifest binds a different source archive")

    original_files: dict[str, bytes] = {}
    actual_manifest: dict[str, str] = {}
    with tarfile.open(archive, mode="r:bz2") as tar:
        for item in tar.getmembers():
            if item.isfile():
                content = tar.extractfile(item).read()
                path = normalize_archive_path(item.name)
                actual_manifest[path] = sha256(content)
                original_files[path] = content
        expected_manifest = {
            normalize_archive_path(path): digest
            for path, digest in manifest["upstream_files_sha256"].items()
        }
        require(actual_manifest == expected_manifest,
                "official archive differs from the complete base source manifest")
        for path, expected in lock["source_members_sha256"].items():
            require(actual_manifest.get(path) == expected,
                    f"locked source-member hash differs: {path}")
        tar.extractall(path=ROOT, filter="data")

    patch_bytes = patch_file.read_bytes()
    patch_text = patch_bytes.decode("utf-8")
    targets = []
    lines = patch_text.splitlines()
    sections: dict[str, list[str]] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("--- "):
            require(index + 1 < len(lines) and lines[index + 1].startswith("+++ "),
                    "unpaired patch header")
            old = line.removeprefix("--- a/")
            new = lines[index + 1].removeprefix("+++ b/")
            require(old == new and old != line and new != lines[index + 1],
                    "patch renamed a source file")
            targets.append(old)
            index += 2
            start = index
            while index < len(lines) and not lines[index].startswith("--- "):
                if lines[index].startswith("-") and not lines[index].startswith("--- "):
                    raise RuntimeError("diagnostic patch deletes or replaces source text")
                index += 1
            sections[old] = lines[start:index]
        else:
            index += 1
    require(targets == lock["patch"]["source_targets"],
            "patch target list differs from the diagnostic lock")
    patched_sha = {}
    for relative in targets:
        path = ROOT / relative
        before = path.read_bytes()
        path.write_bytes(apply_exact_patch(before, sections[relative], relative))
        current = (ROOT / relative).read_bytes()
        insertion_only(before, current, relative)
        marker = "CCX223_ATTEMPT04_CONTACT" if relative.endswith("nonlingeo.c") else \
            "CCX223_ATTEMPT04_CONVERGENCE"
        require(current.decode("utf-8").count(marker) == 1,
                f"expected trace marker missing or duplicated in {relative}")
        patched_sha[relative] = sha256(current)

    before_binaries = {path: file_sha(Path(path)) for path in ORIGINAL_BINARIES}
    require(before_binaries == ORIGINAL_BINARIES,
            "an unpatched historical solver binary differs from its pin")
    source_dir = ROOT / "CalculiX/ccx_2.23/src"
    subprocess.run(
        ["make", "-C", str(source_dir), "-f", str(ROOT / "Makefile.upstream"), "-j2"],
        check=True)
    built = source_dir / "ccx_2.23"
    require(built.is_file(), "upstream make did not produce ccx_2.23")
    destination = Path(PATCHED_BINARY)
    require(not destination.exists(), "diagnostic executable path already exists")
    shutil.copy2(built, destination)
    destination.chmod(0o755)
    after_binaries = {path: file_sha(Path(path)) for path in ORIGINAL_BINARIES}
    require(after_binaries == ORIGINAL_BINARIES,
            "building the diagnostic executable changed a historical binary")

    context_inputs = (
        "Dockerfile", "Makefile.upstream", "record_build.py", "source.tar.bz2",
        "diagnostic.patch", "diagnostic-lock.json", "base-build-manifest.json")
    report = {
        "schema": "calculix_223_attempt04_source_diagnostic_build/v1",
        "base_image_id": base_image,
        "upstream_source_archive_sha256": file_sha(archive),
        "upstream_file_count": len(actual_manifest),
        "complete_source_manifest_match": True,
        "diagnostic_lock_sha256": file_sha(ROOT / "diagnostic-lock.json"),
        "patch_sha256": file_sha(patch_file),
        "patch_targets": targets,
        "patch_edit_policy": "additions only; zero fuzz; no solver logic replaced",
        "original_source_member_sha256": lock["source_members_sha256"],
        "patched_source_member_sha256": patched_sha,
        "build_command": ["make", "-C", str(source_dir), "-f",
                           str(ROOT / "Makefile.upstream"), "-j2"],
        "build_context_sha256": {
            name: file_sha(ROOT / name) for name in context_inputs
        },
        "historical_binary_sha256_before_and_after": before_binaries,
        "patched_binary_path": PATCHED_BINARY,
        "patched_binary_sha256": file_sha(destination),
        "mechanical_acceptance": False,
        "qualification": "Output-only trace instrumentation; no joint acceptance.",
    }
    for generated in source_dir.glob("*.o"):
        generated.unlink()
    for generated in (source_dir / "ccx_2.23.a", built):
        if generated.exists():
            generated.unlink()
    (ROOT / "build_manifest.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
