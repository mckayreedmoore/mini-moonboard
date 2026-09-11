"""Source-bound split-center rigid-floor feasibility, never structural approval."""
import argparse
import gzip
import json
import math
import sys
from collections import Counter
from pathlib import Path

import scipy

from fea.prepare_easy_structural import digest
from fea.rigid_floor_screen import solve
from fea.selective_floor_screen import LIMITS, current_mass
from fea.timber_floor_screen import cases
from fea.user_load_envelope import hull
from fea.wide_structural import locations

OUTPUT = Path("fea/results/split-center-floor-v1.json.gz")
FRICTION = (.1, .2, .4)
# Transitive model dependencies and the shared helpers actually imported by this
# runner. Keep unrelated candidate/audit/export modules outside the frozen closure.
CAD_SOURCES = (
    '__init__', 'base_frame', 'bearing_frame', 'bolted_frame', 'box_exports', 'box_frame',
    'bracket_mvp', 'clip_frame', 'continuous_frame', 'easy_frame', 'export',
    'footprint_frame', 'hybrid', 'hybrid_frame', 'independent_leg_frame',
    'insert_frame', 'joint_frame', 'lean_frame', 'lumber_leg_frame',
    'lumber_leg_spread_frame', 'model', 'panel_grid', 'panel_grid_v2',
    'product_connections', 'product_frame', 'raster', 'screw_mvp_frame',
    'selected_hardware', 'shallow_frame', 'spacing_frame', 'square_2x6_frame',
    'stability', 'timber_connections', 'timber_frame', 'top_joint_frame',
    'transition_frame', 'wide_frame', 'wood_mvp', 'square_2x6_revised_frame',
    'square_2x6_base_revision', 'single_2x6_frame', 'selective_2x6_frame',
    'paired_rail_frame', 'vertical_principal_frame', 'split_center_frame', 'split_center_hardware',
)
FE_SOURCES = (
    'box_results', 'floor_contact', 'floor_contact_results', 'hybrid_results',
    'prepare_easy_structural', 'rigid_floor_screen', 'selective_floor_screen',
    'solve_bearing_frame', 'solve_easy_frame', 'timber_floor_screen',
    'timber_structural', 'user_load_envelope', 'wide_structural', 'split_center_floor',
)


def sources():
    paths = [*(Path('mini_moonboard')/(name+'.py') for name in CAD_SOURCES),
             *(Path('fea')/(name+'.py') for name in FE_SOURCES),
             Path('docs/ml24z-reference.json'), Path('docs/panel-insert-reference.json'),
             Path('docs/selective-stock-reference.json'), Path('uv.lock')]
    return {str(path): digest(path) for path in sorted(paths)}


def verify_loaded_sources(hashes):
    """Fail closed if the standalone run imports an unrecorded local dependency."""
    root = Path.cwd().resolve()
    missing = []
    for name, module in tuple(sys.modules.items()):
        if not name.startswith(('mini_moonboard', 'fea.')):
            continue
        path = getattr(module, '__file__', None)
        if path and Path(path).resolve().is_relative_to(root):
            relative = str(Path(path).resolve().relative_to(root))
            if relative.endswith('.py') and relative not in hashes:
                missing.append(relative)
    if missing:
        raise ValueError('Unrecorded imported local sources: '+', '.join(sorted(set(missing))))


def necessary_conditions(points, wrench, mu):
    """Necessary circular-Coulomb and compression-only support conditions.

    For a level floor, N=-Fz, sum(x*N_i)=My and sum(y*N_i)=-Mx.
    Thus the normal resultant must lie in the contact hull, and the triangle
    inequality requires hypot(Fx,Fy)<=mu*N. Passing does not establish yaw
    feasibility or any particular reaction distribution.
    """
    if (len(wrench) != 6 or not all(math.isfinite(v) for v in wrench)
            or not math.isfinite(mu) or mu < 0 or len(points) == 0
            or any(len(p) != 3 or not all(math.isfinite(v) for v in p)
                   or abs(p[2]) > 1e-9 for p in points)):
        raise ValueError("Finite floor points, six-component wrench and nonnegative mu required")
    polygon = hull([p[:2] for p in points])
    fx, fy, fz, mx, my, mz = wrench
    normal = -fz
    horizontal = math.hypot(fx, fy)
    force_tolerance = 1e-7*max(1., *map(abs, wrench[:3]))
    distance_tolerance = 1e-7*max(1., *(abs(v) for p in polygon for v in p))
    moment_tolerance = force_tolerance*max(1., *(abs(v) for p in polygon for v in p))
    reasons = []
    if normal < -force_tolerance:
        reasons.append("upward_external_force_requires_floor_tension")
    friction_limit = mu*max(0., normal)
    if horizontal-friction_limit > force_tolerance:
        reasons.append("horizontal_force_exceeds_circular_friction_bound")
    resultant, edge_distances = None, []
    if normal > force_tolerance:
        resultant = [my/normal, -mx/normal]
        for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
            dx, dy = b[0]-a[0], b[1]-a[1]
            edge_distances.append((dx*(resultant[1]-a[1])-dy*(resultant[0]-a[0]))/math.hypot(dx, dy))
        if min(edge_distances) < -distance_tolerance:
            reasons.append("normal_resultant_outside_floor_support_polygon")
    elif normal == 0. and max(abs(mx), abs(my), abs(mz)) > moment_tolerance:
        # With exactly zero total compression every point normal and every
        # Coulomb tangential reaction is zero. No floor moment is available.
        reasons.append("zero_normal_force_cannot_balance_external_moment")
    return {"required_total_normal_n": normal, "horizontal_force_n": horizontal,
            "circular_friction_limit_n": friction_limit,
            "horizontal_friction_excess_n": horizontal-friction_limit,
            "normal_resultant_xy_mm": resultant,
            "inward_edge_distances_mm": edge_distances,
            "force_tolerance_n": force_tolerance,
            "distance_tolerance_mm": distance_tolerance,
            "moment_tolerance_nmm": moment_tolerance,
            "circular_cone_infeasibility_proven": bool(reasons), "failure_reasons": reasons,
            "limits": "Necessary conditions only; passing does not prove circular-cone or yaw feasibility."}


def run(output=OUTPUT):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite published floor-screen evidence")
    hashes = sources()
    from mini_moonboard import split_center_frame as model

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
