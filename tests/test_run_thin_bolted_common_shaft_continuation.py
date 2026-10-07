"""Numerical retry provenance must precede the physical state binding."""

import sys

import pytest

from scripts import run_thin_bolted_common_shaft_continuation as driver


def test_retry_routes_the_budget_and_binds_parameters_before_inner_export(monkeypatch):
    captured = {}
    original_solver = driver.frame.compatible_contact_solve
    argv = ["driver", "--newton-limit", "303", "--cases", "a12-rear", "--out", "unused.json"]

    def numerical_solve(*args, max_iterations):
        captured["limit"] = max_iterations
        return {"converged": False, "gradient_inf_n": 21.8}

    def evaluate():
        return {"parameters": {}, "source_sha256": {},
                "response": driver.frame.compatible_contact_solve(None, None, [], [], [])}

    def inner_export():
        captured["report"] = driver.frame.evaluate_elastic()
        captured["inner_argv"] = list(sys.argv)

    monkeypatch.setattr(driver.numerical, "compatible_contact_solve", numerical_solve)
    monkeypatch.setattr(driver.frame, "evaluate_elastic", evaluate)
    monkeypatch.setattr(driver.common, "main", inner_export)
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    report = captured["report"]
    assert captured["limit"] == 303
    assert report["parameters"]["numerical_newton_iteration_limit_per_floor_pattern"] == 303
    assert report["parameters"]["numerical_continuation_method"] == driver.STRATEGY
    assert report["numerical_continuation_execution"]["physical_force_tolerance_changed"] is False
    assert report["source_sha256"]["scripts/thin_bolted_numerical_step.py"] == driver.NUMERICAL_SHA
    assert "--newton-limit" not in captured["inner_argv"]
    assert sys.argv == argv
    assert driver.frame.compatible_contact_solve is original_solver


def test_retry_rejects_a_changed_frozen_common_driver(monkeypatch):
    sha = driver.frame.sha
    monkeypatch.setattr(driver.frame, "sha", lambda path: "changed" if str(path) == driver.common.__file__ else sha(path))
    monkeypatch.setattr(sys, "argv", ["driver", "--out", "unused.json"])
    with pytest.raises(ValueError, match="preserve the frozen"):
        driver.main()
