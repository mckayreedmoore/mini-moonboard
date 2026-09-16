"""Build read-only commercial-angle demand ledger from selected case archives.

No CAD construction or native solve occurs.  The existing ML24Z force evaluator
is applied to authenticated archived reports; unresolved resistance stays open.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from fea.current_response_resistance import angle_comparisons
from scripts.current_candidate import CANONICAL_CASES

ROOT = Path(__file__).resolve().parents[1]
CONNECTIONS_PER_CASE = 24
SCREWS_PER_CONNECTION = 6


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def maximum(rows, field, *, positive=False):
    eligible = [row for row in rows if row[field] is not None
                and (not positive or row[field] > 0)]
    if not eligible:
        return None
    winner = max(eligible, key=lambda row: row[field])
    return {key: winner[key] for key in ('case', 'station', field)}


def build(root=ROOT):
    root = Path(root)
    selection_path = root / 'current-candidate.json'
    selection = json.loads(selection_path.read_text())
    if set(selection.get('recorded_assessments', ())) != set(CANONICAL_CASES):
        raise ValueError('Require exactly six canonical selected cases')

    cases = {}
    envelope_rows = []
    for case in CANONICAL_CASES:
        archive = (root / selection['recorded_assessments'][case]).parent
        manifest_path = archive / 'manifest.json'
        report_path = archive / 'report.json.gz'
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('candidate') != selection['candidate']:
            raise ValueError('Archive candidate differs: ' + case)
        if digest(report_path) != manifest.get('files', {}).get('report.json.gz'):
            raise ValueError('Archived report hash differs: ' + case)
        raw = gzip.decompress(report_path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != manifest.get('native_report_sha256'):
            raise ValueError('Archived native report hash differs: ' + case)
        report = json.loads(raw)
        if report.get('candidate') != selection['candidate']:
            raise ValueError('Report candidate differs: ' + case)

        evaluated = angle_comparisons(
            report['physical_connection_forces'], report['angle_stations'])
        if len(evaluated) != CONNECTIONS_PER_CASE:
            raise ValueError('Require 24 ML24Z connections: ' + case)
        connections = {}
        rows = []
        for station, result in evaluated.items():
            loaded_flange = 'upright' if result['bearing_like'] else 'beam'
            wrench = result['flange_member_on_bracket_wrenches'][loaded_flange]
            couple = wrench['parallel_couple_nmm']
            row = {
                'case': case,
                'station': station,
                'rated_force_component_unity': result['rated_force_component_unity'],
                'unlisted_positive_F2_separation_n': result['unlisted_separation_demand_n'],
                'absolute_force_parallel_couple_nmm': abs(couple) if couple is not None else None,
            }
            rows.append(row)
            envelope_rows.append(row)
            connections[station] = {
                'product': 'Simpson Strong-Tie ML24Z',
                'fastener': 'Simpson SDS25112',
                'screw_count': SCREWS_PER_CONNECTION,
                'bearing_like': result['bearing_like'],
                'loaded_flange': loaded_flange,
                'projected_loaded_flange_force_n': result['projected_loaded_flange_force_n'],
                'rated_force_component_unity': result['rated_force_component_unity'],
                'unlisted_positive_F2_separation_n': result['unlisted_separation_demand_n'],
                'loaded_flange_force_xyz_n': wrench['force_xyz_n'],
                'loaded_flange_moment_xyz_nmm': wrench['moment_xyz_nmm'],
                'force_parallel_couple_nmm': couple,
                'independent_couple_resolved': result['independent_couple_resolved'],
            }
        cases[case] = {
            'archive': archive.relative_to(root).as_posix(),
            'manifest_sha256': digest(manifest_path),
            'report_json_gz_sha256': digest(report_path),
            'native_report_sha256': manifest['native_report_sha256'],
            'ML24Z_connection_count': len(connections),
            'SDS25112_screw_count': len(connections) * SCREWS_PER_CONNECTION,
            'positive_unlisted_F2_station_count': sum(
                row['unlisted_positive_F2_separation_n'] is not None
                and row['unlisted_positive_F2_separation_n'] > 0 for row in rows),
            'maxima': {
                'listed_force_component_interaction': maximum(rows, 'rated_force_component_unity'),
                'unlisted_positive_F2_separation': maximum(
                    rows, 'unlisted_positive_F2_separation_n', positive=True),
                'absolute_force_parallel_loaded_flange_couple': maximum(
                    rows, 'absolute_force_parallel_couple_nmm'),
            },
            'connections': connections,
        }

    return {
        'candidate': selection['candidate'],
        'derivation': 'Read-only evaluation of selected authenticated report archives with fea.current_response_resistance.angle_comparisons; no native solves.',
        'case_count': len(cases),
        'inventory_per_case': {
            'ML24Z_connections': CONNECTIONS_PER_CASE,
            'SDS25112_screws': CONNECTIONS_PER_CASE * SCREWS_PER_CONNECTION,
        },
        'inventory_across_six_case_records': {
            'ML24Z_connection_records': len(cases) * CONNECTIONS_PER_CASE,
            'SDS25112_screw_records': len(cases) * CONNECTIONS_PER_CASE * SCREWS_PER_CONNECTION,
        },
        'envelope_maxima': {
            'listed_force_component_interaction': maximum(
                envelope_rows, 'rated_force_component_unity'),
            'unlisted_positive_F2_separation': maximum(
                envelope_rows, 'unlisted_positive_F2_separation_n', positive=True),
            'absolute_force_parallel_loaded_flange_couple': maximum(
                envelope_rows, 'absolute_force_parallel_couple_nmm'),
        },
        'completion_gate': {
            'status': 'OPEN',
            'reason': 'Listed force-component interactions omit positive F2 separation at bearing-like installations, and no applicable complete-wrench resistance resolves loaded-flange couples.',
            'qualified_for_design': False,
        },
        'input_sha256': {
            'current-candidate.json': digest(selection_path),
            'fea/current_response_resistance.py': digest(
                root / 'fea/current_response_resistance.py'),
            'scripts/compact_spliced_flush_top_angle_ledger.py': digest(Path(__file__)),
        },
        'cases': cases,
        'qualified_for_design': False,
    }


def markdown(ledger):
    lines = [
        '# Selected flush-top commercial-angle ledger', '',
        f"Candidate: `{ledger['candidate']}`.", '',
        ('This deterministic ledger reads six authenticated report archives and applies '
         '`fea.current_response_resistance.angle_comparisons`. It runs no native solve and '
         'changes no archive.'), '',
        ('| Case | ML24Z | SDS25112 | Listed interaction max | Positive unlisted F2 max, N | '
         'Loaded-flange force-parallel couple max, N·m |'),
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for case, record in ledger['cases'].items():
        maxima = record['maxima']
        interaction = maxima['listed_force_component_interaction']
        separation = maxima['unlisted_positive_F2_separation']
        couple = maxima['absolute_force_parallel_loaded_flange_couple']
        lines.append(
            f"| `{case}` | {record['ML24Z_connection_count']} | "
            f"{record['SDS25112_screw_count']} | {interaction['rated_force_component_unity']:.6f} "
            f"(`{interaction['station']}`) | "
            f"{separation['unlisted_positive_F2_separation_n']:.3f} (`{separation['station']}`) | "
            f"{couple['absolute_force_parallel_couple_nmm']/1000:.3f} (`{couple['station']}`) |")
    maxima = ledger['envelope_maxima']
    lines.extend([
        '', '## Six-case envelope', '',
        (f"- Listed interaction maximum: **{maxima['listed_force_component_interaction']['rated_force_component_unity']:.6f}** at "
         f"`{maxima['listed_force_component_interaction']['case']}` / `{maxima['listed_force_component_interaction']['station']}`."),
        (f"- Positive unlisted F2 maximum: **{maxima['unlisted_positive_F2_separation']['unlisted_positive_F2_separation_n']:.3f} N** at "
         f"`{maxima['unlisted_positive_F2_separation']['case']}` / `{maxima['unlisted_positive_F2_separation']['station']}`."),
        (f"- Absolute loaded-flange force-parallel couple maximum: **{maxima['absolute_force_parallel_loaded_flange_couple']['absolute_force_parallel_couple_nmm']/1000:.3f} N·m** at "
         f"`{maxima['absolute_force_parallel_loaded_flange_couple']['case']}` / `{maxima['absolute_force_parallel_loaded_flange_couple']['station']}`."),
        '', '## Completion gate', '',
        ('**OPEN.** Listed interactions do not qualify positive F2 separation in bearing-like '
         'installations. They also do not supply an applicable complete-wrench resistance for '
         'loaded-flange couples. Ledger is demand evidence, not construction release or design qualification.'), '',
        ('The [online product/options review](compact-spliced-flush-top-angle-options.md) '
         'found no catalog-only larger ML angle or screw substitution that closes those '
         'actions. It records the smallest completion routes and a ready-to-send technical '
         'question.'), '',
        ('Full per-case, per-connection values and authenticated input hashes are in '
         '[compact-spliced-flush-top-angle-ledger.json](compact-spliced-flush-top-angle-ledger.json).'),
    ])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-output', type=Path, required=True)
    parser.add_argument('--markdown-output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.json_output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    args.markdown_output.write_text(markdown(result))


if __name__ == '__main__':
    main()
