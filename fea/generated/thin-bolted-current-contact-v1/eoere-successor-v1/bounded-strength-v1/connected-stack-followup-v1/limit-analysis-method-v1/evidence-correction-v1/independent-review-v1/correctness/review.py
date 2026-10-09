"""Independent synthetic correction correctness probes; no candidate mechanics."""

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
CORRECTION = DOC / "evidence-correction-v1"
ISSUED = BASE / "evidence-correction-v1/attempt01"
FROZEN_MAP = ISSUED / "frozen-packet.json"
EXPECTED_MAP_SHA256 = "ace9ab9d51c7f6320fb87be5f88329299f38b4bde5e7f1a9f2f0d77e98d2d371"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(arguments):
    completed = subprocess.run([sys.executable, "-B", *map(str, arguments)], cwd=ROOT, capture_output=True, text=True, check=False)
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def main():
    assert digest((ROOT / FROZEN_MAP).read_bytes()) == EXPECTED_MAP_SHA256
    target_map = read_json(ROOT / FROZEN_MAP)
    correction = load(ROOT / CORRECTION / "correction.py", "independent_correction_review")
    state = correction.snapshot()
    paths = set(state["pins"]) | set(target_map) | {str(FROZEN_MAP)}
    raw_verification = read_json(ROOT / CORRECTION / "verification.json")
    paths.update(row["path"] for row in raw_verification["raw_evidence"])
    paths.update(str(ISSUED / side / name) for side in ("fresh-run", "fresh-replay") for name in ("result.json", "details.json", "run-provenance.json"))
    before = {path: digest((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert all(before[path] == sha for path, sha in state["pins"].items())
    assert all(before[path] == info["sha256"] and (ROOT / path).stat().st_size == info["bytes"] for path, info in target_map.items())
    assert all(before[row["path"]] == row["sha256"] and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in raw_verification["raw_evidence"])
    probes = []
    original = ROOT / ISSUED / "fresh-run"
    result = read_json(original / "result.json")
    details = read_json(original / "details.json")
    provenance = read_json(original / "run-provenance.json")
    analysis = correction.load_original(state, "analyze.py")
    checker = correction.load_original(state, "verify.py")
    assert correction.validate_compact(result, details, state, analysis) == {"candidate_inputs_used": False, "candidate_joint_capacity": None, "capacity_or_pass_claim": False}
    independent = checker.check(result, details, state["inputs"])
    probes.append({"name": "frozen_schema_formulas_and_dimensional_fields", "status": "PASS", "source_closure_count": len(state["pins"]), "checks": independent})

    with tempfile.TemporaryDirectory(prefix="limit-correction-correctness-") as temporary:
        temp = Path(temporary)
        clean = run([ROOT / CORRECTION / "correction.py", "verify", "--run", original, "--replay", ROOT / ISSUED / "fresh-replay", "--out", temp / "clean.json"])
        assert clean["returncode"] == 0, clean
        probes.append({"name": "issued_actual_cli_verification", "status": "PASS", "process": clean})

        forged = copy.deepcopy(result)
        grid = forged["cases"][0]["grids"][0]
        original_raw, original_scale = grid["raw_LP_load_lbf"], grid["numerical_feasibility_scale"]
        grid["raw_LP_load_lbf"] *= 1_000_000
        grid["numerical_feasibility_scale"] /= 1_000_000
        forged_data = correction.encoded(forged)
        forged_provenance = copy.deepcopy(provenance)
        forged_provenance["output_sha256"]["result.json"] = digest(forged_data)
        for side in ("forged-run", "forged-replay"):
            directory = temp / side
            directory.mkdir()
            (directory / "result.json").write_bytes(forged_data)
            (directory / "details.json").write_bytes((original / "details.json").read_bytes())
            (directory / "run-provenance.json").write_bytes(correction.encoded(forged_provenance))
        forged_cli = run([ROOT / CORRECTION / "correction.py", "verify", "--run", temp / "forged-run", "--replay", temp / "forged-replay", "--out", temp / "forged-receipt.json"])
        assert forged_cli["returncode"] == 0 and (temp / "forged-receipt.json").is_file(), forged_cli
        probes.append({"name": "coordinated_raw_load_and_feasibility_scale_forgery", "status": "CONFIRMED_ACCEPTANCE", "original_raw_LP_load_lbf": original_raw, "forged_raw_LP_load_lbf": grid["raw_LP_load_lbf"], "original_scale": original_scale, "forged_scale": grid["numerical_feasibility_scale"], "unchanged_scaled_load_lbf": grid["scaled_statics_load_lbf"], "frozen_main_bearing_force_upper_bound_lbf": state["inputs"]["published_cases"][0]["main_length_in"] * state["inputs"]["published_cases"][0]["main_bearing_lb_in"], "process": forged_cli})

        bad_target = temp / "bad-evidence"
        bad_target.mkdir()
        bad_result = copy.deepcopy(result)
        bad_result["candidate_inputs_used"] = True
        (bad_target / "result.json").write_bytes(correction.encoded(bad_result))
        for name in ("details.json", "run-provenance.json"):
            (bad_target / name).write_bytes((original / name).read_bytes())
        link = temp / "logical-run"
        link.symlink_to(original, target_is_directory=True)
        encoded = correction.encoded

        def retarget_on_serialization(value):
            data = encoded(value)
            if type(value) is dict and value.get("schema") == "synthetic_limit_corrected_verification/v1":
                link.unlink()
                link.symlink_to(bad_target, target_is_directory=True)
            return data

        correction.encoded = retarget_on_serialization
        try:
            accepted = correction.verify(link, ROOT / ISSUED / "fresh-replay", temp / "retarget-receipt.json")
        finally:
            correction.encoded = encoded
        assert accepted["status"] == "VERIFIED_SYNTHETIC_ONLY"
        assert read_json(link / "result.json")["candidate_inputs_used"] is True
        probes.append({"name": "post_consumption_evidence_directory_symlink_retarget", "status": "CONFIRMED_ACCEPTANCE", "receipt_created": (temp / "retarget-receipt.json").is_file(), "current_logical_run_candidate_inputs_used": True, "receipt_validated_candidate_inputs_used": accepted["validated_claims"]["candidate_inputs_used"]})

        fixture = temp / "source-fixture"
        fixture.mkdir()
        (fixture / "current-candidate.json").write_bytes((ROOT / "current-candidate.json").read_bytes())
        for path, data in state["contents"].items():
            destination = fixture / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        source = fixture / CORRECTION / "correction.py"
        wrapper = '''import importlib.util,sys
from pathlib import Path
source=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("loaded_before_change",source)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source.write_bytes(b"raise RuntimeError('source changed after module loading')\\n"+source.read_bytes())
sys.argv=[str(source),"produce","--out",sys.argv[2]]
module.main()
'''
        stale = run(["-c", wrapper, source, fixture / "produced"])
        assert stale["returncode"] == 0, stale
        emitted = read_json(fixture / "produced/run-provenance.json")
        changed_source_hash = digest(source.read_bytes())
        assert emitted["source_sha256"][str(CORRECTION / "correction.py")] == changed_source_hash
        fresh = run([source, "verify", "--run", fixture / "produced", "--replay", fixture / "produced", "--out", fixture / "fresh-check.json"])
        assert fresh["returncode"] != 0 and "source changed after module loading" in fresh["stderr"], fresh
        probes.append({"name": "executed_correction_source_changes_before_snapshot", "status": "CONFIRMED_MISATTRIBUTION", "old_loaded_code_production": stale, "success_marker_binds_unexecuted_source": True, "fresh_execution_of_recorded_source": fresh})

    after = {path: digest((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert before == after, "Reviewed or issued bytes changed"
    receipt = {"schema": "independent_synthetic_correction_correctness_review/v1", "review_target_map_sha256": EXPECTED_MAP_SHA256, "scope": "Frozen synthetic correction only; no candidate, CAD, native, current forces, capacities or physical actions", "read_other_review_findings": False, "source_and_issued_sha256_before": before, "source_and_issued_sha256_after": after, "unchanged": True, "probes": probes}
    output = Path(__file__).with_name("receipt.json")
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "probes": len(probes), "confirmed_gaps": 3, "unchanged": True}, sort_keys=True))


if __name__ == "__main__":
    main()
