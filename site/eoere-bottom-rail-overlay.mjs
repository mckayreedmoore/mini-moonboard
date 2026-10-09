// Distinct bottom-rail display; preserved Eoere geometry carries no acceptance.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadEoereBoltedScene, EOERE_COUNTS, EOERE_MAIN_ANGLE_IDS, EOERE_SHARED_SCENE} from './eoere-bolted-overlay.mjs';

export const EOERE_BOTTOM_RAIL_REVISION = 'eoere-bottom-rail-tnut-clearance-v1';
export const EOERE_BOTTOM_RAIL_BASE = Object.freeze({url: 'eoere-review-scene.json.gz',
  sha256: 'c19ed06fc8cf4e2d4387e6ec17edd51ae1f3ffc6c67bd421022dd9e9185cb844',
  decoded_sha256: '8599fca392ccf2ec366ab4c39e4c1d74be89da50167edc7c760e5cb73c524c4a',
  layout_sha256: '05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd'});
export const EOERE_BOTTOM_RAIL_REPLACED_SHARED = Object.freeze(['main_lower_left', 'main_lower_right',
  ...['left', 'right'].flatMap(side => [1, 2].map(index => `fastener_round_panel_lower_${side}_edge_${index}`))]);
export const EOERE_BOTTOM_RAIL_COUNTS = Object.freeze({...EOERE_COUNTS, owned_scene_solids: 550,
  factory_holes: 176, installed_factory_holes: 88});
const SHA = /^[0-9a-f]{64}$/;
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
const OWN_KINDS = {timber: 22, bracket: 22, bolt: 500, panel: 2, screw: 4};
const RETAINED_KINDS = {panel: 4, screw: 62, wire: 131, light: 132, tnut: 142};
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];

function require(ok, message) {
  if (!ok) throw new Error(`Eoere bottom-rail proposal: ${message}`);
}

function localPath(value) {
  return typeof value === 'string' && !value.startsWith('/') && !value.includes('\\') && !value.includes(':') &&
    !value.split('/').some(part => !part || part === '.' || part === '..');
}

function vector(value, length) {
  return Array.isArray(value) && value.length === length && value.every(Number.isFinite);
}

function rigid(matrix) {
  if (!vector(matrix, 16) || ![3, 7, 11].every(i => matrix[i] === 0) || matrix[15] !== 1) return false;
  const [x, y, z] = [matrix.slice(0, 3), matrix.slice(4, 7), matrix.slice(8, 11)];
  const dot = (a, b) => a.reduce((sum, v, i) => sum + v*b[i], 0);
  const det = x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0]);
  return [x, y, z].every(a => Math.abs(dot(a, a)-1) < 1e-7) &&
    [dot(x, y), dot(x, z), dot(y, z), det-1].every(v => Math.abs(v) < 1e-7);
}

function sameSet(first, second) {
  return first.size === second.size && [...first].every(value => second.has(value));
}

