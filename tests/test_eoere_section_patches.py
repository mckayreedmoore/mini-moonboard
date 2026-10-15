"""Independent exact geometry, statics, field and interpolation controls."""
from fractions import Fraction as F

import pytest

from scripts import eoere_section_patches as patches

STRENGTHS = {'tension': F(2), 'compression': F(3), 'parallel_shear': F(5), 'rolling_shear': F(7)}


def test_rational_section_frame_is_exactly_orthonormal_and_right_handed():
    basis = patches.frame('-0.363970234266')
    assert [[patches.dot(a, b) for b in basis] for a in basis] == [[F(i == j) for j in range(3)] for i in range(3)]
    assert patches.cross(basis[0], basis[1]) == basis[2]


def test_robust_inner_box_handles_a_rotated_convex_face_and_every_vertex_perturbation():
    polygon = [(F(-2), F(0)), (F(0), F(-2)), (F(2), F(0)), (F(0), F(2))]
    inner, outer = patches.robust_boxes(polygon, F(1, 10), F(1, 5))
    assert inner == (F(-9, 10), F(9, 10), F(-9, 10), F(9, 10))
    assert outer == (F(-21, 10), F(21, 10), F(-21, 10), F(21, 10))
    # Every independently shifted diamond vertex may move inward by .1 in
    # each coordinate; its most adverse diagonal edge is p+q=1.8.
    assert inner[1]+inner[3] == F(9, 5)


def test_nearly_axis_aligned_polygon_retains_the_chosen_inset_without_floating_tolerance():
    tiny = F(1, 10**100)
    polygon = [(-2, -1), (2, -1), (2+tiny, 1), (-2+tiny, 1)]
    inner, _ = patches.robust_boxes(polygon, F(1, 10**6), F(1, 10**4))
    assert inner[1]-inner[0] > F(3999, 1000)
    assert inner[3]-inner[2] == F(9999, 5000)


@pytest.mark.parametrize('polygon,envelope,inset', [
    ([(-1, -1), (-1, 1), (1, 1), (1, -1)], '.01', '.1'),
    ([(-1, -1), (1, -1), (0, 0), (1, 1), (-1, 1)], '.01', '.1'),
    ([(-1, -1), (1, -1), (1, 1), (-1, 1)], '0', '.1'),
    ([(-1, -1), (1, -1), (1, 1), (-1, 1)], '.1', '.1'),
    ([(-1, -1), (1, -1), (1, 1), (-1, 1)], '.01', '2'),
])
def test_invalid_convex_domain_or_uncertainty_refuses(polygon, envelope, inset):
    with pytest.raises(ValueError):
        patches.robust_boxes(polygon, envelope, inset)


@pytest.mark.parametrize('boxes', [[], [(0, 0, -1, 1)], [(0, 2, 0, 2), (1, 3, 1, 3)]])
def test_empty_degenerate_or_overlapping_patches_refuse(boxes):
    with pytest.raises(ValueError):
        patches.disjoint(boxes)


def test_constant_off_center_tractions_carry_all_six_independent_resultants():
    box = [0, 4, 4, 6]
    corners = [[[10, -3, 5]]*4]
    wrench = [80, -24, 40, 200, 400, -160]
    result = patches.certify(wrench, [box], STRENGTHS, corners)
    assert list(map(F, result['exact_recovered_wrench'])) == wrench
    assert list(map(F, result['exact_residual_before_correction'])) == [0]*6
    assert F(result['exact_construction_upper']) == F(10, 2)+F(3, 5)+F(5, 7)


def test_opposing_disconnected_patch_forces_carry_a_nonzero_torque():
    boxes = [[-3, -1, -1, 1], [1, 3, -1, 1]]
    corners = [[[0, 0, -2]]*4, [[0, 0, 2]]*4]
    # Each area is 4; forces cancel, while p*Vq gives 16+16.
    result = patches.certify([0, 0, 0, 32, 0, 0], boxes, STRENGTHS, corners)
    assert F(result['exact_construction_upper']) == F(2, 7)
    assert list(map(F, result['exact_recovered_wrench'])) == [0, 0, 0, 32, 0, 0]


def test_polynomial_correction_preserves_six_tiny_nonzero_balance_components():
    tiny = F(1, 2**180)
    wrench = [tiny, -2*tiny, 3*tiny, -4*tiny, 5*tiny, -6*tiny]
    result = patches.certify(wrench, [[-2, 2, -1, 1]], STRENGTHS, [[[0, 0, 0]]*4])
    assert list(map(F, result['exact_residual_before_correction'])) == wrench
    assert list(map(F, result['exact_recovered_wrench'])) == wrench
    assert F(result['exact_construction_upper']) > 0
    assert any(F(value) != 0 for patch in result['traction_polynomials'] for field in patch for _, _, value in field)


