import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import test from 'node:test';
import {gunzipSync} from 'node:zlib';
import {validateV10Scene, validateV10ComposedParts, applyV10StackMetadata} from '../site/eoere-v10-overlay.mjs';
import {meshGeometry, decodeTypedArray} from '../site/wood-joints-overlay.mjs';
import {validateV10Provenance, resolveV10SourceRef, validateV10SceneProvenance,
  isV10RepositoryPath, V10_PROVENANCE_SHA256, V10_SCENE} from '../site/eoere-v10-provenance.mjs';

const provenanceBytes = readFileSync(new URL('../site/eoere-v10-candidate13-provenance.json', import.meta.url));
const provenance = JSON.parse(provenanceBytes);
const sceneBytes = readFileSync(new URL('../site/eoere-v10-scene-13.json.gz', import.meta.url));
const decoded = gunzipSync(sceneBytes), scene = JSON.parse(decoded);
const sha = raw => createHash('sha256').update(raw).digest('hex');

test('the exact frozen Candidate 13 scene and additive provenance are bound', () => {
  assert.equal(sha(provenanceBytes), V10_PROVENANCE_SHA256);
  assert.equal(sha(sceneBytes), V10_SCENE.expectedSha256);
  assert.equal(sha(decoded), V10_SCENE.decodedSha256);
  assert.equal(validateV10Scene(scene, V10_SCENE.layoutSha256), scene);
  assert.equal(validateV10SceneProvenance(scene, provenance), provenance);
  assert.equal(scene.current_response_computed, false);
  assert.equal(provenance.current_own_response_bank_recorded, true);
});

test('original receipt, geometry and clearance resolve without changing frozen references', () => {
  const before = JSON.stringify(scene);
  const receipt = resolveV10SourceRef(scene.layout_report, provenance);
  assert.equal(receipt.encoding, 'identity');
  const geometry = resolveV10SourceRef(scene.geometry_source, provenance);
  assert.equal(geometry.encoding, 'gzip');
  assert.match(geometry.path, /candidate13\/attempt-13\/final-geometry\/geometry\.json\.gz$/);
  assert.equal(geometry.original.sha256, scene.geometry_source.sha256);
  assert.equal(JSON.stringify(scene), before);
});

test('an unmapped source or hash-valid unrelated source cannot replace the candidate geometry', () => {
  assert.throws(() => resolveV10SourceRef({...scene.geometry_source, path: '/foreign/geometry.json'}, provenance), /unmapped/);
  const other = provenance.artifacts.clearance.original;
  const candidate = {...scene, geometry_source: {path: other.path, sha256: other.sha256}};
  assert.throws(() => validateV10SceneProvenance(candidate, provenance), /scene\/source join/);
});

test('foreign parents, wrong patch inventories and overlapping part names fail', () => {
  assert.throws(() => validateV10Scene({...scene, parent_scene: {sha256: 'a'.repeat(64)}}, V10_SCENE.layoutSha256), /parent/);
  assert.throws(() => validateV10SceneProvenance({...scene, additions: []}, provenance), /patch/);
  assert.throws(() => validateV10Scene({...scene, removals: [scene.replacements[0].name]}, V10_SCENE.layoutSha256), /identities/);
});

test('all qualification and physical release flags remain false', () => {
  for (const flag of ['complete_conditional_frame_evaluation', 'complete_joint_qualified',
    'physical_force_bounds_established', 'physical_operations_authorized', 'structural_acceptance',
    'fabrication_released', 'climbing_released']) {
    assert.throws(() => validateV10Provenance({...provenance, [flag]: true}), /claim boundary/);
  }
});

test('relocations cannot escape the repository or silently omit paper evidence', () => {
  for (const path of ['/absolute', '../outside', 'a/../b', 'a/./b', 'a//b', 'C:\\outside', 'a?query', 'a#fragment'])
    assert.equal(isV10RepositoryPath(path), false, path);
  assert.throws(() => validateV10Provenance({...provenance, paper_audit_artifact_paths: []}), /paper roots/);
  const changed = structuredClone(provenance);
  changed.support_files[0].integrated.path = provenance.artifacts.geometry.integrated.path;
  assert.throws(() => validateV10Provenance(changed), /duplicate|target/);
});

test('unchanged heads receive current whole-stack metadata without changing their hardware role or dimensions', () => {
  const selection = scene.stack_updates.find(row => row.axis_id === 'lumber_leg_bolt_left_1');
  const part = {name: 'old_head', fabrication: {kind: 'bolt', connection_name: selection.axis_id,
    hardware_role: 'head', dimensions_mm: [10, 11, 12], stack_roles: ['head']}};
  const result = applyV10StackMetadata([part], scene);
  assert.deepEqual(result[0].fabrication.stack_roles, selection.stack_roles);
  assert.equal(result[0].fabrication.hardware_role, 'head');
  assert.deepEqual(result[0].fabrication.dimensions_mm, [10, 11, 12]);
  assert.equal(result[0].fabrication.actual_parts_verified, false);
  assert.equal(result[0].fabrication.complete_joint_qualified, false);
});

