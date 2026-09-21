"""Actual variable-width C3D20 leg mesh with a grain-aligned recess runout.

All cells are contiguous timber; width varies through the taper rather than
using gross-section stiffness or a shoulder spring. Side and end profiles come
from actual CAD, and volume/centroid follow the same mapped retained solids.
"""
import math
from itertools import pairwise, product

import numpy as np

from fea.current_response_model import CurrentStructure
from fea.floor_recess_mesh import CORNERS, EDGES, shape20


def geometry(record):
    data = record['floor_recess_geometry']
    grain = np.asarray(data['grain_axis_xyz'],dtype=float)
    if not np.allclose(grain,record['axis'],atol=1.e-8,rtol=0) or abs(grain[0])>1.e-8 or grain[2]<=0:
        raise ValueError('Require matching positive-Z leg grain')
    normal = np.array([0.,grain[2],-grain[1]])
    points = np.asarray(data['side_profile_yz_mm'],dtype=float)
    from scipy.spatial import ConvexHull
    points = points[ConvexHull(points).vertices]
    qs = points@normal[1:]; ss=points@grain[1:]
    qvalues = sorted({round(q,8) for q in qs})
    qvalues = [q for i,q in enumerate(qvalues) if i==0 or q-qvalues[i-1]>1.e-6]
    def limits(q):
        values=[]
        for i,j in zip(range(len(points)),np.roll(np.arange(len(points)),-1),strict=True):
            if abs(qs[j]-qs[i])<1.e-7:
                if abs(q-qs[i])<1.e-6:values.extend((ss[i],ss[j]))
            elif min(qs[i],qs[j])-1.e-6<=q<=max(qs[i],qs[j])+1.e-6:
                values.append(ss[i]+(q-qs[i])*(ss[j]-ss[i])/(qs[j]-qs[i]))
        if not values:raise ValueError('Missing actual side-profile section')
        return min(values),max(values)
    ends=[limits(q) for q in qvalues]
    a,b=map(float,(data['taper_start_station_mm'],data['taper_end_station_mm']))
    depth=float(data['max_recess_depth_mm'])
    if (not math.isfinite(a+b+depth) or depth<=0 or b-a<12*depth-1.e-6
            or any(not low<a<b<high for low,high in ends)):
        raise ValueError('Require contained taper at least 1:12 along grain')
    retained=sorted(map(float,data['retained_x_band_mm']))
    cut=sorted(map(float,data['cut_inner_x_band_mm']))
    xs=sorted(set(retained+cut))
    if len(xs)!=3 or not math.isclose(cut[1]-cut[0],depth,abs_tol=1.e-6):
        raise ValueError('Require adjacent full-depth cut and retained X bands')
    outer_left=math.isclose(retained[0],xs[0],abs_tol=1.e-6)
    return data,grain,normal,qvalues,ends,a,b,depth,xs[0],xs[-1],outer_left


def mapped(cell, natural, grain, normal):
    xi,eta,zeta=natural
    q0,q1=cell['q_mm'];t0,t1=cell['t_interval']
    q=(q0+q1)/2+eta*(q1-q0)/2
    t=(t0+t1)/2+zeta*(t1-t0)/2
    fraction=(q-q0)/(q1-q0)
    lower=cell['lower_s_mm'][0]+fraction*np.diff(cell['lower_s_mm'])[0]
    upper=cell['upper_s_mm'][0]+fraction*np.diff(cell['upper_s_mm'])[0]
    s=lower+t*(upper-lower)
    a,b=cell['taper_stations_mm']
    removed=cell['recess_depth_mm']*min(1.,max(0.,(b-s)/(b-a)))
    x0,x1=cell['raw_x_mm']
    if cell['outer_left']:x1-=removed
    else:x0+=removed
    x=(x0+x1)/2+xi*(x1-x0)/2
    return np.array([x,0.,0.])+grain*s+normal*q


