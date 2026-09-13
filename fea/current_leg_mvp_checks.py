"""Conditional checks of recovered forces for the separate leg MVP candidate.

Geometry is supplied as JSON, never imported from an older CAD candidate. A
successful numerical comparison is not a construction release or a prying bound.
"""
import math

from fea.current_response_resistance import VALIDITY, member_comparisons
from fea.dowel_yield import single_shear
from fea.reinforced_fastener_checks import dot, norm
from fea.reinforced_timber_resistance import effective_beam_length, member_check
from fea.wider_leg_wood_checks import joint_local_checks, section_envelope
from mini_moonboard import wider_leg_hardware as hw


def vector(value):
    if len(value) != 3 or not all(math.isfinite(x) for x in value):
        raise ValueError('Require a finite three-component vector')
    return list(value)


def unit(value):
    result = vector(value)
    if not math.isclose(norm(result), 1., abs_tol=1e-8):
        raise ValueError('Require a unit direction')
    return result


def bolt_check(row, members, *, diameter_mm=12.7):
    """Smooth 1/2-inch Grade 5 bolt; diameter-dependent DF-L bearing."""
    if not math.isclose(diameter_mm, hw.BOLT_DIAMETER, abs_tol=1e-8):
        raise ValueError('Catalog hardware checks support only 1/2-inch bolts')
    axis = unit(row['axis'])
    force = vector(row['force_on_first_xyz_n'])
    reaction = vector(row['force_on_second_xyz_n'])
    if norm([a+b for a, b in zip(force, reaction, strict=True)]) > 1e-6:
        raise ValueError('Bolt action/reaction mismatch')
    axial = dot(force, axis)
    lateral_vector = [f-axial*a for f, a in zip(force, axis, strict=True)]
    lateral = norm(lateral_vector)
    diameter = diameter_mm/25.4
    perpendicular = 6100*.5**1.45/math.sqrt(diameter)
    bearing = []
    lengths = []
    for key in ('first', 'second'):
        member = members[row[key]]
        grain = unit(member['grain'])
        if abs(dot(grain, axis)) > 1e-8:
            raise ValueError('Bolt must be perpendicular to member grain')
        cosine2 = min(1., (dot(lateral_vector, grain)/lateral)**2) if lateral else 0.
        bearing.append(5600*perpendicular/(5600*(1-cosine2)+perpendicular*cosine2))
        lengths.append(member['width_mm']/25.4)
    reference = single_shear(main_length_in=lengths[0], side_length_in=lengths[1],
        main_bearing_lb_in=bearing[0]*diameter, side_bearing_lb_in=bearing[1]*diameter,
        main_yield_moment_lb_in=45000*diameter**3/6,
        side_yield_moment_lb_in=45000*diameter**3/6, gap_in=0.,
        reduction_terms={'Im':5., 'Is':5., 'II':4.5, 'IIIm':4., 'IIIs':4., 'IV':4.})
    capacity = reference['reference_lateral_lbf']*4.4482216152605
    # The absolute axial spring force bounds either sign; it is not recovered
    # preload or a validated amplification of local contact/prying.
    tension = abs(axial)
    ratio = lateral/capacity
    return {'lateral_demand_n':lateral, 'axial_increment_signed_n':axial,
            'axial_absolute_envelope_n':tension, 'reference_lateral_n':capacity,
            'lateral_ratio':ratio, 'bearing_psi':bearing, 'dowel_reference':reference,
            'plate':hw.plate_screen(tension), 'washer':hw.washer_screen(tension),
            'steel':hw.bolt_combined_screen(lateral,tension,lateral_ratio=ratio),
            'group_basis':'Individual recovered bolt forces; no second distribution factor. Group stiffness and row applicability remain model assumptions.',
            'axial_basis':'Absolute recovered axial increment; preload and local contact/prying amplification are not resolved.'}


