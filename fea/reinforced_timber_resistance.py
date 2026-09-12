"""2024 NDS conditional member checks against supplied current section actions.

Native demand validity, local opening resistance and end/contact load transfer
are separate gates. No section-stress result releases the physical assembly.
"""
import math

PSI_MPA = 0.006894757293168361
PRIMARY_PDF_SHA256 = {
    'AWC_TR12': '95abb7d382aadf6984121f8731a5b91c2b633516e7f134991ad0a34a1b916be2',
    'NDS2024_errata': '2ecba75d6603994cafca68fbb049d0b9ff00f5e9df8dd0783e5150c3ca6460d8',
    'CDE_SAE_washers': '080131ef1b8ff5cab0e9d40ae6617a90db62f57eb3a48ad6659c5a49e5239d8f',
    'NDS2024_ch3': '205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644',
    'NDS2024_supplement_ch4': '1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b',
    'NDS2024_ch12': '5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a',
    'NDS2024_appendix': '99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7',
}
SIZE_FACTORS = {139.7: (1.3, 1.3, 1.1), 184.15: (1.2, 1.2, 1.05),
                234.95: (1.1, 1.1, 1.), 285.75: (1., 1., 1.)}


def adjusted_reference(depth_mm):
    """US DF-L No.2 dry unincised, CD=1; no repetitive/flat-use increases."""
    stock = next((d for d in SIZE_FACTORS if abs(d-depth_mm) < 1.e-3), None)
    if stock is None:
        raise ValueError('Require an enumerated nominal 2x stock depth')
    cb, ct, cc = SIZE_FACTORS[stock]
    return {'Fb_star_mpa': 900*cb*PSI_MPA, 'Ft_mpa': 575*ct*PSI_MPA,
            'Fc_star_mpa': 1350*cc*PSI_MPA, 'Fv_mpa': 180*PSI_MPA,
            'Fc_perp_mpa': 625*PSI_MPA, 'Emin_mpa': 580000*PSI_MPA}


def stability_factor(ratio, c):
    """Rationalized NDS smaller root, used for Cp(c=.8) and CL(c=.95)."""
    if not math.isfinite(ratio) or ratio <= 0 or not 0 < c < 1:
        raise ValueError('Require positive finite stability ratio and 0<c<1')
    return 2*ratio/(1+ratio+math.sqrt((1+ratio)**2-4*c*ratio))


