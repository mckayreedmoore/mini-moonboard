"""Published references and explicit elastic analogies for current-frame response.

Constants follow CalculiX order E1,E2,E3,nu12,nu13,nu23,G12,G13,G23.
The panel layers are an equivalent section, not a claimed veneer schedule.
See docs/current-response-material-basis.md for sources and applicability.
"""
import json
import math
from pathlib import Path

import numpy as np

from mini_moonboard.selected_hardware import SDS25112, BoltSpec

LBF_N = 4.4482216152605
IN_MM = 25.4
WOOD_E = 1_600_000 * LBF_N / IN_MM**2
APA_EA = (3_150_000 * LBF_N / 304.8, 5_100_000 * LBF_N / 304.8)
APA_EI = (90_500 * LBF_N * IN_MM**2 / 304.8,
          320_000 * LBF_N * IN_MM**2 / 304.8)
APA_GA = 50_500 * LBF_N / IN_MM


def validate_constants(constants):
    """Check a reciprocal orthotropic compliance tensor is positive definite."""
    if len(constants) != 9 or not all(math.isfinite(v) for v in constants):
        raise ValueError('Require nine finite elastic constants')
    e1, e2, e3, n12, n13, n23, g12, g13, g23 = constants
    if min(e1, e2, e3, g12, g13, g23) <= 0:
        raise ValueError('Elastic moduli must be positive')
    compliance = np.diag([1/e1, 1/e2, 1/e3, 1/g12, 1/g13, 1/g23])
    compliance[0, 1] = compliance[1, 0] = -n12/e1
    compliance[0, 2] = compliance[2, 0] = -n13/e1
    compliance[1, 2] = compliance[2, 1] = -n23/e2
    if np.linalg.eigvalsh(compliance).min() <= 0:
        raise ValueError('Elastic compliance must be positive definite')
    return tuple(constants)


def df_l_no2_post_timber():
    """2024 Table 4D US DF-L No.2 Posts and Timbers; dry, unincised, CD=CF=1.

    Only longitudinal E comes from Table 4D. The other elastic constants retain
    the existing explicit FPL ratios, scaled to this timber's E. They remain
    response analogies, not measured properties of purchased stock.
    """
    psi = LBF_N / IN_MM**2
    e = 1_300_000 * psi
    return {
        'constants': validate_constants((e, .068*e, .05*e, .292, .449, .390,
                                        .064*e, .078*e, .007*e)),
        'reference_override': {
            'Fb_star_mpa': 750*psi, 'Ft_mpa': 475*psi, 'Fc_star_mpa': 700*psi,
            'Fv_mpa': 170*psi, 'Fc_perp_mpa': 625*psi, 'Emin_mpa': 470_000*psi},
        'specific_gravity': .50,
        'basis': '2024 NDS Supplement Table 4D, US DF-L No.2 Posts and Timbers; '
                 'dry unincised, CD=CF=1; FPL orthotropic ratios are an explicit analogy',
    }


def equivalent_layers(thickness_mm, ea=APA_EA, ei=APA_EI, ga=APA_GA):
    """Fit symmetric quarter/half/quarter layers to independent axial/bending EA/EI.

    Zero Poisson coupling is an explicit section idealization allowing an exact
    directional fit. E3 and out-of-plane shear use the FPL timber ratios as a
    declared proxy; APA EA/EI do not establish those panel properties.
    """
    if not math.isfinite(thickness_mm) or thickness_mm <= 0:
        raise ValueError('Require positive finite panel thickness')
    if len(ea) != 2 or len(ei) != 2:
        raise ValueError('Require two directional EA and EI values')
    if not all(math.isfinite(v) and v > 0 for v in (*ea, *ei, ga)):
        raise ValueError('Require positive finite section stiffnesses')
    outer, core = [], []
    for axial, bending in zip(ea, ei, strict=True):
        mean = axial/thickness_mm
        apparent = 12*bending/thickness_mm**3
        eo = (apparent-.25*mean)/.75
        ec = 2*mean-eo
        if min(eo, ec) <= 0:
            raise ValueError('Section cannot be fitted with positive quarter/half layers')
        outer.append(eo)
        core.append(ec)
    def constants(moduli):
        return validate_constants((*moduli, .05*WOOD_E, 0., 0., 0.,
                                   ga/thickness_mm, .007*WOOD_E, .007*WOOD_E))
    return [{'thickness_mm': thickness_mm/4, 'constants': constants(outer)},
            {'thickness_mm': thickness_mm/2, 'constants': constants(core)},
            {'thickness_mm': thickness_mm/4, 'constants': constants(outer)}]


