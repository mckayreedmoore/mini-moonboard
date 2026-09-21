"""Catalog hardware and explicit local screens for the wider six-bolt leg joint.

No clamp-friction or composite action between loose washers is credited.
Catalog dimensions and project receipt requirements are kept distinct.
"""
import math

BOLT_LENGTH = 127.0
BOLT_LENGTH_SHORTFALL = 2.54
BOLT_DIAMETER = 12.7
THREAD_PITCH = 25.4 / 13
THREAD_REFERENCE = 31.75
TRANSITION_MAX = .385 * 25.4
STOCK_MIN, STOCK_MAX = 37.5, 38.5
PLATE_SIDE = 50.8
PLATE_HOLE = 14.2875
PLATE_THICKNESS = 4.7625
PLATE_MIN, PLATE_MAX = 4.5, 4.9  # Receipt requirements, not published tolerances.
WASHER_COUNT = 3
WASHER_OD_MIN, WASHER_OD_MAX = 1.057 * 25.4, 1.077 * 25.4
WASHER_ID_MIN, WASHER_ID_MAX = .526 * 25.4, .546 * 25.4
WASHER_MIN, WASHER_MAX = .156 * 25.4, .188 * 25.4
WASHER_THICKNESS = (WASHER_MIN + WASHER_MAX) / 2
NUT_HEIGHT_MAX = .454 * 25.4
HEX_AF_MAX = .750 * 25.4
HEX_CORNERS_MAX = .866 * 25.4
HEAD_HEIGHT_MAX = .323 * 25.4
HEAD_BEARING_MIN = .95 * .736 * 25.4
PSI = .006894757293168361
SOURCES = {
    'bolt': 'https://www.pecofasteners.com/details/item?itemid=12X5HBG5USSZ',
    'bolt_dimensions': 'https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf',
    'bolt_grade': 'https://www.portlandbolt.com/technical/specifications/sae-j429/',
    'nut': 'https://www.fmwfasteners.com/products/1-2-13-grade-5-finished-hex-nut-zinc-plated',
    'washer': 'https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/',
    'plate': 'https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf',
}


def dimensional_window(rim_mm=38.1, leg_mm=38.1):
    """Worst independent corners; five-pitch transition and short bolt retained."""
    if not all(math.isfinite(v) and STOCK_MIN <= v <= STOCK_MAX for v in (rim_mm, leg_mm)):
        raise ValueError('Stock must be within 37.5–38.5 mm')
    body = BOLT_LENGTH - BOLT_LENGTH_SHORTFALL - THREAD_REFERENCE - TRANSITION_MAX
    required = PLATE_MAX + rim_mm + leg_mm
    seat_min = rim_mm + leg_mm + 2 * PLATE_MIN + WASHER_COUNT * WASHER_MIN
    seat_max = rim_mm + leg_mm + 2 * PLATE_MAX + WASHER_COUNT * WASHER_MAX
    tip = BOLT_LENGTH - BOLT_LENGTH_SHORTFALL - seat_max - NUT_HEIGHT_MAX
    margins = {
        'smooth_body_margin_mm': body - required,
        'nut_seating_margin_mm': seat_min - (BOLT_LENGTH - THREAD_REFERENCE),
        'two_thread_margin_mm': tip - 2 * THREAD_PITCH,
    }
    return {'minimum_smooth_body_mm': body, 'required_smooth_body_mm': required,
            'minimum_nut_seat_mm': seat_min, 'maximum_nut_seat_mm': seat_max,
            'minimum_tip_projection_mm': tip, **margins,
            'dimensional_pass': min(margins.values()) >= 0}


def axial_couple_screen(points, load_xyz_n, *, eccentricity_mm=38.5, amplification=2.0):
    """Resolve the complete skew-group covariance, with explicit prying factor.

    load is force transmitted between member centroids; transverse x force is
    allocated equally. Positive and negative moment polarity are both returned.
    The amplification is an assessment assumption, not a proven contact bound.
    """
    if len(points) < 3 or len(load_xyz_n) != 3:
        raise ValueError('Require at least three points and a three-component force')
    values = [v for p in points for v in p] + list(load_xyz_n) + [eccentricity_mm, amplification]
    if not all(math.isfinite(v) for v in values) or amplification < 1 or eccentricity_mm < 0:
        raise ValueError('Invalid finite force, geometry or amplification')
    n = len(points)
    cy, cz = (sum(p[k] for p in points) / n for k in (1, 2))
    offsets = [(p[1] - cy, p[2] - cz) for p in points]
    yy = sum(y*y for y, z in offsets)
    yz = sum(y*z for y, z in offsets)
    zz = sum(z*z for y, z in offsets)
    det = yy*zz - yz*yz
    if det <= 1e-9:
        raise ValueError('Noncollinear group required')
    # r cross (T,0,0) = (0,z*T,-y*T); e_x cross F=(0,-e*Fz,e*Fy).
    sy, sz = -eccentricity_mm*load_xyz_n[1], -eccentricity_mm*load_xyz_n[2]
    a, b = (sy*zz-sz*yz)/det, (sz*yy-sy*yz)/det
    signed = [a*y+b*z for y, z in offsets]
    tension = [amplification*(abs(t)+abs(load_xyz_n[0])/n) for t in signed]
    return {'unamplified_signed_axial_n': signed, 'bolt_tension_envelope_n': tension,
            'peak_tension_n': max(tension), 'amplification_assumed': amplification,
            'target_couple_xyz_nmm': [0., sz, -sy],
            'contact_amplification_is_assumed': True}