def member_check(*, width_mm, depth_mm, axial_n, moment_strong_nmm,
                 moment_weak_nmm, shear_strong_n, shear_weak_n, torsion_nmm,
                 column_effective_strong_mm, column_effective_weak_mm,
                 beam_effective_mm, centered_hole_diameter_mm=0.):
    """Strong dimension is depth; effective lengths must be externally justified.

    Gross rectangular stability equations combined with conservatively increased
    net-section stress provide a conditional screen, not hole qualification.
    The optional centered transverse hole removes a full-width rectangular strip.
    """
    values = (width_mm, depth_mm, axial_n, moment_strong_nmm, moment_weak_nmm,
              shear_strong_n, shear_weak_n, torsion_nmm, column_effective_strong_mm,
              column_effective_weak_mm, beam_effective_mm, centered_hole_diameter_mm)
    if (not all(math.isfinite(v) for v in values)
            or min(width_mm, depth_mm, column_effective_strong_mm,
                   column_effective_weak_mm, beam_effective_mm) <= 0
            or width_mm > depth_mm or not 0 <= centered_hole_diameter_mm < depth_mm):
        raise ValueError('Require finite actions, positive effective lengths and strong depth')
    b, d, hole = width_mm, depth_mm, centered_hole_diameter_mm
    ref = adjusted_reference(d)
    area = b*(d-hole)
    ss = b*(d**3-hole**3)/(6*d)
    sw = (d-hole)*b*b/6
    fc, ft = max(0., -axial_n)/area, max(0., axial_n)/area
    fb1, fb2 = abs(moment_strong_nmm)/ss, abs(moment_weak_nmm)/sw
    slender1, slender2 = column_effective_strong_mm/d, column_effective_weak_mm/b
    fce1, fce2 = (.822*ref['Emin_mpa']/v**2 for v in (slender1, slender2))
    cp = stability_factor(min(fce1, fce2)/ref['Fc_star_mpa'], .8)
    rb = math.sqrt(beam_effective_mm*d/b**2)
    fbe = 1.2*ref['Emin_mpa']/rb**2
    cl = stability_factor(fbe/ref['Fb_star_mpa'], .95)
    fbprime, fcprime = ref['Fb_star_mpa']*cl, ref['Fc_star_mpa']*cp
    denominator1 = 1-fc/fce1
    denominator2 = 1-fc/fce2-(fb1/fbe)**2
    euler_conditions = denominator1 > 0 and denominator2 > 0
    compression_interaction = None
    if euler_conditions:
        compression_interaction = ((fc/fcprime)**2+fb1/(fbprime*denominator1)
                                   +fb2/(ref['Fb_star_mpa']*denominator2))
    lateral_stability_interaction = fc/fce2+(fb1/fbe)**2
    # For axial tension retain a conservative no-relief bending check as well.
    tension_interaction = ft/ref['Ft_mpa']+(fb1+fb2)/ref['Fb_star_mpa']
    max_average_shear = math.hypot(shear_strong_n, shear_weak_n)/area
    gross_rectangular_shear = 1.5*math.hypot(shear_strong_n, shear_weak_n)/(b*d)
    slenderness_ok = rb <= 50 and (fc == 0 or max(slender1, slender2) <= 50)
    applicable_ratios = [lateral_stability_interaction, tension_interaction]
    if compression_interaction is not None:
        applicable_ratios.append(compression_interaction)
    # Bored sections have no assumed parabolic shear distribution across a void.
    shear_ratio = ((max_average_shear if hole else gross_rectangular_shear)/ref['Fv_mpa'])
    applicable_ratios.append(shear_ratio)
    return {'references': ref, 'net_area_mm2': area,
            'section_moduli_strong_weak_mm3': [ss, sw],
            'stress_mpa': {'compression': fc, 'tension': ft, 'bending_strong': fb1,
                          'bending_weak': fb2, 'net_average_resultant_shear': max_average_shear,
                          'gross_rectangular_resultant_shear': gross_rectangular_shear},
            'column_slenderness_strong_weak': [slender1, slender2], 'beam_slenderness': rb,
            'Cp': cp, 'CL': cl, 'FcE_strong_weak_mpa': [fce1, fce2], 'FbE_mpa': fbe,
            'adjusted_Fc_mpa': fcprime, 'adjusted_Fb_strong_mpa': fbprime,
            'compression_biaxial_interaction_NDS_3_9_3': compression_interaction,
            'stability_interaction_NDS_3_9_4': lateral_stability_interaction,
            'necessary_compression_interaction_even_if_fully_braced':
                (fc/ref['Fc_star_mpa'])**2+(fb1+fb2)/ref['Fb_star_mpa'],
            'tension_conservative_interaction': tension_interaction,
            'shear_ratio': shear_ratio,
            'shear_scope': 'Necessary average-only test; local hole shear unresolved' if hole else
                           'Conservative sum-vector magnitude of gross rectangular shear components',
            'within_slenderness_limits': slenderness_ok,
            'Euler_denominators_positive': euler_conditions,
            'conditional_checked_failure': not slenderness_ok or not euler_conditions
                                           or max(applicable_ratios) > 1.+1.e-9,
            'torsion_demand_nmm': torsion_nmm,
            'torsion_resistance_evaluated': False,
            'local_opening_resistance_evaluated': hole == 0.,
            'qualified_for_design': False}


