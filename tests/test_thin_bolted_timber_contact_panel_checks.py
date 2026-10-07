"""New admission/delegation controls; frozen panel/kinematic coupons reused."""

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import thin_bolted_timber_contact_panel_checks as checks


def field_fixture():
    layout = json.loads(checks.method.LAYOUT.read_bytes())
    identity = {"state_id": "new-timber-contact-coupon", "case_id": "a12-rear", "accessory_placement": "original_top"}
    actions = [{"id": row["axis_id"], "kind": "panel_screw", **identity} for row in layout["screw_axes"]]
    actions.extend({"id": f"compression-{i}", "kind": "panel_contact", **identity} for i in range(530))
    actions.append({"id": "new-wood-contact", "kind": "timber_contact", **identity})
    corrections = [{"panel": name, "kind": kind, **identity} for name in checks.method.PANELS
                   for kind in checks.reused.CORRECTION_KINDS]
    return {"schema": checks.reused.FIELD_SCHEMA, "candidate": "thin-development", "revision": "new-contact-method-coupon",
        **identity, "parameters": {"panel_intervals": 8, "foundation_port_cell_mm": 70.},
        "source_sha256": {}, "release": {"fabrication_released": False},
        "response": {"q": [17.]}, "finite_kinematic_map": {"ndof": 1},
        "finite_interaction_actions": actions, "panel_generalized_load_corrections": corrections}


def gate_fixture(tmp_path, monkeypatch, state=None, mutate=None):
    state = field_fixture() if state is None else state
    payload = json.dumps(state).encode()
    path = tmp_path/"new-timber-contact.json"; path.write_bytes(payload)
    pin = "1"*64
    original = checks.method.sha
    monkeypatch.setattr(checks.method, "sha", lambda p: pin if PathLike(p) == checks.ROOT/checks.GATE_SOURCE else original(p))
    seen = []

    def audit(data):
        assert isinstance(data, bytes) and data == payload
        seen.append(data)
        result = {"schema": checks.GATE_SCHEMA, checks.GATE_KEY: True,
            **{key: state[key] for key in checks.IDENTITY_KEYS}, "field_sha256": hashlib.sha256(data).hexdigest(),
            "field_canonical_sha256": checks.canonical_sha(state), "source_sha256": {checks.GATE_SOURCE: pin}}
        if mutate:
            mutate(result, path)
        return result

    gate = SimpleNamespace(__file__=str(checks.ROOT/checks.GATE_SOURCE), LOADED_PRODUCER_SHA256=pin,
                           audit_timber_contact_state=audit)
    monkeypatch.setattr(checks.importlib, "import_module", lambda module: gate if module == checks.GATE_MODULE
                        else (_ for _ in ()).throw(AssertionError("old gate import attempted")))
    return path, pin, gate, seen


def PathLike(value):
    return checks.Path(value).resolve()


def test_new_gate_uses_one_payload_and_binds_new_identity(tmp_path, monkeypatch):
    path, pin, _, seen = gate_fixture(tmp_path, monkeypatch)
    returned_path, payload, field, receipt, pins = checks.admit(path, pin)
    assert seen == [payload] and returned_path == path
    assert receipt["state_id"] == field["state_id"]
    assert pins[checks.GATE_SOURCE] == pin
    assert pins[checks.source_name(path)] == hashlib.sha256(payload).hexdigest()
    assert pins["scripts/thin_bolted_finite_panel_consumer.py"] == checks.REUSED_SHA


@pytest.mark.parametrize("mutation", ["fail", "schema", "raw_hash", "canonical_hash", "state", "source", "replace_path"])
def test_wrong_new_admission_or_changed_payload_is_rejected(tmp_path, monkeypatch, mutation):
    def mutate(receipt, path):
        if mutation == "fail":
            receipt[checks.GATE_KEY] = False
        elif mutation == "schema":
            receipt["schema"] = "thin_bolted_independent_finite_admission/v1"
        elif mutation == "raw_hash":
            receipt["field_sha256"] = "0"*64
        elif mutation == "canonical_hash":
            receipt["field_canonical_sha256"] = "0"*64
        elif mutation == "state":
            receipt["state_id"] = "other-timber-state"
        elif mutation == "source":
            receipt["source_sha256"][checks.GATE_SOURCE] = "0"*64
        else:
            field = json.loads(path.read_bytes()); field["response"]["q"] = [99.]
            path.write_text(json.dumps(field))
    path, pin, _, _ = gate_fixture(tmp_path, monkeypatch, mutate=mutate)
    with pytest.raises(ValueError):
        checks.admit(path, pin)


