"""Inventory intended constitutive laws from frozen INPUT, never solved forces."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json'
PIN = 'd3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'


def intended_internal_force(law, stiffness, delta):
    """delta=u_first-u_second; physical force on first is its negative."""
    if law == 'compression_only':
        return stiffness * min(delta, 0.)
    if law == 'tension_only':
        # The existing axial helper defines positive extension as u_second-u_first.
        # Its head-to-nut / wood-to-panel projection therefore also needs negative
        # native delta. A mechanism's name does not set its algebraic sign.
        return stiffness * min(delta, 0.)
    if law in ('bilateral', 'floor_tangent_all_bearing_hypothesis'):
        return stiffness * delta
    raise ValueError(law)


def produce():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    model = json.loads(raw)
    owners = model['connection_ownership']
    rows = []
    elements = set()
    auxiliary_dofs = set()
    floor_normals = {}
    floor_tangents = {}
    for spring in model['springs']:
        name = spring['name']
        owner = owners[name]
        role = owner['role']
        k = spring['stiffness_n_per_mm']
        assert k > 0 and not spring.get('radial_clearance_assumption', False)
        assert spring['element'] not in elements
        elements.add(spring['element'])
        for node in spring['nodes']:
            key = (node, spring['dof'])
            assert key not in auxiliary_dofs
            auxiliary_dofs.add(key)
        if role in ('timber_or_panel_contact', 'floor_normal'):
            assert spring['bearing_closed_assumption'] and not spring.get('tension_only_assumption', False)
            law = 'compression_only'
        elif role in ('physical_bolt_outer_seat_tension', 'non_qualifying_parametric_screw_withdrawal'):
            assert spring['bearing_closed_assumption'] and spring['tension_only_assumption']
            law = 'tension_only'
        elif role == 'assumed_no_slip_floor':
            assert spring['bearing_closed_assumption']
            law = 'floor_tangent_all_bearing_hypothesis'
        elif role in ('candidate_bolt_lateral_plane', 'retained_bolt_lateral_plane', 'panel_screw_lateral_plane'):
            assert not spring['bearing_closed_assumption']
            law = 'bilateral'
        else:
            raise ValueError(role)
        floor_gate = None
        if role == 'floor_normal':
            floor_normals[name] = spring
        elif role == 'assumed_no_slip_floor':
            floor_gate = name.removesuffix('_friction')
            floor_tangents.setdefault(floor_gate, []).append(spring)
        rows.append({'name': name, 'element': spring['element'], 'group': spring['group'],
                     'nodes': spring['nodes'], 'dof': spring['dof'], 'role': role,
                     'physical_owner': owner,
                     'first_body': owner['first'], 'second_body': owner['second'],
                     'stiffness_n_per_mm': k, 'intended_law': law,
                     'floor_normal_gate': floor_gate,
                     'historical_branch_active_NOT_REUSED': spring['active']})
    assert len(rows) == 1840
    assert set(floor_normals) == set(floor_tangents) and len(floor_normals) == 100
    for name, tangents in floor_tangents.items():
        assert sorted(x['dof'] for x in tangents) == [2, 3]
        assert all(x['stiffness_n_per_mm'] == floor_normals[name]['stiffness_n_per_mm'] for x in tangents)
    new_axes = {owner['axis_id'] for owner in owners.values() if owner['role'] == 'candidate_bolt_lateral_plane'}
    retained_axes = {owner['axis_id'] for owner in owners.values() if owner['role'] == 'retained_bolt_lateral_plane'}
    axial_axes = {owner['axis_id'] for owner in owners.values() if owner['role'] == 'physical_bolt_outer_seat_tension'}
    assert len(new_axes) == 92 and len(retained_axes) == 12 and not new_axes.intersection(retained_axes)
    assert axial_axes == new_axes.union(retained_axes)
    recorded_springs = {int(eid) for eid, element in model['elements'].items() if element[0] == 'SPRING2'}
    # Inactive elements are omitted from the historical native deck, but their
    # complete constitutive rows remain in the frozen model input.
    assert recorded_springs == elements
    for law, expected in [('compression_only', [-10., 0., 0.]),
                          ('tension_only', [-10., 0., 0.]),
                          ('bilateral', [-10., 0., 10.]),
                          ('floor_tangent_all_bearing_hypothesis', [-10., 0., 10.])]:
        assert [intended_internal_force(law, 100., d) for d in [-.1, 0., .1]] == expected
    result = {'schema': 'current_native_carrier_law_inventory/v1',
              'source_input_sha256': PIN, 'source_path': str(SOURCE.relative_to(HERE.parent)),
              'candidate': model['candidate'], 'geometry_revision_id': model['geometry_revision_id'],
              'law_counts': dict(Counter(x['intended_law'] for x in rows)),
              'role_counts': dict(Counter(x['role'] for x in rows)),
              'delta_convention': 'u_first_minus_u_second; RF_first=internal; physical_force_first=-internal',
              'engagement_sign_basis': 'Both current compression and axial tension helpers engage for u_second-u_first>0; tension uses the head-to-nut/wood-to-panel axis and ordered endpoints. See current_response_run.axial_tension_state and horizontal_panel_frame.assess.',
              'rows': rows, 'floor_normal_count': 100, 'floor_tangent_component_count': 200,
              'new_block_attachment_axes': sorted(new_axes),
              'retained_original_leg_runner_axes': sorted(retained_axes),
              'native_solve_executed': False, 'native_method_validated': False,
              'frame_ready_for_native_run': False, 'complete_joint_validated': False,
              'limits': ['Source is C11 INPUT only; rejected response forces and active states are not reused.',
                         'Floor tangents are a hypothesis only: applicable iff every paired normal has strictly positive bearing at the resulting compatible response.',
                         'Opening any floor cell invalidates this all-bearing hypothesis; this inventory supplies no general switching/reference-capture rule.',
                         'No stiffness, gap, material, load, geometry or resistance assumption is changed.',
                         'Native nonlinear force output and branch switching still require a passing method fixture.']}
    (HERE / 'carrier-laws.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['law_counts', 'role_counts', 'frame_ready_for_native_run']}, indent=2))


if __name__ == '__main__':
    produce()
