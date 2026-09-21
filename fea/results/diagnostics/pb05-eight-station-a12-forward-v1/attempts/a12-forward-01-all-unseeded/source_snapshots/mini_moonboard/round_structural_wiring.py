"""Candidate wiring with 1.5-inch passages in nominal 2x6 stock only.

Passages are centered in 2x6 depth; cable ramps follow the actual crossings.
Harness dimensions and feeding access remain provisional.
Historical round-service wiring is not modified.
"""
from collections import defaultdict
from functools import cache
from itertools import pairwise

import cadquery as cq

from . import round_service_wiring as previous

b = previous.b
REFERENCE, DATA = previous.REFERENCE, previous.DATA
MEASURED_MAXIMUM_DIAMETER_MM = previous.MEASURED_MAXIMUM_DIAMETER_MM
APPROXIMATE_PATH_BUDGET_MM = previous.APPROXIMATE_PATH_BUDGET_MM
ROUTING_DEPTH_MM = 69.85
BASE_DEPTH_MM = previous.BASE_DEPTH_MM
GEOMETRY = {**previous.GEOMETRY, 'routing_plane_N': ROUTING_DEPTH_MM}
CROSSING_LEAD_CLEARANCE_MM = 10.
CABLE_DIAMETER_MM = previous.CABLE_DIAMETER_MM
CORNER_RADIUS_MM = previous.CORNER_RADIUS_MM
TWO_BY_SIX_BORE_DIAMETER_MM = 38.1
OTHER_STOCK_BORE_DIAMETER_MM = previous.BORE_DIAMETER_MM
LIMITS = ('38.1 mm enclosed passages in nominal 2x6 stock; 25.4 mm in other stock; '
          'routing, feeding access, residual timber sections and resistance unqualified')
wire_path = previous.wire_path
bore_shape = previous.bore_shape


def bore_diameter_mm(part):
    """Select the nominal stock section from its actual blank dimensions."""
    section = sorted(part.blank)[:2]
    is_two_by_six = (len(section) == 2 and abs(section[0]-38.1) < 1.e-6
                     and abs(section[1]-139.7) < 1.e-6)
    return TWO_BY_SIX_BORE_DIAMETER_MM if is_two_by_six else OTHER_STOCK_BORE_DIAMETER_MM


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
        for segment in previous.segments():
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
                'length_mm': length, 'diameter_mm': bore_diameter_mm(part),
                'axis_local': 'S' if vertical else 'X',
                'center_x_mm': a[0] if vertical else (low+high)/2,
                'center_s_mm': (low+high)/2 if vertical else a[1], 'center_n_mm': ROUTING_DEPTH_MM,
                'member_entry_mm': low, 'member_exit_mm': high, 'datums': segment['datums'],
                'entry_face': 'timber side face; enclosed round passage', 'qualified_for_machining': False}
            if part.shape.intersect(bore_shape(record)).Volume() > 1e-5:
                result.append(record)
    return tuple(result)


@cache
def segments():
    """Adapt endpoint ramps to centered timber passages without changing LED order."""
    from . import round_insert_frame as layout

    crossings = defaultdict(list)
    for bore in bore_records(layout.uncut_wood_parts()):
        crossings[tuple(bore['datums'])].append(bore)
    result = []
    for original in previous.segments():
        first, last = [cq.Vector(*original['route_local_mm'][i]) for i in (0, 3)]
        distance = (last-first).Length
        direction = (last-first).normalized()
        vertical = abs(direction.x) < 1.e-6
        passages = crossings[tuple(original['datums'])]
        if passages:
            origin = first.y if vertical else first.x
            sign = direction.y if vertical else direction.x
            spans = [sorted(((bore['member_entry_mm']-origin)*sign,
                             (bore['member_exit_mm']-origin)*sign)) for bore in passages]
            first_lead = min(span[0] for span in spans)-CROSSING_LEAD_CLEARANCE_MM
            last_lead = distance-max(span[1] for span in spans)-CROSSING_LEAD_CLEARANCE_MM
        else:
            first_lead = last_lead = min(60., distance/3)
        if min(first_lead, last_lead) <= 0:
            raise ValueError('Insufficient endpoint space for centered passage: '+original['name'])
        offset = cq.Vector(GEOMETRY['vertical_run_lateral_offset'] if vertical else 0.,
                           0., ROUTING_DEPTH_MM-BASE_DEPTH_MM)
        points = [first, first+direction*first_lead+offset,
                  last-direction*last_lead+offset, last]
        corners = list(previous._corners(points))
        lengths = [(q-p).Length for p, q in pairwise(points)]
        cutbacks = [corner[3] for corner in corners]
        if (max(cutbacks) >= CROSSING_LEAD_CLEARANCE_MM
                or lengths[0] <= cutbacks[0] or lengths[2] <= cutbacks[1]
                or lengths[1] <= sum(cutbacks)):
            raise ValueError('Centered route has overlapping bends or timber entry: '+original['name'])
        polyline = sum(lengths)
        length = polyline+sum(CORNER_RADIUS_MM*angle-2*cutback
                              for _, _, _, cutback, angle in corners)
        result.append({**original, 'route_local_mm': [list(p.toTuple()) for p in points],
                       'routed_length_mm': length, 'polyline_length_upper_bound_mm': polyline,
                       'nominal_budget_remaining_mm': APPROXIMATE_PATH_BUDGET_MM-length,
                       'within_approximate_budget': length <= APPROXIMATE_PATH_BUDGET_MM,
                       'routing_method': 'centered passage with crossing-specific endpoint ramps',
                       'crossed_members': [bore['member'] for bore in passages]})
    return tuple(result)


@cache
def parts():
    """Build the candidate's own centered cable solids and provisional bulb bodies."""
    timber = previous.timber
    result = []
    for name, (x, station) in timber.grid.main_led_datums().items():
        shape = cq.Solid.makeCylinder(MEASURED_MAXIMUM_DIAMETER_MM/2,
            timber.product.FACE_THICKNESS_MM+GEOMETRY['rear_body_projection'],
            b.point(x-b.HALF, station, -timber.product.FACE_THICKNESS_MM), b.normal())
        result.append(previous.WiringPart('light_'+name, shape, 'light'))
    for record in segments():
        path = wire_path(record)
        first, second = [b.point(*p) for p in record['route_local_mm'][:2]]
        plane = cq.Plane(origin=first, normal=(second-first).normalized())
        shape = cq.Workplane(plane).circle(CABLE_DIAMETER_MM/2).sweep(
            cq.Workplane(obj=path), isFrenet=True).val()
        if record['string_connector_envelope']:
            first, last = [b.point(*p) for p in record['route_local_mm'][1:3]]
            direction, midpoint = (last-first).normalized(), (first+last)*.5
            connector = cq.Solid.makeCylinder(MEASURED_MAXIMUM_DIAMETER_MM/2,
                GEOMETRY['connector_length'],
                midpoint-direction*GEOMETRY['connector_length']/2, direction)
            shape = shape.fuse(connector).clean()
        result.append(previous.WiringPart(record['name'], shape, 'wire'))
    return tuple(result)
