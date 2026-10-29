import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import test from 'node:test';
import {documentsForModel} from '../site/documentation-links.mjs';
import {SIX_BOLT_CLEAT_MODEL,SIX_BOLT_CLEAT_ASSETS} from '../site/eoere-v11-six-bolt-cleat-overlay.mjs';
import {SIX_BOLT_CLEAT_RESULTS_ASSET,SIX_BOLT_CLEAT_RESULTS_SOURCES,
  sixBoltCleatResultsStatus,validateSixBoltCleatComponentReferenceSummary,
  validateSixBoltCleatCurrentReferenceSummary,validateSixBoltCleatParentBankAdmission,
  validateSixBoltCleatResponseBank,validateSixBoltCleatResults}
  from '../site/eoere-v11-six-bolt-cleat-results.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),model='eoere-v11-six-bolt-cleat-preview';
const publicPacket='docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat';
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const bytes=filename=>readFileSync(path.join(root,filename));
const json=filename=>JSON.parse(bytes(filename));
const omitted=['left','right'].flatMap(side=>[1,2].map(index=>`v11_cleat_${side}_post_${index}`));
const refEqual=(left,right)=>assert.deepEqual(left,right);
const portableBytes=ref=>{
  assert.ok(ref?.path.startsWith('docs/'),'computed viewer sources must use portable documentation copies');
  assert.doesNotMatch(ref.path,/fea\/generated|\.\.(\/|$)/);
  const raw=bytes(ref.path);
  assert.equal(hash(raw),ref.sha256,`public source hash must match its result binding: ${ref.path}`);
  return raw;
};

