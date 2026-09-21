"""Frozen-mesh panel screw deletion probes; numerical sensitivity, never qualification."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authenticated_input(root):
    root = Path(root)
    report = json.loads((root/'report.json').read_text())
    if not report['contact_diagnostic_checks_passed']:
        raise ValueError('Parent diagnostic did not pass')
    for name, sha in report['source_sha256'].items():
        if digest(root/'source_snapshots'/name) != sha:
            raise ValueError('Parent source snapshot mismatch: '+name)
    for name, sha in report['artifact_sha256'].items():
        if digest(root/name) != sha:
            raise ValueError('Parent artifact mismatch: '+name)
    path = root/report['final_cycle_directory']/'input.json'
    record = json.loads(path.read_text())
    if record['mode'] != 'coupled':
        raise ValueError('Requires actual panel-loaded coupled parent')
    if record['assumed_modulus_mpa'] != 7000. or record['assumed_poisson_ratio'] != .3:
        raise ValueError('Unsupported parent material parameters')
    control = restore(record)
    active = {r['name'] for r in record['springs'] if r['bearing_closed_assumption'] and r.get('active', True)}
    if control.deck(active_bearings=active, stress=True) != (path.parent/'frame.inp').read_text():
        raise ValueError('Frozen reconstruction differs from parent deck; unsupported material/kernel drift')
    return record, {'directory': str(root), 'report_sha256': digest(root/'report.json'),
                    'input_sha256': digest(path), 'source_sha256': report['source_sha256']}


def restore(record, removed=()):
    """Delete spring triplets only; every solid, shell, load and equation retained."""
    model = frame.Structure()
    model.nodes = {int(n): p for n, p in record['nodes'].items()}
    model.elements = {int(n): e for n, e in record['elements'].items()}
    model.loads = {int(n): f for n, f in record['loads'].items()}
    model.equations = record['equations']
    model.fixed = set(record['fixed_nodes'])
    model.rotation_masters = set(record['rotation_master_nodes'])
    model.members = {r['name']: r for r in record['members']}
    model.panels = {name: {'nodes': nodes} for name, nodes in record['panel_nodes'].items()}
    panel_nodes = {n for ns in record['panel_nodes'].values() for n in ns}
    removed = set(removed)
    for name in removed:
        springs = [r for r in record['springs'] if r['name'] == name]
        if len(springs) != 3 or {r['dof'] for r in springs} != {1, 2, 3}:
            raise ValueError('Removal must name one complete screw triplet: '+name)
        if any(r['bearing_closed_assumption'] or r['nodes'][1] not in panel_nodes
               or r['nodes'][0] in panel_nodes for r in springs):
            raise ValueError('Only wood-to-panel screw removal allowed: '+name)
    model.springs = [r for r in record['springs'] if r['name'] not in removed]
    deleted = {r['element'] for r in record['springs'] if r['name'] in removed}
    model.elements = {n: e for n, e in model.elements.items() if n not in deleted}
    for n, (_, _, group) in model.elements.items():
        model.groups.setdefault(group, []).append(n)
    return model


def patch_weights(nodes, elements, patch):
    """Exact three-point quadrature of S8 shape functions over cell/patch overlap."""
    x0, x1, y0, y1 = patch
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Increasing patch bounds required')
    q, w = np.polynomial.legendre.leggauss(3)
    weights, area = {}, 0.
    for ids in elements:
        corners = np.array([nodes[n] for n in ids[:4]])
        xa, ya = corners[:, :2].min(axis=0)
        xb, yb = corners[:, :2].max(axis=0)
        lo, hi = max(x0, xa), min(x1, xb)
        bottom, top = max(y0, ya), min(y1, yb)
        if hi <= lo or top <= bottom:
            continue
        a = (hi-lo)*(top-bottom)
        area += a
        values = np.zeros(8)
        for i, u in enumerate(q):
            x = (lo+hi)/2+u*(hi-lo)/2
            for j, v in enumerate(q):
                y = (bottom+top)/2+v*(top-bottom)/2
                values += w[i]*w[j]*a/4*frame.shape8(2*(x-xa)/(xb-xa)-1, 2*(y-ya)/(yb-ya)-1)
        for n, value in zip(ids, values, strict=True):
            weights[n] = weights.get(n, 0.)+float(value)
    if not np.isclose(area, (x1-x0)*(y1-y0), rtol=1e-9, atol=1e-6):
        raise ValueError('Patch must lie entirely on one panel')
    return {n: value/area for n, value in weights.items()}


def mirror_load(record):
    """Synthetic mirrored coordinate, not necessarily a named hold; gravity unchanged."""
    result = copy.deepcopy(record)
    target = np.array(record['target_xyz_mm'])
    mirrored = target*np.array([-1., 1., 1.])
    old = record['panel_patch_mm']
    patch = [-old[1], -old[0], old[2], old[3]]
    old_s = (old[2]+old[3])/2
    along = np.array(next(r['axis'] for r in record['members']
                          if r['name'].startswith('base_principal_')))
    panel = next(name for name, tags in record['panel_nodes'].items()
                 if set(record['panel_load']['nodes']) <= set(tags))
    other = panel.removesuffix('left')+'right' if panel.endswith('left') else panel.removesuffix('right')+'left'
    coords = {int(n): p for n, p in record['nodes'].items()}
    local = {n: [coords[n][0], float(np.dot(np.array(coords[n])-target, along))+old_s, 0.]
             for n in record['panel_nodes'][other]}
    elements = [ids for kind, ids, group in record['elements'].values() if kind == 'S8' and group == other]
    weights = patch_weights(local, elements, patch)
    tags = list(weights)
    force = np.array(record['force_xyz_n'])*[-1., 1., 1.]
    moment = np.array(record['moment_at_panel_midplane_nmm'])*[1., -1., -1.]
    values = frame.traction_wrench([coords[n] for n in tags], list(weights.values()), force, moment, mirrored)
    loads = {int(n): np.array(f) for n, f in record['loads'].items()}
    for n, f in zip(record['panel_load']['nodes'], record['panel_load']['forces_xyz_n'], strict=True):
        loads[n] -= f
    for n, f in zip(tags, values, strict=True):
        loads[n] = loads.get(n, np.zeros(3))+f
    result.update(loads={n: f.tolist() for n, f in loads.items()},
                  panel_load={'nodes': tags, 'forces_xyz_n': values.tolist()},
                  panel_patch_mm=patch, target_xyz_mm=mirrored.tolist(),
                  force_xyz_n=force.tolist(), moment_at_panel_midplane_nmm=moment.tolist(),
                  hold='synthetic-mirror-of-'+record['hold'])
    return result


def runtime_sources():
    paths = [Path(__file__), Path(frame.__file__), Path(stress.__file__), Path(frame.panel_kernel.__file__)]
    return {str(p.resolve().relative_to(Path.cwd())): digest(p) for p in paths}


def run(parent, output, removed=(), mirror=False, pattern_path=None):
    record, provenance = authenticated_input(parent)
    if mirror:
        record = mirror_load(record)
    model = restore(record, removed)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    sources = runtime_sources()
    for name in sources:
        target = output/'source_snapshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(name).read_bytes())
    if pattern_path:
        (output/'pattern.json').write_bytes(Path(pattern_path).read_bytes())
    metadata = {k: v for k, v in record.items() if k not in ('nodes', 'elements', 'loads', 'fixed_nodes',
                 'equations', 'springs', 'panel_nodes', 'rotation_master_nodes')}
    metadata['screw_sensitivity'] = {'removed': sorted(removed), 'mirror_load': mirror,
        'parent': provenance, 'mesh_unchanged': True, 'gravity_unchanged': True,
        'limits': 'Synthetic mirrors need not coincide with hold-grid coordinates; opposite panel patch '
                  'uses exact subcell traction integration on unchanged coarse mesh. Local peak stress '
                  'is not converged. Equal isotropic materials and equal directional screw springs '
                  'remain assumptions. No withdrawal, head pull-through, splitting or floor qualification.'}
    active = {r['name'] for r in model.springs if r['bearing_closed_assumption']}
    history, seen = [], set()
    for iteration in range(12):
        signature = tuple(sorted(active))
        if signature in seen:
            raise ValueError('Bearing active set cycled')
        seen.add(signature)
        job = output/f'cycle-{iteration:02d}'
        job.mkdir()
        current = frame.record_structure(model, metadata, active)
        (job/'input.json').write_text(json.dumps(current, indent=2)+'\n')
        (job/'frame.inp').write_text(model.deck(active_bearings=active, stress=True))
        command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=4g',
                   '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
                   '-v', f'{job.resolve()}:/output', '-w', '/output', frame.panel_kernel.IMAGE,
                   'timeout', '180s', 'ccx', '-i', 'frame']
        native = subprocess.run(command, capture_output=True, text=True, timeout=200, check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native solve failed; retained cycle log')
        data = (job/'frame.dat').read_text()
        report = frame.assess(current, data)
        report['diagnostic_stress'] = stress.assess(current, data)
        report['artifact_sha256'] = {p.name: digest(p) for p in job.iterdir() if p.is_file()}
        (job/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        history.append({'directory': job.name, 'report_sha256': digest(job/'report.json')})
        if not report['global_equilibrium_passed'] or not report['mpc_check_passed']:
            raise ValueError('Equilibrium or kinematic audit failed')
        if report['closed_bearing_assumption_passed']:
            break
        active = frame.next_bearing_set(report['bearings'])
    else:
        raise ValueError('Bearing active set did not converge')
    if sources != runtime_sources():
        raise ValueError('Runtime source changed')
    report.update(contact_diagnostic_checks_passed=True, contact_active_set_converged=True,
                  contact_cycles=history, final_cycle_directory=history[-1]['directory'],
                  source_sha256=sources, solver_image=frame.panel_kernel.IMAGE,
                  screw_sensitivity=metadata['screw_sensitivity'])
    report['artifact_sha256'] = {str(p.relative_to(output)): digest(p)
                                 for p in output.rglob('*') if p.is_file()}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pattern', type=Path, help='JSON object with removed connection-name list; omit for control')
    parser.add_argument('--mirror-load', action='store_true')
    args = parser.parse_args()
    removed = json.loads(args.pattern.read_text())['removed'] if args.pattern else []
    result = run(args.parent, args.output, removed, args.mirror_load, args.pattern)
    print(json.dumps({k: result[k] for k in ('maximum_panel_displacement_mm',
          'maximum_timber_displacement_mm', 'qualified_for_design')}))