def bearing_check(force_n, net_area_mm2, angle_to_grain_deg, depth_mm):
    """NDS3.10-1 Hankinson bearing, Cb=1, no strength gain from partial contact."""
    if (not all(math.isfinite(v) for v in (force_n, net_area_mm2, angle_to_grain_deg))
            or force_n < 0 or net_area_mm2 <= 0 or not 0 <= angle_to_grain_deg <= 90):
        raise ValueError('Require compressive force, positive net bearing area and angle0..90')
    ref = adjusted_reference(depth_mm)
    theta = math.radians(angle_to_grain_deg)
    parallel, perpendicular = ref['Fc_star_mpa'], ref['Fc_perp_mpa']
    strength = parallel*perpendicular/(parallel*math.sin(theta)**2+perpendicular*math.cos(theta)**2)
    return {'adjusted_bearing_mpa': strength, 'bearing_ratio': force_n/net_area_mm2/strength,
            'net_area_mm2': net_area_mm2, 'actual_contact_distribution_qualified': False}


def cross_grain_group_check(outermost_spacing_mm, special_shrinkage_detail=False):
    """NDS12.5.1.3 five-inch maximum for dowels D>=1/4inch in sawn wood."""
    if not math.isfinite(outermost_spacing_mm) or outermost_spacing_mm < 0:
        raise ValueError('Require finite nonnegative row spread')
    return {'outermost_cross_grain_mm': outermost_spacing_mm,
            'limit_mm_without_special_detail': 127.,
            'special_shrinkage_detail_provided': special_shrinkage_detail,
            'passed': outermost_spacing_mm <= 127. or special_shrinkage_detail}


def boring_limit(measured_depth_mm, centering_error_mm=.5):
    """Two 50.8 mm residual ligaments; actual finished hole, not bit label."""
    if measured_depth_mm <= 101.6 or centering_error_mm < 0:
        raise ValueError('Require measured depth above101.6mm and nonnegative error')
    return measured_depth_mm-101.6-2*centering_error_mm


def group_factor(n, spacing_in, main_ea_lbf, side_ea_lbf, steel_side=False):
    """NDS11.3-1 with January2025 corrected D**1.5; nominal D=.375in."""
    if n < 1 or int(n) != n or min(spacing_in, main_ea_lbf, side_ea_lbf) <= 0:
        raise ValueError('Require positive row count, spacing and EA')
    if n == 1:
        return 1.
    re = min(main_ea_lbf/side_ea_lbf, side_ea_lbf/main_ea_lbf)
    gamma = (270000 if steel_side else 180000)*.375**1.5
    u = 1+gamma*spacing_in/2*(1/main_ea_lbf+1/side_ea_lbf)
    m = 1/(u+math.sqrt(u*u-1))
    return (m*(1-m**(2*n))/(n*((1+re*m**n)*(1+m)-1+m**(2*n)))
            *(1+re)/(1-m))


def conditional_dowel_reference(steel_side=False, main_fe_psi=3650., side_fe_psi=None):
    """Deliberately weak bearing envelope, root diameter throughout, Fyb45ksi.

    Requires certified SAEJ429Grade1 or independently established Fyb>=45ksi.
    Steel bearing Fe87000psi follows NDS2024 Table12B footnote2 for A36. Opposite bearing plate is not credited as a second shear plane.
    """
    from fea.dowel_yield import single_shear
    root = .298
    if side_fe_psi is None:
        side_fe_psi = 87000. if steel_side else 3650.
    values = single_shear(main_length_in=1.5, side_length_in=.375 if steel_side else 1.5,
        main_bearing_lb_in=main_fe_psi*root, side_bearing_lb_in=side_fe_psi*root,
        main_yield_moment_lb_in=45000*root**3/6,
        side_yield_moment_lb_in=45000*root**3/6, gap_in=0.,
        reduction_terms={'Im': 5., 'Is': 5., 'II': 4.5, 'IIIm': 4., 'IIIs': 4., 'IV': 4.})
    ea_wood = 1600000*1.5*5.5
    # Four-fastener row bound and larger actual pitch deliberately penalize
    # these two-by-two groups; not an assertion of equal actual bolt force.
    cg = group_factor(4, 130/25.4 if steel_side else 70/25.4, ea_wood,
                      29000000*.375*(32/25.4) if steel_side else ea_wood, steel_side)
    return {'reference_lateral_n': values['reference_lateral_lbf']*4.4482216152605,
            'conservative_group_factor': cg,
            'adjusted_lateral_n': values['reference_lateral_lbf']*4.4482216152605*cg,
            'yield_mode': values['governing_mode'], 'root_diameter_in': root,
            'conditional_Fyb_psi': 45000., 'bearing_strengths_main_side_psi': [main_fe_psi, side_fe_psi],
            'steel_Fe_psi': 87000 if steel_side else None, 'actual_grade_verified': False, 'CD': 1., 'CM': 1., 'Ct': 1., 'Cdelta': 1.}


