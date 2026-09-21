"""Enclosed strand passages and provisional lights-last cable routing."""
import itertools
import json
from dataclasses import dataclass
from functools import cache
from math import acos, tan
from pathlib import Path

import cadquery as cq

from . import box_frame as b
from . import timber_frame as timber

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'docs/round-service-wiring-reference.json'
DATA = json.loads(REFERENCE.read_text())
MEASURED_MAXIMUM_DIAMETER_MM = DATA['user_measurements']['maximum_harness_outside_diameter_mm']
APPROXIMATE_PATH_BUDGET_MM = DATA['user_measurements']['approximate_bulb_base_pitch_mm']
BORE_DIAMETER_MM = DATA['installation']['provisional_passage_diameter_mm']
GEOMETRY = DATA['provisional_geometry_mm']
ROUTING_DEPTH_MM = GEOMETRY['routing_plane_N']
BASE_DEPTH_MM = GEOMETRY['bulb_base_plane_N']
CABLE_DIAMETER_MM = GEOMETRY['cable_outside_diameter']
CORNER_RADIUS_MM = GEOMETRY['modeled_corner_radius']
LIMITS = ('Measured maximum harness diameter 12.7 mm; provisional 25.4 mm enclosed passages; '
          'lights installed after panels; connector length, bend radius, feeding access, '
          'extra slack and connection/wood resistance unverified')


@dataclass(frozen=True)
class WiringPart:
    name: str
    shape: cq.Shape
    kind: str


def _corners(points):
    for first, corner, last in zip(points[:-2], points[1:-1], points[2:], strict=True):
        u, v = (corner-first).normalized(), (last-corner).normalized()
        angle = acos(max(-1., min(1., u.dot(v))))
        distance = CORNER_RADIUS_MM*tan(angle/2)
        a, z = corner-u*distance, corner+v*distance
        center = a+(v-u*u.dot(v)).normalized()*CORNER_RADIUS_MM
        midpoint = center+((a-center)+(z-center)).normalized()*CORNER_RADIUS_MM
        yield a, midpoint, z, distance, angle


@cache
def segments():
    reference = json.loads((ROOT/DATA['route_reference']).read_text())
    order = reference['routing']['order']
    datums = timber.grid.main_led_datums()
    if len(order) != 132 or set(order) != set(datums):
        raise ValueError('The installed route must visit exactly 132 LED datums')
    result = []
    lead = GEOMETRY['endpoint_lead_distance']
    for index, (first, last) in enumerate(itertools.pairwise(order), 1):
        xa, sa = datums[first]
        xz, sz = datums[last]
        a, z = cq.Vector(xa-b.HALF, sa, BASE_DEPTH_MM), cq.Vector(xz-b.HALF, sz, BASE_DEPTH_MM)
        direction = (z-a).normalized()
        lateral = cq.Vector(GEOMETRY['vertical_run_lateral_offset'] if abs(xz-xa) < 1e-6 else 0., 0., 0.)
        rear = cq.Vector(0., 0., ROUTING_DEPTH_MM-BASE_DEPTH_MM)
        points = [a, a+direction*lead+lateral+rear, z-direction*lead+lateral+rear, z]
        polyline = sum((q-p).Length for p, q in itertools.pairwise(points))
        length = polyline+sum(CORNER_RADIUS_MM*angle-2*distance for _, _, _, distance, angle in _corners(points))
        result.append({'name': f'wire_{index:03d}_{first}_{last}', 'index': index, 'datums': [first, last],
            'route_local_mm': [list(p.toTuple()) for p in points], 'corner_radius_mm': CORNER_RADIUS_MM,
            'routed_length_mm': length, 'polyline_length_upper_bound_mm': polyline,
            'approximate_path_budget_mm': APPROXIMATE_PATH_BUDGET_MM,
            'nominal_budget_remaining_mm': APPROXIMATE_PATH_BUDGET_MM-length,
            'within_approximate_budget': length <= APPROXIMATE_PATH_BUDGET_MM,
            'string_connector_envelope': index in (50, 100),
            'additional_slack_accommodation_modeled': False, 'qualified_for_installation': False})
    return tuple(result)


