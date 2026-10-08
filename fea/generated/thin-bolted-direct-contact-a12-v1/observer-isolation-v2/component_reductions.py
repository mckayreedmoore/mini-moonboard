"""Use the unchanged component bridge with the real new admission path."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BRIDGE = OWN.parent.parent / "component_reductions.py"
BRIDGE_SHA = "3175e0bf079609998f9b1b434ed3fec4c4910bb99f83a42ed96fd1e7fcf5e7bc"
GATE = OWN.with_name("admission.py")
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
if hashlib.sha256(BRIDGE.read_bytes()).hexdigest() != BRIDGE_SHA:
    raise ValueError("frozen component bridge source differs")
_spec = importlib.util.spec_from_file_location("complete_timber_bridge_for_observer_isolation", BRIDGE)
frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frozen)


def consume(field_path, admission, *, expected_field_sha256, admission_sha256, samples=41, caller_sections=None):
    """Scope only GATE; the real new validator authenticates unchanged bytes."""
    pins = {str(BRIDGE.relative_to(ROOT)): BRIDGE_SHA,
            str(GATE.relative_to(ROOT)): GATE_SHA, str(OWN.relative_to(ROOT)): LOADED_SHA}
    frozen.pure.unit.require(admission_sha256 == GATE_SHA, "mandatory reviewed new gate SHA differs")
    frozen.pure.verify_pins(pins)
    previous = frozen.GATE
    try:
        frozen.GATE = GATE
        result = frozen.consume(field_path, admission, expected_field_sha256=expected_field_sha256,
            admission_sha256=admission_sha256, samples=samples, caller_sections=caller_sections)
    finally:
        frozen.GATE = previous
    frozen.pure.unit.require(result["independent_complete_timber_admission"] is admission
                            and result["field_sha256"] == expected_field_sha256,
                            "new receipt and exact payload provenance must remain unchanged")
    for path, digest in pins.items():
        frozen.pure.unit.require(path not in result["source_sha256"] or result["source_sha256"][path] == digest,
                                "new bridge source contradicts result provenance")
        result["source_sha256"][path] = digest
    frozen.pure.verify_pins(result["source_sha256"])
    result["observer_isolation_component_reduction_bridge"] = {
        "source": {"path": str(OWN.relative_to(ROOT)), "sha256": LOADED_SHA},
        "unchanged_component_bridge": {"path": str(BRIDGE.relative_to(ROOT)), "sha256": BRIDGE_SHA},
        "actual_admission": {"path": str(GATE.relative_to(ROOT)), "sha256": GATE_SHA},
        "only_gate_path_scoped_and_restored": frozen.GATE == previous,
        "source_file_identity_or_receipt_schema_success_relabelled": False,
    }
    return result