def mesh_member(structure,record,attachment_points=(),size=100.):
    if not math.isfinite(size) or size<=0 or record['name'] in structure.members:
        raise ValueError('Require positive size and unmeshed member')
    data,grain,normal,qs,ends,a,b,depth,xmin,xmax,outer_left=geometry(record)
    nodes,cells={},[]
    def node(p):
        key=tuple(round(float(v),8) for v in p)
        if key not in nodes:nodes[key]=structure.node(p)
        return nodes[key]
    # Use common subdivisions across all profile strips to share interface nodes.
    counts=[max(1,math.ceil(span/size)) for span in
            (a-min(r[0] for r in ends),b-a,max(r[1] for r in ends)-b)]
    volume=0.;first_moment=np.zeros(3)
    for index,(q0,q1) in enumerate(pairwise(qs)):
        levels=[[ends[index][0],ends[index+1][0]],[a,a],[b,b],[ends[index][1],ends[index+1][1]]]
        for zone,(lower,upper) in enumerate(pairwise(levels)):
            for t0,t1 in pairwise(np.linspace(0.,1.,counts[zone]+1)):
                cell={'q_mm':[q0,q1],'lower_s_mm':lower,'upper_s_mm':upper,
                      't_interval':[float(t0),float(t1)],'taper_stations_mm':[a,b],
                      'recess_depth_mm':depth,'raw_x_mm':[xmin,xmax],'outer_left':outer_left}
                ids=[node(mapped(cell,p,grain,normal)) for p in np.vstack((CORNERS,EDGES))]
                cell['element']=structure.element('C3D20',ids,record['name'])
                cell_volume=0.;cell_moment=np.zeros(3)
                for point in product((-1/math.sqrt(3),1/math.sqrt(3)),repeat=3):
                    xyz=mapped(cell,point,grain,normal)
                    qfraction=(point[1]+1)/2
                    sspan=(upper[0]-lower[0])*(1-qfraction)+(upper[1]-lower[1])*qfraction
                    station=float(xyz@grain)
                    width=xmax-xmin-depth*min(1.,max(0.,(b-station)/(b-a)))
                    det=width*(q1-q0)*sspan*(t1-t0)/8
                    if det<=0:raise ValueError('Nonpositive tapered cell Jacobian')
                    cell_volume+=det;cell_moment+=xyz*det
                cell['volume_mm3']=cell_volume
                volume+=cell_volume;first_moment+=cell_moment;cells.append(cell)
    expected=data.get('expected_retained_volume_mm3')
    if expected is None or not math.isclose(volume,expected,abs_tol=.03,rel_tol=1.e-9):
        raise ValueError('Native taper volume differs from actual CAD')
    centre=first_moment/volume
    expected_centre=data.get('expected_retained_centroid_xyz_mm')
    if expected_centre is not None and not np.allclose(centre,expected_centre,atol=1.e-6,rtol=0):
        raise ValueError('Native taper centroid differs from actual CAD')
    start,end,u=(np.asarray(record[k],dtype=float) for k in ('start','end','section_u'))
    record.update(native_section_geometry='ACTUAL_GRAIN_TAPER_FOOT_RECESS_C3D20',
                  retained_mesh_volume_mm3=volume,retained_mesh_centroid_xyz_mm=centre.tolist(),
                  additional_recovery_stations_mm=[a-float(start@grain),b-float(start@grain)])
    structure.members[record['name']]={'record':record,'start':start,'axis':grain,'u':u,
        'v':np.cross(grain,u),'length':float(np.linalg.norm(end-start)), 'sections':{},
        'floor_taper_cells':cells,'floor_taper_normal':normal,'retained_mesh_volume_mm3':volume,
        'retained_mesh_centroid_xyz_mm':centre.tolist()}
    for point in attachment_points:locate(structure,record['name'],point)


def locate(structure,name,point):
    member=structure.members[name];point=np.asarray(point,dtype=float)
    grain,normal=member['axis'],member['floor_taper_normal']
    q,s=float(point@normal),float(point@grain)
    for cell in member['floor_taper_cells']:
        q0,q1=cell['q_mm'];t0,t1=cell['t_interval']
        if not q0-1.e-6<=q<=q1+1.e-6:continue
        fraction=(q-q0)/(q1-q0)
        lower=cell['lower_s_mm'][0]+fraction*np.diff(cell['lower_s_mm'])[0]
        upper=cell['upper_s_mm'][0]+fraction*np.diff(cell['upper_s_mm'])[0]
        t=(s-lower)/(upper-lower)
        if not t0-1.e-8<=t<=t1+1.e-8:continue
        a,b=cell['taper_stations_mm'];removed=cell['recess_depth_mm']*min(1.,max(0.,(b-s)/(b-a)))
        x0,x1=cell['raw_x_mm']
        if cell['outer_left']:x1-=removed
        else:x0+=removed
        if not x0-1.e-6<=point[0]<=x1+1.e-6:continue
        natural=[2*(point[0]-x0)/(x1-x0)-1,2*fraction-1,2*(t-t0)/(t1-t0)-1]
        weights=shape20(natural);ids=structure.elements[cell['element']][1]
        if np.linalg.norm(weights@np.asarray([structure.nodes[n] for n in ids])-point)>1.e-6:
            raise ValueError('Taper interpolation lost affine geometry')
        return ids,weights
    raise ValueError('Attachment lies outside actual retained tapered timber')


def attachment(structure,name,point):
    ids,weights=locate(structure,name,point);tag=structure.node(point)
    for dof in (1,2,3):
        structure.equations.append([(tag,dof,1.)]+[(n,dof,-float(w)) for n,w in zip(ids,weights,strict=True) if abs(w)>1.e-13])
    return tag


class TaperStructure(CurrentStructure):
    """Module-level native structure remains pickleable for saved solve states."""
    def member(self,record,attachment_points=(),size=100.):
        if 'floor_recess_geometry' in record:return mesh_member(self,record,attachment_points,size)
        return super().member(record,attachment_points,size)

    def attachment(self,name,point):
        if 'floor_taper_cells' in self.members[name]:return attachment(self,name,point)
        return super().attachment(name,point)


def prepare_taper(module,**kwargs):
    """Serial opt-in factories, restored even when preparation fails."""
    from fea import current_response_model as native
    records=module.floor_recess_geometry()
    if set(records)!={'lumber_leg_left','lumber_leg_right'}:raise ValueError('Require both tapered legs')
    original_structure,original_record,original_floor=native.CurrentStructure,native.gross_member_record,native.floor_attachment
    def revised_record(part,*args,**options):
        record=original_record(part,*args,**options)
        if part.name in records:record['floor_recess_geometry']=records[part.name]
        return record
    def actual_floor(structure,name,point):
        if 'floor_taper_cells' in structure.members[name]:return attachment(structure,name,point)
        return original_floor(structure,name,point)
    try:
        native.CurrentStructure=TaperStructure;native.gross_member_record=revised_record;native.floor_attachment=actual_floor
        return native.prepare(module,**kwargs)
    finally:
        native.CurrentStructure=original_structure;native.gross_member_record=original_record;native.floor_attachment=original_floor
