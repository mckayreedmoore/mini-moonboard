"""Publish compact, auditable current response and resistance comparisons.

Native solver files stay in the generated evidence directories. This report
reassesses their printed output with the current coordinate and precision audit;
it never transfers an older candidate's forces to the current geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fea.current_response_resistance import assess as resistance
from fea.current_response_run import assess as response
from fea.reinforced_frame_demand import repository_source_closure


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def case(directory):
    directory = Path(directory)
    original = json.loads((directory/'report.json').read_text())
    if original['candidate'] != 'no-shoes-development':
        raise ValueError('Wrong candidate')
    for path, expected in original['artifact_sha256'].items():
        if digest(directory/path) != expected:
            raise ValueError('Native evidence changed: '+str(directory/path))
    final = directory/original['contact_cycles'][-1]['directory']
    record = json.loads((final/'input.json').read_text())
    result = response(record,(final/'frame.dat').read_text(),(final/'frame.frd').read_text(),(final/'frame.12d').read_text())
    result.update(candidate=original['candidate'],angle_stations=record['angle_stations'],
        contact_active_set_converged=original['contact_active_set_converged'])
    result['numerically_accepted'] = all(result[k] for k in ('contact_active_set_converged',
        'global_equilibrium_passed','member_equilibrium_passed','mpc_check_passed'))
    checks = resistance(result)
    members = {}
    for name,row in checks['members'].items():
        sections = result['member_section_demands'][name]['sections']
        members[name] = {k:row[k] for k in ('width_mm','depth_mm','gross_length_mm','section_valid_from_mm',
            'gross_section_peak','full_length_unbraced_peak','full_length_unbraced_sensitivity_failed','limits')}
        members[name]['maximum_absolute_actions'] = {key:max(abs(s[key]) for s in sections)
            for key in ('axial_n_tension_positive','shear_u_n','shear_v_n','moment_u_nmm','moment_v_nmm','torsion_nmm')}
    feet = {}
    for row in result['physical_connection_forces'].values():
        if row['second'] != 'floor':
            continue
        foot = feet.setdefault(row['first'],{'force_xyz_n':np.zeros(3),'moment_about_origin_nmm':np.zeros(3)})
        force = np.asarray(row['force_on_first_xyz_n'])
        foot['force_xyz_n'] += force
        foot['moment_about_origin_nmm'] += np.cross(row['point'],force)
    return {
        'name':directory.name, 'native_directory':str(directory),
        'load':{k:record[k] for k in ('hold','pounds','force_xyz_n','moment_at_panel_midplane_nmm',
            'target_xyz_mm','standoff_from_front_mm','equipment_kg','panel_patch_size_mm')},
        'model':{k:record[k] for k in ('materials','stiffnesses','frame_size_mm','panel_size_mm','modeled_mass_kg')},
        'inventory':{'timber_members':len(record['members']),'panels':len(record['panel_nodes']),
            'nodes':len(record['nodes']),'elements':len(record['elements']),**checks['connection_counts']},
        'numerically_accepted':result['numerically_accepted'],
        'numerical_audits':{k:result[k] for k in ('force_residual_n','moment_residual_nmm',
            'global_equilibrium_passed','member_equilibrium_passed','member_equilibrium',
            'mpc_printed_precision_audit','contact_active_set_converged','closed_bearing_assumption_passed')},
        'contact_cycles':len(original['contact_cycles']),
        'displacement_mm':{'timber':result['maximum_timber_displacement_mm'],
            'panel_midsurface':result['maximum_panel_displacement_mm']},
        'members':members,'leg_bolts':checks['leg_bolts'],'panel_screws':checks['panel_screws'],
        'angles':checks['ML24Z'],
        'mechanical_connection_forces':{name:row for name,row in result['physical_connection_forces'].items() if 'axis' in row},
        'floor_resultants':{name:{key:value.tolist() for key,value in row.items()} for name,row in feet.items()},
        'native_producer_source_sha256':original['source_sha256'],
        'native_final_artifact_sha256':{str(path.relative_to(directory)):digest(path)
            for path in final.iterdir() if path.name in ('frame.inp','frame.dat','frame.frd','frame.log','input.json')},
        'qualified_for_design':False,
    }


def build(directories, output, coupon=None, native_evidence=None, equivalence=None):
    rows = [case(path) for path in directories]
    geometry = {k:v for k,v in rows[0]['native_producer_source_sha256'].items() if k.startswith('mini_moonboard/')}
    if any({k:v for k,v in row['native_producer_source_sha256'].items() if k.startswith('mini_moonboard/')} != geometry for row in rows):
        raise ValueError('Do not combine different CAD source identities without an explicit equivalence check')
    source_paths = repository_source_closure([Path(__file__), *Path('fea').glob('current_response_*.py')])
    source_paths += [Path('docs/reinforced-fastener-applicability.json'),
        Path('docs/round-panel-countersink-reference.json'),
        Path('fea/results/round-structural-audit-v1.json')]
    report = {'analyzed_geometry_source_sha256':geometry,
        'workspace_geometry_sources_match':all(digest(k)==v for k,v in geometry.items()),
        'geometry_scope':'Pinned published 277 mm shoe-free candidate; a subsequent source refactor requires an explicit geometry equivalence check',
        'candidate':'no-shoes-development',
        'scope':'Selected assembled-frame load cases and explicit stiffness sensitivities; not an exhaustive internal-force envelope over all holds or climbing actions',
        'cases':rows,'all_cases_numerically_accepted':all(row['numerically_accepted'] for row in rows),
        'sources_sha256':{str(path.resolve().relative_to(Path.cwd())):digest(path) for path in source_paths},
        'qualified_for_design':False}
    if equivalence:
        witness = json.loads(Path(equivalence).read_text())
        if not witness['identical_native_input'] or witness['analyzed_native_deck_sha256'] != witness['refactored_native_deck_sha256']:
            raise ValueError('Dependency-refactor equivalence witness does not establish matching native input')
        report['dependency_refactor_equivalence'] = {'path':str(equivalence),'sha256':digest(equivalence), **witness}
    if native_evidence:
        report['native_evidence'] = {'path':str(native_evidence),'sha256':digest(native_evidence),
            'scope':'Final refined A12/150 case with producer source snapshots, plus four native panel coupons'}
    if coupon:
        report['native_panel_coupon'] = json.loads(Path(coupon).read_text())
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--coupon',type=Path)
    parser.add_argument('--native-evidence',type=Path)
    parser.add_argument('--equivalence',type=Path)
    parser.add_argument('directories',nargs='+',type=Path)
    args = parser.parse_args()
    build(args.directories,args.output,args.coupon,args.native_evidence,args.equivalence)
