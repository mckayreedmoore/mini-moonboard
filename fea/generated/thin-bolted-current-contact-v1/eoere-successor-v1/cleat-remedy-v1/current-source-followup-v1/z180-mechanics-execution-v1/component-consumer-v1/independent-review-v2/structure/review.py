"""Final independent architecture/source review of the bounded release fix.

Only source bytes, authentic descriptor-review metadata and definition-only
compilation are inspected. No config, field, admission or reducer is called.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[10]
TARGET = OWN.parents[2]
FIX = TARGET / "review-fix-v2"
PRIOR = TARGET / "independent-review-v1/structure"
REVIEW = TARGET.parent.parent / "z180-mechanics-inputs-v1/independent-review-v2/correctness/receipt.json"
PINS = {
    FIX / "consume.py": "791e39cbdfbf80e6a207ca568898c0347e7f400ac428efa84dc65906a8a8cf92",
    FIX / "test_consume.py": "6828f723f53d1e3d411ce114d352000bd0156c17713c548003a139ac3cc2524c",
    FIX / "verification.json": "0ceea1da4d9c7c4a7b09f896d2fa2b9787c491756d11c95c531f3e7901ce7832",
    TARGET / "consume.py": "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    TARGET / "test_consume.py": "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44",
    TARGET / "verification.json": "fe7cdb509058d116049fef87bf91266378d4dc252b68c9e80b64d9a439ce2286",
    PRIOR / "review.py": "56f03bdf72f7af1f915ce15fdd9c1db0f8ef891583883b328aa584a5aa001b9b",
    PRIOR / "receipt.json": "bacf59799b477aae4b9f5df7cd68bc50af6d8e7f894fec3520b055b33ce74267",
    REVIEW: "acecce87e8b737374f75b896a7875fcdf287649923b641d431edb8a301e49a38",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def compiled_seam(review_metadata):
    """Compile definitions and test context restoration; never authenticate."""
    spec = importlib.util.spec_from_file_location("independent_final_structure_release_fix", FIX / "consume.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    original = wrapper.original()
    original_authenticate, original_release = original.authenticate, original.RELEASE
    wrapped = wrapper.corrected_authenticate(original)
    closure = dict(zip(wrapped.__code__.co_freevars,
                       (cell.cell_contents for cell in wrapped.__closure__), strict=True))
    actual = closure["corrected"]
    function = copy.deepcopy(next(n for n in ast.parse(wrapper.FROZEN.read_bytes()).body
                                  if isinstance(n, ast.FunctionDef) and n.name == "authenticate"))
    needle = ast.dump(ast.parse("review['release'] == RELEASE", mode="eval").body)
    matches = [n for n in ast.walk(function) if isinstance(n, ast.Compare) and ast.dump(n) == needle]
    require(len(matches) == 1, "one original review-release comparator required")
    matches[0].comparators[0] = ast.Name(id="DESCRIPTOR_RELEASE", ctx=ast.Load())
    namespace = {**vars(original), "DESCRIPTOR_RELEASE": dict(wrapper.DESCRIPTOR_RELEASE)}
    tree = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(tree, str(wrapper.FROZEN), "exec"), namespace)  # noqa: S102
    require(actual.__code__ == namespace["authenticate"].__code__,
            "compiled authentication differs beyond the one declared comparator")
    require(actual.__globals__["OWN"] == wrapper.FROZEN
            and actual.__globals__["LOADED_SHA"] == wrapper.FROZEN_SHA
            and actual.__globals__["RELEASE"] is original_release
            and actual.__globals__["DESCRIPTOR_RELEASE"] == review_metadata["release"],
            "original source identity or distinct release contracts differ")
    try:
        with wrapper.corrected_context():
            require(original.authenticate is not original_authenticate
                    and original.RELEASE is original_release, "incorrect scoped correction")
            raise RuntimeError("independent inert restoration probe")
    except RuntimeError as error:
        require(str(error) == "independent inert restoration probe", "unexpected restoration error")
    require(original.authenticate is original_authenticate and original.RELEASE is original_release,
            "authenticate or global field release not restored")
    return {"exact_original_function_plus_one_comparator_code_equal": True,
            "compiler_flags": actual.__code__.co_flags,
            "original_OWN_LOADED_SHA_and_field_RELEASE_object_preserved": True,
            "authentic_descriptor_release_keys_match": True, "exception_restoration_passed": True,
            "authenticate_config_field_admission_or_reducer_called": False}


def check():
    for path, expected in PINS.items():
        require(sha(path) == expected, "frozen final-review input differs: " + relative(path))
    prior = json.loads((PRIOR / "receipt.json").read_bytes())
    inherited = prior["source_sha256"]
    for path, expected in inherited.items():
        require(sha(ROOT / path) == expected, "unaffected v1 source changed: " + path)
    authentic = json.loads(REVIEW.read_bytes())
    require(authentic["schema"] == "eoere_z180_geometry_descriptors_independent_review/v1"
            and authentic["success"] == "independent_z180_descriptor_source_checks_pass"
            and authentic["independent_z180_descriptor_source_checks_pass"] is True,
            "authentic descriptor-review contract differs")
    seam = compiled_seam(authentic)
    evidence = json.loads((FIX / "verification.json").read_bytes())
    require(evidence["readiness"]["genuine_config_supplied"] is False
            and evidence["readiness"]["actual_field_or_admission_consumed"] is False
            and evidence["readiness"]["actual_reducer_or_component_numbers_produced"] is False
            and not any(evidence["release"].values()), "bounded final evidence scope differs")
    pins = {**inherited, **{relative(p): h for p, h in PINS.items()}}
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "source changed during final review: " + path)
    return {
        "schema": "eoere_z180_component_final_independent_structure_review/v2",
        "status": "NO_REMAINING_SUBSTANTIAL_CONFIRMED_FINDINGS_IN_BOUNDED_FINAL_SCOPE",
        "substantial_confirmed_findings": [],
        "source_sha256": {**pins, relative(OWN): sha(OWN)},
        "source_pins_before_after_unchanged": True,
        "new_wrapper_test_verification_bytes": sum(p.stat().st_size for p in PINS if p.parent == FIX),
        "independent_definition_only_compiled_seam_and_restoration": seam,
        "observed_independent_checks_before_receipt_creation": [
            {"command": [".venv/bin/python", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", relative(FIX / "test_consume.py")],
             "exit_code": 0, "result": "15 passed in 0.41s", "scope": "new inert correction controls only"},
            {"command": [".venv/bin/ruff", "check", relative(FIX)],
             "exit_code": 0, "result": "All checks passed!"},
        ],
        "reused_v1_evidence": {
            "receipt": {"path": relative(PRIOR / "receipt.json"), "sha256": PINS[PRIOR / "receipt.json"]},
            "original_39_test_observation": "39 passed in 0.50s in the original bounded review; not rerun or claimed as 39 tests of this corrected wrapper.",
            "reuse_limit": "Only unaffected source/math, 100-axis/partial-layout/seat provenance, original reducer ownership and output reservation review is reused. The original mismatched descriptor-release comparison is superseded by the corrected wrapper and authentic-metadata controls.",
            "original_three_files_and_v1_review_frozen_unchanged": True,
        },
        "corrected_original_defect": {
            "original_path": relative(TARGET / "consume.py"), "original_line": 129,
            "cause": "Descriptor-review release keys differ from mechanics field/output release keys.",
            "fix": "One exact AST comparator now selects DESCRIPTOR_RELEASE; original authentic review bytes and mechanics RELEASE remain unchanged.",
            "remaining_issue": False,
        },
        "architecture_and_ownership_evidence": [
            {"path": relative(FIX / "consume.py"), "lines": [26, 40, 47, 50, 51],
             "observation": "Exact original/wrapper pins and one authenticated AST seam preserve the original function body, original OWN/LOADED_SHA and field RELEASE. Geometry-review release is a separate private namespace constant; no raw receipt is rewritten or relabeled."},
            {"path": relative(FIX / "consume.py"), "lines": [56, 58, 59, 60, 61],
             "observation": "The complete original authentication runs before adding the wrapper source pin and verifying the source closure. Original consume reaches reducers only after this corrected authentication returns."},
            {"path": relative(FIX / "consume.py"), "lines": [66, 69, 70, 72, 74, 78, 83, 88],
             "observation": "All public entrypoints use the original reentrant lock, reject nested correction, patch only authenticate and restore it in context-manager exit. Original source identities are retained throughout."},
            {"path": relative(TARGET / "consume.py"), "lines": [137, 140, 144, 147, 150, 151, 325, 345, 349],
             "observation": "Raw own-pair/state/case/source checks, own gate admission, deferred C/F loading and exclusive output ownership remain original. Definition/AST preparation occurs before reservation; no config, field, gate or reducer intake does."},
        ],
        "reviewer_harness_observation": {
            "initial_result": "A preliminary code-object equality probe failed because its expected compile omitted the wrapper's future-annotations context.",
            "disposition": "Compile the independent expected function in the same annotations context; complete code-object equality passes. This was a reviewer harness difference, not target behavior or a genuine run.",
        },
        "retention": {
            "active": "Corrected wrapper/test/verification and this final review; original consumer and v1 evidence remain frozen dependencies/witnesses. Existing C/F arithmetic, distinct genuine 491653 compiler and own Z180 gate retain their original ownership.",
            "history_boundary": "Preserve the original descriptor-release mismatch and its correction record. Do not treat the original all-pass inert fixture as validation of the authentic geometry-review release shape.",
            "future_entrypoint": "Use review-fix-v2/consume.py with the original CLI arguments after parent freezes the final config and admitted own pair.",
            "failed_attempts": "Original durable STARTED/FAILED output records and retry refusal remain intact; preserve failed attempts. No new genuine result output was created.",
            "compactness": "The 3596-byte wrapper delegates original logic rather than copying numerical implementations; no dependencies, manuals, geometry, operators or raw runs were duplicated or removed.",
        },
        "claim_boundary": {
            "actual_config_pair_field_admission_or_reducer_run": False,
            "CAD_BREP_K_q_solve_or_browser": False,
            "target_v1_peer_docs_or_Git_edits": False,
            "genuine_readiness": "Parent still owns exact final config/source/gate refs and own admitted Z180 pair before genuine consumption.",
            "unadopted_proposal": True, "complete_joint_resistance": None,
            "panel_or_screw_remedy": False,
        },
        "release": evidence["release"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "helper_sha256": sha(OWN), "receipt_sha256": sha(args.out),
                      "substantial_confirmed_findings": 0}))


if __name__ == "__main__":
    main()
