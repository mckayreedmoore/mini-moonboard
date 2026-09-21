"""Separate outboard-runner candidate with full-thickness rear legs.

Single 6x6 front posts connect the retained kicker region to runners outside
full 4x6 rear legs. Header extensions support the wider posts. Bolt lengths and
thread transitions remain provisional pending catalog and delivered-lot checks.
No historical frame, taper, or connection acceptance transfers to this model.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_floor_flush_frame as previous

KEY = 'compact-floor-uncut-development'
RUNNER_OUTWARD_SHIFT_MM = 88.9
OUTER_POST_THICKNESS_MM = 139.7
FRONT_BOLT_PITCH_MM = 40.5
RECESS_NATIVE_GEOMETRY_REQUIRED = False
TAPER_NATIVE_GEOMETRY_REQUIRED = False
FLUSH_NATIVE_GEOMETRY_REQUIRED = True
LEG_RECESS_NAMES = ()
LEG_RECESS_DEPTH_MM = 0.
REMAINING_LEG_THICKNESS_MM = 88.9
CHANGED_NAMES = (*previous.CHANGED_NAMES, 'base_header')
LIMITS = ('Separate full-thickness leg and outboard-runner candidate; single 6x6 outer posts; '
          'current geometry, material, hardware, and resistance assessment required')
parameters = dict(previous.parameters, floor_runner_outward_shift_mm=RUNNER_OUTWARD_SHIFT_MM,
                  outer_post_stock='6x6', outer_post_thickness_mm=OUTER_POST_THICKNESS_MM,
                  leg_recess_shape='none; full-thickness leg', leg_recess_depth_mm=0.,
                  leg_recess_taper_run_mm=0., leg_recess_taper_ratio=None,
                  front_bolt_pitch_mm=FRONT_BOLT_PITCH_MM,
                  rim_lower_end='full horizontal bevel; partial header bearing',
                  runner_joint_revision='outboard-full-leg-with-six-by-six-front-post')


def __getattr__(name):
    return getattr(previous, name)


def front_points():
    centre = cq.Vector(0., -91.5625, 84.1375)
    direction = cq.Vector(0., 1., 1.).normalized()
    return tuple(centre+direction*offset for offset in
                 (-FRONT_BOLT_PITCH_MM/2, FRONT_BOLT_PITCH_MM/2))


@cache
def stations():
    result = []
    for name, origin, u, v, first, second in previous.stations():
        if name.startswith('clip_timber_header_outer_'):
            # Mount the upright flange against the new inward post face.
            origin += cq.Vector(12.7 if name.endswith('left') else -12.7, 0., 0.)
        result.append((name, origin, u, v, first, second))
    return tuple(result)


@cache
def raw_changed_parts():
    result = []
    for part in previous.uncut_wood_parts():
        if part.name not in CHANGED_NAMES:
            continue
        shape, blank = part.shape, part.blank
        bounds = shape.BoundingBox()
        if part.name in previous.RAIL_NAMES:
            sign = -1 if part.name.endswith('left') else 1
            shape = shape.translate(cq.Vector(sign*RUNNER_OUTWARD_SHIFT_MM, 0., 0.))
        elif part.name.startswith('base_side_'):
            # Restore only the exterior heel to form one horizontal bevel.
            # The existing header supports part of this face, not its free tail.
            grain = previous.axes()[4]
            normal = cq.Vector(0., grain.z, -grain.y)
            qmin = min(v.Center().dot(normal) for v in shape.Vertices())
            outer_y = (qmin-normal.z*bounds.zmin)/normal.y
            heel_top = max(v.Center().z for v in shape.Vertices()
                           if abs(v.Center().y-bounds.ymin) < 1.e-6)
            plane = cq.Plane(origin=(bounds.xmin, 0., 0.), xDir=(0., 1., 0.), normal=(1., 0., 0.))
            heel = cq.Workplane(plane).polyline(((outer_y, bounds.zmin),
                (bounds.ymin, bounds.zmin), (bounds.ymin, heel_top))).close().extrude(bounds.xlen).val()
            shape = shape.fuse(heel).clean()
            stations = [v.Center().dot(grain) for v in shape.Vertices()]
            blank = (max(blank[0], max(stations)-min(stations)), *blank[1:])
        elif part.name.startswith('base_post_outer_'):
            xmin = (-previous.b.HALF-RUNNER_OUTWARD_SHIFT_MM if part.name.endswith('left')
                    else previous.b.HALF+RUNNER_OUTWARD_SHIFT_MM-OUTER_POST_THICKNESS_MM)
            shape = cq.Solid.makeBox(OUTER_POST_THICKNESS_MM, bounds.ylen, bounds.zlen,
                                    cq.Vector(xmin, bounds.ymin, bounds.zmin))
            blank = (bounds.zlen, bounds.ylen, OUTER_POST_THICKNESS_MM)
        elif part.name == 'base_header':
            shape = cq.Solid.makeBox(bounds.xlen+2*RUNNER_OUTWARD_SHIFT_MM, bounds.ylen, bounds.zlen,
                                    cq.Vector(bounds.xmin-RUNNER_OUTWARD_SHIFT_MM, bounds.ymin, bounds.zmin))
            blank = (bounds.xlen+2*RUNNER_OUTWARD_SHIFT_MM, *part.blank[1:])
        result.append(replace(part, shape=shape, blank=blank, description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {part.name: part for part in raw_changed_parts()}
    return tuple(changed.get(part.name, part) for part in previous.uncut_wood_parts())


@cache
def connections():
    result = []
    for connection in previous.connections():
        if connection.name.startswith('clip_'):
            continue
        if connection.name.startswith('rail_'):
            front = connection.name.startswith('rail_front_')
            side = 'left' if '_left_' in connection.name else 'right'
            sign = -1 if side == 'left' else 1
            first_thickness = OUTER_POST_THICKNESS_MM if front else REMAINING_LEG_THICKNESS_MM
            inner_x = previous.b.HALF+RUNNER_OUTWARD_SHIFT_MM-first_thickness
            point = (front_points()[int(connection.name.rsplit('_', 1)[1])-1]
                     if front else connection.start)
            connection = replace(connection,
                start=cq.Vector(sign*(inner_x-2.032), point.y, point.z),
                direction=cq.Vector(sign, 0., 0.),
                members=(f'base_post_outer_{side}' if front else f'lumber_leg_{side}',
                         f'base_floor_{side}'),
                grip=first_thickness+previous.RAIL_THICKNESS_MM,
                length=203.2 if front else 152.4, product_status=LIMITS)
        result.append(connection)
    result.extend(previous.hardware.clip_connections(stations()))
    return tuple(result)


def bolt_dimensions(connection):
    result = previous.bolt_dimensions(connection)
    if connection.name.startswith('rail_'):
        # ASME minimum-thread geometry is a CAD assumption, never a guarantee
        # that delivered thread runout clears the required wood bearing zone.
        thread = 31.75 if connection.length > 152.4 else 25.4
        result = dict(result, thread_length_mm=thread,
                      thread_start_mm=connection.length-thread, provisional=True)
    return result


def bolt_interface_point(connection):
    if connection.name.startswith('rail_'):
        first = OUTER_POST_THICKNESS_MM if connection.name.startswith('rail_front_') else REMAINING_LEG_THICKNESS_MM
        return connection.start+connection.direction*(first+2.032)
    return previous.bolt_interface_point(connection)


def additional_machining_cutters():
    return ()


def floor_recess_geometry():
    return {}


def recess_metadata():
    return {}


def leg_recess_records():
    return {}


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


@cache
def parts():
    result = {part.name: part for part in previous.parts()}
    result.update({part.name: part for part in raw_changed_parts()})
    result.update({part.name: part for part in previous.hardware.clip_parts(stations())})
    for name, _, cutter in previous.service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = bolt_dimensions(connection)['hole_diameter_mm'] if connection.kind == 'bolt' else connection.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, connection.length+2.,
                                          connection.start-connection.direction, connection.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())


EXPECTED_BEARING_LENGTHS_MM = {
    f'rail_{kind}_bolt_{side}_{index}': {
        (f'base_post_outer_{side}' if kind == 'front' else f'lumber_leg_{side}'):
            OUTER_POST_THICKNESS_MM if kind == 'front' else REMAINING_LEG_THICKNESS_MM,
        f'base_floor_{side}': previous.RAIL_THICKNESS_MM}
    for kind in ('front', 'rear') for side in ('left', 'right') for index in (1, 2)
}
