"""Ideal point-supported shell comparison; no real panel or frame qualification.

Each panel is independent, homogeneous isotropic and undrilled. Screw axes fix
normal translation only; no backing, rail stiffness or seam moment transfer is
assumed. Positive local Z is outward from the climbing face. Reactions are ideal
support demands, not qualified individual screw or frame joint forces.
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from itertools import pairwise
from pathlib import Path

IMAGE = 'sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646'
E, NU, THICKNESS, FORCE = 7000., .3, 18.25625, 1200.
SIZES = (40., 25.)
PATCH_WIDTH = 40.


def mesh_axes(lo, hi, size, landmarks=()):
    """Subdivide landmark intervals; preserve exact screw/patch coordinates."""
    if not all(math.isfinite(v) for v in (lo, hi, size, *landmarks)) or hi <= lo or size <= 0:
        raise ValueError('Finite increasing bounds and positive mesh size required')
    if any(v < lo-1e-7 or v > hi+1e-7 for v in landmarks):
        raise ValueError('Landmark outside panel')
    fixed = sorted({round(v, 8) for v in (lo, hi, *landmarks)})
    result = [fixed[0]]
    for a, b in pairwise(fixed):
        count = math.ceil((b-a)/size)
        result.extend(a+(b-a)*i/count for i in range(1, count+1))
    return result


def grid(xs, ys):
    """Abaqus/CalculiX S8 corners counterclockwise, followed by edge middles."""
    nodes, lookup, elements = {}, {}, {}

    def tag(x, y):
        key = (round(x, 8), round(y, 8))
        if key not in lookup:
            lookup[key] = len(nodes)+1
            nodes[lookup[key]] = [float(x), float(y), 0.]
        return lookup[key]

    for y0, y1 in pairwise(ys):
        for x0, x1 in pairwise(xs):
            points = ((x0, y0), (x1, y0), (x1, y1), (x0, y1),
                      ((x0+x1)/2, y0), (x1, (y0+y1)/2),
                      ((x0+x1)/2, y1), (x0, (y0+y1)/2))
            elements[len(elements)+1] = [tag(*p) for p in points]
    return nodes, elements, lookup


def pressure_load(nodes, elements, patch, total):
    """Exact consistent S8 nodal loads for uniform rectangular pressure.

    Negative corner forces are the quadratic shape-function integrals, not
    physical tension patches. They preserve virtual work for the shell field.
    """
    x0, x1, y0, y1 = patch
    if x1 <= x0 or y1 <= y0 or not math.isfinite(total):
        raise ValueError('Invalid finite patch/load')
    area, weights = 0., {}
    for ids in elements.values():
        corners = [nodes[t] for t in ids[:4]]
        xa, xb = min(p[0] for p in corners), max(p[0] for p in corners)
        ya, yb = min(p[1] for p in corners), max(p[1] for p in corners)
        if xa >= x0-1e-6 and xb <= x1+1e-6 and ya >= y0-1e-6 and yb <= y1+1e-6:
            a = (xb-xa)*(yb-ya)
            area += a
            for t, coefficient in zip(ids, (-1/12,)*4+(1/3,)*4, strict=True):
                weights[t] = weights.get(t, 0.)+a*coefficient
    if not math.isclose(area, (x1-x0)*(y1-y0), rel_tol=1e-8, abs_tol=1e-6):
        raise ValueError('Pressure patch not fully and exactly imprinted')
    return {t: w*total/area for t, w in weights.items()}, area


def sets(name, tags):
    values = sorted(tags)
    return [f'*NSET,NSET={name}', *[','.join(map(str, values[i:i+16])) for i in range(0, len(values), 16)]]


def deck(record):
    nodes, elements = record['nodes'], record['elements']
    lines = ['** '+__doc__.replace('\n', ' '), '*NODE']
    lines += [f'{t},'+','.join(f'{v:.14g}' for v in p) for t, p in nodes.items()]
    lines += ['*ELEMENT,TYPE=S8,ELSET=PANEL']
    lines += [f'{e},'+','.join(map(str, ids)) for e, ids in elements.items()]
    lines += [*sets('ALLN', nodes), '*MATERIAL,NAME=ASSUMED_ISOTROPIC', '*ELASTIC',
              f"{record['modulus_mpa']},{record['poisson_ratio']}",
              '*SHELL SECTION,ELSET=PANEL,MATERIAL=ASSUMED_ISOTROPIC', str(record['thickness_mm']),
              '*STEP', '*STATIC', '*BOUNDARY']
    lines += [f'{tag},{dof},{dof},0' for tag, dof in record['constraints']]
    lines += ['*CLOAD', *[f'{t},3,{v:.14g}' for t, v in record['loads'].items()],
              '*NODE PRINT,NSET=ALLN', 'U,RF', '*END STEP']
    return '\n'.join(lines)+'\n'


def prepare_panel(module, band, size):
    b = module.b
    name = f'main_{band}_left'
    screws = [c for c in module.connections() if isinstance(c, module.timber.PanelScrew) and c.members[0] == name]
    along = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    points = [(c.name, c.start.x, (c.start-b.point(0, 0, 0)).dot(along)) for c in screws]
    if len(points) < 3 or not all(abs(c.length-50.8) < 1e-6 for c in screws):
        raise ValueError('Unexpected panel screw inventory')
    low, high = (0., b.HALF) if band == 'lower' else (b.HALF, b.LENGTH)
    cx, cy = -419.2, 1099.2 if band == 'lower' else 1319.2
    patch = (cx-PATCH_WIDTH/2, cx+PATCH_WIDTH/2, cy-PATCH_WIDTH/2, cy+PATCH_WIDTH/2)
    xs = mesh_axes(-b.HALF, 0., size, [x for _, x, _ in points]+list(patch[:2]))
    ys = mesh_axes(low, high, size, [y for _, _, y in points]+list(patch[2:]))
    nodes, elements, lookup = grid(xs, ys)
    screw_nodes = {name: lookup[round(x, 8), round(y, 8)] for name, x, y in points}
    if len(set(screw_nodes.values())) != len(points):
        raise ValueError('Coincident screw restraints')
    constraints = [(t, 3) for t in screw_nodes.values()]
    # These three in-plane DOFs remove translation X/Y and in-plane rotation.
    constraints += [(lookup[round(-b.HALF, 8), round(low, 8)], d) for d in (1, 2)]
    constraints += [(lookup[0., round(low, 8)], 2)]
    loads, area = pressure_load(nodes, elements, patch, FORCE)
    if set(loads) & set(screw_nodes.values()):
        raise ValueError('Load patch overlaps an ideal screw restraint')
    return {'candidate': module.KEY, 'panel': name, 'mesh_max_mm': size,
            'nodes': nodes, 'elements': elements, 'constraints': constraints, 'loads': loads,
            'screw_nodes': screw_nodes, 'modulus_mpa': E, 'poisson_ratio': NU,
            'thickness_mm': THICKNESS, 'patch_mm': patch, 'patch_area_mm2': area,
            'outward_world_axis': list((-b.normal()).toTuple()),
            'patch_basis': 'Hypothetical 40x40 mm uniform pressure patch centered at the specified hold datum; not the actual hold/T-nut footprint',
            'seam_nodes': sorted((t for t, p in nodes.items() if abs(p[1]-b.HALF) < 1e-6), key=lambda t: nodes[t][0])}


def benchmark(size=20.):
    """Narrow free-sided nu=0 cantilever; edge load 1 N, no membrane restraint."""
    width, length, thickness, force = 100., 1000., 10., 1.
    nodes, elements, _ = grid(mesh_axes(0, width, size), mesh_axes(0, length, size))
    root = [t for t, p in nodes.items() if abs(p[1]) < 1e-6]
    loads = {}
    for ids in elements.values():
        if all(abs(nodes[ids[i]][1]-length) < 1e-6 for i in (2, 3, 6)):
            w = nodes[ids[2]][0]-nodes[ids[3]][0]
            for i, coefficient in ((2, 1/6), (3, 1/6), (6, 2/3)):
                loads[ids[i]] = loads.get(ids[i], 0.)+force*w/width*coefficient
    bending = force*length**3/(3*E*(width*thickness**3/12))
    shear = force*length/((5/6)*(E/2)*width*thickness)
    return {'candidate': 'cantilever-benchmark', 'panel': 'benchmark', 'mesh_max_mm': size,
            'nodes': nodes, 'elements': elements, 'loads': loads,
            'constraints': [(t, d) for t in root for d in range(1, 7)],
            'modulus_mpa': E, 'poisson_ratio': 0., 'thickness_mm': thickness,
            'benchmark_tip_mm': bending+shear, 'seam_nodes': [], 'screw_nodes': {}}


def read_blocks(data):
    result = {}
    for kind in ('displacements', 'forces'):
        matches = list(re.finditer(r'^\s*'+kind+r'\s*\([^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)', data, re.MULTILINE | re.DOTALL))
        if len(matches) != 1:
            raise ValueError(f'Expected one complete {kind} block')
        rows = {}
        for line in matches[0][1].splitlines():
            cells = line.split()
            if len(cells) == 4 and cells[0].isdigit():
                tag = int(cells[0])
                if tag in rows:
                    raise ValueError('Duplicate nodal output')
                rows[tag] = [float(v.replace('D', 'E')) for v in cells[1:]]
        result[kind] = rows
    return result


def assess(record, data):
    output = read_blocks(data)
    nodes, u, rf = record['nodes'], output['displacements'], output['forces']
    if set(u) != set(nodes) or set(rf) != set(nodes) or not all(
            math.isfinite(v) for rows in output.values() for xyz in rows.values() for v in xyz):
        raise ValueError('Incomplete/nonfinite original-shell-node output')
    # RF output includes externally applied loads at free loaded nodes in CCX;
    # only constrained translational DOFs are external support reactions.
    constrained = {(t, d) for t, d in record['constraints'] if d <= 3}
    reactions = {t: [rf[t][i] if (t, i+1) in constrained else 0. for i in range(3)] for t in nodes}
    applied = [0., 0., sum(record['loads'].values())]
    force = [applied[i]+sum(v[i] for v in reactions.values()) for i in range(3)]
    moment = [sum(nodes[t][1]*v for t, v in record['loads'].items()),
              -sum(nodes[t][0]*v for t, v in record['loads'].items()), 0.]
    for t, values in reactions.items():
        for i in range(3):
            moment[i] += nodes[t][(i+1)%3]*values[(i+2)%3]-nodes[t][(i+2)%3]*values[(i+1)%3]
    if max(map(abs, force)) > .1:
        raise ValueError(f'Force equilibrium failed: {force}')
    is_benchmark = record['candidate'] == 'cantilever-benchmark'
    # Clamped benchmark transfers a root moment through shell rotations;
    # original-node RF does not expose it. Panel comparison has free rotations.
    if not is_benchmark and max(map(abs, moment)) > 2.:
        raise ValueError(f'Moment equilibrium failed: {moment}')
    if any(abs(u[t][d-1]) > 1e-7 for t, d in constrained):
        raise ValueError('Ideal translational restraint moved')
    work = sum(v*u[t][2] for t, v in record['loads'].items())
    average = work/applied[2]
    if work <= 0:
        raise ValueError('Nonpositive elastic work')
    result = {'force_residual_n': force, 'moment_residual_nmm': None if is_benchmark else moment,
              'normal_patch_average_displacement_mm': average,
              'external_work_nmm': work, 'compliance_mm_per_n': work/applied[2]**2,
              'maximum_abs_normal_displacement_mm': max(abs(v[2]) for v in u.values()),
              'seam_profile': [[nodes[t][0], u[t][2]] for t in record['seam_nodes']],
              'ideal_screw_normal_reactions_n': {name: reactions[t][2] for name, t in record['screw_nodes'].items()},
              'qualified_for_design': False}
    if is_benchmark:
        error = abs(average/record['benchmark_tip_mm']-1)
        if error > .03:
            raise ValueError(f'Cantilever benchmark differs by {error:.2%}')
        result.update(benchmark_tip_reference_mm=record['benchmark_tip_mm'], benchmark_relative_error=error)
    return result


def run(record, directory):
    directory.mkdir(exist_ok=False, parents=True)
    inp = directory/'panel.inp'
    inp.write_text(deck(record))
    (directory/'input.json').write_text(json.dumps(record, indent=2)+'\n')
    command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=2g',
               '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
               '-v', f'{directory.resolve()}:/output', '-w', '/output', IMAGE,
               'timeout', '--signal=TERM', '--kill-after=5s', '120s', 'ccx', '-i', 'panel']
    completed = subprocess.run(command, capture_output=True, text=True, timeout=140, check=False)
    (directory/'panel.log').write_text(completed.stdout+completed.stderr)
    if completed.returncode or '*ERROR' in completed.stdout.upper():
        raise RuntimeError(f'Shell solve failed: {directory}, return {completed.returncode}')
    result = assess(record, (directory/'panel.dat').read_text())
    result['evidence_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}
    (directory/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result



def comparison_summary(cases):
    """Suppress comparative ratios unless both compliance and seam refine."""
    grouped = {}
    for row in cases:
        key = (row['candidate'], row['band'])
        if row['mesh_mm'] in grouped.setdefault(key, {}):
            raise ValueError('Duplicate candidate/band/resolution')
        grouped[key][row['mesh_mm']] = row
    if len(grouped) != 4 or any(set(rows) != set(SIZES) for rows in grouped.values()):
        raise ValueError('Require two variants, two panels and both resolutions')
    checks = []
    for (candidate, band), rows in grouped.items():
        coarse, fine = (rows[size] for size in SIZES)
        metrics = {}
        for label, a, b in (
                ('patch_compliance', coarse['compliance_mm_per_n'], fine['compliance_mm_per_n']),
                ('seam_max_abs', max(abs(p[1]) for p in coarse['seam_profile']),
                 max(abs(p[1]) for p in fine['seam_profile']))):
            metrics[label] = abs(a-b)/max(abs(b), 1e-12)
        checks.append({'candidate': candidate, 'band': band, 'relative_changes': metrics,
                       'passes_5_percent_refinement': max(metrics.values()) <= .05})
    accepted = all(row['passes_5_percent_refinement'] for row in checks)
    ratios = []
    names = sorted({key[0] for key in grouped})
    if accepted:
        paired = next(name for name in names if name.startswith('paired-'))
        vertical = next(name for name in names if name != paired)
        for band in ('lower', 'upper'):
            a, z = (grouped[name, band][min(SIZES)] for name in (paired, vertical))
            ratios.append({'band': band, 'vertical_over_paired_patch_compliance':
                           z['compliance_mm_per_n']/a['compliance_mm_per_n'],
                           'vertical_over_paired_max_abs_seam_displacement':
                           max(abs(p[1]) for p in z['seam_profile'])/max(abs(p[1]) for p in a['seam_profile'])})
    return {'numerical_comparison_accepted': accepted, 'refinement_checks': checks,
            'fine_mesh_surrogate_ratios': ratios, 'qualified_for_design': False,
            'gusset_force_reduction_established': False, 'actual_panel_qualified': False,
            'seam_interpretation': 'Each load case acts on one independent panel; the unloaded neighbor stays zero in this ideal model. The reported seam profile therefore gives the same-case displacement jump. Different loaded-panel cases are not combined.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--benchmark-only', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite diagnostic evidence')
    sources = [Path(__file__), *sorted(Path('mini_moonboard').glob('*.py')),
               *[Path(p) for p in ('docs/ml24z-reference.json', 'docs/panel-insert-reference.json',
                                   'docs/selective-stock-reference.json')]]
    before = {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sources}
    report = {'limits': __doc__, 'solver_image': IMAGE, 'source_sha256': before,
              'qualified_for_design': False, 'actual_panel_qualified': False,
              'gusset_force_reduction_established': False,
              'benchmark': run(benchmark(), args.output/'benchmark'), 'cases': []}
    if not args.benchmark_only:
        from mini_moonboard import paired_rail_frame, vertical_principal_frame
        for module in (paired_rail_frame, vertical_principal_frame):
            for band in ('lower', 'upper'):
                for size in SIZES:
                    record = prepare_panel(module, band, size)
                    name = f'{module.KEY}-{band}-{size:g}'
                    result = run(record, args.output/name)
                    report['cases'].append({'candidate': module.KEY, 'band': band, 'mesh_mm': size, **result})
                    print(name, result['normal_patch_average_displacement_mm'], flush=True)
    if report['cases']:
        report['comparison'] = comparison_summary(report['cases'])
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha for p, sha in before.items()):
        raise ValueError('Source changed during shell diagnostic; evidence not accepted')
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
