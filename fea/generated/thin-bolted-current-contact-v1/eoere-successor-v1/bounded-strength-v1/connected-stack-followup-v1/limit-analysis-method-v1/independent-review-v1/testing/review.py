"""Independent testing of the frozen scalar synthetic LP packet only."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path.cwd()
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
BASE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
ISSUED = BASE / "attempt03"
OWN = Path(__file__).resolve()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source or evidence: " + path)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(operation, kind):
    try:
        operation()
    except kind:
        return
    raise ValueError("expected rejection did not occur")


def cli(script, arguments):
    command = [sys.executable, "-B", str(DOC / script), *map(str, arguments)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def independent_small_checks(a, v, inputs):
    passed = []
    # Four uniform cells close both force and moment, but the governing moment
    # is 30/7 at x=16/7, strictly inside the third cell (node maximum is four).
    left, right, density = [0., 1., 2., 3.], [1., 2., 3., 4.], [3., -1., -7., 5.]
    points, shear, moment = a.integrate(left, right, density)
    require(abs(shear) < 1e-12 and abs(moment) < 1e-12, "independent exact force/moment coupon")
    require(any(abs(x-16/7) < 1e-12 and abs(m-30/7) < 1e-12 for x, m in points), "producer misses interior peak")
    require(max(abs(m) for x, m in points if x in left+right) == 4., "coupon node-only ceiling")
    case = {"id": "independent-interior-peak", "side_length_in": 2., "main_length_in": 2., "gap_in": 0.,
            "side_bearing_lb_in": 7., "main_bearing_lb_in": 7., "yield_moment_lb_in": 4.5}
    small_inputs = {"published_cases": [], "synthetic_cases": [case], "cells_per_member": [2]}
    small_result = {"analyze_sha256": sha(DOC/"analyze.py"), "inputs_sha256": sha(DOC/"inputs.json"),
                    "cases": [{"id": case["id"], "grids": [{"cells_per_member": 2, "scaled_statics_load_lbf": 2., "maximum_exact_moment_lb_in": 30/7}]}]}
    small_details = {case["id"]+"/2": {"a_in": left, "b_in": right, "bearing_density_lb_in": density,
                     "bearing_bounds_lb_in": [7.]*4, "statics_load_lbf": 2., "moment_bound_lb_in": 4.5}}
    require(v.check(small_result, small_details, small_inputs)["independently_integrated_fields"] == 1, "exact safe coupon rejected")
    failed_inputs, failed_details = copy.deepcopy(small_inputs), copy.deepcopy(small_details)
    failed_inputs["synthetic_cases"][0]["yield_moment_lb_in"] = 4.1
    failed_details[case["id"]+"/2"]["moment_bound_lb_in"] = 4.1
    reject(lambda: v.check(small_result, failed_details, failed_inputs), ValueError)
    passed.append("independent_exact_coupon_detects_violating_interior_peak_that_all_nodes_miss")
    gap_points, gap_shear, gap_moment = a.integrate([0., 2.], [1., 3.], [1., -1.])
    require(gap_shear == 0. and gap_moment == 2. and (2., 1.5) in gap_points, "gap transfer known answer")
    passed.append("producer_prefix_integrator_exact_force_and_moment_across_empty_gap")
    for value in (0, 1, 513, 2., True):
        reject(lambda value=value: a.validate(case, value), ValueError)
    passed.append("five_additional_invalid_cell_count_and_type_controls")
    for field, value in (("side_bearing_lb_in", 0.), ("side_length_in", float("nan")), ("gap_in", float("inf"))):
        reject(lambda field=field, value=value: a.validate({**case, field: value}, 2), ValueError)
    passed.append("three_additional_nonfinite_or_nonpositive_coupon_controls")
    fake_failure = type("SyntheticFailure", (), {"success": False, "status": 4, "message": "independent controlled solver failure"})()
    with patch.object(a, "linprog", lambda *_, **__: fake_failure):
        reject(lambda: a.solve(case, 2, inputs), RuntimeError)
    passed.append("nonoptimal_LP_status_is_rejected_before_field_publication")
    grid, field = a.solve(case, 2, inputs)
    require(all(math.isfinite(value) and value <= inputs["limits"]["scaled_LP_residual_tolerance"] for value in grid["scaled_LP_certificate"].values()), "small LP certificate")
    require(grid["maximum_exact_moment_lb_in"] <= case["yield_moment_lb_in"]*(1+1e-10), "small LP exact moment")
    require(len(field["a_in"]) == 4, "small LP field dimension")
    passed.append("real_two_cell_synthetic_LP_certificate_and_exact_moment_cap")
    return passed


def corruptions(v, result, details, inputs):
    accepted = []
    changes = [
        ("candidate_capacity_claim", lambda z: z.update(candidate_inputs_used=True, candidate_joint_capacity=12345., capacity_or_pass_claim=True)),
        ("invented_raw_mode_and_analytic_load", lambda z: z["cases"][0].update(raw_governing_mode="invented", analytic_raw_yield_lbf=1e99)),
        ("nonfinite_compact_peak", lambda z: z["cases"][0]["grids"][0].update(maximum_exact_moment_lb_in=float("nan"))),
    ]
    for label, change in changes:
        value = copy.deepcopy(result)
        change(value)
        observed = v.check(value, details, inputs)
        require(observed["independently_integrated_fields"] == 45, "corruption result coverage")
        accepted.append(label)
    return accepted


def wrapper_checks(temporary, result, details, v, inputs):
    fresh = temporary / "fresh-run"
    replay = temporary / "fresh-replay"
    records = [cli("analyze.py", ["--out", fresh]), cli("analyze.py", ["--out", replay])]
    require(all(r["returncode"] == 0 for r in records), "fresh synthetic wrapper failed: " + str(records))
    matches = {}
    for name in ("result.json", "details.json"):
        matches[name] = sha(fresh/name) == sha(replay/name) == sha(ISSUED/name)
    require(all(matches.values()), "fresh synthetic output differs from issued/replay bytes")
    output = temporary / "fresh-verification.json"
    clean = cli("verify.py", ["--run", fresh, "--replay", replay, "--out", output])
    require(clean["returncode"] == 0, "fresh real checker wrapper failed")
    require(read(output)["independent_checks"] == read(DOC/"verification.json")["independent_checks"], "fresh independent metrics differ")
    records.append(clean)
    guard_records = []
    guard_file = temporary / "existing-file"
    guard_file.write_text("preserved fixture\n")
    linked = temporary / "dangling-output"
    linked.symlink_to(temporary / "absent-output-target")
    directory_link = temporary / "directory-link"
    directory_link.symlink_to(fresh, target_is_directory=True)
    for path in (fresh, guard_file, linked, directory_link):
        rejected = cli("analyze.py", ["--out", path])
        require(rejected["returncode"] == 2 and "must be a new directory" in rejected["stderr"], "real analyzer output guard")
        guard_records.append({"type": "directory" if path == fresh else "file" if path == guard_file else "symlink", "returncode": rejected["returncode"]})
    require(guard_file.read_text() == "preserved fixture\n" and linked.is_symlink(), "guard changed fixture")
    require(not (temporary/"absent-output-target").exists(), "guard followed dangling link")
    reject_verify = cli("verify.py", ["--run", fresh, "--replay", replay, "--out", output])
    require(reject_verify["returncode"] == 2 and "Verification output must be new" in reject_verify["stderr"], "real verifier existing output guard")
    accepted = corruptions(v, result, details, inputs)
    corrupted_result = copy.deepcopy(result)
    corrupted_result.update(candidate_inputs_used=True, candidate_joint_capacity=12345., capacity_or_pass_claim=True)
    corrupted_result["cases"][0].update(raw_governing_mode="invented", analytic_raw_yield_lbf=1e99)
    corrupted_result["cases"][0]["grids"][0]["maximum_exact_moment_lb_in"] = float("nan")
    bad_run, bad_replay = temporary/"corrupt-run", temporary/"corrupt-replay"
    for directory in (bad_run, bad_replay):
        directory.mkdir()
        (directory/"result.json").write_text(json.dumps(corrupted_result, sort_keys=True)+"\n")
        (directory/"details.json").write_bytes((ISSUED/"details.json").read_bytes())
    bad_output = temporary / "corrupt-verification.json"
    bad = cli("verify.py", ["--run", bad_run, "--replay", bad_replay, "--out", bad_output])
    require(bad["returncode"] == 0, "real CLI did not reproduce accepted corrupt result")
    bad_receipt = read(bad_output)
    require(bad_receipt["candidate_inputs_used"] is False and bad_receipt["capacity_or_pass_claim"] is False, "hardcoded receipt behavior changed")
    return {"real_fresh_commands": records, "all_fresh_outputs_byte_identical_to_issued": matches,
            "real_output_guard_controls": guard_records, "existing_verifier_output_rejected": True,
            "accepted_compact_result_corruptions": accepted,
            "real_corrupt_result_verification": {"command": bad["command"], "returncode": bad["returncode"],
                "input_result_candidate_inputs_used": True, "input_result_candidate_joint_capacity": 12345., "input_result_capacity_or_pass_claim": True,
                "input_result_raw_mode": "invented", "input_result_analytic_raw_yield_lbf": 1e99,
                "input_result_compact_moment_peak": "NaN", "output_receipt_candidate_inputs_used": bad_receipt["candidate_inputs_used"],
                "output_receipt_capacity_or_pass_claim": bad_receipt["capacity_or_pass_claim"], "output_receipt_sha256": sha(bad_output)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OWN.with_name("receipt.json"))
    args = parser.parse_args()
    with args.out.open("xb") as stream:
        frozen_path = ISSUED/"frozen-packet.json"
        frozen = read(frozen_path)
        require(len(frozen) == 6, "exact six-file target required")
        source_sha256 = {path: record["sha256"] for path, record in frozen.items()}
        verify(source_sha256)
        for path, record in frozen.items():
            require((ROOT/path).stat().st_size == record["bytes"], "frozen target byte count")
        inputs = read(DOC/"inputs.json")
        source_sha256.update({r["path"]: r["sha256"] for r in inputs["references"]})
        source_sha256.update({str(path.relative_to(ROOT)): sha(path) for path in ISSUED.iterdir() if path.is_file()})
        source_sha256[str(OWN.relative_to(ROOT))] = sha(OWN)
        verify(source_sha256)
        a, v = load(DOC/"analyze.py", "independent_synthetic_LP_analysis"), load(DOC/"verify.py", "independent_synthetic_LP_verifier")
        a.check_pins(inputs)
        result, details = read(ISSUED/"result.json"), read(ISSUED/"details.json")
        independent = v.check(result, details, inputs)
        require(independent["independently_integrated_fields"] == 45, "issued field census")
        small_checks = independent_small_checks(a, v, inputs)
        with tempfile.TemporaryDirectory(prefix="limit-analysis-independent-testing-") as directory:
            wrapper = wrapper_checks(Path(directory), result, details, v, inputs)
        verify(source_sha256)
        a.check_pins(inputs)
        finding = {"severity": "medium", "category": "testing/evidence-validation", "file": str((DOC/"verify.py").relative_to(ROOT)), "line": 101,
            "supporting_lines": [20, 104, 105, 191, 192],
            "description": "The checker validates saved field statics but leaves compact-result scope flags, analytic values/modes and other benchmark assertions unchecked. Its peak comparison also accepts NaN because abs(actual-NaN)>tolerance is false. A real verify.py call accepts two byte-identical corrupted result copies and issues a receipt with hardcoded false scope flags.",
            "impact": "A successful verification receipt can accompany an invented governing mode/analytic benchmark, a nonfinite reported peak, or a non-null candidate capacity claim. Existing corruption controls can therefore pass while the compact reporting artifact contradicts the method's synthetic-only claim boundary.",
            "fix": "Validate the compact result's schema, exact synthetic-only/null-capacity flags, unique case/grid coverage and finite reported values before integration; check benchmark modes/values against the frozen analytic known answers, and explicitly reject nonfinite peak values. Add these result corruptions to the real CLI negative controls; derive receipt scope flags from checked input claims."}
        receipt = {"schema": "synthetic_limit_method_independent_testing_review/v1", "status": "NUMERIC_AND_WRAPPER_CHECKS_PASS_WITH_ONE_CONFIRMED_RESULT_VALIDATION_GAP", "findings": [finding],
            "command": [sys.executable, "-B", str(OWN.relative_to(ROOT)), "--out", str(args.out)], "environment": a.environment(), "source_sha256": source_sha256,
            "six_target_and_all_issued_attempt_files_before_after_unchanged": True, "issued_independent_field_metrics": independent,
            "independent_small_controls": small_checks, "wrapper_checks": wrapper,
            "limits": ["Only scalar synthetic two-member coupons and their frozen helper/environment were used; no actual candidate actions, geometry, material or capacity was evaluated.",
                       "Two fresh synthetic LP wrappers reproduced all 45 fields byte-for-byte, and a separate real verifier call demonstrated corrupt-result acceptance in temporary copies.",
                       "No CAD/BRep/query, current panel bank, frame K, native solve, browser or global candidate case ran. Target/source bytes and issued attempts were preserved.",
                       "Temporary outputs belonged to this review and were removed by TemporaryDirectory. No shared document, staging, commit, archive or prune operation occurred."]}
        stream.write((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n").encode())
    print(json.dumps({"status": receipt["status"], "findings": 1, "receipt_sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
