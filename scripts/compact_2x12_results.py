"""Assess a fresh unbraced 2x12 leg case with actual geometry and force records."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import assess, hardware_assumptions
from fea.compact_thick_checks import assess_local, layout_check
from fea.current_response_resistance import member_comparisons
from scripts.compact_thick_results import base_comparisons


def check(report, geometry):
    assert report['candidate'] == geometry['candidate']
    assert report['numerically_accepted']
    for name,sha in geometry['source_sha256'].items():
        if name.startswith('mini_moonboard/'):
            assert report['source_sha256'].get(name) == sha
    hardware = {name:hardware_assumptions(row['diameter_mm'],washer_od_mm=1.368*25.4,
        hole_diameter_mm=.577*25.4,washer_thickness_mm=.086*25.4)
        for name,row in geometry['geometries_by_bolt_name'].items()}
    result = assess(report,geometry['geometries_by_bolt_name'],hardware,bolt_prefixes=('lumber_leg_bolt_',))
    rows = {n:r for n,r in report['physical_connection_forces'].items() if n.startswith('lumber_leg_bolt_')}
    actual = {n:compare_bolt(row,geometry['geometries_by_bolt_name'][n]) for n,row in rows.items()}
    layouts = {name:layout_check([r['point'] for r in rows.values() if name in (r['first'],r['second'])],member,12.7)
               for name,member in geometry['members'].items()}
    local = assess_local(report,geometry['members'],hole_diameter_mm=14.2875)
    gross = member_comparisons(report)
    base = base_comparisons(report,geometry)
    metrics = {**result['metrics'],
        'actual_angle_lateral':max(r['comparisons']['actual_angle']['ratio_CD_1'] for r in actual.values()),
        'local_parallel':max(r['joint_wood']['parallel_peak_ratio'] for r in local['local_members'].values()),
        'supplemental_splitting':max(r['joint_wood']['splitting_peak_ratio'] for r in local['local_members'].values()),
        'net_member':max(r['sampled_net_peak']['comparison']['conservative_net_section_envelope_ratio'] for r in local['local_members'].values()),
        'header_full_length':gross['base_header']['full_length_unbraced_peak']['full_length_unbraced_ratio'],
        'base_bearing':max(r['average_header_bearing_ratio'] for r in base.values()),
        'base_quarter_area':max(r['quarter_area_corner_sensitivity_ratio'] for r in base.values()),
        'base_notch':max(r['conservative_notched_shear_ratio'] for r in base.values())}
    criteria = {k:metrics[k]<=1 for k in ('actual_angle_lateral','steel_direct','washer_bearing','washer_bending',
        'local_parallel','supplemental_splitting','net_member','header_full_length','base_bearing','base_quarter_area','base_notch')}
    criteria.update(receiver_fit=geometry['receiver_fit_pass'],end_edges=metrics['minimum_directional_edge_end_margin_mm']>=0,
        layout=all(r['component_spacing_screen_passed'] for r in layouts.values()),
        sampled_member_stability=all(not r['sampled_full_length_unbraced_sensitivity_failed'] for r in local['local_members'].values()),
        all_machining_represented=all(r['all_openings_represented'] for r in local['local_members'].values()))
    return {'candidate':report['candidate'],'status':'LISTED_CHECKS_PASS' if all(criteria.values()) else 'DESIGN_SHORTFALL',
        'criteria':criteria,'metrics':metrics,'actual_bolts':actual,'layouts':layouts,'local':local,'gross':gross,
        'base':base,'stage_one':result,'qualified_for_design':False,
        'scope':'Fresh unbraced assembled response; 90ksi specified Grade5 bolt yield, Cd1, catalog-minimum washer dimensions. Geometry/hardware conditions and complete sampled-member stability remain explicit.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((args.archive/'manifest.json').read_text())
    for name,sha in manifest['files'].items():
        assert hashlib.sha256((args.archive/name).read_bytes()).hexdigest()==sha
    report=json.loads(gzip.decompress((args.archive/'report.json.gz').read_bytes()))
    result=check(report,json.loads((args.archive/'geometry.json').read_text()))
    (args.archive/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['metrics'])
    print('Failed criteria:',[k for k,v in result['criteria'].items() if not v])