export function validateEoereBottomRailScene(data, expectedLayoutSha256) {
  require(SHA.test(expectedLayoutSha256 || ''), 'expected new layout hash required');
  require(data?.schema === 'eoere_bolted_review_scene/v1' && data.revision === EOERE_BOTTOM_RAIL_REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.status === 'REVISE_UNQUALIFIED_PROPOSAL', 'new identity or disposition differs');
  require(FLAGS.every(flag => data.release?.[flag] === false) && Object.values(data.release).every(value => value === false) &&
    data.mechanics_ready === false && data.design?.qualified_for_design === false &&
    data.design.key === 'eoere-bolted-bottom-rail-development', 'qualification flags or design differ');
  require(Object.entries(EOERE_BOTTOM_RAIL_BASE).every(([key, value]) => data.base_scene?.[key] === value) &&
    Object.entries(EOERE_SHARED_SCENE).every(([key, value]) => data.shared_scene?.[key] === value) &&
    localPath(data.layout_report?.path) && data.layout_report.sha256 === expectedLayoutSha256 &&
    SHA.test(data.baseline_manifest_sha256 || ''), 'base, ancestry or new layout binding differs');
  require(Object.entries(EOERE_BOTTOM_RAIL_COUNTS).every(([key, value]) => data.counts?.[key] === value), 'declared census differs');
  const retained = data.retained_shared_part_names;
  require(Array.isArray(retained) && retained.length === 471 && new Set(retained).size === 471 &&
    retained.every(name => typeof name === 'string' && name.length && !EOERE_BOTTOM_RAIL_REPLACED_SHARED.includes(name)),
  'retained partition differs');
  require(Array.isArray(data.retained_parent_service_names) && data.retained_parent_service_names.length === 274 &&
    new Set(data.retained_parent_service_names).size === 274 && data.retained_parent_service_names.every(name =>
      retained.includes(name) && (name.startsWith('light_') || name.startsWith('hold_tnut_'))), 'retained service inventory differs');
  require(Array.isArray(data.solids) && data.solids.length === 550 &&
    new Set(data.solids.map(row => row.id)).size === 550 && new Set(data.solids.map(row => row.name)).size === 550 &&
    data.mesh_templates && typeof data.mesh_templates === 'object' && data.triangle_topologies &&
    typeof data.triangle_topologies === 'object', 'owned mesh inventory missing or duplicated');
  const kinds = new Map(), connections = new Map(), angles = new Map(), changedShared = new Set();
  for (const row of data.solids) {
    require(typeof row.name === 'string' && row.name.length && row.id === row.name && row.fabrication &&
      typeof row.fabrication.description === 'string' && row.fabrication.description.length, 'own solid metadata missing');
    const kind = row.fabrication.kind;
    require(Object.hasOwn(OWN_KINDS, kind), 'unknown owned kind');
    kinds.set(kind, (kinds.get(kind) || 0)+1);
    require(Boolean(row.mesh) !== Boolean(row.template_id), 'one own mesh representation required');
    if (row.template_id) require(data.mesh_templates[row.template_id]?.id === row.template_id && rigid(row.transform),
      'template identity or proper transform differs');
    if (kind === 'panel' || kind === 'screw') {
      require(EOERE_BOTTOM_RAIL_REPLACED_SHARED.includes(row.name) &&
        kind === (row.name.startsWith('main_lower_') ? 'panel' : 'screw'), 'new panel/screw belongs to wrong partition');
      changedShared.add(row.name);
    }
    if (kind === 'bracket') angles.set(row.id, row);
    if (kind !== 'bolt') continue;
    const f = row.fabrication;
    require(typeof f.connection_name === 'string' && f.connection_name.length && ROLES.includes(f.hardware_role) &&
      row.name === `${f.connection_name}_${f.hardware_role}`, 'own shaft name or role differs');
    const roles = connections.get(f.connection_name) || new Set();
    require(!roles.has(f.hardware_role), 'duplicate role in physical shaft');
    roles.add(f.hardware_role); connections.set(f.connection_name, roles);
    require(Array.isArray(f.stack_roles) && sameSet(new Set(f.stack_roles), new Set(ROLES)) && f.stack_roles.length === 5,
      'complete stack declaration required');
  }
  require(Object.entries(OWN_KINDS).every(([kind, count]) => kinds.get(kind) === count) &&
    sameSet(changedShared, new Set(EOERE_BOTTOM_RAIL_REPLACED_SHARED)), 'actual owned partition differs');
  require(connections.size === 100 && [...connections.values()].every(roles => sameSet(roles, new Set(ROLES))),
    'complete 100 physical shaft inventory required');
  require(EOERE_MAIN_ANGLE_IDS.every(id => angles.get(id)?.fabrication.duty_id === id.slice(6)), 'main angle duty identities differ');
  require(Array.isArray(data.factory_angle_holes) && data.factory_angle_holes.length === 22 &&
    new Set(data.factory_angle_holes.map(row => row.angle_id)).size === 22, 'factory angle census differs');
  const holeIds = new Set(), installed = new Set();
  for (const row of data.factory_angle_holes) {
    require(angles.has(row.angle_id) && Array.isArray(row.holes) && row.holes.length === 8, 'own eight-hole angle required');
    const positions = new Set();
    for (const hole of row.holes) {
      require(typeof hole.id === 'string' && hole.id.length && !holeIds.has(hole.id) && ['beam', 'post'].includes(hole.flange) &&
        ['near', 'far'].includes(hole.row) && [-1, 1].includes(hole.transverse) && vector(hole.point_xyz_mm, 3) &&
        vector(hole.direction_xyz, 3) && Math.abs(hole.direction_xyz.reduce((sum, v) => sum+v*v, 0)-1) < 1e-7,
      'factory hole record differs');
      holeIds.add(hole.id); positions.add(`${hole.flange}/${hole.row}/${hole.transverse}`);
      require(hole.row === 'far' ? connections.has(hole.installed_bolt_axis_id) : hole.installed_bolt_axis_id === null,
        'factory installed/unused hole joins differ');
      if (hole.row === 'far') installed.add(hole.installed_bolt_axis_id);
    }
    require(positions.size === 8, 'factory position omitted or duplicated');
  }
  require(holeIds.size === 176 && installed.size === 84, '176 holes / 84 distinct installed angle shafts required');
  return connections.size;
}

