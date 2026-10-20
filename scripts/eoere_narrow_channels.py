"""Narrow the existing 32 front openings, preserving depth and every service path."""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import io
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

from scripts.eoere_current_shop_followup import csv_bytes, module
from scripts.eoere_selected_hardware import ROOT, canonical, encoded, require, sha

DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
SHOP = DOC/'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1'
REVISION = 'eoere-narrow-channel-openings-v1'
REPORT = DOC/'occupied-narrow-channels-v1.json'
BASE = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/narrow-channels-v1')
WIDTH = 14.
KEYS = {'base': 'eoere-narrow-channels-frame-development', 'extra': 'eoere-narrow-channels-grid-development'}


def build(out):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT/BASE) and not out.exists(), 'fresh ignored output required')
    import cadquery as cq

    from scripts import thin_bolted_layout_revision as routing
    from scripts import thin_bolted_occupied as hardware
    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    pins = {}

    def pin(path, digest=None):
        path = str(path)
        actual = sha(path)
        require(digest is None or actual == digest, 'source changed: '+path)
        require(path not in pins or pins[path] == actual, 'conflicting source: '+path)
        pins[path] = actual
        return Path(path)

    def read(path):
        return json.loads(pin(path).read_bytes())

    def binding(path):
        return {'path': str(path), 'sha256': sha(path)}

    def bounds(shape):
        b = shape.BoundingBox()
        return [getattr(b, a+end) for a in 'xyz' for end in ('min', 'max')]

    previous = json.loads((ROOT/'docs/bolted-frame-development/development-revisions.json').read_bytes())
    if previous['schema'] == 'bolted_frame_development_revisions/v3':
        previous = previous['preceding_revision']
    require(previous['geometry']['revision'] == 'eoere-4x6-front-posts-v1', '4x6-post parent required')
    parent = read(previous['geometry']['receipt']['path'])
    require(sha(previous['geometry']['receipt']['path']) == previous['geometry']['receipt']['sha256'], 'post receipt changed')
    for p, digest in parent['source_sha256'].items():
        pin(p, digest)
    for name, loaded in tuple(sys.modules.items()):
        if name.startswith(('scripts.', 'mini_moonboard.')) and getattr(loaded, '__file__', None):
            pin(Path(loaded.__file__).resolve().relative_to(ROOT))
    pin(Path(__file__).relative_to(ROOT))
    out.mkdir(parents=True)
    (out/'producer-snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'parent-index.json').write_bytes(encoded(previous))
    profiles = read(SHOP/'current_profiles.json')
    profiles.update(parent['profile_overrides'])
    datums = list(csv.DictReader(io.StringIO(pin(SHOP/'service-channel-datums.csv').read_text())))
    require(len(datums) == 32, '32 base-grid channels required')
    measured = read('docs/round-service-wiring-reference.json')['user_measurements']
    require(measured['maximum_harness_outside_diameter_mm'] == 12.7 and WIDTH > 12.7, 'recorded harness envelope required')
    geometry = read(parent['parent_geometry']['path'])
    axes = [{**a, **parent['axis_overrides'].get(a['id'], {})} for a in geometry['axes']]
    cache = {}

    def load(ref):
        p = str(pin(ref['path'], ref['sha256']))
        if p not in cache:
            cache[p] = cq.Shape.importBrep(p)
        return cache[p]

    changed, additions, proofs, replacements = {}, {}, [], {'base': [], 'extra': []}
    for name in sorted({r['receiver'] for r in datums}):
        g = profiles[name]
        basis = [cq.Vector(*v) for v in g['basis_grain_u_v_xyz']]
        origin = cq.Vector(*g['datum_xyz_mm'])
        points = [v for v in g['vertices_luv_mm'] if abs(v[1]) < 1e-7]
        center = [sum(v[i] for v in points)/len(points) for i in (0, 2)]
        points.sort(key=lambda v: math.atan2(v[2]-center[1], v[0]-center[0]))
        wire = cq.Wire.makePolygon([origin+basis[0]*v[0]+basis[2]*v[2] for v in points], close=True)
        width = max(v[1] for v in g['vertices_luv_mm'])
        raw = cq.Solid.extrudeLinear(wire, [], basis[1]*width)
        old, new = raw, raw
        own_rows = [r for r in datums if r['receiver'] == name]
        for row in own_rows:
            local = json.loads(row['control_route_receiver_L_U_V_mm'])
            spans = [(a, b) for a, b in pairwise(local) if abs(a[0]-b[0]) < 1e-7
                     and min(a[1], b[1]) <= 1e-7 and max(a[1], b[1]) >= width-1e-7]
            require(len(spans) == 1, 'one straight full-thickness channel required: '+name+'/'+row['service'])
            station = spans[0][0][0]
            cutter = routing.front_open_cutter(json.loads(row['control_route_board_X_S_N_mm']),
                                              list(map(float, row['placement_xyz_mm'].split(';'))), 6.35)
            slab = cq.Workplane(cq.Plane(origin=origin+basis[0]*station, xDir=basis[1], normal=basis[0])).box(10000, 10000, WIDTH).val()
            smaller = cutter.intersect(slab)
            old = old.cut(cutter).clean()
            new = new.cut(smaller).clean()
            row.update(front_opening_mm=str(WIDTH), interpretation='Existing swept profile clipped to a 14-mm grain-direction band; rear cap/depth and route unchanged. Nominal geometry, not bit or tolerance instructions.')
        own = [{**a, 'point': cq.Vector(*a['point_xyz_mm']), 'direction': cq.Vector(*a['direction_xyz'])}
               for a in axes if name in a['receivers']]
        old = hardware.bore_wood({name: old}, own)[name]
        new = hardware.bore_wood({name: new}, own)[name]
        saved = load(g['finished'])
        error = old.cut(saved).Volume()+saved.cut(old).Volume()
        require(error < .01, f'old reconstruction differs: {name}/{error}')
        require(new.isValid() and len(new.Solids()) == 1 and saved.cut(new).Volume() < .01, 'old timber removed: '+name)
        added = new.cut(saved).clean()
        require(added.Volume() > 0, 'no size reduction: '+name)
        changed[name], additions[name] = new, added
        proofs.append({'member': name, 'channels': len(own_rows), 'unchanged_bores': len(own),
                       'old_reconstruction_difference_mm3': error, 'restored_volume_mm3': added.Volume()})
        print(name, 'restored', round(added.Volume(), 3), 'mm3', flush=True)

    # Compose the existing complete part banks, then test only the added timber.
    shop = read(SHOP/'inputs.json')
    native = read(shop['sources']['native']['path'])
    helper_ref = shop['sources']['bounds_helper']
    pin(helper_ref['path'], helper_ref['sha256'])
    helper = module(helper_ref['path'], 'narrow_channel_bounds')
    reports = {name: read(DOC/(name+'.json')) for name in ('occupied-aligned-wire-v1', 'occupied-adjusted-base-v3',
               'occupied-2026-adjustments-v3', 'occupied-uniform-channels-v1', 'occupied-kicker-clearance-v1', 'occupied-right-column-v1', 'occupied-selected-hardware-v1')}
    prefix = [helper.asset(str(pin('site/'+name))) for name in ('eoere-bottom-rail-scene.json.gz', 'eoere-cleat-trim-scene.json',
              'eoere-aligned-wire-scene.json.gz', 'eoere-adjusted-base-v3-scene.json.gz', 'eoere-cleat-extension-scene.json.gz')]
    uniform = helper.asset(str(pin('site/eoere-uniform-channels-scene.json.gz')))
    suffix = [helper.asset(str(pin('site/'+name))) for name in ('eoere-kicker-clearance-scene.json.gz', 'eoere-selected-hardware-scene.json.gz', 'eoere-front-posts-4x6-scene.json.gz')]
    saved_rows, comparisons, profile_overrides = [], {}, {}
    for variant, total in (('base', 1033), ('extra', 1428)):
        layers = prefix+[{'replacements': uniform['common_replacements']+uniform[variant+'_replacements']}]+suffix
        if variant == 'extra':
            layers.insert(len(prefix)-1, helper.asset(str(pin('site/eoere-2026-adjustments-v3-scene.json.gz'))))
            layers.insert(-2, helper.asset(str(pin('site/eoere-right-column-scene.json.gz'))))
        bank = helper.compose_bounds(native, layers)
        require(len(bank) == total, 'complete part census differs')
        registry = {r['id']: r for r in native['parts']}
        for label in ('occupied-aligned-wire-v1', 'occupied-adjusted-base-v3', 'occupied-2026-adjustments-v3', 'occupied-uniform-channels-v1',
                      'occupied-kicker-clearance-v1', 'occupied-right-column-v1', 'occupied-selected-hardware-v1'):
            if label in ('occupied-right-column-v1', 'occupied-2026-adjustments-v3') and variant == 'base':
                continue
            registry.update({r['id']: r for r in reports[label]['changed_finished_solids'] if r.get('variant') in (None, variant, 'common')})
        registry.update({r['id']: r for r in parent['changed_finished_solids']})
        if variant == 'base':
            registry.update({n: g['finished'] for n, g in profiles.items()})
        queries = []
        for name, base_shape in changed.items():
            old = load(registry[name])
            new = base_shape if variant == 'base' else old.fuse(additions[name]).clean()
            added = new.cut(old).clean()
            require(new.isValid() and len(new.Solids()) == 1 and old.cut(new).Volume() < .01, 'invalid narrowed timber')
            bb = bounds(added)
            for other, part in bank.items():
                if other == name or not all(min(bb[2*i+1], part['bounds'][2*i+1])-max(bb[2*i], part['bounds'][2*i]) > 1e-7 for i in range(3)):
                    continue
                volume = added.intersect(load(registry[other])).Volume()
                queries.append({'member': name, 'other': other, 'kind': part['kind'], 'intersection_mm3': volume})
                require(volume < 1e-6, f'added timber collision: {variant}/{name}/{other}/{volume}')
            folder = out/variant
            folder.mkdir(exist_ok=True)
            path = folder/(name+'.brep')
            require(new.exportBrep(str(path)), 'BREP export failed')
            rec = {'id': name, 'kind': 'timber', 'variant': variant, **binding(path), 'bytes': path.stat().st_size,
                   'bounds_xyz_mm': bounds(new), 'volume_mm3': new.Volume(), 'restored_volume_mm3': added.Volume()}
            saved_rows.append(rec)
            replacements[variant].append({'id': name, 'name': name, 'mesh': _shape_mesh(new),
                'fabrication': {'kind': 'timber', 'narrow_channel_revision': REVISION,
                'description': '14-mm front openings; original rounded cap, N14.35 depth, routes and bores retained'}})
            if variant == 'base':
                profile_overrides[name] = {**copy.deepcopy(profiles[name]), 'finished': rec}
        comparisons[variant] = {'parts': total, 'added_material_pair_comparisons': 8*(total-1), 'exact_queries': queries, 'all_clear': True}
    (out/'service-channel-datums.csv').write_bytes(csv_bytes(datums))
    for path, digest in pins.items():
        require(sha(path) == digest, 'source changed during run: '+path)
    result = {'schema': 'eoere_narrow_channels_geometry/v1', 'revision': REVISION, 'candidate': parent['candidate'],
        'parent_geometry': previous['geometry']['receipt'], 'parent_index_canonical_sha256': canonical(previous),
        'source_sha256': pins, 'producer_snapshot': binding(out/'producer-snapshot.py'),
        'profile': {'old_front_width_mm': 2*math.hypot(8, 6.35), 'front_width_mm': WIDTH, 'rear_depth_mm': 14.35,
                    'rounded_cap_radius_mm': 6.35, 'channel_center_N_mm': 8., 'maximum_recorded_harness_diameter_mm': 12.7,
                    'actual_fit_or_tolerance_verified': False}, 'channel_count': 32, 'changed_finished_solids': saved_rows,
        'profile_overrides': profile_overrides, 'reconstruction_proofs': proofs, 'clearance': comparisons,
        'shop_override': binding(out/'service-channel-datums.csv'), 'unchanged_bolt_axis_lines': 100, 'unchanged_screw_axes': 66,
        'service_routes_changed': False, 'new_response_computed': False, 'analysis_pass_transferred': False,
        'central_notch_location_holds': 6, 'release': parent['release']}
    (out/'geometry.json').write_bytes(encoded(result))
    patch = {'schema': 'eoere_narrow_channels_patch/v1', 'revision': REVISION, 'keys': KEYS,
        'layout_report': {'path': str(REPORT), 'sha256': sha(out/'geometry.json')},
        'parent_scene': previous['geometry']['scene'], 'parent_layout': previous['geometry']['receipt'],
        'profile': result['profile'], 'counts': {'base': 1033, 'extra': 1428},
        'replacements': replacements, 'analysis_pass_transferred': False, 'release': parent['release']}
    patch['triangle_topologies'] = _deduplicate_triangle_topologies(replacements['base']+replacements['extra'])
    blob = json.dumps(patch, separators=(',', ':'), allow_nan=False).encode()
    (out/'scene.json.gz').write_bytes(gzip.compress(blob, mtime=0))
    print(json.dumps({'receipt': binding(out/'geometry.json'), 'scene': binding(out/'scene.json.gz')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    build(parser.parse_args().out)
