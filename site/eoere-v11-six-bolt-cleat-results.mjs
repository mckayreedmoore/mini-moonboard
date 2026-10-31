import {sha256} from './wood-joints-overlay.mjs';
import {loadSixBoltCleatGeometryScene,SIX_BOLT_CLEAT_MODEL,SIX_BOLT_CLEAT_ASSETS} from './eoere-v11-six-bolt-cleat-overlay.mjs';

const REVISION='v11-six-bolt-cleat-v1';
const ROOT='fea/generated/v11-six-bolt-cleat-v1/';
const ANALYSIS_PREFIX=ROOT+'mechanics/analysis-v1/';
const ADMISSION_PATH=ROOT+'mechanics/parent-bank-admission-v1.json';
const SUMMARY_PATH=ROOT+'references/current-reference-summary-v1.json';
const COMPONENT_SUMMARY_PATH=ROOT+'references/components/component-reference-summary-v1.json';
const GEOMETRY_PATH=ROOT+'geometry-v1/geometry.json';
const CHECKED_RECEIPT_PATH=ROOT+'geometry-v1/checked-receipt-v1.json';
const METADATA_RECEIPT_PATH=ROOT+'geometry-v1/geometry-receipt.json';
const CLEARANCE_PATH=ROOT+'geometry-v1/clearance.json';
const MECHANICS_READINESS_PATH=ANALYSIS_PREFIX+'adapter-readiness.json';
const OWNER_AUTHORIZATION={path:'docs/bolted-frame-development/owner-frame-v11/owner-six-bolt-cleat-evaluation.json',
  sha256:'298e2d0f09a2f5accc9b9067b3936afab952c3b6119644458560a9ad792909ae'};
