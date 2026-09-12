"""Reference-limit sensitivity for the existing six-bolt wider-leg assessment.

These are model-specific allowable-reference crossings, never breaking weights.
Loaded-edge placement and unverified contact/material assumptions remain separate.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path

from fea.dowel_yield import single_shear
from fea.leg_attachment_check import LEG, RIM
from fea.leg_completion_assessment import foot_joint_moment
from fea.leg_only_load_check import axial_support_force
from fea.round_structural_global_envelope import locations
from fea.wider_leg_assessment import (
    CAD,
    evaluate,
    placement,
    planar_forces,
    six_group_factor,
)
from fea.wider_leg_wood_checks import dot
from mini_moonboard import wider_leg_hardware as hw

POUND_FORCE_N = 4.4482216152605


def prepare():
    """Read the same current CAD evidence; no geometry regeneration or alteration."""
    from mini_moonboard import wider_leg_frame as model

    cad = json.loads(CAD.read_text())
    for path, expected in cad['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('CAD evidence stale: ' + path)
    points = [[0., r['world_y_mm'], r['world_z_mm']] for r in cad['drilling']
              if r['member'] == 'lumber_leg_left']
    top = [sum(p[k] for p in points) / len(points) for k in range(3)]
    leg = next(r for r in cad['mass_inventory'] if r['name'] == 'lumber_leg_left')
    polygon = cad['foot_polygons_xyz_mm']['lumber_leg_left']
    foot = [sum(p[k] for p in polygon) / len(polygon) for k in range(3)]
    half = (max(p[1] for p in polygon) - min(p[1] for p in polygon)) / 2
    holds = list(locations(model))
    equipment_y = max(p[1] + offset*n[1] for _, p, n in holds for offset in (0., 100.))
    mass = cad['state']['mass_kg'] + 25.
    dead_y = (cad['state']['mass_kg']*cad['state']['centre_xyz_mm'][1] + 25.*equipment_y)/mass
    return {'cad': cad, 'points': points, 'top': top, 'leg': leg, 'foot': foot, 'half': half,
                'holds': holds, 'mass': mass, 'dead_y': dead_y}


def force_cases(data, pounds, foot_y, share=1., vertical_multiplier=2., horizontal_max=300.):
    """Recompute gravity and fixed 300 N horizontal contribution independently.

