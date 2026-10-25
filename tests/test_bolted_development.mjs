import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, readIndex as readCurrentIndex, checkDevelopment as checkCurrentDevelopment, validateEntry, validateCurrent96Review, validateCurrent96TestingReview, validateBoltGeometryReview, validateCurrentBoltGeometryReview, validateOwnResponseBank, candidate13SourceResolver, readV10Candidate13Authority, validateV10Candidate13Authority, validateCurrentConventionalReferenceReview, validateCurrentPanelBracingSummary, currentFittingProbeGeometry, validateStructuralAssessment, validateCurrentResponse, validateCurrentComponents, validateEngineeringAssessment, validatePackerFreeMethodEvaluation, validatePackerFreeMethodFollowups, validatePackerFreeFittingReference, validatePackerFreeSawnReference, validateUnselectedCenterFarRowTrial, validateLocalSubassemblyActionMap, validateCurrent112HardwarePlanning, validateCurrent112GroupEffects, viewerModel} from '../scripts/check_bolted_development.mjs';
import {validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';
import {validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';
import {validateFrontPosts} from '../site/eoere-front-posts-4x6-overlay.mjs';
import {validateNarrowChannels} from '../site/eoere-narrow-channels-overlay.mjs';
import {validateRetainedFrame} from '../site/eoere-retained-frame-overlay.mjs';
import {validateOwnerFrame} from '../site/eoere-owner-frame-overlay.mjs';
import {validateReferenceCleats} from '../site/eoere-reference-cleat-overlay.mjs';
import {validatePrincipalPairs} from '../site/eoere-principal-pair-overlay.mjs';
import {validateInwardBolts} from '../site/eoere-inward-bolts-overlay.mjs';
import {validateInwardAngles} from '../site/eoere-inward-angles-overlay.mjs';
import {validateSingleSpacers} from '../site/eoere-single-spacer-overlay.mjs';

// Keep exercising the preserved force/shop contracts against their own geometry.
function ownRevision(revision) {
  let index = readCurrentIndex();
  while (index && index.geometry.revision !== revision) index = index.preceding_revision;
  assert.ok(index, `preserved revision missing: ${revision}`);
  return index;
}
const readNotchIndex = () => ownRevision('eoere-narrow-channel-openings-v1');
const readPostIndex = () => ownRevision('eoere-4x6-front-posts-v1');
const readIndex = () => ownRevision('eoere-raised-kicker-screws-v1');
const read96Index = () => ownRevision('eoere-flat-cleats-principal-upper-pairs-v6');
const readStandardSideIndex = () => ownRevision('v10-standard-4x6-top-and-sides-development-v1');
const readPackerFreeIndex = () => ownRevision('v10-packer-free-flush-return-far-row-only-v1');
const checkDevelopment = (index = readIndex()) => checkCurrentDevelopment(index, {entryChecks: false});

const candidate13Index = ownRevision('eoere-candidate13-side-depth-v10');
const candidate13 = readV10Candidate13Authority(candidate13Index);
test('Candidate13 source resolver reads only mapped repository copies, leaving raw fields unopened', () => {
  const requested = [];
  const resolver = candidate13SourceResolver(candidate13.manifest, ref => {
    requested.push(ref.path);
    assert.ok(ref.path.startsWith('docs/bolted-frame-development/owner-frame-v10/candidate13/') ||
      ref.path === 'site/eoere-v10-scene-13.json.gz');
    return readFileSync(path.join(ROOT, ref.path));
  });
  assert.equal(requested.length, 57);
  assert.throws(() => resolver.sourceBound(candidate13.bank.cases[0].field));
  assert.equal(requested.length, 57, 'an unmapped raw field must never trigger another file read');
});
test('Candidate13 source resolver rejects a changed decoded frozen paper source hash', () => {
  const manifest = structuredClone(candidate13.manifest);
  manifest.support_files.find(row => row.encoding === 'gzip').original.sha256 = '0'.repeat(64);
  assert.throws(() => candidate13SourceResolver(manifest));
});
test('Candidate13 source resolver rejects changed integrated encoded bytes', () => {
  const compressed = candidate13.manifest.support_files.find(row => row.encoding === 'gzip').integrated.path;
  assert.throws(() => candidate13SourceResolver(candidate13.manifest, ref => {
    const bytes = readFileSync(path.join(ROOT, ref.path));
    if (ref.path === compressed) {const changed = Buffer.from(bytes); changed[changed.length-1] ^= 1; return changed;}
    return bytes;
  }));
});
test('Candidate13 current development retains its own conditional package and all 26 trial flags', () => {
  assert.equal(validateV10Candidate13Authority(candidate13Index, candidate13).trial_case_flags, 26);
});
test('owner-selected 4x6 development has its own matched bank and preserves Candidate13 separately', () => {
  const selected = candidate13Index.development_selection;
  const result = checkCurrentDevelopment(candidate13Index, {entryChecks: false});
  assert.equal(result.revision, selected.revision);
  assert.equal(result.preserved_integrated_package_revision, 'eoere-candidate13-side-depth-v10');
  assert.equal(result.trial_case_flags, 15); assert.equal(result.trial_flagged_components, 8);
  assert.equal(result.occupied_parts, 1151); assert.equal(result.spacer_pieces, 44);
  assert.equal(result.candidate_selection_only, true); assert.equal(result.purchase_authorized, false);
});
test('standard 4x6 top and sides use a fresh matched bank with unresolved complete joints', () => {
  const result = checkCurrentDevelopment(readStandardSideIndex(), {entryChecks: false});
  assert.equal(result.revision, 'v10-standard-4x6-top-and-sides-development-v1');
  assert.equal(result.reference_case_exceedances, 15);
  assert.equal(result.repository_viewer_integrated, true);
  assert.equal(result.next_candidate_revision, 'v10-packer-free-flush-return-far-row-only-v1');
  assert.equal(result.next_candidate_own_matched_bank_complete, true);
  assert.equal(result.next_candidate_bolt_stacks, 112);
  assert.equal(result.reference_component_exceedances, 8);
  assert.equal(result.actual_Cg_adopted, null);
  assert.equal(result.custom_packers_approved, false);
});
for (const [name, mutate] of [
  ['deeper side substitution', r => {r.development_selection.actual_sections_mm.base_side_left = [88.9, 152.4];}],
  ['ignored viewer runtime dependency', r => {r.repository_viewer.ignored_runtime_dependencies = true;}],
  ['historical viewer substituted', r => {r.repository_viewer.scene = r.preceding_revision.geometry.scene;}],
  ['baseline viewer promotion', r => {r.repository_viewer.selected_baseline_changed = true;}],
  ['unrequested viewer deployment', r => {r.repository_viewer.published_or_deployed = true;}],
  ['approved custom packers', r => {r.development_selection.custom_packers_approved = true;}],
  ['purchasing through selection', r => {r.development_selection.purchase_authorized = true;}],
  ['build selection', r => {r.hardware_model.selected_for_build = true;}],
  ['released historical drills', r => {r.shop.historical_cut_drill_packet_current = true;}],
  ['adopted group factor', r => {r.actual_Cg_adopted = 1;}],
  ['complete joint qualification', r => {r.complete_joint_qualified = true;}],
  ['older force bank', r => {r.response_bank = r.preceding_revision.development_selection.response_bank;}],
  ['foreign connection review', r => {r.connection_review = r.preceding_revision.engineering_review;}],
  ['missing current method evaluation', r => {delete r.connection_method_evaluation;}],
  ['foreign current method evaluation', r => {r.connection_method_evaluation = r.connection_review;}],
  ['next candidate permits wood packers', r => {r.next_candidate_constraint.wood_packers_permitted = true;}],
  ['packer bank silently reused', r => {r.next_candidate_constraint.current_packer_bank_transferred_to_new_design = true;}],
  ['old packer machining allowed', r => {r.next_candidate_constraint.old_packer_machining_and_allocation_on_hold = false;}],
  ['foreign packer-free bank', r => {r.next_candidate_constraint.trial_response_bank = r.response_bank;}],
  ['foreign packer-free evaluation', r => {r.next_candidate_constraint.trial_evaluation = r.standard_side_stock_evaluation;}],
  ['foreign packer-free geometry receipt', r => {r.next_candidate_constraint.trial_geometry_receipt = r.geometry.receipt;}],
  ['foreign packer-free allocation', r => {r.next_candidate_constraint.conditional_stock_planning = r.stock_planning;}],
  ['ignored packer-free runtime dependency', r => {r.next_candidate_constraint.repository_geometry_viewer.ignored_runtime_dependencies = true;}],
  ['fabrication release', r => {r.fabrication_released = true;}],
]) test(`reject standard-side candidate ${name}`, () => {
  const index = readStandardSideIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

test('packer-free development promotes its own matched evidence and results without selecting a build', () => {
  const index = readPackerFreeIndex();
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.revision, index.geometry.revision);
  assert.equal(result.current_response_revision, index.geometry.revision);
  assert.equal(result.bolt_axes, 112); assert.equal(result.screw_axes, 66);
  assert.equal(result.occupied_parts, 1125); assert.equal(result.spacer_pieces, 40);
  assert.equal(result.wood_packers, 0); assert.equal(result.geometry_only, false);
  assert.equal(result.reference_case_exceedances, 15); assert.equal(result.reference_component_exceedances, 8);
  assert.equal(result.preserved_previous_development_revision, index.preceding_revision.geometry.revision);
  assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.equal(result.stock_planning_scope, 'wood allocation only');
  assert.equal(result.full_ignored_input_closure_checked, false); assert.equal(result.mechanics_executed, false);
});

for (const [name, mutate] of [
  ['wrong geometry revision', r => {r.geometry.revision = r.preceding_revision.geometry.revision;}],
  ['historical geometry receipt', r => {r.geometry.receipt = r.preceding_revision.geometry.receipt;}],
  ['historical scene', r => {r.geometry.scene = r.preceding_revision.geometry.scene;}],
  ['unselected side depth', r => {r.geometry.actual_sections_mm.base_side_left = [88.9, 152.4];}],
  ['old packer response bank', r => {r.response_bank = r.preceding_revision.response_bank;}],
  ['old packer evaluation', r => {r.engineering_review = r.preceding_revision.engineering_review;}],
  ['old connection methods', r => {r.connection_method_evaluation = r.preceding_revision.connection_method_evaluation;}],
  ['old packer wood allocation', r => {r.stock_planning = r.preceding_revision.stock_planning;}],
  ['incomplete spacer ledger', r => {r.hardware_model.nominal_spacer_SKU_quantities['13731'] = 12;}],
  ['foreign spacer mapping', r => {r.hardware_spacer_mapping = r.stock_planning;}],
  ['historical buying CSV', r => {r.current_stock_documents['buying-list-current.csv'] =
    r.preceding_revision.stock_planning_frozen_output_snapshots['docs/bolted-frame-development/owner-frame-v10/buying-list-current.csv'];}],
  ['foreign owner constraint', r => {r.owner_no_packers = r.preceding_revision.owner_side_constraint;}],
  ['geometry-only results asset', r => {r.repository_viewer.results_json = r.preceding_revision.repository_viewer.status;}],
  ['old results overlay', r => {r.repository_viewer.results_overlay = r.preceding_revision.repository_viewer.overlay;}],
  ['geometry publisher used for results', r => {r.repository_viewer.results_publisher = r.repository_viewer.geometry_publisher;}],
  ['foreign geometry overlay', r => {r.repository_viewer.geometry_overlay = r.preceding_revision.repository_viewer.overlay;}],
  ['foreign frozen export', r => {r.repository_viewer.frozen_export = r.preceding_revision.geometry.scene;}],
  ['geometry-only viewer claim', r => {r.repository_viewer.geometry_only = true;}],
  ['ignored runtime dependency', r => {r.repository_viewer.ignored_runtime_dependencies = true;}],
  ['viewer deployment', r => {r.repository_viewer.published_or_deployed = true;}],
  ['baseline promotion', r => {r.selected_baseline.candidate = r.geometry.revision;}],
  ['adopted Cg', r => {r.actual_Cg_adopted = 1;}],
  ['adopted Cdelta', r => {r.actual_Cdelta_adopted = 1;}],
  ['complete connection acceptance', r => {r.complete_connection_acceptance = true;}],
  ['build selection', r => {r.hardware_model.selected_for_build = true;}],
  ['invented part observations', r => {r.hardware_model.actual_parts_verified = true;}],
  ['historical drill release', r => {r.shop.historical_cut_drill_packet_current = true;}],
  ['missing method evidence joins', r => {delete r.method_source_joins;}],
  ['foreign fresh atlas', r => {r.method_source_joins.current_wrench_atlas = r.preceding_revision.response_bank;}],
  ['historical V3 post-audit', r => {r.method_source_joins.v3_post_audit.path =
    'fea/generated/v10-standard-side-stock-v1/previous-post-audit.json';}],
  ...['complete_joint_qualified', 'structural_acceptance', 'fabrication_released', 'climbing_released',
    'purchase_authorized', 'physical_operations_authorized'].map(key => [key, r => {r[key] = true;}]),
  ['panel resolution no longer deferred', r => {r.panel_Hillman_resolution_deferred = false;}],
  ['review loop resumed', r => {r.agent_review_loop_suspended = false;}],
]) test(`reject packer-free authority ${name}`, () => {
  const index = readPackerFreeIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [name, mutate] of [
  ['old bank', (r, i) => {r.response_bank = i.preceding_revision.response_bank;}],
  ['old evaluation', (r, i) => {r.evaluation = i.preceding_revision.engineering_review;}],
  ['old geometry', (r, i) => {r.geometry_receipt = i.preceding_revision.geometry.receipt;}],
  ['old axis-case census', r => {r.coverage.axis_case_wrenches = 696;}],
  ['missing source report', r => {delete r.source_bindings[Object.keys(r.source_bindings)[0]];}],
  ['old method source', r => {r.source_bindings[Object.keys(r.source_bindings)[0]].path =
    'fea/generated/v10-standard-side-stock-v1/historical-method.json';}],
  ['adopted actual Cg', r => {r.actual_Cg = 1;}],
  ['adopted actual Cdelta', r => {r.actual_Cdelta = 1;}],
  ['complete connection accepted', r => {r.complete_connection_acceptance = true;}],
  ['fabrication release', r => {r.fabrication_released = true;}],
  ['no remaining qualifications', r => {r.remaining = [];}],
]) test(`reject packer-free method summary ${name}`, () => {
  const index = readPackerFreeIndex();
  const methods = JSON.parse(readFileSync(path.join(ROOT, index.connection_method_evaluation.path)));
  mutate(methods, index);
  assert.throws(() => validatePackerFreeMethodEvaluation(methods, index));
});

test('portable packer-free method checks retain raw references without opening ignored reports', () => {
  const index = readPackerFreeIndex();
  const methods = JSON.parse(readFileSync(path.join(ROOT, index.connection_method_evaluation.path)));
  methods.source_bindings[Object.keys(methods.source_bindings)[0]] = {
    path: 'fea/generated/v10-packer-free-v1/not-materialized-for-this-control.json', sha256: '0'.repeat(64)};
  assert.equal(validatePackerFreeMethodEvaluation(methods, index), methods);
});

test('optional rear-foot diagnostics remain separate from bearing flags and normative acceptance', () => {
  const result = checkCurrentDevelopment(readPackerFreeIndex(), {entryChecks: false});
  assert.equal(result.reference_case_exceedances, 15); assert.equal(result.bearing_diagnostic_case_rows, 15);
  assert.equal(result.optional_rear_foot_case_group_rows, 12); assert.equal(result.optional_rear_foot_full_cut_wrenches, 48);
  assert.equal(result.optional_rear_foot_envelope_case_rows, 3); assert.equal(result.optional_rear_foot_envelope_axes, 2);
  assert.equal(result.optional_rear_foot_maximum_envelope_ratio, 1.0977299914214838);
  assert.equal(result.optional_rear_foot_actual_loaded_edge, null);
  assert.equal(result.optional_rear_foot_NDS_loaded_edge_violation_found, false);
  assert.equal(result.optional_rear_foot_centering_adopted, false);
  assert.equal(result.structural_acceptance, false); assert.equal(result.full_ignored_input_closure_checked, false);
});

for (const [name, mutate] of [
  ['foreign primary bank', (r, i) => {r.primary_method_closure.source_bindings.current_response_bank = i.preceding_revision.response_bank;}],
  ['foreign geometry', (r, i) => {r.geometry_method_followup.current_model_bindings.checked_receipt = i.preceding_revision.geometry.receipt;}],
  ['foreign contact bank', (r, i) => {r.contact_law_evaluation.evidence_bindings.current_response_bank = i.preceding_revision.response_bank;}],
  ['foreign foot bank', (r, i) => {r.rear_foot_shear_evaluation.source_bindings.response_bank = i.preceding_revision.response_bank;}],
  ['foreign centering bank', (r, i) => {r.rear_foot_centering_screen.source_refs.six_case_bank = i.preceding_revision.response_bank;}],
  ['wrong schema', r => {r.contact_law_evaluation.schema = 'unbound-contact-summary/v1';}],
  ['malformed source', r => {r.rear_foot_shear_evaluation.source_bindings.event_cut_kernel.sha256 = 'invalid';}],
  ['erased criterion axis', r => {r.connection_criterion_dispositions.current_flagged_action_envelopes.pop();}],
  ['qualified group capacity', r => {r.primary_method_closure.qualification.complete_group_capacity = 1;}],
  ['adopted criterion Cg', r => {r.connection_criterion_dispositions.disposition.actual_Cg = 1;}],
  ['panel contact comparison enabled', r => {r.contact_law_evaluation.conditional_sawn_wood_mean_pressure_screen.panel_contact_rows_skipped = 0;}],
  ['actual contact pass', r => {r.contact_law_evaluation.actual_pass = true;}],
  ['missing full foot cuts', r => {r.rear_foot_shear_evaluation.cut_inventory.total_full_cut_wrenches = 47;}],
  ['erased optional flag', r => {r.rear_foot_shear_evaluation.optional_envelope_exceedances.pop();}],
  ['missing other edge reference', r => {r.rear_foot_shear_evaluation.geometry.members[0].edge_branches.pop();}],
  ['invented loaded edge', r => {r.rear_foot_shear_evaluation.geometry.members[0].actual_loaded_edge_classification = 'positive_q';}],
  ['optional flag made normative', r => {r.rear_foot_shear_evaluation.interpretation.NDS_loaded_edge_violation_found = true;}],
  ['centering adopted', r => {r.rear_foot_centering_screen.screen.adopted = true;}],
  ['centering claimed new force pass', r => {r.rear_foot_centering_screen.screen.actual_new_pass = true;}],
  ['centering released', r => {r.rear_foot_centering_screen.qualification.fabrication_released = true;}],
]) test(`reject method followup ${name}`, () => {
  const index = readPackerFreeIndex();
  const reports = Object.fromEntries(Object.entries(index.method_followups).map(([key, ref]) =>
    [key, JSON.parse(readFileSync(path.join(ROOT, ref.path)))]));
  mutate(reports, index);
  assert.throws(() => validatePackerFreeMethodFollowups(reports, index));
});

for (const [name, mutate] of [
  ['changed report bytes', r => {r.method_followups.contact_law_evaluation.sha256 = '0'.repeat(64);}],
  ['foreign public source', r => {r.method_followups.rear_foot_shear_evaluation = r.method_followups.primary_method_closure;}],
  ['omitted report', r => {delete r.method_followups.rear_foot_centering_screen;}],
  ['changed fitting report', r => {r.method_followups.fitting_gross_strip_reference.sha256 = '0'.repeat(64);}],
  ['changed sawn report', r => {r.method_followups.sawn_connection_shear_evaluation.sha256 = '0'.repeat(64);}],
]) test(`reject method followup reference ${name}`, () => {
  const index = readPackerFreeIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

test('gross-strip fitting reference reports a required nominal Fy without adopting actual material or strength', () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/fitting-gross-strip-reference.json')));
  const result = validatePackerFreeFittingReference(report, index);
  assert.equal(result.fitting_gross_strip_case_states, 144); assert.equal(result.fitting_gross_strip_section_ends, 2304);
  assert.equal(result.fitting_gross_strip_required_nominal_Fy_MPa, 80.57272595573455);
  assert.equal(result.fitting_gross_strip_actual_Fy_MPa, null); assert.equal(result.fitting_gross_strip_strength_qualified, false);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.source_bindings.analysis_v2_response_bank = i.preceding_revision.response_bank;}],
  ['foreign preparation', r => {r.source_bindings.analysis_v2_prepared_inputs.sha256 = '0'.repeat(64);}],
  ['changed operator snapshot', r => {r.source_bindings.current_fitting_operator_snapshot.sha256 = '0'.repeat(64);}],
  ['incomplete case coverage', r => {r.six_case_result.per_case_maximum_mpa.pop();}],
  ['failed known coupon', r => {r.known_answer_control.passed = false;}],
  ['actual Fy adopted', r => {r.six_case_result.actual_steel_fy = 80.57272595573455;}],
  ['product strength claimed', r => {r.release.physical_fitting_strength = true;}],
  ['fabrication release', r => {r.release.fabrication = true;}],
]) test(`reject gross-strip fitting reference ${name}`, () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/fitting-gross-strip-reference.json')));
  mutate(report, index);
  assert.throws(() => validatePackerFreeFittingReference(report, index));
});

test('additional sawn model references integrate eight reports without changing bearing or optional foot flags', () => {
  const index = readPackerFreeIndex(), result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(Object.keys(index.method_followups).length, 8);
  assert.equal(result.additional_sawn_group_count, 54); assert.equal(result.additional_sawn_case_rows, 324);
  assert.equal(result.additional_sawn_maximum_optional_envelope_ratio, 0.9643026546447111);
  assert.equal(result.additional_sawn_component_acceptance, null);
  assert.equal(result.additional_sawn_complete_joint_qualified, false);
  assert.equal(result.additional_sawn_principal_common_core_exclusions, 0);
  assert.equal(result.additional_sawn_principal_common_core_groups, 2);
  assert.equal(result.additional_sawn_exclusions_are_NDS_violations, false);
  assert.equal(result.additional_sawn_historical_producer_mismatch_disclosed, true);
  assert.equal(result.fitting_gross_strip_case_states, 144); assert.equal(result.fitting_gross_strip_actual_Fy_MPa, null);
  assert.equal(result.reference_case_exceedances, 15); assert.equal(result.optional_rear_foot_envelope_case_rows, 3);
  assert.equal(result.full_ignored_input_closure_checked, false); assert.equal(result.structural_acceptance, false);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {Object.assign(r.current_bindings.six_case_response_bank, i.preceding_revision.response_bank);}],
  ['foreign prepared inputs', r => {r.current_bindings.prepared_inputs.sha256 = '0'.repeat(64);}],
  ['missing replay row', r => {r.fresh_six_case_replay.rows = 299;}],
  ['missing complete cut', r => {r.fresh_six_case_replay.saved_full_cut_wrenches_replayed = 4031;}],
  ['missing event side', r => {r.fresh_six_case_replay.missing_event_sides = 1;}],
  ['post reference count made whole-frame', r => {r.prior_current_receiver_core_qualification.coverage.outer_post_component_references_recalculated = 300;}],
  ['post-only maximum mislabeled', r => {
    const coverage = r.prior_current_receiver_core_qualification.coverage;
    coverage.max_optional_two_edge_envelope_ratio = coverage.max_outer_post_core_optional_two_edge_envelope_ratio;
    delete coverage.max_outer_post_core_optional_two_edge_envelope_ratio;
  }],
  ['beveled post gross width substituted', r => {r.prior_current_receiver_core_qualification.outer_post_core_proof.core_bounds_mm.left_U = [0, 88.9];}],
  ['inscribed depth used as denominator', r => {const core = r.additional_nonrectangular_current_groups.groups[0];
    core.actual_profile_d_mm = core.inscribed_core_d_mm + 0.001;}],
  ['loaded side edge adopted', r => {r.additional_nonrectangular_current_groups.group_maxima[0].loaded_edge = 'positive_v';}],
  ['principal exclusion made violation', r => {r.additional_nonrectangular_current_groups.references.signed_edge_classification = 'NDS violation proven';}],
  ['old false principal exclusions restored', r => {r.additional_nonrectangular_current_groups.principal_center_exclusions =
    [{group: 'base_principal_center_left'}, {group: 'base_principal_center_right'}];}],
  ['principal core witness omitted', r => {r.additional_nonrectangular_current_groups.groups.shift();}],
  ['principal bore fit denied', r => {r.additional_nonrectangular_current_groups.groups[0].all_current_bore_circles_fit = false;}],
  ['incorrect principal near edge', r => {r.additional_nonrectangular_current_groups.groups[0].near_edge_check.center_to_near_q_edge_mm = -8.47671697;}],
  ['ordered-polygon assumption restored', r => {r.additional_nonrectangular_current_groups.current_profile_boundary_proof.vertex_ordering = 'vertices_luv_mm is an ordered boundary';}],
  ['uncorrected source selected', r => {r.additional_nonrectangular_current_groups.source_result.path =
    r.additional_nonrectangular_current_groups.source_result.path.replace('-v5.json', '-v4.json');}],
  ['historical producer discrepancy hidden', r => {r.producer_identity_discrepancy.preserved_raw_claimed_V2_source.sha256 =
    r.producer_identity_discrepancy.currently_available_V2_profile_helper.sha256;}],
  ['separate foot flags erased', r => {r.separate_prior_screens.rear_foot_optional_envelope_flags.flags = [];}],
  ['structural acceptance', r => {r.release.structural_acceptance = true;}],
  ['invalid source digest', r => {r.additional_nonrectangular_current_groups.producer.sha256 = 'invalid';}],
]) test(`reject sawn connection reference ${name}`, () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/sawn-connection-shear-evaluation.json')));
  mutate(report, index);
  assert.throws(() => validatePackerFreeSawnReference(report, index));
});

