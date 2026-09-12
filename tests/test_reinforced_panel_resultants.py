"""Manufactured shell stresses check thickness integration and six-panel scope."""
import math

import numpy as np
import pytest

from fea.reinforced_panel_resultants import GAUSS, assess, integrate_thickness


def test_linear_bending_membrane_and_shear_integrate_exactly():
    t=18.25625
    tensors=[]
    for g in GAUSS:
        z=g*t/2
        tensors.append([[2.+3.*z,4.,5.],[4.,-7.+2.*z,6.],[5.,6.,0.]])
    r=integrate_thickness(tensors,t)
    assert r['nx_n_per_mm']==pytest.approx(2*t)
    assert r['ny_n_per_mm']==pytest.approx(-7*t)
    assert r['mx_nmm_per_mm']==pytest.approx(3*t**3/12)
    assert r['my_nmm_per_mm']==pytest.approx(2*t**3/12)
    assert r['qx_n_per_mm']==pytest.approx(5*t)
    assert r['qy_n_per_mm']==pytest.approx(6*t)
    assert r['nxy_n_per_mm']==pytest.approx(4*t)
    assert abs(r['mxy_nmm_per_mm_unchecked'])<1e-10


def manufactured():
    names=['main_lower_left','main_lower_right','main_upper_left','main_upper_right','kicker_left','kicker_right']
    elements={};nodes={};chunks=[];t=18.25625
    for e,name in enumerate(names,1):
        a=0. if name.startswith('kicker') else math.radians(40.)
        axes=np.array([[1,0,0],[0,math.sin(a),math.cos(a)],[0,-math.cos(a),math.sin(a)]])
        origin=np.array([e*200.,0.,0.]);corners=[[0,0,0],[100,0,0],[100,100,0],[0,100,0]]
        ids=[]
        for j,p in enumerate(corners):
            ids.append(e*10+j);nodes[e*10+j]=(origin+axes.T@p).tolist()
        elements[e]=['S8',ids,name]
        stresses=[];coords=[]
        ip=0
        for gx in GAUSS:
            for gy in GAUSS:
                for gz in GAUSS:
                    ip+=1;z=gz*t/2
                    local=np.diag([1.+z,2.,0.])
                    tensor=axes.T@local@axes
                    components=[tensor[0,0],tensor[1,1],tensor[2,2],tensor[0,1],tensor[0,2],tensor[1,2]]
                    point=origin+axes.T@np.array([(gx+1)*50,(gy+1)*50,z])
                    stresses.append(f'{e} {ip} '+' '.join(f'{v:.10e}'for v in components))
                    coords.append(f'{e} {ip} '+' '.join(f'{v:.10e}'for v in point))
        chunks+=['stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set '+name+' and time 1',*stresses,
                 'global coordinates (elem, integ.pnt.,x,y,z) for set '+name+' and time 1',*coords]
    return {'nodes':nodes,'elements':elements},'\n'.join(chunks)


def test_rotated_manufactured_panels_preserve_section_moments():
    record,data=manufactured();r=assess(record,data)
    assert len(r['panels'])==6
    for p in r['panels'].values():
        assert p['section_count']==9
        moment=p['component_extrema']['bending_x']['resultants']['mx_nmm_per_mm']
        assert moment==pytest.approx(18.25625**3/12)
        assert not r['qualified_for_design']


def test_missing_ip_cannot_be_treated_as_a_lower_stress():
    record,data=manufactured()
    data='\n'.join(line for line in data.splitlines() if not line.startswith('1 1 '))
    with pytest.raises(ValueError,match='Incomplete'):
        assess(record,data)


@pytest.mark.parametrize('file,head_ratio', [('reinforced-panel-F10-k1000-v4.json',3.03151877646),
                                           ('reinforced-panel-F10-k10000-v5.json',4.31585498776)])
def test_saved_native_components_keep_patch_location_and_current_head_basis(file,head_ratio):
    import json
    from pathlib import Path

    r=json.loads((Path('fea/results')/file).read_text())
    assert r['native_contact_active_set_converged']
    assert len(r['panels'])==6
    assert len(r['individual_attachment_checks'])==66
    assert r['attachment_references_n']['head_n']==pytest.approx(120*4.4482216152605)
    assert max(c['head_pull_through_ratio'] for c in r['individual_attachment_checks'])==pytest.approx(head_ratio)
    for p in r['panels'].values():
        for threshold,field in p['field_outside_patch'].items():
            for component,witness in field['component_extrema'].items():
                assert witness['distance_from_declared_patch_mm']>float(threshold)
                assert witness['ratio']<=p['component_extrema'][component]['ratio']
    assert r['reported_displacement_is_absolute_not_relative_panel_bending']
    assert not r['combined_panel_strength_accepted']
