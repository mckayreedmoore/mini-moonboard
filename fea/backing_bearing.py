"""Conditional washer/wood average-pressure arithmetic, not joint resistance."""
import math


def envelope(outer_diameter_mm, unsupported_diameter_mm, adjusted_fc_perp_mpa):
    """Require supplied adjusted wood stress; do not invent a material rating.

    Use the minimum washer OD and the larger of its ID and the actual unsupported
    wood opening. This assumes a fully supported, sufficiently stiff annulus.
    Washer bending, local wood failure, net section, prying and load interaction
    are not established by this calculation.
    """
    values = outer_diameter_mm, unsupported_diameter_mm, adjusted_fc_perp_mpa
    if (not all(math.isfinite(v) for v in values)
            or not 0 < unsupported_diameter_mm < outer_diameter_mm
            or adjusted_fc_perp_mpa <= 0):
        raise ValueError("Finite positive stress and ordered annular diameters required")
    area = math.pi/4*(outer_diameter_mm**2-unsupported_diameter_mm**2)
    return {"supported_annular_area_mm2": area,
            "pressure_at_1kn_mpa": 1000./area,
            "conditional_wood_bearing_force_n": area*adjusted_fc_perp_mpa,
            "adjusted_fc_perp_mpa": adjusted_fc_perp_mpa,
            "limits": "Uniform wood bearing only; NOT an assembled-joint allowable or approval"}
