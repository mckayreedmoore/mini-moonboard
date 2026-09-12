"""Preliminary wider single-stock leg search; no construction qualification."""
import hashlib
import json
import math
from pathlib import Path

from fea.leg_attachment_check import LEG, RIM
from fea.leg_bolt_pattern_search import (
    SOURCE,
    bolt_forces,
    context,
    cross_row_minimum,
    dot,
    lateral,
    pattern,
)
from fea.leg_completion_assessment import foot_joint_moment
from fea.leg_only_load_check import MASS


def load_cases(depth_mm, source, leg, rim_depth_mm=139.7):
    """Keep centreline and add both legs' extra dead weight at their old CG."""
    front = -270.95
    old_cases = source['full_contact_cases']
    foot = [sum(c['foot_pressure_resultant_xyz_mm'][i] for c in old_cases)/2 for i in range(3)]
    extra_mass = 2*leg['mass_kg']*(depth_mm/139.7-1)
    numerator = source['axial_compression_n']*(foot[1]-front)
    numerator += extra_mass*9.80665*(leg['centre_xyz_mm'][1]-front)/LEG[2]
    if rim_depth_mm != 139.7:
        inventory = json.loads(MASS.read_text())['mass_inventory']
        for part in inventory:
            if part['name'] in ('base_side_left', 'base_side_right'):
                extra = part['mass_kg']*(rim_depth_mm/139.7-1)
                numerator += extra*9.80665*(part['centre_xyz_mm'][1]-front)/LEG[2]
    result = []
    for sign in (-1, 1):
        point = [foot[0], foot[1]+sign*depth_mm/(6*LEG[2]), 0.]
        result.append({'foot':point, 'compression_n':numerator/(point[1]-front)})
    return result


def geometry(points, centre, diameter, a, b, forces, depth_mm, rim_depth_mm=139.7):
    cross = math.sqrt(1-dot(LEG, RIM)**2)
    row_min = cross_row_minimum(diameter)
    margins = [a-4*diameter, b-4*diameter, a*cross-row_min,
               b*cross-row_min, 127-a*cross, 127-b*cross]
    for name, grain, sign, depth in (('rim', RIM, 1, rim_depth_mm), ('leg', LEG, -1, depth_mm)):
        normal = (0., grain[2], -grain[1])
        for i, point in enumerate(points):
            offset = [p-c for p, c in zip(point, centre, strict=True)]
            q = dot(offset, normal)
            for case in forces:
                f = sign*dot(case[i], normal)
                margins.extend((depth/2-q-(4 if f > 1e-9 else 1.5)*diameter,
                                depth/2+q-(4 if f < -1e-9 else 1.5)*diameter))
            end = (177.10543796992-dot(offset, grain) if name == 'leg'
                   else 728-math.hypot(offset[1], offset[2]))
            margins.append(end-7*diameter)
    return min(margins)


def candidate(depth, d, a, b, sl, sr, centre, leg, loads, rim_depth=139.7):
    points = pattern(centre, a, b, sl, sr)
    top = [sum(p[k] for p in points)/4 for k in range(3)]
    cases, forces = [], []
    for load in loads:
        moment = foot_joint_moment(compression_n=load['compression_n'], top=top,
            foot=load['foot'], leg_mass_kg=leg['mass_kg']*depth/139.7,
            leg_centre=leg['centre_xyz_mm'])
        forces.append(bolt_forces(points, load['compression_n'], moment))
        cases.append({'compression_n':load['compression_n'], 'moment_nmm':moment})
    margin = geometry(points, centre, d*25.4, a, b, forces, depth, rim_depth)
    if margin < 2:
        return None
    for case, force in zip(cases, forces, strict=True):
        case.update(lateral(force, d, max(a, b)))
    return {'leg_depth_mm':depth, 'rim_depth_mm':rim_depth, 'diameter_in':d,
            'leg_pitch_mm':a, 'rim_pitch_mm':b, 'shift_leg_mm':sl, 'shift_rim_mm':sr,
            'minimum_placement_margin_mm':margin, 'points_xyz_mm':points,
            'peak_lateral_ratio':max(c['peak_ratio'] for c in cases), 'cases':cases}


def build(*, wider_rim=False, extended=False):
    source, centre, leg = context()
    results = []
    for depth in ((234.95,) if extended else (184.15, 234.95)):
        rim_depth = depth if wider_rim else 139.7
        loads = load_cases(depth, source, leg, rim_depth)
        for d in ((.625, .75) if extended else (.5, .625)):
            best, count, examined = None, 0, 0
            for a in range(52, 153 if extended else 141, 4):
                for b in range(52, 153 if extended else 141, 4):
                    cross = math.sqrt(1-dot(LEG, RIM)**2)
                    if min(a, b) < 4*d*25.4+2 or min(a, b)*cross < cross_row_minimum(d*25.4)+2:
                        continue
                    for sl in range(-48 if extended else -32, 49 if extended else 33, 4):
                        for sr in range(-48 if extended else -32, 49 if extended else 33, 4):
                            examined += 1
                            value = candidate(depth, d, a, b, sl, sr, centre, leg, loads, rim_depth)
                            if value:
                                count += 1
                                if best is None or value['peak_lateral_ratio'] < best['peak_lateral_ratio']:
                                    best = value
            row = {'leg_depth_mm':depth, 'rim_depth_mm':rim_depth, 'diameter_in':d, 'examined_count':examined,
                   'geometry_passing_count':count, 'best':best}
            results.append(row)
            print(json.dumps({k:v for k,v in row.items() if k != 'best'}), flush=True)
    paths = [Path(__file__), SOURCE, Path('fea/leg_bolt_pattern_search.py')]
    return {'results':results, 'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'qualified_for_construction':False, 'minimum_placement_margin_mm':2,
            'search_grid':{'pitch_mm':[52,152 if extended else 140,4], 'shift_mm':[-48,48,4] if extended else [-32,32,4]},
            'limits':['Legs and rim remain 38.1 mm thick; rim depth is recorded per result.',
                      'Centreline unchanged; wider stock increases the full-contact pressure-resultant range.',
                      'Extra leg and optional rim mass scales with width at existing CG; existing top end retained.',
                      'Original smaller-section group stiffness retained as a conservative approximation.',
                      'Smooth shank and Fyb >=45 ksi assumed. No custom steel components.',
                      'Lateral/placement screening only: member net sections, splitting, prying and stack fit remain unverified.']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wider-rim', action='store_true')
    parser.add_argument('--extended', action='store_true')
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(wider_rim=args.wider_rim, extended=args.extended), indent=2, allow_nan=False)+'\n')
