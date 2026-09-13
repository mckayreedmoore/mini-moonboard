"""Recompute archived thick-pivot comparisons without CAD or a native solve."""
import gzip
import hashlib
import json
from pathlib import Path

from fea.thick_leg_checks import assess, assess_local

DIRECTORY = Path(__file__).resolve().parents[1]/'fea/results/thick-leg-study'


def main():
    manifest = json.loads((DIRECTORY/'manifest.json').read_text())
    summary = {}
    for label, record in manifest['cases'].items():
        compressed = (DIRECTORY/record['compressed_report']).read_bytes()
        if hashlib.sha256(compressed).hexdigest() != record['compressed_report_sha256']:
            raise ValueError('Compressed report changed: '+label)
        raw = gzip.decompress(compressed)
        if hashlib.sha256(raw).hexdigest() != record['native_report_sha256']:
            raise ValueError('Native report changed: '+label)
        report = json.loads(raw)
        geometry = json.loads((DIRECTORY/record['geometry']).read_text())
        if geometry['candidate'] != report['candidate']:
            raise ValueError('Geometry and native candidate differ: '+label)
        bolt = assess(report,geometry['geometries_by_bolt_name'],geometry['hardware'])
        if 'bolts' not in bolt:
            raise ValueError('Native numerical gates failed: '+label)
        result = {'bolt':bolt}
        members = {n:v for row in geometry['geometries_by_bolt_name'].values()
                   for n,v in row['members'].items()}
        if label.startswith('centered-'):
            diameter = next(iter(bolt['bolts'].values()))['diameter_mm']
            result['local'] = assess_local(report,members,hole_diameter_mm=diameter+1.5875)
        row = {'candidate':report['candidate'],'numerically_accepted':report['numerically_accepted'],
               'lateral_ratio':max(b['lateral_ratio'] for b in bolt['bolts'].values()),
               'minimum_directional_edge_end_margin_mm':min(m['minimum_margin_mm'] for b in bolt['bolts'].values() for m in b['placement'].values()),
               'receiver_fit_pass':geometry['receiver_fit_pass'],
               'modeled_mass_kg':record['modeled_mass_kg'],
               'panel_displacement_mm':report['maximum_panel_displacement_mm'],
               'timber_displacement_mm':report['maximum_timber_displacement_mm'],
               'physical_pivot_behavior_established':False,'qualified_for_design':False}
        if 'local' in result:
            row['sampled_net_member_ratios'] = {n:d['sampled_net_peak']['comparison']['conservative_net_section_envelope_ratio'] for n,d in result['local']['local_members'].items()}
            row['header_gross_ratio'] = result['local']['header_gross']['base_header']['gross_section_peak']['necessary_gross_section_ratio']
        summary[label] = row
        (DIRECTORY/(label+'-checks.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (DIRECTORY/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
