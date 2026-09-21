"""Directional integration-point stresses from the reduced frame diagnostic.

Tensor transformation is exact; the isotropic material/retained-section model
is not a wood resistance model. No von Mises criterion or design pass is used.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

HEADER = re.compile(r'^\s*(stresses|global coordinates)\s*\(([^)]*)\)\s*for set\s+(\S+)\s+and time\s+(\S+)', re.IGNORECASE)


def number(value):
    return float(value.replace('D', 'E').replace('d', 'e'))


def parse(data, expected, endpoint=1.):
    """Reject duplicate, omitted, nonfinite or incorrectly owned IP records."""
    result = {'stresses': {}, 'global coordinates': {}}
    active = None
    for line in data.splitlines():
        header = HEADER.match(line)
        if header:
            kind, columns, group, time = header.groups()
            kind = kind.lower()
            columns = re.sub(r'\s+', '', columns.lower())
            wanted = ('elem,integ.pnt.,sxx,syy,szz,sxy,sxz,syz' if kind == 'stresses' else 'elem,integ.pnt.,x,y,z')
            if columns != wanted:
                raise ValueError('Unexpected integration-point column order')
            active = (kind, group.upper()) if abs(number(time)-endpoint) < 1e-8 else None
            continue
        fields = line.split()
        if not fields:
            continue
        if active is None:
            continue
        if not fields[0].isdigit():
            active = None
            continue
        kind, group = active
        if len(fields) != (8 if kind == 'stresses' else 5) or not fields[1].isdigit():
            raise ValueError('Malformed integration-point record')
        key = (int(fields[0]), int(fields[1]))
        if key not in expected or expected[key] != group:
            raise ValueError('Unexpected integration point or element-set ownership')
        if key in result[kind]:
            raise ValueError('Duplicate integration-point record')
        values = [number(v) for v in fields[2:]]
        if not np.isfinite(values).all():
            raise ValueError('Nonfinite integration-point output')
        result[kind][key] = values
    if any(set(rows) != set(expected) for rows in result.values()):
        raise ValueError('Incomplete stresses or coordinates at requested endpoint')
    return result


def transform(components, axes):
    """CCX global Sxx,Syy,Szz,Sxy,Sxz,Syz -> an orthonormal local tensor."""
    xx, yy, zz, xy, xz, yz = components
    tensor = np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]], float)
    basis = np.asarray(axes, float)
    if basis.shape != (3, 3) or not np.isfinite(basis).all() or not np.isfinite(tensor).all():
        raise ValueError('Finite stress and three local axes required')
    if not np.allclose(basis@basis.T, np.eye(3), atol=1e-8, rtol=0.) or np.linalg.det(basis) < 0:
        raise ValueError('Right-handed orthonormal stress axes required')
    return basis@tensor@basis.T


def assess(record, data):
    metadata = record.get('stress_output', {})
    if metadata.get('global') is not True or set(metadata.get('variables', [])) != {'S', 'COORD'}:
        raise ValueError('Explicit global stress/coordinate output metadata required')
    kinds = metadata.get('integration_points', {})
    if kinds != {'C3D20': 27, 'S8': 27}:
        raise ValueError('Only verified full-integration C3D20/S8 output is supported')
    elements = {int(e): r for e, r in record['elements'].items()}
    physical = {e: r for e, r in elements.items() if r[0] != 'SPRING2'}
    if not physical or any(r[0] not in kinds for r in physical.values()):
        raise ValueError('Unexpected or empty physical element inventory')
    expected = {(e, ip): r[2].upper() for e, r in physical.items() for ip in range(1, kinds[r[0]]+1)}
    parsed = parse(data, expected)
    members = {r['name']: r for r in record['members']}
    nodes = {int(n): np.asarray(p) for n, p in record['nodes'].items()}
    groups = {}
    for e, (kind, ids, name) in physical.items():
        if name not in groups:
            if kind == 'C3D20':
                r = members[name]
                axes = [r['axis'], r['section_u'], r['section_v']]
                labels = ['grain', 'section_u', 'section_v']
                scope = 'Assigned lumber grain axes in an isotropic retained rectangular section; not local notch/hole stresses.'
            else:
                x = nodes[ids[1]]-nodes[ids[0]]
                y = nodes[ids[3]]-nodes[ids[0]]
                x, y = x/np.linalg.norm(x), y/np.linalg.norm(y)
                axes = [x.tolist(), y.tolist(), np.cross(x, y).tolist()]
                labels = ['panel_x', 'panel_y', 'panel_normal']
                scope = 'Geometric shell axes only; purchased plywood strength-axis/layup properties are not assigned.'
            transform([0.]*6, axes)
            groups[name] = {'name': name, 'element_type': kind, 'axes_xyz': axes, 'axis_labels': labels,
                            'scope': scope, 'integration_point_count': 0, 'extrema': {}}
        group = groups[name]
        for ip in range(1, 28):
            key = e, ip
            local = transform(parsed['stresses'][key], group['axes_xyz'])
            values = {**{f'normal_{label}': float(local[i, i]) for i, label in enumerate(group['axis_labels'])},
                      'shear_01': float(local[0, 1]), 'shear_02': float(local[0, 2]),
                      'shear_12': float(local[1, 2]),
                      'shear_on_axis_0_plane_magnitude': float(np.hypot(local[0, 1], local[0, 2]))}
            witness = {'element': e, 'integration_point': ip, 'coordinate_xyz_mm': parsed['global coordinates'][key],
                       'global_components_mpa': parsed['stresses'][key], 'local_tensor_mpa': local.tolist()}
            for field, value in values.items():
                extrema = group['extrema'].setdefault(field, {})
                for label, sign in (('minimum', 1.), ('maximum', -1.)):
                    if label not in extrema or sign*value < sign*extrema[label]['value_mpa']:
                        extrema[label] = {'value_mpa': value, **witness}
            group['integration_point_count'] += 1
    return {'candidate': record.get('candidate'), 'integration_point_count': len(expected),
            'groups': list(groups.values()), 'qualified_for_design': False,
            'member_strength_passed': False, 'plywood_strength_passed': False,
            'limits': 'Sampled integration-point demands only, not surface maxima or mesh-converged notch stresses. '
                      'Signed normal/shear components are not combined into a yield or wood-failure criterion. '
                      'No material resistance, beam-column stability, contact traction or real connection qualification. '
                      'Isotropic plywood stress and retained-prism lumber stress cannot certify actual drilled/pocketed parts.'}


def from_directory(directory):
    """Authenticate a standalone run or a cycle through its parent manifest."""
    directory = Path(directory)
    requested_report = json.loads((directory/'report.json').read_text())
    if 'final_cycle_directory' in requested_report:
        directory = directory/requested_report['final_cycle_directory']
    paths = {n: directory/n for n in ('input.json', 'frame.dat', 'frame.inp', 'report.json')}
    report = json.loads(paths['report.json'].read_text())
    manifest_root, manifest, manifest_sha = directory, report, None
    contact_gates = {}
    if 'source_sha256' not in report:
        manifest_root = directory.parent
        manifest_path = manifest_root/'report.json'
        manifest = json.loads(manifest_path.read_text())
        manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        entries = [r for r in manifest.get('contact_cycles', []) if r['directory'] == directory.name]
        report_sha = hashlib.sha256(paths['report.json'].read_bytes()).hexdigest()
        if (len(entries) != 1 or entries[0]['report_sha256'] != report_sha or
                manifest['artifact_sha256'].get(directory.name+'/report.json') != report_sha):
            raise ValueError('Cycle report is not authenticated by parent manifest')
        final = manifest.get('final_cycle_directory') == directory.name
        contact_gates = {'selected_cycle_is_final': final,
                         'parent_contact_diagnostic_checks_passed': manifest.get('contact_diagnostic_checks_passed') is True,
                         'selected_cycle_complementarity_passed': entries[0]['bearing_complementarity_passed'] is True}
    for name in ('input.json', 'frame.dat', 'frame.inp'):
        digest = hashlib.sha256(paths[name].read_bytes()).hexdigest()
        if digest != report['artifact_sha256'].get(name):
            raise ValueError('Native evidence hash mismatch: '+name)
        if manifest_root != directory and manifest['artifact_sha256'].get(directory.name+'/'+name) != digest:
            raise ValueError('Parent evidence hash mismatch: '+name)
    for name, digest in manifest['source_sha256'].items():
        if hashlib.sha256((manifest_root/'source_snapshots'/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Native source snapshot mismatch: '+name)
    record = json.loads(paths['input.json'].read_text())
    result = assess(record, paths['frame.dat'].read_text())
    gates = {k: report[k] for k in ('global_equilibrium_passed', 'mpc_check_passed', 'closed_bearing_assumption_passed')}
    gates.update(contact_gates)
    result.update({'native_numerical_gates': gates, 'native_numerical_gates_passed': all(gates.values()),
                   'native_evidence_sha256': {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()},
                   'parent_manifest_sha256': manifest_sha,
                   'postprocessor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(from_directory(args.directory), stream, indent=2, allow_nan=False)
        stream.write('\n')