def plate_screen(tension_n, *, yield_psi=33000., thickness_mm=PLATE_MIN):
    """Uniform wood pressure, radial cantilever wedges, longest square corner.

    Includes square corners rather than crediting only an inscribed circle.
    Circumferential plate action is ignored. Local rectangular-strip plastic
    resistance Fy*t²/4 uses Ωb=1.67; first-yield elastic stress is also reported.
    Minimum plate yield and thickness are explicit receipt requirements.
    """
    if not math.isfinite(tension_n) or tension_n < 0 or thickness_mm <= 0 or yield_psi <= 0:
        raise ValueError('Nonnegative load and positive material dimensions required')
    area = PLATE_SIDE**2 - math.pi*PLATE_HOLE**2/4
    pressure = tension_n/area
    a = HEAD_BEARING_MIN/2
    c = PLATE_SIDE/math.sqrt(2) - a
    m = pressure*(c*c/2+c**3/(3*a))
    plastic_reference = yield_psi*PSI*thickness_mm**2/(4*1.67)
    return {'wood_bearing_ratio': pressure/(625*PSI),
            'radial_strip_moment_nmm_per_mm': m,
            'plate_plastic_bending_ratio': m/plastic_reference,
            'plate_elastic_first_yield_ratio': 6*m/(thickness_mm**2*yield_psi*PSI),
            'required_yield_psi_for_plastic_check': 4*1.67*m/(thickness_mm**2*PSI),
            'plate_steel_yield_requirement_psi': yield_psi,
            'minimum_plate_thickness_mm': thickness_mm}


def bolt_combined_screen(lateral_n, tension_n, *, lateral_ratio=None):
    """Steel direct stress and retained dowel-bending yield under axial tension.

    Root area conservatively used for direct shear, tensile stress area for
    axial stress. Grade 5 Fy=92 ksi; compare von Mises with Fy/2. The independent
    NDS dowel calculation retains 45 ksi bending yield, below residual elastic
    yield after axial tension. If lateral_ratio is supplied, also impose the
    conservative linear sum of NDS lateral utilization and axial utilization
    against Fy/2. This additional assessment rule is not a product rating or
    a prescribed NDS combined-action equation.
    """
    if lateral_ratio is not None and (not math.isfinite(lateral_ratio) or lateral_ratio < 0):
        raise ValueError('Nonnegative finite lateral utilization required')
    if not all(math.isfinite(v) and v >= 0 for v in (lateral_n, tension_n)):
        raise ValueError('Nonnegative finite forces required')
    area_t = .1419*25.4**2
    area_root = math.pi*(.4056*25.4)**2/4
    sigma, tau = tension_n/area_t, lateral_n/area_root
    fy = 92000*PSI
    vm = math.sqrt(sigma*sigma+3*tau*tau)
    return {'axial_stress_mpa': sigma, 'direct_shear_stress_mpa': tau,
            'steel_direct_interaction_ratio': vm/(fy/2),
            'remaining_bending_yield_psi': (fy-sigma)/PSI,
            'nds_45000psi_bending_assumption_retained': fy-sigma >= 45000*PSI,
            'lateral_ratio_supplied': lateral_ratio,
            'linear_lateral_axial_interaction_ratio': (
                None if lateral_ratio is None else lateral_ratio + sigma/(fy/2)),
            'linear_interaction_is_additional_assessment_screen': True}


def washer_screen(tension_n):
    """Each loose MCX washer independently checked over the nut bearing circle.

    Entire force crosses every washer; no composite thickness. Use only a
    33 ksi yield receipt floor despite Grade 8/HRC38–45 product designation.
    """
    a = HEAD_BEARING_MIN/2
    c = WASHER_OD_MAX/2-a
    area = math.pi*(WASHER_OD_MIN**2-WASHER_ID_MAX**2)/4
    p = tension_n/area
    m = p*(c*c/2+c**3/(3*a))
    return {'single_washer_elastic_bending_ratio': 6*m/(WASHER_MIN**2*33000*PSI/1.67),
            'washers_act_compositely': False}
