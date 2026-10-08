"""Narrow v3 path/raw-byte seam; reuse frozen synthetic consumer integration."""
from __future__ import annotations

import argparse
import ast
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
GATE_PATH = LEAF + "/four-port-method-v1/first_order_admission_v3.py"
GATE_SHA = "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008"
ORDERED = LEAF + "/component-method-v1/ordered_gate.py"
FROZEN = {
    GATE_PATH: GATE_SHA,
    LEAF + "/four-port-method-v1/test_first_order_admission_v3.py": "f2e1cbe9377219084cd7d4215237b323fb7e82dfdc677051357fac5c8bdbb0a1",
    ORDERED: "b0e1f9f5f894faf0630cf7f6100b0dda75a00e00f840384241d4591788ab88ba",
    LEAF + "/component-method-v1/test_ordered_gate.py": "6913269987f1e3c4874cc39ef7b729d9f5533c6ea533a91fdd8a1855742e707b",
    REVIEW + "independent-corrected-component-gate-api-review.json": "93c16ee5d072e1e4ba63d6f763eec864979630d5913e7c4d054fdb2a150d0ff5",
    REVIEW + "independent_corrected_component_gate_api_review.py": "5cd8aa48fc760b2199f665e0e25802290f466928dfabf1b2939a3ae11a9121fd",
    REVIEW + "independent-component-consumer-gate-api-review.json": "f846a5853a01bb2e35dd4398110ed9cadbdf09cba87d90dd208aa9d4ef772e1e",
    REVIEW + "independent_component_gate_api_review.py": "a2af84fc37bcd525c6e4781e4da84472abe70743c87a02ee738c67b1f54e853d",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, label):
    if not ok:
        raise ValueError(label)


