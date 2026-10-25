import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {CENTER_FAR_ROW_MODEL,CENTER_FAR_ROW_ASSETS,validateCenterFarRowScene,validateCenterFarRowProvenance,loadCenterFarRowScene}
  from '../site/eoere-center-far-row-overlay.mjs';
import {loadPackerFreeResultsScene} from '../site/eoere-packer-free-results.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site');
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const raw=readFileSync(path.join(site,CENTER_FAR_ROW_ASSETS.provenance)),provenance=JSON.parse(raw);
const sceneRaw=readFileSync(path.join(site,'eoere-center-far-row-scene.json.gz')),scene=JSON.parse(gunzipSync(sceneRaw));

test('the public trial binds one new checked rail and its own six-case results',()=>{
  assert.equal(hash(raw),CENTER_FAR_ROW_ASSETS.sha256);assert.equal(hash(sceneRaw),provenance.scene.sha256);
  assert.equal(validateCenterFarRowScene(scene),scene);assert.equal(validateCenterFarRowProvenance(provenance),provenance);
  assert.equal(scene.replacements.length,1);assert.equal(scene.removals.length,20);
  assert.equal(provenance.sources.response_bank.sha256,'0175c7882231a24a35fd44b15b21919143f6c6a2abc9e91e623a9b6215c70bdd');
  assert.equal(provenance.sources.reference_provenance.sha256,'9b8608dc66ec0e41aa12077ced0a6d92ab8487acc1337a69bd12f343097c96ac');
});
for(const[name,change]of[
  ['a current-112 bank',d=>{d.sources.response_bank.sha256='976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3';}],
  ['a 112 vector reference',d=>{d.declared_vector_references.base_side_left.index=.914624720328145;}],
  ['a 112 family reference',d=>{d.declared_family_maxima.reduced_connection_axial_bending.index=.9908139820336671;}],
  ['a missing replay',d=>{d.cases[0].both_independent_replays_admitted=false;}],
  ['duplicated field bytes',d=>{d.cases[1].field.sha256=d.cases[0].field.sha256;}],
  ['another case replay',d=>{d.cases[0].independent_replay.path=d.cases[1].independent_replay.path;}],
  ['a changed applied load',d=>{d.load_contract.horizontal_force_N=250;}],
  ['a relaxed gate',d=>{d.admission_gate_N=1e-4;}],
  ['an adopted diagnostic factor',d=>{d.actual_Cg_adopted=.5;}],
  ['completed connection audits',d=>{d.complete_connection_audits_finished=true;}],
  ['candidate adoption',d=>{d.geometry_adopted=true;}],
  ['climbing release',d=>{d.climbing_released=true;}],
])test('unselected own provenance rejects '+name,()=>{const d=structuredClone(provenance);change(d);assert.throws(()=>validateCenterFarRowProvenance(d));});
for(const[name,change]of[
  ['a retained omitted shaft',d=>{d.removals.pop();}],
  ['an unrelated stack removal',d=>{d.removals[0]='eoere_bolt_022_shaft';}],
  ['the current 112 rail solid',d=>{d.replacements[0].source.sha256='d893c7c1d75671da140017b13eb32817a48e151455e5cd58904fbbced72ed903';}],
])test('the patch rejects '+name,()=>{const d=structuredClone(scene);change(d);assert.throws(()=>validateCenterFarRowScene(d));});

test('the new selector is unselected and preserves the default and current 112 entry',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');
  assert(html.includes("['"+CENTER_FAR_ROW_MODEL+"', 'Unselected trial · center far rows · 108 bolts']"));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert(html.includes("['eoere-packer-free-standard-stock-preview', 'Packer-free 4×6 frame · 112 bolts · own references · development']"));
  assert(html.includes('const selectedSceneLoader = packerFree ? loadPackerFreeResultsScene : sceneLoader;'));
  assert.equal(hash(readFileSync(path.join(site,'eoere-packer-free-results.json'))),'5b78a854d61d0e15dd7ddf84cb7c8b70e052443c4e79571d429158e970d1b6fc');
  assert.equal(hash(readFileSync(path.join(site,'eoere-packer-free-results.mjs'))),'6c5805a33229baa959fa28e11fb855e5e959d40a9746e1384a13de74be765e23');
  for(const row of documentsForModel(CENTER_FAR_ROW_MODEL))assert(readFileSync(path.join(root,row.path)).length);
});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8');
const start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
assert(start>=0&&end>start);const THREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');

