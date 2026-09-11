"""Replay archived panel wrench balance and signed attachment demand without solves."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame


def panel_balance(record, report, precision):
    nodes = {int(n): np.array(x, dtype=float) for n, x in record['nodes'].items()}
    loads = {int(n): np.array(f) for n, f in record['loads'].items()}
    result = []
    for panel, tags in record['panel_nodes'].items():
        tags = set(tags)
        ids = next(ids for kind, ids, group in record['elements'].values() if kind == 'S8' and group == panel)
        normal = np.cross(nodes[ids[1]]-nodes[ids[0]], nodes[ids[3]]-nodes[ids[0]])
        normal /= np.linalg.norm(normal)
        names = {spring['name'] for spring in record['springs'] if spring['nodes'][1] in tags}
        applied = sum((loads.get(n, np.zeros(3)) for n in tags), np.zeros(3))
        moment = sum((np.cross(nodes[n], loads.get(n, np.zeros(3))) for n in tags), np.zeros(3))
        axial, forces = [], []
        force_radius, moment_radius = np.zeros(3), np.zeros(3)
        for name in sorted(names):
            connector = report['connector_forces'][name]
            force = np.array(connector['force_on_first_xyz_n'])
            forces.append(force)
            radius = np.zeros(3)
            for spring in record['springs']:
                if spring['name'] == name:
                    a, b = spring['nodes']
                    dof = spring['dof']-1
                    radius[dof] += spring['stiffness_n_per_mm']*(precision[a][dof]+precision[b][dof])
            force_radius += radius
            x, y, z = connector['first_point_xyz_mm']
            moment_radius += np.abs([[0., -z, y], [z, 0., -x], [-y, x, 0.]])@radius
            moment -= np.cross(connector['first_point_xyz_mm'], force)
            tension = max(0., -float(force@normal))
            compression = max(0., float(force@normal))
            axial.append({'connection': name, 'withdrawal_n': tension, 'compression_n': compression,
                          'shear_n': float(np.linalg.norm(force-(force@normal)*normal))})
        residual = applied-sum(forces, np.zeros(3))
        result.append({'panel': panel, 'attachment_count': len(names),
            'applied_force_xyz_n': applied.tolist(), 'force_residual_n': residual.tolist(),
            'moment_residual_nmm': moment.tolist(),
            'force_rounding_interval_radius_n': force_radius.tolist(),
            'moment_rounding_interval_radius_nmm': moment_radius.tolist(),
            'wrench_balance_passed': bool(np.all(abs(residual) <= force_radius+1.e-5)
                                        and np.all(abs(moment) <= moment_radius+.001)),
            'total_withdrawal_n': sum(row['withdrawal_n'] for row in axial),
            'total_compression_n': sum(row['compression_n'] for row in axial),
            'maximum_withdrawal': max(axial, key=lambda row: row['withdrawal_n']), 'attachments': axial})
    return result


def build(archives):
    cases, hashes = [], {}
    for path in map(Path, archives):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        with tarfile.open(path, 'r:gz') as archive:
            blobs = {member.name: archive.extractfile(member).read() for member in archive.getmembers() if member.isfile()}
        for name, payload in sorted(blobs.items()):
            if name.count('/') != 1 or not name.endswith('/report.json'):
                continue
            root = name.removesuffix('report.json')
            report = json.loads(payload)
            for relative, sha in report['artifact_sha256'].items():
                if hashlib.sha256(blobs[root+relative]).hexdigest() != sha:
                    raise ValueError('Archived artifact mismatch: '+root+relative)
            final = root+report['final_cycle_directory']+'/'
            record = json.loads(blobs[final+'input.json'])
            replay = frame.assess(record, blobs[final+'frame.dat'].decode())
            if replay['connector_forces'] != report['connector_forces']:
                raise ValueError('Native connector force replay differs')
            cases.append({'archive': str(path), 'case': root.rstrip('/'),
                'candidate': record['candidate'], 'load_scenario': record.get('load_assumption_scenario'),
                'panels': panel_balance(record, replay, frame.displacement_roundoff(blobs[final+'frame.dat'].decode())), 'qualified_for_design': False})
    hashes[str(Path(__file__).resolve().relative_to(Path.cwd()))] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {'all_panel_wrench_intervals_passed': all(panel['wrench_balance_passed'] for case in cases for panel in case['panels']),
            'cases': cases, 'input_sha256': hashes, 'qualified_for_design': False,
            'insert_demands_qualified': False,
            'limits': 'Historical ordinary-screw diagnostic only. Signed forces and panel equilibrium '
                      'do not establish actual stiffness, contact, insert resistance or load acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(build(args.archive), stream, indent=2, allow_nan=False)
        stream.write('\n')
