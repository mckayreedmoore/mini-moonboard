import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {V11_MODEL,V11_ASSETS,validateV11GeometryOnly,loadV11V9EightBoltScene}
  from '../site/eoere-v11-v9-eight-bolt-overlay.mjs';
import {loadSingleSpacerScene} from '../site/eoere-single-spacer-overlay.mjs';
import {loadMeshAliases,resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),site=path.join(root,'site');
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const raw=readFileSync(path.join(site,V11_ASSETS.provenance)),provenance=JSON.parse(raw);
const sceneRaw=readFileSync(path.join(site,'eoere-v11-v9-eight-bolt-scene.json.gz')),scene=JSON.parse(gunzipSync(sceneRaw));

test('the geometry-only scene binds its own owner request,final geometry and V9 parent',()=>{
  assert.equal(hash(raw),V11_ASSETS.sha256);assert.equal(hash(sceneRaw),provenance.scene.sha256);
  assert.equal(hash(gunzipSync(sceneRaw)),provenance.scene.decoded_sha256);
  assert.equal(validateV11GeometryOnly(scene),scene);
  for(const ref of[provenance.owner_request,provenance.parent_scene,provenance.parent_layout])
    assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  assert.equal(scene.part_count,1109);assert.equal(scene.counts.bolt_stacks,112);assert.equal(scene.counts.spacer_pieces,24);
  assert.equal(scene.joint_contract.top_joints.length,2);assert.equal(scene.joint_contract.center_top_joints.length,2);
  assert.equal(scene.geometry_only,true);assert.equal(scene.analysis_pending,true);
});

for(const[name,change]of[
  ['the preceding112geometry',d=>{d.geometry_source.sha256='9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde';}],
  ['a duplicated stack selection',d=>{d.stack_updates[1].axis_id=d.stack_updates[0].axis_id;}],
  ['a thinner cleat leaf',d=>{d.joint_contract.cleat_joints[0].nominal_leaf_thickness_mm=12.7;}],
  ['a changed cleat outline',d=>{d.joint_contract.cleat_joints[0].outline_unchanged_from_v9=false;}],
  ['a repeated cleat physical bolt',d=>{const r=d.joint_contract.cleat_joints[0];r.axis_groups.side[0]=r.axis_groups.upright[0];}],
  ['a one-leaf cleat receiver',d=>{const r=d.joint_contract.cleat_joints[0];d.joint_axis_bindings[r.axis_ids[0]].receivers=d.joint_axis_bindings[r.axis_ids[0]].receivers.filter(id=>id!==r.leaf_ids[0]);}],
  ['the opposite top flange',d=>{const r=d.joint_contract.top_joints[0],id=r.flange_axes.beam[0];d.joint_axis_bindings[id].attachments.forEach(a=>{if(a.angle_id===r.fitting_id)a.flange='post';});}],
  ['changed center top membership',d=>{d.joint_contract.center_top_joints[0].v9_axis_ids[0]='v11_top_left_beam_1';}],
  ['an unreversed new near-post stack',d=>{d.stack_updates.find(r=>r.axis_id===d.reversed_new_near_post_axis_ids[0]).head_faces='exterior';}],
  ['the old top grip',d=>{const id=d.joint_contract.top_joints[0].flange_axes.beam[0];d.joint_axis_bindings[id].grip_mm=38.1;}],
  ['the erroneous lower hardwareV1',d=>{d.lower_hardware_recipe.sha256='89e03c7082b8ef0954aa46a52710bde44476a3364b9df6d541e265299ee43c43';}],
  ['the old lower socket head',d=>{d.stack_updates.find(r=>r.axis_id==='v11_cleat_left_post_1').selected_head_style='socket cap';}],
  ['a full-inch lower spacer',d=>{d.stack_updates.find(r=>r.axis_id==='v11_cleat_left_post_1').spacer_piece_length_mm=25.4;}],
  ['a short lower body window',d=>{const r=d.stack_updates.find(r=>r.axis_id==='v11_cleat_left_post_1');r.minimum_full_body_mm=130;}],
  ['a missing actual moved screw',d=>{d.replacements=d.replacements.filter(r=>r.name!=='fastener_round_kicker_left_rim_2');}],
  ['an old kicker panel body',d=>{d.profile_finished_display_sources.kicker_left.sha256='0'.repeat(64);}],
  ['a changed screw direction',d=>{d.screw_axis_updates[0].after.direction_xyz=[1,0,0];}],
  ['a missing screw translation record',d=>{delete d.screw_axis_updates[0].modeled_translation_xyz_mm;}],
  ['a moved lower header instead of actual top',d=>{d.replacements.find(r=>r.name==='eoere_clip_single_top_left_1').name='eoere_clip_header_outer_under_left';}],
  ['a scaling reuse transform',d=>{d.reuses[0].matrix_row_major[0]*=2;d.reuses[0].matrix_row_major[1]*=2;d.reuses[0].matrix_row_major[2]*=2;}],
  ['a prior response bank',d=>{d.response_bank={sha256:'1'.repeat(64)};}],
  ['a historical weight response',d=>{d.weight_response={mass_kg:100};}],
  ['computed analysis',d=>{d.current_response_computed=true;}],
  ['a qualified bond',d=>{d.actual_bond_qualified=true;}],
  ['fabrication release',d=>{d.fabrication_released=true;}],
])test('the new owner model rejects '+name,()=>{const d=structuredClone(scene);change(d);assert.throws(()=>validateV11GeometryOnly(d));});

