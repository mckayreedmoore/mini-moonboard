"""Preparation and failed-result guards; no full frame assembly or solve."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_thin_bolted_finite_frame as driver


def test_saved_panels_reuse_source_operators_and_never_select_old_displacements():
    panels, pins, proof = driver.reuse_panel_operators()
    assert sum(len(panel["screws"]) for panel in panels.values()) == 66
    assert sum(len(panel["contact_area"]) for panel in panels.values()) == 530
    assert proof["contact_maximum_edge_mm"] == 70.
    assert not proof["historical_displacements_forces_or_acceptance_used"]
    assert not proof["panel_reference_K_reassembled"]
    with np.load(driver.OPERATORS, allow_pickle=False) as arrays:
        for name, panel in panels.items():
            assert "q" not in panel
            assert np.array_equal(panel["K"], arrays[name + "/K"])
            assert np.array_equal(panel["screw_w"], arrays[name + "/screw_w"])
            assert len(panel["contact_owner"]) == len(panel["contact_area"])
            assert np.isclose(panel["mass_weights"].sum(), 1.)
    assert pins[str(driver.OPERATORS.relative_to(driver.ROOT))] == driver.OPERATORS_SHA


def test_finite_initialization_rejects_changed_mapping_even_with_equal_length():
    provenance = {"reference_discretization": {"panel_intervals": 8, "beam_size_mm": 150., "shaft_max_segment_mm": 25.}}
    args = SimpleNamespace(beam_size=150., shaft_segment=25.)
    initial, record = driver.initial_vector(np.arange(10.), provenance, 80, 10, args)
    assert np.array_equal(initial[:10], np.arange(10.))
    assert np.count_nonzero(initial[10:]) == 0
    assert record["new_physical_contact_and_kinematic_laws_resolved_again"]
    with pytest.raises(ValueError, match="coordinate blocks"):
        driver.initial_vector(np.arange(10.), provenance, 80, 10, SimpleNamespace(beam_size=100., shaft_segment=25.))


def test_identity_binds_new_physics_and_discretization():
    case = {"case_id": "a12-rear", "accessory_placement": "retained-original-top-hold"}
    original = driver.state_identity(case, {"contact_edge": 70., "shaft_method": "finite-isotropic"})
    changed = driver.state_identity(case, {"contact_edge": 35., "shaft_method": "finite-isotropic"})
    assert original.startswith("thin-finite-v4-") and changed != original


def test_failed_export_keeps_diagnostic_vector_and_no_recovered_actions(monkeypatch):
    monkeypatch.setattr(driver, "verify_pins", lambda pins: None)
    assembly = SimpleNamespace(layout={"candidate": "candidate", "revision": "v4"}, geo={"bodies": [{"id": "one"}]})
    potential = SimpleNamespace(mechanics=SimpleNamespace(assembly=assembly))
    case = {"state_id": "new-state", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold", "loads": []}
    failed = {"converged": False, "diagnostic_last_q": np.zeros(2), "termination": "iteration limit"}
    report = driver.export_state(case, {}, {}, [], {}, failed, potential, {}, [])
    assert report["failed_response_without_recovered_actions"]
    assert not report["usable_conditional_actions"]
    assert "q" not in report["response"]
    assert "finite_interaction_actions" not in report
    with pytest.raises(ValueError, match="accepted coefficients"):
        driver.export_state(case, {}, {}, [], {}, {**failed, "q": np.zeros(2)}, potential, {}, [])
