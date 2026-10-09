"""Final bounded output/provenance review; reuse frozen geometry/math reviews.

Only source/saved-JSON reads, byte hashing and temporary inert output controls.
No genuine descriptor CLI, geometry arithmetic, input preparation or mechanics.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
EXPECTED = {
    "review-fix-v5/descriptor.py": "dc7e6226ded6f62e64792a85309cde05db12b9867a1d1c492468ee086716d632",
    "review-fix-v5/inputs.json": "dd2f03f5735c7c0454e99af0e055edb8ae10c705aa1342dbaaf329009febc081",
    "runs-v1/attempt04/descriptor.json": "deccc585f3cc38cc315bf5618cb7ab7007b948e90cec8a4144c04a89cd2275df",
    "result-v2.json": "12e26549009068ae03e7a855dc3d8af959a1ae1ea45d192c8bd27921f9675db9",
}
PRIOR = {
    "structure/review.py": "b90aab81dc50a31d3397defc59140bbf1dbe0308fd594ee7146d5af2937fe0cf",
    "structure/receipt.json": "e76b4ba86ea3bcccfabb45ccea330df7df118545b415e48464c4a2a854b09056",
    "correctness/review.py": "b6049fbe90910214c44bfbad0a1a4d412f836536d151a63c8bfbc853db228da5",
    "correctness/receipt.json": "f7ec99e36d129326214dd3444135efb463389cb630b3ca9c8a20fa4fb3a90895",
    "testing/review.py": "347918d001f32fc30c9cddb2a29233053991b9cd63a05c184c578bc4ff73e95a",
    "testing/receipt.json": "424dd46cf1f704397ba63e7c54a78b86f5da86174aa6956dbc38b1cdda3bec93",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def inert_output_checks(adapter, writer):
    with tempfile.TemporaryDirectory(prefix="z180-final-output-review-") as temporary:
        root = Path(temporary).resolve()
        packet, outside, alias = root / "packet", root / "outside", root / "alias"
        intended = packet / "runs-v1/intended"
        intended.mkdir(parents=True)
        outside.mkdir()
        alias.symlink_to(intended, target_is_directory=True)
        protected = outside / "descriptor.json"
        protected.write_text("preserved outside bytes\n")
        events = []

        def invoke(out, exception, *, retarget=False, late=False):
            events.clear()

            def delegate():
                events.append("delegate")
                if retarget:
                    alias.unlink()
                    alias.symlink_to(outside, target_is_directory=True)
                if late:
                    out.write_text("preserved late entry\n")
                return SimpleNamespace(write_descriptor=writer)

            def intake(*args, **kwargs):
                events.append("inert intake")
                assert read(intended / "descriptor.json")["status"] == "STARTED"
                raise ValueError("inert retained failure")

            with patch.dict(adapter["write_descriptor"].__globals__, {
                    "OWN": packet / "review-fix-v5/descriptor.py", "corrected_v4": delegate}), \
                    patch.dict(writer.__globals__, {"OWN": packet / "descriptor.py", "ROOT": root, "load_inputs": intake}):
                try:
                    adapter["write_descriptor"](root / "unused.json", "unused", out)
                except exception as error:
                    return str(error)
                raise AssertionError("expected inert rejection")

        assert invoke(alias / "descriptor.json", ValueError, retarget=True) == "inert retained failure"
        saved = read(intended / "descriptor.json")
        assert saved["status"] == "FAILED" and not any(saved["release"].values())
        assert events == ["delegate", "inert intake"] and protected.read_text() == "preserved outside bytes\n"
        cases = ["alias retarget before delegation writes STARTED/FAILED only to bound owned parent"]
        assert "belongs under this packet" in invoke(alias / "other.json", ValueError)
        assert not events and not (outside / "other.json").exists()
        cases.append("initial outside alias rejected before adapter load")
        invoke(intended / "descriptor.json", FileExistsError)
        assert events == ["delegate"] and read(intended / "descriptor.json") == saved
        cases.append("retained failed leaf cannot be reused; intake is not repeated")
        missing = outside / "missing.json"
        dangling = intended / "dangling.json"
        dangling.symlink_to(missing)
        invoke(dangling, FileExistsError)
        assert events == ["delegate"] and dangling.is_symlink() and not missing.exists()
        cases.append("dangling canonical leaf remains unresolved and rejects before intake")
        late = intended / "late.json"
        invoke(late, FileExistsError, late=True)
        assert events == ["delegate"] and late.read_text() == "preserved late entry\n"
        cases.append("late canonical leaf is preserved by exclusive reservation")
        return cases


def main():
    assert all(sha(HERE / name) == digest for name, digest in EXPECTED.items())
    assert all(sha(HERE / "independent-review-v1" / name) == digest for name, digest in PRIOR.items())
    prior_module = runpy.run_path(str(HERE / "independent-review-v1/structure/review.py"))
    old_targets = prior_module["EXPECTED"]
    frozen = {relative(path): sha(path) for path in HERE.rglob("*") if path.is_file()
              and not any(part == "__pycache__" or part.startswith("independent-review-v2") for part in path.relative_to(HERE).parts)}
    inp, result, compact = (read(HERE / name) for name in ("review-fix-v5/inputs.json", "runs-v1/attempt04/descriptor.json", "result-v2.json"))
    old_input, old_result = (read(HERE / name) for name in ("review-fix-v4/inputs.json", "runs-v1/attempt03/descriptor.json"))
    prior_structure = read(HERE / "independent-review-v1/structure/receipt.json")
    prior_math = read(HERE / "independent-review-v1/correctness/receipt.json")
    assert prior_math["success"] == "independent_z180_descriptor_source_checks_pass" and prior_math["findings"] == []
    assert prior_math["descriptor"] == prior_structure["descriptor"] == compact["previous_issued_descriptor"]
    assert prior_structure["sourcepins"]["canonical_sha256"] == canonical(old_result["source_sha256"])
    assert [finding["id"] for finding in prior_structure["findings"]] == ["canonical_output_parent_not_bound"]
    new_adapter = {"path": relative(HERE / "review-fix-v5/descriptor.py"), "sha256": EXPECTED["review-fix-v5/descriptor.py"]}
    expected_input = copy.deepcopy(old_input)
    expected_input["sources"]["canonical_output_adapter"] = new_adapter
    expected_input["scope"]["canonical_output_parent_bound_before_mkdir_reservation_and_delegation"] = True
    assert inp == expected_input
    pins = copy.deepcopy(old_result["source_sha256"])
    removed = {relative(HERE / "review-fix-v4/inputs.json"): pins.pop(relative(HERE / "review-fix-v4/inputs.json"))}
    added = {relative(HERE / "review-fix-v5/inputs.json"): EXPECTED["review-fix-v5/inputs.json"], new_adapter["path"]: new_adapter["sha256"]}
    pins.update(added)
    assert pins == result["source_sha256"] and len(pins) == 1117
    expected_result = copy.deepcopy(old_result)
    expected_result["source_sha256"] = pins
    expected_result["descriptor_source_corrections"]["canonical_output_adapter"] = new_adapter
    assert result == expected_result

    def unchanged():
        assert all(sha(HERE / name) == digest for name, digest in (old_targets | EXPECTED).items())
        assert all(sha(ROOT / path) == digest for path, digest in frozen.items())
        assert all(sha(Path(path) if Path(path).is_absolute() else ROOT / path) == digest for path, digest in pins.items())
        assert all(sha(HERE / "independent-review-v1" / name) == digest for name, digest in PRIOR.items())

    unchanged()
    descriptor_ref = {"path": relative(HERE / "runs-v1/attempt04/descriptor.json"), "sha256": EXPECTED["runs-v1/attempt04/descriptor.json"]}
    assert compact["descriptor"] == descriptor_ref
    assert compact["descriptor_bytes"] == (HERE / "runs-v1/attempt04/descriptor.json").stat().st_size == 6092681
    assert compact["inputs"] == {"path": relative(HERE / "review-fix-v5/inputs.json"), "sha256": EXPECTED["review-fix-v5/inputs.json"]}
    assert compact["canonical_output_adapter"] == new_adapter
    assert compact["generator_corrections"] == result["descriptor_source_corrections"]
    closure = compact["source_closure"]
    assert closure["consumed_pins"] == 1117 and closure["previous_consumed_pins"] == 1116
    assert closure["added"] == added and closure["removed"] == removed and closure["changed_existing_source_hashes"] == {}
    assert closure["canonical_sha256"] == canonical(pins)
    assert compact["original_arithmetic_result"] == {"path": relative(HERE / "result.json"), "sha256": old_targets["result.json"]}
    for name in ("tests", "source_only_preflight"):
        ref = compact[name]
        assert sha(ROOT / ref["path"]) == ref["sha256"]
    for name in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                 "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        assert result[name] is compact[name] is False
    assert compact["mechanics_input_trial_performed"] is False
    assert result["complete_joint_resistance"] is compact["complete_joint_resistance"] is None
    assert result["release"] == compact["release"] == inp["release"] and not any(result["release"].values())
    assert compact["unresolved_joins"] == result["unresolved_joins"]
    assert compact["sampling_limit_retained_from_issued_arithmetic"] == read(HERE / "result.json")["sampling_limit"]

    tree = ast.parse((HERE / "review-fix-v5/descriptor.py").read_bytes())
    imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= sys.stdlib_module_names
    binder = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "bind_output")
    assert ast.unparse(binder.body[-1]) == "return canonical_parent / out.name"
    entry = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "write_descriptor")
    assert ast.unparse(entry.body[0]) == "bound = bind_output(out)"
    assert ast.unparse(entry.body[1]) == "return corrected_v4().write_descriptor(inputs_path, inputs_sha256, bound)"
    adapter = runpy.run_path(str(HERE / "review-fix-v5/descriptor.py"))
    private, other = adapter["corrected_v4"](), adapter["corrected_v4"]()
    assert private is not other and private.corrected_v3 is not other.corrected_v3
    v3 = private.corrected_v3()
    assert v3.source_correction_record(inp) == result["descriptor_source_corrections"]
    bad_input = copy.deepcopy(inp)
    bad_input["sources"]["canonical_output_adapter"]["sha256"] = "foreign"
    try:
        v3.source_correction_record(bad_input)
    except ValueError as error:
        assert "exact canonical-output correction provenance" in str(error)
    else:
        raise AssertionError("foreign adapter provenance accepted")
    base = v3.corrected_frozen_module(v3.verified_v2())
    assert base is not sys.modules.get(base.__name__)
    keys = list(base.DATA_KEYS) + ["geometry_delta_proof"]
    assert len(base.DATA_KEYS) == 22
    mechanical = compact["mechanical_reproduction"]
    assert mechanical["canonical_sha256_by_field"] == {key: canonical(result[key]) for key in keys}
    assert mechanical["combined_canonical_sha256"] == canonical({key: result[key] for key in keys})
    assert mechanical["counts"] == result["geometry_delta_proof"]["counts"]
    assert all(result[key] == old_result[key] for key in keys)
    cases = inert_output_checks(adapter, base.write_descriptor)
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    receipt = {
        "schema": "eoere_z180_geometry_descriptors_independent_review/v1",
        "status": "CLEAN_CANONICAL_OUTPUT_OWNERSHIP_PROVENANCE_AND_GEOMETRY_REUSE_SCOPE",
        "success": "independent_z180_descriptor_source_checks_pass",
        "independent_z180_descriptor_source_checks_pass": True, "findings": [],
        "descriptor": descriptor_ref, "compact_result": {"path": relative(HERE / "result-v2.json"), "sha256": EXPECTED["result-v2.json"]},
        "source_sha256": pins, "release": result["release"], "all_release_false": True,
        "target_sha256": {relative(HERE / name): digest for name, digest in EXPECTED.items()},
        "source_closure": {"verified_before_after": 1117, "canonical_sha256": canonical(pins),
                           "exact_old_closure_with_distinct_final_input_and_adapter": True,
                           "removed_from_computational_closure_but_preserved": removed, "added": added},
        "reused_reviews": {"geometry_math": {"path": relative(HERE / "independent-review-v1/correctness/receipt.json"), "sha256": PRIOR["correctness/receipt.json"]},
                           "structure_finding": {"path": relative(HERE / "independent-review-v1/structure/receipt.json"), "sha256": PRIOR["structure/receipt.json"]},
                           "geometry_arithmetic_or_genuine_descriptor_replayed": False},
        "closed_finding": {"id": "canonical_output_parent_not_bound", "fixed_by": new_adapter,
                           "original_frozen_source_and_review_unchanged": True, "inert_controls": cases},
        "checks": {"22_DATA_KEYS_and_geometry_proof_exactly_attempt03": True,
                   "all_other_fields_exact_except_source_pins_and_added_correction_identity": True,
                   "private_authenticated_adapter_delegation_and_exact_provenance": True,
                   "wrong_parent_rejected_before_adapter_load": True,
                   "canonical_parent_bound_before_delegation_mkdir_and_exclusive_reservation": True,
                   "unresolved_leaf_exclusive_STARTED_FAILED_and_inode_guards_retained": True,
                   "source_only_labels_release_and_deferred_boundaries_unchanged": True,
                   "stdlib_imports": sorted(imports)},
        "retention": {"frozen_records_verified_before_after": len(frozen), "frozen_map_canonical_sha256": canonical(frozen),
                      "all_old_targets_failures_attempts_and_six_prior_reviews_unchanged_in_this_pass": True,
                      "producer_recorded_prior_testing_review_drift_is_outside_final_consumed_closure": True,
                      "earlier_drift_records_and_current_peer_bytes_preserved": True,
                      "new_review_or_result_does_not_replace_old_records": True},
        "limits": ["Only final source/output ownership and saved descriptor comparisons were reviewed; earlier frozen geometry/math proofs are reused.",
                   "The full1117-pin map is retained explicitly as requested; the large descriptor remains an exact referenced ignored witness.",
                   "No genuine descriptor CLI, geometry arithmetic replay, mechanics input preparation, panel preparation, CAD/BREP query, K/q/force, native solve, docs or Git operation.",
                   "Saved native receiver observations, analytic COM/contact/floor derivations and proposal/current authorities remain distinct. No geometry adoption, force admission, resistance, physical or climbing acceptance follows.",
                   "Fresh parent input/method/cases/RHS/operators/response/admission and execution slot remain deferred; no new physical or sign-off prerequisite is added."],
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN), "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"success": receipt["success"], "findings": 0, "pins": len(pins), "inert_controls": len(cases),
                      "helper_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
