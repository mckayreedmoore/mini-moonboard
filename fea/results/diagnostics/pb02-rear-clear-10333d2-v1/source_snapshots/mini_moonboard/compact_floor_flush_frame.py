"""Fresh-stock flush ends for the tapered, outside floor-runner candidate.

Front runner ends align with the outer-post end plane. Rear runner ends follow
actual inclined rear-leg depth faces. The lower rim ends lose the former 7 mm
reserve to align with the post/header plane. This changed geometry requires
its own assessment; the preserved taper candidate's passing cases do not transfer.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_floor_taper_frame as previous
from .compact_spliced_trimmed import _clip

KEY = 'compact-floor-flush-development'
FLUSH_NATIVE_GEOMETRY_REQUIRED = True
NATIVE_SQUARE_END_MEMBERS = ()
REAR_OVERHANG_MM = 0.
INCLINED_TRIM_Y = previous.HEADER_BACK_Y
RAIL_FRONT_Y = previous.HEADER_BACK_Y
TRIMMED_NAMES = (*previous.RAIL_NAMES, 'base_side_left', 'base_side_right',
                 'lumber_leg_left', 'lumber_leg_right')
CHANGED_NAMES = (*TRIMMED_NAMES, 'base_post_outer_left', 'base_post_outer_right')
MOVED_BASE_CLIPS = frozenset(('clip_split_base_center_left', 'clip_split_base_center_right'))
REDRILL_AFTER_BASE_CLIPS = frozenset(
    ('base_header', 'base_principal_center_left', 'base_principal_center_right'))
# Historical split-center station was Y = -135 mm, which hung the front SDS off
# the header. Sit half an ML24Z pitch (19.05 mm) toward the kicker from the
# underside header clips so all three header holes stay in the 2x6 and do not
# line up with the screws coming from below.
HEADER_MID_Y_MM = previous.HEADER_BACK_Y + previous.HEADER_DEPTH / 2
BASE_CENTER_CLIP_Y_MM = HEADER_MID_Y_MM - 19.05
LEG_TOP_PROJECTION_MM = 0.
UPPER_BOLT_PITCH_MM = 56.
UPPER_BOLT_CENTRE_YZ_MM = (1134.25, 1761.5)
LIMITS = ('Fresh-stock flush tapered-runner revision; trimmed runner and lower rim ends; '
          'current geometry, resistance and installation checks required')
parameters = dict(previous.parameters, floor_runner_end_finish='post-plane front; inclined leg-plane rear',
                  rear_inclined_member_overhang_mm=REAR_OVERHANG_MM,
                  floor_runner_front_y_mm=RAIL_FRONT_Y,
                  flush_native_geometry_required=True, leg_top_projection_normal_to_rim_mm=0.,
                  upper_joint_revision='flush-top-relocated-56mm',
                  upper_bolt_centre_yz_mm=UPPER_BOLT_CENTRE_YZ_MM,
                  runner_joint_revision='flush-ends-relocated-front-and-rear-pairs',
                  base_center_clip_y_mm=BASE_CENTER_CLIP_Y_MM)


def __getattr__(name):
    return getattr(previous, name)


def bolt_points():
    centre = cq.Vector(0., *UPPER_BOLT_CENTRE_YZ_MM)
    direction = cq.Vector(0., 18., 53.).normalized()
    return tuple(centre+direction*offset for offset in (-28., 28.))


def front_points():
    centre = cq.Vector(0., -91.5625, 84.1375)
    direction = cq.Vector(0., 1., 1.).normalized()
    return tuple(centre+direction*offset for offset in (-19.75, 19.75))


def rear_points():
    return (cq.Vector(0., 1551., 69.), cq.Vector(0., 1517., 97.5))


@cache
def stations():
    return tuple(
        (name, cq.Vector(origin.x, BASE_CENTER_CLIP_Y_MM, origin.z), *rest)
        if name in MOVED_BASE_CLIPS else (name, origin, *rest)
        for name, origin, *rest in previous.stations())


@cache
def connections():
    moved = {c.name: c for c in previous.hardware.clip_connections(
        tuple(station for station in stations() if station[0] in MOVED_BASE_CLIPS))}
    result = []
    for c in previous.connections():
        c = moved.get(c.name, c)
        points = (bolt_points() if c.name.startswith('lumber_leg_bolt_') else
                  front_points() if c.name.startswith('rail_front_bolt_') else
                  rear_points() if c.name.startswith('rail_rear_bolt_') else None)
        if points is not None:
            point = points[int(c.name.rsplit('_', 1)[1])-1]
            c = replace(c, start=cq.Vector(c.start.x, point.y, point.z), product_status=LIMITS)
        result.append(c)
    return tuple(result)


def bolt_interface_point(connection):
    point = previous.bolt_interface_point(connection)
    if connection.name.startswith('lumber_leg_bolt_'):
        return cq.Vector(point.x, connection.start.y, connection.start.z)
    return point


@cache
def runner_end_geometry():
    """Reference the actual timber faces, including the rear leg's inclination."""
    raw = {p.name: p for p in previous.uncut_wood_parts()}
    grain = previous.axes()[2]
    normal = cq.Vector(0., grain.z, -grain.y)
    result = {}
    for side in ('left', 'right'):
        post = raw['base_post_outer_'+side].shape.BoundingBox()
        leg = raw['lumber_leg_'+side].shape
        rear_plane = max(v.Center().dot(normal) for v in leg.Vertices())
        rear_bottom = rear_plane/normal.y
        rear_top = (rear_plane-normal.z*previous.RAIL_DEPTH_MM)/normal.y
        result['base_floor_'+side] = {
            'front_y_mm': post.ymin,
            'rear_bottom_y_mm': rear_bottom,
            'rear_top_y_mm': rear_top,
            'rear_plane_normal_xyz': normal.toTuple(),
            'rear_plane_offset_mm': rear_plane,
            'profile_yz_mm': [(post.ymin, 0.), (rear_bottom, 0.),
                              (rear_top, previous.RAIL_DEPTH_MM),
                              (post.ymin, previous.RAIL_DEPTH_MM)],
            'original_front_y_mm': previous.RAIL_FRONT_Y,
            'original_rear_y_mm': previous.RAIL_REAR_Y,
            'front_trim_mm': post.ymin-previous.RAIL_FRONT_Y,
            'rear_bottom_trim_mm': previous.RAIL_REAR_Y-rear_bottom,
            'rear_top_trim_mm': previous.RAIL_REAR_Y-rear_top,
            'fresh_native_assessment_required': True,
        }
    return result