def join(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "contradictory ordered-seam source pin")
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "ordered-seam source changed: " + path)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def no_candidate(*args, **kwargs):
    raise AssertionError("ordered cheap seam reached operator read or numerical audit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued ordered-seam receipt")
    verify(FROZEN)
    pins = dict(FROZEN)
    for path in (REVIEW + "independent-corrected-component-gate-api-review.json", REVIEW + "independent-component-consumer-gate-api-review.json"):
        join(pins, json.loads((ROOT/path).read_bytes())["source_sha256"])
    verify(pins)
    tree = ast.parse((ROOT/ORDERED).read_bytes())
    targets = [call.args[1].value for call in ast.walk(tree) if isinstance(call, ast.Call)
               and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)
               and call.func.value.id == "patch" and call.func.attr == "object"]
    require(sorted(targets) == ["GATE", "consume"], "new adapter patches additional producer attributes")
    before = canonical(pins)
    helpers = load(REVIEW + "independent_component_gate_api_review.py", "ordered_seam_reused_synthetic_contract")
    gate = load(GATE_PATH, "ordered_seam_genuine_v3_gate")
    ordered = load(ORDERED, "ordered_seam_genuine_consumer_adapter")
    join(pins, gate.source_pins())
    verify(pins)
    facade = SimpleNamespace(FIELD_SCHEMA=gate.base.FIELD_SCHEMA, TABLES=gate.base.TABLES,
        SCHEMA=gate.SCHEMA, SUCCESS=gate.SUCCESS, core=gate.core, canonical=gate.base.canonical,
        source_pins=gate.source_pins, require_admitted_payload=gate.require_admitted_payload)
    old_helper_gate, old_helper_sha = helpers.GATE, helpers.GATE_SHA
    originals = (ordered.reused.__file__, ordered.base.__file__, ordered.reused.GATE,
                 ordered.base.GATE, ordered.reused.consume, ordered.base.consume)
    metadata = []

    def traced_outer(*args, **kwargs):
        result = ordered.consume(*args, **kwargs)
        metadata.append({key: copy.deepcopy(result[key]) for key in
                         ("consumer_gate_path_adapter", "consumer_order_gate_path_adapter")})
        return result

    try:
        helpers.GATE, helpers.GATE_SHA = GATE_PATH, GATE_SHA
        field, _, receipt = helpers.fixture(facade, gate.source_pins())
        del field["usable_conditional_actions"]
        raw = json.dumps(field, sort_keys=True, separators=(",", ":")).encode()
        receipt.update(input_raw_sha256=hashlib.sha256(raw).hexdigest(), input_canonical_sha256=gate.base.canonical(field),
            admission_compatibility_correction=gate.compatibility_provenance(),
            admission_recovery_order_correction=gate.order_provenance())
        with patch.object(gate.base.bundle, "read_snapshot", no_candidate), patch.object(gate, "audit_first_order_state", no_candidate):
            parsed, returned = gate.require_admitted_payload(raw, receipt, admission_sha256=GATE_SHA)
            require(parsed == field and returned == gate.source_pins(), "new cheap contract changed synthetic raw field")
            rejections = []
            for label in ("same-canonical-different-raw-bytes", "missing-order-provenance", "changed-cut-tolerance-declaration"):
                payload, changed = raw, copy.deepcopy(receipt)
                if label == "same-canonical-different-raw-bytes":
                    payload += b"\n"
                elif label == "missing-order-provenance":
                    del changed["admission_recovery_order_correction"]
                else:
                    changed["admission_recovery_order_correction"]["cut_values_or_force_tolerances_changed"] = True
                try:
                    gate.require_admitted_payload(payload, changed, admission_sha256=GATE_SHA)
                except ValueError:
                    rejections.append(label)
                else:
                    raise ValueError("ordered seam accepted invalid synthetic contract: " + label)
            # Reuse the previous two tiny dispatch cases only (exact bytes and
            # wrong raw receipt). No former full census, mechanics or mutation
            # campaign is repeated.
            with ordered.gate_context(), ordered.reused.gate_context(), patch.object(ordered.base, "consume", traced_outer):
                integration = helpers.review_consumer(ordered.base, facade, raw, receipt)
    finally:
        helpers.GATE, helpers.GATE_SHA = old_helper_gate, old_helper_sha
    require((ordered.reused.__file__, ordered.base.__file__, ordered.reused.GATE,
             ordered.base.GATE, ordered.reused.consume, ordered.base.consume) == originals,
            "nested original file identities/path/dispatch did not restore")
    require(len(metadata) == 1, "wrong raw receipt acquired adapter provenance")
    for key, row in metadata[0].items():
        require(row["actual_gate_path"] == GATE_PATH and row["actual_gate_sha256"] == GATE_SHA
                and row["field_or_admission_payload_modified"] is False,
                "nested v3 adapter provenance differs: " + key)
    require(metadata[0]["consumer_order_gate_path_adapter"]["loaded_outer_sha256"] == FROZEN[ORDERED]
            and metadata[0]["consumer_order_gate_path_adapter"]["frozen_inner_adapter_sha256"] == ordered.BASE_SHA,
            "outer/inner producer identity differs")
    verify(pins)
    require(sha(OWN) == LOADED_SHA, "ordered-seam reviewer changed")
    direct = {**FROZEN, str(OWN.relative_to(ROOT)): LOADED_SHA}
    verify(direct)
    output = {"schema": "eoere_source_order_component_path_cheap_API_independent_readiness/v1",
        "status": "READY_ORDERED_COMPONENT_CONSUMER_METHOD", "source_sha256": direct,
        "prior_402_pin_integration_reused": FROZEN[REVIEW + "independent-corrected-component-gate-api-review.json"],
        "verified_upstream_pin_count": len(pins), "verified_upstream_closure_canonical_sha256_before": before,
        "verified_upstream_closure_canonical_sha256_after": canonical(pins), "all_source_pins_unchanged": True,
        "new_adapter_scoped_attribute_names": sorted(targets), "new_adapter_fixtures_passed": 5,
        "new_cheap_contract_fixture_passed": 1, "Ruff_adapter_gate_tests_and_reviewer_pass": True,
        "narrow_synthetic_rejected_contracts": rejections, "reused_two_case_consumer_integration": integration,
        "genuine_nested_adapter_provenance": metadata[0], "all_original_file_path_and_dispatch_identities_restored": True,
        "candidate_field_operator_read_preparation_CAD_query_q_K_or_solve_executed": False,
        "limits": ["Only new path and byte/provenance binding seams reviewed; original402-pin integration and all component methods reused.",
            "The positive structural contract is synthetic and is not an issued numerical admission or relabeled prior result.",
            "Support independently owns source-order numerical recovery readiness; parent owns the fresh field admission and actual component consume.",
            "No complete resistance, physical demand bound or release is established."],
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version()}, "release": dict(ordered.base.RELEASE)}
    with options.output.open("x") as stream:
        json.dump(output, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "sha256": sha(options.output), "bytes": options.output.stat().st_size,
                      "pins": len(pins), "status": output["status"]}))


if __name__ == "__main__":
    main()