test('optional center-far-row metadata and dependent action map/group assessment can be absent without changing current112 or selected baseline', () => {
  const index = readPackerFreeIndex(); delete index.unselected_trials; delete index.subassembly_action_map;
  delete index.group_effects_assessment;
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.bolt_axes, 112); assert.equal(result.current_response_revision, index.geometry.revision);
  assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.deepEqual(result.unselected_trials, {});
});

test('unselected center-far-row trial reports108 separately from current112 without a release', () => {
  const index = readPackerFreeIndex(), result = checkCurrentDevelopment(index, {entryChecks: false});
  const trial = result.unselected_trials.center_far_row_only;
  assert.equal(result.bolt_axes, 112); assert.equal(result.current_response_revision, index.geometry.revision);
  assert.equal(result.bearing_diagnostic_case_rows, 15);
  assert.equal(trial.revision, 'v10-packer-free-center-far-row-only-development-v1');
  assert.equal(trial.bolt_axes, 108); assert.equal(trial.occupied_parts, 1105); assert.equal(trial.selected, false);
  assert.equal(trial.bearing_diagnostic_case_rows, 15); assert.equal(trial.bearing_diagnostic_components, 8);
  assert.equal(trial.actual_Cg, null); assert.equal(trial.complete_connection_acceptance, null);
  assert.equal(trial.complete_joint_qualified, false); assert.equal(trial.fabrication_released, false);
  assert.equal(result.full_ignored_input_closure_checked, false);
});

