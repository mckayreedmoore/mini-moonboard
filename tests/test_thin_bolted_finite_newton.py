"""Small finite conservative systems, support feedback and circular quotient."""

import importlib.util
from functools import lru_cache
from itertools import pairwise
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_finite_newton as method


@lru_cache(maxsize=1)
def shaft_fixtures():
    path = method.frame.ROOT / "tests/test_thin_bolted_isotropic_shaft.py"
    spec = importlib.util.spec_from_file_location("retained_isotropic_shaft_fixtures", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def quadratic(matrix, force, constant=0.):
    matrix, force = np.asarray(matrix, dtype=float), np.asarray(force, dtype=float)

    def response(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        fields = {"energy_nmm": float(constant+.5*q @ matrix @ q-force @ q),
                  "gradient_n": matrix @ q-force, "hessian_csr": csr_matrix(matrix) if tangent else None}
        if recover_actions:
            fields["test_force_exports"] = force.copy()
        return fields

    return response


def corner_fixture():
    recovered = []

    def response(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        target, vertical_load = np.array([1., 2.]), np.array([-1., 10.])
        active_xy = np.array([name not in disabled_floor_support_ids for name in ["same-body/corner-A", "same-body/corner-B"]])
        closing = np.maximum(q[2:], 0.)
        energy = .5*np.sum((q[:2]-target)**2) + .5*np.sum(active_xy*q[:2]**2)
        energy += .5*np.sum(q[2:]**2) + 5.*np.sum(closing**2) - vertical_load @ q[2:]
        gradient = np.r_[q[:2]-target + active_xy*q[:2], q[2:]+10*closing-vertical_load]
        fields = {"energy_nmm": float(energy), "gradient_n": gradient,
                  "hessian_csr": csr_matrix(np.diag(np.r_[1.+active_xy, 1.+10*(q[2:]>0.)])) if tangent else None,
                  "floor_normal_reactions_n": {"normal-A": float(10*closing[0]), "normal-B": float(10*closing[1])},
                  "floor_xy_enabled_support_ids": [name for name, active in zip(["same-body/corner-A", "same-body/corner-B"], active_xy, strict=True) if active]}
        if recover_actions:
            recovered.append(q.copy()); fields["test_force_exports"] = gradient.copy()
        return fields

    feedback = method.CornerSupportFeedback({"same-body/corner-A": "normal-A", "same-body/corner-B": "normal-B"})
    return response, feedback, recovered


def axial_shaft_fixture(force=2.):
    adapter = shaft_fixtures().small_adapter()
    row = adapter.mechanics.shafts["shaft/test"]
    applied = np.zeros(adapter.ndof)
    applied[row["index"][0, 0]], applied[row["index"][-1, 0]] = -force, force

    def response(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        result = adapter.response(q, tangent)
        result["energy_nmm"] -= applied @ q
        result["gradient_n"] -= applied
        if recover_actions:
            result["test_force_exports"] = applied.copy()
        return result

    return adapter, row, response


def test_convex_known_answer_and_original_forces_are_unmodified():
    matrix, force = np.array([[100., 20.], [20., 50.]]), np.array([3., -4.])
    oracle = quadratic(matrix, force)
    result = method.solve_finite_potential(oracle, np.zeros(2))
    assert result["converged"]
    assert result["q"] == pytest.approx(np.linalg.solve(matrix, force), abs=1e-5*np.linalg.norm(np.linalg.inv(matrix), ord=np.inf))
    assert result["gradient_inf_n"] < 1e-5
    assert result["generalized_residual_tolerance_n"] == 1e-5
    assert result["physical_fields"]["test_force_exports"] == pytest.approx(force)
    assert result["potential_energy_nmm"] == oracle(result["q"])["energy_nmm"]
    assert result["maximum_transient_scaled_step_regularization"] > 0.
    assert result["physical_twist_supports_added"] == 0
    assert result["gradient_work_evaluations"] == 0


def test_inactive_unloaded_null_mode_needs_no_support():
    oracle = quadratic(np.diag([100., 0.]), [2., 0.])
    result = method.solve_finite_potential(oracle, np.array([0., 7.]))
    assert result["converged"]
    assert result["q"] == pytest.approx([.02, 7.], abs=1e-5/100)
    assert result["physical_fields"]["hessian_csr"] is None
    assert np.linalg.matrix_rank(oracle(result["q"])["hessian_csr"].toarray()) == 1


def test_nonconvex_double_well_uses_step_damping_and_reaches_known_minimum():
    def oracle(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        x = q[0]
        return {"energy_nmm": float((x*x-1)**2), "gradient_n": np.array([4*x*(x*x-1)]),
                "hessian_csr": csr_matrix([[12*x*x-4]]) if tangent else None}

    result = method.solve_finite_potential(oracle, np.array([.1]))
    assert result["converged"]
    assert result["q"][0] == pytest.approx(1., abs=1e-6)
    assert result["maximum_transient_scaled_step_regularization"] >= 1.
    energies = [row["physical_potential_energy_nmm"] for row in result["iteration_history"]]
    assert all(b <= a+1e-14 for a, b in pairwise(energies))


def test_huge_potential_offset_uses_gradient_work_without_changing_published_energy():
    oracle = quadratic([[2.]], [2.], constant=1e20)
    result = method.solve_finite_potential(oracle, np.array([1.000001]))
    assert result["converged"]
    # Start farther away because the immutable force tolerance already accepts
    # the first small perturbation; integration is demonstrated independently.
    result = method.solve_finite_potential(oracle, np.array([1.001]))
    assert result["converged"]
    assert result["q"][0] == pytest.approx(1., abs=1e-8)
    assert result["potential_energy_nmm"] == 1e20
    assert result["gradient_work_evaluations"] > 0
    comparison = next(row["potential_difference"] for row in result["iteration_history"] if "potential_difference" in row)
    assert comparison["difference_nmm"] == pytest.approx(-1e-6, rel=2e-6)
    assert comparison["resolved"]
    assert comparison["estimated_absolute_error_nmm"] < 1e-14


@pytest.mark.parametrize("value,delta", [(-.3, .8), (.4, -.8), (.4, .1)])
def test_gradient_work_integral_resolves_unilateral_transition(value, delta):
    def oracle(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        return {"energy_nmm": 1e20 + 3*max(q[0], 0.)**2,
                "gradient_n": np.array([6*max(q[0], 0.)]), "hessian_csr": csr_matrix([[6. if q[0]>0 else 0.]])}

    q, change = np.array([value]), np.array([delta])
    result = method.potential_difference(oracle, q, change, frozenset(), oracle(q), oracle(q+change),
                                         float(oracle(q)["gradient_n"] @ change), method.NewtonOptions())
    expected = 3*(max(value+delta, 0.)**2-max(value, 0.)**2)
    assert result["resolved"]
    assert result["difference_nmm"] == pytest.approx(expected, abs=2e-11)


def test_unresolved_gradient_work_rejects_step_and_exports_no_actions(monkeypatch):
    oracle = quadratic([[2.]], [2.], constant=1e20)
    monkeypatch.setattr(method, "quad", lambda *args, **kwargs: (-1e-6, 1e-3, {}, "subinterval limit"))
    options = method.NewtonOptions(max_backtracks=2, max_regularization_trials=2)
    result = method.solve_finite_potential(oracle, np.array([1.001]), options=options)
    assert not result["converged"]
    assert "line search unresolved" in result["termination"]
    assert "q" not in result and "physical_fields" not in result and "test_force_exports" not in result


def test_own_corner_support_transition_does_not_disable_supported_same_body_corner():
    oracle, feedback, recovered = corner_fixture()
    result = method.solve_finite_potential(oracle, np.zeros(4), support_feedback=feedback)
    assert result["converged"]
    assert result["q"] == pytest.approx([1., 1., -1., 10/11], abs=1e-5)
    assert result["disabled_floor_support_ids"] == ["same-body/corner-A"]
    assert result["physical_fields"]["floor_xy_enabled_support_ids"] == ["same-body/corner-B"]
    assert len(result["support_history"]) == 2 and len(recovered) == 1
    assert all(row["gradient_inf_n"] < 1e-5 for row in result["support_history"])


def test_fixed_corner_pattern_cycle_fails_without_force_recovery():
    oracle, _, recovered = corner_fixture()
    feedback = lambda q, fields, disabled: () if disabled else ("same-body/corner-A",)
    result = method.solve_finite_potential(oracle, np.zeros(4), support_feedback=feedback)
    assert not result["converged"]
    assert "repeated fixed corner" in result["termination"]
    assert not recovered and "physical_fields" not in result and "q" not in result


def test_source_bound_corner_factory_and_missing_reaction_fail_explicitly():
    potential = SimpleNamespace(interactions=[{"kind": "floor_tangent_xy", "floor_support_id": "A", "normal_contact_id": "NA"},
                                             {"kind": "floor_tangent_xy", "floor_support_id": "B", "normal_contact_id": "NB"}])
    feedback = method.CornerSupportFeedback.from_finite_frame(potential)
    assert feedback(None, {"floor_normal_reactions_n": {"NA": 0., "NB": 2.}}, ()) == {"A"}
    oracle = quadratic([[1.]], [0.])
    result = method.solve_finite_potential(oracle, np.zeros(1), support_feedback=feedback)
    assert not result["converged"] and "physical evaluation failed" in result["termination"]
    assert "physical_fields" not in result


def test_iteration_stop_records_actual_last_iterate_without_force_exports():
    oracle = quadratic([[10.]], [4000.])
    result = method.solve_finite_potential(oracle, np.zeros(1), options=method.NewtonOptions(max_iterations=1))
    assert not result["converged"]
    assert result["gradient_inf_n"] == pytest.approx(max(abs(oracle(result["diagnostic_last_q"])["gradient_n"])))
    assert "q" not in result and "physical_fields" not in result
    assert not result["diagnostic_last_q_is_a_converged_or_accepted_force_field"]


def test_action_recovery_cannot_change_physical_gradient_even_inside_tolerance():
    original = quadratic([[1.]], [0.])

    def inconsistent(q, tangent=True, recover_actions=False, **kwargs):
        fields = original(q, tangent, recover_actions, **kwargs)
        if recover_actions:
            fields["gradient_n"] += 2e-6
        return fields

    result = method.solve_finite_potential(inconsistent, np.zeros(1))
    assert not result["converged"] and "changed the original physical gradient" in result["termination"]
    assert "q" not in result and "physical_fields" not in result


def test_progress_callback_exposes_iteration_trials_and_success_recovery():
    events = []
    result = method.solve_finite_potential(quadratic([[2.]], [3.]), np.zeros(1), progress=events.append)
    assert result["converged"]
    assert {"newton-evaluation", "newton-iteration", "trial-evaluation", "converged-action-recovery"} <= {r["event"] for r in events}


def test_circular_quotient_axial_known_answer_preserves_full_residual_and_twist_freedom():
    adapter, row, oracle = axial_shaft_fixture()
    chart = method.CircularShaftQuotient(adapter)
    initial = adapter.common_roll(np.zeros(adapter.ndof), .35)
    result = method.solve_finite_potential(oracle, initial, quotient=chart)
    assert result["converged"]
    indices = row["index"]
    area = np.pi*8**2/4
    expected = 2.*(row["stations"][-1]-row["stations"][0])/(200000.*area)
    assert result["q"][indices[-1, 0]]-result["q"][indices[0, 0]] == pytest.approx(expected, rel=2e-6)
    assert max(abs(oracle(result["q"])["gradient_n"])) < 1e-5
    assert result["q"][row["appended_first_twist_dof"]] == 0.
    assert result["physical_twist_supports_added"] == 0
    assert max(abs(v) for r in result["iteration_history"] for v in r["material_roll_work_nmm_per_rad"].values()) < 1e-6


def test_minimal_chart_principal_hessian_and_compensated_rigid_work_at_bent_pose():
    adapter = shaft_fixtures().small_adapter(); row = adapter.mechanics.shafts["shaft/test"]
    chart = method.CircularShaftQuotient(adapter)
    q = np.zeros(adapter.ndof); q[row["index"]] = shaft_fixtures().bent_two_element()[1]
    q, _ = chart.canonicalize(q)
    response = adapter.response(q)
    direction = np.random.default_rng(71).normal(size=len(chart.indices))
    full_direction = chart.lift(direction); step = 1e-4
    finite_difference = (adapter.response(q+step*full_direction, False)["gradient_n"] - adapter.response(q-step*full_direction, False)["gradient_n"])/(2*step)
    assert response["hessian_csr"][chart.indices][:, chart.indices] @ direction == pytest.approx(finite_difference[chart.indices], rel=1e-7, abs=1e-4)
    reference, forces = np.array([3., -2., 4.]), [np.array([1., 2., -3.]), np.array([-4., 2., 1.])]
    dual, wrench = np.zeros(adapter.ndof), np.zeros(6)
    for station, force in zip(row["stations"][[0, -1]], forces, strict=True):
        point = row["point"]+station*row["storage_basis"][:, 0]
        port = adapter.port("shaft/test", point, q, tangent=False)
        dual += np.asarray(port["J_csr"].T @ force).ravel()
        wrench += np.r_[force, np.cross(port["position_xyz_mm"]-reference, force)]
    generators = chart.world_rigid_generators(q, reference)["shaft/test"]
    assert generators["quotient_world_rigid_G_csr"].T @ dual == pytest.approx(wrench, abs=2e-9)
    assert np.max(abs(generators["quotient_world_rigid_G_csr"].toarray()[chart.omitted_indices]), initial=0.) < 1e-12


def test_real_off_axis_load_breaking_roll_gauge_fails_without_physical_support():
    adapter, row, _ = axial_shaft_fixture()
    point = row["point"]+row["stations"][0]*row["storage_basis"][:, 0]+5*row["storage_basis"][:, 1]
    force = row["storage_basis"][:, 2]

    def oracle(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        result = adapter.response(q, tangent)
        port = adapter.port("shaft/test", point, q, tangent=tangent)
        result["energy_nmm"] -= force @ (port["position_xyz_mm"]-point)
        result["gradient_n"] -= np.asarray(port["J_csr"].T @ force).ravel()
        return result

    result = method.solve_finite_potential(oracle, np.zeros(adapter.ndof), quotient=method.CircularShaftQuotient(adapter))
    assert not result["converged"] and "breaks the circular" in result["termination"]
    assert "q" not in result and "physical_fields" not in result and result["physical_twist_supports_added"] == 0


def test_unsupported_initial_minimal_chart_has_explicit_failure_and_no_force_export():
    adapter, row, oracle = axial_shaft_fixture()
    initial = np.zeros(adapter.ndof)
    initial[row["index"][0, 4]] = 1000*np.pi
    result = method.solve_finite_potential(oracle, initial, quotient=method.CircularShaftQuotient(adapter))
    assert not result["converged"] and "initial finite chart unsupported" in result["termination"]
    assert "q" not in result and "physical_fields" not in result


def test_invalid_trial_is_backtracked_but_invalid_initial_state_exports_no_forces():
    original = quadratic([[1.]], [1.])

    def bounded(q, **kwargs):
        if q[0] > .75:
            raise ValueError("unsupported local chart")
        return original(q, **kwargs)

    result = method.solve_finite_potential(bounded, np.zeros(1), options=method.NewtonOptions(max_iterations=2))
    assert not result["converged"] and result["accepted_numerical_steps"] > 0
    assert result["diagnostic_last_q"][0] <= .75
    failed = method.solve_finite_potential(bounded, np.ones(1))
    assert not failed["converged"] and "unsupported local chart" in failed["termination"]
    assert "physical_fields" not in failed
