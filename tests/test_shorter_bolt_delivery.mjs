import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, checkDevelopment, readIndex, validateShorterBoltDelivery, validateShorterJointDisposition,
  validateCurrentShorterJointDispositionV5, validateShorterWasherStaticSummary, validateRetainedSpacerTransfer, validateBondInterfaceWrenches,
  validateRelocatedRearOwnerEvaluation, validateRelocatedRearTrial, preservedDevelopmentIndex, resolveDevelopmentSelection, viewerModel} from '../scripts/check_bolted_development.mjs';

function packet() {
  const index = preservedDevelopmentIndex(readIndex());
  assert.equal(index.schema, 'bolted_frame_development_revisions/v20');
  assert.ok(index.owner_authorized_shorter_bolt_trial);
  return {index, trial: index.owner_authorized_shorter_bolt_trial};
}

function currentV5() {
  const index = readIndex(), entry = index.owner_authorized_shorter_bolt_trial;
  assert.equal(entry.current_joint_disposition.path, 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/current-joint-disposition-v5.json.gz');
  const report = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, entry.current_joint_disposition.path))));
  return {index, entry, report};
}

test('owner rear-pair exception binds the reviewed coordinates without selecting or releasing the trial', () => {
  const index = readIndex(), record = JSON.parse(readFileSync(path.join(ROOT, index.owner_relocated_rear_pair_evaluation.path)));
  assert.equal(validateRelocatedRearOwnerEvaluation(record, index), record);
  for (const mutate of [r => {r.authorized_axis_changes[0].proposed_existing_axis_point_xyz_mm[2] += 1;},
    r => {r.candidate_selected = true;}, r => {r.candidate_spacers = 0;},
    r => {r.fabrication_released = true;}, r => {r.base_geometry.sha256 = '0'.repeat(64);}]) {
    const changed = structuredClone(record); mutate(changed);
    assert.throws(() => validateRelocatedRearOwnerEvaluation(changed, index));
  }
});

test('relocated rear preview binds its own geometry and stays separate from the selected frame', () => {
  const index = readIndex(), entry = index.owner_authorized_relocated_rear_pair_trial;
  assert.equal(validateRelocatedRearTrial(entry, index), entry);
  for (const mutate of [r => {r.trial_selected = true;}, r => {r.counts.spacer_pieces = 0;},
    r => {r.geometry_source = index.owner_authorized_matching_rear_bolt_trial.geometry_receipt;},
    r => {r.response_bank = index.owner_authorized_matching_rear_bolt_trial.response_bank;},
    r => {r.maximum_gradient_inf_N = 0;},
    r => {r.geometry_applicability = index.owner_authorized_matching_rear_bolt_trial.signed_geometry_applicability;},
    r => {r.reference_completion = index.owner_authorized_matching_rear_bolt_trial.reference_completion;},
    r => {r.contracted_rear_maximum = 0;},
    r => {r.all_applicable_criteria_resolved = true;},
    r => {r.mixed_generic45_Mp4_flag_count = 0;},
    r => {r.mixed_generic45_Mp4_maximum = 1.303678;},
    r => {r.viewer.scene = index.owner_authorized_matching_rear_bolt_trial.viewer.scene;},
    r => {r.fabrication_released = true;}]) {
    const changed = structuredClone(entry); mutate(changed);
    assert.throws(() => validateRelocatedRearTrial(changed, index));
  }
  const changed = structuredClone(index); changed.owner_authorized_relocated_rear_pair_trial.trial_selected = true;
  assert.throws(() => resolveDevelopmentSelection(changed));
});

test('bond wrench partition retains all signs and does not clear local peel or assign adhesive strength', () => {
  const {entry} = currentV5();
  const report = JSON.parse(readFileSync(path.join(ROOT, entry.bond_interface_wrench_followthrough.path)));
  assert.equal(validateBondInterfaceWrenches(report, entry), report);
  for (const mutate of [r => {r.adhesive_strength_or_stiffness_assigned = true;},
    r => {r.rows[0].outer_leaf_interface_moment_xyz_Nmm[0] = 0;},
    r => {r.rows[0].normal_resultant_screen.not_a_traction_or_peel_acceptance_check = false;},
    r => {r.rows[0].normal_resultant_screen.interface_normal_inner_to_outer_xyz = [1, 0, 0];},
    r => {r.complete_bond_or_joint_capacity = 1;}]) {
    const changed = structuredClone(report); mutate(changed);
    assert.throws(() => validateBondInterfaceWrenches(changed, entry));
  }
});

