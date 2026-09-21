"""Isolated fresh-stock wider leg/rim candidate; not a selected assembly.

Outer rim front faces stay fixed. Historical drilling is never plugged or
reused: the four changed members start from raw stock and receive current cuts.
"""
import csv
import hashlib
import json
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

import cadquery as cq

from . import lumber_leg_spread_frame as leg_source
from . import round_reinforcement_frame as previous
from . import round_structural_frame as structural
from . import steel_base_reinforcement as shoes
from . import wider_leg_hardware as catalog
from .bolted_frame import FrameBolt

KEY = 'wider-leg-development'
LIMITS = 'Isolated single 2x8 leg/rim candidate; geometry evidence only; not construction qualified'
DEPTH = 184.15
THICKNESS = 38.1
HOLE_DIAMETER = 14.2875
TOP_EXTENSION = 200.0
PATTERN_ALONG_LEG = 66.0
PATTERN_ALONG_RIM = 84.0
SHIFT_FROM_OLD_LEG = 27.0
SHIFT_FROM_OLD_RIM = 4.0
CHANGED_NAMES = ('base_side_left', 'base_side_right', 'lumber_leg_left', 'lumber_leg_right')


def __getattr__(name):
    return getattr(previous, name)


def axes():
    origin = previous.b.point(0, 0, 0)
    rim = (previous.b.point(0, 1, 0)-origin).normalized()
    centre, foot, along, across = leg_source.geometry('2x8', 0.0)
    return centre, foot, along, across, rim


def bolt_points():
    """Six axes in Y/Z; X is assigned separately at each outer face."""
    _, _, along, _, rim = axes()
    old = previous.bolt_points()
    centre = sum(old, cq.Vector()) / len(old)
    return tuple(centre+along*(SHIFT_FROM_OLD_LEG+s*PATTERN_ALONG_LEG)
                 +rim*(SHIFT_FROM_OLD_RIM+t*PATTERN_ALONG_RIM/2)
                 for s in (-1, 0, 1) for t in (-1, 1))


@cache
def raw_changed_parts():
    old = {p.name: p for p in previous.uncut_wood_parts()}
    origin = previous.b.point(0, 0, 0)
    centre, foot, along, across, rim = axes()
    result = []
    for side in ('left', 'right'):
        name = 'base_side_'+side
        part = old[name]
        vertices = [v.Center() for v in part.shape.Vertices()]
        top = max((v-origin).dot(rim) for v in vertices)
        bounds = part.shape.BoundingBox()
        shape, blank = previous.base._sloped_bearing_member(bounds.xmin, bounds.xmax, DEPTH, top)
        widened = replace(part, shape=shape, blank=blank, description=LIMITS+'; front N=0; rear N=184.15; original top and bearing levels')
        result.extend(shoes.trim_bearing_ends((widened,)))
        top_point = centre+along*TOP_EXTENSION
        corners = []
        for offset in (-DEPTH/2, DEPTH/2):
            bottom = foot+across*offset
            bottom = bottom-along*(bottom.z/along.z)
            corners.append((bottom, top_point+across*offset))
        points = [corners[0][0], corners[1][0], corners[1][1], corners[0][1]]
        x0 = previous.b.HALF if side == 'right' else -previous.b.HALF-THICKNESS
        plane = cq.Plane(origin=(x0, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
        shape = cq.Workplane(plane).polyline([(p.y, p.z) for p in points]).close().extrude(THICKNESS).val()
        length = max(p.dot(along) for p in points)-min(p.dot(along) for p in points)
        result.append(replace(old['lumber_leg_'+side], shape=shape, blank=(length, DEPTH, THICKNESS), description=LIMITS+'; preserved grain axis and level foot; square top200mm above original datum'))
    return tuple(result)


COMPONENT_LABELS = ('shaft', 'head_plate', 'nut_plate', 'spacer_1', 'spacer_2', 'spacer_3', 'head', 'nut')
PLATE_WIDTH = catalog.PLATE_SIDE
PLATE_THICKNESS = catalog.PLATE_THICKNESS
PLATE_HOLE = catalog.PLATE_HOLE
SPACER_OD = (catalog.WASHER_OD_MIN+catalog.WASHER_OD_MAX)/2
SPACER_ID = (catalog.WASHER_ID_MIN+catalog.WASHER_ID_MAX)/2
SPACER_THICKNESS = catalog.WASHER_THICKNESS


@dataclass(frozen=True)
class WiderLegBolt(FrameBolt):
    """Complete catalog stack, nominal washers and conservative hex envelopes."""

    def components(self):
        d = self.direction.normalized()
        _, _, along, _, _ = axes()

        def ring(outer, inner, thickness, station):
            start = self.start+d*station
            return cq.Solid.makeCylinder(outer/2, thickness, start, d).cut(
                cq.Solid.makeCylinder(inner/2, thickness, start, d))

        def plate(station):
            plane = cq.Plane(origin=self.start+d*station, xDir=along, normal=d)
            block = cq.Workplane(plane).rect(PLATE_WIDTH, PLATE_WIDTH).extrude(PLATE_THICKNESS).val()
            return block.cut(cq.Solid.makeCylinder(PLATE_HOLE/2, PLATE_THICKNESS, self.start+d*station, d))

        spacers_start = 2*PLATE_THICKNESS+self.grip
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d),
                plate(0), plate(PLATE_THICKNESS+self.grip),
                *(ring(SPACER_OD, SPACER_ID, SPACER_THICKNESS, spacers_start+i*SPACER_THICKNESS) for i in range(3)),
                cq.Solid.makeCylinder(catalog.HEX_CORNERS_MAX/2, catalog.HEAD_HEIGHT_MAX, self.start, -d),
                ring(catalog.HEX_CORNERS_MAX, self.diameter, catalog.NUT_HEIGHT_MAX, spacers_start+3*SPACER_THICKNESS))