test('routing preserves baseline history and exposes the restored model\'s own geometry and analysis documents',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8');
  assert(html.includes("['"+V11_MODEL+"', 'Preserved V11 · V9 cleats · 112 bolts · 24 spacers']"));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert(html.includes("['eoere-owner-frame-v9-development',"));
  assert(html.includes("['eoere-packer-free-standard-stock-preview',"));
  for(const row of documentsForModel(V11_MODEL))assert(readFileSync(path.join(root,row.path)).length);
  assert(documentsForModel(V11_MODEL).some(row=>row.path==='docs/bolted-frame-development/owner-frame-v11/response-bank.json'));
  assert(!documentsForModel(V11_MODEL).some(row=>/owner-frame-v(?:9|10)\//.test(row.path)));
});

test('the geometry-only route hides mass metadata and never fetches historical prototype weights',()=>{
  const html=readFileSync(path.join(site,'index.html'),'utf8'),start=html.indexOf('const designLabels = '),end=html.indexOf('const categoryLabels = ',start);
  assert(start>=0&&end>start);const weightLine={},weightNote={};
  runInNewContext(html.slice(start,end),{model:V11_MODEL,isWoodJoint:true,woodJointModels:[[V11_MODEL,'Geometry only']],
    modelSelect:{options:[{value:V11_MODEL,text:'Geometry only'}]},weightLine,weightNote,excludedMass:'unused',
    fetch:()=>assert.fail('new geometry must not request old mass metadata')});
  assert.equal(weightLine.hidden,true);assert.equal(weightNote.hidden,true);
});

const helpers=readFileSync(path.join(root,'tests/test_eoere_v10_loader.mjs'),'utf8');
const start=helpers.indexOf('class Matrix4 {'),end=helpers.indexOf("\ntest('the actual V10 loader",start);
assert(start>=0&&end>start);const THREE=runInNewContext(helpers.slice(start,end)+'\n({Matrix4,BufferAttribute,BufferGeometry});');

test('the actual public-only loader composes1109parts and112own stacks without inherited analysis',async context=>{
  const originalFetch=globalThis.fetch,requests=[];let parent;
  context.after(()=>{globalThis.fetch=originalFetch;});
  globalThis.fetch=async input=>{
    const name=String(input);if(name.startsWith('blob:'))return originalFetch(input);
    assert(!/^[a-z][a-z0-9+.-]*:/i.test(name)||name.startsWith('file:'),'no network');
    const target=name.startsWith('file:')?fileURLToPath(input):path.resolve(site,name);
    assert(target.startsWith(site+path.sep)&&/\.json(?:\.gz)?$/.test(target),'public site JSON only:'+name);
    requests.push(path.relative(site,target));return new Response(readFileSync(target));
  };
  const aliases=await loadMeshAliases(),baselineText=readFileSync(path.join(site,'hybrid/compact-floor-flush-kerf-right/parts.json'),'utf8');
  const loaded=await loadV11V9EightBoltScene(THREE,{baselineText,baselineParts:JSON.parse(baselineText).parts,
    resolveMeshPath:name=>resolveMeshPath(name,aliases)},async(three,options)=>{
      const result=await loadSingleSpacerScene(three,options);
      parent=new Map(result.parts.map(part=>[part.name,{geometry:part.geometry,
        vertices:part.geometry?hash(new Uint8Array(part.geometry.attributes.position.array.buffer)):null}]));
      result.meta.inherited_force_index=999;result.meta.planning_mass_kg=999;result.design.inherited_capacity=999;return result;
    });
  assert.equal(loaded.parts.length,1109);assert.equal(loaded.design.key,V11_MODEL);
  assert.equal(loaded.parts.filter(part=>part.fabrication?.kind==='screw').length,66);
  assert.equal(loaded.parts.filter(part=>part.fabrication?.kind==='bracket').length,24);
  const bolts=loaded.parts.filter(part=>part.fabrication?.kind==='bolt');
  assert.equal(new Set(bolts.map(part=>part.fabrication.connection_name)).size,112);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length,224);
  assert.equal(bolts.filter(part=>part.fabrication.hardware_role.startsWith('spacer')).length,24);
  const changed=new Set([...scene.replacements,...scene.reuses].map(row=>row.name));let shared=0;
  for(const part of loaded.parts){
    if(parent.has(part.name)&&!changed.has(part.name)){assert.equal(part.geometry,parent.get(part.name).geometry);shared++;}
    assert(!part.geometry?.disposed);assert.doesNotMatch(part.fabrication?.description||'',/Candidate\s*13|Own six.case|0\.914625/);
  }
  for(const row of parent.values())if(row.geometry)assert.equal(hash(new Uint8Array(row.geometry.attributes.position.array.buffer)),row.vertices);
  for(const name of['eoere_clip_header_outer_under_left','eoere_clip_header_outer_under_right','eoere_clip_split_header_center_left','eoere_clip_split_header_center_right'])
    assert.equal(loaded.parts.find(part=>part.name===name).geometry,parent.get(name).geometry,'lower header mesh remains V9');
  for(const side of['left','right'])for(const n of[1,2]){
    const stack=bolts.filter(part=>part.fabrication.connection_name===`v11_cleat_${side}_post_${n}`);
    assert.equal(stack.length,6);for(const part of stack){assert.equal(part.fabrication.selected_product,'372');assert.equal(part.fabrication.selected_head_style,'hex');}
    const head=stack.find(part=>part.fabrication.hardware_role==='head');assert(changed.has(head.name));
    assert.match(head.fabrication.description,/External hex head/);assert.match(head.fabrication.description,/12\.70 mm each/);
    for(const[role,expected]of[['head',6],['shaft',177.8],['spacer',12.7]]){
      const shape=stack.find(part=>part.fabrication.hardware_role===role).geometry;shape.computeBoundingBox();
      assert(Math.abs(shape.boundingBox.max.x-shape.boundingBox.min.x-expected)<.11,'actual lower '+role+' extent');
    }
  }
  for(const side of['left','right'])for(const suffix of['','_outer']){
    const leaf=loaded.parts.find(part=>part.name===`eoere_cleat_${side}${suffix}`);
    verifyLeafMesh(leaf.geometry.attributes.position.array);
    assert.equal(leaf.fabrication.nominal_independent_leaf_thickness_mm,19.05);
    assert.equal(leaf.fabrication.nominal_bonded_pair_thickness_mm,38.1);
  }
  assert.equal(loaded.meta.geometry_only,true);assert.equal(loaded.meta.analysis_pending,true);assert.equal(loaded.meta.planning_mass_kg,null);
  assert.equal(loaded.meta.inherited_force_index,undefined);assert.equal(loaded.design.inherited_capacity,undefined);
  assert.equal(loaded.meta.actual_Cg_adopted,null);assert.equal(loaded.meta.complete_connection_capacity,null);
  assert.equal(loaded.meta.current_response_computed,false);assert.equal(loaded.meta.historical_capacity_transferred,false);
  assert.equal(loaded.meta.response_bank,undefined);assert.equal(loaded.meta.case_rows,undefined);
  assert(requests.includes('eoere-v11-v9-eight-bolt-scene.json.gz'));
  context.diagnostic(`1109parts/112stacks/24spacers;${shared} unchanged geometry references; no ignored/runtime response fetches.`);
});

