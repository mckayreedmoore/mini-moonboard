"""Recover mechanical S8 translations from native expanded opposite-face output.

Original shell-node output includes thickness warping and does not reproduce
SPRING2/MPC translations in the verified coupon. Preserve raw output; reconstruct
only the opposing-face average, with its actual FRD rounding intervals.
"""
import re

import numpy as np

from fea import frd_displacements
from fea import horizontal_panel_frame as frame


def expanded_faces(record, text):
    blocks = re.findall(r'ELEMENT\s+(\d+) with label "S8\s*" and with nodes:\s*([\d\s]+?)'
                        r'is expanded into a "C3D20 L " element with topology:\s*([\d\s]+?)(?=\n\s*\n|\Z)', text)
    expected = {int(e): ids for e, (kind, ids, _) in record['elements'].items() if kind == 'S8'}
    seen, faces = set(), {}
    for element, original, expanded in blocks:
        element = int(element)
        original, expanded = list(map(int, original.split())), list(map(int, expanded.split()))
        if element in seen or element not in expected or original != expected[element] or len(expanded) != 20:
            raise ValueError('Expanded shell topology differs from native input')
        seen.add(element)
        for index, node in enumerate(original):
            top = index if index < 4 else index+4
            pair = (expanded[top], expanded[top+4])
            if node in faces and faces[node] != pair:
                raise ValueError('Multiple inconsistent expanded-face pairs at shell node')
            faces[node] = pair
    if not expected or seen != expected.keys():
        raise ValueError('Missing expanded S8 topology')
    return faces


def half_last_place(token):
    mantissa, exponent = token.upper().replace('D', 'E').split('E')
    places = len(mantissa.split('.')[1])
    return .5*10.**(int(exponent)-places)


def frd_roundoff(token):
    """Bound double-to-float conversion followed by ASCII decimal rounding.

    CalculiX 2.21 frdvector.c:42-44 and frd.c cast to float before %.5E.
    Source: https://www.dhondt.de/ccx_2.21.src.tar.bz2
    With binary32 unit roundoff u, |x-fl(x)| <= u*|x| (normal values).
    |fl(x)| <= |printed|+decimal gives the bound below; half the smallest
    subnormal spacing covers underflow. This also applies to coordinates.
    """
    decimal = half_last_place(token)
    unit = 2.**-24
    conversion = max(2.**-150, unit*(abs(float(token))+decimal)/(1.-unit))
    return decimal+conversion


def expanded_displacements(text):
    mesh_nodes, coordinates, coordinate_precision, in_mesh = set(), {}, {}, False
    precision, in_disp, blocks = {}, False, 0
    for line in text.splitlines():
        if line.startswith('    2C'):
            in_mesh = True
        elif in_mesh and line.startswith(' -1'):
            node = int(line[3:13])
            mesh_nodes.add(node)
            coordinates[node] = [float(line[i:i+12]) for i in (13, 25, 37)]
            coordinate_precision[node] = [frd_roundoff(line[i:i+12].strip()) for i in (13, 25, 37)]
        elif in_mesh and line.startswith(' -3'):
            in_mesh = False
        if line.startswith(' -4  DISP'):
            in_disp = True
            blocks += 1
        elif in_disp and line.startswith(' -1'):
            precision[int(line[3:13])] = [frd_roundoff(line[i:i+12].strip()) for i in (13, 25, 37)]
        elif in_disp and line.startswith(' -3'):
            in_disp = False
    if blocks != 1:
        raise ValueError('Require one static expanded DISP block')
    values = frd_displacements.read(text, mesh_nodes, mesh_nodes)
    if len(values) != 1 or precision.keys() != mesh_nodes:
        raise ValueError('Expanded displacement precision coverage differs')
    return next(iter(values.values())), precision, coordinates, coordinate_precision


def recover(record, data, frd, expansion):
    faces = expanded_faces(record, expansion)
    expanded, expanded_precision, coordinates, coordinate_precision = expanded_displacements(frd)
    for kind, ids, _ in record['elements'].values():
        if kind != 'S8':
            continue
        points = [np.array(record['nodes'].get(n, record['nodes'].get(str(n)))) for n in ids]
        normal = np.cross(points[1]-points[0], points[3]-points[0])
        normal = normal/np.linalg.norm(normal)
        for node, original in zip(ids, points, strict=True):
            top, bottom = faces[node]
            centre = (np.array(coordinates[top])+coordinates[bottom])/2
            radius = (np.array(coordinate_precision[top])+coordinate_precision[bottom])/2
            delta = np.array(coordinates[bottom])-coordinates[top]
            if np.any(abs(centre-original) > radius+1.e-6):
                raise ValueError('Expanded face midpoint differs from original shell node')
            if (np.linalg.norm(np.cross(delta, normal)) > 2*np.linalg.norm(radius)+1.e-6
                    or abs(abs(delta@normal)-frame.panel_kernel.THICKNESS) > 2*np.linalg.norm(radius)+1.e-6):
                raise ValueError('Expanded shell thickness/orientation differs from native input')
    u = frame.panel_kernel.read_blocks(data)['displacements']
    precision = frame.displacement_roundoff(data)
    common = u.keys() & expanded.keys()
    for node in common:
        radius = np.array(precision[node])+expanded_precision[node]
        allowed = radius+1.e-12
        if np.any(abs(np.array(u[node])-expanded[node]) > allowed):
            raise ValueError('DAT/FRD original-node displacement intervals disagree')
    for node, (top, bottom) in faces.items():
        u[node] = ((np.array(expanded[top])+expanded[bottom])/2).tolist()
        precision[node] = ((np.array(expanded_precision[top])+expanded_precision[bottom])/2).tolist()
    # frame.assess consumes DAT text. These derived values are an adapter only;
    # all acceptance intervals below use actual original/FRD print precision.
    match = re.search(r'(^\s*displacements\s*\([^\n]*\n)(.*?)(?=\n\s*[A-Za-z]|\Z)', data, re.MULTILINE|re.DOTALL)
    if match is None:
        raise ValueError('Missing original displacement block')
    replacement = '\n'+''.join(f'{n:10d} '+ ' '.join(f'{v:.12E}' for v in values)+'\n' for n, values in sorted(u.items()))+'\n'
    derived = data[:match.start(2)]+replacement+data[match.end(2):]
    return derived, u, precision


def assess(record, data, frd, expansion):
    derived, u, precision = recover(record, data, frd, expansion)
    result = frame.assess(record, derived)
    mpc = frame.mpc_intervals(record['equations'], u, precision)
    result.update(maximum_mpc_residual_mm=mpc['maximum_printed_residual_mm'],
                  mpc_printed_precision_audit=mpc, mpc_check_passed=mpc['passed'],
                  displacement_recovery={'method': 'opposite expanded S8 face average',
                    'shell_nodes_recovered': len(expanded_faces(record, expansion)),
                    'raw_dat_modified': False, 'rounding_basis': 'Original DAT for non-shell nodes; half-sum of FRD decimal plus binary32 conversion intervals for shell nodes'})
    return result
