"""Independent structure/source review; no full analysis or CAD/native execution."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
SUPPLEMENT = DOC / "revised-base-audit-v1/reproduction-guard-v1"
EXPECTED = {
    "verification.json": "010fb293bc0b7dead3821e66f9923c0a7a942438e09545cec0dd36e7c8044ae5",
    "result.json": "b48c1ba300e161a729ffa9f9cbcabe75b44126488e376eea0154e7bf7b8d71a7",
    "run_fresh.py": "53fe84d33b19d184c79e07e3a007f29ca40c7b96d3eea9a80d487c0a48f53bb5",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def relative(path):
    return str(Path(path).relative_to(ROOT))


def load_stdlib_module(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def main():
    require((ROOT / ".git").is_dir(), "shared checkout expected")
    for filename, digest in EXPECTED.items():
        require(sha(SUPPLEMENT / filename) == digest, "frozen review target differs: " + filename)
    inputs = read(SUPPLEMENT / "inputs.json")
    supplement_verification = read(SUPPLEMENT / "verification.json")
    targets = {
        r["path"]: r["sha256"]
        for packet in inputs["packets"].values()
        for r in packet["issued_files"]
    }
    targets.update({path: item["sha256"] for path, item in supplement_verification["owned_artifacts"].items()})
    targets[relative(SUPPLEMENT / "verification.json")] = EXPECTED["verification.json"]
    require(len(targets) == 17, "ten original and seven supplement files required")
    for path, digest in targets.items():
        require(sha(ROOT / path) == digest, "target hash differs: " + path)
    before = {path: sha(ROOT / path) for path in targets}
    permanent_bytes = sum((ROOT / path).stat().st_size for path in targets)
    require(permanent_bytes == 255588, "frozen permanent volume differs")
    for path in targets:
        if path.endswith(".py"):
            ast.parse((ROOT / path).read_bytes(), filename=path)
        elif path.endswith(".json"):
            read(ROOT / path)

    guard = load_stdlib_module("run_fresh", SUPPLEMENT / "run_fresh.py")
    checker = load_stdlib_module("structure_bound_evidence_checker", SUPPLEMENT / "check_evidence.py")
    closures = {}
    for key, packet in inputs["packets"].items():
        authenticated = guard.authenticate(inputs, sha(SUPPLEMENT / "inputs.json"), key)
        require(authenticated["issued_pin_count"] == {"audit": 1120, "connected": 1126}[key], "issued pin count")
        detail = guard.read_pinned(packet["details"])
        result = read(ROOT / next(r["path"] for r in packet["issued_files"] if r["path"].endswith("/result.json")))
        require(result["source_pin_count"] == authenticated["issued_pin_count"], "result pin count")
        require(result["complete_source_canonical_sha256"] == authenticated["issued_closure_canonical_sha256"], "result closure digest")
        require("uv.lock" in detail["complete_source_sha256"] and "pyproject.toml" in detail["complete_source_sha256"], "locked environment not retained")
        require(result["fabrication_or_climbing_release"] is False, "release claim")
        verification_path = ROOT / next(r["path"] for r in packet["issued_files"] if r["path"].endswith("/verification.json"))
        verification = read(verification_path)
        for path, record in verification["owned_artifacts"].items():
            require(sha(ROOT / path) == record["sha256"], "original owned-artifact digest")
            require((ROOT / path).stat().st_size == record["bytes"], "original owned-artifact volume")
        require(sha(ROOT / verification["raw_details"]["path"]) == verification["raw_details"]["sha256"], "raw detail binding")
        raw_result = (ROOT / packet["details"]["path"]).parent / "result.json"
        require(raw_result.read_bytes() == (verification_path.parent / "result.json").read_bytes(), "published/raw result bytes differ")
        guard.verify(authenticated["pins"])
        closures[key] = {
            "issued_pin_count": authenticated["issued_pin_count"],
            "issued_closure_canonical_sha256": authenticated["issued_closure_canonical_sha256"],
            "guarded_pin_count": authenticated["guarded_pin_count"],
            "external_archive_manifest_paths": [p for p in detail["complete_source_sha256"] if Path(p).is_absolute()],
            "all_sources_verified_before_after": True,
        }
    reproduced = checker.run(inputs, sha(SUPPLEMENT / "inputs.json"))
    saved = read(SUPPLEMENT / "result.json")
    require(reproduced == saved["evidence_supplement"], "read-only arithmetic/provenance supplement differs")
    require(reproduced["supplement_pin_count"] == 1147, "extended pin count")
    require(len(reproduced["negative_controls_rejected"]) == 4, "corruption control evidence")
    require(saved["guard_controls"]["control_count"] == 14, "sealed guard control count")
    for record in supplement_verification["raw_receipts"]:
        raw = ROOT / record["path"]
        require(sha(raw) == record["sha256"] and raw.stat().st_size == record["bytes"], "supplement raw receipt differs")
        raw_value = read(raw)
        key = "guard_controls" if raw.name == "guard-controls.json" else "evidence_supplement"
        require(raw_value == saved[key], "compact/raw supplement receipt differs")
    connected = read(DOC / "connected-stack-followup-v1/result.json")
    audit = read(DOC / "revised-base-audit-v1/result.json")
    require(len(connected["stacks"]) == 8 and all(r["adjusted_complete_joint_resistance_n"] is None for r in connected["stacks"]), "complete stack resistances must remain null")
    require(connected["source_geometry_revision"] == "eoere-bottom-rail-tnut-clearance-v1", "old-action geometry boundary")
    require(connected["target_geometry_revision_not_evaluated"] == "eoere-midpoint-ready-frame-v3", "target geometry boundary")
    require(audit["geometry_delta"]["current_response_exists_in_this_packet"] is False, "new response claim")
    require(audit["group_applicability"]["unsupported_shaft_count"] == 8, "audit stack boundary")
    require(audit["washer_support"]["fresh_changed_host_probes"] == 36 and audit["washer_support"]["unchanged_seat_proofs_reused"] == 76, "proof ownership census")
    for row in audit["candidate_member_restraint_paths"]:
        require(row["Cp_adopted"] is False and row["effective_length_adopted"] is False, "restraint adoption claim")
    ledger = ROOT / "docs/wood-joints-mvp/completion-ledger.md"
    ledger_text = ledger.read_text()
    require("revised-base-audit-v1/reproduction-guard-v1/README.md" in ledger_text, "supported future entrypoint absent from maintained ledger")
    require("Future reproduction of either packet uses" in ledger_text, "future reproduction precedence missing")
    after = {path: sha(ROOT / path) for path in targets}
    require(before == after, "immutable target changed during review")
    receipt = {
        "schema": "independent_followup_structure_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_FINDINGS",
        "review_scope": "Ownership, helper reuse, source/provenance closure, fresh-output policy, immutability, permanent volume, recoverability and reading boundaries for two original five-file packets plus seven-file guard supplement.",
        "findings": [],
        "frozen_target_files_sha256": before,
        "target_file_count": len(targets),
        "permanent_bytes": permanent_bytes,
        "original_closures": closures,
        "evidence_supplement_exact_saved_result_reproduced_in_memory": True,
        "supplement_pin_count": reproduced["supplement_pin_count"],
        "supplement_closure_canonical_sha256": reproduced["supplement_closure_canonical_sha256"],
        "reused_sealed_guard_control_count": 14,
        "reproduced_corrupted_evidence_control_count": 4,
        "maintained_ledger_future_entrypoint_present": True,
        "historical_source_command_output_binding_verified": True,
        "historical_command_executed": False,
        "genuine_CAD_native_global_browser_or_full_analysis_execution": False,
        "target_files_unchanged": True,
        "staging_or_commit_performed": False,
        "raw_retention": "Original attempts, detailed source maps, recovered checker and v3 proof remain present and active. No archive/prune or removal; archive-candidate statements remain conditional on consumer/ownership checks.",
        "reading_limits": "Audit is preceding base v3/extra-grid OFF, old actions remain original raised-rail fields, current cleat response remains outside the packet, all eight complete stack capacities remain null, panel remedies stay paused.",
        "physical_qualification_claimed": False,
        "review_script_sha256": sha(__file__),
        "command": "python3 -B " + relative(Path(__file__)),
    }
    output = Path(__file__).parent / "receipt.json"
    with output.open("xb") as stream:
        stream.write((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "target_files": len(targets), "permanent_bytes": permanent_bytes, "receipt": relative(output), "receipt_sha256": sha(output)}))


if __name__ == "__main__":
    main()