def materials(panel_thickness_mm=18.25625, panel_group_factor=1.):
    """Return response references; x is sheet width and y assumed face-grain length.

    Group 1 is conditional; use 0.56 for the APA Group 4 stiffness comparison.
    Current CAD thickness is 18.25625 mm. APA targets remain the 23/32-category
    references; the equivalent layer fit retains their section stiffness.
    """
    if panel_group_factor not in (1., .83, .67, .56):
        raise ValueError('Use an APA Group 1, 2, 3 or 4 stiffness factor')
    ea = tuple(v*panel_group_factor for v in APA_EA)
    ei = tuple(v*panel_group_factor for v in APA_EI)
    ga = APA_GA*panel_group_factor
    layers = equivalent_layers(panel_thickness_mm, ea, ei, ga)
    timber = validate_constants((WOOD_E, .068*WOOD_E, .05*WOOD_E,
                                 .292, .449, .390, .064*WOOD_E,
                                 .078*WOOD_E, .007*WOOD_E))
    panel = validate_constants((ea[0]/panel_thickness_mm, ea[1]/panel_thickness_mm,
                                .05*WOOD_E, 0., 0., 0., ga/panel_thickness_mm,
                                .007*WOOD_E, .007*WOOD_E))
    return {'timber': timber, 'panel': panel, 'panel_layers': layers,
            'density_kg_per_mm3': 600.e-9,
            'panel_targets': {'ea_n_per_mm': ea, 'ei_nmm': ei,
                              'ga_n_per_mm': ga, 'thickness_mm': panel_thickness_mm},
            'panel_axis_assumption': 'x sheet width; y sheet length and assumed face grain',
            'panel_model_requirement': 'Use panel_layers; panel alone matches EA, not EI',
            'qualified_for_design': False}


def connection_stiffnesses(*, wood_density=500., panel_density=550.,
                          panel_thread_mm=None, sds_thread_mm=None,
                          scale=1.):
    """Directional analogies with explicit steel, threaded wood and seat compliance.

    Threads deduct a conservative 2D tip allowance, not a measured tip shape.
    Washer/head wood compression uses projected annular area without spreading
    through full member thickness. This is an elastic column idealization, not
    a tested seat law; washer/plate bending and countersink contact are omitted.
    """
    product = json.loads((Path(__file__).resolve().parents[1]/
                          'docs/round-panel-countersink-reference.json').read_text())['nominal']
    panel_d = product['major_thread_diameter_mm']
    panel_t = 18.25625
    panel_gross = product['overall_length_from_head_top_mm']-panel_t
    panel_effective = min(panel_gross, product['thread_length_including_tip_mm'])-2*panel_d
    sds_d = SDS25112.major_diameter_nominal_mm
    sds_effective = min(35.54476, SDS25112.thread_length_nominal_mm)-2*sds_d
    if panel_thread_mm is None:
        panel_thread_mm = panel_effective
    if sds_thread_mm is None:
        sds_thread_mm = sds_effective
    values = (wood_density, panel_density, panel_thread_mm, sds_thread_mm, scale)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError('Require positive finite density, engagement and scale')

    def area(outer, inner=0.):
        return math.pi*(outer**2-inner**2)/4

    def entry(d, density, components, basis, **metadata):
        axial = 1/sum(1/k for k in components.values())
        return {'lateral_n_per_mm': scale*density**1.5*d/23,
                'axial_n_per_mm': scale*axial, 'axial_basis': basis,
                'axial_series_components_n_per_mm': components,
                'qualified_for_design': False, **metadata}

    bolt = BoltSpec('Current 3/8-inch dimensional family', 127., 76.2, 0.)
    washer_area = area(bolt.washer_od_max_mm, bolt.washer_id_min_mm)
    panel_seat_area = area(product['head_diameter_mm'], panel_d)
    return {
        'panel': entry(panel_d, math.sqrt(wood_density*panel_density),
                       {'thread': 25*panel_d*panel_thread_mm,
                        'steel': 200_000*area(product['minor_thread_diameter_mm'])/
                                 product['overall_length_from_head_top_mm'],
                        'head_seat': .05*WOOD_E*panel_seat_area/panel_t},
                       'Threaded-softwood analogy + root-diameter steel + projected panel head seat in series',
                       effective_thread_mm=panel_thread_mm, head_seat_area_mm2=panel_seat_area),
        'sds': entry(sds_d, wood_density,
                     {'thread': 25*sds_d*sds_thread_mm,
                      'steel': 200_000*area(SDS25112.shank_diameter_nominal_mm)/
                               SDS25112.length_nominal_mm},
                     'Threaded-softwood analogy + shank-diameter steel in series; steel head/angle seat treated rigid',
                     effective_thread_mm=sds_thread_mm),
        'bolt': entry(bolt.diameter_nominal_mm, wood_density,
                      {'steel': 200_000*area(bolt.diameter_nominal_mm)/bolt.grip_mm,
                       'first_wood_seat': .05*WOOD_E*washer_area/38.1,
                       'second_wood_seat': .05*WOOD_E*washer_area/38.1},
                      'Steel + two transverse wood columns under modeled washer annuli; no pressure spreading',
                      washer_area_mm2=washer_area, wood_compression_length_mm=38.1),
    }
