import math

import pytest

from scripts.floor_taper_checks import notch_factor, rectangular_shear


def test_torque_centroid_translation_cannot_cancel_native_torsion():
    value = rectangular_shear(50.8,139.7,40,-100,2000,centroid_u_mm=19.05)
    assert value['retained_centroid_torque_bound_nmm'] == pytest.approx(3905)
    assert value['torsional_shear_bound_mpa'] == pytest.approx(5*3905/(139.7*50.8**2))
    assert value['combined_shear_ratio'] > value['transverse_shear_mpa']/value['unreduced_asd_shear_reference_mpa']


def test_shear_and_torsion_reference_does_not_receive_shape_increase():
    value = rectangular_shear(50.8,139.7,0,100,10000,reduction=.5)
    full = rectangular_shear(50.8,139.7,0,100,10000)
    assert value['combined_shear_ratio'] == pytest.approx(2*full['combined_shear_ratio'])
    assert value['unreduced_asd_shear_reference_mpa'] == pytest.approx(180*.006894757293168361)


def test_notch_factor_penalizes_support_offset():
    assert 0 < notch_factor(88.9,50.8,457.2,1000) < notch_factor(88.9,50.8,457.2,0) <= 1


@pytest.mark.parametrize('args',[(88.9,88.9,457.2,0),(88.9,50.8,0,0),(88.9,50.8,457.2,-1),(math.nan,50.8,457.2,0)])
def test_notch_invalid_geometry_rejected(args):
    with pytest.raises(ValueError):
        notch_factor(*args)


def test_actual_floor_contacts_are_not_mistaken_for_bolt_bores():
    import gzip
    import json
    from pathlib import Path

    from scripts.floor_taper_checks import checks

    archive = Path(__file__).resolve().parents[1]/'fea/results/clear-space-floortaper/a12-rear'
    report = json.loads(gzip.decompress((archive/'report.json.gz').read_bytes()))
    geometry = json.loads((archive/'geometry.json').read_text())
    assert 'floor_lumber_leg_left_0' in report['physical_connection_forces']
    assert 'floor_lumber_leg_left_0' not in geometry['hardware_by_name']
    result = checks(report, geometry)
    assert result['passes']
    assert all(member['criteria']['taper_region_unbored_torsion_applicable']
               for member in result['members'].values())


def test_no_slip_uses_leg_normal_cells_not_missing_coulomb_tangent_cells():
    from scripts.floor_taper_checks import leg_floor_points

    report = {'parameters': {}, 'physical_connection_forces': {
        'normal': {'first': 'lumber_leg_left', 'second': 'floor',
                   'scalar_normal': [0., 0., 1.], 'point': [1., 2., 0.]},
        'tangent': {'first': 'lumber_leg_left', 'second': 'floor',
                    'point': [3., 4., 0.]},
    }}
    assert leg_floor_points(report, 'lumber_leg_left') == [[1., 2., 0.]]
    report['parameters']['floor_friction_assumption'] = {'mu': .4}
    with pytest.raises(ValueError, match='lacks tangent-cell geometry'):
        leg_floor_points(report, 'lumber_leg_left')
