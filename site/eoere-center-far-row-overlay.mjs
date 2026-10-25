import {loadPackerFreeResultsScene} from './eoere-packer-free-results.mjs';
import {meshGeometry,decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const CENTER_FAR_ROW_MODEL = 'eoere-packer-free-center-far-row-preview';
export const CENTER_FAR_ROW_REVISION = 'v10-packer-free-center-far-row-only-development-v1';
export const CENTER_FAR_ROW_ASSETS = Object.freeze({provenance:'eoere-center-far-row-provenance.json',
  sha256:'0d869dfe6e6cbc80c5fdd7683f469486d732f56710411c6e8f524a9fad6382f2'});
export const CENTER_FAR_ROW_STATUS = 'Unselected trial · center far rows · 108 bolts. Own six-case conditional references recorded; complete connection audits unfinished. Declared vector section references: left 0.924493, right 0.881709, top 0.591046, header 0.588552. Fifteen bearing diagnostic rows across eight bolts remain above trial references. Actual Cg/Cdelta and complete capacity remain unqualified. No fabrication or climbing release.';
const GEOMETRY = 'ef95c7e8c6727e3fd4051c2de0ff70e8947466ec15d2809d5df5a67c309330bd';
const RECEIPT = '608451425411001f14c768d5ee881fdf686d1d2296749b921390f0a1b7689a79';
const PARENT = '5b78a854d61d0e15dd7ddf84cb7c8b70e052443c4e79571d429158e970d1b6fc';
const SCENE = 'f0ddb1fb35bc8463fd2c76df978ba066dbf06e86c917b6c3e6fccfc58b610b7c';
const DECODED = '510806e6abbda2d4589c973bbae0b85ecf5e26b66a1afdd54bf7a1a2786a7f5b';
const BASE = 'fea/generated/v10-packer-free-center-far-row-v1/';
const ANALYSIS = BASE+'mechanics/analysis-v2/';
const RUN = BASE+'reference-readiness/runs/analysis-v2-center-far-row-v4/';
const COUNTS = {Hillman_axes:66,angles:24,bolt_stacks:108,occupied_parts:1105,panels:6,plywood_cleats:4,sawn_members:20,spacer_pieces:40,washers:216};
const OMITTED = [5,6,7,8].map(n=>'v10_top_bolt_'+String(n).padStart(3,'0'));
const REMOVALS = OMITTED.flatMap(id=>['head','head_washer','shaft','nut_washer','nut'].map(role=>id+'_'+role));
const CASES = ['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const FLAGS = ['geometry_adopted','current_alias_promoted','structural_acceptance','complete_joint_qualified','complete_group_qualified',
  'complete_connection_audits_finished','top_grid_qualified','physical_force_bounds_established','fabrication_released','climbing_released',
  'purchase_authorized','physical_changes_authorized','historical_capacity_transferred'];
const LOAD = {accessory_mass_kg:25,downward_multiplier:2,duration_factor_CD:1,horizontal_force_N:300,weight_lb:250};
const VECTOR = {base_side_left:[0.9244934112235215,'a12-rear'],base_side_right:[0.881708949145358,'k12-rear'],
  base_rail_top:[0.5910460749211319,'k12-rear'],base_header:[0.5885520338229137,'a12-rear']};
const DOCUMENTS = [{label:'Current development and trial status',path:'docs/bolted-frame-development/README.md'},
  {label:'Builder scope and holds',path:'docs/bolted-frame-development/builder-plan.md'},
  {label:'Owner direction: no wood packers',path:'docs/bolted-frame-development/owner-frame-v10/owner-no-wood-packers-v1.json'}];
const require = (ok,message)=>{if(!ok)throw new Error('Center far-row trial: '+message);};
const same = (actual,expected)=>actual&&Object.keys(actual).length===Object.keys(expected).length&&Object.entries(expected).every(([k,v])=>actual[k]===v);

export function validateCenterFarRowScene(data) {
  require(data.schema==='eoere_center_far_row_scene_delta/v1'&&data.key===CENTER_FAR_ROW_MODEL&&data.revision===CENTER_FAR_ROW_REVISION&&
    data.geometry_source?.sha256===GEOMETRY&&data.geometry_receipt?.sha256===RECEIPT&&data.parent_results?.sha256===PARENT&&
    data.parent_geometry?.sha256==='9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde'&&
    same(data.counts,COUNTS)&&data.part_count===1105,'actual 108-bolt geometry/source/census required');
  require(data.unselected_trial===true&&data.geometry_adopted===false&&data.historical_capacity_transferred===false&&
    data.fabrication_released===false&&data.climbing_released===false&&data.unchanged_mesh_bytes_copied===0,'unselected conditional scope required');
  require(data.removals?.length===20&&new Set(data.removals).size===20&&REMOVALS.every(id=>data.removals.includes(id))&&
    data.replacements?.length===1&&data.replacements[0].name==='base_rail_top'&&
    data.replacements[0].source?.sha256==='43a36738d4f50f02a1ddfcc322940ed413e135c6c136a93a2d3a15ccc63e4bd0'&&
    data.replacements[0].target_bounds_xyz_mm?.length===6&&data.replacements[0].target_bounds_xyz_mm.every(Number.isFinite)&&
    [0,2,4].every(k=>data.replacements[0].target_bounds_xyz_mm[k]<=data.replacements[0].target_bounds_xyz_mm[k+1]),
  'exact four stack removals and own fresh top-rail mesh required');
  return data;
}

export function validateCenterFarRowProvenance(data) {
  require(data.schema==='eoere_center_far_row_viewer/v1'&&data.model===CENTER_FAR_ROW_MODEL&&data.revision===CENTER_FAR_ROW_REVISION&&
    data.geometry_sha256===GEOMETRY&&same(data.counts,COUNTS)&&data.unselected_trial===true&&data.status===CENTER_FAR_ROW_STATUS&&
    data.parent_results?.sha256===PARENT&&data.parent_results.path==='site/eoere-packer-free-results.json', 'unselected own trial identity required');
  const refs={geometry_receipt:[BASE+'geometry-v1/checked-receipt-v2.json',RECEIPT],
    response_bank:[ANALYSIS+'response-bank.json','0175c7882231a24a35fd44b15b21919143f6c6a2abc9e91e623a9b6215c70bdd'],
    reference_provenance:[RUN+'authoritative-reference-provenance-v1.json','9b8608dc66ec0e41aa12077ced0a6d92ab8487acc1337a69bd12f343097c96ac'],
    display_export:[BASE+'viewer/export-v1/export-manifest.json','86ec5f9538a05b0ea0e8c9bb5286931500d92f82ec92bd08015c968d30b97e66']};
  for(const[key,[path,hash]]of Object.entries(refs))require(data.sources?.[key]?.path===path&&data.sources[key].sha256===hash,'own source required: '+key);
  require(data.scene?.path==='site/eoere-center-far-row-scene.json.gz'&&data.scene.sha256===SCENE&&data.scene.decoded_sha256===DECODED&&
    data.fresh_mesh_payloads===1&&data.removed_parts===20&&data.unchanged_mesh_bytes_copied===0&&data.ignored_runtime_dependencies===false,
  'compact shared-parent display required');
  require(same(data.load_contract,LOAD)&&data.admission_gate_N===1e-5&&data.analysis_geometry?.path===ANALYSIS+'geometry/geometry.json'&&
    data.analysis_geometry.sha256==='da449012e31f2c735d7dbffbba28f7866f50086d38974b335a5084dbff5398cc'&&
    data.cases?.length===6&&new Set(data.cases.map(row=>row.case_id)).size===6&&CASES.every(id=>data.cases.some(row=>row.case_id===id)),
  'own six-case unchanged load and analysis required');
  const hashes=[];
  for(const row of data.cases){
    require(row.both_independent_replays_admitted===true&&Number.isFinite(row.gradient_inf_N)&&row.gradient_inf_N>=0&&row.gradient_inf_N<=1e-5,
      'both own replays and unchanged residual gate required');
    for(const[key,file]of [['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key]?.path===ANALYSIS+'four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256||''),'own field/replay join required');
      hashes.push(row[key].sha256);
    }
  }
  require(new Set(hashes).size===18&&data.maximum_gradient_inf_N===3.2589200018499127e-6&&
    data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'distinct own fields/replays and maximum required');
  require(Object.keys(data.declared_vector_references||{}).length===4,'four own member references required');
  for(const[component,[index,caseId]]of Object.entries(VECTOR)){
    const row=data.declared_vector_references[component];require(row?.component===component&&row.case_id===caseId&&row.index===index&&
      row.metric==='maximum_shear_torsion_reference_upper','own conditional vector reference required: '+component);
  }
  const familyIndices={cleat_actual_perimeter_rows:0.6619898841298951,direct_elastic_steel:0.42016545959924495,
    reduced_connection_axial_bending:0.9911027229384809,timber_net_shear_torsion:0.9244934112235215,
    timber_normal_and_stability:0.8010883727737207,wood_bearing_whole_affine:1.9700425479692267};
  require(Object.keys(data.declared_family_maxima||{}).length===6,'six own reference families required');
  for(const[name,index]of Object.entries(familyIndices))require(data.declared_family_maxima[name]?.index===index&&
    CASES.includes(data.declared_family_maxima[name].case_id),'own reference family required: '+name);
  require(data.bearing_diagnostic_case_rows===15&&data.bearing_diagnostic_components===8&&data.actual_Cg_adopted===null&&
    data.actual_Cdelta_adopted===null&&data.complete_connection_capacity===null&&data.current_own_response_bank_recorded===true&&
    data.diagnostic_factor_basis==='Receiver-signature 1/n diagnostic factors; not actual Cg or complete capacity.',
  'retained trial diagnostics and null complete capacity required');
  for(const flag of FLAGS)require(data[flag]===false,'unselected unfinished scope required: '+flag);
  return data;
}

export function applyCenterFarRowDelta(THREE,parent,scene,provenance,topologies) {
  validateCenterFarRowScene(scene);validateCenterFarRowProvenance(provenance);
  require(parent.design?.key==='eoere-packer-free-standard-stock-preview'&&parent.parts.length===1125&&
    parent.meta.geometry_sha256==='9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde'&&
    parent.meta.active_results_record?.sha256===PARENT,'exact frozen 112-bolt mesh parent required');
  const old=new Map(parent.parts.map(part=>[part.name,part]));
  require(REMOVALS.every(id=>old.has(id))&&old.has('base_rail_top'),'parent removal/rail identities missing');
  const row=scene.replacements[0],geometry=meshGeometry(THREE,row.mesh,topologies);
  try {
    geometry.computeBoundingBox();geometry.computeBoundingSphere();const b=geometry.boundingBox;
    require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((value,i)=>Math.abs(value-row.target_bounds_xyz_mm[i])<.55),'rail display differs from own checked CAD bounds');
    const parts=parent.parts.filter(part=>!REMOVALS.includes(part.name)).map(part=>{
      const f=part.fabrication;if(!f)return part;
      const current={...part,fabrication:{...f,owner_frame_revision:CENTER_FAR_ROW_REVISION,actual_parts_verified:false,complete_joint_qualified:false,
        description:(f.kind==='bolt'?`${f.connection_name}: ${f.selected_bolt_grade}; nominal bolt length ${Number(f.selected_underhead_length_mm).toFixed(3)} mm. `:
          'Unselected center far-row geometry trial. ')+'Own 108-bolt six-case conditional references recorded; complete connection audits unfinished. Actual material, hardware and fit unobserved.'}};
      if(part.name==='base_rail_top'){current.geometry=geometry;delete current.path;}return current;
    });
    validateV10ComposedParts(parts,scene);
    require(parts.filter(part=>part.fabrication?.hardware_role?.endsWith('washer')).length===216&&
      parts.filter(part=>part.fabrication?.hardware_role?.startsWith('spacer')).length===40,'108-stack washer/spacer inventory differs');
    for(const id of [...REMOVALS,'base_rail_top'])old.get(id).geometry?.dispose();
    return {...parent,parts,design:{...parent.design,key:CENTER_FAR_ROW_MODEL,qualified_for_design:false,documents:DOCUMENTS},
      meta:{revision:CENTER_FAR_ROW_REVISION,geometry_sha256:GEOMETRY,layout_sha256:RECEIPT,provenance_sha256:CENTER_FAR_ROW_ASSETS.sha256,
        counts:COUNTS,status:provenance.status,unselected_trial:true,packers_present:false,current_response_computed:true,
        current_own_response_bank_recorded:true,matched_results_pending:false,planning_mass_kg:null,
        load_contract:provenance.load_contract,case_rows:provenance.cases,maximum_gradient_inf_N:provenance.maximum_gradient_inf_N,
        declared_vector_references:provenance.declared_vector_references,declared_family_maxima:provenance.declared_family_maxima,
        diagnostic_case_rows:15,diagnostic_components:8,actual_Cg_adopted:null,actual_Cdelta_adopted:null,complete_connection_capacity:null,
        ...Object.fromEntries(FLAGS.map(flag=>[flag,false])),physical_release:false,
        parent_sources:{mesh_parent_results:scene.parent_results},portable_sources:{geometry:scene.geometry_source,...provenance.sources}}};
  }catch(error){geometry.dispose();parent.parts.forEach(part=>part.geometry?.dispose());throw error;}
}