test('the six-bolt route preserves historical routes, index authority, and the selected default',()=>{
  const html=bytes('site/index.html').toString();
  assert.equal(SIX_BOLT_CLEAT_MODEL,model);
  assert.ok(html.includes("['"+model+"', 'Six-bolt cleat trial · 102 stacks · conditional results']"));
  assert.ok(html.includes('Loading six-bolt cleat development · 102 stacks'));
  assert.ok(html.includes('sixBoltCleat ? loadSixBoltCleatPreviewScene : externalHexHeads ? loadExternalHexHeadsResultsScene'));
  assert.ok(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert.ok(html.includes("loadExternalHexHeadsResultsScene : fourTopBolts"));
  assert.ok(html.includes("groupExamples: !['eoere-v11-six-bolt-cleat-preview'"));

  const links=documentsForModel(model);
  for(const suffix of ['/owner-six-bolt-cleat-evaluation.json','/six-bolt-cleat/geometry-receipt.json',
    '/six-bolt-cleat/response-bank.json','/six-bolt-cleat/parent-bank-admission.json',
    '/six-bolt-cleat/current-reference-summary.json','/six-bolt-cleat/component-reference-summary.json',
    '/six-bolt-cleat/historical-scope-disposition.json'])
    assert.ok(links.some(row=>row.path.endsWith(suffix)),`candidate documentation navigation must include ${suffix}`);
  for(const row of links)assert.ok(bytes(row.path).length,`linked source exists: ${row.path}`);

  assert.ok(SIX_BOLT_CLEAT_RESULTS_SOURCES,'final computed result source bindings are required');
  const development=json('docs/bolted-frame-development/development-revisions.json');
  const current=json('current-candidate.json');
  const ownerTrial=development.owner_authorized_six_bolt_cleat_trial;
  assert.equal(development.development_selection.record_pointer,'/owner_authorized_shorter_bolt_trial',
    'the existing development-selection pointer remains unchanged');
  assert.equal(current.candidate,'compact-floor-flush-development',
    'current-candidate.json remains the selected screw-and-bracket authority');
  assert.equal(development.selected_baseline?.authority??'current-candidate.json','current-candidate.json');
  assert.equal(development.selected_baseline?.candidate??current.candidate,current.candidate);
  assert.equal(ownerTrial.revision,'v11-six-bolt-cleat-v1');
  assert.equal(ownerTrial.bolt_count,102);
  refEqual(ownerTrial.own_response_bank,SIX_BOLT_CLEAT_RESULTS_SOURCES.response_bank_public);
  refEqual(ownerTrial.parent_bank_admission,SIX_BOLT_CLEAT_RESULTS_SOURCES.parent_bank_admission_public);
  refEqual(ownerTrial.current_reference_summary,SIX_BOLT_CLEAT_RESULTS_SOURCES.current_reference_summary_public);
  refEqual(ownerTrial.component_reference_summary,SIX_BOLT_CLEAT_RESULTS_SOURCES.component_reference_summary_public);
  refEqual(ownerTrial.raw_response_bank,SIX_BOLT_CLEAT_RESULTS_SOURCES.response_bank);
  refEqual(ownerTrial.raw_parent_bank_admission,SIX_BOLT_CLEAT_RESULTS_SOURCES.parent_bank_admission);
  assert.equal(ownerTrial.candidate_selected,false);
  for(const key of['actual_property_qualification','candidate_selected','structural_acceptance','purchase_authorized',
    'drilling_released','physical_release','fabrication_released','climbing_released'])assert.equal(ownerTrial[key],false);
});

test('the checked viewer scene carries the exact 102-axis, 1035-part geometry delta',()=>{
  const provenanceRaw=bytes(SIX_BOLT_CLEAT_ASSETS.path);
  assert.equal(hash(provenanceRaw),SIX_BOLT_CLEAT_ASSETS.sha256);
  const provenance=JSON.parse(provenanceRaw),sceneRaw=bytes(provenance.scene.path);
  assert.equal(hash(sceneRaw),provenance.scene.sha256);
  const scene=JSON.parse(gunzipSync(sceneRaw));
  assert.equal(scene.part_count,1035);assert.equal(scene.counts.bolt_stacks,102);
  assert.equal(scene.counts.metal_role_rows,510);assert.equal(scene.counts.spacer_pieces,0);assert.equal(scene.counts.washer_pieces,204);
  assert.equal(scene.counts.Hillman_axes,66);assert.equal(scene.counts.angles,24);
  assert.deepEqual(scene.part_record_census,{parent_occupied_part_records:1055,removed_hardware_role_records:20,
    candidate_occupied_part_records:1035,replaced_geometry_records:6,unchanged_parent_part_records:1029,
    equation:'1055 parent records - 20 removed bolt-role records = 1035 candidate records; 6 of those retain their part identities but receive replacement wood meshes, leaving 1029 unchanged parent records.'});
  assert.equal(scene.panel_screw_backing.axis_count,66);assert.equal(scene.panel_screw_backing.axis_rows_byte_semantically_identical,true);
  assert.equal(scene.panel_screw_backing.backing_receiver_count,16);assert.equal(scene.panel_screw_backing.unchanged_backing_receivers,14);
  assert.deepEqual(scene.panel_screw_backing.source_material_superset_receivers,['base_post_outer_left','base_post_outer_right']);
  assert.equal(scene.panel_screw_backing.source_material_removed_mm3,0);
  assert.deepEqual(scene.panel_screw_backing.screw_axes_on_restored_receivers,
    ['round_kicker_left_rim_1','round_kicker_left_rim_2','round_kicker_right_rim_1','round_kicker_right_rim_2']);
  assert.equal(scene.all_axis_ids.length,102);assert.equal(new Set(scene.all_axis_ids).size,102);
  assert.deepEqual(scene.removed_axis_ids,omitted);assert.ok(omitted.every(axis=>!scene.all_axis_ids.includes(axis)));
  assert.equal(scene.geometry_only,true);assert.equal(scene.current_response_computed,false);
  assert.equal(scene.trial_selected,false);assert.equal(scene.structural_acceptance,false);
});

test('computed labels join both public summaries and reject stale, omitted, or changed-domain inputs',()=>{
  assert.ok(SIX_BOLT_CLEAT_RESULTS_ASSET,'the candidate-owned computed result asset must be admitted');
  assert.ok(SIX_BOLT_CLEAT_RESULTS_SOURCES,'the complete result source bundle must be admitted');
  const sources=SIX_BOLT_CLEAT_RESULTS_SOURCES;
  for(const key of['response_bank_public','parent_bank_admission_public','current_reference_summary_public',
    'component_reference_summary_public'])portableBytes(sources[key]);

  const provenance=JSON.parse(bytes(SIX_BOLT_CLEAT_ASSETS.path));
  const scene=JSON.parse(gunzipSync(bytes(provenance.scene.path)));
  const bank=JSON.parse(portableBytes(sources.response_bank_public));
  const admission=JSON.parse(portableBytes(sources.parent_bank_admission_public));
  const summary=JSON.parse(portableBytes(sources.current_reference_summary_public));
  const componentSummary=JSON.parse(portableBytes(sources.component_reference_summary_public));
  const receiptRaw=portableBytes({path:`${publicPacket}/geometry-receipt.json`,sha256:summary.geometry_receipt.sha256});
  const receipt=JSON.parse(receiptRaw);
  assert.equal(receipt.occupied_part_count_verified,1035);
  assert.equal(receipt.candidate_spacer_count,0);
  refEqual(summary.geometry,scene.geometry_source);
  refEqual(scene.geometry_receipt,{path:`${publicPacket}/geometry-receipt.json`,sha256:summary.geometry_receipt.sha256});
  refEqual(sources.geometry_receipt_public,scene.geometry_receipt);
  refEqual(summary.source_bindings.geometry,summary.geometry);
  refEqual(summary.source_bindings.bank,summary.response_bank);
  refEqual(summary.source_bindings.receipt,summary.geometry_receipt);
  refEqual(summary.source_bindings.parent_bank_admission,summary.parent_bank_admission);
  refEqual(summary.response_bank,sources.response_bank);
  refEqual(summary.parent_bank_admission,sources.parent_bank_admission);
  assert.equal(summary.axis_ids.length,102);assert.equal(new Set(summary.axis_ids).size,102);
  assert.deepEqual(summary.axis_ids,scene.all_axis_ids);
  assert.deepEqual(summary.omitted_axis_ids,omitted);
  assert.equal(summary.independent_replays,12);
  assert.equal(componentSummary.response_bank.sha256,sources.response_bank.sha256);
  assert.equal(componentSummary.geometry.sha256,sources.geometry.sha256);
  assert.equal(componentSummary.checked_geometry_receipt.sha256,sources.checked_geometry_receipt.sha256);
  refEqual(componentSummary.parent_runtime_proof,sources.parent_runtime_proof);
  assert.equal(componentSummary.compact_metrics.counts.axes,102);
  assert.equal(componentSummary.compact_metrics.counts.ends,204);
  assert.equal(componentSummary.compact_metrics.counts.washer_end_case_rows,1224);
  assert.equal(componentSummary.compact_metrics.counts.bond_leaf_wrench_states,12);
  assert.equal(componentSummary.compact_metrics.counts.baseline_body_case_states,144);
  assert.equal(componentSummary.compact_metrics.counts.header_variant_body_case_states,48);
  assert.equal(componentSummary.compact_metrics.counts.header_event_aliases,96);
  assert.equal(componentSummary.compact_metrics.counts.baseline_fine_states,1);
  assert.equal(componentSummary.compact_metrics.counts.header_fine_states,1);
  assert.equal(componentSummary.compact_metrics.counts.actual_backing_domains,384);
  assert.equal(componentSummary.compact_metrics.domain.actual_domains,384);
  assert.equal(componentSummary.compact_metrics.domain.exact_cached_domains,0);
  assert.equal(componentSummary.compact_metrics.domain.newly_integrated_domains,384);
  assert.equal(componentSummary.compact_metrics.domain.exact_cached_domains+
    componentSummary.compact_metrics.domain.newly_integrated_domains,384);
  const bridgeGate=componentSummary.compact_metrics.angle_header.bridge_gate;
  assert.equal(bridgeGate.all_gates_passed,true);assert.equal(bridgeGate.fresh_case_event_rows,12);
  assert.equal(bridgeGate.raw_high_minus_low_moment_gate_Nmm,1e-4);
  assert.equal(bridgeGate.raw_high_minus_low_moment_gate_passed,true);
  assert.equal(bridgeGate.original_member_cut_gate.gate_Nmm,0.1);
  assert.equal(bridgeGate.original_member_cut_gate.passed,true);
  for(const body of['eoere_clip_header_outer_under_left','eoere_clip_header_outer_under_right']){
    const proof=componentSummary.compact_metrics.domain.affected_post_domains[body];
    assert.equal(proof.post_support_patches,8);assert.equal(proof.all_rebuilt_from_current_fields,true);
    assert.equal(proof.parent_106_two_void_domain_rejected,true);
    for(const key of['near_timber_10_31875_mm_bore_absent','unused_near_steel_factory_hole_at_23_8125_mm',
      'retained_far_timber_bore_at_65_0875_mm','factory_steel_hole_10_mm_retained'])assert.equal(proof[key],true);
  }
  assert.equal('maximum_abs_normal_torque_Nmm' in componentSummary.compact_metrics.bond,false,
    'the projection cannot invent an undefined normal-torque scalar');

  const resultRaw=bytes(SIX_BOLT_CLEAT_RESULTS_ASSET.path);
  assert.equal(hash(resultRaw),SIX_BOLT_CLEAT_RESULTS_ASSET.sha256);
  const data=JSON.parse(resultRaw);
  const expected={revision:scene.revision,geometry:summary.geometry,geometry_receipt:summary.geometry_receipt,
    physical_receipt:sources.checked_geometry_receipt,geometry_metadata_receipt:sources.geometry_metadata_receipt,
    geometry_receipt_public:{path:`${publicPacket}/geometry-receipt.json`,sha256:summary.geometry_receipt.sha256},
    geometry_provenance:{path:SIX_BOLT_CLEAT_ASSETS.path,sha256:SIX_BOLT_CLEAT_ASSETS.sha256},
    owner_authorization:sources.owner_authorization,clearance:sources.clearance,
    mechanics_readiness:sources.mechanics_readiness,response_bank:sources.response_bank,
    parent_bank_admission:sources.parent_bank_admission,current_reference_summary:sources.current_reference_summary,
    component_reference_summary:sources.component_reference_summary,parent_runtime_proof:sources.parent_runtime_proof,
    response_bank_public:sources.response_bank_public,
    parent_bank_admission_public:sources.parent_bank_admission_public,
    current_reference_summary_public:sources.current_reference_summary_public,
    component_reference_summary_public:sources.component_reference_summary_public,axis_ids:scene.all_axis_ids};
  assert.equal(hash(bytes(SIX_BOLT_CLEAT_ASSETS.path)),SIX_BOLT_CLEAT_ASSETS.sha256,
    'geometry-only provenance remains byte-stable after the result overlay');
  validateSixBoltCleatResponseBank(bank,expected);
  validateSixBoltCleatParentBankAdmission(admission,expected);
  validateSixBoltCleatCurrentReferenceSummary(summary,expected);
  validateSixBoltCleatComponentReferenceSummary(componentSummary,expected);
  validateSixBoltCleatResults(data,bank,admission,summary,componentSummary,expected);
  assert.deepEqual(data.conditional_reference_results,summary.conditional_reference_results);
  assert.deepEqual(data.compact_metrics,componentSummary.compact_metrics);
  assert.equal(data.axis_ids.length,102);assert.deepEqual(data.axis_ids,scene.all_axis_ids);
  assert.deepEqual(data.omitted_axis_ids,omitted);
  assert.equal(data.current_response_computed,true);assert.equal(data.trial_selected,false);
  assert.equal(data.structural_acceptance,false);assert.equal(data.fabrication_released,false);
  assert.equal(data.drilling_released,false);assert.equal(data.climbing_released,false);
  const status=sixBoltCleatResultsStatus({data,bank,summary,componentSummary});
  assert.match(status,/Conditional maxima:/);
  assert.match(status,/direct elastic steel 0\.514096/);
  const inherited=summary.conditional_reference_results.families.inherited_factor_diagnostics;
  assert.equal(inherited.wood_bearing_whole_affine.maximum.index.toFixed(6),'1.987349');
  assert.equal(inherited.reduced_connection_axial_bending.maximum.index.toFixed(6),'2.423087');
  assert.match(status,/Inherited-factor pressure\/N\/M maxima 1\.987349\/2\.423087; 13\/612 rows above one each, unadopted, actual Cg unassigned/);
  assert.match(status,/Mixed \(20 axes\/120 states\/240 planes\)/);
  assert.match(status,/Front retained affine-construction Fe\/5 diagnostic max/);
  const rear=summary.conditional_reference_results.rear,
    rearFe5=rear.full_wrench_conditional_reference,
    rearProjected=rear.projected_witness.maximum_projected_reference_index_case[2],
    frontContracted=summary.conditional_reference_results.front.contracted_full_action,
    rearContracted=rear.contracted_full_action;
  assert.ok(Number.isFinite(frontContracted.maximum_contracted_bearing_index));
  assert.ok(Number.isFinite(rearContracted.maximum_contracted_bearing_index));
  assert.equal(frontContracted.states,24);assert.equal(rearContracted.states,36);
  assert.ok(Math.abs(frontContracted.maximum_contracted_bearing_index-0.3870046566)<1e-9);
  assert.ok(Math.abs(rearContracted.maximum_contracted_bearing_index-0.7787434553)<1e-9);
  assert.equal(rearFe5.maximum_Fe_over_5_utilization.toFixed(6),'1.622760');
  assert.equal(rearFe5.Fe_over_5_states_above_one,13);
  assert.equal(rearProjected.toFixed(6),'0.690448');
  assert.equal(rear.projected_witness.reference_index_above_one_count,0);
  assert.ok(status.includes(`Rear retained affine-construction Fe/5 diagnostic max ${rearFe5.maximum_Fe_over_5_utilization.toFixed(6)}`));
  assert.ok(status.includes(`(${rearFe5.Fe_over_5_states_above_one}/${rearFe5.state_count} states above 1)`));
  assert.ok(status.includes(`projected witness max ${rearProjected.toFixed(6)} `+
    `(${rear.projected_witness.reference_index_above_one_count}/${rear.projected_witness.state_count} above 1)`));
  assert.ok(status.includes(`Contracted full-action bearing indices: front ${frontContracted.maximum_contracted_bearing_index.toFixed(6)}, `+
    `rear ${rearContracted.maximum_contracted_bearing_index.toFixed(6)}`));
  assert.doesNotMatch(status,/Contracted full-action bearing indices: .*pending/);
  const signed=summary.conditional_reference_results.signed_end_edge,
    planar=signed.signed_planar_rear_foot,
    optionalValues=signed.optional_both_edge_foot_diagnostic.marker_rows,
    omittedNet=signed.supplemental_signed_end_markers,
    brittle=summary.conditional_reference_results.brittle_paths.component_reference_summaries,
    reduced=brittle.reduced_depth.summary;
  assert.equal(planar.maximum_conditional_planar_component_index.toFixed(6),'0.999045');
  assert.equal(planar.resolved_case_count,12);assert.equal(planar.above_one_count,0);
  assert.equal(optionalValues.filter(value=>value>1).length,2);
  assert.equal(Math.max(...optionalValues).toFixed(6),'1.089124');
  assert.equal(omittedNet.cleat_post_net_rows,0);assert.equal(omittedNet.cleat_post_primitive_rows,0);
  assert.equal(reduced.case_rows,336);assert.equal(reduced.edge_scenario_rows,672);
  assert.equal(reduced.above_one_rows,2);assert.equal(reduced.maximum_conditional_index.toFixed(6),'1.089124');
  assert.match(status,/Signed rear-foot selector 0\.999045 \(12 resolved, 0 flags\)/);
  assert.match(status,/retained optional two-edge foot envelope 1\.089124 \(2 flags\), separate and unselected/);
  assert.match(status,/four omitted near-post axes: zero reported net\/primitive end flags; empty arrays are not acceptance/i);
  assert.match(status,/reduced-depth both-edge max 1\.089124 \(2\/336 case rows above 1; 672 edge-scenario comparisons\), a component check only/i);
  assert.match(status,/Washers \(1,224 end\/case rows; 204 unique ends\)/);
  assert.match(status,/Optional 220-row EYM is non-adopted; no parent-106 transfer/);
  assert.doesNotMatch(status,/signature pressure\/NM was not computed/,
    'current inherited-factor worksheet values are separate from the unregenerated legacy diagnostic book');
  assert.match(status,/compression-only static witness, not capacity/);
  assert.match(status,/four side\/two post bolts per cleat, four at each outer and center top connection/i);
  assert.match(status,/zero spacers/i);
  assert.match(status,/Backing: 384 current patches passed quadrature \(384 fresh, 0 cached\)/);
  assert.match(status,/unused near 10 mm factory steel hole remains/);
  assert.doesNotMatch(status,/unresolved .*ratio|geometry accepted/i);
  const statusWords=status.trim().split(/\s+/u).length;
  assert.ok(statusWords>=250&&statusWords<=350,`candidate status should stay concise (got ${statusWords} words)`);

  const staleSummary=structuredClone(summary);staleSummary.source_bindings.bank.sha256='0'.repeat(64);
  assert.throws(()=>validateSixBoltCleatCurrentReferenceSummary(staleSummary,expected),
    'a summary bound to another bank must be rejected');
  const staleComponentBank=structuredClone(componentSummary);staleComponentBank.response_bank.sha256='0'.repeat(64);
  assert.throws(()=>validateSixBoltCleatComponentReferenceSummary(staleComponentBank,expected),
    'component methods from a stale bank must be rejected');
  const staleDomainSource=structuredClone(componentSummary);
  staleDomainSource.component_routes.backing_domain_audit.audit.sha256='0'.repeat(64);
  assert.throws(()=>validateSixBoltCleatResults(data,bank,admission,summary,staleDomainSource,expected),
    'the component result identity must reject a changed backing-domain audit source');
  const staleDomainMetrics=structuredClone(componentSummary);
  staleDomainMetrics.compact_metrics.domain.actual_domains+=1;
  assert.throws(()=>validateSixBoltCleatComponentReferenceSummary(staleDomainMetrics,expected),
    'a stale backing-domain metric projection must be rejected');
  const omittedBank=structuredClone(bank);omittedBank.axis_ids=[...scene.all_axis_ids,omitted[0]];
  assert.throws(()=>validateSixBoltCleatResponseBank(omittedBank,expected),
    'an omitted post axis cannot return to the admitted bank');
  const omittedResults=structuredClone(data);omittedResults.axis_ids=[...data.axis_ids,omitted[1]];
  assert.throws(()=>validateSixBoltCleatResults(omittedResults,bank,admission,summary,componentSummary,expected),
    'an omitted post axis cannot return in current result labels');
  const missingSummary=structuredClone(data);delete missingSummary.sources.current_reference_summary;
  assert.throws(()=>validateSixBoltCleatResults(missingSummary,bank,admission,summary,componentSummary,expected),
    'computed labels require the current summary source binding');

  const staleParentBank=json('docs/bolted-frame-development/owner-frame-v11/external-hex-heads/response-bank.json');
  assert.throws(()=>validateSixBoltCleatResponseBank(staleParentBank,expected),
    'the public stale 106-axis bank must never provide six-bolt computed labels');
});
