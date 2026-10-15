"""Fixed rigid profile and equilibrium-functional controls without assets."""
import ast
import sys
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_normal_patch_shaft_profiles as model


def body(first=6):
    return {'body': f'shaft/{first}', 'first_rigid_column': first, 'source_mode_columns': [0, 1, 2, 4, 5]}


def displacement(weights, registered, position, reference):
    first = registered['first_rigid_column']
    theta = weights.get(first+3, F(0))/1000
    x = weights.get(first, F(0))+theta*(position[2]-reference[2])
    z = weights.get(first+2, F(0))-theta*(position[0]-reference[0])
    return x, z


@pytest.mark.parametrize('axis_x', [-1, 1])
def test_profile_is_rigid_transverse_and_has_both_prescribed_centroid_values(axis_x):
    registered = body(); point = [F(31), F(7), F(82)]; reference = [F(11), F(51), F(-23)]
    weights = model.shaft_weights(registered, point, reference, axis_x, 10, 0, F(3, 4), F(1, 8))
    for s in [-2, 0, 4, 10, 12]:
        position = [point[0]+axis_x*s, point[1], point[2]]
        dx, dz = displacement(weights, registered, position, reference)
        assert dx == 0 and dz == F(1, 8)+F(3, 4)*F(s, 10)
    assert displacement(weights, registered, [point[0]+axis_x*10, point[1], point[2]], reference)[1] == F(7, 8)


def test_nonzero_rigid_reference_changes_weights_but_not_the_ideal_profile():
    registered = body(); point = [F(31), F(7), F(82)]
    all_weights = []
    for reference in ([0, 0, 0], [0, 750, 1100], [123, -9, 2000]):
        weights = model.shaft_weights(registered, point, reference, 1, 10, 0, F(3, 4), F(1, 8))
        all_weights.append(weights)
        assert displacement(weights, registered, [point[0]+4, point[1], point[2]], reference) == (0, F(17, 40))
    assert all_weights[0] != all_weights[1] != all_weights[2]


def test_uniform_equal_interval_coupon_gives_known_one_eighth_metric():
    # Remote interval [-1,0], leg [0,1], each unit density. The rigid profile
    # is f(s)=1/2+3s/4. Integrate f² and (1-f)² independently.
    registered = body(); point = [F(0)]*3; reference = [F(0), F(750), F(1100)]
    weights = model.shaft_weights(registered, point, reference, 1, F(1, 2), -F(1, 2), F(3, 4), F(1, 8))
    a = displacement(weights, registered, point, reference)[1]
    slope = displacement(weights, registered, [F(1), 0, 0], reference)[1]-a
    remote = a*a-a*slope+slope*slope/3
    leg = (1-a)**2-(1-a)*slope+slope*slope/3
    assert remote == leg == F(1, 16) and remote+leg == F(1, 8)


@pytest.mark.parametrize('change', ['missing_rotation', 'coincident_centroids', 'inclined_axis', 'incomplete_reference'])
def test_profile_refuses_inapplicable_geometry_or_registration(change):
    registered = body(); axis = 1; leg = 10; reference = [0, 750, 1100]
    if change == 'missing_rotation': registered['source_mode_columns'] = [0, 1, 2, 3, 5]
    if change == 'coincident_centroids': leg = 0
    if change == 'inclined_axis': axis = F(1, 2)
    if change == 'incomplete_reference': reference = [0, 750]
    with pytest.raises(ValueError):
        model.shaft_weights(registered, [31, 7, 82], reference, axis, leg, 0, F(3, 4), F(1, 8))


