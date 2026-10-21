"""Publish a checked enclosed-passage geometry without transferring strength."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from scripts.eoere_current_shop_followup import ROOT, canonical, encoded, require, sha


def publish(study):
    import cadquery as cq

    from scripts.export_wood_joint_wj24_scene import (
        _deduplicate_triangle_topologies,
        _shape_mesh,
    )

    index_path = Path('docs/bolted-frame-development/development-revisions.json')
    index_bytes = index_path.read_bytes()
    parent = json.loads(index_bytes)
    raw_path = study/'result.json'
    raw = json.loads(raw_path.read_bytes())
    require(parent['geometry'] == raw['parent_geometry']
            and canonical(parent) == raw['parent_index_canonical_sha256'], 'parent revision differs')
    require(raw['status'] == 'NOMINAL_GEOMETRY_CLEAR' and not raw['problems'], 'clear checked geometry required')
    for name, digest in raw['source_sha256'].items():
        require(sha(name) == digest, 'study source changed: '+name)
    frozen_index = study/'parent-index.json'
    require(not frozen_index.exists(), 'fresh publication required')
    frozen_index.write_bytes(index_bytes)

    def bound(path):
        return {'path': str(path), 'sha256': sha(path)}

    folder = Path(parent['geometry']['receipt']['path']).parent/'enclosed-passages-v1'
    folder.mkdir(exist_ok=True)
    datums = folder/'passage-datums.csv'
    datums.write_bytes((study/'passage-datums.csv').read_bytes())
    previous = json.loads(Path(parent['geometry']['receipt']['path']).read_bytes())
    timber = {r['id']: r for r in raw['changed_finished_solids'] if r['kind'] == 'timber'}
    profiles = {name: {**g, 'finished': timber[name]} for name, g in previous['profile_overrides'].items()}
    report = {key: raw[key] for key in ('schema', 'revision', 'status', 'passages', 'reconstruction_proofs',
              'changed_finished_solids', 'bolt_axis_lines_preserved', 'Hillman_axes_preserved',
              'old_front_open_notches', 'new_front_open_notches', 'harness_cut_or_spliced',
              'recorded_pitch_mm', 'physical_feed_verified', 'hole_strength_qualified',
              'new_response_computed', 'historical_capacity_transferred', 'release')}
    report.update(schema='eoere_enclosed_passages_revision/v1', candidate=parent['evidence_candidate'],
                  parent_geometry=parent['geometry'], parent_index_canonical_sha256=canonical(parent),
                  frozen_parent_index=bound(frozen_index), checked_study=bound(raw_path),
                  profile_overrides=profiles, shop_override=bound(datums),
                  source_sha256={str(p): sha(p) for p in (Path(__file__).relative_to(ROOT),
                      raw_path, frozen_index, datums, Path(parent['geometry']['receipt']['path']))})
    report_path = folder/'geometry.json'
    report_path.write_bytes(encoded(report))
    replacements = []
    for row in raw['changed_finished_solids']:
        require(sha(row['path']) == row['sha256'], 'checked solid differs: '+row['id'])
        shape = cq.Shape.importBrep(row['path'])
        replacements.append({'id': row['id'], 'name': row['id'], 'mesh': _shape_mesh(shape),
                             'fabrication': {'kind': row['kind'], 'enclosed_passage_revision': raw['revision'],
                                             'description': 'Centred enclosed LED passages; nominal geometry, resistance unqualified'}})
    patch = {'schema': 'eoere_enclosed_passages_patch/v1', 'revision': raw['revision'],
             'key': 'eoere-enclosed-passages-frame-development', 'parent_scene': parent['geometry']['scene'],
             'parent_layout': parent['geometry']['receipt'], 'layout_report': bound(report_path),
             'part_count': 1033, 'replacements': replacements, 'new_response_computed': False,
             'historical_capacity_transferred': False, 'release': raw['release']}
    patch['triangle_topologies'] = _deduplicate_triangle_topologies(replacements)
    decoded = json.dumps(patch, separators=(',', ':'), allow_nan=False).encode()
    scene = Path('site/eoere-enclosed-passages-scene.json.gz')
    scene.write_bytes(gzip.compress(decoded, mtime=0))
    current = copy.deepcopy(parent)
    current.update(schema='bolted_frame_development_revisions/v4', preceding_revision=parent)
    current['geometry'] = {'revision': raw['revision'], 'viewer': patch['key'], 'receipt': bound(report_path),
                           'scene': {**bound(scene), 'decoded_sha256': hashlib.sha256(decoded).hexdigest()}}
    current['shop'] = {'revision': raw['revision'], 'geometry': bound(report_path), 'result': bound(report_path),
                       'packet': 'docs/bolted-frame-development/builder-plan.md', 'overrides': [bound(datums)],
                       'shop_planning_only': True, 'affected_installation_qualified': False,
                       'passage_profile': bound('docs/bolted-frame-development/enclosed-passage-study.svg')}
    current['optional_grid']['applies_to_current_geometry'] = False
    current['optional_grid']['scope'] = 'Preserved notched predecessor; no enclosed-passage expanded-grid variant'
    for name in ('current_response', 'structural_assessment', 'engineering_assessment'):
        current[name] = None
    index_path.write_bytes(encoded(current))
    print(json.dumps({'geometry': current['geometry'], 'checked_study': bound(raw_path)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path)
    args = parser.parse_args()
    publish(args.study)
