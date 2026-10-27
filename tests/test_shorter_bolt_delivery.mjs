import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, checkDevelopment, readIndex, validateShorterBoltDelivery, validateShorterJointDisposition} from '../scripts/check_bolted_development.mjs';

function packet() {
  const index = readIndex();
  assert.equal(index.schema, 'bolted_frame_development_revisions/v20');
  assert.ok(index.owner_authorized_shorter_bolt_trial);
  return {index, trial: index.owner_authorized_shorter_bolt_trial};
}

test('shorter-bolt delivery binds the actual own packet without promoting analytical or physical acceptance', () => {
  const {index, trial} = packet();
  const result = validateShorterBoltDelivery(trial, index);
  assert.deepEqual(result, {revision: 'v11-shorter-bolts-v1', selected: false, bolt_axes: 112, occupied_parts: 1089,
    spacer_pieces: 4, reported_reference_rows: 110, optional_rear_foot_envelope_rows: 3,
    conditional_rear_supported_subchecks_above_one: 0, accepted_connection_exceedance_count: null,
    complete_connection_acceptance: null, structural_acceptance: false});
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
