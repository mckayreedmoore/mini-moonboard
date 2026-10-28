import {loadFourBoltOuterTopGeometryScene,FOUR_BOLT_OUTER_TOP_MODEL} from './eoere-v11-four-bolt-outer-top-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const FOUR_BOLT_OUTER_TOP_RESULTS_ASSET=Object.freeze({"path": "site/eoere-v11-four-bolt-outer-top-results.json", "sha256": "3663e14bfea017a0ccdf9769e23491f5914536d86d5679b8bb1bf5bbaa3686c7"});
const PREFIX='docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/';
const ANALYSIS="fea/generated/v11-four-bolt-outer-top-v1/mechanics/analysis-v1/";
const SOURCES={"contracted_rear_summary": {"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/contracted-rear-summary.json", "sha256": "496b13dba58c027f9589b7c15901f03bab4296d743700589a1f6fe4461be5d0c"}, "mixed_common_work_summary": {"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/mixed-common-work-summary.json", "sha256": "48c5772e5a482fcf96f0ff63aed362958ef026547c3544fa500030b78ad7efed"}, "mixed_reference_controls": {"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/mixed-current-controls.json", "sha256": "bc1ea0e899e26e0f08431737f82af773c95b606a9bf642a1dfe7a0bafb342a14"}, "reference_completion": {"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/reference-completion.json", "sha256": "60e8a0e5a9a3bd9cc8c19ab3257ecacc1dbaed74589b5434bcb00a25a84108fc"}, "response_bank": {"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/response-bank.json", "sha256": "41ea66e32d11a816b749170579534a9062085e4a1af4e19e1f98696112df9542"}};
const EXPECTED_MIXED={"above_one_count": 3, "above_one_rows": [{"Mp4_hinge_index": 1.2301854692483343, "Mp4_required_Fyb_ksi": 55.358346116175035, "axis_id": "v11_cleat_left_side_1", "case_id": "a12-forward", "combined_common_work_Mp4_index": 1.2301854692483343, "conditional_Fyb_reference_psi": 45000.0}, {"Mp4_hinge_index": 1.1905336939177829, "Mp4_required_Fyb_ksi": 53.57401622630022, "axis_id": "v11_cleat_left_side_1", "case_id": "a12-left", "combined_common_work_Mp4_index": 1.1905336939177829, "conditional_Fyb_reference_psi": 45000.0}, {"Mp4_hinge_index": 1.1779816622318393, "Mp4_required_Fyb_ksi": 53.00917480043276, "axis_id": "v11_cleat_right_side_1", "case_id": "k12-right", "combined_common_work_Mp4_index": 1.1779816622318393, "conditional_Fyb_reference_psi": 45000.0}], "endpoint_count": 1152, "fresh_Mp5_hinge_above_one_count_preserved": 6, "fresh_Mp5_hinge_maximum_preserved": 1.5377318365604178, "governing_axis_case": ["v11_cleat_left_side_1", "a12-forward"], "maximum_Mp4_hinge_index": 1.2301854692483343, "maximum_combined_common_work_Mp4_index": 1.2301854692483343, "maximum_contracted_bearing_index": 0.45965836128216825, "maximum_required_Fyb_ksi": 55.358346116175035, "receiver_case_count": 432, "state_count": 144};
const PHYSICAL_RECEIPT={"path": "docs/bolted-frame-development/owner-frame-v11/four-bolt-outer-top/geometry-receipt.json", "sha256": "711a3d09cde2d966ad6f97ed7e360569520b4a869ed46b35af4b47931a2266f4"};
const CASE_OUTPUT_BASES={"a1-rear": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/analysis-v2", "a12-forward": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/analysis-v2", "a12-left": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/analysis-v2", "a12-rear": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/precision-polish-v1/a12-rear", "k12-rear": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/precision-polish-v1/k12-rear", "k12-right": "fea/generated/v11-four-bolt-outer-top-v1/mechanics/analysis-v2"};
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const FAMILIES=['timber_net_shear_torsion','timber_normal_and_stability','cleat_actual_perimeter_rows','direct_elastic_steel','wood_bearing_whole_affine','reduced_connection_axial_bending'];
const FALSE_FLAGS=['historical_capacity_transferred','complete_joint_qualified','complete_group_qualified','physical_force_bounds_established',
  'actual_property_adopted','structural_acceptance','purchase_authorized','fabrication_released','climbing_released','physical_changes_authorized','current_alias_promoted'];
const require=(ok,message)=>{if(!ok)throw new Error('Four-bolt outer-top results: '+message);};
const equalRef=(a,b)=>a&&a.path===b.path&&a.sha256===b.sha256;
const index=value=>Number.isFinite(value)&&value>=0;

export function validateFourBoltOuterTopResults(data){
  require(data.schema==='eoere_v11_four_bolt_outer_top_viewer_results/v1'&&data.model===FOUR_BOLT_OUTER_TOP_MODEL&&data.revision==='v11-four-bolt-outer-top-v1','own model required');
  require(data.geometry.sha256==='fa2644301a9050817e1fcb4bd8cd066f92f4446e7d74696b945bcd3900993b0d'&&
    data.geometry_receipt.path===PREFIX+'geometry-receipt.json'&&data.geometry_receipt.sha256==='711a3d09cde2d966ad6f97ed7e360569520b4a869ed46b35af4b47931a2266f4'&&
    data.geometry_provenance.path==='site/eoere-v11-four-bolt-outer-top-provenance.json'&&data.geometry_provenance.sha256==='534d2447f901ababdc63239d6ffd2b7f39a2bc3633f60af1b403037417fd3674'&&
    data.analysis_geometry.path===ANALYSIS+'geometry/geometry.json'&&data.analysis_geometry.sha256==='6c789fb43cafeaf44c2951f77aba7a6943531d78f3feb891a799bf0fa0cc47b1','own frozen geometry/preparation required');
  require(Object.keys(data.sources).length===5&&Object.entries(SOURCES).every(([key,ref])=>equalRef(data.sources[key],ref)),'own bank/completion/contracted/mixed source pins required');
  require(equalRef(data.physical_analysis_receipt,PHYSICAL_RECEIPT)&&data.geometry_receipt.sha256===PHYSICAL_RECEIPT.sha256&&JSON.stringify(data.case_output_bases)===JSON.stringify(CASE_OUTPUT_BASES),'checked physical-analysis receipt and explicit case-base joins required');
  require(JSON.stringify(data.physical_inventory)===JSON.stringify({"fitting_ports": 104, "fitting_poses": 24, "metal_role_rows": 530, "occupied_parts": 1055, "profiles": 30, "receiver_wall_queries": 132, "retained_spacers": 0, "screw_axes": 66, "structural_bolt_axes": 106}),'own prepared physical inventory required');
  require(JSON.stringify(data.cleat_perimeter_scope)===JSON.stringify({"governing_subset_axes": ["cleat_post_bolt_left_2", "eoere_bolt_067", "v11_cleat_left_side_1", "v11_cleat_left_side_2", "v11_cleat_left_post_1", "v11_cleat_left_post_2"], "governing_subset_axis_count": 6, "governing_subset_is_installed_bolt_count": false, "installed_bolts_per_cleat": 8, "subsets_per_component_case_wall": 255, "worksheet": {"path": "fea/generated/v11-four-bolt-outer-top-v1/references/runs/reference-v3/families/cleat_actual_perimeter_rows.json", "sha256": "d356c3919e359740fa9c010a641387ba32b018667b0add3019a7c77d8c3fc69a"}, "worksheet_rows": 6120}),'perimeter subsets differ from installed cleat bolts');
  require(JSON.stringify(data.actualcase_output_bases)===JSON.stringify(CASE_OUTPUT_BASES),'literal actual case output roots required');
  const load=data.load_contract;
  require(Object.keys(load).length===5&&load.weight_lb===250&&load.downward_multiplier===2&&load.horizontal_force_N===300&&
    load.accessory_mass_kg===25&&load.duration_factor_CD===1&&data.fixed_load_only===true&&data.weight_interpolation_available===false&&data.planning_mass_kg===null,'fixed250lb recipe without interpolation required');
  require(data.cases.length===6&&new Set(data.cases.map(row=>row.case_id)).size===6&&data.independent_replays===12,'six own cases and twelve replays required');
  const hashes=[];
  for(const row of data.cases){require(CASES.includes(row.case_id)&&row.both_independent_replays_admitted===true&&index(row.gradient_inf_N)&&row.gradient_inf_N<1e-5&&index(row.result_gradient_inf_N)&&row.result_gradient_inf_N<1e-5,'own admitted case required');
    for(const[key,file]of[['field','field.json'],['result','result.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json'],['execution','v10-execution.json'],['replay_binding','v10-replay-binding.json']]){
      require(row[key].path===CASE_OUTPUT_BASES[row.case_id]+'/four-hosts/'+row.case_id+'/'+file&&/^[a-f0-9]{64}$/.test(row[key].sha256),'own case/replay join required');hashes.push(row[key].sha256);}}
  require(new Set(hashes).size===36&&data.maximum_gradient_inf_N===Math.max(...data.cases.map(row=>Math.max(row.gradient_inf_N,row.result_gradient_inf_N))),'distinct own fields/replays and maximum required');
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
  require(Number.isInteger(s.state_count)&&s.state_count>0&&Number.isInteger(s.receiver_case_count)&&s.receiver_case_count>0&&Number.isInteger(s.endpoint_count)&&s.endpoint_count>0&&
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

export function fourBoltOuterTopResultsStatus(input){
  const data=validateFourBoltOuterTopResults(input),f=data.family_references,rear=data.rear,p=rear.contracted_common_work_reference,mixed=data.mixed_common_work_reference.summary,cleat=data.cleat_perimeter_scope;
  return 'Four-bolt outer-top development · 106 stacks · zero spacers. Six own fixed 250 lb cases and twelve independent replays admitted. Four original cold cases and two same-case precision refreshes; geometry, operator and loads unchanged. '+
    `Conditional member ${f.timber_net_shear_torsion.maximum.index.toFixed(6)}, normal/stability ${f.timber_normal_and_stability.maximum.index.toFixed(6)}, `+
    `cleat perimeter ${f.cleat_actual_perimeter_rows.maximum.index.toFixed(6)} (governing ${cleat.governing_subset_axis_count}-bolt subset; eight installed per cleat) and separate elastic steel ${f.direct_elastic_steel.maximum.index.toFixed(6)} references. `+
    `Mixed contracted bearing / Mp/4 reference: ${mixed.above_one_count} conditional flags across ${mixed.state_count} states, maximum ${mixed.maximum_combined_common_work_Mp4_index.toFixed(6)}; required Fyb ${mixed.maximum_required_Fyb_ksi.toFixed(6)} ksi. `+
    'Flagged states: '+mixed.above_one_rows.map(row=>`${row.axis_id}/${row.case_id} ${row.combined_common_work_Mp4_index.toFixed(6)}`).join('; ')+'. '+
    `Contracted mixed bearing reference ${mixed.maximum_contracted_bearing_index.toFixed(6)} (${mixed.maximum_contracted_bearing_index<1?"below":"above"} reference threshold). `+
    `Primary contracted common-work rear reference ${p.maximum.toFixed(6)} across 36 states, ${p.above_one_state_count} above one. `+
    `Separate original ellipse reference ${rear.separate_original_ellipse_reference.maximum.toFixed(6)}; continuous necessary lower bound ${rear.separate_continuous_necessary_bound.maximum_lower_bound.toFixed(6)}. `+
    `Separate rear affine Fe/5 diagnostic: ${rear.separate_1d_diagnostic_counts.Fe_over_5_states_above_one} states above one; distinct from the contracted rear reference. `+
    `Legacy local wood-pressure diagnostic: ${f.wood_bearing_whole_affine.above_one_count} rows; group-reduced N/M: ${f.reduced_connection_axial_bending.above_one_count}. `+
    'Actual Fyb, group factors, complete connections, physical fit and tool access remain unqualified. Fixed 250 lb × 2 downward, 300 N horizontal, 25 kg accessories, CD = 1; no weight interpolation. No fabrication or climbing release.';
}

export function applyFourBoltOuterTopResults(scene,input){
  const data=validateFourBoltOuterTopResults(input);
  require(scene.design.key===data.model&&scene.parts.length===1055&&scene.meta.counts.bolt_stacks===106&&scene.meta.counts.spacer_pieces===0&&scene.meta.geometry_only===true&&scene.meta.current_response_computed===false&&
    scene.meta.geometry_sha256===data.geometry.sha256&&scene.meta.layout_sha256===data.geometry_receipt.sha256&&
    scene.meta.provenance_sha256===data.geometry_provenance.sha256,'own raw geometry stage required');
  const description='Four bolts at each outer top angle, eight at each plywood cleat and four at each center top angle; zero spacers. Own six-case conditional references recorded; complete connections and actual hardware remain unqualified.';
  const parts=scene.parts.map(part=>({...part,fabrication:{...part.fabrication,description}}));
  return {...scene,parts,meta:{...scene.meta,status:fourBoltOuterTopResultsStatus(data),geometry_only:false,analysis_pending:false,current_response_computed:true,
    current_own_response_bank_recorded:true,family_references:data.family_references,rear_references:data.rear,connection_diagnostic_counts:data.connection_diagnostic_counts,
    mixed_common_work_reference:data.mixed_common_work_reference,
    case_rows:data.cases,physical_inventory:data.physical_inventory,cleat_perimeter_scope:data.cleat_perimeter_scope,case_output_bases:data.case_output_bases,numerical_execution_provenance:data.numerical_execution_provenance,independent_replays:12,maximum_gradient_inf_N:data.maximum_gradient_inf_N,load_contract:data.load_contract,
    trial_selected:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,actual_Fyb_adopted:null,complete_connection_capacity:null,
    accepted_connection_exceedance_count:null,fixed_load_only:true,weight_interpolation_available:false,planning_mass_kg:null,
    ...Object.fromEntries(FALSE_FLAGS.map(key=>[key,false])),
    portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadFourBoltOuterTopResultsScene(THREE,options,geometryLoader=loadFourBoltOuterTopGeometryScene){
  const response=await fetch(new URL(FOUR_BOLT_OUTER_TOP_RESULTS_ASSET.path.slice(5),import.meta.url));require(response.ok,'own result asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===FOUR_BOLT_OUTER_TOP_RESULTS_ASSET.sha256,'own result asset source pin differs');
  const data=validateFourBoltOuterTopResults(JSON.parse(new TextDecoder().decode(raw)));
  return applyFourBoltOuterTopResults(await geometryLoader(THREE,options),data);
}
