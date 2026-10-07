"""Reuse a failed guess without weakening the frozen physical export protocol."""

import json
import sys

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import run_thin_bolted_common_shaft_incremental as driver


def test_warm_source_is_authenticated_and_remains_explicitly_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    source = tmp_path / "source.json"
    source.write_text("{}")
    payload = {"schema": "thin_bolted_common_shaft_frame/v1",
               "geometry_cache_sha256": driver.frame.GEOMETRY_CACHE_SHA,
               "state_id": "failed-state", "case_id": "a12-rear", "accessory_placement": "original",
               "parameters": {"panel_intervals": 8, "beam_size_mm": 150., "shaft_max_segment_mm": 25.},
               "source_sha256": {source.name: driver.frame.sha(source)}, "counts": {"dofs": 2},
               "usable_conditional_actions": False, "failed_response_without_recovered_actions": True,
               "response": {"converged": False, "diagnostic_last_q": [1., 2.], "gradient_inf_n": .001}}
    path = tmp_path / "failed.json"
    path.write_text(json.dumps(payload))
    q, metadata = driver.read_warm(path, driver.frame.sha(path))
    np.testing.assert_array_equal(q, [1., 2.])
    assert metadata["initialization_only"] is True
    assert metadata["accepted_forces_or_resistance_transferred"] is False
    assert metadata["source_state_id"] == "failed-state"
    assert "state_id" not in metadata
    with pytest.raises(ValueError, match="source differs"):
        driver.read_warm(path, "changed")
    source.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="dependency differs"):
        driver.read_warm(path, driver.frame.sha(path))


def test_method_facade_reuses_and_restores_the_frozen_retry_protocol(monkeypatch):
    captured = {}
    old_module, old_strategy = driver.previous.numerical, driver.previous.STRATEGY
    argv = ["driver", "--newton-limit", "12", "--cases", "a12-rear", "--out", "unused.json"]
    # This protocol fixture uses an already issued source-bound receipt; no
    # candidate solve or method certificate is issued by this test.
    monkeypatch.setattr(driver, "CERTIFICATE", driver.previous.CERTIFICATE)
    monkeypatch.setattr(driver, "CERTIFICATE_SHA", driver.previous.CERTIFICATE_SHA)

    def incremental_solve(*args, **kwargs):
        captured["solve"] = kwargs
        return {"converged": False}

    def inner():
        captured["strategy"] = driver.previous.STRATEGY
        captured["report"] = driver.frame.evaluate_elastic()
        driver.previous.numerical.compatible_contact_solve(None, None, [], [], [], max_iterations=12)

    monkeypatch.setattr(driver.incremental, "compatible_contact_solve", incremental_solve)
    monkeypatch.setattr(driver.frame, "evaluate_elastic", lambda: {"source_sha256": {}})
    monkeypatch.setattr(driver.previous, "main", inner)
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    assert captured["strategy"] == driver.STRATEGY
    assert captured["solve"]["max_iterations"] == 12
    assert captured["solve"]["warm_q"] is None
    execution = captured["report"]["incremental_continuation_execution"]
    assert execution["published_energy_forces_and_tolerance_are_original"] is True
    assert execution["warm_initialization"] is None
    assert "scripts/thin_bolted_incremental_step.py" in captured["report"]["source_sha256"]
    assert driver.previous.numerical is old_module
    assert driver.previous.STRATEGY == old_strategy
    assert sys.argv == argv


def test_same_vector_length_does_not_allow_a_changed_reference_discretization(monkeypatch):
    metadata = {"reference_discretization": {"panel_intervals": 8, "beam_size_mm": 150., "shaft_max_segment_mm": 25.}}
    monkeypatch.setattr(driver, "read_warm", lambda *args: (np.zeros(2), metadata))
    monkeypatch.setattr(sys, "argv", ["driver", "--warm-start", "ignored.json", "--warm-start-sha256", "declared",
                                      "--intervals", "12", "--out", "unused.json"])
    with pytest.raises(ValueError, match="unchanged reference"):
        driver.main()


def test_warm_provenance_survives_final_recursive_state_binding():
    from scripts.run_thin_bolted_finished_floor import bind_finished_state

    report = {"state_id": "new", "case_id": "a12-rear", "accessory_placement": "original",
              "parameters": {}, "geometry_cache_sha256": "geometry", "source_sha256": {}, "limits": [],
              "warm_initialization": {"source_state_id": "old", "initialization_only": True}}
    bound = bind_finished_state(report, [], {}, "driver")
    assert bound["state_id"] != "new"
    assert bound["warm_initialization"]["source_state_id"] == "old"


def test_passive_floor_pattern_recovers_original_enabled_rows_without_mutation():
    material = csr_matrix(np.diag([10., 20., 30.]))
    tangents = [{"first": "left", "B": csr_matrix([[1., 0., 0.]]), "stiffness": 1000.},
                {"first": "right", "B": csr_matrix([[0., 1., 0.]]), "stiffness": 2000.}]
    linear = material + 1000. * tangents[0]["B"].T @ tangents[0]["B"]
    before = linear.copy()
    assert driver.enabled_floor_hosts(linear, material, tangents) == ["left"]
    np.testing.assert_array_equal(linear.toarray(), before.toarray())
