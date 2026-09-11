"""One-at-a-time F10 load-assumption probes; no load-rating or screw-count approval."""
import argparse
import copy
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame
from fea import panel_screw_sensitivity as frozen

restore, authenticated_input, digest = frozen.restore, frozen.authenticated_input, frozen.digest


def runtime_sources():
    return {**frozen.runtime_sources(), str(Path(__file__).resolve().relative_to(Path.cwd())): digest(__file__)}


def change_load(record, body_multiplier=2., horizontal_n=300., standoff_mm=100.):
    """Change hold wrench only; retain patch, every panel/wood node and gravity."""
    values = (body_multiplier, horizontal_n, standoff_mm)
    if not all(np.isfinite(v) for v in values) or body_multiplier <= 0 or horizontal_n < 0 or standoff_mm < 0:
        raise ValueError('Finite positive body multiplier and nonnegative horizontal/standoff required')
    if record['load_kind'] != 'full':
        raise ValueError('Load scenarios require full-vector parent')
    result = copy.deepcopy(record)
    target = np.array(record['target_xyz_mm'])
    along = np.array(next(r['axis'] for r in record['members'] if r['name'].startswith('base_principal_')))
    outward = np.cross(along, [1., 0., 0.])
    patch = record['panel_patch_mm']
    center_s = (patch[2]+patch[3])/2
    panel = next(name for name, tags in record['panel_nodes'].items()
                 if set(record['panel_load']['nodes']) <= set(tags))
    coords = {int(n): p for n, p in record['nodes'].items()}
    local = {n: [coords[n][0], float(np.dot(np.array(coords[n])-target, along))+center_s, 0.]
             for n in record['panel_nodes'][panel]}
    elements = [ids for kind, ids, group in record['elements'].values() if kind == 'S8' and group == panel]
    weights = frozen.patch_weights(local, elements, patch)
    tags = list(weights)
    force = np.array([0., horizontal_n, -body_multiplier*record['pounds']*.45359237*9.80665])
    moment = np.cross(outward*(standoff_mm+frame.panel_kernel.THICKNESS/2), force)
    forces = frame.traction_wrench([coords[n] for n in tags], list(weights.values()), force, moment, target)
    loads = {int(n): np.array(f) for n, f in record['loads'].items()}
    for n, f in zip(record['panel_load']['nodes'], record['panel_load']['forces_xyz_n'], strict=True):
        loads[n] -= f
    for n, f in zip(tags, forces, strict=True):
        loads[n] = loads.get(n, np.zeros(3))+f
    result.update(loads={n: f.tolist() for n, f in loads.items()},
                  panel_load={'nodes': tags, 'forces_xyz_n': forces.tolist()},
                  force_xyz_n=force.tolist(), moment_at_panel_midplane_nmm=moment.tolist(),
                  standoff_from_front_mm=standoff_mm,
                  load_assumption_scenario={'body_multiplier': body_multiplier, 'horizontal_n': horizontal_n,
                      'standoff_mm': standoff_mm, 'measured_or_qualified': False,
                      'gravity_preserved': True, 'patch_preserved': True})
    return result


def run(parent, output, removed=(), pattern_path=None, body_multiplier=2., horizontal_n=300., standoff_mm=100.):
    record, provenance = authenticated_input(parent)
    record = change_load(record, body_multiplier, horizontal_n, standoff_mm)
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
    metadata['screw_sensitivity'] = {'removed': sorted(removed), 'mirror_load': False,
        'parent': provenance, 'mesh_unchanged': True, 'gravity_unchanged': True,
        'limits': 'Load scenarios are analyst-selected, not measured acceptance loads. Local peak stress '
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
    parser.add_argument('--pattern', type=Path)
    parser.add_argument('--body-multiplier', type=float, default=2.)
    parser.add_argument('--horizontal-n', type=float, default=300.)
    parser.add_argument('--standoff-mm', type=float, default=100.)
    args = parser.parse_args()
    removed = json.loads(args.pattern.read_text())['removed'] if args.pattern else []
    r = run(args.parent, args.output, removed, args.pattern, args.body_multiplier, args.horizontal_n, args.standoff_mm)
    print(r['maximum_panel_displacement_mm'])
