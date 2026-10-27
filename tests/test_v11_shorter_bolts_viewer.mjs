import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {SHORTER_MODEL,SHORTER_ASSETS,validateShorterBoltDelta,loadShorterBoltScene} from '../site/eoere-v11-shorter-bolts-overlay.mjs';
import {loadV11V9EightBoltScene} from '../site/eoere-v11-v9-eight-bolt-overlay.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site'),hash=raw=>createHash('sha256').update(raw).digest('hex');
const provenanceRaw=readFileSync(path.join(site,SHORTER_ASSETS.provenance)),provenance=JSON.parse(provenanceRaw);
const sceneRaw=readFileSync(path.join(site,'eoere-v11-shorter-bolts-scene.json.gz')),scene=JSON.parse(gunzipSync(sceneRaw));
const owner=JSON.parse(readFileSync(path.join(root,provenance.owner_exemption.path))),a574=owner.authorized_hardware_changes.A574_axes;
test('the separate trial binds its own checked geometry and exact forty updates',()=>{
  assert.equal(hash(provenanceRaw),SHORTER_ASSETS.sha256);assert.equal(hash(sceneRaw),provenance.scene.sha256);
  assert.equal(hash(gunzipSync(sceneRaw)),provenance.scene.decoded_sha256);assert.equal(validateShorterBoltDelta(scene),scene);
  assert.equal(hash(readFileSync(path.join(root,provenance.geometry_receipt.path))),provenance.geometry_receipt.sha256);
  assert.equal(scene.replacements.length,20);assert.equal(scene.reuses.length,20);assert.equal(scene.removals.length,20);
  assert.equal(scene.counts.spacer_pieces,4);assert.equal(scene.part_count,1089);assert.equal(scene.all_axis_ids.length,112);
});
for(const[name,change]of[
  ['the old geometry',d=>{d.geometry_source.sha256='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7';}],
  ['an old selected length',d=>{d.stack_updates[0].selected_underhead_length_mm=190.5;}],
  ['a stale header head label',d=>{d.stack_updates.find(row=>!a574.includes(row.axis_id)).selected_head_style='socket cap';}],
  ['a retained sleeve',d=>{d.removals.pop();}],
  ['a head replaced instead of its nut',d=>{d.reuses[0].name=d.reuses[0].name.replace(/_nut$/,'_head');}],
  ['a shifted nut seat',d=>{d.reuses[0].matrix_row_major[3]+=1;}],
  ['old force data',d=>{d.force_only={maximum:.842003};}],
  ['old diagnostic flags',d=>{d.diagnostic_case_rows=32;}],
  ['an adopted actual factor',d=>{d.actual_Cg_adopted=1;}],
  ['a computed case pass',d=>{d.current_response_computed=true;}],
])test('the new trial rejects '+name,()=>{const data=structuredClone(scene);change(data);assert.throws(()=>validateShorterBoltDelta(data));});
test('routing preserves the old V11 results choice and baseline and links only the own shorter-bolt records',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');assert(html.includes('shorterBolts ? loadShorterBoltResultsScene'));
  assert(html.includes('v11 ? loadV11ResultsSceneV2'));assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  const docs=documentsForModel(SHORTER_MODEL);assert(docs.some(row=>row.path===provenance.geometry_receipt.path));
  assert(docs.some(row=>row.path=== 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/reference-review.json'));
  assert(docs.every(row=>!/owner-frame-v11\/(response-bank|reference-review)|results-v2/.test(row.path)));
  docs.forEach(row=>assert(readFileSync(path.join(root,row.path)).length));
});
test('the new geometry-only route never requests historical weight metadata',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8'),start=html.indexOf('const designLabels = '),end=html.indexOf('const categoryLabels = ',start);
  const weightLine={},weightNote={};runInNewContext(html.slice(start,end),{model:SHORTER_MODEL,isWoodJoint:true,
    woodJointModels:[[SHORTER_MODEL,'Trial']],modelSelect:{options:[{value:SHORTER_MODEL,text:'Trial'}]},weightLine,weightNote,
    excludedMass:'unused',fetch:()=>assert.fail('no old mass request')});assert.equal(weightLine.hidden,true);assert.equal(weightNote.hidden,true);
});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8'),start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
const THREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');
test('the actual public-only loader preserves1049 geometries and all112 current hardware references',async context=>{
  const previousFetch=globalThis.fetch,requests=[];let parent;
  context.after(()=>{globalThis.fetch=previousFetch;});
  globalThis.fetch=async input=>{const name=String(input);if(name.startsWith('blob:'))return previousFetch(input);
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);
    assert(target.startsWith(site+path.sep)&&/\.json(?:\.gz)?$/.test(target),'site JSON only');requests.push(path.relative(site,target));return new Response(readFileSync(target));};
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const loaded=await loadShorterBoltScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,resolveMeshPath:name=>resolveMeshPath(name,aliases)},async(t,o)=>{
    const input=await loadV11V9EightBoltScene(t,o);parent=new Map(input.parts.map(part=>[part.name,{geometry:part.geometry,path:part.path,
      vertices:part.geometry?hash(new Uint8Array(part.geometry.attributes.position.array.buffer)):null}]));return input;});
  const bolts=loaded.parts.filter(part=>part.fabrication?.kind==='bolt');assert.equal(loaded.parts.length,1089);
  assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,112);assert.equal(bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length,224);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.startsWith('spacer')).length,4);assert.equal(loaded.parts.filter(part=>part.fabrication?.kind==='screw').length,66);
  const changed=new Set([...scene.replacements,...scene.reuses].map(row=>row.name));let shared=0;
  for(const part of loaded.parts){if(!changed.has(part.name)){assert.equal(part.geometry,parent.get(part.name).geometry);assert.equal(part.path,parent.get(part.name).path);shared++;}
    assert(!part.geometry?.disposed);assert.equal(part.fabrication.analysis_reference,undefined);assert.equal(part.fabrication.conditional_force_only_reference,undefined);}
  assert.equal(shared,1049);
  for(const update of scene.stack_updates){const expected=a574.includes(update.axis_id)?165.1:76.2;
    const stack=bolts.filter(part=>part.fabrication.connection_name===update.axis_id);assert.equal(stack.length,5);
    for(const part of stack){assert.equal(part.fabrication.selected_product,a574.includes(update.axis_id)?'8093':'365');assert.equal(part.fabrication.selected_underhead_length_mm,expected);assert.equal(part.fabrication.spacer_piece_count,0);}
    const shaft=stack.find(part=>part.fabrication.hardware_role==='shaft'),direction=scene.changed_axis_bindings[update.axis_id].direction_xyz,positions=shaft.geometry.attributes.position.array;
    let low=Infinity,high=-Infinity;for(let i=0;i<positions.length;i+=3){const v=direction.reduce((s,d,k)=>s+d*positions[i+k],0);low=Math.min(low,v);high=Math.max(high,v);}
    assert(Math.abs(high-low-expected)<.15,'actual displayed short shaft extent: '+update.axis_id);
  }
  for(const row of parent.values())if(row.geometry)assert.equal(hash(new Uint8Array(row.geometry.attributes.position.array.buffer)),row.vertices);
  for(const key of['case_rows','force_only','standard_cg','family_maxima','member_vector_maxima','load_contract','weight_response'])assert.equal(loaded.meta[key],undefined);
  assert.equal(loaded.meta.geometry_only,true);assert.equal(loaded.meta.analysis_pending,true);assert.equal(loaded.meta.current_response_computed,false);
  assert.equal(loaded.meta.complete_connection_capacity,null);assert.equal(loaded.meta.actual_Cg_adopted,null);
  assert(!requests.some(name=>/results(?:-v2)?\.json$/.test(name)),'the analyzed V11 parent is never fetched');
  context.diagnostic('1089parts/112stacks/224washers/4spacers;1049 shared geometry references;20 current shaft extents checked; no inherited results.');
});
