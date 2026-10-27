import {loadShorterBoltScene,SHORTER_ASSETS} from './eoere-v11-shorter-bolts-overlay.mjs';
import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const MATCHING_REAR_MODEL='eoere-v11-matching-rear-bolts-preview';
export const MATCHING_REAR_ASSETS=Object.freeze({provenance:'eoere-v11-matching-rear-bolts-provenance.json',sha256:'9e101e7ea3871299f4dd9b30df5ef799a51423b94863c5b56d431fe8bd0f39b0'});
const GEOMETRY='28bf006c24fe2c57bd2b2a942f34954ef23a294789fd9676cdf5c49b48b35a48';
const PARENT='73ce1f19ce97959d3867984cc813c178895b50212128fce6a976548ad6bce4c8';
const RECEIPT='d9e4fc220a5827c45405faa4e8f4e13066e384ecec30dcb259c66d8b70cf677f';
const PREFIX='docs/bolted-frame-development/owner-frame-v11/matching-rear-bolts/';
const ANALYSIS='fea/generated/v11-matching-rear-bolts-v1/mechanics/analysis-v3/';
const SOURCES={response_bank:{path:PREFIX+'response-bank.json',sha256:'b364c9b572960a23c6566575abf3b791a326ab5ac35e263a770dd6e2fe891a46'},
  reference_completion:{path:PREFIX+'reference-completion.json',sha256:'38eceab51e314607bd94663b7130dc6149167724f70d6f5e034ba939e844adf4'}};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const HOSTS=['base_side_left','base_side_right','lumber_leg_left','lumber_leg_right'];
const AXES=['proposal_upper_rear_left_added_half_in','proposal_upper_rear_right_added_half_in'];
const ROLES=['head','head_washer','shaft','nut_washer','nut'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Matching-rear trial: '+message);};
const unique=values=>new Set(values).size===values.length;
const same=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
const finite=(values,n)=>Array.isArray(values)&&values.length===n&&values.every(Number.isFinite);
const index=value=>Number.isFinite(value)&&value>=0;
const equal=(a,b)=>a&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([key,value])=>a[key]===value);

export function validateMatchingRearDelta(data){
  require(data.schema==='eoere_v11_matching_rear_scene/v1'&&data.key===MATCHING_REAR_MODEL&&data.revision==='v11-matching-rear-bolts-v1'&&
    data.geometry_source?.sha256===GEOMETRY&&data.geometry_receipt?.sha256===RECEIPT&&data.parent_geometry?.sha256===PARENT&&
    data.parent_provenance?.sha256===SHORTER_ASSETS.sha256&&data.part_count===1099&&data.counts?.occupied_parts===1099&&
    data.counts.bolt_stacks===114&&data.counts.washer_pieces===228&&data.counts.spacer_pieces===4&&data.counts.Hillman_axes===66&&data.counts.angles===24,
    'exact own1099-part geometry and shorter-bolt parent required');
  require(data.geometry_only===true&&data.trial_selected===false&&data.historical_capacity_transferred===false&&data.structural_acceptance===false&&
    data.fabrication_released===false&&data.climbing_released===false&&data.unchanged_mesh_bytes_copied===0,'separate unselected geometry without inherited acceptance required');
  require(data.all_axis_ids?.length===114&&unique(data.all_axis_ids)&&same(data.new_axis_ids,AXES)&&
    data.replacements?.length===4&&same(data.replacements.map(row=>row.name),HOSTS)&&data.reuses?.length===10&&
    same(data.reuses.map(row=>row.name),AXES.flatMap(axis=>ROLES.map(role=>axis+'_'+role)))&&unique([...data.replacements,...data.reuses].map(row=>row.name)),
    'only four bored wood replacements and ten additional hardware roles permitted');
  require(data.new_stack_updates?.length===2&&same(data.new_stack_updates.map(row=>row.axis_id),AXES),'two own stack selections required');
  for(const id of AXES){const axis=data.new_axis_bindings?.[id],selection=data.new_stack_updates.find(row=>row.axis_id===id);
    require(finite(axis?.point_xyz_mm,3)&&finite(axis.direction_xyz,3)&&axis.diameter_mm===12.7&&axis.grip_mm===177.8&&
      Math.abs(axis.nominal_under_head_length_mm-215.9)<1e-6&&selection.selected_product==='G0340956'&&
      Number(selection.selected_underhead_length_mm)===axis.nominal_under_head_length_mm&&String(selection.selected_nut_SKU)==='2573'&&
      String(selection.selected_washer_SKU)==='15025'&&Number(selection.spacer_piece_count)===0,'own current half-inch no-spacer recipe required');
  }
  for(const row of[...data.replacements,...data.reuses])require(finite(row.target_bounds_xyz_mm,6)&&[0,2,4].every(k=>row.target_bounds_xyz_mm[k]<=row.target_bounds_xyz_mm[k+1]),'finite actual target bounds required');
  for(const row of data.reuses){const f=row.fabrication,side=f?.connection_name?.includes('_left_')?'left':'right',m=row.matrix_row_major;
    require(AXES.includes(f?.connection_name)&&ROLES.includes(f.hardware_role)&&row.source_parent_name===`lumber_leg_bolt_${side}_1_${f.hardware_role}`&&
      row.name===f.connection_name+'_'+f.hardware_role&&finite(m,16)&&/^[a-f0-9]{64}$/.test(row.source?.sha256||'')&&/^[a-f0-9]{64}$/.test(row.target?.sha256||'')&&
      m.every((v,k)=>[3,7,11].includes(k)||Math.abs(v-([0,5,10,15].includes(k)?1:0))<1e-9),'exact same-side current hardware and pure translation required');}
  return data;
}

