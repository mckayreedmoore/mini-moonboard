"""Mechanics tests for the current reinforced diagnostic, without native solving."""
import numpy as np
import pytest

from fea import horizontal_panel_frame as kernel
from fea import reinforced_frame_demand as subject


def test_beveled_floor_attachment_reproduces_all_rigid_motions():
    structure = kernel.Structure()
    axis = np.array([0., .6, .8])
    record = {'name':'leg','start':[0.,20.,0.], 'end':(axis*1000+[0.,20.,0.]).tolist(),
              'section_u':[1.,0.,0.], 'width_mm':38.1,'depth_mm':139.7}
    structure.member(record,size=300.)
    point = [19.05,100.,0.]
    subject.floor_attachment(structure,'leg',point)
    for translation,rotation in (([1.,2.,3.],[0.,0.,0.]),
                                 ([0.,0.,0.],[.01,.02,.03])):
        displacement={n:np.array(translation)+np.cross(rotation,p) for n,p in structure.nodes.items()}
        for terms in structure.equations:
            assert sum(a*displacement[n][d-1] for n,d,a in terms)==pytest.approx(0.,abs=1.e-9)


def test_floor_friction_tracks_normal_contact_state():
    names={'floor_a','floor_a_friction','floor_b','floor_b_friction','seat_x'}
    assert subject.active_with_friction({'floor_a','seat_x'},names)=={
        'floor_a','floor_a_friction','seat_x'}


def test_scalar_normal_and_installation_axial_force_recovery():
    record={'connection_ownership':{
        'seat':{'first':'wood','second':'steel','point':[0.,0.,0.],
                'scalar_normal':[0.,.6,.8]},
        'bolt':{'first':'wood','second':'steel','point':[0.,0.,0.],
                'axis':[-1.,0.,0.]}}}
    result={'connector_forces':{
        'seat':{'force_on_first_xyz_n':[100.,0.,0.]},
        'bolt':{'force_on_first_xyz_n':[30.,40.,0.]}}}
    rows=subject.physical_forces(record,result)
    assert rows['seat']['force_on_first_xyz_n']==pytest.approx([0.,60.,80.])
    assert rows['seat']['force_on_second_xyz_n']==pytest.approx([0.,-60.,-80.])
    assert rows['bolt']['axial_along_installation_direction_n']==-30.
    assert rows['bolt']['transverse_shear_n']==40.


def test_member_cut_preserves_simultaneous_force_moment_and_equilibrium():
    member={'name':'beam','start':[0.,0.,0.],'end':[0.,0.,1000.],
        'axis':[0.,0.,1.],'section_u':[1.,0.,0.],'section_v':[0.,1.,0.],
        'width_mm':38.1,'depth_mm':139.7,'verification_grain_interval_mm':[0.,1000.]}
    record={'members':[member],'gravity_points':{'beam':{
        'point':[0.,0.,500.],'force':[0.,0.,0.]}}}
    rows={
        'upper':{'first':'beam','second':'other','point':[0.,0.,1000.],
                 'force_on_first_xyz_n':[10.,20.,30.],'force_on_second_xyz_n':[-10.,-20.,-30.]},
        'lower':{'first':'beam','second':'other','point':[0.,0.,0.],
                 'force_on_first_xyz_n':[-10.,-20.,-30.],'force_on_second_xyz_n':[10.,20.,30.]}}
    result=subject.member_sections(record,rows)['beam']
    cut=next(s for s in result['sections'] if s['station_along_grain_mm']==500.
             and not s['include_station_loads'])
    assert cut['axial_n_tension_positive']==30.
    assert cut['shear_u_n']==10.
    assert cut['shear_v_n']==20.
    assert cut['moment_u_nmm']==-10000.
    assert cut['moment_v_nmm']==5000.
    assert result['force_residual_n']==pytest.approx([0.,0.,0.])
    assert result['moment_residual_nmm']==pytest.approx([-20000.,10000.,0.])


def test_foot_shear_stays_when_one_of_its_corners_opens():
    owners={
        'corner0':{'first':'foot','second':'floor'},
        'corner1':{'first':'foot','second':'floor'},
        'floor_foot_friction':{'first':'foot','second':'floor'}}
    assert subject.active_with_friction({'corner1'},set(owners),owners)=={
        'corner1','floor_foot_friction'}
    assert not subject.active_with_friction(set(),set(owners),owners)


def test_foot_friction_certificate_matches_shear_and_yaw():
    points=[{'point_xyz_mm':[x,y,0.],'normal_n':10.} for x in (-1.,1.) for y in (-1.,1.)]
    result=subject.foot_friction_witness(points,[0.,0.,0.],[8.,0.,0.])
    assert result['friction_wrench_feasible']
    assert result['sufficient_friction_coefficient']==pytest.approx(.2)
    assert result['force_xy_and_yaw_residual_n_nmm']==pytest.approx([0.,0.,0.],abs=1.e-10)


def test_friction_certificate_rejects_impossible_eccentric_single_contact():
    result=subject.foot_friction_witness(
        [{'point_xyz_mm':[10.,0.,0.],'normal_n':10.}], [0.,0.,0.],[0.,5.,0.])
    assert not result['friction_wrench_feasible']
    assert result['sufficient_friction_coefficient'] is None


def test_captured_transitive_sources_import_without_live_checkout(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    source = subject.sources()
    assert 'fea/horizontal_frame_stress.py' in source
    assert all(not Path(name).is_absolute() for name in source)
    for name in source:
        target = tmp_path/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(Path(name).read_bytes())
    code = '''
import pathlib, sys
root=pathlib.Path.cwd().resolve()
sys.path.insert(0,str(root))
from fea import reinforced_frame_demand
from mini_moonboard import round_reinforcement_frame
for name,module in list(sys.modules.items()):
    if name.startswith(('fea.','mini_moonboard.')) and getattr(module,'__file__',None):
        assert pathlib.Path(module.__file__).resolve().is_relative_to(root),(name,module.__file__)
assert reinforced_frame_demand.sources()
'''
    result=subprocess.run([sys.executable,'-I','-c',code],cwd=tmp_path,
                           env={**os.environ,'PYTHONPATH':''},capture_output=True,text=True,check=False)
    assert result.returncode == 0, result.stderr


def test_kicker_edge_support_cannot_transmit_horizontal_friction():
    structure=kernel.Structure()
    bottom=[structure.node([x,0.,0.]) for x in (-100.,0.,100.)]
    top=structure.node([0.,0.,225.])
    structure.panels['kicker_left']={'nodes':bottom+[top]}
    owners={}
    subject.add_panel_floor(structure,'kicker_left',owners)
    assert len(owners)==3
    assert all(row['scalar_normal']==[0.,0.,1.] for row in owners.values())
    assert all(s['dof']==1 and s['bearing_closed_assumption'] for s in structure.springs)
    # Scalar auxiliary displacement depends only on the panel's vertical DOF.
    for node in bottom:
        terms=[t for eq in structure.equations for t in eq if t[0]==node]
        assert terms and all(t[1]==3 for t in terms)
