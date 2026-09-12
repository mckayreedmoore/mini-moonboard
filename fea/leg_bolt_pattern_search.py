"""Bounded four-bolt pattern search within the existing single 2x6 members.

Results qualify neither the net wood section nor the complete connection.
"""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.dowel_yield import single_shear
from fea.leg_attachment_check import BUNDLE, LEG, RIM
from fea.leg_completion_assessment import foot_joint_moment
from fea.leg_only_load_check import MASS

SOURCE = Path('fea/results/leg-completion-assessment-v2.json')
WIDTH = 139.7
THICKNESS = 38.1


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def group_factor(diameter_in, pitch_mm):
    """NDS 11.3-1, four-fastener row bound with diameter-dependent stiffness."""
    ea = 1600000*1.5*5.5
    gamma = 180000*diameter_in**1.5
    u = 1+gamma*(pitch_mm/25.4)/ea
    m = 1/(u+math.sqrt(u*u-1))
    return m*(1-m**8)/(4*((1+m**4)*(1+m)-1+m**8))*2/(1-m)


def pattern(centre, a, b, shift_leg=0., shift_rim=0.):
    return [[centre[k]+(s*a/2+shift_leg)*LEG[k]+(t*b/2+shift_rim)*RIM[k]
             for k in range(3)] for s in (-1, 1) for t in (-1, 1)]


def bolt_forces(points, compression, moment):
    centre = [sum(p[k] for p in points)/4 for k in range(3)]
    polar = sum((p[1]-centre[1])**2+(p[2]-centre[2])**2 for p in points)
    return [(0., compression*LEG[1]/4-moment*(p[2]-centre[2])/polar,
             compression*LEG[2]/4+moment*(p[1]-centre[1])/polar) for p in points]


def cross_row_minimum(diameter_mm):
    ratio = THICKNESS/diameter_mm
    if ratio >= 6:
        return 5*diameter_mm
    return 2.5*diameter_mm if ratio <= 2 else (5*THICKNESS+10*diameter_mm)/8


def geometry(points, original_centre, diameter_mm, a, b, force_cases):
    """Loaded edge follows force on each member, including the opposite leg force."""
    cross = math.sqrt(1-dot(LEG, RIM)**2)
    row_min = cross_row_minimum(diameter_mm)
    margins = [a-4*diameter_mm, b-4*diameter_mm,
               a*cross-row_min, b*cross-row_min,
               127-a*cross, 127-b*cross]
    for member, grain, sign in (('rim', RIM, 1), ('leg', LEG, -1)):
        normal = (0., grain[2], -grain[1])
        for i, point in enumerate(points):
            offset = [p-c for p, c in zip(point, original_centre, strict=True)]
            q = dot(offset, normal)
            for forces in force_cases:
                f = sign*dot(forces[i], normal)
                positive_required = (4 if f > 1e-9 else 1.5)*diameter_mm
                negative_required = (4 if f < -1e-9 else 1.5)*diameter_mm
                margins.extend((WIDTH/2-q-positive_required, WIDTH/2+q-negative_required))
            if member == 'leg':
                margins.append(177.10543796992-dot(offset, grain)-7*diameter_mm)
            else:
                # Existing minimum rim end clearance is 728 mm. The bounded
                # search displaces bolts less than 200 mm, leaving >7D.
                margins.append(728-math.hypot(offset[1], offset[2])-7*diameter_mm)
    return {'passes':min(margins) >= -1e-8, 'minimum_margin_mm':min(margins),
            'cross_row_minimum_mm':row_min, 'parallel_minimum_mm':4*diameter_mm}


def lateral(forces, diameter_in, pitch_mm):
    cg = group_factor(diameter_in, pitch_mm)
    rows = []
    for force in forces:
        demand = math.hypot(force[1], force[2])
        bearing = []
        for grain in (RIM, LEG):
            cosine2 = min(1., dot(force, grain)**2/demand**2) if demand else 0.
            perpendicular = 6100*.5**1.45/math.sqrt(diameter_in)
            bearing.append(5600*perpendicular/(5600*(1-cosine2)+perpendicular*cosine2))
        d = diameter_in
        result = single_shear(main_length_in=1.5, side_length_in=1.5,
            main_bearing_lb_in=bearing[0]*d, side_bearing_lb_in=bearing[1]*d,
            main_yield_moment_lb_in=45000*d**3/6,
            side_yield_moment_lb_in=45000*d**3/6, gap_in=0.,
            reduction_terms={'Im':5., 'Is':5., 'II':4.5, 'IIIm':4., 'IIIs':4., 'IV':4.})
        capacity = result['reference_lateral_lbf']*4.4482216152605*cg
        rows.append({'force_xyz_n':force, 'demand_n':demand, 'reference_n':capacity,
                     'ratio':demand/capacity, 'mode':result['governing_mode']})
    return {'bolts':rows, 'group_factor':cg, 'peak_ratio':max(r['ratio'] for r in rows)}


