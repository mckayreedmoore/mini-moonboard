"""Current shoe-free whole-frame response model.

Gross timber sections, independent orthotropic equivalent panel layers, rigid
commercial angle bodies, explicit finite connector stiffness and unilateral
normal contacts represent an engineering response idealization. Local bores,
notches, bracket flexure and fastener yielding require separate resistance
checks. No-slip foot resultants act only while the corresponding foot bears.
Material and spring properties are mandatory inputs, not inferred capacities.
"""
import cadquery as cq
import numpy as np

from fea import round_insert_frame as shared
from fea.horizontal_panel_frame import (
    Structure,
    add_load,
    contained_patch,
    distribute_wrench,
    panel_kernel,
    traction_wrench,
)
from fea.reinforced_frame_demand import floor_attachment
from fea.round_structural_frame import SeatingModule


class CurrentModule:
    """Supply explicit shifted-current APIs without mutating historical modules."""
    def __init__(self, module):
        self.module = module
        self.hardware = getattr(module, "hardware", None) or module.previous.hardware
        self.timber = getattr(module, "timber", None) or module.previous.timber
        self.leg = module.leg_source

    def __getattr__(self, name):
        return getattr(self.module, name)

    def wood_parts(self):
        return tuple(p for p in self.module.parts()
                     if p.name.startswith(('base_', 'lumber_leg_', 'main_', 'kicker_')))


def directional_connector(structure, first, second, properties, name, owner):
    """Project motion into axial and two transverse components at one point."""
    axis=np.array(owner['axis'],dtype=float);axis/=np.linalg.norm(axis)
    seed=np.eye(3)[int(np.argmin(abs(axis)))]
    tangent=np.cross(axis,seed);tangent/=np.linalg.norm(tangent)
    basis=np.array([axis,tangent,np.cross(axis,tangent)])
    auxiliary=[structure.node(structure.nodes[first]),structure.node(structure.nodes[second])]
    for node,source in zip(auxiliary,(first,second),strict=True):
        for i,direction in enumerate(basis):
            structure.equations.append([(node,i+1,1.)]+[(source,j+1,-float(value))
                for j,value in enumerate(direction) if abs(value)>1.e-13])
    for i,stiffness in enumerate((properties['axial_n_per_mm'],properties['lateral_n_per_mm'],properties['lateral_n_per_mm'])):
        structure.spring(*auxiliary,stiffness,name,dofs=(i+1,))
    structure.rotation_masters.update(auxiliary)
    owner['force_basis']=basis.tolist()


def mass_by_body(module,raw,materials):
    """Preserve each modeled weight and centroid; hardware follows nearest body.

    This load-placement approximation concerns hardware gravity only. It does
    not allocate climbing forces or join adjacent members. Purchased electrical
    hardware and holds remain in the separate equipment allowance.
    """
    density=materials['density_kg_per_mm3']
    result={name:{'mass_kg':part.shape.Volume()*density,
                  'centre_xyz_mm':np.array(part.shape.Center().toTuple())}
            for name,part in raw.items()}
    boxes={name:part.shape.BoundingBox() for name,part in raw.items()}
    inventory=[]
    def add(name,shape):
        point=np.array(shape.Center().toTuple());mass=shape.Volume()*7.85e-6
        def distance(body):
            bb=boxes[body]
            gap=np.maximum(0.,np.maximum(np.array([bb.xmin,bb.ymin,bb.zmin])-point,
                                         point-np.array([bb.xmax,bb.ymax,bb.zmax])))
            return float(np.linalg.norm(gap))
        body=min(boxes,key=distance)
        row=result[body];new=row['mass_kg']+mass
        row['centre_xyz_mm']=(row['mass_kg']*row['centre_xyz_mm']+mass*point)/new
        row['mass_kg']=new
        inventory.append({'name':name,'body':body,'mass_kg':mass,'centre_xyz_mm':point.tolist()})
    for part in module.parts():
        if part.name not in raw:
            if not part.name.startswith(('clip_','hold_tnut_')):
                raise ValueError('Unclassified hardware mass '+part.name)
            add(part.name,part.shape)
    for connection in module.connections():
        components=tuple(connection.components())
        shape=components[0].fuse(*components[1:]) if len(components)>1 else components[0]
        add('fastener_'+connection.name,shape)
    return result,inventory