@cache
def connections():
    result = [c for c in previous.connections() if not c.name.startswith('lumber_leg_bolt_')]
    for side, sign in (('left', -1), ('right', 1)):
        for index, point in enumerate(bolt_points(), 1):
            # Placeholder conventional envelope; replaced by catalog stack below.
            result.append(WiderLegBolt(f'lumber_leg_bolt_{side}_{index}',
                cq.Vector(sign*(previous.b.HALF+THICKNESS+PLATE_THICKNESS), point.y, point.z),
                cq.Vector(-sign, 0, 0), 127.0, 12.7,
                (f'lumber_leg_{side}', f'base_side_{side}'), 'bolt', 76.2,
                product_status=LIMITS+'; PECO12X5HBG5USSZ; two BP1/2 plates; three Wrought014943 spacers; Grade5 nut'))
    return tuple(result)


@cache
def parts():
    result = {p.name: p for p in previous.parts()}
    result.update({p.name: p for p in raw_changed_parts()})
    # Keep existing LED axes and passage diameters; widening does not reroute LEDs.
    for record in structural.bore_records():
        if record['member'] in CHANGED_NAMES:
            part = result[record['member']]
            result[part.name] = replace(part, shape=part.shape.cut(structural.wiring.bore_shape(record)).clean())
    for connection in connections():
        for index, name in enumerate(connection.members):
            if name not in CHANGED_NAMES:
                continue
            part = result[name]
            diameter = HOLE_DIAMETER if connection.name.startswith('lumber_leg_bolt_') else 11.1125 if connection.kind == 'bolt' else connection.diameter
            cutter = cq.Solid.makeCylinder(diameter/2, connection.length+2,
                                          connection.start-connection.direction, connection.direction)
            shape = part.shape.cut(cutter)
            if index == 0 and connection.kind == 'screw':
                shape = shape.cut(connection.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())


def drilling_records():
    origin = previous.b.point(0, 0, 0)
    centre, _, along, across, rim = axes()
    rows = []
    for connection in connections():
        if not connection.name.startswith('lumber_leg_bolt_'):
            continue
        point = cq.Vector(0, connection.start.y, connection.start.z)
        for member in connection.members:
            is_leg = member.startswith('lumber_leg_')
            rows.append({'connection': connection.name, 'member': member,
                'diameter_mm': HOLE_DIAMETER,
                'world_y_mm': point.y, 'world_z_mm': point.z,
                'grain_station_mm': (point-centre).dot(along) if is_leg else (point-origin).dot(rim),
                'depth_coordinate_mm': (point-centre).dot(across)+DEPTH/2 if is_leg else (point-origin).dot(previous.b.normal()),
                'datum': 'original leg center, depth from negative across edge' if is_leg else 'panel S=0, N=0 front face',
                'fresh_stock_only': True})
    return rows


