"""Independent quadrature of the nominal traction, without importing convert.py."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
data=json.loads((HERE/'normal-traction.json').read_text())
for name,pin in data['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
source=json.loads((HERE.parent/'current-corner-conditional-section-demands-attempt01/section-demands.json').read_text())
geometry=json.loads((HERE.parent/'current-corner-local-wood-screen-attempt01/section-screen.json').read_text())['modeled_geometry_inputs']
models={a['case_id']:json.loads((ROOT/a['source_paths']['model']).read_text()) for a in source['case_authentication']}
reports={a['case_id']:json.loads((ROOT/a['source_paths']['report']).read_text()) for a in source['case_authentication']}
lookup={}
for body in source['per_increment_body_sections']:
    for station in body['section_stations']:
        for side in ['just_below','just_above']:
            lookup[body['case_id'],body['load_factor'],body['body'],station['axis_id'],side]=station['one_sided_cut_results'][side]['lower_segment_material_action']
gauss,weights=np.polynomial.legendre.leggauss(3)


def rectangle(width,depth,x=0.,y=0.,sign=1.):
    return [(x+a*width/2,y+b*depth/2,sign*width*depth*wa*wb/4)
            for a,wa in zip(gauss,weights) for b,wb in zip(gauss,weights)]


def circle(radius,x,y):
    points=[]
    for a,wa in zip(gauss,weights):
        r=radius*(1+a)/2
        for angle in np.arange(16)*2*math.pi/16:
            points.append((x+r*math.cos(angle),y+r*math.sin(angle),-wa*radius/2*r*2*math.pi/16))
    return points


worst=np.zeros(3)
corrected=0
for row in data['rows']:
    case,member,axis=row['case'],row['member'],row['axis']
    actual=lookup[case,row['load_factor'],member,axis,row['cut_side']]
    assert actual['force_xyz_n']==row['source_signed_force_XYZ_N']
    origin=models[case]['body_geometry'][member]['geometry_record']['start']
    w,d=geometry['spine_XY_envelope_mm' if member.endswith('spine') else 'inner_block_XY_envelope_mm']
    full=reports[case]['increments'][-1]
    bolt=next(b for group in full['primary_physical_bolt_groups'].values() for b in group['bolts'] if b['axis_id']==axis)
    y=bolt['axis_datum_global_xyz_mm'][1]-origin[1]
    diameter=geometry['modeled_bore_diameter_mm_from_profile_void_intervals']
    points=rectangle(w,d)+rectangle(w,diameter,y=y,sign=-1.)
    if not member.endswith('spine'):
        for gx,gy in geometry['BG045_inner_block_bore_centers_xy_mm']:
            points+=circle(diameter/2,gx-origin[0],gy-origin[1])
    points=np.array(points)
    section=data['sections'][member+'/'+axis]
    area=sum(points[:,2])
    centroid=(points[:,:2].T@points[:,2])/area
    assert abs(area-section['area_mm2'])<1e-7
    assert np.max(np.abs(centroid-section['centroid_offset_from_gross_XY_mm']))<1e-9
    # Integral about the ORIGINAL datum, bypassing the producer's moment shift.
    sigma=row['uniform_normal_traction_MPa']+(points[:,:2]-centroid)@np.array(row['affine_gradient_XY_MPa_per_mm'])
    traction=sigma*points[:,2]
    recovered=np.array([sum(traction),points[:,1]@traction,-points[:,0]@traction])
    expected=np.array([actual['force_xyz_n'][2],actual['moment_xyz_nmm'][0],actual['moment_xyz_nmm'][1]])
    residual=np.abs(recovered-expected)
    worst=np.maximum(worst,residual)
    assert residual[0]<1e-8 and max(residual[1:])<1e-7
    corrected+=row['source_context_area_corrected_in_this_packet']
assert len(data['rows'])==252 and corrected==84
print('PASS_INDEPENDENT_SUBTRACTED_DOMAIN_TRACTION_QUADRATURE:',len(data['rows']),'cuts; max N/Mx/My residual:',worst.tolist(),';84 contextual areas explicitly corrected')
