"""Verify frozen adapter arithmetic while recording live runtime separately."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
FROZEN_V2 = {
    "adapter-v2.py": "dae93a7011242ad3878f47040cbf3af9cd224d7077eb503621a8816d55cd4014",
    "result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    "result-v3.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify-v2.py": "2f01212e390c5ea53a23821ecb6042e82fe0c9b64fd1fc54341c0944b3c0757f",
    "verification-v2.json": "286c4df35620d46d4a3276904ffb6f4997c5a0cf57f8c49b6e113a0f9231410e",
    "controls01/publication-file-inventory.json": "9f8241920281107edf8edcf77d96b54ec049a0025a0fb2d053a9b54c4d740f0c",
    "controls01/publication-file-inventory-v2.json": "e0f7e412e4f8a64385dc564d7793c8b3b9cdf6fbe256c561c7c8eb9f1497f514",
}
LIVE_RUNTIME_FIELDS = ("generic_live_execution_python", "wrapper_live_execution_python")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_replay(live, saved):
    """Compare every field, normalizing only two live runtime text leaves."""
    expected = {k: v for k, v in saved.items() if k != "drawing"}
    normalized = copy.deepcopy(live)
    for field in LIVE_RUNTIME_FIELDS:
        require(isinstance(live["runtime_reproduction"][field], str)
                and isinstance(expected["runtime_reproduction"][field], str),
                "live runtime text required")
        normalized["runtime_reproduction"][field] = expected["runtime_reproduction"][field]
    require(normalized == expected, "non-runtime wrapper scalar/source/structure replay difference")
    return normalized


def main(argv=None, *, calculate=None, main_control_report=None):
    """The calculator argument is an internal negative-control seam, not a CLI option."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "owned canonical JSON receipt required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "fresh receipt required")
    require(all(sha(HERE / n) == h for n, h in FROZEN_V2.items()), "frozen v2 packet or inventories differ")
    previous_inventory = json.loads((HERE / "controls01/publication-file-inventory.json").read_bytes())
    previous_pins = {n: entry["sha256"] for n, entry in previous_inventory["files"].items()}
    require(all(sha(HERE / n) == h for n, h in previous_pins.items()), "original ten-file packet differs")
    reviews = {str(p.relative_to(ROOT)): sha(p)
               for generation in ("independent-review-v1", "independent-review-v2")
               for p in (HERE / generation).glob("*/*") if p.is_file()}
    checks = runpy.run_path(str(HERE / "verify-v2.py"))
    for name, digest in checks["REVIEWS"].items():
        require(sha(HERE / "independent-review-v1" / name / "receipt.json") == digest, "original v1 review changed")
    method = runpy.run_path(str(HERE / "adapter-v2.py"))
    saved = json.loads((HERE / "result-v3.json").read_bytes())
    live, old = (calculate or method["calculate"])()
    untouched = copy.deepcopy(live)
    compare_replay(live, saved)
    require(live == untouched, "comparison mutated live provenance")
    require(hashlib.sha256(old["drawing"](live)).hexdigest() == saved["drawing"]["sha256"], "unchanged v1 SVG bytes")
    decimal = runpy.run_path(str(HERE / "verify.py"))["decimal_corners"](saved)
    runtime = checks["runtime_controls"](method, live)
    guard = runpy.run_path(str(HERE.parent / "verify.py"))["guard_checks"]
    guard.__globals__["HERE"] = HERE
    (HERE / "controls01").mkdir(exist_ok=True)
    output_controls = guard(old["output_paths"])
    old["verify"](saved["source_sha256"])
    require(all(sha(HERE / n) == h for n, h in FROZEN_V2.items()), "v2 packet changed during checks")
    require(all(sha(HERE / n) == h for n, h in previous_pins.items()), "original packet changed during checks")
    require(all(sha(ROOT / p) == h for p, h in reviews.items()), "preserved review changed during checks")
    require(all(v is False for v in saved["release"].values())
            and all(v == "" for v in saved["actual_observations"].values()), "release or actual observation changed")
    result = {
        "schema": "eoere_Z180_catalog_adapter_runtime_reproduction_verification/v3", "passed": True,
        "frozen_v2_packet_and_inventory_sha256": FROZEN_V2, "preserved_original_ten_file_sha256": previous_pins,
        "preserved_available_review_sha256": reviews, "source_pin_count": saved["source_pin_count"],
        "normalized_wrapper_comparison_paths_only": ["/runtime_reproduction/"+n for n in LIVE_RUNTIME_FIELDS],
        "recorded_runtime_provenance": saved["runtime_reproduction"],
        "live_runtime_provenance": live["runtime_reproduction"],
        "recorded_generic_runtime_and_every_other_field_exact": True,
        "live_comparison_input_unchanged": True, "runtime_reproduction_controls": runtime,
        "actual_main_controls": main_control_report,
        "reused_independent_decimal_checks": decimal, "reused_output_guard_controls": output_controls,
        "v1_scalar_source_and_guard_outputs_exact": True, "v1_drawing_bytes_exact": True,
        "verification_method_sha256": sha(OWN), "all_sources_packets_and_available_reviews_unchanged": True,
        "limits": [
            "Generic producer normalizes only /execution/python; this verifier normalizes only the two declared live-runtime text leaves. Recorded generic runtime and every other field remain exact.",
            "Runtime controls use synthetic metadata on the same interpreter, not execution on a second interpreter or a native-method qualification.",
            "All three generic error allowances remain unmet. No product, fixture, actual-tool, physical fit, strength or budget relaxation.",
        ], "release": saved["release"],
    }
    with destination.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination),
                      "bytes": destination.stat().st_size, "source_pin_count": saved["source_pin_count"],
                      "runtime_controls": len(runtime["nonruntime_controls_rejected"])+2,
                      "output_controls": len(output_controls), "generic_error_target_met": False}))
    return result


