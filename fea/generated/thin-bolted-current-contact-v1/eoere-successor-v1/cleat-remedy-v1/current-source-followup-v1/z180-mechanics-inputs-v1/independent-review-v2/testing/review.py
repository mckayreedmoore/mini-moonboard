"""Bounded final output/provenance review; reuse the frozen v1 math review."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
D = OWN.parents[2]
ROOT = OWN.parents[9]
V1 = D / "independent-review-v1/testing"
V5 = D / "review-fix-v5"
FINAL = D / "runs-v1/attempt04/descriptor.json"
PREVIOUS = D / "runs-v1/attempt03/descriptor.json"
EXPECTED = {
    V5 / "descriptor.py": "dc7e6226ded6f62e64792a85309cde05db12b9867a1d1c492468ee086716d632",
    V5 / "inputs.json": "dd2f03f5735c7c0454e99af0e055edb8ae10c705aa1342dbaaf329009febc081",
    V5 / "test_descriptor.py": "a973b64e07e0c12bd11ce9f222d4f27cba0a04bbab18adb0a9a67031b76b7cf4",
    FINAL: "deccc585f3cc38cc315bf5618cb7ab7007b948e90cec8a4144c04a89cd2275df",
    D / "result-v2.json": "12e26549009068ae03e7a855dc3d8af959a1ae1ea45d192c8bd27921f9675db9",
    PREVIOUS: "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
    V1 / "review.py": "347918d001f32fc30c9cddb2a29233053991b9cd63a05c184c578bc4ff73e95a",
    V1 / "receipt.json": "424dd46cf1f704397ba63e7c54a78b86f5da86174aa6956dbc38b1cdda3bec93",
}


def read_json(path):
    return json.loads(path.read_bytes())


def initial_authentication():
    # Authenticate the reused review implementation before importing it.
    import hashlib
    import importlib.util
    for path, digest in EXPECTED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    spec = importlib.util.spec_from_file_location("frozen_v1_z180_testing_reuse", V1 / "review.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def final_claims(reuse, final, previous, compact):
    original = reuse.load(D / "descriptor.py", "authenticated_z180_original_data_key_contract")
    keys = (*original.DATA_KEYS, "geometry_delta_proof")
    assert len(original.DATA_KEYS) == 22 and all(final[key] == previous[key] for key in keys)
    changed = sorted(key for key in final if final[key] != previous[key])
    assert set(final) == set(previous) and changed == ["descriptor_source_corrections", "source_sha256"]
    mechanical = compact["mechanical_reproduction"]
    by_field = {key: reuse.canonical(final[key]) for key in keys}
    assert mechanical["canonical_sha256_by_field"] == by_field
    assert mechanical["combined_canonical_sha256"] == reuse.canonical({key: final[key] for key in keys})
    assert mechanical["only_changed_top_level_fields"] == changed
    assert mechanical["counts"] == final["geometry_delta_proof"]["counts"]
    assert mechanical["DATA_KEYS_count"] == 22 and mechanical["all_other_top_level_fields_exactly_equal"] is True
    assert mechanical["every_DATA_KEY_and_geometry_delta_proof_exactly_equal"] is True
    old_pins, new_pins = previous["source_sha256"], final["source_sha256"]
    added = {path: digest for path, digest in new_pins.items() if path not in old_pins}
    removed = {path: digest for path, digest in old_pins.items() if path not in new_pins}
    assert all(old_pins[path] == new_pins[path] for path in old_pins.keys() & new_pins.keys())
    assert added == {str((V5 / file).relative_to(ROOT)): EXPECTED[V5 / file] for file in ("descriptor.py", "inputs.json")}
    assert removed == {str((D / "review-fix-v4/inputs.json").relative_to(ROOT)): "a359cb1c7c3c30954d6e36204bd523cd0d565c10a9b78f9af09e6ddcbb66b6be"}
    closure = compact["source_closure"]
    assert closure["added"] == added and closure["removed"] == removed and closure["changed_existing_source_hashes"] == {}
    assert closure["consumed_pins"] == len(new_pins) == 1117 and closure["previous_consumed_pins"] == len(old_pins) == 1116
    assert closure["canonical_sha256"] == reuse.canonical(new_pins)
    assert compact["descriptor"] == reuse.ref(FINAL) and compact["previous_issued_descriptor"] == reuse.ref(PREVIOUS)
    assert compact["descriptor_bytes"] == FINAL.stat().st_size == 6092681
    corrections = dict(previous["descriptor_source_corrections"], canonical_output_adapter=reuse.ref(V5 / "descriptor.py"))
    assert final["descriptor_source_corrections"] == compact["generator_corrections"] == corrections
    assert compact["canonical_output_adapter"] == corrections["canonical_output_adapter"]
    assert compact["inputs"] == reuse.ref(V5 / "inputs.json")
    assert compact["canonical_output_guard"]["canonical_bound_output_path"] == str(FINAL)
    assert compact["canonical_output_guard"]["actual_trial_used_parent_alias_or_retarget"] is False
    assert compact["canonical_output_guard"]["source_schema_and_geometry_math_changed"] is False
    assert compact["complete_joint_resistance"] is final["complete_joint_resistance"] is None
    assert compact["release"] == final["release"] == previous["release"] and all(value is False for value in final["release"].values())
    for key in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        assert compact[key] is final[key] is False
    assert compact["mechanics_input_trial_performed"] is False
    assert compact["original_4in_hardware_retained_spacer_proposal_excluded"] is final["current_4in_hardware_retained_spacer_proposal_excluded"] is True
    assert compact["unresolved_joins"] == final["unresolved_joins"]
    prior_compact = read_json(D / "result.json")
    assert compact["sampling_limit_retained_from_issued_arithmetic"] == prior_compact["sampling_limit"]
    for row in compact["preservation"]["independent_review_snapshot_drift_observed_and_reported_to_parent"]:
        assert row["outside_consumed_descriptor_source_closure"] is True and row["path"] not in new_pins
        assert reuse.sha(ROOT / row["path"]) == row["later_observed_sha256"]
    reuse.verify_nested_refs(compact)
    return {"all_22_mechanical_keys_and_geometry_delta_proof_identical_to_reviewed_attempt03": True,
            "only_canonical_adapter_provenance_and_exact_closure_differ": True,
            "all_final_compact_claims_and_refs_match_saved_artifacts": True,
            "prior_review_snapshot_drift_matches_final_frozen_review_bytes": True}


def inert_controls(reuse):
    helper = reuse.load(V5 / "test_descriptor.py", "authenticated_v5_inert_fixture_reuse")
    fix = helper.fix
    checks = {}
    with tempfile.TemporaryDirectory(prefix="inert-boundaries-", dir=OWN.parent) as directory:
        temp = Path(directory)
        for kind in ("hardlink", "directory"):
            fixture = temp / kind
            with helper.inert_writer(fixture) as (v4, frozen):
                out = fixture / "packet/runs-v1/descriptor.json"
                out.parent.mkdir(parents=True)
                protected = fixture / "protected.json"
                protected.write_bytes(b"protected immutable bytes\n")
                if kind == "hardlink":
                    os.link(protected, out)
                else:
                    out.mkdir()
                with patch.object(fix, "OWN", fixture / "packet/review-fix-v5/descriptor.py"), \
                     patch.object(fix, "corrected_v4", return_value=v4), \
                     patch.object(frozen, "load_inputs", side_effect=AssertionError("intake reached")):
                    reuse.expect(FileExistsError, lambda out=out: fix.write_descriptor("unused", "unused", out))
                assert protected.read_bytes() == b"protected immutable bytes\n"
                assert out.is_dir() if kind == "directory" else out.read_bytes() == protected.read_bytes()
                checks[f"existing_{kind}_leaf_preserved_and_refused_before_intake"] = True
        parent = temp / "cli/packet/runs-v1/intended"
        parent.mkdir(parents=True)
        alias = parent.with_name("alias")
        alias.symlink_to(parent, target_is_directory=True)
        calls = []
        expected = {"path": "inert-only", "sha256": "inert-only", "bytes": 0, "force_execution_readiness_claimed": False}
        def delegate(inputs, digest, out):
            calls.append((inputs, digest, out))
            return expected
        captured = io.StringIO()
        with patch.object(fix, "OWN", temp / "cli/packet/review-fix-v5/descriptor.py"), \
             patch.object(fix, "corrected_v4", return_value=SimpleNamespace(write_descriptor=delegate)), redirect_stdout(captured):
            code = fix.main(["--inputs", "inert-input.json", "--inputs-sha256", "inert-sha", "--out", str(alias / "descriptor.json")])
        assert code == 0 and json.loads(captured.getvalue()) == expected
        assert calls == [(Path("inert-input.json"), "inert-sha", parent / "descriptor.json")]
        assert not (parent / "descriptor.json").exists()
        checks["actual_main_routes_exact_arguments_and_bound_parent_to_inert_delegate_without_generation"] = True
    assert "cadquery" not in sys.modules and "numpy" not in sys.modules
    assert not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules)
    return checks


def main():
    start = time.monotonic()
    reuse = initial_authentication()
    fixed = {str(path.relative_to(ROOT)): digest for path, digest in EXPECTED.items()}
    reuse.verify(fixed)
    prior_review = read_json(V1 / "receipt.json")
    assert prior_review["independent_z180_descriptor_source_checks_pass"] is True and prior_review["findings"] == []
    assert all(prior_review["pure_fixture_checks"].values())
    for path, digest in prior_review["source_sha256"].items():
        assert path not in fixed or fixed[path] == digest
        fixed[path] = digest
    final, previous, compact = read_json(FINAL), read_json(PREVIOUS), read_json(D / "result-v2.json")
    preflight_ref = compact["source_only_preflight"]
    reuse.verify({preflight_ref["path"]: preflight_ref["sha256"]})
    fixed[preflight_ref["path"]] = preflight_ref["sha256"]
    snapshot = read_json(ROOT / preflight_ref["path"])["preserved_frozen_files"]
    drift = {row["path"]: row for row in compact["preservation"]["independent_review_snapshot_drift_observed_and_reported_to_parent"]}
    assert len(snapshot) == compact["preservation"]["snapshot_refs_total"] == 29
    assert len(snapshot) - len(drift) == compact["preservation"]["snapshot_refs_unchanged"] == 27
    for source in snapshot:
        path, digest = source["path"], source["sha256"]
        if path in drift:
            assert digest == drift[path]["preflight_snapshot_sha256"]
            digest = drift[path]["later_observed_sha256"]
        assert path not in fixed or fixed[path] == digest
        fixed[path] = digest
    reuse.verify(fixed)
    reuse.verify(final["source_sha256"])
    reuse.verify(previous["source_sha256"])
    claims = final_claims(reuse, final, previous, compact)
    claims["all29_preservation_snapshot_refs_authenticated_with_exact_two_recorded_review_finalizations"] = True
    controls = inert_controls(reuse)
    environment = dict(os.environ, PYTHONPATH=str(ROOT))
    command = [sys.executable, "-B", "-m", "pytest", "--import-mode=importlib", "-q", "-p", "no:cacheprovider", str((V5 / "test_descriptor.py").relative_to(ROOT))]
    tests = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    lint_command = [sys.executable, "-B", "-m", "ruff", "check", str(V5.relative_to(ROOT)), str(OWN.relative_to(ROOT))]
    lint = subprocess.run(lint_command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert lint.returncode == 0, lint.stdout + lint.stderr
    reuse.verify(final["source_sha256"])
    reuse.verify(previous["source_sha256"])
    reuse.verify(fixed)
    receipt = {"schema": "eoere_z180_geometry_descriptors_independent_review/v1",
        "independent_z180_descriptor_source_checks_pass": True, "reviewer": "/root/intake_final_testing",
        "scope": "bounded final v5 testing/output/provenance review; previous math review reused",
        "descriptor": reuse.ref(FINAL), "compact_result": reuse.ref(D / "result-v2.json"),
        "source_sha256": fixed, "review_source": reuse.ref(OWN), "findings": [],
        "reused_math_review": {"source": reuse.ref(V1 / "review.py"), "receipt": reuse.ref(V1 / "receipt.json"),
            "unchanged_58_tests_or_math_fixtures_repeated": False, "prior_review_remains_byte_unchanged": True},
        "final_controls": {"command": command, "result": tests.stdout.strip()}, "additional_inert_controls": controls,
        "final_saved_artifact_checks": claims, "ruff": {"command": lint_command, "result": lint.stdout.strip()},
        "source_closure": {"pins": 1117, "canonical_sha256": reuse.canonical(final["source_sha256"]),
            "all_pins_verified_before_and_after": True, "previous1116_pin_sources_also_unchanged": True},
        "release": final["release"], "all_release_flags_false": all(value is False for value in final["release"].values()),
        "fresh_descriptor_trial_CAD_BREP_query_native_K_candidate_inputs_panel_forces_solve_or_browser_performed": False,
        "complete_joint_resistance": None, "force_execution_readiness_claimed": False,
        "limits": ["Only saved source hashes/metadata and inert output-boundary fixtures were used; no new descriptor was generated.",
                   "The canonical-parent correction and frozen exclusive writer retain their recorded scope; immutable mechanical equality reuses the prior math evidence.",
                   "Unadopted source-only geometry does not establish mechanics readiness, adoption, joint resistance or physical release."],
        "elapsed_seconds": time.monotonic() - start}
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pass": True, "controls": tests.stdout.strip(), "added_inert_controls": len(controls), "source_pins": 1117}))


if __name__ == "__main__":
    main()
