"""Unbraced single-2x12 leg trial against the retained solid-4x6 outer rims.

The existing braced frame remains the selected viable candidate. This separate
trial lowers the joint and angles the leg to accommodate four half-inch bolts
without exceeding the retained weak-axis slenderness reference.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_spliced_knee_frame as previous
from .compact_thick_frame import CompactLegBolt

KEY = 'compact-2x12-leg-development'
LEG_THICKNESS_MM = 38.1
LEG_DEPTH_MM = 285.75
LEG_REAR_LEAN_DEG = 17.5
JOINT_SHIFT_ALONG_RIM_MM = -225.
BOLT_PITCH_MM = 65.
TOP_EXTENSION_MM = 150.
BOLT_LENGTH_MM = 165.1
CHANGED = ('lumber_leg_left','lumber_leg_right','base_side_left','base_side_right')
NATIVE_SQUARE_END_MEMBERS = ()
NATIVE_RECTANGULAR_KNEES = False
KNEE_NAMES = ()
LIMITS = 'Unbraced 2x12 leg trial; four half-inch bolts per leg; not the selected build package'
parameters = {'leg_stock':'single 2x12','leg_rear_lean_deg':LEG_REAR_LEAN_DEG,
    'joint_shift_along_rim_mm':JOINT_SHIFT_ALONG_RIM_MM,'bolt_pitch_mm':BOLT_PITCH_MM,
    'bolts_per_leg':4,'top_extension_mm':TOP_EXTENSION_MM,'knee_braces':False}


def __getattr__(name):
    return getattr(previous,name)


def axes():
    rim = previous.axes()[4]
    centre = sum(previous.bolt_points(),cq.Vector())/2+rim*JOINT_SHIFT_ALONG_RIM_MM
    theta = math.radians(LEG_REAR_LEAN_DEG)
    grain = cq.Vector(0.,-math.sin(theta),math.cos(theta))
    normal = cq.Vector(0.,grain.z,-grain.y)
    foot = centre-grain*(centre.z/grain.z)
    return centre,foot,grain,normal,rim


MEMBER_AXES = {name:(axes()[2],cq.Vector(1.,0.,0.)) for name in CHANGED if name.startswith('lumber_leg_')}


def bolt_points():
    centre,_,_,_,rim = axes()
    return tuple(centre+rim*s*BOLT_PITCH_MM for s in (-1.5,-.5,.5,1.5))


@cache
def raw_changed_parts():
    old = {p.name:p for p in previous.uncut_wood_parts()}
    centre,foot,grain,normal,_ = axes()
    top = centre+grain*TOP_EXTENSION_MM
    pairs = []
    for offset in (-LEG_DEPTH_MM/2,LEG_DEPTH_MM/2):
        bottom = foot+normal*offset
        bottom -= grain*(bottom.z/grain.z)
        pairs.append((bottom,top+normal*offset))
    points = [pairs[0][0],pairs[1][0],pairs[1][1],pairs[0][1]]
    length = max(p.dot(grain) for p in points)-min(p.dot(grain) for p in points)
    result = []
    for name in CHANGED:
        part = old[name]
        if name.startswith('lumber_leg_'):
            x0 = -previous.b.HALF-LEG_THICKNESS_MM if name.endswith('left') else previous.b.HALF
            plane = cq.Plane(origin=(x0,0.,0.),xDir=(0.,1.,0.),normal=(1.,0.,0.))
            shape = cq.Workplane(plane).polyline([(p.y,p.z) for p in points]).close().extrude(LEG_THICKNESS_MM).val()
            part = replace(part,shape=shape,blank=(length,LEG_DEPTH_MM,LEG_THICKNESS_MM))
        result.append(replace(part,description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    return tuple(changed.get(p.name,p) for p in previous.uncut_wood_parts() if p.name not in previous.KNEE_NAMES)


@cache
def connections():
    result = [c for c in previous.connections() if c.kind != 'bolt']
    washer = previous.bolt_dimensions(next(c for c in previous.connections() if c.name.startswith('lumber_leg_bolt_')))['washer_thickness_mm']
    for side,sign in (('left',-1),('right',1)):
        for index,point in enumerate(bolt_points(),1):
            # Head inside the 4x6 rim; nut and threaded tip outside the 2x12 leg.
            start = cq.Vector(sign*(previous.b.HALF-88.9-washer),point.y,point.z)
            result.append(CompactLegBolt(f'lumber_leg_bolt_{side}_{index}',start,cq.Vector(sign,0.,0.),
                BOLT_LENGTH_MM,12.7,(f'base_side_{side}',f'lumber_leg_{side}'),'bolt',127.,product_status=LIMITS))
    return tuple(result)


def bolt_dimensions(c):
    return {'diameter_mm':c.diameter,'length_mm':c.length,'grip_mm':c.grip,
        'hole_diameter_mm':14.2875,'washer_od_mm':34.925,'washer_thickness_mm':3.175,
        'nut_height_mm':11.5316,'thread_length_mm':38.1,'thread_start_mm':c.length-38.1,
        'provisional':True}


def bolt_interface_point(c):
    return c.start+c.direction*(88.9+3.175)


def additional_machining_cutters():
    return ()


@cache
def parts():
    result = {p.name:p for p in previous.parts() if p.name not in previous.KNEE_NAMES}
    result.update({p.name:p for p in raw_changed_parts()})
    for name,_,cutter in previous.service_cutters():
        if name in CHANGED:
            result[name] = replace(result[name],shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index,name in enumerate(c.members):
            if name not in CHANGED:
                continue
            diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            shape = result[name].shape.cut(cq.Solid.makeCylinder(diameter/2,c.length+2,c.start-c.direction,c.direction))
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name],shape=shape.clean())
    return tuple(result.values())
