"""Split-center versus prior vertical framing: independent panel shell surrogates.

Four separate undrilled homogeneous isotropic panels, ideal normal point
restraints at actual screw axes, and eight independent outward normal-load projections of the 300 lb sensitivity.
The 20x20 mm square patches are numerical comparison loads, not physical hold
seats. No backing contact, frame flexibility, panel seam tie or actual plywood
strength is established. Tangential load and the 100 mm standoff couple are excluded.
Numerical convergence never means construction approval.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path

from fea import vertical_panel_comparison as shell
from mini_moonboard import panel_grid_v2

PATCH_WIDTH = 20.
CASES = (
    ('lower', 'left', 'D6', 'horizontal'), ('upper', 'left', 'D7', 'horizontal'),
    ('lower', 'right', 'H6', 'horizontal'), ('upper', 'right', 'H7', 'horizontal'),
    ('lower', 'left', 'F3', 'vertical'), ('upper', 'left', 'F10', 'vertical'),
    ('lower', 'right', 'G3', 'vertical'), ('upper', 'right', 'G10', 'vertical'),
)


def prepare_panel(module, case, size):
    band, side, label, family = case
    if case not in CASES:
        raise ValueError('Unspecified comparison case')
    b = module.b
    name = f'main_{band}_{side}'
    low, high = (0., b.HALF) if band == 'lower' else (b.HALF, b.LENGTH)
    left, right = (-b.HALF, 0.) if side == 'left' else (0., b.HALF)
    x, y = panel_grid_v2.main_tnut_datums()[label]
    x -= b.HALF
    patch = (x-PATCH_WIDTH/2, x+PATCH_WIDTH/2, y-PATCH_WIDTH/2, y+PATCH_WIDTH/2)
    if not (left < patch[0] < patch[1] < right and low < patch[2] < patch[3] < high):
        raise ValueError('Hypothetical load patch crosses panel boundary')
    along = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    screws = [c for c in module.connections() if isinstance(c, module.timber.PanelScrew) and c.members[0] == name]
    points = [(c.name, c.start.x, (c.start-b.point(0, 0, 0)).dot(along)) for c in screws]
    if len(points) < 3 or any(abs(c.length-50.8) > 1e-6 for c in screws):
        raise ValueError('Unexpected panel screw inventory')
    xs = shell.mesh_axes(left, right, size, [p[1] for p in points]+list(patch[:2]))
    ys = shell.mesh_axes(low, high, size, [p[2] for p in points]+list(patch[2:]))
    nodes, elements, lookup = shell.grid(xs, ys)
    screw_nodes = {name: lookup[round(x, 8), round(y, 8)] for name, x, y in points}
    if len(set(screw_nodes.values())) != len(points):
        raise ValueError('Coincident ideal screw restraints')
    constraints = [(tag, 3) for tag in screw_nodes.values()]
    constraints += [(lookup[round(left, 8), round(low, 8)], d) for d in (1, 2)]
    constraints += [(lookup[round(right, 8), round(low, 8)], 2)]
    outward = -b.normal()
    load_cases = {}
    for pounds in (250, 300):
        world = [0., 300., -2*pounds*.45359237*9.80665]
        load_cases[str(pounds)] = {'world_force_n': world,
            'outward_normal_projection_n': sum(a*z for a, z in zip(world, outward.toTuple(), strict=True))}
    force = load_cases['300']['outward_normal_projection_n']
    if force <= 0:
        raise ValueError('Expected outward normal projection')
    loads, area = shell.pressure_load(nodes, elements, patch, force)
    if set(loads) & set(screw_nodes.values()):
        raise ValueError('Load patch overlaps ideal screw restraint')
    horizontal = sorted((t for t, p in nodes.items() if abs(p[1]-b.HALF) < 1e-6), key=lambda t: nodes[t][0])
    vertical = sorted((t for t, p in nodes.items() if abs(p[0]) < 1e-6), key=lambda t: nodes[t][1])
    return {'candidate': module.KEY, 'panel': name, 'case_id': label, 'load_family': family,
            'band': band, 'side': side, 'mesh_max_mm': size, 'nodes': nodes, 'elements': elements,
            'constraints': constraints, 'loads': loads, 'screw_nodes': screw_nodes,
            'modulus_mpa': shell.E, 'poisson_ratio': shell.NU, 'thickness_mm': shell.THICKNESS,
            'patch_mm': patch, 'patch_area_mm2': area, 'hold_datum_panel_xy_mm': [x, y],
            'patch_basis': 'Hypothetical 20x20 mm square at actual grid datum; not actual hold/T-nut footprint',
            'outward_world_axis': list(outward.toTuple()), 'projected_load_cases': load_cases,
            'applied_normal_force_n': force, 'applied_climber_lb_sensitivity': 300,
            'load_limits': 'Normal component only of twice-weight downward plus300 N world+Y; no tangential force or100 mm standoff couple.300 lb is sensitivity,250 lb requested maximum. Not a complete load envelope',
            'linear_250_over_300_scale': load_cases['250']['outward_normal_projection_n']/force,
            'seam_nodes': horizontal, 'vertical_seam_nodes': vertical}


def assess(record, data):
    """Replay checked force/moment audit and both original-node edge profiles."""
    result = shell.assess(record, data)
    u = shell.read_blocks(data)['displacements']
    horizontal = result.pop('seam_profile')
    vertical = [[record['nodes'][t][1], u[t][2]] for t in record['vertical_seam_nodes']]
    result.update(horizontal_seam_profile=horizontal, vertical_seam_profile=vertical,
                  max_abs_horizontal_seam_displacement_mm=max(abs(p[1]) for p in horizontal),
                  max_abs_vertical_seam_displacement_mm=max(abs(p[1]) for p in vertical),
                  max_abs_ideal_screw_reaction_n=max(abs(v) for v in result['ideal_screw_normal_reactions_n'].values()),
                  screw_reaction_basis='Ideal point-restraint diagnostic, not a strength or convergence acceptance criterion')
    return result


def run_panel(record, directory):
    result = shell.run(record, directory)
    result = {**assess(record, (directory/'panel.dat').read_text()),
              'evidence_sha256': result['evidence_sha256']}
    (directory/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


def comparison_summary(cases, baseline, revised):
    expected = {(candidate, case[2], size) for candidate in (baseline, revised)
                for case in CASES for size in shell.SIZES}
    indexed = {(r['candidate'], r['case_id'], r['mesh_mm']): r for r in cases}
    if len(indexed) != len(cases) or set(indexed) != expected:
        raise ValueError('Require all 32 distinct variant/case/resolution rows')
    checks, ratios = [], []
    metrics = ('compliance_mm_per_n', 'max_abs_horizontal_seam_displacement_mm',
               'max_abs_vertical_seam_displacement_mm')
    passed = {}
    for candidate in (baseline, revised):
        for _, _, label, _ in CASES:
            coarse, fine = (indexed[candidate, label, size] for size in shell.SIZES)
            changes = {key: abs(coarse[key]-fine[key])/max(abs(fine[key]), 1e-12) for key in metrics}
            passed[candidate, label] = max(changes.values()) <= .05
            checks.append({'candidate': candidate, 'case_id': label, 'relative_changes': changes,
                           'passes_5_percent_refinement': passed[candidate, label]})
    for _, _, label, _ in CASES:
        if passed[baseline, label] and passed[revised, label]:
            a, z = (indexed[candidate, label, min(shell.SIZES)] for candidate in (baseline, revised))
            ratios.append({'case_id': label, 'revised_over_baseline_surrogate_ratios':
                           {key: z[key]/a[key] if abs(a[key]) > 1e-12 else None for key in metrics}})
    return {'numerical_comparison_accepted': all(passed.values()), 'refinement_checks': checks,
            'accepted_case_surrogate_ratios': ratios,
            'ratio_policy': 'Each case ratio requires both variants to pass all three refinement metrics; omitted cases remain unresolved',
            'qualified_for_design': False, 'actual_panel_qualified': False,
            'gusset_force_reduction_established': False,
            'seam_interpretation': 'Each loaded panel is independent; its unloaded neighbor remains zero. Each profile is the same-case ideal seam displacement jump. Different load cases are not combined.'}


def source_hashes():
    paths = [Path(__file__), Path(shell.__file__), *sorted(Path('mini_moonboard').glob('*.py')),
             *[Path(p) for p in ('docs/ml24z-reference.json', 'docs/panel-insert-reference.json',
                                 'docs/selective-stock-reference.json')]]
    return {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revised-module', default='mini_moonboard.split_center_frame')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite shell comparison evidence')
    from mini_moonboard import vertical_principal_frame as baseline
    revised = importlib.import_module(args.revised_module)
    sources = source_hashes()
    report = {'limits': __doc__, 'source_sha256': sources, 'solver_image': shell.IMAGE,
              'baseline': baseline.KEY, 'revised': revised.KEY, 'qualified_for_design': False,
              'actual_panel_qualified': False, 'gusset_force_reduction_established': False,
              'benchmark': shell.run(shell.benchmark(), args.output/'benchmark'), 'cases': []}
    for module in (baseline, revised):
        for case in CASES:
            for size in shell.SIZES:
                record = prepare_panel(module, case, size)
                name = f'{module.KEY}-{case[2]}-{size:g}'
                result = run_panel(record, args.output/name)
                report['cases'].append({'candidate': module.KEY, 'case_id': case[2],
                    'panel': record['panel'], 'load_family': case[3], 'mesh_mm': size,
                    'patch_mm': record['patch_mm'], 'projected_load_cases': record['projected_load_cases'],
                    'applied_normal_force_n': record['applied_normal_force_n'],
                    'linear_250_over_300_scale': record['linear_250_over_300_scale'], **result})
                print(name, result['normal_patch_average_displacement_mm'], flush=True)
    report['comparison'] = comparison_summary(report['cases'], baseline.KEY, revised.KEY)
    if source_hashes() != sources:
        raise ValueError('Source changed during shell comparison; results not accepted')
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
