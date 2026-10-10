import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, readIndex, checkDevelopment, validateEntry, viewerModel} from '../scripts/check_bolted_development.mjs';
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
]) test(`reject ${label}`, () => {
  const index = readIndex(); mutate(index);
  assert.throws(() => checkDevelopment(index));
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
