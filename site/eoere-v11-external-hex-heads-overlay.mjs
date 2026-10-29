import {sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';
import {loadFourBoltOuterTopGeometryScene,FOUR_BOLT_OUTER_TOP_ASSETS} from './eoere-v11-four-bolt-outer-top-overlay.mjs';

export const EXTERNAL_HEX_HEADS_MODEL='eoere-v11-external-hex-heads-preview';
const require=(ok,message)=>{if(!ok)throw new Error('External-hex head trial: '+message);};
const equal=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const AXES=['cleat_post_bolt_left_1','cleat_post_bolt_left_2','cleat_post_bolt_right_1','cleat_post_bolt_right_2',
  'eoere_bolt_067','eoere_bolt_070','eoere_bolt_071','eoere_bolt_074',
  'v11_cleat_left_side_1','v11_cleat_left_side_2','v11_cleat_right_side_1','v11_cleat_right_side_2',
  'rail_front_bolt_left_1','rail_front_bolt_left_2','rail_front_bolt_right_1','rail_front_bolt_right_2'];
const FRONT=['left','right'].flatMap(side=>[1,2].map(i=>`rail_front_bolt_${side}_${i}`));
const ROLES=['head','head_washer','shaft','nut_washer','nut'];

export function applyExternalHexHeadsGeometry(THREE,parent,data){
  require(data.schema==='eoere_v11_external_hex_heads_scene/v1'&&data.key===EXTERNAL_HEX_HEADS_MODEL&&data.revision==='v11-external-hex-heads-v1','own model required');
  require(parent.parts.length===1055&&parent.design.key==='eoere-v11-four-bolt-outer-top-preview'&&parent.meta.geometry_only===true&&
    parent.meta.current_response_computed===false&&parent.meta.analysis_pending===true,'raw geometry-only 106 parent required');
  require(data.geometry_only===true&&data.analysis_pending===true&&data.current_response_computed===false&&data.historical_capacity_transferred===false&&
    data.trial_selected===false&&data.structural_acceptance===false&&data.fabrication_released===false&&data.climbing_released===false,'geometry claim boundary required');
  require(data.part_count===1055&&data.counts.occupied_parts===1055&&data.counts.bolt_stacks===106&&data.counts.washer_pieces===212&&
    data.counts.spacer_pieces===0&&data.counts.Hillman_axes===66&&data.parent_geometry.sha256===parent.meta.geometry_sha256,'fixed inventory and parent binding required');
  require(data.reuses.length===16&&data.stack_updates.length===16&&equal(data.changed_axis_ids,AXES)&&
    equal(data.reuses.map(row=>row.name),AXES.map(id=>id+'_head'))&&equal(data.stack_updates.map(row=>row.axis_id),AXES),'exact sixteen heads required');
  require(equal(Object.values(data.outer_corner_bolt_counts),[4,4])&&equal(Object.values(data.center_top_bolt_counts),[4,4])&&
    equal(Object.values(data.cleat_bolt_counts),[8,8]),'four outer/eight cleat/four center treatment required');
  const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Map(),allocated=[];
  try{
    for(const row of data.reuses){const source=old.get(row.source_parent_name),target=old.get(row.name),m=row.matrix_row_major;
      require(source?.geometry&&target?.fabrication.kind==='bolt'&&
        ['v11_cleat_left_post_1_head','v11_cleat_right_post_1_head'].includes(row.source_parent_name)&&m.length===16&&m.every(Number.isFinite)&&
        m.every((v,k)=>[3,7,11].includes(k)||Math.abs(v-([0,5,10,15].includes(k)?1:0))<1e-9),'existing Grade 5 head translation required');
      const geometry=source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...m));allocated.push(geometry);
      geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
      require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((v,k)=>Math.abs(v-row.target_bounds_xyz_mm[k])<.55),'checked actual head bounds: '+row.name);
      const part={...target,geometry};delete part.path;changed.set(row.name,part);
    }
    const updates=new Map(data.stack_updates.map(row=>[row.axis_id,row]));
    const parts=parent.parts.map(part=>{const current=changed.get(part.name)??part,update=updates.get(current.fabrication.connection_name),
      fabrication={...current.fabrication,...(update??{}),owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false};
      if(update){require(['hex','hex head'].includes(update.selected_head_style)&&/Grade\s*5/.test(update.selected_bolt_grade)&&[152.4,165.1].includes(Number(update.selected_underhead_length_mm))&&
        Number(update.spacer_piece_count)===0,'conditional Grade 5 hex-head recipe required');fabrication.stack_roles=[...ROLES];}
      for(const key of ['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity','weight_response','case_rows'])delete fabrication[key];
      let hardware='';
      if(fabrication.kind==='bolt'){
        fabrication.modeled_head_style='external hex';
        const length=Number(fabrication.selected_underhead_length_mm);
        hardware=`${fabrication.connection_name}: external hex head. `+(fabrication.selected_bolt_grade?fabrication.selected_bolt_grade+'. ':'')+
          (Number.isFinite(length)?`Nominal length ${length.toFixed(3)} mm. `:'');
      }
      fabrication.description=hardware+'External-hex head development trial: sixteen frame heads changed; 106 stacks, eight bolts per cleat, four per outer top corner, zero spacers. Own matching analysis pending; complete connections unqualified.';
      return {...current,fabrication};});
    validateV10ComposedParts(parts,data);
    const bolts=parts.filter(part=>part.fabrication.kind==='bolt');
    require(bolts.length===530&&equal([...new Set(bolts.map(part=>part.fabrication.connection_name))],data.all_axis_ids)&&data.all_axis_ids.length===106&&
      bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length===212&&!bolts.some(part=>part.fabrication.hardware_role.startsWith('spacer')),'106 complete five-piece stacks without spacers');
    require(bolts.every(part=>part.fabrication.modeled_head_style==='external hex'&&(part.fabrication.selected_head_style===undefined||['hex','hex head'].includes(part.fabrication.selected_head_style))),'all106 modeled external-hex heads and retained selection labels required');
    const retained=new Set(parts.map(part=>part.geometry));for(const name of changed.keys()){const geometry=old.get(name).geometry;if(!retained.has(geometry))geometry?.dispose();}
    return {parts,bounds_mm:parent.bounds_mm.map(row=>[...row]),design:{...parent.design,key:EXTERNAL_HEX_HEADS_MODEL,qualified_for_design:false},
      meta:{revision:data.revision,geometry_sha256:data.geometry_source.sha256,layout_sha256:data.geometry_receipt.sha256,counts:data.counts,
        changed_head_count:16,external_hex_frame_stacks:106,internal_drive_frame_stacks:0,geometry_only:true,analysis_pending:true,current_response_computed:false,trial_selected:false,
        planning_mass_kg:null,weight_interpolation_available:false,historical_capacity_transferred:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,
        actual_Fyb_adopted:null,complete_connection_capacity:null,structural_acceptance:false,purchase_authorized:false,fabrication_released:false,climbing_released:false,
        physical_tool_access_qualified:false,status:'External-hex head development trial · 106 stacks · all106 external hex heads; sixteen heads changed · eight bolts per cleat · four per outer top corner · center top four · zero spacers · geometry only; own results pending. No fabrication or climbing release.',
        portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source,owner_authorization:data.owner_authorization}}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());throw error;}
}

