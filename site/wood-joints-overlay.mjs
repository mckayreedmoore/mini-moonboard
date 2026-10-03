// Source-bound display adapter. Geometry stays in the source's global millimeter frame.
const REVIEWED = 'owner_wood_joints_design_review_scene/v1';
const PROPOSAL = 'wood_joint_working_proposal_scene/v1';
const MANIFEST_SHA = '4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0';
const SHA = /^[0-9a-f]{64}$/i;
const CLASSES = new Set(['finished_host', 'candidate_part', 'candidate_hardware', 'panel_replacement', 'electrical_replacement']);
const CENSUS = {bodies: 50, blocks: 24, bolts: 108, nuts: 108, washers: 216, panel_kicker_screws: 66};

function require(value, message) {
  if (!value) throw new Error(`Wood-joint scene: ${message}`);
}

async function sha256(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

function vector(value, length) {
  return Array.isArray(value) && value.length === length && value.every(Number.isFinite);
}

function localPath(path) {
  return typeof path === 'string' && !path.startsWith('/') && !path.includes('\\') &&
    !path.includes(':') && !path.split('/').some(part => !part || part === '.' || part === '..');
}

function decodeTypedArray(base64, type, count) {
  require(typeof base64 === 'string' && Number.isInteger(count) && count >= 0, 'invalid encoded array');
  const types = {int16: [Int16Array, 'getInt16', 2], int32: [Int32Array, 'getInt32', 4],
    uint16: [Uint16Array, 'getUint16', 2], uint32: [Uint32Array, 'getUint32', 4]};
  require(Object.hasOwn(types, type), 'unsupported component type');
  const [ArrayType, getter, size] = types[type];
  const bytes = Uint8Array.from(atob(base64), character => character.charCodeAt(0));
  require(bytes.length === count * size, 'encoded component length differs');
  const view = new DataView(bytes.buffer), values = new ArrayType(count);
  for (let i = 0; i < count; i++) values[i] = view[getter](i * size, true);
  return {bytes, values};
}

function meshGeometry(THREE, mesh, topologies) {
  require(mesh?.encoding === 'base64_typed_arrays_le_v1' && vector(mesh.bounds_xyz_mm, 6) &&
    ['int16', 'int32'].includes(mesh.vertex_component_type) &&
    ['uint16', 'uint32'].includes(mesh.triangle_component_type) &&
    Number.isInteger(mesh.vertex_count) && mesh.vertex_count > 0 &&
    Number.isInteger(mesh.triangle_count) && mesh.triangle_count > 0 &&
    mesh.vertex_quantization_mm === 0.1 && Number.isFinite(mesh.vertex_max_euclidean_error_mm) &&
    mesh.vertex_max_euclidean_error_mm >= 0 && mesh.vertex_max_euclidean_error_mm < 0.5,
  'invalid quantized display mesh');
  const bounds = mesh.bounds_xyz_mm;
  require([0, 2, 4].every(i => bounds[i] <= bounds[i + 1]), 'invalid mesh bounds');
  const quantized = decodeTypedArray(mesh.vertices_base64, mesh.vertex_component_type, mesh.vertex_count * 3).values;
  const vertices = new Float32Array(quantized.length);
  for (let i = 0; i < vertices.length; i++) {
    vertices[i] = quantized[i] * mesh.vertex_quantization_mm;
    const axis = 2 * (i % 3), margin = mesh.vertex_quantization_mm / 2 + 1e-4;
    require(Number.isFinite(vertices[i]) && vertices[i] >= bounds[axis] - margin &&
      vertices[i] <= bounds[axis + 1] + margin, 'display vertex lies outside source bounds');
  }
  const topology = topologies.get(mesh.triangle_topology_sha256);
  require(topology && topology.triangle_count === mesh.triangle_count &&
    topology.triangle_component_type === mesh.triangle_component_type, 'missing or mismatched topology');
  require(topology.indices.every(index => index < mesh.vertex_count), 'topology references a missing vertex');
  // Expand triangles exactly as the separate viewer does to preserve its display normals.
  const positions = new Float32Array(topology.indices.length * 3);
  for (let i = 0; i < topology.indices.length; i++) {
    const offset = topology.indices[i] * 3;
    positions.set(vertices.subarray(offset, offset + 3), i * 3);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function validateScene(data) {
  require([REVIEWED, PROPOSAL].includes(data?.schema), 'unsupported schema');
  require(data.candidate === 'compact-floor-flush-wood-joints-development' &&
    data.baseline === 'compact-floor-flush-kerf-right', 'candidate or baseline differs');
  for (const flag of ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
    'fabrication_released', 'structural_released', 'climbing_released']) {
    require(data[flag] === false, `${flag} must remain false`);
  }
  require(data.release && Object.values(data.release).every(value => value === false), 'release flags differ');
  require(data.display_mesh_encoding?.encoding === 'base64_typed_arrays_le_v1' &&
    data.display_mesh_encoding.vertex_quantization_mm === 0.1 &&
    data.display_mesh_encoding.tessellation_tolerance_mm === 0.5 &&
    data.display_mesh_encoding.triangle_topologies_deduplicated === true &&
    data.display_mesh_encoding.cad_geometry_modified === false, 'display encoding declaration differs');
  require(Array.isArray(data.solids) && data.solids.every(row => typeof row.id === 'string' &&
    typeof row.name === 'string' && CLASSES.has(row.display_class)) &&
    new Set(data.solids.map(row => row.id)).size === data.solids.length, 'invalid or duplicate solid identities');
  require(data.triangle_topologies && Object.keys(data.triangle_topologies).length ===
    data.display_mesh_encoding.unique_triangle_topology_count, 'topology census differs');
  require(Array.isArray(data.hidden_baseline_visual_names) &&
    new Set(data.hidden_baseline_visual_names).size === data.hidden_baseline_visual_names.length,
  'hidden baseline identities differ');
  if (data.schema === PROPOSAL) {
    require(data.proposal_binding?.manifest_sha256 === MANIFEST_SHA &&
      localPath(data.proposal_binding.manifest_path), 'working proposal manifest binding differs');
    require(Object.entries(CENSUS).every(([key, value]) => data.census?.[key] === value), 'working proposal census differs');
    require(data.planning_mass_kg == null || (Number.isFinite(data.planning_mass_kg) && data.planning_mass_kg > 0),
      'invalid declared planning mass');
  } else {
    require(data.layout_status === 'DESIGN_REVIEW' && data.model_inventory &&
      Object.keys(data.model_inventory.candidate_axes || {}).length === 92 &&
      data.model_inventory.frame_bolts?.length === 12 &&
      data.model_inventory.panel_screw_axis_count === 66, 'reviewed inventory differs');
  }
}

function fabricationFor(row, inventory) {
  const supplied = row.fabrication || {}, bounds = row.mesh.bounds_xyz_mm;
  const hardware = row.display_class === 'candidate_hardware';
  const electrical = row.display_class === 'electrical_replacement';
  const kind = hardware ? (supplied.kind === 'screw' ? 'screw' : 'bolt') :
    electrical ? (row.id.startsWith('wire_') ? 'wire' : 'light') :
      row.display_class === 'panel_replacement' ? 'panel' : 'timber';
  const category = {bolt: 'bolts', screw: 'screws', wire: 'wiring', light: 'lights', panel: 'panels', timber: 'timber'}[kind];
  const dimensions = supplied.dimensions_mm || [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]];
  require(vector(dimensions, 3) && dimensions.every(value => value >= 0), 'invalid part dimensions');
  const result = {...supplied, kind, category, dimensions_mm: dimensions,
    layer: row.display_class, display_class: row.display_class, wood_joint_overlay: true,
    description: supplied.description || `${row.role || row.display_class}; ${row.visual_status || 'source display mesh'}; dimensions describe the display envelope; no fabrication or structural release`,
    clearance_status: supplied.clearance_status || 'Development geometry; NOT build-ready'};
  if (hardware) {
    const axis = supplied.connection_name || row.axis_id;
    const role = supplied.hardware_role || row.hardware_role || row.role?.split('/').at(-1);
    require(typeof axis === 'string' && axis.length && typeof role === 'string' && role.length, 'hardware identity is missing');
    result.connection_name = axis;
    result.hardware_role = role;
    result.stack_roles = supplied.stack_roles || inventory?.candidate_axes?.[axis]?.installed_role_ids;
  }
  return result;
}

function displayBounds(data, manifest) {
  if (data.bounds_mm !== undefined) {
    require(Array.isArray(data.bounds_mm) && data.bounds_mm.length === 2 &&
      data.bounds_mm.every(point => vector(point, 3)) &&
      data.bounds_mm[0].every((value, i) => value <= data.bounds_mm[1][i]), 'invalid scene bounds');
    return data.bounds_mm;
  }
  require(Array.isArray(manifest.bounds_mm) && manifest.bounds_mm.length === 2 &&
    manifest.bounds_mm.every(point => vector(point, 3)), 'baseline bounds are missing');
  const bounds = manifest.bounds_mm.map(point => [...point]);
  for (const row of data.solids) for (let i = 0; i < 3; i++) {
    bounds[0][i] = Math.min(bounds[0][i], row.mesh.bounds_xyz_mm[2 * i]);
    bounds[1][i] = Math.max(bounds[1][i], row.mesh.bounds_xyz_mm[2 * i + 1]);
  }
  return bounds;
}

/** Baseline path parts carry expected_sha256; callers must authenticate bytes before parsing STL. */
export async function loadWoodJointScene(THREE, {url, expectedSha256, baselineParts, baselineText, resolveMeshPath}) {
  require(SHA.test(expectedSha256 || '') && typeof baselineText === 'string' &&
    Array.isArray(baselineParts) && typeof resolveMeshPath === 'function', 'loader inputs are incomplete');
  const response = await fetch(url);
  require(response.ok, `scene unavailable (HTTP ${response.status})`);
  const bytes = await response.arrayBuffer();
  require(await sha256(bytes) === expectedSha256.toLowerCase(), 'scene bytes differ from the pinned export');
  const data = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  validateScene(data);
  require(SHA.test(data.baseline_manifest_sha256 || '') &&
    await sha256(new TextEncoder().encode(baselineText)) === data.baseline_manifest_sha256, 'baseline manifest bytes differ');
  const manifest = JSON.parse(baselineText);
  require(JSON.stringify(manifest.parts) === JSON.stringify(baselineParts), 'baseline part inventory differs from its manifest');
  const names = new Set(baselineParts.map(part => part.name)), hidden = new Set(data.hidden_baseline_visual_names);
  require(names.size === baselineParts.length && [...hidden].every(name => names.has(name)), 'hidden baseline names are absent or duplicated');
  const translations = data.baseline_display_translations_mm || {};
  require(Object.entries(translations).every(([name, value]) => names.has(name) && !hidden.has(name) && vector(value, 3)), 'invalid baseline display translations');
  const parts = baselineParts.filter(part => !hidden.has(part.name)).map(part => {
    require(localPath(part.path) && SHA.test(data.baseline_asset_sha256?.[part.path] || ''), `baseline asset pin missing: ${part.name}`);
    const path = resolveMeshPath(part.path);
    require(localPath(path), 'resolved baseline mesh path leaves the site');
    return {...part, path, expected_sha256: data.baseline_asset_sha256[part.path],
      ...(translations[part.name] ? {translation_mm: translations[part.name]} : {}),
      fabrication: {...part.fabrication, layer: 'baseline', display_class: 'baseline'}};
  });
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3, 'invalid topology record');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'triangle topology bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  for (const row of data.solids) parts.push({name: row.name,
    geometry: meshGeometry(THREE, row.mesh, topologies), fabrication: fabricationFor(row, data.model_inventory)});
  require(new Set(parts.map(part => part.name)).size === parts.length, 'visible baseline and overlay names collide');
  const connections = new Map();
  for (const part of parts) {
    const f = part.fabrication;
    if (f.kind !== 'bolt' || !f.connection_name) continue;
    require(typeof f.hardware_role === 'string', 'bolt component role missing');
    if (!connections.has(f.connection_name)) connections.set(f.connection_name, new Set());
    const roles = connections.get(f.connection_name);
    require(!roles.has(f.hardware_role), 'duplicate component role in one physical axis');
    roles.add(f.hardware_role);
  }
  for (const part of parts) {
    const f = part.fabrication, roles = connections.get(f.connection_name);
    if (f.kind !== 'bolt' || !roles) continue;
    f.stack_roles ||= [...roles];
    require(Array.isArray(f.stack_roles) && new Set(f.stack_roles).size === f.stack_roles.length &&
      f.stack_roles.length === roles.size && f.stack_roles.every(role => roles.has(role)), 'physical bolt stack roles differ');
  }
  const proposal = data.schema === PROPOSAL;
  if (proposal) {
    require(connections.size === CENSUS.bolts && parts.filter(part => part.fabrication.kind === 'screw').length === CENSUS.panel_kicker_screws,
      'visible bolt or panel screw census differs');
    require(parts.filter(part => part.fabrication.hardware_role === 'nut').length === CENSUS.nuts &&
      parts.filter(part => part.fabrication.hardware_role?.includes('washer')).length === CENSUS.washers, 'visible nut or washer census differs');
  }
  const design = {...manifest.design, ...data.design,
    key: data.design?.key || (proposal ? 'wood-joints-working-proposal' : 'wood-joints-reviewed'),
    status: data.status || data.layout_status, qualified_for_design: false,
    documents: data.design?.documents || [
      {label: 'Reviewed 104-axis development and authority', path: 'docs/wood-joints-mvp/README.md'},
      {label: 'Unadopted knee bridge working package', path: 'docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md'}]};
  const meta = {schema: data.schema, revision: data.revision_id || data.layout_id,
    status: data.status || data.layout_status, census: proposal ? data.census : data.counts,
    planning_mass_kg: proposal ? (data.planning_mass_kg ?? null) : null,
    changed_screw_axis_ids: data.changed_screw_axis_ids || data.model_inventory?.moved_panel_axes?.map(row => row.axis_id) || [],
    source_sha256: expectedSha256.toLowerCase(), proposal_binding: data.proposal_binding || null,
    bounds_scope: data.bounds_mm ? 'Declared source display bounds' : 'Union of baseline and overlay envelopes, including hidden baseline envelopes',
    complete_joint_acceptance: false, physical_release: false};
  return {parts, bounds_mm: displayBounds(data, manifest), design, meta};
}
