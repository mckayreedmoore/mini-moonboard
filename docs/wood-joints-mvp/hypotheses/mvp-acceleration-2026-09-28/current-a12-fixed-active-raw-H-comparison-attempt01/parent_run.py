"""Parent-only serialized one-shot execution entry; not run by preparation."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
LEDGER_LOCK = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
LEDGER_JSON = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_module():
    path = HERE / "prepare_raw.py"
    spec = importlib.util.spec_from_file_location("a12_raw_H_fixed_branch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import method producer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_once() -> None:
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    output_paths = [HERE / name for name in ("frozen-inputs.json", "response.npz", "assessment.json", "output-pin.json")]
    assert not any(path.exists() for path in output_paths), "parent one-shot already frozen or executed"
    module = load_module()
    readiness, context = module.build_readiness()
    readiness_path = HERE / "readiness.json"
    rendered = json.dumps(readiness, indent=2, sort_keys=True, allow_nan=False) + "\n"
    assert readiness_path.read_text(encoding="utf-8") == rendered, "readiness/source pins changed"
    sources = dict(readiness["source_sha256"])
    sources[module.relative(readiness_path)] = sha(readiness_path)
    assert all(sha(ROOT / path) == pin for path, pin in sources.items()), "a frozen input changed before run"

    write_json(HERE / "frozen-inputs.json", {
        "source_sha256": sources,
        "scope": "one exact full-load A12 fixed-branch raw-H compatibility comparison",
        "native_launch": False,
        "state_selection": False,
        "candidate_adoption": False,
        "active_bound_estimate_count": 734,
        "active_set_reselection": False,
        "wall_cap_seconds": 180,
        "CPU_cap_seconds": 180,
        "memory_cap_bytes": 6 * 1024**3,
        "BLAS_threads": 1,
    })

    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))

    def wall_timeout(*_args):
        raise TimeoutError("parent 180-second wall cap")

    signal.signal(signal.SIGALRM, wall_timeout)
    signal.alarm(180)
    started = time.monotonic()
    report = {
        "native_run": False, "candidate_forces_adopted": False,
        "mechanical_acceptance": False,
        "frozen_inputs_sha256": sha(HERE / "frozen-inputs.json"),
    }
    try:
        result, arrays = module.solve_and_audit(context)
        report.update(result)
        if arrays is not None:
            import numpy as np
            np.savez_compressed(HERE / "response.npz", **arrays)
            report["response_npz_sha256"] = sha(HERE / "response.npz")
    except Exception as error:  # parent run records stops; no retry/fallback
        report.update(status="STOP_PARENT_EXCEPTION_OR_BUDGET", exception=repr(error))
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - started
        report["source_freeze_unchanged"] = all(sha(ROOT / path) == pin for path, pin in sources.items())
        if not report["source_freeze_unchanged"]:
            report["status"] = "STOP_SOURCE_CHANGED_DURING_RUN"
        write_json(HERE / "assessment.json", report)
        write_json(HERE / "output-pin.json", {"assessment_sha256": sha(HERE / "assessment.json")})
        print(json.dumps(report, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Parent-owned one-shot; never run by read-only preparation")
    parser.add_argument("--parent-one-shot", action="store_true", required=True,
                        help="execute the one fixed raw-H branch comparison once")
    parser.parse_args()
    with LEDGER_LOCK.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(LEDGER_JSON.read_text(encoding="utf-8"))["slot"]["state"] == "idle"
        run_once()


if __name__ == "__main__":
    main()
