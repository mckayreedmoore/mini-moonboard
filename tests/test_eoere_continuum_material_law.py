"""Exact constitutive and finite-work controls, without candidate assets."""
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_continuum_material_law as model

WOOD = [F(v) for v in ('11032', '750.176', '551.6', '.292', '.449', '.390', '706.048', '860.496', '77.224')]
IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
ROTATION = [[F(3, 5), -F(4, 5), 0], [F(4, 5), F(3, 5), 0], [0, 0, 1]]


def test_existing_nine_constant_law_has_exact_positive_sylvester_minors_and_reciprocity():
    compliance, minors = model.compliance(WOOD)
    assert all(v > 0 for v in minors)
    assert compliance == model.transpose(compliance)
    assert compliance[0][1] == -WOOD[3]/WOOD[0]
    assert compliance[0][2] == -WOOD[4]/WOOD[0]
    assert compliance[1][2] == -WOOD[5]/WOOD[1]
    assert compliance[0][1] == -F(73, 250000)/F('11.032')


def test_known_longitudinal_stress_reproduces_both_poisson_contractions():
    stress = [WOOD[0]/1000, 0, 0, 0, 0, 0]
    strain, energy = model.complementary_density(stress, WOOD)
    assert strain == [F(1, 1000), -WOOD[3]/1000, -WOOD[4]/1000, 0, 0, 0]
    assert energy == WOOD[0]/2000000


@pytest.mark.parametrize('component,modulus', [(3, 6), (4, 7), (5, 8)])
def test_all_three_engineering_shear_pairs_have_the_correct_work_factor(component, modulus):
    stress = [F(0)]*6; stress[component] = WOOD[modulus]/100
    strain, energy = model.complementary_density(stress, WOOD)
    expected = [F(0)]*6; expected[component] = F(1, 100)
    assert strain == expected and energy == WOOD[modulus]/20000
    # Engineering shear 1/100 means tensor strain 1/200.
    assert stress[component]*F(1, 200) == energy


def test_radial_and_tangential_reference_compliances_remain_distinct():
    _, radial = model.complementary_density([0, 1, 0, 0, 0, 0], WOOD)
    _, tangential = model.complementary_density([0, 0, 1, 0, 0, 0], WOOD)
    assert radial == 1/(2*WOOD[1]) and tangential == 1/(2*WOOD[2])
    assert radial < tangential


def test_rigid_rotation_has_zero_green_strain_without_a_small_angle_approximation():
    assert model.determinant(ROTATION) == 1
    assert model.green_strain(ROTATION) == [0]*6
    value, residual = model.mixed_density(ROTATION, [0]*6, WOOD)
    assert value == 0 and residual == [0]*6


def test_known_compatible_uniaxial_state_has_positive_physical_energy_and_correct_stress_measures():
    constants = [1000]*3+[0]*3+[500]*3
    deformation = [[F(101, 100), 0, 0], [0, 1, 0], [0, 0, 1]]
    green = F(201, 20000); stress = [1000*green, 0, 0, 0, 0, 0]
    value, residual = model.mixed_density(deformation, stress, constants)
    assert residual == [0]*6 and value == 500*green**2
    assert model.first_piola(deformation, stress)[0][0] == F(101, 100)*stress[0]
    assert model.cauchy_stress(deformation, stress)[0][0] == F(101, 100)*stress[0]


def test_nonstationary_mixed_value_is_not_mislabelled_as_physical_strain_energy():
    value, residual = model.mixed_density(IDENTITY, [1, 0, 0, 0, 0, 0], WOOD)
    assert value < 0 and any(residual)