export async function loadEoereBottomRailScene(THREE, options) {
  require(localPath(options.url) && SHA.test(options.expectedSha256 || ''), 'local new scene and encoded hash required');
  const response = await fetch(options.url);
  require(response.ok, `scene unavailable (HTTP ${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'new scene bytes differ');
  let bytes = encoded;
  if (options.url.endsWith('.gz')) {
    require(SHA.test(options.decodedSha256 || '') && typeof DecompressionStream === 'function', 'gzip requires decoded hash and decoder');
    bytes = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    require(await sha256(bytes) === options.decodedSha256, 'new decoded scene bytes differ');
  } else if (options.decodedSha256 !== undefined) require(options.decodedSha256 === options.expectedSha256, 'plain decoded hash differs');
  const data = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  validateEoereBottomRailScene(data, options.layoutSha256);
  require(typeof options.baselineText === 'string' && await sha256(new TextEncoder().encode(options.baselineText)) ===
    data.baseline_manifest_sha256, 'baseline manifest differs');
  // The original loader validates its actual source identity and full 1,021-part
  // inventory. No new-revision data is projected into an old scene contract.
  const base = await loadEoereBoltedScene(THREE, {...options, url: EOERE_BOTTOM_RAIL_BASE.url,
    expectedSha256: EOERE_BOTTOM_RAIL_BASE.sha256, decodedSha256: EOERE_BOTTOM_RAIL_BASE.decoded_sha256,
    layoutSha256: EOERE_BOTTOM_RAIL_BASE.layout_sha256});
  const allocated = new Set(base.parts.map(part => part.geometry).filter(Boolean)), parts = [];
  try {
    const expectedRetained = new Set(base.parts.filter(part => Object.hasOwn(RETAINED_KINDS, part.fabrication.kind) &&
      !EOERE_BOTTOM_RAIL_REPLACED_SHARED.includes(part.name)).map(part => part.name));
    const retained = new Set(data.retained_shared_part_names);
    require(sameSet(retained, expectedRetained), 'exact preserved 471-part inventory differs');
    const expectedOwned = new Set(base.parts.filter(part => ['timber', 'bracket', 'bolt'].includes(part.fabrication.kind))
      .map(part => part.name).concat(EOERE_BOTTOM_RAIL_REPLACED_SHARED));
    require(sameSet(new Set(data.solids.map(row => row.name)), expectedOwned), 'new own 550-part identities differ');
    parts.push(...base.parts.filter(part => retained.has(part.name)));
    require(Object.entries(RETAINED_KINDS).every(([kind, count]) => parts.filter(part => part.fabrication.kind === kind).length === count),
      'actual preserved kinds differ');
    const retainedGeometry = new Set(parts.map(part => part.geometry).filter(Boolean));
    for (const geometry of allocated) if (!retainedGeometry.has(geometry)) { geometry.dispose(); allocated.delete(geometry); }
    const topologies = new Map(), templates = new Map();
    for (const [digest, row] of Object.entries(data.triangle_topologies)) {
      require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
        Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count*3,
      'invalid topology record');
      const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
      require(await sha256(decoded.bytes) === digest, 'new topology bytes differ');
      topologies.set(digest, {...row, indices: decoded.values});
    }
    // The six new panel/screw meshes carry authenticated inline indices rather
    // than adding their topologies to the shared-template table. Decode those
    // exact bytes; never invent indices or substitute a parent mesh topology.
    const meshes = [...Object.values(data.mesh_templates).map(row => row.mesh),
      ...data.solids.filter(row => row.mesh).map(row => row.mesh)];
    for (const mesh of meshes) {
      if (mesh?.triangle_indices_base64 === undefined) continue;
      const digest = mesh.triangle_topology_sha256;
      require(SHA.test(digest || '') && ['uint16', 'uint32'].includes(mesh.triangle_component_type) &&
        Number.isInteger(mesh.triangle_count) && mesh.triangle_count > 0, 'invalid inline topology declaration');
      const decoded = decodeTypedArray(mesh.triangle_indices_base64, mesh.triangle_component_type, mesh.triangle_count*3);
      require(await sha256(decoded.bytes) === digest, 'inline topology bytes differ');
      const listed = topologies.get(digest);
      require(!listed || (listed.triangle_count === mesh.triangle_count &&
        listed.triangle_component_type === mesh.triangle_component_type && listed.indices.length === decoded.values.length &&
        listed.indices.every((value, i) => value === decoded.values[i])), 'inline and listed topology differ');
      if (!listed) topologies.set(digest, {triangle_count: mesh.triangle_count,
        triangle_component_type: mesh.triangle_component_type, indices: decoded.values});
    }
    for (const [id, row] of Object.entries(data.mesh_templates)) {
      require(row.id === id, 'new template identity differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      templates.set(id, geometry); allocated.add(geometry);
    }
    require(Array.isArray(base.bounds_mm) && base.bounds_mm.length === 2 && base.bounds_mm.every(p => vector(p, 3)) &&
      base.bounds_mm[0].every((v, i) => v <= base.bounds_mm[1][i]), 'preserved display bounds invalid');
    // Preserved path meshes are loaded by the viewer later. Keep the base's
    // conservative bounds and extend them to include every new display mesh.
    const bounds = base.bounds_mm.map(point => [...point]);
    for (const row of data.solids) {
      const geometry = row.template_id ? templates.get(row.template_id).clone() : meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry);
      if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
      geometry.computeBoundingBox();
      const box = geometry.boundingBox, dimensions = [];
      for (let i = 0; i < 3; i++) {
        const axis = ['x', 'y', 'z'][i], low = box.min[axis], high = box.max[axis];
        require(Number.isFinite(low) && Number.isFinite(high) && high >= low, 'new geometry bounds invalid');
        dimensions.push(high-low); bounds[0][i] = Math.min(bounds[0][i], low); bounds[1][i] = Math.max(bounds[1][i], high);
      }
      parts.push({name: row.name, geometry, fabrication: {...row.fabrication, dimensions_mm: dimensions,
        layer: 'eoere_bottom_rail_candidate', display_class: 'eoere_bottom_rail_candidate'}});
    }
    for (const geometry of templates.values()) { geometry.dispose(); allocated.delete(geometry); }
    require(parts.length === 1021 && new Set(parts.map(part => part.name)).size === 1021, 'complete visible inventory differs');
    return {parts, bounds_mm: bounds, design: {...base.design, ...data.design, qualified_for_design: false},
      meta: {schema: data.schema, candidate: data.candidate, revision: data.revision, status: data.status, census: data.counts,
        source_sha256: options.expectedSha256, decoded_sha256: options.decodedSha256 || options.expectedSha256,
        layout_sha256: options.layoutSha256, base_scene_sha256: EOERE_BOTTOM_RAIL_BASE.sha256,
        shared_parts_reused: 471, own_new_solids: 550, shared_geometry_acceptance_transferred: false,
        bounds_basis: 'preserved conservative display bounds extended by all new geometry',
        complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    throw error;
  }
}
