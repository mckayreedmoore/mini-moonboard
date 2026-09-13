"""Section-integral and constitutive checks without rebuilding CAD."""
import numpy as np
import pytest

from fea.current_response_materials import (
    APA_EA,
    APA_EI,
    APA_GA,
    connection_stiffnesses,
    equivalent_layers,
    materials,
    validate_constants,
)


@pytest.mark.parametrize('thickness', [19.05, 23/32*25.4])
@pytest.mark.parametrize('factor', [1., .56])
def test_symmetric_section_reproduces_independent_axial_bending_and_shear(thickness, factor):
    material = materials(thickness, factor)
    axial, bending, coupling = np.zeros(2), np.zeros(2), np.zeros(2)
    shear = 0.
    z = -thickness/2
    for layer in material['panel_layers']:
        upper = z+layer['thickness_mm']
        constants = layer['constants']
        validate_constants(constants)
        e = np.array(constants[:2])
        axial += e*(upper-z)
        bending += e*(upper**3-z**3)/3
        coupling += e*(upper**2-z**2)/2
        shear += constants[6]*(upper-z)
        z = upper
    assert axial == pytest.approx(np.array(APA_EA)*factor)
    assert bending == pytest.approx(np.array(APA_EI)*factor)
    assert coupling == pytest.approx([0., 0.], abs=1.e-8)
    assert shear == pytest.approx(APA_GA*factor)
    assert z == pytest.approx(thickness/2)
    validate_constants(material['timber'])
    assert material['panel_targets']['ea_n_per_mm'][1] > material['panel_targets']['ea_n_per_mm'][0]


def test_impossible_positive_section_fit_is_rejected():
    with pytest.raises(ValueError, match='cannot be fitted'):
        equivalent_layers(1., ea=(1., 1.), ei=(1., 1.))


def test_nonpositive_constitutive_tensor_is_rejected():
    with pytest.raises(ValueError, match='positive definite'):
        validate_constants((1., 1., 1., .9, .9, .9, 1., 1., 1.))


def test_shear_and_axial_stiffness_follow_distinct_published_dependencies():
    base = connection_stiffnesses()
    longer = connection_stiffnesses(panel_thread_mm=60.)
    assert base['bolt']['lateral_n_per_mm'] == pytest.approx(4630.119015366413)
    assert base['panel']['effective_thread_mm'] == pytest.approx(31.496-2*4.1402)
    assert base['sds']['effective_thread_mm'] == pytest.approx(12.7)
    assert longer['panel']['axial_n_per_mm'] > base['panel']['axial_n_per_mm']
    assert base['bolt']['axial_n_per_mm'] < base['bolt']['axial_series_components_n_per_mm']['first_wood_seat']
    assert longer['panel']['lateral_n_per_mm'] == base['panel']['lateral_n_per_mm']
    assert not base['panel']['qualified_for_design']
