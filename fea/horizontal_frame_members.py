"""CAD-derived constant-section beam surrogates for a current frame diagnostic.

A retained prism is contained in raw timber away from the level end bevel.
This is a stiffness idealization, not a bound on member strength or frame
response. Fastener bores, local notch stresses and connection compliance need
separate treatment; this adapter deliberately consumes undrilled wood_parts.
"""
import cadquery as cq

TOL_MM = 1.e-5
LIMITS = ('Uniform retained-section stiffness surrogate; raw service cuts included; '
          'fastener holes and local stresses excluded; bevel stiffness extrapolated; '
          'neither member strength nor global response is bounded or qualified')


def axes(model, name):
    """Return right-handed grain and first section axes without inferring stock."""
    x, y, z = cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1)
    tangent = (model.b.point(0, 1, 0)-model.b.point(0, 0, 0)).normalized()
    if name.startswith(('base_side_', 'base_principal_')):
        return tangent, -x
    if name.startswith('base_rail_'):
        return x, tangent
    if name == 'base_header':
        return x, y
    if name.startswith('base_post_'):
        return z, x
    if name.startswith('lumber_leg_'):
        return model.leg.geometry('2x6', 0.)[2], x
    raise ValueError(f'Unclassified raw wood member: {name}')


def member_record(part, grain, section_u):
    """Reduce front material losses to a verified constant rectangular prism.

    Local Z is grain; local X/Y are section axes. A level bottom bevel is
    excluded only up to its highest grain-coordinate vertex. Missing material
    in that interior reduces the whole member from its low-Y face. A cut
    reaching the rear face fails explicitly instead of reverting to gross.
    """
    grain, section_u = grain.normalized(), section_u.normalized()
    if abs(grain.dot(section_u)) > 1.e-8:
        raise ValueError('Section axes must be orthogonal')
    section_v = grain.cross(section_u).normalized()
    plane = cq.Plane(origin=(0, 0, 0), xDir=section_u, normal=grain)
    local = plane.toLocalCoords(part.shape)
    bb = local.BoundingBox()
    world = part.shape.BoundingBox()
    z0, z1 = bb.zmin, bb.zmax
    bevel = abs(grain.z) > 1.e-8 and abs(grain.z) < 1-1.e-8
    if bevel:
        floor_points = [v.Center() for v in part.shape.Vertices()
                        if abs(v.Center().z-world.zmin) < TOL_MM]
        if not floor_points:
            raise ValueError(f'{part.name}: cannot identify level end bevel')
        z0 = max(p.dot(grain) for p in floor_points)
    x0, x1 = bb.xmin+TOL_MM, bb.xmax-TOL_MM
    y0, y1 = bb.ymin+TOL_MM, bb.ymax-TOL_MM
    low, high = z0+TOL_MM, z1-TOL_MM
    if min(x1-x0, y1-y0, high-low) <= 0:
        raise ValueError(f'{part.name}: empty section verification interval')

    def prism(front):
        return cq.Solid.makeBox(x1-x0, y1-front, high-low,
                                cq.Vector(x0, front, low))

    missing = prism(y0).cut(local)
    removed_volume = missing.Volume()
    if removed_volume > 1.e-3:
        y0 = missing.BoundingBox().ymax+TOL_MM
    if y0 >= y1:
        raise ValueError(f'{part.name}: no constant rear rectangle remains')
    retained = prism(y0)
    outside_volume = retained.cut(local).Volume()
    if outside_volume > 1.e-3:
        raise ValueError(f'{part.name}: retained prism is not contained in raw wood')
    center = section_u*((x0+x1)/2)+section_v*((y0+y1)/2)
    start_s = (world.zmin-center.z)/grain.z if bevel else bb.zmin
    start, end = center+grain*start_s, center+grain*bb.zmax
    width, depth = x1-x0, y1-y0
    gross_width, gross_depth = bb.xlen, bb.ylen
    return {'name': part.name, 'start': list(start.toTuple()), 'end': list(end.toTuple()),
        'axis': list(grain.toTuple()), 'section_u': list(section_u.toTuple()),
        'section_v': list(section_v.toTuple()), 'width_mm': width, 'depth_mm': depth,
        'area_mm2': width*depth, 'gross_width_mm': gross_width,
        'gross_depth_mm': gross_depth, 'retained_area_fraction': width*depth/(gross_width*gross_depth),
        'section_centroid_xyz_mm': list(center.toTuple()),
        'section_centroid_shift_v_mm': (y0+y1-bb.ymin-bb.ymax)/2,
        'verification_grain_interval_mm': [low, high],
        'bevel_extrapolation_length_mm': max(0., z0-start_s),
        'service_cut_missing_volume_mm3': removed_volume,
        'retained_prism_outside_wood_mm3': outside_volume,
        'qualified_for_design': False, 'limitations': LIMITS}


def extract(model):
    """Return every timber member; skip only explicitly named plywood panels."""
    result = []
    for part in model.wood_parts():
        if part.name.startswith(('main_', 'kicker_')):
            continue
        grain, section_u = axes(model, part.name)
        result.append(member_record(part, grain, section_u))
    if not result or len({r['name'] for r in result}) != len(result):
        raise ValueError('Require nonempty unique timber member names')
    return result
