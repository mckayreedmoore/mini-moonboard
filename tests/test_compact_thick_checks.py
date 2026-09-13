"""The compact candidate retains actual group forces and partial-width openings."""
import copy

import pytest

from fea.compact_thick_checks import (
    assess,
    conservative_group_factor,
    hardware_assumptions,
    layout_check,
)
from fea.current_response_resistance import VALIDITY


def fixture():
    report={'candidate':'compact-thick-development',**dict.fromkeys(VALIDITY,True),
        'physical_connection_forces':{},'member_section_demands':{}}
    geometries={}
    members={}
    points=[[0.,-30.,450.],[0.,30.,450.],[0.,0.,520.]]
    for name in ('leg','rim'):
        members[name]={'grain':[0.,0.,1.],'centre_mm':[0.,0.,0.],
            'end_stations_mm':[0.,2000.],'width_mm':88.9,'depth_mm':139.7,
            'bearing_length_mm':88.9,'specific_gravity':.5,'parallel_bearing_psi':5600.,
            'edge_distances_mm':{'grain_positive':150.,'grain_negative':900.,
                'depth_positive':69.85,'depth_negative':69.85},
            'additional_section_boxes':[],'section_cut_boxes':[],'all_openings_represented':True}
        sections=[{'origin_xyz_mm':p,'station_along_grain_mm':p[2],
            'axial_n_tension_positive':-1000.,'moment_u_nmm':100000.,'moment_v_nmm':1000.,
            'shear_u_n':50.,'shear_v_n':100.,'torsion_nmm':0.,'include_station_loads':True} for p in points]
        report['member_section_demands'][name]={'member':{'width_mm':88.9,'depth_mm':139.7,
            'axis':[0.,0.,1.],'section_u':[1.,0.,0.],'section_v':[0.,1.,0.]},
            'length_mm':2000.,'sections':sections}
    for index,(point,demand) in enumerate(zip(points,(100.,300.,600.),strict=True),1):
        name=f'lumber_leg_bolt_left_{index}'
        report['physical_connection_forces'][name]={'first':'leg','second':'rim','point':point,
            'axis':[1.,0.,0.],'force_on_first_xyz_n':[0.,0.,demand],
            'force_on_second_xyz_n':[0.,0.,-demand]}
        geometries[name]={'diameter_mm':12.7,'bending_yield_psi':45000.,'members':copy.deepcopy(members)}
    return report,geometries


def test_three_bolt_group_uses_each_native_force_and_all_net_holes():
    report,geometry=fixture()
    result=assess(report,geometry,hardware_assumptions(),hole_diameter_mm=14.2875)
    bolts=result['bolts']
    assert bolts['lumber_leg_bolt_left_3']['lateral_ratio']==pytest.approx(6*bolts['lumber_leg_bolt_left_1']['lateral_ratio'])
    assert result['groups']['leg']['layout']['noncollinear'] is True
    assert result['groups']['leg']['peak_with_additional_group_reduction']>result['groups']['leg']['peak_individual_lateral_ratio']
    assert result['local']['local_members']['leg']['sampled_net_peak']['active_hole_count']==2
    assert result['qualified_for_design'] is False


def test_root_sensitivity_does_not_reduce_geometric_edge_requirements():
    report,geometry=fixture()
    result=assess(report,geometry,hardware_assumptions(),hole_diameter_mm=14.2875)
    for row in result['bolts'].values():
        assert row['fully_threaded_sensitivity']['lateral_ratio']>row['lateral_ratio']
        assert row['diameter_mm']==12.7
        assert row['placement']['leg']['margins_mm']['grain_positive']==pytest.approx(150.-7*12.7)


def test_group_factor_and_noncollinear_classification():
    member={'grain':[0.,0.,1.],'width_mm':88.9}
    collinear=layout_check([[0.,0.,0.],[0.,0.,70.],[0.,0.,140.]],member,12.7)
    assert collinear['noncollinear'] is False
    assert 0<conservative_group_factor(3,12.7,100.,88.9*139.7)<1
    with pytest.raises(ValueError):
        conservative_group_factor(1,12.7,100.,88.9*139.7)


def test_numerical_gates_remain_prerequisites():
    report,geometry=fixture()
    for key in VALIDITY:
        invalid=dict(report,**{key:False})
        result=assess(invalid,geometry,hardware_assumptions(),hole_diameter_mm=14.2875)
        assert result['status']=='INVALID_RESPONSE_DIAGNOSTIC_ONLY'
        assert 'bolts' not in result
