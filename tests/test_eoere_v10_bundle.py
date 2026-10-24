import copy
import hashlib
import json

import pytest

from scripts.eoere_v10_bundle import CASES, FALSE_FLAGS, LOAD, validate


@pytest.fixture
def delivery(tmp_path):
    def put(name, data):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(data).encode() if not isinstance(data, bytes) else data
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    revision = 'eoere-v10-controlled-test'
    flags = {key: False for key in FALSE_FLAGS}
    common = {'geometry_revision': revision, **flags}
    geometry = put('geometry.json', common)
    rows = []
    for case in sorted(CASES):
        refs = {key: put(case+'/'+key+'.json', {'case_id': case, 'role': key})
                for key in ('field', 'independent_replay', 'independent_plywood_replay')}
        rows.append({'case_id': case, 'both_independent_replays_admitted': True, **refs})
    bank = put('bank.json', {**common, 'physical_geometry': geometry, 'load_contract': LOAD,
                           'case_ids': sorted(CASES), 'cases': rows,
                           'all_six_cases_admitted': True, 'historical_force_pass_transferred': False})
    reference = put('reference.json', {**common, 'physical_geometry': geometry,
                                     'load_contract': LOAD, 'case_ids': sorted(CASES),
                                     'field_bindings': {r['case_id']: r['field'] for r in rows},
                                     'response_bank': bank})
    helper = put('scripts/eoere_load_parameters.py', b'# frozen load helper\n')
    manifest = {'schema': 'eoere_v10_delivery_bundle/v1', **common,
                'load_contract': LOAD, 'case_ids': sorted(CASES),
                'physical_operations_authorized': False,
                'artifacts': {'geometry': geometry, 'response_bank': bank,
                              'reference_review': reference,
                              'joint_applicability': put('joint.json', {**common, 'physical_geometry': geometry}),
                              'readiness': put('readiness.json', common)},
                'preparation_source_bindings': {helper['path']: helper['sha256']},
                'extra_top_bolt_duties': {'added_axis_ids': ['new_top_axis']},
                'remaining_numerical_exceedances': [{'member': 'test', 'index': 1.1}],
                'unresolved_qualifications': ['physical screw resistance']}
    for name in ('clearance', 'viewer_scene', 'builder_plan', 'hardware_bom', 'cut_plan', 'drill_plan'):
        manifest['artifacts'][name] = put(name+'.txt', b'conditional fixture\n')
    return manifest, tmp_path, put


def test_conditional_bundle_can_preserve_exceedances_without_releasing(delivery):
    manifest, root, _ = delivery
    result = validate(manifest, root)
    assert result['remaining_numerical_exceedances'][0]['index'] == 1.1
    assert result['fabrication_released'] is False


def test_hash_valid_reference_from_different_bank_is_rejected(delivery):
    manifest, root, put = delivery
    ref = manifest['artifacts']['reference_review']
    data = json.loads((root/ref['path']).read_bytes())
    data['field_bindings']['a12-left'] = data['field_bindings']['a12-right'] = data['field_bindings']['a12-rear']
    manifest['artifacts']['reference_review'] = put(ref['path'], data)
    with pytest.raises(ValueError, match='same six fields'):
        validate(manifest, root)


@pytest.mark.parametrize('artifact', ['reference_review', 'joint_applicability', 'readiness'])
def test_rehashed_release_claim_is_rejected(delivery, artifact):
    manifest, root, put = delivery
    ref = manifest['artifacts'][artifact]
    data = json.loads((root/ref['path']).read_bytes())
    data['fabrication_released'] = True
    manifest['artifacts'][artifact] = put(ref['path'], data)
    with pytest.raises(ValueError, match='claim boundary'):
        validate(manifest, root)


def test_changed_load_helper_stops_bundle_intake(delivery):
    manifest, root, _ = delivery
    (root/'scripts/eoere_load_parameters.py').write_text('# changed\n')
    with pytest.raises(ValueError, match='Binding mismatch'):
        validate(manifest, root)


def test_lower_load_not_accepted_as_unchanged_case(delivery):
    manifest, root, _ = delivery
    manifest['load_contract'] = copy.deepcopy(LOAD)
    manifest['load_contract']['weight_lb'] = 175
    with pytest.raises(ValueError, match='Load contract changed'):
        validate(manifest, root)