for (const [name, mutate] of [
  ['current112 bank substituted', (e, r, i) => {r.bindings.response_bank = i.response_bank;}],
  ['current112 bank relabeled', (e, r, i) => {r.bindings.response_bank.sha256 = i.response_bank.sha256;}],
  ['erased bearing flag', (e, r) => {r.bearing_diagnostics.flags.pop();}],
  ['duplicate bearing flag', (e, r) => {r.bearing_diagnostics.flags[1] = r.bearing_diagnostics.flags[0];}],
  ['actual Cg adopted', (e, r) => {r.bearing_diagnostics.actual_Cg = 1;}],
  ['actual Cdelta adopted', (e, r) => {r.bearing_diagnostics.actual_Cdelta = 1;}],
  ['trial entry selected', e => {e.selected = true;}],
  ['assessment selected', (e, r) => {r.selected = true;}],
  ['entry fabrication release', e => {e.fabrication_released = true;}],
  ['complete joint qualified', (e, r) => {r.qualifications.complete_joint_qualified = true;}],
  ['assessment purchase authority', (e, r) => {r.qualifications.purchase_authorized = true;}],
  ['nonstandard side stock', (e, r) => {r.geometry.top_and_sides_actual_mm = [88.9, 152.4];}],
  ['wrong bolt count', (e, r) => {r.geometry.counts.bolt_stacks = 112;}],
  ['prior outer removals conflated', (e, r) => {r.geometry.removed_axis_ids.push('v10_top_bolt_001');}],
  ['load multiplier changed', (e, r) => {r.load_contract.downward_multiplier = 1;}],
  ['wrong trial viewer', (e, r, i) => {e.viewer.model = i.geometry.viewer;}],
  ['wrong schema', (e, r) => {r.schema = 'unbound-trial-summary/v1';}],
]) test(`reject unselected center-far-row trial ${name}`, () => {
  const index = readPackerFreeIndex(), entry = index.unselected_trials.center_far_row_only;
  const report = JSON.parse(readFileSync(path.join(ROOT, entry.evaluation.path)));
  const provenance = JSON.parse(readFileSync(path.join(ROOT, entry.viewer.provenance.path)));
  mutate(entry, report, index);
  assert.throws(() => validateUnselectedCenterFarRowTrial(entry, report, provenance));
});

test('local subassembly action map validates declared comparisons while holding load-path and group acceptance', () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.subassembly_action_map.path)));
  assert.equal(validateLocalSubassemblyActionMap(report, index), report);
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.bolt_axes, 112); assert.equal(result.current_response_revision, index.geometry.revision);
  assert.equal(result.unselected_trials.center_far_row_only.bolt_axes, 108);
  assert.equal(result.structural_acceptance, false); assert.equal(result.full_ignored_input_closure_checked, false);
});

test('local subassembly action map and its dependent group assessment can be omitted without changing current authority', () => {
  const index = readPackerFreeIndex(); delete index.subassembly_action_map; delete index.group_effects_assessment;
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.bolt_axes, 112); assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
});

test('portable local subassembly action map checks never open ignored raw sources', () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.subassembly_action_map.path)));
  report.raw_sources.body_graph = {path: 'fea/generated/not-present-for-portable-action-map-control.json', sha256: '0'.repeat(64)};
  assert.equal(validateLocalSubassemblyActionMap(report, index), report);
});

for (const [name, mutate] of [
  ['foreign current bank', r => {r.current_response_bank = r.unselected_response_bank;}],
  ['foreign unselected bank', r => {r.unselected_response_bank = r.current_response_bank;}],
  ['wrong current revision', r => {r.current_revision = r.unselected_revision;}],
  ['wrong shaft inventory', r => {r.counts.selected112.shafts = 108;}],
  ['wrong component inventory', r => {r.counts.current108.components = 29;}],
  ['review scopes substituted for graph components', r => {r.counts.selected112.components = 26;}],
  ['lower cleat pin omitted', r => {r.cleat_components[0].cleat_axis_ids.shift();}],
  ['header pin omitted from connected component', r => {r.cleat_components[0].all_component_axis_ids.pop();}],
  ['header angle detached', r => {r.cleat_components[0].fitting_body_ids.pop();}],
  ['omitted critical scope', r => {r.critical_bearing_diagnostic_scopes.pop();}],
  ['duplicated scope identity', r => {r.critical_bearing_diagnostic_scopes[1].scope_id = r.critical_bearing_diagnostic_scopes[0].scope_id;}],
  ['wrong physical mapping with same aggregate axes', r => {const rows = r.critical_bearing_diagnostic_scopes;
    [rows[0].axes[1], rows[1].axes[1]] = [rows[1].axes[1], rows[0].axes[1]];}],
  ['erased current diagnostic rows', r => {r.critical_bearing_diagnostic_scopes[0].current_case_rows = 0;}],
  ['erased unselected diagnostic rows', r => {r.critical_bearing_diagnostic_scopes[0].unselected_case_rows = 0;}],
  ['invented joint utilization', r => {r.critical_bearing_diagnostic_scopes[0].complete_joint_utilization = 0.5;}],
  ['invented NDS group', r => {r.critical_bearing_diagnostic_scopes[0].NDS_group_assignment = 'qualified-group';}],
  ['actual Cg adopted', r => {r.qualification.actual_Cg = 1;}],
  ['complete load path claimed', r => {r.qualification.complete_load_path_established = true;}],
  ['fabrication release', r => {r.qualification.fabrication_released = true;}],
  ['relaxed force gate', r => {r.gates.force_N = 1e-3;}],
  ['relaxed moment gate', r => {r.gates.moment_Nmm = 1;}],
  ['failed declared residual', r => {r.closure.selected112.max_component_actual_equilibrium_residual_N = 1e-3;}],
  ['failed actual moment hidden by tiny reconstruction error', r => {r.closure.unselected108.max_component_actual_equilibrium_residual_Nmm = 1;}],
  ['missing origin correction', r => {r.residual_origin.unselected108_V2_overlay_required = false;}],
  ['malformed raw binding', r => {r.raw_sources.body_graph.sha256 = 'invalid';}],
  ['authority changed', r => {r.selected_authority_or_viewer_changed = true;}],
]) test(`reject local subassembly action map ${name}`, () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.subassembly_action_map.path)));
  mutate(report);
  assert.throws(() => validateLocalSubassemblyActionMap(report, index));
});

for (const [name, mutate] of [
  ['changed public source', r => {r.subassembly_action_map.sha256 = '0'.repeat(64);}],
  ['missing referenced trial', r => {delete r.unselected_trials;}],
]) test(`reject local subassembly action map authority ${name}`, () => {
  const index = readPackerFreeIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

test('current112 hardware planning binds the issued nominal table and CSV without granting physical fit', () => {
  const index = readPackerFreeIndex();
  const plan = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.json')));
  assert.equal(validateCurrent112HardwarePlanning(plan, index), plan);
  assert.deepEqual(plan.totals, {bolt: 112, nut: 112, spacer: 40, washer: 224});
  assert.equal(plan.physical_fit_qualified, false); assert.equal(plan.purchase_authorized, false);
});

for (const [name, mutate] of [
  ['foreign bank', (p, i) => {p.source_bindings.response_bank = i.preceding_revision.response_bank;}],
  ['fabrication release', p => {p.fabrication_released = true;}],
  ['physical fit claimed', p => {p.physical_fit_qualified = true;}],
  ['invented Actual observation', p => {p.rows[0].Actual = 'inspected';}],
  ['invented Disposition', p => {p.rows[0].Disposition = 'approved';}],
  ['wrong nominal quantity', p => {p.rows[0].nominal_quantity += 1;}],
  ['unresolved spacer SKU', p => {p.rows.find(row => row.category === 'spacer').SKU = 'unresolved';}],
  ['price or availability claim', p => {p.prices_or_availability_claimed = true;}],
]) test(`reject current112 hardware planning ${name}`, () => {
  const index = readPackerFreeIndex();
  const plan = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.json')));
  mutate(plan, index);
  assert.throws(() => validateCurrent112HardwarePlanning(plan, index));
});

for (const rebound of [false, true]) test(`reject current112 hardware planning corrupt CSV ${rebound ? 'with updated hash' : 'with issued hash'}`, () => {
  const index = readPackerFreeIndex();
  const plan = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.json')));
  const issued = readFileSync(path.join(ROOT, plan.CSV.path));
  const changed = Buffer.from(issued.toString('utf8').replace('bolt,363,48,', 'bolt,363,49,'));
  assert.notDeepEqual(changed, issued);
  if (rebound) plan.CSV.sha256 = createHash('sha256').update(changed).digest('hex');
  assert.throws(() => validateCurrent112HardwarePlanning(plan, index, changed), rebound ? /rows differ/ : /CSV hash differs/);
});

test('optional current112 hardware planning binds its public JSON and can be absent without changing authority', () => {
  const index = readPackerFreeIndex();
  const planPath = 'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.json';
  index.hardware_planning = {path: planPath, sha256: createHash('sha256').update(readFileSync(path.join(ROOT, planPath))).digest('hex')};
  assert.equal(checkCurrentDevelopment(index, {entryChecks: false}).bolt_axes, 112);
  index.hardware_planning.sha256 = '0'.repeat(64);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
  delete index.hardware_planning;
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.bolt_axes, 112); assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.equal(result.purchase_authorized, false); assert.equal(result.full_ignored_input_closure_checked, false);
});

test('current112 group effects retain unresolved scopes and a synthetic benchmark without opening ignored declarations', () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/group-effects-assessment.json')));
  report.raw_assessment.path = 'fea/generated/portable-guard-does-not-read/assessment.json';
  report.producer.path = '/unavailable/source-snapshot/publish_summary.py';
  assert.equal(validateCurrent112GroupEffects(report, index), report);
  assert.equal(report.active_group_assessment.candidate_Cg, null);
  assert.equal(report.active_group_assessment.accepted_capacity_exceedance_count, null);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.response_bank = i.preceding_revision.response_bank;}],
  ['invented actual Cg', r => {r.review_scopes[0].actual_Cg = 1;}],
  ['default candidate Cg', r => {r.active_group_assessment.candidate_Cg = 1;}],
  ['legacy acceptance criterion', r => {r.legacy_diagnostics.acceptance_criterion = true;}],
  ['erased legacy flags', r => {r.legacy_diagnostics.rows = 0;}],
  ['duplicated physical axis', r => {r.review_scopes[0].axis_ids[0] = r.review_scopes[0].axis_ids[1];}],
  ['promoted scope capacity', r => {r.review_scopes[0].capacity = 1000;}],
  ['fabrication release', r => {r.qualifications.fabrication_released = true;}],
  ['missing current operator proof', r => {delete r.current112_operator_reuse_proof;}],
  ['missing referenced ownership authority', (r, i) => {delete i.subassembly_action_map;}],
  ['synthetic distribution changed', r => {r.serial_row_benchmark.result.serial_row_distribution.bolt_force_fractions[0] += 0.1;}],
  ['zero accepted exceedances', r => {r.active_group_assessment.accepted_capacity_exceedance_count = 0;}],
]) test(`reject current112 group effects ${name}`, () => {
  const index = readPackerFreeIndex();
  const report = JSON.parse(readFileSync(path.join(ROOT,
    'docs/bolted-frame-development/owner-frame-v10/packer-free/group-effects-assessment.json')));
  mutate(report, index);
  assert.throws(() => validateCurrent112GroupEffects(report, index));
});

