import {loadV11V9EightBoltScene,V11_MODEL,V11_ASSETS} from './eoere-v11-v9-eight-bolt-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const V11_RESULTS_ASSET=Object.freeze({path:'site/eoere-v11-results.json',sha256:'d729953d54f9b7f989c5155e115758cbd4845bff0795ab27a496b3188c9e2aaf'});
const GEOMETRY='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7';
const RECEIPT='576159eb2dcd791cf1a983165728e173fa594015fd7ab39ed9d69c1cb591a330';
const PREFIX='docs/bolted-frame-development/owner-frame-v11/';
const ANALYSIS='fea/generated/v11-v9-eight-bolt-v1/mechanics/analysis-v4/four-hosts/';
const SOURCES={response_bank:['response-bank.json','482d8e5cf5eec0566a7eb637666137350cbf90f1674f909241c78a103f615963'],
  reference_review:['reference-review.json','8551209039282dff8f3fdd2329b2d3d4396972ed1b74a19e0e5287fbb74c53aa'],
  property_comparison:['grade5-property-comparison.json','06e30473a693f1701f65889507590d16d872950137991d5c267d75ba8825d581'],
  preserved_generic_rows:['connection-capacity-followthrough.json','c19c4a4e7c195dcc7e294090bb0307dd24c87d41adad6ead09eae4a1c0108dcc'],
  row_comparison:['grade5-row-comparison.json','a61f5592607b972b734b753b53971cb845a174c3b28cf1008232a5f3d1072f88']};
const LOAD={accessory_mass_kg:25,downward_multiplier:2,duration_factor_CD:1,horizontal_force_N:300,weight_lb:250};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const VECTOR={base_side_left:.9650288506038316,base_side_right:.9260229699214635,base_rail_top:.6184835117174111,base_header:.5528302165755942};
const require=(ok,message)=>{if(!ok)throw new Error('V11 results: '+message);};
const same=(a,b)=>a&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([key,value])=>a[key]===value);
const unique=values=>new Set(values).size===values.length;
const finiteIndex=value=>Number.isFinite(value)&&value>=0;