def context():
    source = json.loads(SOURCE.read_text())
    for path, expected in source['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Assessment source changed: '+path)
    with tarfile.open(BUNDLE, 'r:gz') as archive:
        native = json.load(archive.extractfile('report.json'))
    old_points = [native['physical_connection_forces'][f'lumber_leg_bolt_left_{i}']['point']
                  for i in range(1, 5)]
    centre = [sum(p[k] for p in old_points)/4 for k in range(3)]
    mass = json.loads(MASS.read_text())
    for record in (native, mass):
        for path, expected in record['source_sha256'].items():
            if path.startswith('mini_moonboard/') and hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise ValueError('CAD source changed: '+path)
    leg = next(p for p in mass['mass_inventory'] if p['name'] == 'lumber_leg_left')
    return source, centre, leg


def candidate(d, a, b, sl, sr, source, centre, leg):
    points = pattern(centre, a, b, sl, sr)
    top = [sum(p[k] for p in points)/4 for k in range(3)]
    cases = []
    forces = []
    for case in source['full_contact_cases']:
        moment = foot_joint_moment(compression_n=case['axial_compression_n'], top=top,
            foot=case['foot_pressure_resultant_xyz_mm'], leg_mass_kg=leg['mass_kg'],
            leg_centre=leg['centre_xyz_mm'])
        force = bolt_forces(points, case['axial_compression_n'], moment)
        forces.append(force)
        cases.append({'joint_moment_nmm':moment, 'compression_n':case['axial_compression_n']})
    geo = geometry(points, centre, d*25.4, a, b, forces)
    if not geo['passes']:
        return None
    for case, force in zip(cases, forces, strict=True):
        case.update(lateral(force, d, max(a, b)))
    return {'diameter_in':d, 'leg_pitch_mm':a, 'rim_pitch_mm':b,
            'shift_leg_mm':sl, 'shift_rim_mm':sr, 'points_xyz_mm':points,
            'geometry':geo, 'cases':cases, 'peak_lateral_ratio':max(c['peak_ratio'] for c in cases)}


def build():
    source, centre, leg = context()
    results = []
    for d in (.375, .4375, 12/25.4, .5, .625):
        count, best, examined = 0, None, 0
        for a in range(38, 111, 2):
            for b in range(38, 111, 2):
                cross = math.sqrt(1-dot(LEG, RIM)**2)
                if min(a, b) < 4*d*25.4 or min(a, b)*cross < cross_row_minimum(d*25.4):
                    continue
                for sl in range(-24, 25, 4):
                    for sr in range(-24, 25, 4):
                        examined += 1
                        value = candidate(d, a, b, sl, sr, source, centre, leg)
                        if value:
                            count += 1
                            if best is None or value['peak_lateral_ratio'] < best['peak_lateral_ratio']:
                                best = value
        results.append({'diameter_in':d, 'examined_count':examined,
                        'geometry_passing_count':count, 'best':best})
    paths = [Path(__file__), SOURCE, BUNDLE, MASS, Path('fea/dowel_yield.py'),
             Path('fea/leg_completion_assessment.py'), Path('fea/leg_attachment_check.py'),
             Path('fea/leg_only_load_check.py')]
    return {'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'search_grid':{'pitches_mm':[38,110,2], 'centre_shifts_mm':[-24,24,4]},
            'original_centre_xyz_mm':centre, 'results':results,
            'qualified_for_construction':False,
            'limits':['Same 38.1 by 139.7 mm leg and rim, fresh-build bores only.',
                      'Original full-contact forces retained; moments recomputed about moved centroid.',
                      'Force-dependent loaded edges, 4D parallel pitch, 7D leg end screen.',
                      'Smooth shank over both members; Fyb >=45 ksi assumed.',
                      'Lateral and spacing search only; net sections, splitting, prying and hardware fit remain separate.']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result['results'], indent=2))
