"""Current reinforced assembly demand diagnostic with explicit contact.

Independent shell panels and uncut gross timber solids retain the current
connection layout, including both eight-bolt shoes. Feet and kicker bottoms
use unilateral vertical springs. Post/leg feet have a tangential resultant at
each footprint centroid while any point of that footprint bears; kicker edges
are frictionless and receive only vertical compression-bearing credit. A separate friction-wrench
feasibility check verifies whether those resultants can be distributed over
the actually compressed points. No tangential rotational stiffness is assigned. Rigid shoe/ML bodies, isotropic E=7000 MPa, homogeneous unperforated
panels, gross timber sections, spring stiffness, point contact and omitted
hardware/hold weight remain assumptions. Results predict this stated model;
they do not qualify the physical frame, connections, plywood or floor.
"""
import argparse
import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from fea import horizontal_panel_frame as frame
from fea import round_insert_frame as shared
from fea import shell_surface_recovery
from fea.horizontal_panel_frame import (
    Structure,
    add_load,
    contained_patch,
    distribute_wrench,
    panel_kernel,
    traction_wrench,
)
from fea.round_structural_frame import SeatingModule


def add_floor(structure, name, wood, point, ownership, body, stiffness=1.e5):
    """A point can transmit compression and assumed sticking shear, never tension."""
    ground = structure.node(point)
    structure.fixed.add(ground)
    shared.normal_contact(structure, name, wood, [ground], [1.], point, [0.,0.,1.], stiffness)
    ownership[name] = {'first': body, 'second': 'floor', 'point': list(point),
                       'scalar_normal': [0.,0.,1.], 'ground_node': ground}


def add_member_floor(structure, name, ownership, shape):
    points = {tuple(v.Center().toTuple()) for v in shape.Vertices() if abs(v.Z)<1.e-6}
    if len(points) != 4:
        raise ValueError('Require exact four-corner current member floor footprint: '+name)
    for i, point in enumerate(sorted(points)):
        wood = floor_attachment(structure, name, point)
        add_floor(structure, 'floor_'+name+'_'+str(i), wood, point, ownership, name)
    point=np.mean(list(points),axis=0)
    wood=floor_attachment(structure,name,point)
    add_foot_friction(structure,name,wood,point,ownership)


def add_foot_friction(structure, body, wood, point, ownership):
    name='floor_'+body+'_friction'
    ground=structure.node(point)
    structure.fixed.add(ground)
    structure.spring(wood,ground,1.e6,name,dofs=(1,2),bearing=True)
    ownership[name]={'first':body,'second':'floor','point':list(point)}


def floor_attachment(structure, member, point):
    """Rigid endpoint cross-section offset to the actual level bevel contact."""
    m = structure.members[member]
    # Endpoint section is an explicit plane-section bevel approximation.
    ids = m['sections'][0.]
    # Offset along grain is retained with a rigid section rotation extracted
    # from opposing section translations. A beam-end assumption, not a clamp.
    from fea.horizontal_panel_frame import distribute_wrench
    node = structure.node(point)
    coords=np.array([structure.nodes[n] for n in ids])
    for dof in range(3):
        force=np.eye(3)[dof]
        loads=distribute_wrench(coords,force,[0.,0.,0.],point)
        terms=[(node,dof+1,1.)]
        terms += [(n,j+1,-float(f[j])) for n,f in zip(ids,loads,strict=True)
                  for j in range(3) if abs(f[j])>1.e-12]
        structure.equations.append(terms)
    return node


def add_panel_floor(structure, name, ownership):
    nodes = structure.panels[name]['nodes']
    bottom = [n for n in nodes if abs(structure.nodes[n][2])<1.e-6]
    for i,node in enumerate(bottom):
        add_floor(structure, 'floor_'+name+'_'+str(i), node, structure.nodes[node], ownership, name)
    # A kicker edge has only compression-bearing credit. No tangential
    # friction restraint or yaw restraint is assigned to the plywood edge.


