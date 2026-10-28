import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';
import {loadRelocatedRearGeometryScene,RELOCATED_REAR_ASSETS} from './eoere-v11-relocated-rear-overlay.mjs';

export const ZERO_SPACER_MODEL='eoere-v11-zero-spacer-preview';
const require=(ok,message)=>{if(!ok)throw new Error('Zero-spacer preview: '+message);};
const equal=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const roles=['head','head_washer','shaft','nut_washer','nut'];

export function applyZeroSpacerGeometry(THREE,parent,data,topologies){
  require(data.schema==='eoere_v11_zero_spacer_scene/v1'&&data.key===ZERO_SPACER_MODEL&&data.revision==='v11-zero-spacer-eight-bolt-v1','own model required');
  require(parent.parts.length===1099&&parent.design.key==='eoere-v11-relocated-rear-preview'&&parent.meta.geometry_only===true&&
    parent.meta.analysis_pending===true&&parent.meta.current_response_computed===false,'raw geometry-only relocated114 parent required');
  require(data.geometry_only===true&&data.analysis_pending===true&&data.current_response_computed===false&&data.historical_capacity_transferred===false&&
    data.trial_selected===false&&data.structural_acceptance===false,'own geometry claim boundary required');
  require(data.replacements.length===4&&data.reuses.length===4&&data.removals.length===4&&data.changed_axis_ids.length===4&&data.stack_updates.length===4,'four shafts/four nuts/four spacer removals required');
  require(data.part_count===1095&&data.counts.occupied_parts===1095&&data.counts.bolt_stacks===114&&data.counts.washer_pieces===228&&
    data.counts.spacer_pieces===0&&data.counts.Hillman_axes===66&&data.parent_geometry.sha256===parent.meta.geometry_sha256,'exact own census and parent geometry required');
  const old=new Map(parent.parts.map(p=>[p.name,p])),changed=new Map(),allocated=[];
  const checkBounds=(geometry,row)=>{geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
    require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((v,k)=>Math.abs(v-row.target_bounds_xyz_mm[k])<.55),'checked actual bounds: '+row.name);};
  try{
    for(const row of data.replacements){require(old.has(row.name)&&row.name.endsWith('_shaft'),'known replacement shaft');
      const geometry=meshGeometry(THREE,row.mesh,topologies);allocated.push(geometry);checkBounds(geometry,row);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);}
    for(const row of data.reuses){const source=old.get(row.source_parent_name),m=row.matrix_row_major;
      require(source?.geometry&&row.name===row.source_parent_name&&row.name.endsWith('_nut')&&m.length===16&&m.every(Number.isFinite)&&
        m.every((v,k)=>[3,7,11].includes(k)||Math.abs(v-([0,5,10,15].includes(k)?1:0))<1e-9),'same-ID translated nut required');
      const axis=data.axis_bindings[source.fabrication.connection_name];
      require(axis&&axis.point_xyz_mm.every((v,k)=>Math.abs(v-source.fabrication.axis_point_xyz_mm[k])<1e-7)&&
        axis.direction_xyz.every((v,k)=>Math.abs(v-source.fabrication.axis_direction_xyz[k])<1e-8)&&
        axis.direction_xyz.every((v,k)=>Math.abs(m[4*k+3]+12.7*v)<1e-7),'nut translation must preserve physical bolt line');
      const geometry=source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...m));allocated.push(geometry);checkBounds(geometry,row);
      const part={...source,geometry};delete part.path;changed.set(row.name,part);}
    require(changed.size===8&&data.removals.every(name=>old.has(name)&&old.get(name).fabrication.hardware_role.startsWith('spacer')),'exact eight changes and four actual spacer removals');
    const updates=new Map(data.stack_updates.map(r=>[r.axis_id,r]));
    const parts=parent.parts.filter(p=>!data.removals.includes(p.name)).map(part=>{const current=changed.get(part.name)??part;
      const update=updates.get(current.fabrication.connection_name),fabrication={...current.fabrication,...(update??{}),
        owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false};
      if(update){fabrication.stack_roles=[...roles];fabrication.spacer_piece_count=0;fabrication.spacer_piece_length_mm=0;fabrication.nut_side_spacer_mm=0;}
      for(const key of ['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity','weight_response','case_rows'])delete fabrication[key];
      fabrication.description='Zero-spacer development geometry: all114 axes and eight-bolt corners retained; four shorter Grade5 bolts and translated nuts, no sleeves. Own analysis pending; complete connections unqualified.';
      return {...current,fabrication};});
    validateV10ComposedParts(parts,data);
    const bolts=parts.filter(p=>p.fabrication.kind==='bolt');
    require(equal([...new Set(bolts.map(p=>p.fabrication.connection_name))],data.all_axis_ids)&&bolts.length===570&&
      bolts.filter(p=>p.fabrication.hardware_role.endsWith('washer')).length===228&&!bolts.some(p=>p.fabrication.hardware_role.startsWith('spacer')),'114 complete five-piece stacks without spacers');
    const retained=new Set(parts.map(p=>p.geometry));
    for(const name of [...changed.keys(),...data.removals]){const geometry=old.get(name).geometry;if(!retained.has(geometry))geometry?.dispose();}
    return {parts,bounds_mm:parent.bounds_mm.map(r=>[...r]),design:{...parent.design,key:ZERO_SPACER_MODEL,qualified_for_design:false},
      meta:{revision:data.revision,geometry_sha256:data.geometry_source.sha256,layout_sha256:data.geometry_receipt.sha256,
        counts:data.counts,geometry_only:true,analysis_pending:true,current_response_computed:false,trial_selected:false,
        planning_mass_kg:null,weight_interpolation_available:false,historical_capacity_transferred:false,
        actual_Cg_adopted:null,actual_Cdelta_adopted:null,complete_connection_capacity:null,structural_acceptance:false,
        purchase_authorized:false,fabrication_released:false,climbing_released:false,physical_tool_access_qualified:false,
        status:'Zero-spacer development · 114 stacks · eight-bolt corners retained · zero sleeves · geometry only; own results pending. Tool access remains conditional. No fabrication or climbing release.',
        portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source,owner_authorization:data.owner_authorization}}};
  }catch(error){allocated.forEach(g=>g.dispose());throw error;}
}

