"""Compact flush-rim development frame with three bolts per solid 4x6 leg.

The 2x6 header/posts retain 7 mm of inclined-member rear overhang to limit
end-cut depth. Actual partial bearing and remaining end section need checks.
Raw timber, receiver drilling and commercial angle stations are rebuilt.
Historical pivot results do not qualify this changed multi-bolt load path.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq
import numpy as np

from . import no_shoes_frame as previous
from . import thick_leg_frame as pivot_reference
from .bolted_frame import FrameBolt

KEY = 'compact-thick-development'
DEPTH = 139.7
THICKNESS = 88.9
INWARD_CHANGE_MM = THICKNESS-38.1
HEADER_DEPTH = 139.7
HEADER_BACK_Y = previous.base.HEADER_FRONT_Y-HEADER_DEPTH
REAR_OVERHANG_MM = 7.0
INCLINED_TRIM_Y = HEADER_BACK_Y-REAR_OVERHANG_MM
BOLT_COUNT_PER_LEG = 3
BOLT_DIAMETER_MM = 12.7
BOLT_LENGTH_MM = 203.2
HOLE_DIAMETER = 14.2875
WASHER_OD_MM = 34.925
WASHER_THICKNESS_MM = 3.175
NUT_HEIGHT_MM = 11.5316
HEX_CORNER_DIAMETER_MM = 21.9964
HEAD_HEIGHT_MM = 8.2042
PATTERN_ALONG_LEG_MM = 76.0
PATTERN_ALONG_RIM_MM = 64.0
CHANGED_NAMES = ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right',
    'base_header', 'base_post_outer_left', 'base_post_outer_right', 'base_post_center_left', 'base_post_center_right',
    'base_principal_center_left', 'base_principal_center_right', 'base_rail_top',
    'base_rail_bottom_left', 'base_rail_bottom_right', 'base_rail_service_lower_left',
    'base_rail_service_lower_right', 'base_rail_service_upper_left', 'base_rail_service_upper_right')
LIMITS = ('Preferred compact 4x6 development geometry; three bolts per leg; flush outer rims; '
          'shortened rails, 2x6 header/posts and small rear end trims; '
          'hardware, changed frame response and build qualification remain unresolved')
b = previous.b
base = replace(previous.base, INNER_EDGE=b.HALF-THICKNESS)
leg_source = previous.leg_source
timber, hardware, wide = previous.previous.timber, previous.previous.hardware, previous.wide
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
    _, _, leg, _, rim = axes()
    centre = pivot_reference.bolt_points()[0]
    normals = (cq.Vector(0., leg.z, -leg.y), cq.Vector(0., rim.z, -rim.y))
    y, z = np.linalg.solve([[n.y, n.z] for n in normals], [-5., 5.])
    points = [leg*(a*PATTERN_ALONG_LEG_MM/2)+rim*(t*PATTERN_ALONG_RIM_MM/2)
              for a,t in ((1,-1), (-1,1), (1,1))]
    centroid = sum(points, cq.Vector())/len(points)
    return tuple(centre+cq.Vector(0., float(y), float(z))+point-centroid for point in points)


@cache
def stations():
    result = []
    for name, origin, u, v, first, second in previous.stations():
        if first.startswith('base_side_') or second.startswith('base_side_'):
            sign = -1 if origin.x < 0 else 1
            origin = origin+cq.Vector(-sign*INWARD_CHANGE_MM, 0., 0.)
        if name.startswith('clip_split_header_center_'):
            origin = origin+cq.Vector(0., (234.95-HEADER_DEPTH)/2, 0.)
        result.append((name, origin, u, v, first, second))
    return tuple(result)


@cache
def raw_changed_parts():
    old = {p.name:p for p in previous.uncut_wood_parts()}
    result = []
    origin, rim = b.point(0, 0, 0), axes()[4]
    for name in CHANGED_NAMES:
        part = old[name]
        bounds = part.shape.BoundingBox()
        shape, blank = part.shape, part.blank
        if name.startswith('base_side_'):
            sign = -1 if name.endswith('left') else 1
            x0 = -b.HALF if sign < 0 else b.HALF-THICKNESS
            top = max((v.Center()-origin).dot(rim) for v in shape.Vertices())
            shape, blank = previous.previous.base._sloped_bearing_member(x0, x0+THICKNESS, DEPTH, top)
            shape = shape.translate(previous.SHIFT)
        elif name.startswith('lumber_leg_'):
            faces = [f for f in shape.Faces() if all(abs(v.X-bounds.xmin) < 1e-6 for v in f.Vertices())]
            if len(faces) != 1:
                raise ValueError('Require single planar raw leg profile')
            x0 = -b.HALF-THICKNESS if name.endswith('left') else b.HALF
            face = faces[0].translate(cq.Vector(x0-bounds.xmin, 0., 0.))
            shape = cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), cq.Vector(THICKNESS, 0., 0.))
            blank = (*blank[:2], THICKNESS)
        elif name == 'base_header' or name.startswith('base_post_'):
            shape = cq.Solid.makeBox(bounds.xlen, HEADER_DEPTH, bounds.zlen,
                cq.Vector(bounds.xmin, HEADER_BACK_Y, bounds.zmin))
            blank = (blank[0], HEADER_DEPTH, blank[2])
        elif name.startswith('base_rail_'):
            x0, x1 = max(bounds.xmin, -base.INNER_EDGE), min(bounds.xmax, base.INNER_EDGE)
            clip = cq.Solid.makeBox(x1-x0, bounds.ylen+2., bounds.zlen+2.,
                cq.Vector(x0, bounds.ymin-1., bounds.zmin-1.))
            shape = shape.intersect(clip).clean()
            blank = (x1-x0, *blank[1:])
        if name.startswith(('base_side_', 'base_principal_')):
            bounds = shape.BoundingBox()
            if bounds.ymin < INCLINED_TRIM_Y:
                cutter = cq.Solid.makeBox(bounds.xlen+2., INCLINED_TRIM_Y-bounds.ymin+1., bounds.zlen+2.,
                    cq.Vector(bounds.xmin-1., bounds.ymin-1., bounds.zmin-1.))
                shape = shape.cut(cutter).clean()
        result.append(replace(part, shape=shape, blank=blank, description=LIMITS))
    return tuple(result)


@dataclass(frozen=True)
class CompactLegBolt(FrameBolt):
    """Complete provisional 1/2-inch bolt, washer, head and nut envelopes."""

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
    result = [c for c in previous.connections()
              if not c.name.startswith('lumber_leg_bolt_') and not c.members[0].startswith('clip_')]
    result.extend(hardware.clip_connections(stations()))
    for side, sign in (('left', -1), ('right', 1)):
        for index, point in enumerate(bolt_points(), 1):
            result.append(CompactLegBolt(f'lumber_leg_bolt_{side}_{index}',
                cq.Vector(sign*(b.HALF+THICKNESS+WASHER_THICKNESS_MM), point.y, point.z),
                cq.Vector(-sign, 0., 0.), BOLT_LENGTH_MM, BOLT_DIAMETER_MM,
                (f'lumber_leg_{side}', f'base_side_{side}'), 'bolt', 2*THICKNESS,
                product_status=LIMITS+'; provisional hardware envelopes'))
    return tuple(result)


def bolt_interface_point(connection):
    return connection.start+connection.direction*(WASHER_THICKNESS_MM+THICKNESS)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, previous.previous.CountersunkPanelScrew))


def outer_base_angles():
    return tuple(p for p in hardware.clip_parts(stations()) if p.name.startswith('clip_angle_base_'))


@cache
def uncut_wood_parts():
    changed = {p.name:p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


@cache
def bore_records():
    source = previous.previous.wiring
    local = tuple(replace(p, shape=p.shape.translate(-previous.SHIFT)) for p in uncut_wood_parts())
    return tuple({**record, 'start_mm':list((cq.Vector(*record['start_mm'])+previous.SHIFT).toTuple())}
                 for record in source.bore_records(local))


@cache
def service_cutters():
    return tuple((record['member'], record['name'], previous.previous.wiring.bore_shape(record))
                 for record in bore_records())


@cache
def parts():
    result = {p.name:p for p in previous.parts()}
    result.update({p.name:p for p in raw_changed_parts()})
    result.update({p.name:p for p in hardware.clip_parts(stations())})
    for name, _, cutter in service_cutters():
        if name in CHANGED_NAMES:
            result[name] = replace(result[name], shape=result[name].shape.cut(cutter).clean())
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in CHANGED_NAMES:
                continue
            diameter = HOLE_DIAMETER if isinstance(c, CompactLegBolt) else 11.1125 if c.kind == 'bolt' else c.diameter
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
