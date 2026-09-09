"""Synthetic free bodies test the auditor, not a physical board."""
import copy

import pytest

from fea import spread_floor_audit as audit


def fixture():
    nodes = {1: [0., 0., 0.], 2: [1., 0., 0.]}
    record = {"mapped_input": {"nodes": nodes},
        "connector_context": {"nodes": nodes, "connections": {}},
        "ground_nodes": {"A": {11: [0., 0., -100.], 12: [1., 0., -100.], 13: [0., 0., 0.]}},
        "bottom_nodes": {"A": [11, 12]}, "density_tonne_mm3": 6e-10,
        "load": {"node": 2, "force_n": [0., 0., -10.]}}
    weights = {1: 1e6, 2: 1e6}
    gravity = 1e6*6e-10*9806.65
    parsed = {}
    for time in (1., 2.):
        parsed["displacements", "WOODN", time] = {n: [0., 0., 0.] for n in nodes}
        parsed["displacements", "GROUND_A", time] = {n: [0., 0., 0.] for n in (11, 12, 13)}
        parsed["forces", "GROUND_A", time] = {11: [0., 0., gravity],
            12: [0., 0., gravity+(10 if time == 2 else 0)], 13: [99999., 99999., 99999.]}
    return record, weights, parsed


def test_balanced_endpoints_ignore_free_master_reaction(monkeypatch):
    record, weights, parsed = fixture()
    monkeypatch.setattr(audit, "blocks", lambda _: parsed)
    result = audit.assess("", record, weights)
    assert result["global_checks_passed"]
    assert not result["local_contact_audited"] and not result["qualified_for_design"]


@pytest.mark.parametrize("change", ["force", "deformed_moment"])
def test_changed_external_force_or_deformed_moment_rejected(monkeypatch, change):
    record, weights, parsed = fixture()
    if change == "force":
        parsed["forces", "GROUND_A", 2.][12][2] += 1
    else:
        parsed["displacements", "WOODN", 2.][2][0] = 1.
    monkeypatch.setattr(audit, "blocks", lambda _: parsed)
    result = audit.assess("", record, weights)
    assert result["endpoints"][0]["global_checks_passed"]
    assert not result["endpoints"][1]["global_checks_passed"]
    assert not result["global_checks_passed"]


def test_missing_endpoint_or_weights_rejected(monkeypatch):
    record, weights, parsed = fixture()
    monkeypatch.setattr(audit, "blocks", lambda _: parsed)
    with pytest.raises(ValueError, match="gravity weights"):
        audit.assess("", record, {1: 1e6})
    missing = copy.deepcopy(parsed)
    del missing["displacements", "WOODN", 2.]
    monkeypatch.setattr(audit, "blocks", lambda _: missing)
    with pytest.raises(ValueError, match="endpoint"):
        audit.assess("", record, weights)


def test_mpc_error_fails_even_when_external_equilibrium_passes(monkeypatch):
    record, weights, parsed = fixture()
    record["connector_context"]["nodes"] = {
        **record["mapped_input"]["nodes"], 3: [.75, 0., 0.], 4: [.75, 0., 0.]}
    record["connector_context"]["connections"] = {"joint": {
        "parent_point": 3, "gusset_point": 4, "nodes": [1, 2],
        "gusset_nodes": [1, 2], "weights": [.25, .75], "other_weights": [.25, .75]}}
    for time in (1., 2.):
        parsed["displacements", "WOODN", time].update({3: [0., 0., 0.], 4: [0., 0., 0.]})
    monkeypatch.setattr(audit, "blocks", lambda _: parsed)
    assert audit.assess("", record, weights)["global_checks_passed"]
    parsed["displacements", "WOODN", 2.][4][0] = .01
    result = audit.assess("", record, weights)
    endpoint = result["endpoints"][1]
    assert max(map(abs, endpoint["force_residual_n"])) < 1e-10
    assert max(map(abs, endpoint["moment_residual_nmm"])) < 1e-10
    assert endpoint["maximum_interpolation_error_mm"] == pytest.approx(.01)
    assert not result["global_checks_passed"]