def prepare(module, stiffness=1000., mode='coupled', hold='F10', pounds=250., load_kind='full',
                  frame_size=100., panel_size=80., patch_size=20.):
    """Build the current independent-panel, gross-member contact diagnostic."""
    from fea.horizontal_frame_members import axes, member_record
    from mini_moonboard import panel_grid_v2
    if module.KEY != 'round-reinforcement-development' or mode != 'coupled':
        raise ValueError('Require current reinforced candidate with independent coupled panels')
    if len(module.panel_connections()) != 66:
        raise ValueError('Require all 66 current panel/kicker attachments')
    if pounds not in (250.,300.) or load_kind not in ('normal','full'):raise ValueError('Unknown load case')
    raw={p.name:p for p in module.wood_parts()}
    records = [member_record(p, *axes(module, p.name)) for p in module.uncut_wood_parts()
               if not p.name.startswith(('main_', 'kicker_'))]
    by_name={r['name']:r for r in records}
    connections=module.connections()
    planned={name:[] for name in by_name}
    angles={};bolts=[];panel_points={};bearings=[];gravity_points={}
    ownership = {}
    for c in connections:
        if c.name.startswith('steel_shoe_'):
            point=np.asarray((c.start+c.direction*(module.base_revision.WASHER+module.base_revision.THICKNESS)).toTuple())
            angles.setdefault(c.members[0],[]).append((c.name,c.members[1],point))
            planned[c.members[1]].append(point)
            ownership[c.name] = {'first': c.members[1], 'second': c.members[0], 'point': point.tolist(), 'axis': list(c.direction.toTuple())}
        elif c.name.startswith('clip_'):
            point=np.asarray((c.start+c.direction*module.hardware.ML['thickness']).toTuple())
            angles.setdefault(c.members[0],[]).append((c.name,c.members[1],point))
            planned[c.members[1]].append(point)
            ownership[c.name] = {'first': c.members[1], 'second': c.members[0], 'point': point.tolist(), 'axis': list(c.direction.toTuple())}
        elif isinstance(c,module.timber.PanelScrew):
            point=np.asarray((c.start+c.direction*(panel_kernel.THICKNESS/2)).toTuple())
            panel_points.setdefault(c.members[0],[]).append((c.name,c.members[1],point))
            planned[c.members[1]].append(point)
            ownership[c.name] = {'first': c.members[1], 'second': c.members[0], 'point': point.tolist(), 'axis': list(c.direction.toTuple())}
        elif c.kind=='bolt':
            if len(c.members)!=2:raise ValueError('Expected two-member current bolt')
            point=np.asarray((c.start+c.direction*(2.032+38.1)).toTuple())
            bolts.append((c.name,*c.members,point))
            for name in c.members:planned[name].append(point)
            ownership[c.name] = {'first': c.members[0], 'second': c.members[1], 'point': point.tolist(), 'axis': list(c.direction.toTuple())}
        else:raise ValueError('Unrepresented current mechanical connection')
    shoe_header_points = {}
    for side,sign in (('left',-1.),('right',1.)):
        bb=raw['base_header'].shape.BoundingBox()
        points=[np.array([sign*x,y,bb.zmax]) for x in (module.base_revision.FOOT_INBOARD_X,min(module.b.HALF,module.base_revision.FOOT_OUTBOARD_X))
                for y in (max(bb.ymin,module.base_revision.FOOT_Y[0]),min(bb.ymax,module.base_revision.FOOT_Y[1]))]
        shoe_header_points['clip_steel_shoe_'+side]=points
        planned['base_header'].extend(points)
    for r in records:
        name=r['name'];centre=np.array(raw[name].shape.Center().toTuple())
        gravity_points[name]=centre;planned[name].append(centre)
        if name.startswith('base_principal_'):
            point=np.asarray(r['start']);bearings.append((name,'base_header',point))
            planned[name].append(point);planned['base_header'].append(point)
        elif name.startswith('base_post_'):
            point=np.asarray(r['end']);bearings.append(('base_header',name,point))
            planned[name].append(point);planned['base_header'].append(point)
    structure=Structure()
    for r in records:structure.member(r,planned[r['name']],frame_size)
    for name,entries in angles.items():
        if len(entries) != (8 if name.startswith('clip_steel_shoe_') else 6):
            raise ValueError('Unexpected angle/shoe attachment count')
        seat_points = []
        if name.startswith('clip_steel_shoe_'):
            side=name.rsplit('_',1)[1]
            rim='base_side_'+side
            shape=raw[rim].shape
            z=shape.BoundingBox().zmin
            seat_points=[np.array(v.Center().toTuple()) for v in shape.Vertices() if abs(v.Z-z)<1.e-6]
            seat_points=list({tuple(p):p for p in seat_points}.values())
            if len(seat_points)!=4: raise ValueError('Require four rim seat corners')
        header_points=shoe_header_points.get(name,[])
        steel=structure.rigid_angle(name,[p for _,_,p in entries]+seat_points+header_points)
        for (screw,member,point),tag in zip(entries,steel[:len(entries)],strict=True):
            wood=structure.attachment(member,point);structure.spring(wood,tag,stiffness,screw)
        for index,(point,tag) in enumerate(zip(seat_points,steel[len(entries):len(entries)+len(seat_points)],strict=True)):
            contact='seat_'+name+'_'+str(index)
            wood=floor_attachment(structure,rim,point)
            structure.spring(wood,tag,1.e6,contact,dofs=(3,),bearing=True)
            ownership[contact]={'first':rim,'second':name,'point':point.tolist()}
        for index,(point,tag) in enumerate(zip(header_points,steel[len(entries)+len(seat_points):],strict=True)):
            contact='foot_'+name+'_'+str(index)
            wood=structure.attachment('base_header',point)
            structure.spring(tag,wood,1.e6,contact,dofs=(3,),bearing=True)
            ownership[contact]={'first':name,'second':'base_header','point':point.tolist()}
    for name,first,second,point in bolts:
        structure.spring(structure.attachment(first,point),structure.attachment(second,point),stiffness,name)
    for first,second,point in bearings:
        name = 'bearing_'+first+'_'+second
        structure.spring(structure.attachment(first,point),structure.attachment(second,point),1.e6,
                         name,dofs=(3,),bearing=True)
        ownership[name] = {'first': first, 'second': second, 'point': point.tolist()}
    for r in records:
        if r['name'].startswith(('base_post_','lumber_leg_')):
            add_member_floor(structure, r['name'], ownership, raw[r['name']].shape)
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
    for panel in structure.panels:
        if panel.startswith('kicker_'):
            add_panel_floor(structure, panel, ownership)
    contacts = shared.seating_contacts(structure, SeatingModule(module), samples=2, penalty=100.)
    for c in contacts:
        ownership[c['name']] = {'first': c['member'], 'second': c['panel'], 'point': c['point_xyz_mm'], 'scalar_normal': c['inward_xyz']}
    metadata={'candidate':module.KEY,'mode':mode,'hold':hold,'pounds':pounds,'load_kind':load_kind,
              'force_xyz_n':force.tolist(),'moment_at_panel_midplane_nmm':moment.tolist(),
              'target_xyz_mm':target.tolist(),'standoff_from_front_mm':100.,'stiffness_n_per_mm':stiffness,
              'frame_size_mm':frame_size,'panel_size_mm':panel_size,'members':records,'panel_load':panel_loads,
              'assumed_modulus_mpa':7000.,'assumed_poisson_ratio':.3,
              'panel_patch_size_mm':patch_size,'panel_patch_mm':list(patch),'panel_patch_load_type':'Consistent uniform vector traction plus zero-resultant nodal couple; not a physical hold-seat traction solution',
              'qualified_for_design':False,'actual_joint_demands_qualified':False,
              'connection_ownership': ownership,
              'gravity_points': {name: {'point': point.tolist(), 'force': [0.,0.,-raw[name].shape.Volume()*6.e-7*9.80665]} for name,point in gravity_points.items()},
              'limits':__doc__+' Closed normal bearing springs must stay compressive. Fasteners/angles have no rated compliance; angle steel is rigid. Raw wood mass 600kg/m3; member weight concentrated at its actual centroid; panel weight distributed preserving resultants; hardware/holds omitted. Panel holes omitted. No implicit panel seam ties. Framing-load control pair isolates passive panel stiffness under identical discrete force/moment loads; it does not establish physical hold load sharing.'}
    metadata['seating_contacts'] = contacts
    metadata['limits'] = __doc__
    return structure,metadata



