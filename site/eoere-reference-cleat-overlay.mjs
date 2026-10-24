import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadOwnerFrameScene} from './eoere-owner-frame-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Reference cleats: '+message);};
const ADDED = ['eoere_bolt_067', 'eoere_bolt_070'];
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'spacer', 'spacer_2', 'spacer_3', 'nut'];

export function validateReferenceCleats(data, layoutSha256) {
  require(data?.schema === 'eoere_reference_cleat_patch/v1' &&
    data.revision === 'eoere-reference-cleat-upper-pair-v5' &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(/^[a-f0-9]{64}$/.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256,
    'receipt differs');
  require(data.parent_layout?.sha256 === '33b7741bca920400860c26acfcfd77dbb019231b49b705537c3d371a612a6081' &&
    data.parent_scene?.sha256 === '9ade02a0370c7afe96ace7db91b677dfed98e29fba8fb7c9b55ccd6fedb491a8', 'parent differs');
  for (const key of ['historical_capacity_transferred', 'complete_conditional_frame_evaluation',
    'current_response_computed', 'upper_pair_eligible', 'fabrication_released', 'climbing_released'])
    require(data[key] === false, 'unresolved review status required: '+key);
  require(data.panel_Hillman_resolution_deferred === true, 'panel deferral differs');
  require(data.part_count === 1027 && data.counts?.bolt_stacks === 94 && data.counts.angles === 24 &&
    data.counts.sawn_members === 20 && data.counts.plywood_cleats === 4 && data.counts.Hillman_axes === 66,
    'inventory differs');
  const expected = ['left', 'right'].flatMap(side => ['base_side_'+side,
    'eoere_cleat_'+side, 'eoere_cleat_'+side+'_outer']);
  expected.push(...ADDED.flatMap(axis => ROLES.map(role => axis+'_'+role)));
  require(data.replacements?.length === 22 && new Set(data.replacements.map(r => r.name)).size === 22 &&
    JSON.stringify(data.replacements.map(r => r.name).sort()) === JSON.stringify(expected.sort()),
    'six changed timbers and two complete eight-piece stacks required');
  require(data.removals?.length === 0 && data.replacements.every(r => r.id === r.name && r.mesh),
    'unexpected removal or missing geometry');
  for (const row of data.replacements) {
    const axis = ADDED.find(axis => row.name.startsWith(axis+'_'));
    if (axis) require(row.fabrication.kind === 'bolt' && row.fabrication.connection_name === axis &&
      row.fabrication.hardware_role === row.name.slice(axis.length+1) &&
      JSON.stringify(row.fabrication.stack_roles) === JSON.stringify(ROLES) && row.copy_metadata_from,
      'added bolt stack identity differs');
    else require(row.fabrication.kind === 'timber', 'changed timber identity differs');
    if (row.name.startsWith('eoere_cleat_'))
      require(row.fabrication.nominal_leaf_thickness_mm === 19.05 &&
        row.fabrication.upper_bolts_per_corner === 2 && row.fabrication.lower_bolts_per_corner === 2 &&
        row.fabrication.actual_bond_qualified === false, 'cleat construction differs');
  }
  return data;
}

export async function loadReferenceCleatScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer();
  require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream()
    .pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateReferenceCleats(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadOwnerFrameScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, decodedSha256: data.parent_scene.decoded_sha256,
    layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name) || old.get(row.copy_metadata_from);
      require(previous?.fabrication.kind === row.fabrication.kind, 'parent part identity differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, name: row.name, geometry, fabrication: {...previous.fabrication, ...row.fabrication}};
      delete part.path;
      if (row.name.startsWith('eoere_cleat_')) {
        delete part.fabrication.proposed_lamination;
        part.fabrication.strength_review = 'Changed four-pin cleat; response and complete joint eligibility remain open';
      }
      changed.set(row.name, part);
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    for (const [name, part] of changed) if (!old.has(name)) parts.push(part);
    require(parts.length === 1027 && new Set(parts.map(p => p.name)).size === 1027, 'composed census differs');
    for (const part of parent.parts) if (changed.has(part.name)) part.geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        selected_bolt_stacks: 94, current_response_computed: false, upper_pair_eligible: false,
        conditional_frame_evaluation_complete: false, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
