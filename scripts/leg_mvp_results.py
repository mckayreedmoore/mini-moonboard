"""Recompute the bounded MVP study from its archived, authenticated reports."""
import gzip
import hashlib
import json
from pathlib import Path

from fea.current_leg_mvp_checks import assess, bolt_check
from fea.current_response_resistance import VALIDITY, bolt_comparison
from fea.leg_mvp_sole_checks import assess as sole_assess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT/'fea/results/leg-mvp-study'


def main():
    manifest = json.loads((DIRECTORY/'manifest.json').read_text())
    reports, summary = {}, {}
    for label, record in manifest['cases'].items():
        compressed = (DIRECTORY/record['compressed_report']).read_bytes()
        if hashlib.sha256(compressed).hexdigest() != record['compressed_report_sha256']:
            raise ValueError('Compressed report hash mismatch: '+label)
        data = gzip.decompress(compressed)
        if hashlib.sha256(data).hexdigest() != record['native_report_sha256']:
            raise ValueError('Native report hash mismatch: '+label)
        report = reports[label] = json.loads(data)
        if not all(report.get(key) is True for key in VALIDITY):
            raise ValueError('Invalid response: '+label)
        members = {n: d['member'] for n, d in report['member_section_demands'].items()}
        forces = {n: row for n, row in report['physical_connection_forces'].items()
                  if n.startswith('lumber_leg_bolt_')}
        if label == 'baseline-foot3':
            comparisons = {n: bolt_comparison(row, members) for n, row in forces.items()}
            ratios = {n: row['conditional_nominal_diameter_ratio'] for n, row in comparisons.items()}
        else:
            geometry = {n: {'grain': m['axis'], 'width_mm': min(m['width_mm'], m['depth_mm'])}
                        for n, m in members.items()}
            comparisons = {n: bolt_check(row, geometry) for n, row in forces.items()}
            ratios = {n: row['lateral_ratio'] for n, row in comparisons.items()}
        governing = max(ratios, key=ratios.get)
        summary[label] = {'candidate': report['candidate'], 'numerically_accepted': True,
                          'governing_bolt': governing, 'lateral_ratio': ratios[governing],
                          'lateral_demand_n': comparisons[governing]['lateral_demand_n'],
                          'qualified_for_design': False}
    sole = reports['relieved-sole-nine-bolt']
    geometry = json.loads((DIRECTORY/'sole-geometry.json').read_text())
    contact = json.loads((DIRECTORY/'sole-contact-geometry.json').read_text())
    outputs = {'summary.json': summary, 'sole-resistance.json': assess(sole, geometry),
               'sole-contact.json': sole_assess(sole, contact)}
    for name, result in outputs.items():
        (DIRECTORY/name).write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
