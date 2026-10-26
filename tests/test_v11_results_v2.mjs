import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import test from 'node:test';
import {V11_RESULTS_V2_ASSET,validateV11ResultsV2,applyV11ResultsV2,loadV11ResultsSceneV2} from '../site/eoere-v11-results-v2.mjs';
import {V11_RESULTS_ASSET,v11ResultsStatus} from '../site/eoere-v11-results.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),raw=readFileSync(path.join(root,V11_RESULTS_V2_ASSET.path)),data=JSON.parse(raw);
const base=JSON.parse(readFileSync(path.join(root,V11_RESULTS_ASSET.path))),hash=raw=>createHash('sha256').update(raw).digest('hex');
test('the additive update joins exact public standard-Cg and mixed-plane summaries',()=>{
  assert.equal(hash(raw),V11_RESULTS_V2_ASSET.sha256);assert.equal(validateV11ResultsV2(data),data);
  const source=JSON.parse(readFileSync(path.join(root,data.standard_cg_source.path)));
  assert.equal(hash(readFileSync(path.join(root,data.standard_cg_source.path))),data.standard_cg_source.sha256);
  assert.equal(hash(readFileSync(path.join(root,data.criterion_source.path))),data.criterion_source.sha256);
  assert.equal(data.standard_cg.aggregate_directional_index,source.maxima.aggregate_directional_index.aggregate_directional_index);
  assert.equal(data.standard_cg.Fe90_net_floor_index,source.maxima.aggregate_direction_independent_floor_index.aggregate_direction_independent_floor_index);
  assert.equal(data.standard_cg.Fe90_net_floor_flags,source.above_one_counts.aggregate_direction_independent_floor_index);
});
for(const[name,change]of[
  ['net floor replaced by gross result',d=>{d.standard_cg.Fe90_net_floor_index=.8420030182968952;}],
  ['five net flags removed',d=>{d.standard_cg.Fe90_net_floor_flags=0;}],
  ['actualCg selected',d=>{d.standard_cg.actual_Cg_selected=true;}],
  ['raw-port bounds called method failures',d=>{d.preserved_raw_port_bounds.conservative_inconclusive_not_new_method_failures=false;}],
  ['full mixed capacity inferred',d=>{d.mixed_plane_references.complete_capacity_qualified=true;}],
  ['a foreign preceding result',d=>{d.base_results.sha256='0'.repeat(64);}],
  ['fabrication release',d=>{d.fabrication_released=true;}],
])test('method update rejects '+name,()=>{const d=structuredClone(data);change(d);assert.throws(()=>validateV11ResultsV2(d));});

const fixture=()=>({parts:Array.from({length:1109},(_,i)=>({geometry:{source:i},fabrication:{unsupported_mixed_capacity:i<24}})),
  design:{key:data.model},meta:{active_results_record:V11_RESULTS_ASSET,status:v11ResultsStatus(base)}});
test('the method layer preserves geometry and separates the three numerical methods',()=>{
  const before=fixture(),after=applyV11ResultsV2(before,data);
  before.parts.forEach((part,i)=>assert.equal(after.parts[i].geometry,part.geometry));
  assert.match(after.meta.status,/aggregate and individual\/Cg maxima 0\.842003, zero flags/);
  assert.match(after.meta.status,/Fe90 net-lateral floor maximum 1\.256360, five flags/);
  assert.match(after.meta.status,/Prior raw-port bound 2\.208084 and 21 flags remain conservative and inconclusive/);
  assert.match(after.parts[0].fabrication.analysis_reference,/Full mixed\/group\/axial\/couple capacity remains unsupported/);
  assert.equal(after.parts[0].fabrication.conditional_force_only_reference,undefined);
  assert.match(before.meta.status,/Fresh 92 ksi row-bound/);
});
test('the V2 loader adds only its tiny source-pinned record before the existing loader',async context=>{
  const old=globalThis.fetch;context.after(()=>{globalThis.fetch=old;});
  globalThis.fetch=async url=>{assert.equal(fileURLToPath(url),path.join(root,V11_RESULTS_V2_ASSET.path));return new Response(raw);};
  const result=await loadV11ResultsSceneV2({}, {}, async()=>fixture());assert.equal(result.meta.standard_cg.Fe90_net_floor_flags,5);
  globalThis.fetch=async()=>new Response('changed');await assert.rejects(loadV11ResultsSceneV2({}, {},async()=>assert.fail()),/bytes changed/);
});
test('V1 evidence and default routing remain preserved beside the explicit V2 choice',()=>{
  assert.equal(hash(readFileSync(path.join(root,'site/eoere-v11-results.json'))),'d729953d54f9b7f989c5155e115758cbd4845bff0795ab27a496b3188c9e2aaf');
  assert.equal(hash(readFileSync(path.join(root,'site/eoere-v11-results.mjs'))),'0a4111d491e4316e5b79da2d82def283b4dee556bdeeb9b6a75be35f8f346bad');
  const html=readFileSync(path.join(root,'site/index.html'),'utf8');assert(html.includes('v11 ? loadV11ResultsSceneV2'));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
});
