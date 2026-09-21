"""Isolated nine-bolt single-2x10 leg/rim candidate on the shoe-free frame.

Fresh stock and explicit catalog stacks are development geometry, not a drilling
release. The rear rim overhang remains unsupported beyond the actual header.
"""
import math
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import no_shoes_frame as previous
from . import wider_leg_hardware as catalog
from .bolted_frame import FrameBolt

KEY = 'leg-mvp-development'
LIMITS = ('Exploratory single 2x10 legs/rims, nine 1/2-inch catalog bolts per leg; '
          'fresh stock only; no custom steel shoes; not selected or construction qualified')
DEPTH = 234.95
THICKNESS = 38.1
HOLE_DIAMETER = catalog.PLATE_HOLE
TOP_EXTENSION = 260.0  # 10 mm beyond screening layout for practical top-cut margin.
PATTERN_ALONG_LEG = 65.0
PATTERN_ALONG_RIM = 75.0
SHIFT_FROM_OLD_LEG = 50.0
CHANGED_NAMES = ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right')
b, base = previous.b, previous.base
leg_source = previous.leg_source
timber, hardware, wide = previous.previous.timber, previous.previous.hardware, previous.wide
stations = previous.stations
electrical_parts = previous.electrical_parts
attachment_datums = previous.attachment_datums
COMPONENT_LABELS = ('shaft', 'head_plate', 'nut_plate', 'spacer_1', 'spacer_2', 'spacer_3', 'head', 'nut')


def axes():
    origin = b.point(0, 0, 0)
    rim = (b.point(0, 1, 0)-origin).normalized()
    _, foot, along, across = leg_source.geometry('2x6', 0.)
    old = previous.bolt_points()
    centre = sum(old, cq.Vector())/len(old)
    return centre, foot+previous.SHIFT, along, across, rim


def bolt_points():
    centre, _, along, _, rim = axes()
    return tuple(centre+along*(SHIFT_FROM_OLD_LEG+s*PATTERN_ALONG_LEG)
                 +rim*(t*PATTERN_ALONG_RIM)
                 for s in (-1, 0, 1) for t in (-1, 0, 1))


@cache
def raw_changed_parts():
    old = {p.name: p for p in previous.uncut_wood_parts()}
    origin = b.point(0, 0, 0)
    centre, foot, along, across, rim = axes()
    result = []
    for side in ('left', 'right'):
        part = old['base_side_'+side]
        top = max((v.Center()-origin).dot(rim) for v in part.shape.Vertices())
        bounds = part.shape.BoundingBox()
        # The historical primitive is untrimmed raw wood. Translate its bearing
        # plane with the 277 mm kicker; do not inherit any steel-shoe clearance.
        shape, blank = previous.previous.base._sloped_bearing_member(
            bounds.xmin, bounds.xmax, DEPTH, top)
        result.append(replace(part, shape=shape.translate(previous.SHIFT), blank=blank,
            description=LIMITS+'; fixed N=0 front; full level bearing cut with actual rear overhang'))
        top_point = centre+along*TOP_EXTENSION
        corners = []
        for offset in (-DEPTH/2, DEPTH/2):
            bottom = foot+across*offset
            bottom = bottom-along*(bottom.z/along.z)
            corners.append((bottom, top_point+across*offset))
        points = [corners[0][0], corners[1][0], corners[1][1], corners[0][1]]
        x0 = b.HALF if side == 'right' else -b.HALF-THICKNESS
        plane = cq.Plane(origin=(x0, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
        shape = cq.Workplane(plane).polyline([(p.y, p.z) for p in points]).close().extrude(THICKNESS).val()
        length = max(p.dot(along) for p in points)-min(p.dot(along) for p in points)
        result.append(replace(old['lumber_leg_'+side], shape=shape,
            blank=(length, DEPTH, THICKNESS), description=LIMITS+'; original centreline; level foot; square top'))
    return tuple(result)


@dataclass(frozen=True)
class LegMvpBolt(FrameBolt):
    """PECO Grade 5 bolt, two BP1/2 plates, three MCX spacers and Grade 5 nut."""

    def components(self):
        d = self.direction.normalized()
        rim = axes()[4]

        def ring(outer, inner, thickness, station):
            start = self.start+d*station
            return cq.Solid.makeCylinder(outer/2, thickness, start, d).cut(
                cq.Solid.makeCylinder(inner/2, thickness, start, d))

        def plate(station):
            plane = cq.Plane(origin=self.start+d*station, xDir=rim, normal=d)
            block = cq.Workplane(plane).rect(catalog.PLATE_SIDE, catalog.PLATE_SIDE).extrude(catalog.PLATE_THICKNESS).val()
            return block.cut(cq.Solid.makeCylinder(catalog.PLATE_HOLE/2, catalog.PLATE_THICKNESS, self.start+d*station, d))

        seat = 2*catalog.PLATE_THICKNESS+self.grip
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d),
                plate(0), plate(catalog.PLATE_THICKNESS+self.grip),
                *(ring((catalog.WASHER_OD_MIN+catalog.WASHER_OD_MAX)/2,
                       (catalog.WASHER_ID_MIN+catalog.WASHER_ID_MAX)/2,
                       catalog.WASHER_THICKNESS, seat+i*catalog.WASHER_THICKNESS) for i in range(3)),
                cq.Solid.makeCylinder(catalog.HEX_CORNERS_MAX/2, catalog.HEAD_HEIGHT_MAX, self.start, -d),
                ring(catalog.HEX_CORNERS_MAX, self.diameter, catalog.NUT_HEIGHT_MAX,
                     seat+3*catalog.WASHER_THICKNESS))


