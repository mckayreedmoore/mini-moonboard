"""Independent bounded correctness verification of frozen path-boundary v3."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
METHOD = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1")
V3 = METHOD / "evidence-correction-v1/review-fix-v2/path-boundary-v3"
ISSUED = BASE / "evidence-correction-v1/review-fix-v2/path-boundary-v3/attempt02"
MAP = ISSUED / "frozen-packet.json"
MAP_SHA = "4acc36d1b238177ed8f5cca62397a6d5d52eedb247d5b43b28ae870f1d5dd467"
NAMES = ("result.json", "details.json", "run-provenance.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load(path):
    spec = importlib.util.spec_from_file_location("independent_v3_path_boundary", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(arguments):
    process = subprocess.run([sys.executable, "-B", *map(str, arguments)], cwd=ROOT, capture_output=True, text=True, check=False)
    return {"returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr}


def main():
    assert sha((ROOT / MAP).read_bytes()) == MAP_SHA
    target = read(ROOT / MAP)
    assert len(target) == 5 and sum(pin["bytes"] for pin in target.values()) == 35903
    for path, pin in target.items():
        data = (ROOT / path).read_bytes()
        assert len(data) == pin["bytes"] and sha(data) == pin["sha256"]
    compact = read(ROOT / V3 / "verification.json")
    paths = set(compact["source_sha256"]) | set(target) | {str(MAP)}
    paths.update(row["path"] for row in compact["raw_evidence"])
    paths.update(str(ISSUED / side / name) for side in ("fresh-run", "fresh-replay") for name in NAMES)
    before = {path: sha((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert all(before[path] == pin for path, pin in compact["source_sha256"].items())
    assert all(before[row["path"]] == row["sha256"] and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in compact["raw_evidence"])
    wrapper = load(ROOT / V3 / "run.py")
    engine = wrapper._engine()
    state = engine.snapshot()
    assert len(state["pins"]) == 34 and state["pins"] == compact["source_sha256"]
    original = ROOT / ISSUED / "fresh-run"
    result, details = read(original / "result.json"), read(original / "details.json")
    analysis, checker = engine.load_original(state, "analyze.py"), engine.load_original(state, "verify.py")
    claims = engine.validate_compact(result, details, state, analysis)
    integrated = checker.check(result, details, state["inputs"])
    assert claims == {"candidate_inputs_used": False, "candidate_joint_capacity": None, "capacity_or_pass_claim": False}
    probes = [{"name": "frozen_34_source_closure_and_45_fields", "status": "PASS", "validated_claims": claims, "independent_checks": integrated}]

    with tempfile.TemporaryDirectory(prefix="v3-boundary-correctness-") as temporary:
        temp = Path(temporary)
        api_cases = []
        original_engine_factory = wrapper._engine

        def fail_if_loaded():
            raise AssertionError("Public parent-path rejection reached engine loading")

        wrapper._engine = fail_if_loaded
        try:
            for function, arguments in ((wrapper.produce, [temp / "new"]), (wrapper.verify, [original, ROOT / ISSUED / "fresh-replay", temp / "receipt.json"])):
                for position in range(len(arguments)):
                    for parent in ("../run", "child/../run", "run/.."):
                        supplied = arguments.copy()
                        supplied[position] = parent
                        try:
                            function(*supplied)
                        except ValueError as error:
                            assert "Parent component '..'" in str(error)
                        else:
                            raise AssertionError("Public API accepted parent component")
                        api_cases.append({"boundary": "public", "function": function.__name__, "position": position, "path": parent})
        finally:
            wrapper._engine = original_engine_factory
        for function, arguments in ((engine.produce, [temp / "new"]), (engine.verify, [original, ROOT / ISSUED / "fresh-replay", temp / "receipt.json"])):
            for position in range(len(arguments)):
                supplied = arguments.copy()
                supplied[position] = temp / "child/../run"
                try:
                    function(*supplied)
                except ValueError as error:
                    assert "Parent component '..'" in str(error)
                else:
                    raise AssertionError("Reused engine API accepted parent component")
                api_cases.append({"boundary": "reused_engine", "function": function.__name__, "position": position, "path": "child/../run"})
        assert not (temp / "new").exists() and not (temp / "receipt.json").exists()
        probes.append({"name": "all_public_and_reused_api_argument_positions", "status": "PASS", "rejections": api_cases, "public_rejected_before_engine_loading": True})

        ordinary = cli([ROOT / V3 / "run.py", "verify", f"--run=./{ISSUED / 'fresh-run'}", "--replay", ISSUED / "fresh-replay", "--out", temp / "relative-receipt.json"])
        assert ordinary["returncode"] == 0 and (temp / "relative-receipt.json").is_file(), ordinary
        probes.append({"name": "ordinary_relative_paths_and_dot_prefix_actual_cli", "status": "PASS", "process": ordinary})

        controlled = cli([ROOT / V3 / "check.py", "regress", "--out", temp / "controls"])
        assert controlled["returncode"] == 0, controlled
        regression = read(temp / "controls/regressions.json")
        assert regression["status"] == "ALL_PARENT_PATH_CONTROLS_PASS"
        assert len(regression["commands"]) - 3 == 7
        assert regression["fresh_three_file_replay_byte_identical"] and regression["numeric_result_and_fields_match_original"]
        for name in NAMES:
            assert (temp / "controls/fresh-run" / name).read_bytes() == (original / name).read_bytes()
        probes.append({"name": "two_fresh_productions_exact_replay_and_seven_cli_controls", "status": "PASS", "process": controlled, "commands": regression["commands"], "four_existing_api_controls": regression["API_parent_path_controls_rejected"], "all_three_production_files_match_issued": True})

        drift_records = []
        for kind in ("run.py", "inputs.json"):
            fixture = temp / ("loaded-" + kind)
            fixture.mkdir()
            (fixture / "current-candidate.json").write_bytes((ROOT / "current-candidate.json").read_bytes())
            for path, data in state["contents"].items():
                target_path = fixture / path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(data)
            fixture_run = fixture / V3 / "run.py"
            script = '''import importlib.util,sys
from pathlib import Path
path=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("loaded_v3",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
changed=path.parent/sys.argv[2]
changed.write_bytes(changed.read_bytes()+b"\\n")
module.produce(Path(sys.argv[3]))
'''
            record = cli(["-c", script, fixture_run, kind, fixture / "rejected-output"])
            assert record["returncode"] != 0 and "Loaded supplement/source changed:" in record["stderr"] and not (fixture / "rejected-output").exists(), record
            drift_records.append({"source": kind, "process": record, "output_created": False})
        probes.append({"name": "loaded_v3_source_and_input_drift_rejected", "status": "PASS", "controls": drift_records})

    after = {path: sha((ROOT / path).read_bytes()) for path in sorted(paths)}
    assert before == after, "Reviewed or issued files changed"
    receipt = {"schema": "independent_synthetic_path_boundary_v3_correctness_review/v1", "frozen_packet_map_sha256": MAP_SHA, "scope": "Frozen parent-path correction; preserved synthetic scalar mechanics and null candidate capacity only", "read_other_review_findings": False, "source_and_issued_sha256_before": before, "source_and_issued_sha256_after": after, "unchanged": True, "probes": probes, "findings": []}
    destination = Path(__file__).with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": "REVIEW_COMPLETE", "findings": 0, "probes": len(probes), "unchanged": True, "receipt": str(destination.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
