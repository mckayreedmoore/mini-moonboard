"""Recover sampled runner/leg gaps from archived native displacement fields.

These are signed small-displacement gap checks, not a contact-enabled response
or a proof that a finite sampling grid bounds every interface location.
"""
import gzip
import json
import pickle
from pathlib import Path

import numpy as np

from fea.floor_recess_mesh import shape20
from fea.floor_taper_mesh import locate
from fea.horizontal_panel_frame import panel_kernel


def displacement(structure, field, name, point):
    point = np.asarray(point, dtype=float)
    member = structure.members[name]
    if 'floor_taper_cells' in member:
        ids, weights = locate(structure, name, point)
    else:
        start, axis, u, v = (member[k] for k in ('start', 'axis', 'u', 'v'))
        local = point-start
        s = float(local@axis)
        for eid in structure.groups[name]:
            ids = structure.elements[eid][1]
            xyz = np.array([structure.nodes[n] for n in ids])
            stations = (xyz-start)@axis
            lo, hi = float(stations.min()), float(stations.max())
            if lo-1.e-6 <= s <= hi+1.e-6:
                natural = [2*float(local@u)/member['record']['width_mm'],
                           2*float(local@v)/member['record']['depth_mm'],
                           2*(s-lo)/(hi-lo)-1]
                if max(map(abs, natural)) > 1+1.e-6:
                    raise ValueError('Point lies outside runner mesh')
                weights = shape20(natural)
                if np.linalg.norm(weights@xyz-point) > 1.e-5:
                    raise ValueError('Runner interpolation does not reconstruct point')
                break
        else:
            raise ValueError('Point lies outside runner longitudinal extent')
    return weights@np.array([field[n] for n in ids])


def review_case(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    native = Path(manifest['native_directory'])
    report = json.loads(gzip.decompress((directory/'report.json.gz').read_bytes()))
    with (native/'model.pkl').open('rb') as handle:
        structure, _ = pickle.load(handle)['model']
    final = native/report['contact_cycles'][-1]['directory']
    field = panel_kernel.read_blocks((final/'frame.dat').read_text())['displacements']
    result = {}
    for side, sign in (('left', -1), ('right', 1)):
        leg, runner = 'lumber_leg_'+side, 'base_floor_'+side
        data = structure.members[leg]['record']['floor_recess_geometry']
        grain = np.array(data['grain_axis_xyz']);normal = np.array(data['normal_axis_xyz'])
        qmin, qmax = data['cross_grain_bounds_mm']
        x = data['inner_face_x_mm']+sign*data['max_recess_depth_mm']
        side_rows, top_rows = [], []
        inward = np.array([-sign, 0., 0.])
        for z in np.linspace(0., 139.7, 9):
            for q in np.linspace(qmin, qmax, 9):
                y = (q-normal[2]*z)/normal[1]
                point = np.array([x, y, z])
                opening = float((displacement(structure,field,runner,point)-
                                 displacement(structure,field,leg,point))@inward)
                side_rows.append({'point_xyz_mm': point.tolist(), 'opening_mm': opening})
        for depth_fraction in (0., .25, .5, .75, 1.):
            depth = data['max_recess_depth_mm']*depth_fraction
            s = data['taper_end_station_mm']-data['taper_run_mm']*depth_fraction
            for q in np.linspace(qmin, qmax, 9):
                leg_point = grain*s+normal*q
                leg_point[0] = data['inner_face_x_mm']+sign*depth
                runner_point = leg_point.copy(); runner_point[2] = 139.7
                gap = leg_point[2]-runner_point[2]
                delta = displacement(structure,field,leg,leg_point)-displacement(structure,field,runner,runner_point)
                top_rows.append({'leg_point_xyz_mm': leg_point.tolist(), 'runner_point_xyz_mm': runner_point.tolist(),
                    'initial_vertical_gap_mm': float(gap), 'deformed_vertical_gap_mm': float(gap+delta[2])})
        result[side] = {'minimum_side_opening_mm': min(r['opening_mm'] for r in side_rows),
            'minimum_top_gap_mm': min(r['deformed_vertical_gap_mm'] for r in top_rows),
            'side_samples': side_rows, 'top_samples': top_rows}
    return {'case': directory.name, 'native_directory': str(native), 'results': result,
        'scope': __doc__, 'qualified_for_design': False}


if __name__ == '__main__':
    results = [review_case(p) for p in sorted(Path('fea/results/clear-space-floortaper').iterdir()) if p.is_dir()]
    Path('docs/taper-contact-review.json').write_text(json.dumps(results, indent=2, allow_nan=False)+'\n')
    for row in results:
        print(row['case'], {side: {k: v for k,v in values.items() if k.startswith('minimum_')}
                            for side, values in row['results'].items()})