export const EXTERNAL_HEX_HEADS_ASSETS=Object.freeze({"path": "site/eoere-v11-external-hex-heads-provenance.json", "sha256": "6c316cab5dbbb43b9e37905d8d2d0c5654d76d9664b9336411c9f955b8d1aeef"});
async function readAsset(ref){require(ref.path.startsWith('site/')&&!ref.path.includes('..'),'public site asset required');
  const response=await fetch(new URL(ref.path.slice(5),import.meta.url));require(response.ok,'asset unavailable');const raw=await response.arrayBuffer();
  require(await sha256(raw)===ref.sha256,'asset source pin differs');
  const decoded=ref.path.endsWith('.gz')?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():raw;
  if(ref.path.endsWith('.gz'))require(await sha256(decoded)===ref.decoded_sha256,'decoded scene pin differs');return JSON.parse(new TextDecoder().decode(decoded));}
export async function loadExternalHexHeadsGeometryScene(THREE,options){
  const provenance=await readAsset(EXTERNAL_HEX_HEADS_ASSETS);
  require(provenance.model===EXTERNAL_HEX_HEADS_MODEL&&provenance.geometry_only===true&&provenance.trial_selected===false&&
    provenance.ignored_runtime_dependencies===false&&provenance.parent_provenance.sha256===FOUR_BOLT_OUTER_TOP_ASSETS.sha256,'own geometry provenance required');
  const data=await readAsset(provenance.scene);
  require(data.geometry_source.sha256===provenance.geometry.sha256&&data.geometry_receipt.sha256===provenance.geometry_receipt.sha256,'own source joins differ');
  const scene=applyExternalHexHeadsGeometry(THREE,await loadFourBoltOuterTopGeometryScene(THREE,options),data);
  return {...scene,meta:{...scene.meta,provenance_sha256:EXTERNAL_HEX_HEADS_ASSETS.sha256}};
}
