import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {readIndex, checkDevelopment} from '../scripts/check_bolted_development.mjs';
import {validateLegHeader} from '../site/eoere-leg-header-overlay.mjs';

test('combined geometry retains its parent, 66 screws and unqualified strength boundary', () => {
  const index = readIndex(), checked = checkDevelopment(index);
  assert.equal(checked.bolt_axes, 96); assert.equal(checked.angles, 24);
  assert.equal(index.preceding_revision.geometry.revision, 'eoere-centred-enclosed-passages-v1');
  assert.equal(index.current_response, null);
  const report = JSON.parse(readFileSync(index.geometry.receipt.path));
  const scene = JSON.parse(gunzipSync(readFileSync(index.geometry.scene.path)));
  for (const part of scene.replacements.filter(r => r.fabrication.kind === 'bolt')) {
    const axis = report.axes.find(a => a.id === part.fabrication.connection_name);
    assert.ok(axis, 'new parts must retain their bolt identity');
    assert.equal(part.fabrication.selected_underhead_length_mm, axis.nominal_under_head_length_mm);
    assert.equal(part.fabrication.nut_side_spacer_mm, axis.nut_side_spacer_mm);
    assert.equal(part.fabrication.delivered_part_verified, false);
  }
});

for (const [label, mutate] of [
  ['old occupied count', p => {p.part_count = 1033;}],
  ['missing removed leg stack', p => {p.removals.pop();}],
  ['missing spacer inspection dimensions', p => {delete p.replacements.find(r => r.name.endsWith('_spacer')).fabrication.dimensions_mm;}],
  ['duplicate replacement', p => {p.replacements[1].name = p.replacements[0].name;}],
  ['strength transfer', p => {p.historical_capacity_transferred = true;}],
  ['fabrication release', p => {p.release.fabrication_released = true;}],
]) test(`reject combined ${label}`, () => {
  const index = readIndex();
  const scene = JSON.parse(gunzipSync(readFileSync(index.geometry.scene.path)));
  mutate(scene);
  assert.throws(() => validateLegHeader(scene, index.geometry.receipt.sha256));
});
