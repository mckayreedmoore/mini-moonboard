"""Conditional four-bolt leg-joint envelope, independent of frame spring forces.

The imposed sagittal joint moment and rear-load share are explicit inputs.
The envelope does not infer either from an uncalibrated frame stiffness model.
"""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.reinforced_timber_resistance import (
    adjusted_reference,
    conditional_dowel_reference,
)

LEG = (0., -.26015745792854417, .9655662054381139)
RIM = (0., .6427876096865427, .7660444431189752)
BUNDLE = Path('fea/results/reinforced-F10-k1000-v4.tar.gz')
GEOMETRY = Path('fea/results/reinforced-timber-resistance-v3.json')


def bolt_group(points, compression_n, moment_x_nmm=0.):
    """Identical isotropic elastic dowels in a rigid planar group; no slip credit.

    Forces are on the rim. Moment is about the four-bolt centroid. The member's
    19.05 mm single-lap eccentricity is separate, not an extra sagittal moment.
    """
    if (len(points) != 4 or any(len(p) != 3 for p in points)
            or not all(math.isfinite(x) for p in points for x in p)
            or not all(math.isfinite(x) for x in (compression_n, moment_x_nmm))
            or compression_n < 0):
        raise ValueError('Require four finite XYZ points and finite nonnegative compression')
    cy, cz = (sum(p[k] for p in points)/4 for k in (1, 2))
    polar = sum((p[1]-cy)**2+(p[2]-cz)**2 for p in points)
    if polar <= 0:
        raise ValueError('Coincident group points')
    rows = []
    for point in points:
        y, z = point[1]-cy, point[2]-cz
        force = (0., compression_n*LEG[1]/4-moment_x_nmm*z/polar,
                 compression_n*LEG[2]/4+moment_x_nmm*y/polar)
        lateral = math.hypot(force[1], force[2])
        bearing = []
        for grain in (RIM, LEG):
            cosine2 = min(1., sum(a*b for a, b in zip(force, grain, strict=True))**2/lateral**2) if lateral else 0.
            bearing.append(5600*3650/(5600*(1-cosine2)+3650*cosine2))
        reference = conditional_dowel_reference(False, *bearing)
        rows.append({'point_xyz_mm':point, 'force_on_rim_xyz_n':force,
                     'lateral_n':lateral, 'reference_n':reference['adjusted_lateral_n'],
                     'ratio':lateral/reference['adjusted_lateral_n']})
    ref = adjusted_reference(139.7)
    parallel = {}
    for member, grain, pitch, spread in (('leg', LEG, 70., 40.9973084),
                                         ('rim', RIM, 50., 57.3962318)):
        demand = sum(abs(sum(a*b for a,b in zip(r['force_on_rim_xyz_n'],grain,strict=True))) for r in rows)
        capacities = [ref['Ft_mpa']*38.1*(139.7-2*11.1125),
                      2*ref['Fv_mpa']*38.1*pitch,
                      2*ref['Fv_mpa']*38.1*pitch+ref['Ft_mpa']*38.1*(spread-11.1125)]
        parallel[member] = {'absolute_parallel_n':demand, 'conservative_reference_n':min(capacities),
                            'ratio':demand/min(capacities)}
    return {'compression_n':compression_n, 'imposed_sagittal_moment_nmm':moment_x_nmm,
            'bolts':rows,'peak_lateral_ratio':max(r['ratio'] for r in rows),
            'parallel_local_checks':parallel,
            'lateral_and_parallel_criteria_met':max([r['ratio'] for r in rows]+
                [r['ratio'] for r in parallel.values()]) <= 1.}


def moment_limit(points, compression_n, sign):
    """First reference crossing in one moment direction; not physical failure."""
    if sign not in (-1, 1):
        raise ValueError('Moment sign must be -1 or +1')
    if not bolt_group(points, compression_n)['lateral_and_parallel_criteria_met']:
        return None
    low, high = 0., 1.e6
    for _ in range(55):
        mid = (low+high)/2
        if bolt_group(points, compression_n, sign*mid)['lateral_and_parallel_criteria_met']:
            low = mid
        else:
            high = mid
    return sign*low


