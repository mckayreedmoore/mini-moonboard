// Validate the actual display delta and load it with Three.js in a file-backed environment.
// Usage: node scripts/check_hl35_scene.mjs /PATH/TO/three.module.js
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {webcrypto} from 'node:crypto';
import {pathToFileURL, fileURLToPath} from 'node:url';
import path from 'node:path';
import {validateHL35Scene, loadHL35Scene} from '../site/hl35-overlay.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const site = path.join(root, 'site');
assert.ok(process.argv[2], 'Supply an existing Three.js module; no installation is performed');
const THREE = await import(pathToFileURL(path.resolve(process.argv[2])).href);
globalThis.crypto ??= webcrypto;
globalThis.fetch = async url => {
  assert.equal(typeof url, 'string');
  assert.ok(!url.includes('..') && !url.includes(':') && !url.startsWith('/'));
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
for (const [url, angles, axes, exportedAxes] of [
  ['hl35-candidate-scene.json', 48, 152, 140],
  ['hl35-fit-v3-scene.json', 30, 112, 112],
  ['hl35-full-fit-scene.json', 30, 112, 112],
  ['hl35-service-fit-scene.json', 30, 112, 112],
  ['hl35-nominal-service-scene.json', 30, 112, 112],
  ['hl35-final-scene.json', 30, 112, 112],
  ['hl35-counterbore-scene.json', 30, 112, 112],
]) {
  const sceneText = await readFile(path.join(site, url), 'utf8');
  const data = JSON.parse(sceneText);
  assert.equal(validateHL35Scene(data), exportedAxes);
  for (const mutate of [
    d => { d.release.climbing_released = true; },
    d => { d.solids.push(d.solids[0]); },
    d => { d.solids.find(row => row.template_id).transform[0] *= 2; },
    d => { d.solids.find(row => row.fabrication.kind === 'bolt').fabrication.hardware_role = 'unknown'; },
    d => { d.counts.new_physical_bolt_axes++; },
    d => { d.parent_scene.sha256 = '0'.repeat(64); },
    d => { d.revision = 'unverified-revision'; },
  ]) {
    const invalid = structuredClone(data);
    mutate(invalid);
    assert.throws(() => validateHL35Scene(invalid));
  }
  if (data.removed_parent_bolt_axes) {
    const invalid = structuredClone(data);
    invalid.removed_parent_bolt_axes.pop();
    assert.throws(() => validateHL35Scene(invalid));
  }
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(sceneText));
  const expectedSha256 = Buffer.from(digest).toString('hex');
  const result = await loadHL35Scene(THREE, {url, expectedSha256,
    baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: p => p});
  assert.equal(result.parts.filter(p => p.fabrication.kind === 'bracket').length, angles);
  assert.equal(result.parts.filter(p => p.fabrication.kind === 'screw').length, 66);
  assert.equal(new Set(result.parts.filter(p => p.fabrication.kind === 'bolt').map(p => p.fabrication.connection_name)).size, axes);
  for (const [kind, count] of [['tnut', 142], ['light', 132], ['wire', 131]])
    assert.equal(result.parts.filter(p => p.fabrication.kind === kind).length, count);
  assert.equal(result.meta.physical_release, false);
  assert.equal(result.design.qualified_for_design, false);
  assert.ok(result.parts.every(p => !p.name.startsWith('wj04_') && !p.name.endsWith('_cleat')));
  console.log(JSON.stringify({scene: url, passed: true, visible_parts: result.parts.length,
    angles, physical_planning_bolt_axes: axes, preserved_screws: 66, retained_service_parts: 405}));
  for (const part of result.parts) part.geometry?.dispose();
}
