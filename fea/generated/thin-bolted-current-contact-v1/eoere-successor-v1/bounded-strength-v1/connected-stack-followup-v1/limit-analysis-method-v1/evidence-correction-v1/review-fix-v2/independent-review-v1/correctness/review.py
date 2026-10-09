"""Independent correctness review of the frozen v2 synthetic evidence correction."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
METHOD = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
V2 = METHOD / "evidence-correction-v1/review-fix-v2"
ISSUED = BASE / "evidence-correction-v1/review-fix-v2/attempt02"
MAP = ISSUED / "frozen-packet.json"
MAP_SHA = "1d214a9a31f37cdaf358a58daba2d143baf79e22787677516e8b6251933f83ce"
NAMES = ("result.json", "details.json", "run-provenance.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load(path):
    spec = importlib.util.spec_from_file_location("independent_v2_launcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(arguments):
    completed = subprocess.run([sys.executable, "-B", *map(str, arguments)], cwd=ROOT, capture_output=True, text=True, check=False)
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def main():
    assert sha((ROOT / MAP).read_bytes()) == MAP_SHA
    target = read(ROOT / MAP)
    for path, pin in target.items():
        data = (ROOT / path).read_bytes()
        assert len(data) == pin["bytes"] and sha(data) == pin["sha256"]
    verification = read(ROOT / V2 / "verification.json")
    paths = set(verification["source_sha256"]) | set(target) | {str(MAP)}
    paths.update(row["path"] for row in verification["raw_evidence"])
    paths.update(str(ISSUED / side / name) for side in ("fresh-run", "fresh-replay") for name in NAMES)
    before = {path: sha((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert all(before[path] == pin for path, pin in verification["source_sha256"].items())
    assert all(before[row["path"]] == row["sha256"] and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in verification["raw_evidence"])

    body = load(ROOT / V2 / "run.py").load_body()
    legacy = body.prepare()
    state = legacy.snapshot()
    assert len(state["pins"]) == 26
    assert state["pins"] == verification["source_sha256"]
    analysis = legacy.load_original(state, "analyze.py")
    checker = legacy.load_original(state, "verify.py")
    original = ROOT / ISSUED / "fresh-run"
    result, details = read(original / "result.json"), read(original / "details.json")
    claims = legacy.validate_compact(result, details, state, analysis)
    independent = checker.check(result, details, state["inputs"])
    assert claims == {"candidate_inputs_used": False, "candidate_joint_capacity": None, "capacity_or_pass_claim": False}
    probes = [{"name": "frozen_26_source_closure_and_45_raw_scaled_fields", "status": "PASS", "independent_checks": independent, "validated_claims": claims}]
    scale_bounds = []
    for case, row in zip(state["inputs"]["published_cases"] + state["inputs"]["synthetic_cases"], result["cases"]):
        limits = state["inputs"]["limits"]
        force = min(case["main_length_in"] * case["main_bearing_lb_in"], case["side_length_in"] * case["side_bearing_lb_in"])
        length = case["main_length_in"] + case["side_length_in"] + case["gap_in"]
        cap = case["yield_moment_lb_in"] / (force * length)
        minimum = (1 - limits["numerical_feasible_scale_margin"]) * min(1 / (1 + limits["scaled_LP_residual_tolerance"]), cap / (cap + limits["moment_cut_tolerance"]))
        assert all(grid["numerical_feasibility_scale"] >= minimum - limits["numerical_feasible_scale_margin"] for grid in row["grids"])
        scale_bounds.append({"case": case["id"], "necessary_scale_lower_bound": minimum, "minimum_recorded_scale": min(grid["numerical_feasibility_scale"] for grid in row["grids"])})
    probes.append({"name": "all_coupon_scale_bound_derivations", "status": "PASS", "bounds": scale_bounds})

    with tempfile.TemporaryDirectory(prefix="v2-correction-correctness-") as temporary:
        temp = Path(temporary)
        controls = cli([ROOT / V2 / "check.py", "regress", "--out", temp / "controls"])
        assert controls["returncode"] == 0, controls
        regression = read(temp / "controls/regressions.json")
        assert regression["status"] == "ALL_TARGETED_REGRESSIONS_PASS"
        assert len(regression["commands"]) - 3 == 14
        probes.append({"name": "fresh_production_replay_and_all_14_actual_cli_controls", "status": "PASS", "process": controls, "three_file_replay": regression["three_file_byte_identical_fresh_replay"], "numerical_bytes_unchanged": regression["result_and_fields_match_original_issued_bytes"], "commands": regression["commands"]})

        def copy_run(destination):
            destination.mkdir(parents=True)
            for name in NAMES:
                (destination / name).write_bytes((original / name).read_bytes())

        base, actual, bad = temp / "base", temp / "actual", temp / "bad"
        base.mkdir()
        (actual / "gateway").mkdir(parents=True)
        (bad / "gateway").mkdir(parents=True)
        for target_path in (base / "run", actual / "run", bad / "run"):
            copy_run(target_path)
        altered = copy.deepcopy(result)
        altered["candidate_inputs_used"] = True
        (bad / "run/result.json").write_bytes(legacy.encoded(altered))
        link = base / "hidden"
        link.symlink_to(actual / "gateway", target_is_directory=True)
        supplied = base / "hidden/../run"
        assert Path(os.path.abspath(supplied)) == base / "run"
        assert supplied.resolve() == actual / "run"
        direct = cli([ROOT / V2 / "run.py", "verify", "--run", supplied, "--replay", ROOT / ISSUED / "fresh-replay", "--out", temp / "dotdot-cli-receipt.json"])
        assert direct["returncode"] == 0 and (temp / "dotdot-cli-receipt.json").is_file(), direct
        probes.append({"name": "symlink_hidden_by_parent_traversal_actual_cli", "status": "CONFIRMED_ACCEPTANCE", "supplied_path": "base/hidden/../run", "normalized_guard_path": "base/run", "actual_read_path": "actual/run", "process": direct})

        encoded = legacy.encoded

        def retarget_on_serialization(value):
            data = encoded(value)
            if type(value) is dict and value.get("schema") == "synthetic_limit_corrected_verification/v1":
                link.unlink()
                link.symlink_to(bad / "gateway", target_is_directory=True)
            return data

        legacy.encoded = retarget_on_serialization
        try:
            accepted = legacy.verify(supplied, ROOT / ISSUED / "fresh-replay", temp / "retarget-receipt.json")
        finally:
            legacy.encoded = encoded
        assert accepted["status"] == "VERIFIED_SYNTHETIC_ONLY"
        assert accepted["validated_claims"]["candidate_inputs_used"] is False
        assert read(supplied / "result.json")["candidate_inputs_used"] is True
        probes.append({"name": "hidden_symlink_retarget_during_receipt_serialization", "status": "CONFIRMED_ACCEPTANCE", "receipt_created": (temp / "retarget-receipt.json").is_file(), "current_supplied_run_candidate_inputs_used": True, "receipt_validated_candidate_inputs_used": False})

    after = {path: sha((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert before == after, "Reviewed or issued evidence changed"
    receipt = {"schema": "independent_synthetic_correction_v2_correctness_review/v1", "frozen_packet_map_sha256": MAP_SHA, "scope": "Frozen synthetic-only numerical/evidence correction; no candidate, physical, CAD, native, global frame or capacity work", "read_other_review_findings": False, "source_and_issued_sha256_before": before, "source_and_issued_sha256_after": after, "unchanged": True, "probes": probes, "findings": [{"priority": "P2", "path": str(V2 / "body.py"), "line": 36, "title": "Parent traversal hides symlink components from evidence guards", "impact": "The actual verify CLI accepts link/../run, and retargeting its hidden symlink during receipt serialization bypasses both lexical and legacy resolved-path checks.", "fix": "Reject parent traversal components before normalization, or inspect every component using filesystem traversal semantics; add CLI and serialization-time regression controls."}]}
    destination = Path(__file__).with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": "REVIEW_COMPLETE", "confirmed_findings": 1, "probes": len(probes), "unchanged": True, "receipt": str(destination.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
