"""Frozen v2 runtime/namespace review with a read-only production-gate replay."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "adapter-v2.py": "dae93a7011242ad3878f47040cbf3af9cd224d7077eb503621a8816d55cd4014",
    "result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    "result-v3.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify-v2.py": "2f01212e390c5ea53a23821ecb6042e82fe0c9b64fd1fc54341c0944b3c0757f",
    "verification-v2.json": "286c4df35620d46d4a3276904ffb6f4997c5a0cf57f8c49b6e113a0f9231410e",
    "controls01/publication-file-inventory-v2.json": "e0f7e412e4f8a64385dc564d7793c8b3b9cdf6fbe256c561c7c8eb9f1497f514",
}
PRIOR = {
    "independent-review-v1/correctness/review.py": "492362cb3246bf799bc8b7c9b38fd929bf5954e1f33f1a0acc87b5fcbb451a78",
    "independent-review-v1/correctness/receipt.json": "9c650931a7de6da7596a21e362fda980868a28042df8142bfb6cedf3607b2111",
}
FACTORY = PACKET.parent.parent / "hardware-followup-v1/factory-guide-sources-v1.json"
FACTORY_SHA = "3e0d553d76fa076764c06a393554c98e297b597fee8d339fd493053ea057e429"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(pins):
    require(all(sha(ROOT / p) == h for p, h in pins.items()), "changed frozen source/target")


def close(a, b, message):
    require(math.isclose(a, b, abs_tol=1e-10, rel_tol=0), message)


def factory_audit(facts, generic_input, bit_facts):
    for name in ("Milescraft_1307", "Big_Gator_STD1000DGNP"):
        f = facts["sources"][name]["facts"]
        lo, hi = f["listed_nominal_guide_range_in"]
        close((hi-lo)/f["listed_increment_in"]+1, f["guide_hole_count"], "guide interval census")
    require(facts["sources"]["Milescraft_1307"]["facts"]["explicit_13p32_guide_listed"] is True
            and facts["sources"]["Big_Gator_STD1000DGNP"]["facts"]["includes_13p32"] is False,
            "distinct product ranges")
    require(all(v is None for v in facts["sources"]["Milescraft_1307"]["not_established_by_read_page"].values()),
            "no unobserved factory geometry substituted")
    d = generic_input["dimensions_mm"]
    pair = 2*d["member_thickness"]+d["matched_stack_deviation_max"]+d["breakout_travel"]
    reach = facts["paired_stack_reach_envelope"]
    close(reach["maximum_pair_plus_breakout_mm"], pair, "pair/breakout reference")
    close(pair+d["free_chuck_to_cap_axial_gap_min"], 85.05, "projection additive relation")
    close(reach["conditional_maximum_offset_for_120mm_full_top_exit_reference_mm"],
          bit_facts["catalog_NL_mm"]-pair, "conditional full-top reference offset")
    require(reach["guide_top_to_wood_offset_mm"] is None, "actual guide height unknown")
    size = facts["diameter_scope"]
    close(size["nominal_13p32_exact_mm"], 13/32*25.4, "exact fractional nominal")
    close(size["printed_difference_mm"], bit_facts["catalog_diameter_mm"]-13/32*25.4, "printed rounding comparison")
    require(all(v is False for v in facts["release"].values())
            and all(v == "" for v in facts["actual_observations"].values()), "factory actuals/releases")
    require(facts["preserved"]["current_forces_transferred_to_Z180"] is False
            and facts["preserved"]["panel_screw_remedies_resumed"] is False, "factory scope preserved")
    return {"pair_plus_breakout_mm": pair, "projection_additive_reference_mm": pair+2,
            "nominal_full_top_offset_comparison_mm": 120-pair, "actual_guide_geometry_known": False}


def runtime_audit(wrapper, verifier, saved, live):
    generic_path = PACKET.parent / "design.py"
    recorded = {k: v for k, v in read(PACKET.parent / "result.json").items() if k != "drawing"}
    changed = copy.deepcopy(recorded)
    alternate = "3.12.99 (independent synthetic runtime metadata; not another interpreter run)"
    changed["execution"]["python"] = alternate
    before = copy.deepcopy(changed)
    require(wrapper["normalized_generic"](changed, recorded) == recorded and changed == before,
            "runtime-only normalization and input immutability")
    rejected = []
    for label, mutate in [
        ("arithmetic", lambda x: x["pointwise_error_and_reach_budget"].__setitem__("relative_bore_screw_bound_mm", 1.6)),
        ("source_digest", lambda x: x["source_sha256"].__setitem__(next(iter(x["source_sha256"])), "0"*64)),
        ("native_execution_flag", lambda x: x["execution"].__setitem__("native_BREP_CAD_mesh_FEA_global_force_or_physical_execution", True)),
        ("extra_nested_field", lambda x: x["execution"].__setitem__("extra", True)),
        ("missing_nested_field", lambda x: x["execution"].pop("reproduce")),
        ("handed_axis", lambda x: x["four_station_coordinate_joins"][0]["fixture_entry_uvw_mm"].__setitem__(0, -1)),
        ("release", lambda x: x["release"].__setitem__("physical_operation", True)),
    ]:
        bad = copy.deepcopy(changed)
        mutate(bad)
        try:
            wrapper["normalized_generic"](bad, recorded)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("nonruntime normalization: "+label)
    original_run_path = runpy.run_path
    namespace = wrapper["method_with_runtime_join"].__globals__
    original_runpy, original_sys = namespace["runpy"], namespace["sys"]

    def alternate_loader(path, *args, **kwargs):
        loaded = original_run_path(path, *args, **kwargs)
        if Path(path).resolve() == generic_path:
            original_evaluate = loaded["evaluate"]

            def evaluate():
                inp, replay, shapes = original_evaluate()
                replay["execution"]["python"] = alternate
                return inp, replay, shapes

            loaded["evaluate"] = evaluate
        return loaded

    try:
        namespace["runpy"] = SimpleNamespace(run_path=alternate_loader)
        namespace["sys"] = SimpleNamespace(version=alternate)
        alternative, old = wrapper["calculate"]()
        require({k: v for k, v in alternative.items() if k != "runtime_reproduction"}
                == {k: v for k, v in live.items() if k != "runtime_reproduction"},
                "synthetic runtime leaves all nonruntime results exact")
        require(alternative["runtime_reproduction"]["generic_recorded_execution_python"] == recorded["execution"]["python"]
                and alternative["runtime_reproduction"]["generic_live_execution_python"] == alternate
                and alternative["runtime_reproduction"]["wrapper_live_execution_python"] == alternate,
                "saved/live runtime provenance separated")
        require(old["load"].__globals__["runpy"] is not runpy, "proxy belongs only to local frozen-module instance")
    finally:
        namespace["runpy"], namespace["sys"] = original_runpy, original_sys
    require(runpy.run_path is original_run_path and namespace["runpy"] is original_runpy
            and namespace["sys"] is original_sys, "shared/local runtime references restored")
    first, second = wrapper["method_with_runtime_join"]({}), wrapper["method_with_runtime_join"]({})
    require(first["load"].__globals__ is not second["load"].__globals__
            and first["load"].__globals__["runpy"] is not second["load"].__globals__["runpy"],
            "separate wrapper calls have independent adapter namespaces")
    # Replay the actual verifier admission statement only. This stops before
    # any peer-review-folder reads, output guard fixtures or receipt writes.
    tree = ast.parse((PACKET / "verify-v2.py").read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    gates = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
             and any(isinstance(a, ast.Constant) and a.value == "v2 wrapper exact scalar/source replay"
                     for a in n.value.args)]
    require(len(gates) == 1, "exact production verifier gate identified")
    gate = compile(ast.Module(body=gates, type_ignores=[]), str(PACKET / "verify-v2.py"), "exec")
    exec(gate, {"require": verifier["require"], "live": live, "saved": saved})  # noqa: S102
    try:
        exec(gate, {"require": verifier["require"], "live": alternative, "saved": saved})  # noqa: S102
    except ValueError as error:
        reproduction = {"production_statement_line": gates[0].lineno, "same_runtime_replay_passed": True,
                        "alternate_runtime_producer_succeeded": True, "all_nonruntime_fields_exact": True,
                        "alternate_runtime_verifier_gate_rejected": str(error),
                        "only_changed_top_level_field": "runtime_reproduction",
                        "synthetic_metadata_only_not_second_interpreter_execution": True}
    else:
        raise ValueError("frozen verifier regression no longer reproduces")
    return {"independent_nonruntime_controls_rejected": rejected,
            "runtime_only_positive_control": True, "normalizer_input_immutable": True,
            "shared_runpy_unchanged_and_local_namespaces_isolated": True,
            "confirmed_verifier_regression": reproduction}


def main():
    destination = OWN.with_name("receipt.json")
    require(not destination.exists(), "preserve earlier receipt")
    saved = read(PACKET / "result-v3.json")
    inventory = read(PACKET / "controls01/publication-file-inventory-v2.json")
    pins = dict(saved["source_sha256"])
    pins.update({str((PACKET / n).relative_to(ROOT)): h for n, h in (TARGETS | PRIOR).items()})
    pins.update({str((PACKET / n).relative_to(ROOT)): r["sha256"] for n, r in inventory["files"].items()})
    pins[str(FACTORY.relative_to(ROOT))] = FACTORY_SHA
    verify(pins)
    for name, row in inventory["files"].items():
        require((PACKET / name).stat().st_size == row["bytes"], "publication inventory byte count")
    require(sum(r["bytes"] for r in inventory["files"].values())
            == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "publication inventory total")
    require(sum(inventory["files"][n]["bytes"] for n in inventory["corrected_final_files"])
            == inventory["new_corrected_final_file_bytes"], "new v2 published byte count")
    wrapper = runpy.run_path(str(PACKET / "adapter-v2.py"))
    verifier = runpy.run_path(str(PACKET / "verify-v2.py"))
    shared_run_path = runpy.run_path
    live, method = wrapper["calculate"]()
    require(live == {k: v for k, v in saved.items() if k != "drawing"}, "actual-runtime source replay")
    require(method["drawing"](live) == (PACKET / "result-v3.svg").read_bytes()
            == (PACKET / "result-v2.svg").read_bytes(), "frozen v1 SVG byte identity")
    previous = read(PACKET / "result-v2.json")
    normalized = copy.deepcopy(live)
    normalized.pop("runtime_reproduction")
    normalized["source_sha256"], normalized["source_pin_count"] = previous["source_sha256"], previous["source_pin_count"]
    normalized["execution"]["reproduce"] = previous["execution"]["reproduce"]
    require(normalized == {k: v for k, v in previous.items() if k != "drawing"}, "only declared v2 provenance changes")
    _, facts, generic_input, generic, _, _, _ = method["load"]()
    prior = runpy.run_path(str(PACKET / "independent-review-v1/correctness/review.py"))
    math_audit = prior["audit"](read(PACKET / "inputs.json"), facts, generic_input, generic, saved)
    factory = read(FACTORY)
    verify(factory["source_sha256"])
    factory_checks = factory_audit(factory, generic_input, facts["sources"]["FISCH_pen_drill"]["facts"])
    runtime = runtime_audit(wrapper, verifier, saved, live)
    saved_controls = verifier["runtime_controls"](wrapper, live)
    require(len(saved_controls["nonruntime_controls_rejected"]) == 5, "reported runtime controls replay")
    require(runpy.run_path is shared_run_path, "shared runpy remained unchanged")
    require(not ({"cadquery", "OCP", "numpy", "scipy"} & set(sys.modules)), "source-only imports")
    verify(pins)
    receipt = {"schema": "catalog_adapter_v2_independent_correctness_review/v1",
               "findings": [{"severity": "P2", "file": str((PACKET / "verify-v2.py").relative_to(ROOT)),
                             "line": 128, "title": "Keep live runtime provenance out of the saved-result equality gate",
                             "impact": "A different Python build's valid producer replay changes only live runtime provenance, but the verifier rejects it before its positive runtime controls. This reintroduces the runtime-only reproducibility failure the v2 wrapper removes.",
                             "fix": "Compare all non-runtime result fields exactly. Validate runtime-block invariant and saved-runtime fields separately, record current live runtimes separately in the new receipt, and add this top-level verifier gate to the alternate-runtime positive control."}],
               "target_sha256": TARGETS, "target_source_inventory_and_own_prior_files_rehashed": len(pins),
               "all_reviewed_bytes_unchanged_before_after": True,
               "reviewed_sha256": dict(sorted(pins.items())), "exact_same_runtime_scalar_and_SVG_replay": True,
               "reused_frozen_v1_independent_math_audit": math_audit, "factory_source_arithmetic": factory_checks,
               "independent_runtime_namespace_checks": runtime, "reported_seven_runtime_controls_replayed": saved_controls,
               "publication_inventory_files_and_bytes_exact": True, "review_helper_sha256": sha(OWN),
               "limits": [
                   "Read-only stdlib/source/JSON/byte hashing and local namespace/synthetic metadata controls. No native/CAD/BREP/FEA/global/physical/browser/site work or shared edits.",
                   "Different runtime strings are synthetic metadata, not execution on a second interpreter. Only the actual verifier admission AST statement is replayed; verifier main and output guard fixtures are not run.",
                   "Frozen v1 math and source-bound finished-solid evidence are reused. Manufacturer source-page facts and actual guide dimensions, product/fixture fit, chip clearing, workholding and achieved tolerances are not regenerated or qualified.",
                   "Current Z200/100 bolts/66 screws/HOLD/forces remain unchanged, Z180 unadopted, panel remedies stopped. Generic error allowances remain unmet; full-cap NL deficit remains distinct from a justified lower outlet. No budget relaxation, strength or physical acceptance."],
               "release": saved["release"]}
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(destination), "helper_sha256": sha(OWN),
                      "reviewed_pins": len(pins), "findings": [{"severity": "P2", "line": 128}]}))


if __name__ == "__main__":
    main()
