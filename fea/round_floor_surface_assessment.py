"""Fresh conditional surface/contact-loss LP cases; no measured floor qualification."""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import scipy

from fea.rigid_floor_screen import solve
from fea.split_center_floor import necessary_conditions
from fea.user_load_envelope import hull

BASE = Path('fea/results/round-insert-floor-v1.json.gz')
OUTPUT = Path('fea/results/round-floor-surfaces-v1.json.gz')
SURFACES = {
    'horse_stall_mats': {'top_mu': .50, 'underlayer_mu': .40, 'degraded_underlayer_mu': .12, 'assumed_thickness_mm': 19.},
    'hardwood_floor': {'top_mu': .30, 'underlayer_mu': None, 'degraded_top_mu': .10, 'assumed_thickness_mm': 0.},
    'carpet': {'top_mu': .40, 'underlayer_mu': .25, 'degraded_underlayer_mu': .10, 'assumed_thickness_mm': 10.},
}
SOURCES = {
    'wood_context': 'https://research.fs.usda.gov/download/treesearch/37440.pdf',
    'mat_installation': 'https://www.greatmats.com/specs/humane/install-horse-stall-mats-straight-edge.pdf',
    'carpet_installation': 'https://pdmsview.shawinc.com/Shaw-Contract-Group-PDMS/SCG-Hard-Surface/Carpet/Cushion-(1)/Cushion-Installation/CushionWorx-Installation-Guidelines',
}
LIMITS = ('Analyst-selected dry-level-floor scenarios, not measured coefficients, product ratings or '
          'validated lower bounds. Layered surfaces use separate upper/lower interface witnesses with no mat/carpet '
          'mass, adhesive, anchorage or tensile credit. Assumed 19mm mat/10mm carpet height translates the lower wrench; same-footprint '
          'idealization omits coupled contact compatibility, shear, peeling, pressure and compliance. Removing '
          'one rear support entirely is a contact-loss sensitivity, not a calibrated carpet/mat '
          'settlement prediction. Saved current mass/CG and 1296 finite raw load wrenches retained; '
          'no new load cases or dynamic simulation. Feasible forces are equilibrium witnesses, '
          'not predicted contact forces or structural/floor approval.')


def effective_friction(values, degraded=False):
    top = values.get('degraded_top_mu', values['top_mu']) if degraded else values['top_mu']
    bottom = values.get('degraded_underlayer_mu', values['underlayer_mu']) if degraded else values['underlayer_mu']
    return top if bottom is None else min(top, bottom)


def interface_wrench(wrench, elevation_mm):
    """Translate upper-surface load wrench to the lower-interface origin."""
    force_x, force_y, force_z, moment_x, moment_y, moment_z = wrench
    return [force_x, force_y, force_z, moment_x-elevation_mm*force_y,
            moment_y+elevation_mm*force_x, moment_z]


def support_points(contacts, unavailable=None):
    names = [row['name'] for row in contacts]
    if len(set(names)) != 6 or (unavailable is not None and unavailable not in names):
        raise ValueError('Require six distinct support bodies and valid unavailable support')
    polygon = hull([v[:2] for row in contacts if row['name'] != unavailable for v in row['vertices_mm']])
    return [[x, y, 0.] for x, y in polygon]