test('optional current112 group effects bind the public summary and preserve authority when absent', () => {
  const index = readPackerFreeIndex();
  const summaryPath = 'docs/bolted-frame-development/owner-frame-v10/packer-free/group-effects-assessment.json';
  index.group_effects_assessment = {path: summaryPath, sha256: createHash('sha256').update(readFileSync(path.join(ROOT, summaryPath))).digest('hex')};
  assert.equal(checkCurrentDevelopment(index, {entryChecks: false}).bolt_axes, 112);
  index.group_effects_assessment.sha256 = '0'.repeat(64);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
  delete index.group_effects_assessment;
  const result = checkCurrentDevelopment(index, {entryChecks: false});
  assert.equal(result.bolt_axes, 112); assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.equal(result.reference_case_exceedances, 15); assert.equal(result.optional_rear_foot_envelope_case_rows, 3);
  assert.equal(result.complete_connection_acceptance, null); assert.equal(result.structural_acceptance, false);
  assert.equal(result.full_ignored_input_closure_checked, false);
});
for (const [name, target, mutate] of [
  ['fabrication release', 'index', (r) => {r.fabrication_released = true;}],
  ['baseline promotion', 'index', (r) => {r.selected_baseline.candidate = r.evidence_candidate;}],
  ['missing previous development', 'index', (r) => {r.preceding_revision.schema = 'old';}],
  ['build selection', 'index', (r) => {r.hardware_model.selected_for_build = true;}],
  ['owner selection changes the chosen revision', 'index', r => {r.development_selection.revision = r.geometry.revision;}],
  ['owner selection uses an older force bank', 'index', r => {r.development_selection.response_bank = r.response_bank;}],
  ['owner selection removes current diagnostic rows', 'index', r => {r.development_selection.retained_bearing_diagnostic_case_rows = 0;}],
  ['owner selection approves other member stock', 'index', r => {r.development_selection.other_nonstandard_member_stock_approved = true;}],
  ['owner selection authorizes purchasing', 'index', r => {r.development_selection.purchase_authorized = true;}],
  ['owner record becomes fabrication release', 'ownerDecision', r => {r.fabrication_released = true;}],
  ['released instructions', 'index', (r) => {r.shop.instructions_current_for_fabrication = true;}],
  ['older shop route', 'index', r => {r.shop.packet = 'docs/bolted-frame-development/owner-frame-v9/layout.md';}],
  ['wrong geometry count', 'geometry', r => {r.counts.bolt_stacks = 96;}],
  ['fabricated observations', 'geometry', r => {r.actual_observations = {checked: true};}],
  ['complete joint qualification', 'geometry', r => {r.complete_joint_qualified = true;}],
  ['missing current axis', 'rawGeometry', r => {r.axes.pop();}],
  ['clearance promoted to strength', 'clearance', r => {r.strength_qualified = true;}],
  ['lower load multiplier', 'bank', r => {r.load_contract.downward_multiplier = 1;}],
  ['partial force bank', 'bank', r => {r.cases.pop();}],
  ['duplicate force case', 'bank', r => {r.cases[1] = r.cases[0];}],
  ['relaxed equilibrium gate', 'bank', r => {r.admission_gate_N = 1e-4;}],
  ['foreign force field route', 'bank', r => {r.cases[0].field.path = r.cases[0].field.path.replace('analysis-attempt-08', 'analysis-attempt-06');}],
  ['foreign own-field hash', 'review', r => {r.field_bindings['a1-rear'].sha256 = '0'.repeat(64);}],
  ['all references claimed below one', 'review', r => {r.all_declared_numerical_references_below_one = true;}],
  ['nonfinite reference maximum', 'review', r => {r.numerical_reference_maxima.direct_elastic_steel.index = NaN;}],
  ['changed maximum disposition', 'review', r => {r.numerical_reference_maxima.wood_bearing_whole_affine.above_reference = false;}],
  ['credited complete geometry factor', 'review', r => {r.numerical_reference_maxima.wood_bearing_whole_affine.complete_Cdelta = 1;}],
  ['empty trial census', 'inventory', r => {r.above_reference_case_rows = [];}],
  ['omitted nonworst trial flag', 'inventory', r => {r.above_reference_case_rows[1] = r.above_reference_case_rows[0];}],
  ['trial criterion renamed', 'inventory', r => {r.above_reference_case_rows[0].criterion = 'qualified_failure';}],
  ['trial arithmetic changed', 'inventory', r => {r.above_reference_case_rows[0].individual_reference_before_Cg *= 2;}],
  ['missing component maximum', 'inventory', r => {r.component_maxima.pop();}],
  ['omitted delivery flag', 'delivery', r => {r.remaining_numerical_exceedances.pop();}],
  ['omitted validation flag', 'validation', r => {r.remaining_numerical_exceedances.pop();}],
  ['changed credited wall', 'readiness', r => {r.credited_aggregate_wall_mm = 25.4;}],
  ['missing canonical proof', 'jointBank', r => {r.verified_case_proof_files.pop();}],
  ['duplicate canonical proof', 'jointBank', r => {r.verified_case_proof_files[1] = r.verified_case_proof_files[0];}],
  ['actual Cg adopted', 'paper', r => {r.actual_Cg_adopted = 1;}],
  ['actual Cdelta adopted', 'paper', r => {r.actual_Cdelta_adopted = 1;}],
  ['missing original flag preservation', 'paper', r => {r.old_case_flags_preserved = false;}],
  ['near-edge net reversal invented', 'edgeCorrection', r => {r.net_actions_toward_near_edge_all_cases = true;}],
  ['optional envelope declared a code violation', 'edgeCorrection', r => {r.established_NDS_near_edge_violation = true;}],
  ['optional both-edges envelope made mandatory', 'edgeCorrection', r => {r.fourD_both_edges_is_optional_conservative_envelope = false;}],
  ['corrected idealized screen erased', 'edgeCorrection', r => {r.idealized_resultant_edge_screen_clears = false;}],
  ['oblique eccentric splitting qualification invented', 'edgeCorrection', r => {r.complete_oblique_eccentric_splitting_qualified = true;}],
  ['correction completion points to a different record', 'correctedCompletion', r => {r.read_first_correction.sha256 = '0'.repeat(64);}],
  ['missing component disposition', 'group', r => {r.per_component_dispositions.pop();}],
  ['trial disposition changed', 'group', r => {r.per_component_dispositions[0].worst_trial.index *= .5;}],
  ['trial group diagnostic removed', 'group', r => {r.double_counting.diagnostic_1_over_n_removed = true;}],
  ['qualified complete group', 'groupSeal', r => {r.complete_group_action_qualified = true;}],
  ['method audit component witness changed', 'method', r => {r.current_above_one_component_rows[0].index *= 2;}],
  ['nested joint qualification', 'joint', r => {r.review.complete_geometry_factor_qualified = true;}],
  ['continuation erases a retained flag', 'continuation', r => {r.trial_flags_retained = 0;}],
  ['continuation substitutes another force bank', 'continuation', r => {r.response_bank.sha256 = '0'.repeat(64);}],
  ['continuation adopts a group factor', 'continuation', r => {r.actual_Cg_adopted = 1;}],
  ['continuation claims full criterion resolution', 'continuation', r => {r.all_applicable_connection_criteria_resolved = true;}],
  ['changed stock inherits Candidate13 result', 'standardTopStock', r => {r.candidate13_section_result_transferred = true;}],
  ['partial stock bank claims six-case pass', 'standardTopStock', r => {r.first_option.evaluated_cases[0].complete_six_case_pass = true;}],
  ['old top result substitutes for fresh rejection', 'standardTopStock', r => {r.first_option.evaluated_cases[0].metric_values.shear_torsion_reference_upper = 0.931579767;}],
  ['fresh stock bank drops a case', 'stockRecords', r => {r.bank.cases.pop();}],
  ['fresh stock bank changes load multiplier', 'stockRecords', r => {r.bank.load_contract.downward_multiplier = 1;}],
  ['fresh stock review substitutes old field geometry', 'stockRecords', r => {r.review.analysis_geometry.sha256 = '0'.repeat(64);}],
  ['fresh stock inventory hides a trial flag', 'stockRecords', r => {r.inventory.above_reference_case_rows.pop();}],
  ['force-only stock subcheck claims whole group capacity', 'standardTopStock', r => {r.fallback.connection_method_summary.complete_group_capacity = 1;}],
  ['stock net-away finding claims normative edge clearance', 'standardTopStock', r => {r.fallback.connection_method_summary.NDS_edge_pass_or_violation_established = true;}],
  ['catalog envelope sensitivity transfers strength', 'standardTopStock', r => {r.fallback.catalog_audit.catalog_maximum_clearance_sensitivity.force_or_strength_result_transferred = true;}],
  ['bearing subpath comparison adopts actual group factor', 'standardTopStock', r => {r.fallback.group_slip_method_assessment.actual_Cg_assigned = 1;}],
  ['rear sufficient bound claims physical failure', 'standardTopStock', r => {r.fallback.rear_full_wrench_reference.physical_failure_established = true;}],
  ['active connection assessment uses signature penalty for acceptance', 'activeConnectionCriteria', r => {r.legacy_signature_1_over_n_used_for_acceptance = true;}],
  ['conditional row comparison adopts an actual connection factor', 'groupRowComparison', r => {r.conditional_scenarios[0].actual_connection_Cg = r.conditional_scenarios[0].Cg;}],
  ['active connection assessment discards free couples', 'activeConnectionCriteria', r => {r.moments_omitted = true;}],
  ['cleat three-media factor becomes a two-member factor', 'activeConnectionCriteria', r => {r.upper_cleat_three_media_Cg = 1;}],
  ['unknown physical row becomes a passing connection', 'activeConnectionCriteria', r => {r.flagged_component_dispositions[0].status = 'PASS';}],
  ['active group method lowers horizontal load', 'activeConnectionCriteria', r => {r.load_contract.horizontal_force_N = 0;}],
  ['wrong scene population', 'scene', r => {r.part_count = 1021;}],
  ['historical strength transferred', 'scene', r => {r.historical_capacity_transferred = true;}],
]) test(`reject Candidate13 ${name}`, () => {
  const index = target === 'index' ? structuredClone(candidate13Index) : candidate13Index;
  const data = target === 'index' ? candidate13 : {...candidate13, [target]: structuredClone(candidate13[target])};
  mutate(target === 'index' ? index : data[target]);
  assert.throws(() => validateV10Candidate13Authority(index, data));
});


function fittingProbeAxes() {
  return new Map([[0, 0, 0], [2, 0, 0], [0, 4, 0], [2, 4, 0]].map((point, i) =>
    [`bolt_${i}`, {point_xyz_mm: [900+i, 0, 0],
      attachments: [{angle_id: 'eoere_clip_single_top_left_1', point,
        receiver: i < 2 ? 'base_rail_top' : 'base_side_left', direction: i < 2 ? [0, 0, 1] : [1, 0, 0]}]}]));
}

test('physical fitting probe centroid uses all four hole centers and ignores bolt head origins', () => {
  const axes = fittingProbeAxes();
  const expected = {axes: ['bolt_0', 'bolt_1', 'bolt_2', 'bolt_3'], point: [1, 2, 0],
    directions: {top: [1, 0, 0], side: [0, 0, 1], normal: [0, -1, 0]}};
  assert.deepEqual(currentFittingProbeGeometry(axes, 'eoere_clip_single_top_left_1'), expected);
  for (const axis of axes.values()) axis.point_xyz_mm = [-999, 0, 0];
  assert.deepEqual(currentFittingProbeGeometry(axes, 'eoere_clip_single_top_left_1'), expected);
});

test('physical fitting probe axes retain reversed attachment signs and recorded direction roundoff', () => {
  const axes = fittingProbeAxes();
  const expected = currentFittingProbeGeometry(axes, 'eoere_clip_single_top_left_1');
  axes.get('bolt_0').attachments[0].direction = [0, 0, 1+5e-10];
  for (const name of ['bolt_1', 'bolt_3']) {
    const attachment = axes.get(name).attachments[0];
    attachment.direction = attachment.direction.map(value => -value);
  }
  assert.deepEqual(currentFittingProbeGeometry(axes, 'eoere_clip_single_top_left_1'), expected);
});

for (const [name, mutate, fitting = 'eoere_clip_single_top_left_1'] of [
  ['unknown fitting', () => {}, 'unknown-fitting'],
  ['missing physical hole', axes => {axes.delete('bolt_3');}],
  ['duplicate attachment on one bolt', axes => {axes.get('bolt_0').attachments.push(axes.get('bolt_0').attachments[0]);}],
  ['coincident hole centers', axes => {axes.get('bolt_1').attachments[0].point = [0, 0, 0];}],
  ['malformed hole center', axes => {axes.get('bolt_0').attachments[0].point = [0, 0];}],
  ['nonfinite hole center', axes => {axes.get('bolt_0').attachments[0].point[0] = NaN;}],
  ['unknown receiver', axes => {axes.get('bolt_0').attachments[0].receiver = 'base_header';}],
  ['wrong receiver population', axes => {axes.get('bolt_2').attachments[0].receiver = 'base_rail_top';}],
  ['malformed attachment direction', axes => {axes.get('bolt_0').attachments[0].direction = [0, 1];}],
  ['nonfinite attachment direction', axes => {axes.get('bolt_0').attachments[0].direction = [0, 0, NaN];}],
  ['nonunit attachment direction', axes => {axes.get('bolt_0').attachments[0].direction = [0, 0, 2];}],
  ['inconsistent receiver axes', axes => {axes.get('bolt_1').attachments[0].direction = [0, 1, 0];}],
  ['unsupported corner axis arrangement', axes => {
    for (const name of ['bolt_2', 'bolt_3']) axes.get(name).attachments[0].direction = [0, 0, 1];
  }],
]) test(`reject physical fitting probe ${name}`, () => {
  const axes = fittingProbeAxes();
  mutate(axes);
  assert.throws(() => currentFittingProbeGeometry(axes, fitting));
});

