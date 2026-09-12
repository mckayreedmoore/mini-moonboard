"""Six-component elastic diagnostic for the frozen single-sided shoe weld.

This is an engineering stress screen, not an AISC-qualified root-bending
resistance model. Moments supplied to evaluate_weld are about weld_centroid().
"""
from math import cos, radians, sin, sqrt, tan

WELD_LEG_MM = 6.0
LENGTH_MM = 105.0 / cos(radians(40.0))
FEXX_MPA = 70.0 * 6.894757293
ALLOWABLE_MPA = 0.6 * FEXX_MPA / 2.0
SOURCES = (
    "https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_june-2018.pdf",
    "https://www.aisc.org/globalassets/modern-steel/archives/2024/january2024.pdf",
    "https://www.aisc.org/globalassets/modern-steel/archives/2025/january2025.pdf",
)


def weld_centroid(side):
    """Actual ideal throat centroid in global millimetres; no CAD import."""
    if side not in ("left", "right"):
        raise ValueError("side must be left or right")
    sign = 1 if side == "right" else -1
    angle = radians(40)
    origin_y = -18 * (1 + cos(angle))
    origin_z = 225 + 18 * sin(angle)
    center_y = origin_y + (234.525 - origin_z) * tan(angle) - 72.5 / cos(angle)
    return (sign * (1219.2 + 9.525 + WELD_LEG_MM / 4), center_y,
            234.525 + WELD_LEG_MM / 4)


def evaluate_weld(force_xyz_n, moment_xyz_nmm, side):
    """Return the frozen E70 diagnostic; moments are at throat centroid.

    The force and moment must describe the same cut free body. Include every
    bolt, contact and applied action on that body before taking the resultant.
    Both vectors must have three finite components. The hard detail gate stays
    unresolved even when the elastic diagnostic is below unity.
    """
    from math import isfinite
    if len(force_xyz_n) != 3 or len(moment_xyz_nmm) != 3:
        raise ValueError("three force and three moment components required")
    if not all(isfinite(x) for x in (*force_xyz_n, *moment_xyz_nmm)):
        raise ValueError("force and moment components must be finite")
    center = weld_centroid(side)
    sign = 1 if side == "right" else -1
    u = (sign / sqrt(2), 0, 1 / sqrt(2))
    v = (0, 1, 0)
    n = (-1 / sqrt(2), 0, sign / sqrt(2))
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    fu, fv, fn = (dot(force_xyz_n, e) for e in (u, v, n))
    mu, mv, mn = (dot(moment_xyz_nmm, e) for e in (u, v, n))
    a = WELD_LEG_MM / sqrt(2)
    area = a * LENGTH_MM
    iu = a * LENGTH_MM ** 3 / 12
    iv = LENGTH_MM * a ** 3 / 12
    polar = iu + iv
    corners = []
    for x in (-a / 2, a / 2):
        for y in (-LENGTH_MM / 2, LENGTH_MM / 2):
            normal = fn / area + mu * y / iu - mv * x / iv
            shear_u = fu / area - mn * y / polar
            shear_v = fv / area + mn * x / polar
            stress = sqrt(normal ** 2 + shear_u ** 2 + shear_v ** 2)
            corners.append({"u_mm": x, "v_mm": y,
                            "traction_uvn_mpa": [shear_u, shear_v, normal],
                            "resultant_mpa": stress,
                            "utilization_diagnostic": stress / ALLOWABLE_MPA})
    utilization = max(c["utilization_diagnostic"] for c in corners)
    return {
        "status": "conditional_elastic_diagnostic_only",
        "qualification_pass": False,
        "rotation_detail_gate": "unresolved_single_sided_root_bending",
        "moment_reference_global_mm": center,
        "weld_leg_mm": WELD_LEG_MM,
        "length_mm": LENGTH_MM,
        "throat_mm": a,
        "E70_required_FEXX_mpa": FEXX_MPA,
        "ASD_stress_limit_mpa": ALLOWABLE_MPA,
        "direct_force_diagnostic_n": area * ALLOWABLE_MPA,
        "pure_longitudinal_moment_diagnostic_nmm": ALLOWABLE_MPA * LENGTH_MM * a*a / 6,
        "required_leg_pure_longitudinal_moment_diagnostic_mm": sqrt(12 * abs(mv) / (ALLOWABLE_MPA * LENGTH_MM)),
        "utilization_diagnostic": utilization,
        "elastic_screen_pass": utilization <= 1 + 1e-12,
        "corners": corners,
        "sources": SOURCES,
        "limits": "Finite-throat elastic traction omits unfused-root notch/fracture, local yielding and prying compatibility; no directional strength increase. A larger leg alone does not resolve the rotation detail.",
    }
