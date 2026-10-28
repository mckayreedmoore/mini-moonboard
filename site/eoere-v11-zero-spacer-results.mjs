import {loadZeroSpacerGeometryScene,ZERO_SPACER_MODEL} from './eoere-v11-zero-spacer-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const ZERO_SPACER_RESULTS_ASSET=Object.freeze({"path": "site/eoere-v11-zero-spacer-results.json", "sha256": "ddf0835b10ce6074caa7fde8d94accedfb53706f38a7894a786a39b387c19b57"});
const PREFIX='docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/';
const ANALYSIS="fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3/";
const SOURCES={"contracted_rear_summary": {"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/contracted-rear-summary.json", "sha256": "92975826b4824df5646037cebf58c1ea30fc9565add8c3ba31c111b746f2cc2b"}, "mixed_common_work_summary": {"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/mixed-common-work-summary.json", "sha256": "65a7c1387752945a0c24609f165def4c4d7adfc23d76874233b5b287a5d243b2"}, "mixed_reference_controls": {"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/mixed-current-controls.json", "sha256": "89cb9b3986b23839864384355700f9f966cf3b51c17f8c810f8f4cc8224d6b95"}, "reference_completion": {"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/reference-completion.json", "sha256": "4328fca61c970ddba797f8530afda1398beeae4101b1dc5a14a7c2058c7664f8"}, "response_bank": {"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/response-bank.json", "sha256": "a87f9edfa6006c206e883dd28108c8fa78369dbc8e40a256f141405fcfa5d092"}};
const EXPECTED_MIXED={"above_one_count": 3, "above_one_rows": [{"Mp4_hinge_index": 1.2366219810676662, "Mp4_required_Fyb_ksi": 55.64798914804497, "axis_id": "v11_cleat_left_side_1", "case_id": "a12-forward", "combined_common_work_Mp4_index": 1.2366219810676662, "conditional_Fyb_reference_psi": 45000.0}, {"Mp4_hinge_index": 1.1992681695695138, "Mp4_required_Fyb_ksi": 53.96706763062812, "axis_id": "v11_cleat_left_side_1", "case_id": "a12-left", "combined_common_work_Mp4_index": 1.1992681695695138, "conditional_Fyb_reference_psi": 45000.0}, {"Mp4_hinge_index": 1.186202648459361, "Mp4_required_Fyb_ksi": 53.379119180671246, "axis_id": "v11_cleat_right_side_1", "case_id": "k12-right", "combined_common_work_Mp4_index": 1.186202648459361, "conditional_Fyb_reference_psi": 45000.0}], "endpoint_count": 1152, "fresh_Mp5_hinge_above_one_count_preserved": 6, "fresh_Mp5_hinge_maximum_preserved": 1.5457774763345826, "governing_axis_case": ["v11_cleat_left_side_1", "a12-forward"], "maximum_Mp4_hinge_index": 1.2366219810676662, "maximum_combined_common_work_Mp4_index": 1.2366219810676662, "maximum_contracted_bearing_index": 0.4561940007546075, "maximum_required_Fyb_ksi": 55.64798914804497, "receiver_case_count": 432, "state_count": 144};
const INTAKE={"path": "docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/analysis-intake-receipt.json", "sha256": "097186e62428ebccf2de5d89541281b6261661e6ac7b9f856b6a827baa50d5d8"};
const CASE_OUTPUT_BASES={"a1-rear": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3", "a12-forward": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3", "a12-left": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3", "a12-rear": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3", "k12-rear": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3/closure-retry-k12-rear-cold-v1", "k12-right": "fea/generated/v11-zero-spacer-eight-bolt-v1/mechanics/analysis-v3"};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const FAMILIES=['timber_net_shear_torsion','timber_normal_and_stability','cleat_actual_perimeter_rows','direct_elastic_steel','wood_bearing_whole_affine','reduced_connection_axial_bending'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Zero-spacer results: '+message);};
const equalRef=(a,b)=>a&&a.path===b.path&&a.sha256===b.sha256;
const index=value=>Number.isFinite(value)&&value>=0;

export function validateZeroSpacerResults(data){
  require(data.schema==='eoere_v11_zero_spacer_viewer_results/v1'&&data.model===ZERO_SPACER_MODEL&&data.revision==='v11-zero-spacer-eight-bolt-v1','own model required');
  require(data.geometry.sha256==='fe56b38ecd57ce1c2b9e36065d66eced35dccf10424d376919243cb7864c6772'&&
    data.geometry_receipt.path===PREFIX+'geometry-receipt.json'&&data.geometry_receipt.sha256==='b52265bcb0d9ff4cdf8215794a00df7b8f13bca285da9a7db532072c18147882'&&
    data.geometry_provenance.path==='site/eoere-v11-zero-spacer-provenance.json'&&data.geometry_provenance.sha256==='50cace54ac07fd7d07b8e62f7d4650da0f65ab26a5e5697556847472e8d8095a'&&
    data.analysis_geometry.path===ANALYSIS+'geometry/geometry.json'&&data.analysis_geometry.sha256==='720e1c96044af250270c6311eba06b3fce41b7dc70b892ce5845e642308cb137','own frozen geometry/preparation required');
  require(Object.keys(data.sources).length===5&&Object.entries(SOURCES).every(([key,ref])=>equalRef(data.sources[key],ref)),'own bank/completion/contracted/mixed source pins required');
  require(equalRef(data.analysis_intake_receipt,INTAKE)&&data.geometry_receipt.sha256!==INTAKE.sha256&&JSON.stringify(data.case_output_bases)===JSON.stringify(CASE_OUTPUT_BASES),'typed build/intake receipt and explicit case-base joins required');
  const load=data.load_contract;
  require(Object.keys(load).length===5&&load.weight_lb===250&&load.downward_multiplier===2&&load.horizontal_force_N===300&&
    load.accessory_mass_kg===25&&load.duration_factor_CD===1&&data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,'fixed250lb recipe without interpolation required');
  require(data.cases.length===6&&new Set(data.cases.map(row=>row.case_id)).size===6&&data.independent_replays===12,'six own cases and twelve replays required');
  const hashes=[];
  for(const row of data.cases){require(CASES.includes(row.case_id)&&row.both_independent_replays_admitted===true&&index(row.gradient_inf_N)&&row.gradient_inf_N<1e-5,'own admitted case required');
    for(const[key,file]of[['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]){
      require(row[key].path===CASE_OUTPUT_BASES[row.case_id]+'/four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256),'own case/replay join required');hashes.push(row[key].sha256);}}
  require(new Set(hashes).size===18&&data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>row.gradient_inf_N)),'distinct own fields/replays and maximum required');
  require(Object.keys(data.family_references).length===6&&FAMILIES.every(key=>Object.hasOwn(data.family_references,key)),'six separate reference families required');
  for(const row of Object.values(data.family_references))require(index(row.maximum.index)&&CASES.includes(row.maximum.case_id)&&Number.isInteger(row.above_one_count)&&row.above_one_count>=0,'finite conditional family references required');
  const rear=data.rear,p=rear.contracted_common_work_reference,e=rear.separate_original_ellipse_reference,n=rear.separate_continuous_necessary_bound;
  require(rear.axis_count===6&&rear.axis_case_states===36&&rear.receiver_case_certificates===72&&p.states===36&&e.states===36,'own36rear states and72receiver certificates required');
  require(p.source.sha256===SOURCES.contracted_rear_summary.sha256&&p.complete_joint_qualified===false&&p.physical_failure_claim===false&&
    index(p.maximum)&&p.maximum===p.governing.contracted_bearing_index&&Number.isInteger(p.above_one_state_count)&&p.above_one_state_count>=0&&
    Number.isInteger(p.bearing_plus_unchanged_hinge_above_one_state_count)&&p.bearing_plus_unchanged_hinge_above_one_state_count>=0,'separate rear component references required');
  require(index(e.maximum)&&Number.isInteger(e.above_one_count)&&e.above_one_count>=0&&index(n.maximum_lower_bound)&&n.maximum_lower_bound<=e.maximum&&n.receiver_case_rows===72,'ellipse and necessary bound stay separate');
  require(p.governing.lambda>0&&p.governing.lambda<=1&&Math.abs(p.maximum-p.governing.original_ellipse_cell_index/p.governing.lambda)<1e-12,'declared contraction normalization differs');
  for(const count of Object.values(data.connection_diagnostic_counts))require(Number.isInteger(count)&&count>=0,'separate diagnostic counts required');
  const mixed=data.mixed_common_work_reference,s=mixed.summary,b=mixed.basis;
  require(equalRef(mixed.source,SOURCES.mixed_common_work_summary)&&equalRef(mixed.controls,SOURCES.mixed_reference_controls)&&
    equalRef(mixed.response_bank,SOURCES.response_bank),'mixed source and own bank joins required');
  require(b.A574_Fyb_scenario_psi===45000&&b.Grade5_Fyb_scenario_psi===92000&&b.hinge_law==='Mp/4'&&b.bearing_law==='contracted_common_work_projected_bearing','declared mixed scenario basis required');
  require(s.state_count===144&&s.receiver_case_count===432&&Number.isInteger(s.endpoint_count)&&s.endpoint_count>0&&
    s.above_one_count===s.above_one_rows.length&&JSON.stringify(s)===JSON.stringify(EXPECTED_MIXED),'own source-bound mixed inventory and fresh flags required');
  for(const row of s.above_one_rows)require([45000,92000].includes(row.conditional_Fyb_reference_psi)&&index(row.Mp4_hinge_index)&&
    index(row.combined_common_work_Mp4_index)&&row.combined_common_work_Mp4_index>1&&row.combined_common_work_Mp4_index>=row.Mp4_hinge_index&&
    index(row.Mp4_required_Fyb_ksi)&&Math.abs(row.Mp4_hinge_index-row.Mp4_required_Fyb_ksi/(row.conditional_Fyb_reference_psi/1000))<1e-12,'conditional mixed reference differs');
  require(index(s.maximum_Mp4_hinge_index)&&index(s.maximum_contracted_bearing_index)&&
    s.maximum_combined_common_work_Mp4_index===Math.max(s.maximum_Mp4_hinge_index,s.maximum_contracted_bearing_index),'separate mixed maxima required');
  for(const key of['actual_Cg','actual_Cdelta','actual_Fyb','complete_joint_capacity'])require(mixed[key]===null,'mixed actual capacity/factors remain null');
  for(const key of['complete_joint_qualified','physical_failure_claim','structural_acceptance'])require(mixed[key]===false,'mixed reference flags are not physical/joint acceptance');
  require(data.current_response_computed===true&&data.trial_selected===false&&data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&
    data.actual_Fyb_adopted===null&&data.complete_connection_capacity===null,'conditional references do not select or qualify the trial');
  for(const key of FALSE_FLAGS)require(data[key]===false,'qualification/release boundary: '+key);
  return data;
}

export function zeroSpacerResultsStatus(input){
  const data=validateZeroSpacerResults(input),f=data.family_references,rear=data.rear,p=rear.contracted_common_work_reference,mixed=data.mixed_common_work_reference.summary;
  return 'Zero-spacer eight-bolt development · 114 stacks · zero spacers. Six own fixed 250 lb cases and twelve independent replays admitted. '+
    `Conditional member ${f.timber_net_shear_torsion.maximum.index.toFixed(6)}, normal/stability ${f.timber_normal_and_stability.maximum.index.toFixed(6)}, `+
    `cleat ${f.cleat_actual_perimeter_rows.maximum.index.toFixed(6)} and separate elastic steel ${f.direct_elastic_steel.maximum.index.toFixed(6)} references. `+
    `Mixed contracted bearing / Mp/4 reference: ${mixed.above_one_count} conditional flags across 144 states, maximum ${mixed.maximum_combined_common_work_Mp4_index.toFixed(6)}; required Fyb ${mixed.maximum_required_Fyb_ksi.toFixed(6)} ksi. `+
    'Flagged states: '+mixed.above_one_rows.map(row=>`${row.axis_id}/${row.case_id} ${row.combined_common_work_Mp4_index.toFixed(6)}`).join('; ')+'. '+
    `Contracted mixed bearing reference ${mixed.maximum_contracted_bearing_index.toFixed(6)} (${mixed.maximum_contracted_bearing_index<1?"below":"above"} reference threshold). `+
    `Primary contracted common-work rear reference ${p.maximum.toFixed(6)} across 36 states, ${p.above_one_state_count} above one. `+
    `Separate original ellipse reference ${rear.separate_original_ellipse_reference.maximum.toFixed(6)}; continuous necessary lower bound ${rear.separate_continuous_necessary_bound.maximum_lower_bound.toFixed(6)}. `+
    `Separate rear affine Fe/5 diagnostic: ${rear.separate_1d_diagnostic_counts.Fe_over_5_states_above_one} states above one; distinct from the contracted rear reference. `+
    `Legacy local wood-pressure diagnostic: ${f.wood_bearing_whole_affine.above_one_count} rows; group-reduced N/M: ${f.reduced_connection_axial_bending.above_one_count}. `+
    'Actual Fyb, group factors, complete connections, physical fit and tool access remain unqualified. Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. No fabrication or climbing release.';
}

export function applyZeroSpacerResults(scene,input){
  const data=validateZeroSpacerResults(input);
  require(scene.design.key===data.model&&scene.parts.length===1095&&scene.meta.counts.bolt_stacks===114&&scene.meta.counts.spacer_pieces===0&&scene.meta.geometry_only===true&&scene.meta.current_response_computed===false&&
    scene.meta.geometry_sha256===data.geometry.sha256&&scene.meta.layout_sha256===data.geometry_receipt.sha256&&
    scene.meta.provenance_sha256===data.geometry_provenance.sha256,'own raw geometry stage required');
  return {...scene,meta:{...scene.meta,status:zeroSpacerResultsStatus(data),geometry_only:false,analysis_pending:false,current_response_computed:true,
    current_own_response_bank_recorded:true,family_references:data.family_references,rear_references:data.rear,connection_diagnostic_counts:data.connection_diagnostic_counts,
    mixed_common_work_reference:data.mixed_common_work_reference,
    case_rows:data.cases,independent_replays:12,maximum_gradient_inf_N:data.maximum_gradient_inf_N,load_contract:data.load_contract,
    trial_selected:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
    accepted_connection_exceedance_count:null,fixed_load_only:true,weight_interpolation_available:false,planning_mass_kg:null,
    ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),
    portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadZeroSpacerResultsScene(THREE,options,geometryLoader=loadZeroSpacerGeometryScene){
  const response=await fetch(new URL(ZERO_SPACER_RESULTS_ASSET.path.slice(5),import.meta.url));require(response.ok,'own result asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===ZERO_SPACER_RESULTS_ASSET.sha256,'own result asset source pin differs');
  const data=validateZeroSpacerResults(JSON.parse(new TextDecoder().decode(raw)));
  return applyZeroSpacerResults(await geometryLoader(THREE,options),data);
}
