"""Verify the vertical-principal export and viewer share current, unqualified evidence."""
import csv
import hashlib
import json
from pathlib import Path

import pytest


def test_vertical_principal_artifacts_match_audit_and_viewer():
    key = 'vertical-principal-development'
    exported, viewer = Path('exports')/key, Path('site/hybrid')/key
    manifest = json.loads((exported/'manifest.json').read_text())
    viewer_manifest = json.loads((viewer/'manifest.json').read_text())
    data = json.loads((viewer/'parts.json').read_text())
    audit = json.loads((exported/'geometry-audit.json').read_text())
    assert (exported/'geometry-audit.json').read_bytes() == Path(
        'fea/results/vertical-principal-audit-v1.json').read_bytes()
    assert manifest['candidate'] == audit['candidate'] == data['design']['key'] == key
    assert manifest['design'] == viewer_manifest['design'] == data['design']
    assert manifest['qualified_for_design'] is False
    assert data['design']['qualified_for_design'] is False
    assert 'NOT build-ready' in data['design']['status']
    for flag in ('qualified_for_design', 'structural_analysis_run', 'joint_strength_passed', 'floor_qualified'):
        assert audit[flag] is False
    assert manifest['source_sha256'] == viewer_manifest['source_sha256']
    assert manifest['source_sha256'].items() >= audit['source_sha256'].items()
    assert manifest['source_sha256']
    assert {'mini_moonboard/vertical_principal_frame.py', 'fea/vertical_principal_audit.py'} <= set(
        audit['source_sha256'])
    assert 'mini_moonboard/vertical_principal_exports.py' in manifest['source_sha256']
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
    assert not any('rail_mid_' in name or name.startswith('clip_paired_mid_') for name in items)
    added = {f'{side}_{index}' for side in ('left', 'right') for index in (1, 2)}
    principals = {'base_principal_'+suffix for suffix in added}
    posts = {'base_post_'+suffix for suffix in added}
    assert principals | posts <= items.keys()
    assert set(inventory['new_single_2x6_principals']) == principals
    assert inventory['interior_horizontal_seam_rails'] == []
    assert all(items[name]['fabrication']['dimensions_mm'][1:] == pytest.approx([139.7, 38.1]) for name in principals)
    assert all(items[name]['fabrication']['dimensions_mm'][1:] == pytest.approx([234.95, 38.1]) for name in posts)
    assert {row['principal'] for row in audit['new_principal_support_paths']} == principals
    assert all(row['strength_qualified'] is False for row in audit['new_principal_support_paths'])
    assert audit['retained_gussets']['current_forces_available'] is False
    assert audit['retained_gussets']['force_reduction_established'] is False
    assert {'timber_base_gusset_left', 'timber_base_gusset_right', 'base_principal_center',
            'base_post_center', 'base_header', 'base_rail_top'} <= items.keys()
    assert inventory['bolts'] == 16
    with (exported/'connections.csv').open(newline='') as stream:
        connections = list(csv.DictReader(stream))
    assert len({row['connection'] for row in connections}) == len(connections)
    assert {row['connection']: (row['kind'], row['members'].split(' + ')) for row in connections} == {
        row['connection']: (row['kind'], row['members']) for row in audit['connection_ownership']}
    assert {'fastener_'+row['connection'] for row in connections} == {
        name for name in items if name.startswith('fastener_')}
    assert {row['connection'] for row in connections if row['kind'] == 'bolt'} == {
        f'{prefix}_{side}_{index}' for prefix in ('lumber_leg_bolt', 'timber_base')
        for side in ('left', 'right') for index in range(1, 5)}
    clips = {name for name in items if name.startswith('clip_')}
    assert len(clips) == inventory['brackets']
    for clip in clips:
        screws = [row for row in connections if row['connection'].startswith(clip+'_')]
        assert len(screws) == 6, clip
        assert all(row['kind'] == 'screw' and row['members'].split(' + ')[0] == clip for row in screws)
        assert all(set(row['members'].split(' + ')) <= items.keys() for row in screws)
    for suffix in added:
        for prefix, receiver, beam in (('clip_vertical_top_', 'base_principal_', 'base_rail_top'),
                                       ('clip_vertical_base_', 'base_principal_', 'base_header'),
                                       ('clip_vertical_header_', 'base_post_', 'base_header')):
            clip = prefix+suffix
            assert clip in clips
            screws = [row for row in connections if row['connection'].startswith(clip+'_')]
            assert {row['members'] for row in screws} == {
                clip+' + '+beam, clip+' + '+receiver+suffix}
    assert all('rail_mid_' not in row['members'] for row in connections)
    for name, part in items.items():
        assert part['path'] == f'hybrid/{key}/models/{name}.stl'
    assert set(viewer_manifest['artifact_sha256']) == {'parts.json'} | {
        'models/'+name+'.stl' for name in items}
