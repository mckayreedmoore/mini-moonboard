import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import test from 'node:test';
import {validateV11Results,applyV11Results,loadV11ResultsScene,v11ResultsStatus,V11_RESULTS_ASSET} from '../site/eoere-v11-results.mjs';
import {V11_MODEL,V11_ASSETS} from '../site/eoere-v11-v9-eight-bolt-overlay.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),hash=raw=>createHash('sha256').update(raw).digest('hex');
const raw=readFileSync(path.join(root,V11_RESULTS_ASSET.path)),data=JSON.parse(raw);
const source=name=>JSON.parse(readFileSync(path.join(root,data.sources[name].path)));

test('the compact current record projects its own public bank, member review and all88 axis maxima',()=>{
  assert.equal(hash(raw),V11_RESULTS_ASSET.sha256);assert.equal(validateV11Results(data),data);
  for(const ref of Object.values(data.sources))assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  const bank=source('response_bank'),review=source('reference_review'),property=source('property_comparison'),rows=source('row_comparison');
  assert.deepEqual(data.cases,bank.cases);assert.deepEqual(data.load_contract,bank.load_contract);
  assert.deepEqual(data.member_vector_maxima,review.member_vector_maxima);assert.deepEqual(data.family_maxima,review.family_maxima);
  const expected=property.all_two_media_axis_maxima.map(({explicit92_maximum:r})=>({axis_id:r.axis_id,case_id:r.case_id,index:r.demand_over_Z,
    governing_mode:r.governing_mode,class_code:r.class_code,conditional_steel_Fe_unassigned:r.actual_candidate_steel_Fe_psi===null}));
  assert.deepEqual(data.axis_force_only_maxima,[...expected].sort((a,b)=>a.axis_id.localeCompare(b.axis_id)));
  assert.deepEqual(data.unsupported_mixed_axes,[...property.unsupported_mixed_axes].sort());
  assert.equal(data.row_bounds.conditional_property_maximum,rows.explicit92_maximum_inconclusive_partition_bound.conditional_index_upper);
  assert.equal(data.row_bounds.inconclusive_flag_rows,rows.explicit92_inconclusive_flags.length);
  assert.equal(data.row_bounds.below_one_rows,231);assert.equal(data.row_bounds.complete_group_pass,null);
});

for(const[name,change]of[
  ['old112 geometry',d=>{d.geometry_sha256='9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde';}],
  ['a prior force bank',d=>{d.sources.response_bank.sha256='976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3';}],
  ['an old analysis geometry',d=>{d.analysis_geometry.sha256='0'.repeat(64);}],
  ['a changed weight',d=>{d.load_contract.weight_lb=300;}],
  ['weight interpolation',d=>{d.weight_interpolation_available=true;}],
  ['one missing replay',d=>{d.cases[0].both_independent_replays_admitted=false;}],
  ['duplicated field bytes',d=>{d.cases[1].field.sha256=d.cases[0].field.sha256;}],
  ['another case replay path',d=>{d.cases[0].independent_replay.path=d.cases[1].independent_replay.path;}],
  ['an old member index',d=>{d.member_vector_maxima.base_side_left.index=.914624720328145;}],
  ['a missing unsupported mixed axis',d=>{d.unsupported_mixed_axes.pop();}],
  ['an unsupported axis assigned a mapped index',d=>{d.axis_force_only_maxima[0].axis_id=d.unsupported_mixed_axes[0];}],
  ['a nonfinite axis index',d=>{d.axis_force_only_maxima[0].index=NaN;}],
  ['the generic45 maximum as current',d=>{d.force_only.conditional_property_maximum=1.189314587548981;}],
  ['the old generic row maximum as current',d=>{d.row_bounds.conditional_property_maximum=2.665863124575772;}],
  ['row-bound flags called failures',d=>{d.row_bounds.above_one_is_inconclusive=false;}],
  ['complete group acceptance',d=>{d.row_bounds.complete_group_pass=true;}],
  ['adopted actualFyb',d=>{d.actual_Fyb_adopted=92000;}],
  ['complete joint capacity',d=>{d.complete_connection_capacity=1000;}],
  ['fabrication release',d=>{d.fabrication_released=true;}],
])test('current results reject '+name,()=>{const d=structuredClone(data);change(d);assert.throws(()=>validateV11Results(d));});

