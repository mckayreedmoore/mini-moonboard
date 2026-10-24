import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {loadPackerFreeScene, validatePackerFreeDelta, validatePackerFreeProvenance, PACKER_FREE_MODEL,
  PACKER_FREE_ASSETS, PACKER_FREE_STATUS} from '../site/eoere-packer-free-overlay.mjs';
import {loadStandardStockScene} from '../site/eoere-standard-stock-overlay.mjs';
import {loadMeshAliases, resolveMeshPath} from '../site/mesh-assets.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const hash = raw => createHash('sha256').update(raw).digest('hex');
const provenanceRaw = readFileSync(path.join(site, PACKER_FREE_ASSETS.provenance)), provenance = JSON.parse(provenanceRaw);
const exportRaw = readFileSync(path.join(site, 'eoere-packer-free-export.json')), exported = JSON.parse(exportRaw);
const sceneRaw = readFileSync(path.join(site, 'eoere-packer-free-scene.json.gz')), scene = JSON.parse(gunzipSync(sceneRaw));

test('public assets preserve the frozen geometry-only export and bind the checked receipt', () => {
  assert.equal(hash(provenanceRaw), PACKER_FREE_ASSETS.provenanceSha256);
  assert.equal(hash(exportRaw), 'e19aa1ac5dacde0d9346dd76ecdf3eb5f24740e8ab321a96d943371d5f4c8944');
  assert.equal(hash(sceneRaw), 'd411401ab67f5d29ce509800fcb0beac0dfed26188b90fc0af76bc05fa2ddd07');
  assert.equal(hash(readFileSync(path.join(root, provenance.geometry_receipt.path))), provenance.geometry_receipt.sha256);
  assert.equal(validatePackerFreeProvenance(provenance, exported), provenance);
  assert.equal(validatePackerFreeDelta(scene), scene);
  assert.equal(scene.replacements.length, 1); assert.equal(scene.reuses.length, 42); assert.equal(scene.removals.length, 26);
});

for (const [name, change] of [
  ['a transferred own bank', p => {p.current_own_response_bank_recorded = true;}],
  ['a carried vector reference', p => {p.declared_vector_reference = {index: 0.9985001243183798};}],
  ['a carried diagnostic count', p => {p.diagnostic_case_rows = 15;}],
  ['the packer-containing receipt', p => {p.geometry_receipt.sha256 = 'd9df40fe76e08f008391cb276b8c2136abae09820273b541d10d49b5648d9ef2';}],
  ['packers still present', p => {p.packers_present = true;}],
  ['an old bank document', p => {p.documents[0].path = 'docs/bolted-frame-development/owner-frame-v10/standard-side-stock/response-bank.json';}],
]) test('geometry-only provenance rejects '+name, () => {
  const current = structuredClone(provenance); change(current); assert.throws(() => validatePackerFreeProvenance(current, exported));
});

for (const [name, change] of [
  ['an omitted near beam stack retained', d => {d.removals = d.removals.filter(id => id !== 'v10_top_bolt_001_shaft');}],
  ['unshortened post metadata', d => {d.stack_updates.find(row => row.axis_id === 'eoere_bolt_006').selected_underhead_length_mm = 203.2;}],
  ['a missing shortened shaft mesh', d => {d.reuses = d.reuses.filter(row => row.name !== 'eoere_bolt_006_shaft');}],
  ['a scaled reusable mesh', d => {d.reuses[0].matrix_row_major[0] = 1.1;}],
  ['an inherited force record', d => {d.response_bank = {sha256:'41f76a1ab0c66a1e5c7056e572f32f5627a11290ce2ed2f3b7e611a72a4a2393'};}],
]) test('the frozen geometry contract rejects '+name, () => {
  const current = structuredClone(scene); change(current); assert.throws(() => validatePackerFreeDelta(current));
});

test('the distinct choice preserves the selected baseline, both 116-bolt routes and C13 bytes', () => {
  const html = readFileSync(path.join(site, 'index.html'), 'utf8');
  assert(html.includes("['"+PACKER_FREE_MODEL+"', 'Packer-free 4×6 frame · 112 bolts · own references · development']"));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert(html.includes('const selectedSceneLoader = packerFree ? loadPackerFreeResultsScene : sceneLoader;'));
  assert(html.includes("if (packerFree) document.querySelector('#model-status').textContent = data.meta.status"));
  for (const key of ['eoere-current-frame-development', 'eoere-owner-frame-v10-development'])
    assert(html.includes("['"+key+"', 'Preserved V10 Candidate 13"));
  assert(html.includes("['eoere-standard-4x6-top-and-sides-preview', 'Preserved standard 4×6 packer frame"));
  assert.equal(hash(readFileSync(path.join(site, 'eoere-v10-scene-13.json.gz'))), '32abbcfcd2552d3df189ea35ab8c1c49d738f447e0dca5d1596eae310766b99f');
  assert.equal(hash(readFileSync(path.join(site, 'eoere-standard-stock-scene.json.gz'))), '0d4549a1baa16c3bf5ce5d4c9ce8a02db7687bf94e966965797c987e544abb62');
  const docs = documentsForModel(PACKER_FREE_MODEL);
  const ownResultPaths = ['evaluation.json', 'response-bank.json', 'connection-method-evaluation.json']
    .map(name => 'docs/bolted-frame-development/owner-frame-v10/packer-free/'+name);
  assert.deepEqual(docs.filter(row => !ownResultPaths.includes(row.path)), provenance.documents);
  assert.equal(docs.length, provenance.documents.length + ownResultPaths.length);
  for (const resultPath of ownResultPaths) assert.equal(docs.filter(row => row.path === resultPath).length, 1);
  assert(provenance.documents.every(row => !/response-bank|reference-review|diagnostic/.test(row.path)));
  for (const row of docs) assert(readFileSync(path.join(root, row.path)).length);
});

