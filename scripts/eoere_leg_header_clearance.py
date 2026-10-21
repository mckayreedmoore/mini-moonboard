"""Check the combined revision against the composed occupied-part registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.eoere_current_shop_followup import ROOT, module, require, sha
from scripts.eoere_leg_header_revision import DOC


def check(geometry_path, out):
    import cadquery as cq

    require(not out.exists(), 'fresh clearance receipt required')
    pins, bodies = {}, {}

    def read(path, expected=None):
        path = Path(path)
        digest = sha(path)
        require(expected is None or expected == digest, 'source differs: '+str(path))
        pins[str(path)] = digest
        return json.loads(path.read_bytes())

    def load(row):
        path = row['path']
        require(sha(path) == row['sha256'], 'solid differs: '+path)
        pins[path] = row['sha256']
        if path not in bodies:
            bodies[path] = cq.Shape.importBrep(path)
        return bodies[path]

    def bounds(body):
        bb = body.BoundingBox()
        return [getattr(bb, a+b) for a in 'xyz' for b in ('min', 'max')]

    def overlaps(a, b):
        return all(min(a[2*i+1], b[2*i+1])-max(a[2*i], b[2*i]) > 1e-7 for i in range(3))

    geometry = read(geometry_path)
    parent = read(geometry['parent_geometry']['receipt']['path'], geometry['parent_geometry']['receipt']['sha256'])
    shop = read(DOC/'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/inputs.json')
    native = read(shop['sources']['native']['path'], shop['sources']['native']['sha256'])
    ref = shop['sources']['bounds_helper']
    require(sha(ref['path']) == ref['sha256'], 'bounds helper differs')
    pins[ref['path']] = ref['sha256']
    helper = module(Path(ref['path']), 'combined_revision_bounds')
    registry = {r['id']: r for r in native['parts']}
    layers = []
    for filename in ('eoere-bottom-rail-scene.json.gz', 'eoere-cleat-trim-scene.json',
                     'eoere-aligned-wire-scene.json.gz', 'eoere-adjusted-base-v3-scene.json.gz',
                     'eoere-cleat-extension-scene.json.gz', 'eoere-uniform-channels-scene.json.gz',
                     'eoere-kicker-clearance-scene.json.gz', 'eoere-selected-hardware-scene.json.gz',
                     'eoere-front-posts-4x6-scene.json.gz', 'eoere-narrow-channels-scene.json.gz',
                     'eoere-enclosed-passages-scene.json.gz'):
        path = Path('site')/filename
        pins[str(path)] = sha(path)
        layer = helper.asset(str(path))
        ref = layer['layout_report']
        report = read(ref['path'], ref['sha256'])
        for key in ('finished_solids', 'finished_panel_solids', 'changed_finished_solids'):
            registry.update({r['id']: r for r in report.get(key, []) if r.get('variant') in (None, 'base', 'common')})
        if filename == 'eoere-uniform-channels-scene.json.gz':
            layer = {'replacements': layer['common_replacements']+layer['base_replacements']}
        elif filename == 'eoere-narrow-channels-scene.json.gz':
            layer = {'replacements': layer['replacements']['base']}
        layers.append(layer)
        if filename == 'eoere-selected-hardware-scene.json.gz':
            interim = helper.compose_bounds(native, layers)
            translated = []
            for move in layer['translations']:
                previous, delta = interim[move['name']]['bounds'], move['translation_xyz_mm']
                translated.append({'name': move['name'], 'fabrication': move['fabrication'],
                                   'mesh': {'bounds_xyz_mm': [value+delta[i//2] for i, value in enumerate(previous)]}})
            layers.append({'replacements': translated})
    bank = helper.compose_bounds(native, layers)
    require(len(bank) == 1033, 'authenticated parent occupied census required')
    registry.update({name: g['finished'] for name, g in geometry['profiles'].items()})
    registry.update({r['id']: r for r in parent['changed_finished_solids']})
    moved = {}
    bottom = read(DOC/'occupied-bottom-rail-v1.json')
    for change in bottom['changes']['Hillman_axes_moved']:
        name = 'fastener_'+change['axis_id']
        delta = [b-a for a, b in zip(change['before_xyz_mm'], change['after_xyz_mm'], strict=True)]
        moved[name] = load(registry[name]).translate(cq.Vector(*delta))
    revised = {r['axis_id'] for r in geometry['selected_stack_overrides']}
    replaced_prefixes = tuple(i+'_' for i in revised | set(geometry['removed_axes']))
    removed_parts = sorted(name for name in bank if name.startswith(replaced_prefixes))
    for name in removed_parts:
        del bank[name]
    changed = {r['id']: r for r in geometry['changed_finished_solids']}
    registry.update(changed)
    for name, row in changed.items():
        bank[name] = {'kind': row['kind'], 'bounds': row['bounds_xyz_mm']}
    screw_hosts = {'fastener_'+r['axis_id']: {r['panel'], r['receiver']} for r in geometry['screw_axes']}
    from scripts import eoere_bolted_candidate as angles
    pins[str(Path(angles.__file__).relative_to(ROOT))] = sha(angles.__file__)
    template = angles.template(angles.Scenario())
    receivers = {(a['angle_id'], a['flange']): a['receiver'] for axis in geometry['axes'] for a in axis['attachments']}
    fitted = {r['id']: angles.pose({**r, 'beam': receivers[(r['id'], 'beam')],
                                  'post': receivers[(r['id'], 'post')]}, template).shape for r in geometry['fitting_poses']}
    for name, body in fitted.items():
        require(max(abs(a-b) for a, b in zip(bounds(body), bank[name]['bounds'], strict=True)) < 1e-5,
                'factory fitting reconstruction bounds differ: '+name)
    axis_names = {name: axis['id'] for axis in geometry['axes'] for name in bank if name.startswith(axis['id']+'_')}
    rows, missing, collisions, intended, seen = [], [], [], [], set()
    for first in sorted(changed):
        own = load(changed[first])
        for second, other in bank.items():
            key = tuple(sorted((first, second)))
            if first == second or key in seen or not overlaps(bounds(own), other['bounds']):
                continue
            seen.add(key)
            if first in axis_names and axis_names.get(first) == axis_names.get(second):
                continue  # Intended shaft/head/washer/nut overlap within one stack.
            if first in screw_hosts.get(second, set()) or second in screw_hosts.get(first, set()):
                intended.append({'first': first, 'second': second, 'reason': 'declared screw receiver engagement'})
                continue
            if second not in registry and second not in fitted:
                missing.append({'first': first, 'second': second, 'kind': other['kind']})
                continue
            other_body = moved[second] if second in moved else fitted[second] if second in fitted else load(registry[second])
            volume = own.intersect(other_body).Volume()
            row = {'first': first, 'second': second, 'intersection_mm3': volume}
            rows.append(row)
            if volume > .001:
                collisions.append(row)
    pins[str(Path(__file__).relative_to(ROOT))] = sha(__file__)
    for path, digest in pins.items():
        require(sha(path) == digest, 'source changed during clearance: '+path)
    result = {'schema': 'eoere_leg_header_occupied_clearance/v1',
              'geometry': {'path': str(geometry_path.relative_to(ROOT)), 'sha256': sha(geometry_path)},
              'occupied_part_count': len(bank), 'changed_parts': len(changed), 'removed_parent_parts': removed_parts,
              'exact_queries': rows, 'intentional_screw_engagements': intended, 'missing_candidates': missing,
              'collisions': collisions, 'nominal_geometry_clear': not collisions and not missing,
              'source_sha256': pins, 'actual_tools_or_hardware_verified': False,
              'strength_qualified': False, 'release': False}
    with out.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('occupied_part_count', 'changed_parts', 'nominal_geometry_clear', 'collisions', 'missing_candidates')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geometry', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    check(args.geometry.resolve(), args.out.resolve())