Share applies to the total rear-support resultant including dead load. Local
leg self-weight in the joint moment remains that of one complete leg.
"""
    if not 0 < share <= 1:
        raise ValueError('Rear-load share must be positive and at most one')
    if pounds < 0 or vertical_multiplier < 0:
        raise ValueError('Climber weight and vertical multiplier must be nonnegative')
    unique = {}
    for name, p, n in data['holds']:
        for front, offset, horizontal in itertools.product((-270.95, -36.), (0., 100.), (0., horizontal_max)):
            compression = share*axial_support_force(
                downward_n=pounds*vertical_multiplier*POUND_FORCE_N,
                horizontal_n=horizontal, load_y=p[1]+offset*n[1], load_z=p[2]+offset*n[2],
                dead_n=data['mass']*9.80665, dead_y=data['dead_y'], front_y=front,
                rear_y=foot_y, vertical_cosine=LEG[2])
            unique[round(compression, 9)] = {'compression_n': compression, 'hold': name,
                'front_y_mm': front, 'standoff_mm': offset, 'horizontal_n': horizontal,
                'front_vertical_reaction_n':data['mass']*9.80665+pounds*vertical_multiplier*POUND_FORCE_N-compression/share*LEG[2]}
    return list(unique.values())


def source_adjusted_lateral(forces, *, exact_angle=False, yield_psi=45000., duration_factor=1.):
    """NDS angle-dependent reduction sensitivity; no spacing approval implied."""
    rows = []
    for force in forces:
        demand = math.hypot(force[1], force[2])
        bearing, angles = [], []
        for grain in (RIM, LEG):
            cosine = min(1., abs(sum(f*g for f, g in zip(force, grain, strict=True)))/demand) if demand else 0.
            perpendicular = 6100*.5**1.45/math.sqrt(.5)
            bearing.append(5600*perpendicular/(5600*(1-cosine*cosine)+perpendicular*cosine*cosine))
            angles.append(math.degrees(math.acos(cosine)))
        ktheta = 1+.25*max(angles)/90 if exact_angle else 1.25
        result = single_shear(main_length_in=1.5, side_length_in=1.5,
            main_bearing_lb_in=bearing[0]*.5, side_bearing_lb_in=bearing[1]*.5,
            main_yield_moment_lb_in=yield_psi*.5**3/6,
            side_yield_moment_lb_in=yield_psi*.5**3/6, gap_in=0.,
            reduction_terms={k: factor*ktheta for k, factor in
                {'Im':4., 'Is':4., 'II':3.6, 'IIIm':3.2, 'IIIs':3.2, 'IV':3.2}.items()})
        reference = result['reference_lateral_lbf']*POUND_FORCE_N*six_group_factor()*duration_factor
        rows.append({'demand_n': demand, 'ratio': demand/reference, 'mode': result['governing_mode']})
    return rows


def connection_metrics(data, compression, foot_y, *, exact_angle=False, yield_psi=45000., duration_factor=1.):
    foot = [data['foot'][0], foot_y, 0.]
    moment = foot_joint_moment(compression_n=compression, top=data['top'], foot=foot,
                              leg_mass_kg=data['leg']['mass_kg'],
                              leg_centre=data['leg']['centre_xyz_mm'])
    forces = planar_forces(data['points'], compression, moment)
    bolts = source_adjusted_lateral(forces, exact_angle=exact_angle, yield_psi=yield_psi, duration_factor=duration_factor)
    ratios = [b['ratio'] for b in bolts]
    axial = hw.axial_couple_screen(data['points'], [0., compression*LEG[1], compression*LEG[2]])
    combined = [ratio + hw.bolt_combined_screen(b['demand_n'], tension)['axial_stress_mpa'] /
                (92000*hw.PSI/2) for ratio, b, tension in
                zip(ratios, bolts, axial['bolt_tension_envelope_n'], strict=True)]
    return {'lateral': max(ratios), 'conservative_lateral_plus_axial': max(combined),
                'compression_n': compression, 'joint_moment_nmm': moment,
                'minimum_placement_margin_mm': placement(data['cad'], forces)['minimum_margin_mm'],
                'governing_modes': sorted({b['mode'] for b in bolts})}


def envelope(data, pounds, offset_mm, share=1., vertical_multiplier=2., horizontal_max=300., **connection_options):
    foot_y = data['foot'][1] + offset_mm
    rows = []
    for load in force_cases(data, pounds, foot_y, share, vertical_multiplier, horizontal_max):
        row = connection_metrics(data, load['compression_n'], foot_y, **connection_options)
        row['load'] = load
        rows.append(row)
    return {key: max(rows, key=lambda r: r[key]) for key in
            ('lateral', 'conservative_lateral_plus_axial')}


def bisect_crossing(function, low, high, iterations=36):
    """Locate an already bracketed continuous unity crossing of either direction."""
    flo, fhi = function(low)-1, function(high)-1
    if flo == 0:
        return low
    if fhi == 0:
        return high
    if flo*fhi > 0:
        raise ValueError('Unity crossing is not bracketed')
    for _ in range(iterations):
        middle = (low+high)/2
        fm = function(middle)-1
        if flo*fm <= 0:
            high = middle
        else:
            low, flo = middle, fm
    return (low+high)/2


def front_contact_crossing(data, offset_mm):
    """First zero front reaction with unanchored unilateral floor contact.

