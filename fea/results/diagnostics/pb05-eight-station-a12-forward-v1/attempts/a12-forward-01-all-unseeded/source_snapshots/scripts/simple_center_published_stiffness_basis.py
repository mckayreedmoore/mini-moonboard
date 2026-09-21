"""Published stiffness inputs and unresolved PB02 compliance terms.

This is a source-bounded sensitivity record, not a connection design or a
fabrication release. Active bolt grips come from the maintained PB02 geometry.
"""

import json
import math

from scripts import simple_center_current_stack_tip_screen as stack
from scripts.simple_center_pb02_geometry import (
    ACTIVE_FINGERPRINT,
    ACTIVE_TRIAL,
    active_geometry,
)

MM_PER_IN = 25.4
LBF_PER_N = 0.22480894387096
NOMINAL_BOLT_DIAMETER_IN = 0.25
NOMINAL_BOLT_DIAMETER_MM = 6.35
DIAGNOSTIC_BORE_DIAMETER_MM = 7.5
TYPICAL_ROOT_DIAMETER_SENSITIVITY_MM = 4.8006
STEEL_MODULUS_N_PER_MM2 = 205_000.0
DFL_RADIAL_TO_LONGITUDINAL_E_RATIO = 0.068
DFL_TANGENTIAL_TO_LONGITUDINAL_E_RATIO = 0.050

SOURCES = {
    "awc_2024_nds_errata": (
        "https://web-media.awc.org/wp-content/uploads/2025/03/"
        "31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf"
    ),
    "usda_fpl_wood_mechanical_fasteners": (
        "https://www.fpl.fs.usda.gov/documnts/pdf2016/fpl_2016_rammer001P.pdf"
    ),
    "usda_fpl_wood_handbook_chapter_5": (
        "https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/"
        "chapter_05_fpl_gtr282.pdf"
    ),
    "journal_bolted_joint_axial_series_model": (
        "https://link.springer.com/article/10.1186/s10086-022-02038-1"
    ),
    "journal_washer_embedment_model_limits": (
        "https://link.springer.com/article/10.1186/s10086-021-01973-9"
    ),
}


def _active_grips_mm():
    """Read ten bolt grips from the shared active geometry and stack pairing."""
    _, bores, ends = active_geometry()
    if set(bores) != set(stack.PAIRS):
        raise ValueError("active PB02 bore inventory changed")
    grips = {}
    for name, pair in stack.PAIRS.items():
        near, far = (ends[end][0] for end in pair)
        grip = sum(abs(first - second) for first, second in zip(near, far, strict=True))
        if not math.isfinite(grip) or grip <= 0:
            raise ValueError(f"invalid active PB02 grip for {name}: {grip}")
        grips[name] = grip
    if len(grips) != 10:
        raise ValueError(f"expected ten active PB02 grips, found {len(grips)}")
    return grips


def _nds_lateral_basis():
    gamma_lb_per_in = 180_000 * NOMINAL_BOLT_DIAMETER_IN**1.5
    gamma_n_per_mm = gamma_lb_per_in / LBF_PER_N / MM_PER_IN
    return {
        "edition": "2024 NDS with 2025-03-28 errata/addenda",
        "connection_type": "wood-to-wood dowel-type connection",
        "formula": "gamma = 180000 * D^1.5 lb/in",
        "diameter_D_in": NOMINAL_BOLT_DIAMETER_IN,
        "gamma_lb_per_in": gamma_lb_per_in,
        "gamma_n_per_mm": gamma_n_per_mm,
        "source_url": SOURCES["awc_2024_nds_errata"],
        "basis": (
            "NDS 11.3.6.1 load/slip modulus used in the group-action-factor "
            "calculation for wood-to-wood dowel-type connections."
        ),
        "semantics": (
            "Single-bolt, single-shear-plane sensitivity for PB02; do not "
            "multiply by contact-sample count."
        ),
        "applicability_limits": [
            "The NDS normative role is the group-action calculation, not a general 3D spring law.",
            "Fastener fit, hole clearance, moisture, load level, and cyclic behavior are separate.",
            "This value is not a strength, capacity, or complete-joint stiffness.",
        ],
    }


def _ec5_lateral_basis():
    rows = []
    for density in (460.0, 480.0, 500.0, 520.0):
        stiffness = density**1.5 * NOMINAL_BOLT_DIAMETER_MM / 23
        rows.append(
            {
                "rho_mean_kg_per_m3": density,
                "kser_n_per_mm_per_bolt_per_shear_plane": stiffness,
            }
        )
    return {
        "formula": "Kser = rho_mean^1.5 * d / 23",
        "diameter_d_mm": NOMINAL_BOLT_DIAMETER_MM,
        "density_sensitivities": rows,
        "source_url": SOURCES["usda_fpl_wood_mechanical_fasteners"],
        "basis": (
            "USDA/FPL reproduces the Eurocode 5 service slip-modulus equation "
            "for predrilled dowel-type fasteners such as bolts."
        ),
        "semantics": "Per fastener per shear plane at service-level loading.",
        "applicability_limits": [
            "The source describes the service region as approximately 40% of maximum load.",
            "rho_mean is mean density at approximately 12% moisture, not NDS assigned specific gravity.",
            "Hole tolerance or clearance must be added to total joint deformation.",
            "The density values are sensitivities, not measurements of delivered PB02 lumber.",
        ],
    }