test('retained spacers join current loads and match unequal nut and washer pressure rings', () => {
  const {entry} = currentV5();
  const report = JSON.parse(readFileSync(path.join(ROOT, entry.retained_spacer_transfer.path)));
  assert.equal(validateRetainedSpacerTransfer(report, entry), report);
  for (const mutate of [r => {r.ring_map.c_mm = 9.525;}, r => {r.rows[0][2] += 1;},
    r => {r.rows[0][6] += 1;}, r => {r.qualification.actual_spacer_Fy_MPa = 250;},
    r => {r.controls.physical_end_moment_or_prying_known_zero = true;}]) {
    const changed = structuredClone(report); mutate(changed);
    assert.throws(() => validateRetainedSpacerTransfer(changed, entry));
  }
});

test('current static washer summary preserves all joint ownership and unknown physical capacity', () => {
  const {entry} = currentV5();
  const report = JSON.parse(readFileSync(path.join(ROOT, entry.washer_static_axial_followthrough.path)));
  assert.equal(validateShorterWasherStaticSummary(report, entry), report);
  for (const mutate of [r => {r.response_bank.sha256 = '0'.repeat(64);},
    r => {r.comparison_material.actual_washer_Fy_MPa = 250;},
    r => {r.joint_summaries[0].complete_joint_capacity = 1;},
    r => {r.current_spacers = 0;}, r => {r.joint_summaries[0].axis_ids = [];}]) {
    const changed = structuredClone(report); mutate(changed);
    assert.throws(() => validateShorterWasherStaticSummary(changed, entry));
  }
});

test('V5 keeps the current bank and every joint while separating corrected washer scenarios from actual capacity', () => {
  const {index, entry, report} = currentV5();
  assert.equal(validateCurrentShorterJointDispositionV5(report, entry, index), report);
  const plate = report.compact_new_evidence.washer_loaded_face_correction.data;
  assert.equal(plate.rows.length, 1344); assert.equal(report.joint_updates.length, 26);
  assert.equal(plate.summary.corrected_radius_rows, 1224); assert.equal(plate.summary.exact_radius_nochange_rows, 120);
  assert.equal(plate.summary.governing.axis_id, 'eoere_bolt_082'); assert.equal(plate.summary.governing.end, 'nut');
  assert.ok(plate.summary.corrected_conditional_maximum_required_Fy_MPa > plate.summary.historical_maximum_required_Fy_MPa);
  assert.equal(report.complete_joint_capacity, null); assert.equal(report.counts.new_force_cases, 0);
});

