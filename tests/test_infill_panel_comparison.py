"""Signed reaction refinement must gate otherwise converged panel comparisons."""
import pytest

from fea import infill_panel_comparison as screen


def test_individual_signed_reactions_and_controller_are_retained():
    a = {'ideal_screw_normal_reactions_n': {'first': -100., 'second': -99., 'small': .01}}
    z = {'ideal_screw_normal_reactions_n': {'first': -98., 'second': -100., 'small': -.01}}
    result = screen.reaction_refinement(a, z)
    assert result['all_individual_reactions_converged'] and result['controlling_identity_changed']
    z['ideal_screw_normal_reactions_n']['first'] = 100.
    result = screen.reaction_refinement(a, z)
    assert not result['all_individual_reactions_converged']
    assert result['individual_reactions'][0]['absolute_change_n'] == 200
    with pytest.raises(ValueError, match='identities changed'):
        screen.reaction_refinement(a, {'ideal_screw_normal_reactions_n': {'first': -100}})


def test_reaction_failure_suppresses_ratio_even_with_converged_displacements():
    cases = [{'candidate': candidate, 'case_id': case[2], 'mesh_mm': size,
              'compliance_mm_per_n': 1., 'max_abs_horizontal_seam_displacement_mm': 2.,
              'max_abs_vertical_seam_displacement_mm': 3.,
              'ideal_screw_normal_reactions_n': {'one': -100., 'two': -200.}}
             for candidate in ('baseline', 'revised') for case in screen.CASES for size in screen.shell.SIZES]
    result = screen.comparison_summary(cases, 'baseline', 'revised')
    assert result['numerical_comparison_accepted']
    cases[0]['ideal_screw_normal_reactions_n']['one'] = -120.
    result = screen.comparison_summary(cases, 'baseline', 'revised')
    assert not result['numerical_comparison_accepted']
    assert 'D6' not in {r['case_id'] for r in result['accepted_case_surrogate_ratios']}
    assert not result['actual_panel_qualified'] and not result['qualified_for_design']


def test_source_closure_contains_all_three_comparison_layers():
    sources = screen.source_hashes()
    assert {'fea/infill_panel_comparison.py', 'fea/split_center_panel_comparison.py',
            'fea/vertical_panel_comparison.py'} <= sources.keys()


def test_finer_mesh_pair_is_derived_without_mutating_frozen_sizes():
    cases = [{'candidate': candidate, 'case_id': case[2], 'mesh_mm': size,
              'compliance_mm_per_n': 1., 'max_abs_horizontal_seam_displacement_mm': 2.,
              'max_abs_vertical_seam_displacement_mm': 3.,
              'ideal_screw_normal_reactions_n': {'one': -100.}}
             for candidate in ('baseline', 'revised') for case in screen.CASES for size in (25., 15.)]
    result = screen.comparison_summary(cases, 'baseline', 'revised')
    assert result['mesh_sizes_mm'] == [25., 15.]
    assert result['numerical_comparison_accepted']
    assert screen.shell.SIZES == (40., 25.)
    with pytest.raises(ValueError, match='32 distinct'):
        screen.comparison_summary(cases[:-1], 'baseline', 'revised')


def test_reuse_cannot_relabel_results_from_another_solver_image():
    screen.verify_reuse_solver({'solver_image': screen.shell.IMAGE})
    for source in ({}, {'solver_image': 'sha256:'+'0'*64}):
        with pytest.raises(ValueError, match='Source solver image differs'):
            screen.verify_reuse_solver(source)