export const ZERO_SPACER_ASSETS=Object.freeze({"path": "site/eoere-v11-zero-spacer-provenance.json", "sha256": "50cace54ac07fd7d07b8e62f7d4650da0f65ab26a5e5697556847472e8d8095a"});
async function readAsset(ref){require(ref.path.startsWith('site/')&&!ref.path.includes('..'),'public site asset required');
  const response=await fetch(new URL(ref.path.slice(5),import.meta.url));require(response.ok,'asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===ref.sha256,'asset source pin differs');
  const decoded=ref.path.endsWith('.gz')?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():raw;
  if(ref.path.endsWith('.gz'))require(await sha256(decoded)===ref.decoded_sha256,'decoded scene pin differs');
  return JSON.parse(new TextDecoder().decode(decoded));}
async function decodeTopologies(data){const rows=new Map();
  for(const [hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'triangle topology pin differs');rows.set(hash,{...row,indices:indices.values});}return rows;}
export async function loadZeroSpacerGeometryScene(THREE,options){
  const provenance=await readAsset(ZERO_SPACER_ASSETS);
  require(provenance.model===ZERO_SPACER_MODEL&&provenance.geometry_only===true&&provenance.trial_selected===false&&
    provenance.ignored_runtime_dependencies===false&&provenance.parent_provenance.sha256===RELOCATED_REAR_ASSETS.sha256,'own geometry provenance required');
  const data=await readAsset(provenance.scene);
  require(data.geometry_source.sha256===provenance.geometry.sha256&&data.geometry_receipt.sha256===provenance.geometry_receipt.sha256,'own source joins differ');
  const scene=applyZeroSpacerGeometry(THREE,await loadRelocatedRearGeometryScene(THREE,options),data,await decodeTopologies(data));
  return {...scene,meta:{...scene.meta,provenance_sha256:ZERO_SPACER_ASSETS.sha256}};
}
