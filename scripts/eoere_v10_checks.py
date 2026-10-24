"""Strict own-field intake and public v10 reference summary assembly.

This publisher does not calculate resistance. It refuses to publish a numerical
summary unless all required changed-candidate worksheet families are supplied.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scripts.eoere_paired_frame_basis import CASES, ROOT, ref, sha
from scripts.eoere_v10_analysis import require

LOAD_CONTRACT = dict(weight_lb=250, downward_multiplier=2, horizontal_force_N=300,
                     accessory_mass_kg=25, duration_factor_CD=1)
REQUIRED_CRITERIA = frozenset((
    "wood_bearing_whole_affine", "reduced_connection_axial_bending",
    "direct_elastic_steel", "timber_net_shear_torsion",
    "timber_normal_and_stability", "cleat_actual_perimeter_rows",
))
UNRESOLVED = [
    "Complete oblique end/edge/group applicability and local splitting",
    "Compatible three-dimensional loaded-hole and fitting stress behavior",
    "Actual Hillman screw force-slip, combined resistance and panel head/edge duties",
    "Physical adhesive bond and actual plywood assembly properties",
    "No-slip floor support, finite-motion/contact and delivered hardware assumptions",
]


def load_bound(record):
    path=(ROOT/record['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), "repository bound file required")
    require(sha(path)==record['sha256'], "bound file changed: "+record['path'])
    return json.loads(path.read_bytes())


def intake_case(case, field, replay, plywood, field_ref, analysis_ref, material_ref, inventory):
    require(field['case_id']==case and replay['field']==plywood['field']==field_ref,
            "matching case and both independent replay field bindings required")
    require(field['trial_parent_geometry']==analysis_ref,
            "field belongs to a different analytical geometry")
    require(field['source_inputs']['plywood_material']==material_ref,
            "field plywood operator differs")
    require(field['response']['converged'] is True and replay['same_state_declared_fixed_floor_replayed'] is True
            and replay['all_credited_hosts_in_bearing'] is True and replay['false_screw_and_floor_forces_rejected'] is True,
            "own case and raw-force controls must be admitted")
    require(replay['equilibrium']['gradient_inf_n']<1e-5,
            "unchanged force residual tolerance exceeded")
    require(replay['equilibrium']['physical_body_count']==field['counts']['physical_bodies']==inventory['bodies'],
            "own physical body count differs")
    require(field['counts']['shaft']==inventory['shafts'] and field['counts']['fitting']==inventory['fittings'],
            "own shaft/fitting count differs")
    require(len(plywood['raw_operator_checks'])==2, "both analytical plywood operator audits required")
    require(len(field['panel_screw_actions'])==66, "exact purchased 66-screw policy required")
    load=field['source_inputs']['scenario']['climber_load_parameters']
    require(load['input_weight']==250 and load['input_unit']=='lb' and load['downward_multiplier']==2
            and load['horizontal_force_n']==300 and load['self_weight_and_accessory_loads_unchanged'] is True,
            "unchanged owner load contract required")
    accessories=[r for r in field['source_inputs']['case']['loads'] if r['id'].startswith('accessory/')]
    require(len(accessories)==2 and math.isclose(sum(-r['force_xyz_n'][2] for r in accessories),25*9.80665,rel_tol=0,abs_tol=1e-9)
            and all(r['force_xyz_n'][:2]==[0,0] for r in accessories),
            "actual 25kg accessory load entries required")
    require(not any(field['release'].values()), "false physical release flags required")


def build_response_bank(base, readiness):
    base=Path(base).resolve()
    records=[]
    for case in CASES:
        folder=base/'four-hosts'/case
        paths={k:folder/name for k,name in (
            ('field','field.json'),('independent_replay','independent-replay.json'),
            ('independent_plywood_replay','independent-replay-plywood.json'))}
        require(all(p.is_file() for p in paths.values()), "own six cases and both replays are incomplete: "+case)
        bound={key:ref(p) for key,p in paths.items()}
        field,replay,plywood=(load_bound(bound[k]) for k in ('field','independent_replay','independent_plywood_replay'))
        intake_case(case,field,replay,plywood,bound['field'],readiness['analysis_geometry'],
                    readiness['material'],readiness['analysis_inventory'])
        records.append(dict(case_id=case,**bound,both_independent_replays_admitted=True,
                            gradient_inf_N=replay['equilibrium']['gradient_inf_n']))
    return dict(schema='eoere_v10_own_response_bank/v1',producer=ref(Path(__file__)),
                geometry_revision=load_bound(readiness['receipt'])['revision'],
                physical_geometry=readiness['receipt'],analysis_geometry=readiness['analysis_geometry'],
                load_contract=LOAD_CONTRACT,case_ids=list(CASES),cases=records,
                maximum_gradient_inf_N=max(r['gradient_inf_N'] for r in records),
                all_six_cases_admitted=True,admission_gate_N=1e-5,
                historical_force_pass_transferred=False,physical_force_bounds_established=False,
                unresolved_qualifications=UNRESOLVED,structural_acceptance=False,
                fabrication_released=False,climbing_released=False)


def summarize_criteria(worksheets, field_bindings, analysis_ref):
    require(set(worksheets)==REQUIRED_CRITERIA, "all required changed-candidate criterion families required")
    maxima={}
    for name,record in worksheets.items():
        data=load_bound(record)
        require(data['analysis_geometry']==analysis_ref and data['field_bindings']==field_bindings,
                "worksheet must use the exact changed candidate and simultaneous six fields: "+name)
        require(data['load_contract']==LOAD_CONTRACT and data['case_ids']==list(CASES),
                "worksheet load/case intake differs")
        maximum=data['maximum']
        require(isinstance(maximum['index'],(int,float)) and 0<=maximum['index']<float('inf'),
                "finite nonnegative declared reference required")
        require(maximum['case_id'] in CASES and maximum.get('component'), "traceable governing component required")
        maxima[name]={**maximum,'worksheet':record,'above_reference':maximum['index']>1}
    return maxima


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=('response-bank','reference-summary'))
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--worksheets',type=Path)
    parser.add_argument('--response-bank',type=Path)
    args=parser.parse_args()
    ready=json.loads((args.base/'adapter-readiness.json').read_bytes())
    if args.kind=='response-bank':result=build_response_bank(args.base,ready)
    else:
        require(args.worksheets is not None and args.response_bank is not None,
                "response bank and every criterion family are required")
        bank=load_bound(ref(args.response_bank))
        bindings={r['case_id']:r['field'] for r in bank['cases']}
        maxima=summarize_criteria(json.loads(args.worksheets.read_bytes()),bindings,ready['analysis_geometry'])
        result=dict(schema='eoere_v10_reference_review/v1',producer=ref(Path(__file__)),
                    geometry_revision=bank['geometry_revision'],physical_geometry=ready['receipt'],
                    analysis_geometry=ready['analysis_geometry'],response_bank=ref(args.response_bank),
                    load_contract=LOAD_CONTRACT,case_ids=list(CASES),field_bindings=bindings,
                    numerical_reference_maxima=maxima,
                    all_declared_numerical_references_below_one=all(v['index']<=1 for v in maxima.values()),
                    unresolved_qualifications=UNRESOLVED,structural_acceptance=False,
                    fabrication_released=False,climbing_released=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False)


if __name__=='__main__':main()
