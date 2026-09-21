"""Compare recovered SPAX/ML24Z forces; retain contact and couple limitations."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.round_structural_screw_reference import LBF_N, wood_interaction

ROOT = Path(__file__).resolve().parents[1]
LOOKUP = ROOT/'docs/reinforced-fastener-applicability.json'
HEAD_N = 120*LBF_N
WITHDRAWAL_N = 133*1.24*LBF_N
LATERAL_N = 235.67993471590563
VALIDITY = ('global_equilibrium_passed', 'mpc_check_passed',
            'contact_active_set_converged', 'closed_bearing_assumption_passed')


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def norm(a):
    return math.sqrt(dot(a, a))


def subtract(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def vector(value):
    if len(value) != 3 or not all(math.isfinite(x) for x in value):
        raise ValueError('Require finite three-component vector')
    return list(value)


def wrench(rows, origin, force_key='force_on_second_xyz_n'):
    """Forces at their physical application points, about one declared origin."""
    force, moment = [0., 0., 0.], [0., 0., 0.]
    for row in rows:
        f = vector(row[force_key])
        m = cross(subtract(vector(row['point']), origin), f)
        force = [x+y for x, y in zip(force, f, strict=True)]
        moment = [x+y for x, y in zip(moment, m, strict=True)]
    return {'force_xyz_n': force, 'moment_xyz_nmm': moment,
            'parallel_couple_nmm': dot(force, moment)/norm(force) if norm(force) > 1e-9 else None}


def panel_check(row):
    """Installation axis points into wood: tensile force on wood is opposite."""
    force, axis = vector(row['force_on_first_xyz_n']), vector(row['axis'])
    if not math.isclose(norm(axis), 1., abs_tol=1e-8):
        raise ValueError('Installation axis must be unit length')
    axial = dot(force, axis)
    tension = max(0., -axial)
    shear = norm(subtract(force, [axial*x for x in axis]))
    return {'tension_n': tension, 'compression_n': max(0., axial), 'shear_n': shear,
            'axial_along_installation_direction_n': axial,
            **wood_interaction(tension, shear, withdrawal_n=WITHDRAWAL_N,
                               lateral_reference_n=LATERAL_N, head_reference_n=HEAD_N),
            'steel_tension_component_ratio': tension/(460*LBF_N),
            'steel_shear_component_ratio': shear/(345*LBF_N),
            'combined_steel_resistance_established': False,
            'compression_action_accepted': False}


def geometry():
    from mini_moonboard import round_reinforcement_frame as model

    panels = {c.name: {'first': c.members[1], 'second': c.members[0],
                       'axis': c.direction.toTuple(),
                       'point': (c.start+c.direction*(model.wide.PANEL/2)).toTuple()}
              for c in model.panel_connections()}
    clips = {c.name: {'first': c.members[1], 'second': c.members[0],
                      'axis': c.direction.toTuple(),
                      'point': (c.start+c.direction*model.hardware.ML['thickness']).toTuple()}
             for c in model.connections() if c.name.startswith('clip_')}
    stations = json.loads(LOOKUP.read_text())['ML24Z']['stations']
    current = {r[0]: r for r in model.stations()}
    if set(current) != {r['name'] for r in stations}:
        raise ValueError('Stale ML station inventory')
    for row in stations:
        actual = current[row['name']]
        for key, value in zip(('origin_mm', 'u', 'v'), actual[1:4], strict=True):
            if norm(subtract(row[key], value.toTuple())) > 1e-8:
                raise ValueError('Stale ML axes/origin: '+row['name'])
    return panels, clips, stations


def validate_row(name, row, expected):
    for key in ('first', 'second'):
        if row[key] != expected[key]:
            raise ValueError(name+': receiver ownership differs')
    for key in ('axis', 'point'):
        if norm(subtract(vector(row[key]), expected[key])) > 1e-6:
            raise ValueError(name+': '+key+' differs from current geometry')
    first, second = vector(row['force_on_first_xyz_n']), vector(row['force_on_second_xyz_n'])
    if norm([a+b for a, b in zip(first, second, strict=True)]) > 1e-6:
        raise ValueError(name+': action/reaction mismatch')


def assess(report, model_geometry=None):
    panels, clips, stations = model_geometry or geometry()
    forces = report['physical_connection_forces']
    required = panels | clips
    missing = sorted(set(required)-set(forces))
    if missing:
        raise ValueError('Missing physical fastener forces: '+', '.join(missing))
    for name, expected in required.items():
        validate_row(name, forces[name], expected)
    panel_results = [{'name': name, 'receiver': forces[name]['first'],
                      'panel': forces[name]['second'], **panel_check(forces[name])}
                     for name in panels]
    angle_results = []
    for station in stations:
        name, origin = station['name'], station['origin_mm']
        groups = {flange: [forces[f'{name}_{flange}_{i}'] for i in (1, 2, 3)]
                  for flange in ('beam', 'upright')}
        flanges = {key: wrench(rows, origin) for key, rows in groups.items()}
        # Six screws balance the free bracket. Joint transfer is a flange wrench,
        # not the sum over both flanges, which would conceal the demand.
        residual = wrench(groups['beam']+groups['upright'], origin)
        bearing = station['F2_catalog_allowable_lbf'] is None
        loaded = flanges['upright' if bearing else 'beam']
        f = loaded['force_xyz_n']
        projected = {key: dot(f, station[axis]) for key, axis in (
            ('F1', 'F1_axis'), ('F2', 'F2_separation_axis'), ('F34', 'F3_F4_axis_unsigned'))}
        # Wrench is member-on-bracket. Positive separation loading of that member
        # puts force on the bracket in the listed outward direction.
        separation = max(0., projected['F2'])
        unity = (abs(projected['F1'])/(595*LBF_N)+abs(projected['F2'])/(450*LBF_N)
                 +abs(projected['F34'])/(450*LBF_N)) if not bearing else None
        angle_results.append({'name': name, 'origin_xyz_mm': origin,
            'first_member': station['first_member'], 'second_member': station['second_member'],
            'flange_member_on_bracket_wrenches': flanges,
            'all_six_screw_free_body_residual': residual,
            'loaded_flange': 'upright' if bearing else 'beam',
            'projected_loaded_flange_force_n': projected,
            'single_end_conservative_absolute_force_unity': unity,
            'bearing_separation_demand_n': separation if bearing else None,
            'bearing_separation_capacity_n': None,
            'bearing_compression_direction_force_n': max(0., -projected['F2']) if bearing else None,
            'bearing_rated_shear_only_unity': (abs(projected['F1'])/(595*LBF_N)
                +abs(projected['F34'])/(450*LBF_N)) if bearing else None,
            'independent_couple_resolved': False, 'connection_rating_passed': False,
            'limits': 'Force projections retain full flange moments. Missing independent-couple '
                      'rating is not created by force unity. Six bearing-like grain/mounting '
                      'applicability remains separate; compression force is not a bearing pass.'})
    validity = {key: report.get(key) for key in VALIDITY}
    converged = all(value is True for value in validity.values())
    def peak(key):
        return max(panel_results, key=lambda row: row[key]) if panel_results else None
    return {'candidate': report.get('candidate'), 'parameters': report.get('parameters'),
            'producer_validity': validity,
            'response_status': 'converged_conditional_model' if converged else 'INVALID_RESPONSE_DIAGNOSTIC_ONLY',
            'panel_screw_count': len(panel_results), 'ML24Z_count': len(angle_results),
            'panel_checks': panel_results, 'ML24Z_checks': angle_results,
            'peak_panel_wood_interaction': peak('wood_interaction_ratio'),
            'peak_panel_head_ratio': peak('head_pull_through_ratio'),
            'qualified_for_design': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demands', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-invalid-diagnostic', action='store_true')
    parser.add_argument('--floor-friction', type=float, default=.4)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.demands.read_bytes()
    report = json.loads(raw)
    result = assess(report)
    sources = report.get('source_sha256', {})
    mismatches = [path for path, sha in sources.items()
                  if not (ROOT/path).is_file() or hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != sha]
    snapshot_mismatches = [path for path, sha in sources.items()
        if not (args.demands.parent/'source_snapshots'/path).is_file()
        or hashlib.sha256((args.demands.parent/'source_snapshots'/path).read_bytes()).hexdigest() != sha]
    matched = bool(sources) and not snapshot_mismatches
    result['current_producer_sources_match'] = bool(sources) and not mismatches
    result['producer_source_mismatches'] = mismatches
    result['archived_producer_sources_match'] = matched
    result['producer_snapshot_mismatches'] = snapshot_mismatches
    invalid = result['response_status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY' or not matched
    if invalid and not args.allow_invalid_diagnostic:
        raise ValueError('Unconverged or stale response; diagnostic mode must be explicit')
    if invalid:
        result['response_status'] = 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    if not math.isfinite(args.floor_friction) or args.floor_friction < 0:
        raise ValueError('Require nonnegative finite floor friction assumption')
    feet = report.get('floor_foot_friction_demands', [])
    floor_pass = bool(feet) and all(
        row.get('friction_wrench_feasible') is True
        and row.get('sufficient_friction_coefficient') is not None
        and row['sufficient_friction_coefficient'] <= args.floor_friction for row in feet)
    result['assumed_floor_friction'] = args.floor_friction
    result['floor_foot_friction_demands'] = feet
    result['sticking_floor_admissible_under_assumption'] = floor_pass
    if not invalid and not floor_pass:
        result['response_status'] = 'CONVERGED_STICKING_MODEL_FLOOR_NOT_ACCEPTED'
    result['archived_producer_replay_verified'] = False
    result['input_report_sha256'] = hashlib.sha256(raw).hexdigest()
    result['input_report'] = str(args.demands)
    result['producer_artifact_manifest'] = report.get('artifact_sha256', {})
    result['producer_artifact_bytes_reverified'] = False
    result['input_physical_connection_forces'] = report['physical_connection_forces']
    result['references_n'] = {'head': HEAD_N, 'withdrawal': WITHDRAWAL_N, 'lateral': LATERAL_N,
                              'steel_tension': 460*LBF_N, 'steel_shear': 345*LBF_N}
    result['resistance_basis'] = ('CD=CM=Ct=1 assumed dry normal-temperature ASD; reference '
        'sources in docs/reinforced-fastener-applicability.md and round-structural-screw-calculation.md')
    paths = (Path(__file__), LOOKUP, ROOT/'fea/round_structural_screw_reference.py')
    result['consumer_source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in paths}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': result['response_status'],
                      'panel_screws': result['panel_screw_count'], 'angles': result['ML24Z_count']}))


if __name__ == '__main__':
    main()
