import pickle
from itertools import product

import numpy as np
import pytest

from fea.floor_taper_mesh import TaperStructure, attachment, mapped, mesh_member


def record(left=False):
    g=np.array([0.,-.24,np.sqrt(1-.24**2)])
    n=np.array([0.,g[2],-g[1]])
    qs=[100.,239.7]
    points=[[float((q-n[2]*z)/n[1]),z] for q in qs for z in (0.,1000.+.2*(q-100.))]
    stations=np.array(points)@g[1:]
    full=88.9*139.7*((stations[1]+stations[3]-stations[0]-stations[2])/2)
    a,b=300.,757.2
    removed=38.1*139.7*(a-(stations[0]+stations[2])/2+(b-a)/2)
    return {'name':'leg','start':[0.,0.,0.],'end':(g*1200).tolist(),'axis':g.tolist(),
        'section_u':[1.,0.,0.],'width_mm':88.9,'depth_mm':139.7,
        'floor_recess_geometry':{'grain_axis_xyz':g.tolist(),'side_profile_yz_mm':points,
            'taper_start_station_mm':a,'taper_end_station_mm':b,'max_recess_depth_mm':38.1,
            'cut_inner_x_band_mm':[-38.1,0.] if left else [0.,38.1],
            'retained_x_band_mm':[-88.9,-38.1] if left else [38.1,88.9],
            'expected_retained_volume_mm3':float(full-removed)}}


def independent_weights(point):
    corners=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
    edges=np.array([[0,-1,-1],[1,0,-1],[0,1,-1],[-1,0,-1],[0,-1,1],[1,0,1],[0,1,1],[-1,0,1],[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]])
    values=[np.prod(1+r*point)*(r@point-2)/8 for r in corners]
    for row in edges:
        axis=np.flatnonzero(row==0)[0]
        values.append((1-point[axis]**2)*np.prod(1+row*point)/4)
    return np.array(values)


def test_actual_taper_volume_centroid_jacobian_and_shared_faces():
    model=TaperStructure({});item=record();mesh_member(model,item,size=250.)
    member=model.members['leg'];integrated=0.;moment=np.zeros(3)
    for cell in member['floor_taper_cells']:
        xyz=np.array([model.nodes[n] for n in model.elements[cell['element']][1]])
        volume=0.
        for p in product((-1/np.sqrt(3),1/np.sqrt(3)),repeat=3):
            p=np.array(p)
            derivative=np.column_stack([(independent_weights(p+a*1.e-6)-independent_weights(p-a*1.e-6))/2.e-6 for a in np.eye(3)])
            det=np.linalg.det(xyz.T@derivative)
            assert det>0
            volume+=det;moment+=(independent_weights(p)@xyz)*det
        assert volume==pytest.approx(cell['volume_mm3'],rel=1.e-8)
        integrated+=volume
    assert integrated==pytest.approx(item['floor_recess_geometry']['expected_retained_volume_mm3'])
    assert moment/integrated==pytest.approx(member['retained_mesh_centroid_xyz_mm'],rel=1.e-8)
    for first,second in zip(member['floor_taper_cells'],member['floor_taper_cells'][1:]):
        assert len(set(model.elements[first['element']][1])&set(model.elements[second['element']][1]))==8
    assert not model.equations
    assert item['additional_recovery_stations_mm']==[300.,757.2]


def test_variable_width_attachment_rejects_removed_wood_and_pickle_roundtrip():
    model=TaperStructure({});item=record();model.member(item,size=250.)
    m=model.members['leg'];g=m['axis'];n=m['floor_taper_normal']
    point=np.array([10.,0.,0.])+g*500+n*170
    with pytest.raises(ValueError,match='outside actual retained'):
        attachment(model,'leg',point)
    cell=next(c for c in m['floor_taper_cells'] if c['lower_s_mm']==[300.,300.])
    point=mapped(cell,[0.,0.,0.],g,n)
    attachment(model,'leg',point)
    for equation in model.equations[-3:]:
        for rotation in np.eye(3):
            assert sum(coef*(np.array([1.,2.,3.])+np.cross(rotation,model.nodes[node]))[dof-1] for node,dof,coef in equation)==pytest.approx(0.,abs=1.e-9)
    restored=pickle.loads(pickle.dumps(model))
    assert type(restored) is TaperStructure
    assert restored.members['leg']['retained_mesh_volume_mm3']==pytest.approx(m['retained_mesh_volume_mm3'])
    restored.attachment('leg',point)


def test_reflected_taper_retains_volume_and_reflects_centroid():
    members=[]
    for left in (False,True):
        model=TaperStructure({});model.member(record(left),size=250.);members.append(model.members['leg'])
    assert members[0]['retained_mesh_volume_mm3']==pytest.approx(members[1]['retained_mesh_volume_mm3'])
    a=np.array(members[0]['retained_mesh_centroid_xyz_mm']);b=np.array(members[1]['retained_mesh_centroid_xyz_mm'])
    assert a==pytest.approx(b*np.array([-1.,1.,1.]))
