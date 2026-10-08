// Separate Eoere proposal display; source-bound geometry carries no release.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadThinBoltedScene} from './thin-bolted-overlay.mjs';

export const EOERE_PARENT_SHA256 = '74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf';
export const EOERE_SHARED_SCENE = Object.freeze({url: 'thin-bolted-scene.json.gz',
  sha256: '2ec1dd37dcd867e1748abe4eeb7567e1f62347802964d14bfcb09dd1329e17dc',
  decoded_sha256: 'ec9bac9be2091aa76c24f4df305c020c69f890a11aa3de93e920e18b209c6c70'});
export const EOERE_COUNTS = Object.freeze({timber: 22, panel: 6, bracket: 22, bolt: 500, screw: 66,
  wire: 131, physical_bolt_axes: 100, lights: 132, tnuts: 142, total_visible_parts: 1021});
export const EOERE_MAIN_ANGLE_IDS = Object.freeze([
  'eoere_clip_single_top_left_1', 'eoere_clip_single_top_right_2',
  'eoere_clip_split_top_center_left', 'eoere_clip_split_top_center_right',
  ...['left', 'right'].flatMap(side => ['bottom', 'lower', 'upper'].flatMap(level =>
    [1, 2].map(index => `eoere_clip_horizontal_${level}_${side}_${index}`))),
]);
const SHA = /^[0-9a-f]{64}$/;
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
const KINDS = ['timber', 'bracket', 'bolt'];
const RETAINED_KINDS = {panel: 6, screw: 66, wire: 131, light: 132, tnut: 142};
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];

function require(value, message) {
  if (!value) throw new Error(`Eoere bolted proposal: ${message}`);
}

function vector(value, length) {
  return Array.isArray(value) && value.length === length && value.every(Number.isFinite);
}

function localPath(value) {
  return typeof value === 'string' && !value.startsWith('/') && !value.includes('\\') &&
    !value.includes(':') && !value.split('/').some(part => !part || part === '.' || part === '..');
}

function rigidTransform(matrix) {
  if (!vector(matrix, 16) || ![3, 7, 11].every(index => matrix[index] === 0) || matrix[15] !== 1) return false;
  const [x, y, z] = [matrix.slice(0, 3), matrix.slice(4, 7), matrix.slice(8, 11)];
  const dot = (a, b) => a.reduce((sum, value, index) => sum + value*b[index], 0);
  const det = x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0]);
  return [x, y, z].every(column => Math.abs(dot(column, column)-1) < 1e-7) &&
    Math.max(Math.abs(dot(x, y)), Math.abs(dot(x, z)), Math.abs(dot(y, z)), Math.abs(det-1)) < 1e-7;
}

