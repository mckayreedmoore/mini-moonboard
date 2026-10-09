"""Independent stdlib testing review; frozen analyses and historical stdin are never run."""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path.cwd()
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1"
GUARD = DOC / "revised-base-audit-v1/reproduction-guard-v1"
OWN = Path(__file__).resolve().parent
PRIOR = OWN.parents[1] / "testing"


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


def bind(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rejects(operation, error_type, message=None):
    try:
        operation()
    except error_type as error:
        if message is not None:
            require(message in str(error), "unexpected rejection: " + str(error))
        return type(error).__name__
    raise ValueError("expected rejection did not occur")


def snapshot_directory(directory):
    return {str(path.relative_to(directory)): sha(path) for path in directory.rglob("*") if path.is_file()}


def run_checks(guard, inputs, temporary):
    observed = {}
    for script, filename in (("check_guard.py", "guard-controls.json"), ("check_evidence.py", "verification-supplement.json")):
        output = temporary / script.removesuffix(".py")
        command = [sys.executable, "-B", "-S", str(GUARD / script), "--out", str(output)]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        require(completed.returncode == 0, f"{script} failed: {completed.stderr}")
        require(completed.stderr == "", f"{script} emitted stderr")
        value = read(output / filename)
        observed[script] = {"command": command, "stdout": completed.stdout, "receipt": value, "receipt_sha256": sha(output / filename)}
    controls = observed["check_guard.py"]["receipt"]
    require(controls["control_count"] == 14 == len(set(controls["passed_controls"])), "fourteen distinct controls")
    require(controls["both_issued_source_closures_verified_before_after"] == [1120, 1126], "issued source closures")
    require(controls["real_full_analysis_executed"] is False, "original analysis must not run")
    evidence = observed["check_evidence.py"]["receipt"]
    require(evidence["supplement_pin_count"] == 1147, "supplement closure count")
    require(len(evidence["negative_controls_rejected"]) == 4, "four evidence corruptions")
    require(evidence["intervals"]["new_independent_BREP_read"] is False, "saved CAD proof reuse")
    require(evidence["washers"]["new_independent_CAD_intersections"] is False, "saved washer proof reuse")
    require(evidence["historical_provenance"]["historical_command_executed_by_supplement"] is False, "historical stdin must not run")
    require(evidence == read(GUARD / "result.json")["evidence_supplement"], "evidence receipt exact reproduction")
    require(controls == read(GUARD / "result.json")["guard_controls"], "guard receipt exact reproduction")
    return observed


def independent_controls(guard, inputs, temporary):
    passed = []
    source = temporary / "independent-source.txt"
    source.write_text("fixture source\n")
    pins = {str(source): sha(source)}
    counts = {"before": 0, "calculate": 0, "after": 0}

    def before():
        counts["before"] += 1
        guard.verify(pins)
        return {"pins": pins, "issued_pin_count": 1, "issued_closure_canonical_sha256": guard.canonical(pins), "guarded_pin_count": 1, "guarded_closure_canonical_sha256": guard.canonical(pins)}

    def after(snapshot):
        counts["after"] += 1
        guard.verify(snapshot["pins"])

    def calculate():
        counts["calculate"] += 1
        return {"scope": "REVIEW_STDLIB_STUB_ONLY", "answer": 42}, {"rows": [1, 2, 3]}

    def run(output, producer=calculate, compare=None, final=after):
        return guard.guarded_calculation(output, before, producer, final, {"review_stub_only": True}, compare)

    good = temporary / "verified-positive"
    provenance = run(good)
    for name, expected in (("result.json", calculate()[0]), ("details.json", calculate()[1])):
        require((good / name).read_bytes() == guard.serialized(expected), "actual output serialization")
        require(provenance["output_files"][name]["sha256"] == sha(good / name), "actual output hash")
        require(provenance["output_files"][name]["bytes"] == (good / name).stat().st_size, "actual output size")
    require(read(good / "run-provenance.json") == provenance, "provenance bytes")
    passed.append("successful_stub_checks_actual_JSON_bytes_and_provenance_hashes")

    same_result = temporary / "comparison-details-mismatch-source"
    same_result.mkdir()
    (same_result / "result.json").write_bytes((good / "result.json").read_bytes())
    (same_result / "details.json").write_text("different details\n")
    mismatch = temporary / "comparison-details-mismatch"
    rejects(lambda: run(mismatch, compare=same_result), ValueError, "details.json")
    require(not list(mismatch.iterdir()), "details mismatch wrote output")
    passed.append("details_comparison_mismatch_rejects_before_any_output")

    missing = temporary / "comparison-missing-details-source"
    missing.mkdir()
    (missing / "result.json").write_bytes((good / "result.json").read_bytes())
    failed = temporary / "comparison-missing-details"
    rejects(lambda: run(failed, compare=missing), FileNotFoundError)
    require(not list(failed.iterdir()), "missing comparison wrote output")
    passed.append("missing_comparison_file_leaves_reserved_empty_output")

    nonfinite = temporary / "nonfinite"
    rejects(lambda: run(nonfinite, lambda: ({"nonfinite": float("nan")}, {})), ValueError)
    require(not list(nonfinite.iterdir()), "nonfinite result wrote output")
    passed.append("nonfinite_result_serialization_fails_before_writes")

    protected = temporary / "protected-existing-file.txt"
    protected.write_text("preserved fixture bytes\n")
    for collision_name in ("result.json", "details.json", "run-provenance.json"):
        output = temporary / ("collision-" + collision_name)

        def plant_collision(output=output, collision_name=collision_name):
            (output / collision_name).symlink_to(protected)
            return calculate()

        rejects(lambda: run(output, plant_collision), FileExistsError)
        require(protected.read_text() == "preserved fixture bytes\n", "exclusive creation followed file symlink")
        require((output / collision_name).is_symlink(), "collision link replaced")
        if collision_name != "run-provenance.json":
            require(not (output / "run-provenance.json").exists(), "partial outputs claim success")
        passed.append("exclusive_" + collision_name + "_symlink_collision_preserves_existing_target")

    postwrite = temporary / "changed-after-output"

    def change_after(snapshot):
        if (postwrite / "details.json").exists():
            source.write_text("changed at output authentication\n")
        after(snapshot)

    rejects(lambda: run(postwrite, final=change_after), ValueError, "changed source")
    require((postwrite / "result.json").is_file() and (postwrite / "details.json").is_file(), "expected partial output retained")
    require(not (postwrite / "run-provenance.json").exists(), "changed source published success provenance")
    source.write_text("fixture source\n")
    passed.append("postwrite_source_change_rejects_success_provenance_and_keeps_failed_attempt")

    barrier = threading.Barrier(2)
    race_output = temporary / "shared-race-output"
    race_count = counts["calculate"]

    def racer():
        barrier.wait(timeout=10)
        try:
            run(race_output)
        except FileExistsError:
            return "already_reserved"
        return "success"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(lambda _: racer(), (0, 1)))
    require(outcomes == ["already_reserved", "success"], "same output reservation race")
    require(counts["calculate"] == race_count + 1, "racing duplicate reached calculation")
    require(read(race_output / "run-provenance.json")["status"] == "VERIFIED_FRESH_OUTPUT", "race winner output")
    passed.append("two_concurrent_calls_same_output_allow_exactly_one_calculation")

    original_loader = guard.load_analysis
    imports = []

    def stub_loader(path, packet):
        require(path == inputs["packets"][packet]["analysis"]["path"], "selected frozen analysis identity")
        imports.append(packet)
        return SimpleNamespace(run=lambda: ({"scope": "REVIEW_STDLIB_EXECUTE_STUB", "packet": packet}, {"rows": []}))

    guard.load_analysis = stub_loader
    try:
        for packet in ("audit", "connected"):
            output = temporary / ("execute-stub-" + packet)
            result = guard.execute(packet, output)
            require(result["issued_pin_count"] == inputs["packets"][packet]["issued_pin_count"], "execute authenticates issued closure")
            require(read(output / "result.json")["packet"] == packet, "execute selected stub result")
            require(result["packet"]["guard_inputs"]["sha256"] == sha(GUARD / "inputs.json"), "execute guard input provenance")
            require(result["packet"]["issued_details"] == inputs["packets"][packet]["details"], "execute issued details provenance")
            require(result["packet"]["expected_analysis_sha256"] == guard.EXPECTED_ANALYSES[packet], "execute frozen analysis provenance")
            rejects(lambda: guard.execute(packet, output), FileExistsError)
        require(imports == ["audit", "connected"], "existing output imports analysis")
    finally:
        guard.load_analysis = original_loader
    passed.append("both_execute_paths_authenticate_real_closures_with_only_stub_analysis_loader")
    return passed