async function readAsset(name,hash){const response=await fetch(new URL(name,import.meta.url));require(response.ok,'portable asset unavailable: '+name);
  const raw=await response.arrayBuffer();require(await sha256(raw)===hash,'portable asset bytes changed: '+name);return raw;}

export async function loadCenterFarRowScene(THREE,options,parentLoader=loadPackerFreeResultsScene){
  const provenance=validateCenterFarRowProvenance(JSON.parse(new TextDecoder().decode(await readAsset(CENTER_FAR_ROW_ASSETS.provenance,CENTER_FAR_ROW_ASSETS.sha256))));
  const encoded=await readAsset('eoere-center-far-row-scene.json.gz',SCENE);
  const decoded=await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded)===DECODED,'decoded rail patch changed');const scene=validateCenterFarRowScene(JSON.parse(new TextDecoder().decode(decoded))),topologies=new Map();
  for(const[hash,row]of Object.entries(scene.triangle_topologies)){const indices=decodeTypedArray(row.triangle_indices_base64,row.triangle_component_type,row.index_count);
    require(await sha256(indices.bytes)===hash,'topology bytes changed');topologies.set(hash,{...row,indices:indices.values});}
  return applyCenterFarRowDelta(THREE,await parentLoader(THREE,options),scene,provenance,topologies);
}