for (const [name, mutate] of [
  ['missing plywood subset', r => {r.compact_new_evidence.washer_loaded_face_correction.data.rows.splice(-96);}],
  ['duplicated washer end identity', r => {const p = r.compact_new_evidence.washer_loaded_face_correction.data; p.rows[1] = structuredClone(p.rows[0]);}],
  ['nominal hex radius relabelled as the smaller product-face scenario', r => {const p = r.compact_new_evidence.washer_loaded_face_correction.data; p.rows[0][9] = p.rows[0][8];}],
  ['head family replaced with a different catalog product', r => {r.compact_new_evidence.washer_loaded_face_correction.data.rows[0][5] = 'G0340956';}],
  ['gage circle called a guaranteed contact patch', r => {r.compact_new_evidence.washer_loaded_face_correction.data.basis_catalog.HCS_washerface_gage_circle_sensitivity_1_2.bearing_plane_guaranteed = true;}],
  ['washer material assigned without evidence', r => {r.compact_new_evidence.washer_loaded_face_correction.data.summary.actual_washer_Fy_MPa = 250;}],
  ['old washer maximum promoted back to current', r => {const s = r.compact_new_evidence.washer_loaded_face_correction.data.summary; s.corrected_conditional_maximum_required_Fy_MPa = s.historical_maximum_required_Fy_MPa;}],
  ['corrected row lost from its joint', r => {r.joint_updates[0].reference_role_updates.washer_plate.corrected_tuple_indices.pop();}],
  ['joint washer envelope understated', r => {r.joint_updates[0].additional_duties.conditional_washer_footprint_references.maximum_required_Fy_MPa_under_stated_footprint_scenarios = 0;}],
  ['zero pitch silently clears the bearing reference', r => {r.joint_updates.find(x => x.joint_id === 'rear-upper-left').additional_duties.rear_internal_allocation_and_bound.zero_pitch_clears_bound = true;}],
  ['local angle factor adopted without its missing method', r => {r.joint_updates.find(x => x.joint_id === 'rear-upper-left').additional_duties.rear_internal_allocation_and_bound.local_direction_dependent_Ktheta_authorized_by_NDS_or_TR12 = true;}],
  ['continuous necessary bound weakened to one', r => {r.compact_new_evidence.continuous_joint_necessary_bound.data.certified_required_lambda_strictly_greater_than.numerator = '100000';}],
  ['historical EC5 comparison promoted to an adopted basis', r => {r.joint_updates.find(x => x.joint_id === 'outer-top-left').additional_duties.historical_own_angle_spacing_screen.EC5_factors_or_load_basis_adopted = true;}],
  ['historical reference flags erased', r => {r.inherited_reference_inventories = {};}],
  ['projection presented as new matched cases', r => {r.counts.new_force_cases = 6;}],
  ['four retained spacers silently removed', r => {r.input_selection.metal_spacers = 0;}],
  ['structural acceptance inferred from the correction', r => {r.structural_acceptance = true;}],
]) test(`V5 rejects ${name}`, () => {
  const {index, entry, report} = currentV5(); mutate(report);
  assert.throws(() => validateCurrentShorterJointDispositionV5(report, entry, index));
});

test('shorter-bolt delivery binds the actual own packet without promoting analytical or physical acceptance', () => {
  const {index, trial} = packet();
  const result = validateShorterBoltDelivery(trial, index);
  assert.deepEqual(result, {revision: 'v11-shorter-bolts-v1', selected: false, bolt_axes: 112, occupied_parts: 1089,
    spacer_pieces: 4, reported_reference_rows: 110, optional_rear_foot_envelope_rows: 3,
    conditional_rear_supported_subchecks_above_one: 0, accepted_connection_exceedance_count: null,
    complete_connection_acceptance: null, structural_acceptance: false});
});

test('owner selection resolves the own four-spacer record while V20 and baseline remain preserved', () => {
  const index = readIndex(), record = resolveDevelopmentSelection(index), result = checkDevelopment(index);
  assert.equal(index.schema, 'bolted_frame_development_revisions/v21'); assert.equal(record, index.owner_authorized_shorter_bolt_trial);
  assert.equal(record.selected, true); assert.deepEqual([result.occupied_parts, result.bolt_axes, result.spacer_pieces], [1089, 112, 4]);
  assert.equal(result.revision, record.revision); assert.equal(result.current_response_revision, record.revision);
  assert.deepEqual(result.geometry_receipt, record.geometry_receipt); assert.deepEqual(result.response_bank, record.response_bank);
  const review = JSON.parse(readFileSync(path.join(ROOT, record.engineering_review.path)));
  assert.deepEqual(result.member_vector_references, review.member_vector_maxima);
  assert.equal(Object.hasOwn(result, 'conditional_Grade5_Fyb92_force_only_maximum'), false, 'preserved original property metrics are not current shorter-bolt results');
  assert.deepEqual([result.preserved_development_base.occupied_parts, result.preserved_development_base.spacer_pieces], [1109, 24]);
  assert.equal(result.preserved_development_base.viewer_model, 'eoere-v11-v9-eight-bolt-preview');
  assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.equal(result.complete_connection_acceptance, null); assert.equal(result.actual_Cg_adopted, null); assert.equal(result.purchase_authorized, false);
});