def net_member_check(data, member, holes):
    """Worst hole-section stresses at all stations, with gross stability factors.

    Equivalent actions reproduce net stresses in the established equations;
    local stress concentrations, torsion and opening shear remain unresolved.
    """
    b, d = member['width_mm'], member['depth_mm']
    sections = section_envelope(holes,depth_mm=d,width_mm=b)
    area = min(s['area_mm2'] for s in sections)
    strong = min(s['strong_modulus_mm3'] for s in sections)
    weak = min(s['weak_modulus_mm3'] for s in sections)
    eccentricity = max(abs(s['centroid_mm']) for s in sections)
    swapped = data['member']['width_mm'] > data['member']['depth_mm']
    checks = []
    for section in data['sections']:
        axial = section['axial_n_tension_positive']
        check = member_check(width_mm=b,depth_mm=d,axial_n=axial*b*d/area,
            moment_strong_nmm=(abs(section['moment_v_nmm' if swapped else 'moment_u_nmm'])+abs(axial)*eccentricity)*(b*d*d/6)/strong,
            moment_weak_nmm=abs(section['moment_u_nmm' if swapped else 'moment_v_nmm'])*(d*b*b/6)/weak,
            shear_strong_n=section['shear_u_n' if swapped else 'shear_v_n']*b*d/area,
            shear_weak_n=section['shear_v_n' if swapped else 'shear_u_n']*b*d/area,
            torsion_nmm=section['torsion_nmm'],column_effective_strong_mm=data['length_mm'],
            column_effective_weak_mm=data['length_mm'],beam_effective_mm=effective_beam_length(data['length_mm'],d))
        check['local_opening_resistance_evaluated'] = False
        check['section_metadata_basis'] = 'Equivalent gross section under scaled actions; actual minimum net area and moduli are in the enclosing envelope record.'
        necessary = max(check['necessary_compression_interaction_even_if_fully_braced'],check['tension_conservative_interaction'],check['shear_ratio'])
        checks.append({'station_along_grain_mm':section['station_along_grain_mm'],
                       'conservative_net_section_envelope_ratio':necessary, **check})
    if not checks:
        raise ValueError('Require recovered member sections')
    return {'minimum_area_mm2':area,'minimum_strong_modulus_mm3':strong,
            'minimum_weak_modulus_mm3':weak,'maximum_centroid_eccentricity_mm':eccentricity,
            'conservative_peak':max(checks,key=lambda c:c['conservative_net_section_envelope_ratio']),
            'full_length_unbraced_sensitivity_failed':any(c['conditional_checked_failure'] for c in checks),
            'scope':'Independent worst area/moduli/eccentricity at every station. Exceedance calls for station-matched refinement, not a demonstrated local failure. Gross stability assumptions persist; raw end/sole reductions, local opening shear and torsion are unresolved.'}


