"""Fresh flush-runner response with explicit unilateral bolted-face contact."""
import hashlib
import itertools
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from fea import current_coulomb_run as native
from fea.floor_flush_mesh import prepare_flush
from mini_moonboard import compact_floor_flush_frame as candidate

ORIGINAL_SOURCES = native.sources


def sources():
    result = ORIGINAL_SOURCES()
    for source in native.base.repository_source_closure([Path(__file__), Path(candidate.__file__)]):
        result[str(source.resolve().relative_to(Path.cwd()))] = hashlib.sha256(source.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = sources()


def face_contacts(module=candidate, *, stiffness_per_area=100.):
    """Triangular face quadrature; no tangential restraint or composite action.

    Each contact node carries its triangle area less a uniform bore-area
    deduction. This is a mesh-dependent contact idealization, not a resolved
    pressure field or a physical installation preload.
    """
    raw = {p.name: p for p in module.uncut_wood_parts()}
    groups = {}
    for bolt in module.connections():
        if bolt.kind == 'bolt':
            groups.setdefault(bolt.members, []).append(bolt)
    result = []
    for (first, second), bolts in groups.items():
        equations = []
        for name in (first, second):
            points = np.unique([[v.Center().y, v.Center().z] for v in raw[name].shape.Vertices()], axis=0)
            equations.extend(ConvexHull(points).equations)
        a = np.array(equations)[:, :2]; c = np.array(equations)[:, 2]
        vertices = []
        for i, j in itertools.combinations(range(len(a)), 2):
            if abs(np.linalg.det(a[[i, j]])) < 1.e-10:
                continue
            point = np.linalg.solve(a[[i, j]], -c[[i, j]])
            if np.max(a@point+c) <= 1.e-6 and not any(np.linalg.norm(point-p) < 1.e-5 for p in vertices):
                vertices.append(point)
        if len(vertices) < 3:
            raise ValueError('No positive bolted-face overlap')
        polygon = np.array(vertices)[ConvexHull(vertices).vertices]
        centre = polygon.mean(axis=0)
        area = ConvexHull(polygon).volume
        holes = sum(np.pi*(module.bolt_dimensions(b)['hole_diameter_mm']/2)**2 for b in bolts)
        factor = (area-holes)/area
        if factor <= 0:
            raise ValueError('Bores exhaust contact face')
        interface = module.bolt_interface_point(bolts[0]).x
        first_centre_x = raw[first].shape.Center().x
        normal = (1. if first_centre_x > interface else -1., 0., 0.)
        # Three interior quadrature points per fan triangle distribute support
        # while avoiding a single centroid coincident with a bolt axis.
        for index in range(len(polygon)):
            triangle = np.array([centre, polygon[index], polygon[(index+1) % len(polygon)]])
            edges = triangle[1:]-triangle[0]
            cell_area = abs(np.linalg.det(edges))/2*factor/3
            for sample, weights in enumerate(((2/3, 1/6, 1/6), (1/6, 2/3, 1/6), (1/6, 1/6, 2/3))):
                yz = np.array(weights)@triangle
                if any(np.linalg.norm(yz-np.array([b.start.y, b.start.z])) <= module.bolt_dimensions(b)['hole_diameter_mm']/2 for b in bolts):
                    raise ValueError('Contact quadrature lies inside bolt bore; revise quadrature')
                result.append({'name': f'flush_face_{first}_{second}_{index}_{sample}',
                    'first': first, 'second': second, 'point_xyz_mm': [interface, *yz.tolist()],
                    'normal_xyz': normal, 'tributary_area_mm2': cell_area,
                    'stiffness_n_per_mm': stiffness_per_area*cell_area})
    return result


def taper_top_monitors(module=candidate):
    result = []
    for side, sign in (('left', -1), ('right', 1)):
        data = module.floor_recess_geometry()['lumber_leg_'+side]
        grain = np.array(data['grain_axis_xyz']); normal = np.array(data['normal_axis_xyz'])
        for i, fraction in enumerate((.5, .75, 1.)):
            station = data['taper_end_station_mm']-data['taper_run_mm']*fraction
            for j, q in enumerate(np.linspace(*data['cross_grain_bounds_mm'], 3)):
                leg = grain*station+normal*q
                leg[0] = data['inner_face_x_mm']+sign*data['max_recess_depth_mm']*fraction
                runner = leg.copy(); runner[2] = module.RAIL_DEPTH_MM
                result.append({'name': f'flush_taper_top_{side}_{i}_{j}',
                    'first': 'base_floor_'+side, 'second': 'lumber_leg_'+side,
                    'first_point': runner.tolist(), 'second_point': leg.tolist(), 'normal': [0., 0., 1.]})
    return result


def run(output, *, module=candidate, **kwargs):
    if module.KEY != candidate.KEY:
        raise ValueError('Flush producer requires the exact flush candidate')
    if ORIGINAL_SOURCES() != native.LOADED_SOURCES or sources() != LOADED_SOURCES:
        raise ValueError('Restart flush runner after source changes')
    if 'member_contacts' in kwargs or 'clearance_monitors' in kwargs:
        raise ValueError('Flush face contacts cannot be silently overridden')
    contacts = face_contacts(module)
    old = native.prepare, native.prepare_recess, native.sources, native.LOADED_SOURCES
    try:
        native.prepare = prepare_flush; native.prepare_recess = prepare_flush
        native.sources = sources; native.LOADED_SOURCES = LOADED_SOURCES
        return native.run(output, module=module, member_contacts=contacts,
                          clearance_monitors=taper_top_monitors(module), **kwargs)
    finally:
        native.prepare, native.prepare_recess, native.sources, native.LOADED_SOURCES = old
