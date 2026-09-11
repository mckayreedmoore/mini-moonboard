"""Installed base-angle directional reference domain, not current frame demands."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from mini_moonboard import angle_base_frame as model

LBF_N = 4.4482216152605
LETTER = 'https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf'
CATALOG = 'https://ssttoolbox.widen.net/content/wrzfhjzbna/pdf/C-C-2026-p323.pdf'
LETTER_SHA256 = '88d9051a9eadc08508a1a1c591914217309d6a2c1a281b375149d0cc57e584ff'
REFERENCE = {'F1': 595.*LBF_N, 'F3': 450.*LBF_N, 'F4': 750.*LBF_N}


def assess(force_xyz_n, moment_xyz_nmm, u, v):
    """Conditional single-direction check of a supplied rim-side local wrench.

    No arbitrary eccentric force may be moved to the bracket without its
    moment. Signed force is applied to the rim; positive v lifts off header.
    """
    vectors = (force_xyz_n, moment_xyz_nmm, u, v)
    if any(len(a) != 3 or not all(math.isfinite(x) for x in a) for a in vectors):
        raise ValueError('Finite three-component vectors required')
    dot = lambda a, b: math.fsum(x*y for x, y in zip(a, b, strict=True))
    if abs(dot(u, u)-1.) > 1e-8 or abs(dot(v, v)-1.) > 1e-8 or abs(dot(u, v)) > 1e-8:
        raise ValueError('Orthonormal flange axes required')
    w = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    local = {'bend_axis': dot(force_xyz_n, w), 'toward_angle_face': dot(force_xyz_n, u),
             'away_from_header': dot(force_xyz_n, v)}
    components = [('F1', abs(local['bend_axis'])),
                  ('F4' if local['toward_angle_face'] >= 0 else 'F3', abs(local['toward_angle_face']))]
    ratios = [{'direction': name, 'demand_n': force, 'conditional_reference_n': REFERENCE[name],
               'component_ratio': force/REFERENCE[name]} for name, force in components if force > 1e-8]
    reasons = []
    if any(abs(m) > 1e-8 for m in moment_xyz_nmm):
        reasons.append('Applied moment/eccentricity not covered by a free moment rating')
    if local['away_from_header'] > 1e-8:
        reasons.append('Uplift F2 not listed for bearing installation')
    elif local['away_from_header'] < -1e-8:
        reasons.append('Downward force requires separate wood/contact bearing assessment')
    if len(ratios) > 1:
        reasons.append('Simultaneous directional interaction not established by the inspected ML letter')
    applicable = not reasons and len(ratios) == 1
    return {'force_on_rim_xyz_n': list(force_xyz_n), 'moment_on_rim_xyz_nmm': list(moment_xyz_nmm),
            'local_components_n': local, 'component_references': ratios,
            'conditional_single_direction_comparison_available': applicable,
            'conditional_single_direction_within_reference': ratios[0]['component_ratio'] <= 1. if applicable else None,
            'unassessed_reasons': reasons, 'qualified_for_design': False,
            'actual_installation_approved': False}


def sources():
    paths = {*Path('mini_moonboard').glob('*.py'), Path(__file__), Path('docs/ml24z-reference.json')}
    root = Path.cwd()
    return {str(p.resolve().relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def build():
    hashes = sources()
    reference = json.loads(Path('docs/ml24z-reference.json').read_text())
    if reference['loads']['bearing']['DF_SP'] != [595, None, 450, 750]:
        raise ValueError('Stored bearing references differ from inspected letter')
    rows = []
    for name, origin, u, v, supporting, loaded in model.stations():
        if not name.startswith('clip_angle_base_'):
            continue
        connections = [c for c in model.connections() if c.name.startswith(name+'_')]
        counts = {n: sum(n in c.members for c in connections) for n in (supporting, loaded)}
        if len(connections) != 6 or any(n != 3 for n in counts.values()):
            raise ValueError('Require three prescribed SDS screws in each member')
        if any(abs(c.length-38.1) > 1e-8 or abs(c.diameter-6.35) > 1e-8 for c in connections):
            raise ValueError('Unexpected base-angle screw dimensions')
        uu, vv = list(u.toTuple()), list(v.toTuple())
        probes = []
        for axis in range(3):
            for sign in (-1., 1.):
                force = [0., 0., 0.]
                force[axis] = sign*1000.
                probes.append(assess(force, [0., 0., 0.], uu, vv))
        rows.append({'angle': name, 'reference_origin_xyz_mm': list(origin.toTuple()),
                     'loaded_member': loaded, 'supporting_member': supporting,
                     'u_toward_angle_xyz': uu, 'v_uplift_xyz': vv,
                     'screw_counts': counts, 'single_axis_1000n_probes': probes,
                     'probe_scope': 'Synthetic unit-scale direction probes; not predicted current joint loads'})
    if len(rows) != 2:
        raise ValueError('Require both current outer base angles')
    if hashes != sources():
        raise ValueError('Source changed during screen')
    return {'candidate': model.KEY, 'qualified_for_design': False, 'joint_strength_passed': False,
            'current_frame_forces_available': False, 'frame_solve_run': False,
            'conditional_single_direction_reference_n': REFERENCE,
            'manufacturer_sources': {'letter': LETTER, 'letter_sha256': LETTER_SHA256,
                                     'catalog_page_323': CATALOG, 'checked_date': '2026-09-11'},
            'installation_interpretation': 'Bearing installation analogy: rim end bears on header, angle is on rim side. '
                                           'F1 follows bend/world Y; F3 points away from angle/outward X; '
                                           'F4 points toward angle/inward X. Figure interpretation is not manufacturer application approval.',
            'conditions': ['Single ML24Z with six specified SDS25112 screws; three into each member.',
                           'DF/SP table is conditional on identified applicable lumber and installation; no unknown species credit.',
                           'No duration increase for these single-connector ML24Z values.',
                           'Cross-grain bending/tension and mechanical reinforcement require separate consideration.',
                           'Geometry fit does not establish timber edge/end resistance, moisture/corrosion suitability or withdrawal strength.',
                           'No F2 uplift entry in bearing table; do not substitute single/end or paired-connector table values.',
                           'No mixed-axis or free-moment interaction established here; do not sum bracket capacities or divide frame load equally.'],
            'angles': rows, 'next_required_input': 'Independently checked current rim-to-header force and moment demands '
                                                'with compression-only wood bearing, real restraints, connector slip and load sharing. '
                                                'Resolve uplift/moment/interaction applicability before an adequacy verdict.',
            'source_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