function fixture(){
  const ids=[...data.axis_force_only_maxima.map(row=>row.axis_id),...data.unsupported_mixed_axes];
  return {parts:Array.from({length:1109},(_,i)=>({name:'part_'+i,geometry:{source:i},fabrication:{kind:i<112?'bolt':'timber',
    connection_name:ids[i],description:'Geometry only; analysis pending. Actual fit unqualified.'}})),
    design:{key:V11_MODEL,qualified_for_design:false},meta:{geometry_sha256:data.geometry_sha256,layout_sha256:data.geometry_receipt.sha256,
      provenance_sha256:V11_ASSETS.sha256,geometry_only:true,analysis_pending:true,planning_mass_kg:null,portable_sources:{}}};
}

test('the wrapper retains all geometry identities and gives mixed axes no fabricated index',()=>{
  const original=fixture(),loaded=applyV11Results(original,data);
  for(let i=0;i<original.parts.length;i++)assert.equal(loaded.parts[i].geometry,original.parts[i].geometry);
  assert.equal(original.meta.geometry_only,true);assert.equal(original.meta.analysis_pending,true);
  assert.equal(loaded.meta.geometry_only,false);assert.equal(loaded.meta.analysis_pending,false);
  assert.equal(loaded.meta.actual_Cg_adopted,null);assert.equal(loaded.meta.actual_Fyb_adopted,null);assert.equal(loaded.meta.complete_connection_capacity,null);
  const mapped=loaded.parts.find(p=>p.fabrication.connection_name==='lumber_leg_bolt_left_1').fabrication;
  assert.equal(mapped.conditional_force_only_reference.index,.8420030182968952);
  assert.match(mapped.analysis_reference,/Fixed 250 lb conditional force-only index 0\.842003/);
  const mixed=loaded.parts.find(p=>p.fabrication.connection_name===data.unsupported_mixed_axes[0]).fabrication;
  assert.equal(mixed.conditional_force_only_reference,null);assert.match(mixed.analysis_reference,/capacity mapping unsupported/);
  assert(!loaded.parts.some(p=>/analysis pending/.test(p.fabrication.description)));
  assert.match(v11ResultsStatus(data),/21 bounds across 10 interfaces remain inconclusive/);
  assert.match(v11ResultsStatus(data),/24 mixed axes and complete connections remain unresolved/);
  original.meta.geometry_sha256='0'.repeat(64);assert.throws(()=>applyV11Results(original,data));
});

test('the results loader fetches only its compact own record before the unchanged geometry loader',async context=>{
  const old=globalThis.fetch,options={same:true},three={},scene=fixture();context.after(()=>{globalThis.fetch=old;});
  globalThis.fetch=async url=>{assert.equal(fileURLToPath(url),path.join(root,V11_RESULTS_ASSET.path));return new Response(raw);};
  const loaded=await loadV11ResultsScene(three,options,async(t,o)=>{assert.equal(t,three);assert.equal(o,options);return scene;});
  assert.equal(loaded.meta.current_own_response_bank_recorded,true);
  globalThis.fetch=async()=>new Response(new Uint8Array([0]));
  await assert.rejects(loadV11ResultsScene(three,options,async()=>assert.fail('bad results stop before geometry')),/bytes changed/);
});

test('the active route uses own results while baseline, historical routes and frozen geometry bytes remain preserved',()=>{
  const html=readFileSync(path.join(root,'site/index.html'),'utf8');
  assert(html.includes('v11 ? loadV11ResultsScene'));assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert(html.includes('head?.userData.part.fabrication.analysis_reference'));
  assert(documentsForModel(V11_MODEL).some(row=>row.path===data.sources.row_comparison.path));
  for(const[file,expected]of Object.entries({
    'site/eoere-v11-v9-eight-bolt-overlay.mjs':'ff95c5d61d706f2ff4b64ea55dba3fac9531211222b62268e3d21337f729752e',
    'site/eoere-v11-v9-eight-bolt-provenance.json':'29be7c0dac1813ccf251bb2ead1829db5d1498f3710302a8f22ccabf0eef590b',
    'site/eoere-v11-v9-eight-bolt-scene.json.gz':'d636881a74ce500d812cd692094250fcff889659ae9a82fc4bc6f87f298de739',
    'scripts/publish_v11_v9_eight_bolt_viewer.py':'eea48b4dc485bbf1b63901cf4748aa39d87247f356a41e45ebed1adc429f724f',
  }))assert.equal(hash(readFileSync(path.join(root,file))),expected,file);
});