function bounds(geometry,row){geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
  require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((value,k)=>Math.abs(value-row.target_bounds_xyz_mm[k])<.55),'display differs from checked target: '+row.name);}

export function applyMatchingRearDelta(THREE,parent,input,topologies){
  const data=validateMatchingRearDelta(input);
  require(parent.parts?.length===1089&&parent.meta?.geometry_sha256===PARENT&&parent.meta.provenance_sha256===SHORTER_ASSETS.sha256&&
    parent.meta.geometry_only===true&&parent.meta.analysis_pending===true&&parent.meta.current_response_computed===false,'use the frozen geometry-only shorter-bolt loader');
  const old=new Map(parent.parts.map(part=>[part.name,part])),changed=new Map(),allocated=[];
  try{
    for(const row of data.replacements){require(old.has(row.name),'replacement parent missing');const geometry=meshGeometry(THREE,row.mesh,topologies);allocated.push(geometry);bounds(geometry,row);
      const part={...old.get(row.name),geometry};delete part.path;changed.set(row.name,part);}
    const selections=new Map(data.new_stack_updates.map(row=>[row.axis_id,row]));
    for(const row of data.reuses){const source=old.get(row.source_parent_name),axis=data.new_axis_bindings[row.fabrication.connection_name],m=row.matrix_row_major;
      require(!old.has(row.name)&&source?.geometry&&finite(source.fabrication.axis_point_xyz_mm,3)&&
        axis.point_xyz_mm.every((value,k)=>Math.abs(value-source.fabrication.axis_point_xyz_mm[k]-m[4*k+3])<1e-6)&&
        axis.direction_xyz.every((value,k)=>Math.abs(value-source.fabrication.axis_direction_xyz[k])<1e-8),'the exact source physical line must translate to the new line');
      const geometry=source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...m));allocated.push(geometry);bounds(geometry,row);
      const part={...source,name:row.name,geometry,fabrication:{...source.fabrication,...selections.get(row.fabrication.connection_name),...row.fabrication,
        selected_head_style:'hex',stack_roles:ROLES,actual_parts_verified:false,complete_joint_qualified:false}};delete part.path;changed.set(row.name,part);
    }
    let parts=parent.parts.map(part=>changed.get(part.name)||part);parts.push(...data.reuses.map(row=>changed.get(row.name)));
    parts=parts.map(part=>{const f={...part.fabrication,owner_frame_revision:data.revision,actual_parts_verified:false,complete_joint_qualified:false};
      for(const key of['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity'])delete f[key];
      f.description=f.kind==='bolt'?`${f.connection_name}: ${f.selected_bolt_grade}; nominal SKU ${f.selected_product}, ${Number(f.selected_underhead_length_mm).toFixed(3)} mm, ${Number(f.spacer_piece_count)} spacer pieces. Unselected matching rear-bolt trial; complete connections unqualified.`:
        'Unselected matching rear-bolt trial. Stock outlines, the original 112 axes, 24 fittings and 66 screws remain; four wood bodies have added bores. Complete connections unqualified.';
      return {...part,fabrication:f};});
    validateV10ComposedParts(parts,data);
    const axes=new Set(parts.filter(part=>part.fabrication.kind==='bolt').map(part=>part.fabrication.connection_name));
    require(same([...axes],data.all_axis_ids)&&parts.filter(part=>part.fabrication.hardware_role?.endsWith('washer')).length===228&&
      parts.filter(part=>part.fabrication.hardware_role?.startsWith('spacer')).length===4,'actual114-stack census and washers/spacers required');
    for(const row of data.replacements)old.get(row.name).geometry?.dispose();
    return {parts,bounds_mm:parent.bounds_mm.map(row=>[...row]),design:{...parent.design,key:MATCHING_REAR_MODEL,qualified_for_design:false},
      meta:{revision:data.revision,geometry_sha256:GEOMETRY,layout_sha256:RECEIPT,provenance_sha256:MATCHING_REAR_ASSETS.sha256,counts:data.counts,
        geometry_only:true,analysis_pending:true,current_response_computed:false,trial_selected:false,planning_mass_kg:null,
        ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
        portable_sources:{geometry:data.geometry_source,geometry_receipt:data.geometry_receipt,clearance:data.clearance_source},parent_provenance:data.parent_provenance}};
  }catch(error){allocated.forEach(geometry=>geometry.dispose());parent.parts.forEach(part=>part.geometry?.dispose());throw error;}
}

