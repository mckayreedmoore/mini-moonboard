"""Authenticate/reproduce the combined CAD inputs with their frozen reader."""

import argparse
import json
from pathlib import Path

from scripts.eoere_current_shop_followup import ROOT, module, require, sha

FOLDER = ROOT/'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/single-leg-header-integration-v1/attempt06'


def replay(out=None):
    geometry = json.loads((FOLDER/'geometry.json').read_bytes())
    reader_path = FOLDER/'frozen-parent-builder-layout.py'
    snapshot = FOLDER/'producer-snapshot.py'
    for path, expected in geometry['source_sha256'].items():
        actual = reader_path if Path(path).resolve() == ROOT/'scripts/eoere_builder_layout.py' else Path(path)
        require(sha(actual) == expected, 'frozen geometry input differs: '+path)
    require(sha(snapshot) == geometry['source_sha256']['scripts/eoere_leg_header_revision.py'],
            'exact corrected producer snapshot required')
    if out is None:
        print(json.dumps({'passed': True, 'source_bindings': len(geometry['source_sha256']),
                          'CAD_rebuilt': False, 'frozen_builder_reader': str(reader_path.relative_to(ROOT))}))
        return
    reader = module(reader_path, 'combined_geometry_frozen_builder_reader')
    reader.ROOT, reader.INDEX = ROOT, FOLDER/'parent-index.json'
    producer = module(snapshot, 'combined_geometry_frozen_producer')
    producer.shop = reader
    producer.build(out.resolve())
    fresh = json.loads((out/'geometry.json').read_bytes())
    require(fresh['axes'] == geometry['axes'] and fresh['fitting_poses'] == geometry['fitting_poses'],
            'replayed physical axes/attachments differ')
    require({r['id']: r['sha256'] for r in fresh['changed_finished_solids']} ==
            {r['id']: r['sha256'] for r in geometry['changed_finished_solids']}, 'replayed occupied solids differ')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-inputs', action='store_true')
    group.add_argument('--out', type=Path)
    replay(parser.parse_args().out)
