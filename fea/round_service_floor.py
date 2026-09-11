"""Current round-service CAD mass and finite floor witnesses, not qualification."""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import scipy

from fea.horizontal_service_floor import floor_contact_bodies, select_floor_supports
from fea.horizontal_service_floor import sources as predecessor_sources
from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.selective_floor_screen import LIMITS, current_mass
from fea.split_center_floor import FRICTION, necessary_conditions, verify_loaded_sources
from fea.timber_floor_screen import cases
from fea.user_load_envelope import hull
from fea.wide_structural import locations

OUTPUT = Path("fea/results/round-service-floor-v1.json.gz")


def sources():
    """Used helper closure plus current model, hardware and machining references."""
    return {**predecessor_sources(), **{path: digest(path) for path in (
        'mini_moonboard/round_service_frame.py', 'mini_moonboard/round_service_wiring.py',
        'mini_moonboard/round_panel_hardware.py', 'mini_moonboard/round_panel_layout.py',
        'docs/round-panel-countersink-reference.json',
        'docs/round-service-wiring-reference.json', 'fea/round_service_floor.py')}}


def run(output=OUTPUT):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    hashes = sources()
    from mini_moonboard import round_service_frame as model

    state, inventory = current_mass(model)
    contacts = floor_contact_bodies(model)
    contact_hull = hull([point[:2] for row in contacts for point in row['vertices_mm']])
    if contact_hull != state['support_polygon_mm']:
        raise ValueError('Current contact bodies disagree with integrated support hull')
    supports = select_floor_supports(contacts)
    state['support_polygon_mm'] = hull([point[:2] for row in supports for point in row['vertices_mm']])
    verify_loaded_sources(hashes)
    floor = [[x, y, 0.] for x, y in state['support_polygon_mm']]
    records = []
    for case in cases(state, locations()):
        results = {}
        for mu in FRICTION:
            result = solve(floor, case['wrench_n_nmm'], mu)
            necessary = necessary_conditions(floor, case['wrench_n_nmm'], mu)
            if result['polygon_feasible'] and necessary['circular_cone_infeasibility_proven']:
                raise ValueError("Feasible witness contradicts necessary static conditions")
            result['necessary_conditions'] = necessary
            result['circular_cone_infeasibility_proven'] = necessary['circular_cone_infeasibility_proven']
            results[str(mu)] = result
        records.append({**case, 'friction_results': results})
    if len(records) != 1296:
        raise ValueError("Expected 1296 prescribed finite load cases")
    feasible = [r for record in records for r in record['friction_results'].values() if r['polygon_feasible']]
    summary = {}
    for mu in FRICTION:
        results = [r['friction_results'][str(mu)] for r in records]
        summary[str(mu)] = {
            **dict(Counter(r['status'] for r in results)),
            'circular_cone_infeasibility_proven': sum(r['circular_cone_infeasibility_proven'] for r in results),
            'polygon_infeasible_without_analytic_proof': sum(
                not r['polygon_feasible'] and not r['circular_cone_infeasibility_proven'] for r in results),
            'analytic_failure_reasons': dict(Counter(reason for r in results
                for reason in r['necessary_conditions']['failure_reasons'])),
        }
    report = {'candidate': model.KEY, 'source_sha256': hashes, 'scipy_version': scipy.__version__,
              'state': state, 'mass_inventory': inventory, 'floor_vertices_mm': floor,
              'floor_contact_bodies': contacts,
              'selected_floor_support_bodies': supports,
              'geometric_contact_hull_mm': contact_hull,
              'support_policy': 'Only the four posts and two leg feet receive support credit. '
              'Kicker panel edges are recorded as coplanar geometry but their floor-bearing resistance is unqualified.',
              'electrical_mass_included': False,
              'assumptions': LIMITS+' Separate displayed bulbs, cable and electrical connectors are excluded '
              'because their material masses are unknown. Current enclosed-bore wood and revised countersunk/bolt hardware mass is integrated afresh. '
              'Floor support uses only four posts and two leg feet; coplanar kicker edges receive no support credit. '
              'Analytic necessary conditions additionally identify some failures '
              'that remain impossible with circular friction cones; this proof applies only to the stated rigid model.',
              'qualified_for_design': False, 'structural_analysis_run': False,
              'case_count': len(records), 'summary': summary,
              'witness_validation': {
                  'checked_feasible_witnesses': len(feasible),
                  'maximum_force_residual_n': max((max(map(abs, r['residual_wrench'][:3]))
                                                   for r in feasible), default=None),
                  'maximum_moment_residual_nmm': max((max(map(abs, r['residual_wrench'][3:]))
                                                      for r in feasible), default=None),
                  'minimum_normal_force_n': min((r['minimum_normal_force_n'] for r in feasible), default=None),
                  'maximum_friction_excess_n': max((r['maximum_friction_excess_n'] for r in feasible), default=None)},
              'cases': records}
    if sources() != hashes:
        raise ValueError("Source changed during floor screen")
    verify_loaded_sources(hashes)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(report, allow_nan=False, sort_keys=True)+'\n').encode()
    with output.open('xb') as stream:
        stream.write(gzip.compress(payload, mtime=0))
    print(json.dumps({'candidate': model.KEY, 'mass_kg': state['mass_kg'], 'summary': summary,
                      'witness_validation': report['witness_validation']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    run(parser.parse_args().output)
