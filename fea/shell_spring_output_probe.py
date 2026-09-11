"""Compare spring k-delta-U recovery with each spring's unique fixed-node reaction."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame


def prepare(proxy=False, all_nodes=False):
    model = frame.Structure()
    points = [(0., 0., 0.), (200., 0., 0.), (200., 200., 0.), (0., 200., 0.),
              (100., 0., 0.), (200., 100., 0.), (100., 200., 0.), (0., 100., 0.)]
    ids = [model.node(p) for p in points]
    model.element('S8', ids, 'PANEL')
    model.panels['PANEL'] = {'nodes': ids}
    supports = []
    for panel_node in (ids if all_nodes else ids[:4]):
        position = model.nodes[panel_node]
        fixed = model.node(position)
        model.fixed.add(fixed)
        attached = panel_node
        if proxy:
            attached = model.node(position)
            model.equations.extend([[(attached, dof, 1.), (panel_node, dof, -1.)] for dof in (1, 2, 3)])
        model.spring(fixed, attached, 1000., f'fastener_{panel_node}')
        supports.append({'fixed': fixed, 'attached': attached, 'shell_node': panel_node})
    model.loads[ids[5]] = [0., 300., -2000.]
    return model, supports


def assess(record, data):
    parsed = frame.panel_kernel.read_blocks(data)
    precision = frame.displacement_roundoff(data)
    u, rf = parsed['displacements'], parsed['forces']
    rows = []
    for row in record['supports']:
        fixed, attached = row['fixed'], row['attached']
        recovered = 1000.*(np.array(u[attached])-u[fixed])
        native = -np.array(rf[fixed])
        radius = 1000.*(np.array(precision[attached])+precision[fixed])
        # RF prints seven significant digits. This separate conservative bound
        # applies only to independent fixed-node reaction output in this coupon.
        rf_radius = np.maximum(1.e-8, abs(native)*1.e-6)
        rows.append({**row, 'recovered_force_on_fixed_n': recovered.tolist(),
            'native_force_on_fixed_n': native.tolist(), 'difference_n': (recovered-native).tolist(),
            'comparison_tolerance_n': (radius+rf_radius).tolist(),
            'passed': bool(np.all(abs(recovered-native) <= radius+rf_radius))})
    return {'proxy': record['proxy'], 'springs': rows,
            'all_spring_recoveries_passed': all(row['passed'] for row in rows),
            'mpc': frame.mpc_intervals(record['equations'], u, precision),
            'support_force_n': sum((np.array(rf[row['fixed']]) for row in record['supports']), np.zeros(3)).tolist(),
            'qualified_for_design': False}


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for proxy, all_nodes in ((False, False), (True, False), (False, True), (True, True)):
        model, supports = prepare(proxy, all_nodes)
        job = output/(('proxy' if proxy else 'direct')+('-all' if all_nodes else ''))
        job.mkdir()
        record = {'proxy': proxy, 'supports': supports, 'equations': model.equations,
                  'nodes': model.nodes, 'loads': model.loads, 'elements': model.elements}
        (job/'input.json').write_text(json.dumps(record, indent=2)+'\n')
        (job/'frame.inp').write_text(model.deck().replace('*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=1g',
            '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
            '-v', f'{job.resolve()}:/output', '-w', '/output', frame.panel_kernel.IMAGE,
            'timeout', '60s', 'ccx', '-i', 'frame']
        native = subprocess.run(command, capture_output=True, text=True, timeout=80, check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native shell spring coupon failed: '+str(job))
        result = assess(record, (job/'frame.dat').read_text())
        (job/'report.json').write_text(json.dumps(result, indent=2)+'\n')
        results.append(result)
    report = {'cases': results, 'solver_image': frame.panel_kernel.IMAGE,
              'source_sha256': {str(Path(__file__).resolve().relative_to(Path.cwd())):
                               hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'artifact_sha256': {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in output.rglob('*') if p.is_file()}}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output)['cases'], indent=2))
