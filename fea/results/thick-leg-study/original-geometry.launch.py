"""Actual CAD geometry and explicit provisional hardware for the 4x6 pivot trial."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard import thick_leg_frame as model


def edge_rays(part, point, grain):
    normal = cq.Vector(0., grain.z, -grain.y)
    polygon = np.array([[(v.Center()-point).dot(grain), (v.Center()-point).dot(normal)] for v in part.shape.Vertices()])
    hull = ConvexHull(polygon)
    nominal, adjusted = {}, {}
    for key, ray in (('grain_positive',(1,0)), ('grain_negative',(-1,0)), ('depth_positive',(0,1)), ('depth_negative',(0,-1))):
        rate = hull.equations[:, :2]@np.array(ray)
        active = rate > 1e-9
        nominal[key] = float(np.min(-hull.equations[active, 2]/rate[active]))
        adjusted[key] = float(np.min((-hull.equations[active, 2]-3.)/rate[active]))
    return nominal, adjusted


def receiver_without_target(part, target):
    """Retain every other machined opening when measuring bearing intervals."""
    shape = part.shape
    for c in model.connections():
        if c.name == target.name or part.name not in c.members:
            continue
        diameter = 11.1125 if c.kind == 'bolt' else c.diameter
        shape = shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2, c.start-c.direction, c.direction))
        if c.members.index(part.name) == 0 and c.kind == 'screw':
            shape = shape.cut(c.components()[1])
    source = model.previous.previous
    for record in source.bore_records():
        if record['member'] == part.name:
            shape = shape.cut(source.wiring.bore_shape(record).translate(model.previous.SHIFT))
    return shape


def provisional_hardware():
    psi = .006894757293168361
    washer = {'outer_diameter_mm':model.WASHER_OD_MM, 'hole_diameter_mm':model.HOLE_DIAMETER,
              'seat_diameter_mm':.95*1.104*25.4, 'thickness_mm':model.WASHER_THICKNESS_MM,
              'wood_bearing_mpa':625*psi, 'yield_mpa':33000*psi, 'safety_factor':1.67}
    return {'tensile_area_mm2':.334*25.4**2, 'shear_area_mm2':math.pi*(.620*25.4)**2/4,
            'steel_yield_mpa':92000*psi, 'steel_safety_factor':2., 'washers':[dict(washer), dict(washer)],
            'provisional_assumptions_only':True, 'catalog_or_receipt_verified':False,
            'basis':'Assumed 3/4 UNC Grade 5 stress areas and 92 ksi yield; washer 33 ksi yield floor and uniform annular pressure. Actual delivery, head seat and thread/runout dimensions remain unverified.'}


def build():
    raw = {p.name:p for p in model.raw_changed_parts()}
    drilled = {p.name:p for p in model.parts() if p.name in raw}
    geometries, witnesses = {}, []
    for c in model.connections():
        if not isinstance(c, model.ProvisionalPivotBolt):
            continue
        members = {}
        point = model.bolt_interface_point(c)
        for index, name in enumerate(c.members):
            grain = model.axes()[2 if name.startswith('lumber_leg_') else 4]
            nominal, adjusted = edge_rays(raw[name], point, grain)
            receiver = receiver_without_target(raw[name], c)
            probe = cq.Solid.makeCylinder(.05, c.length, c.start, c.direction)
            pieces = receiver.intersect(probe).Solids()
            intervals = sorted([sorted((v.Center()-c.start).dot(c.direction) for v in piece.Vertices()) for piece in pieces])
            intervals = [[values[0], values[-1]] for values in intervals]
            length = sum(high-low for low, high in intervals)
            if not intervals or length <= 0:
                raise ValueError('No actual bearing material at '+c.name+' / '+name)
            hole = cq.Solid.makeCylinder(model.HOLE_DIAMETER/2, c.length, c.start, c.direction)
            contained = receiver.intersect(hole).Volume()
            expected = math.pi*(model.HOLE_DIAMETER/2)**2*length
            remaining = drilled[name].shape.intersect(hole).Volume()
            washer = c.components()[1 if index == 0 else 2].translate(c.direction*(1 if index == 0 else -1)*model.WASHER_THICKNESS_MM)
            unsupported = max(0., washer.Volume()-washer.intersect(drilled[name].shape).Volume())
            fit = abs(contained-expected) < .01 and remaining < .01 and unsupported < .01
            witnesses.append({'bolt':c.name, 'member':name, 'axis_material_intervals_mm':intervals,
                'full_hole_supported_volume_mm3':contained, 'expected_mm3':expected,
                'wood_remaining_in_drilled_hole_mm3':remaining, 'unsupported_washer_mm3':unsupported, 'passes':fit})
            members[name] = {'grain':grain.toTuple(), 'bearing_length_mm':length,
                'specific_gravity':.5, 'parallel_bearing_psi':5600., 'edge_distances_mm':adjusted,
                'nominal_edge_distances_mm':nominal, 'axis_material_intervals_mm':intervals}
        geometries[c.name] = {'diameter_mm':c.diameter, 'bending_yield_psi':45000., 'members':members}
    header = raw['base_header'].shape.BoundingBox()
    overlap = {}
    for name in ('base_side_left', 'base_side_right'):
        points = [v.Center() for v in raw[name].shape.Vertices() if abs(v.Z-header.zmax) < 1e-6]
        if len(points) != 4:
            raise ValueError('Require level four-corner rim bearing face')
        x0,x1,y0,y1 = min(p.x for p in points),max(p.x for p in points),min(p.y for p in points),max(p.y for p in points)
        dx,dy = max(0.,min(x1,header.xmax)-max(x0,header.xmin)),max(0.,min(y1,header.ymax)-max(y0,header.ymin))
        overlap[name] = {'actual_overlap_xy_mm':[dx,dy], 'area_mm2':dx*dy,
                         'full_rim_face_area_mm2':(x1-x0)*(y1-y0), 'header_end_extension_mm':model.OUTWARD_EXTENSION_MM,
                         'header_cantilever_qualified':False}
    paths = ['mini_moonboard/thick_leg_frame.py', 'mini_moonboard/no_shoes_frame.py', 'scripts/thick_leg_geometry.py']
    return {'candidate':model.KEY, 'geometries_by_bolt_name':geometries, 'hardware':provisional_hardware(),
            'receiver_fit':witnesses, 'receiver_fit_pass':all(r['passes'] for r in witnesses),
            'header_overlap':overlap, 'stack':model.provisional_stack(),
            'placement_assumptions':{'drill_position_radius_mm':1., 'inward_cut_normal_mm':2.},
            'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},
            'scope':'Actual material intervals, receiver/washer support and header overlap; no full-assembly collision, local opening, cantilever or free-pivot qualification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'candidate':result['candidate'], 'receiver_fit_pass':result['receiver_fit_pass']}))


if __name__ == '__main__':
    main()
