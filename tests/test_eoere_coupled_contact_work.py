"""Exact contact work and ownership controls without candidate assets."""
import copy
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_coupled_contact_work as model

TRIANGLE = [[0, 0, 0], [2, 0, 0], [0, 3, 0]]
POINT = [F(1, 2), F(3, 4), 0]
ROTATION = [[F(3, 5), -F(4, 13), F(48, 65)],
            [F(4, 5), F(3, 13), -F(36, 65)], [0, F(12, 13), F(5, 13)]]


def rotate(point):
    return [sum(a*b for a, b in zip(row, point, strict=True)) for row in ROTATION]


def test_known_oriented_gap_projection_weights_and_units():
    point = POINT[:2]+[2]; pair = model.triangle_pair(point, TRIANGLE)
    assert pair['oriented_gap'] == 12 and pair['normal_area_square'] == 36
    assert pair['projected_point'] == POINT
    assert pair['master_weights'] == [F(1, 2), F(1, 4), F(1, 4)]
    assert pair['projection_inside_closed_triangle'] is True
    # Distance H/|m|=12/6=2, rather than interpreting H as millimetres.
    assert pair['oriented_gap']/6 == 2


def test_active_pair_uses_one_repulsive_force_and_its_barycentric_reactions():
    forces = model.contact_forces(POINT, TRIANGLE, F(5, 3))
    assert forces == [[0, 0, 10], [0, 0, -5], [0, 0, F(-5, 2)], [0, 0, F(-5, 2)]]
    assert [sum(f[i] for f in forces) for i in range(3)] == [0]*3


@pytest.mark.parametrize('point,multiplier', [(POINT[:2]+[1], 1), (POINT[:2]+[-1], 0), (POINT, -1),
    ([3, 3, 0], 1), (POINT, True)])
def test_separation_with_pressure_penetration_tension_outside_projection_and_boolean_are_refused(point, multiplier):
    with pytest.raises(ValueError):
        model.contact_forces(point, TRIANGLE, multiplier)


def test_open_pair_has_no_contact_force():
    assert model.contact_forces(POINT[:2]+[3], TRIANGLE, 0) == [[0]*3]*4


@pytest.mark.parametrize('height', [0, F(2, 5), F(-1, 7)])
def test_all_twelve_gap_derivatives_match_exact_directional_work(height):
    coordinates = [POINT[:2]+[height], *copy.deepcopy(TRIANGLE)]
    gradients = model.triangle_pair(coordinates[0], coordinates[1:])['gap_gradients_slave_a_b_c']
    step = F(1, 100000)
    for owner in range(4):
        for axis in range(3):
            plus, minus = copy.deepcopy(coordinates), copy.deepcopy(coordinates)
            plus[owner][axis] += step; minus[owner][axis] -= step
            high = model.triangle_pair(plus[0], plus[1:])['oriented_gap']
            low = model.triangle_pair(minus[0], minus[1:])['oriented_gap']
            assert (high-low)/(2*step) == gradients[owner][axis]


def test_finite_common_rotation_and_translation_preserve_gap_and_covary_gradients():
    point = POINT[:2]+[F(1, 3)]; old = model.triangle_pair(point, TRIANGLE)
    shift = [17, -23, 31]
    moved = [[a+b for a, b in zip(rotate(p), shift, strict=True)] for p in [point, *TRIANGLE]]
    new = model.triangle_pair(moved[0], moved[1:])
    assert new['oriented_gap'] == old['oriented_gap'] and new['master_weights'] == old['master_weights']
    assert new['gap_gradients_slave_a_b_c'] == [rotate(g) for g in old['gap_gradients_slave_a_b_c']]


@pytest.mark.parametrize('height', [0, 1])
def test_all_gap_gradients_have_zero_net_force_and_spatial_moment_even_off_contact(height):
    points = [POINT[:2]+[height], *TRIANGLE]
    gradients = model.triangle_pair(points[0], points[1:])['gap_gradients_slave_a_b_c']
    assert [sum(g[i] for g in gradients) for i in range(3)] == [0]*3
    moments = [model.cross(p, g) for p, g in zip(points, gradients, strict=True)]
    assert [sum(m[i] for m in moments) for i in range(3)] == [0]*3


def test_flipping_triangle_orientation_changes_the_admissible_side():
    point = POINT[:2]+[1]
    before = model.triangle_pair(point, TRIANGLE)
    after = model.triangle_pair(point, [TRIANGLE[0], TRIANGLE[2], TRIANGLE[1]])
    assert before['oriented_gap'] == -after['oriented_gap'] == 6
    with pytest.raises(ValueError):
        model.contact_forces(point, [TRIANGLE[0], TRIANGLE[2], TRIANGLE[1]], 0)


