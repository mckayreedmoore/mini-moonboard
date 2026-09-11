"""Summarize saved floor and harness limits without CAD or new contact solves."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

FLOOR = Path('fea/results/round-service-floor-v1.json.gz')
WIRING = Path('exports/round-bore-service-development/wiring.json')
REFERENCE = Path('docs/round-service-wiring-reference.json')


def necessary_friction(horizontal_n, normal_n):
    """Resultant force bound only; yaw, contact and dynamics remain unresolved."""
    if not all(math.isfinite(v) for v in (horizontal_n, normal_n)) or horizontal_n < 0 or normal_n <= 0:
        raise ValueError('Require finite nonnegative horizontal force and positive normal force')
    return horizontal_n / normal_n


def bind_candidate(floor, wiring, wiring_path, manifest):
    """Require candidate identity and authenticate the otherwise unlabelled routing."""
    candidate = floor.get('candidate')
    if not candidate or manifest.get('candidate') != candidate or wiring.get('candidate', candidate) != candidate:
        raise ValueError('Floor and wiring manifest candidates differ')
    expected = manifest.get('artifact_sha256', {}).get(wiring_path.name)
    if expected != hashlib.sha256(wiring_path.read_bytes()).hexdigest():
        raise ValueError('Wiring differs from candidate manifest')
    if len(wiring.get('round_bores', [])) != 32 or len(wiring.get('segments', [])) != 131:
        raise ValueError('Expected 32 round passages and 131 links')
    return candidate


def build(floor_path=FLOOR, wiring_path=WIRING):
    from fea.split_center_floor import necessary_conditions

    floor_path, wiring_path = Path(floor_path), Path(wiring_path)
    manifest_path = wiring_path.with_name('manifest.json')
    floor = json.loads(gzip.decompress(floor_path.read_bytes()))
    wiring = json.loads(wiring_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    candidate = bind_candidate(floor, wiring, wiring_path, manifest)
    reference = json.loads(REFERENCE.read_text())
    reference_digest = hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
    if any(report.get('source_sha256', {}).get(str(REFERENCE)) != reference_digest for report in (floor, manifest)):
        raise ValueError('Harness measurement reference differs from evidence sources')
    rows = []
    for case in floor['cases']:
        conditions = necessary_conditions(floor['floor_vertices_mm'], case['wrench_n_nmm'], .2)
        rows.append((necessary_friction(conditions['horizontal_force_n'],
                                       conditions['required_total_normal_n']), case, conditions))
    required, governing, _ = max(rows, key=lambda row: row[0])
    longest = max(wiring['segments'], key=lambda row: row['routed_length_mm'])
    diameter = reference['user_measurements']['maximum_harness_outside_diameter_mm']
    return {
        'candidate': candidate,
        'artifact_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (floor_path, wiring_path, manifest_path, REFERENCE, Path(__file__),
                                      Path('fea/split_center_floor.py'), Path('fea/user_load_envelope.py'))},
        'basis': 'Saved artifact identities bound by export manifest and measurement-reference hashes; force/hull bounds recomputed from raw wrenches. This summary does not revalidate complete source closures or solve changed geometry.',
        'floor': {
            'mass_kg': floor['state']['mass_kg'],
            'minimum_sampled_mass_kg': floor['state']['mass_kg'] * min(c['mass_fraction'] for c in floor['cases']),
            'necessary_resultant_friction_maximum': required,
            'governing_force_bound_case': {k: v for k, v in governing.items() if k != 'friction_results'},
            'minimum_sampled_resultant_hull_margin_mm': min(min(c['inward_edge_distances_mm']) for _, _, c in rows),
            'saved_friction_summary': floor['summary'],
            'friction_or_contact_measured': False,
        },
        'harness': {
            'segments': len(wiring['segments']), 'passages': len(wiring['round_bores']),
            'longest_segment': longest,
            'minimum_nominal_radial_passage_gap_mm': min((b['diameter_mm'] - diameter)/2 for b in wiring['round_bores']),
            'maximum_timber_traverse_mm': max(b['member_exit_mm'] - b['member_entry_mm'] for b in wiring['round_bores']),
            'shortest_pitch_reported_as_approximate_mm': reference['user_measurements']['approximate_bulb_base_pitch_mm'],
            'physical_feed_or_removal_trial_performed': False,
        },
        'qualified_for_design': False, 'qualified_for_installation': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--floor', type=Path, default=FLOOR)
    parser.add_argument('--wiring', type=Path, default=WIRING)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    payload = json.dumps(build(args.floor, args.wiring), indent=2, allow_nan=False)+'\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(payload)
    else:
        print(payload, end='')
