import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {SHORTER_RESULTS_ASSET,validateShorterBoltResults,applyShorterBoltResults,shorterBoltResultsStatus,loadShorterBoltResultsScene} from '../site/eoere-v11-shorter-bolts-results.mjs';
import {loadShorterBoltScene} from '../site/eoere-v11-shorter-bolts-overlay.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site'),hash=raw=>createHash('sha256').update(raw).digest('hex');
const raw=readFileSync(path.join(root,SHORTER_RESULTS_ASSET.path)),data=JSON.parse(raw);
const review=JSON.parse(readFileSync(path.join(root,data.sources.reference_review.path)));
const bank=JSON.parse(readFileSync(path.join(root,data.sources.response_bank.path)));
test('the compact results are an exact own-source projection with all seven flag families',()=>{
  assert.equal(hash(raw),SHORTER_RESULTS_ASSET.sha256);assert.equal(validateShorterBoltResults(data),data);
  Object.values(data.sources).forEach(ref=>assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256));
  assert.deepEqual(data.viewer_presentation,review.viewer_presentation);assert.deepEqual(data.member_vector_maxima,review.member_vector_maxima);
  assert.deepEqual(data.family_maxima,review.family_maxima);assert.equal(data.viewer_presentation.reference_flags.length,7);
  assert.equal(data.viewer_presentation.reference_flags.reduce((sum,row)=>sum+row.count,0),110);
  for(const row of data.cases){const own=bank.cases.find(item=>item.case_id===row.case_id);
    for(const key of['field','independent_replay','independent_plywood_replay','gradient_inf_N'])assert.deepEqual(row[key],own[key]);}
  assert.equal(data.actual_Cg_adopted,null);assert.equal(data.actual_Cdelta_adopted,null);assert.equal(data.complete_connection_capacity,null);
});
for(const[label,mutate]of[
  ['the old geometry',d=>{d.geometry_sha256='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7';}],
  ['the old force bank',d=>{d.sources.response_bank.sha256='482d8e5cf5eec0566a7eb637666137350cbf90f1674f909241c78a103f615963';}],
  ['an unbound review',d=>{d.sources.reference_review.sha256='a'.repeat(64);}],
  ['a relaxed load',d=>{d.load_contract.downward_multiplier=1;}],
  ['a duplicated case',d=>{d.cases[1]=structuredClone(d.cases[0]);}],
  ['an unadmitted replay',d=>{d.cases[0].both_independent_replays_admitted=false;}],
  ['an old replay path',d=>{d.cases[0].independent_replay.path='old/replay.json';}],
  ['shared field and replay bytes',d=>{d.cases[0].independent_replay.sha256=d.cases[0].field.sha256;}],
  ['a nonfinite member index',d=>{d.member_vector_maxima.base_side_left.index=Infinity;}],
  ['an omitted diagnostic count',d=>{delete d.viewer_presentation.reference_flags[0].count;}],
  ['an actual group factor',d=>{d.actual_Cg_adopted=1;}],
  ['a complete joint pass',d=>{d.complete_joint_qualified=true;}],
  ['weight interpolation',d=>{d.weight_interpolation_available=true;}],
])test('the results layer rejects '+label,()=>{const changed=structuredClone(data);mutate(changed);assert.throws(()=>validateShorterBoltResults(changed));});
test('status names current source values and keeps diagnostic and scenario families distinct',()=>{
  const status=shorterBoltResultsStatus(data);assert(status.startsWith(review.viewer_presentation.status));
  for(const row of Object.values(review.member_vector_maxima))assert(status.includes(row.index.toFixed(6)));
  for(const row of review.viewer_presentation.reference_flags)assert(status.includes(row.label+': '+row.count));
  assert.match(status,/Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1/);
  assert.match(status,/full joint qualification remain open/);assert.doesNotMatch(status,/0\.965029|0\.842003|1\.256360|complete joint pass/);
});
test('only the shorter route activates own results and its own evidence menu',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');assert(html.includes('shorterBolts ? loadShorterBoltResultsScene'));
  assert(html.includes('v11 ? loadV11ResultsSceneV2'));assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  const docs=documentsForModel(data.model);
  for(const ref of Object.values(data.sources))assert(docs.some(row=>row.path===ref.path));
  assert(docs.some(row=>row.path===review.numerical_flag_inventory.path));docs.forEach(row=>assert(readFileSync(path.join(root,row.path)).length));
  assert(docs.every(row=>!/owner-frame-v11\/(response-bank|reference-review)\.json/.test(row.path)));
});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8'),start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
const THREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');
test('the actual public loader adds current results over1089 unchanged geometry references',async context=>{
  const previous=globalThis.fetch,requests=[];let parent;
  context.after(()=>{globalThis.fetch=previous;});
  globalThis.fetch=async input=>{const name=String(input);if(name.startsWith('blob:'))return previous(input);
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);assert(target.startsWith(site+path.sep),'public site inputs only');
    requests.push(path.relative(site,target));return new Response(readFileSync(target));};
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const result=await loadShorterBoltResultsScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,resolveMeshPath:name=>resolveMeshPath(name,aliases)},async(t,o)=>{
    parent=await loadShorterBoltScene(t,o);return parent;});
  assert.equal(result.parts.length,1089);result.parts.forEach((part,i)=>{assert.equal(part.geometry,parent.parts[i].geometry);assert.equal(part.path,parent.parts[i].path);});
  const bolts=result.parts.filter(part=>part.fabrication?.kind==='bolt');assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,112);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.startsWith('spacer')).length,4);
  assert.equal(result.meta.geometry_only,false);assert.equal(result.meta.analysis_pending,false);assert.equal(result.meta.current_response_computed,true);
  assert.equal(result.meta.case_rows.length,6);assert.equal(result.meta.independent_replays,12);assert.equal(result.meta.maximum_gradient_inf_N,bank.maximum_gradient_inf_N);
  assert.deepEqual(result.meta.reference_flags,review.viewer_presentation.reference_flags);assert.equal(result.meta.actual_Cg_adopted,null);
  assert.equal(result.meta.complete_connection_capacity,null);assert.equal(result.meta.structural_acceptance,false);
  assert(result.parts.every(part=>part.fabrication.analysis_reference===undefined),'empty own axis mapping cannot inherit the old88/24 split');
  assert(parent.parts.every(part=>part.fabrication.description.includes('matched analysis pending')),'geometry-only parent stays standalone');
  assert(result.parts.every(part=>!part.fabrication.description.includes('matched analysis pending')));
  for(const key of['force_only','row_bounds','standard_cg','weight_response'])assert.equal(result.meta[key],undefined);
  assert(!requests.some(name=>/^eoere-v11-results(?:-v2)?\.json$/.test(name)));assert(requests.includes('eoere-v11-shorter-bolts-results.json'));
  const unknown=structuredClone(data);unknown.viewer_presentation.axis_reference_texts.unknown='Unsupported fixture';
  assert.throws(()=>applyShorterBoltResults(parent,unknown));assert.throws(()=>applyShorterBoltResults(result,data));
});
test('changed result bytes are rejected before any geometry is loaded',async context=>{
  const previous=globalThis.fetch;context.after(()=>{globalThis.fetch=previous;});
  const changed=structuredClone(data);changed.member_vector_maxima.base_side_left.index=0;
  globalThis.fetch=async()=>new Response(JSON.stringify(changed));
  await assert.rejects(()=>loadShorterBoltResultsScene(THREE,{},()=>assert.fail('tampered presentation must be rejected before geometry loading')),/bytes changed/);
});
