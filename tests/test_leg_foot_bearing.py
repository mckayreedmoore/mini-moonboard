"""Foot bearing uses actual area/grain and rejects incomplete contact evidence."""
import pytest

from scripts.leg_foot_bearing import CANDIDATE, leg_foot_bearing_check


def fixture(n=3):
    gy,gz = -0.23915183196324324,0.9709821838059775
    report = {'candidate':CANDIDATE, 'parameters':{'leg_floor_grid':n},
              'physical_connection_forces':{}, 'bearings':[]}
    geometry = {'members':{}}
    for side,x in [('left',-1200.),('right',1200.)]:
        name = 'lumber_leg_'+side
        profile = [[(-1000+gy*q)/gz,q] for q in (-69.85,69.85)]
        profile += [[1000.,q] for q in (-69.85,69.85)]
        geometry['members'][name] = {'grain':[0.,gy,gz], 'centre_mm':[x,0.,1000.],
            'width_mm':88.9,'depth_mm':139.7,'profile_sq_mm':profile,'opening_records':[]}
        ymin = min(gy*s+gz*q for s,q in profile[:2])
        for i in range(n*n):
            key = f'floor_{name}_{i}'
            force = 2749.8204444444445 if i == 0 else 0.
            report['physical_connection_forces'][key] = {'first':name,'second':'floor',
                'point':[x-88.9/2+(i%n+.5)*88.9/n, ymin+(i//n+.5)*139.7/gz/n,0.],
                'scalar_normal':[0.,0.,1.], 'normal_stiffness_fraction':1/n**2,
                'force_on_first_xyz_n':[0.,0.,force]}
            report['bearings'].append({'name':key,'active':i==0,'compression_force_n':force})
    return report,geometry


@pytest.mark.parametrize('n,ratio', [(3,.2038517926294047),(5,.5662549795261241)])
def test_actual_angle_and_grid_pressure(n,ratio):
    result = leg_foot_bearing_check(*fixture(n))
    assert result['passed']
    assert result['peak_ratio'] == pytest.approx(ratio)
    row = result['cells']['floor_lumber_leg_left_0']
    assert row['angle_to_grain_deg'] == pytest.approx(13.8364862168)
    assert row['adjusted_bearing_mpa'] == pytest.approx(9.4917306428)
    if n == 5:
        assert row['perpendicular_625psi_screen_ratio'] > 1.
    assert len(result['cells']) == 2*n*n


@pytest.mark.parametrize('defect', ['missing','duplicate_position','fraction','offset','normal','force','notch','grid'])
def test_reject_invalid_geometry_or_inventory(defect):
    report,geometry = fixture()
    rows = report['physical_connection_forces']
    row = rows['floor_lumber_leg_left_0']
    if defect == 'missing': del rows['floor_lumber_leg_left_0']
    elif defect == 'duplicate_position': row['point'] = rows['floor_lumber_leg_left_1']['point'][:]
    elif defect == 'fraction': row['normal_stiffness_fraction'] = .5
    elif defect == 'offset': row['point'][0] += 1.
    elif defect == 'normal': row['scalar_normal'] = [1.,0.,0.]
    elif defect == 'force': row['force_on_first_xyz_n'][2] += 1.
    elif defect == 'notch': geometry['members']['lumber_leg_left']['opening_records'] = [{'kind':'tab_notch'}]
    elif defect == 'grid': report['parameters']['leg_floor_grid'] = 5
    with pytest.raises(ValueError): leg_foot_bearing_check(report,geometry)


def test_normal_overload_fails_without_using_tangent_force_as_bearing():
    report,geometry = fixture()
    row = report['physical_connection_forces']['floor_lumber_leg_left_0']
    row['force_on_first_xyz_n'][2] *= 6
    report['bearings'][0]['compression_force_n'] *= 6
    result = leg_foot_bearing_check(report,geometry)
    assert not result['passed']
    assert result['peak_ratio'] > 1.
