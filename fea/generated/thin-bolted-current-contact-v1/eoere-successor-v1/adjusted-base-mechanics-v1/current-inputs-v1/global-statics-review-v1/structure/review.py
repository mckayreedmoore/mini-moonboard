"""Source-only architecture/ownership/retention review of frozen current statics.

Only saved records, AST contracts, the pure input validator, and preflight
rejections are exercised. The preserved statics method is never executed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
DOC = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-inputs-v1/global-statics-v1"
EXPECTED = {
    "check_current.py": "c2c32d1fdadae374b5d7f7d192d979e52954011bc041171980cc6e63a0aeceaa",
    "verify.py": "68e27a587cadc08b64923cbe76fdf5db36c35ca0cca6d8789ac3f3b44be7862d",
    "result.json": "f05f81d17a80b1fc1e2a0df106a60ac34f6253a1bb0b664a7241e63cc3702c24",
    "verification.json": "2278f49ebd516bb3cc10fc1fffa53bdda989008c66429eeb4e55c2952404b203",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def record(path):
    raw = path.read_bytes()
    return {"sha256": digest(raw), "bytes": len(raw)}


def load(path):
    return json.loads(path.read_bytes())


def relative(path):
    return str(path.relative_to(ROOT))


def main():
    require(OWN.parts[-2:] == ("global-statics-review-v1", "structure"), "exclusive output root differs")
    target = {name: record(DOC / name) for name in EXPECTED}
    require({name: ref["sha256"] for name, ref in target.items()} == EXPECTED, "frozen target differs")
    require(sum(ref["bytes"] for ref in target.values()) == 56410, "compact target byte volume differs")
    context = {name: record(ROOT / name) for name in ["AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md"]}
    result, verification = load(DOC / "result.json"), load(DOC / "verification.json")
    direct = result["source_bindings"]
    require(len(direct) == 8 and all(record(ROOT / p)["sha256"] == sha for p, sha in direct.items()), "eight direct pins differ")
    verification_pins = verification["source_bindings"]
    require(verification_pins == {**direct, relative(DOC / "result.json"): EXPECTED["result.json"], relative(DOC / "verify.py"): EXPECTED["verify.py"]}, "verifier source boundary differs")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in verification_pins.items()), "verification pins differ")
    current_path = next(ROOT / p for p in direct if p.endswith("current-inputs-v1/attempt01/inputs.json"))
    old_path = next(ROOT / p for p in direct if p.endswith("raised-rail-mechanics-v1/inputs.json"))
    method_path = ROOT / result["method"]["path"]
    current, old = load(current_path), load(old_path)
    cache = load(ROOT / current["geometry"]["cached_source_export"]["path"])
    require(result["input_recursive_pin_count_declared_not_independently_rehashed_here"] == len(current["source_sha256"]) == 1086, "declared recursive-pin boundary differs")
    require(result["input_status_preserved"] == current["status"] == "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW", "pending status relabeled")
    require(result["input_readiness_preserved"] == current["readiness"] and all(v is False for v in current["readiness"].values()), "pending readiness relabeled")
    require(result["release"] == current["release"] and all(v is False for v in current["release"].values()), "acceptance transferred")
    require(current["historical_q"] is current["old_field"] is None and current["optional_2026_extra"] is False, "source-only OFF boundary differs")
    require(result["status"] == "GLOBAL_COMPRESSION_EQUILIBRIUM_ONLY" and result["source_loads_recomputed_not_taken_from_a_response"] is True, "global result scope differs")
    require(all(c["elastic_joint_demands_or_floor_capacity_established"] is False for c in result["cases"]), "joint/floor acceptance claimed")

    producer_source = (DOC / "check_current.py").read_text()
    producer_tree = ast.parse(producer_source)
    verifier_tree = ast.parse((DOC / "verify.py").read_bytes())
    method_tree = ast.parse(method_path.read_bytes())
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in producer_tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {"CURRENT_SHA", "METHOD_SHA", "OLD_INPUT_SHA", "HOSTS", "CASE_IDS"}}
    require(constants["CURRENT_SHA"] == direct[relative(current_path)], "input pre-load hash differs")
    require(constants["METHOD_SHA"] == direct[relative(method_path)] == result["method"]["sha256"], "preserved method pre-load hash differs")
    require(constants["OLD_INPUT_SHA"] == direct[relative(old_path)], "legacy footprint input hash differs")
    calls = Counter(n.func.attr for n in ast.walk(producer_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "method")
    require(calls == {"fixtures": 1, "assess": 1, "ConvexHull": 1}, "legacy method call boundary differs")
    require('exec(compile(method_raw, str(METHOD), "exec"), method.__dict__)' in producer_source, "captured method source not used")
    require('method_raw = capture(METHOD, METHOD_SHA)' in producer_source, "method source authentication differs")
    old_fields = {n.slice.value for n in ast.walk(producer_tree) if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "old" and isinstance(n.slice, ast.Constant)}
    require(old_fields == {"floor_footprints"}, "historical response is consumed")
    fixtures = next(n for n in method_tree.body if isinstance(n, ast.FunctionDef) and n.name == "fixtures")
    require(sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "assess" for n in ast.walk(fixtures)) == 7, "preserved seven-fixture contract differs")
    require('if not __debug__:' in producer_source, "assertion-disabled fixture execution not rejected")
    require('with output.open("xb") as handle:' in producer_source and producer_source.count('unchanged()') == 3, "exclusive output/source stability contract differs")
    verifier_run = next(n for n in verifier_tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    require(ast.unparse(verifier_run.body[0]) == 'output.mkdir(parents=True, exist_ok=False)', "fresh verifier output boundary differs")

    # Compile only function definitions and literal constants; no module imports
    # or producer/method calculation entrypoints run. validate() is pure stdlib.
    namespace = {"hashlib": hashlib, "json": json, "math": math, "Path": Path, "__file__": str(DOC / "check_current.py"), **constants}
    definitions = [n for n in producer_tree.body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[])), str(DOC / "check_current.py"), "exec"), namespace)
    points, changed, mass = namespace["validate"](current, old, cache)
    require(points == result["support_point_order"] and len(points) == 32 and len(changed) == 4, "saved source validation/support ownership differs")
    require(mass == result["mass"], "saved source mass composition differs")
    require(result["legacy_footprint_comparison"]["identical_point_count"] == 28 and result["legacy_footprint_comparison"]["changed_points"] == changed, "legacy footprint comparison differs")
    for key, value in [("historical_q", [1]), ("old_field", {"id": "old"}), ("optional_2026_extra", True)]:
        bad = dict(current)
        bad[key] = value
        try:
            namespace["validate"](bad, old, cache)
        except ValueError as error:
            require("current extra-off source-only inputs required" in str(error), "wrong source-only rejection")
        else:
            raise ValueError(f"source-only gate accepted {key}")
    preflight_checks = []
    for label, input_path, output in [("occupied_review_file", current_path, Path(__file__)), ("source_output_alias", current_path, current_path)]:
        before = record(output)
        try:
            namespace["run"](input_path, output)
        except FileExistsError:
            require(record(output) == before, "occupied preflight changed file")
            preflight_checks.append(label)
        else:
            raise ValueError("occupied preflight accepted output")

    class AbsentOutput:
        def exists(self):
            return False

    try:
        namespace["run"](Path(__file__), AbsentOutput())
    except ValueError as error:
        require("source digest mismatch" in str(error), "wrong input-hash rejection")
        preflight_checks.append("wrong_input_hash_before_method_load")
    else:
        raise ValueError("wrong input hash accepted")

    frozen = load(DOC / "controls01/frozen-packet.json")
    require(frozen["file_count"] == 4 and frozen["bytes"] == 56410, "frozen packet ownership record differs")
    require({Path(r["path"]).name: {"bytes": r["bytes"], "sha256": r["sha256"]} for r in frozen["files"]} == target, "retention artifact map differs")
    retained = {}
    retain_names = ["controls01/frozen-packet.json", "controls01/receipt.json", "controls01/replayed.json", "attempt01/failure.json", "attempt01/source-at-run.py", "attempt02/source-at-run.py", "attempt02/result.json", "attempt03/source-at-run.py", "attempt03/result.json"]
    require((DOC / "controls01/receipt.json").read_bytes() == (DOC / "verification.json").read_bytes(), "issued verification/raw receipt differs")
    require((DOC / "controls01/replayed.json").read_bytes() == (DOC / "result.json").read_bytes(), "retained exact replay differs")
    require(len(verification["controls"]) == 7 and verification["passed"] is verification["source_bindings_unchanged_after"] is True, "seven saved controls differ")
    for control in verification["controls"]:
        require(control["passed"] is True, "saved control failed")
        name = "controls01/" + control["name"] + ".json"
        retain_names.append(name)
        raw = load(DOC / name)
        expected_success = control["name"] == "fresh_exact_replay" or control["name"].startswith("source_drift_or_late_output_")
        require((raw["returncode"] == 0) == expected_success, "saved control exit claim differs")
    failure = load(DOC / "attempt01/failure.json")
    require(failure["no_result_written"] is True and failure["status"] == "rejected_before_calculation", "failed attempt status relabeled")
    require(failure["helper_sha256"] == record(DOC / "attempt01/source-at-run.py")["sha256"], "failed source snapshot differs")
    for attempt in ["attempt02", "attempt03"]:
        old_result = load(DOC / attempt / "result.json")
        producer_pin = next(sha for p, sha in old_result["source_bindings"].items() if p.endswith("check_current.py"))
        require(producer_pin == record(DOC / attempt / "source-at-run.py")["sha256"], "intermediate source/result join differs")
    for name in retain_names:
        retained[name] = record(DOC / name)
    require(not (DOC / "controls01/before/result.json").exists() and not (DOC / "controls01/during/result.json").exists() and not (DOC / "controls01/bad-result.json").exists(), "rejected own output retained as a successful result")
    require((DOC / "controls01/race/result.json").read_bytes() == b"other-writer\n", "late existing output overwritten")
    summary = result["summary"]
    require(summary["case_count"] == summary["compression_feasible_case_count"] == 7, "saved summary count differs")
    require(len(result["cases"]) == verification["numerical_check"]["case_count"] == 7 and verification["numerical_check"]["polygon_vertex_count"] == 6, "saved case/hull count differs")
    require(math.isclose(summary["minimum_edge_margin_mm"], 330.28499147990897, abs_tol=1e-10), "saved minimum margin differs")
    require(result["fixtures"] == {"known_answer_fixture_count": 7, "passed": True}, "saved fixtures claim differs")
    require({name: record(DOC / name) for name in EXPECTED} == target, "target changed during source review")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in verification_pins.items()), "direct source changed during source review")
    require(all(record(ROOT / p) == ref for p, ref in context.items()), "context changed during source review")
    require(all(record(DOC / name) == ref for name, ref in retained.items()), "retained evidence changed during source review")

    receipt = {
        "schema": "eoere_current_global_statics_architecture_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_ARCHITECTURE_SOURCE_OR_RETENTION_FINDINGS",
        "findings": [],
        "review_helper": record(Path(__file__)),
        "target": {"path": relative(DOC), "files": target, "bytes": 56410},
        "current_context": context,
        "direct_source_bindings_authenticated_before_after": direct,
        "recursive_input_pins": {"declared": 1086, "independently_rehashed_here": False, "source_or_method_admission": False},
        "checks": {"captured_authenticated_legacy_source_reused": True, "legacy_method_calls": dict(calls), "old_input_fields_consumed": sorted(old_fields), "preserved_known_answer_fixture_count_source_contract": 7, "pure_source_validator": "PASS", "source_only_negative_gate_checks": 3, "inert_preflight_checks": preflight_checks, "current_support_points": 32, "identical_old_support_points": 28, "translated_right_post_points": 4, "source_mass_kg": mass["total_kg"], "saved_seven_controls_and_seven_decimal_checks_bound": True, "saved_minimum_margin_mm": summary["minimum_edge_margin_mm"], "no_result_or_input_relabeling": True},
        "retained_attempt_and_control_hashes": retained,
        "architecture_assessment": [
            {"evidence": "check_current.py:83-228,253-301; global_statics.py:24-87", "assessment": "The current wrapper owns input validation and composition; the unchanged shared method owns the global compression calculation and seven fixtures. It compiles the captured METHOD_SHA bytes rather than rereading an import path, calls no legacy run(), and uses old input only for footprint/hull comparison. No duplicate mechanics implementation or copied dependency tree."},
            {"evidence": "check_current.py:240-267,302-355; result.json:source_bindings,input_readiness_preserved,limitations", "assessment": "Eight direct pins bind the current source-load descriptor, geometry report/cache/manifest, shared method, legacy footprint input, wrapper and lockfile. The 1,086 recursive pins are explicitly declared without admission. Source-only pending flags and false release values survive unchanged. New records supply no old-field relabeling, elastic reactions, friction/no-slip capacity, floor or joint resistance."},
            {"evidence": "check_current.py:231-237,359-369; verify.py:179-215,219-304", "assessment": "Producer output requires absence and exclusive creation, with source checks before/after writing. Only its newly created invalid output is removed on write-time failure. The verifier owns a fresh directory, retains command/stdout/stderr evidence before checking exits, and confines mutations to copied helpers. Existing/raced outputs are preserved. Frozen results are never overwritten."},
            {"evidence": "controls01/frozen-packet.json; attempt01/failure.json; attempt02/result.json; attempt03/result.json", "assessment": "The rejected footprint-equality attempt and intermediate results retain their own source snapshots and identities. The four-file packet is 56,410 bytes; existing inputs, observations, method, dependencies and old response assets are referenced. Retained raw attempts/control records remain active, with no pruning authority inferred."}
        ],
        "limits": [
            "Source-only architecture/ownership/retention review; the preserved global statics method, its LP/hull computation, frame/native/CAD/BREP and browser execution were not run.",
            "Pure current-input validation and early output/hash rejections were exercised via AST-extracted definitions; all mathematical global-result claims are reused from frozen source-bound producer evidence, not independent mechanical qualification.",
            "No recursive current-input admission, compatible elastic reactions, physical floor/no-slip/friction qualification, complete joint resistance, fabrication or climbing approval. Parent owns final validation/publication."
        ],
        "source_and_target_unchanged": True,
        "shared_edits_staging_commits": False,
        "reproduce_review": "python3 -B " + relative(Path(__file__))
    }
    raw = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (OWN / "receipt.json").write_bytes(raw)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": digest(raw), "receipt_bytes": len(raw), "review_helper_sha256": receipt["review_helper"]["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
