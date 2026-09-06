"""Archive-only sampled geometry/FRD coverage, never mortar weak-law acceptance."""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from fea.floor_contact import FACES
from fea.floor_contact_results import blocks
from fea.full_frame_mortar import verify_deck
from fea.full_frame_refinement import digest, print_bounds, read_archive

FIELDS = ('COPEN', 'CSLIP1', 'CSLIP2', 'CPRESS', 'CSHEAR1', 'CSHEAR2')


def contact_blocks(text):
    """CalculiX ASCII FRD fixed widths; reject incomplete/duplicate CONTACT data."""
    result, time, rows, labels, current, expected = {}, None, None, [], None, None
    for line in text.splitlines():
        if line.startswith('  100CL'):
            if rows is not None:
                raise ValueError('Unterminated CONTACT block')
            cells = line.split()
            time, expected = float(cells[2]), int(cells[3])
            if not math.isfinite(time) or expected <= 0:
                raise ValueError('Invalid FRD time/count')
        elif line.startswith(' -4  CONTACT'):
            if time is None or time in result or rows is not None:
                raise ValueError('Missing/duplicate CONTACT time')
            rows, labels, current = {}, [], None
        elif rows is not None:
            if line.startswith(' -5'):
                labels.append(line.split()[1])
            elif line.startswith((' -1', ' -2')):
                if line.startswith(' -1'):
                    current = int(line[3:13])
                    if current in rows:
                        raise ValueError('Duplicate CONTACT node')
                    rows[current] = []
                if current is None:
                    raise ValueError('CONTACT continuation without node')
                rows[current].extend(float(line[i:i+12]) for i in range(13, len(line), 12) if line[i:i+12].strip())
            elif line.startswith(' -3'):
                if tuple(labels) != FIELDS or len(rows) != expected or any(len(v) != 6 or not all(map(math.isfinite, v)) for v in rows.values()):
                    raise ValueError('Incomplete/nonfinite CONTACT block')
                result[time], rows = rows, None
    if rows is not None or not result:
        raise ValueError('Missing/unterminated CONTACT output')
    return result


def triangle_weights(divisions):
    """Uniform barycentric samples; includes corners/midsides for even divisions."""
    if isinstance(divisions, bool) or not isinstance(divisions, int) or divisions < 2 or divisions % 2:
        raise ValueError('Even integer subdivisions >=2 required')
    bary = np.array([(i/divisions, j/divisions, 1-(i+j)/divisions)
                     for i in range(divisions+1) for j in range(divisions+1-i)])
    a, b, c = bary.T
    return bary, np.column_stack((a*(2*a-1), b*(2*b-1), c*(2*c-1), 4*a*b, 4*b*c, 4*c*a))