def test_superposed_spatial_rotation_preserves_material_strain_and_work():
    deformation = [[F(101, 100), F(1, 100), 0], [0, F(999, 1000), F(1, 100)], [F(1, 200), 0, 1]]
    rotated = model.multiply(ROTATION, deformation); stress = [2, -3, 5, 7, -11, 13]
    assert model.green_strain(rotated) == model.green_strain(deformation)
    assert model.mixed_density(rotated, stress, WOOD) == model.mixed_density(deformation, stress, WOOD)
    assert model.first_piola(rotated, stress) == model.multiply(ROTATION, model.first_piola(deformation, stress))
    expected = model.multiply(model.multiply(ROTATION, model.cauchy_stress(deformation, stress)), model.transpose(ROTATION))
    assert model.cauchy_stress(rotated, stress) == expected


def test_exact_directional_work_matches_all_nine_first_piola_components():
    deformation = [[F(101, 100), F(1, 100), 0], [0, F(999, 1000), F(1, 100)], [F(1, 200), 0, 1]]
    stress = [2, -3, 5, 7, -11, 13]; step = F(1, 10**8)
    piola = model.first_piola(deformation, stress)
    for i in range(3):
        for j in range(3):
            plus, minus = [list(r) for r in deformation], [list(r) for r in deformation]
            plus[i][j] += step; minus[i][j] -= step
            difference = model.mixed_density(plus, stress, WOOD)[0]-model.mixed_density(minus, stress, WOOD)[0]
            assert difference/(2*step) == piola[i][j]


@pytest.mark.parametrize('change', ['zero_E', 'negative_G', 'bad_poisson', 'boolean', 'short'])
def test_inadmissible_material_constants_are_refused(change):
    constants = list(WOOD)
    if change == 'zero_E': constants[0] = 0
    if change == 'negative_G': constants[-1] = -1
    if change == 'bad_poisson': constants[3:6] = [99]*3
    if change == 'boolean': constants[0] = True
    if change == 'short': constants.pop()
    with pytest.raises(ValueError):
        model.compliance(constants)


@pytest.mark.parametrize('deformation', [[[0, 0, 0], [0, 1, 0], [0, 0, 1]],
    [[-1, 0, 0], [0, 1, 0], [0, 0, 1]], [[1, 0], [0, 1]]])
def test_singular_inverted_or_malformed_deformations_are_refused(deformation):
    for function in (model.green_strain, lambda f: model.cauchy_stress(f, [0]*6)):
        with pytest.raises(ValueError):
            function(deformation)


def test_literal_material_read_does_not_execute_unrelated_source_code():
    source = 'raise RuntimeError("do not execute")\nSCENARIO_CONSTANTS_MPA=(11032,750.176,551.6,.292,.449,.390,706.048,860.496,77.224)'
    assert model.literal_constants(source) == WOOD


def test_recorded_material_frames_keep_grain_and_use_a_right_handed_transverse_swap():
    row = {'name': 'synthetic', 'axis': [0, 1, 0], 'section_u': [1, 0, 0], 'section_v': [0, 0, -1]}
    result = model.material_frames(row)
    assert result['source_frame_lrt'][0] == result['swapped_frame_lrt'][0]
    assert model.determinant(result['source_frame_lrt']) == model.determinant(result['swapped_frame_lrt']) == 1
    assert result['growth_ring_orientation_observed'] is False


@pytest.mark.parametrize('change', ['left_handed', 'parallel', 'nonunit'])
def test_incompatible_source_material_frames_are_refused(change):
    row = {'name': 'synthetic', 'axis': [0, 1, 0], 'section_u': [1, 0, 0], 'section_v': [0, 0, -1]}
    if change == 'left_handed': row['section_v'] = [0, 0, 1]
    if change == 'parallel': row['section_v'] = [1, 0, 0]
    if change == 'nonunit': row['axis'] = [0, 2, 0]
    with pytest.raises(ValueError):
        model.material_frames(row)


def test_bootstrap_ignores_an_unbound_module_cache_and_rejects_conflicting_pins(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'scripts.eoere_mixed_shaft_projection_limit', SimpleNamespace(bootstrap=None))
    assert callable(model.bootstrap({}).bootstrap)
    with pytest.raises(ValueError, match='bootstrap changed'):
        model.bootstrap({model.BOOT['path']: '0'*64})
