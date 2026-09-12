"""Conservative, conditional NDS member check for the selected single 2x6 legs.

This calculation accepts leg compression as an input. It does not determine
frame force sharing, joint capacity, floor behavior, or a climber rating.
"""
import math

from fea.reinforced_timber_resistance import adjusted_reference, stability_factor


def leg_check(compression_n, *, effective_length_mm=1807.9717682704706,
              face_eccentricity_mm=19.05, additional_strong_moment_nmm=0.):
    """DF-L No.2, dry/unincised, CD=1, pin ends, no intermediate bracing.

    Use the entire longest stock dimension as the effective column length,
    exceeding the actual 1612.046 mm foot-to-bolt-centroid distance. Apply the
    weakest one-bore net section throughout the member, including its centroid
    shift, and retain the entire face eccentricity moment throughout its length.
    These are conservative member assumptions, not measured connection behavior.
    """
    if (not all(math.isfinite(v) for v in
                (compression_n, effective_length_mm, face_eccentricity_mm, additional_strong_moment_nmm))
            or compression_n < 0 or effective_length_mm <= 0
            or face_eccentricity_mm < 0 or additional_strong_moment_nmm < 0):
        raise ValueError('Require finite nonnegative compression/eccentricity and positive length')
    b, d, hole, offset = 38.1, 139.7, 11.1125, 20.4986542
    area = b*(d-hole)
    shift = -hole*offset/(d-hole)
    inertia = (b*d**3/12-b*hole**3/12-b*hole*offset**2-area*shift**2)
    ss, sw = inertia/(d/2+abs(shift)), (d-hole)*b*b/6
    ref = adjusted_reference(d)
    fce1 = .822*ref['Emin_mpa']/(effective_length_mm/d)**2
    fce2 = .822*ref['Emin_mpa']/(effective_length_mm/b)**2
    cp = stability_factor(min(fce1, fce2)/ref['Fc_star_mpa'], .8)
    # Deliberately long beam effective length; strong-axis bending is small.
    rb = math.sqrt(2*effective_length_mm*d/b**2)
    fbe = 1.2*ref['Emin_mpa']/rb**2
    cl = stability_factor(fbe/ref['Fb_star_mpa'], .95)
    weight_n = 5.713731175945755*9.80665
    transverse_weight_n = weight_n*.26015745792854417
    # Entire leg weight at midspan bounds the simply supported gravity moment.
    self_moment_nmm = transverse_weight_n*effective_length_mm/4
    fc = compression_n/area
    fb1 = (self_moment_nmm+compression_n*abs(shift)+additional_strong_moment_nmm)/ss
    fb2 = compression_n*face_eccentricity_mm/sw
    den1, den2 = 1-fc/fce1, 1-fc/fce2-(fb1/fbe)**2
    interaction = ((fc/(cp*ref['Fc_star_mpa']))**2
                   +fb1/(cl*ref['Fb_star_mpa']*den1)
                   +fb2/(ref['Fb_star_mpa']*den2)) if min(den1, den2) > 0 else None
    stability = fc/fce2+(fb1/fbe)**2
    slenderness = effective_length_mm/b
    return {
        'compression_n': compression_n, 'effective_length_mm': effective_length_mm,
        'face_eccentricity_mm': face_eccentricity_mm, 'net_area_mm2': area,
        'net_centroid_shift_mm': shift,
        'section_moduli_strong_weak_mm3': [ss, sw],
        'self_weight_n': weight_n, 'self_weight_moment_nmm': self_moment_nmm,
        'additional_strong_moment_nmm': additional_strong_moment_nmm,
        'Cp': cp, 'CL': cl, 'weak_axis_column_slenderness': slenderness,
        'NDS_3_9_3_interaction': interaction, 'NDS_3_9_4_stability': stability,
        'meets_member_criteria': (interaction is not None and interaction <= 1
                                  and stability <= 1 and slenderness <= 50 and rb <= 50),
        'scope': 'Conditional leg compression plus stated eccentricity; no connection or frame rating',
    }


def compression_limit(**kwargs):
    """Compression where the stated member criterion first reaches its limit."""
    low, high = 0., 100000.
    if not leg_check(low, **kwargs)['meets_member_criteria']:
        raise ValueError('Zero-load member does not meet the selected assumptions')
    for _ in range(70):
        mid = (low+high)/2
        if leg_check(mid, **kwargs)['meets_member_criteria']:
            low = mid
        else:
            high = mid
    return leg_check(low, **kwargs)