export function validateV11Results(data){
  require(data.schema==='eoere_v11_viewer_results/v1'&&data.model===V11_MODEL&&data.geometry_revision==='v11-v9-eight-bolt-v4'&&
    data.geometry_sha256===GEOMETRY&&data.geometry_receipt?.path===PREFIX+'geometry-receipt.json'&&data.geometry_receipt.sha256===RECEIPT&&
    data.geometry_provenance?.path==='site/eoere-v11-v9-eight-bolt-provenance.json'&&data.geometry_provenance.sha256===V11_ASSETS.sha256&&
    data.analysis_geometry?.path==='fea/generated/v11-v9-eight-bolt-v1/mechanics/analysis-v4/geometry/geometry.json'&&
    data.analysis_geometry.sha256==='1f18ac349bb483f2179e0a7231d808d11e5f3b484cafa77dc51a2972d5022f60'&&
    data.counts?.occupied_parts===1109&&data.counts.bolt_stacks===112&&
    data.counts.spacer_pieces===24&&data.counts.Hillman_axes===66,'exact own frozen geometry required');
  require(data.sources&&Object.keys(data.sources).length===5,'five own public evidence sources required');
  for(const[key,[file,hash]]of Object.entries(SOURCES))require(data.sources[key]?.path===PREFIX+file&&data.sources[key].sha256===hash,'source differs: '+key);
  require(same(data.load_contract,LOAD)&&data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,
    'the fixed 250 lb load contract has no weight interpolation');
  require(data.admission_gate_N===1e-5&&data.all_six_cases_and_both_replays_admitted===true&&data.independent_replays===12&&
    data.cases?.length===6&&unique(data.cases.map(row=>row.case_id))&&CASES.every(id=>data.cases.some(row=>row.case_id===id)),
    'six own cases and twelve admitted independent replays required');
  const hashes=[];
  for(const row of data.cases){
    require(row.both_independent_replays_admitted===true&&finiteIndex(row.gradient_inf_N)&&row.gradient_inf_N<=1e-5,'admitted residual/replays required');
    for(const[key,file]of[['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key]?.path===ANALYSIS+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256||''),'own case field/replay join required');hashes.push(row[key].sha256);}
  }
  require(unique(hashes)&&data.maximum_gradient_inf_N===8.019646646761913e-6&&
    data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'own distinct fields/replays and exact maximum required');
  require(data.member_vector_maxima&&Object.keys(data.member_vector_maxima).length===4,'four conditional member references required');
  for(const[id,index]of Object.entries(VECTOR))require(data.member_vector_maxima[id]?.component===id&&
    data.member_vector_maxima[id].index===index&&CASES.includes(data.member_vector_maxima[id].case_id),'own vector reference differs: '+id);
  require(data.family_maxima?.cleat_actual_perimeter_rows?.index===.43859084780823315&&
    data.family_maxima.cleat_actual_perimeter_rows.wall_mm===36.5&&data.family_maxima.timber_normal_and_stability.index===.7783969878714706&&
    data.family_maxima.direct_elastic_steel.index===.6983836860181827,'own cleat,normal and separate steel references required');
  const force=data.force_only,property=force?.property_specification;
  require(force?.conditional_property_maximum===.8420030182968952&&force.conditional_property_flag_rows===0&&
    force.generic45_maximum===1.189314587548981&&force.generic45_flag_rows===4&&force.mapped_axes===88&&force.Grade5_92ksi_mapped_axes===84&&
    force.unchanged_A574_mapped_axes===4&&property?.Fyb_psi===92000&&property.automatic_actual_property_adoption===false&&
    property.actual_conformity_unobserved===true,'conditional property comparison cannot become actual adoption or a complete pass');
  const axisRows=data.axis_force_only_maxima;
  require(axisRows?.length===88&&unique(axisRows.map(row=>row.axis_id))&&data.unsupported_mixed_axes?.length===24&&
    unique([...axisRows.map(row=>row.axis_id),...data.unsupported_mixed_axes]),'88 mapped and24 unsupported axes must stay distinct');
  for(const row of axisRows)require(typeof row.axis_id==='string'&&CASES.includes(row.case_id)&&finiteIndex(row.index)&&
    ['Im','Is','II','IIIm','IIIs','IV'].includes(row.governing_mode)&&typeof row.class_code==='string'&&row.conditional_steel_Fe_unassigned===true,
    'finite conditional force-only axis reference required');
  require(axisRows.filter(row=>row.class_code.includes('Fyb92')).length===84&&
    axisRows.filter(row=>row.class_code==='wood_wood_G0p50_Fyb45_scenario_only').length===4&&
    Math.max(...axisRows.map(row=>row.index))===force.conditional_property_maximum,'own eligible property-family maxima required');
  const bounds=data.row_bounds;
  require(bounds?.conditional_property_maximum===2.2080838963062854&&bounds.inconclusive_flag_rows===21&&bounds.flagged_interfaces===10&&
    bounds.below_one_rows===231&&bounds.property92_recalculated===true&&bounds.preserved_generic45_maximum===2.665863124575772&&
    bounds.above_one_is_inconclusive===true&&bounds.complete_group_pass===null,'fresh row bounds remain inconclusive, separate from force-only references');
  require(data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null&&
    data.geometry_only===false&&data.analysis_pending===false&&data.current_response_computed===true&&data.current_own_response_bank_recorded===true,
    'own results available while actual properties and full capacity remain unresolved');
  for(const key of FALSE_FLAGS)require(data[key]===false,'qualification/release boundary: '+key);
  return data;
}

export function v11ResultsStatus(data){
  const d=validateV11Results(data),v=d.member_vector_maxima,f=d.force_only,b=d.row_bounds;
  return 'V9 cleats · 4×6 top · 112 bolts · six own 250 lb cases and 12 independent replays admitted. '+
    `Conditional vector references: left ${v.base_side_left.index.toFixed(6)}, right ${v.base_side_right.index.toFixed(6)}, top ${v.base_rail_top.index.toFixed(6)}, header ${v.base_header.index.toFixed(6)}; cleat at 36.5 mm ${d.family_maxima.cleat_actual_perimeter_rows.index.toFixed(6)}. `+
    `Normal/stability ${d.family_maxima.timber_normal_and_stability.index.toFixed(6)}; separate elastic steel ${d.family_maxima.direct_elastic_steel.index.toFixed(6)}. `+
    `Conditional Grade 5/F606 force-only maximum ${f.conditional_property_maximum.toFixed(6)}, zero flags across 88 mapped axes (84 Grade 5; 4 A574 unchanged); generic 45 ksi comparison ${f.generic45_maximum.toFixed(6)}, four flags. `+
    `Fresh 92 ksi row-bound maximum ${b.conditional_property_maximum.toFixed(6)}: 21 bounds across 10 interfaces remain inconclusive. `+
    '24 mixed axes and complete connections remain unresolved. Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. No fabrication or climbing release.';
}

export function applyV11Results(scene,input){
  const data=validateV11Results(input);
  require(scene.design?.key===V11_MODEL&&scene.parts?.length===1109&&scene.meta?.geometry_sha256===GEOMETRY&&
    scene.meta.layout_sha256===RECEIPT&&scene.meta.provenance_sha256===V11_ASSETS.sha256&&scene.meta.geometry_only===true&&scene.meta.analysis_pending===true,
    'unchanged own geometry-only loader required');
  const maxima=new Map(data.axis_force_only_maxima.map(row=>[row.axis_id,row])),unsupported=new Set(data.unsupported_mixed_axes);
  const axes=new Set(scene.parts.filter(part=>part.fabrication?.kind==='bolt').map(part=>part.fabrication.connection_name));
  require(axes.size===112&&[...maxima.keys(),...unsupported].every(id=>axes.has(id)),'per-axis references must join this exact geometry');
  const parts=scene.parts.map(part=>{
    if(!part.fabrication)return part;
    const f=part.fabrication,row=maxima.get(f.connection_name),mixed=unsupported.has(f.connection_name);
    const analysisReference=row?`Fixed 250 lb conditional force-only index ${row.index.toFixed(6)} (${row.case_id}, mode ${row.governing_mode}; ${row.class_code.includes('Fyb92')?'Grade 5/F606 92 ksi scenario':'retained A574 generic 45 ksi scenario'}${row.class_code.startsWith('wood_steel_')?', unadopted steel Fu370 MPa scenario':''}). Actual properties, Cg/Cdelta, couples and complete joint capacity remain unresolved.`:
      mixed?'Mixed-media axis: force-only capacity mapping unsupported. No reference index or complete joint pass is assigned.':'';
    return {...part,fabrication:{...f,description:f.description?.replace('Geometry only; analysis pending.',
      'Own fixed-load six-case references recorded; complete connections unresolved.'),analysis_reference:analysisReference,
      conditional_force_only_reference:row||null,unsupported_mixed_capacity:mixed,complete_joint_qualified:false}};
  });
  return {...scene,parts,meta:{...scene.meta,status:v11ResultsStatus(data),geometry_only:false,analysis_pending:false,
    current_response_computed:true,current_own_response_bank_recorded:true,active_results_record:V11_RESULTS_ASSET,
    load_contract:data.load_contract,case_rows:data.cases,independent_replays:12,maximum_gradient_inf_N:data.maximum_gradient_inf_N,
    member_vector_maxima:data.member_vector_maxima,family_maxima:data.family_maxima,force_only:data.force_only,row_bounds:data.row_bounds,
    unsupported_mixed_axes:data.unsupported_mixed_axes,actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,
    complete_connection_capacity:null,...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),
    portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadV11ResultsScene(THREE,options,geometryLoader=loadV11V9EightBoltScene){
  const response=await fetch(new URL('eoere-v11-results.json',import.meta.url));require(response.ok,'own current results unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===V11_RESULTS_ASSET.sha256,'own current results bytes changed');
  const data=validateV11Results(JSON.parse(new TextDecoder().decode(raw)));
  return applyV11Results(await geometryLoader(THREE,options),data);
}
