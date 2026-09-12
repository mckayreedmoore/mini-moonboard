"""Conditional ASD steel checks for the frozen fabricated-shoe candidate.

N, mm and MPa throughout. These checks do not turn a rigid-shoe analysis into
a flexible plate/contact solution. In particular, prying and single-fillet root
rotation remain explicit acceptance conditions, rather than silently zero loads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

KSI = 6.894757293168
FY = 36 * KSI
FU = 58 * KSI
DIAMETER = 9.525
HOLE = 11.1125
NET_HOLE = HOLE + 1.5875  # AISC B4.3b additional net-area deduction
GRIP = 53.975
PLATE_T = 6.35
SHOE_T = 9.525
OMEGA_RUPTURE = 2.0
OMEGA_YIELD = 1.67
ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'A307': 'https://store.astm.org/a0307-21.html',
    'A36': 'https://www.ssab.com/en-us/brands-and-products/commercial-steel/structural-steel/astm-a36',
    'AISC_bolts_2016': 'https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_march-2021_linked.pdf',
    'AISC_2022_design_cards': 'https://www.aisc.org/media/vlynv2sw/p325-23aw.pdf',
    'rectangle_torsion_research': 'https://link.springer.com/article/10.1186/s10033-018-0214-9',
}


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def wrench(loads, origin):
    """Sum explicit force vectors and their moments; no imposed force allocation."""
    force = [0., 0., 0.]
    moment = [0., 0., 0.]
    for position, value in loads:
        arm = [p-o for p, o in zip(position, origin, strict=True)]
        torque = cross(arm, value)
        force = [a+b for a, b in zip(force, value, strict=True)]
        moment = [a+b for a, b in zip(moment, torque, strict=True)]
    return force, moment


def bolt_capacities():
    # Historical AISC 360-16 Table J3.2 [c], retained conservatively for BOTH
    # tabulated stresses. Do not identify these as newly verified 360-22 values.
    reduction = 1 - max(0., GRIP-5*DIAMETER)/1.5875*.01
    area = math.pi*DIAMETER**2/4
    return {'gross_area_mm2': area, 'long_grip_factor': reduction,
            'tension_asd_n': 45*KSI*reduction*area/2,
            'single_shear_asd_n': 27*KSI*reduction*area/2,
            'basis': 'AISC360-16 TableJ3.2 A307, ASD Omega2, both stresses reduced4%; no yield assumption'}


def bolt_check(force_on_wood, inward_axis, prying_n=0.):
    """Tension pulls wood opposite installation direction. No compression credit."""
    if prying_n < 0 or abs(norm(inward_axis)-1) > 1.e-8:
        raise ValueError('A unit installation axis and nonnegative prying are required')
    axial = dot(force_on_wood, inward_axis)
    tension = max(0., -axial) + prying_n
    shear = norm([v-axial*a for v, a in zip(force_on_wood, inward_axis, strict=True)])
    cap = bolt_capacities()
    # This linear envelope lies inside the AISC tension/shear interaction.
    ratio = tension/cap['tension_asd_n'] + shear/cap['single_shear_asd_n']
    return {'tension_n': tension, 'shear_n': shear, 'included_prying_n': prying_n,
            'conservative_linear_interaction_ratio': ratio,
            'available_additional_prying_n': max(0., (1-shear/cap['single_shear_asd_n'])*cap['tension_asd_n']-tension)}


def bearing_and_tearout(thickness, edge_center_distance):
    """All-direction minimum edge distance; full single-plane shear demand."""
    clear = max(0., edge_center_distance-HOLE/2)
    bearing = 1.2*DIAMETER*thickness*FU
    tearout = .6*clear*thickness*FU
    return {'bearing_asd_n': bearing, 'tearout_asd_n': tearout,
            'governing_asd_n': min(bearing, tearout), 'clear_distance_mm': clear}


def square_plate_capacities():
    net_width = 32-NET_HOLE
    net_area = net_width*PLATE_T
    # Whole-span one-way simple beam, center point load, net section through
    # the hole. This is a declared bending SCREEN, not a contact solution.
    elastic_moment = FY/OMEGA_YIELD*net_width*PLATE_T**2/6
    plastic_moment = FY/OMEGA_YIELD*net_width*PLATE_T**2/4
    return {**bearing_and_tearout(PLATE_T, 16),
            'net_section_mm2': net_area,
            'net_tension_rupture_asd_n': FU*net_area/2,
            'net_shear_rupture_asd_n': .6*FU*net_area/2,
            'gross_tension_yield_asd_n': FY*32*PLATE_T/OMEGA_YIELD,
            'one_way_elastic_bending_screen_n': 4*elastic_moment/32,
            'one_way_plastic_bending_screen_n': 4*plastic_moment/32,
            'bearing_contact_area_mm2': 32**2-math.pi*HOLE**2/4,
            'bending_assumption': '32mm simply supported span, full axial load at center, net-width beam; wood contact not solved'}


def plate_bolt_check(name, tension, shear):
    # Shoe web: closest edge is normal-direction25mm. Foot: inboard25mm.
    shoe = bearing_and_tearout(SHOE_T, 25.)
    plate = square_plate_capacities()
    return {'name': name,
            'shoe_bearing_tearout_ratio': shear/shoe['governing_asd_n'],
            'square_plate_bearing_tearout_ratio': shear/plate['governing_asd_n'],
            'square_plate_net_shear_ratio': shear/plate['net_shear_rupture_asd_n'],
            'square_plate_one_way_bending_screen_ratio': tension/plate['one_way_elastic_bending_screen_n'],
            'square_plate_required_thickness_for_one_way_screen_mm': PLATE_T*math.sqrt(tension/plate['one_way_elastic_bending_screen_n']),
            'wood_contact_pressure_average_mpa': tension/plate['bearing_contact_area_mm2']}


def rectangular_section_check(force, moment, width, thickness):
    """Section normal axis z; width along y and thickness along x.

    Elastic beam-section screen, with an additional plastic upper-bound test.
    Does not assume that passing section averages resolves local plate stress.
    """
    area = width*thickness
    elastic = abs(force[2])/area + 6*abs(moment[0])/(thickness*width**2) + 6*abs(moment[1])/(width*thickness**2)
    torsional_shear = abs(moment[2])*min(width, thickness)/rectangle_torsion_constant(width, thickness)
    shear = 1.5*math.hypot(force[0], force[1])/area + torsional_shear
    vm = math.sqrt(elastic**2+3*shear**2)
    weak_plastic = FY/OMEGA_YIELD*width*thickness**2/4
    return {'elastic_von_mises_screen_ratio': vm/(FY/OMEGA_YIELD),
            'weak_axis_plastic_upper_bound_nmm': weak_plastic,
            'weak_axis_moment_over_plastic_upper_bound': abs(moment[1])/weak_plastic,
            'required_thickness_weak_axis_elastic_mm': math.sqrt(6*abs(moment[1])*OMEGA_YIELD/(width*FY)),
            'saint_venant_torsion_shear_upper_bound_mpa': torsional_shear,
            'torsion_assumption': 'Unrestrained Saint-Venant rectangle; restrained warping stresses not included'}


def rectangle_torsion_constant(width, thickness):
    """Rectangle Saint-Venant series; 100 positive odd terms (mm4)."""
    a, b = max(width, thickness), min(width, thickness)
    series = sum(math.tanh(n*math.pi*a/(2*b))/n**5 for n in range(1, 200, 2))
    series += 1/(4*199**4)  # upper bound on omitted positive tail => lower J
    return a*b**3/3*(1-192*b/(math.pi**5*a)*series)


def web_perforated_section_screens(loads, side):
    """Horizontal net-section equilibrium through the actual LED/bolt holes.

    Plane sections and elastic stress recovery are diagnostic assumptions.
    This adds the missing perforated cuts to the gross root check; it does not
    substitute for a local plate-buckling or bolt-zone contact calculation.
    """
    from mini_moonboard import steel_base_reinforcement as model
    sn, cs = math.sin(math.radians(40)), math.cos(math.radians(40))
    origin = model.previous.b.point(0., 0., 0.).toTuple()
    holes = []
    for c in model.added_connections():
        if c.name.startswith(f'steel_shoe_rim_{side}_'):
            holes.append((c.start.y, c.start.z, NET_HOLE/2))
    for row in model.previous.bore_records():
        if row['member'] == 'base_side_'+side:
            center = model.previous.b.point(0., row['center_s_mm'], row['center_n_mm'])
            if center.z < max(p[2] for p, _ in loads)+25:
                holes.append((center.y, center.z, (row['diameter_mm']+4)/2))
    bottom, top = 234.525, max(p[2] for p, _ in loads)
    cuts = {bottom, *[bottom+(top-bottom)*i/200 for i in range(201)]}
    for _, z, radius in holes:
        cuts.update(z+radius*f for f in (-1., -.5, 0., .5, 1.))
    for p, _ in loads:
        cuts.update((p[2]-.0001, p[2]+.0001))
    checked = []
    sign = -1 if side == 'left' else 1
    for z in sorted(c for c in cuts if bottom <= c <= top):
        nmin = max(20., (z-origin[2]-cs*280)/sn)
        low = origin[1]+sn/cs*(z-origin[2])-125/cs
        high = origin[1]+sn/cs*(z-origin[2])-nmin/cs
        intervals = [(low, high)]
        for yhole, zhole, radius in holes:
            if abs(z-zhole) >= radius:
                continue
            half = math.sqrt(radius**2-(z-zhole)**2)
            a, b = yhole-half, yhole+half
            updated = []
            for lo, hi in intervals:
                if b <= lo or a >= hi:
                    updated.append((lo, hi))
                else:
                    if a > lo: updated.append((lo, a))
                    if b < hi: updated.append((b, hi))
            intervals = updated
        width = sum(b-a for a, b in intervals)
        if width <= 0:
            raise ValueError('Web cut has no remaining steel')
        yc = sum((b*b-a*a)/2 for a, b in intervals)/width
        area = width*SHOE_T
        ix = SHOE_T*sum(((b-yc)**3-(a-yc)**3)/3 for a, b in intervals)
        iy = width*SHOE_T**3/12
        center = [sign*(1219.2+SHOE_T/2), yc, z]
        force, moment = wrench([(p, f) for p, f in loads if p[2] > z], center)
        normal = max(abs(force[2]/area+moment[0]*(y-yc)/ix-moment[1]*x/iy)
                     for interval in intervals for y in interval for x in (-SHOE_T/2, SHOE_T/2))
        torsion_constant = sum(rectangle_torsion_constant(b-a, SHOE_T) for a, b in intervals)
        torsional_shear = abs(moment[2])*max(min(b-a, SHOE_T) for a, b in intervals)/torsion_constant
        shear = 1.5*math.hypot(force[0], force[1])/area+torsional_shear
        checked.append({'z_mm': z, 'net_width_mm': width, 'net_area_mm2': area,
                        'force_n': force, 'moment_nmm': moment,
                        'elastic_von_mises_screen_ratio': math.sqrt(normal**2+3*shear**2)/(FY/OMEGA_YIELD),
                        'normal_stress_over_net_rupture_allowable_screen': normal/(FU/2),
                        'saint_venant_torsion_shear_upper_bound_mpa': torsional_shear})
    return {'checked_cut_count': len(checked),
            'governing_elastic_section': max(checked, key=lambda r: r['elastic_von_mises_screen_ratio']),
            'governing_net_rupture_section': max(checked, key=lambda r: r['normal_stress_over_net_rupture_allowable_screen']),
            'qualification_pass': False,
            'limits': 'Net beam-section elastic screen; actual holes plus1/16in net deduction at bolt bores; equal-twist Saint-Venant strip torsion, no restrained warping; local buckling and bolt-zone stress require separate treatment'}


def foot_prying_necessary_check(values, side):
    """Best-case static feasibility, allowing arbitrary compressive contact.

    This is deliberately optimistic: compression can concentrate at footprint
    corners, plate plastic section strength is fully available, and compatibility
    is not enforced. Infeasibility proves that the specified limits cannot carry
    this wrench; feasibility is NOT a prying solution or a passing design.
    """
    import numpy as np
    from scipy.optimize import linprog

    sign = -1 if side == 'left' else 1
    bolts = [values[f'steel_shoe_header_{side}_{i}'] for i in range(1, 5)]
    seats = [r for name, r in values.items()
             if name.startswith(f'seat_clip_steel_shoe_{side}_')]
    if len(seats) != 4:
        return {'status': 'missing_four_rim_seat_reactions', 'qualification_pass': False}
    external = []
    for name, row in values.items():
        if name.startswith((f'steel_shoe_rim_{side}_', f'seat_clip_steel_shoe_{side}_')):
            p, f = row['point'], row['force_on_second_xyz_n']
            external.append(([sign*p[0], p[1], p[2]], [sign*f[0], f[1], f[2]]))
    # Preserve actual header shear actions. Axial actions are the LP unknowns.
    for row in bolts:
        p, f = row['point'], row['force_on_second_xyz_n']
        external.append(([sign*p[0], p[1], p[2]], [sign*f[0], f[1], 0.]))
    origin = [1035., -245., 225.]
    force, moment = wrench(external, origin)
    if math.hypot(force[0], force[1]) > 1. or abs(moment[2]) > 100.:
        return {'status': 'in_plane_shoe_free_body_not_balanced', 'qualification_pass': False,
                'force_n': force, 'moment_nmm': moment}
    locations = [[sign*r['point'][0], r['point'][1], 225.] for r in bolts]
    contacts = [[x, y, 225.] for x in (1035., 1219.2) for y in (-245., -36.)]
    # Unknowns: four positive bolt tensions (down), four contact reactions (up),
    # common utilization rho. No favorable bolt-compression mechanism.
    columns = []
    for p, sense in [(p, -1.) for p in locations]+[(p, 1.) for p in contacts]:
        _, m = wrench([(p, [0., 0., sense])], origin)
        columns.append([sense, m[0], m[1]])
    equality = np.column_stack([np.array(columns).T, np.zeros(3)])
    target = -np.array([force[2], moment[0], moment[1]])
    inequalities, limits = [], []
    capacities = []
    for i, row in enumerate(bolts):
        check = bolt_check(row['force_on_first_xyz_n'], (0., 0., -1.))
        cap = bolt_capacities()
        available = max(0., (1-check['shear_n']/cap['single_shear_asd_n'])*cap['tension_asd_n'])
        capacities.append(available)
        line = np.zeros(9); line[i] = 1.; line[8] = -available
        inequalities.append(line); limits.append(0.)
    section_rows = []
    # Full-width gross/plastic capacities are upper bounds; using them cannot
    # manufacture a false rejection through a narrow assumed effective width.
    for cut in (1060., 1110., 1181.1, 1219.2):
        width = 213. - (2*NET_HOLE if cut in (1060., 1110.) else 0.)
        capacity = FY/OMEGA_YIELD*width*SHOE_T**2/4
        _, imposed = wrench([(p, f) for p, f in external if p[0] > cut], [cut, 0., 225.])
        line = np.zeros(9)
        for i, (p, sense) in enumerate([(p, -1.) for p in locations]+[(p, 1.) for p in contacts]):
            if p[0] > cut:
                line[i] = -(p[0]-cut)*sense
        for direction in (-1., 1.):
            inequalities.append(direction*line)
            limits.append(capacity-direction*imposed[1])
        section_rows.append({'x_outward_mm': cut, 'plastic_moment_upper_bound_nmm': capacity})
    objective = np.zeros(9); objective[8] = 1.
    solved = linprog(objective, A_ub=inequalities, b_ub=limits,
                     A_eq=equality, b_eq=target, bounds=(0., None), method='highs')
    result = {'status': 'best_case_static_feasibility_only', 'qualification_pass': False,
              'external_force_n': force, 'external_moment_about_inboard_corner_nmm': moment,
              'in_plane_equilibrium_tolerances': '1N force,100Nmm moment; native printed-force precision allowance',
              'header_bolt_available_tension_n': capacities, 'foot_section_upper_bounds': section_rows,
              'solver_success': bool(solved.success), 'solver_message': solved.message,
              'compression_contact_model': 'arbitrary nonnegative corner reactions; no wood stress or compatibility limit'}
    if solved.success:
        result.update(minimum_possible_bolt_utilization=float(solved.x[8]),
                      best_case_bolt_tensions_n=solved.x[:4].tolist(),
                      best_case_contact_reactions_n=solved.x[4:8].tolist(),
                      necessary_bolt_and_foot_limits_satisfied=bool(solved.x[8] <= 1+1.e-8))
    else:
        result['necessary_bolt_and_foot_limits_satisfied'] = False
    return result


def connection_geometry():
    # Importing connection descriptors does not construct CAD solids.
    from mini_moonboard import steel_base_reinforcement as model
    return {c.name: {'axis': c.direction.toTuple(),
                    'point': (c.start+c.direction*(2.032+9.525)).toTuple()}
            for c in model.added_connections()}


def floor_friction_gate(report):
    normals = report.get('floor_contact_demands')
    values = report.get('physical_connection_forces', {})
    friction = [r for name, r in values.items() if name.endswith('_friction') and r.get('second') == 'floor']
    if not normals or not friction:
        return {'status': 'missing_floor_reactions', 'physical_admissibility_pass': False}
    rows = []
    for row in friction:
        normal = sum(r['normal_n'] for r in normals if r['body'] == row['first'])
        shear = math.hypot(*row['force_on_first_xyz_n'][:2])
        required = shear/normal if normal > 1.e-8 else (0. if shear <= 1.e-8 else None)
        rows.append({'body': row['first'], 'normal_n': normal, 'shear_n': shear,
                     'required_mu': required,
                     'mu_0_2_pass': normal >= -1.e-8 and shear <= .2*max(0., normal)+1.e-8,
                     'mu_0_4_pass': normal >= -1.e-8 and shear <= .4*max(0., normal)+1.e-8})
    return {'status': 'whole_foot_friction_necessary_check', 'contacts': rows,
            'mu_0_2_pass': all(r['mu_0_2_pass'] for r in rows),
            'mu_0_4_pass': all(r['mu_0_4_pass'] for r in rows),
            'physical_admissibility_pass': all(r['mu_0_4_pass'] for r in rows),
            'scope': 'Unmeasuredmu0.2/0.4 scenarios; whole-foot necessary conditions only, not local Coulomb or floor qualification'}


def assess_report(report):
    from fea.reinforced_weld_capacity import LENGTH_MM, evaluate_weld, weld_centroid

    values = report['physical_connection_forces']
    geometry = connection_geometry()
    missing = sorted(set(geometry)-set(values))
    if missing:
        raise ValueError('Missing shoe bolt forces: '+', '.join(missing))
    bolts = []
    for name, geo in geometry.items():
        row = values[name]
        force = row['force_on_first_xyz_n']
        if row.get('first') not in ('base_side_left', 'base_side_right', 'base_header'):
            raise ValueError(f'{name}: expected force on receiver wood')
        if norm([a-b for a, b in zip(row['point'], geo['point'], strict=True)]) > .01:
            raise ValueError(f'{name}: force point differs from frozen flange/wood interface')
        checked = bolt_check(force, geo['axis'], row.get('additional_prying_n', 0.))
        bolts.append({'name': name, **checked,
                      **plate_bolt_check(name, checked['tension_n'], checked['shear_n'])})
    shoes = []
    for side in ('left', 'right'):
        # Web free body: only the four rim-bolt actions. The timber seat acts
        # on the FOOT, not on the WEB, and must not be credited across the weld.
        rows = [values[f'steel_shoe_rim_{side}_{i}'] for i in range(1, 5)]
        loads = [(r['point'], r['force_on_second_xyz_n']) for r in rows]
        geo = {'centroid_mm': weld_centroid(side), 'length_mm': LENGTH_MM}
        force, moment = wrench(loads, geo['centroid_mm'])
        weld = evaluate_weld(force, moment, side)
        web_origin = [(-1 if side == 'left' else 1)*(1219.2+9.525/2),
                      geo['centroid_mm'][1], 234.525]
        web_f, web_m = wrench(loads, web_origin)
        web = rectangular_section_check(web_f, web_m, geo['length_mm'], SHOE_T)
        shoes.append({'side': side, 'web_to_weld_force_n': force,
                      'web_to_weld_moment_nmm': moment, 'weld': weld,
                      'web_root_section_screen': web,
                      'web_perforated_section_screens': web_perforated_section_screens(loads, side),
                      'foot_prying_necessary_check': foot_prying_necessary_check(values, side),
                      'web_root_excludes_LED_and_bolt_holes': True})
    validity = {key: report.get(key) for key in (
        'global_equilibrium_passed', 'mpc_check_passed', 'contact_active_set_converged',
        'qualified_for_design', 'actual_joint_demands_qualified')}
    converged = all(validity[key] is True for key in (
        'global_equilibrium_passed', 'mpc_check_passed', 'contact_active_set_converged'))
    friction = floor_friction_gate(report)
    return {'producer_validity': validity,
            'response_status': 'converged_conditional_model' if converged else 'INVALID_RESPONSE_DIAGNOSTIC_ONLY',
            'physical_friction_gate': friction,
            'physical_response_admissible_for_mu_0_4': converged and friction['physical_admissibility_pass'],
            'bolt_checks': bolts, 'shoe_checks': shoes,
            'max_bolt_interaction_ratio': max(b['conservative_linear_interaction_ratio'] for b in bolts),
            'max_square_plate_bending_screen_ratio': max(b['square_plate_one_way_bending_screen_ratio'] for b in bolts),
            'qualified': False,
            'remaining_conditions': ['Single-sided weld rotation detail must be resolved',
                'Rigid shoe forces omit flexible plate prying unless explicitly supplied',
                'Foot plate/contact solution and web sections through LED/bolt holes are not completed by root-section screen',
                'Fatigue, nut/washer product certification and timber connection resistance are separate checks']}


def reports_in(value):
    """Accept the producer's nested case/sweep reports, retaining their paths."""
    if isinstance(value, dict):
        if 'physical_connection_forces' in value:
            yield '', value
        else:
            for key, child in value.items():
                for path, row in reports_in(child):
                    yield f'{key}/{path}', row
    elif isinstance(value, list):
        for index, child in enumerate(value):
            for path, row in reports_in(child):
                yield f'{index}/{path}', row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demands', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    paths = [Path(__file__), ROOT/'fea/reinforced_weld_capacity.py',
             ROOT/'mini_moonboard/steel_base_reinforcement.py']
    if args.demands:
        paths.append(args.demands)
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result = {'units': 'N, mm, MPa; ASD service-demand comparison', 'sources': SOURCES,
              'bolt_capacities': bolt_capacities(), 'square_plate_capacities': square_plate_capacities(),
              'shoe_hole_minimum_capacities': bearing_and_tearout(SHOE_T, 25),
              'qualified': False, 'case_results': []}
    if args.demands:
        data = json.loads(args.demands.read_text())
        result['case_results'] = [{'path': path, **assess_report(row)} for path, row in reports_in(data)]
        if not result['case_results']:
            raise ValueError('No physical_connection_forces found; no demand comparison performed')
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if before != after:
        raise RuntimeError('Sources changed during calculation')
    result['source_sha256'] = before
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write('\n')
    return result


if __name__ == '__main__':
    main()
