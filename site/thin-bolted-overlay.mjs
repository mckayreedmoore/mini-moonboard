// Separate thinner-frame review model; preserved source viewers retain their guards.
import {loadWoodJointScene, meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';

const PARENT = '74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf';
const LAYOUT = '8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c';
const SHA = /^[0-9a-f]{64}$/;
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
const COUNTS = {timber: 20, panel: 6, bracket: 36, bolt: 350, screw: 66, wire: 131,
  physical_bolt_axes: 70, new_bolt_axes: 58, retained_starting_bolt_axes: 12,
  lights: 132, tnuts: 142, total_visible_parts: 883};
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];

function require(value, message) {
  if (!value) throw new Error(`Thinner bolted model: ${message}`);
}

function rigidTransform(m) {
  if (!Array.isArray(m) || m.length !== 16 || !m.every(Number.isFinite) ||
      ![3, 7, 11].every(i => m[i] === 0) || m[15] !== 1) return false;
  const columns = [m.slice(0, 3), m.slice(4, 7), m.slice(8, 11)];
  const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);
  if (!columns.every(a => Math.abs(dot(a, a) - 1) < 1e-7) ||
      ![[0, 1], [0, 2], [1, 2]].every(([i, j]) => Math.abs(dot(columns[i], columns[j])) < 1e-7)) return false;
  const [x, y, z] = columns;
  return Math.abs(x[0] * (y[1] * z[2] - y[2] * z[1]) -
    x[1] * (y[0] * z[2] - y[2] * z[0]) + x[2] * (y[0] * z[1] - y[1] * z[0]) - 1) < 1e-7;
}

export function validateThinBoltedScene(data) {
  require(data?.schema === 'thin_bolted_review_scene/v1' &&
    data.candidate === 'compact-floor-flush-thin-bolted-development' &&
    data.revision === 'thin-offset-header-rows-shallow-wires-v4-review-model' &&
    data.status === 'REVISE_UNQUALIFIED_PROPOSAL', 'identity or disposition differs');
  require(FLAGS.every(flag => data.release?.[flag] === false) && data.mechanics_ready === false &&
    data.design?.qualified_for_design === false, 'qualification flags must remain false');
  require(data.parent_scene?.url === 'owner-wood-joints-wj24-scene.json' &&
    data.parent_scene.sha256 === PARENT && data.layout_report?.sha256 === LAYOUT &&
    SHA.test(data.baseline_manifest_sha256 || ''), 'source bindings differ');
  require(Object.entries(COUNTS).every(([key, value]) => data.counts?.[key] === value), 'declared census differs');
  require(Array.isArray(data.retained_parent_service_names) && data.retained_parent_service_names.length === 274 &&
    new Set(data.retained_parent_service_names).size === 274 &&
    data.retained_parent_service_names.every(name => typeof name === 'string' &&
      (name.startsWith('light_') || name.startsWith('hold_tnut_'))), 'retained service inventory differs');
  require(Array.isArray(data.solids) && new Set(data.solids.map(row => row.id)).size === data.solids.length &&
    new Set(data.solids.map(row => row.name)).size === data.solids.length, 'duplicate solid identities');
  require(data.mesh_templates && data.triangle_topologies &&
    typeof data.mesh_templates === 'object' && typeof data.triangle_topologies === 'object', 'mesh inventories missing');
  const kinds = new Map(), connections = new Map();
  for (const row of data.solids) {
    require(typeof row.name === 'string' && row.name.length > 0 && row.id === row.name &&
      row.fabrication && typeof row.fabrication.description === 'string', 'solid metadata missing');
    const kind = row.fabrication.kind;
    require(['timber', 'panel', 'bracket', 'bolt', 'screw', 'wire'].includes(kind), 'unknown solid kind');
    kinds.set(kind, (kinds.get(kind) || 0) + 1);
    require(Boolean(row.mesh) !== Boolean(row.template_id), 'solid requires exactly one mesh representation');
    if (row.template_id) require(data.mesh_templates[row.template_id]?.id === row.template_id &&
      rigidTransform(row.transform), 'template missing or transform is not rigid');
    if (kind !== 'bolt') continue;
    const f = row.fabrication;
    require(typeof f.connection_name === 'string' && f.connection_name.length && ROLES.includes(f.hardware_role),
      'bolt identity or role missing');
    const roles = connections.get(f.connection_name) || new Set();
    require(!roles.has(f.hardware_role), 'duplicate role in physical bolt');
    roles.add(f.hardware_role); connections.set(f.connection_name, roles);
    require(Array.isArray(f.stack_roles) && f.stack_roles.length === 5 && new Set(f.stack_roles).size === 5 &&
      ROLES.every(role => f.stack_roles.includes(role)), 'stack declaration differs');
  }
  require(['timber', 'panel', 'bracket', 'bolt', 'screw', 'wire'].every(kind => kinds.get(kind) === COUNTS[kind]),
    'solid census differs');
  require(connections.size === 70 && [...connections.values()].every(roles => roles.size === 5 &&
    ROLES.every(role => roles.has(role))), 'incomplete physical bolt inventory');
  return connections.size;
}

