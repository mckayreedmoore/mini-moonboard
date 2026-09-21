"""Reduced solid-member / independent shell-panel stiffness diagnostic.

Fresh current geometry, retained rectangular member sections, actual screw
stations and explicit finite attachment springs. Feet have clamped full cross sections, a diagnostic
boundary, not unanchored floor qualification. Isotropic elastic properties,
rigid angle bodies and spring stiffnesses are assumptions; no rated connection
or build-ready conclusion follows from solver convergence.
"""
import math
from itertools import pairwise

import numpy as np

from fea import vertical_panel_comparison as panel_kernel


def shape8(x, y):
    """Quadratic quadrilateral interpolation, including affine extrapolation."""
    return np.array([-(1-x)*(1-y)*(1+x+y)/4, -(1+x)*(1-y)*(1-x+y)/4,
                     -(1+x)*(1+y)*(1-x-y)/4, -(1-x)*(1+y)*(1+x-y)/4,
                     (1-x*x)*(1-y)/2, (1+x)*(1-y*y)/2,
                     (1-x*x)*(1+y)/2, (1-x)*(1-y*y)/2])


def equation_lines(terms):
    return ['*EQUATION', str(len(terms)),
            *[','.join(f'{n},{d},{v:.14g}' for n, d, v in terms[i:i+4])
              for i in range(0, len(terms), 4)]]


