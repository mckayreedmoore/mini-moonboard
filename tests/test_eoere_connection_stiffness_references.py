"""Units, series compliance, tensor normalization and source-identity controls."""
import copy
import math

import numpy as np
import pytest

from scripts import eoere_connection_stiffness_references as refs


def inputs():
    return refs.current.read(refs.current.ref(refs.INPUT))


def test_current_three_eighth_inch_service_and_group_references_have_correct_units():
    assert refs.ec5_slip(9.525, 500.) == pytest.approx(4630.119, abs=.001)
    assert refs.ec5_slip(9.525, 500.)/refs.ec5_slip(6.35, 500.) == pytest.approx(1.5)
    assert refs.nds_group_slip(9.525) == pytest.approx(180000*.375**1.5*4.4482216152605/25.4)
    assert refs.nds_group_slip(9.525)/refs.nds_group_slip(6.35) == pytest.approx(1.5**1.5)


def test_axial_stiffness_is_area_scaled_and_length_inverted_and_captures_dominate_series():
    assert refs.steel_axial(10., 200000., 100.) == pytest.approx(50000*math.pi)
    assert refs.steel_axial(5., 200000., 100.)/refs.steel_axial(10., 200000., 100.) == .25
    assert refs.steel_axial(10., 200000., 200.)/refs.steel_axial(10., 200000., 100.) == .5
    assert refs.series(1000., 1000., 100000.) == pytest.approx(1./.00201)
    assert 0. < refs.series(1000., 1000., 100000.) < 500.


@pytest.mark.parametrize('value', [0., -1., np.nan, np.inf])
def test_invalid_scalar_inputs_cannot_create_finite_stiffness(value):
    for function, args in ((refs.ec5_slip, (value, 500.)), (refs.nds_group_slip, (value,)),
                           (refs.steel_axial, (10., 200000., value)), (refs.series, (1000., value))):
        with pytest.raises(ValueError):
            function(*args)


def test_series_path_and_nds_domain_are_not_extrapolated():
    with pytest.raises(ValueError):
        refs.series()
    with pytest.raises(ValueError):
        refs.nds_group_slip(4.)


def test_kelvin_enclosure_has_exact_isotropic_eigenvalues_and_encloses_rotated_uniaxial_modulus():
    e, nu = 1000., .25
    s = np.eye(6)/e
    s[:3, :3] = -nu/e
    np.fill_diagonal(s[:3, :3], 1./e)
    for i in range(3, 6):
        s[i, i] = 2*(1+nu)/e
    low, high = refs.normal_modulus_enclosure(s)
    assert [low, high] == pytest.approx([e/(1+nu), e/(1-2*nu)])
    n = np.array([1., 2., 3.])/math.sqrt(14.)
    stress = np.array([*n**2, n[0]*n[1], n[0]*n[2], n[1]*n[2]])
    actual = 1./(stress@s@stress)
    assert actual == pytest.approx(e) and low <= actual <= high