@cache
def raw_changed_parts():
    result = []
    for part in previous.uncut_wood_parts():
        if part.name not in CHANGED_NAMES:
            continue
        bounds = part.shape.BoundingBox()
        if part.name in previous.RAIL_NAMES:
            data = runner_end_geometry()[part.name]
            plane = cq.Plane(origin=(bounds.xmin, 0., 0.), xDir=(0., 1., 0.), normal=(1., 0., 0.))
            shape = cq.Workplane(plane).polyline(data['profile_yz_mm']).close().extrude(bounds.xlen).val()
            blank = (data['rear_bottom_y_mm']-data['front_y_mm'], *part.blank[1:])
        elif part.name.startswith('lumber_leg_'):
            rim = next(p for p in previous.uncut_wood_parts()
                       if p.name == part.name.replace('lumber_leg_', 'base_side_'))
            grain = previous.axes()[4]
            normal = cq.Vector(0., grain.z, -grain.y).normalized()
            offset = min(v.Center().dot(normal) for v in rim.shape.Vertices())
            shape = _clip(part.shape, {'keep_normal_xyz': normal.toTuple(), 'offset_mm': offset})
            blank = part.blank
        elif part.name.startswith('base_post_'):
            shape, blank = part.shape, part.blank
        else:
            cutter = cq.Solid.makeBox(bounds.xlen+2., INCLINED_TRIM_Y-bounds.ymin+1., bounds.zlen+2.,
                cq.Vector(bounds.xmin-1., bounds.ymin-1., bounds.zmin-1.))
            shape = part.shape.cut(cutter).clean()
            blank = part.blank
        result.append(replace(part, shape=shape, blank=blank, description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {p.name: p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


@cache
def parts():
    # Rebuild changed receivers from fresh profiles; inherited axes drill once.
    result = {p.name: p for p in previous.parts()}
    result.update({p.name: p for p in raw_changed_parts()})
    for part in previous.hardware.clip_parts(
            tuple(station for station in stations() if station[0] in MOVED_BASE_CLIPS)):
        result[part.name] = part
    result.update({p.name: p for p in uncut_wood_parts() if p.name in REDRILL_AFTER_BASE_CLIPS})
    recut = CHANGED_NAMES + tuple(REDRILL_AFTER_BASE_CLIPS)
    for name, _, _, cutter in previous.additional_machining_cutters():
        if name in recut:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for name, _, cutter in previous.service_cutters():
        if name in recut:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in recut:
                continue
            diameter = (previous.bolt_dimensions(connection)['hole_diameter_mm']
                        if connection.kind == 'bolt' else connection.diameter)
            cutter = cq.Solid.makeCylinder(diameter/2, connection.length+2.,
                connection.start-connection.direction, connection.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())


@cache
def floor_recess_geometry():
    """Retain taper dimensions but report the newly trimmed actual leg profiles."""
    raw = {p.name: p for p in uncut_wood_parts()}
    result = {}
    for name, old in previous.floor_recess_geometry().items():
        part = raw[name]
        vertices = [v.Center() for v in part.shape.Vertices()]
        bounds = part.shape.BoundingBox()
        grain = cq.Vector(*old['grain_axis_xyz'])
        cutter = previous.recess_cutter('left' if name.endswith('left') else 'right')
        result[name] = {**old,
            'side_profile_yz_mm': sorted({(v.y, v.z) for v in vertices if abs(v.x-bounds.xmin) < 1.e-6}),
            'raw_bounds_xyz_mm': ((bounds.xmin, bounds.xmax), (bounds.ymin, bounds.ymax), (bounds.zmin, bounds.zmax)),
            'grain_bounds_mm': (min(v.dot(grain) for v in vertices), max(v.dot(grain) for v in vertices)),
            'expected_removed_volume_mm3': part.shape.intersect(cutter).Volume(),
            'expected_retained_volume_mm3': part.shape.cut(cutter).Volume()}
    return result


def leg_recess_records():
    return {name: {**old, **floor_recess_geometry()[name],
                   'leg_top_projection_normal_to_rim_mm': 0.}
            for name, old in previous.leg_recess_records().items()}
