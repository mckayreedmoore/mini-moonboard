import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {readIndex as readCurrentIndex, checkDevelopment} from '../scripts/check_bolted_development.mjs';
import {validateEnclosedPassages} from '../site/eoere-enclosed-passages-overlay.mjs';

function readIndex() {
  let index = readCurrentIndex();
  while (index && index.geometry.revision !== 'eoere-centred-enclosed-passages-v1') index = index.preceding_revision;
  assert.ok(index, 'preserved enclosed-passage parent required');
  return index;
}

test('enclosed holes retain their own geometry and open resistance boundary', () => {
  const index = readIndex();
  assert.equal(checkDevelopment(index, {entryChecks: false}).enclosed_passages, 32);
  assert.equal(index.preceding_revision.geometry.revision, 'eoere-narrow-channel-openings-v1');
});

for (const [label, mutate] of [
  ['missing replacement cable', p => {p.replacements.pop();}],
  ['duplicate part identity', p => {p.replacements[1].name = p.replacements[0].name;}],
  ['transferred strength', p => {p.historical_capacity_transferred = true;}],
  ['fabrication release', p => {p.release.fabrication_released = true;}],
]) test(`reject enclosed-passage ${label}`, () => {
  const index = readIndex();
  const patch = JSON.parse(gunzipSync(readFileSync(index.geometry.scene.path)));
  mutate(patch);
  assert.throws(() => validateEnclosedPassages(patch, index.geometry.receipt.sha256));
});
