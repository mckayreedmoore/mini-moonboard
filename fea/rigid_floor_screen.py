"""Rigid, compression-only floor equilibrium feasibility; never structural approval."""
import numpy as np
from scipy.optimize import linprog

RAYS = 16
LIMITS = (
    "Rigid equilibrium feasibility only; no stiffness, pressure distribution, "
    "contact compatibility, dynamics, strength or approval. Forces are one "
    "admissible witness, not predicted reaction allocation. The 16-ray friction "
    "polygon is inscribed in the circular Coulomb cone: polygon infeasibility "
    "does not prove circular-cone infeasibility."
)


def solve(points_mm, external_wrench, mu):
    """Balance external [Fx,Fy,Fz,Mx,My,Mz] in N/Nmm about the global origin.

    Floor points have world Z=0. Returned forces act from floor onto structure.
    All external loads, including gravity, must already be included by caller.
    """
    points = np.asarray(points_mm, dtype=float)
    wrench = np.asarray(external_wrench, dtype=float)
    friction = np.asarray(mu, dtype=float)
    if (points.ndim != 2 or points.shape[1:] != (3,) or len(points) == 0
            or not np.isfinite(points).all() or np.any(np.abs(points[:, 2]) > 1e-9)
            or wrench.shape != (6,) or not np.isfinite(wrench).all()
            or friction.ndim != 0 or not np.isfinite(friction) or friction < 0):
        raise ValueError("Require finite Nx3 floor points at Z=0, a six-component wrench and scalar mu>=0")
    mu = float(friction)
    angles = np.arange(RAYS)*2*np.pi/RAYS
    rays = np.column_stack((mu*np.cos(angles), mu*np.sin(angles), np.ones(RAYS)))
    forces = np.tile(rays, (len(points), 1))
    moments = np.cross(np.repeat(points, RAYS, axis=0), forces)
    matrix = np.column_stack((forces, moments)).T
    # Nmm rows scaled to Nm solely for numerical conditioning.
    scales = np.array([1., 1., 1., 1000., 1000., 1000.])
    result = linprog(np.zeros(len(forces)), A_eq=matrix/scales[:, None],
                     b_eq=-wrench/scales, bounds=(0., None), method="highs")
    if result.status == 2:
        return {"status": "infeasible", "polygon_feasible": False,
                "circular_cone_infeasibility_proven": False, "limits": LIMITS}
    if not result.success or result.status != 0:
        raise RuntimeError(f"Floor equilibrium solver failed: {result.status}: {result.message}")
    weights = np.asarray(result.x, dtype=float)
    if weights.shape != (len(forces),) or not np.isfinite(weights).all():
        raise ValueError("Solver returned an invalid witness")
    point_forces = weights.reshape(len(points), RAYS) @ rays
    # Independent free-body arithmetic, not the LP matrix residual.
    residual = np.concatenate((point_forces.sum(axis=0),
                               np.cross(points, point_forces).sum(axis=0)))+wrench
    force_tolerance = 1e-7*max(1., float(np.max(np.abs(wrench[:3]))))
    moment_tolerance = 1e-7*max(1000., float(np.max(np.abs(wrench[3:]))),
                               float(np.max(np.abs(points)))*max(1., float(np.max(np.abs(wrench[:3])))))
    normals = point_forces[:, 2]
    friction_excess = np.linalg.norm(point_forces[:, :2], axis=1)-mu*normals
    if (not np.isfinite(point_forces).all() or not np.isfinite(residual).all()
            or np.min(weights) < -force_tolerance or np.min(normals) < -force_tolerance
            or np.max(friction_excess) > force_tolerance
            or np.max(np.abs(residual[:3])) > force_tolerance
            or np.max(np.abs(residual[3:])) > moment_tolerance):
        raise ValueError("Floor equilibrium witness failed independent force/moment/friction/tension checks")
    return {"status": "feasible", "polygon_feasible": True,
            "point_forces_n": point_forces.tolist(), "residual_wrench": residual.tolist(),
            "minimum_normal_force_n": float(np.min(normals)),
            "maximum_friction_excess_n": float(np.max(friction_excess)),
            "force_tolerance_n": force_tolerance, "moment_tolerance_nmm": moment_tolerance,
            "limits": LIMITS}
