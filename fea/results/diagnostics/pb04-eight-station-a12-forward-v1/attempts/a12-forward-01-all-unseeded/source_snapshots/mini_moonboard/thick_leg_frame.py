"""Isolated solid-4x6 single-pivot geometry for a native response trial.

Rims grow outward, legs move outward, and the single header extends 50.8 mm
at each end. The resulting header cantilevers require explicit checks. The
5/8 x 9-inch hardware is a provisional envelope: full smooth-shank coverage
is NOT established. A single axis does not establish negligible clamp friction.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq
import numpy as np

from . import no_shoes_frame as previous
from .bolted_frame import FrameBolt

KEY = 'thick-leg-centered-pivot-development'
DEPTH = 139.7
THICKNESS = 88.9
OUTWARD_EXTENSION_MM = THICKNESS-38.1
BOLT_DIAMETER_MM = 15.875
BOLT_LENGTH_MM = 228.6
HOLE_DIAMETER = 17.4625
WASHER_OD_MM = 44.45
WASHER_THICKNESS_MM = 3.175
NUT_HEIGHT_MM = 14.2875
HEX_CORNER_DIAMETER_MM = 27.5
HEAD_HEIGHT_MM = 10.31875
PIVOT_DEPTH_SHIFT_MM = 0.0
CHANGED_NAMES = ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right', 'base_header')
LIMITS = ('Unselected single-4x6 leg/rim pivot trial; outward growth and extended single header; '
          'provisional 5/8x9-inch hardware, smooth-shank coverage not demonstrated; '
          'header cantilever and complete joint qualification unresolved')
b, base = previous.b, previous.base
leg_source = previous.leg_source
timber, hardware, wide = previous.previous.timber, previous.previous.hardware, previous.wide
stations = previous.stations
electrical_parts = previous.electrical_parts
attachment_datums = previous.attachment_datums
COMPONENT_LABELS = ('shaft_envelope', 'head_washer', 'nut_washer', 'head_envelope', 'nut_envelope')


def axes():
    old = previous.bolt_points()
    centre = sum(old, cq.Vector())/len(old)
    _, foot, along, across = leg_source.geometry('2x6', 0.)
    origin = b.point(0, 0, 0)
    rim = (b.point(0, 1, 0)-origin).normalized()
    return centre, foot+previous.SHIFT, along, across, rim


def bolt_points():
    centre, _, leg, _, rim = axes()
    normals = (cq.Vector(0., leg.z, -leg.y), cq.Vector(0., rim.z, -rim.y))
    # Actual preserved stock depth planes: leg source centerline and rim N=d/2.
    leg_centre = leg_source.geometry('2x6', 0.)[0]+previous.SHIFT
    rim_centre = b.point(0., 0., DEPTH/2)
    targets = [(reference-centre).dot(normal) for reference, normal in zip(
        (leg_centre, rim_centre), normals, strict=True)]
    y, z = np.linalg.solve([[n.y, n.z] for n in normals], targets)
    return (centre+cq.Vector(0., float(y), float(z)),)


@cache
def raw_changed_parts():
    old = {p.name:p for p in previous.uncut_wood_parts()}
    result = []
    origin = b.point(0, 0, 0)
    rim = axes()[4]
    for side, sign in (('left', -1), ('right', 1)):
        part = old['base_side_'+side]
        bounds = part.shape.BoundingBox()
        x0 = bounds.xmin-OUTWARD_EXTENSION_MM if sign < 0 else bounds.xmin
        x1 = bounds.xmax if sign < 0 else bounds.xmax+OUTWARD_EXTENSION_MM
        top = max((v.Center()-origin).dot(rim) for v in part.shape.Vertices())
        shape, blank = previous.previous.base._sloped_bearing_member(x0, x1, DEPTH, top)
        result.append(replace(part, shape=shape.translate(previous.SHIFT), blank=blank, description=LIMITS))
        part = old['lumber_leg_'+side]
        bounds = part.shape.BoundingBox()
        faces = [f for f in part.shape.Faces() if all(abs(v.X-bounds.xmin) < 1e-6 for v in f.Vertices())]
        if len(faces) != 1:
            raise ValueError('Require a single raw planar leg profile')
        x0 = -b.HALF-OUTWARD_EXTENSION_MM-THICKNESS if sign < 0 else b.HALF+OUTWARD_EXTENSION_MM
        face = faces[0].translate(cq.Vector(x0-bounds.xmin, 0., 0.))
        shape = cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), cq.Vector(THICKNESS, 0., 0.))
        result.append(replace(part, shape=shape, blank=(*part.blank[:2], THICKNESS), description=LIMITS))
    header = old['base_header']
    bounds = header.shape.BoundingBox()
    shape = cq.Solid.makeBox(bounds.xlen+2*OUTWARD_EXTENSION_MM, bounds.ylen, bounds.zlen,
                            cq.Vector(bounds.xmin-OUTWARD_EXTENSION_MM, bounds.ymin, bounds.zmin))
    result.append(replace(header, shape=shape,
        blank=(header.blank[0]+2*OUTWARD_EXTENSION_MM, *header.blank[1:]), description=LIMITS))
    return tuple(result)


@dataclass(frozen=True)
class ProvisionalPivotBolt(FrameBolt):
    """Complete dimensional envelopes; no catalog or smooth-body qualification."""

    def components(self):
        d = self.direction.normalized()

        def ring(station):
            start = self.start+d*station
            return cq.Solid.makeCylinder(WASHER_OD_MM/2, WASHER_THICKNESS_MM, start, d).cut(
                cq.Solid.makeCylinder(HOLE_DIAMETER/2, WASHER_THICKNESS_MM, start, d))

        nut_start = self.start+d*(self.grip+2*WASHER_THICKNESS_MM)
        nut = cq.Solid.makeCylinder(HEX_CORNER_DIAMETER_MM/2, NUT_HEIGHT_MM, nut_start, d).cut(
            cq.Solid.makeCylinder(self.diameter/2, NUT_HEIGHT_MM, nut_start, d))
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d),
                ring(0.), ring(WASHER_THICKNESS_MM+self.grip),
                cq.Solid.makeCylinder(HEX_CORNER_DIAMETER_MM/2, HEAD_HEIGHT_MM, self.start, -d), nut)


@cache
def connections():
    result = [c for c in previous.connections() if not c.name.startswith('lumber_leg_bolt_')]
    point = bolt_points()[0]
    for side, sign in (('left', -1), ('right', 1)):
        result.append(ProvisionalPivotBolt(f'lumber_leg_bolt_{side}_1',
            cq.Vector(sign*(b.HALF+OUTWARD_EXTENSION_MM+THICKNESS+WASHER_THICKNESS_MM), point.y, point.z),
            cq.Vector(-sign, 0., 0.), BOLT_LENGTH_MM, BOLT_DIAMETER_MM,
            (f'lumber_leg_{side}', f'base_side_{side}'), 'bolt', 2*THICKNESS,
            product_status=LIMITS+'; washer/nut envelope dimensions assumed, not purchased hardware'))
    return tuple(result)


def bolt_interface_point(connection):
    return connection.start+connection.direction*(WASHER_THICKNESS_MM+THICKNESS)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, previous.previous.CountersunkPanelScrew))


def outer_base_angles():
    return tuple(p for p in previous.parts() if p.name.startswith('clip_angle_base_'))


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


@cache
def parts():
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in raw_changed_parts()})
    for record in previous.previous.bore_records():
        if record['member'] in CHANGED_NAMES:
            part = result[record['member']]
            cutter = previous.previous.wiring.bore_shape(record).translate(previous.SHIFT)
            result[part.name] = replace(part, shape=part.shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = HOLE_DIAMETER if isinstance(c, ProvisionalPivotBolt) else 11.1125 if c.kind == 'bolt' else c.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
            shape = result[name].shape.cut(cutter)
            if index == 0 and c.kind == 'screw':
                shape = shape.cut(c.components()[1])
            result[name] = replace(result[name], shape=shape.clean())
    return tuple(result.values())


def provisional_stack():
    return {'bolt_length_mm':BOLT_LENGTH_MM, 'bolt_diameter_mm':BOLT_DIAMETER_MM,
            'wood_grip_mm':2*THICKNESS, 'washer_thickness_mm':WASHER_THICKNESS_MM,
            'nut_height_mm':NUT_HEIGHT_MM,
            'nominal_tip_projection_mm':BOLT_LENGTH_MM-2*THICKNESS-2*WASHER_THICKNESS_MM-NUT_HEIGHT_MM,
            'smooth_shank_across_wood_demonstrated':False, 'catalog_selection_complete':False,
            'moment_release_is_installed_hinge':False}
