import {loadRelocatedRearGeometryScene,RELOCATED_REAR_MODEL} from './eoere-v11-relocated-rear-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const RELOCATED_REAR_RESULTS_ASSET=Object.freeze({path:'site/eoere-v11-relocated-rear-results.json',sha256:'ceffae758ad64905574a9e92d41347fce2736fc8276d22b54c24679ea01f9b88'});
const PREFIX='docs/bolted-frame-development/owner-frame-v11/relocated-rear-pair/';
const ANALYSIS='fea/generated/v11-relocated-rear-pair-v1/mechanics/analysis-v2/';
const SOURCES={response_bank:{path:PREFIX+'response-bank.json',sha256:'ef84f0a7e8630f277ea185a042babd7dd73d54198b13e7197b01336efa9effbd'},
  reference_completion:{path:PREFIX+'reference-completion.json',sha256:'4ace84e17707f7b56367ec36dfe25707c6050505d90ab520cc8c17a48b08e029'},
  contracted_rear_summary:{path:PREFIX+'contracted-rear-summary.json',sha256:'0eacfa18918c342104e225302f139b3e14c13cd1a2abd94914f36bca11cbcb8a'},
  mixed_common_work_summary:{path:PREFIX+'mixed-common-work-summary.json',sha256:'b4c9bafc06af65d62b23d4b18e1ca96137c5599783aa4664e824ef3696494287'},
  mixed_reference_controls:{path:PREFIX+'mixed-control-receipt.json',sha256:'5d2b0c11461d55147d59601a6360458c26fcc3b25004c0e071b8bb7e8c8977e7'}};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const FAMILIES=['timber_net_shear_torsion','timber_normal_and_stability','cleat_actual_perimeter_rows','direct_elastic_steel','wood_bearing_whole_affine','reduced_connection_axial_bending'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Relocated rear results: '+message);};
const equalRef=(a,b)=>a&&a.path===b.path&&a.sha256===b.sha256;
const index=value=>Number.isFinite(value)&&value>=0;

export function validateRelocatedRearResults(data){
  require(data.schema==='eoere_v11_relocated_rear_viewer_results/v1'&&data.model===RELOCATED_REAR_MODEL&&data.revision==='v11-relocated-rear-pair-v1','own model required');
  require(data.geometry.sha256==='9bab57acdfd7fd3d72478a9f44e707413d74f0dded6a106346ccb0807eb73d9f'&&
    data.geometry_receipt.path===PREFIX+'geometry-receipt.json'&&data.geometry_receipt.sha256==='e2fd4bf18df8fa8414ebe65d18865ac2a41deb1e56100dab5cd50a0f27ee63a6'&&
    data.geometry_provenance.path==='site/eoere-v11-relocated-rear-provenance.json'&&data.geometry_provenance.sha256==='aa85ff0be29a73222551a14091d736d62dc08116b94c703c503fabd0754cc0e0'&&
    data.analysis_geometry.path===ANALYSIS+'geometry/geometry.json'&&data.analysis_geometry.sha256==='cbe32f947e200945d10eecc0f8bf600572c0ea7866097eafe43323e85bde1a74','own frozen geometry/preparation required');
  require(Object.keys(data.sources).length===5&&Object.entries(SOURCES).every(([key,ref])=>equalRef(data.sources[key],ref)),'own bank/completion/contracted/mixed source pins required');
  const load=data.load_contract;
  require(Object.keys(load).length===5&&load.weight_lb===250&&load.downward_multiplier===2&&load.horizontal_force_N===300&&
    load.accessory_mass_kg===25&&load.duration_factor_CD===1&&data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,'fixed250lb recipe without interpolation required');
  require(data.cases.length===6&&new Set(data.cases.map(row=>row.case_id)).size===6&&data.independent_replays===12,'six own cases and twelve replays required');
  const hashes=[];
  for(const row of data.cases){require(CASES.includes(row.case_id)&&row.both_independent_replays_admitted===true&&index(row.gradient_inf_N)&&row.gradient_inf_N<1e-5,'own admitted case required');
    for(const[key,file]of[['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key].path===ANALYSIS+'four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256),'own case/replay join required');hashes.push(row[key].sha256);}}
  require(new Set(hashes).size===18&&data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'distinct own fields/replays and maximum required');
  require(Object.keys(data.family_references).length===6&&FAMILIES.every(key=>Object.hasOwn(data.family_references,key)),'six separate reference families required');
  for(const row of Object.values(data.family_references))require(index(row.maximum.index)&&CASES.includes(row.maximum.case_id)&&Number.isInteger(row.above_one_count)&&row.above_one_count>=0,'finite conditional family references required');
  const rear=data.rear,p=rear.contracted_common_work_reference,e=rear.separate_original_ellipse_reference,n=rear.separate_continuous_necessary_bound;
  require(rear.axis_count===6&&rear.axis_case_states===36&&rear.receiver_case_certificates===72&&p.states===36&&e.states===36,'own36rear states and72receiver certificates required');
  require(p.source.sha256===SOURCES.contracted_rear_summary.sha256&&p.complete_joint_qualified===false&&p.physical_failure_claim===false&&
    index(p.maximum)&&p.maximum===p.governing.contracted_bearing_index&&p.above_one_state_count===0&&p.bearing_plus_unchanged_hinge_above_one_state_count===0&&p.maximum<1,'contracted fixed-field reference is not complete capacity');
  require(index(e.maximum)&&e.maximum===p.governing.original_ellipse_cell_index&&e.above_one_count===0&&
    index(n.maximum_lower_bound)&&n.maximum_lower_bound<=e.maximum&&n.receiver_case_rows===72,'ellipse and necessary bound stay separate');
  require(p.governing.lambda>0&&p.governing.lambda<=1&&Math.abs(p.maximum-e.maximum/p.governing.lambda)<1e-12,'declared contraction normalization differs');
  for(const count of Object.values(data.connection_diagnostic_counts))require(Number.isInteger(count)&&count>=0,'separate diagnostic counts required');
  const mixed=data.mixed_common_work_reference,s=mixed.summary,b=mixed.basis;
  require(equalRef(mixed.source,SOURCES.mixed_common_work_summary)&&equalRef(mixed.controls,SOURCES.mixed_reference_controls)&&
    equalRef(mixed.response_bank,SOURCES.response_bank),'mixed source and own bank joins required');
  require(b.A574_Fyb_scenario_psi===45000&&b.Grade5_Fyb_scenario_psi===92000&&b.hinge_law==='Mp/4'&&b.bearing_law==='contracted_common_work_projected_bearing','declared mixed scenario basis required');
  require(s.state_count===144&&s.receiver_case_count===432&&s.endpoint_count===1104&&s.above_one_count===3&&s.above_one_rows.length===3,'own mixed inventory and three reference flags required');
  const flagged=s.above_one_rows.map(row=>row.axis_id+'/'+row.case_id).sort();
  require(JSON.stringify(flagged)===JSON.stringify(['v11_cleat_left_side_1/a12-forward','v11_cleat_left_side_1/a12-left','v11_cleat_right_side_1/k12-right']),'exact own mixed flag states required');
  for(const row of s.above_one_rows)require(row.conditional_Fyb_reference_psi===45000&&index(row.Mp4_hinge_index)&&row.Mp4_hinge_index>1&&
    row.combined_common_work_Mp4_index===row.Mp4_hinge_index&&index(row.Mp4_required_Fyb_ksi)&&
    Math.abs(row.Mp4_hinge_index-row.Mp4_required_Fyb_ksi/45)<1e-12,'conditional generic45 bending reference differs');
  require(s.maximum_Mp4_hinge_index===Math.max(...s.above_one_rows.map(row=>row.Mp4_hinge_index))&&
    s.maximum_required_Fyb_ksi===Math.max(...s.above_one_rows.map(row=>row.Mp4_required_Fyb_ksi))&&
    index(s.maximum_contracted_bearing_index)&&s.maximum_contracted_bearing_index<1&&
    s.maximum_combined_common_work_Mp4_index===Math.max(s.maximum_Mp4_hinge_index,s.maximum_contracted_bearing_index),'separate mixed reference maxima differ');
  for(const key of['actual_Cg','actual_Cdelta','actual_Fyb','complete_joint_capacity'])require(mixed[key]===null,'mixed actual capacity/factors remain null');
  for(const key of['complete_joint_qualified','physical_failure_claim','structural_acceptance'])require(mixed[key]===false,'mixed reference flags are not physical/joint acceptance');
  require(data.current_response_computed===true&&data.trial_selected===false&&data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&
    data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null,'conditional references do not select or qualify the trial');
  for(const key of FALSE_FLAGS)require(data[key]===false,'qualification/release boundary: '+key);
  return data;
}

export function relocatedRearResultsStatus(input){
  const data=validateRelocatedRearResults(input),f=data.family_references,rear=data.rear,p=rear.contracted_common_work_reference,mixed=data.mixed_common_work_reference.summary;
  return 'Unselected relocated upper-rear pair · 114 stacks · four spacers. Six own fixed 250 lb cases and twelve independent replays admitted. '+
    `Conditional member ${f.timber_net_shear_torsion.maximum.index.toFixed(6)}, normal/stability ${f.timber_normal_and_stability.maximum.index.toFixed(6)}, `+
    `cleat ${f.cleat_actual_perimeter_rows.maximum.index.toFixed(6)} and separate elastic steel ${f.direct_elastic_steel.maximum.index.toFixed(6)} references. `+
    `Mixed generic 45 ksi Fyb / Mp/4 bending reference: ${mixed.above_one_count} conditional flags across 144 states, maximum ${mixed.maximum_Mp4_hinge_index.toFixed(6)}; required Fyb ${mixed.maximum_required_Fyb_ksi.toFixed(6)} ksi. `+
    'Flagged states: '+mixed.above_one_rows.map(row=>`${row.axis_id}/${row.case_id} ${row.Mp4_hinge_index.toFixed(6)}`).join('; ')+'. '+
    `Contracted mixed bearing reference ${mixed.maximum_contracted_bearing_index.toFixed(6)}, zero above one. `+
    `Primary contracted common-work rear reference ${p.maximum.toFixed(6)} across 36 states, zero above one. `+
    `Separate original ellipse reference ${rear.separate_original_ellipse_reference.maximum.toFixed(6)}; continuous necessary lower bound ${rear.separate_continuous_necessary_bound.maximum_lower_bound.toFixed(6)}. `+
    `Legacy local wood-pressure diagnostic: ${f.wood_bearing_whole_affine.above_one_count} rows; group-reduced N/M: ${f.reduced_connection_axial_bending.above_one_count}. `+
    'Actual Fyb, group factors, complete connections and physical fit remain unqualified. Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. No fabrication or climbing release.';
}

export function applyRelocatedRearResults(scene,input){
  const data=validateRelocatedRearResults(input);
  require(scene.design.key===data.model&&scene.parts.length===1099&&scene.meta.geometry_only===true&&scene.meta.current_response_computed===false&&
    scene.meta.geometry_sha256===data.geometry.sha256&&scene.meta.layout_sha256===data.geometry_receipt.sha256&&
    scene.meta.provenance_sha256===data.geometry_provenance.sha256,'own raw geometry stage required');
  return {...scene,meta:{...scene.meta,status:relocatedRearResultsStatus(data),geometry_only:false,analysis_pending:false,current_response_computed:true,
    current_own_response_bank_recorded:true,family_references:data.family_references,rear_references:data.rear,connection_diagnostic_counts:data.connection_diagnostic_counts,
    mixed_common_work_reference:data.mixed_common_work_reference,
    case_rows:data.cases,independent_replays:12,maximum_gradient_inf_N:data.maximum_gradient_inf_N,load_contract:data.load_contract,
    trial_selected:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
    accepted_connection_exceedance_count:null,fixed_load_only:true,weight_interpolation_available:false,planning_mass_kg:null,
    ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),
    portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadRelocatedRearResultsScene(THREE,options,geometryLoader=loadRelocatedRearGeometryScene){
  const response=await fetch(new URL(RELOCATED_REAR_RESULTS_ASSET.path.slice(5),import.meta.url));require(response.ok,'own result asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===RELOCATED_REAR_RESULTS_ASSET.sha256,'own result asset source pin differs');
  const data=validateRelocatedRearResults(JSON.parse(new TextDecoder().decode(raw)));
  return applyRelocatedRearResults(await geometryLoader(THREE,options),data);
}
