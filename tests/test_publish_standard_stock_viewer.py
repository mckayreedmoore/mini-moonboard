import copy
import gzip
import json
from pathlib import Path

import pytest

from scripts import publish_standard_stock_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / publisher.PROVENANCE).read_bytes())
STATUS = json.loads((ROOT / publisher.STATUS).read_bytes())
SCENE = json.loads(gzip.decompress((ROOT / publisher.SCENE).read_bytes()))
EVIDENCE = {name: json.loads((ROOT / ref['path']).read_bytes()) for name, ref in STATUS['sources'].items()}


def test_portable_check_never_reads_the_ignored_generation_inputs(monkeypatch):
    real_path = publisher.local_path

    def tracked_only(root, relative):
        assert not relative.startswith('fea/'), relative
        return real_path(root, relative)

    monkeypatch.setattr(publisher, 'local_path', tracked_only)
    result = publisher.check(ROOT)
    assert result['parts'] == 1151
    assert result['mesh_payloads'] == 11
    assert result['rigid_reuses'] == 128
    assert result['new_stl_files'] == 0
    assert result['ignored_inputs_read'] is False


def test_current_side_mesh_witnesses_use_the_new_side_export_and_other_nine_share_the_top_export():
    assert len(MANIFEST['mesh_sources']) == 11
    for row in MANIFEST['mesh_sources']:
        name = 'side_geometry' if row['name'] in {'base_side_left', 'base_side_right'} else 'top_geometry'
        assert row['original_export'] == publisher.FROZEN[name]
        mesh = next(item for item in SCENE['replacements'] if item['name'] == row['name'])
        assert publisher.sha(publisher.encode(mesh['mesh'])) == row['mesh_payload_sha256']
    assert (ROOT / publisher.STATUS).read_bytes().endswith(b'\n')
    assert publisher.sha((ROOT / publisher.STATUS).read_bytes()) == publisher.FROZEN['results']['sha256']


def test_compiler_selects_current_sides_without_copying_superseded_mesh_payloads():
    top = {'parent_scene': {'sha256': publisher.PARENT['sha256']}, 'replacements': copy.deepcopy(SCENE['replacements']),
           'reuses': SCENE['reuses'], 'removals': SCENE['removals'], 'triangle_topologies': SCENE['triangle_topologies'],
           'screw_axis_updates': SCENE['screw_axis_updates']}
    side_rows = [copy.deepcopy(row) for row in SCENE['replacements'] if row['name'] in {'base_side_left', 'base_side_right'}]
    sides = {'geometry_source': {'sha256': publisher.GEOMETRY_SHA}, 'part_count': 1151, 'counts': publisher.COUNTS,
             'replacements': side_rows, 'triangle_topologies': SCENE['triangle_topologies'],
             'stack_updates': SCENE['stack_updates'], 'axis_updates': SCENE['axis_updates']}
    for row in top['replacements']:
        if row['name'] in {'base_side_left', 'base_side_right'}:
            row['mesh']['vertices_base64'] = 'superseded fixture bytes; must never be copied'
    composed, witnesses = publisher.compose(top, sides, STATUS)
    assert len(witnesses) == 11
    assert [r for r in composed['replacements'] if r['name'] in {'base_side_left', 'base_side_right'}] == side_rows


@pytest.mark.parametrize('change', ['scalar', 'old_geometry', 'failed_replay', 'missing_diagnostic', 'adopted_Cg', 'approved_packers'])
def test_numerical_source_counterexamples_cannot_publish_as_current(change):
    status, records = copy.deepcopy(STATUS), copy.deepcopy(EVIDENCE)
    if change == 'scalar':
        records['reference_review']['numerical_reference_maxima']['timber_net_shear_torsion']['index'] = 1.0149317282
        status['declared_vector_reference']['index'] = 1.0149317282
    elif change == 'old_geometry':
        records['response_bank']['physical_geometry']['sha256'] = '0b8fd199d012381308d5a7ce8a579195da6b1297a5b2de8647d30a9651ddcabf'
    elif change == 'failed_replay':
        records['response_bank']['cases'][0]['both_independent_replays_admitted'] = False
    elif change == 'missing_diagnostic':
        records['diagnostic_inventory']['above_reference_case_rows'].pop()
    elif change == 'adopted_Cg':
        status['actual_Cg_adopted'] = .5
    else:
        status['custom_packers_approved'] = True
    with pytest.raises(ValueError):
        publisher.result_contract(status, records)


@pytest.fixture
def portable_target(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.STATUS, publisher.PROVENANCE)}
    monkeypatch.setattr(publisher, 'prepare_payloads', lambda *_: payloads)
    for ref in [publisher.PARENT, *MANIFEST['result_sources'].values()]:
        destination = tmp_path / ref['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / ref['path']).read_bytes())
    return tmp_path, payloads


def test_a_late_conflict_stops_before_any_new_asset_copy(portable_target):
    target, payloads = portable_target
    conflict = target / publisher.PROVENANCE
    conflict.parent.mkdir(parents=True, exist_ok=True)
    conflict.write_bytes(b'preserve another owner\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(ROOT, target)
    assert conflict.read_bytes() == b'preserve another owner\n'
    assert not (target / next(iter(payloads))).exists()


def test_portable_publication_is_idempotent_without_ignored_inputs(portable_target):
    target, payloads = portable_target
    publisher.publish(ROOT, target)
    times = {name: (target / name).stat().st_mtime_ns for name in payloads}
    result = publisher.publish(ROOT, target)
    assert result['ignored_inputs_read'] is False
    assert all((target / name).stat().st_mtime_ns == stamp for name, stamp in times.items())
