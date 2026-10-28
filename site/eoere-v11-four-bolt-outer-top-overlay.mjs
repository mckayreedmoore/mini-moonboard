import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';
import {loadZeroSpacerGeometryScene,ZERO_SPACER_ASSETS} from './eoere-v11-zero-spacer-overlay.mjs';

export const FOUR_BOLT_OUTER_TOP_MODEL='eoere-v11-four-bolt-outer-top-preview';
const require=(ok,message)=>{if(!ok)throw new Error('Four-bolt outer-top preview: '+message);};
const equal=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const HOSTS=['base_rail_top','base_side_left','base_side_right'];
const OMIT=['left','right'].flatMap(side=>['beam','post'].flatMap(flange=>[1,2].map(i=>`v11_top_${side}_${flange}_${i}`)));
const ROLES=['head','head_washer','shaft','nut_washer','nut'];
const REMOVALS=OMIT.flatMap(axis=>ROLES.map(role=>axis+'_'+role));

export function applyFourBoltOuterTopGeometry(THREE,parent,data,topologies){
  require(data.schema==='eoere_v11_four_bolt_outer_top_scene/v1'&&data.key===FOUR_BOLT_OUTER_TOP_MODEL&&data.revision==='v11-four-bolt-outer-top-v1','own model required');
  require(parent.parts.length===1095&&parent.design.key==='eoere-v11-zero-spacer-preview'&&parent.meta.geometry_only===true&&
    parent.meta.analysis_pending===true&&parent.meta.current_response_computed===false,'raw geometry-only zero-spacer114 parent required');
  require(data.geometry_only===true&&data.analysis_pending===true&&data.current_response_computed===false&&data.historical_capacity_transferred===false&&
    data.trial_selected===false&&data.structural_acceptance===false&&data.fabrication_released===false&&data.climbing_released===false,'own geometry claim boundary required');
  require(data.replacements.length===3&&equal(data.replacements.map(r=>r.name),HOSTS)&&equal(data.changed_timber_ids,HOSTS)&&
    equal(data.removals,REMOVALS)&&equal(data.removed_axis_ids,OMIT),'exact three timbers and forty hardware removals required');
  require(data.part_count===1055&&data.counts.occupied_parts===1055&&data.counts.bolt_stacks===106&&data.counts.washer_pieces===212&&
    data.counts.spacer_pieces===0&&data.counts.Hillman_axes===66&&data.parent_geometry.sha256===parent.meta.geometry_sha256,'exact census and parent geometry required');
  require(equal(Object.values(data.outer_corner_bolt_counts),[4,4])&&equal(Object.values(data.center_top_bolt_counts),[4,4])&&
    equal(Object.values(data.cleat_bolt_counts),[8,8]),'four outer/eight cleat/four center treatment required');
  const old=new Map(parent.parts.map(p=>[p.name,p])),changed=new Map(),allocated=[];
  require(data.removals.every(name=>old.has(name)&&old.get(name).fabrication.kind==='bolt'&&
    OMIT.includes(old.get(name).fabrication.connection_name)),'all omissions must be actual authorized bolt roles');
  try{
    for(const row of data.replacements){require(old.has(row.name)&&old.get(row.name).fabrication.kind==='timber','known replacement timber required');
      const geometry=meshGeometry(THREE,row.mesh,topologies);allocated.push(geometry);geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const bounds=geometry.boundingBox;
      require([bounds.min.x,bounds.max.x,bounds.min.y,bounds.max.y,bounds.min.z,bounds.max.z].every((v,k)=>Math.abs(v-row.target_bounds_xyz_mm[k])<.55),'checked actual bounds: '+row.name);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);}
    const parts=parent.parts.filter(part=>!data.removals.includes(part.name)).map(part=>{
      const current=changed.get(part.name)??part,fabrication={...current.fabrication,owner_frame_revision:data.revision,
        actual_parts_verified:false,complete_joint_qualified:false};
      for(const key of ['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity','weight_response','case_rows'])delete fabrication[key];
      fabrication.description='Four-bolt outer-top development geometry: four bolts at each outer top angle, eight per plywood cleat, four per center top angle; zero spacers. Own matching analysis pending; complete connections unqualified.';
      return {...current,fabrication};});
    validateV10ComposedParts(parts,data);
    const bolts=parts.filter(part=>part.fabrication.kind==='bolt');
    require(equal([...new Set(bolts.map(part=>part.fabrication.connection_name))],data.all_axis_ids)&&data.all_axis_ids.length===106&&
      bolts.length===530&&bolts.filter(part=>part.fabrication.hardware_role.endsWith('washer')).length===212&&
      !bolts.some(part=>part.fabrication.hardware_role.startsWith('spacer')),'106 complete five-piece stacks without spacers');
    const retained=new Set(parts.map(part=>part.geometry));
    for(const name of [...changed.keys(),...data.removals]){const geometry=old.get(name).geometry;if(!retained.has(geometry))geometry?.dispose();}
    return {parts,bounds_mm:parent.bounds_mm.map(row=>[...row]),design:{...parent.design,key:FOUR_BOLT_OUTER_TOP_MODEL,qualified_for_design:false},
      meta:{revision:data.revision,geometry_sha256:data.geometry_source.sha256,layout_sha256:data.geometry_receipt.sha256,
        counts:data.counts,geometry_only:true,analysis_pending:true,current_response_computed:false,trial_selected:false,
        planning_mass_kg:null,weight_interpolation_available:false,historical_capacity_transferred:false,
        actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
        structural_acceptance:false,purchase_authorized:false,fabrication_released:false,climbing_released:false,physical_tool_access_qualified:false,
        status:'Four-bolt outer-top development · 106 stacks · four bolts per outer top corner · eight bolts per cleat · center top four · zero spacers · geometry only; own results pending. Prior tool-access limitations remain unresolved. No fabrication or climbing release.',
        portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source,owner_authorization:data.owner_authorization}}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());throw error;}
}