This is a validity limit of the existing support model, not a friction test.
Sharing between rear legs does not change total rear vertical reaction.
"""
    foot_y = data['foot'][1]+offset_mm
    candidates = []
    for name, p, n in data['holds']:
        for front, offset, horizontal in itertools.product((-270.95, -36.), (0., 100.), (0., 300.)):
            y, z = p[1]+offset*n[1], p[2]+offset*n[2]
            intercept = data['mass']*9.80665 - (
                horizontal*z+data['mass']*9.80665*(data['dead_y']-front))/(foot_y-front)
            slope = 2*POUND_FORCE_N*(1-(y-front)/(foot_y-front))
            if intercept <= 0:
                crossing = 0.
            elif slope >= 0:
                continue
            else:
                crossing = -intercept/slope
            candidates.append({'climber_lb': crossing, 'hold': name, 'front_y_mm': front,
                                   'standoff_mm': offset, 'horizontal_n': horizontal,
                                   'reaction_intercept_n': intercept, 'reaction_slope_n_per_lb': slope})
    return min(candidates, key=lambda c:c['climber_lb']) if candidates else None


def weight_crossing(data, offset_mm, share, metric, **connection_options):
    def ratio(pounds):
        return envelope(data, pounds, offset_mm, share, **connection_options)[metric][metric]
    if ratio(0.) >= 1.:
        return {'climber_lb': 0., 'fixed_loads_already_exceed_reference': True}
    upper = 250.
    while ratio(upper) < 1. and upper < 4000.:
        upper *= 2
    if ratio(upper) < 1.:
        return {'climber_lb': None, 'not_crossed_below_lb': upper}
    weight = bisect_crossing(ratio, 0., upper)
    witness = envelope(data, weight, offset_mm, share, **connection_options)[metric]
    contact = front_contact_crossing(data, offset_mm)
    return {'climber_lb': weight, 'witness': witness, 'first_front_contact_loss':contact,
            'within_unanchored_front_contact_domain':contact is None or weight <= contact['climber_lb']}


def cop_intervals(data, share, metric, steps=80):
    """Scan the entire physical footprint then refine every bracketed crossing."""
    xs = [-data['half']+2*data['half']*i/steps for i in range(steps+1)]
    def ratio(x):
        return envelope(data, 250., x, share)[metric][metric]
    ys = [ratio(x) for x in xs]
    roots = [bisect_crossing(ratio, a, b) for a, b, ya, yb in
             zip(xs[:-1], xs[1:], ys[:-1], ys[1:], strict=True) if (ya-1)*(yb-1) < 0]
    bounds = [xs[0], *roots, xs[-1]]
    intervals = [[a, b] for a, b in itertools.pairwise(bounds)
                 if ratio((a+b)/2) <= 1.]
    return {'reference_satisfying_offset_intervals_mm': intervals,
                'crossings_offset_mm': roots, 'scan_steps': steps,
                'sampled_minimum_ratio': min(ys), 'sampled_maximum_ratio': max(ys),
                'curve': [{'offset_mm': x, 'ratio': y} for x, y in zip(xs, ys, strict=True)]}


def full_context(data):
    """Reconstruct the unchanged aggregate's wood-section context from current CAD."""
    from mini_moonboard import wider_leg_frame as model
    centre, _, _, _, _ = model.axes()
    leg_centre = list(centre.toTuple())
    origin = model.previous.b.point(0, 0, 0)
    rim_centre = list((origin+model.previous.b.normal()*92.075).toTuple())
    holes = [(dot([p[i]-leg_centre[i] for i in range(3)], LEG),
              dot([p[i]-leg_centre[i] for i in range(3)], (0., LEG[2], -LEG[1])), 14.2875)
             for p in data['points']]
    rim_notches = []
    for cut in data['cad']['local_rim_cuts']:
        if 'base_side_left' not in cut['members'] or cut['connection'].startswith('lumber_leg_bolt_'):
            continue
        slo, shi = cut['grain_extent_mm']
        nlo, nhi = cut['depth_extent_inside_rim_mm']
        rim_notches.append(((slo+shi)/2, 92.075-(nlo+nhi)/2, nhi-nlo))
    return {'top': data['top'], 'leg': data['leg'], 'leg_centre': leg_centre, 'rim_centre': rim_centre,
        'leg_ends': [-1663.9599640771353, 200.], 'rim_ends': [-157.18998601159768, 2438.4],
        'support_span_mm': math.hypot(data['top'][1]-data['foot'][1], data['top'][2]),
        'holes': holes, 'rim_notches': rim_notches,
        'joint_depth_offset_mm': dot([data['top'][i]-leg_centre[i] for i in range(3)], (0., LEG[2], -LEG[1]))}


