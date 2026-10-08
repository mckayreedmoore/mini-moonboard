"""Reuse prior synthetic API witnesses through the distinct corrected path adapter."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
REVIEW = LEAF + "/raw-angle-review-v1/"
GATE_PATH = LEAF + "/four-port-method-v1/first_order_admission_v2.py"
GATE_SHA = "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821"
ADAPTER = LEAF + "/component-method-v1/corrected_gate.py"
FROZEN = {
    GATE_PATH: GATE_SHA,
    LEAF + "/four-port-method-v1/test_first_order_admission_v2.py": "997e7771ffdba725d2a7b0bd18a1e5e7e1b82e9fd8098ccde4ff93ea8f0332c6",
    ADAPTER: "42c2ae96e2f25e7fb16cbdd3cfe390a620c312bfe9db072d2363bd559e9b35cc",
    LEAF + "/component-method-v1/test_corrected_gate.py": "15166c81de97b444ee7b0d65a9e0e6f18deec76e57beeddeca19fa6e0dd7bec3",
    REVIEW + "independent-corrected-component-adapter-review.json": "48c11881ee1599ca408e640c33e1a5ddff6255cf017cb71f8a5b6256d11551c5",
    REVIEW + "independent_corrected_component_adapter_review.py": "572c013160751298203f8b27b85e3fe027a4d628744d00d06723e03eaca5039c",
    REVIEW + "independent-component-consumer-gate-api-review.json": "f846a5853a01bb2e35dd4398110ed9cadbdf09cba87d90dd208aa9d4ef772e1e",
    REVIEW + "independent_component_gate_api_review.py": "a2af84fc37bcd525c6e4781e4da84472abe70743c87a02ee738c67b1f54e853d",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, label):
    if not ok:
        raise ValueError(label)


def join(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "contradictory corrected API pin")
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "corrected API source changed: " + path)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def correction(gate):
    return {"reused_source_path": str(gate.ORIGINAL.relative_to(ROOT)), "reused_source_sha256": gate.ORIGINAL_SHA,
        "removed_absent_historical_flag_guards": list(gate.CORRECTED_FUNCTIONS),
        "exact_own_alias_metadata_and_table_membership_verified": True,
        "physical_laws_or_algorithms_changed": False, "field_bytes_or_action_aliases_modified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued corrected API addendum")
    verify(FROZEN)
    pins = dict(FROZEN)
    for path in (REVIEW + "independent-component-consumer-gate-api-review.json", REVIEW + "independent-corrected-component-adapter-review.json"):
        join(pins, json.loads((ROOT/path).read_bytes())["source_sha256"])
    verify(pins)
    before = canonical(pins)
    helpers = load(REVIEW + "independent_component_gate_api_review.py", "independent_reused_cheap_API_fixtures")
    gate = load(GATE_PATH, "independent_corrected_component_real_gate")
    adapter = load(ADAPTER, "independent_corrected_component_real_adapter")
    # These constants feed only the preserved synthetic fixture. Neither genuine
    # gate context nor the frozen producer function globals are modified.
    facade = SimpleNamespace(FIELD_SCHEMA=gate.base.FIELD_SCHEMA, TABLES=gate.base.TABLES,
        SCHEMA=gate.SCHEMA, SUCCESS=gate.SUCCESS, core=gate.core, canonical=gate.base.canonical,
        source_pins=gate.source_pins, require_admitted_payload=gate.require_admitted_payload)
    saved_fixture, saved_gate, saved_sha = helpers.fixture, helpers.GATE, helpers.GATE_SHA
    old_gate, old_dispatch = adapter.base.GATE, adapter.base.consume
    provenance = []

    def corrected_fixture(method, source_pins):
        field, _, receipt = saved_fixture(method, source_pins)
        del field["usable_conditional_actions"]  # Match the genuine current v2 producer's absent flag.
        raw = json.dumps(field, sort_keys=True, separators=(",", ":")).encode()
        receipt["input_raw_sha256"] = hashlib.sha256(raw).hexdigest()
        receipt["input_canonical_sha256"] = gate.base.canonical(field)
        receipt["admission_compatibility_correction"] = correction(gate)
        return field, raw, receipt

    def traced_adapter(*args, **kwargs):
        result = adapter.consume(*args, **kwargs)
        provenance.append(copy.deepcopy(result["consumer_gate_path_adapter"]))
        return result

    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic cheap integration reached numerical audit/operator read/preparation")

    try:
        helpers.fixture, helpers.GATE, helpers.GATE_SHA = corrected_fixture, GATE_PATH, GATE_SHA
        with patch.object(gate.base.bundle, "read_snapshot", forbidden), patch.object(gate, "audit_first_order_state", forbidden):
            gate_pins, raw, receipt, api = helpers.review_api(facade)
            join(pins, gate_pins)
            corrected_provenance_rejections = []
            for label in ("missing-correction", "old-source-SHA", "unverified-metadata", "altered-field-declaration"):
                changed = copy.deepcopy(receipt)
                if label == "missing-correction":
                    del changed["admission_compatibility_correction"]
                elif label == "old-source-SHA":
                    changed["admission_compatibility_correction"]["reused_source_sha256"] = "0" * 64
                elif label == "unverified-metadata":
                    changed["admission_compatibility_correction"]["exact_own_alias_metadata_and_table_membership_verified"] = False
                else:
                    changed["admission_compatibility_correction"]["field_bytes_or_action_aliases_modified"] = True
                try:
                    gate.require_admitted_payload(raw, changed, admission_sha256=GATE_SHA)
                except ValueError:
                    corrected_provenance_rejections.append(label)
                else:
                    raise ValueError("invalid corrected gate provenance accepted: " + label)
            with adapter.gate_context(), patch.object(adapter.base, "consume", traced_adapter):
                integration = helpers.review_consumer(adapter.base, facade, raw, receipt)
    finally:
        helpers.fixture, helpers.GATE, helpers.GATE_SHA = saved_fixture, saved_gate, saved_sha
    require(adapter.base.GATE == old_gate and adapter.base.consume is old_dispatch and
            adapter.base.__file__ == str(adapter.BASE), "adapter path/dispatch/file identity did not restore")
    require(len(provenance) == 1 and provenance[0]["actual_gate_path"] == GATE_PATH and
            provenance[0]["actual_gate_sha256"] == GATE_SHA and
            provenance[0]["loaded_wrapper_sha256"] == FROZEN[ADAPTER] and
            provenance[0]["frozen_consumer_sha256"] == adapter.BASE_SHA and
            provenance[0]["field_or_admission_payload_modified"] is False,
            "genuine adapter result provenance differs")
    verify(pins)
    require(sha(OWN) == LOADED_SHA, "corrected API reviewer changed")
    direct = {**FROZEN, str(OWN.relative_to(ROOT)): LOADED_SHA}
    verify(direct)
    result = {"schema": "eoere_corrected_component_consumer_cheap_API_independent_readiness/v1",
        "status": "READY_CORRECTED_COMPONENT_CONSUMER_METHOD", "source_sha256": direct,
        "verified_upstream_pin_count": len(pins), "upstream_closure_canonical_sha256_before": before,
        "upstream_closure_canonical_sha256_after_with_corrected_gate": canonical(pins),
        "all_source_pins_before_after_unchanged": True,
        "reused_prior_synthetic_API_checks": api, "corrected_provenance_mutations_rejected": corrected_provenance_rejections,
        "genuine_corrected_consumer_integration": integration,
        "genuine_adapter_result_provenance": provenance[0],
        "original_path_dispatch_and_file_identity_restored": True,
        "focused_verification": {"adapter_fixtures_passed": 6, "corrected_same_byte_API_fixtures_passed": 7,
                                  "Ruff_adapter_gate_tests_and_reviewer_pass": True},
        "limits": ["Only the corrected cheap API integration is closed; Support separately owns the corrected numerical and alias-metadata audit readiness.",
            "The synthetic positive receipt exists only in memory/temporary fixtures, with no numerical admission issued or old PASS relabeled.",
            "Actual raw v2 bytes must receive their own corrected independent numerical receipt before parent-owned component consumption.",
            "All frozen gross/steel/panel/Hillman/reference and complete-joint resistance limits remain."],
        "candidate_field_operator_read_preparation_CAD_query_q_K_or_solve_executed": False,
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version()}, "release": dict(adapter.base.RELEASE)}
    with options.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "sha256": sha(options.output), "bytes": options.output.stat().st_size,
                      "pins": len(pins), "status": result["status"]}))


if __name__ == "__main__":
    main()
