"""Provisional prewired LED harness and open-front timber routing channels.

The user's approximately 12-inch bulb-base pitch is an approximate path budget,
not a guaranteed cable length. Nominal body, connector, cable and bend geometry
below require measurements of the supplied kit before machining or installation.
"""
import itertools
import json
from dataclasses import dataclass
from functools import cache
from math import asin, hypot
from pathlib import Path

import cadquery as cq

from . import box_frame as b
from . import timber_frame as timber

REFERENCE = Path(__file__).resolve().parents[1]/'docs/led-wiring-reference.json'
STEM_DIAMETER_MM = 12.5
BODY_DIAMETER_MM = 16.
BODY_REAR_DEPTH_MM = 12.
CABLE_DIAMETER_MM = 4.
CONNECTOR_DIAMETER_MM = 20.
CONNECTOR_LENGTH_MM = 30.
CONNECTOR_CENTER_DEPTH_MM = 12.
BASE_DEPTH_MM = 8.
ARC_SAG_MM = 0.
LATERAL_SAG_MM = 30.
ROUTE_SAMPLE_COUNT = 128
ROUTE_BOUND_MARGIN_MM = .1
CHANNEL_WIDTH_MM = 8.
CHANNEL_DEPTH_MM = 12.
APPROXIMATE_PATH_BUDGET_MM = 304.8
LIMITS = ('Provisional kit envelopes and cable routing; approximately 304.8 mm measured '
          'bulb-base pitch is not guaranteed available cable; connector dimensions, '
          'bend limits, strain relief, extensions and controller routing unverified; '
          'displayed arcs are provisional routes, additional harness slack is not modeled')


@dataclass(frozen=True)
class WiringPart:
    name: str
    shape: cq.Shape
    kind: str


@cache
def segments():
    reference = json.loads(REFERENCE.read_text())
    order = reference['routing']['order']
    datums = timber.grid.main_led_datums()
    if len(order) != 132 or len(set(order)) != 132 or set(order) != set(datums):
        raise ValueError('LED route must visit all 132 installed datums exactly once')
    result = []
    for index, (first, last) in enumerate(itertools.pairwise(order), 1):
        x0, s0 = datums[first]
        x1, s1 = datums[last]
        chord = ((x1-x0)**2+(s1-s0)**2)**.5
        lateral = LATERAL_SAG_MM if abs(x1-x0) < 1e-6 else 0.
        sag = hypot(ARC_SAG_MM, lateral)
        radius = chord*chord/(8*sag)+sag/2 if sag else None
        length = 2*radius*asin(chord/(2*radius)) if radius else chord
        result.append({'name': f'wire_{index:03d}_{first}_{last}', 'index': index,
            'datums': [first, last], 'start_local_mm': [x0-b.HALF, s0, BASE_DEPTH_MM],
            'end_local_mm': [x1-b.HALF, s1, BASE_DEPTH_MM],
            'sag_mm': sag, 'rear_sag_mm': ARC_SAG_MM, 'lateral_sag_mm': lateral,
            'bend_radius_mm': radius,
            'routed_length_mm': length, 'approximate_path_budget_mm': APPROXIMATE_PATH_BUDGET_MM,
            'nominal_budget_remaining_mm': APPROXIMATE_PATH_BUDGET_MM-length,
            'additional_slack_accommodation_modeled': False,
            'within_approximate_budget': length <= APPROXIMATE_PATH_BUDGET_MM,
            'string_connector_envelope': index in (50, 100), 'qualified_for_installation': False})
    return tuple(result)


def wire_path(record):
    first, last = record['start_local_mm'], record['end_local_mm']
    start, end = b.point(*first), b.point(*last)
    if not record['sag_mm']:
        return cq.Edge.makeLine(start, end)
    midpoint = b.point((first[0]+last[0])/2+record['lateral_sag_mm'],
                      (first[1]+last[1])/2, BASE_DEPTH_MM+ARC_SAG_MM)
    return cq.Edge.makeThreePointArc(start, midpoint, end)


