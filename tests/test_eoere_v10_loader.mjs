import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync, readFileSync} from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import {fileURLToPath, pathToFileURL} from 'node:url';

// Locate the repository from either tests/ or this unapplied proposal folder.
let root = path.dirname(fileURLToPath(import.meta.url));
while (!existsSync(path.join(root, 'site/eoere-v10-overlay.mjs'))) {
  const parent = path.dirname(root);
  assert.notEqual(parent, root, 'V10 repository root missing');
  root = parent;
}
const siteRoot = path.join(root, 'site');
const {loadV10Scene} = await import(pathToFileURL(path.join(siteRoot, 'eoere-v10-overlay.mjs')));
const {loadMeshAliases, resolveMeshPath} = await import(pathToFileURL(path.join(siteRoot, 'mesh-assets.mjs')));
const {V10_SCENE, V10_PROVENANCE_SHA256} = await import(pathToFileURL(path.join(siteRoot, 'eoere-v10-provenance.mjs')));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

// These implement only the geometry operations the actual loader chain uses.
// Vertices, source hashes, topology decoding, transforms, bounds, composition,
// and disposal are exercised. Normals and spheres are not rendering tests.
class Matrix4 {
  set(...values) {this.values = values; return this;}
  fromArray(values) {
    this.values = Array.from({length: 16}, (_, i) => values[(i % 4)*4 + Math.floor(i/4)]);
    return this;
  }
}
class BufferAttribute {
  constructor(array, itemSize) {this.array = array; this.itemSize = itemSize;}
}
class BufferGeometry {
  constructor() {this.attributes = {}; this.disposed = false;}
  setAttribute(name, attribute) {this.attributes[name] = attribute; return this;}
  computeVertexNormals() {}
  computeBoundingSphere() {}
  computeBoundingBox() {
    const positions = this.attributes.position.array;
    const minimum = [Infinity, Infinity, Infinity], maximum = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < positions.length; i++) {
      const axis = i % 3;
      minimum[axis] = Math.min(minimum[axis], positions[i]);
      maximum[axis] = Math.max(maximum[axis], positions[i]);
    }
    const vector = coordinates => Object.fromEntries(['x', 'y', 'z'].map((name, i) => [name, coordinates[i]]));
    this.boundingBox = {min: vector(minimum), max: vector(maximum)};
  }
  clone() {
    const result = new BufferGeometry();
    for (const [name, attribute] of Object.entries(this.attributes))
      result.attributes[name] = new BufferAttribute(attribute.array.slice(), attribute.itemSize);
    return result;
  }
  applyMatrix4(matrix) {
    const positions = this.attributes.position.array, values = matrix.values;
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i], y = positions[i+1], z = positions[i+2];
      positions[i] = values[0]*x + values[1]*y + values[2]*z + values[3];
      positions[i+1] = values[4]*x + values[5]*y + values[6]*z + values[7];
      positions[i+2] = values[8]*x + values[9]*y + values[10]*z + values[11];
    }
    return this;
  }
  translate(x, y, z) {
    return this.applyMatrix4(new Matrix4().set(1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z, 0, 0, 0, 1));
  }
  dispose() {this.disposed = true;}
}

