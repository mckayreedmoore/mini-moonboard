"""Bounded A34/SD9112 base-angle axis study; no current assembly replacement."""
import argparse
import itertools
import json
from pathlib import Path

import cadquery as cq

from fea.panel_screw_sensitivity import digest
from mini_moonboard.connection_geometry import material_intervals

DATA = Path('docs/a34-base-cad-data.json')


def patterns(data):
    """Preserve both inconsistent manufacturer drawing families and mounting choices."""
    sources = data['sources']
    families = (
        ('dxf', sources['front_dxf']['thickness'], sources['front_dxf']['flange_reach'],
         sources['top_dxf']['hole_centers_width_reach'], sources['front_dxf']['hole_centers_width_reach']),
        ('sat', sources['sat']['thickness'], max(sources['sat']['flange_reaches']),
         sources['sat']['through_y_leg_width_z_reach_x'], sources['sat']['through_x_leg_width_z_reach_minus_y']),
    )
    for family, thickness, reach, beam, upright in families:
        for swapped, width_sign in itertools.product((False, True), (-1., 1.)):
            yield {'name': f'{family}-swap{int(swapped)}-width{int(width_sign)}',
                   'family': family, 'thickness_mm': thickness*25.4, 'reach_mm': reach*25.4,
                   'width_mm': 63.5, 'width_sign': width_sign,
                   'beam': upright if swapped else beam, 'upright': beam if swapped else upright}


def candidate_axes(station, pattern):
    name, origin, u, v, beam, upright = station
    w = u.cross(v)
    rows = []
    for flange, receiver, face, along in (('beam', beam, v, u), ('upright', upright, u, v)):
        for index, (width, reach) in enumerate(pattern[flange], 1):
            start = origin+w*(width*25.4*pattern['width_sign'])+along*(reach*25.4)+face*pattern['thickness_mm']
            rows.append({'name': f'{name}_{flange}_{index}', 'receiver': receiver,
                         'start': start, 'direction': -face, 'flange': flange})
    return rows


def build():
    from mini_moonboard import round_insert_frame as model

    data = json.loads(DATA.read_text())
    sources = {str(DATA): digest(DATA), str(Path(__file__).resolve().relative_to(Path.cwd())): digest(__file__)}
    # Consumers may be extended while the independent fit study runs. Only the
    # existing insert model's geometry producer closure is authenticated here.
    for path in Path('mini_moonboard').glob('*.py'):
        if not path.name.endswith(('_exports.py', '_drilling.py')):
            sources[str(path)] = digest(path)
    raw = {p.name: p for p in model.wood_parts()}
    stations = [s for s in model.stations() if s[0].startswith('clip_angle_base_')]
    if len(stations) != 2:
        raise ValueError('Require the two existing outer base angles')
    retained = [c for c in model.connections() if not c.name.startswith('clip_angle_base_')]
    dimensions = data['sd9112']['precision_dimensions_p33']
    length, diameter = dimensions['length']*25.4, dimensions['major_diameter']*25.4
    variants = []
    for pattern in patterns(data):
        rows = []
        axes = [row for station in stations for row in candidate_axes(station, pattern)]
        for row in axes:
            start, direction = row['start'], row['direction']
            receiver = raw[row['receiver']]
            spans = material_intervals(receiver.shape, start, direction, 0., length)
            expected = [pattern['thickness_mm'], length]
            continuous = (len(spans) == 1 and abs(spans[0][0]-expected[0]) < 1.e-5
                          and abs(spans[0][1]-expected[1]) < 1.e-5)
            # The major-diameter shaft is a conservative solid envelope for
            # thread occupancy. It is not a pilot, head, or bend geometry.
            embedded = cq.Solid.makeCylinder(diameter/2, length-pattern['thickness_mm']-1.e-4,
                                            start+direction*(pattern['thickness_mm']+1.e-4), direction)
            outside = embedded.cut(receiver.shape).Volume()
            line = cq.Edge.makeLine(start, start+direction*length)
            nearby = [c for c in retained if row['receiver'] in c.members]
            separations = [(line.distance(cq.Edge.makeLine(c.start, c.start+c.direction*c.length))
                            -(diameter+c.diameter)/2, c.name) for c in nearby]
            # A negative value detects a cylinder-envelope clash; a positive
            # value does not cover heads, insert bodies, driver access or clips.
            nearest = min(separations) if separations else (None, None)
            records = {'name': row['name'], 'receiver': row['receiver'], 'flange': row['flange'],
                       'start_xyz_mm': list(start.toTuple()), 'direction_xyz': list(direction.toTuple()),
                       'specified_product': 'SD9112', 'underhead_length_mm': length,
                       'major_diameter_mm': diameter, 'raw_receiver_intervals_mm': spans,
                       'continuous_nominal_penetration': continuous,
                       'gross_penetration_mm': length-pattern['thickness_mm'],
                       'shaft_outside_receiver_volume_mm3': outside,
                       'shaft_receiver_fit': continuous and outside < 1.e-3,
                       'nearest_retained_shaft_envelope_gap_mm': nearest[0],
                       'nearest_retained_connection': nearest[1],
                       'qualified_for_installation': False}
            rows.append(records)
        cross = []
        for a, z in itertools.combinations(axes, 2):
            if a['receiver'] != z['receiver']:
                continue
            gap = cq.Edge.makeLine(a['start'], a['start']+a['direction']*length).distance(
                cq.Edge.makeLine(z['start'], z['start']+z['direction']*length))-diameter
            cross.append({'connections': [a['name'], z['name']], 'shaft_envelope_gap_mm': gap})
        variants.append({'pattern': {key: value for key, value in pattern.items() if key not in ('beam', 'upright')},
                         'screws': rows, 'candidate_shaft_pairs': cross,
                         'all_16_receiver_axes_and_shaft_envelopes_fit': all(r['shaft_receiver_fit'] for r in rows),
                         'minimum_retained_shaft_gap_mm': min(r['nearest_retained_shaft_envelope_gap_mm'] for r in rows),
                         'minimum_candidate_shaft_gap_mm': min(r['shaft_envelope_gap_mm'] for r in cross),
                         'qualified_for_design': False})
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError('A34 fit source changed during study')
    return {'existing_candidate': model.KEY, 'proposed_change_applied': False,
            'study': 'One A34 with eight SD9112 screws in place of each of two outer ML24Z angles',
            'manufacturer_cad_disagreements': data['disagreements'], 'variants': variants,
            'source_sha256': sources, 'qualified_for_design': False,
            'sloped_grain_installation_qualified': False,
            'limits': 'Two conflicting US manufacturer CAD families; neither assigned to actual purchased A34. '
                      'Mirrored width/flange choices are fit probes, not approved installation variants. '
                      'Centerline/material and major-diameter shaft tests only; full embossed bracket, '
                      'head height/profile, retained insert bodies/heads, driver access, edge/end capacity, '
                      'grain applicability, full wrench resistance and load redistribution remain unqualified. '
                      'No current geometry changed; no old ML bores treated as repaired stock.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(build(), stream, indent=2, allow_nan=False)
        stream.write('\n')
