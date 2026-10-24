import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import test from 'node:test';
import {validatePackerFreeResults, applyPackerFreeResults, loadPackerFreeResultsScene,
  PACKER_FREE_RESULTS_ASSET, PACKER_FREE_RESULTS_STATUS} from '../site/eoere-packer-free-results.mjs';
import {PACKER_FREE_MODEL, PACKER_FREE_STATUS, PACKER_FREE_ASSETS} from '../site/eoere-packer-free-overlay.mjs';
import {documentsForModel} from '../site/documentation-links.mjs';

const root = fileURLToPath(new URL('../',import.meta.url));
const hash = raw => createHash('sha256').update(raw).digest('hex');
const raw = readFileSync(path.join(root,PACKER_FREE_RESULTS_ASSET.path)), results = JSON.parse(raw);
const bank = JSON.parse(readFileSync(path.join(root,results.sources.response_bank.path)));
const evaluation = JSON.parse(readFileSync(path.join(root,results.sources.evaluation.path)));

test('the small presentation exactly matches its own public bank and assessment without reading fields', () => {
  assert.equal(hash(raw),PACKER_FREE_RESULTS_ASSET.sha256);
  assert.equal(validatePackerFreeResults(results),results);
  for (const ref of Object.values(results.sources)) assert.equal(hash(readFileSync(path.join(root,ref.path))),ref.sha256);
  assert.deepEqual(results.cases,bank.cases);
  assert.deepEqual(results.load_contract,bank.load_contract); assert.deepEqual(results.load_contract,evaluation.load_contract);
  assert.equal(results.geometry_receipt.sha256,bank.physical_geometry.sha256);
  assert.deepEqual(results.geometry_receipt,evaluation.geometry_receipt);
  assert.equal(results.geometry_sha256,evaluation.physical_geometry.sha256);
  assert.deepEqual(results.analysis_geometry,bank.analysis_geometry);
  assert.deepEqual(results.analysis_geometry,evaluation.analysis_geometry);
  assert.deepEqual(results.declared_vector_references,evaluation.member_vector_maxima);
  assert.equal(results.maximum_gradient_inf_N,bank.maximum_gradient_inf_N);
  assert.equal(results.maximum_gradient_inf_N,evaluation.maximum_gradient_inf_N);
  assert.equal(results.bearing_diagnostic_case_rows,evaluation.bearing_diagnostic_rows.length);
  assert.equal(results.bearing_diagnostic_components,new Set(evaluation.bearing_diagnostic_rows.map(row => row.component)).size);
  assert.equal(results.actual_Cg_adopted,null); assert.equal(results.actual_Cdelta_adopted,null);
  assert.equal(results.complete_connection_capacity,null);
});

