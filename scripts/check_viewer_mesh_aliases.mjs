import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateMeshAliases, resolveMeshPath, loadMeshAliases} from '../site/mesh-assets.mjs';

const data = validateMeshAliases(JSON.parse(fs.readFileSync('site/mesh-aliases.json', 'utf8')));
for (const [path, canonical] of Object.entries(data.aliases)) {
  assert.equal(resolveMeshPath(path, data), canonical);
  assert.ok(fs.existsSync('site/' + canonical), canonical);
}
for (const path of Object.keys(data.assets)) assert.equal(resolveMeshPath(path, data), path);
assert.throws(() => validateMeshAliases({schema: 'wrong'}), /invalid/);
assert.throws(() => validateMeshAliases({schema: data.schema, assets: {}, aliases: {'../a.stl': 'b.stl'}}), /invalid/);
const originalFetch = globalThis.fetch;
try {
  globalThis.fetch = async () => ({ok: false, status: 404});
  await assert.rejects(loadMeshAliases(), /unavailable \(HTTP 404\)/);
} finally {
  globalThis.fetch = originalFetch;
}
console.log(`Verified ${Object.keys(data.aliases).length} shared mesh URLs and visible map failure.`);