class Structure:
    """Native CCX elements; interpolation is kinematics, not a custom FE kernel."""
    def __init__(self):
        self.nodes, self.elements, self.groups = {}, {}, {}
        self.equations, self.springs, self.fixed = [], [], set()
        self.members, self.panels = {}, {}
        self.loads = {}
        self.rotation_masters = set()

    def node(self, xyz):
        tag = len(self.nodes)+1
        self.nodes[tag] = list(map(float, xyz))
        return tag

    def element(self, kind, ids, group):
        eid = len(self.elements)+1
        self.elements[eid] = (kind, list(ids), group)
        self.groups.setdefault(group, []).append(eid)
        return eid

    def member(self, record, attachment_points=(), size=100.):
        name = record['name']
        start, end, u = (np.array(record[k], dtype=float) for k in ('start', 'end', 'section_u'))
        length = float(np.linalg.norm(end-start))
        axis = (end-start)/length
        v = np.cross(axis, u)
        if abs(np.dot(axis, u)) > 1e-8 or abs(np.linalg.norm(u)-1) > 1e-8:
            raise ValueError('Member axes must be orthonormal')
        stations = [min(length, max(0., float(np.dot(np.array(p)-start, axis)))) for p in attachment_points]
        xs = panel_kernel.mesh_axes(0., length, size, stations)
        section = [(-1,-1),(1,-1),(1,1),(-1,1),(0,-1),(1,0),(0,1),(-1,0)]
        sections = {}
        width, depth = record['width_mm'], record['depth_mm']
        for s in xs:
            sections[round(s, 8)] = [self.node(start+axis*s+u*x*width/2+v*y*depth/2) for x, y in section]
        for a, b in pairwise(xs):
            first, last = sections[round(a, 8)], sections[round(b, 8)]
            middle = [self.node(start+axis*((a+b)/2)+u*x*width/2+v*y*depth/2) for x, y in section[:4]]
            ids = first[:4]+last[:4]+first[4:]+last[4:]+middle
            self.element('C3D20', ids, name)
        self.members[name] = {'record': record, 'start': start, 'axis': axis, 'u': u, 'v': v,
                              'length': length, 'sections': sections}

    def attachment(self, member_name, point):
        """Separate coincident connector nodes preserve independent member DOFs."""
        m = self.members[member_name]
        point = np.array(point, dtype=float)
        station = min(m['length'], max(0., float(np.dot(point-m['start'], m['axis']))))
        key = round(station, 8)
        if key not in m['sections']:
            raise ValueError('Attachment station was not imprinted in member mesh')
        centre = m['start']+station*m['axis']
        delta = point-centre
        # Endpoint extension along grain is deliberately disallowed: add a
        # physical member station rather than invent an unsupported rigid arm.
        if abs(np.dot(delta, m['axis'])) > 1e-5:
            raise ValueError('Attachment projects outside retained member ends')
        weights = shape8(2*np.dot(delta,m['u'])/m['record']['width_mm'],
                         2*np.dot(delta,m['v'])/m['record']['depth_mm'])
        ids = m['sections'][key]
        reconstructed = sum(w*np.array(self.nodes[n]) for n,w in zip(ids,weights,strict=True))
        if np.linalg.norm(reconstructed-point)>1e-6 or abs(sum(weights)-1)>1e-10:
            raise ValueError('Attachment interpolation lost affine geometry')
        tag = self.node(point)
        for dof in (1,2,3):
            terms = [(tag,dof,1.)]+[(n,dof,-float(w)) for n,w in zip(ids,weights,strict=True) if abs(w)>1e-13]
            self.equations.append(terms)
        return tag

    def spring(self, first, second, stiffness, name, dofs=(1,2,3), bearing=False):
        if not math.isfinite(stiffness) or stiffness<=0:
            raise ValueError('Positive spring stiffness required')
        if np.linalg.norm(np.array(self.nodes[first])-self.nodes[second])>1e-7:
            raise ValueError('Coincident spring points required for rigid-motion invariance')
        for dof in dofs:
            group=f'SPR{len(self.springs)+1}'
            eid=self.element('SPRING2',[first,second],group)
            self.springs.append({'name':name,'element':eid,'group':group,'nodes':[first,second],
                                 'dof':dof,'stiffness_n_per_mm':stiffness,'bearing_closed_assumption':bearing})

    def rigid_angle(self, name, points):
        """Six native translational master DOFs and linear rigid-point equations."""
        centre=np.mean(points,axis=0)
        translation=self.node(centre)
        rotation=self.node(centre)
        self.rotation_masters.add(rotation)
        tags=[]
        for point in points:
            tag=self.node(point)
            r=np.array(point)-centre
            for i in range(3):
                # u(point)=u(reference)+theta cross r.
                j,k=(i+1)%3,(i+2)%3
                terms=[(tag,i+1,1.),(translation,i+1,-1.)]
                if abs(r[k])>1e-13: terms.append((rotation,j+1,-float(r[k])))
                if abs(r[j])>1e-13: terms.append((rotation,k+1,float(r[j])))
                self.equations.append(terms)
            tags.append(tag)
        return tags

    def deck(self, modulus=7000., poisson=.3, active_bearings=None, stress=False):
        lines=['** '+__doc__.replace('\n',' '),'*NODE']
        lines += [f'{n},'+','.join(f'{x:.14g}' for x in p) for n,p in self.nodes.items()]
        omitted={r['group'] for r in self.springs if r['bearing_closed_assumption']
                 and active_bearings is not None and r['name'] not in active_bearings}
        for group,ids in self.groups.items():
            if group in omitted:continue
            kind=self.elements[ids[0]][0]
            lines += [f'*ELEMENT,TYPE={kind},ELSET={group}']
            for eid in ids:
                values=[eid,*self.elements[eid][1]]
                lines += [','.join(map(str,values[i:i+16])) for i in range(0,len(values),16)]
        for terms in self.equations: lines += equation_lines(terms)
        lines += ['*MATERIAL,NAME=ASSUMED_WOOD','*ELASTIC',f'{modulus},{poisson}']
        for name in self.members:
            lines += [f'*SOLID SECTION,ELSET={name},MATERIAL=ASSUMED_WOOD']
        for name in self.panels:
            lines += [f'*SHELL SECTION,ELSET={name},MATERIAL=ASSUMED_WOOD',str(panel_kernel.THICKNESS)]
        for spring in self.springs:
            if spring['group'] in omitted:continue
            lines += [f"*SPRING,ELSET={spring['group']}",f"{spring['dof']},{spring['dof']}",str(spring['stiffness_n_per_mm'])]
        lines += panel_kernel.sets('ALLN',self.nodes)
        lines += ['*BOUNDARY',*[f'{n},1,3,0' for n in sorted(self.fixed)],'*STEP','*STATIC','*CLOAD']
        lines += [f'{n},{i+1},{f:.14g}' for n,force in self.loads.items() for i,f in enumerate(force) if abs(f)>1e-14]
        lines += ['*NODE PRINT,NSET=ALLN','U,RF']
        if stress:
            for name in (*self.members,*self.panels):
                lines += [f'*EL PRINT,ELSET={name},GLOBAL=YES','S,COORD']
        lines += ['*END STEP']
        return '\n'.join(lines)+'\n'