function verifyLeafMesh(positions){
  const minimum=[Infinity,Infinity,Infinity],maximum=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<positions.length;i++){minimum[i%3]=Math.min(minimum[i%3],positions[i]);maximum[i%3]=Math.max(maximum[i%3],positions[i]);}
  assert(Math.abs(maximum[0]-minimum[0]-19.05)<.11,'each displayed leaf has the actual 19.05 mm thickness within display quantization');
  const points=new Map(),edges=new Map();
  const key=(y,z)=>y.toFixed(2)+','+z.toFixed(2);
  for(let i=0;i<positions.length;i+=9){
    if(![0,3,6].every(k=>Math.abs(positions[i+k]-minimum[0])<.11))continue;
    const ids=[0,3,6].map(k=>{const y=positions[i+k+1],z=positions[i+k+2],id=key(y,z);points.set(id,[y,z]);return id;});
    if(new Set(ids).size!==3)continue;
    for(let k=0;k<3;k++){const pair=[ids[k],ids[(k+1)%3]].sort(),id=pair.join('|');const old=edges.get(id);edges.set(id,{pair,count:(old?.count||0)+1});}
  }
  const adjacency=new Map();
  for(const{pair,count}of edges.values())if(count===1)for(let k=0;k<2;k++){
    if(!adjacency.has(pair[k]))adjacency.set(pair[k],[]);adjacency.get(pair[k]).push(pair[1-k]);
  }
  assert(adjacency.size>0&&[...adjacency.values()].every(row=>row.length===2),'display face must have closed nonbranching boundaries');
  const remaining=new Set(adjacency.keys()),loops=[];
  while(remaining.size){const start=remaining.values().next().value,loop=[];let previous=null,current=start;
    do{assert(remaining.delete(current),'face boundary cannot cross itself');loop.push(points.get(current));const next=adjacency.get(current).find(id=>id!==previous);previous=current;current=next;}while(current!==start);
    loops.push(loop);
  }
  assert.equal(loops.length,9,'one original outer contour plus eight physical bore contours per leaf');
  const area=loop=>Math.abs(loop.reduce((sum,p,i)=>{const q=loop[(i+1)%loop.length];return sum+p[0]*q[1]-q[0]*p[1];},0))/2;
  const outer=loops.reduce((best,row)=>area(row)>area(best)?row:best,loops[0]);
  const expected=[[-175.7,139.7],[-36,139.7],[-36,500.886082829381],[-175.7,334.398105944]];
  const distance=(p,a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)));
    return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);};
  for(const p of outer)assert(Math.min(...expected.map((a,i)=>distance(p,a,expected[(i+1)%4])))<.2,'same straight V9 boundary; no new tabs, steps or enlargement');
  for(const p of expected)assert(outer.some(q=>Math.hypot(p[0]-q[0],p[1]-q[1])<.2),'every original V9 corner remains');
  return {outer_contours:1,bore_contours:8,nominal_leaf_thickness_mm:19.05,unchanged_v9_outline:true};
}
