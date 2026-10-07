"""Distinct timber-contact admission adapter over frozen CURRENT steel methods.

Direct wood-face actions belong to full-body admission, not shaft/steel loads.
No washer-face pressure is inferred from the capture director model couple.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path

from scripts import thin_bolted_finite_steel_consumer as base

ROOT, PACKET = base.ROOT, base.PACKET
ADMISSION_MODULE = "scripts.thin_bolted_timber_contact_admission"
ADMISSION_SOURCE = "scripts/thin_bolted_timber_contact_admission.py"
ADMISSION_SCHEMA = "thin_bolted_independent_timber_contact_admission/v1"
ADMISSION_KEY = "independent_finite_timber_contact_support_load_and_equilibrium_checks_pass"
BASE_SOURCE = "scripts/thin_bolted_finite_steel_consumer.py"
BASE_SHA = "1c4573b3c11baaed56c333d3d88653ca816b56e4982176eaf51358dcf6107a28"
BASE_RECEIPT = PACKET / "finite-steel-consumer-method-v4.json"
BASE_RECEIPT_SHA = "0bb1211e5240965b8c038710033af6c8c0916b49f55eaf8ace08398a26f97330"
LOADED_WRITER_SHA256 = base.digest(__file__)


def admit(payload, field, admission_sha256):
    """Only the reviewed new timber-contact gate admits immutable input bytes."""
    base.require(isinstance(admission_sha256, str) and re.fullmatch("[0-9a-f]{64}", admission_sha256) is not None,
                 "explicit reviewed timber-contact admission_sha256 required")
    path = (ROOT/ADMISSION_SOURCE).resolve()
    base.require(base.digest(path) == admission_sha256, "reviewed timber-contact admission source differs")
    gate = importlib.import_module(ADMISSION_MODULE)
    base.require(Path(gate.__file__).resolve() == path and gate.LOADED_PRODUCER_SHA256 == admission_sha256,
                 "loaded timber-contact gate differs from reviewed fixed source")
    receipt = gate.audit_timber_contact_state(payload)
    base.require(receipt.get("schema") == ADMISSION_SCHEMA and receipt.get(ADMISSION_KEY) is True,
                 "new timber-contact admission failed")
    base.require(receipt.get("field_sha256") == hashlib.sha256(payload).hexdigest()
                 and receipt.get("field_canonical_sha256") == base.canonical_sha(field)
                 and all(receipt.get(k) == v for k, v in base.recovery.state_fields(field).items()),
                 "timber-contact receipt belongs to different bytes/state/case/accessory")
    pins = receipt.get("source_sha256", {})
    base.require(pins.get(ADMISSION_SOURCE) == admission_sha256
                 and pins.get("scripts/thin_bolted_finite_frame.py") == base.recovery.FINITE_SHA,
                 "timber-contact receipt omits or changes reviewed gate/current map source")
    base.verify_pins(pins)
    return receipt


def consume(field_path, *, admission_sha256, caller_sections_path=None):
    """Reuse frozen recovery after the distinct complete timber-contact gate."""
    field_path = Path(field_path).resolve()
    payload = field_path.read_bytes()
    field = json.loads(payload)
    base.require(field.get("schema") == base.FIELD_SCHEMA, "new finite timber-contact field required")
    admission = admit(payload, field, admission_sha256)
    base.require(not any(field["release"].values()), "timber-contact components cannot authorize release")
    base.require(base.LOADED_CONSUMER_SHA256 == BASE_SHA, "loaded frozen steel consumer differs")
    pins = {**base.recovery.source_pins(), BASE_SOURCE: BASE_SHA,
            base.bound_path(BASE_RECEIPT): BASE_RECEIPT_SHA, base.bound_path(base.METHOD_RECEIPT): base.METHOD_RECEIPT_SHA}
    base.require(pins.get(base.RECOVERY_SOURCE) == base.RECOVERY_SHA, "frozen current recovery differs")
    base.verify_pins(pins)
    sections, section_bytes = None, None
    if caller_sections_path is not None:
        caller_sections_path = Path(caller_sections_path).resolve()
        section_bytes = caller_sections_path.read_bytes()
        sections = json.loads(section_bytes)
    layout, shafts = base.geometry_inputs()
    values = base.recovery.recover_current_actions(field, field["response"]["q"], layout, shafts, caller_sections=sections)
    base.verify_recovery_census(values)
    base.require(all(values.get(k) == v for k, v in base.recovery.state_fields(field).items()), "current component state differs")
    for group in (field["source_sha256"], admission["source_sha256"], values["source_sha256"]):
        for name, expected in group.items():
            base.require(name not in pins or pins[name] == expected, "timber-contact source bindings disagree")
            pins[name] = expected
    pins.update({base.bound_path(field_path): hashlib.sha256(payload).hexdigest(),
                 base.bound_path(__file__): LOADED_WRITER_SHA256})
    if section_bytes is not None:
        pins[base.bound_path(caller_sections_path)] = hashlib.sha256(section_bytes).hexdigest()
    base.verify_pins(pins)
    base.require(field_path.read_bytes() == payload and
                 (section_bytes is None or caller_sections_path.read_bytes() == section_bytes), "bound component input changed")
    return {**values, "schema": "thin_bolted_timber_contact_steel_components/v1", "candidate": field["candidate"],
        "parameters": field["parameters"], "source_sha256": pins,
        "source_finite_field_path": base.bound_path(field_path), "source_finite_field_sha256": hashlib.sha256(payload).hexdigest(),
        "independent_timber_contact_admission": admission, "supplied_reviewed_admission_sha256": admission_sha256,
        "admitted_direct_timber_face_contact_count": sum(r["kind"] == "timber_face_contact" for r in field["finite_interaction_actions"]),
        "direct_timber_face_contacts_routed_into_steel_or_shaft_loads": False,
        "actual_own_washer_face_pressure_feasibility": None,
        "washer_face_missing_inputs": "current own seating support patch, plane normal and own face wrench; capture director couple is separate",
        "historical_force_or_admission_transferred": False,
        "actual_heel_hole_root_warping_pressure_prying_or_hardware_material_qualified": False,
        "structural_acceptance": False, "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demands", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--caller-sections", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    values = consume(args.demands, admission_sha256=args.admission_sha256, caller_sections_path=args.caller_sections)
    with args.out.open("x") as stream:
        json.dump(values, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "sha256": base.digest(args.out), **base.recovery.state_fields(values)}))


if __name__ == "__main__":
    main()