def cantilever_coupon():
    model=Structure()
    record={'name':'BEAM','start':[0.,0.,0.],'end':[0.,0.,1000.],
            'section_u':[1.,0.,0.],'width_mm':100.,'depth_mm':10.}
    point=[0.,20.,1000.]
    model.member(record,[point],size=50.)
    model.fixed.update(model.members['BEAM']['sections'][0.])
    node=model.attachment('BEAM',point)
    model.loads[node]=[0.,1.,0.]
    return model, {'tip_node':node,'expected_tip_y_mm':1000.**3/(3*7000.*(100*10**3/12))}


def run_coupon(directory, eccentric=False):
    import json
    import os
    import subprocess
    from pathlib import Path
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    structure,basis=cantilever_coupon()
    if eccentric:
        structure.loads[basis['tip_node']]=[0.,0.,1.]
        basis={'tip_node':basis['tip_node'],'expected_tip_z_mm':1000/(7000*100*10)+20**2*1000/(7000*(100*10**3/12))}
    (directory/'coupon.inp').write_text(structure.deck(poisson=0.))
    command=['docker','run','--rm','--network=none','--cpus=1','--memory=2g','--user',f'{os.getuid()}:{os.getgid()}',
             '-e','OMP_NUM_THREADS=1','-v',f'{directory.resolve()}:/output','-w','/output',panel_kernel.IMAGE,
             'timeout','120s','ccx','-i','coupon']
    result=subprocess.run(command,capture_output=True,text=True,timeout=140,check=False)
    (directory/'coupon.log').write_text(result.stdout+result.stderr)
    if result.returncode or '*ERROR' in result.stdout.upper(): raise ValueError('Native member coupon failed')
    output=panel_kernel.read_blocks((directory/'coupon.dat').read_text())
    component=2 if eccentric else 1
    actual=output['displacements'][basis['tip_node']][component]
    relative=abs(actual/basis['expected_tip_z_mm' if eccentric else 'expected_tip_y_mm']-1)
    if relative>.03: raise ValueError(f'Cantilever offset coupling differs {relative:.3%}')
    force=np.sum([output['forces'][n] for n in structure.fixed],axis=0)+structure.loads[basis['tip_node']]
    moment=sum((np.cross(structure.nodes[n],output['forces'][n]) for n in structure.fixed),np.zeros(3))
    moment+=np.cross(structure.nodes[basis['tip_node']],structure.loads[basis['tip_node']])
    if max(abs(moment))>.01:raise ValueError('Cantilever support moment failed')
    if max(abs(force))>1e-4:raise ValueError('Cantilever equilibrium failed')
    report={**basis,'actual_tip_mm':actual,'component':component+1,'relative_error':relative,'force_residual_n':force.tolist(),
            'moment_residual_nmm':moment.tolist(),'eccentric_axial_case':eccentric,
            'qualified_for_design':False}
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def distribute_wrench(points, force, moment, centre, weights=None):
    """Statically equivalent nodal loads, without adding any kinematic ties."""
    points=np.asarray(points,float);centre=np.asarray(centre,float)
    force=np.asarray(force,float);moment=np.asarray(moment,float)
    if len(points)<3:raise ValueError('At least three noncollinear load points required')
    blocks=[]
    for r in points-centre:
        cross=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]])
        blocks.append(np.vstack((np.eye(3),cross/100.)))
    matrix=np.hstack(blocks)
    weight=np.ones(len(points)*3) if weights is None else np.repeat(weights,3)
    target=np.r_[force,moment/100.]
    gram=(matrix*weight)@matrix.T
    if np.linalg.matrix_rank(gram)<6:raise ValueError('Load points cannot transfer full force/moment')
    values=weight*(matrix.T@np.linalg.solve(gram,target))
    if np.max(abs(matrix@values-target))>1e-7:raise ValueError('Force/moment load projection failed')
    return values.reshape(-1,3)


