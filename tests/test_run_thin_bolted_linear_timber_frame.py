"""The bounded orchestration restores contact without replacing mechanics."""

import signal
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_thin_bolted_linear_timber_frame as driver


def test_one_case_scope_rejects_a_sweep_or_failed_warm_vector(monkeypatch):
    for extra in (["--cases", "a12-rear", "a12-front"],
                  ["--warm-start", "old-failed.json"],
                  ["--newton-limit", "301"]):
        monkeypatch.setattr(sys, "argv", ["driver", *extra])
        with pytest.raises(SystemExit):
            driver.main()


def test_wall_limit_restores_alarm_and_diagnostic_does_not_become_actions():
    old_handler = signal.getsignal(signal.SIGALRM)
    with driver.wall_limit(1.):
        assert signal.getitimer(signal.ITIMER_REAL)[0] > 0.
    assert signal.getitimer(signal.ITIMER_REAL) == (0., 0.)
    assert signal.getsignal(signal.SIGALRM) == old_handler
    for invalid in (0., -1., 1801., float("nan")):
        with pytest.raises(ValueError), driver.wall_limit(invalid):
            pytest.fail("invalid wall limit accepted")
    response = driver.failed_wall_response({"q": np.ones(2), "gradient_inf_n": .001})
    assert response["converged"] is False
    assert "q" not in response
    assert response["diagnostic_last_q_is_a_converged_or_accepted_force_field"] is False
    assert response["physical_residual_uses_unmodified_laws"] is True


def test_append_bind_and_solver_reuse_are_one_restored_joint_path(monkeypatch):
    captured = {}
    contacts = [{"id": "old-contact"}]
    extra = [{"id": "paired-wood-contact"}]
    coordinate_map = {"schema": "fixture-map"}
    monkeypatch.setattr(driver.frame, "elastic_connections", lambda *a, **k: ([], contacts, []))
    monkeypatch.setattr(driver.faces, "prepare_linear_timber_faces", lambda *a, **k: {
        "contacts": extra, "coordinate_map": coordinate_map,
        "metadata": {"method": "linear-face-fixture", "parameters": {"bedding": 1.}},
        "source_sha256": {}})
    monkeypatch.setattr(driver.saved_panels, "reuse_panel_operators", lambda: (
        {"saved-panel-fixture": True}, {}, {"saved_reference_geometry_and_operators_reused": True}))

    def stamp(report, prepared, q):
        captured["stamp"] = (prepared, q.copy())
        return {**report, "timber_face_contact_actions": ["all-fixture-rows"]}

    def frozen_metadata(report, system, pins, command):
        captured["command"] = command
        return report

    def frozen_solver(*a, **k):
        captured["solver_options"] = k
        return {"converged": False}

    def frozen_main():
        assembly = SimpleNamespace()
        panels, _, _ = driver.panel_tools.prepare_panel_models(driver.frame.GEOMETRY_CACHE,
                                                               intervals=8, contact_edge=70.)
        assert panels == {"saved-panel-fixture": True}
        captured["contacts"] = driver.frame.elastic_connections(assembly)[1]
        with pytest.raises(ValueError, match="one prepared case"):
            driver.frame.elastic_connections(assembly)
        driver.incremental.compatible_contact_solve(None, max_iterations=300, warm_q=None)
        report = {"parameters": {}, "source_sha256": {}, "counts": {},
                  "response": {"q": [1., 2.]}, "limits": []}
        captured["report"] = driver.common.bind_common_metadata(report, None, {}, [])
        captured["argv"] = sys.argv.copy()

    old_connections = driver.frame.elastic_connections
    monkeypatch.setattr(driver.faces, "stamp_recovered_actions", stamp)
    monkeypatch.setattr(driver.common, "bind_common_metadata", frozen_metadata)
    monkeypatch.setattr(driver.incremental, "compatible_contact_solve", frozen_solver)
    monkeypatch.setattr(driver.reused, "main", frozen_main)
    monkeypatch.setattr(sys, "argv", ["driver", "--cases", "a12-rear", "--out", "unused.json"])
    driver.main()
    assert captured["contacts"] == contacts + extra
    assert captured["solver_options"] == {"max_iterations": 300, "warm_q": None}
    assert captured["report"]["linear_timber_coordinate_map"] == coordinate_map
    assert captured["report"]["counts"]["paired_timber_compression_cells"] == 272
    assert captured["command"][2] == "scripts.run_thin_bolted_linear_timber_frame"
    assert captured["report"]["lean_joint_execution"]["automatic_retries"] == 0
    assert "--newton-limit" in captured["argv"]
    assert driver.frame.elastic_connections is old_connections
    assert driver.incremental.compatible_contact_solve is frozen_solver


