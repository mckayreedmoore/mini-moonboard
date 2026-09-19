"""Diagnostic signed center interface loads from an existing native report.

Use the matching native input record. Baseline ML24Z/SDS loads are provisional
and are not candidate AB205/bolted demands or connection acceptance.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


def _vector(values, label):
    if len(values) != 3 or not all(math.isfinite(float(x)) for x in values):
        raise ValueError(f'Invalid {label} vector')
    return [float(x) for x in values]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _wrench(rows, body, origin):
    force, moment, radius, moment_radius = [0.]*3, [0.]*3, [0.]*3, [0.]*3
    for row in rows:
        sign = 1 if row['first'] == body else -1
        f = _vector(row['force_on_first_xyz_n'], 'force')
        arm = [x-y for x, y in zip(_vector(row['point'], 'point'), origin)]
        m = _cross(arm, f)
        error = _vector(row.get('force_rounding_radius_xyz_n', [0.]*3), 'rounding radius')
        for i in range(3):
            force[i] += sign*f[i]
            moment[i] += sign*m[i]
            radius[i] += abs(error[i])
            moment_radius[i] += (abs(arm[(i+1)%3])*abs(error[(i+2)%3])
                                 + abs(arm[(i+2)%3])*abs(error[(i+1)%3]))
    return {'force_xyz_n': force, 'moment_xyz_nmm': moment}, radius, moment_radius


def _physical_row(name, owner, physical):
    if name not in physical:
        raise ValueError(f'Missing physical connection: {name}')
    row = physical[name]
    if any(row[k] != owner[k] for k in ('first', 'second', 'point')):
        raise ValueError(f'Physical connection ownership mismatch: {name}')
    first = _vector(row['force_on_first_xyz_n'], 'first force')
    second = _vector(row['force_on_second_xyz_n'], 'second force')
    if any(abs(a+b) > 1e-7 for a, b in zip(first, second)):
        raise ValueError(f'Physical connection action-reaction mismatch: {name}')
    return row


def extract(report, record, principal, post, header='base_header', header_origin_xyz_mm=None):
    """Return simultaneous signed actions on both sides of each center interface."""
    if report.get('candidate') != record.get('candidate'):
        raise ValueError('Candidate mismatch between report and input record')
    if len({principal, post, header}) != 3:
        raise ValueError('Center member and header names must be distinct')
    physical = report['physical_connection_forces']
    owners = record['connection_ownership']
    stations = record['angle_stations']
    interfaces = {}
    selected_header_names = set()
    for key, member in (('principal_header', principal), ('post_header', post)):
        matching = [s for s in stations if set(s['members']) == {member, header}]
        if len(matching) != 1:
            raise ValueError(f'Expected one angle station for {member}/{header}')
        clip = matching[0]['name']
        origin = _vector(matching[0]['origin'], 'origin')
        selected = {name: owner for name, owner in owners.items()
                    if ({owner['first'], owner['second']} == {member, header}
                        or {owner['first'], owner['second']} in ({member, clip}, {header, clip}))}
        if not selected:
            raise ValueError(f'No physical connections for {member}/{header}')
        groups = {'direct': [], 'member_clip': [], 'header_clip': []}
        for name, owner in selected.items():
            row = _physical_row(name, owner, physical)
            pair = {row['first'], row['second']}
            group = ('direct' if pair == {member, header} else
                     'member_clip' if member in pair else 'header_clip')
            groups[group].append(name)
        if not groups['member_clip'] or not groups['header_clip']:
            raise ValueError(f'Incomplete clip connection sides: {clip}')
        member_rows = [physical[n] for n in groups['direct'] + groups['member_clip']]
        header_rows = [physical[n] for n in groups['direct'] + groups['header_clip']]
        selected_header_names.update(groups['direct'] + groups['header_clip'])
        on_member, mr, mmr = _wrench(member_rows, member, origin)
        on_header, hr, hmr = _wrench(header_rows, header, origin)
        member_components = {
            'direct': _wrench([physical[n] for n in groups['direct']], member, origin)[0],
            'via_clip': _wrench([physical[n] for n in groups['member_clip']], member, origin)[0],
        }
        header_components = {
            'direct': _wrench([physical[n] for n in groups['direct']], header, origin)[0],
            'via_clip': _wrench([physical[n] for n in groups['header_clip']], header, origin)[0],
        }
        residual_force = [a+b for a, b in zip(on_member['force_xyz_n'], on_header['force_xyz_n'])]
        residual_moment = [a+b for a, b in zip(on_member['moment_xyz_nmm'], on_header['moment_xyz_nmm'])]
        passed = (all(abs(x) <= a+b+0.1 for x, a, b in zip(residual_force, mr, hr)) and
                  all(abs(x) <= a+b+20. for x, a, b in zip(residual_moment, mmr, hmr)))
        interfaces[key] = {'center_member': member, 'header': header, 'clip': clip,
                           'origin_xyz_mm': origin, 'connection_names': groups,
                           'on_center_member': on_member, 'on_header': on_header,
                           'on_center_member_components': member_components,
                           'on_header_components': header_components,
                           'residual': {'force_xyz_n': residual_force,
                                        'moment_xyz_nmm': residual_moment, 'passed': passed}}
    header_origin = _vector(header_origin_xyz_mm if header_origin_xyz_mm is not None
                            else interfaces['principal_header']['origin_xyz_mm'], 'header origin')
    header_names = [name for name, owner in owners.items()
                    if header in (owner['first'], owner['second'])]
    for name in header_names:
        _physical_row(name, owners[name], physical)
    unexpected = [name for name, row in physical.items()
                  if header in (row['first'], row['second']) and name not in owners]
    if unexpected:
        raise ValueError(f'Header physical connection absent from record: {unexpected[0]}')
    other_names = [name for name in header_names if name not in selected_header_names]
    selected_wrench, _, _ = _wrench([physical[n] for n in header_names
                                    if n in selected_header_names], header, header_origin)
    other_wrench, _, _ = _wrench([physical[n] for n in other_names], header, header_origin)
    all_wrench, force_radius, moment_radius = _wrench(
        [physical[n] for n in header_names], header, header_origin)
    gravity = record.get('gravity_points', {}).get(header)
    external = None
    residual = {'available': False, 'passed': None}
    if gravity is not None:
        force = _vector(gravity['force'], 'header external force')
        arm = [x-y for x, y in zip(_vector(gravity['point'], 'header external point'),
                                   header_origin)]
        external = {'source': 'record.gravity_points[header]',
                    'point_xyz_mm': _vector(gravity['point'], 'header external point'),
                    'force_xyz_n': force, 'moment_xyz_nmm': _cross(arm, force)}
        rf = [a+b for a, b in zip(all_wrench['force_xyz_n'], force)]
        rm = [a+b for a, b in zip(all_wrench['moment_xyz_nmm'], external['moment_xyz_nmm'])]
        residual = {'available': True, 'force_xyz_n': rf, 'moment_xyz_nmm': rm,
                    'passed': (all(abs(x) <= r+0.1 for x, r in zip(rf, force_radius)) and
                               all(abs(x) <= r+20. for x, r in zip(rm, moment_radius)))}
    header_free_body = {'header': header, 'origin_xyz_mm': header_origin,
                        'selected_interfaces': {'connection_names': sorted(selected_header_names),
                                                'wrench': selected_wrench},
                        'other_attachments': {'connection_names': other_names,
                                              'wrench': other_wrench},
                        'all_connections': all_wrench,
                        'external_load': external, 'residual': residual}
    candidate = report['candidate']
    classification = ('provisional_baseline_ML24Z_SDS'
                      if candidate == 'compact-floor-flush-development' else
                      'provisional_kerf_right_ML24Z_SDS_proxy'
                      if candidate == 'bolted-kerf-right-diagnostic-proxy' else
                      'unqualified_native_diagnostic')
    return {'source_candidate': candidate, 'classification': classification,
            'scope': 'Signed simultaneous native connector resultants only; no bolt demand, drilling or acceptance claim',
            'interfaces': interfaces, 'header_free_body': header_free_body}


def extract_files(report_path, record_path, principal, post, header='base_header',
                  header_origin_xyz_mm=None):
    """Extract only from an accepted report and its manifested final-cycle input."""
    report_path, record_path = Path(report_path), Path(record_path)
    report_bytes, record_bytes = report_path.read_bytes(), record_path.read_bytes()
    report, record = json.loads(report_bytes), json.loads(record_bytes)
    if report_path.name != 'report.json':
        raise ValueError('Expected final report.json artifact')
    cycles = report.get('contact_cycles')
    if not cycles or cycles[-1].get('directory') != record_path.parent.name or record_path.name != 'input.json':
        raise ValueError('Input record is not the final report cycle')
    try:
        relative = record_path.resolve().relative_to(report_path.parent.resolve()).as_posix()
    except ValueError as error:
        raise ValueError('Input record is outside report artifact') from error
    record_hash = hashlib.sha256(record_bytes).hexdigest()
    if (relative != f"{cycles[-1]['directory']}/input.json"
            or report.get('artifact_sha256', {}).get(relative) != record_hash):
        raise ValueError('Input record digest does not match report artifact manifest')
    sources = ('fea/current_response_run.py', 'scripts/bolted_kerf_diagnostic_probe.py',
               'scripts/bolted_kerf_native_diagnostic.py')
    for source in sources:
        source_path = report_path.parent / 'source_snapshots' / source
        source_hash = report.get('source_sha256', {}).get(source)
        if source != sources[0] and not source_path.exists() and source_hash is None:
            continue
        if (not source_hash or report.get('artifact_sha256', {}).get(f'source_snapshots/{source}') != source_hash
                or not source_path.is_file()
                or hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash):
            raise ValueError(f'Native producer source identity mismatch: {source}')
    if report.get('numerically_accepted') is not True:
        raise ValueError('Report is not numerically accepted')
    if report.get('contact_active_set_converged') is not True or cycles[-1].get('contact_passed') is not True:
        raise ValueError('Native convergence failed')
    if any(report.get(key) is not True for key in
           ('global_equilibrium_passed', 'member_equilibrium_passed', 'mpc_check_passed')):
        raise ValueError('Native equilibrium failed')
    scope = report.get('diagnostic_scope')
    scope_path = report_path.parent / 'diagnostic-scope.json'
    if (not scope_path.is_file()
            or report.get('artifact_sha256', {}).get(scope_path.name)
            != hashlib.sha256(scope_path.read_bytes()).hexdigest()
            or json.loads(scope_path.read_bytes()) != scope):
        raise ValueError('Diagnostic scope sidecar or digest mismatch')
    if (not isinstance(scope, dict)
            or scope.get('source_geometry') != 'compact-floor-flush-bolted-development-kerf-right'
            or scope.get('numerically_converged', True) is not True
            or scope.get('bolted_joint_demands') is not False
            or scope.get('acceptance') is not False):
        raise ValueError('Missing or mismatched diagnostic scope')
    proxy = 'baseline ML24Z angles and SDS screws'
    if (report.get('candidate') != 'bolted-kerf-right-diagnostic-proxy'
            or record.get('candidate') != report['candidate']
            or scope.get('connector_proxy') != proxy
            or record.get('provisional_structural_connectors') != proxy
            or record.get('diagnostic_only') is not True
            or record.get('bolted_joint_demands') is not False):
        raise ValueError('Candidate or connector proxy mismatch')
    cases = {'a12-rear': ('A12', 0, 300), 'a12-forward': ('A12', 0, -300),
             'a12-left': ('A12', -300, 0), 'k12-right': ('K12', 300, 0),
             'k12-rear': ('K12', 0, 300), 'a1-rear': ('A1', 0, 300)}
    case = scope.get('case')
    expected = cases.get(case)
    params = report.get('parameters', {})
    force = record.get('force_xyz_n')
    if (not expected or report_path.parent.name != case or record.get('hold') != expected[0]
            or params.get('hold') != expected[0] or force != params.get('force_xyz_n')
            or not isinstance(force, list) or len(force) != 3
            or force[:2] != list(expected[1:])):
        raise ValueError('Load case mismatch')
    bounds = record.get('kerf_panel_bounds', {})
    for name in ('main_lower', 'main_upper', 'kicker'):
        for side, expected_width in (('left', [-1219.2, -1.5875]),
                                     ('right', [-1.5875, 1216.025])):
            row = bounds.get(f'{name}_{side}', {})
            for key in ('actual_x_mm', 'mesh_x_mm'):
                width = row.get(key)
                if (not isinstance(width, list) or len(width) != 2
                        or any(not math.isclose(a, b, abs_tol=1e-4)
                               for a, b in zip(width, expected_width))):
                    raise ValueError('Missing or mismatched kerf-right width metadata')
    result = extract(report, record, principal, post, header, header_origin_xyz_mm)
    interface_passed = all(row['residual']['passed'] for row in result['interfaces'].values())
    header_residual = result['header_free_body']['residual']
    equilibrium = ('passed' if header_residual['passed'] is True and interface_passed else
                   'unavailable' if header_residual['available'] is False and interface_passed else
                   'failed')
    if equilibrium == 'failed':
        raise ValueError('Extracted interface or header equilibrium failed')
    result['source'] = {'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
                        'record_sha256': record_hash, 'case': case,
                        'candidate': report['candidate'],
                        'diagnostic_scope': scope, 'parameters': params,
                        'record_artifact': relative,
                        'producer_sha256': {source: report['source_sha256'][source]
                                            for source in sources if source in report['source_sha256']}}
    result['status'] = {'source': 'verified', 'convergence': 'passed',
                        'equilibrium': equilibrium}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('record', type=Path)
    parser.add_argument('principal')
    parser.add_argument('post')
    parser.add_argument('--header', default='base_header')
    parser.add_argument('--header-origin', nargs=3, type=float, metavar=('X', 'Y', 'Z'))
    args = parser.parse_args()
    print(json.dumps(extract_files(args.report, args.record, args.principal, args.post,
                                   args.header, args.header_origin), indent=2))