def fresh_control_path(stem):
    for number in range(1, 10001):
        path = HERE / f"{stem}{number:02}.json"
        if not os.path.lexists(path):
            return path
    raise ValueError("fresh main-control path unavailable")


def actual_main_controls():
    """Run real main with alternate runtime metadata and rejected result corruptions."""
    original_run_path = runpy.run_path
    original_version = sys.version
    alternate = "3.12.99 (main, Oct 09 2026, 00:00:00) [GCC 13.3.0]"
    positive = fresh_control_path("main-v3-runtime-control")
    program = (
        "import runpy,sys\n"
        f"sys.version={alternate!r}\n"
        f"module=runpy.run_path({str(OWN)!r})\n"
        f"module['main'](['--out',{str(positive)!r}])\n"
    )
    child = subprocess.run([sys.executable, "-B", "-c", program], cwd=ROOT,
                           capture_output=True, text=True, check=False)
    require(child.returncode == 0, "alternate-runtime actual main failed: "+child.stderr[-3000:])
    receipt = json.loads(positive.read_bytes())
    require(receipt["passed"] and all(receipt["live_runtime_provenance"][n] == alternate for n in LIVE_RUNTIME_FIELDS),
            "actual main did not record both alternate live runtime strings")
    recorded = json.loads((HERE / "result-v3.json").read_bytes())["runtime_reproduction"]
    require(receipt["recorded_runtime_provenance"] == recorded
            and receipt["live_runtime_provenance"]["generic_recorded_execution_python"]
            == recorded["generic_recorded_execution_python"], "recorded runtime normalization expanded")
    method = runpy.run_path(str(HERE / "adapter-v2.py"))
    baseline, old = method["calculate"]()
    rejected = []
    labels = ("relative_budget", "source_pin", "recorded_generic_runtime", "extra_runtime_field",
              "release_flag", "execution_flag", "nontext_live_runtime", "extra_top_level_field")
    for label in labels:
        bad = copy.deepcopy(baseline)
        if label == "relative_budget":
            bad["path_and_error_comparison"]["required_relative_bound_mm"] += .001
        elif label == "source_pin":
            bad["source_sha256"][next(iter(bad["source_sha256"]))] = "0"*64
        elif label == "recorded_generic_runtime":
            bad["runtime_reproduction"]["generic_recorded_execution_python"] = alternate
        elif label == "extra_runtime_field":
            bad["runtime_reproduction"]["unexpected_control_field"] = True
        elif label == "release_flag":
            bad["release"]["fabrication"] = True
        elif label == "execution_flag":
            bad["execution"]["unexpected_control_field"] = True
        elif label == "nontext_live_runtime":
            bad["runtime_reproduction"][LIVE_RUNTIME_FIELDS[0]] = None
        else:
            bad["unexpected_control_field"] = True
        destination = fresh_control_path("main-v3-negative-control")
        try:
            main(["--out", str(destination)], calculate=lambda: (bad, old))
        except ValueError as error:
            require("non-runtime wrapper" in str(error) or "live runtime text required" in str(error),
                    "actual main rejected control for an unrelated reason")
            require(not os.path.lexists(destination), "rejected main control wrote a receipt")
            rejected.append(label)
        else:
            raise ValueError("actual main accepted nonruntime change: "+label)
    require(runpy.run_path is original_run_path and sys.version == original_version, "shared runtime or runpy mutated")
    return {
        "alternate_runtime_actual_main_passed": True, "both_live_runtime_fields_recorded_separately": True,
        "recorded_generic_runtime_strict": True, "nonruntime_actual_main_controls_rejected": rejected,
        "rejected_controls_created_no_receipt": True, "parent_sys_version_and_shared_runpy_unchanged": True,
        "method": "Same sys.executable child with synthetic sys.version metadata; actual main and real adapter calculation executed. Negative controls use main's internal calculator seam and do not alter files or shared modules.",
        "actual_interpreter_executable": sys.executable,
        "positive_probe_receipt_active_ignored": str(positive.relative_to(ROOT)),
        "positive_probe_receipt_sha256": sha(positive),
        "second_interpreter_execution_claimed": False,
    }


if __name__ == "__main__":
    main(main_control_report=actual_main_controls())
