"""Ignore only generic execution.python in an otherwise exact replay join.

Reuse frozen v1 calculations, source guards and drawings. Record both original
and live runtime provenance without making build text a numerical criterion.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PREVIOUS = {
    "inputs.json": "dd0df7d6b5eb30aab11184c4d4471333e545b270232333ba9577678c9155282d",
    "adapter.py": "f3831931d6c89330e07d76d1099cc4ecdf9a9a0c6e7be1b069413a7a1bc22a04",
    "result-v2.json": "e5e34e992365aedf30b56710efd9dcbb4d1a64e77e4ede29ff656d0479ff17de",
    "result-v2.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify.py": "dd755dc20baf508cb03896062f317d5e4a6171e732b1a7329461da4b8a3931d3",
    "verification-v1.json": "7cc2edc01fbdf98536e0a2029ea7e090503e135df7d698395127bbc30bea55b1",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_generic(replay, recorded):
    """Normalize one runtime field; preserve the complete remaining structure."""
    require(isinstance(replay["execution"]["python"], str)
            and isinstance(recorded["execution"]["python"], str), "runtime text required")
    normalized = copy.deepcopy(replay)
    normalized["execution"]["python"] = recorded["execution"]["python"]
    require(normalized == recorded, "non-runtime generic replay/source difference")
    return normalized


def method_with_runtime_join(runtime):
    """Bind a local loader proxy; never mutate the shared runpy module."""
    require(all(sha(HERE / n) == h for n, h in PREVIOUS.items()), "frozen v1 packet changed")
    method = runpy.run_path(str(HERE / "adapter.py"))
    generic_path = HERE.parent / "design.py"
    recorded = json.loads((HERE.parent / "result.json").read_bytes())
    recorded = {k: v for k, v in recorded.items() if k != "drawing"}

    def local_run_path(path, *args, **kwargs):
        loaded = runpy.run_path(path, *args, **kwargs)
        if Path(path).resolve() != generic_path:
            return loaded
        evaluate = loaded["evaluate"]

        def evaluate_with_runtime_join():
            inp, replay, shapes = evaluate()
            runtime["generic_recorded_execution_python"] = recorded["execution"]["python"]
            runtime["generic_live_execution_python"] = replay["execution"]["python"]
            return inp, normalized_generic(replay, recorded), shapes

        loaded["evaluate"] = evaluate_with_runtime_join
        return loaded

    # Function globals are the local frozen-module instance created by run_path;
    # replacing this reference does not replace runpy.run_path globally.
    method["load"].__globals__["runpy"] = SimpleNamespace(run_path=local_run_path)
    return method


def calculate():
    runtime = {}
    method = method_with_runtime_join(runtime)
    result = method["calculate"]()
    previous = json.loads((HERE / "result-v2.json").read_bytes())
    require(result == {k: v for k, v in previous.items() if k != "drawing"},
            "v1 scalar/source/guard results changed")
    require(set(runtime) == {"generic_recorded_execution_python", "generic_live_execution_python"},
            "generic runtime provenance absent")
    pins = result["source_sha256"]
    for name, digest in PREVIOUS.items():
        path = str((HERE / name).relative_to(ROOT))
        require(path not in pins or pins[path] == digest, "conflicting v1 source pin")
        pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    result["source_pin_count"] = len(pins)
    prior_command = result["execution"]["reproduce"]
    result["execution"]["reproduce"] = (
        f"uv run python -B {OWN.relative_to(ROOT)} --out {HERE.relative_to(ROOT)}/reproduction-v2-01.json"
    )
    result["runtime_reproduction"] = {
        **runtime, "wrapper_live_execution_python": sys.version,
        "normalized_generic_comparison_path_only": "/execution/python",
        "every_other_generic_scalar_source_guard_and_structure_field_exact": True,
        "original_v1_result_arithmetic_source_and_guards_exact": True,
        "original_v1_reproduction_command": prior_command,
        "original_v1_six_files_unchanged": True,
        "runtime_change_is_not_a_method_tool_or_physical_qualification": True,
    }
    method["verify"](pins)
    return result, method


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # Frozen v1 output guards retain canonical parent binding and mode-x writes.
    require(sha(HERE / "adapter.py") == PREVIOUS["adapter.py"], "frozen adapter method changed")
    guard = runpy.run_path(str(HERE / "adapter.py"))["output_paths"]
    destination, picture = guard(args.out)
    result, method = calculate()
    svg = method["drawing"](result)
    require(hashlib.sha256(svg).hexdigest() == PREVIOUS["result-v2.svg"], "frozen drawing bytes changed")
    result["drawing"] = {"path": str(picture.relative_to(ROOT)), "sha256": hashlib.sha256(svg).hexdigest(), "bytes": len(svg)}
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    method["verify"](result["source_sha256"])
    with picture.open("xb") as stream:
        stream.write(svg)
    with destination.open("xb") as stream:
        stream.write(raw)
    method["verify"](result["source_sha256"])
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination), "bytes": len(raw),
                      "drawing": result["drawing"], "source_pin_count": result["source_pin_count"],
                      "generic_error_target_met": False, "v1_scalar_results_exact": True}))


if __name__ == "__main__":
    main()