def gross_member_record(part, grain, section_u):
    """Preserve full gross section; level bevels use plane-section end offsets."""
    grain, section_u = grain.normalized(), section_u.normalized()
    section_v = grain.cross(section_u).normalized()
    local=cq.Plane(origin=(0,0,0),xDir=section_u,normal=grain).toLocalCoords(part.shape)
    bb=local.BoundingBox()
    centre=section_u*((bb.xmin+bb.xmax)/2)+section_v*((bb.ymin+bb.ymax)/2)
    low,high=bb.zmin,bb.zmax
    world=part.shape.BoundingBox()
    bevel=1.e-8 < abs(grain.z) < 1-1.e-8
    if bevel:
        low=(world.zmin-centre.z)/grain.z
    width,depth=bb.xlen,bb.ylen
    return {'name':part.name,'start':list((centre+grain*low).toTuple()),
        'end':list((centre+grain*high).toTuple()),'axis':list(grain.toTuple()),
        'section_u':list(section_u.toTuple()),'section_v':list(section_v.toTuple()),
        'width_mm':width,'depth_mm':depth,'gross_width_mm':width,'gross_depth_mm':depth,
        'area_mm2':width*depth,'retained_area_fraction':1.,
        'verification_grain_interval_mm':[max(v.Center().dot(grain) for v in part.shape.Vertices() if abs(v.Z-world.zmin)<1.e-6) if bevel else low,high],
        'section_centroid_xyz_mm':list(centre.toTuple()),'qualified_for_design':False}


def level_face_points(shape, bottom):
    """Read actual horizontal bearing-face corner coordinates from current CAD."""
    bounds=shape.BoundingBox()
    level=bounds.zmin if bottom else bounds.zmax
    points=sorted({tuple(v.Center().toTuple()) for v in shape.Vertices() if abs(v.Z-level)<1.e-6})
    if len(points)!=4:
        raise ValueError('Expected four corners on an uncut horizontal bearing face')
    return [np.array(p) for p in points]


def header_bearing_points(corners, header_shape):
    """Clip the rectangular bearing footprint to the gross header top envelope.

    Local holes and crushing are outside this gross-member spring model. This
    prevents a wider rear rim from receiving fictional support beyond the header.
    """
    points = np.asarray(corners, dtype=float)
    bounds = header_shape.BoundingBox()
    if np.max(abs(points[:, 2]-bounds.zmax)) > 1.e-5:
        raise ValueError('Member bearing face must meet the header top')
    low, high = points.min(axis=0), points.max(axis=0)
    expected = {(x, y) for x in (low[0], high[0]) for y in (low[1], high[1])}
    # Coordinate noise can reverse lexicographic order within a nominal edge.
    # Match each Cartesian corner geometrically, retaining original points.
    expected_xy = np.array(sorted(expected))
    matches = np.all(abs(points[:, None, :2]-expected_xy[None, :, :]) <= 1.e-6, axis=2)
    if len(expected) != 4 or not np.all(matches.sum(axis=0) == 1) or not np.all(matches.sum(axis=1) == 1):
        raise ValueError('Header clipping requires axis-aligned rectangular bearing')
    clipped_low = np.maximum(low[:2], [bounds.xmin, bounds.ymin])
    clipped_high = np.minimum(high[:2], [bounds.xmax, bounds.ymax])
    if np.any(clipped_high-clipped_low <= 1.e-6):
        raise ValueError('Member has no positive-area header bearing overlap')
    # Preserve the original node coordinates/order when fully supported.
    if np.all(low[:2] >= np.array([bounds.xmin, bounds.ymin])-1.e-6) and np.all(high[:2] <= np.array([bounds.xmax, bounds.ymax])+1.e-6):
        return list(corners)
    return [np.array([x, y, low[2]]) for x in (clipped_low[0], clipped_high[0])
            for y in (clipped_low[1], clipped_high[1])]


def endpoint_attachment(structure, name, point):
    entry=structure.members[name]
    station=float(np.dot(np.asarray(point)-entry['start'],entry['axis']))
    if station < -1.e-6:
        return floor_attachment(structure,name,point)
    return structure.attachment(name,point)


