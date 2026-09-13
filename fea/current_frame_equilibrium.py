"""Current shoe-free CAD rigid-body equilibrium; no internal strength claim."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from fea.user_load_envelope import hull

G = 9.80665
LBF = 4.4482216152605


def equilibrium(points, forces, polygon):
    """Required compression resultant at Z=0, assuming no-slip horizontal support."""
    p, f = np.asarray(points, float), np.asarray(forces, float)
    if p.shape != f.shape or p.ndim != 2 or p.shape[1] != 3 or not np.isfinite([p, f]).all():
        raise ValueError('Require matching finite XYZ points and forces')
    force = f.sum(axis=0)
    moment = np.cross(p, f).sum(axis=0)
    normal = -float(force[2])
    if normal <= 0:
        raise ValueError('Require positive net downward load')
    xy = np.array([moment[1]/normal, -moment[0]/normal])
    margins = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
        a, b = np.array(a), np.array(b)
        edge = b-a
        distance = (edge[0]*(xy[1]-a[1])-edge[1]*(xy[0]-a[0]))/np.linalg.norm(edge)
        margins.append(float(distance))
    index = int(np.argmin(margins))
    return {'vertical_reaction_n': normal, 'required_pressure_centre_xy_mm': xy.tolist(),
            'minimum_edge_margin_mm': margins[index], 'edge_index': index,
            'minimum_restoring_moment_nmm': normal*margins[index],
            'normal_equilibrium_feasible': min(margins) >= -1.e-7,
            'required_horizontal_reaction_xy_n': (-force[:2]).tolist(),
            'required_floor_yaw_moment_nmm': -float(moment[2])}


def reaction_ranges(supports, result):
    """Extremize each footprint reaction; feasibility is not a pressure prediction."""
    vertices = [(s['name'], p) for s in supports for p in s['vertices_mm']]
    xy = np.array([p[:2] for _, p in vertices])
    scale = max(1., float(np.abs(xy).max()))
    matrix = np.vstack([np.ones(len(vertices)), xy.T/scale])
    normal = result['vertical_reaction_n']
    target = normal*np.array([1., *np.array(result['required_pressure_centre_xy_mm'])/scale])
    rows = []
    for support in supports:
        objective = np.array([float(name == support['name']) for name, _ in vertices])
        lo = linprog(objective, A_eq=matrix, b_eq=target, bounds=(0, None), method='highs')
        hi = linprog(-objective, A_eq=matrix, b_eq=target, bounds=(0, None), method='highs')
        if not lo.success or not hi.success:
            if not result['normal_equilibrium_feasible']:
                return []
            raise ValueError('LP disagrees with support polygon feasibility')
        if max(np.abs(matrix@lo.x-target)) > 1.e-5:
            raise ValueError('Reaction equilibrium residual')
        rows.append({'name': support['name'], 'minimum_n': float(lo.fun), 'maximum_n': float(-hi.fun)})
    return rows


def azimuth_envelope(report):
    """Exact horizontal-circle edge extrema, optionally bounding equipment XY."""
    polygon = report['support_polygon_mm']
    locations = report['load_locations']
    cg = report['modeled_centre_xyz_mm']
    mass = report['modeled_mass_kg']
    rows = []
    for equipment_mode in ('centered_baseline', 'within_hold_xy_hull'):
        for pounds in (150, 250):
            for multiplier in (1, 2):
                worst = None
                for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
                    edge = np.array(b)-np.array(a)
                    outward = np.array([edge[1], -edge[0]])/np.linalg.norm(edge)
                    equipment = report['equipment_point_xyz_mm']
                    if equipment_mode == 'within_hold_xy_hull':
                        equipment = max((r['front_xyz_mm'] for r in locations),
                                        key=lambda p: np.dot(p[:2], outward))
                    for location in locations:
                        for standoff in (0., 100.):
                            point = np.array(location['front_xyz_mm'])+standoff*np.array(location['outward_xyz'])
                            result = equilibrium([cg, equipment, point],
                                [[0., 0., -mass*G], [0., 0., -25.*G],
                                 [*(300.*outward), -pounds*LBF*multiplier]], polygon)
                            row = {'climber_lb': pounds, 'vertical_multiplier': multiplier,
                                   'equipment_mode': equipment_mode, 'equipment_point_xyz_mm': list(equipment),
                                   'horizontal_force_xy_n': (300.*outward).tolist(),
                                   'hold': location['name'], 'standoff_mm': standoff, **result}
                            if worst is None or row['minimum_edge_margin_mm'] < worst['minimum_edge_margin_mm']:
                                worst = row
                rows.append({**worst, 'normal_reaction_ranges': reaction_ranges(report['supports'], worst)})
    return rows


def source_hashes():
    # Freeze all current geometry dependencies, without relying on historic bundles.
    paths = [Path(__file__), Path('fea/user_load_envelope.py'), Path('uv.lock')]
    paths.extend(Path('mini_moonboard').glob('*.py'))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


def build():
    from mini_moonboard import hold_tnut_reinforcement as tnuts
    from mini_moonboard import no_shoes_frame as model

    before = source_hashes()
    parts = model.parts()
    inventory, supports = [], []

    def add(name, shape, density):
        if not shape.isValid():
            raise ValueError('Invalid current mass shape: '+name)
        inventory.append({'name': name, 'density_kg_m3': density,
            'mass_kg': shape.Volume()*density/1.e9, 'centre_xyz_mm': list(shape.Center().toTuple())})

    for part in parts:
        steel = part.name.startswith(('clip_', 'hold_tnut_'))
        if not steel and not part.name.startswith(('base_', 'main_', 'kicker_', 'lumber_leg_')):
            raise ValueError('Unclassified material: '+part.name)
        add(part.name, part.shape, 7850. if steel else 600.)
        inventory[-1]['stock_blank_mm'] = list(part.blank)
        if part.name.startswith(('base_post_', 'lumber_leg_')):
            vertices = sorted({tuple(v.Center().toTuple()) for v in part.shape.Vertices() if abs(v.Z) < 1.e-6})
            if len(vertices) != 4:
                raise ValueError('Expected four current foot vertices: '+part.name)
            supports.append({'name': part.name, 'vertices_mm': [list(p) for p in vertices]})
    for c in model.connections():
        components = tuple(c.components())
        shape = components[0].fuse(*components[1:]) if len(components) > 1 else components[0]
        add('fastener_'+c.name, shape, 7850.)
    if len(supports) != 6:
        raise ValueError('Require four posts and two rear feet')
    mass = sum(r['mass_kg'] for r in inventory)
    cg = sum((r['mass_kg']*np.array(r['centre_xyz_mm']) for r in inventory), np.zeros(3))/mass
    polygon = hull([p[:2] for s in supports for p in s['vertices_mm']])
    locations = []
    for row in tnuts.datums(model):
        normal = np.array(row['barrel_into_panel_direction'])
        front = np.array(row['rear_seating_xyz_mm'])+normal*model.wide.PANEL
        locations.append((row['name'], front, normal))
    top = max(locations, key=lambda row: row[1][2])[1]
    equipment = np.array([0., top[1], top[2]])
    cases = []
    directions = {'none': (0., 0.), 'left': (-300., 0.), 'right': (300., 0.),
                  'front': (0., -300.), 'rear': (0., 300.)}
    for pounds in (150, 250):
        for multiplier in (1, 2):
            for direction, horizontal in directions.items():
                for standoff in (0., 100.):
                    for name, face, normal in locations:
                        result = equilibrium([cg, equipment, face+standoff*normal],
                            [[0., 0., -mass*G], [0., 0., -25.*G],
                             [*horizontal, -pounds*LBF*multiplier]], polygon)
                        cases.append({'climber_lb': pounds, 'vertical_multiplier': multiplier,
                            'horizontal_case': direction, 'standoff_mm': standoff,
                            'hold': name, **result})
    governing = []
    for pounds in (150, 250):
        for multiplier in (1, 2):
            for direction in directions:
                row = min((r for r in cases if r['climber_lb'] == pounds
                           and r['vertical_multiplier'] == multiplier and r['horizontal_case'] == direction),
                          key=lambda r: r['minimum_edge_margin_mm'])
                governing.append({**row, 'normal_reaction_ranges': reaction_ranges(supports, row)})
    if before != source_hashes():
        raise ValueError('Source changed during current CAD assessment')
    report = {'candidate': model.KEY, 'source_sha256': before,
        'modeled_mass_kg': mass, 'modeled_centre_xyz_mm': cg.tolist(), 'mass_inventory': inventory,
        'equipment_mass_kg': 25., 'equipment_point_xyz_mm': equipment.tolist(),
        'supports': supports, 'support_polygon_mm': polygon, 'hold_count': len(locations),
        'load_locations': [{'name': name, 'front_xyz_mm': p.tolist(), 'outward_xyz': n.tolist()} for name, p, n in locations],
        'case_count': len(cases), 'infeasible_case_count': sum(not r['normal_equilibrium_feasible'] for r in cases),
        'governing_cases': governing, 'cases': cases,
        'internal_member_connection_strength_evaluated': False, 'build_ready': False,
        'assumptions': [
            'Current drilled CAD and complete fused fastener stacks; wood/plywood 600 kg/m3, steel 7850 kg/m3. Densities are declared assumptions.',
            '25 kg equipment at centered uppermost hold plane; explicit placement assumption, not worst placement for every overturning edge.',
            'One climber resultant at one of 142 hold locations; 150 and 250 lb comparisons are not ratings.',
            'Static 1x and selected 2x vertical sensitivity are separate; 300 N horizontal loads act along one axis at a time. No claimed exhaustive dynamic envelope.',
            'Feet do not slide; horizontal reactions and floor yaw resistance assumed available. Friction and tangential wrench feasibility not qualified.',
            'Only four timber posts and two rear timber feet support the frame. Pad and kicker edges provide no structural support; feet carry compression only.',
            'Positive edge margin establishes admissible normal equilibrium of the complete rigid body, not compatibility or strength of its deformable members/joints.',
            'LP reaction ranges are individually attainable statics bounds; extrema for different feet need not coexist and are not predicted contact pressure.',
            'No prescribed overturning safety factor applied; restoring moment and edge distance are raw equilibrium reserve, not rated design acceptance.'
        ]}
    report['all_horizontal_azimuth_envelope'] = azimuth_envelope(report)
    report['assumptions'].append('Additional exact edge-normal envelope covers every horizontal azimuth at 300 N. Equipment XY bounded option permits 25 kg anywhere in the convex hull of current hold front XY positions; this excludes locations beyond that footprint. No dynamic equipment loading.')
    return report


if __name__ == '__main__':
    output = Path('fea/results/current-frame-equilibrium.json')
    report = build()
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: report[k] for k in ('modeled_mass_kg', 'case_count', 'infeasible_case_count')}))
