import {loadShorterBoltScene,SHORTER_MODEL,SHORTER_ASSETS} from './eoere-v11-shorter-bolts-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const SHORTER_RESULTS_ASSET=Object.freeze({path:'site/eoere-v11-shorter-bolts-results.json',sha256:'1997d3a0fb2309e6e1e9f9233c401658db8b1d235228a06d2712f634e55f52b5'});
const GEOMETRY='73ce1f19ce97959d3867984cc813c178895b50212128fce6a976548ad6bce4c8';
const PREFIX='docs/bolted-frame-development/owner-frame-v11/shorter-bolts/';
const RECEIPT={path:PREFIX+'geometry-receipt.json',sha256:'cc2a1688270cd56a36176ff1957ef769d1a84c54eba8c8d255d2b65ec8bcfee9'};
const SOURCES={response_bank:{path:PREFIX+'response-bank.json',sha256:'0ac9bb41342279c536e955e30bc2b5588e07c235843186820982e7a60455c35c'},
  reference_review:{path:PREFIX+'reference-review.json',sha256:'9a95d840a81205e2ef6c9cb6924f8b0f27811339b4eaceff9359d0833cf70c72'}};
const ANALYSIS='fea/generated/v11-shorter-bolts-v1/mechanics/analysis-v3/';
const LOAD={accessory_mass_kg:25,downward_multiplier:2,duration_factor_CD:1,horizontal_force_N:300,weight_lb:250};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const MEMBERS=['base_side_left','base_side_right','base_rail_top','base_header'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Shorter-bolt results: '+message);};
const same=(a,b)=>a&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([key,value])=>a[key]===value);
const unique=values=>new Set(values).size===values.length;
const finiteIndex=value=>Number.isFinite(value)&&value>=0;
const text=value=>typeof value==='string'&&value.trim().length>0;

export function validateShorterBoltResults(data){
  require(data.schema==='eoere_v11_shorter_bolt_viewer_results/v1'&&data.model===SHORTER_MODEL&&data.geometry_revision==='v11-shorter-bolts-v1'&&
    data.geometry_sha256===GEOMETRY&&same(data.geometry_receipt,RECEIPT)&&
    same(data.geometry_provenance,{path:'site/'+SHORTER_ASSETS.provenance,sha256:SHORTER_ASSETS.sha256})&&
    same(data.analysis_geometry,{path:ANALYSIS+'geometry/geometry.json',sha256:'56b543fdc83ce40bcd2088431bc6caf15f0b491f8297d91b8e0926c38b2f8596'})&&
    data.counts?.occupied_parts===1089&&data.counts.bolt_stacks===112&&data.counts.spacer_pieces===4&&data.counts.Hillman_axes===66&&
    data.counts.angles===24,'exact own shorter-bolt geometry and analysis preparation required');
  require(data.sources&&Object.keys(data.sources).length===2,'the own bank and canonical presentation source are required');
  for(const[key,ref]of Object.entries(SOURCES))require(same(data.sources[key],ref),'source differs: '+key);
  require(same(data.load_contract,LOAD)&&data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,
    'the own fixed250lb load contract has no weight interpolation');
  require(data.admission_gate_N===1e-5&&data.all_six_cases_and_both_replays_admitted===true&&data.independent_replays===12&&
    data.cases?.length===6&&unique(data.cases.map(row=>row.case_id))&&CASES.every(id=>data.cases.some(row=>row.case_id===id)),
    'six distinct own cases and twelve admitted independent replays required');
  const hashes=[];
  for(const row of data.cases){
    require(row.both_independent_replays_admitted===true&&finiteIndex(row.gradient_inf_N)&&row.gradient_inf_N<=1e-5,'admitted residual and both replays required');
    for(const[key,file]of[['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key]?.path===ANALYSIS+'four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256||''),'own field and replay case join required');hashes.push(row[key].sha256);}
  }
  require(unique(hashes)&&data.maximum_gradient_inf_N===4.7353206167333184e-7&&
    data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'distinct own field/replay bytes and exact residual maximum required');
  require(data.member_vector_maxima&&Object.keys(data.member_vector_maxima).length===4&&
    MEMBERS.every(id=>data.member_vector_maxima[id]?.component===id),'four own conditional member references required');
  for(const summaries of[data.member_vector_maxima,data.family_maxima]){
    require(summaries&&Object.keys(summaries).length>0,'own conditional reference summaries required');
    for(const row of Object.values(summaries))require(finiteIndex(row.index)&&CASES.includes(row.case_id)&&text(row.component),'finite own conditional reference and case witness required');
  }
  const presentation=data.viewer_presentation;
  require(text(presentation?.status)&&Array.isArray(presentation.reference_flags)&&presentation.reference_flags.every(row=>
    text(row.label)&&text(row.scope)&&text(row.status)&&(row.count===null||Number.isInteger(row.count)&&row.count>=0)),
    'source-authored wording and explicit reference flag scopes required; unevaluated is not zero');
  const axisTexts=presentation.axis_reference_texts??{};
  require(axisTexts&&typeof axisTexts==='object'&&!Array.isArray(axisTexts)&&Object.values(axisTexts).every(text),'explicit own axis wording required');
  require(data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null&&
    data.geometry_only===false&&data.analysis_pending===false&&data.current_response_computed===true&&data.current_own_response_bank_recorded===true,
    'own references are available while actual factors and complete capacity remain unresolved');
  for(const key of FALSE_FLAGS)require(data[key]===false,'qualification/release boundary: '+key);
  return data;
}