def effective_beam_length(length_mm, depth_mm):
    """NDS Table3.3.3 unspecified loading; endpoints assumed adequate restraints."""
    ratio = length_mm/depth_mm
    return (2.06*length_mm if ratio < 7 else 1.63*length_mm+3*depth_mm
            if ratio <= 14.3 else 1.84*length_mm)


def section_report(native_report, bored_members=None):
    """Read current member wrench schema; full-length pin-end bracing sensitivity.

    Width follows section_u, depth section_v in the native rectangular kernel.
    Thus moment about u is strong-axis bending when depth>=width.
    """
    results = {}
    bored_members = bored_members or {}
    for name, data in native_report['member_section_demands'].items():
        member = data['member']
        width, depth = member['width_mm'], member['depth_mm']
        swapped = width > depth
        width, depth = min(width, depth), max(width, depth)
        length = data['length_mm']-data['section_valid_from_mm']
        rows = []
        for section in data['sections']:
            check = member_check(width_mm=width, depth_mm=depth,
                axial_n=section['axial_n_tension_positive'],
                moment_strong_nmm=section['moment_v_nmm' if swapped else 'moment_u_nmm'],
                moment_weak_nmm=section['moment_u_nmm' if swapped else 'moment_v_nmm'],
                shear_strong_n=section['shear_u_n' if swapped else 'shear_v_n'],
                shear_weak_n=section['shear_v_n' if swapped else 'shear_u_n'],
                torsion_nmm=section['torsion_nmm'], column_effective_strong_mm=length,
                column_effective_weak_mm=length,
                beam_effective_mm=effective_beam_length(length, depth),
                centered_hole_diameter_mm=bored_members.get(name, 0.))
            rows.append({'station_along_grain_mm': section['station_along_grain_mm'],
                         'include_station_loads': section['include_station_loads'], **check})
        results[name] = {'unsupported_length_assumed_mm': length, 'checks': rows,
                         'any_conditional_failure': any(r['conditional_checked_failure'] for r in rows),
                         'force_residual_n': data['force_residual_n'],
                         'moment_residual_nmm': data['moment_residual_nmm']}
    return results