def foot_samples(corners, grid=None):
    """Return points and stiffness fractions for corner or finite-area contact.

    Interior midpoint cells represent equal tributary areas on the rectangular
    cut foot. Total normal stiffness is preserved, not rotational stiffness.
    """
    corners = np.asarray(corners, dtype=float)
    if corners.shape != (4, 3) or not np.all(np.isfinite(corners)):
        raise ValueError('Require four finite bearing-face corners')
    if grid is None:
        return [(point, .25) for point in corners]
    if isinstance(grid, bool) or not isinstance(grid, int) or grid < 2:
        raise ValueError('Leg floor grid must be an integer at least two')
    centre = corners.mean(axis=0)
    order = np.argsort(np.arctan2(corners[:, 1]-centre[1], corners[:, 0]-centre[0]))
    a, b, c, d = corners[order]
    u, v = b-a, d-a
    if (not np.allclose(a+c, b+d, atol=1.e-6, rtol=0.)
            or abs(float(u@v)) > 1.e-6
            or min(np.linalg.norm(u), np.linalg.norm(v)) < 1.e-6
            or np.ptp(corners[:, 2]) > 1.e-6):
        raise ValueError('Finite-area foot sampling requires a horizontal rectangle')
    return [(a+(i+.5)/grid*u+(j+.5)/grid*v, 1./grid**2)
            for i in range(grid) for j in range(grid)]


def leg_bolt_properties(properties, first, second, scale):
    """Scale only leg-bolt elastic stiffness, without changing resistance."""
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('Leg bolt stiffness scale must be positive and finite')
    if not any(name.startswith('lumber_leg_') for name in (first, second)):
        return properties
    return {key: value*scale if key in ('axial_n_per_mm', 'lateral_n_per_mm') else value
            for key, value in properties.items()}


def add_member_floor(structure,name,ownership,shape,stiffnesses,grid=None):
    points=level_face_points(shape,True)
    for index,(point,fraction) in enumerate(foot_samples(points, grid)):
        wood=floor_attachment(structure,name,point)
        add_floor(structure,'floor_'+name+'_'+str(index),wood,point,ownership,name,4.*fraction*stiffnesses['floor'])
        ownership['floor_'+name+'_'+str(index)]['normal_stiffness_fraction'] = fraction
    point=np.mean(points,axis=0)
    wood=floor_attachment(structure,name,point)
    ground=structure.node(point);structure.fixed.add(ground)
    spring='floor_'+name+'_friction'
    structure.spring(wood,ground,stiffnesses['floor'],spring,dofs=(1,2),bearing=True)
    ownership[spring]={'first':name,'second':'floor','point':point.tolist()}


def add_floor(structure,name,wood,point,ownership,body,stiffness):
    ground=structure.node(point);structure.fixed.add(ground)
    shared.normal_contact(structure,name,wood,[ground],[1.],point,[0.,0.,1.],stiffness)
    ownership[name]={'first':body,'second':'floor','point':list(point),
                     'scalar_normal':[0.,0.,1.],'ground_node':ground}


def add_panel_floor(structure,name,ownership,stiffness):
    for index,node in enumerate(structure.panels[name]['nodes']):
        if abs(structure.nodes[node][2])<1.e-6:
            add_floor(structure,'floor_'+name+'_'+str(index),node,structure.nodes[node],ownership,name,stiffness)


