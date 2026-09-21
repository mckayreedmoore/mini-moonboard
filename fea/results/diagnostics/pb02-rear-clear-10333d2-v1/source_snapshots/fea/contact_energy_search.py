"""Exact line minimization for fixed-tangent, unilateral normal springs.

No finite-element stiffness is assembled. For each native equilibrium state,
K0 u = f - B.T q, where g = B u is signed opening and q = k g on the
springs included in that linear solve. K0 contains all unchanged bilateral
terms, including fixed tangential stiffness. Convex combinations retain that
identity, allowing subsequent line searches from interpolated states.

This helper selects iterates only. Final acceptance requires a fresh native
solve and the unchanged contact/equilibrium audits. Changing loads, tangential
stiffness, geometry or constraints invalidates the stored reaction identity.
"""
import numpy as np
from scipy.optimize import brentq


def normal_energy_step(gap, linear_contact_force, trial_gap, trial_linear_contact_force,
                       stiffness, *, gap_radius=None, linear_force_radius=None,
                       trial_gap_radius=None, trial_force_radius=None):
    """Minimize exact piecewise-quadratic potential on a native Newton segment.

    All vectors have one entry per normal spring, in identical order. Opening
    is positive. Linear force q is k*opening for an included spring, zero for an
    omitted spring; its sign is opposite the reported compression reaction.
    At an interpolated state q is interpolated, not recomputed from gap.
    """
    g, q, h, r, k = [np.asarray(value, dtype=float) for value in
                     (gap, linear_contact_force, trial_gap, trial_linear_contact_force, stiffness)]
    if (g.ndim != 1 or not g.size or any(value.shape != g.shape for value in (q,h,r,k))
            or not all(np.all(np.isfinite(value)) for value in (g,q,h,r,k)) or np.any(k <= 0)):
        raise ValueError('Require equal finite normal vectors and positive stiffnesses')
    radii = [np.zeros_like(g) if value is None else np.asarray(value, dtype=float)
             for value in (gap_radius, linear_force_radius, trial_gap_radius, trial_force_radius)]
    if any(value.shape != g.shape or not np.all(np.isfinite(value)) or np.any(value < 0) for value in radii):
        raise ValueError('Require finite nonnegative interval radii matching normal vectors')
    gr, qr, hr, rr = radii
    direction = h-g
    direction_radius = gr+hr
    force_difference = q-r
    force_difference_radius = qr+rr
    linear = -float(q@direction)
    raw_curvature = float(force_difference@direction)
    # Product interval bound includes the radius-radius term. This is based on
    # actual DAT quantization, not a relaxed curvature or contact tolerance.
    curvature_radius = float(np.abs(force_difference)@direction_radius
        +np.abs(direction)@force_difference_radius+direction_radius@force_difference_radius)
    if raw_curvature < 0 and raw_curvature+curvature_radius < 0:
        raise ValueError('Negative base curvature outside printed-data interval: states must share loads and tangent stiffness')
    curvature = max(0., raw_curvature)
    start_force = k*np.minimum(g, 0.)-q
    start_force_radius = k*gr+qr
    start_derivative_radius = float(np.abs(start_force)@direction_radius
        +np.abs(direction)@start_force_radius+direction_radius@start_force_radius)
    initial_contact_energy = .5*float(k@np.minimum(g, 0.)**2)

    def derivative(alpha):
        return linear+alpha*curvature+float((k*np.minimum(g+alpha*direction, 0.))@direction)

    def energy_change(alpha):
        normal = .5*float(k@np.minimum(g+alpha*direction, 0.)**2)
        return alpha*linear+.5*alpha*alpha*curvature+normal-initial_contact_energy

    if derivative(0.) >= 0:
        alpha = 0.
    elif derivative(1.) <= 0:
        alpha = 1.
    else:
        alpha = float(brentq(derivative, 0., 1., xtol=1.e-14, rtol=1.e-14))
    return {'alpha':alpha, 'gap_mm':(g+alpha*direction).tolist(),
            'linear_contact_force_n':(q+alpha*(r-q)).tolist(),
            'gap_radius_mm':((1.-alpha)*gr+alpha*hr).tolist(),
            'linear_contact_force_radius_n':((1.-alpha)*qr+alpha*rr).tolist(),
            'potential_change_nmm':energy_change(alpha),
            'directional_derivative_start_nmm':derivative(0.),
            'start_derivative_radius_nmm':start_derivative_radius,
            'start_derivative_interval_contains_zero':abs(derivative(0.)) <= start_derivative_radius,
            'directional_derivative_end_nmm':derivative(1.),
            'directional_derivative_selected_nmm':derivative(alpha),
            'base_directional_curvature_nmm':curvature,
            'raw_base_directional_curvature_nmm':raw_curvature,
            'base_curvature_radius_nmm':curvature_radius,
            'base_curvature_interval_nmm':[raw_curvature-curvature_radius, raw_curvature+curvature_radius],
            'negative_curvature_clamped_within_printed_interval':raw_curvature < 0,
            'active_from_interpolated_gap':(g+alpha*direction < 0.).tolist(),
            'final_native_verification_required':True}