test('current four-spacer UI labels preserve original route and no-query baseline', () => {
  const html = readFileSync(path.join(ROOT, 'site/index.html'), 'utf8'), current = readIndex().development_selection;
  assert.equal(viewerModel(html, current.viewer.model), current.viewer.model);
  assert.equal(viewerModel(html, 'eoere-v11-v9-eight-bolt-preview'), 'eoere-v11-v9-eight-bolt-preview');
  assert.equal(viewerModel(html, null), 'compact-floor-flush-development');
  assert.ok(html.includes("['eoere-v11-shorter-bolts-preview', 'Current development · shorter bolts · 112 stacks · four spacers']"));
  assert.ok(html.includes('Preserved V11 · V9 cleats · 112 bolts · 24 spacers'));
  assert.ok(html.includes("if (shorterBolts) document.querySelector('#model-status').textContent = 'Current development selected by the owner · four spacers. ' + data.meta.status"));
  for (const file of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) {
    const text = readFileSync(path.join(ROOT, file), 'utf8'); assert.ok(text.includes('The current geometry is **`v11-shorter-bolts-v1`**'));
    assert.ok(text.includes('?model=eoere-v11-shorter-bolts-preview&view=rear')); assert.ok(text.includes('owner-shorter-bolt-selection.json'));
    assert.ok(text.includes('shorter-bolts/'+path.basename(readIndex().owner_authorized_shorter_bolt_trial.current_joint_disposition.path)),
      `${file} must link the current joint disposition from the revision index`);
  }
});

for (const [name, mutate] of [
  ['missing selected record', i => {delete i.owner_authorized_shorter_bolt_trial;}],
  ['pointer selects unselected114 record', i => {i.development_selection.record_pointer = '/owner_authorized_matching_rear_bolt_trial';}],
  ['owner decision hash changed', i => {i.development_selection.owner_decision.sha256 = '0'.repeat(64);}],
  ['selection flag omitted', i => {i.owner_authorized_shorter_bolt_trial.selected = false;}],
  ['preserved response bank substituted for selected bank', i => {i.owner_authorized_shorter_bolt_trial.response_bank = i.response_bank;}],
  ['preserved model selected under shorter revision', i => {i.development_selection.viewer.model = i.repository_viewer.model;}],
  ['four remaining spacers silently removed', i => {i.owner_authorized_shorter_bolt_trial.counts.metal_spacers = 0;}],
  ['preserved base receipt relabelled as current geometry', i => {i.geometry.receipt = i.owner_authorized_shorter_bolt_trial.geometry_receipt;}],
  ['root scope no longer marks old evidence preserved', i => {i.preserved_development_base.root_fields_are_preserved_evidence = false;}],
  ['114 trial silently selected alongside current112', i => {i.owner_authorized_matching_rear_bolt_trial.trial_selected = true;}],
  ['baseline promoted with development selection', i => {i.selected_baseline.candidate = 'v11-shorter-bolts-v1';}],
  ['development selection grants fabrication', i => {i.owner_authorized_shorter_bolt_trial.fabrication_released = true;}],
]) test(`current shorter-bolt selection rejects ${name}`, () => {
  const index = readIndex(); mutate(index); assert.throws(() => checkDevelopment(index, {entryChecks: false}));
});

test('current selection preserves optional-addon omissions while keeping its required own record', () => {
  const index = readIndex(); delete index.owner_authorized_matching_rear_bolt_trial;
  delete index.owner_bracket_thickness_confirmation; delete index.owner_authorized_shorter_bolt_trial.build_package;
  assert.equal(checkDevelopment(index, {entryChecks: false}).spacer_pieces, 4);
});

test('optional shorter-bolt delivery is checked by V20 while preserved V11 and baseline keep their identities', () => {
  const {index} = packet(), result = checkDevelopment(index, {entryChecks: false});
  assert.equal(result.owner_authorized_shorter_bolt_trial.revision, 'v11-shorter-bolts-v1');
  assert.equal(result.owner_authorized_shorter_bolt_trial.occupied_parts, 1089);
  assert.equal(result.revision, 'v11-v9-eight-bolt-v4'); assert.equal(result.occupied_parts, 1109);
  assert.equal(result.spacer_pieces, 24); assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development');
  assert.equal(result.full_ignored_input_closure_checked, false); assert.equal(result.mechanics_executed, false);
  delete index.owner_authorized_shorter_bolt_trial;
  const omitted = checkDevelopment(index, {entryChecks: false});
  assert.equal(omitted.owner_authorized_shorter_bolt_trial, undefined);
  assert.equal(omitted.revision, result.revision); assert.equal(omitted.current_response_revision, result.current_response_revision);
  assert.equal(omitted.structural_acceptance, false); assert.equal(omitted.purchase_authorized, false);
});