def project_bilinear(points, corners):
    """Interior closest stationary point, multistart checked; never clamp escape.

    Reject unsupported folded/degenerate/escaped geometry instead of manufacturing
    a zero gap. This diagnostic is deliberately limited to the present broad
    near-horizontal master bricks; it is not a general contact search engine.
    """
    points, corners = np.asarray(points, dtype=float), np.asarray(corners, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or corners.shape != (4, 3) or not np.isfinite(points).all() or not np.isfinite(corners).all():
        raise ValueError('Finite three-dimensional sample/master coordinates required')
    a = corners.mean(axis=0)
    b = (-corners[0]+corners[1]+corners[2]-corners[3])/4
    c = (-corners[0]-corners[1]+corners[2]+corners[3])/4
    d = (corners[0]-corners[1]+corners[2]-corners[3])/4
    roots = []
    for start in ((0., 0.), (-.75, -.75), (.75, .75)):
        uv = np.tile(start, (len(points), 1))
        for _ in range(30):
            s, t = uv.T
            residual = a+s[:, None]*b+t[:, None]*c+(s*t)[:, None]*d-points
            ds, dt = b+t[:, None]*d, c+s[:, None]*d
            h00, h11 = (ds*ds).sum(1), (dt*dt).sum(1)
            h01 = (ds*dt).sum(1)+(residual*d).sum(1)
            determinant = h00*h11-h01*h01
            if np.any(determinant <= 1e-12) or not np.isfinite(determinant).all():
                raise ValueError('Nonconvex/degenerate projection iteration')
            g0, g1 = (residual*ds).sum(1), (residual*dt).sum(1)
            delta = np.column_stack(((h11*g0-h01*g1)/determinant, (h00*g1-h01*g0)/determinant))
            uv -= delta
            if np.max(np.abs(delta)) < 1e-12:
                break
        else:
            raise ValueError('Projection did not converge')
        if np.max(np.abs(uv)) > 1+1e-10:
            raise ValueError('Sample projects outside paired master patch')
        roots.append(uv)
    if any(np.max(np.abs(root-roots[0])) > 1e-9 for root in roots[1:]):
        raise ValueError('Nonunique projection across starting points')
    s, t = roots[0].T
    surface = a+s[:, None]*b+t[:, None]*c+(s*t)[:, None]*d
    normal = np.cross(b+t[:, None]*d, c+s[:, None]*d)
    norm = np.linalg.norm(normal, axis=1)
    if np.any(norm <= 1e-10) or np.any(normal[:, 2] <= 0):
        raise ValueError('Master Jacobian degenerate or not upward')
    normal /= norm[:, None]
    delta = points-surface
    gap = (delta*normal).sum(1)
    tangent_residual = np.linalg.norm(delta-gap[:, None]*normal, axis=1)
    if max(tangent_residual) > 1e-7:
        raise ValueError('Closest-point tangential residual exceeds1e-7mm')
    return gap, roots[0], float(max(tangent_residual))


def diagnostic(files, subdivisions=(4, 8)):
    record = json.loads(files['frame.json'])
    for name in ('frame.dat', 'frame.frd', 'frame.sta'):
        if digest(files[name]) != record['output_sha256'].get(name):
            raise ValueError('Output digest mismatch: '+name)
    if record['formulation'] != 'mortar':
        raise ValueError('Only MORTAR supported')
    nodes, elements, groups, ground, supports = verify_deck(files['frame.inp'].decode(), record)
    contact = contact_blocks(files['frame.frd'].decode())
    accepted = {float(row[4]) for line in files['frame.sta'].decode().splitlines()
                if len(row := line.split()) == 7 and row[0].isdigit()}
    if set(contact) != accepted:
        raise ValueError('CONTACT times differ from accepted increment times')
    patch_nodes = {name: {elements[e][i] for e, face in faces for i in FACES[face-1]} for name, faces in groups.items()}
    slave_nodes = set.union(*patch_nodes.values())
    if any(set(rows) != slave_nodes for rows in contact.values()):
        raise ValueError('CONTACT slave-node coverage differs from verified deck')
    parsed, endpoints = blocks(files['frame.dat'].decode()), []
    quantization = print_bounds(files['frame.dat'].decode())
    for time in (1., 2.):
        u = parsed.get(('displacements', 'WOODN', time), {})
        if u.keys() != nodes.keys():
            raise ValueError('Missing endpoint wood displacement')
        pos = {n: np.array(p)+u[n] for n, p in nodes.items()}
        patches = {}
        for name, faces in groups.items():
            gu = parsed.get(('displacements', 'GROUND_'+name, time), {})
            if gu.keys() != ground[name].keys():
                raise ValueError('Missing ground displacement')
            # verify_deck regenerates the exact C3D8 S2 card and connectivity.
            master = [np.array(p)+gu[n] for n, p in ground[name].items() if n not in supports[name]]
            nodal_gap, _, residual = project_bilinear([pos[n] for n in sorted(patch_nodes[name])], master)
            samples = []
            for division in subdivisions:
                bary, weights = triangle_weights(division)
                points = np.concatenate([weights@np.array([pos[elements[e][i]] for i in FACES[f-1]]) for e, f in faces])
                gap, uv, err = project_bilinear(points, master)
                low, high = int(np.argmin(gap)), int(np.argmax(gap))
                samples.append({'subdivisions': division, 'count': len(gap), 'gap_mm': [float(gap[low]), float(gap[high])],
                                'minimum_slave_face': faces[low//len(bary)], 'minimum_barycentric': bary[low % len(bary)].tolist(),
                                'minimum_master_coordinates': uv[low].tolist(), 'maximum_projection_tangent_residual_mm': err,
                                'maximum_sample_weight_absolute_sum': float(np.max(np.abs(weights).sum(1)))})
            values = np.array([contact[time][n] for n in sorted(patch_nodes[name])])
            excess = np.hypot(values[:, 4], values[:, 5])-record['mu']*values[:, 3]
            # frd.c float-casts then prints5decimal exponent fields. These are
            # representation bounds, not local contact/solver/model tolerances.
            field_bounds = np.array([[.5*10**(int(f'{v:.5E}'.split('E')[1])-5)+abs(v)*2**-24+2**-150 for v in row] for row in values])
            excess_bounds = np.hypot(field_bounds[:, 4], field_bounds[:, 5])+record['mu']*field_bounds[:, 3]
            wood_bound = max(math.hypot(*quantization['displacements', 'WOODN', time][n]) for n in patch_nodes[name])
            master_bound = max(math.hypot(*quantization['displacements', 'GROUND_'+name, time][n]) for n in ground[name] if n not in supports[name])
            corners = {elements[e][i] for e, face in faces for i in FACES[face-1][:3]}
            midsides = patch_nodes[name]-corners
            patches[name] = {'slave_node_count': len(values), 'nodal_geometric_gap_mm': [float(min(nodal_gap)), float(max(nodal_gap))],
                             'nodal_projection_tangent_residual_mm': residual, 'quadratic_face_samples': samples,
                             'frd_field_extrema_not_law_checks': {field: [float(min(values[:, i])), float(max(values[:, i]))] for i, field in enumerate(FIELDS)},
                             'corner_midside_counts': {'corner': len(corners), 'midside': len(midsides)},
                             'displayed_friction_excess_not_law_check': [float(min(excess)), float(max(excess))],
                             'displayed_excess_representation_bound_range': [float(min(excess_bounds)), float(max(excess_bounds))],
                             'displayed_excess_above_representation_bound_count_NOT_law_violations': int(sum(excess > excess_bounds)),
                             'displayed_excess_above_bound_nodes_NOT_law_violations': [n for n, above in zip(sorted(patch_nodes[name]), excess > excess_bounds, strict=True) if above],
                             'displayed_excess_maximum_above_bound': float(max(excess-excess_bounds)),
                             'maximum_DAT_wood_node_position_rounding_mm': wood_bound,
                             'maximum_DAT_master_node_position_rounding_mm': master_bound,
                             'maximum_sample_input_position_rounding_mm': wood_bound*max(s['maximum_sample_weight_absolute_sum'] for s in samples),
                             'uncertainty_qualification': 'Position bounds propagate DAT U rounding through absolute quadratic shape weights; master bilinear weights sum1 inside patch. They do not bound normal/projection changes, input coordinate rounding or continuous sampling error; signed gaps are not certified intervals. FRD excess bounds include float cast and printing only, and are NOT law tolerances.'}
        endpoints.append({'time': time, 'patches': patches})
    return {'status': 'SAMPLED GEOMETRY/COVERAGE ONLY; LOCAL WEAK LAW NOT VALIDATED',
            'deck_sha256': record['deck_sha256'], 'dat_sha256': digest(files['frame.dat']), 'frd_sha256': digest(files['frame.frd']),
            'increment': record['increment'], 'accepted_contact_times': sorted(accepted), 'slave_node_count': len(slave_nodes),
            'limitations': 'Finite LINEAR compliance permits penetration. FRD opening is weighted, not physical distance; transformed stresses cannot establish pointwise law. Samples and multistart Newton do not prove continuous extrema/global uniqueness. DAT/FRD quantization and solver/model errors remain; printed geometry differences are diagnostic, not acceptance tolerances.',
            'endpoints': endpoints}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    root = args.archive.parent
    report = json.loads((root/'report.json').read_text())
    items = report['runs'] if 'runs' in report else report['formulations']
    expected = next(item for item in items.values() if item['archive'] == args.archive.name)
    if digest(args.archive.read_bytes()) != expected['archive_sha256']:
        raise ValueError('Archive differs from published digest')
    files = read_archive(args.archive)
    if {name: digest(raw) for name, raw in files.items()} != expected['archive_contents_sha256']:
        raise ValueError('Archive contents differ from publication')
    print(json.dumps(diagnostic(files), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
