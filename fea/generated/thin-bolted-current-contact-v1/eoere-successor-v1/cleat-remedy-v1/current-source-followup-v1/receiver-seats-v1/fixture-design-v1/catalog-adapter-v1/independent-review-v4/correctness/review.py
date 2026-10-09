"""Narrow v4 preflight/optional-control correctness review; preserve all evidence."""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import runpy
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "verify-v4.py": "7d12b93a566807bdb6ea855f15339bfd11dbc11b7ff12c51e098b25d3d8288b3",
    "verification-v4.json": "d493675b10ed82518371ef23089850114a59025b96007b9f12e50ec207a6367f",
    "controls01/publication-file-inventory-v4.json": "6d35166082919605b1d61684c212e6ff0d5f07620a38b07538dfe4b5f5d438b5",
}
PRIOR = {
    "independent-review-v3/correctness/review.py": "6b199a52a3f7459f056c648c71cb0ecf858c47a835f5e76eb9349c0aad44638b",
    "independent-review-v3/correctness/receipt.json": "76d0c837da31cb1c9595338be2a795035f492c4f16a71102ab75d1ea69ce90e8",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify(pins):
    require(all(sha(ROOT / p) == h for p, h in pins.items()), "changed frozen byte pin")


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def actual_main_early_rejections(method):
    namespace = method["main"].__globals__
    original_controls, original_sha = namespace["actual_main_controls"], namespace["sha"]
    attempts = {"optional_controls": 0, "calculator": 0}
    destination = PACKET / "_independent_v4_preflight_never_created.json"
    require(not os.path.lexists(destination), "fresh non-writing control name")

    def controls():
        attempts["optional_controls"] += 1
        raise AssertionError("controls ran before validation")

    def calculator():
        attempts["calculator"] += 1
        raise AssertionError("calculator ran before validation")

    outcomes = []
    try:
        namespace["actual_main_controls"] = controls
        cases = [
            ("help", ["--help"], 0, ""),
            ("missing_output", [], 2, ""),
            ("unknown_option", ["--out", str(destination), "--unexpected"], 2, ""),
            ("wrong_parent", ["--out", str(OWN.parent / "unused.json")], None, "owned canonical JSON"),
            ("wrong_suffix", ["--out", str(destination.with_suffix(".txt"))], None, "owned canonical JSON"),
            ("occupied_output", ["--out", str(PACKET / "verification-v3.json")], None, "fresh receipt"),
        ]
        for label, argv, code, message in cases:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    method["main"](argv, calculate=calculator, run_main_controls=True)
            except SystemExit as error:
                require(error.code == code, "unexpected parser exit: "+label)
            except ValueError as error:
                require(code is None and message in str(error), "unexpected destination failure: "+label)
            else:
                raise ValueError("early guard accepted: "+label)
            outcomes.append(label)
        namespace["sha"] = lambda path: "0"*64 if Path(path).name == "adapter-v2.py" else original_sha(path)
        try:
            method["main"](["--out", str(destination)], calculate=calculator, run_main_controls=True)
        except ValueError as error:
            require("frozen v2/v3 packet" in str(error), "unrelated source rejection")
            outcomes.append("source_digest_failure")
        else:
            raise ValueError("changed-source control accepted")
    finally:
        namespace["actual_main_controls"], namespace["sha"] = original_controls, original_sha
    require(attempts == {"optional_controls": 0, "calculator": 0}, "preflight calls executed work")
    require(not os.path.lexists(destination), "early rejection created output")
    return {"real_main_early_rejections": outcomes, "optional_control_calls": 0,
            "calculator_calls": 0, "nonwriting_destination_absent": True,
            "source_checksum_failure_is_local_in_memory_control": True}


def main():
    destination = OWN.with_name("receipt.json")
    require(not destination.exists(), "preserve previous review")
    supplemental = {str((PACKET / n).relative_to(ROOT)): h for n, h in (TARGETS | PRIOR).items()}
    verify(supplemental)
    prior = read(PACKET / "independent-review-v3/correctness/receipt.json")
    inherited = read(ROOT / prior["inherited_frozen_pin_map"]["receipt"])["reviewed_sha256"]
    inherited.update(prior["supplemental_reviewed_sha256"])
    require(canonical_sha(inherited) == prior["complete_reviewed_pin_map_canonical_sha256"], "frozen inherited map")
    pins = inherited | supplemental
    inventory = read(PACKET / "controls01/publication-file-inventory-v4.json")
    for name, entry in inventory["files"].items():
        path = str((PACKET / name).relative_to(ROOT))
        require(path not in pins or pins[path] == entry["sha256"], "inventory contradiction")
        pins[path] = entry["sha256"]
        require((ROOT / path).stat().st_size == entry["bytes"], "inventory bytes")
    probe_ref = inventory["active_ignored"]["positive_actual_main_probe"]
    pins[probe_ref["path"]] = supplemental[probe_ref["path"]] = probe_ref["sha256"]
    verify(pins)
    require(sum(e["bytes"] for e in inventory["files"].values())
            == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "inventory total")
    old_tree, tree = (ast.parse((PACKET / f"verify-v{v}.py").read_text()) for v in (3, 4))
    require(ast.dump(function(tree, "compare_replay")) == ast.dump(function(old_tree, "compare_replay")),
            "runtime comparator remains exact v3 source")
    main_node = function(tree, "main")
    kwdefaults = dict(zip((a.arg for a in main_node.args.kwonlyargs), main_node.args.kw_defaults, strict=True))
    require(isinstance(kwdefaults["run_main_controls"], ast.Constant)
            and kwdefaults["run_main_controls"].value is False, "children/negative calls default to no optional controls")
    control_index = next(i for i, n in enumerate(main_node.body)
                         if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "main_control_report" for t in n.targets))
    control_assignment = main_node.body[control_index]
    require(isinstance(control_assignment.value, ast.IfExp)
            and isinstance(control_assignment.value.test, ast.Name)
            and control_assignment.value.test.id == "run_main_controls", "optional controls conditional inside main")
    require(any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Name) and n.value.func.id == "compare_replay"
                for n in main_node.body[:control_index]), "strict replay gate precedes optional controls")
    last = tree.body[-1]
    require(isinstance(last, ast.If) and len(last.body) == 1 and isinstance(last.body[0], ast.Expr), "simple CLI invocation")
    invocation = last.body[0].value
    require(isinstance(invocation, ast.Call) and isinstance(invocation.func, ast.Name)
            and invocation.func.id == "main" and not invocation.args
            and len(invocation.keywords) == 1 and invocation.keywords[0].arg == "run_main_controls"
            and isinstance(invocation.keywords[0].value, ast.Constant)
            and invocation.keywords[0].value.value is True, "CLI passes only control flag, without evaluating controls")
    method = runpy.run_path(str(PACKET / "verify-v4.py"))
    shared_run_path, shared_version = runpy.run_path, sys.version
    preflight = method["entrypoint_preflight_controls"]()
    early = actual_main_early_rejections(method)
    saved = read(PACKET / "result-v3.json")
    for fields in (("generic_live_execution_python",), ("wrapper_live_execution_python",), method["LIVE_RUNTIME_FIELDS"]):
        value = {k: copy.deepcopy(v) for k, v in saved.items() if k != "drawing"}
        for field in fields:
            value["runtime_reproduction"][field] = "synthetic unchanged v4 comparator control"
        untouched = copy.deepcopy(value)
        method["compare_replay"](value, saved)
        require(value == untouched, "runtime input not mutated")
    receipt, probe = read(PACKET / "verification-v4.json"), read(ROOT / probe_ref["path"])
    require(receipt["verification_method_sha256"] == TARGETS["verify-v4.py"]
            and receipt["main_controls_run_after_argument_destination_source_and_normal_checks"] is True,
            "receipt method/order claims")
    require(receipt["recorded_runtime_provenance"] == probe["recorded_runtime_provenance"]
            == saved["runtime_reproduction"], "saved runtime provenance exact")
    require(probe["actual_main_controls"] is None and probe["passed"], "positive child uses default nonrecursive mode")
    require(all(probe["live_runtime_provenance"][f] != probe["recorded_runtime_provenance"][f]
                for f in method["LIVE_RUNTIME_FIELDS"]), "positive probe exercises alternate live runtime")
    report = receipt["actual_main_controls"]
    require(report["positive_probe_receipt_sha256"] == probe_ref["sha256"]
            and report["entrypoint_preflight_controls"] == preflight
            and len(report["nonruntime_actual_main_controls_rejected"]) == 8
            and report["second_interpreter_execution_claimed"] is False, "control report matches scope and observed probe")
    old_receipt = read(PACKET / "verification-v3.json")
    for field in ("reused_independent_decimal_checks", "reused_output_guard_controls", "runtime_reproduction_controls",
                  "release", "normalized_wrapper_comparison_paths_only"):
        require(receipt[field] == old_receipt[field], "unchanged v3 evidence/claims: "+field)
    require(all(v is False for v in receipt["release"].values()), "no release")
    require(runpy.run_path is shared_run_path and sys.version == shared_version, "shared runtime unchanged")
    require(not ({"cadquery", "OCP", "numpy", "scipy"} & set(sys.modules)), "no native/numerical imports")
    verify(pins)
    result = {"schema": "catalog_adapter_verifier_v4_independent_correctness_review/v1", "findings": [],
              "target_sha256": TARGETS, "supplemental_reviewed_sha256": dict(sorted(supplemental.items())),
              "inherited_pin_map_receipt": {"path": str((PACKET / "independent-review-v3/correctness/receipt.json").relative_to(ROOT)),
                                            "sha256": PRIOR["independent-review-v3/correctness/receipt.json"]},
              "all_reviewed_bytes_unchanged_before_after": True, "reviewed_files": len(pins),
              "complete_reviewed_pin_map_canonical_sha256": canonical_sha(pins),
              "actual_entrypoint_readonly_audits": preflight, "independent_actual_main_early_guard_checks": early,
              "optional_controls_are_after_normal_checks_and_default_off": True,
              "runtime_comparator_AST_exact_to_reviewed_v3": True, "three_runtime_leaf_combinations_passed": True,
              "actual_main_positive_probe_authenticated": probe_ref, "child_probe_controls_disabled": True,
              "unchanged_math_and_normalization_evidence_reused": True, "review_helper_sha256": sha(OWN),
              "release": saved["release"],
              "limits": [
                  "Stdlib/source/AST/JSON/byte hashing and read-only preflight controls only. Three real __main__ audit children ran; positive control-producing main, output guard fixtures and numerical studies are reused as frozen evidence, not rerun.",
                  "Seven actual-main early rejects use in-memory spies, including a local mocked source-checksum failure. No target/source bytes or shared runpy/sys state are modified and no control receipts are created.",
                  "All math, producer/result/SVG and strict runtime provenance boundaries remain frozen. Synthetic runtime metadata is not a second interpreter execution or product/fixture qualification.",
                  "Current Z200/100 bolts/66 screws/forces/HOLD remain unchanged, Z180 unadopted, error exceedances retained and panel remedies stopped. No native/CAD/FEA/browser/physical work or strength/physical acceptance."],
              }
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(destination), "helper_sha256": sha(OWN),
                      "reviewed_files": len(pins), "actual_entrypoint_cases": 3, "independent_early_rejections": 7,
                      "findings": []}))


if __name__ == "__main__":
    main()