// Exercise current public contracts only where that report schema exists.
for (const revision of ['eoere-inward-bolts-and-angles-v8', 'eoere-single-spacer-cleat-stacks-v9']) {
  const index = ownRevision(revision);
  if (!index.engineering_review) continue;
  const reference = JSON.parse(readFileSync(path.join(ROOT, index.engineering_review.path)));
  if (reference.schema !== 'eoere_current_conventional_reference_review/v1') continue;
  const label = revision.endsWith('v9') ? 'v9' : 'v8';
  test(`${label} conventional reference report retains its own public evidence`, () => {
    validateCurrentConventionalReferenceReview(reference, index);
  });
  for (const [name, mutate] of [
    ['release claims and empty results', r => {
      r.structural_acceptance = r.fabrication_released = r.climbing_released = true;
      r.load_contract.downward_multiplier = .01;
      r.fields = []; r.reference_exceedances = {}; r.shaft_Cg_only_maxima = {};
      r.vector_timber_member_maxima = {};
    }],
    ['structural acceptance', r => {r.structural_acceptance = true;}],
    ['fabrication release', r => {r.fabrication_released = true;}],
    ['climbing release', r => {r.climbing_released = true;}],
    ['invented complete Cdelta', r => {r.complete_joint_Cdelta_established = true;}],
    ['changed load multiplier', r => {r.load_contract.downward_multiplier = .01;}],
    ['duplicate case', r => {r.case_ids[1] = r.case_ids[0];}],
    ['missing own fields', r => {r.fields = [];}],
    ['different own field hash', r => {r.fields[0].sha256 = '0'.repeat(64);}],
    ['foreign analysis', r => {r.analysis_geometry.path = r.analysis_geometry.path.replace('owner-single-spacer-stacks-v9', 'owner-inward-angles-v8');}],
    ['foreign worksheet', r => {r.source_bindings.timber_vector.path = r.source_bindings.timber_vector.path.replace('owner-single-spacer-stacks-v9', 'owner-inward-angles-v8');}],
    ['malformed worksheet binding', r => {r.source_bindings.timber_cores.sha256 = 'unknown';}],
    ['empty shaft maxima', r => {r.shaft_Cg_only_maxima = {};}],
    ['nonfinite shaft maximum', r => {r.shaft_Cg_only_maxima.maximum_N_M_index_before_Cdelta.index = NaN;}],
    ['foreign shaft witness', r => {r.shaft_Cg_only_maxima.maximum_N_M_index_before_Cdelta.axis = 'not-a-current-bolt';}],
    ['credited shaft geometry factor', r => {r.shaft_Cg_only_maxima.maximum_N_M_index_before_Cdelta.complete_joint_Cdelta = 1;}],
    ['missing timber member', r => {delete r.vector_timber_member_maxima.base_header;}],
    ['nonfinite member maximum', r => {r.vector_timber_member_maxima.base_header.maximum_normal_reference_upper.index = Infinity;}],
    ['changed interval witness', r => {r.vector_timber_member_maxima.base_header.maximum_normal_reference_upper.worst_interval.normal_reference_upper *= .5;}],
    ['missing case maximum', r => {delete r.timber_maxima.timber_vector.maximum_normal_reference_upper.by_case['a1-rear'];}],
    ['understated whole maximum', r => {r.timber_maxima.timber_vector.maximum_shear_torsion_reference_upper.overall.index = .5;}],
    ['empty exceedance disclosures', r => {r.reference_exceedances = {};}],
    ['omitted shaft maximum exceedance', r => {r.reference_exceedances.shaft_Cg_only = [];}],
    ['duplicate shaft exceedance', r => {r.reference_exceedances.shaft_Cg_only.push(r.reference_exceedances.shaft_Cg_only[0]);}],
    ['nonexceeding disclosure', r => {r.reference_exceedances.shaft_Cg_only[0].index = 1;}],
    ['omitted case timber maximum exceedance', r => {r.reference_exceedances.timber_vector.shift();}],
    ['false cleat exceedance', r => {r.reference_exceedances.cleat_nominal = [{...r.cleat_maxima.cleat_nominal, index: 2}];}],
  ]) test(`reject ${label} conventional reference ${name}`, () => {
    const report = structuredClone(reference);
    mutate(report);
    assert.throws(() => validateCurrentConventionalReferenceReview(report, index));
  });
  test(`${label} compact references do not certify omitted nonworst raw results`, () => {
    const report = structuredClone(reference);
    // Keep the published maxima; an absent nonworst row needs the raw audit.
    report.reference_exceedances.shaft_Cg_only = Object.values(report.shaft_Cg_only_maxima)
      .filter(row => row.index > 1).map(row => structuredClone(row));
    validateCurrentConventionalReferenceReview(report, index);
  });

  if (!index.panel_bracing_review) continue;
  const bracing = JSON.parse(readFileSync(path.join(ROOT, index.panel_bracing_review.path)));
  if (bracing.schema !== 'eoere_current_panel_bracing_summary/v1') continue;
  test(`${label} current bracing report retains every public probe`, () => {
    const report = structuredClone(bracing);
    report.probes.reverse();
    validateCurrentPanelBracingSummary(report, index);
  });
  test(`${label} current bracing probe allows coordinate roundoff within 1e-7 mm`, () => {
    const report = structuredClone(bracing);
    for (const row of report.probes) row.point_xyz_mm[0] += 5e-8;
    for (const ranges of Object.values(report.all_six_case_ranges))
      for (const witness of Object.values(ranges)) witness.point_xyz_mm[0] += 5e-8;
    validateCurrentPanelBracingSummary(report, index);
  });
  test(`${label} current bracing allows parallel probe sign reversal`, () => {
    const report = structuredClone(bracing);
    for (const row of report.probes) row.direction_xyz = row.direction_xyz.map(value => -value);
    for (const ranges of Object.values(report.all_six_case_ranges))
      for (const witness of Object.values(ranges)) witness.direction_xyz = witness.direction_xyz.map(value => -value);
    validateCurrentPanelBracingSummary(report, index);
  });
  for (const mode of ['top_grain_compression', 'side_grain_compression', 'panel_normal_translation',
    'top_grain_torsion', 'side_grain_torsion', 'in_plane_corner_rotation'])
    test(`reject ${label} current bracing wrong unit direction for ${mode}`, () => {
      const report = structuredClone(bracing);
      const probe = report.probes.find(row => row.mode === mode &&
        !Object.values(report.all_six_case_ranges[mode]).some(witness =>
          witness.case_id === row.case_id && witness.corner === row.corner));
      assert.ok(probe, 'fixture needs a non-extreme mode probe');
      probe.direction_xyz = mode.startsWith('top_grain') ? [0, 1, 0] : [1, 0, 0];
      assert.throws(() => validateCurrentPanelBracingSummary(report, index));
    });
  for (const [name, mutate] of [
    ['structural acceptance', r => {r.structural_acceptance = true;}],
    ['fabrication release', r => {r.fabrication_released = true;}],
    ['climbing release', r => {r.climbing_released = true;}],
    ['strength multiplier', r => {r.strength_gain_factor = 2;}],
    ['double strength credit', r => {r.double_strength_credit_applied = true;}],
    ['qualified Hillman law', r => {r.model_assumptions.physical_Hillman_law_qualified = true;}],
    ['changed screw stiffness', r => {r.model_assumptions.Hillman_lateral_N_per_mm = 2000;}],
    ['missing probe', r => {r.probes.pop();}],
    ['duplicate probe', r => {r.probes[1] = r.probes[0];}],
    ['unknown probe mode', r => {r.probes[0].mode = 'strength';}],
    ['zero stiffness', r => {r.probes[0].without_panels_stiffness = 0;}],
    ['nonfinite stiffness', r => {r.probes[0].with_panels_stiffness = Infinity;}],
    ['wrong ratio', r => {r.probes[0].modeled_stiffness_ratio *= 2;}],
    ['foreign probe case', r => {r.probes[0].case_id = 'old-case';}],
    ['foreign corner axes', r => {r.probes[0].joint_axis_ids[0] = 'eoere_bolt_067';}],
    ['non-extreme probe moved to origin', r => {
      const probe = r.probes.find(row => !Object.values(r.all_six_case_ranges[row.mode]).some(witness =>
        witness.case_id === row.case_id && witness.corner === row.corner));
      assert.ok(probe, 'fixture needs a probe outside the displayed range extrema');
      probe.point_xyz_mm = [0, 0, 0];
    }],
    ['all probe points and range witnesses moved to origin', r => {
      for (const row of r.probes) row.point_xyz_mm = [0, 0, 0];
      for (const ranges of Object.values(r.all_six_case_ranges))
        for (const witness of Object.values(ranges)) witness.point_xyz_mm = [0, 0, 0];
    }],
    ['foreign raw result', r => {r.source_bindings.raw_result.path = r.source_bindings.raw_result.path.replace('owner-single-spacer-stacks-v9', 'owner-inward-angles-v8');}],
    ['wrong reference review', r => {r.source_bindings.reference_review.sha256 = '0'.repeat(64);}],
    ['mixed range witness', r => {r.all_six_case_ranges.top_grain_torsion.maximum.with_panels_stiffness *= 2;}],
    ['false range maximum', r => {r.all_six_case_ranges.top_grain_torsion.maximum = r.all_six_case_ranges.top_grain_torsion.minimum;}],
    ['missing mode range', r => {delete r.all_six_case_ranges.top_grain_torsion;}],
    ['failed equilibrium gate', r => {r.numerical_checks.maximum_relative_equilibrium_error = 1e-4;}],
  ]) test(`reject ${label} current bracing ${name}`, () => {
    const report = structuredClone(bracing);
    mutate(report);
    assert.throws(() => validateCurrentPanelBracingSummary(report, index));
  });
  for (const [name, mutate] of [
    ['reference report replaced by bracing summary', i => {i.engineering_review = i.panel_bracing_review;}],
    ['bracing summary replaced by reference report', i => {i.panel_bracing_review = i.engineering_review;}],
  ]) test(`current development validates ${label} ${name}`, () => {
    const changed = structuredClone(index);
    mutate(changed);
    assert.throws(() => checkCurrentDevelopment(changed, {entryChecks: false}));
  });
}

for (const [label, mutate] of [
  ['geometry factor credited', r => {r.formal_geometry_Cdelta = 1;}],
  ['legacy adjusted capacity imported', r => {r.base_input_manifest.legacy_screen_adjusted_indices = {axial_bending: 0.5};}],
  ['unresolved neighbor accepted', r => {r.additional_same_host_pairs[0].complete_joint_qualified = true;}],
  ['older field route relabeled', r => {
    const row = r.case_summaries[0];
    row.field.path = row.field.path.replace('owner-inward-angles-v8', 'owner-principal-pairs-v6');
    r.source_bindings.fields_and_replays[row.case_id].field = row.field;
  }],
]) test(`reject own-field geometry review ${label}`, () => {
  const index = ownRevision('eoere-inward-bolts-and-angles-v8');
  const report = JSON.parse(readFileSync(path.join(ROOT, index.bolt_geometry_review.path)));
  mutate(report);
  assert.throws(() => validateCurrentBoltGeometryReview(report, index));
});

for (const [label, mutate] of [
  ['relaxed equilibrium gate', r => {r.admission_gate_N = 1e-4;}],
  ['partial case population', r => {r.cases.pop();}],
  ['different downward multiplier', r => {r.load_contract.downward_multiplier = 2.5;}],
  ['convergence promoted to acceptance', r => {r.structural_acceptance = true;}],
]) test(`reject own response bank ${label}`, () => {
  const index = ownRevision('eoere-inward-bolts-and-angles-v8');
  const report = JSON.parse(readFileSync(path.join(ROOT, index.response_bank.path)));
  mutate(report);
  assert.throws(() => validateOwnResponseBank(report, index));
});

test('current geometry/shop, preceding response and baseline keep their own identities', () => {
  assert.equal(checkCurrentDevelopment().passed, true);
});

test('owner revision cannot inherit the removed-return frame acceptance', () => {
  const index = readCurrentIndex();
  index.conditional_frame_evaluation = ownRevision('eoere-paired-frame-retained-2x6-A574-v2').conditional_frame_evaluation;
  assert.throws(() => checkCurrentDevelopment(index));
});

for (const [label, mutate] of [
  ['unrelated cleat part moved', scene => {scene.replacements[0].name = 'eoere_cleat_left';}],
  ['foreign parent', scene => {scene.parent_layout.sha256 = '0'.repeat(64);}],
  ['front move claims acceptance', scene => {scene.complete_conditional_frame_evaluation = true;}],
]) test(`reject local front revision ${label}`, () => {
  const index = ownRevision('eoere-local-front-bolt-moves-v4');
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateOwnerFrame(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['second upper shaft missing', scene => {scene.replacements = scene.replacements.filter(r => r.name !== 'eoere_bolt_067_shaft');}],
  ['second upper stack borrows the first connection identity', scene => {scene.replacements.find(r => r.name === 'eoere_bolt_070_nut').fabrication.connection_name = 'eoere_bolt_074';}],
  ['preceding strength transferred', scene => {scene.complete_conditional_frame_evaluation = true;}],
  ['panel screw count changed', scene => {scene.counts.Hillman_axes = 68;}],
  ['unrelated geometry included', scene => {scene.replacements[0].name = 'base_header';}],
]) test(`reject reference cleat revision ${label}`, () => {
  const index = ownRevision('eoere-reference-cleat-upper-pair-v5');
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateReferenceCleats(scene, index.geometry.receipt.sha256));
});

