"""Apply and compile the frozen-in-this-context output-only 2.23 patch."""
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
BASE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-v1"
PATCHED_BIN = "/usr/local/bin/ccx-bounded-contact-capture-2.23"
TARGETS = [
    "CalculiX/ccx_2.23/src/nonlingeo.c",
    "CalculiX/ccx_2.23/src/gencontelem_f2f.f",
]
BASE_BINARIES = {
    "/usr/bin/ccx": "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b",
    "/usr/local/bin/ccx-upstream-2.23": "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return sha(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def apply_section(original: bytes, patch_lines: list[str], name: str) -> bytes:
    current = original.decode("utf-8").splitlines(keepends=True)
    offset = 0
    i = 0
    while i < len(patch_lines):
        hunk = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", patch_lines[i])
        require(hunk is not None, f"invalid hunk in {name}: {patch_lines[i]!r}")
        old_start = int(hunk.group(1))
        old_count = int(hunk.group(2) or "1")
        new_start = int(hunk.group(3))
        new_count = int(hunk.group(4) or "1")
        i += 1
        old_lines: list[str] = []
        new_lines: list[str] = []
        while i < len(patch_lines) and not patch_lines[i].startswith("@@ "):
            line = patch_lines[i]
            if line.startswith(" "):
                old_lines.append(line[1:]);new_lines.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith("-"):
                raise RuntimeError(f"capture patch removes upstream source in {name}")
            elif line.startswith("\\ No newline"):
                raise RuntimeError(f"unexpected no-newline marker in {name}")
            else:
                raise RuntimeError(f"invalid patch line in {name}: {line!r}")
            i += 1
        require(len(old_lines) == old_count and len(new_lines) == new_count,
                f"hunk size mismatch in {name}")
        position = old_start - 1 if old_count else old_start
        actual = position + offset
        require(new_start - 1 == actual, f"patch offset mismatch in {name}")
        require(current[actual:actual + old_count] == old_lines,
                f"patch context mismatch in {name}")
        current[actual:actual + old_count] = new_lines
        offset += new_count - old_count
    result = "".join(current).encode("utf-8")
    tags = [tag for tag, *_ in difflib.SequenceMatcher(
        a=original.decode().splitlines(keepends=True),
        b=result.decode().splitlines(keepends=True),autojunk=False).get_opcodes()
        if tag != "equal"]
    require(all(tag == "insert" for tag in tags), f"non-additive edit in {name}")
    return result


def parse_patch(path: Path) -> dict[str, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    sections: dict[str, list[str]] = {}
    i = 0
    order: list[str] = []
    while i < len(lines):
        if not lines[i].startswith("--- a/"):
            raise RuntimeError(f"invalid patch header at line {i+1}")
        old = lines[i].strip().removeprefix("--- a/")
        require(i + 1 < len(lines) and lines[i + 1].startswith("+++ b/"),
                "unpaired patch header")
        new = lines[i + 1].strip().removeprefix("+++ b/")
        require(old == new and old in TARGETS, f"unexpected patch target {old!r}")
        i += 2
        start = i
        while i < len(lines) and not lines[i].startswith("--- a/"):
            i += 1
        sections[old] = lines[start:i]
        order.append(old)
    require(order == TARGETS, "patch target order/set differs from lock")
    return sections


def main() -> None:
    require(os.environ.get("CCX_BASE_IMAGE_ID") == BASE_ID, "base image ID is not the pinned 2.23 image")
    archive = ROOT / "source.tar.bz2"
    patch_path = ROOT / "capture.patch"
    prepared = json.loads((ROOT / "patch-preparation.json").read_text())
    manifest = json.loads((ROOT / "base-build-manifest.json").read_text())
    require(digest(archive) == prepared["source_archive_sha256"] == manifest["upstream_source_archive_sha256"],
            "source archive hash differs from both preparation and base manifest")
    require(digest(patch_path) == prepared["patch_sha256"], "patch hash differs from preparation")
    require(manifest["qualification"].startswith("Unmodified upstream2.23"),
            "base image manifest is not the expected upstream source/build record")

    source_hashes: dict[str, str] = {}
    with tarfile.open(archive, "r:bz2") as tar:
        for member in tar.getmembers():
            if member.isfile():
                data = tar.extractfile(member).read()
                source_hashes[member.name.removeprefix("./")] = sha(data)
    manifest_hashes = {name.removeprefix("./"): value
                       for name, value in manifest["upstream_files_sha256"].items()}
    require(source_hashes == manifest_hashes, "complete archive source manifest mismatch")
    for name in TARGETS:
        require(source_hashes[name] == prepared["targets"][name]["upstream_sha256"],
                f"source member hash mismatch: {name}")
    tarfile.open(archive, "r:bz2").extractall(ROOT, filter="data")

    sections = parse_patch(patch_path)
    modified: dict[str, str] = {}
    for name in TARGETS:
        path = ROOT / name
        before = path.read_bytes()
        after = apply_section(before, sections[name], name)
        path.write_bytes(after)
        require(sha(after) == prepared["targets"][name]["modified_sha256"],
                f"patched source hash mismatch: {name}")
        modified[name] = sha(after)

    original_bins_before = {name: digest(Path(name)) for name in BASE_BINARIES}
    require(original_bins_before == BASE_BINARIES, "base executable hashes differ before build")
    source_dir = ROOT / "CalculiX/ccx_2.23/src"
    command = ["make", "-C", str(source_dir), "-f", str(ROOT / "Makefile.upstream"), "-j2"]
    subprocess.run(command, check=True)
    built = source_dir / "ccx_2.23"
    require(built.is_file(), "upstream build did not produce ccx_2.23")
    destination = Path(PATCHED_BIN)
    require(not destination.exists(), "refusing to overwrite a dedicated capture binary")
    shutil.copy2(built, destination);destination.chmod(0o755)
    symbol_text = subprocess.run(["nm", "-g", str(destination)], check=True,
                                 capture_output=True, text=True).stdout
    for symbol in ("ccxcap_generation_begin_", "ccxcap_face_", "ccxcap_point_",
                   "ccxcap_trial_", "ccxcap_iteration_link_", "ccxcap_finish_"):
        require(symbol in symbol_text, f"capture symbol missing from built executable: {symbol}")
    original_bins_after = {name: digest(Path(name)) for name in BASE_BINARIES}
    require(original_bins_after == BASE_BINARIES, "build modified an upstream executable")

    context_files = ["Dockerfile", "Makefile.upstream", "record_capture_build.py",
                     "source.tar.bz2", "capture.patch", "patch-preparation.json",
                     "base-build-manifest.json"]
    report = {
        "schema": "ccx223_bounded_contact_capture_build/v1",
        "base_image_tag": BASE_TAG,
        "base_image_id": BASE_ID,
        "source_archive_sha256": digest(archive),
        "complete_source_manifest_match": True,
        "upstream_source_file_count": len(source_hashes),
        "capture_patch_sha256": digest(patch_path),
        "patch_preparation_sha256": digest(ROOT / "patch-preparation.json"),
        "source_targets": TARGETS,
        "upstream_source_sha256": {name: source_hashes[name] for name in TARGETS},
        "modified_source_sha256": modified,
        "edit_policy": "Every upstream line is byte-preserved and in order; all source delta hunks are insertions.",
        "mechanics_invariance_scope": "This establishes source-level nonreplacement only. Capture implementation is separately limited to private memory and an append-exclusive sidecar output; it has no writes to native mechanics arrays.",
        "build_command": command,
        "build_context_sha256": {name: digest(ROOT / name) for name in context_files},
        "upstream_binary_sha256_before_and_after": original_bins_before,
        "dedicated_capture_binary": PATCHED_BIN,
        "dedicated_capture_binary_sha256": digest(destination),
        "capture_symbols_present": True,
        "native_solver_case_run": False,
        "mechanical_acceptance": False,
    }
    report_path = ROOT / "build-manifest.json"
    if report_path.exists():
        raise RuntimeError("refusing to overwrite build-manifest.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for path in source_dir.glob("*.o"):
        path.unlink()
    for path in (source_dir / "ccx_2.23.a", built):
        if path.exists():path.unlink()


if __name__ == "__main__":
    main()
