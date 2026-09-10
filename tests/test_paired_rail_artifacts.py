"""Verify the paired-rail export and viewer share current, unqualified evidence."""
import csv
import hashlib
import json
from pathlib import Path


def test_paired_rail_artifacts_match_audit_and_viewer():
    key = 'paired-rail-base-development'
    exported, viewer = Path('exports')/key, Path('site/hybrid')/key
    manifest = json.loads((exported/'manifest.json').read_text())
    viewer_manifest = json.loads((viewer/'manifest.json').read_text())
    data = json.loads((viewer/'parts.json').read_text())
    audit = json.loads((exported/'geometry-audit.json').read_text())
    assert (exported/'geometry-audit.json').read_bytes() == Path(
        'fea/results/paired-rail-base-audit-v1.json').read_bytes()
    assert manifest['candidate'] == audit['candidate'] == data['design']['key'] == key
    assert manifest['design'] == viewer_manifest['design'] == data['design']
    assert manifest['qualified_for_design'] is False
    assert data['design']['qualified_for_design'] is False
    assert 'NOT build-ready' in data['design']['status']
    for flag in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert audit[flag] is False
    assert audit['base_bracket_path']['explicit_path_present']
    assert audit['base_bracket_path']['strength_qualified'] is False
    assert manifest['source_sha256'] == viewer_manifest['source_sha256']
    assert manifest['source_sha256'].items() >= audit['source_sha256'].items()
    assert manifest['source_sha256']
    for name, sha in manifest['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    for directory, record in ((exported, manifest), (viewer, viewer_manifest)):
        actual = {str(path.relative_to(directory)) for path in directory.rglob('*')
                  if path.is_file() and path != directory/'manifest.json'}
        assert set(record['artifact_sha256']) == actual
        for name, sha in record['artifact_sha256'].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha, name
    assert manifest['viewer_artifact_sha256'] == viewer_manifest['artifact_sha256']
    assert {'open-frame.png', 'base-connection.png', key+'.step', 'geometry-audit.json'} <= set(
        manifest['artifact_sha256'])
    for name in ('open-frame.png', 'base-connection.png'):
        assert (exported/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    items = {part['name']: part for part in data['parts']}
    inventory = audit['inventory']
    expected_count = sum(inventory[name] for name in (
        'wood_parts', 'brackets', 'panel_kicker_screws', 'bolts', 'bracket_screws'))
    assert len(items) == len(data['parts']) == expected_count
    assert inventory['installed_inserts'] == 0
    assert not any(name.startswith('insert_') or part['fabrication']['kind'] == 'insert'
                   for name, part in items.items())
    assert sum(part['fabrication']['kind'] == 'screw' for part in items.values()) == (
        inventory['panel_kicker_screws']+inventory['bracket_screws'])
    assert sum(part['fabrication']['kind'] == 'bolt' for part in items.values()) == inventory['bolts']
    rails = {f'base_rail_mid_{level}_{side}' for level in ('lower', 'upper') for side in ('left', 'right')}
    assert {name for name in items if name.startswith('base_rail_mid_')} == rails
    assert set(inventory['independent_paired_rails']) == rails
    assert all(items[name]['fabrication']['dimensions_mm'][1:] == [139.7, 38.1] for name in rails)
    assert {'clip_paired_base_center', 'clip_single_header_center', 'base_principal_center',
            'base_post_center', 'base_header'} <= items.keys()
    with (exported/'connections.csv').open(newline='') as stream:
        connections = list(csv.DictReader(stream))
    assert len({row['connection'] for row in connections}) == len(connections)
    assert {'fastener_'+row['connection'] for row in connections} == {
        name for name in items if name.startswith('fastener_')}
    center = [row for row in connections if row['connection'].startswith('clip_paired_base_center_')]
    assert len(center) == 6
    assert {row['members'] for row in center} == {
        'clip_paired_base_center + base_header', 'clip_paired_base_center + base_principal_center'}
    for name, part in items.items():
        assert part['path'] == f'hybrid/{key}/models/{name}.stl'
    assert set(viewer_manifest['artifact_sha256']) == {'parts.json'} | {
        'models/'+name+'.stl' for name in items}
