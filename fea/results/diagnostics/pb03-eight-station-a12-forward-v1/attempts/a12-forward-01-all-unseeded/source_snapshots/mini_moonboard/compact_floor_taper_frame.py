"""Isolated outside-runner trial with a 1:12 inner-face leg runout.

A full-depth recess clears the runner before a grain-aligned taper returns to
full leg thickness. Previous square-shoulder trials and all hardware are kept
unchanged. This actual geometry requires its own mesh and resistance checks.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_floor_recess_frame as previous

KEY = 'compact-floor-taper-development'
TAPER_RUN_MM = 457.2
TAPER_RATIO = 12.
TAPER_NATIVE_GEOMETRY_REQUIRED = True
RECESS_NATIVE_GEOMETRY_REQUIRED = False
LIMITS = 'Isolated 1:12 tapered leg recess; actual geometry and resistance require assessment'
parameters = dict(previous.parameters, leg_recess_shape='1:12 grain-aligned runout',
                  leg_recess_taper_run_mm=TAPER_RUN_MM, leg_recess_taper_ratio=TAPER_RATIO)


def __getattr__(name):
    return getattr(previous, name)


def taper_stations(profile_yz, grain, clearance_top=previous.NOTCH_TOP_Z_MM):
    """Absolute grain stations; full recess clears the highest runner corner."""
    normal = cq.Vector(0., grain.z, -grain.y)
    qmin = min(cq.Vector(0., y, z).dot(normal) for y, z in profile_yz)
    start = (clearance_top-normal.z*qmin)/grain.z
    return start, start+TAPER_RUN_MM


@cache
def taper_profile_data():
    result = {}
    grain = previous.axes()[2]
    normal = cq.Vector(0., grain.z, -grain.y)
    for part in previous.uncut_wood_parts():
        if part.name not in previous.LEG_RECESS_NAMES:
            continue
        vertices = [v.Center() for v in part.shape.Vertices()]
        xmin, xmax = min(v.x for v in vertices), max(v.x for v in vertices)
        profile = sorted({(v.y, v.z) for v in vertices if abs(v.x-xmin) < 1.e-6})
        start, end = taper_stations(profile, grain)
        qmin, qmax = min(v.dot(normal) for v in vertices), max(v.dot(normal) for v in vertices)
        smin, smax = min(v.dot(grain) for v in vertices), max(v.dot(grain) for v in vertices)
        if end >= smax:
            raise ValueError('Taper must return to full stock before the leg top')
        left = part.name.endswith('left')
        inner = xmax if left else xmin
        sign = -1 if left else 1
        boundary = [(inner, smin), (inner+sign*previous.LEG_RECESS_DEPTH_MM, smin),
                    (inner+sign*previous.LEG_RECESS_DEPTH_MM, start), (inner, end)]
        result[part.name] = {
            'raw_bounds_xyz_mm': ((xmin, xmax), (min(v.y for v in vertices), max(v.y for v in vertices)),
                                  (min(v.z for v in vertices), max(v.z for v in vertices))),
            'side_profile_yz_mm': profile, 'grain_axis_xyz': grain.toTuple(),
            'normal_axis_xyz': normal.toTuple(), 'cross_grain_bounds_mm': (qmin, qmax),
            'grain_bounds_mm': (smin, smax), 'taper_start_station_mm': start,
            'taper_end_station_mm': end, 'taper_run_mm': TAPER_RUN_MM,
            'max_recess_depth_mm': previous.LEG_RECESS_DEPTH_MM, 'taper_ratio': TAPER_RATIO,
            'inner_face_x_mm': inner, 'outward_sign': sign, 'cut_profile_xs_mm': boundary,
            'cut_inner_x_band_mm': tuple(sorted((inner, inner+sign*previous.LEG_RECESS_DEPTH_MM))),
            'retained_x_band_mm': (xmin, inner-previous.LEG_RECESS_DEPTH_MM) if left
                                  else (inner+previous.LEG_RECESS_DEPTH_MM, xmax),
            'notch_top_z_mm': previous.NOTCH_TOP_Z_MM, 'bottom_z_mm': 0.,
            'shoulder_bearing_credited': False}
    if set(result) != set(previous.LEG_RECESS_NAMES):
        raise ValueError('Both full-stock leg profiles are required')
    return result


def cut_depth_at_station(station, data):
    fraction = min(1., max(0., (data['taper_end_station_mm']-station)/data['taper_run_mm']))
    return data['max_recess_depth_mm']*fraction


@cache
def recess_cutter(side):
    data = taper_profile_data()['lumber_leg_'+side]
    inner, sign = data['inner_face_x_mm'], data['outward_sign']
    start, end = data['taper_start_station_mm'], data['taper_end_station_mm']
    low = data['grain_bounds_mm'][0]-1.
    depth = data['max_recess_depth_mm']
    polygon = [(inner-sign, low), (inner+sign*depth, low),
               (inner+sign*depth, start), (inner, end), (inner-sign, end)]
    normal = cq.Vector(*data['normal_axis_xyz'])
    qmin, qmax = data['cross_grain_bounds_mm']
    plane = cq.Plane(origin=normal*(qmax+1.), xDir=(1., 0., 0.), normal=-normal)
    return cq.Workplane(plane).polyline(polygon).close().extrude(qmax-qmin+2.).val()


def additional_machining_cutters():
    return tuple((f'lumber_leg_{side}', f'leg_taper_recess_{side}', 'tab_notch', recess_cutter(side))
                 for side in ('left', 'right'))


def floor_recess_geometry():
    raw = {part.name: part for part in previous.uncut_wood_parts()}
    result = {}
    for name, data in taper_profile_data().items():
        cutter = recess_cutter('left' if name.endswith('left') else 'right')
        result[name] = {**data,
            'expected_removed_volume_mm3': raw[name].shape.intersect(cutter).Volume(),
            'expected_retained_volume_mm3': raw[name].shape.cut(cutter).Volume()}
    return result


def recess_metadata():
    return {name: {**data, 'cut_from': 'inner face', 'depth_x_mm': previous.LEG_RECESS_DEPTH_MM,
                   'cut_top_z_mm': previous.NOTCH_TOP_Z_MM, 'runner_top_z_mm': previous.RAIL_DEPTH_MM,
                   'remaining_leg_thickness_mm': previous.REMAINING_LEG_THICKNESS_MM,
                   'minimum_vertical_runner_clearance_mm': 2., 'transverse_clearance_mm': 0.,
                   'shape': 'Full-depth lower recess followed by 1:12 grain-aligned taper'}
            for name, data in taper_profile_data().items()}


def leg_recess_records():
    return {name: {**record, **recess_metadata()[name],
                   'operation': 'Open-bottom inner-face cut with continuous 1:12 runout to full stock.'}
            for name, record in floor_recess_geometry().items()}


@cache
def parts():
    result = {part.name: part for part in previous.parts()}
    changed = set(previous.LEG_RECESS_NAMES)
    result.update({part.name: part for part in previous.uncut_wood_parts() if part.name in changed})
    for name, _, _, cutter in additional_machining_cutters():
        result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean(), description=LIMITS)
    for name, _, cutter in previous.service_cutters():
        if name in changed:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for connection in previous.connections():
        for index, name in enumerate(connection.members):
            if name not in changed:
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
