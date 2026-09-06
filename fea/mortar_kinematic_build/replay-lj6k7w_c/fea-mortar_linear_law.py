"""Arithmetic check for exported internal LINEAR mortar quantities, not FRD.

This does not reconstruct coupling matrices, kinematics or accepted-state
provenance. No physical or numerical acceptance tolerance is chosen here.
Equations follow the pinned CalculiX 2.21 stressmortar.c and regularization
routines documented in docs/mortar-local-audit-basis.md.
"""
import math


def residuals(*, ln, lt, lt_start, q, ut, mu, normal_inverse_stiffness,
              tangent_inverse_stiffness, constant_n, constant_t, activity, ndof,
              normal_mode, tangent_mode):
    """Return signed residuals for the pre-update internal state of one node.

    Caller must establish frozen bases, correct weighted inputs, and their
    exact observation phase. Only mode 1 normal/tangent laws are supported.
    Excluded nodes remain excluded even if their computed residual is zero.
    """
    vectors = (lt, lt_start, ut)
    if any(type(mode) is not int or mode != 1 for mode in (normal_mode, tangent_mode)):
        raise ValueError("Only LINEAR normal and ordinary tangent mode 1 are supported")
    if any(not isinstance(v, (list, tuple)) or len(v) != 2 for v in vectors):
        raise ValueError("Two internal tangent components required")
    values = (ln, q, mu, normal_inverse_stiffness, tangent_inverse_stiffness,
              constant_n, constant_t, *lt, *lt_start, *ut)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in values):
        raise ValueError("Finite internal scalar quantities required")
    if (mu < 0 or tangent_inverse_stiffness < 0 or
            min(normal_inverse_stiffness, constant_n, constant_t) <= 0):
        raise ValueError("Nonnegative friction/tangent compliance and positive normal compliance/constants required")
    if type(activity) is not int or activity not in (-3, -2, -1, 0, 1, 2):
        raise ValueError("Known integer activity state required")
    if type(ndof) is not int or ndof not in (0, 1, 2, 3):
        raise ValueError("Integer active DOF count from zero to three required")
    gn = normal_inverse_stiffness * ln
    gt = [tangent_inverse_stiffness * (a-b) for a, b in zip(lt, lt_start, strict=True)]
    elastic_slip = [a-b for a, b in zip(ut, gt, strict=True)]
    w = [a+constant_t*b for a, b in zip(lt, elastic_slip, strict=True)]
    norm_w = math.hypot(*w)
    scale = mu if mu > 1e-10 else 1.0
    bound = scale * (ln + constant_n * (q-gn))
    rn = scale*ln - max(0.0, bound)
    if not all(math.isfinite(v) for v in (gn, *gt, *elastic_slip, *w, norm_w, bound, rn)):
        raise ValueError("Internal arithmetic overflow; not an admissible result")
    if mu <= 1e-10 or activity < 0:
        rt = [0.0, 0.0]
    elif activity == 0:
        rt = list(lt)
    elif activity == 1:
        rt = elastic_slip
    else:
        if norm_w == 0:
            raise ValueError("Undefined slipping direction; no zero-norm acceptance shortcut")
        rt = [a-bound*b/norm_w for a, b in zip(lt, w, strict=True)]
    result = {
        "eligible": ndof > 0 and activity >= 0,
        "normal_regularization": gn, "tangent_regularization": gt,
        "weighted_regularized_opening": -q+gn,
        "weighted_complementarity_product": ln*(-q+gn),
        "algorithmic_friction_bound": bound,
        "normal_residual": rn, "tangent_residual": rt,
        "internal_coulomb_excess": math.hypot(*lt)-mu*ln,
    }
    computed = [v for value in result.values() for v in (value if isinstance(value, list) else [value])]
    if not all(math.isfinite(v) for v in computed):
        raise ValueError("Internal arithmetic overflow; not an admissible result")
    return result
