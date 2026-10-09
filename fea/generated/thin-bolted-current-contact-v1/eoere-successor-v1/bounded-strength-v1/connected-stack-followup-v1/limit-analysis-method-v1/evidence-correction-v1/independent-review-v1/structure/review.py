"""Bounded independent source/architecture review; never run LP, CAD or FEA."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
CORRECTION = DOC / "evidence-correction-v1"
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
ATTEMPT = RAW / "evidence-correction-v1/attempt01"
HERE = Path(__file__).resolve().parent
FREEZE_SHA256 = "ace9ab9d51c7f6320fb87be5f88329299f38b4bde5e7f1a9f2f0d77e98d2d371"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected["sha256"], f"Changed hash: {path}")
    if "bytes" in expected:
        require(len(data) == expected["bytes"], f"Changed byte count: {path}")
    return data


def tree_snapshot(path):
    manifest = {}
    total_bytes = 0
    for item in sorted(path.rglob("*")):
        relative = str(item.relative_to(ROOT))
        if item.is_symlink():
            manifest[relative] = {"symlink": str(item.readlink())}
        elif item.is_file():
            data = item.read_bytes()
            manifest[relative] = {"bytes": len(data), "sha256": digest(data)}
            total_bytes += len(data)
    return {"manifest_sha256": digest(encoded(manifest)), "entry_count": len(manifest), "file_bytes": total_bytes}


def main():
    output = HERE / "receipt.json"
    require(not output.exists(), "Use a new receipt; issued review is preserved")
    freeze_path = ATTEMPT / "frozen-packet.json"
    freeze_bytes = freeze_path.read_bytes()
    require(digest(freeze_bytes) == FREEZE_SHA256, "Unrecognized correction freeze")
    targets = json.loads(freeze_bytes)
    metadata = json.loads((CORRECTION / "inputs.json").read_bytes())
    targets.update(metadata["frozen_files"])
    require(len(targets) == 11, "Exactly eleven target files required")
    before_targets = {path: digest(checked(ROOT / path, pin)) for path, pin in targets.items()}
    compact = json.loads((CORRECTION / "verification.json").read_bytes())
    sources = compact["source_sha256"]
    require(len(sources) == 17, "Expected seventeen source pins")
    for path, sha in sources.items():
        checked(ROOT / path, {"sha256": sha})
    for pin in compact["raw_evidence"]:
        checked(ROOT / pin["path"], pin)
    original_verification = json.loads((DOC / "verification.json").read_bytes())
    for pin in original_verification["run_files"].values():
        checked(ROOT / pin["path"], pin)
    before_issued = tree_snapshot(ATTEMPT)
    spec = importlib.util.spec_from_file_location("independent_structure_correction", CORRECTION / "correction.py")
    correction = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(correction)
    state = correction.snapshot()
    require(state["pins"] == sources, "Runtime closure differs from issued closure")
    writes = []
    unwritten = HERE / "unwritten-verification.json"

    def capture_write(path, data):
        require(Path(path) == unwritten, "Unexpected verifier write")
        writes.append(data)

    correction.new_file = capture_write
    receipt = correction.verify(ATTEMPT / "fresh-run", ATTEMPT / "fresh-replay", unwritten)
    require(len(writes) == 1, "Expected one verification receipt")
    require(writes[0] == (ATTEMPT / "clean-verification.json").read_bytes(), "Verification no longer reproduces issued bytes")
    require(not unwritten.exists(), "Probe unexpectedly wrote a file")
    reg = json.loads((ATTEMPT / "regressions.json").read_bytes())
    require(len(reg["commands"]) == 36, "Changed bounded command census")
    require([row["returncode"] for row in reg["commands"]] == [0] * 3 + [1] * 33, "Unexpected issued command statuses")
    pair = {}
    for name in ("result.json", "details.json", "run-provenance.json"):
        first = (ATTEMPT / "fresh-run" / name).read_bytes()
        second = (ATTEMPT / "fresh-replay" / name).read_bytes()
        require(first == second, f"Issued replay differs: {name}")
        pair[name] = digest(first)
    imports = {}
    for name in ("correction.py", "check.py"):
        tree = ast.parse((CORRECTION / name).read_bytes())
        imports[name] = sorted({node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
    after_targets = {path: digest(checked(ROOT / path, pin)) for path, pin in targets.items()}
    for path, sha in sources.items():
        checked(ROOT / path, {"sha256": sha})
    after_issued = tree_snapshot(ATTEMPT)
    require(before_targets == after_targets, "Review changed target files")
    require(before_issued == after_issued, "Review changed issued correction evidence")
    result = {
        "schema": "synthetic_limit_correction_independent_structure_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_IN_BOUNDED_SCOPE",
        "findings": [],
        "review_script_sha256": digest(Path(__file__).read_bytes()),
        "correction_freeze_sha256": FREEZE_SHA256,
        "target_files_sha256": before_targets,
        "source_sha256": sources,
        "source_count": len(sources),
        "target_files_unchanged_before_after": True,
        "source_closure_unchanged_before_after": True,
        "issued_tree_before": before_issued,
        "issued_tree_after": after_issued,
        "issued_raw_pins_authenticated": len(compact["raw_evidence"]),
        "original_issued_result_and_fields_authenticated": True,
        "issued_three_file_replay_sha256": pair,
        "verification_receipt_reproduced_in_memory": True,
        "independent_checks": receipt["independent_checks"],
        "validated_claims": receipt["validated_claims"],
        "issued_regression_commands": {"count": len(reg["commands"]), "successes": 3, "rejections": 33},
        "entrypoint_imports": imports,
        "architecture": [
            "Original six-file numerical packet remains immutable; correction executes captured authenticated analyzer and checker bytes.",
            "Correction owns source capture, compact evidence validation, output creation and provenance; regression checker owns isolated copied-source and corrupt-evidence controls.",
            "Pinned external helper, tests, lockfile, preceding results and original review receipts are explicit reproduction dependencies and presently remain available.",
            "Retained regression commands establish two separate fresh CLI productions; output equality alone does not establish execution independence.",
            "Raw fields and rejected controls remain ignored evidence. The compact supplement records their locations and hashes; no archive or prune is proposed.",
        ],
        "limits": [
            "Reviewed source ownership, coupling, frozen provenance, evidence flow, documented reproduction and retention boundaries.",
            "Consumed original review receipts only as opaque hash-bound source dependencies; did not inspect other reviewers' findings.",
            "Reused the corrected verifier and dimensional field integration; did not rerun synthetic LP optimization, independently reconstruct KKT matrices, run CAD/native mechanics, inspect current candidate fields or alter shared files.",
            "No candidate action, geometry, material, resistance, acceptance or physical-work conclusion follows from this synthetic method review.",
        ],
    }
    with output.open("xb") as stream:
        stream.write(encoded(result))
    print(json.dumps({"status": result["status"], "sources": len(sources), "target_files": len(targets)}, sort_keys=True))


if __name__ == "__main__":
    main()