@pytest.mark.parametrize("mutation", ["wrong_path", "loaded_source", "missing_pin", "wrong_pin", "old_field", "fine_contacts"])
def test_fixed_module_pin_and_initial_panel_scope_are_required(tmp_path, monkeypatch, mutation):
    state = field_fixture()
    if mutation == "old_field":
        state["schema"] = "thin_bolted_frame_response/v1"
    elif mutation == "fine_contacts":
        state["parameters"]["foundation_port_cell_mm"] = 35.
    path, pin, gate, _ = gate_fixture(tmp_path, monkeypatch, state)
    if mutation == "wrong_path":
        gate.__file__ = str(tmp_path/"other_gate.py")
    elif mutation == "loaded_source":
        gate.LOADED_PRODUCER_SHA256 = "0"*64
    elif mutation == "missing_pin":
        pin = None
    elif mutation == "wrong_pin":
        pin = "0"*64
    with pytest.raises(ValueError):
        checks.admit(path, pin)


def test_wrapper_delegates_all66_actions_six_fields_and_twelve_terms(tmp_path, monkeypatch):
    path, pin, _, _ = gate_fixture(tmp_path, monkeypatch)
    panels = {name: object() for name in checks.method.PANELS}
    q = np.array([17.]); seen = {"screws": [], "sections": [], "corrections": []}
    monkeypatch.setattr(checks, "panels_from_map", lambda field: (panels, q))

    def screw(panel, saved_q, source, action):
        assert panel is panels[source["panel"]] and saved_q is q
        seen["screws"].append(action["id"])
        return {**action, "panel": source["panel"], "withdrawal_n": float(len(seen["screws"]))}

    def section(panel, saved_q, samples):
        assert saved_q is q and samples == 7
        seen["sections"].append(panel)
        return {"delegated_section": True}

    def correction(panel, saved_q, rows):
        assert saved_q is q and len(rows) == 2
        seen["corrections"].extend(rows)
        return {"physical_forces_assigned": False}

    monkeypatch.setattr(checks.reused, "current_screw_diagnostics", screw)
    monkeypatch.setattr(checks.reused, "section_diagnostics", section)
    monkeypatch.setattr(checks.reused, "correction_diagnostics", correction)
    result = checks.evaluate(path, 7, admission_sha256=pin)
    assert len(seen["screws"]) == len(set(seen["screws"])) == 66
    assert len(seen["sections"]) == 6 and len(seen["corrections"]) == 12
    assert result["maximum_head_witness"]["withdrawal_n"] == 66.
    assert result["method"]["frozen_panel_functions_reused"] and not result["method"]["old_gate_used"]
    assert not any(result["release"].values()) and not result["complete_panel_resistance_established"]


def test_mixed_same_case_state_actions_are_rejected_before_diagnostics(tmp_path, monkeypatch):
    state = field_fixture(); state["finite_interaction_actions"][0]["state_id"] = "other"
    path, pin, _, _ = gate_fixture(tmp_path, monkeypatch, state)
    monkeypatch.setattr(checks, "panels_from_map", lambda _: ({name: object() for name in checks.method.PANELS}, np.array([17.])))
    with pytest.raises(ValueError, match="mix identities"):
        checks.evaluate(path, admission_sha256=pin)


def test_local_kinematics_reuses_map_API_after_same_new_gate(tmp_path, monkeypatch):
    from scripts import thin_bolted_finite_kinematics as kinematics
    path, pin, _, _ = gate_fixture(tmp_path, monkeypatch)
    seen = []
    monkeypatch.setattr(kinematics.spans_method, "read_member_span_geometry", lambda: {"coupon": {"basis_grain_u_v_xyz": np.eye(3).tolist()}})

    def evaluate_map(mapping, q, basis):
        seen.append((mapping, q, basis))
        return {"no_global_CAD_K_material_energy_or_equilibrium_solve": True, "release": {"fabrication_released": False}}

    monkeypatch.setattr(kinematics, "evaluate_map", evaluate_map)
    report = checks.evaluate_local_kinematics(path, admission_sha256=pin)
    assert seen[0][1] == [17.] and "coupon" in seen[0][2]
    assert report["no_global_CAD_K_material_energy_or_equilibrium_solve"]
    assert report["source_sha256"]["scripts/thin_bolted_finite_kinematics.py"] == checks.KINEMATICS_SHA
    assert report["finite_admission"][checks.GATE_KEY] is True
