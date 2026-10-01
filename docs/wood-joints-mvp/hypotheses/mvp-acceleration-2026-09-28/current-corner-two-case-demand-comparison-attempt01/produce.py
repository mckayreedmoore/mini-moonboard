"""Source-bound two-case corner action comparison, not a design envelope."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
SOURCES = {
    'a12-rear': ('current-corner-native-demand-export-attempt03', 'current-corner-parent-export-audit-attempt01'),
    'a1-rear': ('current-corner-a1-rear-case-bound-export-attempt01', 'current-corner-a1-parent-export-audit-attempt01'),
}
PRIMARY_CONTACT_PAIRS = {
    frozenset(pair) for pair in (
        ('base_post_outer_left', 'knee_outer_left_spine'),
        ('knee_outer_left_spine', 'base_side_left'),
        ('base_side_left', 'knee_outer_left_inner_frame_block'),
        ('knee_outer_left_inner_frame_block', 'base_header'),
    )
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pins, cases, actions, contacts = {}, {}, {}, {}
    for case, (report_folder, audit_folder) in SOURCES.items():
        report_path = BASE / report_folder / 'corner-demand-report.json'
        audit_path = BASE / audit_folder / 'audit.json'
        report, audit = (json.loads(p.read_text()) for p in (report_path, audit_path))
        assert report['status'] == 'PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY'
        assert audit['status'] == 'PASS_PARENT_CORNER_INVENTORY_AND_EXACT_SIGNED_FORCE_AUDIT'
        assert audit['report_sha256'] == sha(report_path)
        assert len(report['increments']) == len(audit['increments']) == 7
        for p in (report_path, audit_path):
            pins[str(p.relative_to(ROOT))] = sha(p)
        cases[case] = {'increment_count': 7, 'full_load_factor': report['increments'][-1]['load_factor']}
        assert cases[case]['full_load_factor'] == 1
        for increment in report['increments']:
            selected_contacts = [x for x in increment['member_contact_bearing']['contact_cells'] if frozenset((x['first'], x['second'])) in PRIMARY_CONTACT_PAIRS]
            assert len(selected_contacts) == 16
            for contact in selected_contacts:
                name = contact['source_connection_name']
                row = contacts.setdefault(name, {'first': contact['first'], 'second': contact['second'], 'cases': {}})
                assert (row['first'], row['second']) == (contact['first'], contact['second'])
                data = contact['contact']
                assert math.isclose(data['normal_action_on_first_n'] / data['source_area_mm2'], data['modeled_average_pressure_mpa'], rel_tol=1e-12, abs_tol=1e-14)
                records = row['cases'].setdefault(case, [])
                records.append({'load_factor': increment['load_factor'], 'force_on_first_xyz_N': contact['force_on_first_xyz_n'], 'normal_force_N': data['normal_action_on_first_n'], 'normal_force_radius_N': data['normal_force_rounding_radius_n'], 'modeled_area_mm2': data['source_area_mm2'], 'modeled_patch_average_pressure_MPa': data['modeled_average_pressure_mpa'], 'state_from_force_interval': data['normal_state_from_force_interval']})
            for group_id, group in increment['primary_physical_bolt_groups'].items():
                for bolt in group['bolts']:
                    for action in bolt['actions']:
                        name = action['source_connection_name']
                        row = actions.setdefault(name, {'group_id': group_id, 'axis_id': bolt['axis_id'], 'role': action['role'], 'first': action['first'], 'second': action['second'], 'cases': {}})
                        assert (row['first'], row['second']) == (action['first'], action['second'])
                        magnitude = math.sqrt(math.fsum(v*v for v in action['force_on_first_xyz_n']))
                        state = {'load_factor': increment['load_factor'], 'resultant_N': magnitude, 'force_on_first_xyz_N': action['force_on_first_xyz_n']}
                        records = row['cases'].setdefault(case, {'all_increments': []})
                        records['all_increments'].append(state)
        for row in actions.values():
            values = row['cases'][case]['all_increments']
            row['cases'][case]['maximum'] = max(values, key=lambda v: v['resultant_N'])
    assert len(actions) == 14
    assert sum(x['role'] == 'candidate_bolt_lateral_plane' for x in actions.values()) == 8
    assert sum(x['role'] == 'physical_bolt_outer_seat_tension' for x in actions.values()) == 6
    for row in actions.values():
        assert set(row['cases']) == set(SOURCES)
        row['larger_resultant_case'] = max(SOURCES, key=lambda c: row['cases'][c]['maximum']['resultant_N'])
    assert len(contacts) == 16 and all(set(x['cases']) == set(SOURCES) for x in contacts.values())
    result = {'status': 'CONDITIONAL_TWO_CASE_CORNER_ACTION_COMPARISON', 'cases': cases, 'actions': actions, 'primary_path_contact_cells': contacts, 'source_sha256': pins, 'six_case_envelope_complete': False, 'joint_accepted': False, 'new_block_axes': 92, 'original_leg_runner_arrangements': 12, 'limits': ['Only two current conditional zero-gap/proxy-stiffness/no-slip cases; no design envelope or complete resistance.', 'Signed vectors are retained; component maxima must not be combined into an invented load case.', 'Interface moments are not internal bolt bending moments.', 'Modeled contact-patch averages are not actual wood stress, continuous contact pressure or bearing resistance. Zero-force intervals do not alone prove finite separation.']}
    (HERE / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    for group in ('BG001', 'BG003', 'BG045'):
        rows = [x for x in actions.values() if x['group_id'] == group]
        print(group, {case: round(max(x['cases'][case]['maximum']['resultant_N'] for x in rows if x['role'] == 'candidate_bolt_lateral_plane'), 3) for case in SOURCES})

if __name__ == '__main__':
    main()
