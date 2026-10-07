"""Generic numerical continuation of an unchanged finite conservative potential.

Only scaled Newton steps are regularized. Full physical gradients determine
equilibrium; fixed corner support patterns are updated only after equilibrium.
Near cancellation, gradient-work integration compares the original potential
without replacing its published scalar energy or physical force law.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.sparse import csr_matrix, diags, eye

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_numerical_step as previous

GENERALIZED_RESIDUAL_TOLERANCE_N = frame.GENERALIZED_RESIDUAL_TOLERANCE_N
FLOOR_BEARING_THRESHOLD_N = 1e-7
FROZEN_SOURCES = {
    "scripts/thin_bolted_frame_mechanics.py": "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448",
    "scripts/thin_bolted_numerical_step.py": "82b7d5a8d9d9dc871ee6410fb4c5854093a998cfd9b331fdd986917b63ebbc28",
    "scripts/thin_bolted_isotropic_shaft.py": "be8e5277999aa2ce01b4a8d81c0e9124dad9dc6023712c13e91595600c1c027a",
    "scripts/thin_bolted_finite_frame.py": "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588",
}
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
SOURCES = [{"url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.quad.html",
            "locator": "quad parameters epsabs/epsrel, full_output and estimated absolute error; QUADPACK qagse",
            "use": "Adaptive integral of the unchanged physical gradient along a fixed-pattern coordinate segment; unresolved integrals reject a trial."},
           {"url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.spsolve.html",
            "locator": "spsolve sparse linear-system interface",
            "use": "Reuse frozen numerical_step.numerical_solve for numerical steps only."}]


def source_pins():
    pins = {**FROZEN_SOURCES, "scripts/thin_bolted_finite_newton.py": LOADED_PRODUCER_SHA256}
    if any(frame.sha(frame.ROOT/path) != digest for path, digest in pins.items()):
        raise ValueError("finite numerical helper or frozen dependency changed")
    return pins


@dataclass(frozen=True)
class NewtonOptions:
    max_iterations: int = 300
    max_support_patterns: int = 10
    max_regularization_trials: int = 20
    max_backtracks: int = 30
    max_step_inf_mm: float = 100.
    initial_damping: float = 1e-6
    maximum_damping: float = 1e8
    minimum_damping: float = 1e-12
    armijo_fraction: float = 1e-4
    work_relative_tolerance: float = 1e-8
    work_absolute_slope_fraction: float = 1e-10
    work_minimum_absolute_tolerance_nmm: float = 1e-30
    work_subinterval_limit: int = 50

    def __post_init__(self):
        counts = (self.max_iterations, self.max_support_patterns, self.max_regularization_trials,
                  self.max_backtracks, self.work_subinterval_limit)
        values = (self.max_step_inf_mm, self.initial_damping, self.maximum_damping, self.minimum_damping,
                  self.armijo_fraction, self.work_relative_tolerance, self.work_absolute_slope_fraction,
                  self.work_minimum_absolute_tolerance_nmm)
        if any(not isinstance(v, int) or v < 1 for v in counts) or not np.isfinite(values).all() or min(values) <= 0:
            raise ValueError("positive finite numerical options required")
        if not self.minimum_damping <= self.initial_damping <= self.maximum_damping or self.armijo_fraction >= 1:
            raise ValueError("invalid numerical damping or Armijo bounds")


class IdentityChart:
    def __init__(self, ndof):
        self.ndof = ndof
        self.indices = np.arange(ndof)

    def canonicalize(self, q):
        q = np.asarray(q, dtype=float)
        if q.shape != (self.ndof,) or not np.isfinite(q).all():
            raise ValueError("finite complete initial state required")
        return q.copy(), {}

    def lift(self, reduced):
        value = np.zeros(self.ndof)
        value[self.indices] = reduced
        return value

    def gauge_work(self, q, gradient):
        return {}

    def gauge_work_budgets(self, q, gradient):
        return {}


class CircularShaftQuotient(IdentityChart):
    """Exact minimal LOCAL director chart for the verified circular symmetry.

    The retained coordinates describe a slice theta_local_first_x=0 after a
    common RIGHT roll canonicalization. Its embedding is linear, so the reduced
    gradient/Hessian are principal restrictions. The omitted full physical dual
    remains in the residual test. This does not remove a world rotation or add
    physical torsional support. World rigid generators include the compensating
    common material roll through the frozen isotropic utility.
    """

    def __init__(self, shaft_adapter):
        super().__init__(shaft_adapter.ndof)
        self.shaft_adapter = shaft_adapter
        self.omitted_indices = np.array(sorted(row["appended_first_twist_dof"]
                                               for row in shaft_adapter.mechanics.shafts.values()), dtype=int)
        if len(set(self.omitted_indices)) != len(self.omitted_indices):
            raise ValueError("one distinct first local twist coordinate per shaft required")
        self.indices = np.setdiff1d(self.indices, self.omitted_indices)

    def canonicalize(self, q):
        q, _ = super().canonicalize(q)
        q, metadata = self.shaft_adapter.minimal_director_gauge(q)
        if np.max(abs(q[self.omitted_indices]), initial=0.) > 1e-8:
            raise ValueError("minimal shaft chart canonicalization failed")
        # This numerical roundoff normalization follows the proved local chart;
        # physical points are neither projected nor assigned a torsional clamp.
        q[self.omitted_indices] = 0.
        return q, metadata

    def gauge_work(self, q, gradient):
        return {body: float(mode @ gradient) for body, mode in self.shaft_adapter.material_roll_generators(q).items()}

    def gauge_work_budgets(self, q, gradient):
        return {body: max(1e-6, 128*np.finfo(float).eps*float(np.sum(abs(mode*gradient))))
                for body, mode in self.shaft_adapter.material_roll_generators(q).items()}

    def world_rigid_generators(self, q, reference_point_xyz_mm=None):
        return self.shaft_adapter.quotient_world_rigid_generators(q, reference_point_xyz_mm)


class CornerSupportFeedback:
    """Fixed corner IDs; remove XY bearing on a nonbearing normal branch."""

    def __init__(self, normal_contact_id_by_support):
        self.normal_contact_id_by_support = dict(normal_contact_id_by_support)
        if (not self.normal_contact_id_by_support or
                any(not isinstance(k, str) or not isinstance(v, str) for k, v in self.normal_contact_id_by_support.items())):
            raise ValueError("explicit support-to-normal contact IDs required")

    @classmethod
    def from_finite_frame(cls, potential):
        mapping = {}
        for row in potential.interactions:
            if row["kind"] == "floor_tangent_xy":
                support, normal = row.get("floor_support_id"), row.get("normal_contact_id")
                if not support or not normal or support in mapping:
                    raise ValueError("distinct source-bound corner support IDs required")
                mapping[support] = normal
        return cls(mapping)

    def __call__(self, q, fields, disabled):
        reactions = fields["floor_normal_reactions_n"]
        if not set(disabled) <= self.normal_contact_id_by_support.keys():
            raise ValueError("unknown fixed corner support ID")
        result = set()
        for support, normal_id in self.normal_contact_id_by_support.items():
            reaction = float(reactions[normal_id])
            if not np.isfinite(reaction) or reaction < -1e-10:
                raise ValueError("finite compression-only corner normal reaction required")
            if reaction <= FLOOR_BEARING_THRESHOLD_N:
                result.add(support)
        return frozenset(result)


def evaluate(response, q, disabled, *, tangent=False, recover_actions=False, progress=None, phase="evaluation"):
    if progress is not None:
        progress({"event": phase, "disabled_floor_support_ids": sorted(disabled)})
    fields = response(q, tangent=tangent, recover_actions=recover_actions, disabled_floor_support_ids=tuple(sorted(disabled)))
    gradient = np.asarray(fields["gradient_n"], dtype=float)
    if gradient.shape != q.shape or not np.isfinite(gradient).all() or not np.isfinite(fields["energy_nmm"]):
        raise ValueError("finite original potential and complete physical gradient required")
    if tangent:
        hessian = csr_matrix(fields["hessian_csr"])
        if hessian.shape != (len(q), len(q)) or not np.isfinite(hessian.data).all():
            raise ValueError("finite original physical Hessian required")
        fields = {**fields, "hessian_csr": hessian}
    return fields


def potential_difference(response, q, delta, disabled, base, trial, slope, options, *, progress=None,
                         predicted_decrease_nmm=None):
    """Compare original energies, integrating g·delta only under cancellation.

    The fundamental theorem gives E(q+delta)-E(q)=integral_0^1 g(q+t delta)·delta dt.
    QUADPACK reports an error estimate, not a rigorous bound. Its warning or an
    unmet absolute/relative budget makes the comparison unresolved. The line
    search uses value+estimated_error, without an additive energy acceptance fudge.
    """
    before, after = float(base["energy_nmm"]), float(trial["energy_nmm"])
    difference = after-before
    subtraction_error = 4*np.finfo(float).eps*(abs(before)+abs(after))
    predicted = abs(slope) if predicted_decrease_nmm is None else abs(predicted_decrease_nmm)
    if abs(difference) > 32*subtraction_error and predicted > 32*subtraction_error:
        return {"difference_nmm": difference, "estimated_absolute_error_nmm": subtraction_error,
                "method": "published-potential-subtraction", "resolved": True, "gradient_evaluations": 0}
    epsabs = max(options.work_minimum_absolute_tolerance_nmm,
                 options.work_absolute_slope_fraction*abs(slope))
    evaluations = 0

    def work(t):
        nonlocal evaluations
        evaluations += 1
        fields = evaluate(response, q+t*delta, disabled, progress=progress, phase="gradient-work-evaluation")
        return float(np.asarray(fields["gradient_n"]) @ delta)

    result = quad(work, 0., 1., epsabs=epsabs, epsrel=options.work_relative_tolerance,
                  limit=options.work_subinterval_limit, full_output=1)
    value, error = float(result[0]), float(result[1])
    budget = max(epsabs, options.work_relative_tolerance*abs(value))
    return {"difference_nmm": value, "estimated_absolute_error_nmm": error,
            "method": "fixed-pattern-physical-gradient-work-QUADPACK", "resolved": len(result) == 3 and error <= budget,
            "absolute_error_budget_nmm": epsabs, "relative_error_budget": options.work_relative_tolerance,
            "gradient_evaluations": evaluations, "integration_message": None if len(result) == 3 else str(result[3])}


def solve_finite_potential(response, q0, *, quotient=None, support_feedback=None, initial_disabled_support_ids=(),
                           options=None, progress=None):
    """Solve fixed-pattern physical equilibria; return actions only on success.

    ``response`` follows FiniteFramePotential.response's public keyword API.
    ``q0`` is initialization only. Support feedback runs after the full original
    generalized residual falls below 1e-5 N. Repeated support patterns fail.
    Progress callbacks receive evaluation and iteration events for caller-owned
    throttled updates; no candidate assembly, execution or writer is invoked.
    """
    source_pins()
    options = options or NewtonOptions()
    q0 = np.asarray(q0, dtype=float)
    chart = quotient or IdentityChart(len(q0))
    q, gauge_metadata = q0.copy(), {}
    disabled = frozenset(initial_disabled_support_ids)
    patterns = {tuple(sorted(disabled))}
    history, support_history = [], []
    damping, maximum_damping = options.initial_damping, 0.
    accepted_steps = rejected_trials = work_evaluations = 0
    residual, energy = None, None

    def failure(reason):
        source_pins()
        return {"converged": False, "termination": reason, "diagnostic_last_q": q.copy(),
                "gradient_inf_n": residual, "potential_energy_nmm": energy,
                "diagnostic_last_q_is_a_converged_or_accepted_force_field": False,
                "iteration_history": history, "support_history": support_history,
                "disabled_floor_support_ids": sorted(disabled), "options": asdict(options),
                "accepted_numerical_steps": accepted_steps, "rejected_numerical_trials": rejected_trials,
                "gradient_work_evaluations": work_evaluations,
                "maximum_transient_scaled_step_regularization": maximum_damping,
                "generalized_residual_tolerance_n": GENERALIZED_RESIDUAL_TOLERANCE_N,
                "physical_residual_uses_unmodified_laws": True, "physical_twist_supports_added": 0}

    try:
        q, gauge_metadata = chart.canonicalize(q0)
    except ValueError as error:
        return failure("initial finite chart unsupported: " + str(error))
    for support_iteration in range(options.max_support_patterns):
        converged = False
        try:
            for iteration in range(options.max_iterations):
                fields = evaluate(response, q, disabled, tangent=True, progress=progress, phase="newton-evaluation")
                gradient, energy = np.asarray(fields["gradient_n"]), float(fields["energy_nmm"])
                residual = float(np.max(abs(gradient), initial=0.))
                gauge_work = chart.gauge_work(q, gradient)
                gauge_budgets = chart.gauge_work_budgets(q, gradient)
                row = {"support_pattern_iteration": support_iteration, "iteration": iteration,
                       "gradient_inf_n": residual, "physical_potential_energy_nmm": energy,
                       "disabled_floor_support_ids": sorted(disabled), "step_damping": damping,
                       "material_roll_work_nmm_per_rad": gauge_work}
                history.append(row)
                row["material_roll_work_budget_nmm_per_rad"] = gauge_budgets
                if progress is not None:
                    progress({"event": "newton-iteration", **row})
                if any(abs(work) > gauge_budgets[body] for body, work in gauge_work.items()):
                    return failure("physical potential breaks the circular material-roll gauge")
                if residual < GENERALIZED_RESIDUAL_TOLERANCE_N:
                    converged = True
                    break
                index = chart.indices
                reduced_gradient = gradient[index]
                if np.max(abs(reduced_gradient), initial=0.) < GENERALIZED_RESIDUAL_TOLERANCE_N:
                    return failure("reduced chart residual passes while full physical residual fails")
                hessian = fields["hessian_csr"][index][:, index]
                scale = diags(1/np.sqrt(np.maximum(abs(hessian.diagonal()), 1e-12)))
                scaled_hessian = (scale @ hessian @ scale).tocsc()
                identity = eye(len(index), format="csc")
                accepted = False
                for _ in range(options.max_regularization_trials):
                    if damping > options.maximum_damping:
                        break
                    maximum_damping = max(maximum_damping, damping)
                    reduced_step = np.asarray(scale @ previous.numerical_solve(
                        scaled_hessian+damping*identity, -scale @ reduced_gradient)).ravel()
                    if not np.isfinite(reduced_step).all():
                        damping *= 10.; rejected_trials += 1
                        continue
                    step = chart.lift(reduced_step)
                    largest = float(np.max(abs(step), initial=0.))
                    if largest > options.max_step_inf_mm:
                        step *= options.max_step_inf_mm/largest
                    slope = float(gradient @ step)
                    if slope >= 0.:
                        damping *= 10.; rejected_trials += 1
                        continue
                    alpha = 1.
                    for _ in range(options.max_backtracks):
                        delta = alpha*step
                        candidate = q+delta
                        prediction = -alpha*slope-.5*float(delta @ (fields["hessian_csr"] @ delta))
                        try:
                            trial = evaluate(response, candidate, disabled, progress=progress, phase="trial-evaluation")
                            difference = potential_difference(response, q, delta, disabled, fields, trial,
                                                              alpha*slope, options, progress=progress,
                                                              predicted_decrease_nmm=prediction)
                        except (ValueError, KeyError, FloatingPointError) as error:
                            rejected_trials += 1; alpha *= .5
                            row["last_rejected_physical_trial"] = str(error)
                            continue
                        work_evaluations += difference["gradient_evaluations"]
                        if (difference["resolved"] and difference["difference_nmm"] + difference["estimated_absolute_error_nmm"]
                                <= options.armijo_fraction*alpha*slope):
                            ratio = -difference["difference_nmm"]/prediction if prediction > 0. else 0.
                            q = candidate
                            maximum_damping = max(maximum_damping, damping)
                            accepted_steps += 1
                            accepted = True
                            row.update(accepted_step_alpha=alpha, accepted_step_inf_mm=float(np.max(abs(delta), initial=0.)),
                                       accepted_original_energy_nmm=float(trial["energy_nmm"]),
                                       original_model_reduction_ratio=ratio, potential_difference=difference)
                            damping = (min(damping*10., options.maximum_damping) if ratio < .25 or alpha < .25
                                       else max(damping*.25, options.minimum_damping) if ratio > .75 and alpha >= .5 else damping)
                            break
                        rejected_trials += 1; alpha *= .5
                    if accepted:
                        break
                    damping *= 10.
                    if damping > options.maximum_damping:
                        break
                if not accepted:
                    return failure("finite original-potential numerical line search unresolved")
            if not converged:
                fields = evaluate(response, q, disabled, progress=progress, phase="iteration-limit-diagnostic")
                residual, energy = float(np.max(abs(fields["gradient_n"]), initial=0.)), float(fields["energy_nmm"])
                if residual >= GENERALIZED_RESIDUAL_TOLERANCE_N:
                    return failure("finite Newton iteration limit")
                # An accepted last step may meet the unchanged force criterion;
                # still perform fixed-support feedback and action checks below.
                converged = True
            next_disabled = disabled if support_feedback is None else frozenset(support_feedback(q, fields, disabled))
            support_history.append({"disabled_floor_support_ids": sorted(disabled),
                                    "next_disabled_floor_support_ids": sorted(next_disabled), "gradient_inf_n": residual})
            if next_disabled == disabled:
                final = evaluate(response, q, disabled, recover_actions=True, progress=progress, phase="converged-action-recovery")
                residual, energy = float(np.max(abs(final["gradient_n"]), initial=0.)), float(final["energy_nmm"])
                if not np.allclose(final["gradient_n"], fields["gradient_n"], rtol=1e-10, atol=1e-10):
                    return failure("action recovery changed the original physical gradient")
                energy_budget = 32*np.finfo(float).eps*(abs(energy)+abs(float(fields["energy_nmm"])))+1e-12
                if abs(energy-float(fields["energy_nmm"])) > energy_budget:
                    return failure("action recovery changed the original published potential")
                if residual >= GENERALIZED_RESIDUAL_TOLERANCE_N:
                    return failure("action recovery changed the original physical residual")
                final_gauge_work = chart.gauge_work(q, final["gradient_n"])
                final_gauge_budgets = chart.gauge_work_budgets(q, final["gradient_n"])
                if any(abs(work) > final_gauge_budgets[body] for body, work in final_gauge_work.items()):
                    return failure("converged physical potential breaks the circular material-roll gauge")
                source_pins()
                return {"converged": True, "termination": "full physical equilibrium and fixed corner-support pattern converged",
                        "q": q.copy(), "physical_fields": final, "gradient_inf_n": residual, "potential_energy_nmm": energy,
                        "iteration_history": history, "support_history": support_history,
                        "disabled_floor_support_ids": sorted(disabled), "initial_gauge_metadata": gauge_metadata,
                        "generalized_residual_tolerance_n": GENERALIZED_RESIDUAL_TOLERANCE_N,
                        "physical_residual_uses_unmodified_laws": True, "physical_twist_supports_added": 0,
                        "accepted_numerical_steps": accepted_steps, "rejected_numerical_trials": rejected_trials,
                        "gradient_work_evaluations": work_evaluations,
                        "maximum_transient_scaled_step_regularization": maximum_damping, "options": asdict(options)}
            pattern = tuple(sorted(next_disabled))
            if pattern in patterns:
                return failure("repeated fixed corner-support activation pattern")
            patterns.add(pattern)
            disabled = next_disabled
        except (ValueError, KeyError, FloatingPointError) as error:
            return failure("finite physical evaluation failed: " + str(error))
    return failure("fixed corner-support pattern iteration limit")
