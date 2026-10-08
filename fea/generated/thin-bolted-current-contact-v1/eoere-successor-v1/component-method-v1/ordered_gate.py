"""Forward the frozen component path adapter to the owned-ID order gate.

No component algorithm, field, action or admission receipt is rewritten.
"""
from __future__ import annotations

import hashlib
import importlib.util
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
BASE = OWN.with_name("corrected_gate.py")
BASE_SHA = "42c2ae96e2f25e7fb16cbdd3cfe390a620c312bfe9db072d2363bd559e9b35cc"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(BASE.read_bytes()).hexdigest() != BASE_SHA:
    raise ValueError("frozen corrected component adapter differs")
SPEC = importlib.util.spec_from_file_location("eoere_frozen_corrected_component", BASE)
reused = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reused)
base = reused.base
FROZEN_CONSUME = reused.consume
GATE = OWN.parent.parent/"four-port-method-v1/first_order_admission_v3.py"


def source_pins():
    pins = {**reused.source_pins(), str(BASE.relative_to(base.ROOT)): BASE_SHA,
            str(OWN.relative_to(base.ROOT)): LOADED_SHA}
    base.verify(pins)
    return pins


@contextmanager
def gate_context():
    """Sequential invocation; frozen nested scopes restore their own globals."""
    before = source_pins()
    try:
        with patch.object(reused, "GATE", GATE):
            yield
    finally:
        base.require(source_pins() == before, "ordered gate adapter sources changed")


def consume(field_path, receipt_path, *, expected_field_sha256, admission_sha256, steel_sha256, samples=41):
    pins = source_pins()
    pins[str(GATE.relative_to(base.ROOT))] = admission_sha256
    base.verify(pins)
    with gate_context():
        result = FROZEN_CONSUME(field_path, receipt_path, expected_field_sha256=expected_field_sha256,
            admission_sha256=admission_sha256, steel_sha256=steel_sha256, samples=samples)
    base.require(result["fresh_gate_sha256"] == admission_sha256
        and result["raw_field_sha256"] == expected_field_sha256
        and result["source_sha256"].get(str(GATE.relative_to(base.ROOT))) == admission_sha256,
        "ordered consumer must bind actual new gate and raw field")
    base.join(result["source_sha256"], pins)
    result["consumer_order_gate_path_adapter"] = {
        "schema": "eoere_owned_id_order_gate_component_path_adapter/v1",
        "loaded_outer_path": str(OWN.relative_to(base.ROOT)), "loaded_outer_sha256": LOADED_SHA,
        "frozen_inner_adapter_path": str(BASE.relative_to(base.ROOT)), "frozen_inner_adapter_sha256": BASE_SHA,
        "frozen_consumer_path": str(reused.BASE.relative_to(base.ROOT)), "frozen_consumer_sha256": reused.BASE_SHA,
        "actual_gate_path": str(GATE.relative_to(base.ROOT)), "actual_gate_sha256": admission_sha256,
        "all_original_module_file_identities_preserved": True,
        "field_or_admission_payload_modified": False, "component_algorithms_changed": False,
        "old_PASS_relabelled": False}
    base.verify(result["source_sha256"])
    return result


def main():
    source_pins()
    with patch.object(reused, "consume", consume):
        return reused.main()


if __name__ == "__main__":
    main()