@pytest.mark.parametrize('force', [F(4), F(-4)])
def test_uniform_normal_lp_matches_the_independent_tension_or_compression_limit(force):
    box = [-1, 1, -1, 1]
    wrench = [force, 0, 0, 0, 0, 0]
    selected = patches.candidate(wrench, [box], STRENGTHS)
    result = patches.certify(wrench, [box], STRENGTHS, selected['corner_tractions_n_mm2'])
    necessary = patches.necessary([1 if force > 0 else -1, 0, 0, 0, 0, 0], wrench, [box], STRENGTHS)
    selected_bound = patches.necessary(selected['dual_multiplier'], wrench, [box], STRENGTHS)
    expected = F(1, 2) if force > 0 else F(1, 3)
    assert F(necessary['exact_necessary_lower']) == expected
    assert F(selected_bound['exact_necessary_lower']) <= expected
    assert expected <= F(result['exact_construction_upper']) <= expected+F(1, 10**12)


@pytest.mark.parametrize('component,target,expected', [(4, 20, 1), (5, 8, 1), (3, 20, 1)])
def test_translated_support_has_independent_moment_and_torque_answers(component, target, expected):
    multiplier, wrench = [0]*6, [0]*6
    multiplier[component], wrench[component] = 1, target
    strengths = {key: F(1) for key in STRENGTHS}
    result = patches.necessary(multiplier, wrench, [[1, 3, 4, 6]], strengths)
    assert F(result['exact_necessary_lower']) == expected


def test_square_continuous_pure_torque_support_matches_direct_maximum_integral():
    strengths = {key: F(1) for key in STRENGTHS}
    result = patches.necessary([0, 0, 0, 1, 0, 0], [0, 0, 0, F(8, 3), 0, 0], [[-1, 1, -1, 1]], strengths)
    # Integral of max(|p|,|q|) over [-1,1]^2 is 8/3.
    assert F(result['exact_outer_support']) == F(8, 3)
    assert F(result['exact_necessary_lower']) == 1


def test_candidate_and_exact_correction_bound_a_full_asymmetric_wrench():
    boxes = [[-3, -1, -1, 1], [1, 3, -1, 1]]
    wrench = [F(2), F(-3), F(4), F(5), F(-6), F(7)]
    selected = patches.candidate(wrench, boxes, STRENGTHS)
    result = patches.certify(wrench, boxes, STRENGTHS, selected['corner_tractions_n_mm2'])
    necessary = patches.necessary(selected['dual_multiplier'], wrench, boxes, STRENGTHS)
    assert F(necessary['exact_necessary_lower']) <= F(result['exact_construction_upper'])
    assert list(map(F, result['exact_recovered_wrench'])) == wrench


def test_original_uniform_gravity_recovers_force_and_moment_with_known_signs():
    force, moment = patches.cut_wrench(F(4), [0, 0], F(0), F(10), [5, 0, 0], [0, 0, -10], [])
    assert force == [0, 0, 4]
    assert moment == [0, 8, 0]


def test_off_axis_point_force_and_free_couple_are_retained_without_a_reaction_solve():
    actions = [([1, 2, 3], [4, 5, 6], [7, 8, 9])]
    force, moment = patches.cut_wrench(F(4), [0, 0], F(0), F(10), [5, 0, 0], [0, 0, 0], actions)
    # (point-cut) x F = (-3,2,3) x (4,5,6) = (-3,30,-23).
    assert force == [-4, -5, -6]
    assert moment == [-4, -38, 14]


def test_affine_selfweight_retains_the_full_source_mass_and_centroid():
    force, moment = patches.cut_wrench(F(10), [0, 0], F(0), F(10), [6, 2, 3], [0, 0, -10], [])
    assert force == [0, 0, 10]
    # Total gravity at (6,2,3), measured from cut (10,0,0).
    assert moment == [20, 40, 0]


def test_negative_source_gravity_density_refuses():
    with pytest.raises(ValueError, match='negative affine'):
        patches.cut_wrench(F(4), [0, 0], 0, 10, [9, 0, 0], [0, 0, -10], [])


def test_cubic_controls_reproduce_complete_known_polynomials_at_independent_points():
    def value(t):
        return [1+2*t-3*t*t+4*t**3, t, 1-t, t*t, 2*t**3, F(7)]
    controls = patches.cubic_controls([value(t) for t in [F(0), F(1, 3), F(2, 3), F(1)]])
    for t in [F(0), F(1, 100), F(2, 7), F(1, 2), F(5, 6), F(1)]:
        assert patches.evaluate_controls(controls, t) == value(t)


def test_affine_gravity_and_fixed_point_set_give_exact_cubic_wrench_interpolation():
    basis = patches.frame('-0.363970234266')
    actions = [([1, 2, 3], [4, 5, 6], [7, 8, 9])]
    def value(t):
        force, moment = patches.cut_wrench(2+5*t, [0, 0], 0, 10, [6, 2, 3], [0, 0, -10], actions)
        return [patches.dot(axis, force) for axis in basis]+[patches.dot(axis, moment) for axis in basis]
    controls = patches.cubic_controls([value(t) for t in [F(0), F(1, 3), F(2, 3), F(1)]])
    for t in [F(1, 17), F(3, 11), F(5, 9), F(19, 20)]:
        assert patches.evaluate_controls(controls, t) == value(t)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), True])
def test_nonfinite_or_boolean_source_values_refuse(value):
    with pytest.raises(ValueError):
        patches.rational(value)
