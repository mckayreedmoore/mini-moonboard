"""Control comparisons require the same actual nodal load locations and forces."""
from copy import deepcopy

from fea.horizontal_frame_batch import CASES, common_loads


def test_common_load_identity_tracks_geometry_and_force_not_node_labels():
    a={'nodes':{'1':[0,0,1]},'loads':{'1':[0,2,3]}}
    b={'nodes':{'9':[0,0,1]},'loads':{'9':[0,2,3]}}
    assert common_loads(a,b)
    changed=deepcopy(b);changed['nodes']['9'][2]=2
    assert not common_loads(a,changed)
    changed=deepcopy(b);changed['loads']['9'][1]=1
    assert not common_loads(a,changed)
    assert len(CASES)==len({name for name,_ in CASES})==10
