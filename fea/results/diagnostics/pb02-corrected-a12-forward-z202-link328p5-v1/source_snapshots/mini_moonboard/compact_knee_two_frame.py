"""Two centered upper bolts with the preserved paired-end knee braces.

Fresh stock removes the historical three-hole upper pattern. This is a
separate development candidate; preceding numerical results do not transfer.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq
import numpy as np

from . import compact_knee_frame as previous

KEY = 'compact-knee-two-development'
UPPER_BOLT_PITCH_MM = 64.
CHANGED_HOSTS = ('base_side_left','base_side_right','lumber_leg_left','lumber_leg_right')


def __getattr__(name):
    return getattr(previous,name)


def bolt_points():
    _,foot,leg,_,rim = previous.axes()
    ln,rn = cq.Vector(0.,leg.z,-leg.y),cq.Vector(0.,rim.z,-rim.y)
    rim_point = previous.b.point(0.,0.,previous.DEPTH/2)
    y,z = np.linalg.solve([[ln.y,ln.z],[rn.y,rn.z]],
                         [foot.dot(ln),rim_point.dot(rn)])
    centre = cq.Vector(0.,float(y),float(z))
    direction = (leg+rim).normalized()
    points = tuple(centre+direction*offset for offset in (-UPPER_BOLT_PITCH_MM/2,UPPER_BOLT_PITCH_MM/2))
    for point in points:
        for normal in (ln,rn):
            margin = previous.DEPTH/2-abs((point-centre).dot(normal))-4*12.7
            if margin < 3.:
                raise ValueError('Upper bolt lacks 3 mm both-direction loaded-edge reserve')
    return points


@cache
def connections():
    result = [c for c in previous.connections() if not c.name.startswith('lumber_leg_bolt_')]
    old = {side:next(c for c in previous.connections() if c.name == f'lumber_leg_bolt_{side}_1')
           for side in ('left','right')}
    for side in ('left','right'):
        for index,point in enumerate(bolt_points(),1):
            template = old[side]
            result.append(replace(template,name=f'lumber_leg_bolt_{side}_{index}',
                start=cq.Vector(template.start.x,point.y,point.z),product_status=KEY+'; provisional hardware'))
    return tuple(result)


@cache
def parts():
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in previous.uncut_wood_parts() if p.name in CHANGED_HOSTS})
    for name,_,cutter in previous.service_cutters():
        if name in CHANGED_HOSTS:
            result[name] = replace(result[name],shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index,name in enumerate(c.members):
            if name not in CHANGED_HOSTS:
                continue
            diameter = previous.bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2,c.length+2.,c.start-c.direction,c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name],shape=shape.clean())
    return tuple(result.values())


parameters = dict(previous.parameters,upper_bolt_count_per_leg=2,
                  upper_bolt_pitch_mm=UPPER_BOLT_PITCH_MM,upper_pattern='centered grain angular bisector')
