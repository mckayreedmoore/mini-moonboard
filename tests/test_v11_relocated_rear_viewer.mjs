import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {gunzipSync} from 'node:zlib';
import test from 'node:test';
import {RELOCATED_REAR_MODEL,RELOCATED_REAR_ASSETS,applyRelocatedRearGeometry,loadRelocatedRearGeometryScene} from '../site/eoere-v11-relocated-rear-overlay.mjs';
import {RELOCATED_REAR_RESULTS_ASSET,validateRelocatedRearResults,relocatedRearResultsStatus,loadRelocatedRearResultsScene} from '../site/eoere-v11-relocated-rear-results.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';
import {viewerModel, validateRelocatedItem3, validateRelocatedCloseout, readIndex} from '../scripts/check_bolted_development.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site'),hash=raw=>createHash('sha256').update(raw).digest('hex');
const provenanceRaw=readFileSync(path.join(root,RELOCATED_REAR_ASSETS.path)),provenance=JSON.parse(provenanceRaw);
const sceneRaw=readFileSync(path.join(root,provenance.scene.path)),data=JSON.parse(gunzipSync(sceneRaw));
const oldProvenance=JSON.parse(readFileSync(path.join(root,provenance.parent_provenance.path)));
const oldResults=JSON.parse(readFileSync(path.join(root,oldProvenance.results.path)));
const resultsRaw=readFileSync(path.join(root,RELOCATED_REAR_RESULTS_ASSET.path)),results=JSON.parse(resultsRaw);

test('item3 component evidence retains open methods and the own fixed load bank',()=>{
  const entry=readIndex().owner_authorized_relocated_rear_pair_trial;
  const raw=readFileSync(path.join(root,entry.item3_disposition.path)),report=JSON.parse(raw);
  assert.equal(hash(raw),entry.item3_disposition.sha256);
  assert.equal(validateRelocatedItem3(report,entry),report);
  for(const mutate of[
    r=>{r.response_bank.sha256=oldResults.sources?.response_bank?.sha256??'0'.repeat(64);},
    r=>{r.geometry_components.current_068069_net_away=false;},
    r=>{r.brittle_components.geometry_paths.interrupted_directional_paths=0;},
    r=>{r.retained_other_flags.mixed_generic45_Mp4_states=0;},
    r=>{r.all_item3_criteria_resolved=true;},
    r=>{r.actual_Fy=235;},
    r=>{r.fabrication_released=true;},
  ]){const changed=structuredClone(report);mutate(changed);assert.throws(()=>validateRelocatedItem3(changed,entry));}
});

test('connection closeout cannot turn component bounds or review options into an adopted pass',()=>{
  const entry=readIndex().owner_authorized_relocated_rear_pair_trial;
  const raw=readFileSync(path.join(root,entry.connection_closeout.path)),report=JSON.parse(raw);
  assert.equal(hash(raw),entry.connection_closeout.sha256);
  assert.equal(validateRelocatedCloseout(report,entry),report);
  for(const mutate of[
    r=>{r.response_bank.sha256='0'.repeat(64);},
    r=>{r.geometry_method.Table_D.criterion_satisfied=true;},
    r=>{r.geometry_method['068069_near_edge_4D_is_optional_envelope']=false;},
    r=>{r.brittle_components.connected_parallel_transfer.interrupted_directions=0;},
    r=>{r.bolt_material.current_generic45_flags_cleared=true;},
    r=>{r.planning.fixed114_counts.bolts=102;},
    r=>{r.fitting_seat_bond.native_and_washer_pressure_fields_pointwise_unified=true;},
    r=>{r.all_applicable_criteria_resolved=true;},
    r=>{r.candidate_selected=true;},
    r=>{r.fabrication_released=true;},
  ]){const changed=structuredClone(report);mutate(changed);assert.throws(()=>validateRelocatedCloseout(changed,entry));}
});

