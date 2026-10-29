import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';
import {loadExternalHexHeadsGeometryScene,EXTERNAL_HEX_HEADS_ASSETS} from './eoere-v11-external-hex-heads-overlay.mjs';

export const SIX_BOLT_CLEAT_MODEL='eoere-v11-six-bolt-cleat-preview';
const require=(ok,message)=>{if(!ok)throw new Error('Six-bolt cleat preview: '+message);};
const equal=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const OMIT=['left','right'].flatMap(side=>[1,2].map(index=>`v11_cleat_${side}_post_${index}`));
const HOSTS=['base_post_outer_left','base_post_outer_right','eoere_cleat_left','eoere_cleat_left_outer','eoere_cleat_right','eoere_cleat_right_outer'];
const ROLES=['head','head_washer','shaft','nut_washer','nut'];
const REMOVALS=OMIT.flatMap(axis=>ROLES.map(role=>axis+'_'+role));

export function applySixBoltCleatGeometry(THREE,parent,data,topologies){
  require(data.schema==='eoere_v11_six_bolt_cleat_scene/v1'&&data.key===SIX_BOLT_CLEAT_MODEL&&data.revision==='v11-six-bolt-cleat-v1','own model required');
  require(parent.parts.length===1055&&parent.design.key==='eoere-v11-external-hex-heads-preview'&&parent.meta.geometry_only===true&&
    parent.meta.current_response_computed===false&&parent.meta.analysis_pending===true,'raw geometry-only 106-stack parent required');
  require(parent.meta.geometry_sha256===data.parent_geometry.sha256&&parent.meta.provenance_sha256===EXTERNAL_HEX_HEADS_ASSETS.sha256,
    'current external-hex parent geometry/provenance required');
  require(data.geometry_only===true&&data.analysis_pending===true&&data.current_response_computed===false&&
    data.historical_capacity_transferred===false&&data.trial_selected===false&&data.structural_acceptance===false&&
    data.purchase_authorized===false&&data.drilling_released===false&&data.fabrication_released===false&&data.climbing_released===false,
    'geometry-only, unreleased claim boundary required');
  require(data.part_count===1035&&data.counts.occupied_parts===1035&&data.counts.bolt_stacks===102&&
    data.counts.washer_pieces===204&&data.counts.spacer_pieces===0&&data.counts.Hillman_axes===66&&
    data.counts.angles===24&&data.counts.profiles===30,'candidate occupied inventory required');
  const backing=data.panel_screw_backing;
  require(backing?.axis_count===66&&backing.axis_rows_byte_semantically_identical===true&&
    backing.backing_preserved_by_unchanged_shapes_or_material_addition===true&&backing.backing_receiver_count===16&&
    backing.unchanged_backing_receivers===14&&backing.source_material_superset_receivers?.join('|')==='base_post_outer_left|base_post_outer_right'&&
    backing.source_material_removed_mm3===0&&backing.unplanned_movement_count===0&&
    backing.source_geometry_binding?.sha256===data.parent_geometry.sha256&&
    equal(backing.screw_axes_on_restored_receivers,['round_kicker_left_rim_1','round_kicker_left_rim_2',
      'round_kicker_right_rim_1','round_kicker_right_rim_2']),
    'all66 Hillman axes require the exact parent-material backing superset proof for both changed outer posts');
  require(data.replacements.length===6&&equal(data.replacements.map(row=>row.name),HOSTS)&&
    equal(data.changed_timber_ids,HOSTS)&&equal(data.removals,REMOVALS)&&equal(data.removed_axis_ids,OMIT),
    'exact six wood/ply replacements and four five-role removals required');
  require(equal(Object.values(data.cleat_bolt_counts),[6,6])&&equal(Object.values(data.outer_corner_bolt_counts),[4,4])&&
    equal(Object.values(data.center_top_bolt_counts),[4,4]),'four side plus two post per cleat, four per outer top and four per center top required');

  const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Map(),allocated=[];
  require(old.size===1055&&REMOVALS.every(name=>old.has(name)&&old.get(name).fabrication.kind==='bolt'&&
    OMIT.includes(old.get(name).fabrication.connection_name)),'each omission must be an actual authorized bolt role');
  try{
    for(const row of data.replacements){
      require(old.has(row.name)&&['timber','panel'].includes(old.get(row.name).fabrication.kind),'known wood or plywood replacement required: '+row.name);
      const geometry=meshGeometry(THREE,row.mesh,topologies);allocated.push(geometry);geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const bounds=geometry.boundingBox;
      require([bounds.min.x,bounds.max.x,bounds.min.y,bounds.max.y,bounds.min.z,bounds.max.z].every((value,index)=>
        Math.abs(value-row.target_bounds_xyz_mm[index])<.55),'checked actual bounds: '+row.name);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);
    }
    const parts=parent.parts.filter(part=>!data.removals.includes(part.name)).map(part=>{
      const current=changed.get(part.name)??part,fabrication={...current.fabrication,
        owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false};
      for(const key of['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity','weight_response','case_rows'])delete fabrication[key];
      fabrication.description='Six-bolt cleat development geometry: four side and two post bolts per cleat; four bolts at each outer top angle and each center top connection; zero spacers. Own matching evaluation pending; complete connections unqualified.';
      return {...current,fabrication};
    });
    validateV10ComposedParts(parts,data);
    const bolts=parts.filter(part=>part.fabrication.kind==='bolt');
    require(equal([...new Set(bolts.map(part=>part.fabrication.connection_name))],data.all_axis_ids)&&data.all_axis_ids.length===102&&
      bolts.length===510&&bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length===204&&
      !bolts.some(part=>part.fabrication.hardware_role.startsWith('spacer')),'102 complete five-piece stacks without spacers required');
    require(equal(data.all_axis_ids,data.parent_all_axis_ids.filter(axis=>!OMIT.includes(axis))),
      'all retained parent axes must stay literal, and omitted axes must be absent');
    require(parts.filter(part=>part.fabrication.kind==='screw').length===66,'all66 Hillman screw parts must remain');
    for(const id of OMIT)require(!bolts.some(part=>part.fabrication.connection_name===id),'omitted axis returned: '+id);
    const retained=new Set(parts.map(part=>part.geometry));
    for(const name of [...changed.keys(),...data.removals]){const geometry=old.get(name).geometry;if(!retained.has(geometry))geometry?.dispose();}
    return {parts,bounds_mm:parent.bounds_mm.map(row=>[...row]),design:{...parent.design,key:SIX_BOLT_CLEAT_MODEL,qualified_for_design:false},
      meta:{revision:data.revision,geometry_sha256:data.geometry_source.sha256,layout_sha256:data.geometry_receipt.sha256,
        provenance_sha256:null,counts:data.counts,axis_ids:[...data.all_axis_ids],removed_axis_ids:[...OMIT],
        geometry_only:true,analysis_pending:true,current_response_computed:false,trial_selected:false,
        planning_mass_kg:null,weight_interpolation_available:false,historical_capacity_transferred:false,
        actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
        structural_acceptance:false,purchase_authorized:false,drilling_released:false,fabrication_released:false,
        climbing_released:false,physical_tool_access_qualified:false,
        status:'Six-bolt cleat development · 102 stacks · four side and two post bolts per cleat · four per outer top corner · center top four · zero spacers · geometry only; own results pending. Omitted near post-flange factory holes remain masked from drilling templates; physical hole state and tool access remain unqualified.',
        portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source,owner_authorization:data.owner_authorization}}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());throw error;}
}