def geometry_review():
    raw = {p.name: p for p in raw_changed_parts()}
    drilled = {p.name: p for p in parts() if p.name in CHANGED_NAMES}
    rows = drilling_records()
    failures = []
    witnesses = []
    for connection in connections():
        if not connection.name.startswith('lumber_leg_bolt_'):
            continue
        cylinder = cq.Solid.makeCylinder(HOLE_DIAMETER/2, 200,
            connection.start-connection.direction*50, connection.direction)
        for member in connection.members:
            raw_volume = raw[member].shape.intersect(cylinder).Volume()
            remaining = drilled[member].shape.intersect(cylinder).Volume()
            expected = 3.141592653589793*(HOLE_DIAMETER/2)**2*THICKNESS
            supported = abs(raw_volume-expected) < 0.01
            if not supported or remaining > 0.01:
                failures.append([connection.name, member, 'bore containment or removal', raw_volume, remaining])
            witnesses.append({'connection': connection.name, 'member': member,
                              'raw_bore_volume_mm3': raw_volume, 'expected_mm3': expected,
                              'remaining_wood_in_bore_mm3': remaining})
    from fea.reinforcement_review import interference
    hardware = {c.name: cq.Compound.makeCompound(c.components()) for c in connections()}
    all_parts = {p.name: p.shape for p in parts()}
    interference_rows = []
    for name in CHANGED_NAMES:
        for other, shape in all_parts.items():
            if other == name:
                continue
            volume = interference(all_parts[name], shape)
            if volume > 0.01:
                interference_rows.append([name, other, volume])
        for other, shape in hardware.items():
            volume = interference(all_parts[name], shape)
            if volume > 0.01:
                interference_rows.append([name, other, volume])
    plate_support = []
    for connection in connections():
        if not isinstance(connection, WiderLegBolt):
            continue
        for label, index, member, sign in (('head_plate', 1, connection.members[0], 1),
                                           ('nut_plate', 2, connection.members[1], -1)):
            plate = connection.components()[index].translate(connection.direction*sign*PLATE_THICKNESS)
            unsupported = max(0., plate.Volume()-plate.intersect(raw[member].shape).Volume())
            plate_support.append({'bolt': connection.name, 'plate': label, 'unsupported_mm3': unsupported})
            if unsupported > 0.01:
                failures.append([connection.name, label, 'unsupported plate', unsupported])
        for other, shape in hardware.items():
            if other == connection.name:
                continue
            volume = interference(hardware[connection.name], shape)
            if volume > 0.01:
                interference_rows.append([connection.name, other, volume])
        for other, shape in all_parts.items():
            volume = interference(hardware[connection.name], shape)
            if volume > 0.01:
                interference_rows.append([connection.name, other, volume])
    failures.extend(interference_rows)
    import sys

    from fea.round_insert_floor import current_mass, inventory_state
    _, inventory = current_mass(sys.modules[__name__])
    for row in inventory:
        if row['name'].startswith('hold_tnut_'):
            row.update(material='steel T-nut envelope', density_kg_m3=7850,
                       mass_kg=row['volume_mm3']/1.e9*7850)
    feet = {name: [list(v.Center().toTuple()) for v in raw[name].shape.Vertices() if abs(v.Z)<1.e-6]
            for name in CHANGED_NAMES if name.startswith('lumber_leg_')}
    return {'status': LIMITS, 'nominal_geometry_pass': not failures,
            'mass_inventory': inventory, 'state': inventory_state(inventory),
            'foot_polygons_xyz_mm': feet, 'plate_support': plate_support,
            'interferences': interference_rows,
            'all_changed_member_connections': [{'name': c.name, 'members': c.members,
                'start_xyz_mm': c.start.toTuple(), 'direction': c.direction.toTuple(),
                'length_mm': c.length, 'diameter_mm': c.diameter} for c in connections()
                if set(c.members).intersection(CHANGED_NAMES)],
            'preserved_LED_passages': [r for r in structural.bore_records() if r['member'] in CHANGED_NAMES],
            'failures': failures, 'drilling': rows, 'bore_witnesses': witnesses,
            'changed_members': [{'name': p.name, 'blank_mm': p.blank,
                'volume_mm3': drilled[p.name].shape.Volume(),
                'center_xyz_mm': drilled[p.name].shape.Center().toTuple(),
                'valid': drilled[p.name].shape.isValid()} for p in raw.values()],
            'selected_variant_changed': False, 'strength_qualified': False}


