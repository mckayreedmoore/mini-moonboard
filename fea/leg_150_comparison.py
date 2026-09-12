"""Matched 150 lb leg sensitivities; these are not construction or user ratings."""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.leg_attachment_check import BUNDLE, bolt_group
from fea.leg_completion_assessment import foot_joint_moment, splitting_screen
from fea.leg_member_capacity import leg_check
from fea.leg_only_load_check import MASS
from fea.leg_smooth_bolt_check import smooth_bolt_group
from fea.round_structural_global_envelope import locations
from fea.wider_leg_assessment import evaluate
from fea.wider_leg_limits import connection_metrics, force_cases, full_context, prepare


def old_prepare():
    from mini_moonboard import round_reinforcement_frame as model
    cad = json.loads(MASS.read_text())
    for path, expected in cad['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Old mass evidence stale: ' + path)
    with tarfile.open(BUNDLE, 'r:gz') as archive:
        native = json.load(archive.extractfile('report.json'))
    for path, expected in native['source_sha256'].items():
        if path.startswith('mini_moonboard/') and hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Old joint geometry stale: ' + path)
    points = [native['physical_connection_forces'][f'lumber_leg_bolt_left_{i}']['point'] for i in range(1, 5)]
    top = [sum(p[k] for p in points)/4 for k in range(3)]
    leg = next(r for r in cad['mass_inventory'] if r['name'] == 'lumber_leg_left')
    polygon = next(r['vertices_mm'] for r in cad['selected_floor_support_bodies'] if r['name'] == 'lumber_leg_left')
    foot = [sum(p[k] for p in polygon)/len(polygon) for k in range(3)]
    holds = list(locations(model))
    equipment_y = max(p[1]+offset*n[1] for _, p, n in holds for offset in (0., 100.))
    mass = cad['state']['mass_kg']+25.
    dead_y = (cad['state']['mass_kg']*cad['state']['centre_xyz_mm'][1]+25.*equipment_y)/mass
    return {'points': points, 'top': top, 'leg': leg, 'foot': foot, 'holds': holds,
            'half': (max(p[1] for p in polygon)-min(p[1] for p in polygon))/2,
            'mass': mass, 'dead_y': dead_y,
            'span': math.hypot(top[1]-foot[1], top[2]-foot[2])}


def old_metrics(data, compression, foot_y):
    moment = foot_joint_moment(compression_n=compression, top=data['top'], foot=[data['foot'][0], foot_y, 0.],
                              leg_mass_kg=data['leg']['mass_kg'], leg_centre=data['leg']['centre_xyz_mm'])
    original = bolt_group(data['points'], compression, moment)
    smooth = smooth_bolt_group(data['points'], compression, moment)
    member = leg_check(compression, effective_length_mm=data['span'], additional_strong_moment_nmm=abs(moment))
    return {'leg_member': member['NDS_3_9_3_interaction'],
            'current_thread_root_lateral': original['peak_lateral_ratio'],
            'smooth_3_8_lateral': smooth['peak_lateral_ratio'],
            'parallel_local': max(v['ratio'] for v in original['parallel_local_checks'].values()),
            'supplemental_rim_splitting': splitting_screen([b['force_xyz_n'] for b in smooth['bolts']])['ratio']}, moment


def scenario(data, name, share, offset, context=None):
    foot_y = data['foot'][1]+offset
    rows = []
    for load in force_cases(data, 150., foot_y, share):
        if context is None:
            metrics, moment = old_metrics(data, load['compression_n'], foot_y)
        else:
            result = evaluate(data['cad'], data['points'], context, load['compression_n'], [data['foot'][0], foot_y, 0.])
            metrics, moment = result['metrics'], result['joint_moment_nmm']
            revised = connection_metrics(data, load['compression_n'], foot_y, exact_angle=True)
            metrics['exact_angle_lateral'] = revised['lateral']
            metrics['exact_angle_combined_connection'] = revised['conservative_lateral_plus_axial']
        rows.append({'metrics': metrics, 'load': load, 'moment_nmm': moment})
    peaks = {key: max(rows, key=lambda r:r['metrics'][key]) for key in rows[0]['metrics']}
    return {'candidate': name, 'rear_load_share': share, 'offset_mm': offset,
            'peak_metrics': {key:value['metrics'][key] for key, value in peaks.items()},
            'witnesses': peaks, 'unique_load_cases': len(rows)}


def build():
    old, new = old_prepare(), prepare()
    context = full_context(new)
    rows = []
    for name, data, ctx in (('2x6_four_bolt', old, None), ('2x8_six_bolt', new, context)):
        for share in (1., .5):
            for pressure, factor in (('front_edge', -1.), ('middle_third_front', -1/3), ('center', 0.),
                                     ('middle_third_rear', 1/3), ('rear_edge', 1.)):
                row = scenario(data, name, share, factor*data['half'], ctx)
                row['pressure_resultant'] = pressure
                rows.append(row)
    paths = [Path(__file__), MASS, BUNDLE, Path('docs/wider-leg-review/review.json'),
             *[Path('fea')/(p+'.py') for p in ('leg_attachment_check', 'leg_member_capacity',
                'leg_completion_assessment', 'leg_smooth_bolt_check', 'wider_leg_limits',
                'wider_leg_assessment', 'wider_leg_wood_checks', 'dowel_yield', 'reinforced_timber_resistance')],
             Path('mini_moonboard/wider_leg_hardware.py')]
    return {'climber_rating_established': False, 'assumptions': {
        'climber_lb': 150., 'downward_multiplier': 2., 'horizontal_force_n': 300.,
        'standoff_mm': 100., 'equipment_mass_kg': 25., 'support_no_slip_assumed': True,
        '2x6_combined_dead_mass_kg': old['mass'], '2x8_combined_dead_mass_kg': new['mass'],
        '2x6_foot_half_length_mm': old['half'], '2x8_foot_half_length_mm': new['half'],
        '2x6_member_span_mm': old['span'], '2x8_member_span_mm': context['support_span_mm']},
        'method_limits': [
            'Each design retains its own actual mass and geometry; identical additional equipment allowance.',
            'All hold positions, two front-resultant bounds, zero/100 mm standoff and zero/300 N horizontal load are scanned.',
            'One leg receives all or ideal half of the total rear resultant, including dead load; local leg weight is conservatively included again.',
            'Existing 2x6 functions retain conservative historical 1.25 angle reduction, bearing references and thread-root or smooth-bolt assumptions.',
            '2x8 historical ratios and exact-angle sensitivities are both reported; do not treat them as identical methods.',
            '2x6 smooth-bolt entry changes connection resistance only on the original assembly mass; it excludes the historical 1.213 kg hardware increment and is not a complete hardware-variant assessment.',
            'Edge geometry, prying assumptions, plate material and real force/contact distribution are not qualified by these numbers.',
            'These endpoint comparisons are pressure sensitivities, not proof of actual pressure position or a continuous-pressure envelope.'],
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scenarios': rows}


if __name__ == '__main__':
    result = build()
    output = Path('fea/results/leg-150-comparison.json')
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    for row in result['scenarios']:
        print(row['candidate'], row['rear_load_share'], row['pressure_resultant'],
              {k:round(v, 4) for k,v in row['peak_metrics'].items()})