@cache
def parts():
    result = []
    for name, (x, s) in timber.grid.main_led_datums().items():
        stem = cq.Solid.makeCylinder(STEM_DIAMETER_MM/2, timber.product.FACE_THICKNESS_MM,
            b.point(x-b.HALF, s, -timber.product.FACE_THICKNESS_MM), b.normal())
        rear = cq.Solid.makeCylinder(BODY_DIAMETER_MM/2, BODY_REAR_DEPTH_MM,
            b.point(x-b.HALF, s, 0.), b.normal())
        result.append(WiringPart('light_'+name, stem.fuse(rear).clean(), 'light'))
    for record in segments():
        arc = wire_path(record)
        path = cq.Wire.assembleEdges([arc])
        plane = cq.Plane(origin=arc.startPoint(), normal=arc.tangentAt(0.))
        shape = cq.Workplane(plane).circle(CABLE_DIAMETER_MM/2).sweep(cq.Workplane(obj=path), isFrenet=True).val()
        if record['string_connector_envelope']:
            center = arc.positionAt(.5)+b.normal()*(CONNECTOR_CENTER_DEPTH_MM-BASE_DEPTH_MM)
            connector = cq.Solid.makeCylinder(CONNECTOR_DIAMETER_MM/2, CONNECTOR_LENGTH_MM,
                center-arc.tangentAt(.5)*(CONNECTOR_LENGTH_MM/2), arc.tangentAt(.5))
            shape = shape.fuse(connector).clean()
        result.append(WiringPart(record['name'], shape, 'wire'))
    return tuple(result)


def cutout_shape(record):
    return b.block(record['x0_mm'], record['x1_mm'], record['s0_mm'], record['s1_mm'],
                   0., record['depth_mm'])


def cutout_records(raw_parts):
    """Open-front channels clipped to actual sloped-member timber extents.

Horizontal turns at E12/F12 and F1/G1 cross the separated center principals;
these require transverse channels even though straight columns clear them.
"""
    origin = b.point(0., 0., 0.)
    tangent = (b.point(0., 1., 0.)-origin).normalized()
    result = []
    routes = []
    for segment in segments():
        arc = wire_path(segment)
        points = [arc.positionAt(i/ROUTE_SAMPLE_COUNT) for i in range(ROUTE_SAMPLE_COUNT+1)]
        # The enclosing rectangles include more than the maximum chord/arc
        # deviation, so channels contain the smooth path between samples.
        if segment['bend_radius_mm']:
            assert (segment['routed_length_mm']/ROUTE_SAMPLE_COUNT)**2/(8*segment['bend_radius_mm']) < ROUTE_BOUND_MARGIN_MM
        local = [(p.x, (p-origin).dot(tangent)) for p in points]
        routes.append((segment, local))
    for part in raw_parts:
        if not part.name.startswith(('base_rail_', 'base_principal_', 'base_side_')):
            continue
        vertices = [v.Center() for v in part.shape.Vertices()]
        xmin, xmax = min(v.x for v in vertices), max(v.x for v in vertices)
        smin, smax = min((v-origin).dot(tangent) for v in vertices), max((v-origin).dot(tangent) for v in vertices)
        for segment, points in routes:
            boxes = []
            margin = CHANNEL_WIDTH_MM/2+ROUTE_BOUND_MARGIN_MM
            for first, last in itertools.pairwise(points):
                x0, x1 = max(min(first[0], last[0])-margin, xmin), min(max(first[0], last[0])+margin, xmax)
                s0, s1 = max(min(first[1], last[1])-margin, smin), min(max(first[1], last[1])+margin, smax)
                if x1-x0 > 1e-6 and s1-s0 > 1e-6:
                    boxes.append((x0, x1, s0, s1))
            if not boxes:
                continue
            x0, x1 = min(row[0] for row in boxes), max(row[1] for row in boxes)
            s0, s1 = min(row[2] for row in boxes), max(row[3] for row in boxes)
            record = {'name': f'channel_{part.name}_{segment["index"]:03d}', 'member': part.name,
                'x0_mm': round(x0, 6), 'x1_mm': round(x1, 6),
                's0_mm': round(s0, 6), 's1_mm': round(s1, 6), 'depth_mm': CHANNEL_DEPTH_MM,
                'width_mm': CHANNEL_WIDTH_MM, 'datums': segment['datums'],
                'route_bound_margin_mm': ROUTE_BOUND_MARGIN_MM,
                'method': 'rectangular channel enclosing the local smooth cable route plus clearance',
                'entry_face': 'front N=0; open with face panel removed',
                'qualified_for_machining': False}
            if part.shape.intersect(cutout_shape(record)).Volume() > 1e-5:
                result.append(record)
    return tuple(result)