def main():
    require(not (OWN / "receipt.json").exists(), "independent receipt already exists")
    fixed_hashes = {"verification.json": "010fb293bc0b7dead3821e66f9923c0a7a942438e09545cec0dd36e7c8044ae5", "result.json": "b48c1ba300e161a729ffa9f9cbcabe75b44126488e376eea0154e7bf7b8d71a7", "run_fresh.py": "53fe84d33b19d184c79e07e3a007f29ca40c7b96d3eea9a80d487c0a48f53bb5"}
    for filename, digest in fixed_hashes.items():
        require(sha(GUARD / filename) == digest, "frozen target differs: " + filename)
    verification = read(GUARD / "verification.json")
    for record in verification["owned_artifacts"].values():
        require(sha(ROOT / record["path"]) == record["sha256"], "supplement owned artifact binding")
        require((ROOT / record["path"]).stat().st_size == record["bytes"], "supplement owned artifact size")
    for record in verification["raw_receipts"]:
        require(sha(ROOT / record["path"]) == record["sha256"], "supplement raw receipt binding")
    sys.path.insert(0, str(GUARD))
    guard = load(GUARD / "run_fresh.py", "run_fresh")
    inputs, digest = guard.load_inputs()
    target_files = [GUARD / filename for filename in ("README.md", "run_fresh.py", "check_guard.py", "check_evidence.py", "inputs.json", "result.json", "verification.json")]
    attempt_snapshots = {}
    for packet in inputs["packets"].values():
        for record in packet["issued_files"]:
            require(sha(ROOT / record["path"]) == record["sha256"], "original five-file binding")
            target_files.append(ROOT / record["path"])
        attempt = (ROOT / packet["details"]["path"]).parent
        attempt_snapshots[str(attempt)] = snapshot_directory(attempt)
    prior_result_path = PRIOR / "result-v1.json"
    prior_result = read(prior_result_path)
    guard.verify(prior_result["source_sha256"])
    require(prior_result["checks"]["independent_saved_endpoint_integrals"] == 144, "reused endpoint checks")
    require(prior_result["checks"]["all_eight_complete_joint_resistances_null"] is True, "unknown complete joint resistance")
    require(prior_result["checks"]["independent_scalar_bound_fixtures"] == 36, "reused scalar fixtures")
    target_files.extend((prior_result_path, PRIOR / "check-testing.py", PRIOR / "v3-reuse-supplement-v1.json"))
    source_sha256 = {str(path.relative_to(ROOT)): sha(path) for path in target_files}
    source_sha256[str(Path(__file__).relative_to(ROOT))] = sha(__file__)
    with tempfile.TemporaryDirectory(prefix="eoere-final-testing-review-") as directory:
        temporary = Path(directory)
        check_receipts = run_checks(guard, inputs, temporary)
        extra_controls = independent_controls(guard, inputs, temporary)
    guard.verify(source_sha256)
    guard.verify(prior_result["source_sha256"])
    for attempt, expected in attempt_snapshots.items():
        require(snapshot_directory(Path(attempt)) == expected, "issued attempt changed")
    record = {
        "schema": "eoere_fresh_independent_testing_review/v1",
        "status": "PASS_NO_SUBSTANTIAL_TESTING_FINDINGS",
        "findings": [],
        "command": [sys.executable, "-B", "-S", str(Path(__file__).relative_to(ROOT))],
        "runtime": {"python": platform.python_version(), "third_party_imports": False},
        "source_sha256": source_sha256,
        "new_checks": check_receipts,
        "independent_extra_control_count": len(extra_controls),
        "independent_extra_controls": extra_controls,
        "reused_prior_numeric_review": {"receipt": bind(prior_result_path), "source_map_verified_before_after": True, "original_checks_reexecuted": False, "checks": prior_result["checks"]},
        "issued_attempt_file_counts_verified_before_after": {str(Path(path).relative_to(ROOT)): len(snapshot) for path, snapshot in attempt_snapshots.items()},
        "all_17_target_files_unchanged": True,
        "limits": ["Real future CLI rejection and the two new stdlib checker CLIs ran. Independent successful execute-path tests replaced only the analysis loader with stdlib stubs.", "No original full-analysis CLI, original run(), historic stdin, CAD/BRep/native/global/browser execution, dependency installation or complete test suite ran.", "Prior scoped endpoint/scalar numerical checks were authenticated and reused. No current or extended-cleat response, joint capacity, restraint strength or physical release is established.", "Temporary new outputs were removed with their owning TemporaryDirectory; receipt embeds their compact results and hashes. No shared, issued or other-agent file was altered."],
    }
    with (OWN / "receipt.json").open("xb") as stream:
        stream.write((json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())
    print(json.dumps({"status": record["status"], "extra_controls": len(extra_controls), "receipt_sha256": sha(OWN / "receipt.json")}))


if __name__ == "__main__":
    main()
