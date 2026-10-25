import {loadSingleSpacerScene} from './eoere-single-spacer-overlay.mjs';
import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {applyV10StackMetadata,validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const V11_MODEL = 'eoere-v11-v9-eight-bolt-preview';
export const V11_ASSETS = Object.freeze({provenance:'eoere-v11-v9-eight-bolt-provenance.json',sha256:'29be7c0dac1813ccf251bb2ead1829db5d1498f3710302a8f22ccabf0eef590b'});
const GEOMETRY='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7', RECEIPT='576159eb2dcd791cf1a983165728e173fa594015fd7ab39ed9d69c1cb591a330', SCENE='d636881a74ce500d812cd692094250fcff889659ae9a82fc4bc6f87f298de739', DECODED='b4dbb18e3431773ef18be54b0488a4ac6e35dcb52ab55b4713ad349b4eaaf379';
const OWNER='8704cdfba23c59ea2a56d87bddf8f1123caedfbaad3c5163d6196eda2234fde0';
const V9_SCENE='250f8fb4e6fc965ebf77dc9a5822ece646a3163fb85878d15c265673275f4058';
const V9_LAYOUT='29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef';
const SHA=/^[a-f0-9]{64}$/;
const OUTER=['eoere_clip_single_top_left_1','eoere_clip_single_top_right_2'];
const CENTER=['eoere_clip_split_top_center_left','eoere_clip_split_top_center_right'];
const FALSE_FLAGS=['current_response_computed','current_own_response_bank_recorded','historical_capacity_transferred',
  'complete_joint_qualified','complete_group_qualified','physical_force_bounds_established','structural_acceptance',
  'actual_bond_qualified','fabrication_released','climbing_released','purchase_authorized','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('V11 V9 preview: '+message);};
const unique=values=>new Set(values).size===values.length;
const finite=(values,n)=>Array.isArray(values)&&values.length===n&&values.every(Number.isFinite);
const sorted=values=>[...values].sort();
const same=(a,b)=>JSON.stringify(sorted(a))===JSON.stringify(sorted(b));

function groupMembers(row,kind,count,bindings,selectionIds){
  const groups=row[kind];require(groups&&Object.keys(groups).length===2,'two distinct joint roles required');
  const ids=Object.values(groups).flat();
  require(ids.length===count&&unique(ids)&&same(ids,row.axis_ids)&&ids.every(id=>selectionIds.has(id)), 'joint must contain distinct complete physical stacks');
  for(const[role,members]of Object.entries(groups)){
    require(members.length===count/2,'equal declared joint roles required');
    for(const id of members){
      const axis=bindings[id];require(axis&&Array.isArray(axis.receivers),'own joint axis binding required');
      if(kind==='axis_groups'){
        const host='base_'+(role==='side'?'side_':role==='upright'?'post_outer_':'invalid_')+row.side;
        require([...row.leaf_ids,host].every(receiver=>axis.receivers.includes(receiver)),'cleat stack must join both leaves to its own host');
      }else require(['beam','post'].includes(role)&&axis.attachments?.some(a=>a.angle_id===row.fitting_id&&a.flange===role&&
        a.installed_bolt_axis_id===id&&axis.receivers.includes(a.receiver)),'top stack must join its own fitting flange/receiver');
    }
  }
}

export function validateV11GeometryOnly(data){
  require(data.schema==='eoere_v11_v9_eight_bolt_scene/v1'&&data.key===V11_MODEL&&data.geometry_source?.sha256===GEOMETRY&&
    data.geometry_receipt?.sha256===RECEIPT&&data.owner_request?.sha256===OWNER&&
    data.parent_scene?.sha256===V9_SCENE&&data.parent_layout?.sha256===V9_LAYOUT,'own geometry/owner and exact V9 parent required');
  const counts=data.counts;
  require(counts?.bolt_stacks===112&&counts.Hillman_axes===66&&counts.angles===24&&counts.plywood_cleats===4&&counts.panels===6&&
    counts.sawn_members===20&&counts.spacer_pieces===24&&data.part_count===1109&&data.part_count===counts.occupied_parts,
  'actual V11 census required; equal bolt counts do not identify the preceding 112-bolt geometry');
  require(data.analysis_pending===true&&data.geometry_only===true&&data.planning_mass_kg===null&&data.unchanged_mesh_bytes_copied===0,
    'geometry-only analysis-pending scope required');
  for(const flag of FALSE_FLAGS)require(data[flag]===false,'no historical analysis or release transfer: '+flag);
  require(!['response_bank','case_rows','declared_vector_references','diagnostic_case_rows','weight_response','load_contract'].some(key=>key in data),
    'geometry-only data cannot contain old response/weight/index metadata');
  require(Array.isArray(data.stack_updates)&&data.stack_updates.length===112&&unique(data.stack_updates.map(row=>row.axis_id)), '112 own complete stack selections required');
  const ids=new Set(data.stack_updates.map(row=>row.axis_id)),contract=data.joint_contract,bindings=data.joint_axis_bindings;
  require(bindings&&contract?.physical_bolt_axes===112&&contract.outer_top_scope_explicitly_confirmed===true&&
    finite(contract.top_actual_section_mm,2)&&contract.top_actual_section_mm.every((value,i)=>Math.abs(value-[88.9,139.7][i])<1e-6), 'confirmed outer-only scope and standard 4x6 required');
  require(contract.cleat_joints?.length===2&&same(contract.cleat_joints.map(row=>row.side),['left','right']), 'two cleat joints required');
  for(const row of contract.cleat_joints){
    require(same(row.leaf_ids,['eoere_cleat_'+row.side,'eoere_cleat_'+row.side+'_outer'])&&row.leaf_count===2&&
      row.nominal_leaf_thickness_mm===19.05&&row.nominal_combined_thickness_mm===38.1&&row.outline_unchanged_from_v9===true&&
      row.glued_pair_requested===true&&row.actual_bond_qualified===false,'two unqualified glued 3/4-inch leaves with unchanged V9 outline required');
    groupMembers(row,'axis_groups',8,bindings,ids);
  }
  require(contract.top_joints?.length===2&&same(contract.top_joints.map(row=>row.fitting_id),OUTER)&&
    contract.center_top_joints?.length===2&&same(contract.center_top_joints.map(row=>row.fitting_id),CENTER), 'only two outer top joints gain bolts');
  for(const row of contract.top_joints)groupMembers(row,'flange_axes',8,bindings,ids);
  for(const row of contract.center_top_joints){groupMembers(row,'flange_axes',4,bindings,ids);require(same(row.axis_ids,row.v9_axis_ids),'center top membership must remain V9');}
  const nearPost=contract.top_joints.flatMap(row=>row.flange_axes.post.filter(id=>bindings[id].attachments.some(a=>a.angle_id===row.fitting_id&&a.flange==='post'&&a.row==='near')));
  require(nearPost.length===4&&same(nearPost,data.reversed_new_near_post_axis_ids||[]),'four explicitly reversed new near-post stacks required');
  for(const id of nearPost){const row=data.stack_updates.find(row=>row.axis_id===id);require(row.head_faces==='interior'&&row.nut_faces==='exterior','new near-post orientation differs');}
  const screwDeltas={round_panel_upper_left_center_4:[0,-32.65361057,-38.91505771],round_panel_upper_right_center_4:[0,-32.65361057,-38.91505771],
    round_kicker_left_rim_2:[0,0,-6.35],round_kicker_right_rim_2:[0,0,-6.35]};
  require(data.screw_axis_updates?.length===4&&same(data.screw_axis_updates.map(row=>row.axis_id),Object.keys(screwDeltas)), 'four actual approved panel-aperture/screw moves required');
  for(const row of data.screw_axis_updates)require(finite(row.before?.origin_xyz_mm,3)&&finite(row.after?.origin_xyz_mm,3)&&
    finite(row.after.direction_xyz,3)&&JSON.stringify(row.before.direction_xyz)===JSON.stringify(row.after.direction_xyz)&&
    row.before.panel===row.after.panel&&row.before.receiver===row.after.receiver&&screwDeltas[row.axis_id].every((delta,k)=>
    Math.abs(row.after.origin_xyz_mm[k]-row.before.origin_xyz_mm[k]-delta)<1e-6),'panel/screw move differs from approved fit');
  const beamIds=[...contract.top_joints,...contract.center_top_joints].flatMap(row=>row.flange_axes.beam);
  require(beamIds.length===12&&beamIds.every(id=>Math.abs(bindings[id].grip_mm-88.9)<1e-6&&
    data.stack_updates.some(row=>row.axis_id===id&&row.selected_product==='G0341148'&&row.selected_underhead_length_mm===120.65)),
    'all twelve top beam stacks need the actual standard-top grip and own 4-3/4-inch recipe');
  require(data.lower_hardware_recipe?.sha256==='51111b77cdeecd7e9178c72e1cdaa1ec813bf98ce2c97973d6e875b4e67699a3', 'own corrected four-lower-stack nominal recipe source required');
  for(const side of ['left','right'])for(const n of [1,2]){
    const row=data.stack_updates.find(row=>row.axis_id===`v11_cleat_${side}_post_${n}`);
    require(row&&String(row.selected_product)==='372'&&/Grade\s*5/.test(row.selected_bolt_grade)&&Number(row.selected_underhead_length_mm)===177.8&&
      String(row.selected_spacer_SKU)==='13731'&&Number(row.spacer_piece_count)===1&&Number(row.spacer_piece_length_mm)===12.7&&
      String(row.selected_nut_SKU)==='2584'&&String(row.selected_washer_SKU)==='15023'&&Number(row.minimum_full_body_mm??row.minimum_body_mm)>=135.9916&&
      row.head_faces==='exterior'&&row.nut_faces==='interior'&&row.selected_head_style==='hex', 'new lower modeled hardware must not inherit the old socket-cap recipe');
  }
  require(Array.isArray(data.replacements)&&Array.isArray(data.reuses)&&Array.isArray(data.removals), 'minimal mesh/reuse/removal patch required');
  const names=[...data.replacements,...data.reuses].map(row=>row.name);
  require(unique([...names,...data.removals]),'changed/removed identities must be unique');
  require([...OUTER,...CENTER].every(name=>names.includes(name))&&
    !['eoere_clip_header_outer_under_left','eoere_clip_header_outer_under_right','eoere_clip_split_header_center_left','eoere_clip_split_header_center_right']
      .some(name=>names.includes(name)||data.removals.includes(name)), 'actual top solids must change while lower V9 header angles remain');
  for(const move of data.screw_axis_updates){
    const part=[...data.replacements,...data.reuses].find(row=>row.name==='fastener_'+move.axis_id);
    require(part?.fabrication?.kind==='screw'&&SHA.test(move.target_solid?.sha256||'')&&
      (part.target||part.source)?.sha256===move.target_solid.sha256&&finite(move.modeled_translation_xyz_mm,3)&&
      screwDeltas[move.axis_id].every((delta,k)=>Math.abs(move.modeled_translation_xyz_mm[k]-delta)<1e-6),
      'moved screw needs its actual occupied solid and bound translation record');
    require(names.includes(move.after.panel),'moved screw needs its actual remachined panel mesh');
  }
  for(const panel of ['kicker_left','kicker_right']){
    const part=[...data.replacements,...data.reuses].find(row=>row.name===panel),source=data.profile_finished_display_sources?.[panel];
    require(part?.fabrication?.kind==='panel'&&SHA.test(source?.sha256||'')&&(part.target||part.source)?.sha256===source.sha256,
      'kicker mesh must use its own final profile-finished body');
  }
  for(const row of [...data.replacements,...data.reuses])require(typeof row.name==='string'&&finite(row.target_bounds_xyz_mm,6)&&
    [0,2,4].every(k=>row.target_bounds_xyz_mm[k]<=row.target_bounds_xyz_mm[k+1]), 'finite target CAD bounds required');
  for(const row of data.reuses){
    const m=row.matrix_row_major;require(finite(m,16)&&JSON.stringify(m.slice(12))==='[0,0,0,1]'&&SHA.test(row.source?.sha256||'')&&SHA.test(row.target?.sha256||'')&&
      (typeof row.source_parent_name==='string')!==(typeof row.source_new_name==='string'),'one source-bound rigid mesh source required');
    for(let i=0;i<3;i++)for(let j=0;j<3;j++)require(Math.abs([0,1,2].reduce((s,k)=>s+m[4*i+k]*m[4*j+k],0)-(i===j?1:0))<1e-8,'reuse cannot scale or shear');
    require(Math.abs(m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8])-1)<1e-8,'reuse cannot reflect');
  }
  return data;
}

