import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {MATCHING_REAR_MODEL,MATCHING_REAR_ASSETS,validateMatchingRearDelta,applyMatchingRearDelta,validateMatchingRearResults,matchingRearStatus,loadMatchingRearScene} from '../site/eoere-v11-matching-rear-bolts-overlay.mjs';
import {loadShorterBoltScene} from '../site/eoere-v11-shorter-bolts-overlay.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';
import {decodeTypedArray} from '../site/wood-joints-overlay.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site'),hash=raw=>createHash('sha256').update(raw).digest('hex');
const provenanceRaw=readFileSync(path.join(site,MATCHING_REAR_ASSETS.provenance)),provenance=JSON.parse(provenanceRaw);
const sceneRaw=readFileSync(path.join(root,provenance.scene.path)),scene=JSON.parse(gunzipSync(sceneRaw));
const resultsRaw=readFileSync(path.join(root,provenance.results.path)),results=JSON.parse(resultsRaw);
const completion=JSON.parse(readFileSync(path.join(root,results.sources.reference_completion.path)));
test('the separate114 trial binds own checked sources and only four wood meshes plus10translated roles',()=>{
  assert.equal(hash(provenanceRaw),MATCHING_REAR_ASSETS.sha256);assert.equal(hash(sceneRaw),provenance.scene.sha256);
  assert.equal(hash(gunzipSync(sceneRaw)),provenance.scene.decoded_sha256);assert.equal(hash(resultsRaw),provenance.results.sha256);
  assert.equal(validateMatchingRearDelta(scene),scene);assert.equal(validateMatchingRearResults(results),results);
  for(const ref of[provenance.geometry_receipt,provenance.parent_provenance,...Object.values(results.sources)])assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  assert.equal(scene.replacements.length,4);assert.equal(scene.reuses.length,10);assert.equal(scene.all_axis_ids.length,114);
  for(const[key,row]of Object.entries(completion.families.outputs))assert.deepEqual(results.family_references[key],{maximum:row.maximum,above_one_count:row.above_one_count});
  assert.deepEqual(results.rear.maximum_case_reference_bracket,completion.rear.maximum_case_reference_bracket);
  assert.equal(results.trial_selected,false);assert.equal(results.actual_Cg_adopted,null);assert.equal(results.complete_connection_capacity,null);
});
for(const[label,mutate]of[
  ['the old112 geometry',d=>{d.geometry_source.sha256='73ce1f19ce97959d3867984cc813c178895b50212128fce6a976548ad6bce4c8';}],
  ['a missing wood receiver',d=>{d.replacements.pop();}],
  ['a missing added hardware role',d=>{d.reuses.pop();}],
  ['a smaller new diameter',d=>{d.new_axis_bindings[d.new_axis_ids[0]].diameter_mm=9.525;}],
  ['a wrong product',d=>{d.new_stack_updates[0].selected_product='8093';}],
  ['a copied sleeve',d=>{d.new_stack_updates[0].spacer_piece_count=1;}],
  ['a scaled reuse',d=>{d.reuses[0].matrix_row_major[0]=2;}],
  ['the other side template',d=>{d.reuses[0].source_parent_name=d.reuses[0].source_parent_name.replace('_left_','_right_');}],
  ['a duplicated physical axis',d=>{d.all_axis_ids[1]=d.all_axis_ids[0];}],
  ['automatic selection',d=>{d.trial_selected=true;}],
])test('the scene rejects '+label,()=>{const data=structuredClone(scene);mutate(data);assert.throws(()=>validateMatchingRearDelta(data));});
for(const[label,mutate]of[
  ['old112 forces',d=>{d.sources.response_bank.sha256='0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c';}],
  ['an unadmitted replay',d=>{d.cases[0].both_independent_replays_admitted=false;}],
  ['a historical field path',d=>{d.cases[0].field.path='old/field.json';}],
  ['shared replay bytes',d=>{d.cases[0].independent_replay.sha256=d.cases[0].field.sha256;}],
  ['a relaxed load',d=>{d.load_contract.downward_multiplier=1;}],
  ['an adopted Cg',d=>{d.actual_Cg_adopted=1;}],
  ['a full joint pass',d=>{d.complete_joint_qualified=true;}],
  ['a nonfinite family reference',d=>{d.family_references.timber_net_shear_torsion.maximum.index=Infinity;}],
  ['a rear reference promoted to capacity',d=>{d.rear.projected_summary.full_NDS_connection_capacity=1;}],
  ['weight interpolation',d=>{d.weight_interpolation_available=true;}],
])test('the own results reject '+label,()=>{const data=structuredClone(results);mutate(data);assert.throws(()=>validateMatchingRearResults(data));});
test('explicit routing and documents preserve the original112 and selected default',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');assert(html.includes('matchingRear ? loadMatchingRearScene : shorterBolts ? loadShorterBoltResultsScene'));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));assert(html.includes("'Unselected matching rear bolts · 114 stacks · own references'"));
  for(const ref of[provenance.geometry_receipt,...Object.values(results.sources)])assert(documentsForModel(MATCHING_REAR_MODEL).some(row=>row.path===ref.path));
  documentsForModel(MATCHING_REAR_MODEL).forEach(row=>assert(readFileSync(path.join(root,row.path)).length));
  const start=html.indexOf('const designLabels = '),end=html.indexOf('const categoryLabels = ',start),weightLine={},weightNote={};
  runInNewContext(html.slice(start,end),{model:MATCHING_REAR_MODEL,isWoodJoint:true,woodJointModels:[[MATCHING_REAR_MODEL,'Trial']],modelSelect:{options:[{value:MATCHING_REAR_MODEL,text:'Trial'}]},
    weightLine,weightNote,excludedMass:'unused',fetch:()=>assert.fail('no old weight fetch')});assert.equal(weightLine.hidden,true);assert.equal(weightNote.hidden,true);
  const status=matchingRearStatus(results);for(const value of['Unselected','0.946179','0.833916','0.410813','0.409168','0.682571','0.676721','0.145 mm','full joint capacity unqualified'])assert(status.includes(value));
  assert.doesNotMatch(status,/0\.965879|0\.439253|matched analysis pending|complete joint pass/);
});
test('the optional revision-index viewer joins exact assets without selecting the114trial',()=>{
  const index=JSON.parse(readFileSync(path.join(root,'docs/bolted-frame-development/development-revisions.json')));
  const trial=index.owner_authorized_matching_rear_bolt_trial;
  assert.equal(trial.revision,'v11-matching-rear-bolts-v1');assert.equal(trial.trial_selected,false);
  assert.deepEqual(trial.geometry_receipt,provenance.geometry_receipt);assert.deepEqual(trial.response_bank,results.sources.response_bank);
  assert.deepEqual(trial.reference_completion,results.sources.reference_completion);
  for(const[key,value]of Object.entries(trial.counts))assert.equal(value,provenance.counts[key]);
  assert.equal(trial.actual_Cg,null);assert.equal(trial.actual_Cdelta,null);
  for(const key of['complete_joint_qualified','structural_acceptance','purchase_authorized','fabrication_released','climbing_released'])assert.equal(trial[key],false);
  const viewer=trial.viewer;assert.equal(viewer.model,MATCHING_REAR_MODEL);assert.match(viewer.url,/model=eoere-v11-matching-rear-bolts-preview/);
  const paths={provenance:'site/'+MATCHING_REAR_ASSETS.provenance,scene:provenance.scene.path,results:provenance.results.path,
    overlay:'site/eoere-v11-matching-rear-bolts-overlay.mjs',publisher:'scripts/publish_v11_matching_rear_viewer.py'};
  for(const[key,name]of Object.entries(paths)){assert.equal(viewer[key].path,name);assert.equal(viewer[key].sha256,hash(readFileSync(path.join(root,name))));}
  assert.notEqual(index.geometry.viewer,MATCHING_REAR_MODEL,'current development selection remains separate');
});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8'),start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
const THREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');
test('actual public-only loader keeps1085old meshes and adds two exact current half-inch stacks',async context=>{
  const previous=globalThis.fetch,requests=[];let parent,before;
  context.after(()=>{globalThis.fetch=previous;});
  globalThis.fetch=async input=>{const name=String(input);if(name.startsWith('blob:'))return previous(input);
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);assert(target.startsWith(site+path.sep),'site inputs only');
    requests.push(path.relative(site,target));return new Response(readFileSync(target));};
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const loaded=await loadMatchingRearScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,resolveMeshPath:name=>resolveMeshPath(name,aliases)},async(t,o)=>{
    parent=await loadShorterBoltScene(t,o);before=new Map(parent.parts.map(part=>[part.name,{geometry:part.geometry,path:part.path,
      vertices:part.geometry?hash(new Uint8Array(part.geometry.attributes.position.array.buffer)):null}]));return parent;});
  assert.equal(loaded.parts.length,1099);const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Set(scene.replacements.map(row=>row.name));let shared=0;
  for(const part of loaded.parts){if(old.has(part.name)&&!changed.has(part.name)){assert.equal(part.geometry,old.get(part.name).geometry);assert.equal(part.path,old.get(part.name).path);shared++;}
    assert.equal(part.fabrication.analysis_reference,undefined);assert(!part.geometry?.disposed);assert(!part.fabrication.description.includes('matched analysis pending'));}
  assert.equal(shared,1085);const bolts=loaded.parts.filter(part=>part.fabrication.kind==='bolt');assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,114);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length,228);assert.equal(bolts.filter(part=>part.fabrication.hardware_role.startsWith('spacer')).length,4);
  for(const id of scene.new_axis_ids){const stack=bolts.filter(part=>part.fabrication.connection_name===id);assert.equal(stack.length,5);
    stack.forEach(part=>{assert.equal(part.fabrication.selected_product,'G0340956');assert.equal(Number(part.fabrication.selected_diameter_mm),12.7);assert.equal(Number(part.fabrication.spacer_piece_count),0);});
    const shaft=stack.find(part=>part.fabrication.hardware_role==='shaft');shaft.geometry.computeBoundingBox();const b=shaft.geometry.boundingBox;assert(Math.abs(b.max.x-b.min.x-215.9)<.2);}
  for(const row of scene.reuses){const source=old.get(row.source_parent_name);assert.equal(hash(new Uint8Array(source.geometry.attributes.position.array.buffer)),before.get(source.name).vertices,'retained source template must not move');}
  assert.equal(loaded.meta.current_response_computed,true);assert.equal(loaded.meta.trial_selected,false);assert.equal(loaded.meta.actual_Cg_adopted,null);assert.equal(loaded.meta.complete_connection_capacity,null);
  assert.equal(loaded.meta.case_rows.length,6);assert.equal(loaded.meta.independent_replays,12);assert.equal(loaded.meta.maximum_gradient_inf_N,2.246134017003243e-6);
  for(const key of['weight_response','force_only','member_vector_maxima','row_bounds','standard_cg'])assert.equal(loaded.meta[key],undefined);
  assert(!requests.some(name=>/^(eoere-v11-results(?:-v2)?|eoere-v11-shorter-bolts-results)\.json$/.test(name)),'no old results layer is loaded');
  const translated=structuredClone(scene);translated.reuses[0].matrix_row_major[7]+=1;
  const topologies=new Map(Object.entries(scene.triangle_topologies).map(([key,row])=>[key,{...row,
    indices:decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count).values}]));
  assert.throws(()=>applyMatchingRearDelta(THREE,parent,translated,topologies),/physical line/,'the actual wrong translation must be rejected after decoding all four wood meshes');
  context.diagnostic('1099parts/114stacks/228washers/4spacers;1085old geometry refs shared,10hardware clones,4new wood meshes; own6+12results only.');
});