class CurrentStructure(Structure):
    """Native CalculiX orthotropic materials with an explicit grain orientation."""
    def __init__(self, materials):
        super().__init__()
        self.materials=materials

    def layered_panels(self):
        """Replace temporary S8 meshing topology with four bonded solid layers.

        Splitting the symmetric equivalent core creates a physical midsurface
        interface. Existing panel nodes remain native C3D20 face nodes, so
        contact, screw and load attachments require no shell-output correction.
        """
        if getattr(self,'panel_solid_layers',False):
            return
        outer,core,last=self.materials['panel_layers']
        layers=[outer,{**core,'thickness_mm':core['thickness_mm']/2},
                {**core,'thickness_mm':core['thickness_mm']/2},last]
        total=sum(row['thickness_mm'] for row in layers)
        if abs(total-panel_kernel.THICKNESS)>1.e-8:
            raise ValueError('Equivalent layers must match current panel thickness')
        self.layer_materials=layers
        self.panel_layer_groups={}
        for name,panel in self.panels.items():
            original=[(eid,self.elements[eid][1]) for eid in self.groups.pop(name)]
            normal=np.array(panel['normal']);normal/=np.linalg.norm(normal)
            # S8 grid face order determines positive thickness direction.
            face=original[0][1]
            actual=np.cross(np.array(self.nodes[face[1]])-self.nodes[face[0]],
                            np.array(self.nodes[face[3]])-self.nodes[face[0]])
            if np.dot(normal,actual)<0:normal=-normal
            offsets=[-total/2]
            for row in layers:offsets.append(offsets[-1]+row['thickness_mm'])
            if abs(offsets[2])>1.e-8:raise ValueError('Require symmetric panel layers')
            grids=[]
            for offset in offsets:
                grids.append({n:n if abs(offset)<1.e-8 else self.node(np.array(self.nodes[n])+normal*offset)
                              for n in panel['nodes']})
            self.panel_layer_groups[name]=[]
            for layer in range(4):
                group=f'{name}_layer_{layer}'
                self.panel_layer_groups[name].append(group)
                middle_nodes={}
                for eid,ids in original:
                    lower=[grids[layer][n] for n in ids]
                    upper=[grids[layer+1][n] for n in ids]
                    offset=(offsets[layer]+offsets[layer+1])/2
                    for n in ids[:4]:
                        if n not in middle_nodes:
                            middle_nodes[n]=self.node(np.array(self.nodes[n])+normal*offset)
                    middle=[middle_nodes[n] for n in ids[:4]]
                    topology=lower[:4]+upper[:4]+lower[4:]+upper[4:]+middle
                    if layer==0:
                        self.elements[eid]=('C3D20',topology,group)
                        self.groups.setdefault(group,[]).append(eid)
                    else:self.element('C3D20',topology,group)
        self.panel_solid_layers=True

    def deck(self, modulus=None, poisson=None, active_bearings=None, stress=False):
        text=super().deck(active_bearings=active_bearings,stress=stress)
        materials=[]
        for name in ('timber','panel'):
            constants=self.materials[name]
            if len(constants)!=9 or not all(np.isfinite(constants)):
                raise ValueError('Require nine finite engineering elastic constants')
            materials += [f'*MATERIAL,NAME={name.upper()}', '*ELASTIC,TYPE=ENGINEERING CONSTANTS',
                          ','.join(map(str,constants[:8])),str(constants[8])]
        if getattr(self,'panel_solid_layers',False):
            for index,layer in enumerate(self.layer_materials):
                constants=layer['constants']
                materials += [f'*MATERIAL,NAME=PANEL_LAYER_{index}','*ELASTIC,TYPE=ENGINEERING CONSTANTS',
                              ','.join(map(str,constants[:8])),str(constants[8])]
        text=text.replace('*MATERIAL,NAME=ASSUMED_WOOD\n*ELASTIC\n7000.0,0.3','\n'.join(materials))
        for name,member in self.members.items():
            axes=[*member['axis'],*member['u']]
            old=f'*SOLID SECTION,ELSET={name},MATERIAL=ASSUMED_WOOD'
            new=f'*ORIENTATION,NAME=ORI_{name}\n'+','.join(map(str,axes))+f'\n*SOLID SECTION,ELSET={name},MATERIAL=TIMBER,ORIENTATION=ORI_{name}'
            text=text.replace(old,new)
        # Panel local first direction follows sheet width; second follows slope/vertical.
        for name in self.panels:
            normal=np.array(self.panels[name]['normal'])
            second=np.cross(normal,[1.,0.,0.])
            old=f'*SHELL SECTION,ELSET={name},MATERIAL=ASSUMED_WOOD'
            new=f'*ORIENTATION,NAME=ORI_{name}\n'+','.join(map(str,[1.,0.,0.,*second]))+f'\n*SHELL SECTION,ELSET={name},MATERIAL=PANEL,ORIENTATION=ORI_{name}'
            if getattr(self,'panel_solid_layers',False):
                old += '\n'+str(panel_kernel.THICKNESS)
                new=f'*ORIENTATION,NAME=ORI_{name}\n'+','.join(map(str,[1.,0.,0.,*second]))
                for index,group in enumerate(self.panel_layer_groups[name]):
                    new+=f'\n*SOLID SECTION,ELSET={group},MATERIAL=PANEL_LAYER_{index},ORIENTATION=ORI_{name}'
            text=text.replace(old,new)
        return text