export function validateMatchingRearResults(data){
  require(data.schema==='eoere_v11_matching_rear_viewer_results/v1'&&data.model===MATCHING_REAR_MODEL&&data.revision==='v11-matching-rear-bolts-v1'&&
    data.geometry?.sha256===GEOMETRY&&data.geometry_receipt?.path===PREFIX+'geometry-receipt.json'&&data.geometry_receipt.sha256===RECEIPT&&
    data.analysis_geometry?.path===ANALYSIS+'geometry/geometry.json'&&data.analysis_geometry.sha256==='1ee6c3693925e7e2026d7a3b1c79b138f35f4c1640cc90f718ea545f7d407ecc',
    'own current114 geometry and analysis required');
  require(data.sources&&Object.keys(data.sources).length===2&&Object.entries(SOURCES).every(([key,ref])=>equal(data.sources[key],ref)),'own fresh bank and reference completion required');
  require(equal(data.load_contract,{accessory_mass_kg:25,downward_multiplier:2,duration_factor_CD:1,horizontal_force_N:300,weight_lb:250})&&
    data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,'fixed250lb recipe with no weight interpolation required');
  require(data.cases?.length===6&&unique(data.cases.map(row=>row.case_id))&&CASES.every(id=>data.cases.some(row=>row.case_id===id))&&data.independent_replays===12,'six own cases and12replays required');
  const hashes=[];for(const row of data.cases){require(row.both_independent_replays_admitted===true&&index(row.gradient_inf_N)&&row.gradient_inf_N<=1e-5,'both replays and admitted residual required');
    for(const[key,file]of[['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key]?.path===ANALYSIS+'four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256||''),'own field/replay case join required');hashes.push(row[key].sha256);}}
  require(unique(hashes)&&data.maximum_gradient_inf_N===2.246134017003243e-6&&data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'own distinct fields and exact residual maximum required');
  require(data.family_references&&same(Object.keys(data.family_references),['cleat_actual_perimeter_rows','direct_elastic_steel','reduced_connection_axial_bending',
    'timber_net_shear_torsion','timber_normal_and_stability','wood_bearing_whole_affine']),'six own reference families required');
  for(const row of Object.values(data.family_references))require(index(row.maximum?.index)&&CASES.includes(row.maximum.case_id)&&Number.isInteger(row.above_one_count)&&row.above_one_count>=0,'finite conditional family references required');
  const rear=data.rear;
  require(rear?.axis_count===6&&rear.axis_case_states===36&&rear.receiver_case_certificates===72&&rear.projected_cases_independently_replayed===36&&
    rear.projected_summary.reference_index_above_one_count===0&&rear.projected_summary.full_NDS_connection_capacity===null&&
    rear.continuous_summary.maximum_lower_bound===.676720794298407&&rear.projected_summary.maximum_projected_reference_index_case[2]===.6825712380846458,
    'rear witnesses and necessary lower bound remain material references');
  require(data.current_response_computed===true&&data.trial_selected===false&&data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&
    data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null,'references do not select the trial or qualify complete capacity');
  for(const key of FALSE_FLAGS)require(data[key]===false,'qualification/release boundary: '+key);
  return data;
}

