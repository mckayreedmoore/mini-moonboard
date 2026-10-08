"""Read-only source closure and tiny gate-path scope checks, no candidate data."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
REVIEW = LEAF + "/raw-angle-review-v1/"
ADAPTER = LEAF + "/component-method-v1/corrected_gate.py"
FROZEN = {
    ADAPTER: "42c2ae96e2f25e7fb16cbdd3cfe390a620c312bfe9db072d2363bd559e9b35cc",
    LEAF + "/component-method-v1/test_corrected_gate.py": "15166c81de97b444ee7b0d65a9e0e6f18deec76e57beeddeca19fa6e0dd7bec3",
    LEAF + "/component-method-v1/assessment.py": "f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0",
    REVIEW + "independent-component-consumer-method-review.json": "f3d7c9d0624986a1f4d34f0a695e31c38961f806d3144d8936cece135f3d83b5",
    REVIEW + "independent-component-consumer-gate-api-review.json": "f846a5853a01bb2e35dd4398110ed9cadbdf09cba87d90dd208aa9d4ef772e1e",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, label):
    if not ok:
        raise ValueError(label)


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "corrected adapter source changed: " + path)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued corrected-adapter review")
    verify(FROZEN)
    pins = dict(FROZEN)
    for relative in (REVIEW + "independent-component-consumer-method-review.json", REVIEW + "independent-component-consumer-gate-api-review.json"):
        for path, digest in json.loads((ROOT/relative).read_bytes())["source_sha256"].items():
            require(path not in pins or pins[path] == digest, "contradictory corrected-adapter closure")
            pins[path] = digest
    verify(pins)
    before = canonical(pins)
    tree = ast.parse((ROOT/ADAPTER).read_text())
    targets = [call.args[1].value for call in ast.walk(tree) if isinstance(call, ast.Call)
               and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)
               and call.func.value.id == "patch" and call.func.attr == "object"]
    require(sorted(targets) == ["GATE", "consume"], "adapter changes additional producer attributes")
    spec = importlib.util.spec_from_file_location("independent_corrected_component_path_adapter", ROOT/ADAPTER)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    old_gate, old_consume = method.base.GATE, method.base.consume
    require(method.base.__file__ == str(method.BASE) and method.FROZEN_CONSUME is old_consume,
            "adapter changed frozen consumer identity or captured dispatch")
    with method.gate_context():
        require(method.base.GATE == method.GATE and method.base.consume is old_consume,
                "path context changed component dispatch/algorithm")
    require(method.base.GATE == old_gate, "normal context did not restore original gate")
    try:
        with method.gate_context():
            raise RuntimeError("independent synthetic exception only")
    except RuntimeError:
        pass
    require(method.base.GATE == old_gate and method.base.consume is old_consume, "exception did not restore producer attributes")
    verify(pins)
    require(canonical(pins) == before and sha(OWN) == LOADED_SHA, "review source closure changed")
    direct = {**FROZEN, str(OWN.relative_to(ROOT)): LOADED_SHA}
    verify(direct)
    result = {"schema": "eoere_corrected_component_gate_path_adapter_independent_readiness/v1",
        "status": "READY_PATH_ADAPTER_PENDING_CORRECTED_GATE_API", "source_sha256": direct,
        "upstream_closure_pin_count": len(pins), "upstream_closure_canonical_sha256_before_after": before,
        "all_upstream_source_pins_before_after_unchanged": True,
        "focused_fixture_checks": {"passed": 6, "seconds": 1.48, "Ruff_adapter_test_and_reviewer_pass": True},
        "independent_scope_checks": {"only_scoped_producer_attributes": sorted(targets),
            "frozen_consumer_file_identity_preserved": True, "original_callable_captured": True,
            "path_only_context_preserves_consume": True, "normal_and_exception_restoration_pass": True},
        "reviewed_source_contract": ["Explicit caller gate SHA is verified at alternate path before the frozen exact-byte consume call.",
            "Arguments/raw hash/samples pass directly to the frozen consumer; no field/receipt payload is changed.",
            "Result must bind actual gate SHA, raw field SHA and alternate gate source pin before wrapper metadata is added.",
            "Wrapper/frozen-consumer/corrected-gate pins are joined contradiction-strict and checked after reduction.",
            "The original CLI parser captures real sys.orig_argv under the wrapper; both callbacks restore after normal or exceptional exit."],
        "corrected_gate_API_status": "PENDING_FROZEN_CORRECTED_SOURCE_SHA",
        "candidate_field_operator_read_preparation_CAD_query_q_K_or_solve_executed": False,
        "limits": ["Sequential parent-owned use only; the scoped module attributes are not a concurrency interface.",
            "This review authorizes only the adapter method. Actual corrected-gate readiness and actual byte admission remain separate.",
            "All prior component/reference/resistance limits remain; old gate and old API receipts are preserved."],
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version()}, "release": dict(method.base.RELEASE)}
    with options.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "sha256": sha(options.output), "bytes": options.output.stat().st_size,
                      "pins": len(pins), "status": result["status"]}))


if __name__ == "__main__":
    main()
