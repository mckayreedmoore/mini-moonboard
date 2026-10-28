import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import {readIndex, validateZeroSpacerTrial, viewerModel} from '../scripts/check_bolted_development.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';
import {validateZeroSpacerResults, zeroSpacerResultsStatus} from '../site/eoere-v11-zero-spacer-results.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const model='eoere-v11-zero-spacer-preview';

test('zero-spacer geometry is distinct, keeps114axes and carries conditional access',()=>{
  const index=readIndex(),entry=index.owner_authorized_zero_spacer_trial;
  assert.equal(validateZeroSpacerTrial(entry,index),entry);
  const receipt=JSON.parse(readFileSync(path.join(root,entry.geometry_receipt.path)));
  assert.equal(receipt.all114_axis_stations_and30_profile_breps_unchanged,true);
  assert.equal(receipt.actual_tool_access_qualified,false);
  const html=readFileSync(path.join(root,'site/index.html'),'utf8');
  assert.equal(viewerModel(html,null),'compact-floor-flush-development');
  assert.ok(html.includes("['"+model+"',"));
  assert.ok(html.includes('zeroSpacerBolts ? loadZeroSpacerResultsScene : relocatedRear ? loadRelocatedRearResultsScene'));
  for(const row of documentsForModel(model))assert.ok(readFileSync(path.join(root,row.path)).length);
});

test('zero-spacer trial rejects wrong profile, geometry, counts and release claims',()=>{
  const index=readIndex(),original=index.owner_authorized_zero_spacer_trial;
  for(const mutate of[
    e=>{e.geometry_source.sha256='0'.repeat(64);},
    e=>{e.hardware_profile_contract.sha256='0'.repeat(64);},
    e=>{e.viewer.scene.decoded_sha256='0'.repeat(64);},
    e=>{e.trial_selected=true;},
    e=>{e.structural_acceptance=true;},
  ]){const changed=structuredClone(original);mutate(changed);assert.throws(()=>validateZeroSpacerTrial(changed,index));}
});

test('own zero-spacer results retain six cases, cold retry and current material flags',()=>{
  const entry=readIndex().owner_authorized_zero_spacer_trial;
  const data=validateZeroSpacerResults(JSON.parse(readFileSync(path.join(root,entry.viewer.results_data.path))));
  assert.equal(data.cases.length,6); assert.equal(data.independent_replays,12);
  assert.equal(data.mixed_common_work_reference.summary.endpoint_count,1152);
  assert.equal(data.mixed_common_work_reference.summary.above_one_rows.length,3);
  assert.ok(data.case_output_bases['k12-rear'].endsWith('/closure-retry-k12-rear-cold-v1'));
  assert.equal(data.rear.contracted_common_work_reference.above_one_state_count,0);
  assert.match(zeroSpacerResultsStatus(data),/3 conditional flags/);
  assert.match(zeroSpacerResultsStatus(data),/No fabrication or climbing release/);
});

test('completed component scope and next outer-top decision remain separately bound',()=>{
  const index=readIndex(),entry=index.owner_authorized_zero_spacer_trial;
  assert.equal(validateZeroSpacerTrial(entry,index),entry);
  const components=JSON.parse(readFileSync(path.join(root,entry.component_reference_summary.path)));
  assert.equal(components.counts.all_end_washer_case_states,1368);
  assert.equal(components.washer.near96_is_all_end_envelope,false);
  for(const mutate of[
    i=>{i.owner_authorized_four_bolt_outer_top_trial.cleat_bolts_each=6;},
    i=>{i.owner_authorized_four_bolt_outer_top_trial.outer_top_bolts_each=8;},
    i=>{i.owner_authorized_four_bolt_outer_top_trial.historical_capacity_transferred=true;},
    i=>{i.owner_authorized_zero_spacer_trial.component_reference_summary.sha256='0'.repeat(64);},
  ]){const changed=structuredClone(index);mutate(changed);assert.throws(()=>validateZeroSpacerTrial(changed.owner_authorized_zero_spacer_trial,changed));}
});

test('zero-spacer results reject old sources, removed flags, altered profiles and release',()=>{
  const index=readIndex(),entry=index.owner_authorized_zero_spacer_trial;
  const original=JSON.parse(readFileSync(path.join(root,entry.viewer.results_data.path)));
  for(const mutate of[
    d=>{d.sources.response_bank=index.owner_authorized_shorter_bolt_trial.response_bank;},
    d=>{d.mixed_common_work_reference.summary.above_one_rows.pop();},
    d=>{d.mixed_common_work_reference.summary.endpoint_count=1104;},
    d=>{d.mixed_common_work_reference.basis.A574_Fyb_scenario_psi=60000;},
    d=>{d.case_output_bases['k12-rear']=d.case_output_bases['a12-rear'];},
    d=>{d.cases[0].independent_replay=d.cases[0].independent_plywood_replay;},
    d=>{d.complete_joint_qualified=true;},
    d=>{d.climbing_released=true;},
  ]){const changed=structuredClone(original);mutate(changed);assert.throws(()=>validateZeroSpacerResults(changed));}
});
