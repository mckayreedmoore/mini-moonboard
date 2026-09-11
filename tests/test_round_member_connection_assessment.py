"""Independent section and sign checks; do not duplicate CAD implementation."""
import pytest

from fea.round_member_connection_assessment import (
    bore_section,
    cut_demand,
    irreducible_couple,
    member_actions,
    wrench,
)


def test_transverse_bore_removes_projected_strip_and_shifts_neutral_axis():
    section = bore_section(38.1, 139.7, 25.4, 35.)
    assert section['net_area_mm2'] == pytest.approx(38.1*(139.7-25.4))
    assert section['centroid_n_mm'] > 139.7/2
    assert section['front_ligament_mm'] == pytest.approx(22.3)
    assert section['rear_ligament_mm'] == pytest.approx(92.)
    centered = bore_section(10., 20., 4., 10.)
    assert centered['centroid_n_mm'] == pytest.approx(10.)
    assert centered['I_u_mm4'] == pytest.approx(10.*(20.**3-4.**3)/12)
    with pytest.raises(ValueError, match='enclosed'):
        bore_section(10., 20., 4., 1.)


def test_eccentric_tension_and_cut_sign_use_original_application_point():
    section = bore_section(10., 20., 4., 10.)
    actions = [{'name': 'pull', 'point': [2., 0., 10.], 'force': [0., 0., 100.]}]
    result = cut_demand(actions, [0., 0., 0.], [0., 0., 1.], [1., 0., 0.], [0., 1., 0.], section)
    assert result['axial_n_tension_positive'] == 100.
    assert result['bending_u_v_nmm'] == [0., -200.]
    assert result['nominal_net_normal_min_max_mpa'] == pytest.approx([.625-.75, .625+.75])
    with pytest.raises(ValueError, match='at the requested bore cut'):
        cut_demand(actions, [0., 0., 10.], [0., 0., 1.], [1., 0., 0.], [0., 1., 0.], section)


def test_mpc_ownership_preserves_bolt_action_reaction_and_member_gravity():
    record = {'elements': {'1': ['C3D20', [1, 2], 'wood_a'], '2': ['C3D20', [3, 4], 'wood_b']},
              'equations': [[[5, 1, 1.], [1, 1, -.5], [2, 1, -.5]],
                            [[6, 1, 1.], [3, 1, -.5], [4, 1, -.5]]],
              'nodes': {str(n): [0., 0., 0.] for n in range(1, 7)},
              'springs': [{'name': 'bolt', 'nodes': [5, 6]}],
              'members': [{'name': 'wood_a'}, {'name': 'wood_b'}], 'loads': {'5': [0., 0., -10.]}}
    actions = member_actions(record, {'connector_forces': {'bolt': {'force_on_first_xyz_n': [1., 2., 3.]}}})
    assert actions['wood_a'][0]['force'] == [1., 2., 3.]
    assert actions['wood_b'][0]['force'] == [-1., -2., -3.]
    all_actions = [row for rows in actions.values() for row in rows]
    force, moment = wrench([r['point'] for r in all_actions], [r['force'] for r in all_actions], [0., 0., 0.])
    assert force == pytest.approx([0., 0., -10.])
    assert moment == pytest.approx([0., 0., 0.])


def test_scalar_seating_spring_uses_physical_force_and_point_once():
    contact = {'name': 'seating_1', 'member': 'wood', 'point_xyz_mm': [2., 3., 4.],
               'inward_xyz': [0., -.8, .6], 'scalar_nodes': [10, 11]}
    record = {'elements': {}, 'equations': [], 'nodes': {'10': [2., 3., 4.], '11': [2., 3., 4.]},
              'springs': [{'name': 'seating_1', 'nodes': [10, 11]}],
              'members': [{'name': 'wood'}], 'loads': {}, 'seating_contacts': [contact]}
    report = {'connector_forces': {'seating_1': {'force_on_first_xyz_n': [0., -8., 6.]}},
              'seating_contacts': [{**contact, 'compression_n': 10., 'physical_force_on_wood_xyz_n': [0., -8., 6.]}]}
    actions = member_actions(record, report)
    assert actions['wood'] == [{'name': 'seating_1', 'point': [2., 3., 4.], 'force': [0., -8., 6.]}]
    report['connector_forces']['seating_1']['force_on_first_xyz_n'] = [10., 0., 0.]
    with pytest.raises(ValueError, match='physical wood normal'):
        member_actions(record, report)


def test_force_translation_cannot_remove_parallel_couple():
    result = irreducible_couple([0., 0., 10.], [0., -20., 3.])
    assert result['parallel_couple_xyz_nmm'] == [0., 0., 3.]
    assert result['equivalent_force_offset_xyz_mm'] == [2., 0., 0.]
    assert irreducible_couple([0., 0., 0.], [1., 2., 2.])['parallel_couple_norm_nmm'] == 3.
