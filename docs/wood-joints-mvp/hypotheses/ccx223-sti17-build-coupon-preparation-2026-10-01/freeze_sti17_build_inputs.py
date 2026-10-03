#!/usr/bin/env python3
"""Parent-only hash freeze for the bounded STI17 build inputs.

Run only after parent readiness is recorded and before the isolated container
is created. This prepares hashes; it does not build or run CalculiX. It has
not been executed.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFLIGHT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01"
)
PARENT_VALIDATION = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json"
)
READINESS = HERE / "parent-build-readiness.json"
FREEZE_PATH = HERE / "build-input-freeze.json"
PARENT_VALIDATION_SHA256 = (
    "5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2"
)
SOURCE_PINS_SHA256 = "1cc174760cb658614431a75532fcd0603342b6e1559ebc0df935be6310e65981"
PATCH_SHA256 = "71e56dc8854d7a89044cd36e961c79d809a12b21882524231bd2a26b6f4f7cd7"
BASE_IMAGE_ID = (
    "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
)
NEW_IMAGE_TAG = "mini-moonboard-fea:ccx-upstream-2.23-sti17-v1"

INPUT_PATHS = [
    "AGENTS.md",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/README.md",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/pin-receipt.json",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/build_sti17.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/freeze_sti17_build_inputs.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/prepare_sti17_coupon.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py",
    "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/parent-build-readiness.json",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/README.md",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/source-pins.json",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/precision-only.patch",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/roundtrip.c",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/host-roundtrip-result.json",
    "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/patch-source-check-result.json",
    "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json",
    "fea/calculix_223/Makefile.upstream",
    "fea/calculix_223/Dockerfile",
    "fea/calculix_223/build.py",
    "fea/calculix_223/record_build.py",
    "fea/calculix_223/.dockerignore",
    "fea/calculix_223/solver-profile.json",
    "fea/calculix_223/README.md",
    "fea/generated/calculix-2.23-build-attempt02/build_manifest.json",
    "fea/generated/calculix-2.23-build-attempt02/build_result.json",
    "fea/wood_joint_reduced_native.py",
    "fea/generated/ccx_2.23.pdf",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/coupon-free-c3d20-matrixstorage.inp",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/matrix_export_oracle.py",
]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    require(
        not FREEZE_PATH.exists(),
        "build-input-freeze.json already exists; do not replace it",
    )
    require(
        sha_file(PARENT_VALIDATION) == PARENT_VALIDATION_SHA256,
        "cited parent validation changed",
    )
    require(
        sha_file(PREFLIGHT / "source-pins.json") == SOURCE_PINS_SHA256,
        "preflight source pins changed",
    )
    require(
        sha_file(PREFLIGHT / "precision-only.patch") == PATCH_SHA256,
        "precision-only patch changed",
    )

    readiness = json.loads(READINESS.read_text())
    require(
        readiness.get("schema") == "ccx223_sti17_parent_build_readiness/v1"
        and readiness.get("status") == "READY_STI17_BUILD",
        "fresh parent readiness for the isolated build is required",
    )
    require(
        readiness.get("parent_validation_sha256") == PARENT_VALIDATION_SHA256
        and readiness.get("source_pins_sha256") == SOURCE_PINS_SHA256,
        "parent readiness does not bind the cited validation and source pins",
    )
    require(
        readiness.get("base_image_id") == BASE_IMAGE_ID
        and readiness.get("new_image_tag") == NEW_IMAGE_TAG,
        "parent readiness names another image identity",
    )
    require(
        readiness.get("base_tag_resolves_to_id") is True
        and readiness.get("new_image_tag_unused") is True,
        "parent has not confirmed immutable base mapping and unused new tag",
    )
    require(
        readiness.get("candidate_export_authorized") is False
        and readiness.get("native_run_authorized") is False,
        "build readiness crosses the bounded build-only scope",
    )
    require(
        readiness.get("max_cpu") == 1
        and readiness.get("memory_bytes") == 2 * 1024**3
        and readiness.get("wall_seconds") == 60,
        "parent readiness does not match the build resource ceiling",
    )
    issued = readiness.get("created_unix")
    require(
        isinstance(issued, (int, float)) and 0 <= time.time() - issued <= 1800,
        "parent build readiness is absent, future-dated, or older than 30 minutes",
    )

    binding = readiness.get("review_binding")
    require(isinstance(binding, dict), "final source-review binding is required")
    target_record = binding.get("target", {})
    target_name = target_record.get("path")
    require(
        isinstance(target_name, str)
        and not Path(target_name).is_absolute()
        and ".." not in Path(target_name).parts,
        "source-review target path must be repository-relative",
    )
    target_path = ROOT / target_name
    require(
        sha_file(target_path) == target_record.get("sha256"),
        "final source-review target changed",
    )
    target = json.loads(target_path.read_text())
    reviews = binding.get("reviews", {})
    require(
        isinstance(reviews, dict)
        and set(reviews) == {"correctness", "testing", "architecture"},
        "three final independent source reviews are required",
    )
    input_paths = set(INPUT_PATHS)
    input_paths.add(target_name)
    input_paths.update(row["path"] for row in target["files"])
    input_paths.update(record["path"] for record in reviews.values())
    files = {}
    for relative in sorted(input_paths):
        path = ROOT / relative
        require(path.is_file(), f"required build input is absent: {relative}")
        files[relative] = sha_file(path)
    sys.path.insert(0, str(HERE))
    from build_sti17 import validate_review_binding

    validate_review_binding(ROOT, binding, files)
    require(
        files[
            "docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/parent-build-readiness.json"
        ]
        == sha_file(READINESS),
        "readiness changed while the build inputs were frozen",
    )

    packet = {
        "schema": "ccx223_sti17_build_input_freeze/v1",
        "status": "FROZEN_FOR_ONE_ISOLATED_BUILD",
        "scope": "copy pinned CalculiX 2.23 image source/object tree; rebuild matrixstorage.o only",
        "created_unix": time.time(),
        "base_image_id": BASE_IMAGE_ID,
        "new_image_tag": NEW_IMAGE_TAG,
        "parent_readiness_sha256": sha_file(READINESS),
        "parent_validation_sha256": PARENT_VALIDATION_SHA256,
        "source_pins_sha256": SOURCE_PINS_SHA256,
        "patch_sha256": PATCH_SHA256,
        "review_binding": binding,
        "resource_limits": {
            "cpu_count": 1,
            "memory_bytes": 2 * 1024**3,
            "wall_seconds": 60,
        },
        "files_sha256": files,
        "native_solver_run": False,
        "candidate_matrix_exported": False,
        "mechanical_acceptance": False,
    }
    with FREEZE_PATH.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(packet, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "status": packet["status"],
                "build_input_freeze_sha256": sha_file(FREEZE_PATH),
                "frozen_file_count": len(files),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