def export_review(directory):
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    report = geometry_review()
    report['raw_edge_distances'] = drilling_edge_distances()
    report['local_rim_cuts'] = local_rim_cut_records()
    report['source_sha256'] = source_hashes()
    (target/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    rows = drilling_records()
    with (target/'drilling.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assembly = cq.Assembly(name=KEY)
    for part in parts():
        assembly.add(part.shape, name=part.name)
    for connection in connections():
        for index, component in enumerate(connection.components()):
            assembly.add(component, name=f'{connection.name}_component_{index}')
    assembly.save(str(target/'assembly.step'))
    return report


def drilling_edge_distances():
    """Actual polygon ray distances from each axis; raw edges, not strength rules."""
    import numpy as np
    from scipy.spatial import ConvexHull

    raw = {p.name: p for p in raw_changed_parts()}
    centre, _, along, across, rim = axes()
    origin = previous.b.point(0, 0, 0)
    result = []
    for row in drilling_records():
        leg = row['member'].startswith('lumber_leg_')
        u, v, datum = (along, across, centre) if leg else (rim, previous.b.normal(), origin)
        polygon = np.array([[(p.Center()-datum).dot(u), (p.Center()-datum).dot(v)]
                            for p in raw[row['member']].shape.Vertices()])
        hull = ConvexHull(polygon)
        point = cq.Vector(0, row['world_y_mm'], row['world_z_mm'])
        xy = np.array([(point-datum).dot(u), (point-datum).dot(v)])
        rays = {}
        for label, direction in (('grain_positive', (1, 0)), ('grain_negative', (-1, 0)),
                                  ('depth_positive', (0, 1)), ('depth_negative', (0, -1))):
            candidates = []
            for a, b, c in hull.equations:
                rate = a*direction[0]+b*direction[1]
                if rate > 1.e-9:
                    candidates.append(-(a*xy[0]+b*xy[1]+c)/rate)
            rays[label+'_mm'] = float(min(candidates))
        result.append({'connection': row['connection'], 'member': row['member'], **rays})
    return result


def source_hashes():
    from fea.reinforcement_review import sources

    paths = set(sources()) | {'mini_moonboard/wider_leg_frame.py',
                              'mini_moonboard/wider_leg_hardware.py'}
    return {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sorted(paths)}


def local_rim_cut_records():
    """Inventory every occupied fastener cut intersecting the bolt-group span.

    Bounds follow the same cylinder used by parts(). A panel screw occupies
    only part of rim thickness; treating its depth interval as full-width loss
    requires an explicitly conservative resistance assumption.
    """
    origin = previous.b.point(0, 0, 0)
    _, _, _, _, rim = axes()
    normal = previous.b.normal()
    stations = [(p-origin).dot(rim) for p in bolt_points()]
    low, high = min(stations)-HOLE_DIAMETER/2, max(stations)+HOLE_DIAMETER/2
    records = []
    for c in connections():
        members = [name for name in c.members if name.startswith('base_side_')]
        if not members:
            continue
        diameter = HOLE_DIAMETER if isinstance(c, WiderLegBolt) else 11.1125 if c.kind == 'bolt' else c.diameter
        a, z = c.start-c.direction, c.start+c.direction*(c.length+1)
        sr = diameter/2*(1-c.direction.dot(rim)**2)**.5
        nr = diameter/2*max(0., 1-c.direction.dot(normal)**2)**.5
        slo, shi = sorted(((a-origin).dot(rim), (z-origin).dot(rim)))
        nlo, nhi = sorted(((a-origin).dot(normal), (z-origin).dot(normal)))
        if shi+sr < low or slo-sr > high:
            continue
        records.append({'connection': c.name, 'members': members,
                        'grain_extent_mm': [slo-sr, shi+sr],
                        'depth_extent_inside_rim_mm': [max(0., nlo-nr), min(DEPTH, nhi+nr)],
                        'cut_diameter_mm': diameter, 'direction_xyz': c.direction.toTuple(),
                        'is_leg_bolt': isinstance(c, WiderLegBolt)})
    return records