test('the actual V10 loader composes the canonical V9 parent into the complete current scene', async context => {
  const originalFetch = globalThis.fetch, requests = [];
  context.after(() => {globalThis.fetch = originalFetch;});
  globalThis.fetch = async input => {
    const name = String(input);
    if (name.startsWith('blob:')) {
      // An existing gzip adapter uses a temporary in-memory object URL.
      requests.push({kind: 'blob'});
      return originalFetch(input);
    }
    assert.ok(!/^[a-z][a-z0-9+.-]*:/i.test(name) || name.startsWith('file:'), 'network access is forbidden');
    const target = name.startsWith('file:') ? fileURLToPath(name) : path.resolve(siteRoot, name);
    const relative = path.relative(siteRoot, target);
    assert.ok(relative && !path.isAbsolute(relative) && !relative.split(path.sep).includes('..'), 'fetch escapes site');
    assert.match(relative, /\.json(?:\.gz)?$/, 'the composition check must not materialize STL assets');
    const bytes = readFileSync(target);
    requests.push({kind: 'file', path: 'site/'+relative.split(path.sep).join('/'), sha256: sha(bytes)});
    return new Response(bytes, {status: 200});
  };
  const aliases = await loadMeshAliases();
  const baselineText = readFileSync(path.join(siteRoot, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
  const scene = await loadV10Scene({BufferGeometry, BufferAttribute, Matrix4}, {
    baselineText, baselineParts: JSON.parse(baselineText).parts,
    resolveMeshPath: name => resolveMeshPath(name, aliases),
  });

  assert.equal(scene.parts.length, 1167);
  assert.equal(new Set(scene.parts.map(part => part.name)).size, 1167);
  const countRole = role => scene.parts.filter(part => part.fabrication?.hardware_role === role).length;
  assert.equal(countRole('shaft'), 116);
  assert.equal(countRole('head'), 116);
  assert.equal(countRole('nut'), 116);
  assert.equal(countRole('head_washer') + countRole('nut_washer'), 232);
  assert.equal(scene.parts.filter(part => part.fabrication?.hardware_role?.startsWith('spacer')).length, 60);
  assert.equal(scene.parts.filter(part => part.fabrication?.kind === 'screw').length, 66);
  const stackRoles = new Map();
  for (const part of scene.parts) {
    const fabrication = part.fabrication;
    if (fabrication?.kind !== 'bolt') continue;
    if (!stackRoles.has(fabrication.connection_name)) stackRoles.set(fabrication.connection_name, []);
    stackRoles.get(fabrication.connection_name).push(fabrication.hardware_role);
  }
  assert.equal(stackRoles.size, 116);
  for (const roles of stackRoles.values()) {
    assert.equal(new Set(roles).size, roles.length);
    for (const role of ['shaft', 'head', 'head_washer', 'nut_washer', 'nut']) assert.ok(roles.includes(role));
  }
  const geometryParts = scene.parts.filter(part => part.geometry);
  assert.ok(geometryParts.length > 296, 'unchanged parent meshes must remain in the composition');
  assert.deepEqual(geometryParts.filter(part => part.geometry.disposed).map(part => part.name), []);
  assert.ok(scene.bounds_mm.every(row => row.length === 3 && row.every(Number.isFinite)));

  const v9 = requests.filter(row => row.path === 'site/eoere-single-spacer-scene.json');
  assert.deepEqual(v9, [{kind: 'file', path: 'site/eoere-single-spacer-scene.json',
    sha256: '250f8fb4e6fc965ebf77dc9a5822ece646a3163fb85878d15c265673275f4058'}]);
  const provenance = JSON.parse(readFileSync(path.join(siteRoot, 'eoere-v10-candidate13-provenance.json')));
  assert.equal(scene.design.key, 'eoere-owner-frame-v10-development');
  assert.equal(scene.design.qualified_for_design, false);
  assert.deepEqual(scene.design.documents, provenance.documents);
  for (const relative of ['geometry-receipt-13.json', 'response-bank-13.json', 'packet-13-complete/readiness.json'])
    assert.ok(scene.design.documents.some(row => row.path === 'docs/bolted-frame-development/owner-frame-v10/candidate13/'+relative));
  assert.ok(scene.design.documents.every(row => row.path.startsWith('docs/') && !row.path.includes('..')));
  assert.equal(scene.meta.revision, 'eoere-candidate13-side-depth-v10');
  assert.equal(scene.meta.source_sha256, V10_SCENE.expectedSha256);
  assert.equal(scene.meta.layout_sha256, V10_SCENE.layoutSha256);
  assert.equal(scene.meta.provenance_sha256, V10_PROVENANCE_SHA256);
  assert.deepEqual(scene.meta.counts, {Hillman_axes: 66, angles: 24, bolt_stacks: 116,
    occupied_parts: 1167, panels: 6, plywood_cleats: 4, sawn_members: 22, spacer_pieces: 60});
  assert.equal(scene.meta.current_response_computed, false);
  assert.equal(scene.meta.current_own_response_bank_recorded, true);
  assert.equal(scene.meta.analysis_pass_transferred, false);
  assert.equal(scene.meta.physical_release, false);
  assert.equal(scene.meta.complete_joint_acceptance, false);
  assert.equal(scene.meta.planning_mass_kg, null);
  assert.equal(scene.meta.portable_sources.geometry_receipt.path,
    'docs/bolted-frame-development/owner-frame-v10/candidate13/geometry-receipt-13.json');
  assert.equal(scene.meta.portable_sources.geometry.encoding, 'gzip');
  assert.equal(scene.meta.portable_sources.clearance.encoding, 'identity');
  context.diagnostic('Composed '+scene.parts.length+' parts through '+requests.length+' local/object-URL fetches; no browser or STL load.');
});
