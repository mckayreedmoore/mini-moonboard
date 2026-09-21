"""Two higher three-bolt leg trials with rebuilt stock and fresh drilling.

Each triangle is regenerated using its new leg axis and the eligible bounded
layout screen: 225 uses 76/61 mm, omit 0, LN/RN=-5/+5 mm; 300 uses 66/56 mm,
omit 2, LN/RN=-15/+20 mm. Offsets reference actual stock-depth intersections.
Neither hypothetical 90 ksi screen results nor older native results qualify
these changed assemblies; hardware and resistance assumptions stay explicit.
"""
import math
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq
import numpy as np

from . import compact_thick_frame as previous
from . import compact_two_frame as baseline_two
from . import no_shoes_frame as datums

CHANGED_NAMES = baseline_two.CHANGED_NAMES
PARAMETERS = {'upper225':(225.,150.), 'upper300':(300.,225.)}
# Per-case (leg pitch, rim pitch, omitted corner, LN shift, RN shift).
LAYOUT_PARAMETERS = {'upper225':(76.,61.,0,-5.,5.), 'upper300':(66.,56.,2,-15.,20.)}
PATTERN_ALONG_LEG_MM = 76.
PATTERN_ALONG_RIM_MM = 56.
REFERENCE_SCREEN_SOURCE = 'fea/results/compact-options-study/upper150-layouts.json'
SCREEN_SOURCE = 'fea/results/compact-next-study/position-layouts.json'
LIMITS = ('Higher three-bolt physical leg trial; unchanged compact 2x6 base and '
          'three 1/2-inch bolts per leg; fresh stock/drilling; no transferred '
          'structural qualification or construction release')


def layout_offsets(leg, rim, parameters=(76.,56.,0,0.,5.)):
    """Recenter the chosen three-corner layout, then apply stock-normal offsets."""
    leg_pitch, rim_pitch, omitted, ln_shift, rn_shift = parameters
    corners = ((-1,-1),(-1,1),(1,-1),(1,1))
    points = [leg*(s*leg_pitch/2)+rim*(t*rim_pitch/2)
              for index,(s,t) in enumerate(corners) if index != omitted]
    centroid = sum(points, cq.Vector())/3
    normals = (cq.Vector(0.,leg.z,-leg.y), cq.Vector(0.,rim.z,-rim.y))
    y,z = np.linalg.solve([[n.y,n.z] for n in normals], [ln_shift,rn_shift])
    shift = cq.Vector(0.,float(y),float(z))
    return tuple(point-centroid+shift for point in points)



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
        return f'compact-three-leg-{self.label}-development'

    @property
    def MEMBER_AXES(self):
        return {name:(self.axes()[2], cq.Vector(1., 0., 0.))
                for name in ('lumber_leg_left', 'lumber_leg_right')}

    @property
    def parameters(self):
        return {'attachment_shift_s_mm':self.attachment_shift_s_mm,
                'foot_shift_y_mm':self.foot_shift_y_mm, 'label':self.label,
                'layout_parameters':list(LAYOUT_PARAMETERS[self.label])}

    def bolt_points(self):
        _, foot, leg, _, _, _, _ = self.leg_datums()
        rim = previous.axes()[4]
        normal = cq.Vector(0.,leg.z,-leg.y)
        rim_normal = cq.Vector(0.,rim.z,-rim.y)
        rim_centre = previous.b.point(0.,0.,previous.DEPTH/2)
        y,z = np.linalg.solve([[normal.y,normal.z],[rim_normal.y,rim_normal.z]],
                             [foot.dot(normal),rim_centre.dot(rim_normal)])
        centre = cq.Vector(0.,float(y),float(z))
        return tuple(centre+offset for offset in layout_offsets(leg,rim,LAYOUT_PARAMETERS[self.label]))

    def bolt_dimensions(self, c):
        return {'diameter_mm':c.diameter, 'length_mm':c.length, 'grip_mm':c.grip,
            'hole_diameter_mm':previous.HOLE_DIAMETER, 'washer_od_mm':previous.WASHER_OD_MM,
            'washer_thickness_mm':previous.WASHER_THICKNESS_MM,
            'nut_height_mm':previous.NUT_HEIGHT_MM, 'provisional':True}

    def leg_datums(self):
        anchor, foot, old_grain, old_normal = previous.leg_source.geometry('2x6', 0.)
        anchor, foot = anchor+datums.SHIFT, foot+datums.SHIFT
        foot = foot-old_grain*(foot.z/old_grain.z)
        old_group = sum(baseline_two.bolt_points(), cq.Vector())/2
        offset = (old_group-anchor).dot(old_normal)
        old_top = anchor+old_grain*previous.leg_source.TOP_EXTENSION
        top_extension = (old_top-old_group).dot(old_grain)
        centre = old_group+previous.axes()[4]*self.attachment_shift_s_mm
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

    @cache  # noqa: B019 - Only two immutable, identity-bound parameter values exist.
    def raw_changed_parts(self):
        old = {p.name:p for p in previous.uncut_wood_parts() if p.name in CHANGED_NAMES}
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

    @cache  # noqa: B019 - Only two immutable, identity-bound parameter values exist.
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

    @cache  # noqa: B019 - Only two immutable, identity-bound parameter values exist.
    def uncut_wood_parts(self):
        changed = {p.name:p for p in self.raw_changed_parts()}
        return tuple(changed.get(p.name,p) for p in previous.uncut_wood_parts())

    @cache  # noqa: B019 - Only two immutable, identity-bound parameter values exist.
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
