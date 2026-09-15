"""Conforming C3D20 timber solids for an inner-face horizontal foot recess.

Exact side-profile polygons define the exterior; no rectangular stiffness or
rigid bevel extension replaces the remaining foot. The two X strips share
native nodes above the shoulder. Fasteners interpolate within retained cells.
"""
import math
from itertools import pairwise

import numpy as np

from fea.current_response_model import CurrentStructure

CORNERS = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                    [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
EDGES = np.array([[0,-1,-1],[1,0,-1],[0,1,-1],[-1,0,-1],
                  [0,-1,1],[1,0,1],[0,1,1],[-1,0,1],
                  [-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]])


def shape20(point):
    point = np.asarray(point, dtype=float)
    values = [np.prod(1+sign*point)*(np.dot(sign,point)-2)/8 for sign in CORNERS]
    for sign in EDGES:
        along = int(np.flatnonzero(sign == 0)[0])
        values.append((1-point[along]**2)*np.prod(1+sign*point)/4)
    return np.asarray(values)


def profile(record):
    data = record['floor_recess_geometry']
    grain = np.asarray(record['axis'], dtype=float)
    if abs(grain[0]) > 1.e-8 or grain[2] <= 0 or abs(np.linalg.norm(grain)-1) > 1.e-8:
        raise ValueError('Recess requires positive-Z grain in the YZ plane')
    normal = np.array([0., grain[2], -grain[1]])
    points = np.asarray(data['side_profile_yz_mm'], dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError('Require finite exact side-profile YZ vertices')
    # Sorting the convex outline avoids relying on BRep vertex enumeration.
    from scipy.spatial import ConvexHull
    points = points[ConvexHull(points).vertices]
    qz = np.column_stack((points@normal[1:], points[:,1]))
    qs = sorted({round(q,8) for q in qz[:,0]})
    # Merge numerical duplicates while retaining real intermediate top corners.
    qs = [q for i,q in enumerate(qs) if i == 0 or q-qs[i-1] > 1.e-6]
    low, high = min(qs), max(qs)
    height = float(data['notch_top_z_mm'])
    if low >= high or height <= 0 or abs(points[:,1].min()) > 1.e-6:
        raise ValueError('Require a positive recess above a level Z=0 foot')

    def z_bounds(q):
        values = []
        for a,b in zip(qz,np.roll(qz,-1,axis=0),strict=True):
            if abs(b[0]-a[0]) < 1.e-7:
                if abs(q-a[0]) < 1.e-6: values.extend((a[1],b[1]))
            elif min(a[0],b[0])-1.e-6 <= q <= max(a[0],b[0])+1.e-6:
                values.append(a[1]+(q-a[0])*(b[1]-a[1])/(b[0]-a[0]))
        if not values: raise ValueError('No profile section')
        if abs(min(values)) > 1.e-5 or max(values) <= height:
            raise ValueError('Require level foot and full-height section above shoulder')
        return 0., max(values)
    tops = [z_bounds(q)[1] for q in qs]
    retained = sorted(map(float,data['retained_x_band_mm']))
    cut = sorted(map(float,data['cut_inner_x_band_mm']))
    xs = sorted(set(retained+cut))
    if len(xs) != 3 or min(np.diff(xs)) <= 0 or not math.isclose(retained[1]-retained[0],50.8,abs_tol=1.e-6):
        raise ValueError('Require adjacent 38.1 mm recess and 50.8 mm retained X strips')
    if not math.isclose(cut[1]-cut[0],38.1,abs_tol=1.e-6):
        raise ValueError('Require exact single 2x recess depth')
    return data, normal, qs, tops, xs, retained, height


def mesh_member(structure, record, attachment_points=(), size=100.):
    if not math.isfinite(size) or size <= 0 or record['name'] in structure.members:
        raise ValueError('Require positive mesh size and an unmeshed member')
    data, normal, qs, tops, xs, retained, shoulder = profile(record)
    name = record['name']
    nodes, cells = {}, []
    def node(point):
        key = tuple(round(float(v),8) for v in point)
        if key not in nodes: nodes[key] = structure.node(point)
        return nodes[key]
    for qi,(q0,q1) in enumerate(pairwise(qs)):
        top0,top1 = tops[qi:qi+2]
        for zone in ('lower','upper'):
            count = max(1,math.ceil((shoulder if zone == 'lower' else max(tops)-shoulder)/size))
            for t0,t1 in pairwise(np.linspace(0.,1.,count+1)):
                for x0,x1 in pairwise(xs):
                    if zone == 'lower' and not retained[0]-1.e-7 <= (x0+x1)/2 <= retained[1]+1.e-7:
                        continue
                    cell = {'x_mm':[x0,x1], 'q_mm':[q0,q1], 't_interval':[float(t0),float(t1)],
                            'top_z_mm':[top0,top1], 'zone':zone, 'shoulder_z_mm':shoulder}
                    def mapped(p, x0=x0, x1=x1, q0=q0, q1=q1, t0=t0, t1=t1,
                               top0=top0, top1=top1, zone=zone):
                        x = (x0+x1)/2+p[0]*(x1-x0)/2
                        q = (q0+q1)/2+p[1]*(q1-q0)/2
                        t = (t0+t1)/2+p[2]*(t1-t0)/2
                        top = top0+(q-q0)*(top1-top0)/(q1-q0)
                        z = t*shoulder if zone == 'lower' else shoulder+t*(top-shoulder)
                        return np.array([x,(q-normal[2]*z)/normal[1],z])
                    ids = [node(mapped(p)) for p in np.vstack((CORNERS,EDGES))]
                    cell['element'] = structure.element('C3D20',ids,name)
                    span = shoulder if zone == 'lower' else (top0+top1)/2-shoulder
                    cell['volume_mm3'] = (x1-x0)*(q1-q0)/normal[1]*(t1-t0)*span
                    cells.append(cell)
    volume = sum(c['volume_mm3'] for c in cells)
    expected = data.get('expected_retained_volume_mm3')
    if expected is not None and not math.isclose(volume,expected,abs_tol=.02,rel_tol=1.e-9):
        raise ValueError('Native recess volume differs from actual CAD')
    start,end,u = (np.asarray(record[k],dtype=float) for k in ('start','end','section_u'))
    record['native_section_geometry'] = 'ACTUAL_HORIZONTAL_FOOT_RECESS_C3D20'
    record['retained_mesh_volume_mm3'] = volume
    shoulder_points = [np.array([0.,(q-normal[2]*shoulder)/normal[1],shoulder]) for q in (qs[0],qs[-1])]
    record['additional_recovery_stations_mm'] = sorted(float(np.dot(p-start,record['axis'])) for p in shoulder_points)
    structure.members[name] = {'record':record,'start':start,'axis':np.asarray(record['axis']),
        'u':u,'v':np.cross(record['axis'],u),'length':float(np.linalg.norm(end-start)),
        'sections':{},'floor_recess_cells':cells,'floor_recess_normal':normal,
        'retained_mesh_volume_mm3':volume}
    for point in attachment_points:
        locate(structure,name,point)


def locate(structure,name,point):
    member = structure.members[name]
    point = np.asarray(point,dtype=float)
    normal = member['floor_recess_normal']
    q,z = float(np.dot(point,normal)),float(point[2])
    for cell in member['floor_recess_cells']:
        x0,x1 = cell['x_mm']; q0,q1 = cell['q_mm']; t0,t1 = cell['t_interval']
        if not x0-1.e-6 <= point[0] <= x1+1.e-6 or not q0-1.e-6 <= q <= q1+1.e-6:continue
        top0,top1 = cell['top_z_mm']; shoulder = cell['shoulder_z_mm']
        top = top0+(q-q0)*(top1-top0)/(q1-q0)
        t = z/shoulder if cell['zone']=='lower' else (z-shoulder)/(top-shoulder)
        if not t0-1.e-8 <= t <= t1+1.e-8:continue
        natural = np.array([2*(point[0]-x0)/(x1-x0)-1,2*(q-q0)/(q1-q0)-1,2*(t-t0)/(t1-t0)-1])
        ids = structure.elements[cell['element']][1]
        weights = shape20(natural)
        actual = weights@np.asarray([structure.nodes[n] for n in ids])
        if np.linalg.norm(actual-point)>1.e-6:raise ValueError('Recess interpolation lost affine geometry')
        return ids,weights
    raise ValueError('Attachment lies outside actual retained foot-recess timber')


def attachment(structure,name,point):
    ids,weights = locate(structure,name,point)
    tag = structure.node(point)
    for dof in (1,2,3):
        structure.equations.append([(tag,dof,1.)]+[(n,dof,-float(w)) for n,w in zip(ids,weights,strict=True) if abs(w)>1.e-13])
    return tag


class RecessStructure(CurrentStructure):
    def member(self,record,attachment_points=(),size=100.):
        if 'floor_recess_geometry' in record:
            return mesh_member(self,record,attachment_points,size)
        return super().member(record,attachment_points,size)

    def attachment(self,name,point):
        if 'floor_recess_cells' in self.members[name]:
            return attachment(self,name,point)
        return super().attachment(name,point)


def prepare_recess(module, **kwargs):
    """Opt-in serial preparation with scoped factories; shared sources unchanged.

    The existing builder still owns all materials, contacts and load records.
    Its gross-member and bevel adapters are replaced only for explicitly named
    recess members, and every factory is restored even if preparation fails.
    This wrapper must not run concurrently with another preparation in-process.
    """
    from fea import current_response_model as native
    geometry = module.floor_recess_geometry()
    if set(geometry) != {'lumber_leg_left','lumber_leg_right'}:
        raise ValueError('Require both explicitly recessed legs')
    original_structure = native.CurrentStructure
    original_record = native.gross_member_record
    original_floor = native.floor_attachment

    def revised_record(part,*args,**options):
        record = original_record(part,*args,**options)
        if part.name in geometry:
            record['floor_recess_geometry'] = geometry[part.name]
        return record

    def actual_floor(structure,name,point):
        if 'floor_recess_cells' in structure.members[name]:
            return attachment(structure,name,point)
        return original_floor(structure,name,point)

    try:
        native.CurrentStructure = RecessStructure
        native.gross_member_record = revised_record
        native.floor_attachment = actual_floor
        return native.prepare(module,**kwargs)
    finally:
        native.CurrentStructure = original_structure
        native.gross_member_record = original_record
        native.floor_attachment = original_floor
