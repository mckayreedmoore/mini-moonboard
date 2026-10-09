"""Bounded final Z180 correctness review; reuse exact immutable arithmetic.

Read source/JSON, authenticate the prior independent arithmetic review, check
all final deltas and source pins, and run only the twelve new inert controls.
No descriptor CLI, arithmetic replay, CAD, mechanics inputs or solve is run.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
D = OWN.parents[2]
ROOT = D.parents[6]
FROZEN = {
    "review-fix-v5/descriptor.py": "dc7e6226ded6f62e64792a85309cde05db12b9867a1d1c492468ee086716d632",
    "review-fix-v5/inputs.json": "dd2f03f5735c7c0454e99af0e055edb8ae10c705aa1342dbaaf329009febc081",
    "review-fix-v5/test_descriptor.py": "a973b64e07e0c12bd11ce9f222d4f27cba0a04bbab18adb0a9a67031b76b7cf4",
    "review-fix-v5/preflight.json": "0e8ad664c4fafaabb6c9980d97b30da0359655e6d4d51c245c7379d186573882",
    "runs-v1/attempt04/descriptor.json": "deccc585f3cc38cc315bf5618cb7ab7007b948e90cec8a4144c04a89cd2275df",
    "result-v2.json": "12e26549009068ae03e7a855dc3d8af959a1ae1ea45d192c8bd27921f9675db9",
    "runs-v1/attempt03/descriptor.json": "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
    "independent-review-v1/correctness/review.py": "b6049fbe90910214c44bfbad0a1a4d412f836536d151a63c8bfbc853db228da5",
    "independent-review-v1/correctness/receipt.json": "f7ec99e36d129326214dd3444135efb463389cb630b3ca9c8a20fa4fb3a90895",
}
ABSOLUTE = {
    "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json":
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
    "/home/mckay-linux/repos/mini-moonboard/scripts/eoere_2026_adjustments.py":
        "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def name(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def ref(relative):
    return {"path": name(D/relative), "sha256": FROZEN[relative]}


def join(pins, additions):
    for path, expected in additions.items():
        require(path not in pins or pins[path] == expected, "conflicting immutable source pin: "+path)
        pins[path] = expected


def verify(pins):
    for text, expected in pins.items():
        path = Path(text)
        if path.is_absolute():
            require(ABSOLUTE.get(text) == expected, "foreign absolute source pin")
        else:
            path = (ROOT/path).resolve()
            require(path.is_relative_to(ROOT), "source path escaped repository")
        require(digest(path.read_bytes()) == expected, "frozen bytes changed: "+text)


def read(relative):
    return json.loads((D/relative).read_bytes())


def main():
    pins = {name(D/path): expected for path, expected in FROZEN.items()}
    verify(pins)
    prior_review = read("independent-review-v1/correctness/receipt.json")
    require(prior_review["schema"] == "eoere_z180_geometry_descriptors_independent_review/v1"
            and prior_review["success"] == "independent_z180_descriptor_source_checks_pass"
            and prior_review["findings"] == [] and not any(prior_review["release"].values())
            and prior_review["descriptor"] == ref("runs-v1/attempt03/descriptor.json"),
            "exact independent arithmetic review required")
    join(pins, prior_review["source_sha256"])
    before, final = read("runs-v1/attempt03/descriptor.json"), read("runs-v1/attempt04/descriptor.json")
    summary, inp = read("result-v2.json"), read("review-fix-v5/inputs.json")
    require(set(before) == set(final), "unexpected final descriptor field set")
    changed = sorted(k for k in final if before[k] != final[k])
    require(changed == ["descriptor_source_corrections", "source_sha256"], "geometry or other descriptor field changed")
    tree = ast.parse((D/"descriptor.py").read_bytes())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "DATA_KEYS" for t in n.targets))
    data_keys = ast.literal_eval(assignment.value)
    require(len(data_keys) == 22, "original geometry DATA_KEYS census differs")
    hashes = {k: canonical(final[k]) for k in (*data_keys, "geometry_delta_proof")}
    require(all(before[k] == final[k] for k in hashes), "reviewed mechanical data or geometry proof changed")
    reproduction = summary["mechanical_reproduction"]
    require(reproduction["DATA_KEYS_count"] == 22 and reproduction["canonical_sha256_by_field"] == hashes
            and reproduction["combined_canonical_sha256"] == canonical({k: final[k] for k in hashes})
            and reproduction["only_changed_top_level_fields"] == changed
            and reproduction["counts"] == final["geometry_delta_proof"]["counts"]
            and reproduction["every_DATA_KEY_and_geometry_delta_proof_exactly_equal"] is True
            and reproduction["all_other_top_level_fields_exactly_equal"] is True,
            "compact final delta claims differ")
    old_sources, new_sources = before["source_sha256"], final["source_sha256"]
    added = {k:v for k,v in new_sources.items() if k not in old_sources}
    removed = {k:v for k,v in old_sources.items() if k not in new_sources}
    changed_pins = {k:(v,new_sources[k]) for k,v in old_sources.items() if k in new_sources and v != new_sources[k]}
    require(len(old_sources) == 1116 and len(new_sources) == 1117 and not changed_pins
            and added == {name(D/k):FROZEN[k] for k in ("review-fix-v5/descriptor.py", "review-fix-v5/inputs.json")}
            and removed == {name(D/"review-fix-v4/inputs.json"): "a359cb1c7c3c30954d6e36204bd523cd0d565c10a9b78f9af09e6ddcbb66b6be"},
            "unexpected producer source-closure delta")
    closure = summary["source_closure"]
    require(closure == {"added":added, "removed":removed, "changed_existing_source_hashes":{},
            "consumed_pins":1117, "previous_consumed_pins":1116, "canonical_sha256":canonical(new_sources),
            "authenticated_before_after_and_post_comparison":True}, "compact source closure differs")
    join(pins, new_sources)
    verify(pins)
    old_input = read("review-fix-v4/inputs.json")
    expected_input = {**old_input, "scope":{**old_input["scope"],
        "canonical_output_parent_bound_before_mkdir_reservation_and_delegation":True},
        "sources":{**old_input["sources"], "canonical_output_adapter":ref("review-fix-v5/descriptor.py")}}
    require(inp == expected_input, "final input changed geometry or source scope")
    correction = {**before["descriptor_source_corrections"], "canonical_output_adapter":ref("review-fix-v5/descriptor.py")}
    require(final["descriptor_source_corrections"] == summary["generator_corrections"] == correction,
            "final output correction provenance differs")
    spec = importlib.util.spec_from_file_location("z180_final_independent_correctness_v5", D/"review-fix-v5/descriptor.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    v3 = adapter.corrected_v4().corrected_v3()
    require(v3.source_correction_record(inp) == correction, "actual source-only adapter provenance differs")
    require(adapter.bind_output(D/"runs-v1/attempt04/descriptor.json") == (D/"runs-v1/attempt04/descriptor.json").absolute(),
            "actual exact final output binding differs")
    guard = summary["canonical_output_guard"]
    require(guard["canonical_bound_output_path"] == str(adapter.bind_output(D/"runs-v1/attempt04/descriptor.json")),
            "compact canonical bound output path differs")
    require(guard["actual_trial_used_parent_alias_or_retarget"] is False
            and guard["source_schema_and_geometry_math_changed"] is False, "compact output scope differs")
    for key, expected in (("descriptor",ref("runs-v1/attempt04/descriptor.json")), ("previous_issued_descriptor",ref("runs-v1/attempt03/descriptor.json")),
                          ("canonical_output_adapter",ref("review-fix-v5/descriptor.py")), ("inputs",ref("review-fix-v5/inputs.json")),
                          ("tests",ref("review-fix-v5/test_descriptor.py")), ("source_only_preflight",ref("review-fix-v5/preflight.json")),
                          ("original_arithmetic_result",prior_review["compact_result"]), ("release",final["release"]),
                          ("unresolved_joins",final["unresolved_joins"])):
        require(summary[key] == expected, "compact final exact reference differs: "+key)
    require(summary["descriptor_bytes"] == (D/"runs-v1/attempt04/descriptor.json").stat().st_size,
            "compact final byte count differs")
    require(summary["sampling_limit_retained_from_issued_arithmetic"] == read("result.json")["sampling_limit"],
            "recorded sampling limitation changed")
    require(final["release"] == before["release"] == inp["release"] == prior_review["release"]
            and not any(final["release"].values()) and final["complete_joint_resistance"] is None,
            "release or capacity boundary changed")
    for key in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        require(final[key] is summary[key] is False, "final no-force scope changed")
    require(summary["mechanics_input_trial_performed"] is False, "unexpected mechanics input trial claim")
    test_command = [sys.executable, "-B", "-m", "pytest", "--import-mode=importlib", "-q", "-p", "no:cacheprovider",
                    str(D/"review-fix-v5/test_descriptor.py")]
    tests = subprocess.run(test_command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    require(tests.returncode == 0 and "12 passed" in tests.stdout, tests.stdout+tests.stderr)
    require(not any(k in sys.modules for k in ("cadquery", "OCP", "numpy")), "review imported numerical/CAD mechanics")
    pins[name(OWN)] = digest(OWN.read_bytes())
    verify(pins)
    receipt = {"schema":"eoere_z180_geometry_descriptors_independent_review/v1",
        "success":"independent_z180_descriptor_source_checks_pass", "independent_z180_descriptor_source_checks_pass":True,
        "status":"CLEAN_FINAL_SOURCE_PROVENANCE_OUTPUT_GUARD_AND_UNCHANGED_GEOMETRY", "findings":[],
        "descriptor":ref("runs-v1/attempt04/descriptor.json"), "compact_result":ref("result-v2.json"),
        "geometry":final["geometry"], "parent_descriptors":final["parent_descriptors"],
        "reused_immutable_arithmetic_review":ref("independent-review-v1/correctness/receipt.json"),
        "checks":{"all22_DATA_KEYS_and_geometry_delta_proof_exactly_identical":True,
            "all_other_descriptor_fields_identical_except_source_pins_and_correction_record":True,
            "final1117_source_pins_authenticated_before_after":True,
            "source_closure_added_adapter_and_input_removed_only_prior_input":True,
            "actual_source_only_adapter_provenance_equals_final_saved_output":True,
            "canonical_output_parent_binding_and_original_unresolved_leaf_guards":True,
            "new_inert_tests_passed":12, "prior58_math_and_source_tests_reused_without_rerun":True,
            "final_compact_refs_delta_hashes_counts_and_scope_claims_verified":True,
            "all_source_union_pins_before_after_unchanged":True},
        "geometry_field_canonical_sha256":hashes, "counts":final["geometry_delta_proof"]["counts"],
        "source_sha256":dict(sorted(pins.items())), "test_command":test_command, "test_result":tests.stdout.strip(),
        "execution":{"source_JSON_and_inert_controls_only":True, "descriptor_CLI_or_arithmetic_replay":False,
            "CAD_BREP_import_or_query":False, "mechanics_input_construction_operator_K_q_forces_or_solve":False},
        "limits":["The frozen v1 arithmetic review applies because all22 geometry data fields and the entire geometry proof remain exact. This bounded review reruns only12 new inert output controls.",
            "No unadopted proposal adoption, current force admission, complete-joint resistance or physical/fabrication/climbing release follows.",
            "The maximum recorded sampled second-moment relative error remains0.25550908214476425; pressure, rocking accuracy and physical applicability remain unqualified.",
            "Unrelated peer-review preflight snapshot drift is disclosed in the compact result and is outside the producer source closure; this review consumes its own exact immutable prior correctness evidence."],
        "release":dict(final["release"]), "python":sys.version}
    out = OWN.with_name("receipt.json")
    with out.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"receipt":name(out), "sha256":digest(out.read_bytes()), "review_helper_sha256":digest(OWN.read_bytes()),
                      "source_union_pins":len(pins), "status":receipt["status"]},sort_keys=True))


if __name__ == "__main__":
    main()
