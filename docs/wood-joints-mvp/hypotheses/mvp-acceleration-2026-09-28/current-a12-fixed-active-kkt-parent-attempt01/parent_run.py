"""Serialized parent-only one-shot fixed A12 episode refinement."""
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
PREP = BASE / "current-a12-fixed-active-kkt-refinement-preflight-attempt01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run():
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
    assert os.environ.get("OMP_NUM_THREADS") == "1"
    assert not (HERE / "frozen-inputs.json").exists(), "one-shot already frozen"
    spec = importlib.util.spec_from_file_location("a12_fixed_refinement", PREP / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.np.__version__ == "2.5.2" and module.scipy.__version__ == "1.18.1"
    proposal, _ = module.build_proposal()
    rendered = json.dumps(proposal, indent=2, sort_keys=True, allow_nan=False) + "\n"
    assert (PREP / "readiness.json").read_text() == rendered
    previous = json.loads((BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt02/frozen-inputs.json").read_text())
    sources = dict(previous["source_sha256"])
    for path in list(module.PIN_PATHS.values()) + [PREP / "prepare.py", PREP / "README.md", PREP / "readiness.json", HERE / "parent_run.py", HERE / "README.md"]:
        sources[str(path.relative_to(ROOT))] = sha(path)
    assert all(sha(ROOT / name) == pin for name, pin in sources.items())
    write(HERE / "frozen-inputs.json", {
        "source_sha256": sources, "native_launch": False,
        "scope": "one fixed A12 full-load historical episode; no state selection",
        "versions": {"numpy": module.np.__version__, "scipy": module.scipy.__version__},
        "wall_cap_seconds": 180, "CPU_cap_seconds": 180,
        "memory_cap_bytes": 6 * 1024**3, "BLAS_threads": 1,
        "active_bound_estimate_count": 734, "floor_mask_changed": False,
    })
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    def timeout(*args):
        raise TimeoutError("parent 180-second wall cap")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    start = time.monotonic()
    report = {"native_launch": False, "candidate_forces_adopted": False,
              "joint_accepted": False, "frozen_inputs_sha256": sha(HERE / "frozen-inputs.json")}
    try:
        report.update(module.one_shot_refine())
    except Exception as error:
        report.update(status="STOP_PARENT_EXCEPTION_OR_BUDGET", exception=repr(error))
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - start
        report["source_freeze_unchanged"] = all(sha(ROOT / name) == pin for name, pin in sources.items())
        if not report["source_freeze_unchanged"]:
            report["status"] = "STOP_SOURCE_CHANGED_DURING_RUN"
        write(HERE / "assessment.json", report)
        write(HERE / "output-pin.json", {"assessment_sha256": sha(HERE / "assessment.json")})
        print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert json.loads(lock.with_suffix(".json").read_text())["slot"]["state"] == "idle"
        run()
