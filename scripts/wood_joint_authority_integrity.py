"""Verify selected-candidate authorities and the wood-joint source exports.

This evidence pins the bytes available at the wood-joints handoff commit. It
does not qualify the selected candidate or transfer any structural result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
OUTPUT = ROOT / "docs/wood-joints-mvp/authority-integrity.json"
EXPORT_PARTS = "site/hybrid/compact-floor-flush-kerf-right/parts.json"
AUTHORITY_PATHS = ("current-candidate.json", "barrel-nut-candidate.json")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _baseline_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout


def _export_tree(commit: str | None) -> dict:
    manifest_path = ROOT / EXPORT_PARTS
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    rows = manifest.get("parts")
    if not isinstance(rows, list) or len(rows) != 725:
        raise ValueError("Expected the reviewed kerf-right export to contain 725 parts")
    identities = [(row["name"], row["path"]) for row in rows]
    if len({name for name, _ in identities}) != len(identities):
        raise ValueError("Kerf-right export part names must be unique")
    if len({path for _, path in identities}) != len(identities):
        raise ValueError("Kerf-right export paths must be unique")

    leaves = []
    baseline_digests = {}
    differences = []
    for name, relative_path in sorted(identities):
        repo_path = f"site/{relative_path}"
        current_path = ROOT / repo_path
        current_bytes = current_path.read_bytes()
        current_digest = _sha(current_bytes)
        baseline_digest = None
        if commit is not None:
            baseline_digest = _sha(_baseline_bytes(commit, repo_path))
            baseline_digests[repo_path] = baseline_digest
            if current_digest != baseline_digest:
                differences.append(repo_path)
        leaves.append(f"{name}\0{relative_path}\0{current_digest}\n".encode())

    current_tree = _sha(b"".join(leaves))
    baseline_manifest_digest = None
    baseline_tree = None
    manifest_matches = None
    if commit is not None:
        baseline_manifest = _baseline_bytes(commit, EXPORT_PARTS)
        baseline_manifest_digest = _sha(baseline_manifest)
        manifest_matches = manifest_bytes == baseline_manifest
        baseline_rows = json.loads(baseline_manifest).get("parts", [])
        if len(baseline_rows) != len(identities):
            raise ValueError("Handoff export part count differs from the current manifest")
        baseline_leaves = []
        for name, relative_path in sorted(
            (row["name"], row["path"]) for row in baseline_rows
        ):
            repo_path = f"site/{relative_path}"
            digest = baseline_digests.get(repo_path)
            if digest is None:
                digest = _sha(_baseline_bytes(commit, repo_path))
            baseline_leaves.append(
                f"{name}\0{relative_path}\0{digest}\n".encode()
            )
        baseline_tree = _sha(b"".join(baseline_leaves))

    return {
        "path": EXPORT_PARTS,
        "manifest_sha256": _sha(manifest_bytes),
        "baseline_manifest_sha256": baseline_manifest_digest,
        "manifest_matches_handoff": manifest_matches,
        "part_count": len(identities),
        "current_export_tree_sha256": current_tree,
        "handoff_export_tree_sha256": baseline_tree,
        "all_export_bytes_match_handoff": not differences if commit is not None else None,
        "differing_export_paths": differences,
    }


def report() -> dict:
    inventory = json.loads(INVENTORY.read_text())
    source_commit = inventory["source_commit"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    authority = {}
    for relative_path in AUTHORITY_PATHS:
        current = (ROOT / relative_path).read_bytes()
        baseline = _baseline_bytes(source_commit, relative_path)
        authority[relative_path] = {
            "current_sha256": _sha(current),
            "handoff_sha256": _sha(baseline),
            "matches_handoff": current == baseline,
        }

    export = _export_tree(source_commit)
    candidate = json.loads((ROOT / "wood-joints-candidate.json").read_text())
    flags = candidate.get("release_flags", {})
    return {
        "schema": "wood_joint_authority_integrity/v1",
        "candidate": candidate["candidate"],
        "handoff_commit": source_commit,
        "repository_head": head,
        "authority_files": authority,
        "selected_kerf_right_exports": export,
        "wood_joint_release_flags": flags,
        "all_release_flags_false": bool(flags) and not any(flags.values()),
        "preservation_check_passes": (
            all(row["matches_handoff"] for row in authority.values())
            and export["manifest_matches_handoff"]
            and export["all_export_bytes_match_handoff"]
            and bool(flags)
            and not any(flags.values())
        ),
        "claim_limit": "Byte-preservation evidence only; no design, geometry, capacity, case, physical inspection or release is established.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = report()
    if not result["preservation_check_passes"]:
        raise SystemExit(json.dumps(result, indent=2, sort_keys=True))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
