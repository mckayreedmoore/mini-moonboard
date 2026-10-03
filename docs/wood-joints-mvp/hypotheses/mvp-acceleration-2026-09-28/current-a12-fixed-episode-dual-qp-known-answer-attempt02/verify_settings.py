"""Replay existing tiny source oracles with this run's numerical settings."""
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OLD = BASE / "current-floor-mask-dual-qp-fixture-attempt01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


producer = module(OLD / "solve_fixture.py", "unchanged_tiny_dual_source")
runner = module(HERE / "parent_run.py", "declared_parent_settings")
producer.SETTINGS = dict(runner.SETTINGS)
report = producer.produce()  # All existing expected masks/sign/KKT assertions.
assert report["status"] == "PASS_TINY_SOURCE_BRANCHES_AND_KKT_FIXTURES"
summary = dict(status="PASS_TINY_SOURCE_ORACLES_WITH_ADAPTIVE_RHO",
               settings=runner.SETTINGS, original_producer_sha256=sha(OLD / "solve_fixture.py"),
               settings_script_sha256=sha(Path(__file__).resolve()),
               parent_run_sha256=sha(HERE / "parent_run.py"),
               source_pin_inventory=report["source_sha256"],
               nonzero_H_e_sign_fixture=report["nonzero_H_e_sign_fixture"],
               source_branch_cases=report["source_branch_cases"],
               native_run=False, frame_solve=False)
(HERE / "numerical-settings-fixture.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
print("PASS_TINY_SOURCE_ORACLES_WITH_ADAPTIVE_RHO")