/** The layout hash is supplied by the source-pinned parent viewer/checker. */
export function validateEoereBoltedScene(data, expectedLayoutSha256) {
  require(SHA.test(expectedLayoutSha256 || ''), 'expected frozen layout hash required');
  require(data?.schema === 'eoere_bolted_review_scene/v1' &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.revision === 'eoere-far-pairs-cleat-corners-v1' &&
    data.status === 'REVISE_UNQUALIFIED_PROPOSAL', 'identity or disposition differs');
  require(FLAGS.every(flag => data.release?.[flag] === false) &&
    Object.values(data.release).every(value => value === false) && data.mechanics_ready === false &&
    data.design?.qualified_for_design === false, 'qualification flags must remain false');
  require(Object.entries(EOERE_SHARED_SCENE).every(([key, value]) => data.shared_scene?.[key] === value) &&
    localPath(data.layout_report?.path) &&
    data.layout_report.sha256 === expectedLayoutSha256 && SHA.test(data.baseline_manifest_sha256 || ''), 'source bindings differ');
  if (data.parent_scene !== undefined) require(data.parent_scene?.url === 'owner-wood-joints-wj24-scene.json' &&
    data.parent_scene.sha256 === EOERE_PARENT_SHA256, 'historical parent source differs');
  require(Object.entries(EOERE_COUNTS).every(([key, value]) => data.counts?.[key] === value), 'declared census differs');
  require(Array.isArray(data.retained_shared_part_names) && data.retained_shared_part_names.length === 477 &&
    new Set(data.retained_shared_part_names).size === 477 &&
    data.retained_shared_part_names.every(name => typeof name === 'string' && name.length), 'retained shared inventory differs');
  if (data.retained_parent_service_names !== undefined) require(Array.isArray(data.retained_parent_service_names) &&
    data.retained_parent_service_names.length === 274 && new Set(data.retained_parent_service_names).size === 274 &&
    data.retained_parent_service_names.every(name => data.retained_shared_part_names.includes(name) &&
      (name.startsWith('light_') || name.startsWith('hold_tnut_'))), 'retained services differ');
  require(Array.isArray(data.solids) && new Set(data.solids.map(row => row.id)).size === data.solids.length &&
    new Set(data.solids.map(row => row.name)).size === data.solids.length, 'duplicate solid identities');
  require(data.mesh_templates && data.triangle_topologies && typeof data.mesh_templates === 'object' &&
    typeof data.triangle_topologies === 'object', 'mesh inventories missing');
  const kinds = new Map(), connections = new Map(), angles = new Map();
  for (const row of data.solids) {
    require(typeof row.name === 'string' && row.name.length && row.id === row.name && row.fabrication &&
      typeof row.fabrication.description === 'string' && row.fabrication.description.length, 'solid metadata missing');
    const kind = row.fabrication.kind;
    require(KINDS.includes(kind), 'unknown solid kind');
    kinds.set(kind, (kinds.get(kind) || 0)+1);
    require(Boolean(row.mesh) !== Boolean(row.template_id), 'solid requires exactly one mesh representation');
    if (row.template_id) require(data.mesh_templates[row.template_id]?.id === row.template_id &&
      rigidTransform(row.transform), 'template missing or transform is not proper rigid');
    if (kind === 'bracket') angles.set(row.id, row);
    if (kind !== 'bolt') continue;
    const f = row.fabrication;
    require(typeof f.connection_name === 'string' && f.connection_name.length && ROLES.includes(f.hardware_role), 'bolt identity or role missing');
    const roles = connections.get(f.connection_name) || new Set();
    require(!roles.has(f.hardware_role), 'duplicate role in one physical shaft');
    roles.add(f.hardware_role); connections.set(f.connection_name, roles);
    require(Array.isArray(f.stack_roles) && f.stack_roles.length === 5 && new Set(f.stack_roles).size === 5 &&
      ROLES.every(role => f.stack_roles.includes(role)), 'stack declaration differs');
  }
  require(KINDS.every(kind => kinds.get(kind) === EOERE_COUNTS[kind]), 'actual solid census differs');
  require(connections.size === EOERE_COUNTS.physical_bolt_axes && [...connections.values()].every(roles =>
    roles.size === 5 && ROLES.every(role => roles.has(role))), 'incomplete physical shaft inventory');
  require(EOERE_MAIN_ANGLE_IDS.every(id => angles.has(id) && angles.get(id).fabrication.duty_id === id.slice(6)), 'main angle identities differ');
  require(Array.isArray(data.factory_angle_holes) && data.factory_angle_holes.length === EOERE_COUNTS.bracket &&
    new Set(data.factory_angle_holes.map(row => row.angle_id)).size === EOERE_COUNTS.bracket, 'factory angle inventory differs');
  const holeIds = new Set(), installedAxes = new Set();
  for (const row of data.factory_angle_holes) {
    require(angles.has(row.angle_id) && Array.isArray(row.holes) && row.holes.length === 8, 'own angle/factory hole census differs');
    const positions = new Set();
    for (const hole of row.holes) {
      require(typeof hole.id === 'string' && hole.id.length && !holeIds.has(hole.id) &&
        ['beam', 'post'].includes(hole.flange) && ['near', 'far'].includes(hole.row) && [-1, 1].includes(hole.transverse) &&
        vector(hole.point_xyz_mm, 3) && vector(hole.direction_xyz, 3) &&
        Math.abs(hole.direction_xyz.reduce((sum, value) => sum+value*value, 0)-1) < 1e-7, 'factory hole metadata differs');
      holeIds.add(hole.id);
      positions.add(`${hole.flange}/${hole.row}/${hole.transverse}`);
      require(hole.row === 'far' ? typeof hole.installed_bolt_axis_id === 'string' && connections.has(hole.installed_bolt_axis_id)
        : hole.installed_bolt_axis_id === null, 'four installed far holes must bind actual shafts; unused near holes stay represented');
      if (hole.row === 'far') installedAxes.add(hole.installed_bolt_axis_id);
    }
    require(positions.size === 8, 'duplicate or omitted factory hole position');
  }
  require(installedAxes.size === 84, 'angle ports must join84 distinct physical shafts; four shared center-header shafts remain single');
  return connections.size;
}

