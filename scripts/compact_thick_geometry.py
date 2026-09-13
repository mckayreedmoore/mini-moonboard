"""Actual compact-frame receivers, machining inventory and base bearing geometry."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_thick_frame as model
from mini_moonboard.connection_geometry import material_intervals
from scripts.leg_mvp_geometry import local_bounds, square_box
from scripts.thick_leg_geometry import edge_rays


def cutters(model=model):
    result = []
    for c in model.connections():
        diameter = c.diameter+1.5875 if c.kind == 'bolt' else c.diameter
        shape = cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction)
        for index, name in enumerate(c.members):
            result.append((name, c.name, 'mechanical_bore', shape))
            if index == 0 and c.kind == 'screw':
                result.append((name, c.name, 'screw_head_recess', c.components()[1]))
    result.extend((member, name, 'service_passage', shape)
                  for member, name, shape in model.service_cutters())
    return result


def build(model=model):
    raw = {p.name:p for p in model.uncut_wood_parts()}
    drilled = {p.name:p for p in model.parts() if p.name in raw}
    machining = cutters(model)
    bolts = [c for c in model.connections() if c.kind == 'bolt']
    groups = {c.name for c in bolts}
    members = {}
    for name in sorted({n for c in bolts for n in c.members}):
        part = raw[name]
        grain = (getattr(model, 'MEMBER_AXES', {}).get(name) or
                 ((cq.Vector(0.,0.,1.), None) if name.startswith('base_post_') else
                  (model.axes()[2 if name.startswith('lumber_leg_') else 4], None)))[0]
        normal = cq.Vector(0., grain.z, -grain.y)
        vertices = [v.Center() for v in part.shape.Vertices()]
        gs, qs = [v.dot(grain) for v in vertices], [v.dot(normal) for v in vertices]
        bb = part.shape.BoundingBox()
        centre = grain*((min(gs)+max(gs))/2)+normal*((min(qs)+max(qs))/2)+cq.Vector((bb.xmin+bb.xmax)/2,0,0)
        profile = [[(v-centre).dot(grain),(v-centre).dot(normal)] for v in vertices]
        ends = [max(s for s,q in profile if s < 0), min(s for s,q in profile if s > 0)]
        records, boxes = [], []
        unrepresented = part.shape.cut(drilled[name].shape)
        for member, source, kind, cutter in machining:
            if member != name:
                continue
            unrepresented = unrepresented.cut(cutter)
            actual = part.shape.intersect(cutter)
            if actual.Volume() <= 1.e-6 or source in groups:
                continue
            bounds = local_bounds(actual, centre, grain, normal)
            boxes.append(square_box(bounds, model.DEPTH))
            cut_bb = actual.BoundingBox()
            records.append({'source':source,'kind':kind,'actual_removed_volume_mm3':actual.Volume(),
                'section_box_sxq_mm':[bounds[0],bounds[1],cut_bb.xmin-centre.x,cut_bb.xmax-centre.x,bounds[2],bounds[3]]})
        residual = unrepresented.Volume()
        if residual > .01:
            raise ValueError('Unrepresented machining in '+name)
        members[name] = {'grain':grain.toTuple(),'centre_mm':centre.toTuple(),
            'end_stations_mm':ends,'depth_mm':max(qs)-min(qs),'width_mm':bb.xlen,
            'profile_sq_mm':profile,'additional_section_boxes':boxes,'opening_records':records,
            'all_openings_represented':True,'unrepresented_removed_volume_mm3':residual,
            'specific_gravity':.5,'parallel_bearing_psi':5600.}
    geometries, fits = {}, []
    for c in bolts:
        point = model.bolt_interface_point(c)
        geometry = {}
        for index,name in enumerate(c.members):
            receiver = raw[name].shape
            for member, source, _, cutter in machining:
                if member == name and source != c.name:
                    receiver = receiver.cut(cutter)
            intervals = material_intervals(receiver,c.start,c.direction,0.,c.length)
            length = sum(hi-lo for lo,hi in intervals)
            nominal, adjusted = edge_rays(raw[name],point,cq.Vector(*members[name]['grain']))
            hole_diameter = c.diameter+1.5875
            hole = cq.Solid.makeCylinder(hole_diameter/2,c.length,c.start,c.direction)
            supported = receiver.intersect(hole).Volume()
            expected = math.pi*(hole_diameter/2)**2*length
            remaining = drilled[name].shape.intersect(hole).Volume()
            washer = c.components()[1 if index == 0 else 2]
            washer = washer.translate(c.direction*(1 if index == 0 else -1)*washer.BoundingBox().xlen)
            unsupported = max(0.,washer.Volume()-washer.intersect(drilled[name].shape).Volume())
            fit = abs(length-members[name]['width_mm'])<1.e-5 and abs(supported-expected)<.01 and remaining<.01 and unsupported<.01
            fits.append({'bolt':c.name,'member':name,'axis_material_intervals_mm':intervals,
                'bearing_length_mm':length,'unsupported_washer_mm3':unsupported,
                'hole_support_error_mm3':supported-expected,'remaining_wood_mm3':remaining,'passes':fit})
            geometry[name] = {**members[name],'bearing_length_mm':length,'edge_distances_mm':adjusted,
                'nominal_edge_distances_mm':nominal,'axis_material_intervals_mm':intervals}
        geometries[c.name] = {'diameter_mm':c.diameter,'bending_yield_psi':45000.,'members':geometry}
    header = raw['base_header'].shape.BoundingBox()
    bearing = {}
    for name,part in raw.items():
        if not name.startswith(('base_side_','base_principal_')):
            continue
        points = [v.Center() for v in part.shape.Vertices() if abs(v.Z-header.zmax)<1.e-5]
        if len(points)!=4:
            raise ValueError('Require rectangular level bearing face: '+name)
        x0,x1,y0,y1 = min(p.x for p in points),max(p.x for p in points),min(p.y for p in points),max(p.y for p in points)
        dx,dy = max(0.,min(x1,header.xmax)-max(x0,header.xmin)),max(0.,min(y1,header.ymax)-max(y0,header.ymin))
        bearing[name] = {'overlap_xy_mm':[dx,dy],'area_mm2':dx*dy,
            'full_member_face_area_mm2':(x1-x0)*(y1-y0),'rear_overhang_mm':max(0.,header.ymin-y0)}
    paths = [Path(__file__),Path(model.__file__)]
    return {'candidate':model.KEY,'geometries_by_bolt_name':geometries,'members':members,
        'receiver_fit':fits,'receiver_fit_pass':all(r['passes'] for r in fits),
        'header_overlap':bearing,'header_depth_mm':header.ylen,
        'placement_assumptions':{'drill_position_radius_mm':1.,'inward_cut_normal_mm':2.},
        'source_sha256':{str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope':'Actual receivers, complete opening inventory and partial base contact; resistance assessed separately.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print({k:result[k] for k in ('candidate','receiver_fit_pass','header_depth_mm')})


if __name__ == '__main__':
    main()
