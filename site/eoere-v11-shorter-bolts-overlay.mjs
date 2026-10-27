import {loadV11V9EightBoltScene,V11_ASSETS} from './eoere-v11-v9-eight-bolt-overlay.mjs';
import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const SHORTER_MODEL='eoere-v11-shorter-bolts-preview';
export const SHORTER_ASSETS=Object.freeze({provenance:'eoere-v11-shorter-bolts-provenance.json',sha256:'92a70022aa149945bac3a548f7b68af1cf03e30c7223f51fd38cd3a28bbc7cbc'});
const GEOMETRY='73ce1f19ce97959d3867984cc813c178895b50212128fce6a976548ad6bce4c8',RECEIPT='cc2a1688270cd56a36176ff1957ef769d1a84c54eba8c8d255d2b65ec8bcfee9',SCENE='47d53b5af8f977aba7345c3a5de55681761160d6f1b817c27b6c9ea4f9fd93a9',DECODED='33286faf5fc739d921d9a27ccf751952136377814d7d2992888b268f6e4b68f9';
const PARENT_GEOMETRY='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7';
const OWNER='e9b7942904ad9a8f24d0b79d3e07f40814b42f0591ffd1dd9dc4255cb4a599e7';
const A574=['eoere_bolt_067','eoere_bolt_070','eoere_bolt_071','eoere_bolt_074',
  ...['left','right'].flatMap(side=>[1,2].map(n=>`cleat_post_bolt_${side}_${n}`)),
  ...['left','right'].flatMap(side=>[1,2].map(n=>`v11_cleat_${side}_side_${n}`))];
const HEADER=['eoere_bolt_065','eoere_bolt_066','eoere_bolt_079','eoere_bolt_080','eoere_bolt_081','eoere_bolt_082','eoere_bolt_083','eoere_bolt_084'];
const AXES=[...A574,...HEADER],SHA=/^[a-f0-9]{64}$/;
const FALSE_FLAGS=['current_response_computed','current_own_response_bank_recorded','historical_capacity_transferred','complete_joint_qualified',
  'complete_group_qualified','physical_force_bounds_established','structural_acceptance','fabrication_released','climbing_released',
  'purchase_authorized','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Shorter-bolt preview: '+message);};
const unique=values=>new Set(values).size===values.length;
const same=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const finite=(a,n)=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite);

