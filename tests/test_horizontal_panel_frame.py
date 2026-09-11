"""Native-member interpolation preserves rigid motion and load resultants."""
import numpy as np
import pytest

from fea import horizontal_panel_frame as frame


def test_quadratic_section_reproduces_rigid_offset_motion():
    model,basis=frame.cantilever_coupon()
    shift=np.array([.1,.2,.3]);rotation=np.array([.002,-.001,.003])
    field={n:shift+np.cross(rotation,xyz) for n,xyz in model.nodes.items()}
    for terms in model.equations:
        assert sum(value*field[node][dof-1] for node,dof,value in terms)==pytest.approx(0,abs=1e-12)
    assert len(model.elements)==20
    assert all(len(ids)==20 for _,ids,_ in model.elements.values())
    assert np.allclose(model.nodes[basis['tip_node']],[0,20,1000])


def test_noncoincident_spring_is_rejected_instead_of_resisting_rigid_rotation():
    model=frame.Structure();a=model.node([0,0,0]);b=model.node([0,0,1])
    with pytest.raises(ValueError,match='Coincident'):
        model.spring(a,b,1000,'bad')


def test_wrench_distribution_preserves_resultants_and_rigid_virtual_work():
    points=np.array([[0,0,0],[2,0,0],[2,3,0],[0,3,0]],float)
    force=np.array([12,-4,30]);moment=np.array([3,7,-2]);centre=np.array([.3,.8,1])
    values=frame.distribute_wrench(points,force,moment,centre,[1,2,3,4])
    assert np.sum(values,axis=0)==pytest.approx(force)
    assert np.sum(np.cross(points-centre,values),axis=0)==pytest.approx(moment)
    shift=np.array([1,2,3]);rotation=np.array([.1,-.2,.3])
    displacement=shift+np.cross(rotation,points-centre)
    assert np.sum(values*displacement)==pytest.approx(force@shift+moment@rotation)
    with pytest.raises(ValueError,match='cannot transfer'):
        frame.distribute_wrench([[0,0,0],[1,0,0],[2,0,0]],force,moment,centre)


def test_rigid_angle_master_equations_preserve_all_six_motion_modes():
    model=frame.Structure()
    points=np.array([[0,0,0],[0,2,0],[2,0,0],[0,0,2],[2,0,2],[0,2,2]],float)
    model.rigid_angle('clip',points)
    shift=np.array([.1,.2,.3]);rotation=np.array([.002,-.001,.003])
    centre=np.mean(points,axis=0)
    field={n:shift+np.cross(rotation,np.array(xyz)-centre) for n,xyz in model.nodes.items()}
    field[1]=shift;field[2]=rotation
    for terms in model.equations:
        assert sum(value*field[node][dof-1] for node,dof,value in terms)==pytest.approx(0,abs=1e-12)


def test_bearing_audit_rejects_tension_and_catches_unbalanced_output(monkeypatch):
    model=frame.Structure();a=model.node([0,0,0]);b=model.node([0,0,0])
    model.spring(a,b,1000,'bearing',dofs=(3,),bearing=True)
    model.fixed.add(b);model.loads[a]=[0,0,1]
    data={'displacements':{a:[0,0,.001],b:[0,0,0]},'forces':{a:[0,0,1],b:[0,0,-1]}}
    monkeypatch.setattr(frame.panel_kernel,'read_blocks',lambda _:data)
    result=frame.assess(frame.record_structure(model,{}),'')
    assert result['global_equilibrium_passed']
    assert not result['closed_bearing_assumption_passed']
    assert not result['qualified_for_design']
    data['forces'][b][2]=0
    assert not frame.assess(frame.record_structure(model,{}),'')['global_equilibrium_passed']


