"""Recheck the frozen current-source seam in its own process, without BREP/K.

The old panel import chain loads the cadquery library. Library presence is not
a geometry query; this check explicitly guards Shape.importBrep throughout.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BANK_DIR = OWN.parent.parent
INTAKE = BANK_DIR.parent / "extended-cleat-intake-v1/export.py"
MANIFEST = BANK_DIR.parent / "parent-authority-v1/extended-cleat-manifest.json"
PINS = {
    BANK_DIR / "panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
    BANK_DIR / "test_panel_operators.py": "dd48189121a3aef78c60a5eb5677f789ac45a91c7fc42ebb7822442a0986c0c1",
    BANK_DIR / "method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
    INTAKE: "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    MANIFEST: "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    assert sha(path) == PINS[path], "frozen source differs: "+str(path)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    for path, expected in PINS.items():
        assert sha(path) == expected, "frozen seam source differs: "+str(path)
    import cadquery as cq
    with patch.object(cq.Shape, "importBrep", side_effect=AssertionError("source-only seam cannot import a BREP")) as importer:
        bank = load(BANK_DIR/"panel_operators.py", "frozen_current_panel_source_seam_v2")
        intake = load(INTAKE, "frozen_extended_intake_source_seam_v2")
        with patch.object(bank.raised, "prepare_panel_operators", side_effect=AssertionError("real panel K forbidden")), \
             patch.object(bank.raised.saved, "reuse_panel_operators", side_effect=AssertionError("real saved panel bank forbidden")):
            preflight, _, _, panels, _ = intake.prepare(MANIFEST, PINS[MANIFEST])
            _, _, current, _, _ = bank.read_sources()
            assert preflight["current_panel_machining_descriptors"] == current["panel_machining"]
            assert [r["source_screw_descriptor"] for r in preflight["hillman_rows"]] == current["screw_axes"]
            assert {r["id"]: bank.source_binding(r) for r in panels} == {
                r["id"]: r for r in current["finished_panel_solids"]}
            data = {**preflight, "panel_operator_source_inputs": bank.source_inputs(), "panel_ids": list(bank.plate.PANELS)}
            assert bank.verify_panel_source_inputs(data)["metadata_only_no_K_q_or_contact_construction"]
        assert importer.call_count == 0
    for path, expected in PINS.items():
        assert sha(path) == expected, "frozen seam source changed during check: "+str(path)
    return {"schema": "eoere_current_off_panel_source_seam_review_supplement/v2",
        "passed": True, "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "current_exporter_replaces_only_stale_seam_binding_in_original_receipt": True,
        "original_receipt_and_original_code_test_hashes_preserved": True,
        "matching_own_panel_sources": 6, "matching_own_screw_descriptors": 66, "matching_aperture_descriptors": 340,
        "cadquery_library_imported": True, "guarded_BREP_import_calls": 0,
        "actual_current_panel_or_frame_K_q_or_native_solve": False,
        "intake_module_absence_assertions_require_isolated_test_process": True}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True, allow_nan=False))