def coupon():
    bodies = [{'body': 'leg', 'first_rigid_column': 0, 'source_mode_columns': list(range(6))}]
    maps, owners = [{i: F(1)} for i in range(26)], ['leg']*6
    shafts = []
    for i in range(4):
        first = 6+5*i; registered = body(first); bodies.append(registered); owners += [registered['body']]*5
        shafts.append({'axis_id': f'axis{i}', 'body': registered['body'], 'point': [31, 7, 82],
                       'source_axis': {'direction_xyz': [1, 0, 0]},
                       'surfaces': [{'host': 'leg', 'kind': 'wood', 'interval_mm': [2, 4]},
                                    {'host': 'other', 'kind': 'wood', 'interval_mm': [0, 2]}]})
    field = {'source_inputs': {'shafts': shafts, 'flange_shared_face_patches': [{'first': 'fitting', 'second': 'other'}]}}
    source = {'shared_material_support_records': [{'exact_rigid_compression_row': {'1': '1'}}]}
    def action(rows, values):
        return [sum((v*values[j] for j, v in row.items()), F(0)) for row in rows]
    h = SimpleNamespace(core=SimpleNamespace(action=action))
    return ['leg', bodies, maps, owners, field, {'rigid_modes_reference_xyz_mm': [0, 750, 1100]}, source, h, '3/4', '1/8']


def test_composite_direction_uses_only_the_five_declared_owner_kernels():
    arguments = coupon(); virtual, direction, profiles = model.composite_direction(*arguments)
    assert len(virtual) == 13 and len(profiles) == 4
    assert direction[2] == 1 and all(direction[i] == 0 for i in (0, 1, 3, 4, 5))
    assert {p['axis_id'] for p in profiles} == {'axis0', 'axis1', 'axis2', 'axis3'}
    assert arguments[4]['source_inputs']['shafts'][0]['surfaces'][0]['interval_mm'] == [2, 4]


def test_whole_bed_owner_exclusion_covers_the_added_shafts():
    arguments = coupon(); arguments[4]['source_inputs']['flange_shared_face_patches'][0]['first'] = 'shaft/6'
    with pytest.raises(ValueError, match='every composite-trial owner'):
        model.composite_direction(*arguments)


def test_nonzero_support_derivative_is_refused_even_if_owner_metadata_claims_exclusion():
    arguments = coupon(); arguments[6]['shared_material_support_records'][0]['exact_rigid_compression_row'] = {'2': '1'}
    with pytest.raises(ValueError, match='support derivatives'):
        model.composite_direction(*arguments)


def test_foreign_coordinate_cannot_enter_a_registered_trial():
    arguments = coupon(); arguments[2].append({2: F(1)}); arguments[3].append('foreign')
    with pytest.raises(ValueError, match='owner isolated'):
        model.composite_direction(*arguments)


def test_profile_fraction_is_a_fixed_proof_choice():
    arguments = coupon(); arguments[-2] = '1/2'
    with pytest.raises(ValueError, match='predeclared fixed proof'):
        model.composite_direction(*arguments)


def test_complete_composed_ast_restores_the_preserved_original_driver():
    wrapper = model.private(model.WRAPPER, {})
    original = ast.parse((model.ROOT/model.DRIVER['path']).read_bytes())
    changed = model.rewrite(wrapper.rewrite(deepcopy(original)))
    restored = wrapper.rewrite(model.rewrite(deepcopy(changed), reverse=True), reverse=True)
    assert ast.dump(restored) == ast.dump(original)


def test_active_offset_expression_retains_all_virtual_owner_loads():
    expression = ast.parse(model.EXPRESSIONS[1][1], mode='eval')
    assert eval(compile(expression, '<virtual-offset>', 'eval'), {'load': [5, 7], 'virtual': {0: F(1), 1: F(2)}, 'F': F}) == -19


def test_verified_producer_ignores_cached_ordinary_modules(monkeypatch):
    def poison(*args, **kwargs):
        raise AssertionError('cached driver must not execute')
    for name in ('scripts.eoere_normal_patch_functionals', 'scripts.eoere_normal_patch_functional_consumer'):
        monkeypatch.setitem(sys.modules, name, SimpleNamespace(run=poison, rewrite=poison))
    driver, digest = model.producer({})
    assert driver._composite_direction is model.composite_direction and len(digest) == 64
    assert driver.equivalent([1, 0], [-1, 1], -1) == [0, 1]


def test_partial_ast_and_conflicting_source_pin_are_refused():
    with pytest.raises(ValueError, match='exact declared composite'):
        model.rewrite(ast.parse('answer = 1'))
    with pytest.raises(ValueError, match='source changed'):
        model.producer({model.WRAPPER['path']: '0'*64})
