import math

import pytest

from fea.panel_math import head_nodes


def test_head_constraints_select_seating_face_and_reject_adjacent_wood():
    screw={"name":"test","head_mm":(10,20,30),"shank_diameter_mm":4.826}
    nodes={}
    for depth in (0,1.5,2.5):
        radius=5-(5-4.826/2)*depth/3
        for i in range(8):
            a=i*math.pi/4
            nodes[len(nodes)+1]=(10+radius*math.cos(a),20+radius*math.sin(a),30+depth)
    nodes[100]=(10,20,31)  # hole axis
    nodes[101]=(15.1,20,30)  # adjacent panel face
    nodes[102]=(15,20,29)  # in front of seating face
    assert head_nodes(nodes,{"normal":(0,0,1)},screw)==list(range(1,25))
    with pytest.raises(ValueError):
        head_nodes({1:(15,20,30)},{"normal":(0,0,1)},screw)