export const SIX_BOLT_CLEAT_ASSETS=Object.freeze({"path": "site/eoere-v11-six-bolt-cleat-provenance.json", "sha256": "a80ae8505d1e763c38d4ffe97666ab6c2eee3bbe1a0676fa5056188493a8cfe5"});
async function readAsset(ref){require(ref.path.startsWith('site/')&&!ref.path.includes('..'),'public site asset required');
  const response=await fetch(new URL(ref.path.slice(5),import.meta.url));require(response.ok,'candidate asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===ref.sha256,'asset source pin differs');
  const decoded=ref.path.endsWith('.gz')?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():raw;
  if(ref.path.endsWith('.gz'))require(await sha256(decoded)===ref.decoded_sha256,'decoded scene pin differs');
  return JSON.parse(new TextDecoder().decode(decoded));}
async function decodeTopologies(data){const rows=new Map();
  for(const[hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'triangle topology pin differs');rows.set(hash,{...row,indices:indices.values});}return rows;}
export async function loadSixBoltCleatGeometryScene(THREE,options){
  const provenance=await readAsset(SIX_BOLT_CLEAT_ASSETS);
  require(provenance.model===SIX_BOLT_CLEAT_MODEL&&provenance.geometry_only===true&&provenance.trial_selected===false&&
    provenance.current_response_computed===false&&provenance.ignored_runtime_dependencies===false&&
    provenance.parent_provenance.sha256===EXTERNAL_HEX_HEADS_ASSETS.sha256,'own geometry-only provenance required');
  const data=await readAsset(provenance.scene);
  require(data.geometry_source.sha256===provenance.geometry.sha256&&data.geometry_receipt.sha256===provenance.geometry_receipt.sha256,
    'candidate source joins differ');
  const scene=applySixBoltCleatGeometry(THREE,await loadExternalHexHeadsGeometryScene(THREE,options),data,await decodeTopologies(data));
  return {...scene,meta:{...scene.meta,provenance_sha256:SIX_BOLT_CLEAT_ASSETS.sha256}};
}
