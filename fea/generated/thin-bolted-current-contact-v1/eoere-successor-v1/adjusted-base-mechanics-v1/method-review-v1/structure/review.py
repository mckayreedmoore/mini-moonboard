"""Independent method ownership/provenance review; only source metadata runs."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
sys.path.insert(0, str(ROOT))
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
EXPECTED = {
    "extended-cleat-intake-v1/export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    "extended-cleat-intake-v1/test_extended_intake.py": "786cdfb9e8560716ab603d26179ce3a0b5635965d3238e234f669811768fe63a",
    "extended-cleat-intake-v1/verification.json": "e5b8451c7b6d23822b8909378f2df98e6132e16384900ac20b5c3522b5193544",
    "current-panel-bank-v1/panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
    "current-panel-bank-v1/test_panel_operators.py": "dd48189121a3aef78c60a5eb5677f789ac45a91c7fc42ebb7822442a0986c0c1",
    "current-panel-bank-v1/method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
    "parent-authority-v1/adjusted-base-manifest.json": "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2",
    "parent-authority-v1/extended-cleat-manifest.json": "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def forbidden(*args, **kwargs):
    raise AssertionError("review must not invoke actual extraction or real panel bank")


def main():
    before = {path: sha(RAW / path) for path in EXPECTED}
    require(before == EXPECTED, "immutable method review target changed")
    for path in EXPECTED:
        if path.endswith(".py"):
            ast.parse((RAW / path).read_bytes(), filename=path)
    x = load("structure_exact_extended_intake", RAW / "extended-cleat-intake-v1/export.py")
    m = load("structure_exact_current_panels", RAW / "current-panel-bank-v1/panel_operators.py")
    manifest = RAW / "parent-authority-v1/extended-cleat-manifest.json"
    manifest_sha = EXPECTED["parent-authority-v1/extended-cleat-manifest.json"]
    with patch.object(x.e, "export_native", forbidden), patch.object(m.raised, "prepare_panel_operators", forbidden), patch.object(m.raised.saved, "reuse_panel_operators", forbidden):
        prepared = x.prepare(manifest, manifest_sha)
        planned = x.source_plan(manifest, manifest_sha)
        plan, prior, current, moved, panel_pins = m.read_sources()
    p, old, report, panels, pins = prepared
    require(len(pins) == 1076 and len(panel_pins) == 840, "reviewed source closure counts differ")
    intake_receipt = json.loads((RAW / "extended-cleat-intake-v1/verification.json").read_bytes())
    panel_receipt = json.loads((RAW / "current-panel-bank-v1/method-receipt.json").read_bytes())
    require(x.a.canonical(pins) == intake_receipt["source_closure"]["canonical_sha256"], "intake closure differs")
    require(m.canonical(panel_pins) == panel_receipt["source_pin_union_canonical_sha256"], "panel closure differs")
    require(m.input_record(plan, current, moved) == panel_receipt["source_inputs"], "panel source contract differs from saved receipt")
    seam = {
        "exact_current_intake_method_sha256": EXPECTED["extended-cleat-intake-v1/export.py"],
        "exact_panel_method_sha256": EXPECTED["current-panel-bank-v1/panel_operators.py"],
        "exact_extended_parent_manifest_sha256": manifest_sha,
        "full_340_aperture_descriptors_equal": current["panel_machining"] == p["current_panel_machining_descriptors"],
        "ordered_66_screw_descriptors_equal": current["screw_axes"] == [r["source_screw_descriptor"] for r in p["hillman_rows"]],
        "six_finished_panel_source_bindings_equal": {r["id"]: m.source_binding(r) for r in panels} == {r["id"]: r for r in current["finished_panel_solids"]},
    }
    require(all(v is True for k, v in seam.items() if k.endswith("equal")), "current intake/panel metadata seam differs")
    original_prepare = x.e.prepare
    for entrypoint, dependency in ((x.source_plan, "source_plan"), (x.export_native, "export_native")):
        def failed(*args, **kwargs):
            raise RuntimeError("controlled metadata-only wrapper failure")
        with patch.object(x, "prepare", lambda *_: prepared), patch.object(x.e, dependency, failed), patch.object(x.e, "slot", lambda *_: {"record_at_start": {"approved_manifest_sha256": manifest_sha}}), patch.dict(os.environ, {"EOERE_PARENT_SERIALIZED_EXTRACTION": "1"}):
            try:
                entrypoint(manifest, manifest_sha, None, None) if dependency == "export_native" else entrypoint(manifest, manifest_sha)
            except RuntimeError:
                pass
            else:
                raise ValueError("controlled wrapper failure not observed")
        require(x.e.prepare is original_prepare, "scoped source override was not restored on exception")
    require(planned["candidate_K_q_forces_or_acceptance"] is None and planned["native_queries_deferred"], "source-only plan claims response readiness")
    require(not any(planned["release"].values()), "source-only release claim")
    for path in EXPECTED:
        require(sha(RAW / path) == before[path], "target changed during independent review")
    x.a.verify(pins)
    m.raised.verify(panel_pins)
    old_seam_sha = panel_receipt["intake_seam"]["method_sha256"]
    require(old_seam_sha != seam["exact_current_intake_method_sha256"], "recorded provenance mismatch no longer exists")
    finding = {
        "category": "architecture/provenance",
        "severity": "medium",
        "file": str((RAW / "current-panel-bank-v1/method-receipt.json").relative_to(ROOT)),
        "line": 47,
        "finding": "The panel method receipt binds its intake seam to exporter SHA 7b85a771... at extended-cleat-intake-v1/export.py, but that path is frozen at bdfa95b4.... The receipt does not label this as a historical producer or provide a recoverable source path for those former bytes.",
        "impact": "The recorded seam comparison cannot be authenticated against the frozen review target, so it cannot serve as exact-source evidence for the parent method-readiness gate. This is a provenance defect; the current source-only comparison itself passes.",
        "concrete_fix": "Preserve the issued receipt and add a compact exact-source correction/supplement recording bdfa95b4..., the exact manifest and the three full metadata comparisons. Retain/identify the former source if the earlier comparison remains claimed as recoverable history. This independent review receipt already supplies the current-source metadata comparison evidence, but the parent must bind it explicitly as the corrected active seam evidence.",
        "recorded_method_sha256": old_seam_sha,
        "observed_current_method_sha256": seam["exact_current_intake_method_sha256"],
    }
    receipt = {
        "schema": "independent_adjusted_base_method_structure_review/v1",
        "status": "ONE_CONFIRMED_PROVENANCE_FINDING_CURRENT_SOURCE_METADATA_SEAM_PASSES",
        "findings": [finding],
        "frozen_target_sha256": before,
        "frozen_target_count": len(before),
        "frozen_target_bytes": sum((RAW / path).stat().st_size for path in before),
        "source_closures_before_after": {"intake_count": len(pins), "intake_canonical_sha256": x.a.canonical(pins), "panel_count": len(panel_pins), "panel_canonical_sha256": m.canonical(panel_pins), "verified": True},
        "current_source_only_intake_panel_seam": seam,
        "source_override_restoration_on_exception": {"source_plan": True, "native_wrapper_with_fake_dependencies_only": True},
        "checks": {"recorded_intake_and_exporter_group": "25 passed in separate process", "recorded_synthetic_panel_group": "18 passed in separate process", "exploratory_all_groups_in_one_process": "41 passed, 2 false isolation failures: panel test collection loads the CAD library through frozen helper imports, violating intake tests' process-wide sys.modules assertions. No BREP was imported; the separately recorded commands both pass."},
        "coupling_and_reuse": "Two-cleat wrapper composes exact frozen adapter/exporter with scoped context-managed overrides. Current panel module reuses frozen raised-bank aperture, ports and mass primitives; no copied math or previous contact/force acceptance is supplied.",
        "retention": "All eight reviewed source/receipt/authority files stay in their existing ignored evidence paths; hashes, original review receipts, historical rendering maps and computation source closures remain separate. No raw geometry/manual/dependency copies, archive or prune were created.",
        "actual_BREP_import_or_query": False,
        "real_panel_or_global_K_or_q_native_or_browser_executed": False,
        "physical_readiness_or_capacity_claimed": False,
        "current_force_bridge_reviewed": False,
        "target_files_unchanged": True,
        "staging_or_commit": False,
        "review_script_sha256": sha(__file__),
        "command": "PYTHONPATH=. .venv/bin/python -B " + str(Path(__file__).relative_to(ROOT)),
    }
    output = Path(__file__).with_name("receipt.json")
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(output.relative_to(ROOT)), "receipt_sha256": sha(output)}))


if __name__ == "__main__":
    main()