def connection_report(native_report):
    """Each same-case bolt vector, no division of total load by bolt count."""
    results = {}
    for name, force in native_report['physical_connection_forces'].items():
        if not name.startswith(('lumber_leg_bolt_', 'steel_shoe_')):
            continue
        steel = name.startswith('steel_shoe_')
        vector = force['force_on_first_xyz_n']
        if steel:
            ref = conditional_dowel_reference(True)
        else:
            grains = [(0., .6427876096865427, .7660444431189752),
                      (0., -.26015745792854417, .9655662054381139)]
            bearing = []
            for grain in grains:
                lateral2 = vector[1]**2+vector[2]**2
                cosine2 = min(1., sum(a*b for a, b in zip(vector, grain, strict=True))**2/lateral2) if lateral2 else 0.
                bearing.append(5600*3650/(5600*(1-cosine2)+3650*cosine2))
            ref = conditional_dowel_reference(False, *bearing)
        # One actual wood-contact footprint on each side. A washer pair does
        # not double the footprint; pressure from tightening is not included.
        area = (32**2-math.pi*11.1125**2/4 if steel else
                math.pi*((.805*25.4)**2-max(.419*25.4, 11.1125)**2)/4)
        axial = abs(force['axial_along_installation_direction_n'])
        bearing = bearing_check(axial, area, 90., 234.95 if '_header_' in name else 139.7)
        lateral_ratio = force['transverse_shear_n']/ref['adjusted_lateral_n']
        results[name] = {'same_case_force_xyz_n': force['force_on_first_xyz_n'],
                         'lateral_demand_n': force['transverse_shear_n'],
                         'axial_increment_abs_n': axial, 'reference': ref,
                         'lateral_ratio': lateral_ratio, 'wood_bearing': bearing,
                         'conditional_checked_failure': max(lateral_ratio, bearing['bearing_ratio']) > 1.,
                         'tightening_preload_included': False,
                         'footprint_basis': '32mm plate minus11.1125mm wood bore' if steel else
                             'CDE minimumOD.805in minus max(maximumID.419in, wood bore11.1125mm)',
                         'qualified_for_design': False}
    return results


def geometry_report():
    """Actual current raw-stock ray intersections at each bolt axis."""
    import cadquery as cq

    from mini_moonboard import lumber_leg_frame
    from mini_moonboard import round_reinforcement_frame as model
    from mini_moonboard.connection_geometry import material_intervals
    raw = {p.name: p.shape for p in model.uncut_wood_parts()}
    slope = (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized()
    leg = lumber_leg_frame.geometry('2x6', 0.)[2]
    rim_zmin = {name: raw[name].BoundingBox().zmin for name in ('base_side_left', 'base_side_right')}
    if any(abs(z-234.525) > 1.e-5 for z in rim_zmin.values()):
        raise ValueError('Frozen shoe-trimmed rim geometry changed')
    header_ys = [c.start.y for c in model.connections() if c.name.startswith('steel_shoe_header_')]
    header_spread = max(header_ys)-min(header_ys)
    result = []
    for bolt in model.connections():
        if bolt.kind != 'bolt':
            continue
        for name in bolt.members:
            if name not in raw:
                continue
            shape = raw[name]
            grain = leg if name.startswith('lumber_leg') else cq.Vector(1, 0, 0) if name == 'base_header' else slope
            cross = bolt.direction.cross(grain).normalized()
            point = bolt.start+bolt.direction*(shape.Center()-bolt.start).dot(bolt.direction)
            ends = material_intervals(shape, point, grain, -5000, 5000)
            edges = material_intervals(shape, point, cross, -5000, 5000)
            containing = lambda intervals: next((a, b) for a, b in intervals if a <= 0 <= b)
            amin, amax = containing(ends)
            emin, emax = containing(edges)
            result.append({'bolt': bolt.name, 'member': name, 'grain': list(grain.toTuple()),
                           'end_distances_mm': [-amin, amax], 'edge_distances_mm': [-emin, emax],
                           'minimum_end_7D_pass': min(-amin, amax) >= 7*bolt.diameter,
                           'minimum_edge_4D_pass': min(-emin, emax) >= 4*bolt.diameter})
    return {'bolt_member_distances': result, 'actual_trimmed_rim_zmin_mm': rim_zmin,
            'header_cross_grain_group': cross_grain_group_check(header_spread),
            'nominal_centered_38_1_bore_ligament_mm': (139.7-38.1)/2,
            'boring_rule': 'Actual finished D <= measured stock depth -101.6 -2*maximum centering error',
            'nominal_depth_with_half_mm_centering_max_actual_bore_mm': boring_limit(139.7),
            'hole_local_stress_qualified': False}


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    from fea.reinforcement_review import sources
    files = list(sources())+[Path(__file__), Path('fea/dowel_yield.py')]
    hashes = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}
    from mini_moonboard import round_reinforcement_frame as model
    bored = {row['member']: row['diameter_mm'] for row in model.bore_records()}
    reports = []
    for path in args.native:
        raw = path.read_bytes()
        native = json.loads(raw)
        if native.get('candidate') != 'round-reinforcement-development':
            raise ValueError('Require current candidate native demands')
        cad_hashes = {p: digest for p, digest in native.get('source_sha256', {}).items()
                      if p.startswith('mini_moonboard/')}
        if 'mini_moonboard/round_reinforcement_frame.py' not in cad_hashes:
            raise ValueError('Missing native current-CAD source provenance')
        changed = [p for p, digest in cad_hashes.items()
                   if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
        if changed:
            raise ValueError('Native geometry source mismatch: '+', '.join(changed))
        reports.append({'native_geometry_source_match': True, 'native_path': str(path), 'native_sha256': hashlib.sha256(raw).hexdigest(),
                        'native_numerical_gates': {k: native.get(k) for k in
                            ('global_equilibrium_passed', 'mpc_check_passed',
                             'contact_active_set_converged', 'closed_bearing_assumption_passed')},
                        'members': section_report(native),
                        'bored_member_conservative_net_section_sensitivity': section_report(native, bored),
                        'connections': connection_report(native),
                        'bolt_local_parallel_grain_checks': local_group_report(native)})
    result = {'candidate': 'round-reinforcement-development', 'source_sha256': hashes,
              'primary_pdf_sha256': PRIMARY_PDF_SHA256,
              'geometry': geometry_report(), 'native_cases': reports,
              'conditional_bolt_references': {k: conditional_dowel_reference(v) for k, v in
                                               [('leg_wood_wood', False), ('shoe_steel_wood', True)]},
              'qualified_for_design': False}
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest for p, digest in hashes.items()):
        raise RuntimeError('Source changed during analysis')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


