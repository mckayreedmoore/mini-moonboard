#!/usr/bin/env python3
"""Statically verify attempt03 bindings and apply the source-only patch."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path


ARTIFACT = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def verify_attempt03(repo_root: Path, binding: dict) -> None:
    attempt03 = repo_root / binding["attempt03_path"]
    execution_path = attempt03 / "execution.json"
    execution_bytes = execution_path.read_bytes()
    execution = json.loads(execution_bytes)
    force_path = attempt03 / "force-freeze.json"
    force_freeze = read_json(force_path)
    input_path = attempt03 / "input-freeze.json"
    readiness_path = attempt03 / "independent-readiness.json"

    require(sha256(execution_bytes) == binding["execution_sha256"],
            "attempt03 execution record hash differs")
    require(sha256(force_path.read_bytes()) == binding["force_freeze_sha256"],
            "attempt03 force freeze hash differs")
    require(sha256(input_path.read_bytes()) == binding["input_freeze_sha256"],
            "attempt03 input freeze hash differs")
    require(sha256(readiness_path.read_bytes()) == binding["readiness_sha256"],
            "attempt03 readiness record hash differs")
    require(execution["force_freeze_sha256"] == binding["force_freeze_sha256"],
            "execution force freeze binding differs")
    require(execution["input_freeze_sha256"] == binding["input_freeze_sha256"],
            "execution input freeze binding differs")
    require(execution["readiness_sha256"] == binding["readiness_sha256"],
            "execution readiness binding differs")
    require(execution["solver_binary_sha256"] == binding["solver_binary_sha256"],
            "attempt03 solver binary binding differs")
    require(force_freeze["solver_image"] == binding["solver_image_id"],
            "attempt03 solver image binding differs")
    require(force_freeze["solver_binary_path"] == binding["solver_binary_path"],
            "attempt03 solver binary path binding differs")
    require(force_freeze["solver_binary_sha256"] == binding["solver_binary_sha256"],
            "attempt03 frozen solver binary hash differs")
    command = execution["command"]
    require(command[-4:] == [
        binding["solver_image_id"], binding["solver_binary_path"], "-i", "pilot"],
        "attempt03 solver image/path differ from the executed command")
    require(execution["frozen_inputs_unchanged"] is True,
            "attempt03 did not record unchanged frozen inputs")

    frozen = read_json(force_path)["artifacts_sha256"]
    require(frozen == binding["frozen_artifacts_sha256"],
            "attempt03 frozen artifact manifest differs")
    require(frozen.get("pilot.inp") == binding["pilot_inp_sha256"],
            "attempt03 pilot.inp binding differs")
    for name, expected in frozen.items():
        path = attempt03 / name
        require(path.is_file(), f"attempt03 input is missing: {name}")
        require(sha256(path.read_bytes()) == expected,
                f"attempt03 frozen artifact hash differs: {name}")

    expected_output_names = {
        "pilot.12d", "pilot.cel", "pilot.cvg", "pilot.dat", "pilot.frd",
        "pilot.sta", "pilot.stdout", "spooles.out",
        "ResultsForLastIterations.frd",
    }
    require(set(execution["outputs_sha256"]) == expected_output_names,
            "attempt03 execution output set differs")
    require(set(binding["outputs_sha256"]) == expected_output_names,
            "attempt03 bound output set differs")
    for name, expected in binding["outputs_sha256"].items():
        require(execution["outputs_sha256"].get(name) == expected,
                f"attempt03 output record differs: {name}")
        require(sha256((attempt03 / name).read_bytes()) == expected,
                f"attempt03 output hash differs: {name}")


def patch_targets(patch_text: str) -> list[str]:
    lines = patch_text.splitlines()
    targets = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("--- "):
            require(index + 1 < len(lines) and lines[index + 1].startswith("+++ "),
                    "unpaired unified diff headers")
            old_path = line.removeprefix("--- a/")
            new_path = lines[index + 1].removeprefix("+++ b/")
            require(old_path != line and new_path != lines[index + 1],
                    "patch paths must use a/ and b/ headers")
            require(old_path == new_path, "patch renames a source file")
            targets.append(old_path)
            index += 2
            continue
        if line.startswith("-") and not line.startswith("--- "):
            raise SystemExit("FAIL: patch deletes or replaces source text")
        index += 1
    return targets


def source_members(archive_path: Path, expected_members: dict) -> dict[str, bytes]:
    contents = {}
    with tarfile.open(archive_path, mode="r:bz2") as archive:
        by_path = {}
        for member in archive.getmembers():
            name = member.name[2:] if member.name.startswith("./") else member.name
            by_path.setdefault(name, []).append(member)
        for path, expected_hash in expected_members.items():
            matches = by_path.get(path, [])
            require(len(matches) == 1 and matches[0].isfile(),
                    f"archive member missing or ambiguous: {path}")
            stream = archive.extractfile(matches[0])
            require(stream is not None, f"could not read archive member: {path}")
            data = stream.read()
            require(sha256(data) == expected_hash,
                    f"pinned source member hash differs: {path}")
            contents[path] = data
    return contents


def require_insertions_only(before: bytes, after: bytes, path: str) -> None:
    old_lines = before.decode("utf-8").splitlines(keepends=True)
    new_lines = after.decode("utf-8").splitlines(keepends=True)
    opcodes = difflib.SequenceMatcher(
        a=old_lines, b=new_lines, autojunk=False).get_opcodes()
    changed = [tag for tag, _, _, _, _ in opcodes if tag != "equal"]
    require(all(tag == "insert" for tag in changed),
            f"patched source changed or removed original text: {path}")


def verify_and_apply(archive_path: Path, repo_root: Path) -> None:
    lock = read_json(ARTIFACT / "diagnostic-lock.json")
    binding = read_json(ARTIFACT / "attempt03-input-binding.json")
    binding_bytes = (ARTIFACT / "attempt03-input-binding.json").read_bytes()
    require(sha256(binding_bytes) == lock["attempt03_binding_sha256"],
            "attempt03 input/output binding hash differs")
    patch_path = ARTIFACT / lock["patch"]["path"]
    patch_bytes = patch_path.read_bytes()
    patch_text = patch_bytes.decode("utf-8")

    require(sha256(patch_bytes) == lock["patch"]["sha256"],
            "diagnostic patch hash differs")
    require(sha256(archive_path.read_bytes()) ==
            lock["official_source_archive"]["sha256"],
            "source archive does not match pinned CalculiX 2.23 archive")
    targets = patch_targets(patch_text)
    expected_targets = lock["patch"]["source_targets"]
    require(targets == expected_targets,
            "patch target list differs from diagnostic lock")
    require("CCX223_ATTEMPT04_CONTACT" in patch_text and
            "CCX223_ATTEMPT04_CONVERGENCE" in patch_text,
            "patch is missing structured trace events")

    verify_attempt03(repo_root, binding)
    originals = source_members(archive_path, lock["source_members_sha256"])

    patch_program = shutil.which("patch")
    require(patch_program is not None, "the standard patch utility is required")
    with tempfile.TemporaryDirectory(prefix="ccx223-attempt04-static-") as tmp:
        source_root = Path(tmp)
        for path, data in originals.items():
            staged = source_root / path
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(data)
        result = subprocess.run(
            [patch_program, "--batch", "--fuzz=0", "-p1", "--no-backup-if-mismatch"],
            input=patch_text,
            text=True,
            capture_output=True,
            cwd=source_root,
            check=False,
        )
        require(result.returncode == 0,
                f"patch application failed: {result.stdout}{result.stderr}")
        staged_files = {str(path.relative_to(source_root))
                        for path in source_root.rglob("*") if path.is_file()}
        require(staged_files == set(expected_targets),
                "patch application created unexpected files")
        for path, original in originals.items():
            patched = (source_root / path).read_bytes()
            require_insertions_only(original, patched, path)
            marker = ("CCX223_ATTEMPT04_CONTACT" if path.endswith("nonlingeo.c")
                      else "CCX223_ATTEMPT04_CONVERGENCE")
            require(patched.decode("utf-8").count(marker) == 1,
                    f"trace marker missing or duplicated: {path}")

    print("PASS: pinned CalculiX archive and source-member hashes")
    print("PASS: attempt03 image/command, 44 inputs, and all 9 recorded outputs")
    print("PASS: two-file patch applies with zero fuzz and only inserts text")
    print("No build or solver was run.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", required=True, type=Path)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[5])
    args = parser.parse_args()
    verify_and_apply(args.source_archive.resolve(), args.repo_root.resolve())


if __name__ == "__main__":
    main()