def wire_path(record):
    points = [b.point(*p) for p in record['route_local_mm']]
    edges, cursor = [], points[0]
    for a, midpoint, z, _, _ in _corners(points):
        edges.extend((cq.Edge.makeLine(cursor, a), cq.Edge.makeThreePointArc(a, midpoint, z)))
        cursor = z
    edges.append(cq.Edge.makeLine(cursor, points[-1]))
    return cq.Wire.assembleEdges(edges)


@cache
def parts():
    result = []
    for name, (x, s) in timber.grid.main_led_datums().items():
        shape = cq.Solid.makeCylinder(MEASURED_MAXIMUM_DIAMETER_MM/2,
            timber.product.FACE_THICKNESS_MM+GEOMETRY['rear_body_projection'],
            b.point(x-b.HALF, s, -timber.product.FACE_THICKNESS_MM), b.normal())
        result.append(WiringPart('light_'+name, shape, 'light'))
    for record in segments():
        path = wire_path(record)
        first, second = [b.point(*p) for p in record['route_local_mm'][:2]]
        plane = cq.Plane(origin=first, normal=(second-first).normalized())
        shape = cq.Workplane(plane).circle(CABLE_DIAMETER_MM/2).sweep(cq.Workplane(obj=path), isFrenet=True).val()
        if record['string_connector_envelope']:
            a, z = [b.point(*p) for p in record['route_local_mm'][1:3]]
            direction, midpoint = (z-a).normalized(), (a+z)*.5
            connector = cq.Solid.makeCylinder(MEASURED_MAXIMUM_DIAMETER_MM/2, GEOMETRY['connector_length'],
                midpoint-direction*GEOMETRY['connector_length']/2, direction)
            shape = shape.fuse(connector).clean()
        result.append(WiringPart(record['name'], shape, 'wire'))
    return tuple(result)


def bore_shape(record):
    return cq.Solid.makeCylinder(record['diameter_mm']/2, record['length_mm'],
                                 cq.Vector(*record['start_mm']), cq.Vector(*record['direction']))


def bore_records(raw_parts):
    """Straight round passages through complete timber, never front-open slots."""
    origin = b.point(0., 0., 0.)
    tangent = (b.point(0., 1., 0.)-origin).normalized()
    result = []
    for part in raw_parts:
        if not part.name.startswith(('base_rail_', 'base_principal_', 'base_side_')):
            continue
        vertices = [v.Center() for v in part.shape.Vertices()]
        xmin, xmax = min(v.x for v in vertices), max(v.x for v in vertices)
        smin, smax = min((v-origin).dot(tangent) for v in vertices), max((v-origin).dot(tangent) for v in vertices)
        for segment in segments():
            a, z = segment['route_local_mm'][1:3]
            vertical = abs(a[0]-z[0]) < 1e-6
            if vertical:
                low, high = max(min(a[1], z[1]), smin), min(max(a[1], z[1]), smax)
                if high-low < 1e-6:
                    continue
                start, direction, length = b.point(a[0], low-1., ROUTING_DEPTH_MM), tangent, high-low+2.
            else:
                low, high = max(min(a[0], z[0]), xmin), min(max(a[0], z[0]), xmax)
                if high-low < 1e-6:
                    continue
                start, direction, length = b.point(low-1., a[1], ROUTING_DEPTH_MM), cq.Vector(1., 0., 0.), high-low+2.
            record = {'name': f'bore_{part.name}_{segment["index"]:03d}', 'member': part.name,
                'start_mm': list(start.toTuple()), 'direction': list(direction.toTuple()),
                'length_mm': length, 'diameter_mm': BORE_DIAMETER_MM,
                'axis_local': 'S' if vertical else 'X',
                'center_x_mm': a[0] if vertical else (low+high)/2,
                'center_s_mm': (low+high)/2 if vertical else a[1], 'center_n_mm': ROUTING_DEPTH_MM,
                'member_entry_mm': low, 'member_exit_mm': high, 'datums': segment['datums'],
                'entry_face': 'timber side face; enclosed round passage', 'qualified_for_machining': False}
            if part.shape.intersect(bore_shape(record)).Volume() > 1e-5:
                result.append(record)
    return tuple(result)
