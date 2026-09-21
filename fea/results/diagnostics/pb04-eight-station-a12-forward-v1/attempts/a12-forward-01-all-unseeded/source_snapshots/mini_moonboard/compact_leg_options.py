"""Bounded physical leg-angle/attachment trials on the compact two-bolt frame.

Each immutable candidate rebuilds actual leg stock and fresh rim drilling.
Moving beam axes alone is not a geometry change. No previous resistance result
or ideal hinge behavior is transferred to a trial.
"""
import math
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import compact_two_frame as previous
from . import no_shoes_frame as datums

CHANGED_NAMES = previous.CHANGED_NAMES
PARAMETERS = {'control':(0.,0.), 'foot150':(0.,150.), 'foot300':(0.,300.),
              'lower150':(-150.,150.), 'upper150':(150.,150.)}
LIMITS = ('Physical leg-position trial; unchanged compact 2x6 base and two 3/4-inch '
          'bolts per leg; fresh stock/drilling; not selected or construction qualified')


@dataclass(frozen=True)
class Candidate:
    label: str
    attachment_shift_s_mm: float
    foot_shift_y_mm: float

    def __post_init__(self):
        if self.label not in PARAMETERS:
            raise ValueError('Require a named bounded leg-position trial')
        if (self.attachment_shift_s_mm, self.foot_shift_y_mm) != PARAMETERS[self.label]:
            raise ValueError('Candidate identity must match its exact bounded parameters')

    def __getattr__(self, name):
        return getattr(previous, name)

    @property
    def __file__(self):
        return __file__

    @property
    def KEY(self):
        return f'compact-leg-{self.label}-development'

    @property
    def MEMBER_AXES(self):
        return {name:(self.axes()[2], cq.Vector(1., 0., 0.))
                for name in ('lumber_leg_left', 'lumber_leg_right')}

    @property
    def parameters(self):
        return {'attachment_shift_s_mm':self.attachment_shift_s_mm,
                'foot_shift_y_mm':self.foot_shift_y_mm, 'label':self.label}

    def bolt_points(self):
        rim = previous.axes()[4]
        return tuple(point+rim*self.attachment_shift_s_mm for point in previous.bolt_points())

    def leg_datums(self):
        anchor, foot, old_grain, old_normal = previous.leg_source.geometry('2x6', 0.)
        anchor, foot = anchor+datums.SHIFT, foot+datums.SHIFT
        foot = foot-old_grain*(foot.z/old_grain.z)
        old_group = sum(previous.bolt_points(), cq.Vector())/2
        offset = (old_group-anchor).dot(old_normal)
        old_top = anchor+old_grain*previous.leg_source.TOP_EXTENSION
        top_extension = (old_top-old_group).dot(old_grain)
        centre = sum(self.bolt_points(), cq.Vector())/2
        foot = foot+cq.Vector(0., self.foot_shift_y_mm, 0.)
        vector = centre-foot
        length = vector.Length
        if centre.z <= 0 or length <= abs(offset):
            raise ValueError('No upward leg axis through the prescribed stock offset')
        along = vector/length
        normal = cq.Vector(0., along.z, -along.y)
        # Rotate the geometric line so the inherited signed depth offset is
        # preserved, rather than silently centering the stock on the bolts.
        grain = along*math.sqrt(1-(offset/length)**2)-normal*(offset/length)
        across = cq.Vector(0., grain.z, -grain.y)
        top = centre-across*offset+grain*top_extension
        return centre, foot, grain, across, top, offset, top_extension

    def axes(self):
        centre, foot, grain, across, *_ = self.leg_datums()
        return centre, foot, grain, across, previous.axes()[4]

    @cache  # noqa: B019 - Only five immutable, identity-bound parameter values exist.
    def raw_changed_parts(self):
        old = {p.name:p for p in previous.raw_changed_parts()}
        if self.attachment_shift_s_mm == self.foot_shift_y_mm == 0:
            return tuple(old.values())
        _, foot, grain, across, top, _, _ = self.leg_datums()
        pairs = []
        for offset in (-previous.DEPTH/2, previous.DEPTH/2):
            bottom = foot+across*offset
            bottom -= grain*(bottom.z/grain.z)
            pairs.append((bottom, top+across*offset))
        points = [pairs[0][0], pairs[1][0], pairs[1][1], pairs[0][1]]
        length = max(p.dot(grain) for p in points)-min(p.dot(grain) for p in points)
        result = []
        for name, part in old.items():
            if name.startswith('lumber_leg_'):
                x0 = -previous.b.HALF-previous.THICKNESS if name.endswith('left') else previous.b.HALF
                plane = cq.Plane(origin=(x0, 0., 0.), xDir=(0., 1., 0.), normal=(1., 0., 0.))
                shape = cq.Workplane(plane).polyline([(p.y,p.z) for p in points]).close().extrude(previous.THICKNESS).val()
                part = replace(part, shape=shape, blank=(length, previous.DEPTH, previous.THICKNESS))
            result.append(replace(part, description=part.description+'; '+LIMITS+'; '+self.KEY))
        return tuple(result)

    @cache  # noqa: B019 - Only five immutable, identity-bound parameter values exist.
    def connections(self):
        points = self.bolt_points()
        result = []
        for c in previous.connections():
            if c.name.startswith('lumber_leg_bolt_'):
                point = points[int(c.name.rsplit('_',1)[1])-1]
                c = replace(c, start=cq.Vector(c.start.x, point.y, point.z),
                            product_status=c.product_status+'; '+self.KEY)
            result.append(c)
        return tuple(result)

    @cache  # noqa: B019 - Only five immutable, identity-bound parameter values exist.
    def uncut_wood_parts(self):
        changed = {p.name:p for p in self.raw_changed_parts()}
        return tuple(changed.get(p.name,p) for p in previous.uncut_wood_parts())

    @cache  # noqa: B019 - Only five immutable, identity-bound parameter values exist.
    def parts(self):
        result = {p.name:p for p in previous.parts()}
        result.update({p.name:p for p in self.raw_changed_parts()})
        for name, _, cutter in previous.service_cutters():
            if name in CHANGED_NAMES:
                result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
        for c in self.connections():
            for index, name in enumerate(c.members):
                if name not in CHANGED_NAMES:
                    continue
                diameter = previous.HOLE_DIAMETER if c.kind == 'bolt' else c.diameter
                cutter = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
                shape = result[name].shape.cut(cutter)
                if index == 0 and c.kind == 'screw':
                    shape = shape.cut(c.components()[1])
                result[name] = replace(result[name], shape=shape.clean())
        return tuple(result.values())


OPTIONS = tuple(Candidate(label, *values) for label, values in PARAMETERS.items())


def option(label):
    return next(candidate for candidate in OPTIONS if candidate.label == label)