function checkBounds(geometry,row){geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
  require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((value,i)=>Math.abs(value-row.target_bounds_xyz_mm[i])<.55),'display differs from target CAD: '+row.name);}

export function applyV11GeometryDelta(THREE,parent,input,topologies){
  const data=validateV11GeometryOnly(input);
  require(parent.parts.length===1021&&parent.meta?.revision==='eoere-single-spacer-cleat-stacks-v9'&&
    parent.meta.source_sha256===V9_SCENE&&parent.meta.layout_sha256===V9_LAYOUT,'actual preserved V9 mesh parent required');
  const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Map(),allocated=[];
  try{
    require(data.removals.every(id=>old.has(id)),'removed V9 part missing');
    for(const row of data.replacements){const geometry=meshGeometry(THREE,row.mesh,topologies);allocated.push(geometry);checkBounds(geometry,row);
      const part={...old.get(row.name),name:row.name,geometry,fabrication:{...old.get(row.name)?.fabrication,...row.fabrication}};delete part.path;changed.set(row.name,part);}
    for(const row of data.reuses){const source=row.source_parent_name?old.get(row.source_parent_name):changed.get(row.source_new_name);
      require(source?.geometry,'reused source geometry missing');const geometry=source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...row.matrix_row_major));allocated.push(geometry);checkBounds(geometry,row);
      const part={...old.get(row.name),name:row.name,geometry,fabrication:{...old.get(row.name)?.fabrication,...row.fabrication}};delete part.path;changed.set(row.name,part);}
    let parts=parent.parts.filter(part=>!data.removals.includes(part.name)).map(part=>changed.get(part.name)||part);
    parts.push(...[...changed.values()].filter(part=>!old.has(part.name)));
    const roles=new Map();for(const part of parts)if(part.fabrication?.kind==='bolt'){const f=part.fabrication;if(!roles.has(f.connection_name))roles.set(f.connection_name,[]);roles.get(f.connection_name).push(f.hardware_role);}
    parts=parts.map(part=>({...part,fabrication:{...part.fabrication,stack_roles:roles.get(part.fabrication?.connection_name)||part.fabrication?.stack_roles}}));
    applyV10StackMetadata(parts,data);
    parts=parts.map(part=>{const f=part.fabrication,cleat=/^eoere_cleat_(left|right)(?:_outer)?$/.test(part.name);
      if(!f)return part;const next={...f,owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false,
        clearance_status:'Geometry-only preview; delivered fit unverified',
        description:(f.kind==='bolt'?`${f.connection_name}: ${f.selected_bolt_grade}; nominal length ${Number(f.selected_underhead_length_mm).toFixed(3)} mm. ${f.selected_head_style==='hex'?'External hex head. ':''}${Number(f.spacer_piece_count)} factory spacer piece${Number(f.spacer_piece_count)===1?'':'s'}${Number(f.spacer_piece_count)?`, nominal ${Number(f.spacer_piece_length_mm).toFixed(2)} mm each`:''}; dimensional fit remains conditional. ${f.head_faces||'Unobserved'} head / ${f.nut_faces||'unobserved'} nut orientation. `:
          cleat?'V9 cleat, same straight outline: 19.05 mm per leaf, 38.1 mm requested glued pair; eight stacks per cleat. Bond unqualified. ':
          part.name==='base_rail_top'?'Standard 4×6 top; modeled actual section 88.9 × 139.7 mm. ':CENTER.includes(part.name)?
            'V9 center top joint: four bolt stacks retained. ':OUTER.includes(part.name)?'Outer top corner: eight bolt stacks, four per flange. ':f.kind==='screw'?
            'Hillman panel/kicker screw axis; existing purchased screw policy retained. ':'V11 from preserved V9. ')+
          'Geometry only; analysis pending. No historical capacity transferred. Actual fit and complete connections unqualified.'};
      if(cleat){delete next.no_glue_friction_or_composite_action_credit;Object.assign(next,{nominal_independent_leaf_thickness_mm:19.05,
        nominal_bonded_pair_thickness_mm:38.1,glued_pair_requested:true,actual_bond_qualified:false,
        proposed_lamination:'Owner-requested glued pair of two nominal 19.05 mm leaves; own bond analysis and physical qualification pending',
        side_receiver_bolts:4,upright_receiver_bolts:4,bolts_per_cleat:8});delete next.upper_bolts_per_corner;delete next.lower_bolts_per_corner;}
      if(part.name==='base_rail_top')Object.assign(next,{nominal_stock:'4x6',actual_section_mm:[88.9,139.7]});
      return {...part,fabrication:next};});
    validateV10ComposedParts(parts,data);
    for(const part of parent.parts)if(changed.has(part.name)||data.removals.includes(part.name))part.geometry?.dispose();
    const bounds=parent.bounds_mm.map(row=>[...row]);for(const row of [...data.replacements,...data.reuses])for(let k=0;k<3;k++){
      bounds[0][k]=Math.min(bounds[0][k],row.target_bounds_xyz_mm[2*k]);bounds[1][k]=Math.max(bounds[1][k],row.target_bounds_xyz_mm[2*k+1]);}
    return {parts,bounds_mm:bounds,design:{key:V11_MODEL,qualified_for_design:false,main_face_height_mm:parent.design?.main_face_height_mm,
      kicker_hold_height_mm:parent.design?.kicker_hold_height_mm,tnut_row_stations_mm:parent.design?.tnut_row_stations_mm,documents:data.documents},
      meta:{revision:data.revision,geometry_sha256:GEOMETRY,layout_sha256:RECEIPT,provenance_sha256:V11_ASSETS.sha256,counts:data.counts,
        status:data.status,geometry_only:true,analysis_pending:true,planning_mass_kg:null,packers_present:false,
        ...Object.fromEntries(FALSE_FLAGS.map(flag=>[flag,false])),physical_release:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,
        complete_connection_capacity:null,joint_contract:data.joint_contract,portable_sources:{owner_request:data.owner_request,
          geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source},
        parent_sources:{scene:data.parent_scene,layout:data.parent_layout}}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());parent.parts.forEach(part=>part.geometry?.dispose());throw error;}
}