def traction_wrench(positions, signed_area_weights, force, moment, centre):
    """Consistent surface traction plus an explicitly separated nodal couple."""
    values=np.asarray(signed_area_weights)[:,None]*np.asarray(force)
    existing=np.sum(np.cross(np.asarray(positions)-centre,values),axis=0)
    correction=distribute_wrench(positions,[0,0,0],np.asarray(moment)-existing,centre,
                                  np.abs(signed_area_weights))
    return values+correction


def add_load(structure, tag, value):
    structure.loads[tag]=(np.asarray(structure.loads.get(tag,[0.,0.,0.]))+value).tolist()


def contained_patch(x, y, width, bounds):
    """Finite square load footprint must fit entirely on its independent panel."""
    if not math.isfinite(width) or width<=0:raise ValueError('Positive finite patch size required')
    patch=(x-width/2,x+width/2,y-width/2,y+width/2)
    left,right,low,high=bounds
    if patch[0]<left or patch[1]>right or patch[2]<low or patch[3]>high:
        raise ValueError('Load patch extends outside independent panel')
    return patch


def current_frame(module, stiffness=1000., mode='coupled', hold='F10', pounds=250., load_kind='full',
                  frame_size=100., panel_size=80., patch_size=20.):
    """Build fresh current-member mechanics; no frame connectivity from old meshes.

    Modes frame_only/panel_credit apply identical framing nodal loads. Mode
    coupled applies the load through its actual panel patch instead. Closed
    bearing is checked after solution and rejected if tensile bearing occurs.
    """
    from fea.horizontal_frame_members import extract
    from mini_moonboard import panel_grid_v2
    if mode not in ('frame_only','panel_credit','coupled'):raise ValueError('Unknown topology mode')
    if pounds not in (250.,300.) or load_kind not in ('normal','full'):raise ValueError('Unknown load case')
    raw={p.name:p for p in module.wood_parts()}
    records=extract(module);by_name={r['name']:r for r in records}
    connections=module.connections()
    planned={name:[] for name in by_name}
    angles={};bolts=[];panel_points={};bearings=[];gravity_points={}
    for c in connections:
        if c.name.startswith('clip_'):
            point=np.asarray((c.start+c.direction*module.hardware.ML['thickness']).toTuple())
            angles.setdefault(c.members[0],[]).append((c.name,c.members[1],point))
            planned[c.members[1]].append(point)
        elif isinstance(c,module.timber.PanelScrew):
            point=np.asarray((c.start+c.direction*(panel_kernel.THICKNESS/2)).toTuple())
            panel_points.setdefault(c.members[0],[]).append((c.name,c.members[1],point))
            planned[c.members[1]].append(point)
        elif c.kind=='bolt':
            if len(c.members)!=2:raise ValueError('Expected two-member current bolt')
            point=np.asarray((c.start+c.direction*(2.032+38.1)).toTuple())
            bolts.append((c.name,*c.members,point))
            for name in c.members:planned[name].append(point)
        else:raise ValueError('Unrepresented current mechanical connection')
    for r in records:
        name=r['name'];centre=np.array(raw[name].shape.Center().toTuple())
        gravity_points[name]=centre;planned[name].append(centre)
        if name.startswith(('base_side_','base_principal_')):
            point=np.asarray(r['start']);bearings.append((name,'base_header',point))
            planned[name].append(point);planned['base_header'].append(point)
        elif name.startswith('base_post_'):
            point=np.asarray(r['end']);bearings.append(('base_header',name,point))
            planned[name].append(point);planned['base_header'].append(point)
    structure=Structure()
    for r in records:structure.member(r,planned[r['name']],frame_size)
    for name,entries in angles.items():
        if len(entries)!=6:raise ValueError('Actual angle must retain six separate screw stations')
        steel=structure.rigid_angle(name,[p for _,_,p in entries])
        for (screw,member,point),tag in zip(entries,steel,strict=True):
            wood=structure.attachment(member,point);structure.spring(wood,tag,stiffness,screw)
    for name,first,second,point in bolts:
        structure.spring(structure.attachment(first,point),structure.attachment(second,point),stiffness,name)
    for first,second,point in bearings:
        structure.spring(structure.attachment(first,point),structure.attachment(second,point),1.e6,
                         'bearing_'+first+'_'+second,dofs=(3,),bearing=True)
    for r in records:
        if r['name'].startswith(('base_post_','lumber_leg_')):
            structure.fixed.update(structure.members[r['name']]['sections'][0.])
        tag=structure.attachment(r['name'],gravity_points[r['name']])
        add_load(structure,tag,[0,0,-raw[r['name']].shape.Volume()*6.e-7*9.80665])
    # Panel attachment points exist even in the frame-only reference so applied
    # framing forces are identical without constructing a virtual diaphragm.
    receiver_tags={}
    for name,points in panel_points.items():
        receiver_tags[name]=[(screw,structure.attachment(receiver,point),point) for screw,receiver,point in points]
    hx,hs=panel_grid_v2.main_tnut_datums()[hold];hx-=module.b.HALF
    loaded_name=f"main_{'lower' if hs<module.b.HALF else 'upper'}_{'left' if hx<0 else 'right'}"
    outward=-np.asarray(module.b.normal().toTuple());along=np.asarray((module.b.point(0,1,0)-module.b.point(0,0,0)).toTuple())
    target=np.asarray(module.b.point(hx,hs,-panel_kernel.THICKNESS/2).toTuple())
    force=np.array([0.,300.,-2*pounds*.45359237*9.80665])
    if load_kind=='normal':force=np.dot(force,outward)*outward
    moment=np.cross(outward*(100.+panel_kernel.THICKNESS/2),force)
    loaded_left=-module.b.HALF if hx<0 else 0.
    loaded_low=0. if hs<module.b.HALF else module.b.HALF
    patch=contained_patch(hx,hs,patch_size,(loaded_left,loaded_left+module.b.HALF,loaded_low,loaded_low+module.b.HALF))
    panel_loads={}
    for name,part in raw.items():
        if not name.startswith(('main_','kicker_')):continue
        main=name.startswith('main_');left=-module.b.HALF if name.endswith('left') else 0.;right=left+module.b.HALF
        low=(module.b.HALF if 'upper' in name else 0.) if main else 0.
        high=low+module.b.HALF if main else module.base.HEADER_TOP
        points=panel_points[name]
        coords=[]
        for _,_,point in points:
            y=float(np.dot(point-np.asarray(module.b.point(0,0,0).toTuple()),along)) if main else point[2]
            coords.append((float(point[0]),y))
        landmarks_x=[x for x,_ in coords];landmarks_y=[y for _,y in coords]
        if name==loaded_name:
            landmarks_x+=list(patch[:2]);landmarks_y+=list(patch[2:])
        xs=panel_kernel.mesh_axes(left,right,panel_size,landmarks_x);ys=panel_kernel.mesh_axes(low,high,panel_size,landmarks_y)
        local,elements,lookup=panel_kernel.grid(xs,ys)
        tags={}
        if mode!='frame_only':
            for n,(x,y,_) in local.items():
                world=module.b.point(x,y,-panel_kernel.THICKNESS/2).toTuple() if main else (x,module.base.HEADER_FRONT_Y+panel_kernel.THICKNESS/2,y)
                tags[n]=structure.node(world)
            for ids in elements.values():structure.element('S8',[tags[n] for n in ids],name)
            structure.panels[name]={'nodes':list(tags.values())}
            for (screw,wood,_),(x,y) in zip(receiver_tags[name],coords,strict=True):
                node=tags[lookup[round(x,8),round(y,8)]]
                structure.spring(wood,node,stiffness,screw)
        weight=np.array([0.,0.,-part.shape.Volume()*6.e-7*9.80665]);cg=np.array(part.shape.Center().toTuple())
        # The control pair loads the same receiver nodes; actual coupled mode
        # applies panel self-weight and climber loading to physical panel nodes.
        if mode=='coupled':
            area_weights,_=panel_kernel.pressure_load(local,elements,(left,right,low,high),1.)
            loadtags=[tags[n] for n in area_weights];positions=[structure.nodes[n] for n in loadtags]
        else:
            loadtags=[n for _,n,_ in receiver_tags[name]];positions=[p for _,_,p in receiver_tags[name]]
        if mode=='coupled':
            values=traction_wrench(positions,list(area_weights.values()),weight,[0,0,0],cg)
        else:
            values=distribute_wrench(positions,weight,[0,0,0],cg)
        for tag,value in zip(loadtags,values,strict=True):add_load(structure,tag,value)
        if name==loaded_name:
            if mode=='coupled':
                patch_weights,_=panel_kernel.pressure_load(local,elements,patch,1.)
                loadtags=[tags[n] for n in patch_weights]
                positions=[structure.nodes[n] for n in loadtags]
            else:
                loadtags=[n for _,n,_ in receiver_tags[name]];positions=[p for _,_,p in receiver_tags[name]]
                weights=[1/(np.linalg.norm(np.array(p)-target)**2+100.**2) for p in positions]
            if mode=='coupled':
                values=traction_wrench(positions,list(patch_weights.values()),force,moment,target)
            else:
                values=distribute_wrench(positions,force,moment,target,weights)
            for tag,value in zip(loadtags,values,strict=True):add_load(structure,tag,value)
            panel_loads={'nodes':loadtags,'forces_xyz_n':values.tolist()}
    metadata={'candidate':module.KEY,'mode':mode,'hold':hold,'pounds':pounds,'load_kind':load_kind,
              'force_xyz_n':force.tolist(),'moment_at_panel_midplane_nmm':moment.tolist(),
              'target_xyz_mm':target.tolist(),'standoff_from_front_mm':100.,'stiffness_n_per_mm':stiffness,
              'frame_size_mm':frame_size,'panel_size_mm':panel_size,'members':records,'panel_load':panel_loads,
              'assumed_modulus_mpa':7000.,'assumed_poisson_ratio':.3,
              'panel_patch_size_mm':patch_size,'panel_patch_mm':list(patch),'panel_patch_load_type':'Consistent uniform vector traction plus zero-resultant nodal couple; not a physical hold-seat traction solution',
              'qualified_for_design':False,'actual_joint_demands_qualified':False,
              'limits':__doc__+' Closed normal bearing springs must stay compressive. Fasteners/angles have no rated compliance; angle steel is rigid. Raw wood mass 600kg/m3; member weight concentrated at its actual centroid; panel weight distributed preserving resultants; hardware/holds omitted. Panel holes omitted. No implicit panel seam ties. Framing-load control pair isolates passive panel stiffness under identical discrete force/moment loads; it does not establish physical hold load sharing.'}
    return structure,metadata


