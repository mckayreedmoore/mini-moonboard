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
import uuid
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
FROZEN_V3 = {
    "verify-v3.py": "354bac725ebd23693bb835da073b8b503118df471cdded27e271dc3cd38f009e",
    "verification-v3.json": "2b484b62786d0c919aa21a0560cff078e2dfd2182ea5c070b5a32d9b920746da",
    "controls01/publication-file-inventory-v3.json": "df6b43be7214dd73b67284df0b45bdf6a7bd4dbeb9eb54a2f459c22447a73230",
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


def main(argv=None, *, calculate=None, run_main_controls=False):
    """The calculator argument is an internal negative-control seam, not a CLI option."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "owned canonical JSON receipt required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "fresh receipt required")
    require(all(sha(HERE / n) == h for n, h in {**FROZEN_V2, **FROZEN_V3}.items()), "frozen v2/v3 packet or inventories differ")
    previous_inventory = json.loads((HERE / "controls01/publication-file-inventory.json").read_bytes())
    previous_pins = {n: entry["sha256"] for n, entry in previous_inventory["files"].items()}
    require(all(sha(HERE / n) == h for n, h in previous_pins.items()), "original ten-file packet differs")
    reviews = {str(p.relative_to(ROOT)): sha(p)
               for generation in ("independent-review-v1", "independent-review-v2", "independent-review-v3")
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
    require(all(sha(HERE / n) == h for n, h in {**FROZEN_V2, **FROZEN_V3}.items()), "v2/v3 packets changed during checks")
    require(all(sha(HERE / n) == h for n, h in previous_pins.items()), "original packet changed during checks")
    require(all(sha(ROOT / p) == h for p, h in reviews.items()), "preserved review changed during checks")
    require(all(v is False for v in saved["release"].values())
            and all(v == "" for v in saved["actual_observations"].values()), "release or actual observation changed")
    main_control_report = actual_main_controls() if run_main_controls else None
    require(all(sha(HERE / n) == h for n, h in {**FROZEN_V2, **FROZEN_V3}.items()), "frozen packets changed during main controls")
    require(all(sha(ROOT / p) == h for p, h in reviews.items()), "preserved review changed during main controls")
    result = {
        "schema": "eoere_Z180_catalog_adapter_runtime_reproduction_verification/v4", "passed": True,
        "frozen_v3_verifier_receipt_inventory_sha256": FROZEN_V3,
        "main_controls_run_after_argument_destination_source_and_normal_checks": True,
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
    for _ in range(1000):
        path = HERE / f"{stem}-{uuid.uuid4().hex}.json"
        if not os.path.lexists(path):
            return path
    raise ValueError("fresh main-control path unavailable")



def entrypoint_preflight_controls():
    """Exercise real __main__; detect any attempted child launch or file mutation."""
    invalid = HERE / "controls01" / ("invalid-main-v4-"+uuid.uuid4().hex+".json")
    occupied = HERE / "verification-v3.json"
    occupied_before = sha(occupied)
    cases = (
        ("help", ["--help"], 0, ""),
        ("invalid_parent", ["--out", str(invalid)], 1, "owned canonical JSON receipt required"),
        ("occupied_output", ["--out", str(occupied)], 1, "fresh receipt required"),
    )
    results = []
    for label, argv, expected_code, expected_error in cases:
        program = r"""
import contextlib,io,json,os,runpy,sys
script,arguments=json.loads(sys.argv[1])
blocked=[]
def audit(event,args):
    mutating=event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.symlink','os.link','os.truncate')
    if event=='open':
        flags=args[2]
        mutating=isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
    if event=='subprocess.Popen' or mutating:
        blocked.append(event)
        raise AssertionError('entrypoint attempted child launch or file mutation: '+event)
sys.addaudithook(audit)
sys.argv=[script]+arguments
output,error=io.StringIO(),io.StringIO()
code,message=0,''
try:
    with contextlib.redirect_stdout(output),contextlib.redirect_stderr(error):
        runpy.run_path(script,run_name='__main__')
except SystemExit as exc:
    code=exc.code if isinstance(exc.code,int) else 1
except Exception as exc:
    code,message=1,str(exc)
print(json.dumps({'exit_code':code,'error':message,'blocked_events':blocked,'help_usage_present':'usage:' in output.getvalue()}))
"""
        child = subprocess.run([sys.executable, "-B", "-c", program, json.dumps([str(OWN), argv])],
                               cwd=ROOT, capture_output=True, text=True, check=False)
        require(child.returncode == 0, "entrypoint control harness failed: "+child.stderr[-3000:])
        check = json.loads(child.stdout)
        require(check["exit_code"] == expected_code and check["error"] == expected_error,
                "entrypoint outcome differs: "+label+" "+json.dumps(check))
        require(not check["blocked_events"], "entrypoint attempted a child or file mutation before guard: "+label)
        if label == "help":
            require(check["help_usage_present"], "actual entrypoint help absent")
        results.append({"case": label, "expected_exit_code": expected_code,
                        "child_launch_attempts": 0, "file_mutation_attempts": 0})
    require(not os.path.lexists(invalid) and sha(occupied) == occupied_before,
            "invalid entrypoint wrote output or occupied bytes changed")
    return {"actual_dunder_main_cases": results, "occupied_output_bytes_unchanged": True,
            "invalid_output_absent": True,
            "method": "Same-executable children invoke runpy.run_path with run_name=__main__ and real CLI arguments. Process audit hooks detect and block any nested subprocess.Popen or filesystem mutation; every case records zero attempts."}


def actual_main_controls():
    """Run real main with alternate runtime metadata and rejected result corruptions."""
    original_run_path = runpy.run_path
    original_version = sys.version
    alternate = "3.12.99 (main, Oct 09 2026, 00:00:00) [GCC 13.3.0]"
    positive = fresh_control_path("main-v4-runtime-control")
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
            bad["derived_relative_bound_under_declared_unobserved_conditions_mm"] += .001
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
        destination = fresh_control_path("main-v4-negative-control")
        try:
            main(["--out", str(destination)], calculate=lambda value=bad: (value, old))
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
        "entrypoint_preflight_controls": entrypoint_preflight_controls(),
        "recorded_generic_runtime_strict": True, "nonruntime_actual_main_controls_rejected": rejected,
        "rejected_controls_created_no_receipt": True, "parent_sys_version_and_shared_runpy_unchanged": True,
        "method": "Same sys.executable child with synthetic sys.version metadata; actual main and real adapter calculation executed. Negative controls use main's internal calculator seam and do not alter files or shared modules.",
        "actual_interpreter_executable": sys.executable,
        "positive_probe_receipt_active_ignored": str(positive.relative_to(ROOT)),
        "positive_probe_receipt_sha256": sha(positive),
        "second_interpreter_execution_claimed": False,
    }


if __name__ == "__main__":
    main(run_main_controls=True)
