"""Recompute local timber and catalog-tolerance hardware checks for archived trials."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from fea.compact_assumption_checks import assess as angle_assess
from fea.compact_thick_checks import assess, hardware_assumptions
from scripts.compact_thick_results import base_comparisons, summary


def build(directory):
    geometry = json.loads((directory/'geometry.json').read_text())
    report = json.loads(gzip.decompress((directory/'report.json.gz').read_bytes()))
    candidate = report['candidate']
    if candidate != geometry['candidate'] or not candidate.startswith('compact-three-leg-'):
        raise ValueError('Require matching higher three-bolt candidate')
    for path, sha in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path) != sha:
            raise ValueError('CAD/native source mismatch: '+path)
    hardware = hardware_assumptions()
    # Catalog minimum OD/thickness and maximum bore, with the retained 33 ksi
    # washer-material reference explicitly treated as an analytical assumption.
    for washer in hardware['washers']:
        washer.update(outer_diameter_mm=1.368*25.4,
            hole_diameter_mm=.577*25.4, thickness_mm=.086*25.4)
    result = assess(report, geometry['geometries_by_bolt_name'], hardware, hole_diameter_mm=14.2875)
    if 'bolts' not in result:
        return result
    result['base'] = base_comparisons(report, geometry)
    result['actual_angle'] = angle_assess(report, geometry, expected_candidate=candidate)
    result['catalog_hardware_basis'] = {'document':'docs/compact-half-inch-hardware.md',
        'washer_minimum_od_in':1.368, 'washer_maximum_id_in':.577,
        'washer_minimum_thickness_in':.086, 'washer_yield_reference_psi':33000.,
        'scope':'Catalog dimensional lower bounds with retained assumed washer material; supplied conformity, thread transition and nut seating remain installation conditions.'}
    result['summary'] = summary(report, result)
    result['summary']['actual_angle_lateral_ratio_CD1'] = result['actual_angle']['governing']['actual_angle_CD_1']['ratio']
    result['summary']['catalog_washer_bending_peak'] = max(w['elastic_bending_ratio'] for b in result['bolts'].values() for w in b['hardware']['washers'])
    result['summary']['minimum_component_spacing_margin_mm'] = min(g['layout']['minimum_component_spacing_margin_mm'] for g in result['groups'].values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = build(args.directory)
    paths = [args.directory/'geometry.json', args.directory/'report.json.gz',
        Path(__file__), Path('fea/compact_thick_checks.py'), Path('fea/compact_assumption_checks.py'),
        Path('scripts/compact_thick_results.py'), Path('docs/compact-half-inch-hardware.md')]
    result['assessment_source_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (args.directory/'full-checks.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result.get('summary', result), indent=2))


if __name__ == '__main__':
    main()