test('relocated geometry joins own public receipt and exact shared parent without copying force results',()=>{
  assert.equal(hash(provenanceRaw),RELOCATED_REAR_ASSETS.sha256);assert.equal(hash(sceneRaw),provenance.scene.sha256);
  assert.equal(hash(sceneRaw),'82503878b440ec14a3d23a5251847b6de7a36f4bf3acc5741618e7759d66eb14');
  assert.equal(hash(provenanceRaw),'aa85ff0be29a73222551a14091d736d62dc08116b94c703c503fabd0754cc0e0');
  assert.equal(hash(readFileSync(path.join(site,'eoere-v11-relocated-rear-overlay.mjs'))),'2928b9b5d3daf2741a7a334537b15c9b7d780bc17e8377bb8358f413930d6bff');
  assert.equal(hash(gunzipSync(sceneRaw)),provenance.scene.decoded_sha256);
  for(const ref of[provenance.geometry_receipt,provenance.parent_provenance])assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  const receipt=JSON.parse(readFileSync(path.join(root,provenance.geometry_receipt.path)));
  assert.deepEqual(data.geometry_source,receipt.geometry);assert.deepEqual(data.geometry_receipt,provenance.geometry_receipt);
  assert.deepEqual(data.parent_geometry,oldProvenance.geometry);assert.equal(receipt.nominal_geometry_clear,true);
  assert.equal(data.replacements.length,4);assert.equal(data.reuses.length,20);assert.equal(data.relocated_axis_ids.length,4);
  assert.equal(new Set([...data.replacements,...data.reuses].map(row=>row.name)).size,24);
  assert.equal(data.part_count,1099);assert.equal(data.all_axis_ids.length,114);assert.equal(data.counts.spacer_pieces,4);
  assert.equal(provenance.unchanged_mesh_bytes_copied,0);assert.equal(provenance.trial_selected,false);
  assert.throws(()=>applyRelocatedRearGeometry({},null,oldResults,new Map()),/own model/,'historical114 results are not a geometry payload');
});

test('explicit own-result route preserves current112, old114 and baseline and exposes the fresh source menu',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');
  for(const key of[RELOCATED_REAR_MODEL,'eoere-v11-shorter-bolts-preview','eoere-v11-matching-rear-bolts-preview'])assert.equal(viewerModel(html,key),key);
  assert.equal(viewerModel(html,null),'compact-floor-flush-development');
  assert.ok(html.includes('relocatedRear ? loadRelocatedRearResultsScene : matchingRear ? loadMatchingRearScene'));
  assert.ok(html.includes('Unselected relocated upper-rear pair · 114 stacks · own references'));
  assert.ok(html.includes("groupExamples: !['eoere-v11-relocated-rear-preview'"));
  const rows=documentsForModel(RELOCATED_REAR_MODEL);assert.ok(rows.some(row=>row.path===provenance.geometry_receipt.path));
  for(const ref of Object.values(results.sources))assert.ok(rows.some(row=>row.path===ref.path));
  for(const file of['geometry-applicability.json','affected-connection-components.json.gz','item3-disposition.json',
    'connection-closeout.json','owner-constraint-options-review-v1.svg','planning/README.md'])assert.ok(rows.some(row=>row.path.endsWith('/relocated-rear-pair/'+file)));
  assert.ok(rows.every(row=>!/(matching-rear-bolts|shorter-bolts)\/(response-bank|reference-completion|reference-review)\.json$/.test(row.path)));
  rows.forEach(row=>assert.ok(readFileSync(path.join(root,row.path)).length));
  const start=html.indexOf('const designLabels = '),end=html.indexOf('const categoryLabels = ',start),weightLine={},weightNote={};
  runInNewContext(html.slice(start,end),{model:RELOCATED_REAR_MODEL,isWoodJoint:true,woodJointModels:[[RELOCATED_REAR_MODEL,'Trial']],
    modelSelect:{options:[{value:RELOCATED_REAR_MODEL,text:'Trial'}]},weightLine,weightNote,excludedMass:'unused',fetch:()=>assert.fail('no historical weight fetch')});
  assert.equal(weightLine.hidden,true);assert.equal(weightNote.hidden,true);
});

