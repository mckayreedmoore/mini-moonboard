"""Analytical field scaling, source-branch and invalid-comparison controls."""
import copy
from types import SimpleNamespace

import pytest

from mini_moonboard import nds_2024_multi_member_bolt_yield as nds
from scripts import eoere_joint_reference_reductions as method


def grid():
    # |q|=5, cap=10; |M|=4t(1-t), cap=2, maximum=.5 at t=.5.
    return {'physical_compatibility': False, 'complete_joint_resistance': None, 'adjusted_capacity': None,
            'cells': [{'low': 0., 'high': 1., 'cap': 10., 'density_yz': [3., 4.]}],
            'continuous_segments': [{'raw_moment_cap': 2.,
                                     'moment_coefficients_unit_interval_nmm': [[0., 0., 0.], [0., 0., 4.], [0., 0., -4.]]}],
            'certified_raw_reference_index': .5, 'raw_bearing_index': .5, 'continuous_raw_bending_index': .5}


def test_reduced_references_leave_the_original_force_and_moment_fields_unchanged():
    source = grid()
    before = copy.deepcopy(source)
    actual = method.compare_saved_field(source, 5.)
    assert source == before
    assert actual['uniform_reduced_certified_witness_index'] == 2.5
    assert actual['uniform_reduced_bearing_index'] == 2.5
    assert actual['uniform_reduced_continuous_bending_index'] == 2.5
    assert actual['saved_witness_exceeds_assumed_reference'] is True
    assert actual['complete_joint_resistance'] is None
    assert actual['physical_failure_established'] is False


def test_exact_reference_boundary_is_not_reported_as_an_exceedance():
    source = grid()
    source['cells'][0]['cap'] = 25.
    source['continuous_segments'][0]['raw_moment_cap'] = 5.
    for key in ('certified_raw_reference_index', 'raw_bearing_index', 'continuous_raw_bending_index'):
        source[key] = .2
    actual = method.compare_saved_field(source, 5.)
    assert actual['uniform_reduced_certified_witness_index'] == 1.
    assert actual['saved_witness_exceeds_assumed_reference'] is False


def test_frozen_source_four_row_zero_padded_quadratic_is_preserved_and_accepted():
    source = grid()
    source['continuous_segments'][0]['moment_coefficients_unit_interval_nmm'].append([0., 0., 0.])
    before = copy.deepcopy(source)
    actual = method.compare_saved_field(source, 5.)
    assert actual['uniform_reduced_continuous_bending_index'] == 2.5
    assert source == before


def test_nonzero_cubic_term_cannot_be_silently_trimmed_into_the_quadratic_model():
    source = grid()
    source['continuous_segments'][0]['moment_coefficients_unit_interval_nmm'].append([0., 0., 1.])
    with pytest.raises(ValueError, match='moment quadratic'):
        method.compare_saved_field(source, 5.)


@pytest.mark.parametrize('divisor', [True, .5, float('nan'), float('inf')])
def test_favorable_or_nonfinite_reference_reductions_are_rejected(divisor):
    with pytest.raises(ValueError, match='reference reduction'):
        method.compare_saved_field(grid(), divisor)


@pytest.mark.parametrize('field,value', [('physical_compatibility', True),
                                        ('complete_joint_resistance', 1.), ('adjusted_capacity', 1.)])
def test_new_physical_or_complete_capacity_claims_are_rejected(field, value):
    source = grid()
    source[field] = value
    with pytest.raises(ValueError, match='claim boundary'):
        method.compare_saved_field(source, 5.)


@pytest.mark.parametrize('field,value', [('cap', 0.), ('cap', float('nan')), ('high', 0.),
                                        ('density_yz', [3., float('nan')]), ('density_yz', [3., 4., 5.])])
def test_invalid_density_or_cell_reference_is_rejected(field, value):
    source = grid()
    source['cells'][0][field] = value
    with pytest.raises(ValueError, match='vector density'):
        method.compare_saved_field(source, 5.)


@pytest.mark.parametrize('field', ['certified_raw_reference_index', 'raw_bearing_index', 'continuous_raw_bending_index'])
def test_understated_source_indices_are_rejected_by_independent_field_norms(field):
    source = grid()
    source[field] = .49
    with pytest.raises(ValueError, match='continuous norms'):
        method.compare_saved_field(source, 5.)


def test_source_mode_endpoints_bound_the_full_affine_angle_range():
    result = method.reduction_range(nds, [.2881, .369], .375)
    assert result['source_mode_reduction_range'] == [3.2, 5.]
    assert result['generalized_mixed_stack_ASD_conversion_established'] is False
    # Independent table coefficients and an interior angle, not another call
    # to the production reduction helper.
    coefficients = {'Im': 4., 'Is': 4., 'II': 3.6, 'IIIm': 3.2, 'IIIs': 3.2, 'IV': 3.2}
    assert min(coefficients.values()) == result['source_mode_reduction_range'][0]
    assert max(coefficients.values())*1.25 == result['source_mode_reduction_range'][1]
    interior = {k: v*(1.+37./360.) for k, v in coefficients.items()}
    assert all(3.2 <= v <= 5. for v in interior.values())


@pytest.mark.parametrize('diameters,nominal', [([.249], .375), ([1.01], 1.1), ([.375], .25), ([], .375)])
def test_other_nds_diameter_branches_or_incompatible_nominal_size_are_rejected(diameters, nominal):
    with pytest.raises(ValueError, match='diameter range'):
        method.reduction_range(nds, diameters, nominal)


@pytest.mark.parametrize('field,value', [('current_screw_count', 65), ('current_bolt_count', 102),
                                        ('extra_grid', True), ('actual_observations', {}),
                                        ('working_uniform_reference_divisor', 4.), ('structural_acceptance', True)])
def test_changed_current_scope_or_claims_are_rejected(field, value):
    inputs = method.current.read(method.current.ref(method.INPUT))
    inputs[field] = value
    with pytest.raises(ValueError):
        method.validate(inputs)


def test_an_imported_ignored_repository_helper_requires_an_explicit_source_pin(tmp_path, monkeypatch):
    path = tmp_path/'ignored-helper.py'
    path.write_text('VALUE = 17\n')
    monkeypatch.setattr(method.current, 'ROOT', tmp_path)
    monkeypatch.setitem(method.sys.modules, 'an_ignored_numeric_helper', SimpleNamespace(__file__=str(path)))
    with pytest.raises(ValueError, match='unbound or changed repository execution source'):
        method.verify_execution_sources({})
    method.verify_execution_sources({'ignored-helper.py': method.current.sha(path)})
