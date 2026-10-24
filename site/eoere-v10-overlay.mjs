import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadSingleSpacerScene} from './eoere-single-spacer-overlay.mjs';
import {loadV10Provenance, resolveV10SourceRef, validateV10SceneProvenance, V10_SCENE,
  V10_PROVENANCE_SHA256} from './eoere-v10-provenance.mjs';

const require = (ok, message) => {if (!ok) throw new Error('V10: '+message);};
const SHA = /^[a-f0-9]{64}$/;
const V9_SCENE = '250f8fb4e6fc965ebf77dc9a5822ece646a3163fb85878d15c265673275f4058';
const V9_LAYOUT = '29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef';
const ids = rows => rows.map(r => r.name);
const unique = rows => new Set(rows).size === rows.length;

export function validateV10Scene(data, layoutSha256) {
  require(data?.schema === 'eoere_v10_geometry_patch/v1' && /v10$/.test(data.revision || '') &&
    ['eoere-owner-frame-v10-development', 'eoere-current-frame-development'].includes(data.key), 'revision differs');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256, 'layout binding differs');
  require(data.parent_scene?.sha256 === V9_SCENE && data.parent_layout?.sha256 === V9_LAYOUT, 'v9 parent differs');
  require(data.geometry_source && SHA.test(data.geometry_source.sha256 || '') &&
    data.clearance_source && SHA.test(data.clearance_source.sha256 || ''), 'geometry/clearance binding missing');
  require(Number.isInteger(data.part_count) && data.part_count > 0 && data.parent_part_count === 1021, 'part census differs');
  require(Number.isInteger(data.counts?.bolt_stacks) && data.counts.bolt_stacks > 96 &&
    data.counts.Hillman_axes === 66 && Number.isInteger(data.counts.angles) && data.counts.angles >= 24,
  'inventory differs');
  for (const flag of ['historical_capacity_transferred', 'complete_conditional_frame_evaluation',
    'actual_parts_verified', 'fabrication_released', 'climbing_released']) require(data[flag] === false, 'claim boundary: '+flag);
  require(data.panel_Hillman_resolution_deferred === true, 'panel qualification differs');
  require(Array.isArray(data.replacements) && Array.isArray(data.additions) && Array.isArray(data.removals), 'patch lists missing');
  const replaced = ids(data.replacements), added = ids(data.additions), removed = data.removals;
  require(unique([...replaced, ...added, ...removed]) && removed.every(n => typeof n === 'string'), 'patch identities overlap');
  require(data.part_count === 1021 - removed.length + added.length, 'patch count differs');
  require(data.triangle_topologies && typeof data.triangle_topologies === 'object', 'topology map missing');
  for (const row of [...data.replacements, ...data.additions]) {
    require(typeof row.name === 'string' && row.id === row.name && row.mesh && row.fabrication &&
      ['timber', 'bolt', 'bracket', 'panel', 'screw', 'wire', 'light'].includes(row.fabrication.kind), 'part metadata missing');
    require(SHA.test(row.source?.sha256 || '') && typeof row.source.path === 'string', 'part source missing');
    require(row.fabrication.actual_parts_verified === false && row.fabrication.complete_joint_qualified === false,
      'part qualification differs');
    if (row.fabrication.kind === 'bolt') require(typeof row.fabrication.connection_name === 'string' &&
      typeof row.fabrication.hardware_role === 'string' && Array.isArray(row.fabrication.stack_roles) &&
      row.fabrication.stack_roles.includes(row.fabrication.hardware_role), 'bolt stack metadata missing');
  }
  return data;
}

export function validateV10ComposedParts(parts, data) {
  require(parts.length === data.part_count && unique(parts.map(p => p.name)), 'composed identities/count differ');
  const stacks = new Map();
  for (const p of parts) {
    const f = p.fabrication;
    if (f?.kind !== 'bolt') continue;
    require(typeof f.connection_name === 'string' && typeof f.hardware_role === 'string', 'composed bolt identity missing');
    if (!stacks.has(f.connection_name)) stacks.set(f.connection_name, new Set());
    const roles = stacks.get(f.connection_name);
    require(!roles.has(f.hardware_role), 'duplicate bolt role: '+f.connection_name);
    roles.add(f.hardware_role);
  }
  require(stacks.size === data.counts.bolt_stacks, 'composed bolt count differs');
  require(parts.filter(p => p.fabrication?.kind === 'screw').length === 66, 'composed screw count differs');
  for (const [axis, roles] of stacks) {
    require(['shaft', 'head', 'head_washer', 'nut_washer', 'nut'].every(r => roles.has(r)), 'incomplete stack: '+axis);
    for (const p of parts.filter(p => p.fabrication?.connection_name === axis)) {
      const declared = p.fabrication.stack_roles;
      require(Array.isArray(declared) && unique(declared) && declared.length === roles.size &&
        declared.every(r => roles.has(r)), 'stack role census differs: '+axis);
    }
  }
  return parts;
}

