import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {runInNewContext} from 'node:vm';
import path from 'node:path';
import test from 'node:test';
import {loadStandardStockScene, validateStandardStockScene, validateStandardStockProvenance, STANDARD_STOCK_MODEL,
  STANDARD_STOCK_ASSETS} from '../site/eoere-standard-stock-overlay.mjs';
import {loadV10Scene} from '../site/eoere-v10-overlay.mjs';
import {loadMeshAliases, resolveMeshPath} from '../site/mesh-assets.mjs';

const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const hash = raw => createHash('sha256').update(raw).digest('hex');
const provenanceBytes = readFileSync(path.join(site, 'eoere-standard-stock-provenance.json'));
const provenance = JSON.parse(provenanceBytes), status = JSON.parse(readFileSync(path.join(site, 'eoere-standard-stock-status.json')));
const sceneBytes = readFileSync(path.join(site, 'eoere-standard-stock-scene.json.gz')), scene = JSON.parse(gunzipSync(sceneBytes));

test('portable stock assets bind the current geometry and own six-case source summaries', () => {
  assert.equal(hash(provenanceBytes), STANDARD_STOCK_ASSETS.provenanceSha256);
  assert.equal(hash(sceneBytes), provenance.scene.sha256);
  assert.equal(validateStandardStockProvenance(provenance, status), provenance);
  assert.equal(validateStandardStockScene(scene), scene);
  for (const ref of Object.values(provenance.result_sources)) assert.equal(hash(readFileSync(path.join(root, ref.path))), ref.sha256);
  assert.equal(provenance.mesh_sources.length, 11);
  for (const name of ['base_side_left', 'base_side_right']) assert.equal(provenance.mesh_sources.find(row => row.name === name).original_export.sha256,
    'a63ee4273ddbe54eda092f1c175a79a25741562677e06c922af69c0fb6090184');
});

for (const [name, change] of [
  ['the scalar comparison as the active vector criterion', (p, s) => {p.result_contract.declared_vector_reference.index = 1.0149317282; s.declared_vector_reference.index = 1.0149317282;}],
  ['an old bank binding', p => {p.result_sources.response_bank.sha256 = '9a885d4dbfe5ef54fbb0d598e3c30d7d0d7233af67d75b39695b6ccdea066736';}],
  ['a failed independent replay', p => {p.result_contract.case_rows[0].both_independent_replays_admitted = false;}],
  ['duplicated case fields', p => {p.result_contract.case_rows[1].field = p.result_contract.case_rows[0].field;}],
  ['an adopted diagnostic Cg', (_, s) => {s.actual_Cg_adopted = .5;}],
  ['approved custom packers', p => {p.custom_packers_approved = true;}],
]) test('current result metadata rejects '+name, () => {
  const p = structuredClone(provenance), s = structuredClone(status); change(p, s);
  assert.throws(() => validateStandardStockProvenance(p, s));
});

for (const [name, change] of [
  ['a scaled reuse matrix', data => {data.reuses[0].matrix_row_major[0] = 1.1;}],
  ['an unrelated spacer removal', data => {data.removals[0] = 'unrelated_parent_part';}],
  ['old product400 body metadata', data => {data.stack_updates.find(row => row.axis_id === 'rail_rear_bolt_left_1').minimum_body_mm = 72.898;}],
  ['old tip metadata', data => {data.axis_updates[0].tip_projection_beyond_nut_mm = 11.557;}],
]) test('current geometry metadata rejects '+name, () => {const data = structuredClone(scene); change(data); assert.throws(() => validateStandardStockScene(data));});

test('the selector adds a distinct choice while preserving the no-query baseline and C13 aliases', () => {
  const html = readFileSync(path.join(site, 'index.html'), 'utf8');
  assert(html.includes("['"+STANDARD_STOCK_MODEL+"', 'Preserved standard 4×6 packer frame"));
  assert(html.includes("? requestedModel : 'compact-floor-flush-development'"));
  assert(html.includes('const sceneLoader = standardStock ? loadStandardStockScene : v10 ? loadV10Scene'));
  for (const id of ['eoere-current-frame-development', 'eoere-owner-frame-v10-development']) assert(html.includes("['"+id+"', 'Preserved V10 Candidate 13"));
  assert(html.includes("if (standardStock) document.querySelector('#model-status').textContent = data.meta.status"));
  assert.equal(hash(readFileSync(path.join(site, 'eoere-v10-scene-13.json.gz'))), '32abbcfcd2552d3df189ea35ab8c1c49d738f447e0dca5d1596eae310766b99f');
});

