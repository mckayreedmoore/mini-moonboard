"""The saved service-joint projection method for any number of bolt pairs.

The equations and tolerances follow check_frame.py. Pair count is determined
from the input rather than fixed to the worker's four bolts.
"""

import numpy as np
from scipy import optimize


def project_disks(value, radius):
    pairs = np.asarray(value).reshape(-1, 2)
    norms = np.linalg.norm(pairs, axis=1)
    return (
        pairs * np.minimum(1.0, radius / np.maximum(norms, 1e-300))[:, None]
    ).ravel()


def clearance_offsets(f0, response, clearance):
    size = len(f0)
    if clearance == 0:
        return np.zeros(size), {"evaluations": 0, "projection_residual_mm": 0.0}
    step = 1.0 / np.linalg.norm(response, ord=2)
    eye = np.eye(size)

    def residual(h):
        return h - project_disks(h + step * (f0 - response @ h), clearance)

    def jacobian(h):
        z = (h + step * (f0 - response @ h)).reshape(-1, 2)
        derivative = np.zeros((size, size))
        for i, pair in enumerate(z):
            radius = np.linalg.norm(pair)
            unit = pair / max(radius, 1e-300)
            derivative[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = (
                np.eye(2)
                if radius <= clearance
                else clearance / radius * (np.eye(2) - np.outer(unit, unit))
            )
        return eye - derivative @ (eye - step * response)

    symmetric = (response + response.T) / 2

    def objective(z):
        h = clearance * z
        return 0.5 * h @ symmetric @ h - f0 @ h

    def gradient(z):
        return clearance * (symmetric @ (clearance * z) - f0)

    def constraints(z):
        return 1.0 - np.sum(z.reshape(-1, 2) ** 2, axis=1)

    def constraint_jacobian(z):
        result = np.zeros((size // 2, size))
        for i in range(size // 2):
            result[i, 2 * i : 2 * i + 2] = -2.0 * z[2 * i : 2 * i + 2]
        return result

    seed = optimize.minimize(
        objective,
        np.zeros(size),
        jac=gradient,
        method="SLSQP",
        constraints=[{"type": "ineq", "fun": constraints, "jac": constraint_jacobian}],
        options={"ftol": 1e-12, "maxiter": 500},
    )
    if not np.all(np.isfinite(seed.x)):
        raise ValueError("nonfinite clearance seed")
    answer = optimize.least_squares(
        residual,
        project_disks(clearance * seed.x, clearance),
        jac=jacobian,
        ftol=1e-13,
        xtol=1e-13,
        gtol=1e-13,
        max_nfev=200,
    )
    error = float(np.max(abs(residual(answer.x))))
    polish_evaluations = 0
    if error > 1e-8:
        # A small gradient in an ill-conditioned projection can stop before
        # its declared residual is reached. Continue the same equations and
        # keep the original acceptance tolerance.
        polished = optimize.least_squares(
            residual, answer.x, jac=jacobian, ftol=None, gtol=None,
            xtol=1e-14, max_nfev=400,
        )
        polished_error = float(np.max(abs(residual(polished.x))))
        polish_evaluations = int(polished.nfev)
        if polished_error < error:
            answer, error = polished, polished_error
    if error > 1e-8:
        raise ValueError(f"clearance projection did not converge: {error}")
    return answer.x, {
        "evaluations": int(answer.nfev),
        "polish_evaluations": polish_evaluations,
        "seed_iterations": int(seed.nit),
        "seed_success": bool(seed.success),
        "seed_message": str(seed.message),
        "raw_response_asymmetry_n_per_mm": float(np.max(abs(response - response.T))),
        "projection_residual_mm": error,
    }