@cache
def connections():
    result = [c for c in previous.connections() if not c.name.startswith('lumber_leg_bolt_')]
    for side, sign in (('left', -1), ('right', 1)):
        for index, point in enumerate(bolt_points(), 1):
            result.append(LegMvpBolt(f'lumber_leg_bolt_{side}_{index}',
                cq.Vector(sign*(b.HALF+THICKNESS+catalog.PLATE_THICKNESS), point.y, point.z),
                cq.Vector(-sign, 0, 0), catalog.BOLT_LENGTH, catalog.BOLT_DIAMETER,
                (f'lumber_leg_{side}', f'base_side_{side}'), 'bolt', 2*THICKNESS,
                product_status=LIMITS+'; PECO12X5HBG5USSZ; two BP1/2 plates; three Wrought014943 spacers; Grade5 nut'))
    return tuple(result)


def bolt_interface_point(connection):
    """Actual mating plane after the outer BP1/2 plate and leg thickness."""
    return connection.start+connection.direction*(catalog.PLATE_THICKNESS+THICKNESS)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, previous.previous.CountersunkPanelScrew))


def outer_base_angles():
    return tuple(p for p in previous.parts() if p.name.startswith('clip_angle_base_'))


@cache
def uncut_wood_parts():
    changed = {p.name: p for p in raw_changed_parts()}
    return tuple(changed.get(p.name, p) for p in previous.uncut_wood_parts())


@cache
def parts():
    result = {p.name: p for p in previous.parts()}
    result.update({p.name: p for p in raw_changed_parts()})
    for record in previous.previous.bore_records():
        if record['member'] in CHANGED_NAMES:
            part = result[record['member']]
            cutter = previous.previous.wiring.bore_shape(record).translate(previous.SHIFT)
            result[part.name] = replace(part, shape=part.shape.cut(cutter).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in CHANGED_NAMES:
                continue
            part = result[name]
            diameter = HOLE_DIAMETER if isinstance(connection, LegMvpBolt) else 11.1125 if connection.kind == 'bolt' else connection.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, connection.length+2,
                                          connection.start-connection.direction, connection.direction)
            shape = part.shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())


def drilling_records():
    origin = b.point(0, 0, 0)
    centre, _, along, across, rim = axes()
    rows = []
    for c in connections():
        if not isinstance(c, LegMvpBolt):
            continue
        point = cq.Vector(0, c.start.y, c.start.z)
        for member in c.members:
            leg = member.startswith('lumber_leg_')
            rows.append({'connection': c.name, 'member': member, 'diameter_mm': HOLE_DIAMETER,
                'world_y_mm': point.y, 'world_z_mm': point.z,
                'grain_station_mm': (point-centre).dot(along) if leg else (point-origin).dot(rim),
                'depth_coordinate_mm': (point-centre).dot(across)+DEPTH/2 if leg else (point-origin).dot(b.normal()),
                'fresh_stock_only': True})
    return rows


def geometry_review():
    """Actual CAD fit witnesses; this potentially expensive check is explicit."""
    from fea.reinforcement_review import interference

    raw = {p.name: p for p in raw_changed_parts()}
    all_parts = {p.name: p.shape for p in parts()}
    bolts = [c for c in connections() if isinstance(c, LegMvpBolt)]
    components = {c.name: c.components() for c in connections()}
    hardware_shapes = {name: cq.Compound.makeCompound(shapes) for name, shapes in components.items()}
    failures, bores, support, collisions = [], [], [], []
    for c in bolts:
        cutter = cq.Solid.makeCylinder(HOLE_DIAMETER/2, 200., c.start-c.direction*50, c.direction)
        expected = math.pi*(HOLE_DIAMETER/2)**2*THICKNESS
        for member in c.members:
            contained = raw[member].shape.intersect(cutter).Volume()
            remaining = all_parts[member].intersect(cutter).Volume()
            bores.append({'connection': c.name, 'member': member, 'raw_volume_mm3': contained,
                          'expected_volume_mm3': expected, 'remaining_volume_mm3': remaining})
            if abs(contained-expected) > .01 or remaining > .01:
                failures.append([c.name, member, 'bore containment or removal'])
        for label, index, member, sign in (('head_plate', 1, c.members[0], 1), ('nut_plate', 2, c.members[1], -1)):
            plate = components[c.name][index].translate(c.direction*sign*catalog.PLATE_THICKNESS)
            unsupported = max(0., plate.Volume()-plate.intersect(raw[member].shape).Volume())
            support.append({'bolt': c.name, 'plate': label, 'unsupported_mm3': unsupported})
            if unsupported > .01:
                failures.append([c.name, label, 'unsupported plate', unsupported])
    pairs = set()
    for name in (*CHANGED_NAMES, *(c.name for c in bolts)):
        first = all_parts.get(name, hardware_shapes.get(name))
        for other, shape in {**all_parts, **hardware_shapes}.items():
            pair = tuple(sorted((name, other)))
            if name == other or pair in pairs:
                continue
            pairs.add(pair)
            volume = interference(first, shape)
            if volume > .01:
                collisions.append([name, other, volume])
    failures.extend(collisions)
    window = catalog.dimensional_window()
    if not window['dimensional_pass']:
        failures.append(['catalog stack dimensional window', window])
    return {'candidate': KEY, 'nominal_geometry_pass': not failures,
            'failures': failures, 'interferences': collisions, 'bore_witnesses': bores,
            'plate_support': support, 'drilling': drilling_records(),
            'catalog_stack_window': window, 'catalog_sources': catalog.SOURCES,
            'changed_members': [{'name': p.name, 'blank_mm': p.blank,
                'valid': all_parts[p.name].isValid(), 'volume_mm3': all_parts[p.name].Volume()} for p in raw.values()],
            'selected_variant_changed': False, 'strength_qualified': False}
