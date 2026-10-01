"""Parent-invoked exact-byte freeze preparation; never launches a solver."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
INPUT_PACKET = SERIES / "current-springa-k12-rear-spr489-direct-master-input-attempt02"
METHOD_PACKET = SERIES / "current-k12-rear-spr489-direct-response-audit-attempt02"
BASELINE_PACKET = SERIES / "current-springa-selected-floor-k12-rear-attempt03"
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
SOURCE_CLOSURE = HERE / "source-closure.json"
SOURCE_PINS = HERE / "source-pins.json"
PARENT_METHOD_REVIEW = SERIES / "current-k12-rear-direct-parent-method-review-attempt01/review.json"
RUN_ID = "k12-rear-spr489-direct-attempt01"


class FreezePreparationError(ValueError):
    """Raised when exact attempt02 inputs or source closure do not match pins."""


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def import_core():
    path = METHOD_PACKET / "response_core.py"
    name = "attempt02_k12_rear_spr489_response_core_for_freeze"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise FreezePreparationError("Cannot import the pinned attempt02 response core")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _load_source_entries() -> dict[str, str]:
    pins = json.loads(SOURCE_PINS.read_text())
    if pins.get("parent_native_readiness") is not False:
        raise FreezePreparationError("Readiness packet must remain parent_native_readiness=false")
    if pins.get("native_solve_executed") is not False or pins.get("freeze_created_by_this_packet") is not False:
        raise FreezePreparationError("Readiness packet cannot claim a freeze or native solve")
    if pins.get("source_closure_sha256") != sha(SOURCE_CLOSURE):
        raise FreezePreparationError("Source closure manifest differs from its readiness pin")
    if pins.get("parent_method_review_sha256") != sha(PARENT_METHOD_REVIEW):
        raise FreezePreparationError("Parent method review differs from its readiness pin")

    manifest = json.loads(SOURCE_CLOSURE.read_text())
    if manifest.get("schema") != "current_k12_rear_spr489_direct_run_source_closure/v1":
        raise FreezePreparationError("Unsupported source closure schema")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise FreezePreparationError("Source closure manifest has no pinned files")
    sources: dict[str, str] = {}
    for entry in entries:
        relative = str(entry.get("path", ""))
        expected = str(entry.get("sha256", ""))
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise FreezePreparationError(f"Unsafe source path in closure manifest: {relative!r}")
        path = ROOT / relative
        if not path.is_file() or sha(path) != expected:
            raise FreezePreparationError(f"Pinned source changed or is missing: {relative}")
        if relative in sources and sources[relative] != expected:
            raise FreezePreparationError(f"Conflicting source pins for {relative}")
        sources[relative] = expected

    own_path = Path(__file__).resolve()
    own_relative = str(own_path.relative_to(ROOT))
    if sources.get(own_relative) != sha(own_path):
        raise FreezePreparationError("Exact-freeze preparation script is not pinned by its source closure")
    manifest_relative = str(SOURCE_CLOSURE.resolve().relative_to(ROOT))
    sources[manifest_relative] = sha(SOURCE_CLOSURE)
    pins_relative = str(SOURCE_PINS.resolve().relative_to(ROOT))
    sources[pins_relative] = sha(SOURCE_PINS)
    review_relative = str(PARENT_METHOD_REVIEW.resolve().relative_to(ROOT))
    sources[review_relative] = sha(PARENT_METHOD_REVIEW)
    return sources


def _validate_review_and_input() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    review = json.loads(PARENT_METHOD_REVIEW.read_text())
    if (review.get("status") != "PASS_PARENT_EXACT_INPUT_AND_UNCHANGED_PHYSICAL_GATES_REVIEW"
            or review.get("native_solve_executed") is not False
            or review.get("mechanical_acceptance") is not False):
        raise FreezePreparationError("Pinned parent method review is absent or does not pass its bounded scope")
    for relative, key in (
        (str(METHOD_PACKET / "response_core.py"), "response_core_sha256"),
        (str(METHOD_PACKET / "validate_direct_master_input.py"), "validate_direct_master_input.py"),
    ):
        expected = review.get("source_sha256", {}).get(str((ROOT / relative).resolve()))
        actual = sha(ROOT / relative)
        if expected != actual:
            raise FreezePreparationError(f"Parent review does not bind the current method source {relative}")

    core = import_core()
    validator = core.load_direct_master_input_validator()
    validated = validator.validate_input_contract(
        INPUT_PACKET / "model.json", INPUT_PACKET / "model.inp",
    )
    if validated.proof_summary.get("status") != "PASS_EXACT_K12_REAR_SPR489_DIRECT_MASTER_INPUT_CONTRACT":
        raise FreezePreparationError("Attempt02 direct-master input contract did not pass")
    if sha(INPUT_PACKET / "model.json") != validator.VARIANT_MODEL_SHA256:
        raise FreezePreparationError("Attempt02 model changed during validation")
    if sha(INPUT_PACKET / "model.inp") != validator.VARIANT_DECK_SHA256:
        raise FreezePreparationError("Attempt02 deck changed during validation")
    return core, validator, validated.proof_summary


def prepare(target_directory: Path) -> dict[str, Any]:
    target = Path(target_directory).resolve()
    if target.exists():
        raise FreezePreparationError(f"Target already exists; no overwrite or reuse: {target}")
    if target == INPUT_PACKET.resolve() or target == METHOD_PACKET.resolve() or target == HERE.resolve():
        raise FreezePreparationError("Refusing to overwrite a frozen source or readiness packet")

    sources = _load_source_entries()
    _, validator, proof = _validate_review_and_input()
    profile = json.loads(PROFILE.read_text())
    if sha(ROOT / profile["manual"]["local_path"]) != profile["manual"]["sha256"]:
        raise FreezePreparationError("Pinned CalculiX 2.23 manual hash changed")

    # Recheck every external source immediately before writing the exact-byte copy.
    for relative, expected in sources.items():
        if sha(ROOT / relative) != expected:
            raise FreezePreparationError(f"Source changed during freeze preparation: {relative}")
    source_model = INPUT_PACKET / "model.json"
    source_deck = INPUT_PACKET / "model.inp"
    source_model_sha, source_deck_sha = sha(source_model), sha(source_deck)
    if (source_model_sha != validator.VARIANT_MODEL_SHA256
            or source_deck_sha != validator.VARIANT_DECK_SHA256):
        raise FreezePreparationError("The exact attempt02 model/deck pair no longer matches its pin")

    target.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source_model, target / "model.json")
    shutil.copyfile(source_deck, target / "model.inp")
    if sha(target / "model.json") != source_model_sha or sha(target / "model.inp") != source_deck_sha:
        raise FreezePreparationError("Frozen model/deck copy is not byte-identical to attempt02")

    for relative, expected in sorted(sources.items()):
        source = ROOT / relative
        snapshot = target / "sources" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, snapshot)
        if sha(snapshot) != expected:
            raise FreezePreparationError(f"Frozen source snapshot does not match pin: {relative}")

    scope = (
        "One bounded K12-rear SPR489 direct-master response test using the exact attempt02 model/deck; "
        "preserve the 23/77 diagnostic support mask; no acceptance or automatic mask iteration."
    )
    manifest_sha = sha(SOURCE_CLOSURE)
    pins_sha = sha(SOURCE_PINS)
    freeze_record = {
        "schema": "wood_joint_reduced_native_freeze/v1",
        "scope": scope,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "case_id": "k12-rear",
        "solver_profile": profile,
        "source_sha256": sources,
        "files_sha256": {
            "model.json": sha(target / "model.json"),
            "model.inp": sha(target / "model.inp"),
        },
        "readiness_packet": str(HERE.relative_to(ROOT)),
        "readiness_source_closure_sha256": manifest_sha,
        "readiness_source_pins_sha256": pins_sha,
        "method_input_contract_status": proof["status"],
        "native_solve_executed": False,
        "mechanical_acceptance": False,
    }
    write_json(target / "freeze.json", freeze_record)

    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_reduced_native import verify

    verify(target)
    return {
        "status": "PASS_PARENT_EXACT_BYTE_FREEZE_PREPARED_INPUT_ONLY",
        "target_directory": str(target),
        "model_sha256": source_model_sha,
        "deck_sha256": source_deck_sha,
        "freeze_sha256": sha(target / "freeze.json"),
        "source_file_count": len(sources),
        "native_solve_executed": False,
        "parent_native_readiness": False,
        "mechanical_acceptance": False,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_directory", type=Path,
                        help="New parent-owned native packet directory; it must not exist")
    args = parser.parse_args()
    print(json.dumps(prepare(args.target_directory), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