def record_structure(structure, metadata, active_bearings=None):
    return {**metadata, 'nodes': structure.nodes, 'elements': structure.elements,
            'loads': structure.loads, 'fixed_nodes': sorted(structure.fixed),
            'equations': structure.equations,
            'springs':[{**r,'active':not r['bearing_closed_assumption'] or active_bearings is None or r['name'] in active_bearings} for r in structure.springs],
            'panel_nodes': {k:v['nodes'] for k,v in structure.panels.items()},
            'rotation_master_nodes':sorted(structure.rotation_masters)}


def displacement_roundoff(data):
    """Half-last-place intervals from actual printed displacement tokens."""
    import re
    blocks=list(re.finditer(r'^\s*displacements\s*\([^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)',data,re.MULTILINE|re.DOTALL))
    if len(blocks)!=1:raise ValueError('Expected one displacement precision block')
    result={}
    for line in blocks[0][1].splitlines():
        cells=line.split()
        if len(cells)!=4 or not cells[0].isdigit():continue
        row=[]
        for token in cells[1:]:
            mantissa,exponent=token.upper().replace('D','E').split('E')
            places=len(mantissa.split('.')[1]) if '.' in mantissa else 0
            row.append(.5*10.**(int(exponent)-places))
        result[int(cells[0])]=row
    return result


