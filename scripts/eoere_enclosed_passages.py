"""Reuse the historical centred round passages in the current bolted frame.

This bounded geometry study replaces the 32 current front-open cuts, preserves
all bolt/screw axes and LED endpoints, and checks the complete occupied bank.
It neither solves mechanics nor changes the selected revision automatically.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from itertools import combinations, pairwise
from pathlib import Path

from scripts.eoere_current_shop_followup import (
    ROOT,
    canonical,
    csv_bytes,
    encoded,
    module,
    require,
    sha,
)

DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
SHOP = DOC/'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1'
BASE = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/enclosed-passages-v1')
REVISION = 'eoere-centred-enclosed-passages-v1'


def build(out, diameter=38.1, f1_offset=40.):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT/BASE)
            and not out.exists(), 'fresh ignored output required')
    import cadquery as cq

    from mini_moonboard import round_structural_wiring as historical
    from scripts import hl35_nominal_service_candidate as service
    from scripts import thin_bolted_layout_revision as routing
    from scripts import thin_bolted_occupied as hardware

    pins = {}

    def pin(path, expected=None):
        path = str(path)
        actual = sha(path)
        require(expected is None or actual == expected, 'source differs: '+path)
        require(path not in pins or pins[path] == actual, 'source changed: '+path)
        pins[path] = actual
        return Path(path)

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def binding(path):
        return {'path': str(path), 'sha256': sha(path)}

    def bounds(shape):
        box = shape.BoundingBox()
        return [getattr(box, axis+end) for axis in 'xyz' for end in ('min', 'max')]

    def overlaps(a, b):
        return all(min(a[2*i+1], b[2*i+1])-max(a[2*i], b[2*i]) > 1e-7 for i in range(3))

    index = read('docs/bolted-frame-development/development-revisions.json')
    require(index['geometry']['revision'] == 'eoere-narrow-channel-openings-v1', 'current parent required')
    current = read(index['geometry']['receipt']['path'], index['geometry']['receipt']['sha256'])
    for path, digest in current['source_sha256'].items():
        pin(path, digest)
    parent = read(current['parent_geometry']['path'], current['parent_geometry']['sha256'])
    original = read(parent['parent_geometry']['path'], parent['parent_geometry']['sha256'])
    axes = [{**a, **parent['axis_overrides'].get(a['id'], {})} for a in original['axes']]
    require(len(axes) == 100 and len(original['screw_axes']) == 66, 'fixed axis census differs')
    measured = read('docs/round-service-wiring-reference.json')['user_measurements']
    require(diameter > measured['maximum_harness_outside_diameter_mm'], 'feeding clearance required')
    pin('mini_moonboard/round_structural_wiring.py')
    pin('docs/history/decision-log.md')
    pin('docs/history/round-floor-harness-verification.md')
    for name, loaded in tuple(sys.modules.items()):
        if name.startswith(('scripts.', 'mini_moonboard.')) and getattr(loaded, '__file__', None):
            pin(Path(loaded.__file__).resolve().relative_to(ROOT))
    pin(Path(__file__).relative_to(ROOT))
    out.mkdir(parents=True)
    (out/'producer-snapshot.py').write_bytes(Path(__file__).read_bytes())
    profiles = read(SHOP/'current_profiles.json')
    profiles.update(current['profile_overrides'])
    datums = list(csv.DictReader(io.StringIO(pin(current['shop_override']['path'], current['shop_override']['sha256']).read_text())))
    require(len(datums) == 32, '32 passages required')
    cache = {}

    def load(ref):
        path = str(pin(ref['path'], ref['sha256']))
        if path not in cache:
            cache[path] = cq.Shape.importBrep(path)
        return cache[path]

    changed, cables, restored, records, proofs, problems = {}, {}, {}, [], [], []
    solids = []

    def save_shape(name, kind, shape):
        path = out/(name+'.brep')
        require(shape.exportBrep(str(path)), 'BREP export failed')
        solids.append({'id': name, 'kind': kind, **binding(path), 'bytes': path.stat().st_size,
                       'bounds_xyz_mm': bounds(shape), 'volume_mm3': shape.Volume()})
    endpoints = {}
    for member in sorted({r['receiver'] for r in datums}):
        g = profiles[member]
        basis = [cq.Vector(*v) for v in g['basis_grain_u_v_xyz']]
        origin = cq.Vector(*g['datum_xyz_mm'])
        vertices = g['vertices_luv_mm']
        face = [v for v in vertices if abs(v[1]) < 1e-7]
        centre = [sum(v[i] for v in face)/len(face) for i in (0, 2)]
        face.sort(key=lambda v: math.atan2(v[2]-centre[1], v[0]-centre[0]))
        edge = cq.Wire.makePolygon([origin+basis[0]*v[0]+basis[2]*v[2] for v in face], close=True)
        width = max(v[1] for v in vertices)
        raw = cq.Solid.extrudeLinear(edge, [], basis[1]*width)
        old, new = raw, raw
        depth = max(v[2] for v in vertices)-min(v[2] for v in vertices)
        vcentre = (max(v[2] for v in vertices)+min(v[2] for v in vertices))/2
        require(abs(depth-139.7) < 1e-6, 'historical 2x6 depth requires review: '+member)
        own_holes = []
        for row in (r for r in datums if r['receiver'] == member):
            controls = json.loads(row['control_route_receiver_L_U_V_mm'])
            spans = [(a, b) for a, b in pairwise(controls) if abs(a[0]-b[0]) < 1e-7
                     and min(a[1], b[1]) <= 1e-7 and max(a[1], b[1]) >= width-1e-7]
            require(len(spans) == 1, 'one straight crossing required: '+row['service'])
            old_station = spans[0][0][0]
            grain_offset = f1_offset if row['service'] == 'wire_072_F1_G1' else 0.
            station = old_station+grain_offset
            placement = list(map(float, row['placement_xyz_mm'].split(';')))
            previous_route = json.loads(row['control_route_board_X_S_N_mm'])
            old_cut = routing.front_open_cutter(previous_route, placement, 6.35)
            slab = cq.Workplane(cq.Plane(origin=origin+basis[0]*old_station,
                                       xDir=basis[1], normal=basis[0])).box(10000, 10000, 14.).val()
            old = old.cut(old_cut.intersect(slab)).clean()
            start = origin+basis[0]*station+basis[2]*vcentre
            cutter = cq.Solid.makeCylinder(diameter/2, width+2, start-basis[1], basis[1])
            expected = math.pi*(diameter/2)**2*width
            lost = expected-raw.intersect(cutter).Volume()
            if abs(lost) > .01:
                problems.append({'duty': 'enclosed_round_section', 'member': member,
                                 'service': row['service'], 'missing_cylinder_volume_mm3': lost})
            new = new.cut(cutter).clean()
            own_holes.append(cutter)
            # The old routing method adapts ramps to the actual timber crossing.
            frame_origin = historical.b.point(0, 0, 0)+cq.Vector(*placement)
            sunit = historical.b.point(0, 1, 0)-historical.b.point(0, 0, 0)
            nunit = historical.b.point(0, 0, 1)-historical.b.point(0, 0, 0)
            relative_ends = [point-frame_origin for point in (start, start+basis[1]*width)]
            ends = [[point.x, point.dot(sunit), point.dot(nunit)] for point in relative_ends]
            first, last = previous_route[0], previous_route[-1]
            coordinate = 1 if abs(last[1]-first[1]) > abs(last[0]-first[0]) else 0
            sign = 1 if last[coordinate] > first[coordinate] else -1
            ends.sort(key=lambda p: sign*p[coordinate])
            near, far = [list(p) for p in ends]
            near[coordinate] -= sign*historical.CROSSING_LEAD_CLEARANCE_MM
            far[coordinate] += sign*historical.CROSSING_LEAD_CLEARANCE_MM
            route = [first, near, far, last]
            vectors = [cq.Vector(*v) for v in route]
            corners = list(historical.previous._corners(vectors))
            lengths = [(b-a).Length for a, b in pairwise(vectors)]
            cutbacks = [c[3] for c in corners]
            require(max(cutbacks) < historical.CROSSING_LEAD_CLEARANCE_MM
                    and lengths[0] > cutbacks[0] and lengths[2] > cutbacks[1]
                    and lengths[1] > sum(cutbacks), 'overlapping bend: '+row['service'])
            body, length = service.sweep(route, historical.CABLE_DIAMETER_MM/2, placement)
            require(body.isValid() and len(body.Solids()) == 1, 'invalid cable')
            if length > measured['approximate_bulb_base_pitch_mm']:
                problems.append({'duty': 'recorded_harness_budget', 'service': row['service'], 'route_length_mm': length})
            cables[row['service']] = body
            save_shape(row['service'], 'wire', body)
            for node, point in zip(row['service'].split('_')[2:], (route[0], route[-1]), strict=True):
                endpoints[node] = historical.b.point(*point)+cq.Vector(*placement)
            records.append({'member': member, 'service': row['service'], 'diameter_mm': diameter,
                            'old_channel_receiver_L_mm': old_station, 'grain_offset_mm': grain_offset,
                            'centre_receiver_L_U_V_mm': [station, width/2, vcentre],
                            'entry_xyz_mm': list(start.toTuple()), 'exit_xyz_mm': list((start+basis[1]*width).toTuple()),
                            'board_normal_centre_mm': ends[0][2], 'front_rear_ligament_mm': (depth-diameter)/2,
                            'through_wood_mm': width, 'route_board_X_S_N_mm': route, 'placement_xyz_mm': placement,
                            'route_length_mm': length, 'nominal_budget_remaining_mm': measured['approximate_bulb_base_pitch_mm']-length,
                            'Actual': '', 'Disposition': ''})
        own = [{**a, 'point': cq.Vector(*a['point_xyz_mm']), 'direction': cq.Vector(*a['direction_xyz'])}
               for a in axes if member in a['receivers']]
        for axis in own:
            bore = cq.Solid.makeCylinder(axis['bore_diameter_mm']/2, axis['grip_mm']+2,
                                        axis['point']-axis['direction'], axis['direction'])
            for cutter in own_holes:
                volume = raw.intersect(cutter).intersect(bore).Volume()
                if volume > 1e-6:
                    problems.append({'duty': 'bolt_bearing_intersection', 'member': member,
                                     'axis': axis['id'], 'intersection_mm3': volume})
        old = hardware.bore_wood({member: old}, own)[member]
        new = hardware.bore_wood({member: new}, own)[member]
        saved = load(g['finished'])
        error = old.cut(saved).Volume()+saved.cut(old).Volume()
        require(error < .01 and new.isValid() and len(new.Solids()) == 1, 'timber reconstruction differs: '+member)
        changed[member], restored[member] = new, new.cut(saved).clean()
        save_shape(member, 'timber', new)
        proofs.append({'member': member, 'old_reconstruction_error_mm3': error,
                       'passages': len(own_holes), 'unchanged_bolt_receivers': len(own),
                       'new_volume_mm3': new.Volume(), 'old_volume_mm3': saved.Volume()})
        print(member, len(own_holes), 'centred passages', flush=True)

    (out/'geometry-checkpoint.json').write_bytes(encoded({
        'passages': records, 'reconstruction_proofs': proofs, 'changed_finished_solids': solids,
        'problems_so_far': problems, 'occupied_part_check_complete': False,
        'producer_snapshot': binding(out/'producer-snapshot.py'), 'source_sha256': pins,
    }))

    shop = read(SHOP/'inputs.json')
    native_ref = shop['sources']['native']
    native = read(native_ref['path'], native_ref['sha256'])
    helper_ref = shop['sources']['bounds_helper']
    helper = module(pin(helper_ref['path'], helper_ref['sha256']), 'enclosed_passage_bounds')
    layers = []
    for filename in ('eoere-bottom-rail-scene.json.gz', 'eoere-cleat-trim-scene.json',
                     'eoere-aligned-wire-scene.json.gz', 'eoere-adjusted-base-v3-scene.json.gz',
                     'eoere-cleat-extension-scene.json.gz', 'eoere-uniform-channels-scene.json.gz',
                     'eoere-kicker-clearance-scene.json.gz', 'eoere-selected-hardware-scene.json.gz',
                     'eoere-front-posts-4x6-scene.json.gz', 'eoere-narrow-channels-scene.json.gz'):
        layer = helper.asset(str(pin('site/'+filename)))
        if filename == 'eoere-uniform-channels-scene.json.gz':
            layer = {'replacements': layer['common_replacements']+layer['base_replacements']}
        elif filename == 'eoere-narrow-channels-scene.json.gz':
            layer = {'replacements': layer['replacements']['base']}
        layers.append(layer)
    bank = helper.compose_bounds(native, layers)
    require(len(bank) == 1033, 'complete current occupied bank required')
    registry = {r['id']: r for r in native['parts']}
    for filename in ('occupied-aligned-wire-v1.json', 'occupied-adjusted-base-v3.json',
                     'occupied-uniform-channels-v1.json', 'occupied-kicker-clearance-v1.json',
                     'occupied-selected-hardware-v1.json', 'occupied-front-posts-4x6-v1.json'):
        registry.update({r['id']: r for r in read(DOC/filename)['changed_finished_solids']
                         if r.get('variant') in (None, 'base', 'common')})
    registry.update({name: g['finished'] for name, g in profiles.items()})
    require(all('fastener_'+a['axis_id'] in registry for a in original['screw_axes']),
            'complete current screw-solid registry required')
    queries, endpoint_contacts, backing = [], [], []
    for wire, body in cables.items():
        for name, part in bank.items():
            if name in cables or not overlaps(bounds(body), part['bounds']):
                continue
            obstacle = changed[name] if name in changed else load(registry[name])
            common = body.intersect(obstacle)
            volume = common.Volume()
            if volume > 1e-6:
                nodes = {name.removeprefix('light_')} if part['kind'] == 'light' else set(name.split('_')[2:]) if part['kind'] == 'wire' else set()
                shared = set(wire.split('_')[2:]) & nodes
                for node in shared:
                    common = common.cut(cq.Solid.makeSphere(10, endpoints[node], angleDegrees1=-90))
                if shared and common.Volume() < 1e-6:
                    endpoint_contacts.append({'wire': wire, 'other': name, 'nodes': sorted(shared)})
                else:
                    problems.append({'duty': 'cable_occupied_part', 'wire': wire, 'other': name,
                                     'intersection_mm3': volume, 'outside_endpoint_mm3': common.Volume()})
            queries.append({'wire': wire, 'other': name, 'intersection_mm3': volume})
        print(wire, 'occupied checks complete', flush=True)
    for (left, a), (right, b) in combinations(cables.items(), 2):
        if not overlaps(bounds(a), bounds(b)):
            continue
        common = a.intersect(b)
        for node in set(left.split('_')[2:]) & set(right.split('_')[2:]):
            common = common.cut(cq.Solid.makeSphere(10, endpoints[node], angleDegrees1=-90))
        if common.Volume() > 1e-6:
            problems.append({'duty': 'changed_cable_pair', 'left': left, 'right': right, 'intersection_mm3': common.Volume()})
    for member, added in restored.items():
        for name, part in bank.items():
            if name == member or name in cables or not overlaps(bounds(added), part['bounds']):
                continue
            obstacle = changed[name] if name in changed else load(registry[name])
            volume = added.intersect(obstacle).Volume()
            if volume > 1e-6:
                problems.append({'duty': 'restored_timber_occupied_part', 'member': member, 'other': name, 'intersection_mm3': volume})
        for screw in original['screw_axes']:
            if screw['receiver'] != member:
                continue
            body = load(registry['fastener_'+screw['axis_id']])
            before = load(profiles[member]['finished']).intersect(body).Volume()
            after = changed[member].intersect(body).Volume()
            backing.append({'member': member, 'screw': screw['axis_id'], 'old_backed_volume_mm3': before, 'new_backed_volume_mm3': after})
            if before-after > 1e-6:
                problems.append({'duty': 'lost_panel_screw_backing', **backing[-1]})
        print(member, 'restored material and screw backing checked', flush=True)
    (out/'passage-datums.csv').write_bytes(csv_bytes([
        {k: json.dumps(v) if isinstance(v, list) else v for k, v in row.items()} for row in records]))
    for path, digest in pins.items():
        require(sha(path) == digest, 'source changed during study: '+path)
    result = {'schema': 'eoere_enclosed_passages_geometry/v1', 'revision': REVISION,
              'parent_geometry': index['geometry'], 'parent_index_canonical_sha256': canonical(index),
              'source_sha256': pins, 'producer_snapshot': binding(out/'producer-snapshot.py'),
              'history_reused': ['mini_moonboard/round_structural_wiring.py', 'docs/history/decision-log.md',
                                 'docs/history/round-floor-harness-verification.md'],
              'status': 'NOMINAL_GEOMETRY_CLEAR' if not problems else 'REVISE_GEOMETRY',
              'passages': records, 'reconstruction_proofs': proofs, 'changed_finished_solids': solids,
              'occupied_part_count': len(bank), 'exact_cable_queries': queries,
              'intentional_endpoint_contacts': endpoint_contacts, 'panel_screw_backing': backing,
              'problems': problems, 'bolt_axis_lines_preserved': 100, 'Hillman_axes_preserved': 66,
              'old_front_open_notches': 32, 'new_front_open_notches': 0,
              'harness_cut_or_spliced': False, 'recorded_pitch_mm': measured['approximate_bulb_base_pitch_mm'],
              'physical_feed_verified': False, 'hole_strength_qualified': False,
              'new_response_computed': False, 'historical_capacity_transferred': False,
              'cadquery_version': cq.__version__, 'python_version': sys.version,
              'selected_revision_index_changed': False, 'release': current['release']}
    (out/'result.json').write_bytes(encoded(result))
    print(json.dumps({'status': result['status'], 'problems': problems,
                      'maximum_route_mm': max(r['route_length_mm'] for r in records),
                      'result': binding(out/'result.json')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--diameter', type=float, default=38.1)
    parser.add_argument('--f1-offset', type=float, default=40.)
    args = parser.parse_args()
    build(args.out, args.diameter, args.f1_offset)