// Use the existing geometry sinks; no Three.js installation or copied helper implementation.
const helpers = readFileSync(path.join(root, 'tests/test_eoere_v10_loader.mjs'), 'utf8');
const start = helpers.indexOf('class Matrix4 {'), end = helpers.indexOf("\ntest('the actual V10 loader", start);
assert(start >= 0 && end > start);
const THREE = runInNewContext(helpers.slice(start, end)+'\n({Matrix4, BufferAttribute, BufferGeometry});');

test('the actual portable loader composes 1151 parts using only tracked site JSON and shared mesh paths', async context => {
  const originalFetch = globalThis.fetch, requests = []; let parent;
  context.after(() => {globalThis.fetch = originalFetch;});
  globalThis.fetch = async input => {
    const name = String(input);
    if (name.startsWith('blob:')) return originalFetch(input);
    assert(!/^[a-z][a-z0-9+.-]*:/i.test(name) || name.startsWith('file:'), 'no network');
    const target = name.startsWith('file:') ? fileURLToPath(input) : path.resolve(site, name);
    assert(target.startsWith(site+path.sep) && /\.json(?:\.gz)?$/.test(target), 'no docs fetch, ignored input, STL or materialization: '+name);
    requests.push(path.relative(site, target)); return new Response(readFileSync(target), {status: 200});
  };
  const aliases = await loadMeshAliases(), baselineText = readFileSync(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
  const result = await loadStandardStockScene(THREE, {baselineText, baselineParts: JSON.parse(baselineText).parts,
    resolveMeshPath: value => resolveMeshPath(value, aliases)}, async (three, options) => {
      const loaded = await loadV10Scene(three, options);
      parent = new Map(loaded.parts.map(part => [part.name, {geometry: part.geometry,
        vertices: part.geometry ? hash(new Uint8Array(part.geometry.attributes.position.array.buffer)) : null}]));
      return loaded;
    });
  const changed = new Set([...scene.replacements, ...scene.reuses].map(row => row.name));
  assert.equal(result.parts.length, 1151); assert.equal(result.design.key, STANDARD_STOCK_MODEL);
  assert.equal(result.meta.geometry_sha256, 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37');
  assert.equal(result.meta.current_own_response_bank_recorded, true); assert.equal(result.meta.actual_Cg_adopted, null);
  assert.equal(result.meta.diagnostic_case_rows, 15); assert.equal(result.meta.diagnostic_components, 8);
  assert.equal(result.meta.custom_packers_approved, false); assert.equal(result.meta.physical_release, false);
  assert.equal(result.parts.filter(part => part.fabrication?.kind === 'screw').length, 66);
  assert.equal(result.parts.filter(part => part.fabrication?.kind === 'bracket').length, 24);
  assert.equal(new Set(result.parts.filter(part => part.fabrication?.kind === 'bolt').map(part => part.fabrication.connection_name)).size, 116);
  assert.equal(result.parts.filter(part => part.fabrication?.hardware_role?.startsWith('spacer')).length, 44);
  for (const part of result.parts) {
    if (changed.has(part.name)) assert.notEqual(part.geometry, parent.get(part.name).geometry);
    else assert.equal(part.geometry, parent.get(part.name).geometry, 'unchanged parent mesh retained: '+part.name);
    assert(!part.geometry?.disposed);
  }
  for (const row of parent.values()) if (row.geometry) assert.equal(hash(new Uint8Array(row.geometry.attributes.position.array.buffer)), row.vertices,
    'source template vertex bytes never change');
  assert.equal(result.parts.find(part => part.name === 'top_packer_left').fabrication.stock_disposition, 'CUSTOM UNAPPROVED');
  assert(result.design.documents.some(row => row.path.endsWith('/connection-method-evaluation.json')));
  assert(requests.includes('eoere-standard-stock-scene.json.gz') && requests.includes('eoere-standard-stock-status.json'));
  context.diagnostic('Verified the C13 chain, 11 current payloads, 128 rigid reuses and 16 removals with zero ignored/runtime evidence dependencies.');
});