def mpc_intervals(equations, displacements, roundoff):
    rows=[]
    for terms in equations:
        residual=abs(sum(v*displacements[n][d-1] for n,d,v in terms))
        uncertainty=sum(abs(v)*roundoff[n][d-1] for n,d,v in terms)
        rows.append((residual,uncertainty,max(0.,residual-uncertainty)))
    return {'maximum_printed_residual_mm':max((r[0] for r in rows),default=0.),
            'maximum_rounding_interval_radius_mm':max((r[1] for r in rows),default=0.),
            'maximum_interval_distance_from_zero_mm':max((r[2] for r in rows),default=0.),
            'passed':all(r[2]<=1.e-5 for r in rows),
            'criterion':'Printed-displacement residual interval intersects +/-1e-5 mm; no claim of unprinted precision.'}


def assess(record, data):
    """Independent global resultants and explicit finite-connector force recovery."""
    output=panel_kernel.read_blocks(data)
    nodes={int(n):np.asarray(p) for n,p in record['nodes'].items()}
    loads={int(n):np.asarray(f) for n,f in record['loads'].items()}
    u=output['displacements'];rf=output['forces']
    if set(nodes)-set(u) or set(record['fixed_nodes'])-set(rf):
        raise ValueError('Incomplete native nodal output')
    if not np.isfinite(np.asarray(list(u.values()))).all():raise ValueError('Nonfinite displacement')
    applied=sum(loads.values(),np.zeros(3))
    support=sum((np.asarray(rf[n]) for n in record['fixed_nodes']),np.zeros(3))
    moment=sum((np.cross(nodes[n],f) for n,f in loads.items()),np.zeros(3))
    moment+=sum((np.cross(nodes[n],rf[n]) for n in record['fixed_nodes']),np.zeros(3))
    residual=applied+support
    mpc=mpc_intervals(record['equations'],u,displacement_roundoff(data) if record['equations'] else {})
    interpolation=mpc['maximum_printed_residual_mm']
    connectors={};bearing=[]
    for spring in record['springs']:
        a,b=spring['nodes'];d=spring['dof']-1
        delta=u[b][d]-u[a][d]
        active=spring.get('active',True)
        value=spring['stiffness_n_per_mm']*delta if active else 0.
        row=connectors.setdefault(spring['name'],{'force_on_first_xyz_n':[0.,0.,0.],
            'first_point_xyz_mm':nodes[a].tolist(),'second_point_xyz_mm':nodes[b].tolist()})
        row['force_on_first_xyz_n'][d]=value
        if spring['bearing_closed_assumption']:
            bearing.append({'name':spring['name'],'opening_mm':-delta,
                            'compression_force_n':value,'active':active,
                            'compression_only_assumption_satisfied':delta>=-1.e-7 if active else delta<=1.e-7})
    for row in connectors.values():row['force_magnitude_n']=float(np.linalg.norm(row['force_on_first_xyz_n']))
    panel_tags={n for tags in record['panel_nodes'].values() for n in tags}
    timber_tags={n for kind,ids,_ in record['elements'].values() if kind=='C3D20' for n in ids}
    maxima=lambda tags:max((float(np.linalg.norm(u[n])) for n in tags),default=0.)
    load_work=sum(float(np.dot(f,u[n])) for n,f in loads.items())
    force_gate=max(abs(residual))<=.1;moment_gate=max(abs(moment))<=2.
    return {'force_residual_n':residual.tolist(),'moment_residual_nmm':moment.tolist(),
            'maximum_mpc_residual_mm':interpolation,'global_equilibrium_passed':bool(force_gate and moment_gate),
            'mpc_printed_precision_audit':mpc,'mpc_check_passed':mpc['passed'],'closed_bearing_assumption_passed':all(r['compression_only_assumption_satisfied'] for r in bearing),
            'bearings':bearing,'connector_forces':connectors,'load_work_nmm':load_work,
            'maximum_panel_displacement_mm':maxima(panel_tags),
            'maximum_timber_displacement_mm':maxima(timber_tags),
            'maximum_node_displacement_mm':maxima(set(nodes)-set(record['rotation_master_nodes'])),'qualified_for_design':False,
            'actual_joint_demands_qualified':False}