def run(base=BASE, output=OUTPUT):
    base, output = Path(base), Path(output)
    if output.exists():
        raise FileExistsError(output)
    original = json.loads(gzip.decompress(base.read_bytes()))
    if original.get('candidate') != 'round-insert-development' or len(original['cases']) != 1296:
        raise ValueError('Require current insert candidate and complete finite load matrix')
    hashes = {**original['source_sha256'], **{str(p): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (base, Path(__file__), Path('fea/rigid_floor_screen.py'),
                         Path('fea/split_center_floor.py'), Path('fea/user_load_envelope.py'))}}

    def verify():
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha for p, sha in hashes.items()):
            raise ValueError('Floor surface assessment source changed')

    verify()
    contacts = original['selected_floor_support_bodies']
    scenarios = []
    for surface, values in SURFACES.items():
        for label, degraded, unavailable in (
                ('full_nominal', False, None), ('full_degraded_friction', True, None),
                ('left_rear_unavailable', False, 'lumber_leg_left'),
                ('right_rear_unavailable', False, 'lumber_leg_right')):
            top_mu = values.get('degraded_top_mu', values['top_mu']) if degraded else values['top_mu']
            interfaces = [('timber_surface', top_mu, 0.)]
            if values['underlayer_mu'] is not None:
                lower_mu = values.get('degraded_underlayer_mu', values['underlayer_mu']) if degraded else values['underlayer_mu']
                interfaces.append(('surface_subfloor', lower_mu, values['assumed_thickness_mm']))
            for interface, mu, elevation in interfaces:
                points = support_points(contacts, unavailable)
                records = []
                for source in original['cases']:
                    case = {k: v for k, v in source.items() if k != 'friction_results'}
                    case['wrench_n_nmm'] = interface_wrench(case['wrench_n_nmm'], elevation)
                    result = solve(points, case['wrench_n_nmm'], mu)
                    conditions = necessary_conditions(points, case['wrench_n_nmm'], mu)
                    if result['polygon_feasible'] and conditions['circular_cone_infeasibility_proven']:
                        raise ValueError('Feasible witness contradicts analytic impossibility')
                    records.append({**case, 'result': result, 'necessary_conditions': conditions})
                feasible = [r['result'] for r in records if r['result']['polygon_feasible']]
                reasons = Counter(reason for r in records for reason in r['necessary_conditions']['failure_reasons'])
                summary = {
                    'case_count': len(records), 'feasible': len(feasible),
                    'infeasible': len(records)-len(feasible),
                    'analytic_infeasible': sum(r['necessary_conditions']['circular_cone_infeasibility_proven'] for r in records),
                    'analytic_failure_reasons': dict(reasons),
                    'polygon_only_infeasible': sum(not r['result']['polygon_feasible'] and not r['necessary_conditions']['circular_cone_infeasibility_proven'] for r in records),
                    'minimum_resultant_hull_margin_mm': min(min(r['necessary_conditions']['inward_edge_distances_mm']) for r in records),
                    'witness_validation': {
                        'checked': len(feasible),
                        'maximum_force_residual_n': max((max(map(abs, r['residual_wrench'][:3])) for r in feasible), default=None),
                        'maximum_moment_residual_nmm': max((max(map(abs, r['residual_wrench'][3:])) for r in feasible), default=None),
                        'minimum_normal_n': min((r['minimum_normal_force_n'] for r in feasible), default=None),
                        'maximum_friction_excess_n': max((r['maximum_friction_excess_n'] for r in feasible), default=None),
                    },
                }
                scenario = {'surface': surface, 'state': label, 'interface': interface, 'assumed_mu': mu, 'elevation_mm': elevation,
                            'unavailable_support': unavailable, 'floor_points_mm': points,
                            'summary': summary, 'cases': records}
                scenarios.append(scenario)
                print(json.dumps({k: v for k, v in scenario.items() if k not in ('cases', 'floor_points_mm')}), flush=True)
    verify()
    report = {'candidate': original['candidate'], 'source_sha256': hashes,
              'scipy_version': scipy.__version__, 'assumption_sources': SOURCES,
              'assumed_surface_inputs': SURFACES, 'mass_state': original['state'],
              'limitations': LIMITS, 'new_lp_solves': sum(len(s['cases']) for s in scenarios),
              'surface_or_contact_properties_measured': False, 'qualified_for_design': False,
              'scenarios': scenarios}
    payload = (json.dumps(report, allow_nan=False, sort_keys=True)+'\n').encode()
    with output.open('xb') as stream:
        stream.write(gzip.compress(payload, mtime=0))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    run(args.base, args.output)