def physical_forces(record, result):
    """Recover physical vector forces from both Cartesian and normal-only springs."""
    rows = {}
    for name, owner in record['connection_ownership'].items():
        found = result['connector_forces'][name]
        force = np.array(found['force_on_first_xyz_n'])
        if 'scalar_normal' in owner:
            force = force[0]*np.array(owner['scalar_normal'])
        row = {**owner, 'force_on_first_xyz_n': force.tolist(),
               'force_on_second_xyz_n': (-force).tolist()}
        if 'axis' in owner:
            axis = np.array(owner['axis'])
            axial = float(np.dot(force, axis))
            row.update(axial_along_installation_direction_n=axial,
                       transverse_shear_n=float(np.linalg.norm(force-axial*axis)))
        rows[name] = row
    return rows


def member_sections(record, connections):
    """Exact free-body resultants of this solved connector-load model.

    Scan both sides of every load jump above the first full-width bevel section.
    Between jumps forces are constant and moments affine. End-bevel regions and
    local load introduction are deliberately outside these plane-section cuts.
    """
    outputs = {}
    for member in record['members']:
        name = member['name']
        entries = [(np.array(c['point']), np.array(c['force_on_first_xyz_n']))
                   for c in connections.values() if c['first'] == name]
        entries += [(np.array(c['point']), np.array(c['force_on_second_xyz_n']))
                    for c in connections.values() if c['second'] == name]
        gravity = record['gravity_points'][name]
        entries.append((np.array(gravity['point']), np.array(gravity['force'])))
        start, end = np.array(member['start']), np.array(member['end'])
        axis, u, v = (np.array(member[k]) for k in ('axis','section_u','section_v'))
        length = float(np.linalg.norm(end-start))
        low = max(0., member['verification_grain_interval_mm'][0]-float(np.dot(start,axis)))
        stations = [float(np.dot(p-start,axis)) for p,_ in entries]
        cuts = sorted({low, length, *(s for s in stations if low <= s <= length)})
        sections = []
        for station in cuts:
            origin = start+station*axis
            for inclusive in (False,True):
                chosen = [(p,f) for (p,f),s in zip(entries,stations,strict=True)
                          if s>station+1.e-7 or (inclusive and abs(s-station)<=1.e-7)]
                force = sum((f for _,f in chosen), np.zeros(3))
                moment = sum((np.cross(p-origin,f) for p,f in chosen),np.zeros(3))
                sections.append({'station_along_grain_mm': station,
                    'include_station_loads': inclusive, 'origin_xyz_mm': origin.tolist(),
                    'axial_n_tension_positive': float(np.dot(force,axis)),
                    'shear_u_n': float(np.dot(force,u)), 'shear_v_n': float(np.dot(force,v)),
                    'moment_u_nmm': float(np.dot(moment,u)), 'moment_v_nmm': float(np.dot(moment,v)),
                    'torsion_nmm': float(np.dot(moment,axis)),
                    'upper_load_force_xyz_n': force.tolist(),
                    'upper_load_moment_xyz_nmm': moment.tolist()})
        residual_force = sum((f for _,f in entries),np.zeros(3))
        residual_moment = sum((np.cross(p-start,f) for p,f in entries),np.zeros(3))
        outputs[name] = {'member': member, 'length_mm': length,
                        'section_valid_from_mm': low, 'sections': sections,
                        'force_residual_n': residual_force.tolist(),
                        'moment_residual_nmm': residual_moment.tolist()}
    return outputs