export async function loadThinBoltedScene(THREE, options) {
  require(SHA.test(options.expectedSha256 || ''), 'scene hash missing');
  const response = await fetch(options.url);
  require(response.ok, `scene unavailable (HTTP ${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'scene bytes differ from the pinned export');
  const compressed = options.url.endsWith('.gz');
  let bytes = encoded;
  if (compressed) {
    require(SHA.test(options.decodedSha256 || '') && typeof DecompressionStream === 'function',
      'gzip scene requires a decoded hash and stream decoder');
    bytes = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    require(await sha256(bytes) === options.decodedSha256, 'decoded scene bytes differ');
  }
  const data = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  validateThinBoltedScene(data);
  require(await sha256(new TextEncoder().encode(options.baselineText)) === data.baseline_manifest_sha256,
    'baseline manifest differs');
  const parent = await loadWoodJointScene(THREE, {...options,
    url: data.parent_scene.url, expectedSha256: data.parent_scene.sha256});
  const retained = new Set(data.retained_parent_service_names), parts = [];
  for (const part of parent.parts) {
    if (retained.has(part.name)) {
      require(['light', 'tnut'].includes(part.fabrication.kind), 'retained body is not a light or T-nut');
      parts.push(part);
    } else part.geometry?.dispose();
  }
  require(parts.length === retained.size && ['light', 'tnut'].every(kind =>
    parts.filter(part => part.fabrication.kind === kind).length === (kind === 'light' ? 132 : 142)),
  'shared services are missing');
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
    'invalid topology record');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'topology bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  const templates = new Map(Object.entries(data.mesh_templates).map(([id, row]) =>
    [id, meshGeometry(THREE, row.mesh, topologies)]));
  const bounds = parent.bounds_mm.map(point => [...point]);
  for (const row of data.solids) {
    const geometry = row.template_id ? templates.get(row.template_id).clone() : meshGeometry(THREE, row.mesh, topologies);
    if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
    geometry.computeBoundingBox();
    const b = geometry.boundingBox;
    for (let i = 0; i < 3; i++) {
      const axis = ['x', 'y', 'z'][i];
      bounds[0][i] = Math.min(bounds[0][i], b.min[axis]);
      bounds[1][i] = Math.max(bounds[1][i], b.max[axis]);
    }
    parts.push({name: row.name, geometry, fabrication: {...row.fabrication,
      dimensions_mm: [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z],
      layer: 'thin_bolted_candidate', display_class: 'thin_bolted_candidate'}});
  }
  for (const geometry of templates.values()) geometry.dispose();
  require(parts.length === 883 && new Set(parts.map(part => part.name)).size === parts.length, 'visible inventory differs');
  return {parts, bounds_mm: bounds, design: {...parent.design, ...data.design},
    meta: {revision: data.revision, status: data.status, census: data.counts,
      complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
}
