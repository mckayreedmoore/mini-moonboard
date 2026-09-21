"""Generate actual-CAD geometry inputs for the isolated leg MVP checks.

Run only when heavy CAD work is serialized. Net-section boxes deliberately
replace each opening with a full-thickness square removal; this does not check
local stress concentration, splitting at service holes, or opening shear.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard import leg_mvp_frame as model


def local_bounds(shape, centre, grain, normal):
    """Rotate exact CAD into member coordinates before bounding curved cuts."""
    axes = (grain, normal, cq.Vector(-1, 0, 0))
    matrix = cq.Matrix([list(axis.toTuple())+[-centre.dot(axis)] for axis in axes]+[[0, 0, 0, 1]])
    bounds = shape.transformGeometry(matrix).BoundingBox()
    return [bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax]


def square_box(bounds, depth):
    """Contain the complete removal bound while staying inside stock depth."""
    slo, shi, qlo, qhi = bounds
    # Boolean-kernel bounding tolerance may extend a boundary by submicrons.
    tolerance = 1e-5
    if qlo < -depth/2-tolerance or qhi > depth/2+tolerance:
        raise ValueError('Removal exceeds actual stock depth')
    qlo, qhi = max(qlo, -depth/2), min(qhi, depth/2)
    size = max(shi-slo, qhi-qlo)
    if size > depth+tolerance:
        raise ValueError('Opening cannot be represented by a contained square')
    size = min(size, depth)
    s = (slo+shi)/2
    q = min(depth/2-size/2, max(-depth/2+size/2, (qlo+qhi)/2))
    if not (s-size/2 <= slo+tolerance and s+size/2 >= shi-tolerance
            and q-size/2 <= qlo+tolerance and q+size/2 >= qhi-tolerance):
        raise ValueError('Square removal does not contain the actual cut')
    return [s, q, size]


def placement(member, bolt_points):
    """Conservative 4D both-edge / 7D both-end screen, including tolerances.

    Drill axes may move 1 mm in any in-plane direction. Every cut boundary may
    move inward 2 mm normal to itself. These are assessment assumptions, not
    released shop tolerances. Ray distances use the actual stock polygon.
    """
    centre = cq.Vector(*member['centre_mm'])
    grain = cq.Vector(*member['grain'])
    normal = cq.Vector(0, grain.z, -grain.y)
    hull = ConvexHull(np.array(member['profile_sq_mm']))
    rows = []
    points = []
    for name, point in bolt_points:
        offset = point-centre
        xy = np.array([offset.dot(grain), offset.dot(normal)])
        points.append(xy)
        distances, adjusted = {}, {}
        for label, direction in (('grain_positive', (1., 0.)), ('grain_negative', (-1., 0.)),
                                  ('depth_positive', (0., 1.)), ('depth_negative', (0., -1.))):
            rates = hull.equations[:, :2]@np.array(direction)
            active = rates > 1e-9
            clearances = -(hull.equations[:, :2]@xy+hull.equations[:, 2])
            # SciPy hull boundary normals have unit magnitude.
            distances[label] = float(np.min(clearances[active]/rates[active]))
            adjusted[label] = float(np.min((clearances[active]-3.)/rates[active]))
        margins = {label:value-(7 if label.startswith('grain') else 4)*model.catalog.BOLT_DIAMETER
                   for label, value in adjusted.items()}
        rows.append({'bolt':name, 'axis_sq_mm':xy.tolist(), 'nominal_ray_distances_mm':distances,
                     'tolerance_adjusted_ray_distances_mm':adjusted, 'conservative_margins_mm':margins})
    minimum_spacing = min(float(np.linalg.norm(a-b)) for a,b in itertools.combinations(points, 2))
    spread = max(p[1] for p in points)-min(p[1] for p in points)
    return {'rows':rows, 'minimum_adjusted_edge_end_margin_mm':min(v for row in rows for v in row['conservative_margins_mm'].values()),
            'minimum_euclidean_axis_spacing_mm':minimum_spacing,
            'adjusted_euclidean_4D_spacing_margin_mm':minimum_spacing-2.-4*model.catalog.BOLT_DIAMETER,
            'adjusted_127mm_cross_grain_spread_margin_mm':127.-spread-2.,
            'scope':'Both-edge 4D and both-end 7D conservative geometry screen; Euclidean spacing is not a substitute for directional NDS row rules.'}


def build(model=model):
    raw = {p.name:p for p in model.raw_changed_parts()}
    drilled = {p.name:p for p in model.parts() if p.name in raw}
    connections = model.connections()
    leg_bolts = [c for c in connections if isinstance(c, model.LegMvpBolt)]
    members = {}
    for name, part in raw.items():
        grain = model.axes()[2 if name.startswith('lumber_leg_') else 4]
        normal = cq.Vector(0, grain.z, -grain.y)
        vertices = [v.Center() for v in part.shape.Vertices()]
        bounds = local_bounds(part.shape, cq.Vector(), grain, normal)
        slo, shi, qlo, qhi = bounds
        xmid = (part.shape.BoundingBox().xmin+part.shape.BoundingBox().xmax)/2
        centre = grain*((slo+shi)/2)+normal*((qlo+qhi)/2)+cq.Vector(xmid, 0, 0)
        profile = [[(v-centre).dot(grain), (v-centre).dot(normal)] for v in vertices]
        # Level feet are oblique to grain. Use the shorter full-depth interval
        # rather than pretending the most distant foot corner is an end plane.
        low = [s for s,q in profile if s < 0]
        high = [s for s,q in profile if s > 0]
        member = {'grain':grain.toTuple(), 'centre_mm':centre.toTuple(),
                  'end_stations_mm':[max(low), min(high)], 'depth_mm':model.DEPTH,
                  'width_mm':model.THICKNESS, 'additional_section_boxes':[],
                  'profile_sq_mm':profile, 'profile_xyz_mm':[v.toTuple() for v in vertices],
                  'blank_mm':part.blank, 'end_basis':'Conservative full-depth interior grain interval of actual oblique end cuts',
                  'opening_records':[], 'openings_complete':False}
        cutters = []
        for c in connections:
            if name not in c.members:
                continue
            leg = isinstance(c, model.LegMvpBolt)
            diameter = model.HOLE_DIAMETER if leg else 11.1125 if c.kind == 'bolt' else c.diameter
            cutters.append((c.name, 'mechanical_bore', leg, cq.Solid.makeCylinder(
                diameter/2, c.length+2, c.start-c.direction, c.direction)))
            if c.members.index(name) == 0 and c.kind == 'screw':
                cutters.append((c.name, 'screw_head_recess', False, c.components()[1]))
        from mini_moonboard import no_shoes_frame as baseline_source
        for record in baseline_source.previous.bore_records():
            if record['member'] == name:
                cutter = baseline_source.previous.wiring.bore_shape(record).translate(baseline_source.SHIFT)
                cutters.append((str(record.get('name', record.get('led', 'service_passage'))), 'service_passage', False, cutter))
        removed = part.shape.cut(drilled[name].shape)
        for source, kind, leg, cutter in cutters:
            actual = part.shape.intersect(cutter)
            if actual.Volume() <= 1e-6:
                continue
            removed = removed.cut(cutter)
            if leg:
                continue
            bound = local_bounds(actual, centre, grain, normal)
            box = square_box(bound, model.DEPTH)
            member['additional_section_boxes'].append(box)
            member['opening_records'].append({'source':source, 'kind':kind, 'actual_removed_volume_mm3':actual.Volume(),
                'actual_bound_sq_mm':bound, 'conservative_full_width_square_sq_d_mm':box})
        member['unrepresented_removed_volume_mm3'] = removed.Volume()
        member['openings_complete'] = removed.Volume() < .01
        if not member['openings_complete']:
            raise ValueError('Unrepresented actual cuts in '+name)
        actual_axes = [(c.name, model.bolt_interface_point(c)) for c in leg_bolts if name in c.members]
        member['placement'] = placement(member, actual_axes)
        members[name] = member
    paths = ['mini_moonboard/leg_mvp_frame.py', 'mini_moonboard/no_shoes_frame.py',
             'mini_moonboard/wider_leg_hardware.py', 'scripts/leg_mvp_geometry.py']
    module_path = Path(model.__file__).resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix()
    if module_path not in paths:
        paths.append(module_path)
    return {'candidate':model.KEY, 'bolt_names':[c.name for c in leg_bolts],
            'bolt_diameter_mm':model.catalog.BOLT_DIAMETER, 'hole_diameter_mm':model.HOLE_DIAMETER,
            'members':members, 'drilling':model.drilling_records(),
            'raw_profile_reductions_in_net_section':False,
            'raw_profile_scope':'Opening completeness covers machining removed from the supplied raw shapes. Gross rectangular net-section envelopes exclude oblique end regions and any sole relief; assess those separately.',
            'placement_assumptions':{'drill_position_radius_mm':1., 'inward_cut_normal_mm':2.,
                                     'released_shop_tolerances':False},
            'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},
            'scope':'Actual CAD opening inventory and conservative net-section geometry; no local opening shear or stress-concentration qualification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'candidate':result['candidate'], 'members':len(result['members']),
                      'openings':sum(len(m['opening_records']) for m in result['members'].values())}))


if __name__ == '__main__':
    main()
