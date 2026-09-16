"""Audit and consolidate six native case angle demands, without rating connections.

Inputs are native report.json directories plus their separately generated
clear-space assessment.json files. Every manifest-declared native artifact and
source snapshot is checked. Wrenches are independently reconstructed from the
144 physical screw-force records in each case and compared with the supplied
assessment. Resistance comparisons are NOT recomputed or authenticated as a
complete structural assessment. An output from this program is never a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.clear_space_case_contract import validate_case_identity

CANDIDATE = 'compact-floor-flush-development'
CASES = {
    'a12-left': ('A12', (-300., 0.)),
    'a12-rear': ('A12', (0., 300.)),
    'a12-forward': ('A12', (0., -300.)),
    'k12-right': ('K12', (300., 0.)),
    'k12-rear': ('K12', (0., 300.)),
    'a1-rear': ('A1', (0., 300.)),
}
VALIDITY = (
    'global_equilibrium_passed', 'mpc_check_passed',
    'contact_active_set_converged', 'closed_bearing_assumption_passed',
    'member_equilibrium_passed', 'numerically_accepted',
)
FLANGES = ('beam', 'upright')
VECTOR_ATOL = 1.e-8  # serialization/reconstruction comparison, not a physical limit
VECTOR_RTOL = 1.e-10
FORCE_DIRECTION_EPS_N = 1.e-9  # matches the existing wrench helper's reporting cutoff


def _object(value: Any, label: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise ValueError(f'{label} must be an object')  # noqa: TRY004 -- invalid input value
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be a finite number')  # noqa: TRY004 -- invalid input value
    try:
        value = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f'{label} must be a finite number') from exc
    if not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number')
    return value


def _vector(value: Any, label: str) -> tuple[float, float, float]:
    if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
            or len(value) != 3):
        raise ValueError(f'{label} must contain three numbers')
    return tuple(_number(v, label) for v in value)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _close(a, b, label):
    if any(not math.isclose(x, y, rel_tol=VECTOR_RTOL, abs_tol=VECTOR_ATOL)
           for x, y in zip(_vector(a, label), _vector(b, label), strict=True)):
        raise ValueError(f'{label} does not match reconstructed native forces')


def wrench_diagnostic(rows: Sequence[Mapping], origin: Sequence[float]) -> dict:
    """Non-lossy force/moment decomposition. This assigns no capacity.

    A negligible resultant has no reliable direction: retain the complete
    origin moment, flag this branch, and do not turn a null signed projection
    into zero demand. All origin moments remain available even at nonzero force.
    """
    origin = _vector(origin, 'origin')
    forces, moments = [], []
    for row in rows:
        row = _object(row, 'physical force row')
        force = _vector(row.get('force_on_second_xyz_n'), 'force_on_second_xyz_n')
        opposite = _vector(row.get('force_on_first_xyz_n'), 'force_on_first_xyz_n')
        _close(opposite, tuple(-x for x in force), 'action/reaction')
        point = _vector(row.get('point'), 'point')
        forces.append(force)
        moments.append(_cross(tuple(p-o for p, o in zip(point, origin, strict=True)), force))
    force = tuple(math.fsum(f[i] for f in forces) for i in range(3))
    moment = tuple(math.fsum(m[i] for m in moments) for i in range(3))
    force_norm, moment_norm = math.hypot(*force), math.hypot(*moment)
    near_zero = force_norm <= FORCE_DIRECTION_EPS_N
    if near_zero:
        signed, independent = None, moment
    else:
        direction = tuple(f/force_norm for f in force)
        signed = math.fsum(m*d for m, d in zip(moment, direction, strict=True))
        independent = tuple(signed*d for d in direction)
    return {
        'force_xyz_n': list(force), 'moment_xyz_nmm': list(moment),
        'force_norm_n': force_norm, 'moment_norm_nmm': moment_norm,
        'force_direction_unresolved': near_zero,
        'signed_parallel_couple_nmm': signed,
        'independent_or_near_zero_force_moment_xyz_nmm': list(independent),
        'independent_or_near_zero_force_moment_norm_nmm': math.hypot(*independent),
        'moment_capacity_nmm': None,
        'capacity_assessment_performed': False,
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def _parse_json(data: bytes, label: str) -> dict:
    return _object(json.loads(data.decode('utf-8'),
        object_pairs_hook=_unique_object, parse_constant=_reject_constant), label)


def read_json(path: Path) -> dict:
    return _parse_json(path.read_bytes(), str(path))


def _read_document(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return _parse_json(raw, str(path)), hashlib.sha256(raw).hexdigest()


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _contained_file(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Manifest path must be a nonempty relative POSIX path')
    path = PurePosixPath(relative)
    if (path.is_absolute() or '..' in path.parts or ':' in relative
            or str(path) != relative):
        raise ValueError('Manifest path must be canonical and remain inside its root')
    target = (root/path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError('Missing or escaping manifest file: '+relative)
    return target


def verify_manifest(root: Path, manifest: Mapping) -> int:
    manifest = _object(manifest, 'hash manifest')
    if not manifest:
        raise ValueError('Require a nonempty hash manifest')
    for name, expected in manifest.items():
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('Invalid SHA256 for '+str(name))
        if digest(_contained_file(root, name)) != expected:
            raise ValueError('Manifest checksum mismatch: '+str(name))
    return len(manifest)


def inspect_case(case: str, native: Path, assessment_path: Path,
                 *, current_source_root: Path | None = None) -> dict:
    if case not in CASES:
        raise ValueError('Unexpected case: '+case)
    report_path = native/'report.json'
    report, report_hash = _read_document(report_path)
    assessment, assessment_hash = _read_document(assessment_path)
    hold, horizontal = CASES[case]
    validate_case_identity(report, expected_candidate=CANDIDATE, expected_hold=hold,
        expected_pounds=250., expected_horizontal_force=horizontal)
    if any(report.get(key) is not True for key in VALIDITY):
        raise ValueError('Native numerical validity flags are not all true: '+case)
    if assessment.get('candidate') != CANDIDATE:
        raise ValueError('Assessment candidate does not match: '+case)
    sources = _object(report.get('source_sha256'), 'source_sha256')
    snapshot_count = verify_manifest(native/'source_snapshots', sources)
    artifact_count = verify_manifest(native, report.get('artifact_sha256'))
    if current_source_root is not None:
        verify_manifest(current_source_root, sources)
    station_rows = report.get('angle_stations')
    if not isinstance(station_rows, list) or len(station_rows) != 24:
        raise ValueError('Require exactly 24 native angle stations')
    stations = {}
    for row in station_rows:
        row = _object(row, 'angle station')
        name = row.get('name')
        if not isinstance(name, str) or not name or name in stations:
            raise ValueError('Invalid or duplicate angle station name')
        stations[name] = row
    angles = _object(assessment.get('commercial_angles'), 'commercial_angles')
    if set(angles) != set(stations):
        raise ValueError('Assessment and native angle inventories differ')
    physical = _object(report.get('physical_connection_forces'), 'physical_connection_forces')
    result, screw_geometry = {}, {}
    for name in sorted(stations):
        expected_screws = {f'{name}_{flange}_{i}' for flange in FLANGES for i in (1, 2, 3)}
        actual_screws = {key for key, row in physical.items()
                         if isinstance(row, Mapping) and row.get('second') == name}
        if actual_screws != expected_screws:
            raise ValueError('Require exactly six physical screws per angle: '+name)
        for key in sorted(expected_screws):
            screw_geometry[key] = {field: physical[key].get(field)
                for field in ('first', 'second', 'point', 'axis')}
        station, angle = stations[name], _object(angles[name], 'angle assessment')
        origin = station.get('origin_mm', station.get('origin'))
        _close(origin, angle.get('origin_mm'), name+' origin')
        recorded_flange = _object(angle.get('flange_member_on_bracket_wrenches'), 'flanges')
        if set(recorded_flange) != set(FLANGES):
            raise ValueError('Require both and only the beam/upright flanges')
        rows, flanges = [], {}
        for flange in FLANGES:
            expected_names = [f'{name}_{flange}_{i}' for i in (1, 2, 3)]
            if any(n not in physical for n in expected_names):
                raise ValueError('Missing physical angle screw: '+name+' '+flange)
            group = [physical[n] for n in expected_names]
            for row in group:
                if (not isinstance(row, Mapping) or row.get('second') != name
                        or not isinstance(row.get('first'), str) or not row['first']):
                    raise ValueError('Incorrect physical wood/angle ownership: '+name)
            if len({row['first'] for row in group}) != 1:
                raise ValueError('One flange spans inconsistent receiver members: '+name)
            computed = wrench_diagnostic(group, origin)
            saved = _object(recorded_flange[flange], 'saved flange wrench')
            for key in ('force_xyz_n', 'moment_xyz_nmm'):
                _close(saved.get(key), computed[key], name+' '+flange+' '+key)
            flanges[flange] = computed
            rows.extend(group)
        # The complete bracket residual is equilibrium evidence, not its demand.
        residual = wrench_diagnostic(rows, origin)
        saved_residual = _object(angle.get('all_six_screw_residual'), 'angle residual')
        for key in ('force_xyz_n', 'moment_xyz_nmm'):
            _close(saved_residual.get(key), residual[key], name+' residual '+key)
        ratio = _number(angle.get('rated_force_component_unity'), 'reported force ratio')
        if ratio < 0 or type(angle.get('bearing_like')) is not bool:
            raise ValueError('Invalid reported angle ratio/type')
        projected = _object(angle.get('projected_loaded_flange_force_n'), 'projected force')
        if set(projected) != {'F1', 'F2', 'F34'}:
            raise ValueError('Unexpected projected force components')
        projected = {k: _number(v, k) for k, v in projected.items()}
        separation = angle.get('unlisted_separation_demand_n')
        if angle['bearing_like']:
            separation = _number(separation, 'unlisted separation')
            if not math.isclose(separation, max(0., projected['F2']),
                                rel_tol=VECTOR_RTOL, abs_tol=VECTOR_ATOL):
                raise ValueError('Unlisted separation disagrees with reported projection')
        elif separation is not None:
            raise ValueError('Non-bearing station must preserve not-applicable separation')
        result[name] = {
            'origin_mm': list(_vector(origin, 'origin')), 'flanges': flanges,
            'all_six_screw_equilibrium_residual': residual,
            'bearing_like_as_reported': angle['bearing_like'],
            'projected_force_n_as_reported': projected,
            'rated_force_component_unity_as_reported': ratio,
            'rated_resistance_recomputed': False,
            'unlisted_separation_demand_n_as_reported': separation,
            'unlisted_separation_capacity_n': None,
            'connection_qualified': False,
        }
    if digest(report_path) != report_hash or digest(assessment_path) != assessment_hash:
        raise ValueError('Input report or assessment changed during audit')
    return {
        'case': case, 'candidate': CANDIDATE, 'angle_count': len(result),
        'native_report_sha256': report_hash,
        'assessment_input_sha256': assessment_hash,
        'native_station_geometry': stations,
        'physical_angle_screw_geometry': screw_geometry,
        'source_sha256': dict(sources),
        'parameters': dict(report['parameters']),
        'manifest_declared_artifact_count_verified': artifact_count,
        'source_snapshot_count_verified': snapshot_count,
        'current_sources_checked': current_source_root is not None,
        'manifest_completeness_independently_established': False,
        'native_solver_replayed': False,
        'assessment_resistance_recomputed': False,
        'angles': result,
    }


def build_ledger(case_inputs: Sequence[tuple[str, Path, Path]],
                 *, current_source_root: Path | None = None) -> dict:
    if _consumer_hashes() != LOADED_CONSUMER_HASHES:
        raise ValueError('Consumer sources changed after import; restart the ledger process')
    names = [entry[0] for entry in case_inputs]
    if len(names) != 6 or len(set(names)) != 6 or set(names) != set(CASES):
        raise ValueError('Require all six distinct planned cases, exactly once')
    by_name = {case: (native, assessment) for case, native, assessment in case_inputs}
    cases = {}
    reference = None
    for case in CASES:
        native, assessment = by_name[case]
        item = inspect_case(case, native, assessment, current_source_root=current_source_root)
        common_parameters = {k: v for k, v in item['parameters'].items()
                             if k not in {'hold', 'pounds', 'force_xyz_n'}}
        identity = (item['source_sha256'], item['native_station_geometry'],
                    item['physical_angle_screw_geometry'], common_parameters)
        if reference is not None and identity != reference:
            raise ValueError('Mixed source snapshots, station inventories or model parameters')
        reference = identity
        cases[case] = item
    if _consumer_hashes() != LOADED_CONSUMER_HASHES:
        raise ValueError('Consumer sources changed during audit')
    return {
        'candidate': CANDIDATE, 'status': 'AUDITED_ANGLE_DEMAND_LEDGER_ONLY',
        'consumer_source_sha256': dict(LOADED_CONSUMER_HASHES),
        'case_order': list(CASES), 'case_count': len(cases),
        'station_case_records': 144, 'flange_case_records': 288,
        'construction_release': False, 'connection_resistance_established': False,
        'limits': [
            'Native numerical flags and declared hashes are checked; native solves are not replayed.',
            'Manifest coverage is not independently established; only declared artifact bytes are checked.',
            'Flange forces/moments are independently reconstructed and matched to supplied assessments.',
            'Supplied directional projections/ratios are labelled as reported; rating applicability is not rederived.',
            'Unknown separation and moment capacities remain null, not zero or infinity.',
            'No panel-screw/SPAX reference, floor-friction qualification or climber rating is introduced.',
        ],
        'cases': cases,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', action='append', nargs=3, required=True,
        metavar=('NAME', 'NATIVE_DIRECTORY', 'ASSESSMENT_JSON'))
    parser.add_argument('--current-source-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    entries = [(name, Path(native), Path(assessment)) for name, native, assessment in args.case]
    result = build_ledger(entries, current_source_root=args.current_source_root)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in
        ('status', 'case_count', 'station_case_records', 'construction_release')}))


def _consumer_hashes():
    folder = Path(__file__).resolve().parent
    return {'scripts/'+name: digest(folder/name) for name in
            ('floor_flush_angle_ledger.py', 'clear_space_case_contract.py')}


LOADED_CONSUMER_HASHES = _consumer_hashes()


if __name__ == '__main__':
    main()