def test_wall_stop_inside_solver_preserves_failed_protocol(monkeypatch):
    def interrupted(*args, **kwargs):
        raise driver.CaseWallTimeLimit("fixture")

    captured = {}
    monkeypatch.setattr(driver.incremental, "compatible_contact_solve", interrupted)
    monkeypatch.setattr(driver.reused, "main", lambda: captured.update(
        response=driver.incremental.compatible_contact_solve(None)))
    monkeypatch.setattr(sys, "argv", ["driver", "--out", "unused.json"])
    driver.main()
    assert captured["response"]["converged"] is False
    assert captured["response"]["wall_time_limit_reached"] is True
    assert "q" not in captured["response"]


@pytest.mark.parametrize("existing", [{"id": "new", "kind": "panel_contact"},
                                       {"id": "old", "kind": "timber_face_contact"}])
def test_existing_face_or_colliding_identity_cannot_add_a_second_path(monkeypatch, existing):
    monkeypatch.setattr(driver.frame, "elastic_connections", lambda *a, **k: ([], [existing], []))
    monkeypatch.setattr(driver.faces, "prepare_linear_timber_faces", lambda *a, **k: {
        "contacts": [{"id": "new", "kind": "timber_face_contact"}]})
    monkeypatch.setattr(driver.reused, "main", lambda: driver.frame.elastic_connections(None))
    monkeypatch.setattr(sys, "argv", ["driver", "--out", "unused.json"])
    with pytest.raises(ValueError, match="already present or contact identities overlap"):
        driver.main()


@pytest.mark.parametrize("existing_output", [False, True])
def test_outer_phase_timeout_keeps_unmeasured_residual_null_and_preserves_outputs(tmp_path, monkeypatch, existing_output):
    output = tmp_path / "field.json"
    if existing_output:
        output.write_text('{"unadmitted":true}')

    def stopped_preparation():
        raise driver.CaseWallTimeLimit("synthetic outside-solver phase")

    monkeypatch.setattr(driver.reused, "main", stopped_preparation)
    monkeypatch.setattr(sys, "argv", ["driver", "--out", str(output)])
    with pytest.raises(SystemExit) as raised:
        driver.main()
    assert raised.value.code == 1
    import json

    report = json.loads(output.with_name(output.name + ".interrupted.json").read_text())
    assert report["response"]["gradient_inf_n"] is None
    assert report["response"]["gradient_observation_available"] is False
    assert report["accepted_field_exported"] is False
    assert report["usable_conditional_actions"] is False
    assert "q" not in report["response"]
    assert not any(report["release"].values())
    assert report["source_sha256"]["scripts/run_thin_bolted_finite_frame.py"] == driver.SAVED_PANEL_HELPER_SHA256
    assert report["source_sha256"]["scripts/run_thin_bolted_common_shaft_incremental.py"] == driver.REUSED_DRIVER_SHA256
    assert all(report["source_sha256"][key] == value for key, value in driver.PANEL_OPERATOR_PINS.items())
    if existing_output:
        assert output.read_text() == '{"unadmitted":true}'
        assert report["existing_output_sha256_not_admitted"] == driver.frame.sha(output)
    else:
        assert not output.exists()
