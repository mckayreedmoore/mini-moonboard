"""Compare authenticated same-mesh screw probes; retain directional demands and limits."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame
from fea.horizontal_panel_fastener_screen import resolve
from fea.panel_screw_sensitivity import digest
from fea.vertical_panel_comparison import THICKNESS


def read_case(directory):
    directory = Path(directory)
    report = json.loads((directory/'report.json').read_text())
    if not report['contact_diagnostic_checks_passed'] or report['qualified_for_design']:
        raise ValueError('Expected passed numerical diagnostic without qualification')
    path = directory/report['final_cycle_directory']/'input.json'
    if digest(path) != report['artifact_sha256'][str(path.relative_to(directory))]:
        raise ValueError('Final input hash mismatch')
    for name, sha in report['artifact_sha256'].items():
        if digest(directory/name) != sha:
            raise ValueError('Case artifact hash mismatch: '+name)
    record = json.loads(path.read_text())
    replay = frame.assess(record, (path.parent/'frame.dat').read_text())
    if any(report.get(key) != value for key, value in replay.items()):
        raise ValueError('Native DAT assessment differs from reported forces/checks')
    return report, record


def compare(full_root, reduced_root, connections):
    full, original = read_case(full_root)
    reduced, candidate = read_case(reduced_root)
    for key in ('nodes', 'loads', 'fixed_nodes', 'equations', 'panel_nodes',
                'members', 'rotation_master_nodes', 'force_xyz_n',
                'target_xyz_mm', 'moment_at_panel_midplane_nmm'):
        if original[key] != candidate[key]:
            raise ValueError('Same-problem comparison mismatch: '+key)
    removed = set(reduced['screw_sensitivity']['removed'])
    old_springs = {r['element']: {k: v for k, v in r.items() if k != 'active'} for r in original['springs']}
    new_springs = {r['element']: {k: v for k, v in r.items() if k != 'active'} for r in candidate['springs']}
    expected = {n: r for n, r in old_springs.items() if r['name'] not in removed}
    if expected != new_springs or {r['name'] for n, r in old_springs.items() if n not in new_springs} != removed:
        raise ValueError('Retained spring mechanics changed or deletion list differs')
    deleted = {n for n, r in old_springs.items() if r['name'] in removed}
    if len(deleted) != 3*len(removed):
        raise ValueError('Expected three spring elements per removed screw')
    if {n: v for n, v in original['elements'].items() if int(n) not in deleted} != candidate['elements']:
        raise ValueError('Elements differ beyond exact deleted springs')
    old_elements = {n: v for n, v in original['elements'].items() if v[0] != 'SPRING2'}
    new_elements = {n: v for n, v in candidate['elements'].items() if v[0] != 'SPRING2'}
    if old_elements != new_elements:
        raise ValueError('Physical mesh changed')
    manifest_path = Path(connections).parent/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest['artifact_sha256']['connections.csv'] != digest(connections):
        raise ValueError('Inventory differs from published export manifest')
    parent_sources = full.get('screw_sensitivity', {}).get('parent', {}).get('source_sha256', full['source_sha256'])
    for name, sha in manifest['source_sha256'].items():
        if (name in parent_sources and name.startswith('mini_moonboard/')
                and not name.endswith('_exports.py') and parent_sources[name] != sha):
            raise ValueError('Inventory geometry source differs from parent: '+name)
    with Path(connections).open() as stream:
        inventory = {r['connection']: r for r in csv.DictReader(stream)
                     if r['members'].startswith(('main_', 'kicker_'))}
    if len(inventory) != 87 or not removed <= inventory.keys():
        raise ValueError('Expected authenticated 87-panel screw inventory')
    rows = []
    for name, c in inventory.items():
        direction = np.array([float(c[k]) for k in ('dx', 'dy', 'dz')])
        expected = np.array([float(c[k]) for k in ('x_mm', 'y_mm', 'z_mm')])+direction*THICKNESS/2
        if not np.isclose(np.linalg.norm(direction), 1.):
            raise ValueError('Screw direction not unit')
        row = {'connection': name, 'members': c['members'], 'removed': name in removed}
        for label, report in (('full', full), ('reduced', reduced)):
            if label == 'reduced' and name in removed:
                if name in report['connector_forces']:
                    raise ValueError('Removed screw still present')
                continue
            force = report['connector_forces'][name]
            if not np.allclose(expected, force['first_point_xyz_mm'], atol=1e-5, rtol=0.):
                raise ValueError('Inventory axis differs from physical spring: '+name)
            tension, compression, lateral = resolve(force['force_on_first_xyz_n'], direction)
            row[label] = {'withdrawal_n': tension, 'compression_n': compression, 'lateral_n': lateral}
        rows.append(row)
    worst = {label: {key: max((r for r in rows if label in r), key=lambda r: r[label][key])
                    for key in ('withdrawal_n', 'lateral_n')} for label in ('full', 'reduced')}
    displacement = {key: {'full': full[key], 'reduced': reduced[key],
                          'percent_change': 100*(reduced[key]/full[key]-1)}
                    for key in ('maximum_panel_displacement_mm', 'maximum_timber_displacement_mm')}
    return {'full_directory': str(full_root), 'reduced_directory': str(reduced_root),
            'full_report_sha256': digest(Path(full_root)/'report.json'),
            'reduced_report_sha256': digest(Path(reduced_root)/'report.json'),
            'same_mesh_loads_constraints_passed': True, 'retained_springs_exactly_preserved': True,
            'connections_sha256': digest(connections), 'export_manifest_sha256': digest(manifest_path), 'removed_count': len(removed),
            'full_count': 87, 'reduced_count': 87-len(removed), 'displacement': displacement,
            'rows': rows, 'worst': worst, 'qualified_for_design': False,
            'removal_approved': False,
            'limits': 'Finite isotropic clamped-foot and assumed equal-spring probes. '
                      'Directional demand only; adjusted withdrawal, head pull-through, combined '
                      'lateral action and cyclic performance not established. Synthetic mirrored '
                      'coordinates need not coincide with hold holes. No frame/floor strength acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', type=Path, required=True)
    parser.add_argument('--reduced', type=Path, required=True)
    parser.add_argument('--connections', type=Path, default=Path('exports/horizontal-service-development/connections.csv'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.full, args.reduced, args.connections)
    result['source_sha256'] = {str(p): digest(p) for p in
                              (Path(__file__), Path('fea/horizontal_panel_fastener_screen.py'),
                               Path('fea/panel_screw_sensitivity.py'), Path(frame.__file__),
                               Path(frame.panel_kernel.__file__), args.connections, args.connections.parent/'manifest.json')}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
