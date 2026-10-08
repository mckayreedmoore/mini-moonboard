"""Serialized sparse export dispatch only; no candidate or solve."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("run_first_order_v2.py")
SPEC = importlib.util.spec_from_file_location("eoere_v2_wrapper_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)
TOY_SPEC = importlib.util.spec_from_file_location("eoere_v2_wrapper_genuine_toy", PATH.with_name("test_first_order_factory.py"))
toy = importlib.util.module_from_spec(TOY_SPEC)
TOY_SPEC.loader.exec_module(toy)


def prepared():
    data, panels, integrated = toy.toy()
    return method.core.factory.prepare_synthetic(data, panels, integrated)


@pytest.mark.parametrize("outcome", ["returned-failure", "dispatch-success", "error", "timeout"])
def test_before_solve_bundle_identity_and_three_callback_restoration(tmp_path, monkeypatch, outcome):
    p = prepared()
    before = (method.core.execute, method.core.runtime_pins, method.core.write_exclusive)
    command = ["python", str(PATH), "--synthetic-dispatch-only"]
    calls = []

    def inner(prepared, **kwargs):
        calls.append(kwargs)
        for suffix in (".operators.npz", ".operators.json"):
            path = tmp_path/("fresh.json"+suffix)
            assert path.exists() and kwargs["pins"][str(path)] == method.frame.sha(path)
        assert kwargs["pins"][str(PATH.relative_to(method.frame.ROOT))] == method.LOADED_SHA
        if outcome == "error":
            raise ValueError("synthetic guarded failure")
        if outcome == "timeout":
            raise method.core.CaseWallTimeLimit("synthetic expiry")
        # Dispatch fixture only; no equilibrium/accepted field is asserted.
        return {"schema": "eoere_first_order_common_shaft_four_port_candidate/v1", "execution": {},
            "response": {"q": np.zeros(p.assembly.ndof)}, "source_sha256": kwargs["pins"],
            "original_operator_fingerprint_sha256": method.core.operator_fingerprint(p),
            "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION" if outcome == "dispatch-success" else "FAILED_NO_ACCEPTED_COEFFICIENTS_OR_ACTIONS"}

    monkeypatch.setattr(method, "FROZEN_EXECUTE", inner)
    if outcome in {"error", "timeout"}:
        error = ValueError if outcome == "error" else method.core.CaseWallTimeLimit
        with pytest.raises(error), method.execution_context(tmp_path/"fresh.json", command):
            method.core.execute(p, pins={}, command=command)
    else:
        with method.execution_context(tmp_path/"fresh.json", command) as context:
            field = method.core.execute(p, pins={}, command=command)
            assert field["schema"] == method.SCHEMA and field["operator_bundle"] == context["operator_bundle"]
            assert field["operator_bundle_execution"]["command"] == command
            assert field["execution"]["role"] == "reused_frozen_first_order_core_execution"
            if outcome == "dispatch-success":
                row = field["panel_generalized_coefficients"]["main_lower_left"]
                assert row["coefficients"] == [0.]*len(p.assembly.panel_offsets["main_lower_left"])
                assert row["global_dof_start"] == row["indices"][0]
                assert row["basis_order_per_direction"] == 4
                assert row["knots_normalized"] == [0.]*4+[1.]*4
    assert len(calls) == 1
    assert (method.core.execute, method.core.runtime_pins, method.core.write_exclusive) == before


def test_context_preserves_existing_bundle_before_any_inner_run(tmp_path, monkeypatch):
    arrays, _ = method.bundle_paths(tmp_path/"fresh.json")
    arrays.write_bytes(b"existing immutable operators")
    monkeypatch.setattr(method, "FROZEN_MAIN", lambda: pytest.fail("existing bundle reached preparation"))
    with pytest.raises(ValueError, match="preserve existing"), method.execution_context(tmp_path/"fresh.json", ["not-run"]):
        method.FROZEN_MAIN()
    assert arrays.read_bytes() == b"existing immutable operators"


def test_genuine_outer_wall_failure_has_new_source_and_restores_callbacks(tmp_path, monkeypatch):
    out = tmp_path/"outside.json"
    monkeypatch.setattr(method.sys, "argv", [str(PATH), "--run", "--inputs", "absent.json", "--inputs-sha256", "0"*64,
        "--input-review", "absent-review.json", "--input-review-sha256", "0"*64, "--out", str(out)])
    monkeypatch.setattr(method.core.factory, "read_inputs", lambda *a: (_ for _ in ()).throw(method.core.CaseWallTimeLimit("expiry")))
    monkeypatch.setattr(method.core.signal, "setitimer", lambda *a: None)
    before = (method.core.execute, method.core.runtime_pins, method.core.write_exclusive)
    assert method.main() == 1
    payload = method.core.json.loads(out.with_suffix(".json.interrupted.json").read_bytes())
    assert payload["accepted_q"] is None and payload["accepted_actions"] is None
    assert payload["operator_bundle"] is None
    assert payload["source_sha256"][str(PATH.relative_to(method.frame.ROOT))] == method.LOADED_SHA
    assert payload["last_observation"]["gradient_available"] is False
    assert (method.core.execute, method.core.runtime_pins, method.core.write_exclusive) == before
