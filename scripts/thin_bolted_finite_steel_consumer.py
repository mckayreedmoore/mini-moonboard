"""Admit a new finite field before frozen CURRENT steel/shaft recovery.

The caller must supply the reviewed digest of the fixed current-state gate.
No CAD, assembly, stiffness, response solve or historical admission is used.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path

from scripts import thin_bolted_common_shaft as shaft_method
from scripts import thin_bolted_finite_steel_recovery as recovery
from scripts import thin_bolted_frame_mechanics as frame

ROOT, PACKET = recovery.ROOT, recovery.PACKET
FIELD_SCHEMA = "thin_bolted_finite_frame_response/v1"
ADMISSION_MODULE = "scripts.thin_bolted_finite_state_audit"
ADMISSION_SOURCE = "scripts/thin_bolted_finite_state_audit.py"
ADMISSION_SCHEMA = "thin_bolted_independent_finite_admission/v1"
ADMISSION_KEY = "independent_finite_current_support_load_and_equilibrium_checks_pass"
RECOVERY_SOURCE = "scripts/thin_bolted_finite_steel_recovery.py"
RECOVERY_SHA = "c8f71a3eebb68e308ff814c5a8995d64c9e571f42556dfacff63280af7a7755a"
METHOD_RECEIPT = PACKET / "finite-steel-recovery-method-v4.json"
METHOD_RECEIPT_SHA = "fcac5af8927859bdc05dc360c787c418a1a801a02751b894f27fb1213b31f5d0"
LOADED_CONSUMER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def bound_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def verify_pins(pins):
    for name, expected in pins.items():
        require(isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None,
                "source binding requires a lowercase SHA256 digest")
        require(digest(ROOT/name) == expected, "finite steel bound source changed: " + name)


def admission_module(admission_sha256):
    require(isinstance(admission_sha256, str) and re.fullmatch("[0-9a-f]{64}", admission_sha256) is not None,
            "explicit reviewed finite admission_sha256 is required")
    path = (ROOT/ADMISSION_SOURCE).resolve()
    require(digest(path) == admission_sha256, "reviewed finite admission digest differs from the fixed new gate")
    module = importlib.import_module(ADMISSION_MODULE)
    require(Path(module.__file__).resolve() == path, "finite admission imported from a different source path")
    require(getattr(module, "LOADED_PRODUCER_SHA256", None) == admission_sha256,
            "loaded finite admission code differs from the reviewed gate digest")
    require(digest(path) == admission_sha256, "finite admission source changed during import")
    return module


def require_admission(field_path, payload, field, admission_sha256):
    """Bind a reviewed current-state receipt to the exact immutable JSON input."""
    module = admission_module(admission_sha256)
    receipt = module.audit_finite_state(field_path)
    require(receipt.get("schema") == ADMISSION_SCHEMA and receipt.get(ADMISSION_KEY) is True,
            "new finite current-state admission failed")
    require(receipt.get("field_sha256") == hashlib.sha256(payload).hexdigest()
            and receipt.get("field_canonical_sha256") == canonical_sha(field),
            "finite admission receipt belongs to different input bytes or parsed field")
    require(all(receipt.get(key) == value for key, value in recovery.state_fields(field).items()),
            "finite admission receipt mixes state/case/accessory identity")
    pins = receipt.get("source_sha256", {})
    require(pins.get(ADMISSION_SOURCE) == admission_sha256
            and pins.get("scripts/thin_bolted_finite_frame.py") == recovery.FINITE_SHA,
            "finite admission receipt omits or changes the reviewed gate/map source")
    verify_pins(pins)
    require(field_path.read_bytes() == payload, "finite field changed during independent admission")
    return receipt


def geometry_inputs():
    require(digest(frame.LAYOUT) == frame.LAYOUT_SHA, "frozen fitting/shaft layout differs")
    return json.loads(frame.LAYOUT.read_bytes()), shaft_method.read_inputs()


def verify_recovery_census(values):
    expected = {"current_shaft_section_cut_actions": 70, "current_steel_port_actions": 72,
                "current_flange_section_actions": 72, "current_shaft_circle_references": 70,
                "current_own_washer_capture_actions": 140}
    require(all(len(values.get(key, [])) == count for key, count in expected.items())
            and values.get("own_metal_role_gravity_count") == 350,
            "complete current70 shaft/72 flange/140 capture/350 role recovery required")


def consume(field_path, *, admission_sha256, caller_sections_path=None):
    """Public writer API; admission digest is mandatory and never inferred."""
    field_path = Path(field_path).resolve()
    payload = field_path.read_bytes()
    field = json.loads(payload)
    require(field.get("schema") == FIELD_SCHEMA, "new finite field required; reference/failed state cannot be relabelled")
    admission = require_admission(field_path, payload, field, admission_sha256)
    require(not any(field["release"].values()), "finite component consumer cannot authorize release")
    dependency_pins = recovery.source_pins()
    require(dependency_pins.get(RECOVERY_SOURCE) == RECOVERY_SHA
            and digest(METHOD_RECEIPT) == METHOD_RECEIPT_SHA, "frozen current recovery or method receipt differs")
    sections, section_bytes = None, None
    if caller_sections_path is not None:
        caller_sections_path = Path(caller_sections_path).resolve()
        section_bytes = caller_sections_path.read_bytes()
        sections = json.loads(section_bytes)
    layout, shafts = geometry_inputs()
    values = recovery.recover_current_actions(field, field["response"]["q"], layout, shafts, caller_sections=sections)
    verify_recovery_census(values)
    require(all(values.get(key) == value for key, value in recovery.state_fields(field).items()),
            "current recovery returns a different state/case/accessory")
    pins = dict(dependency_pins)
    for group in (field["source_sha256"], admission["source_sha256"], values["source_sha256"]):
        for name, expected in group.items():
            require(name not in pins or pins[name] == expected, "finite input/admission/recovery source bindings disagree")
            pins[name] = expected
    pins.update({bound_path(field_path): hashlib.sha256(payload).hexdigest(),
                 bound_path(METHOD_RECEIPT): METHOD_RECEIPT_SHA,
                 bound_path(__file__): LOADED_CONSUMER_SHA256})
    if section_bytes is not None:
        pins[bound_path(caller_sections_path)] = hashlib.sha256(section_bytes).hexdigest()
    verify_pins(pins)
    require(field_path.read_bytes() == payload, "finite field changed during component recovery")
    require(section_bytes is None or caller_sections_path.read_bytes() == section_bytes,
            "caller body/root scenarios changed during component recovery")
    return {**values, "schema": "thin_bolted_admitted_finite_steel_components/v1", "candidate": field["candidate"],
        "parameters": field["parameters"], "source_sha256": pins,
        "source_finite_field_path": bound_path(field_path), "source_finite_field_sha256": hashlib.sha256(payload).hexdigest(),
        "independent_finite_current_admission": admission, "supplied_reviewed_admission_sha256": admission_sha256,
        "old_reference_datum_actions_or_gate_relabelled": False,
        "actual_heel_hole_warping_root_washer_pressure_prying_or_material_qualified": False,
        "physical_demand_bounds_or_continuous_extrema_established": False,
        "structural_acceptance": False, "complete_joint_acceptance": False,
        "fabrication_release": False, "climbing_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demands", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--caller-sections", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = consume(args.demands, admission_sha256=args.admission_sha256, caller_sections_path=args.caller_sections)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "sha256": digest(args.out), "bytes": args.out.stat().st_size,
                      **recovery.state_fields(report), "structural_acceptance": False}))


if __name__ == "__main__":
    main()