test('changed asset bytes fail before loading any parent geometry', async context => {
  const originalFetch = globalThis.fetch; let loaded = false;
  context.after(() => {globalThis.fetch = originalFetch;});
  globalThis.fetch = async () => new Response(new Uint8Array([0,1,2]));
  await assert.rejects(loadPackerFreeScene({}, {}, async () => {loaded = true;}), /asset bytes changed/);
  assert.equal(loaded, false);
});

// Reuse the existing geometry sinks without installing Three.js or materializing shared meshes.
const helpers = readFileSync(path.join(root, 'tests/test_eoere_v10_loader.mjs'), 'utf8');
const start = helpers.indexOf('class Matrix4 {'), end = helpers.indexOf("\ntest('the actual V10 loader", start);
assert(start >= 0 && end > start);
const THREE = runInNewContext(helpers.slice(start, end)+'\n({Matrix4, BufferAttribute, BufferGeometry});');

test('the public-only loader composes 1125 parts and removes all parent result metadata', async context => {
  const originalFetch = globalThis.fetch, requests = []; let old, parentMeta;
  context.after(() => {globalThis.fetch = originalFetch;});
  globalThis.fetch = async input => {
    const name = String(input); if (name.startsWith('blob:')) return originalFetch(input);
    assert(!/^[a-z][a-z0-9+.-]*:/i.test(name) || name.startsWith('file:'), 'no network');
    const target = name.startsWith('file:') ? fileURLToPath(input) : path.resolve(site, name);
    assert(target.startsWith(site+path.sep) && /\.json(?:\.gz)?$/.test(target), 'public site JSON only: '+name);
    requests.push(path.relative(site, target)); return new Response(readFileSync(target), {status:200});
  };
  const aliases = await loadMeshAliases(), baselineText = readFileSync(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
  const result = await loadPackerFreeScene(THREE, {baselineText, baselineParts:JSON.parse(baselineText).parts,
    resolveMeshPath:value => resolveMeshPath(value, aliases)}, async (three, options) => {
      const parent = await loadStandardStockScene(three, options); parentMeta = parent.meta;
      old = new Map(parent.parts.map(part => [part.name, {geometry:part.geometry,
        vertices:part.geometry ? hash(new Uint8Array(part.geometry.attributes.position.array.buffer)) : null}]));
      return parent;
    });
  assert.equal(parentMeta.current_own_response_bank_recorded, true);
  assert.equal(result.parts.length, 1125); assert.equal(result.design.key, PACKER_FREE_MODEL);
  assert.equal(result.meta.geometry_sha256, provenance.geometry_sha256); assert.equal(result.meta.provenance_sha256, hash(provenanceRaw));
  assert.equal(result.parts.filter(part => part.fabrication?.kind === 'screw').length, 66);
  assert.equal(result.parts.filter(part => part.fabrication?.kind === 'bracket').length, 24);
  assert.equal(new Set(result.parts.filter(part => part.fabrication?.kind === 'bolt').map(part => part.fabrication.connection_name)).size, 112);
  assert.equal(result.parts.filter(part => part.fabrication?.hardware_role?.startsWith('spacer')).length, 40);
  assert(!result.parts.some(part => ['top_packer_left','top_packer_right'].includes(part.name)));
  assert.equal(result.meta.current_response_computed, false); assert.equal(result.meta.current_own_response_bank_recorded, false);
  assert.equal(result.meta.matched_results_pending, true); assert.equal(result.meta.packers_present, false); assert.equal(result.meta.status, PACKER_FREE_STATUS);
  assert.equal(result.meta.actual_Cg_adopted, null); assert.equal(result.meta.complete_connection_capacity, null);
  for (const key of ['declared_vector_reference','diagnostic_case_rows','diagnostic_components','case_rows','result_contract','response_bank'])
    assert.equal(result.meta[key], undefined, 'parent result metadata must be absent: '+key);
  assert.equal(result.meta.portable_sources.response_bank, undefined);
  assert.equal(result.meta.portable_sources.geometry_receipt.sha256, provenance.geometry_receipt.sha256);
  assert.deepEqual(result.design.documents, provenance.documents);
  const changed = new Set([...scene.replacements, ...scene.reuses].map(row => row.name));
  for (const part of result.parts) {
    if (changed.has(part.name)) assert.notEqual(part.geometry, old.get(part.name).geometry);
    else assert.equal(part.geometry, old.get(part.name).geometry, 'shared unchanged mesh retained: '+part.name);
    assert(!part.geometry?.disposed);
  }
  for (const row of old.values()) if (row.geometry)
    assert.equal(hash(new Uint8Array(row.geometry.attributes.position.array.buffer)), row.vertices, 'source template vertices unchanged');
  for (const id of ['eoere_bolt_006','eoere_bolt_009','eoere_bolt_010','eoere_bolt_013']) {
    const f = result.parts.find(part => part.name === id+'_shaft').fabrication;
    assert.equal(f.selected_underhead_length_mm, 120.65); assert.equal(f.stack_roles.length, 5); assert.equal(f.spacer_piece_count, 0);
  }
  assert(requests.includes('eoere-packer-free-scene.json.gz') && requests.includes('eoere-packer-free-export.json'));
  context.diagnostic('1125 parts, 112 selectable stacks, 66 screws, 24 angles, 40 spacers; one mesh, 42 reuses, 26 removals. All runtime JSON from site/.');
});