test('restored cleats cannot inherit a preceding strength review', () => {
  const index = read96Index();
  index.engineering_review = ownRevision('eoere-local-front-bolt-moves-v4').engineering_review;
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [label, mutate] of [
  ['different load weight', r => {r.load_contract.input_weight = 175;}],
  ['restored pins omitted', r => {r.inventory.current_bolts = 92;}],
  ['complete joint acceptance', r => {r.qualification.structural_acceptance = true;}],
  ['ineligible geometry treated as passing', r => {r.geometry_eligibility.no_pass_when_geometry_ineligible = false;}],
]) test(`reject current96 review ${label}`, () => {
  const index = read96Index();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.engineering_review.path)));
  mutate(report);
  assert.throws(() => validateCurrent96Review(report, index));
});

for (const [label, mutate] of [
  ['preceding model results', r => {r.geometry_revision = 'eoere-local-front-bolt-moves-v4';}],
  ['different forces', r => {r.analysis_geometry.sha256 = '0'.repeat(64);}],
  ['loaded-edge waiver', r => {r.testing_disposition.geometry_ineligibility_waived = true;}],
  ['force-only row adopted as pass', r => {r.testing_disposition.midface_probe_or_force_only_row_used_as_pass = true;}],
  ['elastic steel reference replaces reduced interaction', r => {r.testing_disposition.reduced_bolt_interaction_replaced_by_elastic_index = true;}],
  ['changed bolt comparison', r => {r.unchanged_reference_maxima.shafts_Cdelta_adjusted.axial_bending_reference_index_after_Cdelta.index = 0.5;}],
  ['filled hole', r => {r.side_core_changes[0].projected_holes_unchanged = false;}],
  ['missing current case', r => {delete r.timber_reference_maxima.maximum_shear_torsion_reference_upper.by_case['a12-rear'];}],
  ['complete frame acceptance', r => {r.qualification.structural_acceptance = true;}],
]) test(`reject current96 testing refinement ${label}`, () => {
  const index = read96Index();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.testing_review.path)));
  mutate(report);
  assert.throws(() => validateCurrent96TestingReview(report, index));
});

test('current development requires the incorporated method review', () => {
  const index = read96Index();
  delete index.testing_review;
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

test('current development requires the corrected bolt rule review', () => {
  const index = read96Index();
  delete index.bolt_geometry_review;
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [label, mutate] of [
  ['unresolved pair promoted to pass', r => {r.affected_pair_measurements[0].rule.status = 'pass';}],
  ['projection substituted for actual spacing', r => {r.affected_pair_measurements[0].rule.actual_spacing_mm = 32.6536;}],
  ['unclassified geometry factor credited', r => {r.formal_geometry_Cdelta = 1;}],
  ['unresolved upper axis marked eligible', r => {r.upper_pair_statuses[0].component_status = 'PASS_COMPONENTS_ONLY';}],
  ['different case field', r => {r.case_summaries[0].field.sha256 = '0'.repeat(64);}],
  ['duplicate upper axis', r => {r.upper_pair_statuses[1] = r.upper_pair_statuses[0];}],
  ['missing pair measurement', r => {r.affected_pair_measurements.pop();}],
  ['different load recipe', r => {r.load_contract.downward_multiplier = 1;}],
  ['changed earlier screen', r => {r.legacy_screen_adjusted_indices_unchanged = {};}],
]) test(`reject bolt geometry review ${label}`, () => {
  const index = read96Index();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.bolt_geometry_review.path)));
  mutate(report);
  assert.throws(() => validateBoltGeometryReview(report, index));
});

for (const [label, mutate] of [
  ['missing shared-host neighbor', r => {r.additional_same_host_pairs.pop();}],
  ['duplicate shared-host neighbor', r => {r.additional_same_host_pairs[1] = r.additional_same_host_pairs[0];}],
  ['neighbor promoted to a joint pass', r => {r.additional_same_host_pairs[0].complete_joint_qualified = true;}],
  ['pair sample with unlabeled loading', r => {delete r.affected_pair_measurements[0].case_id;}],
]) test(`reject corrected same-host census ${label}`, () => {
  const index = read96Index();
  const report = JSON.parse(readFileSync(path.join(ROOT, index.bolt_geometry_review.path)));
  assert.equal(report.schema, 'eoere_current96_bolt_geometry_review/v2');
  mutate(report);
  assert.throws(() => validateBoltGeometryReview(report, index));
});

for (const [label, mutate] of [
  ['missing second center pin', scene => {scene.replacements = scene.replacements.filter(r => r.name !== 'eoere_bolt_068_shaft');}],
  ['tabbed cleat perimeter', scene => {scene.flat_cleat_outline_yz_mm.push([0, 0]);}],
  ['old strength transferred', scene => {scene.complete_conditional_frame_evaluation = true;}],
]) test(`reject center-pair revision ${label}`, () => {
  const index = ownRevision('eoere-flat-cleats-principal-upper-pairs-v6');
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validatePrincipalPairs(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['unreversed outside stack', scene => {scene.transforms.pop();}],
  ['second spacer left outside', scene => {scene.transforms.find(r => r.axis_id === 'eoere_bolt_070').roles.pop();}],
  ['unchanged bolt direction', scene => {scene.transforms[0].rotation_matrix_row_major = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];}],
  ['rotation around the wrong clamped faces', scene => {scene.transforms[0].translation_xyz_mm[0] += 1;}],
  ['strength transferred from exterior nuts', scene => {scene.current_response_computed = true;}],
]) test(`reject inward bolt revision ${label}`, () => {
  const index = ownRevision('eoere-inward-exterior-bolts-v7'), scene = JSON.parse(readFileSync(path.join(ROOT, index.geometry.scene.path)));
  mutate(scene);
  assert.throws(() => validateInwardBolts(scene, index.geometry.receipt.sha256));
});

