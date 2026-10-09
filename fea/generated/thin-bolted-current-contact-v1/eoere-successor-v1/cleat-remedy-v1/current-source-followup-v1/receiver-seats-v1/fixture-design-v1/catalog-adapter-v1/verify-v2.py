"""Verify runtime-only comparison normalization and unchanged v1 arithmetic."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import runpy
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "adapter-v2.py": "dae93a7011242ad3878f47040cbf3af9cd224d7077eb503621a8816d55cd4014",
    "result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    "result-v3.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
}
REVIEWS = {
    "correctness": "9c650931a7de6da7596a21e362fda980868a28042df8142bfb6cedf3607b2111",
    "testing": "e71cae8af9660a4d7b857105a75dc572039a697a78481d74c1907ef211ac5ac8",
    "structure": "af283d3fe442175ee9bd37fb0aba25e701134dc142d46738b8adeed792587b19",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_controls(method, live):
    generic_path = HERE.parent / "design.py"
    recorded = json.loads((HERE.parent / "result.json").read_bytes())
    recorded = {k: v for k, v in recorded.items() if k != "drawing"}
    alternate = "3.12.99 (synthetic different supported-minor build text for a metadata control)"
    changed = copy.deepcopy(recorded)
    changed["execution"]["python"] = alternate
    untouched = copy.deepcopy(changed)
    require(method["normalized_generic"](changed, recorded) == recorded and changed == untouched,
            "runtime-only positive control or input immutability")
    rejected = []
    for label in ("relative_budget", "execution_flag", "source_pin", "extra_execution_field"):
        bad = copy.deepcopy(changed)
        if label == "relative_budget":
            bad["pointwise_error_and_reach_budget"]["relative_bore_screw_bound_mm"] += .001
        elif label == "execution_flag":
            bad["execution"]["native_BREP_CAD_mesh_FEA_global_force_or_physical_execution"] = True
        elif label == "source_pin":
            key = next(iter(bad["source_sha256"]))
            bad["source_sha256"][key] = "0"*64
        else:
            bad["execution"]["unexpected_control_field"] = True
        try:
            method["normalized_generic"](bad, recorded)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("normalized non-runtime change: " + label)
    # Exercise the actual production interception using a local module-loader
    # reference. No monkeypatch to shared runpy.run_path or a source file.
    globals_ = method["method_with_runtime_join"].__globals__
    original_module = globals_["runpy"]
    original_run_path = runpy.run_path

    def simulated_loader(budget_change=False):
        def load(path, *args, **kwargs):
            module = original_run_path(path, *args, **kwargs)
            if Path(path).resolve() == generic_path:
                evaluate = module["evaluate"]

                def different_runtime():
                    inp, replay, shapes = evaluate()
                    replay["execution"]["python"] = alternate
                    if budget_change:
                        replay["pointwise_error_and_reach_budget"]["relative_bore_screw_bound_mm"] += .001
                    return inp, replay, shapes

                module["evaluate"] = different_runtime
            return module
        return SimpleNamespace(run_path=load)

    try:
        globals_["runpy"] = simulated_loader()
        alternative, _ = method["calculate"]()
        require(alternative["runtime_reproduction"]["generic_live_execution_python"] == alternate,
                "alternate runtime provenance lost")
        require({k: v for k, v in alternative.items() if k != "runtime_reproduction"}
                == {k: v for k, v in live.items() if k != "runtime_reproduction"},
                "alternate metadata changed arithmetic/source/guard output")
        globals_["runpy"] = simulated_loader(budget_change=True)
        try:
            method["calculate"]()
        except ValueError:
            rejected.append("production_loader_rejects_relative_budget_change")
        else:
            raise ValueError("production loader normalized an arithmetic difference")
    finally:
        globals_["runpy"] = original_module
    require(runpy.run_path is original_run_path and globals_["runpy"] is original_module,
            "ambient runpy mutation or local reference not restored")
    return {"runtime_only_positive_control": True, "normalizer_does_not_mutate_its_input": True,
            "synthetic_runtime_production_loader_control": True,
            "synthetic_runtime_is_not_an_observed_second_interpreter": True,
            "nonruntime_controls_rejected": rejected,
            "shared_runpy_module_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "owned canonical JSON receipt required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "fresh receipt required")
    require(all(sha(HERE / n) == h for n, h in EXPECTED.items()), "frozen v2 wrapper/result/drawing differ")
    reviews = {str(p.relative_to(ROOT)): sha(p) for p in (HERE / "independent-review-v1").glob("*/*") if p.is_file()}
    for name, digest in REVIEWS.items():
        require(sha(HERE / "independent-review-v1" / name / "receipt.json") == digest, "original v1 review changed")
    method = runpy.run_path(str(HERE / "adapter-v2.py"))
    saved = json.loads((HERE / "result-v3.json").read_bytes())
    live, old = method["calculate"]()
    require(live == {k: v for k, v in saved.items() if k != "drawing"}, "v2 wrapper exact scalar/source replay")
    require(hashlib.sha256(old["drawing"](live)).hexdigest() == saved["drawing"]["sha256"], "unchanged v1 SVG bytes")
    decimal_helper = runpy.run_path(str(HERE / "verify.py"))["decimal_corners"]
    decimal = decimal_helper(saved)
    runtime = runtime_controls(method, live)
    guard = runpy.run_path(str(HERE.parent / "verify.py"))["guard_checks"]
    guard.__globals__["HERE"] = HERE
    (HERE / "controls01").mkdir(exist_ok=True)
    output_controls = guard(old["output_paths"])
    old["verify"](saved["source_sha256"])
    require(all(sha(HERE / n) == h for n, h in EXPECTED.items()), "v2 packet changed during checks")
    require(all(sha(HERE / n) == h for n, h in method["PREVIOUS"].items()), "v1 packet changed during checks")
    require(all(sha(ROOT / p) == h for p, h in reviews.items()), "v1 reviews changed during checks")
    require(all(v is False for v in saved["release"].values())
            and all(v == "" for v in saved["actual_observations"].values()), "release or actual observation changed")
    result = {"schema": "eoere_Z180_catalog_adapter_runtime_reproduction_verification/v2", "passed": True,
        "frozen_v2_wrapper_result_drawing_sha256": EXPECTED, "frozen_v1_six_file_sha256": method["PREVIOUS"],
        "preserved_v1_review_sha256": reviews, "source_pin_count": saved["source_pin_count"],
        "runtime_reproduction_controls": runtime, "runtime_provenance": saved["runtime_reproduction"],
        "reused_independent_decimal_checks": decimal, "reused_output_guard_controls": output_controls,
        "v1_scalar_source_and_guard_outputs_exact": True, "v1_drawing_bytes_exact": True,
        "verification_method_sha256": sha(OWN), "all_sources_packets_and_v1_reviews_unchanged": True,
        "limits": ["Only generic execution.python is normalized for comparison. All arithmetic, source hashes, execution flags and other fields remain exact.",
                   "Alternate build text is a synthetic metadata control, not execution on another interpreter or a native-method qualification.",
                   "All three generic error allowances remain unmet. No product/fixture/actual-tool/physical fit or budget relaxation."],
        "release": saved["release"]}
    with destination.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination),
                      "bytes": destination.stat().st_size, "source_pin_count": saved["source_pin_count"],
                      "runtime_controls": len(runtime["nonruntime_controls_rejected"])+2,
                      "output_controls": len(output_controls), "generic_error_target_met": False}))


if __name__ == "__main__":
    main()
