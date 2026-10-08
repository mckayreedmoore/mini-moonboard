"""Bind the frozen pure reductions to the explicit priority-admission contract.

Only the three receipt-contract constants change in a restored local context.
The actual new receipt and immutable field bytes pass through unchanged.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts import thin_bolted_joint_post_admission as original

GATE = "scripts/thin_bolted_support_priority_admission.py"
SCHEMA = "thin_bolted_independent_support_priority_admission/v1"
SUCCESS = "independent_support_priority_face_source_map_law_and_equilibrium_checks_pass"
FROZEN_REDUCER_SHA256 = "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a"
OWN = str(Path(__file__).resolve().relative_to(original.ROOT))
LOADED_PRODUCER_SHA256 = original.unit.sha(Path(__file__))


def post_priority_admission_reductions(field, admission, *, admission_sha256, samples=41, caller_sections=None):
    """Require fresh priority admission, retaining every frozen data check."""
    pins = {OWN: LOADED_PRODUCER_SHA256,
            str(Path(original.__file__).relative_to(original.ROOT)): FROZEN_REDUCER_SHA256,
            GATE: admission_sha256}
    original.verify_pins(pins)
    original.unit.require(admission.get("schema") == SCHEMA and admission.get(SUCCESS) is True,
                          "the actual fresh priority-admission receipt is required")
    with (patch.object(original, "GATE", GATE),
          patch.object(original, "ADMISSION_SCHEMA", SCHEMA),
          patch.object(original, "ADMISSION_SUCCESS", SUCCESS)):
        result = original.post_admission_reductions(field, admission, admission_sha256=admission_sha256,
                                                   samples=samples, caller_sections=caller_sections)
    original.verify_pins(pins)
    result["source_sha256"].update(pins)
    result["explicit_admission_contract_adapter"] = {
        "producer_path": OWN, "producer_sha256": LOADED_PRODUCER_SHA256,
        "frozen_reducer_sha256": FROZEN_REDUCER_SHA256,
        "admission_gate": GATE, "admission_schema": SCHEMA, "admission_success_key": SUCCESS,
        "only_gate_path_schema_and_success_key_changed": True,
        "receipt_or_field_relabelled": False,
        "forces_coefficients_or_pure_reduction_methods_changed": False,
    }
    return result
