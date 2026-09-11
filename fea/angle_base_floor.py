"""Current angle-base CAD mass and floor witnesses; no assumed strength benefit."""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import scipy

from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.selective_floor_screen import LIMITS, current_mass
from fea.split_center_floor import FRICTION, necessary_conditions, verify_loaded_sources
from fea.split_center_floor import sources as predecessor_sources
from fea.timber_floor_screen import cases
from fea.wide_structural import locations

OUTPUT = Path("fea/results/angle-base-floor-v1.json.gz")


def sources():
    """Retained helper/model closure plus the current drilling and floor wrapper."""
    return {**predecessor_sources(), **{path: digest(path) for path in (
        'mini_moonboard/infill_panel_frame.py', 'mini_moonboard/angle_base_frame.py',
        'fea/angle_base_floor.py')}}


def run(output=OUTPUT):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    hashes = sources()
    from mini_moonboard import angle_base_frame as model

    state, inventory = current_mass(model)
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
              'assumptions': LIMITS+' Analytic necessary conditions additionally identify some failures '
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