export function applyV10StackMetadata(parts, data) {
  require(Array.isArray(data.stack_updates) && data.stack_updates.length === data.counts.bolt_stacks,
    'complete current stack metadata missing');
  const selections = new Map(data.stack_updates.map(r => [r.axis_id, r]));
  require(selections.size === data.counts.bolt_stacks, 'duplicate stack metadata');
  for (const part of parts) {
    const f = part.fabrication, selection = selections.get(f?.connection_name);
    if (f?.kind === 'bolt' && selection) part.fabrication = {...f, ...selection,
      kind: 'bolt', hardware_role: f.hardware_role, dimensions_mm: f.dimensions_mm,
      owner_frame_revision: data.revision,
      description: `V10 Candidate 13 ${selection.axis_id} ${f.hardware_role.replaceAll('_', ' ')}: `+
        `${selection.selected_bolt_grade}; nominal bolt length ${Number(selection.selected_underhead_length_mm).toFixed(3)} mm; `+
        `${Number(selection.spacer_piece_count)} factory spacer pieces in this stack; delivered fit unverified`,
      actual_parts_verified: false, complete_joint_qualified: false};
  }
  return parts;
}

export async function loadV10Scene(THREE, options) {
  options = {...options, ...V10_SCENE};
  const provenance = await loadV10Provenance(options.provenanceUrl);
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const bytes = await response.arrayBuffer();require(await sha256(bytes) === options.expectedSha256, 'scene bytes differ');
  const decoded = options.url.endsWith('.gz') ?
    await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer() : bytes;
  if (options.decodedSha256) require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateV10Scene(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  validateV10SceneProvenance(data, provenance);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'topology bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadSingleSpacerScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, layoutSha256: data.parent_layout.sha256, decodedSha256: undefined});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    require(data.removals.every(n => old.has(n)), 'removed parent part missing');
    for (const [rows, replacing] of [[data.replacements, true], [data.additions, false]]) for (const row of rows) {
      require(old.has(row.name) === replacing, 'replacement/addition parent mismatch: '+row.name);
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const previous = old.get(row.name);
      const part = {...previous, name: row.name, geometry, fabrication: {...previous?.fabrication, ...row.fabrication}};
      delete part.path;changed.set(row.name, part);
    }
    const parts = parent.parts.filter(p => !data.removals.includes(p.name)).map(p => changed.get(p.name) || p);
    parts.push(...data.additions.map(r => changed.get(r.name)));
    applyV10StackMetadata(parts, data);
    validateV10ComposedParts(parts, data);
    for (const part of parent.parts) if (changed.has(part.name) || data.removals.includes(part.name)) part.geometry?.dispose();
    const bounds = parent.bounds_mm.map(p => [...p]);
    for (const row of [...data.replacements, ...data.additions]) for (let k=0;k<3;k++) {
      bounds[0][k] = Math.min(bounds[0][k], row.mesh.bounds_xyz_mm[2*k]);
      bounds[1][k] = Math.max(bounds[1][k], row.mesh.bounds_xyz_mm[2*k+1]);
    }
    return {...parent, parts, bounds_mm: bounds,
      design: {...parent.design, key: data.key, qualified_for_design: false, documents: provenance.documents},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        layout_sha256: options.layoutSha256, counts: data.counts, current_response_computed: data.current_response_computed,
        current_own_response_bank_recorded: provenance.current_own_response_bank_recorded,
        provenance_sha256: V10_PROVENANCE_SHA256,
        portable_sources: {geometry_receipt: resolveV10SourceRef(data.layout_report, provenance),
          geometry: resolveV10SourceRef(data.geometry_source, provenance),
          clearance: resolveV10SourceRef(data.clearance_source, provenance)},
        planning_mass_kg: null,
        analysis_pass_transferred: false, physical_release: false, complete_joint_acceptance: false}};
  } catch (error) {
    for (const p of [...parent.parts, ...changed.values()]) p.geometry?.dispose();
    throw error;
  }
}
