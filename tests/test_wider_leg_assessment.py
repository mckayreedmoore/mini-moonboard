import json
from pathlib import Path

import pytest

from fea.leg_attachment_check import LEG
from fea.wider_leg_assessment import placement, planar_forces, six_group_factor


def current_points():
    cad=json.loads(Path('docs/wider-leg-review/review.json').read_text())
    points=[[0,r['world_y_mm'],r['world_z_mm']] for r in cad['drilling'] if r['member']=='lumber_leg_left']
    return cad,points


def test_six_bolt_force_and_moment_equilibrium():
    _,points=current_points()
    forces=planar_forces(points,4200,-130000)
    centre=[sum(p[i] for p in points)/6 for i in range(3)]
    assert sum(f[1] for f in forces)==pytest.approx(4200*LEG[1])
    assert sum(f[2] for f in forces)==pytest.approx(4200*LEG[2])
    moment=sum((p[1]-centre[1])*f[2]-(p[2]-centre[2])*f[1] for p,f in zip(points,forces,strict=True))
    assert moment==pytest.approx(-130000)


def test_actual_loaded_rear_rim_edge_fails():
    cad,points=current_points()
    result=placement(cad,planar_forces(points,4200,-130000))
    assert not result['passes']
    bolt5=next(r for r in result['witnesses'] if r['member']=='base_side_left' and r['bolt']==5)
    assert bolt5['positive_depth_force_n']>0
    assert bolt5['minimum_margin_mm']==pytest.approx(38.045006360209584-50.8)


def test_group_reduction_is_not_equal_sharing_capacity():
    assert six_group_factor()==pytest.approx(.9509,abs=.0001)


def test_aggregate_transports_moment_to_leg_centerline():
    report=json.loads(Path('fea/results/wider-leg-assessment.json').read_text())
    offset=report['joint_depth_offset_mm']
    assert abs(offset)==pytest.approx(3.2797846727,abs=1e-6)
    for scope in report['pressure_scopes'].values():
        for case in scope['governing_cases']:
            assert case['member_moment_input_nmm']==pytest.approx(
                abs(case['joint_moment_nmm'])+case['compression_n']*abs(offset))
