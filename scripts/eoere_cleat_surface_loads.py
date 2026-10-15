"""Continuous current-cleat load hypotheses on authenticated finished surfaces.

This replaces neither the frozen cloud results nor the connected-frame law.
It defines a reproducible local load functional before another elastic study.
No stiffness, resistance, response solve or physical observation is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
MEMBERS = ('eoere_cleat_left', 'eoere_cleat_right')
ANGLES = (30, 60, 90)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def vector(value):
    result = np.asarray(value, dtype=float)
    require(result.shape == (3,) and np.isfinite(result).all(), 'finite three-vector required')
    return result


def captured(reference, pins):
    path = (ROOT / reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'], 'source changed: ' + reference['path'])
    require(pins.get(reference['path'], digest) == digest, 'contradictory source pin')
    pins[reference['path']] = digest
    return data


def read(reference, pins):
    return json.loads(captured(reference, pins))


def arc_integral(degrees):
    """Integral cos(pi*phi/(2*beta))*cos(phi) over [-beta,beta]."""
    require(degrees in ANGLES, 'declared contact half-angle required')
    beta = math.radians(degrees)
    a = math.pi / (2 * beta)
    return math.pi / 2 if degrees == 90 else 2 * a * math.cos(beta) / (a*a - 1)


def bore_band(action, geometry, bore):
    frame = np.asarray(geometry['frame'])
    local = frame @ (vector(action['point_mm']) - vector(geometry['start']))
    force = frame @ vector(action['force_n'])
    center = vector(bore['origin'])
    require(max(abs(local[[0, 2]] - center[[0, 2]])) < 1e-8
            and abs(force[1]) < 1e-10, 'centerline lateral bore force required')
    low, high = bore['interval_mm']
    radius = float(bore['radius_mm'])
    half = min(local[1] - low, high - local[1])
    require(radius > 0 and half > 1e-8, 'interior band and positive bore radius required')
    magnitude = float(np.linalg.norm(force))
    recovered_point = vector(geometry['start']) + frame.T @ np.array([center[0], local[1], center[2]])
    return {'kind': 'compressive_radial_bore_band', 'bore_id': bore['id'],
            'radius_mm': radius, 'axial_interval_mm': [float(local[1]-half), float(local[1]+half)],
            'axial_centroid_mm': float(local[1]), 'local_force_n': force.tolist(),
            'recovered_force_n': vector(action['force_n']).tolist(),
            'recovered_point_mm': recovered_point.tolist(),
            'peak_pressure_mpa_by_half_angle': {
                str(angle): magnitude / (radius * 2 * half * arc_integral(angle)) for angle in ANGLES}}


def bore_traction(band, phi, axial, degrees):
    """Local traction on wood, at angle phi from its lateral force direction.

    Integrate on r*dphi*du. The bore's wood-outward normal is minus the radial
    direction, so the returned traction is compressive and has no friction.
    """
    beta = math.radians(degrees)
    require(degrees in ANGLES and np.isfinite([phi, axial]).all(), 'finite declared surface point required')
    low, high = band['axial_interval_mm']
    force = vector(band['local_force_n'])
    size = float(np.linalg.norm(force))
    if size == 0 or abs(phi) > beta or not low <= axial <= high:
        return np.zeros(3), np.zeros(3)
    direction = force / size
    tangent = np.cross([0., 1., 0.], direction)
    radial = math.cos(phi)*direction + math.sin(phi)*tangent
    pressure = band['peak_pressure_mpa_by_half_angle'][str(degrees)] * math.cos(math.pi*phi/(2*beta))
    return pressure * radial, radial


def annular_seat(action, geometry, bore, shaft):
    frame = np.asarray(geometry['frame'])
    point = frame @ (vector(action['point_mm']) - vector(geometry['start']))
    force = frame @ vector(action['force_n'])
    require(max(abs(point[[0, 2]] - np.asarray(bore['origin'])[[0, 2]])) < 1e-8
            and max(abs(force[[0, 2]])) < 1e-10, 'centered axial washer action required')
    side = 1 if point[1] > 0 else -1
    require(abs(point[1] - side*geometry['width_mm']/2) < 1e-8
            and side*force[1] <= 1e-10, 'compressive own outer-face washer action required')
    ends = [e for e in shaft['ends'] if e['host'] == geometry['body']]
    require(len(ends) == 1, 'one own wood washer end required')
    dimensions = shaft['source_axis']['hardware_scenario']
    inner, outer = dimensions['washer_id_mm']/2, dimensions['washer_od_mm']/2
    require(outer > inner >= bore['radius_mm'], 'positive annulus outside its own bore required')
    for plane in geometry['planes']:
        normal = vector(plane['normal'])
        radial_size = outer*np.linalg.norm(normal[[0, 2]])
        require(float(normal @ point) + radial_size <= plane['offset'] + 1e-8,
                'washer annulus reaches outside the finished profile')
    for other in geometry['bores']:
        if other['id'] != bore['id']:
            distance = np.linalg.norm(point[[0, 2]] - np.asarray(other['origin'])[[0, 2]])
            require(distance > outer + other['radius_mm'], 'washer annulus intersects another bore')
    area = math.pi*(outer**2-inner**2)
    center = np.array([bore['origin'][0], side*geometry['width_mm']/2, bore['origin'][2]])
    return {'kind': 'uniform_own_washer_annulus', 'bore_id': bore['id'],
            'washer_id': ends[0]['washer_id'], 'inner_radius_mm': inner, 'outer_radius_mm': outer,
            'area_mm2': area, 'pressure_mpa': abs(float(force[1]))/area,
            'recovered_force_n': vector(action['force_n']).tolist(),
            'recovered_point_mm': (vector(geometry['start'])+frame.T@center).tolist()}


def uniform_gravity(action, geometry):
    """Independent trapezoid-minus-four-cylinders volume and first moments."""
    frame = np.asarray(geometry['frame'])
    width, depth = geometry['width_mm'], geometry['depth_mm']
    top = next(p for p in geometry['planes'] if p['normal'][0] == 1.)
    a, b = top['offset'], -top['normal'][2]
    volume = width*depth*a
    moments = np.array([width*(a*a*depth/2 + b*b*depth**3/24), 0., width*b*depth**3/12])
    for bore in geometry['bores']:
        void = math.pi*bore['radius_mm']**2*width
        volume -= void
        moments -= void*vector(bore['origin'])
    require(volume > 0 and abs(volume-geometry['analytic_finished_volume_mm3']) < 1e-5,
            'complete finished volume mismatch')
    center = vector(geometry['start']) + frame.T @ (moments/volume)
    require(max(abs(center-vector(action['point_mm']))) < 1e-7,
            'uniform body load does not retain the source gravity centroid')
    return {'kind': 'uniform_finished_volume_body_force', 'volume_mm3': volume,
            'body_force_n_per_mm3': (vector(action['force_n'])/volume).tolist(),
            'recovered_force_n': vector(action['force_n']).tolist(), 'recovered_point_mm': center.tolist()}


def contact_cells(field, pins):
    """Replay frozen trimmed cells; add their implicit clipping-box definition."""
    import cadquery as cq

    from fea import wood_joint_reduced_contacts as partition
    from scripts import wood_joint_current_face_pair_atlas_attempt01 as atlas

    patches = [p for p in field['source_inputs']['timber_and_panel_shared_face_patches']
               if any(n in MEMBERS for n in (p['first'], p['second']))]
    owners = {p[k] for p in patches for k in ('first', 'second')}
    shapes = {o['id']: cq.Shape.importBrep(io.BytesIO(captured(o['source'], pins)))
              for o in field['source_inputs']['finished_body_observations'] if o['id'] in owners}
    require(len(shapes) == 9 and len(patches) == 8
            and all(s.isValid() and len(s.Solids()) == 1 for s in shapes.values()),
            'complete nine-source/eight-patch current geometry required')
    cells, definitions = {}, []
    for patch in patches:
        faces = [shapes[patch[k]].Faces()[patch['source_'+k+'_face']['face_ordinal_1_based']-1]
                 for k in ('first', 'second')]
        regions = [r for r in faces[0].intersect(faces[1]).Faces()
                   if atlas._canonical_sha256(atlas._region_geometry_data(r)) == patch['trimmed_region_signature_sha256']]
        require(len(regions) == 1, 'one exact authenticated trimmed intersection required')
        region = regions[0]
        replay = partition.area_cells(region, patch['normal_from_second_to_first_xyz'],
                                      size_mm=patch['effective_cell_size_mm'], minimum_divisions=2)
        require(len(replay) == len(patch['cells']), 'trimmed-cell census changed')
        # Extend the existing partition's output with its defining grid; do not
        # copy intersections or substitute a disk for a trimmed contact cell.
        edge = max((e for e in region.Edges() if e.geomType() == 'LINE'), key=lambda e: e.Length())
        plane = cq.Plane(origin=region.Center(), xDir=edge.endPoint()-edge.startPoint(),
                         normal=patch['normal_from_second_to_first_xyz'])
        bounds = plane.toLocalCoords(region).BoundingBox()
        nx, ny = (max(2, math.ceil(span/patch['effective_cell_size_mm'])) for span in (bounds.xlen, bounds.ylen))
        xs, ys = np.linspace(bounds.xmin, bounds.xmax, nx+1), np.linspace(bounds.ymin, bounds.ymax, ny+1)
        used, rows = set(), []
        for saved, actual in zip(patch['cells'], replay, strict=True):
            require(abs(saved['area_mm2']-actual['area_mm2']) < 1e-6
                    and max(abs(vector(saved['point_xyz_mm'])-actual['point_xyz_mm'])) < 1e-7,
                    'trimmed area or centroid changed')
            point = plane.toLocalCoords(cq.Vector(*saved['point_xyz_mm']))
            x, y = int(np.searchsorted(xs, point.x)-1), int(np.searchsorted(ys, point.y)-1)
            require(0 <= x < nx and 0 <= y < ny and (x, y) not in used
                    and xs[x]+1e-8 < point.x < xs[x+1]-1e-8
                    and ys[y]+1e-8 < point.y < ys[y+1]-1e-8, 'unambiguous interior clipping cell required')
            used.add((x, y))
            row = {'id': saved['id'], 'patch_id': patch['id'], 'area_mm2': saved['area_mm2'],
                   'centroid_xyz_mm': saved['point_xyz_mm'], 'grid_index': [x, y],
                   'clipping_box_local_xy_mm': [[float(xs[x]), float(xs[x+1])], [float(ys[y]), float(ys[y+1])]],
                   'direction_on_first_xyz': patch['normal_from_second_to_first_xyz'],
                   'first': patch['first'], 'second': patch['second']}
            cells[row['id']] = row
            rows.append(row)
        definitions.append({'id': patch['id'], 'trimmed_region_signature_sha256': patch['trimmed_region_signature_sha256'],
                            'source_first_face': patch['source_first_face']['face_id'],
                            'source_second_face': patch['source_second_face']['face_id'],
                            'plane_origin_xyz_mm': list(plane.origin.toTuple()),
                            'plane_x_xyz': list(plane.xDir.toTuple()), 'plane_y_xyz': list(plane.yDir.toTuple()),
                            'plane_normal_xyz': list(plane.zDir.toTuple()), 'grid_shape': [nx, ny], 'cells': rows})
    require(len(cells) == 60, 'all sixty current cleat contact cells required')
    return cells, definitions


def run(input_ref):
    pins = {}
    inputs = read(input_ref, pins)
    require(inputs['schema'] == 'eoere_current_cleat_continuous_load_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['actual_observations'] is None
            and inputs['bore_contact_half_angles_degrees'] == list(ANGLES), 'current declared load-hypothesis scope required')
    runtime = {k: importlib.metadata.version(k) for k in ('numpy', 'cadquery', 'cadquery-ocp')}
    require(runtime == inputs['runtime_versions'], 'declared shared numerical/geometry runtime required')
    for ref in inputs['execution_sources']:
        captured(ref, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing producer required')
    seed = read(inputs['seed'], pins)
    audit = read(inputs['seed_audit'], pins)
    require(audit['source_sha256'].get(inputs['seed']['path']) == inputs['seed']['sha256']
            and audit['all_sources_unchanged'] is True
            and audit['status'] == 'COMPLETE_DECLARED_FINER_FIXED_ACTION_FIELDS_AND_10_TO_7P5_MM_COMPARISONS',
            'completed authenticated seed audit required')
    require(seed['geometry_revision'] == inputs['geometry_revision']
            and seed['hardware_revision'] == inputs['hardware_revision']
            and seed['current_bolt_count'] == 100 and seed['current_screw_count'] == 66
            and seed['extra_grid'] is False and seed['actual_observations'] is None
            and seed['status'] == 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
            and seed['structural_acceptance'] is False, 'current unchanged authenticated seed required')
    records = seed['records']
    require(len(records) == 12 and set(seed['geometry']) == set(MEMBERS)
            and len({(r['member'], r['case_id']) for r in records}) == 12, 'two cleats and six own cases required')
    fields = {ref['path']: read(ref, pins) for ref in inputs['fields']}
    require(len(fields) == 6, 'six distinct original fields required')
    first = next(iter(fields.values()))
    cells, patches = contact_cells(first, pins)
    for field in fields.values():
        own = [p for p in field['source_inputs']['timber_and_panel_shared_face_patches']
               if any(n in MEMBERS for n in (p['first'], p['second']))]
        baseline = [p for p in first['source_inputs']['timber_and_panel_shared_face_patches']
                    if any(n in MEMBERS for n in (p['first'], p['second']))]
        require(own == baseline, 'case-specific contact geometry changed')
    output, counts = [], dict.fromkeys(('bore_bands', 'washer_seats', 'contact_cells', 'body_loads'), 0)
    errors = []
    for record in records:
        field = fields[record['field']['path']]
        require(pins[record['field']['path']] == record['field']['sha256']
                and (field['case_id'], field['state_id']) == (record['case_id'], record['state_id']), 'own current field required')
        geometry = seed['geometry'][record['member']]
        shafts = {s['axis_id']: s for s in field['source_inputs']['shafts']}
        bores = {b['id']: b for b in geometry['bores']}
        rows = []
        require(len(record['actions']) == 43 and len({a['id'] for a in record['actions']}) == 43,
                'complete distinct current cleat action inventory required')
        for action in record['actions']:
            require(np.max(abs(vector(action['free_moment_nmm']))) == 0., 'nonzero free couple needs a new surface treatment')
            if '/point/' in action['id']:
                axis, index = action['id'].rsplit('/point/', 1)
                require(axis in bores and index in ('0', '1', '2'), 'own bore/seat source required')
                if index == '2':
                    row = annular_seat(action, geometry, bores[axis], shafts[axis])
                    counts['washer_seats'] += 1
                else:
                    row = bore_band(action, geometry, bores[axis])
                    counts['bore_bands'] += 1
            elif action['id'].startswith('self-weight/'):
                require(action['id'] == 'self-weight/'+record['member'], 'own gravity required')
                row = uniform_gravity(action, geometry)
                counts['body_loads'] += 1
            else:
                cell = cells[action['id']]
                sign = 1 if cell['first'] == record['member'] else -1
                require(record['member'] in (cell['first'], cell['second']), 'own contact cell required')
                direction = sign*vector(cell['direction_on_first_xyz'])
                require(abs(np.linalg.norm(direction)-1.) < 1e-12, 'unit contact normal required')
                magnitude = float(vector(action['force_n']) @ direction)
                require(magnitude >= -1e-10 and np.max(abs(vector(action['force_n'])-magnitude*direction)) < 1e-8
                        and np.max(abs(vector(action['point_mm'])-cell['centroid_xyz_mm'])) < 1e-7,
                        'nonnegative normal own-cell resultant required')
                row = {'kind': 'uniform_trimmed_cell_pressure', 'cell_id': action['id'],
                       'pressure_mpa': max(0., magnitude)/cell['area_mm2'],
                       'recovered_force_n': (max(0., magnitude)*direction).tolist(),
                       'recovered_point_mm': cell['centroid_xyz_mm']}
                counts['contact_cells'] += 1
            original_force, recovered_force = vector(action['force_n']), vector(row['recovered_force_n'])
            error = [*abs(original_force-recovered_force),
                     *abs(np.cross(vector(action['point_mm']), original_force)-np.cross(vector(row['recovered_point_mm']), recovered_force))]
            require(max(error[:3]) < 1e-7 and max(error[3:]) < 1e-5, 'continuous load lost an original signed wrench')
            errors.append(error)
            rows.append({'source_action_id': action['id'], **row})
        resultant = sum((vector(r['recovered_force_n']) for r in rows), np.zeros(3))
        moment = sum((np.cross(vector(r['recovered_point_mm']), vector(r['recovered_force_n'])) for r in rows), np.zeros(3))
        require(max(abs(resultant)) < 1e-7 and max(abs(moment)) < 1e-5, 'complete continuous body loading is not balanced')
        output.append({k: record[k] for k in ('member', 'case_id', 'state_id', 'field')} |
                      {'actions': rows, 'whole_force_residual_n': resultant.tolist(), 'whole_moment_residual_nmm': moment.tolist()})
    require(counts == {'bore_bands': 96, 'washer_seats': 48, 'contact_cells': 360, 'body_loads': 12}, 'complete load-family census required')
    for path, digest in pins.items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, 'input changed during execution: '+path)
    return {'schema': 'eoere_current_cleat_continuous_surface_body_loads/v1', 'inputs': input_ref,
            'status': 'COMPLETE_DECLARED_CONTINUOUS_LOAD_FUNCTIONAL_NOT_JOINT_OR_RESISTANCE_QUALIFICATION',
            'source_sha256': pins, 'counts': counts, 'geometry': seed['geometry'], 'contact_patch_definitions': patches,
            'records': output, 'maximum_individual_wrench_error_n_nmm': np.max(errors, axis=0).tolist(),
            'runtime_versions': runtime,
            'new_elastic_native_or_frame_response_solve': False, 'physical_contact_law_established': False,
            'interior_stress_or_fracture_resistance_established': False, 'structural_acceptance': False,
            'actual_observations': None, 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'fresh output path required')
    data = args.inputs.read_bytes()
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'counts': result['counts']}))


if __name__ == '__main__':
    main()
