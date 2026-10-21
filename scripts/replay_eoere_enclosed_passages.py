"""Replay the frozen hole study with its saved parent index, without changing live files."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(out=None):
    folder = Path('fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/enclosed-passages-v1/attempt02')
    report = json.loads((folder/'result.json').read_bytes())
    parent = folder/'parent-index.json'
    snapshot = Path(report['producer_snapshot']['path'])
    assert digest(snapshot) == report['producer_snapshot']['sha256']
    for name, expected in report['source_sha256'].items():
        actual_path = parent if name == 'docs/bolted-frame-development/development-revisions.json' else Path(name)
        assert digest(actual_path) == expected, name
    source = snapshot.read_text()
    old = "index = read('docs/bolted-frame-development/development-revisions.json')"
    assert source.count(old) == 1
    namespace = {'__name__': 'enclosed_passage_parent_replay', '__file__': str(snapshot),
                 'PARENT_INDEX_INPUT': str(parent)}
    # Execute only the hash-authenticated local producer with one guarded input substitution.
    exec(compile(source.replace(old, 'index = read(PARENT_INDEX_INPUT)'), str(snapshot), 'exec'), namespace)  # noqa: S102
    adapter = {'source_snapshot': report['producer_snapshot'],
               'parent_index': {'path': str(parent), 'sha256': digest(parent)},
               'adapter': {'path': str(Path(__file__).relative_to(Path.cwd())), 'sha256': digest(__file__)},
               'adaptation': 'Replace only the live revision-index read with the authenticated frozen parent-index input; no geometry or force law changes.'}
    if out is None:
        print(json.dumps({'passed': True, 'source_bindings': len(report['source_sha256']),
                          'CAD_executed': False, **adapter}))
        return
    namespace['build'](out, diameter=38.1, f1_offset=40.)
    path = out/'result.json'
    result = json.loads(path.read_bytes())
    result['replay_input_adapter'] = adapter
    path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-inputs', action='store_true')
    group.add_argument('--out', type=Path)
    args = parser.parse_args()
    replay(args.out)