test('composed 116-stack metadata rejects missing or duplicated physical roles', () => {
  const parts = scene.stack_updates.flatMap(selection => selection.stack_roles.map(role => ({
    name: selection.axis_id+'_'+role, fabrication: {kind: 'bolt', connection_name: selection.axis_id,
      hardware_role: role, stack_roles: selection.stack_roles}})));
  parts.push(...Array.from({length: 66}, (_, i) => ({name: 'screw_'+i, fabrication: {kind: 'screw'}})));
  const descriptor = {part_count: parts.length, counts: {bolt_stacks: 116}};
  assert.equal(validateV10ComposedParts(parts, descriptor), parts);
  const duplicate = structuredClone(parts);
  duplicate[1].fabrication.hardware_role = duplicate[0].fabrication.hardware_role;
  assert.throws(() => validateV10ComposedParts(duplicate, descriptor), /duplicate bolt role/);
  const missing = parts.slice(0, -1);
  assert.throws(() => validateV10ComposedParts(missing, {...descriptor, part_count: missing.length}), /screw count/);
});

test('the eight retained cleat nut washers describe the current two-spacer V10 stack', () => {
  const updated = new Set(scene.replacements.map(row => row.name));
  const axes = ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074',
    ...['left', 'right'].flatMap(side => [1, 2].map(n => `cleat_post_bolt_${side}_${n}`))];
  for (const axis of axes) {
    const name = axis+'_nut_washer';
    assert.equal(updated.has(name), false, 'exercise a genuinely retained parent component');
    const part = {name, fabrication: {kind: 'bolt', connection_name: axis, hardware_role: 'nut_washer',
      dimensions_mm: [2, 25, 25], owner_frame_revision: 'eoere-single-spacer-cleat-stacks-v9',
      description: '3/8-16 × 7½-inch cleat stack with one factory spacer'}};
    applyV10StackMetadata([part], scene);
    assert.equal(part.fabrication.owner_frame_revision, scene.revision);
    assert.match(part.fabrication.description, /V10 Candidate 13/);
    assert.match(part.fabrication.description, /2 factory spacer pieces/);
    assert.doesNotMatch(part.fabrication.description, /one factory spacer/);
    assert.equal(part.fabrication.hardware_role, 'nut_washer');
    assert.deepEqual(part.fabrication.dimensions_mm, [2, 25, 25]);
  }
});

test('all 296 changed display meshes decode through the shared helper and retain their frozen CAD sources', () => {
  const record = provenance.artifacts.geometry_raw;
  const geometryBytes = readFileSync(new URL('../'+record.integrated.path, import.meta.url));
  assert.equal(sha(geometryBytes), record.integrated.sha256);
  const original = gunzipSync(geometryBytes);
  assert.equal(sha(original), record.original.sha256);
  const registry = new Map(JSON.parse(original).changed_finished_solids.map(row => [row.id, row]));
  const topologies = new Map();
  for (const [digest, row] of Object.entries(scene.triangle_topologies)) {
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    assert.equal(sha(decoded.bytes), digest);
    topologies.set(digest, {...row, indices: decoded.values});
  }
  // A minimal attribute sink exercises the established decoder without a browser
  // or Three.js installation; normals and WebGL rendering are outside this check.
  const THREE = {BufferAttribute: class {constructor(array, itemSize) {this.array = array;this.itemSize = itemSize;}},
    BufferGeometry: class {setAttribute(name, value) {this[name] = value;} computeVertexNormals() {}}};
  let count = 0;
  for (const row of [...scene.replacements, ...scene.additions]) {
    const source = registry.get(row.name);
    assert(source, 'frozen geometry source missing: '+row.name);
    assert.deepEqual(row.source, {path: source.path, sha256: source.sha256});
    const positions = meshGeometry(THREE, row.mesh, topologies).position.array;
    const bounds = [Infinity, -Infinity, Infinity, -Infinity, Infinity, -Infinity];
    for (let i = 0; i < positions.length; i++) {
      const axis = 2*(i%3);
      bounds[axis] = Math.min(bounds[axis], positions[i]);
      bounds[axis+1] = Math.max(bounds[axis+1], positions[i]);
    }
    for (let i = 0; i < 6; i++) assert(Math.abs(bounds[i]-source.bounds_xyz_mm[i]) < .55,
      'decoded display/CAD bounds differ: '+row.name);
    count++;
  }
  assert.equal(count, 296);
});