const GEOMETRY={path:GEOMETRY_PATH,sha256:'f8e4a4eeac74c5357bc0d50d5085e4ccb9f09022dbf3b194f1ebc8e38221baa3'};
const CHECKED_RECEIPT={path:CHECKED_RECEIPT_PATH,sha256:'2e6f81accf530c3d42eb1f8833be7bc183d374fab32f30667995025f5079a100'};
const METADATA_RECEIPT={path:METADATA_RECEIPT_PATH,sha256:'c60aca45dcc8b1bd9a9594adfbf0a8a0a37fae34f3e7d4d29dc534df500d815b'};
const CLEARANCE={path:CLEARANCE_PATH,sha256:'58280e46c0e740fb615b294440d7d0e88e0b6a00a7cc3ae8a1226baf5e5aafa5'};
const MECHANICS_READINESS={path:MECHANICS_READINESS_PATH,sha256:'4db66871fa62eef934b1443b0537313898f5eba8c69a7555164953762ce09f69'};
const PUBLIC_BASE='docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/';
const PUBLIC_BANK_PATH=PUBLIC_BASE+'response-bank.json';
const PUBLIC_ADMISSION_PATH=PUBLIC_BASE+'parent-bank-admission.json';
const PUBLIC_SUMMARY_PATH=PUBLIC_BASE+'current-reference-summary.json';
const PUBLIC_COMPONENT_SUMMARY_PATH=PUBLIC_BASE+'component-reference-summary.json';
const CASES=['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const OMIT=['left','right'].flatMap(side=>[1,2].map(index=>`v11_cleat_${side}_post_${index}`));
const INVENTORY={structural_bolt_axes:102,metal_role_rows:510,occupied_parts:1035,profiles:30,
  fitting_poses:24,screw_axes:66,retained_spacers:0};
const COMPONENT_COUNTS={axes:102,ends:204,washer_end_case_rows:1224,bond_leaf_wrench_states:12,
  angle_baseline_body_case_states:144,header_variant_body_case_states:48,header_event_aliases:96,
  baseline_fine_states:1,header_fine_states:1};
const COMPONENT_ROUTES={
  washer_ends:['demand','geometry_reuse','validation'],near_plate:['corrected_plate'],
  bond_leaves:['six_resultant_demand','static_witness'],
  angle_baseline:['fitting_demand','followthrough','map_readiness','source_coverage_check','observation','execution'],
  angle_header:['bridge','bridge_gate','fitting_demand','map_readiness','source_coverage_check','observation','execution'],
  backing_domain_audit:['audit','integral_quadrature_audit'],
  baseline_fine:['readiness','observation','execution'],header_fine:['readiness','observation','execution'],
};
const NATIVE_JOBS=['coarse_manifest','complete_manifest','baseline_coarse_execution','header_coarse_execution',
  'baseline_fine_execution','header_fine_execution'];
const ACTUAL_PROPERTY_KEYS=['adhesive_G_MPa','bondline_thickness_mm','Ft90_MPa','Gc_N_per_mm','peel_allowable_MPa',
  'shear_allowable_MPa','torsion_allowable_Nmm','fitting_Fy_MPa','fitting_Fu_MPa','wood_bending_MPa',
  'wood_tension_parallel_MPa','wood_tension_perpendicular_MPa','wood_shear_MPa','washer_strength_MPa',
  'preload_N','friction_coefficient','contact_compliance','glue_coverage_conformity'];
const WASHER_METRICS=['maximum_sawn_mean_index','maximum_plywood_dry_mean_index','maximum_plywood_02in_mean_index',
  'maximum_minimum_thickness_required_Fy_1_67_MPa','maximum_CAD_thickness_required_Fy_1_67_MPa',
  'maximum_near_subset_continuous_dimension_box_required_Fy_1_67_MPa',
  'maximum_minimum_thickness_plate_static_required_Fy_1_67_MPa',
  'maximum_CAD_thickness_plate_static_required_Fy_1_67_MPa','maximum_continuous_dimension_box_required_Fy_1_67_MPa',
  'maximum_saved_shaft_axial_balance_residual_N','maximum_source_force_replay_error_N',
  'maximum_source_global_moment_transport_error_Nmm'];
const BOND_METRICS=['cleat_case_states','max_six_resultant_replay_error_N_Nmm','maximum_long_wavelength_q_N_per_mm',
  'maximum_long_wavelength_width_average_shear_MPa','maximum_reduced_normal_compression_cap_MPa',
  'maximum_reduced_tangential_traction_MPa'];
const BASELINE_METRICS=['states','maximum_IP_VM_MPa','required_Fy_1_67_MPa','conditional_Fy235_marker_index',
  'maximum_gauge_plus_applied_force_residual_N','maximum_gauge_plus_applied_moment_residual_Nmm'];
const HEADER_METRICS=['states','event_aliases','maximum_IP_VM_MPa','required_Fy_1_67_MPa',
  'conditional_Fy235_marker_index','maximum_gauge_plus_applied_force_residual_N',
  'maximum_gauge_plus_applied_moment_residual_Nmm'];
const DOMAIN_METRICS=['fittings','actual_domains','exact_cached_domains','newly_integrated_domains',
  'maximum_actual_area_error_mm2','maximum_actual_first_moment_error_mm3','maximum_actual_centroid_error_mm',
  'unchanged_area_gate_mm2','unchanged_first_moment_gate_mm3','unchanged_centroid_gate_mm'];
const DOMAIN_POST_FLAGS=['near_timber_10_31875_mm_bore_absent','unused_near_steel_factory_hole_at_23_8125_mm',
  'retained_far_timber_bore_at_65_0875_mm','factory_steel_hole_10_mm_retained'];
const FALSE_OPTIONAL=['historical_field_or_force_transfer','historical_capacity_transferred','complete_joint_qualified',
  'complete_group_qualified','physical_force_bounds_established','actual_property_adopted','candidate_selected',
  'structural_acceptance','purchase_authorized','drilling_released','fabrication_released','climbing_released',
  'physical_changes_authorized','physical_release','complete_physical_fitting_capacity',
  'physical_contact_prying_or_complete_joint_qualified'];
const BANK_REQUIRED_FALSE=['historical_field_or_force_transfer','complete_joint_qualified','candidate_selected',
  'structural_acceptance','fabrication_released','climbing_released'];
const SUMMARY_REQUIRED_FALSE=['candidate_selected','structural_acceptance','complete_joint_qualified','purchase_authorized',
  'drilling_released','fabrication_released','climbing_released','physical_release'];
const RESULT_REQUIRED_FALSE=['historical_field_or_force_transfer','historical_capacity_transferred','complete_joint_qualified',
  'complete_group_qualified','physical_force_bounds_established','actual_property_adopted','actual_property_qualification',
  'candidate_selected','structural_acceptance','purchase_authorized','drilling_released','fabrication_released',
  'climbing_released','physical_changes_authorized','physical_release'];
const LOAD={weight_lb:250,downward_multiplier:2,horizontal_force_N:300,accessory_mass_kg:25,duration_factor_CD:1};
const require=(ok,message)=>{if(!ok)throw new Error('Six-bolt cleat results: '+message);};
const sameRef=(a,b)=>Boolean(a&&b&&a.path===b.path&&a.sha256===b.sha256);
const isRef=value=>Boolean(value&&typeof value.path==='string'&&/^[a-f0-9]{64}$/.test(value.sha256));
const sameSet=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&[...a].sort().every((value,index)=>value===[...b].sort()[index]);
const sameObject=(a,b)=>stable(a)===stable(b);
const stable=value=>value===null||typeof value!=='object'?JSON.stringify(value):Array.isArray(value)?`[${value.map(stable).join(',')}]`:
  `{${Object.keys(value).sort().map(key=>`${JSON.stringify(key)}:${stable(value[key])}`).join(',')}}`;
function collectRefs(value,out=[]){
  if(isRef(value)){out.push(value);return out;}
  if(value&&typeof value==='object')for(const child of Object.values(value))collectRefs(child,out);
  return out;
}
const sameLoad=load=>load&&Object.keys(load).length===Object.keys(LOAD).length&&
  Object.entries(LOAD).every(([key,value])=>load[key]===value);

// These two null bindings are the deliberate geometry-only boundary. The
// parent may fill them only after both independent summaries are finalized.
export const SIX_BOLT_CLEAT_RESULTS_ASSET=Object.freeze({"path": "site/eoere-v11-six-bolt-cleat-results.json", "sha256": "9dbf5b50c86cad68ed032526f60a959ed55a879d1c745c136b9b9d3eb58b9510"});
export const SIX_BOLT_CLEAT_RESULTS_SOURCES=Object.freeze({"checked_geometry_receipt": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/checked-receipt-v1.json", "sha256": "2e6f81accf530c3d42eb1f8833be7bc183d374fab32f30667995025f5079a100"}, "clearance": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/clearance.json", "sha256": "58280e46c0e740fb615b294440d7d0e88e0b6a00a7cc3ae8a1226baf5e5aafa5"}, "component_reference_summary": {"path": "fea/generated/v11-six-bolt-cleat-v1/references/components/component-reference-summary-v1.json", "sha256": "b1c7a406c5eab5f64e732fda1198bb31a78d23e5e46aedf6012bd3d0d6636bca"}, "component_reference_summary_public": {"path": "docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/component-reference-summary.json", "sha256": "b1c7a406c5eab5f64e732fda1198bb31a78d23e5e46aedf6012bd3d0d6636bca"}, "current_reference_summary": {"path": "fea/generated/v11-six-bolt-cleat-v1/references/current-reference-summary-v1.json", "sha256": "cd961d2de881e1a66ab9cee6cb7f7b33dc3b8d50a274904033c3e1aff7af1d9b"}, "current_reference_summary_public": {"path": "docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/current-reference-summary.json", "sha256": "cd961d2de881e1a66ab9cee6cb7f7b33dc3b8d50a274904033c3e1aff7af1d9b"}, "geometry": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/geometry.json", "sha256": "f8e4a4eeac74c5357bc0d50d5085e4ccb9f09022dbf3b194f1ebc8e38221baa3"}, "geometry_metadata_receipt": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/geometry-receipt.json", "sha256": "c60aca45dcc8b1bd9a9594adfbf0a8a0a37fae34f3e7d4d29dc534df500d815b"}, "geometry_provenance": {"path": "site/eoere-v11-six-bolt-cleat-provenance.json", "sha256": "a80ae8505d1e763c38d4ffe97666ab6c2eee3bbe1a0676fa5056188493a8cfe5"}, "geometry_receipt": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/checked-receipt-v1.json", "sha256": "2e6f81accf530c3d42eb1f8833be7bc183d374fab32f30667995025f5079a100"}, "geometry_receipt_public": {"path": "docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/geometry-receipt.json", "sha256": "2e6f81accf530c3d42eb1f8833be7bc183d374fab32f30667995025f5079a100"}, "mechanics_readiness": {"path": "fea/generated/v11-six-bolt-cleat-v1/mechanics/analysis-v1/adapter-readiness.json", "sha256": "4db66871fa62eef934b1443b0537313898f5eba8c69a7555164953762ce09f69"}, "owner_authorization": {"path": "docs/bolted-frame-development/owner-frame-v11/owner-six-bolt-cleat-evaluation.json", "sha256": "298e2d0f09a2f5accc9b9067b3936afab952c3b6119644458560a9ad792909ae"}, "parent_bank_admission": {"path": "fea/generated/v11-six-bolt-cleat-v1/mechanics/parent-bank-admission-v1.json", "sha256": "0d8340c6bec153510da35452925e5b0c8d1dcd85b198aa31ddc82ba25e8f0932"}, "parent_bank_admission_public": {"path": "docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/parent-bank-admission.json", "sha256": "0d8340c6bec153510da35452925e5b0c8d1dcd85b198aa31ddc82ba25e8f0932"}, "parent_runtime_proof": {"path": "fea/generated/v11-six-bolt-cleat-v1/parent-validation/component-parent-runtime-proof-v1.json", "sha256": "8277b52174dbb7f9effa74b230671613b2783eda22b500e8f70b361ffca223e0"}, "physical_receipt": {"path": "fea/generated/v11-six-bolt-cleat-v1/geometry-v1/checked-receipt-v1.json", "sha256": "2e6f81accf530c3d42eb1f8833be7bc183d374fab32f30667995025f5079a100"}, "response_bank": {"path": "fea/generated/v11-six-bolt-cleat-v1/mechanics/analysis-v1/response-bank.json", "sha256": "4134b376f92c92a84b7c55316f10a84d4daedff51285f0725b9cdd87a4c04626"}, "response_bank_public": {"path": "docs/bolted-frame-development/owner-frame-v11/six-bolt-cleat/response-bank.json", "sha256": "4134b376f92c92a84b7c55316f10a84d4daedff51285f0725b9cdd87a4c04626"}});

function checkFalseFlags(value,required,message){
  for(const key of required)require(value?.[key]===false,message+': '+key);
  for(const key of FALSE_OPTIONAL)if(key in (value??{}))require(value[key]===false,message+': '+key);
}

function candidateIdentity(expected){
  require(expected?.revision===REVISION&&sameRef(expected.geometry,GEOMETRY)&&
    sameRef(expected.geometry_receipt,CHECKED_RECEIPT)&&sameRef(expected.physical_receipt,CHECKED_RECEIPT)&&
    sameRef(expected.geometry_metadata_receipt,METADATA_RECEIPT)&&sameRef(expected.geometry_provenance,
      {path:SIX_BOLT_CLEAT_ASSETS.path,sha256:SIX_BOLT_CLEAT_ASSETS.sha256})&&
    sameRef(expected.geometry_receipt_public,{path:PUBLIC_BASE+'geometry-receipt.json',sha256:CHECKED_RECEIPT.sha256})&&
    sameRef(expected.owner_authorization,OWNER_AUTHORIZATION)&&sameRef(expected.clearance,CLEARANCE)&&
    sameRef(expected.mechanics_readiness,MECHANICS_READINESS)&&
    sameRef(expected.response_bank,{path:ANALYSIS_PREFIX+'response-bank.json',sha256:'4134b376f92c92a84b7c55316f10a84d4daedff51285f0725b9cdd87a4c04626'})&&
    sameRef(expected.parent_bank_admission,{path:ADMISSION_PATH,sha256:'0d8340c6bec153510da35452925e5b0c8d1dcd85b198aa31ddc82ba25e8f0932'})&&
    expected.current_reference_summary?.path===SUMMARY_PATH&&/^[a-f0-9]{64}$/.test(expected.current_reference_summary.sha256)&&
    expected.component_reference_summary?.path===COMPONENT_SUMMARY_PATH&&/^[a-f0-9]{64}$/.test(expected.component_reference_summary.sha256)&&
    isRef(expected.parent_runtime_proof)&&expected.parent_runtime_proof.path.startsWith(ROOT)&&
    sameRef(expected.response_bank_public,{path:PUBLIC_BANK_PATH,sha256:expected.response_bank.sha256})&&
    sameRef(expected.parent_bank_admission_public,{path:PUBLIC_ADMISSION_PATH,sha256:expected.parent_bank_admission.sha256})&&
    sameRef(expected.current_reference_summary_public,{path:PUBLIC_SUMMARY_PATH,sha256:expected.current_reference_summary.sha256})&&
    sameRef(expected.component_reference_summary_public,{path:PUBLIC_COMPONENT_SUMMARY_PATH,sha256:expected.component_reference_summary.sha256}),
    'current geometry, checked receipts, owner source, readiness, own bank/admission, both public summaries, and the current parent runtime proof are required');
  require(Array.isArray(expected.axis_ids)&&expected.axis_ids.length===102&&new Set(expected.axis_ids).size===102&&
    !OMIT.some(axis=>expected.axis_ids.includes(axis)),'current 102-axis geometry roster must exclude all four omitted axes');
  return expected;
}

function requireCandidateInventory(inventory,message){
  require(inventory&&Object.entries(INVENTORY).every(([key,value])=>inventory[key]===value),message);
}

export function validateSixBoltCleatResponseBank(bank,expected){
  candidateIdentity(expected);
  require(bank&&bank.schema==='eoere_v11_six_bolt_cleat_response_bank/v1'&&bank.candidate_revision===REVISION,
    'candidate-owned response bank required; stale 106-axis banks cannot be reused');
  require(sameRef(bank.physical_geometry,expected.geometry)&&sameRef(bank.physical_receipt,expected.physical_receipt),
    'response bank must match current six-bolt geometry and checked receipt');
  requireCandidateInventory(bank.physical_inventory,'response-bank physical inventory differs from the candidate');
  require(Array.isArray(bank.case_ids)&&sameSet(bank.case_ids,CASES)&&Array.isArray(bank.cases)&&bank.cases.length===6&&
    sameSet(bank.cases.map(row=>row.case_id),CASES)&&bank.cases.every(row=>row.both_independent_replays_admitted===true),
    'all six candidate cases with two admitted independent replays each are required');
  require(bank.all_six_cases_admitted===true&&bank.two_independent_replays_per_case===true&&bank.fresh_fields_only===true&&
    bank.historical_field_or_force_transfer===false,'fresh admitted fields and replays required; parent forces cannot transfer');
  if(bank.axis_ids)require(sameSet(bank.axis_ids,expected.axis_ids),'response-bank axis roster differs');
  if(bank.omitted_axis_ids)require(sameSet(bank.omitted_axis_ids,OMIT),'response-bank omitted-axis record differs');
  for(const row of bank.cases)if(row.axis_ids)
    require(sameSet(row.axis_ids,expected.axis_ids),'case includes a noncandidate or omitted axis: '+row.case_id);
  require(sameLoad(bank.load_contract),'fixed owner load contract must remain unchanged');
  checkFalseFlags(bank,BANK_REQUIRED_FALSE,'response-bank release/transfer boundary');
  return bank;
}

export function validateSixBoltCleatParentBankAdmission(admission,expected){
  candidateIdentity(expected);
  require(admission?.schema==='six_bolt_cleat_parent_bank_admission/v1'&&sameRef(admission.bank,expected.response_bank),
    'parent admission must identify the exact current six-bolt response bank');
  require(admission.source_failures===0&&admission.case_count===6&&admission.independent_replay_count===12&&
    admission.all_frozen_case_recovery_and_replay_gates_rechecked===true&&
    Number.isInteger(admission.unique_current_source_pins_verified)&&admission.unique_current_source_pins_verified>0,
    'six-case/twelve-replay parent-bank admission with zero source failures is required');
  checkFalseFlags(admission,['historical_field_or_force_transfer','candidate_selected','complete_joint_qualified',
    'structural_acceptance','fabrication_released','climbing_released'],'parent-admission release/transfer boundary');
  return admission;
}

export function validateSixBoltCleatCurrentReferenceSummary(summary,expected){
  candidateIdentity(expected);
  require(summary?.schema==='v11_six_bolt_cleat_current_reference_summary/v1'&&summary.revision===REVISION,
    'current candidate-specific reference summary required');
  require(sameRef(summary.geometry,expected.geometry)&&sameRef(summary.response_bank,expected.response_bank)&&
    sameRef(summary.geometry_receipt,expected.physical_receipt),'reference summary must bind own geometry, bank and checked receipt');
  const bindings=summary.source_bindings;
  require(sameRef(bindings?.bank,expected.response_bank)&&sameRef(bindings?.geometry,expected.geometry)&&
    sameRef(bindings?.receipt,expected.physical_receipt)&&sameRef(bindings?.parent_bank_admission,expected.parent_bank_admission),
    'reference-summary source bindings must join the exact own bank, admission, geometry and checked receipt');
  requireCandidateInventory(summary.physical_inventory,'reference-summary inventory differs from the physical candidate');
  require(Array.isArray(summary.axis_ids)&&sameSet(summary.axis_ids,expected.axis_ids)&&
    Array.isArray(summary.omitted_axis_ids)&&sameSet(summary.omitted_axis_ids,OMIT),
    'reference summary must preserve the exact 102 current and four omitted axes');
  require(Array.isArray(summary.case_ids)&&sameSet(summary.case_ids,CASES)&&summary.independent_replays===12&&
    summary.all_six_cases_admitted===true&&summary.two_independent_replays_per_case===true,
    'current reference summary must cover six admitted cases and twelve independent replays');
  require(sameLoad(summary.load_contract)&&summary.scope?.shaft_case_closures===612,
    'reference summary fixed load and current shaft closure census differ');
  require(isRef(summary.reference_outputs),'candidate-specific reference outputs must be source-bound');
  for(const key of['actual_Cg','actual_Cdelta','actual_Fy','actual_Fyb','complete_joint_capacity'])
    require(summary[key]===null,'conditional references cannot adopt '+key);
  require(summary.actual_property_qualification===null,
    'conditional reference package must leave actual-property qualification unset');
  const projection=summary.conditional_reference_results;
  const projectionGroups=['families','mixed','front','rear','signed_end_edge','optional_diagnostics','method_gaps'];
  require(projection&&typeof projection==='object'&&projection.source_bindings&&
    projectionGroups.every(key=>projection[key]&&typeof projection[key]==='object'),
    'compact current conditional-reference metrics, scope groups and exact source refs are required');
  const projectionRefs=collectRefs(projection.source_bindings);
  require(projectionRefs.length>0,'current conditional-reference metric sources must be source-pinned');
  validateConditionalReferenceProjection(projection);
  checkFalseFlags(summary,SUMMARY_REQUIRED_FALSE,'current-reference-summary release boundary');
  return summary;
}

function requireRawCandidateRef(ref,message){
  require(isRef(ref)&&ref.path.startsWith(ROOT)&&!ref.path.includes('v11-external-hex-heads'),message);
}

function requireMetric(value,message){require(typeof value==='number'&&Number.isFinite(value)&&value>=0,message);}
function validateConditionalReferenceProjection(projection){
  const familyNames=['wood_bearing_whole_affine','reduced_connection_axial_bending','direct_elastic_steel',
    'timber_net_shear_torsion','timber_normal_and_stability','cleat_actual_perimeter_rows'];
  const families=projection.families?.methods;
  require(families&&familyNames.every(name=>{
    const family=families[name];
    return Number.isInteger(family?.row_count)&&family.row_count>0&&
      Number.isInteger(family.above_one_count)&&family.above_one_count>=0&&
      typeof family.maximum?.index==='number'&&Number.isFinite(family.maximum.index)&&isRef(family.source);
  }), 'fresh family references must include current source-pinned maxima and row counts');
  require(families.timber_net_shear_torsion.row_count===120&&families.timber_normal_and_stability.row_count===240&&
    families.cleat_actual_perimeter_rows.row_count===1512&&families.direct_elastic_steel.row_count===612,
    'fresh timber, cleat, and direct-steel family row counts differ from the current scope');
  const inherited=projection.families.inherited_factor_diagnostics;
  for(const name of['wood_bearing_whole_affine','reduced_connection_axial_bending'])
    require(inherited?.[name]?.row_count===612&&inherited[name].above_one_count===13&&
      inherited[name].actual_Cg===null&&inherited[name].adopted_as_complete_joint_criterion===false&&
      isRef(inherited[name].source), 'inherited-factor diagnostics must remain explicit, source-bound, and unadopted');
  const mixed=projection.mixed;
  require(mixed?.active_mixed_axes===20&&mixed.axis_case_states===120&&mixed.plane_case_rows===240&&
    mixed.common_work_rows===120&&typeof mixed.maximum_plane_reference?.plane_force_over_Z_conditional_reference==='number'&&
    typeof mixed.maximum_common_work_index==='number'&&isRef(mixed.source_bindings?.plane_references)&&
    isRef(mixed.source_bindings?.common_work_rows),
    'fresh mixed-material maxima must cover the 20-axis current census');
  for(const [name,axes,states,receivers] of[['front',4,24,48],['rear',6,36,72]]){
    const route=projection[name];
    const projected=route?.projected_witness?.maximum_projected_reference_index_case;
    require(route?.axis_count===axes&&route.axis_case_count===states&&route.receiver_case_count===receivers&&
      route.full_wrench_conditional_reference?.state_count===states&&
      typeof route.full_wrench_conditional_reference?.maximum_Fe_over_5_utilization==='number'&&
      Number.isInteger(route.full_wrench_conditional_reference.Fe_over_5_states_above_one)&&
      Array.isArray(projected)&&projected.length===3&&typeof projected[2]==='number'&&
      route.projected_witness.state_count===states&&
      Number.isInteger(route.projected_witness.reference_index_above_one_count)&&
      route.contracted_full_action?.states===states&&
      typeof route.contracted_full_action.maximum_contracted_bearing_index==='number'&&
      Number.isFinite(route.contracted_full_action.maximum_contracted_bearing_index)&&
      isRef(route.contracted_full_action.source)&&
      isRef(route.source)&&isRef(route.contracted_full_action.source),
      'fresh full-action reference maxima or census differ: '+name);
  }
  const signed=projection.signed_end_edge,planar=signed?.signed_planar_rear_foot,
    supplemental=signed?.supplemental_signed_end_markers,marker=signed?.full_7d_end_marker;
  require(planar?.case_rows===12&&planar.resolved_case_count===12&&planar.unresolved_case_count===0&&
    planar.above_one_count===0&&planar.current_planar_foot_reference_exceedances===0&&
    planar.current_planar_foot_unresolved===0&&typeof planar.maximum_conditional_planar_component_index==='number'&&
    isRef(signed.source)&&supplemental?.cleat_post_net_rows===0&&supplemental.cleat_post_net_above_reference_count===0&&
    supplemental.maximum_net_available_to_full_reference_ratio===null&&supplemental.cleat_post_primitive_rows===0&&
    supplemental.cleat_post_primitive_above_reference_count===0&&
    supplemental.maximum_primitive_available_to_full_reference_ratio===null&&
    typeof marker?.principal_end_only_Cdelta_ratio==='number'&&typeof marker.shortfall_mm==='number'&&
    signed.full_7d_marker_is_adopted_or_physical_failure===false,
    'current signed rear-foot selector, zero cleat-post flag arrays, and non-adopted full-7D marker must be explicit');
  const optionalFoot=signed.optional_both_edge_foot_diagnostic,
    optionalValues=optionalFoot?.marker_rows;
  require(optionalFoot?.case_rows_with_marker===12&&Array.isArray(optionalValues)&&optionalValues.length===12&&
    optionalFoot.adopted===false&&optionalValues.every(value=>typeof value==='number'&&Number.isFinite(value))&&
    optionalValues.filter(value=>value>1).length===2&&
    Math.abs(Math.max(...optionalValues)-1.089124390972596)<1e-9,
    'retained optional two-edge foot envelope and its two conditional flags must remain distinct from the signed selector');
  const brittle=projection.brittle_paths?.component_reference_summaries;
  require(brittle&&sameSet(Object.keys(brittle),['member_cuts','interrupted_paths','connected_paths','reduced_depth'])&&
    Object.values(brittle).every(row=>row?.complete_joint_criterion===false&&row.summary&&isRef(row.source)),
    'current member-cut, interrupted-path, connected-path, and reduced-depth summaries must remain source-bound');
  const cuts=brittle.member_cuts.summary,interrupted=brittle.interrupted_paths.summary,
    connected=brittle.connected_paths.summary,reduced=brittle.reduced_depth.summary;
  require(cuts?.counts?.E2===336&&cuts.counts.E3===420&&cuts.counts.E4===192&&
    cuts.counts.unresolved_case_rows===204&&cuts.flags?.E2===0&&cuts.flags.E3===0&&cuts.flags.E4===0&&
    interrupted?.directional_case_rows===480&&interrupted.valid_directional_reference_rows===264&&
    interrupted.blocked_positive_net_force_rows===92&&interrupted.measured_interrupted_paths===36&&
    connected?.case_direction_rows===216&&connected.above_one_count===0&&
    typeof connected.maximum_conditional_extension_index==='number'&&
    reduced?.case_rows===336&&reduced.edge_scenario_rows===672&&reduced.above_one_rows===2&&
    Math.abs(reduced.maximum_conditional_index-1.089124390972596)<1e-9,
    'current brittle-path route counts and conditional flags differ from their source summaries');
  const individual=projection.optional_diagnostics?.individual_EYM_Cg_equation_bound;
  require(individual?.row_count===220&&individual.criterion_adopted===false&&isRef(individual.source)&&
    projection.optional_diagnostics.legacy_signature_pressure_and_nm?.current_fresh_result===null&&
    projection.optional_diagnostics.legacy_signature_pressure_and_nm?.historical_parent_106_values_transferred===false,
    'optional EYM and legacy pressure/NM diagnostic dispositions must remain distinct and source-bound');
}
function validateSixBoltCleatCompactMetrics(metrics){
  require(metrics?.schema==='v11_six_bolt_cleat_component_metric_projection/v1',
    'current component compact-metric projection schema required');
  const expectedCounts={axes:102,ends:204,washer_end_case_rows:1224,bond_leaf_wrench_states:12,
    baseline_body_case_states:144,header_variant_body_case_states:48,header_event_aliases:96,
    baseline_fine_states:1,header_fine_states:1};
  require(metrics.counts&&sameSet(Object.keys(metrics.counts),[...Object.keys(expectedCounts),'actual_backing_domains'])&&
    Object.entries(expectedCounts).every(([key,value])=>metrics.counts[key]===value)&&
    Number.isInteger(metrics.counts.actual_backing_domains)&&metrics.counts.actual_backing_domains>0,
    'component projection counts must match the current cases, routes and readiness-derived backing domains');
  for(const key of WASHER_METRICS)requireMetric(metrics.washer?.[key],'current washer metric is missing or invalid: '+key);
  require(metrics.bond?.cleat_case_states===12&&
    typeof metrics.bond.all_12_reduced_wrenches_compression_only_representable==='boolean',
    'the twelve current bond-leaf wrench states and static compression-witness disposition are required');
  for(const key of BOND_METRICS)requireMetric(metrics.bond?.[key],'current bond demand metric is missing or invalid: '+key);
  for(const [route,stateCount,fields] of[
    ['angle_baseline',144,BASELINE_METRICS],['angle_header',48,HEADER_METRICS],
  ]){
    const values=metrics[route];require(values&&values.states===stateCount,
      'current component state count differs: '+route);
    for(const key of fields)if(key!=='states'&&key!=='event_aliases')
      requireMetric(values[key],'current fitting-map metric is missing or invalid: '+route+'.'+key);
    require(typeof values.governing_fitting==='string'&&typeof values.governing_case==='string',
      'the current coarse fitting governor is required: '+route);
  }
  const bridgeGate=metrics.angle_header.bridge_gate;
  require(metrics.angle_header.event_aliases===96&&bridgeGate&&
    bridgeGate.all_gates_passed===true&&bridgeGate.fresh_case_event_rows===12&&
    bridgeGate.raw_high_minus_low_moment_gate_Nmm===1e-4&&
    bridgeGate.maximum_abs_raw_high_minus_low_moment_Nmm<=bridgeGate.raw_high_minus_low_moment_gate_Nmm&&
    bridgeGate.raw_high_minus_low_moment_gate_passed===true&&
    bridgeGate.original_member_cut_gate?.gate_Nmm===0.1&&
    bridgeGate.original_member_cut_gate?.passed===true&&
    bridgeGate.original_member_cut_gate?.per_member_raw_cut_closure_passed&&
    Object.values(bridgeGate.original_member_cut_gate.per_member_raw_cut_closure_passed).length===5&&
    Object.values(bridgeGate.original_member_cut_gate.per_member_raw_cut_closure_passed).every(value=>value===true),
    'the 96-event header map and passing additive bridge gate are required');
  for(const route of['baseline','header']){
    const fine=metrics.fine?.[route];
    require(fine&&typeof fine.case_id==='string'&&typeof fine.fitting_id==='string',
      'selected current fine-map governor is required: '+route);
    for(const key of['fine_VM_MPa','fine_required_Fy_1_67_MPa','fine_Fy235_marker_index'])
      requireMetric(fine[key],'selected current fine-map metric is missing or invalid: '+route+'.'+key);
    require(typeof fine.relative_VM_change==='number'&&Number.isFinite(fine.relative_VM_change),
      'coarse-to-fine relative change is missing or invalid: '+route);
  }
  const domain=metrics.domain;
  require(domain&&DOMAIN_METRICS.every(key=>Number.isFinite(domain[key])&&domain[key]>=0)&&
    domain.fittings===24&&domain.actual_domains===metrics.counts.actual_backing_domains&&
    domain.exact_cached_domains+domain.newly_integrated_domains===domain.actual_domains,
    'compact domain metrics must reconcile to the actual current readiness census');
  for(const [error,gate] of[['maximum_actual_area_error_mm2','unchanged_area_gate_mm2'],
    ['maximum_actual_first_moment_error_mm3','unchanged_first_moment_gate_mm3'],
    ['maximum_actual_centroid_error_mm','unchanged_centroid_gate_mm']])
    require(domain[error]<=domain[gate],`current exact-domain metric exceeds its gate: ${error}`);
  const changed=['eoere_clip_header_outer_under_left','eoere_clip_header_outer_under_right'];
  require(domain.affected_post_domains&&sameSet(Object.keys(domain.affected_post_domains),changed),
    'the two changed outer-post domain dispositions must be recorded');
  for(const body of changed){
    const proof=domain.affected_post_domains[body];
    require(proof?.post_support_patches===8&&proof.all_rebuilt_from_current_fields===true&&
      proof.parent_106_two_void_domain_rejected===true&&DOMAIN_POST_FLAGS.every(key=>proof[key]===true),
      'compact changed-post disposition differs: '+body);
  }
  return metrics;
}

export function validateSixBoltCleatComponentReferenceSummary(summary,expected){
  candidateIdentity(expected);
  require(summary?.schema==='v11_six_bolt_cleat_component_reference_summary/v1'&&
    summary.candidate_revision===REVISION,'final candidate-specific component-reference summary required');
  require(sameRef(summary.owner_authorization,expected.owner_authorization)&&sameRef(summary.geometry,expected.geometry)&&
    sameRef(summary.geometry_receipt,expected.geometry_metadata_receipt)&&
    sameRef(summary.checked_geometry_receipt,expected.physical_receipt)&&sameRef(summary.clearance,expected.clearance)&&
    sameRef(summary.mechanics_readiness,expected.mechanics_readiness)&&sameRef(summary.response_bank,expected.response_bank)&&
    sameRef(summary.parent_bank_admission,expected.parent_bank_admission)&&
    sameRef(summary.parent_runtime_proof,expected.parent_runtime_proof),
    'component summary must bind exact own geometry, both receipts, clearance, readiness, bank, admission and authorization');
  require(isRef(summary.header_bridge)&&isRef(summary.header_bridge_gate)&&isRef(summary.parent_runtime_proof),
    'component summary must retain its current bridge, additive gate, and validated parent runtime proof refs');
  require(summary.counts&&sameObject(summary.counts,COMPONENT_COUNTS),
    'component-reference summary counts differ from the exact 102-axis census');
  require(summary.component_routes&&summary.native_jobs,'final component routes and native-job record are required');
  for(const [route,children] of Object.entries(COMPONENT_ROUTES)){
    const data=summary.component_routes[route];require(data&&typeof data==='object','component route is missing: '+route);
    for(const child of children){
      const ref=data[child];requireRawCandidateRef(ref,`${route}.${child} must be a current candidate source reference`);
    }
  }
  for(const key of NATIVE_JOBS)requireRawCandidateRef(summary.native_jobs[key],'current parent native-job source ref is required: '+key);
  require(sameRef(summary.component_routes.angle_header.bridge,summary.header_bridge)&&
    sameRef(summary.component_routes.angle_header.bridge_gate,summary.header_bridge_gate),
    'header route must bind the summary bridge and its additive gate');
  require(summary.actual_property_inputs&&sameSet(Object.keys(summary.actual_property_inputs),ACTUAL_PROPERTY_KEYS)&&
    ACTUAL_PROPERTY_KEYS.every(key=>summary.actual_property_inputs[key]===null),
    'every specified actual material, adhesive, contact, preload and glue property must remain explicitly null');
  const metrics=validateSixBoltCleatCompactMetrics(summary.compact_metrics);
  require(metrics.counts.axes===summary.counts.axes&&metrics.counts.ends===summary.counts.ends&&
    metrics.counts.washer_end_case_rows===summary.counts.washer_end_case_rows&&
    metrics.counts.bond_leaf_wrench_states===summary.counts.bond_leaf_wrench_states&&
    metrics.counts.baseline_body_case_states===summary.counts.angle_baseline_body_case_states&&
    metrics.counts.header_variant_body_case_states===summary.counts.header_variant_body_case_states&&
    metrics.counts.header_event_aliases===summary.counts.header_event_aliases&&
    metrics.counts.baseline_fine_states===summary.counts.baseline_fine_states&&
    metrics.counts.header_fine_states===summary.counts.header_fine_states,
    'compact component metrics counts must equal the summary route census');
  checkFalseFlags(summary,['actual_property_qualification','complete_joint_qualified','structural_acceptance',
    'physical_release','candidate_selected','fabrication_released','drilling_released','climbing_released'],
    'component-reference-summary qualification/release boundary');
  return summary;
}

export function validateSixBoltCleatBackingDomainAudit(audit,integral,readiness,componentSummary,expected){
  candidateIdentity(expected);
  validateSixBoltCleatComponentReferenceSummary(componentSummary,expected);
  const readyRef=componentSummary.component_routes.angle_baseline.map_readiness;
  const integralRef=componentSummary.component_routes.backing_domain_audit.integral_quadrature_audit;
  require(audit?.schema==='v11_six_bolt_cleat_actual_backing_domain_quadrature_audit/v1'&&
    sameRef(audit.physical_geometry,expected.geometry)&&sameRef(audit.response_bank,expected.response_bank)&&
    sameRef(audit.readiness,readyRef)&&sameRef(audit.integral_quadrature_audit,integralRef),
    'backing-domain audit must bind current geometry, own bank, current map-readiness and its integral sibling');
  require(sameRef(readiness?.physical_geometry,expected.geometry)&&sameRef(readiness?.response_bank,expected.response_bank)&&
    isRef(readiness.mesh)&&isRef(readiness.deck)&&readiness.source_sha256&&typeof readiness.source_sha256==='object'&&
    readiness.native_execution_authorized_by_this_file===false&&readiness.no_native_or_mesh_execution===true,
    'domain-readiness source must use current geometry/bank and remain an input-only record');
  require(sameRef(integral?.physical_geometry,expected.geometry)&&sameRef(integral?.response_bank,expected.response_bank)&&
    sameRef(integral?.readiness,readyRef),'integral audit must bind the same current geometry, bank and readiness');
  const bodies=readiness.body_geometry;
  require(bodies&&typeof bodies==='object'&&Object.keys(bodies).length===24,
    'current backing-domain body inventory must contain all 24 readied member bodies');
  const expectedKeys=[];
  for(const [body,geometry] of Object.entries(bodies)){
    const actual=geometry.actual_normalized_domains,aliases=geometry.source_to_cached_patch;
    const checks=geometry.current_backing_source_area_and_centroid_checks;
    require(Number.isInteger(geometry.actual_backing_domains)&&actual&&aliases&&
      geometry.actual_backing_domains===Object.keys(actual).length&&geometry.actual_backing_domains===Object.keys(aliases).length&&
      sameSet(Object.keys(actual),Object.keys(aliases))&&Array.isArray(checks)&&
      sameSet(checks.map(row=>row.patch),Object.keys(actual)),
      'readiness must enumerate every current backing domain and cache alias: '+body);
    const exactCount=Object.values(aliases).filter(alias=>!alias.startsWith('fresh/')).length;
    const freshCount=Object.values(aliases).filter(alias=>alias.startsWith('fresh/')).length;
    require(geometry.exact_old_domain_alias_count===exactCount&&geometry.new_domain_quadrature_count===freshCount&&
      (exactCount===0||geometry.maximum_domain_alias_error_mm===0),
      'current backing-domain alias inventory or exact-coordinate gate differs: '+body);
    for(const patch of Object.keys(actual))expectedKeys.push(`${body}\u0000${patch}`);
  }
  const freshRows=readiness.new_actual_domain_quadrature;
  const expectedFresh=[...Object.entries(bodies).flatMap(([body,geometry])=>Object.entries(geometry.source_to_cached_patch)
    .filter(([,alias])=>alias.startsWith('fresh/')).map(([patch])=>`${body}\u0000${patch}`))];
  const freshKey=row=>`${row?.body}\u0000${row?.patch}`;
  require(Array.isArray(freshRows)&&sameSet(freshRows.map(freshKey),expectedFresh)&&
    freshRows.every(row=>{
      const geometry=bodies[row.body],domain=geometry?.actual_normalized_domains?.[row.patch];
      return geometry&&domain&&geometry.source_to_cached_patch[row.patch]==='fresh/'+row.quadrature?.path&&
        row.exact_old_cache_alias_available===false&&row.new_domain_integrated_on_existing_mesh===true&&
        sameObject(row.actual_normalized_domain,domain)&&isRef(row.quadrature);
    }), 'every changed current domain must have its own source-pinned fresh quadrature on the current mesh');
  const rowKey=row=>`${row?.body}\u0000${row?.patch}`;
  const auditRows=audit.domain_rows,integralRows=integral.domain_rows;
  require(Array.isArray(auditRows)&&Array.isArray(integralRows)&&auditRows.length===expectedKeys.length&&
    integralRows.length===expectedKeys.length&&new Set(auditRows.map(rowKey)).size===expectedKeys.length&&
    sameSet(auditRows.map(rowKey),expectedKeys)&&sameObject(auditRows,integralRows),
    'integral audit rows must exactly cover current geometry-derived backing domains');
  const byKey=new Map(auditRows.map(row=>[rowKey(row),row]));
  for(const [body,geometry] of Object.entries(bodies)){
    for(const [patch,domain] of Object.entries(geometry.actual_normalized_domains)){
      const row=byKey.get(`${body}\u0000${patch}`);
      require(row&&sameObject(row.actual_domain,domain),'audited domain differs from current map-readiness: '+body+'/'+patch);
      require(isRef(row.quadrature)&&row.exact_cache_alias===geometry.source_to_cached_patch[patch],
        'quadrature source alias differs from current map-readiness: '+body+'/'+patch);
    }
  }
  const summary=audit.summary,integralSummary=integral.summary;
  require(summary&&integralSummary&&sameObject(summary,integralSummary)&&
    summary.fittings===Object.keys(bodies).length&&summary.actual_domains===expectedKeys.length&&
    summary.exact_cached_domains+summary.newly_integrated_domains===summary.actual_domains,
    'domain audit totals must reconcile to the current body/domain census');
  const compactDomain=componentSummary.compact_metrics.domain;
  require(DOMAIN_METRICS.every(key=>compactDomain[key]===summary[key])&&
    compactDomain.affected_post_domains&&
    sameObject(compactDomain.affected_post_domains,audit.strict_exact_alias_check.affected_post_domains)&&
    componentSummary.compact_metrics.counts.actual_backing_domains===summary.actual_domains,
    'public compact domain metrics must equal the checked raw integral audit and current-readiness census');
  const rows=integralRows;
  const maxima={maximum_actual_area_error_mm2:Math.max(...rows.map(row=>row.area_error_mm2)),
    maximum_actual_first_moment_error_mm3:Math.max(...rows.map(row=>row.first_moment_error_mm3)),
    maximum_actual_centroid_error_mm:Math.max(...rows.map(row=>row.centroid_error_mm))};
  for(const [key,value] of Object.entries(maxima)){
    const gate=summary[key.replace('maximum_actual_','unchanged_').replace('_error','_gate')];
    require(Number.isFinite(summary[key])&&Math.abs(summary[key]-value)<1e-12,
      'integral audit maximum must match the checked domain rows: '+key);
    if(gate!==undefined)require(Number.isFinite(gate)&&value<=gate,'integral audit exceeds its current-domain gate: '+key);
  }
  const aliases=audit.strict_exact_alias_check,changed=['eoere_clip_header_outer_under_left','eoere_clip_header_outer_under_right'];
  require(aliases?.old_force_or_stress_reuse===false&&aliases.boundary_geometry_and_current_source_checks_rebuilt===true&&
    aliases.actual_domains===summary.actual_domains&&aliases.exact_cached_domains===summary.exact_cached_domains&&
    aliases.newly_integrated_domains===summary.newly_integrated_domains&&aliases.affected_post_domains&&
    sameSet(Object.keys(aliases.affected_post_domains),changed),
    'strict alias policy must rebuild changed post domains from current fields without reusing old forces/stresses');
  for(const body of changed){
    const proof=aliases.affected_post_domains[body],geometry=bodies[body];
    require(proof?.post_support_patches===8&&proof.all_rebuilt_from_current_fields===true&&
      proof.parent_106_two_void_domain_rejected===true&&DOMAIN_POST_FLAGS.every(key=>proof[key]===true),
      'changed outer-post backing must retain the checked near-steel and far-timber hole disposition: '+body);
    const patches=Object.entries(geometry.actual_normalized_domains).filter(([name])=>name.includes('/post/'));
    require(patches.length===8&&patches.every(([name,domain])=>{
      const holes=domain.domain?.void_disks;
      const row=byKey.get(`${body}\u0000${name}`);
      return geometry.source_to_cached_patch[name].startsWith('fresh/')&&Array.isArray(holes)&&holes.length===1&&
        Math.abs(holes[0][0]-65.0875)<1e-9&&Math.abs(holes[0][2]-5.159375)<1e-6&&
        sameObject(row?.actual_domain,domain)&&row?.exact_cache_alias===geometry.source_to_cached_patch[name];
    }), 'all eight changed-post timber patches must omit the near timber bore and retain the far timber bore: '+body);
  }
  for(const key of['actual_contact_qualified','structural_acceptance','physical_release'])
    require(audit[key]===false&&integral[key]===false,'domain evidence cannot claim actual contact or release: '+key);
  return {audit,integral,readiness};
}

function validateCurrentSummaryIdentity(identity,summary,expected){
  require(identity?.schema===summary.schema&&identity.revision===REVISION&&
    sameRef(identity.geometry,expected.geometry)&&sameRef(identity.response_bank,expected.response_bank)&&
    sameRef(identity.geometry_receipt,expected.physical_receipt)&&sameRef(identity.reference_outputs,summary.reference_outputs),
    'computed labels must embed the current source-bound reference summary identity');
  require(sameRef(identity.source_bindings?.bank,expected.response_bank)&&
    sameRef(identity.source_bindings?.geometry,expected.geometry)&&
    sameRef(identity.source_bindings?.receipt,expected.physical_receipt)&&
    sameRef(identity.source_bindings?.parent_bank_admission,expected.parent_bank_admission),
    'embedded current-reference summary must preserve every raw source join');
  requireCandidateInventory(identity.physical_inventory,'embedded current-reference inventory differs');
  require(sameSet(identity.axis_ids,expected.axis_ids)&&sameSet(identity.omitted_axis_ids,OMIT)&&
    sameSet(identity.case_ids,CASES)&&identity.independent_replays===12&&sameLoad(identity.load_contract),
    'embedded current-reference summary has stale axes, cases or load contract');
  for(const key of['actual_Cg','actual_Cdelta','actual_Fy','actual_Fyb','complete_joint_capacity'])
    require(identity[key]===null,'embedded current reference cannot adopt '+key);
  require(identity.actual_property_qualification===null&&
    sameObject(identity.conditional_reference_results,summary.conditional_reference_results),
    'embedded current-reference metrics must exactly match the public source-bound summary');
  checkFalseFlags(identity,SUMMARY_REQUIRED_FALSE,'embedded current-reference release boundary');
}

function validateComponentSummaryIdentity(identity,summary,expected){
  require(identity?.schema===summary.schema&&identity.candidate_revision===REVISION,
    'computed labels must embed the independent component-reference summary identity');
  for(const key of['owner_authorization','geometry','geometry_receipt','checked_geometry_receipt','clearance',
    'mechanics_readiness','response_bank','parent_bank_admission','header_bridge','header_bridge_gate','parent_runtime_proof'])
    require(sameRef(identity[key],summary[key]),'embedded component-reference identity differs at '+key);
  for(const key of['counts','component_routes','native_jobs','actual_property_inputs','compact_metrics'])
    require(sameObject(identity[key],summary[key]),'embedded component-reference identity differs at '+key);
  checkFalseFlags(identity,['actual_property_qualification','complete_joint_qualified','structural_acceptance',
    'physical_release','candidate_selected','fabrication_released','drilling_released','climbing_released'],
    'embedded component-reference qualification/release boundary');
}

function validateResultSources(sources,expected){
  for(const [key,ref] of Object.entries({owner_authorization:expected.owner_authorization,geometry:expected.geometry,
    geometry_receipt:expected.physical_receipt,checked_geometry_receipt:expected.physical_receipt,
    geometry_receipt_public:expected.geometry_receipt_public,
    geometry_metadata_receipt:expected.geometry_metadata_receipt,geometry_provenance:expected.geometry_provenance,
    clearance:expected.clearance,mechanics_readiness:expected.mechanics_readiness,response_bank:expected.response_bank,
    parent_bank_admission:expected.parent_bank_admission,current_reference_summary:expected.current_reference_summary,
    component_reference_summary:expected.component_reference_summary,parent_runtime_proof:expected.parent_runtime_proof}))
    require(sameRef(sources?.[key],ref),'result source binding differs: '+key);
}

export function validateSixBoltCleatResults(data,bank,admission,summary,componentSummary,expected){
  candidateIdentity(expected);
  validateSixBoltCleatResponseBank(bank,expected);
  validateSixBoltCleatParentBankAdmission(admission,expected);
  validateSixBoltCleatCurrentReferenceSummary(summary,expected);
  validateSixBoltCleatComponentReferenceSummary(componentSummary,expected);
  require(data?.schema==='eoere_v11_six_bolt_cleat_viewer_results/v1'&&data.model===SIX_BOLT_CLEAT_MODEL&&
    data.revision===REVISION,'own result model and revision required');
  require(sameRef(data.geometry,expected.geometry)&&sameRef(data.geometry_receipt,expected.physical_receipt)&&
    sameRef(data.geometry_provenance,expected.geometry_provenance)&&sameRef(data.response_bank,expected.response_bank)&&
    sameRef(data.parent_bank_admission,expected.parent_bank_admission),
    'result geometry, provenance, bank and admission must bind the current candidate');
  validateResultSources(data.sources,expected);
  require(data.response_bank_identity?.candidate_revision===REVISION&&
    sameRef(data.response_bank_identity.physical_geometry,expected.geometry)&&
    sameRef(data.response_bank_identity.physical_receipt,expected.physical_receipt),
    'result summary must embed the current candidate bank identity');
  requireCandidateInventory(data.response_bank_identity.physical_inventory,'embedded bank identity has the wrong physical census');
  require(sameSet(data.response_bank_identity.axis_ids,expected.axis_ids)&&
    sameSet(data.response_bank_identity.omitted_axis_ids,OMIT),'embedded bank identity has stale or omitted axes');
  require(sameSet(data.axis_ids,expected.axis_ids)&&sameSet(data.omitted_axis_ids,OMIT),
    'result axis rosters must include 102 current axes and exactly four omitted-axis controls');
  require(Array.isArray(data.cases)&&data.cases.length===6&&sameSet(data.cases.map(row=>row.case_id),CASES)&&
    data.independent_replays===12&&data.current_response_computed===true&&data.current_own_response_bank_recorded===true,
    'six current cases and twelve admitted independent replays must be recorded');
  for(const row of data.cases){
    require(row.both_independent_replays_admitted===true,'fresh case replay admission required: '+row.case_id);
    require(sameSet(row.axis_ids,expected.axis_ids),'result case contains omitted or stale axes: '+row.case_id);
  }
  validateCurrentSummaryIdentity(data.current_reference_summary_identity,summary,expected);
  validateComponentSummaryIdentity(data.component_reference_summary_identity,componentSummary,expected);
  require(sameObject(data.conditional_reference_results,summary.conditional_reference_results),
    'viewer metric projection must equal the public current-reference summary byte-for-byte in meaning');
  require(sameObject(data.compact_metrics,componentSummary.compact_metrics),
    'viewer component metric projection must equal the public component summary exactly');
  require(data.geometry_only===false&&data.analysis_pending===false&&data.trial_selected===false&&
    data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&data.actual_Fy_adopted===null&&
    data.actual_Fyb_adopted===null&&data.complete_joint_capacity===null&&
    (!('complete_connection_capacity' in data)||data.complete_connection_capacity===null),
    'computed references must not imply physical acceptance or select the trial');
  checkFalseFlags(data,RESULT_REQUIRED_FALSE,'result release/transfer boundary');
  return {data,bank,admission,summary,componentSummary};
}

function formatMetric(value){
  const number=Number(value),magnitude=Math.abs(number);
  return number!==0&&(magnitude<0.001||magnitude>=1e6)?number.toExponential(3):number.toFixed(3);
}
function metricOr(value,fallback='unresolved'){return Number.isFinite(value)?formatMetric(value):fallback;}
function formatIndex(value){return Number.isFinite(value)?Number(value).toFixed(6):'unresolved';}
function contractedWrenchStatus(route){
  const index=route.contracted_full_action?.maximum_contracted_bearing_index;
  return Number.isFinite(index)?formatIndex(index):'pending';
}
function referenceProjectionStatus(summary){
  const reference=summary.conditional_reference_results,families=reference.families.methods,
    mixed=reference.mixed,signed=reference.signed_end_edge,planar=signed.signed_planar_rear_foot,
    supplemental=signed.supplemental_signed_end_markers,marker=signed.full_7d_end_marker,
    optionalFoot=signed.optional_both_edge_foot_diagnostic,
    optionalValues=optionalFoot.marker_rows,
    individual=reference.optional_diagnostics.individual_EYM_Cg_equation_bound,
    brittle=reference.brittle_paths.component_reference_summaries,
    cuts=brittle.member_cuts.summary,interrupted=brittle.interrupted_paths.summary,
    connected=brittle.connected_paths.summary,reduced=brittle.reduced_depth.summary,
    front=reference.front,rear=reference.rear,
    frontProjected=front.projected_witness.maximum_projected_reference_index_case,
    rearProjected=rear.projected_witness.maximum_projected_reference_index_case;
  return [
    `Conditional maxima: timber net-shear/torsion ${formatIndex(families.timber_net_shear_torsion.maximum?.index)}, `+
      `normal/stability ${formatIndex(families.timber_normal_and_stability.maximum?.index)}, cleat perimeter `+
      `${formatIndex(families.cleat_actual_perimeter_rows.maximum?.index)}, direct elastic steel `+
      `${formatIndex(families.direct_elastic_steel.maximum?.index)}; `+
      `${summary.scope.shaft_case_closures} shaft closures. Inherited-factor pressure/N/M maxima `+
      `${formatIndex(reference.families.inherited_factor_diagnostics.wood_bearing_whole_affine.maximum.index)}/`+
      `${formatIndex(reference.families.inherited_factor_diagnostics.reduced_connection_axial_bending.maximum.index)}; `+
      `13/612 rows above one each, unadopted, actual Cg unassigned.`,
    `Mixed (20 axes/120 states/240 planes): plane/common-work maxima `+
      `${metricOr(mixed.maximum_plane_reference?.plane_force_over_Z_conditional_reference)}/${metricOr(mixed.maximum_common_work_index)}. `+
      `Front retained affine-construction Fe/5 diagnostic max `+
      `${formatIndex(front.full_wrench_conditional_reference.maximum_Fe_over_5_utilization)} `+
      `(${front.full_wrench_conditional_reference.Fe_over_5_states_above_one}/${front.full_wrench_conditional_reference.state_count} states above 1); `+
      `projected witness max ${formatIndex(frontProjected[2])} `+
      `(${front.projected_witness.reference_index_above_one_count}/${front.projected_witness.state_count} above 1). Rear retained `+
      `affine-construction Fe/5 diagnostic max `+
      `${formatIndex(rear.full_wrench_conditional_reference.maximum_Fe_over_5_utilization)} `+
      `(${rear.full_wrench_conditional_reference.Fe_over_5_states_above_one}/${rear.full_wrench_conditional_reference.state_count} states above 1); `+
      `projected witness max ${formatIndex(rearProjected[2])} `+
      `(${rear.projected_witness.reference_index_above_one_count}/${rear.projected_witness.state_count} above 1). `+
      `Contracted full-action bearing indices: front ${contractedWrenchStatus(front)}, `+
      `rear ${contractedWrenchStatus(rear)}.`,
    `Signed rear-foot selector ${formatIndex(planar.maximum_conditional_planar_component_index)} `+
      `(${planar.resolved_case_count} resolved, ${planar.above_one_count} flags); retained optional two-edge foot envelope `+
      `${formatIndex(Math.max(...optionalValues))} (${optionalValues.filter(value=>value>1).length} flags), separate and unselected. `+
      `Four omitted near-post axes: zero reported net/primitive end flags; empty arrays are not acceptance. `+
      `Open full-7D marker ${metricOr(marker.principal_end_only_Cdelta_ratio)} (${metricOr(marker.shortfall_mm)} mm short), not Cdelta or failure.`,
    `Wood paths: cuts E2/E3/E4 ${cuts.counts.E2}/${cuts.counts.E3}/${cuts.counts.E4} rows, flags `+
      `${cuts.flags.E2}/${cuts.flags.E3}/${cuts.flags.E4}; interrupted ${interrupted.directional_case_rows} rows `+
      `(${interrupted.valid_directional_reference_rows} valid, ${interrupted.blocked_positive_net_force_rows} blocked, `+
      `${interrupted.measured_interrupted_paths} paths); connected ${connected.case_direction_rows} rows, `+
      `${connected.above_one_count} flags. Reduced-depth both-edge max ${formatIndex(reduced.maximum_conditional_index)} `+
      `(${reduced.above_one_rows}/${reduced.case_rows} case rows above 1; ${reduced.edge_scenario_rows} edge-scenario comparisons), `+
      `a component check only. `+
      `Optional ${individual.row_count}-row EYM is non-adopted; no parent-106 transfer.`,
  ].join('\n\n');
}
function componentMetricStatus(metrics){
  const w=metrics.washer,b=metrics.bond,a=metrics.angle_baseline,h=metrics.angle_header,
    fine=metrics.fine,d=metrics.domain;
  return `Washers (1,224 end/case rows; 204 unique ends): mean indices, sawn/dry ply/0.02-inch ply `+
    `${formatMetric(w.maximum_sawn_mean_index)}/${formatMetric(w.maximum_plywood_dry_mean_index)}/${formatMetric(w.maximum_plywood_02in_mean_index)}; `+
    `CAD-thickness/continuous-box required Fy ${formatMetric(w.maximum_CAD_thickness_required_Fy_1_67_MPa)}/`+
    `${formatMetric(w.maximum_continuous_dimension_box_required_Fy_1_67_MPa)} MPa. Bond (12 six-resultant states): `+
    `q ${formatMetric(b.maximum_long_wavelength_q_N_per_mm)} N/mm, average shear ${formatMetric(b.maximum_long_wavelength_width_average_shear_MPa)} MPa, `+
    `normal/tangential demand ${formatMetric(b.maximum_reduced_normal_compression_cap_MPa)}/${formatMetric(b.maximum_reduced_tangential_traction_MPa)} MPa; `+
    `compression-only static witness, not capacity.\n\n`+
    `Coarse baseline/header fitting VM ${formatMetric(a.maximum_IP_VM_MPa)}/${formatMetric(h.maximum_IP_VM_MPa)} MPa, `+
    `required Fy ${formatMetric(a.required_Fy_1_67_MPa)}/${formatMetric(h.required_Fy_1_67_MPa)}, 235-MPa markers `+
    `${formatMetric(a.conditional_Fy235_marker_index)}/${formatMetric(h.conditional_Fy235_marker_index)}. `+
    `Selected 3-mm fine VM ${formatMetric(fine.baseline.fine_VM_MPa)}/${formatMetric(fine.header.fine_VM_MPa)} MPa; `+
    `required Fy ${formatMetric(fine.baseline.fine_required_Fy_1_67_MPa)}/${formatMetric(fine.header.fine_required_Fy_1_67_MPa)}, `+
    `coarse-to-fine changes ${formatMetric(fine.baseline.relative_VM_change)}/${formatMetric(fine.header.relative_VM_change)}.\n\n`+
    `Backing: ${d.actual_domains} current patches passed quadrature (${d.newly_integrated_domains} fresh, `+
    `${d.exact_cached_domains} cached). Each changed post has eight `+
    `rebuilt patches; the near timber bore is absent, the unused near 10 mm factory steel hole remains, and the far timber bore remains.`;
}

export function sixBoltCleatResultsStatus(input){
  const {data,bank,summary}=input,load=summary.load_contract,headerGate=data.compact_metrics.angle_header.bridge_gate;
  return `Six-bolt cleat: 102 stacks; six admitted cases/twelve replays at ${load.weight_lb} lb × ${load.downward_multiplier}, `+
    `${load.horizontal_force_N} N, ${load.accessory_mass_kg} kg, CD ${load.duration_factor_CD}. Four side/two post bolts per cleat, `+
    `four at each outer and center top connection, zero spacers.\n\n`+
    `${referenceProjectionStatus(summary)}\n\n${componentMetricStatus(data.compact_metrics)}\n\n`+
    `Header bridge: ${headerGate.fresh_case_event_rows} rows; both gates pass. Conditional and unselected. `+
    `Actual properties and whole-joint capacity remain open. No purchase, cutting, drilling, fabrication or climbing release. `+
    `Panel strength and Hillman resistance are outside this packet; details remain in linked summaries.`;
}

export function applySixBoltCleatResults(scene,data,bank,admission,summary,componentSummary,expected){
  const accepted=validateSixBoltCleatResults(data,bank,admission,summary,componentSummary,expected).data;
  require(scene.design.key===SIX_BOLT_CLEAT_MODEL&&scene.parts.length===1035&&scene.meta.counts.bolt_stacks===102&&
    scene.meta.counts.spacer_pieces===0&&scene.meta.geometry_only===true&&scene.meta.current_response_computed===false&&
    scene.meta.geometry_sha256===accepted.geometry.sha256&&scene.meta.layout_sha256===accepted.geometry_receipt.sha256&&
    scene.meta.provenance_sha256===accepted.geometry_provenance.sha256,
    'candidate raw geometry stage with preserved geometry provenance required');
  const description='Six-bolt cleat development geometry: four side and two post bolts per cleat, four bolts at each outer-top and center-top connection, zero spacers. Own current response and component references are source-bound; actual properties and complete-joint qualification remain open.';
  const parts=scene.parts.map(part=>({...part,fabrication:{...part.fabrication,description}}));
  const summaryIdentity=accepted.current_reference_summary_identity,componentIdentity=accepted.component_reference_summary_identity;
  return {...scene,parts,meta:{...scene.meta,status:sixBoltCleatResultsStatus({data:accepted,bank,summary}),geometry_only:false,
    analysis_pending:false,current_response_computed:true,current_own_response_bank_recorded:true,
    current_reference_summary_recorded:true,component_reference_summary_recorded:true,case_rows:accepted.cases,
    independent_replays:12,response_bank:accepted.response_bank,response_bank_identity:accepted.response_bank_identity,
    current_reference_summary:summaryIdentity,component_reference_summary:componentIdentity,
    conditional_reference_results:accepted.conditional_reference_results,
    compact_metrics:accepted.compact_metrics,
    load_contract:summaryIdentity.load_contract,trial_selected:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,
    actual_Fy_adopted:null,actual_Fyb_adopted:null,complete_joint_capacity:null,complete_connection_capacity:null,
    actual_property_qualification:false,fixed_load_only:true,weight_interpolation_available:false,planning_mass_kg:null,
    historical_field_or_force_transfer:false,historical_capacity_transferred:false,complete_joint_qualified:false,
    complete_group_qualified:false,physical_force_bounds_established:false,actual_property_adopted:false,
    candidate_selected:false,structural_acceptance:false,purchase_authorized:false,drilling_released:false,
    physical_changes_authorized:false,physical_release:false,fabrication_released:false,climbing_released:false,
    portable_sources:{...scene.meta.portable_sources,geometry_provenance:accepted.geometry_provenance,
      geometry:accepted.geometry,geometry_receipt:accepted.geometry_receipt,response_bank:accepted.response_bank,
      parent_bank_admission:accepted.parent_bank_admission,current_reference_summary:accepted.sources.current_reference_summary,
      component_reference_summary:accepted.sources.component_reference_summary,
      parent_runtime_proof:accepted.sources.parent_runtime_proof}}};
}

export async function fetchPinnedJson(publicRef,rawRef,label){
  require(isRef(publicRef)&&sameRef(publicRef,{path:publicRef.path,sha256:rawRef?.sha256}),label+' public and raw source pins must match');
  require(publicRef.path.startsWith('docs/')&&!publicRef.path.includes('..'),label+' must use a portable docs copy');
  // Pages serves site/ only; the portable docs live in the public repository.
  // Use an immutable source revision and retain the exact-byte hash check below.
  const docsBase='https://raw.githubusercontent.com/mckayreedmoore/mini-moonboard/aa226a78c759844b08b6050737f17186825b0aec/';
  const response=await fetch(new URL(publicRef.path,docsBase));require(response.ok,label+' portable copy unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===rawRef.sha256,label+' portable copy differs from its exact raw source');
  return JSON.parse(new TextDecoder().decode(raw));
}

async function readResultsAsset(ref){
  require(ref?.path==='site/eoere-v11-six-bolt-cleat-results.json'&&/^[a-f0-9]{64}$/.test(ref.sha256),
    'parent-integrated candidate result asset binding required');
  const response=await fetch(new URL(ref.path.slice(5),import.meta.url));require(response.ok,'candidate result asset unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===ref.sha256,'candidate result asset source pin differs');
  return JSON.parse(new TextDecoder().decode(raw));
}

function expectedBindings(scene,sources){
  require(sameRef(scene.meta.portable_sources.geometry_receipt,sources.geometry_receipt_public),
    'geometry preview must keep the checked receipt portable path and exact hash');
  return candidateIdentity({revision:REVISION,geometry:scene.meta.portable_sources.geometry,
    geometry_receipt:sources.checked_geometry_receipt,geometry_receipt_public:sources.geometry_receipt_public,
    physical_receipt:sources.checked_geometry_receipt,
    geometry_metadata_receipt:sources.geometry_metadata_receipt,geometry_provenance:SIX_BOLT_CLEAT_ASSETS,
    owner_authorization:sources.owner_authorization,clearance:sources.clearance,mechanics_readiness:sources.mechanics_readiness,
    response_bank:sources.response_bank,parent_bank_admission:sources.parent_bank_admission,
    current_reference_summary:sources.current_reference_summary,component_reference_summary:sources.component_reference_summary,
    parent_runtime_proof:sources.parent_runtime_proof,
    response_bank_public:sources.response_bank_public,parent_bank_admission_public:sources.parent_bank_admission_public,
    current_reference_summary_public:sources.current_reference_summary_public,
    component_reference_summary_public:sources.component_reference_summary_public,axis_ids:scene.meta.axis_ids});
}

export async function loadSixBoltCleatPreviewScene(THREE,options){
  const scene=await loadSixBoltCleatGeometryScene(THREE,options);
  if(!SIX_BOLT_CLEAT_RESULTS_ASSET||!SIX_BOLT_CLEAT_RESULTS_SOURCES)return scene;
  const sources=SIX_BOLT_CLEAT_RESULTS_SOURCES,expected=expectedBindings(scene,sources);
  const [bank,admission,summary,componentSummary]=await Promise.all([
    fetchPinnedJson(sources.response_bank_public,expected.response_bank,'own response bank'),
    fetchPinnedJson(sources.parent_bank_admission_public,expected.parent_bank_admission,'parent bank admission'),
    fetchPinnedJson(sources.current_reference_summary_public,expected.current_reference_summary,'current reference summary'),
    fetchPinnedJson(sources.component_reference_summary_public,expected.component_reference_summary,'component reference summary'),
  ]);
  validateSixBoltCleatResponseBank(bank,expected);
  validateSixBoltCleatParentBankAdmission(admission,expected);
  validateSixBoltCleatCurrentReferenceSummary(summary,expected);
  validateSixBoltCleatComponentReferenceSummary(componentSummary,expected);
  const data=await readResultsAsset(SIX_BOLT_CLEAT_RESULTS_ASSET);
  return applySixBoltCleatResults(scene,data,{...bank,axis_ids:expected.axis_ids,omitted_axis_ids:OMIT},admission,
    summary,componentSummary,expected);
}
