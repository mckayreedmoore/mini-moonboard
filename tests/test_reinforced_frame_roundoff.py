"""Independent interval checks for recovered force/moment roundoff."""
import numpy as np
import pytest

from fea.reinforced_frame_roundoff import moment_radius, spring_radii


def test_moment_interval_encloses_all_vertex_force_errors():
    lever=np.array([13.,-72.,48.])
    radius=np.array([.01,.05,.03])
    bound=moment_radius(lever,radius)
    for signs in np.ndindex(2,2,2):
        error=(np.array(signs)*2-1)*radius
        assert np.all(abs(np.cross(lever,error))<=bound)
    assert bound==pytest.approx([4.56,.87,1.37])


def test_normal_scalar_roundoff_transforms_to_physical_axes():
    record={'connection_ownership':{
        'normal':{'scalar_normal':[0.,.6,.8]},'inactive':{}},
        'springs':[{'name':'normal','nodes':[1,2],'dof':1,'active':True,'stiffness_n_per_mm':100.},
                   {'name':'inactive','nodes':[1,2],'dof':2,'active':False,'stiffness_n_per_mm':10000.}]}
    precision={1:[.001,.01,.001],2:[.002,.01,.001]}
    rows=spring_radii(record,precision)
    assert rows['normal']==pytest.approx([0.,.18,.24])
    assert rows['inactive']==pytest.approx([0.,0.,0.])
