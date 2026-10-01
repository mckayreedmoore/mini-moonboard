"""Rehash the final attempt10 A12-forward input proposal and audit evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
OUT = HERE / "input-evidence-pins.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> None:
    case_dir = HERE / "a12-forward"
    source_revalidation = HERE / "source-revalidation"
    source_files = [
        BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py",
        BASE / "current-springa-case-bound-parent-input-audit-attempt01/check.py",
        BASE / "current-springa-parent-input-audit-attempt01/check.py",
        HERE / "project_a12_forward37.py",
        HERE / "README.md",
        HERE / "pin_input_evidence.py",
        case_dir / "audit_case_context.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/produce.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/diagnosis.json",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/source-pins.json",
        source_revalidation / "diagnosis.json",
        source_revalidation / "source-pins.json",
        HERE / "source-revalidation-audit.json",
        HERE / "screen.json",
        HERE / "screen-source-pins.json",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/model.json",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/model.inp",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/model.dat",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/execution.json",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/freeze.json",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/authorization.json",
        BASE / "current-springa-frame-a12-forward-all-bearing-attempt01/parent-serialized-input-audit.json",
        BASE / "current-six-case-source-load-register-attempt01/register.json",
        BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-forward/model.json",
        BASE / "current-floor-stick-constraint-audit-attempt01/audit.json",
        BASE / "current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz",
    ]
    output_files = [
        case_dir / "model.inp",
        case_dir / "model.json",
        case_dir / "audit.json",
        case_dir / "case-bound-input-context.json",
        case_dir / "case-bound-input-context-contract.json",
        case_dir / "source-pins.json",
        case_dir / "parent-serialized-input-audit.json",
        case_dir / "parent-case-context-check.json",
    ]
    for path in source_files + output_files:
        assert path.is_file(), path

    screen = read(HERE / "screen.json")
    replay = read(HERE / "source-revalidation-audit.json")
    model = read(case_dir / "model.json")
    adapter_audit = read(case_dir / "audit.json")
    serialized_audit = read(case_dir / "parent-serialized-input-audit.json")
    context_audit = read(case_dir / "parent-case-context-check.json")
    context = read(case_dir / "case-bound-input-context.json")
    adapter_pins = read(case_dir / "source-pins.json")

    assert replay["status"] == "PASS_A12_FORWARD_DIAGNOSTIC_SOURCE_REPLAY"
    assert screen["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
    assert screen["case_id"] == "a12-forward"
    assert len(screen["diagnostic_positive_cells_at_final_time"]) == 37
    assert len(screen["diagnostic_separating_cells_at_final_time"]) == 63
    assert model["case_id"] == context["case_id"] == "a12-forward"
    assert len(model["floor_reference_nodes_and_load_map"]) == 74
    assert adapter_audit["native_solve_executed"] is False
    assert adapter_audit["source_response_forces_read"] is False
    assert serialized_audit["status"] == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
    assert serialized_audit["proposed_branch_accepted"] is False
    assert serialized_audit["native_run_authorized"] is False
    assert context_audit["status"] == "PASS_A12_FORWARD_CASE_CONTEXT_BINDING"
    assert context_audit["input_only_no_freeze_or_native_run"] is True
    assert adapter_pins["adapter_script_sha256"] == sha(BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py")
    assert adapter_pins["output_model_sha256"] == sha(case_dir / "model.json")
    assert adapter_pins["output_deck_sha256"] == sha(case_dir / "model.inp")
    assert not (case_dir / "freeze.json").exists()
    assert not (case_dir / "execution.json").exists()
    assert not (case_dir / "model.dat").exists()

    source_hashes = {rel(path): sha(path) for path in source_files}
    for path, expected in screen["source_sha256"].items():
        assert sha(ROOT / path) == expected, path
        source_hashes[path] = expected
    output_hashes = {rel(path): sha(path) for path in output_files}
    result = {
        "schema": "current_springa_a12_forward_attempt10_input_evidence_pins/v1",
        "status": "PASS_A12_FORWARD_ATTEMPT10_INPUT_AND_AUDIT_PINS",
        "case_id": "a12-forward",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "adapter_script_path": rel(BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"),
        "adapter_script_sha256": sha(BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"),
        "source_sha256": dict(sorted(source_hashes.items())),
        "output_sha256": dict(sorted(output_hashes.items())),
        "diagnostic_source_revalidated": True,
        "support_proposal": {"positive_cells": 37, "separated_cells": 63, "active_tangent_rows": 74},
        "parent_serialized_deck_audit_status": serialized_audit["status"],
        "independent_context_audit_status": context_audit["status"],
        "native_solve_executed": False,
        "freeze_created": False,
        "mechanical_acceptance": False,
        "corner_demands_usable": False,
        "physical_force_adoption": False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "case_id": result["case_id"],
        "source_pins": len(source_hashes),
        "output_pins": len(output_hashes),
        "selected_cells": 37,
        "active_tangent_rows": 74,
        "serialized_input_audit": serialized_audit["status"],
        "context_audit": context_audit["status"],
        "adapter02_sha256": result["adapter_script_sha256"],
        "model_sha256": output_hashes[rel(case_dir / "model.json")],
        "deck_sha256": output_hashes[rel(case_dir / "model.inp")],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