export async function loadEoereBoltedScene(THREE, options) {
  require(localPath(options.url) && SHA.test(options.expectedSha256 || ''), 'local scene and encoded hash required');
  const response = await fetch(options.url);
  require(response.ok, `scene unavailable (HTTP ${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'scene bytes differ from the pinned export');
  let bytes = encoded;
  if (options.url.endsWith('.gz')) {
    require(SHA.test(options.decodedSha256 || '') && typeof DecompressionStream === 'function', 'gzip requires decoded hash and stream decoder');
    bytes = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    require(await sha256(bytes) === options.decodedSha256, 'decoded scene bytes differ');
  } else if (options.decodedSha256 !== undefined) {
    require(options.decodedSha256 === options.expectedSha256, 'plain scene decoded hash differs');
  }
  const data = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  validateEoereBoltedScene(data, options.layoutSha256);
  require(typeof options.baselineText === 'string' &&
    await sha256(new TextEncoder().encode(options.baselineText)) === data.baseline_manifest_sha256, 'baseline manifest differs');
  const shared = await loadThinBoltedScene(THREE, {...options, url: data.shared_scene.url,
    expectedSha256: data.shared_scene.sha256, decodedSha256: data.shared_scene.decoded_sha256});
  const retained = new Set(data.retained_shared_part_names), parts = [];
  const allocated = new Set(shared.parts.map(part => part.geometry).filter(Boolean));
  try {
    for (const part of shared.parts) {
      if (retained.has(part.name)) {
        require(Object.hasOwn(RETAINED_KINDS, part.fabrication.kind), 'retained body belongs to replaced geometry');
        parts.push(part);
      } else { part.geometry?.dispose(); allocated.delete(part.geometry); }
    }
    require(parts.length === 477 && Object.entries(RETAINED_KINDS).every(([kind, count]) =>
      parts.filter(part => part.fabrication.kind === kind).length === count), 'shared panels/screws/wires/services are missing or duplicated');
    if (data.retained_parent_service_names !== undefined) require(parts.filter(part => ['light', 'tnut'].includes(part.fabrication.kind))
      .every(part => data.retained_parent_service_names.includes(part.name)), 'historical service names differ from shared geometry');
    const topologies = new Map();
    for (const [digest, row] of Object.entries(data.triangle_topologies)) {
      require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
        Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count*3, 'invalid topology record');
      const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
      require(await sha256(decoded.bytes) === digest, 'topology bytes differ');
      topologies.set(digest, {...row, indices: decoded.values});
    }
    const templates = new Map();
    for (const [id, row] of Object.entries(data.mesh_templates)) {
      require(id === row.id, 'template identity differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      templates.set(id, geometry); allocated.add(geometry);
    }
    const bounds = shared.bounds_mm.map(point => [...point]);
    for (const row of data.solids) {
      const geometry = row.template_id ? templates.get(row.template_id).clone() : meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry);
      if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
      geometry.computeBoundingBox();
      const b = geometry.boundingBox, dimensions = ['x', 'y', 'z'].map(axis => b.max[axis]-b.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value >= 0), 'part display dimensions differ');
      for (let i = 0; i < 3; i++) {
        const axis = ['x', 'y', 'z'][i];
        require(Number.isFinite(b.min[axis]) && Number.isFinite(b.max[axis]), 'part display bounds differ');
        bounds[0][i] = Math.min(bounds[0][i], b.min[axis]); bounds[1][i] = Math.max(bounds[1][i], b.max[axis]);
      }
      parts.push({name: row.name, geometry, fabrication: {...row.fabrication, dimensions_mm: dimensions,
        layer: 'eoere_bolted_candidate', display_class: 'eoere_bolted_candidate'}});
    }
    for (const geometry of templates.values()) { geometry.dispose(); allocated.delete(geometry); }
    require(parts.length === EOERE_COUNTS.total_visible_parts && new Set(parts.map(part => part.name)).size === parts.length, 'visible inventory differs');
    return {parts, bounds_mm: bounds, design: {...shared.design, ...data.design, qualified_for_design: false},
      meta: {schema: data.schema, candidate: data.candidate, revision: data.revision, status: data.status, census: data.counts,
        source_sha256: options.expectedSha256, decoded_sha256: options.decodedSha256 || options.expectedSha256,
        layout_sha256: options.layoutSha256, shared_parts_reused: 477, shared_geometry_acceptance_transferred: false,
        complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    throw error;
  }
}