export function validateShorterBoltDelta(data){
  require(SHA.test(GEOMETRY)&&SHA.test(RECEIPT)&&data.schema==='eoere_v11_shorter_bolt_scene/v1'&&data.key===SHORTER_MODEL&&data.revision==='v11-shorter-bolts-v1'&&
    data.geometry_source?.sha256===GEOMETRY&&data.geometry_receipt?.sha256===RECEIPT&&
    data.owner_exemption?.sha256===OWNER&&data.parent_provenance?.sha256===V11_ASSETS.sha256,'final own checked geometry and exact V11 parent required');
  require(data.part_count===1089&&data.counts?.occupied_parts===1089&&data.counts.bolt_stacks===112&&data.counts.spacer_pieces===4&&
    data.counts.Hillman_axes===66&&data.counts.angles===24&&data.geometry_only===true&&data.analysis_pending===true&&data.planning_mass_kg===null,
    'own geometry-only1089-part census required');
  for(const key of FALSE_FLAGS)require(data[key]===false,'no prior analysis or acceptance transfer: '+key);
  require(data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null,
    'actual properties, factors and complete capacity remain unqualified');
  require(!['response_bank','case_rows','load_contract','force_only','row_bounds','standard_cg','family_maxima','member_vector_maxima',
    'axis_force_only_maxima','weight_response','diagnostic_case_rows'].some(key=>key in data),'old force/flag/weight metadata cannot enter this new geometry stage');
  require(data.all_axis_ids?.length===112&&unique(data.all_axis_ids)&&AXES.every(id=>data.all_axis_ids.includes(id)),'all 112 current physical stack references required');
  require(data.removals?.length===20&&same(data.removals,AXES.map(id=>id+'_spacer'))&&
    data.replacements?.length===20&&same(data.replacements.map(row=>row.name),AXES.map(id=>id+'_shaft'))&&
    data.reuses?.length===20&&same(data.reuses.map(row=>row.name),AXES.map(id=>id+'_nut'))&&
    unique([...data.removals,...data.replacements.map(row=>row.name),...data.reuses.map(row=>row.name)]),
    'only 20 sleeve removals and 40 shaft/nut changes permitted');
  require(data.stack_updates?.length===20&&same(data.stack_updates.map(row=>row.axis_id),AXES),'exact 20 changed stack selections required');
  for(const id of AXES){
    const row=data.stack_updates.find(row=>row.axis_id===id),a574=A574.includes(id),axis=data.changed_axis_bindings?.[id];
    require(row.selected_product===(a574?'8093':'365')&&Math.abs(Number(row.selected_underhead_length_mm)-(a574?165.1:76.2))<1e-6&&
      Number(row.spacer_piece_count)===0&&Number(row.spacer_piece_length_mm)===0&&Number(row.nut_side_spacer_mm)===0&&
      row.selected_head_style===(a574?'socket cap':'hex'),'new nominal SKU, length, head style and no-sleeve metadata required: '+id);
    require(finite(axis?.point_xyz_mm,3)&&finite(axis.direction_xyz,3)&&
      Math.abs(axis.direction_xyz.reduce((s,v)=>s+v*v,0)-1)<1e-8,'own fixed physical bolt line required');
    const nut=data.reuses.find(item=>item.name===id+'_nut'),m=nut.matrix_row_major,length=a574?25.4:12.7;
    require(nut.source_parent_name===nut.name&&finite(m,16)&&SHA.test(nut.source?.sha256||'')&&SHA.test(nut.target?.sha256||''),
      'the exact unchanged nut shape must supply its own translated target');
    require(m.every((value,k)=>[3,7,11].includes(k)?Math.abs(value+length*axis.direction_xyz[(k-3)/4])<1e-6:
      Math.abs(value-([0,5,10,15].includes(k)?1:0))<1e-9),'only the source-bound sleeve-length nut translation is permitted');
  }
  for(const row of[...data.replacements,...data.reuses])require(finite(row.target_bounds_xyz_mm,6)&&
    [0,2,4].every(k=>row.target_bounds_xyz_mm[k]<=row.target_bounds_xyz_mm[k+1]),'actual finite target CAD bounds required');
  return data;
}

function bounds(geometry,row){geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
  require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((v,i)=>Math.abs(v-row.target_bounds_xyz_mm[i])<.55),'display differs from actual target: '+row.name);}

