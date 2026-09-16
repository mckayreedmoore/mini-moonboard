"""Check exterior tail trims using the six retained assembled force cases.

This is an explicitly fixed-response end-detail assessment, not a new native
solve. Retain original member stability/net checks only where the connected
full-section load path is unchanged; report removed tail weight separately.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import assess, hardware_assumptions
from fea.wider_leg_wood_checks import shear_band_ends
from mini_moonboard import compact_spliced_trimmed as model
from scripts.compact_splice_results import PREFIXES, local_groups
from scripts.compact_thick_geometry import build

ROOT = Path.cwd()
ARCHIVES = Path('fea/results/compact-splice-study')
OUT = Path('docs/compact-spliced-construction/end-trim-check.json')


def check():
    cache = Path('fea/generated/current-end-trim-geometry.json')
    dependencies = [Path(model.__file__),Path(model.installed.__file__),Path(model.installed.structural.__file__)]
    hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}
    saved = json.loads(cache.read_text()) if cache.exists() else {}
    if saved.get('trim_dependency_sha256') == hashes:
        geometry = saved['geometry']
    else:
        geometry = build(model)
        cache.write_text(json.dumps({'trim_dependency_sha256':hashes,'geometry':geometry}))
    assert geometry['receiver_fit_pass']
    original = {p.name:p for p in model.installed.uncut_wood_parts()}
    current = {p.name:p for p in model.uncut_wood_parts()}
    tails = {}
    for name,plane in model.trim_planes().items():
        removed = original[name].shape.cut(current[name].shape)
        grain = model.MEMBER_AXES[name][0]
        stations = [model.bolt_interface_point(c).dot(grain)+sign*model.bolt_dimensions(c)['hole_diameter_mm']/2
                    for c in model.connections() if c.kind == 'bolt' and name in c.members for sign in (-1,1)]
        cut_stations = [v.Center().dot(grain) for v in removed.Vertices()]
        before = max(cut_stations) < min(stations)
        gap = min(stations)-max(cut_stations) if before else min(cut_stations)-max(stations)
        assert gap > 0, 'Trim reaches connected full-section span: '+name
        tails[name] = {**plane,'removed_volume_mm3':removed.Volume(),
            'removed_mass_kg_at_600kg_m3':removed.Volume()*6.e-7,
            'full_section_gap_beyond_outer_bolt_bores_mm':gap}
    reference = json.loads((ARCHIVES/'a12-rear/geometry.json').read_text())
    geometry['hardware_by_name'] = reference['hardware_by_name']
    hardware = {}
    for name,row in geometry['geometries_by_bolt_name'].items():
        row['bending_yield_psi'] = reference['geometries_by_bolt_name'][name]['bending_yield_psi']
        bound = reference['hardware_resistance_bounds_by_name'][name]
        hardware[name] = hardware_assumptions(row['diameter_mm'],washer_od_mm=bound['washer_od_mm'],
            hole_diameter_mm=bound['washer_hole_diameter_mm'],washer_thickness_mm=bound['washer_thickness_mm'])
    cases = {}
    for folder in sorted(ARCHIVES.iterdir()):
        manifest = json.loads((folder/'manifest.json').read_text())
        for name,digest in manifest['files'].items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest
        previous = json.loads((folder/'splice-checks.json').read_text())
        assert all(previous['criteria'].values())
        report = json.loads(gzip.decompress((folder/'report.json.gz').read_bytes()))
        rows = {name:row for name,row in report['physical_connection_forces'].items() if name.startswith(PREFIXES)}
        stage = assess(report,geometry['geometries_by_bolt_name'],hardware,bolt_prefixes=PREFIXES)
        actual = {name:compare_bolt(row,geometry['geometries_by_bolt_name'][name]) for name,row in rows.items()}
        groups = local_groups(rows,geometry,actual)
        for key,group in list(groups.items()):
            bounded = copy.deepcopy(geometry)
            band_records = {}
            for name in group['members']:
                if name not in tails:
                    continue
                member = bounded['members'][name]
                grain = np.asarray(member['grain'])
                normal = np.array([0.,grain[2],-grain[1]])
                qs = [float(np.dot(np.asarray(rows[n]['point'])-member['centre_mm'],normal))
                      for n in group['bolt_names']]
                radius = max(geometry['hardware_by_name'][n]['hole_diameter_mm']/2 for n in group['bolt_names'])
                ends = shear_band_ends(member['profile_sq_mm'],min(qs)-radius,max(qs)+radius)
                member['end_stations_mm'] = ends
                band_records[name] = {'q_band_mm':[min(qs)-radius,max(qs)+radius],
                                      'conservative_end_stations_mm':ends}
            if band_records:
                groups[key] = local_groups(rows,bounded,actual)[key]
                groups[key]['actual_shear_band_bounds'] = band_records
        local = [r for group in groups.values() for r in group['member_checks'].values()]
        metrics = {**stage['metrics'],
            'actual_angle_lateral':max(r['comparisons']['actual_angle']['ratio_CD_1'] for r in actual.values()),
            'local_parallel':max(r['wood']['parallel_peak_ratio'] for r in local),
            'supplemental_splitting':max(r['wood']['splitting_peak_ratio'] for r in local),
            'group_spacing_margin_mm':min(r['layout']['minimum_component_spacing_margin_mm'] for r in local)}
        passed = (metrics['minimum_directional_edge_end_margin_mm'] >= 0
            and metrics['group_spacing_margin_mm'] >= 0
            and all(metrics[k] <= 1 for k in ('actual_angle_lateral','local_parallel',
                'supplemental_splitting','steel_direct','washer_bearing','washer_bending')))
        cases[folder.name] = {'passes_updated_end_and_hardware_checks':passed,'metrics':metrics,
            'native_report_sha256':manifest['native_report_sha256'],
            'local_groups':groups,
            'retained_checks_sha256':hashlib.sha256((folder/'splice-checks.json').read_bytes()).hexdigest()}
        assert passed, (folder.name,metrics)
    sources = [Path(__file__),Path(model.__file__),Path(model.installed.__file__),
               Path(model.installed.structural.__file__)]
    return {'candidate':model.KEY,'status':'END_DETAIL_CHECKS_PASS_WITH_RETAINED_RESPONSE',
        'receiver_fit':geometry['receiver_fit'],'trims':tails,'cases':cases,
        'removed_wood_mass_kg_at_600kg_m3':sum(r['removed_mass_kg_at_600kg_m3'] for r in tails.values()),
        'source_sha256':{str(p.resolve().relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'assumption':'Original native stiffness and gravity placement retained for six small exterior tail cuts; all cuts lie beyond every bolt bore station and preserve the connected full-section span. This is an explicit unloaded-tail stiffness approximation, not an identical native mesh or a new assembled solve. Prior sampled connected-section/stability checks retained; current end distances/local connection resistance and actual washer seats rechecked.'}


if __name__ == '__main__':
    result = check()
    OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'], 'removed wood kg',result['removed_wood_mass_kg_at_600kg_m3'])
    print({name:row['metrics']['minimum_directional_edge_end_margin_mm'] for name,row in result['cases'].items()})