def next_bearing_set(bearings, tolerance=1.e-7):
    """Primal-dual update for zero-clearance, frictionless normal springs."""
    return {r['name'] for r in bearings if
            (r['active'] and r['opening_mm']<=tolerance) or
            (not r['active'] and r['opening_mm'] < -tolerance)}


def source_hashes():
    import hashlib
    from pathlib import Path
    paths=[*Path('mini_moonboard').glob('*.py'),Path(__file__),
           Path('fea/horizontal_frame_members.py'),Path('fea/horizontal_frame_stress.py'),Path(panel_kernel.__file__),
           *[Path('docs')/name for name in ('led-wiring-reference.json','ml24z-reference.json',
                                          'panel-insert-reference.json','ml23z-reference.json')]]
    return {str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run_current(directory, **parameters):
    import hashlib
    import json
    import os
    import subprocess
    from pathlib import Path

    from fea import horizontal_frame_stress
    from mini_moonboard import horizontal_service_frame as module
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    sources=source_hashes()
    structure,metadata=current_frame(module,**parameters)
    metadata['cutouts']=module.cutout_records()
    metadata['stress_output']={'global':True,'variables':['S','COORD'],
                              'integration_points':{'C3D20':27,'S8':27}}
    for name in sources:
        target=directory/'source_snapshots'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(Path(name).read_bytes())
    if sources!=source_hashes():raise ValueError('Source changed during preparation')
    active={r['name'] for r in structure.springs if r['bearing_closed_assumption']}
    seen=set();history=[];converged=False
    for iteration in range(12):
        signature=tuple(sorted(active))
        if signature in seen:break
        seen.add(signature)
        job=directory/f'cycle-{iteration:02d}';job.mkdir()
        record=record_structure(structure,metadata,active)
        (job/'input.json').write_text(json.dumps(record,indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active,stress=True))
        command=['docker','run','--rm','--network=none','--cpus=1','--memory=4g','--user',f'{os.getuid()}:{os.getgid()}',
                 '-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/output','-w','/output',panel_kernel.IMAGE,
                 'timeout','180s','ccx','-i','frame']
        result=subprocess.run(command,capture_output=True,text=True,timeout=200,check=False)
        log=result.stdout+result.stderr;(job/'frame.log').write_text(log)
        if result.returncode or '*ERROR' in log.upper():raise ValueError('Native frame solve failed; inspect raw cycle log')
        data=(job/'frame.dat').read_text()
        report=assess(record,data)
        report['diagnostic_stress']=horizontal_frame_stress.assess(record,data)
        if sources!=source_hashes():raise ValueError('Source changed during solve')
        report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in job.iterdir() if p.is_file()}
        (job/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        history.append({'directory':job.name,'active_bearings':list(signature),
                        'bearing_complementarity_passed':report['closed_bearing_assumption_passed'],
                        'report_sha256':hashlib.sha256((job/'report.json').read_bytes()).hexdigest()})
        if report['closed_bearing_assumption_passed']:
            converged=True;break
        active=next_bearing_set(report['bearings'])
    report={**report,'contact_active_set_converged':converged,'contact_cycles':history,
            'contact_cycle_limit':12,'contact_gap_tolerance_mm':1.e-7,
            'bearing_penalty_n_per_mm':1.e6,'final_cycle_directory':history[-1]['directory'],
            'contact_diagnostic_checks_passed':bool(converged and report['global_equilibrium_passed'] and report['mpc_check_passed']),
            'parameters':parameters,'solver_image':panel_kernel.IMAGE,'source_sha256':sources}
    report['artifact_sha256']={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--mode',choices=('frame_only','panel_credit','coupled'),default='coupled')
    parser.add_argument('--hold',default='F10')
    parser.add_argument('--pounds',type=float,choices=(250.,300.),default=250.)
    parser.add_argument('--load-kind',choices=('normal','full'),default='full')
    parser.add_argument('--stiffness',type=float,default=1000.)
    parser.add_argument('--frame-size',type=float,default=100.)
    parser.add_argument('--panel-size',type=float,default=80.)
    parser.add_argument('--patch-size',type=float,default=20.)
    args=vars(parser.parse_args());directory=args.pop('output')
    report=run_current(directory,**args)
    print({key:report[key] for key in ('global_equilibrium_passed','mpc_check_passed','closed_bearing_assumption_passed','maximum_panel_displacement_mm')})


if __name__=='__main__':main()