export function applyShorterBoltDelta(THREE,parent,input,topologies,makeMesh=meshGeometry){
  const data=validateShorterBoltDelta(input);
  require(parent.parts?.length===1109&&parent.meta?.geometry_sha256===PARENT_GEOMETRY&&parent.meta.provenance_sha256===V11_ASSETS.sha256&&
    parent.meta.geometry_only===true&&parent.meta.analysis_pending===true&&parent.meta.current_response_computed===false,
    'use the frozen geometry-only V11 loader, never its analyzed presentation');
  const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Map(),allocated=[];
  try{
    for(const id of AXES){const f=old.get(id+'_head')?.fabrication,axis=data.changed_axis_bindings[id];
      require(f&&finite(f.axis_point_xyz_mm,3)&&finite(f.axis_direction_xyz,3)&&
        axis.point_xyz_mm.every((v,k)=>Math.abs(v-f.axis_point_xyz_mm[k])<1e-8)&&
        axis.direction_xyz.every((v,k)=>Math.abs(v-f.axis_direction_xyz[k])<1e-8),'changed stack must retain its exact parent physical line');}
    for(const name of data.removals)require(old.has(name),'removed parent sleeve missing');
    for(const row of data.replacements){require(old.has(row.name),'shaft parent missing');const geometry=makeMesh(THREE,row.mesh,topologies);allocated.push(geometry);bounds(geometry,row);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);}
    for(const row of data.reuses){const source=old.get(row.source_parent_name);require(source?.geometry,'nut parent missing');
      const geometry=source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...row.matrix_row_major));allocated.push(geometry);bounds(geometry,row);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);}
    let parts=parent.parts.filter(part=>!data.removals.includes(part.name)).map(part=>changed.get(part.name)||part);
    const selections=new Map(data.stack_updates.map(row=>[row.axis_id,row])),roles=new Map();
    for(const part of parts)if(part.fabrication?.kind==='bolt'){const f=part.fabrication;if(!roles.has(f.connection_name))roles.set(f.connection_name,[]);roles.get(f.connection_name).push(f.hardware_role);}
    require(same([...roles.keys()],data.all_axis_ids),'the resulting112 physical stack identities differ');
    parts=parts.map(part=>{
      const f=part.fabrication;if(!f)return part;
      const update=selections.get(f.connection_name),next={...f,...update,hardware_role:f.hardware_role,dimensions_mm:f.dimensions_mm,
        owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false,
        clearance_status:'Nominal geometry preview; actual fit unverified',stack_roles:roles.get(f.connection_name)||f.stack_roles};
      for(const key of['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity'])delete next[key];
      if(changed.has(part.name)){const b=part.geometry.boundingBox;next.dimensions_mm=['x','y','z'].map(a=>b.max[a]-b.min[a]);}
      next.description=(f.kind==='bolt'?`${f.connection_name}: ${next.selected_bolt_grade}; nominal SKU ${next.selected_product}, length ${Number(next.selected_underhead_length_mm).toFixed(3)} mm; ${Number(next.spacer_piece_count)} metal spacer pieces. `:
        'Unchanged frozen V11 frame, cleat, fitting or panel geometry. ')+
        'Shorter-bolt geometry trial; matched analysis pending. No historical forces or capacity transferred. Actual fit and full connections remain unqualified.';
      return {...part,fabrication:next};
    });
    validateV10ComposedParts(parts,data);
    require(parts.filter(part=>part.fabrication?.hardware_role?.startsWith('spacer')).length===4,'exactly four unchanged lower-post spacers must remain');
    for(const part of parent.parts)if(changed.has(part.name)||data.removals.includes(part.name))part.geometry?.dispose();
    return {parts,bounds_mm:parent.bounds_mm.map(row=>[...row]),design:{key:SHORTER_MODEL,qualified_for_design:false,
      main_face_height_mm:parent.design?.main_face_height_mm,kicker_hold_height_mm:parent.design?.kicker_hold_height_mm,
      tnut_row_stations_mm:parent.design?.tnut_row_stations_mm,documents:data.documents},
      meta:{revision:data.revision,geometry_sha256:GEOMETRY,layout_sha256:RECEIPT,provenance_sha256:SHORTER_ASSETS.sha256,
        counts:data.counts,status:data.status,geometry_only:true,analysis_pending:true,planning_mass_kg:null,
        ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,
        complete_connection_capacity:null,portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,
          clearance:data.clearance_source,owner_exemption:data.owner_exemption},parent_sources:{geometry:PARENT_GEOMETRY,provenance:V11_ASSETS.sha256}}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());parent.parts.forEach(part=>part.geometry?.dispose());throw error;}
}

async function readAsset(name,hash){require(SHA.test(hash),'final checked source binding missing');const response=await fetch(new URL(name,import.meta.url));
  require(response.ok,'own shorter-bolt asset unavailable');const raw=await response.arrayBuffer();require(await sha256(raw)===hash,'own asset bytes changed');return raw;}

export async function loadShorterBoltScene(THREE,options,parentLoader=loadV11V9EightBoltScene){
  const provenance=JSON.parse(new TextDecoder().decode(await readAsset(SHORTER_ASSETS.provenance,SHORTER_ASSETS.sha256)));
  require(provenance.model===SHORTER_MODEL&&provenance.geometry_sha256===GEOMETRY&&provenance.geometry_receipt?.sha256===RECEIPT&&
    provenance.geometry_only===true&&provenance.analysis_pending===true,'own checked geometry-only provenance required');
  const raw=await readAsset('eoere-v11-shorter-bolts-scene.json.gz',SCENE);
  const decoded=await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded)===DECODED,'decoded shorter-bolt patch changed');const data=validateShorterBoltDelta(JSON.parse(new TextDecoder().decode(decoded))),topologies=new Map();
  for(const[hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'topology bytes changed');topologies.set(hash,{...row,indices:indices.values});}
  return applyShorterBoltDelta(THREE,await parentLoader(THREE,options),data,topologies);
}
