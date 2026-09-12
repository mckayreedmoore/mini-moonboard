"""Continuous rigid-floor equilibrium envelope for the reinforced candidate.

A Cartesian product of vertices encloses the multi-affine external wrench.
Feasible witnesses at every vertex prove feasibility throughout that envelope;
a failed enclosing vertex is not automatically a failure of an actual load.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from fea.rigid_floor_screen import solve
from fea.round_structural_global_envelope import locations
from fea.split_center_floor import necessary_conditions
from fea.user_load_envelope import hull

EVIDENCE = Path('docs/round-reinforcement-review/review.json')
LBF = 4.4482216152605


def enclosing_horizontal_vertices(limit=300., count=16):
    if count < 3 or limit < 0:
        raise ValueError('Require at least three vertices and nonnegative force')
    radius = limit/math.cos(math.pi/count)
    return [(radius*math.cos(2*math.pi*i/count),
             radius*math.sin(2*math.pi*i/count)) for i in range(count)]


def wrench(point, outward, offset, downward, horizontal, mass, centre):
    force = np.array([*horizontal, -downward], dtype=float)
    position = np.asarray(point)+offset*np.asarray(outward)
    gravity = np.array([0., 0., -mass*9.80665])
    return np.concatenate((force+gravity, np.cross(position, force)+
                           np.cross(centre, gravity))).tolist()


def boundary_locations(all_locations):
    """Take each coplanar family's exact convex hull in its own two axes."""
    selected = []
    for kicker in (False, True):
        group = [p for p in all_locations if p[0].startswith('kicker_') == kicker]
        # Main holds span X/Z; kicker holes are collinear in X at constant Z.
        if kicker:
            selected.extend((min(group, key=lambda p: p[1][0]),
                             max(group, key=lambda p: p[1][0])))
        else:
            polygon = hull([[p[1][0], p[1][2]] for p in group])
            selected.extend(next(p for p in group if
                                 np.allclose([p[1][0], p[1][2]], vertex, atol=1e-8))
                            for vertex in polygon)
    return selected


def build():
    from mini_moonboard import round_reinforcement_frame as model

    raw = EVIDENCE.read_bytes()
    evidence = json.loads(raw)
    # Geometry and inventory must match the authenticated current mass report.
    for filename, expected in evidence['source_sha256'].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Stale geometry/mass evidence: '+filename)
    state = evidence['state']
    all_locations = locations(model)
    boundary = boundary_locations(all_locations)
    floor = [[*p, 0.] for p in state['support_polygon_mm']]
    horizontal = enclosing_horizontal_vertices()
    cases = []
    for loc, downward, scale, offset, h in itertools.product(
            boundary, (250*LBF, 600*LBF), (.8, 1.), (0., 100.), horizontal):
        name, point, outward = loc
        external = wrench(point, outward, offset, downward, h,
                          state['mass_kg']*scale, state['centre_xyz_mm'])
        cases.append({'hold': name, 'downward_n': downward, 'mass_scale': scale,
                      'standoff_mm': offset, 'horizontal_n': h,
                      'wrench_n_nmm': external})
    summaries, witnesses = {}, {}
    for mu in (.1, .2, .4):
        feasible, unproven, actual_failures = 0, 0, []
        maximum_force_residual, maximum_moment_residual = 0., 0.
        first_witness = None
        for case in cases:
            result = solve(floor, case['wrench_n_nmm'], mu)
            if result['polygon_feasible']:
                feasible += 1
                maximum_force_residual = max(maximum_force_residual,
                                            max(map(abs, result['residual_wrench'][:3])))
                maximum_moment_residual = max(maximum_moment_residual,
                                             max(map(abs, result['residual_wrench'][3:])))
                if first_witness is None:
                    first_witness = {**case, **result}
            else:
                unproven += 1
                # A circumscribed vertex lies outside H<=300N. Test its actual
                # disk-boundary counterpart before claiming any real failure.
                loc = next(p for p in boundary if p[0] == case['hold'])
                h = np.asarray(case['horizontal_n'])*math.cos(math.pi/16)
                actual = wrench(loc[1], loc[2], case['standoff_mm'],
                                case['downward_n'], h, state['mass_kg']*case['mass_scale'],
                                state['centre_xyz_mm'])
                necessary = necessary_conditions(floor, actual, mu)
                if necessary['circular_cone_infeasibility_proven']:
                    actual_failures.append({**case, 'horizontal_n': h.tolist(),
                                            'wrench_n_nmm': actual,
                                            'necessary_conditions': necessary})
        summaries[str(mu)] = {
            'enclosing_vertices': len(cases), 'feasible_vertices': feasible,
            'vertices_without_witness': unproven,
            'continuous_envelope_equilibrium_proven': feasible == len(cases),
            'actual_disk_boundary_failures_proven': len(actual_failures),
            'first_actual_failure': actual_failures[0] if actual_failures else None,
            'maximum_force_residual_n': maximum_force_residual,
            'maximum_moment_residual_nmm': maximum_moment_residual,
        }
        witnesses[str(mu)] = first_witness
    return {
        'candidate': model.KEY, 'mass_evidence': str(EVIDENCE),
        'mass_evidence_sha256': hashlib.sha256(raw).hexdigest(),
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          (Path(__file__).relative_to(Path.cwd()),
                           Path('fea/rigid_floor_screen.py'),
                           Path('fea/round_structural_global_envelope.py'),
                           Path('fea/split_center_floor.py'), Path('fea/user_load_envelope.py'))},
        'state': state, 'floor_vertices_mm': floor,
        'all_hold_count': len(all_locations), 'boundary_locations': boundary,
        'summary': summaries, 'representative_witnesses': witnesses,
        'proof': 'External wrench is multi-affine in coplanar hold position, standoff, '
                 'horizontal force, downward force and mass scale at fixed centre. '
                 'Its image is contained in the convex hull of their product vertices. '
                 'The circumscribed 16-gon encloses the 300N horizontal disk; '
                 'the contact-force feasible set is convex. Feasible independently '
                 'verified witnesses at every vertex therefore cover every interior '
                 'load and horizontal azimuth, including H=0.',
        'assumptions': [
            'One resultant at one of 142 holds; no independent multi-hold couples.',
            ('Downward force 250 through 600 lbf covers intended 250 lb x1/x2 and '
            '300 lb x1/x2 sensitivity; project load comparison, not impact certification.'),
            'Horizontal magnitude at most 300 N; outward hold standoff 0 through 100 mm.',
            ('Mass 80% through 100% of modeled 181.2058 kg at unchanged modeled centre; '
            'this is an assumed range, not a measured lower bound.'),
            ('Rigid level floor beneath four posts and two leg feet; compression-only '
            'contact, identical assumed Coulomb coefficient at each contact.'),
            'No kicker support, anchor, additional ballast or pad credit in global equilibrium.',
            ('No physical floor test required by owner. Coefficient is an installation '
            'assumption; no claim of measured friction, floor bearing capacity, actual '
            'pressure allocation or flexible-frame compatibility.'),
        ],
        'build_ready': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build()
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report['summary'], indent=2))