def test_uniform_traction_retains_negative_corner_shape_integrals():
    nodes,elements,_=frame.panel_kernel.grid([0.,20.],[0.,20.])
    weights,_=frame.panel_kernel.pressure_load(nodes,elements,(0.,20.,0.,20.),1.)
    positions=[nodes[n] for n in weights]
    force=np.array([1.,2.,3.]);centre=np.array([10.,10.,0.])
    result=frame.traction_wrench(positions,list(weights.values()),force,[0,0,0],centre)
    assert result==pytest.approx(np.asarray(list(weights.values()))[:,None]*force)
    assert result[0,2]<0
    moment=np.array([10.,20.,30.])
    result=frame.traction_wrench(positions,list(weights.values()),force,moment,centre)
    assert result.sum(axis=0)==pytest.approx(force)
    assert np.cross(np.asarray(positions)-centre,result).sum(axis=0)==pytest.approx(moment)


def test_unilateral_bearing_update_removes_tension_and_reactivates_penetration():
    rows=[{'name':'tension','active':True,'opening_mm':.001},
          {'name':'compression','active':True,'opening_mm':-.001},
          {'name':'gap','active':False,'opening_mm':.1},
          {'name':'penetration','active':False,'opening_mm':-.01}]
    assert frame.next_bearing_set(rows)=={'compression','penetration'}


def test_inactive_bearing_omits_native_element_and_recovers_zero_force(monkeypatch):
    model=frame.Structure();a=model.node([0,0,0]);b=model.node([0,0,0])
    model.spring(a,b,1000,'bearing',dofs=(3,),bearing=True)
    assert '*ELEMENT,TYPE=SPRING2' in model.deck()
    assert '*ELEMENT,TYPE=SPRING2' not in model.deck(active_bearings=set())
    data={'displacements':{a:[0,0,.1],b:[0,0,0]},'forces':{a:[0,0,0],b:[0,0,0]}}
    monkeypatch.setattr(frame.panel_kernel,'read_blocks',lambda _:data)
    record=frame.record_structure(model,{},set())
    result=frame.assess(record,'')
    assert result['closed_bearing_assumption_passed']
    assert result['bearings'][0]['compression_force_n']==0
    data['displacements'][a][2]=-.1
    assert not frame.assess(record,'')['closed_bearing_assumption_passed']


@pytest.mark.parametrize('name', ['led-wiring-reference.json','ml24z-reference.json',
                                  'panel-insert-reference.json','ml23z-reference.json'])
def test_runtime_reference_mutation_changes_authenticated_source_closure(monkeypatch,name):
    from pathlib import Path
    expected='docs/'+name
    original=frame.source_hashes()
    assert expected in original
    read=Path.read_bytes
    def changed(path):
        value=read(path)
        return value+b'\n' if path.resolve()==Path(expected).resolve() else value
    monkeypatch.setattr(Path,'read_bytes',changed)
    updated=frame.source_hashes()
    assert {k for k in original if original[k]!=updated[k]}=={expected}


def test_mpc_uses_actual_token_precision_and_does_not_hide_excess_residual():
    data=' displacements (vx,vy,vz) for set ALLN\n\n1 1.000000E+01 0.000000E+00 0.000000E+00\n2 1.000001E+01 0.000000E+00 0.000000E+00\n'
    roundoff=frame.displacement_roundoff(data)
    assert roundoff[1][0]==pytest.approx(5.e-6)
    assert roundoff[1][1]==pytest.approx(5.e-7)
    equations=[[(1,1,2.),(2,1,-2.)]]
    u={1:[10.,0,0],2:[10.00001,0,0]}
    result=frame.mpc_intervals(equations,u,roundoff)
    assert result['maximum_printed_residual_mm']>1.e-5
    assert result['passed']
    u[2][0]=10.0001
    assert not frame.mpc_intervals(equations,u,roundoff)['passed']


def test_load_patch_requires_full_independent_panel_containment():
    bounds=(-1219.2,0.,1219.2,2438.4)
    assert frame.contained_patch(-619.2,1919.2,20.,bounds)==pytest.approx((-629.2,-609.2,1909.2,1929.2))
    assert frame.contained_patch(-619.2,1919.2,80.,bounds)==pytest.approx((-659.2,-579.2,1879.2,1959.2))
    with pytest.raises(ValueError,match='outside independent panel'):
        frame.contained_patch(-19.2,1919.2,80.,bounds)
    for invalid in (0.,-20.,float('nan')):
        with pytest.raises(ValueError,match='Positive finite'):
            frame.contained_patch(-619.2,1919.2,invalid,bounds)
