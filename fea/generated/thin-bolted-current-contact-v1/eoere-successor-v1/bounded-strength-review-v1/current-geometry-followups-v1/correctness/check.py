"""Read frozen JSON and perform bounded algebra; no CAD/native imports or runs."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import platform
from pathlib import Path
from types import SimpleNamespace
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'current-candidate.json').is_file())
DOC = ROOT / 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1'
HERE = Path(__file__).resolve().parent
pins = {}

def read(path, expected=None):
    path = ROOT / path
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected:
        assert digest == expected, str(path)
    pins[str(path.relative_to(ROOT))] = digest
    return json.loads(data)

def require(ok, message):
    if not ok:
        raise ValueError(message)

def extract(path, names, globals_):
    path = ROOT / path
    data = path.read_bytes()
    pins[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    tree = ast.parse(data)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in functions} == set(names)
    env = dict(globals_)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), env)
    return env

def near(actual, expected, atol=1e-8):
    assert np.allclose(actual, expected, rtol=1e-12, atol=atol), (actual, expected)

def main():
    packets = {}
    for name, result_sha in [('revised-base-audit-v1','1205472ce4f96626318b42f2ad7578396485d167932f22fc0af387b156c4f875'),
                            ('connected-stack-followup-v1','d81540a6c69b98f1182a6d2649d9a0d39126756ea94f0b3cd691026de7cb94d1')]:
        folder = DOC / name
        inputs = read(folder/'inputs.json')
        result = read(folder/'result.json', result_sha)
        verify = read(folder/'verification.json')
        for file in ['README.md','analyze.py']:
            data = (folder/file).read_bytes()
            pins[str((folder/file).relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
        for p, row in verify['owned_artifacts'].items():
            assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == row['sha256']
        detail = read(verify['raw_details']['path'], verify['raw_details']['sha256'])
        packets[name] = inputs, result, verify, detail
    ai, audit, av, ad = packets['revised-base-audit-v1']
    ci, connected, cv, cd = packets['connected-stack-followup-v1']
    refs = ai['references']
    base = read(refs['current_base']['path'], refs['current_base']['sha256'])
    original = read(refs['original_inputs']['path'], refs['original_inputs']['sha256'])
    previous = read(original['current_geometry']['path'], original['current_geometry']['sha256'])
    resistance = read(refs['previous_result']['path'], refs['previous_result']['sha256'])
    publication = read(refs['publication']['path'], refs['publication']['sha256'])
    prior_details = read(refs['prior_details']['path'], refs['prior_details']['sha256'])
    nominal = read(refs['nominal_heel_result']['path'], refs['nominal_heel_result']['sha256'])
    assert base['revision'] == 'eoere-midpoint-ready-frame-v3'
    assert base['unofficial_2026_grid_included'] is False and base['mechanics_ready'] is False
    assert audit['current_base'] == refs['current_base']
    assert connected['source_geometry_revision'] == audit['six_field_geometry_revision'] == 'eoere-bottom-rail-tnut-clearance-v1'
    assert connected['target_geometry_revision_not_evaluated'] == base['revision']
    for key in ['stock_depth_trimmed_engagement_parameter_sensitivity_range_n', 'loaded_bolt_plane_adjusted_net_tension_reference_range_n']:
        assert key in resistance['cleat_member_components']
    assert audit['reused_single_bolt_yield_components'] == resistance['bolt_yield_components']
    assert audit['reused_cleat_component_screens']['actual_all_mode_current_cleat_resistance_n'] is None
    assert audit['reused_cleat_component_screens']['current_geometry_response'] is False
    worst = audit['reused_single_bolt_yield_components']['worst_unadjusted_component_comparison']
    near(worst['V_over_unadjusted_component_Z'], worst['lateral_demand_n']/worst['unadjusted_component_Z_n'])
    near(worst['Cdelta0p5_Cg1_CD1_sensitivity_ratio'], 2*worst['V_over_unadjusted_component_Z'])
    assert audit['supplier_information']['old_nominal_heel_scenario']['worst'] == nominal['worst']
    assert audit['supplier_information']['old_nominal_heel_scenario']['reference_margin_percent'] == nominal['reference_margin_percent']
    assert audit['retained_old_panel_screw_exceedances'] == [dict(case_id=r['case_id'], **{k:v for k,v in r['component_metrics'].items() if k in ['generic_Hillman_head_CD1','panel_spatial_bending_CD1','panel_spatial_rolling_shear_CD1']}) for r in publication['cases']]
    helper_env = {'math':math, 'np':np, 'parent':SimpleNamespace(require=require), 'require':require}
    shift = extract('scripts/eoere_2026_adjustments.py', ['canonical_interval_shift'], helper_env)['canonical_interval_shift']
    audit_env = extract(DOC/'revised-base-audit-v1/analyze.py', ['delta_audit'], helper_env | {'canonical_interval_shift':shift})
    assert audit_env['delta_audit'](base, previous) == audit['geometry_delta']
    changed = {r['id'] for r in base['changed_finished_solids'] if r['kind']=='timber'}
    assert len(changed)==7 and not any(n.startswith('eoere_cleat') for n in changed)
    oldaxes={r['id']:r for r in previous['axes']}; newaxes={r['id']:r for r in base['axes']}
    seats=ad['washer_seat_rows']; oldseats={r['capture_id']:r for r in prior_details['washers']['seat_geometry']}
    assert len(seats)==112
    fresh=0
    for row in seats:
        prior=oldseats[row['capture_id']]
        assert prior['full_modeled_support'] and row['full_modeled_support']
        if row['host'] in changed:
            fresh+=1
            area=math.pi*(row['OD_mm']**2-row['support_inner_diameter_mm']**2)/4
            near(area*row['probe_depth_mm'], row['expected_probe_volume_mm3'])
            near(row['intersected_current_wood_volume_mm3']/row['expected_probe_volume_mm3'], row['support_fraction'])
            assert abs(row['intersected_current_wood_volume_mm3']-row['expected_probe_volume_mm3'])<=1e-4
            assert row['old_force_used_as_new_response'] is False
        else:
            near(np.asarray(newaxes[row['axis_id']]['point_xyz_mm'])-oldaxes[row['axis_id']]['point_xyz_mm'],[0,0,0])
    assert fresh==36 and len(seats)-fresh==76
    for row in audit['moved_screw_edges']:
        near(row['distance_to_left_panel_outline_edge_mm'], row['x_mm']-row['panel_min_x_mm'])
        near(row['distance_to_left_panel_outline_edge_mm'],32.3875)
        assert row['strength_or_punching_capacity'] is None
    for member in audit['candidate_member_restraint_paths']:
        stations=member['candidate_stations_mm']; points=[0,*stations,member['gross_length_mm']]
        gaps=[b-a for a,b in zip(points,points[1:])]
        near(gaps,member['end_and_interior_geometric_gaps_mm'])
        near(max(gaps),member['largest_candidate_gap_mm'])
        near(max(gaps)/38.1,member['Ke1_candidate_gap_over_weak_dimension'])
        near(member['NDS3p7p1p4_domain_limit_mm'],50*member['weak_dimension_mm'])
        near(member['NDS3p7p1p4_domain_limit_mm'],1905,atol=1e-6)
        assert member['effective_length_adopted'] is False and member['Cp_adopted'] is False
        assert all(r['route_strength_and_stiffness_qualified'] is False for r in member['candidate_panel_return_paths'])
    functions=extract(DOC/'connected-stack-followup-v1/analyze.py', ['line_bound','bearing_trial','known_answers'],helper_env)
    known=functions['known_answers']()
    assert known==connected['known_answers']
    trials=cd['member_bearing_trials']; stacks=cd['connected_stacks']
    assert len(trials)==144 and len(stacks)==48
    dfl=extract('mini_moonboard/bolted_timber_checks.py',['dfl_dowel_bearing_psi'],helper_env)['dfl_dowel_bearing_psi']
    threads=extract(ci['references']['timber_helper']['path'],['thread_windows'],helper_env)['thread_windows']
    catalog=read(ci['references']['catalog']['path'],ci['references']['catalog']['sha256'])
    roots=read(ci['references']['roots']['path'],ci['references']['roots']['sha256'])
    max_force_error=max_moment_error=max_endpoint_error=0.0
    fields={}
    for case in original['cases']:
        manifest=read(case['manifest']['path'],case['manifest']['sha256'])
        field=read(manifest['field']['path'],manifest['field']['sha256'])
        assert field['source_inputs']['geometry']['report']==original['old_geometry']
        fields[case['case_id']]=field
    for row in trials:
        field=fields[row['case_id']]
        shaft=next(r for r in field['source_inputs']['shafts'] if r['axis_id']==row['axis_id'])
        port=next(r for key in ['common_shaft_wood_bearing_actions','common_shaft_steel_port_actions'] for r in field[key] if r['axis_id']==row['axis_id'] and r['surface_index']==row['surface_index'])
        bearings={r['id']:r for r in field['common_shaft_bearing_actions']}
        captures={r['id']:r for r in field['shaft_end_capture_actions']}
        replay=functions['bearing_trial'](shaft,row['surface_index'],port,bearings,captures)
        for key,value in replay.items():
            assert row[key]==value, ('bearing replay',row['case_id'],row['axis_id'],key)
        g=np.asarray(shaft['basis'][0]); L=np.diff(row['interval_from_axis_point_mm'])[0]
        F=np.asarray(row['lateral_force_on_host_xyz_n']); C=np.asarray(row['moment_on_host_about_interval_center_xyz_nmm'])
        ends=np.asarray(row['affine_endpoint_line_density_vectors_n_mm'])
        # Integrate the stored endpoint interpolation directly, independently
        # of the producer's two-point Gaussian construction.
        near((ends[0]+ends[1])*L/2,F)
        S=(ends[1]-ends[0])*L**2/12
        near(np.cross(g,S),C)
        full=np.asarray(port['force_on_host_xyz_n'])
        recentered=np.asarray(port['moment_on_host_at_point_xyz_nmm'])+np.cross(np.asarray(port['point_xyz_mm'])-row['center_xyz_mm'],full)
        near(recentered,C)
        peak=max(np.linalg.norm(e) for e in ends)
        max_force_error=max(max_force_error,float(np.linalg.norm((ends[0]+ends[1])*L/2-F)))
        max_moment_error=max(max_moment_error,float(np.linalg.norm(np.cross(g,S)-C)))
        max_endpoint_error=max(max_endpoint_error,abs(peak-row['affine_trial_peak_line_density_n_mm']))
        near(peak,row['affine_trial_peak_line_density_n_mm'])
        assert peak+1e-8 >= row['necessary_directional_peak_line_density_bound_n_mm']
        near(peak/row['bearing_screen_D_mm'],row['affine_trial_peak_projected_bearing_mpa'])
        if row['kind']=='wood':
            Fe=dfl(row['bearing_screen_D_mm']/25.4,90)*0.006894757293168
            near(Fe,row['DFL_Fe90_material_parameter_mpa'])
            near(row['affine_trial_peak_projected_bearing_mpa']/Fe,row['affine_peak_over_Fe90_parameter'])
        else:
            assert row['eoere_product_bearing_resistance_mpa'] is None
        assert row['deformation_compatibility_or_yield_capacity_established'] is False
    for stack in stacks:
        field=fields[stack['case_id']]
        shaft=next(r for r in field['source_inputs']['shafts'] if r['axis_id']==stack['axis_id'])
        assert threads(shaft,catalog,roots)==stack['thread_window']
        assert stack['current_geometry_response_or_joint_capacity'] is None
        p=np.asarray(shaft['point']); g=np.asarray(shaft['basis'][0])
        reaction=np.zeros(3); couple=np.zeros(3)
        own=[r for r in trials if r['case_id']==stack['case_id'] and r['axis_id']==stack['axis_id']]
        assert len(own)==3
        for row in own:
            lo,hi=row['interval_from_axis_point_mm']; L=hi-lo
            # Force and moment about the shaft datum integrated directly from
            # the saved endpoints, with action/reaction sign on the shaft.
            endpoints=np.asarray(row['affine_endpoint_line_density_vectors_n_mm'])
            f=-(endpoints[0]+endpoints[1])*L/2
            s=-(endpoints[1]-endpoints[0])*L**2/12
            reaction+=f
            couple+=np.cross(g,s)+np.cross(np.asarray(row['center_xyz_mm'])-p,f)
        for action in field['shaft_end_capture_actions']:
            if action['axis_id']==stack['axis_id']:
                f=np.asarray(action['force_on_first_xyz_n']); reaction+=f
                couple+=np.cross(np.asarray(action['point_xyz_mm'])-p,f)+action['moment_on_first_at_point_xyz_nmm']
        for load in field['body_applied_loads']:
            if load['body']==shaft['body']:
                f=np.asarray(load['force_xyz_n']); reaction+=f
                couple+=np.cross(np.asarray(load['point_xyz_mm'])-p,f)+load.get('moment_xyz_nmm',[0,0,0])
        near(float(np.linalg.norm(reaction)),stack['connected_force_residual_n'],atol=1e-10)
        near(float(np.linalg.norm(couple)),stack['connected_moment_residual_nmm'],atol=1e-9)
    assert all(r['adjusted_complete_joint_resistance_n'] is None for r in connected['stacks'])
    near(max(r['connected_force_residual_n'] for r in stacks),connected['maximum_connected_force_residual_n'])
    near(max(r['connected_moment_residual_nmm'] for r in stacks),connected['maximum_connected_moment_residual_nmm'])
    for result in [audit,connected]:
        assert result['fabrication_or_climbing_release'] is False
        assert not any(result['execution'].values())
    pins[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for p,digest in pins.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest, 'Source changed during review: '+p
    result={
      'schema':'independent_current_geometry_followups_arithmetic_review/v1',
      'status':'PASS_BOUNDED_SOURCE_ARITHMETIC_AND_APPLICABILITY_ONLY',
      'source_sha256':pins,
      'checks':{'owned_packet_files':10,'revised_base_delta_replayed':True,
       'washer_saved_row_arithmetic':112,'fresh_changed_host_rows':fresh,'unchanged_seat_rows':76,
       'saved_moved_screw_edge_arithmetic':10,'restraint_station_rows':4,
       'old_field_bindings':6,'connected_stored_endpoint_integrals_and_datums':144,
       'own_member_kernel_and_raw_action_replays':144,'independent_connected_free_body_integrals':48,
       'thread_window_kernel_replays':48,'known_answer_and_rejection_controls':known,
       'maximum_endpoint_integral_force_error_n':max_force_error,
       'maximum_endpoint_integral_moment_error_nmm':max_moment_error,
       'maximum_endpoint_peak_error_n_mm':max_endpoint_error,
       'all_eight_complete_joint_resistances_null':True,'retained_old_exceedances_exact':True},
      'substantial_findings':[],
      'applicability':[
       'Audit geometry is base-v3 extra OFF, with preceding trimmed cleats; it does not evaluate the latest two-cleat extension.',
       'Six source fields remain the old untrimmed raised-rail revision; arithmetic does not admit a response for base-v3 or the extension.',
       'Signed affine bearing is an equilibrium construction only; the directional bound is necessary, and compatibility/yield/contact are unresolved.',
       'Fe90 is a dowel-bearing material parameter, not an ASD local pressure allowable or complete capacity.',
       'The root-floor bearing screen is a declared component comparison and does not replace the partially threaded shaft basis.',
       'Annulus support and screw outline distance are nominal geometry evidence; brace station gaps and return paths do not establish restraint strength or effective length.'
      ],
      'primary_source_check':{'TR12_2015_url':'https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf',
       'verified_scope':'Example 3.1 zero-gap mode-II 414-lbf result and report distinction between bearing/yield inputs and adjusted reference values.',
       'NDS2024_live_PDF_access':'Pinned Chapter 11/12 URLs returned web-tool errors; no alternative edition is adopted as a new capacity source.'},
      'limits':['No CAD/BRep import/query, browser, native/global solve, new geometry, install or full test suite.',
       'Existing frozen saved-solid support results are reused; their actual shape intersections are not rerun.',
       'Only selected source-only functions are AST-extracted, so their CAD/native module imports and run methods are never executed.',
       'Parent owns source-closure verification, final integration and publication; no engineering/physical acceptance.'],
      'mechanics_acceptance':False,'physical_release':False,
      'runtime':{'python':platform.python_version(),'numpy':np.__version__},
      'command':['.venv/bin/python','-B',str(Path(__file__).relative_to(ROOT))]
    }
    output=HERE/'receipt.json'
    output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'source_count':len(pins),'checks':result['checks'],'findings':[]}))

if __name__=='__main__':
    main()
