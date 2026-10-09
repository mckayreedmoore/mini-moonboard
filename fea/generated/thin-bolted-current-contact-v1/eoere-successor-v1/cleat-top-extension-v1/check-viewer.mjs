// Exercise the isolated draft with real Three.js; shared site files stay frozen.
import assert from 'node:assert/strict';
import {createHash, webcrypto} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadAdjustedFrameScene, load2026AdjustmentsScene} from '../../../../../site/eoere-2026-adjustments-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = process.cwd(), site = path.join(root, 'site');
const packet = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-top-extension-v1';
const output = process.argv[2]; assert.ok(output, 'fresh receipt path required');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const modulePath = path.join(packet, 'eoere-cleat-extension-overlay.mjs');
const moduleBytes = await readFile(modulePath);
// Resolve its two future site-local imports without installing a draft in site/.
const executableSource = moduleBytes.toString().replaceAll("from './wood-joints-overlay.mjs'",
  `from '${pathToFileURL(path.join(site, 'wood-joints-overlay.mjs')).href}'`).replaceAll("from './eoere-2026-adjustments-overlay.mjs'",
  `from '${pathToFileURL(path.join(site, 'eoere-2026-adjustments-overlay.mjs')).href}'`);
const {loadExtendedCleatBaseScene, loadExtendedCleat2026Scene, validateCleatExtension} =
  await import('data:text/javascript;base64,' + Buffer.from(executableSource).toString('base64'));
const geometryBytes = await readFile(path.join(packet, 'cad-v1/geometry.json'));
const geometry = JSON.parse(geometryBytes);
const asset = await readFile(path.join(packet, 'cad-v1/scene.json.gz'));
const decoded = gunzipSync(asset), patch = JSON.parse(decoded);
assert.equal(sha(geometryBytes), '01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d');
assert.equal(sha(asset), 'ae6315463f0482597075a769ad3ee55630b4c8b430c2ae93137c5232cc6dbb54');
assert.equal(sha(decoded), '6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6');
validateCleatExtension(patch, sha(geometryBytes));
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(bundlePath);
const THREE = await import('data:text/javascript;base64,' + Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
const nativeFetch = globalThis.fetch;
globalThis.fetch = async url => {
  if (typeof url === 'string' && url.startsWith('blob:')) return nativeFetch(url);
  assert.equal(typeof url, 'string');
  assert.ok(!url.startsWith('/') && !url.includes('..') && !url.includes(':'), 'site-local asset expected');
  return new Response(url === 'cleat-extension-fixture.json.gz' ? asset : await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const shared = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const result = [];
for (const variant of ['base', 'extra']) {
  const binding = patch.parent_scenes[variant];
  const parent = await (variant === 'base' ? loadAdjustedFrameScene : load2026AdjustmentsScene)(THREE, {...shared,
    url: binding.url, expectedSha256: binding.sha256, decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const current = await (variant === 'base' ? loadExtendedCleatBaseScene : loadExtendedCleat2026Scene)(THREE, {...shared,
    url: 'cleat-extension-fixture.json.gz', expectedSha256: sha(asset), decodedSha256: sha(decoded), layoutSha256: sha(geometryBytes)});
  const byName = new Map(current.parts.map(part => [part.name, part]));
  let retained = 0;
  for (const old of parent.parts) {
    const now = byName.get(old.name); assert.ok(now, old.name);
    if (patch.replacements.some(row => row.name === old.name)) {
      assert.notDeepEqual(now.geometry.getAttribute('position').array, old.geometry.getAttribute('position').array);
      const b = now.geometry.boundingBox;
      assert.ok(Math.abs(b.max.z - 500.8860828293809) < .1);
      assert.ok(Math.abs(b.max.x - b.min.x - 38.1) < .1);
      assert.ok(Math.abs(b.max.y - b.min.y - 139.7) < .1);
      assert.ok(Math.abs(b.min.z - 139.7) < .1);
    } else {
      assert.deepEqual(now.fabrication, old.fabrication, old.name);
      if (old.geometry) assert.deepEqual(now.geometry.getAttribute('position').array, old.geometry.getAttribute('position').array, old.name);
      else assert.deepEqual(now, old, old.name);
      retained++;
    }
  }
  assert.equal(retained, patch.counts[variant].total_visible_parts - 2);
  assert.equal(current.parts.length, variant === 'base' ? 1021 : 1380);
  assert.equal(new Set(current.parts.filter(part => part.fabrication.kind === 'bolt').map(part => part.fabrication.connection_name)).size, 100);
  assert.equal(current.parts.filter(part => part.fabrication.kind === 'screw').length, 66);
  assert.equal(current.parts.filter(part => part.fabrication.kind === 'wire').length, variant === 'base' ? 131 : 250);
  assert.equal(current.parts.filter(part => part.fabrication.kind === 'light').length, variant === 'base' ? 132 : 252);
  assert.equal(current.meta.analysis_pass_transferred, false);
  assert.equal(current.meta.complete_joint_acceptance, false);
  assert.equal(current.meta.physical_release, false);
  assert.equal(current.design.qualified_for_design, false);
  result.push({variant, total: current.parts.length, unchanged_parts: retained, replacement_cleats: 2});
  for (const group of [parent, current]) for (const part of group.parts) part.geometry?.dispose();
}
const controls = [
  ['missing cleat', data => data.replacements.pop()],
  ['extra cleat', data => data.replacements.push(structuredClone(data.replacements[0]))],
  ['wrong cleat', data => {data.replacements[0].name = 'base_side_left';}],
  ['wrong base parent', data => {data.parent_scenes.base.sha256 = '0'.repeat(64);}],
  ['wrong extra parent', data => {data.parent_scenes.extra.sha256 = '0'.repeat(64);}],
  ['changed census', data => {data.counts.extra.wire = 131;}],
  ['physical release', data => {data.release.fabrication = true;}],
  ['mechanics transfer', data => {data.analysis_pass_transferred = true;}],
  ['not geometry-only', data => {data.mechanics_ready = true;}],
  ['missing body restriction', data => {data.only_two_cleat_bodies_changed = false;}]
];
for (const [name, mutate] of controls) {
  const control = structuredClone(patch); mutate(control);
  assert.throws(() => validateCleatExtension(control, sha(geometryBytes)), undefined, name);
}
const receipt = {schema: 'eoere_extended_cleats_real_three_check/v1', status: 'PASS_DISPLAY_AND_FROZEN_PARENT_BINDINGS_ONLY',
  source_sha256: {[modulePath]: sha(moduleBytes), [`${packet}/cad-v1/geometry.json`]: sha(geometryBytes),
    [`${packet}/cad-v1/scene.json.gz`]: sha(asset), [bundlePath]: sha(bundle),
    [`${packet}/check-viewer.mjs`]: sha(await readFile(path.join(packet, 'check-viewer.mjs')))},
  import_resolution: 'Two draft-relative site imports resolved to the exact existing site modules; draft bytes preserved.',
  variants: result, rejected_guards: controls.map(([name]) => name), mechanics_acceptance: false, physical_release: false,
  node_version: process.version, command: process.argv};
await writeFile(output, JSON.stringify(receipt, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({output, sha256: sha(await readFile(output)), ...receipt}, null, 2));
