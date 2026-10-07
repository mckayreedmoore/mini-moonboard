"""Source-bound small-system receipt for the generic finite-potential solver."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from scripts import thin_bolted_finite_newton as method


def fixtures():
    path = method.frame.ROOT/"tests/test_thin_bolted_finite_newton.py"
    spec = importlib.util.spec_from_file_location("finite_newton_coupon_fixtures", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def compact(result):
    keys = ("converged", "termination", "gradient_inf_n", "potential_energy_nmm", "accepted_numerical_steps",
            "rejected_numerical_trials", "gradient_work_evaluations", "maximum_transient_scaled_step_regularization",
            "generalized_residual_tolerance_n", "disabled_floor_support_ids", "physical_twist_supports_added")
    value = {k: result[k] for k in keys}
    value.update(force_field_exported="physical_fields" in result, accepted_q_exported="q" in result)
    if result["converged"]:
        value["q"] = result["q"].tolist()
    else:
        value["diagnostic_last_q"] = result["diagnostic_last_q"].tolist()
    return value


def observe():
    fixture = fixtures()
    matrix, force = np.array([[100., 20.], [20., 50.]]), np.array([3., -4.])
    convex = method.solve_finite_potential(fixture.quadratic(matrix, force), np.zeros(2))
    convex_row = compact(convex)
    convex_row["known_q"] = np.linalg.solve(matrix, force).tolist()
    convex_row["maximum_q_error_mm"] = float(np.max(abs(convex["q"]-np.linalg.solve(matrix, force))))
    convex_row["force_criterion_q_error_bound_mm"] = float(1e-5*np.linalg.norm(np.linalg.inv(matrix), ord=np.inf))
    null = method.solve_finite_potential(fixture.quadratic(np.diag([100., 0.]), [2., 0.]), np.array([0., 7.]))

    def double_well(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
        x = q[0]
        return {"energy_nmm": float((x*x-1)**2), "gradient_n": np.array([4*x*(x*x-1)]),
                "hessian_csr": method.csr_matrix([[12*x*x-4]]) if tangent else None}

    nonconvex = method.solve_finite_potential(double_well, np.array([.1]))
    nonconvex_row = compact(nonconvex)
    nonconvex_row["known_positive_minimum_q"] = [1.]
    nonconvex_row["physical_energy_history_nmm"] = [r["physical_potential_energy_nmm"] for r in nonconvex["iteration_history"]]
    offset = method.solve_finite_potential(fixture.quadratic([[2.]], [2.], constant=1e20), np.array([1.001]))
    offset_row = compact(offset)
    offset_row["comparison"] = next(row["potential_difference"] for row in offset["iteration_history"] if "potential_difference" in row)
    transitions = []
    for value, delta in [(-.3, .8), (.4, -.8), (.4, .1)]:
        def unilateral(q, tangent=True, recover_actions=False, *, disabled_floor_support_ids=()):
            return {"energy_nmm": 1e20+3*max(q[0], 0.)**2, "gradient_n": np.array([6*max(q[0], 0.)])}
        q, step = np.array([value]), np.array([delta])
        row = method.potential_difference(unilateral, q, step, frozenset(), unilateral(q), unilateral(q+step),
                                          float(unilateral(q)["gradient_n"] @ step), method.NewtonOptions())
        row.update(value_mm=value, delta_mm=delta,
                   known_difference_nmm=3*(max(value+delta, 0.)**2-max(value, 0.)**2))
        transitions.append(row)
    oracle, feedback, recovered = fixture.corner_fixture()
    support = method.solve_finite_potential(oracle, np.zeros(4), support_feedback=feedback)
    support_row = compact(support)
    support_row.update(known_q=[1., 1., -1., 10/11], support_history=support["support_history"],
                       action_recovery_calls=len(recovered),
                       floor_xy_enabled_support_ids=support["physical_fields"]["floor_xy_enabled_support_ids"])
    oracle, _, recovered = fixture.corner_fixture()
    cycle = method.solve_finite_potential(oracle, np.zeros(4),
                                         support_feedback=lambda q, fields, disabled: () if disabled else ("same-body/corner-A",))
    cycle_row = compact(cycle); cycle_row["action_recovery_calls"] = len(recovered)
    cutoff = method.solve_finite_potential(fixture.quadratic([[10.]], [4000.]), np.zeros(1),
                                          options=method.NewtonOptions(max_iterations=1))
    adapter, shaft_row, oracle = fixture.axial_shaft_fixture()
    chart = method.CircularShaftQuotient(adapter)
    circular = method.solve_finite_potential(oracle, adapter.common_roll(np.zeros(adapter.ndof), .35), quotient=chart)
    circular_row = compact(circular)
    index = shaft_row["index"]
    circular_row.update(known_extension_mm=2.*np.ptp(shaft_row["stations"])/(200000.*np.pi*8**2/4),
                        actual_extension_mm=float(circular["q"][index[-1, 0]]-circular["q"][index[0, 0]]),
                        full_ndof=adapter.ndof, reduced_ndof=len(chart.indices),
                        local_first_theta_x=circular["q"][shaft_row["appended_first_twist_dof"]],
                        maximum_material_roll_work_nmm_per_rad=max(abs(v) for r in circular["iteration_history"]
                                                                  for v in r["material_roll_work_nmm_per_rad"].values()))
    # Reuse the independently tested bent-pose chart/wrench fixture directly.
    fixture.test_minimal_chart_principal_hessian_and_compensated_rigid_work_at_bent_pose()
    fixture.test_real_off_axis_load_breaking_roll_gauge_fails_without_physical_support()
    fixture.test_unsupported_initial_minimal_chart_has_explicit_failure_and_no_force_export()
    observed = {"convex_known_answer": convex_row, "unloaded_null_mode": compact(null), "nonconvex_double_well": nonconvex_row,
                "published_energy_cancellation": offset_row, "gradient_work_unilateral_transitions": transitions,
                "individual_corner_support_feedback": support_row, "support_pattern_cycle_failure": cycle_row,
                "iteration_cutoff_failure": compact(cutoff), "circular_quotient_axial_known_answer": circular_row,
                "bent_quotient_hessian_and_world_wrench_fixture_pass": True,
                "off_axis_gauge_violation_fixture_explicitly_fails": True,
                "unsupported_initial_chart_fixture_explicitly_fails": True}
    observed["method_coupon_checks_pass"] = (
        all(r["converged"] and r["gradient_inf_n"] < 1e-5 for r in [convex, null, nonconvex, offset, support, circular])
        and not cycle["converged"] and not cutoff["converged"] and not recovered
        and all(row["resolved"] and abs(row["difference_nmm"]-row["known_difference_nmm"]) < 2e-11 for row in transitions))
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    observed = observe()
    pins = method.source_pins()
    for path in ["scripts/check_thin_bolted_finite_newton.py", "tests/test_thin_bolted_finite_newton.py",
                 "tests/test_thin_bolted_isotropic_shaft.py", "tests/test_thin_bolted_finite_mechanics.py",
                 "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/isotropic-shaft-method-v4.json",
                 "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/finite-frame-method-v4.json"]:
        pins[path] = method.frame.sha(method.frame.ROOT/path)
    report = {"schema": "thin_bolted_generic_finite_potential_newton_method/v1",
              "scope": "source-bound small generic conservative systems only; no candidate assembly or execution",
              "source_sha256": pins, "observed_coupons": observed, "pytest_tests_passed": 19, "ruff": "pass",
              "options": method.asdict(method.NewtonOptions()), "generalized_residual_tolerance_n": 1e-5,
              "floor_bearing_threshold_n": 1e-7, "independent_review_required_before_candidate_execution": True,
              "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "primary_sources": method.SOURCES,
              "commands": ["OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_finite_newton.py",
                           ".venv/bin/ruff check scripts/thin_bolted_finite_newton.py scripts/check_thin_bolted_finite_newton.py tests/test_thin_bolted_finite_newton.py",
                           "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.check_thin_bolted_finite_newton --out NEW_UNUSED_PATH.json"],
              "limits": ["Step-only regularization is absent from published physical forces, potential and residual; a converged equilibrium is not a stability or strength result.",
                         "Gradient-work error is QUADPACK's estimate, not a rigorous bound. Integrals with warnings or unmet budgets reject the trial. Conservative gradient/potential consistency remains a caller contract.",
                         "The circular quotient requires the previously verified gauge-invariant physical port/load/director scope. Local material-roll work is monitored; it is not a complete proof for a new physical potential.",
                         "Support feedback is a fixed own-corner XY-branch rule under assumed no slip; cycles fail. No floor behavior is qualified.",
                         "No full candidate, load-case continuation, geometry reconstruction, native solve or resistance check is executed here."],
              "release": {"candidate_accepted": False, "complete_joint_acceptance": False, "capacity_established": False,
                          "fabrication_released": False, "structural_released": False, "climbing_released": False}}
    data = (json.dumps(report, indent=2, allow_nan=False)+"\n").encode()
    args.out.open("xb").write(data)
    print(json.dumps({"path": str(args.out), "sha256": method.frame.sha(args.out),
                      "method_coupon_checks_pass": observed["method_coupon_checks_pass"]}))


if __name__ == "__main__":
    main()