test('compact own results join the fresh6cases/12replays and distinguish contracted, ellipse and necessary references',()=>{
  assert.equal(hash(resultsRaw),RELOCATED_REAR_RESULTS_ASSET.sha256);assert.equal(validateRelocatedRearResults(results),results);
  for(const ref of Object.values(results.sources))assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  const bank=JSON.parse(readFileSync(path.join(root,results.sources.response_bank.path))),completion=JSON.parse(readFileSync(path.join(root,results.sources.reference_completion.path)));
  const contracted=JSON.parse(readFileSync(path.join(root,results.sources.contracted_rear_summary.path)));
  for(const[key,row]of Object.entries(completion.families.outputs))assert.deepEqual(results.family_references[key],{maximum:row.maximum,above_one_count:row.above_one_count});
  assert.deepEqual(results.rear.contracted_common_work_reference,completion.rear.contracted_common_work_reference);
  assert.equal(results.rear.contracted_common_work_reference.maximum,contracted.contracted_common_work_rear.maximum_contracted_bearing_index);
  assert.equal(results.rear.separate_original_ellipse_reference.maximum,completion.rear.projected_summary.maximum_projected_reference_index_case[2]);
  for(const row of results.cases){const own=bank.cases.find(item=>item.case_id===row.case_id);for(const key of Object.keys(row))assert.deepEqual(row[key],own[key]);}
  const status=relocatedRearResultsStatus(results);
  for(const text of['0.947988','0.815930','0.415174','0.411399','Primary contracted common-work rear reference 0.775020 across 36 states, zero above one',
    'Separate original ellipse reference 0.687147','continuous necessary lower bound 0.681218','35 rows','N/M: 16','complete connections and physical fit remain unqualified'])assert.ok(status.includes(text),text);
  assert.doesNotMatch(status,/0\.769859|0\.682571|1\.303678|complete joint pass|all criteria/);
  assert.throws(()=>validateRelocatedRearResults(oldResults),/own model/);
});

test('fresh mixed references expose all three own generic45bending flags separately from bearing and qualification',()=>{
  const mixed=results.mixed_common_work_reference,source=JSON.parse(readFileSync(path.join(root,results.sources.mixed_common_work_summary.path)));
  const controls=JSON.parse(readFileSync(path.join(root,results.sources.mixed_reference_controls.path)));
  assert.deepEqual(mixed.summary,source.summary);assert.deepEqual(mixed.summary,controls.summary);
  assert.equal(source.source_bindings.fresh_response_bank.sha256,results.sources.response_bank.sha256);
  assert.deepEqual(mixed.response_bank,results.sources.response_bank);assert.deepEqual(mixed.source,results.sources.mixed_common_work_summary);
  assert.deepEqual([mixed.summary.state_count,mixed.summary.receiver_case_count,mixed.summary.endpoint_count],[144,432,1104]);
  assert.equal(mixed.summary.above_one_count,3);assert.equal(mixed.actual_Fyb,null);assert.equal(mixed.complete_joint_capacity,null);assert.equal(mixed.physical_failure_claim,false);
  const status=relocatedRearResultsStatus(results);
  for(const row of source.summary.above_one_rows)assert.ok(status.includes(row.axis_id+'/'+row.case_id+' '+row.Mp4_hinge_index.toFixed(6)));
  for(const text of['3 conditional flags across 144 states, maximum 1.236282','required Fyb 55.632705 ksi','Contracted mixed bearing reference 0.456254, zero above one',
    'Actual Fyb, group factors, complete connections and physical fit remain unqualified'])assert.ok(status.includes(text),text);
});

const oldMixedSummary=JSON.parse(gunzipSync(readFileSync(path.join(root,'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/lateral-method-followthrough.json.gz')))).sections.mixed_Mp4_summary.data.summary;