for (const [name,change] of [
  ['the preceding packer bank', d => {d.sources.response_bank.sha256 = '41f76a1ab0c66a1e5c7056e572f32f5627a11290ce2ed2f3b7e611a72a4a2393';}],
  ['the preceding physical geometry', d => {d.geometry_sha256 = 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37';}],
  ['a changed applied load', d => {d.load_contract.horizontal_force_N = 250;}],
  ['an added load override', d => {d.load_contract.unrecorded_duration_factor = 1.6;}],
  ['a missing replay admission', d => {d.cases[0].both_independent_replays_admitted = false;}],
  ['duplicated fields', d => {d.cases[1].field.sha256 = d.cases[0].field.sha256;}],
  ['one replay used twice', d => {d.cases[0].independent_plywood_replay.sha256 = d.cases[0].independent_replay.sha256;}],
  ['another case replay path', d => {d.cases[0].independent_replay.path = d.cases[1].independent_replay.path;}],
  ['a relaxed admission gate', d => {d.admission_gate_N = 1e-4;}],
  ['a residual above the retained gate', d => {d.cases[0].gradient_inf_N = 1.01e-5;}],
  ['a stale gradient maximum', d => {d.maximum_gradient_inf_N = 4.505646e-6;}],
  ['a prior vector index', d => {d.declared_vector_references.base_side_left.index = 0.9985001243183798;}],
  ['removed trial bearing disclosures', d => {d.bearing_diagnostic_case_rows = 0;}],
  ['an adopted trial group factor', d => {d.actual_Cg_adopted = 0.5;}],
  ['an invented complete capacity', d => {d.complete_connection_capacity = 2000;}],
  ['fabrication release', d => {d.fabrication_released = true;}],
]) test('own results reject '+name, () => {
  const current = structuredClone(results); change(current); assert.throws(() => validatePackerFreeResults(current));
});

function sceneFixture() {
  return {parts:Array.from({length:1125},(_,n) => ({name:'retained_part_'+n,geometry:{source:n},fabrication:{
    description:'Retained nominal hardware. Matched geometry-specific results pending.'}})),
  design:{key:PACKER_FREE_MODEL,qualified_for_design:false,documents:documentsForModel(PACKER_FREE_MODEL).filter(row => !row.path.endsWith('/evaluation.json'))},
  meta:{status:PACKER_FREE_STATUS,geometry_sha256:results.geometry_sha256,layout_sha256:results.geometry_receipt.sha256,
    provenance_sha256:PACKER_FREE_ASSETS.provenanceSha256,matched_results_pending:true,current_own_response_bank_recorded:false,
    portable_sources:{geometry_receipt:results.geometry_receipt}}};
}

test('the separate presentation keeps every geometry reference and its pending input unchanged', () => {
  const scene = sceneFixture(), view = applyPackerFreeResults(scene,results);
  for (let i=0;i<scene.parts.length;i++) {
    assert.equal(view.parts[i].geometry,scene.parts[i].geometry);
    assert.equal(view.parts[i].name,scene.parts[i].name);
    assert.match(scene.parts[i].fabrication.description,/results pending/);
    assert.match(view.parts[i].fabrication.description,/Own six-case conditional references recorded/);
    assert.doesNotMatch(view.parts[i].fabrication.description,/results pending/);
  }
  assert.equal(scene.meta.status,PACKER_FREE_STATUS); assert.equal(scene.meta.current_own_response_bank_recorded,false);
  assert.equal(view.meta.status,PACKER_FREE_RESULTS_STATUS); assert.equal(view.meta.current_own_response_bank_recorded,true);
  assert.equal(view.meta.matched_results_pending,false); assert.equal(view.meta.geometry_only,false);
  assert.equal(view.meta.portable_sources.response_bank.sha256,results.sources.response_bank.sha256);
  assert.equal(view.meta.portable_sources.evaluation.sha256,results.sources.evaluation.sha256);
  assert.equal(view.meta.actual_Cg_adopted,null); assert.equal(view.meta.actual_Cdelta_adopted,null);
  assert.equal(view.meta.complete_connection_capacity,null); assert.equal(view.meta.fabrication_released,false);
  assert.deepEqual(new Map(view.design.documents.map(row => [row.path,row.label])),
    new Map(documentsForModel(PACKER_FREE_MODEL).map(row => [row.path,row.label])));
  scene.meta.layout_sha256 = 'd9df40fe76e08f008391cb276b8c2136abae09820273b541d10d49b5648d9ef2';
  assert.throws(() => applyPackerFreeResults(scene,results),/unchanged geometry-only loader/);
});

test('the wrapper fetches only its tiny record and forwards geometry options unchanged', async context => {
  const originalFetch = globalThis.fetch, options = {retained:true}, geometry = sceneFixture(), three = {};
  context.after(() => {globalThis.fetch = originalFetch;});
  globalThis.fetch = async input => {
    assert.equal(fileURLToPath(input),path.join(root,PACKER_FREE_RESULTS_ASSET.path));
    return new Response(raw);
  };
  const result = await loadPackerFreeResultsScene(three,options,async (actualThree,actualOptions) => {
    assert.equal(actualThree,three); assert.equal(actualOptions,options); return geometry;
  });
  assert.equal(result.meta.current_response_computed,true);
  globalThis.fetch = async () => new Response(new Uint8Array([0]));
  await assert.rejects(loadPackerFreeResultsScene(three,options,async () => assert.fail('bad record must stop before geometry loading')),/bytes changed/);
});

test('the original geometry modules and data remain byte-identical beside the new layer', () => {
  for (const [file,digest] of Object.entries({
    'site/eoere-packer-free-overlay.mjs':'06ba8389009578561d18ec7a1eb40ddb066d9c2f5b2b44ed52b68226505efd33',
    'site/eoere-packer-free-provenance.json':'6730ce627aa2a44c1048d357b4d36dbdd379127cf75e0f6df0fd1a08a9e57ca0',
    'site/eoere-packer-free-export.json':'e19aa1ac5dacde0d9346dd76ecdf3eb5f24740e8ab321a96d943371d5f4c8944',
    'site/eoere-packer-free-scene.json.gz':'d411401ab67f5d29ce509800fcb0beac0dfed26188b90fc0af76bc05fa2ddd07',
    'scripts/publish_packer_free_viewer.py':'40a74740acd2650a7b5849afa5ce2ec7639d344016966afea537554cce451d5e',
  })) assert.equal(hash(readFileSync(path.join(root,file))),digest,file);
});