def assess(report, geometry):
    """Assess one native case using a matching, explicit geometry record.

    geometry members: grain, centre_mm, end_stations_mm, depth_mm, width_mm,
    additional_section_boxes [(grain station, depth coordinate, strip diameter)],
    openings_complete. Bolt holes are generated from recovered bolt points;
    other holes must be supplied explicitly. Required bolt_names binds inventory.
    """
    if report.get('candidate') not in ('leg-mvp-development', 'leg-mvp-sole-development') or geometry.get('candidate') != report['candidate']:
        raise ValueError('Require matching leg MVP candidate response and geometry')
    validity = {key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'candidate':report['candidate'], 'producer_validity':validity,
                'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY', 'qualified_for_design':False}
    hole = geometry['hole_diameter_mm']
    if not math.isfinite(hole) or hole < geometry['bolt_diameter_mm']:
        raise ValueError('Require a finite clearance hole at least bolt diameter')
    members = geometry['members']
    expected_members = {'lumber_leg_left','lumber_leg_right','base_side_left','base_side_right'}
    if set(members) != expected_members:
        raise ValueError('Require both legs and both outer rims')
    source = report.get('physical_connection_forces', report.get('mechanical_connection_forces', {}))
    forces = {name:row for name,row in source.items() if name.startswith('lumber_leg_bolt_')}
    if not forces or set(forces) != set(geometry['bolt_names']):
        raise ValueError('Recovered bolt inventory does not match CAD geometry')
    bolts = {name:bolt_check(row,members,diameter_mm=geometry['bolt_diameter_mm']) for name,row in forces.items()}
    wood = {}
    net = {}
    for name, member in members.items():
        grain = unit(member['grain'])
        centre = vector(member['centre_mm'])
        dimensions = [member['width_mm'],member['depth_mm']]
        ends = member['end_stations_mm']
        if (not all(math.isfinite(v) and v > 0 for v in dimensions)
                or len(ends) != 2 or not all(math.isfinite(v) for v in ends) or ends[0] >= ends[1]):
            raise ValueError('Require positive stock dimensions and ordered finite ends')
        native_member = report['member_section_demands'][name]['member']
        if any(not math.isclose(a,b,abs_tol=1e-6) for a,b in zip(sorted(dimensions),sorted([native_member['width_mm'],native_member['depth_mm']]),strict=True)):
            raise ValueError('Native and supplied member dimensions differ: '+name)
        if 'axis' in native_member and abs(dot(unit(native_member['axis']),grain)) < 1-1e-8:
            raise ValueError('Native and supplied grain directions differ: '+name)
        points, actions = [], []
        for row in forces.values():
            if name in (row['first'],row['second']):
                side = 'first' if name == row['first'] else 'second'
                points.append(vector(row['point']))
                actions.append(vector(row['force_on_'+side+'_xyz_n']))
        if not points:
            raise ValueError('Missing forces for '+name)
        wood[name] = joint_local_checks(points,actions,grain=grain,centre=centre,
            end_stations_mm=member['end_stations_mm'],depth_mm=member['depth_mm'],
            width_mm=member['width_mm'],hole_mm=geometry['hole_diameter_mm'],
            additional_section_boxes=member['additional_section_boxes'])
        wood[name]['all_openings_represented'] = member['openings_complete'] is True
        normal = [0.,grain[2],-grain[1]]
        holes = [(dot([p[i]-centre[i] for i in range(3)],grain),
                  dot([p[i]-centre[i] for i in range(3)],normal),geometry['hole_diameter_mm']) for p in points]
        holes.extend(member['additional_section_boxes'])
        net[name] = net_member_check(report['member_section_demands'][name],member,holes)
    gross_source = dict(report, member_section_demands={name:data for name,data in report['member_section_demands'].items() if name in members})
    if set(gross_source['member_section_demands']) != set(members):
        raise ValueError('Missing current member section demands')
    gross = member_comparisons(gross_source)
    for result in gross.values():
        result.pop('checks', None)
    metrics = {
        'conservative_net_member_envelope':max(n['conservative_peak']['conservative_net_section_envelope_ratio'] for n in net.values()),
        'lateral':max(b['lateral_ratio'] for b in bolts.values()),
        'parallel_wood':max(w['parallel_peak_ratio'] for w in wood.values()),
        'supplemental_splitting':max(w['splitting_peak_ratio'] for w in wood.values()),
        'plate_bearing':max(b['plate']['wood_bearing_ratio'] for b in bolts.values()),
        'plate_plastic_bending':max(b['plate']['plate_plastic_bending_ratio'] for b in bolts.values()),
        'washer_bending':max(b['washer']['single_washer_elastic_bending_ratio'] for b in bolts.values()),
        'steel_direct':max(b['steel']['steel_direct_interaction_ratio'] for b in bolts.values()),
        'additional_linear_lateral_axial':max(b['steel']['linear_lateral_axial_interaction_ratio'] for b in bolts.values()),
    }
    stack = hw.dimensional_window()
    failure = any(v > 1 for v in metrics.values()) or not stack['dimensional_pass']
    return {'candidate':report['candidate'], 'producer_validity':validity,
            'status':'CONDITIONAL_COMPARISON_EXCEEDED' if failure else 'LISTED_LOCAL_COMPARISONS_MET_WITH_OPEN_LIMITS',
            'metrics':metrics, 'bolts':bolts, 'local_wood':wood,'gross_members':gross,'net_members':net,
            'catalog_stack':stack, 'qualified_for_design':False,
            'limits':[
                'Geometry placement and local service-opening resistance require separate checks; net-section stresses and full-length stability sensitivities are included.',
                'Gross-member stability is reported separately as a full-length unbraced sensitivity.',
                'Supplemental EC5 splitting is separate from NDS ASD; kmod=0.8, gammaM=1.3 and additional force factor=1.5 are explicit assumptions.',
                'Plate yield floor 33 ksi, minimum thickness 4.5 mm and uniform bearing pressure are assumptions requiring confirmation.',
                'Recovered axial forces do not bound local prying or contact amplification; no invented 2x amplification is treated as qualified.',
                'Nominal catalog stack dimensions do not verify actual delivered hardware or plate collision fit.',
                'No-slip floor and accepted panels are assessment inputs; this result is not a whole-frame rating.']}
