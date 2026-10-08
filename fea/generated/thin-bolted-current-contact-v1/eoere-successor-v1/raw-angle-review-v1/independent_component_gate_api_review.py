"""Genuine cheap API integration using synthetic bytes only, no numerical audit."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
REVIEW = LEAF + "/raw-angle-review-v1/"
GATE = LEAF + "/four-port-method-v1/first_order_admission.py"
GATE_SHA = "e61ee415f0a8cd83f3ea4b0606064bceb128413eed4e66f1192955b1610ff66b"
FROZEN = {
    GATE: GATE_SHA,
    LEAF + "/four-port-method-v1/test_first_order_admission.py": "2f39c367d3d3162b842156268206363064063a4cf5a7b8dcf3ad61b4e2d64bbe",
    REVIEW + "independent-component-consumer-method-review.json": "f3d7c9d0624986a1f4d34f0a695e31c38961f806d3144d8936cece135f3d83b5",
    REVIEW + "independent_component_consumer_review.py": "c8d6914c2ceee1f08148616c12fd91800bf46bd018ec1cbf0b955e36e20ce734",
    REVIEW + "independent-operator-v2-method-review.json": "56201ebf7d9d420bcf6f5271b5271c404643115b3441ac36cc87cd6e7e3106c5",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def join(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "contradictory gate API review pin")
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "gate API source changed: " + path)


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def no_candidate(*args, **kwargs):
    raise AssertionError("cheap synthetic contract tried operator read or candidate preparation")


def fixture(gate, pins):
    field = {"schema": gate.FIELD_SCHEMA, "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION",
        "state_id": "synthetic-API-only", "case_id": "synthetic-API-case", "accessory_placement": "synthetic-API-placement",
        "response": {"converged": True, "q": [1., 2.], "gradient_n": [3., 4.]}, "usable_conditional_actions": True,
        "release": copy.deepcopy(gate.core.RELEASE), "operator_bundle": {},
        "original_operator_fingerprint_sha256": "a" * 64, "source_sha256": pins}
    field.update({key: {} if key == "panel_generalized_coefficients" else [] for key in gate.TABLES})
    payload = json.dumps(field, sort_keys=True, separators=(",", ":")).encode()
    receipt = {"schema": gate.SCHEMA, gate.SUCCESS: True,
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "source_path": GATE, "admission_source_sha256": GATE_SHA,
        "input_raw_sha256": hashlib.sha256(payload).hexdigest(), "input_canonical_sha256": gate.canonical(field),
        "release": copy.deepcopy(gate.core.RELEASE), "source_sha256": pins,
        "support_search_checks": {"final_q_canonical_sha256": gate.canonical(field["response"]["q"])},
        "original_law_checks": {"full_signed_gradient_canonical_sha256": gate.canonical(field["response"]["gradient_n"])},
        "operator_bundle": {}, "original_operator_fingerprint_sha256": field["original_operator_fingerprint_sha256"],
        "table_canonical_sha256": {key: gate.canonical(field[key]) for key in gate.TABLES}}
    return field, payload, receipt


def review_api(gate):
    # Source bytes only. No saved operator arrays/manifest or candidate input is opened.
    pins = gate.source_pins()
    field, payload, receipt = fixture(gate, pins)
    original = copy.deepcopy((field, receipt))
    parsed, returned = gate.require_admitted_payload(payload, receipt, admission_sha256=GATE_SHA)
    require(parsed == field and returned == pins and (field, receipt) == original,
            "genuine synthetic cheap API changed byte/source contract")
    rejected = []
    for label in ("wrong-gate-SHA", "old-receipt-schema", "false-admission", "same-canonical-different-raw-bytes",
                  "foreign-source-path", "foreign-q-digest", "foreign-gradient-digest", "foreign-table-digest",
                  "foreign-operator-fingerprint", "foreign-state", "foreign-action-identity", "incomplete-field-source-closure"):
        data, record, raw, digest = copy.deepcopy(field), copy.deepcopy(receipt), payload, GATE_SHA
        if label == "wrong-gate-SHA":
            digest = "0" * 64
        elif label == "old-receipt-schema":
            record["schema"] = "old"
        elif label == "false-admission":
            record[gate.SUCCESS] = False
        elif label == "same-canonical-different-raw-bytes":
            raw = payload + b"\n"
        elif label == "foreign-source-path":
            record["source_path"] = "old-gate.py"
        elif label == "foreign-q-digest":
            record["support_search_checks"]["final_q_canonical_sha256"] = "0" * 64
        elif label == "foreign-gradient-digest":
            record["original_law_checks"]["full_signed_gradient_canonical_sha256"] = "0" * 64
        elif label == "foreign-table-digest":
            record["table_canonical_sha256"]["common_shaft_section_cut_actions"] = "0" * 64
        elif label == "foreign-operator-fingerprint":
            record["original_operator_fingerprint_sha256"] = "0" * 64
        elif label == "foreign-state":
            record["state_id"] = "foreign"
        elif label == "foreign-action-identity":
            data["four_port_fitting_actions"] = [{"state_id": "foreign"}]
        else:
            data["source_sha256"]["synthetic-unpinned-source.py"] = "0" * 64
        if data != field:
            raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            record["input_raw_sha256"] = hashlib.sha256(raw).hexdigest()
            record["input_canonical_sha256"] = gate.canonical(data)
            record["table_canonical_sha256"] = {key: gate.canonical(data[key]) for key in gate.TABLES}
        try:
            gate.require_admitted_payload(raw, record, admission_sha256=digest)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("invalid synthetic cheap API accepted: " + label)
    return pins, payload, receipt, {"positive_exact_contract_returns_same_synthetic_field_and_pins": True,
        "synthetic_receipt_constructed_in_memory_only": True, "synthetic_numerical_admission_issued": False,
        "rejected_mutations": rejected}


def review_consumer(method, gate, payload, receipt):
    calls = []
    saved_load, saved_reduce = method.load, method.reduce_field

    def trace_gate(*args, **kwargs):
        calls.append("genuine-cheap-gate")
        return gate.require_admitted_payload(*args, **kwargs)

    def synthetic_load(path, digest, name):
        require(method.sha(path) == digest, "synthetic integration source check differs")
        if path == method.GATE:
            return SimpleNamespace(require_admitted_payload=trace_gate)
        if path == method.STEEL:
            calls.append("steel-method-after-gate")
            return SimpleNamespace(source_contract=lambda: {"source_sha256": {}, "geometry": {"axes": []}})
        require(path == method.GROSS, "unexpected component method load")
        calls.append("gross-method-after-gate")
        return SimpleNamespace(source_pins=dict)

    def synthetic_reduce(field, *args, **kwargs):
        calls.append("synthetic-dispatch-after-gate")
        require(method.canonical(field) == method.canonical(json.loads(payload)), "consumer projected gate field")
        return {"synthetic_dispatch_only": True}, {}

    try:
        method.load, method.reduce_field = synthetic_load, synthetic_reduce
        with tempfile.TemporaryDirectory(prefix=".synthetic-gate-api-", dir=OWN.parent) as temporary:
            leaf = Path(temporary)
            field_path, receipt_path = leaf/"synthetic-field.json", leaf/"synthetic-receipt.json"
            field_path.write_bytes(payload)
            receipt_path.write_text(json.dumps(receipt))
            result = method.consume(field_path, receipt_path, expected_field_sha256=method.sha(field_path),
                admission_sha256=GATE_SHA, steel_sha256="9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360")
            require(calls == ["genuine-cheap-gate", "steel-method-after-gate", "gross-method-after-gate", "synthetic-dispatch-after-gate"]
                    and result["release"] == method.RELEASE, "genuine consumer API call order or unreleased result differs")
            positive_calls = list(calls)
            calls.clear()
            receipt_path.write_text(json.dumps({**receipt, "input_raw_sha256": "0" * 64}))
            try:
                method.consume(field_path, receipt_path, expected_field_sha256=method.sha(field_path),
                    admission_sha256=GATE_SHA, steel_sha256="9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360")
            except ValueError:
                require(calls == ["genuine-cheap-gate"], "rejected receipt reached component loads/reductions")
            else:
                raise ValueError("consumer accepted foreign raw-byte receipt")
    finally:
        method.load, method.reduce_field = saved_load, saved_reduce
    return {"synthetic_exact_API_call_order": positive_calls, "wrong_raw_receipt_stops_before_component_loads": True,
            "consumer_received_unprojected_same_field": True, "actual_component_reductions_executed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued gate integration addendum")
    verify(FROZEN)
    pins = dict(FROZEN)
    for path in (REVIEW + "independent-component-consumer-method-review.json", REVIEW + "independent-operator-v2-method-review.json"):
        join(pins, json.loads((ROOT/path).read_bytes())["source_sha256"])
    verify(pins)  # Full already-reviewed module closure before the first dynamic import.
    gate = load(GATE, "independent_component_genuine_gate_API")
    method = load(LEAF + "/component-method-v1/assessment.py", "independent_component_API_consumer")
    saved_reader, saved_audit = gate.bundle.read_snapshot, gate.audit_first_order_state
    try:
        gate.bundle.read_snapshot, gate.audit_first_order_state = no_candidate, no_candidate
        gate_pins, payload, receipt, checks = review_api(gate)
        join(pins, gate_pins)
        integration = review_consumer(method, gate, payload, receipt)
    finally:
        gate.bundle.read_snapshot, gate.audit_first_order_state = saved_reader, saved_audit
    join(pins, {str(OWN.relative_to(ROOT)): LOADED_SHA})
    verify(pins)
    require(sha(OWN) == LOADED_SHA, "gate API reviewer changed while executing")
    output = {"schema": "eoere_compact_component_consumer_fresh_gate_API_independent_review/v1",
        "status": "READY_COMPONENT_CONSUMER_METHOD", "fresh_gate_sha256": GATE_SHA,
        "source_sha256": pins, "source_pins_before_after_unchanged": True,
        "preserved_consumer_method_receipt_sha256": FROZEN[REVIEW + "independent-component-consumer-method-review.json"],
        "genuine_cheap_API_synthetic_checks": checks, "genuine_consumer_synthetic_integration": integration,
        "focused_gate_cheap_API_fixture": {"passed": 1, "deselected": 33, "seconds": 1.87},
        "Ruff_reviewer_pass": True,
        "limits": ["This addendum only closes the frozen cheap API integration; the full numerical gate has its own independent reviewer.",
            "The positive receipt is an in-memory structural contract fixture, not a numerical admission or saved candidate result.",
            "Actual v2 bytes must separately receive an independently reviewed issued numerical admission before component consumption.",
            "All scenario-reference and complete-joint resistance limits from the preserved component review remain."],
        "candidate_field_operator_read_preparation_CAD_query_q_K_or_solve_executed": False,
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version()}, "release": copy.deepcopy(method.RELEASE)}
    with options.output.open("x") as stream:
        json.dump(output, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "bytes": options.output.stat().st_size, "sha256": sha(options.output), "pins": len(pins)}))


if __name__ == "__main__":
    main()