export function matchingRearStatus(input){
  const data=validateMatchingRearResults(input),f=data.family_references,r=data.rear;
  return 'Unselected matching rear-bolt trial · 114 stacks · four spacers. Six own 250 lb cases and 12 independent replays admitted. '+
    `Conditional references: timber ${f.timber_net_shear_torsion.maximum.index.toFixed(6)}, normal/stability ${f.timber_normal_and_stability.maximum.index.toFixed(6)}, `+
    `cleat ${f.cleat_actual_perimeter_rows.maximum.index.toFixed(6)}, separate elastic steel ${f.direct_elastic_steel.maximum.index.toFixed(6)}. `+
    `Rear projected material reference ${r.maximum_case_reference_bracket[1].toFixed(6)} across 36 states, zero above one; continuous necessary lower bound ${r.maximum_case_reference_bracket[0].toFixed(6)}. `+
    `Legacy diagnostics: wood pressure ${f.wood_bearing_whole_affine.above_one_count}, group-reduced N/M ${f.reduced_connection_axial_bending.above_one_count}; 21 raw-port and 8 individual upper references remain inconclusive. `+
    'Actual Cg/Cdelta and full joint capacity unqualified. Nominal edge/row margin about 0.145 mm; end-distance and top Table D applicability, near-washer, fitting/contact checks remain open. '+
    'Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. No fabrication or climbing release.';
}

export function applyMatchingRearResults(scene,input){
  const data=validateMatchingRearResults(input);
  require(scene.design?.key===MATCHING_REAR_MODEL&&scene.parts?.length===1099&&scene.meta?.geometry_sha256===GEOMETRY&&scene.meta.layout_sha256===RECEIPT&&
    scene.meta.geometry_only===true&&scene.meta.current_response_computed===false,'the own raw geometry stage is required');
  return {...scene,meta:{...scene.meta,status:matchingRearStatus(data),geometry_only:false,analysis_pending:false,current_response_computed:true,
    current_own_response_bank_recorded:true,load_contract:data.load_contract,case_rows:data.cases,independent_replays:12,
    maximum_gradient_inf_N:data.maximum_gradient_inf_N,family_references:data.family_references,connection_references:data.connections,rear_references:data.rear,
    portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

async function readAsset(name,hash){require(/^[a-f0-9]{64}$/.test(hash),'frozen asset pin required');const response=await fetch(new URL(name.replace(/^site\//,''),import.meta.url));
  require(response.ok,'own trial asset unavailable');const raw=await response.arrayBuffer();require(await sha256(raw)===hash,'own trial asset bytes changed');return raw;}

export async function loadMatchingRearScene(THREE,options,parentLoader=loadShorterBoltScene){
  const provenance=JSON.parse(new TextDecoder().decode(await readAsset(MATCHING_REAR_ASSETS.provenance,MATCHING_REAR_ASSETS.sha256)));
  require(provenance.model===MATCHING_REAR_MODEL&&provenance.geometry?.sha256===GEOMETRY&&provenance.geometry_receipt?.sha256===RECEIPT&&
    provenance.parent_provenance?.sha256===SHORTER_ASSETS.sha256&&provenance.trial_selected===false&&provenance.ignored_runtime_dependencies===false,'own unselected portable provenance required');
  const raw=await readAsset(provenance.scene.path,provenance.scene.sha256);
  const decoded=await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded)===provenance.scene.decoded_sha256,'decoded scene bytes changed');
  const data=validateMatchingRearDelta(JSON.parse(new TextDecoder().decode(decoded))),topologies=new Map();
  for(const[hash,row]of Object.entries(data.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'topology bytes changed');topologies.set(hash,{...row,indices:indices.values});}
  const results=validateMatchingRearResults(JSON.parse(new TextDecoder().decode(await readAsset(provenance.results.path,provenance.results.sha256))));
  return applyMatchingRearResults(applyMatchingRearDelta(THREE,await parentLoader(THREE,options),data,topologies),results);
}