def test_current_scenario_bound_covers_all_principal_and_oblique_directions():
    s = np.array(refs.materials.material_scenario()['compliance_matrix_mpa_inv'])
    low, high = refs.normal_modulus_enclosure(s)
    assert low == pytest.approx(2*77.224)
    for n in ([1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [1., 2., 3.], [0., 1., 1.]):
        n = np.array(n)/np.linalg.norm(n)
        stress = np.array([*n**2, n[0]*n[1], n[0]*n[2], n[1]*n[2]])
        assert low <= 1./(stress@s@stress) <= high


@pytest.mark.parametrize('change', ['shape', 'asymmetric', 'nonfinite', 'indefinite'])
def test_invalid_compliance_is_refused(change):
    s = np.eye(6)
    if change == 'shape':
        s = s[:5]
    elif change == 'asymmetric':
        s[0, 1] = .1
    elif change == 'nonfinite':
        s[0, 0] = np.nan
    else:
        s[0, 0] = -1.
    with pytest.raises(ValueError):
        refs.normal_modulus_enclosure(s)


def shaft_fixture():
    surface = {'host': 'ownwood', 'kind': 'wood', 'interval_mm': [0., 38.1]}
    ends = [{'end': 'head', 'pressure_face_s_mm': -2.}, {'end': 'nut', 'pressure_face_s_mm': 42.}]
    shaft = {'axis_id': 'ownbolt', 'diameter_mm': 9.525, 'bore_diameter_mm': 10.31875,
             'ends': ends, 'surfaces': [surface]}
    descriptors = [{'kind': 'shaft_end_capture', 'axis_id': 'ownbolt', 'end': end, 'stiffness': 1000.} for end in ends]
    descriptors += [{'kind': 'common_shaft_bearing', 'axis_id': 'ownbolt', 'surface_index': 0,
                     'surface': surface, 'weight_length_mm': 19.05, 'kl': 500.} for _ in range(2)]
    return shaft, descriptors


def test_reference_keeps_own_lengths_and_does_not_promote_any_scalar_to_joint_stiffness():
    row = refs.shaft_reference(*shaft_fixture(), inputs())
    assert row['own_pressure_face_distance_mm'] == 44.
    assert row['centered_one_sided_clearance_mm'] == pytest.approx(.396875)
    assert row['own_wood_foundations'][0]['integrated_uniform_translation_foundation_n_mm'] == 1000.
    assert len(row['EC5_wood_dowel_service_reference_n_mm']) == 4
    assert row['NDS_wood_to_wood_group_action_gamma_n_mm'] is None  # One-member fixture is outside that scope.
    assert row['physical_axial_or_lateral_stiffness_qualified'] is False
    assert row['length_is_delivered_free_bolt_length'] is False
    assert row['EC5_reference_is_current_complete_joint_stiffness'] is False
    assert row['own_wood_foundations'][0]['foundation_is_complete_joint_slip_modulus'] is False


def test_half_inch_starting_leg_bolt_uses_its_own_9p9949_mm_root_and_slip_reference():
    shaft, descriptors = shaft_fixture()
    shaft.update(diameter_mm=12.7, bore_diameter_mm=13.49375)
    row = refs.shaft_reference(shaft, descriptors, inputs())
    assert row['nominal_diameter_mm'] == 12.7 and row['own_purchase_reference_root_floor_mm'] == 9.9949
    assert row['steel_only_axial_n_mm']['full_root_sensitivity'] == pytest.approx(
        205000*math.pi*9.9949**2/(4*44))
    assert row['EC5_wood_dowel_service_reference_n_mm'][2]['Kser_n_mm'] == pytest.approx(6173.492, abs=.001)
    assert row['centered_one_sided_clearance_mm'] == pytest.approx(.396875)


def source_shaped_inventory():
    rows = []
    for kinds, count in ((['steel', 'wood'], 76), (['wood', 'wood'], 16),
                         (['steel', 'steel', 'wood'], 4), (['steel', 'wood', 'wood'], 4)):
        rows.extend({'bearing_member_kinds': kinds, 'own_wood_foundations': [None]*kinds.count('wood'),
                     'NDS_wood_to_wood_group_action_gamma_n_mm': 7000. if kinds == ['wood', 'wood'] else None}
                    for _ in range(count))
    return rows


def test_current_bearing_inventory_is_distinct_from_the_112_wood_washer_seats():
    census = refs.bearing_census(source_shaped_inventory())
    assert census['physical_bolts'] == 100
    assert census['wood_bearing_occurrences'] == 120 and census['wood_quadrature_samples'] == 240
    assert census['ordinary_wood_to_wood_gamma_references'] == 16


@pytest.mark.parametrize('change', ['washer_census', 'missing_bolt', 'mixed_gamma', 'family'])
def test_changed_or_confused_bearing_census_is_rejected(change):
    rows = copy.deepcopy(source_shaped_inventory())
    if change == 'washer_census':
        for row in rows[76:84]:
            row['own_wood_foundations'].pop()
    elif change == 'missing_bolt':
        rows.pop()
    elif change == 'mixed_gamma':
        rows[-1]['NDS_wood_to_wood_group_action_gamma_n_mm'] = 7000.
    else:
        rows[-1]['bearing_member_kinds'] = ['wood', 'wood', 'wood']
    with pytest.raises(ValueError, match='census'):
        refs.bearing_census(rows)


@pytest.mark.parametrize('change', ['end', 'missing_capture', 'foreign_capture', 'capture_law',
                                  'missing_quadrature', 'foreign_surface', 'coverage', 'foundation', 'bore'])
def test_wrong_source_end_surface_or_spring_cannot_enter_the_scalar_reference(change):
    shaft, descriptors = copy.deepcopy(shaft_fixture())
    if change == 'end':
        shaft['ends'][1]['end'] = 'head'
    elif change == 'missing_capture':
        descriptors.pop(0)
    elif change == 'foreign_capture':
        descriptors[0]['axis_id'] = 'other'
    elif change == 'capture_law':
        descriptors[0]['stiffness'] = 2000.
    elif change == 'missing_quadrature':
        descriptors.pop()
    elif change == 'foreign_surface':
        descriptors[-1]['surface'] = {**descriptors[-1]['surface'], 'host': 'other'}
    elif change == 'coverage':
        descriptors[-1]['weight_length_mm'] = 1.
    elif change == 'foundation':
        descriptors[-1]['kl'] = 1000.
    else:
        shaft['bore_diameter_mm'] = 9.
    with pytest.raises(ValueError):
        refs.shaft_reference(shaft, descriptors, inputs())


@pytest.mark.parametrize('key,value', [('structural_acceptance', True), ('physical_demand_bounds_established', True),
                                    ('actual_observations', 'assumed'), ('current_bolt_count', 102),
                                    ('mean_density_sensitivities_kg_m3', [500.]), ('steel_modulus_mpa', 200000.),
                                    ('purchase_root_floors_by_nominal_diameter_mm', {'9.525': 7.31774})])
def test_frozen_scope_and_unobserved_hypotheses_are_enforced(key, value):
    data = inputs()
    refs.validate(data)
    data[key] = value
    with pytest.raises(ValueError):
        refs.validate(data)
