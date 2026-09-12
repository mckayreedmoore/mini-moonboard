"""Candidate wiring with 1.5-inch passages in nominal 2x6 stock only.

Routing and harness envelopes retain the preceding provisional assumptions.
Historical round-service wiring is not modified.
"""
import cadquery as cq

from . import round_service_wiring as previous

b = previous.b
REFERENCE, DATA = previous.REFERENCE, previous.DATA
MEASURED_MAXIMUM_DIAMETER_MM = previous.MEASURED_MAXIMUM_DIAMETER_MM
APPROXIMATE_PATH_BUDGET_MM = previous.APPROXIMATE_PATH_BUDGET_MM
GEOMETRY = previous.GEOMETRY
ROUTING_DEPTH_MM, BASE_DEPTH_MM = previous.ROUTING_DEPTH_MM, previous.BASE_DEPTH_MM
CABLE_DIAMETER_MM = previous.CABLE_DIAMETER_MM
CORNER_RADIUS_MM = previous.CORNER_RADIUS_MM
TWO_BY_SIX_BORE_DIAMETER_MM = 38.1
OTHER_STOCK_BORE_DIAMETER_MM = previous.BORE_DIAMETER_MM
LIMITS = ('38.1 mm enclosed passages in nominal 2x6 stock; 25.4 mm in other stock; '
          'routing, feeding access, residual timber sections and resistance unqualified')
segments, wire_path, parts = previous.segments, previous.wire_path, previous.parts
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
                'length_mm': length, 'diameter_mm': bore_diameter_mm(part),
                'axis_local': 'S' if vertical else 'X',
                'center_x_mm': a[0] if vertical else (low+high)/2,
                'center_s_mm': (low+high)/2 if vertical else a[1], 'center_n_mm': ROUTING_DEPTH_MM,
                'member_entry_mm': low, 'member_exit_mm': high, 'datums': segment['datums'],
                'entry_face': 'timber side face; enclosed round passage', 'qualified_for_machining': False}
            if part.shape.intersect(bore_shape(record)).Volume() > 1e-5:
                result.append(record)
    return tuple(result)