for (const [name, mutate] of [
  ['preserved V11 bank substituted', (r, i) => {r.response_bank = i.response_bank;}],
  ['preserved V11 bank hash relabelled as own', (r, i) => {r.response_bank.sha256 = i.response_bank.sha256;}],
  ['stale V11 result summary', (r, i) => {r.viewer.results = i.repository_viewer.results_json;}],
  ['stale geometry module', (r, i) => {r.viewer.geometry_overlay = i.repository_viewer.overlay;}],
  ['stale component review', (r, i) => {r.component_reference_summary = i.criterion_followthrough;}],
  ['named rows erased', r => {r.separate_reported_diagnostic_and_scenario_rows = 0;}],
  ['named and optional rows conflated', r => {r.separate_reported_diagnostic_and_scenario_rows = 113;}],
  ['unresolved row applications erased', r => {r.remaining_row_application_interface_cases = 0;}],
  ['optional rear envelopes erased', r => {r.additional_optional_rear_foot_envelope_rows.pop();}],
  ['optional envelope promoted to normative failure', r => {r.additional_optional_rear_foot_envelope_rows[0].normative_violation_established = true;}],
  ['rear subcheck count changed', r => {r.conditional_rear_supported_subchecks_above_one = 1;}],
  ['foreign CSV replaces named rows', r => {r.numerical_flags = r.nominal_hardware_fit;}],
  ['spacer decision bytes changed', r => {r.remaining_spacer_decision.sha256 = '0'.repeat(64);}],
  ['rear appendix bytes changed', r => {r.rear_conditional_followthrough.sha256 = '0'.repeat(64);}],
  ['replay admission erased', r => {r.all_six_cases_and_twelve_replays_admitted = false;}],
  ['geometry parts relabelled', r => {r.counts.occupied_parts = 1109;}],
  ['four retained spacers removed', r => {r.counts.metal_spacers = 0;}],
  ['actual Cg adopted', r => {r.actual_Cg_adopted = 1;}],
  ['zero accepted failure count invented', r => {r.accepted_connection_exceedance_count = 0;}],
  ['frame acceptance inherited', r => {r.conditional_frame_evaluation = {complete: true};}],
  ['complete joint acceptance inherited', r => {r.complete_connection_acceptance = true;}],
  ['fabrication release inherited', r => {r.fabrication_released = true;}],
  ['trial silently selected', r => {r.selected = true;}],
]) test(`V20 shorter-bolt delivery rejects ${name}`, () => {
  const {index, trial} = packet(); mutate(trial, index);
  assert.throws(() => checkDevelopment(index, {entryChecks: false}));
});

function jointPacket() {
  const {index, trial} = packet();
  // Explicit local override permits testing a draft before its public publication; CI uses the public record.
  const fixture = process.env.SHORTER_JOINT_FIXTURE ?? 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/joint-disposition.json';
  return {index, trial, report: JSON.parse(readFileSync(path.resolve(ROOT, fixture))),
    bank: JSON.parse(readFileSync(path.join(ROOT, trial.response_bank.path))),
    scene: JSON.parse(gunzipSync(readFileSync(path.join(ROOT, trial.viewer.scene.path))))};
}

