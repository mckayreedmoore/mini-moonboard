// Separate HL35 experiment. Unchanged panels, LEDs and baseline meshes stay shared.
import {loadWoodJointScene, meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';

const PARENT = '74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf';
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];
const SHA = /^[0-9a-f]{64}$/;
const REVISIONS = {
  'hl35-all-duty-direct-replacement-v1': {duties: 24, angles: 48, newAxes: 140, displayedAxes: 152, screws: 0, panels: 0, wires: 0},
  'hl35-lower-fit-and-screw-clearance-v3': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 4, panels: 2, wires: 0},
  'hl35-full-hardware-and-header-fit-v4': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 4, panels: 2, wires: 0},
  'hl35-separated-seam-rails-and-service-audit-v5': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 8, panels: 2, wires: 0},
  'hl35-nominal-service-passages-and-wire-routes-v6': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 8, panels: 2, wires: 3},
  'hl35-center-foot-wire-clearance-v7': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 8, panels: 2, wires: 3},
  'hl35-deeper-header-seat-and-bearing-audit-v8': {duties: 22, angles: 30, newAxes: 98, displayedAxes: 112, screws: 8, panels: 2, wires: 3},
};

function require(value, message) {
  if (!value) throw new Error(`HL35 candidate: ${message}`);
}

