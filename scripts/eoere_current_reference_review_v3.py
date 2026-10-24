"""Strengthen replay intake while retaining the frozen V2 formula adapters.

No existing report, source map, preparation or response is changed. Every
candidate intake checks its issued plywood certificates against the field's
hash-bound captured coordinate map before a worksheet or probe can start.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts import eoere_current_reference_review_v2 as previous
from scripts import eoere_replay_certificate as certificate
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha

OWN = Path(__file__).resolve()
LOADED_SHA = sha(OWN)
PREVIOUS = Path(previous.__file__).resolve()
PREVIOUS_SHA = "a97e02e138302a15fb48e631259ddb0c68f0f821210f1dd5a99e3993eabad7e2"
VALIDATOR = Path(certificate.__file__).resolve()
VALIDATOR_LOADED_SHA = sha(VALIDATOR)
ISSUED_REPLAY_PRODUCER = {
    "path": "scripts/replay_eoere_leg_header.py",
    "sha256": "9897c23cc967179f7633e7b27f8172eeac0b23a6d107e3b95790e9a4d6efcf7f",
}
SUMMARIZE_BRACING = previous.previous.summarize_bracing
require = certificate.require


def _pin_reference(binding: Mapping[str, Any], pins: dict[str, str]) -> Path:
    certificate.validate_reference(binding)
    target = (ROOT / binding["path"]).resolve()
    require(target.is_relative_to(ROOT), "repository replay source required")
    require(ref(target) == binding, "hash-bound replay source changed: " + binding["path"])
    require(pins.get(binding["path"], binding["sha256"]) == binding["sha256"],
            "conflicting replay source pin: " + binding["path"])
    pins[binding["path"]] = binding["sha256"]
    return target


def verify_plywood_certificate(
    field: Mapping[str, Any], field_ref: Mapping[str, Any], pins: dict[str, str]
) -> None:
    """Read and authenticate one field's manifest and issued replay certificate."""
    certificate.validate_reference(field_ref)
    manifest_ref = field["operator_bundle"]["manifest"]
    manifest_path = _pin_reference(manifest_ref, pins)
    manifest = read(manifest_path, pins, manifest_ref["sha256"])
    expected = certificate.bonded_plywood_dofs(manifest)
    replay_path = ROOT / Path(field_ref["path"]).parent / "independent-replay-plywood.json"
    replay_ref = ref(replay_path)
    replay_path = _pin_reference(replay_ref, pins)
    replay = read(replay_path, pins, replay_ref["sha256"])
    certificate.validate_plywood_replay(
        replay, field_ref=field_ref, material_ref=field["source_inputs"]["plywood_material"],
        expected_dofs=expected,
    )
    require(replay["source"] == ISSUED_REPLAY_PRODUCER,
            "exact issued plywood replay producer required")
    source_input = field["source_input_review"]["input"]
    certificate.validate_reference(source_input)
    expected_launcher = {
        "path": str(Path(source_input["path"]).parent / "producer-snapshot.py"),
        "sha256": field["source_sha256"].get("scripts/eoere_leg_header_mechanics.py"),
    }
    require(replay["captured_launcher"] == expected_launcher,
            "captured launcher must match the field's source-input directory and mechanics digest")
    _pin_reference(source_input, pins)
    for name in ("source", "captured_launcher"):
        _pin_reference(replay[name], pins)


def _method_pins() -> dict[str, str]:
    pins = {}
    for path, expected in (
        (PREVIOUS, PREVIOUS_SHA), (VALIDATOR, VALIDATOR_LOADED_SHA), (OWN, LOADED_SHA),
    ):
        require(sha(path) == expected, "loaded V3 replay intake source changed: " + str(path))
        binding = ref(path)
        pins[binding["path"]] = binding["sha256"]
    return pins


class Intake(previous.Intake):
    def load(self):
        method_pins = _method_pins()
        geometry, fields, pins = super().load()
        for _, _, binding, field in fields:
            verify_plywood_certificate(field, binding, pins)
        for path, digest in method_pins.items():
            require(pins.get(path, digest) == digest, "conflicting V3 intake source pin: " + path)
            pins[path] = digest
        require(_method_pins() == method_pins, "V3 replay intake changed during validation")
        return geometry, fields, pins


def summarize_bracing(analysis, out, public, bindings, reference):
    # The frozen summary path does not otherwise use CurrentIntake. Admit its
    # certificates before it can write, without recomputing any bracing probe.
    Intake(bindings, analysis).load()
    return SUMMARIZE_BRACING(analysis, out, public, bindings, reference)


def main():
    _method_pins()
    with patch.object(previous, "Intake", Intake), \
            patch.object(previous.previous, "summarize_bracing", summarize_bracing):
        previous.main()


if __name__ == "__main__":
    main()