async function readAsset(name,hash){require(SHA.test(hash),'final frozen asset binding missing');const response=await fetch(new URL(name,import.meta.url));
  require(response.ok,'portable V11 asset unavailable: '+name);const raw=await response.arrayBuffer();require(await sha256(raw)===hash,'portable asset bytes changed: '+name);return raw;}

export async function loadV11V9EightBoltScene(THREE,options,parentLoader=loadSingleSpacerScene){
  const provenance=JSON.parse(new TextDecoder().decode(await readAsset(V11_ASSETS.provenance,V11_ASSETS.sha256)));
  require(provenance.schema==='eoere_v11_v9_eight_bolt_provenance/v1'&&provenance.model===V11_MODEL&&provenance.owner_request?.sha256===OWNER&&
    provenance.geometry_sha256===GEOMETRY&&provenance.geometry_receipt?.sha256===RECEIPT&&provenance.geometry_only===true&&provenance.analysis_pending===true,
  'own geometry-only source provenance required');
  const compressed=await readAsset('eoere-v11-v9-eight-bolt-scene.json.gz',SCENE);
  const decoded=await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded)===DECODED,'decoded V11 patch changed');const data=validateV11GeometryOnly(JSON.parse(new TextDecoder().decode(decoded))),topologies=new Map();
  for(const[hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'triangle topology changed');topologies.set(hash,{...row,indices:indices.values});}
  const parent=await parentLoader(THREE,{...options,url:'eoere-single-spacer-scene.json',expectedSha256:V9_SCENE,layoutSha256:V9_LAYOUT,decodedSha256:undefined});
  return applyV11GeometryDelta(THREE,parent,data,topologies);
}