for(const[name,mutate]of[
  ['current112bank substituted',d=>{d.sources.response_bank.sha256='0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c';}],
  ['old114revision relabelled current',d=>{d.revision='v11-matching-rear-bolts-v1';}],
  ['old114geometry substituted',d=>{d.geometry.sha256='28bf006c24fe2c57bd2b2a942f34954ef23a294789fd9676cdf5c49b48b35a48';}],
  ['wrong analysis source',d=>{d.analysis_geometry.path=d.analysis_geometry.path.replace('analysis-v2','analysis-v1');}],
  ['missing fresh case',d=>{d.cases.pop();}],
  ['another case field',d=>{d.cases[0].field=d.cases[1].field;}],
  ['duplicated replay bytes',d=>{d.cases[0].independent_replay.sha256=d.cases[0].field.sha256;}],
  ['unadmitted replay',d=>{d.cases[0].both_independent_replays_admitted=false;}],
  ['relaxed load recipe',d=>{d.load_contract.downward_multiplier=1;}],
  ['weight interpolation',d=>{d.weight_interpolation_available=true;}],
  ['olderellipse substituted as primary',d=>{d.rear.contracted_common_work_reference.maximum=d.rear.separate_original_ellipse_reference.maximum;}],
  ['contracted source unbound',d=>{d.rear.contracted_common_work_reference.source.sha256='0'.repeat(64);}],
  ['contraction removed without changing reference',d=>{d.rear.contracted_common_work_reference.governing.lambda=1;}],
  ['necessarylowerbound promoted beyond its witness',d=>{d.rear.separate_continuous_necessary_bound.maximum_lower_bound=1;}],
  ['reference promoted to complete rear capacity',d=>{d.rear.contracted_common_work_reference.complete_joint_qualified=true;}],
  ['nonfinite family reference',d=>{d.family_references.timber_net_shear_torsion.maximum.index=Infinity;}],
  ['actualCg adopted',d=>{d.actual_Cg_adopted=1;}],
  ['complete capacity invented',d=>{d.complete_connection_capacity=1;}],
  ['physical release inferred',d=>{d.fabrication_released=true;}],
  ['old112bank assigned to mixed states',d=>{d.mixed_common_work_reference.response_bank.sha256='0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c';}],
  ['old112mixed summary substituted',d=>{d.sources.mixed_common_work_summary.sha256='8380c64ecd2d848e10a99cae0edb60f75910ec8e5715a6417da8421535fbf8cc';}],
  ['old112fiveflag inventory copied',d=>{d.mixed_common_work_reference.summary.above_one_rows=oldMixedSummary.new_reference_above_one_rows;d.mixed_common_work_reference.summary.above_one_count=5;}],
  ['oldrear case retained among the three flags',d=>{d.mixed_common_work_reference.summary.above_one_rows[1].case_id='a12-rear';}],
  ['mixed bending flags silently erased',d=>{d.mixed_common_work_reference.summary.above_one_rows=[];d.mixed_common_work_reference.summary.above_one_count=0;}],
  ['a strongerFyb hypothesis silently substituted',d=>{d.mixed_common_work_reference.basis.A574_Fyb_scenario_psi=166500;}],
  ['requiredFyb adopted as actualproperty',d=>{d.mixed_common_work_reference.actual_Fyb=55632.70487412396;}],
  ['conditional mixed flags promoted to physical failure',d=>{d.mixed_common_work_reference.physical_failure_claim=true;}],
  ['bending reference labelled as bearing',d=>{d.mixed_common_work_reference.summary.maximum_contracted_bearing_index=d.mixed_common_work_reference.summary.maximum_Mp4_hinge_index;}],
])test('own relocated results reject '+name,()=>{const changed=structuredClone(results);mutate(changed);assert.throws(()=>validateRelocatedRearResults(changed));});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8'),start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
const baseTHREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');