def _clearance_sensitivity():
    diametral = DIAGNOSTIC_BORE_DIAMETER_MM - NOMINAL_BOLT_DIAMETER_MM
    return {
        "diagnostic_bore_diameter_mm": DIAGNOSTIC_BORE_DIAMETER_MM,
        "nominal_bolt_diameter_mm": NOMINAL_BOLT_DIAMETER_MM,
        "diametral_difference_mm": diametral,
        "one_sided_geometric_dead_zone_mm": diametral / 2,
        "interpretation": (
            "Ideal centered radial travel before shaft-to-bore contact; actual "
            "directional slack depends on initial bolt position and tolerances."
        ),
        "is_drill_size": False,
        "is_selected_clearance": False,
        "design_input_qualified": False,
    }


def _steel_only_axial_sensitivities():
    grips = _active_grips_mm()
    diameters = {
        "nominal_6_35mm_full_shank_area": NOMINAL_BOLT_DIAMETER_MM,
        "typical_root_4_8006mm_diameter_sensitivity": (
            TYPICAL_ROOT_DIAMETER_SENSITIVITY_MM
        ),
    }
    areas = {label: math.pi * diameter**2 / 4 for label, diameter in diameters.items()}
    rows = []
    for name, grip in grips.items():
        rows.append(
            {
                "bolt": name,
                "active_wood_grip_mm": grip,
                "steel_only_ea_over_l_n_per_mm": {
                    label: STEEL_MODULUS_N_PER_MM2 * area / grip
                    for label, area in areas.items()
                },
            }
        )
    return {
        "formula": "K_bolt,steel-only = E_steel * A / L",
        "steel_modulus_n_per_mm2": STEEL_MODULUS_N_PER_MM2,
        "area_models_mm2": areas,
        "active_geometry_variant": ACTIVE_TRIAL.variant_id,
        "active_geometry_fingerprint": ACTIVE_FINGERPRINT,
        "grip_source": (
            "active_geometry() end planes paired by "
            "simple_center_current_stack_tip_screen.PAIRS"
        ),
        "rows": rows,
        "source_url": SOURCES["journal_bolted_joint_axial_series_model"],
        "applicability_limits": [
            "These are steel-only EA/L sensitivities, not complete joint axial stiffnesses.",
            "L is the active wood grip, used only as a transparent length sensitivity.",
            "The 4.8006 mm diameter is a named typical-root sensitivity, not verified purchased-bolt geometry.",
            "Thread engagement, thread play, head, nut, washers, preload, and member compliance are excluded.",
        ],
    }


def _uncomputed_compliance_templates():
    return {
        "washer_seat_and_axial_joint": {
            "series_formula": (
                "1/K_axial_joint = 1/K_bolt + 1/K_washer_seat_1 + "
                "1/K_washer_seat_2 + sum(other_compliances)"
            ),
            "required_inputs": [
                "verified purchased-bolt shank, thread, engagement, and free-length geometry",
                "applicable threaded tensile-stress area and steel modulus",
                "washer inside/outside diameter, thickness, material, and bending rigidity",
                "wood radial/tangential orientation and properties beneath each washer",
                "preload or snug-tight condition, gaps, seating, moisture, and load level",
                "member compliance included in the selected axial load path",
            ],
            "washer_embedment_source_url": SOURCES[
                "journal_washer_embedment_model_limits"
            ],
            "computed": False,
            "qualified": False,
            "value_n_per_mm": None,
        },
        "wood_face_contact": {
            "elastic_formula": "K_face,total = E_normal * A_active / L_effective",
            "sample_formula": "K_contact_sample = K_face,total / sample_count",
            "dfl_elastic_ratios": {
                "radial_E_R_over_E_L": DFL_RADIAL_TO_LONGITUDINAL_E_RATIO,
                "tangential_E_T_over_E_L": (DFL_TANGENTIAL_TO_LONGITUDINAL_E_RATIO),
            },
            "required_inputs": [
                "applicable longitudinal modulus E_L for the actual lumber state",
                "contact-face normal relative to grain and annual-ring orientation",
                "actual active contact area A_active for the load state",
                "justified effective compression depth L_effective",
                "surface seating, initial gaps, moisture, creep, and load level",
                "contact sampling count without multiplying total physical face stiffness",
            ],
            "effective_depth_mm": None,
            "source_url": SOURCES["usda_fpl_wood_handbook_chapter_5"],
            "computed": False,
            "qualified": False,
            "value_n_per_mm": None,
        },
    }


def _validate_finite_values(value, path="root"):
    if isinstance(value, dict):
        for key, nested in value.items():
            _validate_finite_values(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _validate_finite_values(nested, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite output at {path}: {value}")


def report():
    """Return the bounded published-basis record for the active PB02 stack."""
    result = {
        "schema": "simple_center_published_stiffness_basis/v1",
        "lateral_bolt_slip": {
            "nds_2024": _nds_lateral_basis(),
            "ec5_service": _ec5_lateral_basis(),
        },
        "diagnostic_bore_clearance_sensitivity": _clearance_sensitivity(),
        "steel_only_bolt_axial_sensitivities": _steel_only_axial_sensitivities(),
        "uncomputed_compliance_templates": _uncomputed_compliance_templates(),
        "status": {
            "lateral_values_are_published_sensitivities_not_selected_properties": True,
            "axial_joint_stiffness_unqualified_and_uncomputed": True,
            "face_contact_stiffness_unqualified_and_uncomputed": True,
            "design_release": False,
            "fabrication_release": False,
            "drilling_release": False,
        },
    }
    _validate_finite_values(result)
    return result


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