def local_group_report(native):
    """NDS nonmandatory AppendixE parallel-grain net/row/group tear-out.

    Each actual row demand is bounded above by sum(abs(each parallel force))
    across all four bolts. Compare that conservative total to ONE row capacity,
    without equal sharing or cancellation. Perpendicular splitting is separate.
    """
    groups = {}
    slope = [0., .6427876096865427, .7660444431189752]
    leg = [0., -.26015745792854417, .9655662054381139]
    for side in ('left', 'right'):
        for role, member, grain, pitch, spread, depth in (
            ('lumber_leg_bolt', 'base_side_'+side, slope, 50., 57.3962318, 139.7),
            ('lumber_leg_bolt', 'lumber_leg_'+side, leg, 70., 40.9973084, 139.7),
            ('steel_shoe_rim', 'base_side_'+side, slope, 60., 55., 139.7),
            ('steel_shoe_header', 'base_header', [1., 0., 0.], 50., 130., 234.95)):
            forces = [native['physical_connection_forces'][f'{role}_{side}_{i}']['force_on_first_xyz_n']
                      for i in range(1, 5)]
            parallel_sum = sum(abs(sum(a*b for a, b in zip(f, grain, strict=True))) for f in forces)
            ref = adjusted_reference(depth)
            net_capacity = ref['Ft_mpa']*38.1*(depth-2*11.1125)
            single_row_capacity = 2*ref['Fv_mpa']*38.1*pitch
            group_capacity = single_row_capacity+ref['Ft_mpa']*38.1*(spread-11.1125)
            groups[f'{role}_{side}:{member}'] = {
                'absolute_parallel_force_sum_n': parallel_sum,
                'net_tension_capacity_n': net_capacity,
                'one_row_tear_capacity_n': single_row_capacity,
                'two_row_group_tear_capacity_n': group_capacity,
                'conservative_parallel_ratio': parallel_sum/min(net_capacity, single_row_capacity, group_capacity),
                'cross_grain_splitting_qualified': False,
                'scope': 'Parallel-grain local stress only; actual end distances exceed row pitches'}
    return groups


if __name__ == '__main__':
    main()