test('actual portable loader composes24 changes and114 selectable stacks with1075 parent mesh references retained',async context=>{
  const previous=globalThis.fetch,requests=[],geometries=new Set();let before;
  const originalClone=baseTHREE.BufferGeometry.prototype.clone;
  baseTHREE.BufferGeometry.prototype.clone=function(){const result=originalClone.call(this);geometries.add(result);return result;};
  class TrackedGeometry extends baseTHREE.BufferGeometry{constructor(){super();geometries.add(this);}}
  const THREE={...baseTHREE,BufferGeometry:TrackedGeometry};
  context.after(()=>{globalThis.fetch=previous;baseTHREE.BufferGeometry.prototype.clone=originalClone;});
  globalThis.fetch=async input=>{
    const name=String(input);if(name.startsWith('blob:'))return previous(input);
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);
    assert.ok(target.startsWith(site+path.sep)&&/\.json(?:\.gz)?$/.test(target),'only public site JSON assets may be read');
    requests.push(path.relative(site,target));
    if(target===path.join(root,provenance.scene.path))before=new Map([...geometries].filter(g=>!g.disposed&&g.attributes.position)
      .map(g=>[g,hash(new Uint8Array(g.attributes.position.array.buffer))]));
    return new Response(readFileSync(target));
  };
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const loaded=await loadRelocatedRearGeometryScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,resolveMeshPath:name=>resolveMeshPath(name,aliases)});
  assert.ok(before);assert.equal(loaded.parts.length,1099);assert.equal(new Set(loaded.parts.map(part=>part.name)).size,1099);
  const changed=new Set([...data.replacements,...data.reuses].map(row=>row.name));let shared=0;
  for(const part of loaded.parts){if(changed.has(part.name))assert.ok(part.geometry&&!before.has(part.geometry),'new geometry: '+part.name);
    else {if(part.geometry)assert.ok(before.has(part.geometry),'parent geometry identity: '+part.name);else assert.equal(typeof part.path,'string');shared++;}
    assert.ok(!part.geometry?.disposed);assert.equal(part.fabrication.analysis_reference,undefined);assert.equal(part.fabrication.conditional_force_only_reference,undefined);}
  assert.equal(shared,1075);
  for(const[geometry,vertices]of before)assert.equal(hash(new Uint8Array(geometry.attributes.position.array.buffer)),vertices,'parent source vertices must not be translated in place');
  const bolts=loaded.parts.filter(part=>part.fabrication.kind==='bolt');assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,114);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role?.endsWith('washer')).length,228);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role?.startsWith('spacer')).length,4);
  assert.equal(loaded.parts.filter(part=>part.fabrication.kind==='screw').length,66);
  for(const id of data.relocated_axis_ids){const stack=bolts.filter(part=>part.fabrication.connection_name===id);assert.equal(stack.length,5);
    for(const part of stack){assert.deepEqual(part.fabrication.axis_point_xyz_mm,data.axis_bindings[id].point_xyz_mm);assert.equal(part.fabrication.selected_product,'G0340956');assert.equal(Number(part.fabrication.spacer_piece_count),0);}
    const shaft=stack.find(part=>part.fabrication.hardware_role==='shaft');shaft.geometry.computeBoundingBox();
    assert.ok(Math.abs(shaft.geometry.boundingBox.max.x-shaft.geometry.boundingBox.min.x-215.9)<.2);}
  assert.equal(loaded.meta.geometry_only,true);assert.equal(loaded.meta.analysis_pending,true);assert.equal(loaded.meta.current_response_computed,false);
  assert.equal(loaded.meta.trial_selected,false);assert.equal(loaded.meta.actual_Cg_adopted,null);assert.equal(loaded.meta.complete_connection_capacity,null);
  for(const key of['case_rows','family_references','rear_references','member_vector_maxima','weight_response','standard_cg'])assert.equal(loaded.meta[key],undefined);
  assert.ok(!requests.some(name=>/results(?:-v2)?\.json$/.test(name)),'no historical result JSON may be fetched');
  assert.match(loaded.meta.status,/Unselected.*geometry only; own results pending/);
  const rawMeta=structuredClone(loaded.meta);
  const analyzed=await loadRelocatedRearResultsScene(THREE,{},async()=>loaded);
  assert.equal(analyzed.parts,loaded.parts);assert.deepEqual(loaded.meta,rawMeta,'frozen geometry stage metadata remains unchanged');
  assert.equal(analyzed.meta.geometry_only,false);assert.equal(analyzed.meta.analysis_pending,false);assert.equal(analyzed.meta.current_response_computed,true);
  assert.equal(analyzed.meta.case_rows.length,6);assert.equal(analyzed.meta.independent_replays,12);assert.equal(analyzed.meta.trial_selected,false);
  for(const key of['actual_Cg_adopted','actual_Cdelta_adopted','actual_Fyb_adopted','complete_connection_capacity','accepted_connection_exceedance_count'])assert.equal(analyzed.meta[key],null);
  for(const key of['complete_joint_qualified','complete_group_qualified','actual_property_adopted','structural_acceptance','fabrication_released'])assert.equal(analyzed.meta[key],false);
  assert.equal(analyzed.meta.rear_references.contracted_common_work_reference.maximum,.7750203178041969);
  assert.equal(analyzed.meta.mixed_common_work_reference.summary.above_one_count,3);
  assert.deepEqual(requests.filter(name=>/results(?:-v2)?\.json$/.test(name)),['eoere-v11-relocated-rear-results.json']);
  const savedFetch=globalThis.fetch;globalThis.fetch=async()=>new Response(Buffer.concat([resultsRaw,Buffer.from('\n')]));
  try{await assert.rejects(()=>loadRelocatedRearResultsScene(THREE,{},()=>assert.fail('bad results must fail before geometry loads')),/source pin differs/);}
  finally{globalThis.fetch=savedFetch;}
  context.diagnostic('1099parts/114stacks/228washers/4spacers;4wood+20same-ID poses;1075parent mesh references shared;no historical results or ignored requests.');
});