test('the actual public-only 108 loader preserves 1104 shared geometries and replaces only the rail',async context=>{
  const originalFetch=globalThis.fetch,requests=[];let parent;
  context.after(()=>{globalThis.fetch=originalFetch;});
  globalThis.fetch=async input=>{
    const name=String(input);if(name.startsWith('blob:'))return originalFetch(input);
    assert(!/^[a-z][a-z0-9+.-]*:/i.test(name)||name.startsWith('file:'),'no network');
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);
    assert(target.startsWith(site+path.sep)&&/\.json(?:\.gz)?$/.test(target),'public site JSON only: '+name);
    requests.push(path.relative(site,target));return new Response(readFileSync(target));
  };
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const loaded=await loadCenterFarRowScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,
    resolveMeshPath:name=>resolveMeshPath(name,aliases)},async(three,options)=>{
      const result=await loadPackerFreeResultsScene(three,options);
      parent=new Map(result.parts.map(part=>[part.name,{geometry:part.geometry,
        vertices:part.geometry?hash(new Uint8Array(part.geometry.attributes.position.array.buffer)):null}]));return result;
    });
  assert.equal(loaded.parts.length,1105);assert.equal(loaded.design.key,CENTER_FAR_ROW_MODEL);
  assert.equal(loaded.parts.filter(part=>part.fabrication?.kind==='screw').length,66);
  assert.equal(loaded.parts.filter(part=>part.fabrication?.kind==='bracket').length,24);
  const bolts=loaded.parts.filter(part=>part.fabrication?.kind==='bolt');
  assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,108);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length,216);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.startsWith('spacer')).length,40);
  assert(!loaded.parts.some(part=>scene.removals.includes(part.name)));
  for(const part of loaded.parts){
    if(part.name==='base_rail_top')assert.notEqual(part.geometry,parent.get(part.name).geometry);
    else assert.equal(part.geometry,parent.get(part.name).geometry,'unchanged source mesh retained: '+part.name);
    assert(!part.geometry?.disposed);assert.doesNotMatch(part.fabrication?.description||'',/Own 112|results pending/);
  }
  for(const row of parent.values())if(row.geometry)assert.equal(hash(new Uint8Array(row.geometry.attributes.position.array.buffer)),row.vertices);
  assert.equal(loaded.meta.geometry_sha256,provenance.geometry_sha256);assert.equal(loaded.meta.unselected_trial,true);
  assert.equal(loaded.meta.geometry_adopted,false);assert.equal(loaded.meta.complete_connection_audits_finished,false);
  assert.equal(loaded.meta.portable_sources.response_bank.sha256,provenance.sources.response_bank.sha256);
  assert.equal(loaded.meta.active_results_record,undefined);assert.equal(loaded.meta.actual_Cg_adopted,null);
  assert.equal(loaded.meta.complete_connection_capacity,null);assert.equal(loaded.meta.structural_acceptance,false);
  assert.deepEqual(loaded.meta.declared_vector_references,provenance.declared_vector_references);
  assert.equal(loaded.meta.case_rows[0].field.sha256,provenance.cases[0].field.sha256);
  assert.equal(loaded.meta.diagnostic_case_rows,15);assert.equal(loaded.meta.diagnostic_components,8);
  assert(requests.includes('eoere-center-far-row-scene.json.gz'));context.diagnostic('1105 parts / 108 stacks / 216 washers / 40 spacers; one new rail, 1104 shared geometry references, no ignored runtime fetches.');
});