export const FOUR_BOLT_OUTER_TOP_ASSETS=Object.freeze({"path": "site/eoere-v11-four-bolt-outer-top-provenance.json", "sha256": "534d2447f901ababdc63239d6ffd2b7f39a2bc3633f60af1b403037417fd3674"});
async function readAsset(ref){require(ref.path.startsWith('site/')&&!ref.path.includes('..'),'public site asset required');
  const response=await fetch(new URL(ref.path.slice(5),import.meta.url));require(response.ok,'asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===ref.sha256,'asset source pin differs');
  const decoded=ref.path.endsWith('.gz')?await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():raw;
  if(ref.path.endsWith('.gz'))require(await sha256(decoded)===ref.decoded_sha256,'decoded scene pin differs');
  return JSON.parse(new TextDecoder().decode(decoded));}
async function decodeTopologies(data){const rows=new Map();
  for(const [hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'triangle topology pin differs');rows.set(hash,{...row,indices:indices.values});}return rows;}
export async function loadFourBoltOuterTopGeometryScene(THREE,options){
  const provenance=await readAsset(FOUR_BOLT_OUTER_TOP_ASSETS);
  require(provenance.model===FOUR_BOLT_OUTER_TOP_MODEL&&provenance.geometry_only===true&&provenance.trial_selected===false&&
    provenance.ignored_runtime_dependencies===false&&provenance.parent_provenance.sha256===ZERO_SPACER_ASSETS.sha256,'own geometry provenance required');
  const data=await readAsset(provenance.scene);
  require(data.geometry_source.sha256===provenance.geometry.sha256&&data.geometry_receipt.sha256===provenance.geometry_receipt.sha256,'own source joins differ');
  const scene=applyFourBoltOuterTopGeometry(THREE,await loadZeroSpacerGeometryScene(THREE,options),data,await decodeTopologies(data));
  return {...scene,meta:{...scene.meta,provenance_sha256:FOUR_BOLT_OUTER_TOP_ASSETS.sha256}};
}
