"""Tighter finite-area dual supports and saved-pose contact-energy uppers.

Keep the existing continuous contact law, loads and core. Reuse its bound
driver with declared support/integration changes; calculate no new response.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from functools import partial
from itertools import pairwise
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = {'path': 'scripts/eoere_normal_patch_reactions.py',
        'sha256': '2453ea37c5b6f36db193518ebf0e42cc09dc33d9ffc9f2e1d2f69854ed9fc3cd'}
POWERS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def private(reference, pins):
    module = ModuleType('_eoere_verified_supports_'+Path(reference['path']).stem)
    module.__file__ = str(ROOT/reference['path'])
    exec(compile(captured(reference, pins), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned buffer
    return module


def rectangle(box):
    x0, x1, y0, y1 = map(F, box)
    require(x0 < x1 and y0 < y1, 'positive rational rectangle required')
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def symmetric_tiles(domain, center, half_widths, padding, trace, method):
    """Remove hole-cover squares and their central reflections from a box."""
    x, y = map(F, center); hx, hy = map(F, half_widths); padding = F(padding)
    require(hx > 0 and hy > 0 and padding > 0, 'positive support and strict hole padding required')
    outer = x-hx, x+hx, y-hy, y+hy
    polygon = [tuple(map(F, p)) for p in domain['polygon']]
    holes = [tuple(map(F, h)) for h in domain['holes']]
    require(all(trace.previous().inside(polygon, p) for p in rectangle(outer)), 'support box must be strictly inside the outer polygon')
    excluded = []
    for cx, cy, radius in holes:
        require(radius > 0, 'positive retained hole radius required')
        r = radius+padding
        for a, b in ((cx, cy), (2*x-cx, 2*y-cy)):
            excluded.append((a-r, a+r, b-r, b+r))
    xs = sorted({outer[0], outer[1], *(max(outer[0], min(outer[1], value)) for e in excluded for value in e[:2])})
    ys = sorted({outer[2], outer[3], *(max(outer[2], min(outer[3], value)) for e in excluded for value in e[2:])})
    tiles = []
    for x0, x1 in pairwise(xs):
        for y0, y1 in pairwise(ys):
            mid = (x0+x1)/2, (y0+y1)/2
            if any(a <= mid[0] <= b and c <= mid[1] <= d for a, b, c, d in excluded):
                continue
            box = x0, x1, y0, y1
            require(all(trace.previous().box_hole_clearance(box, hole) > 0 for hole in holes), 'every retained tile must be strictly outside both holes')
            tiles.append(rectangle(box))
    moments = [method.geometry.moments(p, F(0)) for p in tiles]
    area, mx, my = (sum((m[j] for m in moments), F(0)) for j in range(3))
    require(area > 0 and mx == area*x and my == area*y, 'positive symmetric material support with exact original first moments required')
    return tiles, area


def patch_supports(domain, fraction, padding, h):
    fraction = F(fraction)
    require(0 < fraction < 1, 'strict interior support fraction required')
    polygon = [tuple(map(F, p)) for p in domain['polygon']]
    width = max(p[0] for p in polygon)-min(p[0] for p in polygon)
    height = max(p[1] for p in polygon)-min(p[1] for p in polygon)
    require(width > 0 and height > 0, 'positive outer patch dimensions required')
    hx, hy = width/4, height/4
    centers = [tuple(map(F, p)) for p in domain['samples']]
    require(centers, 'nonempty original centroid set required')
    limits = [F(1)]
    for x, y in centers:
        for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
            dx, dy = b[0]-a[0], b[1]-a[1]
            denominator = abs(dx)*hy+abs(dy)*hx
            require(denominator > 0, 'nonzero outer polygon edge required')
            limits.append((dx*(y-a[1])-dy*(x-a[0]))/denominator)
    for i, a in enumerate(centers):
        for b in centers[i+1:]:
            limits.append(max(abs(a[0]-b[0])/(2*hx), abs(a[1]-b[1])/(2*hy)))
    scale = min(limits)*fraction
    require(scale > 0, 'distinct original interior centroids required')
    half = hx*scale, hy*scale
    boxes = [(x-half[0], x+half[0], y-half[1], y+half[1]) for x, y in centers]
    require(h.base_disjoint(boxes), 'complete pressure support boxes must be disjoint')
    supports = [symmetric_tiles(domain, center, half, padding, h.trace, h.method) for center in centers]
    return half, supports


def union_average(domain, tiles, timber, port, fitting, normal, h):
    """Integrate each local point-map polynomial against union area moments."""
    grouped = {}
    all_regions = []
    for tile in tiles:
        regions = h.trace.pieces(dict(domain, polygon=tile), timber, h.method.geometry, h.method.poly)
        all_regions.extend(regions)
        for region in regions:
            key = region['mode'], region['segment']
            moments = grouped.setdefault(key, {powers: F(0) for powers in POWERS})
            for powers in POWERS:
                moments[powers] += h.transfer.triangle_integral({powers: F(1)}, region['polygon'], h.method.poly.evaluate)
    area = sum((m[0, 0] for m in grouped.values()), F(0))
    require(area > 0, 'positive complete union area required')
    relevant = h.base_relevant(timber, fitting, all_regions)
    point = h.trace.world_polynomials(domain)
    row = {}
    for coordinate in relevant:
        pose = defaultdict(F, {coordinate: F(1)})
        total = F(0)
        for (mode, segment), moments in grouped.items():
            polynomial = h.trace.gap_polynomial(point, timber, port, fitting, pose, normal, mode, segment, h.method.poly)
            require(set(polynomial) <= set(POWERS), 'quadratic source point map required')
            total -= sum((F(value)*moments[powers] for powers, value in polynomial.items()), F(0))
        if total:
            row[coordinate] = total/area
    return row, area, len(all_regions), grouped


def affine_energy_upper(polynomial, polygon, density, subdivisions, h):
    """Integrate squared affine compression majorants on a complete grid."""
    polynomial = {p: F(v) for p, v in polynomial.items()}
    polygon = [tuple(map(F, p)) for p in polygon]; density = F(density)
    require(set(polynomial) <= set(POWERS) and density > 0 and type(subdivisions) is int and 1 <= subdivisions <= 32,
            'quadratic trace, positive density and bounded integer grid required')
    x0, x1, y0, y1 = h.trace.bounding_box(polygon)
    xs = [x0+(x1-x0)*F(i, subdivisions) for i in range(subdivisions+1)]
    ys = [y0+(y1-y0)*F(i, subdivisions) for i in range(subdivisions+1)]
    energy, area, cells = F(0), F(0), 0
    for xa, xb in pairwise(xs):
        for ya, yb in pairwise(ys):
            piece = polygon
            for plane in ((-xa, F(1), F(0)), (xb, -F(1), F(0)), (-ya, F(0), F(1)), (yb, F(0), -F(1))):
                piece = h.method.geometry.clip(piece, plane)
            measure = h.method.geometry.moments(piece, F(0))[0]
            if measure <= 0:
                continue
            area += measure; cells += 1
            box = h.trace.bounding_box(piece); cx, cy = (box[0]+box[1])/2, (box[2]+box[3])/2
            gx = polynomial.get((1, 0), F(0))+2*polynomial.get((2, 0), F(0))*cx+polynomial.get((1, 1), F(0))*cy
            gy = polynomial.get((0, 1), F(0))+2*polynomial.get((0, 2), F(0))*cy+polynomial.get((1, 1), F(0))*cx
            a0 = h.method.poly.evaluate(polynomial, (cx, cy))-gx*cx-gy*cy
            affine = {(0, 0): a0, (1, 0): gx, (0, 1): gy}
            remainder = h.method.poly.add(polynomial, h.method.poly.scaled(affine, -F(1)))
            lower, _ = h.trace.polynomial_bounds(remainder, box, h.method)
            compression = {(0, 0): -a0-lower, (1, 0): -gx, (0, 1): -gy}
            positive = h.method.geometry.clip(piece, tuple(compression[p] for p in ((0, 0), (1, 0), (0, 1))))
            if h.method.geometry.moments(positive, F(0))[0] > 0:
                square = h.method.poly.multiply(compression, compression)
                integral = h.transfer.triangle_integral(square, positive, h.method.poly.evaluate)
                require(integral >= 0, 'nonnegative exact affine-square integral required')
                energy += h.bounds.upper(density*integral/2)
    require(area == h.method.geometry.moments(polygon, F(0))[0], 'grid must cover the complete outer polygon exactly')
    return energy, cells


def refined_rows(field, chart, components, ports, maps, domains, fraction, h, *, padding):
    lookup = {c['id']: j for j, c in enumerate(components)}
    contacts = {p['descriptor']['id']: p['descriptor'] for p in ports if p['descriptor']['kind'] == 'flange_contact'}
    records = []
    for patch in field['source_inputs']['flange_shared_face_patches']:
        nominal = domains[patch['id']]; domain = nominal['analytic_domain']
        require(patch['trimmed_region_signature_sha256'] == nominal['trimmed_region_signature_sha256'], 'own retained nominal domain required')
        timber, fitting = chart['timber'][patch['second']], chart['four_port_fittings'][patch['first']]
        port, = [p for p in fitting['ports'] if p['id'] == patch['source_owned_port_id']]
        indices = fitting['dof_indices'][6*port['port_index']:6*(port['port_index']+1)]
        half, supports = patch_supports(domain, fraction, padding, h)
        for cell, (tiles, measure) in zip(patch['cells'], supports, strict=True):
            identity = patch['id'].rsplit('/timber-face/', 1)[0]+'/'+cell['id']; j = lookup[identity]
            normal = contacts[identity]['direction_xyz']
            row, area, count, moments = union_average(domain, tiles, timber, port, indices, normal, h)
            require(area == measure, 'complete union integral must retain exact support area')
            density = F(nominal['declared_existing_stiffness_n_mm3'])
            components[j] = dict(components[j], row=row, stiffness=density*area)
            records.append({'patch_id': patch['id'], 'id': identity, 'column': j, 'normal_director_xyz': normal,
                'exact_outer_half_widths_xy_mm': list(map(str, half)), 'support_tiles_xy_mm': [[[str(v) for v in p] for p in t] for t in tiles],
                'exact_area_mm2': str(area), 'exact_density_n_mm3': str(density), 'station_piece_count': count,
                'station_union_moments': [{'mode': mode, 'segment': segment, 'moments_ij': [[i, j, str(v)] for (i, j), v in sorted(m.items())]}
                                          for (mode, segment), m in moments.items()],
                'exact_full_compression_row': {str(i): str(v) for i, v in row.items()},
                'exact_rigid_compression_row': {str(i): str(v) for i, v in h.core.product([row], maps)[0].items()}})
    require(len(records) == len({r['column'] for r in records}) == 352, 'all original normal columns require own union supports')
    return records


def driver_tree(data):
    """Change only the two support-control lookups and their literal gate."""
    tree = ast.parse(data, filename=BASE['path'])
    run, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run']
    lookups = [n for n in ast.walk(run) if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
               and n.value.id == 'inputs' and isinstance(n.slice, ast.Constant) and n.slice.value == 'material_box_maximum_half_width_mm']
    gates = [n for n in ast.walk(run) if isinstance(n, ast.Compare) and len(n.ops) == len(n.comparators) == 1
             and n.left in lookups and isinstance(n.ops[0], ast.Eq) and isinstance(n.comparators[0], ast.Constant)
             and n.comparators[0].value == '8']
    require(len(lookups) == 2 and len(gates) == 1, 'exact preserved support-control AST required')
    for node in lookups:
        node.slice.value = 'support_fraction'
    gates[0].comparators[0].value = '49/50'
    return ast.fix_missing_locations(tree)


def run(reference):
    pins = {}; inputs = json.loads(captured(reference, pins))
    require(inputs['support_refinement_schema'] == 'eoere_continuous_normal_support_refinement_inputs/v1'
            and inputs['support_fraction'] == '49/50' and inputs['hole_square_padding_mm'] == '1/1000000'
            and inputs['energy_grid_subdivisions'] == 4, 'exact declared support and energy refinement required')
    own = {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA}
    require(own in inputs['execution_sources'] and BASE in inputs['execution_sources'], 'exact refinement and preserved driver required')
    previous = json.loads(captured(inputs['previous_finite_support_result'], pins))
    previous_inputs = json.loads(captured(previous['inputs'], pins))
    for key in ('transfer_helper', 'transfer_inputs', 'existence_result', 'core_helper', 'bound_helper', 'port_reader', 'original_bounds', 'mixed_helper', 'mixed_result'):
        require(inputs[key] == previous_inputs[key], 'unchanged declared model and original-load evidence required: '+key)
    safe = private(inputs['exact_scalar_adapter'], pins)
    driver = ModuleType('_eoere_verified_refined_support_driver'); driver.__file__ = str(ROOT/BASE['path'])
    exec(compile(driver_tree(captured(BASE, pins)), driver.__file__, 'exec'), driver.__dict__)  # noqa: S102 - two verified input-control substitutions
    driver.distributed_gap = safe.adapter().producer().distributed_gap
    original_prepare = driver.prepare
    energy_records = []
    def prepare(values, live_pins):
        h = original_prepare(values, live_pins)
        h.base_relevant, h.base_disjoint = driver.relevant_coordinates, driver.disjoint
        domains = {r['id']: r for r in h.nominal['records']}
        rows = []
        for index, row in enumerate(h.trace_result['records']):
            density = F(domains[row['patch_id']]['declared_existing_stiffness_n_mm3'])
            total, count = F(0), 0
            for piece in row['pieces']:
                polynomial = {(i, j): F(v) for i, j, v in piece['gap_polynomial_ij_mm']}
                bound, cells = affine_energy_upper(polynomial, piece['outer_polygon_xy_mm'], density, values['energy_grid_subdivisions'], h)
                total += bound; count += cells
            old = F(row['exact_energy_upper_nmm']); used = min(old, total)
            rows.append(dict(row, exact_energy_upper_nmm=str(used)))
            energy_records.append({'case_id': row['case_id'], 'state_id': row['state_id'], 'patch_id': row['patch_id'],
                'exact_prior_energy_upper_nmm': str(old), 'exact_affine_majorant_energy_upper_nmm': str(total),
                'exact_used_energy_upper_nmm': str(used), 'grid_polygon_count': count})
            if index % 88 == 87:
                print(json.dumps({'case': row['case_id'], 'refined_saved_patch_states': index+1}), flush=True)
        h.trace_result = dict(h.trace_result, records=rows)
        return h
    driver.prepare = prepare
    driver.replace_rows = partial(refined_rows, padding=F(inputs['hole_square_padding_mm']))
    result = driver.run(reference)
    require(len(energy_records) == 528 and [c['binding'] for c in result['cases']] == [c['binding'] for c in previous['cases']],
            'all unchanged original cases and refined saved-pose energy states required')
    for ref in (*inputs['execution_sources'], inputs['previous_finite_support_result'], previous['inputs']):
        captured(ref, pins)
    for path, digest in tuple(pins.items()):
        captured({'path': path, 'sha256': digest}, pins)
        require(result['source_sha256'].get(path, digest) == digest, 'contradictory source pin')
        result['source_sha256'][path] = digest
    require(hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, 'executing support refinement changed')
    result.update(schema='eoere_continuous_normal_support_refinement/v1', execution_driver=own,
        previous_finite_support_result=inputs['previous_finite_support_result'], refined_saved_pose_energy_bounds=energy_records,
        continuous_normal_law_or_original_load_changed=False,
        captured_AST_delta='Only two input support-control keys and the unique support-control literal are changed; prepare and pressure-support construction are explicitly replaced.',
        support_regions_are_auxiliary_pressure_fields_not_model_energy_cells=True)
    result['shared_material_support_records'] = result.pop('shared_material_box_records')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued support-refinement evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size, 'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