def prepare(module, *, materials, stiffnesses, hold='F10', pounds=150.,
            horizontal_force=(0., 300.), dynamic_factor=2., equipment_kg=25.,
            frame_size=150., panel_size=120., patch_size=40.,
            leg_bolt_scale=1., leg_floor_grid=None, expected_candidate='no-shoes-development'):
    """Build the current independent-panel, gross-member contact diagnostic."""
    mode = 'coupled'
    load_kind = 'full'
    module = CurrentModule(module)
    from fea.horizontal_frame_members import axes
    from mini_moonboard import panel_grid_v2
    if module.KEY != expected_candidate or mode != 'coupled':
        raise ValueError('Require current shoe-free candidate with independent coupled panels')
    if len(module.panel_connections()) != 66:
        raise ValueError('Require all 66 current panel/kicker attachments')
    if pounds <= 0 or equipment_kg < 0 or dynamic_factor <= 0:
        raise ValueError('Positive climber load and nonnegative equipment mass required')
    leg_bolt_properties({}, 'lumber_leg_validation', '', leg_bolt_scale)
    foot_samples([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]], leg_floor_grid)
    raw={p.name:p for p in module.wood_parts()}
    body_mass,hardware_mass=mass_by_body(module,raw,materials)
    records = [gross_member_record(p, *axes(module, p.name)) for p in module.uncut_wood_parts()
               if not p.name.startswith(('main_', 'kicker_'))]
    by_name={r['name']:r for r in records}
    connections=module.connections()
    planned={name:[] for name in by_name}
    angles={};bolts=[];panel_points={};bearings=[];gravity_points={}
    ownership = {}
    for c in connections:
        if c.name.startswith('clip_'):
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
            interface = getattr(module, 'bolt_interface_point', None)
            point=np.asarray((interface(c) if interface is not None else c.start+c.direction*(2.032+38.1)).toTuple())
            bolts.append((c.name,*c.members,point))
            for name in c.members:planned[name].append(point)
            ownership[c.name] = {'first': c.members[0], 'second': c.members[1], 'point': point.tolist(), 'axis': list(c.direction.toTuple())}
        else:raise ValueError('Unrepresented current mechanical connection')
    for r in records:
        name=r['name'];centre=body_mass[name]['centre_xyz_mm']
        gravity_points[name]=centre;planned[name].append(centre)
        if name.startswith(('base_principal_', 'base_side_')):
            points=header_bearing_points(level_face_points(raw[name].shape, bottom=True), raw['base_header'].shape)
            for point in points:
                bearings.append((name,'base_header',point))
                planned[name].append(point);planned['base_header'].append(point)
        elif name.startswith('base_post_'):
            points=level_face_points(raw[name].shape, bottom=False)
            for point in points:
                bearings.append(('base_header',name,point))
                planned[name].append(point);planned['base_header'].append(point)
    structure=CurrentStructure(materials)
    for r in records:structure.member(r,planned[r['name']],frame_size)
    for name,entries in angles.items():
        if len(entries) != 6:
            raise ValueError('Require six screws per commercial ML angle')
        steel=structure.rigid_angle(name,[p for _,_,p in entries])
        for (screw,member,point),tag in zip(entries,steel,strict=True):
            wood=structure.attachment(member,point)
            directional_connector(structure,wood,tag,stiffnesses['sds'],screw,ownership[screw])
    for name,first,second,point in bolts:
        directional_connector(structure,structure.attachment(first,point),structure.attachment(second,point),leg_bolt_properties(stiffnesses['bolt'],first,second,leg_bolt_scale),name,ownership[name])
    for index,(first,second,point) in enumerate(bearings):
        name = 'bearing_'+first+'_'+second+'_'+str(index)
        structure.spring(endpoint_attachment(structure,first,point),endpoint_attachment(structure,second,point),stiffnesses['bearing'],
                         name,dofs=(3,),bearing=True)
        ownership[name] = {'first': first, 'second': second, 'point': point.tolist()}
    for r in records:
        if r['name'].startswith(('base_post_','lumber_leg_')):
            add_member_floor(structure, r['name'], ownership, raw[r['name']].shape, stiffnesses,
                             grid=leg_floor_grid if r['name'].startswith('lumber_leg_') else None)
        tag=structure.attachment(r['name'],gravity_points[r['name']])
        add_load(structure,tag,[0,0,-body_mass[r['name']]['mass_kg']*9.80665])
    # Panel attachment points exist even in the frame-only reference so applied
    # framing forces are identical without constructing a virtual diaphragm.
    receiver_tags={}
    for name,points in panel_points.items():
        receiver_tags[name]=[(screw,structure.attachment(receiver,point),point) for screw,receiver,point in points]
    hx,hs=panel_grid_v2.main_tnut_datums()[hold];hx-=module.b.HALF
    loaded_name=f"main_{'lower' if hs<module.b.HALF else 'upper'}_{'left' if hx<0 else 'right'}"
    outward=-np.asarray(module.b.normal().toTuple());along=np.asarray((module.b.point(0,1,0)-module.b.point(0,0,0)).toTuple())
    target=np.asarray(module.b.point(hx,hs,-panel_kernel.THICKNESS/2).toTuple())
    force=np.array([*horizontal_force,-dynamic_factor*pounds*.45359237*9.80665])
    if load_kind=='normal':force=np.dot(force,outward)*outward
    moment=np.cross(outward*(100.+panel_kernel.THICKNESS/2),force)
    loaded_left=-module.b.HALF if hx<0 else 0.
    loaded_low=0. if hs<module.b.HALF else module.b.HALF
    patch=contained_patch(hx,hs,patch_size,(loaded_left,loaded_left+module.b.HALF,loaded_low,loaded_low+module.b.HALF))
    panel_loads={}
    for name in raw:
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
            structure.panels[name]={'nodes':list(tags.values()), 'normal':list(module.b.normal().toTuple()) if main else [0.,1.,0.]}
            for (screw,wood,_),(x,y) in zip(receiver_tags[name],coords,strict=True):
                node=tags[lookup[round(x,8),round(y,8)]]
                directional_connector(structure,wood,node,stiffnesses['panel'],screw,ownership[screw])
        panel_mass=body_mass[name]['mass_kg'];cg=body_mass[name]['centre_xyz_mm']
        if name.startswith('main_upper_') and equipment_kg:
            equipment_point=np.array(module.b.point(0.,max(p[1] for p in panel_grid_v2.main_tnut_datums().values()),-panel_kernel.THICKNESS).toTuple())
            share=equipment_kg/2
            cg=(panel_mass*cg+share*equipment_point)/(panel_mass+share)
            panel_mass+=share
        weight=np.array([0.,0.,-panel_mass*9.80665])
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
            panel_loads={'nodes':loadtags,'forces_xyz_n':values.tolist(), 'area_weights':list(patch_weights.values())}
    contacts = shared.seating_contacts(structure, SeatingModule(module), samples=2, penalty=stiffnesses['seating_per_area'])
    for c in contacts:
        ownership[c['name']] = {'first': c['member'], 'second': c['panel'], 'point': c['point_xyz_mm'], 'scalar_normal': c['inward_xyz']}
    metadata={'candidate':module.KEY,'leg_bolt_scale':leg_bolt_scale,
              'leg_floor_grid':leg_floor_grid,
              'header_bearing_assumption':'Normal springs at corners of actual rectangular overlap with gross header top; local holes and crushing require separate checks',
              'leg_floor_pressure_assumption':('Four corner normal springs' if leg_floor_grid is None else f'{leg_floor_grid}x{leg_floor_grid} midpoint tributary-area normal springs; unchanged total stiffness'),
              'leg_joint_assumption':'Finite elastic bolt springs; leg stiffness scaled independently; no installed hinge or resistance qualification','mode':mode,'hold':hold,'pounds':pounds,'load_kind':load_kind,
              'force_xyz_n':force.tolist(),'moment_at_panel_midplane_nmm':moment.tolist(),
              'target_xyz_mm':target.tolist(),'standoff_from_front_mm':100.,'stiffnesses':stiffnesses,'materials':materials,'equipment_kg':equipment_kg,
              'frame_size_mm':frame_size,'panel_size_mm':panel_size,'members':records,'panel_load':panel_loads,
              
              'panel_patch_size_mm':patch_size,'panel_patch_mm':list(patch),'panel_patch_load_type':'Consistent uniform vector traction plus zero-resultant nodal couple; not a physical hold-seat traction solution',
              'qualified_for_design':False,'actual_joint_demands_qualified':False,
              'connection_ownership': ownership,
              'gravity_points': {name: {'point': point.tolist(), 'force': [0.,0.,-body_mass[name]['mass_kg']*9.80665]} for name,point in gravity_points.items()},
              'limits':__doc__}
    metadata['hardware_mass_inventory'] = hardware_mass
    metadata['modeled_mass_kg'] = sum(row['mass_kg'] for row in body_mass.values())
    metadata['angle_stations'] = [{'name':name,'origin':list(origin.toTuple()),'u':list(u.toTuple()),'v':list(v.toTuple()),'members':[beam,upright]} for name,origin,u,v,beam,upright in module.stations()]
    metadata['seating_contacts'] = contacts
    metadata['limits'] = __doc__
    structure.layered_panels()
    metadata['panel_formulation']='Four bonded C3D20 equivalent layers; exact directional reference EA/EI, physical midsurface nodes'
    return structure,metadata