def build(load_path):
    load_path = Path(load_path)
    loads = json.loads(load_path.read_text())
    for path, expected in loads['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Load evidence source changed: '+path)
    with tarfile.open(BUNDLE, 'r:gz') as archive:
        native = json.load(archive.extractfile('report.json'))
    for path, expected in native['source_sha256'].items():
        if path.startswith('mini_moonboard/') and hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Native joint geometry source changed: '+path)
    points = [native['physical_connection_forces'][f'lumber_leg_bolt_left_{i}']['point'] for i in range(1,5)]
    geometry_record = json.loads(GEOMETRY.read_text())
    for path, expected in geometry_record['source_sha256'].items():
        if path.startswith('mini_moonboard/') and hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Distance geometry source changed: '+path)
    distances = [r for r in geometry_record['geometry']['bolt_member_distances']
                 if r['bolt'].startswith('lumber_leg_bolt_')]
    if len(distances) != 16:
        raise ValueError('Require eight bolts each with two wood-member distance records')
    case = next(c for c in loads['cases'] if c['climber_lb'] == 250 and c['vertical_multiplier'] == 2)
    total = case['entire_rear_compression_assigned_to_one_leg_n']
    pitches, spreads = [], []
    for grain, pairs in ((LEG, ((0,2),(1,3))), (RIM, ((0,1),(2,3)))):
        along = [sum(a*b for a,b in zip(p,grain,strict=True)) for p in points]
        across = [p[1]*grain[2]-p[2]*grain[1] for p in points]
        pitches.append(min(abs(along[a]-along[b]) for a,b in pairs))
        row_centers = [sum(across[i] for i in pair)/2 for pair in pairs]
        spreads.append(abs(row_centers[0]-row_centers[1]))
    scenarios = []
    for share in (.5, .75, 1.):
        force = total*share
        scenarios.append({'rear_compression_share':share, **bolt_group(points,force),
            'conditional_sagittal_moment_interval_nmm':
                [moment_limit(points,force,s) for s in (-1,1)]})
    unit = bolt_group(points,1.)
    axial_reference = 1/unit['peak_lateral_ratio']
    paths = (Path(__file__),load_path,BUNDLE,GEOMETRY,Path('fea/reinforced_timber_resistance.py'),Path('fea/dowel_yield.py'))
    return {'candidate':loads['candidate'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'geometry':{'distances':distances,'all_end_7D_edge_4D_pass':all(r['minimum_end_7D_pass'] and r['minimum_edge_4D_pass'] for r in distances),
            'leg_rim_parallel_pitch_mm':pitches, 'leg_rim_row_spread_mm':spreads,
            'minimum_parallel_pitch_4D_mm':38.1,'minimum_cross_grain_pitch_mm':35.71875,
            'maximum_cross_grain_spread_mm':127.,
            'spacing_pass':min(pitches) >= 38.1 and min(spreads) >= 35.71875 and max(spreads) <= 127.},
        'total_rear_compression_n':total,'pure_axial_conditional_group_reference_n':axial_reference,
        'maximum_share_at_zero_imposed_moment':axial_reference/total,
        'scenarios':scenarios,'assembly_qualified':False,
        'limits':[
            'Four identical elastic bolts, rigid in-plane group; actual clearance/contact can redistribute forces.',
            'Root diameter .298 inch throughout; Fyb at least45ksi required but current A307 designation does not establish it.',
            'CD=CM=Ct=Cdelta=1; conservative four-fastener Cg retained; no tightening friction credited.',
            'Actual load share and sagittal joint moment are not inferred; displayed shares and moment intervals are conditional comparisons.',
            'Single-lap face eccentricity remains in the separate member check; this is not an axial bolt/washer or prying assessment.',
            'Distances and AppendixE parallel-grain checks do not establish perpendicular-to-grain splitting resistance in the rim.',
            'No installed failure weight or larger-leg requirement follows from exceeding a conditional comparison.']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loads',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(build(args.loads),stream,indent=2,allow_nan=False)
        stream.write('\n')