def full_strength_envelope(data, context, pounds, offset):
    """Every unique load case, all existing numerical metrics; exact-angle lateral."""
    foot_y = data['foot'][1]+offset
    cases = []
    for load in force_cases(data, pounds, foot_y):
        row = evaluate(data['cad'], data['points'], context, load['compression_n'],
                       [data['foot'][0], foot_y, 0.])
        corrected = connection_metrics(data, load['compression_n'], foot_y, exact_angle=True)
        for name in ('lateral', 'conservative_lateral_plus_axial'):
            row['metrics'][name] = corrected[name]
        cases.append({'metrics': row['metrics'], 'load': load,
                          'minimum_placement_margin_mm': row['placement']['minimum_margin_mm']})
    peaks = {name: max(cases, key=lambda c:c['metrics'][name]) for name in cases[0]['metrics']}
    name = max(peaks, key=lambda k:peaks[k]['metrics'][k])
    return {'peak_ratio': peaks[name]['metrics'][name], 'governing_metric': name,
                'governing_load': peaks[name]['load'], 'peak_metrics': {k:v['metrics'][k] for k,v in peaks.items()},
                'evaluated_unique_load_cases': len(cases)}


def full_strength_crossings(data):
    context = full_context(data)
    rows = []
    for name, offset in (('front_edge', -data['half']), ('middle_third_front', -data['half']/3), ('center', 0.)):
        contact = front_contact_crossing(data, offset)
        high = min(1000., contact['climber_lb']) if contact else 1000.
        def ratio(pounds, offset=offset):
            return full_strength_envelope(data, context, pounds, offset)['peak_ratio']
        if ratio(0.) >= 1.:
            weight = 0.
        elif ratio(high) < 1.:
            weight = None
        else:
            weight = bisect_crossing(ratio, 0., high, iterations=26)
        rows.append({'pressure_resultant': name, 'rear_load_share': 1.,
            'first_numerical_reference_crossing_lb': weight,
            'at_crossing': full_strength_envelope(data, context, weight, offset) if weight is not None else None,
            'at_250_lb': full_strength_envelope(data, context, 250., offset),
            'first_front_contact_loss': contact,
            'qualified_for_construction': False})
    return rows


