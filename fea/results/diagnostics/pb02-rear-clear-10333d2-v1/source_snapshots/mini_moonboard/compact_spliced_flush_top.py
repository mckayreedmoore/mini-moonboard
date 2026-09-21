"""Flush-top adapter for selected compact spliced-knee kicker assembly.

Rear-leg tops terminate at side-rim rear faces.  Side rims retain their 7 mm
rear overhang, while upper leg bolts use the separately screened flush-layout
pair.  Changed leg and rim members are fresh stock; prior drilling is not
carried into this candidate.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_floor_flush_frame as flush_layout
from . import compact_spliced_kicker as previous

KEY = 'compact-spliced-flush-top-development'
LEG_TOP_PROJECTION_MM = 0.
UPPER_BOLT_PITCH_MM = 56.
UPPER_BOLT_CENTRE_YZ_MM = (1134.25, 1761.5)
CHANGED_NAMES = frozenset(
    f'{prefix}_{side}'
    for prefix in ('base_side', 'lumber_leg')
    for side in ('left', 'right')
)
NATIVE_SQUARE_END_MEMBERS = ()
LIMITS = ('Fresh-stock flush rear-leg tops with relocated upper bolt pairs; '
          'separate geometry and resistance checks required')
parameters = dict(
    previous.parameters,
    leg_top_projection_normal_to_rim_mm=LEG_TOP_PROJECTION_MM,
    upper_joint_revision='flush-top-relocated-56mm',
    upper_bolt_centre_yz_mm=UPPER_BOLT_CENTRE_YZ_MM,
)


def __getattr__(name):
    return getattr(previous, name)


def bolt_points():
    return flush_layout.bolt_points()


def runner_end_geometry():
    """No floor runners exist in selected spliced-knee candidate."""
    return {}


@cache
def connections():
    result = []
    for connection in previous.connections():
        if connection.name.startswith('lumber_leg_bolt_'):
            point = bolt_points()[int(connection.name.rsplit('_', 1)[1])-1]
            connection = replace(
                connection,
                start=cq.Vector(connection.start.x, point.y, point.z),
                product_status=LIMITS,
            )
        result.append(connection)
    return tuple(result)


def bolt_interface_point(connection):
    point = previous.bolt_interface_point(connection)
    if connection.name.startswith('lumber_leg_bolt_'):
        return cq.Vector(point.x, connection.start.y, connection.start.z)
    return point


def _flush_leg_parts(parts):
    source = {part.name: part for part in parts}
    rim_grain = previous.axes()[4]
    normal = cq.Vector(0., rim_grain.z, -rim_grain.y).normalized()
    result = []
    for part in parts:
        if not part.name.startswith('lumber_leg_'):
            result.append(part)
            continue
        rim = source[part.name.replace('lumber_leg_', 'base_side_')]
        offset = min(vertex.Center().dot(normal) for vertex in rim.shape.Vertices())
        shape = previous._clip(part.shape, {
            'keep_normal_xyz': normal.toTuple(),
            'offset_mm': offset,
        })
        result.append(replace(part, shape=shape, description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    return _flush_leg_parts(previous.uncut_wood_parts())


@cache
def raw_changed_parts():
    return tuple(replace(part, description=LIMITS)
                 for part in uncut_wood_parts() if part.name in CHANGED_NAMES)


@cache
def parts():
    """Drill changed legs and rims once from fresh, unbored timber shapes."""
    result = {part.name: part for part in previous.parts()}
    result.update({part.name: part for part in raw_changed_parts()})
    for name, _, cutter in previous.service_cutters():
        if name in CHANGED_NAMES:
            part = result[name]
            result[name] = replace(part, shape=part.shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = (previous.bolt_dimensions(connection)['hole_diameter_mm']
                        if connection.kind == 'bolt' else connection.diameter)
            cutter = cq.Solid.makeCylinder(
                diameter/2,
                connection.length+2.,
                connection.start-connection.direction,
                connection.direction,
            )
            shape = result[name].shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())
