"""Outside floor runners seated within open inner-face rear-leg recesses.

The rails move outside the panel edges; original front posts and complete
kicker profiles remain. Leg recesses leave 50.8 mm thickness below the shoulder.
The 2 mm shoulder gap is explicit; no shoulder bearing is credited. Transverse
fit is nominal with zero clearance, pending a separate installation allowance.
This separate candidate requires its own frame and connection assessment.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_base_finish as previous
from . import compact_rail_frame as hardware_source

KEY = 'compact-floor-recess-development'
RAIL_THICKNESS_MM = 38.1
RAIL_DEPTH_MM = 139.7
RAIL_FRONT_Y = -210.
RAIL_REAR_Y = 1670.
RAIL_BOTTOM_Z = 0.
RAIL_TOP_Z = RAIL_DEPTH_MM
POST_SHIFT_MM = 0.
KICKER_CLEARANCE_MM = 2.
KNEE_NAMES = ()
NATIVE_RECTANGULAR_KNEES = False
RAIL_NAMES = tuple(f'base_floor_{side}' for side in ('left', 'right'))
NATIVE_SQUARE_END_MEMBERS = RAIL_NAMES
FLOOR_RAIL_NAMES = RAIL_NAMES
FLOOR_RAIL_GRID = (7, 2)
REMOVED_NAMES = previous.KNEE_NAMES
CHANGED_NAMES = (*RAIL_NAMES, 'base_post_outer_left', 'base_post_outer_right',
                 'lumber_leg_left', 'lumber_leg_right', 'base_side_left', 'base_side_right',
                 'kicker_left', 'kicker_right', 'base_header')
MEMBER_AXES = {name: axes for name, axes in previous.MEMBER_AXES.items()
               if name not in REMOVED_NAMES}
MEMBER_AXES.update({name: (cq.Vector(0., 1., 0.), cq.Vector(1., 0., 0.))
                    for name in RAIL_NAMES})
LIMITS = 'Isolated inner-face leg-recess candidate; altered leg sections and joints require current assessment'
parameters = dict(previous.parameters, knee_type='none; two continuous floor rails',
                  floor_rail_stock='2x6', floor_rail_bottom_mm=0.,
                  floor_rail_depth_mm=RAIL_DEPTH_MM, floor_rail_bolts_per_end=2,
                  outer_post_inward_shift_mm=POST_SHIFT_MM, leg_recess_depth_mm=38.1,
                  leg_recess_height_mm=141.7, leg_recess_shoulder_clearance_mm=2.,
                  leg_recess_transverse_clearance_mm=0.)


def __getattr__(name):
    return getattr(previous, name)


def front_points():
    return (cq.Vector(0., -134., 70.), cq.Vector(0., -103., 98.))


def rear_points():
    centre, _, grain, _, _ = previous.axes()
    centre = centre+grain*((84.-centre.z)/grain.z)
    return tuple(centre+cq.Vector(0., 15.5*sign, 14.*sign) for sign in (-1, 1))


def panel_edge_cutouts():
    return {}


LEG_RECESS_NAMES = ('lumber_leg_left', 'lumber_leg_right')
LEG_RECESS_DEPTH_MM = 38.1
NOTCH_TOP_Z_MM = RAIL_DEPTH_MM+2.
REMAINING_LEG_THICKNESS_MM = 88.9-LEG_RECESS_DEPTH_MM
RECESS_NATIVE_GEOMETRY_REQUIRED = True


def recess_cutter(side):
    """Open inner-face cut; nominal transverse fit and 2 mm shoulder clearance."""
    x0 = (-previous.b.HALF-LEG_RECESS_DEPTH_MM if side == 'left'
          else previous.b.HALF-1.)
    return cq.Solid.makeBox(LEG_RECESS_DEPTH_MM+1., RAIL_REAR_Y-RAIL_FRONT_Y,
        NOTCH_TOP_Z_MM+1., cq.Vector(x0, RAIL_FRONT_Y, -1.))


def recess_metadata():
    return {name: {'cut_from': 'inner face', 'depth_x_mm': LEG_RECESS_DEPTH_MM,
                   'cut_top_z_mm': NOTCH_TOP_Z_MM, 'runner_top_z_mm': RAIL_DEPTH_MM,
                   'remaining_leg_thickness_mm': REMAINING_LEG_THICKNESS_MM,
                   'shoulder_gap_mm': 2., 'transverse_clearance_mm': 0.,
                   'shoulder_bearing_credited': False}
            for name in LEG_RECESS_NAMES}


def floor_recess_geometry():
    """Exact full-stock side profiles and transverse bands for native meshing."""
    result = {}
    for part in uncut_wood_parts():
        if part.name not in LEG_RECESS_NAMES:
            continue
        vertices = [v.Center() for v in part.shape.Vertices()]
        xmin, xmax = min(v.x for v in vertices), max(v.x for v in vertices)
        ymin, ymax = min(v.y for v in vertices), max(v.y for v in vertices)
        zmin, zmax = min(v.z for v in vertices), max(v.z for v in vertices)
        left = part.name.endswith('left')
        cut_band = ((xmax-LEG_RECESS_DEPTH_MM, xmax) if left
                    else (xmin, xmin+LEG_RECESS_DEPTH_MM))
        retained_band = ((xmin, cut_band[0]) if left
                         else (cut_band[1], xmax))
        profile = sorted({(v.y, v.z) for v in vertices if abs(v.x-xmin) < 1.e-6})
        result[part.name] = {
            'raw_bounds_xyz_mm': ((xmin, xmax), (ymin, ymax), (zmin, zmax)),
            'side_profile_yz_mm': profile, 'cut_inner_x_band_mm': cut_band,
            'notch_top_z_mm': NOTCH_TOP_Z_MM, 'retained_x_band_mm': retained_band,
            'bottom_z_mm': 0., 'shoulder_bearing_credited': False,
            'expected_removed_volume_mm3': part.shape.intersect(recess_cutter('left' if left else 'right')).Volume(),
            'expected_retained_volume_mm3': part.shape.cut(recess_cutter('left' if left else 'right')).Volume()}

    if set(result) != set(LEG_RECESS_NAMES):
        raise ValueError('Both raw leg profiles are required for actual recess meshing')
    return result


def leg_recess_records():
    """Construction record for an inner-side recess open through the foot end."""
    return {name: {**record, **recess_metadata()[name],
                   'operation': 'Open-bottom inner-face recess; retain full opposite-face leg section.'}
            for name, record in floor_recess_geometry().items()}


@cache
def stations():
    result = []
    for name, origin, u, v, first, second in previous.stations():
        if name.startswith('clip_timber_header_outer_'):
            sign = -1 if name.endswith('left') else 1
            origin = origin+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)
        result.append((name, origin, u, v, first, second))
    return tuple(result)


@cache
def raw_changed_parts():
    raw = {p.name: p for p in previous.uncut_wood_parts()}
    result = []
    for name in CHANGED_NAMES:
        side = 'left' if name.endswith('left') else 'right'
        sign = -1 if side == 'left' else 1
        if name in RAIL_NAMES:
            x0 = -previous.b.HALF-RAIL_THICKNESS_MM if sign < 0 else previous.b.HALF
            shape = cq.Solid.makeBox(RAIL_THICKNESS_MM, RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM,
                                    cq.Vector(x0, RAIL_FRONT_Y, 0.))
            result.append(previous.b.Part(name, shape,
                (RAIL_REAR_Y-RAIL_FRONT_Y, RAIL_DEPTH_MM, RAIL_THICKNESS_MM), LIMITS, 1))
            continue
        part = raw[name]
        if name.startswith('base_post_outer_'):
            part = replace(part, shape=part.shape.translate(cq.Vector(-sign*POST_SHIFT_MM, 0., 0.)))
        result.append(replace(part, description=part.description+'; '+LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {p.name: p for p in raw_changed_parts()}
    result = [changed.pop(p.name, p) for p in previous.uncut_wood_parts() if p.name not in REMOVED_NAMES]
    return tuple(result)+tuple(changed.values())


@cache
def connections():
    result = []
    for c in previous.connections():
        if c.name.startswith(('knee_', 'clip_')):
            continue
        if c.members[0].startswith('kicker_') and c.members[1].startswith('base_post_outer_'):
            sign = -1 if c.members[0].endswith('left') else 1
            c = replace(c, start=c.start+cq.Vector(-sign*POST_SHIFT_MM, 0., 0.))
        result.append(c)
    result.extend(previous.hardware.clip_connections(stations()))
    washer = hardware_source.RAIL_WASHER_THICKNESS_MM
    for side, sign in (('left', -1), ('right', 1)):
        for kind, points, first, second, first_thickness, length in (
            ('front', front_points(), f'base_post_outer_{side}', f'base_floor_{side}', 38.1, 101.6),
            ('rear', rear_points(), f'base_floor_{side}', f'lumber_leg_{side}', 38.1, 114.3)):
            inner_x = previous.b.HALF-(RAIL_THICKNESS_MM if kind == 'front' else 0.)
            grip = 76.2 if kind == 'front' else 88.9
            for index, point in enumerate(points, 1):
                result.append(hardware_source.RailBolt(f'rail_{kind}_bolt_{side}_{index}',
                    cq.Vector(sign*(inner_x-washer), point.y, point.z), cq.Vector(sign, 0., 0.),
                    length, 9.525, (first, second), 'bolt', grip, product_status=LIMITS))
    return tuple(result)


def bolt_dimensions(c):
    if not c.name.startswith('rail_'):
        return previous.bolt_dimensions(c)
    return {'diameter_mm': c.diameter, 'length_mm': c.length, 'grip_mm': c.grip,
            'hole_diameter_mm': 11.1125, 'washer_od_mm': 25.4,
            'washer_thickness_mm': 2.032, 'nut_height_mm': 8.5598,
            'thread_length_mm': 25.4, 'thread_start_mm': c.length-25.4, 'provisional': True}


def bolt_interface_point(c):
    if c.name.startswith('rail_'):
        return c.start+c.direction*(38.1+2.032)
    return previous.bolt_interface_point(c)


def panel_connections():
    return tuple(c for c in connections() if c.members[0].startswith(('main_', 'kicker_')))


def attachment_datums():
    positions = {c.name: c.start.x for c in panel_connections()}
    return tuple({**row, 'x': positions[row['name']]} for row in previous.attachment_datums())


def additional_machining_cutters():
    return tuple((f'lumber_leg_{side}', f'leg_inner_recess_{side}', 'tab_notch', recess_cutter(side))
                 for side in ('left', 'right'))


def overlap_contact_datums():
    return ()


@cache
def parts():
    result = {p.name: p for p in previous.parts() if p.name not in REMOVED_NAMES}
    result.update({p.name: p for p in raw_changed_parts()})
    result.update({p.name: p for p in previous.hardware.clip_parts(stations())})
    for name, _, _, cutter in additional_machining_cutters():
        result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for name, _, cutter in previous.service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, c.length+2., c.start-c.direction, c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())


EXPECTED_BEARING_LENGTHS_MM = {
    f'rail_rear_bolt_{side}_{index}': {f'lumber_leg_{side}': REMAINING_LEG_THICKNESS_MM}
    for side in ('left', 'right') for index in (1, 2)
}
