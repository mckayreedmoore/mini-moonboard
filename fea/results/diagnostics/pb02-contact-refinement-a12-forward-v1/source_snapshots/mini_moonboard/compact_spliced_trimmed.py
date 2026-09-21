"""Exterior end trims for the outward-bolt spliced-knee installation.

The frozen native analysis remains in compact_spliced_knee_frame. These cuts
change timber geometry and require the separate current trim assessment.
Rear-leg tops retain 18 mm normal to the rim rear face for bolt end distance;
knee tips terminate at the adjacent host's exterior depth face.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_spliced_installation as installed

KEY = installed.KEY
LEG_TOP_PROJECTION_MM = 18.
TRIMMED_NAMES = tuple(name for side in ('left', 'right') for name in
    (f'lumber_leg_{side}', f'base_knee_{side}_rim', f'base_knee_{side}_leg'))
parameters = dict(installed.parameters, leg_top_projection_normal_to_rim_mm=LEG_TOP_PROJECTION_MM,
                  knee_end_finish='flush to adjoining host exterior depth faces')


def __getattr__(name):
    return getattr(installed, name)


def _normal(grain):
    return cq.Vector(0., grain.z, -grain.y).normalized()


@cache
def trim_planes():
    """Return oriented half-spaces n.dot(point) >= offset, derived from raw hosts."""
    raw = {part.name:part for part in installed.uncut_wood_parts()}
    leg_grain, rim_grain = installed.axes()[2], installed.axes()[4]
    rim_normal, leg_normal = _normal(rim_grain), _normal(leg_grain)
    result = {}
    for side in ('left', 'right'):
        rim_rear = min(v.Center().dot(rim_normal) for v in raw[f'base_side_{side}'].shape.Vertices())
        leg_outer = max(v.Center().dot(leg_normal) for v in raw[f'lumber_leg_{side}'].shape.Vertices())
        for name, normal, offset, grain in (
            (f'lumber_leg_{side}', rim_normal, rim_rear-LEG_TOP_PROJECTION_MM, leg_grain),
            (f'base_knee_{side}_rim', rim_normal, rim_rear, installed.knee_datums()[2]),
            (f'base_knee_{side}_leg', -leg_normal, -leg_outer, installed.knee_datums()[2]),
        ):
            result[name] = {'keep_normal_xyz':normal.toTuple(), 'offset_mm':offset,
                'angle_from_square_deg':math.degrees(math.acos(min(1., abs(normal.dot(grain)))))}
    return result


def _clip(shape, plane):
    """Intersect the existing stock with a half-space; never extend an old end."""
    normal = cq.Vector(*plane['keep_normal_xyz'])
    origin = normal*plane['offset_mm']
    extent = 2.*max((v.Center()-origin).Length for v in shape.Vertices())+1.
    workplane = cq.Plane(origin=origin, xDir=(1., 0., 0.), normal=normal)
    keep = cq.Workplane(workplane).rect(2*extent, 2*extent).extrude(extent).val()
    clipped = shape.intersect(keep).clean()
    if clipped.Volume() <= 0 or len(clipped.Solids()) != 1:
        raise ValueError('Exterior trim must preserve one connected timber solid')
    return clipped


def _trim_parts(parts):
    planes = trim_planes()
    return tuple(replace(part, shape=_clip(part.shape, planes[part.name]))
                 if part.name in planes else part for part in parts)


@cache
def raw_changed_parts():
    return _trim_parts(installed.raw_changed_parts())


@cache
def uncut_wood_parts():
    return _trim_parts(installed.uncut_wood_parts())


@cache
def parts():
    return _trim_parts(installed.parts())


@cache
def trim_records():
    """Auditable raw-stock volume removal; connection axes remain delegated."""
    old = {part.name:part for part in installed.uncut_wood_parts()}
    new = {part.name:part for part in uncut_wood_parts()}
    return {name:dict(plane, original_volume_mm3=old[name].shape.Volume(),
                     retained_volume_mm3=new[name].shape.Volume(),
                     removed_volume_mm3=old[name].shape.Volume()-new[name].shape.Volume())
            for name, plane in trim_planes().items()}
