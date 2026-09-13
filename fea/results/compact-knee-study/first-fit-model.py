"""One tab-ended solid 4x6 knee per side; conditional development geometry.

The opposite half-width end tabs contact the existing rim and leg without
cutting either host. Native gross beams omit these local tab reductions; the
explicit machining inventory is required for local section assessment.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_thick_frame as hardware_source
from . import compact_three_leg_225_refined as previous

KEY = 'compact-knee-development'
DEPTH, THICKNESS = 139.7, 88.9
TAB_WIDTH_MM = THICKNESS/2
END_EXTENSION_MM = 110.
RIM_TAB_REACH_MM, LEG_TAB_REACH_MM = 140., 160.
KNEE_BOLT_LENGTH_MM = 165.1
KNEE_NAMES = ('base_knee_left', 'base_knee_right')
NATIVE_SQUARE_END_MEMBERS = KNEE_NAMES
LIMITS = ('Development knee brace; opposite half-width end tabs; provisional '
          '1/2 x 6.5-inch Grade 5 hardware; no construction qualification')


def __getattr__(name):
    return getattr(previous, name)


def knee_datums():
    rim = previous.b.point(0., 1400., DEPTH/2)
    _, foot, grain, *_ = previous.CANDIDATE.leg_datums()
    leg = foot+grain*((1050.-foot.z)/grain.z)
    axis = (leg-rim).normalized()
    return rim, leg, axis, (leg-rim).Length


MEMBER_AXES = dict(previous.MEMBER_AXES)
MEMBER_AXES.update({name:(knee_datums()[2], cq.Vector(1.,0.,0.)) for name in KNEE_NAMES})
EXPECTED_BEARING_LENGTHS_MM = {
    f'knee_bolt_{side}_{end}':{f'base_knee_{side}':TAB_WIDTH_MM, host:THICKNESS}
    for side in ('left','right') for end,host in
    (('rim',f'base_side_{side}'),('leg',f'lumber_leg_{side}'))}
parameters = dict(previous.parameters, knee_rim_station_mm=1400., knee_leg_z_mm=1050.,
                  knee_end_extension_mm=END_EXTENSION_MM)


def _prism(side, xlo, xhi, slo, shi):
    rim, _, grain, _ = knee_datums()
    normal = cq.Vector(0.,grain.z,-grain.y)
    points = [rim+grain*s+normal*q for s,q in
              ((slo,-DEPTH/2),(shi,-DEPTH/2),(shi,DEPTH/2),(slo,DEPTH/2))]
    interface = (-1 if side == 'left' else 1)*previous.b.HALF
    plane = cq.Plane(origin=(interface+xlo,0.,0.),xDir=(0.,1.,0.),normal=(1.,0.,0.))
    return cq.Workplane(plane).polyline([(p.y,p.z) for p in points]).close().extrude(xhi-xlo).val()


@cache
def raw_changed_parts():
    result = list(previous.raw_changed_parts())
    template = next(p for p in result if p.name == 'lumber_leg_left')
    length = knee_datums()[3]
    for side in ('left','right'):
        result.append(replace(template,name=f'base_knee_{side}',
            shape=_prism(side,-TAB_WIDTH_MM,TAB_WIDTH_MM,-END_EXTENSION_MM,length+END_EXTENSION_MM),
            blank=(length+2*END_EXTENSION_MM,DEPTH,THICKNESS),description=LIMITS))
    return tuple(result)


@cache
def additional_machining_cutters():
    length = knee_datums()[3]
    result = []
    for side,sign in (('left',-1),('right',1)):
        # Rim tab is outboard; leg tab is inboard. Cut only the brace.
        for end,slo,shi,remove_sign in (
            ('rim',-END_EXTENSION_MM-1.,RIM_TAB_REACH_MM,-sign),
            ('leg',length-LEG_TAB_REACH_MM,length+END_EXTENSION_MM+1.,sign)):
            xlo,xhi = (0.,TAB_WIDTH_MM+1.) if remove_sign > 0 else (-TAB_WIDTH_MM-1.,0.)
            result.append((f'base_knee_{side}',f'knee_{side}_{end}_tab','tab_notch',
                           _prism(side,xlo,xhi,slo,shi)))
    return tuple(result)


@cache
def connections():
    result = list(previous.connections())
    rim,leg,_,_ = knee_datums()
    for side,sign in (('left',-1),('right',1)):
        interface = sign*previous.b.HALF
        for end,point,host,direction in (
            ('rim',rim,f'base_side_{side}',-sign),
            ('leg',leg,f'lumber_leg_{side}',sign)):
            d = cq.Vector(direction,0.,0.)
            start = cq.Vector(interface,point.y,point.z)-d*(TAB_WIDTH_MM+hardware_source.WASHER_THICKNESS_MM)
            result.append(hardware_source.CompactLegBolt(f'knee_bolt_{side}_{end}',start,d,
                KNEE_BOLT_LENGTH_MM,12.7,(f'base_knee_{side}',host),'bolt',TAB_WIDTH_MM+THICKNESS,
                product_status=LIMITS+'; head on 44.45 mm tab, nut on 88.9 mm host'))
    return tuple(result)


def bolt_dimensions(c):
    result = previous.bolt_dimensions(c)
    if c.name.startswith('knee_bolt_'):
        result.update(thread_length_mm=38.1, thread_start_mm=127.,
                      first_bearing_length_mm=TAB_WIDTH_MM,second_bearing_length_mm=THICKNESS)
    return result


def bolt_interface_point(c):
    if c.name.startswith('knee_bolt_'):
        return c.start+c.direction*(hardware_source.WASHER_THICKNESS_MM+TAB_WIDTH_MM)
    return previous.bolt_interface_point(c)


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    return tuple(changed.get(p.name,p) for p in previous.uncut_wood_parts())+tuple(changed[n] for n in KNEE_NAMES)


@cache
def parts():
    # Existing host machining is preserved, then the new knee bores are cut.
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in raw_changed_parts() if p.name in KNEE_NAMES})
    for member,_,_,cutter in additional_machining_cutters():
        result[member] = replace(result[member],shape=result[member].shape.cut(cutter).clean())
    for c in connections():
        if not c.name.startswith('knee_bolt_'):
            continue
        cutter = cq.Solid.makeCylinder(hardware_source.HOLE_DIAMETER/2,c.length+2.,c.start-c.direction,c.direction)
        for name in c.members:
            result[name] = replace(result[name],shape=result[name].shape.cut(cutter).clean())
    return tuple(result.values())