@pytest.mark.parametrize('triangle', [[[0, 0, 0]]*3, [[0, 0, 0], [1, 1, 1], [2, 2, 2]], TRIANGLE[:2]])
def test_degenerate_or_incomplete_contact_faces_are_refused(triangle):
    with pytest.raises(ValueError):
        model.triangle_pair(POINT, triangle)


def small_load_case():
    roles = [{'id': 'bolt/shaft', 'center_of_mass_xyz_mm': [1, 0, 0]},
             {'id': 'bolt/head', 'center_of_mass_xyz_mm': [-2, 0, 0]}]
    return {'source_inputs': {'physical_owner_gravity_rows': [{'id': 'wood', 'kind': 'timber'}, {'id': 'shaft/bolt', 'kind': 'shaft'}],
        'shafts': [{'body': 'shaft/bolt', 'metal_roles': roles}]},
        'body_applied_loads': [{'id': 'physical-bolt-metal/bolt/shaft', 'body': 'shaft/bolt',
            'point_xyz_mm': [1, 0, 0], 'force_xyz_n': [0, 0, -4]},
            {'id': 'physical-bolt-metal/bolt/head', 'body': 'shaft/bolt', 'point_xyz_mm': [-2, 0, 0], 'force_xyz_n': [0, 0, -1]},
            {'id': 'self-weight/wood', 'body': 'wood', 'point_xyz_mm': [0, 3, 0], 'force_xyz_n': [0, 0, -7]}]}


def test_role_reparenting_preserves_each_force_point_and_all_twelve_affine_work_coefficients():
    field = small_load_case(); mapped = model.split_loads(field, (1, 2, 3))
    assert [row['body'] for row in mapped] == ['bolt/shaft', 'bolt/head', 'wood']
    assert [row['parent_body'] for row in mapped] == ['shaft/bolt', 'shaft/bolt', 'wood']
    for source, row in zip(field['body_applied_loads'], mapped, strict=True):
        assert source['id'] == row['id'] and source['point_xyz_mm'] == row['point_xyz_mm'] and source['force_xyz_n'] == row['force_xyz_n']
    coefficients = model.affine_load_coefficients(mapped)
    assert coefficients[:3] == [0, 0, -12]
    assert coefficients[9:] == [-2, -21, 0]


@pytest.mark.parametrize('change', ['duplicate_load', 'wrong_parent', 'wrong_role_point', 'unbound_owner',
    'missing_role', 'free_couple', 'duplicate_owner', 'duplicate_role'])
def test_incomplete_or_changed_load_ownership_is_refused(change):
    field = small_load_case(); loads = field['body_applied_loads']
    if change == 'duplicate_load': loads[1] = copy.deepcopy(loads[0])
    if change == 'wrong_parent': loads[0]['body'] = 'wood'
    if change == 'wrong_role_point': loads[0]['point_xyz_mm'][0] += 1
    if change == 'unbound_owner': loads[2]['body'] = 'unknown'
    if change == 'missing_role': loads.pop(1)
    if change == 'free_couple': loads[0]['moment_xyz_nmm'] = [0, 1, 0]
    if change == 'duplicate_owner': field['source_inputs']['physical_owner_gravity_rows'].append({'id': 'wood', 'kind': 'timber'})
    if change == 'duplicate_role': field['source_inputs']['shafts'][0]['metal_roles'].append(
        copy.deepcopy(field['source_inputs']['shafts'][0]['metal_roles'][0]))
    with pytest.raises(ValueError):
        model.split_loads(field, (1, 2, 3))


def stack_fixture():
    interval_centres = {'shaft': 27, 'head': F(-9, 2), 'head_washer': F(-5, 2),
                        'nut_washer': F(81, 2), 'spacer': 43, 'nut': F(95, 2)}
    return {'axis_id': 'bolt', 'body': 'shaft/bolt', 'basis': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        'point': [7, 11, 13], 'diameter_mm': 8, 'shaft_interval_mm': [-3, 57],
        'source_axis': {'before_plate_mm': 2, 'after_plate_mm': 0, 'grip_mm': 40, 'nut_side_spacer_mm': 4,
            'nominal_under_head_length_mm': 60, 'hardware_scenario': {
                'washer_thickness_mm': 1, 'washer_id_mm': 10, 'head_height_mm': 3, 'nut_height_mm': 5}},
        'metal_roles': [{'kind': key, 'center_of_mass_xyz_mm': [7+value, 11, 13]} for key, value in interval_centres.items()],
        'ends': [{'end': 'head', 'host': 'angle', 'support_s_mm': -2, 'pressure_face_s_mm': -3},
                 {'end': 'nut', 'host': 'wood_b', 'support_s_mm': 40, 'pressure_face_s_mm': 45}],
        'surfaces': [{'host': 'angle', 'kind': 'steel', 'interval_mm': [-2, 0], 'bore_diameter_mm': 9},
                     {'host': 'wood_a', 'kind': 'wood', 'interval_mm': [0, 20], 'bore_diameter_mm': 10},
                     {'host': 'wood_b', 'kind': 'wood', 'interval_mm': [20, 40], 'bore_diameter_mm': 10}]}


