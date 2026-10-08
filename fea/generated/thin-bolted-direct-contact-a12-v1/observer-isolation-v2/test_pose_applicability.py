"""Source/route fixtures only; synthetic dispatch is not field admission."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).with_name("pose_applicability.py")
SPEC = importlib.util.spec_from_file_location("current_pose_route_fixture", PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def test_fixed_new_gate_and_frozen_pose_sources():
    assert helper.sha(helper.GATE) == helper.GATE_SHA
    assert helper.sha(helper.POSE) == helper.POSE_SHA
    assert helper.sha(helper.CONFIG) == helper.CONFIG_SHA
    assert "zero first-shaft-roll" in helper.LIMITS[1]
    assert "objective shaft/washer orientation is not recovered" in helper.LIMITS[1]


@pytest.mark.parametrize("failure", ["wrong_gate", "wrong_raw"])
def test_input_rejection_precedes_gate_load_and_vector_dispatch(tmp_path, monkeypatch, failure):
    path = tmp_path / "unadmitted.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(helper, "load", lambda *a: pytest.fail("module dispatch before mandatory bindings"))
    monkeypatch.setattr(helper, "_observe", lambda *a: pytest.fail("unadmitted vectors observed"))
    with pytest.raises(ValueError, match="gate SHA|raw pose field SHA"):
        helper.consume(path, {}, expected_field_sha256="0" * 64 if failure == "wrong_raw" else helper.sha(path),
                       admission_sha256="0" * 64 if failure == "wrong_gate" else helper.GATE_SHA)


@pytest.mark.parametrize("schema", [
    "thin_bolted_independent_complete_timber_admission/v1",
    "thin_bolted_independent_complete_timber_observer_isolation_admission/v1",
])
def test_genuine_new_validator_rejects_unqualified_receipt_before_pose(tmp_path, monkeypatch, schema):
    path = tmp_path / "unadmitted.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(helper, "_observe", lambda *a: pytest.fail("unadmitted vectors observed"))
    with pytest.raises(ValueError, match="actual complete-field admission"):
        helper.consume(path, {"schema": schema}, expected_field_sha256=helper.sha(path), admission_sha256=helper.GATE_SHA)


def test_exact_byte_route_calls_actual_validator_before_pure_pose(tmp_path, monkeypatch):
    # Explicit route stub only. It does not invent a successful domain receipt.
    field = {"state_id": "route-stub", "case_id": "stub", "accessory_placement": "stub",
             "response": {"q": [0.]}, "release": {"capacity_established": False}}
    path = tmp_path / "route-stub.json"
    payload = json.dumps(field).encode()
    path.write_bytes(payload)
    receipt = {"explicit_route_stub_not_admission": True}
    calls = []

    def validate(data, admitted, **kwargs):
        assert data == payload and admitted is receipt and kwargs == {"admission_sha256": helper.GATE_SHA}
        calls.append("new_validator")
        return json.loads(data), {}

    canonical = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    gate = SimpleNamespace(require_admitted_payload=validate,
                           linear=SimpleNamespace(merge_pins=lambda *groups: {k: v for g in groups for k, v in g.items()}))
    method = SimpleNamespace(canonical=canonical)

    def loader(p, digest, name):
        if p == helper.GATE:
            return gate
        assert p == helper.POSE and digest == helper.POSE_SHA and calls == ["new_validator"]
        return method

    def observe(admitted, actual_gate, frozen_pose):
        assert admitted == field and actual_gate is gate and frozen_pose is method
        assert calls == ["new_validator"]
        calls.append("pose_after_admission")
        return {"source_sha256": {}, "explicit_route_stub_not_pose_evaluation": True}

    monkeypatch.setattr(helper, "load", loader)
    monkeypatch.setattr(helper, "_observe", observe)
    out = helper.consume(path, receipt, expected_field_sha256=helper.sha(path), admission_sha256=helper.GATE_SHA)
    assert calls == ["new_validator", "pose_after_admission"]
    assert out["state_id"] == "route-stub" and out["actual_gate_sha256"] == helper.GATE_SHA
    assert out["q_canonical_sha256"] == canonical([0.])
    assert not out["material_K_loaded_assembled_or_evaluated"]
    assert not out["old_main_or_old_field_admission_called"]
    assert receipt == {"explicit_route_stub_not_admission": True}
