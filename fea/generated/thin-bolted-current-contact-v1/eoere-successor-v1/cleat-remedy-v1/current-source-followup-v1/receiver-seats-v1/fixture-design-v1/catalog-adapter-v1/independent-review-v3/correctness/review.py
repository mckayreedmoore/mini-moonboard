"""Bounded v3 verifier review; reuse frozen math and replay only its real gate."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "verify-v3.py": "354bac725ebd23693bb835da073b8b503118df471cdded27e271dc3cd38f009e",
    "verification-v3.json": "2b484b62786d0c919aa21a0560cff078e2dfd2182ea5c070b5a32d9b920746da",
    "controls01/publication-file-inventory-v3.json": "df6b43be7214dd73b67284df0b45bdf6a7bd4dbeb9eb54a2f459c22447a73230",
}
PRIOR = {
    "independent-review-v2/correctness/review.py": "3a1bfdbc265754b05337a85adecdd8a7242985e0ca63f261bc4cd88bfa5dc214",
    "independent-review-v2/correctness/receipt.json": "2fa20fccddc98183caac46b5f6a80a114881639d067d5ae524749bedebb38b31",
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
    require(all(sha(ROOT / p) == h for p, h in pins.items()), "changed frozen bytes")


def main_gate(verifier):
    tree = ast.parse((PACKET / "verify-v3.py").read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    begin = next(i for i, n in enumerate(main.body)
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "untouched" for t in n.targets))
    statements = main.body[begin:begin+3]
    require(isinstance(statements[1], ast.Expr) and isinstance(statements[1].value, ast.Call)
            and isinstance(statements[1].value.func, ast.Name) and statements[1].value.func.id == "compare_replay",
            "real main invokes corrected comparator")
    code = compile(ast.Module(body=statements, type_ignores=[]), str(PACKET / "verify-v3.py"), "exec")

    def gate(live, saved):
        namespace = {"live": live, "saved": saved, "copy": copy,
                     "compare_replay": verifier["compare_replay"], "require": verifier["require"]}
        exec(code, namespace)  # noqa: S102

    return gate


def alternate_producer(wrapper):
    namespace = wrapper["method_with_runtime_join"].__globals__
    original_runpy, original_sys, original_run_path = namespace["runpy"], namespace["sys"], runpy.run_path
    generic_path = PACKET.parent / "design.py"
    alternate = "3.12.99 (independent v3 synthetic metadata; same interpreter)"

    def loader(path, *args, **kwargs):
        loaded = original_run_path(path, *args, **kwargs)
        if Path(path).resolve() == generic_path:
            original = loaded["evaluate"]

            def evaluate():
                inp, live, shapes = original()
                live["execution"]["python"] = alternate
                return inp, live, shapes

            loaded["evaluate"] = evaluate
        return loaded

    try:
        namespace["runpy"] = SimpleNamespace(run_path=loader)
        namespace["sys"] = SimpleNamespace(version=alternate)
        live, _ = wrapper["calculate"]()
    finally:
        namespace["runpy"], namespace["sys"] = original_runpy, original_sys
    require(runpy.run_path is original_run_path, "shared runpy unchanged")
    return live, alternate


def main():
    destination = OWN.with_name("receipt.json")
    require(not destination.exists(), "preserve prior review")
    supplemental = {str((PACKET / n).relative_to(ROOT)): h for n, h in (TARGETS | PRIOR).items()}
    verify(supplemental)
    prior = read(PACKET / "independent-review-v2/correctness/receipt.json")
    pins = dict(prior["reviewed_sha256"])
    pins.update(supplemental)
    inventory = read(PACKET / "controls01/publication-file-inventory-v3.json")
    for name, entry in inventory["files"].items():
        path = str((PACKET / name).relative_to(ROOT))
        require(path not in pins or pins[path] == entry["sha256"], "inventory pin contradiction")
        if path not in pins:
            supplemental[path] = entry["sha256"]
        pins[path] = entry["sha256"]
        require((ROOT / path).stat().st_size == entry["bytes"], "inventory byte count")
    probe_ref = inventory["active_ignored"]["positive_actual_main_probe"]
    pins[probe_ref["path"]] = supplemental[probe_ref["path"]] = probe_ref["sha256"]
    verify(pins)
    require(sum(e["bytes"] for e in inventory["files"].values())
            == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "inventory total")
    require(sum(inventory["files"][n]["bytes"] for n in inventory["corrected_verification_files"])
            == inventory["new_final_verifier_and_receipt_bytes"], "final verifier bytes")
    verifier = runpy.run_path(str(PACKET / "verify-v3.py"))
    wrapper = runpy.run_path(str(PACKET / "adapter-v2.py"))
    saved = read(PACKET / "result-v3.json")
    current, method = wrapper["calculate"]()
    gate = main_gate(verifier)
    gate(current, saved)
    live, alternate = alternate_producer(wrapper)
    untouched = copy.deepcopy(live)
    gate(live, saved)
    require(live == untouched, "gate preserves actual live provenance")
    require({k: v for k, v in live.items() if k != "runtime_reproduction"}
            == {k: v for k, v in current.items() if k != "runtime_reproduction"}, "alternate producer keeps math/source exact")
    fields = verifier["LIVE_RUNTIME_FIELDS"]
    require(fields == ("generic_live_execution_python", "wrapper_live_execution_python"), "only two allowed text leaves")
    require(all(live["runtime_reproduction"][f] == alternate for f in fields)
            and live["runtime_reproduction"]["generic_recorded_execution_python"]
            == saved["runtime_reproduction"]["generic_recorded_execution_python"], "strict saved and separate observed runtimes")
    positive = []
    for combination in ((fields[0],), (fields[1],), fields):
        value = copy.deepcopy(current)
        for field in combination:
            value["runtime_reproduction"][field] = alternate
        gate(value, saved)
        positive.append(list(combination))
    rejected = []
    mutations = [
        ("saved_generic_runtime", lambda x: x["runtime_reproduction"].__setitem__("generic_recorded_execution_python", alternate)),
        ("runtime_invariant", lambda x: x["runtime_reproduction"].__setitem__("original_v1_result_arithmetic_source_and_guards_exact", False)),
        ("runtime_command", lambda x: x["runtime_reproduction"].__setitem__("original_v1_reproduction_command", "other")),
        ("extra_runtime_leaf", lambda x: x["runtime_reproduction"].__setitem__("extra", True)),
        ("missing_runtime_leaf", lambda x: x["runtime_reproduction"].pop("runtime_change_is_not_a_method_tool_or_physical_qualification")),
        ("arithmetic", lambda x: x.__setitem__("derived_relative_bound_under_declared_unobserved_conditions_mm", 1.5)),
        ("source_pin", lambda x: x["source_sha256"].__setitem__(next(iter(x["source_sha256"])), "0"*64)),
        ("release", lambda x: x["release"].__setitem__("fabrication", True)),
        ("execution_flag", lambda x: x["execution"].__setitem__("new_CAD_BREP_native_mechanics_mesh_or_physical_run", True)),
        ("extra_top_level_field", lambda x: x.__setitem__("extra", True)),
    ]
    for field in fields:
        for wrong in (None, 3, [], True):
            mutations.append((f"nontext_{field}_{type(wrong).__name__}",
                              lambda x, f=field, v=wrong: x["runtime_reproduction"].__setitem__(f, v)))
    for label, mutate in mutations:
        changed = copy.deepcopy(live)
        mutate(changed)
        try:
            gate(changed, saved)
        except (ValueError, KeyError):
            rejected.append(label)
        else:
            raise ValueError("accepted nonruntime change: "+label)
    receipt = read(PACKET / "verification-v3.json")
    probe = read(ROOT / probe_ref["path"])
    require(receipt["verification_method_sha256"] == TARGETS["verify-v3.py"]
            and receipt["normalized_wrapper_comparison_paths_only"]
            == ["/runtime_reproduction/"+f for f in fields], "receipt method and comparator paths exact")
    require(probe["passed"] and receipt["passed"] and probe["recorded_runtime_provenance"]
            == receipt["recorded_runtime_provenance"] == saved["runtime_reproduction"], "saved positive probe provenance")
    require(all(isinstance(probe["live_runtime_provenance"][f], str)
                and probe["live_runtime_provenance"][f] != probe["recorded_runtime_provenance"][f] for f in fields),
            "actual-main positive probe exercised both changed live strings")
    require(probe["live_runtime_provenance"]["generic_recorded_execution_python"]
            == saved["runtime_reproduction"]["generic_recorded_execution_python"], "actual-main recorded generic runtime strict")
    report = receipt["actual_main_controls"]
    require(report["positive_probe_receipt_sha256"] == probe_ref["sha256"]
            and len(report["nonruntime_actual_main_controls_rejected"]) == 8
            and report["second_interpreter_execution_claimed"] is False, "actual-main report binds observed probe and scope")
    require(method["drawing"](live) == (PACKET / "result-v3.svg").read_bytes(), "runtime does not alter drawing")
    require(all(v is False for v in receipt["release"].values())
            and receipt["release"] == saved["release"], "no changed release")
    require(not ({"cadquery", "OCP", "numpy", "scipy"} & set(sys.modules)), "no native/numerical imports")
    verify(pins)
    result = {"schema": "catalog_adapter_verifier_v3_independent_correctness_review/v1", "findings": [],
              "target_sha256": TARGETS, "supplemental_reviewed_sha256": dict(sorted(supplemental.items())),
              "inherited_frozen_pin_map": {"receipt": str((PACKET / "independent-review-v2/correctness/receipt.json").relative_to(ROOT)),
                                           "sha256": PRIOR["independent-review-v2/correctness/receipt.json"],
                                           "field": "reviewed_sha256"},
              "all_unchanged_before_after": True, "reviewed_files": len(pins),
              "complete_reviewed_pin_map_canonical_sha256": canonical_sha(pins),
              "prior_P2_corrected": True, "actual_main_gate_alternate_producer_replay_passed": True,
              "independent_positive_runtime_leaf_combinations": positive, "independent_rejected_gate_controls": rejected,
              "live_provenance_not_mutated": True, "saved_generic_runtime_strict": True,
              "saved_real_main_positive_probe_authenticated": probe_ref, "reported_actual_main_negative_controls": 8,
              "math_evidence_reused_without_independent_recalculation": True,
              "original_derived_relative_bound_mm": saved["derived_relative_bound_under_declared_unobserved_conditions_mm"],
              "review_helper_sha256": sha(OWN), "release": saved["release"],
              "limits": [
                  "Stdlib source/AST/JSON/byte-hash review and local synthetic runtime metadata controls only. Real verifier main/child/output guard fixtures are reused as authenticated saved evidence, not rerun by this reviewer.",
                  "Producer and real admission gate are replayed with synthetic alternate runtime text, not a second interpreter. Shared runpy/sys modules are not changed; only the freshly loaded wrapper's local references are rebound and restored.",
                  "Frozen v1 math/source and v2 scope evidence are reused. No CAD/BREP/native/FEA/global/browser/physical work, product/fixture qualification or shared edits.",
                  "All generic error exceedances remain; current Z200/100 bolts/66 screws/HOLD/forces remain unchanged, Z180 unadopted and panel remedies stopped. No budget relaxation, strength or physical acceptance."],
              }
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(destination), "helper_sha256": sha(OWN),
                      "reviewed_files": len(pins), "negative_controls": len(rejected), "findings": []}))


if __name__ == "__main__":
    main()
