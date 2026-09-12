import pytest

from fea.wider_leg_wood_checks import (
    joint_local_checks,
    member_net_check,
    section_envelope,
)


def test_staggered_overlapping_holes_remove_two_strips():
    sections=section_envelope([(0,-30,14),(10,30,14)],depth_mm=184.15)
    assert min(s['area_mm2'] for s in sections)==pytest.approx(38.1*(184.15-28))
    isolated=section_envelope([(0,-30,14),(20,30,14)],depth_mm=184.15)
    assert min(s['area_mm2'] for s in isolated)==pytest.approx(38.1*(184.15-14))


def test_hole_union_and_centroid():
    sections=section_envelope([(0,20,14),(0,20,14)])
    s=min(sections,key=lambda v:v['area_mm2'])
    assert s['centroid_mm']==pytest.approx(-14*20/(184.15-14))
    assert s['area_mm2']==pytest.approx(38.1*(184.15-14))


def test_net_member_monotonic_in_moment():
    args={'holes_sq_d':[(0,-30,14.2875),(10,30,14.2875)],'effective_length_mm':1650,
          'mass_kg':8,'axis_vertical_cosine':.9655662054}
    low=member_net_check(4000,0,**args)
    high=member_net_check(4000,200000,**args)
    assert high['peak_interaction']>low['peak_interaction']


def test_parallel_rows_and_directional_splitting():
    points=[(0,q,s) for q in (-30,30) for s in (-66,0,66)]
    forces=[(0,100,500)]*6
    args={'grain':(0,0,1),'centre':(0,0,0),'end_stations_mm':(-1000,250)}
    result=joint_local_checks(points,forces,**args)
    assert len(result['rows'])==2
    assert all(r['critical_spacing_mm']==66 for r in result['rows'])
    assert result['splitting'][0]['demand_n']==0
    assert result['splitting'][1]['demand_n']==900
    assert result['splitting'][0]['resistance_n']==pytest.approx(result['splitting'][1]['resistance_n'])
    reverse=joint_local_checks(points,[(0,-100,-500)]*6,**args)
    assert reverse['parallel_peak_ratio']==pytest.approx(result['parallel_peak_ratio'])
    assert reverse['splitting_peak_ratio']==pytest.approx(result['splitting_peak_ratio'])


def test_edge_crossing_hole_rejected():
    with pytest.raises(ValueError):
        section_envelope([(0,90,14)])


def test_permanent_duration_reduces_wood_resistance():
    args={'holes_sq_d':[(0,-30,14.2875)],'effective_length_mm':1641,
          'mass_kg':7.7,'axis_vertical_cosine':.9655662054}
    normal=member_net_check(2000,70000,**args)
    permanent=member_net_check(2000,70000,duration_factor=.9,**args)
    assert permanent['peak_interaction']>normal['peak_interaction']
    points=[(0,q,s) for q in (-30,30) for s in (-66,0,66)]
    kwargs={'grain':(0,0,1),'centre':(0,0,0),'end_stations_mm':(-1000,250)}
    a=joint_local_checks(points,[(0,100,500)]*6,**kwargs)
    b=joint_local_checks(points,[(0,100,500)]*6,duration_factor=.9,**kwargs)
    assert b['parallel_peak_ratio']==pytest.approx(a['parallel_peak_ratio']/.9)
