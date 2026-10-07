// Validate the actual compressed scene and load it with existing Three.js geometry.
// Usage: node scripts/check_thin_bolted_scene.mjs /PATH/TO/three.module.js
// Or: ... --bundle /PATH/TO/ocp_vscode/static/js/three-cad-viewer.esm.js
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {webcrypto, createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {pathToFileURL, fileURLToPath} from 'node:url';
import path from 'node:path';
import {validateThinBoltedScene, loadThinBoltedScene} from '../site/thin-bolted-overlay.mjs';

const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const bundle = process.argv[2] === '--bundle', modulePath = process.argv[bundle ? 3 : 2];
assert.ok(modulePath, 'Supply an existing Three.js module or existing viewer bundle');
const moduleSource = await readFile(modulePath);
const THREE = bundle
  ? await import('data:text/javascript;base64,' + Buffer.concat([moduleSource,
    Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'))
  : await import(pathToFileURL(path.resolve(modulePath)).href);
globalThis.crypto ??= webcrypto;
globalThis.fetch = async url => {
  assert.equal(typeof url, 'string');
  assert.ok(!url.includes('..') && !url.includes(':') && !url.startsWith('/'));
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const contract = JSON.parse(await readFile(path.join(root, 'thin-bolted-candidate.json'), 'utf8'));
assert.equal(contract.selected, false);
const t = contract.viewer.transport, encoded = await readFile(path.join(root, t.path));
const raw = gunzipSync(encoded), scene = JSON.parse(raw);
assert.equal(digest(encoded), t.sha256);
assert.equal(digest(raw), contract.viewer.sha256);
assert.equal(validateThinBoltedScene(scene), 70);
const rejected = [];
for (const [name, mutate] of [
  ['release', d => { d.release.climbing_released = true; }],
  ['duplicate-part', d => { d.solids.push(d.solids[0]); }],
  ['scale-transform', d => { d.solids.find(row => row.template_id).transform[0] *= 2; }],
  ['reflect-transform', d => { const m = d.solids.find(row => row.template_id).transform; m[0] *= -1; m[1] *= -1; m[2] *= -1; }],
  ['unknown-role', d => { d.solids.find(row => row.fabrication.kind === 'bolt').fabrication.hardware_role = 'unknown'; }],
  ['missing-role', d => { d.solids.splice(d.solids.findIndex(row => row.fabrication.kind === 'bolt'), 1); }],
  ['changed-census', d => { d.counts.physical_bolt_axes++; }],
  ['changed-source', d => { d.parent_scene.sha256 = '0'.repeat(64); }],
  ['old-wire-retained', d => { d.retained_parent_service_names[0] = 'wire_001_A1_A2'; }],
  ['unknown-revision', d => { d.revision = 'unknown'; }],
]) {
  const invalid = structuredClone(scene); mutate(invalid);
  assert.throws(() => validateThinBoltedScene(invalid)); rejected.push(name);
}
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const options = {url: path.basename(t.path), expectedSha256: t.sha256, decodedSha256: t.decoded_sha256,
  baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: p => aliases[p] || p};
await assert.rejects(loadThinBoltedScene(THREE, {...options, expectedSha256: '0'.repeat(64)}), /scene bytes differ/);
await assert.rejects(loadThinBoltedScene(THREE, {...options, decodedSha256: '0'.repeat(64)}), /decoded scene bytes differ/);
const loaded = await loadThinBoltedScene(THREE, options);
const kinds = Object.fromEntries(['timber', 'panel', 'bracket', 'bolt', 'screw', 'wire', 'light', 'tnut']
  .map(kind => [kind, loaded.parts.filter(p => p.fabrication.kind === kind).length]));
assert.deepEqual(kinds, {timber: 20, panel: 6, bracket: 36, bolt: 350, screw: 66, wire: 131, light: 132, tnut: 142});
assert.equal(loaded.parts.length, 883);
assert.equal(new Set(loaded.parts.filter(p => p.fabrication.kind === 'bolt').map(p => p.fabrication.connection_name)).size, 70);
assert.equal(loaded.meta.physical_release, false);
assert.equal(loaded.design.qualified_for_design, false);
assert.ok(loaded.parts.every(p => !p.name.startsWith('wj04_') && !p.name.endsWith('_cleat') &&
  !p.name.startsWith('clip_') && !p.name.includes('SDS')));
let sharedAssets = 0;
for (const part of loaded.parts) {
  if (part.path) {
    assert.equal(digest(await readFile(path.join(site, part.path))), part.expected_sha256);
    sharedAssets++;
  }
  if (part.geometry) assert.ok([...part.geometry.getAttribute('position').array].every(Number.isFinite));
}
assert.equal(sharedAssets, 273);
const index = await readFile(path.join(site, 'index.html'), 'utf8');
assert.ok(index.includes("['thin-bolted-development',") && index.includes(t.sha256) && index.includes(t.decoded_sha256));
const packet = path.join(root, 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison');
const report = {schema: 'thin_bolted_viewer_validation/v1', candidate: scene.candidate,
  revision: scene.revision, passed: true, loaded_visible_parts: loaded.parts.length,
  kinds, complete_bolt_axes: 70, authenticated_shared_assets: sharedAssets,
  rejected_invalid_scenes: rejected, rejected_encoded_and_decoded_hash_mismatches: true,
  native_browser_or_webgl_render_tested: false,
  geometry_module: {source_sha256: digest(moduleSource), bundled: bundle,
    three_revision: moduleSource.toString().match(/const REVISION\s*=\s*['"]([^'"]+)['"]/)?.[1] || null},
  source_sha256: Object.fromEntries(await Promise.all([
    'site/index.html', 'site/thin-bolted-overlay.mjs', 'scripts/check_thin_bolted_scene.mjs',
    'site/thin-bolted-scene.json.gz', 'site/owner-wood-joints-wj24-scene.json',
  ].map(async p => [p, digest(await readFile(path.join(root, p)))]))),
  limits: 'File-backed loader and real Three.js geometry only; browser launch unavailable. This establishes display bindings/census, not structural resistance or hardware access.'};
const reportPath = path.join(packet, 'viewer-validation-v4.json');
await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify(report, null, 2));
for (const part of loaded.parts) part.geometry?.dispose();
