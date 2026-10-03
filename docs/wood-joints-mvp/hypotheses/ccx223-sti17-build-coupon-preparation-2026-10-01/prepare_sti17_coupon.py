#!/usr/bin/env python3
"""Parent-only creation of a separate STI17 free-C3D20 coupon freeze.

This script generates inputs and an embedded solver profile only. It does not
launch CalculiX or write to the native run ledger. It has not been executed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFLIGHT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01"
)
OLD_PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
MANUAL = ROOT / "fea/generated/ccx_2.23.pdf"
PARENT_VALIDATION = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json"
)
COUPON_DIR = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01"
)
DECK = COUPON_DIR / "coupon-free-c3d20-matrixstorage.inp"
ORACLE = COUPON_DIR / "matrix_export_oracle.py"
BUILD_RECEIPT = HERE / "sti17-build-receipt.json"
IMAGE_RECEIPT = HERE / "sti17-image-receipt.json"
PARENT_READINESS = HERE / "parent-coupon-readiness.json"
PROFILE_PATH = HERE / "solver-profile-sti17.json"
FREEZE_DIR = HERE / "sti17-free-c3d20-coupon-freeze-attempt01"
EXPECTED_BASE_ID = (
    "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
)
EXPECTED_NEW_TAG = "mini-moonboard-fea:ccx-upstream-2.23-sti17-v1"
EXPECTED_BINARY_PATH = "/usr/local/bin/ccx-upstream-2.23-sti17"
EXPECTED_SOURCE_PINS_SHA256 = (
    "1cc174760cb658614431a75532fcd0603342b6e1559ebc0df935be6310e65981"
)
EXPECTED_PARENT_VALIDATION_SHA256 = (
    "5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2"
)
EXPECTED_DECK_SHA256 = (
    "e128a62f899c90965fd68be09a7362ed836a30ff6b1c3f1c6dc0581e118b79fe"
)
EXPECTED_ORACLE_SHA256 = (
    "17a908d1283f676df7af97511ef2ecd3c794b98c6b81dc50e2a6f14cec57b79a"
)
FREEZE_SCOPE = "free unit C3D20 native MATRIXSTORAGE known-answer export only"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write_json_exclusive(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_coupon_readiness(
    readiness: dict,
    *,
    build_receipt_sha256: str,
    image_id: str,
    image_receipt_sha256: str,
    now: float | None = None,
) -> dict:
    require(
        readiness.get("schema") == "ccx223_sti17_coupon_readiness/v1"
        and readiness.get("status") == "READY_FOR_STI17_COUPON_FREEZE",
        "parent has not marked the isolated coupon freeze ready",
    )
    require(
        readiness.get("build_receipt_sha256") == build_receipt_sha256
        and readiness.get("image_id") == image_id,
        "parent coupon readiness does not bind this exact build and image",
    )
    require(
        readiness.get("image_receipt_sha256") == image_receipt_sha256,
        "parent coupon readiness does not bind the terminal image receipt",
    )
    require(
        readiness.get("scope") == "free-c3d20-sti17-output-precision-coupon-only"
        and readiness.get("candidate_export_authorized") is False
        and readiness.get("native_run_authorized") is False,
        "parent readiness widened the coupon scope",
    )
    require(
        readiness.get("max_cpu") == 1
        and readiness.get("memory_bytes") == 2 * 1024**3
        and readiness.get("wall_seconds") == 60
        and readiness.get("max_native_runs") == 1,
        "parent coupon readiness does not preserve the single 60-second run limit",
    )
    created = readiness.get("created_unix")
    reference_time = time.time() if now is None else now
    require(
        isinstance(created, (int, float)) and 0 <= reference_time - created <= 1800,
        "parent coupon readiness is absent, future-dated, or older than 30 minutes",
    )
    return readiness


def make_model_record(deck_sha256: str) -> dict:
    return {
        "schema": "wood_joint_reduced_native_model/v1",
        "scope": FREEZE_SCOPE,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "synthetic_only": True,
        "coupon_deck_sha256": deck_sha256,
        "material": {"E_N_per_mm2": 1.0, "nu": 0.25, "density_consistent_units": 1.0},
        "expected_equations": 60,
        "expected_rigid_modes": 6,
        "expected_shear_energy_N_mm": 2.0e-5,
        "expected_translation_mass": 1.0,
        "candidate_export_authorized": False,
        "mechanical_acceptance": False,
    }


def make_coupon_freeze_packet(
    profile: dict,
    source_hashes: dict[str, str],
    *,
    deck_sha256: str,
    model_sha256: str,
) -> dict:
    return {
        "schema": "wood_joint_reduced_native_freeze/v1",
        "scope": FREEZE_SCOPE,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "solver_profile": profile,
        "source_sha256": source_hashes,
        "files_sha256": {"model.inp": deck_sha256, "model.json": model_sha256},
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "candidate_export_authorized": False,
    }


def main() -> None:
    require(
        sha_file(PREFLIGHT / "source-pins.json") == EXPECTED_SOURCE_PINS_SHA256,
        "precision preflight source pins changed",
    )
    require(
        sha_file(PREFLIGHT / "precision-only.patch")
        == "71e56dc8854d7a89044cd36e961c79d809a12b21882524231bd2a26b6f4f7cd7",
        "precision-only patch changed",
    )
    require(
        sha_file(PARENT_VALIDATION) == EXPECTED_PARENT_VALIDATION_SHA256,
        "cited source-only parent validation changed; review current parent evidence",
    )
    require(sha_file(DECK) == EXPECTED_DECK_SHA256, "retained free C3D20 deck changed")
    require(
        sha_file(ORACLE) == EXPECTED_ORACLE_SHA256, "retained matrix oracle changed"
    )
    require(
        sha_file(OLD_PROFILE)
        == "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c",
        "shared 2.23 solver profile changed",
    )
    manual_profile = json.loads(OLD_PROFILE.read_text())["manual"]
    require(
        sha_file(MANUAL) == manual_profile["sha256"],
        "pinned 2.23 manual changed",
    )
    require(
        BUILD_RECEIPT.is_file()
        and IMAGE_RECEIPT.is_file()
        and PARENT_READINESS.is_file(),
        "terminal build/image receipts and fresh parent coupon readiness are required",
    )
    require(
        not PROFILE_PATH.exists(),
        "STI17 profile path already exists; do not overwrite it",
    )
    require(
        not FREEZE_DIR.exists(), "coupon freeze path already exists; do not reuse it"
    )

    build = json.loads(BUILD_RECEIPT.read_text())
    image = json.loads(IMAGE_RECEIPT.read_text())
    readiness = json.loads(PARENT_READINESS.read_text())
    require(
        build.get("schema") == "ccx223_sti17_build_receipt/v1"
        and build.get("status") == "PASS_BUILD_ONLY",
        "isolated build receipt is not a successful build-only receipt",
    )
    require(
        build.get("base_image_id") == EXPECTED_BASE_ID
        and build.get("new_image_tag") == EXPECTED_NEW_TAG,
        "build receipt names another image lineage",
    )
    require(
        build.get("new_binary_path") == EXPECTED_BINARY_PATH
        and re.fullmatch(r"[0-9a-f]{64}", build.get("new_binary_sha256", "")),
        "build receipt lacks the separate STI17 binary identity",
    )
    require(
        build.get("candidate_matrix_exported") is False
        and build.get("native_solver_run") is False
        and build.get("mechanical_acceptance") is False,
        "build receipt crossed its build-only scope",
    )
    require(
        build.get("changed_objects") == ["matrixstorage.o"],
        "build receipt does not isolate the one changed object",
    )
    require(
        build.get("source_diff")
        and "20.13e" in build["source_diff"]
        and "20.16e" in build["source_diff"],
        "build receipt does not retain the exact one-token source diff",
    )
    require(
        build.get("resource_limits", {}).get("outer_wall_seconds") == 60
        and build.get("resource_limits", {}).get("memory.max_bytes") == 2 * 1024**3,
        "build receipt did not enforce the bounded build",
    )
    build_sha = sha_file(BUILD_RECEIPT)

    require(
        image.get("schema") == "ccx223_sti17_image_receipt/v1"
        and image.get("status") == "PASS_STI17_IMAGE",
        "separate image receipt is not terminal and successful",
    )
    require(
        image.get("base_image_id") == EXPECTED_BASE_ID
        and image.get("image_tag") == EXPECTED_NEW_TAG,
        "image receipt has another base or tag",
    )
    require(
        image.get("build_receipt_sha256") == build_sha,
        "image receipt is not bound to the terminal build receipt",
    )
    require(
        image.get("binary_path") == EXPECTED_BINARY_PATH
        and image.get("binary_sha256") == build["new_binary_sha256"],
        "image receipt does not match the built binary",
    )
    image_id = image.get("image_id", "")
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is not None,
        "image receipt lacks the immutable committed image ID",
    )

    validate_coupon_readiness(
        readiness,
        build_receipt_sha256=build_sha,
        image_id=image_id,
        image_receipt_sha256=sha_file(IMAGE_RECEIPT),
    )

    profile = {
        "schema": "calculix_development_toolchain/v1",
        "version": "2.23-sti17",
        "image_tag": EXPECTED_NEW_TAG,
        "image_id": image_id,
        "binary_path": EXPECTED_BINARY_PATH,
        "binary_sha256": build["new_binary_sha256"],
        "scope": "One free C3D20 matrix-output precision method coupon; no candidate joint or frame result",
        "method_patch": {
            "source_member": "CalculiX/ccx_2.23/src/matrixstorage.c",
            "source_line": 304,
            "format_change": "%20.13e to %20.16e for .sti stiffness values",
            "mass_writer": "line 543 retained at %20.13e for .mas mass values",
            "patch_sha256": "71e56dc8854d7a89044cd36e961c79d809a12b21882524231bd2a26b6f4f7cd7",
        },
        "build_receipt_sha256": build_sha,
        "manual": manual_profile,
        "balanced_force_fixture_pass": False,
        "candidate_joint_contact_validated": False,
        "candidate_export_authorized": False,
        "mechanical_acceptance": False,
    }

    profile_bytes = (json.dumps(profile, indent=2, allow_nan=False) + "\n").encode()
    with PROFILE_PATH.open("xb") as stream:
        stream.write(profile_bytes)
    FREEZE_DIR.mkdir(parents=False, exist_ok=False)
    shutil.copyfile(DECK, FREEZE_DIR / "model.inp")
    model = make_model_record(EXPECTED_DECK_SHA256)
    model_path = FREEZE_DIR / "model.json"
    model_path.write_text(json.dumps(model, indent=2, allow_nan=False) + "\n")

    source_paths = [
        "fea/wood_joint_reduced_native.py",
        str(PROFILE_PATH.relative_to(ROOT)),
        str(Path(__file__).resolve().relative_to(ROOT)),
        str((HERE / "check_sti17_coupon.py").relative_to(ROOT)),
        str((HERE / "launch_sti17_coupon.py").relative_to(ROOT)),
        "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/README.md",
        "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/source-pins.json",
        "docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/precision-only.patch",
        str(DECK.relative_to(ROOT)),
        str(ORACLE.relative_to(ROOT)),
        str(PARENT_VALIDATION.relative_to(ROOT)),
        str(BUILD_RECEIPT.relative_to(ROOT)),
        str(IMAGE_RECEIPT.relative_to(ROOT)),
        str(PARENT_READINESS.relative_to(ROOT)),
    ]
    source_hashes = {}
    for name in sorted(set(source_paths)):
        source = ROOT / name
        require(source.is_file(), f"freeze source is absent: {name}")
        content = source.read_bytes()
        snapshot = FREEZE_DIR / "sources" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(content)
        source_hashes[name] = sha_bytes(content)

    packet = make_coupon_freeze_packet(
        profile,
        source_hashes,
        deck_sha256=sha_file(FREEZE_DIR / "model.inp"),
        model_sha256=sha_file(model_path),
    )
    write_json_exclusive(FREEZE_DIR / "freeze.json", packet)
    from fea.wood_joint_reduced_native import verify

    verify(FREEZE_DIR)

    preparation = {
        "schema": "ccx223_sti17_coupon_input_preparation/v1",
        "status": "FROZEN_NOT_EXECUTED",
        "freeze_path": str(FREEZE_DIR.relative_to(ROOT)),
        "freeze_sha256": sha_file(FREEZE_DIR / "freeze.json"),
        "profile_path": str(PROFILE_PATH.relative_to(ROOT)),
        "profile_sha256": sha_file(PROFILE_PATH),
        "build_receipt_sha256": build_sha,
        "image_receipt_sha256": sha_file(IMAGE_RECEIPT),
        "parent_readiness_sha256": sha_file(PARENT_READINESS),
        "deck_sha256": sha_file(FREEZE_DIR / "model.inp"),
        "oracle_sha256": sha_file(ORACLE),
        "native_run_executed": False,
        "ledger_reserved": False,
        "candidate_matrix_exported": False,
        "mechanical_acceptance": False,
    }
    write_json_exclusive(FREEZE_DIR / "preparation.json", preparation)
    print(json.dumps(preparation, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