def build():
    data = prepare()
    scenarios = []
    for share in (1., .5):
        for name, offset in (('front_edge', -data['half']), ('middle_third_front', -data['half']/3),
                             ('center', 0.), ('middle_third_rear', data['half']/3),
                             ('rear_edge', data['half'])):
            row = {'rear_load_share': share, 'pressure_resultant': name, 'offset_from_foot_center_mm': offset,
                       'at_250_lb': envelope(data, 250., offset, share),
                       'first_front_contact_loss':front_contact_crossing(data, offset)}
            row['reference_weight_crossings'] = {metric: weight_crossing(data, offset, share, metric)
                for metric in ('lateral', 'conservative_lateral_plus_axial')}
            scenarios.append(row)
    intervals = {str(share): {metric: cop_intervals(data, share, metric) for metric in
                 ('lateral', 'conservative_lateral_plus_axial')} for share in (1., .5)}
    sensitivities = []
    for name, offset in (('front_edge', -data['half']), ('middle_third_front', -data['half']/3),
                         ('center', 0.), ('middle_third_rear', data['half']/3), ('rear_edge', data['half'])):
        sensitivities.append({'pressure_resultant': name, 'offset_mm': offset,
            'exact_angle': envelope(data, 250., offset, exact_angle=True),
            'exact_angle_grade5_yield': envelope(data, 250., offset, exact_angle=True, yield_psi=92000.),
            'exact_angle_weight_crossings': {metric: weight_crossing(data, offset, 1., metric, exact_angle=True)
                for metric in ('lateral', 'conservative_lateral_plus_axial')},
            'duration_1_6_sensitivity': envelope(data, 250., offset, exact_angle=True, duration_factor=1.6),
            'unroped_1200_n_vertical_no_horizontal': envelope(data, 250., offset,
                vertical_multiplier=1200/(250*POUND_FORCE_N), horizontal_max=0.),
            'unroped_1200_n_vertical_300_n_horizontal': envelope(data, 250., offset,
                vertical_multiplier=1200/(250*POUND_FORCE_N))})
    source_paths = [Path(__file__), CAD, Path('fea/wider_leg_assessment.py'),
                    Path('fea/leg_bolt_pattern_search.py'), Path('fea/leg_completion_assessment.py'),
                    Path('fea/leg_only_load_check.py'), Path('mini_moonboard/wider_leg_hardware.py'),
                    Path('fea/dowel_yield.py'), Path('fea/round_structural_global_envelope.py'),
                    Path('fea/wider_leg_wood_checks.py'), Path('fea/reinforced_timber_resistance.py')]
    return {'candidate': 'wider-leg-development', 'climber_rating_established': False,
        'assumptions': {'vertical_multiplier': 2., 'fixed_horizontal_force_n': 300., 'maximum_standoff_mm': 100.,
                         'equipment_mass_kg': 25., 'combined_dead_mass_kg': data['mass'],
                         'plate_yield_floor_psi_assumed': 33000., 'prying_amplification_assumed': 2.,
                         'foot_center_y_mm': data['foot'][1], 'foot_half_length_mm': data['half'],
                         'no_sliding_assumed': True, 'hold_positions': len(data['holds'])},
        'all_metric_crossings_one_leg': full_strength_crossings(data), 'scenarios': scenarios, 'pressure_intervals_at_250_lb': intervals, 'source_sensitivities': sensitivities,
        'limits': ['Reference crossings are not physical breaking weights or approved climber limits.',
                'Reference crossings beyond first front contact loss extrapolate outside the unanchored support model and are not usable limits.',
                'Exact-angle reductions follow NDS Table12.3.1B; the 92ksi yield comparison is conditional on the catalog Grade5 steel property.',
                'Duration factor1.6 is an explicitly separate short-duration sensitivity, not a selected adjustment or automatic consequence of a dynamic load.',
                'The1200N comparisons use the cited CWA unroped-climber vertical value only; they do not reproduce a complete CWA load combination or claim compliance.',
                'Existing loaded-edge placement deficiency is separate and not waived by a smaller force ratio.',
                'Fifty-percent sharing is an idealized sensitivity, not demonstrated for the installed frame.',
                'Center/middle-third pressure assumptions are not installed constraints; full-foot endpoints are sensitivities.',
                'Prying factor, plate material, fixed leg-force direction and local contact remain assumed.',
                'Connection-only crossings are separate from all-metric crossings; the latter cover all existing numerical metrics for three one-leg pressure positions, with exact-angle lateral reductions.',
                'At zero climber weight the fixed horizontal-force sensitivity still includes 300 N; this is not a permanent-only load case.'],
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}


if __name__ == '__main__':
    result = build()
    Path('fea/results/wider-leg-limits.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps([{'share': r['rear_load_share'], 'cop': r['pressure_resultant'],
        'lateral': r['at_250_lb']['lateral']['lateral'], 'combined': r['at_250_lb']['conservative_lateral_plus_axial']['conservative_lateral_plus_axial'],
        'limits_lb': {k:v['climber_lb'] for k,v in r['reference_weight_crossings'].items()}} for r in result['scenarios']], indent=2))
