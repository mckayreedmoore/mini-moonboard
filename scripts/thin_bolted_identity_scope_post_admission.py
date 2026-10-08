"""Bind unchanged joint reductions to the actual outer identity-scope receipt."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts import thin_bolted_joint_post_admission as original

GATE = "scripts/thin_bolted_support_identity_scope_admission.py"
SCHEMA = "thin_bolted_independent_support_identity_scope_admission/v1"
SUCCESS = "independent_support_identity_scope_face_source_map_law_and_equilibrium_checks_pass"
FROZEN_REDUCER_SHA256 = "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a"
OWN = str(Path(__file__).resolve().relative_to(original.ROOT))
LOADED_PRODUCER_SHA256 = original.unit.sha(Path(__file__))


def post_identity_scope_admission_reductions(field, receipt, *, admission_sha256, samples=41, caller_sections=None):
    """Change only three restored contract constants; pass actual bytes/receipt."""
    pins = {OWN: LOADED_PRODUCER_SHA256,
            str(Path(original.__file__).relative_to(original.ROOT)): FROZEN_REDUCER_SHA256, GATE: admission_sha256}
    original.verify_pins(pins)
    original.unit.require(receipt.get("schema") == SCHEMA and receipt.get(SUCCESS) is True,
                          "actual fresh identity-scope admission receipt required")
    before = original.GATE, original.ADMISSION_SCHEMA, original.ADMISSION_SUCCESS
    with (patch.object(original, "GATE", GATE), patch.object(original, "ADMISSION_SCHEMA", SCHEMA),
          patch.object(original, "ADMISSION_SUCCESS", SUCCESS)):
        result = original.post_admission_reductions(field, receipt, admission_sha256=admission_sha256,
                                                   samples=samples, caller_sections=caller_sections)
    restored = (original.GATE, original.ADMISSION_SCHEMA, original.ADMISSION_SUCCESS) == before
    original.unit.require(restored, "frozen reducer contract constants must be restored")
    original.verify_pins(pins)
    result["source_sha256"].update(pins)
    result["explicit_admission_contract_adapter"] = {
        "producer_path": OWN, "producer_sha256": LOADED_PRODUCER_SHA256,
        "frozen_reducer_sha256": FROZEN_REDUCER_SHA256, "admission_gate": GATE,
        "admission_schema": SCHEMA, "admission_success_key": SUCCESS,
        "only_gate_path_schema_and_success_key_changed": True,
        "frozen_reducer_contract_constants_restored": restored, "receipt_or_field_relabelled": False,
        "forces_coefficients_or_pure_reduction_methods_changed": False}
    return result
