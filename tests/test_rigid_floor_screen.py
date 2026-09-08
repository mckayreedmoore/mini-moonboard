"""Analytic rigid-floor equilibrium checks; no CAD or finite-element solver."""
from types import SimpleNamespace

import numpy as np
import pytest

from fea import rigid_floor_screen as screen

SQUARE = np.array([[-1000., -1000., 0.], [-1000., 1000., 0.],
                   [1000., -1000., 0.], [1000., 1000., 0.]])


def test_centered_weight_has_upward_compressive_witness():
    result = screen.solve(SQUARE, [0, 0, -1000, 0, 0, 0], 0.)
    forces = np.array(result["point_forces_n"])
    assert result["status"] == "feasible"
    assert forces.sum(axis=0) == pytest.approx([0, 0, 1000])
    assert forces[:, 2].min() >= 0
    assert result["residual_wrench"] == pytest.approx([0]*6, abs=1e-6)
    assert "not predicted" in result["limits"]


@pytest.mark.parametrize("offset,feasible", [(999., True), (1000., True), (1001., False)])
def test_tip_boundary_matches_support_square(offset, feasible):
    # Downward load at x=offset creates positive My.
    result = screen.solve(SQUARE, [0, 0, -1000, 0, 1000*offset, 0], 0.)
    assert result["polygon_feasible"] is feasible


@pytest.mark.parametrize("horizontal,feasible", [(0., True), (499., True), (500., True), (501., False)])
def test_slip_limit_and_force_sign(horizontal, feasible):
    result = screen.solve(SQUARE, [horizontal, 0, -1000, 0, 0, 0], .5)
    assert result["polygon_feasible"] is feasible
    if feasible:
        assert np.array(result["point_forces_n"]).sum(axis=0) == pytest.approx([-horizontal, 0, 1000])


@pytest.mark.parametrize("yaw,feasible", [(400000., True), (-400000., True), (800000., False)])
def test_yaw_requires_distributed_friction(yaw, feasible):
    assert screen.solve(SQUARE, [0, 0, -1000, 0, 0, yaw], .5)["polygon_feasible"] is feasible


def test_upward_external_force_cannot_be_balanced_by_tensile_floor():
    result = screen.solve(SQUARE, [0, 0, 1000, 0, 0, 0], .5)
    assert result["status"] == "infeasible"
    assert result["circular_cone_infeasibility_proven"] is False


def test_translation_preserves_equilibrium_with_transformed_wrench():
    wrench = np.array([100., -50., -1000., 20000., 50000., 30000.])
    shift = np.array([430., -270., 0.])
    shifted = wrench.copy()
    shifted[3:] += np.cross(shift, wrench[:3])
    for points, loads in ((SQUARE, wrench), (SQUARE+shift, shifted)):
        result = screen.solve(points, loads, .5)
        assert result["status"] == "feasible"
        assert result["residual_wrench"] == pytest.approx([0]*6, abs=1e-6)


def test_inscribed_polygon_rejection_is_not_circular_cone_failure():
    angle = np.pi/16
    magnitude = 1000*.5*(1+np.cos(angle))/2
    result = screen.solve(SQUARE, [magnitude*np.cos(angle), magnitude*np.sin(angle), -1000, 0, 0, 0], .5)
    assert magnitude < 500  # Within the circular friction cone, outside polygon.
    assert result["status"] == "infeasible"
    assert not result["circular_cone_infeasibility_proven"]


@pytest.mark.parametrize("points,wrench,mu", [
    ([], [0]*6, .5), ([[0, 0]], [0]*6, .5),
    ([[0, 0, 1]], [0]*6, .5), ([[0, 0, np.nan]], [0]*6, .5),
    ([[np.inf, 0, 0]], [0]*6, .5), (SQUARE, [0]*5, .5),
    (SQUARE, [0, 0, -1, 0, np.inf, 0], .5),
    (SQUARE, [0]*6, -.1), (SQUARE, [0]*6, np.nan),
    (SQUARE, [0]*6, [.5]),
])
def test_invalid_input_rejected(points, wrench, mu):
    with pytest.raises(ValueError):
        screen.solve(points, wrench, mu)


def test_solver_errors_and_bad_witness_fail_closed(monkeypatch):
    monkeypatch.setattr(screen, "linprog", lambda *a, **k: SimpleNamespace(
        status=4, success=False, message="numerical failure"))
    with pytest.raises(RuntimeError, match="solver failed"):
        screen.solve(SQUARE, [0, 0, -1000, 0, 0, 0], .5)
    monkeypatch.setattr(screen, "linprog", lambda *a, **k: SimpleNamespace(
        status=0, success=True, x=np.zeros(64)))
    with pytest.raises(ValueError, match="independent"):
        screen.solve(SQUARE, [0, 0, -1000, 0, 0, 0], .5)
