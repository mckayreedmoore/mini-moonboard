"""Independent final source/evidence review. No real analysis or CAD import."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
SUPPLEMENT = DOC / "revised-base-audit-v1/reproduction-guard-v1"
PRIOR = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-review-v1/current-geometry-followups-v1/correctness/receipt.json"
PINS = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def pin(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    actual = sha(path)
    need(expected is None or actual == expected, "pin mismatch: " + str(path))
    key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    need(key not in PINS or PINS[key] == actual, "conflicting source: " + key)
    PINS[key] = actual
    return path


def read(path, expected=None):
    return json.loads(pin(path, expected).read_bytes())


def import_stdlib(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def norm(vector):
    return math.sqrt(sum(x * x for x in vector))


def close(a, b, tolerance=1e-8):
    need(abs(a - b) <= tolerance, "scalar arithmetic differs")


def must_fail(operation, errors):
    try:
        operation()
    except errors:
        return
    raise ValueError("expected failure accepted")


def extra_guard_controls(guard):
    passed = []
    with tempfile.TemporaryDirectory(prefix="eoere-final-correctness-") as directory:
        temporary = Path(directory)
        snapshot = {
            "pins": {}, "issued_pin_count": 0,
            "issued_closure_canonical_sha256": canonical({}),
            "guarded_pin_count": 0, "guarded_closure_canonical_sha256": canonical({}),
        }
        def runner(path, producer, after=lambda _: None, compare=None):
            return guard.guarded_calculation(path, lambda: snapshot, producer, after,
                                             {"independent_fixture_only": True}, compare)
        producer = lambda: ({"finite": 1}, {"finite": 2})
        out = temporary / "finite"
        receipt = runner(out, producer)
        for name, record in receipt["output_files"].items():
            need(record["sha256"] == sha(out / name), "provenance output hash")
            need(record["bytes"] == (out / name).stat().st_size, "output size")
        passed.append("successful_stub_provenance_binds_both_exact_outputs")
        bad = temporary / "nonfinite"
        must_fail(lambda: runner(bad, lambda: ({"bad": float("nan")}, {})), ValueError)
        need(not list(bad.iterdir()), "nonfinite output was published")
        passed.append("nonfinite_serialization_rejected_without_outputs")
        bad = temporary / "details-collision"
        def collide():
            (bad / "details.json").write_bytes(b"preserve sentinel")
            return producer()
        must_fail(lambda: runner(bad, collide), FileExistsError)
        need((bad / "details.json").read_bytes() == b"preserve sentinel", "collision clobbered")
        need(not (bad / "run-provenance.json").exists(), "failed attempt marked verified")
        passed.append("details_collision_retains_sentinel_without_verified_provenance")
        bad = temporary / "second-compare-difference"
        comparison = temporary / "compare"
        comparison.mkdir()
        (comparison / "result.json").write_bytes((out / "result.json").read_bytes())
        (comparison / "details.json").write_bytes(b"wrong")
        must_fail(lambda: runner(bad, producer, compare=comparison), ValueError)
        need(not list(bad.iterdir()), "second comparison failure wrote outputs")
        passed.append("second_comparison_file_mismatch_leaves_empty_reserved_attempt")
        after_calls = 0
        bad = temporary / "after-write-failure"
        def fail_second_after(_):
            nonlocal after_calls
            after_calls += 1
            if after_calls == 2:
                raise ValueError("controlled late source failure")
        must_fail(lambda: runner(bad, producer, after=fail_second_after), ValueError)
        need(not (bad / "run-provenance.json").exists(), "late failure marked verified")
        need((bad / "result.json").is_file() and (bad / "details.json").is_file(), "attempt not retained")
        passed.append("postwrite_source_failure_keeps_attempt_without_success_provenance")
        original_loader = guard.load_analysis
        original_inputs_loader = guard.load_inputs
        def forbidden_loader(*_):
            raise AssertionError("real analysis import forbidden")
        guard.load_analysis = forbidden_loader
        def invalid_inputs():
            raise ValueError("controlled authentication failure")
        guard.load_inputs = invalid_inputs
        try:
            bad = temporary / "real-execute-input-failure"
            must_fail(lambda: guard.execute("audit", bad), ValueError)
            need(bad.is_dir() and not list(bad.iterdir()), "before failure not retained")
            passed.append("real_execute_authentication_failure_precedes_analysis_import")
            must_fail(lambda: guard.execute("connected", out), FileExistsError)
            passed.append("real_execute_existing_output_rejected_before_input_authentication")
        finally:
            guard.load_analysis = original_loader
            guard.load_inputs = original_inputs_loader
    return passed


prior = read(PRIOR, "0be9568bf749bfef1861390d0751b81af0d9309cc46730cb12cbe613fb8757bb")
need(prior["substantial_findings"] == [], "prior review is not clean")
for path, digest in prior["source_sha256"].items():
    pin(path, digest)
verification = read(SUPPLEMENT / "verification.json", "010fb293bc0b7dead3821e66f9923c0a7a942438e09545cec0dd36e7c8044ae5")
result = read(SUPPLEMENT / "result.json", "b48c1ba300e161a729ffa9f9cbcabe75b44126488e376eea0154e7bf7b8d71a7")
for record in [*verification["owned_artifacts"].values(), *verification["raw_receipts"]]:
    path = pin(record["path"], record["sha256"])
    need(path.stat().st_size == record["bytes"], "artifact byte count")
need(len(verification["owned_artifacts"]) == 6, "six externally verified supplement artifacts")
need(set(p.name for p in SUPPLEMENT.iterdir() if p.is_file()) == {
    "README.md", "inputs.json", "result.json", "verification.json",
    "run_fresh.py", "check_guard.py", "check_evidence.py"}, "supplement file set")

inputs = read(SUPPLEMENT / "inputs.json")
packet_details = {}
for name, packet in inputs["packets"].items():
    for reference in [packet["analysis"], packet["details"], *packet["issued_files"]]:
        pin(reference["path"], reference["sha256"])
    details = read(packet["details"]["path"], packet["details"]["sha256"])
    packet_details[name] = details
    closure = details["complete_source_sha256"]
    need(len(closure) == packet["issued_pin_count"], "issued pin count")
    need(canonical(closure) == packet["issued_closure_canonical_sha256"], "issued closure digest")
    for path, digest in closure.items():
        pin(path, digest)
    # The supported guard imports run(), never the historical main block.
    tree = ast.parse((ROOT / packet["analysis"]["path"]).read_text())
    run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
    need(not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and node.func.attr in {"write_text", "write_bytes", "mkdir", "open"}
                 for node in ast.walk(run)), "analysis run has an output side effect")

for reference in inputs["evidence"].values():
    pin(reference["path"], reference["sha256"])
reuse = read(inputs["evidence"]["v3_interval_reuse"]["path"])
for path, digest in reuse["source_sha256"].items():
    pin(path, digest)
proof = reuse["reused_proof"]
pin(proof["path"], proof["sha256"])
pin(proof["supporting_retained_checker"]["path"], proof["supporting_retained_checker"]["sha256"])
need(proof["exact_base_geometry_sha256"] == inputs["evidence"]["base_v3"]["sha256"], "proof revision mismatch")
need(proof["reusable_principal_and_kicker_post_interval_subset"] == 12, "proof subset mismatch")
recovery = read(inputs["evidence"]["historical_recovery"]["path"])
for key in ("source", "historical_command", "historical_tool_records", "issued_verification", "existing_independent_checks"):
    pin(recovery[key]["path"], recovery[key]["sha256"])
source = (ROOT / recovery["source"]["path"]).read_text()
ast.parse(source)
need(len(source.encode()) == 2720, "source recovery byte count")
command = (ROOT / recovery["historical_command"]["path"]).read_text()
need(command == "uv run python - <<'PY'\n" + source + "PY", "stdin recovery mismatch")
records = [json.loads(line) for line in (ROOT / recovery["historical_tool_records"]["path"]).read_text().splitlines()]
call = next(row for row in records if row["payload"]["type"] == "custom_tool_call")
output = next(row for row in records if row["payload"]["type"] == "custom_tool_call_output")
need(call["payload"]["call_id"] == output["payload"]["call_id"] == recovery["original_tool_call_id"], "historical call identity")
need(call["timestamp"] == recovery["original_call_timestamp_utc"], "historical call timestamp")
need(output["timestamp"] == recovery["original_output_timestamp_utc"], "historical output timestamp")
decoded, _ = json.JSONDecoder().raw_decode(call["payload"]["input"].split("tools.exec_command({cmd:", 1)[1])
need(decoded == command, "historical command mismatch")
need("(out/'independent-checks.json').write_text" in source, "historical output side effect not disclosed")
need("result['known_answers']['full_gap_clipped_probe_fractions']" in source, "historical coupon reuse not disclosed")

model = read(inputs["evidence"]["base_v3"]["path"])
issued_audit = read(inputs["evidence"]["audit_result"]["path"])
field = read(inputs["evidence"]["first_old_field"]["path"])
interval_error = max(abs(a-b) for row in model["canonical_interval_checks"]
                     for a,b in zip(row["canonical_interval_mm"], row["saved_receiver_x_bounds_mm"]))
need(len(model["canonical_interval_checks"]) == 12 and interval_error < 1e-6, "saved interval arithmetic")
fresh = [row for row in packet_details["audit"]["washer_seat_rows"] if "current_host_support_point_xyz_mm" in row]
need(len(fresh) == 36, "fresh support row count")
for row in fresh:
    expected = math.pi * (row["OD_mm"]**2 - row["support_inner_diameter_mm"]**2) * row["probe_depth_mm"] / 4
    close(expected, row["expected_probe_volume_mm3"])
    close(expected, row["intersected_current_wood_volume_mm3"], 1e-4)
    close(row["intersected_current_wood_volume_mm3"] / expected, row["support_fraction"], 1e-12)

members = {row["name"]: row for row in field["source_inputs"]["timber_rows"]}
independent_gaps = {}
for row in issued_audit["candidate_member_restraint_paths"]:
    member = members[row["member"]]
    delta = [b-a for a,b in zip(member["start"], member["end"])]
    length = norm(delta)
    grain = [value/length for value in delta]
    shift = model["principal_shift_xyz_mm"] if row["member"] == "base_principal_center_right" else [0,0,0]
    start = [a+b for a,b in zip(member["start"], shift)]
    screws = [s for s in model["screw_axes"] if s["receiver"] == row["member"]]
    need(sorted(s["axis_id"] for s in screws) == sorted(row["candidate_screw_axis_ids"]), "station identity mismatch")
    positions = sorted(sum((p-a)*g for p,a,g in zip(s["origin_xyz_mm"], start, grain)) for s in screws)
    gaps = [b-a for a,b in zip([0,*positions], [*positions,length])]
    independent_gaps[row["member"]] = max(gaps)
    close(max(gaps), row["largest_candidate_gap_mm"], 1e-6)
    close(length, row["gross_length_mm"], 1e-6)

max_integral_error = 0.0
for row in packet_details["connected"]["member_bearing_trials"]:
    length = row["interval_from_axis_point_mm"][1] - row["interval_from_axis_point_mm"][0]
    left, right = row["affine_endpoint_line_density_vectors_n_mm"]
    force = [(a+b)*length/2 for a,b in zip(left,right)]
    first = [(b-a)*length**2/12 for a,b in zip(left,right)]
    for actual, expected in zip(force, row["lateral_force_on_host_xyz_n"]):
        max_integral_error = max(max_integral_error, abs(actual-expected))
        close(actual, expected, 1e-8)
    for actual, expected in zip(first, row["lateral_first_moment_xyz_nmm"]):
        max_integral_error = max(max_integral_error, abs(actual-expected))
        close(actual, expected, 1e-8)
    peak = max(norm(left), norm(right))
    close(peak, row["affine_trial_peak_line_density_n_mm"])
    close(peak/row["bearing_screen_D_mm"], row["affine_trial_peak_projected_bearing_mpa"])
    if row["kind"] == "wood":
        close(row["affine_trial_peak_projected_bearing_mpa"]/row["DFL_Fe90_material_parameter_mpa"], row["affine_peak_over_Fe90_parameter"])
    need(not row["deformation_compatibility_or_yield_capacity_established"], "trial acceptance overclaim")
need(len(packet_details["connected"]["member_bearing_trials"]) == 144, "member trial count")
connected = read(DOC / "connected-stack-followup-v1/result.json", "d81540a6c69b98f1182a6d2649d9a0d39126756ea94f0b3cd691026de7cb94d1")
need(len(connected["stacks"]) == 8 and all(r["adjusted_complete_joint_resistance_n"] is None for r in connected["stacks"]), "resistance overclaim")
need(not connected["fabrication_or_climbing_release"] and not issued_audit["fabrication_or_climbing_release"], "release overclaim")
need(connected["source_geometry_revision"] == "eoere-bottom-rail-tnut-clearance-v1", "source geometry mismatch")
need(connected["target_geometry_revision_not_evaluated"] == "eoere-midpoint-ready-frame-v3", "response overclaim")

sys.path.insert(0, str(SUPPLEMENT))
guard = import_stdlib(SUPPLEMENT / "run_fresh.py", "run_fresh")
evidence = import_stdlib(SUPPLEMENT / "check_evidence.py", "final_evidence_checker")
controls = import_stdlib(SUPPLEMENT / "check_guard.py", "final_guard_checker")
snapshots = [guard.authenticate(inputs, sha(SUPPLEMENT / "inputs.json"), key) for key in ("audit", "connected")]
replayed_controls = controls.controls(inputs)
need(replayed_controls == result["guard_controls"]["passed_controls"] and len(replayed_controls) == 14, "guard controls differ")
replayed_evidence = evidence.run(inputs, sha(SUPPLEMENT / "inputs.json"))
need(replayed_evidence == result["evidence_supplement"], "evidence supplement reproduction differs")
additional_controls = extra_guard_controls(guard)
for snapshot in snapshots:
    guard.verify(snapshot["pins"])
for path, digest in list(PINS.items()):
    need(sha(ROOT / path) == digest, "source changed during final review: " + path)
pin(__file__)
receipt = {
    "schema": "independent_final_two_packet_correctness_review/v1",
    "status": "PASS_BOUNDED_SOURCE_GUARD_PROVENANCE_AND_ARITHMETIC_REVIEW",
    "substantial_findings": [],
    "prior_numeric_review_reused": {"path": str(PRIOR.relative_to(ROOT)), "sha256": sha(PRIOR), "exact_original_target_files_unchanged": True},
    "checks": {
        "original_source_closures_before_after": [s["issued_pin_count"] for s in snapshots],
        "supplement_source_closure": replayed_evidence["supplement_pin_count"],
        "supplement_record_reproduced_exactly": True,
        "retained_guard_controls": replayed_controls,
        "independent_extra_guard_controls": additional_controls,
        "source_authenticated_historical_provenance_without_execution": True,
        "prior_v3_saved_solid_proof_reused_with_exact_revision": True,
        "independent_saved_interval_arithmetic_count": 12,
        "maximum_saved_interval_error_mm": interval_error,
        "independent_ring_volume_and_saved_full_support_arithmetic_count": len(fresh),
        "independent_member_endpoint_and_station_gaps_mm": independent_gaps,
        "independent_affine_endpoint_integrals": 144,
        "maximum_endpoint_integral_error": max_integral_error,
        "all_eight_complete_joint_resistances_null": True,
        "frozen_reporting_and_geometry_boundaries_preserved": True,
    },
    "limits": [
        "Original full numeric review is reused only against its exact source/result pins; its source hashes were checked again.",
        "No original full analyze CLI, original run method or recovered fixed-output stdin command executed.",
        "All new calculation execution uses stdlib retained evidence checks and temporary stub guard fixtures.",
        "No CAD/BRep import/query/rebuild, native/global solve, browser, geometry alteration, full analysis or test suite.",
        "Prior saved-solid interval and washer intersections are authenticated reuse, not new geometric observations.",
        "Old-action statics, Fe material input comparisons and candidate restraint stations do not establish current response or complete joint resistance.",
        "No tracked or peer-owned path edited; only the reviewer script and receipt are retained.",
    ],
    "mechanics_acceptance": False,
    "physical_release": False,
    "command": [".venv/bin/python", "-B", str(Path(__file__).relative_to(ROOT))],
    "source_sha256": PINS,
}
with (OUT / "receipt.json").open("x") as stream:
    stream.write(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT / "receipt.json"), "source_pins": len(PINS)}))
