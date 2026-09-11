"""Verify the horizontal-service export and viewer share current, unqualified evidence."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import pytest


def test_horizontal_service_artifacts_match_audit_and_viewer():
    key = 'horizontal-service-development'
    exported, viewer = Path('exports')/key, Path('site/hybrid')/key
    manifest = json.loads((exported/'manifest.json').read_text())
    viewer_manifest = json.loads((viewer/'manifest.json').read_text())
    data = json.loads((viewer/'parts.json').read_text())
    audit = json.loads((exported/'geometry-audit.json').read_text())
    assert (exported/'geometry-audit.json').read_bytes() == Path(
        'fea/results/horizontal-service-audit-v1.json').read_bytes()
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
    assert {'mini_moonboard/horizontal_service_frame.py', 'mini_moonboard/split_center_hardware.py',
            'fea/horizontal_service_audit.py'} <= set(
        audit['source_sha256'])
    assert 'mini_moonboard/horizontal_service_exports.py' in manifest['source_sha256']
    for name, sha in manifest['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    for directory, record in ((exported, manifest), (viewer, viewer_manifest)):
        actual = {str(path.relative_to(directory)) for path in directory.rglob('*')
                  if path.is_file() and path != directory/'manifest.json'}
        assert set(record['artifact_sha256']) == actual
        for name, sha in record['artifact_sha256'].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha, name
    assert manifest['viewer_artifact_sha256'] == viewer_manifest['artifact_sha256']
    assert {'open-frame.png', 'base-connection.png', 'bolt-ends-cutaway.png', key+'.step', 'geometry-audit.json'} <= set(
        manifest['artifact_sha256'])
    for name in ('open-frame.png', 'base-connection.png', 'bolt-ends-cutaway.png'):
        assert (exported/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    items = {part['name']: part for part in data['parts']}
    inventory = audit['inventory']
    expected_count = sum(inventory[name] for name in (
        'wood_parts', 'brackets', 'panel_kicker_screws', 'bracket_screws', 'lights', 'wires'))+5*inventory['bolts']
    assert len(items) == len(data['parts']) == expected_count
    assert inventory['installed_inserts'] == 0
    assert not any(name.startswith('insert_') or part['fabrication']['kind'] == 'insert'
                   for name, part in items.items())
    assert sum(part['fabrication']['kind'] == 'screw' for part in items.values()) == (
        inventory['panel_kicker_screws']+inventory['bracket_screws'])
    assert sum(part['fabrication']['kind'] == 'bolt' for part in items.values()) == 5*inventory['bolts']
    assert not any('rail_mid_' in name or name.startswith('clip_paired_mid_') for name in items)
    added = {'center_left', 'center_right'}
    principals = {'base_principal_'+suffix for suffix in added}
    posts = {'base_post_'+suffix for suffix in added}
    assert {name for name in items if name.startswith('base_principal_')} == principals
    assert {name for name in items if name.startswith('base_post_')} == posts | {
        'base_post_outer_left', 'base_post_outer_right'}
    assert 'base_principal_center' not in items and 'base_post_center' not in items
    assert set(inventory['new_single_2x6_principals']) == principals
    assert inventory['legacy_mid_rail_members'] == []
    assert set(inventory['upper_panel_edge_rails']) == {
        'base_rail_service_upper_left', 'base_rail_service_upper_right'}
    assert all(items[name]['fabrication']['dimensions_mm'][1:] == pytest.approx([139.7, 38.1]) for name in principals)
    assert all(items[name]['fabrication']['dimensions_mm'][1:] == pytest.approx([234.95, 38.1])
               for name in posts | {'base_post_outer_left', 'base_post_outer_right'})
    assert {row['principal'] for row in audit['new_principal_support_paths']} == principals
    assert all(row['strength_qualified'] is False for row in audit['new_principal_support_paths'])
    assert {'base_header', 'base_rail_top', 'clip_angle_base_left', 'clip_angle_base_right'} <= items.keys()
    assert inventory['bolts'] == 8
    with (exported/'connections.csv').open(newline='') as stream:
        connections = list(csv.DictReader(stream))
    assert len({row['connection'] for row in connections}) == len(connections)
    assert {row['connection']: (row['kind'], row['members'].split(' + ')) for row in connections} == {
        row['connection']: (row['kind'], row['members']) for row in audit['connection_ownership']}
    roles = ('shaft', 'near_washer', 'far_washer', 'head', 'nut')
    assert {name for name in items if name.startswith('fastener_')} == {
        'fastener_'+row['connection']+suffix for row in connections
        for suffix in (['_'+role for role in roles] if row['kind'] == 'bolt' else [''])}
    assert {row['connection'] for row in connections if row['kind'] == 'bolt'} == {
        f'{prefix}_{side}_{index}' for prefix in ('lumber_leg_bolt',)
        for side in ('left', 'right') for index in range(1, 5)}
    clips = {name for name in items if name.startswith('clip_')}
    assert len(clips) == inventory['brackets']
    for clip in clips:
        screws = [row for row in connections if row['connection'].startswith(clip+'_')]
        assert len(screws) == 6, clip
        assert all(row['kind'] == 'screw' and row['members'].split(' + ')[0] == clip for row in screws)
        assert all(set(row['members'].split(' + ')) <= items.keys() for row in screws)
    for suffix in added:
        family = 'split' if suffix.startswith('center_') else 'vertical'
        for prefix, receiver, beam in ((f'clip_{family}_top_', 'base_principal_', 'base_rail_top'),
                                       (f'clip_{family}_base_', 'base_principal_', 'base_header'),
                                       (f'clip_{family}_header_', 'base_post_', 'base_header')):
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

    electrical = [part for part in items.values() if part['fabrication']['kind'] in ('light', 'wire')]
    assert len(electrical) == inventory['lights']+inventory['wires'] == 263
    assert sum(p['fabrication']['kind'] == 'light' for p in electrical) == 132
    assert all(p['fabrication']['mass_included'] is False for p in electrical)
    assert data['design']['electrical_mass_included'] is False
    assert len(inventory['service_rails']) == 4
    assert {'wiring.json', 'wood-parts.csv'} <= manifest['artifact_sha256'].keys()

    # Inspect every selectable bolt mesh at its assembled location, not metadata alone.
    envelopes = {row['connection']: row for row in audit['bolt_component_envelopes']}
    audit_roles = {'near_washer': 'head_washer', 'far_washer': 'nut_washer'}
    for connection in (row for row in connections if row['kind'] == 'bolt'):
        name = connection['connection']
        origin = [float(connection[axis+'_mm']) for axis in 'xyz']
        direction = [float(connection['d'+axis]) for axis in 'xyz']
        assert math.sqrt(sum(value**2 for value in direction)) == pytest.approx(1.)
        expected = {row['role']: row['expected_axial_interval_mm'] for row in envelopes[name]['components']}
        intervals = {}
        for role in roles:
            item = items['fastener_'+name+'_'+role]
            assert item['fabrication']['connection_name'] == name
            assert item['fabrication']['hardware_role'] == role
            raw = (Path('site')/item['path']).read_bytes()
            count = struct.unpack_from('<I', raw, 80)[0]
            assert count > 0 and len(raw) == 84+50*count
            vertices = [row[3+i:6+i] for row in struct.iter_unpack('<12fH', raw[84:]) for i in (0, 3, 6)]
            assert all(math.isfinite(value) for point in vertices for value in point)
            extents = [max(point[i] for point in vertices)-min(point[i] for point in vertices) for i in range(3)]
            assert min(extents) > 0.
            assert extents == pytest.approx(item['viewer_aabb_mm'], abs=.51)
            axial = [sum((point[i]-origin[i])*direction[i] for i in range(3)) for point in vertices]
            intervals[role] = [min(axial), max(axial)]
            assert intervals[role] == pytest.approx(expected[audit_roles.get(role, role)], abs=.001)
        assert intervals['head'][0] < -.1 and intervals['head'][1] == pytest.approx(0., abs=.001)
        assert intervals['near_washer'][0] == pytest.approx(0., abs=.001)
        assert intervals['far_washer'][0] > intervals['near_washer'][1]
        assert intervals['nut'][0] == pytest.approx(intervals['far_washer'][1], abs=.001)