def assess(record, data, frd, expansion):
    # Tangential sticking springs share the corresponding normal contact's
    # active state. Their signed shear is not a compression-only force test.
    ordinary = {**record, 'springs': [dict(s, bearing_closed_assumption=False)
                  if s['name'].endswith('_friction') else s for s in record['springs']]}
    result = shell_surface_recovery.assess(ordinary,data,frd,expansion)
    physical = physical_forces(record,result)
    result['physical_connection_forces'] = physical
    result['member_section_demands'] = member_sections(record,physical)
    contacts = [{'name':name,'body':c['first'],'point_xyz_mm':c['point'],
                 'normal_n':c['force_on_first_xyz_n'][2]}
                for name,c in physical.items() if c['second']=='floor' and not name.endswith('_friction')]
    feet = []
    for name,c in physical.items():
        if c['second']!='floor' or not name.endswith('_friction'):
            continue
        points=[r for r in contacts if r['body']==c['first']]
        force=np.array(c['force_on_first_xyz_n'])
        feet.append({'body':c['first'],'resultant_point_xyz_mm':c['point'],
                     'tangential_force_xyz_n':force.tolist(),
                     **foot_friction_witness(points,c['point'],force)})
    result['floor_foot_friction_demands']=feet
    result['floor_contact_demands'] = contacts
    # RF at a fixed node used as an MPC independent variable omits scalar
    # normal transfer in native DAT. Sum physical spring reactions instead.
    loads=[(np.array(record['nodes'][n] if n in record['nodes'] else record['nodes'][str(n)]),np.array(f)) for n,f in record['loads'].items()]
    supports=[(np.array(c['point']),np.array(c['force_on_first_xyz_n'])) for c in physical.values() if c['second']=='floor']
    force=sum((f for _,f in loads+supports),np.zeros(3))
    moment=sum((np.cross(p,f) for p,f in loads+supports),np.zeros(3))
    result['native_fixed_node_resultants']={'force_residual_n':result['force_residual_n'],'moment_residual_nmm':result['moment_residual_nmm']}
    result['force_residual_n']=force.tolist()
    result['moment_residual_nmm']=moment.tolist()
    result['global_equilibrium_passed']=bool(max(abs(force))<=.1 and max(abs(moment))<=2.)
    result['reaction_recovery']='Physical normal and tangential floor spring forces; native fixed-node RF omits scalar MPC normal transfer'
    return result


