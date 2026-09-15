from itertools import product

import numpy as np
import pytest

from fea.floor_recess_mesh import attachment, mesh_member, shape20
from fea.horizontal_panel_frame import Structure


def record(left=False):
    axis = np.array([0.,-.24,np.sqrt(1-.24**2)])
    normal = np.array([0.,axis[2],-axis[1]])
    qs = [100.,239.7]
    points = [[(q-normal[2]*z)/normal[1],z] for q in qs for z in (0.,1000.+.2*(q-100))]
    retained = [-88.9,-38.1] if left else [38.1,88.9]
    removed = [-38.1,0.] if left else [0.,38.1]
    full_volume = 88.9*139.7/normal[1]*(1000.+.1*139.7)
    volume = full_volume-38.1*139.7/normal[1]*141.7
    return {'name':'leg','start':[(-44.45 if left else 44.45),0.,0.],
            'end':[(-44.45 if left else 44.45),axis[1]*1200,axis[2]*1200],
            'axis':axis.tolist(),'section_u':[1.,0.,0.],'width_mm':88.9,'depth_mm':139.7,
            'floor_recess_geometry':{'side_profile_yz_mm':points,'retained_x_band_mm':retained,
                'cut_inner_x_band_mm':removed,'notch_top_z_mm':141.7,
                'expected_retained_volume_mm3':volume}}


def test_actual_recess_volume_and_native_shoulder_continuity():
    model = Structure(); item = record()
    mesh_member(model,item,size=200.)
    m = model.members['leg']
    assert m['retained_mesh_volume_mm3'] == pytest.approx(item['floor_recess_geometry']['expected_retained_volume_mm3'])
    assert not model.equations
    before = next(c for c in m['floor_recess_cells'] if c['zone']=='lower')
    after = next(c for c in m['floor_recess_cells'] if c['zone']=='upper' and c['t_interval'][0]==0 and c['x_mm']==[38.1,88.9])
    assert len(set(model.elements[before['element']][1]) & set(model.elements[after['element']][1])) == 8
    assert item['native_section_geometry']=='ACTUAL_HORIZONTAL_FOOT_RECESS_C3D20'


def test_interpolation_rejects_recess_and_reproduces_affine_motion():
    model = Structure(); item=record(); mesh_member(model,item,size=200.)
    normal=np.array([0.,item['axis'][2],-item['axis'][1]])
    def point(x,z):return [x,(170.-normal[2]*z)/normal[1],z]
    for p in (point(60.,0.),point(38.1,80.),point(20.,350.)):
        attachment(model,'leg',p)
        for equation in model.equations[-3:]:
            for rotation in np.eye(3):
                assert sum(coef*(np.array([1.,2.,3.])+np.cross(rotation,model.nodes[n]))[d-1]
                           for n,d,coef in equation)==pytest.approx(0.,abs=1.e-9)
    with pytest.raises(ValueError,match='outside actual retained'):
        attachment(model,'leg',point(20.,80.))


def test_independent_quadrature_positive_jacobian_volume_and_mirror():
    volumes=[]
    for left in (False,True):
        model=Structure(); item=record(left); mesh_member(model,item,size=500.)
        integrated=0.
        for cell in model.members['leg']['floor_recess_cells']:
            xyz=np.array([model.nodes[n] for n in model.elements[cell['element']][1]])
            volume=0.
            for p in product((-1/np.sqrt(3),1/np.sqrt(3)),repeat=3):
                p=np.array(p)
                derivative=np.column_stack([(shape20(p+a*1.e-6)-shape20(p-a*1.e-6))/2.e-6 for a in np.eye(3)])
                det=np.linalg.det(xyz.T@derivative)
                assert det>0
                volume+=det
            assert volume==pytest.approx(cell['volume_mm3'],rel=1.e-8)
            integrated+=volume
        volumes.append(integrated)
    assert volumes[0]==pytest.approx(volumes[1])


def test_recess_structure_pickle_roundtrip_retains_geometry_and_attachment():
    import pickle

    from fea.floor_recess_mesh import RecessStructure

    model = RecessStructure({})
    model.member(record(),size=500.)
    restored = pickle.loads(pickle.dumps(model))
    assert type(restored) is RecessStructure
    assert restored.members['leg']['retained_mesh_volume_mm3'] == pytest.approx(
        model.members['leg']['retained_mesh_volume_mm3'])
    normal = restored.members['leg']['floor_recess_normal']
    point = [60.,(170.-normal[2]*80.)/normal[1],80.]
    tag = restored.attachment('leg',point)
    assert restored.nodes[tag] == pytest.approx(point)