test('reversed hardware cannot inherit the exterior-nut strength report', () => {
  const index = readCurrentIndex();
  index.engineering_review = read96Index().engineering_review;
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [label, mutate] of [
  ['nut left in its old position', scene => {scene.translations = scene.translations.filter(r => r.name !== 'eoere_bolt_070_nut');}],
  ['second spacer left in its old position', scene => {scene.translations.find(r => r.name === 'eoere_bolt_070_spacer_2').translation_xyz_mm = [0, 0, 0];}],
  ['old receiver bores retained', scene => {scene.replacements.pop();}],
  ['inward hardware parent discarded', scene => {scene.parent_scene.sha256 = '0'.repeat(64);}],
  ['old frame strength transferred', scene => {scene.current_response_computed = true;}],
]) test(`reject cumulative inset-angle revision ${label}`, () => {
  const index = ownRevision('eoere-inward-bolts-and-angles-v8'), scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateInwardAngles(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['unsupported seven-inch substitute', scene => {scene.stack_updates[0].selected_underhead_length_mm = 177.8;}],
  ['weaker bolt grade', scene => {scene.stack_updates[0].selected_bolt_grade = 'SAE J429 Grade 5';}],
  ['extra spacer retained', scene => {scene.stack_updates[0].spacer_piece_count = 2;}],
  ['nut not moved with shorter spacer', scene => {scene.part_transforms.find(r => r.role === 'nut').translation_xyz_mm = [0, 0, 0];}],
  ['wrong shaft length', scene => {scene.part_transforms.find(r => r.role === 'shaft').scale_xyz[0] = .875;}],
  ['receiver removed instead of spacer', scene => {scene.removals[0] = 'base_side_left';}],
  ['old force acceptance transferred', scene => {scene.current_response_computed = true;}],
]) test(`reject single-spacer revision ${label}`, () => {
  const index = ownRevision('eoere-single-spacer-cleat-stacks-v9'), scene = JSON.parse(readFileSync(path.join(ROOT, index.geometry.scene.path)));
  mutate(scene);
  assert.throws(() => validateSingleSpacers(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['missing omitted stack component', scene => {scene.removals.pop();}],
  ['foreign parent receipt', scene => {scene.parent_layout.sha256 = '0'.repeat(64);}],
  ['historical strength transferred', scene => {scene.historical_capacity_transferred = true;}],
]) test(`reject retained-frame ${label}`, () => {
  const index = ownRevision('eoere-paired-frame-retained-2x6-A574-v2');
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateRetainedFrame(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['stale post geometry', i => {i.geometry.revision = i.preceding_revision.geometry.revision;}],
  ['post scene drift', i => {i.geometry.scene.sha256 = '0'.repeat(64);}],
  ['old response transfer to 4x6 posts', i => {i.current_response = i.preceding_revision.current_response;}],
  ['post hardware receipt drift', i => {i.hardware_model.receipt = i.preceding_revision.hardware_model.receipt;}],
  ['post hardware override omission', i => {i.shop.overrides.pop();}],
  ['post physical release', i => {i.fabrication_released = true;}],
]) test(`reject ${label}`, () => {
  const index = readPostIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [label, mutate] of [
  ['second spacer hidden by a duplicate role', p => {p.replacements.find(r => r.name.endsWith('_spacer_2')).fabrication.hardware_role = 'spacer';}],
  ['incomplete advertised stack roles', p => {p.replacements.find(r => r.fabrication.connection_name === 'cleat_post_bolt_left_1').fabrication.stack_roles.pop();}],
]) test(`reject post viewer ${label}`, () => {
  const index = readPostIndex(), scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateFrontPosts(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['stale current revision', i => {i.geometry.revision = i.response.revision;}],
  ['unknown viewer', i => {i.geometry.viewer = 'not-a-model';}],
  ['scene hash drift', i => {i.geometry.scene.sha256 = '0'.repeat(64);}],
  ['response relabel', i => {i.response.revision = i.geometry.revision;}],
  ['response transfer', i => {i.response.applies_to_current_geometry = true;}],
  ['missing shop override', i => {i.shop.overrides = [];}],
  ['stale shop revision', i => {i.shop.revision = i.response.revision;}],
  ['stale shop geometry', i => {i.shop.geometry = i.response.geometry;}],
  ['shop result hash drift', i => {i.shop.result.sha256 = '0'.repeat(64);}],
  ['missing current channel drawings', i => {i.shop.current_channel_drawings_complete = false;}],
  ['shop hardware application missing', i => {i.shop.hardware_model_updated = false;}],
  ['applied hardware binding missing', i => {delete i.hardware_model;}],
  ['applied hardware parent drift', i => {i.hardware_model.wood_screw_geometry = i.response.geometry;}],
  ['hardware response transfer', i => {i.hardware_model.analysis_pass_transferred = true;}],
  ['shop plan relabeled as release', i => {i.shop.shop_planning_only = false;}],
  ['official optional grid', i => {i.optional_grid.official = true;}],
  ['optional viewer aliasing the base', i => {i.optional_grid.viewer = i.geometry.viewer;}],
  ['proposal relabel', i => {i.unadopted_proposal.revision = 'invented-revision';}],
  ['adopted Z180 proposal', i => {i.unadopted_proposal.adopted = true;}],
  ['physical release', i => {i.fabrication_released = true;}],
  ['structural assessment missing', i => {delete i.structural_assessment;}],
  ['structural assessment hash drift', i => {i.structural_assessment.sha256 = '0'.repeat(64);}],
  ['current response missing', i => {delete i.current_response;}],
  ['engineering assessment missing', i => {delete i.engineering_assessment;}],
  ['engineering assessment hash drift', i => {i.engineering_assessment.sha256 = '0'.repeat(64);}],
  ['current response hardware transfer', i => {i.current_response.hardware_model = i.response.geometry;}],
]) test(`reject ${label}`, () => {
  const index = readIndex(); mutate(index);
  assert.throws(() => checkDevelopment(index));
});

for (const [label, mutate] of [
  ['structural acceptance', r => {r.structural_acceptance = true;}],
  ['invented joint capacity', r => {r.complete_joint_resistance = 1;}],
  ['invented bracing', r => {r.member_effective_length_domain[0].actual_effective_length_factor = .5;}],
  ['changed effective length', r => {r.member_effective_length_domain[0].maximum_effective_length_for_l_over_d_50_mm *= 2;}],
  ['missing member domain', r => {r.member_effective_length_domain.pop();}],
  ['wrong model', r => {r.geometry_revision = 'old';}],
  ['wrong producer', r => {r.producer.sha256 = '0'.repeat(64);}],
  ['missing case', r => {r.cases.pop();}],
  ['wrong probe state', r => {r.finite_arm_contact_probe.cases[1].state_id = r.cases[0].state_id;}],
  ['wrong load direction', r => {r.load_checks[0].climber_force_xyz_n[1] *= -1;}],
  ['changed gravity', r => {r.load_checks[0].permanent_and_accessory_weight_n += 1;}],
  ['invented complete load envelope', r => {r.recorded_load_basis.dynamic_spectrum_or_all_hold_direction_envelope_verified = true;}],
  ['invented physical error bound', r => {r.finite_arm_contact_probe.finite_equilibrium_contact_law_or_error_bound = true;}],
  ['invented pressure response', r => {r.finite_arm_contact_probe.cases[0].physical_error_bound_or_response = true;}],
  ['missing contact switches', r => {r.finite_arm_contact_probe.cases[0].strict_open_compressed_class_changes = 0;}],
  ['coordinated contact-switch omission', r => {
    for (const c of r.finite_arm_contact_probe.cases) {
      c.open_to_compressed = c.compressed_to_open = c.strict_open_compressed_class_changes = 0;
      c.largest_gap_change_class_switch = null;
    }
  }],
  ['compressed-to-open census omission', r => {
    for (const c of r.finite_arm_contact_probe.cases) {
      c.compressed_to_open = 0; c.strict_open_compressed_class_changes = c.open_to_compressed;
      if (!c.open_to_compressed) c.largest_gap_change_class_switch = null;
    }
  }],
  ['missing contact scalar', r => {r.finite_arm_contact_probe.cases[0].all_contact_scalars.pop();}],
  ['nonfinite contact scalar', r => {r.finite_arm_contact_probe.cases[0].all_contact_scalars[0][1] = Infinity;}],
  ['wrong witness contact identity', r => {r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change.contact_id = 'foreign';}],
  ['changed gap witness', r => {r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change.gap_change_mm = 0;}],
  ['coherent fabricated gap maximum', r => {
    const w = r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change;
    w.fixed_director_finite_arm_gap_mm = 1; w.gap_change_mm = 1-w.linear_gap_mm; w.surrogate_class = 1;
  }],
  ['missing whole-load moment', r => {delete r.load_checks[0].whole_moment_about_origin_xyz_nmm;}],
  ['finite wrong whole-load moment', r => {r.load_checks[0].whole_moment_about_origin_xyz_nmm[0] += 1e6;}],
  ['zeroed whole-load moments', r => {for (const load of r.load_checks) load.whole_moment_about_origin_xyz_nmm = [0,0,0];}],
  ['zeroed eccentric couples', r => {for (const load of r.load_checks) load.midplane_couple_xyz_nmm = [0,0,0];}],
  ['wrong load point', r => {r.load_checks[0].load_point_xyz_mm = [0,0,0];}],
  ['foreign hold', r => {r.load_checks[0].hold = 'foreign';}],
  ['foreign loaded panel', r => {r.load_checks[0].panel = 'foreign';}],
  ['wrong wrench reference', r => {r.equilibrium_wrench_reference_xyz_mm[0] += 1;}],
  ['missing hold geometry', r => {delete r.recorded_hold_geometry.A12;}],
  ['wrong maximum rotation', r => {r.finite_arm_contact_probe.cases[0].maximum_relative_linear_rotation.relative_linear_rotation_rad = 0;}],
  ['missing active-action count', r => {delete r.active_action_load_path_screen[0].active_action_rows;}],
  ['zero active-action count', r => {r.active_action_load_path_screen[0].active_action_rows = 0;}],
  ['coordinated omitted routing edges', r => {for (const s of r.active_action_load_path_screen) {s.active_action_rows = 0; s.active_edge_census = [];}}],
  ['wrong routing owner census', r => {r.active_action_load_path_screen[0].physical_owner_ids.pop();}],
  ['false disconnected owner', r => {
    const s = r.active_action_load_path_screen[0];
    s.owners_without_active_action_path_to_floor = [s.physical_owner_ids[0]]; s.all_owners_have_active_action_path_to_floor = false;
  }],
  ['connectivity claimed as resistance', r => {r.active_action_load_path_screen[0].directional_restraint_capacity_or_complete_joint_behavior_qualified = true;}],
  ['screw-panel waiver', r => {r.screw_panel_load_path_removed_or_capacity_accepted = true;}],
  ['screw-panel deferral missing', r => {r.screw_panel_exceedance_resolution_deferred_by_owner = false;}],
  ['new unadopted motion threshold', r => {r.small_motion_threshold_adopted = .01;}],
  ['wrong frozen inputs', r => {r.verified_input_unions.pop();}],
]) test(`reject engineering assessment ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.engineering_assessment.path)));
  mutate(report);
  assert.throws(() => validateEngineeringAssessment(report, index));
});

for (const [label, mutate] of [
  ['stale geometry', r => {r.geometry_revision = 'old';}],
  ['stale hardware', r => {r.hardware_revision = 'old';}],
  ['response transfer', r => {r.preceding_reference_comparisons.applies_to_current_model = true;}],
  ['invented capacity', r => {r.thread_stacks[0].current_capacity = 1;}],
  ['false actual observation', r => {r.actual_observations = {};}],
  ['wrong source', r => {r.source_sha256[readIndex().hardware_model.receipt.path] = '0'.repeat(64);}],
  ['wrong producer', r => {r.source_sha256['scripts/eoere_structural_assessment.py'] = '0'.repeat(64);}],
  ['missing exceedances', r => {r.preceding_reference_comparisons.saved_reference_exceedances = [];}],
  ['missing witnesses', r => {r.preceding_reference_comparisons.governing_own_case_witnesses = [];}],
  ['missing case disclosures', r => {r.preceding_reference_comparisons.other_saved_exceedance_and_sensitivity_disclosures.pop();}],
  ['false count summary', r => {r.thread_catalog_envelope_counts = {NOMINAL_SMOOTH_BODY_COVERS_WOOD: 100};}],
  ['wrong quarter threshold', r => {r.thread_method.threshold = .27;}],
  ['missing unresolved mode', r => {r.current_unresolved_modes.pop();}],
  ['duplicated unresolved mode', r => {r.current_unresolved_modes[1] = r.current_unresolved_modes[0];}],
  ['invented spacer resistance', r => {r.spacer_contact.current_resistance = 1000;}],
  ['invented spacer action', r => {r.spacer_contact.current_axial_actions = {uncomputed: 1000};}],
  ['zero spacer contact area', r => {r.spacer_contact.nominal_projection_areas_mm2.spacer_annulus = 0;}],
  ['false spacer unit pressure', r => {r.spacer_contact.mean_pressure_mpa_per_1000n_centered_axial_force.spacer_annulus = 0;}],
  ['missing spacer unit pressure', r => {delete r.spacer_contact.mean_pressure_mpa_per_1000n_centered_axial_force.spacer_annulus;}],
  ...['structural_acceptance', 'native_solve_performed', 'remedies_attempted', 'extra_grid']
    .map(key => [key, r => {r[key] = true;}]),
]) test(`reject structural assessment ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.structural_assessment.path)));
  mutate(report);
  assert.throws(() => validateStructuralAssessment(report, index));
});

for (const [label, mutate] of [
  ['stale geometry', r => {r.geometry = readIndex().response.geometry;}],
  ['stale hardware', r => {r.hardware_revision = 'old';}],
  ['missing case', r => {r.cases.pop();}],
  ['duplicated state', r => {r.cases[1].state_id = r.cases[0].state_id;}],
  ['failed admission', r => {r.cases[0].current_equilibrium_and_recovery_pass = false;}],
  ['residual above gate', r => {r.cases[0].gradient_inf_n = .01;}],
  ['false residual maximum', r => {r.maximum_full_gradient_residual_n = 0;}],
  ['old case path', r => {r.cases[0].field.path = 'old/field.json';}],
  ['missing spacer action', r => {r.cases[0].spacer_nut_capture_actions.pop();}],
  ['unmeasured floor capacity', r => {r.cases[0].floor_support_summary.friction_or_anchor_capacity_established = true;}],
  ['invented panel RHS check', r => {r.cases[0].applied_load_checks.distributed_panel_rhs_independently_regenerated = true;}],
  ['invented joint capacity', r => {r.complete_joint_resistance = 1;}],
  ['invented finished capacity', r => {r.finished_member_capacity = 1;}],
  ['missing release flags', r => {r.release = {};}],
  ['changed force producer', r => {r.force_producer.sha256 = '0'.repeat(64);}],
  ['changed input checker', r => {r.input_checker.sha256 = '0'.repeat(64);}],
  ...['extra_grid', 'native_solve_performed', 'historical_q_forces_or_passes_transferred',
    'remedies_attempted', 'actual_build_fit_work_performed', 'structural_acceptance',
    'physical_demand_bounds_established'].map(key => [key, r => {r[key] = true;}]),
]) test(`reject current force response ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.cases.path)));
  mutate(report);
  assert.throws(() => validateCurrentResponse(report, index));
});

test('incoming descriptions reject a stale revision even when its link resolves', () => {
  const index = readCurrentIndex(), root = readFileSync(path.join(ROOT, 'README.md'), 'utf8');
  const revision = index.development_selection?.revision ?? index.geometry.revision;
  assert.throws(() => validateEntry(root.replaceAll(revision, index.preceding_revision.geometry.revision), index));
  const html = readFileSync(path.join(ROOT, 'site/index.html'), 'utf8');
  assert.equal(viewerModel(html, index.preceding_revision.geometry.revision), index.selected_baseline.candidate);
});

for (const [label, mutate] of [
  ['foreign force packet', r => {r.current_response = r.geometry;}],
  ['foreign geometry', r => {r.geometry = r.hardware_model;}],
  ['foreign state', r => {r.cases[0].state_id = r.cases[1].state_id;}],
  ['foreign field', r => {r.cases[0].field = r.cases[1].field;}],
  ['foreign raw component', r => {r.cases[0].raw_components.path = r.cases[1].raw_components.path;}],
  ['stale component producer', r => {r.component_producer.sha256 = '0'.repeat(64);}],
  ['stale section producer', r => {r.section_producer.sha256 = '0'.repeat(64);}],
  ['stale summary producer', r => {r.summary_producer.sha256 = '0'.repeat(64);}],
  ['missing release', r => {r.release = {};}],
  ['screw product capacity', r => {r.Hillman_product_capacity = 100;}],
  ['complete joint capacity', r => {r.complete_joint_resistance = 100;}],
  ['finished member capacity', r => {r.finished_member_capacity = 100;}],
  ['missing head exceedances', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids = [];}],
  ['missing nonworst head exceedance', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids.pop();}],
  ['missing nonworst head exceedances with coordinated counts', r => {
    const screws = r.cases[0].coarse.generic_screw_references;
    screws.generic_CD1_head_exceedance_axis_ids = [screws.generic_head_ratio_CD1.axis_id];
    screws.reference_counts.generic_CD1_head_exceedances = 1;
  }],
  ['foreign screw scalar axis', r => {r.cases[0].coarse.generic_screw_references.all_screw_reference_scalars[0].axis_id = 'foreign';}],
  ['nonfinite head reference', r => {r.cases[0].coarse.generic_screw_references.all_screw_reference_scalars[0].generic_head_ratio_CD1 = NaN;}],
  ['missing thread exceedances', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances = [];}],
  ['missing nonworst thread exceedance with coordinated counts', r => {
    const screws = r.cases[3].coarse.generic_screw_references;
    screws.all_effective_thread_length_reference_exceedances = screws.all_effective_thread_length_reference_exceedances.filter(w =>
      w.axis_id === screws.generic_withdrawal_required_effective_thread_mm_CD1.axis_id);
    screws.reference_counts.effective_thread_length_exceedances = screws.all_effective_thread_length_reference_exceedances.length;
  }],
  ['missing panel exceedances', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1 = [];}],
  ['missing nonworst panel exceedance', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1.pop();}],
  ['missing stability census', r => {delete r.cases[0].gross_member_stability.all_member_witness_records;}],
  ['missing stability member', r => {r.cases[0].gross_member_stability.all_member_witness_records.pop();}],
  ['duplicate stability member', r => {
    const rows = r.cases[0].gross_member_stability.all_member_witness_records;
    rows[1] = structuredClone(rows[0]);
  }],
  ['foreign stability member', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].member = 'foreign';}],
  ['changed stability span', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].span_mm += 1;}],
  ['missing stability domain exceedances', r => {delete r.cases[0].gross_member_stability.full_length_domain_exceedances;}],
  ['empty stability domain exceedances', r => {r.cases[0].gross_member_stability.full_length_domain_exceedances = [];}],
  ['missing nonworst stability domain exceedance', r => {r.cases[0].gross_member_stability.full_length_domain_exceedances.pop();}],
  ['missing largest stability witness', r => {delete r.cases[0].gross_member_stability.largest_saved_K1_normal_sensitivity;}],
  ['changed whole largest stability witness', r => {r.cases[0].gross_member_stability.largest_saved_K1_normal_sensitivity.stress_compression_tension_strong_weak_mpa[0] += 1;}],
  ['missing stability reference exceedance list', r => {delete r.cases[0].gross_member_stability.saved_witness_reference_exceedances;}],
  ['nonexceeding stability reference witness', r => {
    const s = r.cases[0].gross_member_stability;
    s.saved_witness_reference_exceedances.push({member: s.all_member_witness_records[0].member,
      ...s.all_member_witness_records[0].two_saved_witness_sensitivities[0]});
  }],
  ['invented stability resistance', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].actual_restraint_or_complete_resistance = 1;}],
  ['qualified outside stability domain', r => {
    const w = r.cases[0].gross_member_stability.all_member_witness_records
      .flatMap(m => m.two_saved_witness_sensitivities).find(v => !v.within_slenderness_limits);
    w.ratio_qualified_inside_declared_stability_domain = true;
  }],
  ['wrong screw reference census', r => {r.cases[0].coarse.generic_screw_references.reference_counts.axes = 65;}],
  ['duplicate head exceedance', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids[1] = r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids[0];}],
  ['foreign thread exceedance state', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].state_id = 'foreign';}],
  ['nonexceeding thread witness', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].generic_withdrawal_required_effective_thread_mm_CD1 = 0;}],
  ['changed same-axis thread witness', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].lateral_n += 1.;}],
  ['changed nonworst same-axis thread witness', r => {
    const screws = r.cases[3].coarse.generic_screw_references;
    const nonworst = screws.all_effective_thread_length_reference_exceedances.find(w =>
      w.axis_id !== screws.generic_withdrawal_required_effective_thread_mm_CD1.axis_id);
    assert.ok(nonworst);
    nonworst.lateral_n += 999;
  }],
  ['changed panel exceedance witness', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1[0].xy_mm[0] += 1.;}],
  ['missing steel scenarios', r => {for (const c of r.cases) delete c.rich.steel_scenarios;}],
  ['missing steel scenario', r => {r.cases[0].rich.steel_scenarios.pop();}],
  ['foreign steel scenario', r => {r.cases[0].rich.steel_scenarios[0].comparison.id = 'foreign';}],
  ['invented Eoere strength', r => {r.cases[0].rich.steel_scenarios[0].product_strength = 100;}],
  ['steel changed actions', r => {r.cases[0].rich.steel_scenarios[0].fixed_actions_only = false;}],
  ['missing steel category', r => {delete r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined;}],
  ['wrong steel comparison count', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.comparison_count = 87;}],
  ['missing steel scalar census', r => {delete r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.all_reference_values;}],
  ['short steel scalar census', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.all_reference_values.pop();}],
  ['missing heel exceedances', r => {r.cases[0].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity.exceedances = [];}],
  ['missing nonworst heel exceedance with coordinated counts and bindings', r => {
    const c = r.cases[2].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity;
    assert.ok(c.exceedances.length > 1);
    c.exceedances = [structuredClone(c.worst)];
    c.whole_exceedance_witness_bindings = structuredClone(c.exceedances);
    c.exceedance_count = 1;
  }],
  ['changed nonworst heel witness', r => {
    const c = r.cases[2].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity;
    const w = c.exceedances.find(w => w.conditional_combined_yield_reference_ratio < c.worst.conditional_combined_yield_reference_ratio);
    assert.ok(w); w.pure_bending_peak_mpa += 1;
  }],
  ['false worst steel value', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.worst.conditional_combined_yield_reference_ratio = 999;}],
  ['wood washer land transfer', r => {r.cases[0].rich.washers.nominal_seat_geometry.all_current_finished_wood_lands_qualified = true;}],
  ['spacer loading proxy', r => {r.cases[0].spacer_nuts[0].nominal_washer_ring_reference.uniform_load_ring_outer_radius_mm = 6.;}],
  ['spacer own force', r => {r.cases[0].spacer_nuts[0].N_n += 1.;}],
  ['mixed stack capacity', r => {r.cases[0].mixed_stack_statics.compatible_threaded_contact_or_yield_capacity = 100;}],
  ['floor capacity', r => {r.cases[0].support_screen.floor_friction_or_contact_pressure_capacity = 100;}],
  ['foreign finished state', r => {r.targeted_finished_sections.per_case_worst_witnesses[0].normal_worst.state_id = 'foreign';}],
  ['foreign global normal state', r => {r.targeted_finished_sections.maximum_normal_reference.state_id = 'foreign';}],
  ['foreign global shear state', r => {r.targeted_finished_sections.maximum_necessary_mean_shear.state_id = 'foreign';}],
  ['inconsistent global normal value', r => {r.targeted_finished_sections.maximum_normal_reference.normal_reference.fully_braced_linear_normal_CD1_reference_index = 999;}],
  ['inconsistent global shear value', r => {r.targeted_finished_sections.maximum_necessary_mean_shear.necessary_mean_shear_over_CD1_Fv = 999;}],
  ['missing global normal witness', r => {delete r.targeted_finished_sections.maximum_normal_reference;}],
  ['missing global shear witness', r => {delete r.targeted_finished_sections.maximum_necessary_mean_shear;}],
  ['missing finished normal exceedance list', r => {delete r.targeted_finished_sections.all_selected_plane_normal_reference_exceedances;}],
  ['missing finished shear exceedance list', r => {delete r.targeted_finished_sections.all_selected_plane_necessary_shear_reference_exceedances;}],
  ['fabricated foreign finished exceedance', r => {
    const f = r.targeted_finished_sections, w = structuredClone(f.maximum_normal_reference);
    w.state_id = 'foreign'; w.normal_reference.fully_braced_linear_normal_CD1_reference_index = 1.1;
    f.all_selected_plane_normal_reference_exceedances = [w];
  }],
  ['fabricated current finished exceedance', r => {
    const f = r.targeted_finished_sections, w = structuredClone(f.maximum_normal_reference);
    w.normal_reference.fully_braced_linear_normal_CD1_reference_index = 1.1;
    f.all_selected_plane_normal_reference_exceedances = [w];
  }],
  ['nonexceeding finished normal witness', r => {r.targeted_finished_sections.all_selected_plane_normal_reference_exceedances = [structuredClone(r.targeted_finished_sections.maximum_normal_reference)];}],
  ['nonexceeding finished shear witness', r => {r.targeted_finished_sections.all_selected_plane_necessary_shear_reference_exceedances = [structuredClone(r.targeted_finished_sections.maximum_necessary_mean_shear)];}],
  ['foreign finished plane', r => {r.targeted_finished_sections.per_case_worst_witnesses[0].normal_worst.member = 'foreign';}],
  ['nonfinite finished maximum', r => {r.targeted_finished_sections.maximum_normal_reference.normal_reference.fully_braced_linear_normal_CD1_reference_index = NaN;}],
  ['mixed global normal witness', r => {r.targeted_finished_sections.maximum_normal_reference.necessary_mean_shear_mpa += 1;}],
  ['duplicate plane', r => {r.targeted_finished_sections.planes[1] = r.targeted_finished_sections.planes[0];}],
  ['missing finished scalar census', r => {delete r.targeted_finished_sections.all_selected_plane_reference_scalars;}],
  ['missing finished scalar row', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars.pop();}],
  ['duplicate finished scalar row', r => {
    const scalars = r.targeted_finished_sections.all_selected_plane_reference_scalars;
    scalars[1] = structuredClone(scalars[0]);
  }],
  ['foreign nonworst finished scalar state', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars[0].state_id = 'foreign';}],
  ['nonfinite nonworst finished scalar', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars[0].necessary_mean_shear_over_CD1_Fv = NaN;}],
  ['changed selected-plane normal worst value', r => {
    const f = r.targeted_finished_sections;
    f.per_case_worst_witnesses[0].normal_worst.normal_reference.fully_braced_linear_normal_CD1_reference_index += .01;
  }],
  ['continuous member capacity', r => {r.targeted_finished_sections.continuous_finished_member_resistance = 100;}],
  ...['extra_grid', 'structural_acceptance', 'native_solve_performed', 'CAD_rebuilt', 'actual_build_fit_work_performed',
    'remedies_attempted', 'physical_demand_bounds_established'].map(key => [key, r => {r[key] = true;}]),
]) test(`reject current component references ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  mutate(report);
  assert.throws(() => validateCurrentComponents(report, index));
});

test('stability disclosures retain complete strict-threshold and tied whole witnesses', () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  const stability = report.cases[0].gross_member_stability, members = stability.all_member_witness_records;
  for (const [i, j, ratio] of [[0, 0, 1.25], [1, 0, 1.25], [0, 1, 1.1], [1, 1, 1]]) {
    const witness = members[i].two_saved_witness_sensitivities[j];
    witness.interaction_ratio = ratio;
    witness.ratio_exceeds_one = ratio > 1;
  }
  const all = members.flatMap(m => m.two_saved_witness_sensitivities.map(w => ({member: m.member, ...w})));
  stability.saved_witness_reference_exceedances = structuredClone(all.filter(w => w.interaction_ratio > 1));
  stability.largest_saved_K1_normal_sensitivity = structuredClone(all.find(w => w.interaction_ratio === 1.25));
  assert.equal(stability.saved_witness_reference_exceedances.length, 3);
  validateCurrentComponents(report, index);
  stability.saved_witness_reference_exceedances.pop();
  assert.throws(() => validateCurrentComponents(report, index));
});

function reportWithFinishedExceedances() {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  const f = report.targeted_finished_sections;
  const planeID = w => JSON.stringify([w.member, w.station_global_grain_projection_mm]);
  function raise(caseIndex, worstKey, metric, value, otherPlane = false) {
    const original = f.per_case_worst_witnesses[caseIndex][worstKey];
    const plane = otherPlane ? f.planes.find(p => planeID(p) !== planeID(original)) : original;
    const scalar = f.all_selected_plane_reference_scalars.find(s => s.case_id === original.case_id && planeID(s) === planeID(plane));
    const witness = structuredClone(original);
    Object.assign(witness, {member: scalar.member, station_global_grain_projection_mm: scalar.station_global_grain_projection_mm,
      finished_area_mm2: f.planes.find(p => planeID(p) === planeID(scalar)).finished_area_mm2});
    scalar[metric] = value;
    witness.normal_reference.fully_braced_linear_normal_CD1_reference_index = scalar.fully_braced_linear_normal_CD1_reference_index;
    witness.necessary_mean_shear_over_CD1_Fv = scalar.necessary_mean_shear_over_CD1_Fv;
    scalar.exceedance_witness = witness;
  }
  const normalKey = 'fully_braced_linear_normal_CD1_reference_index', shearKey = 'necessary_mean_shear_over_CD1_Fv';
  for (const i of [0, 1]) raise(i, 'normal_worst', normalKey, 1.25);
  raise(0, 'normal_worst', normalKey, 1.1, true);
  for (const i of [2, 3]) raise(i, 'necessary_shear_worst', shearKey, i === 2 ? 1.2 : 1.3);
  raise(2, 'necessary_shear_worst', shearKey, 1.05, true);
  for (const row of f.per_case_worst_witnesses) for (const [key, metric] of [['normal_worst', normalKey], ['necessary_shear_worst', shearKey]]) {
    const worst = f.all_selected_plane_reference_scalars.filter(s => s.case_id === row.case_id).reduce((a,b) => a[metric] >= b[metric] ? a : b);
    row[key] = structuredClone(worst.exceedance_witness ?? row[key]);
  }
  f.maximum_normal_reference = structuredClone(f.per_case_worst_witnesses[1].normal_worst);
  f.maximum_necessary_mean_shear = structuredClone(f.per_case_worst_witnesses[3].necessary_shear_worst);
  f.all_selected_plane_normal_reference_exceedances = f.all_selected_plane_reference_scalars.filter(s => s[normalKey] > 1).map(s => structuredClone(s.exceedance_witness));
  f.all_selected_plane_necessary_shear_reference_exceedances = f.all_selected_plane_reference_scalars.filter(s => s[shearKey] > 1).map(s => structuredClone(s.exceedance_witness));
  return {index, report};
}

test('finished disclosures accept complete exceedances and tied whole maxima', () => {
  const {index, report} = reportWithFinishedExceedances();
  validateCurrentComponents(report, index);
});

for (const kind of ['normal_reference', 'necessary_shear_reference']) test(`reject omitted finished ${kind} witness`, () => {
  const {index, report} = reportWithFinishedExceedances();
  report.targeted_finished_sections[`all_selected_plane_${kind}_exceedances`].shift();
  assert.throws(() => validateCurrentComponents(report, index));
});

for (const [kind, metric, value] of [['normal_reference', w => w.normal_reference.fully_braced_linear_normal_CD1_reference_index, 1.1],
  ['necessary_shear_reference', w => w.necessary_mean_shear_over_CD1_Fv, 1.05]]) test(`reject omitted nonworst same-case finished ${kind} witness`, () => {
  const {index, report} = reportWithFinishedExceedances();
  const key = `all_selected_plane_${kind}_exceedances`;
  assert.ok(report.targeted_finished_sections[key].some(w => metric(w) === value));
  report.targeted_finished_sections[key] = report.targeted_finished_sections[key].filter(w => metric(w) !== value);
  assert.throws(() => validateCurrentComponents(report, index));
});

test('existing scene validators reject altered counts, moves and acceptance claims', () => {
  const index = readIndex();
  const current = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  const parent = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, 'site', current.parent_scene.url))));
  for (const [patch, validate, digest, mutate] of [
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.counts.base.screw = 65;}],
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.moved_screw_axes[0].new_origin_xyz_mm[2] = 211;}],
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.analysis_pass_transferred = true;}],
    [parent, validateUniformChannels, current.parent_scene.layout_sha256, p => {p.release.fabrication_released = true;}],
  ]) {
    const changed = structuredClone(patch); mutate(changed);
    assert.throws(() => validate(changed, digest));
  }
});

for (const [label, mutate] of [
  ['unsupported smaller harness envelope', p => {p.profile.front_width_mm = 8;}],
  ['missing narrowed member', p => {p.replacements.base.pop();}],
  ['notch physical release', p => {p.release.fabrication = true;}],
]) test(`reject ${label}`, () => {
  const index = readNotchIndex();
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene); assert.throws(() => validateNarrowChannels(scene, index.geometry.receipt.sha256));
});
for (const [label, mutate] of [
  ['notch receipt drift', i => {i.geometry.receipt.sha256 = '0'.repeat(64);}],
  ['missing narrowed shop coordinates', i => {i.shop.overrides = [];}],
  ['notch response transfer', i => {i.current_response = i.preceding_revision.preceding_revision.current_response;}],
]) test(`reject ${label}`, () => {
  const index = readNotchIndex(); mutate(index); assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});
