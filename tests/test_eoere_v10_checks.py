
import pytest

from scripts import eoere_v10_checks as checks


def rows():
    binding={'path':'own/field.json','sha256':'known'}
    analysis={'path':'own/geometry.json','sha256':'geometry'}
    material={'path':'own/material.json','sha256':'material'}
    field={'case_id': 'a12-forward','trial_parent_geometry': analysis,
        'response': {'converged':True},'counts': {'physical_bodies': 168,'shaft': 114,'fitting': 24},
        'panel_screw_actions': [{} for _ in range(66)],'release': {'fabrication':False,'climbing':False},
        'source_inputs': {'plywood_material': material,
            'scenario': {'climber_load_parameters':{'input_weight': 250,'input_unit': 'lb','downward_multiplier': 2,
                'horizontal_force_n': 300,'self_weight_and_accessory_loads_unchanged': True}},
            'case': {'loads':[{'id': 'accessory/left','force_xyz_n': [0,0,-122.583125]},
                           {'id': 'accessory/right','force_xyz_n': [0,0,-122.583125]}]}}}
    replay={'field': binding,'same_state_declared_fixed_floor_replayed': True,'all_credited_hosts_in_bearing': True,
                'false_screw_and_floor_forces_rejected': True,'equilibrium': {'gradient_inf_n': 1e-6,'physical_body_count': 168}}
    plywood={'field': binding,'raw_operator_checks': [{},{}]}
    return field,replay,plywood,binding,analysis,material,{'bodies': 168,'shafts': 114,'fittings': 24}


def admit(values):checks.intake_case('a12-forward',*values)


def test_matching_own_case_with_both_replays_is_admitted():admit(rows())


def test_other_candidate_replay_is_rejected():
    values=rows();values[1]['field']={'path':'old/field.json','sha256':'old'}
    with pytest.raises(ValueError,match='matching case'):admit(values)


def test_changed_accessory_load_is_rejected():
    values=rows();values[0]['source_inputs']['case']['loads'][0]['force_xyz_n'][2]/=2
    with pytest.raises(ValueError,match='25kg'):admit(values)


def test_missing_operator_replay_is_rejected():
    values=rows();values[2]['raw_operator_checks'].pop()
    with pytest.raises(ValueError,match='both analytical plywood'):admit(values)


def test_false_screw_force_control_cannot_be_omitted():
    values=rows();values[1]['false_screw_and_floor_forces_rejected']=False
    with pytest.raises(ValueError,match='must be admitted'):admit(values)


def test_physical_release_flag_is_rejected():
    values=rows();values[0]['release']['fabrication']=True
    with pytest.raises(ValueError,match='false physical release'):admit(values)


def test_incomplete_criterion_set_cannot_create_a_passing_summary():
    with pytest.raises(ValueError,match='all required'):
        checks.summarize_criteria({}, {}, {})