export function shorterBoltResultsStatus(input){
  const data=validateShorterBoltResults(input),members=data.member_vector_maxima,cleat=data.family_maxima.cleat_actual_perimeter_rows;
  const flags=data.viewer_presentation.reference_flags;
  return data.viewer_presentation.status+' Conditional vector section references: '+
    `left ${members.base_side_left.index.toFixed(6)}, right ${members.base_side_right.index.toFixed(6)}, top ${members.base_rail_top.index.toFixed(6)}, header ${members.base_header.index.toFixed(6)}; `+
    `cleat perimeter ${cleat.index.toFixed(6)} at ${cleat.wall_mm} mm. `+
    'Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. '+
    'Separate diagnostic and scenario rows: '+flags.map(row=>`${row.label}: ${row.count===null?'unevaluated':row.count}`).join('; ')+'.';
}

export function applyShorterBoltResults(scene,input){
  const data=validateShorterBoltResults(input);
  require(scene.design?.key===SHORTER_MODEL&&scene.parts?.length===1089&&scene.meta?.geometry_sha256===GEOMETRY&&
    scene.meta.layout_sha256===RECEIPT.sha256&&scene.meta.provenance_sha256===SHORTER_ASSETS.sha256&&scene.meta.geometry_only===true&&
    scene.meta.analysis_pending===true&&scene.meta.current_response_computed===false,'the frozen own geometry-only loader is required');
  const axes=new Set(scene.parts.filter(part=>part.fabrication?.kind==='bolt').map(part=>part.fabrication.connection_name));
  const axisTexts=data.viewer_presentation.axis_reference_texts??{};
  require(axes.size===112&&Object.keys(axisTexts).every(id=>axes.has(id)),'explicit per-axis references must join this exact geometry');
  const parts=scene.parts.map(part=>{
    if(!part.fabrication)return part;
    const f={...part.fabrication,description:part.fabrication.description?.replace('Shorter-bolt geometry trial; matched analysis pending.',
      'Own fixed-load references are available; complete connections remain unresolved.'),complete_joint_qualified:false};
    for(const key of['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity'])delete f[key];
    if(f.kind==='bolt'&&axisTexts[f.connection_name])f.analysis_reference=axisTexts[f.connection_name];
    return {...part,fabrication:f};
  });
  return {...scene,parts,meta:{...scene.meta,status:shorterBoltResultsStatus(data),geometry_only:false,analysis_pending:false,
    current_response_computed:true,current_own_response_bank_recorded:true,active_results_record:SHORTER_RESULTS_ASSET,
    load_contract:data.load_contract,case_rows:data.cases,independent_replays:12,maximum_gradient_inf_N:data.maximum_gradient_inf_N,
    member_vector_maxima:data.member_vector_maxima,family_maxima:data.family_maxima,reference_flags:data.viewer_presentation.reference_flags,
    actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
    ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadShorterBoltResultsScene(THREE,options,geometryLoader=loadShorterBoltScene){
  const response=await fetch(new URL('eoere-v11-shorter-bolts-results.json',import.meta.url));require(response.ok,'own fresh results unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===SHORTER_RESULTS_ASSET.sha256,'own fresh results bytes changed');
  const data=validateShorterBoltResults(JSON.parse(new TextDecoder().decode(raw)));
  return applyShorterBoltResults(await geometryLoader(THREE,options),data);
}
