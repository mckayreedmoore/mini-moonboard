"""Explicit new admission contract around the immutable complete-contact gate.

The frozen gate executes its checks on the original bytes and creates this
leaf's receipt directly. Only its invocation and receipt contract constants
change; its source path, physics and validation algorithms remain unchanged.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DRIVER = str(PACKET.relative_to(ROOT) / "runner.py")
SCHEMA = "thin_bolted_independent_complete_timber_observer_isolation_admission/v1"
SUCCESS = "independent_complete_timber_observer_isolation_face_source_map_original_gradient_and_equilibrium_checks_pass"
FROZEN_GATE = "fea/generated/thin-bolted-direct-contact-a12-v1/admission.py"
FROZEN_DRIVER = "fea/generated/thin-bolted-direct-contact-a12-v1/runner.py"
FROZEN_PINS = {
    FROZEN_GATE: "6797388b8a99e1f2d510d69c22ce932283b8128607842337e9cea300ae3fb5be",
    FROZEN_DRIVER: "ea3b310657b66869b59c35b5cb126280df5b042b8c50e9848d463b3a9b5eef01",
    "fea/generated/thin-bolted-direct-contact-a12-v1/test_admission.py":
        "1133fe49e257b4c5e4c54c49f1298acf49c9853df9da21ce80c2585e04126241",
    "fea/generated/thin-bolted-direct-contact-a12-v1/test_runner.py":
        "65d183868bfa41506340567aff596e9a20f757c154f3805452756b3f227baeb5",
}
for _path, _sha in FROZEN_PINS.items():
    if hashlib.sha256((ROOT / _path).read_bytes()).hexdigest() != _sha:
        raise ValueError("frozen observer-isolation reuse source changed: " + _path)
_spec = importlib.util.spec_from_file_location("complete_timber_frozen_gate_for_observer_isolation", ROOT / FROZEN_GATE)
frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frozen)
linear = frozen.linear
require = frozen.require
canonical_sha = frozen.canonical_sha
_SOURCE_PINS = frozen.source_pins
_VERIFY_EXECUTION = frozen.verify_execution


def observer_isolation_contract():
    return {"schema": "thin_bolted_complete_timber_observer_isolation/v1",
        "method": "copy-floor-tangent-B-for-enabled-host-observation",
        "frozen_driver": {"path": FROZEN_DRIVER, "sha256": FROZEN_PINS[FROZEN_DRIVER]},
        "frozen_admission": {"path": FROZEN_GATE, "sha256": FROZEN_PINS[FROZEN_GATE]},
        "observer_input_rows_copied": True,
        "solver_operator_inputs_changed": False,
        "solver_q_initialization_changed": False,
        "solver_constitutive_laws_changed": False}


def _check_observer_contract(field, method_receipt=None):
    expected = observer_isolation_contract()
    require(field["complete_timber_a12_execution"].get("observer_isolation") == expected,
            "source-bound observer-only isolation contract required")
    require(all(field["source_sha256"].get(path) == sha for path, sha in FROZEN_PINS.items()),
            "current field must retain exact frozen validation and driver sources")
    if method_receipt is not None:
        require(method_receipt.get("observer_isolation") == expected,
                "reviewed method receipt omits observer-only isolation contract")
    return expected


def _scoped_source_pins(additional=None):
    return _SOURCE_PINS(linear.merge_pins(FROZEN_PINS, additional or {}))


def _scoped_verify_execution(field, **options):
    execution, receipt, pins = _VERIFY_EXECUTION(field, **options)
    _check_observer_contract(field, receipt)
    return execution, receipt, pins


@contextmanager
def explicit_frozen_contract():
    """Scope contract values in our private module, preserving genuine code."""
    values = {"OWN": OWN, "PACKET": PACKET, "DRIVER": DRIVER,
        "LOADED_PRODUCER_SHA256": LOADED_PRODUCER_SHA256, "SCHEMA": SCHEMA, "SUCCESS": SUCCESS,
        "source_pins": _scoped_source_pins, "verify_execution": _scoped_verify_execution}
    before = {key: getattr(frozen, key) for key in values}
    try:
        for key, value in values.items():
            setattr(frozen, key, value)
        yield frozen
    finally:
        for key, value in before.items():
            setattr(frozen, key, value)


def source_pins(additional=None):
    with explicit_frozen_contract():
        return frozen.source_pins(additional)


def verify_execution(field, **options):
    with explicit_frozen_contract():
        return frozen.verify_execution(field, **options)


def replay_original_gradient(*args, **kwargs):
    return frozen.replay_original_gradient(*args, **kwargs)


def audit_complete_timber_state(path_or_bytes, *, driver_sha256, method_receipt_path, method_receipt_sha256):
    """Run the unchanged complete gate under this explicit new contract."""
    with explicit_frozen_contract():
        receipt = frozen.audit_complete_timber_state(path_or_bytes, driver_sha256=driver_sha256,
            method_receipt_path=method_receipt_path, method_receipt_sha256=method_receipt_sha256)
    payload = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    field = json.loads(payload)
    checks = _check_observer_contract(field)
    require(receipt["schema"] == SCHEMA and receipt.get(SUCCESS) is True
            and receipt["field_sha256"] == hashlib.sha256(payload).hexdigest()
            and receipt["field_canonical_sha256"] == canonical_sha(field),
            "new gate must issue its own exact-byte receipt directly")
    receipt["observer_isolation_checks"] = checks
    return receipt


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    with explicit_frozen_contract():
        field, pins = frozen.require_admitted_payload(field_bytes, receipt, admission_sha256=admission_sha256)
    require(receipt.get("observer_isolation_checks") == _check_observer_contract(field),
            "actual observer-isolation admission receipt required")
    return field, pins


def __getattr__(name):
    """Expose the same immutable pure geometry/law APIs to the new runner."""
    return getattr(frozen, name)