def active_with_friction(normal_names, spring_names, ownership=None):
    active = set(normal_names)
    if ownership is None:
        active.update(name+'_friction' for name in normal_names if name+'_friction' in spring_names)
    else:
        bodies={ownership[name]['first'] for name in normal_names if name in ownership and ownership[name]['second']=='floor'}
        active.update(name for name in spring_names if name.endswith('_friction') and ownership[name]['first'] in bodies)
    return active


def foot_friction_witness(points, center, tangential, directions=32):
    """Find a conservative polygonal friction-cone force/yaw certificate.

    The solved normal reactions are held fixed. Nonnegative force rays inside
    each exact Coulomb disk reproduce both resultant shear and its yaw moment.
    Minimizing mu provides a sufficient coefficient, not the exact disk optimum.
    """
    center=np.asarray(center,dtype=float)
    tangential=np.asarray(tangential,dtype=float)
    valid=[p for p in points if p['normal_n']>1.e-8]
    total_normal=sum(p['normal_n'] for p in valid)
    force_only_mu=float(np.linalg.norm(tangential[:2])/total_normal) if total_normal else None
    necessary={'total_compression_n':total_normal,
               'total_tangential_force_n':float(np.linalg.norm(tangential[:2])),
               'necessary_force_only_coefficient':force_only_mu,
               'assumed_friction_checks':[{'coefficient':mu,
                   'force_only_ratio':force_only_mu/mu if force_only_mu is not None else None,
                   'necessary_force_bound_failed':bool(force_only_mu is not None and force_only_mu>mu)}
                    for mu in (.2,.4)]}
    if not valid:
        return {**necessary,'friction_wrench_feasible':bool(np.linalg.norm(tangential)<1.e-8),
                'sufficient_friction_coefficient':0. if np.linalg.norm(tangential)<1.e-8 else None,
                'witness':[]}
    angle=np.arange(directions)*2*np.pi/directions
    rays=np.array([np.cos(angle),np.sin(angle)]).T
    count=len(valid)*directions
    equality=np.zeros((3,count+1))
    inequality=np.zeros((len(valid),count+1))
    for i,p in enumerate(valid):
        block=slice(i*directions,(i+1)*directions)
        dx,dy=(np.array(p['point_xyz_mm'])-center)[:2]
        equality[:2,block]=rays.T
        equality[2,block]=dx*rays[:,1]-dy*rays[:,0]
        inequality[i,block]=1.
        inequality[i,-1]=-p['normal_n']
    objective=np.zeros(count+1)
    objective[-1]=1.
    target=np.array([*tangential[:2],0.])
    solution=linprog(objective,A_eq=equality,b_eq=target,A_ub=inequality,
                     b_ub=np.zeros(len(valid)),bounds=(0.,None),method='highs')
    if not solution.success:
        return {**necessary,'friction_wrench_feasible':False,'sufficient_friction_coefficient':None,
                'witness':[],'reason':solution.message}
    witness=[]
    for i,p in enumerate(valid):
        force=solution.x[i*directions:(i+1)*directions]@rays
        witness.append({**p,'shear_xy_n':force.tolist(),
                        'actual_coefficient':float(np.linalg.norm(force)/p['normal_n'])})
    residual=equality@solution.x-target
    mu=float(solution.x[-1])
    verified=bool(max(abs(residual))<1.e-5 and all(w['actual_coefficient']<=mu+1.e-8 for w in witness))
    return {**necessary,'friction_wrench_feasible':verified,'sufficient_friction_coefficient':mu,
            'force_xy_and_yaw_residual_n_nmm':residual.tolist(),
            'polygon_direction_count':directions,'witness':witness}