export function validateHL35Scene(data) {
  require(data?.schema === 'hl35_candidate_display_delta/v1' &&
    data.candidate === 'compact-floor-flush-hl35-development' && data.status === 'REVISE', 'identity or disposition differs');
  require(data.parent_scene?.url === 'owner-wood-joints-wj24-scene.json' && data.parent_scene.sha256 === PARENT,
    'parent source binding differs');
  require(FLAGS.every(flag => data.release?.[flag] === false), 'release flags must remain false');
  const expected = REVISIONS[data.revision];
  require(expected, 'unknown revision');
  require(data.counts?.duties === expected.duties && data.counts.hl35_angles === expected.angles &&
    data.counts.retained_frame_bolt_axes === 12 && data.counts.panel_kicker_screw_axes === 66 &&
    data.counts.new_physical_bolt_axes === expected.newAxes, 'invalid candidate census');
  require(Array.isArray(data.replaced_host_names) && data.replaced_host_names.length === 16 &&
    new Set(data.replaced_host_names).size === 16, 'receiving-host census differs');
  require(Array.isArray(data.solids) && new Set(data.solids.map(row => row.id)).size === data.solids.length &&
    new Set(data.solids.map(row => row.name)).size === data.solids.length, 'duplicate solid identities');
  const counts = {timber: 0, bracket: 0, bolt: 0, screw: 0, panel: 0, wire: 0}, connections = new Map();
  for (const row of data.solids) {
    require(typeof row.name === 'string' && typeof row.id === 'string' &&
      Object.hasOwn(counts, row.fabrication?.kind), 'invalid solid or material');
    counts[row.fabrication.kind]++;
    if (row.template_id) {
      require(Object.hasOwn(data.mesh_templates || {}, row.template_id) &&
        Array.isArray(row.transform) && row.transform.length === 16 && row.transform.every(Number.isFinite),
      'invalid template instance');
      const m = row.transform;
      require(m[3] === 0 && m[7] === 0 && m[11] === 0 && m[15] === 1, 'invalid homogeneous transform');
      const columns = [[m[0], m[1], m[2]], [m[4], m[5], m[6]], [m[8], m[9], m[10]]];
      const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
      require(columns.every(c => Math.abs(dot(c, c) - 1) < 1e-7) &&
        [[0, 1], [0, 2], [1, 2]].every(([a, b]) => Math.abs(dot(columns[a], columns[b])) < 1e-7),
      'instance transform changes dimensions');
      const [a, b, c] = columns;
      const determinant = a[0] * (b[1] * c[2] - b[2] * c[1]) -
        b[0] * (a[1] * c[2] - a[2] * c[1]) + c[0] * (a[1] * b[2] - a[2] * b[1]);
      require(Math.abs(determinant - 1) < 1e-7, 'instance transform reflects geometry');
    } else require(row.mesh, 'solid has no display geometry');
    if (row.fabrication.kind !== 'bolt') continue;
    const f = row.fabrication;
    require(typeof f.connection_name === 'string' && typeof f.hardware_role === 'string', 'bolt identity missing');
    if (!connections.has(f.connection_name)) connections.set(f.connection_name, new Set());
    const roles = connections.get(f.connection_name);
    require(!roles.has(f.hardware_role), 'duplicate role on one physical bolt');
    roles.add(f.hardware_role);
  }
  const exportedAxes = expected.screws ? expected.displayedAxes : expected.newAxes;
  require(counts.timber === 16 && counts.bracket === expected.angles && counts.bolt === exportedAxes * 5 &&
    connections.size === exportedAxes && counts.screw === expected.screws && counts.panel === expected.panels && counts.wire === expected.wires,
    'visible new-part census differs');
  if (expected.screws) {
    const replacementCount = expected.screws + expected.panels + expected.wires;
    require(Array.isArray(data.removed_parent_visual_names) && data.removed_parent_visual_names.length === replacementCount &&
      new Set(data.removed_parent_visual_names).size === replacementCount, 'replacement identity census differs');
    require(Array.isArray(data.removed_parent_bolt_axes) && data.removed_parent_bolt_axes.length === 12 &&
      new Set(data.removed_parent_bolt_axes).size === 12 &&
      data.removed_parent_bolt_axes.every(id => connections.has(id)), 'rebuilt starting bolt census differs');
    require(Array.isArray(data.changed_screw_axis_ids) && data.changed_screw_axis_ids.length === expected.screws &&
      new Set(data.changed_screw_axis_ids).size === expected.screws &&
      data.changed_screw_axis_ids.every(id => data.solids.some(row => row.name === `fastener_${id}` && row.fabrication.kind === 'screw')),
      'changed screw display identity differs');
    if (expected.wires) require(Array.isArray(data.changed_wire_ids) && data.changed_wire_ids.length === expected.wires &&
      new Set(data.changed_wire_ids).size === expected.wires && data.changed_wire_ids.every(id =>
        data.removed_parent_visual_names.includes(id) && data.solids.some(row => row.name === id && row.fabrication.kind === 'wire')),
      'changed wire display identity differs');
  }
  for (const roles of connections.values()) require(roles.size === 5 &&
    ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'].every(role => roles.has(role)), 'incomplete planning bolt stack');
  for (const row of data.solids.filter(row => row.fabrication.kind === 'bolt')) {
    const expected = connections.get(row.fabrication.connection_name), supplied = row.fabrication.stack_roles;
    require(Array.isArray(supplied) && new Set(supplied).size === 5 && supplied.length === 5 &&
      supplied.every(role => expected.has(role)), 'stack role declaration differs');
  }
  return connections.size;
}

export async function loadHL35Scene(THREE, options) {
  require(SHA.test(options.expectedSha256 || ''), 'scene hash missing');
  const response = await fetch(options.url);
  require(response.ok, `scene unavailable (HTTP ${response.status})`);
  const bytes = await response.arrayBuffer();
  require(await sha256(bytes) === options.expectedSha256, 'scene bytes differ from the pinned export');
  const data = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  validateHL35Scene(data);
  const parent = await loadWoodJointScene(THREE, {...options,
    url: data.parent_scene.url, expectedSha256: data.parent_scene.sha256});
  const removedVisuals = new Set(data.removed_parent_visual_names || []);
  const removedAxes = new Set(data.removed_parent_bolt_axes || []);
  const parts = parent.parts.filter(part => (part.fabrication.display_class === 'baseline' ||
    ['panel_replacement', 'electrical_replacement'].includes(part.fabrication.display_class) ||
    part.fabrication.kind === 'screw') && !removedVisuals.has(part.name) &&
    !(part.fabrication.kind === 'bolt' && removedAxes.has(part.fabrication.connection_name)));
  require(!parts.some(part => data.replaced_host_names.includes(part.name)), 'old receiving host remains');
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && row.index_count === row.triangle_count * 3 && row.triangle_count > 0,
      'invalid topology record');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'triangle topology bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  const templates = new Map();
  for (const [id, row] of Object.entries(data.mesh_templates)) {
    templates.set(id, meshGeometry(THREE, row.mesh, topologies));
  }
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
      layer: 'hl35_candidate', display_class: row.fabrication.kind === 'bolt' ? 'candidate_hardware' : 'hl35_candidate'}});
  }
  for (const geometry of templates.values()) geometry.dispose();
  require(new Set(parts.map(part => part.name)).size === parts.length, 'visible part names collide');
  require(parts.filter(part => part.fabrication.kind === 'screw').length === 66, 'preserved screw census differs');
  const boltAxes = new Set(parts.filter(part => part.fabrication.kind === 'bolt').map(part => part.fabrication.connection_name));
  require(boltAxes.size === REVISIONS[data.revision].displayedAxes, 'complete physical bolt census differs');
  return {parts, bounds_mm: bounds, design: {...parent.design, ...data.design},
    meta: {status: data.status, revision: data.revision, census: data.counts,
      complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
}
