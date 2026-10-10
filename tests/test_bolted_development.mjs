import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, readIndex, checkDevelopment, validateEntry, validateStructuralAssessment, viewerModel} from '../scripts/check_bolted_development.mjs';
import {validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';
import {validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';

test('current geometry/shop, preceding response and baseline keep their own identities', () => {
  assert.equal(checkDevelopment().passed, true);
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
]) test(`reject ${label}`, () => {
  const index = readIndex(); mutate(index);
  assert.throws(() => checkDevelopment(index));
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

test('incoming descriptions reject a stale revision even when its link resolves', () => {
  const index = readIndex(), root = readFileSync(path.join(ROOT, 'README.md'), 'utf8');
  assert.throws(() => validateEntry(root.replaceAll(index.geometry.revision, index.response.revision), index));
  const html = readFileSync(path.join(ROOT, 'site/index.html'), 'utf8');
  assert.equal(viewerModel(html, index.response.revision), index.selected_baseline.candidate);
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