def repository_source_closure(seeds):
    """Follow repository Python imports, including imports inside lazy functions."""
    root=Path.cwd().resolve()
    pending=[Path(p).resolve() for p in seeds]
    found=set()
    while pending:
        path=pending.pop()
        if path in found or not path.is_file() or path.suffix!='.py':
            continue
        relative=path.relative_to(root)
        if relative.parts[0] not in ('fea','mini_moonboard'):
            continue
        found.add(path)
        package=list(relative.with_suffix('').parts[:-1])
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):
                modules=[alias.name.split('.') for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix=package[:len(package)-node.level+1] if node.level else []
                prefix+=node.module.split('.') if node.module else []
                modules=[prefix,*[prefix+alias.name.split('.') for alias in node.names if alias.name!='*']]
            for names in modules:
                if not names or names[0] not in ('fea','mini_moonboard'):
                    continue
                pending.append(root.joinpath(*names).with_suffix('.py'))
                pending.extend(root.joinpath(*names[:i],'__init__.py') for i in range(1,len(names)+1))
    return sorted(found)


def sources():
    paths=repository_source_closure([Path(__file__),*Path('mini_moonboard').glob('*.py')])
    paths += list(Path('docs').glob('*reference.json'))
    paths += [Path('pyproject.toml'),Path('uv.lock')]
    return {str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(output, **parameters):
    from mini_moonboard import round_reinforcement_frame as module
    directory=Path(output)
    directory.mkdir(parents=True,exist_ok=False)
    before=sources()
    structure,metadata=prepare(module,**parameters)
    if before!=sources():
        raise ValueError('Consumed source changed while preparing model')
    for name,digest in before.items():
        content=Path(name).read_bytes()
        if hashlib.sha256(content).hexdigest()!=digest:
            raise ValueError('Consumed source changed before snapshot: '+name)
        target=directory/'source_snapshots'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    spring_names={s['name'] for s in structure.springs}
    active={s['name'] for s in structure.springs if s['bearing_closed_assumption']}
    seen,history=set(),[]
    converged=False
    for iteration in range(30):
        signature=tuple(sorted(active))
        if signature in seen:
            break
        seen.add(signature)
        job=directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record=frame.record_structure(structure,metadata,active)
        (job/'input.json').write_text(json.dumps(record,indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active,stress=True).replace(
            '*END STEP','*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command=['docker','run','--rm','--network=none','--cpus=1','--memory=4g',
            '--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1',
            '-v',f'{job.resolve()}:/output','-w','/output',panel_kernel.IMAGE,
            'timeout','240s','ccx','-i','frame']
        native=subprocess.run(command,capture_output=True,text=True,timeout=260,check=False)
        log=native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native reinforced-frame solve failed; inspect '+str(job/'frame.log'))
        report=assess(record,(job/'frame.dat').read_text(),(job/'frame.frd').read_text(),(job/'frame.12d').read_text())
        (job/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        history.append({'directory':job.name,'active_count':len(active),
                        'contact_passed':report['closed_bearing_assumption_passed']})
        print(json.dumps({'cycle':iteration,'equilibrium':report['global_equilibrium_passed'],
              'contacts':report['closed_bearing_assumption_passed'],
              'panel_displacement_mm':report['maximum_panel_displacement_mm']}),flush=True)
        if report['closed_bearing_assumption_passed']:
            converged=True
            break
        normal=frame.next_bearing_set(report['bearings'])
        active=active_with_friction(normal,spring_names,metadata['connection_ownership'])
    report.update(candidate=module.KEY,parameters=parameters,source_sha256=before,
        contact_cycles=history,contact_active_set_converged=converged,
        final_cycle_directory=history[-1]['directory'],solver_image=panel_kernel.IMAGE,
        assumptions=__doc__,qualified_for_design=False)
    report['artifact_sha256']={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hold',default='F10')
    parser.add_argument('--stiffness',type=float,default=1000.)
    parser.add_argument('--pounds',type=float,default=250.)
    parser.add_argument('--frame-size',type=float,default=200.)
    parser.add_argument('--panel-size',type=float,default=200.)
    args=parser.parse_args()
    result=run(args.output,hold=args.hold,stiffness=args.stiffness,pounds=args.pounds,
               frame_size=args.frame_size,panel_size=args.panel_size)
    print(json.dumps({k:result[k] for k in ('contact_active_set_converged',
         'global_equilibrium_passed','maximum_panel_displacement_mm')}))
