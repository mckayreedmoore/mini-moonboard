"""Diagnostic signed center interface loads from an existing native report.

Use the matching native input record. Baseline ML24Z/SDS loads are provisional
and are not candidate AB205/bolted demands or connection acceptance.
"""

import argparse
import gzip
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
        residual_force = [a+b for a, b in zip(on_member['force_xyz_n'], on_header['force_xyz_n'])]
        residual_moment = [a+b for a, b in zip(on_member['moment_xyz_nmm'], on_header['moment_xyz_nmm'])]
        passed = (all(abs(x) <= a+b+0.1 for x, a, b in zip(residual_force, mr, hr)) and
                  all(abs(x) <= a+b+20. for x, a, b in zip(residual_moment, mmr, hmr)))
        interfaces[key] = {'center_member': member, 'header': header, 'clip': clip,
                           'origin_xyz_mm': origin, 'connection_names': groups,
                           'on_center_member': on_member, 'on_header': on_header,
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
    return {'source_candidate': candidate,
            'classification': ('provisional_baseline_ML24Z_SDS'
                               if candidate == 'compact-floor-flush-development'
                               else 'unqualified_native_diagnostic'),
            'scope': 'Signed simultaneous native connector resultants only; no bolt demand, drilling or acceptance claim',
            'interfaces': interfaces, 'header_free_body': header_free_body}


def _read_json(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt') as stream:
        return json.load(stream)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('record', type=Path)
    parser.add_argument('principal')
    parser.add_argument('post')
    parser.add_argument('--header', default='base_header')
    parser.add_argument('--header-origin', nargs=3, type=float, metavar=('X', 'Y', 'Z'))
    args = parser.parse_args()
    print(json.dumps(extract(_read_json(args.report), _read_json(args.record),
                             args.principal, args.post, args.header, args.header_origin), indent=2))
