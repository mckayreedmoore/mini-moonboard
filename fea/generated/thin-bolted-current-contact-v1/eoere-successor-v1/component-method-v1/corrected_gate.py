"""Source-preserving path adapter for the corrected successor admission gate.

The actual frozen consumer remains at its own path. Only its gate-path
argument and CLI dispatch are scoped; all component algorithms are reused.
"""
from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
BASE = OWN.with_name("assessment.py")
BASE_SHA = "f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0"


def sha(path):
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


LOADED_SHA = sha(OWN)
if sha(BASE) != BASE_SHA:
    raise ValueError("frozen component consumer differs")
SPEC = importlib.util.spec_from_file_location("eoere_frozen_component_consumer", BASE)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
FROZEN_CONSUME = base.consume
GATE = OWN.parent.parent/"four-port-method-v1/first_order_admission_v2.py"


def source_pins():
    pins = {str(BASE.relative_to(base.ROOT)): BASE_SHA, str(OWN.relative_to(base.ROOT)): LOADED_SHA}
    base.verify(pins)
    return pins


@contextmanager
def gate_context():
    """Sequential use only; leave the real __file__/all algorithms untouched."""
    before = source_pins()
    try:
        with patch.object(base, "GATE", GATE):
            yield
    finally:
        base.require(source_pins() == before, "path-adapter sources changed during call")


def consume(field_path, receipt_path, *, expected_field_sha256, admission_sha256, steel_sha256, samples=41):
    """Forward to the unchanged exact-byte consumer with an explicit gate SHA."""
    pins = source_pins()
    pins[str(GATE.relative_to(base.ROOT))] = admission_sha256
    base.verify(pins)
    with gate_context():
        result = FROZEN_CONSUME(field_path, receipt_path, expected_field_sha256=expected_field_sha256,
            admission_sha256=admission_sha256, steel_sha256=steel_sha256, samples=samples)
    base.require(result["fresh_gate_sha256"] == admission_sha256
        and result["raw_field_sha256"] == expected_field_sha256
        and result["source_sha256"].get(str(GATE.relative_to(base.ROOT))) == admission_sha256,
        "forwarded result must bind actual corrected gate and raw bytes")
    base.join(result["source_sha256"], pins)
    result["consumer_gate_path_adapter"] = {
        "schema": "eoere_corrected_gate_component_path_adapter/v1",
        "loaded_wrapper_path": str(OWN.relative_to(base.ROOT)), "loaded_wrapper_sha256": LOADED_SHA,
        "frozen_consumer_path": str(BASE.relative_to(base.ROOT)), "frozen_consumer_sha256": BASE_SHA,
        "actual_gate_path": str(GATE.relative_to(base.ROOT)), "actual_gate_sha256": admission_sha256,
        "original_consumer_file_identity_preserved": True,
        "field_or_admission_payload_modified": False, "component_algorithms_changed": False,
        "historical_PASS_relabelled": False}
    base.verify(result["source_sha256"])
    return result


def main():
    source_pins()
    with patch.object(base, "consume", consume):
        return base.main()


if __name__ == "__main__":
    main()
