"""The published candidate must retain all hardware and authenticated assets."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT/'site/hybrid/wider-leg-development'


def test_published_wider_leg_inventory():
    manifest = json.loads((VIEWER/'parts.json').read_text())
    assert manifest['design']['qualified_for_design'] is False
    assert manifest['design']['bolts_per_leg'] == 6
    groups = defaultdict(set)
    for part in manifest['parts']:
        f = part['fabrication']
        if f.get('connection_name', '').startswith('lumber_leg_bolt_'):
            groups[f['connection_name']].add(f['hardware_role'])
    assert len(groups) == 12
    assert all(roles == {'shaft', 'head_plate', 'nut_plate', 'spacer_1',
                         'spacer_2', 'spacer_3', 'head', 'nut'} for roles in groups.values())
    assert len(manifest['parts']) == len({p['name'] for p in manifest['parts']})
    assert sum(p['fabrication']['kind'] == 'tnut' for p in manifest['parts']) == 142


def test_published_wider_leg_provenance():
    manifest = json.loads((VIEWER/'manifest.json').read_text())
    for key, base in [('source_sha256', ROOT), ('artifact_sha256', VIEWER),
                      ('inherited_mesh_sha256', ROOT/'site')]:
        for name, expected in manifest[key].items():
            assert hashlib.sha256((base/name).read_bytes()).hexdigest() == expected, name
    parts = json.loads((VIEWER/'parts.json').read_text())['parts']
    for part in parts:
        path = part['path']
        assert (ROOT/'site'/path).is_file()
        if not path.startswith('hybrid/wider-leg-development/'):
            assert path in manifest['inherited_mesh_sha256']
