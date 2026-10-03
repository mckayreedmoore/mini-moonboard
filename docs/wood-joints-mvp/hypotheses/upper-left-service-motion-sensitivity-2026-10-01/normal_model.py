"""Unilateral normal springs with an explicit representative for neutral motion."""

import itertools

import numpy as np

MOTION_TOL = 1e-10
FORCE_TOL = 1e-7


def minimum_norm_feasible(base, nullspace, constraints):
    """Project zero onto the branch polyhedron in at most three neutral DOFs.

    ``base`` is perpendicular to the orthonormal nullspace. Enumerating up to
    its dimension in binding inequalities gives the closest feasible point;
    a zero-force contact is an inequality, not an added bilateral restraint.
    """
    if np.min(constraints @ base) >= -MOTION_TOL:
        return base
    dimension = nullspace.shape[1]
    if not dimension:
        return None
    a = constraints @ nullspace
    rhs = -constraints @ base
    candidates = []
    for count in range(1, dimension + 1):
        for indices in itertools.combinations(range(len(rhs)), count):
            rows = a[list(indices)]
            gram = rows @ rows.T
            if np.linalg.matrix_rank(gram, tol=1e-12) < count:
                continue
            z = rows.T @ np.linalg.solve(gram, rhs[list(indices)])
            if np.min(a @ z - rhs) >= -MOTION_TOL:
                candidates.append(z)
    if not candidates:
        return None
    return base + nullspace @ min(candidates, key=lambda z: float(z @ z))


def normal_response(bolts, patches, bolt_stiffness, patch_stiffness, demand):
    """Invert traction on the cleat; report ambiguity rather than invent a fixity.

    Positive opening gives bolt tension, negative opening gives contact
    compression. R = -Kq is target interface traction, not an extra applied
    load. Among equal-force equilibrium poses, choose minimum scaled motion.
    This is a deterministic representative, not a physical rotation law.
    """
    geometry = np.asarray(bolts + patches, dtype=float)
    stiffness = np.asarray([bolt_stiffness] * len(bolts) + patch_stiffness, dtype=float)
    target = np.asarray(demand, dtype=float)
    if (geometry.shape != (len(stiffness), 3) or target.shape != (3,)
            or not np.all(np.isfinite(geometry)) or not np.all(np.isfinite(target))
            or not np.all(np.isfinite(stiffness)) or np.min(stiffness) <= 0):
        raise ValueError("Invalid normal geometry, stiffness or traction")
    count = len(bolts)
    length = max(1.0, float(np.max(np.linalg.norm(geometry[:, 1:], axis=1))))
    scale = np.array([1.0, length, length])
    b = geometry / scale
    d = target / scale
    direction = np.r_[np.ones(count), -np.ones(len(patches))]
    candidates = []
    for mask in itertools.product((False, True), repeat=len(b)):
        active = np.asarray(mask)
        matrix = b.T @ ((stiffness * active)[:, None] * b)
        values, vectors = np.linalg.eigh(matrix)
        positive = values > max(1e-12, float(np.max(values)) * 1e-11)
        base = -vectors[:, positive] @ ((vectors[:, positive].T @ d) / values[positive])
        if np.max(np.abs(matrix @ base + d)) > FORCE_TOL * max(1, np.max(np.abs(d))):
            continue
        signs = direction * (2 * active.astype(int) - 1)
        y = minimum_norm_feasible(base, vectors[:, ~positive], signs[:, None] * b)
        if y is not None:
            candidates.append(y)
    if not candidates:
        raise ValueError("No compatible normal bolt/contact equilibrium")
    y = min(candidates, key=lambda value: float(value @ value))
    motion = y / scale
    opening = geometry @ motion
    tension = stiffness[:count] * np.maximum(opening[:count], 0)
    compression = stiffness[count:] * np.maximum(-opening[count:], 0)
    recovered = geometry.T @ np.r_[-tension, compression]
    residual = recovered - target
    if not np.allclose(recovered, target, rtol=1e-9, atol=FORCE_TOL):
        raise ValueError("Returned normal motion does not reproduce target traction")

    bearing = np.r_[tension, compression] > FORCE_TOL
    matrix = b.T @ ((stiffness * bearing)[:, None] * b)
    values, vectors = np.linalg.eigh(matrix)
    positive = values > max(1e-12, float(np.max(values)) * 1e-11)
    neutral = vectors[:, ~positive]
    interval = None
    if neutral.shape[1] == 1:
        lower, upper = -np.inf, np.inf
        # Zero-force bolts cannot open; zero-force contacts cannot close.
        signs = np.r_[-np.ones(count), np.ones(len(patches))]
        for coefficient, rhs in zip(((signs[:, None] * b) @ neutral[:, 0])[~bearing],
                                    (-signs * opening)[~bearing], strict=True):
            if abs(coefficient) < 1e-12:
                continue
            if coefficient > 0:
                lower = max(lower, rhs / coefficient)
            else:
                upper = min(upper, rhs / coefficient)
        interval = [None if np.isinf(lower) else float(lower),
                    None if np.isinf(upper) else float(upper)]
    unique = int(np.sum(positive)) == 3
    if interval is not None and all(x is not None for x in interval):
        unique = interval[1] - interval[0] <= MOTION_TOL
    return {
        "motion_mm_rad_rad": motion.tolist(),
        "tension_n": tension.tolist(), "compression_n": compression.tolist(),
        "opening_at_all_sites_mm": opening.tolist(),
        "traction_residual_n_nmm_nmm": residual.tolist(),
        "force_bearing_stiffness_rank": int(np.sum(positive)),
        "zero_force_touching_contacts": int(np.sum(
            (np.abs(opening[count:]) <= MOTION_TOL) & (compression <= FORCE_TOL))),
        "motion_uniqueness_established": bool(unique),
        "neutral_mode_basis_mm_rad_rad_per_mm": (neutral / scale[:, None]).T.tolist(),
        "one_neutral_mode_parameter_interval_mm": interval,
        "selection": "Minimum norm of [translation, L*tilt1, L*tilt2]; neutral pose is a representative, not a physical prediction.",
        "rotation_scale_length_mm": length,
    }
