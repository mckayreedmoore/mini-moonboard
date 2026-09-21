"""Independent unnotched 2x6 knee segments joined by four through bolts.

The diagonal overlap is explicitly connected; no composite action is assumed.
Existing 4x6 hosts, two upper bolts and the compact 2x6 base are preserved.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import compact_knee_frame as knee_geometry
from . import compact_knee_two_frame as previous
from . import compact_rail_frame as hardware_source

KEY = 'compact-spliced-knee-development'
THICKNESS = 38.1
UPPER_BOLT_PITCH_MM = 56.
KNEE_NAMES = tuple(f'base_knee_{side}_{end}' for side in ('left','right') for end in ('rim','leg'))
NATIVE_SQUARE_END_MEMBERS = KNEE_NAMES
MEMBER_AXES = {name:axes for name,axes in previous.MEMBER_AXES.items() if name not in knee_geometry.KNEE_NAMES}
MEMBER_AXES.update({name:(previous.knee_datums()[2],cq.Vector(1.,0.,0.)) for name in KNEE_NAMES})
EXPECTED_BEARING_LENGTHS_MM = {}
LIMITS = 'Development independent 2x6 spliced knees; provisional hardware; no construction qualification'
parameters = dict(previous.parameters,upper_bolt_pitch_mm=UPPER_BOLT_PITCH_MM,knee_type='two independent unnotched 2x6 pieces per side',splice_bolts_per_side=4)


def __getattr__(name):
    return getattr(previous,name)


def bolt_points():
    old = previous.bolt_points()
    centre = (old[0]+old[1])/2
    direction = (old[1]-old[0]).normalized()
    return tuple(centre+direction*offset for offset in (-UPPER_BOLT_PITCH_MM/2,UPPER_BOLT_PITCH_MM/2))


def splice_stations():
    length = previous.knee_datums()[3]
    return (212.,252.,length-312.,length-272.)


@cache
def raw_changed_parts():
    result = [p for p in previous.raw_changed_parts() if p.name not in knee_geometry.KNEE_NAMES]
    template = next(p for p in result if p.name == 'lumber_leg_left')
    length = previous.knee_datums()[3]
    for side,sign in (('left',-1),('right',1)):
        for end,slo,shi,piece_sign in (('rim',-110.,length-200.,sign),('leg',140.,length+110.,-sign)):
            xlo,xhi = (-THICKNESS,0.) if piece_sign < 0 else (0.,THICKNESS)
            result.append(replace(template,name=f'base_knee_{side}_{end}',
                shape=knee_geometry._prism(side,xlo,xhi,slo,shi),
                blank=(shi-slo,139.7,THICKNESS),description=LIMITS))
    return tuple(result)


@cache
def uncut_wood_parts():
    old = tuple(p for p in previous.uncut_wood_parts() if p.name not in knee_geometry.KNEE_NAMES)
    return old+tuple(p for p in raw_changed_parts() if p.name in KNEE_NAMES)


def additional_machining_cutters():
    return ()


@cache
def connections():
    result = []
    for c in previous.connections():
        if c.name.startswith('knee_bolt_'):
            continue
        if c.name.startswith('lumber_leg_bolt_'):
            point = bolt_points()[int(c.name.rsplit('_',1)[1])-1]
            c = replace(c,start=cq.Vector(c.start.x,point.y,point.z),product_status=LIMITS)
        result.append(c)
    washer = hardware_source.RAIL_WASHER_THICKNESS_MM
    for c in previous.connections():
        if c.name.startswith('knee_bolt_'):
            _,_,side,end,_ = c.name.split('_')
            interface = previous.bolt_interface_point(c)
            result.append(replace(c,start=interface-c.direction*(THICKNESS+washer),
                members=(f'base_knee_{side}_{end}',c.members[1]),grip=THICKNESS+88.9,
                product_status=LIMITS))
    rim,_,grain,_ = previous.knee_datums()
    for side,sign in (('left',-1),('right',1)):
        d = cq.Vector(-sign,0.,0.)
        for index,station in enumerate(splice_stations(),1):
            point = rim+grain*station
            start = cq.Vector(sign*previous.b.HALF,point.y,point.z)-d*(THICKNESS+washer)
            result.append(hardware_source.RailBolt(f'knee_splice_bolt_{side}_{index}',start,d,101.6,9.525,
                (f'base_knee_{side}_rim',f'base_knee_{side}_leg'),'bolt',2*THICKNESS,product_status=LIMITS))
    return tuple(result)


def bolt_dimensions(c):
    if not c.name.startswith(('knee_bolt_','knee_splice_bolt_')):
        return previous.bolt_dimensions(c)
    return {'diameter_mm':c.diameter,'length_mm':c.length,'grip_mm':c.grip,
            'hole_diameter_mm':11.1125,'washer_od_mm':25.4,'washer_thickness_mm':2.032,
            'nut_height_mm':8.5598,'thread_length_mm':25.4,'thread_start_mm':c.length-25.4,
            'provisional':True}


def bolt_interface_point(c):
    if c.name.startswith(('knee_bolt_','knee_splice_bolt_')):
        return c.start+c.direction*(THICKNESS+2.032)
    return previous.bolt_interface_point(c)


@cache
def parts():
    result = {p.name:p for p in previous.parts() if p.name not in knee_geometry.KNEE_NAMES}
    changed = set(KNEE_NAMES)|set(previous.CHANGED_HOSTS)
    result.update({p.name:p for p in uncut_wood_parts() if p.name in changed})
    for name,_,cutter in previous.service_cutters():
        if name in changed:
            result[name] = replace(result[name],shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index,name in enumerate(c.members):
            if name not in changed:
                continue
            diameter = bolt_dimensions(c)['hole_diameter_mm'] if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2,c.length+2.,c.start-c.direction,c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name],shape=shape.clean())
    return tuple(result.values())


NATIVE_RECTANGULAR_KNEES = True


def overlap_contact_datums():
    """Nine compression-only face samples per actual rectangular splice lap.

    Uniform tributary area subtracts four circular splice bores from total
    face area; it is a quadrature assumption, not an exact perforated mesh.
    Points must remain on both nominal faces and outside every modeled bore.
    """
    import math

    rim,_,grain,length = previous.knee_datums()
    across = cq.Vector(0.,grain.z,-grain.y)
    slo,shi,depth = 140.,length-200.,139.7
    hole_area = 4*math.pi*(11.1125/2)**2
    area = ((shi-slo)*depth-hole_area)/9
    if area <= 0:
        raise ValueError('Splice requires positive net contact area')
    result = []
    for side,sign in (('left',-1),('right',1)):
        members = (f'base_knee_{side}_rim',f'base_knee_{side}_leg')
        for i in range(3):
            station = slo+(i+0.5)*(shi-slo)/3
            for j in range(3):
                q = -depth/2+(j+0.5)*depth/3
                p = rim+grain*station+across*q+cq.Vector(sign*previous.b.HALF,0.,0.)
                if not (slo < station < shi and abs(q) < depth/2):
                    raise ValueError('Contact sample lies outside common raw faces')
                for c in connections():
                    if not any(member in c.members for member in members):
                        continue
                    d = c.direction.normalized()
                    delta = p-c.start
                    radius = bolt_dimensions(c)['hole_diameter_mm']/2 if c.kind == 'bolt' else c.diameter/2
                    if (delta-d*delta.dot(d)).Length <= radius:
                        raise ValueError('Contact sample lies inside a modeled bore')
                result.append({'name':f'knee_splice_contact_{side}_{i}_{j}',
                    'first':members[0],'second':members[1],
                    'point_xyz_mm':p.toTuple(),'normal_xyz':(sign,0.,0.),
                    'tributary_area_mm2':area})
    return tuple(result)
