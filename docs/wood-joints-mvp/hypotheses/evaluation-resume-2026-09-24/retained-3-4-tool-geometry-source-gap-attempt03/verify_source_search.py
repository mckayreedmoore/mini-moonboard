#!/usr/bin/env python3
"""Verify attempt03's local packet and unchanged attempt02/review evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
ATTEMPT02 = BASE / "retained-3-4-tool-geometry-source-gap-attempt02"
REVIEW02 = BASE / "retained-3-4-tool-geometry-source-gap-attempt02-independent-review-2026-09-28"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    audit = json.loads((HERE / "source-audit.json").read_text(encoding="utf-8"))
    terminal = json.loads((HERE / "terminal-hashes.json").read_text(encoding="utf-8"))
    checked = 0
    for row in terminal["artifacts"]:
        path = HERE / row["path"]
        require(path.is_file(), f"missing packet artifact: {row['path']}")
        require(digest(path) == row["sha256"], f"packet hash mismatch: {row['path']}")
        checked += 1

    require(audit["decision"] == "NO_NEW_EXACT_PART_GEOMETRY_FOUND_IN_CHECKED_WERA_ROUTES", "unexpected decision")
    require(audit["target"]["part_number"] == "05073287001", "wrong target part")
    require(audit["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1", "geometry revision changed")
    require(audit["scope_and_disposition"]["full_profile_or_exact_part_cad_found"] is False, "unexpected geometry result")
    require(audit["scope_and_disposition"]["raw_source_bytes_downloaded"] is False, "raw bytes were not available")
    require(audit["scope_and_disposition"]["tool_selected"] is False, "tool selection prohibited")
    require(audit["scope_and_disposition"]["geometry_changed"] is False, "geometry changed")
    require(audit["scope_and_disposition"]["tool_motion_or_fit_screen_run"] is False, "fit screen run")
    require(audit["scope_and_disposition"]["native_solver_or_docker_run"] is False, "native execution recorded")
    require(len(audit["target"]["retained_target_axes"]) == 4, "target axis count changed")
    require(all(row["complete_profile_coverage"] is False for row in audit["manufacturer_routes"]), "complete profile asserted")
    require(audit["prior_context"]["attempt02_and_review_files_unchanged"] is True, "prior attempt not marked unchanged")

    predecessor_pins = {
        ATTEMPT02 / "README.md": "e25e475083b65ab906fdcf60bf3df344137687c667fa2c9a0d099a52ae7d8048",
        ATTEMPT02 / "source-gap.json": "f26e741d6125515cd1d14f93d1f7c9eba7db8901cbba3006ba73bc070fb72366",
        ATTEMPT02 / "source-pins.json": "647a606354f4f56198dbd33d0cda7e87ebec8939575e347fa1bc643ba20982b9",
        ATTEMPT02 / "verify_source_gap.py": "21c67b0e51541493f0797c263dec238a13feb2d0a819fe78539ab6158a8335b6",
        REVIEW02 / "README.md": "f25b74bbd18b08f761e6d5c54a992392ea064ea7f4835d64517a86bbabdf775e",
        REVIEW02 / "review-record.json": "1ab859e904c02e1b9a8406be2f8497b78664167bdb73825c41240b2e4671fd36",
        REVIEW02 / "terminal-hashes.json": "176b69a5825789a6da2c152a995e6c2df5b7d197e9e3722de68282f119820b38",
    }
    for path, expected in predecessor_pins.items():
        require(path.is_file(), f"missing predecessor evidence: {path.relative_to(ROOT)}")
        require(digest(path) == expected, f"predecessor evidence changed: {path.relative_to(ROOT)}")

    print(
        "attempt03 source-search packet verified: "
        f"{checked} packet artifact hashes; attempt02 and independent-review files unchanged; "
        "4 exact-part axes remain NOT_RUN_SOURCE_GAP"
    )


if __name__ == "__main__":
    main()
