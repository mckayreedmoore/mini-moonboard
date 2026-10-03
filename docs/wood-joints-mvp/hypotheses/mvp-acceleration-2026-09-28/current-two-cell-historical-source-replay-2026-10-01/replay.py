"""Replay unchanged two-cell mathematics against authenticated historical policy."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
OLD = BASE / "conditional-floor-two-cell-coupled-stick-fixture-attempt01"
HISTORICAL_COMMIT = "33d0e129"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def produce():
    spec = importlib.util.spec_from_file_location("historical_two_cell", OLD / "verify_fixture.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = json.loads(module.FIXTURE_PATH.read_text())
    historical_policy = subprocess.check_output(["git", "show", f"{HISTORICAL_COMMIT}:AGENTS.md"], cwd=ROOT)
    source_hashes = {}
    for name, (relative, expected) in module.PINNED_SOURCES.items():
        data = historical_policy if name == "AGENTS.md" else (ROOT / relative).read_bytes()
        assert sha(data) == expected == fixture["sources"][name], name
        source_hashes[str(relative)] = expected
    observed = module.run_fixture(fixture, source_hashes)
    rendered = json.dumps(observed, indent=2, sort_keys=True) + "\n"
    assert rendered == (OLD / "observed.json").read_text()
    return {
        "status": "PASS_UNCHANGED_EIGHT_STAGE_HISTORICAL_MATHEMATICS",
        "original_cli_replay_status": "STOP_CURRENT_AGENTS_SOURCE_HASH_CHANGED",
        "historical_policy_commit": subprocess.check_output(["git", "rev-parse", HISTORICAL_COMMIT], cwd=ROOT, text=True).strip(),
        "historical_AGENTS_sha256": sha(historical_policy),
        "current_AGENTS_sha256": sha((ROOT / "AGENTS.md").read_bytes()),
        "source_sha256": {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [OLD / "verify_fixture.py", OLD / "fixture.json", OLD / "observed.json", HERE / "replay.py"]},
        "mathematical_result_summary": observed["result_summary"],
        "native_launch": False,
        "frame_response_accepted": False,
        "limits": "Normal and tangent coordinates are separate. Re-engagement uses the preceding open-stage coordinate, not a solved continuous contact-event location. No staged frame history, unique coupled frame state or current-policy native readiness is established.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True) + "\n"
    output = HERE / "assessment.json"
    if args.verify:
        assert output.read_text() == rendered
    else:
        output.write_text(rendered)
    print("PASS_UNCHANGED_EIGHT_STAGE_HISTORICAL_MATHEMATICS")
