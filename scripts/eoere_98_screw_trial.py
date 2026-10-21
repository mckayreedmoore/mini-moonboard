"""Prepare the owner-requested 98-screw proposal on the current frame.

Reuse the corrected historical station rule, preserving all 66 existing axes.
Cached-solid checks are analysis geometry, not drilling or installation sizes.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

from scripts.eoere_current_shop_followup import ROOT, canonical, require, sha

DOC = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1')
HISTORY = Path('docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment')
RAW = Path('fea/generated/selected-hardware-followup-v1/panel98-current-v1')
INDEX = Path('docs/bolted-frame-development/development-revisions.json')
REVISION = 'eoere-current-panel98-proposal-v1'
PANELS = ('main_lower_left', 'main_lower_right', 'main_upper_left', 'main_upper_right')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def bounds(row):
    box = row['bounds_xyz_mm']
    return [v for interval in box for v in interval] if len(box) == 3 else list(box)


def parent_sources():
    pins = {}

    def read(path, expected=None):
        path = Path(path)
        digest = sha(ROOT/path)
        require(expected is None or digest == expected, 'changed source: '+str(path))
        require(pins.get(str(path), digest) == digest, 'conflicting source: '+str(path))
        pins[str(path)] = digest
        return json.loads((ROOT/path).read_bytes())

    index = read(INDEX)
    require(index['geometry']['revision'] in ('eoere-narrow-channel-openings-v1',
            'eoere-centred-enclosed-passages-v1'), 'current reviewed service geometry required')
    chain, node = [], index
    while node:
        record = read(node['geometry']['receipt']['path'], node['geometry']['receipt']['sha256'])
        chain.append((node, record))
        node = node.get('preceding_revision')
    current = chain[0][1]
    posts = next(record for node, record in chain if node['geometry']['revision'] == 'eoere-4x6-front-posts-v1')
    previous = next(node for node, _ in chain if node['current_response'] is not None)
    response = read(previous['current_response']['cases']['path'], previous['current_response']['cases']['sha256'])
    data = read(response['input']['path'], response['input']['sha256'])
    sources = {r['id']: {**copy.deepcopy(r['source']),
               'bounds_xyz_mm': copy.deepcopy(r['bounds_xyz_mm'])}
               for r in data['finished_body_observations']}
    for _, record in reversed(chain):
        sources.update({r['id']: copy.deepcopy(r) for r in record['changed_finished_solids']
                        if r['id'] in sources and r.get('variant') in (None, 'base', 'common')})
    for source in sources.values():
        require(sha(ROOT/source['path']) == source['sha256'], 'changed cached solid')
        pins[source['path']] = source['sha256']
    for path in (HISTORY/'count_layout.py', HISTORY/'count_mirrored_layout.py', Path(__file__).relative_to(ROOT)):
        pins[str(path)] = sha(ROOT/path)
    return index, current, posts, data, sources, pins


def proposed_axes(data, sources):
    """Adapt source metadata to the existing layout helper; no old force reuse."""
    original = {r['id']: r for r in data['hillman_rows']}
    connections = []
    for row in original.values():
        axis = row['source_screw_descriptor']
        connections.append({'kind': 'panel_screw', 'axis_id': row['id'],
            'source_point_xyz_mm': axis['origin_xyz_mm'], 'axis_xyz': axis['direction_xyz'],
            'receiver_member_ids': [row['first'], row['second']],
            'source_record': {'axis_id': row['id'], 'panel_member': row['first'],
                'receiver_member': row['second'], 'origin_global_xyz_mm': axis['origin_xyz_mm'],
                'axis_global_xyz': axis['direction_xyz'], 'purchased_nominal_length_mm': 63.5}})
    inputs = {'connections': connections, 'members': [
        {'member_id': name, 'graph_finished_geometry_summary': {'bounds_xyz_mm': bounds(row)}}
        for name, row in sources.items()]}
    module(HISTORY/'count_layout.py', 'count_layout')
    rule = module(HISTORY/'count_mirrored_layout.py', 'eoere_panel98_corrected_rule')
    layout = rule.build_layout(inputs)
    additions = []
    for row in layout['added_connections']:
        template = original[row['template_axis_id']]
        axis = copy.deepcopy(template['source_screw_descriptor'])
        axis.update(axis_id=row['axis_id'], origin_xyz_mm=row['source_point_xyz_mm'],
                    owner_authorized_development_trial=True, existing_axis=False,
                    installed=False, purchased=False)
        delta = [a-b for a, b in zip(axis['origin_xyz_mm'], template['source_screw_descriptor']['origin_xyz_mm'], strict=True)]
        mechanical = copy.deepcopy(template)
        mechanical.update(id=row['axis_id'], source_screw_descriptor=axis,
            point_xyz_mm=[a+b for a, b in zip(template['point_xyz_mm'], delta, strict=True)])
        additions.append({'axis': axis, 'mechanical': mechanical, 'template_axis_id': template['id'],
                          'edge_role': row['hypothetical_edge_role']})
    require(len(original) == 66 and len(additions) == 32, 'exact 66+32 axes required')
    require(len({r['axis']['axis_id'] for r in additions} | set(original)) == 98, 'duplicate axis')
    require(all(sum(r['axis']['panel'] == p for r in additions) == 8 for p in PANELS), 'eight additions per main panel required')
    return additions


def build(out):
    require(Path.cwd() == ROOT and out.resolve().is_relative_to(ROOT/RAW)
            and not out.exists(), 'fresh ignored proposal output required')
    index, _current, _posts, data, sources, pins = parent_sources()
    additions = proposed_axes(data, sources)
    out.mkdir(parents=True)
    (out/'producer-snapshot.py').write_bytes(Path(__file__).read_bytes())
    import cadquery as cq

    cache = {}

    def solid(name):
        if name not in cache:
            cache[name] = cq.Shape.importBrep(str(ROOT/sources[name]['path']))
        return cache[name]

    thickness = 18.25625
    checks, cutters = [], {p: [] for p in PANELS}
    for row in additions:
        axis = row['axis']
        origin, direction = cq.Vector(*axis['origin_xyz_mm']), cq.Vector(*axis['direction_xyz']).normalized()
        panel, receiver = axis['panel'], axis['receiver']
        # Reuse the existing 5-mm analysis envelope; this is not a pilot size.
        panel_probe = cq.Solid.makeCylinder(2.5, thickness-.1, origin+direction*.05, direction)
        receiver_probe = cq.Solid.makeCylinder(2.5, 63.5-thickness-.1, origin+direction*(thickness+.05), direction)
        fractions = [solid(panel).intersect(panel_probe).Volume()/panel_probe.Volume(),
                     solid(receiver).intersect(receiver_probe).Volume()/receiver_probe.Volume()]
        cutter = cq.Solid.makeCylinder(2.5, thickness+2., origin-direction, direction)
        cutters[panel].append(cutter)
        checks.append({'axis_id': axis['axis_id'], 'panel': panel, 'receiver': receiver,
            'panel_occupied_fraction': fractions[0], 'receiver_occupied_fraction': fractions[1],
            'nominal_full_backing': min(fractions) >= 1-1e-7,
            'clearance_diameter_is_analysis_only_mm': 5.})
    panel_sources = []
    if all(r['nominal_full_backing'] for r in checks):
        for name in PANELS:
            changed = solid(name).cut(*cutters[name])
            require(changed.isValid() and len(changed.Solids()) == 1, 'valid connected proposed panel required')
            path = out/(name+'.brep')
            changed.exportBrep(str(path))
            box = changed.BoundingBox()
            panel_sources.append({'id': name, 'kind': 'panel', 'path': str(path.relative_to(ROOT)),
                'sha256': sha(path), 'volume_mm3': changed.Volume(),
                'center_of_mass_xyz_mm': list(changed.Center().toTuple()),
                'bounds_xyz_mm': [getattr(box, a+b) for a in 'xyz' for b in ('min', 'max')],
                'new_clearance_axes': 8, 'existing_solid_replaced': False})
    result = {'schema': 'eoere_current_panel98_layout_preflight/v1', 'revision': REVISION,
        'parent_geometry': index['geometry']['receipt'], 'parent_revision': index['geometry']['revision'],
        'original_66_axis_sha256': canonical([r['source_screw_descriptor'] for r in data['hillman_rows']]),
        'original_axes_retained': True, 'original_main_screws_per_panel': 12,
        'proposed_main_screws_per_panel': 20, 'unchanged_kicker_screws': 18,
        'total_screws': 98, 'added_axes': additions, 'backing_checks': checks,
        'all_added_axes_fully_backed': all(r['nominal_full_backing'] for r in checks),
        'changed_panel_solids': panel_sources, 'cadquery_version': cq.__version__,
        'no_existing_axes_moved': True, 'frame_bolts_unchanged': 100,
        'primary_plywood_cleat_proposal_adopted': False, 'frame_response_computed': False,
        'structural_acceptance': False, 'fabrication_released': False, 'actual_observations': None,
        'source_sha256': pins, 'limits': ['Cached-solid backing only; complete obstacle, hole/edge and tool clearance require their own checks.',
            'Source-preserved 5-mm panel apertures and 63.5-mm length are analysis envelopes, not drilling instructions.',
            'No frame response, load-sharing improvement, product resistance or installed build is inferred.']}
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, 'source drift: '+path)
    (out/'layout.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = build(args.out.resolve())
    print(json.dumps({key: result[key] for key in ('revision', 'total_screws', 'all_added_axes_fully_backed', 'frame_response_computed')}))