def test_spacer_and_all_axial_seats_have_the_known_order_and_clearances():
    result = model.nominal_stack(stack_fixture(), F(1, 10**7))
    assert result['nominal_role_intervals_mm']['spacer'] == ['41', '45']
    assert result['nominal_role_intervals_mm']['nut'] == ['45', '50']
    assert len(result['potential_axial_pairs']) == 5
    assert [row['role'] for row in result['potential_loose_metal_bore_pairs']] == ['head_washer', 'nut_washer', 'spacer']
    assert [F(row['exact_nominal_radial_clearance_mm']) for row in result['potential_host_bore_pairs']] == [F(1, 2), 1, 1]
    assert F(result['maximum_stored_axial_chain_error_mm']) == F(result['maximum_stored_centroid_error_mm']) == 0
    assert result['engaged_thread_geometry_partial_shank_and_interface_compliance_resolved'] is False


def test_no_spacer_chain_has_four_axial_pairs_and_retains_the_original_nut_seat():
    shaft = stack_fixture(); shaft['source_axis']['nut_side_spacer_mm'] = 0
    shaft['metal_roles'] = [row for row in shaft['metal_roles'] if row['kind'] != 'spacer']
    next(row for row in shaft['metal_roles'] if row['kind'] == 'nut')['center_of_mass_xyz_mm'][0] -= 4
    shaft['ends'][1]['pressure_face_s_mm'] = 41
    result = model.nominal_stack(shaft, F(1, 10**7))
    assert result['nominal_role_intervals_mm']['nut'] == ['41', '46']
    assert len(result['potential_axial_pairs']) == 4 and result['potential_axial_pairs'][-1] == ['nut_washer', 'nut']
    assert len(result['potential_loose_metal_bore_pairs']) == 2


def test_nominal_chain_keeps_world_centroids_on_a_tilted_recorded_axis():
    shaft = stack_fixture(); direction = [F(3, 5), F(4, 5), 0]; shaft['basis'][0] = direction
    for row in shaft['metal_roles']:
        station = row['center_of_mass_xyz_mm'][0]-7
        row['center_of_mass_xyz_mm'] = [value+station*n for value, n in zip(shaft['point'], direction, strict=True)]
    assert F(model.nominal_stack(shaft, F(1, 10**7))['maximum_stored_centroid_error_mm']) == 0


@pytest.mark.parametrize('length', [0, -1])
def test_consistently_changed_empty_or_reversed_shaft_domain_is_refused(length):
    shaft = stack_fixture(); shaft['source_axis']['nominal_under_head_length_mm'] = length
    shaft['shaft_interval_mm'] = [-3, -3+length]
    role = next(row for row in shaft['metal_roles'] if row['kind'] == 'shaft')
    role['center_of_mass_xyz_mm'][0] = 7-3+F(length, 2)
    with pytest.raises(ValueError, match='positive retained nominal stack dimensions'):
        model.nominal_stack(shaft, F(1, 10**7))


@pytest.mark.parametrize('change', ['centroid', 'shaft_length', 'host_gap', 'host_overlap', 'interference', 'seat', 'missing_role'])
def test_inconsistent_nominal_stack_data_are_refused(change):
    shaft = stack_fixture()
    if change == 'centroid': shaft['metal_roles'][0]['center_of_mass_xyz_mm'][1] += 1
    if change == 'shaft_length': shaft['shaft_interval_mm'][1] += 1
    if change == 'host_gap': shaft['surfaces'][1]['interval_mm'][0] += 1
    if change == 'host_overlap': shaft['surfaces'][1]['interval_mm'][0] -= 1
    if change == 'interference': shaft['surfaces'][0]['bore_diameter_mm'] = 7
    if change == 'seat': shaft['ends'][1]['pressure_face_s_mm'] += 1
    if change == 'missing_role': shaft['metal_roles'].pop()
    with pytest.raises(ValueError):
        model.nominal_stack(shaft, F(1, 10**7))


def test_literal_flange_dimensions_do_not_execute_cad_or_other_source():
    source = 'raise RuntimeError("do not execute")\nclass Scenario:\n leg_mm:float=88.9\n width_mm:float=88.9\n thickness_mm:float=6.35\n'
    assert model.literal_flange_dimensions(source) == {'leg_mm': F('88.9'), 'width_mm': F('88.9'), 'thickness_mm': F('6.35')}


def test_frozen_bootstrap_ignores_poisoned_module_cache_and_refuses_conflicting_pin(monkeypatch):
    monkeypatch.setitem(sys.modules, 'scripts.eoere_continuum_material_law', SimpleNamespace(bootstrap=None))
    assert callable(model.bootstrap({}).bootstrap)
    with pytest.raises(ValueError, match='bootstrap changed'):
        model.bootstrap({model.BOOT['path']: '0'*64})
