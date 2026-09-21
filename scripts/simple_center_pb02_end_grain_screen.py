"""Conditional PB02 block/header end-grain single-bolt yield screen."""

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
)

MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605


def root_case(root_diameter_in: float) -> dict:
    """Apply the 2024 NDS axis-parallel main-member and end-grain route.

    This is a conditional single-fastener component calculation. It does not
    qualify group action, geometry factors, splitting, hardware, or the joint.
    """
    grain_angle_factor = 1.25
    reduction = (10 * root_diameter_in + 0.5) * grain_angle_factor
    bearing_psi = dfl_dowel_bearing_psi(root_diameter_in, 90)
    yield_moment = dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=45_000,
        effective_diameter_in=root_diameter_in,
    )
    result = single_shear(
        main_length_in=143.9 / 25.4,
        side_length_in=1.5,
        main_bearing_lb_in=bearing_psi * root_diameter_in,
        side_bearing_lb_in=bearing_psi * root_diameter_in,
        main_yield_moment_lb_in=yield_moment,
        side_yield_moment_lb_in=yield_moment,
        gap_in=0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )
    end_grain_factor = 0.67
    adjusted_n = result["reference_lateral_lbf"] * end_grain_factor * N_PER_LBF
    demand_n = 33.71
    return {
        "root_diameter_in": root_diameter_in,
        "dfl_specific_gravity": 0.5,
        "bearing_psi": bearing_psi,
        "bolt_bending_yield_strength_psi": 45_000,
        "yield_moment_lb_in": yield_moment,
        "reduction_term": reduction,
        "governing_mode": result["governing_mode"],
        "reference_lateral_lbf": result["reference_lateral_lbf"],
        "end_grain_factor": end_grain_factor,
        "end_grain_adjusted_reference_n": adjusted_n,
        "single_case_demand_n": demand_n,
        "demand_ratio": demand_n / adjusted_n,
        "minimum_remaining_adjustment_product": demand_n / adjusted_n,
        "limits": (
            "Conditional 2024 NDS single-bolt yield reference only; Ceg applied, "
            "CD=CM=Ct=Cdi=Ctn=1 assumed, Cg and CDelta unresolved; no group, "
            "splitting, local-ligament, hardware, joint, or drilling qualification"
        ),
    }


def screen() -> dict:
    return {
        "candidate": "pb02-kerf-right-native-development-only",
        "interface": "block_header",
        "disposition": "retain_current_z_grain_block_for_development",
        "cases": {
            "typical_root": root_case(0.189),
            "smaller_root_sensitivity": root_case(0.180),
        },
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2, sort_keys=True))
