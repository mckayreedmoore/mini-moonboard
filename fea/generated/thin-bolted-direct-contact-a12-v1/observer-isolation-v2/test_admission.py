"""Invocation/receipt coupons only; no candidate preparation or solve."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PATH = ROOT / "fea/generated/thin-bolted-direct-contact-a12-v1/observer-isolation-v2/admission.py"
spec = importlib.util.spec_from_file_location("observer_isolation_gate_coupon", PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def field_contract():
    return {"complete_timber_a12_execution": {"observer_isolation": gate.observer_isolation_contract()},
            "source_sha256": dict(gate.FROZEN_PINS)}


def test_real_source_pins_and_truthful_implementation_path():
    before = {key: getattr(gate.frozen, key) for key in
              ("OWN", "PACKET", "DRIVER", "LOADED_PRODUCER_SHA256", "SCHEMA", "SUCCESS")}
    pins = gate.source_pins()
    assert all(pins[path] == sha for path, sha in gate.FROZEN_PINS.items())
    assert pins[gate.OWN] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert Path(gate.frozen.__file__).resolve() == ROOT / gate.FROZEN_GATE
    assert Path(gate.frozen.audit_complete_timber_state.__code__.co_filename).resolve() == ROOT / gate.FROZEN_GATE
    assert before == {key: getattr(gate.frozen, key) for key in before}


def test_explicit_contract_restores_on_exception():
    values = dict(gate.frozen.__dict__)
    with pytest.raises(RuntimeError), gate.explicit_frozen_contract():
        assert gate.frozen.OWN == gate.OWN
        assert gate.frozen.DRIVER == gate.DRIVER
        assert gate.frozen.PACKET == gate.PACKET
        assert gate.frozen.LOADED_PRODUCER_SHA256 == gate.LOADED_PRODUCER_SHA256
        assert gate.frozen.SCHEMA == gate.SCHEMA and gate.frozen.SUCCESS == gate.SUCCESS
        assert Path(gate.frozen.__file__).resolve() == ROOT / gate.FROZEN_GATE
        raise RuntimeError("coupon failure")
    assert values == gate.frozen.__dict__


def test_frozen_audit_creates_new_receipt_on_same_bytes_without_relabel(monkeypatch):
    # A transparent audit seam coupon, not a full mechanics admission.
    payload = json.dumps(field_contract(), indent=2).encode()
    before = dict(gate.frozen.__dict__)
    seen = []

    def seam(same_bytes, **options):
        seen.append((same_bytes, options))
        assert same_bytes is payload
        assert gate.frozen.SCHEMA == gate.SCHEMA
        assert gate.frozen.SUCCESS == gate.SUCCESS
        return {"schema": gate.frozen.SCHEMA, gate.frozen.SUCCESS: True,
                "field_sha256": hashlib.sha256(same_bytes).hexdigest(),
                "field_canonical_sha256": gate.canonical_sha(json.loads(same_bytes))}

    monkeypatch.setattr(gate.frozen, "audit_complete_timber_state", seam)
    receipt = gate.audit_complete_timber_state(payload, driver_sha256="coupon-driver",
        method_receipt_path=gate.PACKET / "coupon-method.json", method_receipt_sha256="coupon-receipt")
    assert receipt["schema"] == gate.SCHEMA and receipt[gate.SUCCESS] is True
    assert receipt["observer_isolation_checks"] == gate.observer_isolation_contract()
    assert seen[0][0] is payload and len(seen) == 1
    assert gate.frozen.OWN == before["OWN"] and gate.frozen.SCHEMA == before["SCHEMA"]
    assert payload == json.dumps(field_contract(), indent=2).encode()


def test_no_old_receipt_is_relabelled(monkeypatch):
    payload = json.dumps(field_contract()).encode()
    old_receipt = {"schema": gate.frozen.SCHEMA, gate.frozen.SUCCESS: True,
                   "field_sha256": hashlib.sha256(payload).hexdigest(),
                   "field_canonical_sha256": gate.canonical_sha(json.loads(payload))}
    monkeypatch.setattr(gate.frozen, "audit_complete_timber_state", lambda *a, **k: old_receipt)
    with pytest.raises(ValueError, match="own exact-byte receipt"):
        gate.audit_complete_timber_state(payload, driver_sha256="coupon", method_receipt_path="coupon",
                                         method_receipt_sha256="coupon")
    assert old_receipt["schema"] != gate.SCHEMA and gate.SUCCESS not in old_receipt


@pytest.mark.parametrize("mutation", ["scope", "copy", "operators", "initialization", "law", "driver", "gate", "source"])
def test_observer_or_frozen_source_mutations_rejected(mutation):
    field = field_contract()
    policy = field["complete_timber_a12_execution"]["observer_isolation"]
    if mutation == "scope": policy["method"] = "change-floor-law"
    elif mutation == "copy": policy["observer_input_rows_copied"] = False
    elif mutation == "operators": policy["solver_operator_inputs_changed"] = True
    elif mutation == "initialization": policy["solver_q_initialization_changed"] = True
    elif mutation == "law": policy["solver_constitutive_laws_changed"] = True
    elif mutation == "driver": policy["frozen_driver"]["sha256"] = "0" * 64
    elif mutation == "gate": policy["frozen_admission"]["path"] = "historical-alias.py"
    elif mutation == "source": del field["source_sha256"][gate.FROZEN_GATE]
    with pytest.raises(ValueError):
        gate._check_observer_contract(field)


@pytest.fixture
def invocation(monkeypatch):
    # Authenticate invocation with the genuine frozen parser and checks.
    # Record reading/pin verification alone are mocked; no field is admitted.
    driver_sha, method_sha = "d" * 64, "a" * 64
    method_path = gate.PACKET / "coupon-method.json"
    out = gate.PACKET / "coupon-case"
    pins = {**gate.FROZEN_PINS, gate.OWN: gate.LOADED_PRODUCER_SHA256,
            gate.DRIVER: driver_sha, gate.ADAPTER: gate.ADAPTER_SHA256,
            gate.PREPARATION: gate.PREPARATION_SHA256}
    method_record = {"path": str(method_path.relative_to(ROOT)), "sha256": method_sha}
    release = {key: False for key in gate.floor_reuse.RELEASE_KEYS}
    receipt = {"schema": "thin_bolted_complete_timber_a12_method_inputs/v1",
        "driver": {"path": gate.DRIVER, "sha256": driver_sha}, "method_checks_pass": True,
        "complete_face_basis": gate.BASIS, "complete_face_scenario": gate.SCENARIO,
        "historical_q_force_or_acceptance_transferred": False, "floor_datum_or_constitutive_law_changed": False,
        "execution_authorization_supplied_by_receipt": False,
        "original_physical_fields_source_sha256": gate.NUMERICAL_SHA256,
        "fixed_options": {"cases": ["a12-rear"], "wood_bedding": 1., "intervals": 8,
            "contact_edge": 70., "newton_limit": 300, "wall_seconds": 600.},
        "expected_census": {"timber": 20, "fittings": 36, "panels": 6, "shafts": 70,
            "bodies": 132, "dofs": 8018, "timber_pairs": 30, "timber_cells": 584,
            "compression_contacts": 1402, "normal_contacts": 1574},
        "release": release, "source_sha256": pins, "observer_isolation": gate.observer_isolation_contract()}
    command = ["python", gate.DRIVER, "--method-input", str(method_path), "--method-input-sha256", method_sha,
               "--out", str(out)]
    execution = {"command": command, "loaded_driver_sha256": driver_sha,
        "loaded_admission_sha256": gate.LOADED_PRODUCER_SHA256, "loaded_adapter_sha256": gate.ADAPTER_SHA256,
        "nested_lean_execution_is_a_reused_internal_call": True, "method_input": method_record,
        "one_case_only": True, "automatic_retries": 0, "wall_time_limit_seconds": 600.,
        "controller": "frozen-lean-common-shaft-incremental-original-cold", "environment": {"OPENBLAS_NUM_THREADS": "1"},
        "warm_initialization": None, "all_30_patches_used_once": True, "original_floor_datum_and_law_preserved": True,
        "new_constitutive_law": False, "native_or_CAD_execution": False,
        "old_q_force_or_acceptance_transfer": False, "observer_isolation": gate.observer_isolation_contract()}
    params = {"complete_timber_a12_driver_sha256": driver_sha, "complete_timber_a12_method_input_sha256": method_sha,
        "beam_size_mm": 150., "shaft_max_segment_mm": 25., "panel_intervals": 8,
        "foundation_port_cell_mm": 70., "floor_corner_contact_n_mm": 25000., "floor_no_slip_xy_penalty_n_mm": 100000.,
        "shaft_steel_E_mpa": 200000., "shaft_steel_nu": .3, "shaft_diameter_scale": 1.,
        "end_capture_stiffness_n_mm": 1000., "Hillman_axial_lateral_stiffness_n_mm": 1000., "fitting_section": "gross",
        "lean_case_wall_time_limit_seconds": 600., "numerical_newton_iteration_limit_per_floor_pattern": 300,
        "wood_radial_foundation_n_mm2": 1000. / 38.1, "plate_radial_foundation_n_mm2": 10000. / 5.55625}
    inner = ["python", "-m", "scripts.run_thin_bolted_linear_timber_frame", "--cases", "a12-rear", "--out", str(out),
        "--wall-seconds", "600", "--newton-limit", "300", "--wood-bedding", "1", "--intervals", "8", "--contact-edge", "70"]
    field = {"complete_timber_a12_execution": execution, "release": release, "source_sha256": pins,
             "lean_joint_execution": {"command": inner}, "common_shaft_execution": {"command": command}, "parameters": params}
    monkeypatch.setattr(gate.frozen, "_read_record", lambda *a: json.dumps(receipt).encode())
    monkeypatch.setattr(gate, "_SOURCE_PINS", lambda extra=None: {**pins, **(extra or {})})
    return field, receipt, {"driver_sha256": driver_sha, "method_receipt_path": method_path,
                            "method_receipt_sha256": method_sha}


def test_genuine_frozen_parser_accepts_explicit_new_path(invocation):
    field, receipt, options = invocation
    before = gate.canonical_sha(field)
    execution, actual_receipt, pins = gate.verify_execution(field, **options)
    assert execution is field["complete_timber_a12_execution"] and actual_receipt == receipt
    assert pins[gate.FROZEN_GATE] == gate.FROZEN_PINS[gate.FROZEN_GATE]
    assert gate.canonical_sha(field) == before


@pytest.mark.parametrize("mutation", ["old_command", "warm", "floor", "old_loaded_gate", "method_scope"])
def test_genuine_parser_and_scope_reject_invocation_mutations(invocation, mutation):
    field, receipt, options = invocation
    if mutation == "old_command": field["complete_timber_a12_execution"]["command"][1] = gate.FROZEN_DRIVER
    elif mutation == "warm": field["complete_timber_a12_execution"]["command"] += ["--warm-start", "old.json"]
    elif mutation == "floor": field["parameters"]["floor_no_slip_xy_penalty_n_mm"] = 1.
    elif mutation == "old_loaded_gate": field["complete_timber_a12_execution"]["loaded_admission_sha256"] = gate.FROZEN_PINS[gate.FROZEN_GATE]
    elif mutation == "method_scope": del receipt["observer_isolation"]
    with pytest.raises(ValueError):
        gate.verify_execution(field, **options)


def test_cheap_validator_rejects_old_receipt_before_operator_replay():
    with pytest.raises(ValueError, match="actual complete-field admission"):
        gate.require_admitted_payload(b"{}", {"schema": gate.frozen.SCHEMA, gate.frozen.SUCCESS: True},
                                       admission_sha256=gate.LOADED_PRODUCER_SHA256)
