// Check the assembled meshes against the preserved parent and revised CAD receipt.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadSelectedHardwareBaseScene, loadSelectedHardwareGridScene} from '../site/eoere-selected-hardware-overlay.mjs';
import {loadFrontPostsBaseScene, loadFrontPostsGridScene, validateFrontPosts} from '../site/eoere-front-posts-4x6-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh ignored output path required');
const assetPath = 'site/eoere-front-posts-4x6-scene.json.gz';
const asset = await readFile(path.join(root, assetPath)), decoded = gunzipSync(asset), patch = JSON.parse(decoded);
const receiptBytes = await readFile(path.join(root, patch.layout_report.path)), receipt = JSON.parse(receiptBytes);
assert.equal(sha(receiptBytes), patch.layout_report.sha256);
assert.equal(receipt.unchanged_bolt_axis_lines, 100); assert.equal(receipt.unchanged_screw_axes, 66);
assert.equal(receipt.changed_finished_solids.length, 50);
assert.equal(receipt.metal_member_intersections_clear, true);
assert.equal(receipt.kicker_screw_backing.length, 4);
assert.ok(receipt.kicker_screw_backing.every(r => r.modeled_wood_body_backing_fraction > .999999));
assert.equal(receipt.service_census.all_clear, true);
assert.equal(receipt.service_census.unbeveled_stock_failures.length, 2);
assert.equal(receipt.service_census.post_service_comparisons, 810);
assert.ok(receipt.service_census.refined_queries.every(r => r.minimum_distance_mm > 3 && r.intersection_volume_mm3 === 0));
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(path.join(root, bundlePath));
const THREE = await import('data:text/javascript;base64,' + Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
const nativeFetch = globalThis.fetch;
globalThis.fetch = async url => {
  if (typeof url === 'string' && url.startsWith('blob:')) return nativeFetch(url);
  assert.ok(typeof url === 'string' && !url.startsWith('/') && !url.includes('..') && !url.includes(':'), 'site-local asset expected');
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const shared = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const options = {...shared, url: path.basename(assetPath), expectedSha256: sha(asset), decodedSha256: sha(decoded), layoutSha256: sha(receiptBytes)};
const parentOptions = {...shared, url: patch.parent_scene.url, expectedSha256: patch.parent_scene.sha256,
  decodedSha256: patch.parent_scene.decoded_sha256, layoutSha256: patch.parent_layout.sha256};
const changedNames = new Set(patch.replacements.map(r => r.name));
const ownAxes = new Set(Object.keys(receipt.axis_overrides));
const nativePath = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/native-geometry-v4.json';
const nativeBytes = await readFile(path.join(root, nativePath));
assert.equal(sha(nativeBytes), receipt.source_sha256[nativePath]);
const nativeParts = new Map(JSON.parse(nativeBytes).parts.map(p => [p.id, p]));
const variants = [];
for (const [variant, oldLoader, loader] of [['base', loadSelectedHardwareBaseScene, loadFrontPostsBaseScene],
  ['extra', loadSelectedHardwareGridScene, loadFrontPostsGridScene]]) {
  const before = await oldLoader(THREE, parentOptions), after = await loader(THREE, options);
  const parts = new Map(after.parts.map(p => [p.name, p]));
  assert.equal(after.parts.length, patch.counts[variant]); assert.equal(parts.size, after.parts.length);
  let reused = 0;
  for (const old of before.parts) {
    const now = parts.get(old.name); assert.ok(now, old.name);
    if (changedNames.has(old.name)) continue;
    assert.deepEqual(now.fabrication, old.fabrication, old.name);
    if (old.geometry) assert.deepEqual(now.geometry.getAttribute('position').array, old.geometry.getAttribute('position').array, old.name);
    else assert.deepEqual(now, old, old.name);
    reused++;
  }
  assert.equal(reused, before.parts.length-46);
  assert.equal(after.parts.filter(p => p.fabrication.kind === 'timber').length, 22);
  assert.equal(after.parts.filter(p => p.fabrication.kind === 'screw').length, 66);
  assert.equal(after.parts.filter(p => p.fabrication.hardware_role?.startsWith('spacer')).length, 12);
  assert.equal(new Set(after.parts.filter(p => p.fabrication.kind === 'bolt').map(p => p.fabrication.connection_name)).size, 100);
  let separateMetalScreens = 0, separateServiceScreens = 0, refinedServiceScreens = 0;
  for (const name of ['base_post_outer_left', 'base_post_outer_right']) {
    const p = parts.get(name), box = p.geometry.boundingBox;
    for (const [axis, size] of [['x', 88.9], ['y', 139.7], ['z', 238.9]])
      assert.ok(Math.abs(box.max[axis]-box.min[axis]-size) < .11, `${name}/${axis}`);
    assert.match(p.fabrication.description, /Solid 4×6/);
    const sourceBounds = receipt.profile_overrides[name].finished.bounds_xyz_mm;
    const cornerX = sourceBounds[0][name.endsWith('left') ? 1 : 0], cornerY = sourceBounds[1][1];
    const vertices = p.geometry.getAttribute('position');
    for (let i = 0; i < vertices.count; i++) {
      const across = name.endsWith('left') ? cornerX-vertices.getX(i) : vertices.getX(i)-cornerX;
      assert.ok(across+cornerY-vertices.getY(i) >= 9.525-.2, 'display mesh must retain the T-nut clearance bevel');
    }
    for (const other of after.parts) {
      if (['tnut', 'light', 'wire'].includes(other.fabrication.kind)) {
        let sb;
        if (other.geometry) {
          other.geometry.computeBoundingBox();
          const b = other.geometry.boundingBox;
          sb = ['x', 'y', 'z'].map(a => [b.min[a], b.max[a]]);
        } else {
          const source = nativeParts.get(other.name);
          assert.ok(source, 'missing native service bounds: ' + other.name);
          sb = source.bounds_xyz_mm;
        }
        const gap = Math.max(...['x', 'y', 'z'].map((a, j) => Math.max(sb[j][0]-box.max[a], box.min[a]-sb[j][1])));
        if (gap > .2) separateServiceScreens++;
        else {
          const proof = receipt.service_census.refined_queries.find(r => r.post === name && r.service === other.name);
          assert.ok(proof && proof.minimum_distance_mm > 3 && proof.intersection_volume_mm3 === 0,
            `service needs a CAD clearance proof: ${name}/${other.name}`);
          refinedServiceScreens++;
        }
      }
      if (!['bolt', 'bracket'].includes(other.fabrication.kind) || ownAxes.has(other.fabrication.connection_name)) continue;
      assert.ok(other.geometry, 'metal geometry required: ' + other.name);
      other.geometry.computeBoundingBox();
      const b = other.geometry.boundingBox;
      const gap = Math.max(...['x', 'y', 'z'].map(a => Math.max(b.min[a]-box.max[a], box.min[a]-b.max[a])));
      assert.ok(gap > .2, `unresolved other-metal proximity: ${name}/${other.name}/${gap}`);
      separateMetalScreens++;
    }
  }
  for (const axis of ownAxes) {
    const stack = after.parts.filter(p => p.fabrication.connection_name === axis);
    assert.equal(stack.length, axis.startsWith('cleat_') ? 7 : 5);
    const roles = new Set(stack.map(p => p.fabrication.hardware_role));
    const selected = receipt.selected_stack_overrides.find(r => r.axis_id === axis);
    for (const p of stack) {
      assert.equal(p.fabrication.selected_hardware_revision, receipt.revision);
      for (const key of ['minimum_body_mm', 'maximum_grip_gaging_mm', 'selected_underhead_length_mm', 'nut_side_spacer_mm'])
        assert.equal(p.fabrication[key], selected[key], `${axis}/${p.name}/${key}`);
      assert.equal(p.fabrication.stack_roles.length, stack.length);
      assert.ok(p.fabrication.stack_roles.every(role => roles.has(role)), 'every advertised stack role must be selectable');
    }
  }
  assert.equal(after.meta.new_response_computed, false);
  assert.equal(after.meta.analysis_pass_transferred, false); assert.equal(after.meta.physical_release, false);
  assert.equal(after.design.qualified_for_design, false);
  assert.equal(refinedServiceScreens, 2);
  variants.push({variant, parts: after.parts.length, reused, separateMetalScreens, separateServiceScreens, refinedServiceScreens});
  for (const p of [...before.parts, ...after.parts]) p.geometry?.dispose();
}
for (const change of [p => {p.analysis_pass_transferred = true;}, p => {p.release.fabrication = true;},
  p => {p.replacements.pop();}, p => {p.replacements[0] = p.replacements[1];}, p => {p.counts.spacers = 8;}]) {
  const bad = structuredClone(patch); change(bad);
  assert.throws(() => validateFrontPosts(bad, sha(receiptBytes)));
}
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadFrontPostsBaseScene(THREE, {...options, [key]: '0'.repeat(64)}));
const files = [assetPath, patch.layout_report.path, 'site/eoere-front-posts-4x6-overlay.mjs',
  'scripts/check_eoere_front_posts_4x6.mjs', bundlePath];
await writeFile(output, JSON.stringify({schema: 'eoere_front_posts_4x6_mesh_check/v1', passed: true, variants,
  source_sha256: Object.fromEntries(await Promise.all(files.map(async f => [f, sha(await readFile(path.join(root, f)))]))),
  mechanics_or_physical_release: false}, null, 2)+'\n', {flag: 'wx'});
console.log(JSON.stringify({passed: true, variants, output}));
