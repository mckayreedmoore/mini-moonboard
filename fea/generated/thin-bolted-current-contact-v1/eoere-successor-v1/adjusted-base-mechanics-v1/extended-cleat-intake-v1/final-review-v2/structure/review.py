"""Independent source/architecture review; no genuine BREP query or mechanics.

Run with PYTHONPATH=. .venv/bin/python -B PATH/review.py. The three isolated
pytest commands recorded below were independently run before this receipt.
Only this review directory is written; temporary fake fixtures use /tmp.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[8]
INTAKE = OWN.parents[2]
RAW = INTAKE.parent
WRAPPER = INTAKE / "review-fix-v2/export.py"
MANIFEST = RAW / "parent-authority-v1/extended-cleat-manifest.json"
MANIFEST_SHA = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"
EXPECTED = {
    INTAKE / "export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    WRAPPER: "93ed36c39b4237cd587498fbb9dd2b2b7e3d275afc2be89302dab178c25d5858",
    INTAKE / "review-fix-v2/verification.json": "a046295fd38714893276dda6f495307821ab2c2545107298bb530d897e7e8ed3",
    MANIFEST: MANIFEST_SHA,
    RAW / "parent-authority-v1/adjusted-base-manifest.json": "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert all(digest(path) == expected for path, expected in EXPECTED.items())
    spec = importlib.util.spec_from_file_location("independent_structure_reserving_wrapper", WRAPPER)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    x = wrapper.load_frozen()
    prepared = x.prepare(MANIFEST, MANIFEST_SHA)
    p, _old, report, panels, pins = prepared
    x.a.verify(pins)
    assert len(pins) == 1076
    assert len(report["finished_solids"]) == 22 and len(panels) == 6
    assert len(p["gross_raw_timber_rows"]) == 22
    assert len(p["physical_owner_gravity_descriptors"]) == 150
    assert len(p["shaft_descriptors"]) == 100 and len(p["hillman_rows"]) == 66
    assert p["optional_2026_extra"] is False and not any(p["release"].values())
    assert p["case_provider"]["fresh_cases_ready"] is False
    assert p["panel_refresh"]["fresh_geometry_source_contract_required"] is True
    assert not p["historical_q_forces_or_passes_transferred"]
    assert not p["candidate_CAD_K_factorization_q_force_or_native_run_performed"]
    original_prepare = x.e.prepare
    restoration = {}
    for failure in (False, True):
        def fake_plan(*args, should_fail=failure):
            assert x.e.prepare(*args) is prepared
            if should_fail:
                raise RuntimeError("synthetic source-plan failure")
            return {"serial_slot_API": {}}
        with patch.object(x, "prepare", lambda *_: prepared), patch.object(x.e, "source_plan", fake_plan):
            try:
                x.source_plan(MANIFEST, MANIFEST_SHA)
            except RuntimeError:
                assert failure
        assert x.e.prepare is original_prepare
        restoration[f"source_plan_{'exception' if failure else 'success'}"] = True
    with tempfile.TemporaryDirectory(prefix="eoere-structure-fake-") as temporary:
        fake_slot = Path(temporary) / "synthetic-slot.json"
        fake_slot.write_text(json.dumps({"status": "FREE_SLOT", "cached_descriptor_extraction_authorized": True,
                                        "approved_geometry_sha256": x.GEOMETRY["sha256"],
                                        "approved_manifest_sha256": MANIFEST_SHA}))
        for failure in (False, True):
            def fake_export(*args, should_fail=failure):
                assert x.e.prepare(*args[:2]) is prepared
                if should_fail:
                    raise RuntimeError("synthetic native-callback failure")
                return {"geometry": p["geometry"], "source_sha256": dict(pins)}
            with patch.dict(os.environ, {"EOERE_PARENT_SERIALIZED_EXTRACTION": "1"}), \
                    patch.object(x, "prepare", lambda *_: prepared), patch.object(x.e, "export_native", fake_export):
                try:
                    x.export_native(MANIFEST, MANIFEST_SHA, fake_slot, digest(fake_slot))
                except RuntimeError:
                    assert failure
            assert x.e.prepare is original_prepare
            restoration[f"fake_export_{'exception' if failure else 'success'}"] = True
        output = Path(temporary) / "source-only.json"
        plan = wrapper.export_to_file(MANIFEST, MANIFEST_SHA, output)
        assert plan["schema"] == "eoere_extended_cleat_cached_source_export_plan/v1"
        assert len(plan["source_sha256"]) == 1077
        assert plan["native_queries_deferred"] and plan["candidate_K_q_forces_or_acceptance"] is None
        assert plan["manifest"]["sha256"] == MANIFEST_SHA
        assert plan["geometry"]["sha256"] == "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
        assert plan["optional_2026_extra"] is False and not any(plan["release"].values())
        x.a.verify(plan["source_sha256"])
    assert "cadquery" not in sys.modules
    assert all(digest(path) == expected for path, expected in EXPECTED.items())
    dependencies = p["geometry_review_evidence"]["dependency_checks"]
    assert [d["current_computational_overlap_pins_verified"] for d in dependencies] == [0, 582, 710, 0]
    historical_runtime = {path: value for row in dependencies
                          for path, value in row["historical_viewer_hashes_not_used_as_current_runtime"].items()}
    assert set(historical_runtime) == {"site/index.html", "site/eoere-2026-adjustments-overlay.mjs"}
    assert not (set(historical_runtime) & set(pins))
    reviewed = [INTAKE / "export.py", WRAPPER, RAW / "adapter.py",
                RAW / "current-source-export-v1/export.py", RAW.parent / "mechanics-inputs-v1/extract.py",
                INTAKE / "test_extended_intake.py", INTAKE / "review-fix-v2/test_output_reservation.py",
                RAW / "current-source-export-v1/test_export.py", INTAKE / "verification.json",
                INTAKE / "review-fix-v2/verification.json", MANIFEST,
                RAW / "parent-authority-v1/adjusted-base-manifest.json", OWN]
    receipt = {
        "schema": "eoere_extended_cleat_intake_independent_structure_review/v2",
        "status": "PASS_SOURCE_ONLY_ARCHITECTURE_AND_RETENTION_NO_CONFIRMED_BLOCKING_FINDINGS",
        "scope": "Exact current extended-cleat OFF cached-solid intake and corrected atomic output wrapper only",
        "confirmed_findings": [],
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in reviewed},
        "source_closure": {"verified_pins": len(plan["source_sha256"]),
                           "canonical_sha256": x.a.canonical(plan["source_sha256"]),
                           "before_after_unchanged": True},
        "fake_scoped_override_restoration": restoration,
        "independent_isolated_tests": [
            {"command": "PYTHONPATH=. .venv/bin/python -B -m pytest -q " + str((INTAKE / "review-fix-v2/test_output_reservation.py").relative_to(ROOT)), "passed": 6, "seconds": 1.66},
            {"command": "PYTHONPATH=. .venv/bin/python -B -m pytest -q " + str((INTAKE / "test_extended_intake.py").relative_to(ROOT)), "passed": 17, "seconds": 2.34},
            {"command": "PYTHONPATH=. .venv/bin/python -B -m pytest -q " + str((RAW / "current-source-export-v1/test_export.py").relative_to(ROOT)), "passed": 8, "seconds": .26},
        ],
        "architecture": {
            "ownership": "adapter owns adjusted-base ancestry, geometry transforms and source descriptors; intake owns exact extension and two-cleat gross/source replacements; frozen exporter owns query mechanics; corrected wrapper owns output lifecycle",
            "reuse_boundary": "Source-plan/native-export prepare substitutions and cached importer/bore substitutions use context-managed patches; parent serialization remains required for process-global CadQuery importBrep patch",
            "geometry": plan["geometry"], "manifest": plan["manifest"],
            "inventory": {"gross_timber_profiles": 22, "finished_sources": 28, "physical_owners": 150, "shafts": 100, "Hillman_screws": 66},
            "current_historical_separation": "Current computational pins are verified; four exact geometry review receipts remain authority evidence. Historical overlapping computational pins agree; two historical viewer-runtime hashes remain excluded from current runtime closure.",
            "output_lifecycle": "Corrected entry point exclusively creates and fsyncs STARTED before lazy loading/producer; same descriptor receives success or FAILED. Abrupt callback exit retains STARTED. The frozen original CLI remains historical and must not be used for the new extraction.",
        },
        "remaining_parent_gates": [
            "Parent review and exact same-manifest serialized slot before genuine cached-solid descriptor extraction",
            "Parent final validation of all current volume/bounds/COM/topology, bore/seat, face/contact/flange and floor observations after extraction",
            "Current panel bank and force bridge are separate unready review targets; this receipt does not admit their methods, outputs or fields",
            "No current global K/q/force or physical/structural acceptance follows from source closure or fake controls",
        ],
        "retention": {"active": "Exact frozen manifests, original and corrected intake sources/tests/receipts, transitive computational closure and future current extraction remain active dependencies",
                      "archive_or_prune_performed": False,
                      "archive_eligibility": "No input or frozen evidence is disposable merely because historical or ignored; later archive requires consumer/process/ownership checks and evidence_archive verified recovery before separate prune",
                      "new_review_artifacts": [str(OWN.relative_to(ROOT)), str(OWN.with_name("receipt.json").relative_to(ROOT))],
                      "bulky_artifacts_added": False},
        "genuine_BREP_queries_or_production_extraction_or_panel_K_global_q_native_browser": False,
        "actual_parent_slot_created": False,
        "shared_docs_targets_staging_commits_pushes_changed": False,
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "pins": receipt["source_closure"]["verified_pins"],
                      "canonical_sha256": receipt["source_closure"]["canonical_sha256"],
                      "review_sha256": digest(OWN), "receipt_sha256": digest(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