test('shorter joint disposition covers26 clusters and112 axes with unresolved whole-joint capacities', () => {
  const {report, trial, index, bank, scene} = jointPacket();
  assert.equal(validateShorterJointDisposition(report, trial, index, bank, scene), report);
  assert.equal(report.counts.fittings, 24); assert.equal(report.counts.mixed_axes, 24);
  assert.equal(report.accepted_connection_exceedance_count, null);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.response_bank = i.response_bank;}],
  ['stale public review', (r, i) => {r.engineering_review = i.engineering_review;}],
  ['duplicate cluster identity', r => {r.joint_clusters[0].joint_id = r.joint_clusters[1].joint_id;}],
  ['multiply owned axis', r => {r.joint_clusters[0].axis_ids[0] = r.joint_clusters[0].axis_ids[1];}],
  ['foreign axis preserves the count', r => {r.joint_clusters[0].axis_ids[0] = 'foreign-axis';}],
  ['missing fitting', r => {r.joint_clusters.find(row => row.fitting_ids.length).fitting_ids.pop();}],
  ['mixed axis removed', r => {r.joint_clusters.find(row => row.mixed_axis_ids.length).mixed_axis_ids.pop();}],
  ['whole cluster qualified', r => {r.joint_clusters[0].whole_joint_qualified = true;}],
  ['complete capacity invented', r => {r.joint_clusters[0].complete_joint_capacity = 1000;}],
  ['actual row factor adopted', r => {r.joint_clusters[0].actual_Cg_adopted = 1;}],
  ['remaining duties erased', r => {r.joint_clusters[0].remaining_duties = [];}],
  ['contact sensitivity promoted to qualification', r => {r.new_followthrough.contact_motion.contact_assumption_qualified = true;}],
  ['unselected outer-top option adopted', r => {r.review_options.outer_top.adopted = true;}],
  ['zero accepted failures invented', r => {r.accepted_connection_exceedance_count = 0;}],
  ['unresolved status promoted to pass', r => {r.status = 'PASS';}],
  ['physical release inherited', r => {r.fabrication_released = true;}],
]) test(`shorter joint disposition rejects ${name}`, () => {
  const {report, trial, index, bank, scene} = jointPacket(); mutate(report, index);
  assert.throws(() => validateShorterJointDisposition(report, trial, index, bank, scene));
});

test('shorter joint supplement checks its own bytes and permits the preserved delivery without the supplement', () => {
  const {index, trial} = packet();
  trial.joint_disposition = {path: 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/joint-disposition.json', sha256: '0'.repeat(64)};
  assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  delete trial.joint_disposition;
  assert.equal(validateShorterBoltDelivery(trial, index).reported_reference_rows, 110);
});

test('shorter 1D material reference keeps its eight states distinct from the frozen110 rows and acceptance', () => {
  const {report, trial, index, bank, scene} = jointPacket();
  assert.equal(validateShorterJointDisposition(report, trial, index, bank, scene), report);
  const model = report.new_followthrough.generalized_lateral_material_reference;
  assert.equal(model.additional_named_model_reference_flags.length, 8);
  assert.equal(model.actual_A574_Fyb_adopted, null); assert.equal(model.accepted_connection_failure_count, null);
  assert.equal(trial.separate_reported_diagnostic_and_scenario_rows, 110);
  delete report.new_followthrough.generalized_lateral_material_reference;
  delete report.source_bindings.generalized_lateral_material_model;
  assert.equal(validateShorterJointDisposition(report, trial, index, bank, scene), report,
    'the preserved core schema remains valid without an optional model-reference supplement');
});

for (const [name, mutate] of [
  ['eight-state inventory erased', r => {r.additional_named_model_reference_flags.pop();}],
  ['duplicated model state', r => {r.additional_named_model_reference_flags[0] = r.additional_named_model_reference_flags[1];}],
  ['unmatched model source', r => {r.source.sha256 = '0'.repeat(64);}],
  ['A574 actual Fyb adopted', r => {r.actual_A574_Fyb_adopted = 153000;}],
  ['generic A574 reference replaced by tensile value', r => {r.additional_named_model_reference_flags[0].shaft_bending_reference.conditional_Fyb_reference_psi = 153000;}],
  ['model factor promoted to actual Cg', r => {r.factor_is_actual_Cg_or_independent_steel_code_factor = true;}],
  ['accepted failure count inferred', r => {r.accepted_connection_failure_count = 8;}],
  ['complete NDS capacity inferred', r => {r.qualifications.complete_NDS_connection_capacity = 1;}],
  ['physical failure inferred', r => {r.qualifications.physical_failure_claim = true;}],
]) test(`shorter 1D material reference rejects ${name}`, () => {
  const {report, trial, index, bank, scene} = jointPacket();
  // Clone the block so a source-pointer mutation cannot update its independent declaration by alias.
  report.new_followthrough.generalized_lateral_material_reference = structuredClone(report.new_followthrough.generalized_lateral_material_reference);
  mutate(report.new_followthrough.generalized_lateral_material_reference);
  assert.throws(() => validateShorterJointDisposition(report, trial, index, bank, scene));
});
