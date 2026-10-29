import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {readIndex, validateExternalHexTrial, viewerModel} from '../scripts/check_bolted_development.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';
import {validateExternalHexHeadsResults, externalHexHeadsResultsStatus} from '../site/eoere-v11-external-hex-heads-results.mjs';

test('external-hex trial binds its own geometry and fresh bank without selecting it', () => {
  const index = readIndex(), entry = index.owner_authorized_external_hex_trial;
  assert.equal(validateExternalHexTrial(entry, index), entry);
  assert.equal(entry.response_case_count, 6);
  assert.equal(entry.independent_replay_count, 12);
  const html = readFileSync(new URL('../site/index.html', import.meta.url), 'utf8');
  assert.equal(viewerModel(html, entry.viewer.model), entry.viewer.model);
  assert.equal(viewerModel(html, null), 'compact-floor-flush-development');
  for (const row of documentsForModel(entry.viewer.model)) {
    assert.ok(readFileSync(new URL('../' + row.path, import.meta.url)).length);
    assert.ok(row.path.includes('/external-hex-heads/') || row.path === entry.owner_direction.path);
  }
});

test('external-hex evidence rejects old-bank transfer, omitted cleat bolts and release claims', () => {
  const index = readIndex(), original = index.owner_authorized_external_hex_trial;
  for (const mutate of [
    e => { e.response_bank = index.owner_authorized_four_bolt_outer_top_trial.response_bank; },
    e => { e.geometry_source.sha256 = '0'.repeat(64); },
    e => { e.hardware_profile_validation.sha256 = '0'.repeat(64); },
    e => { e.parent_bank_admission.sha256 = '0'.repeat(64); },
    e => { e.end_edge_followthrough.calculation.sha256 = '0'.repeat(64); },
    e => { e.target_cleat_bolts_each = 6; },
    e => { e.target_spacer_pieces = 4; },
    e => { e.trial_selected = true; },
    e => { e.actual_Fyb = 92000; },
    e => { e.structural_acceptance = true; },
    e => { e.climbing_released = true; },
  ]) {
    const entry = structuredClone(original);
    mutate(entry);
    assert.throws(() => validateExternalHexTrial(entry, index));
  }
});

test('thread transitions include the head-side plate and the distinct front washer datum', () => {
  const entry = readIndex().owner_authorized_external_hex_trial;
  const data = JSON.parse(readFileSync(new URL('../' + entry.hardware_profile_clarification.path, import.meta.url)));
  const profiles = data.all28_actual_face_resistance_profiles;
  assert.ok(Math.abs(profiles.eoere_bolt_065.strength_transition_axis_t_mm - 33.9344) < 1e-9);
  assert.ok(Math.abs(profiles.rail_front_bolt_left_1.strength_transition_axis_t_mm - 117.094) < 1e-9);
});

test('computed external-hex results retain separate front coverage and geometry limits', () => {
  const entry = readIndex().owner_authorized_external_hex_trial;
  const data = validateExternalHexHeadsResults(JSON.parse(readFileSync(new URL('../' + entry.viewer.results_data.path, import.meta.url))));
  assert.equal(data.mixed_common_work_reference.summary.state_count, 144);
  assert.equal(data.mixed_common_work_reference.summary.above_one_count, 0);
  assert.equal(data.front_four_bolt_reference.states, 24);
  assert.equal(data.geometry_limitations.near_end_axes.length, 4);
  assert.equal(data.geometry_limitations.optional_weak_edge_rows, 3);
  assert.match(externalHexHeadsResultsStatus(data), /nominal9.525|nominal 9.525/);
  for (const mutate of [
    d => { d.sources.response_bank.sha256 = '0'.repeat(64); },
    d => { d.front_four_bolt_reference.states = 0; },
    d => { d.geometry_limitations.near_end_axes = []; },
    d => { d.geometry_limitations.optional_weak_edge_flags = []; },
    d => { d.conditional_hardware_profile_scope.all_current_resistance_profiles = 24; },
    d => { d.force_stiffness_vs_strength = 'Thread-zone stiffness is qualified.'; },
    d => { d.actual_property_adopted = true; },
    d => { d.complete_joint_qualified = true; },
  ]) {
    const changed = structuredClone(data);
    mutate(changed);
    assert.throws(() => validateExternalHexHeadsResults(changed));
  }
});
